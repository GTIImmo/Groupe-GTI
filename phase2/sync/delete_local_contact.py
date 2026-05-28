import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"


def table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def delete_where(con: sqlite3.Connection, table: str, column: str, value: str | None) -> int:
    if value is None or not table_exists(con, table):
        return 0
    if column not in table_columns(con, table):
        return 0
    before = con.total_changes
    con.execute(f"DELETE FROM {table} WHERE CAST({column} AS TEXT) = ?", (str(value),))
    return con.total_changes - before


def cleanup_hektor_db(hektor_contact_id: str) -> dict[str, int]:
    if not HEKTOR_DB.exists():
        return {"missing_database": 1}
    con = sqlite3.connect(HEKTOR_DB)
    try:
        removed: dict[str, int] = {}
        for table in [
            "hektor_contact",
            "sync_contact_state",
            "sync_contact_detail_skip",
            "sync_annonce_contact_link",
        ]:
            count = delete_where(con, table, "hektor_contact_id", hektor_contact_id)
            if count:
                removed[table] = count

        if table_exists(con, "raw_api_response") and {"object_id_key", "object_type"}.issubset(table_columns(con, "raw_api_response")):
            before = con.total_changes
            con.execute(
                """
                DELETE FROM raw_api_response
                WHERE CAST(object_id_key AS TEXT) = ?
                  AND object_type IN ('contact', 'contact_archived', 'contact_detail')
                """,
                (hektor_contact_id,),
            )
            count = con.total_changes - before
            if count:
                removed["raw_api_response"] = count

        if table_exists(con, "sync_error") and {"object_id", "object_type"}.issubset(table_columns(con, "sync_error")):
            before = con.total_changes
            con.execute(
                """
                DELETE FROM sync_error
                WHERE CAST(object_id AS TEXT) = ?
                  AND object_type = 'contact_detail'
                """,
                (hektor_contact_id,),
            )
            count = con.total_changes - before
            if count:
                removed["sync_error"] = count

        con.commit()
        return removed
    finally:
        con.close()


def cleanup_phase2_db(hektor_contact_id: str) -> dict[str, int]:
    if not PHASE2_DB.exists():
        return {"missing_database": 1}
    con = sqlite3.connect(PHASE2_DB)
    try:
        removed: dict[str, int] = {}
        for table in [
            "app_contact_current",
            "app_contact_relation_current",
            "app_contact_search_current",
            "app_contact_duplicate_member_current",
        ]:
            count = delete_where(con, table, "hektor_contact_id", hektor_contact_id)
            if count:
                removed[table] = count

        if table_exists(con, "app_contact_duplicate_group_current") and table_exists(con, "app_contact_duplicate_member_current"):
            before = con.total_changes
            con.execute(
                """
                DELETE FROM app_contact_duplicate_group_current
                WHERE duplicate_group_id NOT IN (
                    SELECT DISTINCT duplicate_group_id
                    FROM app_contact_duplicate_member_current
                )
                """
            )
            count = con.total_changes - before
            if count:
                removed["app_contact_duplicate_group_current_empty"] = count

        con.commit()
        return removed
    finally:
        con.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove a deleted Hektor contact from local SQLite caches.")
    parser.add_argument("--contact-id", required=True)
    args = parser.parse_args()

    contact_id = str(args.contact_id).strip()
    if not contact_id.isdigit():
        raise SystemExit("--contact-id must be numeric")

    result = {
        "hektor_contact_id": contact_id,
        "hektor_db": cleanup_hektor_db(contact_id),
        "phase2_db": cleanup_phase2_db(contact_id),
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
