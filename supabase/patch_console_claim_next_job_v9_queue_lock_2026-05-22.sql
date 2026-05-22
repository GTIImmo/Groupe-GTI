create or replace function public.app_console_claim_next_job(
    p_worker_id text default null::text,
    p_worker_kind text default 'actions'::text
)
returns setof app_console_job
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
    worker_kind text := lower(coalesce(nullif(p_worker_kind, ''), 'actions'));
    is_current_worker boolean := coalesce(p_worker_id, '') like '%:scheduled:v9';
begin
    update public.app_console_job j
    set status = 'error',
        finished_at = now(),
        updated_at = now(),
        error_message = coalesce(nullif(j.error_message, ''), 'Job interrompu automatiquement: execution running trop ancienne (> 30 minutes). Relancer la demande si necessaire.')
    where j.status = 'running'
      and coalesce(j.started_at, j.updated_at, j.requested_at, j.created_at) < now() - interval '30 minutes';

    return query
    with next_job as (
        select j.id
        from public.app_console_job j
        where j.status = 'pending'
          and is_current_worker
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
                    'sync_hektor_photos',
                    'upload_hektor_photo',
                    'prepare_archived_annonce_detail',
                    'prepare_historical_annonce_detail'
                ))
             or (worker_kind = 'admin' and j.job_type in (
                    'delete_hektor_annonce',
                    'archive_hektor_annonce',
                    'restore_hektor_annonce',
                    'change_hektor_annonce_status',
                    'assign_hektor_annonce_negotiator'
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
                j.job_type not in ('upload_document_to_hektor', 'upload_hektor_photo')
             or exists (
                    select 1
                    from storage.objects o
                    where o.bucket_id = 'hektor-console-documents'
                      and o.name = j.payload_json->>'temp_storage_path'
                )
          )
          and (
                nullif(j.hektor_annonce_id, '') is null
             or not exists (
                    select 1
                    from public.app_console_job running_job
                    where running_job.status = 'running'
                      and running_job.hektor_annonce_id = j.hektor_annonce_id
                      and running_job.id <> j.id
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
$function$;
