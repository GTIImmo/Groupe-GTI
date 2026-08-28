# -*- coding: utf-8 -*-
"""C.13-a -- LE DOMICILE DU MANDAT : le magasin de ce que l'app detient.

POURQUOI IL EXISTE, ET POURQUOI app_annonce_champ_app NE POUVAIT PAS SUFFIRE.

Le magasin des annonces (C.6) est cle par app_dossier_id -- une ligne par ANNONCE.
Or une date de cloture appartient a un MANDAT, et une annonce en porte plusieurs
dans sa vie : 24 939 mandats pour 24 657 annonces, et certaines en comptent dix.
Ecrire la cloture au grain de l'annonce ne saurait designer QUEL mandat est clos.

LA CLE, MESUREE LE 28/08 -- on ne l'a pas choisie, on l'a constatee :

    (annonce, hektor_mandat_id)   24 939 combinaisons sur 24 939   UNIQUE
    (annonce, numero)                157 collisions
    hektor_mandat_id seul            500 collisions   <- Hektor reutilise ses id
    numero seul                    6 803 collisions

C'est exactement le couple que le projet avait deja retenu pour les mandats.

CE QUE CE MAGASIN FAIT, ET CE QU'IL NE FAIT PAS.
    Il note, par mandat, ce que l'APP detient et ce que le MIROIR dit -- rien de
    plus. Il OBSERVE, il ne tranche pas : c'est le contrat d'autorite qui tranche
    (contrat_autorite.py) et l'applicateur qui ecrit (appliquer_contrat.py).
    Meme partage des roles que C.6 / C.7, pour la meme raison : un ecart n'est pas
    une preuve que l'app est l'auteur, ce peut etre un simple decalage.

CE QU'IL PROTEGE. app_view_generale est DETRUITE et refaite chaque nuit depuis le
miroir. Une date de cloture ecrite par l'app n'y survivrait pas jusqu'a 05:30. Ce
magasin est une table A COTE, JAMAIS RECONSTRUITE -- le patron qui a deja marche
quatre fois ici : app_dossier, app_affaire_ledger, app_search_registry,
app_annonce_champ_app.

CE QU'IL NE FAIT PAS, ET C'EST UNE DECISION. Le rattrapage des 23 715 mandats qui
devraient porter une date de cloture est reporte EN FIN DE PLAN, avec A.1/A.2/A.3
-- decision de Frederic, 28/08. Ici on ne fait qu'observer.

    python phase2/identite/magasin_mandat_app.py --dry-run
    python phase2/identite/magasin_mandat_app.py
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"
MIROIR_DB = RACINE / "data" / "hektor.sqlite"
VERROU = RACINE / "pull_from_supabase.lock"

MAGASIN = "app_mandat_champ_app"

# Les champs suivis. UN SEUL pour l'instant, et c'est delibere : sur 24 939 mandats,
# Hektor ne porte une date de cloture que 94 fois (0,4 %). C'est le seul champ du
# mandat ou il n'a rien a dire -- donc le seul qu'on puisse confier a l'app sans
# risquer de la figer sur une valeur perimee. Les autres (date_debut, date_fin,
# type, montant) sont renseignes a ~100 % chez Hektor ; ils suivront quand
# l'editeur de mandat de l'app sera le seul lieu de saisie.
CHAMPS_SUIVIS = ("mandat_date_cloture",)

SCHEMA = """
CREATE TABLE IF NOT EXISTS app_mandat_champ_app (
    hektor_annonce_id   TEXT NOT NULL,
    hektor_mandat_id    TEXT NOT NULL,
    champ               TEXT NOT NULL,
    valeur_app          TEXT,
    valeur_miroir       TEXT,
    numero_mandat       TEXT,
    origine             TEXT,
    vu_le               TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vu_la_premiere_fois TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (hektor_annonce_id, hektor_mandat_id, champ)
)
"""


def norme(valeur) -> str:
    """Compare ce qui se compare, pas les representations.

    Les deux registres de Hektor n'ecrivent pas la cloture pareil -- mesure du
    28/08 : PROTEXA rend '2026-08-26 10:26:42', HEKTOR rend '2026-08-25'. Sans
    cette normalisation, tout mandat PROTEXA clos apparaitrait comme un ecart.
    """
    texte = "" if valeur is None else str(valeur).strip()
    if texte in ("", "0", "0000-00-00", "0000-00-00 00:00:00", "-0001-11-30"):
        return ""
    if len(texte) >= 10 and texte[4:5] == "-" and texte[7:8] == "-":
        return texte[:10]
    return texte


def charger_env() -> tuple[str, str]:
    for fichier in (RACINE / ".env", RACINE / "apps" / "hektor-v1" / ".env"):
        if not fichier.exists():
            continue
        for ligne in fichier.read_text(encoding="utf-8", errors="ignore").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, valeur = ligne.split("=", 1)
            os.environ.setdefault(cle.strip(), valeur.strip().strip('"').strip("'"))
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    return url.rstrip("/"), cle


def lire_registre_supabase(url: str, cle: str) -> list[dict]:
    """Le registre tel que l'APP le connait. PAGINE, et ce n'est pas decoratif :
    PostgREST plafonne TOUTE reponse a 1 000 lignes quelle que soit la limite
    demandee. Le piege a ete mesure le 25/08 -- sans pagination, on aurait
    applique un contrat au douzieme du parc, EN SILENCE."""
    lignes: list[dict] = []
    depart = 0
    while True:
        params = urllib.parse.urlencode({
            "select": "hektor_annonce_id,mandat_source_id,numero_mandat,mandat_date_cloture",
            "order": "register_row_id.asc",
            "limit": "1000",
            "offset": str(depart),
        })
        requete = urllib.request.Request(
            url + "/rest/v1/app_mandat_register_current?" + params,
            headers={"apikey": cle, "Authorization": "Bearer " + cle})
        with urllib.request.urlopen(requete, timeout=90) as reponse:
            page = json.loads(reponse.read().decode("utf-8"))
        if not page:
            break
        lignes.extend(page)
        if len(page) < 1000:
            break
        depart += len(page)
    return lignes


def lire_magasin_supabase(url: str, cle: str) -> list[dict]:
    """Ce que le WORKER a ecrit -- les clotures faites depuis l'app.

    Source distincte du registre, et c'est deliberé : une annonce close SORT du
    registre (642 des 1 105 mandats invisibles le sont pour cette raison), donc la
    cloture ne pouvait pas s'y poser. La table app_mandat_champ_app, elle, n'est
    jamais reconstruite -- c'est le patron app_dossier / app_affaire_ledger.

    Sa cle est (annonce, NUMERO de mandat) : c'est ce que le worker detient au
    moment du geste, le payload du front ne portant jamais l'identifiant Hektor.
    """
    lignes: list[dict] = []
    depuis = 0
    while True:
        params = urllib.parse.urlencode({
            "select": "hektor_annonce_id,numero_mandat,champ,valeur_app,origine,ecrit_le",
            "order": "hektor_annonce_id",
            "offset": str(depuis),
            "limit": "1000",
        })
        requete = urllib.request.Request(
            url + "/rest/v1/app_mandat_champ_app?" + params,
            headers={"apikey": cle, "Authorization": "Bearer " + cle},
        )
        with urllib.request.urlopen(requete, timeout=60) as reponse:
            paquet = json.loads(reponse.read().decode("utf-8"))
        lignes.extend(paquet)
        if len(paquet) < 1000:
            return lignes
        depuis += 1000


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="montre sans rien ecrire")
    args = ap.parse_args()

    # La descente tient ce verrou pendant ~21 minutes. Ecrire pendant qu'elle
    # tourne, c'est l'incident du 22/08 -- on ne recommence pas.
    if VERROU.exists() and not args.dry_run:
        print("La descente est en cours (verrou present) -- on ne touche a rien.")
        return 0

    # uri=True est necessaire pour attacher le miroir en LECTURE SEULE : sans lui,
    # sqlite3 prend 'file:...?mode=ro' pour un nom de fichier litteral.
    conn = sqlite3.connect("file:" + BASE.as_posix() + "?mode=rw", timeout=60, uri=True)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute(SCHEMA)
    conn.execute("ATTACH DATABASE 'file:" + MIROIR_DB.as_posix() + "?mode=ro' AS miroir")

    # CE QUE DIT LE MIROIR, par couple (annonce, mandat).
    miroir = {}
    for annonce, mandat, numero, cloture in conn.execute(
            "SELECT CAST(hektor_annonce_id AS TEXT), CAST(hektor_mandat_id AS TEXT), "
            "COALESCE(numero,''), COALESCE(date_cloture,'') FROM miroir.hektor_mandat"):
        miroir[(annonce, mandat)] = {"numero": numero, "mandat_date_cloture": cloture}
    print("miroir : %d mandats" % len(miroir))

    # CE QUE DIT L'APP. Relu EN DIRECT dans Supabase, pas dans la copie locale :
    # la copie a 22 h de retard a 05:30, et le seul moment ou cette etape SERT,
    # c'est justement quand une saisie est recente. Meme raison qu'en C.7.
    url, cle = charger_env()
    lignes = lire_registre_supabase(url, cle)
    print("app    : %d lignes de registre relues dans Supabase" % len(lignes))

    ecrits = inchanges = sans_mandat = absents_miroir = 0
    ecarts = []
    for ligne in lignes:
        annonce = str(ligne.get("hektor_annonce_id") or "").strip()
        mandat = str(ligne.get("mandat_source_id") or "").strip()
        if not annonce or not mandat:
            sans_mandat += 1
            continue
        ref = miroir.get((annonce, mandat))
        if ref is None:
            absents_miroir += 1
            ref = {}
        for champ in CHAMPS_SUIVIS:
            v_app = norme(ligne.get(champ))
            v_mir = norme(ref.get(champ))
            if v_app == v_mir:
                inchanges += 1
                continue
            ecarts.append((annonce, mandat, champ, v_app, v_mir))
            if args.dry_run:
                continue
            conn.execute(
                "INSERT INTO " + MAGASIN + " "
                "(hektor_annonce_id, hektor_mandat_id, champ, valeur_app, "
                " valeur_miroir, numero_mandat, origine, vu_le) "
                "VALUES (?,?,?,?,?,?,'observe',CURRENT_TIMESTAMP) "
                "ON CONFLICT(hektor_annonce_id, hektor_mandat_id, champ) DO UPDATE SET "
                "  valeur_app    = excluded.valeur_app, "
                "  valeur_miroir = excluded.valeur_miroir, "
                "  numero_mandat = excluded.numero_mandat, "
                "  vu_le         = CURRENT_TIMESTAMP",
                (annonce, mandat, champ, v_app or None, v_mir or None,
                 str(ligne.get("numero_mandat") or "") or None))
            ecrits += 1

    # --- SECONDE SOURCE : CE QUE L'APP A ECRIT ELLE-MEME ---------------------
    # Le registre ci-dessus dit ce que l'app AFFICHE ; celui-ci dit ce qu'elle a
    # VOULU. Les deux sont necessaires : une annonce close ne figure plus dans le
    # registre, donc sa cloture n'y serait jamais lue.
    #
    # Le worker ecrit un NUMERO de mandat ; le magasin travaille par identifiant.
    # On construit donc l'index inverse -- et on REFUSE de trancher quand il est
    # ambigu, plutot que de deviner (regle du projet : Hektor reutilise ses
    # identifiants, 342 sont partages entre annonces).
    par_numero: dict[tuple[str, str], str] = {}
    ambigus: set[tuple[str, str]] = set()
    for (a_id, m_id), ref in miroir.items():
        num = str(ref.get("numero") or "").strip()
        if not num:
            continue
        cle_num = (a_id, num)
        if cle_num in par_numero and par_numero[cle_num] != m_id:
            ambigus.add(cle_num)
        par_numero[cle_num] = m_id

    ecrits_app = non_resolus = 0
    try:
        saisies = lire_magasin_supabase(url, cle)
    except Exception as err:  # une lecture ratee ne doit jamais valoir "rien a dire"
        print("   magasin Supabase illisible (%s) -- on ne conclut rien" % str(err)[:70])
        saisies = None

    if saisies is not None:
        print("app    : %d saisie(s) lue(s) dans app_mandat_champ_app" % len(saisies))
        for ligne in saisies:
            annonce = str(ligne.get("hektor_annonce_id") or "").strip()
            numero = str(ligne.get("numero_mandat") or "").strip()
            champ = str(ligne.get("champ") or "").strip()
            v_app = norme(ligne.get("valeur_app"))
            if not annonce or not numero or champ not in CHAMPS_SUIVIS or not v_app:
                continue
            cle_num = (annonce, numero)
            mandat = par_numero.get(cle_num)
            if mandat is None or cle_num in ambigus:
                non_resolus += 1
                continue
            v_mir = norme((miroir.get((annonce, mandat)) or {}).get(champ))
            if args.dry_run:
                continue
            conn.execute(
                "INSERT INTO " + MAGASIN + " "
                "(hektor_annonce_id, hektor_mandat_id, champ, valeur_app, "
                " valeur_miroir, numero_mandat, origine, vu_le) "
                "VALUES (?,?,?,?,?,?,'cloture_app',CURRENT_TIMESTAMP) "
                "ON CONFLICT(hektor_annonce_id, hektor_mandat_id, champ) DO UPDATE SET "
                "  valeur_app    = excluded.valeur_app, "
                "  valeur_miroir = excluded.valeur_miroir, "
                "  numero_mandat = excluded.numero_mandat, "
                "  origine       = 'cloture_app', "
                "  vu_le         = CURRENT_TIMESTAMP",
                (annonce, mandat, champ, v_app, v_mir or None, numero))
            ecrits_app += 1

    if not args.dry_run:
        conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM " + MAGASIN).fetchone()[0]
    conn.close()

    print()
    print("   couples compares sans ecart                  : %d" % inchanges)
    print("   ecarts notes                                 : %d" % len(ecarts))
    print("   lignes sans identifiant de mandat (ignorees) : %d" % sans_mandat)
    print("   mandats absents du miroir                    : %d" % absents_miroir)
    print("   SAISIES DE L APP reprises                    : %d" % ecrits_app)
    print("   saisies au numero de mandat introuvable      : %d" % non_resolus)
    for annonce, mandat, champ, v_app, v_mir in ecarts[:10]:
        print("      annonce %-8s mandat %-8s %s : app=%r miroir=%r"
              % (annonce, mandat, champ, v_app, v_mir))
    print()
    print("   magasin : %d ligne(s)%s"
          % (total, "   (dry-run : rien ecrit)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
