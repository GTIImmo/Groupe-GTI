from __future__ import annotations

"""Ecriture du battement de coeur d'un worker GTI dans app_worker_registry.

Palier 1 / Lot 1.2 — instrumentation.

Principe : chaque worker signale sa derniere execution (colonnes ajoutees par
supabase/patch_worker_heartbeat_2026-07-04.sql). Le monitoring
(check_gti_health.py -> check_worker_heartbeat) alerte si un worker planifie
n'a plus de succes recent.

GARANTIE : best-effort. Une defaillance du heartbeat (Supabase injoignable,
colonnes pas encore migrees, timeout) ne doit JAMAIS casser le worker instrumente
-> report() n'echoue jamais, la CLI renvoie toujours 0.

Usage CLI (appelee par run_full_pipeline.ps1) :
    python monitoring/heartbeat.py --worker phase1.sync_raw --status success
    python monitoring/heartbeat.py --worker phase1.sync_raw --status error --error "boom"
    python monitoring/heartbeat.py --worker x --status success --dry-run

Usage import (scripts Python) :
    from monitoring.heartbeat import report, heartbeat
    report("phase1.sync_raw", status="success")
    with heartbeat("phase2.bootstrap"):
        do_work()  # running a l'entree, success en sortie, error sur exception
"""

import argparse
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


def _config() -> tuple[str | None, str | None]:
    for rel in (".env", "backend/.env", "apps/hektor-v1/.env"):
        _load_env_file(ROOT / rel)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    return (url.rstrip("/") if url else None), key


def report(
    worker_key: str,
    status: str = "success",
    duration_ms: int | None = None,
    error: str | None = None,
    host: str | None = None,
    *,
    dry_run: bool = False,
    timeout: int = 10,
) -> bool:
    """Ecrit un heartbeat. Renvoie True si ecrit, False sinon. Ne leve JAMAIS."""
    try:
        now = _iso_now()
        payload: dict[str, Any] = {
            "last_run_at": now,
            "last_status": status,
            "last_run_host": host or socket.gethostname(),
            "updated_at": now,
        }
        if status == "success":
            payload["last_success_at"] = now
            payload["last_error"] = None
        elif error:
            payload["last_error"] = str(error)[:1000]
        if duration_ms is not None:
            payload["last_duration_ms"] = int(duration_ms)

        if dry_run:
            print(f"[heartbeat dry-run] {worker_key}: {json.dumps(payload, ensure_ascii=True)}")
            return False

        url, api_key = _config()
        if not url or not api_key:
            print(f"[heartbeat] skipped {worker_key}: Supabase not configured", file=sys.stderr)
            return False

        endpoint = (
            f"{url}/rest/v1/app_worker_registry"
            f"?worker_key=eq.{urllib.parse.quote(str(worker_key), safe='')}"
        )
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=True).encode("utf-8"),
            method="PATCH",
            headers={
                "apikey": api_key,
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        # 400 typique avant application de la migration (colonnes absentes) : non fatal.
        print(f"[heartbeat] HTTP {exc.code} for {worker_key}: {detail}", file=sys.stderr)
        return False
    except Exception as exc:
        print(f"[heartbeat] failed for {worker_key}: {exc}", file=sys.stderr)
        return False


class heartbeat:
    """Context manager : running a l'entree, success en sortie, error sur exception."""

    def __init__(self, worker_key: str, *, host: str | None = None, dry_run: bool = False) -> None:
        self.worker_key = worker_key
        self.host = host
        self.dry_run = dry_run
        self._t0: float | None = None

    def __enter__(self) -> "heartbeat":
        self._t0 = time.monotonic()
        report(self.worker_key, status="running", host=self.host, dry_run=self.dry_run)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        duration_ms = int((time.monotonic() - self._t0) * 1000) if self._t0 is not None else None
        if exc_type is None:
            report(self.worker_key, status="success", duration_ms=duration_ms, host=self.host, dry_run=self.dry_run)
        else:
            report(self.worker_key, status="error", duration_ms=duration_ms, error=repr(exc), host=self.host, dry_run=self.dry_run)
        return False  # ne supprime pas l'exception


def main() -> int:
    parser = argparse.ArgumentParser(description="Ecrit un heartbeat worker GTI dans app_worker_registry.")
    parser.add_argument("--worker", required=True)
    parser.add_argument("--status", default="success", choices=["success", "error", "running"])
    parser.add_argument("--duration-ms", type=int, default=None)
    parser.add_argument("--error", default=None)
    parser.add_argument("--host", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    report(
        args.worker,
        status=args.status,
        duration_ms=args.duration_ms,
        error=args.error,
        host=args.host,
        dry_run=args.dry_run,
    )
    # Best-effort : ne jamais faire echouer l'appelant (l'orchestrateur teste $LASTEXITCODE).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
