-- ═══════════════════════════════════════════════════════════════════════════════
-- CHANTIER GED — MORCEAU 1 : LA BASE DE L'OUTIL D'AJOUT DE DOCUMENTS     12/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md, §12 (la proposition
-- arrêtée) et §6.4 (la nomenclature, points 1 à 7 tranchés par Frédéric le 12/11).
--
-- ─── CE QUE CE PATCH POSE ───
--   ① app_ged_type        la nomenclature : 60 types + 6 types partenaires (66 codes).
--                         Le CODE est un contrat (jamais renommé) ; le libellé peut changer.
--   ② app_ged_classement  UNE fiche par document DÉPOSÉ AVEC L'OUTIL : son type, qui l'a
--                         décidé, ce que l'IA ou le nom avaient proposé.
--   ③ app_ged_rattachement à quoi le document se rapporte (bien, mandat, affaire, contact).
--   ④ app_ged_journal     chaque changement de classement, avant et après
--                         (« une saisie ne se perd jamais »).
--   ⑤ trois interrupteurs ÉTEINTS : ged_depot_multiple, ged_lecture_ia, ged_propositions.
--
-- ─── CE QUE CE PATCH NE FAIT PAS, ET C'EST VOULU ───
-- ⛔ IL NE TOUCHE PAS app_console_document : ni colonne, ni index, ni déclencheur, ni CLÉ
--   ÉTRANGÈRE. La table appartient aussi à la signature (metadata_json, storage_path) et la
--   synchro y supprime et recrée des lignes (15 403 recréées en sept.-oct.). Le lien vers le
--   document est donc une simple colonne uuid, doublée d'une EMPREINTE DE SECOURS
--   (annonce + sha256 + nom) qui permet de le retrouver si la ligne change d'id. Une clé
--   étrangère aurait verrouillé app_console_document pendant la pose, et son ON DELETE
--   aurait effacé le lien au premier dédoublonnage de la synchro.
-- ⛔ AUCUN DOCUMENT EXISTANT N'EST CLASSÉ (décision du 12/11, point 5 : « on ne va pas
--   traiter les documents déjà en base »). Les tables ② ③ ④ naissent VIDES.
-- ⛔ PAS ENCORE les tables de lecture, de valeurs lues et de propositions : elles viendront
--   avec les morceaux qui les remplissent (6 à 9), quand leur forme sera éprouvée.
-- ⛔ AUCUNE FONCTION. L'écriture passera par des RPC du morceau 2.
-- ⛔ RIEN chez Hektor, rien dans le run de nuit, rien dans le worker, rien à l'écran.
--
-- ─── LES DROITS ───
-- ⛔ Dans ce schéma, une table neuve donne PAR DÉFAUT tous les droits à `authenticated`
--   (pg_default_acl, mesuré le 12/11) et `revoke all from public` ne la ferme pas : chaque
--   rôle est donc nommé. RLS activée partout.
--   · app_ged_type : lisible par tout utilisateur actif (comme app_setting), rien d'autre.
--   · ② ③ ④ : RLS SANS POLITIQUE = personne ne lit ni n'écrit, sauf le service_role. Les
--     droits de l'écran se poseront au morceau 2, avec les RPC.
--
-- ─── CE QUE ÇA POURRAIT TOUCHER AILLEURS ───
--   · La DESCENTE de 07:45 (phase2/sync/pull_from_supabase.py) découvre les tables du schéma :
--     elle recopiera ces quatre tables (66 lignes + vides). Rien d'autre ne les lit.
--   · app_setting reçoit 3 lignes neuves, éteintes : aucun code ne les lit encore.
--   · Les noms `app_ged_*` sont neufs (aucune table ni réglage `ged` en base, mesuré le 12/11).
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_ged_m1_base_2026-11-12_INVERSE.sql : il refuse si un classement a déjà été
-- écrit (une vraie saisie), sinon il retire tout et vérifie qu'il ne reste aucune trace.
-- Répétition sans rien garder : supabase/patch_ged_m1_base_2026-11-12_REPETITION.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

