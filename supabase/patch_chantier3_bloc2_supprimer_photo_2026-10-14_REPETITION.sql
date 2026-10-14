-- =====================================================================
-- REPETITION du bloc 2 (le travail « supprimer une photo » devient permis) -- RIEN NE RESTE
-- Date : 2026-10-14
--
-- A COLLER DANS L'EDITEUR SQL. Elle fait tout pour de vrai, puis ANNULE TOUT par une levee
-- volontaire a la fin. L'editeur affichera une ERREUR : c'est le SUCCES, le tableau des
-- epreuves est dans son message.
--
-- CE QU'ELLE PROUVE :
--   ① la contrainte accepte delete_hektor_photo, et REFUSE toujours un type inconnu
--   ② ⭐ LES DROITS : admin oui · un commercial sur SON bien oui · le MEME commercial
--      sur le bien d'un AUTRE non
--   ③ ⭐ TEMOINS DE NON-REGRESSION : la suppression d'un DOCUMENT garde exactement ses
--      droits, et un geste absent de la liste du commercial lui reste interdit
--   ④ ⭐ l'inverse REFUSE de partir tant qu'un travail delete_hektor_photo existe
--   ⑤ ⭐ TEMOIN INVERSE : apres l'inverse, contrainte et fonction ont leur empreinte
--      d'origine, AU CARACTERE PRES
--
-- Identites relevees en lecture seule le 14/10 :
--   admin       d4b1685f-948b-4ce8-af15-671b94a725e6  (frederic)
--   commercial  05beded4-3e17-4a0c-ab58-e2c63da3da24  (legrand)
--   SON bien    annonce 6 / dossier 19486             (negociateur = legrand)
--   un AUTRE    annonce 5 / dossier 1096848           (negociateur = forlico)
-- ⚠ Les temoins sont figes AVANT les epreuves (lecon du 13/10).
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout = '120s';

CREATE TEMP TABLE _res (n int, titre text, attendu text, obtenu text, ok boolean);

-- ---------------------------------------------------------------------
-- 0. LES TEMOINS, FIGES
-- ---------------------------------------------------------------------
CREATE TEMP TABLE _t AS
SELECT (SELECT md5(pg_get_constraintdef(oid)) FROM pg_constraint
         WHERE conrelid = 'public.app_console_job'::regclass
           AND conname = 'app_console_job_job_type_check')                     AS md5_contrainte,
       (SELECT md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
          FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
         WHERE n.nspname = 'public' AND p.proname = 'app_console_can_request_job') AS md5_droits,
       (SELECT count(*) FROM public.app_console_job)                           AS travaux;

INSERT INTO _res SELECT 0, 'etat de depart : les deux empreintes mesurees le 14/10',
  '622672c8... / eb33ddee...', left(md5_contrainte, 8) || '... / ' || left(md5_droits, 8) || '...',
  md5_contrainte = '622672c8a736dbf40c20b5590246c2c2' AND md5_droits = 'eb33ddee4fc15c6bbdc7582337dd9c49'
  FROM _t;

-- ---------------------------------------------------------------------
-- 1. LE PATCH, TEL QUEL (sans son BEGIN/COMMIT)
-- ---------------------------------------------------------------------
DO $contrainte$
DECLARE
  v_def   text;
  v_ancre text := '''unlink_hektor_mandant''::text])))';
  v_neuf  text;
BEGIN
  SELECT pg_get_constraintdef(c.oid) INTO v_def
    FROM pg_constraint c
   WHERE c.conrelid = 'public.app_console_job'::regclass
     AND c.conname  = 'app_console_job_job_type_check';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : contrainte app_console_job_job_type_check introuvable'; END IF;
  IF md5(v_def) <> '622672c8a736dbf40c20b5590246c2c2' THEN
    RAISE EXCEPTION 'STOP : la contrainte n''est pas celle mesuree le 14/10 (empreinte %)', md5(v_def);
  END IF;
  IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre de la contrainte n''est pas unique';
  END IF;
  v_neuf := replace(v_def, v_ancre, '''unlink_hektor_mandant''::text, ''delete_hektor_photo''::text])))');

  EXECUTE 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
  EXECUTE 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check '
          || v_neuf || ' NOT VALID';
