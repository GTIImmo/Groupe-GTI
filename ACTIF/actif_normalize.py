from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "actif.sqlite"


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_normalized_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS actif_parc_courant (
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
            normalized_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS actif_annonce_contact (
            annonce_id TEXT NOT NULL,
            contact_id TEXT NOT NULL,
            role_contact TEXT NOT NULL,
            contact_list_date_last_traitement TEXT,
            contact_list_date_maj TEXT,
            civilite TEXT,
            nom TEXT,
            prenom TEXT,
            email TEXT,
            portable TEXT,
            fixe TEXT,
            ville TEXT,
            code_postal TEXT,
            archive TEXT,
            date_enregistrement TEXT,
            date_maj TEXT,
            id_negociateur TEXT,
            ref_couple TEXT,
            contact_list_json TEXT,
            contact_detail_date_maj TEXT,
            contact_detail_json TEXT,
            recherches_json TEXT,
            normalized_at TEXT NOT NULL,
            PRIMARY KEY (annonce_id, contact_id, role_contact),
            FOREIGN KEY (annonce_id) REFERENCES actif_parc_courant(annonce_id)
        );

        CREATE TABLE IF NOT EXISTS actif_contact_courant (
            contact_id TEXT PRIMARY KEY,
            contact_list_date_last_traitement TEXT,
            contact_list_date_maj TEXT,
            contact_detail_date_maj TEXT,
            civilite TEXT,
            nom TEXT,
            prenom TEXT,
            email TEXT,
            portable TEXT,
            fixe TEXT,
            ville TEXT,
            code_postal TEXT,
            archive TEXT,
            date_enregistrement TEXT,
            id_negociateur TEXT,
            ref_couple TEXT,
            contact_list_json TEXT,
            contact_detail_json TEXT,
            recherches_json TEXT,
            normalized_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS actif_broadcast_courant (
            broadcast_id TEXT NOT NULL,
            annonce_id TEXT NOT NULL,
            broadcast_nom TEXT,
            commercial_id TEXT,
            commercial_type TEXT,
            commercial_nom TEXT,
            commercial_prenom TEXT,
            export_status TEXT,
            raw_json TEXT,
            normalized_at TEXT NOT NULL,
            PRIMARY KEY (broadcast_id, annonce_id, commercial_id)
        );

        CREATE INDEX IF NOT EXISTS idx_actif_parc_courant_active_current
            ON actif_parc_courant(active_current);
        CREATE INDEX IF NOT EXISTS idx_actif_annonce_contact_annonce
            ON actif_annonce_contact(annonce_id);
        CREATE INDEX IF NOT EXISTS idx_actif_annonce_contact_role
            ON actif_annonce_contact(role_contact);
        CREATE INDEX IF NOT EXISTS idx_actif_annonce_contact_contact
            ON actif_annonce_contact(contact_id);
        CREATE INDEX IF NOT EXISTS idx_actif_broadcast_courant_annonce
            ON actif_broadcast_courant(annonce_id);
        """
    )
    existing_contact_columns = {row["name"] for row in conn.execute("PRAGMA table_info(actif_annonce_contact)")}
    for column_name, ddl in (
        ("contact_list_date_last_traitement", "ALTER TABLE actif_annonce_contact ADD COLUMN contact_list_date_last_traitement TEXT"),
        ("contact_list_date_maj", "ALTER TABLE actif_annonce_contact ADD COLUMN contact_list_date_maj TEXT"),
        ("contact_detail_date_maj", "ALTER TABLE actif_annonce_contact ADD COLUMN contact_detail_date_maj TEXT"),
        ("contact_list_json", "ALTER TABLE actif_annonce_contact ADD COLUMN contact_list_json TEXT"),
        ("contact_detail_json", "ALTER TABLE actif_annonce_contact ADD COLUMN contact_detail_json TEXT"),
        ("recherches_json", "ALTER TABLE actif_annonce_contact ADD COLUMN recherches_json TEXT"),
    ):
        if column_name not in existing_contact_columns:
            conn.execute(ddl)
    existing_contact_current_columns = {row["name"] for row in conn.execute("PRAGMA table_info(actif_contact_courant)")}
    for column_name, ddl in (
        ("contact_list_date_last_traitement", "ALTER TABLE actif_contact_courant ADD COLUMN contact_list_date_last_traitement TEXT"),
        ("contact_list_date_maj", "ALTER TABLE actif_contact_courant ADD COLUMN contact_list_date_maj TEXT"),
        ("contact_list_json", "ALTER TABLE actif_contact_courant ADD COLUMN contact_list_json TEXT"),
    ):
        if column_name not in existing_contact_current_columns:
            conn.execute(ddl)
    conn.commit()


def now_sqlite(conn: sqlite3.Connection) -> str:
    return str(conn.execute("SELECT datetime('now')").fetchone()[0])


def load_json(text: Optional[str]) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def extract_locality(contact: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    localite = contact.get("localite")
    if not isinstance(localite, dict):
        return None, None
    nested = localite.get("localite")
    if not isinstance(nested, dict):
        return None, None
    return nested.get("ville"), nested.get("code")


def build_contact_detail_index(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT contact_id, contact_list_date_last_traitement, contact_list_date_maj, contact_date_maj,
               contact_list_json, contact_json, recherches_json
        FROM actif_contact
        """
    ).fetchall()
    index: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        contact_json = load_json(row["contact_json"])
        recherches_json = load_json(row["recherches_json"])
        if not isinstance(contact_json, dict):
            contact_json = {}
        index[str(row["contact_id"])] = {
            "contact_list_date_last_traitement": row["contact_list_date_last_traitement"],
            "contact_list_date_maj": row["contact_list_date_maj"],
            "contact_date_maj": row["contact_date_maj"],
            "contact_list_json": load_json(row["contact_list_json"]),
            "contact": contact_json,
            "recherches": recherches_json,
        }
    return index


def iter_contacts(contacts_payload: Any) -> Iterable[tuple[str, Dict[str, Any]]]:
    if not isinstance(contacts_payload, dict):
        return []
    rows: list[tuple[str, Dict[str, Any]]] = []
    role_map = {
        "proprietaires": "proprietaire",
        "mandants": "mandant",
        "acquereurs": "acquereur",
    }
    for source_key, role_contact in role_map.items():
        source = contacts_payload.get(source_key) or []
        if not isinstance(source, list):
            continue
        for item in source:
            if isinstance(item, dict):
                rows.append((role_contact, item))
    notaires = contacts_payload.get("notaires")
    if isinstance(notaires, dict):
        for source_key, role_contact in (("entree", "notaire_entree"), ("sortie", "notaire_sortie")):
            item = notaires.get(source_key)
            if isinstance(item, dict):
                rows.append((role_contact, item))
    return rows


def normalize(conn: sqlite3.Connection) -> dict[str, int]:
    init_normalized_schema(conn)
    normalized_at = now_sqlite(conn)
    contact_detail_index = build_contact_detail_index(conn)

    rows = conn.execute(
        """
        SELECT annonce_id, active_current, listing_date_maj, first_seen_at, last_seen_at, removed_at,
               statut_id, statut_name, no_dossier, no_mandat, agence_id, negociateur_id, archive,
               diffusable, partage, valide, prix, surface, titre, ville, code_postal,
               mandat_json, contacts_json
        FROM actif_annonce
        """
    ).fetchall()

    conn.execute("DELETE FROM actif_annonce_contact")
    conn.execute("DELETE FROM actif_parc_courant")
    conn.execute("DELETE FROM actif_contact_courant")
    conn.execute("DELETE FROM actif_broadcast_courant")

    parc_rows = []
    contact_rows = []
    contact_current_rows = []
    for row in rows:
        mandat = load_json(row["mandat_json"])
        parc_rows.append(
            (
                row["annonce_id"],
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
                mandat.get("id") if isinstance(mandat, dict) else None,
                mandat.get("numero") if isinstance(mandat, dict) else None,
                mandat.get("type") if isinstance(mandat, dict) else None,
                mandat.get("debut") if isinstance(mandat, dict) else None,
                mandat.get("fin") if isinstance(mandat, dict) else None,
                mandat.get("cloture") if isinstance(mandat, dict) else None,
                mandat.get("montant") if isinstance(mandat, dict) else None,
                normalized_at,
            )
        )

        contacts_payload = load_json(row["contacts_json"])
        for role_contact, contact in iter_contacts(contacts_payload):
            contact_id = str(contact.get("id") or "").strip()
            if not contact_id:
                continue
            detail = contact_detail_index.get(contact_id, {})
            detail_contact = detail.get("contact") if isinstance(detail.get("contact"), dict) else {}
            coordonnees = contact.get("coordonnees")
            if not isinstance(coordonnees, dict):
                coordonnees = {}
            detail_coordonnees = detail_contact.get("coordonnees")
            if not isinstance(detail_coordonnees, dict):
                detail_coordonnees = {}
            ville, code_postal = extract_locality(contact)
            detail_ville, detail_code_postal = extract_locality(detail_contact) if detail_contact else (None, None)
            contact_rows.append(
                (
                    row["annonce_id"],
                    contact_id,
                    role_contact,
                    detail.get("contact_list_date_last_traitement"),
                    detail.get("contact_list_date_maj"),
                    detail_contact.get("civilite") or contact.get("civilite"),
                    detail_contact.get("nom") or contact.get("nom"),
                    detail_contact.get("prenom") or contact.get("prenom"),
                    detail_coordonnees.get("email") or coordonnees.get("email"),
                    detail_coordonnees.get("portable") or coordonnees.get("portable"),
                    detail_coordonnees.get("fixe") or coordonnees.get("fixe"),
                    detail_ville or ville,
                    detail_code_postal or code_postal,
                    detail_contact.get("archive") or contact.get("archive"),
                    detail_contact.get("dateenr") or contact.get("dateenr"),
                    contact.get("datemaj"),
                    detail_contact.get("id_negociateur") or contact.get("id_negociateur"),
                    detail_contact.get("refCouple") or contact.get("refCouple"),
                    json.dumps(detail.get("contact_list_json"), ensure_ascii=False) if detail.get("contact_list_json") is not None else None,
                    detail.get("contact_date_maj"),
                    json.dumps(detail_contact, ensure_ascii=False) if detail_contact else None,
                    json.dumps(detail.get("recherches"), ensure_ascii=False) if detail.get("recherches") is not None else None,
                    normalized_at,
                )
            )

    for contact_id, detail in contact_detail_index.items():
        detail_contact = detail.get("contact") if isinstance(detail.get("contact"), dict) else {}
        detail_coordonnees = detail_contact.get("coordonnees")
        if not isinstance(detail_coordonnees, dict):
            detail_coordonnees = {}
        ville, code_postal = extract_locality(detail_contact) if detail_contact else (None, None)
        contact_current_rows.append(
            (
                contact_id,
                detail.get("contact_list_date_last_traitement"),
                detail.get("contact_list_date_maj"),
                detail.get("contact_date_maj"),
                detail_contact.get("civilite"),
                detail_contact.get("nom"),
                detail_contact.get("prenom"),
                detail_coordonnees.get("email"),
                detail_coordonnees.get("portable"),
                detail_coordonnees.get("fixe"),
                ville,
                code_postal,
                detail_contact.get("archive"),
                detail_contact.get("dateenr"),
                detail_contact.get("id_negociateur"),
                detail_contact.get("refCouple"),
                json.dumps(detail.get("contact_list_json"), ensure_ascii=False) if detail.get("contact_list_json") is not None else None,
                json.dumps(detail_contact, ensure_ascii=False) if detail_contact else None,
                json.dumps(detail.get("recherches"), ensure_ascii=False) if detail.get("recherches") is not None else None,
                normalized_at,
            )
        )

    broadcast_rows = conn.execute(
        """
        SELECT l.broadcast_id, l.annonce_id, b.nom AS broadcast_nom, l.commercial_id, l.commercial_type,
               l.commercial_nom, l.commercial_prenom, l.export_status, l.raw_json
        FROM actif_broadcast_listing l
        LEFT JOIN actif_broadcast b ON b.broadcast_id = l.broadcast_id
        """
    ).fetchall()
    broadcast_current_rows = [
        (
            row["broadcast_id"],
            row["annonce_id"],
            row["broadcast_nom"],
            row["commercial_id"],
            row["commercial_type"],
            row["commercial_nom"],
            row["commercial_prenom"],
            row["export_status"],
            row["raw_json"],
            normalized_at,
        )
        for row in broadcast_rows
    ]

    conn.executemany(
        """
        INSERT INTO actif_parc_courant(
            annonce_id, active_current, listing_date_maj, first_seen_at, last_seen_at, removed_at,
            statut_id, statut_name, no_dossier, no_mandat, agence_id, negociateur_id, archive,
            diffusable, partage, valide, prix, surface, titre, ville, code_postal,
            mandat_id, mandat_numero, mandat_type, mandat_debut, mandat_fin, mandat_cloture,
            mandat_montant, normalized_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        parc_rows,
    )

    conn.executemany(
        """
        INSERT INTO actif_annonce_contact(
            annonce_id, contact_id, role_contact, contact_list_date_last_traitement, contact_list_date_maj,
            civilite, nom, prenom, email, portable, fixe,
            ville, code_postal, archive, date_enregistrement, date_maj, id_negociateur, ref_couple,
            contact_list_json, contact_detail_date_maj, contact_detail_json, recherches_json, normalized_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        contact_rows,
    )

    conn.executemany(
        """
        INSERT INTO actif_contact_courant(
            contact_id, contact_list_date_last_traitement, contact_list_date_maj, contact_detail_date_maj,
            civilite, nom, prenom, email, portable, fixe,
            ville, code_postal, archive, date_enregistrement, id_negociateur, ref_couple,
            contact_list_json, contact_detail_json, recherches_json, normalized_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        contact_current_rows,
    )
    conn.executemany(
        """
        INSERT INTO actif_broadcast_courant(
            broadcast_id, annonce_id, broadcast_nom, commercial_id, commercial_type,
            commercial_nom, commercial_prenom, export_status, raw_json, normalized_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        broadcast_current_rows,
    )
    conn.commit()
    return {
        "parc_rows": len(parc_rows),
        "contact_rows": len(contact_rows),
        "contact_current_rows": len(contact_current_rows),
        "broadcast_current_rows": len(broadcast_current_rows),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalise la base ACTIF en tables metier legeres.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Chemin de la base SQLite ACTIF.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    conn = connect_db(Path(args.db_path))
    summary = normalize(conn)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
