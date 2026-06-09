from __future__ import annotations

import argparse
import subprocess
import sys
import time
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


SCOPE_CHOICES = ("all", "active", "archived")
SELECTION_MODE_CHOICES = ("missing_only", "missing_or_stale")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recupere prudemment les details AnnonceById manquants dans SQLite local."
    )
    parser.add_argument(
        "--scope",
        choices=SCOPE_CHOICES,
        default="all",
        help="Perimetre a traiter. all = actives + archivees.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Nombre maximum de details a recuperer. 0 = tous les candidats.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Taille des lots de details. Le run reprend naturellement au prochain lancement.",
    )
    parser.add_argument(
        "--batch-pause-seconds",
        type=int,
        default=60,
        help="Pause entre deux lots. 0 = pas de pause.",
    )
    parser.add_argument(
        "--request-delay-seconds",
        type=float,
        default=0.1,
        help="Pause entre deux appels API detail/relation. Aligne par defaut sur le rattrapage contacts.",
    )
    parser.add_argument(
        "--selection-mode",
        choices=SELECTION_MODE_CHOICES,
        default="missing_only",
        help="missing_only ne prend que les fiches absentes. missing_or_stale imite le rattrapage archive historique.",
    )
    parser.add_argument(
        "--force-full",
        action="store_true",
        help="Rejouer tous les details du perimetre, meme ceux deja synchronises.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher le volume candidat sans authentification et sans appel API.",
    )
    parser.add_argument(
        "--refresh-listing",
        action="store_true",
        help="Rafraichir le listing Hektor avant de choisir les details. Desactive par defaut pour proteger le perimetre local.",
    )
    parser.add_argument(
        "--full-listing-refresh",
        action="store_true",
        help="Avec --refresh-listing, relire tout le listing au lieu de l'endpoint update.",
    )
    parser.add_argument(
        "--listing-max-pages",
        type=int,
        default=5,
        help="Pages de listing a rafraichir si --refresh-listing est actif. 0 = toutes les pages.",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Ne pas lancer normalize_source.py apres la recuperation.",
    )
    return parser.parse_args()


def scope_where(scope: str) -> str:
    if scope == "active":
        return "coalesce(a.archive, '0') <> '1'"
    if scope == "archived":
        return "coalesce(a.archive, '0') = '1'"
    return "1 = 1"


