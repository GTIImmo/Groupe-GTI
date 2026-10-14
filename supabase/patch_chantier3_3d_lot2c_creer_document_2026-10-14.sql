-- =====================================================================
-- CHANTIER ③ -- 3d / LOT 2c : UN DOCUMENT (ET UNE PHOTO) EXISTE CHEZ NOUS
--                             AVANT QUE HEKTOR AIT REPONDU
-- Date : 2026-10-14 · Detail : notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md
--
-- LA DERNIERE PIECE D'UN TRAVAIL COMMENCE LE 25/09, ET LAISSEE EN PLAN.
--   Lot 1  (7428303) le worker : un DOCUMENT existe sans que Hektor ait repondu
--   Lot 2a (db5c38c) la jumelle PHOTO
--   Lot 2b (ec838b2) le repreneur des envois restes en attente
--   Lot 2c            LE FRONT -- JAMAIS FAIT
-- Les messages des lots 1 et 2a finissent tous deux par « ⛔ RESTE : le repassage,
-- et le front (lot 2c) ». Le 2b a ete fait le soir meme ; le 2c, jamais.
--
-- CE QUI DORT, ET POURQUOI. `completerEnvoiDocumentDiffere()` fait deja l'inversion :
--      ① NOTRE SERVEUR D'ABORD. C'est l'inversion.
--      ② HEKTOR ENSUITE, et son silence n'efface rien.
--   Si Hektor refuse, la ligne est marquee « echec » et NOTRE COPIE RESTE. Mais ce
--   chemin n'est pris que si la charge du travail porte `app_document_id` -- et
--   PERSONNE ne le pose, parce que le front ne peut pas creer la ligne : mesure du
--   14/10, `app_console_document` et `app_console_photo` n'ont qu'UNE politique
--   chacune, SELECT.
--   ⚠ Verifie aujourd'hui : le test `Console/test_envoi_hektor_differe.js` est TOUT
--     VERT (25 controles) malgre trois semaines de changements dans le worker. Le code
--     dormant n'a pas pourri.
--
-- CE QUE FAIT CE PATCH : deux RPC `SECURITY DEFINER`, une par objet, qui creent la
-- ligne chez nous ET posent `app_document_id` / `app_photo_id` dans la charge du
-- travail, DANS LA MEME TRANSACTION. L'une sans l'autre serait pire que rien : une
-- ligne orpheline, ou un travail qui pointe vers du vide.
--
-- ⚠⚠ DEUX GARDES, PAS UNE -- et c'est plus strict que le patron d'origine.
--   ① L'ACCES AU DOSSIER : `app_console_can_access_dossier`, recopiee SANS L'ALLEGER
--      du patron `app_console_mark_document_signed_manual` (27/07). Lu le 14/10, elle
--      fait DEJA ce que Frederic a demande : admin/manager -> tout ; commercial ->
--      SEULEMENT si `negociateur_email` est le sien (parc vivant, archive, historique) ;
--      inactif ou autre -> refuse. ⭐ « Interdire a un negociateur de deposer sur le
--      bien d'un autre » etait deja la regle : il n'y avait rien a ajouter.
--   ② L'ACCES AU TRAVAIL : patron de `app_console_fail_own_pending_job` --
--      `status = 'pending'` ET `requested_by = auth.uid()`. On ne complete QUE son
--      propre travail, et seulement s'il attend encore.
--
-- ⭐ ET ON NE FAIT PAS CONFIANCE AU CLIENT POUR LE CHEMIN DU FICHIER. On le LIT dans
--   la charge du travail (`temp_storage_path`), ou le front l'avait pose avant de
--   deposer -- et ou la politique de storage l'a deja lie a cet utilisateur :
--     temp/uploads/<id-du-travail>/...  avec le travail pending ET requested_by = lui.
--   Le client ne nous dit donc jamais ou chercher un fichier.
--
-- ⚠ LE REPLI EST NATUREL ET SUR : si cette RPC n'est pas appelee, ou echoue, le
--   travail reste SANS `app_document_id` -> le worker prend L'ANCIEN CHEMIN, celui qui
--   tourne depuis mai (121 ajouts sur 121 reussis). RIEN NE REGRESSE.
--
-- CE QUI NE CHANGE PAS : aucune table, aucune colonne (celles du lot 1 existent depuis
-- le 25/09) · aucune politique de storage · l'ancien chemin du worker · le run.
--
-- RETOUR ARRIERE : supabase/patch_chantier3_3d_lot2c_creer_document_2026-10-14_INVERSE.sql
-- REPETITION     : supabase/patch_chantier3_3d_lot2c_creer_document_2026-10-14_REPETITION.sql
-- ⚠ NE LE COLLER QU'UNE SEULE FOIS (le succes est un NOTICE, invisible dans l'editeur).
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. LE DOCUMENT
-- ---------------------------------------------------------------------
create or replace function public.app_console_creer_document_optimistic(
  target_job_id            uuid,
  target_app_dossier_id    bigint,
  target_hektor_annonce_id text,
  nom_du_document          text,
  type_de_document         text   default null,
  visibilite               text   default 'private',
  taille_octets            bigint default null,
  type_mime                text   default null
) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $fn$
DECLARE
  v_annonce  text := nullif(btrim(coalesce(target_hektor_annonce_id, '')), '');
  v_nom      text := nullif(btrim(coalesce(nom_du_document, '')), '');
  v_vis      text := case when visibilite = 'shared' then 'shared' else 'private' end;
  v_charge   jsonb;
  v_chemin   text;
  v_coffre   text;
  v_id       uuid;
