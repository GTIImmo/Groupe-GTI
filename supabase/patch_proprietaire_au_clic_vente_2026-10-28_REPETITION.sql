-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ⑧ types §52 C : « Propriétaire depuis le … » au clic de la vente                     28/10/2026
-- LECTURE SEULE. À coller APRÈS le patch : chaque ligne doit dire « OK ».
-- La preuve par le geste (une vraie vente dans une transaction annulée) est faite par l'essai du 28/10 (11/11).
-- ═══════════════════════════════════════════════════════════════════════════

WITH f AS (SELECT pg_get_functiondef('public.app_change_annonce_status_optimistic'::regproc) d,
                  (SELECT prosecdef FROM pg_proc WHERE oid = 'public.app_change_annonce_status_optimistic'::regproc) sd)
SELECT n, controle, verdict FROM (
  SELECT 1 n, 'la fonction n''est plus celle d''avant (fce35139) et porte le bloc @C-proprio-au-clic' controle,
         CASE WHEN md5(d) <> 'fce35139d02f8f4f995392a9f8566891' AND position('-- @C-proprio-au-clic' IN d) > 0
              AND position('-- @C-fin' IN d) > 0 THEN 'OK' ELSE 'ROUGE : patch non posé' END verdict FROM f
  UNION ALL
  SELECT 2, 'le bloc est juste AVANT le recalcul du type (le type lit le lien posé)',
         CASE WHEN position('-- @C-fin' IN d) < position('perform public.app_recalculer_type_du_bien(d.hektor_annonce_id::text, target_dossier_id);' IN d)
              THEN 'OK' ELSE 'ROUGE' END FROM f
  UNION ALL
  SELECT 3, 'la fonction reste SECURITY DEFINER, appelable par l''app',
         CASE WHEN sd AND has_function_privilege('authenticated', 'public.app_change_annonce_status_optimistic(bigint, text, jsonb, integer)', 'EXECUTE')
              THEN 'OK' ELSE 'ROUGE' END FROM f
  UNION ALL
  SELECT 4, 'le bloc ne vise que la VENTE (pas l''offre ni le compromis)',
         CASE WHEN position('if v_kind = ''vente'' and v_affaire_id is not null then' IN d) > 0 THEN 'OK' ELSE 'ROUGE' END FROM f
) t ORDER BY n;
