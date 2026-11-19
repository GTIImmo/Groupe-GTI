"""Étape 4 chap. 6, P4-a (19/11/2026) -- LA TRADUCTION DU SERVEUR RÉPOND COMME LA FENÊTRE.

parcours_traduction.json est PRODUIT par le vrai code de la fenêtre (apps/hektor-v1/parcours_traduction.cjs) avec un jeu
d'exemples : ce que rendent les fonctions de la fenêtre. Cet essai exige que le serveur rende EXACTEMENT la même chose,
puis traduit une lecture complète et vérifie chaque case.
Lancement : python tests/test_parcours_traduction.py (depuis backend/). Sortie 0 = vert.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import assistant_parcours as moteur  # noqa: E402
from app.services import parcours_traduction as tr  # noqa: E402

ok = 0


def voir(vrai, libelle, detail=""):
    global ok
    if not vrai:
        print(f"  ROUGE {libelle}  {detail}")
        sys.exit(1)
    ok += 1
    print(f"  VERT  {libelle}")


def comparer(nom, exemples, fonction):
    ecarts = [(e, attendu, fonction(e)) for e, attendu in exemples if fonction(e) != attendu]
    voir(not ecarts and len(exemples) > 0, f"{nom} : {len(exemples)} exemples, les MÊMES réponses que la fenêtre",
         str(ecarts[:5]))


print("1) les fonctions du serveur répondent comme celles de la fenêtre (jeu d'exemples produit par App.tsx)")
ex = tr.DONNEES["exemples"]
comparer("normaliser", ex["normaliser"], tr.normaliser)
comparer("oui / non", ex["oui_non"], tr.oui_non)
comparer("type de bien", ex["type_bien"], tr.type_de_bien)
comparer("type de pièce", ex["piece"], tr.type_de_piece)
listes = {**tr.DONNEES["listes"], **{e["fenetre"]: e["options"] for e in tr.DONNEES["carte"] if e.get("options")}}
for nom, exemples in ex["listes"].items():
    comparer(f"liste « {nom} »", exemples, lambda t, o=listes[nom]: tr.option(t, o))

print("2) une lecture complète, traduite")
lecture = {
    "propertyType": "grande maison", "address": "12 rue des Tilleuls", "postalCode": "42700", "city": "Firminy",
    "surface": "118,5", "roomCount": "5", "bedroomCount": "3", "landSurface": "612", "garden": "oui", "pool": "non",
    "exposure": "S", "kitchen": "séparée", "elevator": "non", "heatingEnergy": "gaz", "constructionYear": "1975",
    "price": "245000", "title": "Maison familiale", "note": "RDV 14 h",
}
r = tr.traduire(lecture, [{"type": "Cuisine", "surface": "12,5", "etage": "", "detail": ""},
                          {"type": "véranda vitrée", "surface": "", "etage": "", "detail": ""},
                          {"type": "machin", "surface": "", "etage": "", "detail": ""}])
voir(r["type"] == "1" and r["offre_famille"] == "0", "« grande maison » -> le type Maison (1), vente ordinaire")
voir(r["adresse_haut"] == "12 rue des Tilleuls" and r["adresse"] == "12 rue des Tilleuls" and r["cp"] == "42700"
     and r["codeprive"] == r["codepublique"] == "42700" and r["villeprivee"] == r["villepublique"] == "Firminy",
     "l'adresse du haut ET les adresses privée / publique (§89 D6)")
voir(r["surfappart"] == "118.5" and r["nbpieces"] == "5" and r["NB_CHAMBRES"] == "3" and r["surfterrain"] == "612",
     "les nombres par le miroir, la virgule devient un point")
voir(r["JARDIN-"] == "OUI" and r["PISCINE-"] == "NON" and r["ASCENSEUR"] == "NON", "oui / non")
voir(r["EXPOSITION"] == "SUD", "l'exposition en lettres (« S ») -> SUD", r.get("EXPOSITION"))
voir(r.get("CUISINE", "") != "" and r["prix"] == "245000" and r["titre"] == "Maison familiale" and r["note"] == "RDV 14 h",
     "la cuisine (liste), le prix, le titre, la note")
voir(r["ANNEE_CONS"] == "1975", "l'année de construction (miroir)")
pieces = r["composition"]
voir(len(pieces) == 3 and pieces[0]["idTypePiece"] == "13" and pieces[0]["surfacePiece"] == "12.5"
     and pieces[1]["idTypePiece"] == "20" and pieces[2]["idTypePiece"] == "" and pieces[2]["detailPiece"] == "machin",
     "les pièces : cuisine, véranda reconnue, une inconnue gardée par son nom (§89 D4)", str(pieces))

print("3) la traduction ne parle QUE la langue du parcours, sans coordonnée")
toutes = {c for q in moteur.QUESTIONS for c in q["champs"]}
cases_scan = [e["scan"] for e in tr.DONNEES["carte"]] + list(tr.DONNEES["miroir"].values()) + list(tr.DONNEES["directes"])
complete = tr.traduire({c: "1" for c in cases_scan} | {"propertyType": "maison", "exposure": "sud", "kitchen": "américaine"})
hors = sorted(set(complete) - toutes)
# Trois cases que le scan remplit mais que la fenêtre ne MONTRE pour aucun type de bien (absentes de
# draftAnnonceWizardFieldsByProfile et des cases communes, vérifié le 19/11) ; à la création elle les retire
# (filterDraftAnnonceWizardFieldsForProfile). Le moteur du parcours ne garde que les cases de ses questions : pareil.
JAMAIS_MONTREES = {"TAXE_HABITATION", "cable", "gardien"}
voir(set(hors) == JAMAIS_MONTREES, f"chaque case traduite ({len(complete)}) est une case du parcours, sauf les 3 que la "
     "fenêtre ne montre jamais", str(hors))
voir(not (set(complete) & moteur.COORDONNEES), "aucune coordonnée de mandant")
voir(tr.traduire({}) == {} and tr.traduire({"propertyType": "zzz"}) == {}, "rien de dit -> rien de traduit")

print(f"\nTOUT EST VERT ({ok} contrôles)")
