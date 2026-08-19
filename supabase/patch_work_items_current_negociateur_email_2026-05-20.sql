-- Expose negociateur_email in app_work_items_current for commercial scoped CRM screens.

create or replace view public.app_work_items_current
with (security_invoker=on) as
select
    w.app_dossier_id,
    w.hektor_annonce_id,
    w.archive,
    w.numero_dossier,
    w.numero_mandat,
    w.titre_bien,
    w.commercial_nom,
    d.negociateur_email,
    d.agence_nom,
    w.type_demande_label,
    w.work_status,
    w.internal_status,
    w.priority,
    w.validation_diffusion_state,
    w.etat_visibilite,
    w.motif_blocage,
    w.has_open_blocker,
    w.next_action,
    w.date_relance_prevue,
    w.date_entree_file,
    w.date_derniere_action,
    w.age_jours
from public.app_work_item_current w
left join public.app_dossier_current d
    on d.app_dossier_id = w.app_dossier_id
where exists (select 1 from public.app_delta_run where scope = 'annonces_current' and status = 'completed')
union all
select
    w.app_dossier_id,
    w.hektor_annonce_id,
    w.archive,
    w.numero_dossier,
    w.numero_mandat,
    w.titre_bien,
    w.commercial_nom,
    d.negociateur_email,
    d.agence_nom,
    w.type_demande_label,
    w.work_status,
    w.internal_status,
    w.priority,
    w.validation_diffusion_state,
    w.etat_visibilite,
    w.motif_blocage,
    w.has_open_blocker,
    w.next_action,
    w.date_relance_prevue,
    w.date_entree_file,
    w.date_derniere_action,
    w.age_jours
from public.app_work_item_v1 w
join public.app_latest_sync_run r on r.id = w.sync_run_id
left join public.app_dossier_v1 d
    on d.app_dossier_id = w.app_dossier_id
   and d.sync_run_id = w.sync_run_id
where not exists (select 1 from public.app_delta_run where scope = 'annonces_current' and status = 'completed');
