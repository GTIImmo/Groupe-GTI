-- ============================================================================
-- INVERSE de patch_chantier7_3c_photo_couverture_2026-10-16.sql
-- 16/10/2026
-- ============================================================================
-- Il retire `reorder_hektor_photos` des TROIS verrous et supprime la RPC de
-- couverture. Rien d'autre.
--
-- ⚠ IL NE DEFAIT PAS LES DONNEES. Les photos deja renumerotees chez nous
--   RESTENT renumerotees, et les ordres deja envoyes a Hektor restent chez lui.
--   Retirer le code n'est pas revenir en arriere sur ce qui a ete ecrit.
--   ➡ Pour defaire un ordre, il faut rejouer l'ancien -- et il est garde dans
--     `base_snapshot` de chaque travail.
--
-- ⚠ IL REFUSE DE TRAVAILLER S'IL RESTE DES TRAVAUX EN COURS de ce type : les
--   retirer de la distribution les laisserait « pending » POUR TOUJOURS, sans
--   erreur -- exactement la panne du 03/10. On preferе s'arreter et le dire.
--
-- ⚠ L'EMPREINTE N'EST PAS UN VETO (lecon du 15/10) : si un autre patch est passe
--   sur ces objets depuis, l'inverse le DIT au lieu de bloquer. Ce qu'il exige,
--   c'est qu'il ne reste AUCUNE TRACE de ce qu'il devait retirer.
-- ============================================================================

BEGIN;

SET LOCAL lock_timeout = '5s';

-- ⓪ LE GARDE-FOU : aucun travail de ce type ne doit etre en vol.
DO $garde$
DECLARE v_n integer;
BEGIN
  SELECT count(*) INTO v_n FROM public.app_console_job
   WHERE job_type = 'reorder_hektor_photos' AND status IN ('pending', 'running');
  IF v_n > 0 THEN
    RAISE EXCEPTION 'STOP : % travail(aux) reorder_hektor_photos encore en attente ou en cours. Les retirer de la distribution les laisserait pending POUR TOUJOURS. Attendre qu''ils finissent, ou les passer en error a la main.', v_n;
  END IF;
END $garde$;

-- ① LA CONTRAINTE
DO $contrainte$
DECLARE v_def text; v_neuf text;
BEGIN
  SELECT pg_get_constraintdef(c.oid) INTO v_def FROM pg_constraint c
   WHERE c.conrelid = 'public.app_console_job'::regclass
     AND c.conname  = 'app_console_job_job_type_check';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : contrainte introuvable'; END IF;
  IF position('reorder_hektor_photos' in v_def) = 0 THEN
    RAISE NOTICE 'RIEN A RETIRER de la contrainte';
  ELSE
    v_neuf := replace(v_def, ', ''reorder_hektor_photos''::text', '');
    IF position('reorder_hektor_photos' in v_neuf) > 0 THEN
      RAISE EXCEPTION 'STOP : il reste une trace du type dans la contrainte apres retrait';
    END IF;
    EXECUTE 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
    EXECUTE 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check '
            || v_neuf || ' NOT VALID';
    IF md5(v_neuf) = 'beacc240a7974dec70a876b717ed052b' THEN
      RAISE NOTICE 'CONTRAINTE : empreinte d''origine retrouvee (beacc240...)';
    ELSE
      RAISE NOTICE 'CONTRAINTE retiree (0 trace), mais l''empreinte est % et non beacc240... -- un AUTRE type a ete ajoute depuis le 16/10. Ce n''est pas une erreur de cet inverse.', md5(v_neuf);
    END IF;
  END IF;
END $contrainte$;

-- ② LES DROITS
DO $droits$
DECLARE v_def text; v_neuf text;
BEGIN
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_def FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_console_can_request_job';
  IF position('reorder_hektor_photos' in v_def) = 0 THEN
    RAISE NOTICE 'RIEN A RETIRER des droits';
  ELSE
    v_neuf := replace(v_def, '''reorder_hektor_photos'',', '');
    IF position('reorder_hektor_photos' in v_neuf) > 0 THEN
      RAISE EXCEPTION 'STOP : il reste une trace du type dans les droits apres retrait';
    END IF;
    EXECUTE v_neuf;
    IF md5(v_neuf) = 'd013972f13ce6f881aa0494c4529e3ae' THEN
      RAISE NOTICE 'DROITS : empreinte d''origine retrouvee (d013972f...)';
    ELSE
      RAISE NOTICE 'DROITS retires (0 trace), mais l''empreinte est % et non d013972f... -- un AUTRE patch est passe. Ce n''est pas une erreur de cet inverse.', md5(v_neuf);
    END IF;
  END IF;
END $droits$;

-- ③ LA DISTRIBUTION
DO $distribution$
DECLARE v_def text; v_neuf text;
BEGIN
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_def FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_console_claim_next_job';
  IF position('reorder_hektor_photos' in v_def) = 0 THEN
    RAISE NOTICE 'RIEN A RETIRER de la distribution';
  ELSE
    v_neuf := replace(v_def, ',''reorder_hektor_photos''', '');
    IF position('reorder_hektor_photos' in v_neuf) > 0 THEN
      RAISE EXCEPTION 'STOP : il reste une trace du type dans la distribution apres retrait';
    END IF;
    EXECUTE v_neuf;
    IF md5(v_neuf) = '4da660742838e4e0849bbd70b7b9a7f5' THEN
      RAISE NOTICE 'DISTRIBUTION : empreinte d''origine retrouvee (4da66074...)';
    ELSE
      RAISE NOTICE 'DISTRIBUTION retiree (0 trace), mais l''empreinte est % et non 4da66074... -- un AUTRE patch est passe. Ce n''est pas une erreur de cet inverse.', md5(v_neuf);
    END IF;
  END IF;
END $distribution$;

-- ④ LA RPC
DROP FUNCTION IF EXISTS public.app_console_photo_couverture_optimistic(bigint, text, text);

-- ⑤ LE CONTROLE DE SORTIE : plus aucune trace, nulle part.
DO $ctrl$
DECLARE v_c text; v_d text; v_x text; v_n integer;
BEGIN
  SELECT pg_get_constraintdef(oid) INTO v_c FROM pg_constraint
   WHERE conrelid='public.app_console_job'::regclass AND conname='app_console_job_job_type_check';
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_d FROM pg_proc p
    JOIN pg_namespace n ON n.oid=p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_console_can_request_job';
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_x FROM pg_proc p
    JOIN pg_namespace n ON n.oid=p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_console_claim_next_job';
  SELECT count(*) INTO v_n FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
   WHERE n.nspname='public' AND p.proname='app_console_photo_couverture_optimistic';

  IF position('reorder_hektor_photos' in coalesce(v_c,'')||coalesce(v_d,'')||coalesce(v_x,'')) > 0 THEN
    RAISE EXCEPTION 'STOP : il reste une trace de reorder_hektor_photos dans un des trois verrous';
  END IF;
  IF v_n > 0 THEN
    RAISE EXCEPTION 'STOP : la RPC de couverture existe encore';
  END IF;
  RAISE NOTICE 'OK : reorder_hektor_photos a disparu des 3 verrous, et la RPC est supprimee.';
END $ctrl$;

COMMIT;

ALTER TABLE public.app_console_job VALIDATE CONSTRAINT app_console_job_job_type_check;
