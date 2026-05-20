create table if not exists public.app_archive_annonce_detail_cache (
    hektor_annonce_id bigint primary key,
    app_archive_id bigint,
    detail_payload_json jsonb not null,
    requested_by uuid,
    prepared_at timestamptz not null default now(),
    expires_at timestamptz not null default (now() + interval '2 hours'),
    source_hash text,
    source_updated_at timestamptz
);

create index if not exists idx_app_archive_annonce_detail_cache_expires
on public.app_archive_annonce_detail_cache (expires_at);

alter table public.app_archive_annonce_detail_cache enable row level security;

drop policy if exists "app_archive_annonce_detail_cache_select_scope" on public.app_archive_annonce_detail_cache;
create policy "app_archive_annonce_detail_cache_select_scope"
on public.app_archive_annonce_detail_cache
for select
using (
    public.app_console_can_access_dossier(
        app_archive_id,
        hektor_annonce_id::text
    )
);

drop policy if exists "app_archive_annonce_detail_cache_delete_admin" on public.app_archive_annonce_detail_cache;
create policy "app_archive_annonce_detail_cache_delete_admin"
on public.app_archive_annonce_detail_cache
for delete
using (public.app_console_current_role() in ('admin', 'manager'));

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
    'upload_hektor_photo',
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
    'archive_cloud_documents',
    'prepare_archived_annonce_detail'
));

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
       and target_job_type in (
            'prepare_document_cloud',
            'upload_document_to_hektor',
            'prepare_archived_annonce_detail'
       ) then
        return public.app_console_can_access_dossier(target_app_dossier_id, target_hektor_annonce_id);
    end if;

    return false;
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
                    'sync_hektor_photos',
                    'upload_hektor_photo',
                    'prepare_archived_annonce_detail'
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
