from __future__ import annotations

import argparse
import copy
import json
import os
from datetime import date, timedelta
from math import ceil
from typing import Any, Dict, Iterable, Optional

from hektor_pipeline.common import (
    HektorClient,
    Settings,
    cleanup_stale_sync_runs,
    connect_db,
    create_sync_run,
    fetch_latest_raw_payloads,
    finish_sync_run,
    init_db,
    log_sync_error,
    now_utc_iso,
    sleep_brief,
    update_sync_run_progress,
    upsert_raw_response,
)


ANNONCE_VARIANTS = (
    {
        "scope": "active",
        "archive": 0,
        "base_endpoint_name": "list_annonces_active",
        "update_endpoint_name": "list_annonces_active_update",
        "object_type": "annonce_active",
    },
)

CONTACT_VARIANTS = (
    {
        "scope": "active",
        "archive": 0,
        "base_endpoint_name": "list_contacts_active",
        "update_endpoint_name": "list_contacts_active_update",
        "object_type": "contact_active",
    },
    {
        "scope": "archived",
        "archive": 1,
        "base_endpoint_name": "list_contacts_archived",
        "update_endpoint_name": "list_contacts_archived_update",
        "object_type": "contact_archived",
    },
)

GENERIC_RESOURCE_CONFIG: Dict[str, Dict[str, Any]] = {
    "agences": {
        "endpoint_name": "list_agences",
        "path": "/Api/Agence/ListAgences/",
        "object_type": "agence",
        "paged": False,
    },
    "negos": {
        "endpoint_name": "list_negos",
        "path": "/Api/Negociateur/listNegos/",
        "object_type": "negociateur",
        "paged": True,
        "extra_params": {"actif": 1},
    },
    "mandats": {
        "endpoint_name": "list_mandats",
        "update_endpoint_name": "list_mandats_update",
        "path": "/Api/Mandat/ListMandat",
        "object_type": "mandat",
        "paged": True,
        "extra_params": {"beginDate": "2020-01-01", "endDate": "2030-12-31"},
    },
    "offres": {
        "endpoint_name": "list_offres",
        "update_endpoint_name": "list_offres_update",
        "path": "/Api/Offre/ListOffres/",
        "object_type": "offre",
        "paged": True,
        "extra_params": {"withOfferStatus": "false"},
    },
    "compromis": {
        "endpoint_name": "list_compromis",
        "update_endpoint_name": "list_compromis_update",
        "path": "/Api/Vente/ListCompromis/",
        "object_type": "compromis",
        "paged": True,
        "extra_params": {"withCompromisStatus": "false"},
    },
    "ventes": {
        "endpoint_name": "list_ventes",
        "update_endpoint_name": "list_ventes_update",
        "path": "/Api/Vente/ListVentes/",
        "object_type": "vente",
        "paged": True,
        "extra_params": {"dateStart": "2020-01-01", "dateEnd": "2030-12-31"},
    },
    "broadcasts": {
        "endpoint_name": "list_broadcasts",
        "path": "/Api/Passerelle/DetailedBroadcastList/",
        "object_type": "broadcast",
        "paged": True,
    },
}

DETAIL_CONFIG: Dict[str, Dict[str, Any]] = {
    "annonces": {
        "endpoint_name": "annonce_detail",
        "path": "/Api/Annonce/AnnonceById/",
        "object_type": "annonce_detail",
        "id_param": "id",
    },
    "mandats": {
        "endpoint_name": "mandat_detail",
        "path": "/Api/Mandat/MandatById/",
        "object_type": "mandat_detail",
        "id_param": "id",
    },
    "offres": {
        "endpoint_name": "offre_detail",
        "path": "/Api/Offre/OffreById/",
        "object_type": "offre_detail",
        "id_param": "id",
    },
    "compromis": {
        "endpoint_name": "compromis_detail",
        "path": "/Api/Vente/CompromisById/",
        "object_type": "compromis_detail",
        "id_param": "idCompromis",
    },
    "ventes": {
        "endpoint_name": "vente_detail",
        "path": "/Api/Vente/VenteById/",
        "object_type": "vente_detail",
        "id_param": "id",
    },
}

MANDAT_RELATION_CONFIG = {
    "endpoint_name": "mandats_by_annonce",
    "path": "/Api/Mandat/MandatsByIdAnnonce/",
    "object_type": "mandat_by_annonce",
    "target_param": "idAnnonce",
}

SQLITE_MAX_VARIABLES = 900


def iter_pages(max_pages: Optional[int]) -> Iterable[int]:
    page = 0
    while max_pages is None or page < max_pages:
        yield page
        page += 1


def chunked_values(values: Iterable[str], chunk_size: int = SQLITE_MAX_VARIABLES) -> Iterable[list[str]]:
    batch: list[str] = []
    for value in values:
        batch.append(value)
        if len(batch) >= chunk_size:
            yield batch
            batch = []
    if batch:
        yield batch


def bool_string(value: bool) -> str:
    return "true" if value else "false"


def iso_date_months_ago(months: int) -> str:
    return (date.today() - timedelta(days=max(months, 0) * 30)).isoformat()


