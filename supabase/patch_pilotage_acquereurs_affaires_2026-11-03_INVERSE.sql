-- Retour arrière de patch_pilotage_acquereurs_affaires_2026-11-03.sql : retire les deux lectures, rien d'autre.
-- L'écran garde un repli : sans ces fonctions, ses blocs disent « n'a pas pu être lu ».
drop function if exists public.app_pilotage_acquereurs(integer);
drop function if exists public.app_pilotage_affaires_plus(integer);
select count(*) as reste from pg_proc where proname in ('app_pilotage_acquereurs', 'app_pilotage_affaires_plus');  -- doit valoir 0
