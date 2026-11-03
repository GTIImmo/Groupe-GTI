-- Retour arrière de patch_index_signature_document_2026-11-03.sql : retire l'index, rien d'autre.
drop index if exists public.idx_app_console_document_signature_statut;
select count(*) as reste from pg_indexes where indexname = 'idx_app_console_document_signature_statut';  -- doit valoir 0
