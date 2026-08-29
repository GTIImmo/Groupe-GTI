#!/usr/bin/env python3
"""Lit l'ÉTAT d'une annonce (archive, négociateur) via l'API Hektor — porte 2.

POURQUOI CE SCRIPT, et c'est une leçon du 29/08.

Le worker vérifiait ses gestes en balayant le listing GraphQL
(`fetchHektorPropertyById`). Deux limites mesurées :

  * il ne cherche que dans la famille `SALE` par défaut — une location ou un bien
    professionnel n'y est jamais trouvé ;
  * il pagine jusqu'à 8 pages, et le code porte lui-même la trace de l'incident du
    27/08 : *« l'annonce 62962 a bien été créée, et le job a quand même fini en
    error — après six tentatives et seize pages inutiles chez Hektor »*.

Une lecture ciblée par l'API coûte **une seule requête** et ne dépend d'aucune
famille. C'est le même patron que `annonce_datemaj_from_api.py`, qui existe déjà
parce que le worker n'a pas de JWT.

Sort une ligne JSON :
    {"trouve": true, "archive": "0", "negociateur": "23", "agence": "12"}
    {"trouve": false}                      annonce inconnue (404) ou vide
    {"_error": "..."}                      lecture impossible -- l'appelant DÉCIDE
                                           quoi en faire, ce script ne conclut pas
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
        print(json.dumps({"_error": "annonce-id non numerique"}))
        return 0

    try:
        client = HektorClient(Settings.from_env())
        payload = client.get_json("/Api/Annonce/AnnonceById/", params={"id": aid})
    except Exception as exc:
        texte = str(exc)
        # Un 404 est une REPONSE, pas une panne : l'annonce n'existe plus.
        if "404" in texte:
            print(json.dumps({"trouve": False}))
            return 0
        print(json.dumps({"_error": texte[:200]}, ensure_ascii=False))
        return 0

    annonce = payload.get("annonce") if isinstance(payload, dict) else None
    key_data = annonce.get("keyData") if isinstance(annonce, dict) else None
    if not isinstance(key_data, dict) or not key_data.get("id"):
        print(json.dumps({"trouve": False}))
        return 0

    print(json.dumps({
        "trouve": True,
        "id": str(key_data.get("id") or ""),
        "archive": str(key_data.get("archive") if key_data.get("archive") is not None else ""),
        "negociateur": str(key_data.get("NEGOCIATEUR") if key_data.get("NEGOCIATEUR") is not None else ""),
        "agence": str(key_data.get("agence") if key_data.get("agence") is not None else ""),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
