"""Sauvegarde des donnees LOCALES irremplacables (chantier Phase 0.1).

REGLE 5 -- LE MIROIR SE MET A JOUR, IL NE SE REMPLACE PAS  (posee le 2026-08-21)
--------------------------------------------------------------------------------
data/hektor.sqlite (3,89 Go, 464 952 reponses) est l'archive de TOUT ce que Hektor a
jamais dit. C'est encore lui qui fabrique chaque nuit les 56 890 annonces et les
355 641 contacts -- en 37 secondes (app_view_generale, build_contacts_layer).

  - une mise a jour n'a JAMAIS besoin d'une suppression : elle ecrase en place
    (INSERT ... ON CONFLICT(...) DO UPDATE SET). Le miroir grossit et se corrige,
    il ne se vide jamais pour se remplir ;
  - les suppressions CIBLEES restent permises : une annonce, un contact, les mandats
    d'une annonce reverses a chaque run, une page de listing reecrite ;
  - INTERDIT : supprimer le fichier, le deplacer, vider une table en masse, ou
    « faire de la place » sur les 3,89 Go ;
  - apres la coupure il GELE, il ne devient pas inutile : il reste la source des
    annonces, puis l'archive.

C'est une regle de CONSERVATION, pas de gel. Elle n'empeche rien de ce qui tourne.

POURQUOI
--------
L'audit du 2026-08-17 (notice/NOTE_AUDIT_MAITRE_2026-08-17.md, section 5) a montre que
le disque porte des donnees qu'AUCUNE copie cloud ne couvre :

  - app_dossier (56 867 lignes) : le mapping app_dossier_id <-> hektor_annonce_id.
    Sa perte orpheline TOUTES les lignes Supabase clees sur app_dossier_id (42 tables).
    Le regenerer re-emet des ids AUTOINCREMENT : la correspondance est perdue.
  - Les caches de scrape Console (~100 k lignes) : les VALEURS partent bien vers Supabase,
    mais pas le cache "deja fait" -> une perte force un re-scrape Playwright de plusieurs jours.
  - hektor_price_change_event : derive de diffs entre snapshots successifs, NON re-derivable.
  - sync_meta : 4 lignes de curseurs delta ; sans elles le pipeline repart d'un re-pull complet.
  - app_internal_status / app_diffusion_* : saisies et configuration non rejouables.

CONTRAINTE TECHNIQUE
--------------------
Les deux bases sont en mode WAL : une copie de fichier brute PENDANT un run du pipeline
serait incoherente. On n'utilise donc que :
  - des lectures en 'mode=ro' (jamais d'ecriture sur les sources),
  - VACUUM INTO pour les instantanes complets (coherent + compacte, meme base ouverte).

CONTRAINTE DISQUE (demande Frederic)
------------------------------------
Ne pas saturer le serveur. D'ou la strategie etagee :
  niveau 1 (quotidien)     : tables critiques uniquement -> quelques dizaines de Mo
  niveau 2 (hebdomadaire)  : instantane compacte de phase2.sqlite (porte l'identite)
  niveau 3 (hebdomadaire)  : archive documents locaux -- DESACTIVE le 2026-08-18,
                             couvert par OVH Backup Agent (voir DOCUMENTS_ARCHIVE_ENABLED)
  niveau 4 (sur demande)   : instantane complet de hektor.sqlite (3,9 Go) -- --full
Retention glissante sur chaque niveau, purge automatique.

USAGE
-----
  python phase2/sync/backup_critical.py                 # niveau 1 seul (quotidien)
  python phase2/sync/backup_critical.py --weekly        # + niveaux 2 et 3
  python phase2/sync/backup_critical.py --full          # + niveau 4 (gros)
  python phase2/sync/backup_critical.py --dry-run       # n'ecrit rien, affiche le plan

Racine de sauvegarde : $GTI_BACKUP_ROOT sinon C:\\Hektor\\Backups
(volontairement HORS de C:\\Hektor\\Projet : ni dans git, ni dans l'arbre projet).
"""

from __future__ import annotations

