from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Iterable

try:
    from phase2.sync.export_app_payload import build_payload
except ModuleNotFoundError:
    import sys

    ROOT_DIR = Path(__file__).resolve().parents[2]
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from phase2.sync.export_app_payload import build_payload


ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_ENV_FILE = ROOT / ".env"
DEFAULT_BATCH_SIZE = 500


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
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase REST error {exc.code} on {path}: {detail}") from exc

    def insert_sync_run(self, meta: dict[str, object], summary: dict[str, object]) -> str:
        sync_run_id = str(uuid.uuid4())
        rows = self._request(
            method="POST",
            path="app_sync_run",
            payload=[
                {
                    "id": sync_run_id,
                    "source_name": meta.get("source", "phase2.sqlite"),
                    "contract_name": meta.get("contract", "app_payload_v1"),
                    "status": "completed",
                    "payload_meta": meta,
                    "summary": summary,
                }
            ],
            prefer="return=representation",
        )
        if not rows or not isinstance(rows, list):
            raise RuntimeError("Supabase did not acknowledge sync_run insertion")
        return sync_run_id

    def upsert_summary(self, sync_run_id: str, summary: dict[str, object]) -> None:
        row = {"sync_run_id": sync_run_id, **summary}
        self._request(
            method="POST",
            path="app_summary_snapshot",
            payload=[row],
            prefer="resolution=merge-duplicates",
            query={"on_conflict": "sync_run_id"},
        )

    def insert_rows(
        self,
        *,
        path: str,
        rows: list[dict[str, object]],
        batch_size: int,
    ) -> None:
        for batch in chunked(rows, batch_size):
            self._request(
                method="POST",
                path=path,
                payload=batch,
            )

    def upsert_rows(
        self,
        *,
        path: str,
        rows: list[dict[str, object]],
        batch_size: int,
    ) -> None:
        for batch in chunked(rows, batch_size):
            self._request(
                method="POST",
                path=path,
                payload=batch,
                prefer="resolution=merge-duplicates",
            )

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
                    "limit": str(1000),
                    "offset": str(offset),
                },
            )
            if not isinstance(batch, list) or not batch:
                break
            rows.extend(batch)
            if len(batch) < 1000:
                break
            offset += 1000
        return rows

    def delete_rows_by_ids(self, *, path: str, column: str, ids: list[int], chunk_size: int = 500) -> None:
        for index in range(0, len(ids), chunk_size):
            batch = ids[index : index + chunk_size]
            id_list = ",".join(str(int(value)) for value in batch)
            self._request(method="DELETE", path=f"{path}?{column}=in.({id_list})")

    def delete_broadcast_rows(self, rows: list[tuple[int, str, str]]) -> None:
        for app_dossier_id, passerelle_key, commercial_key in rows:
            filter_query = (
                f"app_dossier_id=eq.{app_dossier_id}"
                f"&passerelle_key=eq.{urllib.parse.quote(passerelle_key, safe='')}"
                f"&commercial_key=eq.{urllib.parse.quote(commercial_key, safe='')}"
            )
            self._request(method="DELETE", path=f"app_mandat_broadcast_current?{filter_query}")


def normalize_payload_rows(sync_run_id: str, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for row in rows:
        next_row = {"sync_run_id": sync_run_id, **row}
        if "has_open_blocker" in next_row:
            next_row["has_open_blocker"] = bool(next_row["has_open_blocker"])
        for nullable_key in (
            "archive",
            "prix",
            "date_relance_prevue",
            "date_entree_file",
            "date_derniere_action",
            "numero_dossier",
            "numero_mandat",
            "commercial_id",
            "commercial_nom",
            "agence_nom",
            "statut_annonce",
            "validation_diffusion_state",
            "etat_visibilite",
            "alerte_principale",
            "priority",
            "commentaire_resume",
            "dernier_event_type",
            "dernier_work_status",
            "type_demande_label",
            "work_status",
            "internal_status",
            "motif_blocage",
            "next_action",
            "titre_bien",
            "ville",
            "type_bien",
        ):
            if next_row.get(nullable_key) == "":
                next_row[nullable_key] = None
        normalized.append(next_row)
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--sample-limit", type=int, default=None, help="borne optionnelle pour test")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_env_file(args.env_file)

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    payload = build_payload(limit=args.sample_limit)
    meta = payload["meta"]
    summary = payload["summary"]
    dossiers = payload["dossiers"]
    dossier_details = payload.get("dossier_details", [])
    work_items = payload["work_items"]
    broadcasts = payload.get("broadcasts", [])
    filter_catalog = payload.get("filter_catalog", [])

    client = SupabaseRestClient(
        base_url=supabase_url,
        service_role_key=supabase_service_role_key,
    )

    sync_run_id = client.insert_sync_run(meta=meta, summary=summary)
    client.upsert_summary(sync_run_id, summary)
    client.insert_rows(
        path="app_dossier_v1",
        rows=normalize_payload_rows(sync_run_id, dossiers),
        batch_size=args.batch_size,
    )
    client.insert_rows(
        path="app_dossier_detail_v1",
        rows=normalize_payload_rows(sync_run_id, dossier_details),
        batch_size=args.batch_size,
    )
    client.insert_rows(
        path="app_work_item_v1",
        rows=normalize_payload_rows(sync_run_id, work_items),
        batch_size=args.batch_size,
    )
    client.insert_rows(
        path="app_filter_catalog_v1",
        rows=[{"sync_run_id": sync_run_id, **row} for row in filter_catalog],
        batch_size=args.batch_size,
    )

    normalized_broadcasts = []
    for row in broadcasts:
        normalized_broadcasts.append(
            {
                **row,
                "is_success": row.get("is_success") in (True, 1, "1", "true"),
                "is_error": row.get("is_error") in (True, 1, "1", "true"),
            }
        )

    remote_broadcast_rows = client.fetch_all_rows(
        path="app_mandat_broadcast_current",
        select="app_dossier_id,passerelle_key,commercial_key",
        order="app_dossier_id.asc",
    )
    remote_broadcast_keys = {
        (int(row["app_dossier_id"]), str(row["passerelle_key"] or ""), str(row.get("commercial_key") or ""))
        for row in remote_broadcast_rows
        if row.get("app_dossier_id") is not None and row.get("passerelle_key") is not None
    }
    local_broadcast_keys = {
        (int(row["app_dossier_id"]), str(row["passerelle_key"] or ""), str(row.get("commercial_key") or ""))
        for row in normalized_broadcasts
    }
    stale_broadcast_keys = sorted(remote_broadcast_keys - local_broadcast_keys)
    client.upsert_rows(path="app_mandat_broadcast_current", rows=normalized_broadcasts, batch_size=args.batch_size)
    if stale_broadcast_keys:
        client.delete_broadcast_rows(stale_broadcast_keys)

    print(json.dumps({
        "sync_run_id": sync_run_id,
        "dossiers": len(dossiers),
        "dossier_details": len(dossier_details),
        "work_items": len(work_items),
        "broadcasts": len(normalized_broadcasts),
        "filter_catalog": len(filter_catalog),
        "batch_size": args.batch_size,
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
