-- =====================================================================
-- Alignement des identifiants de dossier -- Supabase adopte la serie locale
-- Date : 2026-08-19
--
-- POURQUOI. app_dossier.id est distribue par le serveur local. Le 05/06/2026,
-- une regle de menage a supprime puis recree 55 426 dossiers : AUTOINCREMENT
-- ne rend jamais le meme numero. Supabase porte encore la serie de mars pour
-- 12 162 annonces courantes. Le pont entre les deux machines est aujourd'hui
-- hektor_annonce_id -- un identifiant qui appartient a Hektor, et qui doit
-- disparaitre. Il faut donc que les deux machines s'accordent sur un numero
-- a elles : celui du local, qui reste l'atelier qui les distribue.
--
-- PRE-VOL, mesure le 19/08/2026 :
--   13 220 annonces courantes, toutes presentes en local
--    1 048 deja alignees + 10 alignees a la main (essai valide)
--   12 162 a aligner  -> table app_ticket_migration
--        0 collision (aucun ticket cible deja pris)
--        0 doublon de hektor_annonce_id
--        0 heurt d'unicite sur les 10 tables dont la cle contient app_dossier_id
--
-- ATOMIQUE. Une seule instruction : soit tout passe, soit rien ne bouge.
-- REVERSIBLE. app_ticket_migration conserve les 12 162 paires : rejouer les
-- memes UPDATE en inversant ancien/nouveau ramene l'etat anterieur, a condition
-- de le faire avant que de nouvelles lignes ne soient ecrites sous la cible.
--
-- NE PAS lancer pendant le run de nuit (05:30) ni pendant un push.
-- =====================================================================

-- =====================================================================
-- ESSAI A BLANC PAR DEFAUT. Passer ESSAI_A_BLANC a false pour appliquer.
-- Forme exacte executee et validee le 19/08/2026 :
--   341 394 lignes deplacees, 12 162 paires, 0 violation, puis annulation.
-- =====================================================================
do $$
declare
  ESSAI_A_BLANC constant boolean := true;   -- <<< false pour appliquer
  t text; n bigint; total bigint := 0; rapport text := '';
  tables text[] := array[
    'app_dossier_current','app_dossier_detail_current','app_work_item_current',
    'app_mandat_broadcast_current','app_mandat_register_current','app_contact_relation_current',
    'app_rapprochement','app_rapprochement_score_history','app_console_document','app_console_photo',
    'app_console_job','app_console_deleted_annonce_log','app_notification','app_email_event',
    'app_email_envoi_bien','app_bien_acquereur_statut','app_proposition','app_relance_rapprochement',
    'app_appointment_public_link','app_appointment_request','app_dossier_estimation','app_dossier_cadastre',
    'app_diffusion_request','app_diffusion_target','app_google_calendar_event_link','app_espace_message',
    'app_espace_visite_request','app_agent_run','app_annonce_pending','app_dossier_v1',
    'app_dossier_detail_v1','app_work_item_v1'];
begin
  foreach t in array tables loop
    execute format(
      'update %I x set app_dossier_id = m.nouveau_ticket '
      'from app_ticket_migration m where x.app_dossier_id = m.ancien_ticket', t);
    get diagnostics n = row_count;
    total := total + n;
    if n > 0 then rapport := rapport || t || '=' || n || ' | '; end if;
  end loop;
  update app_ticket_migration set applique_at = now() where applique_at is null;
  get diagnostics n = row_count;
  if ESSAI_A_BLANC then
    raise exception 'ESSAI A BLANC ANNULE VOLONTAIREMENT -- total=% | paires=% | %', total, n, rapport;
  end if;
  raise notice 'ALIGNEMENT APPLIQUE -- total=% | paires=% | %', total, n, rapport;
end $$;

-- =====================================================================
-- VERIFICATION, a passer juste apres (lecture seule)
-- =====================================================================
-- with tickets as (
--   select app_dossier_id as id from app_dossier_current
--   union select app_archive_id from app_archive_annonce_index_current
--   union select app_historical_id from app_historical_annonce_index_current)
-- select
--   (select count(*) from app_dossier_current where app_dossier_id < 25000)      as anciens_restants,   -- attendu 0
--   (select count(*) from (select hektor_annonce_id from app_dossier_current
--                          group by 1 having count(*) > 1) z)                    as doublons,           -- attendu 0
--   (select count(*) from app_console_document
--      where app_dossier_id not in (select id from tickets))                     as documents_decroches,-- attendu 53 (stock ancien)
--   (select count(*) from app_notification
--      where app_dossier_id not in (select id from tickets))                     as notifs_decrochees,  -- attendu 31 (abandonnees, decision du 19/08)
--   (select count(*) from app_ticket_migration where applique_at is not null)    as paires_appliquees;  -- attendu 12 162

-- =====================================================================
-- RETOUR ARRIERE, si necessaire et RAPIDEMENT (avant toute ecriture neuve)
-- =====================================================================
-- Rejouer les memes UPDATE en inversant : x.app_dossier_id = m.nouveau_ticket
-- -> set app_dossier_id = m.ancien_ticket. La table de correspondance suffit.
