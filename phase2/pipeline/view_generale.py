from __future__ import annotations

from phase2.pipeline.view_common import (
    SQL_ALERTE_PRINCIPALE,
    SQL_ETAT_VISIBILITE,
    SQL_VALIDATION_DIFFUSION_GENERALE,
)


# Cette vue reste volumineuse; elle est sortie de refresh_views.py pour isoler le SQL metier.
SQL_REFRESH_VUE_GENERALE = """
DROP TABLE IF EXISTS app_view_generale;

CREATE TABLE app_view_generale AS
WITH latest_note AS (
    SELECT
        n.app_dossier_id,
        n.content AS commentaire_resume
    FROM app_note n
    INNER JOIN (
        SELECT
            app_dossier_id,
            MAX(created_at) AS max_created_at
        FROM app_note
        GROUP BY app_dossier_id
    ) x
        ON x.app_dossier_id = n.app_dossier_id
       AND x.max_created_at = n.created_at
),
open_blocker AS (
    SELECT
        b.app_dossier_id,
        1 AS has_open_blocker,
        GROUP_CONCAT(b.blocker_type, ', ') AS motif_blocage
    FROM app_blocker b
    WHERE b.status = 'open'
    GROUP BY b.app_dossier_id
),
broadcast_agg AS (
    SELECT
        s.hektor_annonce_id,
        SUM(CASE WHEN s.current_state = 'broadcasted' THEN 1 ELSE 0 END) AS nb_portails_actifs,
        MAX(CASE WHEN s.is_error = 1 THEN 1 ELSE 0 END) AS has_diffusion_error,
        GROUP_CONCAT(CASE WHEN s.current_state = 'broadcasted' THEN s.passerelle_key END, ', ') AS portails_resume
    FROM hektor.hektor_annonce_broadcast_state s
    GROUP BY s.hektor_annonce_id
),
latest_followup AS (
    SELECT
        f.app_dossier_id,
        MAX(f.planned_for) AS date_relance_prevue
    FROM app_followup f
    WHERE COALESCE(f.result_status, 'pending') = 'pending'
    GROUP BY f.app_dossier_id
),
detail_enrich AS (
    SELECT
        det.hektor_annonce_id,
        det.statut_name AS detail_statut_name,
        det.localite_json,
        det.mandats_json,
        det.proprietaires_json,
        det.honoraires_json,
        det.notes_json,
        det.zones_json,
        det.particularites_json,
        det.pieces_json,
        det.images_json,
        det.textes_json,
        det.terrain_json,
        det.copropriete_json,
        det.raw_json AS detail_raw_json,
        json_extract(det.localite_json, '$.publique.code') AS code_postal_detail,
        json_extract(det.localite_json, '$.publique.latitude') AS latitude_detail,
        json_extract(det.localite_json, '$.publique.longitude') AS longitude_detail,
        json_extract(det.localite_json, '$.privee.adresse') AS adresse_detail,
        json_extract(det.localite_json, '$.privee.ville') AS ville_privee_detail,
        json_extract(det.localite_json, '$.privee.code') AS code_postal_prive_detail,
        COALESCE(json_array_length(det.images_json), 0) AS nb_images,
        COALESCE(json_array_length(det.textes_json), 0) AS nb_textes,
        COALESCE(json_array_length(det.notes_json), 0) AS nb_notes_hektor,
        COALESCE(json_array_length(det.proprietaires_json), 0) AS nb_proprietaires,
        (
            SELECT json_group_array(
                json_object(
                    'url', COALESCE(json_extract(j.value, '$.pathTumb'), json_extract(j.value, '$.path')),
                    'full', json_extract(j.value, '$.path'),
                    'legend', json_extract(j.value, '$.legende'),
                    'order', json_extract(j.value, '$.order')
                )
            )
            FROM (
                SELECT value
                FROM json_each(det.images_json)
                ORDER BY CAST(COALESCE(json_extract(value, '$.order'), '9999') AS INTEGER)
                LIMIT 12
            ) j
        ) AS images_preview_json,
        json_extract(det.textes_json, '$[0].titre') AS texte_principal_titre,
        json_extract(det.textes_json, '$[0].text') AS texte_principal_html,
        json_extract(det.raw_json, '$.ag_interieur.props.nbpieces.value') AS nb_pieces,
        json_extract(det.raw_json, '$.ag_interieur.props.NB_CHAMBRES.value') AS nb_chambres,
        json_extract(det.raw_json, '$.ag_interieur.props.surfappart.value') AS surface_habitable_detail,
        json_extract(det.raw_json, '$.ag_exterieur.props.ETAGE.value') AS etage_detail,
        json_extract(det.raw_json, '$.ag_exterieur.props.TERRASSE.value') AS terrasse_detail,
        json_extract(det.raw_json, '$.ag_exterieur.props.GARAGE_BOX.value') AS garage_box_detail,
        json_extract(det.raw_json, '$.terrain.props.surfterrain.value') AS surface_terrain_detail,
        json_extract(det.raw_json, '$.copropriete.props.copropriete.value') AS copropriete_detail,
        json_extract(det.raw_json, '$.equipements.props.ASCENSEUR.value') AS ascenseur_detail,
        (
            SELECT GROUP_CONCAT(
                TRIM(COALESCE(json_extract(j.value, '$.prenom'), '') || ' ' || COALESCE(json_extract(j.value, '$.nom'), '')),
                ' | '
            )
            FROM json_each(det.proprietaires_json) j
        ) AS proprietaires_resume,
        (
            SELECT GROUP_CONCAT(
                TRIM(
                    COALESCE(json_extract(j.value, '$.coordonnees.portable'), '') ||
                    CASE
                        WHEN COALESCE(json_extract(j.value, '$.coordonnees.portable'), '') <> ''
                             AND COALESCE(json_extract(j.value, '$.coordonnees.email'), '') <> ''
                        THEN ' · '
                        ELSE ''
                    END ||
                    COALESCE(json_extract(j.value, '$.coordonnees.email'), '')
                ),
                ' | '
            )
            FROM json_each(det.proprietaires_json) j
        ) AS proprietaires_contacts,
        (
            SELECT GROUP_CONCAT(
                TRIM(
                    COALESCE(json_extract(j.value, '$.charge'), '') ||
                    CASE
                        WHEN COALESCE(json_extract(j.value, '$.charge'), '') <> ''
                             AND COALESCE(json_extract(j.value, '$.taux'), '') <> ''
                        THEN ' '
                        ELSE ''
                    END ||
                    COALESCE(json_extract(j.value, '$.taux'), '')
                ),
                ' | '
            )
            FROM json_each(det.honoraires_json) j
        ) AS honoraires_resume,
        json_extract(det.notes_json, '$[0].content') AS note_hektor_principale
    FROM hektor.hektor_annonce_detail det
),
latest_work_item AS (
    SELECT
        wi.app_dossier_id,
        wi.workflow_type,
        wi.event_type,
        wi.status,
        wi.priority,
        wi.reason,
        wi.detected_at,
        wi.updated_at
    FROM app_work_item wi
    INNER JOIN (
        SELECT
            app_dossier_id,
            MAX(COALESCE(updated_at, created_at)) AS max_updated_at
        FROM app_work_item
        GROUP BY app_dossier_id
    ) x
        ON x.app_dossier_id = wi.app_dossier_id
       AND x.max_updated_at = COALESCE(wi.updated_at, wi.created_at)
)
SELECT
    d.id AS app_dossier_id,
    d.hektor_annonce_id,
    src.no_dossier AS numero_dossier,
    src.no_mandat AS numero_mandat,
    COALESCE(
        NULLIF(TRIM(ann.titre), ''),
        NULLIF(TRIM(det.texte_principal_titre), ''),
        CASE
            WHEN COALESCE(src.no_dossier, '') <> '' THEN '[Sans titre] ' || src.no_dossier
            ELSE '[Sans titre]'
        END
    ) AS titre_bien,
    ann.ville,
    ann.code_postal,
    ann.idtype AS type_bien,
    src.prix,
    ann.surface,
    ann.date_maj,
    json_extract(ann.raw_json, '$.dateenr') AS date_enregistrement_annonce,
    ann.offre_type,
    ann.partage,
    json_extract(ann.raw_json, '$.photo') AS photo_url_listing,
    json_extract(ann.raw_json, '$.corps') AS corps_listing_html,
    json_extract(ann.raw_json, '$.localite.publique.ville') AS ville_publique_listing,
    json_extract(ann.raw_json, '$.localite.publique.code') AS code_postal_public_listing,
    json_extract(ann.raw_json, '$.localite.privee.adresse') AS adresse_privee_listing,
    ann.raw_json AS annonce_list_raw_json,
    src.hektor_negociateur_id AS commercial_id,
    TRIM(COALESCE(src.negociateur_prenom, '') || ' ' || COALESCE(src.negociateur_nom, '')) AS commercial_nom,
    src.negociateur_email AS negociateur_email,
    ag.nom AS agence_nom,
    CASE
        WHEN TRIM(COALESCE(src.negociateur_prenom, '') || ' ' || COALESCE(src.negociateur_nom, '')) <> '' THEN
            TRIM(COALESCE(src.negociateur_prenom, '') || ' ' || COALESCE(src.negociateur_nom, ''))
        WHEN COALESCE(ag.nom, '') <> '' THEN ag.nom
        ELSE ''
    END AS responsable_affichage,
    CASE
        WHEN TRIM(COALESCE(src.negociateur_prenom, '') || ' ' || COALESCE(src.negociateur_nom, '')) <> '' THEN 'negociateur'
        WHEN COALESCE(ag.nom, '') <> '' THEN 'agence'
        ELSE 'non_attribue'
    END AS responsable_type,
    src.statut_name AS statut_annonce,
    src.archive,
    src.diffusable,
    src.valide,
    src.mandat_type,
    src.mandat_date_debut,
    src.mandat_date_fin,
    src.mandat_date_cloture,
    m.numero AS mandat_numero_source,
    m.type AS mandat_type_source,
    m.date_enregistrement AS mandat_date_enregistrement,
    m.montant AS mandat_montant,
    m.mandants_texte,
    m.note AS mandat_note,
    __SQL_VALIDATION_DIFFUSION_GENERALE__ AS validation_diffusion_state,
    __SQL_ETAT_VISIBILITE__ AS etat_visibilite,
    COALESCE(ba.nb_portails_actifs, 0) AS nb_portails_actifs,
    COALESCE(ba.has_diffusion_error, 0) AS has_diffusion_error,
    COALESCE(ba.portails_resume, '') AS portails_resume,
    src.offre_id,
    off.offre_state,
    off.offre_event_date,
    off.raw_status AS offre_raw_status,
    off.raw_montant AS offre_montant,
    TRIM(COALESCE(off.prenom, '') || ' ' || COALESCE(off.nom, '')) AS offre_acquereur_nom,
    json_extract(off.acquereur_json, '$.coordonnees.portable') AS offre_acquereur_portable,
    json_extract(off.acquereur_json, '$.coordonnees.email') AS offre_acquereur_email,
    src.compromis_id,
    cmp.compromis_state,
    cmp.date_start AS compromis_date_start,
    cmp.date_end AS compromis_date_end,
    cmp.date_signature_acte,
    cmp.prix_net_vendeur,
    cmp.prix_publique,
    cmp.part_admin AS compromis_part_admin,
    cmp.sequestre AS compromis_sequestre,
    (
        SELECT GROUP_CONCAT(
            TRIM(COALESCE(json_extract(j.value, '$.prenom'), '') || ' ' || COALESCE(json_extract(j.value, '$.nom'), '')),
            ' | '
        )
        FROM json_each(cmp.acquereurs_json) j
    ) AS compromis_acquereurs_resume,
    src.vente_id,
    src.vente_date,
    v.prix AS vente_prix,
    v.honoraires AS vente_honoraires,
    v.part_admin AS vente_part_admin,
    v.commission_agence AS vente_commission_agence,
    (
        SELECT GROUP_CONCAT(
            TRIM(COALESCE(json_extract(j.value, '$.prenom'), '') || ' ' || COALESCE(json_extract(j.value, '$.nom'), '')),
            ' | '
        )
        FROM json_each(v.acquereurs_json) j
    ) AS vente_acquereurs_resume,
    (
        SELECT GROUP_CONCAT(
            TRIM(COALESCE(json_extract(j.value, '$.nom'), '') || ' ' || COALESCE(json_extract(j.value, '$.prenom'), '')),
            ' | '
        )
        FROM json_each(v.notaires_json) j
    ) AS vente_notaires_resume,
    det.detail_statut_name,
    det.localite_json,
    det.mandats_json,
    det.proprietaires_json,
    det.honoraires_json,
    det.notes_json,
    det.zones_json,
    det.particularites_json,
    det.pieces_json,
    det.images_json,
    det.textes_json,
    det.terrain_json,
    det.copropriete_json,
    det.detail_raw_json,
    det.code_postal_detail,
    det.latitude_detail,
    det.longitude_detail,
    det.adresse_detail,
    det.ville_privee_detail,
    det.code_postal_prive_detail,
    det.nb_images,
    det.nb_textes,
    det.nb_notes_hektor,
    det.nb_proprietaires,
    det.images_preview_json,
    det.texte_principal_titre,
    det.texte_principal_html,
    det.nb_pieces,
    det.nb_chambres,
    det.surface_habitable_detail,
    det.etage_detail,
    det.terrasse_detail,
    det.garage_box_detail,
    det.surface_terrain_detail,
    det.copropriete_detail,
    det.ascenseur_detail,
    det.proprietaires_resume,
    det.proprietaires_contacts,
    det.honoraires_resume,
    det.note_hektor_principale,
    CASE
        WHEN src.vente_id IS NOT NULL THEN 'vente_en_cours'
        WHEN src.compromis_id IS NOT NULL THEN 'compromis_en_cours'
        WHEN src.offre_id IS NOT NULL THEN 'offre_en_cours'
        ELSE 'sans_transaction'
    END AS etat_transaction,
    COALESCE(ist.internal_status, 'a_qualifier') AS internal_status,
    COALESCE(ist.priority, lwi.priority, 'normal') AS priority,
    COALESCE(ob.has_open_blocker, 0) AS has_open_blocker,
    ob.motif_blocage,
    ist.next_action,
    lf.date_relance_prevue,
    COALESCE(ln.commentaire_resume, '') AS commentaire_resume,
    lwi.workflow_type AS dernier_workflow_type,
    lwi.event_type AS dernier_event_type,
    lwi.status AS dernier_work_status,
    lwi.detected_at AS date_entree_file,
    lwi.updated_at AS date_derniere_action,
    __SQL_ALERTE_PRINCIPALE__ AS alerte_principale,
    COALESCE(ob.has_open_blocker, 0) AS is_blocked,
    CASE
        WHEN lf.date_relance_prevue IS NOT NULL
             AND lf.date_relance_prevue <= date('now') THEN 1
        ELSE 0
    END AS is_followup_needed
FROM app_dossier d
LEFT JOIN hektor.case_dossier_source src ON src.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
LEFT JOIN hektor.hektor_annonce ann ON ann.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
LEFT JOIN hektor.hektor_agence ag ON ag.hektor_agence_id = src.hektor_agence_id
LEFT JOIN hektor.hektor_mandat m ON m.hektor_mandat_id = src.mandat_id
LEFT JOIN hektor.hektor_offre off ON off.hektor_offre_id = src.offre_id
LEFT JOIN hektor.hektor_compromis cmp ON cmp.hektor_compromis_id = src.compromis_id
LEFT JOIN hektor.hektor_vente v ON v.hektor_vente_id = src.vente_id
LEFT JOIN detail_enrich det ON det.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
LEFT JOIN app_internal_status ist ON ist.app_dossier_id = d.id
LEFT JOIN latest_note ln ON ln.app_dossier_id = d.id
LEFT JOIN open_blocker ob ON ob.app_dossier_id = d.id
LEFT JOIN broadcast_agg ba ON ba.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
LEFT JOIN latest_followup lf ON lf.app_dossier_id = d.id
LEFT JOIN latest_work_item lwi ON lwi.app_dossier_id = d.id;

CREATE INDEX idx_view_generale_commercial ON app_view_generale(commercial_id);
CREATE INDEX idx_view_generale_diffusion ON app_view_generale(validation_diffusion_state, etat_visibilite);
"""

SQL_REFRESH_VUE_GENERALE = (
    SQL_REFRESH_VUE_GENERALE
    .replace("__SQL_VALIDATION_DIFFUSION_GENERALE__", SQL_VALIDATION_DIFFUSION_GENERALE)
    .replace("__SQL_ETAT_VISIBILITE__", SQL_ETAT_VISIBILITE)
    .replace("__SQL_ALERTE_PRINCIPALE__", SQL_ALERTE_PRINCIPALE)
)
