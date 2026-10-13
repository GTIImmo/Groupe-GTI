-- =====================================================================
-- REPETITION du patch 4j -- ⚠ CETTE VERSION N'ECRIT RIEN : ELLE S'ANNULE
-- Date : 2026-10-13
--
-- A COLLER DANS https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
--
-- Elle joue LE VRAI PATCH, puis LE VRAI INVERSE (le texte est decoupe dans les deux
-- fichiers, pas recopie a la main), compte a chaque etape, et finit par une ERREUR
-- VOLONTAIRE qui annule la transaction entiere. La base ressort INTACTE.
--
-- CE QU'IL FAUT VOIR, exactement :
--     ERROR:  P0001: ESSAI ANNULE -- 4j : lignes 53 -> 76 (+23) -> 53 (ecart 0) ;
--     critical 12 -> 16 -> 12 ; cles des 23 absentes du registre 23 -> 0 -> 23
--
--   Les trois choses qui comptent :
--     « +23 »         le patch pose bien 23 lignes, pas 22 ni 24
--     « ecart 0 »     l'inverse les retire TOUTES, la base revient a l'identique
--     « 23 -> 0 »     les 23 cles sont TOUTES couvertes -- puis remises a l'etat
--                     d'avant par l'inverse (-> 23)
--
--   Le premier chiffre (53) peut differer si une autre cle a ete posee entre-temps.
--   Ce qui doit etre exact, ce sont les ECARTS : +23, 0, et 23 -> 0 -> 23.
--
-- ⚠ CETTE REPETITION EST LA SECONDE. La premiere, collee le 13/10 a ~15:05, a donne
--   « +23 » et « ecart 0 » JUSTES, mais son troisieme controle disait « 1 -> 0 -> 1 » :
--   mon gabarit mettait des parentheses en trop autour de la liste, et Postgres n'a
--   verifie QU'UNE cle sur neuf. Corrige, et le controle porte desormais sur LES 23,
--   extraites du patch lui-meme pour qu'il ne puisse plus en deriver.
-- =====================================================================

BEGIN;

create temporary table _rep_4j (etape text, lignes bigint, critical bigint, orphelines bigint)
  on commit drop;

insert into _rep_4j
select 'avant',
       (select count(*) from public.app_worker_registry),
       (select count(*) from public.app_worker_registry where criticality = 'critical' and status = 'active'),
       (select count(*) from (values ('phase2.adresses_photos'),
   ('phase2.correspondance_identite'),
   ('phase2.doublure_relation'),
   ('phase2.doublure_mandat'),
   ('phase2.correspondance_annonces'),
   ('phase2.rattrapage_photos'),
   ('phase2.derives_photos'),
   ('phase2.sonde_photos'),
   ('phase1.archived_details'),
   ('hektor.drafts_sweep'),
   ('hektor.immo_pro'),
   ('hektor.immo_pro_archivees'),
   ('hektor.chauffage_delta'),
   ('contacts.champs_manquants'),
   ('phase2.magasin_mandat'),
   ('phase2.contrat_mandat'),
   ('phase2.contacts_layer_passe2'),
   ('phase2.doublure_affaire_ledger'),
   ('phase2.registre_relations'),
   ('phase2.registre_mandats'),
   ('phase2.magasin_affaire'),
   ('phase2.contrat_affaire'),
   ('phase2.carnet_annonce')) as v(cle)
          where not exists (select 1 from public.app_worker_registry r where r.worker_key = v.cle));

-- ---------------------------------------------------------------------
-- LE VRAI PATCH (decoupe dans patch_4j_battements_invisibles_2026-10-13.sql)
-- ---------------------------------------------------------------------
-- ---------------------------------------------------------------------
-- ① LES 9 DONT LE RUN ENVOIE DEJA LE NOM
-- ---------------------------------------------------------------------
insert into public.app_worker_registry
  (worker_key, worker_name, worker_role, worker_type, criticality, frequency,
   status, owner, script_path, expected_max_runtime_minutes, monitoring_domain,
   source_notes)
