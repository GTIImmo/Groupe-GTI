-- =====================================================================
-- CHANTIER ③ -- 3e : LE JOURNAL DES SUPPRESSIONS (documents et photos)
-- Date : 2026-10-13 · Detail : notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md
-- Palier 1 sur 3. ⚠ CE PATCH NE CHANGE AUCUN COMPORTEMENT : il pose les tables
-- et les colonnes. Le worker et l'ecran viennent apres.
--
-- LA DEMANDE DE FREDERIC, MOT POUR MOT (13/10) :
--   « Si il est supprime dans Hektor donc supprime du run, alors on garde dans
--     l'app avec mention "supprime chez Hektor", une purge sera possible. Mais si
--     supprime par l'app, alors on demande la suppression chez Hektor et on
--     supprime dans l'app aussi. »
--   puis : « Retire l'idee de la corbeille. [...] Il faudrait juste une ligne, une
--     forme de journal des suppressions : qui, quoi, quand. »
--
-- CE QUE L'AUDIT A TROUVE, ET QUI REND CE PATCH PETIT :
--   ⭐ LE JOURNAL EXISTE DEJA DANS LE PROJET, DEUX FOIS --
--      app_console_deleted_annonce_log (78 lignes) et
--      app_console_deleted_contact_log. On recopie leur patron a l'identique :
--      job_id · app_dossier_id · hektor_* · requested_by (QUI) · reason ·
--      before_json (QUOI : toute la ligne d'avant) · result_json ·
--      created_at (QUAND). Eprouve sur une vraie ligne : l'annonce 62741 (21/07)
--      garde 17 champs dans before_json, avec son demandeur.
--      ⚠ Mais PAS TOUJOURS : une autre ligne a before_json vide et aucun
--        demandeur. Le patron est bon, son REMPLISSAGE doit etre garanti --
--        c'est le palier 2 (worker) qui s'en charge, et il refusera de detruire
--        si le journal n'a pas pu s'ecrire.
--   ⭐ LA MENTION « PLUS CHEZ HEKTOR » EXISTE DEJA POUR LES PHOTOS (G.10bis) :
--      present_in_hektor + absent_depuis. Les DOCUMENTS ne l'ont pas. On pose
--      donc LES MEMES NOMS -- un seul vocabulaire dans le projet.
--
-- LES MESURES QUI ONT CONDUIT ICI (13/10) :
--   162 543 documents (~229 Go) · 441 117 photos
--   34 documents DETRUITS par l'app du 14/05 au 22/07, sur 11 annonces REELLES
--     (19 sur la seule 24113) -- fichier cloud, fichier serveur ET ligne, sans
--     aucune trace. L'ecran disait seulement « Supprimer ce document dans Hektor ? »
--   0 corbeille, et aucune trace qu'un document a existe (l'empreinte
--     app_console_document_fingerprint est PAR ANNONCE, pas par document)
--   1 a 12 documents que Hektor n'a plus et dont nous ne savons rien
--   0 photo marquee absente sur 441 117 -- le mecanisme des photos TOURNE
--     (toutes portent present_in_hektor = true), il n'a jamais rien eu a marquer
--
-- RETOUR ARRIERE : supabase/patch_chantier3_3e_journal_suppressions_2026-10-13_INVERSE.sql
-- REPETITION     : supabase/patch_chantier3_3e_journal_suppressions_2026-10-13_REPETITION.sql
-- ⚠ NE LE COLLER QU'UNE SEULE FOIS (le succes est un NOTICE, invisible dans l'editeur).
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. LE JOURNAL DES DOCUMENTS SUPPRIMES
--
-- ⚠ `document_id` et `document_name` sont des COLONNES, pas seulement des cles de
--   before_json : Frederic veut lire « qui quoi quand » sans ouvrir un JSON.
-- ⚠ Pas de cle etrangere vers app_console_document : la ligne est DETRUITE juste
--   apres, une FK empecherait le journal d'exister. C'est tout l'interet.
-- ---------------------------------------------------------------------
create table if not exists public.app_console_deleted_document_log (
  id                  uuid primary key default gen_random_uuid(),
  job_id              uuid references public.app_console_job(id) on delete set null,
  app_dossier_id      bigint,
  hektor_annonce_id   text not null,
  document_id         uuid,
  hektor_document_id  text,
  document_name       text,
  requested_by        uuid references auth.users(id) on delete set null,
  reason              text,
  before_json         jsonb,
  result_json         jsonb,
  created_at          timestamptz not null default now()
);

