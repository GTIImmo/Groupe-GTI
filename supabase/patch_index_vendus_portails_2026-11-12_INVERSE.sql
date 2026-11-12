-- Retour arriere du patch_index_vendus_portails_2026-11-12.sql.
-- ⚠ Remettre d'abord l'ecran d'avant (api.ts sans ces deux colonnes) : sinon la liste des vendus tombe.
alter table public.app_historical_annonce_index_current
  drop column if exists portails_resume,
  drop column if exists nb_portails_actifs;
