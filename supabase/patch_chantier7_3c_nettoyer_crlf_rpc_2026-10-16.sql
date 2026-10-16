-- ============================================================================
-- (7)-3c -- NETTOYER LES RETOURS CHARIOT DE LA RPC DE COUVERTURE
-- 16/10/2026 · 5 lignes, aucun changement de comportement
-- ============================================================================
-- CE QUE LE CONTROLE D'APRES-COLLAGE A TROUVE : le corps de
-- app_console_photo_couverture_optimistic porte **112 retours chariot** sur
-- 118 lignes. Le fichier du depot, lui, est en LF : ils viennent du TRANSPORT
-- (le copier-coller depuis Windows). C'est la 4e fois aujourd'hui que cette
-- famille se manifeste.
--
-- ⚠ CE N'EST PAS UN DEFAUT DE FONCTIONNEMENT, et il faut le dire :
--   · aucune chaine ne traverse de ligne dans cette fonction (verifie : les
--     3 lignes a apostrophes impaires sont des COMMENTAIRES francais --
--     « L'ETAT », « n'aurait », « l'insertion ») ;
--   · preuve par l'exemple : app_set_mandat_cloture_optimistic porte 102
--     retours chariot, elle est en production depuis le 13/10 et elle a tourne
--     correctement aujourd'hui.
--
-- ⚠ MAIS CA MORDRA PLUS TARD. Tout patch futur qui voudra modifier cette
--   fonction par la technique du projet -- lire le corps, chercher une ANCRE,
--   inserer, reexecuter -- ne retrouvera pas son ancre si elle est multi-ligne
--   (lecon du 15/10, ecrite trois fois). On nettoie donc maintenant, pendant
--   que c'est gratuit.
--
-- ⭐ POURQUOI CELLE-CI ET PAS LES AUTRES : les patchs qui LISENT la fonction
--   dans la base et la REECRIVENT enveloppent deja replace(..., chr(13), '')
--   -- c'est pourquoi app_console_archiver_contact_optimistic a ZERO retour
--   chariot. Un patch qui CREE une fonction depuis le texte colle, lui, emporte
--   le CRLF tel quel. La difference est la, et elle merite d'etre sue.
--
-- INVERSE : il n'y en a pas, et c'est voulu. Remettre des retours chariot
-- n'aurait aucun sens. Le comportement ne change pas d'un caractere.
-- ============================================================================

BEGIN;

SET LOCAL lock_timeout = '5s';

DO $nettoyage$
DECLARE
  v_src   text;
  v_propre text;
  v_avant integer;
BEGIN
  SELECT pg_get_functiondef(p.oid) INTO v_src
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_photo_couverture_optimistic';
  IF v_src IS NULL THEN
    RAISE EXCEPTION 'STOP : app_console_photo_couverture_optimistic introuvable';
  END IF;

  v_avant := length(v_src) - length(replace(v_src, chr(13), ''));
  IF v_avant = 0 THEN
    RAISE NOTICE 'DEJA PROPRE : zero retour chariot';
    RETURN;
  END IF;

  v_propre := replace(v_src, chr(13), '');

  -- ⚠ GARDE-FOU : on ne doit RIEN changer d'autre. Le texte nettoye doit faire
  --   exactement la taille d'avant moins le nombre de retours chariot retires.
  IF length(v_propre) <> length(v_src) - v_avant THEN
    RAISE EXCEPTION 'STOP : le nettoyage a change autre chose que les retours chariot';
  END IF;

  EXECUTE v_propre;
  RAISE NOTICE 'NETTOYE : % retours chariot retires du corps', v_avant;
END $nettoyage$;

-- LE CONTROLE DE SORTIE
DO $ctrl$
DECLARE v_cr integer; v_acl text;
BEGIN
  SELECT length(pg_get_functiondef(p.oid)) - length(replace(pg_get_functiondef(p.oid), chr(13), '')),
         array_to_string(p.proacl, ' | ')
    INTO v_cr, v_acl
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_photo_couverture_optimistic';

  IF v_cr <> 0 THEN
    RAISE EXCEPTION 'STOP : il reste % retours chariot', v_cr;
  END IF;
  -- ⚠ Un CREATE OR REPLACE garde les droits, mais on le VERIFIE au lieu de le croire.
  IF v_acl IS NULL OR position('authenticated=X' in v_acl) = 0 THEN
    RAISE EXCEPTION 'STOP : authenticated a perdu l''execute (%)', coalesce(v_acl, '(aucun)');
  END IF;
  IF position('anon=' in v_acl) > 0 THEN
    RAISE EXCEPTION 'STOP : anon a gagne un droit (%)', v_acl;
  END IF;
  RAISE NOTICE 'OK : 0 retour chariot, authenticated garde l''execute, anon n''a rien.';
END $ctrl$;

COMMIT;
