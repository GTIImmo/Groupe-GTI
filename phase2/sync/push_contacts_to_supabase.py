from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[2]
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
DEFAULT_ENV_FILES = (ROOT / ".env", ROOT / "apps" / "hektor-v1" / ".env")
PUSH_STATE_TABLE = "app_contact_supabase_push_state"
VOLATILE_HASH_FIELDS = {"refreshed_at"}
CONTACT_STATS_TABLE = "app_contact_stats_current"


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


def chunked(items: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_json(value: Any, fallback: Any) -> Any:
    text = str(value or "").strip()
    if not text:
        return fallback
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return fallback
    # Un JSON littéral "null" (présent en local pour de rares contacts) donne None :
    # les colonnes *_json sont NOT NULL côté Supabase -> on retombe sur le défaut ([]/{}).
    return fallback if parsed is None else parsed


def bool_value(value: Any) -> bool:
    return value in (True, 1, "1", "true", "oui")


def explicit_contact_ids(values: Iterable[str]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        for chunk in str(raw_value or "").replace(";", ",").split(","):
            contact_id = chunk.strip()
            if not contact_id:
                continue
            if not contact_id.isdigit():
                raise RuntimeError(f"ID contact invalide: {contact_id}")
            if contact_id in seen:
                continue
            seen.add(contact_id)
            ids.append(contact_id)
    return ids


def sqlite_text_in(column: str, values: list[str]) -> str:
    if not values:
        return ""
    quoted = ",".join("'" + value.replace("'", "''") + "'" for value in values)
    return f"CAST({column} AS TEXT) IN ({quoted})"


def build_search_text(row: dict[str, Any]) -> str | None:
    parts = [
        row.get("display_name"),
        row.get("email"),
        row.get("phone_primary"),
        row.get("phone_secondary"),
        row.get("ville"),
        row.get("code_postal"),
        row.get("commercial_nom"),
        row.get("agence_nom"),
        " ".join(parse_json(row.get("relation_roles_json"), [])),
    ]
    text = " ".join(str(part).strip() for part in parts if str(part or "").strip())
    return " ".join(text.split()) or None


def normalize_contact_row(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["archive"] = bool_value(payload.get("archive"))
    payload["has_contact_detail"] = bool_value(payload.get("has_contact_detail"))
    payload["supabase_sync_eligible"] = bool_value(payload.get("supabase_sync_eligible"))
    payload["typologies_json"] = parse_json(payload.get("typologies_json"), [])
    payload["relation_roles_json"] = parse_json(payload.get("relation_roles_json"), [])
    payload["eligibility_reasons_json"] = parse_json(payload.get("eligibility_reasons_json"), [])
    payload["search_text"] = build_search_text(dict(row))
    return payload


def normalize_relation_row(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["is_active_annonce"] = bool_value(payload.get("is_active_annonce"))
    return payload


def normalize_search_row(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["archive"] = bool_value(payload.get("archive"))
    payload["is_active"] = bool_value(payload.get("is_active"))
    payload["villes_json"] = parse_json(payload.get("villes_json"), [])
    payload["types_json"] = parse_json(payload.get("types_json"), {})
    payload["criteres_json"] = parse_json(payload.get("criteres_json"), [])
    return payload


def normalize_duplicate_group_row(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["suspected_mass_archive_error"] = bool_value(payload.get("suspected_mass_archive_error"))
    return payload


def normalize_duplicate_member_row(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["is_primary_candidate"] = bool_value(payload.get("is_primary_candidate"))
    payload["archive"] = bool_value(payload.get("archive"))
    return payload


def stable_payload_hash(row: dict[str, Any]) -> str:
    stable_row = {key: value for key, value in row.items() if key not in VOLATILE_HASH_FIELDS}
    payload = json.dumps(stable_row, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def row_key(table: str, row: dict[str, Any]) -> str:
    if table == "app_contact_current":
        return str(row["hektor_contact_id"])
    if table == "app_contact_relation_current":
        return str(row["relation_key"])
    if table == "app_contact_search_current":
        return str(row["contact_search_key"])
    if table == "app_contact_duplicate_group_current":
        return str(row["duplicate_group_id"])
    if table == "app_contact_duplicate_member_current":
        return f"{row['duplicate_group_id']}::{row['hektor_contact_id']}"
    raise ValueError(f"Unknown contact push table: {table}")


def key_column(table: str) -> str | None:
    if table == "app_contact_current":
        return "hektor_contact_id"
    if table == "app_contact_relation_current":
        return "relation_key"
    if table == "app_contact_search_current":
        return "contact_search_key"
    if table == "app_contact_duplicate_group_current":
        return "duplicate_group_id"
    return None


def ensure_push_state(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {PUSH_STATE_TABLE} (
            table_name TEXT NOT NULL,
            row_key TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            pushed_at TEXT NOT NULL,
            PRIMARY KEY (table_name, row_key)
        )
        """
    )
    conn.commit()


def filter_changed_rows(db_path: Path, loaded: list[tuple[str, list[dict[str, Any]]]]) -> list[tuple[str, list[dict[str, Any]]]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        ensure_push_state(conn)
        output: list[tuple[str, list[dict[str, Any]]]] = []
        for table, rows in loaded:
            state_rows = conn.execute(
                f"SELECT row_key, payload_hash FROM {PUSH_STATE_TABLE} WHERE table_name = ?",
                (table,),
            ).fetchall()
            known_hashes = {str(row["row_key"]): str(row["payload_hash"]) for row in state_rows}
            changed = [
                row
                for row in rows
                if known_hashes.get(row_key(table, row)) != stable_payload_hash(row)
            ]
            output.append((table, changed))
        return output
    finally:
        conn.close()


def find_stale_row_keys(db_path: Path, loaded: list[tuple[str, list[dict[str, Any]]]]) -> dict[str, list[str]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        ensure_push_state(conn)
        output: dict[str, list[str]] = {}
        for table, rows in loaded:
            current_keys = {row_key(table, row) for row in rows}
            state_rows = conn.execute(
                f"SELECT row_key FROM {PUSH_STATE_TABLE} WHERE table_name = ?",
                (table,),
            ).fetchall()
            stale = [str(row["row_key"]) for row in state_rows if str(row["row_key"]) not in current_keys]
            if stale:
                output[table] = stale
        return output
    finally:
        conn.close()


def mark_pushed_rows(db_path: Path, loaded: list[tuple[str, list[dict[str, Any]]]]) -> None:
    conn = sqlite3.connect(db_path)
    try:
        ensure_push_state(conn)
        pushed_at = now_utc_iso()
        for table, rows in loaded:
            conn.executemany(
                f"""
                INSERT INTO {PUSH_STATE_TABLE}(table_name, row_key, payload_hash, pushed_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(table_name, row_key) DO UPDATE SET
                    payload_hash = excluded.payload_hash,
                    pushed_at = excluded.pushed_at
                """,
                [(table, row_key(table, row), stable_payload_hash(row), pushed_at) for row in rows],
            )
        conn.commit()
    finally:
        conn.close()


def mark_deleted_rows(db_path: Path, stale_by_table: dict[str, list[str]]) -> None:
    conn = sqlite3.connect(db_path)
    try:
        ensure_push_state(conn)
        for table, row_keys in stale_by_table.items():
            conn.executemany(
                f"DELETE FROM {PUSH_STATE_TABLE} WHERE table_name = ? AND row_key = ?",
                [(table, row_key_value) for row_key_value in row_keys],
            )
        conn.commit()
    finally:
        conn.close()


class SupabaseRestClient:
    def __init__(self, *, base_url: str, service_role_key: str, timeout: int = 300, max_retries: int = 4) -> None:
        self.base_url = base_url.rstrip("/")
        self.service_role_key = service_role_key
        self.timeout = timeout
        self.max_retries = max_retries

    def request(self, *, method: str, path: str, payload: object | None = None, prefer: str | None = None) -> object | None:
        url = f"{self.base_url}/rest/v1/{path.lstrip('/')}"
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8") if payload is not None else None
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        # Robustesse alignee sur push_upgrade_to_supabase : retry sur 5xx transitoires
        # (500/502/503/504) et sur incidents reseau/timeout (URLError/TimeoutError), avec
        # backoff lineaire. Sans ca, un seul aleas transitoire pendant les ~59 requetes
        # d'upsert relations faisait echouer tout le push contacts (run nocturne du 22/06).
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read().decode("utf-8")
                    return json.loads(raw) if raw else None
            except HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code in (500, 502, 503, 504) and attempt < self.max_retries:
                    last_error = RuntimeError(f"Supabase {method} {path} failed HTTP {exc.code}: {detail[:1000]}")
                    time.sleep(1.5 * attempt)
                    continue
                raise RuntimeError(f"Supabase {method} {path} failed HTTP {exc.code}: {detail[:1000]}") from exc
            except (TimeoutError, URLError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(1.5 * attempt)
        raise RuntimeError(f"Supabase {method} {path} timeout/network error: {last_error}") from last_error

    def upsert_rows(self, table: str, rows: list[dict[str, Any]], batch_size: int) -> int:
        count = 0
        for batch in chunked(rows, batch_size):
            self.request(method="POST", path=table, payload=batch, prefer="resolution=merge-duplicates,return=minimal")
            count += len(batch)
        return count

    def delete_rows_by_key(self, table: str, column: str, row_keys: list[str], batch_size: int) -> int:
        count = 0
        for batch in chunked([{"row_key": row_key_value} for row_key_value in row_keys], batch_size):
            values = ",".join(urllib.parse.quote(str(row["row_key"]), safe="") for row in batch)
            self.request(method="DELETE", path=f"{table}?{column}=in.({values})", prefer="return=minimal")
            count += len(batch)
        return count

    def delete_rows_by_filter(self, table: str, column: str, values: list[str], batch_size: int) -> int:
        count = 0
        for batch in chunked([str(value) for value in values], batch_size):
            encoded = ",".join(urllib.parse.quote(value, safe="") for value in batch)
            self.request(method="DELETE", path=f"{table}?{column}=in.({encoded})", prefer="return=minimal")
            count += len(batch)
        return count


def load_rows(db_path: Path, table: str, normalizer, where: str = "") -> list[dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return [normalizer(row) for row in conn.execute(f"SELECT * FROM {table} {where}").fetchall()]
    finally:
        conn.close()


def scoped_where(base_where: str, extra_condition: str | None = None) -> str:
    where = base_where.strip()
    if where.upper().startswith("WHERE "):
        where = where[6:].strip()
    if not extra_condition:
        return f"WHERE ({where})" if where else ""
    if where:
        return f"WHERE ({where}) AND ({extra_condition})"
    return f"WHERE {extra_condition}"


def build_contact_stats_row(db_path: Path, scope: str, contact_where: str) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    try:
        def count(extra_condition: str | None = None) -> int:
            where = scoped_where(contact_where, extra_condition)
            return int(conn.execute(f"SELECT COUNT(*) FROM app_contact_current {where}").fetchone()[0])

        return {
            "scope": scope,
            "total": count(),
            "active": count("archive = 0"),
            "archived": count("archive = 1"),
            "duplicates": count("duplicate_group_count > 0"),
            "high_risk_duplicates": count("duplicate_max_severity IN ('high', 'critical')"),
            "linked": count("linked_annonce_count > 0"),
            "search_contacts": count("total_search_count > 0"),
            "active_search_contacts": count("active_search_count > 0"),
            "eligible": count("supabase_sync_eligible = 1"),
            "with_detail": count("has_contact_detail = 1"),
            "active_or_eligible": count("archive = 0 OR supabase_sync_eligible = 1"),
            "refreshed_at": now_utc_iso(),
        }
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pousse l'index Contacts limite vers Supabase. Ne lance rien sans appel explicite.")
    parser.add_argument("--phase2-db", type=Path, default=PHASE2_DB)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--push-mode", choices=["full", "update"], default="update", help="full = charge tout le scope; update = charge seulement les lignes dont le hash local a change.")
    parser.add_argument("--reset-push-state", action="store_true", help="Vide l'etat local de push avant de calculer les lignes update.")
    parser.add_argument(
        "--contacts-scope",
        choices=["all", "active", "active_or_eligible", "eligible"],
        default="eligible",
        help=(
            "eligible = seulement contacts utiles a l'app; "
            "active = listing leger des contacts non archives; "
            "active_or_eligible = tous les actifs + les archives deja utiles a l'app; "
            "all = listing leger de tous les contacts pour operation manuelle."
        ),
    )
    parser.add_argument("--include-archived-relations", action="store_true", help="Pousse aussi les relations rattachees uniquement a des annonces archivees.")
    parser.add_argument("--include-archived-searches", action="store_true", help="Pousse aussi les recherches archivees. Par defaut seules les recherches actives partent.")
    parser.add_argument("--include-duplicates", action="store_true", help="Pousse aussi les tables d'audit doublons reservees admin/manager.")
    parser.add_argument(
        "--contact-id",
        action="append",
        default=[],
        help="Pousse uniquement un ou plusieurs contacts Hektor (valeurs separees par virgule acceptees).",
    )
    parser.add_argument("--skip-stats", action="store_true", help="Ne pousse pas le snapshot de statistiques globales contacts.")
    return parser.parse_args()


def fetch_dirty_search_pairs(client: "SupabaseRestClient", contact_ids: list[str] | None) -> set[tuple[str, int]]:
    """Recherches en cours d'édition app (table app_search_pending) à NE PAS écraser.

    Affinage Supabase-first : tant qu'une recherche est "dirty" (éditée dans l'app/espace,
    pas encore poussée vers Hektor), le pipeline doit conserver ses critères affinés dans
    Supabase au lieu de les remplacer par l'ancienne version Hektor.
    """
    path = "app_search_pending?select=hektor_contact_id,search_index"
    if contact_ids:
        encoded = ",".join(urllib.parse.quote(str(value), safe="") for value in contact_ids)
        path += f"&hektor_contact_id=in.({encoded})"
    try:
        rows = client.request(method="GET", path=path) or []
    except Exception:
        return set()
    pairs: set[tuple[str, int]] = set()
    for row in rows:
        cid = row.get("hektor_contact_id")
        idx = row.get("search_index")
        if cid is not None and idx is not None:
            pairs.add((str(cid), int(idx)))
    return pairs


def delete_searches_except_dirty(
    client: "SupabaseRestClient", contact_ids: list[str], dirty_pairs: set[tuple[str, int]]
) -> int:
    """Supprime les recherches d'un contact SAUF celles "dirty" (édition app en attente)."""
    count = 0
    for contact_id in contact_ids:
        dirty_idx = sorted({idx for (cid, idx) in dirty_pairs if cid == str(contact_id)})
        path = f"app_contact_search_current?hektor_contact_id=eq.{urllib.parse.quote(str(contact_id), safe='')}"
        if dirty_idx:
            path += f"&search_index=not.in.({','.join(str(i) for i in dirty_idx)})"
        client.request(method="DELETE", path=path, prefer="return=minimal")
        count += 1
    return count


def main() -> int:
    args = parse_args()
    contact_ids = explicit_contact_ids(args.contact_id)
    if args.contacts_scope == "eligible":
        contact_where = "WHERE supabase_sync_eligible = 1"
    elif args.contacts_scope == "active":
        contact_where = "WHERE archive = 0"
    elif args.contacts_scope == "active_or_eligible":
        contact_where = "WHERE archive = 0 OR supabase_sync_eligible = 1"
    else:
        contact_where = ""
    relation_where = "" if args.include_archived_relations else "WHERE is_active_annonce = 1"
    search_where = "" if args.include_archived_searches else "WHERE is_active = 1"
    stats_contact_where = contact_where
    if contact_ids:
        contact_id_where = sqlite_text_in("hektor_contact_id", contact_ids)
        contact_where = scoped_where(contact_where, contact_id_where)
        relation_where = scoped_where(relation_where, contact_id_where)
        search_where = scoped_where(search_where, contact_id_where)
    table_specs = [
        ("app_contact_current", normalize_contact_row, contact_where),
        ("app_contact_relation_current", normalize_relation_row, relation_where),
        ("app_contact_search_current", normalize_search_row, search_where),
    ]
    if args.include_duplicates:
        table_specs.extend(
            [
                ("app_contact_duplicate_group_current", normalize_duplicate_group_row, ""),
                ("app_contact_duplicate_member_current", normalize_duplicate_member_row, ""),
            ]
        )

    loaded: list[tuple[str, list[dict[str, Any]]]] = []
    for table, normalizer, where in table_specs:
        rows = load_rows(args.phase2_db, table, normalizer, where)
        loaded.append((table, rows))
    loaded_counts = {table: len(rows) for table, rows in loaded}
    contact_stats = None if args.skip_stats else build_contact_stats_row(args.phase2_db, args.contacts_scope, stats_contact_where)
    stale_by_table = {} if contact_ids else find_stale_row_keys(args.phase2_db, loaded)

    if args.reset_push_state:
        conn = sqlite3.connect(args.phase2_db)
        try:
            ensure_push_state(conn)
            conn.execute(f"DELETE FROM {PUSH_STATE_TABLE}")
            conn.commit()
        finally:
            conn.close()

    if args.push_mode == "update" and not contact_ids:
        loaded = filter_changed_rows(args.phase2_db, loaded)

    if args.dry_run:
        dry_run_summary = {
            table: {
                "loaded": loaded_counts.get(table, len(rows)),
                "to_upload": len(rows),
                "to_delete": len(stale_by_table.get(table, [])),
                "push_mode": "contact_replace" if contact_ids else args.push_mode,
            }
            for table, rows in loaded
        }
        if contact_stats is not None:
            dry_run_summary[CONTACT_STATS_TABLE] = {
                "loaded": 1,
                "to_upload": 1,
                "to_delete": 0,
                "push_mode": "snapshot",
                "stats": contact_stats,
            }
        if contact_ids:
            dry_run_summary["_contact_scope"] = {
                "contact_ids": contact_ids,
                "delete_before_upsert": [
                    "app_contact_current",
                    "app_contact_relation_current",
                    "app_contact_search_current",
                ],
            }
        print(
            json.dumps(
                dry_run_summary,
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    for env_file in DEFAULT_ENV_FILES:
        load_env_file(env_file)
    supabase_url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_role_key:
        raise RuntimeError("SUPABASE_URL/VITE_SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")

    client = SupabaseRestClient(base_url=supabase_url, service_role_key=service_role_key)
    results = {}
    deleted_results = {}
    deleted_state: dict[str, list[str]] = {}
    # Affinage Supabase-first : recherches "dirty" (éditées dans l'app/espace, en attente de
    # push Hektor) -> on NE LES écrase PAS (ni delete, ni upsert) pour conserver les critères
    # affinés dans Supabase. Voir table app_search_pending.
    dirty_search_pairs = fetch_dirty_search_pairs(client, contact_ids)
    if dirty_search_pairs:
        loaded = [
            (
                table,
                [
                    row
                    for row in rows
                    if table != "app_contact_search_current"
                    or (str(row.get("hektor_contact_id")), int(row.get("search_index", -1))) not in dirty_search_pairs
                ],
            )
            for table, rows in loaded
        ]
    if contact_ids:
        for table in ["app_contact_current", "app_contact_relation_current", "app_contact_search_current"]:
            if table == "app_contact_search_current" and dirty_search_pairs:
                deleted_results[table] = delete_searches_except_dirty(client, contact_ids, dirty_search_pairs)
            else:
                deleted_results[table] = client.delete_rows_by_filter(table, "hektor_contact_id", contact_ids, args.batch_size)
    else:
        for table, stale_row_keys in stale_by_table.items():
            column = key_column(table)
            if column is None:
                continue
            deleted_results[table] = client.delete_rows_by_key(table, column, stale_row_keys, args.batch_size)
            deleted_state[table] = stale_row_keys
    for table, rows in loaded:
        results[table] = client.upsert_rows(table, rows, args.batch_size)
    if contact_stats is not None:
        results[CONTACT_STATS_TABLE] = client.upsert_rows(CONTACT_STATS_TABLE, [contact_stats], 1)
    if deleted_state:
        mark_deleted_rows(args.phase2_db, deleted_state)
    mark_pushed_rows(args.phase2_db, loaded)
    print(json.dumps({"upserted": results, "deleted": deleted_results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
