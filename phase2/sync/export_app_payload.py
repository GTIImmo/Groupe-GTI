from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path
from datetime import datetime
from collections import defaultdict


ROOT = Path(__file__).resolve().parent.parent.parent
PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
HEKTOR_DB = ROOT / "data" / "hektor.sqlite"
OUTPUT_JSON = ROOT / "phase2" / "docs" / "APP_PAYLOAD_V1_SAMPLE.json"
SQLITE_IN_MAX = 900
MAX_EXPORTED_IMAGES = 5
CURRENT_MANDATE_SERIES_START = "2024-01-01"
CURRENT_MANDATE_SERIES_MAX_NUM = 199999
DPE_IMAGE_BASE_URL = "https://groupe-gti-immobilier.staticlbi.com/wa/images/DPEImages/"
API_DETAIL_GROUP_PAYLOAD_FIELDS = {
    "ag_interieur": "ag_interieur_json",
    "ag_exterieur": "ag_exterieur_json",
    "equipements": "equipements_json",
    "diagnostiques": "diagnostiques_json",
    "terrain": "terrain_json",
    "copropriete": "copropriete_json",
    "mandat_infofi": "mandat_infofi_json",
    "mandat_mandatdispo": "mandat_mandatdispo_json",
    "organiser_visite": "organiser_visite_json",
}
CONSOLE_DETAIL_PAYLOAD_FIELDS = {
    "console_missing_fields_json",
    "console_missing_fields_extracted_at",
    "console_missing_fields_status",
    "chauffage_console_extracted_at",
    "secteur_console_json",
    "chauffage_console_json",
    "chauffage_console_status",
    "diagnostics_contacts_console_json",
    "honoraires_detail_console_json",
    "location_rendement_console_json",
    "pieces_detail_console_json",
    "dpe_image_url",
    "ges_image_url",
    "dpe_image_urls_json",
}
# C.15 26/08 -- QUELS TYPES D'OFFRE VONT VERS L'APP.
#
# Le run ne demandait a Hektor que les VENTES : ListAnnonces sans le parametre `offre` ne
# rend que offre=0. Resultat mesure le 26/08 : 4 165 annonces -- toutes les locations, tout
# l'immobilier professionnel, le neuf -- ne sont JAMAIS entrees dans le miroir.
#
# DECISION DE FREDERIC (26/08) : le SERVEUR recevra TOUS les types (il devient le maitre),
# mais SUPABASE, LE FRONT ET LES WORKERS n'en recoivent que trois :
#     0  vente              22 424 actives + 34 487 archivees
#     10 vente immo pro        251 actives +    782 archivees
#     6  neuf                    1 active
# Les locations (2 et 11) et le saisonnier (8) restent au serveur : 3 131 annonces qui
# n'apparaitront PAS dans l'app.
#
# POURQUOI CE FILTRE EST POSE AVANT D'OUVRIR LE ROBINET, et pourquoi c'est gratuit :
# aujourd'hui `offre_type` vaut 0 sur les 56 910 lignes du miroir, donc CE FILTRE N'EXCLUT
# RIEN. Il est totalement inerte. Une fois pose, on pourra ouvrir le run type par type sans
# qu'il existe UN SEUL INSTANT ou une location puisse atteindre Supabase. L'ordre inverse
# reviendrait a publier 3 131 locations dans l'app, puis a courir apres.
#
# COALESCE a '0' : trois annonces ont offre_type NULL (celles que Hektor ne rend plus, gardees
# avec absent_depuis). Elles etaient incluses avant, elles le restent.
TYPES_OFFRE_APP = ("0", "10", "6")
_LISTE_TYPES = ", ".join("'%s'" % code for code in TYPES_OFFRE_APP)

FILTRE_OFFRE_APP = "COALESCE(offre_type, '0') IN (%s)" % _LISTE_TYPES


def filtre_offre_app(alias: str) -> str:
    """Le meme filtre, mais qualifie par un alias de table.

    LOT A 27/08 -- LA FUITE DU REGISTRE. Le registre des mandats ne passe PAS par
    ANNONCES_SCOPE_WHERE : il lit `hektor.hektor_annonce` en direct, filtre seulement sur
    le statut. Sans cette fonction, les mandats des 3 131 locations remonteraient dans le
    registre LEGAL affiche par l'app, alors meme que leurs annonces en sont exclues.

    Trouve en verifiant la couverture du filtre, pas apres coup.

    La liste des types reste a UN SEUL endroit (TYPES_OFFRE_APP) : ajouter un type a l'app
    se fait la, et nulle part ailleurs.
    """
    return "COALESCE(%s.offre_type, '0') IN (%s)" % (alias, _LISTE_TYPES)

ANNONCES_SCOPE_WHERE = (
    "COALESCE(archive, '0') = '0' "
    "AND COALESCE(detail_statut_name, statut_annonce, '') IN ('Actif', 'Sous offre', 'Sous compromis', 'Estimation') "
    f"AND {FILTRE_OFFRE_APP}"
)
# "Estimation" ajoute le 21/07/2026. Le registre des mandats est un document legal :
# tout mandat signe doit y figurer, quel que soit le statut commercial de l'annonce.
# Or 139 annonces en statut Estimation portent un vrai mandat, avec ses deux dates
# (75 SIMPLE, 39 EXCLUSIF, 13 ACCORD, 12 sans type), du 2012 au 07/07/2026 -- elles
# etaient absentes du registre alors que le detail annonce les affichait.
# Le perimetre passe de 44 040 a 56 681 annonces balayees, mais n'ajoute que
# +139 lignes : les 12 502 estimations sans mandat n'en produisent aucune, la
# construction ne retenant que les annonces portant un mandat.
REGISTRE_SCOPE_STATUTS = ("Actif", "Sous offre", "Sous compromis", "Vendu", "Clos", "Estimation")
REGISTRE_SCOPE_SQL = ",".join(f"'{value}'" for value in REGISTRE_SCOPE_STATUTS)


def sqlite_read_connection(path: Path) -> sqlite3.Connection:
    uri = f"file:{path.resolve().as_posix()}?mode=ro&immutable=1"
    return sqlite3.connect(uri, uri=True)


def attach_hektor_read(con: sqlite3.Connection) -> None:
    uri = f"file:{HEKTOR_DB.resolve().as_posix()}?mode=ro&immutable=1"
    con.execute("ATTACH DATABASE ? AS hektor", (uri,))


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
    -- C.15 27/08 : LE BLOC COMMERCIAL. L'API REST ecrase les huit sous-types
    -- d'immobilier professionnel en un seul code (idtype 23, "Commerce") ; le vrai
    -- detail vient de GraphQL. Ces colonnes sont NULL pour toute annonce non
    -- commerciale. Colonnes posees dans Supabase AVANT ce push.
    commerce_sous_type,
    commerce_famille,
    commerce_activite,
    commerce_loyer,
    commerce_charges,
    commerce_taxe_fonciere,
    commerce_bail_duree,
    commerce_bail_echeance,
    commerce_etat,
    commerce_zone,
    commerce_json,
    app_dossier_id,
    hektor_annonce_id,
    -- C.15 27/08 : la NATURE de l'offre arrive jusqu'a l'app (0 vente, 6 neuf,
    -- 10 vente immo pro). Elle s'arretait au serveur ; au palier suivant, 251 biens
    -- d'immobilier professionnel entreront ici et seraient sinon indiscernables des
    -- 22 424 maisons et appartements. Colonne posee dans Supabase AVANT ce push.
    offre_type,
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
    COALESCE(detail_statut_name, statut_annonce) AS statut_annonce,
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
    ville_publique_detail,
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

# app_archive_annonce_index_current a pour cle hektor_annonce_id : il lui faut
# exactement une ligne par annonce. Or app_view_generale peut en porter plusieurs
# pour la meme annonce (fan-out de la jointure mandat sur la condition OR). Deux
# lignes de meme cle dans un meme lot font echouer l'upsert cote Postgres
# ("ON CONFLICT DO UPDATE command cannot affect row a second time"), ce qui
# interrompt tout le push. On ne retient donc que la ligne la plus recente.
SQL_ARCHIVE_ANNONCE_INDEX_BASE = """
WITH archive_ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY hektor_annonce_id
               ORDER BY COALESCE(date_maj, '') DESC,
                        CAST(app_dossier_id AS INTEGER) DESC
           ) AS archive_rn
    FROM app_view_generale
    WHERE COALESCE(archive, '0') = '1'
  AND __FILTRE_OFFRE_APP__
)
SELECT
    CAST(hektor_annonce_id AS INTEGER) AS hektor_annonce_id,
    CAST(app_dossier_id AS INTEGER) AS app_archive_id,
    -- C.15 27/08 : le sous-type commerce, pour l'index (badge et filtre).
    commerce_sous_type,
    commerce_famille,
    commerce_activite,
    -- C.15 27/08 : la NATURE de l'offre arrive jusqu'a l'app (0 vente, 6 neuf,
    -- 10 vente immo pro). Elle s'arretait au serveur ; au palier suivant, 251 biens
    -- d'immobilier professionnel entreront ici et seraient sinon indiscernables des
    -- 22 424 maisons et appartements. Colonne posee dans Supabase AVANT ce push.
    offre_type,
    numero_dossier,
    numero_mandat,
    titre_bien,
    ville,
    code_postal,
    type_bien,
    prix,
    commercial_id,
    commercial_nom,
    negociateur_email,
    agence_nom,
    COALESCE(detail_statut_name, statut_annonce) AS statut_annonce,
    archive,
    diffusable,
    date_maj,
    mandat_type,
    mandat_date_debut,
    mandat_date_fin,
    mandat_montant,
    CASE
        WHEN mandants_texte IS NULL THEN NULL
        WHEN length(mandants_texte) <= 240 THEN mandants_texte
        ELSE substr(mandants_texte, 1, 240) || '...'
    END AS mandants_texte,
    CASE WHEN detail_statut_name IS NOT NULL THEN 1 ELSE 0 END AS has_local_detail,
    NULL AS local_detail_updated_at,
    photo_url_listing
FROM archive_ranked
WHERE archive_rn = 1
ORDER BY
    COALESCE(date_maj, '') DESC,
    hektor_annonce_id DESC
"""

SQL_HISTORICAL_ANNONCE_INDEX_BASE = """
SELECT
    CAST(hektor_annonce_id AS INTEGER) AS hektor_annonce_id,
    CAST(app_dossier_id AS INTEGER) AS app_historical_id,
    -- C.15 27/08 : le sous-type commerce, pour l'index (badge et filtre).
    commerce_sous_type,
    commerce_famille,
    commerce_activite,
    -- C.15 27/08 : la NATURE de l'offre arrive jusqu'a l'app (0 vente, 6 neuf,
    -- 10 vente immo pro). Elle s'arretait au serveur ; au palier suivant, 251 biens
    -- d'immobilier professionnel entreront ici et seraient sinon indiscernables des
    -- 22 424 maisons et appartements. Colonne posee dans Supabase AVANT ce push.
    offre_type,
    numero_dossier,
    numero_mandat,
    titre_bien,
    ville,
    code_postal,
    type_bien,
    prix,
    commercial_id,
    commercial_nom,
    negociateur_email,
    agence_nom,
    COALESCE(detail_statut_name, statut_annonce) AS statut_annonce,
    archive,
    diffusable,
    date_maj,
    mandat_type,
    mandat_date_debut,
    mandat_date_fin,
    mandat_montant,
    CASE
        WHEN mandants_texte IS NULL THEN NULL
        WHEN length(mandants_texte) <= 240 THEN mandants_texte
        ELSE substr(mandants_texte, 1, 240) || '...'
    END AS mandants_texte,
    CASE WHEN detail_statut_name IS NOT NULL THEN 1 ELSE 0 END AS has_local_detail,
    NULL AS local_detail_updated_at,
    photo_url_listing
FROM app_view_generale
WHERE COALESCE(archive, '0') = '0'
  AND COALESCE(detail_statut_name, statut_annonce, '') IN ('Vendu', 'Clos')
  AND __FILTRE_OFFRE_APP__
ORDER BY
    COALESCE(date_maj, '') DESC,
    hektor_annonce_id DESC
"""


