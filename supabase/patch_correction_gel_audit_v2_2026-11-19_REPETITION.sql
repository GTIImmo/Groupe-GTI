-- REPETITION de patch_correction_gel_audit_v2_2026-11-19.sql -- LECTURE SEULE, a jouer APRES le patch.
-- Chaque compte a sa valeur attendue a cote. Une lecture qui echoue n'est JAMAIS un vert.
select json_build_object(
  'liens', (select count(*) from app_classeur_lien), 'attendu', 12820,
  'poses_par_le_patch', (select count(*) from app_classeur_lien where gele_par = 'audit_independant_v2_2026-11-19'), 'attendu_poses', 78,
  'preuves_des_poses', (select json_object_agg(p, c) from (select preuves p, count(*) c from app_classeur_lien
                         where gele_par = 'audit_independant_v2_2026-11-19' group by 1) x),
  'transactions_prises_deux_fois', (select count(*) from (select app_affaire_id from app_classeur_lien
                                     group by 1 having count(distinct id_unique) > 1) x), 'attendu_deux_fois', 0,
  'lignes_sans_lien', (select count(*) from app_v_classeur_ligne_sans_lien), 'attendu_sans_lien', 71,
  'liens_casses_disparue', (select count(*) from app_v_classeur_lien_casse where gravite = 'DISPARUE'), 'attendu_disparue', 0,
  'sauvegarde', (select count(*) from app_classeur_lien_avant_audit_v2_20261119), 'attendu_sauvegarde', 12787,
  -- ➡ CORRECTION 3 : ce qui reste a ENCHAINER -- les valeurs posees par NOUS sur les 36
  --   transactions de Hektor que le patch detache d'une ligne (les copies de C5 se retirent entieres)
  --   ⓘ MESURE DU 19/11 AVANT LE PATCH (le patch ne les touche pas) : 10 transactions portent une
  --     valeur, 15 portent une note du Sheet. Le geste suivant doit les faire DESCENDRE.
  'attendu_traces_avant_nettoyage', 10, 'attendu_notes_avant_nettoyage', 15,
  'traces_sur_transactions_detachees', (select count(*) from app_affaire_ledger
     where app_affaire_id in (998, 1000, 1876, 3648, 3650, 4385, 4496, 4747, 6341, 6554, 6555, 7780, 8321, 8322, 10730, 11138, 11958, 12952, 12953, 16377, 16378, 17427, 17430, 19277, 23050, 23995, 24291, 26395, 26397, 27195, 27196, 28558, 28930, 28967, 30712, 1001361)
       and (honoraires_entree_app is not null or honoraires_sortie_app is not null
            or charge_commission_app is not null or date_annulation_app is not null
            or motif_annulation_app is not null or numero_facture_app is not null
            or vente_reglee_app is not null)),
  'notes_classeur_sur_transactions_detachees', (select count(*) from app_affaire_note
     where app_affaire_id in (998, 1000, 1876, 3648, 3650, 4385, 4496, 4747, 6341, 6554, 6555, 7780, 8321, 8322, 10730, 11138, 11958, 12952, 12953, 16377, 16378, 17427, 17430, 19277, 23050, 23995, 24291, 26395, 26397, 27195, 27196, 28558, 28930, 28967, 30712, 1001361) and origine like 'classeur%')
) r;
