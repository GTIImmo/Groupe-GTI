-- INVERSE -- genere par phase2/checks/parts_3647_generer_patch_2026-11-27.py (son ordre du 27/11)

begin;

-- ─── L'INVERSE : les parts du classeur retirees de 3647, les deux suppositions remises, le journal du lot retire ───────
delete from public.app_affaire_repartition where app_chaine_id = 3647 and ecrit_par = 'classeur:9Q0FHAKK' and origine = 'classeur_reconstitue';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select ancien_app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_parts_3647_2026-11-27';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_parts_3647_2026-11-27';
delete from public.app_classeur_realignement_journal where lot = 'parts_3647_2026-11-27';
do $$
begin
  if (select count(*) from (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
        ecrit_le, ecrit_par from public.app_affaire_repartition where app_chaine_id = 3647
      except all select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le,
        ecrit_par from public.app_affaire_repartition_avant_parts3647_20261127) z) <> 0
     or (select count(*) from (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
        ecrit_le, ecrit_par from public.app_affaire_repartition_avant_parts3647_20261127
      except all select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le,
        ecrit_par from public.app_affaire_repartition where app_chaine_id = 3647) z) <> 0 then
    raise exception '⛔ inverse : 3647 n''est pas revenue a la sauvegarde'; end if;
  raise notice '✅ inverse : 3647 est revenue aux deux suppositions, la mise de cote et le journal du lot sont vides';
end $$;

commit;
