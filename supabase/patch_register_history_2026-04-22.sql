create table if not exists public.app_mandat_register_current (
    register_row_id text primary key,
    app_dossier_id bigint,
    hektor_annonce_id bigint not null,
    photo_url_listing text,
    images_preview_json text,
    adresse_privee_listing text,
    adresse_detail text,
    code_postal text,
    code_postal_prive_detail text,
    ville_privee_detail text,
    archive text,
    diffusable text,
    nb_portails_actifs integer not null default 0,
    has_diffusion_error boolean not null default false,
    portails_resume text,
    numero_dossier text,
    numero_mandat text,
    register_sort_num bigint not null default 0,
    titre_bien text,
    ville text,
    type_bien text,
    prix numeric,
    commercial_id text,
    commercial_nom text,
    negociateur_email text,
    agence_nom text,
    statut_annonce text,
    validation_diffusion_state text,
    mandat_source_id text,
    mandat_numero_reference text,
    mandat_type text,
    mandat_type_source text,
    mandat_date_debut text,
    mandat_date_fin text,
    mandat_montant numeric,
    mandants_texte text,
    mandat_note text,
    priority text,
    offre_id text,
    offre_state text,
    offre_last_proposition_type text,
    compromis_id text,
    compromis_state text,
    vente_id text,
    source_updated_at timestamptz,
    register_source_kind text,
    register_detail_available boolean not null default false,
    register_version_count integer not null default 1,
    register_embedded_avenant_count integer not null default 0,
    register_history_json text,
    register_avenants_json text,
    register_detail_payload_json text,
    source_hash text not null,
    refreshed_at timestamptz not null default now()
);

create index if not exists idx_app_mandat_register_annonce on public.app_mandat_register_current (hektor_annonce_id, numero_mandat);
create index if not exists idx_app_mandat_register_dossier on public.app_mandat_register_current (app_dossier_id);
create index if not exists idx_app_mandat_register_statut on public.app_mandat_register_current (statut_annonce, register_source_kind);
create index if not exists idx_app_mandat_register_commercial on public.app_mandat_register_current (commercial_nom, negociateur_email);
create index if not exists idx_app_mandat_register_sort on public.app_mandat_register_current (register_sort_num desc, hektor_annonce_id desc, register_row_id desc);

create or replace view public.app_registre_mandats_current
with (security_invoker=on) as
select *
from public.app_mandat_register_current;

alter table public.app_mandat_register_current enable row level security;

drop policy if exists "app_mandat_register_current_select_active_users" on public.app_mandat_register_current;
create policy "app_mandat_register_current_select_active_users"
on public.app_mandat_register_current
for select
using (public.is_app_user_active());

notify pgrst, 'reload schema';
