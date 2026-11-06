-- A.2 P8-4 (06/11/2026) -- OUVRIR LES PREUVES ET L'ORIGINAL D'UN DOCUMENT SIGNÉ DEPUIS L'ÉCRAN
-- ---------------------------------------------------------------------------------------------------------
-- Audit P8 du 06/11 : la règle de lecture du coffre (`hektor_console_documents_read_scope`) n'ouvre qu'un objet dont le
-- chemin est ÉGAL à `storage_path` d'un document `cloud_available`. Or un document signé range À CÔTÉ de son fichier :
--   . Youtrust : `proofs/preuves-<n>-<role>.pdf` (une preuve par signataire) + l'ORIGINAL non signé ;
--   . ImmoSign : `immosign/preuves-<p>.zip` et `immosign/procedure-<p>.zip` + l'ORIGINAL non signé.
-- Mesuré le 06/11 : 24 856 chemins sur 24 856 ont la forme `annonces/<n° annonce>/documents/<id du document>/…` ; dans
-- ces dossiers il n'y a QUE : le fichier du document (24 856), immosign/ (848), l'original d'un signé (390, un par
-- document, nom = celui de sa copie serveur), proofs/ (3). Rien d'autre.
--
-- Ce qui change : la règle gagne UNE branche (OU) -- un objet rangé dans le dossier d'un document que l'utilisateur a
-- DÉJÀ le droit de lire (même document `cloud_available`, même garde `app_console_can_access_dossier`). Rien n'est
-- retiré ; aucune écriture n'est touchée ; le worker et le webhook passent par la clé de service (hors règle).
-- La branche passe par une fonction pour garder l'accès par CLÉ PRIMAIRE (id du document lu dans le chemin, vérifié
-- comme uuid AVANT la conversion -- un chemin mal formé rend faux, jamais une erreur).
-- Retour arrière : patch_a2_p8_4_preuves_coffre_2026-11-06_INVERSE.sql.

do $$
declare v_qual text;
begin
  select qual into v_qual from pg_policies where schemaname = 'storage' and tablename = 'objects' and policyname = 'hektor_console_documents_read_scope';
  if v_qual is null then raise exception 'REGLE ABSENTE : hektor_console_documents_read_scope introuvable.'; end if;
  if v_qual ilike '%app_console_dossier_document_lisible%' then raise exception 'DEJA POSE : la branche est deja dans la regle.'; end if;
  -- On ne remplace QUE la règle connue (le fichier du document + temp/uploads de ses propres travaux).
  if replace(v_qual, chr(13), '') not ilike '%d.storage_path = objects.name%' or v_qual not ilike '%''uploads''::text%' then
    raise exception 'VERSION INATTENDUE de la regle : on ne remplace pas a l''aveugle.';
  end if;
end $$;

create or replace function public.app_console_dossier_document_lisible(p_name text)
returns boolean
language plpgsql
stable
security definer
set search_path = public
as $$
declare
  f text[];
begin
  f := storage.foldername(p_name);
  if coalesce(array_length(f, 1), 0) < 4 or f[1] <> 'annonces' or f[3] <> 'documents'
     or f[4] !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then
    return false;
  end if;
  return exists (
    select 1
      from public.app_console_document d
     where d.id = f[4]::uuid
       and d.hektor_annonce_id = f[2]
       and d.storage_bucket = 'hektor-console-documents'
       and d.storage_status = 'cloud_available'
       and public.app_console_can_access_dossier(d.app_dossier_id, d.hektor_annonce_id)
  );
end;
$$;

-- ⛔ `revoke from public` ne ferme pas `authenticated` (droit par défaut) : on ferme public ET anon, on ouvre authenticated.
revoke all on function public.app_console_dossier_document_lisible(text) from public, anon;
grant execute on function public.app_console_dossier_document_lisible(text) to authenticated;

alter policy hektor_console_documents_read_scope on storage.objects
using (
  (bucket_id = 'hektor-console-documents'::text)
  AND (
    (EXISTS ( SELECT 1
       FROM app_console_document d
      WHERE ((d.storage_bucket = objects.bucket_id) AND (d.storage_path = objects.name) AND (d.storage_status = 'cloud_available'::text) AND app_console_can_access_dossier(d.app_dossier_id, d.hektor_annonce_id))))
    OR (((storage.foldername(name))[1] = 'temp'::text) AND ((storage.foldername(name))[2] = 'uploads'::text) AND (EXISTS ( SELECT 1
       FROM app_console_job j
      WHERE (((j.id)::text = (storage.foldername(objects.name))[3]) AND (j.requested_by = auth.uid())))))
    -- A.2 P8-4 : les preuves et l'original rangés dans le dossier d'un document qu'on a déjà le droit de lire.
    OR public.app_console_dossier_document_lisible(name)
  )
);

do $$
begin
  if (select qual from pg_policies where schemaname = 'storage' and tablename = 'objects' and policyname = 'hektor_console_documents_read_scope') not ilike '%app_console_dossier_document_lisible%' then
    raise exception 'POSE RATEE : la branche n''est pas dans la regle.';
  end if;
end $$;