values
  -- ---- les 4 critical ----------------------------------------------
  ('phase2.adresses_photos',
   'Adresses des photos (colonnes soeurs)',
   'Entretient les adresses de nos photos dans les colonnes soeurs. Un garde-fou '
   'en base REFUSE d''agir si le parc passe sous son plancher (5 000) : sans lui, '
   'un push casse VIDERAIT les adresses de tout le parc et l''app retomberait '
   'entierement sur Hektor.',
   'node_script', 'critical', 'pipeline_step',
   'active', 'frederic',
   'Console\remplir_adresses_photos.js',
   10, 'business',
   'Ajoutee le 13/10/2026 (4j). CRITICAL parce que le commentaire du run promet '
   'depuis le 27/09 que « le moniteur le dit » -- ce qui etait FAUX : la cle n''avait '
   'aucune ligne. Tourne chaque nuit, 0 echec sur 46 journaux.'),

  ('phase2.correspondance_identite',
   'Correspondance d''identite des contacts',
   'Apprend au serveur quel numero Hektor EST quelle identite d''app. Sans elle, un '
   'contact ne dans l''app finit en DEUX fiches (mesure du 21/09 : 10000001 et 605450 '
   'pour la meme personne).',
   'python_worker', 'critical', 'pipeline_step',
   'active', 'frederic',
   'phase2\identite\descendre_correspondance_contacts.py',
   10, 'business',
   'Ajoutee le 13/10/2026 (4j). CRITICAL : son echec fabrique des doublons de '
   'contacts, qui se paient en travail manuel. Tourne chaque nuit, 0 echec sur 46.'),

  ('phase2.doublure_relation',
   'Doublure du registre des liens',
   'Fait descendre dans la copie locale le registre des liens de Supabase. Si elle '
   's''arrete, la copie vieillit SANS RIEN DIRE et les controles de la nuit repondent '
   '« tout va bien » sur des donnees perimees.',
   'python_worker', 'critical', 'pipeline_step',
   'active', 'frederic',
   'phase2\sync\pull_from_supabase.py',
   15, 'business',
   'Ajoutee le 13/10/2026 (4j). Entree dans le run le 03/10, 0 echec depuis. '
   'CRITICAL : le 10/10 un garde-fou a refuse de travailler parce que la doublure et '
   'la couche ne parlaient plus la meme serie de numeros.'),

  ('phase2.doublure_mandat',
   'Doublure du registre des mandats',
   'Fait descendre dans la copie locale le registre des mandats de Supabase. Meme '
   'raisonnement que la doublure des liens : une copie perimee rend tous les '
   'controles menteurs.',
   'python_worker', 'critical', 'pipeline_step',
   'active', 'frederic',
   'phase2\sync\pull_from_supabase.py',
   15, 'business',
   'Ajoutee le 13/10/2026 (4j). Entree dans le run le 08/10, 0 echec depuis.'),

  -- ---- les 5 medium ------------------------------------------------
  ('phase2.correspondance_annonces',
   'Correspondance d''identite des annonces',
   'La meme correspondance, pour les annonces. Pose aussi le garde-fou du compteur '
   '(app_dossier_adoption).',
   'python_worker', 'medium', 'pipeline_step',
   'active', 'frederic',
   'phase2\identite\descendre_correspondance_annonces.py',
   10, 'business',
   'Ajoutee le 13/10/2026 (4j). MEDIUM et non critical parce qu''elle est la SEULE '
   'des 9 a porter -FailOnError : son echec TUE le run, donc l''alarme du run entier '
   'sonne deja. La mettre en critical ferait sonner deux fois pour un seul fait.'),

  ('phase2.rattrapage_photos',
   'Rattrapage des photos (CDN)',
   'Rapatrie les photos manquantes depuis le CDN, hors quota Hektor. Non bloquante '
   'et plafonnee.',
   'node_script', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'Console\rattrapage_photos.js',
   10, 'business',
   'Ajoutee le 13/10/2026 (4j). Seuil large (50 h) : confort avec rattrapage.'),

  ('phase2.derives_photos',
   'Derives des photos (coffre public)',
   'Fabrique les vignettes et derives dans le coffre public.',
   'node_script', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'Console\generer_derives_photos.js',
   10, 'business',
   'Ajoutee le 13/10/2026 (4j). Seuil large (50 h) : confort.'),

  ('phase2.sonde_photos',
   'Sonde des photos manquantes',
   'Regarde si Hektor porte des photos que nous n''avons pas. Elle n''ecrit rien du '
   'cote de Hektor.',
   'node_script', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'Console\sonde_photos_manquantes.js',
   10, 'business',
   'Ajoutee le 13/10/2026 (4j). Seuil large (50 h) : elle ne fait que regarder.'),

  ('phase1.archived_details',
   'Fiches detail des annonces archivees',
   'Va chercher chez Hektor le detail des annonces archivees. Etape optionnelle : '
   'si Hektor refuse, le run continue -- ce n''est qu''un enrichissement.',
   'python_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'sync_archived_annonce_details.py',
   30, 'business',
   'Ajoutee le 13/10/2026 (4j). Entree dans le run le 09/10. Seuil large (50 h) '
   'parce qu''elle est la SEULE des 9 sous condition (-SkipArchivedDetails et '
   '-ArchivedDetailLimit).'),

  -- ---------------------------------------------------------------------
  -- ② LES 14 QUI N'ENVOIENT AUCUNE CLE -- toutes en `medium` (observation)
  --    Elles ne seront suivies qu'une fois le run modifie pour envoyer leur nom.
  -- ---------------------------------------------------------------------
  ('hektor.drafts_sweep',
   'Panier brouillon : etat isDraft',
   'Rafraichit l''etat isDraft des annonces (GraphQL Console, lecture seule) dans '
   'hektor_annonce_draft_state.',
   'python_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'phase2\sync\sync_hektor_drafts.py',
   15, 'business',
   'Ajoutee le 13/10/2026 (4j). Seuil large (50 h) : a DEJA echoue les 17 et 18/09 '
   '(session Hektor expiree), en silence.'),

  ('hektor.immo_pro',
   'Bloc commercial immo pro (actives)',
   'Descend le bloc commercial immo pro des annonces actives. Arret immediat sur '
   '403 : c''est l''insistance qui avait aggrave le bannissement du 26/08.',
   'python_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'phase2\sync\sync_hektor_immo_pro.py',
   20, 'business',
   'Ajoutee le 13/10/2026 (4j). A DEJA echoue les 17 et 18/09, en silence.'),

  ('hektor.immo_pro_archivees',
   'Bloc commercial immo pro (archivees)',
   'La meme chose pour les annonces archivees.',
   'python_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'phase2\sync\sync_hektor_immo_pro.py',
   30, 'business',
   'Ajoutee le 13/10/2026 (4j). A DEJA echoue les 17 et 18/09, en silence.'),

  ('hektor.chauffage_delta',
   'Chauffage des fiches (delta)',
   'Lit le chauffage des fiches chez Hektor, 50 par nuit, avec un rattrapage '
   'automatique a 30 jours.',
   'python_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'phase2\sync\sync_hektor_chauffages.py',
   15, 'business',
   'Ajoutee le 13/10/2026 (4j). ⭐ LE RUN RECLAMAIT CET AJOUT NOIR SUR BLANC (l. 735 : '
   '« a ajouter au registre pour rendre l''echec visible dans l''ecran Sante »). '
   'C''est l''etape qui a le plus echoue en silence : 5 nuits (18, 27/09, 01, 05, 09/10).'),

  ('contacts.champs_manquants',
   'Champs manquants des contacts (delta)',
   'Va chercher naissance, lieu et situation matrimoniale : Hektor ne les rend pas '
   'par l''API.',
   'python_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'phase2\sync\sync_console_contact_missing.py',
   20, 'business',
   'Ajoutee le 13/10/2026 (4j). Sous condition (-SkipContactMissing). A echoue le '
   '18/09, en silence.'),

  ('phase2.magasin_mandat',
   'Magasin des champs de mandat',
   'Tient le magasin des observations de champs de mandat (ce que l''app sait, ce '
   'que Hektor sait).',
   'python_worker', 'medium', 'pipeline_step',
   'active', 'frederic',
   'phase2\identite\magasin_mandat_app.py',
   10, 'business',
   'Ajoutee le 13/10/2026 (4j). Inconditionnelle, 0 echec sur 46 journaux.'),

  ('phase2.contrat_mandat',
   'Applicateur du contrat de mandat',
   'Applique la regle « l''app gagne quand elle a quelque chose a dire » aux champs '
   'de mandat. ⚠ AUJOURD''HUI ELLE NE FAIT RIEN, et c''est VOULU : cette regle '
   'protege les 94 clotures que Hektor porte encore.',
   'python_worker', 'medium', 'pipeline_step',
   'active', 'frederic',
   'phase2\identite\appliquer_contrat_mandat.py',
   10, 'business',
   'Ajoutee le 13/10/2026 (4j). Inscrite BIEN QU''ELLE SOIT SANS EFFET aujourd''hui : '
   'une etape qui ne fait rien reussit, donc ca ne coute aucune alarme -- et elle sera '
   'couverte le jour ou elle fera quelque chose.'),

  ('phase2.contacts_layer_passe2',
   'Couche contacts, seconde passe',
   'Rejoue le build de la couche contacts APRES le registre et AVANT le push, pour '
   'que les contacts neufs ne changent pas d''identite le lendemain en laissant '
   'derriere eux ce que l''app leur a accroche (67 rapprochements le 24/09).',
   'python_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'phase2\contacts\build_contacts_layer.py',
   20, 'business',
   'Ajoutee le 13/10/2026 (4j). Seuil large (50 h) : non bloquante, 1 seul essai, et '
   'elle s''arrete aussitot s''il n''y a aucun contact neuf.'),

  ('phase2.doublure_affaire_ledger',
   'Doublure du ledger d''affaires',
   'Fait descendre app_affaire_ledger (offres, compromis, ventes) dans la copie '
   'locale, AVANT le push du registre qui lit les affaires disparues.',
   'python_worker', 'medium', 'pipeline_step',
   'active', 'frederic',
   'phase2\sync\pull_from_supabase.py',
   15, 'business',
   'Ajoutee le 13/10/2026 (4j). Inconditionnelle, 0 echec sur 46 journaux.'),

  ('phase2.registre_relations',
   'Registre des liens (app_relation)',
   'Reconstruit et pousse le registre des liens.',
   'python_worker', 'medium', 'pipeline_step',
   'active', 'frederic',
   'phase2\sync\relation_ledger.py',
   20, 'business',
   'Ajoutee le 13/10/2026 (4j). ⚠ ELLE A DEJA DISPARU UNE NUIT ENTIERE, EN SILENCE : '
   'le 01/10, un chemin casse (« can''t open file ...sync<CR>elation_ledger.py ») l''a '
   'empechee de demarrer, le run a ecrit « pipeline continues » et a conclu exit 0. '
   'Reparee seule le 02/10. Reste en MEDIUM pour l''observation : promotion en critical '
   'a revoir dans un mois, mesures en main.'),

  ('phase2.registre_mandats',
   'Registre des mandats (app_mandat)',
   'Reconstruit et pousse le registre des mandats.',
   'python_worker', 'medium', 'pipeline_step',
   'active', 'frederic',
   'phase2\sync\mandat_ledger.py',
   20, 'business',
   'Ajoutee le 13/10/2026 (4j). Inconditionnelle, 0 echec sur 46 journaux.'),

  ('phase2.magasin_affaire',
   'Magasin des champs d''affaire',
   'Le magasin des observations de champs d''affaire.',
   'python_worker', 'medium', 'pipeline_step',
   'active', 'frederic',
   'phase2\identite\magasin_affaire_app.py',
   10, 'business',
   'Ajoutee le 13/10/2026 (4j). Inconditionnelle, 0 echec sur 46 journaux.'),

  ('phase2.contrat_affaire',
   'Applicateur du contrat d''affaire',
   'Applique la regle « l''app gagne quand elle a quelque chose a dire » aux champs '
   'd''affaire.',
   'python_worker', 'medium', 'pipeline_step',
   'active', 'frederic',
   'phase2\identite\appliquer_contrat_affaire.py',
   10, 'business',
   'Ajoutee le 13/10/2026 (4j). Meme raisonnement que l''applicateur de mandat.'),

  ('phase2.carnet_annonce',
   'Carnet des champs d''annonce',
   'Tient le carnet des champs d''annonce dont l''app est maitresse.',
   'python_worker', 'medium', 'pipeline_step',
   'active', 'frederic',
   'phase2\identite\magasin_annonce_app.py',
   10, 'business',
   'Ajoutee le 13/10/2026 (4j). Inconditionnelle, 0 echec sur 46 journaux.')

