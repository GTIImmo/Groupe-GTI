begin;

alter table public.app_hektor_negotiator_agency_directory
add column if not exists is_active boolean not null default false;

alter table public.app_hektor_negotiator_agency_directory
add column if not exists active_source text not null default 'unknown';

alter table public.app_hektor_negotiator_agency_directory
add column if not exists active_refreshed_at timestamptz not null default now();

create index if not exists idx_app_hektor_negotiator_agency_directory_active_user
on public.app_hektor_negotiator_agency_directory (is_active, hektor_user_id);

update public.app_hektor_negotiator_agency_directory d
set is_active = exists (
        select 1
        from public.app_user_directory u
        where u.id_user = d.hektor_user_id
          and upper(coalesce(u.user_type, '')) = 'NEGO'
    ),
    active_source = case
        when exists (
            select 1
            from public.app_user_directory u
            where u.id_user = d.hektor_user_id
              and upper(coalesce(u.user_type, '')) = 'NEGO'
        ) then 'users_of_parent_nego'
        else 'local_hektor_negociateur_inactive'
    end,
    active_refreshed_at = now();

comment on column public.app_hektor_negotiator_agency_directory.is_active
is 'Vrai uniquement si le idUser Hektor est present dans app_user_directory comme NEGO actif.';

comment on column public.app_hektor_negotiator_agency_directory.active_source
is 'Source du statut actif/inactif calcule pendant la synchronisation annuaire.';

comment on column public.app_hektor_negotiator_agency_directory.active_refreshed_at
is 'Date du dernier recalcul du statut actif/inactif du rattachement negociateur/agence.';

commit;
