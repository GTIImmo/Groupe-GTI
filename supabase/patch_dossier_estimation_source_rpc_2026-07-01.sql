-- =====================================================================
-- RPC de mémorisation d'UNE source d'estimation — 2026-07-01.
--
-- Permet au FRONT (rôle authenticated) d'enregistrer une source calculée
-- directement depuis l'onglet Estimation (bouton « Générer et enregistrer »,
-- comme le cadastre) SANS passer par la modale/PDF. Fusionne une seule clé de
-- `sources` (dvf / cadre / cadastre / bdnb / dpe / rnb …) sans écraser les autres.
-- Le worker (génération PDF) appelle la MÊME RPC par source -> sémantique de
-- fusion unifiée (pas de perte quand on génère un bloc puis le PDF).
--
-- SECURITY DEFINER : la table n'accorde l'écriture qu'au service_role ; la RPC
-- fait le pont pour l'utilisateur authentifié (données non sensibles, publiques).
-- =====================================================================

create or replace function public.app_upsert_dossier_estimation_source(
  p_app_dossier_id   bigint,
  p_hektor_annonce_id text,
  p_key              text,
  p_ok               boolean,
  p_data             jsonb
) returns void
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_entry jsonb := jsonb_build_object('ok', coalesce(p_ok, false), 'data', p_data, 'fetched_at', now());
begin
  if p_app_dossier_id is null or p_key is null then
    return;
  end if;
  insert into public.app_dossier_estimation (app_dossier_id, hektor_annonce_id, sources, updated_at)
  values (p_app_dossier_id, p_hektor_annonce_id, jsonb_build_object(p_key, v_entry), now())
  on conflict (app_dossier_id) do update
    set sources = coalesce(public.app_dossier_estimation.sources, '{}'::jsonb)
                  || jsonb_build_object(p_key, v_entry),
        hektor_annonce_id = coalesce(excluded.hektor_annonce_id, public.app_dossier_estimation.hektor_annonce_id),
        updated_at = now();
end
$function$;

grant execute on function public.app_upsert_dossier_estimation_source(bigint, text, text, boolean, jsonb) to authenticated;
grant execute on function public.app_upsert_dossier_estimation_source(bigint, text, text, boolean, jsonb) to service_role;
