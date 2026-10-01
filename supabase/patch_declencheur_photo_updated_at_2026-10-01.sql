-- ═══════════════════════════════════════════════════════════════════════════════
-- GARANTIR updated_at SUR app_console_photo -- LA CONDITION DU DELTA   01/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Aucun redemarrage, aucun deploiement. Ne touche AUCUNE donnee.
--
-- ─── POURQUOI ───────────────────────────────────────────────────────────────────
-- La descente rapatrie app_console_photo EN ENTIER chaque nuit : 437 044 lignes,
-- 964 Mo, 30 % du volume. Or il n'en change que ~219 par jour (mesure du 01/10).
--
-- Le mecanisme pour ne descendre que les modifications EXISTE depuis le 16/09
-- (DELTA_HORODATAGE dans phase2/sync/pull_from_supabase.py). Il a divise
-- app_rapprochement_score_history par 1 600 : 454 267 lignes -> 283.
--
-- ⛔ MAIS IL EST INTERDIT DE S'EN SERVIR SANS GARANTIE, et la note du 16/09 dit
--    exactement pourquoi :
--      « ON N'ACTIVE LE DELTA QUE LA OU L'HORODATAGE EST ECRIT A CHAQUE ECRITURE.
--        Donc `updated_at` ne vaut que ce que l'ecrivain a bien voulu y mettre --
--        s'y fier ferait manquer des modifications EN SILENCE, ce qui est pire
--        que de tout redescendre. »
--
-- ⭐ L'AUDIT DU 01/10 A TROUVE L'ECRIVAIN QUI OUBLIE, et il n'est pas theorique :
--
--      ecrivain                              modifie ?   tamponne updated_at ?
--      ----------------------------------------------------------------------
--      worker  upsertConsolePhotos              oui              OUI  (l. 4362)
--      worker  les derives (PATCH)               oui              OUI  (l. 5689)
--      rattrapage_photos.js                      oui              OUI
--      app_photo_marquer_sortie_vitrine          OUI              ⛔ NON
--
--    La derniere est la tache pg_cron « app-photo-sortie-vitrine », qui tourne
--    CHAQUE JOUR A 08:30. Elle pose `hors_vitrine_depuis` -- L'ANCRE DES SIX MOIS,
--    celle qui decide quand une photo sort du coffre public (G.8).
--    Sans ce declencheur, le delta raterait CHAQUE sortie de vitrine, en silence :
--    le serveur ne saurait jamais qu'une photo a ete demonetisee.
--
-- ⭐ CE PATCH DEPLACE LA GARANTIE : elle ne depend plus de la bonne volonte de
--    chaque ecrivain, mais de la BASE elle-meme. C'est ce qui rend le delta sur
--    cette table aussi sur que sur les quatre tables deja en place.
--
-- ─── CE QU'IL FAIT, ET CE QU'IL NE FAIT PAS ─────────────────────────────────────
--   UPDATE : updated_at := now(), TOUJOURS, quoi que l'ecrivain ait envoye.
--            Aucun ecrivain ne postdate ni n'antidate cette colonne (verifie sur
--            les quatre) : forcer ne casse donc rien, et c'est le seul reglage qui
--            interdise un oubli.
--   INSERT : COALESCE(valeur envoyee, now()) -- on RESPECTE ce que l'ecrivain pose,
--            on comble seulement s'il n'a rien mis. Une ligne neuve sans date
--            serait invisible au delta.
--   ⛔ IL NE MODIFIE AUCUNE LIGNE EXISTANTE. Les 437 044 dates actuelles restent
--      telles quelles. Le declencheur n'agit qu'aux ecritures FUTURES.
--
-- ⚠ CE PATCH NE SUFFIT PAS A ACTIVER LE DELTA. Il pose la garantie, rien de plus.
--   L'activation est une ligne de Python (DELTA_HORODATAGE), livree separement, et
--   elle VERIFIE la presence de ce declencheur avant de se fier a la date.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
--   DROP TRIGGER IF EXISTS trg_app_console_photo_updated_at ON public.app_console_photo;
--   DROP FUNCTION IF EXISTS public.app_console_photo_touch_updated_at();
--   (et retirer la ligne de DELTA_HORODATAGE si elle a ete posee -- sinon le delta
--    se fierait de nouveau a une date sans garantie)
--
-- ─── EPROUVE AVANT ENVOI, le 01/10 ──────────────────────────────────────────────
--   En BEGIN/ROLLBACK sur la base reelle : on a rejoue le geste qui OUBLIE la date
--   (un UPDATE de hors_vitrine_depuis seul, comme la tache de 08:30).
--      avant   2026-09-26 04:08:18     (la photo n'avait pas bouge depuis 5 jours)
--      apres   2026-10-01 18:29:52     -> le declencheur l'a rattrape
--   Puis ROLLBACK verifie : 0 declencheur restant, 0 fonction restante, 0 ecriture.
--
--   ⚠ DEUXIEME VERSION. La premiere a ETE REFUSEE par la base a 18:35 sur son
--     propre garde-fou 3 -- voir l'encadre devant ce garde-fou : elle defaisait
--     l'essai par un UPDATE, que le declencheur ecrasait. Corrigee en annulant une
--     sous-transaction. La version ci-dessous va jusqu'au bout (« patch jouable »).
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ⛔ GARDE-FOU 1 : la table est bien celle qu'on croit, avec sa colonne.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public' AND table_name = 'app_console_photo'
       AND column_name = 'updated_at'
  ) THEN
    RAISE EXCEPTION 'ARRET : public.app_console_photo.updated_at est introuvable.';
  END IF;
