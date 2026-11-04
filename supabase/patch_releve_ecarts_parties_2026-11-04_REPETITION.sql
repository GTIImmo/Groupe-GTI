-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — le relevé horaire des écarts de la table des parties                      04/11/2026
-- Lecture seule. À jouer juste après la pose, puis après le premier passage de la tâche (:40).
-- ═══════════════════════════════════════════════════════════════════════════
SELECT 1 AS "#", 'la tâche horaire existe et est active' AS controle,
       (SELECT CASE WHEN count(*) = 1 AND bool_and(active) AND min(schedule) = '40 * * * *' THEN 'OK'
                    ELSE '⛔ ECHEC (' || count(*) || ' tâche(s))' END
          FROM cron.job WHERE jobname = 'affaire-partie-releve-ecarts') AS verdict
UNION ALL SELECT 2, 'le relevé est vide (0 écart, comme la vue)',
       (SELECT CASE WHEN count(*) = 0 THEN 'OK' ELSE '⛔ ' || count(*) || ' écart(s) relevé(s) : lire la table' END
          FROM public.app_affaire_partie_ecart_releve)
UNION ALL SELECT 3, 'la tâche a déjà tourné, et sans échec',
       (SELECT CASE WHEN h.last_run IS NULL THEN 'pas encore (attendre :40)'
                    WHEN h.last_status = 'succeeded' THEN 'OK (' || to_char(h.last_run AT TIME ZONE 'Europe/Paris', 'DD/MM HH24:MI') || ')'
                    ELSE '⛔ ' || coalesce(h.last_status, '?') END
          FROM public.app_cron_health() h WHERE h.jobname = 'affaire-partie-releve-ecarts')
UNION ALL SELECT 4, 'personne d''autre que service_role ne lit le relevé',
       CASE WHEN NOT has_table_privilege('anon', 'public.app_affaire_partie_ecart_releve', 'select')
             AND NOT has_table_privilege('authenticated', 'public.app_affaire_partie_ecart_releve', 'select')
             AND has_table_privilege('service_role', 'public.app_affaire_partie_ecart_releve', 'select')
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'personne d''autre que service_role ne lance la fonction',
       CASE WHEN NOT has_function_privilege('anon', 'public.app_affaire_partie_relever_ecarts()', 'execute')
             AND NOT has_function_privilege('authenticated', 'public.app_affaire_partie_relever_ecarts()', 'execute')
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 6, 'la vue d''origine est toujours là',
       CASE WHEN to_regclass('public.app_v_affaire_partie_ecarts') IS NOT NULL THEN 'OK' ELSE '⛔ ECHEC' END;
