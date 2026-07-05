-- ============================================================================
-- patch_actif_workers_disabled_2026-07-05.sql
--
-- Marque les 5 workers du prototype ACTIF (abandonne le 23/03/2026, cf.
-- ACTIF/STATUT_ACTIF_2026-03-23.md) comme 'disabled' dans le registre.
-- Ils gonflaient le compteur "35 workers" alors que le systeme reel en compte
-- ~30. Ils ne tournent pas (ACTIF est une archive de reference) et n'appellent
-- aucune alerte (deja exclus du heartbeat via leur frequence manual/watcher).
--
-- Le check_supabase_registry (monitoring) compte desormais les workers non
-- 'disabled' -> le compteur reflete la realite (30 actifs, 5 desactives).
-- Additif, reversible (remettre 'active' si ACTIF est un jour repris).
-- ============================================================================

update public.app_worker_registry
set status = 'disabled', updated_at = now()
where worker_key like 'actif%'
  and status <> 'disabled';
