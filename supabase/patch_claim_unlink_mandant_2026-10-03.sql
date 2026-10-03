-- ═══════════════════════════════════════════════════════════════════════════════
-- app_console_claim_next_job : la file « actions » doit reclamer unlink_hektor_mandant
-- ═══════════════════════════════════════════════════════════════════════════════
-- TROUVE PAR LE PREMIER ESSAI REEL, le 03/10/2026 a 16:43.
--
-- Le geste « retirer un mandant » etait complet PARTOUT ailleurs : la RPC qui pose
-- le travail, le case du repartiteur, l'implementation, le chemin de retour, le
-- bouton. Mais le type n'etait reclame par AUCUNE file -- ni cote JS, ni ICI.
-- Resultat mesure : le travail reste « pending » POUR TOUJOURS,
--     worker_id = null, attempt_count = 0, error_message = null.
-- Aucune erreur. Aucune alerte. Rien.
--
-- ⚠⚠ ET C'EST LA DIVERGENCE MUETTE QUE TOUT LE CHANTIER CHERCHE A EVITER :
--   la RPC avait DEJA date le retrait (retire_le + retire_par) et la vue cachait
--   deja le lien. L'ecran disait « retire », et Hektor ne l'apprenait JAMAIS.
--
-- ⭐ LE CODE AVAIT PREVENU, MOT POUR MOT. Commentaire de ADMIN_JOB_TYPES dans
--   console_job_worker.js : « Oublier cette liste = un travail qui reste en attente
--   indefiniment, SANS erreur : aucun service ne le reclame. » Et le worker leve
--   justement « Appliquer la migration app_console_claim_next_job » quand les deux
--   cartes divergent -- il y a DEUX cartes, une en JS et une ICI, et il faut les
--   deux. La JS est corrigee par le commit qui accompagne ce patch.
--
-- CE QUI CHANGE : une seule chaine ajoutee a la liste 'actions'.
-- Sa place est collee a son jumeau link_hektor_mandant : meme session negociateur,
-- meme objet, meme famille de geste.
--
-- RETOUR ARRIERE : rejouer ce fichier en retirant 'unlink_hektor_mandant' de la
-- liste. Le travail en attente cesserait simplement d'etre reclame.
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
                    'unlink_hektor_mandant'))
             or (worker_kind = 'documents' and j.job_type in (
                    'sync_console_documents','prepare_document_cloud','generate_estimation_pdf','generate_mandat_document','generate_cadastre_document','relance_signature','cancel_signature_procedure','upload_document_to_hektor','delete_document_from_hektor',
                    'sync_hektor_photos','upload_hektor_photo','prepare_archived_annonce_detail','prepare_historical_annonce_detail'))
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
             or exists (select 1 from storage.objects o where o.bucket_id = 'hektor-console-documents' and o.name = j.payload_json->>'temp_storage_path'))
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

-- ─── LE GARDE-FOU : on verifie ce qu'on vient de poser, on ne le suppose pas ───
DO $$
DECLARE src text;
BEGIN
    SELECT pg_get_functiondef(p.oid) INTO src
      FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = 'public' AND p.proname = 'app_console_claim_next_job';

    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : la fonction app_console_claim_next_job est introuvable.';
    END IF;
    IF position('''unlink_hektor_mandant''' in src) = 0 THEN
        RAISE EXCEPTION 'ARRET : unlink_hektor_mandant n''est PAS dans la fonction.';
    END IF;
    -- son jumeau doit toujours y etre : si on l'a perdu, on a ecrase autre chose
    IF position('''link_hektor_mandant''' in src) = 0 THEN
        RAISE EXCEPTION 'ARRET : link_hektor_mandant a DISPARU -- la fonction a ete abimee.';
    END IF;
    -- et les autres familles aussi, meme raison
    IF position('''delete_hektor_vente''' in src) = 0
       OR position('''sync_console_documents''' in src) = 0
       OR position('''refresh_console_data''' in src) = 0 THEN
        RAISE EXCEPTION 'ARRET : une autre file a ete abimee par ce patch.';
    END IF;

    RAISE NOTICE 'OK : la file actions reclame desormais unlink_hektor_mandant, et les autres files sont intactes.';
END $$;

COMMIT;
