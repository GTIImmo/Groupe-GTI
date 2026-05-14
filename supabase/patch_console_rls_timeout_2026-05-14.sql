-- Correctif timeout RLS Console documents.
-- Cause visee: la fonction d'acces agence des commerciaux pouvait scanner app_dossier_current
-- pour chaque document Storage/REST.

create index if not exists idx_app_dossier_current_agence_email_lower
on public.app_dossier_current (agence_nom, lower(coalesce(negociateur_email, '')))
where nullif(agence_nom, '') is not null;

create index if not exists idx_app_dossier_current_email_lower
on public.app_dossier_current (lower(coalesce(negociateur_email, '')))
where nullif(negociateur_email, '') is not null;

create index if not exists idx_app_console_document_dossier_name
on public.app_console_document (app_dossier_id, document_type, document_name);

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
    target_agence text;
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
        if target_app_dossier_id is not null then
            select d.agence_nom
            into target_agence
            from public.app_dossier_current d
            where d.app_dossier_id = target_app_dossier_id
            limit 1;
        elsif nullif(target_hektor_annonce_id, '') is not null
              and target_hektor_annonce_id ~ '^[0-9]+$' then
            select d.agence_nom
            into target_agence
            from public.app_dossier_current d
            where d.hektor_annonce_id = target_hektor_annonce_id::bigint
            limit 1;
        end if;

        if nullif(target_agence, '') is null or nullif(current_email, '') is null then
            return false;
        end if;

        return exists (
            select 1
            from public.app_dossier_current owned
            where owned.agence_nom = target_agence
              and lower(coalesce(owned.negociateur_email, '')) = lower(coalesce(current_email, ''))
            limit 1
        );
    end if;

    return false;
end;
$$;

create or replace function public.app_console_can_request_job(
    target_job_type text,
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
begin
    current_app_role := public.app_console_current_role();

    if current_app_role in ('admin', 'manager') then
        return true;
    end if;

    if current_app_role = 'commercial'
       and target_job_type in ('prepare_document_cloud', 'upload_document_to_hektor', 'delete_document_from_hektor') then
        return public.app_console_can_access_dossier(target_app_dossier_id, target_hektor_annonce_id);
    end if;

    return false;
end;
$$;

grant execute on function public.app_console_can_access_dossier(bigint, text) to authenticated;
grant execute on function public.app_console_can_request_job(text, bigint, text) to authenticated;