END $$;

-- ⛔ GARDE-FOU 2 : on ne pose pas un second declencheur par-dessus un existant.
--   Deux declencheurs sur la meme colonne, c'est un ordre d'execution a deviner.
DO $$
DECLARE deja int;
BEGIN
  SELECT count(*) INTO deja
    FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname = 'public' AND c.relname = 'app_console_photo'
     AND NOT t.tgisinternal
     AND t.tgname <> 'trg_app_console_photo_updated_at';
  IF deja > 0 THEN
    RAISE EXCEPTION 'ARRET : % declencheur(s) deja pose(s) sur app_console_photo. '
                    'Les lire avant d''en ajouter un.', deja;
  END IF;
END $$;

-- ① LA FONCTION
CREATE OR REPLACE FUNCTION public.app_console_photo_touch_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    -- TOUJOURS : c'est la garantie. Un ecrivain qui oublie ne peut plus nuire.
    NEW.updated_at := now();
  ELSE
    -- INSERT : on respecte la valeur de l'ecrivain, on comble seulement le vide.
    NEW.updated_at := COALESCE(NEW.updated_at, now());
  END IF;
  RETURN NEW;
END $$;

COMMENT ON FUNCTION public.app_console_photo_touch_updated_at() IS
  'Garantit updated_at sur app_console_photo : c''est la CONDITION du delta de la '
  'descente (DELTA_HORODATAGE). Pose le 01/10/2026 apres avoir mesure que '
  'app_photo_marquer_sortie_vitrine ecrit hors_vitrine_depuis SANS toucher la date : '
  'le delta aurait rate chaque sortie de vitrine en silence.';

-- ② LE DECLENCHEUR
DROP TRIGGER IF EXISTS trg_app_console_photo_updated_at ON public.app_console_photo;
CREATE TRIGGER trg_app_console_photo_updated_at
  BEFORE INSERT OR UPDATE ON public.app_console_photo
  FOR EACH ROW
  EXECUTE FUNCTION public.app_console_photo_touch_updated_at();

