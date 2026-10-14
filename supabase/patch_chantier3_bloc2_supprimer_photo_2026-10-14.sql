-- =====================================================================
-- CHANTIER ③ -- BLOC 2 : LE TRAVAIL « SUPPRIMER UNE PHOTO » DEVIENT PERMIS
-- Date : 2026-10-14 · Decision de Frederic : « fais le bloc 2 »
-- Detail : notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md
--
-- POURQUOI. Le worker sait desormais supprimer une photo (handleDeleteHektorPhoto, type
-- `delete_hektor_photo`), mais la base REFUSERAIT de poser ce travail, a deux verrous :
--   ① la contrainte app_console_job_job_type_check, qui liste les types permis ;
--   ② la regle d'insertion app_console_job_insert_scope, qui appelle
--      app_console_can_request_job pour decider QUI peut demander QUOI.
--
-- ⭐ LES DROITS SONT CEUX DU DOCUMENT, A L'IDENTIQUE. Lu en base le 14/10 :
--     admin / manager            -> tout
--     commercial                 -> une liste de gestes, SEULEMENT sur ses biens
--                                   (app_console_can_access_dossier)
--   `delete_hektor_photo` est pose JUSTE A COTE de `delete_document_from_hektor` dans la
--   liste du commercial : un negociateur supprime une photo de SES biens, comme il
--   supprime un document de ses biens. Rien de plus, rien de moins.
--
-- ⚠ ON NE RECOPIE RIEN A LA MAIN. La contrainte et la fonction sont LUES EN BASE, leur
--   empreinte est verifiee (sans les retours chariot), l'ancre doit etre UNIQUE, et l'on
--   ajoute une valeur a cote de son modele. Si l'une ou l'autre a change depuis la mesure,
--   le patch S'ARRETE.
--
-- ⚠ LA CONTRAINTE EST POSEE `NOT VALID`, puis validee APRES le COMMIT. Raison : la
--   table compte 93 663 travaux (64 Mo, mesure du 14/10). Valider dans la transaction
--   tiendrait le verrou exclusif pendant le balayage, et bloquerait les workers. Hors
--   transaction, VALIDATE ne prend qu'un verrou leger. Et la nouvelle liste CONTIENT
--   l'ancienne : toutes les lignes existantes la respectent deja.
--
-- CE QUI NE CHANGE PAS : aucune table, aucune ligne · les droits de tous les autres
-- types · la regle d'insertion elle-meme (elle appelle toujours la meme fonction).
--
-- RETOUR ARRIERE : supabase/patch_chantier3_bloc2_supprimer_photo_2026-10-14_INVERSE.sql
-- REPETITION     : supabase/patch_chantier3_bloc2_supprimer_photo_2026-10-14_REPETITION.sql
-- ⚠ NE LE COLLER QU'UNE SEULE FOIS (le succes est un NOTICE, invisible dans l'editeur).
-- =====================================================================

BEGIN;

-- ① LA CONTRAINTE DES TYPES
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

-- ② LA FONCTION DES DROITS
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

-- ③ LE CONTROLE DE SORTIE
DO $ctrl$
DECLARE v_c text; v_f text;
BEGIN
  SELECT pg_get_constraintdef(oid) INTO v_c FROM pg_constraint
   WHERE conrelid = 'public.app_console_job'::regclass AND conname = 'app_console_job_job_type_check';
  SELECT pg_get_functiondef(p.oid) INTO v_f FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_can_request_job';
  IF position('''delete_hektor_photo''::text' in v_c) = 0 THEN
    RAISE EXCEPTION 'STOP : la contrainte ne connait pas delete_hektor_photo';
  END IF;
  IF position('''delete_document_from_hektor'',''delete_hektor_photo''' in v_f) = 0 THEN
    RAISE EXCEPTION 'STOP : la fonction des droits ne connait pas delete_hektor_photo';
  END IF;
  RAISE NOTICE 'OK : delete_hektor_photo est permis, avec les droits du document.';
END $ctrl$;

COMMIT;

-- ④ HORS TRANSACTION : la validation de la contrainte, sous verrou LEGER.
ALTER TABLE public.app_console_job VALIDATE CONSTRAINT app_console_job_job_type_check;
