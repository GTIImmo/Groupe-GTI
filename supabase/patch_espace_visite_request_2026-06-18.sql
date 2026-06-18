-- Demande de visite interactive (Lot 1) : objet à statut suivi côté client ET négociateur.
-- Additif, réversible (drop table). N'utilise PAS la vitrine simulée. Le créneau confirmé crée
-- un VRAI évènement Google (via app_google_calendar_event_link) — référencé ici par google_event_id.

create table if not exists public.app_espace_visite_request (
    id                 uuid primary key default gen_random_uuid(),
    -- Contact (acquéreur)
    hektor_contact_id  text,
    contact_email      text,
    contact_name       text,
    contact_search_key text,
    envoi_id           uuid references public.app_email_envoi(id) on delete set null,
    -- Bien
    app_dossier_id     bigint,
    hektor_annonce_id  bigint,
    bien_title         text,
    -- Interlocuteur = négociateur du MANDAT
    negociateur_email  text,
    -- Cycle de vie : demandee -> proposee -> confirmee (ou refusee / annulee)
    status             text not null default 'demandee',
    -- Demande du client
    requested_days     jsonb,   -- ex. ["Dim 21 juin","Lun 22 juin"]
    requested_periods  jsonb,   -- ex. ["Matin","Après-midi"]
    phone              text,
    message            text,
    -- Niveau 2 : créneaux proposés par le négociateur
    proposed_slots     jsonb,   -- ex. [{"start":"2026-06-21T10:00:00+02:00","end":"...","label":"Dim 21 · 10h"}]
    -- Confirmation (crée le vrai RDV Google)
    confirmed_start    timestamptz,
    confirmed_end      timestamptz,
    google_event_id    text,
    google_html_link   text,
    -- Audit
    created_at         timestamptz not null default now(),
    updated_at         timestamptz not null default now()
);

create index if not exists idx_avr_contact on public.app_espace_visite_request (hektor_contact_id, created_at desc);
create index if not exists idx_avr_nego    on public.app_espace_visite_request (lower(negociateur_email), created_at desc);
create index if not exists idx_avr_status  on public.app_espace_visite_request (status, created_at desc);

comment on table public.app_espace_visite_request is
  'Demandes de visite depuis l espace client (statut demandee/proposee/confirmee). Confirmation -> vrai evenement Google.';

-- RLS : lecture authentifiée réservée managers/admins (comme app_espace_message) ; tout le flux
-- actionnable passe par le backend en service_role (jetons signés, sans login).
alter table public.app_espace_visite_request enable row level security;
drop policy if exists avr_select on public.app_espace_visite_request;
create policy avr_select on public.app_espace_visite_request
    for select to authenticated using (public.is_app_manager_or_admin());
grant select on public.app_espace_visite_request to authenticated;
grant all on public.app_espace_visite_request to service_role;
