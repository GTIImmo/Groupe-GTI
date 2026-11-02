-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION de patch_pilotage_stock_2026-11-02.sql — À COLLER APRÈS LE PATCH                 02/11/2026
-- Lecture seule (la transaction est annulée à la fin). Rend une ligne par contrôle : « OK » ou « ROUGE ».
-- Les chiffres de référence ont été mesurés le 02/11/2026 au soir ; ils bougent avec le stock :
-- un écart de quelques biens est normal, un ordre de grandeur différent ne l'est pas.
-- Le contrôle « sans utilisateur, rien » est dans le patch lui-même (bloc $preuve$).
-- ═══════════════════════════════════════════════════════════════════════════
BEGIN;

SELECT set_config('request.jwt.claims', json_build_object(
         'sub', (SELECT id FROM auth.users WHERE email = 'frederic.gerphagnon@gti-immobilier.fr'),
         'email', 'frederic.gerphagnon@gti-immobilier.fr', 'role', 'authenticated')::text, true);

CREATE TEMP TABLE _pilotage_stock ON COMMIT DROP AS SELECT * FROM public.app_pilotage_stock();

WITH s AS (SELECT * FROM _pilotage_stock),
att AS (SELECT count(*) AS n FROM public.app_dossier_current WHERE statut_annonce IN ('Actif', 'Sous offre', 'Sous compromis'))
SELECT '1. un admin lit tous les biens en vente, sous offre et sous compromis' AS controle,
       CASE WHEN (SELECT count(*) FROM s) = (SELECT n FROM att) THEN 'OK' ELSE 'ROUGE' END AS verdict,
       (SELECT count(*) FROM s)::text || ' / ' || (SELECT n FROM att)::text AS detail
UNION ALL
SELECT '2. environ 3 biens sur 4 ont des honoraires (521 sur 699 le 02/11)',
       CASE WHEN (SELECT count(honoraires)::numeric / nullif(count(*), 0) FROM s) BETWEEN 0.6 AND 0.95 THEN 'OK' ELSE 'ROUGE' END,
       (SELECT count(honoraires)::text || ' avec honoraires' FROM s)
UNION ALL
SELECT '3. honoraires des biens Actif de l''ordre de 3,8 M€ (3 768 418 le 02/11)',
       CASE WHEN (SELECT sum(honoraires) FROM s WHERE statut_annonce = 'Actif') BETWEEN 2500000 AND 5000000 THEN 'OK' ELSE 'ROUGE' END,
       (SELECT round(sum(honoraires))::text FROM s WHERE statut_annonce = 'Actif')
UNION ALL
SELECT '4. presque aucun honoraire au-delà de 20 % du prix (une copie additionnée le trahirait)',
       CASE WHEN (SELECT count(*) FROM s WHERE honoraires > prix * 0.2 AND statut_annonce = 'Actif') <= 2 THEN 'OK' ELSE 'ROUGE' END,
       (SELECT count(*)::text FROM s WHERE honoraires > prix * 0.2 AND statut_annonce = 'Actif')
UNION ALL
SELECT '5. la clé publique ne peut pas l''appeler',
       CASE WHEN NOT has_function_privilege('anon', 'public.app_pilotage_stock()', 'EXECUTE') THEN 'OK' ELSE 'ROUGE' END,
       '';

ROLLBACK;
