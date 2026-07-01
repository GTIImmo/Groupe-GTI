-- =====================================================================
-- Snapshot d'estimation (avis de valeur) par dossier — 2026-07-01.
--
-- L'éditeur d'avis de valeur (EstimationDocumentEditor) calcule à la volée
-- plusieurs sources de données sur le bien (DVF/marché, cadre de vie, cadastre,
-- puis d'autres à venir : BDNB, DPE ADEME, RNB…). Ces données étaient jusqu'ici
-- ÉPHÉMÈRES (perdues à la fermeture de la modale). On les persiste ici, par
-- dossier, au moment de « Générer le PDF » (job generate_estimation_pdf), pour
-- pouvoir les RE-CONSULTER sans tout recalculer — même logique que
-- app_dossier_cadastre, généralisée à toutes les sources.
--
-- Conteneur EXTENSIBLE `sources` : une clé par source de données, chacune de la
-- forme { ok, data, fetched_at }. Ajouter une source = ajouter une clé (aucune
-- migration DDL). Clés de départ : dvf, cadre, cadastre. À venir : bdnb, dpe,
-- rnb, … (cf. plan estimation, « registre des sources »).
--
-- Aucune donnée nominative. Le worker (service_role) écrit cette table ; le
-- front (authenticated) la relit pour ré-afficher la consultation.
-- =====================================================================

create table if not exists public.app_dossier_estimation (
  app_dossier_id     bigint primary key,
  hektor_annonce_id  text,
  valeurs            jsonb,                                -- {basse, estimee, haute}
  sources            jsonb not null default '{}'::jsonb,  -- { dvf:{ok,data,fetched_at}, cadre:{...}, cadastre:{...}, bdnb:{...}, dpe:{...}, rnb:{...} }
  updated_at         timestamptz not null default now()
);

create index if not exists idx_dossier_estimation_annonce on public.app_dossier_estimation (hektor_annonce_id);

-- Données app non sensibles : lecture aux utilisateurs authentifiés ; écriture
-- par le service_role (worker console). Calqué sur app_dossier_cadastre.
alter table public.app_dossier_estimation enable row level security;
drop policy if exists app_dossier_estimation_read on public.app_dossier_estimation;
create policy app_dossier_estimation_read on public.app_dossier_estimation for select to authenticated using (true);
grant select on public.app_dossier_estimation to authenticated;
grant select, insert, update, delete on public.app_dossier_estimation to service_role;
