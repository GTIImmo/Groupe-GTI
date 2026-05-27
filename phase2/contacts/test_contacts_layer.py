from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from phase2.contacts.build_contacts_layer import build_contacts_layer


class ContactsLayerTest(unittest.TestCase):
    def test_duplicate_audit_keeps_sources_and_classifies_archived_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hektor_db = root / "hektor.sqlite"
            phase2_db = root / "phase2.sqlite"
            conn = sqlite3.connect(hektor_db)
            try:
                conn.executescript(
                    """
                    CREATE TABLE hektor_contact (
                        hektor_contact_id TEXT PRIMARY KEY,
                        hektor_agence_id TEXT,
                        hektor_negociateur_id TEXT,
                        civilite TEXT,
                        nom TEXT,
                        prenom TEXT,
                        archive TEXT,
                        date_enregistrement TEXT,
                        date_maj TEXT,
                        email TEXT,
                        portable TEXT,
                        fixe TEXT,
                        ville TEXT,
                        code_postal TEXT,
                        typologie_json TEXT,
                        raw_json TEXT,
                        synced_at TEXT
                    );
                    CREATE TABLE sync_annonce_contact_link (
                        hektor_annonce_id TEXT,
                        hektor_contact_id TEXT,
                        role_contact TEXT,
                        contact_date_maj TEXT,
                        last_seen_at TEXT
                    );
                    CREATE TABLE case_dossier_source (
                        hektor_annonce_id TEXT,
                        archive TEXT
                    );
                    CREATE TABLE hektor_compromis (
                        hektor_compromis_id TEXT,
                        hektor_annonce_id TEXT,
                        hektor_mandat_id TEXT,
                        status TEXT,
                        compromis_state TEXT,
                        date_start TEXT,
                        date_end TEXT,
                        date_signature_acte TEXT,
                        part_admin TEXT,
                        sequestre TEXT,
                        prix_net_vendeur TEXT,
                        prix_publique TEXT,
                        mandants_json TEXT,
                        acquereurs_json TEXT,
                        raw_json TEXT,
                        synced_at TEXT
                    );
                    CREATE TABLE raw_api_response (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        endpoint_name TEXT,
                        object_id TEXT,
                        object_id_key TEXT,
                        payload_json TEXT
                    );
                    """
                )
                conn.executemany(
                    """
                    INSERT INTO hektor_contact VALUES (
                        ?, '10', '20', 'M.', ?, ?, ?, '2024-01-01', ?, ?, ?, NULL,
                        'Lyon', '69000', '["mandant"]', '{}', '2026-05-25'
                    )
                    """,
                    [
                        ("1", "Dupont", "Jean", "0", "2026-05-20", "same@example.test", "0600000001"),
                        ("2", "Dupont", "Jean", "1", "2026-05-19", "same@example.test", "0600000001"),
                        ("3", "Martin", "Anne", "0", "2026-05-18", "other@example.test", "0600000002"),
                    ],
                )
                conn.execute("INSERT INTO sync_annonce_contact_link VALUES ('100', '1', 'mandant', '2026-05-20', '2026-05-25')")
                conn.execute("INSERT INTO case_dossier_source VALUES ('100', '0')")
                conn.execute("INSERT INTO case_dossier_source VALUES ('101', '0')")
                conn.executemany(
                    """
                    INSERT INTO hektor_compromis VALUES (
                        ?, '100', '900', ?, ?, ?, NULL, NULL, NULL, NULL, '190000', '200000',
                        '[]', ?, '{}', '2026-05-25'
                    )
                    """,
                    [
                        ("c1", "2", "cancelled", "2024-01-01", json.dumps([{"id": "1", "datemaj": "2026-05-20"}])),
                        ("c2", "1", "active", "2024-02-01", json.dumps([{"id": "1", "datemaj": "2026-05-20"}])),
                    ],
                )
                conn.execute(
                    """
                    INSERT INTO raw_api_response(endpoint_name, object_id, object_id_key, payload_json)
                    VALUES ('contact_detail', '3', '3', ?)
                    """,
                    (
                        json.dumps(
                            {
                                "data": {
                                    "contact": {"id": "3", "datemaj": "2026-05-18"},
                                    "annonces": [
                                        {
                                            "id": "101",
                                            "NO_DOSSIER": "D101",
                                            "NO_MANDAT": "M101",
                                            "archive": "0",
                                            "datemaj": "2026-05-17",
                                        }
                                    ],
                                    "recherches": [
                                        {
                                            "archive": "0",
                                            "offre": "0",
                                            "types": {"2": "Appartement"},
                                            "villes": ["Lyon"],
                                            "criteres": [
                                                {"cle": "ITEM_PRIX_MAX", "valeur": "250000", "ponderation": "obligatoire"},
                                                {"cle": "ITEM_SURFACE_MIN", "valeur": "45", "ponderation": "facultatif"},
                                            ],
                                        }
                                    ],
                                }
                            }
                        ),
                    ),
                )
                conn.commit()
            finally:
                conn.close()
            conn = sqlite3.connect(phase2_db)
            try:
                conn.executescript(
                    """
                    CREATE TABLE app_dossier (
                        id INTEGER PRIMARY KEY,
                        hektor_annonce_id INTEGER,
                        numero_dossier TEXT,
                        numero_mandat TEXT
                    );
                    CREATE TABLE app_view_generale (
                        app_dossier_id INTEGER,
                        titre_bien TEXT
                    );
                    INSERT INTO app_dossier VALUES (7, 100, 'D100', 'M100');
                    INSERT INTO app_dossier VALUES (8, 101, 'D101', 'M101');
                    INSERT INTO app_view_generale VALUES (7, 'Maison test');
                    INSERT INTO app_view_generale VALUES (8, 'Maison contact detail');
                    """
                )
                conn.commit()
            finally:
                conn.close()

            summary = build_contacts_layer(
                hektor_db=hektor_db,
                phase2_db=phase2_db,
                report_dir=root / "reports",
                write_reports_enabled=True,
            )

            self.assertEqual(summary["contacts_total"], 3)
            self.assertGreaterEqual(summary["duplicate_group_total"], 1)
            self.assertGreaterEqual(summary["suspected_mass_archive_error_total"], 1)

            conn = sqlite3.connect(phase2_db)
            try:
                contacts = conn.execute("SELECT COUNT(*) FROM app_contact_current").fetchone()[0]
                groups = conn.execute("SELECT COUNT(*) FROM app_contact_duplicate_group_current").fetchone()[0]
                members = conn.execute("SELECT COUNT(*) FROM app_contact_duplicate_member_current").fetchone()[0]
                relation = conn.execute("SELECT app_dossier_id FROM app_contact_relation_current WHERE hektor_contact_id = '1'").fetchone()[0]
                contact_one_relations = conn.execute("SELECT COUNT(*) FROM app_contact_relation_current WHERE hektor_contact_id = '1'").fetchone()[0]
                contact_three_relation = conn.execute(
                    """
                    SELECT app_dossier_id, role_contact, relation_source
                    FROM app_contact_relation_current
                    WHERE hektor_contact_id = '3' AND hektor_annonce_id = '101'
                    """
                ).fetchone()
                contact_three_searches = conn.execute("SELECT active_search_count FROM app_contact_current WHERE hektor_contact_id = '3'").fetchone()[0]
                active_searches = conn.execute("SELECT COUNT(*) FROM app_contact_search_current WHERE is_active = 1").fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(contacts, 3)
            self.assertGreaterEqual(groups, 1)
            self.assertGreaterEqual(members, 2)
            self.assertEqual(relation, 7)
            self.assertEqual(contact_one_relations, 3)
            self.assertEqual(contact_three_relation, (8, "mandant", "api_contact_detail_annonces"))
            self.assertEqual(contact_three_searches, 1)
            self.assertEqual(active_searches, 1)
            self.assertEqual(summary["transaction_relations_total"], 2)
            self.assertEqual(summary["active_searches_total"], 1)

            report = json.loads((root / "reports" / "contact_audit_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(report["contacts_total"], 3)


if __name__ == "__main__":
    unittest.main()
