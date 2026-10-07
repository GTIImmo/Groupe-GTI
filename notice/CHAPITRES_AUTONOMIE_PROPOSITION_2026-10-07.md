# SYNTHESE

PRINCIPE: VERDICT DU JURY (07/10/2026), puis la règle de la séquence finale.

CE QUE J'AI VÉRIFIÉ AUJOURD'HUI, en lecture seule :
- Console/enqueue_empreinte_lot.js:153 enchaîne bien archive → historical → brouillon. scheduled/run_rattrapage_documents.ps1:75 passe « --limit 2500 ».
- Le débordement a DÉJÀ eu lieu avec les archives. Le 05/10, l'étape « hektor chauffage delta » a été refusée deux fois (logs/scheduled/quotidien_2026-10-05, l.371-426), par require_no_console_jobs (sync_hektor_chauffages.py:263).
- Cette étape tourne vers 06:35 heure de Paris. Deux autres étapes refusent aussi quand un travail console attend : sync_hektor_compromis_console.py:227 (vers 06:50) et sync_console_missing_fields.py:263. La limite dure est donc vers 06:35. Le critère « lot fini avant 05:00 » garde une marge.

COMPARAISON DES TROIS PROPOSITIONS
1) Dépendances techniques. La proposition « technique » est la plus stricte : L10-1 vient avant les gestes, et chaque RPC n'est écrite qu'une fois. « Péremption » et « usage » écrivent G.5 et L10-3 avant L10-1d. C'est permis : l'inventaire prévoit leur reprise par L10-1e et G.5-f. Écart dans « péremption » : L10-6b (ch.15) passe avant G.5 (ch.16), alors que G.5 est un prérequis mesuré de L10-6b.
2) Échéances datées. Les trois mettent G.1-e en tête. Seule « technique » avait vu que le débordement existe déjà ; je l'ai confirmé. « Usage » repousse G.1-b-2 au ch.5, ce qui reste acceptable grâce à la garde G.1-b-1.
3) Risque pour la prod d'aujourd'hui. « Technique » est la meilleure (planchers au ch.5). « Péremption » les met au ch.9. « Usage » ouvre le pilote avant les planchers et relit le parc vivant après l'ouverture du pilote.
4) Preuve par l'usage. « Usage » est la meilleure (pilote vers le 29/10). « Péremption » ouvre le pilote au ch.14. « Technique » l'ouvre au ch.17, après 55 à 85 jours de code : trop tard pour corriger ce que seul l'usage révèle.
5) Clarté pour le développeur. « Technique » et « usage » regroupent les changements du worker par fenêtre de redémarrage. « Péremption » a le chapitre 1 le plus net. « Technique » a des chapitres trop gros (8 tâches au ch.5).
6) Place des décisions de Frédéric. Les trois les mettent dans les prérequis. « Péremption » a la meilleure table « question → chapitre ».

BASE RETENUE : « péremption ». Elle équilibre le mieux les échéances, ce qui périme avec Hektor et un pilote placé AVANT le gros chantier L10-1. Les gestes du pilote portent sur le stock actuel, qui a 100 % de numéros Hektor : L10-1 doit être fini avant la coupure, pas avant le pilote.

GREFFES
- De « technique » :
  - Le ch.1 réunit tout ce qui protège le rattrapage : G.1-e, G.1-b-1, L10-10a, L10-8c, plus la sonde disque.
  - UNE seule fenêtre de redémarrage pour G.1-b-2, G.5-a et A.3-a (on corrige tôt un défaut latent de la prod).
  - Les planchers « Hektor répond vide » passent AVANT le pilote, et la sécurité L10-16 avant toute RPC SECURITY DEFINER.
  - La porte L10-1b est écrite pour accepter aussi le motif « Hektor coupé ».
  - Le report de G.4, avec sa raison.
- De « usage » :
  - Le pilote s'ouvre dès que protection, droits et comptes sont prêts (ch.10). Ensuite, chaque chapitre livre un geste quotidien « chez nous d'abord » que les pilotes utilisent : statuts, fichiers, PDF.
  - Vérifier la règle « le carnet cède quand Hektor confirme » avant d'allumer L10-3.
  - Une règle provisoire pour L10-16c tant que Q6 n'est pas tranchée.
  - La branche brouillon de loadDossier est dessinée pour recevoir l'écriture plus tard.
  - Vérifier R-1 à R-5 en entrant au ch.8.
  - Le trou « Storage non sauvegardé ».
- De « péremption » :
  - Les captures de ce qui ne vit que chez Hektor passent avant le bloc L10-1.
  - Aucun préavis avant les planchers.
  - L10-8e est coupé en deux : annuaire et vitrine au ch.5, liens RDV au ch.27 avec le jeton stable.
  - Une 1re version du carnet du jour J, écrite tôt.

RÈGLES TENUES PARTOUT
- UNE seule tâche de code à la fois. Le ch.3 (mesures, écrits, gestes humains, sondes SELECT) avance à côté, jamais à la place.
- Chaque chapitre est ré-audité en entrant (CLAUDE.md §0) : l'audit est une carte du 07/10.
- Les changements du worker d'un même chapitre partagent un seul redémarrage : en journée, file documents VIDE. Un travail « running » depuis plus de 30 min passe en erreur, et son annonce est exclue à vie du rattrapage.
- Tout ce qui pourrait inverser le courant reste derrière un réglage éteint tant que les commerciaux saisissent dans Hektor (décision du 21/09). Un geste de l'app part aussi chez Hektor. Une saisie faite ENSUITE dans Hektor gagne.
- Feu vert selon CLAUDE.md §0 : additif et dormant = j'enchaîne ; code existant, run ou worker = « vas-y » ; prod, Hektor, run, redémarrage, déploiement = accord.

REPORTÉES APRÈS LA COUPURE (à confirmer par Frédéric)
- G.3, purge du cloud. Elle est irréversible et le Storage n'est pas sauvegardé. Elle ne sert pas à vivre sans Hektor : elle ne fait que libérer de la place. Elle vient après une restauration éprouvée (ch.43, L10-9f) et après la fin de la course avec la réindexation.
- G.4, l'état cloud qui suit l'annonce. Tel qu'il est décrit, il agit pendant une synchronisation avec Hektor, qui n'existera plus. Il faut le refaire comme une réaction au geste « restaurer » de l'app (L10-3b). D'ici là, rien n'est perdu : un document local_only se rouvre par « Préparer », qui est dans la liste blanche de L10-6b.
- CONDITIONNELLE : L10-13-c sort de la liste si la question 8 dit que les automatismes CRM de Hektor ne servent pas.
- PEUVENT GLISSER sans perte si le calendrier serre (Frédéric décide) : E.0-bis-e (fusion, ch.39 ; le bouton serait masqué au jour J) et L10-12-b (offre d'achat, ch.31).
Toutes les autres tâches mesurées sont placées avant la coupure.

HORS DE LA LISTE MESURÉE, MAIS EXIGÉS : « 4-suite », la clé des recherches (ch.24, taille non mesurée) ; le registre des relations autonome, avec ses 5 questions (ch.25, taille non mesurée) ; la copie serveur des 35 documents qui n'existent que dans le Storage (ch.6).

VOLUME : environ 145 à 215 jours de code, une tâche à la fois, sans compter les deux chantiers non mesurés. Pilote vers la 2e quinzaine de novembre si les décisions suivent. Coupure réaliste au plus tôt au printemps 2027.

## CH1 — Le rattrapage des documents tient dans la nuit, et ses erreurs se voient
- objectif: Les 8 895 ventes passent sans faire sauter le run de 05:00. Les 508 brouillons ne sont pas exclus pour toujours. Une erreur neuve, un index effacé ou un disque qui se remplit déclenche une alerte.
- taches: G.1-e — calibrer le lot des VENTES (avant le 08/10 à 21:00), G.1-b-1 — garde : pas de périmètre « brouillon » tant que le worker ne sait pas le charger, L10-10a — solder les 15 travaux en erreur, puis alerter sur la HAUSSE et non sur le total, L10-8c — plancher sur l'effacement des index archives / historiques / brouillons dans le push de nuit, L10-10e — surveiller la place disque et les plantages des workers (0xC0000409)
- ordre: 1) G.1-e, AVANT le 08/10 à 21:00. Ajouter dans parseArgs (Console/enqueue_empreinte_lot.js:31-50) une option additive de limite propre au périmètre historical, et la passer par scheduled/run_rattrapage_documents.ps1:75 (aujourd'hui « --limit 2500 »). Tester les arguments hors ligne, puis faire un --dry-run (il ne lit que Supabase). Commit G.1-e.
2) G.1-b-1, dans le même fichier : à la l.153, ne poser « brouillon » que si une variable d'environnement dit que le worker sait le charger. Test hors ligne du choix de périmètre, puis --dry-run. Commit. Les étapes 1 et 2 se livrent ensemble, sans toucher au worker ni redémarrer.
3) L10-10a : dans monitoring/check_gti_health.py:200-207, une règle « nouvelles erreurs depuis le passage précédent ». Ensuite, sur décision, le geste SQL qui solde les 15 erreurs. Avant tout rejeu du unlink, vérifier EN LECTURE si Hektor a reçu le retrait du mandant.
4) L10-8c : une garde copiée sur le frein de la l.1422 de push_upgrade_to_supabase.py, appliquée aux effacements des l.1630-1652. L'éprouver en exécutant LE vrai code sur une copie de phase2.sqlite dont la source des archives est vidée.
5) L10-10e : sentinelle disque (shutil.disk_usage) et compteur de redémarrages des workers sur 7 jours.
6) Observer 5 nuits de ventes tout en avançant les chapitres suivants. Régler la taille du lot après la 1re nuit mesurée.
- prerequis: Aucun chapitre. | Décision de Frédéric AVANT le 08/10 à 21:00 : la taille du lot des ventes. Proposition : 400 la 1re nuit, puis 400 à 600 selon la durée mesurée. Une vente porte 24,3 documents, une archive 2,7. | Décision : que faire des 15 travaux en erreur (14 refresh_console_data du 01 au 05/10 sur 63156 et 63158, 1 unlink_hektor_mandant) ? | Décision : le seuil du plancher L10-8c (proposition : 500 lignes ou 5 % de l'index), et garder ou non -AllowStaleSupabaseDeletes (run_quotidien.ps1:39). | Décision : le seuil disque (proposition : critique sous 100 Go ; 444 Go libres, +137 à +273 Go attendus pour les ventes).
- feu vert: « vas-y » pour G.1-e, G.1-b-1, L10-10a (la règle), L10-8c et L10-10e : code existant, script de tâche planifiée, run de nuit, moniteur. Aucun worker n'est touché, rien n'est redémarré. ACCORD obligatoire pour solder les 15 erreurs (écriture en prod). Filet si G.1-e n'est pas en service le 08/10 à 21:00 : désactiver la tâche « GTI Rattrapage Documents » pour une nuit (accord). | perime: True | taille: 2 à 3,5 j, dont 0,5 j avant le 08/10 à 21:00 ; puis 5 nuits d'observation en fond
- fin: Le 08/10 à 21:00, le lot des ventes est posé avec la taille fixée, et non 2 500.
Pendant 5 nuits de ventes :
- chaque lot finit avant 05:00 heure de Paris (max(finished_at) < 03:00 UTC jusqu'au 25/10, < 04:00 UTC après le passage à l'heure d'hiver) ;
- aucun refus « file_occupee » ;
- « hektor chauffage delta » est DONE chaque matin.
Avec archive et historique simulés vides, le --dry-run en --scope auto ne retient aucun brouillon.
0 travail en erreur antérieur au correctif. Une erreur injectée donne UN mail au passage suivant, et aucun au passage d'après.
Sur copie, un index d'archives vidé fait refuser l'étape, avec 0 DELETE. Une nuit réelle garde les mêmes compteurs archive_index_deleted.
La sentinelle disque et le compteur de redémarrages ont une valeur dans l'écran Santé.
- verif: Journaux logs/scheduled/rattrapage_documents_*.log et quotidien_*.log (lignes START/DONE de « hektor chauffage delta », vers 06:35 heure de Paris). Requête : SELECT status, payload_json->>'scope', count(*), max(finished_at) FROM app_console_job WHERE job_type='sync_console_documents' GROUP BY 1,2. Tests hors ligne des arguments et du choix de périmètre. Journal du moniteur sur une configuration d'essai. Vrai push_upgrade exécuté sur copie.
- gestes Frederic: Fixer la taille du lot des ventes aujourd'hui ou demain matin, et dire « vas-y ». | Trancher les 15 erreurs, puis accorder le geste SQL. | Fixer le seuil du plancher et le seuil disque. | Le 09/10 au matin : relire avec moi le journal du rattrapage et l'étape chauffage.

## CH2 — Une seule fenêtre de redémarrage du worker : brouillons, garde de purge, registre des mandats
- objectif: Les 508 brouillons peuvent être rattrapés. Une ligne de document née dans l'app ne peut plus être purgée. Le premier numéro de mandat demandé depuis l'app ne fera pas échouer le push de nuit.
- taches: G.1-b-2 — loadDossier sait retrouver un brouillon (pour les seuls travaux de lecture), G.5-a — la purge des documents « supprimés dans Hektor » épargne les lignes nées dans l'app, A.3-a — réparer les 2 défauts dormants de l'étape D du registre des mandats (doublure non rafraîchie, date JJ-MM-AAAA)
- ordre: 1) G.1-b-2. Ajouter une 4e recherche dans loadDossier (console_job_worker.js:1877-1929), APRÈS les 3 existantes, dans app_brouillon_annonce_index_current par app_brouillon_id ou par n° Hektor. La réserver à READ_ONLY_ARCHIVE_JOB_TYPES (l.128-133). La dessiner pour qu'une future branche « écriture » (E.0-bis-f, ch.38) s'y ajoute sans la réécrire. Test node hors ligne.
2) G.5-a. Dans pruneDeletedDocuments (l.5323-5355), ignorer les lignes dont hektor_document_id est NULL ou dont envoi_hektor_statut n'est pas NULL. Test hors ligne.
3) A.3-a :
- écrire la date en ISO dans le worker (l.15277-15285 et l.12989) ;
- ajouter une étape non bloquante « pull_from_supabase.py --table app_mandat » avant l'étape registre (run_full_pipeline.ps1:946, patron l.923-926) ;
- essai sur copie : mandat_ledger --refresh sans --push.
4) UN redémarrage des 4 services, un après-midi, file documents VIDE : après la fin du lot de nuit, avant 21:00.
5) Essai réel de 3 brouillons posés à la main.
6) S'ils finissent « done » avec une empreinte, lever le filet G.1-b-1 (variable d'environnement).
La preuve réelle d'A.3-a, avec un vrai numéro demandé chez Hektor, peut attendre le pilote (ch.10).
- prerequis: Chapitre 1 (G.1-e et G.1-b-1 en service). | Décision : les brouillons valent-ils le rattrapage ? 185 sont sans date, 323 de 2026, 1 seul a un numéro de mandat. Si non, G.1-b-2 sort du chapitre et la garde reste : E.0-bis-f en aura besoin plus tard. | « vas-y » pour modifier le worker et le run. | Accord pour redémarrer les 4 services en journée, file documents vide.
- feu vert: « vas-y » pour le worker et le run. ACCORD obligatoire pour : le redémarrage des 4 services, l'essai réel des 3 brouillons (il lit Hektor) et la preuve A.3-a sur l'annonce d'essai 62966 (elle écrit chez Hektor). | perime: True | taille: 1,25 à 2 j. À finir avant la fin des ventes du rattrapage pour ne perdre aucune nuit : vers le 22/10 à 600 par nuit, vers le 31/10 à 400.
- fin: 3 travaux brouillon posés à la main sont « done » avec une empreinte.
Test hors ligne : une ligne sans hektor_document_id et avec un envoi « echec » survit à pruneDeletedDocuments, et une ligne Hektor obsolète est toujours purgée.
Sur copie : une ligne de mandat née dans l'app (id ≥ 1 000 000) est adoptée (adoptes_au_depart ≥ 1), date_debut est en AAAA-MM-JJ, et le push de app_mandat réussit deux nuits de suite.
0 travail passé en erreur à cause du redémarrage.
- verif: Tests node hors ligne. Requête : nombre de brouillons de app_brouillon_annonce_index_current qui ont une empreinte dans app_console_document_fingerprint (par hektor_annonce_id::text). Journal du worker après le redémarrage. Comptes de app_mandat, local contre cloud, après 2 nuits.
- gestes Frederic: Décider si les brouillons valent le rattrapage. | Dire « vas-y » et accorder la fenêtre de redémarrage (un après-midi, file vide). | Accorder l'essai des 3 brouillons.

## CH3 — EN PARALLÈLE des chapitres 1 à 10 : mesurer et écrire ce qui périme, sans code de production
- objectif: Pendant que Hektor répond : savoir par où arrivent les leads, où vit le consentement RGPD, si l'agenda se lit, comment Hektor fabrique un ménage, et quelles signatures sont ouvertes. Écrire aussi l'ordre d'extinction et le classement du run, sans lesquels aucun préavis n'est sûr.
- taches: L10-6a — l'ordre d'extinction et l'inventaire de tout ce qui parle à Hektor (document), E.4a — 1re version du carnet du jour J (réécrite au ch.45), L10-7a — classer les 54 étapes du run : parle à Hektor / lit le miroir / indépendante, A.5-a — leads : établir le canal réel de chaque portail depuis le 01/02 (mesure), L10-13-a — ce que Hektor envoie aux clients, et où vit l'état RGPD (mesure ; la descente éventuelle du consentement est codée au ch.16), E.1b — mesurer si l'API Hektor expose l'agenda des visites, pour que Frédéric tranche (l'import éventuel est au ch.16), C.9-couple-a — le ménage d'essai créé par Frédéric, puis les deux sondes et le rapport, E.1c — une sonde SELECT des procédures de signature ouvertes (50 aujourd'hui), relue chaque semaine
- ordre: Ces tâches avancent à côté de la tâche de code en cours, jamais à sa place (CLAUDE.md §0 : les audits peuvent tourner en parallèle). Ordre conseillé :
1) L10-6a, d'abord, parce qu'il conditionne le préavis. 3 tâches, 4 services, 4 crons, 30 fonctions, le backend Render ; vérifier aussi GTI Relances Email (B8).
2) E.4a, 1re version.
3) L10-7a : chaque ligne justifiée par fichier:ligne.
4) A.5-a : lecture du module Leads de Hektor et du centre de leads LBC. Ne JAMAIS ouvrir le détail d'un lead : il serait marqué lu.
5) L10-13-a : lecture d'une fiche Hektor connue, comparée au miroir et à Supabase.
6) E.1b : mesure de l'API, puis décision de Frédéric (question 2).
7) C.9-couple-a, dès que Frédéric a fait le geste : phase2/checks/sonde_paire_de_menage.py et Console/sonde_conjoint.js, puis le rapport.
8) E.1c : la sonde, relue chaque semaine jusqu'au jour J.
Si A.5-a montre que l'historique des leads ne vit que dans le module Leads de Hektor, son export brut remonte au ch.16.
- prerequis: Aucun chapitre. | Question 8 : demander aux négociateurs où ils voient un lead aujourd'hui, et s'ils utilisent SMS, tâches, envoi de fiches, automatismes. | Choix de la cible du ménage d'essai (mémoire : GONZALEZ / Firminy) et accord d'écriture chez Hektor. | Accords pour LIRE chez Hektor (module Leads, fiche contact, agenda) et dans le centre de leads Leboncoin.
- feu vert: J'enchaîne sans attendre pour les documents, le tableau et la sonde E.1c : c'est additif et en lecture. ACCORD obligatoire pour toute lecture chez Hektor ou Leboncoin, et pour l'écriture chez Hektor du ménage d'essai. | perime: True | taille: 3 à 5 j, étalés sur les chapitres 1 à 10
- fin: - L10-6a : un document rangé dans notice/ et relié au plan, chaque élément avec son ordre d'arrêt et son retour arrière.
- E.4a : la v1 du carnet est datée.
- L10-7a : un tableau des 54 étapes, avec leur classe, leur source et leur sort après la coupure.
- A.5-a : le canal réel est écrit pour chaque portail, avec un exemple daté d'octobre 2026, et le nombre de leads du module Hektor depuis le 01/02 est connu.
- L10-13-a : chaque service aux clients est déclaré utilisé ou non, et l'état RGPD est localisé (ou déclaré inexistant).
- E.1b : la décision est écrite.
- C.9-couple-a : le rapport dit combien de fiches Hektor crée, le sens de refCouple et les champs de la 2e fiche.
- E.1c : la sonde rend la liste datée des procédures ouvertes.
- verif: Relecture par Frédéric. Chaque ligne de L10-6a confrontée à Get-ScheduledTask, Get-Service et cron.job. Le rapport C.9 comparé à la paire réelle 10871/10872. Un lead connu (date, portail, bien) retrouvé dans le canal identifié.
- gestes Frederic: Créer le ménage d'essai depuis l'app (environ 1 h). | Poser la question 8 aux négociateurs. | Accorder les lectures chez Hektor et chez Leboncoin. | Trancher la question 2 (agenda) après la mesure. | Relire l'ordre d'extinction : AUCUN préavis avant cette relecture.

