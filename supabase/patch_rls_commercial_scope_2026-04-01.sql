create or replace function public.is_app_global_reader()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select exists (
        select 1
        from public.app_user_profile p
        where p.id = auth.uid()
          and p.is_active = true
          and p.role in ('admin', 'manager', 'lecture')
    );
$$;

create or replace function public.can_access_negotiator_email(target_email text)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select exists (
        select 1
        from public.app_user_profile p
        where p.id = auth.uid()
          and p.is_active = true
          and (
            p.role in ('admin', 'manager', 'lecture')
            or (
              p.role = 'commercial'
              and nullif(lower(coalesce(target_email, '')), '') is not null
              and lower(coalesce(p.email, '')) = lower(coalesce(target_email, ''))
            )
          )
    );
$$;

create or replace function public.can_access_current_dossier(target_app_dossier_id bigint)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select
      public.is_app_global_reader()
      or exists (
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
    select
      public.is_app_global_reader()
      or exists (
        select 1
        from public.app_dossier_v1 d
        where d.app_dossier_id = target_app_dossier_id
          and public.can_access_negotiator_email(d.negociateur_email)
      );
$$;

do $$
begin
  if to_regclass('public.app_dossier_v1') is not null then
    execute 'drop policy if exists "app_dossiers_select_active_users" on public.app_dossier_v1';
    execute 'drop policy if exists "app_dossiers_select_scoped_users" on public.app_dossier_v1';
    execute $sql$
      create policy "app_dossiers_select_scoped_users"
      on public.app_dossier_v1
      for select
      using (public.can_access_negotiator_email(negociateur_email))
    $sql$;
  end if;

  if to_regclass('public.app_dossier_detail_v1') is not null then
    execute 'drop policy if exists "app_dossier_details_select_active_users" on public.app_dossier_detail_v1';
    execute 'drop policy if exists "app_dossier_details_select_scoped_users" on public.app_dossier_detail_v1';
    execute $sql$
      create policy "app_dossier_details_select_scoped_users"
      on public.app_dossier_detail_v1
      for select
      using (public.can_access_v1_dossier(app_dossier_id))
    $sql$;
  end if;

  if to_regclass('public.app_work_item_v1') is not null then
    execute 'drop policy if exists "app_work_items_select_active_users" on public.app_work_item_v1';
    execute 'drop policy if exists "app_work_items_select_scoped_users" on public.app_work_item_v1';
    execute $sql$
      create policy "app_work_items_select_scoped_users"
      on public.app_work_item_v1
      for select
      using (public.can_access_v1_dossier(app_dossier_id))
    $sql$;
  end if;

  if to_regclass('public.app_dossier_current') is not null then
    execute 'drop policy if exists "app_dossier_current_select_active_users" on public.app_dossier_current';
    execute 'drop policy if exists "app_dossier_current_select_scoped_users" on public.app_dossier_current';
    execute $sql$
      create policy "app_dossier_current_select_scoped_users"
      on public.app_dossier_current
      for select
      using (public.can_access_negotiator_email(negociateur_email))
    $sql$;
  end if;

  if to_regclass('public.app_dossier_detail_current') is not null then
    execute 'drop policy if exists "app_dossier_detail_current_select_active_users" on public.app_dossier_detail_current';
    execute 'drop policy if exists "app_dossier_detail_current_select_scoped_users" on public.app_dossier_detail_current';
    execute $sql$
      create policy "app_dossier_detail_current_select_scoped_users"
      on public.app_dossier_detail_current
      for select
      using (public.can_access_current_dossier(app_dossier_id))
    $sql$;
  end if;

  if to_regclass('public.app_work_item_current') is not null then
    execute 'drop policy if exists "app_work_item_current_select_active_users" on public.app_work_item_current';
    execute 'drop policy if exists "app_work_item_current_select_scoped_users" on public.app_work_item_current';
    execute $sql$
      create policy "app_work_item_current_select_scoped_users"
      on public.app_work_item_current
      for select
      using (public.can_access_current_dossier(app_dossier_id))
    $sql$;
  end if;

  if to_regclass('public.app_mandat_current') is not null then
    execute 'drop policy if exists "app_mandat_current_select_active_users" on public.app_mandat_current';
    execute 'drop policy if exists "app_mandat_current_select_scoped_users" on public.app_mandat_current';
    execute $sql$
      create policy "app_mandat_current_select_scoped_users"
      on public.app_mandat_current
      for select
      using (public.can_access_current_dossier(app_dossier_id))
    $sql$;
  end if;

  if to_regclass('public.app_mandat_register_current') is not null then
    execute 'drop policy if exists "app_mandat_register_current_select_active_users" on public.app_mandat_register_current';
    execute 'drop policy if exists "app_mandat_register_current_select_scoped_users" on public.app_mandat_register_current';
    execute $sql$
      create policy "app_mandat_register_current_select_scoped_users"
      on public.app_mandat_register_current
      for select
      using (
        case
          when app_dossier_id is not null then public.can_access_current_dossier(app_dossier_id)
          else public.is_app_manager_or_admin()
        end
      )
    $sql$;
  end if;

  if to_regclass('public.app_mandat_broadcast_current') is not null then
    execute 'drop policy if exists "app_mandat_broadcast_current_select_active_users" on public.app_mandat_broadcast_current';
    execute 'drop policy if exists "app_mandat_broadcast_current_select_scoped_users" on public.app_mandat_broadcast_current';
    execute $sql$
      create policy "app_mandat_broadcast_current_select_scoped_users"
      on public.app_mandat_broadcast_current
      for select
      using (public.can_access_current_dossier(app_dossier_id))
    $sql$;
  end if;

  if to_regclass('public.app_diffusion_request') is not null then
    execute 'drop policy if exists "app_diffusion_request_select_active_users" on public.app_diffusion_request';
    execute 'drop policy if exists "app_diffusion_request_select_scoped_users" on public.app_diffusion_request';
    execute $sql$
      create policy "app_diffusion_request_select_scoped_users"
      on public.app_diffusion_request
      for select
      using (
        public.is_app_global_reader()
        or public.can_access_current_dossier(app_dossier_id)
      )
    $sql$;

    execute 'drop policy if exists "app_diffusion_request_insert_active_users" on public.app_diffusion_request';
    execute 'drop policy if exists "app_diffusion_request_insert_scoped_users" on public.app_diffusion_request';
    execute $sql$
      create policy "app_diffusion_request_insert_scoped_users"
      on public.app_diffusion_request
      for insert
      with check (
        requested_by = auth.uid()
        and (
          public.is_app_global_reader()
          or public.can_access_current_dossier(app_dossier_id)
        )
      )
    $sql$;
  end if;
end
$$;
