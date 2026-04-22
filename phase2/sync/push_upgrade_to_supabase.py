from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

try:
    from phase2.sync.export_app_payload import ANNONCES_SCOPE_WHERE, build_payload
except ModuleNotFoundError:
    import sys

    ROOT_DIR = Path(__file__).resolve().parents[2]
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from phase2.sync.export_app_payload import ANNONCES_SCOPE_WHERE, build_payload


ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ENV_FILE = ROOT / ".env"
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
DEFAULT_DOSSIER_BATCH_SIZE = 100
DEFAULT_DETAIL_BATCH_SIZE = 50
DEFAULT_WORK_ITEM_BATCH_SIZE = 100
DEFAULT_FILTER_BATCH_SIZE = 100
FETCH_PAGE_SIZE = 1000
DEFAULT_HTTP_TIMEOUT_SECONDS = 300
DEFAULT_HTTP_MAX_RETRIES = 4


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


def chunked(items: list[object], size: int) -> Iterable[list[object]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def stable_hash(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


def normalize_timestamp(value: object) -> str | None:
    text = str(value or "").strip()
    if not text or text.startswith("0000-00-00"):
        return None
    return text


def normalize_sqlite_timestamp(value: object) -> str | None:
    text = normalize_timestamp(value)
    if not text:
        return None
    return text[:19].replace("T", " ")


def normalize_bool(value: object) -> bool:
    return value in (True, 1, "1", "true")


def normalize_numeric(value: object) -> object:
    text = str(value or "").strip()
    if not text:
        return None
    return value


def normalize_row(row: dict[str, object], nullable_keys: tuple[str, ...]) -> dict[str, object]:
    normalized = dict(row)
    for key in nullable_keys:
        if normalized.get(key) == "":
            normalized[key] = None
    return normalized


DOSSIER_NULLABLE_KEYS = (
    "archive",
    "diffusable",
    "portails_resume",
    "offre_id",
    "offre_state",
    "offre_last_proposition_type",
    "compromis_id",
    "compromis_state",
    "vente_id",
    "numero_dossier",
    "numero_mandat",
    "mandat_source_id",
    "mandat_numero_reference",
    "ville",
    "type_bien",
    "prix",
    "adresse_privee_listing",
    "adresse_detail",
    "code_postal",
    "code_postal_prive_detail",
    "ville_privee_detail",
    "commercial_id",
    "commercial_nom",
    "negociateur_email",
    "agence_nom",
    "statut_annonce",
    "validation_diffusion_state",
    "mandat_type",
    "mandat_type_source",
    "mandat_date_debut",
    "mandat_date_fin",
    "mandat_montant",
    "mandants_texte",
    "etat_visibilite",
    "alerte_principale",
    "priority",
    "commentaire_resume",
    "date_relance_prevue",
    "dernier_event_type",
    "dernier_work_status",
)

WORK_ITEM_NULLABLE_KEYS = (
    "archive",
    "numero_dossier",
    "numero_mandat",
    "mandat_source_id",
    "mandat_numero_reference",
    "commercial_nom",
    "type_demande_label",
    "work_status",
    "internal_status",
    "priority",
    "validation_diffusion_state",
    "etat_visibilite",
    "motif_blocage",
    "next_action",
    "date_relance_prevue",
    "date_entree_file",
    "date_derniere_action",
    "age_jours",
)

MANDAT_REGISTER_NULLABLE_KEYS = (
    "app_dossier_id",
    "photo_url_listing",
    "images_preview_json",
    "adresse_privee_listing",
    "adresse_detail",
    "code_postal",
    "code_postal_prive_detail",
    "ville_privee_detail",
    "archive",
    "diffusable",
    "portails_resume",
    "numero_dossier",
    "numero_mandat",
    "register_sort_group",
    "register_sort_num",
    "titre_bien",
    "ville",
    "type_bien",
    "prix",
    "commercial_id",
    "commercial_nom",
    "negociateur_email",
    "agence_nom",
    "statut_annonce",
    "validation_diffusion_state",
    "mandat_source_id",
    "mandat_numero_reference",
    "mandat_type",
    "mandat_type_source",
    "mandat_date_debut",
    "mandat_date_fin",
    "mandat_montant",
    "mandants_texte",
    "mandat_note",
    "priority",
    "offre_id",
    "offre_state",
    "offre_last_proposition_type",
    "compromis_id",
    "compromis_state",
    "vente_id",
    "source_updated_at",
    "register_source_kind",
    "register_history_json",
    "register_avenants_json",
    "register_detail_payload_json",
)


class SupabaseRestClient:
    def __init__(self, *, base_url: str, service_role_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.service_role_key = service_role_key
        self.timeout_seconds = DEFAULT_HTTP_TIMEOUT_SECONDS
        self.max_retries = DEFAULT_HTTP_MAX_RETRIES

    def _request(
        self,
        *,
        method: str,
        path: str,
        payload: object | None = None,
        prefer: str | None = None,
        query: dict[str, str] | None = None,
    ) -> object | None:
        url = f"{self.base_url}/rest/v1/{path.lstrip('/')}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"

        body = None
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=True).encode("utf-8")

        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    raw = response.read().decode("utf-8")
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code in (500, 502, 503, 504) and attempt < self.max_retries:
                    last_error = RuntimeError(f"Supabase REST error {exc.code} on {path}: {detail}")
                    time.sleep(1.5 * attempt)
                    continue
                raise RuntimeError(f"Supabase REST error {exc.code} on {path}: {detail}") from exc
            except (TimeoutError, urllib.error.URLError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(1.5 * attempt)
        raise RuntimeError(f"Supabase REST timeout/network error on {path}: {last_error}") from last_error

    def fetch_all_rows(self, *, path: str, select: str, order: str) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        offset = 0
        while True:
            batch = self._request(
                method="GET",
                path=path,
                query={
                    "select": select,
                    "order": order,
                    "limit": str(FETCH_PAGE_SIZE),
                    "offset": str(offset),
                },
            )
            if not isinstance(batch, list) or not batch:
                break
            rows.extend(batch)
            if len(batch) < FETCH_PAGE_SIZE:
                break
            offset += FETCH_PAGE_SIZE
        return rows

    def fetch_first_row(self, *, path: str, select: str, order: str) -> dict[str, object] | None:
        rows = self._request(
            method="GET",
            path=path,
            query={
                "select": select,
                "order": order,
                "limit": "1",
            },
        )
        if isinstance(rows, list) and rows:
            return rows[0]
        return None

    def fetch_rows_by_ids(self, *, path: str, select: str, id_column: str, ids: list[int], order: str) -> list[dict[str, object]]:
        if not ids:
            return []
        rows: list[dict[str, object]] = []
        for batch in chunked(ids, 500):
            id_list = ",".join(str(int(value)) for value in batch)
            batch_rows = self._request(
                method="GET",
                path=path,
                query={
                    "select": select,
                    id_column: f"in.({id_list})",
                    "order": order,
                },
            )
            if isinstance(batch_rows, list):
                rows.extend(batch_rows)
        return rows

    def fetch_latest_completed_delta_run(self) -> dict[str, object] | None:
        rows = self._request(
            method="GET",
            path="app_delta_run",
            query={
                "select": "id,started_at,finished_at,notes",
                "scope": "eq.annonces_current",
                "status": "eq.completed",
                "order": "started_at.desc",
                "limit": "1",
            },
        )
        if isinstance(rows, list) and rows:
            return rows[0]
        return None

    def insert_delta_run(self, *, mode: str, notes: dict[str, object]) -> str:
        run_id = str(uuid.uuid4())
        self._request(
            method="POST",
            path="app_delta_run",
            payload=[{"id": run_id, "mode": mode, "scope": "annonces_current", "status": "running", "notes": notes}],
            prefer="return=representation",
        )
        return run_id

    def update_delta_run(self, run_id: str, payload: dict[str, object]) -> None:
        self._request(
            method="PATCH",
            path="app_delta_run",
            payload=payload,
            query={"id": f"eq.{run_id}"},
        )

    def upsert_rows(self, *, path: str, rows: list[dict[str, object]], batch_size: int) -> None:
        for batch in chunked(rows, batch_size):
            self._request(method="POST", path=path, payload=batch, prefer="resolution=merge-duplicates")

    def insert_rows(self, *, path: str, rows: list[dict[str, object]], batch_size: int) -> None:
        for batch in chunked(rows, batch_size):
            self._request(method="POST", path=path, payload=batch)

    def delete_all_rows(self, *, path: str, filter_expr: str) -> None:
        self._request(method="DELETE", path=f"{path}?{filter_expr}")

    def delete_rows_by_ids(self, *, path: str, column: str, ids: list[int], chunk_size: int = 500) -> None:
        for batch in chunked(ids, chunk_size):
            id_list = ",".join(str(int(value)) for value in batch)
            self._request(method="DELETE", path=f"{path}?{column}=in.({id_list})")


def build_current_dossiers(dossiers: list[dict[str, object]]) -> list[dict[str, object]]:
    rows_by_id: dict[int, dict[str, object]] = {}
    for row in dossiers:
        normalized = normalize_row(row, DOSSIER_NULLABLE_KEYS)
        source_updated_at = normalize_timestamp(normalized.get("date_maj") or normalized.get("date_enregistrement_annonce"))
        current_row = {
            "app_dossier_id": normalized["app_dossier_id"],
            "hektor_annonce_id": normalized["hektor_annonce_id"],
            "archive": normalized.get("archive"),
            "diffusable": normalized.get("diffusable"),
            "adresse_privee_listing": normalized.get("adresse_privee_listing"),
            "adresse_detail": normalized.get("adresse_detail"),
            "code_postal": normalized.get("code_postal"),
            "code_postal_prive_detail": normalized.get("code_postal_prive_detail"),
            "ville_privee_detail": normalized.get("ville_privee_detail"),
            "nb_portails_actifs": int(normalized.get("nb_portails_actifs") or 0),
            "has_diffusion_error": normalize_bool(normalized.get("has_diffusion_error")),
            "portails_resume": normalized.get("portails_resume"),
            "offre_id": normalized.get("offre_id"),
            "offre_state": normalized.get("offre_state"),
            "offre_last_proposition_type": normalized.get("offre_last_proposition_type"),
            "compromis_id": normalized.get("compromis_id"),
            "compromis_state": normalized.get("compromis_state"),
            "vente_id": normalized.get("vente_id"),
            "numero_dossier": normalized.get("numero_dossier"),
            "numero_mandat": normalized.get("numero_mandat"),
            "titre_bien": normalized["titre_bien"],
            "ville": normalized.get("ville"),
            "type_bien": normalized.get("type_bien"),
            "prix": normalize_numeric(normalized.get("prix")),
            "commercial_id": normalized.get("commercial_id"),
            "commercial_nom": normalized.get("commercial_nom"),
            "negociateur_email": normalized.get("negociateur_email"),
            "agence_nom": normalized.get("agence_nom"),
            "photo_url_listing": normalized.get("photo_url_listing"),
            "images_preview_json": normalized.get("images_preview_json"),
            "statut_annonce": normalized.get("statut_annonce"),
            "validation_diffusion_state": normalized.get("validation_diffusion_state"),
            "mandat_type": normalized.get("mandat_type"),
            "mandat_type_source": normalized.get("mandat_type_source"),
            "mandat_date_debut": normalized.get("mandat_date_debut"),
            "mandat_date_fin": normalized.get("mandat_date_fin"),
            "mandat_montant": normalize_numeric(normalized.get("mandat_montant")),
            "mandants_texte": normalized.get("mandants_texte"),
            "etat_visibilite": normalized.get("etat_visibilite"),
            "alerte_principale": normalized.get("alerte_principale"),
            "priority": normalized.get("priority"),
            "has_open_blocker": bool(normalized.get("has_open_blocker")),
            "commentaire_resume": normalized.get("commentaire_resume"),
            "date_relance_prevue": normalized.get("date_relance_prevue"),
            "dernier_event_type": normalized.get("dernier_event_type"),
            "dernier_work_status": normalized.get("dernier_work_status"),
            "source_updated_at": source_updated_at,
        }
        current_row["source_hash"] = stable_hash(current_row)
        rows_by_id[int(current_row["app_dossier_id"])] = current_row
    return list(rows_by_id.values())


def build_current_details(dossier_details: list[dict[str, object]], source_updated_at_by_id: dict[int, str | None]) -> list[dict[str, object]]:
    rows_by_id: dict[int, dict[str, object]] = {}
    for row in dossier_details:
        current_row = {
            "app_dossier_id": row["app_dossier_id"],
            "hektor_annonce_id": row["hektor_annonce_id"],
            "source_updated_at": source_updated_at_by_id.get(int(row["app_dossier_id"])),
            "detail_payload_json": row["detail_payload_json"],
        }
        current_row["source_hash"] = stable_hash(current_row)
        rows_by_id[int(current_row["app_dossier_id"])] = current_row
    return list(rows_by_id.values())


def build_current_work_items(work_items: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in work_items:
        normalized = normalize_row(row, WORK_ITEM_NULLABLE_KEYS)
        current_row = {
            "app_dossier_id": normalized["app_dossier_id"],
            "hektor_annonce_id": normalized["hektor_annonce_id"],
            "archive": normalized.get("archive"),
            "numero_dossier": normalized.get("numero_dossier"),
            "numero_mandat": normalized.get("numero_mandat"),
            "titre_bien": normalized["titre_bien"],
            "commercial_nom": normalized.get("commercial_nom"),
            "type_demande_label": normalized.get("type_demande_label"),
            "work_status": normalized.get("work_status"),
            "internal_status": normalized.get("internal_status"),
            "priority": normalized.get("priority"),
            "validation_diffusion_state": normalized.get("validation_diffusion_state"),
            "etat_visibilite": normalized.get("etat_visibilite"),
            "motif_blocage": normalized.get("motif_blocage"),
            "has_open_blocker": bool(normalized.get("has_open_blocker")),
            "next_action": normalized.get("next_action"),
            "date_relance_prevue": normalized.get("date_relance_prevue"),
            "date_entree_file": normalized.get("date_entree_file"),
            "date_derniere_action": normalized.get("date_derniere_action"),
            "age_jours": normalized.get("age_jours"),
        }
        current_row["source_hash"] = stable_hash(current_row)
        rows.append(current_row)
    return rows


def build_current_filter_catalog(filter_catalog: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in filter_catalog:
        current_row = {
            "filter_type": row["filter_type"],
            "filter_value": row["filter_value"],
            "sort_order": row["sort_order"],
        }
        current_row["source_hash"] = stable_hash(current_row)
        rows.append(current_row)
    return rows


def build_current_mandat_register_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    current_rows: list[dict[str, object]] = []
    for row in rows:
        normalized = normalize_row(row, MANDAT_REGISTER_NULLABLE_KEYS)
        current_row = {
            "register_row_id": normalized["register_row_id"],
            "app_dossier_id": normalized.get("app_dossier_id"),
            "hektor_annonce_id": normalized["hektor_annonce_id"],
            "photo_url_listing": normalized.get("photo_url_listing"),
            "images_preview_json": normalized.get("images_preview_json"),
            "adresse_privee_listing": normalized.get("adresse_privee_listing"),
            "adresse_detail": normalized.get("adresse_detail"),
            "code_postal": normalized.get("code_postal"),
            "code_postal_prive_detail": normalized.get("code_postal_prive_detail"),
            "ville_privee_detail": normalized.get("ville_privee_detail"),
            "archive": normalized.get("archive"),
            "diffusable": normalized.get("diffusable"),
            "nb_portails_actifs": int(normalized.get("nb_portails_actifs") or 0),
            "has_diffusion_error": normalize_bool(normalized.get("has_diffusion_error")),
            "portails_resume": normalized.get("portails_resume"),
            "numero_dossier": normalized.get("numero_dossier"),
            "numero_mandat": normalized.get("numero_mandat"),
            "register_sort_group": int(normalized.get("register_sort_group") or 1),
            "register_sort_num": int(normalized.get("register_sort_num") or 0),
            "titre_bien": normalized.get("titre_bien"),
            "ville": normalized.get("ville"),
            "type_bien": normalized.get("type_bien"),
            "prix": normalize_numeric(normalized.get("prix")),
            "commercial_id": normalized.get("commercial_id"),
            "commercial_nom": normalized.get("commercial_nom"),
            "negociateur_email": normalized.get("negociateur_email"),
            "agence_nom": normalized.get("agence_nom"),
            "statut_annonce": normalized.get("statut_annonce"),
            "validation_diffusion_state": normalized.get("validation_diffusion_state"),
            "mandat_source_id": normalized.get("mandat_source_id"),
            "mandat_numero_reference": normalized.get("mandat_numero_reference"),
            "mandat_type": normalized.get("mandat_type"),
            "mandat_type_source": normalized.get("mandat_type_source"),
            "mandat_date_debut": normalized.get("mandat_date_debut"),
            "mandat_date_fin": normalized.get("mandat_date_fin"),
            "mandat_montant": normalize_numeric(normalized.get("mandat_montant")),
            "mandants_texte": normalized.get("mandants_texte"),
            "mandat_note": normalized.get("mandat_note"),
            "priority": normalized.get("priority"),
            "offre_id": normalized.get("offre_id"),
            "offre_state": normalized.get("offre_state"),
            "offre_last_proposition_type": normalized.get("offre_last_proposition_type"),
            "compromis_id": normalized.get("compromis_id"),
            "compromis_state": normalized.get("compromis_state"),
            "vente_id": normalized.get("vente_id"),
            "source_updated_at": normalize_timestamp(normalized.get("source_updated_at")),
            "register_source_kind": normalized.get("register_source_kind"),
            "register_detail_available": normalize_bool(normalized.get("register_detail_available")),
            "register_version_count": int(normalized.get("register_version_count") or 0),
            "register_embedded_avenant_count": int(normalized.get("register_embedded_avenant_count") or 0),
            "register_history_json": normalized.get("register_history_json"),
            "register_avenants_json": normalized.get("register_avenants_json"),
            "register_detail_payload_json": normalized.get("register_detail_payload_json"),
        }
        current_row["source_hash"] = stable_hash(current_row)
        current_rows.append(current_row)
    return current_rows


def normalize_broadcast_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized_by_key: dict[tuple[int, str, str], dict[str, object]] = {}
    for row in rows:
        normalized_row = {
            "app_dossier_id": int(row["app_dossier_id"]),
            "hektor_annonce_id": int(row["hektor_annonce_id"]),
            "passerelle_key": str(row.get("passerelle_key") or ""),
            "commercial_key": str(row.get("commercial_key") or ""),
            "commercial_id": row.get("commercial_id"),
            "commercial_nom": row.get("commercial_nom"),
            "commercial_prenom": row.get("commercial_prenom"),
            "current_state": row.get("current_state"),
            "export_status": row.get("export_status"),
            "is_success": normalize_bool(row.get("is_success")),
            "is_error": normalize_bool(row.get("is_error")),
        }
        dedupe_key = (
            int(normalized_row["app_dossier_id"]),
            str(normalized_row["passerelle_key"]),
            str(normalized_row["commercial_key"]),
        )
        normalized_by_key[dedupe_key] = normalized_row
    return list(normalized_by_key.values())


def map_hashes(rows: list[dict[str, object]], *, id_key: str) -> dict[int, str]:
    return {int(row[id_key]): str(row["source_hash"]) for row in rows}


def grouped_work_hashes(rows: list[dict[str, object]]) -> dict[int, list[str]]:
    grouped: dict[int, list[str]] = defaultdict(list)
    for row in rows:
        grouped[int(row["app_dossier_id"])].append(str(row["source_hash"]))
    return {key: sorted(values) for key, values in grouped.items()}


def fetch_local_app_dossier_ids() -> list[int]:
    con = sqlite3.connect(PHASE2_DB)
    try:
        rows = con.execute(
            f"""
            SELECT app_dossier_id
            FROM app_view_generale
            WHERE {ANNONCES_SCOPE_WHERE}
            ORDER BY app_dossier_id
            """
        ).fetchall()
        return [int(row[0]) for row in rows]
    finally:
        con.close()


def fetch_source_watermark() -> str | None:
    con = sqlite3.connect(PHASE2_DB)
    try:
        con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
        queries = [
            "SELECT MAX(REPLACE(SUBSTR(COALESCE(date_maj, synced_at), 1, 19), 'T', ' ')) FROM hektor.hektor_annonce",
            "SELECT MAX(REPLACE(SUBSTR(synced_at, 1, 19), 'T', ' ')) FROM hektor.hektor_annonce_detail",
            "SELECT MAX(REPLACE(SUBSTR(synced_at, 1, 19), 'T', ' ')) FROM hektor.hektor_mandat",
            "SELECT MAX(REPLACE(SUBSTR(synced_at, 1, 19), 'T', ' ')) FROM hektor.hektor_offre",
            "SELECT MAX(REPLACE(SUBSTR(synced_at, 1, 19), 'T', ' ')) FROM hektor.hektor_compromis",
            "SELECT MAX(REPLACE(SUBSTR(synced_at, 1, 19), 'T', ' ')) FROM hektor.hektor_vente",
            "SELECT MAX(REPLACE(SUBSTR(synced_at, 1, 19), 'T', ' ')) FROM hektor.hektor_annonce_broadcast_state",
            "SELECT MAX(REPLACE(SUBSTR(created_at, 1, 19), 'T', ' ')) FROM app_note",
            "SELECT MAX(REPLACE(SUBSTR(COALESCE(done_at, created_at), 1, 19), 'T', ' ')) FROM app_followup",
            "SELECT MAX(REPLACE(SUBSTR(COALESCE(resolved_at, detected_at), 1, 19), 'T', ' ')) FROM app_blocker",
        ]
        watermarks = [normalize_sqlite_timestamp(con.execute(sql).fetchone()[0]) for sql in queries]
        cleaned = [value for value in watermarks if value]
        return max(cleaned) if cleaned else None
    finally:
        con.close()


def detect_candidate_dossier_ids(*, since: str) -> list[int]:
    con = sqlite3.connect(PHASE2_DB)
    try:
        con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
        sql = """
        WITH changed_annonce_ids AS (
            SELECT DISTINCT CAST(hektor_annonce_id AS INTEGER) AS hektor_annonce_id
            FROM hektor.hektor_annonce
            WHERE hektor_annonce_id IS NOT NULL
              AND REPLACE(SUBSTR(COALESCE(date_maj, synced_at), 1, 19), 'T', ' ') > ?
            UNION
            SELECT DISTINCT CAST(hektor_annonce_id AS INTEGER)
            FROM hektor.hektor_annonce_detail
            WHERE hektor_annonce_id IS NOT NULL
              AND REPLACE(SUBSTR(synced_at, 1, 19), 'T', ' ') > ?
            UNION
            SELECT DISTINCT CAST(hektor_annonce_id AS INTEGER)
            FROM hektor.hektor_mandat
            WHERE hektor_annonce_id IS NOT NULL
              AND REPLACE(SUBSTR(synced_at, 1, 19), 'T', ' ') > ?
            UNION
            SELECT DISTINCT CAST(hektor_annonce_id AS INTEGER)
            FROM hektor.hektor_offre
            WHERE hektor_annonce_id IS NOT NULL
              AND REPLACE(SUBSTR(synced_at, 1, 19), 'T', ' ') > ?
            UNION
            SELECT DISTINCT CAST(hektor_annonce_id AS INTEGER)
            FROM hektor.hektor_compromis
            WHERE hektor_annonce_id IS NOT NULL
              AND REPLACE(SUBSTR(synced_at, 1, 19), 'T', ' ') > ?
            UNION
            SELECT DISTINCT CAST(hektor_annonce_id AS INTEGER)
            FROM hektor.hektor_vente
            WHERE hektor_annonce_id IS NOT NULL
              AND REPLACE(SUBSTR(synced_at, 1, 19), 'T', ' ') > ?
            UNION
            SELECT DISTINCT CAST(hektor_annonce_id AS INTEGER)
            FROM hektor.hektor_annonce_broadcast_state
            WHERE hektor_annonce_id IS NOT NULL
              AND REPLACE(SUBSTR(synced_at, 1, 19), 'T', ' ') > ?
        ),
        changed_dossiers AS (
            SELECT d.id AS app_dossier_id
            FROM app_dossier d
            INNER JOIN changed_annonce_ids a ON a.hektor_annonce_id = d.hektor_annonce_id
            UNION
            SELECT app_dossier_id
            FROM app_note
            WHERE REPLACE(SUBSTR(created_at, 1, 19), 'T', ' ') > ?
            UNION
            SELECT app_dossier_id
            FROM app_followup
            WHERE REPLACE(SUBSTR(COALESCE(done_at, created_at), 1, 19), 'T', ' ') > ?
            UNION
            SELECT app_dossier_id
            FROM app_blocker
            WHERE REPLACE(SUBSTR(COALESCE(resolved_at, detected_at), 1, 19), 'T', ' ') > ?
        )
        SELECT DISTINCT app_dossier_id
        FROM changed_dossiers
        WHERE app_dossier_id IS NOT NULL
        ORDER BY app_dossier_id
        """
        params = (since,) * 10
        rows = con.execute(sql, params).fetchall()
        return [int(row[0]) for row in rows]
    finally:
        con.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--dossier-batch-size", type=int, default=DEFAULT_DOSSIER_BATCH_SIZE)
    parser.add_argument("--detail-batch-size", type=int, default=DEFAULT_DETAIL_BATCH_SIZE)
    parser.add_argument("--work-item-batch-size", type=int, default=DEFAULT_WORK_ITEM_BATCH_SIZE)
    parser.add_argument("--filter-batch-size", type=int, default=DEFAULT_FILTER_BATCH_SIZE)
    parser.add_argument("--full-rebuild", action="store_true")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    args = parse_args()
    load_env_file(args.env_file)

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    client = SupabaseRestClient(base_url=supabase_url, service_role_key=supabase_service_role_key)
    source_watermark = fetch_source_watermark()
    latest_completed_run = client.fetch_latest_completed_delta_run()
    latest_notes = latest_completed_run.get("notes") if latest_completed_run else None
    latest_source_watermark = None
    if isinstance(latest_notes, dict):
        latest_source_watermark = normalize_sqlite_timestamp(latest_notes.get("source_watermark"))

    local_ids = set(fetch_local_app_dossier_ids())
    remote_dossiers = client.fetch_all_rows(path="app_dossier_current", select="app_dossier_id", order="app_dossier_id.asc")
    remote_ids = {int(row["app_dossier_id"]) for row in remote_dossiers if row.get("app_dossier_id") is not None}
    remote_has_rows = bool(remote_ids)
    stale_ids: list[int] = []
    baseline_adopted = False

    if args.full_rebuild:
        candidate_ids = sorted(local_ids)
        stale_ids = sorted(remote_ids - local_ids)
    elif latest_source_watermark is None and remote_has_rows:
        candidate_ids = []
        stale_ids = sorted(remote_ids - local_ids)
        baseline_adopted = True
    elif latest_source_watermark:
        candidate_ids = detect_candidate_dossier_ids(since=latest_source_watermark)
        stale_ids = sorted(remote_ids - local_ids)
    else:
        candidate_ids = sorted(local_ids)
        stale_ids = sorted(remote_ids - local_ids)

    payload = build_payload(limit=None, dossier_ids=candidate_ids, include_filter_catalog=False)
    current_dossiers = build_current_dossiers(payload["dossiers"])
    source_updated_at_by_id = {int(row["app_dossier_id"]): row.get("source_updated_at") for row in current_dossiers}
    current_details = build_current_details(payload["dossier_details"], source_updated_at_by_id)
    current_work_items = build_current_work_items(payload["work_items"])
    current_mandat_register_rows = build_current_mandat_register_rows(payload.get("mandat_register_rows", []))
    current_broadcasts = normalize_broadcast_rows(payload.get("broadcasts", []))

    dossier_upsert_ids = sorted({int(row["app_dossier_id"]) for row in current_dossiers})
    detail_upsert_ids = sorted({int(row["app_dossier_id"]) for row in current_details})
    local_work_hashes = grouped_work_hashes(current_work_items)
    work_candidate_ids = sorted({int(row["app_dossier_id"]) for row in current_work_items})
    broadcast_candidate_ids = sorted({int(row["app_dossier_id"]) for row in current_broadcasts})

    current_filter_catalog: list[dict[str, object]] = []
    filters_should_refresh = (
        args.full_rebuild
        or bool(candidate_ids)
        or bool(stale_ids)
        or (latest_completed_run is None and not baseline_adopted)
    )

    delta_run_id = client.insert_delta_run(
        mode="upgrade",
        notes={
            "generated_from": "phase2/sync/push_upgrade_to_supabase.py",
            "full_rebuild": args.full_rebuild,
            "baseline_adopted": baseline_adopted,
            "source_watermark": source_watermark,
            "previous_source_watermark": latest_source_watermark,
            "candidate_count": len(candidate_ids),
        },
    )

    try:
        remote_dossier_hashes = {
            int(row["app_dossier_id"]): str(row["source_hash"])
            for row in client.fetch_rows_by_ids(
                path="app_dossier_current",
                select="app_dossier_id,source_hash",
                id_column="app_dossier_id",
                ids=dossier_upsert_ids,
                order="app_dossier_id.asc",
            )
        }
        remote_detail_hashes = {
            int(row["app_dossier_id"]): str(row["source_hash"])
            for row in client.fetch_rows_by_ids(
                path="app_dossier_detail_current",
                select="app_dossier_id,source_hash",
                id_column="app_dossier_id",
                ids=detail_upsert_ids,
                order="app_dossier_id.asc",
            )
        }
        remote_work_hashes = grouped_work_hashes(
            client.fetch_rows_by_ids(
                path="app_work_item_current",
                select="app_dossier_id,source_hash",
                id_column="app_dossier_id",
                ids=sorted(set(candidate_ids) | set(work_candidate_ids)),
                order="app_dossier_id.asc",
            )
        )
        remote_broadcast_rows = client.fetch_rows_by_ids(
            path="app_mandat_broadcast_current",
            select="app_dossier_id,passerelle_key,commercial_key",
            id_column="app_dossier_id",
            ids=sorted(set(candidate_ids) | set(stale_ids) | set(broadcast_candidate_ids)),
            order="app_dossier_id.asc",
        )

        local_dossier_hashes = map_hashes(current_dossiers, id_key="app_dossier_id")
        local_detail_hashes = map_hashes(current_details, id_key="app_dossier_id")

        if args.full_rebuild:
            dossier_upsert_ids = sorted(local_dossier_hashes)
            detail_upsert_ids = sorted(local_detail_hashes)
            work_replace_ids = sorted(set(work_candidate_ids) | set(remote_work_hashes))
        else:
            dossier_upsert_ids = sorted(
                app_dossier_id
                for app_dossier_id, source_hash in local_dossier_hashes.items()
                if remote_dossier_hashes.get(app_dossier_id) != source_hash
            )
            detail_upsert_ids = sorted(
                app_dossier_id
                for app_dossier_id, source_hash in local_detail_hashes.items()
                if remote_detail_hashes.get(app_dossier_id) != source_hash
            )
            work_replace_ids = sorted(
                app_dossier_id
                for app_dossier_id in (set(candidate_ids) | set(local_work_hashes) | set(remote_work_hashes))
                if local_work_hashes.get(app_dossier_id, []) != remote_work_hashes.get(app_dossier_id, [])
            )
        remote_broadcast_keys = {
            (int(row["app_dossier_id"]), str(row["passerelle_key"] or ""), str(row.get("commercial_key") or ""))
            for row in remote_broadcast_rows
            if row.get("app_dossier_id") is not None and row.get("passerelle_key") is not None
        }
        local_broadcast_keys = {
            (int(row["app_dossier_id"]), str(row["passerelle_key"] or ""), str(row.get("commercial_key") or ""))
            for row in current_broadcasts
        }
        if args.full_rebuild:
            broadcast_replace_ids = sorted(set(broadcast_candidate_ids) | {key[0] for key in remote_broadcast_keys})
        else:
            broadcast_replace_ids = sorted({key[0] for key in (remote_broadcast_keys ^ local_broadcast_keys)})

        if stale_ids:
            client.delete_rows_by_ids(path="app_dossier_current", column="app_dossier_id", ids=stale_ids)
            client.delete_rows_by_ids(path="app_dossier_detail_current", column="app_dossier_id", ids=stale_ids)
            client.delete_rows_by_ids(path="app_work_item_current", column="app_dossier_id", ids=stale_ids)
            client.delete_rows_by_ids(path="app_mandat_broadcast_current", column="app_dossier_id", ids=stale_ids)

        if dossier_upsert_ids:
            client.upsert_rows(
                path="app_dossier_current",
                rows=[row for row in current_dossiers if int(row["app_dossier_id"]) in set(dossier_upsert_ids)],
                batch_size=args.dossier_batch_size,
            )

        if detail_upsert_ids:
            client.upsert_rows(
                path="app_dossier_detail_current",
                rows=[row for row in current_details if int(row["app_dossier_id"]) in set(detail_upsert_ids)],
                batch_size=args.detail_batch_size,
            )

        if work_replace_ids:
            client.delete_rows_by_ids(path="app_work_item_current", column="app_dossier_id", ids=work_replace_ids)
            work_rows = [row for row in current_work_items if int(row["app_dossier_id"]) in set(work_replace_ids)]
            if work_rows:
                client.insert_rows(path="app_work_item_current", rows=work_rows, batch_size=args.work_item_batch_size)

        if broadcast_replace_ids:
            client.delete_rows_by_ids(path="app_mandat_broadcast_current", column="app_dossier_id", ids=broadcast_replace_ids)
            broadcast_rows = [row for row in current_broadcasts if int(row["app_dossier_id"]) in set(broadcast_replace_ids)]
            if broadcast_rows:
                client.insert_rows(path="app_mandat_broadcast_current", rows=broadcast_rows, batch_size=args.work_item_batch_size)

        if filters_should_refresh:
            current_filter_catalog = build_current_filter_catalog(build_payload(limit=0)["filter_catalog"])
            client.delete_all_rows(path="app_filter_catalog_current_store", filter_expr="filter_type=not.is.null")
            if current_filter_catalog:
                client.insert_rows(path="app_filter_catalog_current_store", rows=current_filter_catalog, batch_size=args.filter_batch_size)

        client.delete_all_rows(path="app_mandat_register_current", filter_expr="register_row_id=not.is.null")
        if current_mandat_register_rows:
            client.insert_rows(
                path="app_mandat_register_current",
                rows=current_mandat_register_rows,
                batch_size=args.work_item_batch_size,
            )

        client.update_delta_run(
            delta_run_id,
            {
                "status": "completed",
                    "finished_at": now_iso(),
                    "dossiers_detected": len(set(candidate_ids) | set(stale_ids)),
                    "dossiers_upserted": len(dossier_upsert_ids),
                    "details_upserted": len(detail_upsert_ids),
                    "work_items_replaced": len(work_replace_ids),
                    "filters_replaced": len(current_filter_catalog),
                    "deleted_dossiers": len(stale_ids),
                },
            )

        print(
            json.dumps(
                {
                    "delta_run_id": delta_run_id,
                    "dossiers_detected": len(set(dossier_upsert_ids) | set(detail_upsert_ids) | set(work_replace_ids)),
                    "dossiers_upserted": len(dossier_upsert_ids),
                    "details_upserted": len(detail_upsert_ids),
                    "work_items_replaced": len(work_replace_ids),
                    "filters_replaced": len(current_filter_catalog),
                    "mandat_register_replaced": len(current_mandat_register_rows),
                    "deleted_dossiers": len(stale_ids),
                    "mode": "full_rebuild" if args.full_rebuild else "upgrade",
                    "baseline_adopted": baseline_adopted,
                },
                ensure_ascii=True,
                indent=2,
            )
        )
    except Exception as exc:
        client.update_delta_run(
            delta_run_id,
            {
                "status": "failed",
                "finished_at": now_iso(),
                "notes": {"error": str(exc)},
            },
        )
        raise


if __name__ == "__main__":
    main()
