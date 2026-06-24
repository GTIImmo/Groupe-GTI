"""Sync « champs manquants » contact (naissance / lieu / matrimonial) depuis la
Console Hektor — CALQUÉ sur le chauffage (sync_hektor_chauffages.py), avec CACHE
LOCAL RESUMABLE.

Hektor ne renvoie PAS ces champs par l'API ContactById ; ils existent dans le
formulaire web. Ce sync scrape le formulaire (LECTURE SEULE) via
Console/extract_hektor_contact_missing.js, met en cache local
`hektor_contact_missing_detail` (resumable : on ne re-scrape pas ce qui est déjà
`done` et inchangé), puis pousse vers Supabase app_contact_current (DIRTY-SKIP +
jamais écraser par du vide).

Modèle = NOTE_EXTRACTION_CHAUFFAGE_HEKTOR : run global en vagues, resumable via
le cache (récents d'abord car ORDER BY date_maj DESC).

Anti-bugs : lecture seule (ni négo/agence ni disparition), login 2FA réutilisé,
petits lots, dirty-skip.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
DEFAULT_NODE_SCRIPT = ROOT / "Console" / "extract_hektor_contact_missing.js"
DEFAULT_LOGIN_SCRIPT = ROOT / "Console" / "playwright_login.js"
DEFAULT_STORAGE_STATE = ROOT / "Console" / "sessions" / "storage_state_admin.json"
ENV_FILES = (ROOT / ".env", ROOT / "Console" / ".env", ROOT / "apps" / "hektor-v1" / ".env")
APP_OWNED_FIELDS = ("birth_date", "birth_place", "marital_status")
ELIGIBLE_SCOPE_WHERE = "COALESCE(supabase_sync_eligible, 0) = 1"
ALL_SCOPE_WHERE = "NULLIF(TRIM(hektor_contact_id), '') IS NOT NULL"


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


def stable_hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()


def sqlite_ro(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def table_exists(con: sqlite3.Connection, name: str) -> bool:
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


# --------------------------------------------------------------- cache local
def ensure_contact_missing_table(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS hektor_contact_missing_detail (
            hektor_contact_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            birth_date TEXT,
            birth_place TEXT,
            marital_status TEXT,
            source_hash TEXT,
            extracted_at TEXT NOT NULL,
            storage_state_path TEXT,
            forbidden403 INTEGER NOT NULL DEFAULT 0,
            elapsed_ms INTEGER,
            error TEXT
        )
        """
    )
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_hektor_contact_missing_status "
        "ON hektor_contact_missing_detail(status, extracted_at)"
    )
    con.commit()


def read_contacts(explicit_ids: list[str], scope: str) -> list[dict[str, Any]]:
    con = sqlite_ro(PHASE2_DB)
    try:
        where = ALL_SCOPE_WHERE if scope == "all" else ELIGIBLE_SCOPE_WHERE
        params: list[object] = []
        if explicit_ids:
            placeholders = ",".join("?" for _ in explicit_ids)
            where = f"CAST(hektor_contact_id AS TEXT) IN ({placeholders})"
            params.extend(explicit_ids)
        sql = f"""
            SELECT hektor_contact_id, date_maj
            FROM app_contact_current
            WHERE {where}
            ORDER BY COALESCE(date_maj, '') DESC, CAST(hektor_contact_id AS INTEGER) DESC
        """
        return [dict(row) for row in con.execute(sql, tuple(params)).fetchall()]
    finally:
        con.close()


def read_existing_cache() -> dict[str, dict[str, Any]]:
    if not HEKTOR_DB.exists():
        return {}
    con = sqlite_ro(HEKTOR_DB)
    try:
        if not table_exists(con, "hektor_contact_missing_detail"):
            return {}
        rows = con.execute(
            "SELECT hektor_contact_id, status, source_hash, extracted_at FROM hektor_contact_missing_detail"
        ).fetchall()
        return {
            str(row["hektor_contact_id"]): {
                "status": row["status"], "source_hash": row["source_hash"], "extracted_at": row["extracted_at"],
            }
            for row in rows
        }
    finally:
        con.close()


