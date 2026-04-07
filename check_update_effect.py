from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from hektor_pipeline.common import DEFAULT_DB_PATH, init_db


RESOURCE_DEFS = {
    "mandats": {
        "update_listing_endpoint": "list_mandats_update",
        "detail_endpoint": "mandat_detail",
        "table": "hektor_mandat",
    },
    "offres": {
        "update_listing_endpoint": "list_offres_update",
        "detail_endpoint": "offre_detail",
        "table": "hektor_offre",
    },
    "compromis": {
        "update_listing_endpoint": "list_compromis_update",
        "detail_endpoint": "compromis_detail",
        "table": "hektor_compromis",
    },
    "ventes": {
        "update_listing_endpoint": "list_ventes_update",
        "detail_endpoint": "vente_detail",
        "table": "hektor_vente",
    },
    "annonces": {
        "update_listing_endpoints": ["list_annonces_active_update", "list_annonces_archived_update"],
        "detail_endpoint": "annonce_detail",
        "table": "hektor_annonce",
    },
    "contacts": {
        "update_listing_endpoints": ["list_contacts_active_update", "list_contacts_archived_update"],
        "detail_endpoint": "contact_detail",
        "table": "hektor_contact",
    },
}


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def fetch_one(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise RuntimeError("Query returned no row")
    return row


def latest_sync_raw_run_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute(
        """
        SELECT id
        FROM sync_run
        WHERE stage = 'sync_raw' AND status = 'success'
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return None
    return int(row["id"])


def listing_stats(conn: sqlite3.Connection, endpoint_names: list[str]) -> tuple[int, int, str]:
    placeholders = ", ".join("?" for _ in endpoint_names)
    row = fetch_one(
        conn,
        f"""
        SELECT
            COUNT(*) AS page_count,
            MAX(fetched_at) AS last_fetched
        FROM raw_api_response
        WHERE endpoint_name IN ({placeholders})
        """,
        tuple(endpoint_names),
    )
    unique_row = fetch_one(
        conn,
        f"""
        SELECT COUNT(DISTINCT TRIM(json_extract(json_each.value, '$.id'))) AS unique_ids
        FROM raw_api_response
        JOIN json_each(raw_api_response.payload_json, '$.data')
        WHERE endpoint_name IN ({placeholders})
          AND TRIM(COALESCE(json_extract(json_each.value, '$.id'), '')) != ''
        """,
        tuple(endpoint_names),
    )
    return int(row["page_count"] or 0), int(unique_row["unique_ids"] or 0), str(row["last_fetched"] or "-")


def listing_stats_for_run(conn: sqlite3.Connection, run_id: int, endpoint_names: list[str]) -> tuple[int, int, str]:
    placeholders = ", ".join("?" for _ in endpoint_names)
    params = (run_id, *endpoint_names)
    row = fetch_one(
        conn,
        f"""
        SELECT
            COUNT(*) AS page_count,
            MAX(fetched_at) AS last_fetched
        FROM raw_api_response
        WHERE run_id = ?
          AND endpoint_name IN ({placeholders})
        """,
        params,
    )
    unique_row = fetch_one(
        conn,
        f"""
        SELECT COUNT(DISTINCT TRIM(json_extract(json_each.value, '$.id'))) AS unique_ids
        FROM raw_api_response
        JOIN json_each(raw_api_response.payload_json, '$.data')
        WHERE raw_api_response.run_id = ?
          AND endpoint_name IN ({placeholders})
          AND TRIM(COALESCE(json_extract(json_each.value, '$.id'), '')) != ''
        """,
        params,
    )
    return int(row["page_count"] or 0), int(unique_row["unique_ids"] or 0), str(row["last_fetched"] or "-")


def detail_stats(conn: sqlite3.Connection, endpoint_name: str) -> tuple[int, str]:
    row = fetch_one(
        conn,
        """
        SELECT COUNT(DISTINCT object_id) AS detail_count, MAX(fetched_at) AS last_fetched
        FROM raw_api_response
        WHERE endpoint_name = ?
          AND object_id IS NOT NULL
          AND TRIM(object_id) != ''
        """,
        (endpoint_name,),
    )
    return int(row["detail_count"] or 0), str(row["last_fetched"] or "-")


def detail_stats_for_run(conn: sqlite3.Connection, run_id: int, endpoint_name: str) -> tuple[int, str]:
    row = fetch_one(
        conn,
        """
        SELECT COUNT(DISTINCT object_id) AS detail_count, MAX(fetched_at) AS last_fetched
        FROM raw_api_response
        WHERE run_id = ?
          AND endpoint_name = ?
          AND object_id IS NOT NULL
          AND TRIM(object_id) != ''
        """,
        (run_id, endpoint_name),
    )
    return int(row["detail_count"] or 0), str(row["last_fetched"] or "-")


def table_stats(conn: sqlite3.Connection, table_name: str) -> tuple[int, str]:
    row = fetch_one(
        conn,
        f"SELECT COUNT(*) AS row_count, MAX(synced_at) AS last_synced FROM {table_name}"
    )
    return int(row["row_count"] or 0), str(row["last_synced"] or "-")


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def main() -> int:
    parser = argparse.ArgumentParser(description="Show whether update runs actually fetched and normalized data.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to the SQLite database.")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    with connect_db(db_path) as conn:
        init_db(conn)
        run_id = latest_sync_raw_run_id(conn)
        if run_id is None:
            raise SystemExit("No successful sync_raw run found.")

        header = (
            f"{'resource':<12} {'run_raw':>20} {'pages':>8} {'ids':>8} "
            f"{'detail_ids':>12} {'normalized':>20} {'raw?':>6} {'detail?':>8}"
        )
        print(header)
        print("-" * len(header))
        print(f"latest sync_raw run id: {run_id}")
        print()

        for resource_name, cfg in RESOURCE_DEFS.items():
            endpoint_names = cfg.get("update_listing_endpoints") or [cfg["update_listing_endpoint"]]
            page_count, listing_ids, listing_last = listing_stats_for_run(conn, run_id, endpoint_names)
            detail_count, _detail_last = detail_stats_for_run(conn, run_id, cfg["detail_endpoint"])
            table_count, table_last = table_stats(conn, cfg["table"])

            print(
                f"{resource_name:<12} {listing_last:>10} {page_count:>8} {listing_ids:>8} "
                f"{detail_count:>12} {table_last:>12} {yes_no(page_count > 0):>6} {yes_no(detail_count > 0):>8}"
            )

        print()
        print("Interpretation:")
        print("- raw? = update listings present in raw_api_response")
        print("- detail? = ById details present in raw_api_response")
        print("- normalized = latest synced_at in normalized table")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
