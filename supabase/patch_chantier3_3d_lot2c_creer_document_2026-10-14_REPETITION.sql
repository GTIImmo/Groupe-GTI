-- =====================================================================
-- REPETITION du patch 3d / lot 2c -- RIEN NE RESTE
-- Date : 2026-10-14
--
-- A COLLER DANS L'EDITEUR SQL. Elle fait tout pour de vrai -- elle pose les RPC, elle
-- cree des lignes, elle eprouve les refus, elle retire les RPC -- puis elle ANNULE TOUT
-- par une levee volontaire a la fin. L'editeur affichera une ERREUR : c'est le SUCCES.
-- Le tableau des epreuves est dans le message de cette erreur.
--
-- CE QU'ELLE PROUVE, EN 15 EPREUVES :
--   ① les 2 RPC se posent, authenticated a l'execute, anon n'a RIEN
--   ② un depot AUTORISE passe : la ligne existe, le travail porte app_document_id
--   ③ ⭐ LE DEPOT EST IDEMPOTENT : le meme appel deux fois ne cree PAS deux documents
--   ④ ⭐⭐ UN DEPOT SUR LE BIEN D'UN AUTRE EST REFUSE (la demande de Frederic)
--   ⑤ le travail de QUELQU'UN D'AUTRE est refuse
--   ⑥ un travail DEJA FINI est refuse
--   ⑦ une charge SANS CHEMIN DE FICHIER est refusee
--   ⑧ ⭐ LE CLIENT NE CHOISIT PAS LE CHEMIN : la ligne porte celui de la charge
--   ⑨ anon est refuse (par les droits, avant meme la premiere garde)
--   ⑩ la photo : un depot autorise passe, un depot etranger est refuse
--   ⑪ ⭐ L'INVERSE REFUSE de partir tant qu'un objet est en vol
--   ⑫ le travail porte app_document_id -- C'EST LUI QUI ALLUME LE CHEMIN DIFFERE
--   ⑬ apres le retrait, plus aucune RPC
--   ⑭ TEMOIN INVERSE : les comptes sont EXACTEMENT ceux du depart
--
-- ⚠ LES TEMOINS SONT FIGES AVANT LES EPREUVES (lecon du 13/10 : mon temoin lisait une
--   table que l'epreuve modifiait, et rendait 117 / 117 / 118).
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout = '120s';

-- ---------------------------------------------------------------------
-- 0. LES TEMOINS, FIGES
-- ---------------------------------------------------------------------
CREATE TEMP TABLE _t_avant AS
SELECT (SELECT count(*) FROM public.app_console_document)                        AS docs,
       (SELECT count(*) FROM public.app_console_photo)                           AS photos,
       (SELECT count(*) FROM public.app_console_job)                             AS travaux,
       (SELECT count(*) FROM public.app_console_document
         WHERE storage_status = 'pending_upload')                                AS docs_en_vol,
       (SELECT count(*) FROM public.app_console_photo
         WHERE storage_status = 'pending_upload')                                AS photos_en_vol,
       (SELECT count(*) FROM public.app_console_job
         WHERE payload_json ? 'app_document_id')                                 AS travaux_portant_doc;

CREATE TEMP TABLE _res (n int, titre text, attendu text, obtenu text, ok boolean);

-- ⚠ INDISPENSABLE : une table temporaire n'appartient qu'a son createur. Sans ces
--   droits, le premier « INSERT INTO _res » fait APRES l'emprunt d'identite partirait
--   en « permission denied », et l'epreuve mourrait au lieu de mesurer.
GRANT ALL ON _res, _t_avant TO authenticated, anon;

-- ---------------------------------------------------------------------
-- 1. LE PATCH, TEL QUEL
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

  IF NOT public.app_console_can_access_dossier(target_app_dossier_id, v_annonce) THEN
    RAISE EXCEPTION 'dossier_not_found_or_forbidden';
  END IF;

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

  IF (v_charge ->> 'app_document_id') IS NOT NULL THEN
    RETURN jsonb_build_object('ok', true, 'app_document_id', v_charge ->> 'app_document_id',
                              'deja_cree', true);
  END IF;

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

  UPDATE public.app_console_job
     SET payload_json = coalesce(payload_json, '{}'::jsonb)
                        || jsonb_build_object('app_document_id', v_id),
         updated_at = now()
   WHERE id = target_job_id;

  RETURN jsonb_build_object('ok', true, 'app_document_id', v_id, 'deja_cree', false);
END $fn$;

revoke all on function public.app_console_creer_document_optimistic(uuid, bigint, text, text, text, text, bigint, text) from public;
grant execute on function public.app_console_creer_document_optimistic(uuid, bigint, text, text, text, text, bigint, text) to authenticated;

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

notify pgrst, 'reload schema';

-- ---------------------------------------------------------------------
-- 2. LES EPREUVES
-- ---------------------------------------------------------------------
DO $ep$
DECLARE
  -- Les deux identites, relevees en lecture seule le 14/10.
  v_admin      uuid := 'd4b1685f-948b-4ce8-af15-671b94a725e6';  -- frederic, admin
  v_commercial uuid := '05beded4-3e17-4a0c-ab58-e2c63da3da24';  -- legrand, commercial
  -- Le bien d'un AUTRE negociateur (forlico) : l'epreuve du refus.
  v_autre_ann  text   := '5';
  v_autre_dos  bigint := 1096848;
  -- Le bac a sable du projet (ecarte des mesures, cf. CLAUDE.md lecon 18).
  v_bac_ann    text := '62774';
  v_bac_dos    bigint;
  v_acl        text;
  v_j_ok       uuid; v_j_ok2 uuid; v_j_autrui uuid; v_j_fini uuid;
  v_j_sans     uuid; v_j_etranger uuid; v_j_photo uuid; v_j_photo_etr uuid;
  v_r          jsonb; v_r2 jsonb;
  v_doc_id     uuid;
  v_chemin     text;
  v_n          int;
  v_msg        text;
BEGIN
  SELECT app_dossier_id INTO v_bac_dos FROM public.app_annonces_current
   WHERE hektor_annonce_id::text = v_bac_ann LIMIT 1;
  IF v_bac_dos IS NULL THEN
    RAISE EXCEPTION 'STOP : le bac a sable 62774 est introuvable dans app_annonces_current';
  END IF;

  -- ===== ① les droits =====
  SELECT array_to_string(p.proacl, ' | ') INTO v_acl
    FROM pg_proc p JOIN pg_namespace ns ON ns.oid = p.pronamespace
   WHERE ns.nspname='public' AND p.proname='app_console_creer_document_optimistic';
  INSERT INTO _res VALUES (1, 'les droits : authenticated oui, anon non',
    'authenticated=X, pas de anon',
    CASE WHEN v_acl LIKE '%authenticated=X%' AND v_acl NOT LIKE '%anon=%'
         THEN 'conforme' ELSE 'NON CONFORME : ' || coalesce(v_acl,'(vide)') END,
    v_acl LIKE '%authenticated=X%' AND v_acl NOT LIKE '%anon=%');

  -- ===== les travaux d'epreuve, poses en tant que postgres =====
  v_chemin := 'temp/uploads/' || gen_random_uuid()::text || '/epreuve.pdf';

  INSERT INTO public.app_console_job (job_type, status, requested_by, hektor_annonce_id,
                                      app_dossier_id, payload_json)
  VALUES ('upload_document_to_hektor','pending', v_admin, v_bac_ann, v_bac_dos,
          jsonb_build_object('temp_storage_path', v_chemin,
                             'temp_storage_bucket','gti-doc',
                             'original_filename','epreuve.pdf'))
  RETURNING id INTO v_j_ok;

  INSERT INTO public.app_console_job (job_type, status, requested_by, hektor_annonce_id,
                                      app_dossier_id, payload_json)
  VALUES ('upload_document_to_hektor','pending', v_admin, v_autre_ann, v_autre_dos,
          jsonb_build_object('temp_storage_path','temp/uploads/x/a.pdf',
                             'temp_storage_bucket','gti-doc'))
  RETURNING id INTO v_j_etranger;

  INSERT INTO public.app_console_job (job_type, status, requested_by, hektor_annonce_id,
                                      app_dossier_id, payload_json)
  VALUES ('upload_document_to_hektor','pending', v_commercial, v_bac_ann, v_bac_dos,
          jsonb_build_object('temp_storage_path','temp/uploads/y/b.pdf',
                             'temp_storage_bucket','gti-doc'))
  RETURNING id INTO v_j_autrui;

  INSERT INTO public.app_console_job (job_type, status, requested_by, hektor_annonce_id,
                                      app_dossier_id, payload_json)
  VALUES ('upload_document_to_hektor','done', v_admin, v_bac_ann, v_bac_dos,
          jsonb_build_object('temp_storage_path','temp/uploads/z/c.pdf',
                             'temp_storage_bucket','gti-doc'))
  RETURNING id INTO v_j_fini;

  INSERT INTO public.app_console_job (job_type, status, requested_by, hektor_annonce_id,
                                      app_dossier_id, payload_json)
  VALUES ('upload_document_to_hektor','pending', v_admin, v_bac_ann, v_bac_dos,
          jsonb_build_object('original_filename','sans_chemin.pdf'))
  RETURNING id INTO v_j_sans;

  INSERT INTO public.app_console_job (job_type, status, requested_by, hektor_annonce_id,
                                      app_dossier_id, payload_json)
  VALUES ('upload_hektor_photo','pending', v_admin, v_bac_ann, v_bac_dos,
          jsonb_build_object('temp_storage_path','temp/photos/p1/img.jpg',
                             'temp_storage_bucket','gti-doc'))
  RETURNING id INTO v_j_photo;

  INSERT INTO public.app_console_job (job_type, status, requested_by, hektor_annonce_id,
                                      app_dossier_id, payload_json)
  VALUES ('upload_hektor_photo','pending', v_commercial, v_autre_ann, v_autre_dos,
          jsonb_build_object('temp_storage_path','temp/photos/p2/img.jpg',
                             'temp_storage_bucket','gti-doc'))
  RETURNING id INTO v_j_photo_etr;

  -- ===================================================================
  -- ON DEVIENT L'ADMIN (lecon 4 : emprunter l'identite, sans mot de passe)
  -- ===================================================================
  PERFORM set_config('role', 'authenticated', true);
  PERFORM set_config('request.jwt.claims',
    json_build_object('sub', v_admin::text, 'role','authenticated')::text, true);

  -- ===== ② un depot autorise =====
  BEGIN
    v_r := public.app_console_creer_document_optimistic(
             v_j_ok, v_bac_dos, v_bac_ann, 'Epreuve 3d.pdf', 'autre', 'private', 1234, 'application/pdf');
    v_doc_id := (v_r ->> 'app_document_id')::uuid;
    INSERT INTO _res VALUES (2, 'un depot AUTORISE passe', 'ok=true, deja_cree=false',
      v_r::text, (v_r ->> 'ok') = 'true' AND (v_r ->> 'deja_cree') = 'false');
  EXCEPTION WHEN others THEN
    INSERT INTO _res VALUES (2, 'un depot AUTORISE passe', 'ok=true',
      'LEVEE : ' || SQLERRM, false);
  END;


  -- ⚠ ON REDEVIENT SOI-MEME POUR MESURER. Sous l'identite empruntee, ces lectures
  --   passeraient par la RLS de app_console_document : une politique restrictive
  --   rendrait 0 ligne sur une ligne qui EXISTE, et l'epreuve raterait a tort.
  PERFORM set_config('role', 'none', true);
  -- ===== ⑧ le chemin vient de la CHARGE, pas du client =====
  SELECT storage_path INTO v_msg FROM public.app_console_document WHERE id = v_doc_id;
  INSERT INTO _res VALUES (8, 'le chemin du fichier est LU dans la charge',
    v_chemin, coalesce(v_msg,'(aucune ligne)'), v_msg = v_chemin);

  -- la charge porte-t-elle le numero de la ligne ?
  SELECT payload_json ->> 'app_document_id' INTO v_msg
    FROM public.app_console_job WHERE id = v_j_ok;
  INSERT INTO _res VALUES (15, 'le travail porte app_document_id (c''est ca qui allume le chemin differe)',
    v_doc_id::text, coalesce(v_msg,'(absent)'), v_msg = v_doc_id::text);

  -- et on reprend l'identite de l'admin pour la suite des appels
  PERFORM set_config('role', 'authenticated', true);

  -- ===== ③ idempotence =====
  BEGIN
    v_r2 := public.app_console_creer_document_optimistic(
              v_j_ok, v_bac_dos, v_bac_ann, 'Epreuve 3d.pdf', 'autre', 'private', 1234, 'application/pdf');
    PERFORM set_config('role', 'none', true);   -- mesurer sans la RLS (cf. ci-dessus)
    SELECT count(*) INTO v_n FROM public.app_console_document
     WHERE hektor_annonce_id = v_bac_ann AND storage_status = 'pending_upload';
    INSERT INTO _res VALUES (3, 'le MEME appel deux fois ne cree pas deux documents',
      'deja_cree=true et 1 seule ligne',
      format('deja_cree=%s, lignes=%s', v_r2 ->> 'deja_cree', v_n),
      (v_r2 ->> 'deja_cree') = 'true' AND v_n = 1);
    PERFORM set_config('role', 'authenticated', true);
  EXCEPTION WHEN others THEN
    PERFORM set_config('role', 'authenticated', true);
    INSERT INTO _res VALUES (3, 'le MEME appel deux fois ne cree pas deux documents',
      'deja_cree=true', 'LEVEE : ' || SQLERRM, false);
  END;

  -- ===== ⑥ un travail DEJA FINI =====
  BEGIN
    PERFORM public.app_console_creer_document_optimistic(v_j_fini, v_bac_dos, v_bac_ann, 'fini.pdf');
    INSERT INTO _res VALUES (6, 'un travail DEJA FINI est refuse', 'refus', 'ACCEPTE (defaut)', false);
  EXCEPTION WHEN others THEN
    INSERT INTO _res VALUES (6, 'un travail DEJA FINI est refuse', 'refus',
      'refuse : ' || SQLERRM, SQLERRM LIKE '%job_not_found_or_forbidden%');
  END;

  -- ===== ⑤ le travail de QUELQU'UN D'AUTRE =====
  BEGIN
    PERFORM public.app_console_creer_document_optimistic(v_j_autrui, v_bac_dos, v_bac_ann, 'autrui.pdf');
    INSERT INTO _res VALUES (5, 'le travail de QUELQU''UN D''AUTRE est refuse', 'refus', 'ACCEPTE (defaut)', false);
  EXCEPTION WHEN others THEN
    INSERT INTO _res VALUES (5, 'le travail de QUELQU''UN D''AUTRE est refuse', 'refus',
      'refuse : ' || SQLERRM, SQLERRM LIKE '%job_not_found_or_forbidden%');
  END;

  -- ===== ⑦ une charge SANS CHEMIN =====
  BEGIN
    PERFORM public.app_console_creer_document_optimistic(v_j_sans, v_bac_dos, v_bac_ann, 'sans.pdf');
    INSERT INTO _res VALUES (7, 'une charge SANS CHEMIN de fichier est refusee', 'refus', 'ACCEPTE (defaut)', false);
  EXCEPTION WHEN others THEN
    INSERT INTO _res VALUES (7, 'une charge SANS CHEMIN de fichier est refusee', 'refus',
      'refuse : ' || SQLERRM, SQLERRM LIKE '%chemin_du_fichier_absent%');
  END;

  -- ===== ⑩a la photo, depot autorise =====
  BEGIN
    v_r := public.app_console_creer_photo_optimistic(v_j_photo, v_bac_dos, v_bac_ann, 'img.jpg', 'facade', 9876);
    INSERT INTO _res VALUES (10, 'la PHOTO : un depot autorise passe', 'ok=true',
      v_r::text, (v_r ->> 'ok') = 'true');
  EXCEPTION WHEN others THEN
    INSERT INTO _res VALUES (10, 'la PHOTO : un depot autorise passe', 'ok=true',
      'LEVEE : ' || SQLERRM, false);
  END;

  -- ===================================================================
  -- ON DEVIENT LE COMMERCIAL -- l'epreuve que Frederic a demandee
  -- ===================================================================
  PERFORM set_config('request.jwt.claims',
    json_build_object('sub', v_commercial::text, 'role','authenticated')::text, true);

  -- ===== ④ un depot sur le bien d'un AUTRE negociateur =====
  BEGIN
    PERFORM public.app_console_creer_document_optimistic(
              v_j_etranger, v_autre_dos, v_autre_ann, 'intrusion.pdf');
    INSERT INTO _res VALUES (4, 'UN DEPOT SUR LE BIEN D''UN AUTRE EST REFUSE',
      'refus (dossier_not_found_or_forbidden)', 'ACCEPTE -- DEFAUT GRAVE', false);
  EXCEPTION WHEN others THEN
    INSERT INTO _res VALUES (4, 'UN DEPOT SUR LE BIEN D''UN AUTRE EST REFUSE',
      'refus (dossier_not_found_or_forbidden)', 'refuse : ' || SQLERRM,
      SQLERRM LIKE '%dossier_not_found_or_forbidden%');
  END;

  -- ===== ⑩b la photo d'un autre =====
  BEGIN
    PERFORM public.app_console_creer_photo_optimistic(
              v_j_photo_etr, v_autre_dos, v_autre_ann, 'intrusion.jpg');
    INSERT INTO _res VALUES (11, 'la PHOTO sur le bien d''un autre est refusee',
      'refus', 'ACCEPTE -- DEFAUT GRAVE', false);
  EXCEPTION WHEN others THEN
    INSERT INTO _res VALUES (11, 'la PHOTO sur le bien d''un autre est refusee',
      'refus', 'refuse : ' || SQLERRM, SQLERRM LIKE '%dossier_not_found_or_forbidden%');
  END;

  -- ===================================================================
  -- ⑨ ANON
  -- ===================================================================
  PERFORM set_config('request.jwt.claims', '', true);
  PERFORM set_config('role', 'anon', true);
  BEGIN
    PERFORM public.app_console_creer_document_optimistic(v_j_ok, v_bac_dos, v_bac_ann, 'anon.pdf');
    INSERT INTO _res VALUES (9, 'anon est refuse', 'refus', 'ACCEPTE -- DEFAUT GRAVE', false);
  EXCEPTION WHEN others THEN
    INSERT INTO _res VALUES (9, 'anon est refuse', 'refus', 'refuse : ' || SQLERRM, true);
  END;

  PERFORM set_config('role', 'none', true);
