-- G.10bis -- LA LIGNE D'UNE PHOTO NE DOIT PLUS DISPARAITRE              26/09/2026
--
-- POURQUOI. Les photos vont etre publiees a une adresse PERMANENTE batie sur l'id de
-- la ligne app_console_photo (uuid) :
--     gti-photo/{app_dossier_id}/{id}/w1600.jpg
-- Un portail la met en cache, un email l'integre. Si la ligne est supprimee puis
-- recreee, l'id change et l'adresse publiee pointe dans le vide -- et le derive
-- depose devient orphelin. (C'est deja cet id qui nomme le dossier du fichier sur le
-- serveur : console_job_worker.js:4758, :4816, rattrapage_photos.js:329.)
--
-- Aujourd'hui upsertConsolePhotos SUPPRIME les lignes dont la photo n'est plus dans
-- images_json. On passe en « delete-never », comme le registre d'affaires : on MARQUE.
--
-- MEME PATRON QUE app_affaire_ledger.present_in_hektor (boolean NOT NULL DEFAULT true)
-- -- on ne cree pas un troisieme vocabulaire pour la meme idee.
--
-- SANS EFFET SEUL : tant que le worker n'est pas redemarre, il continue de supprimer.
-- Les 436 524 lignes existantes deviennent toutes present_in_hektor = true, ce qui est
-- exact : elles sont toutes dans Hektor aujourd'hui.

alter table public.app_console_photo
  add column if not exists present_in_hektor boolean not null default true,
  add column if not exists absent_depuis     timestamptz;

comment on column public.app_console_photo.present_in_hektor is
  'false = la photo n''est plus dans images_json chez Hektor. On NE SUPPRIME PAS la '
  'ligne : son id porte l''adresse publique du derive et le chemin du fichier sur le '
  'serveur. Patron delete-never, comme app_affaire_ledger.';

comment on column public.app_console_photo.absent_depuis is
  'Quand la photo a quitte Hektor. Null si elle y est. Remis a null si elle revient.';

-- Les lecteurs d'affichage filtrent sur present_in_hektor : cet index leur evite de
-- balayer 436 524 lignes pour en ecarter une poignee.
create index if not exists app_console_photo_presentes_idx
  on public.app_console_photo (app_dossier_id, sort_order)
  where present_in_hektor;
