"""Tests Lot B — suivi email (logique pure, sans DB).

Lancer depuis backend/ :  ../.venv/Scripts/python.exe tests/test_email_tracking.py
"""
import os, sys
from types import SimpleNamespace
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services import email_tracking as ET

# 1) Garde-fou preview vs envoi réel
assert ET.is_real_envoi_id("12345678-1234-1234-1234-123456789abc") is True
assert ET.is_real_envoi_id("preview") is False
assert ET.is_real_envoi_id("") is False
assert ET.is_real_envoi_id(None) is False
print("1) is_real_envoi_id OK")

# 2) hash_ip déterministe, None-safe
assert ET.hash_ip(None) is None
h = ET.hash_ip("1.2.3.4")
assert h and h == ET.hash_ip("1.2.3.4") and len(h) == 32
assert ET.hash_ip("1.2.3.5") != h
print("2) hash_ip OK")

# 3) Scoring : clic fort / ouverture faible
svc = ET.EmailTrackingService(SimpleNamespace(
    email_tracking_secret="s", email_tracking_base_url="https://api.gti.fr",
    app_base_url="https://app.gti.fr", supabase_service_role_key="srk",
))
sf = svc.score_from_events
assert sf([{"type": "like"}]) == "chaud"
assert sf([{"type": "visite"}]) == "chaud"
assert sf([{"type": "open"}, {"type": "like"}]) == "chaud"      # like prime sur open
assert sf([{"type": "open"}]) == "tiede"                          # ouverture = signal faible
assert sf([{"type": "pass"}]) == "tiede"                          # ✕ = engagement sans intérêt
assert sf([]) == "froid"
print("3) scoring chaud/tiède/froid OK")

# 4) En-têtes List-Unsubscribe + List-Unsubscribe-Post (1-clic)
hdr = svc.list_unsubscribe_headers("12345678-1234-1234-1234-123456789abc")
assert hdr["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
assert "https://api.gti.fr/r/u/" in hdr["List-Unsubscribe"]
assert "mailto:postmaster@gti-immobilier.fr" in hdr["List-Unsubscribe"]
# sans base d'URL : on garde au moins le mailto, sans le header one-click
svc2 = ET.EmailTrackingService(SimpleNamespace(
    email_tracking_secret="s", email_tracking_base_url=None, app_base_url=None, supabase_service_role_key="srk"))
hdr2 = svc2.list_unsubscribe_headers("12345678-1234-1234-1234-123456789abc")
assert "mailto:" in hdr2["List-Unsubscribe"] and "List-Unsubscribe-Post" not in hdr2
print("4) List-Unsubscribe OK")

print("\nTOUS LES TESTS LOT B PASSENT ✅")
