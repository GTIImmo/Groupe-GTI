-- ============================================================================
-- REPETITION -- patch_alerte_resolu_tient_2026-10-26.sql
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS. Le `begin;` et l'ERREUR VOLONTAIRE de la fin font que
--    RIEN n'est ecrit : ni la vue, ni le clic d'essai, ni l'evenement d'essai.
-- ⚠ Elle touche UNE ligne de app_monitor_status (date de passage simulee) le temps de la
--   transaction : pas a l'heure du moniteur (h48).
--
-- CE QU'ELLE PROUVE :
--   1-avant    empreinte 13f1ee80, options, droits ; la reponse de la vue ligne par ligne
--   2-pose     la vue passe ; security_invoker et droits GARDES
--   3-rien     AUCUNE ligne actuelle ne change de reponse (notifications, relances, Pauline
--              ET moniteur) -- aucun ancien clic ne fait taire une alerte d'aujourd'hui
--   4-tient    un clic « Resolu », puis un repassage du moniteur : l'ancienne regle dit
--              « new » (le defaut), la nouvelle dit « resolved »
--   5-reveil   une transition apres le clic (evenement) -> « new » : jamais masquee a tort
--   6-7jours   un clic de plus de 7 jours sans transition -> « new »
--   7-duree    lecture de la vue entiere
--   8-retour   l'inverse remet EXACTEMENT 13f1ee80, options gardees
-- ============================================================================

begin;
set local statement_timeout = '60s';
set local lock_timeout = '10s';

create temporary table essai_mesures (id serial, etape text, mesure text, valeur text) on commit drop;
create temporary table essai_avant on commit drop as
  select alert_key, lifecycle_status from public.alerts_governed;

insert into essai_mesures (etape, mesure, valeur) values
 ('1-avant  ', 'empreinte                    ', md5(replace(pg_get_viewdef('public.alerts_governed'::regclass, true), chr(13), ''))),
 ('1-avant  ', 'options                      ', (select array_to_string(reloptions, ',') from pg_class where oid = 'public.alerts_governed'::regclass)),
 ('1-avant  ', 'droits                       ', (select relacl::text from pg_class where oid = 'public.alerts_governed'::regclass)),
 ('1-avant  ', 'lignes                       ', (select count(*)::text from essai_avant));

-- =========================== 2. LA POSE (copie conforme du patch) ==========
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

insert into essai_mesures (etape, mesure, valeur) values
 ('2-pose   ', 'empreinte apres pose         ', md5(replace(pg_get_viewdef('public.alerts_governed'::regclass, true), chr(13), ''))),
 ('2-pose   ', 'options                      ', (select array_to_string(reloptions, ',') from pg_class where oid = 'public.alerts_governed'::regclass)),
 ('2-pose   ', 'droits                       ',
    case when (select relacl::text from pg_class where oid = 'public.alerts_governed'::regclass)
              = (select valeur from essai_mesures where etape like '1%' and mesure like 'droits%') then 'inchanges -- OK' else 'STOP : CHANGES' end);

-- =========================== 3. RIEN NE BOUGE AUJOURD'HUI ==================
insert into essai_mesures (etape, mesure, valeur)
select '3-rien   ', 'reponses changees            ',
       count(*) filter (where b.alert_key is null or b.lifecycle_status is distinct from a.lifecycle_status)
       || ' sur ' || count(*) || ' lignes'
       || case when count(*) filter (where b.alert_key is null or b.lifecycle_status is distinct from a.lifecycle_status) = 0
               then '  -- OK' else '  -- STOP' end
  from essai_avant a left join public.alerts_governed b on b.alert_key = a.alert_key;

-- =========================== 4 a 6. LES TEMOINS ============================
do $temoins$
declare
  k text; cle_statut text; v_ancienne text; v_nouvelle text;
