-- RÉPÉTITION de patch_a2_p8_4_code_usage_unique_2026-11-06.sql -- à lancer APRÈS le patch, dans une transaction ANNULÉE.
-- Elle n'écrit rien : elle lit sous l'identité de Frédéric (rôle pris SEULEMENT autour de chaque lecture).
begin;
create temp table _rep_otp (controle text, ok boolean, detail text) on commit drop;
grant all on _rep_otp to authenticated;

do $$
declare
  v_fred text := '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6","role":"authenticated","email":"frederic.gerphagnon@gti-immobilier.fr"}';
  v_n int; v_err text; v_sig jsonb;
begin
  -- [1] plus aucun code en clair, et la preuve (heure + mode) est restée
  insert into _rep_otp select '1 aucun code en clair',
    not exists (select 1 from public.app_signature_request where jsonb_path_exists(proofs, 'strict $[*].audit.**.authentication.code ? (@ != "masqué")')), null;
  insert into _rep_otp select '1 heure de validation et mode gardes',
    (select bool_and(jsonb_path_exists(proofs, 'strict $[*].audit.**.authentication.validated_at') and jsonb_path_exists(proofs, 'strict $[*].audit.**.authentication.mode'))
       from public.app_signature_request where proofs is not null), null;
  -- [2] la sauvegarde existe et est FERMÉE à l'API
  insert into _rep_otp select '2 sauvegarde datee presente et fermee',
    to_regclass('public.app_signature_request_avant_masquage_otp_20261106') is not null
    and not has_table_privilege('authenticated', 'public.app_signature_request_avant_masquage_otp_20261106', 'SELECT')
    and not has_table_privilege('anon', 'public.app_signature_request_avant_masquage_otp_20261106', 'SELECT'), null;

  perform set_config('request.jwt.claims', v_fred, true);
  -- [3] Frédéric ne lit plus `proofs` par l'API
  execute 'set local role authenticated';
  begin
    perform proofs from public.app_signature_request limit 1;
    v_err := 'LU';
  exception when others then v_err := sqlstate || ' ' || sqlerrm;
  end;
  execute 'reset role';
  insert into _rep_otp values ('3 proofs refuse a authenticated', v_err like '42501%', v_err);

  -- [4] TÉMOIN : le suivi P8-3 lit toujours ses colonnes (la même liste que lib/api.ts loadDemandeSignature)
  execute 'set local role authenticated';
  select count(*), max(signers::text)::jsonb into v_n, v_sig
    from (select id, status, signers, expiration_at, done_at, canceled_at, expired_at, last_synced_at from public.app_signature_request) x;
  execute 'reset role';
  insert into _rep_otp values ('4 TEMOIN : le suivi lit id/status/signers/dates', v_n >= 1 and jsonb_array_length(v_sig) = 3, v_n || ' demande(s)');

  -- [5] TÉMOIN : la règle des avis (qui lit provider_request_id de la table) marche encore
  execute 'set local role authenticated';
  begin
    select count(*) into v_n from public.app_signature_event;
    v_err := 'ok';
  exception when others then v_err := sqlstate || ' ' || sqlerrm;
  end;
  execute 'reset role';
  insert into _rep_otp values ('5 TEMOIN : app_signature_event lisible', v_err = 'ok', v_err || ' / ' || coalesce(v_n, 0) || ' avis');
end $$;

select controle, ok, detail from _rep_otp order by controle;
rollback;
