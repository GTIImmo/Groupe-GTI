# -*- coding: utf-8 -*-
"""Essai HORS LIGNE de l'OUVERTURE d'une collecte (24/11/2026) -- une base jetable, aucun reseau.

    python -X utf8 recrutement/test_ouverture_collecte.py

LE DEFAUT QU'IL GARDE (trouve par le 1er passage complet, collecte n° 2, le 24/11) : une collecte neuve ne
remettait pas a zero les marques « deja lu » de la precedente. SAFTI, KW et 3G n'ont donc rien relu, aucune
de leurs fiches n'a ete VUE, et ils sont sortis MALADES. test_mise_a_jour.py ne l'avait pas vu : il fabrique
les observations, il ne passe pas par les marques des lecteurs.

Chaque attendu est ecrit AVANT de lancer. Sortie 0 = tout vert, 1 = un rouge.
Temoin inverse : le meme essai contre l'ANCIEN collecteur doit sortir ROUGE (voir la note du chantier, §14).
"""
import argparse
import datetime as dt
import os
import shutil
import sys
import tempfile
from pathlib import Path

DOSSIER_ESSAI = Path(tempfile.mkdtemp(prefix="recrutement_ouverture_"))
os.environ["RECRUTEMENT_DONNEES"] = str(DOSSIER_ESSAI)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import collecte_annuaires as ca  # noqa: E402

ARGS = argparse.Namespace(limite=0, relire=False, sans_reseau=True)
rouges = []


def verifier(quoi, obtenu, attendu):
    ok = obtenu == attendu
    print(("  OK    " if ok else "  ROUGE ") + f"{quoi} : {obtenu!r}" + ("" if ok else f"   (attendu {attendu!r})"))
    if not ok:
        rouges.append(quoi)


def il_y_a(secondes: int) -> str:
    return (dt.datetime.now() - dt.timedelta(seconds=secondes)).strftime("%Y-%m-%d %H:%M:%S")


def main() -> int:
    con = ca.ouvrir_base()
    print("1. LA COLLECTE N° 1, LUE EN ENTIER (fiches lues, communes SAFTI lues, une page de liste lue ce matin)")
    for reseau, ident in (("safti", "a"), ("kw", "b"), ("3g", "c"), ("orpi", "d")):
        ca.enregistrer_fiche(con, reseau, ident, prenom="Essai", nom=f"Fictif {ident}", departement="42", fiche_lue=1)
    con.execute("insert into grille_safti (chemin, dep, population, ordre, lue) values ('commune-essai', '42', 100, 0, 1)")
    con.execute("insert into page_lue (url, reseau, lu_le, statut_http) values ('https://exemple.invalid/liste', 'capifrance', ?, 200)",
                (il_y_a(120),))
    con.commit()
    ca._CACHE.clear()
    ca.cmd_collecte_initiale(con, None, ARGS)
    verifier("collecte n° 1 finie", con.execute("select etat from collecte where numero=1").fetchone()[0], "finie")

    print("2. ON OUVRE LA COLLECTE N° 2 : TOUT EST A RELIRE")
    ca._CACHE.clear()
    verifier("ouverture rend FINI", ca.cmd_collecte_ouvrir(con, None, ARGS), ca.CODE_FINI)
    verifier("collecte n° 2 en cours", con.execute("select etat from collecte where numero=2").fetchone()[0], "en_cours")
    verifier("fiches encore marquees lues", con.execute("select count(*) from fiche where fiche_lue=1").fetchone()[0], 0)
    verifier("communes SAFTI encore marquees lues", con.execute("select count(*) from grille_safti where lue=1").fetchone()[0], 0)
    # ce que voient les lecteurs (les memes requetes qu'eux)
    verifier("SAFTI : communes a lire", len(con.execute("select chemin from grille_safti where lue=0").fetchall()), 1)
    verifier("KW : fiches a lire", len(con.execute("select 1 from fiche where reseau='kw' and fiche_lue=0").fetchall()), 1)
    verifier("3G : sa fiche serait sautee", bool(con.execute(
        "select 1 from fiche where reseau='3g' and identifiant='c' and fiche_lue=1").fetchone()), False)
    verifier("la page lue AVANT l'ouverture est a relire", ca.deja_lue_aujourdhui(con, "https://exemple.invalid/liste"), False)

    print("3. PENDANT LA COLLECTE : une fiche relue est VUE, une page relue n'est pas relue deux fois")
    ca.enregistrer_fiche(con, "safti", "a", fiche_lue=1)
    verifier("la fiche relue est observee dans la n° 2", bool(con.execute(
        "select 1 from observation where collecte=2 and reseau='safti' and identifiant='a'").fetchone()), True)
    ca.noter_page(con, "https://exemple.invalid/liste", "capifrance", 200)
    verifier("la page relue PENDANT la collecte compte comme lue", ca.deja_lue_aujourdhui(con, "https://exemple.invalid/liste"), True)

    print("4. LA REPRISE (coupure a 9 min) NE REMET RIEN A ZERO")
    con.execute("update grille_safti set lue=1")
    con.commit()
    ca._CACHE.clear()
    verifier("reprise rend FINI", ca.cmd_collecte_ouvrir(con, None, ARGS), ca.CODE_FINI)
    verifier("pas de collecte n° 3", con.execute("select count(*) from collecte").fetchone()[0], 2)
    verifier("la fiche relue reste lue", con.execute("select fiche_lue from fiche where reseau='safti' and identifiant='a'").fetchone()[0], 1)
    verifier("la commune relue reste lue", con.execute("select lue from grille_safti").fetchone()[0], 1)
    verifier("les autres restent a lire", con.execute("select count(*) from fiche where fiche_lue=0").fetchone()[0], 3)

    print("5. HORS COLLECTE (relecture d'un seul site) : « deja lue » veut dire « aujourd'hui »")
    con.execute("update collecte set etat='finie', fin=? where numero=2", (ca.maintenant(),))
    con.commit()
    ca._CACHE.clear()
    verifier("aucune collecte ouverte", ca.collecte_ouverte(con), None)
    verifier("la page lue aujourd'hui compte comme lue", ca.deja_lue_aujourdhui(con, "https://exemple.invalid/liste"), True)
    con.execute("update page_lue set lu_le='2026-01-01 10:00:00'")
    con.commit()
    verifier("une page lue un autre jour est a relire", ca.deja_lue_aujourdhui(con, "https://exemple.invalid/liste"), False)

    con.close()
    print("TOUT VERT" if not rouges else f"ROUGE : {len(rouges)} controle(s) -- {', '.join(rouges)}")
    return 1 if rouges else 0


if __name__ == "__main__":
    try:
        code = main()
    finally:
        shutil.rmtree(DOSSIER_ESSAI, ignore_errors=True)
    sys.exit(code)
