-- ============================================================================
-- patch_alerts_current_view_2026-07-05.sql
--
-- Phase 2 (couche app_alert) - Etape 1 : vue de LECTURE unifiee `alerts_current`.
-- Rassemble les signaux disperses en UN seul format : monitoring, notifications,
-- relances humaines, demandes Pauline. Concue "agent-aware" : une branche
-- 'agent' s'ajoutera trivialement quand les agents IA produiront des signaux.
--
-- SECURITE : `security_invoker = true` -> la vue respecte les RLS des tables
-- sources (chacun ne voit que ce a quoi il a droit ; aucune fuite cross-nego).
-- ADDITIF & READ-ONLY : ne modifie aucune donnee, ne cree aucune ecriture.
-- DORMANTE : rien ne la consomme encore (elle alimentera le cockpit / onglet Sante).
--
-- Colonnes unifiees :
--   alert_key, source, category, severity, owner_role, owner_email,
--   object_type, object_id, title, action_url, created_at, updated_at
-- ============================================================================

create or replace view public.alerts_current
with (security_invoker = true) as

-- 1) Monitoring technique / qualite de donnees (warnings + criticals)
select
  'monitor:' || ms.status_key            as alert_key,
  'monitoring'::text                      as source,
  case when ms.domain = 'data_quality' then 'data_quality'
       when ms.domain = 'business'     then 'business'
       else 'technical' end              as category,
  ms.severity                            as severity,
  'admin'::text                          as owner_role,
  null::text                             as owner_email,
  coalesce(ms.component, ms.domain)      as object_type,
  ms.status_key                          as object_id,
  ms.message                             as title,
  null::text                             as action_url,
  ms.observed_at                         as created_at,
  ms.updated_at                          as updated_at
from public.app_monitor_status ms
where ms.status in ('warning', 'critical')

union all
-- 2) Notifications non lues (proprietaire = negociateur)
select
  'notif:' || n.id::text,
  'notification',
  'business',
  'info',
  'nego',
  n.negociateur_email,
  case when n.app_dossier_id is not null    then 'dossier'
       when n.contact_search_key is not null then 'search'
       else 'autre' end,
  coalesce(n.app_dossier_id::text, n.contact_search_key),
  coalesce(nullif(n.title, ''), n.type),
  n.payload ->> 'action_url',
  n.created_at,
  n.created_at
from public.app_notification n
where n.read_at is null

union all
-- 3) Relances humaines a faire (warning si en retard)
select
  'relance:' || r.id::text,
  'relance',
  'business',
  case when r.due_date is not null and r.due_date < now() then 'warning' else 'info' end,
  'nego',
  r.negociateur_email,
  'dossier',
  r.app_dossier_id::text,
  coalesce(nullif(r.label, ''), 'Relance acquereur'),
  null::text,
  r.created_at,
  r.updated_at
from public.app_relance_rapprochement r
where r.status = 'a_faire'

union all
-- 4) Demandes Pauline en attente de decision
select
  'pauline:' || d.id::text,
  'pauline',
  'workflow',
  'warning',
  'pauline',
  null::text,
  'dossier',
  d.app_dossier_id::text,
  coalesce(nullif(d.request_type, ''), 'demande') || coalesce(' - ' || nullif(d.titre_bien, ''), ''),
  null::text,
  d.requested_at,
  d.updated_at
from public.app_diffusion_request d
where d.request_status = 'pending';

grant select on public.alerts_current to authenticated, service_role;
