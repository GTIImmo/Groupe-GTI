-- =====================================================================
-- RETOUR ARRIERE de patch_chantier3_bloc2_distribution_2026-10-14.sql
-- Date : 2026-10-14
--
-- Il retire `delete_hektor_photo` de la liste du service documents, et verifie que la
-- fonction retrouve son empreinte d'origine (8447b6cfd7530134ded46056e39d2e4e, sans les
-- retours chariot), au caractere pres.
-- ⚠ Un travail delete_hektor_photo pose ensuite restera « pending » : personne ne le
--   prendra. A faire avec le retour arriere du bloc 2 (la contrainte et les droits).
-- =====================================================================

BEGIN;

DO $distribution$
DECLARE
  v_def  text;
  v_ajout text := '''delete_hektor_photo'',';
  v_restaure text;
BEGIN
  SELECT pg_get_functiondef(p.oid) INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_claim_next_job';
  IF (length(v_def) - length(replace(v_def, v_ajout, ''))) / length(v_ajout) <> 1 THEN
    RAISE EXCEPTION 'STOP : delete_hektor_photo n''est pas present une seule fois dans la distribution';
  END IF;
  v_restaure := replace(v_def, v_ajout, '');
  IF md5(replace(v_restaure, chr(13), '')) <> '8447b6cfd7530134ded46056e39d2e4e' THEN
    RAISE EXCEPTION 'STOP : la fonction restauree n''a pas l''empreinte d''origine (%)', md5(replace(v_restaure, chr(13), ''));
  END IF;
  EXECUTE v_restaure;
  RAISE NOTICE 'OK : la distribution retrouve son empreinte d''origine.';
END $distribution$;

COMMIT;
