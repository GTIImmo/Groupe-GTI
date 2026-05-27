from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hektor_pipeline.common import (  # noqa: E402
    HektorClient,
    Settings,
    cleanup_stale_sync_runs,
    connect_db,
    create_sync_run,
    finish_sync_run,
    init_db,
    log_sync_error,
    now_utc_iso,
    sleep_brief,
    update_sync_run_progress,
    upsert_raw_response,
)
from sync_raw import (  # noqa: E402
    CONTACT_VARIANTS,
    load_contact_state_map,
    mark_contact_detail_synced,
    set_meta_value,
    sync_contact_listing_variant,
)


CONTACT_DETAIL_ENDPOINT_NAME = "contact_detail"
CONTACT_DETAIL_PATH = "/Api/Contact/ContactById"
CONTACT_DETAIL_SKIP_TABLE = "sync_contact_detail_skip"


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recupere les details ContactById Hektor dans SQLite local, sur le modele du wrapper detail annonce."
    )
    parser.add_argument("--limit", type=int, default=0, help="Nombre maximum de details contact a recuperer. 0 = tous les candidats.")
    parser.add_argument("--batch-size", type=int, default=100, help="Taille des lots de details. Le run reprend naturellement au prochain lancement.")
    parser.add_argument("--force-full", action="store_true", help="Rejouer tous les details contacts, meme ceux deja synchronises.")
    parser.add_argument("--dry-run", action="store_true", help="Afficher le volume candidat sans appeler l'API detail.")
    parser.add_argument("--skip-listing-refresh", action="store_true", help="Ne pas rafraichir le listing contacts avant de choisir les details.")
    parser.add_argument("--full-listing-refresh", action="store_true", help="Relire tout le listing contacts avant les details. Utile pour le run full initial.")
    parser.add_argument("--listing-max-pages", type=int, default=5, help="Pages de listing contacts a rafraichir en mode update. 0 = toutes les pages.")
    parser.add_argument("--contact-scope", choices=["active", "archived", "both"], default="both", help="Scope contacts a traiter.")
    parser.add_argument("--missing-only", action="store_true", help="Ne prendre que les contacts sans detail local, sans rejouer les details modifies.")
    parser.add_argument("--changed-only", action="store_true", help="Compatibilite: comportement par defaut, details absents ou date_maj plus recente.")
    parser.add_argument("--retry-404", action="store_true", help="Retenter les contacts dont ContactById a deja repondu 404. Par defaut ils sont exclus de la reprise.")
    parser.add_argument(
        "--use-last-seen-as-changed",
        action="store_true",
        help=(
            "Mode quotidien apres ListContacts trie par dateLastTraitement: "
            "rejoue aussi les contacts revus dans le dernier listing update."
        ),
    )
    parser.add_argument("--no-normalize", action="store_true", help="Ne pas lancer normalize_source.py apres la recuperation.")
    return parser.parse_args()


def selected_contact_variants(scope: str) -> list[dict[str, Any]]:
    if scope == "both":
        return list(CONTACT_VARIANTS)
    return [variant for variant in CONTACT_VARIANTS if variant["scope"] == scope]


def iter_batches(values: list[str], batch_size: int) -> Iterable[list[str]]:
    size = max(1, batch_size)
    for index in range(0, len(values), size):
        yield values[index:index + size]


def run_normalize() -> None:
    subprocess.run([sys.executable, "normalize_source.py"], cwd=str(ROOT), check=True)


def is_contact_detail_404(error: object) -> bool:
    text = str(error or "").lower()
    return "404 client error" in text or "not found" in text


