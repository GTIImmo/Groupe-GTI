import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
SCHEMA_SQL = ROOT / "phase2" / "schema_phase2.sql"


def ensure_schema(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
    con.commit()


def reconcile_app_dossier(con: sqlite3.Connection) -> None:
    con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
    try:
        orphan_ids = [
            row[0]
            for row in con.execute(
                """
                SELECT d.id
                FROM app_dossier d
                LEFT JOIN hektor.case_dossier_source src
                    ON src.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
                   AND src.annonce_source_status = 'present'
                WHERE src.hektor_annonce_id IS NULL
                """
            ).fetchall()
        ]
        if not orphan_ids:
            return

        placeholders = ", ".join("?" for _ in orphan_ids)
        for table in (
            "app_broadcast_action",
            "app_blocker",
            "app_followup",
            "app_internal_status",
            "app_note",
            "app_work_item",
        ):
            con.execute(f"DELETE FROM {table} WHERE app_dossier_id IN ({placeholders})", orphan_ids)
        con.execute(f"DELETE FROM app_dossier WHERE id IN ({placeholders})", orphan_ids)
        con.commit()
    finally:
        con.execute("DETACH DATABASE hektor")


def bootstrap_app_dossier(con: sqlite3.Connection) -> None:
    con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
    try:
        con.execute(
            """
            INSERT INTO app_dossier (
                hektor_annonce_id,
                hektor_mandat_id,
                numero_dossier,
                numero_mandat,
                commercial_id,
                commercial_nom
            )
            SELECT
                CAST(src.hektor_annonce_id AS INTEGER),
                CAST(
                    COALESCE(
                        src.mandat_id,
                        (
                            SELECT m.hektor_mandat_id
                            FROM hektor.hektor_mandat m
                            WHERE m.hektor_annonce_id = src.hektor_annonce_id
                              AND COALESCE(m.numero, '') = COALESCE(src.no_mandat, '')
                            LIMIT 1
                        )
                    ) AS INTEGER
                ),
                src.no_dossier,
                src.no_mandat,
                src.hektor_negociateur_id,
                TRIM(COALESCE(src.negociateur_prenom, '') || ' ' || COALESCE(src.negociateur_nom, ''))
            FROM hektor.case_dossier_source src
            WHERE src.annonce_source_status = 'present'
              AND src.hektor_annonce_id IS NOT NULL
            ON CONFLICT(hektor_annonce_id) DO UPDATE SET
                hektor_mandat_id = excluded.hektor_mandat_id,
                numero_dossier = excluded.numero_dossier,
                numero_mandat = excluded.numero_mandat,
                commercial_id = excluded.commercial_id,
                commercial_nom = excluded.commercial_nom,
                updated_at = CURRENT_TIMESTAMP
            """
        )
        con.commit()
    finally:
        con.execute("DETACH DATABASE hektor")


def seed_work_items(con: sqlite3.Connection) -> None:
    con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
    try:
        con.execute("DELETE FROM app_work_item WHERE workflow_type = 'mandat_diffusion'")

        # 1. Dossiers actifs, non diffusable: signal automatique a controler.
        con.execute(
            """
            INSERT INTO app_work_item (
                app_dossier_id,
                workflow_type,
                event_type,
                status,
                assigned_role,
                priority,
                reason
            )
            SELECT
                d.id,
                'mandat_diffusion',
                'mandat_actif_non_diffusable',
                'new',
                'pauline',
                'normal',
                'Signal automatique : mandat actif non diffusable'
            FROM app_dossier d
            INNER JOIN hektor.case_dossier_source src
                ON src.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
            WHERE COALESCE(src.archive, '0') = '0'
              AND COALESCE(src.diffusable, '0') <> '1'
              AND COALESCE(src.annonce_source_status, 'present') = 'present'
            """
        )

        # 2. Dossiers actifs, diffusable, mais sans diffusion reelle sur les portails.
        con.execute(
            """
            INSERT INTO app_work_item (
                app_dossier_id,
                workflow_type,
                event_type,
                status,
                assigned_role,
                priority,
                reason
            )
            SELECT
                d.id,
                'mandat_diffusion',
                'diffusable_non_visible',
                'pending',
                'pauline',
                'high',
                'Signal automatique : bien diffusable mais non visible sur les passerelles'
            FROM app_dossier d
            INNER JOIN hektor.case_dossier_source src
                ON src.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
            LEFT JOIN (
                SELECT
                    hektor_annonce_id,
                    SUM(CASE WHEN current_state = 'broadcasted' THEN 1 ELSE 0 END) AS nb_portails_actifs
                FROM hektor.hektor_annonce_broadcast_state
                GROUP BY hektor_annonce_id
            ) ba
                ON ba.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
            WHERE COALESCE(src.archive, '0') = '0'
              AND COALESCE(src.diffusable, '0') = '1'
              AND COALESCE(ba.nb_portails_actifs, 0) = 0
              AND COALESCE(src.annonce_source_status, 'present') = 'present'
            """
        )

        # 3. Dossiers archives avec cloture mandat: clotures / annulations a verifier.
        con.execute(
            """
            INSERT INTO app_work_item (
                app_dossier_id,
                workflow_type,
                event_type,
                status,
                assigned_role,
                priority,
                reason
            )
            SELECT
                d.id,
                'mandat_diffusion',
                'mandat_archive_cloture',
                'pending',
                'pauline',
                'normal',
                'Signal automatique : mandat archive avec date de cloture'
            FROM app_dossier d
            INNER JOIN hektor.case_dossier_source src
                ON src.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
            WHERE COALESCE(src.archive, '0') = '1'
              AND src.mandat_date_cloture IS NOT NULL
              AND COALESCE(src.annonce_source_status, 'present') = 'present'
            """
        )

        # Internal statuses defaults.
        con.execute(
            """
            INSERT INTO app_internal_status (
                app_dossier_id,
                internal_status,
                priority,
                next_action,
                updated_by
            )
            SELECT
                wi.app_dossier_id,
                CASE
                    WHEN wi.event_type = 'diffusable_non_visible' THEN 'pret_diffusion'
                    ELSE 'a_controler'
                END,
                wi.priority,
                CASE
                    WHEN wi.event_type = 'mandat_actif_non_diffusable' THEN 'Verifier s''il manque une vraie demande de diffusion ou des elements de validation'
                    WHEN wi.event_type = 'diffusable_non_visible' THEN 'Verifier pourquoi le bien n''est pas visible'
                    WHEN wi.event_type = 'mandat_archive_cloture' THEN 'Verifier la cloture et l''annulation du mandat'
                    ELSE NULL
                END,
                'bootstrap_phase2'
            FROM app_work_item wi
            WHERE wi.workflow_type = 'mandat_diffusion'
            ON CONFLICT(app_dossier_id) DO UPDATE SET
                internal_status = excluded.internal_status,
                priority = excluded.priority,
                next_action = excluded.next_action,
                updated_by = excluded.updated_by,
                updated_at = CURRENT_TIMESTAMP
            """
        )
        con.commit()
    finally:
        con.execute("DETACH DATABASE hektor")


def main() -> None:
    con = sqlite3.connect(PHASE2_DB)
    try:
        ensure_schema(con)
        reconcile_app_dossier(con)
        bootstrap_app_dossier(con)
        seed_work_items(con)

        cur = con.cursor()
        print("app_dossier", cur.execute("SELECT COUNT(*) FROM app_dossier").fetchone()[0])
        print(
            "app_work_item",
            cur.execute(
                "SELECT COUNT(*) FROM app_work_item WHERE workflow_type = 'mandat_diffusion'"
            ).fetchone()[0],
        )
    finally:
        con.close()


if __name__ == "__main__":
    main()
