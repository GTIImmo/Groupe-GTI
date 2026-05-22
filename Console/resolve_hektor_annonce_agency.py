from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "hektor.sqlite"


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve the agency user context required for a Hektor annonce.")
    parser.add_argument("--annonce-id", required=True)
    args = parser.parse_args()

    annonce_id = str(args.annonce_id).strip()
    if not annonce_id:
        raise SystemExit("annonce-id is required")

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            """
            SELECT
                a.hektor_annonce_id,
                a.hektor_agence_id,
                ag.nom,
                ag.mail,
                ag.raw_json
            FROM hektor_annonce a
            LEFT JOIN hektor_agence ag ON ag.hektor_agence_id = a.hektor_agence_id
            WHERE a.hektor_annonce_id = ?
            LIMIT 1
            """,
            (annonce_id,),
        ).fetchone()
        if not row:
            print(json.dumps({"found": False}, ensure_ascii=True))
            return 0

        raw = {}
        try:
            raw = json.loads(row["raw_json"] or "{}")
        except Exception:
            raw = {}

        id_user = str(raw.get("idUser") or "").strip()
        print(
            json.dumps(
                {
                    "found": True,
                    "hektor_annonce_id": str(row["hektor_annonce_id"] or ""),
                    "hektor_agence_id": str(row["hektor_agence_id"] or ""),
                    "agency_id_user": id_user or None,
                    "agency_label": row["nom"],
                    "agency_email": row["mail"],
                },
                ensure_ascii=True,
            )
        )
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
