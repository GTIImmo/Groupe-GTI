from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"


SQL_MANDATS = """
SELECT
    app_dossier_id,
    hektor_annonce_id,
    archive,
    diffusable,
    nb_portails_actifs,
    has_diffusion_error,
    portails_resume,
    numero_dossier,
    numero_mandat,
    titre_bien,
    ville,
    type_bien,
    prix,
    commercial_id,
    commercial_nom,
    agence_nom,
    statut_annonce,
    priority,
    offre_id,
    compromis_id,
    vente_id,
    date_maj AS source_updated_at
FROM app_view_generale
ORDER BY app_dossier_id;
"""


SQL_BROADCASTS = """
SELECT
    d.app_dossier_id,
    d.hektor_annonce_id,
    s.passerelle_key,
    COALESCE(s.commercial_key, '') AS commercial_key,
    s.commercial_id,
    TRIM(COALESCE(s.commercial_nom, '') || CASE WHEN COALESCE(s.commercial_prenom, '') <> '' THEN ' ' || s.commercial_prenom ELSE '' END) AS commercial_nom,
    s.commercial_prenom,
    s.current_state,
    s.export_status,
    CAST(COALESCE(s.is_success, 0) AS INTEGER) AS is_success,
    CAST(COALESCE(s.is_error, 0) AS INTEGER) AS is_error
FROM app_view_generale d
JOIN hektor.hektor_annonce_broadcast_state s
  ON s.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
ORDER BY d.app_dossier_id, s.passerelle_key, commercial_key;
"""


def row_dicts(cursor: sqlite3.Cursor) -> list[dict[str, object]]:
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def build_payload() -> dict[str, object]:
    con = sqlite3.connect(PHASE2_DB)
    try:
        con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
        mandats = row_dicts(con.execute(SQL_MANDATS))
        broadcasts = row_dicts(con.execute(SQL_BROADCASTS))
    finally:
        try:
            con.execute("DETACH DATABASE hektor")
        except sqlite3.Error:
            pass
        con.close()

    return {
        "meta": {
            "source": "phase2.sqlite + hektor.sqlite",
            "contract": "app_mandat_payload_v1",
            "generated_from": "phase2/sync/export_mandat_payload.py",
        },
        "mandats": mandats,
        "broadcasts": broadcasts,
    }


def main() -> None:
    print(json.dumps(build_payload(), ensure_ascii=True))


if __name__ == "__main__":
    main()
