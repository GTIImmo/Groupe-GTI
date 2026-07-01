-- =====================================================================
-- Potentiel locatif par commune — 2026-07-01 (patron « bulk / pré-téléchargé »,
-- comme app_dvf_vente / app_commune_risques).
--
-- Données par COMMUNE (INSEE), stables (~1×/an), donc pré-chargées en masse par
-- backend/scripts/ingest_loyers.py (télécharge les CSV data.gouv, DELETE+COPY),
-- pas d'appel API par bien. Le front lit par INSEE (résolu depuis lat/lon via
-- geo.api.gouv) pour estimer le loyer + le rendement + la zone fiscale.
--
-- Sources : ANIL/DHUP « Carte des loyers » (loyer €/m²/mois charges comprises,
-- maison & appartement) + « Liste des communes selon le zonage ABC » (data.gouv).
-- =====================================================================

create table if not exists public.app_commune_loyers (
  insee         text primary key,
  libgeo        text,
  dep           text,
  loyer_maison  numeric,     -- €/m²/mois (charges comprises), indicateur d'annonce
  loyer_appart  numeric,     -- €/m²/mois
  zone_abc      text,        -- Abis / A / B1 / B2 / C (tension marché → Pinel/Loc'Avantages)
  millesime     integer,     -- année du millésime loyers
  updated_at    timestamptz not null default now()
);

alter table public.app_commune_loyers enable row level security;
drop policy if exists app_commune_loyers_read on public.app_commune_loyers;
create policy app_commune_loyers_read on public.app_commune_loyers for select to authenticated using (true);
grant select on public.app_commune_loyers to authenticated;
grant select, insert, update, delete on public.app_commune_loyers to service_role;
