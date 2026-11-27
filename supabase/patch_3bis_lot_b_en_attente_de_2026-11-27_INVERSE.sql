-- INVERSE de patch_3bis_lot_b_en_attente_de_2026-11-27 : retire les notes neuves du lot, rend les notes et les avis d'avant a l'octet (sauvegardes datees).
-- Il ne juge que SA part (lecon 31).

begin;
delete from public.app_affaire_note where ecrit_par = 'classeur:3bisB:2026-11-27';
update public.app_affaire_note a set texte = s.texte from public.app_affaire_note_avant_3bisB_20261127 s where s.app_affaire_id = a.app_affaire_id;
delete from public.app_classeur_avis where ecrit_par = 'classeur:3bisB:2026-11-27' and id_unique not in (select id_unique from public.app_classeur_avis_avant_3bisB_20261127);
update public.app_classeur_avis a set avis_a_envoyer = s.avis_a_envoyer, commentaire_avis = s.commentaire_avis,
       avis_envoye = s.avis_envoye, ecrit_par = s.ecrit_par, ecrit_le = s.ecrit_le
  from public.app_classeur_avis_avant_3bisB_20261127 s where s.id_unique = a.id_unique;
do $$ declare n int; begin
  select count(*) into n from public.app_affaire_note where ecrit_par = 'classeur:3bisB:2026-11-27' or texte like '%[classeur F, suivi en cours au 26/11/2026]%';
  if n <> 0 then raise exception '⛔ inverse : % trace(s) du lot restent', n; end if;
  select count(*) into n from public.app_classeur_avis where ecrit_par = 'classeur:3bisB:2026-11-27';
  if n <> 0 then raise exception '⛔ inverse : % avis marques restent', n; end if;
  raise notice '✅ inverse : le lot 3 bis B est retire, les sauvegardes restent (elles se gardent)';
end $$;
commit;
