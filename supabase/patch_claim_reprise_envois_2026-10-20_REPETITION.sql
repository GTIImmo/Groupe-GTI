-- ═══════════════════════════════════════════════════════════════════════════════
-- REPETITION de patch_claim_reprise_envois_2026-10-20.sql -- TOUT EST ANNULE A LA FIN
-- ═══════════════════════════════════════════════════════════════════════════════
-- A coller dans l'editeur SQL de Supabase. Rien ne reste : la derniere ligne est un
-- ROLLBACK. Le resultat se lit dans les messages (NOTICE) ; une EXCEPTION dit lequel
-- des controles a echoue.
--
-- Les travaux d'essai portent une priorite de -1000 (ils passent AVANT tout vrai travail
-- en attente) et AUCUN hektor_annonce_id (ils ne peuvent bloquer ni etre bloques par un
-- travail reel de la meme annonce).
--
-- QUATRE CONTROLES :
--   (1) une REPRISE (app_document_id, sans temp_storage_path) est RECLAMEE ;
--   (2) ⭐ TEMOIN INVERSE : un envoi IMMEDIAT sans fichier temporaire NE l'est PAS ;
--   (3) une reprise de PHOTO (app_photo_id) est reclamee ;
--   (4) un envoi immediat AVEC fichier temporaire reste reclamable (rien de perdu).
--
-- ⚠ Pour le controle (4) il faut un objet reel dans le coffre : on en pose un faux dans
--   storage.objects DANS la transaction (annule avec le reste).
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── 1. le patch, recopie TEL QUEL (genere depuis patch_claim_reprise_envois_2026-10-20.sql) ──

CREATE OR REPLACE FUNCTION public.app_console_claim_next_job(p_worker_id text DEFAULT NULL::text, p_worker_kind text DEFAULT 'actions'::text)
 RETURNS SETOF app_console_job
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare worker_kind text := lower(coalesce(nullif(p_worker_kind, ''), 'actions'));
        is_current_worker boolean := coalesce(p_worker_id, '') like '%:scheduled:v9' or coalesce(p_worker_id, '') like '%:service:v9';
begin
    update public.app_console_job j set status = 'error', finished_at = now(), updated_at = now(),
        error_message = coalesce(nullif(j.error_message, ''), 'Job interrompu automatiquement: execution running trop ancienne (> 30 minutes). Relancer la demande si necessaire.')
    where j.status = 'running' and coalesce(j.started_at, j.updated_at, j.requested_at, j.created_at) < now() - interval '30 minutes';
    return query
    with next_job as (
        select j.id from public.app_console_job j
        where j.status = 'pending' and is_current_worker
          and (worker_kind = 'all'
             or (worker_kind = 'actions' and j.job_type in (
                    'create_hektor_draft_annonce','update_hektor_annonce_fields','create_hektor_contact','update_hektor_contact',
                    'add_hektor_contact_search','update_hektor_contact_search','delete_hektor_contact_search',
                    'create_hektor_mandant_contact','update_hektor_mandant_contact','create_hektor_mandat_auto_number','link_hektor_mandant',
                    -- 03/10/2026 : le jumeau du rattachement. Sans cette ligne, le
                    -- travail n'est reclame par personne et reste « pending » a vie.
                    'unlink_hektor_mandant','archive_hektor_contact'))
             or (worker_kind = 'documents' and j.job_type in (
                    'sync_console_documents','prepare_document_cloud','generate_estimation_pdf','generate_mandat_document','generate_cadastre_document','relance_signature','cancel_signature_procedure','upload_document_to_hektor','delete_document_from_hektor',
                    'sync_hektor_photos','upload_hektor_photo','delete_hektor_photo','reorder_hektor_photos','set_hektor_photo_visibility','prepare_archived_annonce_detail','prepare_historical_annonce_detail'))
             or (worker_kind = 'admin' and j.job_type in (
                    'delete_hektor_annonce','delete_hektor_contact','archive_hektor_annonce','restore_hektor_annonce',
                    'change_hektor_annonce_status','assign_hektor_annonce_negotiator',
                    -- C.19 etape 4, 29/08 : les gestes d'etat sur les transactions.
                    -- 3.4, 07/09 : `delete_hektor_compromis` rejoint la liste. Il demande
                    -- la meme session admin que les autres -- mesure du 29/08 : le compte
                    -- negociateur est refuse sur le compromis.
                    'change_hektor_offre_status','cancel_hektor_compromis',
                    'delete_hektor_compromis','delete_hektor_vente'))
             or (worker_kind = 'matterport' and j.job_type in ('matterport_online','matterport_offline','matterport_archive','matterport_reactivate'))
             or (worker_kind = 'sync_light' and j.job_type in ('refresh_console_data','refresh_console_contact_data'))
             or (worker_kind = 'sync_full' and j.job_type in ('archive_cloud_documents'))
             or (worker_kind = 'sync' and j.job_type in ('refresh_console_data','refresh_console_contact_data','archive_cloud_documents')))
          and (j.job_type not in ('upload_document_to_hektor', 'upload_hektor_photo')
             or exists (select 1 from storage.objects o where o.bucket_id = 'hektor-console-documents' and o.name = j.payload_json->>'temp_storage_path')
             -- 20/10/2026 : une REPRISE d'envoi (Console/reprendre_envois_hektor.js) ne porte
             -- que app_document_id / app_photo_id, pas de temp_storage_path : le fichier est
             -- deja range chez nous (la ligne existe, avec son storage_path). Sans cette
             -- ligne, la reprise reste « pending » a vie, sans erreur.
             -- Sans risque pour la course que le garde ci-dessus protege : le front depose
             -- le fichier AVANT d'appeler la RPC qui pose app_document_id (api.ts,
             -- createUploadDocumentToHektorJob), donc cette cle prouve que le fichier est la.
             or nullif(coalesce(j.payload_json->>'app_document_id', j.payload_json->>'app_photo_id'), '') is not null)
          and (nullif(j.hektor_annonce_id, '') is null
             or not exists (select 1 from public.app_console_job running_job
                    where running_job.status = 'running' and running_job.hektor_annonce_id = j.hektor_annonce_id and running_job.id <> j.id))
          and (nullif(coalesce(j.payload_json->>'hektor_contact_id', j.payload_json->>'contact_id'), '') is null
             or not exists (select 1 from public.app_console_job running_contact_job
                    where running_contact_job.status = 'running' and running_contact_job.id <> j.id
                      and nullif(coalesce(running_contact_job.payload_json->>'hektor_contact_id', running_contact_job.payload_json->>'contact_id'), '') =
                          nullif(coalesce(j.payload_json->>'hektor_contact_id', j.payload_json->>'contact_id'), '')))
        order by j.priority asc, j.requested_at asc for update skip locked limit 1
    )
    update public.app_console_job j set status = 'running', started_at = now(), worker_id = p_worker_id, attempt_count = j.attempt_count + 1, updated_at = now()
    from next_job where j.id = next_job.id returning j.*;
