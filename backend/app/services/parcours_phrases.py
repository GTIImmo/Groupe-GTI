"""Le parcours guidé, P4-d (20/11/2026) : LES PHRASES LIBRES, lues tout de suite par le petit lecteur.

Ses décisions du 20/11 : la phrase se tape (ou se dicte) dans la ZONE DU BAS pendant qu'une question est ouverte (une
pastille « Pour : <la question> ✕ » le montre ; ✕ renvoie le message à l'assistant) ; elle est lue TOUT DE SUITE.
Ce qu'il en est fait (maquette v27, planches 6 et 7) :
  - ce qui touche la QUESTION OUVERTE remplit sa carte (rendu à l'écran, PAS gardé : la personne valide elle-même) ;
  - ce qui touche une AUTRE question est pré-rempli « dit » (source « phrase »), JAMAIS à la place d'une réponse ;
  - ce qui ne rentre dans aucune case va dans la NOTE de la fenêtre, comme le scan (ajouté aux phrases d'avant, jamais à
    la place d'une note dite ou lue) ;
  - la phrase reste affichée « gardée » sous sa question.
⛔ AVANT le modèle, les téléphones et les e-mails sont RETIRÉS de la phrase (règle du 18/11 : les coordonnées ne passent
   jamais par l'IA ; règle : l'e-mail d'une personne ne part jamais chez OpenAI). Un nom de vendeur lu par le lecteur
   n'est PAS gardé : il est masqué dans la phrase gardée et la personne est renvoyée aux cases protégées.
⛔ Le texte de la phrase ne va jamais dans le journal des agents (app_agent_run : jetons et coût seulement).

Note : notice/ETAPE4_ECRAN_ACCUEIL_ASSISTANT_AUDIT_2026-11-16.md §99.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable

from . import assistant_parcours as moteur
from . import parcours_traduction

MAX_PHRASE = 1000       # caractères d'une phrase
MAX_PHRASES = 40        # phrases gardées par parcours
MASQUE = "[coordonnée retirée]"
MASQUE_NOM = "[vendeur]"

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.UNICODE)
# Les numéros français : 06 12 34 56 78, 06.12.34.56.78, 0612345678, +33 6 12 34 56 78, 0033 6…
_TELEPHONE = re.compile(r"(?<!\d)(?:\+\s?33\s?\(?0?\)?|0033\s?|0)\s?[1-9](?:[\s.\-]?\d{2}){4}(?!\d)")


def retirer_coordonnees(texte: str) -> tuple[str, int]:
    """La phrase sans e-mail ni téléphone, et combien en ont été retirés."""
    n = 0

    def _compte(_m: re.Match[str]) -> str:
        nonlocal n
        n += 1
        return MASQUE

    propre = _EMAIL.sub(_compte, texte)
    propre = _TELEPHONE.sub(_compte, propre)
    return propre, n


def nettoyer(texte: Any) -> str:
    t = " ".join(str(texte or "").split())
    if not t:
        raise moteur.RefusParcours("Phrase vide.")
    if len(t) > MAX_PHRASE:
        raise moteur.RefusParcours(f"Phrase trop longue ({len(t)} caractères, {MAX_PHRASE} au plus) : coupe-la en deux.")
    return t


def lire(texte_propre: str, question_titre: str, extraire: Callable[[str, str], dict[str, Any]]) -> dict[str, Any]:
    """Le petit lecteur (le format du scan), puis la même traduction que la fiche de visite."""
    extraction = extraire(texte_propre, question_titre)
    return {"lecture": parcours_traduction.lire_fiche(parcours_traduction.fusionner_pages([extraction])),
            "model": extraction.get("model"), "usage": extraction.get("usage")}


def appliquer(reponses: dict[str, Any], question_id: str, texte_propre: str, lecture: dict[str, Any], annee: int,
              cout_usd: float | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Fonction pure : rend (les nouvelles réponses, les cases pour la CARTE de la question ouverte, ce qu'il faut dire).
    Ne remplace jamais une réponse ; ne garde jamais une coordonnée."""
    question = moteur.PAR_ID.get(question_id)
    if not question:
        raise moteur.RefusParcours("Question inconnue.")
    valeurs = {k: v for k, v in (lecture.get("valeurs") or {}).items()
               if not k.startswith("_") and k not in moteur.COORDONNEES and k != "photos"}
    doutes = dict(lecture.get("doutes") or {})
    reste = str(valeurs.pop("note", "") or "").strip()
    # 1) la question ouverte : rendu à l'écran, la personne valide
    carte = {k: v for k, v in valeurs.items() if k in question["champs"] and v not in (None, "", [])}
    autres = {k: v for k, v in valeurs.items() if k not in carte}
    # 2) les autres questions : pré-remplies « dit », jamais à la place d'une réponse
    avant = {k for k, v in reponses.items() if not k.startswith("_") and v not in (None, "", [])}
    nouvelles = moteur.appliquer_depart(reponses, autres, "phrase", annee, {k: v for k, v in doutes.items() if k in autres})
    remplies = sorted(k for k, v in nouvelles.items() if not k.startswith("_") and k not in avant and v not in (None, "", []))
    # 3) ce qui ne rentre dans aucune case : la note de la fenêtre (ajoutée aux phrases d'avant, jamais sur une note dite)
    note = False
    if reste:
        sources = dict(nouvelles.get(moteur.CLE_SOURCES) or {})
        actuelle = str(nouvelles.get("note") or "").strip()
        if not actuelle or sources.get("note") == "phrase":
            nouvelles["note"] = (actuelle + "\n" + reste).strip()[:moteur.MAX_VALEUR] if actuelle else reste[:moteur.MAX_VALEUR]
            sources["note"] = "phrase"
            nouvelles[moteur.CLE_SOURCES] = sources
            note = True
    # 4) un nom de vendeur lu n'est pas gardé : masqué dans la phrase gardée
    coordonnees = {k: str(v) for k, v in (lecture.get("coordonnees") or {}).items() if str(v or "").strip()}
    gardee = texte_propre
    for valeur in sorted(coordonnees.values(), key=len, reverse=True):
        if len(valeur) >= 2:
            gardee = re.sub(re.escape(valeur), MASQUE_NOM, gardee, flags=re.IGNORECASE)
    phrases = [p for p in nouvelles.get(moteur.CLE_PHRASES) or [] if isinstance(p, dict)]
    if len(phrases) >= MAX_PHRASES:
        raise moteur.RefusParcours(f"{MAX_PHRASES} phrases déjà gardées pour ce parcours : réponds avec les boutons.")
    phrases.append({"question": question_id, "texte": gardee, "le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "carte": sorted(carte), "remplies": remplies, "note": note,
                    **({"cout_usd": round(cout_usd, 6)} if cout_usd is not None else {})})
    nouvelles[moteur.CLE_PHRASES] = phrases
    dire = {"carte": len(carte), "remplies": len(remplies), "note": note, "vendeur": bool(coordonnees)}
    return nouvelles, carte, dire