END $ep$;

-- ---------------------------------------------------------------------
-- 3. ⑪ L'INVERSE REFUSE DE PARTIR TANT QU'UN OBJET EST EN VOL
-- ---------------------------------------------------------------------
DO $inv1$
DECLARE v_docs int; v_photos int;
BEGIN
  SELECT count(*) INTO v_docs   FROM public.app_console_document
   WHERE storage_status='pending_upload' AND source='app';
  SELECT count(*) INTO v_photos FROM public.app_console_photo
   WHERE storage_status='pending_upload' AND source='app';
  INSERT INTO _res VALUES (12, 'l''INVERSE refuse de partir tant qu''un objet est en vol',
    'au moins 1 objet en vol -> le garde-fou doit mordre',
    format('%s document(s) + %s photo(s) en vol', v_docs, v_photos),
    (v_docs + v_photos) > 0);
END $inv1$;

-- ---------------------------------------------------------------------
-- 4. ON RETIRE LES LIGNES D'EPREUVE, PUIS L'INVERSE PASSE PROPREMENT
-- ---------------------------------------------------------------------
DELETE FROM public.app_console_document
 WHERE hektor_annonce_id IN ('62774','5') AND source='app'
   AND storage_status='pending_upload' AND metadata_json ? 'cree_par_app';
