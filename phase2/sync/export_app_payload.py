from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from datetime import datetime


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
    "mandat_type",
    "mandat_type_source",
    "mandat_date_debut",
    "mandat_date_fin",
    "mandat_montant",
    "mandants_texte",
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
