-- REPETITION de patch_3bis_lot_c_repartitions_2026-11-27 (lecture seule) -- attendu : 419 parts sur 203 chaines, aucune au-dela de 100 %
select (select count(*) from public.app_affaire_repartition where ecrit_par = 'classeur:3bisC:2026-11-27') parts,
       (select count(distinct app_chaine_id) from public.app_affaire_repartition where ecrit_par = 'classeur:3bisC:2026-11-27') chaines,
       (select count(*) from (select app_chaine_id from public.app_affaire_repartition group by 1
         having sum(pourcentage) > 100.001) x) chaines_au_dela_de_100;
