create table if not exists public.app_mandat_current (
    app_dossier_id bigint primary key,
    hektor_annonce_id bigint not null,
    archive text,
    diffusable text,
    nb_portails_actifs integer not null default 0,
    has_diffusion_error boolean not null default false,
    portails_resume text,
    numero_dossier text,
    numero_mandat text,
    titre_bien text not null,
    ville text,
    type_bien text,
    prix numeric,
    commercial_id text,
    commercial_nom text,
    agence_nom text,
    statut_annonce text,
    priority text,
    offre_id text,
    compromis_id text,
    vente_id text,
    source_updated_at timestamptz,
    refreshed_at timestamptz not null default now()
);

create table if not exists public.app_mandat_broadcast_current (
    app_dossier_id bigint not null,
    hektor_annonce_id bigint not null,
    passerelle_key text not null,
    commercial_key text not null default '',
    commercial_id text,
    commercial_nom text,
    commercial_prenom text,
    current_state text,
    export_status text,
    is_success boolean not null default false,
    is_error boolean not null default false,
    refreshed_at timestamptz not null default now(),
    primary key (app_dossier_id, passerelle_key, commercial_key)
);

create table if not exists public.app_diffusion_request (
    id uuid primary key default gen_random_uuid(),
    app_dossier_id bigint not null,
    hektor_annonce_id bigint not null,
    numero_dossier text,
    numero_mandat text,
    titre_bien text not null,
    commercial_nom text,
    request_type text not null default 'demande_diffusion',
    requested_by uuid not null references auth.users(id) on delete cascade,
    requested_by_label text,
    requested_at timestamptz not null default now(),
    request_status text not null default 'pending',
    request_comment text,
    request_reason text,
    admin_response text,
    refusal_reason text,
    follow_up_needed boolean not null default false,
    follow_up_at timestamptz,
    relaunch_count integer not null default 0,
    processed_by uuid references auth.users(id) on delete set null,
    processed_by_label text,
    processed_at timestamptz,
    processing_comment text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_app_mandat_current_commercial on public.app_mandat_current (commercial_id, commercial_nom);
create index if not exists idx_app_mandat_current_statut on public.app_mandat_current (statut_annonce, archive, diffusable);
create index if not exists idx_app_mandat_broadcast_current_annonce on public.app_mandat_broadcast_current (hektor_annonce_id, passerelle_key);
create index if not exists idx_app_diffusion_request_status on public.app_diffusion_request (request_status, requested_at desc);
create index if not exists idx_app_diffusion_request_dossier on public.app_diffusion_request (app_dossier_id);

create or replace view public.app_mandats_current
with (security_invoker=on) as
select *
from public.app_mandat_current;

create or replace view public.app_mandat_broadcasts_current
with (security_invoker=on) as
select *
from public.app_mandat_broadcast_current;

create or replace view public.app_diffusion_requests_current
with (security_invoker=on) as
select
    r.*,
    coalesce(req.display_name, req.email, r.requested_by_label) as requested_by_name,
    coalesce(proc.display_name, proc.email, r.processed_by_label) as processed_by_name
from public.app_diffusion_request r
left join public.app_user_profile req on req.id = r.requested_by
left join public.app_user_profile proc on proc.id = r.processed_by;

create or replace function public.is_app_manager_or_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select exists (
        select 1
        from public.app_user_profile p
        where p.id = auth.uid()
          and p.role in ('admin', 'manager')
          and p.is_active = true
    );
$$;

alter table public.app_mandat_current enable row level security;
alter table public.app_mandat_broadcast_current enable row level security;
alter table public.app_diffusion_request enable row level security;

create policy "app_mandat_current_select_active_users"
on public.app_mandat_current
for select
using (public.is_app_user_active());

create policy "app_mandat_broadcast_current_select_active_users"
on public.app_mandat_broadcast_current
for select
using (public.is_app_user_active());

create policy "app_diffusion_request_select_active_users"
on public.app_diffusion_request
for select
using (public.is_app_user_active());

create policy "app_diffusion_request_insert_active_users"
on public.app_diffusion_request
for insert
with check (
    public.is_app_user_active()
    and requested_by = auth.uid()
);

create policy "app_diffusion_request_update_admin"
on public.app_diffusion_request
for update
using (public.is_app_manager_or_admin())
with check (public.is_app_manager_or_admin());
