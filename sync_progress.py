from __future__ import annotations

import argparse
import math
import shutil
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from hektor_pipeline.common import DEFAULT_DB_PATH, RUN_STALE_AFTER_MINUTES, cleanup_stale_sync_runs, init_db


@dataclass
class StepProgress:
    label: str
    done: int
    total: int

    @property
    def ratio(self) -> float:
        if self.total <= 0:
            return 0.0
        return min(self.done / self.total, 1.0)


LISTING_ENDPOINTS = {
    "agences": ["list_agences"],
    "negos": ["list_negos"],
    "annonces": ["list_annonces_active", "list_annonces_archived", "list_annonces_active_update", "list_annonces_archived_update"],
    "contacts": ["list_contacts_active", "list_contacts_archived", "list_contacts", "list_contacts_active_update", "list_contacts_archived_update"],
    "mandats": ["list_mandats", "list_mandats_update"],
    "offres": ["list_offres", "list_offres_update"],
    "compromis": ["list_compromis", "list_compromis_update"],
    "ventes": ["list_ventes", "list_ventes_update"],
    "broadcasts": ["list_broadcasts"],
}

DETAIL_ENDPOINTS = {
    "annonces": "annonce_detail",
    "mandats": "mandat_detail",
}


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_latest_sync_run(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT
            id, stage, started_at, finished_at, status, notes, pid, heartbeat_at,
            current_step, current_resource, current_endpoint, current_object_id,
            current_page, progress_done, progress_total, progress_unit
        FROM sync_run
        ORDER BY CASE WHEN status = 'running' THEN 0 ELSE 1 END, id DESC
        LIMIT 1
        """
    ).fetchone()


def get_listing_stats(conn: sqlite3.Connection, run_id: int, endpoint_names: list[str]) -> tuple[int, int]:
    page_count = 0
    expected_pages = 0
    for endpoint_name in endpoint_names:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS page_count,
                MAX(CAST(json_extract(payload_json, '$.metadata.total') AS INTEGER)) AS meta_total,
                MAX(CAST(json_extract(payload_json, '$.metadata.perPage') AS INTEGER)) AS per_page
            FROM raw_api_response
            WHERE run_id = ? AND endpoint_name = ?
            """,
            (run_id, endpoint_name),
        ).fetchone()
        endpoint_pages = int(row["page_count"] or 0)
        meta_total = int(row["meta_total"] or 0)
        per_page = int(row["per_page"] or 0)
        page_count += endpoint_pages
        if endpoint_pages == 0:
            continue
        if per_page <= 0:
            expected_pages += endpoint_pages
        else:
            expected_pages += max(math.ceil(meta_total / per_page) if meta_total > 0 else endpoint_pages, endpoint_pages)
    return page_count, expected_pages


def get_listing_item_total(conn: sqlite3.Connection, run_id: int, endpoint_names: list[str]) -> int:
    total = 0
    for endpoint_name in endpoint_names:
        row = conn.execute(
            """
            SELECT MAX(CAST(json_extract(payload_json, '$.metadata.total') AS INTEGER)) AS meta_total
            FROM raw_api_response
            WHERE run_id = ? AND endpoint_name = ?
            """,
            (run_id, endpoint_name),
        ).fetchone()
        total += int(row["meta_total"] or 0)
    return total


def get_listing_unique_id_total(conn: sqlite3.Connection, run_id: int, endpoint_names: list[str]) -> int:
    if not endpoint_names:
        return 0
    placeholders = ", ".join("?" for _ in endpoint_names)
    row = conn.execute(
        f"""
        SELECT COUNT(DISTINCT TRIM(json_extract(json_each.value, '$.id'))) AS unique_count
        FROM raw_api_response
        JOIN json_each(raw_api_response.payload_json, '$.data')
        WHERE run_id = ?
          AND endpoint_name IN ({placeholders})
          AND TRIM(COALESCE(json_extract(json_each.value, '$.id'), '')) != ''
        """,
        (run_id, *endpoint_names),
    ).fetchone()
    return int(row["unique_count"] or 0)


def get_detail_stats(conn: sqlite3.Connection, run_id: int, endpoint_name: str, expected_total: int) -> tuple[int, int]:
    row = conn.execute(
        """
        SELECT COUNT(DISTINCT object_id) AS row_count
        FROM raw_api_response
        WHERE run_id = ? AND endpoint_name = ? AND object_id IS NOT NULL AND object_id != ''
        """,
        (run_id, endpoint_name),
    ).fetchone()
    done = int(row["row_count"] or 0)
    return done, expected_total


