-- Retour arrière de patch_registre_negociateurs_nuit_total_2026-11-04.sql : retire la version à 3 paramètres, puis
-- RECOLLER la section 4 de patch_registre_negociateurs_nuit_2026-11-04.sql (la version à 2 paramètres) et ses droits.
-- La contrainte garde 'disparitions_nombreuses' (une ligne déjà écrite reste lisible).
drop function if exists public.app_negociateur_registre_maintenir(text[], boolean, integer);
