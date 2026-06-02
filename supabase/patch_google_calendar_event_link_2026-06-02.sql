begin;

create table if not exists public.app_google_calendar_event_link (
    id uuid primary key default gen_random_uuid(),
    event_type text not null default 'visite'
        check (event_type in ('visite', 'estimation', 'mandat', 'compromis', 'relance', 'agence', 'autre')),
    related_entity_type text not null default 'annonce'
        check (related_entity_type in ('annonce', 'contact', 'affaire', 'visite', 'relance', 'other')),
    related_entity_id text,
    app_dossier_id bigint,
    hektor_annonce_id bigint,
    hektor_contact_id text,
    google_calendar_email text not null,
    google_event_id text not null,
    google_html_link text,
    summary text not null,
    location text,
    starts_at timestamptz not null,
    ends_at timestamptz not null,
    attendees_json jsonb not null default '[]'::jsonb,
    status text not null default 'active'
        check (status in ('active', 'cancelled', 'deleted')),
    metadata_json jsonb not null default '{}'::jsonb,
    created_by uuid references auth.users(id) on delete set null,
    created_by_email text,
    updated_by uuid references auth.users(id) on delete set null,
    updated_by_email text,
    cancelled_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint app_google_calendar_event_link_time_check
        check (ends_at > starts_at),
    constraint app_google_calendar_event_link_workspace_check
        check (position('@' in google_calendar_email) > 1 and lower(split_part(google_calendar_email, '@', 2)) = 'gti-immobilier.fr')
);

create unique index if not exists idx_app_google_calendar_event_link_google_event
on public.app_google_calendar_event_link (google_calendar_email, google_event_id);

create index if not exists idx_app_google_calendar_event_link_dossier
on public.app_google_calendar_event_link (app_dossier_id, starts_at desc);

create index if not exists idx_app_google_calendar_event_link_annonce
on public.app_google_calendar_event_link (hektor_annonce_id, starts_at desc);

create index if not exists idx_app_google_calendar_event_link_contact
on public.app_google_calendar_event_link (hektor_contact_id, starts_at desc);

create index if not exists idx_app_google_calendar_event_link_calendar
on public.app_google_calendar_event_link (lower(google_calendar_email), starts_at desc);

alter table public.app_google_calendar_event_link enable row level security;

drop policy if exists app_google_calendar_event_link_select_scope on public.app_google_calendar_event_link;
create policy app_google_calendar_event_link_select_scope
on public.app_google_calendar_event_link
for select
to authenticated
using (
    public.is_app_manager_or_admin()
    or created_by = auth.uid()
    or lower(google_calendar_email) in (
        select lower(google_email)
        from public.app_google_workspace_identity
        where app_user_id = auth.uid()
          and is_active is true
          and link_status = 'linked'
    )
    or lower(google_calendar_email) in (
        select lower(negociateur_email)
        from public.app_google_workspace_identity
        where app_user_id = auth.uid()
          and is_active is true
          and link_status = 'linked'
          and negociateur_email is not null
    )
);

grant select on public.app_google_calendar_event_link to authenticated;
grant all on public.app_google_calendar_event_link to service_role;

comment on table public.app_google_calendar_event_link
is 'Lien metier entre un rendez-vous Google Agenda et un objet GTI: annonce, contact, affaire, visite ou relance.';

comment on column public.app_google_calendar_event_link.google_calendar_email
is 'Compte Google Workspace proprietaire du rendez-vous, generalement le negociateur.';

comment on column public.app_google_calendar_event_link.google_event_id
is 'Identifiant de l evenement Google Calendar, utilise pour modifier ou supprimer le rendez-vous.';

comment on column public.app_google_calendar_event_link.attendees_json
is 'Invites envoyes a Google Calendar, conserves pour historique metier et futurs agents.';

commit;
