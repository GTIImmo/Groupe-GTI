-- ═══════════════════════════════════════════════════════════════════════════
-- 5b lot 3 — LA BARRIERE : UN ENVOI ATTEND AU LIEU D'ECHOUER      21/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Suite de l'option B. La porte du worker (5eef5eb) REFUSE d'envoyer a Hektor un
-- contact ne dans l'app. C'est juste, mais insuffisant : la file continuerait de
-- lui presenter le travail, il echouerait 5 fois, et finirait en conflit -- donc
-- en ALERTE, pour une situation normale.
--
-- Les deux fonctions de mise en file apprennent donc a ATTENDRE : tant que le
-- contact n'a pas de numero chez Hektor, sa ligne reste dans la bannette, sans
-- travail cree. Des que le numero arrive, le declencheur pose la case cible et
-- le passage suivant envoie la ligne.
--
-- AUCUN EFFET AUJOURD'HUI : les 61 955 contacts ont leur case cible. La barriere
-- ne se fermera qu'au premier contact ne dans l'app (lot L4).
--
-- RETOUR ARRIERE : les definitions d'avant sont dans le commit de ce patch
-- (scratchpad defs_enqueue.sql).
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_contact_enqueue_due_pushes()
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare r record; ec public.app_contact_current%rowtype; te text; tu text;
        n int := 0; jid uuid; max_attempts int := 5;
begin
  delete from public.app_contact_pending p
  using public.app_console_job j
  where p.push_job_id = j.id and j.status = 'done' and p.conflict = false;

  -- C.1' 24/08 : LA PURGE DES 24 H EST RETIREE.
  -- Elle effacait la ligne ET la saisie (base_snapshot + push_fields) : une
  -- edition bloquee etait perdue au bout d'un jour, vue ou pas. Desormais elle
  -- reste jusqu'a ce qu'un humain la traite (bandeau sur la fiche + sonde).

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
    select * into ec from public.app_contact_current where hektor_contact_id = r.hektor_contact_id limit 1;
    if ec.hektor_contact_id is null then continue; end if;
    -- ── 5b 21/09/2026 : LA BARRIERE ───────────────────────────────────────
    -- Pas de numero chez Hektor -> on N'ENFILE PAS, la ligne ATTEND dans la
    -- bannette. C'est le geste 2.6 du plan : « un travail sans numero Hektor
    -- attend au lieu d'echouer ». Sans lui, le travail partirait, la porte du
    -- worker le refuserait, il serait rejoue 5 fois puis marque en conflit --
    -- une alerte pour une situation parfaitement normale (le contact vient de
    -- naitre dans l'app, Hektor ne le connait pas encore).
    -- Des que le numero arrive, le declencheur remplit la case et le passage
    -- suivant envoie la ligne : l'attente se resout toute seule.
    if coalesce(ec.hektor_target_id, '') = '' then continue; end if;
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


CREATE OR REPLACE FUNCTION public.app_search_enqueue_due_pushes()
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare r record; ec public.app_contact_current%rowtype; te text; tu text; n int := 0; jid uuid;
        max_attempts int := 5;
begin
  -- (0a) Job dÃ©jÃ  'done' mais pending encore lÃ  -> obsolÃ¨te, on supprime.
  delete from public.app_search_pending p
  using public.app_console_job j
  where p.push_job_id = j.id and j.status = 'done' and p.conflict = false;

  -- (0a-bis) TTL CONFLIT : conflit non rÃ©solu depuis > 24h -> on libÃ¨re le verrou.
  -- C.1' 24/08 : LA PURGE DES 24 H EST RETIREE.
  -- Elle effacait la ligne ET la saisie (base_snapshot + push_fields) : une
  -- edition bloquee etait perdue au bout d'un jour, vue ou pas. Desormais elle
  -- reste jusqu'a ce qu'un humain la traite (bandeau sur la fiche + sonde).

  -- (0b) Job de push Ã‰CHOUÃ‰ / PERDU / INTROUVABLE -> rÃ©-armer avec backoff (sous le plafond).
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

  -- (0c) Plafond atteint -> conflict=true (surface + stop). Sera nettoyÃ© par (0a-bis) aprÃ¨s 24h.
  update public.app_search_pending p
  set conflict = true, updated_at = now()
  where p.push_job_id is not null and p.conflict = false and p.push_attempts >= max_attempts
    and (
      not exists (select 1 from public.app_console_job j where j.id = p.push_job_id)
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id and j.status = 'error')
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id
                 and j.finished_at is null and j.requested_at < now() - interval '30 minutes')
    );

  -- (1) Boucle d'enfilage normale â€” INCHANGÃ‰E.
  for r in select * from public.app_search_pending
           where push_after <= now() and push_job_id is null and conflict = false and push_search is not null
           order by push_after limit 100 loop
    select * into ec from public.app_contact_current where hektor_contact_id = r.hektor_contact_id limit 1;
    if ec.hektor_contact_id is null then continue; end if;
    -- ── 5b 21/09/2026 : LA BARRIERE ───────────────────────────────────────
    -- Pas de numero chez Hektor -> on N'ENFILE PAS, la ligne ATTEND dans la
    -- bannette. C'est le geste 2.6 du plan : « un travail sans numero Hektor
    -- attend au lieu d'echouer ». Sans lui, le travail partirait, la porte du
    -- worker le refuserait, il serait rejoue 5 fois puis marque en conflit --
    -- une alerte pour une situation parfaitement normale (le contact vient de
    -- naitre dans l'app, Hektor ne le connait pas encore).
    -- Des que le numero arrive, le declencheur remplit la case et le passage
    -- suivant envoie la ligne : l'attente se resout toute seule.
    if coalesce(ec.hektor_target_id, '') = '' then continue; end if;
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


-- ── LA SONDE : CE QUI ATTEND, ET DEPUIS QUAND ──────────────────────────────
create or replace view public.app_v_envois_en_attente_hektor as
  select 'recherche' as objet, p.hektor_contact_id, p.search_index::text as detail, p.dirty_at
    from public.app_search_pending p
    join public.app_contact_current c on c.hektor_contact_id = p.hektor_contact_id
   where coalesce(c.hektor_target_id, '') = '' and p.push_search is not null
  union all
  select 'contact', p.hektor_contact_id, null, p.dirty_at
    from public.app_contact_pending p
    join public.app_contact_current c on c.hektor_contact_id = p.hektor_contact_id
   where coalesce(c.hektor_target_id, '') = '';

comment on view public.app_v_envois_en_attente_hektor is
  '5b 21/09/2026 : saisies qui attendent que leur contact existe chez Hektor. Normal quelques minutes apres une creation ; anormal au-dela -- le worker de creation n''a pas rapporte le numero.';

grant select on public.app_v_envois_en_attente_hektor to service_role, authenticated;
