-- RÉPÉTITION de patch_suppression_document_signe_garde_2026-11-17.sql -- TOUT dans une transaction ANNULÉE à la fin.
-- À lancer APRÈS le patch. Aucun document n'est modifié ; les travaux insérés par l'essai disparaissent au ROLLBACK
-- (non validés, le worker ne les voit jamais).
-- Documents de l'essai : le mandat SIGNÉ Youtrust de 61398 (f0d73f5a…) et une photo ordinaire du bien de TEST 62965
-- (ab0f34be…). L'insertion est jouée en `authenticated`, identité de Frédéric (admin), comme le bouton de l'écran.
begin;

do $$
declare
  v_signe  uuid := 'f0d73f5a-b283-407d-a5f8-49496deb7027';
  v_libre  uuid := 'ab0f34be-11cc-4f1d-b92f-9cfdc5d3987d';
  v_refus  text;
  v_ok     int := 0;
begin
  -- [1] le garde et la règle sont posés
  if not exists (select 1 from pg_trigger where tgrelid = 'public.app_console_job'::regclass
                   and tgname = 'app_console_job_refus_suppression_signe_trg') then
    raise exception '[1] KO : le garde n''est pas pose';
  end if;
  v_ok := v_ok + 1;

  -- [2] la règle, cas par cas (signé, en cours, à la main -> engagé ; à envoyer, annulé, refusé, vide -> libre)
  if not (public.app_document_signature_engagee('{"signed_document":{"path":"x"}}')
      and public.app_document_signature_engagee('{"signature":{"status":"signed"}}')
      and public.app_document_signature_engagee('{"signature":{"status":"pending","procedure_id":3}}')
      and public.app_document_signature_engagee('{"signature":{"provider":"youtrust","status":"ongoing"}}')
      and public.app_document_signature_engagee('{"signature":{"provider":"youtrust","status":"approval"}}')
      and public.app_document_signature_engagee('{"signature":{"source":"manuscrite"}}')
      and not public.app_document_signature_engagee('{"signature":{"status":"to_send"}}')
      and not public.app_document_signature_engagee('{"signature":{"provider":"youtrust","status":"cancelled"}}')
      and not public.app_document_signature_engagee('{"signature":{"status":"refused","procedure_id":3}}')
      and not public.app_document_signature_engagee('{}')) then
    raise exception '[2] KO : la regle ne dit pas ce qui est attendu';
  end if;
  v_ok := v_ok + 1;

  -- [3] mise en scène VÉRIFIÉE : le document signé l'est bien, l'autre non (un zéro ne se croit pas sans témoin)
  if not public.app_document_signature_engagee((select metadata_json from public.app_console_document where id = v_signe)) then
    raise exception '[3] mise en scene : f0d73f5a n''est plus signe -- choisir un autre document signe';
  end if;
  if public.app_document_signature_engagee((select coalesce(metadata_json, '{}') from public.app_console_document where id = v_libre)) then
    raise exception '[3] mise en scene : ab0f34be est engage -- choisir un autre document libre';
  end if;
  v_ok := v_ok + 1;

  -- [4] le bouton sur un document SIGNÉ -> refusé
  perform set_config('request.jwt.claims', '{"sub":"d4b1685f-948b-4ce8-af15-671b94a725e6","role":"authenticated","email":"frederic.gerphagnon@gti-immobilier.fr"}', true);
  execute 'set local role authenticated';
  begin
    insert into public.app_console_job (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
    values ('delete_document_from_hektor', 1387336, '61398',
            jsonb_build_object('document_id', v_signe, 'document_name', 'Mandat de vente - 18420.pdf'), 15,
            'd4b1685f-948b-4ce8-af15-671b94a725e6');
    v_refus := 'ACCEPTE';
  exception when others then
    get stacked diagnostics v_refus = message_text;
  end;
  execute 'reset role';
  if v_refus not ilike 'document_signe_non_supprimable%' then raise exception '[4] KO : %', v_refus; end if;
  v_ok := v_ok + 1;

  -- [5] le bouton sur un document ORDINAIRE -> accepté, comme avant (inséré puis effacé par le ROLLBACK)
  execute 'set local role authenticated';
  insert into public.app_console_job (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  values ('delete_document_from_hektor', 5941336, '62965',
          jsonb_build_object('document_id', v_libre, 'document_name', 'essai'), 15,
          'd4b1685f-948b-4ce8-af15-671b94a725e6');
  execute 'reset role';
  v_ok := v_ok + 1;

  -- [6] TÉMOIN INVERSE : garde coupé (dans cette transaction seulement), le document SIGNÉ passait -- c'est bien le garde
  --     qui refuse, pas une autre règle.
  execute 'alter table public.app_console_job disable trigger app_console_job_refus_suppression_signe_trg';
  execute 'set local role authenticated';
  insert into public.app_console_job (job_type, app_dossier_id, hektor_annonce_id, payload_json, priority, requested_by)
  values ('delete_document_from_hektor', 1387336, '61398',
          jsonb_build_object('document_id', v_signe, 'document_name', 'essai temoin'), 15,
          'd4b1685f-948b-4ce8-af15-671b94a725e6');
  execute 'reset role';
  execute 'alter table public.app_console_job enable trigger app_console_job_refus_suppression_signe_trg';
  v_ok := v_ok + 1;

  -- [7] un autre type de travail n'est jamais touché par le garde
  if (select count(*) from pg_trigger t where t.tgname = 'app_console_job_refus_suppression_signe_trg'
        and pg_get_triggerdef(t.oid) ilike '%delete_document_from_hektor%') <> 1 then
    raise exception '[7] KO : le garde ne se limite pas aux suppressions de document';
  end if;
  v_ok := v_ok + 1;

  raise notice 'REPETITION OK : % controles verts sur 7 (tout est annule par le ROLLBACK)', v_ok;
end $$;

rollback;
