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
DEFAULT_NODE_SCRIPT = ROOT / "Console" / "extract_hektor_missing_fields.js"
DEFAULT_LOGIN_SCRIPT = ROOT / "Console" / "playwright_login.js"

ANNONCES_SCOPE_WHERE = (
    "COALESCE(archive, '0') = '0' "
    "AND COALESCE(detail_statut_name, statut_annonce, '') IN ('Actif', 'Sous offre', 'Sous compromis', 'Estimation')"
)
ALL_ANNONCES_SCOPE_WHERE = (
    "hektor_annonce_id IS NOT NULL "
    "AND TRIM(CAST(hektor_annonce_id AS TEXT)) <> ''"
)


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


def stable_hash(value: object) -> str:
    if isinstance(value, str):
        raw = value
    else:
        raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_id(value: object) -> str:
    text = str(value or "").strip()
    if not text.isdigit():
        raise ValueError(f"Identifiant annonce invalide: {value!r}")
    return text


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


def sqlite_ro(path: Path) -> sqlite3.Connection:
    uri = f"file:{path.resolve().as_posix()}?mode=ro&immutable=1"
    return sqlite3.connect(uri, uri=True)


def attach_hektor_ro(con: sqlite3.Connection) -> None:
    uri = f"file:{HEKTOR_DB.resolve().as_posix()}?mode=ro&immutable=1"
    con.execute("ATTACH DATABASE ? AS hektor", (uri,))


def table_exists(con: sqlite3.Connection, name: str) -> bool:
    row = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return bool(row)


