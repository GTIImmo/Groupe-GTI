-- Patch additif : modifier + supprimer (archiver) une recherche contact.
-- update_hektor_contact_search / delete_hektor_contact_search.
-- Suite de patch_console_contact_search_actions_2026-06-12.sql.

begin;

-- 1) Contrainte CHECK : ajout des 2 nouveaux types.
alter table public.app_console_job
    drop constraint if exists app_console_job_job_type_check;

alter table public.app_console_job
    add constraint app_console_job_job_type_check
    check (job_type in (
        'sync_console_documents','prepare_document_cloud','upload_document_to_hektor','delete_document_from_hektor',
        'sync_hektor_photos','upload_hektor_photo','prepare_archived_annonce_detail','prepare_historical_annonce_detail',
        'link_hektor_mandant','create_hektor_contact','update_hektor_contact',
        'add_hektor_contact_search','update_hektor_contact_search','delete_hektor_contact_search',
        'delete_hektor_contact','create_hektor_mandant_contact','update_hektor_mandant_contact',
        'update_hektor_annonce_fields','create_hektor_mandat_auto_number','delete_hektor_annonce','archive_hektor_annonce',
        'restore_hektor_annonce','change_hektor_annonce_status','assign_hektor_annonce_negotiator','create_hektor_draft_annonce',
        'matterport_online','matterport_offline','matterport_archive','matterport_reactivate',
        'refresh_console_data','refresh_console_contact_data','archive_cloud_documents'
    ));

-- 2) Autorisation : meme controle d'acces que update_hektor_contact pour toutes les actions recherche.
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

    if current_app_role in ('admin', 'manager') then
        return true;
    end if;
    if current_app_role <> 'commercial' then
        return false;
    end if;
    if target_job_type = 'create_hektor_contact' then
        return public.can_access_negotiator_email(target_negociateur_email);
    end if;
    if target_job_type in (
        'update_hektor_contact', 'add_hektor_contact_search',
        'update_hektor_contact_search', 'delete_hektor_contact_search'
    ) and clean_contact_id is not null then
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

-- 3) Helper interne : resout email + user_id Hektor du negociateur d'un contact existant.
--    (factorise la logique commune aux RPC recherche.)
create or replace function public.app_console_resolve_contact_hektor_user(
    existing_contact public.app_contact_current,
    override_email text default null,
    override_user_id text default null,
    out target_email text,
    out target_user_id text
)
language plpgsql
stable
security definer
set search_path = public
as $$
begin
    target_email := nullif(trim(coalesce(override_email, existing_contact.negociateur_email, '')), '');
    target_user_id := nullif(trim(coalesce(
        override_user_id,
        (
            select d.hektor_user_id
            from public.app_hektor_negotiator_agency_directory d
            where (
                (existing_contact.hektor_negociateur_id is not null and d.hektor_negociateur_id = existing_contact.hektor_negociateur_id)
                or (target_email is not null and lower(coalesce(d.email, '')) = lower(target_email))
            )
            and exists (
                select 1 from public.app_user_directory u
                where u.id_user = d.hektor_user_id and upper(coalesce(u.user_type, '')) = 'NEGO'
            )
            order by case when d.hektor_negociateur_id = existing_contact.hektor_negociateur_id then 0 else 1 end,
                     d.display_name nulls last
            limit 1
        ),
        ''
    )), '');
end;
$$;

-- 4) RPC modifier une recherche.
create or replace function public.app_console_create_update_contact_search_job(
    target_contact_id text,
    search_payload jsonb,
    job_priority integer default 16
)
returns public.app_console_job
language plpgsql
security definer
set search_path = public
as $$
declare
    created_job public.app_console_job;
    clean_contact_id text;
    existing_contact public.app_contact_current%rowtype;
    target_email text;
    target_user_id text;
    search_spec jsonb;
