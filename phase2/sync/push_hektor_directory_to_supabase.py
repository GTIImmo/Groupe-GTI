from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hektor_pipeline.common import HektorClient, Settings


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


def stable_hash(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


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
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else None

    def upsert_rows(self, *, path: str, rows: list[dict[str, object]], batch_size: int = 100) -> None:
        for index in range(0, len(rows), batch_size):
            batch = rows[index : index + batch_size]
            self._request(method="POST", path=path, payload=batch, prefer="resolution=merge-duplicates")

    def fetch_ids(self, *, path: str, column: str) -> list[str]:
        rows = self._request(
            method="GET",
            path=path,
            query={"select": column, "order": f"{column}.asc"},
        ) or []
        return [str(row.get(column) or "").strip() for row in rows if str(row.get(column) or "").strip()]

    def delete_missing(self, *, path: str, column: str, keep_ids: list[str], chunk_size: int = 200) -> int:
        existing = self.fetch_ids(path=path, column=column)
        stale = [value for value in existing if value not in set(keep_ids)]
        for index in range(0, len(stale), chunk_size):
            batch = stale[index : index + chunk_size]
            joined = ",".join(batch)
            self._request(method="DELETE", path=f"{path}?{column}=in.({joined})")
        return len(stale)


def fetch_all_users(client: HektorClient, version: str) -> list[dict[str, Any]]:
    page = 1
    rows: list[dict[str, Any]] = []
    while True:
        payload = client.get_json("/Api/User/UsersOfParent/", params={"page": page, "version": version})
        data = payload.get("data") if isinstance(payload, dict) else None
        metadata = payload.get("metadata") if isinstance(payload, dict) else None
        batch = data if isinstance(data, list) else []
        rows.extend(item for item in batch if isinstance(item, dict))
        next_page = metadata.get("nextPage") if isinstance(metadata, dict) else None
        if not next_page:
            break
        page = int(next_page)
    return rows


def fetch_all_agencies(client: HektorClient, version: str) -> list[dict[str, Any]]:
    page = 0
    rows: list[dict[str, Any]] = []
    while True:
        payload = client.get_json("/Api/Agence/ListAgences/", params={"page": page, "version": version})
        data = payload.get("data") if isinstance(payload, dict) else None
        metadata = payload.get("metadata") if isinstance(payload, dict) else None
        batch = data if isinstance(data, list) else []
        rows.extend(item for item in batch if isinstance(item, dict))
        next_page = metadata.get("nextPage") if isinstance(metadata, dict) else None
        if next_page in (None, "", 0, "0"):
            break
        page = int(next_page) - 1
    return rows


def build_user_rows(rows: list[dict[str, Any]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        id_user = str(row.get("idUser") or "").strip()
        if not id_user:
            continue
        coord = row.get("coordonnees") if isinstance(row.get("coordonnees"), dict) else {}
        payload = {
            "id_user": id_user,
            "user_type": str(row.get("type") or "").strip() or None,
            "prenom": str(row.get("prenom") or "").strip() or None,
            "nom": str(row.get("nom") or "").strip() or None,
            "display_name": " ".join(part for part in [str(row.get("prenom") or "").strip(), str(row.get("nom") or "").strip()] if part) or None,
            "email": str(coord.get("mail") or "").strip() or None,
            "tel": str(coord.get("tel") or "").strip() or None,
            "portable": str(coord.get("portable") or "").strip() or None,
            "site": str(row.get("site") or "").strip() or None,
            "parent_id": str(row.get("parent") or "").strip() or None,
        }
        payload["source_hash"] = stable_hash(payload)
        output.append(payload)
    return output


def build_agency_rows(rows: list[dict[str, Any]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        id_agence = str(row.get("id") or "").strip()
        if not id_agence:
            continue
        payload = {
            "id_agence": id_agence,
            "id_user": str(row.get("idUser") or "").strip() or None,
            "nom": str(row.get("nom") or "").strip(),
            "mail": str(row.get("mail") or "").strip() or None,
            "tel": str(row.get("tel") or "").strip() or None,
            "responsable": str(row.get("responsable") or "").strip() or None,
            "parent_id": str(row.get("parent") or "").strip() or None,
        }
        payload["source_hash"] = stable_hash(payload)
        output.append(payload)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synchronise users et agences Hektor vers Supabase.")
    parser.add_argument("--skip-purge", action="store_true", help="N'efface pas les ids absents du listing source.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_env_file(ROOT / ".env")
    load_env_file(ROOT / "apps" / "hektor-v1" / ".env")

    supabase_url = os.environ.get("SUPABASE_URL", "").strip()
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not supabase_url or not service_role_key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY requis")

    settings = Settings.from_env()
    hektor = HektorClient(settings)
    client = SupabaseRestClient(base_url=supabase_url, service_role_key=service_role_key)

    user_rows = build_user_rows(fetch_all_users(hektor, settings.api_version))
    agency_rows = build_agency_rows(fetch_all_agencies(hektor, settings.api_version))

    client.upsert_rows(path="app_user_directory", rows=user_rows)
    client.upsert_rows(path="app_agence_directory", rows=agency_rows)

    deleted_users = 0
    deleted_agencies = 0
    if not args.skip_purge:
        deleted_users = client.delete_missing(
            path="app_user_directory",
            column="id_user",
            keep_ids=[str(row["id_user"]) for row in user_rows],
        )
        deleted_agencies = client.delete_missing(
            path="app_agence_directory",
            column="id_agence",
            keep_ids=[str(row["id_agence"]) for row in agency_rows],
        )

    print(
        json.dumps(
            {
                "users_upserted": len(user_rows),
                "agencies_upserted": len(agency_rows),
                "users_deleted": deleted_users,
                "agencies_deleted": deleted_agencies,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