BEGIN
  IF v_annonce IS NULL OR v_nom IS NULL THEN
    RAISE EXCEPTION 'parametres_incomplets';
  END IF;

  -- ① LA GARDE DU DOSSIER.
  IF NOT public.app_console_can_access_dossier(target_app_dossier_id, v_annonce) THEN
    RAISE EXCEPTION 'dossier_not_found_or_forbidden';
  END IF;

  -- ② LA GARDE DU TRAVAIL, et on en profite pour LIRE le chemin a la source.
  SELECT j.payload_json INTO v_charge
    FROM public.app_console_job j
   WHERE j.id = target_job_id
     AND j.status = 'pending'
     AND j.requested_by = auth.uid()
     AND j.job_type = 'upload_document_to_hektor'
     AND j.hektor_annonce_id = v_annonce;
  IF NOT found THEN
    RAISE EXCEPTION 'job_not_found_or_forbidden';
  END IF;

  v_chemin := nullif(btrim(coalesce(v_charge ->> 'temp_storage_path', '')), '');
  v_coffre := nullif(btrim(coalesce(v_charge ->> 'temp_storage_bucket', '')), '');
  IF v_chemin IS NULL THEN
    RAISE EXCEPTION 'chemin_du_fichier_absent_de_la_charge';
  END IF;

  -- ⚠ IDEMPOTENT : si la ligne existe deja pour ce travail, on la rend au lieu d'en
  --   creer une seconde. Un double clic, un reseau qui rejoue, et on aurait deux
  --   documents pour un fichier.
  IF (v_charge ->> 'app_document_id') IS NOT NULL THEN
    RETURN jsonb_build_object('ok', true, 'app_document_id', v_charge ->> 'app_document_id',
                              'deja_cree', true);
  END IF;

  -- ③ LA LIGNE. `storage_status='pending_upload'` dit au worker que ce chemin est
  --    TEMPORAIRE et qu'il doit ranger le fichier a sa place definitive.
  --    ⚠ `hektor_document_id` reste NULL -- c'est ce qui fait qu'elle SURVIT a la
  --      synchro de nuit (regle identifiee le 25/09 comme « le risque principal »,
  --      et verifiee le 14/10 : le marquage « plus chez Hektor » de 3e ignore les
  --      lignes sans numero Hektor).
  INSERT INTO public.app_console_document
    (app_dossier_id, hektor_annonce_id, document_name, document_type, visibility,
     source, storage_bucket, storage_path, storage_status, file_size, mime_type,
     envoi_hektor_statut, metadata_json)
  VALUES
    (target_app_dossier_id, v_annonce, v_nom, nullif(btrim(coalesce(type_de_document,'')),''),
     v_vis, 'app', v_coffre, v_chemin, 'pending_upload', taille_octets,
     nullif(btrim(coalesce(type_mime,'')),''),
     'a_envoyer',
     jsonb_build_object('cree_par_app', true, 'cree_le',
                        to_char(now() at time zone 'Europe/Paris', 'YYYY-MM-DD"T"HH24:MI:SS')))
  RETURNING id INTO v_id;

  -- ④ ET LE TRAVAIL APPREND QU'IL A UNE LIGNE. C'est ce qui allume le chemin differe.
  UPDATE public.app_console_job
     SET payload_json = coalesce(payload_json, '{}'::jsonb)
                        || jsonb_build_object('app_document_id', v_id),
         updated_at = now()
   WHERE id = target_job_id;

  RETURN jsonb_build_object('ok', true, 'app_document_id', v_id, 'deja_cree', false);
