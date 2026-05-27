begin;

drop view if exists public.app_contact_relations_current;
drop view if exists public.app_contact_searches_current;
drop table if exists public.app_contact_relation_current;

create table if not exists public.app_contact_current (
    hektor_contact_id text primary key,
    hektor_agence_id text,
    hektor_negociateur_id text,
    negociateur_email text,
    commercial_nom text,
    agence_nom text,
    civilite text,
    nom text,
    prenom text,
    display_name text not null,
    archive boolean not null default false,
    date_enregistrement text,
    date_maj text,
    email text,
    phone_primary text,
    phone_secondary text,
    ville text,
    code_postal text,
    typologies_json jsonb not null default '[]'::jsonb,
    relation_roles_json jsonb not null default '[]'::jsonb,
    linked_annonce_count integer not null default 0,
    active_search_count integer not null default 0,
    total_search_count integer not null default 0,
    has_contact_detail boolean not null default false,
    contact_detail_synced_at text,
    supabase_sync_eligible boolean not null default false,
    eligibility_reasons_json jsonb not null default '[]'::jsonb,
    duplicate_group_count integer not null default 0,
    duplicate_max_severity text check (duplicate_max_severity in ('low', 'medium', 'high', 'critical') or duplicate_max_severity is null),
    duplicate_primary_candidate_id text,
    completeness_score integer not null default 0,
    search_text text,
    source_hash text not null,
    refreshed_at timestamptz not null default now()
);

alter table public.app_contact_current
    add column if not exists active_search_count integer not null default 0,
    add column if not exists total_search_count integer not null default 0,
    add column if not exists has_contact_detail boolean not null default false,
    add column if not exists contact_detail_synced_at text,
    add column if not exists supabase_sync_eligible boolean not null default false,
    add column if not exists eligibility_reasons_json jsonb not null default '[]'::jsonb;

create table public.app_contact_relation_current (
    relation_key text primary key,
    hektor_contact_id text not null,
    hektor_annonce_id text not null,
    app_dossier_id bigint,
    numero_dossier text,
    numero_mandat text,
    titre_bien text,
    role_contact text not null,
    contact_date_maj text,
    relation_source text not null default 'api_annonce_detail',
    transaction_type text,
    transaction_id text,
    transaction_state text,
    transaction_date text,
    transaction_amount text,
    is_active_annonce boolean not null default false,
    last_seen_at text,
    refreshed_at timestamptz not null default now()
);

create table if not exists public.app_contact_search_current (
    contact_search_key text primary key,
    hektor_contact_id text not null,
    search_index integer not null,
    archive boolean not null default false,
    is_active boolean not null default false,
    offre text,
    villes_json jsonb not null default '[]'::jsonb,
    types_json jsonb not null default '{}'::jsonb,
    criteres_json jsonb not null default '[]'::jsonb,
    prix_min text,
    prix_max text,
    surface_min text,
    surface_max text,
    pieces_min text,
    pieces_max text,
    chambre_min text,
    chambre_max text,
    surface_terrain_min text,
    surface_terrain_max text,
    contact_date_maj text,
    refreshed_at timestamptz not null default now()
);

create table if not exists public.app_contact_duplicate_group_current (
    duplicate_group_id text primary key,
    rule_code text not null,
    severity text not null check (severity in ('low', 'medium', 'high', 'critical')),
    review_status text not null default 'proposed',
    archive_pattern text not null,
    member_count integer not null,
    active_count integer not null,
    archived_count integer not null,
    linked_annonce_count integer not null default 0,
    primary_candidate_hektor_contact_id text,
    normalized_key_hash text not null,
    suspected_mass_archive_error boolean not null default false,
    review_hint text,
    refreshed_at timestamptz not null default now()
);

create table if not exists public.app_contact_duplicate_member_current (
    duplicate_group_id text not null,
    hektor_contact_id text not null,
    is_primary_candidate boolean not null default false,
    archive boolean not null default false,
    display_name text not null,
    email_hash text,
    phone_hash text,
    date_maj text,
    linked_annonce_count integer not null default 0,
    completeness_score integer not null default 0,
    member_rank integer not null default 0,
    refreshed_at timestamptz not null default now(),
    primary key (duplicate_group_id, hektor_contact_id)
);

create index if not exists idx_app_contact_current_search_text
    on public.app_contact_current using gin (to_tsvector('simple', coalesce(search_text, '')));
create index if not exists idx_app_contact_current_archive
    on public.app_contact_current (archive, date_maj desc);
create index if not exists idx_app_contact_current_nego
    on public.app_contact_current (negociateur_email, hektor_negociateur_id);
create index if not exists idx_app_contact_current_agency
    on public.app_contact_current (agence_nom);
create index if not exists idx_app_contact_current_duplicate
    on public.app_contact_current (duplicate_max_severity, duplicate_group_count);
create index if not exists idx_app_contact_current_detail_state
    on public.app_contact_current (has_contact_detail, contact_detail_synced_at desc);
create index if not exists idx_app_contact_relation_contact
    on public.app_contact_relation_current (hektor_contact_id);
