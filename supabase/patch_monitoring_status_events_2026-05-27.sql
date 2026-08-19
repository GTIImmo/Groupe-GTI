begin;

create table if not exists public.app_monitor_status (
    status_key text primary key,
    domain text not null
        check (domain in ('system', 'business', 'mixed')),
    component text not null,
    check_name text not null,
    status text not null
        check (status in ('ok', 'warning', 'critical', 'unknown')),
    severity text not null
        check (severity in ('info', 'warning', 'critical', 'unknown')),
    message text not null,
    observed_at timestamptz not null,
    details_json jsonb not null default '{}'::jsonb
        constraint app_monitor_status_details_json_is_object
        check (jsonb_typeof(details_json) = 'object'),
    source text not null default 'check_gti_health',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.app_monitor_event (
    id uuid primary key default gen_random_uuid(),
    event_key text not null,
    domain text not null
        check (domain in ('system', 'business', 'mixed')),
    component text not null,
    check_name text not null,
    status text not null
        check (status in ('ok', 'warning', 'critical', 'unknown')),
    severity text not null
        check (severity in ('info', 'warning', 'critical', 'unknown')),
    message text not null,
    observed_at timestamptz not null,
    details_json jsonb not null default '{}'::jsonb
        constraint app_monitor_event_details_json_is_object
        check (jsonb_typeof(details_json) = 'object'),
    source text not null default 'check_gti_health',
    created_at timestamptz not null default now()
);

create index if not exists idx_app_monitor_status_status
on public.app_monitor_status (status, severity, observed_at desc);

create index if not exists idx_app_monitor_status_component
on public.app_monitor_status (component, check_name);

create index if not exists idx_app_monitor_event_observed
on public.app_monitor_event (observed_at desc, severity);

create index if not exists idx_app_monitor_event_component
on public.app_monitor_event (component, check_name, observed_at desc);

alter table public.app_monitor_status enable row level security;
alter table public.app_monitor_event enable row level security;

drop policy if exists app_monitor_status_select_ops on public.app_monitor_status;
create policy app_monitor_status_select_ops
on public.app_monitor_status
for select
to authenticated
using (public.is_app_manager_or_admin());

drop policy if exists app_monitor_event_select_ops on public.app_monitor_event;
create policy app_monitor_event_select_ops
on public.app_monitor_event
for select
to authenticated
using (public.is_app_manager_or_admin());

revoke all on public.app_monitor_status from anon;
revoke all on public.app_monitor_status from public;
revoke all on public.app_monitor_status from authenticated;

revoke all on public.app_monitor_event from anon;
revoke all on public.app_monitor_event from public;
revoke all on public.app_monitor_event from authenticated;

grant select on public.app_monitor_status to authenticated;
grant select on public.app_monitor_event to authenticated;
grant all on public.app_monitor_status to service_role;
grant all on public.app_monitor_event to service_role;

comment on table public.app_monitor_status is
'Etat courant des checks de supervision GTI. Alimente par monitoring/check_gti_health.py uniquement.';

comment on table public.app_monitor_event is
'Evenements de supervision GTI. Stocke les alertes et changements simples sans logs bruts.';

commit;
