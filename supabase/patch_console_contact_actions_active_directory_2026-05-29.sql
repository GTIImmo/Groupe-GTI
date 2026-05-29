begin;

create or replace function public.app_console_create_update_contact_job(
    target_contact_id text,
    contact_payload jsonb,
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
begin
    clean_contact_id := nullif(trim(coalesce(target_contact_id, '')), '');

    if clean_contact_id is null or clean_contact_id !~ '^[0-9]+$' then
        raise exception 'invalid_contact_id' using errcode = '22023';
    end if;

    if coalesce(jsonb_typeof(contact_payload), '') <> 'object' then
        raise exception 'invalid_contact_payload' using errcode = '22023';
    end if;

    if nullif(trim(coalesce(contact_payload->>'last_name', contact_payload->>'nom', contact_payload->>'name', '')), '') is null then
        raise exception 'missing_contact_name' using errcode = '22023';
    end if;

    select *
    into existing_contact
    from public.app_contact_current
    where hektor_contact_id = clean_contact_id
    limit 1;

    if existing_contact.hektor_contact_id is null then
        raise exception 'contact_not_found' using errcode = '22023';
    end if;

    target_email := nullif(trim(coalesce(
        contact_payload->>'hektor_user_email',
        contact_payload->>'negociateur_email',
        contact_payload->>'target_hektor_user_email',
        existing_contact.negociateur_email,
        ''
    )), '');

    target_user_id := nullif(trim(coalesce(
        contact_payload->>'hektor_user_id',
        contact_payload->>'hektor_id_user',
        contact_payload->>'target_hektor_user_id',
        (
            select d.hektor_user_id
            from public.app_hektor_negotiator_agency_directory d
            where (
                (
                    existing_contact.hektor_negociateur_id is not null
                and d.hektor_negociateur_id = existing_contact.hektor_negociateur_id
                )
                or (
                    target_email is not null
                and lower(coalesce(d.email, '')) = lower(target_email)
                )
            )
              and exists (
                    select 1
                    from public.app_user_directory u
                    where u.id_user = d.hektor_user_id
                      and upper(coalesce(u.user_type, '')) = 'NEGO'
              )
            order by
                case when d.hektor_negociateur_id = existing_contact.hektor_negociateur_id then 0 else 1 end,
                d.display_name nulls last
            limit 1
        ),
        ''
    )), '');

    if target_email is null and target_user_id is null then
        raise exception 'missing_contact_hektor_context' using errcode = '22023';
    end if;

    if not public.app_console_can_request_contact_job('update_hektor_contact', clean_contact_id, target_email) then
        raise exception 'forbidden_update_contact' using errcode = '42501';
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
        'update_hektor_contact',
        null,
        null,
        contact_payload || jsonb_build_object(
            'hektor_contact_id', clean_contact_id,
            'contact_id', clean_contact_id,
            'hektor_user_email', target_email,
            'target_hektor_user_email', target_email,
            'hektor_user_id', target_user_id,
            'target_hektor_user_id', target_user_id,
            'contact_negociateur_email', existing_contact.negociateur_email,
            'contact_hektor_negociateur_id', existing_contact.hektor_negociateur_id
        ),
        'pending',
        coalesce(job_priority, 16),
        auth.uid(),
        now()
    )
    returning * into created_job;

    return created_job;
end;
$$;

grant execute on function public.app_console_create_update_contact_job(text, jsonb, integer) to authenticated;

commit;
