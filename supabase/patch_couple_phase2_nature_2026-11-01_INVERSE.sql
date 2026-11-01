-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PHASE 2 — RETOUR ARRIÈRE                                  01/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- ⛔ D'ABORD : APP_CONTACT_NATURE=0 (ou retiré) dans C:\Hektor\Projet\.env, sinon le
--   push des contacts de la nuit échouerait sur les colonnes disparues.
-- Supprime les six colonnes et la clé de battement. Rien d'autre n'est touché.
-- (Le battement de l'étape locale redevient sans effet, sans erreur.)
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

alter table public.app_contact_current
  drop column if exists nature_fiche,
  drop column if exists couple_deuxieme,
  drop column if exists civilite_app,
  drop column if exists civilite_source,
  drop column if exists suit_principale_archivee,
  drop column if exists supprimee_chez_hektor;
delete from public.app_worker_registry where worker_key = 'phase2.nature_contacts';

COMMIT;

-- CONTROLE : tout doit valoir 0, et la table garde ses autres lignes
select
  (select count(*) from information_schema.columns
    where table_schema = 'public' and table_name = 'app_contact_current'
      and column_name in ('nature_fiche','couple_deuxieme','civilite_app','civilite_source',
                          'suit_principale_archivee','supprimee_chez_hektor')) as colonnes,
  (select count(*) from public.app_worker_registry where worker_key = 'phase2.nature_contacts') as battement,
  (select count(*) from public.app_contact_current) as contacts;
