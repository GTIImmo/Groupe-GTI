-- ============================================================================
-- patch_mandat_echu_alerts_2026-07-30.sql
--
-- Lot A / A6 : alerte « mandat échu » au négociateur (cloche).
-- Fonction Postgres idempotente + auto-nettoyante, calquée sur
-- app_generate_rapprochement_alerts, planifiée en pg_cron quotidien.
--
-- Un mandat est « échu » quand mandat_date_fin (ISO) est dépassée, que le
-- mandat courant existe, et que l'annonce n'est ni close/vendue ni archivée.
-- L'alerte invite le négo à demander l'annulation ou à refaire un mandat.
-- Idempotence : index unique partiel app_notif_unread_uq
-- (negociateur_email, app_dossier_id, type) WHERE read_at IS NULL.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.app_generate_mandat_echu_alerts()
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_count int := 0;
begin
  -- 1) Auto-nettoyage : retirer les alertes échu devenues obsolètes
  --    (mandat renouvelé / clos / vendu / archivé / sans mandat / dossier disparu).
  delete from app_notification n
  using app_dossier_current d
  where n.type = 'mandat_echu' and n.app_dossier_id = d.app_dossier_id
    and (
      coalesce(d.numero_mandat, '') = ''
      or d.mandat_date_fin !~ '^\d{4}-\d{2}-\d{2}$'
      or d.mandat_date_fin::date >= current_date
      or coalesce(d.archive, '0') = '1'
      or lower(coalesce(d.statut_annonce, '')) similar to '%(clos|clotur|vendu|vente)%'
    );
  delete from app_notification n
  where n.type = 'mandat_echu'
    and not exists (select 1 from app_dossier_current d where d.app_dossier_id = n.app_dossier_id);

  -- 2) Génération des alertes pour les mandats échu (une seule par dossier).
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
        select 1 from app_notification n
        where n.app_dossier_id = d.app_dossier_id and n.type = 'mandat_echu'
      )
    on conflict (negociateur_email, app_dossier_id, type) where (read_at is null) do nothing
    returning 1
  )
  select count(*) from ins into v_count;
  return v_count;
end $function$;

-- Planification quotidienne (06:00 UTC), après la synchro nocturne.
select cron.schedule('mandat-echu-alerts', '0 6 * * *', 'select public.app_generate_mandat_echu_alerts()');
