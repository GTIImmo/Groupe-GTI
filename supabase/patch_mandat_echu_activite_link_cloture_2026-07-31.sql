-- ============================================================================
-- patch_mandat_echu_activite_link_cloture_2026-07-31.sql
--
-- Deux corrections sur l'alerte « Mandat échu » (cockpit / cloche).
--
-- Fix 1 — MAUVAIS LIEN (app_cockpit_activite) :
--   La RPC transformait TOUTE notification (sauf type '%rapproch%') en evenement kind
--   'lead', or CK_ACTI_KMAP['lead'] mappe sur rub 'rapprochement'. Une alerte de MANDAT
--   ('mandat_echu') s'affichait donc avec une action « Rapprocher » (lien faux).
--   -> On route les notifications de type 'mandat%' vers kind 'mandat' (rub Mandat,
--      action « Suivre », aud 'mandant'). Le reste des notifications reste 'lead'.
--
-- Fix 2 — ALERTE « ECHU MAIS CLOS » (app_generate_mandat_echu_alerts) :
--   Un mandat CLOTURE (clôture posée) n'est jamais « échu » : la clôture prime sur
--   l'échéance. La fonction ne testait que statut_annonce (etat de la TRANSACTION), pas la
--   clôture du mandat. Un cycle clos dont l'échéance était dépassée gardait/regenerait une
--   alerte « échu ».
--   -> Gate la génération ET le nettoyage sur mandat_date_cloture. Comme app_dossier_current
--      ne porte pas cette colonne (seul app_mandat_register_current l'a), on joint le registre
--      sur (hektor_annonce_id, numero_mandat).
--   Mesure du 31/07 : 141 alertes échu -> 3 retirees (2 « clos » + 1 dossier re-mandate),
--   138 restantes (vrais échus), 0 « échu mais clos ».
--
-- Applique en base via migration `mandat_echu_activite_link_and_cloture_gate` le 2026-07-31.
-- NB : ne PAS re-executer cron.schedule('mandat-echu-alerts', ...) — deja planifie.
-- ============================================================================

-- Fix 1 : app_cockpit_activite — notification de MANDAT -> kind 'mandat' (rub Mandat).
CREATE OR REPLACE FUNCTION public.app_cockpit_activite(p_app_dossier_id bigint, p_limit integer DEFAULT 30)
 RETURNS TABLE(kind text, aud text, at timestamp with time zone, lead text, rest text, actor text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  with evts as (
    select 'match'::text kind, 'acq'::text aud,
           coalesce(max(r.first_seen_at), max(r.computed_at)) at,
           (count(distinct r.contact_search_key)::text
             || ' acquéreur' || case when count(distinct r.contact_search_key)>1 then 's' else '' end
             || ' correspondant' || case when count(distinct r.contact_search_key)>1 then 's' else '' end) lead,
           coalesce('meilleur score ' || max(r.score)::text || ' %','') rest, null::text actor
    from app_rapprochement r
    join app_contact_search_current s
         on s.contact_search_key = r.contact_search_key
        and s.is_active = true and coalesce(s.archive,false) = false
    where r.eligible = true and r.app_dossier_id = p_app_dossier_id
    having count(distinct r.contact_search_key) > 0

    union all
    -- Notification de MANDAT -> kind 'mandat' (rub Mandat) ; sinon 'lead' (acquereur).
    select
      case when n.type ilike 'mandat%' then 'mandat' else 'lead' end,
      case when n.type ilike 'mandat%' then 'mandant' else 'acq' end,
      n.created_at, coalesce(n.title,'Notification'), coalesce(n.body,''), null
    from app_notification n where n.app_dossier_id = p_app_dossier_id and n.type not ilike '%rapproch%'

    union all
    select 'rdv','acq', coalesce(g.starts_at, g.created_at), coalesce(g.summary,'Rendez-vous'), coalesce(g.location,''), g.created_by_email
    from app_google_calendar_event_link g
    where g.app_dossier_id = p_app_dossier_id and coalesce(g.status,'active') <> 'deleted'

    union all
    -- Retour acquéreur sur un bien proposé : DISTINGUE le coup de cœur du refus (motif humanisé).
    select case when b.feedback = 'refuse' then 'pass' else 'like' end, 'acq', b.feedback_at,
           case when b.feedback = 'refuse' then 'Pas intéressé' else 'Coup de coeur' end,
           case b.feedback_reason
             when 'trop_cher'  then 'Trop cher'
             when 'secteur'    then 'Mauvais secteur'
             when 'trop_petit' then 'Trop petit'
             when 'autre'      then 'Autre motif'
             else coalesce(nullif(initcap(replace(b.feedback_reason, '_', ' ')), ''),
                           case when b.feedback = 'refuse' then 'Sans motif précisé' else '' end)
           end,
           null
    from app_email_envoi_bien b where b.app_dossier_id = p_app_dossier_id and b.feedback is not null

    union all
    select 'relance','acq', coalesce(r.created_at, r.updated_at), coalesce(r.label,'Relance'), coalesce(r.sub,''), r.negociateur_email
    from app_relance_rapprochement r where r.app_dossier_id = p_app_dossier_id

    union all
    select 'offer','acq', p.created_at, 'Proposition acquereur', coalesce(p.note, p.status_after,''), p.negociateur_email
    from app_proposition p where p.app_dossier_id = p_app_dossier_id

    union all
    select 'visitreq','acq', v.created_at, coalesce(v.contact_name,'Demande de visite'), coalesce(v.message,'demande de visite'), v.negociateur_email
    from app_espace_visite_request v where v.app_dossier_id = p_app_dossier_id

    union all
    select 'estimopen','mandant', e.created_at, 'Avis de valeur ouvert par le propriétaire', '', null
    from app_email_event e where e.app_dossier_id = p_app_dossier_id and e.type = 'download'

    union all
    select 'estimopen','mandant', ev.sent_at, 'Avis de valeur envoyé au propriétaire',
           coalesce(ev.recipient_email,''), null
    from app_email_envoi ev
    join app_email_envoi_bien eb on eb.envoi_id = ev.id
    where eb.app_dossier_id = p_app_dossier_id
      and ev.sent_at is not null
      and ev.subject ilike 'Votre estimation%'

    union all
    select 'sign','mandant',
           coalesce(
             case when (d.metadata_json->'signature'->>'sent_at') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                  then (d.metadata_json->'signature'->>'sent_at')::timestamptz end,
             d.created_at),
           case when d.document_name ilike '%avenant%' then 'Avenant ' else 'Mandat ' end ||
             case (d.metadata_json->'signature'->>'status')
               when 'signed' then 'signé' when 'pending' then 'envoyé en signature'
               when 'cancelled' then 'signature annulée' else 'signature' end,
           coalesce(d.document_name,''), null
    from app_console_document d
    where d.app_dossier_id = p_app_dossier_id
      and (d.metadata_json->'signature'->>'status') in ('signed','pending','cancelled')
      and ((d.metadata_json->'signature'->>'procedure_id') is not null
           or (d.metadata_json->'signature'->>'status') = 'signed')

    union all
    select 'sign','mandant', coalesce(j.finished_at, j.requested_at),
           case j.job_type when 'relance_signature' then 'Relance de signature'
                           when 'cancel_signature_procedure' then 'Signature annulée' end,
           '', null
    from app_console_job j
    where j.app_dossier_id = p_app_dossier_id and j.status='done'
      and j.job_type in ('relance_signature','cancel_signature_procedure')

    union all
    select 'estimopen','mandant', max(coalesce(j.finished_at, j.requested_at)), 'Avis de valeur généré', '', null
    from app_console_job j
    where j.app_dossier_id = p_app_dossier_id and j.status='done' and j.job_type='generate_estimation_pdf'
    group by date_trunc('day', coalesce(j.finished_at, j.requested_at))

    union all
    select 'mandat','mandant', max(coalesce(j.finished_at, j.requested_at)), 'Document de mandat préparé', '', null
    from app_console_job j
    where j.app_dossier_id = p_app_dossier_id and j.status='done' and j.job_type='generate_mandat_document'
    group by date_trunc('day', coalesce(j.finished_at, j.requested_at))

    union all
    select case when d.request_type ilike '%baisse%' then 'price'
                when d.request_type ilike '%annul%' then 'requalif' else 'mandat' end,
           'mandant', ev.event_at, coalesce(ev.event_label, d.request_type), coalesce(ev.actor_role,''), ev.actor_name
    from app_diffusion_request_event ev
    join app_diffusion_request d on d.id::text = ev.diffusion_request_id
    where d.app_dossier_id = p_app_dossier_id
  )
  select kind, aud, at, lead, rest, actor from evts
  where at is not null order by at desc
  limit greatest(1, least(coalesce(p_limit,30), 100));
$function$;

-- Fix 2 : app_generate_mandat_echu_alerts — un mandat CLOTURE n'est jamais « échu ».
CREATE OR REPLACE FUNCTION public.app_generate_mandat_echu_alerts()
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_count int := 0;
begin
  -- 1) Auto-nettoyage : renouvelé / clos / vendu / archivé / sans mandat / dossier disparu
  --    OU mandat courant CLOTURE (clôture au registre).
  delete from app_notification n
  using app_dossier_current d
  where n.type = 'mandat_echu' and n.app_dossier_id = d.app_dossier_id
    and (
      coalesce(d.numero_mandat, '') = ''
      or d.mandat_date_fin !~ '^\d{4}-\d{2}-\d{2}$'
      or d.mandat_date_fin::date >= current_date
      or coalesce(d.archive, '0') = '1'
      or lower(coalesce(d.statut_annonce, '')) similar to '%(clos|clotur|vendu|vente)%'
      or exists (
        select 1 from app_mandat_register_current r
        where r.hektor_annonce_id = d.hektor_annonce_id and r.numero_mandat = d.numero_mandat
          and nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') is not null
      )
    );
  delete from app_notification n
  where n.type = 'mandat_echu'
    and not exists (select 1 from app_dossier_current d where d.app_dossier_id = n.app_dossier_id);

  -- 2) Génération : mandats échu, en EXCLUANT les mandats clôturés.
  with ins as (
    insert into app_notification(negociateur_email, type, title, body, payload, app_dossier_id)
    select d.negociateur_email, 'mandat_echu', 'Mandat échu',
           'Mandat n° ' || coalesce(d.numero_mandat, '?')
             || coalesce(' · ' || d.ville, '')
             || ' — échéance dépassée le ' || to_char(d.mandat_date_fin::date, 'DD/MM/YYYY')
             || '. Demandez l''annulation du mandat ou refaites-en un nouveau.',
           jsonb_build_object(
             'numero_mandat', d.numero_mandat,
             'mandat_date_fin', d.mandat_date_fin,
             'hektor_annonce_id', d.hektor_annonce_id,
             'titre', d.titre_bien,
             'ville', d.ville
           ),
           d.app_dossier_id
    from app_dossier_current d
    where d.negociateur_email is not null and d.negociateur_email <> ''
      and coalesce(d.numero_mandat, '') <> ''
      and d.mandat_date_fin ~ '^\d{4}-\d{2}-\d{2}$'
      and d.mandat_date_fin::date < current_date
      and coalesce(d.archive, '0') <> '1'
      and lower(coalesce(d.statut_annonce, '')) not similar to '%(clos|clotur|vendu|vente)%'
      and not exists (
        select 1 from app_mandat_register_current r
        where r.hektor_annonce_id = d.hektor_annonce_id and r.numero_mandat = d.numero_mandat
          and nullif(btrim(coalesce(r.mandat_date_cloture, '')), '') is not null
      )
      and not exists (
        select 1 from app_notification n
        where n.app_dossier_id = d.app_dossier_id and n.type = 'mandat_echu'
      )
    on conflict (negociateur_email, app_dossier_id, type) where (read_at is null) do nothing
    returning 1
  )
  select count(*) from ins into v_count;
  return v_count;
end $function$;
