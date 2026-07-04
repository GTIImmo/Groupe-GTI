-- ============================================================================
-- patch_rapprochement_alerts_onconflict_2026-07-04.sql
--
-- Corrige app_generate_rapprochement_alerts : le cron "rapprochement-alerts"
-- echouait (72x le 04/07) avec "duplicate key value violates unique constraint
-- app_notif_unread_uq". Cause : le garde-fou NOT EXISTS teste
-- (contact_search_key, app_dossier_id, type, perspective), alors que l'index
-- unique partiel porte sur (negociateur_email, app_dossier_id, type) WHERE
-- read_at IS NULL. Deux recherches distinctes du meme negociateur sur le meme
-- bien passent le garde-fou mais violent la contrainte -> l'insert plante et le
-- cron s'arrete => negociateurs non notifies des nouveaux matches (leads perdus).
--
-- Fix : ajouter ON CONFLICT (...) WHERE (read_at is null) DO NOTHING aux 2 INSERT
-- (aligne sur l'index partiel). L'insert saute le doublon au lieu de planter ;
-- le NOT EXISTS est conserve (reduit deja la plupart des cas). Aucune autre
-- modification de la logique.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.app_generate_rapprochement_alerts(p_min_score integer DEFAULT 80, p_since timestamp with time zone DEFAULT (now() - '3 days'::interval))
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_count int := 0;
begin
  with cand as (
    select distinct on (h.contact_search_key, h.app_dossier_id)
           h.contact_search_key, h.app_dossier_id, r.score,
           cc.negociateur_email as contact_nego, cc.display_name,
           d.negociateur_email as bien_nego, d.numero_mandat, d.ville, d.hektor_annonce_id, d.titre_bien
    from app_rapprochement_score_history h
    join app_rapprochement r on r.contact_search_key = h.contact_search_key and r.app_dossier_id = h.app_dossier_id
    join app_contact_search_current s on s.contact_search_key = h.contact_search_key and s.is_active = true and coalesce(s.archive,false) = false
    left join app_contact_current cc on cc.hektor_contact_id = r.hektor_contact_id
    left join app_dossier_current d on d.app_dossier_id = h.app_dossier_id
    where h.reason = 'new_bien' and h.computed_at >= p_since and r.eligible = true and r.score >= p_min_score
    order by h.contact_search_key, h.app_dossier_id, h.computed_at desc
  ),
  ins_contact as (
    insert into app_notification(negociateur_email, type, title, body, payload, contact_search_key, app_dossier_id)
    select c.contact_nego, 'nouveau_rapprochement', 'Nouveau bien correspondant',
           coalesce('V' || c.hektor_annonce_id, c.numero_mandat, '#' || c.app_dossier_id)
             || coalesce(' · ' || c.ville, '') || ' · score ' || c.score || ' %',
           jsonb_build_object('perspective','contact','score',c.score,'titre',c.titre_bien,'ville',c.ville),
           c.contact_search_key, c.app_dossier_id
    from cand c
    where c.contact_nego is not null
      and not exists (select 1 from app_notification n
        where n.contact_search_key = c.contact_search_key and n.app_dossier_id = c.app_dossier_id
          and n.type = 'nouveau_rapprochement' and n.payload->>'perspective' = 'contact')
    on conflict (negociateur_email, app_dossier_id, type) where (read_at is null) do nothing
    returning 1
  ),
  ins_bien as (
    insert into app_notification(negociateur_email, type, title, body, payload, contact_search_key, app_dossier_id)
    select c.bien_nego, 'nouveau_rapprochement', 'Nouvel acquéreur correspondant',
           coalesce(c.display_name, 'Un acquéreur') || ' · score ' || c.score || ' %',
           jsonb_build_object('perspective','bien','score',c.score,'acquereur',c.display_name),
           c.contact_search_key, c.app_dossier_id
    from cand c
    where c.bien_nego is not null
      and not exists (select 1 from app_notification n
        where n.contact_search_key = c.contact_search_key and n.app_dossier_id = c.app_dossier_id
          and n.type = 'nouveau_rapprochement' and n.payload->>'perspective' = 'bien')
    on conflict (negociateur_email, app_dossier_id, type) where (read_at is null) do nothing
    returning 1
  )
  select (select count(*) from ins_contact) + (select count(*) from ins_bien) into v_count;
  return v_count;
end $function$;
