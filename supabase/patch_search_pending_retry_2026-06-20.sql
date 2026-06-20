-- =====================================================================
-- Fix « stuck-pending » (garde-fou n°6) — 2026-06-20
-- ---------------------------------------------------------------------
-- Problème : app_search_enqueue_due_pushes() pose push_job_id quand elle
-- crée le job de push débouncé. Si ce job ÉCHOUE (status='error') ou est
-- PERDU (worker mort / job introuvable), le pending garde push_job_id et
-- n'est JAMAIS repris (le WHERE exige push_job_id IS NULL). L'affinage du
-- négo/client n'arrive donc jamais dans Hektor, en silence.
--
-- Correctif (additif, idempotent) :
--   1) compteur push_attempts (borne les retries).
--   2) sweep réécrit : nettoie les jobs 'done' orphelins, ré-arme avec
--      backoff les jobs échoués/perdus (jusqu'à 5 fois), puis au plafond
--      marque conflict=true pour surfacer (et arrêter de boucler).
--   3) les 2 RPC d'édition réinitialisent push_attempts sur ré-édition
--      (une nouvelle saisie = nouveau cycle de retry propre).
-- La boucle d'enfilage normale est INCHANGÉE.
-- =====================================================================

-- 1) Compteur de tentatives de push (défaut 0).
alter table public.app_search_pending
  add column if not exists push_attempts integer not null default 0;

-- 2) Sweep avec ré-armement borné.
create or replace function public.app_search_enqueue_due_pushes()
 returns integer
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare r record; ec public.app_contact_current%rowtype; te text; tu text; n int := 0; jid uuid;
        max_attempts int := 5;
begin
  -- (0a) Job DÉJÀ réussi mais pending encore là (clearSearchPending best-effort a échoué)
  --      -> le push a eu lieu, le pending est obsolète : on le supprime.
  delete from public.app_search_pending p
  using public.app_console_job j
  where p.push_job_id = j.id and j.status = 'done';

  -- (0b) Job de push ÉCHOUÉ / PERDU / INTROUVABLE -> ré-armer avec backoff (sous le plafond).
  --      Condition "mauvais job" : introuvable, OU status='error', OU non terminé depuis >30 min.
  update public.app_search_pending p
  set push_job_id   = null,
      push_after    = now() + make_interval(mins => 5 * (p.push_attempts + 1)),
      push_attempts = p.push_attempts + 1,
      updated_at    = now()
  where p.push_job_id is not null and p.conflict = false and p.push_attempts < max_attempts
    and (
      not exists (select 1 from public.app_console_job j where j.id = p.push_job_id)
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id and j.status = 'error')
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id
                 and j.finished_at is null and j.requested_at < now() - interval '30 minutes')
    );

  -- (0c) Plafond de tentatives atteint -> on arrête de réessayer et on surface (conflict=true).
  --      Une nouvelle édition (RPC) remettra conflict=false + push_attempts=0 -> cycle neuf.
  update public.app_search_pending p
  set conflict = true, updated_at = now()
  where p.push_job_id is not null and p.conflict = false and p.push_attempts >= max_attempts
    and (
      not exists (select 1 from public.app_console_job j where j.id = p.push_job_id)
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id and j.status = 'error')
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id
                 and j.finished_at is null and j.requested_at < now() - interval '30 minutes')
    );

  -- (1) Boucle d'enfilage normale — INCHANGÉE.
  for r in select * from public.app_search_pending
           where push_after <= now() and push_job_id is null and conflict = false and push_search is not null
           order by push_after limit 100 loop
    select * into ec from public.app_contact_current where hektor_contact_id = r.hektor_contact_id limit 1;
    if ec.hektor_contact_id is null then continue; end if;
    select target_email, target_user_id into te, tu from public.app_console_resolve_contact_hektor_user(ec, null, null);
    insert into public.app_console_job(job_type, payload_json, status, priority, requested_at)
    values ('update_hektor_contact_search',
      jsonb_build_object('hektor_contact_id', r.hektor_contact_id, 'contact_id', r.hektor_contact_id,
        'search', r.push_search, 'search_index', r.search_index, 'from_pending', true, 'base_snapshot', r.base_snapshot,
        'hektor_user_email', te, 'target_hektor_user_email', te, 'hektor_user_id', tu, 'target_hektor_user_id', tu,
        'contact_negociateur_email', ec.negociateur_email, 'contact_hektor_negociateur_id', ec.hektor_negociateur_id,
        'source', coalesce(r.source,'nego_app')),
      'pending', 70, now())
    returning id into jid;
    update public.app_search_pending set push_job_id = jid, updated_at = now()
      where hektor_contact_id = r.hektor_contact_id and search_index = r.search_index;
    n := n + 1;
  end loop;
  return n;
