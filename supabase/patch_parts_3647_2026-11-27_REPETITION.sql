-- REPETITION (lecture seule) -- genere par phase2/checks/parts_3647_generer_patch_2026-11-27.py (son ordre du 27/11)
select
  (select string_agg(cote || ' ' || hektor_user_id || ' ' || nom_au_moment || ' ' || pourcentage || ' ' || origine, ' + ' order by cote, rang) from public.app_affaire_repartition where app_chaine_id = 3647) as parts_3647_attendu_dechaud_entree_gentes_sortie_classeur,
  (select count(*) from public.app_affaire_repartition where app_chaine_id = 3647 and coalesce(origine, '') like 'hektor%') as parts_hektor_sur_3647_attendu_0,
  (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id = 3646) = 'b8b0db64973095395b287a37383825a8' as voisine_3646_intacte,
  (select count(*) from public.app_classeur_realignement_journal where lot = 'parts_3647_2026-11-27') as journal_attendu_2,
  (select count(*) from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_parts_3647_2026-11-27') as mise_de_cote_attendu_2,
  (select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l where l.app_chaine_id = r.app_chaine_id)) as orphelines_attendu_0, (select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) as ventes_reglees_sans_part_attendu_0,
  (select count(*) from public.app_affaire_repartition) as parts_attendu_17970,
  (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition) as empreinte_apres;
