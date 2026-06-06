from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAME = "check_gti_health"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime | None = None) -> str:
    return (dt or utc_now()).isoformat().replace("+00:00", "Z")


def load_env_file(path: Path) -> None:
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
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = str(value).strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def age_minutes(dt: datetime | None) -> float | None:
    if dt is None:
        return None
    return max(0.0, (utc_now() - dt).total_seconds() / 60.0)


def file_mtime(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    except OSError:
        return None


def dir_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                continue
    return total


def newest_file(directory: Path, pattern: str) -> Path | None:
    if not directory.exists():
        return None
    files = [p for p in directory.glob(pattern) if p.is_file()]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def tail_text(path: Path, max_bytes: int = 8192) -> str:
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - max_bytes), os.SEEK_SET)
            return handle.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def simple_error_seen(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in (" error", "failed", "exception", "traceback", "echou", "erreur"))


@dataclass
class CheckResult:
    status_key: str
    domain: str
    component: str
    check_name: str
    status: str
    severity: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    observed_at: str = field(default_factory=iso_utc)

    def status_row(self) -> dict[str, Any]:
        return {
            "status_key": self.status_key,
            "domain": self.domain,
            "component": self.component,
            "check_name": self.check_name,
            "status": self.status,
            "severity": self.severity,
            "message": self.message[:1000],
            "observed_at": self.observed_at,
            "details_json": self.details,
            "source": SOURCE_NAME,
            "updated_at": iso_utc(),
        }

    def event_row(self) -> dict[str, Any]:
        return {
            "event_key": self.status_key,
            "domain": self.domain,
            "component": self.component,
            "check_name": self.check_name,
            "status": self.status,
            "severity": self.severity,
            "message": self.message[:1000],
            "observed_at": self.observed_at,
            "details_json": self.details,
            "source": SOURCE_NAME,
        }


