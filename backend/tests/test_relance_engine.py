"""Tests Lot C — moteur de décision des relances (pur).

Lancer depuis backend/ :  ../.venv/Scripts/python.exe tests/test_relance_engine.py
Vérifie les garde-fous : plafond, arrêt terminal, opt-out, clic-sans-RDV, J+2/J+3.
"""
import os, sys
from datetime import UTC, datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.relance_engine import decide_relance

NOW = datetime(2026, 6, 17, 12, 0, 0, tzinfo=UTC)


def env(**kw):
    base = {"statut": "envoye", "open_count": 0, "click_count": 0, "relances_count": 0,
            "sent_at": (NOW - timedelta(days=5)).isoformat(), "rdv_at": None, "replied_at": None,
            "unsubscribed_at": None}
    base.update(kw)
    return base


def act(**kw):
    return decide_relance(env(**kw), NOW, max_relances=2)["action"], decide_relance(env(**kw), NOW, max_relances=2)["reason"]


# Arrêt immédiat : statuts terminaux
for s in ("refuse", "rdv", "repondu", "desinscrit"):
    a, r = act(statut=s)
    assert a == "skip" and ("terminal" in r or r == "opt_out"), (s, a, r)
assert act(replied_at=NOW.isoformat())[0] == "skip"
assert act(unsubscribed_at=NOW.isoformat())[1] == "opt_out"
print("1) arrêt terminal / opt-out OK")

# Plafond de relances
assert act(relances_count=2, open_count=0)[1] == "plafond_atteint"
assert act(relances_count=5)[1] == "plafond_atteint"
print("2) plafond relances OK")

# Clic « ça m'intéresse » sans RDV -> alerte humaine, jamais d'auto-relance
assert decide_relance(env(statut="interesse", click_count=1), NOW)["action"] == "alert_human"
assert decide_relance(env(click_count=1, statut="clique"), NOW)["action"] == "alert_human"
print("3) clic sans RDV -> alerte humaine OK")

# Pas d'ouverture à J+2 -> relance 'no_open'
d = decide_relance(env(open_count=0, sent_at=(NOW - timedelta(days=2)).isoformat()), NOW)
assert d["action"] == "send" and d["type"] == "no_open", d
# mais pas avant J+2
assert decide_relance(env(open_count=0, sent_at=(NOW - timedelta(days=1)).isoformat()), NOW)["action"] == "skip"
print("4) relance J+2 sans ouverture OK")

# Ouvert sans clic à J+3 -> relance 'soft'
d = decide_relance(env(open_count=2, click_count=0, sent_at=(NOW - timedelta(days=3)).isoformat()), NOW)
assert d["action"] == "send" and d["type"] == "soft", d
# mais pas à J+2
assert decide_relance(env(open_count=2, click_count=0, sent_at=(NOW - timedelta(days=2)).isoformat()), NOW)["action"] == "skip"
print("5) relance J+3 ouvert sans clic OK")

print("\nTOUS LES TESTS LOT C PASSENT ✅")
