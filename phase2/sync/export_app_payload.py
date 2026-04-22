from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict


ROOT = Path(__file__).resolve().parent.parent.parent
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
OUTPUT_JSON = ROOT / "phase2" / "docs" / "APP_PAYLOAD_V1_SAMPLE.json"
SQLITE_IN_MAX = 900
MAX_EXPORTED_IMAGES = 5
ANNONCES_SCOPE_WHERE = (
    "COALESCE(archive, '0') = '0' "
    "AND COALESCE(detail_statut_name, statut_annonce, '') IN ('Actif', 'Sous offre', 'Sous compromis')"
)
REGISTRE_SCOPE_STATUTS = ("Actif", "Sous offre", "Sous compromis", "Vendu", "Clos")
REGISTRE_SCOPE_SQL = ",".join(f"'{value}'" for value in REGISTRE_SCOPE_STATUTS)


SQL_SUMMARY = """
SELECT
    (SELECT COUNT(*) FROM app_view_generale WHERE __ANNONCES_SCOPE_WHERE__) AS total_dossiers,
    (
        SELECT COUNT(*)
        FROM app_view_demandes_mandat_diffusion
        WHERE app_dossier_id IN (
            SELECT app_dossier_id FROM app_view_generale WHERE __ANNONCES_SCOPE_WHERE__
        )
    ) AS total_demandes,
    (SELECT COUNT(*) FROM app_view_generale WHERE __ANNONCES_SCOPE_WHERE__ AND NULLIF(TRIM(numero_mandat), '') IS NULL) AS total_sans_mandat,
    (SELECT COUNT(*) FROM app_view_generale WHERE __ANNONCES_SCOPE_WHERE__ AND COALESCE(has_open_blocker, 0) = 1) AS total_bloques,
    (SELECT COUNT(*) FROM app_view_generale WHERE __ANNONCES_SCOPE_WHERE__ AND COALESCE(validation_diffusion_state, '') = 'valide') AS total_valides_diffusion,
    (SELECT COUNT(*) FROM app_view_generale WHERE __ANNONCES_SCOPE_WHERE__ AND COALESCE(etat_visibilite, '') = 'visible') AS total_visibles;
""".replace("__ANNONCES_SCOPE_WHERE__", ANNONCES_SCOPE_WHERE)


SQL_DOSSIERS_BASE = """
SELECT
    app_dossier_id,
    hektor_annonce_id,
    archive,
    numero_dossier,
    numero_mandat,
    mandat_source_id,
    mandat_numero_reference,
    titre_bien,
    ville,
    type_bien,
    prix,
    commercial_id,
    commercial_nom,
    negociateur_email,
    statut_annonce,
    validation_diffusion_state,
    etat_visibilite,
    alerte_principale,
    priority,
    has_open_blocker,
    commentaire_resume,
    date_relance_prevue,
    dernier_event_type,
    dernier_work_status,
    code_postal,
    surface,
    date_maj,
    date_enregistrement_annonce,
    photo_url_listing,
    corps_listing_html,
    ville_publique_listing,
    code_postal_public_listing,
    adresse_privee_listing,
    agence_nom,
    responsable_affichage,
    responsable_type,
    archive,
    diffusable,
    valide,
    mandat_type,
    mandat_date_debut,
    mandat_date_fin,
    mandat_date_cloture,
    mandat_numero_source,
    mandat_type_source,
    mandat_date_enregistrement,
    mandat_montant,
    mandants_texte,
    mandat_note,
    nb_portails_actifs,
    has_diffusion_error,
    portails_resume,
    offre_id,
    offre_state,
    offre_event_date,
    offre_raw_status,
    offre_montant,
    offre_acquereur_nom,
    offre_acquereur_portable,
    offre_acquereur_email,
    compromis_id,
    compromis_state,
    compromis_date_start,
    compromis_date_end,
    date_signature_acte,
    prix_net_vendeur,
    prix_publique,
    compromis_part_admin,
    compromis_sequestre,
    compromis_acquereurs_resume,
    vente_id,
    vente_date,
    vente_prix,
    vente_honoraires,
    vente_part_admin,
    vente_commission_agence,
    vente_acquereurs_resume,
    vente_notaires_resume,
    detail_statut_name,
    localite_json,
    mandats_json,
    proprietaires_json,
    honoraires_json,
    notes_json,
    zones_json,
    particularites_json,
    pieces_json,
    images_json,
    textes_json,
    terrain_json,
    copropriete_json,
    detail_raw_json,
    annonce_list_raw_json,
    code_postal_detail,
    latitude_detail,
    longitude_detail,
    adresse_detail,
    ville_privee_detail,
    code_postal_prive_detail,
    nb_images,
    nb_textes,
    nb_notes_hektor,
    nb_proprietaires,
    images_preview_json,
    texte_principal_titre,
    texte_principal_html,
    nb_pieces,
    nb_chambres,
    surface_habitable_detail,
    etage_detail,
    terrasse_detail,
    garage_box_detail,
    surface_terrain_detail,
    copropriete_detail,
    ascenseur_detail,
    proprietaires_resume,
    proprietaires_contacts,
    honoraires_resume,
    note_hektor_principale,
    etat_transaction,
    internal_status,
    motif_blocage,
    next_action,
    date_entree_file,
    date_derniere_action,
    is_blocked,
    is_followup_needed
FROM app_view_generale
WHERE __ANNONCES_SCOPE_WHERE__
ORDER BY
    CASE WHEN priority = 'urgent' THEN 1 WHEN priority = 'high' THEN 2 WHEN priority = 'normal' THEN 3 ELSE 4 END,
    hektor_annonce_id
""".replace("__ANNONCES_SCOPE_WHERE__", ANNONCES_SCOPE_WHERE)


