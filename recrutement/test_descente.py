# -*- coding: utf-8 -*-
"""Essai HORS LIGNE de la partie locale de la descente (R4) -- une base jetable, sans reseau.

    python -X utf8 recrutement/test_descente.py
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

DOSSIER_ESSAI = Path(tempfile.mkdtemp(prefix="recrutement_descente_"))
os.environ["RECRUTEMENT_DONNEES"] = str(DOSSIER_ESSAI)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import collecte_annuaires as ca  # noqa: E402
import descendre  # noqa: E402

rouges = []


def verifier(quoi, obtenu, attendu):
    ok = obtenu == attendu
    print(("  OK    " if ok else "  ROUGE ") + f"{quoi} : {obtenu!r}" + ("" if ok else f"   (attendu {attendu!r})"))
    if not ok:
        rouges.append(quoi)


def main():
    con = ca.ouvrir_base()
    base = {"departement": "42", "code_postal": "42000", "commune": "Saint-Etienne"}
    ca.enregistrer_fiche(con, "alpha", "a1", prenom="Pa", nom="NA1", telephone="06 11 11 11 11",
                         source_contact="essai", url="https://exemple.test/a1", **base)
    ca.enregistrer_fiche(con, "alpha", "a2", prenom="Pb", nom="NA2", siren="123456782", url="https://exemple.test/a2", **base)
    ca.enregistrer_fiche(con, "beta", "b1", prenom="Pc", nom="NB1", **base)
    ca.enregistrer_fiche(con, "beta", "b2", prenom="Pd", nom="NB2", **base)   # temoin inverse : jamais sur la liste
    con.execute("insert into entreprise (siren, trouve) values ('123456782', 1)")
    con.execute("insert into page_lue (url, reseau, lu_le, statut_http) values ('https://exemple.test/a1','alpha','x',200)")
    con.commit()
    noire = [(e, n, "2026-11-24") for n, e in (
        ca.empreintes_personne(telephone="06 11 11 11 11")                       # a1 par son telephone
        + ca.empreintes_personne(siren="123456782")                                # a2 par son SIREN
        + [x for x in ca.empreintes_personne(prenom="Pc", nom="NB1", departement="42") if x[0] == "nom"])]  # b1 par son nom
    corrections = [("beta", "b2", "telephone", "06 22 22 22 22", None, "2026-11-24 10:00:00+01")]

    print("\n1. L'essai ne touche a rien")
    c = descendre.appliquer(con, noire, corrections, essai=True)
    verifier("essai : fiches qui seraient retirees", c["fiches_retirees"], 3)
    verifier("essai : la base locale n'a pas bouge", con.execute("select count(*) from fiche").fetchone()[0], 4)

    print("\n2. La descente applique la liste et recopie le carnet")
    c = descendre.appliquer(con, noire, corrections, essai=False)
    restantes = sorted(r[0] for r in con.execute("select identifiant from fiche"))
    verifier("fiches restantes", restantes, ["b2"])
    verifier("l'entreprise de a2 est partie avec lui", con.execute("select count(*) from entreprise").fetchone()[0], 0)
    verifier("l'adresse de la page de a1 est partie", con.execute("select count(*) from page_lue").fetchone()[0], 0)
    verifier("la liste est rangee en local", con.execute("select count(*) from liste_noire").fetchone()[0], 3)
    verifier("le carnet est recopie", [tuple(r) for r in con.execute("select champ, valeur from correction")],
             [("telephone", "06 22 22 22 22")])

    print("\n3. La collecte suivante ne peut plus les remettre")
    ca.enregistrer_fiche(con, "alpha", "a1", prenom="Pa", nom="NA1", telephone="06 11 11 11 11", source_contact="essai", **base)
    ca.enregistrer_fiche(con, "gamma", "g9", prenom="Pc", nom="NB1", **base)   # b1 sous un autre reseau : son nom suffit
    verifier("a1 et b1 (sous un autre reseau) refuses", sorted(r[0] for r in con.execute("select identifiant from fiche")), ["b2"])
    ca.enregistrer_fiche(con, "beta", "b3", prenom="Pe", nom="NB3", **base)
    verifier("TEMOIN INVERSE : une personne neuve, hors liste, entre", con.execute(
        "select count(*) from fiche where identifiant='b3'").fetchone()[0], 1)

    print("\n4. Un carnet vide en base vide le carnet local")
    descendre.appliquer(con, noire, [], essai=False)
    verifier("carnet local", con.execute("select count(*) from correction").fetchone()[0], 0)
    con.close()


try:
    main()
finally:
    shutil.rmtree(DOSSIER_ESSAI, ignore_errors=True)
print(f"\n{'TOUT VERT' if not rouges else str(len(rouges)) + ' ROUGE(S) : ' + ', '.join(rouges)}")
sys.exit(1 if rouges else 0)
