-- CONTROLE (lecture seule) -- a coller APRES le patch. Chaque ligne doit dire OK.
select 'repartitions' controle, count(*)::text valeur, case when count(*) = 17883 then 'OK' else 'ROUGE' end from app_affaire_repartition
union all select 'mises de cote par ce geste', count(*)::text, case when count(*) = 24 then 'OK' else 'ROUGE' end
  from app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'orphelines_mises_de_cote_essai_avant_v3_2026-11-22'
union all select 'orphelines restantes (la vue)', count(*)::text, case when count(*) = 2 then 'OK' else 'ROUGE' end
  from app_v_repartition_orpheline
union all select 'temoin : ' || 3670 || ' garde son ancien numero', count(*)::text, case when count(*) > 0 then 'OK' else 'ROUGE' end
  from app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'orphelines_mises_de_cote_essai_avant_v3_2026-11-22' and ancien_app_chaine_id = 3670;
