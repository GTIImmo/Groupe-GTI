#!/usr/bin/env python3
"""Recopie en local la table Supabase app_contact_override.

Les champs de la fiche contact que l'API Hektor ne retourne pas en lecture
(date de naissance, lieu, statut matrimonial, source, categorie, automatismes CRM,
RGPD, adresse, note) sont stockes dans Supabase (app_contact_override), ecrits par
l'app a l'enregistrement et par le worker apres confirmation Hektor.

Ce script telecharge ces overrides dans data/hektor.sqlite (table hektor_contact_overrides)
pour garder une copie locale durable cote PC. Idempotent : a lancer apres chaque session
d'edition contact, ou via la meme planification que les autres syncs.

Variables d'environnement requises (lues aussi depuis .env / apps/hektor-v1/.env) :
  SUPABASE_URL (ou VITE_SUPABASE_URL)
  SUPABASE_SERVICE_ROLE_KEY
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ENV_FILE = ROOT / ".env"
APP_ENV_FILE = ROOT / "apps" / "hektor-v1" / ".env"
DEFAULT_ENV_FILES = (DEFAULT_ENV_FILE, APP_ENV_FILE)
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"

FETCH_PAGE_SIZE = 1000
HTTP_TIMEOUT_SECONDS = 120
HTTP_MAX_RETRIES = 4

TABLE = "app_contact_override"
LOCAL_TABLE = "hektor_contact_overrides"
COLUMNS = (
    "hektor_contact_id",
    "address",
    "birth_date",
    "birth_place",
    "marital_status",
    "source_id",
    "category_id",
    "comments",
    "crm_mandate_summary",
    "crm_mandate_expiration",
    "crm_birthday",
    "rgpd_email_sent",
    "updated_by",
    "updated_at",
)
BOOL_COLUMNS = {"crm_mandate_summary", "crm_mandate_expiration", "crm_birthday", "rgpd_email_sent"}


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_env_files(paths: Iterable[Path]) -> None:
    for path in paths:
        load_env_file(path)


def ensure_local_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {LOCAL_TABLE} (
            hektor_contact_id      TEXT PRIMARY KEY,
            address                TEXT,
            birth_date             TEXT,
            birth_place            TEXT,
            marital_status         TEXT,
            source_id              TEXT,
            category_id            TEXT,
            comments               TEXT,
            crm_mandate_summary    INTEGER,
            crm_mandate_expiration INTEGER,
            crm_birthday           INTEGER,
            rgpd_email_sent        INTEGER,
            updated_by             TEXT,
            updated_at             TEXT
        )
        """
    )
    conn.commit()


def supabase_get(base_url: str, key: str, query: dict[str, str]) -> list[dict]:
    url = f"{base_url.rstrip('/')}/rest/v1/{TABLE}?{urllib.parse.urlencode(query)}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    request = urllib.request.Request(url, headers=headers, method="GET")
    last_error: Exception | None = None
    for attempt in range(1, HTTP_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else []
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase REST error {exc.code} on {TABLE}: {detail}") from exc
        except (TimeoutError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt >= HTTP_MAX_RETRIES:
                break
            time.sleep(1.5 * attempt)
    raise RuntimeError(f"Supabase REST network error on {TABLE}: {last_error}")


def to_local_value(column: str, value: object) -> object:
    if value is None:
        return None
    if column in BOOL_COLUMNS:
        return 1 if value else 0
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Recopie app_contact_override (Supabase) vers data/hektor.sqlite")
    parser.add_argument("--contact-id", help="Ne recopier qu'un seul contact (sinon: tous).")
    args = parser.parse_args()
    contact_id = str(args.contact_id).strip() if args.contact_id else None

    load_env_files(DEFAULT_ENV_FILES)
    base_url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not base_url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    conn = sqlite3.connect(str(HEKTOR_DB))
    try:
        ensure_local_table(conn)
        total = 0
        placeholders = ",".join("?" for _ in COLUMNS)
        upsert_sql = (
            f"INSERT INTO {LOCAL_TABLE} ({','.join(COLUMNS)}) VALUES ({placeholders}) "
            f"ON CONFLICT(hektor_contact_id) DO UPDATE SET "
            + ",".join(f"{c}=excluded.{c}" for c in COLUMNS if c != "hektor_contact_id")
        )

        def upsert_rows(rows: list[dict]) -> None:
            conn.executemany(
                upsert_sql,
                [tuple(to_local_value(c, row.get(c)) for c in COLUMNS) for row in rows],
            )
            conn.commit()

        if contact_id:
            rows = supabase_get(
                base_url,
                key,
                {
                    "select": ",".join(COLUMNS),
                    "hektor_contact_id": f"eq.{contact_id}",
                    "limit": "1",
                },
            )
            upsert_rows(rows)
            total = len(rows)
        else:
            offset = 0
            while True:
                rows = supabase_get(
                    base_url,
                    key,
                    {
                        "select": ",".join(COLUMNS),
                        "order": "hektor_contact_id.asc",
                        "offset": str(offset),
                        "limit": str(FETCH_PAGE_SIZE),
                    },
                )
                if not rows:
                    break
                upsert_rows(rows)
                total += len(rows)
                offset += len(rows)
                if len(rows) < FETCH_PAGE_SIZE:
                    break

        scope = f"contact {contact_id}" if contact_id else "tous"
        print(f"pull_contact_overrides ({scope}): {total} override(s) recopie(s) dans {LOCAL_TABLE}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
