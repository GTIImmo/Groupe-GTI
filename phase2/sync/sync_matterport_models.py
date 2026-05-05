from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MATTERPORT_ENV_FILE = ROOT / "matterport" / ".env"
DEFAULT_ENV_FILE = ROOT / ".env"
DEFAULT_OUTPUT = ROOT / "matterport" / "matterport_sync_preview.csv"
DEFAULT_JSON_OUTPUT = ROOT / "matterport" / "matterport_sync_preview.json"
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
MATTERPORT_GRAPHQL_URL = "https://api.matterport.com/api/models/graph"
MATTERPORT_SHOW_URL = "https://my.matterport.com/show/?m={model_id}"
MATTERPORT_GROUP_NAMESPACE = uuid.UUID("8b741103-5a9b-4432-8b25-e5fb53df5cf8")
MATTERPORT_MODEL_NAMESPACE = uuid.UUID("a0dcfb5d-e5e7-4577-9452-efad253de4f5")


FOLDER_PAGE_SIZE = 100
MODEL_PAGE_SIZE = 100
HTTP_TIMEOUT_SECONDS = 60
NUMBER_RE = re.compile(r"\d+")


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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_text(value: object) -> str:
    return str(value or "").strip()


def normalize_mandat(value: object) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def extract_numbers(value: object, min_digits: int = 1) -> list[str]:
    text = normalize_text(value)
    seen: set[str] = set()
    numbers: list[str] = []
    for match in NUMBER_RE.findall(text):
        normalized = normalize_mandat(match)
        if normalized and len(normalized) >= min_digits and normalized not in seen:
            seen.add(normalized)
            numbers.append(normalized)
    return numbers


def matterport_url(model_id: str) -> str:
    return MATTERPORT_SHOW_URL.format(model_id=model_id)


def stable_group_id(hektor_annonce_id: str, numero_mandat: str) -> str:
    return str(uuid.uuid5(MATTERPORT_GROUP_NAMESPACE, f"{hektor_annonce_id}:{numero_mandat}"))


def stable_group_model_id(matterport_model_id: str) -> str:
    return str(uuid.uuid5(MATTERPORT_MODEL_NAMESPACE, matterport_model_id))


@dataclass(frozen=True)
class MatterportCredentials:
    token_id: str
    token_secret: str


class MatterportClient:
    def __init__(self, credentials: MatterportCredentials) -> None:
        token = f"{credentials.token_id}:{credentials.token_secret}".encode("utf-8")
        self.headers = {
            "Authorization": f"Basic {base64.b64encode(token).decode('ascii')}",
            "Content-Type": "application/json",
        }

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = json.dumps({"query": query, "variables": variables or {}}, ensure_ascii=True).encode("utf-8")
        request = urllib.request.Request(MATTERPORT_GRAPHQL_URL, data=payload, headers=self.headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Matterport API HTTP {error.code}: {body[:500]}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"Matterport API unreachable: {error}") from error
        parsed = json.loads(body)
        if parsed.get("errors"):
            raise RuntimeError(f"Matterport GraphQL error: {json.dumps(parsed['errors'], ensure_ascii=True)[:1000]}")
        return parsed.get("data") or {}

    def root_folder(self) -> dict[str, Any]:
        query = """
        query RootFolder {
          rootFolder {
            id
            name
            modelCountSummary
          }
        }
        """
        return self.graphql(query)["rootFolder"]

    def folder_page(self, folder_id: str, model_offset: int, folder_offset: int) -> dict[str, Any]:
        query = """
        query FolderPage($id: ID!, $modelOffset: String, $folderOffset: String, $pageSize: Int!) {
          folder(id: $id) {
            id
            name
            modelCountSummary
            models(offset: $modelOffset, pageSize: $pageSize) {
              totalResults
              results {
                id
                name
                internalId
                created
                modified
                state
                visibility
              }
            }
            subfolders(offset: $folderOffset, pageSize: $pageSize) {
              totalResults
              results {
                id
                name
                modelCountSummary
              }
            }
          }
        }
        """
        return self.graphql(
            query,
            {
                "id": folder_id,
                "modelOffset": str(model_offset),
                "folderOffset": str(folder_offset),
                "pageSize": MODEL_PAGE_SIZE,
            },
        )["folder"]

