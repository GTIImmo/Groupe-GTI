-- =====================================================================
-- CONTROLE APRES POSE de patch_recherche_libelles_et_rayon_2026-11-06.sql
-- LECTURE SEULE. Chaque ligne doit sortir « OK ».
-- =====================================================================
with c as (
  select 1 n, 'la table des rayons existe, sous RLS' quoi,
         exists (select 1 from pg_class where relname='app_search_rayon' and relrowsecurity) ok
  union all select 2, 'authenticated lit les rayons mais ne peut PAS les ecrire',
         has_table_privilege('authenticated','public.app_search_rayon','SELECT')
     and not has_table_privilege('authenticated','public.app_search_rayon','INSERT')
     and not has_table_privilege('authenticated','public.app_search_rayon','UPDATE')
     and not has_table_privilege('anon','public.app_search_rayon','SELECT')
  union all select 3, 'les deux aides sont fermees a anon et authenticated',
         not has_function_privilege('authenticated','public.app_search_types_libelles(jsonb,jsonb,jsonb)','EXECUTE')
     and not has_function_privilege('anon','public.app_search_types_libelles(jsonb,jsonb,jsonb)','EXECUTE')
     and not has_function_privilege('authenticated','public.app_search_rayon_km(jsonb)','EXECUTE')
     and not has_function_privilege('anon','public.app_search_rayon_km(jsonb)','EXECUTE')
  union all select 4, 'le moteur lit le rayon',
         pg_get_functiondef('public.app_match_score_v2(jsonb,jsonb)'::regprocedure) ~ 'app_search_rayon_km'
  union all select 5, 'les deux portes ecrivent { code : libelle }',
         pg_get_functiondef('public.app_edit_search_optimistic(text,jsonb,integer)'::regprocedure) ~ 'app_search_types_libelles'
     and pg_get_functiondef('public.app_espace_edit_search_optimistic(text,jsonb,integer)'::regprocedure) ~ 'app_search_types_libelles'
     and pg_get_functiondef('public.app_edit_search_optimistic(text,jsonb,integer)'::regprocedure) !~ 'jsonb_object_agg\(t,t\)'
     and pg_get_functiondef('public.app_espace_edit_search_optimistic(text,jsonb,integer)'::regprocedure) !~ 'jsonb_object_agg\(t,t\)'
  union all select 6, 'la porte de l''app range le rayon AVANT le recalcul',
         position('insert into public.app_search_rayon' in pg_get_functiondef('public.app_edit_search_optimistic(text,jsonb,integer)'::regprocedure))
       < position('perform public.app_refresh_rapprochements_for_search' in pg_get_functiondef('public.app_edit_search_optimistic(text,jsonb,integer)'::regprocedure))
  union all select 7, 'les droits des portes n''ont pas bouge',
         has_function_privilege('authenticated','public.app_edit_search_optimistic(text,jsonb,integer)','EXECUTE')
     and not has_function_privilege('authenticated','public.app_espace_edit_search_optimistic(text,jsonb,integer)','EXECUTE')
     and not has_function_privilege('authenticated','public.app_match_score_v2(jsonb,jsonb)','EXECUTE')
  union all select 8, 'plus AUCUNE recherche aux types en chiffres seuls',
         not exists (select 1 from public.app_contact_search_current
                     where jsonb_typeof(types_json)='object' and types_json <> '{}'::jsonb
                       and not exists (select 1 from jsonb_each_text(types_json) e where e.value !~ '^[0-9]*$'))
  union all select 9, 'la sauvegarde datee porte les recherches reparees',
         (select count(*) from public.app_contact_search_types_avant_libelles_20261106) >= 1
  union all select 10, 'l''aide des libelles : sans rien -> Maison / Appartement',
         public.app_search_types_libelles('["1","2"]', null, null) = '{"1":"Maison","2":"Appartement"}'::jsonb
  union all select 11, 'sans rayon enregistre -> 15 km ; un rayon pose par la charge est lu',
         public.app_search_rayon_km('{"contact_search_key":"__aucune__"}') = 15
     and public.app_search_rayon_km('{"rayon_km":"30"}') = 30
     and public.app_search_rayon_km('{"rayon_km":"0"}') = 0
)
select n, quoi, case when ok then 'OK' else '⛔ ECHEC' end as verdict from c order by n;
