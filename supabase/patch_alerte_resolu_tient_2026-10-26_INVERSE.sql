-- ============================================================================
-- INVERSE -- patch_alerte_resolu_tient_2026-10-26.sql
-- ============================================================================
-- Ne juge QUE sa part (lecon 31) : remet la vue du 05/07 (patch_alert_lifecycle) mot pour
-- mot et verifie que l'empreinte revient EXACTEMENT a 13f1ee80... ; options et droits gardes.
-- Les clics deja poses dans app_alert_state ne sont PAS touches.
-- ============================================================================

do $inverse$
declare
  v_src text;
begin
  v_src := replace(pg_get_viewdef('public.alerts_governed'::regclass, true), chr(13), '');
  if position('app_monitor_event' in v_src) = 0 then
    raise exception 'STOP : la vue ne porte pas la forme du 26/10 -- rien n a ete touche';
  end if;

  execute replace($def$
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
left join public.app_alert_state s on s.alert_key = a.alert_key
$def$, chr(13), '');

  v_src := replace(pg_get_viewdef('public.alerts_governed'::regclass, true), chr(13), '');
  if md5(v_src) <> '13f1ee80ebed4999303893b454756d43' then
    raise exception 'ATTENTION : empreinte % apres retour (attendue 13f1ee80...) -- relire la vue', md5(v_src);
  end if;
end
$inverse$;

select 'empreinte revenue' as controle,
       case when md5(replace(pg_get_viewdef('public.alerts_governed'::regclass, true), chr(13), ''))
                 = '13f1ee80ebed4999303893b454756d43' then 'OK (13f1ee80)' else 'NON' end as verdict
union all
select 'options', (select array_to_string(reloptions, ',') from pg_class where oid = 'public.alerts_governed'::regclass);
