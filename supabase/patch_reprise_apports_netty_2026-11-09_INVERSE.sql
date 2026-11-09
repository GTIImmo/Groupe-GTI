-- INVERSE — patch_reprise_apports_netty_2026-11-09.sql : retire EXACTEMENT les liens apporteur ↔ client d'origine 'netty'.
-- Il ne juge que SA part : aucun lien posé dans l'app (origine 'app') n'est touché, et il vérifie qu'il n'en reste aucun.
-- Un lien Netty RETIRÉ depuis l'écran (retire_le rempli) part aussi : il n'existait que par la reprise.
BEGIN;
SET LOCAL lock_timeout = '3s';

DO $inverse$
DECLARE
  n_app_avant int; n_app_apres int; n_retire int; n_reste int;
BEGIN
  SELECT count(*) INTO n_app_avant FROM public.app_partenaire_lien WHERE origine <> 'netty';

  DELETE FROM public.app_partenaire_lien
   WHERE origine = 'netty' AND objet = 'client' AND role = 'apporteur';
  GET DIAGNOSTICS n_retire = ROW_COUNT;

  SELECT count(*) INTO n_reste FROM public.app_partenaire_lien WHERE origine = 'netty';
  SELECT count(*) INTO n_app_apres FROM public.app_partenaire_lien WHERE origine <> 'netty';
  IF n_reste <> 0 OR n_app_apres <> n_app_avant OR n_retire > 14 THEN
    RAISE EXCEPTION 'Inverse annulé : retirés %, restent % netty, autres liens % -> %.', n_retire, n_reste, n_app_avant, n_app_apres;
  END IF;
  RAISE NOTICE 'Inverse Netty : % lien(s) retiré(s), les % autres liens intacts.', n_retire, n_app_apres;
END
$inverse$;

COMMIT;
