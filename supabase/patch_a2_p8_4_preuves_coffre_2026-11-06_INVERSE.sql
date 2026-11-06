-- RETOUR ARRIÈRE de patch_a2_p8_4_preuves_coffre_2026-11-06.sql : la règle d'avant, à l'identique, puis la fonction
-- retirée. Ne juge que SA part : il ne touche à rien d'autre que cette règle et cette fonction.

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
  )
);

drop function if exists public.app_console_dossier_document_lisible(text);

do $$
begin
  if (select qual from pg_policies where schemaname = 'storage' and tablename = 'objects' and policyname = 'hektor_console_documents_read_scope') ilike '%app_console_dossier_document_lisible%' then
    raise exception 'RETOUR ARRIERE RATE : la branche est encore dans la regle.';
  end if;
end $$;
