-- RETOUR ARRIÈRE de patch_a2_p8_4_code_usage_unique_2026-11-06.sql : le droit de table d'avant, et les preuves remises
-- depuis la sauvegarde datée. Ne juge que SA part : il ne touche qu'à cette table, ses droits et sa sauvegarde.

do $$
begin
  if to_regclass('public.app_signature_request_avant_masquage_otp_20261106') is null then
    raise exception 'SAUVEGARDE ABSENTE : rien a remettre.';
  end if;
end $$;

revoke select (id, provider, provider_request_id, sandbox, app_console_document_id, app_dossier_id, hektor_annonce_id,
               document_kind, status, signers, external_id, expiration_at, activated_at, done_at, canceled_at, expired_at,
               signed_storage_path, last_event_at, last_synced_at, erreur, requested_by, created_at, updated_at)
  on public.app_signature_request from authenticated;
grant select on public.app_signature_request to authenticated;

update public.app_signature_request r
   set proofs = s.proofs, updated_at = now()
  from public.app_signature_request_avant_masquage_otp_20261106 s
 where s.id = r.id;

do $$
begin
  if not has_column_privilege('authenticated', 'public.app_signature_request', 'proofs', 'SELECT') then
    raise exception 'RETOUR ARRIERE RATE : authenticated ne lit toujours pas proofs.';
  end if;
end $$;
-- La sauvegarde est GARDÉE (un retour arrière ne détruit pas sa source) ; la retirer à la main une fois vérifié :
--   drop table public.app_signature_request_avant_masquage_otp_20261106;