# --- Panier Brouillon (isDraft) : OFF par defaut, inerte tant que le drapeau n'est pas active ---
BROUILLON_BUCKET_ENABLED = os.environ.get("APP_BROUILLON_BUCKET_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


def brouillon_active_exclusion_sql() -> str:
    """Clause SQL (a concatener au scope actif) qui exclut les brouillons isDraft.
    Vide si le drapeau est OFF -> aucun changement. Suppose `hektor` attache."""
    if not BROUILLON_BUCKET_ENABLED:
        return ""
    return (
        " AND CAST(hektor_annonce_id AS TEXT) NOT IN "
        "(SELECT CAST(hektor_annonce_id AS TEXT) FROM hektor.hektor_annonce_draft_state "
        "WHERE COALESCE(is_draft, 0) = 1)"
    )

# Index brouillon = clone du patron Vendu/Clos, mais filtre par les ids presents dans
# hektor.hektor_annonce_draft_state (is_draft=1), injectes en Python (pas de cross-db dans le SQL).
SQL_BROUILLON_ANNONCE_INDEX_BASE = """
SELECT
    CAST(hektor_annonce_id AS INTEGER) AS hektor_annonce_id,
    CAST(app_dossier_id AS INTEGER) AS app_brouillon_id,
    numero_dossier,
    numero_mandat,
    titre_bien,
    ville,
    code_postal,
    type_bien,
    prix,
    commercial_id,
    commercial_nom,
    negociateur_email,
    agence_nom,
    COALESCE(detail_statut_name, statut_annonce) AS statut_annonce,
    archive,
    diffusable,
    date_maj,
    mandat_type,
    mandat_date_debut,
    mandat_date_fin,
    mandat_montant,
    CASE
        WHEN mandants_texte IS NULL THEN NULL
        WHEN length(mandants_texte) <= 240 THEN mandants_texte
        ELSE substr(mandants_texte, 1, 240) || '...'
    END AS mandants_texte,
    CASE WHEN detail_statut_name IS NOT NULL THEN 1 ELSE 0 END AS has_local_detail,
    NULL AS local_detail_updated_at,
    photo_url_listing
FROM app_view_generale
WHERE COALESCE(archive, '0') = '0'
  AND CAST(hektor_annonce_id AS INTEGER) IN (__BROUILLON_IDS__)
  AND __FILTRE_OFFRE_APP__
ORDER BY
    COALESCE(date_maj, '') DESC,
    hektor_annonce_id DESC
"""

# C.15 26/08 -- LA REGLE EST ECRITE UNE FOIS, APPLIQUEE PARTOUT.
# Les trois requetes ci-dessus portent le marqueur __FILTRE_OFFRE_APP__ ; on le remplace ici
# par FILTRE_OFFRE_APP, defini en tete. Ainsi la liste des types qui vont vers l'app n'existe
# qu'a UN endroit : la changer, c'est la changer partout.
SQL_ARCHIVE_ANNONCE_INDEX_BASE = SQL_ARCHIVE_ANNONCE_INDEX_BASE.replace(
    "__FILTRE_OFFRE_APP__", FILTRE_OFFRE_APP)
SQL_HISTORICAL_ANNONCE_INDEX_BASE = SQL_HISTORICAL_ANNONCE_INDEX_BASE.replace(
    "__FILTRE_OFFRE_APP__", FILTRE_OFFRE_APP)
SQL_BROUILLON_ANNONCE_INDEX_BASE = SQL_BROUILLON_ANNONCE_INDEX_BASE.replace(
    "__FILTRE_OFFRE_APP__", FILTRE_OFFRE_APP)



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
    "price_change_event_count",
    "price_change_last_source_kind",
    "price_change_last_old_value",
    "price_change_last_new_value",
    "price_change_last_detected_at",
    "price_change_last_source_updated_at",
    "price_change_events_json",
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
    "ag_interieur_json",
    "ag_exterieur_json",
    "equipements_json",
    "diagnostiques_json",
    "terrain_json",
    "copropriete_json",
    "mandat_infofi_json",
    "mandat_mandatdispo_json",
    "organiser_visite_json",
    "console_missing_fields_json",
    "console_missing_fields_extracted_at",
    "console_missing_fields_status",
    "chauffage_console_extracted_at",
    "secteur_console_json",
    "chauffage_console_json",
    "chauffage_console_status",
    "diagnostics_contacts_console_json",
    "honoraires_detail_console_json",
    "location_rendement_console_json",
    "pieces_detail_console_json",
    "dpe_image_url",
    "ges_image_url",
    "dpe_image_urls_json",
    "detail_raw_json",
    "annonce_list_raw_json",
    "code_postal_detail",
    "ville_publique_detail",
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
    "date_enregistrement_annonce",
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
    "price_change_event_count",
    "price_change_last_source_kind",
    "price_change_last_old_value",
    "price_change_last_new_value",
    "price_change_last_detected_at",
    "price_change_last_source_updated_at",
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


FILTRE_REGISTRE = filtre_offre_app("ann")
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
    neg.email AS negociateur_email,
    -- C.15 27/08 : le registre affiche le type de bien. Hektor renvoie "Commerce"
    -- pour les huit sous-types immo pro ; le vrai libelle vient de la console.
    com.sous_type_label AS commerce_sous_type
FROM hektor.hektor_annonce ann
LEFT JOIN hektor.hektor_annonce_detail det
    ON det.hektor_annonce_id = ann.hektor_annonce_id
LEFT JOIN hektor.hektor_annonce_commercial com
    ON CAST(com.hektor_annonce_id AS TEXT) = CAST(ann.hektor_annonce_id AS TEXT)
LEFT JOIN hektor.hektor_agence ag
    ON ag.hektor_agence_id = ann.hektor_agence_id
LEFT JOIN hektor.hektor_negociateur neg
    ON neg.hektor_negociateur_id = ann.hektor_negociateur_id
WHERE COALESCE(det.statut_name, '') IN ({REGISTRE_SCOPE_SQL})
  -- LOT A 27/08 : le registre lit hektor_annonce EN DIRECT, il ne passe pas par
  -- ANNONCES_SCOPE_WHERE. Sans cette ligne, les mandats des locations remonteraient
  -- dans le registre legal de l'app.
  AND {FILTRE_REGISTRE}
ORDER BY CAST(ann.hektor_annonce_id AS INTEGER), ann.no_mandat
"""


# ═══════════════════════════════════════════════════════════════════════════════
# A.3-tech etape C -- LE REGISTRE PREND SES COLONNES DE MANDAT DANS app_mandat
# ═══════════════════════════════════════════════════════════════════════════════
# 30/09/2026. DERRIERE UN INTERRUPTEUR, et par defaut ETEINT tant que la
# comparaison des deux constructions n'a pas ete faite sur les donnees reelles.
#
#     APP_REGISTRE_DEPUIS_APP_MANDAT=1    le registre lit app_mandat
#     (absent ou 0)                       comportement d'avant, inchange
#
# ─── CE QUE CELA CHANGE, ET POURQUOI ───────────────────────────────────────────
# La vue `app_registre_mandats_current` N'EST PAS TOUCHEE : elle lit UNE table et
# ne sait pas d'ou vient la donnee. Ses 70 colonnes, ses 4 fonctions cote front
# (loadMandatRegisterPage, loadMandatRegisterStats, loadMandatFilterCatalog,
# loadRegisterCycleAffaires) ne changent pas d'une ligne. On change seulement
# l'endroit ou le FABRICANT va chercher la matiere.
#
# ─── LE GAIN MESURE : 453 MANDATS ──────────────────────────────────────────────
# Le fabricant filtre sur le STATUT de l'annonce :
#     WHERE COALESCE(det.statut_name,'') IN ('Actif','Sous offre','Sous compromis',
#                                            'Vendu','Clos','Estimation')
# Une annonce SANS DETAIL (statut '') ou dans un autre statut sort du registre
# AVEC SON MANDAT. Mesure du 30/09 : 453 mandats de vente manquants, dont
#     371  le numero est porte par l'annonce (no_mandat) sans fiche
#      82  l'annonce n'est meme pas LUE par la requete
# Et le fichier porte deja la phrase qui condamne ce filtre, ecrite le 21/07
# quand « Estimation » a du etre ajoute a la liste :
#     « Le registre des mandats est un document legal : tout mandat signe doit y
#       figurer, quel que soit le statut commercial de l'annonce. »
# Ajouter un statut de plus ne reglait qu'un cas ; lire app_mandat les regle tous,
# parce que la table, elle, ne perd jamais une ligne.
#
# ⚠ LE FILTRE DES TYPES D'OFFRE RESTE, ET IL EST INDISPENSABLE. app_mandat porte
#   TOUT (26 826 lignes, locations comprises) ; le registre n'admet que 0, 10 et
#   6 -- decision du 26/08. Sans ce filtre on ferait entrer 2 348 locations dans
#   un registre qui les exclut.
#
# ⚠ ON NE TOUCHE PAS AU FILTRE `archive`, NI A LA PORTEE DES 57 COLONNES
#   D'ANNONCE : elles continuent de venir d'ou elles venaient.
# ═══════════════════════════════════════════════════════════════════════════════
# ⭐ ALLUME PAR DEFAUT LE 30/09, APRES LA COMPARAISON DES DEUX CONSTRUCTIONS SUR
#   LES DONNEES REELLES : +453 lignes, 0 PERDUE, et les seules colonnes qui
#   bougent sur les 24 025 lignes communes sont celles ou « 0 EUR » devient vide
#   (171 montants, 189 historiques, 189 details -- la meme regle, trois fois).
#   Aucune identite, aucune version, aucun tri ne change.
# RETOUR ARRIERE : APP_REGISTRE_DEPUIS_APP_MANDAT=0 dans l'environnement du run.
REGISTRE_DEPUIS_APP_MANDAT = os.environ.get("APP_REGISTRE_DEPUIS_APP_MANDAT", "1") == "1"

# Les seuls types d'offre que le registre de l'app admet (decision du 26/08).
TYPES_ADMIS_AU_REGISTRE = ("0", "10", "6")

# Le meme socle, mais la porte n'est plus le statut : c'est « cette annonce
# porte-t-elle un mandat au registre ? ». On lit donc exactement les annonces
# dont app_mandat a besoin, ni plus ni moins.
SQL_REGISTER_RAW_DEPUIS_APP_MANDAT = SQL_REGISTER_RAW_BASE.replace(
    f"WHERE COALESCE(det.statut_name, '') IN ({REGISTRE_SCOPE_SQL})",
    "WHERE CAST(ann.hektor_annonce_id AS TEXT) IN ("
    "      SELECT hektor_annonce_id FROM app_mandat"
    "       WHERE COALESCE(offre_type,'') IN ("
    + ",".join("'%s'" % t for t in TYPES_ADMIS_AU_REGISTRE) + "))",
)


def charger_mandats_depuis_app_mandat(
    con: sqlite3.Connection, annonces: set[str] | None = None
) -> dict[str, dict[str, list[dict[str, object]]]]:
    """LE REGISTRE, TEL QUE app_mandat LE PORTE : {annonce: {numero: [versions]}}.

    Les versions sortent de `versions_json`, deja triees LA MEILLEURE EN TETE par
    compute_mandat_version_score -- la formule du registre, importee par
    mandat_ledger.py et non recopiee. Le tri est refait plus bas de toute facon :
    il est idempotent, et le refaire coute moins que de supposer.

    ⚠ UNE LIGNE SANS VERSION N'EST PAS UNE LIGNE VIDE. Les numeros emis dont
      aucune fiche n'est redescendue (origine 'annonce', 2 072 le 30/09) portent
      une version de repli ne contenant que le numero -- exactement ce que le
      fabricant fabriquait lui-meme quand `mandats_json` etait vide. On la
      refabrique ici si elle manque, plutot que de perdre la ligne.
    """
    par_annonce: dict[str, dict[str, list[dict[str, object]]]] = defaultdict(dict)
    places = ",".join("'%s'" % t for t in TYPES_ADMIS_AU_REGISTRE)
    for ligne in con.execute(
        "SELECT hektor_annonce_id, numero_mandat, versions_json FROM app_mandat"
        f" WHERE COALESCE(offre_type,'') IN ({places})"
    ):
        annonce = normalize_text(ligne[0])
        numero = normalize_text(ligne[1])
        if not annonce or not numero:
            continue
        if annonces is not None and annonce not in annonces:
            continue
        versions = safe_json_loads(ligne[2], [])
        if not isinstance(versions, list):
            versions = []
        versions = [v for v in versions if isinstance(v, dict)]
        if not versions:
            versions = [{
                "id": None, "numero": numero, "type": None, "debut": None,
                "fin": None, "cloture": None, "montant": None, "mandants": None,
                "note": None, "avenants": [],
            }]
        par_annonce[annonce][numero] = versions
    return par_annonce


SQL_REGISTER_BROADCAST_AGG = """
SELECT
    s.hektor_annonce_id,
    SUM(CASE WHEN s.current_state = 'broadcasted' THEN 1 ELSE 0 END) AS nb_portails_actifs,
    MAX(CASE WHEN s.is_error = 1 THEN 1 ELSE 0 END) AS has_diffusion_error,
    GROUP_CONCAT(CASE WHEN s.current_state = 'broadcasted' THEN s.passerelle_key END, ', ') AS portails_resume
FROM hektor.hektor_annonce_broadcast_state s
GROUP BY s.hektor_annonce_id
"""


# Lot B (vision par cycle) : meilleure affaire (offre/compromis/vente) PAR (annonce, mandat).
# Les affaires portent deja leur hektor_mandat_id ; ici on les groupe par cycle au lieu de
# n'en garder qu'une par annonce (comme build_case_index). Cle fiable = (annonce, mandat) car
# Hektor recycle ses ids de mandat entre annonces.
SQL_MANDAT_AFFAIRES = """
WITH offre_ranked AS (
    SELECT hektor_annonce_id, hektor_mandat_id, hektor_offre_id, offre_state,
        raw_montant, offre_event_date, hektor_acquereur_id, acquereur_json,
        ROW_NUMBER() OVER (
            PARTITION BY hektor_annonce_id, hektor_mandat_id
            ORDER BY CASE offre_state WHEN 'accepted' THEN 0 WHEN 'proposed' THEN 1 ELSE 2 END,
                     COALESCE(offre_event_date, raw_date, synced_at) DESC
        ) AS rn
    FROM hektor.hektor_offre
    WHERE hektor_annonce_id IS NOT NULL AND COALESCE(NULLIF(hektor_mandat_id, ''), '0') <> '0'
),
compromis_ranked AS (
    SELECT hektor_annonce_id, hektor_mandat_id, hektor_compromis_id, compromis_state,
        date_start, date_signature_acte, sequestre, prix_net_vendeur, prix_publique,
        mandants_json, acquereurs_json,
        ROW_NUMBER() OVER (
            PARTITION BY hektor_annonce_id, hektor_mandat_id
            ORDER BY CASE compromis_state WHEN 'active' THEN 0 WHEN 'cancelled' THEN 1 ELSE 2 END,
                     COALESCE(date_start, synced_at) DESC
        ) AS rn
    FROM hektor.hektor_compromis
    WHERE hektor_annonce_id IS NOT NULL AND COALESCE(NULLIF(hektor_mandat_id, ''), '0') <> '0'
),
vente_ranked AS (
    SELECT hektor_annonce_id, hektor_mandat_id, hektor_vente_id, date_vente,
        prix, honoraires, commission_agence, mandants_json, acquereurs_json, notaires_json,
        ROW_NUMBER() OVER (
            PARTITION BY hektor_annonce_id, hektor_mandat_id
            ORDER BY COALESCE(date_vente, synced_at) DESC
        ) AS rn
    FROM hektor.hektor_vente
    WHERE hektor_annonce_id IS NOT NULL AND COALESCE(NULLIF(hektor_mandat_id, ''), '0') <> '0'
),
keys AS (
    SELECT hektor_annonce_id, hektor_mandat_id FROM offre_ranked WHERE rn = 1
    UNION SELECT hektor_annonce_id, hektor_mandat_id FROM compromis_ranked WHERE rn = 1
    UNION SELECT hektor_annonce_id, hektor_mandat_id FROM vente_ranked WHERE rn = 1
)
SELECT
    k.hektor_annonce_id,
    k.hektor_mandat_id,
    o.hektor_offre_id AS offre_id, o.offre_state AS offre_state,
    o.raw_montant AS offre_montant, o.offre_event_date AS offre_date,
    o.acquereur_json AS offre_acquereur_json,
    c.hektor_compromis_id AS compromis_id, c.compromis_state AS compromis_state,
    c.date_start AS compromis_date_start, c.date_signature_acte AS compromis_date_acte,
    c.sequestre AS compromis_sequestre, c.prix_net_vendeur AS compromis_prix_net,
    c.prix_publique AS compromis_prix_public,
    c.mandants_json AS compromis_mandants_json, c.acquereurs_json AS compromis_acquereurs_json,
    v.hektor_vente_id AS vente_id, v.date_vente AS vente_date,
    v.prix AS vente_prix, v.honoraires AS vente_honoraires, v.commission_agence AS vente_commission,
    v.mandants_json AS vente_mandants_json, v.acquereurs_json AS vente_acquereurs_json,
    v.notaires_json AS vente_notaires_json
FROM keys k
LEFT JOIN offre_ranked o ON o.hektor_annonce_id = k.hektor_annonce_id AND o.hektor_mandat_id = k.hektor_mandat_id AND o.rn = 1
LEFT JOIN compromis_ranked c ON c.hektor_annonce_id = k.hektor_annonce_id AND c.hektor_mandat_id = k.hektor_mandat_id AND c.rn = 1
LEFT JOIN vente_ranked v ON v.hektor_annonce_id = k.hektor_annonce_id AND v.hektor_mandat_id = k.hektor_mandat_id AND v.rn = 1
"""


def _compact_party(obj: object) -> dict[str, object] | None:
    """Contact compact d'une partie d'affaire (embarque en local, pas de jointure Supabase)."""
    if isinstance(obj, str):
        obj = safe_json_loads(obj, None)
    if isinstance(obj, list):
        obj = obj[0] if obj else None
    if not isinstance(obj, dict):
        return None
    coord = obj.get("coordonnees") if isinstance(obj.get("coordonnees"), (dict, list)) else None
    party = {
        "id": normalize_text(obj.get("id")) or None,
        "civilite": normalize_text(obj.get("civilite")) or None,
        "nom": normalize_text(obj.get("nom")) or None,
        "prenom": normalize_text(obj.get("prenom")) or None,
        "coordonnees": coord,
    }
    return party if (party["id"] or party["nom"]) else None


def build_affaire_detail_for_cycle(row: dict[str, object]) -> dict[str, object] | None:
    """Detail complet de l'affaire d'un cycle (financiers + parties), pour la rubrique
    Affaires/Contacts du cockpit re-scopee par cycle. Tout vient des tables locales."""
    detail: dict[str, object] = {}
    if normalize_text(row.get("offre_id")):
        detail["offre"] = {
            "id": normalize_text(row.get("offre_id")) or None,
            "state": normalize_text(row.get("offre_state")) or None,
            "montant": normalize_text(row.get("offre_montant")) or None,
            "date": normalize_text(row.get("offre_date")) or None,
            "acquereur": _compact_party(row.get("offre_acquereur_json")),
        }
    if normalize_text(row.get("compromis_id")):
        detail["compromis"] = {
            "id": normalize_text(row.get("compromis_id")) or None,
            "state": normalize_text(row.get("compromis_state")) or None,
            "date_start": normalize_text(row.get("compromis_date_start")) or None,
            "date_acte": normalize_text(row.get("compromis_date_acte")) or None,
            "sequestre": normalize_text(row.get("compromis_sequestre")) or None,
            "prix_net": normalize_text(row.get("compromis_prix_net")) or None,
            "prix_public": normalize_text(row.get("compromis_prix_public")) or None,
            "acquereur": _compact_party(row.get("compromis_acquereurs_json")),
            "mandant": _compact_party(row.get("compromis_mandants_json")),
        }
    if normalize_text(row.get("vente_id")):
        detail["vente"] = {
            "id": normalize_text(row.get("vente_id")) or None,
            "date": normalize_text(row.get("vente_date")) or None,
            "prix": normalize_text(row.get("vente_prix")) or None,
            "honoraires": normalize_text(row.get("vente_honoraires")) or None,
            "commission": normalize_text(row.get("vente_commission")) or None,
            "acquereur": _compact_party(row.get("vente_acquereurs_json")),
            "mandant": _compact_party(row.get("vente_mandants_json")),
            "notaire": _compact_party(row.get("vente_notaires_json")),
        }
    return detail or None


# Toutes les affaires d'un cycle SANS collapse rn=1 : sert a lister les DOSSIERS par acquereur
# (affaire courante vs dossiers abandonnes). Etat offre = offre_state (derive du dernier evenement
# de propositions_json par normalize_source) ; compromis = compromis_state ; vente = definitif.
SQL_MANDAT_AFFAIRES_ALL = """
SELECT hektor_annonce_id, hektor_mandat_id, 'offre' AS kind, hektor_offre_id AS id,
       offre_state AS state, hektor_acquereur_id AS acq_id, acquereur_json AS acq_json,
       raw_montant AS montant, COALESCE(offre_event_date, raw_date, synced_at) AS dt,
       NULL AS date_acte, NULL AS sequestre
FROM hektor.hektor_offre
WHERE hektor_annonce_id IS NOT NULL
UNION ALL
SELECT hektor_annonce_id, hektor_mandat_id, 'compromis', hektor_compromis_id,
       compromis_state, NULL, acquereurs_json,
       COALESCE(prix_publique, prix_net_vendeur), COALESCE(date_start, synced_at),
       date_signature_acte, sequestre
FROM hektor.hektor_compromis
WHERE hektor_annonce_id IS NOT NULL
UNION ALL
SELECT hektor_annonce_id, hektor_mandat_id, 'vente', hektor_vente_id,
       NULL, NULL, acquereurs_json,
       prix, COALESCE(date_vente, synced_at),
       NULL, NULL
FROM hektor.hektor_vente
WHERE hektor_annonce_id IS NOT NULL
"""

_DOSSIER_STATE_RANK = {"vendu": 0, "compromis": 1, "offre_acceptee": 2, "offre_en_cours": 3, "compromis_annule": 4, "offre_refusee": 5}
_DOSSIER_STATE_LABEL = {
    "vendu": "Vendu", "compromis": "Compromis", "offre_acceptee": "Offre acceptée",
    "offre_en_cours": "Offre en cours", "compromis_annule": "Compromis annulé", "offre_refusee": "Offre refusée",
}
_DOSSIER_LIVE = {"vendu", "compromis", "offre_acceptee", "offre_en_cours"}


def _dossier_state(kind: str, state: object) -> str:
    s = normalize_text(state).lower()
    if kind == "vente":
        return "vendu"
    if kind == "compromis":
        return "compromis_annule" if s == "cancelled" else "compromis"
    if s == "accepted":
        return "offre_acceptee"
    if s == "refused":
        return "offre_refusee"
    return "offre_en_cours"


# Au sein d'un type d'affaire, on garde l'occurrence la PLUS AVANCEE (offre acceptee > proposee >
# refusee ; compromis actif > annule). Rang bas = a garder.
_OFFRE_LEG_RANK = {"accepted": 0, "acceptee": 0, "proposed": 1, "en_cours": 1, "": 2, "refused": 3, "refusee": 3}
_COMPROMIS_LEG_RANK = {"active": 0, "": 1, "cancelled": 2, "annule": 2}


def _leg_rank(kind: str, leg: dict[str, object]) -> int:
    s = normalize_text(leg.get("state")).lower()
    if kind == "offre":
        return _OFFRE_LEG_RANK.get(s, 2)
    if kind == "compromis":
        return _COMPROMIS_LEG_RANK.get(s, 1)
    return 0


def build_affaires_dossiers(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Un DOSSIER par acquereur du cycle, portant la CHAINE COMPLETE de ses affaires
    (offre + compromis + vente), classe par l'etape la PLUS AVANCEE atteinte. Ainsi la trace
    de l'offre n'est jamais perdue quand le compromis est annule.
    Une offre refusee (sans suite) ou un compromis annule (etape la plus avancee) => abandonne."""
    by_acq: dict[str, dict[str, object]] = {}
    for r in rows:
        kind = normalize_text(r.get("kind"))
        if kind not in ("offre", "compromis", "vente"):
            continue
        party = _compact_party(r.get("acq_json"))
        acq_id = normalize_text(r.get("acq_id")) or (normalize_text(party.get("id")) if party else "")
        if not acq_id and not party:
            continue
        key = acq_id or f"{kind}:{normalize_text(r.get('id'))}"
        d = by_acq.setdefault(key, {"acquereur": party, "offre": None, "compromis": None, "vente": None, "_mandats": set()})
        if party and not d.get("acquereur"):
            d["acquereur"] = party
        mid = normalize_text(r.get("hektor_mandat_id"))
        # seuls compromis/vente portent un mandat fiable (offres ~98% a 0) : sert a affecter le
        # dossier au bon cycle sur les rares annonces multi-mandats.
        if mid and mid != "0" and kind in ("compromis", "vente"):
            d["_mandats"].add(mid)  # type: ignore[union-attr]
        dropped = bool(r.get("_dropped"))
        leg: dict[str, object] = {
            "montant": normalize_text(r.get("montant")) or None,
            "date": normalize_text(r.get("dt")) or None,
            "state": normalize_text(r.get("state")) or None,
        }
        if kind == "compromis":
            leg["date_acte"] = normalize_text(r.get("date_acte")) or None
            leg["sequestre"] = normalize_text(r.get("sequestre")) or None
        if dropped:
            # B+ : affaire conservee par le ledger mais plus dans Hektor.
            leg["dropped"] = True
            leg["dropped_since"] = normalize_text(r.get("_last_seen")) or None
        existing = d.get(kind)
        # Priorite a la version PRESENTE (Hektor live) sur une version disparue (ledger) ; a defaut,
        # l'occurrence la plus avancee.
        old_dropped = bool(existing.get("dropped")) if isinstance(existing, dict) else False
        if existing is None or (old_dropped and not dropped) or (
            old_dropped == dropped and _leg_rank(kind, leg) < _leg_rank(kind, existing)  # type: ignore[arg-type]
        ):
            d[kind] = leg
    dossiers: list[dict[str, object]] = []
    for d in by_acq.values():
        offre, compromis, vente = d.get("offre"), d.get("compromis"), d.get("vente")
        if not (offre or compromis or vente):
            continue
        if vente:
            etat = "vendu"
        elif compromis:
            etat = "compromis_annule" if normalize_text(compromis.get("state")).lower() in ("cancelled", "annule") else "compromis"  # type: ignore[union-attr]
        else:
            s = normalize_text(offre.get("state")).lower()  # type: ignore[union-attr]
            etat = "offre_acceptee" if s in ("accepted", "acceptee") else ("offre_refusee" if s in ("refused", "refusee") else "offre_en_cours")
        dossiers.append({
            "acquereur": d.get("acquereur"),
            "etat": etat,
            "etat_label": _DOSSIER_STATE_LABEL[etat],
            "courante": etat in _DOSSIER_LIVE,
            "offre": offre,
            "compromis": compromis,
            "vente": vente,
            "_rank": _DOSSIER_STATE_RANK[etat],
            "_mandats": d.get("_mandats") or set(),
        })
    dossiers.sort(key=lambda d: (0 if d["courante"] else 1, int(d["_rank"])))
    for d in dossiers:
        d.pop("_rank", None)
    return dossiers


def build_cycle_affaire_blob(row: dict[str, object] | None, dossiers: list[dict[str, object]]) -> str | None:
    """Blob affaires_detail_json enrichi : detail de l'affaire courante (rn=1) + liste des dossiers
    par acquereur (courant + abandonnes, deja construits/affectes au cycle). Un seul blob."""
    detail = build_affaire_detail_for_cycle(row) if row else None
    detail = dict(detail) if detail else {}
    if dossiers:
        detail["dossiers"] = dossiers
    return json.dumps(detail, ensure_ascii=True, separators=(",", ":")) if detail else None


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


def build_price_change_by_annonce(
    con: sqlite3.Connection,
    annonce_ids: list[object],
) -> dict[str, dict[str, object]]:
    cleaned_ids = sorted({str(value or "").strip() for value in annonce_ids if str(value or "").strip()})
    if not cleaned_ids:
        return {}
    output: dict[str, dict[str, object]] = {}
    for start in range(0, len(cleaned_ids), SQLITE_IN_MAX):
        batch = cleaned_ids[start : start + SQLITE_IN_MAX]
        placeholders = ",".join("?" for _ in batch)
        try:
            rows = con.execute(
                f"""
                SELECT
                    hektor_annonce_id,
                    hektor_mandat_id,
                    numero_mandat,
                    source_kind,
                    old_value,
                    new_value,
                    source_updated_at,
                    detected_at
                FROM hektor.hektor_price_change_event
                WHERE hektor_annonce_id IN ({placeholders})
                ORDER BY COALESCE(source_updated_at, detected_at) DESC, detected_at DESC, event_key DESC
                """,
                batch,
            ).fetchall()
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc).lower():
                return {}
            raise
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            annonce_id = str(row[0] or "").strip()
            if not annonce_id:
                continue
            grouped[annonce_id].append(
                {
                    "hektor_mandat_id": row[1],
                    "numero_mandat": row[2],
                    "source_kind": row[3],
                    "old_value": row[4],
                    "new_value": row[5],
                    "source_updated_at": row[6],
                    "detected_at": row[7],
                }
            )
        for annonce_id, events in grouped.items():
            latest = events[0] if events else {}
            output[annonce_id] = {
                "price_change_event_count": len(events),
                "price_change_last_source_kind": latest.get("source_kind"),
                "price_change_last_old_value": latest.get("old_value"),
                "price_change_last_new_value": latest.get("new_value"),
                "price_change_last_detected_at": latest.get("detected_at"),
                "price_change_last_source_updated_at": latest.get("source_updated_at"),
                "price_change_events_json": json.dumps(events[:20], ensure_ascii=True, separators=(",", ":")),
            }
    return output


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


