-- Rollback du Lot B (suivi email de rapprochement + consentement).
-- Supprime UNIQUEMENT les tables neuves créées par patch_email_tracking_2026-06-16.sql.
-- L'ordre respecte les dépendances (les enfants d'abord via cascade).

begin;

drop table if exists public.app_email_event cascade;
drop table if exists public.app_email_envoi_bien cascade;
drop table if exists public.app_email_envoi cascade;
drop table if exists public.app_contact_consent cascade;

commit;
