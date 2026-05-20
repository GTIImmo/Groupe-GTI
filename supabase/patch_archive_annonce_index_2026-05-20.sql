create table if not exists public.app_archive_annonce_index_current (
    hektor_annonce_id bigint primary key,
    app_archive_id bigint not null,
    numero_dossier text,
    numero_mandat text,
    titre_bien text not null,
    ville text,
    code_postal text,
    type_bien text,
    prix numeric,
    commercial_id text,
    commercial_nom text,
    negociateur_email text,
    agence_nom text,
    statut_annonce text,
    archive text,
    diffusable text,
    date_maj text,
    mandat_type text,
    mandat_date_debut text,
    mandat_date_fin text,
    mandat_montant numeric,
    mandants_texte text,
    has_local_detail boolean not null default false,
    local_detail_updated_at text,
    source_updated_at text,
    source_hash text not null,
    refreshed_at timestamptz not null default now()
);

create index if not exists idx_app_archive_annonce_index_mandat
on public.app_archive_annonce_index_current (numero_mandat);

create index if not exists idx_app_archive_annonce_index_dossier
on public.app_archive_annonce_index_current (numero_dossier);

create index if not exists idx_app_archive_annonce_index_city
on public.app_archive_annonce_index_current (ville, code_postal);

create index if not exists idx_app_archive_annonce_index_commercial
on public.app_archive_annonce_index_current (commercial_id, commercial_nom, lower(coalesce(negociateur_email, '')));

create index if not exists idx_app_archive_annonce_index_date
on public.app_archive_annonce_index_current (date_maj desc, hektor_annonce_id desc);

alter table public.app_archive_annonce_index_current enable row level security;

drop policy if exists "app_archive_annonce_index_current_select_active_users"
on public.app_archive_annonce_index_current;

create policy "app_archive_annonce_index_current_select_active_users"
on public.app_archive_annonce_index_current
for select
using (public.is_app_user_active());