END $fn$;

revoke all on function public.app_console_creer_document_optimistic(uuid, bigint, text, text, text, text, bigint, text) from public;
grant execute on function public.app_console_creer_document_optimistic(uuid, bigint, text, text, text, text, bigint, text) to authenticated;

comment on function public.app_console_creer_document_optimistic(uuid, bigint, text, text, text, text, bigint, text) is
  'Chantier 3d / lot 2c, 14/10/2026. Cree la ligne du document CHEZ NOUS et pose '
  'app_document_id dans la charge du travail, dans la MEME transaction -- ce qui allume '
  'le chemin differe du worker (notre serveur d''abord, Hektor ensuite). DEUX gardes : '
  'app_console_can_access_dossier, et le travail doit etre pending ET a l''appelant. '
  'Le chemin du fichier est LU dans la charge, jamais fourni par le client.';

-- ---------------------------------------------------------------------
-- 2. LA PHOTO -- meme forme, meme gardes
--
-- ⚠ `present_in_hektor` garde son defaut `true` : le mettre a `false` ferait afficher
--   « supprimee chez Hektor » (3e) sur une photo qui attend simplement son envoi. La
--   verite de l'envoi est portee par `envoi_hektor_statut`, pas par cette colonne.
-- ---------------------------------------------------------------------
create or replace function public.app_console_creer_photo_optimistic(
  target_job_id            uuid,
  target_app_dossier_id    bigint,
  target_hektor_annonce_id text,
  nom_du_fichier           text,
  legende                  text   default null,
  taille_octets            bigint default null
) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $fn$
DECLARE
  v_annonce text := nullif(btrim(coalesce(target_hektor_annonce_id, '')), '');
  v_nom     text := nullif(btrim(coalesce(nom_du_fichier, '')), '');
  v_charge  jsonb;
  v_chemin  text;
  v_coffre  text;
  v_id      uuid;
