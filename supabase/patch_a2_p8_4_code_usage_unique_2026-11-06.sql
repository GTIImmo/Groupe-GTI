-- A.2 P8-4 (06/11/2026) -- LE CODE À USAGE UNIQUE NE RESTE PAS EN BASE, ET L'ÉCRAN NE LIT PLUS LA COLONNE DES PREUVES
-- ---------------------------------------------------------------------------------------------------------
-- Audit P8 du 06/11 : la piste JSON de Youtrust, rangée dans `app_signature_request.proofs`, porte le code reçu par le
-- signataire (`authentication.code`). La règle `app_signature_request_select_scope` donne la LIGNE ENTIÈRE à tout
-- utilisateur qui a le bien dans son portefeuille : le code est lisible par l'API (pas par l'écran, qui ne lit pas
-- cette colonne). Il est déjà consommé, mais il ne PROUVE rien : la preuve est `validated_at` + `mode`, qui restent.
--
-- Deux protections, indépendantes :
--   A. la ligne existante (la seule demande, l'essai de 61398) : `code` -> « masqué », APRÈS une sauvegarde datée
--      (table fermée à l'API : RLS active, aucun droit pour anon / authenticated) ;
--   B. `authenticated` perd le droit de lire la colonne `proofs` (il garde toutes les autres). Mesuré le 06/11 : aucune
--      vue ni fonction ne lit la table ; l'écran lit des colonnes nommées (lib/api.ts, loadDemandeSignature) ; le
--      webhook et le worker passent par la clé de service. La règle de app_signature_event lit provider_request_id
--      (gardé).
-- Le worker est corrigé à part (masquerCodesUsageUnique, console_job_worker.js) : les prochaines demandes n'écriront
-- plus le code. Retour arrière : patch_a2_p8_4_code_usage_unique_2026-11-06_INVERSE.sql.

do $$
begin
  if to_regclass('public.app_signature_request_avant_masquage_otp_20261106') is not null then
    raise exception 'DEJA POSE : la sauvegarde existe deja -- rien a faire.';
  end if;
  if not has_column_privilege('authenticated', 'public.app_signature_request', 'proofs', 'SELECT') then
    raise exception 'VERSION INATTENDUE : authenticated ne lit deja plus proofs.';
  end if;
end $$;

-- A. sauvegarde datée, fermée à l'API
create table public.app_signature_request_avant_masquage_otp_20261106 as
  select id, proofs, now() as sauvegarde_le from public.app_signature_request where proofs is not null;
alter table public.app_signature_request_avant_masquage_otp_20261106 enable row level security;
revoke all on public.app_signature_request_avant_masquage_otp_20261106 from public, anon, authenticated;

create function pg_temp.masquer_codes(j jsonb, sous_auth boolean default false) returns jsonb language plpgsql immutable as $$
declare r jsonb; k text; v jsonb;
begin
  if jsonb_typeof(j) = 'object' then
    r := '{}'::jsonb;
    for k, v in select * from jsonb_each(j) loop
      if sous_auth and k = 'code' and jsonb_typeof(v) in ('string', 'number') then r := r || jsonb_build_object(k, 'masqué');
      else r := r || jsonb_build_object(k, pg_temp.masquer_codes(v, k = 'authentication'));
      end if;
    end loop;
    return r;
  elsif jsonb_typeof(j) = 'array' then
    return coalesce((select jsonb_agg(pg_temp.masquer_codes(e, sous_auth) order by n) from jsonb_array_elements(j) with ordinality t(e, n)), '[]'::jsonb);
  end if;
  return j;
end $$;

update public.app_signature_request
   set proofs = pg_temp.masquer_codes(proofs), updated_at = now()
 where proofs is not null and jsonb_path_exists(proofs, 'strict $[*].audit.**.authentication.code ? (@ != "masqué")');

-- B. la colonne des preuves n'est plus lisible par l'API (toutes les autres le restent)
revoke select on public.app_signature_request from authenticated;
grant select (id, provider, provider_request_id, sandbox, app_console_document_id, app_dossier_id, hektor_annonce_id,
              document_kind, status, signers, external_id, expiration_at, activated_at, done_at, canceled_at, expired_at,
              signed_storage_path, last_event_at, last_synced_at, erreur, requested_by, created_at, updated_at)
  on public.app_signature_request to authenticated;

do $$
begin
  if exists (select 1 from public.app_signature_request where jsonb_path_exists(proofs, 'strict $[*].audit.**.authentication.code ? (@ != "masqué")')) then
    raise exception 'POSE RATEE : un code est encore en clair.';
  end if;
  if has_column_privilege('authenticated', 'public.app_signature_request', 'proofs', 'SELECT') then
    raise exception 'POSE RATEE : authenticated lit encore proofs.';
  end if;
  if not has_column_privilege('authenticated', 'public.app_signature_request', 'signers', 'SELECT') then
    raise exception 'POSE RATEE : authenticated ne lit plus signers (le suivi P8-3 tomberait).';
  end if;
end $$;
