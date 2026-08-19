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

with
u00 as (
  update app_dossier_current x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u01 as (
  update app_dossier_detail_current x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u02 as (
  update app_work_item_current x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u03 as (
  update app_mandat_broadcast_current x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u04 as (
  update app_mandat_register_current x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u05 as (
  update app_contact_relation_current x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u06 as (
  update app_rapprochement x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u07 as (
  update app_rapprochement_score_history x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u08 as (
  update app_console_document x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u09 as (
  update app_console_photo x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u10 as (
  update app_console_job x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u11 as (
  update app_console_deleted_annonce_log x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u12 as (
  update app_notification x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u13 as (
  update app_email_event x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u14 as (
  update app_email_envoi_bien x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u15 as (
  update app_bien_acquereur_statut x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u16 as (
  update app_proposition x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u17 as (
  update app_relance_rapprochement x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u18 as (
  update app_appointment_public_link x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u19 as (
  update app_appointment_request x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u20 as (
  update app_dossier_estimation x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u21 as (
  update app_dossier_cadastre x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u22 as (
  update app_diffusion_request x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u23 as (
  update app_diffusion_target x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u24 as (
  update app_google_calendar_event_link x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u25 as (
  update app_espace_message x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u26 as (
  update app_espace_visite_request x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u27 as (
  update app_agent_run x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u28 as (
  update app_annonce_pending x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u29 as (
  update app_dossier_v1 x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u30 as (
  update app_dossier_detail_v1 x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
u31 as (
  update app_work_item_v1 x set app_dossier_id = m.nouveau_ticket
  from app_ticket_migration m
  where x.app_dossier_id = m.ancien_ticket
  returning 1),
trace as (
  update app_ticket_migration set applique_at = now()
  where applique_at is null
  returning 1)
select
  (select count(*) from u00) as dossier_current,
  (select count(*) from u01) as dossier_detail_current,
  (select count(*) from u02) as work_item_current,
  (select count(*) from u03) as mandat_broadcast_current,
  (select count(*) from u04) as mandat_register_current,
  (select count(*) from u05) as contact_relation_current,
  (select count(*) from u06) as rapprochement,
  (select count(*) from u07) as rapprochement_score_history,
  (select count(*) from u08) as console_document,
  (select count(*) from u09) as console_photo,
  (select count(*) from u10) as console_job,
  (select count(*) from u11) as console_deleted_annonce_log,
  (select count(*) from u12) as notification,
  (select count(*) from u13) as email_event,
  (select count(*) from u14) as email_envoi_bien,
  (select count(*) from u15) as bien_acquereur_statut,
  (select count(*) from u16) as proposition,
  (select count(*) from u17) as relance_rapprochement,
  (select count(*) from u18) as appointment_public_link,
  (select count(*) from u19) as appointment_request,
  (select count(*) from u20) as dossier_estimation,
  (select count(*) from u21) as dossier_cadastre,
  (select count(*) from u22) as diffusion_request,
  (select count(*) from u23) as diffusion_target,
  (select count(*) from u24) as google_calendar_event_link,
  (select count(*) from u25) as espace_message,
  (select count(*) from u26) as espace_visite_request,
  (select count(*) from u27) as agent_run,
  (select count(*) from u28) as annonce_pending,
  (select count(*) from u29) as dossier_v1,
  (select count(*) from u30) as dossier_detail_v1,
  (select count(*) from u31) as work_item_v1,
  (select count(*) from trace) as paires_tracees;

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
