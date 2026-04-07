from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ENV_FILE = ROOT / ".env"
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


class SupabaseRestClient:
    def __init__(self, *, base_url: str, service_role_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.service_role_key = service_role_key
        self.timeout_seconds = DEFAULT_HTTP_TIMEOUT_SECONDS
        self.max_retries = DEFAULT_HTTP_MAX_RETRIES

    def _request(self, *, method: str, path: str, query: dict[str, str] | None = None) -> object | None:
        url = f"{self.base_url}/rest/v1/{path.lstrip('/')}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(
            url,
            headers={
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json",
            },
            method=method,
        )
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

    def delete_all(self, *, path: str, filter_expr: str) -> None:
        key, value = filter_expr.split("=", 1)
        self._request(method="DELETE", path=path, query={key: value})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--scope", choices=["annonces", "mandats", "all"], default="all")
    return parser.parse_args()


def purge_annonces(client: SupabaseRestClient) -> dict[str, str]:
    client.delete_all(path="app_delta_run", filter_expr="scope=eq.annonces_current")
    client.delete_all(path="app_dossier_detail_current", filter_expr="app_dossier_id=gte.0")
    client.delete_all(path="app_work_item_current", filter_expr="app_dossier_id=gte.0")
    client.delete_all(path="app_filter_catalog_current_store", filter_expr="filter_type=not.is.null")
    client.delete_all(path="app_dossier_current", filter_expr="app_dossier_id=gte.0")
    client.delete_all(path="app_sync_run", filter_expr="contract_name=eq.app_payload_v1")
    return {
        "app_delta_run": "scope=annonces_current",
        "app_dossier_detail_current": "all",
        "app_work_item_current": "all",
        "app_filter_catalog_current_store": "all",
        "app_dossier_current": "all",
        "app_sync_run": "contract_name=app_payload_v1",
    }


def purge_mandats(client: SupabaseRestClient) -> dict[str, str]:
    client.delete_all(path="app_mandat_broadcast_current", filter_expr="app_dossier_id=gte.0")
    client.delete_all(path="app_diffusion_request", filter_expr="app_dossier_id=gte.0")
    return {
        "app_mandat_broadcast_current": "all",
        "app_diffusion_request": "all",
    }


def main() -> None:
    args = parse_args()
    load_env_file(args.env_file)
    supabase_url = os.environ.get("SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    client = SupabaseRestClient(base_url=supabase_url, service_role_key=service_role_key)
    result: dict[str, object] = {"scope": args.scope, "purged": {}}

    if args.scope in ("annonces", "all"):
        result["purged"] = {**result["purged"], **purge_annonces(client)}
    if args.scope in ("mandats", "all"):
        result["purged"] = {**result["purged"], **purge_mandats(client)}

    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
