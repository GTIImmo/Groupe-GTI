from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List

from hektor_pipeline.common import HektorClient, Settings


ENDPOINTS: List[Dict[str, Any]] = [
    {"name": "agences", "path": "/Api/Agence/ListAgences/", "params": {"page": 0}},
    {"name": "negos", "path": "/Api/Negociateur/listNegos/", "params": {"page": 0, "actif": 1}},
    {"name": "annonces", "path": "/Api/Annonce/ListAnnonces/", "params": {"page": 0}},
    {"name": "contacts", "path": "/Api/Contact/ListContacts/", "params": {"page": 0, "archive": 0}},
    {"name": "mandats", "path": "/Api/Mandat/ListMandat", "params": {"page": 0, "beginDate": "2020-01-01", "endDate": "2030-12-31"}},
    {"name": "offres", "path": "/Api/Offre/ListOffres/", "params": {"page": 0, "withOfferStatus": "false"}},
    {"name": "compromis", "path": "/Api/Vente/ListCompromis/", "params": {"page": 0, "withCompromisStatus": "false"}},
    {"name": "ventes", "path": "/Api/Vente/ListVentes/", "params": {"page": 0, "dateStart": "2020-01-01", "dateEnd": "2030-12-31"}},
    {"name": "broadcasts", "path": "/Api/Passerelle/DetailedBroadcastList/", "params": {"page": 0}},
]


def summarize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = payload.get("data")
    metadata = payload.get("metadata")

    summary: Dict[str, Any] = {
        "data_type": type(data).__name__,
        "count": len(data) if isinstance(data, list) else (1 if isinstance(data, dict) else 0),
        "meta_total": metadata.get("total") if isinstance(metadata, dict) else None,
    }

    if isinstance(data, list) and data and isinstance(data[0], dict):
        summary["sample_keys"] = sorted(data[0].keys())
        summary["sample_preview"] = {k: data[0].get(k) for k in list(data[0].keys())[:8]}
    elif isinstance(data, dict):
        summary["sample_keys"] = sorted(data.keys())
        summary["sample_preview"] = {k: data.get(k) for k in list(data.keys())[:8]}

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick Hektor API probe.")
    parser.add_argument("--endpoint", choices=[e["name"] for e in ENDPOINTS], help="Probe only one endpoint.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    settings = Settings.from_env()
    client = HektorClient(settings)
    client.authenticate()

    chosen = [e for e in ENDPOINTS if not args.endpoint or e["name"] == args.endpoint]
    results: Dict[str, Any] = {}

    for endpoint in chosen:
        params = dict(endpoint["params"])
        params["version"] = settings.api_version
        payload = client.get_json(endpoint["path"], params=params)
        results[endpoint["name"]] = summarize_payload(payload)

    if args.pretty:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(results, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
