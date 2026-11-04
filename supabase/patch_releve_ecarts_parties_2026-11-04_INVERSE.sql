-- ═══════════════════════════════════════════════════════════════════════════
-- INVERSE — le relevé horaire des écarts de la table des parties                         04/11/2026
-- Retire la tâche, la fonction et la table. La vue app_v_affaire_partie_ecarts n'a jamais été touchée.
-- ⚠ À faire AVEC le retour de la sonde : "table": "app_v_affaire_partie_ecarts" dans monitoring/check_gti_health.py,
--   sinon la sentinelle lirait une table absente (elle passerait « illisible », pas « verte »).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

select cron.unschedule(jobid) from cron.job where jobname = 'affaire-partie-releve-ecarts';
drop function if exists public.app_affaire_partie_relever_ecarts();
drop table if exists public.app_affaire_partie_ecart_releve;

-- Le retour arrière ne juge que SA part : il ne reste aucune trace de ce qu'il devait retirer.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'affaire-partie-releve-ecarts') THEN
    RAISE EXCEPTION 'la tâche affaire-partie-releve-ecarts est toujours là';
  END IF;
  IF to_regprocedure('public.app_affaire_partie_relever_ecarts()') IS NOT NULL THEN
    RAISE EXCEPTION 'la fonction app_affaire_partie_relever_ecarts est toujours là';
  END IF;
  IF to_regclass('public.app_affaire_partie_ecart_releve') IS NOT NULL THEN
    RAISE EXCEPTION 'la table app_affaire_partie_ecart_releve est toujours là';
  END IF;
  IF to_regclass('public.app_v_affaire_partie_ecarts') IS NULL THEN
    RAISE EXCEPTION 'la vue app_v_affaire_partie_ecarts a disparu : elle ne devait pas être touchée';
  END IF;
END $$;

COMMIT;
