-- patch_a2_vague_2026-11-25_INVERSE -- le retour arriere d'A2 (begin ... commit). La sauvegarde app_affaire_repartition_avant_a2vague_20261125 reste.
begin;

-- ─── LE RETOUR ARRIERE : les parts du lot retirees, les mises de cote remises EN PLACE, le journal du lot retire ─────
do $$
declare n int;
begin
  if to_regclass('public.app_affaire_repartition_avant_a2vague_20261125') is null then raise exception '⛔ inverse : la sauvegarde app_affaire_repartition_avant_a2vague_20261125 est absente'; end if;
  select count(*) into n from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_a2_vague_2026-11-25';
  if n <> 143 then raise exception '⛔ inverse : % mise(s) de cote du lot au lieu de 143', n; end if;
end $$;
delete from public.app_affaire_repartition where ecrit_par like 'a2_vague_2026-11-25:%';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select ancien_app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_a2_vague_2026-11-25';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_a2_vague_2026-11-25';
delete from public.app_classeur_realignement_journal where lot = 'a2_vague_2026-11-25';
do $$
declare n int;
begin
  -- la table est revenue EXACTEMENT a la sauvegarde, dans les deux sens
  select count(*) into n from (
    (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_a2vague_20261125
     except all
     select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition)
    union all
    (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition
     except all
     select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_a2vague_20261125)) z;
  if n <> 0 then raise exception '⛔ inverse : % part(s) differente(s) de la sauvegarde', n; end if;
  raise notice '✅ inverse : la repartition est revenue a la sauvegarde, la mise de cote et le journal du lot sont vides';
end $$;

commit;
