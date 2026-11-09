-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE — patch_catalogue_notaires_numeros_2026-11-09.sql
-- ═══════════════════════════════════════════════════════════════════════════
-- Retire la fonction public.app_catalogue_notaires_ids() et l'index idx_app_contact_current_relation_roles_gin. L'écran retombe tout seul sur l'ancienne lecture
-- (parcours des contacts) : rien d'autre à faire.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
SET LOCAL lock_timeout = '3s';
DROP FUNCTION IF EXISTS public.app_catalogue_notaires_ids();
DROP INDEX IF EXISTS public.idx_app_contact_current_relation_roles_gin;

DO $verif$
BEGIN
  IF to_regprocedure('public.app_catalogue_notaires_ids()') IS NOT NULL OR to_regclass('public.idx_app_contact_current_relation_roles_gin') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRET : il reste une trace du patch. Annule.';
  END IF;
END
$verif$;

COMMIT;
