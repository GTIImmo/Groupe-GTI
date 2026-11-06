-- RETOUR ARRIÈRE de patch_partenaire_du_bien_2026-11-06.sql (lot 5, 06/11/2026). Ne juge QUE sa part (leçon 31) :
-- les liens déjà posés dans l'app RESTENT (des données, comptées) ; le geste du syndic (4.2) n'est pas touché.
BEGIN;
DROP FUNCTION IF EXISTS public.app_partenaire_du_bien(text,bigint,bigint,text,boolean);
DROP FUNCTION IF EXISTS public.app_partenaire_du_bien_lire(text,bigint);
DROP INDEX IF EXISTS public.app_partenaire_lien_un_diag_uidx;
DO $controle$
DECLARE v_app int;
BEGIN
  IF to_regprocedure('public.app_partenaire_du_bien(text,bigint,bigint,text,boolean)') IS NOT NULL
     OR to_regprocedure('public.app_partenaire_du_bien_lire(text,bigint)') IS NOT NULL
     OR to_regclass('public.app_partenaire_lien_un_diag_uidx') IS NOT NULL THEN
    RAISE EXCEPTION 'ÉCHEC : une trace du patch reste.';
  END IF;
  IF to_regprocedure('public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean)') IS NULL THEN
    RAISE EXCEPTION 'ÉCHEC : le geste du syndic (4.2) a disparu.';
  END IF;
  SELECT count(*) INTO v_app FROM public.app_partenaire_lien WHERE role = 'diagnostiqueur' AND origine = 'app';
  RAISE NOTICE 'Retour arrière fait. Liens diagnostiqueur posés dans l''app, laissés en place : %', v_app;
END
$controle$;
COMMIT;
