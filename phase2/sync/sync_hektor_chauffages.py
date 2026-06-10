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
DEFAULT_ENV_FILE = ROOT / ".env"
APP_ENV_FILE = ROOT / "apps" / "hektor-v1" / ".env"
DEFAULT_STORAGE_STATE = ROOT / "Console" / "sessions" / "storage_state_admin.json"
DEFAULT_NODE_SCRIPT = ROOT / "Console" / "extract_hektor_chauffage_only.js"
DEFAULT_LOGIN_SCRIPT = ROOT / "Console" / "playwright_login.js"

CURRENT_SCOPE_WHERE = (
    "COALESCE(archive, '0') = '0' "
    "AND COALESCE(detail_statut_name, statut_annonce, '') IN ('Actif', 'Sous offre', 'Sous compromis', 'Estimation')"
)
ALL_SCOPE_WHERE = "hektor_annonce_id IS NOT NULL AND TRIM(CAST(hektor_annonce_id AS TEXT)) <> ''"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
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


def normalize_id(value: object) -> str:
    text = str(value or "").strip()
    if not text.isdigit():
        raise ValueError(f"Identifiant annonce invalide: {value!r}")
    return text


def stable_hash(value: object) -> str:
    if isinstance(value, str):
        raw = value
    else:
        raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def sqlite_ro(path: Path) -> sqlite3.Connection:
    uri = f"file:{path.resolve().as_posix()}?mode=ro&immutable=1"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    return con


def table_exists(con: sqlite3.Connection, name: str) -> bool:
    row = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return bool(row)


