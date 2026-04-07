from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import requests
from requests import Response


DEFAULT_DB_PATH = Path("data") / "hektor.sqlite"
RUN_STALE_AFTER_MINUTES = 30


def load_env(env_path: str | Path = ".env") -> None:
    path = Path(env_path)
    if not path.exists():
        return

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
    api_version: str = "v2"
    db_path: Path = DEFAULT_DB_PATH
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "Settings":
        load_env()
        base_url = os.getenv("HEKTOR_BASE_URL", "").strip().rstrip("/")
        client_id = os.getenv("HEKTOR_CLIENT_ID", "").strip()
        client_secret = os.getenv("HEKTOR_CLIENT_SECRET", "").strip()
        api_version = (os.getenv("HEKTOR_VERSION", "") or os.getenv("VERSION", "v2") or "v2").strip()
        db_path = Path(os.getenv("HEKTOR_DB_PATH", "") or DEFAULT_DB_PATH)

        missing = [name for name, value in (
            ("HEKTOR_BASE_URL", base_url),
            ("HEKTOR_CLIENT_ID", client_id),
            ("HEKTOR_CLIENT_SECRET", client_secret),
        ) if not value]
        if missing:
            raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

        return cls(
            base_url=base_url,
            client_id=client_id,
            client_secret=client_secret,
            api_version=api_version,
            db_path=db_path,
        )


class HektorClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.jwt: Optional[str] = None
        self.max_retries = 4

    def authenticate(self) -> str:
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
        return self.jwt

    def request(self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None) -> Response:
        if not self.jwt:
            self.authenticate()

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.request(
                    method,
                    f"{self.settings.base_url}{path}",
                    headers={"jwt": self.jwt or ""},
                    params=params or {},
                    timeout=self.settings.timeout,
                )

                refresh = response.headers.get("x-refresh-token")
                if refresh:
                    self.jwt = refresh

                if response.status_code == 403 and "expired token" in (response.text or "").lower():
                    self.authenticate()
                    continue

                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(0.35 * (2 ** (attempt - 1)))

        raise RuntimeError(f"{method} {path} failed after {self.max_retries} attempts: {last_error}")

    def get_json(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.request("GET", path, params=params)
                payload = response.json()
                if isinstance(payload, dict) and payload.get("refresh"):
                    self.jwt = str(payload["refresh"]).strip()
                return payload
            except (ValueError, RuntimeError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(0.35 * (2 ** (attempt - 1)))

        raise RuntimeError(f"GET {path} did not return valid JSON after {self.max_retries} attempts: {last_error}")


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def connect_db(db_path: str | Path) -> sqlite3.Connection:
    ensure_parent_dir(db_path)
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def now_utc_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def parse_utc_iso(value: str | None) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    with suppress(ValueError):
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    return None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sync_run (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL,
            notes TEXT,
            pid INTEGER,
            heartbeat_at TEXT,
            current_step TEXT,
            current_resource TEXT,
            current_endpoint TEXT,
            current_object_id TEXT,
            current_page INTEGER,
            progress_done INTEGER,
            progress_total INTEGER,
            progress_unit TEXT
        );

        CREATE TABLE IF NOT EXISTS sync_error (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            stage TEXT NOT NULL,
            endpoint_name TEXT,
            object_type TEXT,
            object_id TEXT,
            page INTEGER,
            error_message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES sync_run(id)
        );

        CREATE TABLE IF NOT EXISTS raw_api_response (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            endpoint_name TEXT NOT NULL,
            object_type TEXT NOT NULL,
            object_id TEXT,
            object_id_key TEXT NOT NULL DEFAULT '',
            page INTEGER,
            page_key INTEGER NOT NULL DEFAULT -1,
            params_json TEXT,
            payload_json TEXT NOT NULL,
            http_status INTEGER,
            fetched_at TEXT NOT NULL,
            UNIQUE(endpoint_name, object_type, object_id_key, page_key),
            FOREIGN KEY (run_id) REFERENCES sync_run(id)
        );

        CREATE TABLE IF NOT EXISTS sync_meta (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sync_annonce_state (
            hektor_annonce_id TEXT PRIMARY KEY,
            listing_variant TEXT NOT NULL,
            date_maj TEXT,
            last_seen_at TEXT NOT NULL,
            last_detail_sync_at TEXT
        );

        CREATE TABLE IF NOT EXISTS sync_contact_state (
            hektor_contact_id TEXT PRIMARY KEY,
            listing_variant TEXT NOT NULL,
            date_last_traitement TEXT,
            date_maj TEXT,
            last_seen_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sync_annonce_contact_link (
            hektor_annonce_id TEXT NOT NULL,
            hektor_contact_id TEXT NOT NULL,
            role_contact TEXT NOT NULL,
            contact_date_maj TEXT,
            last_seen_at TEXT NOT NULL,
            PRIMARY KEY (hektor_annonce_id, hektor_contact_id, role_contact)
        );

        CREATE TABLE IF NOT EXISTS hektor_agence (
            hektor_agence_id TEXT PRIMARY KEY,
            nom TEXT,
            type TEXT,
            mail TEXT,
            tel TEXT,
            responsable TEXT,
            parent_id TEXT,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hektor_negociateur (
            hektor_negociateur_id TEXT PRIMARY KEY,
            hektor_user_id TEXT,
            hektor_agence_id TEXT,
            nom TEXT,
            prenom TEXT,
            email TEXT,
            telephone TEXT,
            portable TEXT,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hektor_annonce (
            hektor_annonce_id TEXT PRIMARY KEY,
            no_dossier TEXT,
            no_mandat TEXT,
            hektor_agence_id TEXT,
            hektor_negociateur_id TEXT,
            date_maj TEXT,
            offre_type TEXT,
            idtype TEXT,
            prix REAL,
            surface TEXT,
            archive TEXT,
            diffusable TEXT,
            valide TEXT,
            partage TEXT,
            titre TEXT,
            ville TEXT,
            code_postal TEXT,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hektor_annonce_detail (
            hektor_annonce_id TEXT PRIMARY KEY,
            statut_id TEXT,
            statut_name TEXT,
            localite_json TEXT,
            mandats_json TEXT,
            proprietaires_json TEXT,
            honoraires_json TEXT,
            notes_json TEXT,
            zones_json TEXT,
            particularites_json TEXT,
            pieces_json TEXT,
            images_json TEXT,
            textes_json TEXT,
            terrain_json TEXT,
            copropriete_json TEXT,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hektor_mandat (
            hektor_mandat_id TEXT PRIMARY KEY,
            hektor_annonce_id TEXT,
            numero TEXT,
            type TEXT,
            date_enregistrement TEXT,
            date_debut TEXT,
            date_fin TEXT,
            date_cloture TEXT,
            montant TEXT,
            mandants_texte TEXT,
            note TEXT,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hektor_contact (
            hektor_contact_id TEXT PRIMARY KEY,
            hektor_agence_id TEXT,
            hektor_negociateur_id TEXT,
            civilite TEXT,
            nom TEXT,
            prenom TEXT,
            archive TEXT,
            date_enregistrement TEXT,
            date_maj TEXT,
            email TEXT,
            portable TEXT,
            fixe TEXT,
            ville TEXT,
            code_postal TEXT,
            typologie_json TEXT,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hektor_offre (
            hektor_offre_id TEXT PRIMARY KEY,
            hektor_annonce_id TEXT,
            hektor_mandat_id TEXT,
            hektor_acquereur_id TEXT,
            nom TEXT,
            prenom TEXT,
            raw_status TEXT,
            raw_date TEXT,
            offre_state TEXT,
            offre_event_date TEXT,
            raw_montant TEXT,
            acquereur_json TEXT,
            propositions_json TEXT,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hektor_compromis (
            hektor_compromis_id TEXT PRIMARY KEY,
            hektor_annonce_id TEXT,
            hektor_mandat_id TEXT,
            status TEXT,
            compromis_state TEXT,
            date_start TEXT,
            date_end TEXT,
            date_signature_acte TEXT,
            part_admin TEXT,
            sequestre TEXT,
            prix_net_vendeur TEXT,
            prix_publique TEXT,
            mandants_json TEXT,
            acquereurs_json TEXT,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hektor_vente (
            hektor_vente_id TEXT PRIMARY KEY,
            hektor_annonce_id TEXT,
            hektor_mandat_id TEXT,
            date_vente TEXT,
            prix TEXT,
            honoraires TEXT,
            part_admin TEXT,
            commission_agence TEXT,
            mandants_json TEXT,
            acquereurs_json TEXT,
            notaires_json TEXT,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hektor_broadcast (
            hektor_broadcast_id TEXT PRIMARY KEY,
            nom TEXT,
            count INTEGER,
            listings_json TEXT,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hektor_broadcast_listing (
            hektor_broadcast_id TEXT NOT NULL,
            hektor_annonce_id TEXT NOT NULL,
            passerelle TEXT,
            commercial_id TEXT,
            commercial_type TEXT,
            commercial_nom TEXT,
            commercial_prenom TEXT,
            export_status TEXT,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL,
            PRIMARY KEY (hektor_broadcast_id, hektor_annonce_id, commercial_id)
        );

        CREATE TABLE IF NOT EXISTS hektor_broadcast_portal (
            hektor_broadcast_id TEXT PRIMARY KEY,
            passerelle_key TEXT NOT NULL,
            listing_count INTEGER,
            supports_read INTEGER NOT NULL DEFAULT 1,
            supports_write INTEGER NOT NULL DEFAULT 1,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hektor_annonce_broadcast_state (
            hektor_broadcast_id TEXT NOT NULL,
            hektor_annonce_id TEXT NOT NULL,
            commercial_key TEXT NOT NULL,
            passerelle_key TEXT NOT NULL,
            commercial_id TEXT,
            commercial_type TEXT,
            commercial_nom TEXT,
            commercial_prenom TEXT,
            current_state TEXT NOT NULL,
            export_status TEXT,
            is_success INTEGER NOT NULL DEFAULT 0,
            is_error INTEGER NOT NULL DEFAULT 0,
            raw_json TEXT NOT NULL,
            synced_at TEXT NOT NULL,
            PRIMARY KEY (hektor_broadcast_id, hektor_annonce_id, commercial_key)
        );

        CREATE TABLE IF NOT EXISTS hektor_annonce_broadcast_target (
            hektor_broadcast_id TEXT NOT NULL,
            hektor_annonce_id TEXT NOT NULL,
            target_state TEXT NOT NULL,
            source_ref TEXT,
            note TEXT,
            updated_at TEXT NOT NULL,
            last_applied_at TEXT,
            last_apply_status TEXT,
            last_apply_error TEXT,
            PRIMARY KEY (hektor_broadcast_id, hektor_annonce_id)
        );

        CREATE TABLE IF NOT EXISTS case_dossier_source (
            hektor_annonce_id TEXT PRIMARY KEY,
            no_dossier TEXT,
            no_mandat TEXT,
            hektor_agence_id TEXT,
            hektor_negociateur_id TEXT,
            negociateur_nom TEXT,
            negociateur_prenom TEXT,
            negociateur_email TEXT,
            negociateur_telephone TEXT,
            negociateur_portable TEXT,
            statut_name TEXT,
            annonce_source_status TEXT,
            archive TEXT,
            diffusable TEXT,
            valide TEXT,
            prix REAL,
            case_kind TEXT,
            mandat_id TEXT,
            mandat_type TEXT,
            mandat_date_debut TEXT,
            mandat_date_fin TEXT,
            mandat_date_cloture TEXT,
            offre_id TEXT,
            compromis_id TEXT,
            vente_id TEXT,
            vente_date TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_raw_endpoint_object ON raw_api_response(endpoint_name, object_type, object_id_key, page_key);
        CREATE INDEX IF NOT EXISTS idx_annonce_nego ON hektor_annonce(hektor_negociateur_id);
        CREATE INDEX IF NOT EXISTS idx_annonce_dossier ON hektor_annonce(no_dossier, no_mandat);
        CREATE INDEX IF NOT EXISTS idx_mandat_annonce ON hektor_mandat(hektor_annonce_id, numero);
        CREATE INDEX IF NOT EXISTS idx_offre_annonce ON hektor_offre(hektor_annonce_id);
        CREATE INDEX IF NOT EXISTS idx_compromis_annonce ON hektor_compromis(hektor_annonce_id);
        CREATE INDEX IF NOT EXISTS idx_vente_annonce ON hektor_vente(hektor_annonce_id);
        CREATE INDEX IF NOT EXISTS idx_contact_nego ON hektor_contact(hektor_negociateur_id);
        CREATE INDEX IF NOT EXISTS idx_broadcast_listing_annonce ON hektor_broadcast_listing(hektor_annonce_id);
        CREATE INDEX IF NOT EXISTS idx_broadcast_listing_status ON hektor_broadcast_listing(export_status);
        CREATE INDEX IF NOT EXISTS idx_broadcast_state_annonce ON hektor_annonce_broadcast_state(hektor_annonce_id);
        CREATE INDEX IF NOT EXISTS idx_broadcast_state_portal ON hektor_annonce_broadcast_state(passerelle_key, current_state);
        CREATE INDEX IF NOT EXISTS idx_broadcast_target_annonce ON hektor_annonce_broadcast_target(hektor_annonce_id, target_state);
        CREATE INDEX IF NOT EXISTS idx_sync_annonce_variant ON sync_annonce_state(listing_variant, date_maj);
        CREATE INDEX IF NOT EXISTS idx_sync_contact_variant ON sync_contact_state(listing_variant, date_last_traitement);
        CREATE INDEX IF NOT EXISTS idx_sync_link_contact ON sync_annonce_contact_link(hektor_contact_id);
        """
    )
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(sync_run)")}
    for column_name, ddl in (
        ("pid", "ALTER TABLE sync_run ADD COLUMN pid INTEGER"),
        ("heartbeat_at", "ALTER TABLE sync_run ADD COLUMN heartbeat_at TEXT"),
        ("current_step", "ALTER TABLE sync_run ADD COLUMN current_step TEXT"),
        ("current_resource", "ALTER TABLE sync_run ADD COLUMN current_resource TEXT"),
        ("current_endpoint", "ALTER TABLE sync_run ADD COLUMN current_endpoint TEXT"),
        ("current_object_id", "ALTER TABLE sync_run ADD COLUMN current_object_id TEXT"),
        ("current_page", "ALTER TABLE sync_run ADD COLUMN current_page INTEGER"),
        ("progress_done", "ALTER TABLE sync_run ADD COLUMN progress_done INTEGER"),
        ("progress_total", "ALTER TABLE sync_run ADD COLUMN progress_total INTEGER"),
        ("progress_unit", "ALTER TABLE sync_run ADD COLUMN progress_unit TEXT"),
    ):
        if column_name not in existing_columns:
            conn.execute(ddl)
    existing_annonce_columns = {row["name"] for row in conn.execute("PRAGMA table_info(hektor_annonce)")}
    if "date_maj" not in existing_annonce_columns:
        conn.execute("ALTER TABLE hektor_annonce ADD COLUMN date_maj TEXT")
    existing_offre_columns = {row["name"] for row in conn.execute("PRAGMA table_info(hektor_offre)")}
    for column_name, ddl in (
        ("offre_state", "ALTER TABLE hektor_offre ADD COLUMN offre_state TEXT"),
        ("offre_event_date", "ALTER TABLE hektor_offre ADD COLUMN offre_event_date TEXT"),
    ):
        if column_name not in existing_offre_columns:
            conn.execute(ddl)
    existing_compromis_columns = {row["name"] for row in conn.execute("PRAGMA table_info(hektor_compromis)")}
    if "compromis_state" not in existing_compromis_columns:
        conn.execute("ALTER TABLE hektor_compromis ADD COLUMN compromis_state TEXT")
    existing_case_columns = {row["name"] for row in conn.execute("PRAGMA table_info(case_dossier_source)")}
    if "annonce_source_status" not in existing_case_columns:
        conn.execute("ALTER TABLE case_dossier_source ADD COLUMN annonce_source_status TEXT")
    if "case_kind" not in existing_case_columns:
        conn.execute("ALTER TABLE case_dossier_source ADD COLUMN case_kind TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sync_run_status ON sync_run(status, heartbeat_at, started_at)")
    conn.commit()


def create_sync_run(conn: sqlite3.Connection, stage: str, notes: Optional[str] = None) -> int:
    cleanup_stale_sync_runs(conn, stale_after_minutes=RUN_STALE_AFTER_MINUTES)
    cursor = conn.execute(
        """
        INSERT INTO sync_run(
            stage, started_at, status, notes, pid, heartbeat_at, current_step,
            current_resource, current_endpoint, current_object_id, current_page,
            progress_done, progress_total, progress_unit
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            stage,
            now_utc_iso(),
            "running",
            notes,
            os.getpid(),
            now_utc_iso(),
            "starting",
            None,
            None,
            None,
            None,
            0,
            0,
            "items",
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def finish_sync_run(conn: sqlite3.Connection, run_id: int, status: str, notes: Optional[str] = None) -> None:
    conn.execute(
        """
        UPDATE sync_run
        SET finished_at = ?,
            heartbeat_at = ?,
            status = ?,
            notes = COALESCE(?, notes)
        WHERE id = ?
        """,
        (now_utc_iso(), now_utc_iso(), status, notes, run_id),
    )
    conn.commit()


def update_sync_run_progress(
    conn: sqlite3.Connection,
    run_id: int,
    *,
    current_step: str,
    current_resource: str | None = None,
    current_endpoint: str | None = None,
    current_object_id: str | None = None,
    current_page: int | None = None,
    progress_done: int | None = None,
    progress_total: int | None = None,
    progress_unit: str | None = None,
    notes: str | None = None,
) -> None:
    conn.execute(
        """
        UPDATE sync_run
        SET heartbeat_at = ?,
            current_step = ?,
            current_resource = ?,
            current_endpoint = ?,
            current_object_id = ?,
            current_page = ?,
            progress_done = COALESCE(?, progress_done),
            progress_total = COALESCE(?, progress_total),
            progress_unit = COALESCE(?, progress_unit),
            notes = COALESCE(?, notes)
        WHERE id = ?
        """,
        (
            now_utc_iso(),
            current_step,
            current_resource,
            current_endpoint,
            current_object_id,
            current_page,
            progress_done,
            progress_total,
            progress_unit,
            notes,
            run_id,
        ),
    )
    conn.commit()


def cleanup_stale_sync_runs(conn: sqlite3.Connection, *, stale_after_minutes: int = RUN_STALE_AFTER_MINUTES) -> int:
    threshold = utc_now() - timedelta(minutes=stale_after_minutes)
    updated = 0
    rows = conn.execute(
        """
        SELECT id, started_at, heartbeat_at
        FROM sync_run
        WHERE status = 'running' AND finished_at IS NULL
        """
    ).fetchall()
    for row in rows:
        heartbeat_dt = parse_utc_iso(row["heartbeat_at"])
        started_dt = parse_utc_iso(row["started_at"])
        reference_dt = heartbeat_dt or started_dt
        if reference_dt is None or reference_dt > threshold:
            continue
        conn.execute(
            """
            UPDATE sync_run
            SET status = 'abandoned',
                finished_at = ?,
                notes = COALESCE(notes || ' | ', '') || ?
            WHERE id = ?
            """,
            (
                now_utc_iso(),
                f"Marked abandoned after {stale_after_minutes} minutes without heartbeat",
                row["id"],
            ),
        )
        updated += 1
    if updated:
        conn.commit()
    return updated


def log_sync_error(
    conn: sqlite3.Connection,
    *,
    run_id: Optional[int],
    stage: str,
    endpoint_name: Optional[str],
    object_type: Optional[str],
    object_id: Optional[str],
    page: Optional[int],
    error_message: str,
) -> None:
    conn.execute(
        """
        INSERT INTO sync_error(run_id, stage, endpoint_name, object_type, object_id, page, error_message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, stage, endpoint_name, object_type, object_id, page, error_message, now_utc_iso()),
    )
    conn.commit()


def upsert_raw_response(
    conn: sqlite3.Connection,
    *,
    run_id: Optional[int],
    endpoint_name: str,
    object_type: str,
    object_id: Optional[str],
    page: Optional[int],
    params: Optional[Dict[str, Any]],
    payload: Dict[str, Any],
    http_status: int,
) -> None:
    conn.execute(
        """
        INSERT INTO raw_api_response (
            run_id, endpoint_name, object_type, object_id, object_id_key, page, page_key, params_json, payload_json, http_status, fetched_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(endpoint_name, object_type, object_id_key, page_key)
        DO UPDATE SET
            run_id = excluded.run_id,
            params_json = excluded.params_json,
            payload_json = excluded.payload_json,
            http_status = excluded.http_status,
            fetched_at = excluded.fetched_at
        """,
        (
            run_id,
            endpoint_name,
            object_type,
            object_id,
            object_id or "",
            page,
            -1 if page is None else page,
            json.dumps(params or {}, ensure_ascii=False),
            json.dumps(payload, ensure_ascii=False),
            http_status,
            now_utc_iso(),
        ),
    )
    conn.commit()


def fetch_latest_raw_payloads(conn: sqlite3.Connection, endpoint_name: str) -> Iterable[sqlite3.Row]:
    return conn.execute(
        """
        SELECT r.*
        FROM raw_api_response r
        JOIN (
            SELECT endpoint_name, object_type, object_id_key, page_key,
                   MAX(id) AS max_id
            FROM raw_api_response
            WHERE endpoint_name = ?
            GROUP BY endpoint_name, object_type, object_id_key, page_key
        ) latest ON latest.max_id = r.id
        ORDER BY r.id
        """,
        (endpoint_name,),
    )


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def sleep_brief(delay_seconds: float = 0.1) -> None:
    time.sleep(delay_seconds)
