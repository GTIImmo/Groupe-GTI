from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Assistant IA (12/11/2026, étape 1) -- LES TARIFS DES MODÈLES, EN UN SEUL ENDROIT.
#
# USD par jeton (entrée / sortie), pour le coût de chaque tour et le plafond du jour.
# ⚠ Seul l'assistant lit ce module. Le rédacteur (prix fixes) et la GED (_TARIFS dans
#   openai_ged_classement_service) gardent les leurs : les rebrancher ici serait modifier
#   du code existant, à décider à l'étape 6 (coûts).
# Un modèle absent de la table = coût inconnu (None), jamais zéro : le plafond du jour
# ne doit pas croire qu'un tour a été gratuit.
# ---------------------------------------------------------------------------

TARIFS: dict[str, tuple[float, float]] = {
    # 13/11/2026 : le modèle de l'assistant (décision de Frédéric) ; prix de la grille officielle relue ce jour-là
    "gpt-6.1-terra": (1.00 / 1_000_000, 5.00 / 1_000_000),
    "gpt-6-luna": (0.10 / 1_000_000, 0.50 / 1_000_000),
    "gpt-5.6-luna": (0.20 / 1_000_000, 1.20 / 1_000_000),
    "gpt-4.1-mini": (0.40 / 1_000_000, 1.60 / 1_000_000),
}


def cout_usd(model: str | None, usage: dict[str, Any]) -> float | None:
    tarif = TARIFS.get(str(model or ""))
    entree, sortie = usage.get("input_tokens"), usage.get("output_tokens")
    if not tarif or not isinstance(entree, (int, float)) or not isinstance(sortie, (int, float)):
        return None
    return round(entree * tarif[0] + sortie * tarif[1], 6)
