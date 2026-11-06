-- RETOUR ARRIÈRE de patch_partenaire_syndic_du_bien_2026-11-06.sql (pièce 4.2a, 06/11/2026).
-- Retire les deux fonctions et l'index « un seul syndic par bien ». Ne juge QUE sa part (leçon 31) :
--   · les liens déjà posés dans l'app (origine « app ») RESTENT : ce sont des données, pas le patch. Ils sont COMPTÉS ;
--   · `app_partenaire_lien_ecrire` et la table ne sont pas touchées.

BEGIN;

DROP FUNCTION IF EXISTS public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean);
DROP FUNCTION IF EXISTS public.app_partenaire_syndic_du_bien_lire(bigint);
DROP INDEX IF EXISTS public.app_partenaire_lien_un_syndic_uidx;

DO $controle$
DECLARE v_app int;
BEGIN
  IF to_regprocedure('public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean)') IS NOT NULL
     OR to_regprocedure('public.app_partenaire_syndic_du_bien_lire(bigint)') IS NOT NULL
     OR to_regclass('public.app_partenaire_lien_un_syndic_uidx') IS NOT NULL THEN
    RAISE EXCEPTION 'ÉCHEC : une trace du patch reste.';
  END IF;
  IF to_regprocedure('public.app_partenaire_lien_ecrire(bigint,text,text,text,bigint,bigint,bigint,text,boolean)') IS NULL THEN
    RAISE EXCEPTION 'ÉCHEC : app_partenaire_lien_ecrire a disparu (elle ne devait pas être touchée).';
  END IF;
  SELECT count(*) INTO v_app FROM public.app_partenaire_lien WHERE role = 'syndic' AND origine = 'app';
  RAISE NOTICE 'Retour arrière fait. Liens syndic posés dans l''app, laissés en place : %', v_app;
END
$controle$;

COMMIT;
