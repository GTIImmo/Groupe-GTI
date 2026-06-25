-- =====================================================================
-- DVF v2 — fondation données : colonnes nettoyage + PostGIS (2026-06-25)
--
-- Lot 1 du chantier « amélioration estimation DVF ». Ajoute à `app_dvf_vente` :
--   - id_mutation / code_commune / nombre_lots : traçabilité + dédup en-bloc
--     (l'exclusion en-bloc elle-même est faite à l'ingestion : 1 logement bâti
--     par mutation, nombre_lots <= 2, prix/m² borné 300-8000).
--   - geom geography(Point,4326) GÉNÉRÉE depuis (lon, lat) + index GiST -> filtre
--     géographique réel par rayon GPS (ST_DWithin) au lieu du haversine manuel.
--     ATTENTION ordre : ST_MakePoint(lon, lat) (longitude d'abord).
--
-- Après cette migration : RE-INGÉRER (python backend/scripts/ingest_dvf.py) pour
-- peupler les nouvelles colonnes et purger l'en-bloc (~67k -> ~39k lignes propres).
-- =====================================================================

create extension if not exists postgis with schema extensions;

alter table public.app_dvf_vente
  add column if not exists id_mutation  text,
  add column if not exists code_commune text,
  add column if not exists nombre_lots  integer,
  add column if not exists geom extensions.geography(Point, 4326)
    generated always as (
      (extensions.st_setsrid(extensions.st_makepoint(lon, lat), 4326))::extensions.geography
    ) stored;

create index if not exists idx_dvf_geom     on public.app_dvf_vente using gist (geom);
create index if not exists idx_dvf_mutation on public.app_dvf_vente (id_mutation);