DETAIL_PAYLOAD_FIELDS = {
    "code_postal",
    "surface",
    "date_maj",
    "date_enregistrement_annonce",
    "photo_url_listing",
    "corps_listing_html",
    "ville_publique_listing",
    "code_postal_public_listing",
    "adresse_privee_listing",
    "agence_nom",
    "responsable_affichage",
    "responsable_type",
    "diffusable",
    "valide",
    "mandat_type",
    "mandat_date_debut",
    "mandat_date_fin",
    "mandat_date_cloture",
    "mandat_source_id",
    "mandat_numero_reference",
    "mandat_numero_source",
    "mandat_type_source",
    "mandat_date_enregistrement",
    "mandat_montant",
    "mandants_texte",
    "mandat_note",
    "nb_portails_actifs",
    "has_diffusion_error",
    "portails_resume",
    "offre_id",
    "offre_state",
    "offre_last_proposition_type",
    "offre_event_date",
    "offre_raw_status",
    "offre_montant",
    "offre_acquereur_nom",
    "offre_acquereur_portable",
    "offre_acquereur_email",
    "compromis_id",
    "compromis_state",
    "compromis_date_start",
    "compromis_date_end",
    "date_signature_acte",
    "prix_net_vendeur",
    "prix_publique",
    "compromis_part_admin",
    "compromis_sequestre",
    "compromis_acquereurs_resume",
    "vente_id",
    "vente_date",
    "vente_prix",
    "vente_honoraires",
    "vente_part_admin",
    "vente_commission_agence",
    "vente_acquereurs_resume",
    "vente_notaires_resume",
    "detail_statut_name",
    "localite_json",
    "mandats_json",
    "proprietaires_json",
    "honoraires_json",
    "notes_json",
    "zones_json",
    "particularites_json",
    "pieces_json",
    "images_json",
    "textes_json",
    "terrain_json",
    "copropriete_json",
    "detail_raw_json",
    "annonce_list_raw_json",
    "code_postal_detail",
    "latitude_detail",
    "longitude_detail",
    "adresse_detail",
    "ville_privee_detail",
    "code_postal_prive_detail",
    "nb_images",
    "nb_textes",
    "nb_notes_hektor",
    "nb_proprietaires",
    "images_preview_json",
    "texte_principal_titre",
    "texte_principal_html",
    "nb_pieces",
    "nb_chambres",
    "surface_habitable_detail",
    "etage_detail",
    "terrasse_detail",
    "garage_box_detail",
    "surface_terrain_detail",
    "copropriete_detail",
    "ascenseur_detail",
    "proprietaires_resume",
    "proprietaires_contacts",
    "honoraires_resume",
    "note_hektor_principale",
    "etat_transaction",
    "internal_status",
    "motif_blocage",
    "next_action",
    "date_entree_file",
    "date_derniere_action",
    "is_blocked",
    "is_followup_needed",
}
DETAIL_PAYLOAD_FIELD_ORDER = tuple(sorted(DETAIL_PAYLOAD_FIELDS))

DOSSIER_KEEP_FIELDS = {
    "agence_nom",
    "negociateur_email",
    "diffusable",
    "adresse_privee_listing",
    "adresse_detail",
    "code_postal",
    "code_postal_prive_detail",
    "ville_privee_detail",
    "nb_portails_actifs",
    "has_diffusion_error",
    "portails_resume",
    "photo_url_listing",
    "images_preview_json",
    "mandat_type",
    "mandat_type_source",
    "mandat_date_debut",
    "mandat_date_fin",
    "mandat_montant",
    "mandants_texte",
    "mandat_source_id",
    "mandat_numero_reference",
    "offre_id",
    "offre_state",
    "offre_last_proposition_type",
    "compromis_id",
    "compromis_state",
    "vente_id",
}


SQL_WORK_ITEMS_BASE = """
SELECT
    app_dossier_id,
    hektor_annonce_id,
    archive,
    numero_dossier,
    numero_mandat,
    titre_bien,
    commercial_nom,
    type_demande_label,
    work_status,
    internal_status,
    priority,
    validation_diffusion_state,
    etat_visibilite,
    motif_blocage,
    has_open_blocker,
    next_action,
    date_relance_prevue,
    date_entree_file,
    date_derniere_action,
    age_jours
FROM app_view_demandes_mandat_diffusion
WHERE app_dossier_id IN (
    SELECT app_dossier_id
    FROM app_view_generale
    WHERE __ANNONCES_SCOPE_WHERE__
)
ORDER BY
    CASE WHEN priority = 'urgent' THEN 1 WHEN priority = 'high' THEN 2 WHEN priority = 'normal' THEN 3 ELSE 4 END,
    age_jours DESC
""".replace("__ANNONCES_SCOPE_WHERE__", ANNONCES_SCOPE_WHERE)


SQL_BROADCASTS_BASE = """
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
WHERE __ANNONCES_SCOPE_WHERE__
ORDER BY d.app_dossier_id, s.passerelle_key, commercial_key
""".replace("__ANNONCES_SCOPE_WHERE__", ANNONCES_SCOPE_WHERE)


