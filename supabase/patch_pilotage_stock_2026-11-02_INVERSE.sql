-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE de patch_pilotage_stock_2026-11-02.sql                                       02/11/2026
-- Retire app_pilotage_stock(). Rien d'autre n'avait été touché (lecture seule).
-- Il ne juge que SA part : il vérifie qu'il ne reste aucune trace de la fonction.
-- ⚠ L'onglet Stock du Pilotage affichera « le stock n'a pas pu être lu » ; les autres onglets ne changent pas.
-- ═══════════════════════════════════════════════════════════════════════════
BEGIN;

DO $garde$
BEGIN
    IF to_regprocedure('public.app_pilotage_stock()') IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : app_pilotage_stock() n''est pas la -- rien a retirer.';
    END IF;
END
$garde$;

DROP FUNCTION public.app_pilotage_stock();

DO $preuve$
BEGIN
    IF to_regprocedure('public.app_pilotage_stock()') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la fonction est toujours la. Rien n''est garde.';
    END IF;
END
$preuve$;

COMMIT;
