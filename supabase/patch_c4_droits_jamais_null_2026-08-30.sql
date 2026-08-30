-- =====================================================================
-- LE CONTRÔLE DE DROITS NE REND PLUS JAMAIS `NULL`
-- Date : 2026-08-30
--
-- TROUVÉ EN ÉPROUVANT MA PROPRE RPC, pas en la relisant.
--
-- `app_archive_annonce_optimistic` est passée **sans aucun contrôle de droits**,
-- alors que sa jumelle `app_restore_annonce_optimistic` refusait. Mesure :
--
--     app_console_current_role()                       ->  NULL   (pas de session)
--     can_request_job('archive_hektor_annonce', …)      ->  NULL
--     can_request_job('restore_hektor_annonce', …)      ->  false
--
-- LA CAUSE. Pour DEUX types de travaux, la fonction rendait
-- `current_app_role = 'admin'` — qui vaut **NULL** quand le rôle est inconnu.
-- Et les douze appelants écrivent tous :
--
--     if not public.app_console_can_request_job(...) then raise exception ...
--
-- Or **`not NULL` vaut NULL** : la condition n'est pas prise, le garde-fou ne se
-- déclenche pas, et l'action passe.
--
-- C'est exactement le défaut traqué toute la nuit dans les workers — **conclure
-- du silence**. Ici, une absence de réponse valait autorisation.
--
-- ─────────────────────────────────────────────────────────────────────
-- CE QUI N'ÉTAIT PAS EXPLOITABLE, et il faut le dire aussi
--
-- Les **sept** fonctions ouvertes à `anon` utilisent des types de travaux qui
-- empruntent le `return false` final : elles étaient bien protégées. Les deux
-- seules qui pouvaient rendre NULL sont fermées à `anon` — vérifié par
-- `has_function_privilege`. Le défaut était donc **latent, pas ouvert**.
--
-- Mais il suffisait d'ajouter un type de travail à cette première liste, ou
-- d'ouvrir `anon` sur l'une de ces deux RPC, pour qu'il le devienne.
-- ─────────────────────────────────────────────────────────────────────
--
-- LE CORRECTIF EST À LA SOURCE, pas chez les douze appelants : une fonction de
-- droits doit rendre vrai ou faux, **jamais « je ne sais pas »**. Un rôle inconnu
-- n'est pas un administrateur.
--
-- VÉRIFIÉ APRÈS APPLICATION, sans session :
--     archiver false · statut false · désarchiver false · champs false
--
-- Appliqué en production via la migration `c4_droits_jamais_null`.
-- =====================================================================

create or replace function public.app_console_can_request_job(
  target_job_type text,
  target_app_dossier_id bigint,
  target_hektor_annonce_id text
)
returns boolean
language plpgsql
stable
security definer
set search_path to 'public'
as $function$
declare current_app_role text;
begin
    current_app_role := public.app_console_current_role();

    if target_job_type in ('archive_hektor_annonce', 'change_hektor_annonce_status') then
        -- coalesce : un role inconnu (NULL) n'est PAS un administrateur.
        return coalesce(current_app_role = 'admin', false);
    end if;

    if current_app_role in ('admin', 'manager') then
        return true;
    end if;

    if current_app_role = 'commercial'
       and target_job_type in (
            'prepare_document_cloud','upload_document_to_hektor','prepare_archived_annonce_detail','prepare_historical_annonce_detail',
            'sync_console_documents','relance_signature','cancel_signature_procedure'
       ) then
        return coalesce(public.app_console_can_access_dossier(target_app_dossier_id, target_hektor_annonce_id), false);
    end if;

    return false;
end;
$function$;
