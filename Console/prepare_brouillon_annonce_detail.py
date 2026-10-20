"""PREPARER LE DETAIL COMPLET D'UN BROUILLON, POUR 24 H -- chantier 7, piece ②.
                                                                  20/10/2026

CE QUE FAIT CE SCRIPT. Il reconstruit la fiche complete d'une annonce BROUILLON
depuis le miroir local (`data/hektor.sqlite` + `phase2/phase2.sqlite`), et la depose
dans `app_brouillon_annonce_detail_cache` avec une date de peremption. Le front la
lit ensuite comme il lit deja celle des Vendu/Clos, et la fiche s'ouvre.

⭐ ZERO APPEL A HEKTOR. Tout vient du miroir. Mesure du 20/10 : 464 des 529
   brouillons ont deja leur detail REST en local, donc la fiche se fabrique sans
   deranger Hektor une seule fois. Les 65 autres recoivent un REFUS NOMME (voir
   plus bas) -- jamais une fiche vide et muette.

C'EST UN CLONE de Console/prepare_archived_annonce_detail.py (la famille Archive) et
de son jumeau Historical. On garde la MEME forme de charge -- {listing, index,
detail} -- parce que le front lit ces trois cles telles quelles
(apps/hektor-v1/src/lib/api.ts, loadLightweightAnnonceDetailCache).

CE QUI CHANGE PAR RAPPORT AU PATRON, et pourquoi :

  1. LA FAMILLE. L'archive se reconnait a une COLONNE (`archive = '1'`), le brouillon
     a une TABLE A PART (`hektor_annonce_draft_state.is_draft = 1`). C'est toute
     l'histoire de la piece ① : rien dans `hektor_annonce` ne dit qu'une annonce est
     un brouillon -- son statut est « Actif » ou « Estimation » comme les autres.

  2. ⭐ L'INDEX EST LU POUR DE VRAI. Le patron lit `app_view_generale` sur la
     connexion a `hektor.sqlite`, ou cette table N'EXISTE PAS -- mesure du 20/10 :
     0 ATTACH dans le fichier, table absente, donc son `try/except` se declenche
     TOUJOURS et `index_row` reste vide. Consequence chez lui : `app_archive_id`
     recoit le numero HEKTOR au lieu du notre, et la couche `index` de la charge est
     vide. Le front compense (il relit l'index en direct, 31 colonnes, et c'est lui
     qui gagne), donc le defaut est LATENT, pas actif -- il est NOTE, pas corrige
     chez le patron, hors perimetre.
     ⭐ Ici on ouvre `phase2.sqlite` en lecture seule, avec son propre repli declare.
     ⚠ Et SANS `immutable=1` : le run de 05:00 ecrit dans ce fichier, et promettre a
       SQLite qu'il ne change jamais ferait lire des pages perimees.
     ⚠ Avec busy_timeout : la base est tenue une vingtaine de secondes pendant le
       rafraichissement des vues (regle du projet).

  3. LA VALEUR PAR DEFAUT DU DELAI est 24 h, pas 2 h. Le travail du worker passe
     toujours `--ttl-hours 24` explicitement ; c'est la main qui profite du defaut.

LES TROIS REFUS, CHACUN AVEC SON NOM (on ne rend jamais une fiche a moitie) :
  · l'annonce n'est pas dans le miroir      -> « introuvable localement »
  · elle n'est pas (ou plus) un brouillon   -> « n'est pas un brouillon »
  · son detail REST n'est pas descendu      -> « detail absent en local »

    python Console/prepare_brouillon_annonce_detail.py --hektor-annonce-id 63131
    python Console/prepare_brouillon_annonce_detail.py --hektor-annonce-id 63131 --dry-run

⚠ `--dry-run` fabrique la charge et l'affiche SANS rien deposer : c'est ce qui permet
  d'eprouver le script sans ecrire une ligne en production.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "hektor.sqlite"
DEFAULT_PHASE2_DB_PATH = PROJECT_ROOT / "phase2" / "phase2.sqlite"
CACHE_TABLE = "app_brouillon_annonce_detail_cache"


def sqlite_read_connection(path: Path) -> sqlite3.Connection:
    uri = f"file:{path.resolve().as_posix()}?mode=ro&immutable=1"
    return sqlite3.connect(uri, uri=True)


def sqlite_read_connection_vivante(path: Path) -> sqlite3.Connection:
    """Pour une base QU'ON ECRIT AILLEURS (phase2.sqlite) : pas d'immutable, et un
    busy_timeout -- le run de nuit tient le verrou une vingtaine de secondes."""
    uri = f"file:{path.resolve().as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=30)
    conn.execute("pragma busy_timeout = 30000")
    return conn


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def fetch_matterport_groups(annonce_id: str) -> list[dict[str, Any]]:
    supabase_url = (os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL") or "").rstrip("/")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not supabase_url or not service_key:
        return []
    response = requests.get(
        f"{supabase_url}/rest/v1/app_matterport_group",
        headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
        params={
            "select": "*,app_matterport_group_model(*)",
            "hektor_annonce_id": f"eq.{annonce_id}",
            "order": "numero_mandat.asc",
        },
        timeout=20,
    )
    if response.status_code >= 400:
        return []
    groups = response.json() or []
    for group in groups:
        models = group.pop("app_matterport_group_model", None) or []
        group["models"] = sorted(
            models,
            key=lambda item: (
                item.get("display_order") if item.get("display_order") is not None else 999,
                str(item.get("matterport_name") or ""),
            ),
        )
    return groups


def nested_value(source: dict[str, Any], *path: str) -> Any:
    value: Any = source
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def first_text_block(textes: Any) -> dict[str, Any]:
    if not isinstance(textes, list):
        return {}
    for item in textes:
        if isinstance(item, dict) and (item.get("text") or item.get("html")):
            return item
    return {}


def compact_json(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return text
        return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def load_console_missing_fields(conn: sqlite3.Connection, annonce_id: str) -> dict[str, Any]:
    try:
        row = conn.execute(
            """
            select status, console_payload_json, extracted_at
            from hektor_annonce_console_detail
            where hektor_annonce_id = ?
            """,
            (annonce_id,),
        ).fetchone()
    except sqlite3.OperationalError as exc:
        if "hektor_annonce_console_detail" not in str(exc):
            raise
        return {}
    if not row:
        return {}
    status = str(row["status"] or "").strip() or None
    payload = parse_json(row["console_payload_json"], {})
    if not isinstance(payload, dict):
        payload = {}
    fields: dict[str, Any] = {
        "console_missing_fields_status": status or payload.get("status"),
        "console_missing_fields_extracted_at": row["extracted_at"] or payload.get("extracted_at"),
    }
    if fields["console_missing_fields_status"] == "done":
        fields.update(
            {
                "console_missing_fields_json": compact_json(payload),
                "secteur_console_json": compact_json(payload.get("secteur_console_json")),
                "chauffage_console_json": compact_json(payload.get("chauffage_console_json")),
                "diagnostics_contacts_console_json": compact_json(payload.get("diagnostics_contacts_console_json")),
                "honoraires_detail_console_json": compact_json(payload.get("honoraires_detail_console_json")),
                "location_rendement_console_json": compact_json(payload.get("location_rendement_console_json")),
                "pieces_detail_console_json": compact_json(payload.get("pieces_detail_console_json")),
                "dpe_image_url": payload.get("dpe_image_url"),
                "ges_image_url": payload.get("ges_image_url"),
                "dpe_image_urls_json": compact_json(payload.get("dpe_image_urls")),
            }
        )
    return {key: value for key, value in fields.items() if value is not None}


def load_chauffage_missing_fields(conn: sqlite3.Connection, annonce_id: str) -> dict[str, Any]:
    try:
        row = conn.execute(
            """
            select status, chauffage_json, extracted_at
            from hektor_annonce_chauffage_detail
            where hektor_annonce_id = ?
            """,
            (annonce_id,),
        ).fetchone()
    except sqlite3.OperationalError as exc:
        if "hektor_annonce_chauffage_detail" not in str(exc):
            raise
        return {}
    if not row:
        return {}
    status = str(row["status"] or "").strip() or None
    fields: dict[str, Any] = {
        "chauffage_console_status": status,
        "chauffage_console_extracted_at": row["extracted_at"],
    }
    if status == "done":
        fields["chauffage_console_json"] = compact_json(row["chauffage_json"])
    return {key: value for key, value in fields.items() if value is not None}


def build_enriched_detail(detail: dict[str, Any], index_row: dict[str, Any], annonce: dict[str, Any]) -> dict[str, Any]:
    raw_detail = parse_json(detail.get("raw_json"), {})
    textes = parse_json(detail.get("textes_json"), [])
    text_block = first_text_block(textes)
    enriched = {
        **index_row,
        **detail,
        "detail_raw_json": detail.get("raw_json"),
        "localite_json": parse_json(detail.get("localite_json"), None),
        "mandats_json": parse_json(detail.get("mandats_json"), []),
        "proprietaires_json": parse_json(detail.get("proprietaires_json"), []),
        "honoraires_json": parse_json(detail.get("honoraires_json"), []),
        "notes_json": parse_json(detail.get("notes_json"), []),
        "zones_json": parse_json(detail.get("zones_json"), []),
        "particularites_json": parse_json(detail.get("particularites_json"), []),
        "pieces_json": parse_json(detail.get("pieces_json"), []),
        "images_json": parse_json(detail.get("images_json"), []),
        "textes_json": textes,
        "terrain_json": parse_json(detail.get("terrain_json"), None),
        "copropriete_json": parse_json(detail.get("copropriete_json"), None),
    }
    enriched["surface"] = enriched.get("surface") or annonce.get("surface")
    enriched["surface_habitable_detail"] = (
        enriched.get("surface_habitable_detail")
        or nested_value(raw_detail, "ag_interieur", "props", "surfappart", "value")
        or enriched.get("surface")
    )
    enriched["nb_pieces"] = enriched.get("nb_pieces") or nested_value(raw_detail, "ag_interieur", "props", "nbpieces", "value")
    enriched["nb_chambres"] = enriched.get("nb_chambres") or nested_value(raw_detail, "ag_interieur", "props", "NB_CHAMBRES", "value")
    enriched["surface_terrain_detail"] = enriched.get("surface_terrain_detail") or nested_value(raw_detail, "terrain", "props", "surfterrain", "value")
    enriched["texte_principal_titre"] = enriched.get("texte_principal_titre") or text_block.get("titre")
    enriched["texte_principal_html"] = enriched.get("texte_principal_html") or text_block.get("html") or text_block.get("text")
    return enriched


def est_un_brouillon(conn: sqlite3.Connection, annonce_id: str) -> bool:
    """La MEME question que la piece ①, et la meme source : is_draft = 1.

    ⚠ Si la table n'existe pas encore, on ne REND PAS « faux » en silence : ce
      script n'a de sens que pour un brouillon, donc une table absente est une
      panne qu'il faut dire. (A l'inverse de la piece ①, ou l'absence doit laisser
      passer le travail normal -- « builder inerte ».)
    """
    try:
        row = conn.execute(
            """
            select 1
            from hektor_annonce_draft_state
            where cast(hektor_annonce_id as text) = ?
              and coalesce(is_draft, 0) = 1
            limit 1
            """,
            (annonce_id,),
        ).fetchone()
    except sqlite3.OperationalError as exc:
        if "hektor_annonce_draft_state" not in str(exc):
            raise
        raise RuntimeError(
            "La table des brouillons (hektor_annonce_draft_state) est absente du miroir local. "
            "Lance d'abord phase2/sync/sync_hektor_drafts.py."
        ) from exc
    return row is not None


def charger_index_row(annonce_id: str, phase2_path: Path) -> tuple[dict[str, Any], str]:
    """L'index de l'app, lu dans phase2.sqlite -- la base ou il vit VRAIMENT.

    Rend (ligne, raison) : la raison dit pourquoi elle est vide, s'elle l'est. On ne
    tombe jamais en panne pour ca -- le front relit l'index en direct et c'est lui
    qui gagne -- mais on ECRIT ce qu'on n'a pas pu lire.
    """
    if not phase2_path.exists():
        return {}, f"phase2.sqlite absent ({phase2_path})"
    conn = None
    try:
        conn = sqlite_read_connection_vivante(phase2_path)
        conn.row_factory = sqlite3.Row
        row = row_dict(conn.execute(
            """
            select *
            from app_view_generale
            where cast(hektor_annonce_id as text) = ?
            """,
            (annonce_id,),
        ).fetchone())
        if not row:
            return {}, "annonce absente de app_view_generale"
        return row, ""
    except sqlite3.OperationalError as exc:
        return {}, f"phase2.sqlite illisible: {exc}"
    finally:
        if conn is not None:
            conn.close()


def build_detail_payload(conn: sqlite3.Connection, annonce_id: str, phase2_path: Path) -> tuple[int, dict[str, Any], str]:
    annonce = row_dict(conn.execute(
        """
        select *
        from hektor_annonce
        where hektor_annonce_id = ?
        """,
        (annonce_id,),
    ).fetchone())
    if not annonce:
        raise RuntimeError(f"Annonce introuvable localement: {annonce_id}")

    # LA FAMILLE : une TABLE A PART, pas une colonne (voir l'en-tete).
    if not est_un_brouillon(conn, annonce_id):
        raise RuntimeError(
            f"L'annonce {annonce_id} n'est pas un brouillon (is_draft != 1). "
            "Ce script ne prepare que le panier Brouillon."
        )
    # L'index brouillon ecarte les archivees (son propre WHERE archive = '0'), donc on
    # s'aligne sur lui : fabriquer un cache pour une annonce ABSENTE de l'index donnerait
    # une fiche que le front ne saurait pas fusionner.
    # ⚠ GARDE DEFENSIVE, ET MESUREE : 0 brouillon archive le 20/10/2026 (sur 529). Elle
    #   ne porte donc rien aujourd'hui -- ne pas la croire charpente.
    if str(annonce.get("archive") or "0") == "1":
        raise RuntimeError(
            f"L'annonce {annonce_id} est archivee : elle releve du cache Archive, pas du panier Brouillon."
        )

    detail = row_dict(conn.execute(
        """
        select *
        from hektor_annonce_detail
        where hektor_annonce_id = ?
        """,
        (annonce_id,),
    ).fetchone())
    if not detail:
        raise RuntimeError(
            "Detail du brouillon absent en local. Mesure du 20/10 : 464 des 529 brouillons "
            "l'ont, 65 ne l'ont pas encore -- lance la recuperation des details avant."
        )

    index_row, raison_index = charger_index_row(annonce_id, phase2_path)
    app_brouillon_id = int(index_row.get("app_dossier_id") or annonce_id)
    enriched_detail = build_enriched_detail(detail, index_row, annonce)
    enriched_detail.update(load_console_missing_fields(conn, annonce_id))
    enriched_detail.update(load_chauffage_missing_fields(conn, annonce_id))
    payload = {
        "hektor_annonce_id": annonce_id,
        "app_brouillon_id": app_brouillon_id,
        "listing": annonce,
        "index": index_row,
        "detail": enriched_detail,
        "prepared_locally_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return app_brouillon_id, payload, raison_index


def supabase_upsert(row: dict[str, Any]) -> None:
    supabase_url = (os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL") or "").rstrip("/")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not supabase_url or not service_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    response = requests.post(
        f"{supabase_url}/rest/v1/{CACHE_TABLE}?on_conflict=hektor_annonce_id",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation",
        },
        json=[row],
        timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Supabase cache upsert failed: {response.status_code} {response.text[:800]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hektor-annonce-id", required=True)
    parser.add_argument("--requested-by")
    parser.add_argument("--ttl-hours", type=int, default=24)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--phase2-db-path", default=str(DEFAULT_PHASE2_DB_PATH))
    parser.add_argument("--dry-run", action="store_true",
                        help="fabrique la charge et l'affiche SANS rien deposer chez Supabase")
    args = parser.parse_args()

    load_env(PROJECT_ROOT / ".env")
    load_env(PROJECT_ROOT / "apps" / "hektor-v1" / ".env")

    annonce_id = str(args.hektor_annonce_id).strip()
    if not annonce_id.isdigit():
        raise RuntimeError("hektor_annonce_id numerique requis")

    conn = sqlite_read_connection(Path(args.db_path))
    conn.row_factory = sqlite3.Row
    try:
        app_brouillon_id, payload, raison_index = build_detail_payload(
            conn, annonce_id, Path(args.phase2_db_path)
        )
    finally:
        conn.close()

    payload["detail"]["matterport_groups_json"] = json.dumps(
        fetch_matterport_groups(annonce_id) if not args.dry_run else [],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    prepared_at = datetime.now(timezone.utc)
    row = {
        "hektor_annonce_id": int(annonce_id),
        "app_brouillon_id": app_brouillon_id,
        "detail_payload_json": payload,
        "requested_by": args.requested_by or None,
        "prepared_at": prepared_at.isoformat(timespec="seconds"),
        "expires_at": (prepared_at + timedelta(hours=max(1, args.ttl_hours))).isoformat(timespec="seconds"),
        "source_hash": hashlib.sha256(payload_text.encode("utf-8")).hexdigest(),
        "source_updated_at": payload["listing"].get("date_maj") or None,
    }
    if not args.dry_run:
        supabase_upsert(row)
    compte_rendu = {
        "status": "dry_run" if args.dry_run else "done",
        "hektor_annonce_id": annonce_id,
        "app_brouillon_id": app_brouillon_id,
        "payload_bytes": len(payload_text.encode("utf-8")),
        "expires_at": row["expires_at"],
        "cache_table": CACHE_TABLE,
        "index_champs": len(payload["index"]),
        "detail_champs": len(payload["detail"]),
    }
    # ⚠ On DIT quand l'index n'a pas pu etre lu, au lieu de rendre une charge
    #   silencieusement plus pauvre.
    if raison_index:
        compte_rendu["index_non_lu"] = raison_index
    print(json.dumps(compte_rendu, ensure_ascii=False))


if __name__ == "__main__":
    main()
