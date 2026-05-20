create or replace function public.app_console_can_access_dossier(
    target_app_dossier_id bigint,
    target_hektor_annonce_id text
)
returns boolean
language plpgsql
stable
security definer
set search_path = public
as $$
declare
    current_app_role text;
    current_email text;
begin
    select p.role::text, p.email
    into current_app_role, current_email
    from public.app_user_profile p
    where p.id = auth.uid()
      and p.is_active = true
    limit 1;

    if current_app_role in ('admin', 'manager') then
        return true;
    end if;

    if current_app_role = 'commercial' then
        return exists (
            select 1
            from public.app_dossiers_current target
            where (
                    (target_app_dossier_id is not null and target.app_dossier_id = target_app_dossier_id)
                 or (nullif(target_hektor_annonce_id, '') is not null and target.hektor_annonce_id::text = target_hektor_annonce_id)
                )
              and lower(coalesce(target.negociateur_email, '')) = lower(coalesce(current_email, ''))
        )
        or exists (
            select 1
            from public.app_archive_annonce_index_current target
            where (
                    (target_app_dossier_id is not null and target.app_archive_id = target_app_dossier_id)
                 or (nullif(target_hektor_annonce_id, '') is not null and target.hektor_annonce_id::text = target_hektor_annonce_id)
                )
              and lower(coalesce(target.negociateur_email, '')) = lower(coalesce(current_email, ''))
        );
    end if;

    return false;
end;
$$;

drop view if exists public.app_annonces_current;