begin
    clean_contact_id := nullif(trim(coalesce(target_contact_id, '')), '');
    if clean_contact_id is null or clean_contact_id !~ '^[0-9]+$' then
        raise exception 'invalid_contact_id' using errcode = '22023';
    end if;
    if coalesce(jsonb_typeof(search_payload), '') <> 'object' then
        raise exception 'invalid_search_payload' using errcode = '22023';
    end if;
    search_spec := case when jsonb_typeof(search_payload->'search') = 'object' then search_payload->'search' else search_payload end;
    if nullif(trim(coalesce(search_spec->>'priceMax', search_spec->>'price_max', search_spec->>'prix_max', '')), '') is null then
        raise exception 'missing_search_price_max' using errcode = '22023';
    end if;

    select * into existing_contact from public.app_contact_current where hektor_contact_id = clean_contact_id limit 1;
    if existing_contact.hektor_contact_id is null then
        raise exception 'contact_not_found' using errcode = '22023';
    end if;

    select r.target_email, r.target_user_id into target_email, target_user_id
    from public.app_console_resolve_contact_hektor_user(
        existing_contact,
        coalesce(search_payload->>'hektor_user_email', search_payload->>'target_hektor_user_email'),
        coalesce(search_payload->>'hektor_user_id', search_payload->>'target_hektor_user_id')
    ) r;

    if not public.app_console_can_request_contact_job('update_hektor_contact_search', clean_contact_id, target_email) then
        raise exception 'forbidden_update_contact_search' using errcode = '42501';
    end if;

    insert into public.app_console_job (job_type, payload_json, status, priority, requested_by, requested_at)
    values (
        'update_hektor_contact_search',
        search_payload || jsonb_build_object(
            'hektor_contact_id', clean_contact_id, 'contact_id', clean_contact_id, 'search', search_spec,
            'hektor_user_email', target_email, 'target_hektor_user_email', target_email,
            'hektor_user_id', target_user_id, 'target_hektor_user_id', target_user_id,
            'contact_negociateur_email', existing_contact.negociateur_email,
            'contact_hektor_negociateur_id', existing_contact.hektor_negociateur_id
        ),
        'pending', coalesce(job_priority, 16), auth.uid(), now()
    )
    returning * into created_job;
    return created_job;
end;
$$;

-- 5) RPC supprimer (archiver) une recherche.
create or replace function public.app_console_create_delete_contact_search_job(
    target_contact_id text,
    search_index integer default null,
    target_critere_id text default null,
    job_priority integer default 14
)
returns public.app_console_job
language plpgsql
security definer
set search_path = public
as $$
declare
    created_job public.app_console_job;
    clean_contact_id text;
    existing_contact public.app_contact_current%rowtype;
    target_email text;
    target_user_id text;
    clean_critere_id text;
begin
    clean_contact_id := nullif(trim(coalesce(target_contact_id, '')), '');
    if clean_contact_id is null or clean_contact_id !~ '^[0-9]+$' then
        raise exception 'invalid_contact_id' using errcode = '22023';
    end if;
    clean_critere_id := nullif(trim(coalesce(target_critere_id, '')), '');
    if search_index is null and (clean_critere_id is null or clean_critere_id !~ '^[0-9]+$') then
        raise exception 'missing_search_target' using errcode = '22023';
    end if;

    select * into existing_contact from public.app_contact_current where hektor_contact_id = clean_contact_id limit 1;
    if existing_contact.hektor_contact_id is null then
        raise exception 'contact_not_found' using errcode = '22023';
    end if;

    select r.target_email, r.target_user_id into target_email, target_user_id
    from public.app_console_resolve_contact_hektor_user(existing_contact) r;

    if not public.app_console_can_request_contact_job('delete_hektor_contact_search', clean_contact_id, target_email) then
        raise exception 'forbidden_delete_contact_search' using errcode = '42501';
    end if;

    insert into public.app_console_job (job_type, payload_json, status, priority, requested_by, requested_at)
    values (
        'delete_hektor_contact_search',
        jsonb_build_object(
            'hektor_contact_id', clean_contact_id, 'contact_id', clean_contact_id,
            'search_index', search_index, 'idCritere', clean_critere_id,
            'hektor_user_email', target_email, 'target_hektor_user_email', target_email,
            'hektor_user_id', target_user_id, 'target_hektor_user_id', target_user_id,
            'contact_negociateur_email', existing_contact.negociateur_email,
            'contact_hektor_negociateur_id', existing_contact.hektor_negociateur_id
        ),
        'pending', coalesce(job_priority, 14), auth.uid(), now()
    )
    returning * into created_job;
    return created_job;