end; $function$;


-- ── 2. les essais ───────────────────────────────────────────────────────────────
DO $essai$
declare
  v_id uuid;
  v_ok boolean;
  v_worker text := 'ESSAI:documents:service:v9';
begin
  -- (1) la reprise d'un document
  insert into public.app_console_job (job_type, payload_json, status, priority)
  values ('upload_document_to_hektor', '{"app_document_id":"00000000-0000-0000-0000-0000000000a1","repris_le":"2026-10-20"}'::jsonb, 'pending', -1000)
  returning id into v_id;
  select exists (select 1 from public.app_console_claim_next_job(v_worker, 'documents') c where c.id = v_id) into v_ok;
  if not v_ok then raise exception 'ECHEC (1) : la reprise d''un document n''est PAS reclamee'; end if;
  raise notice 'OK (1) la reprise d''un document est reclamee';

  -- (2) TEMOIN INVERSE : envoi immediat sans fichier temporaire
  insert into public.app_console_job (job_type, payload_json, status, priority)
  values ('upload_document_to_hektor', '{"temp_storage_path":"temp/uploads/essai/introuvable.pdf"}'::jsonb, 'pending', -999)
  returning id into v_id;
  select exists (select 1 from public.app_console_claim_next_job(v_worker, 'documents') c where c.id = v_id) into v_ok;
  if v_ok then raise exception 'ECHEC (2) : un envoi immediat SANS fichier temporaire a ete reclame (le garde a saute)'; end if;
  raise notice 'OK (2) TEMOIN INVERSE : un envoi immediat sans fichier temporaire n''est pas reclame';

  -- (3) la reprise d'une photo
  insert into public.app_console_job (job_type, payload_json, status, priority)
  values ('upload_hektor_photo', '{"app_photo_id":"00000000-0000-0000-0000-0000000000b1","repris_le":"2026-10-20"}'::jsonb, 'pending', -998)
  returning id into v_id;
  select exists (select 1 from public.app_console_claim_next_job(v_worker, 'documents') c where c.id = v_id) into v_ok;
  if not v_ok then raise exception 'ECHEC (3) : la reprise d''une photo n''est PAS reclamee'; end if;
  raise notice 'OK (3) la reprise d''une photo est reclamee';

  -- (4) un envoi immediat AVEC son fichier temporaire
  insert into storage.objects (bucket_id, name, owner_id)
  values ('hektor-console-documents', 'temp/uploads/essai/present.pdf', null);
  insert into public.app_console_job (job_type, payload_json, status, priority)
  values ('upload_document_to_hektor', '{"temp_storage_path":"temp/uploads/essai/present.pdf"}'::jsonb, 'pending', -997)
  returning id into v_id;
  select exists (select 1 from public.app_console_claim_next_job(v_worker, 'documents') c where c.id = v_id) into v_ok;
  if not v_ok then raise exception 'ECHEC (4) : un envoi immediat AVEC fichier temporaire n''est plus reclame (regression)'; end if;
  raise notice 'OK (4) un envoi immediat avec son fichier temporaire reste reclamable';

  raise notice 'TOUT EST VERT -- rien n''est conserve (ROLLBACK)';
end
$essai$;

ROLLBACK;
