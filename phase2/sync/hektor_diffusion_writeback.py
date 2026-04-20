from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hektor_pipeline.common import HektorClient, Settings, connect_db

PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
REFRESH_SINGLE_ANNONCE_SCRIPT = ROOT / "phase2" / "sync" / "refresh_single_annonce.py"

DEFAULT_AGENCY_TARGETS: tuple[tuple[str, str, str], ...] = (
    ("Groupe GTI Ambert", "bienicidirect", "2"),
    ("Groupe GTI Ambert", "leboncoinDirect", "35"),
    ("Groupe GTI ANNONAY", "bienicidirect", "3"),
    ("Groupe GTI ANNONAY", "leboncoinDirect", "36"),
    ("Groupe GTI BRIOUDE", "bienicidirect", "4"),
    ("Groupe GTI BRIOUDE", "leboncoinDirect", "41"),
    ("Groupe GTI Craponne-sur-Arzon", "bienicidirect", "5"),
    ("Groupe GTI Craponne-sur-Arzon", "leboncoinDirect", "42"),
    ("Groupe GTI Yssingeaux", "bienicidirect", "6"),
    ("Groupe GTI Yssingeaux", "leboncoinDirect", "38"),
    ("Groupe GTI Montbrison", "bienicidirect", "7"),
    ("Groupe GTI Montbrison", "leboncoinDirect", "37"),
    ("Groupe GTI Saint-Just-Saint-Rambert", "bienicidirect", "8"),
    ("Groupe GTI Saint-Just-Saint-Rambert", "leboncoinDirect", "37"),
    ("Groupe GTI Issoire", "bienicidirect", "9"),
    ("Groupe GTI Issoire", "leboncoinDirect", "41"),
    ("Groupe GTI Saint-Bonnet-le-Château", "bienicidirect", "10"),
    ("Groupe GTI Saint-Bonnet-le-Château", "leboncoinDirect", "42"),
    ("Groupe GTI COURPIERE", "bienicidirect", "11"),
    ("Groupe GTI COURPIERE", "leboncoinDirect", "35"),
    ("Groupe GTI Monistrol sur Loire", "bienicidirect", "13"),
    ("Groupe GTI Monistrol sur Loire", "leboncoinDirect", "40"),
    ("Groupe GTI Saint-Didier-en-Velay", "bienicidirect", "14"),
    ("Groupe GTI Saint-Didier-en-Velay", "leboncoinDirect", "40"),
    ("Groupe GTI Firminy", "bienicidirect", "15"),
    ("Groupe GTI Firminy", "leboncoinDirect", "39"),
    ("Groupe GTI Saint-Etienne", "bienicidirect", "16"),
    ("Groupe GTI Saint-Etienne", "leboncoinDirect", "39"),
    ("Groupe GTI Dunières", "bienicidirect", "17"),
    ("Groupe GTI Dunières", "leboncoinDirect", "43"),
    ("Groupe GTI Tence", "bienicidirect", "22"),
    ("Groupe GTI Tence", "leboncoinDirect", "43"),
    ("Groupe Gti Le Puy en Velay", "bienicidirect", "23"),
    ("Groupe Gti Le Puy en Velay", "leboncoinDirect", "38"),
)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class DiffusionTarget:
    app_dossier_id: int
    hektor_annonce_id: str
    hektor_broadcast_id: str
    portal_key: str
    target_state: str


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_value.lower().split()).strip()


def fetchone_or_fail(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...], message: str) -> sqlite3.Row:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise RuntimeError(message)
    return row


def load_dossier(conn: sqlite3.Connection, app_dossier_id: int) -> sqlite3.Row:
    return fetchone_or_fail(
        conn,
        """
        SELECT
            d.id,
            d.hektor_annonce_id,
            d.numero_dossier,
            d.numero_mandat,
            v.validation_diffusion_state,
            v.diffusable
        FROM app_dossier d
        LEFT JOIN app_view_generale v
          ON v.app_dossier_id = d.id
        WHERE d.id = ?
        """,
        (app_dossier_id,),
        f"app_dossier introuvable: {app_dossier_id}",
    )


