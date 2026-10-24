-- ============================================================================
-- INVERSE -- retirer l'index de patch_photos_index_derniere_date_2026-10-24.sql
-- ============================================================================
-- Ce retour arriere ne juge QUE sa part (lecon 31) : il retire l'index, et il
-- verifie qu'il ne reste aucune trace de l'index ET que la fonction n'a pas
-- bouge (le patch ne l'a jamais touchee).
--
-- ⚠ Apres ce retour, la fonction redevient LENTE (3,5 s et plus) : c'est l'etat
--   du 20 au 24/10. Les adresses photos de nuit risquent de nouveau le 57014.
--
-- DEUX COLLAGES SEPARES : `drop index concurrently` refuse de tourner dans une
-- transaction.
-- ============================================================================


-- ① LE RETRAIT -- coller et lancer CETTE LIGNE SEULE
drop index concurrently if exists public.app_console_photo_derniere_bouge_idx;


-- ② LE CONTROLE -- coller et lancer SEULS (lecture seule). Tout doit dire OK.
select 'index retire' as controle,
       case when to_regclass('public.app_console_photo_derniere_bouge_idx') is null
            then 'OK' else 'NON -- il existe encore' end as verdict
union all
select 'aucun autre index sur cette formule',
       case when count(*) = 0 then 'OK' else 'NON -- ' || string_agg(indexname, ', ') end
  from pg_indexes
 where schemaname = 'public' and tablename = 'app_console_photo'
   and indexdef ilike '%greatest(derives_generes_le, absent_depuis)%'
union all
select 'fonction intacte',
       case when md5(replace(pg_get_functiondef('public.app_photos_remplir_adresses_app(integer,boolean)'::regprocedure), chr(13), ''))
                 = 'ec8066616381cdb90df38ec561f1441f'
            then 'OK (ec806661)' else 'A VERIFIER -- la fonction a change, mais PAS par ce patch' end;