on conflict (worker_key) do nothing;

-- (notify retire : inutile dans une repetition annulee)

insert into _rep_4j
select 'apres_patch',
       (select count(*) from public.app_worker_registry),
       (select count(*) from public.app_worker_registry where criticality = 'critical' and status = 'active'),
       (select count(*) from (values ('phase2.adresses_photos'),
   ('phase2.correspondance_identite'),
   ('phase2.doublure_relation'),
   ('phase2.doublure_mandat'),
   ('phase2.correspondance_annonces'),
   ('phase2.rattrapage_photos'),
   ('phase2.derives_photos'),
   ('phase2.sonde_photos'),
   ('phase1.archived_details'),
   ('hektor.drafts_sweep'),
   ('hektor.immo_pro'),
   ('hektor.immo_pro_archivees'),
   ('hektor.chauffage_delta'),
   ('contacts.champs_manquants'),
   ('phase2.magasin_mandat'),
   ('phase2.contrat_mandat'),
   ('phase2.contacts_layer_passe2'),
   ('phase2.doublure_affaire_ledger'),
   ('phase2.registre_relations'),
   ('phase2.registre_mandats'),
   ('phase2.magasin_affaire'),
   ('phase2.contrat_affaire'),
   ('phase2.carnet_annonce')) as v(cle)
          where not exists (select 1 from public.app_worker_registry r where r.worker_key = v.cle));

