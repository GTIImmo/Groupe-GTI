"""Sync de l'etat brouillon (isDraft) Hektor -> table locale hektor_annonce_draft_state.

Lecture seule cote Hektor (GraphQL PropertyListing de la Console) + ecriture locale
SQLite uniquement. Aucun ecriture Supabase ni Hektor.

Modele identique a la philosophie chauffage : delta quotidien (scan du recent
jusqu'au watermark) + backstop complet periodique.

- delta  : scanne PropertyListing (order LATEST) jusqu'a depasser le watermark
           (createdAt) -> capte les nouveaux brouillons + les biens recemment
           modifies (dont finalisations qui bougent createdAt/datemaj).
- full   : scanne tout, reconcilie (is_draft=0 pour les anciens brouillons qui ne
           sont plus isDraft), repose le watermark. Declenche par --full ou si le
           dernier full date de plus de --backstop-days, ou si la table est vide.

Usage:
  python phase2/sync/sync_hektor_drafts.py [--full] [--backstop-days 7]
         [--session <storage_state.json>] [--max-pages N] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
DEFAULT_SESSION = ROOT / "Console" / "sessions" / "storage_state_sync_light.json"
HEKTOR_BASE_URL = "https://groupe-gti-immobilier.la-boite-immo.com"
GRAPHQL_URL = f"{HEKTOR_BASE_URL}/ws/GraphQL_Web"

PROPERTY_LISTING_QUERY = (
    "query PropertyListing($filters: AnnonceSearchInput!){listing:properties(filters:$filters){"
    "metadata{total perPage nextPage} "
    "properties:nodes{id status isDraft isBroadcasted isValid createdAt datemaj}}}"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_session(path: Path) -> tuple[str, str | None]:
    state = json.loads(path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).timestamp()
    cookies = "; ".join(
        f"{c['name']}={c['value']}"
        for c in state.get("cookies", [])
        if not c.get("expires") or c["expires"] < 0 or c["expires"] > now
    )
    token = None
    for origin in state.get("origins", []):
        if origin.get("origin") == HEKTOR_BASE_URL:
            for item in origin.get("localStorage", []):
                if item.get("name") == "token" and item.get("value"):
                    raw = str(item["value"])
                    token = raw if raw.startswith("Bearer ") else f"Bearer {raw}"
    return cookies, token


def graphql_page(session: requests.Session, cookies: str, token: str | None, page: int) -> dict:
    headers = {
        "Cookie": cookies,
        "Referer": f"{HEKTOR_BASE_URL}/admin/",
        "Origin": HEKTOR_BASE_URL,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = token
    payload = {
        "operationName": "PropertyListing",
        "query": PROPERTY_LISTING_QUERY,
        "variables": {
            "filters": {
                "limit": 50,
                "offers": ["SALE"],
                "status": "ALL",
                "page": page,
                "order": "LATEST",
                "sources": ["local"],
                "archived": False,
            }
        },
    }
    resp = session.post(GRAPHQL_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    body = resp.json()
    if body.get("errors"):
        raise RuntimeError(f"GraphQL Hektor: {body['errors']}")
    return body["data"]["listing"]


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS hektor_annonce_draft_state (
          hektor_annonce_id TEXT PRIMARY KEY,
          is_draft INTEGER NOT NULL DEFAULT 1,
          status TEXT,
          is_broadcasted INTEGER,
          is_valid INTEGER,
          created_at_hektor TEXT,
          datemaj TEXT,
          source TEXT,
          seen_at TEXT
        )
        """
    )
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_hektor_annonce_draft_state_isdraft ON hektor_annonce_draft_state(is_draft)"
    )
    con.execute("CREATE TABLE IF NOT EXISTS hektor_draft_sweep_meta (key TEXT PRIMARY KEY, value TEXT)")


