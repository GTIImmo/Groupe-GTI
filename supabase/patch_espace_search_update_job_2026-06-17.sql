-- Espace client (Étape 2) : fonction jumelle de app_console_create_update_contact_search_job,
-- autorisée par le lien magique (token espace, vérifié côté backend) au lieu du login négociateur.
-- ADDITIVE (ne modifie pas l'existante) et réversible : drop function pour annuler.
-- Réservée à service_role (le backend) : pas appelable par anon/authenticated.

create or replace function public.app_espace_create_search_update_job(
    target_contact_id text, search_payload jsonb, job_priority integer default 16)
returns app_console_job
language plpgsql security definer set search_path to 'public'
as $function$
declare created_job public.app_console_job; clean_contact_id text;
        existing_contact public.app_contact_current%rowtype;
        target_email text; target_user_id text; search_spec jsonb;
begin
    clean_contact_id := nullif(trim(coalesce(target_contact_id, '')), '');
    if clean_contact_id is null or clean_contact_id !~ '^[0-9]+$' then raise exception 'invalid_contact_id' using errcode='22023'; end if;
    if coalesce(jsonb_typeof(search_payload), '') <> 'object' then raise exception 'invalid_search_payload' using errcode='22023'; end if;
    search_spec := case when jsonb_typeof(search_payload->'search') = 'object' then search_payload->'search' else search_payload end;
    if nullif(trim(coalesce(search_spec->>'priceMax', search_spec->>'price_max', search_spec->>'prix_max', '')), '') is null then
        raise exception 'missing_search_price_max' using errcode='22023'; end if;
    select * into existing_contact from public.app_contact_current where hektor_contact_id = clean_contact_id limit 1;
    if existing_contact.hektor_contact_id is null then raise exception 'contact_not_found' using errcode='22023'; end if;
    select r.target_email, r.target_user_id into target_email, target_user_id
    from public.app_console_resolve_contact_hektor_user(existing_contact,
        coalesce(search_payload->>'hektor_user_email', search_payload->>'target_hektor_user_email'),
        coalesce(search_payload->>'hektor_user_id', search_payload->>'target_hektor_user_id')) r;
    -- Pas de gate auth.uid() : l'autorisation vient du lien magique (token espace), validé par le backend.
    insert into public.app_console_job (job_type, payload_json, status, priority, requested_by, requested_at)
    values ('update_hektor_contact_search',
        search_payload || jsonb_build_object('hektor_contact_id', clean_contact_id, 'contact_id', clean_contact_id, 'search', search_spec,
            'hektor_user_email', target_email, 'target_hektor_user_email', target_email,
            'hektor_user_id', target_user_id, 'target_hektor_user_id', target_user_id,
            'contact_negociateur_email', existing_contact.negociateur_email, 'contact_hektor_negociateur_id', existing_contact.hektor_negociateur_id,
            'source', 'espace_client'),
        'pending', coalesce(job_priority, 16), null, now())
    returning * into created_job;
    return created_job;
end; $function$;

revoke all on function public.app_espace_create_search_update_job(text, jsonb, integer) from public, anon, authenticated;
grant execute on function public.app_espace_create_search_update_job(text, jsonb, integer) to service_role;

comment on function public.app_espace_create_search_update_job(text, jsonb, integer)
is 'Jumelle espace client de app_console_create_update_contact_search_job : meme job, autorise par le token espace (backend), source=espace_client. Reserve service_role.';