do $garde$
begin
  if exists (select 1 from information_schema.tables
              where table_schema = 'public' and table_name like 'app\_ged\_%') then
    raise exception 'ARRET : une table app_ged_* existe deja -- patch deja applique ?';
  end if;
  if exists (select 1 from public.app_setting
              where key in ('ged_depot_multiple', 'ged_lecture_ia', 'ged_propositions')) then
    raise exception 'ARRET : un interrupteur ged_* existe deja -- patch deja applique ?';
  end if;
end
$garde$;

-- ─────────────────────────────────────────────────────── ① LA NOMENCLATURE
create table public.app_ged_type (
  code         text primary key,
  famille      text not null,
  libelle      text not null,
  -- 'lue'            l'IA lit ses valeurs après l'envoi (23 types, décision du 12/11)
  -- 'classer'        classée seulement : la lecture n'apporterait rien à comparer
  -- 'jamais_envoye'  jamais envoyée à l'IA, même pour la classer (RIB : « NON IL FAUT
  --                  EXCLURE LES RIB ! », 12/11 ; comptes, notes internes, courrier, clés)
  lecture      text not null,
  -- accès restreint (admin, managers, négociateur du bien) : les pièces des personnes
  sensible     boolean not null default false,
  ordre        integer not null,
  actif        boolean not null default true,
  constraint app_ged_type_code_forme check (code ~ '^[a-z]+(\.[a-z_]+)?$'),
  constraint app_ged_type_lecture check (lecture in ('lue', 'classer', 'jamais_envoye'))
);

comment on table public.app_ged_type is
  'GED : la nomenclature des documents (note du chantier GED §6.4, tranchée le 12/11/2026). '
  'Le CODE est un contrat : il ne se renomme jamais (on en ajoute un, on en désactive un). '
  'lecture = ce que l''IA fait du document (lue / classer / jamais_envoye). '
  'sensible = accès restreint (pièces des personnes).';

