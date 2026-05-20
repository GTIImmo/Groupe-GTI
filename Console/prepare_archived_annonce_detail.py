from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "hektor.sqlite"


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def build_detail_payload(conn: sqlite3.Connection, annonce_id: str) -> tuple[int, dict[str, Any]]:
    annonce = row_dict(conn.execute(
        """
        select *
        from hektor_annonce
        where hektor_annonce_id = ?
          and archive = '1'
        """,
        (annonce_id,),
    ).fetchone())
    if not annonce:
        raise RuntimeError(f"Annonce archivee introuvable localement: {annonce_id}")

    detail = row_dict(conn.execute(
        """
        select *
        from hektor_annonce_detail
        where hektor_annonce_id = ?
        """,
        (annonce_id,),
    ).fetchone())
    if not detail:
        raise RuntimeError(
            "Detail archive absent en local. Lance d'abord le run de recuperation des details archives."
        )

    try:
        index_row = row_dict(conn.execute(
            """
            select *
            from app_view_generale
            where hektor_annonce_id = ?
            """,
            (annonce_id,),
        ).fetchone()) or {}
    except sqlite3.OperationalError as exc:
        if "app_view_generale" not in str(exc):
            raise
        index_row = {}

    app_archive_id = int(index_row.get("app_dossier_id") or annonce_id)
    payload = {
        "hektor_annonce_id": annonce_id,
        "app_archive_id": app_archive_id,
        "listing": annonce,
        "index": index_row,
        "detail": {
            **detail,
            "localite_json": parse_json(detail.get("localite_json"), None),
            "mandats_json": parse_json(detail.get("mandats_json"), []),
            "proprietaires_json": parse_json(detail.get("proprietaires_json"), []),
            "honoraires_json": parse_json(detail.get("honoraires_json"), []),
            "notes_json": parse_json(detail.get("notes_json"), []),
            "zones_json": parse_json(detail.get("zones_json"), []),
            "particularites_json": parse_json(detail.get("particularites_json"), []),
            "pieces_json": parse_json(detail.get("pieces_json"), []),
            "images_json": parse_json(detail.get("images_json"), []),
            "textes_json": parse_json(detail.get("textes_json"), []),
            "terrain_json": parse_json(detail.get("terrain_json"), None),
            "copropriete_json": parse_json(detail.get("copropriete_json"), None),
        },
        "prepared_locally_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return app_archive_id, payload


def supabase_upsert(row: dict[str, Any]) -> None:
    supabase_url = (os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL") or "").rstrip("/")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not supabase_url or not service_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    response = requests.post(
        f"{supabase_url}/rest/v1/app_archive_annonce_detail_cache?on_conflict=hektor_annonce_id",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation",
        },
        json=[row],
        timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Supabase cache upsert failed: {response.status_code} {response.text[:800]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hektor-annonce-id", required=True)
    parser.add_argument("--requested-by")
    parser.add_argument("--ttl-hours", type=int, default=2)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    args = parser.parse_args()

    load_env(PROJECT_ROOT / ".env")
    load_env(PROJECT_ROOT / "apps" / "hektor-v1" / ".env")

    annonce_id = str(args.hektor_annonce_id).strip()
    if not annonce_id.isdigit():
        raise RuntimeError("hektor_annonce_id numerique requis")

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        app_archive_id, payload = build_detail_payload(conn, annonce_id)
    finally:
        conn.close()

    payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    prepared_at = datetime.now(timezone.utc)
    row = {
        "hektor_annonce_id": int(annonce_id),
        "app_archive_id": app_archive_id,
        "detail_payload_json": payload,
        "requested_by": args.requested_by or None,
        "prepared_at": prepared_at.isoformat(timespec="seconds"),
        "expires_at": (prepared_at + timedelta(hours=max(1, args.ttl_hours))).isoformat(timespec="seconds"),
        "source_hash": hashlib.sha256(payload_text.encode("utf-8")).hexdigest(),
        "source_updated_at": payload["listing"].get("date_maj") or None,
    }
    supabase_upsert(row)
    print(json.dumps({
        "status": "done",
        "hektor_annonce_id": annonce_id,
        "app_archive_id": app_archive_id,
        "payload_bytes": len(payload_text.encode("utf-8")),
        "expires_at": row["expires_at"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