import argparse
import gzip
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
DOCUMENTS_DIR = Path(os.environ.get("CONSOLE_LOCAL_ARCHIVE_ROOT", r"C:\Hektor\HektorConsoleDocuments"))
BACKUP_ROOT = Path(os.environ.get("GTI_BACKUP_ROOT", r"C:\Hektor\Backups"))

# --- Niveau 3 (archive zip des documents) : DESACTIVE le 2026-08-18 ---------------------
# POURQUOI. L'agent OVH Backup Agent (Veeam) a ete installe le 18/08 a 17:08. Il sauvegarde
# desormais l'INTEGRALITE du volume C: vers un vault de Roubaix -- le serveur etant a
# Gravelines -- avec 14 jours d'immuabilite. Les 32,5 Go de documents sont donc deja hors
# site, et l'archive zip n'en etait qu'une SECONDE copie SUR LE MEME DISQUE que la source :
# elle ne couvrait ni la panne disque, ni l'incendie, ni le rancongiciel.
# Son cout, en revanche, etait reel : les PDF ne se compressent qu'a 6,3 % (mesure), donc
# ~30 Go par passe, 20 min de passe synchrone, et 4 copies coexistantes en retention 28 j
# = ~122 Go -- desormais re-sauvegardees et facturees par Veeam (0,007 EUR HT/Go/mois).
# A la cible de ~155 Go de documents (rattrapage des 318 000 photos), ce serait ~580 Go.
# Les niveaux 1 (quotidien) et 2 (instantane phase2) ne sont PAS touches.
# Etude complete : notice/NOTE_PLAN_SAUVEGARDE_2026-08-18.md section 1.2.
# POUR REACTIVER : definir GTI_BACKUP_DOCUMENTS=1 dans l'environnement.
DOCUMENTS_ARCHIVE_ENABLED = os.environ.get("GTI_BACKUP_DOCUMENTS", "0") == "1"

# --- Niveau 1 : les tables dont la perte est irreversible ou tres couteuse ---------------
# (source_key, table) ; l'ordre n'a pas d'importance.
CRITICAL_TABLES: dict[str, list[str]] = {
    "phase2": [
        "app_dossier",                     # LE mapping d'identite -- priorite absolue
        "app_internal_status",             # statut interne / next_action / auteur
        "app_diffusion_target",            # config diffusion par dossier
        "app_diffusion_agency_target",     # routage portail par agence
        "app_diffusion_refusal_reason",    # catalogue des motifs de refus
        "app_contact_audit_run",           # historique des audits qualite contact
        # Ajoutees le 2026-08-21 (tache 0.1), apres l'audit de la data locale
        # (notice/AUDIT_DATA_LOCALE_ET_SYNCHRO_2026-08-21.md, trou A). Ce sont les deux
        # seules autres tables locales qui DETIENNENT quelque chose : tout le reste est
        # reconstruit chaque nuit depuis le miroir. Elles n'etaient couvertes que par
        # l'instantane hebdomadaire -> jusqu'a 7 jours d'exposition.
        "app_search_registry",             # 76 841 NOMS FIGES de recherche. Meme classe de
                                           # sinistre que app_dossier : les perdre fait
                                           # recalculer tous les haches, donc orpheline tout
                                           # ce qui pend dessous -- propositions, relances,
                                           # retours acquereur, rapprochements.
        "app_affaire_ledger",              # 28 981 app_affaire_id : la serie d'identite des
                                           # transactions (offre / compromis / vente).
    ],
    "hektor": [
        "sync_meta",                       # 4 curseurs delta : sans eux, re-pull complet
        "hektor_price_change_event",       # historique de prix NON re-derivable
        "hektor_contact_missing_detail",   # cache scrape naissance/lieu/matrimonial
        "hektor_annonce_chauffage_detail", # cache scrape chauffage
        "hektor_annonce_console_detail",   # cache scrape champs console
        "hektor_annonce_draft_state",      # brouillons invisibles de l'API
        "hektor_draft_sweep_meta",         # curseurs du sweep brouillons
    ],
}

# Retention par niveau (jours)
RETENTION_DAYS = {
    "critical": 90,   # petit -> on garde 3 mois
    "phase2": 28,     # ~4 instantanes hebdo
    "documents": 28,
    "hektor": 60,
}

SOURCES = {"phase2": PHASE2_DB, "hektor": HEKTOR_DB}


