-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ⑧ §58 point 7 B : remettre les 23 saisies des 5 offres d'essai comme avant (état vide)    28/10/2026
-- Il ne juge que SA part : il remet état et date de constat depuis la sauvegarde, ligne par ligne, et ne touche à rien d'autre.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
UPDATE public.app_affaire_champ_app c
   SET etat = s.etat, constate_le = s.constate_le
  FROM public.app_affaire_champ_app_avant_point7_20261028 s
 WHERE c.app_affaire_id = s.app_affaire_id AND c.champ = s.champ AND c.ecrit_le IS NOT DISTINCT FROM s.ecrit_le;
DO $v$
DECLARE n int;
BEGIN
    SELECT count(*) INTO n FROM public.app_affaire_champ_app WHERE app_affaire_id IN (1001339, 1001381, 1001384, 1001390, 1001393) AND etat IS NULL;
    IF n <> 23 THEN RAISE EXCEPTION '%', format('ARRET : %s lignes remises sans etat (23 attendues). Tout est annule.', n); END IF;
END
$v$;
-- la sauvegarde est gardée (elle ne coûte rien) ; la retirer est une décision à part
COMMIT;