def compact_json_field(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        raw = value.strip()
        if not raw or raw == "null":
            return None
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            return raw
        return json.dumps(parsed, ensure_ascii=True, separators=(",", ":")) if parsed is not None else None
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def extract_api_detail_groups(detail_raw_json: object) -> dict[str, str | None]:
    raw_detail = safe_json_loads(detail_raw_json, {})
    if not isinstance(raw_detail, dict):
        return {field: None for field in API_DETAIL_GROUP_PAYLOAD_FIELDS.values()}
    return {
        payload_field: compact_json_field(raw_detail.get(group_name))
        for group_name, payload_field in API_DETAIL_GROUP_PAYLOAD_FIELDS.items()
    }


def build_console_detail_by_annonce(
    con: sqlite3.Connection,
    annonce_ids: list[object],
) -> dict[str, dict[str, object]]:
    cleaned_ids = sorted({str(value or "").strip() for value in annonce_ids if str(value or "").strip()})
    if not cleaned_ids:
        return {}
    output: dict[str, dict[str, object]] = {}
    for start in range(0, len(cleaned_ids), SQLITE_IN_MAX):
        batch = cleaned_ids[start : start + SQLITE_IN_MAX]
        placeholders = ",".join("?" for _ in batch)
        try:
            rows = con.execute(
                f"""
                SELECT
                    hektor_annonce_id,
                    status,
                    console_payload_json,
                    extracted_at
                FROM hektor.hektor_annonce_console_detail
                WHERE hektor_annonce_id IN ({placeholders})
                """,
                batch,
            ).fetchall()
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc).lower():
                return {}
            raise
        for hektor_annonce_id, status, payload_json, extracted_at in rows:
            annonce_id = str(hektor_annonce_id or "").strip()
            if not annonce_id:
                continue
            payload = safe_json_loads(payload_json, {})
            if not isinstance(payload, dict):
                payload = {}
            output[annonce_id] = {
                "status": status,
                "payload": payload,
                "extracted_at": extracted_at,
            }
    return output


