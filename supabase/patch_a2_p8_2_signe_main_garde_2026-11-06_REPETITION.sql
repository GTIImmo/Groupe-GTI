-- RÉPÉTITION de patch_a2_p8_2_signe_main_garde_2026-11-06.sql -- TOUT dans une transaction ANNULÉE à la fin.
-- À lancer APRÈS le patch. Le document d'essai est le mandat Youtrust de 61398 (f0d73f5a…), dont l'état est modifié
-- PUIS remis par le ROLLBACK : rien ne reste.
-- ⚠ 06/11, 1er passage : la MISE EN SCÈNE jouée en `authenticated` n'écrivait RIEN (RLS active, aucune règle UPDATE
--   sur app_console_document) -> la fonction voyait « signé » et le contrôle [2] mentait. Désormais : la mise en scène
--   en propriétaire, l'APPEL seul en `authenticated` (identité de Frédéric, pour passer la garde d'accès), et chaque
--   mise en scène est VÉRIFIÉE avant l'appel (un zéro ne se croit pas sans témoin positif).
begin;
create temp table _rep_p8_2 (n int) on commit drop;
grant all on _rep_p8_2 to authenticated;

do $$
declare
  v_doc uuid := 'f0d73f5a-b283-407d-a5f8-49496deb7027';
  v_refus text;
  v_ok int := 0;
begin
  -- [1] la garde est dans la fonction
  if pg_get_functiondef('public.app_console_mark_document_signed_manual(uuid,date)'::regprocedure) not ilike '%signature_en_cours%' then
    raise exception '[1] KO : la garde n''est pas posee';
  end if;
  v_ok := v_ok + 1;

  -- [2] Youtrust EN COURS -> refus, avec le message pour l'ecran
  update public.app_console_document set metadata_json = jsonb_set(metadata_json, '{signature}', '{"provider":"youtrust","status":"pending","progress":"1/3"}'::jsonb) where id = v_doc;
  if (select metadata_json -> 'signature' ->> 'status' from public.app_console_document where id = v_doc) <> 'pending' then
    raise exception '[2] mise en scene ratee';
  end if;
  perform set_config('request.jwt.claims', '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6","role":"authenticated","email":"frederic.gerphagnon@gti-immobilier.fr"}', true);
  execute 'set local role authenticated';
  begin
    perform public.app_console_mark_document_signed_manual(v_doc, null);
    v_refus := 'ACCEPTE';
  exception when others then
    get stacked diagnostics v_refus = message_text;
  end;
  execute 'reset role';
  if v_refus not ilike '%annulez-la d''abord%' then raise exception '[2] KO : %', v_refus; end if;
  v_ok := v_ok + 1;

  -- [3] ImmoSign en attente (procedure) -> refus
  update public.app_console_document set metadata_json = jsonb_set(metadata_json, '{signature}', '{"status":"pending","procedure_id":999,"progress":"1/2"}'::jsonb) where id = v_doc;
  if (select metadata_json -> 'signature' ->> 'procedure_id' from public.app_console_document where id = v_doc) <> '999' then
    raise exception '[3] mise en scene ratee';
  end if;
  execute 'set local role authenticated';
  begin
    perform public.app_console_mark_document_signed_manual(v_doc, null);
    v_refus := 'ACCEPTE';
  exception when others then
    get stacked diagnostics v_refus = message_text;
  end;
  execute 'reset role';
  if v_refus not ilike '%annulez-la d''abord%' then raise exception '[3] KO : %', v_refus; end if;
  v_ok := v_ok + 1;

  -- [4] TEMOIN : « a envoyer » sans procedure (etat par defaut) -> ACCEPTE, comme avant
  update public.app_console_document set metadata_json = jsonb_set(metadata_json, '{signature}', '{"status":"to_send","procedure_id":null}'::jsonb) where id = v_doc;
  execute 'set local role authenticated';
  perform public.app_console_mark_document_signed_manual(v_doc, '2026-11-06');
  execute 'reset role';
  if (select (metadata_json -> 'signature' ->> 'source') || '/' || (metadata_json -> 'signature' ->> 'signed_at') from public.app_console_document where id = v_doc) is distinct from 'manuscrite/2026-11-06' then
    raise exception '[4] KO : le cas normal ne marque plus';
  end if;
  v_ok := v_ok + 1;

  -- [5] TEMOIN : ImmoSign ANNULE (procedure videe) -> accepte
  update public.app_console_document set metadata_json = jsonb_set(metadata_json, '{signature}', '{"status":"cancelled","procedure_id":null}'::jsonb) where id = v_doc;
  execute 'set local role authenticated';
  perform public.app_console_mark_document_signed_manual(v_doc, null);
  execute 'reset role';
  if (select metadata_json -> 'signature' ->> 'status' from public.app_console_document where id = v_doc) <> 'signed' then
    raise exception '[5] KO : un ImmoSign annule ne se marque plus';
  end if;
  v_ok := v_ok + 1;

  insert into _rep_p8_2 values (v_ok);
end $$;

select n as controles_verts_sur_5 from _rep_p8_2;
rollback;

-- [6] apres l'annulation, le document d'essai est INTACT (Youtrust signe 3/3, aucune trace manuscrite)
select metadata_json -> 'signature' ->> 'status' as statut_apres, metadata_json -> 'signature' ->> 'provider' as fournisseur,
       metadata_json -> 'signature' ->> 'source' as source_doit_etre_vide, updated_at
  from public.app_console_document where id = 'f0d73f5a-b283-407d-a5f8-49496deb7027';
