-- CONTROLE DU GEL V3 (lecture seule) -- a coller APRES le patch. Chaque ligne doit dire OK.
select 'liens' controle, count(*)::text valeur, case when count(*) = 12805 then 'OK' else 'ROUGE' end from app_classeur_lien
union all select 'poses par la V3', count(*)::text, case when count(*) = 14 then 'OK' else 'ROUGE' end from app_classeur_lien where gele_par = 'v3_ou_ca_tombe_2026-11-22'
union all select 'tenues par deux lignes', count(*)::text, case when count(*) = 0 then 'OK' else 'ROUGE' end
  from (select app_affaire_id from app_classeur_lien group by 1 having count(distinct id_unique) > 1) x
union all select 'deux liens pour un role', count(*)::text, case when count(*) = 0 then 'OK' else 'ROUGE' end
  from (select id_unique, role from app_classeur_lien group by 1, 2 having count(*) > 1) x
union all select 'sauvegarde', count(*)::text, case when count(*) = 12820 then 'OK' else 'ROUGE' end from app_classeur_lien_avant_v3_20261122
union all select 'temoin positif : ' || 'c08ff7cb' || ' tient ' || 3678, count(*)::text, case when count(*) = 1 then 'OK' else 'ROUGE' end
  from app_classeur_lien where id_unique = 'c08ff7cb' and app_affaire_id = 3678
union all select 'temoin positif : ' || '721e650c' || ' ne tient plus ' || 3678, count(*)::text, case when count(*) = 0 then 'OK' else 'ROUGE' end
  from app_classeur_lien where id_unique = '721e650c' and app_affaire_id = 3678;
