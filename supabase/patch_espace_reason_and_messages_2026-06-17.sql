-- Espace client (Étape 3) : raison du refus (sur le bien) + messages client -> négociateur.
-- Additif, réversible.
alter table public.app_email_envoi_bien add column if not exists feedback_reason text;
comment on column public.app_email_envoi_bien.feedback_reason
is 'Raison du refus client (trop_cher/secteur/trop_petit/autre), saisie dans l espace.';

create table if not exists public.app_espace_message (
    id uuid primary key default gen_random_uuid(),
    envoi_id uuid references public.app_email_envoi(id) on delete set null,
    hektor_contact_id text,
    contact_search_key text,
    app_dossier_id bigint,
    negociateur_email text,
    message text not null,
    handled_at timestamptz,
    created_at timestamptz not null default now()
);
create index if not exists idx_app_espace_message_nego on public.app_espace_message (lower(negociateur_email), created_at desc);
create index if not exists idx_app_espace_message_contact on public.app_espace_message (hektor_contact_id, created_at desc);

alter table public.app_espace_message enable row level security;
drop policy if exists app_espace_message_select on public.app_espace_message;
create policy app_espace_message_select on public.app_espace_message
    for select to authenticated using (public.is_app_manager_or_admin());
grant select on public.app_espace_message to authenticated;
grant all on public.app_espace_message to service_role;
comment on table public.app_espace_message is 'Messages/questions envoyes par un client depuis son espace, destines a son negociateur.';
