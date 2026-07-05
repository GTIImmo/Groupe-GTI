-- ============================================================================
-- patch_monitor_domain_check_2026-07-05.sql
--
-- CORRECTIF : la contrainte app_monitor_status_domain_check (et event) n'autorisait
-- que domain in ('system','business','mixed'). Or les sentinelles de donnees
-- ajoutees en Palier 1 ecrivent domain='data_quality' -> HTTP 400 (23514) ->
-- l'ECRITURE COMPLETE du monitor echouait depuis ~23h (le run calculait bien
-- mais ne persistait rien ; l'app affichait donc un etat gele).
--
-- Elargit le domaine autorise (ADDITIF : ajoute des valeurs, n'en retire aucune)
-- et future-proof avec les domaines susceptibles d'etre utilises.
--
-- Lecon : ce bug n'apparaissait pas en --dry-run (qui saute l'ecriture) -> il
-- faut un smoke-test d'ECRITURE reelle pour valider le write-path du monitor.
-- ============================================================================

alter table public.app_monitor_status drop constraint if exists app_monitor_status_domain_check;
alter table public.app_monitor_status add constraint app_monitor_status_domain_check
  check (domain = any (array[
    'system','business','mixed','data_quality','workers','cron','surface','scheduledtasks','email'
  ]));

alter table public.app_monitor_event drop constraint if exists app_monitor_event_domain_check;
alter table public.app_monitor_event add constraint app_monitor_event_domain_check
  check (domain = any (array[
    'system','business','mixed','data_quality','workers','cron','surface','scheduledtasks','email'
  ]));
