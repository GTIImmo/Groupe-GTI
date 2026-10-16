-- ============================================================================
-- CHANTIER (7)-3c -- METTRE UNE PHOTO EN COUVERTURE
-- 16/10/2026
-- ============================================================================
-- LA DEMANDE. Frederic, 16/10 : « fais juste 1 » -- c'est-a-dire le geste
-- minimal : un clic sur une photo, elle passe en tete. Le glisser-deposer est
-- ecarte pour aujourd'hui (« le but est de finir le chantier 7 »).
--
-- ⭐ CE QUI EXISTAIT DEJA, ET QUI REND CE PATCH POSSIBLE :
--   La commande de Hektor (`mode=ordonne_photos`) est ECRITE ET EN PRODUCTION
--   dans le worker depuis le 14/10 -- elle sert a RENUMEROTER apres une
--   suppression (console_job_worker.js l. 8725-8745). Elle n'a jamais ete un
--   geste, seulement une consequence.
--   Et « photo principale » n'est pas une notion a part : c'est LA PREMIERE DE
--   LA LISTE. Reordonner et choisir la couverture sont LE MEME ordre.
--
-- ⚠⚠ LA MESURE QUI A EVITE UNE ERREUR SUR 47 584 ANNONCES. J'allais ecrire
--   « la couverture, c'est sort_order = 1 ». C'est FAUX : notre numerotation
--   commence a ZERO dans 97 % des cas (47 584 annonces sur 49 188 ; 1 561
--   commencent a 1 ; 37 commencent plus loin -- des listes A TROUS).
--   ➡ On ne cherche donc jamais « le rang 1 » : on RENUMEROTE la liste entiere,
--     de 0 a n-1. C'est aussi ce qui repare les 37 listes trouees au passage.
--
-- CE QUE CE PATCH POSE :
--   ① la contrainte des types connait `reorder_hektor_photos`
--   ② les droits : le NEGOCIATEUR sur SES biens -- ce n'est pas un choix de ma
--      part, c'est la regle que le projet applique deja aux deux autres gestes
--      photo (`upload_hektor_photo` et `delete_hektor_photo` sont dans la liste
--      du commercial, mesure du 16/10)
--   ③ la distribution : dans la branche `documents`, collee a ses deux soeurs
--      -- et PAS dans `actions` (mesure du 16/10 : c'est le worker documents qui
--      porte les photos)
--   ④ la RPC `app_console_photo_couverture_optimistic` : elle renumerote CHEZ
--      NOUS et cree le travail DANS LA MEME TRANSACTION, avec l'ordre d'avant
--      garde dans la charge. Patron de (7)-1 (archiver un contact).
--
-- ⚠ LE 4e VERROU EST DANS LE WORKER, PAS ICI : DOCUMENT_JOB_TYPES, le libelle,
--   la liste a notifier et le repartiteur. Un type absent de ces listes reste
--   « pending » POUR TOUJOURS, sans erreur (lecon du 03/10, repayee le 14/10).
--
-- EMPREINTES MESUREES LE 16/10 (sans retours chariot) :
--   contrainte   beacc240a7974dec70a876b717ed052b  (1 516 car.)
--   droits       d013972f13ce6f881aa0494c4529e3ae  (1 633 car.)
--   distribution 4da660742838e4e0849bbd70b7b9a7f5  (4 888 car.)
-- Dans les trois, `delete_hektor_photo` apparait EXACTEMENT UNE FOIS : c'est
-- notre ancre, et elle est verifiee avant chaque ecriture.
-- ANCRES MULTI-LIGNES : ZERO.
-- ============================================================================

BEGIN;

SET LOCAL lock_timeout = '5s';