def build_chauffage_detail_by_annonce(
    con: sqlite3.Connection,
    annonce_ids: list[object],
) -> dict[str, dict[str, object]]:
    cleaned_ids = sorted({str(value or "").strip() for value in annonce_ids if str(value or "").strip()})
    if not cleaned_ids:
        return {}
    output: dict[str, dict[str, object]] = {}
    for start in range(0, len(cleaned_ids), SQLITE_IN_MAX):
        batch = cleaned_ids[start : start + SQLITE_IN_MAX]
        placeholders = ",".join("?" for _ in batch)
        try:
            rows = con.execute(
                f"""
                SELECT
                    hektor_annonce_id,
                    status,
                    chauffage_json,
                    extracted_at
                FROM hektor.hektor_annonce_chauffage_detail
                WHERE hektor_annonce_id IN ({placeholders})
                """,
                batch,
            ).fetchall()
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc).lower():
                return {}
            raise
        for hektor_annonce_id, status, chauffage_json, extracted_at in rows:
            annonce_id = str(hektor_annonce_id or "").strip()
            if not annonce_id:
                continue
            chauffage = safe_json_loads(chauffage_json, None)
            output[annonce_id] = {
                "status": status,
                "chauffage": chauffage,
                "extracted_at": extracted_at,
            }
    return output