-- ---------------------------------------------------------------------
-- LE VRAI INVERSE (decoupe dans ..._INVERSE.sql)
-- ---------------------------------------------------------------------
delete from public.app_worker_registry
where worker_key in (
  -- les 9 dont le run envoyait deja le nom
  'phase2.adresses_photos',
  'phase2.correspondance_identite',
  'phase2.doublure_relation',
  'phase2.doublure_mandat',
  'phase2.correspondance_annonces',
  'phase2.rattrapage_photos',
  'phase2.derives_photos',
  'phase2.sonde_photos',
  'phase1.archived_details',
  -- les 14 qui n'envoyaient aucune cle
  'hektor.drafts_sweep',
  'hektor.immo_pro',
  'hektor.immo_pro_archivees',
  'hektor.chauffage_delta',
  'contacts.champs_manquants',
  'phase2.magasin_mandat',
  'phase2.contrat_mandat',
  'phase2.contacts_layer_passe2',
  'phase2.doublure_affaire_ledger',
  'phase2.registre_relations',
  'phase2.registre_mandats',
  'phase2.magasin_affaire',
  'phase2.contrat_affaire',
  'phase2.carnet_annonce'
);

-- (notify retire : inutile dans une repetition annulee)

insert into _rep_4j
select 'apres_inverse',
       (select count(*) from public.app_worker_registry),
       (select count(*) from public.app_worker_registry where criticality = 'critical' and status = 'active'),
       (select count(*) from (values ('phase2.adresses_photos'),
   ('phase2.correspondance_identite'),
   ('phase2.doublure_relation'),
   ('phase2.doublure_mandat'),
   ('phase2.correspondance_annonces'),
   ('phase2.rattrapage_photos'),
   ('phase2.derives_photos'),
   ('phase2.sonde_photos'),
   ('phase1.archived_details'),
   ('hektor.drafts_sweep'),
   ('hektor.immo_pro'),
   ('hektor.immo_pro_archivees'),
   ('hektor.chauffage_delta'),
   ('contacts.champs_manquants'),
   ('phase2.magasin_mandat'),
   ('phase2.contrat_mandat'),
   ('phase2.contacts_layer_passe2'),
   ('phase2.doublure_affaire_ledger'),
   ('phase2.registre_relations'),
   ('phase2.registre_mandats'),
   ('phase2.magasin_affaire'),
   ('phase2.contrat_affaire'),
   ('phase2.carnet_annonce')) as v(cle)
          where not exists (select 1 from public.app_worker_registry r where r.worker_key = v.cle));

-- ---------------------------------------------------------------------
-- L'ERREUR VOLONTAIRE : elle annule TOUT ce qui precede.
-- ---------------------------------------------------------------------
DO $rep$
DECLARE
  a record; b record; c record;
BEGIN
  SELECT * INTO a FROM _rep_4j WHERE etape = 'avant';
  SELECT * INTO b FROM _rep_4j WHERE etape = 'apres_patch';
  SELECT * INTO c FROM _rep_4j WHERE etape = 'apres_inverse';
  RAISE EXCEPTION
    'ESSAI ANNULE -- 4j : lignes % -> % (+%) -> % (ecart %) ; critical % -> % -> % ; cles des 23 absentes du registre % -> % -> %',
    a.lignes, b.lignes, b.lignes - a.lignes, c.lignes, c.lignes - a.lignes,
    a.critical, b.critical, c.critical,
    a.orphelines, b.orphelines, c.orphelines;
END
$rep$;

COMMIT;  -- jamais atteint : l'erreur ci-dessus annule la transaction
