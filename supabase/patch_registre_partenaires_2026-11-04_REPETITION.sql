-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — patch_registre_partenaires_2026-11-04.sql                                     04/11/2026
-- À coller APRÈS le patch. Lecture seule : chaque contrôle doit être « VERT ».
-- (L'essai complet, avec écritures et témoins, a été fait le 04/11 dans une transaction annulée : 13 verts sur 13.)
-- ═══════════════════════════════════════════════════════════════════════════

SELECT n, controle, CASE WHEN ok THEN 'VERT' ELSE 'ROUGE' END AS resultat
FROM (VALUES
  (1, 'les deux tables existent',
      to_regclass('public.app_partenaire_metier') IS NOT NULL AND to_regclass('public.app_partenaire_lien') IS NOT NULL),
  (2, 'RLS active sur les deux',
      (SELECT bool_and(relrowsecurity) FROM pg_class
        WHERE oid IN (to_regclass('public.app_partenaire_metier'), to_regclass('public.app_partenaire_lien')))),
  (3, 'anon ne lit pas',
      NOT has_table_privilege('anon', 'public.app_partenaire_lien', 'SELECT')
      AND NOT has_table_privilege('anon', 'public.app_partenaire_metier', 'SELECT')),
  (4, 'authenticated lit mais n''écrit pas directement',
      has_table_privilege('authenticated', 'public.app_partenaire_lien', 'SELECT')
      AND NOT has_table_privilege('authenticated', 'public.app_partenaire_lien', 'INSERT')
      AND NOT has_table_privilege('authenticated', 'public.app_partenaire_metier', 'INSERT')
      AND NOT has_table_privilege('authenticated', 'public.app_partenaire_metier', 'UPDATE')),
  (5, 'anon n''exécute pas les fonctions',
      NOT has_function_privilege('anon', 'public.app_partenaire_lien_ecrire(bigint,text,text,text,bigint,bigint,bigint,text,boolean)', 'EXECUTE')
      AND NOT has_function_privilege('anon', 'public.app_partenaire_metier_ecrire(text,text,boolean)', 'EXECUTE')),
  (6, 'authenticated exécute les deux fonctions',
      has_function_privilege('authenticated', 'public.app_partenaire_lien_ecrire(bigint,text,text,text,bigint,bigint,bigint,text,boolean)', 'EXECUTE')
      AND has_function_privilege('authenticated', 'public.app_partenaire_metier_ecrire(text,text,boolean)', 'EXECUTE')),
  (7, 'les deux fonctions sont SECURITY DEFINER',
      (SELECT count(*) FROM pg_proc WHERE proname IN ('app_partenaire_lien_ecrire', 'app_partenaire_metier_ecrire') AND prosecdef) = 2),
  (8, 'les deux index d''unicité « actif » existent',
      to_regclass('public.app_partenaire_metier_actif_uidx') IS NOT NULL AND to_regclass('public.app_partenaire_lien_actif_uidx') IS NOT NULL),
  (9, 'les tables sont vides juste après la pose',
      (SELECT count(*) FROM public.app_partenaire_metier) = 0 AND (SELECT count(*) FROM public.app_partenaire_lien) = 0)
) AS t(n, controle, ok)
ORDER BY n;
