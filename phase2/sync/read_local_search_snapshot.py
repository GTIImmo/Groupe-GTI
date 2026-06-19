#!/usr/bin/env python3
"""Lit l'état Hektor FRAIS d'une recherche dans la base locale (phase2.sqlite).

Utilisé par le garde-fou anti-écrasement pour un push 'from_pending' (affinage
Supabase-first) : après le refresh (Hektor -> local), le push saute la recherche
dirty, donc Supabase garde l'état optimiste (affiné). Pour comparer la "base"
(état pré-affinage) à l'état Hektor RÉEL, on lit ici le local (que sync_contact_details
+ build_contacts_layer viennent de remplir avec la version Hektor courante).

Sort une ligne JSON : le snapshot des colonnes (mêmes clés que SNAPSHOT_KEYS côté
backend), ou {} si la recherche est introuvable.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
SNAPSHOT_KEYS = (
    "offre", "types_json", "villes_json", "surface_terrain_min", "criteres_json",
    "prix_min", "prix_max", "surface_min", "pieces_min", "chambre_min",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contact-id", required=True)
    parser.add_argument("--search-index", type=int, default=0)
    parser.add_argument("--phase2-db", type=Path, default=DEFAULT_PHASE2_DB)
    args = parser.parse_args()

    conn = sqlite3.connect(str(args.phase2_db))
    conn.row_factory = sqlite3.Row
    try:
        columns = ", ".join(SNAPSHOT_KEYS)
        row = conn.execute(
            f"SELECT {columns} FROM app_contact_search_current "
            "WHERE hektor_contact_id = ? AND search_index = ? LIMIT 1",
            (str(args.contact_id), int(args.search_index)),
        ).fetchone()
    finally:
        conn.close()

    print(json.dumps(dict(row) if row else {}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
