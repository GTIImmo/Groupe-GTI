from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hektor_pipeline.common import HektorClient, Settings


HEKTOR_DB = ROOT / "data" / "hektor.sqlite"


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


def dedupe_rows(rows: list[dict[str, object]], key: str) -> list[dict[str, object]]:
    deduped: dict[str, dict[str, object]] = {}
    for row in rows:
        value = str(row.get(key) or "").strip()
        if not value:
            continue
        deduped[value] = row
    return list(deduped.values())


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_duplicate_user_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        user_id = str(row.get("idUser") or "").strip()
        if not user_id:
            continue
        grouped.setdefault(user_id, []).append(row)
    return {user_id: items for user_id, items in grouped.items() if len(items) > 1}


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
            with urllib.request.urlopen(request, timeout=300) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase {method} {path} failed HTTP {exc.code}: {detail[:800]}") from exc
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

    def supports_columns(self, *, path: str, columns: list[str]) -> bool:
        try:
            self._request(
                method="GET",
                path=path,
                query={"select": ",".join(columns), "limit": "1"},
            )
            return True
        except RuntimeError as exc:
            message = str(exc).lower()
            if "pgrst204" in message or "could not find" in message or "schema cache" in message or "does not exist" in message:
                return False
            raise

    def delete_missing(self, *, path: str, column: str, keep_ids: list[str], chunk_size: int = 200) -> int:
        existing = self.fetch_ids(path=path, column=column)
        stale = [value for value in existing if value not in set(keep_ids)]
        for index in range(0, len(stale), chunk_size):
            batch = stale[index : index + chunk_size]
            joined = ",".join(batch)
            self._request(method="DELETE", path=f"{path}?{column}=in.({joined})")
        return len(stale)


def fetch_all_users(client: HektorClient, version: str) -> list[dict[str, Any]]:
    payload = client.get_json("/Api/User/UsersOfParent/", params={"page": 1, "version": version})
    data = payload.get("data") if isinstance(payload, dict) else None
    batch = data if isinstance(data, list) else []
    return [item for item in batch if isinstance(item, dict)]


def fetch_active_negos(client: HektorClient) -> list[dict[str, Any]]:
    """Négociateurs ACTIFS via listNegos actif=1 (source de vérité de l'actif).
    UsersOfParent ne voit que les ~12 users directs du compte parent (2 NEGO),
    alors que listNegos actif=1 renvoie les ~30 négociateurs réellement actifs.
    Renvoie les lignes brutes (id, idUser, nom, prenom, email, telephone, portable...)."""
    page = 0
    rows: list[dict[str, Any]] = []
    while page < 50:
        payload = client.get_json("/Api/Negociateur/listNegos/", params={"page": page, "actif": 1})
        batch = payload.get("res") if isinstance(payload, dict) else None
        batch = batch if isinstance(batch, list) else []
        if not batch:
            break
        rows.extend(item for item in batch if isinstance(item, dict))
        page += 1
    return rows


def active_nego_user_ids_from_rows(rows: list[dict[str, Any]]) -> set[str]:
    return {
        str(row.get("idUser") or "").strip()
        for row in rows
        if str(row.get("idUser") or "").strip()
    }


def build_nego_user_rows(rows: list[dict[str, Any]]) -> list[dict[str, object]]:
    """Transforme les négociateurs actifs (listNegos) en lignes app_user_directory
    de type NEGO, pour qu'ils soient de VRAIS utilisateurs résolvables (worker + RPC
    de résolution dépendent de app_user_directory user_type=NEGO). Même format que
    build_user_rows (issu de UsersOfParent)."""
    output: list[dict[str, object]] = []
    for row in rows:
        id_user = str(row.get("idUser") or "").strip()
        if not id_user:
            continue
        prenom = str(row.get("prenom") or "").strip()
        nom = str(row.get("nom") or "").strip()
        payload = {
            "id_user": id_user,
            "user_type": "NEGO",
            "prenom": prenom or None,
            "nom": nom or None,
            "display_name": " ".join(part for part in [prenom, nom] if part) or None,
            "email": str(row.get("email") or "").strip() or None,
            "tel": str(row.get("telephone") or "").strip() or None,
            "portable": str(row.get("portable") or "").strip() or None,
            "site": None,
            "parent_id": None,
        }
        payload["source_hash"] = stable_hash(payload)
        output.append(payload)
    return output


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