## CH4 — Relire le parc vivant chaque nuit (G.2 puis G.6), et rapatrier les pièces de fin de vie
- objectif: Les documents des 724 biens en vente sont relus chaque nuit, les estimations en rotation lente. Les signatures abouties redeviennent visibles. Les pièces des biens vendus depuis août et les 230 fichiers manquants sont rapatriés.
- taches: L10-10c — inscrire au registre les 7 heartbeats qui partent dans le vide, plus la clé de G.2, G.2 — détection plafonnée du parc vivant (en vente, rotation des estimations, suivi des signatures, sorties récentes), G.6 — geste de Frédéric : allumer -EnqueueConsoleDocuments (scheduled/run_quotidien.ps1:39), G.1-c — le stock des annonces lues vivantes en août puis vendues (le flux est dans G.2), G.1-d — les 230 documents indexés sans fichier
- ordre: 1) L10-10c : insérer les 8 clés dans app_worker_registry (accord).
2) G.2 dans Console/enqueue_console_sync_jobs.js :
- INDEX_SOURCES (l.102) : un périmètre « en vente » et une rotation des estimations par checked_at le plus ancien ;
- runDetection (l.373) : les sorties récentes du parc ;
- curseur trié dans loadFingerprints (l.323) et dans loadSignatureFollowSet (l.341), avec un filtre serveur pour les 75 signatures ;
- l'étape de run_full_pipeline.ps1:1308-1333 passe en Invoke-OptionalStepWithRetry -Exe node, avec la WorkerKey inscrite ;
- tests hors ligne avec fetch simulé, sur le patron de test_frein_detection.js.
⚠ Le --dry-run du mode --detect LIT Hektor.
3) Un passage réel à plafond bas (accord), en mesurant la durée et le nombre de requêtes.
4) Le geste G.6.
5) Pendant les 3 nuits de surveillance (pas de code), le développeur commence le ch.5.
6) G.1-c : recompter la liste (97 remesurées, 111 selon l'audit), créer le périmètre additif « fin-de-vie » dans enqueue_empreinte_lot.js, faire un --dry-run, puis poser le lot en journée (fini avant 21:00) ou une nuit de petit lot.
7) G.1-d, après 3 nuits de G.6 : la requête de suivi, 3 travaux ciblés sur les annonces qui ont déjà une empreinte, et la recherche de la cause des cas récents (jusqu'au 05/10).
- prerequis: Chapitre 1 (G.1-e : sans lui, la détection lirait Hektor en même temps qu'un lot de 20 à 36 h). | Chapitre 2 (G.5-a doit précéder toute synchronisation relancée par G.6). | Décision : la taille de la rotation des 12 739 estimations. | Décision : où tourne la détection : dans le run de 05:00 (25 à 30 min de plus, alors que le run finit déjà à 07:20) ou dans une tâche à part. | Décision : inclure les sorties récentes. | Décision : allumer G.6 AVANT la fin du rattrapage, ce qui inverse la règle D.0-g du 25/09. Fait mesuré : environ 18 000 requêtes par nuit depuis 12 nuits, 0 bannissement.
- feu vert: « vas-y » pour G.2 et G.1-c (code existant, run). ACCORD obligatoire pour : L10-10c (insertion en prod), tout passage réel de G.2 (il lit Hektor), le geste G.6, le lot G.1-c et les travaux ciblés de G.1-d. | perime: True | taille: 2,5 à 3,5 j de code, puis 3 nuits de surveillance
- fin: Tests hors ligne : le périmètre vaut 724 + N estimations + les annonces en suivi de signature, et le curseur ne perd ni ne double aucune des 47 146 empreintes.
Une session Hektor morte n'arrête plus le run : Matterport, liens RDV et vitrine passent.
Après 3 nuits :
- les biens en vente sans empreinte passent de 132 à 0 ;
- les 724 ont un checked_at de moins de 48 h ;
- aucun travail G.6 n'est encore en file à 21:00 ;
- aucun refus du rattrapage n'est dû à G.6.
Les 8 clés ont un last_run_at de la nuit.
G.1-c : chaque annonce de la liste a une empreinte postérieure à sa sortie du parc, et ses compromis ou actes sont dans app_console_document.
G.1-d : la requête des documents local_only sans fichier rend 0, ou chaque reste est expliqué.
- verif: Tests node hors ligne. Requête app_console_document_fingerprint × app_dossier_current (archive='0', biens en vente). Journal du run : « DONE enqueue console documents » et ses statistiques JSON (balayees, changees, sans_empreinte, suivi_signature). Requêtes G.1-c et G.1-d avant et après (230 documents sur 55 annonces le 07/10).
- gestes Frederic: Trancher la rotation, le lieu d'exécution et les sorties récentes. | Accepter G.6 avant la fin du rattrapage, puis faire le geste G.6 (ou me donner l'accord). | Accorder L10-10c, le passage réel à plafond bas, le lot G.1-c et les travaux G.1-d.

## CH5 — Les planchers « Hektor répond vide » : miroir, registres, annuaire, vitrine
- objectif: Une réponse vide ou tronquée de Hektor, sur un hoquet ou parce que le compte est résilié, ne vide plus le miroir, ne masque plus les affaires ni les mandants, n'écrase plus un détail bon, ne vide plus l'annuaire et ne publie pas une vitrine vide. C'est la condition de tout préavis.
- taches: L10-8a — plancher dans sync_raw, avant l'effacement des pages brutes, L10-8b — plancher dans normalize_source (9 tables et hektor_mandat), L10-8d — planchers des registres des affaires et des relations, L10-8f — valider la forme avant d'écrire (détail d'annonce, cache console), L10-8e, partie annuaire et vitrine — push_hektor_directory_to_supabase.py et export_project_vitrine.py (la partie liens RDV va au ch.27, avec le jeton stable : même fonction)
- ordre: 1) L10-8a. Comparer last_page aux pages attendues (metadata.total, ou pages de la veille) AVANT le prune de sync_raw.py:1648. D'abord quelques nuits en mode « journal seulement » derrière une variable d'environnement, puis le refus.
2) L10-8b (normalize_source.py:658-726).
3) L10-8d (affaire_ledger.py:868-918, relation_ledger.py:463-476), avec des seuils calibrés sur les 30 dernières nuits. Il passe AVANT L10-1, qui réécrira ces clés.
4) L10-8f (sync_raw, sync_console_missing_fields.py:330-370).
5) L10-8e : d'abord l'annuaire (l.412-430, étape bloquante), puis la vitrine (refus sous N biens).
Chaque garde est éprouvée en exécutant LE vrai code sur une copie (data/hektor.sqlite ou phase2.sqlite), avec un faux client qui rend {data:[]} puis {data:{}}. Jamais sur une imitation de sa logique.
- prerequis: Chapitre 1 (L10-8c donne le patron). | Décisions sur les seuils. Propositions : sync_raw comparé à metadata.total ; normalize_source refuse sous 50 % des annonces connues et toujours sur un périmètre vide ; les registres refusent au-delà de 5 % en une nuit ; la vitrine refuse sous N biens. | Accepter qu'un refus arrête une étape bloquante (sync_raw, normalize_source, annuaire) pour une nuit : l'app a un jour de retard, rien n'est perdu.
- feu vert: « vas-y » : code existant du run de nuit. Aucune écriture en base, aucun redémarrage. | perime: False | taille: 3 à 4 j, plus quelques nuits en mode journal
- fin: Sur copie, avec le vrai code :
- une page 1 vide ou de forme objet laisse intactes les 3 064 pages brutes et sort en code ≠ 0 avant normalize_source ;
- un périmètre vide ou sous le seuil donne 0 DELETE ;
- un miroir vidé donne 0 UPDATE dans les registres, et un heartbeat en erreur ;
- une charge malformée n'écrase aucune ligne ;
- une source vide ne retire ni négociateur ni agence, et ne produit pas de vitrine vide.
Ensuite, 3 nuits réelles passent sans refus, avec les mêmes compteurs que la veille.
- verif: Comptes des tables avant et après, sur les copies. Vitrine produite sans --push-github. Journaux des 3 premières nuits réelles.
- gestes Frederic: Fixer les seuils. | Accepter qu'un refus arrête une nuit. | Ne donner AUCUN préavis avant la fin de ce chapitre et la relecture de L10-6a.