def ensure_console_table(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS hektor_annonce_console_detail (
            hektor_annonce_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            console_payload_json TEXT,
            source_hash TEXT,
            detail_synced_at TEXT,
            extracted_at TEXT NOT NULL,
            storage_state_path TEXT,
            export_root TEXT,
            forbidden403 INTEGER NOT NULL DEFAULT 0,
            error TEXT
        )
        """
    )
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_hektor_annonce_console_detail_status "
        "ON hektor_annonce_console_detail(status, extracted_at)"
    )
    con.commit()


def read_annonces(explicit_ids: list[str], annonce_scope: str) -> list[dict[str, Any]]:
    con = sqlite_ro(PHASE2_DB)
    try:
        attach_hektor_ro(con)
        where = ALL_ANNONCES_SCOPE_WHERE if annonce_scope == "all" else ANNONCES_SCOPE_WHERE
        params: list[object] = []
        if explicit_ids:
            placeholders = ",".join("?" for _ in explicit_ids)
            where = f"hektor_annonce_id IN ({placeholders})"
            params.extend(int(value) for value in explicit_ids)
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
        cursor = con.execute(sql, tuple(params))
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        con.close()


def read_existing_cache() -> dict[str, dict[str, Any]]:
    if not HEKTOR_DB.exists():
        return {}
    con = sqlite_ro(HEKTOR_DB)
    try:
        if not table_exists(con, "hektor_annonce_console_detail"):
            return {}
        rows = con.execute(
            """
            SELECT hektor_annonce_id, status, source_hash, extracted_at
            FROM hektor_annonce_console_detail
            """
        ).fetchall()
        return {
            str(row[0]): {
                "status": row[1],
                "source_hash": row[2],
                "extracted_at": row[3],
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
        source_hash = stable_hash(str(row.get("detail_raw_json") or ""))
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


def run_login_refresh(node_exe: str, storage_state: Path, timeout_seconds: int) -> None:
    env = dict(os.environ)
    env["CONSOLE_STORAGE_STATE_PATH"] = str(storage_state)
    completed = subprocess.run(
        [node_exe, str(DEFAULT_LOGIN_SCRIPT)],
        cwd=str(ROOT / "Console"),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "Echec refresh session Hektor").strip()[-3000:])


def run_node_extractor(
    *,
    node_exe: str,
    script: Path,
    annonce_id: str,
    storage_state: Path,
    timeout_seconds: int,
    write_debug: bool,
) -> dict[str, Any]:
    cmd = [
        node_exe,
        str(script),
        "--annonce-id",
        annonce_id,
        "--storage-state",
        str(storage_state),
    ]
    if write_debug:
        cmd.append("--write-debug")
    completed = subprocess.run(
        cmd,
        cwd=str(ROOT / "Console"),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    payload = load_json_from_stdout(completed.stdout) if completed.stdout.strip() else {}
    if completed.returncode != 0:
        status = str(payload.get("status") or "")
        error = str(payload.get("error") or completed.stderr or completed.stdout or "Extraction console en erreur").strip()
        if status == "stopped_on_403":
            raise PermissionError(error)
        raise RuntimeError(error)
    return payload


def store_result(con: sqlite3.Connection, row: dict[str, Any], payload: dict[str, Any], storage_state: Path) -> None:
    status = str(payload.get("status") or "error")
    con.execute(
        """
        INSERT INTO hektor_annonce_console_detail (
            hektor_annonce_id,
            status,
            console_payload_json,
            source_hash,
            detail_synced_at,
            extracted_at,
            storage_state_path,
            export_root,
            forbidden403,
            error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(hektor_annonce_id) DO UPDATE SET
            status=excluded.status,
            console_payload_json=excluded.console_payload_json,
            source_hash=excluded.source_hash,
            detail_synced_at=excluded.detail_synced_at,
            extracted_at=excluded.extracted_at,
            storage_state_path=excluded.storage_state_path,
            export_root=excluded.export_root,
            forbidden403=excluded.forbidden403,
            error=excluded.error
        """,
        (
            row["hektor_annonce_id"],
            status,
            json.dumps(payload, ensure_ascii=True, separators=(",", ":")) if payload else None,
            row["source_hash"],
            row.get("date_maj"),
            str(payload.get("extracted_at") or now_iso()),
            str(storage_state),
            str(payload.get("exportRoot") or ""),
            1 if status == "stopped_on_403" else 0,
            payload.get("error"),
        ),
    )
    con.commit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Complete localement les champs Hektor absents de l'API via console Playwright.")
    parser.add_argument("--hektor-annonce-id", action="append", default=[], help="Annonce Hektor ciblee. Peut etre repete.")
    parser.add_argument(
        "--annonce-scope",
        choices=("all", "current"),
        default="all",
        help="all = extrait toutes les annonces locales; current = limite aux annonces poussees dans l'app.",
    )
    parser.add_argument("--limit", type=int, default=25, help="Nombre maximum d'annonces a extraire. 0 = aucune limite.")
    parser.add_argument("--stale-days", type=int, default=30, help="Rejouer les caches plus vieux que N jours. 0 = jamais par age.")
    parser.add_argument("--force", action="store_true", help="Rejouer meme si le cache est a jour.")
    parser.add_argument("--dry-run", action="store_true", help="Liste les annonces candidates sans appeler Hektor.")
    parser.add_argument("--skip-job-check", action="store_true", help="Ne verifie pas les jobs console pending/running avant extraction.")
    parser.add_argument("--storage-state", type=Path, default=DEFAULT_STORAGE_STATE)
    parser.add_argument("--node-exe", default=os.environ.get("CONSOLE_NODE_EXE") or "node.exe")
    parser.add_argument("--node-script", type=Path, default=DEFAULT_NODE_SCRIPT)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--delay-seconds", type=float, default=10.0)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--batch-pause-seconds", type=int, default=60)
    parser.add_argument("--write-debug", action="store_true")
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

    rows = read_annonces(explicit_ids, args.annonce_scope)
    existing = read_existing_cache()
    candidates = select_candidates(
        rows,
        existing,
        explicit_ids=explicit_ids,
        force=args.force,
        limit=max(0, args.limit),
        stale_days=max(0, args.stale_days),
    )

    summary: dict[str, Any] = {
        "dry_run": args.dry_run,
        "annonce_scope": args.annonce_scope,
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
    }

    if args.dry_run or not candidates:
        print(json.dumps(summary, ensure_ascii=True, indent=2))
        return

    if not args.skip_job_check:
        require_no_console_jobs()

    con = sqlite3.connect(HEKTOR_DB)
    ensure_console_table(con)
    try:
        for index, row in enumerate(candidates, start=1):
            annonce_id = row["hektor_annonce_id"]
            try:
                try:
                    payload = run_node_extractor(
                        node_exe=args.node_exe,
                        script=args.node_script,
                        annonce_id=annonce_id,
                        storage_state=storage_state,
                        timeout_seconds=args.timeout_seconds,
                        write_debug=args.write_debug,
                    )
                except RuntimeError as exc:
                    if args.refresh_session_on_expired and "Session Hektor expiree" in str(exc):
                        run_login_refresh(args.node_exe, storage_state, args.timeout_seconds)
                        payload = run_node_extractor(
                            node_exe=args.node_exe,
                            script=args.node_script,
                            annonce_id=annonce_id,
                            storage_state=storage_state,
                            timeout_seconds=args.timeout_seconds,
                            write_debug=args.write_debug,
                        )
                    else:
                        raise
                store_result(con, row, payload, storage_state)
                summary["extracted"].append(
                    {
                        "hektor_annonce_id": annonce_id,
                        "status": payload.get("status"),
                        "dpe_image_url": payload.get("dpe_image_url"),
                        "ges_image_url": payload.get("ges_image_url"),
                    }
                )
            except PermissionError as exc:
                payload = {
                    "status": "stopped_on_403",
                    "error": str(exc),
                    "extracted_at": now_iso(),
                    "hektor_annonce_id": annonce_id,
                }
                store_result(con, row, payload, storage_state)
                summary["stopped_on_403"] = {"hektor_annonce_id": annonce_id, "error": str(exc)}
                print(json.dumps(summary, ensure_ascii=True, indent=2))
                raise SystemExit(3) from exc
            except Exception as exc:
                payload = {
                    "status": "error",
                    "error": str(exc),
                    "extracted_at": now_iso(),
                    "hektor_annonce_id": annonce_id,
                }
                store_result(con, row, payload, storage_state)
                summary["errors"].append({"hektor_annonce_id": annonce_id, "error": str(exc)})

            if index < len(candidates):
                if args.batch_size > 0 and index % args.batch_size == 0:
                    time.sleep(max(0, args.batch_pause_seconds))
                else:
                    time.sleep(max(0.0, args.delay_seconds))
    finally:
        con.close()

    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise
    except SystemExit:
        raise
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=True, indent=2), file=sys.stderr)
        raise SystemExit(1) from exc
