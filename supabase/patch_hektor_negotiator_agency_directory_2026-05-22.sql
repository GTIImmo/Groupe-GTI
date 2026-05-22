create table if not exists public.app_hektor_negotiator_agency_directory (
    hektor_negociateur_id text primary key,
    hektor_user_id text,
    hektor_agence_id text,
    agence_id_user text,
    agence_nom text,
    nom text,
    prenom text,
    display_name text,
    email text,
    telephone text,
    portable text,
    source_hash text not null,
    refreshed_at timestamptz not null default now()
);

create index if not exists idx_app_hektor_negotiator_agency_directory_agence
on public.app_hektor_negotiator_agency_directory (hektor_agence_id);

create index if not exists idx_app_hektor_negotiator_agency_directory_user
on public.app_hektor_negotiator_agency_directory (hektor_user_id);

create index if not exists idx_app_hektor_negotiator_agency_directory_email
on public.app_hektor_negotiator_agency_directory (email);

alter table public.app_hektor_negotiator_agency_directory enable row level security;

drop policy if exists app_hektor_negotiator_agency_directory_select on public.app_hektor_negotiator_agency_directory;
create policy app_hektor_negotiator_agency_directory_select
on public.app_hektor_negotiator_agency_directory
for select
using (public.is_app_user_active());

comment on table public.app_hektor_negotiator_agency_directory is 'Annuaire local des rattachements negociateurs Hektor par agence.';
