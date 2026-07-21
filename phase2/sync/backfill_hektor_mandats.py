from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
# Meme variable que hektor_pipeline.common : permet d'eprouver l'etape sur une copie
# de la base avant de la laisser tourner dans le run quotidien.
HEKTOR_DB = Path(os.getenv("HEKTOR_DB_PATH", "") or (ROOT / "data" / "hektor.sqlite"))


def normalize_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def storage_mandat_id(annonce_id: str, mandat_id: str) -> str:
    """Identifiant natif Hektor : l'unicite est portee par le couple (annonce, mandat)."""
    return mandat_id


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

            exploitables = [
                item
                for item in mandats
                if isinstance(item, dict)
                and normalize_text(item.get("id") or item.get("idMandat") or item.get("mandat_id"))
            ]
            if not exploitables:
                continue

            # Filet purement ADDITIF : on ne supprime rien. mandats_json provient du
            # detail de l'annonce (AnnonceById.mandats, cf. normalize_source), alors que
            # normalize_source alimente aussi hektor_mandat depuis le listing global.
            # Purger l'annonce avant de reposer ce seul JSON appauvrissait la table
            # (mesure : 6 mandats actifs dates perdus sur un run complet).
            annonces_touched += 1

            for item in exploitables:
                mandat_id = normalize_text(item.get("id") or item.get("idMandat") or item.get("mandat_id"))
                mandat_storage_id = storage_mandat_id(annonce_id, mandat_id)
                con.execute(
                    """
                    INSERT OR REPLACE INTO hektor_mandat(
                        hektor_mandat_id, hektor_annonce_id, numero, type, date_enregistrement, date_debut, date_fin,
                        date_cloture, montant, mandants_texte, note, raw_json, synced_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        mandat_storage_id,
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