def get_relation_stats(conn: sqlite3.Connection, run_id: int, endpoint_name: str, expected_total: int) -> tuple[int, int]:
    row = conn.execute(
        "SELECT COUNT(*) AS row_count FROM raw_api_response WHERE run_id = ? AND endpoint_name = ?",
        (run_id, endpoint_name),
    ).fetchone()
    done = int(row["row_count"] or 0)
    return done, expected_total


def render_bar(ratio: float, width: int) -> str:
    width = max(width, 10)
    filled = min(int(round(ratio * width)), width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def collect_progress(conn: sqlite3.Connection, run_id: int) -> list[StepProgress]:
    listing_page_totals: dict[str, int] = {}
    listing_item_totals: dict[str, int] = {}
    steps: list[StepProgress] = []

    for label, endpoint_names in LISTING_ENDPOINTS.items():
        done, total = get_listing_stats(conn, run_id, endpoint_names)
        listing_page_totals[label] = total
        listing_item_totals[label] = get_listing_unique_id_total(conn, run_id, endpoint_names)
        steps.append(StepProgress(f"list:{label}", done, total))

    for label, endpoint_name in DETAIL_ENDPOINTS.items():
        expected_total = listing_item_totals.get(label, 0)
        done, total = get_detail_stats(conn, run_id, endpoint_name, expected_total)
        steps.append(StepProgress(f"detail:{label}", done, total))

    annonce_total = listing_item_totals.get("annonces", 0)
    relation_done, relation_total = get_relation_stats(conn, run_id, "mandats_by_annonce", annonce_total)
    steps.append(StepProgress("relation:annonces_to_mandats", relation_done, relation_total))

    return steps


def print_progress(conn: sqlite3.Connection) -> None:
    stale_count = cleanup_stale_sync_runs(conn, stale_after_minutes=RUN_STALE_AFTER_MINUTES)
    run = get_latest_sync_run(conn)
    steps = collect_progress(conn, int(run["id"])) if run is not None else []
    done_total = sum(step.done for step in steps if step.total > 0)
    expected_total = sum(step.total for step in steps if step.total > 0)
    ratio = (done_total / expected_total) if expected_total else 0.0

    cols = shutil.get_terminal_size((100, 20)).columns
    bar_width = max(20, min(40, cols - 45))

    print("Hektor sync progress")
    if run is None:
        print("No sync run found.")
    else:
        print(
            f"run #{run['id']}  status={run['status']}  started={run['started_at']}  "
            f"finished={run['finished_at'] or '-'}"
        )
        if run["heartbeat_at"]:
            print(f"heartbeat={run['heartbeat_at']}  pid={run['pid'] or '-'}")
        current_label = "  ".join(
            part for part in (
                f"step={run['current_step']}" if run["current_step"] else "",
                f"resource={run['current_resource']}" if run["current_resource"] else "",
                f"endpoint={run['current_endpoint']}" if run["current_endpoint"] else "",
                f"page={run['current_page']}" if run["current_page"] is not None else "",
                f"object={run['current_object_id']}" if run["current_object_id"] else "",
            ) if part
        )
        if current_label:
            print(current_label)
        if run["progress_total"] not in (None, 0):
            unit = run["progress_unit"] or "items"
            print(
                f"current progress {run['progress_done'] or 0}/{run['progress_total']} {unit}"
            )
        elif run["progress_done"] not in (None, 0):
            unit = run["progress_unit"] or "items"
            print(f"current progress {run['progress_done']} {unit}")
        if run["notes"]:
            print(f"notes={run['notes']}")
    if stale_count:
        print(f"cleanup={stale_count} stale run(s) marked abandoned")
    print(f"overall {render_bar(ratio, bar_width)} {done_total}/{expected_total} ({ratio * 100:5.1f}%)")
    print()

    for step in steps:
        if step.total <= 0:
            continue
        print(
            f"{step.label:<28} {render_bar(step.ratio, bar_width)} "
            f"{step.done:>6}/{step.total:<6} {step.ratio * 100:5.1f}%"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Show approximate progress for a Hektor full sync.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to the SQLite database.")
    parser.add_argument("--watch", type=int, default=0, help="Refresh every N seconds.")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return 1

    if args.watch <= 0:
        with connect_db(db_path) as conn:
            init_db(conn)
            print_progress(conn)
        return 0

    try:
        while True:
            with connect_db(db_path) as conn:
                init_db(conn)
                print("\x1b[2J\x1b[H", end="")
                print_progress(conn)
            time.sleep(args.watch)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