## CH6 — Sauvegarde et surveillance d'aujourd'hui
- objectif: Le moteur de l'app (51 fonctions SQL hors git, 12 crons) a une copie. Les registres des liens et des mandats sont sauvegardés chaque jour. Le miroir a une copie froide. Les 35 documents qui n'existent que dans le cloud ont une copie serveur. Crons, documents, photos et RDV sont surveillés.
- taches: L10-9a — versionner dans git les 51 fonctions Supabase absentes et les horaires des 12 crons, L10-9b — ajouter app_relation, app_relation_app_seule, app_relation_registry, app_mandat et app_mandat_champ_app à CRITICAL_TABLES, L10-9c — copie froide hebdomadaire de data/hektor.sqlite hors Veeam (la copie figée du jour J est au ch.45), Hors liste (remarque de G.1-d) — copie serveur des 35 documents « cloud_available » qui n'existent que dans le Storage, lequel n'est pas sauvegardé, L10-10b — une sentinelle des crons honnête, et la purge de cron.job_run_details, L10-10d — sentinelles de données sur les documents, les photos et les RDV
- ordre: 1) L10-9a d'abord, en additif : pg_get_functiondef et cron.job, un fichier par fonction sous supabase/, un script de contrôle « 0 absente ». C'est le préalable de TOUTE retouche de fonction SQL dans les chapitres suivants.
2) L10-9b : 5 noms dans la liste, puis --dry-run.
3) L10-9c : un script sur l'API de sauvegarde de sqlite, lecture seule sur la source. La tâche hebdomadaire s'installe avec accord, hors 05:00-07:20 et hors 21:00.
4) Les 35 documents : lecture du Storage, écriture sur le serveur au bon sha256 (additif).
5) L10-10b : « inconnu » puis « critique » au lieu de « ok », et purge du journal des crons (accord).
6) L10-10d : 3 à 5 sentinelles déclaratives (documents en uploading depuis plus de 24 h, photos du parc vivant sans dérivé, liens RDV actifs ≠ annonces diffusables).
- prerequis: Chapitre 1 (L10-10a : sinon une sentinelle neuve reste muette). | Chapitre 4 (L10-10c). | Décision : où ranger les copies froides (4,1 Go chacune, 444 Go libres sur l'unique volume C:) et combien en garder. | Décision : les seuils des sentinelles. | Accord pour purger cron.job_run_details et pour installer la tâche hebdomadaire.
- feu vert: J'enchaîne sans attendre pour L10-9a, le script de L10-9c et la copie des 35 documents (additifs). « vas-y » pour L10-9b, L10-10b et L10-10d. ACCORD obligatoire pour la purge et la tâche planifiée. | perime: False | taille: 3,5 à 5,5 j
- fin: Pour chacune des 140 fonctions non-extension du schéma public, un .sql suivi par git : le contrôle compte 0 absente, et le hash du corps est conforme. Les 12 crons sont écrits avec leur horaire.
Le fichier critique du lendemain contient les 5 tables, avec les mêmes comptes que la source.
Une copie datée du miroir passe PRAGMA integrity_check, avec les mêmes comptes pour hektor_annonce_detail et hektor_mandat.
Les 35 documents ont une copie serveur au bon sha256.
app_cron_health répond en moins de 2 s, et une mesure impossible n'est plus « ok ».
Chaque sentinelle neuve s'affiche dans l'écran Santé ; une anomalie injectée sur une configuration d'essai la fait passer au rouge.
- verif: Script de contrôle des fonctions. backup_critical.py --dry-run, puis ouverture du fichier en mode ro. PRAGMA integrity_check. Comparaison des sha256. Moniteur lancé sur une configuration d'essai.
- gestes Frederic: Choisir l'emplacement et le nombre de copies froides. | Fixer les seuils. | Accorder la purge et la tâche hebdomadaire.

## CH7 — Fermer les portes ouvertes (sécurité) avant toute ouverture
- objectif: La clé publique anon ne permet plus d'écrire. La fonction Edge ne sert plus de porte dérobée. Les cibles de diffusion ne sont plus modifiables par n'importe quel compte actif.
- taches: L10-16a — fonction Edge hektor-diffusion : vérifier le rôle, ou la retirer, L10-16b — retirer à anon l'exécution des fonctions d'écriture (environ 30 à trier, 9 selon l'audit), L10-16c — les cibles de diffusion ne sont plus modifiables par tout compte actif sur toute annonce
- ordre: 1) L10-16a : lire 30 jours de journaux Edge, puis retirer la fonction (le front ne l'appelle pas : api.ts:5143-5297 passe par le backend) ou y ajouter un contrôle admin.
2) L10-16b : trier chaque fonction selon son appelant (front connecté = authenticated, run = service_role, page publique = anon). Écrire le patch ET son patch de retour arrière. Parcourir les écrans et les pages publiques avec un compte de test.
3) L10-16c : les politiques RLS de app_diffusion_target. Si la question 6 n'est pas tranchée, une règle provisoire : accès au dossier, ou rôle manager ou admin. Elle sera revue au ch.23.
- prerequis: Chapitre 6 (L10-9a : app_set_bien_statut, app_record_proposition et app_create_relance_for_contact n'ont pas de copie dans git). | Décision : retirer la fonction Edge ou y ajouter un contrôle. | Décision : quelles pages publiques (espace client, RDV) appellent des RPC sans être connectées. | Question 6, ou accord pour la règle provisoire.
- feu vert: ACCORD obligatoire : droits et politiques en prod, déploiement Supabase. | perime: False | taille: 1,75 à 2,5 j
- fin: has_function_privilege('anon', f, 'EXECUTE') = false pour toute fonction d'écriture non justifiée, et la liste des exceptions est écrite. hektor-diffusion répond 403 à un compte non admin, ou n'existe plus. app_diffusion_target exige l'accès au dossier ou un rôle manager ou admin. Les écrans et les pages publiques se parcourent sans erreur.
- verif: Requête de catalogue avant et après. Appel d'essai à la fonction Edge. Parcours avec un compte commercial de test.
- gestes Frederic: Trancher le sort de la fonction Edge. | Dire quelles pages publiques fonctionnent sans connexion. | Répondre à la question 6, ou accepter la règle provisoire. | Accorder les patchs.

## CH8 — Les filets du pilote : une création ne se perd plus, et un seul déploiement du front
- objectif: Une création ratée reste visible au lieu de disparaître en 24 h. Plus aucun texte « null » n'est envoyé comme numéro d'annonce. Les liens « Ouvrir Hektor » et « Signature » visent le bon domaine. Le logo du mandat vient de notre coffre. Le registre des mandats s'exporte pour un contrôle.
- taches: L10-2a — le balayeur des lignes provisoires n'efface plus rien de non traité, et l'erreur n'est plus avalée, L10-1a — le piège « null » : une aide qui rend null au lieu de « null » (21 appels dans api.ts), E.0-bis-a — les liens « Ouvrir Hektor » et « Signature » sur l'ancien domaine (3 fabricants l'ont en dur), L10-15-a — le logo du PDF de mandat vient de gti-photo, A.3-b — export et impression du registre des mandats
- ordre: 0) En entrant : vérifier l'état des défauts R-1 à R-5 du registre des relations (non mesuré). S'ils toucheraient les pilotes (R-1 : fiche contact vide ouverte depuis une annonce ; R-3 : lien en attente invisible), ils entrent dans ce chapitre.
1) L10-2a. Relire d'abord supabase/patch_purge_provisoires_2026-09-25.sql : c'est la décision du 25/09 que cette tâche amende. Retirer les deux DELETE de app_sweep_stale_provisionals. Journaliser au lieu d'avaler l'erreur (app_create_search_optimistic, app_create_annonce_job_optimistic). Ajouter la sonde « créations en erreur ».
2) Le front, en un seul build et un seul déploiement :
- L10-1a (fonction d'aide, puis 21 remplacements) ;
- E.0-bis-a (une constante, 6 remplacements : App.tsx:8209-8253, 5430, 10778, 11021) ;
- L10-15-a (mandat-template.html:11 et :61) ;
- A.3-b (composant neuf : CSV, PDF imprimable, filtres).
3) npm run build (tsc -b), puis recherche dans dist.
- prerequis: Chapitre 6 (L10-9a : app_create_search_optimistic et le balayeur sont capturés avant d'être touchés). | Décision : où l'utilisateur voit une création en erreur, et qui la traite. | Confirmer l'adresse visée par les liens (www.gti-immobilier.fr/admin), à coordonner avec A.4. | Vérifier que gti-photo/marque/logo-gti.png est le même logo que logoSite.png. | Colonnes du registre (juriste) ; à défaut, les colonnes actuelles, avec le « Montant » signalé comme étant le prix de l'annonce.
- feu vert: « vas-y » (code existant, SQL, front). ACCORD obligatoire pour le patch SQL en prod et pour le déploiement Vercel. Pousser = déployer : le déploiement emporte aussi les commits locaux en attente. | perime: False | taille: 2,6 à 4,1 j
- fin: Plus aucun DELETE de ligne 'error' sans geste humain, et la sonde compte les créations en erreur. Sur copie, une recherche créée pendant 15 min d'arrêt du worker est encore là le lendemain.
0 appel String(...hektor_annonce_id) sans garde dans api.ts.
« la-boite-immo » apparaît 0 fois dans dist, hors filtre volontaire.
Un mandat d'essai n'émet aucune requête vers gti-immobilier.fr.
Un export 2026 compte autant de lignes que le registre, dans l'ordre des numéros.
- verif: Relecture des fonctions au catalogue. Fonctions rejouées sur des lignes fabriquées (copie). grep avant et après. Build, puis recherche dans dist. Compte de l'export contre la vue app_registre_mandats_current.
- gestes Frederic: Dire où montrer les créations en erreur. | Confirmer l'adresse et le logo. | Fournir les colonnes du registre (juriste), ou accepter les actuelles. | Accorder le patch et le déploiement.

## CH9 — Les droits en gestes métier, et les comptes des pilotes
- objectif: Un négociateur peut faire seul, sur SES biens, les gestes décidés, sans toucher aux biens des autres. Chaque pilote a un compte relié.
- taches: L10-11-a — réécrire les droits en gestes métier, derrière un réglage éteint (avec agency_forbidden et le droit sur les contacts), L10-11-b (pilotes) — créer les comptes des négociateurs pilotes
- ordre: 1) Écrire la matrice rôle × geste × propriétaire et la faire valider.
2) L10-11-a :
- app_console_can_request_job et ses appelants, réécrits derrière un réglage app_setting éteint ;
- revoir l'agency_forbidden de app_console_create_draft_annonce_job (la première annonce d'un négociateur neuf) ;
- app_console_can_request_contact_job lit le registre durable plutôt que app_contact_relation_current ;
- tests SQL BEGIN … ROLLBACK, sur une branche ou une copie.
3) Comptes des pilotes par le chemin existant (admin_users.py /create). Vérifier qu'ils sont « linked » et que negociateur_email est celui de leurs annonces.
Le réglage s'allume au ch.10, pour les seuls pilotes.
- prerequis: Chapitre 7 (L10-16b : sinon la porte d'à côté reste ouverte). | Question 3 : que fait un négociateur seul ? Aujourd'hui, un commercial n'a que 7 types de travaux ; archiver et changer le statut sont réservés à l'admin. | Décision sur les rôles : la base a admin, manager, commercial, lecture ; le plan a admin, commercial, administratif. | La liste des pilotes (au moins 3). | Accord pour créer les comptes (des emails d'invitation partent).
- feu vert: ACCORD obligatoire : patch des droits en prod, création de comptes. Le réglage reste éteint jusqu'au ch.10. | perime: False | taille: 2,5 à 3,5 j
- fin: Réglage éteint : la matrice donne les mêmes résultats qu'aujourd'hui. Réglage allumé (branche ou copie) : un commercial modifie SON annonce et fait les gestes décidés, mais pas sur celles des autres, et un négociateur sans annonce crée sa première annonce. Chaque pilote a un compte « linked », avec negociateur_email égal à l'email de ses annonces (aujourd'hui 4 sur 39).
- verif: Matrice de tests SQL. Requête : emails des négociateurs des annonces vivantes × app_user_profile. Connexion réelle de chaque pilote.
- gestes Frederic: Répondre à la question 3 et trancher les rôles. | Valider la matrice. | Désigner les pilotes. | Accorder le patch et les comptes.

## CH10 — Le pilote s'ouvre : quelques négociateurs travaillent dans l'app pendant que Hektor vit
- objectif: La première preuve par l'usage : de vraies saisies passent par l'app, et chaque défaut se trouve pendant que Hektor sert encore de filet.
- taches: E.2 (ouverture) — allumer les droits pour les pilotes, le tableau de suivi, les consignes et le canal de retours
- ordre: 1) Frédéric écrit l'amendement de la décision du 21/09 :
- qui, dans quelles agences, avec quels gestes ;
- la règle contre la double saisie ;
- ce qui reste dans Hektor : signature, diffusion, gestion des photos, fusion, et l'ajout de fichiers tant que les ch.12-13 ne sont pas faits.
2) Allumer le réglage des droits pour les pilotes seulement (accord).
3) Le code de soutien : un tableau hebdomadaire (app_console_job par rôle et par type, carnets *_pending et *_provisional, sentinelles du ch.6).
4) Première semaine : lire leurs travaux chaque jour et écrire chaque défaut au plan. Un défaut bloquant passe devant le chapitre en cours.
5) La preuve réelle d'A.3-a : un numéro de mandat demandé depuis l'app, par un pilote sur un vrai mandat, ou sur l'annonce d'essai 62966.
Le pilote court ensuite en fond, pendant les ch.11 à 13. Son bilan est au ch.14.
- prerequis: Chapitres 1 (alerte sur la hausse), 2 (A.3-a), 8 (L10-2a, E.0-bis-a) et 9 (droits, comptes). | Décision écrite : l'amendement du 21/09 pour les pilotes. | Accord pour allumer le réglage pour les pilotes.
- feu vert: « vas-y » pour le tableau de suivi. ACCORD obligatoire pour l'allumage (utilisateurs réels) et pour la preuve A.3-a (écriture chez Hektor). | perime: True | taille: 1 à 2 j de code, puis 2 à 4 semaines d'usage en fond. Ouverture vers la 2e quinzaine de novembre si les décisions suivent (non daté ferme).
- fin: Au moins 3 comptes pilotes « linked », avec le réglage allumé pour eux. Au moins 1 travail demandé par un compte commercial dans les 3 premiers jours (aujourd'hui 0 en 120 jours). 0 saisie perdue dans les carnets. Le tableau de suivi est publié. Le push de app_mandat passe la nuit qui suit le premier numéro de mandat demandé depuis l'app.
- verif: Comptes de app_console_job par requested_by et par rôle. Lecture des carnets *_pending et *_provisional. Journal du run de la nuit qui suit le premier numéro de mandat.
- gestes Frederic: Écrire l'amendement du 21/09. | Prévenir et accompagner les pilotes la première semaine. | Accorder l'allumage.

## CH11 — Les statuts écrits chez nous d'abord : mise sous mandat, archiver, restaurer, négociateur, clôture
- objectif: Mettre sous mandat (environ 60 par mois), archiver, restaurer, changer de négociateur et clore un mandat s'écrivent chez nous dans la seconde. La valeur tient la nuit, même si Hektor refuse. Hektor reçoit toujours le geste.
- taches: L10-3a — l'applicateur du carnet d'annonce : « l'app gagne quand elle a quelque chose à dire » (dormant, liste vide), L10-3c — la mise sous mandat (Estimation → Actif) et les changements de statut, écrits chez nous, L10-3b — archiver, restaurer, changer de négociateur, appliqués tout de suite, avec le motif d'archivage, L10-3d — « Mandat clos » : chez nous d'abord, Hektor ensuite (worker)
- ordre: 1) L10-3a : un applicateur jumeau de appliquer_contrat_mandat.py, avec une table carnet → colonne. Piège : le carnet écrit 'statut', la colonne s'appelle 'statut_annonce' (sinon REFUS code 3). Avec la liste vide, le run reste identique. --dry-run, puis un run complet sur copie.
2) Étendre au carnet la protection de la relecture (push_single_annonce_to_supabase.py:367-395). Ajouter une sonde « l'app et Hektor divergent ».
3) L10-3c, sur le patron de app_geste_affaire_optimistic.
4) L10-3b, avec une colonne neuve pour le motif.
5) L10-3d (worker, l.13121-13135), puis un redémarrage.
6) Inscrire les champs au contrat UN par UN (archive, statut_annonce, negociateur_email), avec une nuit d'observation pour chacun.
⚠ À vérifier EN ENTRANT (non mesuré) : une ligne du carnet doit céder dès que Hektor confirme la même valeur, et une saisie faite ENSUITE dans Hektor par un non-pilote doit gagner (récence par champ). Sinon le courant s'inverse, et rien n'est allumé.
- prerequis: Chapitre 6 (L10-9a : app_statut_redescente_calcule était hors git). | Chapitre 9 (archive et statut ouverts aux commerciaux, selon la question 3). | Chapitre 10 (les pilotes s'en servent). | Décision : quels champs entrent en premier au contrat. | Décision : la liste des motifs d'archivage. | Question 6 : passer en Actif rend-il le bien diffusable ? Sinon, la diffusion reste par Hektor jusqu'au ch.23.
- feu vert: J'enchaîne sans attendre pour L10-3a à liste vide (additif dormant). « vas-y » pour le brancher dans le run, pour les RPC et pour le worker. ACCORD obligatoire pour les patchs SQL, le redémarrage, les essais réels et chaque allumage de champ. | perime: False | taille: 4,5 à 6 j
- fin: Liste vide : le run est identique (0 ligne changée).
Après une mise sous mandat depuis l'app : statut_annonce = 'Actif' dans app_dossier_current dans la seconde, au carnet, et toujours après une ouverture de fiche et un run.
Après un archivage : archive = '1' dans la seconde, motif gardé, même si le travail Hektor échoue.
Hektor injoignable (simulé) : « Mandat clos » et sa date sont posés chez nous, et le travail Hektor attend.
Une valeur changée ENSUITE dans Hektor gagne.
Au moins une mise sous mandat est faite par un pilote.
- verif: --dry-run, puis run complet sur copie. Essais réels sur une estimation et une annonce d'essai, worker arrêté pour simuler un refus, puis un run. Essai hors ligne du worker avec Hektor simulé en panne. Lecture de la sonde de divergence.
- gestes Frederic: Choisir les premiers champs du contrat et donner la liste des motifs. | Répondre à la question 6. | Accorder les patchs, le redémarrage, les essais et chaque allumage.

## CH12 — Documents et photos : chez nous d'abord, et les retraits faits dans Hektor remontent
- objectif: Un document ou une photo ajouté par un négociateur existe chez nous (serveur, cloud, vitrine) avant Hektor, et n'est jamais purgé. Les 350 photos retirées dans Hektor ne s'affichent plus.
- taches: G.5-b — une RPC qui crée la ligne document ou photo, avec contrôle d'accès, et sa politique Storage, G.5-c — front et repassage : un document ajouté existe chez nous avant Hektor, G.5-e — ajouter une photo chez nous d'abord (dérivés immédiats, ordre), E.0-bis-c1 — faire remonter les RETRAITS et l'ORDRE des photos faits dans Hektor
- ordre: 1) G.5-b : une RPC SECURITY DEFINER qui exige auth.uid() et app_console_can_access_dossier, et pose envoi_hektor_statut='a_envoyer'. Plus une politique Storage d'écriture sur le chemin définitif. Essais BEGIN … ROLLBACK, puis advisors.
2) G.5-c :
- front derrière une variable VITE_ (api.ts:7669) ;
- puis le REPASSAGE des 'a_envoyer' et 'echec', qui relit la liste Hektor avant tout renvoi (pas de double envoi) ;
- le nouveau type de travail va À LA FOIS dans la liste en dur de app_console_claim_next_job ET dans DOCUMENT_JOB_TYPES (l.81), sinon il reste pending à vie.
3) G.5-e : dérivés w400 et w1600 tout de suite, sort_order, visible, present_in_hektor=true à la naissance (api.ts:7585, completerEnvoiPhotoDifferee l.7971).
4) E.0-bis-c1 : une nuit en mode mesure, avec un plancher sur le patron du ch.5, puis l'application (present_in_hektor=false, absent_depuis, sort_order, vignette).
Mise en service : un patch SQL, un redémarrage, un déploiement.
- prerequis: Chapitre 2 (G.5-a en service, sinon la ligne est purgée à la synchro suivante). | Chapitre 7 (L10-16 : les deux tables donnent tous les droits à anon et à authenticated). | Chapitre 9 (upload_hektor_photo ouvert aux commerciaux, selon la question 3 ; sinon les essais se font en admin). | Chapitre 5 (patron du plancher pour E.0-bis-c1). | Décision : la « source » de la ligne. Garder 'hektor_console' (la garde G.5-a suffit), ou une source app que l'adoption réécrit (sinon doublon). | Décision : une photo retirée chez Hektor est cachée et sort de la vitrine, jamais effacée.
- feu vert: « vas-y » pour le code. ACCORD obligatoire pour la RPC et la politique Storage en prod, le patch du distributeur, le redémarrage, le déploiement Vercel, les essais réels et le passage de la mesure à l'application pour E.0-bis-c1. | perime: True | taille: 5 à 7,5 j
- fin: En transaction annulée : un commercial est accepté sur son bien, refusé sur celui d'un autre, et anon est refusé.
Sur une annonce d'essai :
- la ligne du document est visible avant Hektor et tient 15 min de worker arrêté ;
- un envoi raté passe 'echec', puis 'envoye' au repassage, avec UN seul document chez Hektor ;
- une photo est visible dans l'app et dans la vitrine, avec ses dérivés, avant la confirmation de Hektor.
Les 350 photos retirées sont marquées absentes, et les 33 photos principales sont alignées. Une réponse vide simulée marque 0 photo absente.
- verif: Essais SQL et advisors. Requêtes sur app_console_document et app_console_photo (envoi_hektor_statut, derives_json, present_in_hektor), avant et après. Liste des documents de l'annonce chez Hektor. Essai sur copie avec une réponse vide, puis partielle.
- gestes Frederic: Choisir la source de la ligne. | Valider la règle des photos retirées. | Accorder les patchs, le redémarrage, le déploiement et les essais.

## CH13 — Les 3 PDF que nous fabriquons naissent chez nous d'abord
- objectif: L'avis de valeur, le mandat et le plan cadastral ont leur ligne et leur fichier chez nous avant l'envoi à Hektor. L'avis de valeur prend ses photos dans nos dérivés.
- taches: G.5-d — les 3 PDF (avis de valeur, mandat, plan cadastral) créent leur ligne avant Hektor, L10-15-c — les photos de l'avis de valeur viennent de nos dérivés w1600
- ordre: 1) G.5-d : handleGenerateEstimationPdf (l.7239, pose du travail l.7336), handleGenerateMandatDocument (l.7413, l.7434) et handleGenerateCadastreDocument (l.7606, l.7650). Créer la ligne avec la clé de service, puis poser payload.app_document_id. Reporter dans le chemin différé l'annotation avenant_new_price, que seul le chemin immédiat pose (l.7865-7885).
2) L10-15-c : loadEstimationDetail (l.6116-6133) prend les w1600 de app_console_photo par app_dossier_id, en gardant le repli actuel.
3) Un seul redémarrage, puis l'essai de chaque générateur.
- prerequis: Chapitre 12 (G.5-c : le repassage commun si Hektor échoue). | Chapitre 2 (G.5-a). | Chapitre 9 (les travaux generate_* ouverts aux commerciaux, si la question 3 le décide).
- feu vert: « vas-y » pour le worker. ACCORD obligatoire pour le redémarrage et l'essai de chaque générateur (le PDF du mandat part en signature). | perime: False | taille: 1,5 j
- fin: Pour chacun des 3 générateurs, sur une annonce d'essai : la ligne et le fichier serveur existent avant l'envoi à Hektor. Un avenant garde avenant_new_price. Un avis de valeur d'essai ne charge aucune image hors gti-photo.
- verif: Essais réels avec accord. Relecture du HTML rendu et du PDF. Requêtes sur app_console_document et ses métadonnées.
- gestes Frederic: Accorder le redémarrage et les essais.

## CH14 — Bilan du pilote, puis tous les négociateurs dans l'app
- objectif: Le pilote a prouvé par l'usage les gestes quotidiens : modifier, mettre sous mandat, ajouter documents et photos, générer les PDF. On l'élargit aux 30 négociateurs actifs environ, pendant que Hektor vit encore.
- taches: E.2 (critère complet) — le bilan chiffré des pilotes, L10-11-b (tous) — les comptes de tous les négociateurs actifs, Les correctifs des défauts trouvés par le pilote, une tâche de code à la fois
- ordre: 1) Le bilan, sur au moins 2 semaines et 3 pilotes : travaux par rôle et par type, saisies perdues, défauts écrits au plan.
2) Les correctifs bloquants, un à la fois.
3) Frédéric décide de l'élargissement (quelles agences, dans quel ordre).
4) Les comptes de tous : 39 emails portent des annonces vivantes, 4 ont un compte aujourd'hui.
5) Le tableau de suivi continue jusqu'à la coupure.
- prerequis: Chapitres 10 à 13. | Décision : élargir, à qui, dans quel ordre. | Accord pour créer les comptes.
- feu vert: « vas-y » pour chaque correctif de code existant. ACCORD obligatoire pour les comptes et les réglages en prod. | perime: True | taille: 1 à 3 j de code, plus l'accompagnement
- fin: Au moins 3 pilotes sur 2 semaines, avec des travaux demandés par des commerciaux chaque semaine. 0 saisie perdue. Chaque défaut est écrit au plan. Ensuite, chaque négociateur actif a un compte « linked », avec negociateur_email égal à l'email de ses annonces.
- verif: Comptes hebdomadaires de app_console_job par rôle et par type. Carnets *_pending et *_provisional. Retours écrits des pilotes. Requête emails × app_user_profile.
- gestes Frederic: Lire le bilan et décider de l'élargissement. | Accorder les comptes. | Prévenir les équipes.

## CH15 — Les mandats existants vivent chez nous : dates de clôture et corrections
- objectif: Chaque mandat a une date de clôture avec sa règle, ou le statut « en cours », pendant que Hektor peut encore trancher « le reste ». Une erreur de type ou de date se corrige dans l'app.
- taches: C.13-c — rattraper les dates de clôture (règles 1, 2 et 3, plus « le reste »), E.0-bis-d1 — corriger le type et les dates d'un mandat existant, sans avenant
- ordre: 1) C.13-c :
- calculer dans une table de PROPOSITIONS à part (additif) ;
- « le reste » d'abord (environ 3 207 mandats, seuls à périmer), puis la règle 1 (vente, 6 766), la règle 2 (échéance dépassée, 16 869) et la règle 3 (annulation, 4) ;
- mesurer plus finement les 2 441 mandats rattachés à aucun index ;
- échantillon de 20 relu par Frédéric ;
- application par le carnet app_mandat_champ_app (delete-never, rien ne part chez Hektor) ;
- câblage du registre dans export_app_payload.py (plan l.1555) ;
- une nuit de run.
2) E.0-bis-d1 : le patron de la clôture (C.13-a et b), étendu à 3 champs ajoutés au contrat un par un, plus une RPC et l'écran de la fiche du mandat. Essai sur l'annonce 62966 (mandat 660), sans toucher à Hektor.
- prerequis: Chapitre 2 (A.3-a). | Décision : la date à donner à « le reste ». | Accord pour l'écriture de masse en prod (environ 23 600 lignes). | Juriste : quelles corrections sont permises sans avenant ? | Décision : pendant la cohabitation, la correction part-elle chez Hektor ? C'est lui qui envoie les mails d'échéance. | Doit précéder A.3-f (ch.30) et L10-13-c (ch.40).
- feu vert: J'enchaîne sans attendre pour la table de propositions (additif). « vas-y » pour le run et la RPC. ACCORD obligatoire pour l'écriture de masse, les patchs et le déploiement. | perime: True | taille: 4 à 6 j
- fin: Chaque mandat a une date de clôture avec sa règle d'origine, ou le statut explicite « en cours ». Écart 0 entre app_mandat et le registre affiché. Les 3 clôtures de Hektor que Supabase ignorait sont conservées. Une nuit de run passe sans écrasement. Une date corrigée dans l'app tient après une nuit, à l'écran et dans app_mandat.
- verif: Comptes de la table de propositions comparés aux mesures du 07/10. Échantillon de 20 relu. Requêtes sur app_mandat et le registre avant et après la nuit. Essai sur l'annonce 62966.
- gestes Frederic: Trancher « le reste » et relire l'échantillon. | Poser la question au juriste. | Trancher l'envoi des corrections chez Hektor. | Accorder l'écriture de masse.

