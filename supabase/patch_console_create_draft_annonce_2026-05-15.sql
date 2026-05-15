begin;

alter table public.app_console_job
drop constraint if exists app_console_job_job_type_check;

alter table public.app_console_job
add constraint app_console_job_job_type_check
check (job_type in (
    'sync_console_documents',
    'prepare_document_cloud',
    'upload_document_to_hektor',
    'delete_document_from_hektor',
    'create_hektor_draft_annonce',
    'refresh_console_data',
    'archive_cloud_documents'
));

create or replace function public.app_console_create_draft_annonce_job(
    draft_payload jsonb,
    draft_priority integer default 20
)
returns public.app_console_job
language plpgsql
security definer
set search_path = public
as $$
declare
    current_app_role text;
    current_email text;
    requested_agency text;
    created_job public.app_console_job;
begin
    select p.role::text, p.email
    into current_app_role, current_email
    from public.app_user_profile p
    where p.id = auth.uid()
      and p.is_active = true
    limit 1;

    if current_app_role is null then
        raise exception 'user_not_allowed';
    end if;

    if current_app_role not in ('admin', 'manager', 'commercial') then
        raise exception 'role_not_allowed';
    end if;

    requested_agency := nullif(btrim(coalesce(draft_payload->>'agence_nom', '')), '');

    if current_app_role = 'commercial' then
        if requested_agency is null or nullif(current_email, '') is null then
            raise exception 'agency_required';
        end if;

        if not exists (
            select 1
            from public.app_dossier_current d
            where d.agence_nom = requested_agency
              and lower(coalesce(d.negociateur_email, '')) = lower(coalesce(current_email, ''))
            limit 1
        ) then
            raise exception 'agency_forbidden';
        end if;
    end if;

    insert into public.app_console_job (
        job_type,
        app_dossier_id,
        hektor_annonce_id,
        payload_json,
        status,
        priority,
        requested_by
    )
    values (
        'create_hektor_draft_annonce',
        null,
        null,
        coalesce(draft_payload, '{}'::jsonb) || jsonb_build_object(
            'creation_mode', 'draft_only',
            'requested_agence_nom', requested_agency
        ),
        'pending',
        coalesce(draft_priority, 20),
        auth.uid()
    )
    returning * into created_job;

    return created_job;
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

grant execute on function public.app_console_create_draft_annonce_job(jsonb, integer) to authenticated;
grant execute on function public.app_console_can_request_job(text, bigint, text) to authenticated;

commit;
