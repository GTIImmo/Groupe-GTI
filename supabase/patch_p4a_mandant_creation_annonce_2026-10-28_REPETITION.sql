-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ⑧ types §53 P4-a : le mandant existant choisi à la création, chez nous au clic          28/10/2026
-- LECTURE SEULE. À coller APRÈS le patch : chaque ligne doit dire « OK ».
-- La preuve par le geste (une vraie création dans des transactions annulées) est l'essai du 28/10 (13/13).
-- ═══════════════════════════════════════════════════════════════════════════

WITH f AS (SELECT pg_get_functiondef('public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)'::regprocedure) d)
SELECT n, controle, verdict FROM (
  SELECT 1 n, 'la fonction n''est plus celle d''avant (a5e70b57) et porte le bloc @P4a' controle,
         CASE WHEN md5(d) <> 'a5e70b5734876f74ecd0083681a1ebe8' AND position('-- @P4a-debut' IN d) > 0 AND position('-- @P4a-fin' IN d) > 0
              THEN 'OK' ELSE 'ROUGE : patch non posé' END verdict FROM f
  UNION ALL
  SELECT 2, 'le bloc est dans la branche « l''annonce naît dans l''app », avant la création du travail',
         CASE WHEN position('-- @P4a-fin' IN d) > position('-- === fin 8a piece 2 ===' IN d)
                   AND position('-- @P4a-fin' IN d) < position('created_job := public.app_console_create_draft_annonce_job(' IN substr(d, position('-- === fin 8a piece 2 ===' IN d))) + position('-- === fin 8a piece 2 ===' IN d)
              THEN 'OK' ELSE 'ROUGE' END FROM f
  UNION ALL
  SELECT 3, 'le lien peut attendre son numéro de bien (colonne facultative)',
         CASE WHEN (SELECT is_nullable FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'app_relation'
                     AND column_name = 'hektor_annonce_id') = 'YES' THEN 'OK' ELSE 'ROUGE' END
  UNION ALL
  SELECT 4, 'l''unicité (contact, bien) est toujours là',
         CASE WHEN EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'app_relation_couple_unique') THEN 'OK' ELSE 'ROUGE' END
  UNION ALL
  SELECT 5, 'les liens qui attendent leur numéro de bien (0 attendu tant qu''aucune annonce n''a été créée avec un mandant)',
         'OK (' || (SELECT count(*) FROM public.app_relation WHERE hektor_annonce_id IS NULL)::text || ')'
) t ORDER BY n;