insert into public.app_ged_type (code, famille, libelle, lecture, sensible, ordre) values
  -- mandat
  ('mandat.vente',              'mandat',       'Mandat de vente',                                        'lue',           false, 101),
  ('mandat.avenant',            'mandat',       'Avenant au mandat',                                      'lue',           false, 102),
  ('mandat.fin',                'mandat',       'Fin de mandat (résiliation, dénonciation)',              'lue',           false, 103),
  ('mandat.honoraires',         'mandat',       'Accord ou baisse d''honoraires',                         'classer',       false, 104),
  ('mandat.recherche',          'mandat',       'Mandat de recherche',                                    'classer',       false, 105),
  -- justificatifs du mandat
  ('justif.titre',              'justificatifs', 'Titre ou origine de propriété',                         'lue',           false, 201),
  ('justif.identite',           'justificatifs', 'Pièce d''identité',                                     'lue',           true,  202),
  ('justif.taxe',               'justificatifs', 'Taxe foncière, impôts locaux',                          'classer',       false, 203),
  ('justif.pouvoir',            'justificatifs', 'Pouvoir, procuration',                                  'classer',       false, 204),
  ('justif.societe',            'justificatifs', 'Société venderesse (Kbis, statuts)',                    'classer',       false, 205),
  ('justif.etat_civil',         'justificatifs', 'État civil, capacité (livret, mariage, décès, jugement)', 'lue',         true,  206),
  ('justif.rib',                'justificatifs', 'RIB',                                                   'jamais_envoye', true,  207),
  -- transaction
  ('transaction.offre',         'transaction',  'Offre d''achat (et sa réponse)',                         'lue',           false, 301),
  ('transaction.avant_contrat', 'transaction',  'Compromis, promesse de vente',                           'lue',           false, 302),
  ('transaction.financement',   'transaction',  'Financement (accord, offre ou refus de prêt)',           'lue',           true,  303),
  ('transaction.acte',          'transaction',  'Acte de vente, attestation de vente',                    'lue',           false, 304),
  ('transaction.renseignements','transaction',  'Fiche de renseignements acquéreurs ou vendeurs',         'lue',           true,  305),
  ('transaction.notaire',       'transaction',  'Dossier ou courrier du notaire',                         'classer',       false, 306),
  ('transaction.annulation',    'transaction',  'Annulation d''une vente, désistement',                   'lue',           false, 307),
  ('transaction.sru',           'transaction',  'Notification SRU, rétractation',                         'classer',       false, 308),
  ('transaction.mobilier',      'transaction',  'Liste du mobilier',                                      'classer',       false, 309),
  ('transaction.sequestre',     'transaction',  'Séquestre, dépôt de garantie',                           'classer',       false, 310),
  -- visite
  ('visite.bon',                'visite',       'Bon de visite',                                          'classer',       false, 401),
  ('visite.compte_rendu',       'visite',       'Compte rendu de visite',                                 'classer',       false, 402),
  -- estimation
  ('estimation.avis',           'estimation',   'Avis de valeur, dossier d''estimation',                  'classer',       false, 501),
  -- diagnostics (un type par diagnostic : point 2 du 12/11)
  ('diag.dpe',                  'diagnostics',  'DPE',                                                    'lue',           false, 601),
  ('diag.dossier',              'diagnostics',  'Dossier de diagnostics (DDT)',                           'lue',           false, 602),
  ('diag.erp',                  'diagnostics',  'État des risques',                                       'lue',           false, 603),
  ('diag.assainissement',       'diagnostics',  'Assainissement (SPANC, raccordement)',                   'lue',           false, 604),
  ('diag.amiante',              'diagnostics',  'Amiante',                                                'classer',       false, 605),
  ('diag.surface',              'diagnostics',  'Surfaces (Carrez, habitable)',                           'lue',           false, 606),
  ('diag.electricite',          'diagnostics',  'Électricité',                                            'lue',           false, 607),
  ('diag.gaz',                  'diagnostics',  'Gaz',                                                    'lue',           false, 608),
  ('diag.plomb',                'diagnostics',  'Plomb (CREP)',                                           'classer',       false, 609),
  ('diag.audit',                'diagnostics',  'Audit énergétique',                                      'classer',       false, 610),
  ('diag.termites',             'diagnostics',  'Termites, parasites, mérule',                            'classer',       false, 611),
  -- copropriété
  ('copro.pv_ag',               'copropriete',  'PV ou convocation d''assemblée générale',                'classer',       false, 701),
  ('copro.arrete_charges',      'copropriete',  'Arrêté ou décompte de charges (dépenses réelles)',       'lue',           false, 702),
  ('copro.appel_fonds',         'copropriete',  'Appels de fonds, budget prévisionnel',                   'lue',           false, 703),
  ('copro.reglement',           'copropriete',  'Règlement de copropriété, état descriptif',              'classer',       false, 704),
  ('copro.autre',               'copropriete',  'Autre document de copropriété',                          'classer',       false, 705),
  ('copro.carnet',              'copropriete',  'Carnet d''entretien, fiche synthétique',                 'lue',           false, 706),
  ('copro.dtg',                 'copropriete',  'DTG, plan pluriannuel de travaux',                       'classer',       false, 707),
  ('copro.etat_date',           'copropriete',  'Pré-état daté, état daté',                               'classer',       false, 708),
  -- urbanisme et terrain
  ('urba.cadastre',             'urbanisme',    'Cadastre, parcelles',                                    'classer',       false, 801),
  ('urba.permis',               'urbanisme',    'Permis, déclaration de travaux, conformité',             'classer',       false, 802),
  ('urba.certificat',           'urbanisme',    'Certificat d''urbanisme, PLU, lotissement',              'classer',       false, 803),
  ('urba.bornage',              'urbanisme',    'Bornage, division, servitudes',                          'classer',       false, 804),
  ('urba.etude_sol',            'urbanisme',    'Étude de sol',                                           'classer',       false, 805),
  -- bien
  ('bien.plans',                'bien',         'Plans, vues du bien',                                    'classer',       false, 901),
  ('bien.cles',                 'bien',         'Clés (photo, remise)',                                   'jamais_envoye', false, 902),
  ('bien.entretien',            'bien',         'Entretien, énergie (chaudière, ramonage, factures)',     'classer',       false, 903),
  ('bien.descriptif',           'bien',         'Descriptif, fiche commerciale',                          'classer',       false, 904),
  -- facturation (factures d'honoraires NON sensibles : point 6 du 12/11)
  ('facture.honoraires',        'facturation',  'Facture ou note d''honoraires GTI',                      'lue',           false, 1001),
  ('facture.autre',             'facturation',  'Autre facture',                                          'classer',       false, 1002),
  ('facture.devis',             'facturation',  'Devis, travaux',                                         'classer',       false, 1003),
  -- location, entreprise, courrier, interne (gardées : point 4 du 12/11)
  ('location.bail',             'location',     'Bail, état des lieux, quittance, gérance',               'classer',       false, 1101),
  ('entreprise.comptes',        'entreprise',   'Bilans, comptes (fonds de commerce)',                    'jamais_envoye', false, 1201),
  ('courrier',                  'courrier',     'Courrier, lettre, accusé de réception',                  'jamais_envoye', false, 1301),
  ('interne.notes',             'interne',      'Notes, suivi interne',                                   'jamais_envoye', false, 1401),
  -- partenaires (les 6 gardés : point 7 du 12/11)
  ('partenaire.convention',     'partenaires',  'Convention avec un partenaire',                          'classer',       false, 1501),
  ('partenaire.assurance',      'partenaires',  'Assurance d''un partenaire',                             'classer',       false, 1502),
  ('partenaire.certification',  'partenaires',  'Certification d''un partenaire',                         'classer',       false, 1503),
  ('partenaire.societe',        'partenaires',  'Société d''un partenaire (Kbis, statuts)',               'classer',       false, 1504),
  ('partenaire.tarifs',         'partenaires',  'Tarifs d''un partenaire',                                'classer',       false, 1505),
  ('partenaire.autre',          'partenaires',  'Autre document de partenaire',                           'classer',       false, 1506);

-- ─────────────────────────────────────────────────────── ② LE CLASSEMENT
create table public.app_ged_classement (
  id                       uuid primary key default gen_random_uuid(),
  -- ⛔ PAS de clé étrangère vers app_console_document (voir l'en-tête) : un simple uuid,
  --   et l'empreinte de secours juste en dessous pour le retrouver s'il change d'id.
  app_console_document_id  uuid,
  hektor_annonce_id        text not null,
  sha256                   text,
  document_name            text not null,
  -- le type DÉCIDÉ (celui qui fait foi)
  type_code                text not null references public.app_ged_type (code),
  -- qui l'a décidé : un humain, l'IA validée par un humain, le nom, ou l'app qui a
  -- généré le document (mandat, avis de valeur, plan cadastral)
  origine                  text not null,
  -- ce qui avait été PROPOSÉ, gardé même si l'humain a corrigé (mesure de justesse)
  type_propose             text,
  type_propose_par         text,
  decide_par               uuid,
  decide_le                timestamptz,
  cree_le                  timestamptz not null default now(),
  maj_le                   timestamptz not null default now(),
  constraint app_ged_classement_origine check (origine in ('humain', 'ia', 'nom', 'app_genere')),
  constraint app_ged_classement_propose_par check (type_propose_par is null or type_propose_par in ('ia', 'nom')),
  constraint app_ged_classement_nom_non_vide check (btrim(document_name) <> ''),
  constraint app_ged_classement_annonce_non_vide check (btrim(hektor_annonce_id) <> '')
);

-- un document n'a qu'UNE fiche vivante ; l'historique va au journal
create unique index app_ged_classement_un_par_document_uidx
  on public.app_ged_classement (app_console_document_id)
  where app_console_document_id is not null;
create index app_ged_classement_annonce_idx on public.app_ged_classement (hektor_annonce_id);
create index app_ged_classement_sha256_idx  on public.app_ged_classement (sha256) where sha256 is not null;

comment on table public.app_ged_classement is
  'GED : le classement d''un document DÉPOSÉ AVEC L''OUTIL (morceau 1, 12/11/2026). Les '
  'documents déjà en base ne sont pas classés (décision du 12/11). Pas de clé étrangère vers '
  'app_console_document : uuid + empreinte de secours (annonce, sha256, nom). Le type vit '
  'ICI, jamais dans app_console_document.document_type (réécrit par la synchro).';

-- ─────────────────────────────────────────────────────── ③ LES RATTACHEMENTS
create table public.app_ged_rattachement (
  id             uuid primary key default gen_random_uuid(),
  classement_id  uuid not null references public.app_ged_classement (id) on delete cascade,
  objet          text not null,
  objet_id       text not null,
  role           text,
  origine        text not null,
  cree_par       uuid,
  cree_le        timestamptz not null default now(),
  constraint app_ged_rattachement_objet check (objet in ('bien', 'mandat', 'affaire', 'contact')),
  constraint app_ged_rattachement_origine check (origine in ('humain', 'ia', 'nom', 'app_genere')),
  constraint app_ged_rattachement_objet_id_non_vide check (btrim(objet_id) <> ''),
  constraint app_ged_rattachement_unique unique (classement_id, objet, objet_id)
);
create index app_ged_rattachement_objet_idx on public.app_ged_rattachement (objet, objet_id);

comment on table public.app_ged_rattachement is
  'GED : à quoi un document se rapporte (bien, mandat, affaire, contact). Le même fichier '
  'relié, jamais copié. Une pièce de personne se rattache au CONTACT.';

-- ─────────────────────────────────────────────────────── ④ LE JOURNAL
create table public.app_ged_journal (
  id        bigint generated always as identity primary key,
  objet     text not null,
  objet_id  uuid not null,
  geste     text not null,
  avant     jsonb,
  apres     jsonb,
  par       uuid,
  le        timestamptz not null default now(),
  constraint app_ged_journal_objet check (objet in ('classement', 'rattachement'))
);
create index app_ged_journal_objet_idx on public.app_ged_journal (objet, objet_id);

comment on table public.app_ged_journal is
  'GED : chaque changement de classement ou de rattachement, avant et après. Une saisie ne '
  'se perd jamais.';

-- ─────────────────────────────────────────────────────── ⑤ LES DROITS
alter table public.app_ged_type          enable row level security;
alter table public.app_ged_classement    enable row level security;
alter table public.app_ged_rattachement  enable row level security;
alter table public.app_ged_journal       enable row level security;

-- ⛔ chaque rôle nommé : `revoke ... from public` ne ferme pas `authenticated`
revoke all on table public.app_ged_type          from public, anon, authenticated;
revoke all on table public.app_ged_classement    from public, anon, authenticated;
revoke all on table public.app_ged_rattachement  from public, anon, authenticated;
revoke all on table public.app_ged_journal       from public, anon, authenticated;
revoke all on sequence public.app_ged_journal_id_seq from public, anon, authenticated;

-- la nomenclature se LIT par tout utilisateur actif, comme app_setting ; rien d'autre
grant select on table public.app_ged_type to authenticated;
create policy app_ged_type_select_active_user on public.app_ged_type
  for select to authenticated using (public.is_app_user_active());

-- ② ③ ④ : RLS sans politique = personne n'y accède, sauf le service_role. Les droits de
-- l'écran se poseront au morceau 2, avec les RPC qui écrivent.

-- ─────────────────────────────────────────────────────── ⑥ LES INTERRUPTEURS (ÉTEINTS)
-- trois crans, patron de signature_youtrust : off / admin / on. Absent ou illisible = éteint.
insert into public.app_setting (key, value, description, updated_at) values
  ('ged_depot_multiple', 'off',
   'GED (12/11/2026) : la nouvelle fenêtre de dépôt (plusieurs fichiers, type proposé). off / admin / on. Éteint = le formulaire d''aujourd''hui, inchangé.',
   now()),
  ('ged_lecture_ia', 'off',
   'GED (12/11/2026) : le classement par l''IA avant l''envoi et la lecture des valeurs après. off / admin / on. Éteint = rien n''est envoyé à l''IA.',
   now()),
  ('ged_propositions', 'off',
   'GED (12/11/2026) : les propositions (remplir, conflit, alerte, pièce manquante). off / admin / on. Éteint = rien n''est montré.',
   now());

commit;

-- ALLUMER pour Frédéric seul : update public.app_setting set value = 'admin', updated_at = now() where key = 'ged_depot_multiple';
-- ÉTEINDRE                  : update public.app_setting set value = 'off',   updated_at = now() where key = 'ged_depot_multiple';

-- ═══════════════════════════════════════════════════════════════════════════════
-- LES CONTRÔLES — à lire après le COMMIT. Tout doit être VERT.
-- ═══════════════════════════════════════════════════════════════════════════════
select '① les 4 tables existent' as controle, count(*) as trouve,
       case when count(*) = 4 then 'VERT' else 'ROUGE' end as verdict
  from information_schema.tables
 where table_schema = 'public'
   and table_name in ('app_ged_type', 'app_ged_classement', 'app_ged_rattachement', 'app_ged_journal')
union all
select '② 66 codes (60 types + 6 partenaires)', count(*),
       case when count(*) = 66 then 'VERT' else 'ROUGE' end
  from public.app_ged_type
union all
select '③ 23 types lus', count(*),
       case when count(*) = 23 then 'VERT' else 'ROUGE' end
  from public.app_ged_type where lecture = 'lue'
union all
select '④ 5 types jamais envoyés à l''IA, dont le RIB', count(*),
       case when count(*) = 5 and bool_or(code = 'justif.rib') then 'VERT' else 'ROUGE' end
  from public.app_ged_type where lecture = 'jamais_envoye'
union all
select '⑤ 5 types sensibles, sans les factures', count(*),
       case when count(*) = 5 and not bool_or(code like 'facture.%') then 'VERT' else 'ROUGE' end
  from public.app_ged_type where sensible
union all
select '⑥ classement, rattachement et journal VIDES', (select count(*) from public.app_ged_classement)
         + (select count(*) from public.app_ged_rattachement) + (select count(*) from public.app_ged_journal),
       case when (select count(*) from public.app_ged_classement)
               + (select count(*) from public.app_ged_rattachement)
               + (select count(*) from public.app_ged_journal) = 0 then 'VERT' else 'ROUGE' end
union all
select '⑦ RLS activée sur les 4', count(*),
       case when count(*) = 4 then 'VERT' else 'ROUGE' end
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname = 'public' and c.relrowsecurity
   and c.relname in ('app_ged_type', 'app_ged_classement', 'app_ged_rattachement', 'app_ged_journal')
union all
select '⑧ anon n''a AUCUN droit', count(*),
       case when count(*) = 0 then 'VERT' else 'ROUGE' end
  from information_schema.role_table_grants
 where table_schema = 'public' and table_name like 'app\_ged\_%' and grantee in ('anon', 'PUBLIC')
union all
select '⑨ authenticated : seulement SELECT sur la nomenclature', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from information_schema.role_table_grants
 where table_schema = 'public' and table_name like 'app\_ged\_%' and grantee = 'authenticated'
union all
select '⑩ une seule politique, sur la nomenclature', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_policies where schemaname = 'public' and tablename like 'app\_ged\_%'
union all
select '⑪ les 3 interrupteurs sont ÉTEINTS', count(*),
       case when count(*) = 3 then 'VERT' else 'ROUGE' end
  from public.app_setting
 where key in ('ged_depot_multiple', 'ged_lecture_ia', 'ged_propositions') and value = 'off'
union all
-- ⭐ TÉMOIN : app_console_document n'a reçu AUCUNE clé étrangère nouvelle (seule celle de la signature)
select '⑫ TÉMOIN : app_console_document garde sa seule clé étrangère (signature)', count(*),
       case when count(*) = 1 then 'VERT' else 'ROUGE' end
  from pg_constraint where confrelid = 'public.app_console_document'::regclass;
