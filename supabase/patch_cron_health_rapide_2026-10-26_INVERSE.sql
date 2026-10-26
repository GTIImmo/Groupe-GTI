-- ============================================================================
-- INVERSE -- patch_cron_health_rapide_2026-10-26.sql
-- ============================================================================
-- Ne juge QUE sa part (lecon 31) : remet l'ancienne forme mot pour mot et verifie que
-- l'empreinte revient EXACTEMENT a ac303763... ; la signature et les droits ne bougent pas.
-- ⚠ Apres ce retour, la sonde pg_cron est de nouveau coupee a 8 s ~4 passages sur 10 --
--   mais grace a A1 elle le DIT (« illisible ») au lieu d'afficher vert.
-- ============================================================================

do $inverse$
declare
  v_src text;
begin
  v_src := replace(pg_get_functiondef('public.app_cron_health()'::regprocedure), chr(13), '');
  if position('order by r.runid desc' in v_src) = 0 then
    raise exception 'STOP : la fonction ne porte pas la forme du 26/10 -- rien n a ete touche';
  end if;

  execute replace($def$
CREATE OR REPLACE FUNCTION public.app_cron_health()
 RETURNS TABLE(jobname text, active boolean, schedule text, last_run timestamp with time zone, last_status text)
 LANGUAGE sql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select j.jobname::text,
         j.active,
         j.schedule::text,
         (select max(r.start_time) from cron.job_run_details r where r.jobid = j.jobid) as last_run,
         (select r.status from cron.job_run_details r where r.jobid = j.jobid
           order by r.start_time desc limit 1) as last_status
  from cron.job j
$function$
$def$, chr(13), '');

  v_src := replace(pg_get_functiondef('public.app_cron_health()'::regprocedure), chr(13), '');
  if md5(v_src) <> 'ac303763457278129147d23451295183' then
    raise exception 'ATTENTION : empreinte % apres retour (attendue ac303763...) -- relire la fonction', md5(v_src);
  end if;
end
$inverse$;

select 'empreinte revenue' as controle,
       case when md5(replace(pg_get_functiondef('public.app_cron_health()'::regprocedure), chr(13), ''))
                 = 'ac303763457278129147d23451295183' then 'OK (ac303763)' else 'NON' end as verdict
union all
select 'droits', (select proacl::text from pg_proc where oid = 'public.app_cron_health()'::regprocedure);