DELETE FROM public.app_console_photo
 WHERE hektor_annonce_id IN ('62774','5') AND source='app'
   AND storage_status='pending_upload' AND source_json ? 'cree_par_app';

DROP FUNCTION IF EXISTS public.app_console_creer_document_optimistic(uuid, bigint, text, text, text, text, bigint, text);
DROP FUNCTION IF EXISTS public.app_console_creer_photo_optimistic(uuid, bigint, text, text, text, bigint);

-- ---------------------------------------------------------------------
-- 5. ⑫ LE TEMOIN INVERSE, ET LE TABLEAU
-- ---------------------------------------------------------------------
DO $fin$
DECLARE
  a record;      -- le temoin fige
  l record;      -- la ligne du tableau
  v_n int; v_msg text; v_rates int; v_total int;
BEGIN
  SELECT * INTO a FROM _t_avant;

  -- Les travaux d'epreuve, eux, on les retire aussi pour que le temoin soit juste.
  DELETE FROM public.app_console_job
   WHERE hektor_annonce_id IN ('62774','5')
     AND job_type IN ('upload_document_to_hektor','upload_hektor_photo')
     AND (payload_json ->> 'temp_storage_path') LIKE 'temp/%'
     AND requested_at >= now() - interval '5 minutes';

  SELECT count(*) INTO v_n FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
   WHERE ns.nspname='public' AND p.proname IN
     ('app_console_creer_document_optimistic','app_console_creer_photo_optimistic');
  INSERT INTO _res VALUES (13, 'apres l''inverse, plus aucune RPC', '0', v_n::text, v_n = 0);

  INSERT INTO _res
  SELECT 14, 'TEMOIN INVERSE : les comptes sont ceux du depart',
         format('docs=%s photos=%s en_vol=%s/%s', a.docs, a.photos, a.docs_en_vol, a.photos_en_vol),
         format('docs=%s photos=%s en_vol=%s/%s', d, p, dv, pv),
         (d = a.docs AND p = a.photos AND dv = a.docs_en_vol AND pv = a.photos_en_vol)
    FROM (SELECT (SELECT count(*) FROM public.app_console_document) d,
                 (SELECT count(*) FROM public.app_console_photo) p,
                 (SELECT count(*) FROM public.app_console_document
                   WHERE storage_status='pending_upload') dv,
                 (SELECT count(*) FROM public.app_console_photo
                   WHERE storage_status='pending_upload') pv) s;

  SELECT count(*), count(*) FILTER (WHERE NOT ok) INTO v_total, v_rates FROM _res;

  v_msg := format(E'\n%s\n  REPETITION 3d / LOT 2c -- %s epreuve(s), %s echec(s)\n%s\n',
                  repeat('=',76), v_total, v_rates, repeat('=',76));
  FOR l IN SELECT * FROM _res ORDER BY n LOOP
    v_msg := v_msg || format(E'%s  [%s] %s\n       attendu : %s\n       obtenu  : %s\n',
      CASE WHEN l.ok THEN 'OK  ' ELSE 'RATE' END, l.n, l.titre, l.attendu, l.obtenu);
  END LOOP;
  v_msg := v_msg || format(E'%s\n%s\n%s\n',
    repeat('=',76),
    CASE WHEN v_rates = 0
         THEN 'TOUT EST VERT. Le patch peut etre colle. RIEN N''A ETE ECRIT : la transaction est annulee.'
         ELSE format('%s EPREUVE(S) RATEE(S) -- NE PAS COLLER LE PATCH.', v_rates) END,
    repeat('=',76));

  RAISE EXCEPTION '%', v_msg;
END $fin$;

ROLLBACK;
