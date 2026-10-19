-- ============================================================================
-- INVERSE -- retirer le geste « masquer / afficher une photo »
-- 19/10/2026
-- ============================================================================
-- Il retire les QUATRE choses que le patch a posees, dans l'ordre inverse :
--     ④ la RPC app_console_photo_visibilite_optimistic
--     ③ le type dans la DISTRIBUTION
--     ② le type dans les DROITS
--     ① le type dans la CONTRAINTE
--
-- ⚠⚠ L'ORDRE N'EST PAS DECORATIF. On retire la RPC D'ABORD : tant qu'elle existe,
--   un clic pourrait poser un travail d'un type que la contrainte ne connait plus
--   -- et l'insertion echouerait au nez de l'utilisateur. Et on retire la
--   contrainte EN DERNIER pour la meme raison.
--
-- ⛔⛔ ET IL REFUSE S'IL RESTE DES TRAVAUX DE CE TYPE. Retirer le type de la
--   contrainte alors que des lignes le portent casserait la table : la contrainte
--   est reposee en NOT VALID, donc les lignes existantes ne sont pas verifiees...
--   mais la DISTRIBUTION, elle, ne les reclamerait plus et ils resteraient
--   « pending » A VIE, invisibles. C'est exactement le defaut du 14/10
--   (« un type absent de claim_next_job reste pending a vie »), a l'envers.
--   ➡ On compte, et on DIT quoi faire.
--
-- ⚠ CE QU'IL NE DEFAIT PAS, et il faut le savoir : les drapeaux `visible` deja
--   changes par le geste RESTENT. C'est voulu -- ils disent la verite de Hektor,
--   relue et prouvee par le worker. L'inverse retire le GESTE, pas ses effets.
--
-- ⚠ ANCRES SUR UNE SEULE LIGNE + replace(chr(13)) DES DEUX COTES (lecon 30).
-- ============================================================================

BEGIN;

SET LOCAL lock_timeout = '5s';

-- ⓿ LE REFUS QUI PROTEGE : des travaux de ce type en vol ?
DO $garde$
DECLARE
  v_vol integer;
  v_tot integer;
BEGIN
  SELECT count(*) INTO v_vol FROM public.app_console_job
   WHERE job_type = 'set_hektor_photo_visibility' AND status IN ('pending','running');
  SELECT count(*) INTO v_tot FROM public.app_console_job
   WHERE job_type = 'set_hektor_photo_visibility';

  IF v_vol > 0 THEN
    RAISE EXCEPTION 'STOP : % travail(aux) set_hektor_photo_visibility en vol (pending/running) sur % au total. Les laisser finir, ou les passer en cancelled AVANT de defaire -- sinon ils resteraient pending a vie, invisibles.', v_vol, v_tot;
  END IF;
  IF v_tot > 0 THEN
    RAISE NOTICE 'INFO : % travail(aux) de ce type en base, tous termines. On peut defaire : la contrainte est reposee en NOT VALID, donc les lignes existantes ne sont pas revalidees.', v_tot;
  END IF;
END $garde$;

-- ④ LA RPC D'ABORD
DROP FUNCTION IF EXISTS public.app_console_photo_visibilite_optimistic(bigint, text, text, boolean);

-- ③ LA DISTRIBUTION
DO $distribution$
DECLARE
  v_def  text;
  v_pose text := replace(',''set_hektor_photo_visibility''', chr(13), '');
BEGIN
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_claim_next_job';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : app_console_claim_next_job introuvable'; END IF;
  IF position(v_pose in v_def) = 0 THEN
    RAISE NOTICE 'RIEN A DEFAIRE dans la distribution';
  ELSE
    IF (length(v_def) - length(replace(v_def, v_pose, ''))) / length(v_pose) <> 1 THEN
      RAISE EXCEPTION 'STOP : la pose apparait plusieurs fois dans la distribution -- ne PAS defaire a l aveugle';
    END IF;
    EXECUTE replace(v_def, v_pose, '');
  END IF;
END $distribution$;

