-- =====================================================================
-- 3c PIECE 4 -- CORRECTION DE DROITS, le meme soir            13/10/2026
--
-- CE QUE LE CONTROLE A TROUVE. Mon patch dit « DROITS : service_role seulement »,
-- et il fait bien `revoke all ... from public` puis `grant ... to service_role`.
-- Mais la base repond :
--     postgres=X | authenticated=X | service_role=X
-- ➡ `authenticated` a l'EXECUTE, et ce n'est PAS passe par PUBLIC : c'est un
--   **droit par defaut** pose par Supabase (ALTER DEFAULT PRIVILEGES ... GRANT
--   EXECUTE ON FUNCTIONS TO authenticated). Un `revoke from public` ne l'enleve pas.
--
-- ⚠ LA PORTEE REELLE DU RISQUE EST FAIBLE : la fonction ne fait que rendre le
--   registre CONFORME au carnet -- l'etat juste. Un utilisateur connecte pourrait
--   la declencher, ou passer un plancher bas pour contourner le garde-fou ; le
--   resultat resterait « le registre dit la verite du carnet ».
--   ⭐ ET `anon` NE L'A PAS (verifie) -- c'est le point du chantier ①.
--
-- POURQUOI ON CORRIGE QUAND MEME : un commentaire qui dit « service_role seulement »
-- alors que la base dit autre chose est exactement la derive qui mord six mois plus
-- tard. Le code et la base doivent dire la meme chose.
--
-- ⚠ NE PAS TOUCHER A `app_set_mandat_cloture_optimistic` : pour celle-la,
--   `authenticated` est VOULU -- c'est l'ecran qui l'appelle pour saisir.
--
-- RETOUR ARRIERE :
--   grant execute on function public.app_reposer_cloture_mandat_app(text, int) to authenticated;
-- =====================================================================

BEGIN;

revoke execute on function public.app_reposer_cloture_mandat_app(text, int) from authenticated;

DO $ctrl$
DECLARE v_acl text;
BEGIN
  SELECT array_to_string(p.proacl, ' | ') INTO v_acl
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
   WHERE n.nspname = 'public' AND p.proname = 'app_reposer_cloture_mandat_app';

  IF v_acl LIKE '%authenticated=%' THEN
    RAISE EXCEPTION 'STOP : authenticated a toujours un droit (%)', v_acl;
  END IF;
  IF v_acl NOT LIKE '%service_role=X%' THEN
    RAISE EXCEPTION 'STOP : service_role a PERDU l''execute (%) -- le run ne pourrait plus reposer', v_acl;
  END IF;
  IF v_acl LIKE '%anon=%' THEN
    RAISE EXCEPTION 'STOP : anon a un droit (%)', v_acl;
  END IF;

  RAISE NOTICE 'OK : droits reduits a %', v_acl;
END $ctrl$;

notify pgrst, 'reload schema';

COMMIT;
