-- =====================================================================
-- Risques par commune (Géorisques) — pré-chargé, actualisation annuelle
-- 2026-06-26.
--
-- Même logique que la DVF : les risques (inondation, mouvement de terrain,
-- séisme, radon, argiles, industriel…) sont par commune (INSEE) et changent
-- rarement. On pré-charge les communes des 4 départements GTI (42/43/63/07)
-- via `backend/scripts/ingest_georisques.py` (regroupé avec la tâche DVF), et
-- l'avis de valeur lit cette table — aucune dépendance Géorisques à la génération.
-- Source : API Géorisques (gaspar/risques · radon · zonage_sismique · rga).
-- =====================================================================

create table if not exists public.app_commune_risques (
  code_insee text primary key,
  commune    text,
  dept       text,
  risques    text[],        -- risques principaux recensés (GASPAR)
  radon      text,          -- potentiel radon : Faible | Moyen | Élevé
  sismicite  text,          -- zone de sismicité, ex. « 2 - Faible »
  argiles    text,          -- exposition retrait-gonflement argiles, ex. « Moyenne »
  updated_at timestamptz not null default now()
);

create index if not exists idx_commune_risques_dept on public.app_commune_risques (dept);

-- Référence publique non sensible : lecture autorisée aux utilisateurs authentifiés ;
-- écriture par le service_role (script d'ingestion).
alter table public.app_commune_risques enable row level security;
drop policy if exists app_commune_risques_read on public.app_commune_risques;
create policy app_commune_risques_read on public.app_commune_risques for select to authenticated using (true);
grant select on public.app_commune_risques to authenticated;
grant select, insert, delete on public.app_commune_risques to service_role;
