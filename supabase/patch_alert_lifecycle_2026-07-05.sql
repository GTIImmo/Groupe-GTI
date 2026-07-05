-- ============================================================================
-- patch_alert_lifecycle_2026-07-05.sql
--
-- Phase 2 (couche app_alert) - Etape 3 : CYCLE DE VIE des alertes.
-- Une table d'etat "overlay" par-dessus la vue alerts_current + une RPC d'action
-- + une vue gouvernee alerts_governed (alerte + etat).
--
-- ROBUSTE A LA RECURRENCE : l'etat (pris en charge / resolu...) n'est applique
-- que s'il est PLUS RECENT que la derniere emission de l'alerte (acted_at >=
-- alerte.updated_at). Ainsi une alerte deja resolue qui REPART (nouvelle
-- emission, updated_at plus recent) redevient 'new' -> jamais masquee a tort.
--
-- SECURITE : RLS activee ; RPC security invoker (respecte les RLS) ; vue
-- security_invoker. ADDITIF, aucune donnee existante modifiee.
-- ============================================================================

-- 1) Table d'etat (overlay lifecycle, cle = alert_key de alerts_current).
create table if not exists public.app_alert_state (
  alert_key      text primary key,
  status         text not null check (status in ('acknowledged','resolved','ignored','snoozed')),
  acted_by       uuid,
  acted_at       timestamptz not null default now(),
  snoozed_until  timestamptz,
  note           text,
  updated_at     timestamptz not null default now()
);

alter table public.app_alert_state enable row level security;
drop policy if exists app_alert_state_rw on public.app_alert_state;
create policy app_alert_state_rw on public.app_alert_state
  for all to authenticated using (true) with check (true);
grant select, insert, update, delete on public.app_alert_state to authenticated, service_role;

-- 2) RPC d'action : pose/maj l'etat d'une alerte (upsert par alert_key).
create or replace function public.app_alert_set_state(
  p_alert_key     text,
  p_status        text,
  p_by            uuid default null,
  p_note          text default null,
  p_snoozed_until timestamptz default null
)
returns public.app_alert_state
language plpgsql
security invoker
set search_path = public
as $function$
declare v_row public.app_alert_state;
begin
  if p_status not in ('acknowledged','resolved','ignored','snoozed') then
    raise exception 'Statut alerte invalide: %', p_status;
  end if;
  insert into public.app_alert_state as s (alert_key, status, acted_by, acted_at, snoozed_until, note, updated_at)
  values (p_alert_key, p_status, p_by, now(), p_snoozed_until, p_note, now())
  on conflict (alert_key) do update
     set status        = excluded.status,
         acted_by      = excluded.acted_by,
         acted_at      = now(),
         snoozed_until = excluded.snoozed_until,
         note          = coalesce(excluded.note, s.note),
         updated_at    = now()
  returning * into v_row;
  return v_row;
end
$function$;

revoke all on function public.app_alert_set_state(text, text, uuid, text, timestamptz) from public, anon;
grant execute on function public.app_alert_set_state(text, text, uuid, text, timestamptz) to authenticated, service_role;

-- 3) Vue gouvernee : alerte + etat (robuste a la recurrence).
create or replace view public.alerts_governed
with (security_invoker = true) as
select
  a.alert_key, a.source, a.category, a.severity, a.owner_role, a.owner_email,
  a.object_type, a.object_id, a.title, a.action_url, a.created_at, a.updated_at,
  case when s.alert_key is not null and s.acted_at >= a.updated_at then s.status else 'new' end
       as lifecycle_status,
  s.acted_by      as lifecycle_acted_by,
  s.acted_at      as lifecycle_acted_at,
  s.snoozed_until as lifecycle_snoozed_until,
  s.note          as lifecycle_note
from public.alerts_current a
left join public.app_alert_state s on s.alert_key = a.alert_key;

grant select on public.alerts_governed to authenticated, service_role;
