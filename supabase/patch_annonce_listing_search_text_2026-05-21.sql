create extension if not exists pg_trgm;

alter table public.app_dossier_current
  add column if not exists search_text text;
alter table public.app_archive_annonce_index_current
  add column if not exists search_text text;
alter table public.app_historical_annonce_index_current
  add column if not exists search_text text;

update public.app_dossier_current
set search_text = nullif(regexp_replace(concat_ws(' ', numero_dossier, numero_mandat, titre_bien, ville, code_postal, commercial_nom, agence_nom, mandants_texte), '\s+', ' ', 'g'), '')
where search_text is null;

update public.app_archive_annonce_index_current
set search_text = nullif(regexp_replace(concat_ws(' ', numero_dossier, numero_mandat, titre_bien, ville, code_postal, commercial_nom, agence_nom, mandants_texte), '\s+', ' ', 'g'), '')
where search_text is null;

update public.app_historical_annonce_index_current
set search_text = nullif(regexp_replace(concat_ws(' ', numero_dossier, numero_mandat, titre_bien, ville, code_postal, commercial_nom, agence_nom, mandants_texte), '\s+', ' ', 'g'), '')
where search_text is null;

create index if not exists idx_app_dossier_current_search_text_trgm
  on public.app_dossier_current using gin (search_text gin_trgm_ops);
create index if not exists idx_app_archive_annonce_index_search_text_trgm
  on public.app_archive_annonce_index_current using gin (search_text gin_trgm_ops);
create index if not exists idx_app_historical_annonce_index_search_text_trgm
  on public.app_historical_annonce_index_current using gin (search_text gin_trgm_ops);

create or replace view public.app_dossiers_current as
select
  app_dossier_id,
  hektor_annonce_id,
  archive,
  diffusable,
  adresse_privee_listing,
  adresse_detail,
  code_postal,
  code_postal_prive_detail,
  ville_privee_detail,
  nb_portails_actifs,
  has_diffusion_error,
  portails_resume,
  offre_id,
  offre_state,
  compromis_id,
  compromis_state,
  vente_id,
  numero_dossier,
  numero_mandat,
  titre_bien,
  ville,
  type_bien,
  prix,
  commercial_id,
  commercial_nom,
  negociateur_email,
  agence_nom,
  statut_annonce,
  photo_url_listing,
  images_preview_json,
  validation_diffusion_state,
  mandat_type,
  mandat_type_source,
  mandat_date_debut,
  mandat_date_fin,
  mandat_montant,
  mandants_texte,
  price_change_event_count,
  price_change_last_source_kind,
  price_change_last_old_value,
  price_change_last_new_value,
  price_change_last_detected_at,
  price_change_last_source_updated_at,
  etat_visibilite,
  alerte_principale,
  priority,
  has_open_blocker,
  commentaire_resume,
  date_relance_prevue,
  dernier_event_type,
  dernier_work_status,
  offre_last_proposition_type,
  search_text
from public.app_dossier_current d;
