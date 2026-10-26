-- ============================================================================
-- RETOUR ARRIERE de patch_index_recherche_adresse_2026-10-26.sql
-- Retire les 4 index, et seulement eux. Aucune donnee n'est touchee.
-- ⚠ Comme a la pose : SELECTIONNER UNE LIGNE A LA FOIS (CONCURRENTLY refuse un bloc).
-- ⚠ AVANT : remettre l'interrupteur ADRESSE_INDEXEE a false dans le front (lib/api.ts)
--   et pousser -- sinon la recherche par adresse retomberait a 1,5 s.
-- ============================================================================

DROP INDEX CONCURRENTLY IF EXISTS public.idx_app_dossier_current_search_adresse_trgm;

DROP INDEX CONCURRENTLY IF EXISTS public.idx_app_mandat_register_search_adresse_trgm;

DROP INDEX CONCURRENTLY IF EXISTS public.idx_app_mandat_register_search_text_trgm;

DROP INDEX CONCURRENTLY IF EXISTS public.idx_app_contact_current_search_adresse_trgm;

-- Controle : doit rendre 0.
SELECT count(*) AS index_restants
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN ('idx_app_dossier_current_search_adresse_trgm', 'idx_app_mandat_register_search_adresse_trgm',
                    'idx_app_mandat_register_search_text_trgm', 'idx_app_contact_current_search_adresse_trgm');
