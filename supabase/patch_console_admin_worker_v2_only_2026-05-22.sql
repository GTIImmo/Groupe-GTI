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
    is_admin_v2 boolean := coalesce(p_worker_id, '') like '%:admin:scheduled:v2';
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
                    'sync_hektor_photos',
                    'upload_hektor_photo',
                    'prepare_archived_annonce_detail',
                    'prepare_historical_annonce_detail'
                ))
             or (worker_kind = 'admin' and is_admin_v2 and j.job_type in (
                    'delete_hektor_annonce',
                    'archive_hektor_annonce',
                    'restore_hektor_annonce',
                    'change_hektor_annonce_status'
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

grant execute on function public.app_console_claim_next_job(text, text) to service_role;
