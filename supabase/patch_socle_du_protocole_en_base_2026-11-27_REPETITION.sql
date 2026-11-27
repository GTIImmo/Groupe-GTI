-- REPETITION de patch_socle_du_protocole_en_base_2026-11-27 (lecture seule). Apres la copie, attendu : 82 passages,
-- 393 449 verdicts, 65 361 lignes de temoin, 18 motifs, 8 fichiers ; 5 tables avec la RLS ; 0 droit ouvert.
-- La preuve octet pour octet est celle de l'outil : python -u -X utf8 phase2/checks/socle_du_protocole_en_base_2026-11-27.py --verifier
select (select count(*) from public.app_classeur_protocole_passage) as passages,
       (select count(*) from public.app_classeur_protocole_verdict) as verdicts,
       (select count(*) from public.app_classeur_protocole_temoin) as temoins,
       (select count(*) from public.app_classeur_protocole_motif) as motifs,
       (select count(*) from public.app_classeur_protocole_fichier) as fichiers,
       (select max(id) from public.app_classeur_protocole_passage) as dernier_passage,
       (select count(*) from pg_class c join pg_namespace s on s.oid = c.relnamespace where s.nspname = 'public'
         and c.relname like 'app_classeur_protocole_%' and c.relkind = 'r' and c.relrowsecurity) as tables_avec_rls,
       (select count(*) from information_schema.role_table_grants where table_schema = 'public'
         and table_name like 'app_classeur_protocole_%' and grantee in ('PUBLIC', 'anon', 'authenticated')) as droits_ouverts,
       pg_size_pretty((select sum(pg_total_relation_size(c.oid)) from pg_class c join pg_namespace s on s.oid = c.relnamespace
         where s.nspname = 'public' and c.relname like 'app_classeur_protocole_%' and c.relkind = 'r')) as place;
