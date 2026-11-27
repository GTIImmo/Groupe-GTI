# -*- coding: utf-8 -*-
"""R6.8 (R5 bis) : la SAUVEGARDE QUOTIDIENNE de ce que l'app ecrit (24/11/2026).

    python -X utf8 recrutement/sauvegarder_app.py            -> copie datee + relue + rotation (90 gardees)
    python -X utf8 recrutement/sauvegarder_app.py --essai    -> lit et compte, n'ecrit rien

Note : notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md, §13 (R5 bis) et §14 (R6.8).
Lancee chaque jour par scheduled/run_recrutement_sauvegarde.ps1 (tache « GTI Recrutement Sauvegarde »).

POURQUOI : depuis l'ecran (R6), l'app ecrit TOUS LES JOURS dans le schema « recrutement » : le suivi, le fil des
echanges, les retraits, les corrections, la liste « ne plus contacter », les fiches ajoutees a la main. Rien de
cela n'existe en local (la collecte n'en a pas besoin), la sauvegarde de nuit ne copie que le schema public, et
celle du recrutement ne passe que tous les deux mois. Cette copie est donc la seule trace hors de Supabase.

CE QU'ELLE FAIT :
  - elle lit, par le ROBOT (recrutement/robot.py), dans UNE transaction en lecture seule et a image fixe
    (REPEATABLE READ : les tables sont lues au meme instant), les 7 tables ci-dessous ;
  - elle les ecrit dans une base SQLite datee, C:\\Hektor\\Backups\\recrutement\\quotidien\\app_<date>.sqlite ;
  - elle la RELIT (integrity_check + nombre de lignes egal, table par table) : une sauvegarde qu'on ne relit
    pas n'en est pas une ;
  - elle garde les 90 plus recentes (90 jours, comme les tables critiques de l'app). C'est aussi ainsi qu'une
    personne effacee dans l'app disparait de ces copies : 90 jours au plus (duree ecrite dans la note).
Le journal ne porte que des COMPTES, jamais un nom. Sortie : 0 = copie faite et relue (ou essai), 1 = echec.
"""
import argparse
import datetime as dt
import decimal
import json
import os
import sqlite3
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

CIBLE = Path(os.environ.get("RECRUTEMENT_SAUVEGARDES", r"C:\Hektor\Backups\recrutement")) / "quotidien"
GARDER = 90
TABLES = (
    ("suivi", "select * from recrutement.suivi order by reseau, identifiant"),
    ("evenement", "select * from recrutement.evenement order by id"),
    ("retrait", "select * from recrutement.retrait order by id"),
    ("correction", "select * from recrutement.correction order by reseau, identifiant, champ"),
    ("liste_noire", "select * from recrutement.liste_noire order by empreinte"),
    ("fiche_saisie", "select * from recrutement.fiche where origine = 'saisie' order by reseau, identifiant"),
    ("agence_gti", "select * from recrutement.agence_gti order by nom"),
)


def valeur(v):
    """Une valeur Postgres en valeur SQLite, sans perte : dates en ISO, nombres exacts en texte."""
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (dt.datetime, dt.date, dt.time)):
        return v.isoformat()
    if isinstance(v, (decimal.Decimal, uuid.UUID)):
        return str(v)
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def lire() -> dict:
    """Les 7 tables, lues au meme instant, en lecture seule. Leve RobotIndisponible ou l'erreur de la base."""
    import robot
    con = robot.connexion()
    try:
        con.set_session(isolation_level="REPEATABLE READ", readonly=True)
        cur = con.cursor()
        lu = {}
        for nom, requete in TABLES:
            cur.execute(requete)
            lu[nom] = ([d[0] for d in cur.description], cur.fetchall())
        con.rollback()  # rien a valider : on n'a fait que lire
        return lu
    finally:
        con.close()


def ecrire(lu: dict, chemin: Path) -> None:
    dst = sqlite3.connect(chemin)
    try:
        for nom, (colonnes, lignes) in lu.items():
            cols = ", ".join(f'"{c}"' for c in colonnes)
            dst.execute(f'create table "{nom}" ({cols})')
            if lignes:
                trous = ", ".join("?" for _ in colonnes)
                dst.executemany(f'insert into "{nom}" ({cols}) values ({trous})',
                                [tuple(valeur(v) for v in l) for l in lignes])
        dst.execute("create table sauvegarde (quand text, source text, comptes text)")
        dst.execute("insert into sauvegarde values (?, ?, ?)",
                    (dt.datetime.now().isoformat(timespec="seconds"), "schema recrutement (Supabase), par le robot",
                     json.dumps({n: len(l) for n, (_, l) in lu.items()})))
        dst.commit()
    finally:
        dst.close()


def relire(lu: dict, chemin: Path) -> str | None:
    """None si la copie est bonne, sinon la raison."""
    relue = sqlite3.connect(chemin)
    try:
        integrite = relue.execute("pragma integrity_check").fetchone()[0]
        if integrite != "ok":
            return f"integrite {integrite}"
        for nom, (_, lignes) in lu.items():
            n = relue.execute(f'select count(*) from "{nom}"').fetchone()[0]
            if n != len(lignes):
                return f"{nom} : {n} lignes relues pour {len(lignes)} lues"
        return None
    finally:
        relue.close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--essai", action="store_true", help="lire et compter, sans rien ecrire")
    args = p.parse_args()
    import robot
    try:
        lu = lire()
    except robot.RobotIndisponible as e:
        print(f"⛔ SAUVEGARDE IMPOSSIBLE : {e}")
        return 1
    except Exception as e:
        texte = str(e).strip().splitlines()[0][:300] if str(e).strip() else ""
        conseil = (" -- le patch supabase/patch_recrutement_sauvegarde_2026-11-24.sql est-il pose ?"
                   if "permission" in texte.lower() or "denied" in texte.lower() else "")
        print(f"⛔ SAUVEGARDE IMPOSSIBLE (lecture) : {e.__class__.__name__} : {texte}{conseil}")
        return 1
    comptes = ", ".join(f"{n} {len(l)}" for n, (_, l) in lu.items())
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    chemin = CIBLE / f"app_{stamp}.sqlite"
    anciennes = sorted(CIBLE.glob("app_*.sqlite")) if CIBLE.exists() else []
    if args.essai:
        print(f"[essai] lu : {comptes}")
        print(f"[essai] ecrirait {chemin} ; en supprimerait {max(0, len(anciennes) + 1 - GARDER)} ancienne(s)")
        return 0
    CIBLE.mkdir(parents=True, exist_ok=True)
    try:
        ecrire(lu, chemin)
        raison = relire(lu, chemin)
    except Exception as e:
        raison = f"{e.__class__.__name__} : {str(e)[:200]}"
    if raison:
        chemin.unlink(missing_ok=True)  # une copie qui ne se relit pas ne doit pas passer pour bonne
        print(f"⛔ ECHEC : la copie ne se relit pas ({raison}) ; retiree")
        return 1
    for vieux in sorted(CIBLE.glob("app_*.sqlite"))[:-GARDER]:
        vieux.unlink()
    print(f"sauvegarde : {chemin.name} relue (integrite ok) -- {comptes} ; "
          f"{len(list(CIBLE.glob('app_*.sqlite')))} copie(s) gardee(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