## CH16 — Capturer ce qui ne vit que chez Hektor : brouillons, consentement, agenda, historique des leads
- objectif: Ce que seul Hektor connaît est descendu chez nous, ou déclaré abandonné par écrit : le contenu des brouillons, le consentement RGPD, l'agenda des visites (si décidé) et l'historique brut des leads (si A.5-a l'exige).
- taches: E.0-bis-f (étape 1) — descendre le détail des 508 brouillons, dont les 67 qui n'ont aucun détail local, L10-13-a (suite) — descendre l'état RGPD dans une colonne neuve, s'il existe chez Hektor, E.1b (import) — si l'import est décidé : créer d'abord la table « visite » et sa séquence (1re pièce de L10-12-a), puis le lecteur de l'agenda, A.5-b (partie historique) — si A.5-a montre que les leads depuis le 01/02 ne vivent que chez Hektor : leur export brut, rangé chez nous sans traitement (le traitement est au ch.36)
- ordre: 1) Brouillons : 441 depuis le détail local, 67 par lecture chez Hektor à cadence imposée, vers app_brouillon_annonce_detail_cache (0 ligne aujourd'hui).
2) L10-13-a : une colonne neuve et une lecture additive, seulement si le ch.3 a trouvé le consentement.
3) E.1b : table « visite » et séquence (dormantes), puis le lecteur, comparé sur un mois témoin. 0 j si Frédéric a renoncé.
4) Historique des leads : l'export brut, seulement si le ch.3 l'a demandé.
- prerequis: Chapitre 3 (mesures A.5-a, L10-13-a, E.1b). | Question 2 : importer l'agenda ou y renoncer. | Avis juridique éventuel sur la reprise du consentement. | Accords de lecture chez Hektor.
- feu vert: J'enchaîne sans attendre pour le code additif. ACCORD obligatoire pour chaque lecture chez Hektor et pour créer une table ou une colonne en prod. | perime: True | taille: 1,5 à 3 j ; plus 2 à 4 j si l'agenda est importé
- fin: app_brouillon_annonce_detail_cache compte 508 lignes, dont les 67 rapatriées. L'état RGPD de chaque contact est descendu, ou déclaré inexistant chez Hektor. Agenda : la décision est écrite ; en cas d'import, autant de visites que chez Hektor sur le mois témoin. Leads : l'historique est chez nous, ou déclaré inutile par écrit.
- verif: Compte du cache des brouillons contre l'index. Une fiche Hektor connue comparée à la colonne neuve. Comparaison sur un mois témoin.
- gestes Frederic: Trancher la question 2. | Obtenir l'avis juridique sur le consentement, si nécessaire. | Accorder les lectures chez Hektor.

## CH17 — Comparer tant que Hektor vit : le corps de l'annonce et la paire du ménage
- objectif: On sait, colonne par colonne, si le corps de l'annonce peut venir du cloud quand le miroir s'arrêtera. Un couple créé dans l'app donne deux fiches liées avec nos numéros, comme chez Hektor, sans troisième fiche.
- taches: 26bis-3b — prouver que la copie du cloud vaut le miroir pour le corps de l'annonce (comparateur en lecture seule), C.9-couple-b — l'app fabrique la paire du ménage (deux fiches, deux numéros, le lien), derrière un réglage
- ordre: 1) 26bis-3b : un script neuf en lecture seule. phase2.sqlite en mode=ro (app_view_generale, 163 colonnes) contre app_dossier_current et app_dossier_detail_current, sur 13 463 annonces. Il tourne hors du run (05:00-07:20), hors de la descente (08:15) et hors du rattrapage (21:00). Le rapport est refait un 2e matin.
2) C.9-couple-b, derrière un réglage app_setting (patron c9_annonce_nait_dans_app) :
- réserver 2 numéros ;
- écrire les 2 fiches et le lien dans la même transaction ;
- adapter l'envoi du worker (l.15697-15703, 15850-15851) sans jamais créer de 3e fiche chez Hektor ;
- essai réel, sonde, puis une nuit.
- prerequis: Chapitre 3 (le rapport C.9-couple-a). | Décision : pendant la cohabitation, envoyer le bloc conjoint (Hektor crée la 2e fiche) ou deux fiches déjà liées.
- feu vert: J'enchaîne sans attendre pour 26bis-3b (lecture seule, additif). « vas-y » pour C.9-couple-b. ACCORD obligatoire pour le patch, le redémarrage et l'essai réel chez Hektor. | perime: True | taille: 3,5 à 5 j
- fin: Un tableau donne, pour chaque colonne de app_view_generale, sa source dans le cloud, le nombre d'écarts sur 13 463 annonces et une explication pour chaque écart non nul, avec la liste des colonnes SANS source. Il est stable sur deux matins. Un ménage créé dans l'app donne 2 lignes app_contact_current aux app_couple_contact_id croisés dès le geste, toujours 2 fiches (pas 3) après le retour de Hektor, et la sonde montre une paire identique à celle de Hektor.
- verif: Le rapport refait le lendemain, et 10 annonces contrôlées à la main. sonde_paire_de_menage.py sur les deux numéros, puis un run par-dessus.
- gestes Frederic: Relire les colonnes sans source : elles décident des ch.19 et 41. | Trancher bloc conjoint ou deux fiches liées. | Accorder l'essai réel.

## CH18 — Une seule porte vers Hektor : attendre un numéro, ou attendre que Hektor revienne (dormante)
- objectif: Une seule porte décide qu'un travail ne part pas chez Hektor, parce que l'annonce n'a pas encore son numéro ou parce que Hektor est coupé. Rien ne se perd, aucune erreur n'est levée, et « Préparer », l'étape « notre serveur d'abord » et les PDF passent toujours.
- taches: L10-1b — une barrière d'attente dans app_annonce_enqueue_due_pushes (cron 7), et relecture des autres fabricants de travaux, L10-1c — une porte unique côté worker pour la cible « annonce », L10-6b — l'interrupteur de coupure dans app_setting, lu par le worker, avec la liste blanche de ce qui continue, L10-6c — côté base : plus aucun travail Hektor réclamé quand l'interrupteur est allumé, L10-6d — côté backend Render : les routes Hektor obéissent à l'interrupteur
- ordre: 1) L10-1b, sur le patron de app_contact_enqueue_due_pushes. Relire app_console_action_enqueue_due_retries (cron 13). La condition est écrite comme une PORTE qui accepte deux motifs : « pas encore de numéro » et « Hektor coupé ». On ne l'écrit qu'une fois.
2) L10-1c, sur le patron de cibleHektorContact : environ 35 lectures de job.hektor_annonce_id. Les chemins de stockage restent pour G.5-f.
3) L10-6b :
- clé lue à chaque tour, avec un cache ;
- liste blanche : prepare_document_cloud, étape ① de G.5, générateurs ;
- connexion et keep-alive coupés ;
- travaux Hektor laissés en pending (le statut « suspendu » n'existe pas) ;
- on ne touche pas à HektorConsoleWorkerService.cs.
4) L10-6c : une garde dans app_console_claim_next_job, essayée sur une branche ou une copie. Une faute bloquerait tous les workers.
5) L10-6d : hektor_bridge.py:242-307.
Mise en service : un patch, un redémarrage, un déploiement Render. Clé absente = comportement identique à aujourd'hui.
- prerequis: Chapitre 3 (L10-6a, l'ordre d'extinction). | Chapitre 6 (L10-9a). | Chapitre 8 (L10-1a). | Chapitres 12 et 13 (G.5 : sinon l'interrupteur couperait les PDF ; prérequis mesuré de L10-6b). | Décision : le nom de la clé. | Décision : mettre la garde dans app_console_claim_next_job (un seul point, versionné) ou dans les 4 crons (5, 7, 8, 13).
- feu vert: « vas-y » (code existant). ACCORD obligatoire pour les patchs SQL, le redémarrage des 4 services et le déploiement Render. L'interrupteur ne s'allume en réel que le jour J. | perime: False | taille: 4 à 5,5 j
- fin: Sur copie, une saisie sur une annonce sans numéro ne produit ni travail ni conflit, et part dans la minute où le numéro arrive. grep : aucun appel à Hektor ne lit job.hektor_annonce_id hors de la porte. Un travail sans numéro reste pending, pas en erreur.
Worker --once, clé forcée : prepare_document_cloud réussit, update_hektor_annonce_fields reste pending, aucune connexion à Hektor dans le journal.
Clé allumée sur copie : 0 travail Hektor réclamé, et les routes Render répondent « Hektor coupé ».
Clé absente : taux d'erreur des travaux inchangé sur 24 h après le redémarrage.
- verif: Essais sur copie et sur branche. LE worker exécuté en --once. backend/tests. Sonde en prod : 0 app_console_job à hektor_annonce_id NULL créé par le cron.
- gestes Frederic: Nommer la clé et choisir où mettre la garde. | Accorder les patchs, le redémarrage et le déploiement.

## CH19 — Le corps de l'annonce née dans l'app est tenu chez nous
- objectif: Une annonce créée dans l'app a tous ses champs chez nous dès le geste, et le serveur la tient même si le miroir l'ignore.
- taches: L10-2d — le corps complet de l'annonce écrit chez nous à la naissance, 26bis-3a — le serveur tient le corps d'une annonce que le miroir ignore (brancher --injecter)
- ordre: 1) L10-2d : extraire la carte des champs de app_edit_annonce_optimistic dans une fonction partagée, et écrire app_dossier_detail_current à la création, derrière un réglage NEUF. L'interrupteur c9 est ALLUMÉ et garde l'ancien chemin tant que le nouveau n'est pas éprouvé.
2) 26bis-3a : --injecter (phase2/identite/annonces_app_seule.py) lit aussi la ligne détail, puis il est branché au run. Essai sur copie avec une annonce fabriquée dans la plage ≥ 10 000 000.
- prerequis: Chapitre 18 (L10-1b : la carte des champs passe par app_annonce_pending, que le cron 7 transforme en travaux). | Chapitre 17 (26bis-3b : les colonnes qui ont une source dans le cloud). | Chapitre 11 (L10-3a). | Accord pour changer ce que le push nocturne envoie.
- feu vert: « vas-y » (code existant, run). ACCORD obligatoire pour le patch SQL, le branchement au run et une création réelle d'essai. | perime: False | taille: 3 à 4,5 j
- fin: Une annonce née dans l'app a sa ligne détail dès le geste, avec 0 écart champ à champ avec la charge envoyée à Hektor. Sur copie, une annonce présente dans Supabase et inconnue du miroir a sa ligne dans app_view_generale après le run, et le push ne la modifie pas.
- verif: Essai et run complet sur copie. Une création réelle d'essai comparée à la charge, à la ligne détail et au retour du miroir.
- gestes Frederic: Accorder le changement du push nocturne. | Accorder la création réelle d'essai.

## CH20 — La nuit de bascule du schéma : le numéro Hektor de l'annonce devient facultatif
- objectif: Une annonce née sans numéro Hektor peut exister dans les 17 tables qui l'exigent, et les 7 clés uniques ont leur équivalent sur app_dossier_id, dans Supabase comme sur le serveur local.
- taches: L10-1d — lever les NOT NULL, poser les clés sur app_dossier_id et basculer les ON CONFLICT la même nuit (Supabase et phase2.sqlite)
- ordre: 1) Ré-auditer l'inventaire : 17 tables, 7 clés, types mélangés (bigint et text), 9 lignes de app_relation sans app_dossier_id, 30 lignes sur 114 dans app_console_deleted_annonce_log.
2) Partie additive : lever les NOT NULL et créer les index uniques parallèles en CONCURRENTLY, hors descente, hors run et hors rattrapage (app_console_photo : 437 346 lignes ; app_relation : 132 709). Ajouter une colonne app_dossier_id à app_mandat_champ_app.
3) Répétition complète sur une copie de phase2.sqlite et sur une branche Supabase, avec un run par-dessus.
4) La nuit réelle, services arrêtés : les ON CONFLICT du worker (l.1167, 4394, 4545, 5123), de relation_ledger.py (l.350, 433) et de mandat_ledger.py (l.547, 764), plus la reconstruction SQLite de app_relation et de app_mandat. Code et données la même nuit, comme la bascule contact des 22-23/09.
5) Comptes à J+1.
- prerequis: Chapitre 18 (L10-1b, L10-1c). | Chapitre 5 (L10-8d : le plancher avant de réécrire ces clés). | Chapitre 2 (A.3-a : même contrainte app_mandat_couple_unique). | Chapitre 6 (L10-9a). | Décision : la nuit de bascule. | Décision : le sort des 9 lignes de app_relation et des 30 lignes du journal des suppressions. | Accord pour le coût d'une branche Supabase.
- feu vert: ACCORD obligatoire : schéma de production, nuit de bascule, arrêt et redémarrage des services. | perime: False | taille: 3 à 5 j
- fin: 0 colonne hektor_annonce_id NOT NULL dans les 17 tables vivantes. Chaque clé unique vivante a son équivalent sur app_dossier_id. Après la 1re nuit réelle : 0 doublon, 0 ligne rejetée, et les mêmes comptes de lignes avant et après.
- verif: Catalogue (information_schema, pg_index) avant et après. Répétition sur copie et sur branche. Comptes après la 1re nuit.
- gestes Frederic: Choisir et accorder la nuit de bascule. | Trancher le sort des 9 et des 30 lignes. | Accorder la branche.

## CH21 — Les gestes et les transactions d'une annonce sans numéro Hektor
- objectif: Sur une annonce née dans l'app, les gestes créent leur ligne et leur travail attend. Offre, compromis et vente forment une seule chaîne, gardée par le serveur.
- taches: L10-1e — les 8 fonctions, la chaîne des transactions et les écrans acceptent une annonce sans numéro Hektor, 26bis-TRANSACTIONS — le serveur local garde une transaction née dans l'app que Hektor n'a jamais vue
- ordre: 1) L10-1e :
- les 8 RPC ;
- app_chaine_pour (2 versions) ET son jumeau local recalculer_les_chaines(), changés à l'identique ;
- app_change_annonce_status_optimistic ;
- _ensure_link_for_annonce (backend) ;
- les écrans qui doivent cacher leurs boutons.
2) 26bis-TRANSACTIONS : un chemin INSERT dans redescendre_ce_que_l_app_possede (affaire_ledger.py, vers l.1316) pour les lignes ≥ 1 000 000 sans hektor_affaire_id, puis le recalcul de la chaîne.
- prerequis: Chapitre 20 (L10-1d). | Chapitres 8 et 18 (L10-1a, L10-1b, L10-1c).
- feu vert: « vas-y » (code existant, run). ACCORD obligatoire pour les patchs SQL, les déploiements et l'essai réel. | perime: False | taille: 3 à 4,5 j
- fin: Sur copie, sur une annonce d'essai sans numéro Hektor : les 8 gestes créent leur ligne et leur travail attend. Une offre, puis un compromis, puis une vente forment UNE chaîne. Les app_chaine_id des 31 047 affaires sont identiques avant et après (0 écart). Une transaction de la plage app sans numéro Hektor existe dans phase2.sqlite après le run, et y est encore 2 nuits plus tard.
- verif: Essai sur copie. Comparaison des app_chaine_id. Run sur copie avec une ligne fabriquée. Essai réel accordé sur une annonce d'essai.
- gestes Frederic: Accorder les patchs, les déploiements et l'essai réel.

## CH22 — Numéro de dossier et fichiers d'une annonce sans numéro Hektor
- objectif: Une annonce née dans l'app reçoit son numéro de dossier. Elle porte documents, photos et avis de valeur, même avec le worker coupé de Hektor.
- taches: L10-14 — le numéro de dossier (EM…/V…) fabriqué chez nous quand il n'y a pas de numéro Hektor, G.5-f — un document ou une photo sur une annonce SANS numéro Hektor, worker coupé de Hektor
- ordre: 1) L10-14 : un distributeur dans Supabase, utilisé seulement sans numéro Hektor, avec un contrôle d'unicité contre les 13 463 numéros existants. Les 787 numéros « V… » se terminent tous par le numéro Hektor de l'annonce.
2) G.5-f :
- chemins de fichiers par app_dossier_id, comme cheminDerivePhoto (les anciens chemins restent lisibles) ;
- l'étape ① détachée de l'interrupteur Hektor ;
- le front sans String(null).
Essai sur copie, Hektor coupé.
- prerequis: Chapitres 20 et 21 (L10-1d, L10-1e). | Chapitre 18 (L10-6b). | Chapitres 12 et 13 (G.5-c, G.5-d, G.5-e). | Question 5 : continuer les séries EM et V…, ou passer à notre numéro ? Format ?
- feu vert: « vas-y » pour G.5-f. ACCORD obligatoire pour le distributeur L10-14, les patchs, le redémarrage, les déploiements et l'essai réel. | perime: False | taille: 2 à 4 j
- fin: Une annonce née dans l'app reçoit un numéro de dossier unique, sans collision, affiché dans les mails, les documents et la vitrine. Sur copie, Hektor coupé, elle reçoit un document, une photo et un avis de valeur PDF : les lignes et les fichiers sont sur le serveur et dans le cloud, et s'affichent.
- verif: Contrôle d'unicité. Essai sur copie avec l'interrupteur forcé. Essai réel accordé sur une annonce d'essai.
- gestes Frederic: Répondre à la question 5. | Accorder les patchs et les essais.

