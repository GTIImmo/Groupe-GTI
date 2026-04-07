from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from hektor_pipeline.common import DEFAULT_DB_PATH, init_db


RESOURCE_DEFS = {
    "annonces": {
        "listing_endpoints": ["list_annonces_active", "list_annonces_archived"],
        "update_listing_endpoints": ["list_annonces_active_update", "list_annonces_archived_update"],
        "detail_endpoint": "annonce_detail",
        "table": "hektor_annonce",
        "table_pk": "hektor_annonce_id",
    },
    "contacts": {
        "listing_endpoints": ["list_contacts_active", "list_contacts_archived", "list_contacts"],
        "update_listing_endpoints": ["list_contacts_active_update", "list_contacts_archived_update"],
        "detail_endpoint": "contact_detail",
        "table": "hektor_contact",
        "table_pk": "hektor_contact_id",
    },
    "mandats": {
        "listing_endpoints": ["list_mandats"],
        "update_listing_endpoints": ["list_mandats_update"],
        "detail_endpoint": "mandat_detail",
        "table": "hektor_mandat",
        "table_pk": "hektor_mandat_id",
    },
    "offres": {
        "listing_endpoints": ["list_offres"],
        "update_listing_endpoints": ["list_offres_update"],
        "detail_endpoint": "offre_detail",
        "table": "hektor_offre",
        "table_pk": "hektor_offre_id",
    },
    "compromis": {
        "listing_endpoints": ["list_compromis"],
        "update_listing_endpoints": ["list_compromis_update"],
        "detail_endpoint": "compromis_detail",
        "table": "hektor_compromis",
        "table_pk": "hektor_compromis_id",
    },
    "ventes": {
        "listing_endpoints": ["list_ventes"],
        "update_listing_endpoints": ["list_ventes_update"],
        "detail_endpoint": "vente_detail",
        "table": "hektor_vente",
        "table_pk": "hektor_vente_id",
    },
}


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def endpoint_max_total(conn: sqlite3.Connection, endpoint_name: str) -> int:
    row = conn.execute(
        """
        SELECT MAX(CAST(json_extract(payload_json, '$.metadata.total') AS INTEGER)) AS total
        FROM raw_api_response
        WHERE endpoint_name = ?
        """,
        (endpoint_name,),
    ).fetchone()
    return int(row["total"] or 0)


def sum_api_totals(conn: sqlite3.Connection, endpoint_names: list[str]) -> int:
    return sum(endpoint_max_total(conn, endpoint_name) for endpoint_name in endpoint_names)


def count_distinct_listing_ids(conn: sqlite3.Connection, endpoint_names: list[str]) -> int:
    if not endpoint_names:
        return 0
    placeholders = ", ".join("?" for _ in endpoint_names)
    row = conn.execute(
        f"""
        SELECT COUNT(DISTINCT TRIM(json_extract(json_each.value, '$.id'))) AS total
        FROM raw_api_response
        JOIN json_each(raw_api_response.payload_json, '$.data')
        WHERE endpoint_name IN ({placeholders})
          AND TRIM(COALESCE(json_extract(json_each.value, '$.id'), '')) != ''
        """,
        tuple(endpoint_names),
    ).fetchone()
    return int(row["total"] or 0)


def count_distinct_object_ids(conn: sqlite3.Connection, endpoint_name: str) -> int:
    row = conn.execute(
        """
        SELECT COUNT(DISTINCT object_id) AS total
        FROM raw_api_response
        WHERE endpoint_name = ? AND object_id IS NOT NULL AND TRIM(object_id) != ''
        """,
        (endpoint_name,),
    ).fetchone()
    return int(row["total"] or 0)


def count_table_rows(conn: sqlite3.Connection, table_name: str, pk_name: str) -> int:
    row = conn.execute(
        f"""
        SELECT COUNT(DISTINCT {pk_name}) AS total
        FROM {table_name}
        WHERE {pk_name} IS NOT NULL AND TRIM({pk_name}) != ''
        """
    ).fetchone()
    return int(row["total"] or 0)


def latest_timestamp(conn: sqlite3.Connection, sql: str) -> str:
    row = conn.execute(sql).fetchone()
    value = row[0] if row else None
    return str(value or "-")


def render_int(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def render_gap(left: int, right: int) -> str:
    return render_int(left - right)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare API totals, raw stored IDs, and normalized tables.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to the SQLite database.")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    with connect_db(db_path) as conn:
        init_db(conn)

        header = (
            f"{'resource':<12} {'api_total':>10} {'raw_list':>10} {'raw_detail':>10} "
            f"{'data':>10} {'api-data':>10} {'detail-data':>12}"
        )
        print(header)
        print("-" * len(header))

        for resource_name, cfg in RESOURCE_DEFS.items():
            canonical_api_total = sum_api_totals(conn, cfg["listing_endpoints"])
            update_api_total = sum_api_totals(conn, cfg["update_listing_endpoints"])
            raw_listing_total = count_distinct_listing_ids(
                conn,
                cfg["listing_endpoints"] + cfg["update_listing_endpoints"],
            )
            raw_detail_total = count_distinct_object_ids(conn, cfg["detail_endpoint"])
            data_total = count_table_rows(conn, cfg["table"], cfg["table_pk"])

            api_total = max(canonical_api_total, update_api_total)
            print(
                f"{resource_name:<12} {render_int(api_total):>10} {render_int(raw_listing_total):>10} "
                f"{render_int(raw_detail_total):>10} {render_int(data_total):>10} "
                f"{render_gap(api_total, data_total):>10} {render_gap(raw_detail_total, data_total):>12}"
            )

        print()
        print("timestamps")
        print(f"raw_api_response : {latest_timestamp(conn, 'SELECT MAX(fetched_at) FROM raw_api_response')}")
        for resource_name, cfg in RESOURCE_DEFS.items():
            print(
                f"{cfg['table']:<16}: "
                f"{latest_timestamp(conn, 'SELECT MAX(synced_at) FROM ' + cfg['table'])}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
