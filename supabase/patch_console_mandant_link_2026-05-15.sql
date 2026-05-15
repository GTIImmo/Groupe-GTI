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
        'delete_hektor_annonce',
        'create_hektor_draft_annonce',
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
           'link_hektor_mandant'
       ) then
        return public.app_console_can_access_dossier(target_app_dossier_id, target_hektor_annonce_id);
    end if;

    return false;
end;
$$;

grant execute on function public.app_console_can_request_job(text, bigint, text) to authenticated;

commit;
