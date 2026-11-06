-- CONTRÔLES de patch_partenaire_syndic_du_bien_2026-11-06.sql (pièce 4.2a, 06/11/2026). Lecture seule : n'écrit rien.
-- Chaque ligne doit dire « vert ».

SELECT '1 index un seul syndic par bien' AS controle,
       CASE WHEN to_regclass('public.app_partenaire_lien_un_syndic_uidx') IS NOT NULL THEN 'vert' ELSE 'ROUGE' END AS etat
UNION ALL
SELECT '2 fonction poser/changer/retirer',
       CASE WHEN to_regprocedure('public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean)') IS NOT NULL THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '3 fonction lire',
       CASE WHEN to_regprocedure('public.app_partenaire_syndic_du_bien_lire(bigint)') IS NOT NULL THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '4 droits : authenticated oui, anon non',
       CASE WHEN has_function_privilege('authenticated', 'public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean)', 'execute')
             AND has_function_privilege('authenticated', 'public.app_partenaire_syndic_du_bien_lire(bigint)', 'execute')
             AND NOT has_function_privilege('anon', 'public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean)', 'execute')
             AND NOT has_function_privilege('anon', 'public.app_partenaire_syndic_du_bien_lire(bigint)', 'execute')
            THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '5 la garde du perimetre est dans le texte',
       CASE WHEN pg_get_functiondef('public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean)'::regprocedure) LIKE '%app_console_can_access_dossier%'
            THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '6 aucun bien a deux syndics actifs',
       CASE WHEN NOT EXISTS (SELECT 1 FROM public.app_partenaire_lien WHERE role = 'syndic' AND objet = 'bien' AND retire_le IS NULL
                              GROUP BY hektor_annonce_id HAVING count(*) > 1) THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '7 app_partenaire_lien_ecrire intacte (a77de569)',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_partenaire_lien_ecrire(bigint,text,text,text,bigint,bigint,bigint,text,boolean)'::regprocedure), chr(13), ''))
                 = 'a77de569ab6b0e3a77f380fe1f6f40ca' THEN 'vert' ELSE 'ROUGE' END
UNION ALL
SELECT '8 temoin : les liens de la nuit sont toujours la (>= 80 syndics actifs)',
       CASE WHEN (SELECT count(*) FROM public.app_partenaire_lien WHERE role = 'syndic' AND retire_le IS NULL) >= 80
            THEN 'vert' ELSE 'ROUGE' END;
