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
    from phase2.sync.export_app_payload import (
        ANNONCES_SCOPE_WHERE,
        attach_hektor_read,
        build_archive_annonce_index,
        build_historical_annonce_index,
        build_payload,
        sqlite_read_connection,
    )
except ModuleNotFoundError:
    import sys

    ROOT_DIR = Path(__file__).resolve().parents[2]
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from phase2.sync.export_app_payload import (
        ANNONCES_SCOPE_WHERE,
        attach_hektor_read,
        build_archive_annonce_index,
        build_historical_annonce_index,
        build_payload,
        sqlite_read_connection,
    )


ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ENV_FILE = ROOT / ".env"
APP_ENV_FILE = ROOT / "apps" / "hektor-v1" / ".env"
DEFAULT_ENV_FILES = (DEFAULT_ENV_FILE, APP_ENV_FILE)
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


def load_env_files(paths: Iterable[Path]) -> None:
    seen: set[str] = set()
    for path in paths:
        path_key = str(path)
        if path_key in seen:
            continue
        seen.add(path_key)
        load_env_file(path)


def chunked(items: list[object], size: int) -> Iterable[list[object]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def stable_hash(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


def stable_upload_hash(row: dict[str, object]) -> str:
    return stable_hash({key: value for key, value in row.items() if key != "search_text"})


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


def build_search_text(row: dict[str, object]) -> str | None:
    parts = [
        row.get("numero_dossier"),
        row.get("numero_mandat"),
        row.get("titre_bien"),
        row.get("ville"),
        row.get("code_postal"),
        row.get("commercial_nom"),
        row.get("agence_nom"),
        row.get("mandants_texte"),
    ]
    text = " ".join(str(part).strip() for part in parts if str(part or "").strip())
    return " ".join(text.split()) or None


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
    "price_change_event_count",
    "price_change_last_source_kind",
    "price_change_last_old_value",
    "price_change_last_new_value",
    "price_change_last_detected_at",
    "price_change_last_source_updated_at",
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
    "price_change_event_count",
    "price_change_last_source_kind",
    "price_change_last_old_value",
    "price_change_last_new_value",
    "price_change_last_detected_at",
    "price_change_last_source_updated_at",
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

ARCHIVE_INDEX_NULLABLE_KEYS = (
    "numero_dossier",
    "numero_mandat",
    "titre_bien",
    "ville",
    "code_postal",
    "type_bien",
    "prix",
    "commercial_id",
    "commercial_nom",
    "negociateur_email",
    "agence_nom",
    "statut_annonce",
    "archive",
    "diffusable",
    "date_maj",
    "mandat_type",
    "mandat_date_debut",
    "mandat_date_fin",
    "mandat_montant",
    "mandants_texte",
    "local_detail_updated_at",
    "photo_url_listing",
)

HISTORICAL_INDEX_NULLABLE_KEYS = (
    "numero_dossier",
    "numero_mandat",
    "titre_bien",
    "ville",
    "code_postal",
    "type_bien",
    "prix",
    "commercial_id",
    "commercial_nom",
    "negociateur_email",
    "agence_nom",
    "statut_annonce",
    "archive",
    "diffusable",
    "date_maj",
    "mandat_type",
    "mandat_date_debut",
    "mandat_date_fin",
    "mandat_montant",
    "mandants_texte",
    "local_detail_updated_at",
    "photo_url_listing",
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

    def table_available(self, path: str) -> bool:
        try:
            self._request(method="GET", path=path, query={"select": "*", "limit": "1"})
            return True
        except RuntimeError as exc:
            message = str(exc)
            if "PGRST205" in message or "Could not find the table" in message or "404" in message:
                return False
            raise


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
            "search_text": None,
            "price_change_event_count": int(normalized.get("price_change_event_count") or 0),
            "price_change_last_source_kind": normalized.get("price_change_last_source_kind"),
            "price_change_last_old_value": normalize_numeric(normalized.get("price_change_last_old_value")),
            "price_change_last_new_value": normalize_numeric(normalized.get("price_change_last_new_value")),
            "price_change_last_detected_at": normalized.get("price_change_last_detected_at"),
            "price_change_last_source_updated_at": normalized.get("price_change_last_source_updated_at"),
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
        current_row["search_text"] = build_search_text(current_row)
        current_row["source_hash"] = stable_upload_hash(current_row)
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
            "register_sort_group": int(normalized.get("register_sort_group") if normalized.get("register_sort_group") is not None else 1),
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
            "price_change_event_count": int(normalized.get("price_change_event_count") or 0),
            "price_change_last_source_kind": normalized.get("price_change_last_source_kind"),
            "price_change_last_old_value": normalize_numeric(normalized.get("price_change_last_old_value")),
            "price_change_last_new_value": normalize_numeric(normalized.get("price_change_last_new_value")),
            "price_change_last_detected_at": normalized.get("price_change_last_detected_at"),
            "price_change_last_source_updated_at": normalized.get("price_change_last_source_updated_at"),
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


def build_current_archive_index_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    current_rows: list[dict[str, object]] = []
    for row in rows:
        normalized = normalize_row(row, ARCHIVE_INDEX_NULLABLE_KEYS)
        hektor_annonce_id = normalized.get("hektor_annonce_id")
        if hektor_annonce_id is None:
            continue
        current_row = {
            "hektor_annonce_id": int(hektor_annonce_id),
            "app_archive_id": int(normalized.get("app_archive_id") or hektor_annonce_id),
            "numero_dossier": normalized.get("numero_dossier"),
            "numero_mandat": normalized.get("numero_mandat"),
            "titre_bien": normalized.get("titre_bien") or "[Sans titre]",
            "ville": normalized.get("ville"),
            "code_postal": normalized.get("code_postal"),
            "type_bien": normalized.get("type_bien"),
            "prix": normalize_numeric(normalized.get("prix")),
            "commercial_id": normalized.get("commercial_id"),
            "commercial_nom": normalized.get("commercial_nom"),
            "negociateur_email": normalized.get("negociateur_email"),
            "agence_nom": normalized.get("agence_nom"),
            "statut_annonce": normalized.get("statut_annonce"),
            "archive": normalized.get("archive") or "1",
            "diffusable": normalized.get("diffusable"),
            "date_maj": normalize_timestamp(normalized.get("date_maj")),
            "mandat_type": normalized.get("mandat_type"),
            "mandat_date_debut": normalized.get("mandat_date_debut"),
            "mandat_date_fin": normalized.get("mandat_date_fin"),
            "mandat_montant": normalize_numeric(normalized.get("mandat_montant")),
            "mandants_texte": normalized.get("mandants_texte"),
            "search_text": None,
            "has_local_detail": normalize_bool(normalized.get("has_local_detail")),
            "local_detail_updated_at": normalize_timestamp(normalized.get("local_detail_updated_at")),
            "photo_url_listing": normalized.get("photo_url_listing"),
        }
        current_row["search_text"] = build_search_text(current_row)
        current_row["source_updated_at"] = current_row["date_maj"] or current_row["local_detail_updated_at"]
        current_row["source_hash"] = stable_upload_hash(current_row)
        current_rows.append(current_row)
    return current_rows


def build_current_historical_index_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    current_rows: list[dict[str, object]] = []
    for row in rows:
        normalized = normalize_row(row, HISTORICAL_INDEX_NULLABLE_KEYS)
        hektor_annonce_id = normalized.get("hektor_annonce_id")
        if hektor_annonce_id is None:
            continue
        current_row = {
            "hektor_annonce_id": int(hektor_annonce_id),
            "app_historical_id": int(normalized.get("app_historical_id") or hektor_annonce_id),
            "numero_dossier": normalized.get("numero_dossier"),
            "numero_mandat": normalized.get("numero_mandat"),
            "titre_bien": normalized.get("titre_bien") or "[Sans titre]",
            "ville": normalized.get("ville"),
            "code_postal": normalized.get("code_postal"),
            "type_bien": normalized.get("type_bien"),
            "prix": normalize_numeric(normalized.get("prix")),
            "commercial_id": normalized.get("commercial_id"),
            "commercial_nom": normalized.get("commercial_nom"),
            "negociateur_email": normalized.get("negociateur_email"),
            "agence_nom": normalized.get("agence_nom"),
            "statut_annonce": normalized.get("statut_annonce"),
            "archive": normalized.get("archive") or "0",
            "diffusable": normalized.get("diffusable"),
            "date_maj": normalize_timestamp(normalized.get("date_maj")),
            "mandat_type": normalized.get("mandat_type"),
            "mandat_date_debut": normalized.get("mandat_date_debut"),
            "mandat_date_fin": normalized.get("mandat_date_fin"),
            "mandat_montant": normalize_numeric(normalized.get("mandat_montant")),
            "mandants_texte": normalized.get("mandants_texte"),
            "search_text": None,
            "has_local_detail": normalize_bool(normalized.get("has_local_detail")),
            "local_detail_updated_at": normalize_timestamp(normalized.get("local_detail_updated_at")),
            "photo_url_listing": normalized.get("photo_url_listing"),
        }
        current_row["search_text"] = build_search_text(current_row)
        current_row["source_updated_at"] = current_row["date_maj"] or current_row["local_detail_updated_at"]
        current_row["source_hash"] = stable_upload_hash(current_row)
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
    return [row["app_dossier_id"] for row in fetch_local_app_dossier_identity()]


def fetch_local_app_dossier_identity() -> list[dict[str, int]]:
    con = sqlite_read_connection(PHASE2_DB)
    try:
        attach_hektor_read(con)
        rows = con.execute(
            f"""
            SELECT app_dossier_id, hektor_annonce_id
            FROM app_view_generale
            WHERE {ANNONCES_SCOPE_WHERE}
            ORDER BY app_dossier_id
            """
        ).fetchall()
        return [
            {"app_dossier_id": int(row[0]), "hektor_annonce_id": int(row[1])}
            for row in rows
            if row[0] is not None and row[1] is not None
        ]
    finally:
        con.close()


def rewrite_payload_app_dossier_ids(payload: dict[str, list[dict[str, object]]], id_rewrites: dict[int, int]) -> None:
    if not id_rewrites:
        return
    for key in ("dossiers", "dossier_details", "work_items", "mandat_register_rows", "broadcasts"):
        for row in payload.get(key, []):
            app_dossier_id = row.get("app_dossier_id")
            if app_dossier_id is None:
                continue
            rewritten = id_rewrites.get(int(app_dossier_id))
            if rewritten is not None:
                row["app_dossier_id"] = rewritten


def resolve_app_dossier_ids_from_hektor_annonce_ids(hektor_annonce_ids: list[str]) -> list[int]:
    cleaned = sorted({str(value).strip() for value in hektor_annonce_ids if str(value).strip()})
    if not cleaned:
        return []
    placeholders = ",".join("?" for _ in cleaned)
    con = sqlite_read_connection(PHASE2_DB)
    try:
        rows = con.execute(
            f"""
            SELECT id
            FROM app_dossier
            WHERE CAST(hektor_annonce_id AS TEXT) IN ({placeholders})
            ORDER BY id
            """,
            cleaned,
        ).fetchall()
        return [int(row[0]) for row in rows]
    finally:
        con.close()


def fetch_source_watermark() -> str | None:
    con = sqlite_read_connection(PHASE2_DB)
    try:
        attach_hektor_read(con)
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
    con = sqlite_read_connection(PHASE2_DB)
    try:
        attach_hektor_read(con)
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
    parser.add_argument("--rebuild-register-only", action="store_true", help="Rebuild only app_mandat_register_current from the local complete register payload.")
    parser.add_argument("--dossier-id", action="append", default=[], help="Limit push to one app_dossier_id. Can be repeated.")
    parser.add_argument("--hektor-annonce-id", action="append", default=[], help="Resolve and limit push to one Hektor annonce id. Can be repeated.")
    parser.add_argument("--all-local-current", action="store_true", help="Push the current local export scope as a delta without treating remote-only dossiers as stale.")
    parser.add_argument("--since-watermark", default=None, help="Force delta detection from this local source watermark, for example '2026-05-20 00:00:00'.")
    parser.add_argument("--skip-stale-deletes", action="store_true", help="Do not delete remote current rows that are absent from the local current export scope.")
    parser.add_argument("--allow-stale-deletes", action="store_true", help="Allow deleting stale remote current dossiers. Disabled by default as a safety guard.")
    parser.add_argument("--max-stale-deletes", type=int, default=500, help="Maximum stale remote dossiers that can be deleted without --allow-stale-deletes.")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_dirty_annonce_ids(client) -> set[int]:
    """Tier 2 dirty-skip : app_dossier_id ayant un pending d'edition optimiste
    (table app_annonce_pending) -> a NE PAS reecraser lors du push (on preserve la
    valeur optimiste affichee jusqu'a confirmation du push Hektor)."""
    try:
        rows = client.fetch_all_rows(
            path="app_annonce_pending", select="app_dossier_id", order="app_dossier_id.asc")
    except Exception:
        return set()
    out: set[int] = set()
    for row in rows or []:
        try:
            out.add(int(row["app_dossier_id"]))
        except (TypeError, ValueError, KeyError):
            continue
    return out


def main() -> None:
    args = parse_args()
    load_env_files((args.env_file, *DEFAULT_ENV_FILES))

    supabase_url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    supabase_service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    client = SupabaseRestClient(base_url=supabase_url, service_role_key=supabase_service_role_key)
    source_watermark = fetch_source_watermark()

    if args.rebuild_register_only:
        register_payload = build_payload(limit=None, dossier_ids=None, include_filter_catalog=False)
        current_mandat_register_rows = build_current_mandat_register_rows(register_payload.get("mandat_register_rows", []))
        delta_run_id = client.insert_delta_run(
            mode="upgrade",
            notes={
                "generated_from": "phase2/sync/push_upgrade_to_supabase.py",
                "register_only": True,
                "source_watermark": source_watermark,
                "mandat_register_local_count": len(current_mandat_register_rows),
            },
        )
        try:
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
                    "dossiers_detected": 0,
                    "dossiers_upserted": 0,
                    "details_upserted": 0,
                    "work_items_replaced": 0,
                    "filters_replaced": 0,
                    "deleted_dossiers": 0,
                },
            )
            print(
                json.dumps(
                    {
                        "delta_run_id": delta_run_id,
                        "mandat_register_replaced": len(current_mandat_register_rows),
                        "mode": "register_only",
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
                    "notes": {"error": str(exc), "register_only": True},
                },
            )
            raise
        return

    latest_completed_run = client.fetch_latest_completed_delta_run()
    latest_notes = latest_completed_run.get("notes") if latest_completed_run else None
    latest_source_watermark = None
    if isinstance(latest_notes, dict):
        latest_source_watermark = normalize_sqlite_timestamp(latest_notes.get("source_watermark"))
    forced_since_watermark = normalize_sqlite_timestamp(args.since_watermark)
    if args.since_watermark and not forced_since_watermark:
        raise RuntimeError(f"Invalid --since-watermark value: {args.since_watermark}")
    effective_source_watermark = forced_since_watermark or latest_source_watermark

    targeted_dossier_ids = sorted({
        int(value)
        for value in args.dossier_id
        if str(value).strip()
    } | set(resolve_app_dossier_ids_from_hektor_annonce_ids(args.hektor_annonce_id)))
    targeted_push = bool(targeted_dossier_ids)

    local_identity = fetch_local_app_dossier_identity()
    local_ids = {row["app_dossier_id"] for row in local_identity}
    local_id_by_hektor_id = {
        row["hektor_annonce_id"]: row["app_dossier_id"]
        for row in local_identity
    }
    remote_dossiers = client.fetch_all_rows(path="app_dossier_current", select="app_dossier_id,hektor_annonce_id", order="app_dossier_id.asc")
    remote_ids = {int(row["app_dossier_id"]) for row in remote_dossiers if row.get("app_dossier_id") is not None}
    remote_id_by_hektor_id = {
        int(row["hektor_annonce_id"]): int(row["app_dossier_id"])
        for row in remote_dossiers
        if row.get("app_dossier_id") is not None and row.get("hektor_annonce_id") is not None
    }
    id_rewrites = {
        local_id: remote_id
        for hektor_id, local_id in local_id_by_hektor_id.items()
        if (remote_id := remote_id_by_hektor_id.get(hektor_id)) is not None and remote_id != local_id
    }
    effective_local_ids = {id_rewrites.get(local_id, local_id) for local_id in local_ids}
    remote_has_rows = bool(remote_ids)
    stale_ids: list[int] = []
    baseline_adopted = False

    def stale_remote_ids() -> list[int]:
        if args.skip_stale_deletes:
            return []
        return sorted(remote_ids - effective_local_ids)

    if targeted_push:
        candidate_ids = [value for value in targeted_dossier_ids if value in local_ids]
        stale_ids = []
    elif args.all_local_current:
        candidate_ids = sorted(local_ids)
        stale_ids = stale_remote_ids()
    elif args.full_rebuild:
        candidate_ids = sorted(local_ids)
        stale_ids = stale_remote_ids()
    elif effective_source_watermark:
        candidate_ids = detect_candidate_dossier_ids(since=effective_source_watermark)
        stale_ids = stale_remote_ids()
    elif latest_source_watermark is None and remote_has_rows:
        candidate_ids = []
        stale_ids = stale_remote_ids()
        baseline_adopted = True
    else:
        candidate_ids = sorted(local_ids)
        stale_ids = stale_remote_ids()

    if stale_ids and not args.allow_stale_deletes and (baseline_adopted or len(stale_ids) > args.max_stale_deletes):
        raise RuntimeError(
            "Safety stop: refusing to delete "
            f"{len(stale_ids)} stale remote dossiers "
            f"(baseline_adopted={baseline_adopted}, max_stale_deletes={args.max_stale_deletes}). "
            "Re-run with --allow-stale-deletes only after a manual audit."
        )

    should_build_delta_payload = args.full_rebuild or targeted_push or bool(candidate_ids) or bool(stale_ids)
    should_build_global_payload = args.full_rebuild or (not targeted_push and not candidate_ids and bool(stale_ids))
    payload_dossier_ids = None if should_build_global_payload else candidate_ids
    payload = (
        build_payload(limit=None, dossier_ids=payload_dossier_ids, include_filter_catalog=False)
        if should_build_delta_payload
        else {"dossiers": [], "dossier_details": [], "work_items": [], "mandat_register_rows": [], "broadcasts": []}
    )
    rewrite_payload_app_dossier_ids(payload, id_rewrites)
    candidate_ids = sorted({id_rewrites.get(value, value) for value in candidate_ids})
    targeted_dossier_ids = sorted({id_rewrites.get(value, value) for value in targeted_dossier_ids})
    if should_build_global_payload or targeted_push or candidate_ids:
        register_payload = payload
    else:
        register_payload = {"mandat_register_rows": []}
    current_dossiers = build_current_dossiers(payload["dossiers"])
    source_updated_at_by_id = {int(row["app_dossier_id"]): row.get("source_updated_at") for row in current_dossiers}
    current_details = build_current_details(payload["dossier_details"], source_updated_at_by_id)
    current_work_items = build_current_work_items(payload["work_items"])
    current_mandat_register_rows = build_current_mandat_register_rows(register_payload.get("mandat_register_rows", []))
    current_broadcasts = normalize_broadcast_rows(payload.get("broadcasts", []))

    # Tier 2 dirty-skip : preserver les dossiers en cours d'edition optimiste (pending)
    # -> on les retire de l'upsert pour ne pas reecraser la valeur affichee. stale_ids
    # est deja calcule plus haut, donc aucun risque de suppression de ces dossiers.
    dirty_annonce_ids = fetch_dirty_annonce_ids(client)
    if dirty_annonce_ids:
        _before = len(current_dossiers)
        current_dossiers = [r for r in current_dossiers if int(r["app_dossier_id"]) not in dirty_annonce_ids]
        current_details = [r for r in current_details if int(r["app_dossier_id"]) not in dirty_annonce_ids]
        _skipped = _before - len(current_dossiers)
        if _skipped:
            print(f"[tier2-dirty-skip] {_skipped} dossier(s) en edition optimiste preserves (non reecrases)")

    archive_table_available = client.table_available("app_archive_annonce_index_current")
    historical_table_available = client.table_available("app_historical_annonce_index_current")
    current_archive_index_rows = build_current_archive_index_rows(build_archive_annonce_index(limit=None)) if archive_table_available else []
    current_historical_index_rows = build_current_historical_index_rows(build_historical_annonce_index(limit=None)) if historical_table_available else []

    dossier_upsert_ids = sorted({int(row["app_dossier_id"]) for row in current_dossiers})
    detail_upsert_ids = sorted({int(row["app_dossier_id"]) for row in current_details})
    local_work_hashes = grouped_work_hashes(current_work_items)
    work_candidate_ids = sorted({int(row["app_dossier_id"]) for row in current_work_items})
    broadcast_candidate_ids = sorted({int(row["app_dossier_id"]) for row in current_broadcasts})
    archive_upsert_ids: list[int] = []
    archive_delete_ids: list[int] = []
    historical_upsert_ids: list[int] = []
    historical_delete_ids: list[int] = []

    current_filter_catalog: list[dict[str, object]] = []
    filters_should_refresh = (
        not targeted_push
        and (args.full_rebuild
        or bool(candidate_ids)
        or bool(stale_ids)
        or (latest_completed_run is None and not baseline_adopted))
    )

    delta_run_id = client.insert_delta_run(
        mode="upgrade",
        notes={
            "generated_from": "phase2/sync/push_upgrade_to_supabase.py",
            "full_rebuild": args.full_rebuild,
            "baseline_adopted": baseline_adopted,
            "source_watermark": source_watermark,
            "previous_source_watermark": latest_source_watermark,
            "forced_since_watermark": forced_since_watermark,
            "effective_source_watermark": effective_source_watermark,
            "skip_stale_deletes": args.skip_stale_deletes,
            "candidate_count": len(candidate_ids),
            "all_local_current": args.all_local_current,
            "remote_id_rewrites": len(id_rewrites),
            "targeted_push": targeted_push,
            "targeted_dossier_ids": targeted_dossier_ids,
            "targeted_hektor_annonce_ids": args.hektor_annonce_id,
            "archive_index_enabled": archive_table_available,
            "archive_index_local_count": len(current_archive_index_rows),
            "historical_index_enabled": historical_table_available,
            "historical_index_local_count": len(current_historical_index_rows),
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
        remote_archive_hashes: dict[int, str] = {}
        if archive_table_available:
            remote_archive_hashes = {
                int(row["hektor_annonce_id"]): str(row["source_hash"])
                for row in client.fetch_all_rows(
                    path="app_archive_annonce_index_current",
                    select="hektor_annonce_id,source_hash",
                    order="hektor_annonce_id.asc",
                )
                if row.get("hektor_annonce_id") is not None
            }
        remote_historical_hashes: dict[int, str] = {}
        if historical_table_available:
            remote_historical_hashes = {
                int(row["hektor_annonce_id"]): str(row["source_hash"])
                for row in client.fetch_all_rows(
                    path="app_historical_annonce_index_current",
                    select="hektor_annonce_id,source_hash",
                    order="hektor_annonce_id.asc",
                )
                if row.get("hektor_annonce_id") is not None
            }

        local_dossier_hashes = map_hashes(current_dossiers, id_key="app_dossier_id")
        local_detail_hashes = map_hashes(current_details, id_key="app_dossier_id")
        local_archive_hashes = map_hashes(current_archive_index_rows, id_key="hektor_annonce_id")
        local_historical_hashes = map_hashes(current_historical_index_rows, id_key="hektor_annonce_id")

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
        if archive_table_available:
            archive_upsert_ids = sorted(
                hektor_annonce_id
                for hektor_annonce_id, source_hash in local_archive_hashes.items()
                if remote_archive_hashes.get(hektor_annonce_id) != source_hash
            )
            archive_delete_ids = sorted(set(remote_archive_hashes) - set(local_archive_hashes))
        if historical_table_available:
            historical_upsert_ids = sorted(
                hektor_annonce_id
                for hektor_annonce_id, source_hash in local_historical_hashes.items()
                if remote_historical_hashes.get(hektor_annonce_id) != source_hash
            )
            historical_delete_ids = sorted(set(remote_historical_hashes) - set(local_historical_hashes))
        if args.skip_stale_deletes:
            archive_delete_ids = []
            historical_delete_ids = []

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

        register_replace_annonce_ids = sorted({
            int(row["hektor_annonce_id"])
            for row in [*current_dossiers, *current_mandat_register_rows]
            if row.get("hektor_annonce_id") is not None
        })
        register_replace_dossier_ids = sorted(set(stale_ids) | (set(targeted_dossier_ids) if targeted_push else set()))
        if args.full_rebuild:
            client.delete_all_rows(path="app_mandat_register_current", filter_expr="register_row_id=not.is.null")
        else:
            if register_replace_annonce_ids:
                client.delete_rows_by_ids(path="app_mandat_register_current", column="hektor_annonce_id", ids=register_replace_annonce_ids)
            if register_replace_dossier_ids:
                client.delete_rows_by_ids(path="app_mandat_register_current", column="app_dossier_id", ids=register_replace_dossier_ids)
        if current_mandat_register_rows:
            client.insert_rows(
                path="app_mandat_register_current",
                rows=current_mandat_register_rows,
                batch_size=args.work_item_batch_size,
            )

        if archive_table_available:
            if archive_delete_ids:
                client.delete_rows_by_ids(path="app_archive_annonce_index_current", column="hektor_annonce_id", ids=archive_delete_ids)
            if archive_upsert_ids:
                archive_upsert_set = set(archive_upsert_ids)
                client.upsert_rows(
                    path="app_archive_annonce_index_current",
                    rows=[row for row in current_archive_index_rows if int(row["hektor_annonce_id"]) in archive_upsert_set],
                    batch_size=args.dossier_batch_size,
                )

        if historical_table_available:
            if historical_delete_ids:
                client.delete_rows_by_ids(path="app_historical_annonce_index_current", column="hektor_annonce_id", ids=historical_delete_ids)
            if historical_upsert_ids:
                historical_upsert_set = set(historical_upsert_ids)
                client.upsert_rows(
                    path="app_historical_annonce_index_current",
                    rows=[row for row in current_historical_index_rows if int(row["hektor_annonce_id"]) in historical_upsert_set],
                    batch_size=args.dossier_batch_size,
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
                    "archive_index_enabled": archive_table_available,
                    "archive_index_local": len(current_archive_index_rows),
                    "archive_index_upserted": len(archive_upsert_ids),
                    "archive_index_deleted": len(archive_delete_ids),
                    "historical_index_enabled": historical_table_available,
                    "historical_index_local": len(current_historical_index_rows),
                    "historical_index_upserted": len(historical_upsert_ids),
                    "historical_index_deleted": len(historical_delete_ids),
                    "deleted_dossiers": len(stale_ids),
                    "mode": "full_rebuild" if args.full_rebuild else "upgrade",
                    "targeted_push": targeted_push,
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
