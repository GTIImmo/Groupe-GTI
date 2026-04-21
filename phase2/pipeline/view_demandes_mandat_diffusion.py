from __future__ import annotations

from phase2.pipeline.view_common import (
    SQL_ETAT_VISIBILITE,
    SQL_TYPE_DEMANDE_LABEL,
    SQL_VALIDATION_DIFFUSION_DEMANDES,
)
from phase2.rules.status_rules import WORKFLOW_MANDAT_DIFFUSION


SQL_REFRESH_DEMANDES_MANDAT_DIFFUSION = f"""
DROP TABLE IF EXISTS app_view_demandes_mandat_diffusion;

CREATE TABLE app_view_demandes_mandat_diffusion AS
WITH latest_admin_note AS (
    SELECT n.app_dossier_id, n.content AS commentaire_admin_resume, n.created_at AS note_created_at
    FROM app_note n
    INNER JOIN (
        SELECT app_dossier_id, MAX(created_at) AS max_created_at
        FROM app_note
        WHERE note_type IN ('admin', 'general')
        GROUP BY app_dossier_id
    ) x ON x.app_dossier_id = n.app_dossier_id AND x.max_created_at = n.created_at
),
open_blocker AS (
    SELECT b.app_dossier_id, 1 AS has_open_blocker, GROUP_CONCAT(b.blocker_type, ', ') AS motif_blocage
    FROM app_blocker b
    WHERE b.status = 'open'
    GROUP BY b.app_dossier_id
),
broadcast_agg AS (
    SELECT
        s.hektor_annonce_id,
        SUM(CASE WHEN s.current_state = 'broadcasted' THEN 1 ELSE 0 END) AS nb_portails_actifs,
        MAX(CASE WHEN s.is_error = 1 THEN 1 ELSE 0 END) AS has_diffusion_error
    FROM hektor.hektor_annonce_broadcast_state s
    GROUP BY s.hektor_annonce_id
),
latest_followup AS (
    SELECT f.app_dossier_id, MAX(f.planned_for) AS date_relance_prevue
    FROM app_followup f
    WHERE COALESCE(f.result_status, 'pending') = 'pending'
    GROUP BY f.app_dossier_id
)
SELECT
    d.id AS app_dossier_id,
    d.hektor_annonce_id,
    src.mandat_id AS hektor_mandat_id,
    src.mandat_id AS mandat_source_id,
    src.no_dossier AS numero_dossier,
    src.no_mandat AS numero_mandat,
    src.no_mandat AS mandat_numero_reference,
    COALESCE(NULLIF(TRIM(ann.titre), ''), CASE WHEN COALESCE(src.no_dossier, '') <> '' THEN '[Sans titre] ' || src.no_dossier ELSE '[Sans titre]' END) AS titre_bien,
    ann.ville,
    ann.idtype AS type_bien,
    src.prix AS prix_affiche,
    src.archive,
    src.hektor_negociateur_id AS commercial_id,
    TRIM(COALESCE(src.negociateur_prenom, '') || ' ' || COALESCE(src.negociateur_nom, '')) AS commercial_nom,
    wi.workflow_type,
    wi.event_type,
    {SQL_TYPE_DEMANDE_LABEL} AS type_demande_label,
    wi.status AS work_status,
    COALESCE(ist.internal_status, 'a_controler') AS internal_status,
    COALESCE(ist.priority, wi.priority, 'normal') AS priority,
    src.diffusable,
    {SQL_VALIDATION_DIFFUSION_DEMANDES} AS validation_diffusion_state,
    {SQL_ETAT_VISIBILITE} AS etat_visibilite,
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
INNER JOIN app_dossier d ON d.id = wi.app_dossier_id
LEFT JOIN hektor.case_dossier_source src ON src.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
LEFT JOIN hektor.hektor_annonce ann ON ann.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
LEFT JOIN app_internal_status ist ON ist.app_dossier_id = d.id
LEFT JOIN latest_admin_note lan ON lan.app_dossier_id = d.id
LEFT JOIN open_blocker ob ON ob.app_dossier_id = d.id
LEFT JOIN broadcast_agg ba ON ba.hektor_annonce_id = CAST(d.hektor_annonce_id AS TEXT)
LEFT JOIN latest_followup lf ON lf.app_dossier_id = d.id
WHERE wi.workflow_type = '__WORKFLOW_MANDAT_DIFFUSION__'
  AND wi.status IN ('new', 'pending', 'in_progress', 'refused');

CREATE INDEX idx_view_dmd_priority ON app_view_demandes_mandat_diffusion(priority);
CREATE INDEX idx_view_dmd_status ON app_view_demandes_mandat_diffusion(work_status, validation_diffusion_state);
CREATE INDEX idx_view_dmd_commercial ON app_view_demandes_mandat_diffusion(commercial_id);
""".replace("__WORKFLOW_MANDAT_DIFFUSION__", WORKFLOW_MANDAT_DIFFUSION)
