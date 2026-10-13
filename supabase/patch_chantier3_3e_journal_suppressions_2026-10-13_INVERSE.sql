-- =====================================================================
-- RETOUR ARRIERE du palier 1 de 3e -- 2026-10-13
--
-- ⚠⚠ LIS CECI AVANT DE LE COLLER.
--
-- CE SCRIPT NE SUPPRIME PAS LES JOURNAUX S'ILS CONTIENNENT QUELQUE CHOSE.
-- Un journal de suppressions est, par construction, LA SEULE TRACE de ce qui a
-- ete detruit : le fichier cloud, le fichier serveur et la ligne sont partis. Le
-- jeter reviendrait a effacer la memoire de la destruction -- exactement le
-- defaut que ce palier repare.
--   ➡ s'ils sont VIDES, il les supprime.
--   ➡ s'ils portent des lignes, IL REFUSE et dit combien.
--
-- Pour les jeter quand meme, apres avoir decide de perdre ces traces :
--     drop table if exists public.app_console_deleted_document_log;
--     drop table if exists public.app_console_deleted_photo_log;
--
-- LA MENTION SUR LES DOCUMENTS (present_in_hektor / absent_depuis) est, elle,
-- RETIREE : elle ne porte aucune information qu'on ne puisse recalculer -- la
-- prochaine synchro reconstate ce que Hektor a ou n'a pas.
--   ⚠ SAUF si des documents sont deja marques « plus chez Hektor » : cette
--     constatation-la ne se retrouve PAS (le document a disparu de chez Hektor,
--     donc plus aucune lecture ne le redira). Le script refuse aussi dans ce cas.
-- =====================================================================

BEGIN;

DO $retour$
DECLARE
  n_doc int; n_photo int; n_marques int;
BEGIN
  SELECT count(*) INTO n_doc   FROM public.app_console_deleted_document_log;
  SELECT count(*) INTO n_photo FROM public.app_console_deleted_photo_log;
  SELECT count(*) INTO n_marques FROM public.app_console_document
   WHERE present_in_hektor IS FALSE;

  IF n_doc > 0 OR n_photo > 0 THEN
    RAISE EXCEPTION
      'REFUS : les journaux portent des traces (% documents, % photos). Les jeter '
      'effacerait la memoire de suppressions DEFINITIVES. Voir l''en-tete du script '
      'pour le faire quand meme, en connaissance.', n_doc, n_photo;
  END IF;

  IF n_marques > 0 THEN
    RAISE EXCEPTION
      'REFUS : % document(s) sont marques « plus chez Hektor ». Cette constatation '
      'ne se retrouve PAS -- le document a disparu de chez Hektor, aucune lecture '
      'ne le redira. Retirer la colonne perdrait l''information.', n_marques;
  END IF;

  RAISE NOTICE 'OK : les journaux sont vides et aucun document n''est marque -- on peut defaire.';
END $retour$;

-- ---------------------------------------------------------------------
-- 1. LES DEUX JOURNAUX (verifies vides ci-dessus)
-- ---------------------------------------------------------------------
drop table if exists public.app_console_deleted_document_log;
drop table if exists public.app_console_deleted_photo_log;

-- ---------------------------------------------------------------------
-- 2. LA MENTION SUR LES DOCUMENTS
--    L'index d'abord : il depend des colonnes.
-- ---------------------------------------------------------------------
drop index if exists public.app_console_document_absent_idx;

alter table public.app_console_document
  drop column if exists present_in_hektor,
  drop column if exists absent_depuis;

-- ---------------------------------------------------------------------
-- 3. LE CONTROLE DE SORTIE
-- ---------------------------------------------------------------------
DO $ctrl$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
   WHERE ns.nspname='public'
     AND c.relname IN ('app_console_deleted_document_log','app_console_deleted_photo_log');
  IF n <> 0 THEN RAISE EXCEPTION 'STOP : % journal(aux) subsiste(nt)', n; END IF;

  SELECT count(*) INTO n FROM pg_attribute
   WHERE attrelid='public.app_console_document'::regclass
     AND attname IN ('present_in_hektor','absent_depuis') AND NOT attisdropped;
  IF n <> 0 THEN RAISE EXCEPTION 'STOP : % colonne(s) subsiste(nt)', n; END IF;

  RAISE NOTICE 'OK : palier 1 de 3e entierement defait.';
END $ctrl$;

notify pgrst, 'reload schema';

COMMIT;
