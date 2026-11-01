-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PHASE 2 — LA NATURE DE CHAQUE FICHE ARRIVE CHEZ SUPABASE  01/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'éditeur SQL Supabase, APRES la répétition.
-- Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §4 (étape 3) et §8-§9.
--
-- CE QUE FAIT CE PATCH — ADDITIF :
--   1. six colonnes NEUVES, vides, sur app_contact_current. La nuit les remplit
--      (phase2/contacts/nature_des_fiches.py, puis le push des contacts) :
--        nature_fiche              personne_seule · couple · conjoint ·
--                                  conjoint_sans_prenom · case_conjoint_vide ·
--                                  case_vide_orpheline
--        couple_deuxieme           (couples) conjoint_avec_prenom · nom_recopie ·
--                                  case_vide · aucune_deuxieme_fiche · aucun_lien
--        civilite_app              « Mme. » perdue à la migration, rendue d'après
--                                  l'ancien logiciel (décision « A » du 01/11) ;
--                                  NULL = lire `civilite` (celle de Hektor)
--        civilite_source           'ancien_logiciel' quand civilite_app est posée
--        suit_principale_archivee  case vide active dont la principale est archivée
--        supprimee_chez_hektor     fiche sans agence : supprimée chez Hektor
--   2. la clé de battement de l'étape « phase2 nature des fiches contact »
--      (une clé sans ligne part dans le vide, leçon du 13/10).
--
-- CE QU'IL NE FAIT PAS : aucune vue n'est touchée (l'écran lira les colonnes en
-- phase 3) ; `civilite`, `couple_role`, `display_name` ne changent pas ; rien chez
-- Hektor ; aucune ligne existante modifiée. Pas de contrainte CHECK : une valeur
-- refusée ferait échouer TOUT le push des contacts.
--
-- ⛔ ORDRE DES GESTES :
--   a. coller ce patch ;
--   b. SEULEMENT APRES : APP_CONTACT_NATURE=1 dans C:\Hektor\Projet\.env
--      (sans les colonnes, le push des contacts échouerait) ;
--   c. la nuit suivante envoie la nature : ⚠ TOUT LE PARC repart UNE fois
--      (~62 000 lignes), puis seulement ce qui change.
-- RETOUR ARRIÈRE : supabase/patch_couple_phase2_nature_2026-11-01_INVERSE.sql
--    (éteindre APP_CONTACT_NATURE D'ABORD).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. LES COLONNES
alter table public.app_contact_current
  add column if not exists nature_fiche text,
  add column if not exists couple_deuxieme text,
  add column if not exists civilite_app text,
  add column if not exists civilite_source text,
  add column if not exists suit_principale_archivee boolean,
  add column if not exists supprimee_chez_hektor boolean;
comment on column public.app_contact_current.nature_fiche is
  'COUPLES phase 2 (01/11/2026) : nature de la fiche, calculee la nuit (phase2/contacts/nature_des_fiches.py).';
comment on column public.app_contact_current.couple_deuxieme is
  'COUPLES phase 2 (01/11/2026) : pour un couple, ce qu''est sa deuxieme fiche (cas a-e de l''audit).';
comment on column public.app_contact_current.civilite_app is
  'COUPLES phase 2 (01/11/2026) : civilite rendue par nous (Mme. perdue a la migration) ; NULL = lire civilite (Hektor). Jamais envoyee a Hektor.';
comment on column public.app_contact_current.civilite_source is
  'COUPLES phase 2 (01/11/2026) : origine de civilite_app (ancien_logiciel).';
comment on column public.app_contact_current.suit_principale_archivee is
  'COUPLES phase 2 (01/11/2026) : case de conjoint vide, active, dont la principale est archivee.';
comment on column public.app_contact_current.supprimee_chez_hektor is
  'COUPLES phase 2 (01/11/2026) : fiche sans agence, supprimee chez Hektor, gardee parce qu''une annonce ou une offre la cite.';

-- 2. LA CLE DE BATTEMENT
insert into public.app_worker_registry
  (worker_key, worker_name, worker_role, worker_type, criticality, frequency,
   status, owner, script_path, expected_max_runtime_minutes, monitoring_domain,
   source_notes)
values
  ('phase2.nature_contacts',
   'Nature des fiches contact (couples, civilite rendue)',
   'Calcule chaque nuit la nature de chaque fiche (personne seule, couple, conjoint, cases vides), '
   'la civilite Mme. rendue d''apres l''ancien logiciel, les cases archivees de fait et les fiches '
   'supprimees chez Hektor. Table locale contact_nature_current ; le push l''envoie si APP_CONTACT_NATURE=1.',
   'python_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'phase2\contacts\nature_des_fiches.py',
   5, 'business',
   'Ajoutee le 01/11/2026 (couples, phases 1-2). Ne lit et n''ecrit que la base locale ; aucune '
   'requete chez Hektor. Mesure : ~8 s.')
on conflict (worker_key) do nothing;

COMMIT;

-- CONTROLE (lecture seule) : colonnes 6, battement 1, remplies 0 avant la nuit
select
  (select count(*) from information_schema.columns
    where table_schema = 'public' and table_name = 'app_contact_current'
      and column_name in ('nature_fiche','couple_deuxieme','civilite_app','civilite_source',
                          'suit_principale_archivee','supprimee_chez_hektor')) as colonnes,
  (select count(*) from public.app_worker_registry where worker_key = 'phase2.nature_contacts') as battement,
  (select count(*) from public.app_contact_current where nature_fiche is not null) as remplies_avant_la_nuit;
