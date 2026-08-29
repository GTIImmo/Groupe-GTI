-- =====================================================================
-- C.19 -- FERMER anon SUR LES DEUX RPC DE LA JOURNEE
-- Date : 2026-08-29
--
-- TROUVE EN VERIFIANT MON PROPRE TRAVAIL pendant l'audit demande par Frederic.
--
-- Les deux RPC posees ce jour-la (app_edit_affaire_optimistic et
-- app_geste_affaire_optimistic) etaient APPELABLES SANS ETRE CONNECTE.
--
-- POURQUOI, ET C'EST LE PIEGE A RETENIR. J'avais bien ecrit
--     REVOKE ALL ON FUNCTION ... FROM PUBLIC;
-- mais cela NE SUFFIT PAS : Supabase accorde EXECUTE a `anon` et `authenticated`
-- par PRIVILEGE PAR DEFAUT sur toute fonction neuve du schema public. Retirer le
-- pseudo-role PUBLIC ne retire pas ces deux roles-la, qui sont des GRANT explicites.
--
-- Le garde-fou interne tenait -- is_app_admin() leve not_allowed, verifie en direct --
-- donc rien n'etait exploitable. Mais une fonction qui ne doit pas etre appelable ne
-- doit pas l'etre du tout. C'est exactement la dette mesuree par la tache 0.7 le
-- 24/08 (81 fonctions ouvertes a la cle publique) : j'en ajoutais deux sans le voir.
--
-- REGLE A APPLIQUER DESORMAIS a toute RPC neuve reservee aux utilisateurs connectes :
--     REVOKE EXECUTE ... FROM PUBLIC;
--     REVOKE EXECUTE ... FROM anon;          <-- celui qu'on oublie
--     GRANT  EXECUTE ... TO authenticated, service_role;
--
-- VERIFIE APRES APPLICATION : les deux rendent « authenticated, postgres,
-- service_role ». Applique en production via la migration `c19_fermer_anon_sur_mes_rpc`.
-- =====================================================================

REVOKE EXECUTE ON FUNCTION public.app_edit_affaire_optimistic(bigint, jsonb) FROM anon;
REVOKE EXECUTE ON FUNCTION public.app_geste_affaire_optimistic(bigint, text, integer) FROM anon;

GRANT EXECUTE ON FUNCTION public.app_edit_affaire_optimistic(bigint, jsonb) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.app_geste_affaire_optimistic(bigint, text, integer) TO authenticated, service_role;
