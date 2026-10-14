-- =====================================================================
-- CHANTIER ③ -- BLOC 2, LE TROISIEME VERROU : LA DISTRIBUTION DES TRAVAUX
-- Date : 2026-10-14
--
-- CE QUI S'EST PASSE. L'essai reel du 14/10 sur 62774 (accord de Frederic) : la photo
-- d'essai s'est AJOUTEE en 28 s par le chemin differe -- puis le travail de SUPPRESSION
-- est reste `pending` six minutes : AUCUN SERVICE NE L'A PRIS.
--
-- POURQUOI. app_console_claim_next_job, la fonction qui distribue les travaux aux
-- services, a SA PROPRE LISTE de types par service. `delete_hektor_photo` n'est pas dans
-- celle du service `documents`. Le patch du bloc 2 avait ouvert la contrainte des types
-- et les droits ; il avait oublie ce troisieme verrou.
-- ⚠ LE PIEGE ETAIT DEJA ECRIT DANS LA FONCTION ELLE-MEME, pour un autre geste (03/10) :
--   « Sans cette ligne, le travail n'est reclame par personne et reste « pending » a vie. »
--   ➡ Pour poser un NOUVEAU type de travail, il y a TROIS verrous en base (la contrainte,
--     les droits, la distribution) et cinq endroits dans le worker. Mesure du 14/10 : aucun
--     autre (ni vue, ni tache cron, ni autre fonction ne cite ces types).
--
-- CE QUE FAIT CE PATCH : il lit la fonction en base, verifie son empreinte (sans les
-- retours chariot), exige une ancre UNIQUE, et ajoute `delete_hektor_photo` JUSTE APRES
-- `upload_hektor_photo` dans la liste du service `documents` -- le service qui porte deja
-- le geste (DOCUMENT_JOB_TYPES, cote worker).
-- ⭐ Le travail d'essai en attente (b7519387…) sera pris par le service documents dans les
--   5 secondes qui suivent le COMMIT : c'est la suite de l'essai, autorise par Frederic.
--
-- CE QUI NE CHANGE PAS : aucune table · les listes des autres services · tout le reste de
-- la fonction (la reprise des travaux bloques > 30 min, les gardes par annonce et par
-- contact, l'ordre de priorite).
--
-- RETOUR ARRIERE : supabase/patch_chantier3_bloc2_distribution_2026-10-14_INVERSE.sql
-- REPETITION     : supabase/patch_chantier3_bloc2_distribution_2026-10-14_REPETITION.sql
-- =====================================================================

BEGIN;

DO $distribution$
DECLARE
  v_def   text;
  v_ancre text := '''sync_hektor_photos'',''upload_hektor_photo'',';
BEGIN
  SELECT pg_get_functiondef(p.oid) INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_claim_next_job';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : app_console_claim_next_job introuvable'; END IF;
  IF md5(replace(v_def, chr(13), '')) <> '8447b6cfd7530134ded46056e39d2e4e' THEN
    RAISE EXCEPTION 'STOP : la fonction de distribution n''est pas celle mesuree le 14/10 (empreinte %)',
      md5(replace(v_def, chr(13), ''));
  END IF;
  IF (length(v_def) - length(replace(v_def, v_ancre, ''))) / length(v_ancre) <> 1 THEN
    RAISE EXCEPTION 'STOP : l''ancre de la liste documents n''est pas unique';
  END IF;
  EXECUTE replace(v_def, v_ancre,
    '''sync_hektor_photos'',''upload_hektor_photo'',''delete_hektor_photo'',');
END $distribution$;

DO $ctrl$
DECLARE v_def text;
BEGIN
  SELECT pg_get_functiondef(p.oid) INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_claim_next_job';
  IF position('''upload_hektor_photo'',''delete_hektor_photo''' in v_def) = 0 THEN
    RAISE EXCEPTION 'STOP : la liste documents ne connait pas delete_hektor_photo';
  END IF;
  RAISE NOTICE 'OK : le service documents prend desormais les suppressions de photo.';
END $ctrl$;

COMMIT;
