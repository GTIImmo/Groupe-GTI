#!/usr/bin/env python3
"""Lit la date_maj FRAÎCHE d'une annonce via l'API Hektor (porte 2 / AnnonceById).

Léger : JUSTE l'appel API + extraction de la date_maj. AUCUN re-sync, AUCUNE
écriture locale ni Supabase. Réutilise le client Python qui a déjà le JWT OAuth
(porte 2), comme le run quotidien. Miroir de contact_datemaj_from_api.py.

Utilisé par le garde-fou anti-écrasement annonce (Tier 2) côté worker, qui
faisait jusque-là un appel Node direct → 403 « You must be logged in » (le worker
n'a pas de JWT), donc ne bloquait jamais.

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
    ap.add_argument("--annonce-id", required=True)
    args = ap.parse_args()
    aid = str(args.annonce_id).strip()
    if not aid.isdigit():
        print("{}")
        return 0
    try:
        settings = Settings.from_env()
        client = HektorClient(settings)
        payload = client.get_json("/Api/Annonce/AnnonceById/", params={"id": aid})
    except Exception as exc:  # best-effort : sur erreur on ne bloque pas l'écriture
        print(json.dumps({"_error": str(exc)[:200]}, ensure_ascii=False))
        return 0
    # Structure réelle (cf. refresh_annonce_nego_from_api.py) : annonce.keyData.datemaj
    annonce = payload.get("annonce") if isinstance(payload, dict) else None
    key_data = annonce.get("keyData") if isinstance(annonce, dict) else None
    datemaj = None
    if isinstance(key_data, dict):
        datemaj = key_data.get("datemaj") or key_data.get("date_maj")
    print(json.dumps({"datemaj": datemaj} if datemaj else {}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
