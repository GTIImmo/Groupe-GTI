create table if not exists public.app_user_directory (
    id_user text primary key,
    user_type text,
    prenom text,
    nom text,
    display_name text,
    email text,
    tel text,
    portable text,
    site text,
    parent_id text,
    source_hash text not null,
    refreshed_at timestamptz not null default now()
);

create table if not exists public.app_agence_directory (
    id_agence text primary key,
    id_user text,
    nom text not null,
    mail text,
    tel text,
    responsable text,
    parent_id text,
    source_hash text not null,
    refreshed_at timestamptz not null default now()
);

create index if not exists idx_app_agence_directory_user on public.app_agence_directory (id_user);
create index if not exists idx_app_user_directory_email on public.app_user_directory (email);
create index if not exists idx_app_user_directory_type on public.app_user_directory (user_type);
create index if not exists idx_app_agence_directory_nom on public.app_agence_directory (nom);

alter table public.app_user_directory enable row level security;
alter table public.app_agence_directory enable row level security;

drop policy if exists app_user_directory_select on public.app_user_directory;
create policy app_user_directory_select
on public.app_user_directory
for select
using (public.is_app_user_active());

drop policy if exists app_agence_directory_select on public.app_agence_directory;
create policy app_agence_directory_select
on public.app_agence_directory
for select
using (public.is_app_user_active());

comment on table public.app_user_directory is 'Annuaire local des users Hektor synchronise pour eviter les appels externes au chargement public.';
comment on table public.app_agence_directory is 'Annuaire local des agences Hektor synchronise pour eviter les appels externes au chargement public.';
