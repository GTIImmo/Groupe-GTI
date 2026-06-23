#!/usr/bin/env python3
"""Lit la date_maj FRAÎCHE d'un contact via l'API Hektor (porte 2 / ContactById).

Léger : JUSTE l'appel API + extraction de la date_maj. AUCUN re-sync, AUCUNE
écriture locale ni Supabase (contrairement à refresh_contact_inproc.py qui, lui,
delete+upsert et effacerait un contact dirty). Réutilise le client Python qui a
déjà le JWT OAuth (porte 2), comme le run quotidien.

Utilisé par le garde-fou anti-écrasement contact (Lot B) côté worker.
Sort une ligne JSON {"datemaj": "..."} ou {} si introuvable/erreur (best-effort).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hektor_pipeline.common import HektorClient, Settings  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contact-id", required=True)
    args = ap.parse_args()
    cid = str(args.contact_id).strip()
    if not cid.isdigit():
        print("{}")
        return 0
    try:
        settings = Settings.from_env()
        client = HektorClient(settings)
        payload = client.get_json("/Api/Contact/ContactById", params={"id": cid, "version": settings.api_version})
    except Exception as exc:  # best-effort : sur erreur on ne bloque pas l'écriture
        print(json.dumps({"_error": str(exc)[:200]}, ensure_ascii=False))
        return 0
    data = payload.get("data") if isinstance(payload, dict) else None
    contact = data.get("contact") if isinstance(data, dict) else None
    datemaj = None
    if isinstance(contact, dict):
        datemaj = contact.get("datemaj") or contact.get("date_maj")
    print(json.dumps({"datemaj": datemaj} if datemaj else {}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
