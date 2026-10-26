-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ⑧ types, chantier 1 : l'acheteur « propriétaire depuis la vente »          26/10/2026
-- Lecture seule. À rejouer : (A) juste après le patch ; (B) après la PREMIÈRE NUIT interrupteur allumé.
-- En (A), les lignes 6 à 9 disent « en attente de la nuit » : c'est normal.
-- ═══════════════════════════════════════════════════════════════════════════

WITH
regle AS (SELECT count(*) FILTER (WHERE origine = 'vente') AS nes FROM public.app_relation),
-- ⭐ le témoin POSITIF : l'acheteur de 61730 (JACQUIER, vente du 25/09/2026), absent du mandat de Hektor
temoin AS (SELECT origine, proprietaire_depuis FROM public.app_relation
            WHERE app_contact_id = 10354352 AND hektor_annonce_id = '61730'),
-- ⭐ les 10 VRAIS mandants (anciennes ventes, nommés au mandat de Hektor) : ils ne bougent JAMAIS (D5 b)
vrais(ann, hid) AS (VALUES ('10293','31405'),('10447','132724'),('10776','167529'),('19850','46028'),
                           ('29546','153073'),('29822','166093'),('39359','334205'),('45119','179814'),
                           ('45172','179417'),('9823','68121'))
SELECT 1 AS "#", 'A · les deux colonnes existent' AS controle,
       CASE WHEN (SELECT count(*) FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'app_relation'
                     AND column_name IN ('origine', 'proprietaire_depuis')) = 2 THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'A · la vue porte la regle une fois, et reste security_invoker',
       CASE WHEN (length(pg_get_viewdef('public.app_contact_relations_current'::regclass))
                  - length(replace(pg_get_viewdef('public.app_contact_relations_current'::regclass), 'r.origine', ''))) / 9 = 1
             AND (SELECT reloptions FROM pg_class WHERE oid = 'public.app_contact_relations_current'::regclass)
                 @> array['security_invoker=true'] THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'A · les 55 liens du filet sont retires (filet_26_10), et aucun autre retrait n''a bouge',
       CASE WHEN (SELECT count(*) FROM public.app_relation WHERE retire_par = 'filet_26_10') = 55
             AND (SELECT count(*) FROM public.app_relation WHERE retire_le IS NOT NULL
                     AND coalesce(retire_par, '') <> 'filet_26_10') >= 2 THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'A · aucun lien « acquereur » ne reste vivant dans le registre des liens',
       CASE WHEN (SELECT count(*) FROM public.app_relation
                   WHERE role_hektor LIKE 'acquereur%' AND retire_le IS NULL) = 0 THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 5, 'A · la vue ne montre aucun des 55',
       CASE WHEN (SELECT count(*) FROM public.app_contact_relations_current v
                   JOIN public.app_relation r ON v.hektor_contact_id = r.app_contact_id::text
                                             AND v.hektor_annonce_id::text = r.hektor_annonce_id
                  WHERE r.retire_par = 'filet_26_10' AND v.role_contact IN ('mandant', 'proprietaire')) = 0
            THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 6, 'B · des liens nes d''une vente sont poses (~113 attendus le 26/10)',
       CASE WHEN (SELECT nes FROM regle) = 0 THEN 'en attente de la nuit'
            WHEN (SELECT nes FROM regle) BETWEEN 100 AND 140 THEN 'OK (' || (SELECT nes FROM regle) || ')'
            ELSE '⚠ A REGARDER (' || (SELECT nes FROM regle) || ')' END
UNION ALL SELECT 7, 'B · le temoin positif 61730 / JACQUIER : origine vente, depuis le 2026-09-25',
       CASE WHEN (SELECT nes FROM regle) = 0 THEN 'en attente de la nuit'
            WHEN (SELECT origine FROM temoin) = 'vente' AND (SELECT proprietaire_depuis FROM temoin) = '2026-09-25' THEN 'OK'
            ELSE '⛔ ECHEC' END
UNION ALL SELECT 8, 'B · les 10 vrais mandants n''ont PAS d''origine vente (D5 b)',
       CASE WHEN (SELECT nes FROM regle) = 0 THEN 'en attente de la nuit'
            WHEN (SELECT count(*) FROM public.app_relation r JOIN vrais v
                    ON r.hektor_annonce_id = v.ann AND r.hektor_contact_id = v.hid
                  WHERE r.origine IS NOT NULL) = 0 THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 9, 'B · la vue ne dit plus « mandant » pour un lien ne d''une vente',
       CASE WHEN (SELECT nes FROM regle) = 0 THEN 'en attente de la nuit'
            WHEN (SELECT count(*) FROM public.app_contact_relations_current v
                    JOIN public.app_relation r ON v.hektor_contact_id = r.app_contact_id::text
                                              AND v.hektor_annonce_id::text = r.hektor_annonce_id
                   WHERE r.origine = 'vente' AND v.role_contact = 'mandant') = 0 THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;
