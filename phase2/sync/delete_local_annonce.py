import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
ANNONCE_RAW_OBJECT_TYPES = (
    "annonce_detail",
    "mandat_by_annonce",
    "annonce_active",
    "annonce_archived",
)


def table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def delete_where(con: sqlite3.Connection, table: str, column: str, value: str | int | None) -> int:
    if value is None or not table_exists(con, table):
        return 0
    if column not in table_columns(con, table):
        return 0
    before = con.total_changes
    con.execute(f"DELETE FROM {table} WHERE CAST({column} AS TEXT) = ?", (str(value),))
    return con.total_changes - before


def cleanup_hektor_db(hektor_annonce_id: str) -> dict[str, int]:
    if not HEKTOR_DB.exists():
        return {"missing_database": 1}
    con = sqlite3.connect(HEKTOR_DB)
    try:
        removed: dict[str, int] = {}
        for table in [
            "case_dossier_source",
            "hektor_annonce",
            "hektor_annonce_detail",
            "hektor_annonce_photo",
            "hektor_annonce_reporting",
            "hektor_mandat",
            "hektor_offre",
            "hektor_compromis",
            "hektor_vente",
            "hektor_annonce_broadcast_state",
            "hektor_annonce_broadcast_target",
            "hektor_annonce_contact_link",
            "hektor_annonce_chauffage_detail",
            "hektor_annonce_console_detail",
            "hektor_annonce_draft_state",
            "sync_annonce_contact_link",
            "sync_annonce_state",
        ]:
            count = delete_where(con, table, "hektor_annonce_id", hektor_annonce_id)
            if count:
                removed[table] = count

        raw_columns = table_columns(con, "raw_api_response") if table_exists(con, "raw_api_response") else set()
        if {"object_type", "object_id"}.issubset(raw_columns):
            before = con.total_changes
            placeholders = ",".join("?" for _ in ANNONCE_RAW_OBJECT_TYPES)
            if "object_id_key" in raw_columns:
                con.execute(
                    f"""
                    DELETE FROM raw_api_response
                    WHERE (
                        CAST(object_id AS TEXT) = ?
                        OR CAST(object_id_key AS TEXT) = ?
                    )
                      AND object_type IN ({placeholders})
                    """,
                    (hektor_annonce_id, hektor_annonce_id, *ANNONCE_RAW_OBJECT_TYPES),
                )
            else:
                con.execute(
                    f"""
                    DELETE FROM raw_api_response
                    WHERE CAST(object_id AS TEXT) = ?
                      AND object_type IN ({placeholders})
                    """,
                    (hektor_annonce_id, *ANNONCE_RAW_OBJECT_TYPES),
                )
            count = con.total_changes - before
            if count:
                removed["raw_api_response"] = count

        if table_exists(con, "sync_error") and {"object_id", "object_type"}.issubset(table_columns(con, "sync_error")):
            before = con.total_changes
            placeholders = ",".join("?" for _ in ANNONCE_RAW_OBJECT_TYPES)
            con.execute(
                f"""
                DELETE FROM sync_error
                WHERE CAST(object_id AS TEXT) = ?
                  AND object_type IN ({placeholders})
                """,
                (hektor_annonce_id, *ANNONCE_RAW_OBJECT_TYPES),
            )
            count = con.total_changes - before
            if count:
                removed["sync_error"] = count
        con.commit()
        return removed
    finally:
        con.close()


def cleanup_phase2_db(hektor_annonce_id: str, app_dossier_id: str | None) -> dict[str, int]:
    if not PHASE2_DB.exists():
        return {"missing_database": 1}
    con = sqlite3.connect(PHASE2_DB)
    try:
        removed: dict[str, int] = {}
        for table in [
            "app_broadcast_action",
            "app_blocker",
            "app_contact_relation_current",
            "app_diffusion_target",
            "app_dossier",
            "app_dossier_current",
            "app_dossier_detail_current",
            "app_followup",
            "app_internal_status",
            "app_mandat_broadcast_current",
            "app_mandat_register_current",
            "app_note",
            "app_view_demandes_mandat_diffusion",
            "app_view_generale",
            "app_work_item",
            "app_work_item_current",
        ]:
            count = delete_where(con, table, "app_dossier_id", app_dossier_id)
            if count:
                removed[table] = removed.get(table, 0) + count
        for table in [
            "app_contact_relation_current",
            "app_diffusion_target",
            "app_dossier",
            "app_dossier_current",
            "app_dossier_detail_current",
            "app_mandat_broadcast_current",
            "app_mandat_register_current",
            "app_view_demandes_mandat_diffusion",
            "app_view_generale",
            "app_work_item_current",
        ]:
            count = delete_where(con, table, "hektor_annonce_id", hektor_annonce_id)
            if count:
                removed[table] = removed.get(table, 0) + count
        con.commit()
        return removed
    finally:
        con.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove a deleted Hektor annonce from local SQLite caches.")
    parser.add_argument("--id-annonce", required=True)
    parser.add_argument("--app-dossier-id")
    args = parser.parse_args()

    result = {
        "hektor_annonce_id": str(args.id_annonce),
        "app_dossier_id": str(args.app_dossier_id) if args.app_dossier_id else None,
        "hektor_db": cleanup_hektor_db(str(args.id_annonce)),
        "phase2_db": cleanup_phase2_db(str(args.id_annonce), str(args.app_dossier_id) if args.app_dossier_id else None),
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
