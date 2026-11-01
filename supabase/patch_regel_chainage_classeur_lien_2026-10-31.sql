-- ===========================================================================
-- REGEL DE app_classeur_lien APRES LE § 2.8 DU CHAINAGE          31/10/2026
-- ===========================================================================
-- POURQUOI. Le run du 31/10 04:00 a recolle 12 biens : l'offre « proposee » a
-- rejoint le compromis et la vente du MEME acquereur (§ 2.8, interrupteur
-- `chainage_offre_proposee`). Le gel, lui, lie une ligne du classeur a CHAQUE
-- transaction de sa chaine -- il lui manque donc les offres qui viennent d'y
-- entrer, et il porte un lien devenu faux.
--
-- MESURE AVANT D'ECRIRE, PAS APRES. Les deux sorties de l'apparieur ont ete
--   comparees ligne a ligne (29/10 16:41 contre 31/10 08:04, MEMES options) :
--     1 seule ligne de classeur change de chaine : beb4e44b (14042 -> plus rien,
--       « chaine 14041 deja prise par L4522 » : c'etait un DOUBLON, et l'apparieur
--       garde celle qui a 7 preuves contre 2)
--     11 lignes changent d'ETAGE sans changer de chaine -- NON TOUCHEES ICI
--       (hors perimetre : le perimetre accorde porte sur les LIENS)
--     2 lignes NEUVES au classeur (1a474908, cd29653f) -- NON TRAITEES ICI,
--       le classeur a grossi de 4 773 a 4 775 lignes, c'est un autre sujet
--
-- LE CHIFFRE ANNONCE LA VEILLE ETAIT +9 / -1. LA MESURE DIT +10 / -1.
--   Le 10e est l'offre 28811 du bien 61534 (ligne 6095c819), de meme nature que
--   les neuf autres. L'ecart a ete signale a Frederic AVANT l'application.
--
-- NI `preuves` NI `confiance` NE SONT RECALCULES -- lecon du 29/10 :
--   recalcules, ils BAISSENT sur 3 001 lignes et le maximum passe de 8 a 7.
--   Les liens ajoutes COPIENT les valeurs de leur ligne soeur (meme id_unique).
--
-- SAUVEGARDE DATEE, PRISE AVANT : public.app_classeur_lien_avant_regel_20261031
--   (12 404 lignes, controlee A L'UNITE : 0 ecart dans les DEUX sens).
-- RETOUR ARRIERE : patch_regel_chainage_classeur_lien_2026-10-31_INVERSE.sql
--
-- ATTENDU APRES : 12 404 - 1 + 10 = 12 413 liens · 4 679 lignes reconnues
--   (beb4e44b n'avait qu'UN lien : la retirer retire la ligne du gel, et c'est
--    voulu -- une ligne mal rattachee vaut moins qu'une ligne non rattachee)
-- ===========================================================================

BEGIN;

-- 1. LES 10 OFFRES QUI ONT REJOINT LEUR CHAINE : un lien de plus pour leur ligne.
--    On part d'une ligne EXISTANTE du meme id_unique et on ne change que la
--    transaction, le role et la tracabilite.
INSERT INTO public.app_classeur_lien
      (ligne_classeur, app_affaire_id, role, confiance, preuves, etage, gele_le, gele_par, id_unique)
SELECT DISTINCT ON (c.id_unique)
       l.ligne_classeur, c.app_affaire_id, 'offre', l.confiance, l.preuves, l.etage,
       now(), 'regel_chainage_2026-10-31', l.id_unique
  FROM (VALUES
          ('d1484acb', 14042::bigint), ('f276bd71', 21525), ('2740db19', 25673),
          ('45fa3495', 27010),         ('a49d96ef', 28228), ('cbc5a95b', 28550),
          ('bce3d047', 28577),         ('12a4bf9f', 28628), ('3bc00e81', 28789),
          ('6095c819', 28811)
       ) AS c(id_unique, app_affaire_id)
  JOIN public.app_classeur_lien l ON l.id_unique = c.id_unique
 ORDER BY c.id_unique, l.app_affaire_id;

-- 2. LE FAUX LIEN QUI TOMBE : beb4e44b visait l'offre 14042, que l'apparieur
--    attribue desormais a d1484acb (7 preuves contre 2).
DELETE FROM public.app_classeur_lien
 WHERE id_unique = 'beb4e44b' AND app_affaire_id = 14042;

-- 3. LES CONTROLES, DANS LA MEME TRANSACTION : si un seul est faux, tout tombe.
DO $ctrl$
DECLARE
  v_liens int; v_lignes int; v_poses int; v_beb int; v_hors int;
BEGIN
  SELECT count(*), count(DISTINCT id_unique) INTO v_liens, v_lignes
    FROM public.app_classeur_lien;
  SELECT count(*) INTO v_poses FROM public.app_classeur_lien
   WHERE gele_par = 'regel_chainage_2026-10-31';
  SELECT count(*) INTO v_beb FROM public.app_classeur_lien WHERE id_unique = 'beb4e44b';
  -- TEMOIN LE PLUS IMPORTANT : rien d'AUTRE que nos 11 gestes n'a bouge.
  SELECT count(*) INTO v_hors FROM (
      SELECT * FROM public.app_classeur_lien_avant_regel_20261031
       EXCEPT SELECT ligne_classeur, app_affaire_id, role, confiance, preuves, etage,
                     gele_le, gele_par, id_unique FROM public.app_classeur_lien
  ) x WHERE NOT (x.id_unique = 'beb4e44b' AND x.app_affaire_id = 14042);

  RAISE NOTICE 'liens %, lignes %, poses %, beb4e44b %, perdus hors perimetre %',
               v_liens, v_lignes, v_poses, v_beb, v_hors;

  IF v_liens  <> 12413 THEN RAISE EXCEPTION 'liens = % au lieu de 12413', v_liens; END IF;
  IF v_lignes <> 4679  THEN RAISE EXCEPTION 'lignes = % au lieu de 4679',  v_lignes; END IF;
  IF v_poses  <> 10    THEN RAISE EXCEPTION 'liens poses = % au lieu de 10', v_poses; END IF;
  IF v_beb    <> 0     THEN RAISE EXCEPTION 'beb4e44b porte encore % lien(s)', v_beb; END IF;
  IF v_hors   <> 0     THEN RAISE EXCEPTION '% lien(s) PERDU(S) hors perimetre', v_hors; END IF;
END $ctrl$;

COMMIT;
