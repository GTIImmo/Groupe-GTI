create table if not exists public.app_matterport_group (
    id uuid primary key default gen_random_uuid(),
    hektor_annonce_id bigint not null,
    numero_mandat text,
    group_label text,
    group_state text,
    group_visibility text,
    match_status text not null default 'pending',
    is_validated boolean not null default false,
    synced_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.app_matterport_group_model (
    id uuid primary key default gen_random_uuid(),
    group_id uuid not null references public.app_matterport_group(id) on delete cascade,
    matterport_model_id text not null,
    matterport_url text not null,
    matterport_name text,
    matterport_internal_id text,
    label text,
    display_order integer not null default 1,
    is_primary boolean not null default false,
    state text,
    visibility text,
    created_at_matterport timestamptz,
    modified_at_matterport timestamptz,
    synced_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists idx_app_matterport_group_annonce_mandat
on public.app_matterport_group (hektor_annonce_id, coalesce(numero_mandat, ''));

create unique index if not exists idx_app_matterport_group_model_model_id
on public.app_matterport_group_model (matterport_model_id);

create index if not exists idx_app_matterport_group_model_group
on public.app_matterport_group_model (group_id, display_order, matterport_name);

create unique index if not exists idx_app_matterport_group_model_primary
on public.app_matterport_group_model (group_id)
where is_primary = true;

alter table public.app_matterport_group enable row level security;
alter table public.app_matterport_group_model enable row level security;

create policy "app_matterport_group_select_active_users"
on public.app_matterport_group
for select
using (public.is_app_user_active());

create policy "app_matterport_group_model_select_active_users"
on public.app_matterport_group_model
for select
using (public.is_app_user_active());

create policy "app_matterport_group_write_admin"
on public.app_matterport_group
for all
using (public.is_app_manager_or_admin())
with check (public.is_app_manager_or_admin());

create policy "app_matterport_group_model_write_admin"
on public.app_matterport_group_model
for all
using (public.is_app_manager_or_admin())
with check (public.is_app_manager_or_admin());
