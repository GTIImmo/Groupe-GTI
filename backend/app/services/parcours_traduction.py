"""Étape 4 chap. 6, P4-a (19/11/2026) -- TRADUIRE la lecture de l'IA (clés du SCAN) dans la langue de la FENÊTRE.

La carte « créer » d'aujourd'hui range ce que la personne a dit dans les clés du scan de la fiche papier
(openai_listing_sheet_service.FIELD_KEYS) ; la fenêtre les pose avec son remplisseur (App.tsx, applyDraftAnnonceScan).
Le parcours guidé, lui, parle la langue de la FENÊTRE (noms de ses cases). Décision « A » de Frédéric (19/11) : la
traduction vit ICI, côté serveur, pour que le parcours démarre déjà rempli.

⛔ Rien n'est recopié à la main : les tables et les listes viennent de `parcours_traduction.json`, PRODUIT par le vrai
code de la fenêtre (apps/hektor-v1/parcours_traduction.cjs, qui vérifie aussi qu'il est à jour). Les cinq petites
fonctions ci-dessous refont celles de la fenêtre ; l'essai (tests/test_parcours_traduction.py) exige les MÊMES réponses
que la fenêtre sur le jeu d'exemples du fichier.
⛔ Jamais les coordonnées d'un mandant : la lecture de l'IA ne les porte pas (CASES_CREATION les exclut).
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

DONNEES: dict[str, Any] = json.loads((Path(__file__).with_name("parcours_traduction.json")).read_text(encoding="utf-8"))

# P2 (§89, D6) : le haut de la fenêtre et son adresse privée / publique portent la même rue, le même code postal, la
# même ville -- le parcours les remplit tous (ParcoursGuide.tsx, RECOPIES, fait la même chose à l'écran).
RECOPIES = {"adresse_haut": ("adresse",), "cp": ("codeprive", "codepublique"), "ville": ("villeprivee", "villepublique")}


def normaliser(valeur: Any) -> str:
    """normalizeDraftAnnonceScanText : sans accents, sans espaces au bord, en minuscules, espaces simples."""
    t = unicodedata.normalize("NFD", "" if valeur is None else str(valeur))
    t = "".join(c for c in t if not 0x300 <= ord(c) <= 0x36F)
    return re.sub(r"\s+", " ", t.strip().lower())


def oui_non(brut: Any) -> str:
    """toOuiNon du remplisseur : « oui / avec / 1 » -> OUI, « non / sans / 0 » -> NON, sinon rien."""
    t = str(brut or "").strip().lower()
    if not t:
        return ""
    if t.startswith("o") or "oui" in t or "avec" in t or t == "1":
        return "OUI"
    if t.startswith("n") or "non" in t or "sans" in t or t == "0":
        return "NON"
    return ""


def option(texte: Any, options: list[dict[str, str]]) -> str:
    """resolveWizardOptionValue : le libellé exact, sinon le premier qui contient l'autre ; inconnu -> vide."""
    norm = normaliser(texte)
    if not norm:
        return ""
    for o in options:
        if o.get("value") and normaliser(o.get("label")) == norm:
            return str(o["value"])
    for o in options:
        lib = normaliser(o.get("label"))
        if o.get("value") and lib and (lib in norm or norm in lib):
            return str(o["value"])
    return ""


def type_de_bien(libelle: Any) -> str:
    """draftAnnoncePropertyTypeIdFromLabel : anciens libellés, libellé exact, libellé contenu, puis synonymes."""
    norm = normaliser(libelle)
    if not norm:
        return ""
    for item in DONNEES["types_bien_anciens"]:
        if any(norm == l or l in norm for l in item["labels"]):
            return str(item["id"])
    for t in DONNEES["types_bien"]:
        if normaliser(t["label"]) == norm:
            return str(t["id"])
    for t in DONNEES["types_bien"]:
        lib = normaliser(t["label"])
        if len(lib) >= 3 and (lib in norm or norm in lib):
            return str(t["id"])
    mots = norm.split(" ")
    for item in DONNEES["types_bien_synonymes"]:
        if any(norm == k or k in mots or (len(k) > 4 and k in norm) for k in item["keys"]):
            return str(item["id"])
    return ""


