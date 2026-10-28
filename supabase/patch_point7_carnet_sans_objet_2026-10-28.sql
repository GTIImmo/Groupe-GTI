-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ §58 POINT 7 B — LES 5 OFFRES D'ESSAI DU CARNET, CLOSES « sans_objet »                       28/10/2026
-- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, §58 point 7 (audit du 26/10) et décision de Frédéric
--        du 28/10 : « on les clôt ou supprime ».
-- On CLÔT (on ne supprime pas) : la ligne garde ce qui a été saisi, quand et par qui ; seul son état passe de vide à
-- « sans_objet » (l'état que le carnet porte déjà sur 26 lignes). Les 5 transactions : l'offre d'essai 1001339 (24933, 5 champs)
-- et les 4 offres de l'essai 5 sur 24113 (1001381 / 84 / 90 / 93). Leurs biens sont vendus : R3 ne les rejugera jamais.
-- ⛔ SAUVEGARDE DATÉE d'abord (app_affaire_champ_app_avant_point7_20261028). GARDE : s'arrête si ce ne sont pas EXACTEMENT
--    23 lignes sans état sur ces 5 transactions -- quelqu'un serait passé avant.
-- Retour arrière : patch_point7_carnet_sans_objet_2026-10-28_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $p7$
DECLARE n int; m int;
BEGIN
    SELECT count(*) INTO n FROM public.app_affaire_champ_app
     WHERE app_affaire_id IN (1001339, 1001381, 1001384, 1001390, 1001393) AND etat IS NULL;
    SELECT count(*) INTO m FROM public.app_affaire_champ_app WHERE etat IS NULL;
    IF n <> 23 OR m <> 23 THEN
        RAISE EXCEPTION '%', format('ARRET : %s lignes sans etat sur les 5 transactions (23 attendues), %s dans tout le carnet (23 attendues). Rien n''est change.', n, m);
    END IF;
END
$p7$;

CREATE TABLE public.app_affaire_champ_app_avant_point7_20261028 AS
SELECT * FROM public.app_affaire_champ_app WHERE app_affaire_id IN (1001339, 1001381, 1001384, 1001390, 1001393);
REVOKE ALL ON TABLE public.app_affaire_champ_app_avant_point7_20261028 FROM PUBLIC, anon, authenticated;
COMMENT ON TABLE public.app_affaire_champ_app_avant_point7_20261028 IS
  'Sauvegarde du 28/10/2026 avant la cloture « sans_objet » des 5 offres d''essai du carnet (§58 point 7). Sert au retour arriere.';

UPDATE public.app_affaire_champ_app
   SET etat = 'sans_objet', constate_le = now()
 WHERE app_affaire_id IN (1001339, 1001381, 1001384, 1001390, 1001393) AND etat IS NULL;

COMMIT;
