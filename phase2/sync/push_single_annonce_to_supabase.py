from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_case_index import build_case_dossier_source  # noqa: E402
from hektor_pipeline.common import Settings, connect_db, init_db  # noqa: E402
from phase2.bootstrap_phase2 import ensure_schema  # noqa: E402
from phase2.pipeline.view_demandes_mandat_diffusion import SQL_REFRESH_DEMANDES_MANDAT_DIFFUSION  # noqa: E402
from phase2.pipeline.view_generale import SQL_REFRESH_VUE_GENERALE  # noqa: E402
from phase2.sync.export_app_payload import build_payload  # noqa: E402
from phase2.sync.push_upgrade_to_supabase import (  # noqa: E402
    SupabaseRestClient,
    build_current_details,
    build_current_dossiers,
    build_current_mandat_register_rows,
    build_current_work_items,
    load_env_file,
    normalize_broadcast_rows,
    now_iso,
)


PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
DEFAULT_ENV_FILE = ROOT / ".env"
EXTRA_ENV_FILES = (
    ROOT / "Console" / ".env",
    ROOT / "apps" / "hektor-v1" / ".env",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Push direct Supabase pour une seule annonce Hektor.")
    parser.add_argument("--hektor-annonce-id", required=True, help="ID Hektor de l'annonce a pousser")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    return parser.parse_args()


def run_case_index_for_annonce(hektor_annonce_id: str) -> int:
    settings = Settings.from_env()
    conn = connect_db(settings.db_path)
    try:
        init_db(conn)
        return build_case_dossier_source(conn, [hektor_annonce_id])
    finally:
        conn.close()


def sync_target_app_dossier(con: sqlite3.Connection, hektor_annonce_id: str) -> int | None:
    con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
    try:
        con.execute(
            """
            WITH mandat_match AS (
                SELECT
                    src.hektor_annonce_id,
                    m.hektor_mandat_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY src.hektor_annonce_id
                        ORDER BY
                            CASE WHEN COALESCE(m.hektor_mandat_id, '') = COALESCE(src.mandat_id, '') THEN 0 ELSE 1 END,
                            CASE WHEN COALESCE(m.numero, '') = COALESCE(src.no_mandat, '') THEN 0 ELSE 1 END,
                            COALESCE(m.synced_at, '') DESC,
                            COALESCE(m.hektor_mandat_id, '') DESC
                    ) AS rn
                FROM hektor.case_dossier_source src
                LEFT JOIN hektor.hektor_mandat m
                    ON m.hektor_annonce_id = src.hektor_annonce_id
                WHERE src.annonce_source_status = 'present'
                  AND src.hektor_annonce_id = ?
            )
            INSERT INTO app_dossier (
                hektor_annonce_id,
                hektor_mandat_id,
                numero_dossier,
                numero_mandat,
                commercial_id,
                commercial_nom
            )
            SELECT
                CAST(src.hektor_annonce_id AS INTEGER),
                COALESCE(mm.hektor_mandat_id, src.mandat_id),
                src.no_dossier,
                src.no_mandat,
                src.hektor_negociateur_id,
                TRIM(COALESCE(src.negociateur_prenom, '') || ' ' || COALESCE(src.negociateur_nom, ''))
            FROM hektor.case_dossier_source src
            LEFT JOIN mandat_match mm
                ON mm.hektor_annonce_id = src.hektor_annonce_id
               AND mm.rn = 1
            WHERE src.annonce_source_status = 'present'
              AND src.hektor_annonce_id = ?
            ON CONFLICT(hektor_annonce_id) DO UPDATE SET
                hektor_mandat_id = excluded.hektor_mandat_id,
                numero_dossier = excluded.numero_dossier,
                numero_mandat = excluded.numero_mandat,
                commercial_id = excluded.commercial_id,
                commercial_nom = excluded.commercial_nom,
                updated_at = CURRENT_TIMESTAMP
            """,
            (hektor_annonce_id, hektor_annonce_id),
        )
        row = con.execute(
            "SELECT id FROM app_dossier WHERE CAST(hektor_annonce_id AS TEXT) = ?",
            (hektor_annonce_id,),
        ).fetchone()
        con.commit()
        return int(row[0]) if row else None
    finally:
        con.execute("DETACH DATABASE hektor")


def seed_target_work_items(con: sqlite3.Connection, app_dossier_id: int) -> None:
    con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
    try:
        con.execute(
            "DELETE FROM app_work_item WHERE workflow_type = 'mandat_diffusion' AND app_dossier_id = ?",
            (app_dossier_id,),
        )
        con.execute(
            """
            INSERT INTO app_work_item (
                app_dossier_id, workflow_type, event_type, status, assigned_role, priority, reason
            )
            SELECT d.id, 'mandat_diffusion', 'mandat_actif_non_diffusable', 'new', 'pauline', 'normal',
                   'Signal automatique : mandat actif non diffusable'
            FROM app_dossier d
            INNER JOIN hektor.case_dossier_source src
                ON src.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
            WHERE d.id = ?
              AND COALESCE(src.archive, '0') = '0'
              AND COALESCE(src.diffusable, '0') <> '1'
              AND COALESCE(src.annonce_source_status, 'present') = 'present'
            """,
            (app_dossier_id,),
        )
        con.execute(
            """
            INSERT INTO app_work_item (
                app_dossier_id, workflow_type, event_type, status, assigned_role, priority, reason
            )
            SELECT d.id, 'mandat_diffusion', 'diffusable_non_visible', 'pending', 'pauline', 'high',
                   'Signal automatique : bien diffusable mais non visible sur les passerelles'
            FROM app_dossier d
            INNER JOIN hektor.case_dossier_source src
                ON src.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
            LEFT JOIN (
                SELECT hektor_annonce_id, SUM(CASE WHEN current_state = 'broadcasted' THEN 1 ELSE 0 END) AS nb_portails_actifs
                FROM hektor.hektor_annonce_broadcast_state
                GROUP BY hektor_annonce_id
            ) ba ON ba.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
            WHERE d.id = ?
              AND COALESCE(src.archive, '0') = '0'
              AND COALESCE(src.diffusable, '0') = '1'
              AND COALESCE(ba.nb_portails_actifs, 0) = 0
              AND COALESCE(src.annonce_source_status, 'present') = 'present'
            """,
            (app_dossier_id,),
        )
        con.execute(
            """
            INSERT INTO app_work_item (
                app_dossier_id, workflow_type, event_type, status, assigned_role, priority, reason
            )
            SELECT d.id, 'mandat_diffusion', 'mandat_archive_cloture', 'pending', 'pauline', 'normal',
                   'Signal automatique : mandat archive avec date de cloture'
            FROM app_dossier d
            INNER JOIN hektor.case_dossier_source src
                ON src.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
            WHERE d.id = ?
              AND COALESCE(src.archive, '0') = '1'
              AND src.mandat_date_cloture IS NOT NULL
              AND COALESCE(src.annonce_source_status, 'present') = 'present'
            """,
            (app_dossier_id,),
        )
        con.execute(
            """
            INSERT INTO app_internal_status (
                app_dossier_id, internal_status, priority, next_action, updated_by
            )
            SELECT
                wi.app_dossier_id,
                CASE WHEN wi.event_type = 'diffusable_non_visible' THEN 'pret_diffusion' ELSE 'a_controler' END,
                wi.priority,
                CASE
                    WHEN wi.event_type = 'mandat_actif_non_diffusable' THEN 'Verifier s''il manque une vraie demande de diffusion ou des elements de validation'
                    WHEN wi.event_type = 'diffusable_non_visible' THEN 'Verifier pourquoi le bien n''est pas visible'
                    WHEN wi.event_type = 'mandat_archive_cloture' THEN 'Verifier la cloture et l''annulation du mandat'
                    ELSE NULL
                END,
                'push_single_annonce_to_supabase'
            FROM app_work_item wi
            WHERE wi.workflow_type = 'mandat_diffusion'
              AND wi.app_dossier_id = ?
            ON CONFLICT(app_dossier_id) DO UPDATE SET
                internal_status = excluded.internal_status,
                priority = excluded.priority,
                next_action = excluded.next_action,
                updated_by = excluded.updated_by,
                updated_at = CURRENT_TIMESTAMP
            """,
            (app_dossier_id,),
        )
        con.commit()
    finally:
        con.execute("DETACH DATABASE hektor")


def extract_create_select(script: str, table_name: str) -> str:
    marker = f"CREATE TABLE {table_name} AS"
    if marker not in script:
        raise RuntimeError(f"CREATE TABLE marker missing for {table_name}")
    body = script.split(marker, 1)[1]
    body = body.split(";\n\nCREATE INDEX", 1)[0]
    return body.strip().rstrip(";")


def create_temp_view_table(con: sqlite3.Connection, table_name: str, create_script: str, app_dossier_id: int) -> None:
    select_sql = extract_create_select(create_script, table_name)
    con.execute(f"DROP TABLE IF EXISTS temp.{table_name}")
    con.execute(
        f"""
        CREATE TEMP TABLE {table_name} AS
        SELECT *
        FROM ({select_sql}) AS generated
        WHERE app_dossier_id = ?
        """,
        (app_dossier_id,),
    )


def delete_target_remote(client: SupabaseRestClient, app_dossier_id: int) -> None:
    for table in (
        "app_dossier_current",
        "app_dossier_detail_current",
        "app_work_item_current",
        "app_mandat_broadcast_current",
        "app_mandat_register_current",
    ):
        client.delete_rows_by_ids(path=table, column="app_dossier_id", ids=[app_dossier_id])


def push_payload(client: SupabaseRestClient, payload: dict[str, Any], app_dossier_id: int) -> dict[str, int]:
    current_dossiers = build_current_dossiers(payload["dossiers"])
    source_updated_at_by_id = {int(row["app_dossier_id"]): row.get("source_updated_at") for row in current_dossiers}
    current_details = build_current_details(payload["dossier_details"], source_updated_at_by_id)
    current_work_items = build_current_work_items(payload["work_items"])
    current_broadcasts = normalize_broadcast_rows(payload.get("broadcasts", []))
    current_mandat_register_rows = build_current_mandat_register_rows(payload.get("mandat_register_rows", []))

    delete_target_remote(client, app_dossier_id)
    if current_dossiers:
        client.upsert_rows(path="app_dossier_current", rows=current_dossiers, batch_size=10)
    if current_details:
        client.upsert_rows(path="app_dossier_detail_current", rows=current_details, batch_size=10)
    if current_work_items:
        client.insert_rows(path="app_work_item_current", rows=current_work_items, batch_size=20)
    if current_broadcasts:
        client.insert_rows(path="app_mandat_broadcast_current", rows=current_broadcasts, batch_size=20)
    if current_mandat_register_rows:
        client.insert_rows(path="app_mandat_register_current", rows=current_mandat_register_rows, batch_size=20)

    return {
        "dossiers_upserted": len(current_dossiers),
        "details_upserted": len(current_details),
        "work_items_replaced": len(current_work_items),
        "broadcasts_replaced": len(current_broadcasts),
        "mandat_register_replaced": len(current_mandat_register_rows),
    }


def main() -> int:
    args = parse_args()
    load_env_file(args.env_file)
    for env_file in EXTRA_ENV_FILES:
        load_env_file(env_file)
    supabase_url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    supabase_service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    started = time.perf_counter()
    hektor_annonce_id = str(args.hektor_annonce_id).strip()
    client = SupabaseRestClient(base_url=supabase_url, service_role_key=supabase_service_role_key)
    delta_run_id = client.insert_delta_run(
        mode="single_annonce_direct",
        notes={
            "generated_from": "phase2/sync/push_single_annonce_to_supabase.py",
            "hektor_annonce_id": hektor_annonce_id,
        },
    )

    try:
        indexed_rows = run_case_index_for_annonce(hektor_annonce_id)
        con = sqlite3.connect(PHASE2_DB)
        try:
            ensure_schema(con)
            app_dossier_id = sync_target_app_dossier(con, hektor_annonce_id)
            if app_dossier_id is None:
                raise RuntimeError(f"app_dossier introuvable pour annonce Hektor {hektor_annonce_id}")
            seed_target_work_items(con, app_dossier_id)
            con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
            try:
                create_temp_view_table(con, "app_view_demandes_mandat_diffusion", SQL_REFRESH_DEMANDES_MANDAT_DIFFUSION, app_dossier_id)
                create_temp_view_table(con, "app_view_generale", SQL_REFRESH_VUE_GENERALE, app_dossier_id)
                payload = build_payload(
                    limit=None,
                    dossier_ids=[app_dossier_id],
                    include_filter_catalog=False,
                    connection=con,
                )
                counts = push_payload(client, payload, app_dossier_id)
            finally:
                con.execute("DETACH DATABASE hektor")
        finally:
            con.close()

        duration = round(time.perf_counter() - started, 3)
        client.update_delta_run(
            delta_run_id,
            {
                "status": "completed",
                "finished_at": now_iso(),
                "dossiers_detected": 1,
                "dossiers_upserted": counts["dossiers_upserted"],
                "details_upserted": counts["details_upserted"],
                "work_items_replaced": counts["work_items_replaced"],
                "filters_replaced": 0,
                "deleted_dossiers": 0,
            },
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": "single_annonce_direct",
                    "delta_run_id": delta_run_id,
                    "hektor_annonce_id": hektor_annonce_id,
                    "app_dossier_id": app_dossier_id,
                    "case_index_rows": indexed_rows,
                    "duration_seconds": duration,
                    **counts,
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        client.update_delta_run(
            delta_run_id,
            {
                "status": "failed",
                "finished_at": now_iso(),
                "notes": {
                    "generated_from": "phase2/sync/push_single_annonce_to_supabase.py",
                    "hektor_annonce_id": hektor_annonce_id,
                    "error": str(exc),
                },
            },
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
