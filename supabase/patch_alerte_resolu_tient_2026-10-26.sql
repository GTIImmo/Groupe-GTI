-- ============================================================================
-- PATCH B -- un « Résolu » du moniteur TIENT (26/10/2026)
-- ============================================================================
-- Audit : notice/AUDIT_ALERTES_MONITORING_2026-10-24.md §4.2, et le 14/10
--   (notice/AUDIT_MONITORING_ALERTES_2026-10-14.md §11-13, option A jamais tranchee).
--
-- LE DEFAUT. alerts_governed n'applique le clic que si `acted_at >= updated_at`. Or le
--   moniteur reecrit updated_at de CHAQUE alerte a CHAQUE passage (status_row(), l. 1085)
--   -- et il en a besoin : sa purge des statuts obsoletes s'en sert. Un clic tient donc
--   au plus 2 h : « le sapin de Noel se reconstitue tout seul ».
--
-- LE REMEDE, dans la vue seulement, pour les alertes du MONITEUR seulement :
--   le clic vaut tant que l'alerte n'a PAS CHANGE D'ETAT depuis, et au plus 7 JOURS.
--   « Changer d'etat » = une ligne dans app_monitor_event, que le moniteur n'ecrit QUE
--   sur une transition (l. 3576-3585 : 15 en 24 h). Vert -> rouge, rouge -> vert,
--   warning -> critical, illisible : chacun reveille l'alerte.
--   ⭐ Le principe du 05/07 (« jamais masquee a tort ») est GARDE : une alerte qui REPART
--     est une transition, donc un evenement, donc « new ». Ce qui change : un simple
--     REPASSAGE du moniteur n'est plus pris pour une nouvelle emission.
--   ⚠ LIMITE ASSUMEE : une alerte qui EMPIRE SANS CHANGER DE COULEUR (warning 5 -> warning
--     50) reste muette jusqu'a 7 jours. L'e-mail est deja dans ce cas aujourd'hui (il ne
--     part que sur une bascule).
--   Les notifications, relances et demandes de Pauline gardent leur regle, INCHANGEE.
--
-- Meme colonnes, meme ordre, memes types ; security_invoker garde (le lecteur doit pouvoir
--   lire app_monitor_event : meme politique que app_monitor_status -- admin/manager).
-- Seul lecteur : l'ecran Sante (loadAlertsCurrent). Aucune vue ni fonction n'en depend.
--
-- ⛔ AVANT : avoir joue ..._REPETITION.sql. EN CAS DE PROBLEME : ..._INVERSE.sql.
-- EMPREINTE DE DEPART (pg_get_viewdef) : 13f1ee80ebed4999303893b454756d43.
-- ============================================================================

do $patch$
declare
  v_src text;
begin
  v_src := replace(pg_get_viewdef('public.alerts_governed'::regclass, true), chr(13), '');
  if md5(v_src) <> '13f1ee80ebed4999303893b454756d43' then
    raise exception 'STOP : empreinte % au lieu de 13f1ee80... -- la vue a change, la RELIRE.', md5(v_src);
  end if;

  execute replace($def$
create or replace view public.alerts_governed
with (security_invoker = true) as
select
  a.alert_key, a.source, a.category, a.severity, a.owner_role, a.owner_email,
  a.object_type, a.object_id, a.title, a.action_url, a.created_at, a.updated_at,
  case
    when s.alert_key is null then 'new'
    when s.acted_at >= a.updated_at then s.status
    -- 26/10/2026 : alerte du MONITEUR -- le clic tient tant qu'elle n'a pas change d'etat
    --   (aucune transition dans app_monitor_event depuis le clic), et au plus 7 jours.
    when a.source = 'monitoring'
         and s.acted_at > now() - interval '7 days'
         and not exists (select 1 from public.app_monitor_event e
                          where e.event_key = a.object_id
                            and e.observed_at > s.acted_at)
      then s.status
    else 'new'
  end as lifecycle_status,
  s.acted_by      as lifecycle_acted_by,
  s.acted_at      as lifecycle_acted_at,
  s.snoozed_until as lifecycle_snoozed_until,
  s.note          as lifecycle_note
from public.alerts_current a
left join public.app_alert_state s on s.alert_key = a.alert_key
$def$, chr(13), '');

  v_src := replace(pg_get_viewdef('public.alerts_governed'::regclass, true), chr(13), '');
  if position('app_monitor_event' in v_src) = 0 then
    raise exception 'STOP : la vue posee n''est pas la nouvelle forme';
  end if;
  if not exists (select 1 from pg_class where oid = 'public.alerts_governed'::regclass
                  and reloptions @> array['security_invoker=true']) then
    raise exception 'STOP : security_invoker perdu';
  end if;
end
$patch$;

-- ① LE CONTROLE APRES (lecture seule).
select 'empreinte apres pose' as controle,
       md5(replace(pg_get_viewdef('public.alerts_governed'::regclass, true), chr(13), '')) as verdict
union all
select 'options (attendu security_invoker=true)',
       (select array_to_string(reloptions, ',') from pg_class where oid = 'public.alerts_governed'::regclass)
union all
select 'droits', (select relacl::text from pg_class where oid = 'public.alerts_governed'::regclass)
union all
select 'lignes de la vue', (select count(*)::text from public.alerts_governed);
