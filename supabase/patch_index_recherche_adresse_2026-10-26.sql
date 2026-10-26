-- ============================================================================
-- POINT 4 (navigation) -- RENDRE L'ADRESSE CHERCHABLE           26/10/2026
-- notice/AUDIT_NAVIGATION_APRES_ACTION_2026-10-23.md §20.3 et §20.4
--
-- POURQUOI. L'adresse est chez nous (10 787 annonces en cours, 24 347 mandats du
-- registre dont 23 584 biens vendus ou archives, 32 685 contacts), mais AUCUNE colonne
-- d'adresse n'a d'index : la chercher relit toute la table (1 515 ms mesure sur les
-- annonces en cours, au lieu de 80 ms). Le registre n'a meme aucun index texte (196 ms).
--
-- CE QUE CA FAIT. 4 index « trigramme » (le meme genre que les 37 qui existent deja sur
-- les annonces), et RIEN D'AUTRE : aucune ligne n'est ecrite, modifiee ni effacee.
--
-- CE QUE CA COUTE. Un peu de travail en plus quand ces lignes sont ECRITES. Mesure des
-- 8 dernieres nuits : 2 a 52 annonces, ~742 lignes du registre, ~4 000 contacts par nuit
-- -- des volumes faibles. Disque : quelques dizaines de Mo.
--
-- ⚠ COMMENT LE COLLER. « CONCURRENTLY » construit l'index SANS BLOQUER l'app, mais
--   refuse de tourner dans un bloc de plusieurs instructions. Dans l'editeur SQL de
--   Supabase : SELECTIONNER UNE LIGNE A LA FOIS et l'executer (4 executions).
--   ⛔ Pas pendant le run de nuit (04:00 -> ~06:15). En journee, c'est fait pour.
--   Une ligne deja posee se relance sans dommage (IF NOT EXISTS).
--
-- RETOUR ARRIERE : patch_index_recherche_adresse_2026-10-26_INVERSE.sql
-- CONTROLE       : patch_index_recherche_adresse_2026-10-26_REPETITION.sql
-- ============================================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_app_dossier_current_search_adresse_trgm ON public.app_dossier_current USING gin (adresse_detail gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_app_mandat_register_search_adresse_trgm ON public.app_mandat_register_current USING gin (adresse_detail gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_app_mandat_register_search_text_trgm ON public.app_mandat_register_current USING gin (search_text gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_app_contact_current_search_adresse_trgm ON public.app_contact_current USING gin (adresse gin_trgm_ops);
