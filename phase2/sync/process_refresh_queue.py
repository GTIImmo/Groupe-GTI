from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = ROOT / ".env"
REFRESH_SINGLE_ANNONCE_SCRIPT = ROOT / "phase2" / "sync" / "refresh_single_annonce.py"


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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class QueueClient:
    def __init__(self, *, base_url: str, service_role_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.service_role_key = service_role_key

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }

    def fetch_pending(self, limit: int) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.base_url}/rest/v1/app_annonce_refresh_queue",
            headers=self._headers(),
            params={
                "select": "*",
                "status": "eq.pending",
                "order": "requested_at.asc,id.asc",
                "limit": str(limit),
            },
            timeout=30,
        )
        response.raise_for_status()
        rows = response.json() or []
        return rows if isinstance(rows, list) else []

    def update_row(self, row_id: int, payload: dict[str, Any]) -> None:
        response = requests.patch(
            f"{self.base_url}/rest/v1/app_annonce_refresh_queue",
            headers=self._headers(),
            params={"id": f"eq.{row_id}"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()


def run_refresh(annonce_id: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(REFRESH_SINGLE_ANNONCE_SCRIPT), "--id-annonce", str(annonce_id).strip()],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0:
        return {
            "ok": False,
            "error": f"refresh_single_annonce failed with code {completed.returncode}",
            "stdout": stdout or None,
            "stderr": stderr or None,
        }
    if stdout:
        try:
            payload = json.loads(stdout)
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
    return {"ok": True, "stdout": stdout or None, "stderr": stderr or None}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Traite la file d'attente des refresh annonce demandés depuis l'app en ligne.")
    parser.add_argument("--limit", type=int, default=25)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(DEFAULT_ENV_FILE)
    supabase_url = os.environ.get("SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    client = QueueClient(base_url=supabase_url, service_role_key=service_role_key)
    rows = client.fetch_pending(args.limit)
    processed: list[dict[str, Any]] = []
    for row in rows:
        row_id = int(row["id"])
        annonce_id = str(row.get("hektor_annonce_id") or "").strip()
        if not annonce_id:
            client.update_row(row_id, {
                "status": "failed",
                "started_at": now_iso(),
                "finished_at": now_iso(),
                "attempt_count": int(row.get("attempt_count") or 0) + 1,
                "last_error": "hektor_annonce_id missing",
            })
            processed.append({"id": row_id, "status": "failed", "error": "hektor_annonce_id missing"})
            continue
        client.update_row(row_id, {
            "status": "processing",
            "started_at": now_iso(),
            "attempt_count": int(row.get("attempt_count") or 0) + 1,
        })
        result = run_refresh(annonce_id)
        if result.get("ok") is False:
            client.update_row(row_id, {
                "status": "failed",
                "finished_at": now_iso(),
                "last_error": str(result.get("error") or "unknown error"),
                "result_json": result,
            })
            processed.append({"id": row_id, "status": "failed", "hektor_annonce_id": annonce_id, "error": result.get("error")})
            continue
        client.update_row(row_id, {
            "status": "completed",
            "finished_at": now_iso(),
            "last_error": None,
            "result_json": result,
        })
        processed.append({"id": row_id, "status": "completed", "hektor_annonce_id": annonce_id})
    print(json.dumps({"processed": processed, "count": len(processed)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
