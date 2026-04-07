from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import requests


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "actif.sqlite"
RUN_STALE_AFTER_SECONDS = 300


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def load_env_files() -> None:
    candidates = [
        BASE_DIR / ".env",
        BASE_DIR.parent / ".env",
    ]
    for path in candidates:
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


@dataclass
class Settings:
    base_url: str
    client_id: str
    client_secret: str
    api_version: str
    db_path: Path
    timeout: int = 30

    @classmethod
    def from_env(cls, db_path: Optional[str] = None) -> "Settings":
        load_env_files()
        base_url = os.getenv("HEKTOR_BASE_URL", "").strip().rstrip("/")
        client_id = os.getenv("HEKTOR_CLIENT_ID", "").strip()
        client_secret = os.getenv("HEKTOR_CLIENT_SECRET", "").strip()
        api_version = (os.getenv("HEKTOR_VERSION", "") or os.getenv("VERSION", "v2") or "v2").strip()
        missing = [name for name, value in (
            ("HEKTOR_BASE_URL", base_url),
            ("HEKTOR_CLIENT_ID", client_id),
            ("HEKTOR_CLIENT_SECRET", client_secret),
        ) if not value]
        if missing:
            raise RuntimeError(f"Variables d'environnement manquantes: {', '.join(missing)}")
        resolved_db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        return cls(
            base_url=base_url,
            client_id=client_id,
            client_secret=client_secret,
            api_version=api_version,
            db_path=resolved_db_path,
        )


class HektorClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.jwt: Optional[str] = None

    def authenticate(self) -> None:
        auth_resp = self.session.post(
            f"{self.settings.base_url}/Api/OAuth/Authenticate/",
            params={
                "client_id": self.settings.client_id,
                "client_secret": self.settings.client_secret,
                "grant_type": "client_credentials",
            },
            timeout=self.settings.timeout,
        )
        auth_resp.raise_for_status()
        access_token = auth_resp.json()["access_token"]

        sso_resp = self.session.post(
            f"{self.settings.base_url}/Api/OAuth/Sso/",
            params={
                "token": access_token,
                "scope": "sso",
                "client_id": self.settings.client_id,
            },
            timeout=self.settings.timeout,
        )
        sso_resp.raise_for_status()
        self.jwt = sso_resp.json()["jwt"]

    def get_json(self, path: str, *, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.jwt:
            self.authenticate()
        response = self.session.get(
            f"{self.settings.base_url}{path}",
            headers={"jwt": self.jwt or ""},
            params=params,
            timeout=self.settings.timeout,
        )
        refresh = response.headers.get("x-refresh-token")
        if refresh:
            self.jwt = refresh
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            body_preview = (response.text or "").strip().replace("\n", " ")[:200]
            raise RuntimeError(
                f"Réponse non JSON pour {path} avec params={params}: {body_preview or '<empty>'}"
            ) from exc
        if isinstance(payload, dict) and payload.get("refresh"):
            self.jwt = str(payload["refresh"]).strip()
        return payload


def connect_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS actif_run (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL,
            current_step TEXT,
            progress_done INTEGER NOT NULL DEFAULT 0,
            progress_total INTEGER NOT NULL DEFAULT 0,
            current_annonce_id TEXT,
            heartbeat_at TEXT,
            listing_count INTEGER NOT NULL DEFAULT 0,
            new_count INTEGER NOT NULL DEFAULT 0,
            updated_count INTEGER NOT NULL DEFAULT 0,
            unchanged_count INTEGER NOT NULL DEFAULT 0,
            removed_count INTEGER NOT NULL DEFAULT 0,
            detail_count INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS actif_listing_item (
            run_id INTEGER NOT NULL,
            annonce_id TEXT NOT NULL,
            date_maj TEXT,
            raw_json TEXT NOT NULL,
            PRIMARY KEY (run_id, annonce_id),
            FOREIGN KEY (run_id) REFERENCES actif_run(id)
        );

        CREATE TABLE IF NOT EXISTS actif_error (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            stage TEXT NOT NULL,
            object_id TEXT,
            error_message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES actif_run(id)
        );

        CREATE TABLE IF NOT EXISTS actif_meta (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS actif_annonce (
            annonce_id TEXT PRIMARY KEY,
            listing_date_maj TEXT,
            active_current INTEGER NOT NULL DEFAULT 0,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            last_active_run_id INTEGER,
            last_detail_sync_at TEXT,
            removed_at TEXT,
            statut_id TEXT,
            statut_name TEXT,
            no_dossier TEXT,
            no_mandat TEXT,
            agence_id TEXT,
            negociateur_id TEXT,
            archive TEXT,
            diffusable TEXT,
            partage TEXT,
            valide TEXT,
            prix REAL,
            surface TEXT,
            titre TEXT,
            ville TEXT,
            code_postal TEXT,
            listing_json TEXT,
            annonce_detail_json TEXT,
            mandat_json TEXT,
            contacts_json TEXT
        );

        CREATE TABLE IF NOT EXISTS actif_contact (
            contact_id TEXT PRIMARY KEY,
            contact_list_date_last_traitement TEXT,
            contact_date_maj TEXT,
            contact_list_date_maj TEXT,
            contact_list_json TEXT,
            contact_json TEXT,
            recherches_json TEXT,
            last_list_sync_at TEXT,
            last_sync_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS actif_broadcast (
            broadcast_id TEXT PRIMARY KEY,
            nom TEXT,
            count_value INTEGER,
            raw_json TEXT,
            last_sync_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS actif_broadcast_listing (
            broadcast_id TEXT NOT NULL,
            annonce_id TEXT NOT NULL,
            commercial_id TEXT,
            commercial_type TEXT,
            commercial_nom TEXT,
            commercial_prenom TEXT,
            export_status TEXT,
            raw_json TEXT,
            last_sync_at TEXT NOT NULL,
            PRIMARY KEY (broadcast_id, annonce_id, commercial_id)
        );

        CREATE INDEX IF NOT EXISTS idx_actif_annonce_active_current ON actif_annonce(active_current);
        CREATE INDEX IF NOT EXISTS idx_actif_annonce_last_active_run_id ON actif_annonce(last_active_run_id);
        CREATE INDEX IF NOT EXISTS idx_actif_broadcast_listing_annonce ON actif_broadcast_listing(annonce_id);
        """
    )
    existing_run_columns = {row["name"] for row in conn.execute("PRAGMA table_info(actif_run)")}
    if "error_count" not in existing_run_columns:
        conn.execute("ALTER TABLE actif_run ADD COLUMN error_count INTEGER NOT NULL DEFAULT 0")
    for column_name, ddl in (
        ("current_step", "ALTER TABLE actif_run ADD COLUMN current_step TEXT"),
        ("progress_done", "ALTER TABLE actif_run ADD COLUMN progress_done INTEGER NOT NULL DEFAULT 0"),
        ("progress_total", "ALTER TABLE actif_run ADD COLUMN progress_total INTEGER NOT NULL DEFAULT 0"),
        ("current_annonce_id", "ALTER TABLE actif_run ADD COLUMN current_annonce_id TEXT"),
        ("heartbeat_at", "ALTER TABLE actif_run ADD COLUMN heartbeat_at TEXT"),
    ):
        if column_name not in existing_run_columns:
            conn.execute(ddl)
    existing_contact_columns = {row["name"] for row in conn.execute("PRAGMA table_info(actif_contact)")}
    for column_name, ddl in (
        ("contact_list_date_last_traitement", "ALTER TABLE actif_contact ADD COLUMN contact_list_date_last_traitement TEXT"),
        ("contact_list_date_maj", "ALTER TABLE actif_contact ADD COLUMN contact_list_date_maj TEXT"),
        ("contact_list_json", "ALTER TABLE actif_contact ADD COLUMN contact_list_json TEXT"),
        ("last_list_sync_at", "ALTER TABLE actif_contact ADD COLUMN last_list_sync_at TEXT"),
    ):
        if column_name not in existing_contact_columns:
            conn.execute(ddl)
    conn.commit()


def cleanup_stale_runs(conn: sqlite3.Connection, *, stale_after_seconds: int = RUN_STALE_AFTER_SECONDS) -> int:
    now_dt = datetime.now(timezone.utc)
    rows = conn.execute(
        """
        SELECT id, started_at, heartbeat_at
        FROM actif_run
        WHERE status = 'running' AND finished_at IS NULL
        """
    ).fetchall()
    abandoned = 0
    for row in rows:
        reference = parse_iso_datetime(row["heartbeat_at"]) or parse_iso_datetime(row["started_at"])
        if reference is None:
            continue
        age_seconds = (now_dt - reference).total_seconds()
        if age_seconds < stale_after_seconds:
            continue
        conn.execute(
            """
            UPDATE actif_run
            SET status = 'abandoned',
                finished_at = ?,
                notes = COALESCE(notes || ' | ', '') || ?
            WHERE id = ?
            """,
            (
                now_utc_iso(),
                f"Run marque abandoned apres {stale_after_seconds} secondes sans heartbeat",
                row["id"],
            ),
        )
        abandoned += 1
    conn.commit()
    return abandoned


def create_run(conn: sqlite3.Connection) -> int:
    cleanup_stale_runs(conn)
    cursor = conn.execute(
        """
        INSERT INTO actif_run(started_at, status, heartbeat_at)
        VALUES (?, ?, ?)
        """,
        (now_utc_iso(), "running", now_utc_iso()),
    )
    conn.commit()
    return int(cursor.lastrowid)


def finish_run(
    conn: sqlite3.Connection,
    run_id: int,
    *,
    status: str,
    listing_count: int,
    new_count: int,
    updated_count: int,
    unchanged_count: int,
    removed_count: int,
    detail_count: int,
    error_count: int,
    notes: Optional[str] = None,
) -> None:
    conn.execute(
        """
        UPDATE actif_run
        SET finished_at = ?,
            status = ?,
            heartbeat_at = ?,
            listing_count = ?,
            new_count = ?,
            updated_count = ?,
            unchanged_count = ?,
            removed_count = ?,
            detail_count = ?,
            error_count = ?,
            notes = ?
        WHERE id = ?
        """,
        (
            now_utc_iso(),
            status,
            now_utc_iso(),
            listing_count,
            new_count,
            updated_count,
            unchanged_count,
            removed_count,
            detail_count,
            error_count,
            notes,
            run_id,
        ),
    )
    conn.commit()


def log_error(conn: sqlite3.Connection, *, run_id: int, stage: str, object_id: Optional[str], error_message: str) -> None:
    conn.execute(
        """
        INSERT INTO actif_error(run_id, stage, object_id, error_message, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (run_id, stage, object_id, error_message, now_utc_iso()),
    )
    conn.commit()


def update_run_progress(
    conn: sqlite3.Connection,
    *,
    run_id: int,
    current_step: str,
    progress_done: int,
    progress_total: int,
    current_annonce_id: Optional[str] = None,
) -> None:
    conn.execute(
        """
        UPDATE actif_run
        SET current_step = ?,
            progress_done = ?,
            progress_total = ?,
            current_annonce_id = ?,
            heartbeat_at = ?
        WHERE id = ?
        """,
        (current_step, progress_done, progress_total, current_annonce_id, now_utc_iso(), run_id),
    )
    conn.commit()


def fetch_active_listing(
    client: HektorClient,
    settings: Settings,
    *,
    max_pages: Optional[int] = None,
    on_page=None,
) -> list[Dict[str, Any]]:
    items: list[Dict[str, Any]] = []
    page = 1
    pages_seen = 0
    pages_total: Optional[int] = None
    while True:
        if on_page is not None:
            on_page(page, pages_seen, len(items), pages_total)
        params = {
            "archive": 0,
            "sort": "datemaj",
            "way": "DESC",
            "page": page,
            "version": settings.api_version,
        }
        payload = client.get_json("/Api/Annonce/ListAnnonces/", params=params)
        data = payload.get("data") or []
        metadata = payload.get("metadata") or {}
        if isinstance(metadata, dict):
            try:
                meta_total = int(metadata.get("total") or 0)
                per_page = int(metadata.get("perPage") or 0)
                if meta_total > 0 and per_page > 0:
                    computed_total = (meta_total + per_page - 1) // per_page
                    pages_total = min(computed_total, max_pages) if max_pages is not None else computed_total
            except (TypeError, ValueError):
                pages_total = pages_total
        if not isinstance(data, list):
            break
        items.extend(item for item in data if isinstance(item, dict))
        pages_seen += 1
        if on_page is not None:
            on_page(page, pages_seen, len(items), pages_total)
        if max_pages is not None and pages_seen >= max_pages:
            break
        next_page = metadata.get("nextPage") if isinstance(metadata, dict) else None
        if not data or next_page in (None, "", 0, "0"):
            break
        page = int(next_page)
        time.sleep(0.1)
    return items


def load_previous_active_index(conn: sqlite3.Connection) -> Dict[str, str]:
    rows = conn.execute(
        """
        SELECT annonce_id, listing_date_maj
        FROM actif_annonce
        WHERE active_current = 1
        """
    ).fetchall()
    return {str(row["annonce_id"]): str(row["listing_date_maj"] or "") for row in rows}


def has_any_annonce_stock(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT 1 FROM actif_annonce LIMIT 1").fetchone()
    return row is not None


def save_listing_snapshot(conn: sqlite3.Connection, run_id: int, listing_items: Iterable[Dict[str, Any]]) -> None:
    rows = []
    for item in listing_items:
        annonce_id = str(item.get("id") or "").strip()
        if not annonce_id:
            continue
        rows.append((run_id, annonce_id, item.get("datemaj"), json.dumps(item, ensure_ascii=False)))
    conn.executemany(
        """
        INSERT OR REPLACE INTO actif_listing_item(run_id, annonce_id, date_maj, raw_json)
        VALUES (?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()


def get_meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute(
        "SELECT value FROM actif_meta WHERE key = ?",
        (key,),
    ).fetchone()
    return None if row is None else str(row["value"] or "")


def set_meta_value(conn: sqlite3.Connection, key: str, value: Optional[str]) -> None:
    conn.execute(
        """
        INSERT INTO actif_meta(key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
        """,
        (key, value, now_utc_iso()),
    )
    conn.commit()


def upsert_listing_presence(
    conn: sqlite3.Connection,
    *,
    run_id: int,
    now_iso: str,
    listing_map: Dict[str, Dict[str, Any]],
    unchanged_ids: Iterable[str],
) -> None:
    for annonce_id in unchanged_ids:
        listing_item = listing_map[annonce_id]
        listing_json = json.dumps(listing_item, ensure_ascii=False)
        date_maj = listing_item.get("datemaj")
        conn.execute(
            """
            INSERT INTO actif_annonce(
                annonce_id, listing_date_maj, active_current, first_seen_at, last_seen_at,
                last_active_run_id, listing_json
            ) VALUES (?, ?, 1, ?, ?, ?, ?)
            ON CONFLICT(annonce_id) DO UPDATE SET
                listing_date_maj = excluded.listing_date_maj,
                active_current = 1,
                last_seen_at = excluded.last_seen_at,
                last_active_run_id = excluded.last_active_run_id,
                removed_at = NULL,
                listing_json = excluded.listing_json
            """,
            (annonce_id, date_maj, now_iso, now_iso, run_id, listing_json),
        )
    conn.commit()


def fetch_annonce_detail(client: HektorClient, settings: Settings, annonce_id: str) -> Dict[str, Any]:
    return client.get_json(
        "/Api/Annonce/AnnonceById/",
        params={"id": annonce_id, "version": settings.api_version},
    )


def extract_annonce_block(detail_payload: Dict[str, Any]) -> Dict[str, Any]:
    data = detail_payload.get("data")
    if isinstance(data, dict):
        annonce = data.get("annonce")
        if isinstance(annonce, dict):
            return annonce
        return data
    return {}


def extract_status(detail_payload: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    data = detail_payload.get("data")
    if not isinstance(data, dict):
        return None, None
    statut = data.get("statut")
    if isinstance(statut, dict):
        statut_id = str(statut.get("id") or "").strip() or None
        statut_name = str(statut.get("name") or "").strip() or None
        if statut_id is not None or statut_name is not None:
            return statut_id, statut_name
    for id_key, name_key in (
        ("statut_id", "statut_name"),
        ("statutId", "statutName"),
    ):
        if data.get(id_key) is not None or data.get(name_key) is not None:
            return (
                str(data.get(id_key) or "") or None,
                str(data.get(name_key) or "") or None,
            )
    annonce = data.get("annonce")
    if isinstance(annonce, dict):
        for id_key, name_key in (
            ("statut_id", "statut_name"),
            ("statutId", "statutName"),
        ):
            if annonce.get(id_key) is not None or annonce.get(name_key) is not None:
                return (
                    str(annonce.get(id_key) or "") or None,
                    str(annonce.get(name_key) or "") or None,
                )
    return None, None


def extract_contacts(detail_payload: Dict[str, Any]) -> Dict[str, Any]:
    data = detail_payload.get("data")
    if not isinstance(data, dict):
        return {
            "proprietaires": [],
            "mandants": [],
            "acquereurs": [],
            "notaires": {"entree": None, "sortie": None},
        }
    contacts = {
        "proprietaires": data.get("proprietaires") or [],
        "mandants": data.get("mandants") or [],
        "acquereurs": data.get("acquereurs") or [],
        "notaires": data.get("notaires") or {"entree": None, "sortie": None},
    }
    return contacts


def iter_contact_entries(contacts_payload: Dict[str, Any]) -> Iterable[tuple[str, Dict[str, Any]]]:
    role_map = {
        "proprietaires": "proprietaire",
        "mandants": "mandant",
        "acquereurs": "acquereur",
    }
    for source_key, role_contact in role_map.items():
        source = contacts_payload.get(source_key) or []
        if not isinstance(source, list):
            continue
        for item in source:
            if isinstance(item, dict):
                yield role_contact, item
    notaires = contacts_payload.get("notaires") or {}
    if isinstance(notaires, dict):
        for source_key, role_contact in (("entree", "notaire_entree"), ("sortie", "notaire_sortie")):
            item = notaires.get(source_key)
            if isinstance(item, dict):
                yield role_contact, item


def parse_json_object(text: Optional[str]) -> Dict[str, Any]:
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def get_existing_contact_signatures(conn: sqlite3.Connection, annonce_id: str) -> Dict[tuple[str, str], str]:
    row = conn.execute(
        """
        SELECT contacts_json
        FROM actif_annonce
        WHERE annonce_id = ?
        """,
        (annonce_id,),
    ).fetchone()
    contacts_payload = parse_json_object(row["contacts_json"]) if row and row["contacts_json"] else {}
    signatures: Dict[tuple[str, str], str] = {}
    for role_contact, contact in iter_contact_entries(contacts_payload):
        contact_id = str(contact.get("id") or "").strip()
        if not contact_id:
            continue
        signatures[(role_contact, contact_id)] = str(contact.get("datemaj") or "")
    return signatures


def extract_contact_signatures(contacts_payload: Dict[str, Any]) -> Dict[tuple[str, str], str]:
    signatures: Dict[tuple[str, str], str] = {}
    for role_contact, contact in iter_contact_entries(contacts_payload):
        contact_id = str(contact.get("id") or "").strip()
        if not contact_id:
            continue
        signatures[(role_contact, contact_id)] = str(contact.get("datemaj") or "")
    return signatures


def compute_contacts_to_refresh(
    previous_signatures: Dict[tuple[str, str], str],
    current_signatures: Dict[tuple[str, str], str],
) -> set[str]:
    changed_contact_ids: set[str] = set()
    for key, current_date_maj in current_signatures.items():
        previous_date_maj = previous_signatures.get(key)
        if previous_date_maj != current_date_maj:
            changed_contact_ids.add(key[1])
    return changed_contact_ids


def fetch_contact_detail(client: HektorClient, settings: Settings, contact_id: str) -> Dict[str, Any]:
    return client.get_json(
        "/Api/Contact/ContactById",
        params={"id": contact_id, "version": settings.api_version},
    )


def fetch_contact_listing(
    client: HektorClient,
    settings: Settings,
    *,
    max_pages: Optional[int] = None,
    on_page=None,
) -> list[Dict[str, Any]]:
    items: list[Dict[str, Any]] = []
    page = 1
    pages_seen = 0
    pages_total: Optional[int] = None
    while True:
        if on_page is not None:
            on_page(page, pages_seen, len(items), pages_total)
        payload = client.get_json(
            "/Api/Contact/ListContacts/",
            params={
                "archive": 0,
                "sort": "dateLastTraitement",
                "way": "DESC",
                "page": page,
                "version": settings.api_version,
            },
        )
        data = payload.get("data") or []
        metadata = payload.get("metadata") or {}
        if isinstance(metadata, dict):
            try:
                meta_total = int(metadata.get("total") or 0)
                per_page = int(metadata.get("perPage") or 0)
                if meta_total > 0 and per_page > 0:
                    computed_total = (meta_total + per_page - 1) // per_page
                    pages_total = min(computed_total, max_pages) if max_pages is not None else computed_total
            except (TypeError, ValueError):
                pass
        if not isinstance(data, list):
            break
        items.extend(item for item in data if isinstance(item, dict))
        pages_seen += 1
        if on_page is not None:
            on_page(page, pages_seen, len(items), pages_total)
        if max_pages is not None and pages_seen >= max_pages:
            break
        next_page = metadata.get("nextPage") if isinstance(metadata, dict) else None
        if not data or next_page in (None, "", 0, "0"):
            break
        page = int(next_page)
        time.sleep(0.05)
    return items


def upsert_contact_detail(conn: sqlite3.Connection, *, now_iso: str, contact_id: str, payload: Dict[str, Any]) -> None:
    data = payload.get("data") or {}
    if not isinstance(data, dict):
        data = {}
    contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}
    recherches = data.get("recherches")
    conn.execute(
        """
        INSERT INTO actif_contact(contact_id, contact_date_maj, contact_json, recherches_json, last_sync_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(contact_id) DO UPDATE SET
            contact_date_maj = excluded.contact_date_maj,
            contact_json = excluded.contact_json,
            recherches_json = excluded.recherches_json,
            last_sync_at = excluded.last_sync_at
        """,
        (
            contact_id,
            contact.get("datemaj") if isinstance(contact, dict) else None,
            json.dumps(contact, ensure_ascii=False),
            json.dumps(recherches, ensure_ascii=False),
            now_iso,
        ),
    )


def upsert_contact_listing_item(conn: sqlite3.Connection, *, now_iso: str, item: Dict[str, Any]) -> Optional[str]:
    contact_id = str(item.get("id") or "").strip()
    if not contact_id:
        return None
    conn.execute(
        """
        INSERT INTO actif_contact(
            contact_id, contact_list_date_last_traitement, contact_list_date_maj,
            contact_list_json, last_list_sync_at, last_sync_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(contact_id) DO UPDATE SET
            contact_list_date_last_traitement = excluded.contact_list_date_last_traitement,
            contact_list_date_maj = excluded.contact_list_date_maj,
            contact_list_json = excluded.contact_list_json,
            last_list_sync_at = excluded.last_list_sync_at
        """,
        (
            contact_id,
            item.get("dateLastTraitement"),
            item.get("datemaj"),
            json.dumps(item, ensure_ascii=False),
            now_iso,
            now_iso,
        ),
    )
    return contact_id


def find_annonce_ids_by_contact_ids(conn: sqlite3.Connection, contact_ids: set[str]) -> set[str]:
    if not contact_ids:
        return set()
    rows = conn.execute(
        """
        SELECT annonce_id, contacts_json
        FROM actif_annonce
        WHERE contacts_json IS NOT NULL
        ORDER BY annonce_id
        """
    ).fetchall()
    annonce_ids: set[str] = set()
    for row in rows:
        contacts_payload = parse_json_object(row["contacts_json"]) if row["contacts_json"] else {}
        for _, contact in iter_contact_entries(contacts_payload):
            contact_id = str(contact.get("id") or "").strip()
            if contact_id and contact_id in contact_ids:
                annonce_ids.add(str(row["annonce_id"]))
                break
    return annonce_ids


def fetch_broadcast_pages(
    client: HektorClient,
    settings: Settings,
    *,
    max_pages: Optional[int] = None,
    on_page=None,
) -> list[Dict[str, Any]]:
    items: list[Dict[str, Any]] = []
    page = 1
    pages_seen = 0
    pages_total: Optional[int] = None
    while True:
        if on_page is not None:
            on_page(page, pages_seen, len(items), pages_total)
        payload = client.get_json(
            "/Api/Passerelle/DetailedBroadcastList/",
            params={"page": page, "version": settings.api_version},
        )
        data = payload.get("data")
        metadata = payload.get("metadata") or {}
        if isinstance(metadata, dict):
            try:
                meta_total = int(metadata.get("total") or 0)
                per_page = int(metadata.get("perPage") or 0)
                if meta_total > 0 and per_page > 0:
                    computed_total = (meta_total + per_page - 1) // per_page
                    pages_total = min(computed_total, max_pages) if max_pages is not None else computed_total
            except (TypeError, ValueError):
                pass
        page_items = data if isinstance(data, list) else ([data] if isinstance(data, dict) else [])
        items.extend(item for item in page_items if isinstance(item, dict))
        pages_seen += 1
        if on_page is not None:
            on_page(page, pages_seen, len(items), pages_total)
        if max_pages is not None and pages_seen >= max_pages:
            break
        next_page = metadata.get("nextPage") if isinstance(metadata, dict) else None
        if not page_items or next_page in (None, "", 0, "0"):
            break
        page = int(next_page)
        time.sleep(0.05)
    return items


def sync_broadcasts(
    conn: sqlite3.Connection,
    *,
    run_id: int,
    now_iso: str,
    client: HektorClient,
    settings: Settings,
    max_pages: Optional[int],
) -> Dict[str, int]:
    def on_broadcast_page(page: int, pages_seen: int, items_seen: int, pages_total: Optional[int]) -> None:
        progress_total = pages_total or (max_pages if max_pages is not None else max(pages_seen, 1))
        update_run_progress(
            conn,
            run_id=run_id,
            current_step=f"broadcast_page_{page}",
            progress_done=pages_seen,
            progress_total=progress_total,
            current_annonce_id=str(items_seen),
        )

    broadcast_items = fetch_broadcast_pages(client, settings, max_pages=max_pages, on_page=on_broadcast_page)
    conn.execute("DELETE FROM actif_broadcast_listing")
    conn.execute("DELETE FROM actif_broadcast")

    broadcast_rows = []
    listing_rows = []
    for item in broadcast_items:
        broadcast_id = str(item.get("id") or "").strip()
        if not broadcast_id:
            continue
        listings = item.get("listings") or []
        broadcast_rows.append(
            (
                broadcast_id,
                item.get("nom"),
                item.get("count"),
                json.dumps(item, ensure_ascii=False),
                now_iso,
            )
        )
        if not isinstance(listings, list):
            continue
        for listing in listings:
            if not isinstance(listing, dict):
                continue
            annonce_id = str(listing.get("annonce_id") or "").strip()
            if not annonce_id:
                continue
            commercial = listing.get("commercial") or {}
            if not isinstance(commercial, dict):
                commercial = {}
            listing_rows.append(
                (
                    broadcast_id,
                    annonce_id,
                    str(commercial.get("id") or "") or None,
                    commercial.get("type"),
                    commercial.get("nom"),
                    commercial.get("prenom"),
                    listing.get("export_status"),
                    json.dumps(listing, ensure_ascii=False),
                    now_iso,
                )
            )

    conn.executemany(
        """
        INSERT INTO actif_broadcast(broadcast_id, nom, count_value, raw_json, last_sync_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        broadcast_rows,
    )
    conn.executemany(
        """
        INSERT INTO actif_broadcast_listing(
            broadcast_id, annonce_id, commercial_id, commercial_type, commercial_nom,
            commercial_prenom, export_status, raw_json, last_sync_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        listing_rows,
    )
    conn.commit()
    return {
        "broadcast_count": len(broadcast_rows),
        "broadcast_listing_count": len(listing_rows),
    }


def upsert_detail_record(
    conn: sqlite3.Connection,
    *,
    run_id: int,
    now_iso: str,
    annonce_id: str,
    listing_item: Optional[Dict[str, Any]],
    detail_payload: Dict[str, Any],
    active_current: bool,
) -> None:
    annonce = extract_annonce_block(detail_payload)
    mandat = detail_payload.get("data", {}).get("mandat") if isinstance(detail_payload.get("data"), dict) else None
    contacts = extract_contacts(detail_payload)
    statut_id, statut_name = extract_status(detail_payload)

    ville = None
    code_postal = None
    localite = annonce.get("localite")
    if isinstance(localite, dict):
        publique = localite.get("publique")
        if isinstance(publique, dict):
            ville = publique.get("ville")
            code_postal = publique.get("code")

    listing_json = json.dumps(listing_item, ensure_ascii=False) if listing_item is not None else None
    listing_date_maj = listing_item.get("datemaj") if listing_item is not None else None
    conn.execute(
        """
        INSERT INTO actif_annonce(
            annonce_id, listing_date_maj, active_current, first_seen_at, last_seen_at,
            last_active_run_id, last_detail_sync_at, removed_at, statut_id, statut_name,
            no_dossier, no_mandat, agence_id, negociateur_id, archive, diffusable, partage,
            valide, prix, surface, titre, ville, code_postal, listing_json,
            annonce_detail_json, mandat_json, contacts_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(annonce_id) DO UPDATE SET
            listing_date_maj = excluded.listing_date_maj,
            active_current = excluded.active_current,
            last_seen_at = excluded.last_seen_at,
            last_active_run_id = excluded.last_active_run_id,
            last_detail_sync_at = excluded.last_detail_sync_at,
            removed_at = excluded.removed_at,
            statut_id = excluded.statut_id,
            statut_name = excluded.statut_name,
            no_dossier = excluded.no_dossier,
            no_mandat = excluded.no_mandat,
            agence_id = excluded.agence_id,
            negociateur_id = excluded.negociateur_id,
            archive = excluded.archive,
            diffusable = excluded.diffusable,
            partage = excluded.partage,
            valide = excluded.valide,
            prix = excluded.prix,
            surface = excluded.surface,
            titre = excluded.titre,
            ville = excluded.ville,
            code_postal = excluded.code_postal,
            listing_json = COALESCE(excluded.listing_json, actif_annonce.listing_json),
            annonce_detail_json = excluded.annonce_detail_json,
            mandat_json = excluded.mandat_json,
            contacts_json = excluded.contacts_json
        """,
        (
            annonce_id,
            listing_date_maj,
            1 if active_current else 0,
            now_iso,
            now_iso,
            run_id if active_current else None,
            now_iso,
            None if active_current else now_iso,
            statut_id,
            statut_name,
            annonce.get("NO_DOSSIER"),
            annonce.get("NO_MANDAT"),
            annonce.get("agence"),
            annonce.get("NEGOCIATEUR"),
            annonce.get("archive"),
            annonce.get("diffusable"),
            annonce.get("partage"),
            annonce.get("valide"),
            annonce.get("prix"),
            annonce.get("surface"),
            annonce.get("titre"),
            ville,
            code_postal,
            listing_json,
            json.dumps(detail_payload, ensure_ascii=False),
            json.dumps(mandat, ensure_ascii=False),
            json.dumps(contacts, ensure_ascii=False),
        ),
    )


def mark_removed_without_detail(conn: sqlite3.Connection, removed_ids: Iterable[str], now_iso: str) -> None:
    conn.executemany(
        """
        UPDATE actif_annonce
        SET active_current = 0,
            removed_at = ?,
            last_seen_at = ?
        WHERE annonce_id = ?
        """,
        [(now_iso, now_iso, annonce_id) for annonce_id in removed_ids],
    )
    conn.commit()


def run_sync(settings: Settings, *, max_pages: Optional[int] = None, broadcasts_only: bool = False) -> Dict[str, int]:
    conn = connect_db(settings.db_path)
    init_db(conn)
    run_id = create_run(conn)
    now_iso = now_utc_iso()
    client = HektorClient(settings)

    if broadcasts_only:
        summary = sync_broadcasts(
            conn,
            run_id=run_id,
            now_iso=now_iso,
            client=client,
            settings=settings,
            max_pages=max_pages,
        )
        finish_run(
            conn,
            run_id,
            status="success",
            listing_count=0,
            new_count=0,
            updated_count=0,
            unchanged_count=0,
            removed_count=0,
            detail_count=0,
            error_count=0,
            notes=f"broadcasts only: {summary['broadcast_count']} passerelle(s), {summary['broadcast_listing_count']} diffusion(s)",
        )
        return summary

    update_run_progress(conn, run_id=run_id, current_step="listing", progress_done=0, progress_total=0)

    def on_listing_page(page: int, pages_seen: int, items_seen: int, pages_total: Optional[int]) -> None:
        progress_total = pages_total or (max_pages if max_pages is not None else max(pages_seen, 1))
        update_run_progress(
            conn,
            run_id=run_id,
            current_step=f"listing_page_{page}",
            progress_done=pages_seen,
            progress_total=progress_total,
            current_annonce_id=str(items_seen),
        )

    listing_items = fetch_active_listing(client, settings, max_pages=max_pages, on_page=on_listing_page)
    listing_map: Dict[str, Dict[str, Any]] = {}
    for item in listing_items:
        annonce_id = str(item.get("id") or "").strip()
        if annonce_id:
            listing_map[annonce_id] = item
    update_run_progress(
        conn,
        run_id=run_id,
        current_step="listing_done",
        progress_done=len(listing_map),
        progress_total=len(listing_map),
    )

    save_listing_snapshot(conn, run_id, listing_map.values())
    is_bootstrap_run = not has_any_annonce_stock(conn)
    previous_active = load_previous_active_index(conn)
    current_ids = set(listing_map)
    previous_ids = set(previous_active)

    new_ids = sorted(current_ids - previous_ids)
    removed_ids = sorted(previous_ids - current_ids)
    unchanged_ids = sorted(
        annonce_id
        for annonce_id in (current_ids & previous_ids)
        if str(listing_map[annonce_id].get("datemaj") or "") == previous_active.get(annonce_id, "")
    )
    updated_ids = sorted((current_ids & previous_ids) - set(unchanged_ids))
    error_count = 0
    update_run_progress(
        conn,
        run_id=run_id,
        current_step="delta_ready",
        progress_done=len(new_ids) + len(updated_ids) + len(removed_ids),
        progress_total=len(current_ids),
    )

    upsert_listing_presence(
        conn,
        run_id=run_id,
        now_iso=now_iso,
        listing_map=listing_map,
        unchanged_ids=unchanged_ids,
    )

    # Bootstrap explicite: au premier run, on recharge tout le parc actif
    # car on ne dispose ni d'historique annonce fiable ni de curseur contact.
    base_detail_ids = sorted(current_ids) if is_bootstrap_run else list(dict.fromkeys(new_ids + updated_ids + removed_ids))

    def on_contact_listing_page(page: int, pages_seen: int, items_seen: int, pages_total: Optional[int]) -> None:
        progress_total = pages_total or (max_pages if max_pages is not None else max(pages_seen, 1))
        update_run_progress(
            conn,
            run_id=run_id,
            current_step=f"contact_listing_page_{page}",
            progress_done=pages_seen,
            progress_total=progress_total,
            current_annonce_id=str(items_seen),
        )

    last_contact_run_at = None if is_bootstrap_run else get_meta_value(conn, "last_contact_run_at")
    contact_listing_items = fetch_contact_listing(client, settings, max_pages=max_pages, on_page=on_contact_listing_page)
    updated_contact_ids: set[str] = set()
    for item in contact_listing_items:
        contact_id = upsert_contact_listing_item(conn, now_iso=now_iso, item=item)
        if not contact_id:
            continue
        date_last_traitement = str(item.get("dateLastTraitement") or "").strip()
        if last_contact_run_at and date_last_traitement and date_last_traitement <= last_contact_run_at:
            continue
        updated_contact_ids.add(contact_id)

    contact_triggered_annonce_ids = find_annonce_ids_by_contact_ids(conn, updated_contact_ids)
    detail_ids = list(dict.fromkeys(base_detail_ids + sorted(contact_triggered_annonce_ids)))
    detail_count = 0
    total_detail_ids = len(detail_ids)
    update_run_progress(
        conn,
        run_id=run_id,
        current_step="detail",
        progress_done=0,
        progress_total=total_detail_ids,
    )
    for index, annonce_id in enumerate(detail_ids, start=1):
        update_run_progress(
            conn,
            run_id=run_id,
            current_step="detail",
            progress_done=index - 1,
            progress_total=total_detail_ids,
            current_annonce_id=annonce_id,
        )
        listing_item = listing_map.get(annonce_id)
        try:
            detail_payload = fetch_annonce_detail(client, settings, annonce_id)
        except Exception as exc:
            log_error(
                conn,
                run_id=run_id,
                stage="annonce_detail",
                object_id=annonce_id,
                error_message=str(exc),
            )
            error_count += 1
            if annonce_id in removed_ids:
                mark_removed_without_detail(conn, [annonce_id], now_iso)
            continue
        upsert_detail_record(
            conn,
            run_id=run_id,
            now_iso=now_iso,
            annonce_id=annonce_id,
            listing_item=listing_item,
            detail_payload=detail_payload,
            active_current=annonce_id in current_ids,
        )
        detail_count += 1
        update_run_progress(
            conn,
            run_id=run_id,
            current_step="detail",
            progress_done=index,
            progress_total=total_detail_ids,
            current_annonce_id=annonce_id,
        )
        time.sleep(0.1)

    if removed_ids:
        removed_without_detail = [annonce_id for annonce_id in removed_ids if annonce_id not in detail_ids]
        if removed_without_detail:
            mark_removed_without_detail(conn, removed_without_detail, now_iso)

    set_meta_value(conn, "last_contact_run_at", now_iso)

    conn.commit()
    summary = {
        "is_bootstrap_run": 1 if is_bootstrap_run else 0,
        "listing_count": len(current_ids),
        "new_count": len(new_ids),
        "updated_count": len(updated_ids),
        "unchanged_count": len(unchanged_ids),
        "removed_count": len(removed_ids),
        "detail_count": detail_count,
        "error_count": error_count,
        "contact_listing_count": len(contact_listing_items),
        "contact_updated_count": len(updated_contact_ids),
        "contact_triggered_annonce_count": len(contact_triggered_annonce_ids),
    }

    broadcast_summary = sync_broadcasts(
        conn,
        run_id=run_id,
        now_iso=now_iso,
        client=client,
        settings=settings,
        max_pages=max_pages,
    )
    summary.update(broadcast_summary)

    update_run_progress(
        conn,
        run_id=run_id,
        current_step="finished",
        progress_done=summary["broadcast_listing_count"],
        progress_total=max(summary["broadcast_count"], 1),
        current_annonce_id=None,
    )
    run_notes = None
    if is_bootstrap_run:
        run_notes = "bootstrap complet annonces + listing contacts"
    if error_count > 0:
        run_notes = f"{error_count} erreur(s) sur les details annonces" + (
            f" | {run_notes}" if run_notes else ""
        )

    finish_run(
        conn,
        run_id,
        status="success" if error_count == 0 else "partial_success",
        listing_count=summary["listing_count"],
        new_count=summary["new_count"],
        updated_count=summary["updated_count"],
        unchanged_count=summary["unchanged_count"],
        removed_count=summary["removed_count"],
        detail_count=summary["detail_count"],
        error_count=summary["error_count"],
        notes=None if error_count == 0 else f"{error_count} erreur(s) sur les détails annonces",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync ACTIF autonome centre sur les annonces actives.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Chemin de la base SQLite ACTIF.")
    parser.add_argument("--max-pages", type=int, default=0, help="Limiter le nombre de pages de ListAnnonces. 0 = toutes les pages.")
    parser.add_argument("--broadcasts-only", action="store_true", help="Extraire uniquement la diffusion reelle par portail.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = Settings.from_env(db_path=args.db_path)
    max_pages = None if args.max_pages == 0 else args.max_pages
    summary = run_sync(settings, max_pages=max_pages, broadcasts_only=args.broadcasts_only)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
