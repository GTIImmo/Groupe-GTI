from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = ROOT / ".env"


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


def rest_get(*, base_url: str, service_role_key: str, path: str, query: dict[str, str]) -> object | None:
    url = f"{base_url.rstrip('/')}/rest/v1/{path.lstrip('/')}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    request = urllib.request.Request(
        url,
        headers={
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase REST error {exc.code} on {path}: {detail}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Relit l'etat live d'un dossier dans app_dossier_current et app_dossiers_current.")
    parser.add_argument("--app-dossier-id", type=int, required=True)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_env_file(args.env_file)
    supabase_url = os.environ.get("SUPABASE_URL", "").strip()
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not supabase_url or not service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    filters = {
        "app_dossier_id": f"eq.{int(args.app_dossier_id)}",
    }
    current_rows = rest_get(
        base_url=supabase_url,
        service_role_key=service_role_key,
        path="app_dossier_current",
        query={
            "select": "app_dossier_id,hektor_annonce_id,validation_diffusion_state,diffusable,refreshed_at",
            **filters,
        },
    )
    view_rows = rest_get(
        base_url=supabase_url,
        service_role_key=service_role_key,
        path="app_dossiers_current",
        query={
            "select": "app_dossier_id,hektor_annonce_id,validation_diffusion_state,diffusable",
            **filters,
        },
    )
    delta_rows = rest_get(
        base_url=supabase_url,
        service_role_key=service_role_key,
        path="app_delta_run",
        query={
            "select": "id,scope,status,started_at,finished_at",
            "scope": "eq.annonces_current",
            "order": "started_at.desc",
            "limit": "3",
        },
    )
    print(
        json.dumps(
            {
                "app_dossier_current": current_rows or [],
                "app_dossiers_current": view_rows or [],
                "latest_delta_runs": delta_rows or [],
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
