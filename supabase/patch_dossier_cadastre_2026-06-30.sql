-- =====================================================================
-- Éléments cadastraux par dossier (IGN / Géoportail) — 2026-06-30.
--
-- Contrairement à la DVF/risques (par commune, pré-chargés en masse), le
-- cadastre est SPÉCIFIQUE À CHAQUE BIEN : la (les) parcelle(s) sous le point
-- géolocalisé du bien. On les récupère donc à la demande (IGN apicarto :
-- /cadastre/parcelle + /gpu/zone-urba) et on les persiste ici, par dossier,
-- au moment du bouton « Générer et enregistrer les éléments du cadastre »
-- (onglet Commercialisation). Le worker écrit cette table ; le front la relit
-- pour ré-afficher sans re-interroger l'IGN.
--
-- Aucune donnée nominative (le propriétaire cadastral n'est pas diffusé
-- publiquement par l'IGN). Le PDF « Plan cadastral » associé est déposé dans
-- Hektor via la chaîne upload_document_to_hektor existante.
-- =====================================================================

create table if not exists public.app_dossier_cadastre (
  app_dossier_id     bigint primary key,
  hektor_annonce_id  text,
  parcelles          jsonb,        -- [{reference, section, numero, contenance, commune, code_insee, idu}]
  contenance_totale  integer,      -- somme des contenances (m²)
  plu                jsonb,        -- {zone, libelle, type}
  hektor_document_id text,         -- doc « Plan cadastral » déposé (si rattaché ultérieurement)
  updated_at         timestamptz not null default now()
);

create index if not exists idx_dossier_cadastre_annonce on public.app_dossier_cadastre (hektor_annonce_id);

-- Données app non sensibles : lecture aux utilisateurs authentifiés ; écriture
-- par le service_role (worker console). Calqué sur app_commune_risques.
alter table public.app_dossier_cadastre enable row level security;
drop policy if exists app_dossier_cadastre_read on public.app_dossier_cadastre;
create policy app_dossier_cadastre_read on public.app_dossier_cadastre for select to authenticated using (true);
grant select on public.app_dossier_cadastre to authenticated;
grant select, insert, update, delete on public.app_dossier_cadastre to service_role;
