# -*- coding: utf-8 -*-
"""Essai HORS LIGNE du lecteur des agences La Boite Immo (25/11/2026) -- une base jetable, aucun reseau.

    python -X utf8 recrutement/test_lecteurs_agences.py
    python -X utf8 recrutement/test_lecteurs_agences.py --collecteur <dossier>   (temoin inverse : un AUTRE collecteur)

CE QU'IL GARDE (sonde du 25/11 sur les vraies pages) :
  - Henri Pardon : l'element d'une personne n'est pas un <article>, et le titre <h1> porte le nom ET la fonction
    (« title__content-1 » / « title__content-2 ») -- l'ancien lecteur ne voyait personne ;
  - Cantard : la page n'a pas de donnees structurees ; l'adresse de l'agence n'est ECRITE que sur la page
    (« coords-address__zipcity ») -- sans elle la personne n'etait pas situee, donc pas gardee ;
  - le conteneur « team-listing-v1__items » ne doit JAMAIS compter pour une personne.
Les pages ci-dessous reprennent la FORME des vraies pages ; les personnes sont fictives.

Chaque attendu est ecrit AVANT de lancer. Sortie 0 = tout vert, 1 = un rouge.
Temoin inverse : contre le collecteur d'avant le 25/11, les points 1 et 5 doivent sortir ROUGES.
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

P = argparse.ArgumentParser()
P.add_argument("--collecteur", help="dossier d'un autre collecte_annuaires.py (temoin inverse)")
OPTIONS = P.parse_args()

DOSSIER_ESSAI = Path(tempfile.mkdtemp(prefix="recrutement_agences_"))
os.environ["RECRUTEMENT_DONNEES"] = str(DOSSIER_ESSAI)
sys.path.insert(0, OPTIONS.collecteur or str(Path(__file__).resolve().parent))
import collecte_annuaires as ca  # noqa: E402

print(f"collecteur essaye : {Path(ca.__file__).resolve()}")
rouges = []


def verifier(quoi, obtenu, attendu):
    ok = obtenu == attendu
    print(("  OK    " if ok else "  ROUGE ") + f"{quoi} : {obtenu!r}" + ("" if ok else f"   (attendu {attendu!r})"))
    if not ok:
        rouges.append(quoi)


# --- les formes des vraies pages (personnes fictives) ---------------------------------------
HENRI_PARDON = """
<div class="team-listing-v1__items-wrapper"><div class="team-listing-v1__items">
<div class="team-listing-v1__item"><div class="item__data"><div class="item__info"><header class="item__info-title">
<div class="title"><h1 class="title__content"><span class="title__content-1">Jean ESSAI</span><span class="title__content-2">G&eacute;rant</span></h1></div>
</header><div class="item__info-extra"><a href="tel:+33600000001" class="item__info-extra--phone">06 00 00 00 01</a></div></div></div></div>
<div class="team-listing-v1__item"><div class="item__data"><div class="item__info"><header class="item__info-title">
<div class="title"><h1 class="title__content"><span class="title__content-1">Marie FICTIVE</span><span class="title__content-2">Assistante commerciale</span></h1></div>
</header><div class="item__info-extra"><a href="tel:+33600000002" class="item__info-extra--phone">06 00 00 00 02</a></div></div></div></div>
<div class="team-listing-v1__item"><div class="item__data"><div class="item__info"><header class="item__info-title">
<div class="title"><h1 class="title__content"><span class="title__content-1">Paul TEMOIN</span><span class="title__content-2">N&eacute;gociateur</span></h1></div>
</header></div></div></div>
</div></div>
"""
CANTARD = """
<div class="team-listing-v1__listing"><article class="team-listing-v1__item member-1"><div class="member-1__content">
<div class="member-1__title title"><h2 class="title__content">Claire ESSAI</h2><p class="title__subtitle">Agent immobilier</p></div>
<div class="member-1__coords"><a href="tel:0400000003" class="coords-phone__content">04 00 00 00 03</a>
<a href="mailto:claire.essai@exemple.invalid">claire.essai@exemple.invalid</a></div></div></article></div>
<footer><div class="coords-address type-bdd-adrs-1"><p class="coords-address__content">1 place de l'Essai
<span class="coords-address__zipcity">63140 <span class="coords-address__city">Ch&acirc;tel-Guyon</span></span></p></div></footer>
"""
V2_INFOS = """
<article class="team-listing-v2__item"><span class="infos__name">Luc</span><span class="infos__name">FICTIF</span>
<span class="infos__position">Conseiller immobilier</span><a href="tel:0600000004">tel</a></article>
"""
TEAM_LIST = """
<div class="team-list-v1__item"><div class="item__block-name">Anne ESSAI</div><span class="title-v1__part1">Agent commercial</span>
<a href="tel:0600000005">tel</a></div>
"""
CONTENEUR_SEUL = '<div class="team-listing-v1__items"><h1 class="title__content">Notre equipe</h1></div>'


def noms(page):
    return [(m["nom"], m["fonction"], m["tel"], m["mail"]) for m in ca.membres_lbi(page)]


def main() -> int:
    print("1. HENRI PARDON : <div> + nom et fonction dans le titre (3 personnes ; le conteneur ne compte pas)")
    verifier("personnes lues", noms(HENRI_PARDON), [
        ("Jean ESSAI", "Gérant", "06 00 00 00 01", None),
        ("Marie FICTIVE", "Assistante commerciale", "06 00 00 00 02", None),
        ("Paul TEMOIN", "Négociateur", None, None)])

    print("2. LES FORMES DEJA CONNUES NE BOUGENT PAS")
    verifier("member-1 (Cantard)", noms(CANTARD), [("Claire ESSAI", "Agent immobilier", "04 00 00 00 03", "claire.essai@exemple.invalid")])
    verifier("team-listing-v2 / infos__name", noms(V2_INFOS), [("Luc FICTIF", "Conseiller immobilier", "06 00 00 00 04", None)])
    verifier("team-list-v1 / item__block-name", noms(TEAM_LIST), [("Anne ESSAI", "Agent commercial", "06 00 00 00 05", None)])

    print("3. TEMOIN : un conteneur seul n'est pas une personne")
    verifier("conteneur seul", noms(CONTENEUR_SEUL), [])

    print("4. L'ADRESSE ECRITE SUR LA PAGE")
    lire_adresse = getattr(ca, "adresse_page", None)
    verifier("adresse de Cantard", lire_adresse(CANTARD) if lire_adresse else "fonction absente",
             {"cp": "63140", "commune": "Châtel-Guyon"})
    verifier("pas d'adresse -> rien", lire_adresse(HENRI_PARDON) if lire_adresse else "fonction absente", {})

    print("5. DE BOUT EN BOUT (lecteur simule, pas de reseau) : une agence SANS lieu dans la liste")
    con = ca.ouvrir_base()
    pages = {"https://essai.invalid/cantard/": CANTARD, "https://essai.invalid/sans-adresse/": CANTARD.split("<footer>")[0]}
    ca.lire = lambda lecteur, url, reseau, entetes=None: pages.get(url)
    sites = (("cantard", "Agence Essai", "https://essai.invalid/cantard/", None, None),
             ("sansadresse", "Agence Sans Adresse", "https://essai.invalid/sans-adresse/", None, None))
    ca._lire_agences(con, None, argparse.Namespace(limite=0), "lbi", sites, ca.membres_lbi)
    lignes = con.execute("select identifiant, code_postal, departement, telephone, email, agence from fiche where reseau='lbi'"
                         " order by identifiant").fetchall()
    verifier("fiches gardees", [tuple(r) for r in lignes],
             [("cantard/claire-essai", "63140", "63", "04 00 00 00 03", "claire.essai@exemple.invalid", "Agence Essai")])
    verifier("TEMOIN : sans adresse nulle part, la personne n'est pas gardee",
             con.execute("select count(*) from fiche where identifiant like 'sansadresse/%'").fetchone()[0], 0)

    print("6. MINIMISATION (inchangee) : l'assistante de Henri Pardon n'est pas gardee")
    pages["https://essai.invalid/hp/"] = HENRI_PARDON
    ca._lire_agences(con, None, argparse.Namespace(limite=0), "lbi",
                     (("hp", "Agence HP", "https://essai.invalid/hp/", "42000", "Saint-Étienne"),), ca.membres_lbi)
    verifier("gardes chez HP", [r[0] for r in con.execute(
        "select identifiant from fiche where identifiant like 'hp/%' order by identifiant")], ["hp/jean-essai", "hp/paul-temoin"])
    con.close()

    print("\nTOUT VERT" if not rouges else f"\n{len(rouges)} ROUGE(S) : {rouges}")
    return 0 if not rouges else 1


if __name__ == "__main__":
    sys.exit(main())
