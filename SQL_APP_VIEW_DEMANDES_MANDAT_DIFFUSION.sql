CREATE VIEW app_view_demandes_mandat_diffusion AS
WITH latest_admin_note AS (
    SELECT
        n.app_dossier_id,
        n.content AS commentaire_admin_resume,
        n.created_at AS note_created_at
    FROM app_note n
    INNER JOIN (
        SELECT
            app_dossier_id,
            MAX(created_at) AS max_created_at
        FROM app_note
        WHERE note_type IN ('admin', 'general')
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
        MAX(CASE WHEN s.is_error = 1 THEN 1 ELSE 0 END) AS has_diffusion_error
    FROM hektor_annonce_broadcast_state s
    GROUP BY s.hektor_annonce_id
),
latest_followup AS (
    SELECT
        f.app_dossier_id,
        MAX(f.planned_for) AS date_relance_prevue
    FROM app_followup f
    WHERE COALESCE(f.result_status, 'pending') = 'pending'
    GROUP BY f.app_dossier_id
)
SELECT
    d.id AS app_dossier_id,
    d.hektor_annonce_id,
    src.mandat_id AS hektor_mandat_id,
    src.no_dossier AS numero_dossier,
    src.no_mandat AS numero_mandat,
    ann.titre AS titre_bien,
    ann.ville,
    ann.idtype AS type_bien,
    src.prix AS prix_affiche,
    src.archive,
    src.hektor_negociateur_id AS commercial_id,
    TRIM(COALESCE(src.negociateur_prenom, '') || ' ' || COALESCE(src.negociateur_nom, '')) AS commercial_nom,
    wi.workflow_type,
    wi.event_type,
    CASE wi.event_type
        WHEN 'demande_diffusion' THEN 'Demande diffusion'
        WHEN 'baisse_prix' THEN 'Avenant baisse prix'
        WHEN 'annulation_mandat' THEN 'Annulation mandat'
        WHEN 'mandat_non_diffuse' THEN 'Mandat non diffuse'
        WHEN 'bien_non_visible' THEN 'Bien non visible'
        WHEN 'piece_manquante' THEN 'Piece manquante'
        WHEN 'donnee_incomplete' THEN 'Donnee incomplete'
        ELSE wi.event_type
    END AS type_demande_label,
    wi.status AS work_status,
    COALESCE(ist.internal_status, 'a_controler') AS internal_status,
    COALESCE(ist.priority, wi.priority, 'normal') AS priority,
    src.diffusable,
    CASE
        WHEN wi.status = 'refused' THEN 'refuse'
        WHEN COALESCE(ist.internal_status, '') = 'en_attente_commercial' THEN 'en_attente_commercial'
        WHEN COALESCE(ist.internal_status, '') = 'pret_diffusion' THEN 'valide'
        ELSE 'a_controler'
    END AS validation_diffusion_state,
    CASE
        WHEN COALESCE(src.diffusable, '0') <> '1' THEN 'non_diffusable'
        WHEN COALESCE(ba.has_diffusion_error, 0) = 1 THEN 'en_erreur'
        WHEN COALESCE(ba.nb_portails_actifs, 0) > 0 THEN 'visible'
        WHEN COALESCE(src.diffusable, '0') = '1' AND COALESCE(ba.nb_portails_actifs, 0) = 0 THEN 'diffusable_non_visible'
        ELSE 'a_verifier'
    END AS etat_visibilite,
    COALESCE(ba.nb_portails_actifs, 0) AS nb_portails_actifs,
    COALESCE(ba.has_diffusion_error, 0) AS has_diffusion_error,
    COALESCE(ob.motif_blocage, wi.reason) AS motif_blocage,
    COALESCE(ob.has_open_blocker, 0) AS has_open_blocker,
    ist.next_action,
    ist.last_action_note,
    lf.date_relance_prevue,
    wi.detected_at AS date_entree_file,
    wi.updated_at AS date_derniere_action,
    CAST(julianday('now') - julianday(COALESCE(wi.detected_at, wi.created_at)) AS INTEGER) AS age_jours,
    lan.commentaire_admin_resume
FROM app_work_item wi
INNER JOIN app_dossier d
    ON d.id = wi.app_dossier_id
LEFT JOIN case_dossier_source src
    ON src.hektor_annonce_id = d.hektor_annonce_id
LEFT JOIN hektor_annonce ann
    ON ann.hektor_annonce_id = d.hektor_annonce_id
LEFT JOIN app_internal_status ist
    ON ist.app_dossier_id = d.id
LEFT JOIN latest_admin_note lan
    ON lan.app_dossier_id = d.id
LEFT JOIN open_blocker ob
    ON ob.app_dossier_id = d.id
LEFT JOIN broadcast_agg ba
    ON ba.hektor_annonce_id = d.hektor_annonce_id
LEFT JOIN latest_followup lf
    ON lf.app_dossier_id = d.id
WHERE wi.workflow_type = 'mandat_diffusion'
  AND wi.status IN ('new', 'pending', 'in_progress', 'refused')
ORDER BY
    CASE COALESCE(ist.priority, wi.priority, 'normal')
        WHEN 'urgent' THEN 4
        WHEN 'high' THEN 3
        WHEN 'normal' THEN 2
        WHEN 'low' THEN 1
        ELSE 0
    END DESC,
    age_jours DESC,
    wi.detected_at ASC;
