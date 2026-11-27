-- REPETITION (lecture seule) -- genere par phase2/checks/remede_8016_generer_patch_2026-11-25.py (son mot du 25/11)
select
  (select string_agg(cote || ' ' || nom_au_moment || ' ' || pourcentage || ' ' || origine, ' + ' order by cote)
     from public.app_affaire_repartition where app_chaine_id = 8016) as parts_8016_attendu_romera_50_50_classeur,
  (select count(*) from public.app_classeur_realignement_journal where lot = 'remede_8016_2026-11-25') as journal_attendu_3,
  (select count(*) from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_remede_8016_2026-11-25') as mise_de_cote_attendu_1,
  (select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l where l.app_chaine_id = r.app_chaine_id)) as orphelines_attendu_0, (select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) as ventes_reglees_sans_part_attendu_0,
  (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition) as empreinte_apres;