def build_negotiator_agency_rows(
    active_hektor_user_ids: set[str] | None = None,
    *,
    include_status_columns: bool = False,
) -> list[dict[str, object]]:
    if not HEKTOR_DB.exists():
        return []
    con = sqlite3.connect(HEKTOR_DB)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            """
            SELECT
                n.hektor_negociateur_id,
                n.hektor_user_id,
                n.hektor_agence_id,
                ag.nom AS agence_nom,
                json_extract(ag.raw_json, '$.idUser') AS agence_id_user,
                n.nom,
                n.prenom,
                n.email,
                n.telephone,
                n.portable
            FROM hektor_negociateur n
            LEFT JOIN hektor_agence ag ON ag.hektor_agence_id = n.hektor_agence_id
            WHERE NULLIF(TRIM(n.hektor_negociateur_id), '') IS NOT NULL
            ORDER BY
                COALESCE(ag.nom, ''),
                COALESCE(n.prenom, ''),
                COALESCE(n.nom, '')
            """
        ).fetchall()
    finally:
        con.close()

    output: list[dict[str, object]] = []
    active_refreshed_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        hektor_user_id = str(row["hektor_user_id"] or "").strip()
        is_active = active_hektor_user_ids is not None and hektor_user_id in active_hektor_user_ids
        display_name = " ".join(
            part for part in [str(row["prenom"] or "").strip(), str(row["nom"] or "").strip()] if part
        ) or None
        payload = {
            "hektor_negociateur_id": str(row["hektor_negociateur_id"] or "").strip(),
            "hektor_user_id": hektor_user_id or None,
            "hektor_agence_id": str(row["hektor_agence_id"] or "").strip() or None,
            "agence_id_user": str(row["agence_id_user"] or "").strip() or None,
            "agence_nom": str(row["agence_nom"] or "").strip() or None,
            "nom": str(row["nom"] or "").strip() or None,
            "prenom": str(row["prenom"] or "").strip() or None,
            "display_name": display_name,
            "email": str(row["email"] or "").strip() or None,
            "telephone": str(row["telephone"] or "").strip() or None,
            "portable": str(row["portable"] or "").strip() or None,
        }
        payload["source_hash"] = stable_hash(payload)
        if include_status_columns:
            payload["is_active"] = is_active
            payload["active_source"] = "users_of_parent_nego" if is_active else "local_hektor_negociateur_inactive"
            payload["active_refreshed_at"] = active_refreshed_at
        output.append(payload)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synchronise users et agences Hektor vers Supabase.")
    parser.add_argument("--skip-purge", action="store_true", help="N'efface pas les ids absents du listing source.")
    parser.add_argument("--dump-dir", default="", help="Dossier optionnel pour exporter les fichiers users/agences en local.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_env_file(ROOT / ".env")
    load_env_file(ROOT / "apps" / "hektor-v1" / ".env")

    supabase_url = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").strip()
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not supabase_url or not service_role_key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY requis")

    settings = Settings.from_env()
    hektor = HektorClient(settings)
    client = SupabaseRestClient(base_url=supabase_url, service_role_key=service_role_key)

    raw_users = fetch_all_users(hektor, settings.api_version)
    raw_agencies = fetch_all_agencies(hektor, settings.api_version)
    user_rows = dedupe_rows(build_user_rows(raw_users), "id_user")
    agency_rows = dedupe_rows(build_agency_rows(raw_agencies), "id_agence")
    # Actif = listNegos actif=1 (source de vérité). Fallback sur le signal
    # UsersOfParent NEGO si l'appel échoue/0 (évite de tout marquer inactif).
    active_negos = fetch_active_negos(hektor)
    active_nego_user_ids = active_nego_user_ids_from_rows(active_negos)
    if not active_nego_user_ids:
        active_nego_user_ids = {
            str(row["id_user"]).strip()
            for row in user_rows
            if str(row.get("user_type") or "").strip().upper() == "NEGO" and str(row.get("id_user") or "").strip()
        }
    # Les négociateurs actifs deviennent de VRAIS utilisateurs (type NEGO) dans
    # app_user_directory : la résolution worker+RPC en dépend, et comme ils font
    # désormais partie de la liste source, le purge (delete_missing) les conserve.
    # Parent prioritaire en cas de doublon d'id_user (négos d'abord -> parent garde la main).
    if active_negos:
        user_rows = dedupe_rows(build_nego_user_rows(active_negos) + user_rows, "id_user")
        # Un négo actif doit RESTER résolvable comme NEGO même s'il est aussi ADMIN
        # dans le compte parent : la résolution worker/RPC, l'identité Google et l'assign
        # exigent user_type=NEGO. (Le rôle admin de l'app vient du profil, pas de cette table ;
        # rien ne lit user_type=ADMIN dans app_user_directory.)
        for row in user_rows:
            if str(row.get("id_user") or "").strip() in active_nego_user_ids:
                row["user_type"] = "NEGO"
    negotiator_status_columns_supported = client.supports_columns(
        path="app_hektor_negotiator_agency_directory",
        columns=["is_active", "active_source", "active_refreshed_at"],
    )
    negotiator_agency_rows = dedupe_rows(
        build_negotiator_agency_rows(
            active_nego_user_ids,
            include_status_columns=negotiator_status_columns_supported,
        ),
        "hektor_negociateur_id",
    )
    active_negotiator_agency_count = sum(
        1
        for row in negotiator_agency_rows
        if str(row.get("hektor_user_id") or "").strip() in active_nego_user_ids
    )

    if args.dump_dir:
        dump_dir = Path(args.dump_dir)
        duplicate_user_rows = build_duplicate_user_rows(raw_users)
        duplicate_user_ids = sorted(duplicate_user_rows.keys())
        write_json(dump_dir / "hektor_users_raw.json", raw_users)
        write_json(dump_dir / "hektor_users_directory.json", user_rows)
        write_json(dump_dir / "hektor_agences_raw.json", raw_agencies)
        write_json(dump_dir / "hektor_agences_directory.json", agency_rows)
        write_json(dump_dir / "hektor_negotiator_agency_directory.json", negotiator_agency_rows)
        write_json(dump_dir / "hektor_users_duplicate_ids.json", duplicate_user_ids)
        write_json(dump_dir / "hektor_users_duplicates.json", duplicate_user_rows)

    client.upsert_rows(path="app_user_directory", rows=user_rows)
    client.upsert_rows(path="app_agence_directory", rows=agency_rows)
    if negotiator_agency_rows:
        client.upsert_rows(path="app_hektor_negotiator_agency_directory", rows=negotiator_agency_rows)

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
        if negotiator_agency_rows:
            client.delete_missing(
                path="app_hektor_negotiator_agency_directory",
                column="hektor_negociateur_id",
                keep_ids=[str(row["hektor_negociateur_id"]) for row in negotiator_agency_rows],
            )

    print(
        json.dumps(
            {
                "users_upserted": len(user_rows),
                "agencies_upserted": len(agency_rows),
                "negotiator_agencies_upserted": len(negotiator_agency_rows),
                "negotiator_agencies_active": active_negotiator_agency_count,
                "negotiator_agencies_inactive": len(negotiator_agency_rows) - active_negotiator_agency_count,
                "negotiator_status_columns_supported": negotiator_status_columns_supported,
                "users_deleted": deleted_users,
                "agencies_deleted": deleted_agencies,
                "dump_dir": args.dump_dir or None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