SQL_REGISTER_RAW_BASE = f"""
SELECT
    ann.hektor_annonce_id,
    ann.no_dossier,
    ann.no_mandat,
    ann.hektor_agence_id,
    ann.hektor_negociateur_id,
    ann.date_maj,
    ann.offre_type,
    ann.idtype,
    ann.prix,
    ann.surface,
    ann.archive,
    ann.diffusable,
    ann.valide,
    ann.partage,
    ann.titre,
    ann.ville,
    ann.code_postal,
    ann.raw_json AS annonce_raw_json,
    ann.synced_at AS annonce_synced_at,
    det.statut_name,
    det.localite_json,
    det.mandats_json,
    det.images_json,
    det.textes_json,
    det.raw_json AS detail_raw_json,
    det.synced_at AS detail_synced_at,
    ag.nom AS agence_nom,
    neg.prenom AS negociateur_prenom,
    neg.nom AS negociateur_nom,
    neg.email AS negociateur_email
FROM hektor.hektor_annonce ann
LEFT JOIN hektor.hektor_annonce_detail det
    ON det.hektor_annonce_id = ann.hektor_annonce_id
LEFT JOIN hektor.hektor_agence ag
    ON ag.hektor_agence_id = ann.hektor_agence_id
LEFT JOIN hektor.hektor_negociateur neg
    ON neg.hektor_negociateur_id = ann.hektor_negociateur_id
WHERE COALESCE(det.statut_name, '') IN ({REGISTRE_SCOPE_SQL})
ORDER BY CAST(ann.hektor_annonce_id AS INTEGER), ann.no_mandat
"""


SQL_REGISTER_BROADCAST_AGG = """
SELECT
    s.hektor_annonce_id,
    SUM(CASE WHEN s.current_state = 'broadcasted' THEN 1 ELSE 0 END) AS nb_portails_actifs,
    MAX(CASE WHEN s.is_error = 1 THEN 1 ELSE 0 END) AS has_diffusion_error,
    GROUP_CONCAT(CASE WHEN s.current_state = 'broadcasted' THEN s.passerelle_key END, ', ') AS portails_resume
FROM hektor.hektor_annonce_broadcast_state s
GROUP BY s.hektor_annonce_id
"""


