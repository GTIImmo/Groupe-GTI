-- Correctif timeout REST app_work_items_current.
-- Optimise les policies RLS pour eviter d'appeler les fonctions de role global ligne par ligne.

create index if not exists idx_app_work_item_current_dossier
on public.app_work_item_current (app_dossier_id);

create index if not exists idx_app_work_item_current_list_order
on public.app_work_item_current (has_open_blocker desc, priority asc, date_entree_file desc, app_dossier_id);

create index if not exists idx_app_delta_run_scope_status
on public.app_delta_run (scope, status);

do $$
begin
  if to_regclass('public.app_work_item_v1') is not null then
    execute 'create index if not exists idx_app_work_item_v1_dossier on public.app_work_item_v1 (app_dossier_id)';
    execute 'create index if not exists idx_app_work_item_v1_list_order on public.app_work_item_v1 (has_open_blocker desc, priority asc, date_entree_file desc, app_dossier_id)';
  end if;

  if to_regclass('public.app_dossier_v1') is not null then
    execute 'create index if not exists idx_app_dossier_v1_dossier_email on public.app_dossier_v1 (app_dossier_id, lower(coalesce(negociateur_email, '''')))';
  end if;
end
$$;

create or replace function public.can_access_current_dossier(target_app_dossier_id bigint)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select exists (
        select 1
        from public.app_dossier_current d
        where d.app_dossier_id = target_app_dossier_id
          and public.can_access_negotiator_email(d.negociateur_email)
    );
$$;

create or replace function public.can_access_v1_dossier(target_app_dossier_id bigint)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select exists (
        select 1
        from public.app_dossier_v1 d
        where d.app_dossier_id = target_app_dossier_id
          and public.can_access_negotiator_email(d.negociateur_email)
    );
$$;

drop policy if exists "app_dossier_current_select_scoped_users" on public.app_dossier_current;
create policy "app_dossier_current_select_scoped_users"
on public.app_dossier_current
for select
using (
  (select public.is_app_global_reader())
  or public.can_access_negotiator_email(negociateur_email)
);

drop policy if exists "app_dossier_detail_current_select_scoped_users" on public.app_dossier_detail_current;
create policy "app_dossier_detail_current_select_scoped_users"
on public.app_dossier_detail_current
for select
using (
  (select public.is_app_global_reader())
  or public.can_access_current_dossier(app_dossier_id)
);

drop policy if exists "app_work_item_current_select_scoped_users" on public.app_work_item_current;
create policy "app_work_item_current_select_scoped_users"
on public.app_work_item_current
for select
using (
  (select public.is_app_global_reader())
  or public.can_access_current_dossier(app_dossier_id)
);

do $$
begin
  if to_regclass('public.app_dossier_v1') is not null then
    execute 'drop policy if exists "app_dossiers_select_scoped_users" on public.app_dossier_v1';
    execute $sql$
      create policy "app_dossiers_select_scoped_users"
      on public.app_dossier_v1
      for select
      using (
        (select public.is_app_global_reader())
        or public.can_access_negotiator_email(negociateur_email)
      )
    $sql$;
  end if;

  if to_regclass('public.app_dossier_detail_v1') is not null then
    execute 'drop policy if exists "app_dossier_details_select_scoped_users" on public.app_dossier_detail_v1';
    execute $sql$
      create policy "app_dossier_details_select_scoped_users"
      on public.app_dossier_detail_v1
      for select
      using (
        (select public.is_app_global_reader())
        or public.can_access_v1_dossier(app_dossier_id)
      )
    $sql$;
  end if;

  if to_regclass('public.app_work_item_v1') is not null then
    execute 'drop policy if exists "app_work_items_select_scoped_users" on public.app_work_item_v1';
    execute $sql$
      create policy "app_work_items_select_scoped_users"
      on public.app_work_item_v1
      for select
      using (
        (select public.is_app_global_reader())
        or public.can_access_v1_dossier(app_dossier_id)
      )
    $sql$;
  end if;
end
$$;
