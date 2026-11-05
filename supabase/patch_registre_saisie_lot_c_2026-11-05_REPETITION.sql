-- CONTRÔLE après la pose de patch_registre_saisie_lot_c_2026-11-05.sql — LECTURE SEULE, rien n'est écrit.
-- À coller juste après le patch : chaque ligne doit dire « vert ».
select controle, case when ok then 'vert' else 'ROUGE' end as etat from (values
  ('1. la saisie existe',                    to_regprocedure('public.app_registre_saisir(text,bigint,jsonb)') is not null),
  ('2. rendre, trancher, vu existent',       to_regprocedure('public.app_registre_rendre(text,bigint,text)') is not null
                                             and to_regprocedure('public.app_registre_trancher(text,bigint,text)') is not null
                                             and to_regprocedure('public.app_registre_personne_vue(bigint)') is not null),
  ('3. l''écran (authenticated) peut saisir', has_function_privilege('authenticated', 'public.app_registre_saisir(text,bigint,jsonb)', 'execute')),
  ('4. anon ne peut pas saisir',             not has_function_privilege('anon', 'public.app_registre_saisir(text,bigint,jsonb)', 'execute')),
  ('5. l''écriture brute reste fermée',      not has_function_privilege('authenticated', 'public.app_registre_ecrire_champ(text,bigint,text,text,uuid)', 'execute')),
  ('6. la nuit respecte le statut saisi',    strpos(pg_get_functiondef('public.app_negociateur_registre_maintenir(text[],boolean,integer)'::regprocedure),
                                                    'k.champ = ''actif''') > 0),
  ('7. le journal sait qui',                 exists (select 1 from information_schema.columns where table_schema = 'public'
                                                     and table_name = 'app_registre_journal' and column_name = 'par')),
  ('8. aucune saisie n''a été faite',        not exists (select 1 from public.app_registre_journal where evenement in ('saisie', 'rendu', 'tranche', 'vu'))),
  ('9. le carnet est vide',                  not exists (select 1 from public.app_registre_champ_app))
) as t(controle, ok);
