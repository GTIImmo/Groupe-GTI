from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
OUTPUT = ROOT / "phase2" / "docs" / "RAPPORT_CONTACT_SYNC_STATUS.md"


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
        (table,),
    ).fetchone() is not None


def scalar(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return 0
    value = row[0]
    return int(value or 0)


def rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def age_minutes(value: str | None) -> int | None:
    parsed = parse_iso(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0, int((datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() // 60))


def hektor_status() -> dict[str, Any]:
    if not HEKTOR_DB.exists():
        return {"db_exists": False}
    with connect(HEKTOR_DB) as conn:
        report: dict[str, Any] = {"db_exists": True}
        if table_exists(conn, "sync_contact_state"):
            total = scalar(conn, "SELECT COUNT(*) FROM sync_contact_state")
            synced = scalar(conn, "SELECT COUNT(*) FROM sync_contact_state WHERE last_detail_sync_at IS NOT NULL")
            report["contact_state"] = {
                "total": total,
                "detail_synced": synced,
                "detail_missing": max(0, total - synced),
                "latest_detail_sync_at": conn.execute("SELECT MAX(last_detail_sync_at) FROM sync_contact_state").fetchone()[0],
            }
        if table_exists(conn, "raw_api_response"):
            report["raw_contact_details"] = scalar(
                conn,
                """
                SELECT COUNT(DISTINCT COALESCE(object_id_key, object_id))
                FROM raw_api_response
                WHERE endpoint_name = 'contact_detail'
                """,
            )
        if table_exists(conn, "sync_contact_detail_skip"):
            report["contact_detail_skip"] = {
                "total": scalar(conn, "SELECT COUNT(*) FROM sync_contact_detail_skip"),
                "by_reason": rows(
                    conn,
                    """
                    SELECT reason, COUNT(*) AS count
                    FROM sync_contact_detail_skip
                    GROUP BY reason
                    ORDER BY count DESC
                    """,
                ),
            }
        if table_exists(conn, "sync_error"):
            report["contact_detail_errors"] = {
                "total": scalar(conn, "SELECT COUNT(*) FROM sync_error WHERE endpoint_name = 'contact_detail'"),
                "not_found": scalar(
                    conn,
                    """
                    SELECT COUNT(*) FROM sync_error
                    WHERE endpoint_name = 'contact_detail'
                      AND (LOWER(error_message) LIKE '%404%' OR LOWER(error_message) LIKE '%not found%')
                    """,
                ),
                "timeout_or_connect": scalar(
                    conn,
                    """
                    SELECT COUNT(*) FROM sync_error
                    WHERE endpoint_name = 'contact_detail'
                      AND (
                        LOWER(error_message) LIKE '%timeout%'
                        OR LOWER(error_message) LIKE '%connect%'
                        OR LOWER(error_message) LIKE '%10060%'
                      )
                    """,
                ),
                "latest": rows(
                    conn,
                    """
                    SELECT created_at, object_id, substr(error_message, 1, 220) AS error_message
                    FROM sync_error
                    WHERE endpoint_name = 'contact_detail'
                    ORDER BY id DESC
                    LIMIT 5
                    """,
                ),
            }
        if table_exists(conn, "sync_run"):
            latest = conn.execute(
                """
                SELECT id, status, started_at, finished_at, heartbeat_at, current_step,
                       current_endpoint, current_object_id, current_page,
                       progress_done, progress_total, progress_unit, notes
                FROM sync_run
                WHERE stage = 'sync_contact_details'
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
            if latest:
                latest_dict = dict(latest)
                latest_dict["heartbeat_age_minutes"] = age_minutes(latest_dict.get("heartbeat_at"))
                report["latest_run"] = latest_dict
        return report


def phase2_status() -> dict[str, Any]:
    if not PHASE2_DB.exists():
        return {"db_exists": False}
    with connect(PHASE2_DB) as conn:
        report: dict[str, Any] = {"db_exists": True}
        if table_exists(conn, "app_contact_current"):
            contact_columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(app_contact_current)").fetchall()
            }
            report["contacts_layer"] = {
                "total": scalar(conn, "SELECT COUNT(*) FROM app_contact_current"),
                "active": scalar(conn, "SELECT COUNT(*) FROM app_contact_current WHERE archive = 0"),
                "archived": scalar(conn, "SELECT COUNT(*) FROM app_contact_current WHERE archive = 1"),
                "eligible_supabase": scalar(conn, "SELECT COUNT(*) FROM app_contact_current WHERE supabase_sync_eligible = 1"),
                "with_relation": scalar(conn, "SELECT COUNT(*) FROM app_contact_current WHERE linked_annonce_count > 0"),
                "with_active_search": scalar(conn, "SELECT COUNT(*) FROM app_contact_current WHERE active_search_count > 0"),
                "with_any_search": scalar(conn, "SELECT COUNT(*) FROM app_contact_current WHERE total_search_count > 0"),
            }
            if "has_contact_detail" in contact_columns:
                report["contacts_layer"]["with_contact_detail"] = scalar(
                    conn,
                    "SELECT COUNT(*) FROM app_contact_current WHERE has_contact_detail = 1",
                )
        if table_exists(conn, "app_contact_relation_current"):
            report["relations_layer"] = {
                "total": scalar(conn, "SELECT COUNT(*) FROM app_contact_relation_current"),
                "active_annonce": scalar(conn, "SELECT COUNT(*) FROM app_contact_relation_current WHERE is_active_annonce = 1"),
                "transaction": scalar(conn, "SELECT COUNT(*) FROM app_contact_relation_current WHERE transaction_id IS NOT NULL"),
                "by_role": rows(
                    conn,
                    """
                    SELECT role_contact, COUNT(*) AS count
                    FROM app_contact_relation_current
                    GROUP BY role_contact
                    ORDER BY count DESC
                    LIMIT 12
                    """,
                ),
            }
        if table_exists(conn, "app_contact_search_current"):
            report["searches_layer"] = {
                "total": scalar(conn, "SELECT COUNT(*) FROM app_contact_search_current"),
                "active": scalar(conn, "SELECT COUNT(*) FROM app_contact_search_current WHERE is_active = 1"),
                "archived": scalar(conn, "SELECT COUNT(*) FROM app_contact_search_current WHERE archive = 1"),
            }
        if table_exists(conn, "app_contact_duplicate_group_current"):
            report["duplicates_layer"] = {
                "groups": scalar(conn, "SELECT COUNT(*) FROM app_contact_duplicate_group_current"),
                "high_or_critical": scalar(
                    conn,
                    """
                    SELECT COUNT(*)
                    FROM app_contact_duplicate_group_current
                    WHERE severity IN ('high', 'critical')
                    """,
                ),
                "suspected_mass_archive_error": scalar(
                    conn,
                    "SELECT COUNT(*) FROM app_contact_duplicate_group_current WHERE suspected_mass_archive_error = 1",
                ),
            }
        if table_exists(conn, "app_contact_supabase_push_state"):
            report["supabase_push_state"] = rows(
                conn,
                """
                SELECT table_name, COUNT(*) AS rows_marked_pushed, MAX(pushed_at) AS latest_pushed_at
                FROM app_contact_supabase_push_state
                GROUP BY table_name
                ORDER BY table_name
                """,
            )
        return report


def render_markdown(report: dict[str, Any]) -> str:
    contact_state = report.get("hektor", {}).get("contact_state", {})
    contacts_layer = report.get("phase2", {}).get("contacts_layer", {})
    latest_run = report.get("hektor", {}).get("latest_run", {})
    lines = [
        "# Rapport statut contacts",
        "",
        "Controle local de l'extraction ContactById, de la couche contacts phase 2 et de l'etat de push Supabase.",
        "",
        "## Synthese",
        "",
        f"- Contacts listing local : `{contact_state.get('total', 0)}`",
        f"- Fiches detail recuperees : `{contact_state.get('detail_synced', 0)}`",
        f"- Fiches detail restantes : `{contact_state.get('detail_missing', 0)}`",
        f"- Contacts app eligibles Supabase : `{contacts_layer.get('eligible_supabase', 0)}`",
        f"- Contacts avec recherche active : `{contacts_layer.get('with_active_search', 0)}`",
        f"- Dernier run detail : `{latest_run.get('status', 'n/a')}` / `{latest_run.get('finished_at') or latest_run.get('heartbeat_at') or 'n/a'}`",
        "",
        "## Donnees completes",
        "",
        "```json",
        json.dumps(report, ensure_ascii=True, indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "hektor": hektor_status(),
        "phase2": phase2_status(),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"report": str(OUTPUT), **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