END $contrainte$;

DO $droits$
DECLARE
  v_def   text;
  v_ancre text := '''delete_document_from_hektor'',''generate_estimation_pdf'',';
BEGIN
  SELECT pg_get_functiondef(p.oid) INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_can_request_job';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : app_console_can_request_job introuvable'; END IF;
  IF md5(replace(v_def, chr(13), '')) <> 'eb33ddee4fc15c6bbdc7582337dd9c49' THEN
    RAISE EXCEPTION 'STOP : la fonction des droits n''est pas celle mesuree le 14/10 (empreinte %)',
      md5(replace(v_def, chr(13), ''));
  END IF;
  IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre de la fonction des droits n''est pas unique';
  END IF;
  EXECUTE replace(v_def, v_ancre,
    '''delete_document_from_hektor'',''delete_hektor_photo'',''generate_estimation_pdf'',');
END $droits$;

-- Dans la repetition, on valide DANS la transaction (elle est annulee de toute facon) :
-- c'est la preuve que les 93 663 lignes existantes respectent la nouvelle liste.
ALTER TABLE public.app_console_job VALIDATE CONSTRAINT app_console_job_job_type_check;

-- ---------------------------------------------------------------------
-- 2. LES EPREUVES
-- ---------------------------------------------------------------------
DO $ep$
DECLARE
  v_admin uuid := 'd4b1685f-948b-4ce8-af15-671b94a725e6';
  v_com   uuid := '05beded4-3e17-4a0c-ab58-e2c63da3da24';
  v_c text; v_f text; v_b boolean; v_msg text;
BEGIN
  SELECT pg_get_constraintdef(oid) INTO v_c FROM pg_constraint
   WHERE conrelid = 'public.app_console_job'::regclass AND conname = 'app_console_job_job_type_check';
  SELECT pg_get_functiondef(p.oid) INTO v_f FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_can_request_job';

  INSERT INTO _res VALUES (1, 'la contrainte cite delete_hektor_photo, une seule fois', '1',
    ((length(v_c) - length(replace(v_c, '''delete_hektor_photo''', ''))) / length('''delete_hektor_photo'''))::text,
    (length(v_c) - length(replace(v_c, '''delete_hektor_photo''', ''))) / length('''delete_hektor_photo''') = 1);
  INSERT INTO _res VALUES (2, 'la fonction des droits le pose JUSTE A COTE du document, une seule fois', '1',
    ((length(v_f) - length(replace(v_f, '''delete_document_from_hektor'',''delete_hektor_photo''', ''))) / length('''delete_document_from_hektor'',''delete_hektor_photo'''))::text,
    (length(v_f) - length(replace(v_f, '''delete_document_from_hektor'',''delete_hektor_photo''', ''))) / length('''delete_document_from_hektor'',''delete_hektor_photo''') = 1);

  -- ① la contrainte
  BEGIN
    INSERT INTO public.app_console_job (job_type, app_dossier_id, hektor_annonce_id, payload_json)
    VALUES ('delete_hektor_photo', 3828957, '62774', '{"photo_id":"repetition"}'::jsonb);
    INSERT INTO _res VALUES (3, 'la contrainte ACCEPTE un travail delete_hektor_photo', 'accepte', 'accepte', true);
  EXCEPTION WHEN others THEN
    INSERT INTO _res VALUES (3, 'la contrainte ACCEPTE un travail delete_hektor_photo', 'accepte', 'REFUSE : ' || SQLERRM, false);
  END;
  BEGIN
    INSERT INTO public.app_console_job (job_type, payload_json) VALUES ('type_qui_n_existe_pas', '{}'::jsonb);
    INSERT INTO _res VALUES (4, 'et REFUSE toujours un type inconnu', 'refus', 'ACCEPTE (defaut grave)', false);
  EXCEPTION WHEN check_violation THEN
    INSERT INTO _res VALUES (4, 'et REFUSE toujours un type inconnu', 'refus', 'refuse : ' || SQLERRM, true);
  END;

  -- ② les droits, avec les vraies identites
  PERFORM set_config('request.jwt.claims', json_build_object('sub', v_admin::text, 'role', 'authenticated')::text, true);
  v_b := public.app_console_can_request_job('delete_hektor_photo', 3828957, '62774');
  INSERT INTO _res VALUES (5, 'admin : supprimer une photo', 'true', coalesce(v_b::text, 'null'), v_b IS TRUE);

  PERFORM set_config('request.jwt.claims', json_build_object('sub', v_com::text, 'role', 'authenticated')::text, true);
  v_b := public.app_console_can_request_job('delete_hektor_photo', 19486, '6');
  INSERT INTO _res VALUES (6, 'commercial : supprimer une photo de SON bien', 'true', coalesce(v_b::text, 'null'), v_b IS TRUE);
  v_b := public.app_console_can_request_job('delete_hektor_photo', 1096848, '5');
  INSERT INTO _res VALUES (7, '⭐ le MEME commercial : une photo du bien d''un AUTRE', 'false', coalesce(v_b::text, 'null'), v_b IS FALSE);

  -- ③ temoins de non-regression
  v_b := public.app_console_can_request_job('delete_document_from_hektor', 19486, '6');
  INSERT INTO _res VALUES (8, 'temoin : un DOCUMENT de son bien, toujours permis', 'true', coalesce(v_b::text, 'null'), v_b IS TRUE);
  v_b := public.app_console_can_request_job('delete_document_from_hektor', 1096848, '5');
  INSERT INTO _res VALUES (9, 'temoin : un DOCUMENT du bien d''un autre, toujours refuse', 'false', coalesce(v_b::text, 'null'), v_b IS FALSE);
  v_b := public.app_console_can_request_job('delete_hektor_annonce', 19486, '6');
  INSERT INTO _res VALUES (10, 'temoin : SUPPRIMER L''ANNONCE reste interdit au commercial', 'false', coalesce(v_b::text, 'null'), v_b IS FALSE);

  PERFORM set_config('request.jwt.claims', '', true);