end; $function$;

-- 3) RPC d'édition (négo) : réinitialiser push_attempts sur ré-édition.
--    (corps identique à l'existant, seul ajout : push_attempts=0 dans le ON CONFLICT)
create or replace function public.app_edit_search_optimistic(target_contact_id text, search_payload jsonb, debounce_seconds integer default 600)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare clean_id text; existing_contact public.app_contact_current%rowtype;
        target_email text; target_user_id text; v_index int; v_search jsonb;
        cur public.app_contact_search_current%rowtype; v_types jsonb; v_villes jsonb; v_base jsonb;
begin
  clean_id := nullif(trim(coalesce(target_contact_id,'')),'');
  if clean_id is null or clean_id !~ '^[0-9]+$' then raise exception 'invalid_contact_id' using errcode='22023'; end if;
  v_search := case when jsonb_typeof(search_payload->'search')='object' then search_payload->'search' else search_payload end;
  v_index := coalesce((search_payload->>'search_index')::int,(search_payload->>'searchIndex')::int,0);
  if nullif(trim(coalesce(v_search->>'priceMax',v_search->>'prix_max','')),'') is null then raise exception 'missing_search_price_max' using errcode='22023'; end if;

  select * into existing_contact from public.app_contact_current where hektor_contact_id=clean_id limit 1;
  if existing_contact.hektor_contact_id is null then raise exception 'contact_not_found' using errcode='22023'; end if;
  select r.target_email, r.target_user_id into target_email, target_user_id
    from public.app_console_resolve_contact_hektor_user(existing_contact,
      coalesce(search_payload->>'hektor_user_email',search_payload->>'target_hektor_user_email'),
      coalesce(search_payload->>'hektor_user_id',search_payload->>'target_hektor_user_id')) r;
  if not public.app_console_can_request_contact_job('update_hektor_contact_search', clean_id, target_email) then
    raise exception 'forbidden_update_contact_search' using errcode='42501'; end if;

  select * into cur from public.app_contact_search_current where hektor_contact_id=clean_id and search_index=v_index limit 1;
  if cur.contact_search_key is null then raise exception 'search_not_found' using errcode='22023'; end if;

  v_types := coalesce((select jsonb_object_agg(t,t) from jsonb_array_elements_text(v_search->'propertyTypeIds') t), cur.types_json);
  v_villes := coalesce((select jsonb_agg(trim(coalesce(l->>'city','')||' '||coalesce(l->>'postalCode','')))
                        from jsonb_array_elements(v_search->'localities') l
                        where coalesce(l->>'city','')<>'' or coalesce(l->>'postalCode','')<>''), cur.villes_json);

  if exists (select 1 from public.app_search_pending p where p.hektor_contact_id=clean_id and p.search_index=v_index)
    then select base_snapshot into v_base from public.app_search_pending where hektor_contact_id=clean_id and search_index=v_index;
    else v_base := jsonb_build_object('offre',cur.offre,'types_json',cur.types_json,'villes_json',cur.villes_json,
           'surface_terrain_min',cur.surface_terrain_min,'criteres_json',cur.criteres_json,'prix_min',cur.prix_min,
           'prix_max',cur.prix_max,'surface_min',cur.surface_min,'pieces_min',cur.pieces_min,'chambre_min',cur.chambre_min);
  end if;

  update public.app_contact_search_current set
    offre=coalesce(nullif(v_search->>'offerCode',''),offre), types_json=v_types, villes_json=v_villes,
    criteres_json=public.app_search_criteres_from_input(v_search),
    prix_min=coalesce(nullif(v_search->>'priceMin',''),prix_min), prix_max=nullif(v_search->>'priceMax',''),
    surface_min=nullif(v_search->>'surfaceMin',''), pieces_min=nullif(v_search->>'roomsMin',''),
    chambre_min=nullif(v_search->>'bedroomsMin',''), surface_terrain_min=nullif(v_search->>'landSurfaceMin',''),
    refreshed_at=now()
  where hektor_contact_id=clean_id and search_index=v_index;

  perform public.app_refresh_rapprochements_for_search(cur.contact_search_key);

  insert into public.app_search_pending(hektor_contact_id,search_index,base_snapshot,push_search,push_after,source,dirty_by)
  values (clean_id,v_index,v_base, v_search, now()+make_interval(secs=>greatest(debounce_seconds,30)),'nego_app',auth.uid()::text)
  on conflict (hektor_contact_id,search_index) do update set
    push_search=excluded.push_search, push_after=now()+make_interval(secs=>greatest(debounce_seconds,30)),
    push_job_id=null, conflict=false, push_attempts=0, updated_at=now();

  return jsonb_build_object('ok',true,'contact_id',clean_id,'search_index',v_index);
end; $function$;

-- 3bis) RPC d'édition (espace client) : idem.
create or replace function public.app_espace_edit_search_optimistic(target_contact_id text, search_payload jsonb, debounce_seconds integer default 600)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare clean_id text; cur public.app_contact_search_current%rowtype;
        v_index int; v_search jsonb; v_types jsonb; v_villes jsonb; v_base jsonb;