-- ① LA CONTRAINTE DES TYPES
DO $contrainte$
DECLARE
  v_def   text;
  v_ancre text := replace('''delete_hektor_photo''::text])))', chr(13), '');
  v_neuf  text;
BEGIN
  SELECT pg_get_constraintdef(c.oid) INTO v_def
    FROM pg_constraint c
   WHERE c.conrelid = 'public.app_console_job'::regclass
     AND c.conname  = 'app_console_job_job_type_check';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : contrainte introuvable'; END IF;

  IF position('reorder_hektor_photos' in v_def) > 0 THEN
    RAISE NOTICE 'DEJA FAIT : la contrainte connait reorder_hektor_photos';
  ELSE
    IF md5(v_def) <> 'beacc240a7974dec70a876b717ed052b' THEN
      RAISE NOTICE 'ATTENTION : empreinte de contrainte % (attendue beacc240...) -- un autre type a ete ajoute depuis. On continue : l''ancre unique est le vrai garde-fou.', md5(v_def);
    END IF;
    IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
      RAISE EXCEPTION 'STOP : l''ancre de la contrainte n''est pas unique';
    END IF;
    v_neuf := replace(v_def, v_ancre,
      replace('''delete_hektor_photo''::text, ''reorder_hektor_photos''::text])))', chr(13), ''));
    EXECUTE 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
    EXECUTE 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check '
            || v_neuf || ' NOT VALID';
  END IF;
END $contrainte$;