## CH23 — Valider pour la diffusion et accepter une baisse de prix, sur les valeurs de l'app
- objectif: Le drapeau « diffusable » devient un champ de l'app, avec un geste « valider pour diffusion ». Une baisse de prix se juge sur le prix de l'app. Le rapprochement ne dépend plus d'un aller-retour par Hektor.
- taches: L10-4 — le drapeau « diffusable » devient un champ de l'app, L10-5 — la baisse de prix contrôlée sur le prix de l'app
- ordre: 1) L10-4 :
- valeur '0' à la naissance (recommandé) ;
- RPC du geste, carnet, applicateur du ch.11, relecture protégée, écran ;
- vérifier les 8 lecteurs du drapeau ;
- revoir la règle L10-16c si la question 6 l'a changée.
2) L10-5, derrière un réglage app_setting éteint : une source de prix de l'app dans hektor_bridge.py (l.98-103, 410-427, 475-495), et le message corrigé. Tests du backend avec une lecture Hektor qui lève une exception.
- prerequis: Chapitre 11 (L10-3a et la relecture protégée). | Chapitre 20 (L10-1d : app_diffusion_request et app_diffusion_target ne sont plus NOT NULL). | Chapitre 6 (L10-9a : 6 des 9 fonctions qui filtrent sur diffusable étaient hors git). | Question 6 : qui valide un bien pour la diffusion ? | Décision : le geste de la baisse de prix (l'app pose le prix, ou le commercial saisit et l'admin contrôle), et la source du prix pendant la cohabitation.
- feu vert: « vas-y » (code existant). ACCORD obligatoire pour les patchs SQL, les déploiements Render et Vercel, et les essais réels. | perime: False | taille: 3 à 4 j
- fin: 0 annonce à diffusable NULL. Le geste pose '1' dans app_dossier_current et au carnet, un run ne le défait pas, et le bien entre au rapprochement sans passer par Hektor. Hektor injoignable (simulé) : la baisse est jugée sur le prix de l'app, sans « Prix différent Hektor ». Réglage éteint : comportement identique à aujourd'hui.
- verif: Essai réel sur une annonce d'essai, lecture du rapprochement, puis un run. Tests du backend.
- gestes Frederic: Répondre à la question 6. | Décider du geste de la baisse de prix. | Accorder les patchs, les déploiements et les essais.

## CH24 — La recherche naît chez nous
- objectif: Une recherche saisie dans l'app est durable, numérotée chez nous, rapprochée dans la minute, et ne fait qu'une ligne au retour de Hektor.
- taches: 4-suite — basculer la clé des recherches sur app_search_id (case ouverte de la liste, hors liste mesurée, taille non mesurée), L10-2b — la recherche naît chez nous : durable, numérotée, rapprochée tout de suite
- ordre: 1) Ré-auditer 4-suite. La doublure app_search_id est remplie (11 455 sur 11 455). Mais contact_search_key = sha1(contact, index, contenu) change à chaque édition (build_contacts_layer.py:1477), et push_contacts_to_supabase.py:873-900 efface la nuit les clés absentes du miroir.
2) Basculer la clé : répétition sur copie, puis une nuit.
3) L10-2b :
- écrire la vraie ligne à la naissance (app_search_id_app_seq, jamais appelée à ce jour) ;
- la protéger du push nocturne ;
- la rapprocher ;
- la réconcilier au retour de Hektor.
- prerequis: Chapitre 8 (L10-2a). | Décision : quel search_index donner à une recherche née dans l'app, sans collision avec celui que Hektor attribuera (non mesuré).
- feu vert: « vas-y » (code existant). ACCORD obligatoire pour la nuit de bascule de la clé, les patchs et l'essai réel. | perime: False | taille: 3 à 5 j pour L10-2b, plus 4-suite (non mesuré)
- fin: La clé des recherches est app_search_id. Une recherche créée dans l'app a un app_search_id ≥ 1 000 000, entre au rapprochement dans la minute, survit à 2 runs de nuit, et ne fait qu'UNE ligne après le retour de Hektor.
- verif: Répétition de la bascule sur copie. Essai réel sur la cible d'essai, avec lecture de app_contact_search_current sur 2 nuits.
- gestes Frederic: Trancher le search_index. | Accorder la nuit de bascule et l'essai réel.

## CH25 — Les mandants naissent chez nous
- objectif: Un mandant ajouté dans l'app, à la création d'une annonce ou plus tard, existe chez nous durablement, avant toute réponse de Hektor, sans doublon au retour.
- taches: Registre des relations autonome — chantier du 30/09, hors liste mesurée (plan, section « LE REGISTRE DES RELATIONS DEVIENT AUTONOME »), taille non mesurée, L10-2c — les mandants saisis à la création d'une annonce sont écrits chez nous
- ordre: 1) Les 5 réponses de Frédéric, puis un ré-audit : la table est refaite chaque nuit depuis 6 sources Hektor, et l'app n'écrit qu'une ligne provisoire.
2) Contrat d'autorité entre le run et l'app, et une sentinelle.
3) L10-2c :
- la RPC de création écrit les liens ;
- relation_ledger.py l.395-433 cesse d'écarter les liens « app seule » sans numéro d'annonce ;
- le worker (l.19761-19862) ne fait plus que relayer.
- prerequis: Chapitres 20 et 21 (L10-1d, L10-1e). | Les 5 questions du registre des relations, surtout la 3 : retirer un mandant part-il chez Hektor tant qu'il vit ?
- feu vert: « vas-y » (code existant, run). ACCORD obligatoire pour les patchs, la modification du run et les essais réels. | perime: False | taille: 1 à 2 j pour L10-2c, plus le registre (non mesuré)
- fin: Un lien ajouté dans l'app survit à 2 nuits (exigence du 30/09). Une annonce créée avec 2 mandants montre 2 liens chez nous dès le geste, et toujours 2 (pas 4) après le run de nuit.
- verif: Essai réel sur la cible d'essai. Lecture de app_relation avant et après la nuit. Sentinelle du registre.
- gestes Frederic: Répondre aux 5 questions du registre des relations. | Accorder les patchs et les essais.

## CH26 — L'annuaire des négociateurs et des agences devient le nôtre
- objectif: Un collaborateur embauché après la coupure se crée dans l'app : il reçoit un numéro, un compte relié, et peut créer une annonce. Une réponse vide de Hektor ne retire personne.
- taches: L10-11-c — l'annuaire à nous, et créer un collaborateur dans l'app
- ordre: 1) Rendre NON bloquante l'étape « push hektor directory » (run_full_pipeline.ps1:1203). Le plancher est déjà posé au ch.5.
2) Une table durable delete-never et une identité propre (série, patron option B).
3) Le geste de création, et un compte « linked » sans passer par l'annuaire de Hektor (supabase_admin.py:55-157).
4) Ré-auditer app_affaire_repartition.hektor_user_id NOT NULL (commissions), commercial_id (vitrine, RDV) et les créneaux RDV (non mesurés).
- prerequis: Chapitre 5 (plancher de l'annuaire). | Chapitre 14 (tous les négociateurs ont un compte). | Revenir sur la décision du 19/09 (« un nouveau collaborateur se crée dans Hektor »). | Décision : le numéro du négociateur dans notre série.
- feu vert: « vas-y » (code existant, étape du run). ACCORD obligatoire pour les patchs, les déploiements et la création d'un négociateur d'essai. | perime: False | taille: 3 à 5 j
- fin: Un négociateur fictif créé dans l'app reçoit un numéro et un compte « linked », et crée une annonce. Une réponse vide de Hektor, simulée sur copie, ne retire personne. L'étape d'annuaire n'arrête plus le run.
- verif: Essai sur copie avec une réponse vide. Création d'un négociateur d'essai, avec accord.
- gestes Frederic: Revenir sur la décision du 19/09. | Choisir la série. | Accorder les patchs et l'essai.

## CH27 — Le côté public stable : jeton RDV, vitrine au jeton, vignettes DPE
- objectif: Un bien garde son jeton RDV, la vitrine publie ce jeton sans casser les anciens QR, une liste vide ne désactive aucun lien, et les étiquettes DPE et GES sont servies par nous.
- taches: 11bis-2 — le service de RDV lit le bien par notre numéro, 11bis-1a — rendre le jeton RDV stable (réparer les 81 annonces qui ont plusieurs jetons), L10-8e (partie liens RDV) — plancher de deactivate_out_of_scope_links, même fonction que 11bis-1a, 11bis-1b — la vitrine publie le jeton, et l'ancienne forme ?ref=<n° Hektor> répond toujours, L10-15-b — vignettes DPE/GES servies par nous (vitrine, fiche, espace client)
- ordre: 1) 11bis-2 (appointment_service.py l.203-209).
2) 11bis-1a ET le plancher RDV, ENSEMBLE, dans deactivate_out_of_scope_links (backfill_appointment_public_links.py:57-92) : réactiver l'ancien lien au lieu d'en créer un, et faire répondre les anciens jetons.
3) 11bis-1b (export_project_vitrine.py l.369, 449-450), en recouvrement.
4) L10-15-b :
- un ensemble fini d'images déposé dans gti-photo ;
- la nouvelle base dans export_app_payload.py:21 ;
- la réécriture à la lecture des adresses déjà stockées (espace_client.py:478, App.tsx:6206-6209 et 9835-9841).
- prerequis: Chapitre 5 (patron des planchers). | Chapitre 20, pour servir une annonce née dans l'app. | Décision : ce que montre un jeton dont le bien est sorti de la vitrine (404, ou page « bien plus disponible »). | Décision : copier les images de La Boîte Immo (droit d'usage ?) ou dessiner les nôtres. Juriste : faut-il afficher la classe DPE dans la vitrine (449 biens, 0 étiquette) ? | Accord de publication : ces liens sont publics (QR, mails, imprimés).
- feu vert: « vas-y » (code existant). ACCORD obligatoire pour les déploiements Render et Vercel, le script du run et toute publication de la vitrine. | perime: True | taille: 3,5 à 4,5 j
- fin: Un jeton se lit par app_dossier_id, et les anciens liens ?ref répondent. Une annonce qui sort puis revient garde son jeton. 0 nouveau jeton pour une annonce qui en a déjà un. Les jetons des 81 annonces répondent. Une liste diffusable vide ou divisée par deux ne désactive aucun lien. Le catalogue publié porte des liens au jeton : 5 anciens et 5 nouveaux liens répondent. 0 adresse staticlbi dans les détails exportés et servis.
- verif: Essai sur copie (sortie puis retour d'une annonce). Comptage des jetons par annonce avant et après. Lecture du JSON publié. Contrôle réseau d'une page d'espace client d'essai.
- gestes Frederic: Trancher le cas du jeton d'un bien sorti. | Choisir entre copier et dessiner les vignettes, et poser la question au juriste. | Accorder la publication. Si la décision est de COPIER : avant la fin du contrat La Boîte Immo, qui sert ces images.

## CH28 — Le registre des mandats lit nos tables, et le mandat créé dans l'app est complet
- objectif: Le registre légal est bâti depuis app_mandat et comparé à l'ancien tant que Hektor vit. Un mandat créé dans l'app porte tout son contenu sans attendre le run.
- taches: A.3-c — détacher le registre du miroir : il lit app_mandat, avec une clé sur notre numéro d'annonce, A.3-d — le mandat créé depuis l'app porte son contenu COMPLET dès la création
- ordre: 1) A.3-c : un constructeur neuf à côté de export_app_payload.py:735-760, une sentinelle de comparaison chaque nuit, puis la bascule par réglage après plusieurs nuits à 0 écart. mandat_ledger.py:538-566 cesse alors de réécrire depuis le miroir.
2) A.3-d : une fonction partagée côté Supabase pour famille, nature, versions_json et mandants. Les règles Python de mandat_ledger.py ne sont PAS recopiées en JS.
- prerequis: Chapitre 2 (A.3-a). | Chapitres 20 et 21 (L10-1 : app_mandat_couple_unique, le carnet). | Chapitre 25 (L10-2c : les mandants à la création). | Chapitre 15 (C.13-c câblé).
- feu vert: « vas-y » (code existant, run). ACCORD obligatoire pour la bascule (écran légal), les patchs et le redémarrage. | perime: True | taille: 5 à 8 j
- fin: Le registre est bâti depuis app_mandat, avec 0 écart contre l'ancien sur les 24 494 lignes, plusieurs nuits de suite. Un mandat posé sur une annonce sans numéro Hektor y figure. Un mandat créé dans l'app, run arrêté, a famille, nature, type, dates et mandants identiques à ce que le run aurait posé.
- verif: Sentinelle de comparaison nocturne. Essai sur copie, comparé à la ligne bâtie par le run sur un mandat réel.
- gestes Frederic: Accorder la bascule après les nuits à 0 écart.

## CH29 — La série légale des numéros de mandat, et l'avenant complet
- objectif: L'app sait attribuer le numéro légal (vente, recherche, avenant) sans trou ni doublon, dans la série décidée. L'avenant sait changer les dates et la durée, pas seulement le prix.
- taches: A.3-e — la série LÉGALE des numéros de mandat : le distributeur (dormant jusqu'au jour J) et les chemins vente, recherche et avenant, L10-12-c — l'avenant complet (dates, durée, prolongation)
- ordre: 1) A.3-e :
- une table de compteur verrouillée et une fonction SECURITY DEFINER ;
- un test de 1 000 tirages concurrents sur une copie ou une branche ;
- le point de départ justifié par l'export PROTEXA ;
- les chemins du mandat de recherche et de l'avenant.
La porte app_console_create_mandat_auto_number_job existe déjà.
2) L10-12-c : mandat-template.html et le générateur generate_mandat_document (l.7413). L'avenant est numéroté dans la série.
- prerequis: Chapitre 28 (A.3-c). | Chapitres 13 et 15 (G.5-d, E.0-bis-d1). | Question 1 : continuer la série PROTEXA ou repartir de 0, écrite au journal des décisions. | L'EXPORT COMPLET PROTEXA reçu (25 trous de 2026 restent inexpliqués). | Juriste : mentions et forme.
- feu vert: ACCORD obligatoire pour le compteur en prod. « vas-y » pour L10-12-c, avec accord pour ses essais réels. Le distributeur reste dormant jusqu'au jour J. | perime: True | taille: 6 à 9 j
- fin: 1 000 tirages concurrents : 0 trou et 0 doublon. Vente, recherche et avenant partagent la série, et le point de départ est justifié par l'export. Un avenant de prolongation d'essai change les dates du mandat chez nous et entre au registre.
- verif: Test de concurrence sur une branche. Relecture par le juriste. Essai réel sur l'annonce d'essai.
- gestes Frederic: Répondre à la question 1 et l'écrire au journal. | Obtenir l'export PROTEXA. | Consulter le juriste.

## CH30 — L'inaltérabilité du registre des mandats
- objectif: Toute modification d'une colonne légale laisse une trace datée et chaînée, rien ne peut l'effacer, et une empreinte quotidienne est horodatée par un tiers.
- taches: A.3-f — journal en ajout seul, déclencheur, retrait des droits UPDATE/DELETE, horodatage tiers
- ordre: 1) Une table de journal et un déclencheur sur app_mandat, essayés sur une branche.
2) Retirer les droits UPDATE et DELETE sur les colonnes légales, y compris pour la clé de service.
3) Une empreinte quotidienne horodatée par le prestataire.
4) Surveiller le push nocturne de app_mandat pendant 3 nuits.
- prerequis: Chapitre 15 (C.13-c : l'écriture de masse avant le scellement). | Chapitre 28 (A.3-c : sinon le run écrirait chaque nuit des milliers de « modifications »). | Chapitre 29 (A.3-e). | Contrat du prestataire d'horodatage. | Juriste : le niveau de preuve exigé.
- feu vert: ACCORD obligatoire : droits et déclencheur en prod. | perime: False | taille: 3 à 5 j
- fin: Toute modification d'une colonne légale laisse une trace datée et chaînée. Un effacement est refusé, même par service_role. Une empreinte quotidienne est horodatée par un tiers. Le push nocturne de app_mandat réussit 3 nuits de suite.
- verif: Sur une branche Supabase : UPDATE et DELETE refusés, chaîne vérifiée. Puis le journal du run réel.
- gestes Frederic: Signer avec le prestataire d'horodatage. | Faire fixer le niveau de preuve par le juriste. | Accorder le patch.

## CH31 — Notre bon de visite, et l'offre d'achat
- objectif: Un bon de visite numéroté, sur plusieurs biens, avec l'acquéreur nommé, est archivé chez nous. Une offre d'achat se fabrique, s'archive et se rattache à son affaire.
- taches: L10-12-a — notre bon de visite : un objet visite, une série, un PDF archivé, plusieurs biens, L10-12-b — le générateur de l'offre d'achat
- ordre: 1) L10-12-a :
- reprendre la table « visite » si le ch.16 l'a créée, sinon la créer avec sa séquence ;
- plusieurs biens, acquéreur nommé ;
- un générateur PDF côté worker, sur le patron du mandat ;
- le nouveau type de travail dans app_console_claim_next_job ET dans DOCUMENT_JOB_TYPES ;
- l'archivage par G.5 ;
- signature manuscrite d'abord (l'électronique viendra avec A.2).
Dormant derrière un réglage, puis ouvert aux négociateurs.
2) L10-12-b : un modèle HTML neuf et un générateur sur le patron de generate_mandat_document. Le PDF crée sa ligne (G.5-d) et se rattache à la transaction.
- prerequis: Chapitres 12 et 13 (G.5-b, G.5-d). | Chapitre 9 (les travaux generate_* ouverts aux commerciaux). | Chapitres 20 et 21 (L10-1 ; 26bis-TRANSACTIONS pour l'offre). | Chapitre 7 (app_record_proposition n'est plus exécutable par anon). | Question 2 : notre bon, sur plusieurs biens, dans une série. | Le texte de l'offre, validé par Frédéric ou le juriste.
- feu vert: « vas-y » pour le code. ACCORD obligatoire pour la table, le distributeur, le redémarrage, le déploiement et les essais réels. | perime: False | taille: 6 à 9 j
- fin: Un bon d'essai est numéroté dans la série et porte plusieurs biens et l'acquéreur. Son PDF est dans app_console_document et visible dans l'app. Les bons de Hektor (environ 115 par mois) continuent pendant ce temps. Une offre d'essai est générée, archivée et rattachée à son affaire.
- verif: Essais réels sur une annonce et une affaire d'essai. Requêtes sur la table visite et sur app_console_document.
- gestes Frederic: Choisir le mode de signature du bon. | Valider le texte de l'offre. | Accorder les essais.