create index if not exists idx_app_contact_relation_dossier
    on public.app_contact_relation_current (app_dossier_id);
create index if not exists idx_app_contact_relation_annonce
    on public.app_contact_relation_current (hektor_annonce_id);
create index if not exists idx_app_contact_relation_transaction
    on public.app_contact_relation_current (transaction_type, transaction_id);
create index if not exists idx_app_contact_relation_role_active
    on public.app_contact_relation_current (role_contact, is_active_annonce);
create index if not exists idx_app_contact_search_contact
    on public.app_contact_search_current (hektor_contact_id);
create index if not exists idx_app_contact_search_active
    on public.app_contact_search_current (is_active, archive);
create index if not exists idx_app_contact_duplicate_group_severity
    on public.app_contact_duplicate_group_current (severity, suspected_mass_archive_error);
create index if not exists idx_app_contact_duplicate_member_contact
    on public.app_contact_duplicate_member_current (hektor_contact_id);

create or replace view public.app_contacts_current
with (security_invoker = true)
as
select *
from public.app_contact_current;

create or replace view public.app_contact_relations_current
with (security_invoker = true)
as
select *
from public.app_contact_relation_current;

create or replace view public.app_contact_searches_current
with (security_invoker = true)
as
select *
from public.app_contact_search_current;

create or replace view public.app_contact_duplicate_groups_current
with (security_invoker = true)
as
select *
from public.app_contact_duplicate_group_current;

alter table public.app_contact_current enable row level security;
alter table public.app_contact_relation_current enable row level security;
alter table public.app_contact_search_current enable row level security;
alter table public.app_contact_duplicate_group_current enable row level security;
alter table public.app_contact_duplicate_member_current enable row level security;

drop policy if exists app_contact_current_select_scoped on public.app_contact_current;
create policy app_contact_current_select_scoped
on public.app_contact_current
for select
to authenticated
using (
    public.is_app_global_reader()
    or public.can_access_negotiator_email(negociateur_email)
    or exists (
        select 1
        from public.app_contact_relation_current r
        where r.hektor_contact_id = app_contact_current.hektor_contact_id
          and r.app_dossier_id is not null
          and public.can_access_current_dossier(r.app_dossier_id)
    )
);

drop policy if exists app_contact_relation_current_select_scoped on public.app_contact_relation_current;
create policy app_contact_relation_current_select_scoped
on public.app_contact_relation_current
for select
to authenticated
using (
    public.is_app_global_reader()
    or (
        app_dossier_id is not null
        and public.can_access_current_dossier(app_dossier_id)
    )
);

drop policy if exists app_contact_search_current_select_scoped on public.app_contact_search_current;
create policy app_contact_search_current_select_scoped
on public.app_contact_search_current
for select
to authenticated
using (
    exists (
        select 1
        from public.app_contact_current c
        where c.hektor_contact_id = app_contact_search_current.hektor_contact_id
          and (
              public.is_app_global_reader()
              or public.can_access_negotiator_email(c.negociateur_email)
          )
    )
);

drop policy if exists app_contact_duplicate_group_current_select_admin on public.app_contact_duplicate_group_current;
create policy app_contact_duplicate_group_current_select_admin
on public.app_contact_duplicate_group_current
for select
to authenticated
using (public.is_app_manager_or_admin());

drop policy if exists app_contact_duplicate_member_current_select_admin on public.app_contact_duplicate_member_current;
create policy app_contact_duplicate_member_current_select_admin
on public.app_contact_duplicate_member_current
for select
to authenticated
using (public.is_app_manager_or_admin());

grant select on public.app_contacts_current to authenticated;
grant select on public.app_contact_relations_current to authenticated;
grant select on public.app_contact_searches_current to authenticated;
grant select on public.app_contact_duplicate_groups_current to authenticated;
grant select on public.app_contact_current to authenticated;
grant select on public.app_contact_relation_current to authenticated;
grant select on public.app_contact_search_current to authenticated;
grant select on public.app_contact_duplicate_group_current to authenticated;
grant select on public.app_contact_duplicate_member_current to authenticated;

grant all on public.app_contact_current to service_role;
grant all on public.app_contact_relation_current to service_role;
grant all on public.app_contact_search_current to service_role;
grant all on public.app_contact_duplicate_group_current to service_role;
grant all on public.app_contact_duplicate_member_current to service_role;

comment on table public.app_contact_current is 'Index limite des contacts Hektor expose a l app. Les payloads Hektor complets restent uniquement dans le miroir local.';
comment on table public.app_contact_relation_current is 'Relations normalisees contacts-annonces, y compris historique offre/compromis/vente. La selection du dossier principal reste portee par case_dossier_source cote local.';
comment on table public.app_contact_search_current is 'Recherches acquereurs normalisees depuis ContactById. Par defaut le push limite aux recherches actives.';
comment on table public.app_contact_duplicate_group_current is 'Groupes de doublons contacts proposes par audit local, sans suppression automatique.';
comment on table public.app_contact_duplicate_member_current is 'Membres des groupes doublons. Acces reserve manager/admin.';

commit;
