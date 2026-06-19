#!/usr/bin/env python3
"""Run « recherches actives » (filet de fond, n°5 de l'archi cible).

Rafraîchit depuis Hektor les contacts ayant au moins une recherche ACTIVE, SANS
filtre date_maj — pour capter les éditions de recherche faites directement dans
Hektor (que le quotidien `--changed-only` manque, car éditer une recherche ne
bump pas la date_maj du contact). Complète le read-through (qui ne couvre que les
contacts ouverts) : ce run rattrape ceux que personne n'ouvre.

Périmètre : `app_contact_search_current.is_active = 1` dans la base locale phase2
(~3 590 contacts). Traite par lots via le pipeline éprouvé :
  sync_contact_details (fetch ContactById, ~0,3s/contact) -> normalize ->
  build_contacts_layer -> push_contacts_to_supabase (qui saute déjà les "dirty").

Coût mesuré ~0,3s/contact -> ~20 min pour un passage complet. Idempotent et
reprenable (chaque lot est indépendant). À planifier 1×/jour (tâche planifiée).
"""
from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
PYTHON = sys.executable


def active_search_contact_ids(db_path: Path) -> list[str]:
    """IDs des contacts ayant >=1 recherche active (couche locale phase2)."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT DISTINCT hektor_contact_id FROM app_contact_search_current "
            "WHERE is_active = 1 AND (archive IS NULL OR archive = 0) "
            "ORDER BY CAST(hektor_contact_id AS INTEGER)"
        ).fetchall()
    finally:
        conn.close()
    out: list[str] = []
    seen: set[str] = set()
    for row in rows:
        cid = str(row["hektor_contact_id"] or "").strip()
        if cid.isdigit() and cid not in seen:
            seen.add(cid)
            out.append(cid)
    return out


def run_step(args: list[str]) -> None:
    result = subprocess.run([PYTHON, *args], cwd=str(ROOT))
    if result.returncode != 0:
        raise RuntimeError(f"Echec etape: {' '.join(args)} (code {result.returncode})")


def process_batch(ids: list[str]) -> None:
    csv = ",".join(ids)
    # 1) fetch ContactById (sans date_maj : --contact-id court-circuite la sélection)
    run_step([
        "phase2/sync/sync_contact_details.py", "--contact-id", csv,
        "--skip-listing-refresh", "--limit", "0", "--request-delay-seconds", "0",
        "--batch-size", str(len(ids)), "--batch-pause-seconds", "0",
        "--max-consecutive-hard-errors", "3", "--no-normalize",
    ])
    # 2) normalize -> 3) build couche contacts -> 4) push (saute les dirty via C)
    run_step(["normalize_source.py", "--contact-id", csv])
    run_step(["phase2/contacts/build_contacts_layer.py", "--contact-id", csv, "--no-reports"])
    run_step([
        "phase2/sync/push_contacts_to_supabase.py", "--contact-id", csv,
        "--push-mode", "full", "--contacts-scope", "active_or_eligible", "--skip-stats",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run recherches actives : refresh Hektor des contacts a recherche active, sans filtre date_maj."
    )
    parser.add_argument("--batch-size", type=int, default=300, help="Contacts par lot (defaut 300).")
    parser.add_argument("--limit", type=int, default=0, help="Nombre max de contacts a traiter. 0 = tous.")
    parser.add_argument("--phase2-db", type=Path, default=PHASE2_DB)
    parser.add_argument("--dry-run", action="store_true", help="Affiche le volume sans fetch.")
    args = parser.parse_args()

    ids = active_search_contact_ids(args.phase2_db)
    if args.limit and args.limit > 0:
        ids = ids[: args.limit]
    total = len(ids)
    print(f"[recherches-actives] {total} contacts a recherche active")
    if args.dry_run:
        print("[recherches-actives] dry-run : aucun fetch")
        return 0
    if total == 0:
        return 0

    start = time.time()
    done = 0
    for i in range(0, total, max(args.batch_size, 1)):
        batch = ids[i : i + max(args.batch_size, 1)]
        process_batch(batch)
        done += len(batch)
        print(f"[recherches-actives] {done}/{total} ({round(time.time() - start)}s)")
    print(f"[recherches-actives] termine : {done} contacts en {round(time.time() - start)}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