## CH32 — La signature électronique en propre (1/2) : envoyer et suivre
- objectif: Un mandat part en signature depuis l'app, chez NOTRE prestataire, et son état remonte sans ouvrir Hektor.
- taches: A.2 (partie 1) — envoi au prestataire depuis notre coffre, webhooks, état de la procédure, derrière un réglage
- ordre: 1) Lire l'API du prestataire choisi.
2) L'envoi du PDF pris dans notre coffre (G.5).
3) Les webhooks et la table d'état.
4) Un écran et un bouton derrière un réglage éteint.
Les 16 scripts Console/immosign_*.js (hors git, ils lisent le jeton dans l'iframe Hektor) ne sont pas réutilisés.
- prerequis: Le contrat du prestataire (hors code), ou une exception assumée. | Chapitres 12-13 (le PDF du mandat chez nous d'abord), 29 (le numéro de notre série imprimé sur le PDF) et 31 (les bons de visite se signent aussi).
- feu vert: J'enchaîne sans attendre pour le code dormant. ACCORD obligatoire pour les déploiements et les essais réels (Frédéric seul signataire). | perime: False | taille: 4 à 8 j après le contrat. Peut remonter si le contrat arrive tôt : il ne dépend que de G.5 et de A.3-e.
- fin: Un mandat d'essai part depuis l'app chez le prestataire, et son état (envoyé, vu, signé, refusé) remonte par webhook dans l'app, sans ouvrir Hektor. Réglage éteint : rien ne change.
- verif: Essai réel avec Frédéric comme seul signataire (règle des essais de signature), puis lecture de la table d'état.
- gestes Frederic: Signer le contrat du prestataire. | Être le seul signataire des essais. | Continuer de solder les procédures ImmoSign dans Hektor.

## CH33 — La signature (2/2), et prolonger un mandat par avenant
- objectif: Le PDF signé et ses preuves sont chez nous, relance et annulation marchent, et une prolongation de mandat se fait de bout en bout dans l'app.
- taches: A.2 (partie 2) — rapatriement du PDF signé et des preuves, relance, annulation, boutons « Signature » qui n'ouvrent plus Hektor (App.tsx:5427-5433, 10777, 11021), E.0-bis-d2 — prolonger un mandat existant par avenant (numéroté, signé, archivé)
- ordre: 1) A.2, partie 2 :
- PDF signé et ZIP de preuves rangés dans le coffre et dans app_console_document ;
- relance, puis annulation ;
- boutons derrière le réglage.
2) E.0-bis-d2 : l'avenant de L10-12-c, numéroté par A.3-e, signé par A.2 et archivé par G.5. Mise à jour de date_fin, avenants_json, avenant_count et du carnet.
- prerequis: Chapitre 32. | Chapitres 29 (L10-12-c, A.3-e) et 15 (E.0-bis-d1). | Juriste : la forme de l'avenant de prolongation.
- feu vert: J'enchaîne sans attendre pour A.2 (dormant). « vas-y » pour E.0-bis-d2. ACCORD obligatoire pour les déploiements et les essais réels (Frédéric seul signataire). | perime: False | taille: 6 à 10 j
- fin: Le PDF signé et les preuves du mandat d'essai sont chez nous. Relance et annulation sont vérifiées. Réglage allumé : aucun bouton « Signature » n'ouvre Hektor. Un avenant de prolongation d'essai est généré, numéroté, signé et archivé. date_fin et avenants_json sont à jour, et le registre l'affiche.
- verif: Essai de bout en bout sur l'annonce d'essai, Frédéric seul signataire. Contrôle du ZIP de preuves. Recherche dans le paquet du front.
- gestes Frederic: Faire valider la forme de l'avenant par le juriste. | Être le seul signataire des essais.

## CH34 — La diffusion (1/2) : notre flux d'annonces
- objectif: Toutes les annonces diffusables sortent chaque nuit dans un flux au format du diffuseur, avec nos propres références stables, sans dépendre de l'API Hektor.
- taches: A.1 (partie 1) — le générateur de flux, produit chaque nuit et validé en recette, mais non envoyé en production
- ordre: 1) Le format du diffuseur.
2) Le générateur, depuis le corps tenu chez nous (app_dossier_current et app_dossier_detail_current), nos photos et nos vignettes DPE.
3) Les références : numéro de mandat (Leboncoin affiche « 18689 ») et numéro de dossier (« VM66272 »).
4) Production chaque nuit, sans envoi, puis recette.
- prerequis: Contrat avec un diffuseur ou des portails au nom de GTI (hors code). | Chapitres 19 (corps), 22 (numéro de dossier), 23 (diffusable), 27 (DPE), 29 (numéro de mandat) et 12 (photos neuves).
- feu vert: J'enchaîne sans attendre (le flux est produit, pas envoyé). ACCORD obligatoire pour la recette avec le diffuseur. | perime: False | taille: 5 à 10 j après le contrat
- fin: Le flux de toutes les annonces diffusables est produit chaque nuit et validé en recette par le diffuseur, avec des références stables d'une nuit à l'autre. Rien n'est envoyé en production.
- verif: Retour de recette du diffuseur. Compte des annonces du flux contre les annonces diffusables.
- gestes Frederic: Signer le contrat du diffuseur. | Accorder la recette.

## CH35 — La diffusion (2/2) : suivi, reprise des 346 annonces en ligne, retrait de l'API Hektor
- objectif: On sait ce qui est réellement publié, les 346 annonces en ligne passent sur notre flux sans disparaître des portails, et plus aucun code n'appelle l'API de diffusion de Hektor.
- taches: A.1 (partie 2) — suivi de publication, retours d'erreur, reprise des 346 annonces, puis retrait des 4 copies de l'appel à l'API Hektor
- ordre: 1) Le suivi et les retours d'erreur.
2) La table de correspondance des références des 346 annonces, préparée pendant que Hektor diffuse encore.
3) La reprise éprouvée en recette, puis la bascule par lots.
4) Les 4 copies obéissent à l'interrupteur, puis sont retirées : backend/app/services/hektor_bridge.py, la fonction Edge (si elle existe encore), phase2/sync/hektor_diffusion_writeback.py, phase2/sync/test_annonce_passerelles.py. Le front « activer les passerelles après la baisse » (App.tsx:16832-16858) passe par notre flux.
- prerequis: Chapitre 34. | Chapitre 18 (l'interrupteur). | Décision : comment reprendre les 346 annonces en ligne.
- feu vert: « vas-y » pour retirer du code existant. ACCORD obligatoire pour chaque bascule de diffusion (publication sur les portails). | perime: True | taille: 5 à 10 j
- fin: Le suivi dit ce qui est réellement publié, comparé aux 1 536 diffusions remontées de Hektor. Les 346 annonces sont reprises sans coupure. Interrupteur forcé : aucune des 4 copies n'appelle Hektor.
- verif: Comparaison avec app_mandat_broadcast_current. Essais en recette. grep des appels restants. Essai sur copie avec l'interrupteur forcé.
- gestes Frederic: Valider le plan de reprise avec le diffuseur. | Accorder chaque lot de bascule.

## CH36 — Les leads des portails entrent dans l'app
- objectif: Une demande d'un portail arrive dans l'app en moins de 15 minutes, rattachée au bon bien et au bon négociateur, sans doublon de contact.
- taches: A.5-b — l'entrée des demandes : contact (retrouvé ou créé), recherche durable, lien au bien, notification, et import de l'historique s'il est décidé
- ordre: 1) Lecteur du canal retenu, en mode mesure.
2) Recherche de contact existante avant toute création.
3) Recherche durable (ch.24) et lien au bien par la référence portail.
4) Notification du négociateur.
5) Une semaine rejouée en mode mesure, puis l'allumage.
6) Traitement de l'historique capturé au ch.16, s'il y en a un.
- prerequis: Chapitre 3 (A.5-a : le canal). | Chapitres 24 (la recherche naît chez nous), 26 (le bon négociateur), 22, 34 et 35 (de la référence portail au bien). | Le worker Leboncoin Pro (en attente au palier 1), si le canal LBC est lead-center. | Décision : le canal retenu, et l'import de l'historique depuis le 01/02.
- feu vert: J'enchaîne sans attendre pour le code dormant. ACCORD obligatoire pour l'allumage et pour l'import de l'historique. | perime: False | taille: 3 à 5 j (inconnu tant que A.5-a n'a pas parlé)
- fin: Un lead réel arrive dans l'app en moins de 15 min, rattaché au bon bien et au bon négociateur, sans doublon de contact. Une semaine rejouée en mode mesure correspond au canal actuel.
- verif: Rejeu d'une semaine de leads réels en mode mesure. Compte des doublons de contacts.
- gestes Frederic: Choisir le canal et décider de l'import de l'historique. | Décider de reprendre le worker Leboncoin Pro. | Accorder l'allumage.

## CH37 — Gérer les photos dans l'app : supprimer, réordonner, choisir la principale
- objectif: Un négociateur range ses photos dans l'app, et Hektor (donc les portails) suit tant qu'il diffuse.
- taches: E.0-bis-c2 — supprimer, réordonner, choisir la photo principale dans l'app
- ordre: 1) Découvrir l'appel Hektor qui supprime ou réordonne (lecture, avec accord ; non mesuré).
2) RPC « l'app d'abord » et écran.
3) Deux travaux du worker (suppression, ordre), ajoutés au distributeur ET à la liste du worker.
4) Contrat pour que le run n'écrase pas.
5) Essai sur l'annonce 62966.
- prerequis: Chapitres 12 (G.5-e, E.0-bis-c1), 20 (clé des photos sans numéro Hektor) et 9 (droits sur les photos). | Décision : pendant la cohabitation, pousser l'ordre et les retraits chez Hektor (recommandé, les portails passent par lui), ou accepter que les portails divergent jusqu'au ch.35.
- feu vert: « vas-y » (code existant). ACCORD obligatoire pour l'écriture chez Hektor (donc sur les portails) sur l'annonce d'essai, le redémarrage et le déploiement. | perime: False | taille: 3 à 5 j
- fin: Sur l'annonce d'essai, la suppression, l'ordre et la photo principale se voient tout de suite, tiennent après un run et arrivent chez Hektor.
- verif: Essai réel sur l'annonce 62966. Requêtes sur app_console_photo avant et après le run. Lecture de la galerie chez Hektor.
- gestes Frederic: Trancher l'envoi chez Hektor pendant la cohabitation. | Accorder l'essai réel.

## CH38 — Reprendre un brouillon, et supprimer « l'app d'abord » (dormant jusqu'au jour J)
- objectif: Un brouillon s'achève dans l'app jusqu'à devenir une annonce. Une suppression d'annonce, de contact ou de document se fait chez nous, sans que la nuit la fasse revenir.
- taches: E.0-bis-f (étape 2) — ouvrir un brouillon dans l'assistant prérempli, et le finaliser sans Hektor, E.0-bis-g — suppressions « l'app d'abord », avec une pierre tombale respectée par le run
- ordre: 1) E.0-bis-f : ouvrir le brouillon depuis app_brouillon_annonce_detail_cache (rempli au ch.16). Ajouter la branche ÉCRITURE de loadDossier à côté de la branche lecture du ch.2. Puis la finalisation.
2) E.0-bis-g : suppression douce chez nous, pierre tombale respectée chaque nuit par le run (app_console_deleted_annonce_log existe), réglage du jour J éteint.
- prerequis: Chapitres 2 (G.1-b-2), 16 (détail des brouillons), 19 (L10-2d) et 20 à 22 (L10-1, G.5-f). | Question 4 : après la coupure, les suppressions sont-elles réservées à l'admin ? | Décision : reprendre les 508 brouillons Hektor, ou seulement ceux nés dans l'app.
- feu vert: « vas-y » (code existant). ACCORD obligatoire pour l'essai sur un brouillon d'essai (écriture chez Hektor), les patchs, le redémarrage et les déploiements. | perime: False | taille: 4 à 6 j
- fin: Un brouillon s'ouvre dans l'app avec tous ses champs, se complète et devient une annonce, sans ouvrir Hektor. Réglage allumé sur copie : une annonce sans numéro Hektor se supprime, disparaît des écrans, reste au journal et ne revient pas après un run. Réglage éteint : comportement identique à aujourd'hui.
- verif: Essai réel sur un brouillon d'essai. Essai sur copie, puis un run partiel.
- gestes Frederic: Répondre à la question 4. | Choisir le périmètre des brouillons à reprendre. | Accorder les essais.

## CH39 — Fusionner les doublons de contacts dans l'app
- objectif: Deux fiches d'une même personne se fusionnent dans l'app, de façon réversible, sans perdre de lien et sans résurrection la nuit.
- taches: E.0-bis-e — la fusion (aujourd'hui « Comparer & fusionner » ouvre Hektor)
- ordre: 1) Mesurer la détection actuelle (app_contact_duplicate_group_current : 0 ligne au cloud).
2) Un alias « absorbé → survivant », réversible et delete-never, respecté par le registre d'identité du run.
3) Re-pointer les quelque 20 tables qui portent app_contact_id (app_relation, app_search_registry, app_affaire_ledger, documents, RDV, rapprochements).
4) L'annulation.
5) L'écran.
- prerequis: Chapitre 9 (si la fusion est ouverte aux commerciaux). | Question 4 : la fusion est-elle réservée à l'admin ? | Décision : pendant la cohabitation, fusionner aussi chez Hektor (handler non mesuré), ou laisser Hektor garder 2 fiches et faire respecter notre alias par le run.
- feu vert: « vas-y » (code existant). ACCORD obligatoire pour les patchs et les essais. | perime: False | taille: 4 à 6 j (peut glisser après la coupure si le calendrier serre : aucune donnée ne se perd, le bouton serait masqué au jour J)
- fin: Deux fiches d'essai fusionnées donnent un seul contact à l'écran, tous les liens rattachés, et aucune résurrection après un run. L'annulation rend l'état d'avant.
- verif: Essai sur copie avec le ménage d'essai (cible GONZALEZ / Firminy). Comptes des liens avant et après.
- gestes Frederic: Répondre à la question 4 et trancher la fusion chez Hektor. | Dire si la fusion passe avant ou après la coupure.

## CH40 — Ce que Hektor envoyait aux clients, envoyé par l'app
- objectif: L'email RGPD et « Espace personnel » d'un nouveau contact part de l'app, avec le consentement gardé chez nous. Les automatismes CRM partent aussi de l'app s'ils servent, une seule fois, à partir du jour J.
- taches: L10-13-b — l'email RGPD / « Espace personnel » envoyé par l'app, L10-13-c — les automatismes CRM (nouveau mandat, échéance, anniversaire), SEULEMENT si la question 8 dit qu'ils servent ; sinon la tâche sort de la liste
- ordre: 1) L10-13-b : une colonne de suivi du consentement, et l'envoi Gmail du backend derrière un réglage. Allumé, il n'envoie plus _email_rgpd à Hektor (console_job_worker.js:15791, 15879-15880). Essai sur l'email de Frédéric seulement.
2) L10-13-c : seulement les automatismes retenus, en run à blanc sur une semaine, avec la liste des envois relue.
Les deux restent éteints jusqu'au jour J, ou jusqu'à leur extinction chez Hektor (sinon le client reçoit 2 mails).
- prerequis: Chapitres 3 et 16 (L10-13-a). | A.4 fait, hors code : SPF, DKIM et DMARC de gti-immobilier.fr sortis de la zone de La Boîte Immo. | Chapitres 15 (pas de mail d'échéance sur un mandat clos), 28 (dates fiables) et 26 (l'expéditeur est le négociateur). | Question 8. | Décision : lever pour ces cas le blocage volontaire RELANCE_AUTO_SEND_ENABLED ? L'espace client de l'app remplace-t-il l'« Espace personnel » de Hektor ?
- feu vert: J'enchaîne sans attendre pour L10-13-b (dormant). « vas-y » pour L10-13-c (relance_worker existant). ACCORD obligatoire pour tout allumage : ce sont des envois à des clients. | perime: False | taille: 1 à 2 j, plus 3 à 5 j si les automatismes servent
- fin: Réglage allumé : un contact créé reçoit l'email depuis l'app, son consentement est enregistré chez nous, et _email_rgpd n'est plus envoyé à Hektor. Pour chaque automatisme retenu, la liste des envois prévus sur une semaine à blanc est relue, avec 0 doublon.
- verif: Essai avec l'email de Frédéric seulement. Run à blanc sur une semaine de données.
- gestes Frederic: Répondre à la question 8. | Décider du blocage des envois et de l'espace client. | Faire A.4. | Relire la liste des envois.

## CH41 — La vitrine depuis Supabase, et la bascule du corps serveur prête (dormante)
- objectif: Tant que les deux sources vivent, on prouve que la vitrine fabriquée depuis Supabase égale celle fabriquée depuis le miroir, et que le corps serveur de l'annonce peut venir du cloud.
- taches: L10-7c — la vitrine publique fabriquée depuis Supabase, 26bis-3c — la source du corps serveur de l'annonce : la copie du cloud au lieu du miroir, derrière un interrupteur éteint
- ordre: 1) L10-7c, en dry-run (sans --push-github) : diff des deux sorties sur les 449 biens, le même matin.
2) 26bis-3c : une source alternative derrière un interrupteur ÉTEINT, et une comparaison ligne à ligne sur les 13 463 annonces, sur copie. Mesurer d'abord la capacité de la descente pour app_dossier_detail_current (environ 370 Mo ; Supabase a saturé le 01/10).
- prerequis: Chapitres 17 (26bis-3b), 19 (26bis-3a), 11 (L10-3a), 23 (L10-4), 26 (L10-11-c), 20 à 22 (L10-1) et 5 (planchers). | Décision : basculer 26bis-3c à la coupure, ou avant, champ par champ. | Question 6.
- feu vert: « vas-y » (code existant, dormant). ACCORD obligatoire pour toute publication de la vitrine. | perime: True | taille: 3,5 à 5 j
- fin: La sortie vitrine Supabase est identique à la sortie miroir sur l'ensemble des biens publiés, ou chaque écart est expliqué. Interrupteur allumé sur copie : app_view_generale refaite depuis le cloud a 0 écart non expliqué sur 13 463 annonces, et le push nocturne ne change aucune ligne.
- verif: Diff des deux fichiers produits le même matin. Run complet sur copie et comparaison ligne à ligne.
- gestes Frederic: Choisir le moment de la bascule du corps. | Accorder la publication si elle est demandée.

## CH42 — Le run d'après la coupure, et notre fiche visite
- objectif: Un run de nuit sans un seul appel à Hektor produit vitrine, dérivés, adresses et liens RDV, et la fiche visite publique est la nôtre.
- taches: L10-7b — le run d'après (script neuf scheduled/run_apres_coupure.ps1, non planifié), L10-15-d — la fiche visite PDF faite par nous (remplace pdf.php)
- ordre: 1) L10-7b : réutiliser les étapes indépendantes classées au ch.3 (L10-7a), sans sync_raw, normalize_source, l'annuaire Hektor, push_upgrade ni les ledgers, avec sa reprise et ses heartbeats. Répétition sur copie.
2) L10-15-d : un générateur neuf branché dans build_listing_url (export_project_vitrine.py:359-366) et buildListingSheetUrl (apps/rdv-public/app.js:169-173). L'adresse pdf.php reste servie tant que Hektor vit.
- prerequis: Chapitres 3 (L10-7a), 18 (L10-6b), 41 (26bis-3c, L10-7c), 26 (L10-11-c), 12-13 (G.5) et 27 (L10-15-b). | Décision à acter : après la coupure, plus AUCUN push du miroir vers Supabase. | Décision : la forme de la fiche visite (page imprimable ou PDF de nuit).
- feu vert: J'enchaîne sans attendre pour le script neuf non planifié et le générateur (additifs). ACCORD obligatoire pour toute planification et toute publication. | perime: False | taille: 3,5 à 5 j
- fin: Sur copie, le run d'après tourne de bout en bout sans un seul appel à Hektor (journal réseau) et produit vitrine, dérivés et liens RDV. La vitrine et la page RDV pointent vers notre fiche, et l'export ne contient plus aucun lien pdf.php.
- verif: Répétition sur copie avec le journal réseau. grep « pdf.php » sur un export d'essai.
- gestes Frederic: Acter la fin du push du miroir après la coupure. | Choisir la forme de la fiche visite.

