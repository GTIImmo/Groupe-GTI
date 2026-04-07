from __future__ import annotations

"""
Script de secours pour recharger explicitement la couche Mandats.

Le contrat app_mandat_current a ete retire du flux applicatif.
Ce script est obsolete et ne doit plus etre utilise.
"""

import argparse
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable

try:
    from phase2.sync.export_mandat_payload import build_payload
except ModuleNotFoundError:
    import sys

    ROOT_DIR = Path(__file__).resolve().parents[2]
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from phase2.sync.export_mandat_payload import build_payload


ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ENV_FILE = ROOT / ".env"
DEFAULT_BATCH_SIZE = 200
FETCH_PAGE_SIZE = 1000
DELETE_CHUNK_SIZE = 100
REQUEST_TIMEOUT = 120
MAX_RETRIES = 5
RETRY_SLEEP_SECONDS = 3


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


def chunked(items: list[dict[str, object]], size: int) -> Iterable[list[dict[str, object]]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


class SupabaseRestClient:
    def __init__(self, *, base_url: str, service_role_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.service_role_key = service_role_key

    def _request(
        self,
        *,
        method: str,
        path: str,
        payload: object | None = None,
        prefer: str | None = None,
    ) -> object | None:
        url = f"{self.base_url}/rest/v1/{path.lstrip('/')}"
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
        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            request = urllib.request.Request(url, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                    raw = response.read().decode("utf-8")
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code in {500, 502, 503, 504} and attempt < MAX_RETRIES:
                    print(f"RETRY {attempt}/{MAX_RETRIES} {method} {path} -> HTTP {exc.code}")
                    time.sleep(RETRY_SLEEP_SECONDS)
                    last_error = exc
                    continue
                raise RuntimeError(f"Supabase REST error {exc.code} on {path}: {detail}") from exc
            except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
                if attempt < MAX_RETRIES:
                    print(f"RETRY {attempt}/{MAX_RETRIES} {method} {path} -> timeout")
                    time.sleep(RETRY_SLEEP_SECONDS)
                    last_error = exc
                    continue
                raise RuntimeError(f"Supabase REST timeout on {path} after {MAX_RETRIES} attempts") from exc
        if last_error:
            raise RuntimeError(f"Supabase REST request failed on {path}") from last_error
        return None

    def fetch_all_rows(self, *, path: str, select: str, order: str) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        offset = 0
        while True:
            query = urllib.parse.urlencode(
                {
                    "select": select,
                    "order": order,
                    "limit": str(FETCH_PAGE_SIZE),
                    "offset": str(offset),
                }
            )
            batch = self._request(method="GET", path=f"{path}?{query}")
            if not isinstance(batch, list) or not batch:
                break
            rows.extend(batch)
            if len(batch) < FETCH_PAGE_SIZE:
                break
            offset += FETCH_PAGE_SIZE
        return rows

    def delete_by_numeric_ids(self, *, path: str, id_field: str, ids: list[int]) -> None:
        for start in range(0, len(ids), DELETE_CHUNK_SIZE):
            chunk = ids[start : start + DELETE_CHUNK_SIZE]
            joined = ",".join(str(value) for value in chunk)
            self._request(method="DELETE", path=f"{path}?{id_field}=in.({joined})")
            print(f"DELETE {path} {len(chunk)}")

    def delete_by_composite_rows(
        self,
        *,
        path: str,
        rows: list[tuple[int, str, str]],
    ) -> None:
        for app_dossier_id, passerelle_key, commercial_key in rows:
            passerelle = urllib.parse.quote(passerelle_key, safe="")
            commercial = urllib.parse.quote(commercial_key, safe="")
            filter_query = (
                f"app_dossier_id=eq.{app_dossier_id}"
                f"&passerelle_key=eq.{passerelle}"
                f"&commercial_key=eq.{commercial}"
            )
            self._request(method="DELETE", path=f"{path}?{filter_query}")
            print(f"DELETE {path} ({app_dossier_id}, {passerelle_key}, {commercial_key})")

    def upsert_rows(
        self,
        *,
        path: str,
        rows: list[dict[str, object]],
        batch_size: int,
    ) -> None:
        for batch in chunked(rows, batch_size):
            self._request(method="POST", path=path, payload=batch, prefer="resolution=merge-duplicates")


def normalize_bool(value: object) -> bool:
    return value in (True, 1, "1", "true")


def normalize_timestamp(value: object) -> str | None:
    text = str(value or "").strip()
    if not text or text.startswith("0000-00-00"):
        return None
    return text


def normalize_numeric(value: object) -> object:
    text = str(value or "").strip()
    if not text:
        return None
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    return parser.parse_args()


def main() -> None:
    raise RuntimeError(
        "push_mandat_to_supabase.py est obsolete: le contrat app_mandat_current a ete retire. Utiliser push_to_supabase.py ou push_upgrade_to_supabase.py."
    )


if __name__ == "__main__":
    main()