def ensure_agency_target_config(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_diffusion_agency_target (
            agence_nom TEXT NOT NULL,
            portal_key TEXT NOT NULL,
            hektor_broadcast_id TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (agence_nom, portal_key)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_app_diffusion_agency_target_portal
        ON app_diffusion_agency_target(portal_key, hektor_broadcast_id, is_active)
        """
    )
    conn.executemany(
        """
        INSERT OR IGNORE INTO app_diffusion_agency_target(
            agence_nom, portal_key, hektor_broadcast_id, is_active, note
        )
        VALUES(?, ?, ?, 1, 'Flux par agence')
        """,
        DEFAULT_AGENCY_TARGETS,
    )
    conn.commit()


def load_agency_name(conn: sqlite3.Connection, app_dossier_id: int) -> str:
    row = fetchone_or_fail(
        conn,
        """
        SELECT agence_nom
        FROM app_view_generale
        WHERE app_dossier_id = ?
        """,
        (app_dossier_id,),
        f"Agence introuvable pour app_dossier_id={app_dossier_id}",
    )
    agence_nom = str(row["agence_nom"] or "").strip()
    if not agence_nom:
        raise RuntimeError(f"Agence vide pour app_dossier_id={app_dossier_id}")
    return agence_nom


def load_agency_targets(conn: sqlite3.Connection, agence_nom: str) -> list[sqlite3.Row]:
    ensure_agency_target_config(conn)
    normalized_agence = normalize_text(agence_nom)
    rows = conn.execute(
        """
        SELECT agence_nom, portal_key, hektor_broadcast_id
        FROM app_diffusion_agency_target
        WHERE COALESCE(is_active, 1) = 1
        ORDER BY portal_key, hektor_broadcast_id
        """
    ).fetchall()
    matching_rows = [row for row in rows if normalize_text(str(row["agence_nom"] or "")) == normalized_agence]
    if not matching_rows:
        raise RuntimeError(f"Aucun flux de diffusion parametre pour l'agence '{agence_nom}'")
    return matching_rows


def load_portal_keys_by_broadcast_id(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT hektor_broadcast_id, passerelle_key
        FROM hektor_broadcast_portal
        WHERE COALESCE(supports_write, 0) = 1
        """
    ).fetchall()
    if not rows:
        raise RuntimeError("Aucune passerelle writable dans hektor_broadcast_portal")
    return {str(row["hektor_broadcast_id"]): str(row["passerelle_key"] or "") for row in rows}


def known_broadcast_ids_for_annonce(conn: sqlite3.Connection, annonce_id: str) -> set[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT hektor_broadcast_id
        FROM hektor_annonce_broadcast_state
        WHERE hektor_annonce_id = ?
        """,
        (annonce_id,),
    ).fetchall()
    return {str(row["hektor_broadcast_id"] or "").strip() for row in rows if str(row["hektor_broadcast_id"] or "").strip()}


def seed_default_targets(
    *,
    phase2_conn: sqlite3.Connection,
    hektor_conn: sqlite3.Connection,
    app_dossier_id: int,
    requested_by: str | None,
    target_state: str = "enabled",
    source_ref: str = "accepted_default",
    note: str = "Activation par defaut suite a acceptation",
    requested_by_role: str = "system",
) -> int:
    dossier = load_dossier(phase2_conn, app_dossier_id)
    agence_nom = load_agency_name(phase2_conn, app_dossier_id)
    agency_targets = load_agency_targets(phase2_conn, agence_nom)
    portal_keys_by_broadcast_id = load_portal_keys_by_broadcast_id(hektor_conn)
    now_iso = now_utc_iso()
    valid_broadcast_ids = {str(portal["hektor_broadcast_id"] or "").strip() for portal in agency_targets}
    phase2_conn.execute(
        """
        DELETE FROM app_diffusion_target
        WHERE app_dossier_id = ?
          AND hektor_broadcast_id NOT IN ({placeholders})
        """.format(placeholders=", ".join("?" for _ in valid_broadcast_ids)),
        (app_dossier_id, *sorted(valid_broadcast_ids)),
    )
    count = 0
    for portal in agency_targets:
        broadcast_id = str(portal["hektor_broadcast_id"] or "").strip()
        portal_key = portal_keys_by_broadcast_id.get(broadcast_id) or str(portal["portal_key"] or "").strip()
        if not broadcast_id or not portal_key:
            raise RuntimeError(f"Configuration diffusion invalide pour l'agence '{agence_nom}'")
        phase2_conn.execute(
            """
            INSERT INTO app_diffusion_target(
                app_dossier_id, hektor_annonce_id, hektor_broadcast_id, portal_key,
                target_state, source_ref, note, requested_by_role, requested_by_name,
                requested_at, created_at, updated_at
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(app_dossier_id, hektor_broadcast_id) DO UPDATE SET
                target_state = excluded.target_state,
                source_ref = excluded.source_ref,
                note = excluded.note,
                requested_by_role = excluded.requested_by_role,
                requested_by_name = excluded.requested_by_name,
                requested_at = excluded.requested_at,
                updated_at = excluded.updated_at
            """,
            (
                app_dossier_id,
                str(dossier["hektor_annonce_id"]),
                broadcast_id,
                portal_key,
                target_state,
                source_ref,
                note,
                requested_by_role,
                requested_by,
                now_iso,
                now_iso,
                now_iso,
            ),
        )
        count += 1
    phase2_conn.commit()
    return count


def preview_default_targets(
    *,
    phase2_conn: sqlite3.Connection,
    hektor_conn: sqlite3.Connection,
    app_dossier_id: int,
    target_state: str = "disabled",
) -> list[DiffusionTarget]:
    dossier = load_dossier(phase2_conn, app_dossier_id)
    agence_nom = load_agency_name(phase2_conn, app_dossier_id)
    agency_targets = load_agency_targets(phase2_conn, agence_nom)
    portal_keys_by_broadcast_id = load_portal_keys_by_broadcast_id(hektor_conn)
    preview: list[DiffusionTarget] = []
    for portal in agency_targets:
        broadcast_id = str(portal["hektor_broadcast_id"] or "").strip()
        portal_key = portal_keys_by_broadcast_id.get(broadcast_id) or str(portal["portal_key"] or "").strip()
        if not broadcast_id or not portal_key:
            raise RuntimeError(f"Configuration diffusion invalide pour l'agence '{agence_nom}'")
        preview.append(
            DiffusionTarget(
                app_dossier_id=app_dossier_id,
                hektor_annonce_id=str(dossier["hektor_annonce_id"]),
                hektor_broadcast_id=broadcast_id,
                portal_key=portal_key,
                target_state=target_state,
            )
        )
    return preview


def seed_single_target(
    *,
    phase2_conn: sqlite3.Connection,
    app_dossier_id: int,
    hektor_broadcast_id: str,
    portal_key: str,
    requested_by: str | None,
) -> int:
    dossier = load_dossier(phase2_conn, app_dossier_id)
    now_iso = now_utc_iso()
    phase2_conn.execute(
        """
        DELETE FROM app_diffusion_target
        WHERE app_dossier_id = ?
        """,
        (app_dossier_id,),
    )
    phase2_conn.execute(
        """
        INSERT INTO app_diffusion_target(
            app_dossier_id, hektor_annonce_id, hektor_broadcast_id, portal_key,
            target_state, source_ref, note, requested_by_role, requested_by_name,
            requested_at, created_at, updated_at
        )
        VALUES(?, ?, ?, ?, 'enabled', 'single_target_test', 'Test unitaire passerelle', 'system', ?, ?, ?, ?)
        """,
        (
            app_dossier_id,
            str(dossier["hektor_annonce_id"]),
            str(hektor_broadcast_id),
            str(portal_key),
            requested_by,
            now_iso,
            now_iso,
            now_iso,
        ),
    )
    phase2_conn.commit()
    return 1


def replace_targets(
    *,
    phase2_conn: sqlite3.Connection,
    app_dossier_id: int,
    targets: Iterable[dict[str, Any]],
    requested_by: str | None,
) -> list[DiffusionTarget]:
    dossier = load_dossier(phase2_conn, app_dossier_id)
    now_iso = now_utc_iso()
    phase2_conn.execute("DELETE FROM app_diffusion_target WHERE app_dossier_id = ?", (app_dossier_id,))
    for item in targets:
        broadcast_id = str(item.get("hektor_broadcast_id") or "").strip()
        portal_key = str(item.get("portal_key") or "").strip()
        target_state = str(item.get("target_state") or "disabled").strip() or "disabled"
        if not broadcast_id:
            raise RuntimeError("hektor_broadcast_id manquant dans replace-targets")
        phase2_conn.execute(
            """
            INSERT INTO app_diffusion_target(
                app_dossier_id, hektor_annonce_id, hektor_broadcast_id, portal_key,
                target_state, source_ref, note, requested_by_role, requested_by_name,
                requested_at, created_at, updated_at
            )
            VALUES(?, ?, ?, ?, ?, 'console_diffusion', NULL, 'app', ?, ?, ?, ?)
            """,
            (
                app_dossier_id,
                str(dossier["hektor_annonce_id"]),
                broadcast_id,
                portal_key,
                target_state,
                requested_by,
                now_iso,
                now_iso,
                now_iso,
            ),
        )
    phase2_conn.commit()
    return load_targets(phase2_conn, app_dossier_id)


def load_targets(conn: sqlite3.Connection, app_dossier_id: int) -> list[DiffusionTarget]:
    rows = conn.execute(
        """
        SELECT app_dossier_id, hektor_annonce_id, hektor_broadcast_id, portal_key, target_state
        FROM app_diffusion_target
        WHERE app_dossier_id = ?
        ORDER BY portal_key, hektor_broadcast_id
        """,
        (app_dossier_id,),
    ).fetchall()
    return [
        DiffusionTarget(
            app_dossier_id=int(row["app_dossier_id"]),
            hektor_annonce_id=str(row["hektor_annonce_id"]),
            hektor_broadcast_id=str(row["hektor_broadcast_id"]),
            portal_key=str(row["portal_key"] or ""),
            target_state=str(row["target_state"]),
        )
        for row in rows
    ]


def fetch_annonce_detail(client: HektorClient, settings: Settings, annonce_id: str) -> dict[str, Any]:
    return client.get_json(
        "/Api/Annonce/AnnonceById/",
        params={"id": annonce_id, "version": settings.api_version},
    )


def fetch_annonce_detail_optional(client: HektorClient, settings: Settings, annonce_id: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return fetch_annonce_detail(client, settings, annonce_id), None
    except Exception as exc:
        return None, normalize_hektor_message(str(exc))


def fetch_annonce_search_row(
    client: HektorClient,
    settings: Settings,
    *,
    annonce_id: str,
    numero_dossier: str | None,
) -> dict[str, Any] | None:
    search = (numero_dossier or "").strip()
    if not search:
        return None
    payload = client.get_json(
        "/Api/Annonce/searchAnnonces/",
        params={"search": search, "strict": "1", "version": settings.api_version},
    )
    rows = payload.get("liste")
    if not isinstance(rows, list):
        rows = payload.get("data")
    if not isinstance(rows, list):
        return None
    for row in rows:
        if isinstance(row, dict) and str(row.get("id") or "") == annonce_id:
            return row
    return rows[0] if rows and isinstance(rows[0], dict) else None


def extract_diffusable(detail_payload: dict[str, Any]) -> str | None:
    if detail_payload.get("diffusable") is not None:
        return str(detail_payload.get("diffusable"))
    data = detail_payload.get("data")
    if isinstance(data, dict):
        for candidate in (data.get("annonce"), data.get("keyData"), data):
            if isinstance(candidate, dict):
                value = candidate.get("diffusable")
                if value is not None:
                    return str(value)
    return None


def read_observed_diffusable(client: HektorClient, settings: Settings, dossier: sqlite3.Row, annonce_id: str) -> str | None:
    try:
        return extract_diffusable(fetch_annonce_detail(client, settings, annonce_id))
    except Exception:
        row = fetch_annonce_search_row(
            client,
            settings,
            annonce_id=annonce_id,
            numero_dossier=str(dossier["numero_dossier"] or ""),
        )
        return extract_diffusable(row or {})


def extract_validation_state(detail_payload: dict[str, Any]) -> str | None:
    def normalize_validation_value(value: Any) -> str | None:
        text = str(value).strip()
        if not text:
            return None
        lowered = text.lower()
        if lowered in {"1", "true", "oui", "ok", "valide", "validee", "validation ok"}:
            return "oui"
        if lowered in {"0", "false", "non", "invalide"}:
            return "non"
        return text

    validation_keys = (
        "validation",
        "valide",
        "validated",
        "isValid",
        "is_valid",
        "checkValid",
        "check_valid",
        "validationMandat",
        "validation_mandat",
    )
    for key in validation_keys:
        value = detail_payload.get(key)
        if value is not None:
            return normalize_validation_value(value)
    data = detail_payload.get("data")
    if isinstance(data, dict):
        for candidate in (data.get("annonce"), data.get("keyData"), data):
            if not isinstance(candidate, dict):
                continue
            for key in validation_keys:
                value = candidate.get(key)
                if value is not None:
                    return normalize_validation_value(value)
    return None


def list_passerelles_payload(client: HektorClient, settings: Settings, annonce_id: str) -> dict[str, Any]:
    return client.get_json(
        "/Api/Annonce/ListPasserelles/",
        params={"idAnnonce": annonce_id, "version": settings.api_version},
    )


def iter_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from iter_dicts(nested)
    elif isinstance(value, list):
        for item in value:
            yield from iter_dicts(item)


def extract_live_enabled_ids(payload: dict[str, Any]) -> set[str]:
    enabled: set[str] = set()
    for item in iter_dicts(payload.get("data")):
        candidate_id = item.get("idPasserelle") or item.get("id")
        if candidate_id in (None, "", 0, "0"):
            continue
        raw_enabled = item.get("active")
        raw_state = item.get("state") or item.get("statut") or item.get("status")
        raw_selected = item.get("selected")
        is_enabled = raw_enabled in (1, "1", True, "true") or raw_selected in (1, "1", True, "true")
        if not is_enabled and raw_state is not None:
            is_enabled = str(raw_state).lower() in {"1", "active", "enabled", "selected", "checked", "exported"}
        if is_enabled:
            enabled.add(str(candidate_id))
    return enabled


def fallback_enabled_ids_from_local(hektor_conn: sqlite3.Connection, annonce_id: str) -> set[str]:
    rows = hektor_conn.execute(
        """
        SELECT DISTINCT hektor_broadcast_id
        FROM hektor_annonce_broadcast_state
        WHERE hektor_annonce_id = ?
          AND current_state = 'broadcasted'
        """,
        (annonce_id,),
    ).fetchall()
    return {str(row["hektor_broadcast_id"]) for row in rows}


def log_action(
    conn: sqlite3.Connection,
    *,
    app_dossier_id: int,
    annonce_id: str,
    broadcast_id: str | None,
    portal_key: str | None,
    action_type: str,
    requested_by: str,
    status: str,
    api_response: str | None = None,
    error_message: str | None = None,
    executed_at: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO app_broadcast_action(
            app_dossier_id, hektor_annonce_id, hektor_broadcast_id, portal_key,
            action_type, requested_by, requested_at, status, api_response,
            error_message, executed_at
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            app_dossier_id,
            int(annonce_id),
            int(str(broadcast_id)) if broadcast_id not in (None, "") and str(broadcast_id).isdigit() else None,
            portal_key,
            action_type,
            requested_by,
            now_utc_iso(),
            status,
            api_response,
            error_message,
            executed_at,
        ),
    )


def update_target_apply_status(
    conn: sqlite3.Connection,
    *,
    app_dossier_id: int,
    broadcast_id: str,
    status: str,
    error_message: str | None,
) -> None:
    conn.execute(
        """
        UPDATE app_diffusion_target
        SET last_applied_at = ?, last_apply_status = ?, last_apply_error = ?, updated_at = ?
        WHERE app_dossier_id = ? AND hektor_broadcast_id = ?
        """,
        (now_utc_iso(), status, error_message, now_utc_iso(), app_dossier_id, broadcast_id),
    )


def normalize_hektor_message(message: str | None) -> str:
    return " ".join((message or "").replace("Â", " ").split()).strip()


def is_validation_state_approved(value: str | None) -> bool:
    normalized = normalize_text(value)
    return normalized in {"oui", "valide", "validee", "validation ok", "ok"}


def is_hektor_validation_pending_message(message: str | None) -> bool:
    text = normalize_hektor_message(message).lower()
    return (
        "unable to send listing" in text
        or "n'a pas été validée" in text
        or "na pas été validée" in text
        or "responsable réseau" in text
        or "responsable reseau" in text
    )


def apply_portal_change(
    client: HektorClient,
    *,
    action_name: str,
    hektor_broadcast_id: str,
    annonce_id: str,
    api_version: str,
):
    del api_version
    path = "/Api/Passerelle/addAnnonceToPasserelle/" if action_name == "add" else "/Api/Passerelle/removeAnnonceToPasserelle/"
    method = "PUT" if action_name == "add" else "DELETE"
    params = {
        "idPasserelle": hektor_broadcast_id,
        "idAnnonce": annonce_id,
    }
    if not client.jwt:
        client.authenticate()
    last_error: Exception | None = None
    for attempt in range(1, client.max_retries + 1):
        try:
            response = client.session.request(
                method,
                f"{client.settings.base_url}{path}",
                headers={"jwt": client.jwt or ""},
                params=params,
                timeout=client.settings.timeout,
            )
            refresh = response.headers.get("x-refresh-token")
            if refresh:
                client.jwt = refresh
            if response.status_code == 403 and "expired token" in (response.text or "").lower():
                client.authenticate()
                continue
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt >= client.max_retries:
                break
        except Exception as exc:
            last_error = exc
            break
    raise RuntimeError(f"{method} query {json.dumps(params, ensure_ascii=False)} => {normalize_hektor_message(str(last_error))}")


def try_diffuse_request(client: HektorClient, settings: Settings, annonce_id: str) -> str:
    params = {"idAnnonce": annonce_id, "version": settings.api_version}
    response = client.request("PATCH", "/Api/Annonce/Diffuse/", params=params)
    return response.text[:500] or "PATCH ok"


def set_property_validation(client: HektorClient, settings: Settings, annonce_id: str, *, state: int, dry_run: bool) -> dict[str, Any]:
    before, before_error = fetch_annonce_detail_optional(client, settings, annonce_id)
    before_validation = extract_validation_state(before) if before else None
    before_diffusable = extract_diffusable(before) if before else None
    if dry_run:
        return {
            "hektor_annonce_id": annonce_id,
            "dry_run": True,
            "requested_state": state,
            "validation_result": "would_patch_property_validation",
            "observed_validation_before": before_validation,
            "observed_validation": before_validation,
            "observed_diffusable_before": before_diffusable,
            "observed_diffusable": before_diffusable,
            "read_before_error": before_error,
            "read_after_error": None,
            "error": None,
        }
    response = client.request(
        "PATCH",
        "/Api/Annonce/PropertyValidation/",
        params={"idAnnonce": annonce_id, "state": state, "version": settings.api_version},
    )
    response_text = response.text[:1000] if response.text else ""
    response_payload: Any = None
    response_error: str | None = None
    try:
        response_payload = response.json()
        if isinstance(response_payload, dict):
            raw_error = response_payload.get("error")
            response_error = normalize_hektor_message(str(raw_error)) if raw_error not in (None, "", False) else None
    except Exception:
        response_payload = response_text or None

    after, after_error = fetch_annonce_detail_optional(client, settings, annonce_id)
    observed_validation = extract_validation_state(after) if after else None
    if observed_validation is None and isinstance(response_payload, dict):
        observed_validation = extract_validation_state(response_payload)
    observed_diffusable = extract_diffusable(after) if after else None
    if observed_diffusable is None and isinstance(response_payload, dict):
        observed_diffusable = extract_diffusable(response_payload)
    return {
        "hektor_annonce_id": annonce_id,
        "dry_run": False,
        "requested_state": state,
        "validation_result": "patched",
        "response_status": response.status_code,
        "response_payload": response_payload,
        "response_preview": response_text,
        "error": response_error,
        "observed_validation_before": before_validation,
        "observed_validation": observed_validation,
        "observed_diffusable_before": before_diffusable,
        "observed_diffusable": observed_diffusable,
        "read_before_error": before_error,
        "read_after_error": after_error,
    }


def set_validation_for_dossier(
    *,
    phase2_conn: sqlite3.Connection,
    app_dossier_id: int,
    state: int,
    dry_run: bool,
) -> dict[str, Any]:
    if state not in (0, 1):
        raise RuntimeError("state doit etre 0 ou 1")
    dossier = load_dossier(phase2_conn, app_dossier_id)
    annonce_id = str(dossier["hektor_annonce_id"])
    settings = Settings.from_env()
    client = HektorClient(settings)
    result = set_property_validation(client, settings, annonce_id, state=state, dry_run=dry_run)
    return {
        "app_dossier_id": app_dossier_id,
        **result,
    }


def refresh_single_annonce_local(annonce_id: str) -> dict[str, Any]:
    if not REFRESH_SINGLE_ANNONCE_SCRIPT.exists():
        return {"ok": False, "error": f"Script introuvable: {REFRESH_SINGLE_ANNONCE_SCRIPT}"}
    try:
        completed = subprocess.run(
            [sys.executable, str(REFRESH_SINGLE_ANNONCE_SCRIPT), "--id-annonce", str(annonce_id).strip()],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0:
        return {
            "ok": False,
            "error": f"refresh_single_annonce failed with code {completed.returncode}",
            "stdout": stdout or None,
            "stderr": stderr or None,
        }
    if stdout:
        try:
            payload = json.loads(stdout)
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
    return {"ok": True, "stdout": stdout or None, "stderr": stderr or None}


def set_diffusable_state(client: HektorClient, settings: Settings, dossier: sqlite3.Row, annonce_id: str, *, requested: bool, dry_run: bool) -> tuple[bool, str, str | None]:
    current = read_observed_diffusable(client, settings, dossier, annonce_id)
    requested_value = "1" if requested else "0"
    if current == requested_value:
        return False, "already_diffusable" if requested else "already_not_diffusable", current
    if dry_run:
        return True, "would_patch_diffuse", current
    try:
        response_preview = try_diffuse_request(client, settings, annonce_id)
        observed = read_observed_diffusable(client, settings, dossier, annonce_id)
        if observed == requested_value:
            return True, response_preview, observed
        return True, f"diffuse_unconfirmed: observed_diffusable={observed}; response={response_preview}", observed
    except Exception as exc:
        message = normalize_hektor_message(str(exc))
        try:
            observed = read_observed_diffusable(client, settings, dossier, annonce_id)
            if observed == requested_value:
                return True, f"confirmed_after_diffuse_error: {message}", observed
        except Exception:
            pass
        return True, f"diffuse_unconfirmed: {message}", current


def ensure_diffusable(client: HektorClient, settings: Settings, dossier: sqlite3.Row, annonce_id: str, *, dry_run: bool) -> tuple[bool, str]:
    changed, result, _ = set_diffusable_state(client, settings, dossier, annonce_id, requested=True, dry_run=dry_run)
    return changed, result


def set_diffusable_for_dossier(
    *,
    phase2_conn: sqlite3.Connection,
    app_dossier_id: int,
    diffusable: bool,
    dry_run: bool,
) -> dict[str, Any]:
    dossier = load_dossier(phase2_conn, app_dossier_id)
    annonce_id = str(dossier["hektor_annonce_id"])
    settings = Settings.from_env()
    client = HektorClient(settings)
    changed, result, observed = set_diffusable_state(
        client,
        settings,
        dossier,
        annonce_id,
        requested=diffusable,
        dry_run=dry_run,
    )
    if not dry_run:
        observed = read_observed_diffusable(client, settings, dossier, annonce_id)
    expected = "1" if diffusable else "0"
    return {
        "app_dossier_id": app_dossier_id,
        "hektor_annonce_id": annonce_id,
        "dry_run": dry_run,
        "requested_diffusable": diffusable,
        "changed": changed,
        "result": result,
        "observed_diffusable": observed,
        "error": None if dry_run or observed == expected else f"Hektor n'a pas confirme diffusable = {expected} apres PATCH Diffuse.",
    }


def build_apply_result(
    *,
    app_dossier_id: int,
    annonce_id: str,
    dry_run: bool,
    diffusable_changed: bool,
    diffusable_result: str,
    observed_diffusable: str | None,
    validation_state: str | None,
    validation_approved: bool,
    waiting_on_hektor: bool,
    waiting_message: str | None,
    current_enabled_count: int,
    targets_count: int,
    to_add_count: int,
    to_remove_count: int,
    applied: list[dict[str, Any]],
    failed: list[dict[str, Any]],
    pending: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "app_dossier_id": app_dossier_id,
        "hektor_annonce_id": annonce_id,
        "dry_run": dry_run,
        "diffusable_changed": diffusable_changed,
        "diffusable_result": diffusable_result,
        "observed_diffusable": observed_diffusable,
        "validation_state": validation_state,
        "validation_approved": validation_approved,
        "waiting_on_hektor": waiting_on_hektor,
        "waiting_message": waiting_message,
        "current_enabled_count": current_enabled_count,
        "targets_count": targets_count,
        "to_add_count": to_add_count,
        "to_remove_count": to_remove_count,
        "applied": applied,
        "failed": failed,
        "pending": pending,
    }


def apply_targets(
    *,
    phase2_conn: sqlite3.Connection,
    hektor_conn: sqlite3.Connection,
    app_dossier_id: int,
    requested_by: str,
    dry_run: bool,
    manage_diffusable: bool = False,
    reset_to_agency_defaults: bool = False,
    validation_state_override: str | None = None,
) -> dict[str, Any]:
    dossier = load_dossier(phase2_conn, app_dossier_id)
    annonce_id = str(dossier["hektor_annonce_id"])
    targets = load_targets(phase2_conn, app_dossier_id)
    if reset_to_agency_defaults or not targets:
        seed_default_targets(
            phase2_conn=phase2_conn,
            hektor_conn=hektor_conn,
            app_dossier_id=app_dossier_id,
            requested_by=requested_by,
            target_state="enabled" if reset_to_agency_defaults else "disabled",
            source_ref="accepted_default" if reset_to_agency_defaults else "console_seed",
            note="Activation par defaut suite a acceptation" if reset_to_agency_defaults else "Passerelles proposees par defaut dans la console diffusion",
            requested_by_role="system" if reset_to_agency_defaults else "app",
        )
        targets = load_targets(phase2_conn, app_dossier_id)
    if not targets:
        raise RuntimeError(f"Aucune cible de diffusion pour app_dossier_id={app_dossier_id}")

    settings = Settings.from_env()
    client = HektorClient(settings)
    validation_state = validation_state_override or (str(dossier["validation_diffusion_state"] or "").strip() or None)
    validation_approved = is_validation_state_approved(validation_state)

    diffusable_changed = False
    diffusable_result = "not_managed_in_console"
    observed_diffusable = str(dossier["diffusable"] or "").strip() or None
    waiting_on_hektor = False
    waiting_message: str | None = None

    applied: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    if manage_diffusable:
        diffusable_changed, diffusable_result = ensure_diffusable(client, settings, dossier, annonce_id, dry_run=dry_run)
        if not dry_run:
            try:
                observed_diffusable = read_observed_diffusable(client, settings, dossier, annonce_id)
                confirmed_diffusable = observed_diffusable == "1"
            except Exception as exc:
                confirmed_diffusable = False
                diffusable_result = normalize_hektor_message(str(exc)) or diffusable_result
            if not confirmed_diffusable:
                waiting_on_hektor = True
                if not validation_approved:
                    waiting_message = "Action Hektor non appliquee : l'annonce est encore en validation = non. Ouvre Hektor pour corriger la validation, puis relance."
                else:
                    waiting_message = "En attente de mise a jour Hektor. Le bien n'est pas encore confirme en diffusable."
                return build_apply_result(
                    app_dossier_id=app_dossier_id,
                    annonce_id=annonce_id,
                    dry_run=dry_run,
                    diffusable_changed=diffusable_changed,
                    diffusable_result=diffusable_result,
                    observed_diffusable=observed_diffusable,
                    validation_state=validation_state,
                    validation_approved=validation_approved,
                    waiting_on_hektor=waiting_on_hektor,
                    waiting_message=waiting_message,
                    current_enabled_count=0,
                    targets_count=len(targets),
                    to_add_count=0,
                    to_remove_count=0,
                    applied=applied,
                    failed=failed,
                    pending=pending,
                )

    live_payload = list_passerelles_payload(client, settings, annonce_id)
    current_enabled_ids = extract_live_enabled_ids(live_payload)
    if not current_enabled_ids:
        current_enabled_ids = fallback_enabled_ids_from_local(hektor_conn, annonce_id)
    desired_enabled = {target.hektor_broadcast_id for target in targets if target.target_state == "enabled"}
    desired_disabled = {target.hektor_broadcast_id for target in targets if target.target_state == "disabled"}

    to_add = [target for target in targets if target.hektor_broadcast_id in desired_enabled and target.hektor_broadcast_id not in current_enabled_ids]
    to_remove = [target for target in targets if target.hektor_broadcast_id in desired_disabled]
    for action_name, batch in (("add", to_add), ("remove", to_remove)):
        for target in batch:
            if dry_run:
                applied.append({"action": action_name, "portal_key": target.portal_key, "broadcast_id": target.hektor_broadcast_id, "dry_run": True})
                continue
            try:
                response = apply_portal_change(
                    client,
                    action_name=action_name,
                    hektor_broadcast_id=target.hektor_broadcast_id,
                    annonce_id=annonce_id,
                    api_version=settings.api_version,
                )
                payload_preview = response.text[:500]
                log_action(
                    phase2_conn,
                    app_dossier_id=app_dossier_id,
                    annonce_id=annonce_id,
                    broadcast_id=target.hektor_broadcast_id,
                    portal_key=target.portal_key,
                    action_type=action_name,
                    requested_by=requested_by,
                    status="done",
                    api_response=payload_preview,
                    executed_at=now_utc_iso(),
                )
                update_target_apply_status(
                    phase2_conn,
                    app_dossier_id=app_dossier_id,
                    broadcast_id=target.hektor_broadcast_id,
                    status="done",
                    error_message=None,
                )
                applied.append({"action": action_name, "portal_key": target.portal_key, "broadcast_id": target.hektor_broadcast_id})
            except Exception as exc:
                message = normalize_hektor_message(str(exc))
                if is_hektor_validation_pending_message(message):
                    waiting_on_hektor = True
                    waiting_message = "En attente de mise à jour Hektor. La demande est enregistrée mais Hektor n'a pas encore confirmé le bien en diffusable."
                    update_target_apply_status(
                        phase2_conn,
                        app_dossier_id=app_dossier_id,
                        broadcast_id=target.hektor_broadcast_id,
                        status="pending",
                        error_message=waiting_message,
                    )
                    pending.append(
                        {
                            "action": action_name,
                            "portal_key": target.portal_key,
                            "broadcast_id": target.hektor_broadcast_id,
                            "message": waiting_message,
                        }
                    )
                    continue
                log_action(
                    phase2_conn,
                    app_dossier_id=app_dossier_id,
                    annonce_id=annonce_id,
                    broadcast_id=target.hektor_broadcast_id,
                    portal_key=target.portal_key,
                    action_type=action_name,
                    requested_by=requested_by,
                    status="error",
                    error_message=message,
                    executed_at=now_utc_iso(),
                )
                update_target_apply_status(
                    phase2_conn,
                    app_dossier_id=app_dossier_id,
                    broadcast_id=target.hektor_broadcast_id,
                    status="error",
                    error_message=message,
                )
                failed.append({"action": action_name, "portal_key": target.portal_key, "broadcast_id": target.hektor_broadcast_id, "error": message})

    phase2_conn.commit()
    return build_apply_result(
        app_dossier_id=app_dossier_id,
        annonce_id=annonce_id,
        dry_run=dry_run,
        diffusable_changed=diffusable_changed,
        diffusable_result=diffusable_result,
        observed_diffusable=observed_diffusable,
        validation_state=validation_state,
        validation_approved=validation_approved,
        waiting_on_hektor=waiting_on_hektor,
        waiting_message=waiting_message,
        current_enabled_count=len(current_enabled_ids),
        targets_count=len(targets),
        to_add_count=len(to_add),
        to_remove_count=len(to_remove),
        applied=applied,
        failed=failed,
        pending=pending,
    )


def accept_request(
    *,
    phase2_conn: sqlite3.Connection,
    hektor_conn: sqlite3.Connection,
    app_dossier_id: int,
    requested_by: str,
    dry_run: bool,
) -> dict[str, Any]:
    validation = set_validation_for_dossier(
        phase2_conn=phase2_conn,
        app_dossier_id=app_dossier_id,
        state=1,
        dry_run=dry_run,
    )
    observed_validation = str(validation.get("observed_validation") or "").strip() or None
    validation_approved = is_validation_state_approved(observed_validation)
    observed_diffusable = str(validation.get("observed_diffusable") or "").strip() or None
    if not validation_approved:
        waiting_message = (
            "En attente de validation Hektor. La demande est acceptee, "
            "mais Hektor n'a pas encore confirme validation = oui."
        )
        return {
            "app_dossier_id": app_dossier_id,
            "hektor_annonce_id": validation.get("hektor_annonce_id"),
            "dry_run": dry_run,
            "validation_result": validation.get("validation_result"),
            "observed_validation": observed_validation,
            "diffusable_changed": False,
            "diffusable_result": "skipped_until_validation_confirmed",
            "observed_diffusable": observed_diffusable,
            "validation_state": observed_validation,
            "validation_approved": False,
            "waiting_on_hektor": True,
            "waiting_message": waiting_message,
            "current_enabled_count": 0,
            "targets_count": 0,
            "to_add_count": 0,
            "to_remove_count": 0,
            "applied": [],
            "failed": [],
            "pending": [],
            "validation_response_status": validation.get("response_status"),
            "validation_error": validation.get("error"),
        }

    apply_result = apply_targets(
        phase2_conn=phase2_conn,
        hektor_conn=hektor_conn,
        app_dossier_id=app_dossier_id,
        requested_by=requested_by,
        dry_run=dry_run,
        manage_diffusable=True,
        reset_to_agency_defaults=True,
        validation_state_override=observed_validation,
    )
    return {
        **apply_result,
        "validation_result": validation.get("validation_result"),
        "observed_validation": observed_validation,
        "validation_state": observed_validation,
        "validation_approved": True,
        "validation_response_status": validation.get("response_status"),
        "validation_error": validation.get("error"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write-back diffusion Hektor depuis les cibles phase2.")
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed-default-targets", help="Alimente app_diffusion_target avec les passerelles writable par defaut.")
    seed.add_argument("--app-dossier-id", type=int, required=True)
    seed.add_argument("--requested-by", default="system")

    preview = sub.add_parser("preview-default-targets", help="Retourne les passerelles par defaut d'un dossier sans rien ecrire.")
    preview.add_argument("--app-dossier-id", type=int, required=True)

    replace = sub.add_parser("replace-targets", help="Remplace les cibles de diffusion d'un dossier.")
    replace.add_argument("--app-dossier-id", type=int, required=True)
    replace.add_argument("--requested-by", default="system")
    replace.add_argument("--payload-json", required=True)

    list_targets = sub.add_parser("list-targets", help="Liste les cibles de diffusion d'un dossier.")
    list_targets.add_argument("--app-dossier-id", type=int, required=True)

    list_broadcasts = sub.add_parser("list-broadcasts", help="Liste les broadcasts locaux d'un dossier.")
    list_broadcasts.add_argument("--app-dossier-id", type=int, required=True)

    apply = sub.add_parser("apply-targets", help="Applique app_diffusion_target sur Hektor.")
    apply.add_argument("--app-dossier-id", type=int, required=True)
    apply.add_argument("--requested-by", default="system")
    apply.add_argument("--dry-run", action="store_true")
    apply.add_argument("--ensure-diffusable", action="store_true")

    accept = sub.add_parser("accept-request", help="Rend le bien diffusable puis applique les passerelles par defaut de l'agence.")
    accept.add_argument("--app-dossier-id", type=int, required=True)
    accept.add_argument("--requested-by", default="system")
    accept.add_argument("--dry-run", action="store_true")

    validation = sub.add_parser("set-validation", help="Valide ou invalide une annonce via PropertyValidation.")
    validation.add_argument("--app-dossier-id", type=int, required=True)
    validation.add_argument("--state", type=int, choices=[0, 1], required=True)
    validation.add_argument("--dry-run", action="store_true")

    diffusable = sub.add_parser("set-diffusable", help="Active ou desactive diffusable via PATCH Diffuse puis relecture Hektor.")
    diffusable.add_argument("--app-dossier-id", type=int, required=True)
    diffusable.add_argument("--state", type=int, choices=[0, 1], required=True)
    diffusable.add_argument("--dry-run", action="store_true")

    single = sub.add_parser("test-single-target", help="Ecrase localement les cibles d'un dossier avec une seule passerelle puis la teste.")
    single.add_argument("--app-dossier-id", type=int, required=True)
    single.add_argument("--broadcast-id", required=True)
    single.add_argument("--portal-key", required=True)
    single.add_argument("--requested-by", default="system")
    single.add_argument("--dry-run", action="store_true")
    single.add_argument("--ensure-diffusable", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    phase2_conn = connect_db(PHASE2_DB)
    hektor_conn = connect_db(HEKTOR_DB)
    try:
        if args.command == "seed-default-targets":
            count = seed_default_targets(
                phase2_conn=phase2_conn,
                hektor_conn=hektor_conn,
                app_dossier_id=args.app_dossier_id,
                requested_by=args.requested_by,
                target_state="disabled",
                source_ref="console_seed",
                note="Passerelles proposees par defaut dans la console diffusion",
                requested_by_role="app",
            )
            targets = [
                {
                    "app_dossier_id": target.app_dossier_id,
                    "hektor_annonce_id": target.hektor_annonce_id,
                    "hektor_broadcast_id": target.hektor_broadcast_id,
                    "portal_key": target.portal_key,
                    "target_state": target.target_state,
                }
                for target in load_targets(phase2_conn, args.app_dossier_id)
            ]
            print(json.dumps({"app_dossier_id": args.app_dossier_id, "seeded_targets": count, "targets": targets}, ensure_ascii=False, indent=2))
            return
        if args.command == "preview-default-targets":
            targets = preview_default_targets(
                phase2_conn=phase2_conn,
                hektor_conn=hektor_conn,
                app_dossier_id=args.app_dossier_id,
                target_state="disabled",
            )
            print(json.dumps({
                "app_dossier_id": args.app_dossier_id,
                "targets": [
                    {
                        "app_dossier_id": target.app_dossier_id,
                        "hektor_annonce_id": target.hektor_annonce_id,
                        "hektor_broadcast_id": target.hektor_broadcast_id,
                        "portal_key": target.portal_key,
                        "target_state": target.target_state,
                    }
                    for target in targets
                ],
            }, ensure_ascii=False, indent=2))
            return
        if args.command == "replace-targets":
            payload = json.loads(args.payload_json)
            if not isinstance(payload, list):
                raise RuntimeError("payload-json doit etre une liste")
            targets = replace_targets(
                phase2_conn=phase2_conn,
                app_dossier_id=args.app_dossier_id,
                targets=payload,
                requested_by=args.requested_by,
            )
            print(json.dumps({
                "app_dossier_id": args.app_dossier_id,
                "targets": [
                    {
                        "app_dossier_id": target.app_dossier_id,
                        "hektor_annonce_id": target.hektor_annonce_id,
                        "hektor_broadcast_id": target.hektor_broadcast_id,
                        "portal_key": target.portal_key,
                        "target_state": target.target_state,
                    }
                    for target in targets
                ],
            }, ensure_ascii=False, indent=2))
            return
        if args.command == "list-targets":
            targets = load_targets(phase2_conn, args.app_dossier_id)
            print(json.dumps({
                "app_dossier_id": args.app_dossier_id,
                "targets": [
                    {
                        "app_dossier_id": target.app_dossier_id,
                        "hektor_annonce_id": target.hektor_annonce_id,
                        "hektor_broadcast_id": target.hektor_broadcast_id,
                        "portal_key": target.portal_key,
                        "target_state": target.target_state,
                    }
                    for target in targets
                ],
            }, ensure_ascii=False, indent=2))
            return
        if args.command == "list-broadcasts":
            dossier = load_dossier(phase2_conn, args.app_dossier_id)
            annonce_id = str(dossier["hektor_annonce_id"])
            rows = hektor_conn.execute(
                """
                SELECT
                    ? AS app_dossier_id,
                    CAST(hektor_annonce_id AS INTEGER) AS hektor_annonce_id,
                    passerelle_key,
                    commercial_key,
                    commercial_id,
                    commercial_nom,
                    commercial_prenom,
                    current_state,
                    export_status,
                    is_success,
                    is_error,
                    synced_at AS refreshed_at
                FROM hektor_annonce_broadcast_state
                WHERE hektor_annonce_id = ?
                ORDER BY passerelle_key, hektor_broadcast_id
                """,
                (args.app_dossier_id, annonce_id),
            ).fetchall()
            print(json.dumps({
                "app_dossier_id": args.app_dossier_id,
                "broadcasts": [dict(row) for row in rows],
            }, ensure_ascii=False, indent=2))
            return
        if args.command == "apply-targets":
            result = apply_targets(
                phase2_conn=phase2_conn,
                hektor_conn=hektor_conn,
                app_dossier_id=args.app_dossier_id,
                requested_by=args.requested_by,
                dry_run=bool(args.dry_run),
                manage_diffusable=bool(args.ensure_diffusable),
            )
            if not bool(args.dry_run) and result.get("hektor_annonce_id"):
                result["refresh_single_annonce"] = refresh_single_annonce_local(str(result["hektor_annonce_id"]))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        if args.command == "accept-request":
            result = accept_request(
                phase2_conn=phase2_conn,
                hektor_conn=hektor_conn,
                app_dossier_id=args.app_dossier_id,
                requested_by=args.requested_by,
                dry_run=bool(args.dry_run),
            )
            if not bool(args.dry_run) and result.get("hektor_annonce_id"):
                result["refresh_single_annonce"] = refresh_single_annonce_local(str(result["hektor_annonce_id"]))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        if args.command == "set-validation":
            result = set_validation_for_dossier(
                phase2_conn=phase2_conn,
                app_dossier_id=args.app_dossier_id,
                state=int(args.state),
                dry_run=bool(args.dry_run),
            )
            if not bool(args.dry_run) and result.get("hektor_annonce_id"):
                result["refresh_single_annonce"] = refresh_single_annonce_local(str(result["hektor_annonce_id"]))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        if args.command == "set-diffusable":
            result = set_diffusable_for_dossier(
                phase2_conn=phase2_conn,
                app_dossier_id=args.app_dossier_id,
                diffusable=bool(int(args.state)),
                dry_run=bool(args.dry_run),
            )
            if not bool(args.dry_run) and result.get("hektor_annonce_id"):
                result["refresh_single_annonce"] = refresh_single_annonce_local(str(result["hektor_annonce_id"]))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        if args.command == "test-single-target":
            seed_single_target(
                phase2_conn=phase2_conn,
                app_dossier_id=args.app_dossier_id,
                hektor_broadcast_id=args.broadcast_id,
                portal_key=args.portal_key,
                requested_by=args.requested_by,
            )
            result = apply_targets(
                phase2_conn=phase2_conn,
                hektor_conn=hektor_conn,
                app_dossier_id=args.app_dossier_id,
                requested_by=args.requested_by,
                dry_run=bool(args.dry_run),
                manage_diffusable=bool(args.ensure_diffusable),
            )
            if not bool(args.dry_run) and result.get("hektor_annonce_id"):
                result["refresh_single_annonce"] = refresh_single_annonce_local(str(result["hektor_annonce_id"]))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        raise RuntimeError(f"Commande inconnue: {args.command}")
    finally:
        phase2_conn.close()
        hektor_conn.close()


if __name__ == "__main__":
    main()
