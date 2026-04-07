from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ENV_FILE = ROOT / ".env"
DELETE_CHUNK_SIZE = 250


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
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None

    def delete_all(self, *, path: str, filter_expr: str) -> None:
        self._request(method="DELETE", path=path, query={filter_expr.split("=")[0]: filter_expr.split("=", 1)[1]})


def main() -> None:
    load_env_file(DEFAULT_ENV_FILE)
    supabase_url = os.environ.get("SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    client = SupabaseRestClient(base_url=supabase_url, service_role_key=service_role_key)

    client.delete_all(path="app_delta_run", filter_expr="scope=eq.annonces_current")

    client.delete_all(path="app_dossier_detail_current", filter_expr="app_dossier_id=gte.0")
    client.delete_all(path="app_work_item_current", filter_expr="app_dossier_id=gte.0")
    client.delete_all(path="app_filter_catalog_current_store", filter_expr="filter_type=not.is.null")
    client.delete_all(path="app_dossier_current", filter_expr="app_dossier_id=gte.0")

    client.delete_all(path="app_sync_run", filter_expr="contract_name=eq.app_payload_v1")

    print(
        json.dumps(
            {
                "purged": {
                    "app_delta_run": "scope=annonces_current",
                    "app_dossier_current": "all",
                    "app_dossier_detail_current": "all",
                    "app_work_item_current": "all",
                    "app_filter_catalog_current_store": "all",
                    "app_sync_run": "contract_name=app_payload_v1",
                }
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
