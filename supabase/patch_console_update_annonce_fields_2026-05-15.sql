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
        'link_hektor_mandant',
        'update_hektor_annonce_fields',
        'delete_hektor_annonce',
        'create_hektor_draft_annonce',
        'refresh_console_data',
        'archive_cloud_documents'
    ));

create or replace function public.app_console_create_update_annonce_job(
    target_app_dossier_id bigint,
    target_hektor_annonce_id text,
    update_fields jsonb,
    update_priority integer default 15
)
returns public.app_console_job
language plpgsql
security definer
set search_path = public
as $$
declare
    created_job public.app_console_job;
begin
    if nullif(trim(coalesce(target_hektor_annonce_id, '')), '') is null then
        raise exception 'missing_hektor_annonce_id' using errcode = '22023';
    end if;

    if coalesce(jsonb_typeof(update_fields), '') <> 'object' or update_fields = '{}'::jsonb then
        raise exception 'missing_update_fields' using errcode = '22023';
    end if;

    if not public.app_console_can_request_job('update_hektor_annonce_fields', target_app_dossier_id, target_hektor_annonce_id) then
        raise exception 'forbidden_update_annonce' using errcode = '42501';
    end if;

    insert into public.app_console_job (
        job_type,
        app_dossier_id,
        hektor_annonce_id,
        payload_json,
        status,
        priority,
        requested_by,
        requested_at
    )
    values (
        'update_hektor_annonce_fields',
        target_app_dossier_id,
        trim(target_hektor_annonce_id),
        jsonb_build_object(
            'hektor_annonce_id', trim(target_hektor_annonce_id),
            'app_dossier_id', target_app_dossier_id,
            'fields_json', update_fields
        ),
        'pending',
        coalesce(update_priority, 15),
        auth.uid(),
        now()
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

    if current_app_role = 'admin' then
        return true;
    end if;

    if current_app_role = 'manager' then
        return target_job_type <> 'delete_hektor_annonce';
    end if;

    if current_app_role = 'commercial'
       and target_job_type in (
           'prepare_document_cloud',
           'upload_document_to_hektor',
           'delete_document_from_hektor',
           'link_hektor_mandant',
           'update_hektor_annonce_fields'
       ) then
        return public.app_console_can_access_dossier(target_app_dossier_id, target_hektor_annonce_id);
    end if;

    return false;
end;
$$;

grant execute on function public.app_console_create_update_annonce_job(bigint, text, jsonb, integer) to authenticated;
grant execute on function public.app_console_can_request_job(text, bigint, text) to authenticated;

commit;
