begin;

create table if not exists public.app_console_photo (
    id uuid primary key default gen_random_uuid(),
    app_dossier_id bigint,
    hektor_annonce_id text not null,
    hektor_photo_id text not null,
    filename text,
    url_preview text,
    url_hd text,
    visible boolean not null default true,
    legend text,
    sort_order integer,
    source text not null default 'hektor_console',
    source_json jsonb not null default '{}'::jsonb,
    synced_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (hektor_annonce_id, hektor_photo_id)
);

create index if not exists idx_app_console_photo_dossier
on public.app_console_photo (app_dossier_id, visible, sort_order);

create index if not exists idx_app_console_photo_annonce
on public.app_console_photo (hektor_annonce_id, visible, sort_order);

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

    if current_app_role in ('admin', 'manager') then
        return true;
    end if;

    if current_app_role = 'commercial'
       and target_job_type in (
            'prepare_document_cloud',
            'upload_document_to_hektor',
            'delete_document_from_hektor',
            'sync_hektor_photos',
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

create or replace function public.app_console_create_sync_photos_job(
    target_app_dossier_id bigint,
    target_hektor_annonce_id text,
    job_priority integer default 28
)
returns public.app_console_job
language plpgsql
security definer
set search_path = public
as $$
declare
    created_job public.app_console_job;
begin
    if not public.app_console_can_request_job('sync_hektor_photos', target_app_dossier_id, target_hektor_annonce_id) then
        raise exception 'job_forbidden';
    end if;

    select *
    into created_job
    from public.app_console_job j
    where j.job_type = 'sync_hektor_photos'
      and j.status in ('pending', 'running')
      and (
            (target_app_dossier_id is not null and j.app_dossier_id = target_app_dossier_id)
         or (nullif(target_hektor_annonce_id, '') is not null and j.hektor_annonce_id = target_hektor_annonce_id)
      )
    order by j.requested_at desc
    limit 1;

    if found then
        return created_job;
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
        'sync_hektor_photos',
        target_app_dossier_id,
        target_hektor_annonce_id,
        jsonb_build_object(
            'app_dossier_id', target_app_dossier_id,
            'hektor_annonce_id', target_hektor_annonce_id
        ),
        'pending',
        coalesce(job_priority, 28),
        auth.uid()
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

alter table public.app_console_photo enable row level security;

drop policy if exists "app_console_photo_select_scope" on public.app_console_photo;
create policy "app_console_photo_select_scope"
on public.app_console_photo
for select
using (public.app_console_can_access_dossier(app_dossier_id, hektor_annonce_id));

grant select on public.app_console_photo to authenticated;
grant execute on function public.app_console_create_sync_photos_job(bigint, text, integer) to authenticated;
grant execute on function public.app_console_can_request_job(text, bigint, text) to authenticated;
grant execute on function public.app_console_claim_next_job(text, text) to service_role;

notify pgrst, 'reload schema';

commit;
