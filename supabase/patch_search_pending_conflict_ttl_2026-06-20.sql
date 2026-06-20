-- =====================================================================
-- TTL conflit (garde-fou n°6) — 2026-06-20
-- ---------------------------------------------------------------------
-- Un pending passé en `conflict=true` (Hektor a changé en même temps, OU push
-- échoué 5x) reste bloqué pour TOUJOURS : tant qu'il existe, la recherche est
-- "dirty" -> le pipeline la saute -> l'app garde la valeur en attente et ne
-- réaffiche jamais la valeur officielle Hektor.
--
-- Fix : ménage automatique. Si un conflit reste non résolu > 24h (le négo a été
-- alerté entre-temps), on supprime le pending -> le verrou "dirty" est libéré ->
-- la prochaine synchro (read-through à l'ouverture / run recherches actives nuit /
-- quotidien) réaligne la recherche sur la valeur Hektor.
--
-- Implémentation : 1 DELETE ajouté dans le sweep existant (cron */1). Le reste de
-- la fonction est INCHANGÉ par rapport à la migration search_pending_retry_stuck_fix.
-- =====================================================================

create or replace function public.app_search_enqueue_due_pushes()
 returns integer
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare r record; ec public.app_contact_current%rowtype; te text; tu text; n int := 0; jid uuid;
        max_attempts int := 5;
begin
  -- (0a) Job déjà 'done' mais pending encore là -> obsolète, on supprime.
  delete from public.app_search_pending p
  using public.app_console_job j
  where p.push_job_id = j.id and j.status = 'done';

  -- (0a-bis) TTL CONFLIT : conflit non résolu depuis > 24h -> on libère le verrou.
  --          La prochaine synchro réaligne la recherche sur la valeur Hektor officielle.
  delete from public.app_search_pending
  where conflict = true and updated_at < now() - interval '24 hours';

  -- (0b) Job de push ÉCHOUÉ / PERDU / INTROUVABLE -> ré-armer avec backoff (sous le plafond).
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

  -- (0c) Plafond atteint -> conflict=true (surface + stop). Sera nettoyé par (0a-bis) après 24h.
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
