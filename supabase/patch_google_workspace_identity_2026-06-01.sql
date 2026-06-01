begin;

create table if not exists public.app_google_workspace_identity (
    id uuid primary key default gen_random_uuid(),
    app_user_id uuid not null references public.app_user_profile(id) on delete cascade,
    google_email text not null,
    workspace_domain text not null default 'gti-immobilier.fr',
    hektor_user_id text,
    hektor_negociateur_id text,
    negociateur_email text,
    link_status text not null default 'pending'
        check (link_status in ('pending', 'linked', 'conflict', 'disabled')),
    is_active boolean not null default true,
    last_login_at timestamptz,
    last_checked_at timestamptz,
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    created_by uuid references auth.users(id) on delete set null,
    updated_by uuid references auth.users(id) on delete set null,
    constraint app_google_workspace_identity_google_domain_check
        check (position('@' in google_email) > 1 and lower(split_part(google_email, '@', 2)) = lower(workspace_domain))
);

create unique index if not exists idx_app_google_workspace_identity_user
on public.app_google_workspace_identity (app_user_id);

create unique index if not exists idx_app_google_workspace_identity_google_email
on public.app_google_workspace_identity (lower(google_email));

create index if not exists idx_app_google_workspace_identity_hektor_user
on public.app_google_workspace_identity (hektor_user_id);

create index if not exists idx_app_google_workspace_identity_negociateur_email
on public.app_google_workspace_identity (lower(coalesce(negociateur_email, '')));

alter table public.app_google_workspace_identity enable row level security;

drop policy if exists app_google_workspace_identity_select_scope on public.app_google_workspace_identity;
create policy app_google_workspace_identity_select_scope
on public.app_google_workspace_identity
for select
to authenticated
using (
    app_user_id = auth.uid()
    or public.is_app_manager_or_admin()
);

drop policy if exists app_google_workspace_identity_insert_admin on public.app_google_workspace_identity;
create policy app_google_workspace_identity_insert_admin
on public.app_google_workspace_identity
for insert
to authenticated
with check (public.is_app_manager_or_admin());

drop policy if exists app_google_workspace_identity_update_admin on public.app_google_workspace_identity;
create policy app_google_workspace_identity_update_admin
on public.app_google_workspace_identity
for update
to authenticated
using (public.is_app_manager_or_admin())
with check (public.is_app_manager_or_admin());

drop policy if exists app_google_workspace_identity_delete_admin on public.app_google_workspace_identity;
create policy app_google_workspace_identity_delete_admin
on public.app_google_workspace_identity
for delete
to authenticated
using (public.is_app_manager_or_admin());

grant select, insert, update, delete on public.app_google_workspace_identity to authenticated;
grant all on public.app_google_workspace_identity to service_role;

comment on table public.app_google_workspace_identity
is 'Liaison entre utilisateur GTI Supabase, compte Google Workspace et identite negociateur Hektor. Google sert a l identite, app_user_profile reste la source des roles.';

comment on column public.app_google_workspace_identity.app_user_id
is 'Utilisateur applicatif GTI existant dans app_user_profile.';

comment on column public.app_google_workspace_identity.google_email
is 'Adresse Google Workspace autorisee pour la connexion SSO.';

comment on column public.app_google_workspace_identity.hektor_user_id
is 'id_user Hektor associe quand le collaborateur est negociateur.';

comment on column public.app_google_workspace_identity.hektor_negociateur_id
is 'Identifiant negociateur Hektor associe si disponible.';

comment on column public.app_google_workspace_identity.negociateur_email
is 'Email negociateur Hektor utilise pour le scope commercial existant.';

comment on column public.app_google_workspace_identity.link_status
is 'Etat de controle de la liaison: pending, linked, conflict ou disabled.';

commit;
