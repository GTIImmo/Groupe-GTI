begin;

create table if not exists public.app_console_deleted_contact_log (
    id uuid primary key default gen_random_uuid(),
    job_id uuid references public.app_console_job(id) on delete set null,
    hektor_contact_id text not null,
    requested_by uuid references auth.users(id) on delete set null,
    reason text,
    before_json jsonb,
    result_json jsonb,
    created_at timestamptz not null default now()
);

alter table public.app_console_deleted_contact_log enable row level security;

drop policy if exists "app_console_deleted_contact_log_admin_select" on public.app_console_deleted_contact_log;
create policy "app_console_deleted_contact_log_admin_select"
on public.app_console_deleted_contact_log
for select
to authenticated
using (public.app_console_current_role() = 'admin');

drop policy if exists "app_console_deleted_contact_log_service_insert" on public.app_console_deleted_contact_log;
create policy "app_console_deleted_contact_log_service_insert"
on public.app_console_deleted_contact_log
for insert
to service_role
with check (true);

grant select on public.app_console_deleted_contact_log to authenticated;
grant all on public.app_console_deleted_contact_log to service_role;

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
        'prepare_archived_annonce_detail',
        'prepare_historical_annonce_detail',
        'link_hektor_mandant',
        'create_hektor_contact',
        'update_hektor_contact',
        'delete_hektor_contact',
        'create_hektor_mandant_contact',
        'update_hektor_mandant_contact',
        'update_hektor_annonce_fields',
        'create_hektor_mandat_auto_number',
        'delete_hektor_annonce',
        'archive_hektor_annonce',
        'restore_hektor_annonce',
        'change_hektor_annonce_status',
        'assign_hektor_annonce_negotiator',
        'create_hektor_draft_annonce',
        'matterport_online',
        'matterport_offline',
        'matterport_archive',
        'matterport_reactivate',
        'refresh_console_data',
        'refresh_console_contact_data',
        'archive_cloud_documents'
    ));

drop index if exists public.idx_app_console_job_contact_target;
create index idx_app_console_job_contact_target
on public.app_console_job (
    (coalesce(payload_json->>'hektor_contact_id', payload_json->>'contact_id')),
    status,
    requested_at
)
where job_type in ('create_hektor_contact', 'update_hektor_contact', 'delete_hektor_contact', 'refresh_console_contact_data');

create or replace function public.app_console_can_request_contact_job(
    target_job_type text,
    target_hektor_contact_id text default null,
    target_negociateur_email text default null
)
returns boolean
language plpgsql
stable
security definer
set search_path = public
as $$
declare
    current_app_role text;
    clean_contact_id text;
begin
    current_app_role := public.app_console_current_role();
    clean_contact_id := nullif(trim(coalesce(target_hektor_contact_id, '')), '');

    if target_job_type = 'delete_hektor_contact' then
        return current_app_role = 'admin';
    end if;

    if current_app_role in ('admin', 'manager') then
        return true;
    end if;

    if current_app_role <> 'commercial' then
        return false;
    end if;

    if target_job_type = 'create_hektor_contact' then
        return public.can_access_negotiator_email(target_negociateur_email);
    end if;

    if target_job_type = 'update_hektor_contact' and clean_contact_id is not null then
        return exists (
            select 1
            from public.app_contact_current c
            where c.hektor_contact_id = clean_contact_id
              and (
                    public.can_access_negotiator_email(c.negociateur_email)
                 or exists (
                        select 1
                        from public.app_contact_relation_current r
                        where r.hektor_contact_id = c.hektor_contact_id
                          and r.app_dossier_id is not null
                          and public.can_access_current_dossier(r.app_dossier_id)
                    )
              )
        );
    end if;

    return false;
end;
$$;

create or replace function public.app_console_create_delete_contact_job(
    target_contact_id text,
    delete_reason text default null,
    confirm_text text default null,
    job_priority integer default 6
)
returns public.app_console_job
language plpgsql
security definer
set search_path = public
as $$
declare
    created_job public.app_console_job;
    clean_contact_id text;
    expected_confirm text;
    before_contact jsonb;
begin
    clean_contact_id := nullif(trim(coalesce(target_contact_id, '')), '');

    if clean_contact_id is null or clean_contact_id !~ '^[0-9]+$' then
        raise exception 'invalid_contact_id' using errcode = '22023';
    end if;

    if not public.app_console_can_request_contact_job('delete_hektor_contact', clean_contact_id, null) then
        raise exception 'forbidden_delete_contact' using errcode = '42501';
    end if;

    expected_confirm := 'SUPPRIMER CONTACT ' || clean_contact_id;
    if coalesce(confirm_text, '') <> expected_confirm then
        raise exception 'invalid_delete_confirmation' using errcode = '22023';
    end if;

    select to_jsonb(c)
    into before_contact
    from public.app_contact_current c
    where c.hektor_contact_id = clean_contact_id;

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
        'delete_hektor_contact',
        null,
        null,
        jsonb_build_object(
            'hektor_contact_id', clean_contact_id,
            'contact_id', clean_contact_id,
            'reason', nullif(trim(coalesce(delete_reason, '')), ''),
            'confirm_text', confirm_text,
            'delete_scope', 'hektor_supabase_local',
            'before_contact', before_contact
        ),
        'pending',
        coalesce(job_priority, 6),
        auth.uid(),
        now()
    )
    returning * into created_job;

    return created_job;
end;
$$;

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
    is_current_worker boolean := coalesce(p_worker_id, '') like '%:scheduled:v9'
        or coalesce(p_worker_id, '') like '%:service:v9';
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
                    'create_hektor_contact',
                    'update_hektor_contact',
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
                    'delete_hektor_contact',
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
                    'refresh_console_data',
                    'refresh_console_contact_data'
                ))
             or (worker_kind = 'sync_full' and j.job_type in (
                    'archive_cloud_documents'
                ))
             or (worker_kind = 'sync' and j.job_type in (
                    'refresh_console_data',
                    'refresh_console_contact_data',
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
          and (
                nullif(coalesce(j.payload_json->>'hektor_contact_id', j.payload_json->>'contact_id'), '') is null
             or not exists (
                    select 1
                    from public.app_console_job running_contact_job
                    where running_contact_job.status = 'running'
                      and running_contact_job.id <> j.id
                      and nullif(coalesce(running_contact_job.payload_json->>'hektor_contact_id', running_contact_job.payload_json->>'contact_id'), '') =
                          nullif(coalesce(j.payload_json->>'hektor_contact_id', j.payload_json->>'contact_id'), '')
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

grant execute on function public.app_console_can_request_contact_job(text, text, text) to authenticated;
grant execute on function public.app_console_create_delete_contact_job(text, text, text, integer) to authenticated;
grant execute on function public.app_console_claim_next_job(text, text) to service_role;

commit;
