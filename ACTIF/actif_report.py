from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "actif.sqlite"


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def fetch_last_run(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT id, started_at, finished_at, status, listing_count, new_count, updated_count,
               unchanged_count, removed_count, detail_count, error_count, notes
        FROM actif_run
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    return dict(row) if row else None


def fetch_annonces(conn: sqlite3.Connection, *, active_current: int, limit: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT annonce_id, listing_date_maj, statut_name, no_dossier, no_mandat, prix, titre,
               ville, code_postal, last_seen_at, removed_at
        FROM actif_annonce
        WHERE active_current = ?
        ORDER BY COALESCE(listing_date_maj, '') DESC, annonce_id DESC
        LIMIT ?
        """,
        (active_current, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def fetch_errors(conn: sqlite3.Connection, *, limit: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, run_id, stage, object_id, error_message, created_at
        FROM actif_error
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def fetch_annonce(conn: sqlite3.Connection, annonce_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT annonce_id, listing_date_maj, active_current, first_seen_at, last_seen_at, removed_at,
               statut_id, statut_name, no_dossier, no_mandat, agence_id, negociateur_id, archive,
               diffusable, partage, valide, prix, surface, titre, ville, code_postal,
               mandat_json, contacts_json
        FROM actif_annonce
        WHERE annonce_id = ?
        """,
        (annonce_id,),
    ).fetchone()
    if not row:
        return None
    payload = dict(row)
    for key in ("mandat_json", "contacts_json"):
        raw = payload.get(key)
        payload[key] = json.loads(raw) if raw else None
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rapport simple sur la base SQLite ACTIF.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Chemin de la base SQLite ACTIF.")
    parser.add_argument("--last-run", action="store_true", help="Afficher le dernier run.")
    parser.add_argument("--active", action="store_true", help="Afficher les annonces actuellement actives.")
    parser.add_argument("--removed", action="store_true", help="Afficher les annonces sorties du parc actif.")
    parser.add_argument("--errors", action="store_true", help="Afficher les erreurs enregistrees.")
    parser.add_argument("--annonce-id", help="Afficher une annonce precise avec son mandat et ses contacts.")
    parser.add_argument("--limit", type=int, default=20, help="Limite d'affichage pour les listes.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    conn = connect_db(Path(args.db_path))

    if args.annonce_id:
        payload = fetch_annonce(conn, args.annonce_id)
        print_json(payload if payload else {"error": f"annonce {args.annonce_id} introuvable"})
        return 0

    something_selected = args.last_run or args.active or args.removed or args.errors
    if not something_selected:
        args.last_run = True

    if args.last_run:
        print_json({"last_run": fetch_last_run(conn)})
    if args.active:
        print_json({"active": fetch_annonces(conn, active_current=1, limit=args.limit)})
    if args.removed:
        print_json({"removed": fetch_annonces(conn, active_current=0, limit=args.limit)})
    if args.errors:
        print_json({"errors": fetch_errors(conn, limit=args.limit)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
