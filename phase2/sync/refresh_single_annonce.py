from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hektor_pipeline.common import (  # noqa: E402
    HektorClient,
    Settings,
    connect_db,
    create_sync_run,
    finish_sync_run,
    init_db,
    now_utc_iso,
    upsert_raw_response,
)
from sync_raw import mark_annonce_detail_synced, replace_annonce_contact_links  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rafraichit une seule annonce Hektor dans la base locale.")
    parser.add_argument("--id-annonce", required=True, help="ID Hektor de l'annonce")
    return parser.parse_args()


def iter_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from iter_dicts(nested)
    elif isinstance(value, list):
        for item in value:
            yield from iter_dicts(item)


def is_enabled_payload(item: dict[str, Any]) -> bool:
    raw_enabled = item.get("active")
    raw_selected = item.get("selected")
    raw_state = item.get("state") or item.get("statut") or item.get("status")
    if raw_enabled in (1, "1", True, "true") or raw_selected in (1, "1", True, "true"):
        return True
    if raw_state is not None and str(raw_state).lower() in {"1", "active", "enabled", "selected", "checked", "exported"}:
        return True
    return False


def normalized_id(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def update_annonce_from_detail(conn: sqlite3.Connection, annonce_id: str, payload: dict[str, Any]) -> None:
    data = payload.get("data") or {}
    key_data = data.get("keyData") if isinstance(data, dict) else {}
    localite = data.get("localite") if isinstance(data, dict) else {}
    publique = localite.get("publique") if isinstance(localite, dict) else {}

    existing = conn.execute(
        "SELECT titre, valide, partage FROM hektor_annonce WHERE hektor_annonce_id = ?",
        (annonce_id,),
    ).fetchone()
    existing_titre = existing["titre"] if existing else None
    existing_valide = existing["valide"] if existing else None
    existing_partage = existing["partage"] if existing else None

    conn.execute(
        """
        INSERT INTO hektor_annonce(
            hektor_annonce_id, no_dossier, no_mandat, hektor_agence_id, hektor_negociateur_id, date_maj, offre_type, idtype,
            prix, surface, archive, diffusable, valide, partage, titre, ville, code_postal, raw_json, synced_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(hektor_annonce_id) DO UPDATE SET
            no_dossier = excluded.no_dossier,
            no_mandat = excluded.no_mandat,
            hektor_agence_id = excluded.hektor_agence_id,
            hektor_negociateur_id = excluded.hektor_negociateur_id,
            date_maj = excluded.date_maj,
            offre_type = excluded.offre_type,
            idtype = excluded.idtype,
            prix = excluded.prix,
            surface = excluded.surface,
            archive = excluded.archive,
            diffusable = excluded.diffusable,
            valide = excluded.valide,
            partage = excluded.partage,
            titre = excluded.titre,
            ville = excluded.ville,
            code_postal = excluded.code_postal,
            raw_json = excluded.raw_json,
            synced_at = excluded.synced_at
        """,
        (
            annonce_id,
            key_data.get("NO_DOSSIER"),
            key_data.get("NO_MANDAT"),
            normalized_id(key_data.get("agence")),
            normalized_id(key_data.get("NEGOCIATEUR")),
            key_data.get("datemaj"),
            key_data.get("offredem"),
            key_data.get("idtype"),
            key_data.get("prix"),
            key_data.get("surface"),
            key_data.get("archive"),
            key_data.get("diffusable"),
            key_data.get("valide") if key_data.get("valide") is not None else existing_valide,
            key_data.get("partage") if key_data.get("partage") is not None else existing_partage,
            data.get("titre") or key_data.get("titre") or existing_titre,
            publique.get("ville") if isinstance(publique, dict) else None,
            publique.get("code") if isinstance(publique, dict) else None,
            json.dumps(key_data if isinstance(key_data, dict) else data, ensure_ascii=False),
            now_utc_iso(),
        ),
    )


def upsert_annonce_detail(conn: sqlite3.Connection, annonce_id: str, payload: dict[str, Any]) -> None:
    data = payload.get("data") or {}
    statut = data.get("statut") if isinstance(data, dict) else {}
    conn.execute(
        """
        INSERT INTO hektor_annonce_detail(
            hektor_annonce_id, statut_id, statut_name, localite_json, mandats_json, proprietaires_json, honoraires_json,
            notes_json, zones_json, particularites_json, pieces_json, images_json, textes_json, terrain_json,
            copropriete_json, raw_json, synced_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(hektor_annonce_id) DO UPDATE SET
            statut_id = excluded.statut_id,
            statut_name = excluded.statut_name,
            localite_json = excluded.localite_json,
            mandats_json = excluded.mandats_json,
            proprietaires_json = excluded.proprietaires_json,
            honoraires_json = excluded.honoraires_json,
            notes_json = excluded.notes_json,
            zones_json = excluded.zones_json,
            particularites_json = excluded.particularites_json,
            pieces_json = excluded.pieces_json,
            images_json = excluded.images_json,
            textes_json = excluded.textes_json,
            terrain_json = excluded.terrain_json,
            copropriete_json = excluded.copropriete_json,
            raw_json = excluded.raw_json,
            synced_at = excluded.synced_at
        """,
        (
            annonce_id,
            statut.get("id") if isinstance(statut, dict) else None,
            statut.get("name") if isinstance(statut, dict) else None,
            json.dumps(data.get("localite"), ensure_ascii=False),
            json.dumps(data.get("mandats"), ensure_ascii=False),
            json.dumps(data.get("proprietaires"), ensure_ascii=False),
            json.dumps(data.get("honoraires"), ensure_ascii=False),
            json.dumps(data.get("notes"), ensure_ascii=False),
            json.dumps(data.get("zones"), ensure_ascii=False),
            json.dumps(data.get("particularites"), ensure_ascii=False),
            json.dumps(data.get("pieces"), ensure_ascii=False),
            json.dumps(data.get("images"), ensure_ascii=False),
            json.dumps(data.get("textes"), ensure_ascii=False),
            json.dumps(data.get("terrain"), ensure_ascii=False),
            json.dumps(data.get("copropriete"), ensure_ascii=False),
            json.dumps(data, ensure_ascii=False),
            now_utc_iso(),
        ),
    )


def refresh_broadcast_state(conn: sqlite3.Connection, annonce_id: str, payload: dict[str, Any]) -> list[str]:
    enabled_portals: list[str] = []
    conn.execute("DELETE FROM hektor_annonce_broadcast_state WHERE hektor_annonce_id = ?", (annonce_id,))
    now_iso = now_utc_iso()

    for item in iter_dicts(payload.get("data")):
        broadcast_id = normalized_id(item.get("idPasserelle") or item.get("id"))
        if not broadcast_id or not is_enabled_payload(item):
            continue
        portal_row = conn.execute(
            "SELECT passerelle_key FROM hektor_broadcast_portal WHERE hektor_broadcast_id = ?",
            (broadcast_id,),
        ).fetchone()
        portal_key = str(portal_row["passerelle_key"] or "").strip() if portal_row else str(item.get("nom") or "").strip()
        enabled_portals.append(portal_key or broadcast_id)
        conn.execute(
            """
            INSERT INTO hektor_annonce_broadcast_state(
                hektor_broadcast_id, hektor_annonce_id, commercial_key, passerelle_key, commercial_id,
                commercial_type, commercial_nom, commercial_prenom, current_state, export_status,
                is_success, is_error, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hektor_broadcast_id, hektor_annonce_id, commercial_key) DO UPDATE SET
                passerelle_key = excluded.passerelle_key,
                current_state = excluded.current_state,
                export_status = excluded.export_status,
                is_success = excluded.is_success,
                is_error = excluded.is_error,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at
            """,
            (
                broadcast_id,
                annonce_id,
                "",
                portal_key,
                None,
                None,
                None,
                None,
                "broadcasted",
                "exported",
                1,
                0,
                json.dumps(item, ensure_ascii=False),
                now_iso,
            ),
        )
    return sorted({value for value in enabled_portals if value})


def main() -> int:
    args = parse_args()
    annonce_id = str(args.id_annonce).strip()
    settings = Settings.from_env()
    conn = connect_db(settings.db_path)
    init_db(conn)
    run_id = create_sync_run(conn, "refresh_single_annonce")
    client = HektorClient(settings)

    try:
        client.authenticate()

        detail_payload = client.get_json(
            "/Api/Annonce/AnnonceById/",
            params={"id": annonce_id, "version": settings.api_version},
        )
        upsert_raw_response(
            conn,
            run_id=run_id,
            endpoint_name="annonce_detail",
            object_type="annonce_detail",
            object_id=annonce_id,
            page=None,
            params={"id": annonce_id, "version": settings.api_version},
            payload=detail_payload,
            http_status=200,
        )
        update_annonce_from_detail(conn, annonce_id, detail_payload)
        upsert_annonce_detail(conn, annonce_id, detail_payload)
        replace_annonce_contact_links(conn, annonce_id, detail_payload)
        mark_annonce_detail_synced(conn, annonce_id)

        mandats_payload = client.get_json(
            "/Api/Mandat/MandatsByIdAnnonce/",
            params={"idAnnonce": annonce_id, "version": settings.api_version},
        )
        upsert_raw_response(
            conn,
            run_id=run_id,
            endpoint_name="mandats_by_annonce",
            object_type="mandat_by_annonce",
            object_id=annonce_id,
            page=None,
            params={"idAnnonce": annonce_id, "version": settings.api_version},
            payload=mandats_payload,
            http_status=200,
        )

        passerelles_payload = client.get_json(
            "/Api/Annonce/ListPasserelles/",
            params={"idAnnonce": annonce_id, "version": settings.api_version},
        )
        enabled_portals = refresh_broadcast_state(conn, annonce_id, passerelles_payload)

        conn.commit()
        finish_sync_run(conn, run_id, "success", notes=f"single annonce refreshed: {annonce_id}")
        print(
            json.dumps(
                {
                    "ok": True,
                    "run_id": run_id,
                    "hektor_annonce_id": annonce_id,
                    "diffusable": ((detail_payload.get("data") or {}).get("keyData") or {}).get("diffusable"),
                    "enabled_portals": enabled_portals,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        conn.rollback()
        finish_sync_run(conn, run_id, "failed", notes=str(exc))
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