comment on table public.app_console_deleted_document_log is
  'Chantier 3e, 13/10/2026. QUI a supprime QUOI et QUAND. Ecrit AVANT la '
  'destruction : si cette ligne ne peut pas s''ecrire, le worker NE DETRUIT PAS. '
  '`before_json` garde la ligne entiere (nom, type, empreinte sha256, taille, '
  'chemins cloud et serveur, id Hektor, visibilite) -- la suppression est '
  'definitive, le journal dit ce qui a existe. Patron : app_console_deleted_annonce_log.';

-- Le journal se lira PAR ANNONCE, du plus recent au plus ancien. Le patron copie
-- n'a que sa cle primaire (78 lignes, ca suffisait) ; ici on prevoit la lecture.
create index if not exists app_console_deleted_document_log_annonce_idx
  on public.app_console_deleted_document_log (hektor_annonce_id, created_at desc);

-- ---------------------------------------------------------------------
-- 2. LE JOURNAL DES PHOTOS SUPPRIMEES
--
-- ⚠ `before_json` DEVRA EMPORTER `derives_json`. Decision de Frederic du 13/10 :
--   les derives publics « partent tout de suite ». Il l'a tranche en connaissant
--   la consequence, que son propre code ecrit noir sur blanc :
--     « l'id porte le chemin du fichier sur le serveur et l'adresse PUBLIQUE de
--       ses derives, qu'un portail met en cache et qu'un email integre. Un id
--       supprime ne revient jamais. »
--   ➡ les adresses deja diffusees (portails en cache, emails envoyes) tomberont.
--     Le journal est donc la SEULE trace de ce qui a ete publie.
-- ---------------------------------------------------------------------
create table if not exists public.app_console_deleted_photo_log (
  id                 uuid primary key default gen_random_uuid(),
  job_id             uuid references public.app_console_job(id) on delete set null,
  app_dossier_id     bigint,
  hektor_annonce_id  text not null,
  photo_id           uuid,
  hektor_photo_id    text,
  filename           text,
  requested_by       uuid references auth.users(id) on delete set null,
  reason             text,
  before_json        jsonb,
  result_json        jsonb,
  created_at         timestamptz not null default now()
);

comment on table public.app_console_deleted_photo_log is
  'Chantier 3e, 13/10/2026. QUI a supprime QUELLE photo et QUAND. Ecrit AVANT la '
  'destruction : si cette ligne ne peut pas s''ecrire, le worker NE DETRUIT PAS. '
  '⚠ `before_json` emporte `derives_json` : les derives PUBLICS partent avec la '
  'photo (decision de Frederic du 13/10), donc les adresses deja diffusees '
  'tomberont -- ce journal est la seule trace de ce qui a ete publie.';

create index if not exists app_console_deleted_photo_log_annonce_idx
  on public.app_console_deleted_photo_log (hektor_annonce_id, created_at desc);

-- ---------------------------------------------------------------------
-- 3. LES DROITS, RECOPIES A L'IDENTIQUE DU PATRON
--    Releve le 13/10 sur app_console_deleted_annonce_log :
--      RLS active · INSERT : service_role (with check true)
--      SELECT : authenticated, MAIS seulement si app_console_current_role()='admin'
--      grants : authenticated et service_role = tout
--    ⚠ `anon` n'a RIEN, et n'aura rien (chantier ①).
--    ⚠ Un journal de suppressions est une piece sensible : il dit qui a detruit
--      quoi. Le reserver aux admins est deliberé, et c'est deja la regle du patron.
-- ---------------------------------------------------------------------
alter table public.app_console_deleted_document_log enable row level security;
alter table public.app_console_deleted_photo_log    enable row level security;

drop policy if exists app_console_deleted_document_log_service_insert on public.app_console_deleted_document_log;
create policy app_console_deleted_document_log_service_insert
  on public.app_console_deleted_document_log for insert to service_role with check (true);

drop policy if exists app_console_deleted_document_log_admin_select on public.app_console_deleted_document_log;
create policy app_console_deleted_document_log_admin_select
  on public.app_console_deleted_document_log for select to authenticated
  using (public.app_console_current_role() = 'admin');

