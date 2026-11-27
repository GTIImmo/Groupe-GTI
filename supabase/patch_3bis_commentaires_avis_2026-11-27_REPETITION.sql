-- REPETITION de patch_3bis_commentaires_avis_2026-11-27 (lecture seule) -- attendu : 47 notes neuves, 78 paragraphes, 27 lignes d'avis, 4571 notes en tout
select (select count(*) from public.app_affaire_note where ecrit_par = 'classeur:3bis:2026-11-27') notes_neuves,
       (select count(*) from public.app_affaire_note where texte like '%[classeur G, relu le 26/11/2026]%') paragraphes,
       (select count(*) from public.app_classeur_avis where ecrit_par = 'classeur:3bis:2026-11-27') avis,
       (select count(*) from public.app_affaire_note) notes_en_tout,
       (select count(*) from public.app_affaire_note a join public.app_affaire_note_avant_3bis_20261127 s using (app_affaire_id)
         where left(a.texte, length(s.texte)) <> s.texte) textes_d_avant_abimes;
