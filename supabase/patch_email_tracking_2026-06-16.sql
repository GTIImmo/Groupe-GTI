-- Lot B — Persistance du suivi de l'email de rapprochement + consentement RGPD.
-- Additif et réversible (rollback : patch_email_tracking_2026-06-16_rollback.sql).
-- Aucune donnée existante touchée. Tables neuves uniquement.

begin;

-- 1) Un email envoyé (1 ligne par envoi de rapprochement).
create table if not exists public.app_email_envoi (
    id uuid primary key default gen_random_uuid(),
    contact_search_key text,
    hektor_contact_id text,
    recipient_email text,
    sender_email text,
    variante text check (variante in ('push', 'pull')),
    subject text,
    gmail_message_id text,
    gmail_thread_id text,
    statut text not null default 'envoye'
        check (statut in ('brouillon', 'envoye', 'ouvert', 'clique', 'interesse', 'refuse', 'rdv', 'repondu', 'desinscrit')),
    score text check (score in ('chaud', 'tiede', 'froid')),
    sent_at timestamptz,
    opened_at timestamptz,
    open_count integer not null default 0,
    first_clicked_at timestamptz,
    click_count integer not null default 0,
    rdv_at timestamptz,
    replied_at timestamptz,
    unsubscribed_at timestamptz,
    relances_count integer not null default 0,
    dry_run boolean not null default true,
    created_by uuid references auth.users(id) on delete set null,
    created_at timestamptz not null default now()
);

create index if not exists idx_app_email_envoi_contact on public.app_email_envoi (hektor_contact_id, created_at desc);
create index if not exists idx_app_email_envoi_search on public.app_email_envoi (contact_search_key, created_at desc);
create index if not exists idx_app_email_envoi_recipient on public.app_email_envoi (lower(recipient_email), created_at desc);

-- 2) Les biens proposés dans un email (N par envoi) + feedback ❤️/✕ par bien.
create table if not exists public.app_email_envoi_bien (
    id uuid primary key default gen_random_uuid(),
    envoi_id uuid not null references public.app_email_envoi(id) on delete cascade,
    app_dossier_id bigint,
    feedback text check (feedback in ('interesse', 'refuse')),
    feedback_at timestamptz,
    created_at timestamptz not null default now(),
    unique (envoi_id, app_dossier_id)
);

create index if not exists idx_app_email_envoi_bien_envoi on public.app_email_envoi_bien (envoi_id);
create index if not exists idx_app_email_envoi_bien_dossier on public.app_email_envoi_bien (app_dossier_id);

-- 3) Journal brut des événements (append-only) : ouverture, clics, désinscription.
create table if not exists public.app_email_event (
    id uuid primary key default gen_random_uuid(),
    envoi_id uuid not null references public.app_email_envoi(id) on delete cascade,
    app_dossier_id bigint,
    type text not null check (type in ('open', 'like', 'pass', 'visite', 'unsub')),
    user_agent text,
    ip_hash text,
    created_at timestamptz not null default now()
);

create index if not exists idx_app_email_event_envoi on public.app_email_event (envoi_id, created_at desc);
create index if not exists idx_app_email_event_type on public.app_email_event (type, created_at desc);

-- 4) Consentement / opt-out (RGPD). Filtré AVANT chaque envoi.
create table if not exists public.app_contact_consent (
    id uuid primary key default gen_random_uuid(),
    hektor_contact_id text,
    email text not null,  -- stocké normalisé en minuscules (le backend lowercase avant écriture)
    channel text not null default 'email',
    status text not null check (status in ('opt_in', 'opt_out')),
    source text,
    consent_at timestamptz,
    opt_out_at timestamptz,
    ip_hash text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (email, channel)
);

create index if not exists idx_app_contact_consent_contact on public.app_contact_consent (hektor_contact_id);

-- RLS : lecture pour les gestionnaires/admins, écriture réservée au backend (service_role).
alter table public.app_email_envoi enable row level security;
alter table public.app_email_envoi_bien enable row level security;
alter table public.app_email_event enable row level security;
alter table public.app_contact_consent enable row level security;

drop policy if exists app_email_envoi_select_scope on public.app_email_envoi;
create policy app_email_envoi_select_scope on public.app_email_envoi
    for select to authenticated
    using (created_by = auth.uid() or public.is_app_manager_or_admin());

drop policy if exists app_email_envoi_bien_select_scope on public.app_email_envoi_bien;
create policy app_email_envoi_bien_select_scope on public.app_email_envoi_bien
    for select to authenticated
    using (public.is_app_manager_or_admin());

drop policy if exists app_email_event_select_scope on public.app_email_event;
create policy app_email_event_select_scope on public.app_email_event
    for select to authenticated
    using (public.is_app_manager_or_admin());

drop policy if exists app_contact_consent_select_scope on public.app_contact_consent;
create policy app_contact_consent_select_scope on public.app_contact_consent
    for select to authenticated
    using (public.is_app_manager_or_admin());

grant select on public.app_email_envoi, public.app_email_envoi_bien, public.app_email_event, public.app_contact_consent to authenticated;
grant all on public.app_email_envoi, public.app_email_envoi_bien, public.app_email_event, public.app_contact_consent to service_role;

comment on table public.app_email_envoi is 'Suivi des emails de rapprochement (Lot B). 1 ligne = 1 envoi. Pas de corps email stocke.';
comment on table public.app_email_envoi_bien is 'Biens proposes dans un email + feedback interesse/refuse par bien.';
comment on table public.app_email_event is 'Journal append-only des evenements email (ouverture, clic, desinscription).';
comment on table public.app_contact_consent is 'Consentement/opt-out par email et canal. Filtre opt_out applique AVANT tout envoi.';

commit;