def parse_iso(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def is_stale(extracted_at: object, stale_days: int) -> bool:
    if stale_days <= 0:
        return False
    parsed = parse_iso(extracted_at)
    if not parsed:
        return True
    age = (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()
    return age > stale_days * 86400


def row_source_hash(row: dict[str, Any]) -> str:
    return stable_hash({"date_maj": row.get("date_maj") or ""})


def select_candidates(rows, existing, *, explicit_ids, force, limit, stale_days):
    explicit_set = set(explicit_ids)
    selected = []
    for row in rows:
        cid = str(row.get("hektor_contact_id") or "").strip()
        if not cid:
            continue
        source_hash = row_source_hash(row)
        cache = existing.get(cid)
        reason = ""
        if force:
            reason = "force"
        elif cid in explicit_set and not cache:
            reason = "explicit_missing_cache"
        elif cid in explicit_set:
            reason = "explicit"
        elif not cache:
            reason = "missing_cache"
        elif cache.get("status") != "done":
            if is_stale(cache.get("extracted_at"), stale_days):
                reason = "previous_not_done"
        elif cache.get("source_hash") != source_hash:
            reason = "source_changed"
        elif is_stale(cache.get("extracted_at"), stale_days):
            reason = "stale_cache"
        if not reason:
            continue
        selected.append({"hektor_contact_id": cid, "source_hash": source_hash, "reason": reason})
        if limit > 0 and len(selected) >= limit:
            break
    return selected


def store_result(con: sqlite3.Connection, result: dict[str, Any], source_hash: str, storage_state: Path) -> None:
    con.execute(
        """
        INSERT INTO hektor_contact_missing_detail (
            hektor_contact_id, status, birth_date, birth_place, marital_status,
            source_hash, extracted_at, storage_state_path, forbidden403, elapsed_ms, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(hektor_contact_id) DO UPDATE SET
            status=excluded.status, birth_date=excluded.birth_date, birth_place=excluded.birth_place,
            marital_status=excluded.marital_status, source_hash=excluded.source_hash,
            extracted_at=excluded.extracted_at, storage_state_path=excluded.storage_state_path,
            forbidden403=excluded.forbidden403, elapsed_ms=excluded.elapsed_ms, error=excluded.error
        """,
        (
            str(result.get("hektor_contact_id")), str(result.get("status") or "error"),
            result.get("birth_date") or None, result.get("birth_place") or None, result.get("marital_status") or None,
            source_hash, result.get("extracted_at") or datetime.now(timezone.utc).isoformat(),
            str(storage_state), 1 if result.get("status") == "stopped_on_403" else 0,
            result.get("elapsed_ms"), result.get("error"),
        ),
    )


# --------------------------------------------------------------- Supabase REST
class Supabase:
    def __init__(self) -> None:
        self.url = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").rstrip("/")
        self.key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
        if not self.url or not self.key:
            raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY requis (.env)")

    def _req(self, method, path, body=None, prefer=None):
        headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        if prefer:
            headers["Prefer"] = prefer
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(f"{self.url}/rest/v1/{path}", data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else None

    def dirty_contact_ids(self, contact_ids: list[str]) -> set[str]:
        out: set[str] = set()
        for i in range(0, len(contact_ids), 200):
            chunk = contact_ids[i:i + 200]
            encoded = ",".join(urllib.parse.quote(c, safe="") for c in chunk)
            rows = self._req("GET", f"app_contact_pending?select=hektor_contact_id&hektor_contact_id=in.({encoded})") or []
            out |= {str(r["hektor_contact_id"]) for r in rows if r.get("hektor_contact_id")}
        return out

    def patch_contact(self, contact_id: str, fields: dict[str, str]) -> None:
        path = f"app_contact_current?hektor_contact_id=eq.{urllib.parse.quote(contact_id, safe='')}"
        self._req("PATCH", path, body=fields, prefer="return=minimal")


# --------------------------------------------------------------- node scraper
def run_login_refresh(node_exe: str, storage_state: Path, timeout_seconds: int) -> None:
    env = dict(os.environ)
    env["CONSOLE_STORAGE_STATE_PATH"] = str(storage_state)
    subprocess.run([node_exe, str(DEFAULT_LOGIN_SCRIPT)], cwd=str(ROOT / "Console"), env=env,
                   capture_output=True, text=True, encoding="utf-8", errors="replace",
                   timeout=max(60, timeout_seconds * 3))


def run_node_batch(args: argparse.Namespace, contact_ids: list[str]) -> dict[str, Any]:
    cmd = [args.node_exe, str(args.node_script), "--storage-state", str(args.storage_state),
           "--timeout-ms", str(max(1, args.timeout_seconds) * 1000),
           "--delay-ms", str(int(max(0.0, args.delay_seconds) * 1000))]
    for cid in contact_ids:
        cmd.extend(["--contact-id", cid])
    completed = subprocess.run(cmd, cwd=str(ROOT / "Console"), capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               timeout=max(1, args.timeout_seconds) * max(1, len(contact_ids)) + 30)
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


def push_cache_to_supabase(sb: Supabase, contact_ids: list[str], dry_run: bool) -> dict[str, int]:
    """Pousse les champs app-owned du cache local -> Supabase, DIRTY-SKIP + non-vide."""
    if not contact_ids:
        return {"written": 0, "skipped_dirty": 0, "empty": 0, "errors": 0}
    con = sqlite_ro(HEKTOR_DB)
    try:
        placeholders = ",".join("?" for _ in contact_ids)
        rows = con.execute(
            f"SELECT hektor_contact_id, birth_date, birth_place, marital_status "
            f"FROM hektor_contact_missing_detail "
            f"WHERE status='done' AND hektor_contact_id IN ({placeholders})",
            tuple(contact_ids),
        ).fetchall()
    finally:
        con.close()
    dirty = sb.dirty_contact_ids([str(r["hektor_contact_id"]) for r in rows])
    written = skipped_dirty = empty = errors = 0
    for row in rows:
        cid = str(row["hektor_contact_id"])
        if cid in dirty:
            skipped_dirty += 1
            continue
        fields = {f: row[f] for f in APP_OWNED_FIELDS if str(row[f] or "").strip()}
        if not fields:
            empty += 1
            continue
        if dry_run:
            written += 1
            continue
        try:
            sb.patch_contact(cid, fields)
            written += 1
        except urllib.error.HTTPError as exc:
            errors += 1
            print(f"[error] PATCH {cid} HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:200]}", file=sys.stderr)
    return {"written": written, "skipped_dirty": skipped_dirty, "empty": empty, "errors": errors}


def chunked(items, size):
    for i in range(0, len(items), max(1, size)):
        yield items[i:i + max(1, size)]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scrape naissance/lieu/matrimonial contact (cache local resumable) -> Supabase.")
    p.add_argument("--contact-id", action="append", default=[])
    p.add_argument("--scope", choices=["eligible", "all"], default="eligible")
    p.add_argument("--limit", type=int, default=50, help="Max contacts à scraper cette exécution. 0 = aucune limite.")
    p.add_argument("--stale-days", type=int, default=30)
    p.add_argument("--force", action="store_true")
    p.add_argument("--batch-size", type=int, default=10)
    p.add_argument("--batch-pause-seconds", type=int, default=0)
    p.add_argument("--delay-seconds", type=float, default=0.4)
    p.add_argument("--timeout-seconds", type=int, default=60)
    p.add_argument("--storage-state", type=Path, default=DEFAULT_STORAGE_STATE)
    p.add_argument("--node-exe", default=os.environ.get("CONSOLE_NODE_EXE", "node"))
    p.add_argument("--node-script", type=Path, default=DEFAULT_NODE_SCRIPT)
    p.add_argument("--refresh-session-on-expired", action="store_true")
    p.add_argument("--skip-push", action="store_true", help="Scrape vers le cache mais ne pousse pas vers Supabase.")
    p.add_argument("--dry-run", action="store_true", help="Sélectionne mais ne scrape ni n'écrit (contrôle).")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    for env_file in ENV_FILES:
        load_env_file(env_file)

    explicit = [str(c).strip() for c in args.contact_id if str(c).strip().isdigit()]
    rows = read_contacts(explicit, args.scope)
    existing = read_existing_cache()
    candidates = select_candidates(rows, existing, explicit_ids=explicit, force=args.force,
                                   limit=args.limit, stale_days=args.stale_days)
    if args.dry_run:
        full = select_candidates(rows, existing, explicit_ids=explicit, force=args.force, limit=0, stale_days=args.stale_days)
        print(json.dumps({
            "scope": args.scope, "in_scope": len(rows),
            "to_scrape_total": len(full), "already_done": len(rows) - len(full),
            "would_scrape_this_run": (min(len(full), args.limit) if args.limit > 0 else len(full)),
            "dry_run": True,
        }, ensure_ascii=False))
        return 0
    if not candidates:
        print(json.dumps({"scope": args.scope, "in_scope": len(rows), "candidates": 0, "note": "rien à scraper (cache à jour)"}))
        return 0

    HEKTOR_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(HEKTOR_DB)
    ensure_contact_missing_table(con)
    hash_by_id = {c["hektor_contact_id"]: c["source_hash"] for c in candidates}
    cand_ids = [c["hektor_contact_id"] for c in candidates]

    scraped = errors = 0
    started = time.time()
    try:
        for batch in chunked(cand_ids, args.batch_size):
            payload = run_node_batch_with_recovery(args, batch)
            for result in payload.get("results", []):
                cid = str(result.get("hektor_contact_id") or "")
                if not cid:
                    continue
                store_result(con, result, hash_by_id.get(cid, ""), args.storage_state)
                if result.get("status") == "done":
                    scraped += 1
                else:
                    errors += 1
            con.commit()
            if args.batch_pause_seconds > 0:
                time.sleep(args.batch_pause_seconds)
    finally:
        con.close()

    push = {"written": 0, "skipped_dirty": 0, "empty": 0, "errors": 0}
    if not args.skip_push:
        push = push_cache_to_supabase(Supabase(), cand_ids, args.dry_run)

    print(json.dumps({
        "scope": args.scope, "in_scope": len(rows), "candidates": len(candidates),
        "scraped": scraped, "scrape_errors": errors, "push": push,
        "elapsed_s": round(time.time() - started, 1),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