def attach_console_missing_fields(con: sqlite3.Connection, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    console_by_annonce = build_console_detail_by_annonce(con, [row.get("hektor_annonce_id") for row in rows])
    chauffage_by_annonce = build_chauffage_detail_by_annonce(con, [row.get("hektor_annonce_id") for row in rows])
    enriched: list[dict[str, object]] = []
    json_keys = {
        "secteur_console_json": "secteur_console_json",
        "chauffage_console_json": "chauffage_console_json",
        "diagnostics_contacts_console_json": "diagnostics_contacts_console_json",
        "honoraires_detail_console_json": "honoraires_detail_console_json",
        "location_rendement_console_json": "location_rendement_console_json",
        "pieces_detail_console_json": "pieces_detail_console_json",
        "dpe_image_urls_json": "dpe_image_urls",
    }
    for row in rows:
        next_row = dict(row)
        for field in CONSOLE_DETAIL_PAYLOAD_FIELDS:
            next_row.setdefault(field, None)
        console_detail = console_by_annonce.get(str(row.get("hektor_annonce_id") or "").strip())
        if console_detail:
            payload = console_detail.get("payload") if isinstance(console_detail.get("payload"), dict) else {}
            status = str(console_detail.get("status") or payload.get("status") or "").strip() or None
            next_row["console_missing_fields_status"] = status
            next_row["console_missing_fields_extracted_at"] = console_detail.get("extracted_at") or payload.get("extracted_at")
            if status == "done":
                next_row["console_missing_fields_json"] = compact_json_field(payload)
                next_row["dpe_image_url"] = payload.get("dpe_image_url")
                next_row["ges_image_url"] = payload.get("ges_image_url")
                for target_key, payload_key in json_keys.items():
                    next_row[target_key] = compact_json_field(payload.get(payload_key))
        chauffage_detail = chauffage_by_annonce.get(str(row.get("hektor_annonce_id") or "").strip())
        if chauffage_detail:
            chauffage_status = str(chauffage_detail.get("status") or "").strip() or None
            next_row["chauffage_console_status"] = chauffage_status
            next_row["chauffage_console_extracted_at"] = chauffage_detail.get("extracted_at")
            if chauffage_status == "done":
                next_row["chauffage_console_json"] = compact_json_field(chauffage_detail.get("chauffage"))
        enriched.append(next_row)
    return enriched


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


def api_prop_value(props: dict[str, object], key: str) -> str:
    item = props.get(key)
    if isinstance(item, dict):
        return normalize_text(item.get("value"))
    return normalize_text(item)


def normalize_dpe_image_value(value: object) -> str:
    text = normalize_text(value)
    for suffix in (".00", ".0"):
        if text.endswith(suffix):
            return text[: -len(suffix)]
    return text


def is_recent_dpe_date(value: object) -> bool:
    text = normalize_text(value)
    return bool(text and text not in {"0000-00-00", "1970-01-01"} and text >= "2021-07-01")


def build_dpe_image_urls_from_api_detail(detail_raw_json: object) -> dict[str, str | None]:
    raw_detail = safe_json_loads(detail_raw_json, {})
    if not isinstance(raw_detail, dict):
        return {}
    diagnostiques = raw_detail.get("diagnostiques")
    props = diagnostiques.get("props") if isinstance(diagnostiques, dict) else None
    if not isinstance(props, dict):
        return {}

    dpe_cons = normalize_dpe_image_value(api_prop_value(props, "dpe_cons"))
    dpe_ges = normalize_dpe_image_value(api_prop_value(props, "dpe_ges"))
    energie_finale = normalize_dpe_image_value(api_prop_value(props, "valeurEnergieFinale"))
    dpe_date = api_prop_value(props, "dpe_date")
    dpe_vierge = api_prop_value(props, "dpe_vierge") == "1"
    dpe_non_concerne = api_prop_value(props, "dpe_non_concerne") == "1"
    dpe_altitude = api_prop_value(props, "isDpeAltitude") == "1"

    if dpe_vierge:
        dpe_url = f"{DPE_IMAGE_BASE_URL}dpe_cons_FR_vierge_fr_web_V6.jpg"
        ges_url = f"{DPE_IMAGE_BASE_URL}dpe_ges_FR_vierge_fr_web_V6.jpg"
    elif dpe_non_concerne:
        dpe_url = f"{DPE_IMAGE_BASE_URL}dpe_cons_FR_nonconcerne_fr_web_V6.jpg"
        ges_url = f"{DPE_IMAGE_BASE_URL}dpe_ges_FR_nonconcerne_fr_web_V6.jpg"
    elif not dpe_cons or not dpe_ges:
        dpe_url = f"{DPE_IMAGE_BASE_URL}dpe_FR_cons_nonEffectue_fr_web_V6.jpg"
        ges_url = f"{DPE_IMAGE_BASE_URL}dpe_FR_ges_nonEffectue_fr_web_V6.jpg"
    elif dpe_cons == "0" and dpe_ges == "0":
        dpe_url = f"{DPE_IMAGE_BASE_URL}dpe_FR_cons_0_fr_web_V6.jpg"
        ges_url = f"{DPE_IMAGE_BASE_URL}dpe_FR_ges_0_fr_web_V6.jpg"
    elif is_recent_dpe_date(dpe_date):
        energy_suffix = f"_{energie_finale}" if energie_finale and energie_finale not in {"0", "0.0"} else ""
        altitude_suffix = "_altitude" if dpe_altitude else ""
        dpe_url = f"{DPE_IMAGE_BASE_URL}dpeg_web{dpe_cons}_{dpe_ges}{energy_suffix}_v3{altitude_suffix}.png"
        ges_url = f"{DPE_IMAGE_BASE_URL}ges_{dpe_ges}{energy_suffix}_v3{altitude_suffix}.png"
    else:
        dpe_url = f"{DPE_IMAGE_BASE_URL}dpe_FR_cons_{dpe_cons}_fr_web_V6.jpg"
        ges_url = f"{DPE_IMAGE_BASE_URL}dpe_FR_ges_{dpe_ges}_fr_web_V6.jpg"

    return {
        "dpe_image_url": dpe_url,
        "ges_image_url": ges_url,
        "dpe_image_urls_json": compact_json_field([dpe_url, ges_url]),
    }


def normalize_register_mandat_type(value: object) -> str | None:
    text = normalize_text(value)
    if not text:
        return None
    lowered = text.lower()
    # L'ordre est significatif, et doit rester aligne sur SQL_NORMALIZE_MANDAT_TYPE
    # (phase2/pipeline/view_generale.py), sans quoi le registre et la fiche annonce
    # classent differemment le meme mandat.
    #
    # "mandat de vente" etait teste en meme temps que "non exclusif" : un libelle
    # comme "Mandat de vente exclusif en cas de demarchage" etait donc classe SIMPLE,
    # le test sur "exclusif" n'etant jamais atteint. 107 mandats exclusifs
    # apparaissaient ainsi en SIMPLE au registre, alors que la fiche les donnait
    # justes. Un exclusif presente comme simple n'est pas une nuance d'affichage :
    # les deux n'ont pas les memes effets juridiques.
    if "semi-exclusif" in lowered:
        return "ACCORD"
    if "non exclusif" in lowered:
        return "SIMPLE"
    if "exclusif" in lowered:
        return "EXCLUSIF"
    if "mandat de vente" in lowered:
        return "SIMPLE"
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


# ═══════════════════════════════════════════════════════════════════════════════
# LE REGISTRE DIT « MONTANT » ET IL DIT LE PRIX DE L'ANNONCE          06/10/2026
# ═══════════════════════════════════════════════════════════════════════════════
# Le montant que Hektor rend dans `mandats[]` est resolu sur l'identifiant NU du
# mandat, qui est ambigu entre les familles HEKTOR et PROTEXA : 88 lignes portent
# le montant d'un AUTRE bien (62 000 EUR sur un bien a 112 500).
#
# ⛔ LE 05/10 ON AVAIT MASQUE CE CHIFFRE. C'ETAIT UNE RUSTINE, et elle a fait ce
#   que font les rustines : elle couvrait `mandat_montant` et laissait passer
#   `register_history_json` et `register_detail_payload_json`. Un masque cache,
#   il ne repare pas -- et il faut le reposer a chaque nouvel endroit qui lit.
#
# ─── LA REPARATION : ON MET LA VRAIE VALEUR, ON NE CACHE PLUS ──────────────────
# Le montant d'un mandat EST le prix du bien. Le registre le sait deja partout
# ailleurs -- le listing, la fiche, le €/m² et meme la branche de repli de la
# modale « Historique des versions » (App.tsx:24035) affichent `prix`.
# On prend donc le MEME `prix` que la ligne de registre porte deja, sans le
# reformater : un seul chiffre, une seule source, aucune divergence possible.
#
# MESURE QUI REND LA REPARATION SURE -- les 457 lignes a corps emprunte portent
#   TOUTES UNE SEULE VERSION, et leurs 88 montants sont tous sur la version
#   COURANTE : ZERO sur une version passee. Il n'y a donc rien d'ancien a perdre.
#   Les 112 montants de versions passees du reste du registre ne sont pas touches.
#
# ⚠ SEULE LA VERSION COURANTE PREND LE PRIX. Une version PASSEE garde son montant
#   d'epoque : l'annonce n'a qu'UN prix, celui d'aujourd'hui, et elle ne peut pas
#   dire a combien un mandat de 2022 avait ete signe.
#
# ⚠ LA PART « RECHERCHE » DU CORPS SUSPECT RESTE EN PLACE : retirer un texte
#   emprunte de la recherche n'est pas masquer un chiffre, et elle, elle sert.
# ═══════════════════════════════════════════════════════════════════════════════
def normalize_history_version(
    item: dict[str, object],
    *,
    is_current: bool,
    index: int,
    prix_annonce: object = None,
    corps_suspect: bool = False,
) -> dict[str, object]:
    montant = normalize_text(item.get("montant")) or None
    if is_current:
        # ⚠ PAS DE REPLI SUR LE CORPS QUAND IL EST EMPRUNTE. Mesure du 06/10 :
        #   une ligne (annonce 8482, n° 18513) n'a AUCUN prix et portait 69 000
        #   venus d'un autre bien -- le repli l'aurait reaffichee alors que le
        #   masque la cachait. Sans prix et corps emprunte : on ne dit rien.
        montant = normalize_text(prix_annonce) or (None if corps_suspect else montant)
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
        "montant": montant,
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


def mandate_current_series_rank(value: object, *dates: object) -> int:
    sort_num = mandate_sort_number(value)
    if sort_num <= 0 or sort_num > CURRENT_MANDATE_SERIES_MAX_NUM:
        return 1
    for item in dates:
        text = normalize_text(item)
        if text and text[:10] >= CURRENT_MANDATE_SERIES_START:
            return 0
    return 1


def build_register_detail_payload(
    *,
    raw_row: dict[str, object],
    current_version: dict[str, object],
    versions: list[dict[str, object]],
    embedded_avenants: list[dict[str, object]],
    images_preview_json: str | None,
    active_row: dict[str, object] | None,
    detail_available: bool,
    price_change_summary: dict[str, object] | None = None,
    prix_annonce: object = None,
    corps_suspect: bool = False,
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
        "mandat_history_json": json.dumps([normalize_history_version(item, is_current=index == 0, index=index, prix_annonce=prix_annonce, corps_suspect=corps_suspect) for index, item in enumerate(versions)], ensure_ascii=True, separators=(",", ":")),
        "mandat_avenants_json": json.dumps(embedded_avenants, ensure_ascii=True, separators=(",", ":")),
        "mandat_type": normalize_register_mandat_type(current_version.get("type")),
        "mandat_type_source": normalize_text(current_version.get("type")) or None,
        "mandat_date_debut": normalize_text(current_version.get("debut")) or None,
        "mandat_date_fin": normalize_text(current_version.get("fin")) or None,
        "mandat_date_cloture": normalize_text(current_version.get("cloture")) or None,
        # 06/10 : le prix de l'annonce, pas le montant resolu sur l'identifiant nu.
        # Sans prix ET corps emprunte, on ne dit rien plutot que de reprendre le
        # chiffre d'un autre bien.
        "mandat_montant": (
            normalize_text(prix_annonce)
            or (None if corps_suspect
                else normalize_text(current_version.get("montant")) or None)
        ),
        "mandants_texte": normalize_text(current_version.get("mandants")) or None,
        "mandat_note": normalize_text(current_version.get("note")) or None,
        "nb_images": len(preview_images) if isinstance(preview_images, list) else 0,
        "price_change_event_count": (price_change_summary or {}).get("price_change_event_count", 0),
        "price_change_last_source_kind": (price_change_summary or {}).get("price_change_last_source_kind"),
        "price_change_last_old_value": (price_change_summary or {}).get("price_change_last_old_value"),
        "price_change_last_new_value": (price_change_summary or {}).get("price_change_last_new_value"),
        "price_change_last_detected_at": (price_change_summary or {}).get("price_change_last_detected_at"),
        "price_change_last_source_updated_at": (price_change_summary or {}).get("price_change_last_source_updated_at"),
        "price_change_events_json": (price_change_summary or {}).get("price_change_events_json"),
    }
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


# Les deux etiquettes du MEME geste (lien vers le bien). Voir le commentaire
# dans charger_mandants_du_registre_des_liens.
ROLES_MANDANT = frozenset({"mandant", "proprietaire"})

# « Contact 10309272 », « Mr./Mme 276250_01 » : une civilite et un NUMERO, pas un
# nom. Ce sont les FICHES MUETTES du magasin de contacts (36 463 sur 356 342) :
# Hektor cree une seconde fiche pour le menage et n'y met pas de nom, le nom vit
# sur la fiche du conjoint.
# Mesure du 05/10 : 11 857 liens vivants pointent une fiche muette, dont 199 sur
# les 607 lignes a combler -- un nom affiche sur cinq aurait ete « Contact ... ».
# ⭐ ET LES JETER NE COUTE RIEN : sur les 607, ZERO ligne redevient vide, 196
#   perdent seulement un nom sur plusieurs. Le conjoint, lui, est nomme.
# ⚠ « Mr./Mme REYMONDON » n'est PAS muet : il faut des CHIFFRES SEULS apres la
#   civilite. Le motif l'exige.
_NOM_MUET = re.compile(r"^(?:contact|mr\.?/mme|m\.?/mme)\s*\d+(?:_\d+)?$", re.IGNORECASE)


def _nom_est_muet(nom: str) -> bool:
    return bool(_NOM_MUET.match((nom or "").strip()))



def _cle_de_nom(nom: str) -> str:
    """Le nom NU : sans civilite, sans accents, sans casse -- pour reperer un doublon.

    ⚠ IL EN FAUT UNE, ET C'EST LA MESURE QUI L'A IMPOSEE (04/10). Sur les 607
      annonces a combler, le registre des liens rend 1 241 personnes -- dont 267
      sont la MEME entite vue deux fois (974 apres nettoyage, -22 %).
      Exemple releve : « M. SCI JCL » et « Mr./Mme SCI JCL ».
      C'est le probleme connu des FICHES DE COUPLE : Hektor cree une seconde fiche
      pour le menage, et notre registre porte les deux A JUSTE TITRE -- c'est
      l'AFFICHAGE qui ne doit pas les repeter.
    """
    s = unicodedata.normalize("NFD", nom or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"\b(m|mme|mr|mlle|monsieur|madame|m\.)\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def charger_mandants_du_registre_des_liens(
    con: sqlite3.Connection,
) -> dict[str, list[dict[str, object]]]:
    """Les mandants que NOTRE registre des liens connait, par annonce.

    ══════════════════════════════════════════════════════════════════════════════
    POURQUOI CETTE SOURCE EXISTE                                     04/10/2026
    ══════════════════════════════════════════════════════════════════════════════
    SIGNALE PAR FREDERIC : des lignes du registre des mandats n'affichent AUCUN
    mandant, alors que la fiche annonce et le registre des relations les ont.

    MESURE : 638 lignes sans mandant sur 24 487, dont 607 que notre registre des
    liens connait parfaitement. Il couvre 24 451 des 24 487 lignes (99,9 %).

    LA CAUSE N'EST PAS LA LIGNEE DU REGISTRE -- il est AUTONOME (app_mandat est
    notre table durable : 26 835 mandats, plage d'identifiants propre, doublure,
    2 sentinelles, le worker y ecrit a la naissance). Le defaut porte sur UNE
    COLONNE SUR 25 : `mandants_texte`, la seule restee un texte recopie de Hektor,
    sans identifiant et sans chemin pour se remplir depuis chez nous.
        view_generale.py:338 -> COALESCE(mandat Hektor, detail Hektor)
        « app_relation » : ZERO occurrence dans ce fichier.
    Quand Hektor ne fournit plus ce texte -- bien VENDU, ARCHIVE, fiche mandat
    incomplete -- RIEN ne prend le relais. Or ce sont exactement les liens que le
    registre des relations a ete cree pour garder (les 82 386 qu'un bien vendu
    emportait) : 635 des 638 trous sont des biens sans fiche dans l'app.

    ⚠ ON NE LIT QUE LES LIENS VIVANTS (`retire_le IS NULL`) : un mandant retire le
      03/10 ne doit pas reapparaitre ici par la bande.

    ⭐ ET SA PLACE DANS LE RUN EST LE POINT DELICAT. Cette fonction est appelee par
      build_mandat_register_rows, donc au MOMENT DU PUSH :
         l. 839  registre des mandats (app_mandat)   <- lirait les liens DE LA VEILLE
         l. 922  registre des liens (app_relation)      rafraichi ici
         l.1159  push upgrade -> ECRIT le registre    <- NOUS SOMMES ICI, c'est frais
      Corriger dans mandat_ledger.py aurait reintroduit l'erreur classique du
      projet : lire la couche de la veille.
      ⭐ Et le meme constructeur sert push_single_annonce_to_supabase.py -- donc le
        chemin IMMEDIAT du worker (~1 min) en profite aussi, sans code en plus.
    """
    mandants: dict[str, list[dict[str, object]]] = {}
    try:
        lignes = con.execute(
            # ⭐ LE NOM SE LIT PAR NOTRE NUMERO, PAS PAR CELUI DE HEKTOR.
            #   `app_contact_current.hektor_contact_id` porte EN FAIT l'identifiant
            #   de l'app (serie 10 000 001+) -- la substitution d'identite du build.
            #   Mesure du 05/10 sur 20 000 liens vivants :
            #       JOIN sur app_contact_id     -> 20 000 noms
            #       JOIN sur hektor_contact_id  ->      0 nom
            "SELECT r.hektor_annonce_id AS ann,"
            "       r.app_contact_id    AS app_id,"
            "       r.hektor_contact_id AS hektor_id,"
            "       r.role_hektor       AS role,"
            "       COALESCE(NULLIF(TRIM(c.display_name), ''), '') AS nom"
            "  FROM app_relation r"
            "  LEFT JOIN app_contact_current c"
            "         ON c.hektor_contact_id = CAST(r.app_contact_id AS TEXT)"
            " WHERE r.retire_le IS NULL"
        ).fetchall()
    except sqlite3.OperationalError:
        # Le registre des liens n'existe pas encore (environnement neuf). On ne
        # devine pas : on rend vide, et le COALESCE d'en face garde Hektor.
        return {}

    vus: dict[str, set[str]] = {}
    roles_ecartes: dict[str, int] = {}
    # ⛔⛔ ACCES PAR POSITION, JAMAIS PAR NOM -- ET C'EST UNE PANNE VECUE.
    #   Ma 1re version lisait ligne["ann"], ce qui exige con.row_factory =
    #   sqlite3.Row. registre_mandats_upsert.py le pose, mes controles aussi --
    #   mais push_single_annonce_to_supabase.py NON. Resultat le 05/10 : le chemin
    #   IMMEDIAT du worker (refresh_console_data, ~1 min) a echoue 9 fois en 9
    #   heures sur « TypeError: tuple indices must be integers », et l'app est
    #   restee sur les donnees de la veille sans que rien ne le dise a l'ecran.
    #   ⚠ Une fonction appelee par PLUSIEURS chemins ne suppose pas la forme des
    #     lignes : la position marche dans les deux cas.
    for annonce_brute, app_id, hektor_id, role_brut, nom_brut in lignes:
        annonce = normalize_text(annonce_brute)
        nom = normalize_text(nom_brut)
        role = (normalize_text(role_brut) or "").lower()
        # ⚠ LE REGISTRE DES LIENS NE PORTE PAS QUE DES MANDANTS. Mesure du 05/10 :
        #     mandant 74 200 · proprietaire 58 479 · acquereur_compromis 4
        #   Les deux premiers sont LE MEME GESTE (`fait = proprietaire_du_bien`
        #   pour 100 % des lignes) : « proprietaire » devient « mandant » quand un
        #   numero de mandat existe (taxonomie du 24/07). Le troisieme est un
        #   geste DIFFERENT : un acquereur n'est jamais un mandant.
        #   ⭐ LISTE BLANCHE, PAS LISTE NOIRE -- et COMPTEE : une forme inconnue
        #     ne se taira pas (lecon de `list_broadcasts`, 3 mois de silence).
        if role not in ROLES_MANDANT:
            roles_ecartes[role or "(vide)"] = roles_ecartes.get(role or "(vide)", 0) + 1
            continue
        if not annonce or not nom:
            # Sans nom, on n'a rien a AFFICHER. La ligne reste au registre des
            # liens (elle y a sa place), elle n'entre simplement pas ici.
            continue
        cle = _cle_de_nom(nom)
        if not cle or cle in vus.setdefault(annonce, set()):
            continue
        vus[annonce].add(cle)
        entree: dict[str, object] = {
            "app_contact_id": app_id,
            "hektor_contact_id": normalize_text(hektor_id) or None,
            "nom": nom,
        }
        if _nom_est_muet(nom):
            # ⭐ LE LIEN RESTE DANS LA LISTE -- la personne EST mandante, et ses deux
            #   numeros sont vrais : la fiche cliquable a venir saura la retrouver.
            #   C'est seulement son NOM qu'on n'affiche pas.
            entree["muet"] = True
        mandants.setdefault(annonce, []).append(entree)
    if roles_ecartes:
        print(
            "[registre des liens] roles ecartes : "
            + ", ".join("%s=%d" % (k, v) for k, v in sorted(roles_ecartes.items())),
            file=sys.stderr,
        )
    return mandants


def texte_des_mandants(mandants: list[dict[str, object]]) -> str:
    """Le meme separateur que Hektor (« Petra COSTE | Guy COSTE »), pour que le
    listing et la recherche ne voient aucune difference de forme.

    ⚠ Les fiches MUETTES sont ecartees ICI, et seulement ici : elles restent dans
      `mandants_json` avec leurs identifiants. Voir `_nom_est_muet`.
    """
    return " | ".join(
        str(m.get("nom") or "").strip()
        for m in mandants
        if str(m.get("nom") or "").strip() and not m.get("muet")
    )


def charger_corps_suspects(con: sqlite3.Connection) -> set[tuple[str, str]]:
    """Les (annonce, numero) dont le CORPS vient d'un autre mandat.       05/10/2026

    ══════════════════════════════════════════════════════════════════════════════
    LE DEFAUT, ETABLI SUR LA REPONSE BRUTE DE HEKTOR
    ══════════════════════════════════════════════════════════════════════════════
        hektor_mandat_id = 105 sert DEUX annonces, avec le MEME corps
           annonce   454  numero 14898  2022-07-20  montant 62000  « Marie-Jose BANO »
           annonce 39707  numero 18523  2026-04-10  montant 62000  « Marie-Jose BANO »
        l'annonce 39707 vaut 112 500, et ses proprietaires sont SOUVIGNET.

    ⭐⭐ LA VRAIE CAUSE, ET CE N'EST PAS UN « RECYCLAGE ». Le projet l'avait deja
      etablie le 25/08 (notice/NOTE_CHAINE_DES_MANDATS_2026-08-25.md, §6) :
          « Hektor n'attend pas un numero mais un couple <id>-<FAMILLE> --
            648-PROTEXA ou 9887-HEKTOR -- et une valeur amputee est IGNOREE
            SANS ERREUR. »
      L'identifiant complet d'un mandat est donc `<id>-<FAMILLE>`. L'agence est
      passee aux mandats PROTEXA en mars 2026, et PROTEXA numerote DEPUIS 1 :
      `10-PROTEXA` et `10-HEKTOR` sont deux mandats DIFFERENTS, pas un recyclage.
      Mesure du 05/10 : sur 449 identifiants nus partages, 446 portent les DEUX
      familles. Et les 454 lignes marquees ici sont PROTEXA a 100 %.

      ⛔ MAIS LA FICHE ANNONCE ET getMandatById RESOLVENT SUR L'IDENTIFIANT NU.
        Ils tombent donc sur l'enregistrement HEKTOR de meme numero, et nous
        renvoient SON montant et SES mandants -- avec le numero et les dates du
        mandat PROTEXA. Le suffixe ne sert a rien en lecture : verifie le 05/10,
        getMandatById("10"), ("10-PROTEXA") et ("10-HEKTOR") rendent TOUS les trois
        le mandat HEKTOR 16564 de 2024.

    ⭐ DONC LA DONNEE EXISTE CHEZ HEKTOR : l'enregistrement PROTEXA est bien la (ses
      DATES nous parviennent, 2026->2027, elles ne peuvent pas venir du HEKTOR de
      2022). C'est sa RESOLUTION qui echoue. Le jour ou Hektor tiendra compte de la
      famille, le montant reviendra tout seul au prochain run.
    Voir notice/AUDIT_REGISTRE_MANDATS_2026-10-05.md.

    ⭐ LE CRITERE, ET IL A ETE VALIDE CONTRE L'API DE HEKTOR (8 cas sur 8).
      Un identifiant partage par plusieurs mandats de NUMEROS DIFFERENTS porte un
      seul vrai enregistrement, et `getMandatById(id)` rend TOUJOURS celui dont le
      NUMERO EST LE PLUS PETIT :
          id  3 : nos lignes 16767 (2024) / 18420 (2026)      -> l'API rend 16767
          id  7 : nos lignes 16635 (2024) / 18424 (sans date) -> l'API rend 16635
          id 10 : nos lignes 16564 (2024) / 18427 (2026)      -> l'API rend 16564
      Donc : le plus petit numero est le VRAI mandat, et les autres lignes sont
      FABRIQUEES par la fiche annonce (numero et dates de l'annonce + corps du vieux
      mandat). On ne marque QUE les fabriquees -- masquer le vrai cacherait un
      montant juste.

    ⚠ ON TRIE SUR LE NUMERO, PAS SUR LA DATE. L'identifiant 7 porte une ligne SANS
      date : un tri par date la ferait passer en tete et accuserait le vrai mandat.
      Le numero, lui, est toujours present et croit avec le temps.

    ⛔ CE QUE CETTE LISTE NE FAIT PAS : elle ne repare rien. Le montant du mandat
      fabrique n'existe NULLE PART -- ni chez nous, ni chez Hektor : `getMandatById`
      ne connait que le vieux mandat, et `mandats(idAnnonce)` rend []. Elle permet
      seulement de ne plus AFFICHER une valeur fausse, et de ne plus donner un nom
      etranger a la recherche. La valeur de Hektor reste dans le payload embarque.
    """
    try:
        lignes = con.execute(
            "WITH partages AS ("
            "   SELECT hektor_mandat_id FROM hektor.hektor_mandat"
            "    WHERE TRIM(COALESCE(CAST(hektor_annonce_id AS TEXT), '')) <> ''"
            "    GROUP BY 1 HAVING COUNT(DISTINCT COALESCE(numero, '')) > 1),"
            # Le VRAI mandat de chaque identifiant : le plus petit numero.
            " vrais AS ("
            "   SELECT hektor_mandat_id,"
            "          MIN(CAST(numero AS INTEGER)) AS numero_vrai"
            "     FROM hektor.hektor_mandat"
            "    WHERE hektor_mandat_id IN (SELECT hektor_mandat_id FROM partages)"
            "      AND numero GLOB '[0-9]*'"
            "    GROUP BY 1)"
            " SELECT CAST(m.hektor_annonce_id AS TEXT), CAST(m.numero AS TEXT)"
            "   FROM hektor.hektor_mandat m"
            "   JOIN vrais v ON v.hektor_mandat_id = m.hektor_mandat_id"
            "  WHERE TRIM(COALESCE(CAST(m.hektor_annonce_id AS TEXT), '')) <> ''"
            "    AND (m.numero NOT GLOB '[0-9]*'"
            "         OR CAST(m.numero AS INTEGER) <> v.numero_vrai)"
        ).fetchall()
    except sqlite3.OperationalError:
        # Le miroir n'est pas attache (environnement reduit) : on ne devine pas, on
        # ne marque rien -- le registre garde exactement son comportement.
        return set()
    suspects = {(normalize_text(a) or "", normalize_text(n) or "") for a, n in lignes}
    suspects.discard(("", ""))
    if suspects:
        print("[registre des mandats] lignes dont le corps vient d'un AUTRE mandat "
              "(l'identifiant nu est ambigu entre les familles HEKTOR et PROTEXA) : "
              "%d -- mandants repris chez nous, texte retire de la recherche "
              "(le montant, lui, n'est plus masque : c'est le prix de l'annonce)"
              % len(suspects),
              file=sys.stderr)
    return suspects


def build_mandat_register_rows(
    con: sqlite3.Connection,
    *,
    limit: int | None,
    dossier_ids: list[int] | None = None,
) -> list[dict[str, object]]:
    active_rows = enrich_offer_transaction_fields(
        con,
        fetch_rows_by_ids(
            con,
            base_sql=SQL_DOSSIERS_BASE,
            id_column="app_dossier_id",
            ids=dossier_ids,
            limit=None,
        ),
    )
    if dossier_ids is not None and not active_rows:
        return []
    target_annonce_ids = {
        normalize_text(row.get("hektor_annonce_id"))
        for row in active_rows
        if dossier_ids is not None and normalize_text(row.get("hektor_annonce_id"))
    }
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

    # ⚠ UNE SEULE LECTURE POUR TOUT LE LOT, pas une par ligne : 132 683 liens et
    #   356 344 contacts -- une requete par mandat ferait 24 487 allers-retours.
    #   Meme patron que les autres dictionnaires de ce constructeur.
    mandants_par_annonce = charger_mandants_du_registre_des_liens(con)
    corps_suspects = charger_corps_suspects(con)

    # Lot B : affaire (offre/compromis/vente) PAR cycle, clé (annonce, hektor_mandat_id).
    affaires_by_mandat: dict[tuple[str, str], dict[str, object]] = {}
    for row in fetch_rows(con, SQL_MANDAT_AFFAIRES):
        a_id = normalize_text(row.get("hektor_annonce_id"))
        m_id = normalize_text(row.get("hektor_mandat_id"))
        if a_id and m_id:
            affaires_by_mandat[(a_id, m_id)] = row
    # Dossiers par acquereur : les OFFRES ne portent quasi jamais de mandat (98% a 0), donc le lien
    # offre<->compromis se fait par (annonce, id acquereur), pas par le mandat. On regroupe donc TOUTES
    # les affaires (offres incluses) par annonce, on batit un dossier par acquereur (chaine complete),
    # puis on affecte chaque dossier a un cycle. Les annonces a affaires sont quasi toutes mono-cycle
    # (8/10462 multi) : pour celles-la on affecte via le mandat du compromis/vente -> numero.
    mandat_numero: dict[tuple[str, str], str] = {}
    annonce_numeros: dict[str, set[str]] = {}
    for row in fetch_rows(con, "SELECT hektor_annonce_id, hektor_mandat_id, numero FROM hektor.hektor_mandat"):
        a_id = normalize_text(row.get("hektor_annonce_id"))
        m_id = normalize_text(row.get("hektor_mandat_id"))
        num = normalize_text(row.get("numero"))
        if a_id and m_id and num:
            mandat_numero[(a_id, m_id)] = num
        if a_id and num:
            annonce_numeros.setdefault(a_id, set()).add(num)

    affaires_by_annonce: dict[str, list[dict[str, object]]] = {}
    for row in fetch_rows(con, SQL_MANDAT_AFFAIRES_ALL):
        a_id = normalize_text(row.get("hektor_annonce_id"))
        if a_id:
            affaires_by_annonce.setdefault(a_id, []).append(row)

    # B+ : filet ledger — on ajoute les affaires DISPARUES de Hektor (present_in_hektor=0), conservees
    # dans le ledger app-owned. Les affaires PRESENTES viennent de Hektor live ci-dessus (autorite) ;
    # ici uniquement les disparues, marquees _dropped pour l'affichage ("plus dans Hektor depuis ...").
    # Strategie "Hektor d'abord, ledger en filet" : aucune dependance de fraicheur pour les presentes.
    try:
        ledger_dropped = fetch_rows(con, """
            SELECT hektor_annonce_id, hektor_mandat_id, kind, hektor_affaire_id AS id, state,
                   hektor_acquereur_id AS acq_id, acquereur_json AS acq_json, montant,
                   date AS dt, date_acte, sequestre, last_seen_at
            FROM app_affaire_ledger WHERE present_in_hektor = 0
        """)
    except sqlite3.OperationalError:
        ledger_dropped = []  # ledger pas encore cree (env sans backfill)
    for row in ledger_dropped:
        a_id = normalize_text(row.get("hektor_annonce_id"))
        if not a_id:
            continue
        row["_dropped"] = True
        row["_last_seen"] = normalize_text(row.get("last_seen_at")) or None
        affaires_by_annonce.setdefault(a_id, []).append(row)

    # dossiers par cycle (annonce, numero) + repli agrege par annonce (mono-cycle / numero absent)
    dossiers_by_cycle: dict[tuple[str, str], list[dict[str, object]]] = {}
    dossiers_by_annonce: dict[str, list[dict[str, object]]] = {}
    for a_id, rows in affaires_by_annonce.items():
        dossiers = build_affaires_dossiers(rows)
        nums = annonce_numeros.get(a_id) or set()
        for d in dossiers:
            mids = d.pop("_mandats", None) or set()
            targets = {mandat_numero[(a_id, m)] for m in mids if (a_id, m) in mandat_numero}
            targets = (targets & nums) or nums  # cycles resolus, sinon tous les cycles de l'annonce
            for num in targets:
                dossiers_by_cycle.setdefault((a_id, num), []).append(d)
        dossiers_by_annonce[a_id] = list(dossiers)  # _mandats deja retire ci-dessus

    register_rows: list[dict[str, object]] = []
    socle = (SQL_REGISTER_RAW_DEPUIS_APP_MANDAT if REGISTRE_DEPUIS_APP_MANDAT
             else SQL_REGISTER_RAW_BASE)
    if dossier_ids is not None and target_annonce_ids:
        # ⚠ LE MEME SOCLE QUE LE RUN COMPLET, ET C'EST INDISPENSABLE.
        #   Ce chemin est le push CIBLE d'une annonce : il EFFACE les lignes de
        #   registre de cette annonce, puis repose ce qu'il fabrique. S'il
        #   fabriquait avec l'ancienne requete -- filtree sur le statut --
        #   pendant que le run complet fabrique avec la nouvelle, une annonce
        #   hors statut verrait ses lignes effacees et JAMAIS reposees.
        #   Le registre perdrait en journee ce que la nuit vient de gagner.
        placeholders = ",".join("?" for _ in target_annonce_ids)
        raw_rows = fetch_rows(
            con,
            f"SELECT * FROM ({socle}) AS base WHERE CAST(hektor_annonce_id AS TEXT) IN ({placeholders})",
            tuple(sorted(target_annonce_ids)),
        )
    else:
        raw_rows = fetch_rows(con, build_limited_sql(socle, None))
    # A.3-tech etape C : la matiere du mandat vient de NOTRE registre, qui ne
    # perd jamais une ligne -- au lieu du tableau `mandats` du detail, qui
    # disparait avec l'annonce des que son statut sort de la liste.
    mandats_app = charger_mandats_depuis_app_mandat(con) if REGISTRE_DEPUIS_APP_MANDAT else None
    price_change_by_annonce = build_price_change_by_annonce(
        con,
        [normalize_text(row.get("hektor_annonce_id")) for row in raw_rows if normalize_text(row.get("hektor_annonce_id"))],
    )
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
        if not mandate_entries and mandats_app is None:
            continue

        grouped_entries: dict[str, list[dict[str, object]]] = defaultdict(list)
        for item in mandate_entries:
            grouped_entries[normalize_text(item.get("numero"))].append(item)
        if mandats_app is not None:
            # NOTRE registre fait foi pour le mandat. S'il ne connait pas cette
            # annonce, on ne fabrique rien : une ligne de registre sans mandat
            # au registre serait une ligne inventee.
            depuis_nous = mandats_app.get(annonce_id)
            if not depuis_nous:
                continue
            grouped_entries = defaultdict(list, {n: list(v) for n, v in depuis_nous.items()})

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
        price_change_summary = price_change_by_annonce.get(annonce_id, {})

        for numero, versions in grouped_entries.items():
            if mandats_app is not None:
                # ⚠ ON NE RETRIE PAS. versions_json est DEJA classe, et il l'a
                #   ete sur la matiere BRUTE -- avant que « 0 » ne devienne vide.
                #   Retrier ici, c'est noter des montants deja nettoyes : le
                #   classement change, donc la version retenue (annonce 59279,
                #   n° 18259 : le registre garde la ligne close, le retri prenait
                #   l'ouverte). Un nettoyage d'affichage ne vote pas -- et il ne
                #   doit pas voter une etape plus loin non plus.
                versions_sorted = list(versions)
            else:
                versions_sorted = sorted(
                    versions,
                    key=lambda item: compute_mandat_version_score(item),
                    reverse=True,
                )
            current_version = versions_sorted[0]
            active_exact = active_by_key.get((annonce_id, numero))
            source_row = active_exact or active_any
            # Lot B : affaire PROPRE à ce cycle (via l'id hektor du mandat courant du numéro).
            # Repli sur l'affaire aplatie du dossier actif SEULEMENT si ce cycle est l'actif
            # (pour un cycle passé, source_row = active_any porterait l'affaire du cycle courant).
            cycle_affaire = affaires_by_mandat.get((annonce_id, normalize_text(current_version.get("id"))))
            if not cycle_affaire and active_exact is not None:
                cycle_affaire = active_exact
            cycle_affaire = cycle_affaire or {}
            detail_available = source_row is not None and source_row.get("app_dossier_id") is not None
            synthetic_app_dossier_id = int(source_row.get("app_dossier_id")) if detail_available else synthetic_register_app_dossier_id(annonce_id, numero)
            embedded_avenants = normalize_embedded_avenants(versions_sorted)
            source_updated_at = (
                normalize_text(source_row.get("date_maj")) if source_row else ""
            ) or normalize_text(raw.get("date_maj")) or normalize_text(raw.get("detail_synced_at")) or normalize_text(raw.get("annonce_synced_at")) or None
            # Ce que NOTRE registre des liens sait de ce bien (deja dedoublonne).
            mandants_du_bien = mandants_par_annonce.get(annonce_id) or []
            # ⚠ LE CORPS DE CETTE LIGNE VIENT-IL D'UN AUTRE MANDAT ? Voir
            #   charger_corps_suspects : Hektor recycle ses identifiants de mandat et
            #   sert, pour le mandat neuf, le corps de l'ancien (montant + mandants).
            corps_suspect = (annonce_id, numero) in corps_suspects
            # LE PRIX DU BIEN, calcule UNE fois : il sert a la colonne `prix`, au
            # montant de la ligne, a celui du payload embarque et a la version
            # courante de l'historique. Une seule variable = aucune divergence
            # possible entre ce que le listing affiche et ce que la fiche affiche.
            prix_ligne = (source_row.get("prix") if source_row else None) or raw.get("prix")
            row = {
                "register_row_id": f"{annonce_id}:{numero}",
                # ⚠ MARQUEUR INTERNE, JAMAIS ENVOYE : build_current_mandat_register_rows
                #   enumere ses colonnes une par une, donc celle-ci s'arrete au push.
                #   Elle y sert a retirer le texte de Hektor de `search_text`.
                "corps_suspect": 1 if corps_suspect else 0,
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
                "register_sort_group": mandate_current_series_rank(
                    numero,
                    current_version.get("dateenr"),
                    current_version.get("debut"),
                    current_version.get("fin"),
                    raw.get("date_enregistrement"),
                    raw.get("date_maj"),
                    source_updated_at,
                ),
                "register_sort_num": mandate_sort_number(numero),
                "titre_bien": titre_bien,
                "ville": (source_row.get("ville") if source_row else None) or normalize_text(raw.get("ville")) or None,
                "type_bien": (source_row.get("type_bien") if source_row else None) or normalize_text(raw.get("idtype")) or None,
                "commerce_sous_type": (source_row.get("commerce_sous_type") if source_row else None) or normalize_text(raw.get("commerce_sous_type")) or None,
                # C.15 : la famille d'offre, pour que le registre sache distinguer
                # une vente d'un local professionnel sans deviner d'apres le type.
                "offre_type": (source_row.get("offre_type") if source_row else None) or normalize_text(raw.get("offre_type")) or None,
                "prix": prix_ligne,
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
                "mandat_date_cloture": normalize_text(current_version.get("cloture") or current_version.get("dateCloture") or current_version.get("date_cloture")) or None,
                # ─── LE MONTANT EST LE PRIX DE L'ANNONCE ─────────── 06/10/2026
                # Le masque du 05/10 (« None si corps_suspect ») est RETIRE : il
                # cachait un chiffre faux sans en mettre un vrai, et il laissait
                # passer deux autres chemins. Voir le bloc au-dessus de
                # `normalize_history_version`. On prend EXACTEMENT le `prix` que
                # la ligne porte -- meme variable, donc jamais de divergence.
                "mandat_montant": (
                    normalize_text(prix_ligne)
                    or (None if corps_suspect
                        else normalize_text(current_version.get("montant")) or None)
                ),
                # ─── LES MANDANTS ────────────────────────────────── 04/10/2026
                # `mandants_json` : NOTRE liste, avec les DEUX numeros de chaque
                #   personne. Elle est posee des qu'on la connait -- c'est elle
                #   qui permettra des fiches CLIQUABLES (chantier suivant), et
                #   elle porte le MULTIPLE : 81 % des mandats ont plusieurs
                #   mandants (jusqu'a 7 apres dedoublonnage). Un texte unique ne
                #   savait pas les distinguer.
                # ═══ `mandants_texte` : NOTRE LISTE D'ABORD ═══  change le 05/10
                #
                # ⚠ L'INVERSE DE CE QUE J'AVAIS POSE LE MATIN MEME, et c'est la
                #   MESURE qui l'a impose. « Jamais d'ecrasement » etait une regle
                #   de prudence prise avant de savoir ce que notre liste valait.
                #
                #   Ce qu'ecraser coute, mesure sur les 24 451 lignes remplies :
                #       personnes que Hektor nomme et que nous perdrions :  0
                #   (ma premiere mesure disait 7 503 : je comparais des FICHES, pas
                #    des PERSONNES -- les doubles fiches de couple, deja fusionnees
                #    par le dedoublonnage. Avec la vraie cle : zero.)
                #
                # ⭐ ET L'ARGUMENT QUI TRANCHE : depuis le 03/10 on sait RETIRER un
                #   mandant. Notre liste se met a jour ; le texte de Hektor, FIGE,
                #   ne le fera jamais. Le garder prioritaire, c'etait s'engager a
                #   afficher indefiniment un mandant qu'on vient de retirer.
                #
                # ⛔ RIEN N'EST DETRUIT. Le texte de Hektor reste tel quel dans le
                #   payload embarque (`build_trimmed_detail_payload`, qui lit la
                #   valeur brute), et le push le redonne a `search_text` : les
                #   adresses collees aux noms (62 % des lignes) restent CHERCHABLES
                #   sans etre affichees.
                #
                # Hektor redevient le repli, pour le jour ou nos liens ne savent
                # personne (31 lignes aujourd'hui).
                "mandants_json": json.dumps(mandants_du_bien, ensure_ascii=False) if mandants_du_bien else None,
                "mandants_texte": (
                    texte_des_mandants(mandants_du_bien)
                    or normalize_text(current_version.get("mandants"))
                    or None
                ),
                "mandat_note": normalize_text(current_version.get("note")) or None,
                "price_change_event_count": price_change_summary.get("price_change_event_count", 0),
                "price_change_last_source_kind": price_change_summary.get("price_change_last_source_kind"),
                "price_change_last_old_value": price_change_summary.get("price_change_last_old_value"),
                "price_change_last_new_value": price_change_summary.get("price_change_last_new_value"),
                "price_change_last_detected_at": price_change_summary.get("price_change_last_detected_at"),
                "price_change_last_source_updated_at": price_change_summary.get("price_change_last_source_updated_at"),
                "priority": source_row.get("priority") if source_row else None,
                "offre_id": cycle_affaire.get("offre_id"),
                "offre_state": cycle_affaire.get("offre_state"),
                "offre_last_proposition_type": (active_exact.get("offre_last_proposition_type") if active_exact is not None else None),
                "compromis_id": cycle_affaire.get("compromis_id"),
                "compromis_state": cycle_affaire.get("compromis_state"),
                "vente_id": cycle_affaire.get("vente_id"),
                "affaires_detail_json": build_cycle_affaire_blob(
                    cycle_affaire,
                    dossiers_by_cycle.get((annonce_id, numero))
                    or dossiers_by_annonce.get(annonce_id, []),
                ),
                "source_updated_at": source_updated_at,
                "register_source_kind": "historique" if status in {"Vendu", "Clos"} or not detail_available else "actif",
                "register_detail_available": 1 if detail_available else 0,
                "register_version_count": len(versions_sorted),
                "register_embedded_avenant_count": len(embedded_avenants),
                "register_history_json": json.dumps(
                    [
                        normalize_history_version(
                            item, is_current=index == 0, index=index,
                            prix_annonce=prix_ligne, corps_suspect=corps_suspect,
                        )
                        for index, item in enumerate(versions_sorted)
                    ],
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
                    price_change_summary=price_change_summary,
                    prix_annonce=prix_ligne,
                    corps_suspect=corps_suspect,
                ),
            }
            register_rows.append(row)

    register_rows.sort(
        key=lambda item: (
            int(item.get("register_sort_group") if item.get("register_sort_group") is not None else 1),
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


# ═══════════════════════════════════════════════════════════════════════════════
# LA FICHE ANNONCE PREND SES MANDANTS CHEZ NOUS                      06/10/2026
# ═══════════════════════════════════════════════════════════════════════════════
# Le registre des mandats a ete repare le 05/10 : ses mandants viennent de NOTRE
# registre des liens. LA FICHE ANNONCE, ELLE, N'A JAMAIS ETE TOUCHEE -- elle lit
# `mandats_json`, c'est-a-dire la reponse brute de Hektor.
#
# ─── CE QUE LA MESURE DIT VRAIMENT, ET ELLE A CORRIGE UN CHIFFRE DE LA VEILLE ──
# Compter les entrees qui PORTENT un texte de mandant n'est pas compter celles
# qui portent le nom D'UN AUTRE. Sur les 457 couples a corps emprunte :
#       370  Hektor et nous designons LA MEME PERSONNE, ecrite autrement
#            (« M. CLEMENT Pascal - bonarme Sermentizon (63120) » contre
#             « M. Pascal CLEMENT ») -- et le texte de Hektor est PLUS RICHE :
#            il porte l'adresse, et parfois un co-mandant que notre texte perd.
#        86  AUCUN nom en commun : la, c'est vraiment le nom d'un autre bien
#         1  Hektor n'a pas de texte
#         0  sans recours chez nous
#
# ⭐ LES 86 SONT PROUVES PAR UNE TROISIEME SOURCE, independante des deux autres :
#   le bloc `proprietaires` DE L'ANNONCE, que Hektor rend par annonce et non par
#   identifiant de mandat. Mesure : il confirme NOTRE nom 86 fois sur 86, et
#   celui de `mandats[]` ZERO fois.
#
# ─── LA REGLE, PLUS ETROITE QUE CELLE DU REGISTRE -- ET C'EST VOULU ────────────
#   Le registre porte une colonne de NOMS SEULS : y preferer notre liste ne perd
#   rien. La fiche annonce, elle, affiche un texte qui porte AUSSI l'adresse.
#   On ne remplace donc QUE si les deux conditions tiennent :
#       ① le couple (annonce, numero) est un corps emprunte  -- critere du 05/10,
#         valide contre l'API de Hektor 8 fois sur 8
#       ② et nos noms n'ont AUCUN nom en commun avec le texte de Hektor
#   Sinon on ne touche a rien. 86 entrees reecrites, 370 laissees intactes.
#
# ⚠ NOS MANDANTS SONT CONNUS PAR ANNONCE, PAS PAR MANDAT -- comme au registre,
#   qui applique deja la meme liste a tous les mandats d'un bien (ligne 2262).
#
# ⚠ ON NE TOUCHE PAS AU MIROIR. `hektor_annonce_detail.mandats_json` garde la
#   reponse de Hektor telle quelle : la reecriture n'a lieu que dans le PAYLOAD.
#
# ⚠ `mandats_json` est tantot une LISTE, tantot un OBJET SEUL (memoire
#   `blob-json-liste-ou-objet-seul`) : les deux formes sont traitees.
#
# ─── ET LE MONTANT AUSSI (lot 4, le meme jour) ────────────────────────────────
#   La fiche annonce affichait AUSSI le montant emprunte, sur 88 entrees :
#   « 147 000 » sur un bien a 49 000 (annonce 59559), « 80 000 » sur un bien a
#   40 500 (annonce 61740). Le registre a ete repare au lot 2 ; ici c'est le
#   meme geste, au meme endroit, derriere le meme interrupteur.
#
# RETOUR ARRIERE : APP_DETAIL_MANDANTS_DEPUIS_NOS_LIENS=0 dans l'environnement.
# ═══════════════════════════════════════════════════════════════════════════════
DETAIL_MANDANTS_DEPUIS_NOS_LIENS = (
    os.environ.get("APP_DETAIL_MANDANTS_DEPUIS_NOS_LIENS", "1") == "1"
)

# Les mots qui ne designent personne : civilites et liaisons. Ils ne doivent pas
# faire croire a un nom commun entre deux textes (« M. » est partout).
_MOTS_SANS_NOM = {
    "MONSIEUR", "MADAME", "MLLE", "MME", "MR", "ETS", "SARL", "SCI",
    "ET", "DE", "DU", "DES", "LA", "LE", "LES", "BIS", "TER", "RUE",
}


def jetons_de_nom(valeur: object) -> set[str]:
    """Les noms d'un texte, sans accent, sans ponctuation, sans civilite.

    Sert UNIQUEMENT a repondre a « ces deux textes parlent-ils de la meme
    personne ? ». On ne compare donc pas des chaines : « M. CLEMENT Pascal -
    bonarme Sermentizon » et « M. Pascal CLEMENT » doivent se reconnaitre.
    """
    sans_accent = (
        unicodedata.normalize("NFKD", str(valeur or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    mots = re.sub(r"[^A-Za-z]+", " ", sans_accent).upper().split()
    return {mot for mot in mots if len(mot) > 2 and mot not in _MOTS_SANS_NOM}


def mandats_json_corrige(
    valeur: object,
    mandants_du_bien: list[dict[str, object]] | None,
    numeros_suspects: set[str] | None,
    prix_annonce: object = None,
    numero_courant: object = None,
) -> tuple[object, int, int]:
    """Rend (le blob, mandants reecrits, montants corriges).

    DEUX CORRECTIONS, et elles ne portent QUE sur les entrees a corps emprunte.

    ① LES MANDANTS -- on ne remplace que si nos noms n'ont AUCUN nom en commun
      avec le texte de Hektor. Sinon on garde le sien, qui est plus riche (il
      porte l'adresse, parfois un co-mandant). Un texte n'est JAMAIS vide.

    ② LE MONTANT (06/10, lot 4) -- il est emprunte a un autre bien : mesure sur
      88 entrees, « 147 000 » affiche sur un bien a 49 000 (annonce 59559).
      Quand l'entree est LE MANDAT COURANT du bien, on met le prix de l'annonce,
      comme le registre le fait depuis le lot 2. Sinon on EFFACE : l'annonce n'a
      qu'un prix, celui d'aujourd'hui, et il ne dit rien d'un mandat ancien.
      Mesure du 06/10 : 87 des 88 sont le mandat courant, 1 est un mandat
      ancien, et 1 des 87 porte sur une annonce sans prix -> effaces tous deux.
      ⚠ UN MONTANT EFFACE N'EST PAS UNE PERTE : il n'etait pas celui de ce bien.
    """
    if not numeros_suspects:
        return valeur, 0, 0
    items = safe_json_loads(valeur, None)
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        return valeur, 0, 0
    nos_noms = texte_des_mandants(mandants_du_bien or [])
    nos_jetons = jetons_de_nom(nos_noms) if nos_noms else set()
    prix = normalize_text(prix_annonce) or ""
    courant = normalize_text(numero_courant) or ""
    sortie: list[object] = []
    mandants_reecrits = montants_corriges = 0
    for item in items:
        if not isinstance(item, dict):
            sortie.append(item)
            continue
        numero = normalize_text(item.get("numero")) or ""
        if numero not in numeros_suspects:
            sortie.append(item)
            continue
        suivant = dict(item)
        ancien = str(item.get("mandants") or "").strip()
        # ① la meme personne ecrite autrement -> on garde le texte de Hektor
        if nos_noms and not (ancien and jetons_de_nom(ancien) & nos_jetons):
            suivant["mandants"] = nos_noms
            mandants_reecrits += 1
        if normalize_text(item.get("montant")):
            attendu = prix if (numero and numero == courant and prix) else ""
            if (normalize_text(item.get("montant")) or "") != attendu:
                suivant["montant"] = attendu or None
                montants_corriges += 1
        sortie.append(suivant)
    if not (mandants_reecrits or montants_corriges):
        return valeur, 0, 0
    return (json.dumps(sortie, ensure_ascii=False),
            mandants_reecrits, montants_corriges)


def build_trimmed_detail_payload(
    row: dict[str, object],
    mandants_par_annonce: dict[str, list[dict[str, object]]] | None = None,
    suspects_par_annonce: dict[str, set[str]] | None = None,
) -> dict[str, object]:
    detail_payload = {field: row.get(field, None) for field in DETAIL_PAYLOAD_FIELD_ORDER}
    for field, value in extract_api_detail_groups(detail_payload.get("detail_raw_json")).items():
        if compact_json_field(detail_payload.get(field)) is None:
            detail_payload[field] = value
    for field, value in build_dpe_image_urls_from_api_detail(detail_payload.get("detail_raw_json")).items():
        if value:
            detail_payload[field] = value
    detail_payload["images_json"] = trim_json_array_field(detail_payload.get("images_json"), limit=MAX_EXPORTED_IMAGES)
    detail_payload["images_preview_json"] = trim_json_array_field(
        detail_payload.get("images_preview_json"),
        limit=MAX_EXPORTED_IMAGES,
    )
    if DETAIL_MANDANTS_DEPUIS_NOS_LIENS and mandants_par_annonce is not None:
        annonce = normalize_text(row.get("hektor_annonce_id")) or ""
        blob, _, _ = mandats_json_corrige(
            detail_payload.get("mandats_json"),
            mandants_par_annonce.get(annonce),
            (suspects_par_annonce or {}).get(annonce),
            prix_annonce=row.get("prix"),
            numero_courant=row.get("numero_mandat"),
        )
        detail_payload["mandats_json"] = blob
    return detail_payload


def attach_price_change_summary(con: sqlite3.Connection, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_annonce = build_price_change_by_annonce(con, [row.get("hektor_annonce_id") for row in rows])
    enriched: list[dict[str, object]] = []
    for row in rows:
        next_row = dict(row)
        summary = by_annonce.get(str(row.get("hektor_annonce_id") or "").strip(), {})
        next_row["price_change_event_count"] = summary.get("price_change_event_count", 0)
        next_row["price_change_last_source_kind"] = summary.get("price_change_last_source_kind")
        next_row["price_change_last_old_value"] = summary.get("price_change_last_old_value")
        next_row["price_change_last_new_value"] = summary.get("price_change_last_new_value")
        next_row["price_change_last_detected_at"] = summary.get("price_change_last_detected_at")
        next_row["price_change_last_source_updated_at"] = summary.get("price_change_last_source_updated_at")
        next_row["price_change_events_json"] = summary.get("price_change_events_json")
        enriched.append(next_row)
    return enriched


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


def build_dossier_details(
    rows: list[dict[str, object]],
    mandants_par_annonce: dict[str, list[dict[str, object]]] | None = None,
    suspects_par_annonce: dict[str, set[str]] | None = None,
) -> list[dict[str, object]]:
    details: list[dict[str, object]] = []
    for row in rows:
        detail_payload = build_trimmed_detail_payload(
            row, mandants_par_annonce, suspects_par_annonce
        )
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
    connection: sqlite3.Connection | None = None,
) -> dict[str, object]:
    con = connection or sqlite_read_connection(PHASE2_DB)
    owns_connection = connection is None
    attached_hektor = False
    try:
        if owns_connection:
            attach_hektor_read(con)
            attached_hektor = True
        summary_cursor = con.execute(SQL_SUMMARY)
        summary_row = summary_cursor.fetchone()
        summary_cols = [col[0] for col in summary_cursor.description]
        dossier_rows = fetch_rows_by_ids(
            con,
            base_sql=SQL_DOSSIERS_BASE,
            id_column="app_dossier_id",
            ids=dossier_ids,
            limit=limit,
        )
        dossier_rows = enrich_offer_transaction_fields(con, dossier_rows)
        dossier_rows = attach_price_change_summary(con, dossier_rows)
        dossier_rows = attach_console_missing_fields(con, dossier_rows)
        dossiers = attach_detail_payload(dossier_rows)
        # 06/10 : la fiche annonce reprend ses mandants chez nous sur les seuls corps
        # empruntes (voir le bloc au-dessus de `mandats_json_corrige`).
        # Cout mesure le 06/10 : 3,3 s pour la carte des liens.
        # ⚠ L'ORDRE N'EST PAS INDIFFERENT. Les corps empruntes coutent 0,09 s, la
        #   carte des liens 2,82 s (mesure du 06/10). Le CHEMIN IMMEDIAT appelle
        #   cette fonction pour UNE annonce apres chaque saisie : lui imposer
        #   2,8 s pour une carte dont il n'a presque jamais besoin serait une
        #   regression ressentie. On ne la charge donc que si au moins une des
        #   annonces servies porte un corps emprunte.
        mandants_fiche: dict[str, list[dict[str, object]]] | None = None
        suspects_fiche: dict[str, set[str]] | None = None
        if DETAIL_MANDANTS_DEPUIS_NOS_LIENS:
            suspects_fiche = defaultdict(set)
            for annonce_suspecte, numero_suspect in charger_corps_suspects(con):
                suspects_fiche[annonce_suspecte].add(numero_suspect)
            if any(
                (normalize_text(row.get("hektor_annonce_id")) or "") in suspects_fiche
                for row in dossier_rows
            ):
                mandants_fiche = charger_mandants_du_registre_des_liens(con)
        dossier_details = build_dossier_details(
            dossier_rows, mandants_fiche, suspects_fiche
        )
        work_items = fetch_rows_by_ids(
            con,
            base_sql=SQL_WORK_ITEMS_BASE,
            id_column="app_dossier_id",
            ids=dossier_ids,
            limit=limit,
        )
        mandat_register_rows = build_mandat_register_rows(con, limit=limit, dossier_ids=dossier_ids)
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
        if attached_hektor:
            try:
                con.execute("DETACH DATABASE hektor")
            except sqlite3.Error:
                pass
        if owns_connection:
            con.close()

    return payload


def build_archive_annonce_index(
    *,
    limit: int | None = None,
    connection: sqlite3.Connection | None = None,
) -> list[dict[str, object]]:
    con = connection or sqlite_read_connection(PHASE2_DB)
    owns_connection = connection is None
    try:
        return fetch_rows(con, build_limited_sql(SQL_ARCHIVE_ANNONCE_INDEX_BASE, limit))
    finally:
        if owns_connection:
            con.close()


def build_historical_annonce_index(
    *,
    limit: int | None = None,
    connection: sqlite3.Connection | None = None,
) -> list[dict[str, object]]:
    con = connection or sqlite_read_connection(PHASE2_DB)
    owns_connection = connection is None
    try:
        return fetch_rows(con, build_limited_sql(SQL_HISTORICAL_ANNONCE_INDEX_BASE, limit))
    finally:
        if owns_connection:
            con.close()


def load_brouillon_draft_ids() -> list[int]:
    """Ids Hektor des annonces brouillon (isDraft=1) depuis le store local hektor.hektor_annonce_draft_state.
    Retourne [] si la table n'existe pas encore -> builder inerte."""
    con = sqlite_read_connection(HEKTOR_DB)
    try:
        has_table = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='hektor_annonce_draft_state'"
        ).fetchone()
        if not has_table:
            return []
        rows = con.execute(
            "SELECT hektor_annonce_id FROM hektor_annonce_draft_state WHERE COALESCE(is_draft, 0) = 1"
        ).fetchall()
        ids: list[int] = []
        for row in rows:
            value = str(row[0]).strip()
            if value.isdigit():
                ids.append(int(value))
        return ids
    finally:
        con.close()


def build_brouillon_annonce_index(
    *,
    limit: int | None = None,
    connection: sqlite3.Connection | None = None,
) -> list[dict[str, object]]:
    if not BROUILLON_BUCKET_ENABLED:
        return []
    ids = load_brouillon_draft_ids()
    if not ids:
        return []
    con = connection or sqlite_read_connection(PHASE2_DB)
    owns_connection = connection is None
    try:
        in_list = ",".join(str(value) for value in ids)
        sql = SQL_BROUILLON_ANNONCE_INDEX_BASE.replace("__BROUILLON_IDS__", in_list)
        return fetch_rows(con, build_limited_sql(sql, limit))
    finally:
        if owns_connection:
            con.close()


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
