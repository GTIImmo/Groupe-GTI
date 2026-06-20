-- =====================================================================
-- Vue d'observabilité Supabase-first (garde-fou n°6) — 2026-06-20
-- ---------------------------------------------------------------------
-- Pilotage du push débouncé des affinages de recherche : visualise l'état
-- de chaque pending (app_search_pending) + le job de push lié.
-- Additif (CREATE VIEW), aucune donnée modifiée, aucune table touchée.
-- security_invoker=on -> si un jour on l'expose, la RLS sous-jacente joue.
-- NON exposée à `authenticated` (pas de GRANT) : lecture admin/service_role.
-- =====================================================================

create or replace view public.app_search_pending_audit
  with (security_invoker = on)
as
select
  p.hektor_contact_id,
  p.search_index,
  p.source,                                  -- nego_app | espace_client
  ec.negociateur_email,
  case
    when p.conflict then 'conflit'                                       -- Hektor a changé OU plafond retry atteint
    when j.status = 'error' then 'echec_retry'                          -- job en erreur -> sera ré-armé
    when j.id is not null and j.finished_at is null
         and j.requested_at < now() - interval '30 minutes' then 'push_perdu'   -- job parti depuis trop longtemps
    when j.id is not null and j.status in ('pending','running') then 'push_en_cours'
    when p.push_job_id is null and p.push_after <= now() then 'a_pousser'        -- dû, sera enfilé au prochain sweep
    when p.push_job_id is null and p.push_after > now() then 'en_attente_debounce'
    else 'indetermine'
  end as etat,
  p.push_attempts,
  p.conflict,
  greatest(0, round(extract(epoch from (p.push_after - now())) / 60))::int as minutes_avant_push,
  p.push_after,
  p.dirty_at,
  p.updated_at,
  p.push_job_id,
  j.status        as job_status,
  j.attempt_count as job_attempt_count,
  left(coalesce(j.error_message, ''), 200) as job_error,
  j.requested_at  as job_requested_at,
  j.finished_at   as job_finished_at
from public.app_search_pending p
left join public.app_console_job j on j.id = p.push_job_id
left join public.app_contact_current ec on ec.hektor_contact_id = p.hektor_contact_id;

comment on view public.app_search_pending_audit is
  'Observabilité du push débouncé des affinages de recherche (Supabase-first / garde-fou n°6). Admin/service_role uniquement.';
