-- ============================================================================
-- INVERSE -- patch_menage_orphelins_api_2026-10-25.sql
-- ============================================================================
-- Ne juge QUE sa part (lecon 31) : retire les deux delais, remet la ligne nue,
-- retire le plancher, et verifie que l'empreinte revient EXACTEMENT a be11efc3...
-- ⚠ Apres ce retour, l'etape du run ECHOUE de nouveau chaque nuit (safeupdate) ;
--   le cron n. 11 continue de faire le menage.
-- ============================================================================

alter function public.app_sweep_search_orphans() reset statement_timeout;
alter function public.app_sweep_search_orphans() reset lock_timeout;

do $inverse$
declare
  v_src  text;
  v_a1   text := replace('  delete from _cible_sweep where true;', chr(13), '');
  v_n1   text := replace('  delete from _cible_sweep;', chr(13), '');
  v_debut text := replace('  -- 25/10/2026 : LE PLANCHER.', chr(13), '');
  v_fin   text := replace('  create temporary table if not exists _cible_sweep (hektor_contact_id text primary key, nouvelle_cle text) on commit drop;', chr(13), '');
  v_i int; v_j int;
begin
  v_src := replace(pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure), chr(13), '');
  if (length(v_src) - length(replace(v_src, v_a1, ''))) / length(v_a1) <> 1 then
    raise exception 'STOP : la ligne corrigee n apparait pas exactement 1 fois -- rien n a ete touche';
  end if;
  v_i := position(v_debut in v_src);
  v_j := position(v_fin in v_src);
  if v_i = 0 or v_j = 0 or v_j < v_i then
    raise exception 'STOP : bloc du plancher introuvable -- rien n a ete touche';
  end if;
  -- on retire le bloc du plancher (du commentaire jusqu'a la ligne create temporary, exclue)
  v_src := substr(v_src, 1, v_i - 1) || substr(v_src, v_j);
  v_src := replace(v_src, v_a1, v_n1);
  execute v_src;
  v_src := replace(pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure), chr(13), '');
  if md5(v_src) <> 'be11efc3e8134afa50ba7ca47b0681e8' then
    raise exception 'ATTENTION : empreinte % apres retour (attendue be11efc3...) -- relire la fonction', md5(v_src);
  end if;
end
$inverse$;

notify pgrst, 'reload schema';

select 'empreinte revenue' as controle,
       case when md5(replace(pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure), chr(13), ''))
                 = 'be11efc3e8134afa50ba7ca47b0681e8' then 'OK (be11efc3)' else 'NON' end as verdict
union all
select 'delais retires',
       case when (select proconfig from pg_proc where oid = 'public.app_sweep_search_orphans()'::regprocedure)::text not ilike '%timeout%'
            then 'OK' else 'NON' end;
