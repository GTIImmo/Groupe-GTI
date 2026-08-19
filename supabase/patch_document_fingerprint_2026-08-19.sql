-- Empreinte du contenu documentaire par annonce (2026-08-19).
-- Ajout PUR : nouvelle table, aucune table existante modifiee, aucune RLS existante touchee.
-- Sert au futur run de detection : comparer l'empreinte du jour a celle du dernier passage
-- pour n'empiler une synchro documents que sur les annonces qui ont reellement bouge.
-- Reversible : DROP TABLE app_console_document_fingerprint;

create table if not exists public.app_console_document_fingerprint (
    hektor_annonce_id text primary key,
    fingerprint       text not null,
    checked_at        timestamptz not null default now(),
    synced_at         timestamptz,
    created_at        timestamptz not null default now(),
    updated_at        timestamptz not null default now()
);

comment on table public.app_console_document_fingerprint is
  'Empreinte du contenu documentaire Hektor par annonce (fichiers deposes + lignes modelo + procedures). Accelerateur de detection, jamais source de verite.';

alter table public.app_console_document_fingerprint enable row level security;

-- Ecriture reservee au worker (service_role, qui contourne la RLS). Lecture pour les comptes
-- authentifies, alignee sur app_console_document.
drop policy if exists app_console_document_fingerprint_select on public.app_console_document_fingerprint;
create policy app_console_document_fingerprint_select
    on public.app_console_document_fingerprint
    for select to authenticated using (true);