## CH43 — Sauvegarde et surveillance de l'après (dormantes)
- objectif: Après la coupure, on sauvegarde ce qui vient de Supabase, après la descente. Une vraie restauration est prouvée. Une machine extérieure prévient si le serveur meurt. Les sentinelles ne crient plus à tort.
- taches: L10-9d — inverser la doctrine de sauvegarde (dormant), L10-9e — export régulier de Supabase (pg_dump ou équivalent), L10-9f — éprouver trois restaurations : phase2.sqlite, le miroir, Supabase, L10-10f — un témoin extérieur, L10-10g — les sentinelles de l'après (dormantes)
- ordre: 1) L10-9d : une liste « après coupure » activée par l'interrupteur. Déplacer « GTI Sauvegarde » (08:00) après « GTI Descente » (08:15) peut se faire dès maintenant si Frédéric l'accorde.
2) L10-9e, dès que les outils sont installés. Il peut remonter au ch.6 si Frédéric les installe tôt.
3) L10-9f : trois restaurations sur copies, avec leur durée.
4) L10-10f : tâche planifiée Render ou service tiers.
5) L10-10g : la joignabilité de Hektor (l.1564) et la fraîcheur de sqlite.hektor (l.2444) s'éteignent, les sentinelles d'identité se réveillent.
- prerequis: Chapitres 18 (L10-6b), 6 (L10-9a, L10-9c) et 4 (L10-10c). | Frédéric installe les outils clients PostgreSQL et pose LUI-MÊME la chaîne de connexion (c'est un secret). | Non mesuré : PITR et rétention Supabase, à lire dans la console. | Accord pour le coût d'une branche ou d'un projet d'essai ; choix et coût du témoin extérieur ; nouvel horaire de GTI Sauvegarde.
- feu vert: « vas-y » pour L10-9d et L10-10g (code existant, dormant). ACCORD obligatoire pour L10-9e, L10-9f (branche payante), L10-10f (déploiement Render), le changement d'horaire et la suspension d'essai du moniteur. | perime: False | taille: 4 à 6,5 j
- fin: Interrupteur forcé sur copie : le fichier quotidien contient les tables descendues, daté après la descente. Un export Supabase daté existe. Trois restaurations réussissent, avec les mêmes comptes sur 5 tables témoins et une durée mesurée. Moniteur arrêté, ou pipeline.full vieux de plus de 26 h : un mail part d'une autre machine. Moniteur lancé interrupteur forcé : 0 alerte « Hektor » ou « miroir figé », et les sentinelles d'identité lisent des lignes.
- verif: Essais sur copie. PRAGMA integrity_check. Quelques RPC de lecture sur la base restaurée. Suspension courte de « GTI Health Monitor » avec accord.
- gestes Frederic: Installer les outils et poser le secret. | Lire la PITR dans la console Supabase. | Choisir le témoin extérieur. | Accorder les coûts et les horaires.

## CH44 — L'écran sans Hektor (dormant)
- objectif: En mode « sans Hektor », aucun bouton n'ouvre Hektor et aucun libellé d'état ne parle de Hektor. Chaque geste garde son chemin, et un vrai conflit reste visible.
- taches: E.3 — les workers deviennent invisibles à l'écran (environ 40 libellés, mobile et desktop), E.0-bis-b — un interrupteur qui fait disparaître les 16 entrées « Ouvrir Hektor » le jour J
- ordre: 1) E.3 derrière l'interrupteur, dans les deux cascades d'écrans.
2) E.0-bis-b : une variable de build, allumée par défaut. D'abord les 4 portes centrales (App.tsx:8648-8680), puis les autres points d'entrée.
3) Build tsc -b des deux variantes, recherche dans le paquet, parcours des écrans.
- prerequis: Chapitres 18 (interrupteur) et 14 (avertissement d'échec éprouvé par le pilote). | Les gestes de remplacement : 11 (statuts), 23 (prix), 15 (mandat), 33 (signature), 37 (photos), 38 (brouillon), 39 (fusion, ou bouton masqué et annoncé si elle glisse). | Décision : allumer E.3 au jour J, ou dès la fin du pilote.
- feu vert: « vas-y » pour E.3. J'enchaîne sans attendre pour E.0-bis-b (dormant, allumé par défaut). ACCORD obligatoire pour le déploiement Vercel. | perime: False | taille: 2,5 à 3,5 j
- fin: Mode « sans Hektor », en mobile et en desktop : aucun libellé « Hektor » d'état de travail, un conflit reste visible, aucun bouton n'ouvre Hektor, et chaque écran garde un chemin pour faire son geste. Mode normal : identique à aujourd'hui.
- verif: Build des deux variantes. Recherche dans dist. Parcours des écrans en local avec l'interrupteur forcé.
- gestes Frederic: Choisir le moment d'allumer E.3. | Accorder le déploiement.

## CH45 — La fenêtre finale : rapatrier les derniers restes pendant que Hektor vit
- objectif: La veille de la coupure, il ne reste rien chez Hektor qui n'ait été rapatrié, ou abandonné par écrit. Le carnet du jour J est réécrit et répété.
- taches: E.1d — le contrôle de complétude de la fenêtre finale (documents, photos, PROTEXA), E.4a — le carnet du jour J, réécrit et daté (v1 au ch.3), E.1a — le rattrapage final des recherches acquéreurs (71 337 fiches, plusieurs sessions), E.1c — solde final : 0 procédure de signature ouverte, PDF signés et preuves rapatriés, L10-9c (2e partie) — la copie figée du miroir le jour J
- ordre: 1) E.1d : une sonde en lecture seule (documents indexés sans fichier, parc vivant non relu depuis X jours, photos sans fichier, export PROTEXA reçu).
2) E.4a réécrit : ordre, retour arrière de chaque pas, responsable. Répétition à blanc sur copie.
3) Gel des saisies dans Hektor.
4) E.1a : plusieurs sessions d'environ 33 min, en vagues de 2 000, à cadence imposée, commencées plusieurs jours avant la coupure et APRÈS la date de gel. Outil existant : scheduled/run_rattrapage_acquereurs.ps1, reprise par -StartAfterId.
5) E.1c : la sonde à 0.
6) La copie figée du miroir.
- prerequis: Chapitres 1 à 44. | Dates de gel des saisies et de coupure (aucune n'est fixée). | Geste de Frédéric : solder les procédures de signature en cours.
- feu vert: J'enchaîne sans attendre pour les sondes et le carnet. ACCORD obligatoire pour chaque session de rattrapage (risque de bannissement d'IP, déjà vécu les 20 et 22/08). | perime: True | taille: 1 à 2 j de code et d'écrit, plus plusieurs sessions d'environ 33 min sur plusieurs jours
- fin: Toutes les fiches acquéreurs relues après la date de gel, 0 lot en échec non repris. La sonde E.1d est à 0 sur chaque ligne, ou chaque reste est accepté par écrit par Frédéric. 0 procédure ImmoSign ouverte, et PDF signés et preuves rapatriés. Le carnet est daté et répété à blanc. La copie figée s'ouvre en mode ro, avec les mêmes comptes que la source.
- verif: Journal du rattrapage (dernier identifiant, lots OK) et comptes des recherches avant et après. Sonde E.1d le matin du jour J. Contrôle des ZIP de preuves.
- gestes Frederic: Fixer les dates de gel et de coupure. | Finir de solder les signatures. | Accepter par écrit les restes éventuels. | Accorder chaque session.

## CH46 — Le jour J : répétition sur copie, puis la coupure
- objectif: Le serveur et l'app vivent une semaine sans Hektor, sans perte ni fausse alerte.
- taches: E.4b — répétition sur copie (la semaine sans Hektor du critère de L10), puis exécution du carnet
- ordre: 1) Répétition complète sur copie, interrupteur allumé, avec le run d'après, pendant une semaine.
2) Le jour J, dans l'ordre de L10-6a, et AVANT la fin de l'accès à Hektor :
- dernier run ;
- interrupteur allumé ;
- tâches et services éteints ;
- run d'après planifié ;
- sauvegarde inversée ;
- sentinelles basculées ;
- E.3 et E.0-bis-b allumés ;
- série légale et signature en propre en service.
3) Contrôles à J+1 et J+7.
4) Ensuite (après la coupure) : G.4 refait comme réaction au geste « restaurer » de l'app, puis la purge G.3 après la restauration éprouvée du ch.43.
- prerequis: Chapitres 1 à 45. | Hors code : A.1 à A.5 réglés (DNS et site, contrats, leads, PROTEXA), juriste consulté. | Les questions 1 à 8 tranchées. | Les dates du préavis et de la coupure.
- feu vert: ACCORD obligatoire, pas à pas : tâches, services, app_setting, cron, Render, Vercel. | perime: True | taille: 1 à 2 j de répétition, 1 j d'exécution, puis la semaine d'observation
- fin: Le critère du lot L10 : le serveur et l'app vivent une semaine sans Hektor, sans perte ni fausse alerte.
- verif: Sentinelles L10-10, témoin extérieur, sonde de complétude E.1d à J+1 et à J+7.
- gestes Frederic: Fixer la date. | Donner chaque accord du carnet. | Prévenir les négociateurs. | Être présent le jour J et vérifier à J+1 et J+7.

## EN PARALLELE HORS CODE
- AVANT LE 08/10 À 21:00 (la seule heure limite) : fixer la taille du lot des ventes (proposition : 400 la 1re nuit, puis 400 à 600) et dire « vas-y » pour le ch.1. Filet si rien n'est prêt : désactiver la tâche « GTI Rattrapage Documents » une nuit. Rappel mesuré : le débordement a déjà fait refuser l'étape chauffage le 05/10.
- DÈS MAINTENANT : dire quoi faire des 15 travaux en erreur (ch.1), si les 508 brouillons valent le rattrapage (ch.2), et accepter ou non d'allumer G.6 avant la fin du rattrapage (ch.4, inverse la règle D.0-g).
- DÈS CETTE SEMAINE : créer depuis l'app le ménage d'essai C.9-couple-a (environ 1 h ; c'est une écriture chez Hektor, donc un accord). Je lance ensuite les deux sondes (ch.3).
- A.4, ZONE DNS, avant tout préavis : demander à La Boîte Immo l'export complet de la zone gti-immobilier.fr (MX Google de toute l'agence, SPF, DKIM, DMARC), la recréer à l'identique chez OVH, puis basculer les serveurs DNS en GARDANT www vers la machine de Hektor (l'admin et le worker y passent depuis le 11/09). Ensuite seulement, décider où héberger le site public. Débloque les ch.40 et 42.
- A.5, LEADS, et la question 8 : demander aux négociateurs où ils voient aujourd'hui une demande Leboncoin, Bien'ici ou SeLoger. Accorder la LECTURE du module Leads de Hektor et du centre de leads LBC, sans ouvrir aucun détail (ch.3). Le worker Leboncoin Pro, en attente au palier 1, en dépend.
- A.3, PROTEXA : demander maintenant l'export complet de la série (25 trous de 2026). Il périt avec Hektor et sert au ch.29. Écrire au journal des décisions l'arbitrage de la question 1 (continuer la série PROTEXA ou repartir de 0).
- CONTRATS, à lancer maintenant : ce sont eux, pas le code, qui fixent la date au plus tôt de la coupure. Signature en propre (A.2, ch.32-33), diffuseur ou portails au nom de GTI avec la reprise des 346 annonces en ligne (A.1, ch.34-35), prestataire d'horodatage (ch.30). Si un contrat arrive tôt, son chapitre remonte dès que ses fondations sont faites.
- LE JURISTE, en une seule consultation :
- colonnes du registre et sens du « Montant » (ch.8) ;
- corrections de mandat permises sans avenant (ch.15) ;
- mentions et forme de la série (ch.29) ;
- niveau de preuve du registre scellé (ch.30) ;
- texte de l'offre d'achat (ch.31) ;
- forme de l'avenant de prolongation (ch.33) ;
- affichage obligatoire du DPE en vitrine (ch.27) ;
- reprise du consentement RGPD (ch.16).
- LES 8 QUESTIONS, chacune avant le chapitre qui en a besoin :
- Q3, droits d'un négociateur : ch.9, vers fin octobre ;
- Q6, qui valide la diffusion : ch.7 (sinon règle provisoire), ch.11 et ch.23 ;
- Q2, agenda et bon de visite : ch.3, ch.16, ch.31 ; à trancher TÔT, l'agenda périt ;
- Q8, questions de fait (leads, SMS, automatismes, Properstar) : ch.3, ch.36, ch.40 ;
- Q5, numéro de dossier : ch.22 ;
- Q1, série PROTEXA : ch.29 ;
- Q4, suppressions et fusion : ch.38, ch.39 ;
- Q7, les 2 locations vivantes (62309, 62504) et la carte G : aucune tâche mesurée ne la couvre (non mesuré) ; à trancher avant la fin du rattrapage des documents.
- LES 5 QUESTIONS DU REGISTRE DES RELATIONS (30/09) : à trancher avant le ch.25. Leur état de réponse n'est pas mesuré.
- AVANT LE CH.10 (PILOTE) : amender par écrit la décision du 21/09 pour quelques pilotes (qui, quelles agences, quels gestes, règle contre la double saisie, ce qui reste dans Hektor), et désigner au moins 3 pilotes. Plus tard (ch.14), donner la liste des quelque 30 négociateurs actifs.
- AU FIL DE L'EAU : solder dans ImmoSign, via Hektor, les 50 procédures de signature en cours (48 mandats, 2 bons de visite), et n'en plus ouvrir la dernière semaine. La sonde du ch.3 les compte, et G.6 (ch.4) fera voir celles qui ont déjà abouti.
- LE PRÉAVIS : n'en donner AUCUN, ni à Hektor ni à La Boîte Immo, avant la fin du ch.5 (planchers), la relecture de l'ordre d'extinction (ch.3) et la bascule DNS (A.4). Un compte résilié qui répond « 200 vide » purgerait le miroir la nuit même.
- DATES : fixer la date de gel des saisies dans Hektor et la date de coupure. Le rattrapage final des recherches (E.1a, ch.45) doit commencer plusieurs jours avant la coupure.
- INFRASTRUCTURE (ch.43, peut remonter) : installer les outils clients PostgreSQL et poser vous-même la chaîne de connexion (c'est un secret). Regarder dans la console Supabase la sauvegarde PITR et sa rétention (non mesuré). Choisir le témoin extérieur et son coût. Choisir où ranger les copies froides du miroir (4,1 Go chacune, ch.6).
- ACCEPTER OU REFUSER LES REPORTS proposés : G.3 et G.4 après la coupure ; E.0-bis-e (fusion) et L10-12-b (offre d'achat) qui peuvent glisser ; L10-13-c conditionné à la question 8.
- POUSSER = DÉPLOYER (Render et Vercel) : les commits locaux en attente partiront avec le premier déploiement accordé (ch.8).
- Après la coupure : garder ou non un accès Hektor en lecture quelques semaines (E.4a).

## RISQUES
- L'ÉCHÉANCE DU 08/10 EST DÉJÀ DÉPASSÉE DANS LES FAITS. Le 05/10, l'étape chauffage a été refusée deux fois à cause d'un lot d'ARCHIVES non fini (vérifié dans quotidien_2026-10-05, l.371-426). Si G.1-e n'est pas en service le 08/10 à 21:00, un lot de 2 500 ventes (20 à 36 h estimées) fera refuser :
- le chauffage, l'entretien des compromis (sync_hektor_compromis_console.py:227) et console_missing_fields le matin ;
- puis le lot du soir suivant (« file_occupee », alerte critique).
- LE RYTHME DES VENTES N'EST PAS MESURÉ (24,3 documents par vente contre 2,7 par archive). 400 à 600 ventes par nuit est une estimation, à réviser après la 1re nuit.
- À 400 par nuit, les ventes finissent vers le 31/10 ; à 600, vers le 22/10.
- Le passage à l'heure d'hiver, le 25/10, déplace la marge : 05:00 à Paris vaut 03:00 UTC avant, 04:00 UTC après. La limite dure est l'étape chauffage, vers 06:35.
- Le disque passera d'environ 444 Go libres à 170-300 Go. La sentinelle disque est au ch.1 pour cette raison.
- G.6 ET LE RATTRAPAGE SE PARTAGENT LA FILE ET LE QUOTA HEKTOR (ch.4). Des travaux G.6 non finis à 21:00 font refuser le lot du soir. Leurs erreurs comptent dans le seuil des 20 du rattrapage. La concurrence des lectures n'est pas mesurée. Fait connu : environ 18 000 requêtes par nuit, 0 bannissement en 12 nuits.
- CHAQUE REDÉMARRAGE DU WORKER (ch.2, 11, 12, 13, 17, 18, 20, 22, 31…) EXIGE UNE FILE DOCUMENTS VIDE. Un travail « running » depuis plus de 30 min passe en erreur, et son annonce est exclue À VIE du rattrapage. Seule fenêtre sûre : l'après-midi, entre la fin du lot de nuit (et des travaux G.6) et 21:00.
- LE PILOTE ARRIVE PLUS TARD QUE DANS LA PROPOSITION « USAGE ». Il s'ouvre vers la 2e quinzaine de novembre au lieu du 29/10, parce que les planchers (ch.5), la sauvegarde (ch.6) et la sécurité (ch.7) passent avant.
- Option si Frédéric préfère la preuve par l'usage : faire les ch.5 et 6 juste après le ch.10. On gagne environ 1,5 semaine de pilote, mais un hoquet de Hektor pourrait purger le miroir sous les yeux des pilotes.
- LE CHEMIN DES PILOTES CHANGE PENDANT QU'ILS TRAVAILLENT. Statuts, fichiers et PDF passent « chez nous d'abord » aux ch.11 à 13, pendant le pilote. Parade : chaque bascule se fait derrière un réglage, elle est annoncée aux pilotes et observée une semaine. Une double saisie reste possible : il faut la règle écrite de l'amendement du 21/09.
- INVERSION DU COURANT (ch.11, 15, 23). Si une ligne du carnet ne cède pas quand Hektor confirme la même valeur, une saisie faite ENSUITE dans Hektor par un non-pilote ne redescend plus. Ce comportement n'est pas mesuré. Il se vérifie en entrant au ch.11, et rien n'est allumé sans lui.
- DOUBLE TRAVAIL ASSUMÉ, l'objection de la proposition « technique ». G.5 (ch.12-13) et L10-3 (ch.11) sont écrits sur des clés qui contiennent encore hektor_annonce_id. L10-1e (ch.21) et G.5-f (ch.22) les reprendront. L'inventaire prévoit déjà ces reprises : environ 1 à 2 j de plus contre plusieurs mois de pilote gagnés.
- LA NUIT DE BASCULE L10-1d (ch.20) EST LE GESTE LE PLUS RISQUÉ : 17 tables, 7 clés et le serveur local, la même nuit. Les index se créent en CONCURRENTLY, hors descente et hors run. Supabase a saturé le 01/10 (cache 256 Mo).
- DEUX CHANTIERS NON MESURÉS commandent la seconde moitié : « 4-suite », la clé des recherches (ch.24), et le registre des relations autonome, avec 5 questions et aucun code (ch.25). Ils conditionnent ensuite A.3-d (ch.28) et A.5-b (ch.36). Leur taille peut décaler les ch.24 à 36.
- LES CONTRATS SONT À ZÉRO (A.1, A.2, horodatage). Ce sont eux, pas le code, qui fixent la date des ch.30 et 32 à 35. Sans eux, aucune coupure n'est possible : chaque semaine de retard d'un contrat s'ajoute à la date de coupure.
- CE QUI PÉRIME DÉPEND DU PRÉAVIS. Beaucoup de tâches périssables sont au milieu de la séquence (ch.15 à 17, 27 à 29, 35, 41) à cause de leurs dépendances : « le reste » de C.13-c, les 67 brouillons, l'agenda, la paire du ménage, l'export PROTEXA, la reprise des 346 annonces, la comparaison des vitrines. Un préavis envoyé trop tôt, ou une résiliation subie, les ferait perdre. D'où la règle : aucun préavis avant le ch.5 et A.4, et les mesures du ch.3 dès maintenant.
- LE STORAGE SUPABASE N'EST PAS SAUVEGARDÉ, et aucune tâche mesurée ne le couvre. Le ch.6 copie les 35 documents qui n'existent que là. L10-9e (pg_dump) ne couvre pas le Storage. C'est un trou à écrire au plan.
- LES REPORTS ONT UN COÛT. Tant que G.3 et G.4 attendent, le stock cloud continue de grossir (2 747 Mo le 07/10), et les documents d'une annonce restaurée restent local_only, rouvrables par « Préparer ». Si la fusion (ch.39) glisse, son bouton est masqué quelques semaines après la coupure.
- LE VOLUME : environ 145 à 215 jours de code, une tâche à la fois, sans compter « 4-suite », le registre des relations, les nuits d'observation, les 2 à 4 semaines du pilote et les délais des contrats et du juriste. Une coupure n'est pas réaliste avant le printemps 2027. Aucune date ne doit être annoncée avant d'avoir regardé ce chiffre en face.
- LES CHIFFRES SONT CEUX DU 07/10 et certains ont déjà bougé à la remesure : 17 tables et 7 clés (au lieu de 16 et 4), 97 annonces de fin de vie (au lieu de 111), environ 30 fonctions exécutables par anon (au lieu de 9). Chaque chapitre est ré-audité en entrant, et sa taille peut changer.
- E.1a DÉPEND D'UNE DATE DE GEL que personne n'a fixée. Il faut plusieurs sessions sur plusieurs jours, avec un risque de bannissement d'IP (déjà arrivé les 20 et 22/08).

# CONTRADICTEUR
VERDICT: La séquence tient. Je n'ai trouvé aucun problème bloquant.

Vérifié dans le code et en base, en lecture seule :
- Le rattrapage ne prend qu'UN périmètre par nuit (enqueue_empreinte_lot.js:150-157).
- Il reste 1 250 archives (ce soir), 8 895 ventes et 508 brouillons. Aucune annonce n'est ni en file ni en erreur.
- La tâche tourne bien à 21:00.
- L'échéance du 08/10 à 21:00 est juste.
- Aucun numéro de brouillon n'entre en collision avec un numéro d'annonce, de vente ou d'archive. La branche brouillon de loadDossier (G.1-b-2) ne prendra donc pas une mauvaise fiche.

Trois manques importants, chacun prouvé dans le code :
1) Ch.11, 15 et 23 : la règle « une saisie faite ensuite dans Hektor gagne » n'existe pas pour les carnets d'annonce et de mandat. Il faut la construire, pas seulement la vérifier. Sans elle, L10-3, l'application de C.13-c, E.0-bis-d1 et L10-4 inversent le courant.
2) Ch.15 : l'applicateur des mandats ne sait pas à quel mandat appartient une date (39 annonces ont plusieurs mandats). Écrire en masse quelque 23 600 dates pendant que Hektor vit est donc risqué.
3) Ch.12-13 : le distributeur de travaux n'accepte un envoi de document ou de photo que si un fichier temporaire existe. Un envoi « chez nous d'abord » resterait en attente pour toujours, sans erreur.

