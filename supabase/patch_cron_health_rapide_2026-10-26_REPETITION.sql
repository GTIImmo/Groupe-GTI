-- ============================================================================
-- REPETITION -- patch_cron_health_rapide_2026-10-26.sql
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS. Le `begin;` et l'ERREUR VOLONTAIRE de la fin font que
--    RIEN n'est ecrit. Lecture seule sur cron.* ; aucune tache n'est touchee.
--
-- CE QU'ELLE PROUVE :
--   1-avant    empreinte ac303763, droits, duree de l'ancienne forme, sa reponse par tache
--   2-pose     le patch passe ; droits et security definer INCHANGES ; nouvelle empreinte
--   3-meme     la nouvelle forme rend les MEMES 12 taches (nom, active, cadence), et pour
--              chacune un dernier passage egal ou plus recent (les taches a la minute
--              tournent entre les deux lectures) avec le meme statut quand c'est le meme
--   4-vite     sa duree
--   5-trou     une tache sans passage dans la fenetre rend un last_run VIDE (sonde A1)
--   6-retour   l'inverse remet EXACTEMENT ac303763, droits inchanges
-- ============================================================================

begin;
set local statement_timeout = '120s';
set local lock_timeout = '10s';

create temporary table essai_mesures (id serial, etape text, mesure text, valeur text) on commit drop;
create temporary table essai_avant on commit drop as select * from public.app_cron_health() where false;

do $avant$
declare t0 timestamptz;
begin
  insert into essai_mesures (etape, mesure, valeur) values
   ('1-avant  ', 'empreinte                    ', md5(replace(pg_get_functiondef('public.app_cron_health()'::regprocedure), chr(13), ''))),
   ('1-avant  ', 'droits                       ', (select proacl::text from pg_proc where oid = 'public.app_cron_health()'::regprocedure));
  t0 := clock_timestamp();
  insert into essai_avant select * from public.app_cron_health();
  insert into essai_mesures (etape, mesure, valeur) values
   ('1-avant  ', 'duree ancienne forme         ', round(extract(epoch from clock_timestamp() - t0) * 1000) || ' ms');
end
$avant$;

-- =========================== 2. LA POSE (copie conforme du patch) ==========
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

do $apres$
declare t0 timestamptz; v_ms int; r record; n_ecart int := 0; n int := 0;
begin
  insert into essai_mesures (etape, mesure, valeur) values
   ('2-pose   ', 'empreinte apres pose         ', md5(replace(pg_get_functiondef('public.app_cron_health()'::regprocedure), chr(13), ''))),
   ('2-pose   ', 'droits                       ', (select proacl::text from pg_proc where oid = 'public.app_cron_health()'::regprocedure)
       || case when (select proacl::text from pg_proc where oid = 'public.app_cron_health()'::regprocedure)
                    = (select valeur from essai_mesures where mesure like 'droits%' and etape like '1%') then '  -- OK inchanges' else '  -- STOP : CHANGES' end),
   ('2-pose   ', 'security definer             ', (select prosecdef::text from pg_proc where oid = 'public.app_cron_health()'::regprocedure));

  t0 := clock_timestamp();
  create temporary table essai_apres on commit drop as select * from public.app_cron_health();
  v_ms := round(extract(epoch from clock_timestamp() - t0) * 1000);
  insert into essai_mesures (etape, mesure, valeur) values ('4-vite   ', 'duree nouvelle forme         ', v_ms || ' ms');

  for r in
    select a.jobname, a.active, a.schedule, a.last_run av_run, a.last_status av_st, b.last_run ap_run, b.last_status ap_st,
           (b.jobname is null) manque
      from essai_avant a left join essai_apres b on b.jobname = a.jobname
     order by a.jobname
  loop
    n := n + 1;
    -- un passage « en cours » (starting / connecting / running) a le droit d'avoir fini entre
    -- les deux lectures (l'ancienne en prend ~10 s) : 1re repetition du 26/10, 6 cas ainsi.
    if r.manque or r.ap_run is null or r.ap_run < r.av_run
       or (r.ap_run = r.av_run and r.ap_st is distinct from r.av_st
           and r.av_st not in ('starting', 'connecting', 'running')) then
      n_ecart := n_ecart + 1;
    end if;
    insert into essai_mesures (etape, mesure, valeur) values ('3-meme   ', rpad(r.jobname, 29),
      coalesce(to_char(r.av_run at time zone 'Europe/Paris', 'DD/MM HH24:MI:SS'), 'vide') || ' ' || coalesce(r.av_st, '-')
      || '  ->  ' || coalesce(to_char(r.ap_run at time zone 'Europe/Paris', 'DD/MM HH24:MI:SS'), 'vide') || ' ' || coalesce(r.ap_st, '-'));
  end loop;
  insert into essai_mesures (etape, mesure, valeur) values ('3-meme   ', 'BILAN                        ',
    n || ' taches avant, ' || (select count(*) from essai_apres) || ' apres, ' || n_ecart || ' ecart(s)'
    || case when n_ecart = 0 and n = (select count(*) from essai_apres) then '  -- OK' else '  -- STOP' end);
end
$apres$;

-- =========================== 5. LE TROU : une tache sans passage dans la fenetre =====
insert into essai_mesures (etape, mesure, valeur)
select '5-trou   ', 'tache inconnue (jobid -1)    ',
       coalesce((select r.start_time::text from cron.job_run_details r
                  where r.jobid = -1 and r.runid > (select max(x.runid) - 50000 from cron.job_run_details x)
                  order by r.runid desc limit 1), 'vide -> la sonde A1 dit « aucun passage connu »');

-- =========================== 6. LE RETOUR (copie conforme de l'inverse) ====
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
end
$inverse$;

insert into essai_mesures (etape, mesure, valeur)
select '6-retour ', 'empreinte revenue            ',
       case when md5(replace(pg_get_functiondef('public.app_cron_health()'::regprocedure), chr(13), ''))
                 = 'ac303763457278129147d23451295183' then 'oui (ac303763)'
            else 'NON : ' || md5(replace(pg_get_functiondef('public.app_cron_health()'::regprocedure), chr(13), '')) end
union all
select '6-retour ', 'droits                       ', (select proacl::text from pg_proc where oid = 'public.app_cron_health()'::regprocedure);

do $fin$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id) into v_txt from essai_mesures;
  raise exception '%', 'ESSAI ANNULE -- rien n a ete ecrit.' || chr(10) || v_txt;
end
$fin$;

rollback;
