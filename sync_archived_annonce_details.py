from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Any

from hektor_pipeline.common import (
    HektorClient,
    Settings,
    cleanup_stale_sync_runs,
    connect_db,
    create_sync_run,
    finish_sync_run,
    init_db,
    update_sync_run_progress,
)
from sync_raw import (
    ANNONCE_VARIANTS,
    load_annonce_state_map,
    prune_raw_listing_pages,
    set_meta_value,
    sync_annonce_details,
    sync_annonce_listing_variant,
    sync_mandats_by_annonce,
)


ARCHIVED_VARIANT = next(variant for variant in ANNONCE_VARIANTS if variant["scope"] == "archived")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recupere uniquement les details des annonces archivees Hektor dans SQLite local."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Nombre maximum de details archive a recuperer. 0 = tous les candidats.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Taille des lots de details. Le run reprend naturellement au prochain lancement.",
    )
    parser.add_argument(
        "--force-full",
        action="store_true",
        help="Rejouer tous les details archives, meme ceux deja synchronises.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher le volume candidat sans appeler l'API detail.",
    )
    parser.add_argument(
        "--skip-listing-refresh",
        action="store_true",
        help="Ne pas rafraichir le listing archive avant de choisir les details.",
    )
    parser.add_argument(
        "--full-listing-refresh",
        action="store_true",
        help="Relire tout le listing archive avant les details. Utile si le listing archive local est vide.",
    )
    parser.add_argument(
        "--listing-max-pages",
        type=int,
        default=5,
        help="Pages de listing archive a rafraichir en mode update. 0 = toutes les pages.",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Ne pas lancer normalize_source.py apres la recuperation.",
    )
    return parser.parse_args()


def count_archived_rows(conn) -> dict[str, int]:
    row = conn.execute(
        """
        select
            count(*) as archived_total,
            sum(case when d.hektor_annonce_id is not null then 1 else 0 end) as archived_with_detail,
            sum(case when s.last_detail_sync_at is not null then 1 else 0 end) as archived_marked_synced
        from hektor_annonce a
        left join hektor_annonce_detail d on d.hektor_annonce_id = a.hektor_annonce_id
        left join sync_annonce_state s on s.hektor_annonce_id = a.hektor_annonce_id
        where a.archive = '1'
        """
    ).fetchone()
    return {
        "archived_total": int(row["archived_total"] or 0),
        "archived_with_detail": int(row["archived_with_detail"] or 0),
        "archived_marked_synced": int(row["archived_marked_synced"] or 0),
    }


def load_archived_detail_candidate_ids(conn, *, force_full: bool, limit: int) -> list[str]:
    if force_full:
        where_clause = "a.archive = '1'"
    else:
        where_clause = """
            a.archive = '1'
            and (
                d.hektor_annonce_id is null
                or s.last_detail_sync_at is null
                or (
                    nullif(a.date_maj, '') is not null
                    and datetime(replace(a.date_maj, 'T', ' ')) > datetime(replace(substr(s.last_detail_sync_at, 1, 19), 'T', ' '))
                )
            )
        """
    sql = f"""
        select a.hektor_annonce_id
        from hektor_annonce a
        left join hektor_annonce_detail d on d.hektor_annonce_id = a.hektor_annonce_id
        left join sync_annonce_state s on s.hektor_annonce_id = a.hektor_annonce_id
        where {where_clause}
        order by
            case when d.hektor_annonce_id is null then 0 else 1 end,
            coalesce(a.date_maj, '') desc,
            cast(a.hektor_annonce_id as integer) asc
    """
    params: tuple[Any, ...] = ()
    if limit and limit > 0:
        sql += "\nlimit ?"
        params = (limit,)
    rows = conn.execute(sql, params).fetchall()
    return [str(row["hektor_annonce_id"]).strip() for row in rows if str(row["hektor_annonce_id"] or "").strip()]


def iter_batches(values: list[str], batch_size: int):
    size = max(1, batch_size)
    for index in range(0, len(values), size):
        yield values[index:index + size]


def run_normalize() -> None:
    subprocess.run([sys.executable, "normalize_source.py"], check=True)


def main() -> int:
    args = parse_args()
    settings = Settings.from_env()
    conn = connect_db(settings.db_path)
    init_db(conn)
    cleanup_stale_sync_runs(conn)
    run_id = create_sync_run(conn, "sync_archived_annonce_details")
    client = HektorClient(settings)

    try:
        update_sync_run_progress(conn, run_id, current_step="authenticate", progress_done=0, progress_total=1, progress_unit="step")
        client.authenticate()

        if not args.skip_listing_refresh:
            state_map = load_annonce_state_map(conn)
            changed_ids, seen_ids, max_seen_date, last_page = sync_annonce_listing_variant(
                conn,
                run_id,
                client,
                settings,
                variant=ARCHIVED_VARIANT,
                state_map=state_map,
                max_pages=None if args.listing_max_pages == 0 else args.listing_max_pages,
                use_update_endpoint=not args.full_listing_refresh,
                bootstrap=args.full_listing_refresh,
            )
            prune_raw_listing_pages(conn, endpoint_name=ARCHIVED_VARIANT["base_endpoint_name"], max_page=last_page)
            if max_seen_date:
                set_meta_value(conn, "annonce_cursor_archived", max_seen_date)
            print(
                "Archived listing refreshed: "
                f"seen={len(seen_ids)} changed={len(changed_ids)} last_page={last_page}"
            )

        before = count_archived_rows(conn)
        detail_ids = load_archived_detail_candidate_ids(conn, force_full=args.force_full, limit=args.limit)
        print(
            "Archived detail candidates: "
            f"{len(detail_ids)} / total={before['archived_total']} "
            f"with_detail={before['archived_with_detail']} marked_synced={before['archived_marked_synced']}"
        )

        if args.dry_run:
            finish_sync_run(conn, run_id, "success", notes="dry-run")
            return 0

        total = len(detail_ids)
        done = 0
        for batch in iter_batches(detail_ids, args.batch_size):
            sync_annonce_details(conn, run_id, client, settings, batch)
            sync_mandats_by_annonce(conn, run_id, client, settings, batch)
            done += len(batch)
            update_sync_run_progress(
                conn,
                run_id,
                current_step="archived_detail_batch",
                current_resource="annonces",
                current_endpoint="annonce_detail",
                progress_done=done,
                progress_total=total,
                progress_unit="objects",
            )
            print(f"Archived details synced: {done}/{total}")

        if total and not args.no_normalize:
            update_sync_run_progress(conn, run_id, current_step="normalize_source", progress_done=0, progress_total=1, progress_unit="step")
            run_normalize()

        after = count_archived_rows(conn)
        finish_sync_run(
            conn,
            run_id,
            "success",
            notes=(
                f"details_synced={total}; "
                f"before_with_detail={before['archived_with_detail']}; "
                f"after_with_detail={after['archived_with_detail']}"
            ),
        )
        print(
            "Archived detail run completed: "
            f"synced={total} total={after['archived_total']} with_detail={after['archived_with_detail']}"
        )
        return 0
    except Exception as exc:
        finish_sync_run(conn, run_id, "failed", notes=str(exc))
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
