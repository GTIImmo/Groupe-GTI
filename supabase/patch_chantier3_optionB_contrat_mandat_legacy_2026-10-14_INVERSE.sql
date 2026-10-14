-- =====================================================================
-- RETOUR ARRIERE de patch_chantier3_optionB_contrat_mandat_legacy_2026-10-14.sql
-- Date : 2026-10-14
--
-- Il remet les deux inscriptions en `active` et RETIRE la note ajoutee, au caractere pres
-- (tout ce qui suit le marqueur « [[RETIREE DU RUN 14/10/2026]] », espace de tete compris).
--
-- ⚠ A FAIRE DANS LE MEME GESTE : decommenter les six lignes dans run_full_pipeline.ps1.
--   Remettre les inscriptions en `active` SANS remettre les etapes dans le run ferait
--   exactement l'alerte quotidienne que le patch evitait.
-- =====================================================================

BEGIN;

DO $garde$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM public.app_worker_registry
   WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')
     AND status = 'legacy'
     AND position(' [[RETIREE DU RUN 14/10/2026]]' in coalesce(source_notes, '')) > 0;
  IF n <> 2 THEN
    RAISE EXCEPTION 'STOP : % inscription(s) portent le patch au lieu de 2 -- rien a defaire, ou elles ont change', n;
  END IF;
END $garde$;

UPDATE public.app_worker_registry
   SET status       = 'active',
       source_notes = left(source_notes, position(' [[RETIREE DU RUN 14/10/2026]]' in source_notes) - 1),
       updated_at   = now()
 WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')
   AND status = 'legacy'
   AND position(' [[RETIREE DU RUN 14/10/2026]]' in coalesce(source_notes, '')) > 0;

DO $ctrl$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM public.app_worker_registry
   WHERE worker_key IN ('phase2.magasin_mandat', 'phase2.contrat_mandat')
     AND status = 'active'
     AND position('[[RETIREE DU RUN' in coalesce(source_notes, '')) = 0;
  IF n <> 2 THEN RAISE EXCEPTION 'STOP : % ligne(s) revenues au lieu de 2', n; END IF;
  RAISE NOTICE 'OK : les 2 inscriptions sont revenues en active, notes d''origine restituees.';
END $ctrl$;

COMMIT;
