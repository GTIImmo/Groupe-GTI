-- =====================================================================
-- RETOUR ARRIERE de patch_chantier3_3d_lot2c_creer_document_2026-10-14.sql
-- Date : 2026-10-14
--
-- CE QU'IL FAIT : il retire les deux RPC. C'est tout, et c'est suffisant --
-- aucune table, aucune colonne, aucune politique n'a ete touchee par le patch.
--
-- ⭐ ET LE SYSTEME CONTINUE DE MARCHER SANS ELLES. Sans ces RPC, l'ecran ne peut
--   plus creer la ligne, donc le travail part SANS `app_document_id`, donc le worker
--   prend l'ancien chemin -- celui qui tourne depuis mai (121 envois sur 121 reussis).
--   On perd l'inversion « chez nous d'abord », on ne perd pas la fonction.
--
-- ⚠ MAIS IL REFUSE DE PARTIR S'IL RESTE DES LIGNES EN VOL. Une ligne
--   `storage_status = 'pending_upload'` est un fichier encore dans le dossier
--   temporaire, dont SEUL le worker (via `app_document_id`) sait finir le rangement.
--   Retirer la RPC pendant qu'il en reste ne casse rien -- mais si on retire AUSSI le
--   code du worker ensuite, ces fichiers resteraient en temp pour toujours. Le refus
--   force a regarder avant.
--   POUR PASSER QUAND MEME : attendre que le worker ait digere (quelques minutes),
--   ou mettre `v_forcer := true` ci-dessous en sachant ce qu'on fait.
-- =====================================================================

BEGIN;

DO $garde$
DECLARE
  v_forcer  boolean := false;   -- <-- mettre true pour passer outre, en connaissance
  v_docs    int;
  v_photos  int;
BEGIN
  SELECT count(*) INTO v_docs   FROM public.app_console_document
   WHERE storage_status = 'pending_upload' AND source = 'app';
  SELECT count(*) INTO v_photos FROM public.app_console_photo
   WHERE storage_status = 'pending_upload' AND source = 'app';

  RAISE NOTICE 'En vol : % document(s), % photo(s) en pending_upload.', v_docs, v_photos;

  IF (v_docs + v_photos) > 0 AND NOT v_forcer THEN
    RAISE EXCEPTION
      'STOP : % objet(s) attendent encore leur rangement par le worker. Attendre quelques minutes, ou mettre v_forcer := true.',
      v_docs + v_photos;
  END IF;
END $garde$;

DROP FUNCTION IF EXISTS public.app_console_creer_document_optimistic(uuid, bigint, text, text, text, text, bigint, text);
DROP FUNCTION IF EXISTS public.app_console_creer_photo_optimistic(uuid, bigint, text, text, text, bigint);

DO $ctrl$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM pg_proc p JOIN pg_namespace ns ON ns.oid = p.pronamespace
   WHERE ns.nspname = 'public'
     AND p.proname IN ('app_console_creer_document_optimistic','app_console_creer_photo_optimistic');
  IF n <> 0 THEN RAISE EXCEPTION 'STOP : % RPC restante(s)', n; END IF;
  RAISE NOTICE 'OK : les 2 RPC sont retirees. L''ancien chemin (celui de mai) reprend seul.';
END $ctrl$;

notify pgrst, 'reload schema';

COMMIT;
