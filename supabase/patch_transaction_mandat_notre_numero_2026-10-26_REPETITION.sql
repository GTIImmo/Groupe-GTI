-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ⑧ types, chantier 2 — c : notre numéro de mandat sur la transaction           26/10/2026
-- Lecture seule. (A) juste après le patch ; (B) après la PREMIÈRE NUIT interrupteur allumé.
-- ═══════════════════════════════════════════════════════════════════════════

WITH
t AS (SELECT * FROM public.app_affaire_ledger WHERE present_in_hektor),
poses AS (SELECT count(*) FILTER (WHERE app_mandat_id IS NOT NULL) n FROM t)
SELECT 1 AS "#", 'A · la colonne existe' AS controle,
       CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public'
                          AND table_name = 'app_affaire_ledger' AND column_name = 'app_mandat_id')
            THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'B · des transactions portent notre numero de mandat (~23 336 attendues le 26/10)',
       CASE WHEN (SELECT n FROM poses) = 0 THEN 'en attente de la nuit'
            WHEN (SELECT n FROM poses) BETWEEN 22000 AND 25000 THEN 'OK (' || (SELECT n FROM poses) || ')'
            ELSE '⚠ A REGARDER (' || (SELECT n FROM poses) || ')' END
UNION ALL SELECT 3, 'B · chaque numero pose designe le mandat de la MEME cle bien + numero',
       CASE WHEN (SELECT n FROM poses) = 0 THEN 'en attente de la nuit'
            WHEN (SELECT count(*) FROM t JOIN public.app_mandat m ON m.app_mandat_id = t.app_mandat_id
                   WHERE m.hektor_annonce_id::text <> t.hektor_annonce_id::text OR m.numero_mandat <> t.numero_mandat) = 0
             AND (SELECT count(*) FROM t WHERE t.app_mandat_id IS NOT NULL
                     AND NOT EXISTS (SELECT 1 FROM public.app_mandat m WHERE m.app_mandat_id = t.app_mandat_id)) = 0
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'B · aucune transaction SANS numero de mandat n''a recu un app_mandat_id',
       CASE WHEN (SELECT n FROM poses) = 0 THEN 'en attente de la nuit'
            WHEN (SELECT count(*) FROM t WHERE nullif(numero_mandat, '') IS NULL AND app_mandat_id IS NOT NULL) = 0
            THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;