Le reste est mineur :
- G.1-e se règle en changeant un seul chiffre.
- Deux logos de PDF dépendent encore de www.gti-immobilier.fr.
- L'essai prévu pour L10-6b réclamerait de vrais travaux de prod.
- Les erreurs qu'on solde ne doivent pas toucher la liste « ne jamais rejouer ».
- Le ch.4 attend le ch.2 sans raison.
- Deux critères ne se mesurent pas.
- Un push lancé à la main hors du run réinjecte les brouillons. Le run de nuit, lui, est protégé.

- [important] 11 (touche aussi 15 et 23) : La séquence demande de « vérifier en entrant » que le carnet cède quand Hektor confirme. La mesure est faite : rien ne le fait cède pour l'annonce ni pour le mandat. Ce n'est donc pas une vérification, c'est une tâche absente de la liste et non chiffrée. Sans elle, dès qu'un champ entre au contrat (L10-3a), une valeur posée UNE fois dans l'app écrase Hektor chaque nuit, pour toujours. Cela vaut même si un commercial qui n'est pas pilote change ensuite la valeur dans Hektor. Pour L10-4 (ch.23), un « diffusable = 1 » resterait dans la vitrine publique après un retrait fait dans Hektor.
  preuve: Catalogue Supabase : 4 fonctions écrivent dans app_annonce_champ_app (app_geste_affaire_optimistic, app_archive/restore_annonce_optimistic, app_assign_negotiator_optimistic), aucune n'y fait de DELETE. grep sur phase2, Console, backend et front : aucune suppression. Le worker ne fait qu'un PATCH quand Hektor refuse (console_job_worker.js:18657). phase2/identite/magasin_annonce_app.py : « Une saisie posée ici survit à tout ». phase2/identite/appliquer_contrat_mandat.py : « l'app a une valeur -> elle gagne », sans aucune date. Seules les affaires ont le mécanisme : retrait à chaud (prouverTransactionModifiee) et phase2/identite/nettoyer_carnet_affaire.py (« une saisie en attente ... DISPARAÎT UNE FOIS ARRIVÉE »).
  correction: Ajouter en tête du ch.11 une tâche « le carnet cède », pour app_annonce_champ_app et app_mandat_champ_app :
- retrait à chaud dans le worker quand Hektor porte la valeur envoyée ;
- un script de stock calqué sur nettoyer_carnet_affaire.py ;
- une règle de récence par champ.
Compter 1 à 2 j. En faire la condition d'allumage de L10-3a/b/c, de l'application de C.13-c, de E.0-bis-d1 et de L10-4.
- [important] 15 : C.13-c écrit en masse environ 23 600 dates de clôture dans un carnet qui gagne contre Hektor. Or l'applicateur choisit la ligne par annonce, et non par mandat. Sur une annonce qui a plusieurs mandats, la date d'un ANCIEN mandat (règles 1 et 2) peut s'afficher comme clôture du mandat EN COURS. Par ailleurs, faute de carnet qui cède (problème précédent), une prolongation saisie ensuite dans Hektor (environ 8 avenants par mois) ne défait plus la date posée par l'app. Cela contredit la règle de la séquence elle-même : « une saisie faite ENSUITE dans Hektor gagne ».
  preuve: appliquer_contrat_mandat.py lit « SELECT hektor_annonce_id, valeur_app FROM app_mandat_champ_app WHERE champ = ? », sans numero_mandat. Il range ensuite les valeurs par INSERT OR REPLACE dans une table temporaire dont la clé est hektor_annonce_id, puis met à jour la ligne de l'annonce dans app_view_generale, qui porte le mandat courant. Le magasin local est pourtant clé (hektor_annonce_id, hektor_mandat_id, champ) (magasin_mandat_app.py:67-78). Mesuré le 07/10 : app_mandat compte 26 842 mandats pour 26 803 annonces, et 39 annonces ont plus d'un mandat.
  correction: Dans le ch.15, avant toute écriture :
(a) corriger l'applicateur pour ne retenir que la ligne dont numero_mandat est celui de app_view_generale ;
(b) calculer et faire relire la table de PROPOSITIONS maintenant, car « le reste » périme ;
(c) tant que le carnet ne cède pas, n'écrire au carnet que les mandats hors du parc vivant ou déjà clos chez Hektor, et appliquer le reste à la coupure.
Ajouter au critère de fin : « 0 annonce dont le mandat courant reçoit la date d'un autre mandat ».
- [important] 12 (et 13) : Le distributeur ne réclame un travail upload_document_to_hektor ou upload_hektor_photo que si le fichier TEMPORAIRE nommé dans payload.temp_storage_path existe dans le Storage. Or les chemins « chez nous d'abord » (app_document_id, app_photo_id) lisent le fichier définitif, et G.5-b prévoit d'écrire directement sur le chemin définitif. Un travail différé, ou un travail de repassage, resterait « pending » pour toujours, sans erreur ni alerte. Le ch.12 ne cite que l'ajout du type de repassage à la liste en dur.
  preuve: Définition de app_console_claim_next_job (catalogue, 07/10) : « and (j.job_type not in ('upload_document_to_hektor','upload_hektor_photo') or exists (select 1 from storage.objects o where o.bucket_id = 'hektor-console-documents' and o.name = j.payload_json->>'temp_storage_path')) ». Dans le worker, completerEnvoiDocumentDiffere (console_job_worker.js:7717-7728) lit ligne.storage_path et n'utilise pas temp_storage_path. handleUploadDocumentToHektor (l.7833) et handleUploadHektorPhoto (l.8072) prennent le chemin différé AVANT d'exiger le fichier temporaire.
  correction: Dans le même patch SQL que le type de repassage (G.5-c), laisser passer un envoi dont la charge porte app_document_id ou app_photo_id. Autre solution : imposer temp_storage_path = storage_path, mais aucune purge des fichiers temporaires (G.3) ne doit alors les retirer. Ajouter au critère de fin du ch.12 : « un travail différé sans fichier temporaire est réclamé dans la minute ». G.5-d (ch.13) dépend du même patch.
- [mineur] 1 : G.1-e ajoute une option de limite propre à chaque périmètre dans parseArgs. C'est inutile, et cela ajoute du code avant l'échéance du 08/10 à 21:00. Ce soir, le lot prend les 1 250 dernières archives (moins que la limite de 2 500, et un seul périmètre par nuit). À partir du 08/10, --limit ne s'applique donc plus qu'aux ventes.
  preuve: enqueue_empreinte_lot.js:150-157 : le premier périmètre qui a du travail, et lui seul. Mesuré le 07/10 : 1 250 archives à faire, 8 895 ventes, 508 brouillons, 0 en file, 0 en erreur. Remarque : l'en-tête de scheduled/run_rattrapage_documents.ps1 dit encore 22:00, alors que la tâche planifiée part à 21:00 (Get-ScheduledTask).
  correction: Pour G.1-e, changer seulement « --limit 2500 » à la ligne 75 du .ps1, avec la taille décidée par Frédéric, et garder G.1-b-1. Abandonner l'option de parseArgs. Corriger au passage le commentaire « 22:00 ».
- [mineur] 13 (L10-15-a au ch.8) : L10-15-a ne traite que le logo du mandat. Deux autres PDF que nous fabriquons chargent leur logo sur www.gti-immobilier.fr, servi par la machine de l'éditeur de Hektor : l'avis de valeur et le plan cadastral. Ces logos casseront à la coupure ou au déménagement du site. Pour la même raison, le site public (même nom www) ne peut pas déménager avant la coupure : l'admin Hektor, le worker et pdf.php passent par ce nom. Cette contrainte n'est écrite nulle part.
  preuve: console_job_worker.js:6679 (avis de valeur) et :7476 (cadastrePlanHtml) : LOGO = "https://www.gti-immobilier.fr/images/logoSite.png". L10-15-a ne touche que apps/hektor-v1/src/mandat-template.html:11 et :61. pdf.php : Ecrans Android/export_project_vitrine.py:364 et apps/rdv-public/app.js:172.
  correction: Ajouter les deux lignes du worker au ch.13 (même worker et même redémarrage que G.5-d et L10-15-c), avec le critère « aucune requête vers gti-immobilier.fr ». Dans le point A.4 de la liste hors code, écrire : « le site public ne déménage pas avant la coupure, ou avant le ch.42 et ce correctif ».
- [mineur] 18 : Le critère et la vérification de L10-6b (« exécuter LE worker en --once, clé forcée, sur un travail d'essai ») ne peuvent pas viser un travail d'essai. --once réclame le PROCHAIN travail de la file de prod. De plus, la clé doit vivre dans app_setting, donc la forcer couperait aussi les 4 services de prod.
  preuve: console_job_worker.js:20106 et 20143 : --once appelle claimNextJob(), sans filtre sur un identifiant de travail. app_console_claim_next_job ne sert que les identifiants de worker qui finissent par ':service:v9' ou ':scheduled:v9' : un worker d'essai à l'identifiant par défaut ne réclame rien, et un worker qui imite un service entre en concurrence avec la prod.
  correction: Ajouter à L10-6b une option --job-id, ou une variable d'environnement qui force la clé pour le seul worker d'essai et passe avant app_setting. Faire l'essai sur une branche ou une copie, et l'écrire dans la vérification.
- [mineur] 1 : L10-10a prévoit de « solder » des travaux en erreur pour que l'alerte redevienne verte. Si cette pratique touche un jour des sync_console_documents, elle efface la liste « ne jamais rejouer » du rattrapage. Les annonces repartiraient alors au lot suivant, ce qui est le risque de bannissement d'IP.
  preuve: enqueue_empreinte_lot.js:154 : les erreurs (status='error', job_type='sync_console_documents') servent d'exclusion définitive. Les 15 erreurs d'aujourd'hui sont 14 refresh_console_data et 1 unlink_hektor_mandant (mesuré), donc le geste du jour est sans danger.
  correction: Écrire dans L10-10a que le geste exclut job_type='sync_console_documents'. La nouvelle règle « alerter sur la hausse » rend inutile de solder ces erreurs-là.
- [mineur] 4 : Le ch.4 dépend du ch.2 (G.5-a) sans raison technique aujourd'hui. Si la fenêtre de redémarrage du ch.2 attend une décision, G.2 et G.6 attendent aussi, alors qu'ils pressent (132 biens en vente jamais lus). Par ailleurs, l'option « détection dans une tâche à part » n'est pas bornée dans le temps. Or plusieurs étapes du run refusent de tourner dès qu'un seul travail console attend.
  preuve: Mesuré : 0 ligne de app_console_document avec hektor_document_id NULL, et 0 avec envoi_hektor_statut. pruneDeletedDocuments n'a donc rien à épargner avant G.5-c. Les gardes sont dans sync_hektor_chauffages.py:251-263 et sync_hektor_compromis_console.py:220-229 (tout travail pending ou running). Dans les journaux, ces étapes tournent vers 06:35-06:51. L'appel de G.6 dans le run est placé après elles (run_full_pipeline.ps1:1308).
  correction: Remplacer le prérequis « chapitre 2 » du ch.4 par « G.1-e seulement ». Ajouter à la décision « où faire tourner la détection » : jamais de travaux en file entre environ 06:30 et 07:00, et une file vide avant 21:00.
- [mineur] 10 et 14 (et 5) : Trois critères de fin ne se mesurent pas :
- ch.10 et ch.14 : « 0 saisie perdue » n'a pas de référence à laquelle comparer ;
- ch.5 : « les mêmes compteurs que la veille » est faux d'une nuit normale à l'autre (réactivations, ventes du jour).
  preuve: Critères de fin des ch.10, 14 et 5 dans la séquence. Exemple : le push du 07/10 donne deleted_dossiers = 9 ; ce nombre varie chaque nuit.
  correction: Ch.10 et 14 : « chaque geste du journal tenu par les pilotes est retrouvé dans app_console_job ou dans un carnet ; 0 ligne *_provisional en erreur non traitée (sonde de L10-2a) ; 0 conflit envoi_impossible non soldé ».
Ch.5 : « compteurs compris entre le minimum et le maximum des 30 dernières nuits, et aucun refus ».
- [mineur] 2, 20 et 43 (tout push hors du run) : Un push lancé à la main, hors de run_full_pipeline, réinjecte les brouillons dans les annonces actives. C'est arrivé le 07/10 : 441 brouillons sont entrés, et le patch du jour l'a réparé. La séquence prévoit plusieurs passages réels hors du run de nuit (répétitions, nuit de bascule, restauration) sans écrire cette règle. Le patch se trompe de cause : il parle d'un « interrupteur éteint », alors que le run de nuit l'allume.
  preuve: Commit local 38ad468 (non poussé) : supabase/patch_retirer_brouillons_du_perimetre_actif_2026-10-07.sql. Mesuré en lecture seule : sans la variable, le périmètre local du push compte en ce moment 13 904 annonces, dont 441 brouillons. run_full_pipeline.ps1:349 pose APP_BROUILLON_BUCKET_ENABLED=1 sans condition : le run de 05:00 est protégé (il a vu 13 463 annonces ce matin).
  correction: Écrire dans les règles de la séquence : « tout push ou toute étape rejouée passe par run_full_pipeline.ps1 -StartAtLabel, ou pose APP_BROUILLON_BUCKET_ENABLED=1 ». Mieux : faire refuser export_app_payload.py ou push_upgrade_to_supabase.py quand la variable est absente. Corriger le texte du patch.

OUBLIS: ["Le carnet qui cède pour app_annonce_champ_app et app_mandat_champ_app : retrait à chaud quand Hektor confirme, script de stock calqué sur nettoyer_carnet_affaire.py, règle de récence. C'est le prérequis de L10-3, de l'application de C.13-c, de E.0-bis-d1 et de L10-4.", "Corriger phase2/identite/appliquer_contrat_mandat.py pour qu'il n'applique que la valeur du mandat courant (filtre sur numero_mandat ; 39 annonces ont plusieurs mandats). À faire avant d'écrire les dates de C.13-c.", "Ouvrir app_console_claim_next_job aux envois « chez nous d'abord » (app_document_id ou app_photo_id sans temp_storage_path). Prérequis de G.5-c, G.5-d, G.5-e et de leur repassage.", "Logos des PDF fabriqués par le worker : avis de valeur (console_job_worker.js:6679) et plan cadastral (:7476). Ils pointent sur www.gti-immobilier.fr et ne sont pas couverts par L10-15-a.", "Règle d'exploitation : aucun push hors de run_full_pipeline sans APP_BROUILLON_BUCKET_ENABLED=1, ou bien un refus codé en dur (incident du 07/10, commit 38ad468).", "Question 7 (les 2 locations vivantes 62309 et 62504, la carte G) : aucune tâche ni aucun chapitre ne la porte, alors que la séquence lui donne une échéance (« avant la fin du rattrapage des documents »)."]
