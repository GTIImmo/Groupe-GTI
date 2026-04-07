from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patche localement une annonce phase 1 par hektor_annonce_id.")
    parser.add_argument("--id-annonce", required=True, help="ID Hektor de l'annonce")
    parser.add_argument("--valide", choices=["0", "1"], required=True, help="Valeur locale du champ valide")
    parser.add_argument("--diffusable", choices=["0", "1"], required=True, help="Valeur locale du champ diffusable")
    parser.add_argument("--archive", choices=["0", "1"], default=None, help="Valeur locale du champ archive")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    annonce_id = str(args.id_annonce).strip()
    conn = sqlite3.connect(HEKTOR_DB)
    conn.row_factory = sqlite3.Row
    try:
        before = conn.execute(
            "select hektor_annonce_id, valide, diffusable, archive from hektor_annonce where hektor_annonce_id = ?",
            (annonce_id,),
        ).fetchone()
        if before is None:
            raise RuntimeError(f"Annonce introuvable dans hektor_annonce: {annonce_id}")

        archive_value = args.archive if args.archive is not None else str(before["archive"] or "0")
        conn.execute(
            """
            update hektor_annonce
            set valide = ?, diffusable = ?, archive = ?, synced_at = datetime('now')
            where hektor_annonce_id = ?
            """,
            (args.valide, args.diffusable, archive_value, annonce_id),
        )
        conn.commit()

        after = conn.execute(
            "select hektor_annonce_id, valide, diffusable, archive from hektor_annonce where hektor_annonce_id = ?",
            (annonce_id,),
        ).fetchone()
        print(
            json.dumps(
                {
                    "ok": True,
                    "before": dict(before),
                    "after": dict(after) if after else None,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
