-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ⑧ types §52 : la vue des liens ne fait plus d'un acquéreur sans vente un mandant      28/10/2026
-- LECTURE SEULE. À coller APRÈS le patch : chaque ligne doit dire « OK ».
-- ⚠ Les 4 testeurs de 24113 restent « mandant » jusqu'à la 1re nuit qui pose la marque (interrupteur
--   APP_RELATION_ACHETEUR_SANS_VENTE=1) : ce n'est PAS un rouge ici, c'est la ligne 6 qui le dit.
-- ═══════════════════════════════════════════════════════════════════════════

WITH v AS (SELECT pg_get_viewdef('public.app_contact_relations_current'::regclass) d)
SELECT n, controle, verdict FROM (
  SELECT 1 n, 'la vue n''est plus celle d''avant (647c3285)' controle,
         CASE WHEN md5(d) <> '647c32855a9b4d8db7b3db8f19247e1e' AND position('app_lien_vente_devenu_acheteur' IN d) > 0
              AND position('<> ''acheteur''' IN d) > 0 THEN 'OK' ELSE 'ROUGE : patch non posé' END verdict FROM v
  UNION ALL
  SELECT 2, 'la vue garde security_invoker',
         CASE WHEN (SELECT reloptions::text FROM pg_class WHERE relname = 'app_contact_relations_current') LIKE '%security_invoker=true%'
              THEN 'OK' ELSE 'ROUGE' END
  UNION ALL
  SELECT 3, 'la règle b est SECURITY DEFINER (même réponse pour tous les comptes)',
         CASE WHEN (SELECT prosecdef FROM pg_proc WHERE proname = 'app_lien_vente_devenu_acheteur') THEN 'OK' ELSE 'ROUGE' END
  UNION ALL
  SELECT 4, 'les 4 vrais mandants (10414, 39032, 39291, 36244) gardent leur rôle',
         CASE WHEN (SELECT count(*) FROM public.app_contact_relations_current
                     WHERE (hektor_contact_id, hektor_annonce_id) IN (('10059470','10414'),('10329773','39032'),('10191838','39291'),('10330240','36244'))
                       AND role_contact IN ('mandant','proprietaire')) = 4 THEN 'OK' ELSE 'ROUGE : un vrai mandant a disparu' END
  UNION ALL
  SELECT 5, 'un acheteur dont la vente vit reste propriétaire (20000015 sur 24113)',
         CASE WHEN EXISTS (SELECT 1 FROM public.app_contact_relations_current
                            WHERE hektor_contact_id = '20000015' AND hektor_annonce_id = '24113' AND role_contact = 'proprietaire')
              THEN 'OK' ELSE 'ROUGE' END
  UNION ALL
  SELECT 6, 'les 4 testeurs de 24113 : « mandant » tant que la nuit n''a pas posé la marque, plus rien ensuite',
         CASE WHEN (SELECT count(*) FROM public.app_relation WHERE hektor_annonce_id = '24113' AND origine = 'acheteur') = 0
              THEN 'OK (marque pas encore posée : ' || (SELECT count(*) FROM public.app_contact_relations_current
                     WHERE hektor_annonce_id = '24113' AND role_contact = 'mandant'
                       AND hektor_contact_id IN ('20000011','20000012','20000013','20000014'))::text || ' encore mandants)'
              WHEN (SELECT count(*) FROM public.app_contact_relations_current
                     WHERE hektor_annonce_id = '24113' AND role_contact = 'mandant'
                       AND hektor_contact_id IN ('20000011','20000012','20000013','20000014')) = 0
              THEN 'OK (marque posée, plus aucun mandant)' ELSE 'ROUGE : marque posée mais encore mandant' END
) t ORDER BY n;
