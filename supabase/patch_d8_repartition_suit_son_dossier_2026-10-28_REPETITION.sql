-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ⑧ D8 : la répartition saisie suit sa transaction                                   28/10/2026
-- LECTURE SEULE. À coller APRÈS le patch : chaque ligne doit dire « OK ».
-- ⚠ Elle n'appelle PAS la fonction (la fonction écrit) : le vrai juge est le compte rendu de la nuit
--   (étape « phase2 repartition de commission », ligne « purge des orphelines »), qui doit porter les nouvelles clés.
-- ═══════════════════════════════════════════════════════════════════════════

WITH f AS (SELECT pg_get_functiondef('public.app_repartition_purger_orphelines'::regproc) d)
SELECT n, controle, verdict FROM (
  SELECT 1 n, 'la fonction n''est plus celle d''avant (1e107de3)' controle,
         CASE WHEN md5(d) <> '1e107de38d57b23b36a4f184f348a438' THEN 'OK' ELSE 'ROUGE : patch non posé' END verdict FROM f
  UNION ALL
  SELECT 2, 'elle ramène d''abord les saisies, puis purge les déduites',
         CASE WHEN position('saisies_ramenees' IN d) > 0 AND position('orphelines_en_conflit' IN d) > 0
                   AND position('derivees_supprimees' IN d) > 0 THEN 'OK' ELSE 'ROUGE' END FROM f
  UNION ALL
  SELECT 3, 'seul service_role peut l''appeler (ni anon, ni authenticated)',
         CASE WHEN has_function_privilege('service_role', 'public.app_repartition_purger_orphelines()', 'EXECUTE')
                   AND NOT has_function_privilege('anon', 'public.app_repartition_purger_orphelines()', 'EXECUTE')
                   AND NOT has_function_privilege('authenticated', 'public.app_repartition_purger_orphelines()', 'EXECUTE')
              THEN 'OK' ELSE 'ROUGE' END
  UNION ALL
  SELECT 4, 'aucune saisie n''a été effacée par la pose (non-hektor : 26 lignes le 28/10, 1 orpheline 1001347)',
         CASE WHEN (SELECT count(*) FROM public.app_affaire_repartition WHERE coalesce(origine,'') NOT LIKE 'hektor%') >= 26
              THEN 'OK' ELSE 'ROUGE : des saisies manquent' END
) t ORDER BY n;
