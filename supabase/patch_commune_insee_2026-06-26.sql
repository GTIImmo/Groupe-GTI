-- =====================================================================
-- Profil commune (INSEE) — pré-chargé, actualisation annuelle
-- 2026-06-26.
--
-- Même modèle que DVF / risques : données INSEE par commune, annuelles -> pré-chargées
-- (script ingest_insee.py, regroupé à la tâche DVF + risques), lues à la génération.
-- Source : API INSEE Melodi (open data, sans clé) :
--   DS_POPULATIONS_HISTORIQUES (population + évolution) · DS_FILOSOFI_CC (revenu médian, MED_SL).
-- Colonnes v2 (proprietaires/maisons/csp/chômage) prévues nullable pour enrichissement.
-- =====================================================================

create table if not exists public.app_commune_insee (
  code_insee       text primary key,
  commune          text,
  dept             text,
  population       integer,        -- population municipale (dernier millésime)
  population_annee integer,
  pop_evolution    numeric,        -- évolution % sur ~15 ans
  pop_tendance     text,           -- Croissance | Stable | Déclin
  revenu_median    integer,        -- niveau de vie médian €/an (FiLoSoFi MED_SL)
  -- v2 (nullable, à enrichir) :
  part_proprietaires numeric,
  part_maisons       numeric,
  taux_chomage       numeric,
  csp_dominante      text,
  age_median         numeric,
  updated_at       timestamptz not null default now()
);

create index if not exists idx_commune_insee_dept on public.app_commune_insee (dept);

alter table public.app_commune_insee enable row level security;
drop policy if exists app_commune_insee_read on public.app_commune_insee;
create policy app_commune_insee_read on public.app_commune_insee for select to authenticated using (true);
grant select on public.app_commune_insee to authenticated;
grant select, insert, delete on public.app_commune_insee to service_role;
