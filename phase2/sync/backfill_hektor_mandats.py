from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"


def normalize_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def main() -> int:
    con = sqlite3.connect(HEKTOR_DB)
    con.row_factory = sqlite3.Row
    try:
        detail_rows = con.execute(
            """
            SELECT hektor_annonce_id, mandats_json
            FROM hektor_annonce_detail
            WHERE mandats_json IS NOT NULL
              AND TRIM(mandats_json) <> ''
              AND TRIM(mandats_json) <> 'null'
            """
        ).fetchall()

        annonces_touched = 0
        mandats_upserted = 0
        for row in detail_rows:
            annonce_id = str(row["hektor_annonce_id"] or "").strip()
            if not annonce_id:
                continue
            try:
                mandats = json.loads(row["mandats_json"])
            except json.JSONDecodeError:
                continue
            if not isinstance(mandats, list):
                continue

            con.execute("DELETE FROM hektor_mandat WHERE hektor_annonce_id = ?", (annonce_id,))
            annonces_touched += 1

            for item in mandats:
                if not isinstance(item, dict):
                    continue
                mandat_id = normalize_text(item.get("id") or item.get("idMandat") or item.get("mandat_id"))
                if not mandat_id:
                    continue
                con.execute(
                    """
                    INSERT INTO hektor_mandat(
                        hektor_mandat_id, hektor_annonce_id, numero, type, date_enregistrement, date_debut, date_fin,
                        date_cloture, montant, mandants_texte, note, raw_json, synced_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(hektor_mandat_id) DO UPDATE SET
                        hektor_annonce_id = excluded.hektor_annonce_id,
                        numero = excluded.numero,
                        type = excluded.type,
                        date_enregistrement = excluded.date_enregistrement,
                        date_debut = excluded.date_debut,
                        date_fin = excluded.date_fin,
                        date_cloture = excluded.date_cloture,
                        montant = excluded.montant,
                        mandants_texte = excluded.mandants_texte,
                        note = excluded.note,
                        raw_json = excluded.raw_json,
                        synced_at = CURRENT_TIMESTAMP
                    """,
                    (
                        mandat_id,
                        annonce_id,
                        normalize_text(item.get("numero") or item.get("NO_MANDAT")),
                        normalize_text(item.get("type")),
                        normalize_text(item.get("dateenr") or item.get("date_enregistrement")),
                        normalize_text(item.get("debut") or item.get("date_debut")),
                        normalize_text(item.get("fin") or item.get("date_fin")),
                        normalize_text(item.get("cloture") or item.get("date_cloture")),
                        normalize_text(item.get("montant")),
                        normalize_text(item.get("mandants")),
                        normalize_text(item.get("note")),
                        json.dumps(item, ensure_ascii=False),
                    ),
                )
                mandats_upserted += 1

        con.commit()
        print(
            json.dumps(
                {
                    "ok": True,
                    "annonces_touched": annonces_touched,
                    "mandats_upserted": mandats_upserted,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