END $ep$;

-- ④ l'inverse refuse tant qu'un travail delete_hektor_photo existe
DO $refus$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM public.app_console_job WHERE job_type = 'delete_hektor_photo';
  INSERT INTO _res VALUES (11, '⭐ l''inverse REFUSE de partir tant qu''un travail delete_hektor_photo existe',
    'au moins 1 -> refus', n || ' travail(aux) -> ' || CASE WHEN n > 0 THEN 'refus' ELSE 'il passerait' END, n > 0);
END $refus$;

-- on retire le travail d'epreuve, puis l'inverse passe
DELETE FROM public.app_console_job
 WHERE job_type = 'delete_hektor_photo' AND payload_json ->> 'photo_id' = 'repetition';

-- ---------------------------------------------------------------------
-- 3. L'INVERSE, TEL QUEL (sans son BEGIN/COMMIT)
-- ---------------------------------------------------------------------
DO $garde_inv$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM public.app_console_job WHERE job_type = 'delete_hektor_photo';
  IF n > 0 THEN
    RAISE EXCEPTION 'STOP : % travail(aux) delete_hektor_photo existe(nt). Decider de leur sort avant de retirer le type.', n;
  END IF;
END $garde_inv$;

DO $contrainte_inv$
DECLARE
  v_def  text;
  v_ajout text := ', ''delete_hektor_photo''::text';
  v_restaure text;
BEGIN
  SELECT pg_get_constraintdef(c.oid) INTO v_def FROM pg_constraint c
   WHERE c.conrelid = 'public.app_console_job'::regclass AND c.conname = 'app_console_job_job_type_check';
  IF (length(v_def) - length(replace(v_def, v_ajout, ''))) / length(v_ajout) <> 1 THEN
    RAISE EXCEPTION 'STOP : delete_hektor_photo n''est pas present une seule fois dans la contrainte';
  END IF;
  v_restaure := replace(replace(v_def, v_ajout, ''), ' NOT VALID', '');
  IF md5(v_restaure) <> '622672c8a736dbf40c20b5590246c2c2' THEN
    RAISE EXCEPTION 'STOP : la contrainte restauree n''a pas l''empreinte d''origine (%)', md5(v_restaure);
  END IF;
  EXECUTE 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
  EXECUTE 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check '
          || v_restaure || ' NOT VALID';
