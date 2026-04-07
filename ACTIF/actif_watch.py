from __future__ import annotations

import argparse
import os
import sqlite3
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "actif.sqlite"


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def fetch_last_run(conn: sqlite3.Connection):
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(actif_run)")}
    optional_columns = {
        "current_step": "NULL AS current_step",
        "progress_done": "0 AS progress_done",
        "progress_total": "0 AS progress_total",
        "current_annonce_id": "NULL AS current_annonce_id",
        "error_count": "0 AS error_count",
        "heartbeat_at": "NULL AS heartbeat_at",
    }
    selected = [
        "id",
        "started_at",
        "finished_at",
        "status",
    ]
    for column_name, fallback in optional_columns.items():
        selected.append(column_name if column_name in columns else fallback)
    selected.extend([
        "listing_count",
        "new_count",
        "updated_count",
        "unchanged_count",
        "removed_count",
        "detail_count",
        "notes",
    ])
    query = f"""
        SELECT {', '.join(selected)}
        FROM actif_run
        ORDER BY id DESC
        LIMIT 1
    """
    return conn.execute(query).fetchone()


def fetch_recent_errors(conn: sqlite3.Connection, run_id: int, limit: int = 5):
    return conn.execute(
        """
        SELECT stage, object_id, error_message, created_at
        FROM actif_error
        WHERE run_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (run_id, limit),
    ).fetchall()


def render_run(row, errors) -> str:
    lines = []
    if row is None:
        return "Aucun run ACTIF en base."

    total = int(row["progress_total"] or 0)
    done = int(row["progress_done"] or 0)
    percent = 0.0 if total <= 0 else (done / total) * 100.0

    lines.append(f"Run ACTIF #{row['id']}  status={row['status']}")
    lines.append(
        f"started_at={row['started_at']}  finished_at={row['finished_at'] or '-'}  heartbeat_at={row['heartbeat_at'] or '-'}"
    )
    current_label = "items_seen" if str(row["current_step"] or "").startswith("listing_page_") else "current_annonce_id"
    lines.append(
        f"step={row['current_step'] or '-'}  progress={done}/{total}  percent={percent:.1f}%  {current_label}={row['current_annonce_id'] or '-'}"
    )
    lines.append(
        "listing={listing_count} new={new_count} updated={updated_count} unchanged={unchanged_count} removed={removed_count} detail={detail_count} errors={error_count}".format(
            **dict(row)
        )
    )
    if row["notes"]:
        lines.append(f"notes={row['notes']}")
    if errors:
        lines.append("")
        lines.append("Dernieres erreurs :")
        for error in errors:
            lines.append(
                f"- [{error['created_at']}] stage={error['stage']} object_id={error['object_id'] or '-'} :: {error['error_message']}"
            )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Suivi temps reel des runs ACTIF.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Chemin de la base SQLite ACTIF.")
    parser.add_argument("--interval", type=float, default=2.0, help="Intervalle de rafraichissement en secondes.")
    parser.add_argument("--once", action="store_true", help="Afficher une seule fois sans boucle.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path)

    while True:
        conn = connect_db(db_path)
        row = fetch_last_run(conn)
        errors = fetch_recent_errors(conn, row["id"]) if row is not None else []
        clear_screen()
        print(render_run(row, errors))
        if args.once:
            return 0
        if row is not None and row["status"] in {"success", "partial_success", "failed"} and row["finished_at"]:
            return 0
        time.sleep(max(args.interval, 0.2))


if __name__ == "__main__":
    raise SystemExit(main())
