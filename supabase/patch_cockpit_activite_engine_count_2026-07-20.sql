-- Patch 2026-07-20 — Fil d'activité du cockpit (RPC app_cockpit_activite)
-- Déjà appliqué en prod (base dwaqxfrinihnychuoptk). Versionné ici pour garder le
-- repo cohérent avec la base (la RPC n'était versionnée nulle part auparavant).
--
-- Deux corrections du bloc « Activité » (retour Frédéric) :
--   1) Le compteur d'acquéreurs rapprochés vient désormais du MOTEUR (table
--      app_rapprochement, même jointure que le badge du listing Annonces) et non du
--      nombre de notifications, qui sous-comptait (« 1 acquéreur » alors que le moteur
--      en rapprochait 16, 27, 114, 215…). Le fil « donne le résultat du rapprochement ».
--   2) Le « meilleur score » était comparé comme du TEXTE (donc "90" > "100"). Corrigé :
--      max sur un entier → 100 % s'affiche bien au lieu de 90 %.

CREATE OR REPLACE FUNCTION public.app_cockpit_activite(p_app_dossier_id bigint, p_limit integer DEFAULT 30)
 RETURNS TABLE(kind text, aud text, at timestamp with time zone, lead text, rest text, actor text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  with evts as (
    -- Rapprochement : compteur AUTORITATIF du moteur (table app_rapprochement, même
    -- jointure que le badge du listing) et NON le nombre de notifications, qui sous-comptait
    -- (retour Frédéric : le fil affichait « 1 acquéreur » quand le moteur en rapprochait 16).
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
    select 'lead','acq', n.created_at, coalesce(n.title,'Notification'), coalesce(n.body,''), null
    from app_notification n where n.app_dossier_id = p_app_dossier_id and n.type not ilike '%rapproch%'

    union all
    select 'rdv','acq', coalesce(g.starts_at, g.created_at), coalesce(g.summary,'Rendez-vous'), coalesce(g.location,''), g.created_by_email
    from app_google_calendar_event_link g
    where g.app_dossier_id = p_app_dossier_id and coalesce(g.status,'active') <> 'deleted'

    union all
    select 'like','acq', b.feedback_at, 'Coup de coeur', coalesce(b.feedback_reason, b.feedback), null
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
    select 'sign','mandant',
           case when (d.metadata_json->'signature'->>'status')='pending'
                then coalesce(nullif(d.metadata_json->'signature'->>'sent_at','')::timestamptz, d.updated_at)
                else d.updated_at end,
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
