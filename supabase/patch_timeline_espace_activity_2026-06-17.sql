-- Historique rapprochement : ajout de l'activité ESPACE CLIENT à app_get_search_timeline.
-- Les 4 branches existantes (proposition/relance/nouveau/visite) sont INCHANGÉES (par p_search_key).
-- Les branches espace sont jointes par (hektor_contact_id + search_index) STABLE — robuste au
-- changement de contact_search_key lors d'une édition de recherche. Réversible (réappliquer l'ancienne def).

create or replace function public.app_get_search_timeline(p_search_key text, p_limit integer default 15)
returns table(event_at timestamp with time zone, kind text, title text, sub text)
language sql stable security definer set search_path to 'public'
as $function$
  with cur as (
    select hektor_contact_id, search_index
    from app_contact_search_current where contact_search_key = p_search_key limit 1
  ),
  env as (
    select e.id as envoi_id
    from app_email_envoi e join cur
      on e.hektor_contact_id = cur.hektor_contact_id and e.search_index = cur.search_index
    where cur.hektor_contact_id is not null
  ),
  ev as (
    select pr.created_at as event_at, 'proposition'::text as kind, 'Bien proposé'::text as title,
           coalesce(d.numero_mandat, 'V'||d.hektor_annonce_id, '#'||pr.app_dossier_id) || ' · ' || pr.channel as sub
    from app_proposition pr
    left join app_dossier_current d on d.app_dossier_id = pr.app_dossier_id
    where pr.contact_search_key = p_search_key
    union all
    select r.created_at, 'relance', coalesce(r.label, 'Relance'), coalesce(r.sub, '')
    from app_relance_rapprochement r
    where r.contact_search_key = p_search_key
    union all
    select h.computed_at, 'nouveau', 'Nouveau bien correspondant',
           coalesce(d.numero_mandat, 'V'||d.hektor_annonce_id, '#'||h.app_dossier_id) || ' · score ' || h.score || ' %'
    from app_rapprochement_score_history h
    left join app_dossier_current d on d.app_dossier_id = h.app_dossier_id
    where h.contact_search_key = p_search_key and h.reason = 'new_bien'
    union all
    select e.starts_at, 'visite',
           case when e.status='cancelled' then 'Visite annulée' else 'Visite planifiée' end,
           coalesce(e.metadata_json->>'titre_bien', d.numero_mandat, 'V'||d.hektor_annonce_id, '#'||e.app_dossier_id)
             || ' · ' || to_char(e.starts_at at time zone 'Europe/Paris', 'DD/MM "à" HH24"h"MI')
    from app_google_calendar_event_link e
    left join app_dossier_current d on d.app_dossier_id = e.app_dossier_id
    where e.metadata_json->>'contact_search_key' = p_search_key
      and e.event_type = 'visite' and coalesce(e.status,'active') <> 'deleted'
    union all
    -- ESPACE CLIENT : feedback (intérêt / refus + raison)
    select eb.feedback_at, 'espace_feedback',
           case eb.feedback when 'interesse' then 'Bien retenu (espace client)' else 'Bien écarté (espace client)' end,
           coalesce(d.numero_mandat, 'V'||d.hektor_annonce_id, '#'||eb.app_dossier_id, '')
             || case when eb.feedback='refuse' and eb.feedback_reason is not null then ' · ' || eb.feedback_reason else '' end
    from app_email_envoi_bien eb join env on eb.envoi_id = env.envoi_id
    left join app_dossier_current d on d.app_dossier_id = eb.app_dossier_id
    where eb.feedback is not null and eb.feedback_at is not null
    union all
    -- ESPACE CLIENT : questions du client
    select m.created_at, 'espace_question', 'Question du client (espace)', left(m.message, 80)
    from app_espace_message m join env on m.envoi_id = env.envoi_id
    union all
    -- ESPACE CLIENT : première consultation de l'espace
    select min(ee.created_at), 'espace_ouvert', 'Espace consulté', ''
    from app_email_event ee join env on ee.envoi_id = env.envoi_id
    where ee.type = 'open' group by ee.envoi_id
  )
  select event_at, kind, title, sub from ev where event_at is not null order by event_at desc limit p_limit
$function$;
