-- ============================================================================
-- patch_worker_heartbeat_2026-07-04.sql
-- Palier 1 / Lot 1.1 — Battement de coeur runtime des workers.
--
-- Objectif : transformer app_worker_registry (catalogue statique) en preuve de
--            vie. Chaque worker ecrit sa derniere execution ; le monitoring
--            alerte si un worker planifie n'a plus donne signe.
--
-- SECURITE / REGLES :
--   * 100% ADDITIF : aucune colonne existante modifiee ou supprimee.
--   * IDEMPOTENT : "add column if not exists" -> rejouable sans risque.
--   * PAS de fonction security-definer (les workers ecrivent via PATCH REST
--     en service_role, comme le fait deja check_gti_health.py) -> ne cree pas
--     de nouvelle surface exposee en public (cf. risque R4 audit global).
--
-- Ecriture cote worker (Step 2, helper heartbeat) :
--   PATCH /rest/v1/app_worker_registry?worker_key=eq.<key>
--   body: { last_run_at, last_success_at, last_status, last_duration_ms,
--           last_error, last_run_host, updated_at }
-- ============================================================================

alter table public.app_worker_registry
  add column if not exists last_run_at       timestamptz,
  add column if not exists last_success_at   timestamptz,
  add column if not exists last_status       text,
  add column if not exists last_duration_ms  integer,
  add column if not exists last_error        text,
  add column if not exists last_run_host     text;

comment on column public.app_worker_registry.last_run_at is
  'Heartbeat : horodatage du dernier demarrage/execution du worker (UTC).';
comment on column public.app_worker_registry.last_success_at is
  'Heartbeat : dernier run termine avec succes (UTC). Source de la detection de retard.';
comment on column public.app_worker_registry.last_status is
  'Heartbeat : statut du dernier run (success | error | running).';
comment on column public.app_worker_registry.last_error is
  'Heartbeat : message d''erreur du dernier run en echec (null si succes).';
comment on column public.app_worker_registry.last_run_host is
  'Heartbeat : hote ayant execute le worker (utile si sortie du mono-poste, risque R2).';

-- Rien d'autre : la politique de fraicheur (seuils par classe de frequence)
-- est portee cote monitoring (check_gti_health.py -> check_worker_heartbeat),
-- pas dans le schema, pour rester ajustable sans migration.