def variants_for_scope(scope: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for variant in ANNONCE_VARIANTS:
        if scope == "active" and variant["scope"] != "active":
            continue
        if scope == "archived" and variant["scope"] != "archived":
            continue
        output.append(variant)
    return output


def count_scope_rows(conn, *, scope: str) -> dict[str, int]:
    row = conn.execute(
        f"""
        select
            count(*) as total,
            sum(case when d.hektor_annonce_id is not null then 1 else 0 end) as with_detail,
            sum(case when d.hektor_annonce_id is null then 1 else 0 end) as missing_detail,
            sum(case when s.last_detail_sync_at is not null then 1 else 0 end) as marked_synced
        from hektor_annonce a
        left join hektor_annonce_detail d on d.hektor_annonce_id = a.hektor_annonce_id
        left join sync_annonce_state s on s.hektor_annonce_id = a.hektor_annonce_id
        where {scope_where(scope)}
        """
    ).fetchone()
    return {
        "total": int(row["total"] or 0),
        "with_detail": int(row["with_detail"] or 0),
        "missing_detail": int(row["missing_detail"] or 0),
        "marked_synced": int(row["marked_synced"] or 0),
    }


def load_detail_candidate_ids(
    conn,
    *,
    scope: str,
    force_full: bool,
    selection_mode: str,
    limit: int,
) -> list[str]:
    if force_full:
        candidate_clause = "1 = 1"
    elif selection_mode == "missing_or_stale":
        candidate_clause = """
            (
                d.hektor_annonce_id is null
                or s.last_detail_sync_at is null
                or (
                    nullif(a.date_maj, '') is not null
                    and a.date_maj <> '0000-00-00 00:00:00'
                    and datetime(replace(a.date_maj, 'T', ' ')) > datetime(replace(substr(s.last_detail_sync_at, 1, 19), 'T', ' '))
                )
            )
        """
    else:
        candidate_clause = "d.hektor_annonce_id is null"

    sql = f"""
        select a.hektor_annonce_id
        from hektor_annonce a
        left join hektor_annonce_detail d on d.hektor_annonce_id = a.hektor_annonce_id
        left join sync_annonce_state s on s.hektor_annonce_id = a.hektor_annonce_id
        where {scope_where(scope)}
          and {candidate_clause}
        order by
            case when coalesce(a.archive, '0') <> '1' and coalesce(a.diffusable, '0') = '1' then 0 else 1 end,
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


def refresh_listing(conn, run_id: int, client: HektorClient, settings: Settings, *, scope: str, full_listing_refresh: bool, listing_max_pages: int) -> None:
    for variant in variants_for_scope(scope):
        state_map = load_annonce_state_map(conn)
        changed_ids, seen_ids, max_seen_date, last_page = sync_annonce_listing_variant(
            conn,
            run_id,
            client,
            settings,
            variant=variant,
            state_map=state_map,
            max_pages=None if listing_max_pages == 0 else listing_max_pages,
            use_update_endpoint=not full_listing_refresh,
            bootstrap=full_listing_refresh,
        )
        if full_listing_refresh:
            prune_raw_listing_pages(conn, endpoint_name=variant["base_endpoint_name"], max_page=last_page)
        if max_seen_date:
            set_meta_value(conn, f"annonce_cursor_{variant['scope']}", max_seen_date)
        print(
            "Listing refreshed: "
            f"scope={variant['scope']} seen={len(seen_ids)} changed={len(changed_ids)} last_page={last_page}"
        )


def run_normalize() -> None:
    subprocess.run([sys.executable, "normalize_source.py"], check=True)


def count_run_errors(conn, run_id: int) -> int:
    row = conn.execute(
        """
        select count(*) as n
        from sync_error
        where run_id = ?
          and endpoint_name in ('annonce_detail', 'mandats_by_annonce')
        """,
        (run_id,),
    ).fetchone()
    return int(row["n"] or 0)


def count_run_detail_success(conn, run_id: int) -> int:
    row = conn.execute(
        """
        select count(*) as n
        from raw_api_response
        where run_id = ?
          and endpoint_name = 'annonce_detail'
        """,
        (run_id,),
    ).fetchone()
    return int(row["n"] or 0)


def main() -> int:
    args = parse_args()
    settings = Settings.from_env()
    conn = connect_db(settings.db_path)
    init_db(conn)

    try:
        if args.dry_run:
            before = count_scope_rows(conn, scope=args.scope)
            detail_ids = load_detail_candidate_ids(
                conn,
                scope=args.scope,
                force_full=args.force_full,
                selection_mode=args.selection_mode,
                limit=args.limit,
            )
            print(
                "Annonce detail candidates: "
                f"{len(detail_ids)} / total={before['total']} "
                f"with_detail={before['with_detail']} missing_detail={before['missing_detail']} "
                f"marked_synced={before['marked_synced']} scope={args.scope} "
                f"selection_mode={'force_full' if args.force_full else args.selection_mode}"
            )
            return 0

        cleanup_stale_sync_runs(conn)
        run_id = create_sync_run(conn, "sync_annonce_details_backfill")
        client = HektorClient(settings)

        try:
            update_sync_run_progress(
                conn,
                run_id,
                current_step="authenticate",
                progress_done=0,
                progress_total=1,
                progress_unit="step",
            )
            client.authenticate()

            if args.refresh_listing:
                refresh_listing(
                    conn,
                    run_id,
                    client,
                    settings,
                    scope=args.scope,
                    full_listing_refresh=args.full_listing_refresh,
                    listing_max_pages=args.listing_max_pages,
                )

            before = count_scope_rows(conn, scope=args.scope)
            detail_ids = load_detail_candidate_ids(
                conn,
                scope=args.scope,
                force_full=args.force_full,
                selection_mode=args.selection_mode,
                limit=args.limit,
            )
            print(
                "Annonce detail candidates: "
                f"{len(detail_ids)} / total={before['total']} "
                f"with_detail={before['with_detail']} missing_detail={before['missing_detail']} "
                f"marked_synced={before['marked_synced']} scope={args.scope} "
                f"selection_mode={'force_full' if args.force_full else args.selection_mode}"
            )

            total = len(detail_ids)
            done = 0
            for batch in iter_batches(detail_ids, args.batch_size):
                sync_annonce_details(conn, run_id, client, settings, batch, delay_seconds=args.request_delay_seconds)
                sync_mandats_by_annonce(conn, run_id, client, settings, batch, delay_seconds=args.request_delay_seconds)
                done += len(batch)
                update_sync_run_progress(
                    conn,
                    run_id,
                    current_step="annonce_detail_batch",
                    current_resource="annonces",
                    current_endpoint="annonce_detail",
                    progress_done=done,
                    progress_total=total,
                    progress_unit="objects",
                )
                print(f"Annonce details synced: {done}/{total}")
                if args.batch_pause_seconds > 0 and done < total:
                    time.sleep(args.batch_pause_seconds)

            detail_success = count_run_detail_success(conn, run_id)
            errors = count_run_errors(conn, run_id)

            if total and not args.no_normalize:
                update_sync_run_progress(
                    conn,
                    run_id,
                    current_step="normalize_source",
                    progress_done=0,
                    progress_total=1,
                    progress_unit="step",
                )
                run_normalize()

            after = count_scope_rows(conn, scope=args.scope)
            status = "success_with_errors" if errors else "success"
            finish_sync_run(
                conn,
                run_id,
                status,
                notes=(
                    f"scope={args.scope}; "
                    f"selection_mode={'force_full' if args.force_full else args.selection_mode}; "
                    f"details_requested={total}; details_success={detail_success}; errors={errors}; "
                    f"before_with_detail={before['with_detail']}; after_with_detail={after['with_detail']}; "
                    f"before_missing_detail={before['missing_detail']}; after_missing_detail={after['missing_detail']}"
                ),
            )
            print(
                "Annonce detail run completed: "
                f"requested={total} success={detail_success} errors={errors} "
                f"total={after['total']} with_detail={after['with_detail']} missing_detail={after['missing_detail']}"
            )
            return 0
        except Exception as exc:
            finish_sync_run(conn, run_id, "failed", notes=str(exc))
            raise
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
