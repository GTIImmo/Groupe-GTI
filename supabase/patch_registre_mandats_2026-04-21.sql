alter table public.app_dossier_v1
add column if not exists adresse_privee_listing text;

alter table public.app_dossier_v1
add column if not exists adresse_detail text;

alter table public.app_dossier_v1
add column if not exists code_postal text;

alter table public.app_dossier_v1
add column if not exists code_postal_prive_detail text;

alter table public.app_dossier_v1
add column if not exists ville_privee_detail text;

alter table public.app_dossier_v1
add column if not exists mandat_type text;

alter table public.app_dossier_v1
add column if not exists mandat_type_source text;

alter table public.app_dossier_v1
add column if not exists mandat_date_debut text;

alter table public.app_dossier_v1
add column if not exists mandat_date_fin text;

alter table public.app_dossier_v1
add column if not exists mandat_montant numeric;

alter table public.app_dossier_v1
add column if not exists mandants_texte text;

alter table public.app_dossier_current
add column if not exists adresse_privee_listing text;

alter table public.app_dossier_current
add column if not exists adresse_detail text;

alter table public.app_dossier_current
add column if not exists code_postal text;

alter table public.app_dossier_current
add column if not exists code_postal_prive_detail text;

alter table public.app_dossier_current
add column if not exists ville_privee_detail text;

alter table public.app_dossier_current
add column if not exists mandat_type text;

alter table public.app_dossier_current
add column if not exists mandat_type_source text;

alter table public.app_dossier_current
add column if not exists mandat_date_debut text;

alter table public.app_dossier_current
add column if not exists mandat_date_fin text;

alter table public.app_dossier_current
add column if not exists mandat_montant numeric;

alter table public.app_dossier_current
add column if not exists mandants_texte text;

create or replace view public.app_dossiers_current
with (security_invoker=on) as
select
    d.app_dossier_id,
    d.hektor_annonce_id,
    d.archive,
    d.diffusable,
    d.adresse_privee_listing,
    d.adresse_detail,
    d.code_postal,
    d.code_postal_prive_detail,
    d.ville_privee_detail,
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
    d.mandat_type,
    d.mandat_type_source,
    d.mandat_date_debut,
    d.mandat_date_fin,
    d.mandat_montant,
    d.mandants_texte,
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
    d.adresse_privee_listing,
    d.adresse_detail,
    d.code_postal,
    d.code_postal_prive_detail,
    d.ville_privee_detail,
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
    d.mandat_type,
    d.mandat_type_source,
    d.mandat_date_debut,
    d.mandat_date_fin,
    d.mandat_montant,
    d.mandants_texte,
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
