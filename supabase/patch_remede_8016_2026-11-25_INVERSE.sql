-- INVERSE -- genere par phase2/checks/remede_8016_generer_patch_2026-11-25.py (son mot du 25/11)

begin;

-- ─── L'INVERSE : les parts du classeur retirees de 8016, la part de la nuit remise, le journal du lot retire ─────────
delete from public.app_affaire_repartition where app_chaine_id = 8016 and ecrit_par = 'remede_8016_2026-11-25:SXJDHXKF';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select ancien_app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_remede_8016_2026-11-25';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_remede_8016_2026-11-25';
delete from public.app_classeur_realignement_journal where lot = 'remede_8016_2026-11-25';
do $$
begin
  if (select count(*) from (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
        ecrit_le, ecrit_par from public.app_affaire_repartition where app_chaine_id = 8016
      except all select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le,
        ecrit_par from public.app_affaire_repartition_avant_remede8016_20261125) z) <> 0 or (select count(*) from public.app_affaire_repartition where app_chaine_id = 8016) <> 1 then
    raise exception '⛔ inverse : 8016 n''est pas revenue a la sauvegarde'; end if;
  raise notice '✅ inverse : 8016 est revenue a la part de la nuit, la mise de cote et le journal du lot sont vides';
end $$;

commit;
