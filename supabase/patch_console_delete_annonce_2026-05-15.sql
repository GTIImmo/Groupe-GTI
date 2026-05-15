begin;

create table if not exists public.app_console_deleted_annonce_log (
    id uuid primary key default gen_random_uuid(),
    job_id uuid references public.app_console_job(id) on delete set null,
    app_dossier_id bigint,
    hektor_annonce_id text not null,
    requested_by uuid references auth.users(id) on delete set null,
    reason text,
    before_json jsonb,
    result_json jsonb,
    created_at timestamptz not null default now()
);

alter table public.app_console_deleted_annonce_log enable row level security;

drop policy if exists "app_console_deleted_annonce_log_admin_select" on public.app_console_deleted_annonce_log;
create policy "app_console_deleted_annonce_log_admin_select"
on public.app_console_deleted_annonce_log
for select
to authenticated
using (public.app_console_current_role() = 'admin');

drop policy if exists "app_console_deleted_annonce_log_service_insert" on public.app_console_deleted_annonce_log;
create policy "app_console_deleted_annonce_log_service_insert"
on public.app_console_deleted_annonce_log
for insert
to service_role
with check (true);

alter table public.app_console_job
    drop constraint if exists app_console_job_job_type_check;

alter table public.app_console_job
    add constraint app_console_job_job_type_check
    check (job_type in (
        'sync_console_documents',
        'prepare_document_cloud',
        'upload_document_to_hektor',
        'delete_document_from_hektor',
        'delete_hektor_annonce',
        'create_hektor_draft_annonce',
        'refresh_console_data',
        'archive_cloud_documents'
    ));

create or replace function public.app_console_create_delete_annonce_job(
    target_app_dossier_id bigint,
    target_hektor_annonce_id text,
    delete_reason text,
    confirm_text text,
    delete_priority integer default 5
)
returns public.app_console_job
language plpgsql
security definer
set search_path = public
as $$
declare
    requester_role text;
    requester_active boolean;
    expected_confirm text;
    created_job public.app_console_job;
begin
    select role, is_active
    into requester_role, requester_active
    from public.app_user_profile
    where id = auth.uid();

    if coalesce(requester_active, false) is not true or requester_role <> 'admin' then
        raise exception 'forbidden_admin_only' using errcode = '42501';
    end if;

    if nullif(trim(coalesce(target_hektor_annonce_id, '')), '') is null then
        raise exception 'missing_hektor_annonce_id' using errcode = '22023';
    end if;

    expected_confirm := 'SUPPRIMER ' || trim(target_hektor_annonce_id);
    if coalesce(confirm_text, '') <> expected_confirm then
        raise exception 'invalid_delete_confirmation' using errcode = '22023';
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
        'delete_hektor_annonce',
        target_app_dossier_id,
        trim(target_hektor_annonce_id),
        jsonb_build_object(
            'hektor_annonce_id', trim(target_hektor_annonce_id),
            'app_dossier_id', target_app_dossier_id,
            'reason', nullif(trim(coalesce(delete_reason, '')), ''),
            'confirm_text', confirm_text,
            'delete_scope', 'hektor_supabase_local'
        ),
        'pending',
        coalesce(delete_priority, 5),
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
       and target_job_type in ('prepare_document_cloud', 'upload_document_to_hektor', 'delete_document_from_hektor') then
        return public.app_console_can_access_dossier(target_app_dossier_id, target_hektor_annonce_id);
    end if;

    return false;
end;
$$;

grant execute on function public.app_console_create_delete_annonce_job(bigint, text, text, text, integer) to authenticated;
grant execute on function public.app_console_can_request_job(text, bigint, text) to authenticated;

commit;