begin
  select alert_key, object_id into k, cle_statut
    from public.alerts_current
   where source = 'monitoring' and object_id <> 'monitor.summary'
   order by alert_key limit 1;
  if k is null then
    insert into essai_mesures (etape, mesure, valeur) values ('4-tient  ', 'alerte d''essai              ', 'AUCUNE alerte du moniteur ouverte : temoins non joues');
    return;
  end if;
  insert into essai_mesures (etape, mesure, valeur) values ('4-tient  ', 'alerte d''essai               ', k);

  -- un clic « Resolu » maintenant
  insert into public.app_alert_state (alert_key, status, acted_at, updated_at) values (k, 'resolved', now(), now())
  on conflict (alert_key) do update set status = 'resolved', acted_at = now(), updated_at = now(), snoozed_until = null;
  -- puis le moniteur repasse 2 h plus tard, sans changement d'etat (il reecrit updated_at)
  update public.app_monitor_status set updated_at = now() + interval '2 hours' where status_key = cle_statut;

  select case when s.acted_at >= a.updated_at then s.status else 'new' end, g.lifecycle_status
    into v_ancienne, v_nouvelle
    from public.alerts_current a join public.app_alert_state s on s.alert_key = a.alert_key
    join public.alerts_governed g on g.alert_key = a.alert_key
   where a.alert_key = k;
  insert into essai_mesures (etape, mesure, valeur) values ('4-tient  ', 'apres un repassage           ',
    'ancienne regle ' || v_ancienne || ' / nouvelle ' || v_nouvelle
    || case when v_ancienne = 'new' and v_nouvelle = 'resolved' then '  -- OK (le clic tient)' else '  -- STOP' end);

  -- 5. une transition apres le clic (le moniteur l'ecrit seulement quand l'etat change)
  insert into public.app_monitor_event (event_key, domain, component, check_name, status, severity, message, observed_at, details_json, source)
  values (cle_statut, 'system', 'essai', 'essai', 'critical', 'critical', 'ESSAI repetition 26/10', now() + interval '1 hour', '{}'::jsonb, 'essai_repetition');
  select lifecycle_status into v_nouvelle from public.alerts_governed where alert_key = k;
  insert into essai_mesures (etape, mesure, valeur) values ('5-reveil ', 'transition apres le clic     ',
    v_nouvelle || case when v_nouvelle = 'new' then '  -- OK (jamais masquee a tort)' else '  -- STOP' end);
  delete from public.app_monitor_event where source = 'essai_repetition';

  -- 6. un clic de plus de 7 jours, sans transition depuis
  update public.app_alert_state set acted_at = now() - interval '8 days' where alert_key = k;
  delete from public.app_monitor_event where event_key = cle_statut and observed_at > now() - interval '8 days';
  select lifecycle_status into v_nouvelle from public.alerts_governed where alert_key = k;
  insert into essai_mesures (etape, mesure, valeur) values ('6-7jours ', 'clic de 8 jours, rien depuis ',
    v_nouvelle || case when v_nouvelle = 'new' then '  -- OK (le plafond joue)' else '  -- STOP' end);
end
$temoins$;

do $duree$
declare t0 timestamptz; n int;
begin
  t0 := clock_timestamp();
  select count(*) into n from public.alerts_governed;
  insert into essai_mesures (etape, mesure, valeur) values ('7-duree  ', 'lecture de la vue            ',
    n || ' lignes en ' || round(extract(epoch from clock_timestamp() - t0) * 1000) || ' ms');
end
$duree$;

-- =========================== 8. LE RETOUR (copie conforme de l'inverse) ====
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
end
$inverse$;

insert into essai_mesures (etape, mesure, valeur)
select '8-retour ', 'empreinte revenue            ',
       case when md5(replace(pg_get_viewdef('public.alerts_governed'::regclass, true), chr(13), ''))
                 = '13f1ee80ebed4999303893b454756d43' then 'oui (13f1ee80)'
            else 'NON : ' || md5(replace(pg_get_viewdef('public.alerts_governed'::regclass, true), chr(13), '')) end
union all
select '8-retour ', 'options                      ', (select array_to_string(reloptions, ',') from pg_class where oid = 'public.alerts_governed'::regclass);

do $fin$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id) into v_txt from essai_mesures;
  raise exception '%', 'ESSAI ANNULE -- rien n a ete ecrit.' || chr(10) || v_txt;
end
$fin$;

rollback;
