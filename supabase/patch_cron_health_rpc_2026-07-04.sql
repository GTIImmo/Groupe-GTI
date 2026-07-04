-- ============================================================================
-- patch_cron_health_rpc_2026-07-04.sql
--
-- Expose la sante pg_cron au monitoring (check_gti_health.py -> check_cron_health).
-- Les tables cron.* ne sont pas accessibles via PostgREST (schema hors expose) :
-- une petite RPC SECURITY DEFINER lit le dernier run/statut de chaque job.
--
-- SECURITE : lecture seule ; execute REVOKE de public/anon/authenticated,
-- GRANT au seul service_role (la cle utilisee par le monitor). Ne renvoie que
-- des metadonnees d'ordonnancement (aucune donnee metier).
--
-- Contexte : le 04/07 le cron "rapprochement-alerts" echouait 72x sans que le
-- monitoring ne le voie. Cette RPC comble cet angle mort.
-- ============================================================================

create or replace function public.app_cron_health()
returns table(jobname text, active boolean, last_run timestamptz, last_status text)
language sql
security definer
set search_path = public
as $$
  select j.jobname::text,
         j.active,
         (select max(r.start_time) from cron.job_run_details r where r.jobid = j.jobid) as last_run,
         (select r.status from cron.job_run_details r where r.jobid = j.jobid
           order by r.start_time desc limit 1) as last_status
  from cron.job j
$$;

revoke all on function public.app_cron_health() from public, anon, authenticated;
grant execute on function public.app_cron_health() to service_role;
