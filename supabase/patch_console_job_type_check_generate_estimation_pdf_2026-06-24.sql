-- Lot 1 — Avis de valeur : autorise le type de job generate_estimation_pdf dans la
-- contrainte CHECK de app_console_job.job_type (sinon l'insert est rejeté).
-- Additif : reprend les 33 types LIVE (pg_get_constraintdef) + ajoute generate_estimation_pdf.
-- Rien retiré. Appliquée en prod le 2026-06-24.

alter table public.app_console_job drop constraint if exists app_console_job_job_type_check;
alter table public.app_console_job add constraint app_console_job_job_type_check check (job_type = any (array[
  'sync_console_documents','prepare_document_cloud','generate_estimation_pdf','upload_document_to_hektor','delete_document_from_hektor',
  'sync_hektor_photos','upload_hektor_photo','prepare_archived_annonce_detail','prepare_historical_annonce_detail',
  'link_hektor_mandant','create_hektor_contact','update_hektor_contact','add_hektor_contact_search','update_hektor_contact_search',
  'delete_hektor_contact_search','delete_hektor_contact','create_hektor_mandant_contact','update_hektor_mandant_contact',
  'update_hektor_annonce_fields','create_hektor_mandat_auto_number','delete_hektor_annonce','archive_hektor_annonce',
  'restore_hektor_annonce','change_hektor_annonce_status','assign_hektor_annonce_negotiator','create_hektor_draft_annonce',
  'matterport_online','matterport_offline','matterport_archive','matterport_reactivate',
  'refresh_console_data','refresh_console_contact_data','archive_cloud_documents'
]::text[]));
