-- ═══════════════════════════════════════════════════════════════════════════
-- INVERSE — RECRUTEMENT R3                                                                   24/11/2026
-- Retire tout ce que patch_recrutement_schema_2026-11-24.sql a posé : les 7 battements, la fonction du
-- bandeau, le schéma « recrutement » (et ses 6 tables), le rôle recrutement_robot.
-- ⛔ GARDE : il REFUSE de tourner si l'app a déjà écrit quelque chose (corrections, « ne plus contacter ») :
--   ces données ne se recollectent pas. Les sauvegarder d'abord, puis décider.
-- Les données MONTÉES par le serveur (fiches, collectes) se reconstruisent, elles : la base locale
-- C:\Hektor\recrutement_donnees\recrutement.sqlite les garde.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $$
BEGIN
  IF to_regclass('recrutement.correction') IS NOT NULL
     AND ((SELECT count(*) FROM recrutement.correction) > 0 OR (SELECT count(*) FROM recrutement.liste_noire) > 0) THEN
    RAISE EXCEPTION 'l''app a deja ecrit des corrections ou des demandes « ne plus contacter » : les sauvegarder avant (rien n''a ete fait)';
  END IF;
END $$;

delete from public.app_worker_registry
 where worker_key in ('recrutement.descente', 'recrutement.collecte', 'recrutement.mise_a_jour', 'recrutement.controle',
                      'recrutement.montee', 'recrutement.sauvegarde', 'recrutement.compte_rendu');
drop function if exists public.rec_etat_collecte();
drop schema if exists recrutement cascade;
drop role if exists recrutement_robot;

-- Le retour arrière ne juge que SA part : il ne reste aucune trace de ce qu'il devait retirer, et ce qu'il
-- ne devait pas toucher est toujours là.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'recrutement') THEN
    RAISE EXCEPTION 'le schema recrutement est toujours la';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'recrutement_robot') THEN
    RAISE EXCEPTION 'le role recrutement_robot est toujours la';
  END IF;
  IF to_regprocedure('public.rec_etat_collecte()') IS NOT NULL THEN
    RAISE EXCEPTION 'la fonction rec_etat_collecte est toujours la';
  END IF;
  IF EXISTS (SELECT 1 FROM public.app_worker_registry WHERE worker_key LIKE 'recrutement.%') THEN
    RAISE EXCEPTION 'des lignes recrutement.* restent dans app_worker_registry';
  END IF;
  IF (SELECT count(*) FROM public.app_worker_registry) = 0 THEN
    RAISE EXCEPTION 'app_worker_registry est VIDE : elle ne devait pas etre touchee au-dela des 7 lignes';
  END IF;
  IF to_regprocedure('public.is_app_admin()') IS NULL THEN
    RAISE EXCEPTION 'is_app_admin a disparu : elle ne devait pas etre touchee';
  END IF;
END $$;

COMMIT;