-- ② LES DROITS
DO $droits$
DECLARE
  v_def  text;
  v_pose text := replace('''set_hektor_photo_visibility'',', chr(13), '');
BEGIN
  SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO v_def
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_console_can_request_job';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : app_console_can_request_job introuvable'; END IF;
  IF position(v_pose in v_def) = 0 THEN
    RAISE NOTICE 'RIEN A DEFAIRE dans les droits';
  ELSE
    IF (length(v_def) - length(replace(v_def, v_pose, ''))) / length(v_pose) <> 1 THEN
      RAISE EXCEPTION 'STOP : la pose apparait plusieurs fois dans les droits';
    END IF;
    EXECUTE replace(v_def, v_pose, '');
  END IF;
END $droits$;

-- ① LA CONTRAINTE EN DERNIER
DO $contrainte$
DECLARE
  v_def  text;
  v_pose text := replace(', ''set_hektor_photo_visibility''::text', chr(13), '');
  v_neuf text;
BEGIN
  SELECT pg_get_constraintdef(c.oid) INTO v_def
    FROM pg_constraint c
   WHERE c.conrelid = 'public.app_console_job'::regclass
     AND c.conname  = 'app_console_job_job_type_check';
  IF v_def IS NULL THEN RAISE EXCEPTION 'STOP : contrainte introuvable'; END IF;
  IF position(v_pose in v_def) = 0 THEN
    RAISE NOTICE 'RIEN A DEFAIRE dans la contrainte';
  ELSE
    IF (length(v_def) - length(replace(v_def, v_pose, ''))) / length(v_pose) <> 1 THEN
      RAISE EXCEPTION 'STOP : la pose apparait plusieurs fois dans la contrainte';
    END IF;
    v_neuf := replace(v_def, v_pose, '');
    EXECUTE 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
    EXECUTE 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check '
            || v_neuf || ' NOT VALID';
  END IF;
END $contrainte$;

-- ⓹ LE CONTROLE DU RETOUR : aucune trace nulle part.
DO $fin$
DECLARE
  v_reste integer := 0;
BEGIN
  IF EXISTS (SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
              WHERE n.nspname='public' AND p.proname='app_console_photo_visibilite_optimistic') THEN
    v_reste := v_reste + 1;
    RAISE NOTICE 'ROUGE : la RPC existe encore';
  END IF;
  IF (SELECT position('set_hektor_photo_visibility' in pg_get_constraintdef(c.oid)) > 0
        FROM pg_constraint c WHERE c.conrelid='public.app_console_job'::regclass
         AND c.conname='app_console_job_job_type_check') THEN
    v_reste := v_reste + 1;
    RAISE NOTICE 'ROUGE : la contrainte connait encore le type';
  END IF;
  IF (SELECT position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid)) > 0
        FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
       WHERE n.nspname='public' AND p.proname='app_console_can_request_job') THEN
    v_reste := v_reste + 1;
    RAISE NOTICE 'ROUGE : les droits connaissent encore le type';
  END IF;
  IF (SELECT position('set_hektor_photo_visibility' in pg_get_functiondef(p.oid)) > 0
        FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
       WHERE n.nspname='public' AND p.proname='app_console_claim_next_job') THEN
    v_reste := v_reste + 1;
    RAISE NOTICE 'ROUGE : la distribution connait encore le type';
  END IF;

  IF v_reste > 0 THEN
    RAISE EXCEPTION 'STOP : % trace(s) du geste subsistent -- le retour arriere est INCOMPLET', v_reste;
  END IF;
  RAISE NOTICE 'DEFAIT : les 4 poses sont retirees, aucune trace.';
  RAISE NOTICE '⚠ LES DRAPEAUX `visible` DEJA CHANGES RESTENT -- ils disent la verite de Hektor, relue et prouvee. L inverse retire le GESTE, pas ses effets.';
  RAISE NOTICE '⚠ LE WORKER garde son handler : il est inerte sans le type (aucun travail ne peut plus etre pose).';
END $fin$;

COMMIT;
