from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
DEFAULT_PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
DEFAULT_REPORT_DIR = ROOT / "exports_contacts_audit"


GENERIC_CONTACT_NAMES = {
    "m",
    "mr",
    "mme",
    "m mme",
    "mr mme",
    "monsieur",
    "madame",
    "monsieur madame",
    "monsieur mme",
    "m et mme",
    "mr et mme",
}

SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class ContactRow:
    hektor_contact_id: str
    hektor_agence_id: str | None
    hektor_negociateur_id: str | None
    civilite: str | None
    nom: str | None
    prenom: str | None
    archive: int
    date_enregistrement: str | None
    date_maj: str | None
    email: str | None
    portable: str | None
    fixe: str | None
    ville: str | None
    code_postal: str | None
    adresse: str | None
    typologie_json: str | None
    raw_json: str | None
    synced_at: str | None

    @property
    def display_name(self) -> str:
        return " ".join(part for part in [self.civilite, self.prenom, self.nom] if clean_text(part)) or f"Contact {self.hektor_contact_id}"

    @property
    def email_normalized(self) -> str:
        return normalize_email(self.email)

    @property
    def phone_primary(self) -> str | None:
        return clean_text(self.portable) or clean_text(self.fixe) or None

    @property
    def phone_normalized(self) -> str:
        return normalize_phone(self.portable) or normalize_phone(self.fixe)

    @property
    def first_name_normalized(self) -> str:
        return normalize_text(self.prenom)

    @property
    def last_name_normalized(self) -> str:
        return normalize_text(self.nom)

    @property
    def city_normalized(self) -> str:
        return normalize_text(self.ville)

    @property
    def postal_code_normalized(self) -> str:
        return clean_text(self.code_postal) or ""

    @property
    def completeness_score(self) -> int:
        return sum(
            1
            for value in (
                self.email,
                self.portable,
                self.fixe,
                self.ville,
                self.code_postal,
                self.prenom,
                self.nom,
                self.date_maj,
            )
            if clean_text(value)
        )


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_text(value: Any) -> str:
    text = clean_text(value).lower()
    text = "".join(ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_email(value: Any) -> str:
    return clean_text(value).lower()


def normalize_phone(value: Any) -> str:
    digits = re.sub(r"\D+", "", clean_text(value))
    if digits.startswith("33") and len(digits) == 11:
        digits = f"0{digits[2:]}"
    return digits if len(digits) >= 9 else ""


def stable_hash(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


def short_hash(value: str) -> str:
    if not value:
        return ""
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def parse_bool_archive(value: Any) -> int:
    return 1 if clean_text(value).lower() in {"1", "true", "oui", "yes"} else 0


def json_array(value: Any) -> str:
    return json.dumps(value or [], ensure_ascii=False, separators=(",", ":"))


def parse_json_value(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    text = clean_text(value)
    if not text:
        return fallback
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def json_items(value: Any) -> list[dict[str, Any]]:
    data = parse_json_value(value, [])
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def first_non_empty(*values: Any) -> str | None:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return None


def normalize_contact_ids(values: Iterable[Any]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        for chunk in clean_text(raw_value).replace(";", ",").split(","):
            contact_id = clean_text(chunk)
            if not contact_id:
                continue
            if not contact_id.isdigit():
                raise ValueError(f"ID contact invalide: {contact_id}")
            if contact_id in seen:
                continue
            seen.add(contact_id)
            ids.append(contact_id)
    return ids


def active_archive_flag(value: Any) -> int:
    return 0 if parse_bool_archive(value) else 1


def contact_from_row(row: sqlite3.Row) -> ContactRow:
    return ContactRow(
        hektor_contact_id=clean_text(row["hektor_contact_id"]),
        hektor_agence_id=clean_text(row["hektor_agence_id"]) or None,
        hektor_negociateur_id=clean_text(row["hektor_negociateur_id"]) or None,
        civilite=clean_text(row["civilite"]) or None,
        nom=clean_text(row["nom"]) or None,
        prenom=clean_text(row["prenom"]) or None,
        archive=parse_bool_archive(row["archive"]),
        date_enregistrement=clean_text(row["date_enregistrement"]) or None,
        date_maj=clean_text(row["date_maj"]) or None,
        email=clean_text(row["email"]) or None,
        portable=clean_text(row["portable"]) or None,
        fixe=clean_text(row["fixe"]) or None,
        ville=clean_text(row["ville"]) or None,
        code_postal=clean_text(row["code_postal"]) or None,
        adresse=clean_text(row["adresse"]) or None,
        typologie_json=clean_text(row["typologie_json"]) or None,
        raw_json=clean_text(row["raw_json"]) or None,
        synced_at=clean_text(row["synced_at"]) or None,
    )


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_contacts_schema(conn: sqlite3.Connection) -> None:
    relation_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(app_contact_relation_current)").fetchall()
    }
    if relation_columns and "relation_key" not in relation_columns:
        conn.execute("DROP TABLE app_contact_relation_current")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS app_contact_current (
            hektor_contact_id TEXT PRIMARY KEY,
            hektor_agence_id TEXT,
            hektor_negociateur_id TEXT,
            negociateur_email TEXT,
            commercial_nom TEXT,
            agence_nom TEXT,
            civilite TEXT,
            nom TEXT,
            prenom TEXT,
            display_name TEXT NOT NULL,
            archive INTEGER NOT NULL DEFAULT 0,
            date_enregistrement TEXT,
            date_maj TEXT,
            email TEXT,
            phone_primary TEXT,
            phone_secondary TEXT,
            ville TEXT,
            code_postal TEXT,
            adresse TEXT,
            typologies_json TEXT NOT NULL DEFAULT '[]',
            relation_roles_json TEXT NOT NULL DEFAULT '[]',
            linked_annonce_count INTEGER NOT NULL DEFAULT 0,
            active_search_count INTEGER NOT NULL DEFAULT 0,
            total_search_count INTEGER NOT NULL DEFAULT 0,
            has_contact_detail INTEGER NOT NULL DEFAULT 0,
            contact_detail_synced_at TEXT,
            supabase_sync_eligible INTEGER NOT NULL DEFAULT 0,
            eligibility_reasons_json TEXT NOT NULL DEFAULT '[]',
            duplicate_group_count INTEGER NOT NULL DEFAULT 0,
            duplicate_max_severity TEXT,
            duplicate_primary_candidate_id TEXT,
            completeness_score INTEGER NOT NULL DEFAULT 0,
            source_hash TEXT NOT NULL,
            refreshed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS app_contact_relation_current (
            relation_key TEXT PRIMARY KEY,
            hektor_contact_id TEXT NOT NULL,
            hektor_annonce_id TEXT NOT NULL,
            app_dossier_id INTEGER,
            numero_dossier TEXT,
            numero_mandat TEXT,
            titre_bien TEXT,
            role_contact TEXT NOT NULL,
            contact_date_maj TEXT,
            relation_source TEXT NOT NULL DEFAULT 'api_annonce_detail',
            transaction_type TEXT,
            transaction_id TEXT,
            transaction_state TEXT,
            transaction_date TEXT,
            transaction_amount TEXT,
            is_active_annonce INTEGER NOT NULL DEFAULT 0,
            last_seen_at TEXT,
            refreshed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS app_contact_search_current (
            contact_search_key TEXT PRIMARY KEY,
            hektor_contact_id TEXT NOT NULL,
            search_index INTEGER NOT NULL,
            archive INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 0,
            offre TEXT,
            villes_json TEXT NOT NULL DEFAULT '[]',
            types_json TEXT NOT NULL DEFAULT '[]',
            criteres_json TEXT NOT NULL DEFAULT '[]',
            prix_min TEXT,
            prix_max TEXT,
            surface_min TEXT,
            surface_max TEXT,
            pieces_min TEXT,
            pieces_max TEXT,
            chambre_min TEXT,
            chambre_max TEXT,
            surface_terrain_min TEXT,
            surface_terrain_max TEXT,
            contact_date_maj TEXT,
            refreshed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS app_contact_duplicate_group_current (
            duplicate_group_id TEXT PRIMARY KEY,
            rule_code TEXT NOT NULL,
            severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
            review_status TEXT NOT NULL DEFAULT 'proposed',
            archive_pattern TEXT NOT NULL,
            member_count INTEGER NOT NULL,
            active_count INTEGER NOT NULL,
            archived_count INTEGER NOT NULL,
            linked_annonce_count INTEGER NOT NULL DEFAULT 0,
            primary_candidate_hektor_contact_id TEXT,
            normalized_key_hash TEXT NOT NULL,
            suspected_mass_archive_error INTEGER NOT NULL DEFAULT 0,
            review_hint TEXT,
            refreshed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS app_contact_duplicate_member_current (
            duplicate_group_id TEXT NOT NULL,
            hektor_contact_id TEXT NOT NULL,
            is_primary_candidate INTEGER NOT NULL DEFAULT 0,
            archive INTEGER NOT NULL DEFAULT 0,
            display_name TEXT NOT NULL,
            email_hash TEXT,
            phone_hash TEXT,
            date_maj TEXT,
            linked_annonce_count INTEGER NOT NULL DEFAULT 0,
            completeness_score INTEGER NOT NULL DEFAULT 0,
            member_rank INTEGER NOT NULL DEFAULT 0,
            refreshed_at TEXT NOT NULL,
            PRIMARY KEY (duplicate_group_id, hektor_contact_id)
        );

        CREATE TABLE IF NOT EXISTS app_contact_audit_run (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL,
            contacts_total INTEGER NOT NULL,
            contacts_active INTEGER NOT NULL,
            contacts_archived INTEGER NOT NULL,
            duplicate_group_total INTEGER NOT NULL,
            duplicate_member_total INTEGER NOT NULL,
            high_or_critical_group_total INTEGER NOT NULL,
            suspected_mass_archive_error_total INTEGER NOT NULL,
            report_summary_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_app_contact_current_archive
            ON app_contact_current(archive, date_maj);
        CREATE INDEX IF NOT EXISTS idx_app_contact_current_name
            ON app_contact_current(nom, prenom);
        CREATE INDEX IF NOT EXISTS idx_app_contact_current_email
            ON app_contact_current(email);
        CREATE INDEX IF NOT EXISTS idx_app_contact_current_phone
            ON app_contact_current(phone_primary);
        CREATE INDEX IF NOT EXISTS idx_app_contact_current_nego
            ON app_contact_current(negociateur_email, hektor_negociateur_id);
        CREATE INDEX IF NOT EXISTS idx_app_contact_relation_contact
            ON app_contact_relation_current(hektor_contact_id);
        CREATE INDEX IF NOT EXISTS idx_app_contact_relation_annonce
            ON app_contact_relation_current(hektor_annonce_id);
        CREATE INDEX IF NOT EXISTS idx_app_contact_relation_transaction
            ON app_contact_relation_current(transaction_type, transaction_id);
        CREATE INDEX IF NOT EXISTS idx_app_contact_relation_role_active
            ON app_contact_relation_current(role_contact, is_active_annonce);
        CREATE INDEX IF NOT EXISTS idx_app_contact_search_contact
            ON app_contact_search_current(hektor_contact_id);
        CREATE INDEX IF NOT EXISTS idx_app_contact_search_active
            ON app_contact_search_current(is_active, archive);
        CREATE INDEX IF NOT EXISTS idx_app_contact_duplicate_severity
            ON app_contact_duplicate_group_current(severity, suspected_mass_archive_error);
        CREATE INDEX IF NOT EXISTS idx_app_contact_duplicate_member_contact
            ON app_contact_duplicate_member_current(hektor_contact_id);
        """
    )
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(app_contact_current)").fetchall()}
    for column_name, column_type in (
        ("negociateur_email", "TEXT"),
        ("commercial_nom", "TEXT"),
        ("agence_nom", "TEXT"),
        ("active_search_count", "INTEGER NOT NULL DEFAULT 0"),
        ("total_search_count", "INTEGER NOT NULL DEFAULT 0"),
        ("has_contact_detail", "INTEGER NOT NULL DEFAULT 0"),
        ("contact_detail_synced_at", "TEXT"),
        ("supabase_sync_eligible", "INTEGER NOT NULL DEFAULT 0"),
        ("eligibility_reasons_json", "TEXT NOT NULL DEFAULT '[]'"),
        ("adresse", "TEXT"),
    ):
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE app_contact_current ADD COLUMN {column_name} {column_type}")
    conn.commit()


def load_contacts(
    conn: sqlite3.Connection,
    limit: int | None = None,
    contact_ids: Iterable[str] | None = None,
) -> list[ContactRow]:
    ids = normalize_contact_ids(contact_ids or [])
    params: list[Any] = []
    sql = """
        SELECT hektor_contact_id, hektor_agence_id, hektor_negociateur_id, civilite, nom, prenom,
               archive, date_enregistrement, date_maj, email, portable, fixe, ville, code_postal, adresse,
               typologie_json, raw_json, synced_at
        FROM hektor_contact
        WHERE NULLIF(TRIM(hektor_contact_id), '') IS NOT NULL
    """
    if ids:
        placeholders = ",".join("?" for _ in ids)
        sql += f" AND CAST(hektor_contact_id AS TEXT) IN ({placeholders})\n"
        params.extend(ids)
    sql += " ORDER BY CAST(hektor_contact_id AS INTEGER)"
    if limit and limit > 0:
        sql += f" LIMIT {int(limit)}"
    return [contact_from_row(row) for row in conn.execute(sql, params).fetchall()]


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    return conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone() is not None


def load_active_annonce_ids(hektor_conn: sqlite3.Connection) -> set[str]:
    if table_exists(hektor_conn, "case_dossier_source"):
        return {
            clean_text(row["hektor_annonce_id"])
            for row in hektor_conn.execute(
                """
                SELECT hektor_annonce_id
                FROM case_dossier_source
                WHERE COALESCE(archive, '0') = '0'
                  AND NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
                """
            )
        }
    if table_exists(hektor_conn, "hektor_annonce"):
        return {
            clean_text(row["hektor_annonce_id"])
            for row in hektor_conn.execute(
                """
                SELECT hektor_annonce_id
                FROM hektor_annonce
                WHERE COALESCE(archive, '0') = '0'
                  AND NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
                """
            )
        }
    return set()


def contact_id_from_payload(value: Any) -> str:
    item = value[0] if isinstance(value, list) and value and isinstance(value[0], dict) else value
    if not isinstance(item, dict):
        return ""
    return first_non_empty(item.get("id"), item.get("id_contact"), item.get("contact_id")) or ""


def load_relations(
    hektor_conn: sqlite3.Connection,
    phase2_conn: sqlite3.Connection,
    contact_ids: Iterable[str] | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, set[str]]]:
    contact_filter = set(normalize_contact_ids(contact_ids or []))
    dossier_by_annonce: dict[str, sqlite3.Row] = {}
    for row in phase2_conn.execute(
        """
        SELECT d.id AS app_dossier_id, d.hektor_annonce_id, d.numero_dossier, d.numero_mandat, vg.titre_bien
        FROM app_dossier d
        LEFT JOIN app_view_generale vg ON vg.app_dossier_id = d.id
        WHERE d.hektor_annonce_id IS NOT NULL
        """
    ):
        dossier_by_annonce[clean_text(row["hektor_annonce_id"])] = row

    active_annonce_ids = load_active_annonce_ids(hektor_conn)
    relation_by_key: dict[str, dict[str, Any]] = {}
    contact_filter_placeholders = ",".join("?" for _ in contact_filter)
    contact_filter_params = sorted(contact_filter)

    def add_relation(
        *,
        contact_id: str,
        annonce_id: str,
        role: str,
        contact_date_maj: str | None,
        relation_source: str,
        last_seen_at: str | None,
        transaction_type: str | None = None,
        transaction_id: str | None = None,
        transaction_state: str | None = None,
        transaction_date: str | None = None,
        transaction_amount: str | None = None,
    ) -> None:
        contact_id = clean_text(contact_id)
        annonce_id = clean_text(annonce_id)
        role = clean_text(role) or "contact"
        if not contact_id or not annonce_id:
            return
        if contact_filter and contact_id not in contact_filter:
            return
        dossier = dossier_by_annonce.get(annonce_id)
        source_identity = relation_source if clean_text(transaction_id) else "non_transaction"
        relation_key = stable_hash(
            {
                "contact_id": contact_id,
                "annonce_id": annonce_id,
                "role": role,
                "source": source_identity,
                "transaction_type": transaction_type,
                "transaction_id": transaction_id,
            }
        )[:24]
        relation_by_key[relation_key] = {
            "relation_key": relation_key,
            "hektor_contact_id": contact_id,
            "hektor_annonce_id": annonce_id,
            "app_dossier_id": dossier["app_dossier_id"] if dossier else None,
            "numero_dossier": dossier["numero_dossier"] if dossier else None,
            "numero_mandat": dossier["numero_mandat"] if dossier else None,
            "titre_bien": dossier["titre_bien"] if dossier else None,
            "role_contact": role,
            "contact_date_maj": clean_text(contact_date_maj) or None,
            "relation_source": relation_source,
            "transaction_type": clean_text(transaction_type) or None,
            "transaction_id": clean_text(transaction_id) or None,
            "transaction_state": clean_text(transaction_state) or None,
            "transaction_date": clean_text(transaction_date) or None,
            "transaction_amount": clean_text(transaction_amount) or None,
            "is_active_annonce": int(annonce_id in active_annonce_ids),
            "last_seen_at": clean_text(last_seen_at) or None,
        }

    if table_exists(hektor_conn, "hektor_annonce_detail") and not contact_filter:
        for row in hektor_conn.execute(
            """
            SELECT hektor_annonce_id, proprietaires_json, synced_at
            FROM hektor_annonce_detail
            WHERE NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
              AND NULLIF(TRIM(proprietaires_json), '') IS NOT NULL
              AND TRIM(proprietaires_json) NOT IN ('[]', '{}', 'null')
            """
        ):
            for owner in json_items(row["proprietaires_json"]):
                add_relation(
                    contact_id=clean_text(owner.get("id")),
                    annonce_id=clean_text(row["hektor_annonce_id"]),
                    role="proprietaire",
                    contact_date_maj=clean_text(owner.get("datemaj")),
                    relation_source="api_annonce_detail_proprietaires",
                    last_seen_at=clean_text(row["synced_at"]) or None,
                )

    if table_exists(hektor_conn, "sync_annonce_contact_link"):
        link_where = """
            WHERE NULLIF(TRIM(hektor_contact_id), '') IS NOT NULL
              AND NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
        """
        link_params: list[Any] = []
        if contact_filter:
            link_where += f" AND CAST(hektor_contact_id AS TEXT) IN ({contact_filter_placeholders})"
            link_params.extend(contact_filter_params)
        for row in hektor_conn.execute(
            f"""
            SELECT hektor_annonce_id, hektor_contact_id, role_contact, contact_date_maj, last_seen_at
            FROM sync_annonce_contact_link
            {link_where}
            """,
            link_params,
        ):
            add_relation(
                contact_id=clean_text(row["hektor_contact_id"]),
                annonce_id=clean_text(row["hektor_annonce_id"]),
                role=clean_text(row["role_contact"]) or "contact",
                contact_date_maj=clean_text(row["contact_date_maj"]) or None,
                relation_source="sync_annonce_contact_link",
                last_seen_at=clean_text(row["last_seen_at"]) or None,
            )

    if table_exists(hektor_conn, "hektor_offre"):
        offre_where = "WHERE NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL"
        offre_params: list[Any] = []
        if contact_filter:
            offre_where += f" AND CAST(hektor_acquereur_id AS TEXT) IN ({contact_filter_placeholders})"
            offre_params.extend(contact_filter_params)
        for row in hektor_conn.execute(
            f"""
            SELECT hektor_offre_id, hektor_annonce_id, hektor_mandat_id, hektor_acquereur_id,
                   offre_state, offre_event_date, raw_date, raw_montant, acquereur_json, synced_at
            FROM hektor_offre
            {offre_where}
            """,
            offre_params,
        ):
            acquereur_items = json_items(row["acquereur_json"])
            acquereur = acquereur_items[0] if acquereur_items else {}
            add_relation(
                contact_id=first_non_empty(row["hektor_acquereur_id"], contact_id_from_payload(acquereur)) or "",
                annonce_id=clean_text(row["hektor_annonce_id"]),
                role="acquereur_offre",
                contact_date_maj=clean_text(acquereur.get("datemaj")) if isinstance(acquereur, dict) else None,
                relation_source="api_list_offres",
                transaction_type="offre",
                transaction_id=clean_text(row["hektor_offre_id"]),
                transaction_state=clean_text(row["offre_state"]),
                transaction_date=first_non_empty(row["offre_event_date"], row["raw_date"], row["synced_at"]),
                transaction_amount=clean_text(row["raw_montant"]),
                last_seen_at=clean_text(row["synced_at"]) or None,
            )

    if table_exists(hektor_conn, "hektor_compromis") and not contact_filter:
        for row in hektor_conn.execute(
            """
            SELECT hektor_compromis_id, hektor_annonce_id, hektor_mandat_id, compromis_state,
                   date_start, date_end, date_signature_acte, prix_publique, prix_net_vendeur,
                   acquereurs_json, synced_at
            FROM hektor_compromis
            WHERE NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
            """
        ):
            for acquereur in json_items(row["acquereurs_json"]):
                add_relation(
                    contact_id=contact_id_from_payload(acquereur),
                    annonce_id=clean_text(row["hektor_annonce_id"]),
                    role="acquereur_compromis",
                    contact_date_maj=clean_text(acquereur.get("datemaj")),
                    relation_source="api_list_compromis",
                    transaction_type="compromis",
                    transaction_id=clean_text(row["hektor_compromis_id"]),
                    transaction_state=clean_text(row["compromis_state"]),
                    transaction_date=first_non_empty(row["date_start"], row["date_signature_acte"], row["date_end"], row["synced_at"]),
                    transaction_amount=first_non_empty(row["prix_publique"], row["prix_net_vendeur"]),
                    last_seen_at=clean_text(row["synced_at"]) or None,
                )

    if table_exists(hektor_conn, "hektor_vente") and not contact_filter:
        for row in hektor_conn.execute(
            """
            SELECT hektor_vente_id, hektor_annonce_id, hektor_mandat_id, date_vente, prix,
                   acquereurs_json, synced_at
            FROM hektor_vente
            WHERE NULLIF(TRIM(hektor_annonce_id), '') IS NOT NULL
            """
        ):
            for acquereur in json_items(row["acquereurs_json"]):
                add_relation(
                    contact_id=contact_id_from_payload(acquereur),
                    annonce_id=clean_text(row["hektor_annonce_id"]),
                    role="acquereur_vente",
                    contact_date_maj=clean_text(acquereur.get("datemaj")),
                    relation_source="api_list_ventes",
                    transaction_type="vente",
                    transaction_id=clean_text(row["hektor_vente_id"]),
                    transaction_state="vente",
                    transaction_date=first_non_empty(row["date_vente"], row["synced_at"]),
                    transaction_amount=clean_text(row["prix"]),
                    last_seen_at=clean_text(row["synced_at"]) or None,
                )

    existing_contact_annonce_pairs = {
        (row["hektor_contact_id"], row["hektor_annonce_id"])
        for row in relation_by_key.values()
    }
    if table_exists(hektor_conn, "raw_api_response"):
        raw_columns = {
            row["name"]
            for row in hektor_conn.execute("PRAGMA table_info(raw_api_response)").fetchall()
        }
        fetched_expr = "fetched_at" if "fetched_at" in raw_columns else "NULL AS fetched_at"
        raw_where = "endpoint_name = 'contact_detail'"
        raw_params: list[Any] = []
        if contact_filter:
            raw_where += f" AND (CAST(object_id AS TEXT) IN ({contact_filter_placeholders}) OR CAST(object_id_key AS TEXT) IN ({contact_filter_placeholders}))"
            raw_params.extend(contact_filter_params)
            raw_params.extend(contact_filter_params)
        detail_rows = hektor_conn.execute(
            f"""
            SELECT object_id, object_id_key, payload_json, {fetched_expr}
            FROM raw_api_response
            WHERE {raw_where}
            ORDER BY id DESC
            """,
            raw_params,
        ).fetchall()
        seen_contacts: set[str] = set()
        for row in detail_rows:
            contact_id = first_non_empty(row["object_id_key"], row["object_id"])
            if not contact_id or contact_id in seen_contacts:
                continue
            seen_contacts.add(contact_id)
            try:
                payload = json.loads(row["payload_json"])
            except json.JSONDecodeError:
                continue
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, dict):
                continue
            contact_payload = data.get("contact") if isinstance(data.get("contact"), dict) else {}
            contact_date_maj = clean_text(contact_payload.get("datemaj") or contact_payload.get("date_maj")) or None
            for annonce in json_items(data.get("annonces")):
                annonce_id = clean_text(annonce.get("id"))
                pair = (clean_text(contact_id), annonce_id)
                if not annonce_id or pair in existing_contact_annonce_pairs:
                    continue
                add_relation(
                    contact_id=clean_text(contact_id),
                    annonce_id=annonce_id,
                    role="mandant",
                    contact_date_maj=contact_date_maj or clean_text(annonce.get("datemaj")) or None,
                    relation_source="api_contact_detail_annonces",
                    last_seen_at=clean_text(row["fetched_at"]) or None,
                )
                existing_contact_annonce_pairs.add(pair)

    relation_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    roles_by_contact: dict[str, set[str]] = defaultdict(set)
    for row in relation_by_key.values():
        contact_id = row["hektor_contact_id"]
        roles_by_contact[contact_id].add(row["role_contact"])
        relation_rows[contact_id].append(row)
    return relation_rows, roles_by_contact


def criteria_map(search: dict[str, Any]) -> dict[str, str]:
    output: dict[str, str] = {}
    criteres = search.get("criteres")
    items: list[dict[str, Any]]
    if isinstance(criteres, list):
        items = [item for item in criteres if isinstance(item, dict)]
    elif isinstance(criteres, dict):
        items = [item for item in criteres.values() if isinstance(item, dict)]
    else:
        items = []
    for item in items:
        key = clean_text(item.get("cle"))
        if not key:
            continue
        value = clean_text(item.get("valeur"))
        if value:
            output[key] = value
    return output


def load_contact_searches(
    hektor_conn: sqlite3.Connection,
    contact_ids: Iterable[str] | None = None,
) -> tuple[list[dict[str, Any]], Counter[str], Counter[str]]:
    if not table_exists(hektor_conn, "raw_api_response"):
        return [], Counter(), Counter()

    ids = normalize_contact_ids(contact_ids or [])
    where_parts = ["endpoint_name = 'contact_detail'"]
    params: list[Any] = []
    if ids:
        placeholders = ",".join("?" for _ in ids)
        where_parts.append(f"(CAST(object_id AS TEXT) IN ({placeholders}) OR CAST(object_id_key AS TEXT) IN ({placeholders}))")
        params.extend(ids)
        params.extend(ids)

    search_rows: list[dict[str, Any]] = []
    total_counts: Counter[str] = Counter()
    active_counts: Counter[str] = Counter()
    rows = hektor_conn.execute(
        f"""
        SELECT object_id, object_id_key, payload_json
        FROM raw_api_response
        WHERE {" AND ".join(where_parts)}
        ORDER BY id DESC
        """,
        params,
    ).fetchall()
    seen_contacts: set[str] = set()
    for row in rows:
        contact_id = first_non_empty(row["object_id_key"], row["object_id"])
        if not contact_id or contact_id in seen_contacts:
            continue
        seen_contacts.add(contact_id)
        try:
            payload = json.loads(row["payload_json"])
        except json.JSONDecodeError:
            continue
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            continue
        contact_payload = data.get("contact") if isinstance(data.get("contact"), dict) else {}
        contact_date_maj = clean_text(contact_payload.get("datemaj") or contact_payload.get("date_maj")) or None
        recherches = data.get("recherches")
        if not isinstance(recherches, list):
            continue
        for index, search in enumerate(recherches):
            if not isinstance(search, dict):
                continue
            archive = parse_bool_archive(search.get("archive"))
            is_active = int(not archive)
            criteria = criteria_map(search)
            key_payload = {"contact_id": contact_id, "index": index, "search": search}
            search_key = stable_hash(key_payload)[:24]
            total_counts[contact_id] += 1
            active_counts[contact_id] += is_active
            search_rows.append(
                {
                    "contact_search_key": search_key,
                    "hektor_contact_id": contact_id,
                    "search_index": index,
                    "archive": archive,
                    "is_active": is_active,
                    "offre": clean_text(search.get("offre")) or None,
                    "villes_json": json_array(search.get("villes") or []),
                    "types_json": json.dumps(search.get("types") or {}, ensure_ascii=False, separators=(",", ":")),
                    "criteres_json": json.dumps(search.get("criteres") or [], ensure_ascii=False, separators=(",", ":")),
                    "prix_min": criteria.get("ITEM_PRIX_MIN"),
                    "prix_max": criteria.get("ITEM_PRIX_MAX"),
                    "surface_min": criteria.get("ITEM_SURFACE_MIN"),
                    "surface_max": criteria.get("ITEM_SURFACE_MAX"),
                    "pieces_min": criteria.get("ITEM_PIECES_MIN"),
                    "pieces_max": criteria.get("ITEM_PIECES_MAX"),
                    "chambre_min": criteria.get("ITEM_CHAMBRE_MIN"),
                    "chambre_max": criteria.get("ITEM_CHAMBRE_MAX"),
                    "surface_terrain_min": criteria.get("ITEM_SURFACE_TERRAIN_MIN"),
                    "surface_terrain_max": criteria.get("ITEM_SURFACE_TERRAIN_MAX"),
                    "contact_date_maj": contact_date_maj,
                }
            )
    return search_rows, total_counts, active_counts


def load_contact_detail_state(
    hektor_conn: sqlite3.Connection,
    contact_ids: Iterable[str] | None = None,
) -> dict[str, str | None]:
    ids = normalize_contact_ids(contact_ids or [])
    detail_state: dict[str, str | None] = {}
    if table_exists(hektor_conn, "sync_contact_state"):
        columns = {
            row["name"]
            for row in hektor_conn.execute("PRAGMA table_info(sync_contact_state)").fetchall()
        }
        if {"hektor_contact_id", "last_detail_sync_at"}.issubset(columns):
            state_where = "WHERE last_detail_sync_at IS NOT NULL"
            state_params: list[Any] = []
            if ids:
                placeholders = ",".join("?" for _ in ids)
                state_where += f" AND CAST(hektor_contact_id AS TEXT) IN ({placeholders})"
                state_params.extend(ids)
            for row in hektor_conn.execute(
                f"""
                SELECT hektor_contact_id, last_detail_sync_at
                FROM sync_contact_state
                {state_where}
                """,
                state_params,
            ).fetchall():
                contact_id = clean_text(row["hektor_contact_id"])
                if contact_id:
                    detail_state[contact_id] = clean_text(row["last_detail_sync_at"]) or None

    if table_exists(hektor_conn, "raw_api_response"):
        raw_columns = {
            row["name"]
            for row in hektor_conn.execute("PRAGMA table_info(raw_api_response)").fetchall()
        }
        fetched_expr = "fetched_at" if "fetched_at" in raw_columns else "NULL AS fetched_at"
        raw_where = "endpoint_name = 'contact_detail'"
        raw_params: list[Any] = []
        if ids:
            placeholders = ",".join("?" for _ in ids)
            raw_where += f" AND (CAST(object_id AS TEXT) IN ({placeholders}) OR CAST(object_id_key AS TEXT) IN ({placeholders}))"
            raw_params.extend(ids)
            raw_params.extend(ids)
        rows = hektor_conn.execute(
            f"""
            SELECT object_id, object_id_key, {fetched_expr}
            FROM raw_api_response
            WHERE {raw_where}
            ORDER BY id DESC
            """,
            raw_params,
        ).fetchall()
        for row in rows:
            contact_id = first_non_empty(row["object_id_key"], row["object_id"])
            if not contact_id:
                continue
            detail_state.setdefault(contact_id, clean_text(row["fetched_at"]) or None)
    return detail_state


def load_directory_maps(hektor_conn: sqlite3.Connection) -> tuple[dict[str, dict[str, str | None]], dict[str, str | None]]:
    negotiators: dict[str, dict[str, str | None]] = {}
    agencies: dict[str, str | None] = {}
    if hektor_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hektor_agence'").fetchone():
        for row in hektor_conn.execute("SELECT hektor_agence_id, nom FROM hektor_agence"):
            agencies[clean_text(row["hektor_agence_id"])] = clean_text(row["nom"]) or None
    if hektor_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hektor_negociateur'").fetchone():
        for row in hektor_conn.execute(
            """
            SELECT hektor_negociateur_id, hektor_agence_id, nom, prenom, email
            FROM hektor_negociateur
            """
        ):
            negotiator_id = clean_text(row["hektor_negociateur_id"])
            if not negotiator_id:
                continue
            display_name = " ".join(part for part in [clean_text(row["prenom"]), clean_text(row["nom"])] if part) or None
            agency_id = clean_text(row["hektor_agence_id"])
            negotiators[negotiator_id] = {
                "negociateur_email": clean_text(row["email"]) or None,
                "commercial_nom": display_name,
                "agence_nom": agencies.get(agency_id),
            }
    return negotiators, agencies


def duplicate_key_groups(contacts: Iterable[ContactRow]) -> dict[tuple[str, str], list[ContactRow]]:
    groups: dict[tuple[str, str], list[ContactRow]] = defaultdict(list)
    for contact in contacts:
        first = contact.first_name_normalized
        last = contact.last_name_normalized
        full_name = f"{first} {last}".strip()
        email = contact.email_normalized
        phone = contact.phone_normalized
        city = contact.city_normalized
        postal_code = contact.postal_code_normalized
        name_is_generic = not first and (not last or last in GENERIC_CONTACT_NAMES or full_name in GENERIC_CONTACT_NAMES)

        if email:
            groups[("exact_email", email)].append(contact)
        if email and phone and (first or last):
            groups[("exact_full_identity", f"{email}|{phone}|{first}|{last}")].append(contact)
        if phone and (first or last) and not name_is_generic:
            groups[("exact_phone_name", f"{phone}|{first}|{last}")].append(contact)
        if first and last and not name_is_generic and (city or postal_code):
            groups[("same_name_place", f"{first}|{last}|{city}|{postal_code}")].append(contact)
    return {key: group for key, group in groups.items() if len(group) >= 2}


def archive_pattern(group: list[ContactRow]) -> str:
    archived = sum(contact.archive for contact in group)
    active = len(group) - archived
    if active and archived:
        return "active_plus_archived"
    if archived:
        return "all_archived"
    return "all_active"


def group_severity(rule_code: str, group: list[ContactRow]) -> str:
    pattern = archive_pattern(group)
    if rule_code == "exact_full_identity":
        return "critical" if pattern == "active_plus_archived" or len(group) >= 5 else "high"
    if rule_code == "exact_email":
        return "critical" if len(group) >= 10 else "high"
    if rule_code == "exact_phone_name":
        return "high" if pattern == "active_plus_archived" or len(group) >= 5 else "medium"
    return "medium" if pattern == "active_plus_archived" else "low"


def primary_candidate(group: list[ContactRow], linked_counts: dict[str, int]) -> ContactRow:
    return sorted(
        group,
        key=lambda contact: (
            contact.archive,
            -linked_counts.get(contact.hektor_contact_id, 0),
            -contact.completeness_score,
            clean_text(contact.date_maj),
            clean_text(contact.date_enregistrement),
            -int(contact.hektor_contact_id) if contact.hektor_contact_id.isdigit() else 0,
        ),
    )[0]


def review_hint(rule_code: str, severity: str, pattern: str, member_count: int, archived_count: int) -> str:
    if severity == "critical" and pattern == "active_plus_archived":
        return "Priorite forte: identite identique avec fiche active et fiche(s) archivee(s). Ne pas supprimer; verifier fusion Hektor."
    if pattern == "active_plus_archived" and archived_count >= 1:
        return "Suspect transfert archive: conserver le candidat actif le plus complet, verifier les fiches archivees."
    if member_count >= 10:
        return "Groupe massif: verifier s'il s'agit d'une adresse partagée ou d'une creation automatique."
    if rule_code == "same_name_place":
        return "Probable uniquement: verifier manuellement avant fusion."
    return "Doublon probable: classer puis traiter manuellement."


def build_duplicate_records(
    contacts: list[ContactRow],
    linked_counts: dict[str, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    group_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    best_duplicate_by_contact: dict[str, dict[str, Any]] = {}
    for (rule_code, normalized_key), group in duplicate_key_groups(contacts).items():
        sorted_group = sorted(group, key=lambda contact: int(contact.hektor_contact_id) if contact.hektor_contact_id.isdigit() else contact.hektor_contact_id)
        member_ids = [contact.hektor_contact_id for contact in sorted_group]
        active_count = sum(1 for contact in sorted_group if not contact.archive)
        archived_count = len(sorted_group) - active_count
        pattern = archive_pattern(sorted_group)
        severity = group_severity(rule_code, sorted_group)
        candidate = primary_candidate(sorted_group, linked_counts)
        linked_annonce_count = sum(linked_counts.get(contact.hektor_contact_id, 0) for contact in sorted_group)
        suspected_mass_archive_error = int(pattern == "active_plus_archived" and archived_count >= 1 and severity in {"high", "critical"})
        duplicate_group_id = stable_hash({"rule": rule_code, "members": member_ids})[:20]
        row = {
            "duplicate_group_id": duplicate_group_id,
            "rule_code": rule_code,
            "severity": severity,
            "archive_pattern": pattern,
            "member_count": len(sorted_group),
            "active_count": active_count,
            "archived_count": archived_count,
            "linked_annonce_count": linked_annonce_count,
            "primary_candidate_hektor_contact_id": candidate.hektor_contact_id,
            "normalized_key_hash": short_hash(normalized_key),
            "suspected_mass_archive_error": suspected_mass_archive_error,
            "review_hint": review_hint(rule_code, severity, pattern, len(sorted_group), archived_count),
        }
        group_rows.append(row)
        for rank, contact in enumerate(
            sorted(
                sorted_group,
                key=lambda item: (
                    0 if item.hektor_contact_id == candidate.hektor_contact_id else 1,
                    item.archive,
                    -linked_counts.get(item.hektor_contact_id, 0),
                    -item.completeness_score,
                ),
            ),
            start=1,
        ):
            member_rows.append(
                {
                    "duplicate_group_id": duplicate_group_id,
                    "hektor_contact_id": contact.hektor_contact_id,
                    "is_primary_candidate": int(contact.hektor_contact_id == candidate.hektor_contact_id),
                    "archive": contact.archive,
                    "display_name": contact.display_name,
                    "email_hash": short_hash(contact.email_normalized),
                    "phone_hash": short_hash(contact.phone_normalized),
                    "date_maj": contact.date_maj,
                    "linked_annonce_count": linked_counts.get(contact.hektor_contact_id, 0),
                    "completeness_score": contact.completeness_score,
                    "member_rank": rank,
                }
            )
            current = best_duplicate_by_contact.get(contact.hektor_contact_id)
            if current is None or SEVERITY_RANK[severity] > SEVERITY_RANK.get(str(current.get("severity")), 0):
                best_duplicate_by_contact[contact.hektor_contact_id] = row
    return group_rows, member_rows, best_duplicate_by_contact


def build_contact_rows(
    contacts: list[ContactRow],
    relation_rows: dict[str, list[dict[str, Any]]],
    roles_by_contact: dict[str, set[str]],
    total_search_counts: Counter[str],
    active_search_counts: Counter[str],
    duplicate_member_counts: Counter[str],
    best_duplicate_by_contact: dict[str, dict[str, Any]],
    negotiator_map: dict[str, dict[str, str | None]],
    agency_map: dict[str, str | None],
    contact_detail_state: dict[str, str | None],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for contact in contacts:
        roles = sorted(roles_by_contact.get(contact.hektor_contact_id, set()))
        duplicate = best_duplicate_by_contact.get(contact.hektor_contact_id)
        directory = negotiator_map.get(contact.hektor_negociateur_id or "", {})
        relations = relation_rows.get(contact.hektor_contact_id, [])
        active_relation_count = sum(1 for row in relations if int(row.get("is_active_annonce") or 0))
        active_search_count = active_search_counts.get(contact.hektor_contact_id, 0)
        eligibility_reasons = []
        if active_relation_count:
            eligibility_reasons.append("active_annonce_relation")
        if active_search_count:
            eligibility_reasons.append("active_search")
        payload = {
            "hektor_contact_id": contact.hektor_contact_id,
            "hektor_agence_id": contact.hektor_agence_id,
            "hektor_negociateur_id": contact.hektor_negociateur_id,
            "negociateur_email": directory.get("negociateur_email"),
            "commercial_nom": directory.get("commercial_nom"),
            "agence_nom": directory.get("agence_nom") or agency_map.get(contact.hektor_agence_id or ""),
            "civilite": contact.civilite,
            "nom": contact.nom,
            "prenom": contact.prenom,
            "display_name": contact.display_name,
            "archive": contact.archive,
            "date_enregistrement": contact.date_enregistrement,
            "date_maj": contact.date_maj,
            "email": contact.email,
            "phone_primary": contact.phone_primary,
            "phone_secondary": contact.fixe if contact.portable and contact.fixe else None,
            "ville": contact.ville,
            "code_postal": contact.code_postal,
            "adresse": contact.adresse,
            "typologies_json": contact.typologie_json or "[]",
            "relation_roles_json": json_array(roles),
            "linked_annonce_count": len({row["hektor_annonce_id"] for row in relations}),
            "active_search_count": active_search_count,
            "total_search_count": total_search_counts.get(contact.hektor_contact_id, 0),
            "has_contact_detail": int(contact.hektor_contact_id in contact_detail_state),
            "contact_detail_synced_at": contact_detail_state.get(contact.hektor_contact_id),
            "supabase_sync_eligible": int(bool(eligibility_reasons)),
            "eligibility_reasons_json": json_array(eligibility_reasons),
            "duplicate_group_count": duplicate_member_counts.get(contact.hektor_contact_id, 0),
            "duplicate_max_severity": duplicate.get("severity") if duplicate else None,
            "duplicate_primary_candidate_id": duplicate.get("primary_candidate_hektor_contact_id") if duplicate else None,
            "completeness_score": contact.completeness_score,
        }
        payload["source_hash"] = stable_hash({key: value for key, value in payload.items() if key != "source_hash"})
        rows.append(payload)
    return rows


def replace_table_rows(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]], refreshed_at: str) -> None:
    conn.execute(f"DELETE FROM {table}")
    if not rows:
        conn.commit()
        return
    keys = list(rows[0].keys())
    if "refreshed_at" not in keys:
        keys.append("refreshed_at")
    placeholders = ",".join("?" for _ in keys)
    columns = ",".join(keys)
    values = []
    for row in rows:
        values.append(tuple(row.get(key, refreshed_at if key == "refreshed_at" else None) for key in keys))
    conn.executemany(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
    conn.commit()


def insert_table_rows(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]], refreshed_at: str) -> None:
    if not rows:
        return
    keys = list(rows[0].keys())
    if "refreshed_at" not in keys:
        keys.append("refreshed_at")
    placeholders = ",".join("?" for _ in keys)
    columns = ",".join(keys)
    values = [
        tuple(refreshed_at if key == "refreshed_at" else row.get(key) for key in keys)
        for row in rows
    ]
    conn.executemany(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)


def load_existing_duplicate_fields(
    conn: sqlite3.Connection,
    contact_ids: Iterable[str],
) -> dict[str, dict[str, Any]]:
    ids = normalize_contact_ids(contact_ids)
    if not ids:
        return {}
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"""
        SELECT hektor_contact_id, duplicate_group_count, duplicate_max_severity, duplicate_primary_candidate_id
        FROM app_contact_current
        WHERE CAST(hektor_contact_id AS TEXT) IN ({placeholders})
        """,
        ids,
    ).fetchall()
    return {
        clean_text(row["hektor_contact_id"]): {
            "duplicate_group_count": row["duplicate_group_count"],
            "duplicate_max_severity": row["duplicate_max_severity"],
            "duplicate_primary_candidate_id": row["duplicate_primary_candidate_id"],
        }
        for row in rows
    }


def load_existing_relation_rows(
    conn: sqlite3.Connection,
    contact_ids: Iterable[str],
) -> list[dict[str, Any]]:
    ids = normalize_contact_ids(contact_ids)
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"""
        SELECT *
        FROM app_contact_relation_current
        WHERE CAST(hektor_contact_id AS TEXT) IN ({placeholders})
        """,
        ids,
    ).fetchall()
    return [dict(row) for row in rows]


def merge_relation_rows(
    current_rows: list[dict[str, Any]],
    previous_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_key = {clean_text(row.get("relation_key")): row for row in previous_rows if clean_text(row.get("relation_key"))}
    for row in current_rows:
        key = clean_text(row.get("relation_key"))
        if key:
            by_key[key] = row
    return list(by_key.values())


def preserve_duplicate_fields(
    contact_rows: list[dict[str, Any]],
    previous_duplicate_fields: dict[str, dict[str, Any]],
) -> None:
    for row in contact_rows:
        previous = previous_duplicate_fields.get(clean_text(row.get("hektor_contact_id")))
        if not previous:
            continue
        row.update(previous)
        row["source_hash"] = stable_hash({key: value for key, value in row.items() if key != "source_hash"})


def write_reports(report_dir: Path, summary: dict[str, Any], group_rows: list[dict[str, Any]], member_rows: list[dict[str, Any]]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "contact_audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    top_groups = sorted(
        group_rows,
        key=lambda row: (
            -SEVERITY_RANK[str(row["severity"])],
            -int(row["suspected_mass_archive_error"]),
            -int(row["member_count"]),
            str(row["rule_code"]),
        ),
    )[:5000]
    with (report_dir / "contact_duplicate_groups_top.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(top_groups[0].keys()) if top_groups else ["duplicate_group_id"])
        writer.writeheader()
        writer.writerows(top_groups)

    group_ids = {row["duplicate_group_id"] for row in top_groups[:1000]}
    top_members = [row for row in member_rows if row["duplicate_group_id"] in group_ids]
    with (report_dir / "contact_duplicate_members_top.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(top_members[0].keys()) if top_members else ["duplicate_group_id", "hektor_contact_id"])
        writer.writeheader()
        writer.writerows(top_members)


def refresh_contact_slice(
    *,
    contact_ids: Iterable[str],
    hektor_db: Path = DEFAULT_HEKTOR_DB,
    phase2_db: Path = DEFAULT_PHASE2_DB,
) -> dict[str, Any]:
    ids = normalize_contact_ids(contact_ids)
    if not ids:
        raise ValueError("Au moins un ID contact est requis")

    started_at = now_utc_iso()
    hektor_conn = connect(hektor_db)
    phase2_conn = connect(phase2_db)
    try:
        init_contacts_schema(phase2_conn)
        contacts = load_contacts(hektor_conn, contact_ids=ids)
        valid_contact_ids = {contact.hektor_contact_id for contact in contacts}
        relation_rows, roles_by_contact = load_relations(hektor_conn, phase2_conn, contact_ids=ids)
        search_rows, total_search_counts, active_search_counts = load_contact_searches(hektor_conn, contact_ids=ids)
        contact_detail_state = load_contact_detail_state(hektor_conn, contact_ids=ids)

        raw_relation_total = sum(len(rows) for rows in relation_rows.values())
        relation_rows = {
            contact_id: rows
            for contact_id, rows in relation_rows.items()
            if contact_id in valid_contact_ids
        }
        raw_search_total = len(search_rows)
        search_rows = [row for row in search_rows if row["hektor_contact_id"] in valid_contact_ids]
        roles_by_contact = {
            contact_id: roles
            for contact_id, roles in roles_by_contact.items()
            if contact_id in valid_contact_ids
        }

        negotiator_map, agency_map = load_directory_maps(hektor_conn)
        previous_duplicate_fields = load_existing_duplicate_fields(phase2_conn, ids)
        previous_relation_rows = load_existing_relation_rows(phase2_conn, ids)
        contact_rows = build_contact_rows(
            contacts,
            relation_rows,
            roles_by_contact,
            total_search_counts,
            active_search_counts,
            Counter(),
            {},
            negotiator_map,
            agency_map,
            contact_detail_state,
        )
        preserve_duplicate_fields(contact_rows, previous_duplicate_fields)
        current_relation_rows = [row for rows in relation_rows.values() for row in rows]
        relation_flat_rows = merge_relation_rows(
            current_relation_rows,
            previous_relation_rows,
        )
        refreshed_at = now_utc_iso()

        for contact_id in ids:
            phase2_conn.execute("DELETE FROM app_contact_current WHERE hektor_contact_id = ?", (contact_id,))
            phase2_conn.execute("DELETE FROM app_contact_relation_current WHERE hektor_contact_id = ?", (contact_id,))
            phase2_conn.execute("DELETE FROM app_contact_search_current WHERE hektor_contact_id = ?", (contact_id,))

        insert_table_rows(phase2_conn, "app_contact_current", contact_rows, refreshed_at)
        insert_table_rows(phase2_conn, "app_contact_relation_current", relation_flat_rows, refreshed_at)
        insert_table_rows(phase2_conn, "app_contact_search_current", search_rows, refreshed_at)
        phase2_conn.commit()

        missing_contact_ids = [contact_id for contact_id in ids if contact_id not in valid_contact_ids]
        return {
            "started_at": started_at,
            "finished_at": refreshed_at,
            "mode": "contact_slice",
            "requested_contact_ids": ids,
            "contacts_total": len(contact_rows),
            "missing_contact_ids": missing_contact_ids,
            "relations_total": len(relation_flat_rows),
            "previous_relations_preserved": max(0, len(relation_flat_rows) - len(current_relation_rows)),
            "relations_skipped_missing_contact": raw_relation_total - len(current_relation_rows),
            "searches_total": len(search_rows),
            "active_searches_total": sum(int(row["is_active"]) for row in search_rows),
            "searches_skipped_missing_contact": raw_search_total - len(search_rows),
            "supabase_sync_eligible_contacts": sum(int(row["supabase_sync_eligible"]) for row in contact_rows),
            "duplicate_fields_preserved": sum(1 for row in contact_rows if row["hektor_contact_id"] in previous_duplicate_fields),
        }
    finally:
        hektor_conn.close()
        phase2_conn.close()


def build_contacts_layer(
    *,
    hektor_db: Path = DEFAULT_HEKTOR_DB,
    phase2_db: Path = DEFAULT_PHASE2_DB,
    report_dir: Path = DEFAULT_REPORT_DIR,
    limit: int | None = None,
    write_reports_enabled: bool = True,
) -> dict[str, Any]:
    started_at = now_utc_iso()
    hektor_conn = connect(hektor_db)
    phase2_conn = connect(phase2_db)
    try:
        init_contacts_schema(phase2_conn)
        contacts = load_contacts(hektor_conn, limit)
        relation_rows, roles_by_contact = load_relations(hektor_conn, phase2_conn)
        search_rows, total_search_counts, active_search_counts = load_contact_searches(hektor_conn)
        contact_detail_state = load_contact_detail_state(hektor_conn)
        valid_contact_ids = {contact.hektor_contact_id for contact in contacts}
        raw_relation_total = sum(len(rows) for rows in relation_rows.values())
        relation_rows = {
            contact_id: rows
            for contact_id, rows in relation_rows.items()
            if contact_id in valid_contact_ids
        }
        raw_search_total = len(search_rows)
        search_rows = [row for row in search_rows if row["hektor_contact_id"] in valid_contact_ids]
        roles_by_contact = {
            contact_id: roles
            for contact_id, roles in roles_by_contact.items()
            if contact_id in valid_contact_ids
        }
        skipped_missing_contact_relations = raw_relation_total - sum(len(rows) for rows in relation_rows.values())
        skipped_missing_contact_searches = raw_search_total - len(search_rows)
        negotiator_map, agency_map = load_directory_maps(hektor_conn)
        linked_counts = {contact_id: len({row["hektor_annonce_id"] for row in rows}) for contact_id, rows in relation_rows.items()}
        group_rows, member_rows, best_duplicate_by_contact = build_duplicate_records(contacts, linked_counts)
        duplicate_member_counts = Counter(row["hektor_contact_id"] for row in member_rows)
        contact_rows = build_contact_rows(
            contacts,
            relation_rows,
            roles_by_contact,
            total_search_counts,
            active_search_counts,
            duplicate_member_counts,
            best_duplicate_by_contact,
            negotiator_map,
            agency_map,
            contact_detail_state,
        )
        relation_flat_rows = [row for rows in relation_rows.values() for row in rows]
        refreshed_at = now_utc_iso()

        replace_table_rows(phase2_conn, "app_contact_current", contact_rows, refreshed_at)
        replace_table_rows(phase2_conn, "app_contact_relation_current", relation_flat_rows, refreshed_at)
        replace_table_rows(phase2_conn, "app_contact_search_current", search_rows, refreshed_at)
        replace_table_rows(phase2_conn, "app_contact_duplicate_group_current", group_rows, refreshed_at)
        replace_table_rows(phase2_conn, "app_contact_duplicate_member_current", member_rows, refreshed_at)

        severity_counts = Counter(row["severity"] for row in group_rows)
        rule_counts = Counter(row["rule_code"] for row in group_rows)
        archive_pattern_counts = Counter(row["archive_pattern"] for row in group_rows)
        summary = {
            "started_at": started_at,
            "finished_at": refreshed_at,
            "contacts_total": len(contacts),
            "contacts_active": sum(1 for contact in contacts if not contact.archive),
            "contacts_archived": sum(1 for contact in contacts if contact.archive),
            "relations_total": len(relation_flat_rows),
            "transaction_relations_total": sum(1 for row in relation_flat_rows if row.get("transaction_id")),
            "contacts_with_relation": len(relation_rows),
            "relations_skipped_missing_contact": skipped_missing_contact_relations,
            "searches_total": len(search_rows),
            "active_searches_total": sum(int(row["is_active"]) for row in search_rows),
            "contacts_with_active_search": sum(1 for count in active_search_counts.values() if count),
            "contacts_with_detail": sum(1 for contact in contacts if contact.hektor_contact_id in contact_detail_state),
            "searches_skipped_missing_contact": skipped_missing_contact_searches,
            "supabase_sync_eligible_contacts": sum(int(row["supabase_sync_eligible"]) for row in contact_rows),
            "duplicate_group_total": len(group_rows),
            "duplicate_member_total": len(set(row["hektor_contact_id"] for row in member_rows)),
            "high_or_critical_group_total": sum(1 for row in group_rows if row["severity"] in {"high", "critical"}),
            "suspected_mass_archive_error_total": sum(int(row["suspected_mass_archive_error"]) for row in group_rows),
            "duplicate_rule_counts": dict(sorted(rule_counts.items())),
            "duplicate_severity_counts": dict(sorted(severity_counts.items())),
            "duplicate_archive_pattern_counts": dict(sorted(archive_pattern_counts.items())),
            "report_dir": str(report_dir),
        }
        phase2_conn.execute(
            """
            INSERT INTO app_contact_audit_run (
                started_at, finished_at, contacts_total, contacts_active, contacts_archived,
                duplicate_group_total, duplicate_member_total, high_or_critical_group_total,
                suspected_mass_archive_error_total, report_summary_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                started_at,
                refreshed_at,
                summary["contacts_total"],
                summary["contacts_active"],
                summary["contacts_archived"],
                summary["duplicate_group_total"],
                summary["duplicate_member_total"],
                summary["high_or_critical_group_total"],
                summary["suspected_mass_archive_error_total"],
                json.dumps(summary, ensure_ascii=False, separators=(",", ":")),
            ),
        )
        phase2_conn.commit()
    finally:
        hektor_conn.close()
        phase2_conn.close()

    if write_reports_enabled:
        write_reports(report_dir, summary, group_rows, member_rows)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Construit la couche Contacts Phase2 et audite les doublons sans suppression.")
    parser.add_argument("--hektor-db", type=Path, default=DEFAULT_HEKTOR_DB)
    parser.add_argument("--phase2-db", type=Path, default=DEFAULT_PHASE2_DB)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--limit", type=int, default=0, help="Limite de contacts pour test local. 0 = tous.")
    parser.add_argument(
        "--contact-id",
        action="append",
        default=[],
        help="Reconstruit uniquement un ou plusieurs contacts Hektor (valeurs separees par virgule acceptees).",
    )
    parser.add_argument("--no-reports", action="store_true", help="Ne genere pas les CSV/JSON d'audit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contact_ids = normalize_contact_ids(args.contact_id)
    if contact_ids:
        summary = refresh_contact_slice(
            contact_ids=contact_ids,
            hektor_db=args.hektor_db,
            phase2_db=args.phase2_db,
        )
    else:
        summary = build_contacts_layer(
            hektor_db=args.hektor_db,
            phase2_db=args.phase2_db,
            report_dir=args.report_dir,
            limit=args.limit or None,
            write_reports_enabled=not args.no_reports,
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
