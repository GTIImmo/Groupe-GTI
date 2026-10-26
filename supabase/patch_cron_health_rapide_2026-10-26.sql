-- ============================================================================
-- PATCH A2 -- app_cron_health() rapide (26/10/2026)
-- ============================================================================
-- Audit : notice/AUDIT_ALERTES_MONITORING_2026-10-24.md, section 4.
--
-- LE DEFAUT. La fonction relit cron.job_run_details 24 FOIS (2 sous-requetes x 12
--   taches). Cette table n'est jamais purgee (doc Supabase : « not cleaned up
--   automatically ») : 1 226 263 lignes, 225 Mo au 26/10, +10 372 par jour, et AUCUN
--   index sur jobid (seulement la cle runid ; table de supabase_admin, on ne peut pas
--   en creer). 3,6 s au calme, > 8 s sous charge : coupee par l'API (57014) sur 146
--   passages du moniteur sur 362 -- et la sonde les affichait VERTS (corrige en A1).
--
-- LE REMEDE. Meme signature, memes colonnes, memes droits. Pour chaque tache, on
--   remonte la cle runid A L'ENVERS dans les 50 000 derniers passages (~4,8 jours)
--   et on prend le premier : 3,4 ms au lieu de 3 585 ms (mesure du 26/10).
--   ⚠ Une tache sans passage dans la fenetre rend last_run vide : la sonde (A1) le
--     signale desormais (« aucun passage connu »). Elle l'IGNORAIT avant.
--   ⚠ runid vient d'une sequence : plus grand = plus recent.
--
-- ⛔ AVANT : avoir joue ..._REPETITION.sql. EN CAS DE PROBLEME : ..._INVERSE.sql.
-- EMPREINTE DE DEPART : ac303763457278129147d23451295183.
-- ============================================================================

do $patch$
declare
  v_src text;
begin
  v_src := replace(pg_get_functiondef('public.app_cron_health()'::regprocedure), chr(13), '');
  if md5(v_src) <> 'ac303763457278129147d23451295183' then
    raise exception 'STOP : empreinte % au lieu de ac303763... -- la fonction a change, la RELIRE.', md5(v_src);
  end if;

  execute replace($def$
create or replace function public.app_cron_health()
returns table(jobname text, active boolean, schedule text, last_run timestamptz, last_status text)
language sql
security definer
set search_path = public
as $function$
  -- 26/10/2026 : lecture par la cle runid, a l'envers, dans les 50 000 derniers passages.
  --   L'ancienne forme relisait cron.job_run_details (1,2 M lignes, sans index sur jobid)
  --   24 fois : 3,6 s, coupee a 8 s par l'API. Audit : AUDIT_ALERTES_MONITORING_2026-10-24.md §4.
  select j.jobname::text,
         j.active,
         j.schedule::text,
         d.start_time as last_run,
         d.status     as last_status
    from cron.job j
    left join lateral (
      select r.start_time, r.status
        from cron.job_run_details r
       where r.jobid = j.jobid
         and r.runid > (select max(x.runid) - 50000 from cron.job_run_details x)
       order by r.runid desc
       limit 1
    ) d on true
$function$
$def$, chr(13), '');

  v_src := replace(pg_get_functiondef('public.app_cron_health()'::regprocedure), chr(13), '');
  if position('order by r.runid desc' in v_src) = 0 then
    raise exception 'STOP : la fonction posee n''est pas la nouvelle forme';
  end if;
end
$patch$;

-- ① LE CONTROLE APRES (lecture seule).
select 'empreinte apres pose' as controle,
       md5(replace(pg_get_functiondef('public.app_cron_health()'::regprocedure), chr(13), '')) as verdict
union all
select 'droits (attendu postgres + service_role seuls)',
       (select proacl::text from pg_proc where oid = 'public.app_cron_health()'::regprocedure)
union all
select 'security definer garde',
       (select prosecdef::text from pg_proc where oid = 'public.app_cron_health()'::regprocedure)
union all
select 'taches rendues', (select count(*)::text from public.app_cron_health())
union all
select 'taches actives sans passage connu', (select count(*)::text from public.app_cron_health() where active and last_run is null);
