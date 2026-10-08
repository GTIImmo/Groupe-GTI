-- =====================================================================
-- RETOUR ARRIÈRE du CHANTIER ① -- rendre à anon / PUBLIC / authenticated les droits d'avant
-- Date : 2026-10-08 · à n'utiliser QUE si le patch casse quelque chose
--
-- Il relit la PHOTO D'AVANT prise par le patch (app_securite_droits_avant_20261008) et
-- redonne chaque droit, à l'identique. Puis il remet les défauts et désactive la RLS des
-- 2 tables, comme avant. La photo est GARDÉE (on peut rejouer le patch plus tard en la
-- supprimant d'abord).
-- =====================================================================

BEGIN;

DO $$
DECLARE r record; n int := 0;
BEGIN
  IF to_regclass('public.app_securite_droits_avant_20261008') IS NULL THEN
    RAISE EXCEPTION 'STOP : la photo d''avant est absente -- le patch n''a pas ete applique';
  END IF;

  FOR r IN SELECT DISTINCT objet_type, objet, beneficiaire, privilege
             FROM public.app_securite_droits_avant_20261008
  LOOP
    BEGIN
      EXECUTE format('GRANT %s ON %s %s TO %s', r.privilege, r.objet_type, r.objet,
                     CASE WHEN r.beneficiaire='PUBLIC' THEN 'PUBLIC' ELSE quote_ident(r.beneficiaire) END);
      n := n + 1;
    EXCEPTION WHEN undefined_function OR undefined_table OR undefined_object THEN
      RAISE NOTICE 'objet disparu depuis, ignore : % %', r.objet_type, r.objet;
    END;
  END LOOP;
  RAISE NOTICE 'droits rendus : %', n;
END $$;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres GRANT EXECUTE ON FUNCTIONS TO PUBLIC;

ALTER TABLE public.app_console_job_error_archive  DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_rapprochement_search_state DISABLE ROW LEVEL SECURITY;

DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
   WHERE ns.nspname='public' AND p.prokind='f' AND has_function_privilege('anon', p.oid, 'EXECUTE');
  RAISE NOTICE 'RETOUR ARRIERE : % fonctions de nouveau ouvertes a anon (136 avant le patch, extensions comprises)', n;
END $$;

COMMIT;
