-- ============================================================================
-- PATCH -- le menage des orphelins de recherche passe ENFIN par l'API (25/10/2026)
-- ============================================================================
-- Audit : notice/AUDIT_ALERTES_MONITORING_2026-10-24.md, section 2 sexies.
--
-- LE DEFAUT. app_sweep_search_orphans() commence par `delete from _cible_sweep;`
--   (une table TEMPORAIRE de travail), SANS WHERE. Par l'API, le role authenticator
--   charge `safeupdate`, qui refuse tout DELETE sans WHERE (21000). L'etape du run
--   (phase2/sync/menage_orphelins_recherche.py) echoue donc CHAQUE NUIT depuis le
--   16/10 ; le cron n. 11 (role postgres, sans safeupdate) reussit.
--
-- TROIS PIECES EN BASE (la 4e est dans le script du run) :
--   1. `delete from _cible_sweep where true;` -- vide la MEME table, accepte par safeupdate.
--   2. LE PLANCHER : si app_contact_search_current compte moins de 5 000 recherches
--      (11 544 le 25/10), la fonction ne supprime RIEN, l'ecrit dans son journal et
--      rend {"ok": false, "raison": "plancher"}. Une recherche absente fait SUPPRIMER
--      ses rapprochements et son historique de score -- l'historique ne se recalcule
--      pas. Protege le cron ET l'etape d'une table abimee par un push coupe en route.
--   3. DES DELAIS PROPRES A LA FONCTION : statement_timeout 60 s (doc Supabase,
--      « Function level » : respecte par l'API) et lock_timeout 45 s. Par l'API, la
--      limite etait 8 s ; la fonction a mis 8,5 s le 25/10 a 06:00 et 10,5 s le 11/10.
--      ⚠ lock_timeout s'applique AUSSI au cron (illimite -> 45 s) : plus longue attente
--        observee ~11 s.
--   Puis `notify pgrst, 'reload schema'` : l'API relit les reglages des fonctions.
--
-- ⚠ ANCRES SUR UNE SEULE LIGNE + replace(chr(13)) des deux cotes (lecon 30).
-- EMPREINTE DE DEPART : be11efc3e8134afa50ba7ca47b0681e8 (lue le 25/10, inchangee depuis).
-- EMPREINTE APRES POSE : f39dc33f0e73a2a06bd4fce103829a43 -- la meme dans la repetition et a la
--   pose (25/10 ~08:30, par Claude avec l'accord de Frederic). Repetition : 12 controles verts.
-- ⛔ AVANT : avoir joue ..._REPETITION.sql. EN CAS DE PROBLEME : ..._INVERSE.sql.
-- ⛔ CE QUE CE PATCH NE PEUT PAS PROUVER : le passage par l'API. La preuve est le run
--    suivant : `DONE phase2 menage orphelins de recherche attempt 1/2`.
-- ============================================================================

do $patch$
declare
  v_src  text;
  v_new  text;
  v_a1   text := replace('  delete from _cible_sweep;', chr(13), '');
  v_n1   text := replace('  delete from _cible_sweep where true;', chr(13), '');
  v_a2   text := replace('  create temporary table if not exists _cible_sweep (hektor_contact_id text primary key, nouvelle_cle text) on commit drop;', chr(13), '');
  v_n2   text;
  v_vu   int;
begin
  v_n2 := replace($plancher$  -- 25/10/2026 : LE PLANCHER. Une recherche absente de app_contact_search_current fait
  --   SUPPRIMER ses rapprochements et son historique de score (qui ne se recalcule pas).
  --   Une table anormalement petite (push coupe en route) ne doit rien faire effacer.
  --   11 544 recherches le 25/10 ; plancher 5 000. Voir AUDIT_ALERTES_MONITORING_2026-10-24.md.
  if (select count(*) from public.app_contact_search_current) < 5000 then
    insert into public.app_sweep_search_orphans_log(ok, raison)
    values (false, 'plancher')
    on conflict (run_at) do nothing;
    return jsonb_build_object('ok', false, 'raison', 'plancher',
      'recherches', (select count(*) from public.app_contact_search_current));
  end if;
$plancher$, chr(13), '') || v_a2;

  v_src := replace(pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure), chr(13), '');
  if md5(v_src) <> 'be11efc3e8134afa50ba7ca47b0681e8' then
    raise exception 'STOP : empreinte % au lieu de be11efc3... -- la fonction a change, la RELIRE avant de patcher.', md5(v_src);
  end if;
  v_vu := (length(v_src) - length(replace(v_src, v_a1, ''))) / length(v_a1);
  if v_vu <> 1 then raise exception 'STOP : l ancre 1 (delete nu) apparait % fois (attendu 1)', v_vu; end if;
  v_vu := (length(v_src) - length(replace(v_src, v_a2, ''))) / length(v_a2);
  if v_vu <> 1 then raise exception 'STOP : l ancre 2 (create temporary) apparait % fois (attendu 1)', v_vu; end if;

  v_new := replace(replace(v_src, v_a1, v_n1), v_a2, v_n2);
  execute v_new;

  v_src := replace(pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure), chr(13), '');
  if position(v_n1 in v_src) = 0 or position('''plancher''' in v_src) = 0 or position(v_a1 in v_src) > 0 then
    raise exception 'STOP : la fonction posee ne porte pas les deux changements';
  end if;
end
$patch$;

alter function public.app_sweep_search_orphans() set statement_timeout = '60s';
alter function public.app_sweep_search_orphans() set lock_timeout = '45s';

notify pgrst, 'reload schema';

-- ① LE CONTROLE APRES (lecture seule) : tout doit dire OK.
select 'ligne corrigee (where true)' as controle,
       case when position('delete from _cible_sweep where true;' in pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure)) > 0
            then 'OK' else 'NON' end as verdict
union all
select 'plancher pose',
       case when position('''plancher''' in pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure)) > 0
            then 'OK' else 'NON' end
union all
select 'delais propres a la fonction',
       coalesce((select array_to_string(proconfig, ' | ') from pg_proc where oid = 'public.app_sweep_search_orphans()'::regprocedure), 'AUCUN')
union all
select 'empreinte apres pose',
       md5(replace(pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure), chr(13), ''))
union all
select 'recherches (plancher 5 000)', (select count(*)::text from public.app_contact_search_current);
