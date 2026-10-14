-- =============================================================================
--  RETOUR ARRIERE du patch « registre du menage des orphelins »   14/10/2026
-- =============================================================================
--  Il retire la ligne de registre posee par
--  patch_registre_menage_orphelins_2026-10-14.sql, et RIEN D'AUTRE.
--
--  ⚠ A N'UTILISER QUE SI L'ETAPE DU RUN EST RETIREE EN MEME TEMPS. Une etape
--    qui tourne SANS sa ligne de registre est pire que pas d'etape du tout :
--    son battement part dans le vide et compte pour un succes (defaut 4j).
-- =============================================================================

DO $$
DECLARE
  v_supprimees int;
BEGIN
  DELETE FROM public.app_worker_registry
   WHERE worker_key = 'phase2.menage_orphelins_recherche';
  GET DIAGNOSTICS v_supprimees = ROW_COUNT;

  IF v_supprimees = 0 THEN
    RAISE NOTICE 'RIEN A FAIRE : la cle n''existait pas.';
  ELSE
    RAISE NOTICE 'RETIREE : % ligne(s).', v_supprimees;
  END IF;
END $$;

-- Controle : la ligne ne doit plus exister (0 ligne attendue).
SELECT worker_key
  FROM public.app_worker_registry
 WHERE worker_key = 'phase2.menage_orphelins_recherche';