def get_meta(con: sqlite3.Connection, key: str) -> str | None:
    row = con.execute("SELECT value FROM hektor_draft_sweep_meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def set_meta(con: sqlite3.Connection, key: str, value: str | None) -> None:
    con.execute(
        "INSERT INTO hektor_draft_sweep_meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def upsert_state(con: sqlite3.Connection, prop: dict, source: str) -> None:
    is_draft = 1 if prop.get("isDraft") is True else 0
    con.execute(
        """
        INSERT INTO hektor_annonce_draft_state(
          hektor_annonce_id, is_draft, status, is_broadcasted, is_valid,
          created_at_hektor, datemaj, source, seen_at)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(hektor_annonce_id) DO UPDATE SET
          is_draft = excluded.is_draft,
          status = excluded.status,
          is_broadcasted = excluded.is_broadcasted,
          is_valid = excluded.is_valid,
          created_at_hektor = excluded.created_at_hektor,
          datemaj = excluded.datemaj,
          source = excluded.source,
          seen_at = excluded.seen_at
        """,
        (
            str(prop.get("id")),
            is_draft,
            prop.get("status"),
            1 if prop.get("isBroadcasted") is True else 0,
            1 if prop.get("isValid") is True else 0,
            prop.get("createdAt"),
            prop.get("datemaj"),
            source,
            now_iso(),
        ),
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sync isDraft Hektor -> hektor_annonce_draft_state (local).")
    p.add_argument("--full", action="store_true", help="Force un scan complet (reconciliation).")
    p.add_argument("--backstop-days", type=int, default=7, help="Declenche un full si le dernier full est plus vieux.")
    p.add_argument("--session", type=Path, default=DEFAULT_SESSION)
    p.add_argument("--max-pages", type=int, default=0, help="Plafond de pages (0 = illimite).")
    p.add_argument("--dry-run", action="store_true", help="N'ecrit rien, affiche seulement.")
    return p.parse_args()


def should_full(con: sqlite3.Connection, args: argparse.Namespace) -> bool:
    if args.full:
        return True
    if con.execute("SELECT count(*) FROM hektor_annonce_draft_state").fetchone()[0] == 0:
        return True
    last = get_meta(con, "last_full_sweep_at")
    if not last:
        return True
    try:
        last_dt = datetime.strptime(last[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return True
    return datetime.now(timezone.utc) - last_dt > timedelta(days=args.backstop_days)


def main() -> int:
    args = parse_args()
    if not args.session.exists():
        print(f"Session introuvable: {args.session}", file=sys.stderr)
        return 2
    cookies, token = load_session(args.session)

    con = sqlite3.connect(HEKTOR_DB, timeout=60)
    ensure_schema(con)
    full = should_full(con, args)
    wm_created = get_meta(con, "watermark_createdAt") or ""
    mode = "full" if full else "delta"
    print(f"Mode: {mode} | watermark_createdAt={wm_created or '(aucun)'}")

    session = requests.Session()
    seen_draft_ids: set[str] = set()
    seen_total = 0
    new_max_created = wm_created
    new_max_datemaj = get_meta(con, "watermark_datemaj") or ""
    page = 1
    stop = False
    while not stop:
        listing = graphql_page(session, cookies, token, page)
        props = listing.get("properties") or []
        if not props:
            break
        page_has_new = False
        for prop in props:
            seen_total += 1
            created = prop.get("createdAt") or ""
            datemaj = prop.get("datemaj") or ""
            if created > new_max_created:
                new_max_created = created
            if datemaj > new_max_datemaj:
                new_max_datemaj = datemaj
            if not full and wm_created and created <= wm_created:
                pass
            else:
                page_has_new = True
            if prop.get("isDraft") is True:
                seen_draft_ids.add(str(prop.get("id")))
                if not args.dry_run:
                    upsert_state(con, prop, mode)
            elif not args.dry_run:
                # bien non-brouillon : on ne le stocke pas ; on demote seulement s'il etait
                # connu comme brouillon (= finalise depuis).
                con.execute(
                    "UPDATE hektor_annonce_draft_state SET is_draft = 0, status = ?, datemaj = ?, "
                    "source = ?, seen_at = ? WHERE hektor_annonce_id = ? AND is_draft = 1",
                    (prop.get("status"), prop.get("datemaj"), mode + "_demote", now_iso(), str(prop.get("id"))),
                )
        meta = listing.get("metadata") or {}
        nxt = meta.get("nextPage")
        if args.max_pages and page >= args.max_pages:
            break
        # delta : on s'arrete des qu'une page entiere est plus vieille que le watermark
        if not full and wm_created and not page_has_new:
            stop = True
            break
        if nxt in (None, "", 0, "0"):
            break
        page = int(nxt)

    # En full : les anciens brouillons non revus comme isDraft repassent is_draft=0 (finalises/supprimes).
    demoted = 0
    if full and not args.dry_run:
        rows = con.execute("SELECT hektor_annonce_id FROM hektor_annonce_draft_state WHERE is_draft = 1").fetchall()
        for (aid,) in rows:
            if str(aid) not in seen_draft_ids:
                con.execute(
                    "UPDATE hektor_annonce_draft_state SET is_draft = 0, source = 'full_demote', seen_at = ? "
                    "WHERE hektor_annonce_id = ?",
                    (now_iso(), str(aid)),
                )
                demoted += 1

    if not args.dry_run:
        set_meta(con, "watermark_createdAt", new_max_created)
        set_meta(con, "watermark_datemaj", new_max_datemaj)
        set_meta(con, "last_sweep_at", now_iso())
        if full:
            set_meta(con, "last_full_sweep_at", now_iso())
        con.commit()

    total_draft = con.execute("SELECT count(*) FROM hektor_annonce_draft_state WHERE is_draft = 1").fetchone()[0]
    print(
        f"{mode}: pages_scannees~{page} biens_vus={seen_total} brouillons_vus={len(seen_draft_ids)} "
        f"demotes={demoted} | total is_draft=1 en base={total_draft}"
    )
    print(f"watermark -> createdAt={new_max_created} datemaj={new_max_datemaj}")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
