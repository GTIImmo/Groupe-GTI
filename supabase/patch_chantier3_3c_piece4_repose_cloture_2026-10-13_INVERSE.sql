-- =====================================================================
-- RETOUR ARRIERE de la piece 4 de 3c -- 2026-10-13
--
-- Supprime la fonction de re-pose. AUCUN SCHEMA TOUCHE : la colonne
-- `mandat_date_cloture_app` reste, avec ce qu'elle porte.
--
-- ⚠ LES DEUX AUTRES MORCEAUX SE DEFONT DANS LE DEPOT, PAS ICI :
--   1. l'etape du run      -> retirer le bloc « phase2 re-pose cloture mandat »
--                             de run_full_pipeline.ps1 (une etape, non bloquante)
--   2. le chemin immediat  -> retirer l'appel `reposer_cloture_mandat(...)` de
--                             phase2/sync/push_single_annonce_to_supabase.py
--                             (additif et enveloppe : son retrait ne casse rien)
--   `git revert` du commit les emporte tous les deux d'un coup.
--
-- ⚠ CE QUI REVIENT ALORS : la date de cloture repartira a chaque reconstruction du
--   registre -- la nuit, et ~1 min apres un geste sur l'annonce. C'est l'etat
--   d'avant le 13/10, pas une regression nouvelle.
-- =====================================================================

BEGIN;

DO $retour$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = 'public' AND p.proname = 'app_reposer_cloture_mandat_app'
  ) THEN
    RAISE EXCEPTION 'STOP : la fonction n''existe pas -- rien a defaire';
  END IF;
END $retour$;

drop function if exists public.app_reposer_cloture_mandat_app(text, int);

-- L'enregistrement du battement de coeur, retire lui aussi : sans l'etape du run,
-- la cle n'aurait plus personne pour la battre et le moniteur crierait a tort.
-- ⚠ On ne retire QUE la notre. Les 9 autres cles du run qui n'ont aucune ligne sont
--   un sujet du chantier ④, pas d'ici.
delete from public.app_worker_registry
 where worker_key = 'phase2.repose_cloture_mandat';

DO $retour$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = 'public' AND p.proname = 'app_reposer_cloture_mandat_app'
  ) THEN
    RAISE EXCEPTION 'STOP : la fonction est toujours la apres le drop';
  END IF;
  RAISE NOTICE 'OK : la re-pose est retiree. La colonne et ses valeurs sont intactes.';
END $retour$;

notify pgrst, 'reload schema';

COMMIT;