class SupabaseClient:
    def __init__(self, url: str, service_role_key: str, timeout_seconds: int = 15) -> None:
        self.url = url.rstrip("/")
        self.key = service_role_key
        self.timeout_seconds = timeout_seconds

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        params: dict[str, str] | None = None,
        payload: Any | None = None,
        prefer: str | None = None,
    ) -> Any:
        query = ""
        if params:
            query = "?" + urllib.parse.urlencode(params, doseq=False, safe="(),.*")
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        request = urllib.request.Request(
            f"{self.url}/rest/v1/{path}{query}",
            data=body,
            method=method,
            headers=self._headers(prefer),
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                text = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase HTTP {exc.code} on {path}: {detail[:500]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Supabase unreachable on {path}: {exc}") from exc
        if not text:
            return None
        return json.loads(text)

    def get(self, path: str, params: dict[str, str] | None = None) -> Any:
        return self.request(path, params=params)

    def upsert_status(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        self.request(
            "app_monitor_status",
            method="POST",
            params={"on_conflict": "status_key"},
            payload=rows,
            prefer="resolution=merge-duplicates,return=minimal",
        )

    def insert_events(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        self.request("app_monitor_event", method="POST", payload=rows, prefer="return=minimal")


class Monitor:
    def __init__(self, args: argparse.Namespace, supabase: SupabaseClient | None) -> None:
        self.args = args
        self.supabase = supabase
        self.root = Path(args.project_root).resolve()
        self.results: list[CheckResult] = []

    def add(
        self,
        status_key: str,
        domain: str,
        component: str,
        check_name: str,
        status: str,
        message: str,
        details: dict[str, Any] | None = None,
        severity: str | None = None,
    ) -> None:
        if severity is None:
            severity = "info" if status == "ok" else status
        self.results.append(
            CheckResult(
                status_key=status_key,
                domain=domain,
                component=component,
                check_name=check_name,
                status=status,
                severity=severity,
                message=message,
                details=details or {},
            )
        )

    def safe_check(self, label: str, func: Any) -> None:
        try:
            func()
        except Exception as exc:
            self.add(
                f"monitor.{label}",
                "system",
                "monitor",
                label,
                "unknown",
                f"Check {label} failed locally: {exc}",
                {"error": str(exc)},
                severity="unknown",
            )

    def run(self) -> list[CheckResult]:
        checks = [
            ("supabase_registry", self.check_supabase_registry),
            ("supabase_runs", self.check_supabase_runs),
            ("console_jobs", self.check_console_jobs),
            ("backend_health", self.check_backend_health),
            ("sqlite_files", self.check_sqlite_files),
            ("local_logs", self.check_local_logs),
            ("playwright_sessions", self.check_playwright_sessions),
            ("document_storage", self.check_document_storage),
        ]
        for label, check in checks:
            self.safe_check(label, check)
        self.add_summary()
        return self.results

    def check_supabase_registry(self) -> None:
        if not self.supabase:
            self.add("supabase.registry", "system", "supabase", "worker_registry", "unknown", "Supabase not configured")
            return
        rows = self.supabase.get(
            "app_worker_registry",
            {
                "select": "worker_key,status,criticality,monitoring_domain",
                "order": "worker_key.asc",
            },
        )
        count = len(rows or [])
        if count == 0:
            self.add("supabase.registry", "system", "supabase", "worker_registry", "critical", "Worker registry is empty")
            return
        critical = sum(1 for row in rows if row.get("criticality") == "critical")
        self.add(
            "supabase.registry",
            "system",
            "supabase",
            "worker_registry",
            "ok",
            f"Worker registry available: {count} workers",
            {"worker_count": count, "critical_count": critical},
        )

    def check_supabase_runs(self) -> None:
        if not self.supabase:
            return
        delta_rows = self.supabase.get(
            "app_delta_run",
            {
                "select": "id,status,scope,started_at,finished_at,notes",
                "order": "started_at.desc",
                "limit": "10",
            },
        ) or []
        completed = [row for row in delta_rows if row.get("status") == "completed"]
        failed = [row for row in delta_rows if row.get("status") == "failed"]
        latest_completed = completed[0] if completed else None
        latest_finished = parse_iso(latest_completed.get("finished_at") if latest_completed else None)
        latest_age = age_minutes(latest_finished)
        stale_limit = float(self.args.supabase_freshness_minutes)
        if latest_age is None:
            self.add(
                "supabase.delta_run.freshness",
                "system",
                "supabase",
                "delta_run_freshness",
                "warning",
                "No completed app_delta_run found",
                {"recent_runs": len(delta_rows)},
            )
        elif latest_age > stale_limit:
            self.add(
                "supabase.delta_run.freshness",
                "system",
                "supabase",
                "delta_run_freshness",
                "warning",
                f"Latest completed Supabase delta run is stale: {latest_age:.0f} min",
                {"age_minutes": latest_age, "threshold_minutes": stale_limit},
            )
        else:
            self.add(
                "supabase.delta_run.freshness",
                "system",
                "supabase",
                "delta_run_freshness",
                "ok",
                f"Latest completed Supabase delta run age: {latest_age:.0f} min",
                {"age_minutes": latest_age, "threshold_minutes": stale_limit},
            )
        self.add(
            "supabase.delta_run.errors",
            "system",
            "supabase",
            "delta_run_errors",
            "warning" if failed else "ok",
            f"{len(failed)} failed app_delta_run rows in latest {len(delta_rows)} runs",
            {"failed_count": len(failed), "recent_count": len(delta_rows)},
        )

    def check_console_jobs(self) -> None:
        if not self.supabase:
            return
        rows = self.supabase.get(
            "app_console_job",
            {
                "select": "id,job_type,status,requested_at,started_at,worker_id,error_message",
                "status": "in.(pending,running,error)",
                "order": "requested_at.desc",
                "limit": "200",
            },
        ) or []
        pending_stale = []
        running_stale = []
        error_recent = []
        pending_limit = float(self.args.console_pending_minutes)
        running_limit = float(self.args.console_running_minutes)
        for row in rows:
            status = row.get("status")
            if status == "pending":
                current_age = age_minutes(parse_iso(row.get("requested_at"))) or 0
                if current_age > pending_limit:
                    pending_stale.append(row)
            elif status == "running":
                current_age = age_minutes(parse_iso(row.get("started_at"))) or 0
                if current_age > running_limit:
                    running_stale.append(row)
            elif status == "error":
                error_recent.append(row)
        if running_stale:
            self.add(
                "console.jobs.running_stale",
                "system",
                "console",
                "running_jobs",
                "critical",
                f"{len(running_stale)} Console jobs running too long",
                {"count": len(running_stale), "threshold_minutes": running_limit},
            )
        else:
            self.add(
                "console.jobs.running_stale",
                "system",
                "console",
                "running_jobs",
                "ok",
                "No stale running Console jobs",
                {"threshold_minutes": running_limit},
            )
        self.add(
            "console.jobs.pending_stale",
            "system",
            "console",
            "pending_jobs",
            "warning" if pending_stale else "ok",
            f"{len(pending_stale)} Console jobs pending too long",
            {"count": len(pending_stale), "threshold_minutes": pending_limit},
        )
        self.add(
            "console.jobs.errors",
            "business",
            "console",
            "error_jobs",
            "warning" if error_recent else "ok",
            f"{len(error_recent)} Console jobs currently in error",
            {"count": len(error_recent)},
        )

    def check_backend_health(self) -> None:
        url = self.args.backend_health_url
        if not url:
            self.add("backend.health", "system", "backend", "health", "unknown", "Backend health URL not configured")
            return
        request = urllib.request.Request(url, method="GET")
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.args.timeout_seconds) as response:
                elapsed_ms = int((time.monotonic() - started) * 1000)
                payload = response.read().decode("utf-8", errors="replace")[:500]
                if response.status != 200:
                    self.add(
                        "backend.health",
                        "system",
                        "backend",
                        "health",
                        "warning",
                        f"Backend health returned HTTP {response.status}",
                        {"url": url, "elapsed_ms": elapsed_ms, "body": payload},
                    )
                else:
                    self.add(
                        "backend.health",
                        "system",
                        "backend",
                        "health",
                        "ok",
                        "Backend health OK",
                        {"url": url, "elapsed_ms": elapsed_ms},
                    )
        except Exception as exc:
            self.add(
                "backend.health",
                "system",
                "backend",
                "health",
                "warning",
                f"Backend health unreachable: {exc}",
                {"url": url, "error": str(exc)},
            )

    def check_sqlite_files(self) -> None:
        sqlite_specs = [
            ("sqlite.hektor", self.root / "data" / "hektor.sqlite", self.args.sqlite_freshness_minutes, "critical"),
            ("sqlite.phase2", self.root / "phase2" / "phase2.sqlite", self.args.sqlite_freshness_minutes, "critical"),
            ("sqlite.actif", self.root / "ACTIF" / "actif.sqlite", self.args.actif_sqlite_freshness_minutes, "warning"),
        ]
        for key, path, freshness_minutes, stale_status in sqlite_specs:
            if not path.exists():
                self.add(key, "system", "sqlite", "file_presence", "critical", f"SQLite missing: {path}", {"path": str(path)})
                continue
            mtime = file_mtime(path)
            current_age = age_minutes(mtime)
            details = {"path": str(path), "size_bytes": path.stat().st_size, "mtime": iso_utc(mtime) if mtime else None}
            if current_age is not None:
                details["age_minutes"] = current_age
            if current_age is not None and current_age > float(freshness_minutes):
                self.add(key, "system", "sqlite", "mtime", stale_status, f"SQLite stale: {path.name} age {current_age:.0f} min", details)
            else:
                self.add(key, "system", "sqlite", "mtime", "ok", f"SQLite fresh enough: {path.name}", details)
        wal_path = self.root / "data" / "hektor.sqlite-wal"
        if wal_path.exists():
            size_mb = wal_path.stat().st_size / (1024 * 1024)
            status = "critical" if size_mb > self.args.wal_critical_mb else "warning" if size_mb > self.args.wal_warning_mb else "ok"
            self.add(
                "sqlite.hektor.wal_size",
                "system",
                "sqlite",
                "wal_size",
                status,
                f"Hektor WAL size: {size_mb:.1f} MB",
                {"path": str(wal_path), "size_mb": size_mb, "warning_mb": self.args.wal_warning_mb, "critical_mb": self.args.wal_critical_mb},
            )

    def check_local_logs(self) -> None:
        tmp_dir = self.root / ".tmp"
        console_log_dir = self.root / "Console" / "logs"
        latest_pipeline = newest_file(tmp_dir, "full_pipeline_*.log")
        if not latest_pipeline:
            self.add("logs.pipeline.latest", "system", "logs", "pipeline_log", "warning", "No full pipeline log found", {"directory": str(tmp_dir)})
        else:
            mtime = file_mtime(latest_pipeline)
            current_age = age_minutes(mtime) or 0
            tail = tail_text(latest_pipeline)
            has_error = simple_error_seen(tail)
            stale = current_age > float(self.args.pipeline_log_freshness_minutes)
            status = "warning" if has_error or stale else "ok"
            self.add(
                "logs.pipeline.latest",
                "system",
                "logs",
                "pipeline_log",
                status,
                f"Latest pipeline log: {latest_pipeline.name}",
                {"path": str(latest_pipeline), "age_minutes": current_age, "tail_has_error_token": has_error},
            )
        self._check_log_dir_size("logs.tmp.size", tmp_dir)
        self._check_log_dir_size("logs.console.size", console_log_dir)

    def _check_log_dir_size(self, status_key: str, directory: Path) -> None:
        if not directory.exists():
            self.add(status_key, "system", "logs", "log_dir_size", "warning", f"Log directory missing: {directory}", {"path": str(directory)})
            return
        size_mb = dir_size_bytes(directory) / (1024 * 1024)
        status = "warning" if size_mb > float(self.args.log_dir_warning_mb) else "ok"
        self.add(
            status_key,
            "system",
            "logs",
            "log_dir_size",
            status,
            f"Log directory size {size_mb:.1f} MB: {directory.name}",
            {"path": str(directory), "size_mb": size_mb, "warning_mb": self.args.log_dir_warning_mb},
        )

    def check_playwright_sessions(self) -> None:
        session_dir = self.root / "Console" / "sessions"
        expected = {
            "actions": "critical",
            "admin": "critical",
            "documents": "warning",
            "sync_light": "warning",
        }
        missing = []
        present = []
        for kind, missing_status in expected.items():
            path = session_dir / f"storage_state_{kind}.json"
            if path.exists():
                present.append(kind)
            else:
                missing.append({"kind": kind, "status": missing_status, "path": str(path)})
        if any(item["status"] == "critical" for item in missing):
            status = "critical"
        elif missing:
            status = "warning"
        else:
            status = "ok"
        self.add(
            "playwright.hektor.sessions",
            "system",
            "playwright",
            "hektor_sessions",
            status,
            f"Hektor Playwright sessions present={len(present)} missing={len(missing)}",
            {"present": present, "missing": missing},
        )
        matterport_path = self.root / "Console" / "matterport_storage_state.json"
        self.add(
            "playwright.matterport.session",
            "system",
            "playwright",
            "matterport_session",
            "ok" if matterport_path.exists() else "warning",
            "Matterport Playwright session present" if matterport_path.exists() else "Matterport Playwright session missing",
            {"path": str(matterport_path)},
        )

    def check_document_storage(self) -> None:
        path = Path(self.args.document_storage_path)
        if not path.exists():
            self.add(
                "documents.local_storage",
                "system",
                "documents",
                "storage_presence",
                "warning",
                f"Local document storage missing: {path}",
                {"path": str(path)},
            )
            return
        size_mb = dir_size_bytes(path) / (1024 * 1024)
        self.add(
            "documents.local_storage",
            "system",
            "documents",
            "storage_presence",
            "ok",
            f"Local document storage reachable: {path}",
            {"path": str(path), "size_mb": size_mb},
        )

    def add_summary(self) -> None:
        critical = sum(1 for result in self.results if result.status == "critical")
        warning = sum(1 for result in self.results if result.status == "warning")
        unknown = sum(1 for result in self.results if result.status == "unknown")
        status = "critical" if critical else "warning" if warning or unknown else "ok"
        severity = "critical" if critical else "warning" if warning else "unknown" if unknown else "info"
        self.add(
            "monitor.summary",
            "system",
            "monitor",
            "summary",
            status,
            f"GTI monitor summary: {critical} critical, {warning} warning, {unknown} unknown",
            {"critical": critical, "warning": warning, "unknown": unknown, "total_checks": len(self.results)},
            severity=severity,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GTI local read-only health supervisor.")
    parser.add_argument("--project-root", default=str(ROOT))
    parser.add_argument("--backend-health-url", default=os.getenv("GTI_BACKEND_HEALTH_URL", "http://127.0.0.1:8000/health"))
    parser.add_argument("--document-storage-path", default=os.getenv("CONSOLE_LOCAL_ARCHIVE_ROOT", r"C:\Hektor\HektorConsoleDocuments"))
    parser.add_argument("--timeout-seconds", type=int, default=15)
    parser.add_argument("--supabase-freshness-minutes", type=int, default=30 * 60)
    parser.add_argument("--sqlite-freshness-minutes", type=int, default=30 * 60)
    parser.add_argument("--actif-sqlite-freshness-minutes", type=int, default=7 * 24 * 60)
    parser.add_argument("--pipeline-log-freshness-minutes", type=int, default=30 * 60)
    parser.add_argument("--console-pending-minutes", type=int, default=60)
    parser.add_argument("--console-running-minutes", type=int, default=45)
    parser.add_argument("--wal-warning-mb", type=int, default=512)
    parser.add_argument("--wal-critical-mb", type=int, default=1024)
    parser.add_argument("--log-dir-warning-mb", type=int, default=1024)
    parser.add_argument("--dry-run", action="store_true", help="Run checks but do not write to Supabase.")
    parser.add_argument("--emit-ok-events", action="store_true", help="Insert events for OK checks too.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--strict-exit", action="store_true", help="Exit non-zero on critical or unknown checks.")
    return parser


def configure_supabase(args: argparse.Namespace) -> SupabaseClient | None:
    project_root = Path(args.project_root)
    load_env_file(project_root / ".env")
    load_env_file(project_root / "backend" / ".env")
    load_env_file(project_root / "apps" / "hektor-v1" / ".env")
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not service_key:
        return None
    return SupabaseClient(url, service_key, timeout_seconds=args.timeout_seconds)


def write_results(supabase: SupabaseClient | None, results: list[CheckResult], emit_ok_events: bool) -> tuple[bool, str | None]:
    if not supabase:
        return False, "Supabase writes skipped"
    try:
        supabase.upsert_status([result.status_row() for result in results])
        event_rows = [
            result.event_row()
            for result in results
            if emit_ok_events or result.status in {"warning", "critical", "unknown"}
        ]
        supabase.insert_events(event_rows)
        return True, None
    except Exception as exc:
        return False, str(exc)


def print_report(results: list[CheckResult], as_json: bool) -> None:
    if as_json:
        print(json.dumps([result.status_row() for result in results], ensure_ascii=True, indent=2))
        return
    for result in results:
        print(f"[{result.status.upper():8}] {result.status_key}: {result.message}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    supabase = configure_supabase(args)
    monitor = Monitor(args, supabase)
    results = monitor.run()
    if args.dry_run:
        wrote, write_error = False, None
    else:
        wrote, write_error = write_results(supabase, results, args.emit_ok_events)
    if args.dry_run:
        results.append(
            CheckResult(
                status_key="monitor.supabase_write",
                domain="system",
                component="monitor",
                check_name="supabase_write",
                status="ok",
                severity="info",
                message="Dry-run mode: Supabase writes skipped intentionally",
                details={"dry_run": True},
            )
        )
    elif write_error:
        results.append(
            CheckResult(
                status_key="monitor.supabase_write",
                domain="system",
                component="monitor",
                check_name="supabase_write",
                status="critical",
                severity="critical",
                message=f"Unable to write monitor results to Supabase: {write_error}",
                details={"error": write_error},
            )
        )
    elif wrote:
        results.append(
            CheckResult(
                status_key="monitor.supabase_write",
                domain="system",
                component="monitor",
                check_name="supabase_write",
                status="ok",
                severity="info",
                message="Monitor results written to Supabase",
            )
        )
    print_report(results, args.json)
    if args.strict_exit and any(result.status in {"critical", "unknown"} for result in results):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
