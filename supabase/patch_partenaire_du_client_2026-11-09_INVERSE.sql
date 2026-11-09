-- RETOUR ARRIERE — patch_partenaire_du_client_2026-11-09.sql : retire la fonction et l'index. Les liens déjà posés RESTENT (de vrais apports
-- notés par un utilisateur) ; l'écran retombe sur le bloc « en construction ».
BEGIN;
SET LOCAL lock_timeout = '3s';
DROP FUNCTION IF EXISTS public.app_partenaire_du_client(text,text,text,boolean);
DROP INDEX IF EXISTS public.app_partenaire_lien_un_client_uidx;
DO $verif$
BEGIN
  IF to_regprocedure('public.app_partenaire_du_client(text,text,text,boolean)') IS NOT NULL OR to_regclass('public.app_partenaire_lien_un_client_uidx') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRET : il reste une trace du patch. Annule.';
  END IF;
END
$verif$;
COMMIT;
