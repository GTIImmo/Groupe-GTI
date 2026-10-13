-- =====================================================================
-- CHANTIER ④ -- POINT 4j : LES BATTEMENTS QUE PERSONNE NE LIT
-- Date : 2026-10-13 · Detail : notice/CHANTIER_4_ECHECS_SILENCIEUX_2026-10-09.md
--
-- D'OU CA VIENT. La session du chantier ③ a bute sur le defaut en inscrivant SA
-- cle (phase2.repose_cloture_mandat, posee le 13/10 a 14:08), l'a signale sans le
-- corriger -- ce n'etait pas son perimetre -- et l'a renvoye ici.
--
-- LE DEFAUT, MESURE LE 13/10.
--   monitoring/heartbeat.py ecrit en PATCH FILTRE sur app_worker_registry : si la
--   cle n'y a AUCUNE ligne, il touche 0 ligne, recoit 204, et le code
--   `200 <= status < 300` compte UN SUCCES ;
--   check_gti_health.check_worker_heartbeat (l. 1276) ENUMERE la table : une cle
--   sans ligne n'est jamais regardee.
-- ➡ UNE CLE NON ENREGISTREE = UN BATTEMENT QUI PART DANS LE VIDE, EN SILENCE.
--
-- LE RELEVE COMPLET DU RUN DE NUIT (58 etapes) :
--   41 envoient une cle (40 distinctes + pipeline.full, envoyee a part a la fin)
--      -> 9 ecrivent dans le vide
--   17 n'envoient AUCUNE cle
--      ->  3 n'en ont pas BESOIN : elles passent par Invoke-Step, qui TUE le run
--          (`throw`, l. 17) -- leur echec declenche deja l'alarme du run entier
--      -> 14 sont vraiment muettes
--   (+ 3 appels directs hors du mecanisme des etapes : NON MESURES)
--
-- ⚠ ET LE SILENCE N'EST PAS THEORIQUE : 6 nuits sur 46 journaux portent au moins
--   un echec dont personne n'a jamais rien su.
--     17/09 et 18/09  Hektor muet : brouillons, immo pro, immo pro archivees
--     18/09            + les champs manquants
--     18, 27/09, 01, 05, 09/10   le chauffage (5 nuits)
--     01/10            LE REGISTRE DES LIENS n'a pas tourne DU TOUT --
--                      « can't open file ...phase2\sync<CR>elation_ledger.py »
--                      -> WARN, puis « pipeline continues ». Repare seul le 02/10.
--   ⚠ Je n'affirme PAS que ca ait cause l'incident du carnet des liens du
--     09->10/10 : ce n'est pas mesure, et la proximite des dates ne prouve rien.
--
-- CE QUE FAIT CE PATCH : **RIEN QUE 23 LIGNES DE CONFIGURATION.** Aucune fonction,
-- aucune vue, aucune donnee metier. Le run envoie DEJA les 9 premiers noms ; les
-- 14 autres recoivent leur `-WorkerKey` dans un changement de run separe.
--
-- LA GRAVITE, CHOISIE PAR FREDERIC (option B du 13/10) :
--   4 en `critical` -> un e-mail. Ce sont les 4 qui touchent l'identite du parc
--     ou les adresses de toutes les photos.
--   19 en `medium`  -> visibles dans l'ecran Sante, PAS d'e-mail.
--   ⭐ POURQUOI SI PEU DE CRITICAL : la surveillance n'envoie un mail que sur une
--      BASCULE vers critical, et un « retour a la normale » exige ZERO critical
--      (check_gti_health.py:2843). Le 11/10, 3 alarmes coincees l'ont rendue muette
--      pendant des jours. On passe de 12 a 16 critical, pas plus.
--
-- LE SEUIL, DICTE PAR LA MESURE (et non choisi au doigt) :
--   `pipeline_step`          = 28 h -> « elle a manque UNE nuit »
--      pour les etapes inconditionnelles
--   `optional_pipeline_step` = 50 h -> « elle en a manque DEUX »
--      pour les etapes SOUS CONDITION ou qui ont DEJA echoue
--
-- ⚠ CE QUE CE PATCH NE FAIT PAS. Une cle fraichement posee n'a aucun succes : elle
--   tombe dans la liste « jamais vu », qui ne declenche RIEN (le resume ne regarde
--   que les RETARDS, l. 1357). Elle sera donc silencieuse jusqu'a son premier
--   succes -- donc demain matin. Revers connu, signale, non corrige ici : une
--   etape cassee des le premier jour resterait muette pour toujours.
--
-- IDEMPOTENT : `on conflict do nothing`. Le recoller ne fait rien.
-- RETOUR ARRIERE : supabase/patch_4j_battements_invisibles_2026-10-13_INVERSE.sql
-- REPETITION     : supabase/patch_4j_battements_invisibles_2026-10-13_REPETITION.sql
-- =====================================================================

BEGIN;

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

notify pgrst, 'reload schema';

COMMIT;
