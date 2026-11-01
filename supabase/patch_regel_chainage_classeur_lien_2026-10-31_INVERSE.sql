-- ===========================================================================
-- RETOUR ARRIERE DU REGEL DU 31/10                               31/10/2026
-- ===========================================================================
-- IL NE JUGE QUE SA PART (lecon 31) : il verifie d'abord qu'il ne reste
--   AUCUNE trace de ce qu'il devait retirer, ET que le gel redevient
--   IDENTIQUE A L'UNITE a la sauvegarde datee du 31/10.
--
-- 01/11 : LA SAUVEGARDE N'EST PLUS DANS SUPABASE. Sans cle primaire, elle
--   faisait echouer la descente ; exportee (12 404 lignes, empreinte complete
--   verifiee) puis supprimee sur decision de Frederic. AVANT ce fichier, coller
--   supabase/rollback/app_classeur_lien_avant_regel_20261031.sql (il la recree).
-- ===========================================================================

BEGIN;

-- 1. retirer les 10 liens poses par le regel (ils portent leur signature)
DELETE FROM public.app_classeur_lien WHERE gele_par = 'regel_chainage_2026-10-31';

-- 2. remettre le lien de beb4e44b, avec SES valeurs d'origine
INSERT INTO public.app_classeur_lien
      (ligne_classeur, app_affaire_id, role, confiance, preuves, etage, gele_le, gele_par, id_unique)
SELECT 4450, 14042, 'offre', 'sûre', 2, '2 mandat + acquéreur + exclusivité',
       '2026-10-29 11:11:32.780512+00'::timestamptz, 'apparier_classeur.py', 'beb4e44b'
 WHERE NOT EXISTS (SELECT 1 FROM public.app_classeur_lien
                    WHERE id_unique = 'beb4e44b' AND app_affaire_id = 14042);

-- 3. controles
DO $ctrl$
DECLARE v_liens int; v_lignes int; v_reste int; v_a int; v_b int;
BEGIN
  SELECT count(*), count(DISTINCT id_unique) INTO v_liens, v_lignes FROM public.app_classeur_lien;
  SELECT count(*) INTO v_reste FROM public.app_classeur_lien
   WHERE gele_par = 'regel_chainage_2026-10-31';
  SELECT count(*) INTO v_a FROM (
      SELECT * FROM public.app_classeur_lien_avant_regel_20261031
       EXCEPT SELECT ligne_classeur, app_affaire_id, role, confiance, preuves, etage,
                     gele_le, gele_par, id_unique FROM public.app_classeur_lien) x;
  SELECT count(*) INTO v_b FROM (
      SELECT ligne_classeur, app_affaire_id, role, confiance, preuves, etage,
             gele_le, gele_par, id_unique FROM public.app_classeur_lien
       EXCEPT SELECT * FROM public.app_classeur_lien_avant_regel_20261031) y;

  RAISE NOTICE 'liens %, lignes %, traces restantes %, ecarts % / %',
               v_liens, v_lignes, v_reste, v_a, v_b;

  IF v_reste <> 0     THEN RAISE EXCEPTION '% trace(s) du regel subsistent', v_reste; END IF;
  IF v_liens <> 12404 THEN RAISE EXCEPTION 'liens = % au lieu de 12404', v_liens; END IF;
  IF v_lignes<> 4680  THEN RAISE EXCEPTION 'lignes = % au lieu de 4680', v_lignes; END IF;
  IF v_a <> 0 OR v_b <> 0 THEN
     RAISE EXCEPTION 'le gel DIFFERE de la sauvegarde : % / %', v_a, v_b; END IF;
END $ctrl$;

COMMIT;
