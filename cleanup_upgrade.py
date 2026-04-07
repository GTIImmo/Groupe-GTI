import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import OrderedDict
from pathlib import Path


FETCH_PAGE_SIZE = 100
DELETE_CHUNK_SIZE = 50
REQUEST_TIMEOUT = 120
MAX_RETRIES = 5
RETRY_SLEEP_SECONDS = 3


vals = {}
for line in Path(".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        vals[key.strip()] = value.strip().strip('"').strip("'")

base = vals["SUPABASE_URL"].rstrip("/") + "/rest/v1"
key = vals["SUPABASE_SERVICE_ROLE_KEY"]

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}

TABLE_COUNTS = OrderedDict(
    [
        ("app_sync_run", "sync_runs"),
        ("app_dossier_v1", "dossier_v1"),
        ("app_dossier_detail_v1", "dossier_detail_v1"),
        ("app_work_item_v1", "work_item_v1"),
        ("app_filter_catalog_v1", "filter_catalog_v1"),
        ("app_dossier_current", "dossier_current"),
        ("app_dossier_detail_current", "dossier_detail_current"),
        ("app_work_item_current", "work_item_current"),
        ("app_filter_catalog_current_store", "filter_catalog_current"),
        ("app_delta_run", "delta_run"),
        ("app_mandat_current", "mandat_current"),
        ("app_mandat_broadcast_current", "mandat_broadcast_current"),
        ("app_diffusion_request", "diffusion_request"),
    ]
)


