"""Les NOTAIRES connus du registre des ventes -- pour qu'une fiche notaire ne soit jamais un couple.

⛔ RÈGLE DE FRÉDÉRIC (02/11/2026) : « une fiche type notaire ne peut pas être considérée comme couple,
dans l'historique et dans les ajouts ». Hektor range des études (SCP, SELARL…) en fiches « ménage » :
50 notaires étaient « couple » au 02/11 (44 case vide, 4 aucun lien, 1 sans seconde, 1 par le rattachement).

« Notaire » = la même personne que l'écran appelle notaire (rôle notaire_vendeur / notaire_acquereur,
calculé chez Supabase depuis nos registres). La couche locale ne porte pas ce rôle : on le relit ici dans
sa source locale, `app_affaire_ledger.notaires_json` (entrée = notaire de l'acquéreur, sortie = du mandant,
NUMÉROS HEKTOR). Mesure du 02/11 : 1 280 notaires, dont 1 071 ont une fiche chez nous ; les 50 « couple »
sont les mêmes des deux côtés. Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §23-24.

Lecture seule. Une table absente ou illisible rend un ensemble VIDE (la nuit continue, comme avant).
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

TABLE_REGISTRE = "app_affaire_ledger"


def _ids_du_cote(valeur: Any) -> set[str]:
    elements = valeur if isinstance(valeur, list) else [valeur]
    return {str(e.get("id")).strip() for e in elements
            if isinstance(e, dict) and str(e.get("id") or "").strip()}


def notaires_du_json(texte: Any) -> set[str]:
    """Les numéros Hektor d'un `notaires_json` (entrée et sortie, objet seul ou liste). Fonction PURE."""
    if not texte:
        return set()
    try:
        donnees = json.loads(texte) if isinstance(texte, str) else texte
    except (TypeError, ValueError):
        return set()
    if not isinstance(donnees, dict):
        return set()
    return _ids_du_cote(donnees.get("entree")) | _ids_du_cote(donnees.get("sortie"))


def notaires_hektor(conn: sqlite3.Connection) -> set[str]:
    """Les numéros HEKTOR de tous les notaires du registre des ventes (vide si la table manque)."""
    try:
        lignes = conn.execute(
            f"SELECT notaires_json FROM {TABLE_REGISTRE} "
            "WHERE notaires_json IS NOT NULL AND notaires_json NOT IN ('', '[]', '{{}}')").fetchall()
    except sqlite3.Error:
        return set()
    resultat: set[str] = set()
    for (texte,) in lignes:
        resultat |= notaires_du_json(texte)
    return resultat
