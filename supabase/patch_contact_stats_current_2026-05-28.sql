begin;

create table if not exists public.app_contact_stats_current (
    scope text primary key,
    total bigint not null default 0,
    active bigint not null default 0,
    archived bigint not null default 0,
    duplicates bigint not null default 0,
    high_risk_duplicates bigint not null default 0,
    linked bigint not null default 0,
    search_contacts bigint not null default 0,
    active_search_contacts bigint not null default 0,
    eligible bigint not null default 0,
    with_detail bigint not null default 0,
    active_or_eligible bigint not null default 0,
    refreshed_at timestamptz not null default now()
);

alter table public.app_contact_stats_current enable row level security;

drop policy if exists app_contact_stats_current_select on public.app_contact_stats_current;
create policy app_contact_stats_current_select
on public.app_contact_stats_current
for select
to authenticated
using (public.is_app_user_active());

grant select on public.app_contact_stats_current to authenticated;
grant all on public.app_contact_stats_current to service_role;

insert into public.app_contact_stats_current (
    scope,
    total,
    active,
    archived,
    duplicates,
    high_risk_duplicates,
    linked,
    search_contacts,
    active_search_contacts,
    eligible,
    with_detail,
    active_or_eligible,
    refreshed_at
)
select
    'active_or_eligible',
    count(*)::bigint,
    count(*) filter (where coalesce(archive, false) = false)::bigint,
    count(*) filter (where coalesce(archive, false) = true)::bigint,
    count(*) filter (where coalesce(duplicate_group_count, 0) > 0)::bigint,
    count(*) filter (where duplicate_max_severity in ('high', 'critical'))::bigint,
    count(*) filter (where coalesce(linked_annonce_count, 0) > 0)::bigint,
    count(*) filter (where coalesce(total_search_count, 0) > 0)::bigint,
    count(*) filter (where coalesce(active_search_count, 0) > 0)::bigint,
    count(*) filter (where coalesce(supabase_sync_eligible, false) = true)::bigint,
    count(*) filter (where coalesce(has_contact_detail, false) = true)::bigint,
    count(*) filter (where coalesce(archive, false) = false or coalesce(supabase_sync_eligible, false) = true)::bigint,
    now()
from public.app_contact_current
on conflict (scope) do update set
    total = excluded.total,
    active = excluded.active,
    archived = excluded.archived,
    duplicates = excluded.duplicates,
    high_risk_duplicates = excluded.high_risk_duplicates,
    linked = excluded.linked,
    search_contacts = excluded.search_contacts,
    active_search_contacts = excluded.active_search_contacts,
    eligible = excluded.eligible,
    with_detail = excluded.with_detail,
    active_or_eligible = excluded.active_or_eligible,
    refreshed_at = excluded.refreshed_at;

commit;