begin
  clean_id := nullif(trim(coalesce(target_contact_id,'')),'');
  if clean_id is null or clean_id !~ '^[0-9]+$' then raise exception 'invalid_contact_id' using errcode='22023'; end if;
  v_search := case when jsonb_typeof(search_payload->'search')='object' then search_payload->'search' else search_payload end;
  v_index := coalesce((search_payload->>'search_index')::int,(search_payload->>'searchIndex')::int,0);
  if nullif(trim(coalesce(v_search->>'priceMax',v_search->>'prix_max','')),'') is null then raise exception 'missing_search_price_max' using errcode='22023'; end if;

  select * into cur from public.app_contact_search_current where hektor_contact_id=clean_id and search_index=v_index limit 1;
  if cur.contact_search_key is null then raise exception 'search_not_found' using errcode='22023'; end if;

  v_types := coalesce((select jsonb_object_agg(t,t) from jsonb_array_elements_text(v_search->'propertyTypeIds') t), cur.types_json);
  v_villes := coalesce((select jsonb_agg(trim(coalesce(l->>'city','')||' '||coalesce(l->>'postalCode','')))
                        from jsonb_array_elements(v_search->'localities') l
                        where coalesce(l->>'city','')<>'' or coalesce(l->>'postalCode','')<>''), cur.villes_json);

  if exists (select 1 from public.app_search_pending p where p.hektor_contact_id=clean_id and p.search_index=v_index)
    then select base_snapshot into v_base from public.app_search_pending where hektor_contact_id=clean_id and search_index=v_index;
    else v_base := jsonb_build_object('offre',cur.offre,'types_json',cur.types_json,'villes_json',cur.villes_json,
           'surface_terrain_min',cur.surface_terrain_min,'criteres_json',cur.criteres_json,'prix_min',cur.prix_min,
           'prix_max',cur.prix_max,'surface_min',cur.surface_min,'pieces_min',cur.pieces_min,'chambre_min',cur.chambre_min);
  end if;

  update public.app_contact_search_current set
    offre=coalesce(nullif(v_search->>'offerCode',''),offre), types_json=v_types, villes_json=v_villes,
    criteres_json=public.app_search_criteres_from_input(v_search),
    prix_min=coalesce(nullif(v_search->>'priceMin',''),prix_min), prix_max=nullif(v_search->>'priceMax',''),
    surface_min=nullif(v_search->>'surfaceMin',''), pieces_min=nullif(v_search->>'roomsMin',''),
    chambre_min=nullif(v_search->>'bedroomsMin',''), surface_terrain_min=nullif(v_search->>'landSurfaceMin',''),
    refreshed_at=now()
  where hektor_contact_id=clean_id and search_index=v_index;

  perform public.app_refresh_rapprochements_for_search(cur.contact_search_key);

  insert into public.app_search_pending(hektor_contact_id,search_index,base_snapshot,push_search,push_after,source,dirty_by)
  values (clean_id,v_index,v_base, v_search, now()+make_interval(secs=>greatest(debounce_seconds,30)),'espace_client',
          nullif(search_payload->>'dirty_by',''))
  on conflict (hektor_contact_id,search_index) do update set
    push_search=excluded.push_search, push_after=now()+make_interval(secs=>greatest(debounce_seconds,30)),
    push_job_id=null, conflict=false, push_attempts=0, updated_at=now();

  return jsonb_build_object('ok',true,'contact_id',clean_id,'search_index',v_index);
end; $function$;
