from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "hektor.sqlite"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "exports_annonce_detail_audit"

MAIN_DETAIL_STATUSES = {"Actif", "Sous offre", "Sous compromis", "Estimation"}
HISTORICAL_STATUSES = {"Vendu", "Clos"}

# Photos and documents are intentionally excluded from this audit.
LOCAL_JSON_BLOCKS = (
    "textes_json",
    "proprietaires_json",
    "mandats_json",
    "pieces_json",
    "notes_json",
    "honoraires_json",
    "terrain_json",
    "copropriete_json",
    "localite_json",
)

RAW_OBJECT_BLOCKS = (
    "ag_interieur",
    "ag_exterieur",
    "terrain",
    "copropriete",
    "equipements",
    "organiser_visite",
    "diagnostiques",
    "mandat_infofi",
    "mandat_mandatdispo",
    "offre_type",
    "localite",
    "proprietaires",
    "mandats",
    "pieces",
    "textes",
    "notes",
    "honoraires",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit read-only de couverture des details annonces locaux et Supabase, "
            "hors photos et documents."
        )
    )
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--skip-supabase", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Limite locale de debug. 0 = tout.")
    return parser.parse_args()


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def safe_json_loads(value: Any) -> Any:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw or raw.lower() == "null":
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def is_present_json(value: Any) -> bool:
    parsed = safe_json_loads(value)
    if parsed is None:
        return False
    if parsed == [] or parsed == {}:
        return False
    return True


def filled_prop_count(block: Any) -> int:
    if not isinstance(block, dict):
        return 0
    props = block.get("props")
    if not isinstance(props, dict):
        return 1 if block else 0
    count = 0
    for item in props.values():
        value = item.get("value") if isinstance(item, dict) else item
        if value not in (None, "", [], {}, "null"):
            count += 1
    return count


def determine_target(archive: str | None, status: str | None) -> str:
    archive_value = str(archive or "0").strip()
    status_value = str(status or "").strip()
    if archive_value == "1":
        return "archive_index_cache_on_demand"
    if status_value in HISTORICAL_STATUSES:
        return "historical_index_cache_on_demand"
    if status_value in MAIN_DETAIL_STATUSES:
        return "principal_detail_current"
    return "out_of_expected_scope"


