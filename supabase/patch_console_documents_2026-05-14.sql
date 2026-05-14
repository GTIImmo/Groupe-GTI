create extension if not exists pgcrypto;

create table if not exists public.app_console_document (
    id uuid primary key default gen_random_uuid(),
    app_dossier_id bigint,
    hektor_annonce_id text not null,
    hektor_document_id text,
    document_type text,
    document_name text not null,
    source text not null default 'hektor_console',
    visibility text not null default 'private'
        check (visibility in ('private', 'shared', 'unknown')),
    storage_bucket text,
    storage_path text,
    storage_status text not null default 'local_only'
        check (storage_status in (
            'cloud_available',
            'local_only',
            'pending_upload',
            'uploading',
            'archived_cloud_removed',
            'missing',
            'error'
        )),
    file_size bigint,
    sha256 text,
    mime_type text,
    created_at_hektor timestamptz,
    synced_at timestamptz,
    last_accessed_at timestamptz,
    archive_policy text,
    metadata_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (hektor_annonce_id, source, hektor_document_id),
    unique (storage_bucket, storage_path)
);

create table if not exists public.app_console_job (
    id uuid primary key default gen_random_uuid(),
    job_type text not null
        check (job_type in (
            'sync_console_documents',
            'prepare_document_cloud',
            'upload_document_to_hektor',
            'refresh_console_data',
            'archive_cloud_documents'
        )),
    app_dossier_id bigint,
    hektor_annonce_id text,
    payload_json jsonb not null default '{}'::jsonb,
    status text not null default 'pending'
        check (status in ('pending', 'running', 'done', 'error')),
    priority integer not null default 100,
    requested_by uuid references auth.users(id) on delete set null,
    requested_at timestamptz not null default now(),
    started_at timestamptz,
    finished_at timestamptz,
    worker_id text,
    attempt_count integer not null default 0,
    error_message text,
    result_json jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.app_console_job_log (
    id uuid primary key default gen_random_uuid(),
    job_id uuid references public.app_console_job(id) on delete cascade,
    step text,
    status text,
    message text,
    payload_preview text,
    created_at timestamptz not null default now()
);

create index if not exists idx_app_console_document_dossier
on public.app_console_document (app_dossier_id, storage_status, document_type);

create index if not exists idx_app_console_document_annonce
on public.app_console_document (hektor_annonce_id, storage_status);

create index if not exists idx_app_console_document_storage_status
on public.app_console_document (storage_status, last_accessed_at);

create index if not exists idx_app_console_job_queue
on public.app_console_job (status, priority, requested_at);

create index if not exists idx_app_console_job_dossier
on public.app_console_job (app_dossier_id, hektor_annonce_id, status);

create index if not exists idx_app_console_job_log_job
on public.app_console_job_log (job_id, created_at);

create or replace function public.app_console_current_role()
returns text
language sql
stable
security definer
set search_path = public
as $$
    select p.role::text
    from public.app_user_profile p
    where p.id = auth.uid()
      and p.is_active = true
    limit 1;
$$;

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
            from public.app_dossier_current target
            where (
                    (target_app_dossier_id is not null and target.app_dossier_id = target_app_dossier_id)
                 or (nullif(target_hektor_annonce_id, '') is not null and target.hektor_annonce_id::text = target_hektor_annonce_id)
                )
              and nullif(target.agence_nom, '') is not null
              and exists (
                    select 1
                    from public.app_dossier_current owned
                    where lower(coalesce(owned.negociateur_email, '')) = lower(coalesce(current_email, ''))
                      and owned.agence_nom = target.agence_nom
                )
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

    if current_app_role = 'commercial' and target_job_type in ('prepare_document_cloud', 'upload_document_to_hektor') then
        return public.app_console_can_access_dossier(target_app_dossier_id, target_hektor_annonce_id);
    end if;

    return false;
end;
$$;

create or replace function public.app_console_touch_document(document_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
    update public.app_console_document d
    set last_accessed_at = now(),
        updated_at = now()
    where d.id = document_id
      and public.app_console_can_access_dossier(d.app_dossier_id, d.hektor_annonce_id);

    if not found then
        raise exception 'document_not_found_or_forbidden';
    end if;
end;
$$;

create or replace function public.app_console_fail_own_pending_job(
    target_job_id uuid,
    failure_message text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
    update public.app_console_job j
    set status = 'error',
        finished_at = now(),
        error_message = left(coalesce(failure_message, 'upload_failed'), 2000),
        updated_at = now()
    where j.id = target_job_id
      and j.status = 'pending'
      and j.requested_by = auth.uid();

    if not found then
        raise exception 'job_not_found_or_forbidden';
    end if;
end;
$$;

create or replace function public.app_console_claim_next_job(p_worker_id text default null)
returns setof public.app_console_job
language plpgsql
security definer
set search_path = public
as $$
begin
    return query
    with next_job as (
        select j.id
        from public.app_console_job j
        where j.status = 'pending'
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

alter table public.app_console_document enable row level security;
alter table public.app_console_job enable row level security;
alter table public.app_console_job_log enable row level security;

drop policy if exists "app_console_document_select_scope" on public.app_console_document;
create policy "app_console_document_select_scope"
on public.app_console_document
for select
using (public.app_console_can_access_dossier(app_dossier_id, hektor_annonce_id));

drop policy if exists "app_console_job_select_scope" on public.app_console_job;
create policy "app_console_job_select_scope"
on public.app_console_job
for select
using (
    requested_by = auth.uid()
    or public.app_console_can_request_job(job_type, app_dossier_id, hektor_annonce_id)
);

drop policy if exists "app_console_job_insert_scope" on public.app_console_job;
create policy "app_console_job_insert_scope"
on public.app_console_job
for insert
with check (
    requested_by = auth.uid()
    and status = 'pending'
    and public.app_console_can_request_job(job_type, app_dossier_id, hektor_annonce_id)
);

drop policy if exists "app_console_job_log_select_scope" on public.app_console_job_log;
create policy "app_console_job_log_select_scope"
on public.app_console_job_log
for select
using (
    exists (
        select 1
        from public.app_console_job j
        where j.id = app_console_job_log.job_id
          and (
                j.requested_by = auth.uid()
             or public.app_console_can_request_job(j.job_type, j.app_dossier_id, j.hektor_annonce_id)
          )
    )
);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
    'hektor-console-documents',
    'hektor-console-documents',
    false,
    52428800,
    array[
        'application/pdf',
        'image/jpeg',
        'image/png',
        'image/webp',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain'
    ]
)
on conflict (id) do update
set public = false,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "hektor_console_documents_read_scope" on storage.objects;
create policy "hektor_console_documents_read_scope"
on storage.objects
for select
to authenticated
using (
    bucket_id = 'hektor-console-documents'
    and (
        exists (
            select 1
            from public.app_console_document d
            where d.storage_bucket = bucket_id
              and d.storage_path = name
              and d.storage_status = 'cloud_available'
              and public.app_console_can_access_dossier(d.app_dossier_id, d.hektor_annonce_id)
        )
        or (
            (storage.foldername(name))[1] = 'temp'
            and (storage.foldername(name))[2] = 'uploads'
            and exists (
                select 1
                from public.app_console_job j
                where j.id::text = (storage.foldername(name))[3]
                  and j.requested_by = auth.uid()
            )
        )
    )
);

drop policy if exists "hektor_console_documents_temp_upload" on storage.objects;
create policy "hektor_console_documents_temp_upload"
on storage.objects
for insert
to authenticated
with check (
    bucket_id = 'hektor-console-documents'
    and (storage.foldername(name))[1] = 'temp'
    and (storage.foldername(name))[2] = 'uploads'
    and exists (
        select 1
        from public.app_console_job j
        where j.id::text = (storage.foldername(name))[3]
          and j.job_type = 'upload_document_to_hektor'
          and j.status = 'pending'
          and j.requested_by = auth.uid()
    )
);

revoke all on function public.app_console_claim_next_job(text) from anon, authenticated;
grant execute on function public.app_console_claim_next_job(text) to service_role;

grant execute on function public.app_console_touch_document(uuid) to authenticated;
grant execute on function public.app_console_fail_own_pending_job(uuid, text) to authenticated;
