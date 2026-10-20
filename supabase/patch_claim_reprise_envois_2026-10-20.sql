-- ═══════════════════════════════════════════════════════════════════════════════
-- app_console_claim_next_job : les REPRISES d'envoi doivent pouvoir etre reclamees
-- ═══════════════════════════════════════════════════════════════════════════════
-- TROUVE LE 20/10/2026, en cherchant pourquoi un travail « Document envoye au PC
-- serveur » restait en attente depuis 1 h 13.
--
-- Le script de reprise (Console/reprendre_envois_hektor.js, tache « GTI Reprise Envois
-- Hektor », 12:30) pose des travaux `upload_document_to_hektor` / `upload_hektor_photo`
-- dont la charge est {app_document_id | app_photo_id, repris_le}. Or cette fonction
-- n'accorde un travail d'envoi que si `payload_json->>'temp_storage_path'` designe un
-- objet EXISTANT dans le coffre. Une reprise n'en porte pas : elle n'etait reclamee par
-- PERSONNE. Statut « pending », worker_id null, 0 tentative, aucune erreur -- le defaut
-- muet que le chantier ④ a passe dix points a supprimer.
--
-- Il ne s'etait jamais vu : la reprise n'avait jamais rien eu a reprendre avant le
-- 19/10 (premier vrai envoi par le chemin differe, AVENANTS 87K, annonce 59578).
--
-- CE QUI CHANGE : UNE SEULE CLAUSE, dans le garde des envois. Un travail qui porte
-- `app_document_id` ou `app_photo_id` est reclamable sans fichier temporaire. Le
-- worker lit alors la ligne et son storage_path (completerEnvoiDocumentDiffere).
--
-- CE QUE CELA NE CHANGE PAS :
--   · un envoi IMMEDIAT (sans app_document_id) exige toujours son fichier temporaire ;
--   · les quatre files, leurs listes de types, le verrou par annonce et par contact,
--     l'ordre de priorite : identiques au caractere pres (voir l'empreinte ci-dessous).
--
-- ⚠ ORDRE DE DEPLOIEMENT : le correctif du worker et du script de reprise (statut qui
--   ne ment plus, refus de renvoyer une ligne qui a deja son numero Hektor) DOIT etre
--   en place AVANT ce patch. Sinon une reprise rendue reclamable renverrait a Hektor un
--   document qu'il a deja -- un doublon.
--
-- AVANT / APRES (relever avec : select md5(prosrc), octet_length(prosrc) from pg_proc
--   where proname='app_console_claim_next_job' and pronamespace='public'::regnamespace) :
--   avant : md5 9091986503169283a770059028174f3e · 4682 octets
--
-- RETOUR ARRIERE : patch_claim_reprise_envois_2026-10-20_INVERSE.sql (la definition
-- d'avant, relevee en production). Les reprises cessent alors d'etre reclamees.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

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

COMMIT;