def load_credentials() -> MatterportCredentials:
    load_env_file(MATTERPORT_ENV_FILE)
    token_id = os.getenv("MATTERPORT_TOKEN_ID", "").strip()
    token_secret = os.getenv("MATTERPORT_TOKEN_SECRET", "").strip()
    if not token_id or not token_secret:
        raise RuntimeError(f"Missing Matterport credentials in {MATTERPORT_ENV_FILE}")
    return MatterportCredentials(token_id=token_id, token_secret=token_secret)


def scan_matterport_models(client: MatterportClient, max_models: int | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    root = client.root_folder()
    folders: list[dict[str, Any]] = []
    models_by_id: dict[str, dict[str, Any]] = {}
    queue: list[tuple[str, str]] = [(root["id"], root.get("name") or "")]
    visited: set[str] = set()

    while queue:
        folder_id, folder_path = queue.pop(0)
        if folder_id in visited:
            continue
        visited.add(folder_id)

        model_offset = 0
        folder_offset = 0
        subfolders_done = False
        models_done = False
        folder_seen = False

        while not (subfolders_done and models_done):
            folder = client.folder_page(folder_id, model_offset, folder_offset)
            if not folder_seen:
                folders.append(
                    {
                        "matterport_folder_id": folder.get("id"),
                        "folder_path": folder_path or folder.get("name"),
                        "name": folder.get("name"),
                        "modelCountSummary": folder.get("modelCountSummary"),
                    }
                )
                folder_seen = True

            if not models_done:
                model_page = folder.get("models") or {}
                model_results = model_page.get("results") or []
                for model in model_results:
                    model_id = normalize_text(model.get("id"))
                    if not model_id:
                        continue
                    models_by_id[model_id] = {
                        "matterport_id": model_id,
                        "name": model.get("name"),
                        "internalId": model.get("internalId"),
                        "created": model.get("created"),
                        "modified": model.get("modified"),
                        "state": model.get("state"),
                        "visibility": model.get("visibility"),
                        "folder_path": folder_path or folder.get("name"),
                        "matterport_url": matterport_url(model_id),
                    }
                    if max_models is not None and len(models_by_id) >= max_models:
                        return list(models_by_id.values()), folders
                model_offset += len(model_results)
                models_done = model_offset >= int(model_page.get("totalResults") or 0) or len(model_results) == 0

            if not subfolders_done:
                subfolder_page = folder.get("subfolders") or {}
                subfolder_results = subfolder_page.get("results") or []
                for subfolder in subfolder_results:
                    subfolder_name = normalize_text(subfolder.get("name"))
                    subfolder_path = f"{folder_path}/{subfolder_name}" if folder_path else subfolder_name
                    queue.append((normalize_text(subfolder.get("id")), subfolder_path))
                folder_offset += len(subfolder_results)
                subfolders_done = folder_offset >= int(subfolder_page.get("totalResults") or 0) or len(subfolder_results) == 0

            time.sleep(0.03)

    return list(models_by_id.values()), folders


def load_current_hektor_by_mandat() -> dict[str, list[dict[str, Any]]]:
    if not PHASE2_DB.exists():
        return {}
    con = sqlite3.connect(PHASE2_DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT
            hektor_annonce_id,
            app_dossier_id,
            numero_dossier,
            numero_mandat,
            titre_bien,
            ville,
            type_bien,
            statut_annonce,
            archive,
            commercial_nom,
            agence_nom
        FROM app_view_generale
        WHERE NULLIF(TRIM(COALESCE(numero_mandat, '')), '') IS NOT NULL
        """
    ).fetchall()
    con.close()
    by_mandat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        mandat = normalize_mandat(row["numero_mandat"])
        if not mandat:
            continue
        by_mandat[mandat].append(dict(row))
    return dict(by_mandat)


def load_historical_hektor_by_mandat() -> dict[str, list[dict[str, Any]]]:
    if not HEKTOR_DB.exists():
        return {}
    con = sqlite3.connect(HEKTOR_DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT
            m.hektor_annonce_id,
            a.no_dossier AS numero_dossier,
            m.numero AS numero_mandat,
            a.titre AS titre_bien,
            a.ville,
            a.archive,
            a.diffusable,
            a.valide,
            d.statut_name
        FROM hektor_mandat m
        LEFT JOIN hektor_annonce a ON a.hektor_annonce_id = m.hektor_annonce_id
        LEFT JOIN hektor_annonce_detail d ON d.hektor_annonce_id = m.hektor_annonce_id
        WHERE NULLIF(TRIM(COALESCE(m.numero, '')), '') IS NOT NULL
        """
    ).fetchall()
    con.close()
    by_mandat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        mandat = normalize_mandat(row["numero_mandat"])
        if not mandat:
            continue
        by_mandat[mandat].append(dict(row))
    return dict(by_mandat)


def select_mandat_for_model(
    model: dict[str, Any],
    current: dict[str, list[dict[str, Any]]],
    historical: dict[str, list[dict[str, Any]]],
    min_mandat_digits: int,
) -> tuple[str | None, str, str]:
    internal = normalize_mandat(model.get("internalId"))
    if len(internal) < min_mandat_digits:
        internal = ""
    numbers = extract_numbers(model.get("name"), min_digits=min_mandat_digits)
    candidates: list[tuple[str, str]] = []
    if internal:
        candidates.append((internal, "internalId"))
    candidates.extend((number, "name") for number in numbers if number != internal)

    current_matches = [(number, source) for number, source in candidates if number in current]
    if len({number for number, _source in current_matches}) == 1:
        number, source = current_matches[0]
        if len(current[number]) == 1:
            return number, "matched_current", source
        return number, "ambiguous_current", source
    if len({number for number, _source in current_matches}) > 1:
        return None, "multiple_current_numbers", ",".join(sorted({source for _number, source in current_matches}))

    historical_matches = [(number, source) for number, source in candidates if number in historical]
    if len({number for number, _source in historical_matches}) == 1:
        number, source = historical_matches[0]
        if len(historical[number]) == 1:
            return number, "matched_historical", source
        return number, "ambiguous_historical", source
    if len({number for number, _source in historical_matches}) > 1:
        return None, "multiple_historical_numbers", ",".join(sorted({source for _number, source in historical_matches}))

    if candidates:
        return candidates[0][0], "number_no_hektor_match", candidates[0][1]
    return None, "no_number", ""


def build_preview_rows(models: list[dict[str, Any]], min_mandat_digits: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    current = load_current_hektor_by_mandat()
    historical = load_historical_hektor_by_mandat()
    enriched: list[dict[str, Any]] = []
    groups_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for model in models:
        selected_mandat, match_status, match_source = select_mandat_for_model(model, current, historical, min_mandat_digits)
        current_rows = current.get(selected_mandat or "", [])
        historical_rows = historical.get(selected_mandat or "", [])
        hektor_rows = current_rows or historical_rows
        hektor_ids = sorted({normalize_text(row.get("hektor_annonce_id")) for row in hektor_rows if normalize_text(row.get("hektor_annonce_id"))})
        dossiers = sorted({normalize_text(row.get("numero_dossier")) for row in hektor_rows if normalize_text(row.get("numero_dossier"))})
        villes = sorted({normalize_text(row.get("ville")) for row in hektor_rows if normalize_text(row.get("ville"))})
        numbers_in_name = extract_numbers(model.get("name"), min_digits=min_mandat_digits)
        row = {
            **model,
            "numbers_in_name": "|".join(numbers_in_name),
            "selected_numero_mandat": selected_mandat or "",
            "match_status": match_status,
            "match_source": match_source,
            "hektor_annonce_ids": "|".join(hektor_ids),
            "hektor_dossiers": "|".join(dossiers),
            "hektor_villes": "|".join(villes),
            "suggested_name": suggested_model_name(model, hektor_rows, selected_mandat),
        }
        enriched.append(row)
        if selected_mandat and match_status == "matched_current" and hektor_ids:
            groups_by_key[(hektor_ids[0], selected_mandat)].append(row)

    groups: list[dict[str, Any]] = []
    for (hektor_id, mandat), rows in sorted(groups_by_key.items(), key=lambda item: (item[0][1], item[0][0])):
        rows_sorted = sorted(rows, key=lambda item: (normalize_text(item.get("name")).lower(), normalize_text(item.get("matterport_id"))))
        states = sorted({normalize_text(row.get("state")) for row in rows_sorted if normalize_text(row.get("state"))})
        visibilities = sorted({normalize_text(row.get("visibility")) for row in rows_sorted if normalize_text(row.get("visibility"))})
        groups.append(
            {
                "id": stable_group_id(hektor_id, mandat),
                "hektor_annonce_id": hektor_id,
                "numero_mandat": mandat,
                "model_count": len(rows_sorted),
                "group_state": states[0] if len(states) == 1 else "mixed",
                "group_visibility": visibilities[0] if len(visibilities) == 1 else "mixed",
                "matterport_model_ids": [row["matterport_id"] for row in rows_sorted],
                "labels": [suggest_label(row, len(rows_sorted)) for row in rows_sorted],
            }
        )
    return enriched, groups


def suggested_model_name(model: dict[str, Any], hektor_rows: list[dict[str, Any]], mandat: str | None) -> str:
    if not hektor_rows or not mandat:
        return ""
    row = hektor_rows[0]
    type_bien = normalize_text(row.get("type_bien")) or "Bien"
    ville = normalize_text(row.get("ville"))
    if ville:
        return f"{type_bien} - {ville} - ref.{mandat}"
    return f"{type_bien} - ref.{mandat}"


def suggest_label(row: dict[str, Any], group_size: int) -> str:
    name = normalize_text(row.get("name"))
    if group_size <= 1:
        return "Visite virtuelle"
    lower = name.lower()
    patterns = [
        (r"\br\s*[-+]?\s*\d+\b", "niveau"),
        (r"\brdc\b", "RDC"),
        (r"\blot\s*\d+\b", "lot"),
        (r"\bappart(?:ement)?\s*\d+\b", "appartement"),
    ]
    for pattern, _kind in patterns:
        match = re.search(pattern, lower, flags=re.IGNORECASE)
        if match:
            return match.group(0).upper().replace("  ", " ")
    return name[:80] if name else "Visite virtuelle"


def write_outputs(rows: list[dict[str, Any]], groups: list[dict[str, Any]], csv_path: Path, json_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "matterport_id",
        "name",
        "internalId",
        "created",
        "modified",
        "state",
        "visibility",
        "folder_path",
        "matterport_url",
        "numbers_in_name",
        "selected_numero_mandat",
        "match_status",
        "match_source",
        "hektor_annonce_ids",
        "hektor_dossiers",
        "hektor_villes",
        "suggested_name",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(
        json.dumps({"generated_at": utc_now_iso(), "rows": rows, "groups": groups}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def summarize(rows: list[dict[str, Any]], groups: list[dict[str, Any]]) -> dict[str, Any]:
    by_status: dict[str, int] = defaultdict(int)
    by_group_size: dict[str, int] = defaultdict(int)
    for row in rows:
        by_status[normalize_text(row.get("match_status"))] += 1
    for group in groups:
        size = int(group["model_count"])
        by_group_size["multi_model" if size > 1 else "single_model"] += 1
    return {
        "models_scanned": len(rows),
        "groups_matched_current": len(groups),
        "match_status_counts": dict(sorted(by_status.items())),
        "group_size_counts": dict(sorted(by_group_size.items())),
    }


def supabase_headers(service_role_key: str) -> dict[str, str]:
    return {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }


def supabase_request(url: str, key: str, table: str, rows: list[dict[str, Any]], conflict_target: str) -> None:
    if not rows:
        return
    endpoint = f"{url.rstrip('/')}/rest/v1/{table}?on_conflict={conflict_target}"
    payload = json.dumps(rows, ensure_ascii=True).encode("utf-8")
    request = urllib.request.Request(endpoint, data=payload, headers=supabase_headers(key), method="POST")
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            response.read()
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase upsert failed on {table}: HTTP {error.code}: {body[:800]}") from error


def build_supabase_rows(rows: list[dict[str, Any]], groups: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups_by_key = {(str(group["hektor_annonce_id"]), str(group["numero_mandat"])): group for group in groups}
    group_rows: list[dict[str, Any]] = []
    model_rows: list[dict[str, Any]] = []
    now = utc_now_iso()

    for group in groups:
        group_rows.append(
            {
                "id": group["id"],
                "hektor_annonce_id": int(group["hektor_annonce_id"]),
                "numero_mandat": group["numero_mandat"],
                "group_label": f"Mandat {group['numero_mandat']}",
                "group_state": group["group_state"],
                "group_visibility": group["group_visibility"],
                "match_status": "matched_current",
                "is_validated": True,
                "synced_at": now,
                "updated_at": now,
            }
        )

    model_index: dict[tuple[str, str], int] = defaultdict(int)
    matched_rows = [row for row in rows if row.get("match_status") == "matched_current" and row.get("hektor_annonce_ids") and row.get("selected_numero_mandat")]
    for row in sorted(matched_rows, key=lambda item: (str(item.get("hektor_annonce_ids")), str(item.get("selected_numero_mandat")), str(item.get("name")))):
        hektor_id = str(row.get("hektor_annonce_ids")).split("|")[0]
        mandat = str(row.get("selected_numero_mandat"))
        group = groups_by_key.get((hektor_id, mandat))
        if not group:
            continue
        key = (hektor_id, mandat)
        model_index[key] += 1
        is_single = int(group.get("model_count") or 0) <= 1
        label = suggest_label(row, int(group.get("model_count") or 1))
        model_rows.append(
            {
                "id": stable_group_model_id(str(row["matterport_id"])),
                "group_id": group["id"],
                "matterport_model_id": row["matterport_id"],
                "matterport_url": row["matterport_url"],
                "matterport_name": row.get("name") or None,
                "matterport_internal_id": row.get("internalId") or None,
                "label": "Visite virtuelle" if is_single else label,
                "display_order": model_index[key],
                "is_primary": model_index[key] == 1,
                "state": row.get("state") or None,
                "visibility": row.get("visibility") or None,
                "created_at_matterport": row.get("created") or None,
                "modified_at_matterport": row.get("modified") or None,
                "synced_at": now,
                "updated_at": now,
            }
        )
    return group_rows, model_rows


def upsert_supabase(rows: list[dict[str, Any]], groups: list[dict[str, Any]], limit_groups: int | None = None) -> dict[str, int]:
    load_env_file(DEFAULT_ENV_FILE)
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        raise RuntimeError(f"Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in {DEFAULT_ENV_FILE}")
    selected_groups = groups[:limit_groups] if limit_groups is not None else groups
    selected_group_ids = {group["id"] for group in selected_groups}
    group_rows, model_rows = build_supabase_rows(rows, selected_groups)
    model_rows = [row for row in model_rows if row["group_id"] in selected_group_ids]
    supabase_request(url, key, "app_matterport_group", group_rows, "id")
    supabase_request(url, key, "app_matterport_group_model", model_rows, "matterport_model_id")
    return {"groups_upserted": len(group_rows), "models_upserted": len(model_rows)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan Matterport models, match them with Hektor mandates, and upsert read-only links into Supabase.")
    parser.add_argument("--max-models", type=int, default=25, help="Small dry-run limit. Use 0 for no limit.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--min-mandat-digits", type=int, default=4, help="Ignore shorter numbers to avoid matching street numbers or floors.")
    parser.add_argument("--supabase-upsert", action="store_true", help="Actually upsert matched current Matterport groups/models into Supabase.")
    parser.add_argument("--supabase-limit-groups", type=int, default=0, help="Safety limit for Supabase upsert groups. Use 0 for all matched groups.")
    args = parser.parse_args(argv)

    max_models = None if args.max_models == 0 else args.max_models

    credentials = load_credentials()
    client = MatterportClient(credentials)
    models, _folders = scan_matterport_models(client, max_models=max_models)
    rows, groups = build_preview_rows(models, min_mandat_digits=args.min_mandat_digits)
    write_outputs(rows, groups, args.output, args.json_output)
    summary = summarize(rows, groups)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"CSV: {args.output}")
    print(f"JSON: {args.json_output}")

    print("READ_ONLY: no Matterport write operation exists in this script.")
    if args.supabase_upsert:
        limit_groups = None if args.supabase_limit_groups == 0 else args.supabase_limit_groups
        result = upsert_supabase(rows, groups, limit_groups=limit_groups)
        print(json.dumps({"supabase_upsert_result": result}, ensure_ascii=False, indent=2))
    else:
        print("DRY_RUN: no Supabase write performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
