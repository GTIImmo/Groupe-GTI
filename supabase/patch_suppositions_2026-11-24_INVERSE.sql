-- patch_suppositions_2026-11-24 -- genere par phase2/checks/repartition_4_5_generer_patchs_2026-11-24.py (« rien ne s'ecrit sans mon accord sur le patch »)
-- Retour arriere : patch_suppositions_2026-11-24_INVERSE.sql . Controle : patch_suppositions_2026-11-24_REPETITION.sql

begin;

-- ─── LE RETOUR : retirer ce que le lot a pose, reposer chaque ancienne part depuis la mise de cote, a l'identique ─────────
do $$
declare n int;
begin
  select count(*) into n from public.app_affaire_repartition r join public.app_classeur_realignement_journal j
      on j.lot = 'suppositions_2026-11-24' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')'
   where r.origine = 'classeur_reconstitue' and r.ecrit_par = 'classeur:' || j.ligne_origine;
  if n <> 12 then raise exception '⛔ garde du retour : % part(s) du lot retrouvee(s) sur 12 (une saisie est passee ?)', n; end if;
end $$;
delete from public.app_affaire_repartition r using public.app_classeur_realignement_journal j
 where j.lot = 'suppositions_2026-11-24' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')'
   and r.origine = 'classeur_reconstitue' and r.ecrit_par = 'classeur:' || j.ligne_origine;
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select m.app_chaine_id, m.app_dossier_id, m.cote, m.rang, m.hektor_user_id, m.nom_au_moment, m.pourcentage, m.origine,
       m.ecrit_le, m.ecrit_par
  from public.app_affaire_repartition_mise_de_cote m where m.mise_de_cote_par = 'patch_suppositions_2026-11-24';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_suppositions_2026-11-24';
do $$
declare n int; e text;
begin
  select count(*) into n from (
    (select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984)
     except select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_suppositions_20261124)
    union all
    (select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_suppositions_20261124
     except select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984))) d;
  if n <> 0 then raise exception '⛔ controle du retour : % part(s) differente(s) de la sauvegarde', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984));
  if e <> '1c741e0f96bb4a55c672d4e0cd37407d' then raise exception '⛔ controle du retour : empreinte % au lieu de 1c741e0f96bb4a55c672d4e0cd37407d (celle d''AVANT)', e; end if;
end $$;

commit;