BEGIN
  IF v_annonce IS NULL OR v_nom IS NULL THEN
    RAISE EXCEPTION 'parametres_incomplets';
  END IF;

  IF NOT public.app_console_can_access_dossier(target_app_dossier_id, v_annonce) THEN
    RAISE EXCEPTION 'dossier_not_found_or_forbidden';
  END IF;

  SELECT j.payload_json INTO v_charge
    FROM public.app_console_job j
   WHERE j.id = target_job_id
     AND j.status = 'pending'
     AND j.requested_by = auth.uid()
     AND j.job_type = 'upload_hektor_photo'
     AND j.hektor_annonce_id = v_annonce;
  IF NOT found THEN
    RAISE EXCEPTION 'job_not_found_or_forbidden';
  END IF;

  v_chemin := nullif(btrim(coalesce(v_charge ->> 'temp_storage_path', '')), '');
  v_coffre := nullif(btrim(coalesce(v_charge ->> 'temp_storage_bucket', '')), '');
  IF v_chemin IS NULL THEN
    RAISE EXCEPTION 'chemin_du_fichier_absent_de_la_charge';
  END IF;

  IF (v_charge ->> 'app_photo_id') IS NOT NULL THEN
    RETURN jsonb_build_object('ok', true, 'app_photo_id', v_charge ->> 'app_photo_id',
                              'deja_cree', true);
  END IF;

  INSERT INTO public.app_console_photo
    (app_dossier_id, hektor_annonce_id, filename, legend, source,
     storage_bucket, storage_path, storage_status, file_size,
     envoi_hektor_statut, source_json)
  VALUES
    (target_app_dossier_id, v_annonce, v_nom, nullif(btrim(coalesce(legende,'')),''), 'app',
     v_coffre, v_chemin, 'pending_upload', taille_octets, 'a_envoyer',
     jsonb_build_object('cree_par_app', true, 'cree_le',
                        to_char(now() at time zone 'Europe/Paris', 'YYYY-MM-DD"T"HH24:MI:SS')))
  RETURNING id INTO v_id;

  UPDATE public.app_console_job
     SET payload_json = coalesce(payload_json, '{}'::jsonb)
                        || jsonb_build_object('app_photo_id', v_id),
         updated_at = now()
   WHERE id = target_job_id;

  RETURN jsonb_build_object('ok', true, 'app_photo_id', v_id, 'deja_cree', false);
END $fn$;

revoke all on function public.app_console_creer_photo_optimistic(uuid, bigint, text, text, text, bigint) from public;
grant execute on function public.app_console_creer_photo_optimistic(uuid, bigint, text, text, text, bigint) to authenticated;

comment on function public.app_console_creer_photo_optimistic(uuid, bigint, text, text, text, bigint) is
  'Chantier 3d / lot 2c, 14/10/2026. Jumelle photo de '
  'app_console_creer_document_optimistic : memes deux gardes, meme transaction, et '
  'present_in_hektor garde son defaut true (le mettre a false ferait afficher '
  '« supprimee chez Hektor » sur une photo qui attend juste son envoi).';

-- ---------------------------------------------------------------------
-- 3. LE CONTROLE DE SORTIE
-- ---------------------------------------------------------------------
DO $ctrl$
DECLARE n int; v_acl text;
BEGIN
  SELECT count(*) INTO n FROM pg_proc p JOIN pg_namespace ns ON ns.oid = p.pronamespace
   WHERE ns.nspname = 'public'
     AND p.proname IN ('app_console_creer_document_optimistic','app_console_creer_photo_optimistic');
  IF n <> 2 THEN RAISE EXCEPTION 'STOP : % RPC posee(s) au lieu de 2', n; END IF;

  -- ⚠ On relit les droits : un « revoke from public » n'enleve PAS un droit par defaut
  --   (lecon du 13/10). `anon` ne doit RIEN avoir.
  FOR v_acl IN
    SELECT array_to_string(p.proacl, ' | ') FROM pg_proc p
      JOIN pg_namespace ns ON ns.oid = p.pronamespace
     WHERE ns.nspname = 'public'
       AND p.proname IN ('app_console_creer_document_optimistic','app_console_creer_photo_optimistic')
  LOOP
    IF v_acl LIKE '%anon=%' THEN RAISE EXCEPTION 'STOP : anon a un droit (%)', v_acl; END IF;
    IF v_acl NOT LIKE '%authenticated=X%' THEN
      RAISE EXCEPTION 'STOP : authenticated n''a pas l''execute (%) -- l''ecran ne pourrait pas appeler', v_acl;
    END IF;
  END LOOP;

  RAISE NOTICE 'OK : 2 RPC posees, authenticated seulement, anon exclu.';
END $ctrl$;

notify pgrst, 'reload schema';

COMMIT;
