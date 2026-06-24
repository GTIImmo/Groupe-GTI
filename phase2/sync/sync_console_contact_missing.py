"""Sync « champs manquants » contact (naissance / lieu / matrimonial) depuis la
Console Hektor — parité avec le chauffage (sync_hektor_chauffages.py).

Hektor ne renvoie PAS ces champs par l'API ContactById. Ce sync scrape le
formulaire contact via Console/extract_hektor_contact_missing.js (LECTURE SEULE),
puis écrit le résultat dans Supabase app_contact_current — en respectant le
garde-fou DIRTY (édition app en attente non écrasée) et SANS écraser une valeur
existante par du vide.

Anti-bugs (cf. autres workers) :
- login 2FA : réutilise playwright_login.js corrigé (via --refresh-session-on-expired) ;
- pas de disparition : UPDATE de 3 colonnes app-owned, jamais de delete ;
- pas de souci négo/agence : lecture seule, aucune impersonation/écriture Hektor ;
- pas de timeout : petits lots ; dirty-skip : ne touche pas un contact en édition.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NODE_SCRIPT = ROOT / "Console" / "extract_hektor_contact_missing.js"
DEFAULT_LOGIN_SCRIPT = ROOT / "Console" / "playwright_login.js"
DEFAULT_STORAGE_STATE = ROOT / "Console" / "sessions" / "storage_state_admin.json"
ENV_FILES = (ROOT / ".env", ROOT / "Console" / ".env", ROOT / "apps" / "hektor-v1" / ".env")
APP_OWNED_FIELDS = ("birth_date", "birth_place", "marital_status")


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_json_from_stdout(stdout: str) -> dict[str, Any]:
    for chunk in reversed(stdout.strip().splitlines()):
        chunk = chunk.strip()
        if chunk.startswith("{"):
            try:
                return json.loads(chunk)
            except json.JSONDecodeError:
                continue
    return {}


# ---------------------------------------------------------------- Supabase REST
class Supabase:
    def __init__(self) -> None:
        self.url = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").rstrip("/")
        self.key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
        if not self.url or not self.key:
            raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY requis (.env)")

    def _req(self, method: str, path: str, body: Any = None, prefer: str | None = None) -> Any:
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(f"{self.url}/rest/v1/{path}", data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else None

    def eligible_contact_ids(self, limit: int) -> list[str]:
        path = f"app_contact_current?select=hektor_contact_id&supabase_sync_eligible=eq.true&limit={int(limit)}"
        rows = self._req("GET", path) or []
        return [str(r["hektor_contact_id"]) for r in rows if r.get("hektor_contact_id")]

    def dirty_contact_ids(self, contact_ids: list[str]) -> set[str]:
        if not contact_ids:
            return set()
        encoded = ",".join(urllib.parse.quote(c, safe="") for c in contact_ids)
        rows = self._req("GET", f"app_contact_pending?select=hektor_contact_id&hektor_contact_id=in.({encoded})") or []
        return {str(r["hektor_contact_id"]) for r in rows if r.get("hektor_contact_id")}

    def patch_contact(self, contact_id: str, fields: dict[str, str]) -> None:
        path = f"app_contact_current?hektor_contact_id=eq.{urllib.parse.quote(contact_id, safe='')}"
        self._req("PATCH", path, body=fields, prefer="return=minimal")


# ---------------------------------------------------------------- Node scraper
def run_login_refresh(node_exe: str, storage_state: Path, timeout_seconds: int) -> None:
    env = dict(os.environ)
    env["CONSOLE_STORAGE_STATE_PATH"] = str(storage_state)
    subprocess.run(
        [node_exe, str(DEFAULT_LOGIN_SCRIPT)],
        cwd=str(ROOT / "Console"), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=max(60, timeout_seconds * 3),
    )


def run_node_batch(args: argparse.Namespace, contact_ids: list[str]) -> dict[str, Any]:
    cmd = [
        args.node_exe, str(args.node_script),
        "--storage-state", str(args.storage_state),
        "--timeout-ms", str(max(1, args.timeout_seconds) * 1000),
        "--delay-ms", str(int(max(0.0, args.delay_seconds) * 1000)),
    ]
    for cid in contact_ids:
        cmd.extend(["--contact-id", cid])
    completed = subprocess.run(
        cmd, cwd=str(ROOT / "Console"), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        timeout=max(1, args.timeout_seconds) * max(1, len(contact_ids)) + 30,
    )
    payload = load_json_from_stdout(completed.stdout) if completed.stdout.strip() else {}
    if completed.returncode == 3 or payload.get("status") == "stopped_on_403":
        raise PermissionError(json.dumps(payload, ensure_ascii=True))
    if completed.returncode == 2 or payload.get("status") == "session_expired":
        raise RuntimeError("Session Hektor expiree")
    if completed.returncode != 0:
        raise RuntimeError(str(payload.get("error") or completed.stderr or completed.stdout or "scrape contact en erreur").strip())
    return payload


def run_node_batch_with_recovery(args: argparse.Namespace, contact_ids: list[str]) -> dict[str, Any]:
    refreshed = False
    while True:
        try:
            return run_node_batch(args, contact_ids)
        except (RuntimeError, PermissionError) as exc:
            expired = isinstance(exc, PermissionError) or "Session Hektor expiree" in str(exc)
            if args.refresh_session_on_expired and not refreshed and expired:
                print("[recovery] session expiree -> refresh login 2FA + retry une fois", file=sys.stderr)
                run_login_refresh(args.node_exe, args.storage_state, args.timeout_seconds)
                refreshed = True
                continue
            raise


def chunked(items: list[str], size: int):
    for i in range(0, len(items), max(1, size)):
        yield items[i:i + max(1, size)]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scrape naissance/lieu/matrimonial contact depuis Hektor (Console) -> Supabase.")
    p.add_argument("--contact-id", action="append", default=[], help="Contact(s) explicite(s). Sinon --scope.")
    p.add_argument("--scope", choices=["eligible"], default="eligible")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--batch-size", type=int, default=10)
    p.add_argument("--delay-seconds", type=float, default=0.4)
    p.add_argument("--timeout-seconds", type=int, default=60)
    p.add_argument("--storage-state", type=Path, default=DEFAULT_STORAGE_STATE)
    p.add_argument("--node-exe", default=os.environ.get("CONSOLE_NODE_EXE", "node"))
    p.add_argument("--node-script", type=Path, default=DEFAULT_NODE_SCRIPT)
    p.add_argument("--refresh-session-on-expired", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="Scrape mais n'écrit PAS dans Supabase.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    for env_file in ENV_FILES:
        load_env_file(env_file)
    sb = Supabase()

    contact_ids = [str(c).strip() for c in args.contact_id if str(c).strip().isdigit()]
    if not contact_ids:
        contact_ids = sb.eligible_contact_ids(args.limit)
    if not contact_ids:
        print(json.dumps({"selected": 0, "note": "aucun contact"}))
        return 0

    dirty = sb.dirty_contact_ids(contact_ids)
    scraped, written, skipped_dirty, empty, errors = 0, 0, 0, 0, 0
    for batch in chunked(contact_ids, args.batch_size):
        payload = run_node_batch_with_recovery(args, batch)
        for result in payload.get("results", []):
            cid = str(result.get("hektor_contact_id") or "")
            if not cid or result.get("status") != "done":
                errors += 1 if result.get("status") not in (None, "done") else 0
                continue
            scraped += 1
            if cid in dirty:
                skipped_dirty += 1
                continue
            fields = {f: result.get(f) for f in APP_OWNED_FIELDS if str(result.get(f) or "").strip()}
            if not fields:
                empty += 1
                continue
            if args.dry_run:
                print(f"[dry-run] {cid} -> {fields}")
                written += 1
                continue
            try:
                sb.patch_contact(cid, fields)
                written += 1
            except urllib.error.HTTPError as exc:
                errors += 1
                print(f"[error] PATCH {cid} HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:200]}", file=sys.stderr)

    print(json.dumps({
        "selected": len(contact_ids), "scraped": scraped, "written": written,
        "skipped_dirty": skipped_dirty, "empty": empty, "errors": errors, "dry_run": args.dry_run,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