drop policy if exists app_console_deleted_photo_log_service_insert on public.app_console_deleted_photo_log;
create policy app_console_deleted_photo_log_service_insert
  on public.app_console_deleted_photo_log for insert to service_role with check (true);

drop policy if exists app_console_deleted_photo_log_admin_select on public.app_console_deleted_photo_log;
create policy app_console_deleted_photo_log_admin_select
  on public.app_console_deleted_photo_log for select to authenticated
  using (public.app_console_current_role() = 'admin');

grant all on public.app_console_deleted_document_log to authenticated, service_role;
grant all on public.app_console_deleted_photo_log    to authenticated, service_role;

-- ---------------------------------------------------------------------
-- 4. LA MENTION « PLUS CHEZ HEKTOR » SUR LES DOCUMENTS
--    Memes noms que les photos (G.10bis) : un seul vocabulaire.
--
-- ⚠ `default true` ET un rattrapage des lignes existantes : sans ca, « false »
--   et « vide » voudraient dire la meme chose, et on ne saurait pas distinguer
--   « Hektor ne l'a plus » de « on n'a jamais regarde ». Les 162 543 documents
--   actuels ONT ete vus chez Hektor (la synchro passe partout : 23 850 annonces,
--   toutes revues depuis le 18/08), donc `true` est la verite pour eux.
-- ---------------------------------------------------------------------
alter table public.app_console_document
  add column if not exists present_in_hektor boolean default true,
  add column if not exists absent_depuis     timestamptz;

update public.app_console_document
   set present_in_hektor = true
 where present_in_hektor is null;

comment on column public.app_console_document.present_in_hektor is
  'false = Hektor ne l''a plus, NOUS SI. La ligne et les fichiers sont CONSERVES '
  '(decision de Frederic du 13/10 : « on garde dans l''app avec mention supprime '
  'chez Hektor, une purge sera possible »). Meme nom et meme sens que '
  'app_console_photo.present_in_hektor (G.10bis).';

comment on column public.app_console_document.absent_depuis is
  'Depuis quand Hektor ne l''a plus. Posee UNE SEULE FOIS : on ne re-date jamais '
  'un document deja marque, sinon l''horloge d''une purge repartirait a chaque '
  'synchro (meme regle que app_console_photo.hors_vitrine_depuis).';

-- La purge future cherchera « les absents depuis plus de N mois » sans balayer
-- 162 543 lignes.
create index if not exists app_console_document_absent_idx
  on public.app_console_document (absent_depuis)
  where present_in_hektor is false;

-- ---------------------------------------------------------------------
-- 5. LE CONTROLE DE SORTIE
-- ---------------------------------------------------------------------
DO $ctrl$
DECLARE
  n_doc_log int; n_photo_log int; n_cols int; n_pol int; n_null int;
BEGIN
  SELECT count(*) INTO n_doc_log FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND c.relname='app_console_deleted_document_log';
  SELECT count(*) INTO n_photo_log FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND c.relname='app_console_deleted_photo_log';
  IF n_doc_log <> 1 OR n_photo_log <> 1 THEN
    RAISE EXCEPTION 'STOP : les deux journaux ne sont pas la (% et %)', n_doc_log, n_photo_log;
  END IF;

  SELECT count(*) INTO n_cols FROM pg_attribute
   WHERE attrelid='public.app_console_document'::regclass
     AND attname IN ('present_in_hektor','absent_depuis') AND NOT attisdropped;
  IF n_cols <> 2 THEN
    RAISE EXCEPTION 'STOP : les colonnes de la mention manquent (% sur 2)', n_cols;
  END IF;

  SELECT count(*) INTO n_null FROM public.app_console_document WHERE present_in_hektor IS NULL;
  IF n_null <> 0 THEN
    RAISE EXCEPTION 'STOP : % documents sans present_in_hektor -- le rattrapage a rate', n_null;
  END IF;

  SELECT count(*) INTO n_pol FROM pg_policies
   WHERE schemaname='public'
     AND tablename IN ('app_console_deleted_document_log','app_console_deleted_photo_log');
  IF n_pol <> 4 THEN
    RAISE EXCEPTION 'STOP : % politiques au lieu de 4', n_pol;
  END IF;

  RAISE NOTICE 'OK : 2 journaux, 4 politiques, la mention posee sur % documents',
    (SELECT count(*) FROM public.app_console_document WHERE present_in_hektor IS TRUE);
END $ctrl$;

notify pgrst, 'reload schema';

COMMIT;
