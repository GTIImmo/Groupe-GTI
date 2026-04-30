create table if not exists public.app_estimation_agency_route (
    route_key text primary key,
    agency_id text not null,
    agency_label text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.app_estimation_agency_negotiator (
    id bigserial primary key,
    route_key text not null references public.app_estimation_agency_route(route_key) on delete cascade,
    user_id text not null,
    negotiator_label text,
    negotiator_email text,
    negotiator_phone text,
    is_active boolean not null default true,
    sort_order integer not null default 100,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (route_key, user_id)
);

create table if not exists public.app_estimation_agency_rotation (
    route_key text primary key references public.app_estimation_agency_route(route_key) on delete cascade,
    last_user_id text,
    rotation_count bigint not null default 0,
    updated_at timestamptz not null default now()
);

create index if not exists idx_app_estimation_agency_route_active
on public.app_estimation_agency_route (is_active, route_key);

create index if not exists idx_app_estimation_agency_negotiator_route
on public.app_estimation_agency_negotiator (route_key, is_active, sort_order, id);

alter table public.app_estimation_agency_route enable row level security;
alter table public.app_estimation_agency_negotiator enable row level security;
alter table public.app_estimation_agency_rotation enable row level security;

drop policy if exists app_estimation_agency_route_select on public.app_estimation_agency_route;
create policy app_estimation_agency_route_select
on public.app_estimation_agency_route
for select
using (public.is_app_user_active());

drop policy if exists app_estimation_agency_negotiator_select on public.app_estimation_agency_negotiator;
create policy app_estimation_agency_negotiator_select
on public.app_estimation_agency_negotiator
for select
using (public.is_app_user_active());

drop policy if exists app_estimation_agency_rotation_select on public.app_estimation_agency_rotation;
create policy app_estimation_agency_rotation_select
on public.app_estimation_agency_rotation
for select
using (public.is_app_user_active());

comment on table public.app_estimation_agency_route is 'Routes publiques estimation par agence (slug -> agence).';
comment on table public.app_estimation_agency_negotiator is 'Liste ordonnée des négociateurs éligibles pour la rotation d estimation par agence.';
comment on table public.app_estimation_agency_rotation is 'Etat courant de rotation des leads estimation par route agence.';