END $contrainte_inv$;

DO $droits_inv$
DECLARE
  v_def  text;
  v_ajout text := '''delete_hektor_photo'',';
  v_restaure text;
BEGIN
  SELECT pg_get_functiondef(p.oid) INTO v_def FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_can_request_job';
  IF (length(v_def) - length(replace(v_def, v_ajout, ''))) / length(v_ajout) <> 1 THEN
    RAISE EXCEPTION 'STOP : delete_hektor_photo n''est pas present une seule fois dans la fonction des droits';
  END IF;
  v_restaure := replace(v_def, v_ajout, '');
  IF md5(replace(v_restaure, chr(13), '')) <> 'eb33ddee4fc15c6bbdc7582337dd9c49' THEN
    RAISE EXCEPTION 'STOP : la fonction restauree n''a pas l''empreinte d''origine (%)', md5(replace(v_restaure, chr(13), ''));
  END IF;
  EXECUTE v_restaure;
END $droits_inv$;

ALTER TABLE public.app_console_job VALIDATE CONSTRAINT app_console_job_job_type_check;

-- ---------------------------------------------------------------------
-- 4. ⑤ LE TEMOIN INVERSE, ET LE TABLEAU
-- ---------------------------------------------------------------------
INSERT INTO _res
SELECT 12, 'TEMOIN INVERSE : la contrainte retrouve son empreinte d''origine, au caractere pres',
       t.md5_contrainte, x.m, x.m = t.md5_contrainte
  FROM _t t,
       (SELECT md5(pg_get_constraintdef(oid)) AS m FROM pg_constraint
         WHERE conrelid = 'public.app_console_job'::regclass AND conname = 'app_console_job_job_type_check') x;

INSERT INTO _res
SELECT 13, 'TEMOIN INVERSE : la fonction des droits retrouve son empreinte d''origine',
       t.md5_droits, x.m, x.m = t.md5_droits
  FROM _t t,
       (SELECT md5(replace(pg_get_functiondef(p.oid), chr(13), '')) AS m
          FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
         WHERE n.nspname = 'public' AND p.proname = 'app_console_can_request_job') x;

INSERT INTO _res
SELECT 14, 'aucun travail laisse derriere', t.travaux::text, x.n::text, x.n = t.travaux
  FROM _t t, (SELECT count(*) AS n FROM public.app_console_job) x;

DO $fin$
DECLARE l record; v_msg text; v_total int; v_rates int;
BEGIN
  SELECT count(*), count(*) FILTER (WHERE NOT ok) INTO v_total, v_rates FROM _res;
  v_msg := format(E'\n%s\n  REPETITION BLOC 2 (supprimer une photo) -- %s epreuve(s), %s echec(s)\n%s\n',
                  repeat('=', 76), v_total, v_rates, repeat('=', 76));
  FOR l IN SELECT * FROM _res ORDER BY n LOOP
    v_msg := v_msg || format(E'%s  [%s] %s\n       attendu : %s\n       obtenu  : %s\n',
      CASE WHEN l.ok THEN 'OK  ' ELSE 'RATE' END, l.n, l.titre, l.attendu, l.obtenu);
  END LOOP;
  v_msg := v_msg || format(E'%s\n%s\n%s\n', repeat('=', 76),
    CASE WHEN v_rates = 0
         THEN 'TOUT EST VERT. Le patch peut etre colle. RIEN N''A ETE ECRIT : la transaction est annulee.'
         ELSE format('%s EPREUVE(S) RATEE(S) -- NE PAS COLLER LE PATCH.', v_rates) END,
    repeat('=', 76));
  RAISE EXCEPTION '%', v_msg;
END $fin$;

ROLLBACK;