end;
$$;

-- 6) File : worker actions peut reclamer les 2 nouveaux types.
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
    set status = 'error', finished_at = now(), updated_at = now(),
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
                    'create_hektor_draft_annonce','update_hektor_annonce_fields','create_hektor_contact','update_hektor_contact',
                    'add_hektor_contact_search','update_hektor_contact_search','delete_hektor_contact_search',
                    'create_hektor_mandant_contact','update_hektor_mandant_contact','create_hektor_mandat_auto_number','link_hektor_mandant'
                ))
             or (worker_kind = 'documents' and j.job_type in (
                    'sync_console_documents','prepare_document_cloud','upload_document_to_hektor','delete_document_from_hektor',
                    'sync_hektor_photos','upload_hektor_photo','prepare_archived_annonce_detail','prepare_historical_annonce_detail'
                ))
             or (worker_kind = 'admin' and j.job_type in (
                    'delete_hektor_annonce','delete_hektor_contact','archive_hektor_annonce','restore_hektor_annonce',
                    'change_hektor_annonce_status','assign_hektor_annonce_negotiator'
                ))
             or (worker_kind = 'matterport' and j.job_type in (
                    'matterport_online','matterport_offline','matterport_archive','matterport_reactivate'
                ))
             or (worker_kind = 'sync_light' and j.job_type in ('refresh_console_data','refresh_console_contact_data'))
             or (worker_kind = 'sync_full' and j.job_type in ('archive_cloud_documents'))
             or (worker_kind = 'sync' and j.job_type in ('refresh_console_data','refresh_console_contact_data','archive_cloud_documents'))
          )
          and (
                j.job_type not in ('upload_document_to_hektor', 'upload_hektor_photo')
             or exists (
                    select 1 from storage.objects o
                    where o.bucket_id = 'hektor-console-documents' and o.name = j.payload_json->>'temp_storage_path'
                )
          )
          and (
                nullif(j.hektor_annonce_id, '') is null
             or not exists (
                    select 1 from public.app_console_job running_job
                    where running_job.status = 'running' and running_job.hektor_annonce_id = j.hektor_annonce_id and running_job.id <> j.id
                )
          )
          and (
                nullif(coalesce(j.payload_json->>'hektor_contact_id', j.payload_json->>'contact_id'), '') is null
             or not exists (
                    select 1 from public.app_console_job running_contact_job
                    where running_contact_job.status = 'running' and running_contact_job.id <> j.id
                      and nullif(coalesce(running_contact_job.payload_json->>'hektor_contact_id', running_contact_job.payload_json->>'contact_id'), '') =
                          nullif(coalesce(j.payload_json->>'hektor_contact_id', j.payload_json->>'contact_id'), '')
                )
          )
        order by j.priority asc, j.requested_at asc
        for update skip locked
        limit 1
    )
    update public.app_console_job j
    set status = 'running', started_at = now(), worker_id = p_worker_id, attempt_count = j.attempt_count + 1, updated_at = now()
    from next_job
    where j.id = next_job.id
    returning j.*;
end;
$function$;

grant execute on function public.app_console_can_request_contact_job(text, text, text) to authenticated;
grant execute on function public.app_console_create_update_contact_search_job(text, jsonb, integer) to authenticated;
grant execute on function public.app_console_create_delete_contact_search_job(text, integer, text, integer) to authenticated;
grant execute on function public.app_console_claim_next_job(text, text) to service_role;

commit;
