-- ============================================================================
-- REPETITION -- patch_menage_orphelins_api_2026-10-25.sql
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS. Le `begin;` et l'ERREUR VOLONTAIRE de la fin font
--    que RIEN n'est ecrit : ni la fonction, ni ses delais, ni le menage, ni le journal.
-- ⚠ Elle REDUIT temporairement app_contact_search_current a 100 lignes (pour eprouver
--   le plancher) : ses ecrivains attendent la fin de la transaction (quelques
--   secondes). Le seul declencheur de la table est AFTER INSERT OR UPDATE (pas de
--   DELETE) et aucune table n'en depend (0 cle etrangere) -- verifie le 25/10.
--   Pas pendant le run (04:00-06:30).
--
-- CE QU'ELLE PROUVE :
--   1-avant   empreinte be11efc3 ; aucun delai propre
--   2-pose    le patch passe (ancres uniques), la ligne corrigee et le plancher sont la,
--             les delais 60 s / 45 s sont poses
--   3-positif table pleine -> {"ok": true}
--   4-plancher table reduite a 100 -> {"ok": false, "raison": "plancher"}, et AUCUN
--             rapprochement, AUCUN historique de score supprime (temoin du refus)
--   5-retour  l'inverse remet EXACTEMENT be11efc3, sans delai
-- ⛔ CE QU'ELLE NE PROUVE PAS : le passage par l'API (safeupdate, 8 s). Preuve = le run.
-- ============================================================================

begin;
set local statement_timeout = '180s';
set local lock_timeout = '10s';

create temporary table essai_mesures (id serial, etape text, mesure text, valeur text) on commit drop;

insert into essai_mesures (etape, mesure, valeur)
select '1-avant  ', 'empreinte                      ',
       md5(replace(pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure), chr(13), ''));
insert into essai_mesures (etape, mesure, valeur)
select '1-avant  ', 'delais propres                 ',
       coalesce((select array_to_string(proconfig, ' | ') from pg_proc where oid = 'public.app_sweep_search_orphans()'::regprocedure), 'aucun');

-- =========================== 2. LA POSE (copie conforme du patch) ==========
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

insert into essai_mesures (etape, mesure, valeur)
select '2-pose   ', 'ligne corrigee + plancher      ',
       case when position('delete from _cible_sweep where true;' in d) > 0 and position('''plancher''' in d) > 0
                 and position('delete from _cible_sweep;' in d) = 0 then 'oui' else 'NON' end
  from (select pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure) d) x;
insert into essai_mesures (etape, mesure, valeur)
select '2-pose   ', 'delais propres                 ',
       coalesce((select array_to_string(proconfig, ' | ') from pg_proc where oid = 'public.app_sweep_search_orphans()'::regprocedure), 'aucun');
insert into essai_mesures (etape, mesure, valeur)
select '2-pose   ', 'empreinte apres pose           ',
       md5(replace(pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure), chr(13), ''));

-- =========================== 3. LE TEMOIN POSITIF ==========================
do $positif$
declare v jsonb; t0 timestamptz;
begin
  t0 := clock_timestamp();
  v := public.app_sweep_search_orphans();
  insert into essai_mesures (etape, mesure, valeur) values ('3-positif', 'table pleine -> reponse        ',
    left(v::text, 160) || ' en ' || round(extract(epoch from clock_timestamp() - t0) * 1000) || ' ms'
    || case when (v->>'ok')::boolean then '  -- OK' else '  -- STOP : PAS OK' end);
end
$positif$;

-- =========================== 4. LE TEMOIN DU PLANCHER ======================
do $plancher_essai$
declare v jsonb; n_rap_avant bigint; n_his_avant bigint; n_rap_apres bigint; n_his_apres bigint; n_rech bigint;
begin
  delete from public.app_contact_search_current
   where contact_search_key not in (select contact_search_key from public.app_contact_search_current
                                     order by contact_search_key limit 100);
  select count(*) into n_rech from public.app_contact_search_current;
  select count(*) into n_rap_avant from public.app_rapprochement;
  select count(*) into n_his_avant from public.app_rapprochement_score_history;
  v := public.app_sweep_search_orphans();
  select count(*) into n_rap_apres from public.app_rapprochement;
  select count(*) into n_his_apres from public.app_rapprochement_score_history;
  insert into essai_mesures (etape, mesure, valeur) values
    ('4-plancher', 'recherches restantes           ', n_rech::text),
    ('4-plancher', 'reponse                        ', left(v::text, 120)
       || case when v->>'raison' = 'plancher' and not (v->>'ok')::boolean then '  -- OK (refus)' else '  -- STOP : PAS DE REFUS' end),
    ('4-plancher', 'rapprochements avant / apres   ', n_rap_avant || ' / ' || n_rap_apres
       || case when n_rap_avant = n_rap_apres then '  -- OK (rien efface)' else '  -- STOP : EFFACES' end),
    ('4-plancher', 'historique avant / apres       ', n_his_avant || ' / ' || n_his_apres
       || case when n_his_avant = n_his_apres then '  -- OK (rien efface)' else '  -- STOP : EFFACES' end);
end
$plancher_essai$;

-- =========================== 5. LE RETOUR (copie conforme de l'inverse) ====
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
  v_src := substr(v_src, 1, v_i - 1) || substr(v_src, v_j);
  v_src := replace(v_src, v_a1, v_n1);
  execute v_src;
end
$inverse$;

insert into essai_mesures (etape, mesure, valeur)
select '5-retour ', 'empreinte revenue              ',
       case when md5(replace(pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure), chr(13), ''))
                 = 'be11efc3e8134afa50ba7ca47b0681e8' then 'oui (be11efc3)'
            else 'NON : ' || md5(replace(pg_get_functiondef('public.app_sweep_search_orphans()'::regprocedure), chr(13), '')) end;
insert into essai_mesures (etape, mesure, valeur)
select '5-retour ', 'delais retires                 ',
       coalesce((select array_to_string(proconfig, ' | ') from pg_proc where oid = 'public.app_sweep_search_orphans()'::regprocedure), 'aucun');

-- ================== L ERREUR VOLONTAIRE : tout est annule ===================
do $fin$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id) into v_txt from essai_mesures;
  raise exception '%', 'ESSAI ANNULE -- rien n a ete ecrit : ni la fonction, ni ses delais, ni le menage, ni le journal.'
    || chr(10) || v_txt;
end
$fin$;

rollback;