def fetch_rows(con: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
    cursor = con.execute(sql, params)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def build_limited_sql(base_sql: str, limit: int | None) -> str:
    if limit is None:
        return base_sql + ";"
    return f"{base_sql}\nLIMIT {int(limit)};"


def build_filtered_sql(base_sql: str, *, id_column: str, ids: list[int] | None, limit: int | None) -> tuple[str, tuple[object, ...]]:
    sql = base_sql
    params: list[object] = []
    if ids:
        placeholders = ",".join("?" for _ in ids)
        sql = f"SELECT * FROM ({base_sql}) AS base WHERE {id_column} IN ({placeholders})"
        params.extend(ids)
    sql = build_limited_sql(sql, limit)
    return sql, tuple(params)


def fetch_rows_by_ids(
    con: sqlite3.Connection,
    *,
    base_sql: str,
    id_column: str,
    ids: list[int] | None,
    limit: int | None,
) -> list[dict[str, object]]:
    if not ids:
        return fetch_rows(con, build_limited_sql(base_sql, limit))

    if limit is not None and limit <= 0:
        return []

    remaining = limit
    rows: list[dict[str, object]] = []
    for start in range(0, len(ids), SQLITE_IN_MAX):
        batch_ids = ids[start : start + SQLITE_IN_MAX]
        batch_limit = remaining if remaining is not None else None
        sql, params = build_filtered_sql(
            base_sql,
            id_column=id_column,
            ids=batch_ids,
            limit=batch_limit,
        )
        batch_rows = fetch_rows(con, sql, params)
        rows.extend(batch_rows)
        if remaining is not None:
            remaining -= len(batch_rows)
            if remaining <= 0:
                break
    return rows


def trim_json_array_field(value: object, *, limit: int) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return raw
    if not isinstance(parsed, list):
        return raw
    return json.dumps(parsed[:limit], ensure_ascii=True, separators=(",", ":"))


def normalize_offer_proposition_type(value: object) -> str | None:
    text = str(value or "").strip().lower()
    return text or None


def parse_offer_proposition_date(value: object) -> tuple[int, str]:
    text = str(value or "").strip()
    if not text:
        return (0, "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text, fmt)
            return (1, parsed.isoformat())
        except ValueError:
            continue
    return (0, text)


def derive_offer_last_proposition_type(value: object) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(parsed, list):
        return None
    events: list[tuple[tuple[int, str], int, str]] = []
    for index, item in enumerate(parsed):
        if not isinstance(item, dict):
            continue
        event_type = normalize_offer_proposition_type(item.get("type"))
        if not event_type:
            continue
        events.append((parse_offer_proposition_date(item.get("date")), index, event_type))
    if not events:
        return None
    events.sort(key=lambda entry: (entry[0][0], entry[0][1], entry[1]))
    return events[-1][2]


def safe_json_loads(value: object, fallback: object):
    raw = str(value or "").strip()
    if not raw:
        return fallback
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback
    return parsed if parsed is not None else fallback


def normalize_text(value: object) -> str:
    return str(value or "").strip()


def normalize_register_mandat_type(value: object) -> str | None:
    text = normalize_text(value)
    if not text:
        return None
    lowered = text.lower()
    if "semi-exclusif" in lowered:
        return "ACCORD"
    if "non exclusif" in lowered or "mandat de vente" in lowered:
        return "SIMPLE"
    if "exclusif" in lowered:
        return "EXCLUSIF"
    if lowered == "simple":
        return "SIMPLE"
    if lowered == "exclusif":
        return "EXCLUSIF"
    if lowered == "accord":
        return "ACCORD"
    return text


def derive_register_validation_state(value: object) -> str:
    return "valide" if normalize_text(value) == "1" else "a_controler"


def build_images_preview_json(images_json: object) -> str | None:
    images = safe_json_loads(images_json, [])
    if not isinstance(images, list) or not images:
        return None
    preview: list[dict[str, object]] = []
    for item in images:
        if not isinstance(item, dict):
            continue
        preview.append(
            {
                "url": item.get("pathTumb") or item.get("path"),
                "full": item.get("path"),
                "legend": item.get("legende"),
                "order": item.get("order"),
            }
        )
    if not preview:
        return None
    preview.sort(key=lambda entry: int(str(entry.get("order") or "9999")) if str(entry.get("order") or "").isdigit() else 9999)
    return json.dumps(preview[:MAX_EXPORTED_IMAGES], ensure_ascii=True, separators=(",", ":"))


def pick_listing_photo(images_preview_json: str | None, annonce_raw_json: object) -> str | None:
    preview = safe_json_loads(images_preview_json, [])
    if isinstance(preview, list):
        for item in preview:
            if isinstance(item, dict):
                candidate = normalize_text(item.get("url"))
                if candidate:
                    return candidate
    annonce_raw = safe_json_loads(annonce_raw_json, {})
    if isinstance(annonce_raw, dict):
        return normalize_text(annonce_raw.get("photo")) or None
    return None


def compute_mandat_version_score(item: dict[str, object]) -> tuple[int, int]:
    fields = [
        "type",
        "debut",
        "fin",
        "cloture",
        "montant",
        "mandants",
        "note",
    ]
    score = sum(1 for field in fields if normalize_text(item.get(field)))
    raw_id = normalize_text(item.get("id"))
    digits = "".join(ch for ch in raw_id if ch.isdigit())
    numeric_id = int(digits) if digits else -1
    return score, numeric_id


def normalize_history_version(item: dict[str, object], *, is_current: bool, index: int) -> dict[str, object]:
    return {
        "history_id": f"{normalize_text(item.get('numero'))}:{normalize_text(item.get('id')) or index}",
        "label": "Version courante" if is_current else f"Version {index + 1}",
        "source_id": normalize_text(item.get("id")) or None,
        "numero": normalize_text(item.get("numero")) or None,
        "type": normalize_register_mandat_type(item.get("type")),
        "type_source": normalize_text(item.get("type")) or None,
        "date_debut": normalize_text(item.get("debut")) or None,
        "date_fin": normalize_text(item.get("fin")) or None,
        "date_cloture": normalize_text(item.get("cloture")) or None,
        "montant": normalize_text(item.get("montant")) or None,
        "mandants_texte": normalize_text(item.get("mandants")) or None,
        "note": normalize_text(item.get("note")) or None,
        "is_current": is_current,
    }


def normalize_embedded_avenants(versions: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for version in versions:
        source_id = normalize_text(version.get("id")) or None
        numero_parent = normalize_text(version.get("numero")) or None
        embedded = version.get("avenants")
        if not isinstance(embedded, list):
            continue
        for index, avenant in enumerate(embedded):
            if not isinstance(avenant, dict):
                continue
            rows.append(
                {
                    "avenant_id": f"{source_id or numero_parent or 'mandat'}:{index}",
                    "source_id": source_id,
                    "numero_parent": numero_parent,
                    "numero": normalize_text(avenant.get("numero")) or None,
                    "date": normalize_text(avenant.get("date")) or None,
                    "detail": normalize_text(avenant.get("detail")) or None,
                }
            )
    rows.sort(key=lambda item: (item.get("date") or "", item.get("numero") or ""))
    return rows


def synthetic_register_app_dossier_id(hektor_annonce_id: str, numero_mandat: str) -> int:
    digest = hashlib.sha1(f"{hektor_annonce_id}:{numero_mandat}".encode("utf-8")).hexdigest()[:12]
    return -int(digest, 16)


def mandate_sort_number(value: object) -> int:
    digits = "".join(ch for ch in normalize_text(value) if ch.isdigit())
    return int(digits) if digits else 0


def build_register_detail_payload(
    *,
    raw_row: dict[str, object],
    current_version: dict[str, object],
    versions: list[dict[str, object]],
    embedded_avenants: list[dict[str, object]],
    images_preview_json: str | None,
    active_row: dict[str, object] | None,
    detail_available: bool,
) -> str:
    localite = safe_json_loads(raw_row.get("localite_json"), {})
    textes = safe_json_loads(raw_row.get("textes_json"), [])
    raw_detail = safe_json_loads(raw_row.get("detail_raw_json"), {})
    preview_images = safe_json_loads(images_preview_json, [])
    text_title = textes[0].get("titre") if isinstance(textes, list) and textes and isinstance(textes[0], dict) else None
    text_html = textes[0].get("text") if isinstance(textes, list) and textes and isinstance(textes[0], dict) else None
    payload = {
        "detail_available": detail_available,
        "source_kind": "actif" if detail_available else "historique",
        "app_dossier_id": active_row.get("app_dossier_id") if active_row else None,
        "titre_bien": active_row.get("titre_bien") if active_row else (normalize_text(raw_row.get("titre")) or normalize_text(text_title) or None),
        "photo_url_listing": active_row.get("photo_url_listing") if active_row else pick_listing_photo(images_preview_json, raw_row.get("annonce_raw_json")),
        "images_preview_json": active_row.get("images_preview_json") if active_row else images_preview_json,
        "adresse_privee_listing": active_row.get("adresse_privee_listing") if active_row else normalize_text(localite.get("privee", {}).get("adresse") if isinstance(localite, dict) else None) or None,
        "adresse_detail": active_row.get("adresse_detail") if active_row else normalize_text(localite.get("privee", {}).get("adresse") if isinstance(localite, dict) else None) or None,
        "ville": active_row.get("ville") if active_row else normalize_text(raw_row.get("ville")) or None,
        "ville_privee_detail": active_row.get("ville_privee_detail") if active_row else normalize_text(localite.get("privee", {}).get("ville") if isinstance(localite, dict) else None) or None,
        "code_postal": active_row.get("code_postal") if active_row else normalize_text(raw_row.get("code_postal")) or None,
        "code_postal_prive_detail": active_row.get("code_postal_prive_detail") if active_row else normalize_text(localite.get("privee", {}).get("code") if isinstance(localite, dict) else None) or None,
        "texte_principal_titre": active_row.get("texte_principal_titre") if active_row else normalize_text(text_title) or None,
        "texte_principal_html": active_row.get("texte_principal_html") if active_row else normalize_text(text_html) or None,
        "surface": active_row.get("surface") if active_row else raw_row.get("surface"),
        "surface_habitable_detail": active_row.get("surface_habitable_detail") if active_row else (raw_detail.get("ag_interieur", {}).get("props", {}).get("surfappart", {}).get("value") if isinstance(raw_detail, dict) else None),
        "nb_pieces": active_row.get("nb_pieces") if active_row else (raw_detail.get("ag_interieur", {}).get("props", {}).get("nbpieces", {}).get("value") if isinstance(raw_detail, dict) else None),
        "nb_chambres": active_row.get("nb_chambres") if active_row else (raw_detail.get("ag_interieur", {}).get("props", {}).get("NB_CHAMBRES", {}).get("value") if isinstance(raw_detail, dict) else None),
        "mandat_history_json": json.dumps([normalize_history_version(item, is_current=index == 0, index=index) for index, item in enumerate(versions)], ensure_ascii=True, separators=(",", ":")),
        "mandat_avenants_json": json.dumps(embedded_avenants, ensure_ascii=True, separators=(",", ":")),
        "mandat_type": normalize_register_mandat_type(current_version.get("type")),
        "mandat_type_source": normalize_text(current_version.get("type")) or None,
        "mandat_date_debut": normalize_text(current_version.get("debut")) or None,
        "mandat_date_fin": normalize_text(current_version.get("fin")) or None,
        "mandat_date_cloture": normalize_text(current_version.get("cloture")) or None,
        "mandat_montant": normalize_text(current_version.get("montant")) or None,
        "mandants_texte": normalize_text(current_version.get("mandants")) or None,
        "mandat_note": normalize_text(current_version.get("note")) or None,
        "nb_images": len(preview_images) if isinstance(preview_images, list) else 0,
    }
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def build_mandat_register_rows(con: sqlite3.Connection, *, limit: int | None) -> list[dict[str, object]]:
    active_rows = enrich_offer_transaction_fields(con, fetch_rows(con, build_limited_sql(SQL_DOSSIERS_BASE, None)))
    active_by_key = {
        (normalize_text(row.get("hektor_annonce_id")), normalize_text(row.get("numero_mandat"))): row
        for row in active_rows
        if normalize_text(row.get("hektor_annonce_id")) and normalize_text(row.get("numero_mandat"))
    }
    active_by_annonce: dict[str, dict[str, object]] = {}
    for row in active_rows:
        annonce_id = normalize_text(row.get("hektor_annonce_id"))
        if annonce_id and annonce_id not in active_by_annonce:
            active_by_annonce[annonce_id] = row

    broadcast_map = {
        normalize_text(row.get("hektor_annonce_id")): row
        for row in fetch_rows(con, build_limited_sql(SQL_REGISTER_BROADCAST_AGG, None))
    }

    register_rows: list[dict[str, object]] = []
    raw_rows = fetch_rows(con, build_limited_sql(SQL_REGISTER_RAW_BASE, None))
    for raw in raw_rows:
        annonce_id = normalize_text(raw.get("hektor_annonce_id"))
        if not annonce_id:
            continue
        status = normalize_text(raw.get("statut_name"))
        active_any = active_by_annonce.get(annonce_id)
        mandates = safe_json_loads(raw.get("mandats_json"), [])
        mandate_entries: list[dict[str, object]] = []
        if isinstance(mandates, list):
            for item in mandates:
                if not isinstance(item, dict):
                    continue
                numero = normalize_text(item.get("numero"))
                if not numero:
                    continue
                mandate_entries.append(item)
        fallback_numero = normalize_text(raw.get("no_mandat"))
        if not mandate_entries and fallback_numero:
            mandate_entries.append(
                {
                    "id": None,
                    "numero": fallback_numero,
                    "type": None,
                    "debut": None,
                    "fin": None,
                    "cloture": None,
                    "montant": None,
                    "mandants": None,
                    "note": None,
                    "avenants": [],
                }
            )
        if not mandate_entries:
            continue

        grouped_entries: dict[str, list[dict[str, object]]] = defaultdict(list)
        for item in mandate_entries:
            grouped_entries[normalize_text(item.get("numero"))].append(item)

        annonce_raw = safe_json_loads(raw.get("annonce_raw_json"), {})
        localite = safe_json_loads(raw.get("localite_json"), {})
        images_preview_json = active_any.get("images_preview_json") if active_any else build_images_preview_json(raw.get("images_json"))
        photo_url_listing = active_any.get("photo_url_listing") if active_any else pick_listing_photo(images_preview_json, raw.get("annonce_raw_json"))
        address_private = active_any.get("adresse_privee_listing") if active_any else normalize_text(localite.get("privee", {}).get("adresse") if isinstance(localite, dict) else None) or None
        address_detail = active_any.get("adresse_detail") if active_any else address_private
        city_private = active_any.get("ville_privee_detail") if active_any else normalize_text(localite.get("privee", {}).get("ville") if isinstance(localite, dict) else None) or None
        postal_private = active_any.get("code_postal_prive_detail") if active_any else normalize_text(localite.get("privee", {}).get("code") if isinstance(localite, dict) else None) or None
        titre_bien = (
            normalize_text(active_any.get("titre_bien")) if active_any else ""
        ) or normalize_text(raw.get("titre")) or normalize_text((safe_json_loads(raw.get("textes_json"), [{}])[0] or {}).get("titre")) or "[Sans titre]"
        commercial_nom = (
            normalize_text(active_any.get("commercial_nom")) if active_any else ""
        ) or " ".join(filter(None, [normalize_text(raw.get("negociateur_prenom")), normalize_text(raw.get("negociateur_nom"))])).strip() or None
        agence_nom = (normalize_text(active_any.get("agence_nom")) if active_any else "") or normalize_text(raw.get("agence_nom")) or None
        broadcast = broadcast_map.get(annonce_id, {})

        for numero, versions in grouped_entries.items():
            versions_sorted = sorted(
                versions,
                key=lambda item: compute_mandat_version_score(item),
                reverse=True,
            )
            current_version = versions_sorted[0]
            active_exact = active_by_key.get((annonce_id, numero))
            source_row = active_exact or active_any
            detail_available = source_row is not None and source_row.get("app_dossier_id") is not None
            synthetic_app_dossier_id = int(source_row.get("app_dossier_id")) if detail_available else synthetic_register_app_dossier_id(annonce_id, numero)
            embedded_avenants = normalize_embedded_avenants(versions_sorted)
            source_updated_at = (
                normalize_text(source_row.get("date_maj")) if source_row else ""
            ) or normalize_text(raw.get("date_maj")) or normalize_text(raw.get("detail_synced_at")) or normalize_text(raw.get("annonce_synced_at")) or None
            row = {
                "register_row_id": f"{annonce_id}:{numero}",
                "app_dossier_id": synthetic_app_dossier_id,
                "hektor_annonce_id": int(annonce_id),
                "photo_url_listing": photo_url_listing,
                "images_preview_json": images_preview_json,
                "adresse_privee_listing": address_private,
                "adresse_detail": address_detail,
                "code_postal": (source_row.get("code_postal") if source_row else None) or normalize_text(raw.get("code_postal")) or None,
                "code_postal_prive_detail": postal_private,
                "ville_privee_detail": city_private,
                "archive": (source_row.get("archive") if source_row else None) or normalize_text(raw.get("archive")) or "0",
                "diffusable": (source_row.get("diffusable") if source_row else None) or normalize_text(raw.get("diffusable")) or "0",
                "nb_portails_actifs": int((source_row.get("nb_portails_actifs") if source_row else None) or broadcast.get("nb_portails_actifs") or 0),
                "has_diffusion_error": bool((source_row.get("has_diffusion_error") if source_row else None) or broadcast.get("has_diffusion_error")),
                "portails_resume": (source_row.get("portails_resume") if source_row else None) or normalize_text(broadcast.get("portails_resume")) or None,
                "numero_dossier": (source_row.get("numero_dossier") if source_row else None) or normalize_text(raw.get("no_dossier")) or None,
                "numero_mandat": numero,
                "register_sort_num": mandate_sort_number(numero),
                "titre_bien": titre_bien,
                "ville": (source_row.get("ville") if source_row else None) or normalize_text(raw.get("ville")) or None,
                "type_bien": (source_row.get("type_bien") if source_row else None) or normalize_text(raw.get("idtype")) or None,
                "prix": (source_row.get("prix") if source_row else None) or raw.get("prix"),
                "commercial_id": (source_row.get("commercial_id") if source_row else None) or normalize_text(raw.get("hektor_negociateur_id")) or None,
                "commercial_nom": commercial_nom,
                "negociateur_email": (source_row.get("negociateur_email") if source_row else None) or normalize_text(raw.get("negociateur_email")) or None,
                "agence_nom": agence_nom,
                "statut_annonce": (source_row.get("statut_annonce") if source_row else None) or status or None,
                "validation_diffusion_state": (source_row.get("validation_diffusion_state") if source_row else None) or derive_register_validation_state(raw.get("valide")),
                "mandat_source_id": normalize_text(current_version.get("id")) or None,
                "mandat_numero_reference": numero,
                "mandat_type": normalize_register_mandat_type(current_version.get("type")),
                "mandat_type_source": normalize_text(current_version.get("type")) or None,
                "mandat_date_debut": normalize_text(current_version.get("debut")) or None,
                "mandat_date_fin": normalize_text(current_version.get("fin")) or None,
                "mandat_montant": normalize_text(current_version.get("montant")) or None,
                "mandants_texte": normalize_text(current_version.get("mandants")) or None,
                "mandat_note": normalize_text(current_version.get("note")) or None,
                "priority": source_row.get("priority") if source_row else None,
                "offre_id": source_row.get("offre_id") if source_row else None,
                "offre_state": source_row.get("offre_state") if source_row else None,
                "offre_last_proposition_type": source_row.get("offre_last_proposition_type") if source_row else None,
                "compromis_id": source_row.get("compromis_id") if source_row else None,
                "compromis_state": source_row.get("compromis_state") if source_row else None,
                "vente_id": source_row.get("vente_id") if source_row else None,
                "source_updated_at": source_updated_at,
                "register_source_kind": "historique" if status in {"Vendu", "Clos"} or not detail_available else "actif",
                "register_detail_available": 1 if detail_available else 0,
                "register_version_count": len(versions_sorted),
                "register_embedded_avenant_count": len(embedded_avenants),
                "register_history_json": json.dumps(
                    [normalize_history_version(item, is_current=index == 0, index=index) for index, item in enumerate(versions_sorted)],
                    ensure_ascii=True,
                    separators=(",", ":"),
                ),
                "register_avenants_json": json.dumps(embedded_avenants, ensure_ascii=True, separators=(",", ":")),
                "register_detail_payload_json": build_register_detail_payload(
                    raw_row=raw,
                    current_version=current_version,
                    versions=versions_sorted,
                    embedded_avenants=embedded_avenants,
                    images_preview_json=images_preview_json,
                    active_row=source_row,
                    detail_available=detail_available,
                ),
            }
            register_rows.append(row)

    register_rows.sort(
        key=lambda item: (
            -(int("".join(ch for ch in str(item.get("numero_mandat") or "") if ch.isdigit()) or 0)),
            -int(item.get("hektor_annonce_id") or 0),
            str(item.get("register_row_id") or ""),
        )
    )
    if limit is not None:
        return register_rows[:limit]
    return register_rows


def build_offer_last_proposition_type_by_id(con: sqlite3.Connection, offre_ids: list[str]) -> dict[str, str | None]:
    cleaned_ids = [str(value).strip() for value in offre_ids if str(value).strip()]
    if not cleaned_ids:
        return {}
    mapping: dict[str, str | None] = {}
    for start in range(0, len(cleaned_ids), SQLITE_IN_MAX):
        batch = cleaned_ids[start : start + SQLITE_IN_MAX]
        placeholders = ",".join("?" for _ in batch)
        rows = con.execute(
            f"""
            SELECT hektor_offre_id, propositions_json
            FROM hektor.hektor_offre
            WHERE hektor_offre_id IN ({placeholders})
            """,
            batch,
        ).fetchall()
        for offre_id, propositions_json in rows:
            mapping[str(offre_id)] = derive_offer_last_proposition_type(propositions_json)
    return mapping


def enrich_offer_transaction_fields(con: sqlite3.Connection, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    offre_ids = [str(row.get("offre_id") or "").strip() for row in rows if str(row.get("offre_id") or "").strip()]
    offer_type_by_id = build_offer_last_proposition_type_by_id(con, offre_ids)
    enriched: list[dict[str, object]] = []
    for row in rows:
        next_row = dict(row)
        offre_id = str(row.get("offre_id") or "").strip()
        next_row["offre_last_proposition_type"] = offer_type_by_id.get(offre_id) if offre_id else None
        enriched.append(next_row)
    return enriched


def build_trimmed_detail_payload(row: dict[str, object]) -> dict[str, object]:
    detail_payload = {field: row.get(field, None) for field in DETAIL_PAYLOAD_FIELD_ORDER}
    detail_payload["images_json"] = trim_json_array_field(detail_payload.get("images_json"), limit=MAX_EXPORTED_IMAGES)
    detail_payload["images_preview_json"] = trim_json_array_field(
        detail_payload.get("images_preview_json"),
        limit=MAX_EXPORTED_IMAGES,
    )
    return detail_payload


def attach_detail_payload(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    enriched: list[dict[str, object]] = []
    for row in rows:
        next_row = dict(row)
        detail_payload = build_trimmed_detail_payload(row)
        for field in DETAIL_PAYLOAD_FIELD_ORDER:
            if field not in DOSSIER_KEEP_FIELDS:
                next_row.pop(field, None)
        next_row["photo_url_listing"] = detail_payload.get("photo_url_listing")
        enriched.append(next_row)
    return enriched


def build_dossier_details(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    details: list[dict[str, object]] = []
    for row in rows:
        detail_payload = build_trimmed_detail_payload(row)
        details.append(
            {
                "app_dossier_id": row["app_dossier_id"],
                "hektor_annonce_id": row["hektor_annonce_id"],
                "detail_payload_json": json.dumps(detail_payload, ensure_ascii=True, separators=(",", ":")),
            }
        )
    return details


def uniq_sorted(values: list[object]) -> list[str]:
    cleaned = sorted({str(value).strip() for value in values if value is not None and str(value).strip()}, key=lambda item: item.lower())
    return cleaned


def build_filter_catalog(dossiers: list[dict[str, object]], work_items: list[dict[str, object]]) -> list[dict[str, object]]:
    mapping = {
        "commercial": uniq_sorted([row.get("commercial_nom") for row in dossiers] + [row.get("commercial_nom") for row in work_items]),
        "diffusable": ['diffusable', 'non_diffusable'],
        "passerelle": uniq_sorted([
            item.strip()
            for row in dossiers
            for item in str(row.get("portails_resume") or "").split(",")
            if item.strip()
        ]),
        "erreur_diffusion": ["avec_erreur", "sans_erreur"],
        "priority": uniq_sorted([row.get("priority") for row in dossiers] + [row.get("priority") for row in work_items]),
        "work_status": uniq_sorted([row.get("work_status") for row in work_items]),
        "internal_status": uniq_sorted([row.get("internal_status") for row in work_items]),
    }
    rows: list[dict[str, object]] = []
    for filter_type, values in mapping.items():
        for sort_order, filter_value in enumerate(values, start=1):
            rows.append({
                "filter_type": filter_type,
                "filter_value": filter_value,
                "sort_order": sort_order,
            })
    return rows


def build_filter_catalog_from_db(con: sqlite3.Connection) -> list[dict[str, object]]:
    commercial_rows = fetch_rows(
        con,
        """
        SELECT commercial_nom
        FROM app_view_generale
        WHERE __ANNONCES_SCOPE_WHERE__
          AND NULLIF(TRIM(commercial_nom), '') IS NOT NULL
        UNION
        SELECT commercial_nom
        FROM app_view_demandes_mandat_diffusion
        WHERE app_dossier_id IN (
            SELECT app_dossier_id
            FROM app_view_generale
            WHERE __ANNONCES_SCOPE_WHERE__
        )
          AND NULLIF(TRIM(commercial_nom), '') IS NOT NULL
        """.replace("__ANNONCES_SCOPE_WHERE__", ANNONCES_SCOPE_WHERE),
    )
    priority_rows = fetch_rows(
        con,
        """
        SELECT priority
        FROM app_view_generale
        WHERE __ANNONCES_SCOPE_WHERE__
          AND NULLIF(TRIM(priority), '') IS NOT NULL
        UNION
        SELECT priority
        FROM app_view_demandes_mandat_diffusion
        WHERE app_dossier_id IN (
            SELECT app_dossier_id
            FROM app_view_generale
            WHERE __ANNONCES_SCOPE_WHERE__
        )
          AND NULLIF(TRIM(priority), '') IS NOT NULL
        """.replace("__ANNONCES_SCOPE_WHERE__", ANNONCES_SCOPE_WHERE),
    )
    work_status_rows = fetch_rows(
        con,
        """
        SELECT DISTINCT work_status
        FROM app_view_demandes_mandat_diffusion
        WHERE app_dossier_id IN (
            SELECT app_dossier_id
            FROM app_view_generale
            WHERE __ANNONCES_SCOPE_WHERE__
        )
          AND NULLIF(TRIM(work_status), '') IS NOT NULL
        """.replace("__ANNONCES_SCOPE_WHERE__", ANNONCES_SCOPE_WHERE),
    )
    internal_status_rows = fetch_rows(
        con,
        """
        SELECT DISTINCT internal_status
        FROM app_view_demandes_mandat_diffusion
        WHERE app_dossier_id IN (
            SELECT app_dossier_id
            FROM app_view_generale
            WHERE __ANNONCES_SCOPE_WHERE__
        )
          AND NULLIF(TRIM(internal_status), '') IS NOT NULL
        """.replace("__ANNONCES_SCOPE_WHERE__", ANNONCES_SCOPE_WHERE),
    )
    passerelle_rows = fetch_rows(
        con,
        """
        SELECT DISTINCT portails_resume
        FROM app_view_generale
        WHERE __ANNONCES_SCOPE_WHERE__
          AND NULLIF(TRIM(portails_resume), '') IS NOT NULL
        """.replace("__ANNONCES_SCOPE_WHERE__", ANNONCES_SCOPE_WHERE),
    )
    mapping = {
        "commercial": uniq_sorted([row.get("commercial_nom") for row in commercial_rows]),
        "diffusable": ["diffusable", "non_diffusable"],
        "passerelle": uniq_sorted(
            [
                item.strip()
                for row in passerelle_rows
                for item in str(row.get("portails_resume") or "").split(",")
                if item.strip()
            ]
        ),
        "erreur_diffusion": ["avec_erreur", "sans_erreur"],
        "priority": uniq_sorted([row.get("priority") for row in priority_rows]),
        "work_status": uniq_sorted([row.get("work_status") for row in work_status_rows]),
        "internal_status": uniq_sorted([row.get("internal_status") for row in internal_status_rows]),
    }
    rows: list[dict[str, object]] = []
    for filter_type, values in mapping.items():
        for sort_order, filter_value in enumerate(values, start=1):
            rows.append(
                {
                    "filter_type": filter_type,
                    "filter_value": filter_value,
                    "sort_order": sort_order,
                }
            )
    return rows


def build_payload(
    *,
    limit: int | None = 200,
    dossier_ids: list[int] | None = None,
    include_filter_catalog: bool = True,
) -> dict[str, object]:
    con = sqlite3.connect(PHASE2_DB)
    try:
        con.execute("ATTACH DATABASE ? AS hektor", (str(HEKTOR_DB),))
        summary_row = con.execute(SQL_SUMMARY).fetchone()
        summary_cols = [col[0] for col in con.execute(SQL_SUMMARY).description]
        dossier_rows = fetch_rows_by_ids(
            con,
            base_sql=SQL_DOSSIERS_BASE,
            id_column="app_dossier_id",
            ids=dossier_ids,
            limit=limit,
        )
        dossier_rows = enrich_offer_transaction_fields(con, dossier_rows)
        dossiers = attach_detail_payload(dossier_rows)
        dossier_details = build_dossier_details(dossier_rows)
        work_items = fetch_rows_by_ids(
            con,
            base_sql=SQL_WORK_ITEMS_BASE,
            id_column="app_dossier_id",
            ids=dossier_ids,
            limit=limit,
        )
        mandat_register_rows = build_mandat_register_rows(con, limit=limit)
        broadcasts = fetch_rows_by_ids(
            con,
            base_sql=SQL_BROADCASTS_BASE,
            id_column="app_dossier_id",
            ids=dossier_ids,
            limit=limit,
        )
        payload: dict[str, object] = {
            "meta": {
                "source": "phase2.sqlite",
                "contract": "app_payload_v1",
                "generated_from": "phase2/sync/export_app_payload.py",
                "row_limit": limit,
                "dossier_ids": dossier_ids,
            },
            "summary": dict(zip(summary_cols, summary_row)),
            "dossiers": dossiers,
            "dossier_details": dossier_details,
            "work_items": work_items,
            "mandat_register_rows": mandat_register_rows,
            "broadcasts": broadcasts,
            "filter_catalog": build_filter_catalog_from_db(con) if include_filter_catalog else build_filter_catalog(dossiers, work_items),
        }
    finally:
        try:
            con.execute("DETACH DATABASE hektor")
        except sqlite3.Error:
            pass
        con.close()

    return payload


def export_payload(*, limit: int | None = 200, output: Path = OUTPUT_JSON) -> Path:
    payload = build_payload(limit=limit)
    output.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="exporte toutes les lignes")
    parser.add_argument("--limit", type=int, default=200, help="nombre max de lignes par bloc")
    parser.add_argument("--output", type=Path, default=OUTPUT_JSON, help="fichier de sortie")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    limit = None if args.full else args.limit
    output = export_payload(limit=limit, output=args.output)
    print(output)


if __name__ == "__main__":
    main()