def ensure_chauffage_table(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS hektor_annonce_chauffage_detail (
            hektor_annonce_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            chauffage_json TEXT,
            raw_payload_json TEXT,
            source_hash TEXT,
            detail_synced_at TEXT,
            extracted_at TEXT NOT NULL,
            storage_state_path TEXT,
            forbidden403 INTEGER NOT NULL DEFAULT 0,
            elapsed_ms INTEGER,
            error TEXT
        )
        """
    )
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_hektor_annonce_chauffage_detail_status "
        "ON hektor_annonce_chauffage_detail(status, extracted_at)"
    )
    con.commit()


def read_annonces(explicit_ids: list[str], scope: str) -> list[dict[str, Any]]:
    con = sqlite_ro(PHASE2_DB)
    try:
        where = ALL_SCOPE_WHERE if scope == "all" else CURRENT_SCOPE_WHERE
        params: list[object] = []
        if explicit_ids:
            placeholders = ",".join("?" for _ in explicit_ids)
            where = f"CAST(hektor_annonce_id AS TEXT) IN ({placeholders})"
            params.extend(explicit_ids)
        sql = f"""
            SELECT
                app_dossier_id,
                hektor_annonce_id,
                titre_bien,
                detail_raw_json,
                date_maj,
                date_enregistrement_annonce
            FROM app_view_generale
            WHERE {where}
            ORDER BY COALESCE(date_maj, date_enregistrement_annonce, '') DESC, hektor_annonce_id DESC
        """
        rows = con.execute(sql, tuple(params)).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def read_existing_cache() -> dict[str, dict[str, Any]]:
    if not HEKTOR_DB.exists():
        return {}
    con = sqlite_ro(HEKTOR_DB)
    try:
        if not table_exists(con, "hektor_annonce_chauffage_detail"):
            return {}
        rows = con.execute(
            """
            SELECT hektor_annonce_id, status, source_hash, extracted_at
            FROM hektor_annonce_chauffage_detail
            """
        ).fetchall()
        return {
            str(row["hektor_annonce_id"]): {
                "status": row["status"],
                "source_hash": row["source_hash"],
                "extracted_at": row["extracted_at"],
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
    age_seconds = (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()
    return age_seconds > stale_days * 86400


def row_source_hash(row: dict[str, Any]) -> str:
    return stable_hash(
        {
            "detail_raw_json": row.get("detail_raw_json") or "",
            "date_maj": row.get("date_maj") or "",
        }
    )


def select_candidates(
    rows: list[dict[str, Any]],
    existing: dict[str, dict[str, Any]],
    *,
    explicit_ids: list[str],
    force: bool,
    limit: int,
    stale_days: int,
) -> list[dict[str, Any]]:
    explicit_set = set(explicit_ids)
    selected: list[dict[str, Any]] = []
    for row in rows:
        annonce_id = normalize_id(row.get("hektor_annonce_id"))
        source_hash = row_source_hash(row)
        cache = existing.get(annonce_id)
        reason = ""
        if force:
            reason = "force"
        elif annonce_id in explicit_set and not cache:
            reason = "explicit_missing_cache"
        elif annonce_id in explicit_set:
            reason = "explicit"
        elif not cache:
            reason = "missing_cache"
        elif cache.get("status") != "done":
            if is_stale(cache.get("extracted_at"), stale_days):
                reason = "previous_not_done"
        elif cache.get("source_hash") != source_hash:
            reason = "api_changed"
        elif is_stale(cache.get("extracted_at"), stale_days):
            reason = "stale_cache"
        if not reason:
            continue
        selected.append({**row, "hektor_annonce_id": annonce_id, "source_hash": source_hash, "reason": reason})
        if limit > 0 and len(selected) >= limit:
            break
    return selected


def supabase_rest_get(pathname: str, query: dict[str, str]) -> object:
    supabase_url = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").strip()
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not supabase_url or not service_role_key:
        raise RuntimeError("SUPABASE_URL/VITE_SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY requis pour verifier les jobs")
    url = f"{supabase_url.rstrip('/')}/rest/v1/{pathname.lstrip('/')}"
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
        raise RuntimeError(f"Supabase REST error {exc.code} on {pathname}: {detail}") from exc


def require_no_console_jobs() -> list[dict[str, Any]]:
    rows = supabase_rest_get(
        "app_console_job",
        {
            "select": "id,job_type,status,hektor_annonce_id,created_at",
            "status": "in.(pending,running)",
            "order": "created_at.asc",
            "limit": "20",
        },
    )
    pending = rows if isinstance(rows, list) else []
    if pending:
        raise RuntimeError(f"Jobs console pending/running presents: {json.dumps(pending, ensure_ascii=True)}")
    return pending


def load_json_from_stdout(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.rfind("{")
        if start >= 0:
            return json.loads(text[start:])
        raise


def run_login_refresh(node_exe: str, storage_state: Path, timeout_seconds: int) -> None:
    env = dict(os.environ)
    env["CONSOLE_STORAGE_STATE_PATH"] = str(storage_state)
    completed = subprocess.run(
        [node_exe, str(DEFAULT_LOGIN_SCRIPT)],
        cwd=str(ROOT / "Console"),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "Echec refresh session Hektor").strip()[-3000:])


def run_node_batch(
    *,
    node_exe: str,
    script: Path,
    annonce_ids: list[str],
    storage_state: Path,
    timeout_seconds: int,
    delay_seconds: float,
) -> dict[str, Any]:
    cmd = [
        node_exe,
        str(script),
        "--storage-state",
        str(storage_state),
        "--timeout-ms",
        str(max(1, timeout_seconds) * 1000),
        "--delay-ms",
        str(int(max(0.0, delay_seconds) * 1000)),
    ]
    for annonce_id in annonce_ids:
        cmd.extend(["--annonce-id", annonce_id])
    completed = subprocess.run(
        cmd,
        cwd=str(ROOT / "Console"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=max(1, timeout_seconds) * max(1, len(annonce_ids)) + 30,
    )
    payload = load_json_from_stdout(completed.stdout) if completed.stdout.strip() else {}
    if completed.returncode == 3 or payload.get("status") == "stopped_on_403":
        raise PermissionError(json.dumps(payload, ensure_ascii=True))
    if completed.returncode == 2 or payload.get("status") == "session_expired":
        raise RuntimeError("Session Hektor expiree")
    if completed.returncode != 0:
        error = payload.get("error") or completed.stderr or completed.stdout or "Extraction chauffage en erreur"
        raise RuntimeError(str(error).strip())
    return payload


def run_node_batch_with_recovery(
    *,
    args: argparse.Namespace,
    ids: list[str],
    storage_state: Path,
) -> dict[str, Any]:
    """Lance un lot node en recuperant UNE fois d'une session expiree.

    Hektor signale une session admin expiree de deux facons :
    - une page de login en HTTP 200 -> RuntimeError("Session Hektor expiree") ;
    - un HTTP 403 nu sur l'endpoint ajax -> PermissionError (stopped_on_403).

    Si --refresh-session-on-expired est actif, on rafraichit la session et on
    rejoue le lot UNE seule fois pour l'un ou l'autre des signaux. Un second 403
    est traite comme un vrai blocage Hektor et propage, donc l'arret dur de
    securite s'applique toujours.
    """
    refreshed = False
    while True:
        try:
            return run_node_batch(
                node_exe=args.node_exe,
                script=args.node_script,
                annonce_ids=ids,
                storage_state=storage_state,
                timeout_seconds=args.timeout_seconds,
                delay_seconds=args.delay_seconds,
            )
        except RuntimeError as exc:
            if args.refresh_session_on_expired and not refreshed and "Session Hektor expiree" in str(exc):
                print("[recovery] session expiree (page login) -> refresh + retry une fois", file=sys.stderr)
                run_login_refresh(args.node_exe, storage_state, args.timeout_seconds)
                refreshed = True
                continue
            raise
        except PermissionError:
            if args.refresh_session_on_expired and not refreshed:
                print("[recovery] 403 Hektor -> tentative refresh session + retry une fois", file=sys.stderr)
                run_login_refresh(args.node_exe, storage_state, args.timeout_seconds)
                refreshed = True
                continue
            raise


def store_result(con: sqlite3.Connection, row: dict[str, Any], result: dict[str, Any], storage_state: Path) -> None:
    status = str(result.get("status") or "error")
    chauffage = result.get("chauffage_console_json")
    con.execute(
        """
        INSERT INTO hektor_annonce_chauffage_detail (
            hektor_annonce_id,
            status,
            chauffage_json,
            raw_payload_json,
            source_hash,
            detail_synced_at,
            extracted_at,
            storage_state_path,
            forbidden403,
            elapsed_ms,
            error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(hektor_annonce_id) DO UPDATE SET
            status=excluded.status,
            chauffage_json=excluded.chauffage_json,
            raw_payload_json=excluded.raw_payload_json,
            source_hash=excluded.source_hash,
            detail_synced_at=excluded.detail_synced_at,
            extracted_at=excluded.extracted_at,
            storage_state_path=excluded.storage_state_path,
            forbidden403=excluded.forbidden403,
            elapsed_ms=excluded.elapsed_ms,
            error=excluded.error
        """,
        (
            row["hektor_annonce_id"],
            status,
            json.dumps(chauffage, ensure_ascii=True, separators=(",", ":")) if chauffage is not None else None,
            json.dumps(result, ensure_ascii=True, separators=(",", ":")),
            row["source_hash"],
            row.get("date_maj"),
            str(result.get("extracted_at") or now_iso()),
            str(storage_state),
            1 if status == "stopped_on_403" else 0,
            int(result.get("elapsed_ms") or 0),
            result.get("error"),
        ),
    )
    con.commit()


def iter_batches(values: list[dict[str, Any]], batch_size: int):
    size = max(1, batch_size)
    for index in range(0, len(values), size):
        yield values[index : index + size]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extrait rapidement les lignes chauffage Hektor depuis le seul groupe equipements.")
    parser.add_argument("--hektor-annonce-id", action="append", default=[], help="Annonce Hektor ciblee. Peut etre repete.")
    parser.add_argument("--scope", choices=("all", "current"), default="current")
    parser.add_argument("--limit", type=int, default=100, help="Nombre maximum d'annonces. 0 = aucune limite.")
    parser.add_argument("--stale-days", type=int, default=30, help="Rejouer les caches plus vieux que N jours. 0 = jamais par age.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-job-check", action="store_true")
    parser.add_argument("--storage-state", type=Path, default=DEFAULT_STORAGE_STATE)
    parser.add_argument("--node-exe", default=os.environ.get("CONSOLE_NODE_EXE") or "node.exe")
    parser.add_argument("--node-script", type=Path, default=DEFAULT_NODE_SCRIPT)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--delay-seconds", type=float, default=0.5)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--batch-pause-seconds", type=int, default=30)
    parser.add_argument("--refresh-session-on-expired", action="store_true")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_env_file(args.env_file)
    load_env_file(APP_ENV_FILE)

    explicit_ids = [normalize_id(value) for value in args.hektor_annonce_id]
    storage_state = args.storage_state.resolve()
    if not storage_state.exists() and not args.dry_run:
        raise RuntimeError(f"Session Playwright introuvable: {storage_state}")

    rows = read_annonces(explicit_ids, args.scope)
    existing = read_existing_cache()
    candidates = select_candidates(
        rows,
        existing,
        explicit_ids=explicit_ids,
        force=args.force,
        limit=max(0, args.limit),
        stale_days=max(0, args.stale_days),
    )
    by_id = {row["hektor_annonce_id"]: row for row in candidates}
    summary: dict[str, Any] = {
        "dry_run": args.dry_run,
        "scope": args.scope,
        "selected": len(candidates),
        "storage_state": str(storage_state),
        "candidates": [
            {
                "hektor_annonce_id": item["hektor_annonce_id"],
                "app_dossier_id": item.get("app_dossier_id"),
                "reason": item.get("reason"),
                "titre_bien": item.get("titre_bien"),
            }
            for item in candidates
        ],
        "extracted": [],
        "errors": [],
        "skipped": len(rows) - len(candidates),
        "elapsed_ms": 0,
    }

    if args.dry_run or not candidates:
        print(json.dumps(summary, ensure_ascii=True, indent=2))
        return

    if not args.skip_job_check:
        require_no_console_jobs()

    started = time.perf_counter()
    con = sqlite3.connect(HEKTOR_DB)
    ensure_chauffage_table(con)
    try:
        batches = list(iter_batches(candidates, args.batch_size))
        for batch_index, batch in enumerate(batches, start=1):
            ids = [row["hektor_annonce_id"] for row in batch]
            try:
                payload = run_node_batch_with_recovery(
                    args=args,
                    ids=ids,
                    storage_state=storage_state,
                )
                for result in payload.get("results") or []:
                    annonce_id = normalize_id(result.get("hektor_annonce_id"))
                    row = by_id.get(annonce_id)
                    if not row:
                        continue
                    store_result(con, row, result, storage_state)
                    summary["extracted"].append(
                        {
                            "hektor_annonce_id": annonce_id,
                            "status": result.get("status"),
                            "chauffage_count": result.get("chauffage_count"),
                            "elapsed_ms": result.get("elapsed_ms"),
                        }
                    )
            except PermissionError as exc:
                error_text = str(exc)
                for row in batch:
                    result = {
                        "hektor_annonce_id": row["hektor_annonce_id"],
                        "status": "stopped_on_403",
                        "error": error_text,
                        "extracted_at": now_iso(),
                    }
                    store_result(con, row, result, storage_state)
                summary["stopped_on_403"] = {"batch": ids, "error": error_text}
                summary["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
                print(json.dumps(summary, ensure_ascii=True, indent=2))
                raise SystemExit(3) from exc
            except Exception as exc:
                error_text = str(exc)
                for row in batch:
                    result = {
                        "hektor_annonce_id": row["hektor_annonce_id"],
                        "status": "error",
                        "error": error_text,
                        "extracted_at": now_iso(),
                    }
                    store_result(con, row, result, storage_state)
                    summary["errors"].append({"hektor_annonce_id": row["hektor_annonce_id"], "error": error_text})

            if batch_index < len(batches):
                time.sleep(max(0, args.batch_pause_seconds))
    finally:
        con.close()

    summary["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
