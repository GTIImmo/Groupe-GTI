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
        'sync_hektor_photos',
        'link_hektor_mandant',
        'create_hektor_mandant_contact',
        'update_hektor_mandant_contact',
        'update_hektor_annonce_fields',
        'create_hektor_mandat_auto_number',
        'delete_hektor_annonce',
        'create_hektor_draft_annonce',
        'matterport_online',
        'matterport_offline',
        'matterport_archive',
        'matterport_reactivate',
        'refresh_console_data',
        'archive_cloud_documents'
    ));

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
           'sync_hektor_photos',
           'link_hektor_mandant',
           'create_hektor_mandant_contact',
           'update_hektor_mandant_contact',
           'update_hektor_annonce_fields',
           'create_hektor_mandat_auto_number',
           'matterport_online',
           'matterport_offline',
           'matterport_archive',
           'matterport_reactivate'
       ) then
        return public.app_console_can_access_dossier(target_app_dossier_id, target_hektor_annonce_id);
    end if;

    return false;
end;
$$;

create or replace function public.app_console_create_matterport_action_job(
    target_app_dossier_id bigint,
    target_hektor_annonce_id text,
    target_matterport_model_id text,
    matterport_action text,
    job_priority integer default 18
)
returns public.app_console_job
language plpgsql
security definer
set search_path = public
as $$
declare
    clean_annonce_id text;
    clean_model_id text;
    clean_action text;
    target_job_type text;
    linked_model record;
    created_job public.app_console_job;
begin
    clean_annonce_id := nullif(trim(coalesce(target_hektor_annonce_id, '')), '');
    clean_model_id := nullif(trim(coalesce(target_matterport_model_id, '')), '');
    clean_action := lower(nullif(trim(coalesce(matterport_action, '')), ''));

    if clean_annonce_id is null then
        raise exception 'missing_hektor_annonce_id' using errcode = '22023';
    end if;

    if clean_model_id is null or clean_model_id !~ '^[A-Za-z0-9_-]+$' then
        raise exception 'invalid_matterport_model_id' using errcode = '22023';
    end if;

    target_job_type := case clean_action
        when 'online' then 'matterport_online'
        when 'offline' then 'matterport_offline'
        when 'archive' then 'matterport_archive'
        when 'reactivate' then 'matterport_reactivate'
        when 'unarchive' then 'matterport_reactivate'
        else null
    end;

    if target_job_type is null then
        raise exception 'invalid_matterport_action' using errcode = '22023';
    end if;

    if not public.app_console_can_request_job(target_job_type, target_app_dossier_id, clean_annonce_id) then
        raise exception 'forbidden_matterport_action' using errcode = '42501';
    end if;

    select m.matterport_model_id,
           m.matterport_name,
           m.matterport_url,
           g.id as group_id,
           g.numero_mandat
    into linked_model
    from public.app_matterport_group g
    join public.app_matterport_group_model m on m.group_id = g.id
    where g.hektor_annonce_id::text = clean_annonce_id
      and m.matterport_model_id = clean_model_id
    limit 1;

    if linked_model.matterport_model_id is null then
        raise exception 'matterport_model_not_linked_to_dossier' using errcode = '22023';
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
        target_job_type,
        target_app_dossier_id,
        clean_annonce_id,
        jsonb_build_object(
            'matterport_model_id', clean_model_id,
            'matterport_name', linked_model.matterport_name,
            'matterport_url', coalesce(linked_model.matterport_url, 'https://my.matterport.com/show/?m=' || clean_model_id),
            'matterport_action', clean_action,
            'matterport_group_id', linked_model.group_id,
            'numero_mandat', linked_model.numero_mandat,
            'hektor_annonce_id', clean_annonce_id,
            'app_dossier_id', target_app_dossier_id
        ),
        'pending',
        coalesce(job_priority, 18),
        auth.uid(),
        now()
    )
    returning * into created_job;

    return created_job;
end;
$$;

create or replace function public.app_console_claim_next_job(
    p_worker_id text default null,
    p_worker_kind text default 'actions'
)
returns setof public.app_console_job
language plpgsql
security definer
set search_path = public
as $$
declare
    worker_kind text := lower(coalesce(nullif(p_worker_kind, ''), 'actions'));
begin
    return query
    with next_job as (
        select j.id
        from public.app_console_job j
        where j.status = 'pending'
          and (
                worker_kind = 'all'
             or (worker_kind = 'actions' and j.job_type in (
                    'create_hektor_draft_annonce',
                    'update_hektor_annonce_fields',
                    'create_hektor_mandant_contact',
                    'update_hektor_mandant_contact',
                    'create_hektor_mandat_auto_number',
                    'link_hektor_mandant'
                ))
             or (worker_kind = 'documents' and j.job_type in (
                    'sync_console_documents',
                    'prepare_document_cloud',
                    'upload_document_to_hektor',
                    'delete_document_from_hektor',
                    'sync_hektor_photos'
                ))
             or (worker_kind = 'admin' and j.job_type in (
                    'delete_hektor_annonce'
                ))
             or (worker_kind = 'matterport' and j.job_type in (
                    'matterport_online',
                    'matterport_offline',
                    'matterport_archive',
                    'matterport_reactivate'
                ))
             or (worker_kind = 'sync_light' and j.job_type in (
                    'refresh_console_data'
                ))
             or (worker_kind = 'sync_full' and j.job_type in (
                    'archive_cloud_documents'
                ))
             or (worker_kind = 'sync' and j.job_type in (
                    'refresh_console_data',
                    'archive_cloud_documents'
                ))
          )
          and (
                j.job_type <> 'upload_document_to_hektor'
             or exists (
                    select 1
                    from storage.objects o
                    where o.bucket_id = 'hektor-console-documents'
                      and o.name = j.payload_json->>'temp_storage_path'
                )
          )
        order by j.priority asc, j.requested_at asc
        for update skip locked
        limit 1
    )
    update public.app_console_job j
    set status = 'running',
        started_at = now(),
        worker_id = p_worker_id,
        attempt_count = j.attempt_count + 1,
        updated_at = now()
    from next_job
    where j.id = next_job.id
    returning j.*;
end;
$$;

grant execute on function public.app_console_can_request_job(text, bigint, text) to authenticated;
grant execute on function public.app_console_create_matterport_action_job(bigint, text, text, text, integer) to authenticated;
grant execute on function public.app_console_create_matterport_action_job(bigint, text, text, text, integer) to service_role;
grant execute on function public.app_console_claim_next_job(text, text) to service_role;

notify pgrst, 'reload schema';

commit;