def request(path: str, method: str = "GET") -> object | None:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        req = urllib.request.Request(f"{base}/{path}", headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code in {500, 502, 503, 504} and attempt < MAX_RETRIES:
                print(f"RETRY {attempt}/{MAX_RETRIES} {method} {path} -> HTTP {exc.code}")
                time.sleep(RETRY_SLEEP_SECONDS)
                last_error = exc
                continue
            raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {detail}") from exc
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            if attempt < MAX_RETRIES:
                print(f"RETRY {attempt}/{MAX_RETRIES} {method} {path} -> timeout")
                time.sleep(RETRY_SLEEP_SECONDS)
                last_error = exc
                continue
            raise RuntimeError(f"{method} {path} -> timeout after {MAX_RETRIES} attempts") from exc
    if last_error:
        raise RuntimeError(f"{method} {path} -> failed after retries") from last_error
    return None


def fetch_ids(path: str, id_field: str) -> list[str]:
    ids: list[str] = []
    offset = 0
    while True:
        query = urllib.parse.urlencode(
            {
                "select": id_field,
                "order": f"{id_field}.asc",
                "limit": str(FETCH_PAGE_SIZE),
                "offset": str(offset),
            }
        )
        rows = request(f"{path}?{query}")
        if not isinstance(rows, list) or not rows:
            break
        ids.extend(str(row[id_field]) for row in rows if row.get(id_field) is not None)
        if len(rows) < FETCH_PAGE_SIZE:
            break
        offset += FETCH_PAGE_SIZE
    return ids


def fetch_count(path: str) -> int:
    rows = request(f"{path}?select=count&limit=1")
    if not isinstance(rows, list) or not rows:
        return 0
    value = rows[0].get("count")
    return int(value or 0)


def print_counts(label: str) -> None:
    print(label)
    for table, alias in TABLE_COUNTS.items():
        print(f"  lecture {alias}...", flush=True)
        try:
            count = fetch_count(table)
        except Exception as exc:
            print(f"  {alias}: ERROR {exc}")
            continue
        print(f"  {alias}: {count}")


def delete_numeric_chunk(path: str, id_field: str, chunk: list[str]) -> None:
    joined = ",".join(str(int(value)) for value in chunk)
    request(f"{path}?{id_field}=in.({joined})", method="DELETE")
    print("DELETE", path, len(chunk))


def delete_numeric_ids(path: str, id_field: str, ids: list[str]) -> None:
    for start in range(0, len(ids), DELETE_CHUNK_SIZE):
        chunk = ids[start : start + DELETE_CHUNK_SIZE]
        try:
            delete_numeric_chunk(path, id_field, chunk)
            continue
        except RuntimeError:
            pass

        if len(chunk) == 1:
            delete_numeric_chunk(path, id_field, chunk)
            continue

        mid = len(chunk) // 2
        left = chunk[:mid]
        right = chunk[mid:]
        if left:
            delete_numeric_ids(path, id_field, left)
        if right:
            delete_numeric_ids(path, id_field, right)


def delete_text_ids(path: str, id_field: str, ids: list[str]) -> None:
    for value in ids:
        encoded = urllib.parse.quote(value, safe="")
        request(f"{path}?{id_field}=eq.{encoded}", method="DELETE")
        print("DELETE", path, value)


def reset_annonces_snapshots() -> None:
    summary_ids = fetch_ids("app_summary_snapshot", "sync_run_id")
    dossier_v1_ids = fetch_ids("app_dossier_v1", "id")
    detail_v1_ids = fetch_ids("app_dossier_detail_v1", "id")
    work_v1_ids = fetch_ids("app_work_item_v1", "id")
    filter_v1_ids = fetch_ids("app_filter_catalog_v1", "id")
    sync_run_ids = fetch_ids("app_sync_run", "id")

    if summary_ids:
        delete_text_ids("app_summary_snapshot", "sync_run_id", summary_ids)
    if detail_v1_ids:
        delete_numeric_ids("app_dossier_detail_v1", "id", detail_v1_ids)
    if work_v1_ids:
        delete_numeric_ids("app_work_item_v1", "id", work_v1_ids)
    if filter_v1_ids:
        delete_numeric_ids("app_filter_catalog_v1", "id", filter_v1_ids)
    if dossier_v1_ids:
        delete_numeric_ids("app_dossier_v1", "id", dossier_v1_ids)
    if sync_run_ids:
        delete_text_ids("app_sync_run", "id", sync_run_ids)


def reset_annonces_current() -> None:
    detail_ids = fetch_ids("app_dossier_detail_current", "app_dossier_id")
    work_ids = fetch_ids("app_work_item_current", "id")
    filter_ids = fetch_ids("app_filter_catalog_current_store", "id")
    dossier_ids = fetch_ids("app_dossier_current", "app_dossier_id")
    delta_ids = fetch_ids("app_delta_run", "id")

    if detail_ids:
        delete_numeric_ids("app_dossier_detail_current", "app_dossier_id", detail_ids)
    if work_ids:
        delete_numeric_ids("app_work_item_current", "id", work_ids)
    if filter_ids:
        delete_numeric_ids("app_filter_catalog_current_store", "id", filter_ids)
    if dossier_ids:
        delete_numeric_ids("app_dossier_current", "app_dossier_id", dossier_ids)
    if delta_ids:
        delete_text_ids("app_delta_run", "id", delta_ids)


def reset_mandats() -> None:
    broadcast_ids = fetch_ids("app_mandat_broadcast_current", "app_dossier_id")
    mandat_ids = fetch_ids("app_mandat_current", "app_dossier_id")
    diffusion_ids = fetch_ids("app_diffusion_request", "id")

    if broadcast_ids:
        unique_broadcast_ids = sorted(set(broadcast_ids), key=int)
        delete_numeric_ids("app_mandat_broadcast_current", "app_dossier_id", unique_broadcast_ids)
    if mandat_ids:
        delete_numeric_ids("app_mandat_current", "app_dossier_id", mandat_ids)
    if diffusion_ids:
        delete_text_ids("app_diffusion_request", "id", diffusion_ids)


def main() -> None:
    print_counts("AVANT PURGE")
    reset_annonces_current()
    reset_annonces_snapshots()
    reset_mandats()
    print_counts("APRES PURGE")
    print("RESET COMPLET TERMINE")


if __name__ == "__main__":
    main()
