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
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
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


def acquereur_contact_ids(hektor_db: Path) -> list[str]:
    """IDs des contacts NON archives portant la typologie Hektor « acquereur ».

    Perimetre du RATTRAPAGE (21/08/2026). Le run quotidien ne relit que les contacts
    dont l'app connait deja une recherche active (~3 800) : un contact qui gagne sa
    PREMIERE recherche n'y entre jamais, et creer une recherche ne bouge pas la
    date_maj du contact -- il reste donc invisible indefiniment. La typologie, elle,
    est dans le listing (rafraichi chaque nuit) et ENVELOPPE les recherches : sonde du
    21/08 sur 249 fiches lues en direct, aucune recherche connue hors de cette
    typologie. Relire tous les acquereurs ferme le trou.

    Sonde du 21/08 : 1 fiche sur 249 portait une recherche que l'app ignorait,
    soit ~270 recherches invisibles sur 67 483 contacts.
    """
    conn = sqlite3.connect(f"file:{hektor_db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT hektor_contact_id FROM hektor_contact "
            "WHERE archive = '0' AND typologie_json LIKE '%acqu%' "
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
    # --include-archived-searches (21/08/2026) : SANS cette option, ce run considererait
    # les recherches archivees deja poussees comme "disparues" et les supprimerait de
    # Supabase -- defaisant chaque nuit ce que le run de 05:30 vient d'ecrire.
    run_step([
        "phase2/sync/push_contacts_to_supabase.py", "--contact-id", csv,
        "--push-mode", "full", "--contacts-scope", "active_or_eligible", "--skip-stats",
        "--include-archived-searches",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run recherches actives : refresh Hektor des contacts a recherche active, sans filtre date_maj."
    )
    parser.add_argument("--batch-size", type=int, default=300, help="Contacts par lot (defaut 300).")
    parser.add_argument("--limit", type=int, default=0, help="Nombre max de contacts a traiter. 0 = tous.")
    parser.add_argument("--phase2-db", type=Path, default=PHASE2_DB)
    parser.add_argument("--hektor-db", type=Path, default=HEKTOR_DB)
    parser.add_argument(
        "--scope", choices=("actives", "acquereurs"), default="actives",
        help="actives = contacts a recherche active connue (defaut, run de 03:00). "
             "acquereurs = TOUS les contacts de typologie acquereur (rattrapage).",
    )
    parser.add_argument(
        "--pause-between-batches", type=float, default=0.0,
        help="Pause en secondes entre deux lots. 0 = aucune (defaut). Mettre 20 sur un "
             "rattrapage long : tenir 6 appels/s pendant des heures est la forme qui a "
             "fait bannir notre IP au rattrapage des documents.",
    )
    parser.add_argument(
        "--max-consecutive-failed-batches", type=int, default=3,
        help="Coupe-circuit : abandonne le run apres N lots consecutifs en echec "
             "(defaut 3, 0 = desactive). Sans lui, un bannissement d'IP au lot 12 "
             "laisse le run taper 226 lots de plus sur une porte fermee.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Affiche le volume sans fetch.")
    args = parser.parse_args()

    if args.scope == "acquereurs":
        ids = acquereur_contact_ids(args.hektor_db)
        libelle = "acquereurs (typologie Hektor)"
    else:
        ids = active_search_contact_ids(args.phase2_db)
        libelle = "contacts a recherche active"
    if args.limit and args.limit > 0:
        ids = ids[: args.limit]
    total = len(ids)
    print(f"[recherches-actives] {total} {libelle}")
    if args.dry_run:
        print("[recherches-actives] dry-run : aucun fetch")
        return 0
    if total == 0:
        return 0

    start = time.time()
    done = 0
    failed_batches = 0
    consecutive_failed = 0
    aborted = False
    for i in range(0, total, max(args.batch_size, 1)):
        batch = ids[i : i + max(args.batch_size, 1)]
        # Robustesse : un lot en échec (hoquet Hektor/réseau) ne doit PAS arrêter
        # tout le run — on log et on continue avec les lots suivants.
        try:
            process_batch(batch)
            consecutive_failed = 0
        except Exception as exc:  # noqa: BLE001
            failed_batches += 1
            consecutive_failed += 1
            print(f"[recherches-actives] LOT EN ECHEC (contacts {i}-{i + len(batch)}): {exc} -- on continue")
        done += len(batch)
        print(f"[recherches-actives] {done}/{total} ({round(time.time() - start)}s)")
        # Coupe-circuit (21/08/2026). Des lots qui echouent EN CHAINE ne sont plus un
        # hoquet : c'est la signature d'un bannissement d'IP ou d'une session Hektor
        # morte. Continuer, c'est marteler une porte fermee pendant des heures --
        # exactement ce qui a aggrave le rattrapage des documents. On sort ici : le run
        # est reprenable, et il faut verifier depuis une AUTRE IP avant de conclure a
        # une panne Hektor.
        if args.max_consecutive_failed_batches > 0 and consecutive_failed >= args.max_consecutive_failed_batches:
            aborted = True
            print(
                f"[recherches-actives] COUPE-CIRCUIT : {consecutive_failed} lots consecutifs en echec"
                f" -- run ABANDONNE a {done}/{total} ({round(time.time() - start)}s)."
                " Suspecter un bannissement d'IP ou une session Hektor morte ; verifier depuis"
                " une autre IP avant de relancer."
            )
            break
        if args.pause_between_batches > 0 and done < total:
            time.sleep(args.pause_between_batches)
    if aborted:
        return 2  # 2 = abandon coupe-circuit (a distinguer de 1 = echecs partiels)
    if failed_batches:
        print(f"[recherches-actives] TERMINE AVEC {failed_batches} lot(s) en echec sur {((total - 1) // max(args.batch_size, 1)) + 1} -- {done} contacts traites en {round(time.time() - start)}s")
        return 1  # code non nul -> la tache planifiee signale l'echec partiel
    print(f"[recherches-actives] termine OK : {done} contacts en {round(time.time() - start)}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