def expected_total_from_payload(payload: Dict[str, Any], default_total: int) -> int:
    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        return default_total
    try:
        meta_total = int(metadata.get("total") or 0)
        per_page = int(metadata.get("perPage") or 0)
    except (TypeError, ValueError):
        meta_total = 0
        per_page = 0
    if meta_total > 0 and per_page > 0:
        pages = (meta_total + per_page - 1) // per_page
        return pages if pages > 0 else default_total
    return default_total


def purge_database_files(db_path: str) -> None:
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(f"{db_path}{suffix}")
        except FileNotFoundError:
            pass


def get_meta_value(conn, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM sync_meta WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row and row["value"] is not None else None


def set_meta_value(conn, key: str, value: Optional[str]) -> None:
    conn.execute(
        """
        INSERT INTO sync_meta(key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
        """,
        (key, value, now_utc_iso()),
    )
    conn.commit()


def has_any_annonce_state(conn) -> bool:
    row = conn.execute("SELECT 1 FROM sync_annonce_state LIMIT 1").fetchone()
    return row is not None


def load_annonce_state_map(conn) -> Dict[str, str]:
    rows = conn.execute("SELECT hektor_annonce_id, date_maj FROM sync_annonce_state").fetchall()
    return {str(row["hektor_annonce_id"]): str(row["date_maj"] or "") for row in rows}


def load_contact_state_map(conn) -> Dict[str, str]:
    rows = conn.execute("SELECT hektor_contact_id, date_maj FROM sync_contact_state").fetchall()
    return {str(row["hektor_contact_id"]): str(row["date_maj"] or "") for row in rows}


def load_annonce_ids_missing_detail_sync(conn) -> list[str]:
    rows = conn.execute(
        """
        SELECT hektor_annonce_id
        FROM sync_annonce_state
        WHERE last_detail_sync_at IS NULL
        ORDER BY hektor_annonce_id
        """
    ).fetchall()
    return [str(row["hektor_annonce_id"]).strip() for row in rows if str(row["hektor_annonce_id"] or "").strip()]


def upsert_annonce_state(conn, *, annonce_id: str, listing_variant: str, date_maj: Optional[str]) -> None:
    now_iso = now_utc_iso()
    conn.execute(
        """
        INSERT INTO sync_annonce_state(hektor_annonce_id, listing_variant, date_maj, last_seen_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(hektor_annonce_id) DO UPDATE SET
            listing_variant = excluded.listing_variant,
            date_maj = excluded.date_maj,
            last_seen_at = excluded.last_seen_at
        """,
        (annonce_id, listing_variant, date_maj, now_iso),
    )


def mark_annonce_detail_synced(conn, annonce_id: str) -> None:
    conn.execute(
        """
        UPDATE sync_annonce_state
        SET last_detail_sync_at = ?
        WHERE hektor_annonce_id = ?
        """,
        (now_utc_iso(), annonce_id),
    )


def upsert_contact_state(
    conn,
    *,
    contact_id: str,
    listing_variant: str,
    date_last_traitement: Optional[str],
    date_maj: Optional[str],
) -> None:
    now_iso = now_utc_iso()
    conn.execute(
        """
        INSERT INTO sync_contact_state(hektor_contact_id, listing_variant, date_last_traitement, date_maj, last_seen_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(hektor_contact_id) DO UPDATE SET
            listing_variant = excluded.listing_variant,
            date_last_traitement = excluded.date_last_traitement,
            date_maj = excluded.date_maj,
            last_seen_at = excluded.last_seen_at
        """,
        (contact_id, listing_variant, date_last_traitement, date_maj, now_iso),
    )


def iter_contact_entries(detail_payload: Dict[str, Any]) -> Iterable[tuple[str, Dict[str, Any]]]:
    data = detail_payload.get("data") or {}
    if not isinstance(data, dict):
        return []

    def iterator() -> Iterable[tuple[str, Dict[str, Any]]]:
        for source_key, role_contact in (
            ("proprietaires", "proprietaire"),
            ("mandants", "mandant"),
            ("acquereurs", "acquereur"),
        ):
            source = data.get(source_key) or []
            if not isinstance(source, list):
                continue
            for item in source:
                if isinstance(item, dict):
                    yield role_contact, item
        notaires = data.get("notaires") or {}
        if isinstance(notaires, dict):
            for source_key, role_contact in (("entree", "notaire_entree"), ("sortie", "notaire_sortie")):
                item = notaires.get(source_key)
                if isinstance(item, dict):
                    yield role_contact, item

    return iterator()


def replace_annonce_contact_links(conn, annonce_id: str, detail_payload: Dict[str, Any]) -> None:
    now_iso = now_utc_iso()
    conn.execute("DELETE FROM sync_annonce_contact_link WHERE hektor_annonce_id = ?", (annonce_id,))
    rows = []
    for role_contact, contact in iter_contact_entries(detail_payload):
        contact_id = str(contact.get("id") or "").strip()
        if not contact_id:
            continue
        rows.append(
            (
                annonce_id,
                contact_id,
                role_contact,
                str(contact.get("datemaj") or "").strip() or None,
                now_iso,
            )
        )
    if rows:
        conn.executemany(
            """
            INSERT INTO sync_annonce_contact_link(
                hektor_annonce_id, hektor_contact_id, role_contact, contact_date_maj, last_seen_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )


def find_annonce_ids_by_contact_ids(conn, contact_ids: set[str]) -> set[str]:
    normalized_ids = sorted({str(value).strip() for value in contact_ids if str(value).strip()})
    if not normalized_ids:
        return set()

    annonce_ids: set[str] = set()
    for batch in chunked_values(normalized_ids):
        placeholders = ", ".join("?" for _ in batch)
        rows = conn.execute(
            f"""
            SELECT DISTINCT hektor_annonce_id
            FROM sync_annonce_contact_link
            WHERE hektor_contact_id IN ({placeholders})
            """,
            tuple(batch),
        ).fetchall()
        annonce_ids.update(str(row["hektor_annonce_id"]) for row in rows if row["hektor_annonce_id"] is not None)
    return annonce_ids


def prune_raw_listing_pages(conn, *, endpoint_name: str, max_page: int) -> None:
    conn.execute(
        """
        DELETE FROM raw_api_response
        WHERE endpoint_name = ?
          AND page_key > ?
        """,
        (endpoint_name, max_page),
    )
    conn.commit()


def delete_rows_by_ids(conn, *, table: str, column: str, ids: Iterable[str]) -> None:
    normalized_ids = sorted({str(value).strip() for value in ids if str(value).strip()})
    if not normalized_ids:
        return
    for batch in chunked_values(normalized_ids):
        placeholders = ", ".join("?" for _ in batch)
        conn.execute(f"DELETE FROM {table} WHERE {column} IN ({placeholders})", tuple(batch))
    conn.commit()


def delete_rows_by_endpoint(conn, endpoint_names: Iterable[str]) -> None:
    endpoint_name_list = [name for name in endpoint_names if name]
    if not endpoint_name_list:
        return
    placeholders = ", ".join("?" for _ in endpoint_name_list)
    conn.execute(f"DELETE FROM raw_api_response WHERE endpoint_name IN ({placeholders})", tuple(endpoint_name_list))
    conn.commit()


def delete_raw_object_rows(conn, *, endpoint_names: Iterable[str], object_ids: Iterable[str]) -> None:
    endpoint_name_list = [name for name in endpoint_names if name]
    object_id_list = sorted({str(value).strip() for value in object_ids if str(value).strip()})
    if not endpoint_name_list or not object_id_list:
        return
    endpoint_placeholders = ", ".join("?" for _ in endpoint_name_list)
    object_chunk_size = max(1, SQLITE_MAX_VARIABLES - len(endpoint_name_list))
    for batch in chunked_values(object_id_list, chunk_size=object_chunk_size):
        object_placeholders = ", ".join("?" for _ in batch)
        conn.execute(
            f"""
            DELETE FROM raw_api_response
            WHERE endpoint_name IN ({endpoint_placeholders})
              AND object_id_key IN ({object_placeholders})
            """,
            tuple(endpoint_name_list + batch),
        )
    conn.commit()


def reconcile_active_annonce_scope(conn, active_annonce_ids: set[str]) -> set[str]:
    rows = conn.execute("SELECT hektor_annonce_id FROM sync_annonce_state").fetchall()
    known_ids = {str(row["hektor_annonce_id"]).strip() for row in rows if str(row["hektor_annonce_id"] or "").strip()}
    stale_ids = sorted(known_ids - active_annonce_ids)
    if not stale_ids:
        delete_rows_by_endpoint(
            conn,
            (
                "list_annonces_archived",
                "list_annonces_archived_update",
            ),
        )
        return set()

    delete_rows_by_ids(conn, table="sync_annonce_state", column="hektor_annonce_id", ids=stale_ids)
    delete_rows_by_ids(conn, table="sync_annonce_contact_link", column="hektor_annonce_id", ids=stale_ids)
    delete_raw_object_rows(
        conn,
        endpoint_names=("annonce_detail", "mandats_by_annonce"),
        object_ids=stale_ids,
    )
    delete_rows_by_endpoint(
        conn,
        (
            "list_annonces_archived",
            "list_annonces_archived_update",
        ),
    )
    return set(stale_ids)


def collect_ids_from_rows(rows, object_id_field: str = "id", limit: Optional[int] = None) -> list[str]:
    object_ids: list[str] = []
    seen_ids: set[str] = set()
    for row in rows:
        payload = json.loads(row["payload_json"])
        data = payload.get("data") or []
        for item in data:
            if not isinstance(item, dict):
                continue
            object_id = str(item.get(object_id_field) or "").strip()
            if object_id and object_id not in seen_ids:
                seen_ids.add(object_id)
                object_ids.append(object_id)
            if limit is not None and len(object_ids) >= limit:
                break
        if limit is not None and len(object_ids) >= limit:
            break
    return object_ids


def extract_missing_nego_ids_from_annonces(conn) -> list[str]:
    known_nego_ids: set[str] = set()
    for row in fetch_latest_raw_payloads(conn, "list_negos"):
        payload = json.loads(row["payload_json"])
        data = payload.get("data") or []
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            nego_id = str(item.get("id") or "").strip()
            if nego_id:
                known_nego_ids.add(nego_id)

    for row in fetch_latest_raw_payloads(conn, "nego_by_id"):
        object_id = str(row["object_id"] or "").strip()
        if object_id:
            known_nego_ids.add(object_id)

    missing_ids: set[str] = set()
    for row in fetch_latest_raw_payloads(conn, "list_annonces_active"):
        payload = json.loads(row["payload_json"])
        data = payload.get("data") or []
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            nego_id = str(item.get("NEGOCIATEUR") or "").strip()
            if not nego_id or nego_id == "0":
                continue
            if nego_id not in known_nego_ids:
                missing_ids.add(nego_id)

    return sorted(missing_ids, key=lambda value: (len(value), value))


def sync_missing_negos_by_id(conn, run_id: int, client: HektorClient, settings: Settings) -> int:
    missing_ids = extract_missing_nego_ids_from_annonces(conn)
    if not missing_ids:
        return 0

    synced = 0
    total = len(missing_ids)
    for index, nego_id in enumerate(missing_ids, start=1):
        update_sync_run_progress(
            conn,
            run_id,
            current_step="sync_missing_nego_by_id",
            current_resource="negociateurs",
            current_endpoint="/Api/Negociateur/getNegoById",
            current_object_id=nego_id,
            progress_done=index,
            progress_total=total,
            progress_unit="negos",
        )
        payload = client.get_json(
            "/Api/Negociateur/getNegoById",
            params={"id": nego_id},
        )
        upsert_raw_response(
            conn,
            run_id=run_id,
            endpoint_name="nego_by_id",
            object_type="negociateur",
            object_id=nego_id,
            page=None,
            params={"id": nego_id},
            payload=payload,
            http_status=200,
        )
        sleep_brief()
        synced += 1
    return synced


def collect_ids_from_raw_many(conn, endpoint_names: Iterable[str], object_id_field: str = "id", limit: Optional[int] = None) -> list[str]:
    endpoint_name_list = list(endpoint_names)
    if not endpoint_name_list:
        return []
    rows = conn.execute(
        """
        SELECT payload_json
        FROM raw_api_response
        WHERE endpoint_name IN ({})
        ORDER BY id DESC
        """.format(", ".join("?" for _ in endpoint_name_list)),
        tuple(endpoint_name_list),
    ).fetchall()
    return collect_ids_from_rows(rows, object_id_field=object_id_field, limit=limit)


def collect_existing_object_ids(conn, endpoint_name: str) -> set[str]:
    rows = conn.execute(
        """
        SELECT object_id
        FROM raw_api_response
        WHERE endpoint_name = ? AND object_id IS NOT NULL AND object_id != ''
        """,
        (endpoint_name,),
    ).fetchall()
    return {str(row["object_id"]).strip() for row in rows if str(row["object_id"]).strip()}


def sync_generic_listing(conn, run_id: int, client: HektorClient, settings: Settings, config: Dict[str, Any], max_pages: Optional[int]) -> None:
    pages = [None] if not config["paged"] else iter_pages(max_pages)
    pages_done = 0
    expected_pages = 0 if max_pages is None else max_pages
    update_sync_run_progress(
        conn,
        run_id,
        current_step="listing",
        current_resource=config["resource_name"],
        current_endpoint=config["effective_endpoint_name"],
        current_object_id=None,
        current_page=0 if config["paged"] else None,
        progress_done=0,
        progress_total=expected_pages,
        progress_unit="pages",
    )
    for page in pages:
        params = dict(config.get("extra_params", {}))
        params["version"] = settings.api_version
        if page is not None:
            params["page"] = page
        payload = client.get_json(config["path"], params=params)
        upsert_raw_response(
            conn,
            run_id=run_id,
            endpoint_name=config["effective_endpoint_name"],
            object_type=config["object_type"],
            object_id=None,
            page=page,
            params=params,
            payload=payload,
            http_status=200,
        )
        pages_done += 1
        expected_pages = expected_total_from_payload(payload, expected_pages)
        update_sync_run_progress(
            conn,
            run_id,
            current_step="listing",
            current_resource=config["resource_name"],
            current_endpoint=config["effective_endpoint_name"],
            current_object_id=None,
            current_page=page,
            progress_done=pages_done,
            progress_total=expected_pages,
            progress_unit="pages",
        )
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or []
        next_page = metadata.get("nextPage") if isinstance(metadata, dict) else None
        if config["paged"] and (not data or next_page in (None, "", 0, "0")):
            break
        sleep_brief()


def sync_generic_details(
    conn,
    run_id: int,
    client: HektorClient,
    settings: Settings,
    listing_endpoint_names: Iterable[str],
    resource_name: str,
    limit: Optional[int],
    missing_only: bool,
) -> None:
    detail_cfg = DETAIL_CONFIG[resource_name]
    object_ids = collect_ids_from_raw_many(conn, listing_endpoint_names, limit=limit)
    if missing_only:
        existing_ids = collect_existing_object_ids(conn, detail_cfg["endpoint_name"])
        object_ids = [object_id for object_id in object_ids if object_id not in existing_ids]
        if limit is not None:
            object_ids = object_ids[:limit]

    total_objects = len(object_ids)
    update_sync_run_progress(
        conn,
        run_id,
        current_step="detail",
        current_resource=resource_name,
        current_endpoint=detail_cfg["endpoint_name"],
        current_object_id=None,
        current_page=None,
        progress_done=0,
        progress_total=total_objects,
        progress_unit="objects",
    )
    for index, object_id in enumerate(object_ids, start=1):
        params = {detail_cfg["id_param"]: object_id, "version": settings.api_version}
        try:
            payload = client.get_json(detail_cfg["path"], params=params)
        except Exception as exc:
            log_sync_error(
                conn,
                run_id=run_id,
                stage="sync_raw",
                endpoint_name=detail_cfg["endpoint_name"],
                object_type=detail_cfg["object_type"],
                object_id=object_id,
                page=None,
                error_message=str(exc),
            )
            continue
        upsert_raw_response(
            conn,
            run_id=run_id,
            endpoint_name=detail_cfg["endpoint_name"],
            object_type=detail_cfg["object_type"],
            object_id=object_id,
            page=None,
            params=params,
            payload=payload,
            http_status=200,
        )
        update_sync_run_progress(
            conn,
            run_id,
            current_step="detail",
            current_resource=resource_name,
            current_endpoint=detail_cfg["endpoint_name"],
            current_object_id=object_id,
            current_page=None,
            progress_done=index,
            progress_total=total_objects,
            progress_unit="objects",
        )
        sleep_brief()


def sync_annonce_listing_variant(
    conn,
    run_id: int,
    client: HektorClient,
    settings: Settings,
    *,
    variant: Dict[str, Any],
    state_map: Dict[str, str],
    max_pages: Optional[int],
    use_update_endpoint: bool,
    bootstrap: bool,
) -> tuple[set[str], set[str], Optional[str], int]:
    endpoint_name = variant["update_endpoint_name"] if use_update_endpoint else variant["base_endpoint_name"]
    changed_ids: set[str] = set()
    seen_ids: set[str] = set()
    cursor = None if bootstrap else get_meta_value(conn, f"annonce_cursor_{variant['scope']}")
    max_seen_date = cursor
    sort_field = "id" if bootstrap else "datemaj"
    sort_way = "ASC" if bootstrap else "DESC"
    page = 1
    pages_seen = 0
    pages_total: Optional[int] = None

    while True:
        params = {
            "archive": variant["archive"],
            "sort": sort_field,
            "way": sort_way,
            "page": page,
            "version": settings.api_version,
        }
        payload = client.get_json("/Api/Annonce/ListAnnonces/", params=params)
        upsert_raw_response(
            conn,
            run_id=run_id,
            endpoint_name=endpoint_name,
            object_type=variant["object_type"],
            object_id=None,
            page=page,
            params=params,
            payload=payload,
            http_status=200,
        )
        data = payload.get("data") or []
        metadata = payload.get("metadata") or {}
        pages_seen += 1
        pages_total = expected_total_from_payload(payload, pages_total or 0) or pages_total
        update_sync_run_progress(
            conn,
            run_id,
            current_step="listing",
            current_resource="annonces",
            current_endpoint=endpoint_name,
            current_object_id=None,
            current_page=page,
            progress_done=pages_seen,
            progress_total=pages_total or max(pages_seen, 1),
            progress_unit="pages",
        )
        if not isinstance(data, list) or not data:
            break

        page_is_stale = cursor is not None
        for item in data:
            if not isinstance(item, dict):
                continue
            annonce_id = str(item.get("id") or "").strip()
            if not annonce_id:
                continue
            seen_ids.add(annonce_id)
            date_maj = str(item.get("datemaj") or "").strip()
            previous_date_maj = state_map.get(annonce_id, "")
            if previous_date_maj != date_maj:
                changed_ids.add(annonce_id)
            state_map[annonce_id] = date_maj
            upsert_annonce_state(conn, annonce_id=annonce_id, listing_variant=variant["scope"], date_maj=date_maj or None)
            if date_maj and (max_seen_date is None or date_maj > max_seen_date):
                max_seen_date = date_maj
            if not cursor or not date_maj or date_maj > cursor:
                page_is_stale = False

        next_page = metadata.get("nextPage") if isinstance(metadata, dict) else None
        conn.commit()
        if max_pages is not None and pages_seen >= max_pages:
            break
        if not bootstrap and cursor and page_is_stale:
            break
        if next_page in (None, "", 0, "0"):
            break
        page = int(next_page)
        sleep_brief()

    return changed_ids, seen_ids, max_seen_date, max(page, pages_seen)


def sync_contact_listing_variant(
    conn,
    run_id: int,
    client: HektorClient,
    settings: Settings,
    *,
    variant: Dict[str, Any],
    state_map: Dict[str, str],
    max_pages: Optional[int],
    use_update_endpoint: bool,
    bootstrap: bool,
) -> tuple[set[str], Optional[str]]:
    endpoint_name = variant["update_endpoint_name"] if use_update_endpoint else variant["base_endpoint_name"]
    changed_ids: set[str] = set()
    cursor = None if bootstrap else get_meta_value(conn, f"contact_cursor_{variant['scope']}")
    max_seen_date = cursor
    sort_field = "id" if bootstrap else "dateLastTraitement"
    sort_way = "ASC" if bootstrap else "DESC"
    page = 1
    pages_seen = 0
    pages_total: Optional[int] = None

    while True:
        params = {
            "archive": variant["archive"],
            "sort": sort_field,
            "way": sort_way,
            "page": page,
            "version": settings.api_version,
        }
        payload = client.get_json("/Api/Contact/ListContacts/", params=params)
        upsert_raw_response(
            conn,
            run_id=run_id,
            endpoint_name=endpoint_name,
            object_type=variant["object_type"],
            object_id=None,
            page=page,
            params=params,
            payload=payload,
            http_status=200,
        )
        data = payload.get("data") or []
        metadata = payload.get("metadata") or {}
        pages_seen += 1
        pages_total = expected_total_from_payload(payload, pages_total or 0) or pages_total
        update_sync_run_progress(
            conn,
            run_id,
            current_step="listing",
            current_resource="contacts",
            current_endpoint=endpoint_name,
            current_object_id=None,
            current_page=page,
            progress_done=pages_seen,
            progress_total=pages_total or max(pages_seen, 1),
            progress_unit="pages",
        )
        if not isinstance(data, list) or not data:
            break

        page_is_stale = cursor is not None
        for item in data:
            if not isinstance(item, dict):
                continue
            contact_id = str(item.get("id") or "").strip()
            if not contact_id:
                continue
            # On this instance, the API accepts sorting by dateLastTraitement but does not
            # actually return that field in the listing payload; datemaj is the observable
            # timestamp present in data and is therefore used as the persisted update marker.
            date_last_traitement = str(item.get("dateLastTraitement") or "").strip() or None
            date_maj = str(item.get("datemaj") or "").strip()
            previous_date = state_map.get(contact_id, "")
            if previous_date != date_maj:
                changed_ids.add(contact_id)
            state_map[contact_id] = date_maj
            upsert_contact_state(
                conn,
                contact_id=contact_id,
                listing_variant=variant["scope"],
                date_last_traitement=date_last_traitement,
                date_maj=date_maj or None,
            )
            if date_maj and (max_seen_date is None or date_maj > max_seen_date):
                max_seen_date = date_maj
            if not cursor or not date_maj or date_maj > cursor:
                page_is_stale = False

        next_page = metadata.get("nextPage") if isinstance(metadata, dict) else None
        conn.commit()
        if max_pages is not None and pages_seen >= max_pages:
            break
        if not bootstrap and cursor and page_is_stale:
            break
        if next_page in (None, "", 0, "0"):
            break
        page = int(next_page)
        sleep_brief()

    return changed_ids, max_seen_date


def sync_annonce_details(conn, run_id: int, client: HektorClient, settings: Settings, detail_ids: list[str]) -> None:
    detail_cfg = DETAIL_CONFIG["annonces"]
    total_objects = len(detail_ids)
    update_sync_run_progress(
        conn,
        run_id,
        current_step="detail",
        current_resource="annonces",
        current_endpoint=detail_cfg["endpoint_name"],
        current_object_id=None,
        current_page=None,
        progress_done=0,
        progress_total=total_objects,
        progress_unit="objects",
    )
    for index, annonce_id in enumerate(detail_ids, start=1):
        params = {detail_cfg["id_param"]: annonce_id, "version": settings.api_version}
        try:
            payload = client.get_json(detail_cfg["path"], params=params)
        except Exception as exc:
            log_sync_error(
                conn,
                run_id=run_id,
                stage="sync_raw",
                endpoint_name=detail_cfg["endpoint_name"],
                object_type=detail_cfg["object_type"],
                object_id=annonce_id,
                page=None,
                error_message=str(exc),
            )
            continue
        upsert_raw_response(
            conn,
            run_id=run_id,
            endpoint_name=detail_cfg["endpoint_name"],
            object_type=detail_cfg["object_type"],
            object_id=annonce_id,
            page=None,
            params=params,
            payload=payload,
            http_status=200,
        )
        replace_annonce_contact_links(conn, annonce_id, payload)
        mark_annonce_detail_synced(conn, annonce_id)
        update_sync_run_progress(
            conn,
            run_id,
            current_step="detail",
            current_resource="annonces",
            current_endpoint=detail_cfg["endpoint_name"],
            current_object_id=annonce_id,
            current_page=None,
            progress_done=index,
            progress_total=total_objects,
            progress_unit="objects",
        )
        conn.commit()
        sleep_brief()


def sync_mandats_by_annonce(conn, run_id: int, client: HektorClient, settings: Settings, annonce_ids: list[str]) -> None:
    total_objects = len(annonce_ids)
    update_sync_run_progress(
        conn,
        run_id,
        current_step="relation",
        current_resource="annonces_to_mandats",
        current_endpoint=MANDAT_RELATION_CONFIG["endpoint_name"],
        current_object_id=None,
        current_page=None,
        progress_done=0,
        progress_total=total_objects,
        progress_unit="objects",
    )
    for index, annonce_id in enumerate(annonce_ids, start=1):
        params = {MANDAT_RELATION_CONFIG["target_param"]: annonce_id, "version": settings.api_version}
        try:
            payload = client.get_json(MANDAT_RELATION_CONFIG["path"], params=params)
        except Exception as exc:
            log_sync_error(
                conn,
                run_id=run_id,
                stage="sync_raw",
                endpoint_name=MANDAT_RELATION_CONFIG["endpoint_name"],
                object_type=MANDAT_RELATION_CONFIG["object_type"],
                object_id=annonce_id,
                page=None,
                error_message=str(exc),
            )
            continue
        upsert_raw_response(
            conn,
            run_id=run_id,
            endpoint_name=MANDAT_RELATION_CONFIG["endpoint_name"],
            object_type=MANDAT_RELATION_CONFIG["object_type"],
            object_id=annonce_id,
            page=None,
            params=params,
            payload=payload,
            http_status=200,
        )
        update_sync_run_progress(
            conn,
            run_id,
            current_step="relation",
            current_resource="annonces_to_mandats",
            current_endpoint=MANDAT_RELATION_CONFIG["endpoint_name"],
            current_object_id=annonce_id,
            current_page=None,
            progress_done=index,
            progress_total=total_objects,
            progress_unit="objects",
        )
        sleep_brief()


def configure_generic_resources(args: argparse.Namespace, bootstrap: bool) -> Dict[str, Dict[str, Any]]:
    configs = copy.deepcopy(GENERIC_RESOURCE_CONFIG)
    configs["offres"]["extra_params"]["withOfferStatus"] = bool_string(args.with_offer_status)
    configs["compromis"]["extra_params"]["withCompromisStatus"] = bool_string(args.with_compromis_status)
    configs["mandats"]["extra_params"]["beginDate"] = args.mandat_date_start or "2020-01-01"
    configs["mandats"]["extra_params"]["endDate"] = args.mandat_date_end or "2030-12-31"
    configs["ventes"]["extra_params"]["dateStart"] = args.vente_date_start or "2020-01-01"
    configs["ventes"]["extra_params"]["dateEnd"] = args.vente_date_end or "2030-12-31"

    for resource_name, config in configs.items():
        config["resource_name"] = resource_name
        config["effective_endpoint_name"] = config["endpoint_name"]

    if bootstrap or args.mode != "update":
        return configs

    for resource_name in ("mandats", "offres", "compromis", "ventes"):
        configs[resource_name]["effective_endpoint_name"] = configs[resource_name]["update_endpoint_name"]

    configs["mandats"]["extra_params"]["sort"] = "id"
    configs["mandats"]["extra_params"]["way"] = "DESC"
    configs["compromis"]["extra_params"]["sort"] = "dateStart"
    configs["compromis"]["extra_params"]["way"] = "DESC"
    configs["offres"]["extra_params"]["sort"] = "date"
    configs["offres"]["extra_params"]["way"] = "DESC"

    if args.vente_date_start is None:
        configs["ventes"]["extra_params"]["dateStart"] = iso_date_months_ago(args.vente_lookback_months)
    if args.vente_date_end is None:
        configs["ventes"]["extra_params"]["dateEnd"] = date.today().isoformat()

    return configs


def resolve_generic_max_pages(args: argparse.Namespace, resource_name: str, bootstrap: bool) -> Optional[int]:
    if bootstrap or args.mode != "update":
        return None if args.max_pages == 0 else args.max_pages
    if resource_name == "mandats":
        return max(1, ceil(args.mandat_recent_limit / 20))
    if resource_name == "compromis":
        return max(1, ceil(args.compromis_recent_limit / 20))
    if resource_name == "offres":
        return max(1, ceil(args.offre_recent_limit / 20))
    if resource_name == "ventes":
        return None if args.max_pages == 0 else args.max_pages
    return None if args.update_max_pages == 0 else args.update_max_pages


def resolve_generic_detail_limit(args: argparse.Namespace, resource_name: str, bootstrap: bool) -> Optional[int]:
    if bootstrap or args.mode != "update":
        return None if args.detail_limit == 0 else args.detail_limit
    if resource_name == "mandats":
        return args.mandat_recent_limit
    if resource_name == "compromis":
        return args.compromis_recent_limit
    if resource_name == "offres":
        return args.offre_recent_limit
    return None if args.update_detail_limit == 0 else args.update_detail_limit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync raw Hektor payloads into SQLite.")
    parser.add_argument(
        "--resources",
        nargs="+",
        choices=["agences", "negos", "annonces", "contacts", "mandats", "offres", "compromis", "ventes", "broadcasts"],
        default=["agences", "negos", "annonces", "contacts", "mandats", "offres", "compromis", "ventes", "broadcasts"],
    )
    parser.add_argument("--mode", choices=["full", "update"], default="update", help="Le premier run bascule automatiquement en bootstrap complet.")
    parser.add_argument("--purge", action="store_true", help="Supprimer la base SQLite avant la synchronisation.")
    parser.add_argument("--max-pages", type=int, default=0, help="Limite globale de pages. 0 = toutes les pages.")
    parser.add_argument("--detail-limit", type=int, default=0, help="Limite globale de details ById. 0 = tous les IDs.")
    parser.add_argument("--missing-only", action="store_true", help="Pour les details generiques, ignorer les IDs deja presents.")
    parser.add_argument(
        "--force-annonce-detail-full",
        action="store_true",
        help="Pour les annonces, rejouer AnnonceById sur tout le stock actif, meme sans changement de date_maj.",
    )
    parser.add_argument("--with-offer-status", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--with-compromis-status", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--mandat-date-start", default=None)
    parser.add_argument("--mandat-date-end", default=None)
    parser.add_argument("--vente-date-start", default=None)
    parser.add_argument("--vente-date-end", default=None)
    parser.add_argument("--mandat-recent-limit", type=int, default=500)
    parser.add_argument("--compromis-recent-limit", type=int, default=1000)
    parser.add_argument("--offre-recent-limit", type=int, default=1000)
    parser.add_argument("--vente-lookback-months", type=int, default=12)
    parser.add_argument("--update-max-pages", type=int, default=5)
    parser.add_argument("--update-detail-limit", type=int, default=200)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = Settings.from_env()
    if args.purge:
        purge_database_files(str(settings.db_path))

    conn = connect_db(settings.db_path)
    init_db(conn)
    cleanup_stale_sync_runs(conn)
    run_id = create_sync_run(conn, "sync_raw")
    client = HektorClient(settings)

    try:
        update_sync_run_progress(conn, run_id, current_step="authenticate", progress_done=0, progress_total=1, progress_unit="step")
        client.authenticate()

        bootstrap = not has_any_annonce_state(conn)
        annonce_state_map = load_annonce_state_map(conn)
        contact_state_map = load_contact_state_map(conn)
        use_update_endpoints = args.mode == "update" and not bootstrap

        detail_ids: list[str] = []

        if "annonces" in args.resources:
            changed_annonce_ids: set[str] = set()
            active_annonce_ids: set[str] = set()
            for variant in ANNONCE_VARIANTS:
                variant_changed_ids, variant_seen_ids, max_seen_date, last_page = sync_annonce_listing_variant(
                    conn,
                    run_id,
                    client,
                    settings,
                    variant=variant,
                    state_map=annonce_state_map,
                    max_pages=None if args.max_pages == 0 else args.max_pages,
                    use_update_endpoint=False,
                    bootstrap=True,
                )
                changed_annonce_ids.update(variant_changed_ids)
                active_annonce_ids.update(variant_seen_ids)
                prune_raw_listing_pages(conn, endpoint_name=variant["base_endpoint_name"], max_page=last_page)
                if max_seen_date:
                    set_meta_value(conn, f"annonce_cursor_{variant['scope']}", max_seen_date)
            reconcile_active_annonce_scope(conn, active_annonce_ids)
            if args.force_annonce_detail_full:
                detail_ids = sorted(active_annonce_ids)
            else:
                detail_ids = sorted(set(changed_annonce_ids) | set(load_annonce_ids_missing_detail_sync(conn)))

        if "contacts" in args.resources:
            changed_contact_ids: set[str] = set()
            for variant in CONTACT_VARIANTS:
                variant_changed_ids, max_seen_date = sync_contact_listing_variant(
                    conn,
                    run_id,
                    client,
                    settings,
                    variant=variant,
                    state_map=contact_state_map,
                    max_pages=None if args.max_pages == 0 else args.max_pages,
                    use_update_endpoint=use_update_endpoints,
                    bootstrap=bootstrap or args.mode == "full",
                )
                changed_contact_ids.update(variant_changed_ids)
                if max_seen_date:
                    set_meta_value(conn, f"contact_cursor_{variant['scope']}", max_seen_date)
            if "annonces" in args.resources:
                detail_ids = list(dict.fromkeys(detail_ids + sorted(find_annonce_ids_by_contact_ids(conn, changed_contact_ids))))

        if "annonces" in args.resources and detail_ids:
            sync_annonce_details(conn, run_id, client, settings, detail_ids)
            sync_mandats_by_annonce(conn, run_id, client, settings, detail_ids)

        generic_configs = configure_generic_resources(args, bootstrap=bootstrap)
        for resource_name in ("agences", "negos", "mandats", "offres", "compromis", "ventes", "broadcasts"):
            if resource_name not in args.resources:
                continue
            config = generic_configs[resource_name]
            sync_generic_listing(
                conn,
                run_id,
                client,
                settings,
                config,
                resolve_generic_max_pages(args, resource_name, bootstrap),
            )
            if resource_name == "negos":
                sync_missing_negos_by_id(conn, run_id, client, settings)
            if resource_name == "mandats":
                mandat_detail_sources = [config["effective_endpoint_name"]]
                if "annonces" in args.resources:
                    mandat_detail_sources.append(MANDAT_RELATION_CONFIG["endpoint_name"])
                sync_generic_details(
                    conn,
                    run_id,
                    client,
                    settings,
                    mandat_detail_sources,
                    resource_name,
                    resolve_generic_detail_limit(args, resource_name, bootstrap),
                    missing_only=args.missing_only,
                )

        update_sync_run_progress(conn, run_id, current_step="finalizing", progress_done=1, progress_total=1, progress_unit="step")
        finish_sync_run(conn, run_id, "success", notes="bootstrap" if bootstrap else None)
        print(f"Raw sync completed into {settings.db_path}")
        return 0
    except Exception as exc:
        finish_sync_run(conn, run_id, "failed", notes=str(exc))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
