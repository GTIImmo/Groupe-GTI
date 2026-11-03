-- Retour arrière de patch_pilotage_limites_2026-11-03.sql : remet les deux fonctions de la 1re pose.
drop function if exists public.app_pilotage_acquereurs(integer, text);
-- puis coller patch_pilotage_acquereurs_affaires_2026-11-03.sql (il recrée app_pilotage_acquereurs(integer)
-- et remplace app_pilotage_affaires_plus par sa version sans les compromis en cours).
