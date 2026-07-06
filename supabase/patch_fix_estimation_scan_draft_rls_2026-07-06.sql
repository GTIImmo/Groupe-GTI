-- FIX : le brouillon d'estimation scanne (scan_draft) n'etait JAMAIS ecrit.
-- Cause : app_dossier_estimation a RLS activee avec une SEULE policy (SELECT
-- authenticated) ; aucune policy INSERT/UPDATE. Or la RPC d'ecriture etait en
-- LANGUAGE sql SANS security definer -> l'INSERT/UPDATE s'executait avec les droits
-- de l'utilisateur -> refuse par RLS -> 0 ligne ecrite -> editeur d'estimation vide.
--
-- Correctif : passer la RPC en SECURITY DEFINER (elle devient le point d'ecriture
-- controle ; la table reste verrouillee, aucune policy d'ecriture ouverte). Coherent
-- avec le modele actuel (lecture all-authenticated). search_path fige (hygiene definer).
-- Additif/idempotent (create or replace). Application GATED.

create or replace function public.app_upsert_dossier_estimation_scan_draft(
  p_app_dossier_id bigint,
  p_hektor_annonce_id bigint,
  p_scan_draft jsonb
)
returns void
language sql
security definer
set search_path = public, pg_temp
as $function$
  insert into public.app_dossier_estimation (app_dossier_id, hektor_annonce_id, scan_draft, updated_at)
  values (p_app_dossier_id, p_hektor_annonce_id, p_scan_draft, now())
  on conflict (app_dossier_id) do update
    set scan_draft = excluded.scan_draft,
        hektor_annonce_id = coalesce(excluded.hektor_annonce_id, public.app_dossier_estimation.hektor_annonce_id),
        updated_at = now();
$function$;

grant execute on function public.app_upsert_dossier_estimation_scan_draft(bigint, bigint, jsonb) to authenticated;