def ensure_contact_detail_skip(conn) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {CONTACT_DETAIL_SKIP_TABLE} (
            hektor_contact_id TEXT PRIMARY KEY,
            reason TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 1,
            last_error TEXT
        )
        """
    )
    conn.commit()


def mark_contact_detail_skip(conn, contact_id: str, *, reason: str, error_message: str) -> None:
    ensure_contact_detail_skip(conn)
    now = now_utc_iso()
    conn.execute(
        f"""
        INSERT INTO {CONTACT_DETAIL_SKIP_TABLE}(
            hektor_contact_id, reason, first_seen_at, last_seen_at, attempts, last_error
        )
        VALUES (?, ?, ?, ?, 1, ?)
        ON CONFLICT(hektor_contact_id) DO UPDATE SET
            reason = excluded.reason,
            last_seen_at = excluded.last_seen_at,
            attempts = {CONTACT_DETAIL_SKIP_TABLE}.attempts + 1,
            last_error = excluded.last_error
        """,
        (contact_id, reason, now, now, error_message[:1000]),
    )


def backfill_contact_detail_404_skips(conn) -> int:
    ensure_contact_detail_skip(conn)
    rows = conn.execute(
        """
        SELECT object_id, MAX(created_at) AS last_seen_at, MAX(error_message) AS last_error
        FROM sync_error
        WHERE stage = 'sync_contact_details'
          AND endpoint_name = ?
          AND object_type = 'contact_detail'
          AND NULLIF(TRIM(object_id), '') IS NOT NULL
          AND (
              lower(error_message) LIKE '%404 client error%'
              OR lower(error_message) LIKE '%not found%'
          )
        GROUP BY object_id
        """,
        (CONTACT_DETAIL_ENDPOINT_NAME,),
    ).fetchall()
    if not rows:
        return 0
    now = now_utc_iso()
    conn.executemany(
        f"""
        INSERT INTO {CONTACT_DETAIL_SKIP_TABLE}(
            hektor_contact_id, reason, first_seen_at, last_seen_at, attempts, last_error
        )
        VALUES (?, 'http_404_not_found', ?, ?, 1, ?)
        ON CONFLICT(hektor_contact_id) DO UPDATE SET
            reason = excluded.reason,
            last_seen_at = excluded.last_seen_at,
            last_error = excluded.last_error
        """,
        [
            (
                clean_text(row["object_id"]),
                clean_text(row["last_seen_at"]) or now,
                clean_text(row["last_seen_at"]) or now,
                clean_text(row["last_error"])[:1000],
            )
            for row in rows
            if clean_text(row["object_id"])
        ],
    )
    conn.commit()
    return len(rows)


def backfill_contact_detail_sync_markers(conn) -> int:
    rows = conn.execute(
        """
        SELECT object_id_key, MAX(fetched_at) AS fetched_at
        FROM raw_api_response
        WHERE endpoint_name = ?
          AND object_type = 'contact_detail'
          AND NULLIF(TRIM(object_id_key), '') IS NOT NULL
        GROUP BY object_id_key
        """,
        (CONTACT_DETAIL_ENDPOINT_NAME,),
    ).fetchall()
    if not rows:
        return 0
    updated_count = 0
    for row in rows:
        cursor = conn.execute(
            """
            UPDATE sync_contact_state
            SET last_detail_sync_at = ?
            WHERE last_detail_sync_at IS NULL
              AND hektor_contact_id = ?
            """,
            (row["fetched_at"], row["object_id_key"]),
        )
        updated_count += int(cursor.rowcount or 0)
    conn.commit()
    return updated_count


def count_contact_rows(conn, scope: str) -> dict[str, int]:
    scope_filter = ""
    params: list[Any] = [CONTACT_DETAIL_ENDPOINT_NAME]
    if scope != "both":
        scope_filter = "WHERE s.listing_variant = ?"
        params.append(scope)
    row = conn.execute(
        f"""
        SELECT
            COUNT(*) AS contact_total,
            SUM(CASE WHEN r.object_id_key IS NOT NULL THEN 1 ELSE 0 END) AS contact_with_detail,
            SUM(CASE WHEN s.last_detail_sync_at IS NOT NULL THEN 1 ELSE 0 END) AS contact_marked_synced
        FROM sync_contact_state s
        LEFT JOIN raw_api_response r
          ON r.endpoint_name = ?
         AND r.object_type = 'contact_detail'
         AND r.object_id_key = s.hektor_contact_id
        {scope_filter}
        """,
        params,
    ).fetchone()
    return {
        "contact_total": int(row["contact_total"] or 0),
        "contact_with_detail": int(row["contact_with_detail"] or 0),
        "contact_marked_synced": int(row["contact_marked_synced"] or 0),
    }


def load_contact_detail_candidate_ids(
    conn,
    *,
    scope: str,
    force_full: bool,
    missing_only: bool,
    use_last_seen_as_changed: bool,
    retry_404: bool,
    limit: int,
) -> list[str]:
    where_parts: list[str] = []
    params: list[Any] = [CONTACT_DETAIL_ENDPOINT_NAME]
    if scope != "both":
        where_parts.append("s.listing_variant = ?")
        params.append(scope)
    if not retry_404:
        where_parts.append("k.hektor_contact_id IS NULL")

    if not force_full:
        if missing_only:
            where_parts.append("(r.object_id_key IS NULL OR s.last_detail_sync_at IS NULL)")
        else:
            where_parts.append(
                """
                (
                    r.object_id_key IS NULL
                    OR s.last_detail_sync_at IS NULL
                    OR (
                        NULLIF(s.date_maj, '') IS NOT NULL
                        AND datetime(replace(s.date_maj, 'T', ' ')) > datetime(replace(substr(s.last_detail_sync_at, 1, 19), 'T', ' '))
                    )
                    {last_seen_condition}
                )
                """
                .format(
                    last_seen_condition="""
                    OR (
                        NULLIF(s.last_seen_at, '') IS NOT NULL
                        AND datetime(replace(substr(s.last_seen_at, 1, 19), 'T', ' ')) > datetime(replace(substr(s.last_detail_sync_at, 1, 19), 'T', ' '))
                    )
                    """
                    if use_last_seen_as_changed
                    else ""
                )
            )

    where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    sql = f"""
        SELECT s.hektor_contact_id
        FROM sync_contact_state s
        LEFT JOIN raw_api_response r
          ON r.endpoint_name = ?
         AND r.object_type = 'contact_detail'
         AND r.object_id_key = s.hektor_contact_id
        LEFT JOIN {CONTACT_DETAIL_SKIP_TABLE} k
          ON k.hektor_contact_id = s.hektor_contact_id
         AND k.reason = 'http_404_not_found'
        {where_sql}
        ORDER BY
            CASE WHEN r.object_id_key IS NULL THEN 0 ELSE 1 END,
            COALESCE(s.date_maj, '') DESC,
            CAST(s.hektor_contact_id AS INTEGER) ASC,
            s.hektor_contact_id ASC
    """
    if limit and limit > 0:
        sql += "\nLIMIT ?"
        params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [clean_text(row["hektor_contact_id"]) for row in rows if clean_text(row["hektor_contact_id"])]


def sync_contact_details(conn, run_id: int, client: HektorClient, settings: Settings, contact_ids: list[str]) -> dict[str, int]:
    total_objects = len(contact_ids)
    success_count = 0
    error_count = 0
    update_sync_run_progress(
        conn,
        run_id,
        current_step="detail",
        current_resource="contacts",
        current_endpoint=CONTACT_DETAIL_ENDPOINT_NAME,
        current_object_id=None,
        current_page=None,
        progress_done=0,
        progress_total=total_objects,
        progress_unit="objects",
    )
    for index, contact_id in enumerate(contact_ids, start=1):
        params = {"id": contact_id, "version": settings.api_version}
        try:
            payload = client.get_json(CONTACT_DETAIL_PATH, params=params)
        except Exception as exc:
            error_count += 1
            error_message = str(exc)
            log_sync_error(
                conn,
                run_id=run_id,
                stage="sync_contact_details",
                endpoint_name=CONTACT_DETAIL_ENDPOINT_NAME,
                object_type="contact_detail",
                object_id=contact_id,
                page=None,
                error_message=error_message,
            )
            if is_contact_detail_404(exc):
                mark_contact_detail_skip(
                    conn,
                    contact_id,
                    reason="http_404_not_found",
                    error_message=error_message,
                )
            conn.commit()
            continue
        upsert_raw_response(
            conn,
            run_id=run_id,
            endpoint_name=CONTACT_DETAIL_ENDPOINT_NAME,
            object_type="contact_detail",
            object_id=contact_id,
            page=None,
            params=params,
            payload=payload,
            http_status=200,
        )
        mark_contact_detail_synced(conn, contact_id)
        success_count += 1
        update_sync_run_progress(
            conn,
            run_id,
            current_step="detail",
            current_resource="contacts",
            current_endpoint=CONTACT_DETAIL_ENDPOINT_NAME,
            current_object_id=contact_id,
            current_page=None,
            progress_done=index,
            progress_total=total_objects,
            progress_unit="objects",
        )
        conn.commit()
        sleep_brief()
    return {"success_count": success_count, "error_count": error_count}


def main() -> int:
    args = parse_args()
    settings = Settings.from_env()
    settings.db_path = settings.db_path if settings.db_path.is_absolute() else ROOT / settings.db_path
    conn = connect_db(settings.db_path)
    init_db(conn)
    cleanup_stale_sync_runs(conn)
    run_id = create_sync_run(conn, "sync_contact_details")
    client = HektorClient(settings)

    try:
        if not args.dry_run or not args.skip_listing_refresh:
            update_sync_run_progress(conn, run_id, current_step="authenticate", progress_done=0, progress_total=1, progress_unit="step")
            client.authenticate()

        if not args.skip_listing_refresh:
            state_map = load_contact_state_map(conn)
            for variant in selected_contact_variants(args.contact_scope):
                changed_ids, max_seen_date = sync_contact_listing_variant(
                    conn,
                    run_id,
                    client,
                    settings,
                    variant=variant,
                    state_map=state_map,
                    max_pages=None if args.listing_max_pages == 0 else args.listing_max_pages,
                    use_update_endpoint=not args.full_listing_refresh,
                    bootstrap=args.full_listing_refresh,
                )
                if max_seen_date:
                    set_meta_value(conn, f"contact_cursor_{variant['scope']}", max_seen_date)
                print(
                    "Contact listing refreshed: "
                    f"scope={variant['scope']} changed={len(changed_ids)} max_seen_date={max_seen_date or ''}"
                )

        marker_count = backfill_contact_detail_sync_markers(conn)
        skipped_404_count = backfill_contact_detail_404_skips(conn)
        before = count_contact_rows(conn, args.contact_scope)
        detail_ids = load_contact_detail_candidate_ids(
            conn,
            scope=args.contact_scope,
            force_full=args.force_full,
            missing_only=args.missing_only,
            use_last_seen_as_changed=args.use_last_seen_as_changed,
            retry_404=args.retry_404,
            limit=args.limit,
        )
        print(
            "Contact detail candidates: "
            f"{len(detail_ids)} / total={before['contact_total']} "
            f"with_detail={before['contact_with_detail']} marked_synced={before['contact_marked_synced']} "
            f"markers_backfilled={marker_count} skipped_404={skipped_404_count}"
        )

        if args.dry_run:
            finish_sync_run(conn, run_id, "success", notes="dry-run")
            return 0

        total = len(detail_ids)
        done = 0
        success_total = 0
        error_total = 0
        for batch in iter_batches(detail_ids, args.batch_size):
            result = sync_contact_details(conn, run_id, client, settings, batch)
            done += len(batch)
            success_total += result["success_count"]
            error_total += result["error_count"]
            update_sync_run_progress(
                conn,
                run_id,
                current_step="contact_detail_batch",
                current_resource="contacts",
                current_endpoint=CONTACT_DETAIL_ENDPOINT_NAME,
                progress_done=done,
                progress_total=total,
                progress_unit="objects",
            )
            print(f"Contact details synced: {done}/{total} success={success_total} errors={error_total}")

        if total and not args.no_normalize:
            update_sync_run_progress(conn, run_id, current_step="normalize_source", progress_done=0, progress_total=1, progress_unit="step")
            run_normalize()

        after = count_contact_rows(conn, args.contact_scope)
        finish_sync_run(
            conn,
            run_id,
            "success_with_errors" if error_total else "success",
            notes=(
                f"details_synced={success_total}; errors={error_total}; "
                f"before_with_detail={before['contact_with_detail']}; "
                f"after_with_detail={after['contact_with_detail']}"
            ),
        )
        print(
            "Contact detail run completed: "
            f"selected={total} success={success_total} errors={error_total} "
            f"total={after['contact_total']} with_detail={after['contact_with_detail']}"
        )
        return 0
    except KeyboardInterrupt:
        finish_sync_run(conn, run_id, "interrupted", notes="KeyboardInterrupt")
        raise
    except Exception as exc:
        finish_sync_run(conn, run_id, "failed", notes=str(exc))
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