-- ② LES DROITS : le negociateur sur SES biens, comme les deux autres gestes photo
DO $droits$
DECLARE
  v_def   text;
  v_ancre text := replace('''delete_hektor_photo'',', chr(13), '');
BEGIN
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_can_request_job';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : app_console_can_request_job introuvable'; END IF;

  IF position('reorder_hektor_photos' in v_def) > 0 THEN
    RAISE NOTICE 'DEJA FAIT : les droits connaissent reorder_hektor_photos';
    RETURN;
  END IF;
  IF md5(v_def) <> 'd013972f13ce6f881aa0494c4529e3ae' THEN
    RAISE NOTICE 'ATTENTION : empreinte des droits % (attendue d013972f...). On continue : l''ancre unique est le vrai garde-fou.', md5(v_def);
  END IF;
  IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre des droits n''est pas unique';
  END IF;
  EXECUTE replace(v_def, v_ancre,
    replace('''delete_hektor_photo'',''reorder_hektor_photos'',', chr(13), ''));
END $droits$;

-- ③ LA DISTRIBUTION : branche `documents`, collee a ses deux soeurs
DO $distribution$
DECLARE
  v_def   text;
  v_ancre text := replace('''delete_hektor_photo''', chr(13), '');
BEGIN
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_claim_next_job';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : app_console_claim_next_job introuvable'; END IF;

  IF position('reorder_hektor_photos' in v_def) > 0 THEN
    RAISE NOTICE 'DEJA FAIT : la distribution connait reorder_hektor_photos';
    RETURN;
  END IF;
  IF md5(v_def) <> '4da660742838e4e0849bbd70b7b9a7f5' THEN
    RAISE NOTICE 'ATTENTION : empreinte de la distribution % (attendue 4da66074...). On continue : l''ancre unique est le vrai garde-fou.', md5(v_def);
  END IF;
  IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre de la distribution n''est pas unique';
  END IF;
  EXECUTE replace(v_def, v_ancre,
    replace('''delete_hektor_photo'',''reorder_hektor_photos''', chr(13), ''));
END $distribution$;

-- ④ LA RPC : on renumerote CHEZ NOUS et on cree le travail, en une transaction
CREATE OR REPLACE FUNCTION public.app_console_photo_couverture_optimistic(
  p_app_dossier_id      bigint,
  p_hektor_annonce_id   text,
  p_hektor_photo_id     text
) RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $fn$
DECLARE
  v_annonce  text := nullif(btrim(coalesce(p_hektor_annonce_id, '')), '');
  v_photo    text := nullif(btrim(coalesce(p_hektor_photo_id, '')), '');
  v_avant    jsonb;
  v_premier  text;
  v_visibles jsonb;
  v_masquees jsonb;
  v_job_id   uuid;
  v_combien  integer;
BEGIN
  -- ⓵ DES PARAMETRES LISIBLES
  IF v_annonce IS NULL OR v_photo IS NULL OR p_app_dossier_id IS NULL THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'parametres_incomplets');
  END IF;

  -- ⓶ LES DROITS. On reutilise la garde du projet, celle qui sert deja a
  --    deposer et a supprimer une photo : le negociateur sur SES biens.
  IF NOT coalesce(public.app_console_can_access_dossier(p_app_dossier_id, v_annonce), false) THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'droits_insuffisants');
  END IF;

  -- ⓷ L'ETAT D'AVANT, garde dans la charge -- c'est le retour arriere.
  SELECT jsonb_agg(jsonb_build_object('hektor_photo_id', hektor_photo_id,
                                      'sort_order', sort_order,
                                      'visible', visible)
                   ORDER BY visible DESC, sort_order ASC, id ASC)
    INTO v_avant
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id
     AND present_in_hektor IS TRUE;

  -- ⓸ LA CIBLE DOIT EXISTER, ETRE CHEZ HEKTOR ET ETRE VISIBLE.
  --    ⚠ Une photo deposee par l'app et pas encore envoyee n'a pas de numero
  --      Hektor : la mettre en couverture n'aurait aucun sens tant que Hektor ne
  --      la connait pas. Meme refus que pour la suppression.
  IF NOT EXISTS (
    SELECT 1 FROM public.app_console_photo
     WHERE app_dossier_id = p_app_dossier_id
       AND hektor_photo_id = v_photo
       AND visible IS TRUE
       AND present_in_hektor IS TRUE
  ) THEN
    RETURN jsonb_build_object('ok', false, 'erreur', 'photo_introuvable_ou_masquee');
  END IF;

  -- ⓹ EST-ELLE DEJA EN COUVERTURE ? Alors on ne derange pas Hektor.
  SELECT hektor_photo_id INTO v_premier
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id
     AND visible IS TRUE
     AND present_in_hektor IS TRUE
   ORDER BY sort_order ASC, id ASC
   LIMIT 1;
  IF v_premier = v_photo THEN
    RETURN jsonb_build_object('ok', true, 'deja_en_couverture', true);
  END IF;

  -- ⓺ ON RENUMEROTE DE 0 A n-1. Jamais « le rang 1 » : notre numerotation
  --    commence a 0 dans 97 % des cas, et 37 annonces ont des TROUS.
  WITH ordonnees AS (
    SELECT id,
           (row_number() OVER (ORDER BY (hektor_photo_id = v_photo) DESC,
                                        sort_order ASC, id ASC) - 1)::integer AS rang
      FROM public.app_console_photo
     WHERE app_dossier_id = p_app_dossier_id
       AND visible IS TRUE
       AND present_in_hektor IS TRUE
  )
  UPDATE public.app_console_photo p
     SET sort_order = o.rang, updated_at = now()
    FROM ordonnees o
   WHERE o.id = p.id
     AND p.sort_order IS DISTINCT FROM o.rang;
  GET DIAGNOSTICS v_combien = ROW_COUNT;

  -- ⓻ LES DEUX LISTES QUE HEKTOR ATTEND. Sa page en tient DEUX : les visibles
  --    (`liste_photos`) et les masquees (`liste_photos_hidden`). On lui renvoie
  --    les deux, les masquees dans leur ordre inchange.
  SELECT coalesce(jsonb_agg(hektor_photo_id ORDER BY sort_order ASC, id ASC), '[]'::jsonb)
    INTO v_visibles
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id AND visible IS TRUE AND present_in_hektor IS TRUE;

  SELECT coalesce(jsonb_agg(hektor_photo_id ORDER BY sort_order ASC, id ASC), '[]'::jsonb)
    INTO v_masquees
    FROM public.app_console_photo
   WHERE app_dossier_id = p_app_dossier_id AND visible IS FALSE AND present_in_hektor IS TRUE;

  -- ⓼ LE TRAVAIL, DANS LA MEME TRANSACTION. Si l'insertion echoue, la
  --    renumerotation est annulee avec elle : on ne reste jamais avec un ordre
  --    change chez nous et rien de parti chez Hektor.
  INSERT INTO public.app_console_job
    (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  VALUES
    ('reorder_hektor_photos', p_app_dossier_id, v_annonce,
     jsonb_build_object(
       'motif', 'couverture',
       'hektor_photo_id', v_photo,
       'liste_photos', v_visibles,
       'liste_photos_hidden', v_masquees,
       'base_snapshot', coalesce(v_avant, '[]'::jsonb)),
     20, auth.uid())
  RETURNING id INTO v_job_id;

  RETURN jsonb_build_object(
    'ok', true,
    'deja_en_couverture', false,
    'job_id', v_job_id,
    'photos_renumerotees', v_combien,
    'visibles', jsonb_array_length(v_visibles),
    'masquees', jsonb_array_length(v_masquees));
END $fn$;

REVOKE ALL ON FUNCTION public.app_console_photo_couverture_optimistic(bigint, text, text) FROM public;
GRANT EXECUTE ON FUNCTION public.app_console_photo_couverture_optimistic(bigint, text, text)
  TO authenticated, service_role;

COMMENT ON FUNCTION public.app_console_photo_couverture_optimistic(bigint, text, text) IS
  '(7)-3c (16/10/2026) : met une photo en couverture. Renumerote NOS photos de 0 a n-1 '
  'et cree le travail reorder_hektor_photos dans la meme transaction, avec l''ordre '
  'd''avant dans base_snapshot. Garde : app_console_can_access_dossier (le negociateur '
  'sur ses biens, comme deposer et supprimer une photo).';

-- ⑤ LE CONTROLE DE SORTIE
DO $ctrl$
DECLARE v_c text; v_d text; v_x text; v_acl text;
BEGIN
  SELECT pg_get_constraintdef(oid) INTO v_c FROM pg_constraint
   WHERE conrelid = 'public.app_console_job'::regclass AND conname = 'app_console_job_job_type_check';
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_d FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_console_can_request_job';
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_x FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_console_claim_next_job';
  SELECT array_to_string(p.proacl, ' | ') INTO v_acl FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_console_photo_couverture_optimistic';

  IF position('''reorder_hektor_photos''::text' in v_c) = 0 THEN
    RAISE EXCEPTION 'STOP : la contrainte ne connait pas reorder_hektor_photos';
  END IF;
  IF position('''delete_hektor_photo'',''reorder_hektor_photos''' in v_d) = 0 THEN
    RAISE EXCEPTION 'STOP : les droits ne connaissent pas reorder_hektor_photos';
  END IF;
  IF position('''delete_hektor_photo'',''reorder_hektor_photos''' in v_x) = 0 THEN
    RAISE EXCEPTION 'STOP : la distribution ne connait pas reorder_hektor_photos';
  END IF;
  -- ⚠ Il doit etre dans la branche `documents`, PAS dans `actions` : c'est le
  --   worker documents qui porte les photos (mesure du 16/10).
  IF position('''sync_hektor_photos'',''upload_hektor_photo'',''delete_hektor_photo'',''reorder_hektor_photos''' in v_x) = 0 THEN
    RAISE EXCEPTION 'STOP : reorder_hektor_photos n''est pas colle a ses deux soeurs dans la branche documents';
  END IF;
  IF v_acl IS NULL OR position('authenticated=X' in v_acl) = 0 THEN
    RAISE EXCEPTION 'STOP : authenticated n''a pas l''execute sur la RPC (%)', coalesce(v_acl, '(aucun)');
  END IF;
  IF position('anon=' in v_acl) > 0 THEN
    RAISE EXCEPTION 'STOP : anon a un droit sur la RPC (%)', v_acl;
  END IF;

  RAISE NOTICE 'OK : reorder_hektor_photos est permis (negociateur sur ses biens), distribue au worker documents, et la RPC de couverture est posee.';
END $ctrl$;

COMMIT;

-- ⑥ HORS TRANSACTION : la validation de la contrainte, sous verrou LEGER.
ALTER TABLE public.app_console_job VALIDATE CONSTRAINT app_console_job_job_type_check;