def open_local_db(path: Path) -> sqlite3.Connection:
    uri = f"file:{path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_local_rows(conn: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    sql = """
        select
            a.hektor_annonce_id,
            a.no_dossier,
            a.no_mandat,
            a.archive,
            a.date_maj,
            a.synced_at as listing_synced_at,
            d.statut_name,
            d.synced_at as detail_synced_at,
            d.raw_json,
            d.textes_json,
            d.proprietaires_json,
            d.mandats_json,
            d.pieces_json,
            d.notes_json,
            d.honoraires_json,
            d.terrain_json,
            d.copropriete_json,
            d.localite_json,
            s.last_detail_sync_at
        from hektor_annonce a
        left join hektor_annonce_detail d on d.hektor_annonce_id = a.hektor_annonce_id
        left join sync_annonce_state s on s.hektor_annonce_id = a.hektor_annonce_id
        order by cast(a.hektor_annonce_id as integer)
    """
    if limit > 0:
        sql += "\nlimit ?"
        rows = conn.execute(sql, (limit,)).fetchall()
    else:
        rows = conn.execute(sql).fetchall()
    return [dict(row) for row in rows]


def fetch_local_sync_errors(conn: sqlite3.Connection) -> dict[str, str]:
    output: dict[str, str] = {}
    try:
        rows = conn.execute(
            """
            select object_id, max(error_message) as error_message
            from sync_error
            where endpoint_name = 'annonce_detail'
              and object_id is not null
            group by object_id
            """
        ).fetchall()
    except sqlite3.OperationalError:
        return output
    for row in rows:
        object_id = str(row["object_id"] or "").strip()
        if object_id:
            output[object_id] = str(row["error_message"] or "").strip()
    return output


def supabase_headers(service_key: str, range_start: int, range_end: int) -> dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Accept": "application/json",
        "Range-Unit": "items",
        "Range": f"{range_start}-{range_end}",
    }


def fetch_supabase_table(
    base_url: str,
    service_key: str,
    table: str,
    select: str,
    *,
    page_size: int = 1000,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        query = urllib.parse.urlencode({"select": select, "order": "hektor_annonce_id.asc"})
        url = f"{base_url.rstrip('/')}/rest/v1/{table}?{query}"
        request = urllib.request.Request(
            url,
            headers=supabase_headers(service_key, offset, offset + page_size - 1),
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            batch = json.loads(response.read().decode("utf-8"))
        if not isinstance(batch, list):
            raise RuntimeError(f"Reponse Supabase inattendue pour {table}")
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def fetch_supabase_presence(skip: bool) -> tuple[dict[str, set[str]], list[str]]:
    if skip:
        return {}, ["Supabase ignore par option --skip-supabase"]

    load_env_file(PROJECT_ROOT / ".env")
    load_env_file(PROJECT_ROOT / "apps" / "hektor-v1" / ".env")
    base_url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or ""
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not base_url or not service_key:
        return {}, ["Variables Supabase absentes: audit local uniquement"]

    specs = {
        "principal_detail_current": ("app_dossier_detail_current", "hektor_annonce_id"),
        "archive_index": ("app_archive_annonce_index_current", "hektor_annonce_id"),
        "historical_index": ("app_historical_annonce_index_current", "hektor_annonce_id"),
        "archive_detail_cache": ("app_archive_annonce_detail_cache", "hektor_annonce_id,expires_at"),
        "historical_detail_cache": ("app_historical_annonce_detail_cache", "hektor_annonce_id,expires_at"),
    }
    presence: dict[str, set[str]] = {}
    warnings: list[str] = []
    for key, (table, select) in specs.items():
        try:
            rows = fetch_supabase_table(base_url, service_key, table, select)
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            warnings.append(f"Lecture Supabase impossible pour {table}: {exc}")
            continue
        if key.endswith("_detail_cache"):
            now = datetime.now(timezone.utc)
            valid: set[str] = set()
            expired: set[str] = set()
            for row in rows:
                annonce_id = str(row.get("hektor_annonce_id") or "").strip()
                expires_raw = str(row.get("expires_at") or "").strip()
                if not annonce_id:
                    continue
                try:
                    expires_at = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
                except ValueError:
                    expired.add(annonce_id)
                    continue
                if expires_at > now:
                    valid.add(annonce_id)
                else:
                    expired.add(annonce_id)
            presence[f"{key}_valid"] = valid
            presence[f"{key}_expired"] = expired
        else:
            presence[key] = {str(row.get("hektor_annonce_id") or "").strip() for row in rows if row.get("hektor_annonce_id") is not None}
    return presence, warnings


def build_audit_rows(
    local_rows: list[dict[str, Any]],
    errors_by_id: dict[str, str],
    supabase_presence: dict[str, set[str]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in local_rows:
        annonce_id = str(row.get("hektor_annonce_id") or "").strip()
        raw_json = row.get("raw_json")
        raw = safe_json_loads(raw_json)
        raw = raw if isinstance(raw, dict) else {}
        target = determine_target(row.get("archive"), row.get("statut_name"))

        local_block_presence = {name: is_present_json(row.get(name)) for name in LOCAL_JSON_BLOCKS}
        raw_block_counts = {f"raw_{name}_filled_props": filled_prop_count(raw.get(name)) for name in RAW_OBJECT_BLOCKS}
        raw_block_presence = {f"raw_{name}_present": bool(raw.get(name)) for name in RAW_OBJECT_BLOCKS}

        local_detail_present = bool(row.get("raw_json"))
        empty_local_blocks = [name for name, present in local_block_presence.items() if not present]
        missing_critical: list[str] = []
        if not local_detail_present:
            missing_critical.append("detail_raw_json")
        if not row.get("statut_name"):
            missing_critical.append("statut_name")
        if not raw.get("keyData"):
            missing_critical.append("raw.keyData")
        if not raw.get("diagnostiques"):
            missing_critical.append("raw.diagnostiques")

        principal_present = annonce_id in supabase_presence.get("principal_detail_current", set())
        archive_index_present = annonce_id in supabase_presence.get("archive_index", set())
        historical_index_present = annonce_id in supabase_presence.get("historical_index", set())
        archive_cache_valid = annonce_id in supabase_presence.get("archive_detail_cache_valid", set())
        archive_cache_expired = annonce_id in supabase_presence.get("archive_detail_cache_expired", set())
        historical_cache_valid = annonce_id in supabase_presence.get("historical_detail_cache_valid", set())
        historical_cache_expired = annonce_id in supabase_presence.get("historical_detail_cache_expired", set())

        supabase_anomaly = ""
        if target == "principal_detail_current" and supabase_presence and not principal_present:
            supabase_anomaly = "missing_principal_detail_current"
        elif target == "archive_index_cache_on_demand" and supabase_presence and not archive_index_present:
            supabase_anomaly = "missing_archive_index"
        elif target == "historical_index_cache_on_demand" and supabase_presence and not historical_index_present:
            supabase_anomaly = "missing_historical_index"

        output.append(
            {
                "hektor_annonce_id": annonce_id,
                "numero_dossier": row.get("no_dossier") or "",
                "numero_mandat": row.get("no_mandat") or "",
                "archive": row.get("archive") or "",
                "statut_name": row.get("statut_name") or "",
                "target_supabase": target,
                "date_maj": row.get("date_maj") or "",
                "detail_synced_at": row.get("detail_synced_at") or "",
                "last_detail_sync_at": row.get("last_detail_sync_at") or "",
                "local_detail_present": int(local_detail_present),
                "local_raw_length": len(str(raw_json or "")),
                "empty_local_blocks_excluding_photos_docs": "|".join(empty_local_blocks),
                "missing_critical": "|".join(missing_critical),
                "last_detail_error": errors_by_id.get(annonce_id, ""),
                "supabase_principal_detail_present": int(principal_present),
                "supabase_archive_index_present": int(archive_index_present),
                "supabase_historical_index_present": int(historical_index_present),
                "supabase_archive_cache_valid": int(archive_cache_valid),
                "supabase_archive_cache_expired": int(archive_cache_expired),
                "supabase_historical_cache_valid": int(historical_cache_valid),
                "supabase_historical_cache_expired": int(historical_cache_expired),
                "supabase_anomaly": supabase_anomaly,
                **{name: int(value) for name, value in local_block_presence.items()},
                **{name: int(value) for name, value in raw_block_presence.items()},
                **raw_block_counts,
            }
        )
    return output


def summarize(rows: list[dict[str, Any]], warnings: list[str]) -> dict[str, Any]:
    by_target: dict[str, Counter[str]] = defaultdict(Counter)
    missing_critical = Counter()
    empty_blocks = Counter()
    supabase_anomalies = Counter()
    for row in rows:
        target = str(row["target_supabase"])
        by_target[target]["total"] += 1
        by_target[target]["with_local_detail"] += int(row["local_detail_present"])
        if row["missing_critical"]:
            by_target[target]["with_missing_critical"] += 1
            for item in str(row["missing_critical"]).split("|"):
                if item:
                    missing_critical[item] += 1
        for item in str(row["empty_local_blocks_excluding_photos_docs"]).split("|"):
            if item:
                empty_blocks[item] += 1
        if row["supabase_anomaly"]:
            supabase_anomalies[str(row["supabase_anomaly"])] += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "annonce detail excluding photos and documents",
        "rows": len(rows),
        "by_target": {key: dict(counter) for key, counter in sorted(by_target.items())},
        "missing_critical": dict(missing_critical.most_common()),
        "empty_blocks_excluding_photos_docs": dict(empty_blocks.most_common()),
        "supabase_anomalies": dict(supabase_anomalies.most_common()),
        "warnings": warnings,
    }


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"annonce_detail_coverage_{stamp}.csv"
    json_path = output_dir / f"annonce_detail_coverage_{stamp}.json"

    fieldnames = list(rows[0].keys()) if rows else []
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return csv_path, json_path


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path)
    output_dir = Path(args.output_dir)
    if not db_path.exists():
        raise RuntimeError(f"Base locale introuvable: {db_path}")

    conn = open_local_db(db_path)
    try:
        local_rows = fetch_local_rows(conn, args.limit)
        errors_by_id = fetch_local_sync_errors(conn)
    finally:
        conn.close()

    supabase_presence, warnings = fetch_supabase_presence(args.skip_supabase)
    rows = build_audit_rows(local_rows, errors_by_id, supabase_presence)
    summary = summarize(rows, warnings)
    csv_path, json_path = write_outputs(rows, summary, output_dir)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
