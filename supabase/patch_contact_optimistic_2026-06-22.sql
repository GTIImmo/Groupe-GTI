-- =====================================================================
-- Édition CONTACT optimiste — MIROIR STRICT du stack annonce :
--   app_annonce_pending / app_edit_annonce_optimistic /
--   app_annonce_enqueue_due_pushes  (déclinés pour le contact).
-- Date 2026-06-22. Additif : aucun objet existant modifié.
-- Clés push canoniques = celles lues par normalizeHektorContactPayload
-- (worker) : last_name, first_name, civility, email, phone,
-- phone_secondary, address, city, postal_code.
-- Anti-écrasement via base_snapshot._date_maj (= app_contact_current.date_maj).
-- =====================================================================

-- ---- 1) Table pending (miroir app_annonce_pending) ----
create table if not exists public.app_contact_pending (
  hektor_contact_id text primary key,
  base_snapshot   jsonb       not null default '{}'::jsonb,
  push_fields     jsonb,
  dirty_at        timestamptz not null default now(),
  push_after      timestamptz not null default now(),
  source          text,
  dirty_by        text,
  push_job_id     uuid,
  conflict        boolean     not null default false,
  push_attempts   integer     not null default 0,
  updated_at      timestamptz not null default now()
);
alter table public.app_contact_pending enable row level security;

-- ---- 2) RPC édition optimiste (miroir app_edit_annonce_optimistic) ----
create or replace function public.app_edit_contact_optimistic(
  target_contact_id text, edit_fields jsonb, debounce_seconds integer default 600)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $function$
declare
  c app_contact_current%rowtype;
  v_base jsonb := '{}'::jsonb;
  ef jsonb := '{}'::jsonb;
  -- variantes entrantes -> clé canonique (lue par le worker)
  alias_map jsonb := '{"nom":"last_name","name":"last_name","prenom":"first_name",
                       "civilite":"civility","telephone":"phone","mobile":"phone",
                       "telephone2":"phone_secondary","phoneSecondary":"phone_secondary",
                       "adresse":"address","ville":"city","code_postal":"postal_code"}'::jsonb;
  -- clé canonique -> colonne app_contact_current (affichage optimiste)
  col_map jsonb := '{"last_name":"nom","first_name":"prenom","civility":"civilite",
                     "email":"email","phone":"phone_primary","phone_secondary":"phone_secondary",
                     "city":"ville","postal_code":"code_postal"}'::jsonb;
  k text;
begin
  select * into c from app_contact_current where hektor_contact_id = target_contact_id;
  if not found then raise exception 'contact_not_found' using errcode='22023'; end if;
  if not public.app_console_can_request_contact_job('update_hektor_contact', target_contact_id, c.negociateur_email) then
    raise exception 'forbidden_update_contact' using errcode='42501'; end if;
  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;

  -- normalisation des clés entrantes vers les clés canoniques
  for k in select jsonb_object_keys(edit_fields) loop
    ef := ef || jsonb_build_object(coalesce(alias_map->>k, k), edit_fields->>k);
  end loop;

  -- base_snapshot : photo pré-édition (figée si un pending existe déjà)
  if exists (select 1 from app_contact_pending p where p.hektor_contact_id = target_contact_id) then
    select base_snapshot into v_base from app_contact_pending where hektor_contact_id = target_contact_id;
  else
    for k in select jsonb_object_keys(ef) loop
      if col_map ? k then v_base := v_base || jsonb_build_object(k, to_jsonb(c) ->> (col_map->>k)); end if;
    end loop;
    v_base := v_base || jsonb_build_object('_date_maj', c.date_maj);
  end if;

  -- écriture optimiste des colonnes mappées (champ présent = appliqué, même vide ;
  -- champ absent = inchangé). date_maj NON touché (= référence anti-écrasement).
  update app_contact_current set
    nom             = case when ef ? 'last_name'       then ef->>'last_name'       else nom end,
    prenom          = case when ef ? 'first_name'      then ef->>'first_name'      else prenom end,
    civilite        = case when ef ? 'civility'        then ef->>'civility'        else civilite end,
    email           = case when ef ? 'email'           then ef->>'email'           else email end,
    phone_primary   = case when ef ? 'phone'           then ef->>'phone'           else phone_primary end,
    phone_secondary = case when ef ? 'phone_secondary' then ef->>'phone_secondary' else phone_secondary end,
    ville           = case when ef ? 'city'            then ef->>'city'            else ville end,
    code_postal     = case when ef ? 'postal_code'     then ef->>'postal_code'     else code_postal end
  where hektor_contact_id = target_contact_id;

  -- pending : push_fields = champs canoniques (accumulés si ré-édition)
  insert into app_contact_pending(hektor_contact_id, base_snapshot, push_fields, push_after, source, dirty_by)
  values (target_contact_id, v_base, ef,
          now() + make_interval(secs => greatest(debounce_seconds,30)), 'nego_app', auth.uid()::text)
  on conflict (hektor_contact_id) do update set
    push_fields = (coalesce(app_contact_pending.push_fields,'{}'::jsonb) || excluded.push_fields),
    push_after  = now() + make_interval(secs => greatest(debounce_seconds,30)),
    push_job_id = null, conflict = false, push_attempts = 0, updated_at = now();

  return jsonb_build_object('ok', true, 'hektor_contact_id', target_contact_id,
                            'fields_count', (select count(*) from jsonb_object_keys(ef)));
