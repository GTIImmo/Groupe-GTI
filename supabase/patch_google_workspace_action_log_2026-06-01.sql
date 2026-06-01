begin;

create table if not exists public.app_google_workspace_action_log (
    id uuid primary key default gen_random_uuid(),
    requested_by uuid references auth.users(id) on delete set null,
    requested_by_email text,
    action_type text not null
        check (action_type in (
            'calendar.freebusy',
            'calendar.event.create',
            'calendar.event.update',
            'calendar.event.delete',
            'gmail.send',
            'gmail.metadata.search',
            'gmail.readonly.thread',
            'contacts.read'
        )),
    subject_email text not null,
    target_email text,
    related_entity_type text,
    related_entity_id text,
    dry_run boolean not null default false,
    status text not null
        check (status in ('done', 'error', 'skipped')),
    provider_status_code integer,
    error_code text,
    error_message text,
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_app_google_workspace_action_log_created
on public.app_google_workspace_action_log (created_at desc);

create index if not exists idx_app_google_workspace_action_log_requested_by
on public.app_google_workspace_action_log (requested_by, created_at desc);

create index if not exists idx_app_google_workspace_action_log_subject
on public.app_google_workspace_action_log (lower(subject_email), created_at desc);

alter table public.app_google_workspace_action_log enable row level security;

drop policy if exists app_google_workspace_action_log_select_scope on public.app_google_workspace_action_log;
create policy app_google_workspace_action_log_select_scope
on public.app_google_workspace_action_log
for select
to authenticated
using (
    requested_by = auth.uid()
    or public.is_app_manager_or_admin()
);

grant select on public.app_google_workspace_action_log to authenticated;
grant all on public.app_google_workspace_action_log to service_role;

comment on table public.app_google_workspace_action_log
is 'Journal securise des actions Google Workspace declenchees par le backend GTI. Ne stocke pas les secrets ni le contenu complet des emails/agendas.';

comment on column public.app_google_workspace_action_log.requested_by
is 'Utilisateur Supabase ayant demande l action, si disponible.';

comment on column public.app_google_workspace_action_log.action_type
is 'Type d action Google Workspace: disponibilite agenda, creation evenement, envoi Gmail, lecture future, contacts.';

comment on column public.app_google_workspace_action_log.subject_email
is 'Compte Google Workspace au nom duquel l action est realisee.';

comment on column public.app_google_workspace_action_log.metadata_json
is 'Metadonnees techniques limitees. Ne pas y stocker de corps email, description complete de rendez-vous ou secret.';

commit;
