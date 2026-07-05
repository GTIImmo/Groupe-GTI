-- ============================================================================
-- patch_dossier_estimation_scan_draft_2026-07-05.sql
--
-- Agent de saisie (estimation par photo) : persiste le BROUILLON D'ESTIMATION
-- scanne (valeurs, etat, bareme, points, argumentaire, avis, charges) pour que
-- l'editeur d'avis de valeur (EstimationDocumentEditor) le charge en initialDraft
-- au lieu de repartir de zero. Le scan a lieu au CREATE (id annonce pas encore
-- connu) ; le front ecrit scan_draft une fois l'app_dossier_id resolu.
--
-- ADDITIF : une colonne jsonb + un RPC d'upsert, sur le meme patron que
-- valeurs/sources. N'altere rien d'existant.
-- ============================================================================

alter table public.app_dossier_estimation
  add column if not exists scan_draft jsonb;

-- Upsert du brouillon scanne pour un dossier (cree la ligne si absente).
create or replace function public.app_upsert_dossier_estimation_scan_draft(
  p_app_dossier_id bigint,
  p_hektor_annonce_id bigint,
  p_scan_draft jsonb
) returns void
language sql
security invoker
as $$
  insert into public.app_dossier_estimation (app_dossier_id, hektor_annonce_id, scan_draft, updated_at)
  values (p_app_dossier_id, p_hektor_annonce_id, p_scan_draft, now())
  on conflict (app_dossier_id) do update
    set scan_draft = excluded.scan_draft,
        hektor_annonce_id = coalesce(excluded.hektor_annonce_id, public.app_dossier_estimation.hektor_annonce_id),
        updated_at = now();
$$;