-- ⛔ GARDE-FOU 3 : il est bien la, et il FONCTIONNE sur le cas qui le motive.
--   On rejoue le geste qui oublie la date, puis on ANNULE l'essai -- sans quoi on
--   livrerait un declencheur sans avoir verifie qu'il attrape ce pour quoi il existe.
--
-- ⚠⚠ PREMIERE VERSION REFUSEE PAR LA BASE, le 01/10 a 18:35, et la lecon vaut
--    d'etre gardee. Elle « defaisait » l'essai par un UPDATE qui remettait
--    updated_at a sa valeur d'avant :
--        UPDATE app_console_photo SET hors_vitrine_depuis = ancre, updated_at = avant
--    Or CE DECLENCHEUR-LA FORCE updated_at = now() SUR TOUT UPDATE. Il a donc
--    ecrase ma restauration, et le controle a conclu « l'essai n'a pas ete defait
--    proprement » -- ce qui etait VRAI.
--    ⭐ On ne peut pas defaire une ecriture EN ECRIVANT, a travers un declencheur
--      dont le role est precisement d'interdire cette ecriture. Le garde-fou a
--      echoue en PROUVANT que le declencheur marche.
--    -> La seule facon propre est d'ANNULER une SOUS-TRANSACTION : un bloc
--       BEGIN/EXCEPTION en PL/pgSQL en ouvre une, et l'exception la rejette. Les
--       donnees reviennent sans qu'aucun UPDATE ne soit rejoue ; les VARIABLES,
--       elles, survivent (elles ne sont pas transactionnelles) -- c'est ce qui
--       permet de lire le verdict apres l'annulation.
--    (Le patch refuse n'avait RIEN applique : tout etait dans le BEGIN/COMMIT,
--     l'exception a tout annule. Verifie : 0 declencheur, 0 fonction, 0 ligne.)
DO $$
DECLARE
  cible uuid; avant timestamptz; apres timestamptz; verdict text := 'NON MESURE';
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
     WHERE c.relname = 'app_console_photo'
       AND t.tgname = 'trg_app_console_photo_updated_at'
  ) THEN
    RAISE EXCEPTION 'Le declencheur n''a pas ete cree.';
  END IF;

  SELECT id, updated_at INTO cible, avant
    FROM public.app_console_photo
   WHERE updated_at < now() - interval '2 hours'
   ORDER BY id LIMIT 1;

  IF cible IS NULL THEN
    RAISE NOTICE 'Pas de ligne assez ancienne pour l''essai -- declencheur pose, non eprouve ici.';
    RETURN;
  END IF;

  -- ⭐ LA SOUS-TRANSACTION : tout ce qui s'ecrit ici sera ANNULE par l'exception.
  BEGIN
    -- le geste de app_photo_marquer_sortie_vitrine : hors_vitrine_depuis SEUL,
    -- sans toucher updated_at. C'est le cas que le declencheur doit rattraper.
    UPDATE public.app_console_photo SET hors_vitrine_depuis = now() WHERE id = cible;
    SELECT updated_at INTO apres FROM public.app_console_photo WHERE id = cible;
    verdict := CASE WHEN apres > avant THEN 'OK' ELSE 'ECHEC' END;
    RAISE EXCEPTION 'GTI_ESSAI_FINI';   -- rejette la sous-transaction
  EXCEPTION WHEN raise_exception THEN
    -- on n'avale QUE notre propre signal : toute autre erreur doit remonter
    IF SQLERRM <> 'GTI_ESSAI_FINI' THEN RAISE; END IF;
  END;

  IF verdict <> 'OK' THEN
    RAISE EXCEPTION 'ECHEC : updated_at n''a pas bouge (% -> %)', avant, apres;
  END IF;
  IF (SELECT updated_at FROM public.app_console_photo WHERE id = cible) <> avant THEN
    RAISE EXCEPTION 'L''essai n''a pas ete annule : la ligne porte encore sa trace.';
  END IF;

  RAISE NOTICE 'OK : le declencheur rattrape l''oubli (% -> %), essai ANNULE.', avant, apres;
END $$;

COMMIT;

-- ─── A LIRE APRES LE COMMIT ─────────────────────────────────────────────────────
-- SELECT tgname FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
--  WHERE c.relname='app_console_photo' AND NOT t.tgisinternal;
--   -> doit rendre exactement : trg_app_console_photo_updated_at
--
-- PUIS, et seulement apres, l'activation du delta cote serveur (une ligne) :
--   DELTA_HORODATAGE["app_console_photo"] = "updated_at"
-- Attendu a la descente suivante, dans le journal :
--   [NNN/150] app_console_photo    ~219 lignes  (delta)      au lieu de 437 044
