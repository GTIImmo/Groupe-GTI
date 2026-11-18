-- REPETITION de patch_correction_gel_audit_independant_2026-11-18.sql -- lecture seule, a jouer APRES le patch.
select json_build_object(
  'liens', (select count(*) from app_classeur_lien),
  'attendu', 12841,
  'poses_par_l_audit', (select count(*) from app_classeur_lien where gele_par = 'audit_independant_2026-11-18'),
  'attendu_poses', 109,
  'transactions_prises_deux_fois', (select count(*) from (select app_affaire_id from app_classeur_lien
                                     group by 1 having count(distinct id_unique) > 1) x),
  'lignes_sans_lien', (select count(*) from app_v_classeur_ligne_sans_lien),
  'attendu_sans_lien', 60,
  'liens_casses_disparue', (select count(*) from app_v_classeur_lien_casse where gravite = 'DISPARUE'),
  'sauvegarde', (select count(*) from app_classeur_lien_avant_audit_independant_20261118)
) r;
