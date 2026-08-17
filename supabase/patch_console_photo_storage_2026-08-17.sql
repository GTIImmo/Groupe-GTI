-- =====================================================================
-- PHOTOS — rendre le binaire STOCKABLE (chantier d'indépendance, étape 1).
-- 2026-08-17.
--
-- LE PROBLÈME
-- -----------
-- `app_console_photo` n'est aujourd'hui qu'un INDEX D'URL : url_preview /
-- url_hd pointent le CDN Hektor (groupe-gti-immobilier.staticlbi.com).
-- Aucun octet n'est rapatrié — il n'existe nulle part de mécanisme de
-- téléchargement (vérifié : worker, python, backend, export vitrine).
-- 100 % des 56 863 annonces (tous index confondus) affichent donc des
-- images hébergées chez Hektor. À la coupure, toutes les photos cassent :
-- app négociateur, espace client, emails, écrans vitrine.
--
-- CE PATCH
-- --------
-- Purement additif : il ajoute à `app_console_photo` les colonnes qui
-- manquent pour porter un fichier, en miroir EXACT de ce que
-- `app_console_document` possède déjà. Il ne télécharge rien par lui-même :
-- il rend le stockage possible. Le téléchargement est fait par le worker
-- (persistConsolePhotoFile).
--
-- PRINCIPE DE STOCKAGE (décision Frédéric, 2026-08-17)
-- ----------------------------------------------------
--   serveur local = TOUT, tous les index, sans condition -> le maître
--   cloud         = l'INDEX + extraction à la demande     -> reste léger
-- C'est déjà le principe appliqué au détail des annonces archivées.
-- `storage_status` reprend donc le vocabulaire des documents :
--   'pending'         : indexée, pas encore téléchargée
--   'local_only'      : fichier sur le serveur, pas de copie cloud
--   'cloud_available' : fichier sur le serveur ET copie cloud
--
-- Volumétrie mesurée (300 photos pesées, aucun échec) : 0,49 Mo en moyenne,
-- médiane 0,29 Mo, 90e centile 1,14 Mo. Soit ~163 Go pour les ~318 000
-- photos des quatre index — largement dans les 806 Go libres du serveur.
-- =====================================================================

alter table public.app_console_photo
  add column if not exists storage_bucket text,
  add column if not exists storage_path   text,
  add column if not exists storage_status text not null default 'pending',
  add column if not exists file_size      bigint,
  add column if not exists sha256         text,
  add column if not exists metadata_json  jsonb;

comment on column public.app_console_photo.storage_status is
  'pending = indexee non telechargee ; local_only = fichier sur le serveur ; cloud_available = serveur + copie cloud.';
comment on column public.app_console_photo.storage_path is
  'Chemin dans le bucket Supabase quand une copie cloud existe (annonces/<annonce>/photos/<photo>/<fichier>).';
comment on column public.app_console_photo.metadata_json is
  'Metadonnees techniques : local_archive_path, local_archive_root, local_archived_at, source_url, mime_type.';
comment on column public.app_console_photo.sha256 is
  'Empreinte du binaire telecharge : permet de ne pas re-telecharger une photo inchangee.';

-- Retrouver rapidement ce qui reste a telecharger (pilotage du rattrapage).
create index if not exists idx_app_console_photo_storage_status
  on public.app_console_photo (storage_status)
  where storage_status = 'pending';
