"""Moteur de décision des relances (Lot C) — logique PURE, sans IO.

Décide, pour un envoi donné et l'instant présent, l'action de relance :
- 'skip'        : ne rien faire (avec une raison : attente, plafond, terminal, opt-out…)
- 'send'        : envoyer une relance (avec un type : no_open / soft)
- 'alert_human' : ne PAS relancer automatiquement, remonter au négociateur (clic sans RDV)

Garde-fous (indépendants du DNS) :
- Plafond de N relances par envoi (défaut 2).
- Arrêt immédiat si réponse / RDV / refus / désinscription (statuts terminaux).
- Jamais de relance si désinscrit (unsubscribed_at).
- Déclenché sur ABSENCE d'événement (jamais « juste le temps ») :
    * pas d'ouverture à J+2  -> relance 'no_open' (objet différent)
    * ouvert sans clic à J+3 -> relance 'soft' (angle nouveau)
    * cliqué (intéressé) sans RDV -> alerte humaine (pas d'auto-relance)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

# Statuts terminaux : toute relance s'arrête.
TERMINAL_STATUTS = {"refuse", "rdv", "repondu", "desinscrit"}

NO_OPEN_DELAY_DAYS = 2
SOFT_DELAY_DAYS = 3


def _age_days(envoi: dict[str, Any], now: datetime) -> float:
    ref = envoi.get("sent_at") or envoi.get("created_at")
    if not ref:
        return 0.0
    try:
        ts = datetime.fromisoformat(str(ref).replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=now.tzinfo)
    return (now - ts).total_seconds() / 86400.0


def decide_relance(
    envoi: dict[str, Any],
    now: datetime,
    *,
    max_relances: int = 2,
) -> dict[str, str]:
    """Retourne {action, type, reason}. IO et envoi gérés par le worker."""
    statut = (envoi.get("statut") or "").strip()

    if envoi.get("unsubscribed_at") or statut == "desinscrit":
        return {"action": "skip", "type": "", "reason": "opt_out"}
    if statut in TERMINAL_STATUTS:
        return {"action": "skip", "type": "", "reason": f"terminal:{statut}"}
    if envoi.get("replied_at"):
        return {"action": "skip", "type": "", "reason": "terminal:repondu"}
    if int(envoi.get("relances_count") or 0) >= max_relances:
        return {"action": "skip", "type": "", "reason": "plafond_atteint"}

    open_count = int(envoi.get("open_count") or 0)
    click_count = int(envoi.get("click_count") or 0)
    age = _age_days(envoi, now)

    # Cliqué « ça m'intéresse » mais pas de RDV -> contact humain, jamais d'auto-relance.
    if statut == "interesse" or (click_count > 0 and not envoi.get("rdv_at")):
        return {"action": "alert_human", "type": "clic_sans_rdv", "reason": "signal_fort_sans_rdv"}

    # Pas d'ouverture à J+2 -> relance avec objet différent.
    if open_count == 0 and age >= NO_OPEN_DELAY_DAYS:
        return {"action": "send", "type": "no_open", "reason": "pas_d_ouverture_J+2"}

    # Ouvert sans clic à J+3 -> relance plus douce, angle nouveau.
    if open_count > 0 and click_count == 0 and age >= SOFT_DELAY_DAYS:
        return {"action": "send", "type": "soft", "reason": "ouvert_sans_clic_J+3"}

    return {"action": "skip", "type": "", "reason": "attente"}
