alter table public.app_dossier_v1
add column if not exists agence_nom text;

alter table public.app_dossier_current
add column if not exists agence_nom text;

alter table public.app_dossier_v1
add column if not exists offre_state text;

alter table public.app_dossier_v1
add column if not exists compromis_state text;

alter table public.app_dossier_v1
add column if not exists offre_last_proposition_type text;

alter table public.app_dossier_current
add column if not exists offre_state text;

alter table public.app_dossier_current
add column if not exists compromis_state text;

alter table public.app_dossier_current
add column if not exists offre_last_proposition_type text;

create or replace view public.app_dossiers_current
with (security_invoker=on) as
select
    d.app_dossier_id,
    d.hektor_annonce_id,
    d.archive,
    d.diffusable,
    d.nb_portails_actifs,
    d.has_diffusion_error,
    d.portails_resume,
    d.offre_id,
    d.offre_state,
    d.compromis_id,
    d.compromis_state,
    d.vente_id,
    d.numero_dossier,
    d.numero_mandat,
    d.titre_bien,
    d.ville,
    d.type_bien,
    d.prix,
    d.commercial_id,
    d.commercial_nom,
    d.negociateur_email,
    d.agence_nom,
    d.statut_annonce,
    d.validation_diffusion_state,
    d.etat_visibilite,
    d.alerte_principale,
    d.priority,
    d.has_open_blocker,
    d.commentaire_resume,
    d.date_relance_prevue,
    d.dernier_event_type,
    d.dernier_work_status,
    d.offre_last_proposition_type
from public.app_dossier_current d
where exists (select 1 from public.app_delta_run where scope = 'annonces_current' and status = 'completed')
union all
select
    d.app_dossier_id,
    d.hektor_annonce_id,
    d.archive,
    d.diffusable,
    d.nb_portails_actifs,
    d.has_diffusion_error,
    d.portails_resume,
    d.offre_id,
    d.offre_state,
    d.compromis_id,
    d.compromis_state,
    d.vente_id,
    d.numero_dossier,
    d.numero_mandat,
    d.titre_bien,
    d.ville,
    d.type_bien,
    d.prix,
    d.commercial_id,
    d.commercial_nom,
    d.negociateur_email,
    d.agence_nom,
    d.statut_annonce,
    d.validation_diffusion_state,
    d.etat_visibilite,
    d.alerte_principale,
    d.priority,
    d.has_open_blocker,
    d.commentaire_resume,
    d.date_relance_prevue,
    d.dernier_event_type,
    d.dernier_work_status,
    d.offre_last_proposition_type
from public.app_dossier_v1 d
join public.app_latest_sync_run r on r.id = d.sync_run_id
where not exists (select 1 from public.app_delta_run where scope = 'annonces_current' and status = 'completed');
