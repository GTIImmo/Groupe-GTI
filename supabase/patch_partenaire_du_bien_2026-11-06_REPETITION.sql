-- CONTRÔLES de patch_partenaire_du_bien_2026-11-06.sql (lot 5, 06/11/2026). Lecture seule. Chaque ligne doit dire « vert ».
SELECT '1 index un seul diagnostiqueur par bien' AS controle,
       CASE WHEN to_regclass('public.app_partenaire_lien_un_diag_uidx') IS NOT NULL THEN 'vert' ELSE 'ROUGE' END AS etat
UNION ALL
SELECT '2 fonction poser/changer/retirer (generique)',
       CASE WHEN to_regprocedure('public.app_partenaire_du_bien(text,bigint,bigint,text,boolean)') IS NOT NULL THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '3 fonction lire (generique)',
       CASE WHEN to_regprocedure('public.app_partenaire_du_bien_lire(text,bigint)') IS NOT NULL THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '4 droits : authenticated oui, anon non',
       CASE WHEN has_function_privilege('authenticated', 'public.app_partenaire_du_bien(text,bigint,bigint,text,boolean)', 'execute')
             AND has_function_privilege('authenticated', 'public.app_partenaire_du_bien_lire(text,bigint)', 'execute')
             AND NOT has_function_privilege('anon', 'public.app_partenaire_du_bien(text,bigint,bigint,text,boolean)', 'execute')
             AND NOT has_function_privilege('anon', 'public.app_partenaire_du_bien_lire(text,bigint)', 'execute')
            THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '5 la garde du perimetre est dans le texte',
       CASE WHEN pg_get_functiondef('public.app_partenaire_du_bien(text,bigint,bigint,text,boolean)'::regprocedure) LIKE '%app_console_can_access_dossier%'
            THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '6 aucun bien a deux diagnostiqueurs actifs',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_partenaire_lien WHERE role = 'diagnostiqueur' AND objet = 'bien' AND retire_le IS NULL
                              GROUP BY hektor_annonce_id HAVING count(*) > 1) THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '7 le geste du syndic (4.2) est intact',
       CASE WHEN to_regprocedure('public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean)') IS NOT NULL
             AND to_regclass('public.app_partenaire_lien_un_syndic_uidx') IS NOT NULL THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '8 temoin : les liens de la nuit sont toujours la (>= 4 diagnostiqueurs actifs)',
       CASE WHEN (SELECT count(*) FROM public.app_partenaire_lien WHERE role = 'diagnostiqueur' AND retire_le IS NULL) >= 4
            THEN 'vert' ELSE 'ROUGE' END;
