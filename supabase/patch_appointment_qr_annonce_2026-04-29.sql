create table if not exists public.app_appointment_public_link (
    id uuid primary key default gen_random_uuid(),
    link_type text not null default 'annonce'
        check (link_type in ('annonce')),
    token text not null unique,
    hektor_annonce_id bigint not null,
    app_dossier_id bigint,
    commercial_id text,
    commercial_nom text,
    negociateur_email text,
    agence_nom text,
    title_override text,
    is_active boolean not null default true,
    last_generated_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.app_appointment_slot_rule (
    id uuid primary key default gen_random_uuid(),
    scope_type text not null default 'global'
        check (scope_type in ('global', 'negociateur', 'annonce')),
    scope_key text,
    min_delay_hours integer not null default 36,
    days_ahead integer not null default 21,
    slot_minutes integer not null default 30,
    day_start_hour integer not null default 9,
    day_end_hour integer not null default 18,
    lunch_break_start text,
    lunch_break_end text,
    fake_busy_ratio numeric(5,4) not null default 0.3500,
    allow_saturday boolean not null default true,
    allow_sunday boolean not null default false,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (scope_type, scope_key)
);

create table if not exists public.app_appointment_request (
    id uuid primary key default gen_random_uuid(),
    public_link_id uuid not null references public.app_appointment_public_link(id) on delete cascade,
    app_dossier_id bigint,
    hektor_annonce_id bigint not null,
    commercial_id text,
    commercial_nom text,
    negociateur_email text,
    agence_nom text,
    client_nom text not null,
    client_email text,
    client_telephone text not null,
    requested_start_at timestamptz not null,
    requested_end_at timestamptz,
    client_message text,
    request_status text not null default 'pending'
        check (request_status in ('pending', 'contacted', 'confirmed', 'rescheduled', 'cancelled')),
    mail_sent_at timestamptz,
    contacted_at timestamptz,
    closed_at timestamptz,
    internal_note text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.app_appointment_request_event (
    id uuid primary key default gen_random_uuid(),
    appointment_request_id uuid not null references public.app_appointment_request(id) on delete cascade,
    event_type text not null,
    event_label text not null,
    actor_name text,
    payload_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_app_appointment_public_link_annonce
on public.app_appointment_public_link (hektor_annonce_id, is_active);

create index if not exists idx_app_appointment_public_link_dossier
on public.app_appointment_public_link (app_dossier_id, is_active);

create index if not exists idx_app_appointment_request_annonce
on public.app_appointment_request (hektor_annonce_id, created_at desc);

create index if not exists idx_app_appointment_request_dossier
on public.app_appointment_request (app_dossier_id, created_at desc);

create index if not exists idx_app_appointment_request_status
on public.app_appointment_request (request_status, created_at desc);

create index if not exists idx_app_appointment_request_negociateur
on public.app_appointment_request (commercial_id, negociateur_email, created_at desc);

create index if not exists idx_app_appointment_request_event_request
on public.app_appointment_request_event (appointment_request_id, created_at desc);

insert into public.app_appointment_slot_rule (
    scope_type,
    scope_key,
    min_delay_hours,
    days_ahead,
    slot_minutes,
    day_start_hour,
    day_end_hour,
    lunch_break_start,
    lunch_break_end,
    fake_busy_ratio,
    allow_saturday,
    allow_sunday,
    is_active
)
values (
    'global',
    null,
    36,
    21,
    30,
    9,
    18,
    '12:30',
    '14:00',
    0.3500,
    true,
    false,
    true
)
on conflict (scope_type, scope_key) do update
set
    min_delay_hours = excluded.min_delay_hours,
    days_ahead = excluded.days_ahead,
    slot_minutes = excluded.slot_minutes,
    day_start_hour = excluded.day_start_hour,
    day_end_hour = excluded.day_end_hour,
    lunch_break_start = excluded.lunch_break_start,
    lunch_break_end = excluded.lunch_break_end,
    fake_busy_ratio = excluded.fake_busy_ratio,
    allow_saturday = excluded.allow_saturday,
    allow_sunday = excluded.allow_sunday,
    is_active = excluded.is_active,
    updated_at = now();

create or replace view public.app_appointment_request_current
with (security_invoker=on) as
select
    r.id,
    r.public_link_id,
    r.app_dossier_id,
    r.hektor_annonce_id,
    r.commercial_id,
    r.commercial_nom,
    r.negociateur_email,
    r.agence_nom,
    r.client_nom,
    r.client_email,
    r.client_telephone,
    r.requested_start_at,
    r.requested_end_at,
    r.client_message,
    r.request_status,
    r.mail_sent_at,
    r.contacted_at,
    r.closed_at,
    r.internal_note,
    r.created_at,
    r.updated_at
from public.app_appointment_request r;

create or replace view public.app_appointment_event_current
with (security_invoker=on) as
select
    e.id,
    e.appointment_request_id,
    e.event_type,
    e.event_label,
    e.actor_name,
    e.payload_json,
    e.created_at
from public.app_appointment_request_event e;

alter table public.app_appointment_public_link enable row level security;
alter table public.app_appointment_slot_rule enable row level security;
alter table public.app_appointment_request enable row level security;
alter table public.app_appointment_request_event enable row level security;

drop policy if exists app_appointment_public_link_select on public.app_appointment_public_link;
create policy app_appointment_public_link_select
on public.app_appointment_public_link
for select
using (public.is_app_user_active());

drop policy if exists app_appointment_slot_rule_select on public.app_appointment_slot_rule;
create policy app_appointment_slot_rule_select
on public.app_appointment_slot_rule
for select
using (public.is_app_user_active());

drop policy if exists app_appointment_request_select on public.app_appointment_request;
create policy app_appointment_request_select
on public.app_appointment_request
for select
using (public.is_app_user_active());

drop policy if exists app_appointment_request_update on public.app_appointment_request;
create policy app_appointment_request_update
on public.app_appointment_request
for update
using (public.is_app_user_active())
with check (public.is_app_user_active());

drop policy if exists app_appointment_request_event_select on public.app_appointment_request_event;
create policy app_appointment_request_event_select
on public.app_appointment_request_event
for select
using (public.is_app_user_active());

drop policy if exists app_appointment_request_event_insert on public.app_appointment_request_event;
create policy app_appointment_request_event_insert
on public.app_appointment_request_event
for insert
with check (public.is_app_user_active());

comment on table public.app_appointment_public_link is 'Liens publics QR annonce vers le module de demande de rendez-vous.';
comment on table public.app_appointment_slot_rule is 'Regles de generation des creneaux fictifs de rendez-vous.';
comment on table public.app_appointment_request is 'Demandes de rendez-vous declenchees depuis un QR annonce.';
comment on table public.app_appointment_request_event is 'Historique des evenements d une demande de rendez-vous.';
