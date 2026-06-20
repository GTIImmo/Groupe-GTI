-- =====================================================================
-- TIER 2 — Lot 2 : sweep + push débouncé des annonces
-- 2026-06-20. Clone de app_search_enqueue_due_pushes (mêmes garde-fous
-- retry/TTL/conflit). Crée un job `update_hektor_annonce_fields` débouncé.
-- ⚠️ Le CRON n'est PAS créé ici (volontaire) : tant que le garde-fou worker
-- (Lot 3) et le front (Lot 5) ne sont pas en place, aucun pending réel ne
-- doit partir en automatique. On l'ajoutera quand la chaîne sera complète.
-- =====================================================================

create or replace function public.app_annonce_enqueue_due_pushes()
 returns integer language plpgsql security definer set search_path to 'public'
as $function$
declare r record; n int := 0; jid uuid; max_attempts int := 5;
begin
  -- (0a) job déjà 'done' mais pending encore là -> obsolète.
  delete from public.app_annonce_pending p
  using public.app_console_job j
  where p.push_job_id = j.id and j.status = 'done';

  -- (0a-bis) TTL conflit 24h.
  delete from public.app_annonce_pending
  where conflict = true and updated_at < now() - interval '24 hours';

  -- (0b) job échoué / perdu / introuvable -> ré-armer avec backoff (sous plafond).
  update public.app_annonce_pending p
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

  -- (0c) plafond atteint -> conflit (surface + stop). Nettoyé par (0a-bis) après 24h.
  update public.app_annonce_pending p
  set conflict = true, updated_at = now()
  where p.push_job_id is not null and p.conflict = false and p.push_attempts >= max_attempts
    and (
      not exists (select 1 from public.app_console_job j where j.id = p.push_job_id)
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id and j.status = 'error')
      or exists (select 1 from public.app_console_job j where j.id = p.push_job_id
                 and j.finished_at is null and j.requested_at < now() - interval '30 minutes')
    );

  -- (1) Enfilage : 1 job update_hektor_annonce_fields débouncé par pending dû.
  --     Le worker résout le négo depuis le dossier (preferDossierOwner) ; on passe
  --     from_pending + base_snapshot pour le garde-fou anti-écrasement (Lot 3).
  for r in select * from public.app_annonce_pending
           where push_after <= now() and push_job_id is null and conflict = false and push_fields is not null
           order by push_after limit 100 loop
    insert into public.app_console_job(job_type, app_dossier_id, hektor_annonce_id, payload_json, status, priority, requested_at)
    values ('update_hektor_annonce_fields', r.app_dossier_id, r.hektor_annonce_id,
      coalesce(r.push_fields, '{}'::jsonb) || jsonb_build_object(
        'app_dossier_id', r.app_dossier_id,
        'hektor_annonce_id', r.hektor_annonce_id,
        'from_pending', true,
        'base_snapshot', r.base_snapshot,
        'source', coalesce(r.source, 'nego_app')),
      'pending', 70, now())
    returning id into jid;
    update public.app_annonce_pending set push_job_id = jid, updated_at = now()
      where app_dossier_id = r.app_dossier_id;
    n := n + 1;
  end loop;
  return n;
end $function$;