def log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def human(num_bytes: float) -> str:
    for unit in ("o", "Ko", "Mo", "Go"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} To"


def connect_readonly(path: Path) -> sqlite3.Connection:
    """Ouvre une base en LECTURE SEULE : impossible d'alterer la source."""
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (table,)
    ).fetchone()
    return row is not None


def backup_critical_tables(stamp: str, dry_run: bool) -> Path | None:
    """Niveau 1 : copie les tables critiques des deux bases dans un SQLite dedie, puis gzip."""
    out_dir = BACKUP_ROOT / "critical"
    target = out_dir / f"critical_{stamp}.sqlite"
    log(f"Niveau 1 - tables critiques -> {target.name}.gz")

    if dry_run:
        for source_key, tables in CRITICAL_TABLES.items():
            log(f"  [dry-run] {source_key}: {', '.join(tables)}")
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()

    # uri=True est indispensable : sans lui, l'ATTACH d'un chemin 'file:...?mode=ro'
    # ci-dessous echoue ("unable to open database"). Le chemin simple de `target`
    # reste interprete comme un fichier normal.
    dest = sqlite3.connect(target)
    total_rows = 0
    batch_size = 5000
    try:
        for source_key, tables in CRITICAL_TABLES.items():
            source_path = SOURCES[source_key]
            if not source_path.exists():
                log(f"  ! source absente, ignoree : {source_path}")
                continue
            # Lecture seule sur la source ; ecriture uniquement dans `dest`.
            # (On evite volontairement ATTACH : l'URI 'file:...?mode=ro' se comporte mal
            #  sur les chemins Windows.)
            src_con = connect_readonly(source_path)
            try:
                for table in tables:
                    if not table_exists(src_con, table):
                        log(f"  - {source_key}.{table}: absente, ignoree")
                        continue
                    ddl = src_con.execute(
                        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
                    ).fetchone()[0]
                    dest.execute(f'DROP TABLE IF EXISTS "{table}"')
                    dest.execute(ddl)

                    cursor = src_con.execute(f'SELECT * FROM "{table}"')
                    placeholders = ",".join("?" * len(cursor.description))
                    insert_sql = f'INSERT INTO "{table}" VALUES ({placeholders})'
                    count = 0
                    while True:
                        rows = cursor.fetchmany(batch_size)
                        if not rows:
                            break
                        dest.executemany(insert_sql, rows)
                        count += len(rows)
                    dest.commit()
                    total_rows += count
                    log(f"  + {source_key}.{table}: {count} lignes")
            finally:
                src_con.close()
                dest.commit()
        # Manifeste : de quoi savoir ce que contient l'archive sans l'ouvrir.
        dest.execute(
            "CREATE TABLE IF NOT EXISTS _backup_manifest ("
            "created_at TEXT, source TEXT, table_name TEXT, row_count INTEGER)"
        )
        for source_key, tables in CRITICAL_TABLES.items():
            for table in tables:
                try:
                    count = dest.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                except sqlite3.Error:
                    continue
                dest.execute(
                    "INSERT INTO _backup_manifest VALUES (?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), source_key, table, count),
                )
        dest.commit()
    finally:
        dest.close()

    compressed = compress_file(target)
    log(f"  = {total_rows} lignes, {human(compressed.stat().st_size)} compresse")
    return compressed


def snapshot_database(source_path: Path, label: str, stamp: str, dry_run: bool) -> Path | None:
    """Niveaux 2/4 : instantane coherent via VACUUM INTO (sur de meme en mode WAL), puis gzip."""
    out_dir = BACKUP_ROOT / label
    target = out_dir / f"{label}_{stamp}.sqlite"
    log(f"Instantane {label} ({human(source_path.stat().st_size)}) -> {target.name}.gz")

    if dry_run:
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()

    started = time.perf_counter()
    con = connect_readonly(source_path)
    try:
        # VACUUM INTO : produit un fichier compacte ET coherent, sans verrouiller en ecriture.
        con.execute("VACUUM INTO ?", (str(target),))
    finally:
        con.close()

    compressed = compress_file(target)
    log(
        f"  = {human(compressed.stat().st_size)} compresse "
        f"en {round(time.perf_counter() - started, 1)} s"
    )
    return compressed