def type_de_piece(libelle: Any) -> str:
    """compositionPieceTypeIdFromLabel : le libellé exact, sinon le premier qui contient l'autre."""
    norm = normaliser(libelle)
    if not norm:
        return ""
    for o in DONNEES["types_piece"]:
        if normaliser(o["label"]) == norm:
            return str(o["value"])
    for o in DONNEES["types_piece"]:
        lib = normaliser(o["label"])
        if lib and (norm in lib or lib in norm):
            return str(o["value"])
    return ""


def _virgule(v: str) -> str:
    return v.replace(",", ".", 1)  # comme `.replace(',', '.')` en JavaScript : la PREMIÈRE seulement


def traduire(cases: dict[str, Any], composition: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """La lecture de l'IA (clés du scan) -> les réponses du parcours (cases de la fenêtre), comme le remplisseur."""
    v = {k: str(x or "").strip() for k, x in (cases or {}).items()}
    sortie: dict[str, Any] = {}

    def poser(nom: str, valeur: str) -> None:
        if valeur:
            sortie[nom] = valeur

    directes = DONNEES["directes"]
    for cle in ("title", "address", "postalCode", "city", "note", "description", "works", "chargesDetail"):
        if directes.get(cle):
            poser(directes[cle], v.get(cle, ""))
    type_id = type_de_bien(v.get("propertyType"))
    if type_id:
        sortie["type"] = type_id
        sortie["offre_famille"] = "0"  # une lecture est résidentielle : vente ordinaire (comme le scan)
    poser("JARDIN-", oui_non(v.get("garden")))
    poser("PISCINE-", oui_non(v.get("pool")))
    for e in DONNEES["carte"]:
        brut = v.get(e["scan"], "")
        if not brut:
            continue
        sorte = e["sorte"]
        valeur = oui_non(brut) if sorte == "ouinon" else _virgule(brut) if sorte == "num" \
            else option(brut, e["options"]) if sorte == "enum" and e.get("options") else brut
        poser(e["fenetre"], valeur)
    for nom, cle in DONNEES["miroir"].items():
        if v.get(cle):
            sortie[nom] = _virgule(v[cle])
    expo = v.get("exposure", "")
    poser("EXPOSITION", option(DONNEES["expo_lettres"].get(expo.upper()) or expo, DONNEES["listes"]["exposition"]))
    poser("CUISINE", option(v.get("kitchen"), DONNEES["listes"]["cuisine"]))
    poser("etat_interieur", option(v.get("interiorState"), DONNEES["listes"]["etat_interieur"]))
    poser("etat_exterieur", option(v.get("exteriorState"), DONNEES["listes"]["etat_exterieur"]))
    for source, cibles in RECOPIES.items():
        if sortie.get(source):
            for cible in cibles:
                sortie.setdefault(cible, sortie[source])
    pieces = []
    for p in composition or []:
        libelle = str(p.get("type") or "").strip()
        detail = str(p.get("detail") or "").strip()
        piece = {"idTypePiece": type_de_piece(libelle), "typeLabel": libelle, "detailPiece": detail,
                 "etagePiece": str(p.get("etage") or "").strip(),
                 "surfacePiece": _virgule(str(p.get("surface") or "")).strip(), "notePublique": str(p.get("note") or "").strip()}
        if not piece["idTypePiece"]:
            piece["detailPiece"] = detail or libelle  # §89 D4 : un type non reconnu reste à choisir, son nom est gardé
        if any(piece[k] for k in ("idTypePiece", "detailPiece", "etagePiece", "surfacePiece", "notePublique")):
            pieces.append(piece)
    if pieces:
        sortie["composition"] = pieces
    return sortie