end $function$;

-- ---- 3) Sweep (miroir app_annonce_enqueue_due_pushes) ----
create or replace function public.app_contact_enqueue_due_pushes()
 returns integer language plpgsql security definer set search_path to 'public'
as $function$
declare r record; ec public.app_contact_current%rowtype; te text; tu text;
        n int := 0; jid uuid; max_attempts int := 5;
begin
  delete from public.app_contact_pending p
  using public.app_console_job j
  where p.push_job_id = j.id and j.status = 'done';

  delete from public.app_contact_pending
  where conflict = true and updated_at < now() - interval '24 hours';

  update public.app_contact_pending p
  set push_job_id = null,
      push_after = now() + make_interval(mins => 5 * (p.push_attempts + 1)),
      push_attempts = p.push_attempts + 1,
      updated_at = now()
  where p.push_job_id is not null and p.conflict = false and p.push_attempts < max_attempts
    and (
      not exists (select 1 from public.app_console_job j where j.id = p.push_job_id)
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id and j.status = 'error')
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id
                 and j.finished_at is null and j.requested_at < now() - interval '30 minutes')
    );

  update public.app_contact_pending p
  set conflict = true, updated_at = now()
  where p.push_job_id is not null and p.conflict = false and p.push_attempts >= max_attempts
    and (
      not exists (select 1 from public.app_console_job j where j.id = p.push_job_id)
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id and j.status = 'error')
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id
                 and j.finished_at is null and j.requested_at < now() - interval '30 minutes')
    );

  for r in select * from public.app_contact_pending
           where push_after <= now() and push_job_id is null and conflict = false and push_fields is not null
           order by push_after limit 100 loop
    -- Résolution du négo cible (miroir app_search_enqueue_due_pushes /
    -- app_console_create_update_contact_job) : le job from_pending doit porter le
    -- MÊME contexte négo que le job direct éprouvé.
    select * into ec from public.app_contact_current where hektor_contact_id = r.hektor_contact_id limit 1;
    if ec.hektor_contact_id is null then continue; end if;
    select target_email, target_user_id into te, tu
      from public.app_console_resolve_contact_hektor_user(ec, null, null);
    insert into public.app_console_job(job_type, payload_json, status, priority, requested_at)
    values ('update_hektor_contact',
      coalesce(r.push_fields, '{}'::jsonb) || jsonb_build_object(
        'hektor_contact_id', r.hektor_contact_id,
        'contact_id', r.hektor_contact_id,
        'from_pending', true,
        'base_snapshot', r.base_snapshot,
        'hektor_user_email', te, 'target_hektor_user_email', te,
        'hektor_user_id', tu, 'target_hektor_user_id', tu,
        'contact_negociateur_email', ec.negociateur_email,
        'contact_hektor_negociateur_id', ec.hektor_negociateur_id,
        'source', coalesce(r.source, 'nego_app')),
      'pending', 70, now())
    returning id into jid;
    update public.app_contact_pending set push_job_id = jid, updated_at = now()
      where hektor_contact_id = r.hektor_contact_id;
    n := n + 1;
  end loop;
  return n;
end $function$;

-- ---- 4) Cron (toutes les minutes, miroir app-annonce-push-due) ----
select cron.schedule('app-contact-push-due', '*/1 * * * *', $$select public.app_contact_enqueue_due_pushes();$$);