def backup_documents(stamp: str, dry_run: bool) -> Path | None:
    """Niveau 3 : archive de l'arborescence documents locale (PDF signes / estimations
    en 'local_only' n'ont AUCUNE source amont -> irrecuperables sans cette copie).

    DESACTIVE depuis le 2026-08-18 : cette source amont existe maintenant (OVH Backup
    Agent / Veeam, vault de Roubaix). Voir DOCUMENTS_ARCHIVE_ENABLED en tete de fichier.
    """
    if not DOCUMENTS_ARCHIVE_ENABLED:
        log("Niveau 3 - archive documents DESACTIVEE (couverte par OVH Backup Agent depuis le 2026-08-18)")
        log("  reactiver avec GTI_BACKUP_DOCUMENTS=1 -- cf. notice/NOTE_PLAN_SAUVEGARDE_2026-08-18.md")
        return None

    if not DOCUMENTS_DIR.exists():
        log(f"Documents : repertoire absent ({DOCUMENTS_DIR}), ignore")
        return None

    out_dir = BACKUP_ROOT / "documents"
    base = out_dir / f"documents_{stamp}"
    log(f"Niveau 3 - documents locaux -> {base.name}.zip")

    if dry_run:
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    archive = shutil.make_archive(str(base), "zip", root_dir=str(DOCUMENTS_DIR))
    path = Path(archive)
    log(f"  = {human(path.stat().st_size)}")
    return path


def compress_file(path: Path) -> Path:
    """Compresse puis supprime l'original (on ne garde que le .gz)."""
    target = path.with_suffix(path.suffix + ".gz")
    with open(path, "rb") as src, gzip.open(target, "wb", compresslevel=6) as dst:
        shutil.copyfileobj(src, dst, length=1024 * 1024)
    path.unlink()
    return target


def purge_old(label: str, days: int, dry_run: bool) -> None:
    """Retention glissante : supprime UNIQUEMENT dans le repertoire de sauvegarde."""
    directory = BACKUP_ROOT / label
    if not directory.exists():
        return
    cutoff = datetime.now() - timedelta(days=days)
    removed = 0
    freed = 0
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        if datetime.fromtimestamp(entry.stat().st_mtime) >= cutoff:
            continue
        freed += entry.stat().st_size
        if dry_run:
            log(f"  [dry-run] purgerait {entry.name}")
        else:
            entry.unlink()
        removed += 1
    if removed:
        log(f"  purge {label}: {removed} fichier(s), {human(freed)} liberes (> {days} j)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--weekly", action="store_true", help="Ajoute l'instantane phase2 + les documents.")
    parser.add_argument("--full", action="store_true", help="Ajoute l'instantane complet de hektor.sqlite (3,9 Go).")
    parser.add_argument("--dry-run", action="store_true", help="N'ecrit rien ; affiche seulement le plan.")
    args = parser.parse_args()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log(f"Sauvegarde GTI - racine {BACKUP_ROOT}" + (" [DRY-RUN]" if args.dry_run else ""))

    if not args.dry_run:
        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    produced: list[Path] = []
    try:
        result = backup_critical_tables(stamp, args.dry_run)
        if result:
            produced.append(result)

        if args.weekly or args.full:
            result = snapshot_database(PHASE2_DB, "phase2", stamp, args.dry_run)
            if result:
                produced.append(result)
            result = backup_documents(stamp, args.dry_run)
            if result:
                produced.append(result)

        if args.full:
            result = snapshot_database(HEKTOR_DB, "hektor", stamp, args.dry_run)
            if result:
                produced.append(result)
    except Exception as exc:  # noqa: BLE001 - on veut le motif exact dans le log de la tache
        log(f"ECHEC : {exc}")
        return 1

    log("Retention :")
    for label, days in RETENTION_DAYS.items():
        purge_old(label, days, args.dry_run)

    if produced:
        total = sum(p.stat().st_size for p in produced)
        log(f"Termine - {len(produced)} archive(s), {human(total)} au total")
    else:
        log("Termine (dry-run, rien ecrit)" if args.dry_run else "Termine - aucune archive produite")
    return 0


if __name__ == "__main__":
    sys.exit(main())
