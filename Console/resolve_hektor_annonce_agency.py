from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "hektor.sqlite"


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve the agency user context required for a Hektor annonce.")
    parser.add_argument("--annonce-id", required=True)
    parser.add_argument("--agency-id")
    parser.add_argument("--target-user-id")
    parser.add_argument("--target-email")
    args = parser.parse_args()

    annonce_id = str(args.annonce_id).strip()
    if not annonce_id:
        raise SystemExit("annonce-id is required")

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            """
            SELECT
                a.hektor_annonce_id,
                a.hektor_agence_id,
                ag.nom,
                ag.mail,
                ag.raw_json
            FROM hektor_annonce a
            LEFT JOIN hektor_agence ag ON ag.hektor_agence_id = a.hektor_agence_id
            WHERE a.hektor_annonce_id = ?
            LIMIT 1
            """,
            (annonce_id,),
        ).fetchone()
        if not row:
            print(json.dumps({"found": False}, ensure_ascii=True))
            return 0

        raw = {}
        try:
            raw = json.loads(row["raw_json"] or "{}")
        except Exception:
            raw = {}

        id_user = str(raw.get("idUser") or "").strip()
        selected_agency_id = str(args.agency_id or "").strip() or str(row["hektor_agence_id"] or "").strip()
        agency_row = con.execute(
            """
            SELECT hektor_agence_id, nom, mail, raw_json
            FROM hektor_agence
            WHERE hektor_agence_id = ?
            LIMIT 1
            """,
            (selected_agency_id,),
        ).fetchone()
        agency_raw = {}
        try:
            agency_raw = json.loads((agency_row["raw_json"] if agency_row else row["raw_json"]) or "{}")
        except Exception:
            agency_raw = raw
        agency_id_user = str(agency_raw.get("idUser") or "").strip()

        payload = {
            "found": True,
            "hektor_annonce_id": str(row["hektor_annonce_id"] or ""),
            "current_hektor_agence_id": str(row["hektor_agence_id"] or ""),
            "hektor_agence_id": selected_agency_id,
            "agency_changed": selected_agency_id != str(row["hektor_agence_id"] or "").strip(),
            "agency_id_user": agency_id_user or id_user or None,
            "agency_label": (agency_row["nom"] if agency_row else row["nom"]),
            "agency_email": (agency_row["mail"] if agency_row else row["mail"]),
        }

        target_email = str(args.target_email or "").strip().lower()
        target_user_id = str(args.target_user_id or "").strip()
        target = None
        if target_user_id:
            target = con.execute(
                """
                SELECT hektor_negociateur_id, hektor_user_id, hektor_agence_id, nom, prenom, email
                FROM hektor_negociateur
                WHERE COALESCE(hektor_user_id, '') = ?
                  AND COALESCE(hektor_agence_id, '') = ?
                ORDER BY CAST(COALESCE(hektor_negociateur_id, '0') AS INTEGER)
                LIMIT 1
                """,
                (target_user_id, payload["hektor_agence_id"]),
            ).fetchone()
        if target is None and target_email and not target_user_id:
            target = con.execute(
                """
                SELECT hektor_negociateur_id, hektor_user_id, hektor_agence_id, nom, prenom, email
                FROM hektor_negociateur
                WHERE lower(COALESCE(email, '')) = ?
                  AND COALESCE(hektor_agence_id, '') = ?
                ORDER BY CAST(COALESCE(hektor_negociateur_id, '0') AS INTEGER)
                LIMIT 1
                """,
                (target_email, payload["hektor_agence_id"]),
            ).fetchone()
        if target is not None:
            label = " ".join(part for part in [target["prenom"], target["nom"]] if part).strip()
            payload.update(
                {
                    "target_found": True,
                    "target_hektor_negociateur_id": str(target["hektor_negociateur_id"] or ""),
                    "target_hektor_user_id": str(target["hektor_user_id"] or ""),
                    "target_hektor_agence_id": str(target["hektor_agence_id"] or ""),
                    "target_label": label or None,
                    "target_email": target["email"],
                }
            )
        elif target_email or target_user_id:
            payload["target_found"] = False

        print(json.dumps(payload, ensure_ascii=True))
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
