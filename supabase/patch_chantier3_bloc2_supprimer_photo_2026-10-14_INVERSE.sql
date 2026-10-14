-- =====================================================================
-- RETOUR ARRIERE de patch_chantier3_bloc2_supprimer_photo_2026-10-14.sql
-- Date : 2026-10-14
--
-- Il retire `delete_hektor_photo` de la contrainte ET de la fonction des droits, et
-- verifie que les DEUX reviennent a leur empreinte d'origine, au caractere pres :
--     contrainte            622672c8a736dbf40c20b5590246c2c2
--     fonction des droits   eb33ddee4fc15c6bbdc7582337dd9c49   (sans les retours chariot)
--
-- ⚠ IL REFUSE DE PARTIR TANT QU'UN TRAVAIL `delete_hektor_photo` EXISTE. L'ancienne
--   contrainte ne le connait pas : la remettre rendrait la table INVALIDE au premier
--   VALIDATE. Il faut d'abord decider du sort de ces travaux -- on ne les efface pas
--   en silence.
--
-- ⚠ A FAIRE DANS LE MEME GESTE cote worker : rien n'est obligatoire (le worker garde son
--   geste, il ne recevra simplement plus de travail). Cote ecran, le bouton recevrait un
--   refus de la base -- le retirer aussi.
-- =====================================================================

BEGIN;

DO $garde$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM public.app_console_job WHERE job_type = 'delete_hektor_photo';
  IF n > 0 THEN
    RAISE EXCEPTION 'STOP : % travail(aux) delete_hektor_photo existe(nt). Decider de leur sort avant de retirer le type.', n;
  END IF;
END $garde$;

DO $contrainte$
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
END $contrainte$;

DO $droits$
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
END $droits$;

DO $ctrl$
BEGIN
  RAISE NOTICE 'OK : delete_hektor_photo est retire ; contrainte et fonction a leur empreinte d''origine.';
END $ctrl$;

COMMIT;

ALTER TABLE public.app_console_job VALIDATE CONSTRAINT app_console_job_job_type_check;
