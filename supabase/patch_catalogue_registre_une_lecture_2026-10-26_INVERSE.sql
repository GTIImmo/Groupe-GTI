-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE de patch_catalogue_registre_une_lecture_2026-10-26.sql                       26/10/2026
-- Il ne retire QUE sa part : la vue app_filter_catalog_registre, et la règle du registre revient à
-- is_app_manager_or_admin(). L'écran retombe tout seul sur l'ancienne lecture (25 pages) : rien d'autre à faire.
-- ⛔ RIEN chez Hektor.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
SET LOCAL lock_timeout = '5s';

drop view if exists public.app_filter_catalog_registre;

alter policy app_mandat_register_current_select_active_users on public.app_mandat_register_current
    using (public.is_app_manager_or_admin());

COMMIT;

SELECT 1 AS "#", 'la vue est retiree' AS controle,
       CASE WHEN to_regclass('public.app_filter_catalog_registre') IS NULL THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'la regle du registre est revenue a is_app_manager_or_admin()',
       (SELECT CASE WHEN pg_get_expr(polqual, polrelid) = 'is_app_manager_or_admin()' THEN 'OK' ELSE '⛔ ECHEC (' || pg_get_expr(polqual, polrelid) || ')' END
          FROM pg_policy WHERE polname = 'app_mandat_register_current_select_active_users' AND polrelid = 'public.app_mandat_register_current'::regclass)
UNION ALL SELECT 3, 'le registre est intact (lignes)',
       (SELECT CASE WHEN count(*) > 20000 THEN 'OK (' || count(*) || ')' ELSE '⛔ ECHEC (' || count(*) || ')' END FROM public.app_mandat_register_current)
ORDER BY 1;
