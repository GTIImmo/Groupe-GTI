from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "actif.sqlite"


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_build_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS actif_case_index (
            annonce_id TEXT PRIMARY KEY,
            active_current INTEGER NOT NULL,
            listing_date_maj TEXT,
            first_seen_at TEXT,
            last_seen_at TEXT,
            removed_at TEXT,
            statut_id TEXT,
            statut_name TEXT,
            no_dossier TEXT,
            no_mandat TEXT,
            agence_id TEXT,
            negociateur_id TEXT,
            archive TEXT,
            diffusable TEXT,
            partage TEXT,
            valide TEXT,
            prix REAL,
            surface TEXT,
            titre TEXT,
            ville TEXT,
            code_postal TEXT,
            mandat_id TEXT,
            mandat_numero TEXT,
            mandat_type TEXT,
            mandat_debut TEXT,
            mandat_fin TEXT,
            mandat_cloture TEXT,
            mandat_montant TEXT,
            has_mandat INTEGER NOT NULL DEFAULT 0,
            nb_contacts_total INTEGER NOT NULL DEFAULT 0,
            nb_proprietaires INTEGER NOT NULL DEFAULT 0,
            nb_mandants INTEGER NOT NULL DEFAULT 0,
            nb_acquereurs INTEGER NOT NULL DEFAULT 0,
            nb_notaires INTEGER NOT NULL DEFAULT 0,
            has_contact_detail INTEGER NOT NULL DEFAULT 0,
            has_contact_list_activity INTEGER NOT NULL DEFAULT 0,
            last_contact_list_date_last_traitement TEXT,
            last_contact_list_date_maj TEXT,
            last_contact_detail_date_maj TEXT,
            proprietaires_noms TEXT,
            mandants_noms TEXT,
            acquereurs_noms TEXT,
            notaire_entree_nom TEXT,
            notaire_sortie_nom TEXT,
            nb_broadcasts INTEGER NOT NULL DEFAULT 0,
            has_broadcast INTEGER NOT NULL DEFAULT 0,
            is_broadcasted INTEGER NOT NULL DEFAULT 0,
            broadcast_names TEXT,
            broadcast_status_summary TEXT,
            build_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_actif_case_index_active_current
            ON actif_case_index(active_current);
        CREATE INDEX IF NOT EXISTS idx_actif_case_index_statut_name
            ON actif_case_index(statut_name);
        CREATE INDEX IF NOT EXISTS idx_actif_case_index_no_dossier
            ON actif_case_index(no_dossier);
        """
    )
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(actif_case_index)")}
    for column_name, ddl in (
        ("has_contact_list_activity", "ALTER TABLE actif_case_index ADD COLUMN has_contact_list_activity INTEGER NOT NULL DEFAULT 0"),
        ("last_contact_list_date_last_traitement", "ALTER TABLE actif_case_index ADD COLUMN last_contact_list_date_last_traitement TEXT"),
        ("last_contact_list_date_maj", "ALTER TABLE actif_case_index ADD COLUMN last_contact_list_date_maj TEXT"),
        ("last_contact_detail_date_maj", "ALTER TABLE actif_case_index ADD COLUMN last_contact_detail_date_maj TEXT"),
    ):
        if column_name not in existing_columns:
            conn.execute(ddl)
    conn.commit()


def now_sqlite(conn: sqlite3.Connection) -> str:
    return str(conn.execute("SELECT datetime('now')").fetchone()[0])


def format_contact_name(row: sqlite3.Row) -> str:
    nom = (row["nom"] or "").strip()
    prenom = (row["prenom"] or "").strip()
    joined = " ".join(part for part in (prenom, nom) if part)
    return joined or str(row["contact_id"])


def group_contacts(rows: Iterable[sqlite3.Row]) -> Dict[str, object]:
    grouped = {
        "proprietaire": [],
        "mandant": [],
        "acquereur": [],
        "notaire_entree": [],
        "notaire_sortie": [],
    }
    has_contact_detail = 0
    has_contact_list_activity = 0
    last_contact_list_date_last_traitement = None
    last_contact_list_date_maj = None
    last_contact_detail_date_maj = None
    for row in rows:
        role = row["role_contact"]
        if role in grouped:
            grouped[role].append(format_contact_name(row))
        if row["contact_list_date_last_traitement"]:
            has_contact_list_activity = 1
            last_contact_list_date_last_traitement = max(
                last_contact_list_date_last_traitement or "",
                str(row["contact_list_date_last_traitement"]),
            )
        if row["contact_list_date_maj"]:
            last_contact_list_date_maj = max(
                last_contact_list_date_maj or "",
                str(row["contact_list_date_maj"]),
            )
        if row["contact_detail_json"]:
            has_contact_detail = 1
        if row["contact_detail_date_maj"]:
            last_contact_detail_date_maj = max(
                last_contact_detail_date_maj or "",
                str(row["contact_detail_date_maj"]),
            )
    return {
        "nb_contacts_total": sum(len(values) for values in grouped.values()),
        "nb_proprietaires": len(grouped["proprietaire"]),
        "nb_mandants": len(grouped["mandant"]),
        "nb_acquereurs": len(grouped["acquereur"]),
        "nb_notaires": len(grouped["notaire_entree"]) + len(grouped["notaire_sortie"]),
        "has_contact_detail": has_contact_detail,
        "has_contact_list_activity": has_contact_list_activity,
        "last_contact_list_date_last_traitement": last_contact_list_date_last_traitement or None,
        "last_contact_list_date_maj": last_contact_list_date_maj or None,
        "last_contact_detail_date_maj": last_contact_detail_date_maj or None,
        "proprietaires_noms": " | ".join(grouped["proprietaire"]) or None,
        "mandants_noms": " | ".join(grouped["mandant"]) or None,
        "acquereurs_noms": " | ".join(grouped["acquereur"]) or None,
        "notaire_entree_nom": " | ".join(grouped["notaire_entree"]) or None,
        "notaire_sortie_nom": " | ".join(grouped["notaire_sortie"]) or None,
    }


def group_broadcasts(rows: Iterable[sqlite3.Row]) -> Dict[str, object]:
    names: list[str] = []
    statuses: list[str] = []
    for row in rows:
        name = (row["broadcast_nom"] or "").strip()
        status = (row["export_status"] or "").strip()
        if name and name not in names:
            names.append(name)
        if status:
            entry = f"{name}: {status}" if name else status
            if entry not in statuses:
                statuses.append(entry)
    return {
        "nb_broadcasts": len(list(rows)) if False else None,
        "has_broadcast": 1 if names or statuses else 0,
        "is_broadcasted": 1 if names else 0,
        "broadcast_names": " | ".join(names) or None,
        "broadcast_status_summary": " | ".join(statuses) or None,
    }


def build_case_index(conn: sqlite3.Connection) -> dict[str, int]:
    init_build_schema(conn)
    build_at = now_sqlite(conn)

    parc_rows = conn.execute("SELECT * FROM actif_parc_courant").fetchall()
    contact_rows = conn.execute("SELECT * FROM actif_annonce_contact").fetchall()
    broadcast_rows = conn.execute("SELECT * FROM actif_broadcast_courant").fetchall()

    contacts_by_annonce: Dict[str, list[sqlite3.Row]] = {}
    for row in contact_rows:
        contacts_by_annonce.setdefault(str(row["annonce_id"]), []).append(row)

    broadcasts_by_annonce: Dict[str, list[sqlite3.Row]] = {}
    for row in broadcast_rows:
        broadcasts_by_annonce.setdefault(str(row["annonce_id"]), []).append(row)

    conn.execute("DELETE FROM actif_case_index")

    insert_rows = []
    for row in parc_rows:
        annonce_id = str(row["annonce_id"])
        contact_group = group_contacts(contacts_by_annonce.get(annonce_id, []))
        broadcast_group_rows = broadcasts_by_annonce.get(annonce_id, [])
        broadcast_group = group_broadcasts(broadcast_group_rows)
        nb_broadcasts = len(broadcast_group_rows)
        insert_rows.append(
            (
                annonce_id,
                row["active_current"],
                row["listing_date_maj"],
                row["first_seen_at"],
                row["last_seen_at"],
                row["removed_at"],
                row["statut_id"],
                row["statut_name"],
                row["no_dossier"],
                row["no_mandat"],
                row["agence_id"],
                row["negociateur_id"],
                row["archive"],
                row["diffusable"],
                row["partage"],
                row["valide"],
                row["prix"],
                row["surface"],
                row["titre"],
                row["ville"],
                row["code_postal"],
                row["mandat_id"],
                row["mandat_numero"],
                row["mandat_type"],
                row["mandat_debut"],
                row["mandat_fin"],
                row["mandat_cloture"],
                row["mandat_montant"],
                1 if row["mandat_id"] or row["mandat_numero"] or row["mandat_type"] else 0,
                contact_group["nb_contacts_total"],
                contact_group["nb_proprietaires"],
                contact_group["nb_mandants"],
                contact_group["nb_acquereurs"],
                contact_group["nb_notaires"],
                contact_group["has_contact_detail"],
                contact_group["has_contact_list_activity"],
                contact_group["last_contact_list_date_last_traitement"],
                contact_group["last_contact_list_date_maj"],
                contact_group["last_contact_detail_date_maj"],
                contact_group["proprietaires_noms"],
                contact_group["mandants_noms"],
                contact_group["acquereurs_noms"],
                contact_group["notaire_entree_nom"],
                contact_group["notaire_sortie_nom"],
                nb_broadcasts,
                broadcast_group["has_broadcast"],
                broadcast_group["is_broadcasted"],
                broadcast_group["broadcast_names"],
                broadcast_group["broadcast_status_summary"],
                build_at,
            )
        )

    conn.executemany(
        """
        INSERT INTO actif_case_index(
            annonce_id, active_current, listing_date_maj, first_seen_at, last_seen_at, removed_at,
            statut_id, statut_name, no_dossier, no_mandat, agence_id, negociateur_id, archive,
            diffusable, partage, valide, prix, surface, titre, ville, code_postal,
            mandat_id, mandat_numero, mandat_type, mandat_debut, mandat_fin, mandat_cloture,
            mandat_montant, has_mandat, nb_contacts_total, nb_proprietaires, nb_mandants,
            nb_acquereurs, nb_notaires, has_contact_detail, has_contact_list_activity,
            last_contact_list_date_last_traitement, last_contact_list_date_maj, last_contact_detail_date_maj,
            proprietaires_noms, mandants_noms,
            acquereurs_noms, notaire_entree_nom, notaire_sortie_nom, nb_broadcasts, has_broadcast,
            is_broadcasted, broadcast_names, broadcast_status_summary, build_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        insert_rows,
    )
    conn.commit()
    return {"case_rows": len(insert_rows)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Construit la table finale consolidee ACTIF.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Chemin de la base SQLite ACTIF.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    conn = connect_db(Path(args.db_path))
    summary = build_case_index(conn)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
