# PROMPT — chantier « domaine des documents » : fiches remplacées à chaque changement d'adresse

*À coller au début d'une NOUVELLE conversation. Tout ce qu'il faut savoir est dans le bloc :
le problème, les preuves chiffrées, le correctif proposé (avec le SQL en brouillon), ce qui
est déjà fait, ce qui reste non prouvé, et les règles du projet. Rédigé le 20/10/2026 à la
fin d'une conversation qui a corrigé le bug du 409 des documents, puis a découvert celui-ci
en prouvant ce correctif en réel.*

---

```
CHANTIER = DOMAINE DES DOCUMENTS

Tu es l'ingénieur principal de mon projet (agence GTI : une app qui remplace le logiciel
Hektor). Dépôt : C:\Hektor\Projet. Je ne suis pas développeur : parle-moi en français
simple, phrases courtes, sans jargon non expliqué.

━━ 0. LES RÈGLES (CLAUDE.md §0 et §4 — relis-les, elles priment sur ce prompt) ━━
- AUDITER → EXPLIQUER (avec « ce que ça pourrait casser ailleurs », obligatoire) → attendre
  mon « vas-y » → CODER (additif, réversible) → CONTRÔLER → mettre à jour les documents.
- Un message court de ma part est une QUESTION, pas un « vas-y ».
- Toute écriture en base de production, tout redémarrage de service, tout push : MON accord,
  au cas par cas. Je colle moi-même les patchs SQL dans l'éditeur Supabase (l'outil MCP bloque
  parfois les écritures) : tu prépares PATCH + INVERSE + RÉPÉTITION (avec ROLLBACK), tu me
  les donnes, tu vérifies après par l'empreinte.
- Une seule tâche en code à la fois. Chaque message commence par une ligne de position.
- Stage fichier par fichier. Une autre session travaille en parallèle (voir §7).
- NE JAMAIS lancer le worker pour l'inspecter. NE JAMAIS redémarrer un service si la file n'est
  pas vide (0 pending ET 0 running).
- Compare toujours les empreintes de fonctions SQL APRÈS retrait de chr(13) : le collage
  Windows ajoute des retours chariot (leçon 30, vécue le 20/10 : 57 CR, 5424 → 5481 octets).

━━ 1. LE PROBLÈME EN CINQ PHRASES ━━
Le numéro Hektor d'un document déposé (colonne hektor_document_id de app_console_document,
sources hektor_console_uploaded_private / _shared) est calculé en sha1 de l'ADRESSE COMPLÈTE
du fichier, domaine compris (Console/console_job_worker.js, extractDocumentEntries, ~l.1061 :
`hektor_document_id: sha1(url)`). Le 11/09/2026 le portail Hektor a changé de domaine :
groupe-gti-immobilier.la-boite-immo.com → www.gti-immobilier.fr (mémoire :
hektor-bascule-domaine-gti-immobilier). Même fichier, même chemin, autre numéro. Le worker croit
à un nouveau document, et pruneDeletedDocuments (~l.5607, appelé ~l.5815) SUPPRIME les anciennes
fiches (son seul garde-fou est « liste vide ») pendant que de nouvelles fiches sont créées avec
de nouveaux `id`. C'est contraire à ma règle : l'identifiant de l'app ne doit jamais changer
parce que Hektor a déménagé.

━━ 2. LES PREUVES (toutes mesurées le 20/10, base Supabase projet dwaqxfrinihnychuoptk) ━━
CAUSE PROUVÉE (test causal, pas une corrélation) :
- 2 330 travaux sync_console_documents ont supprimé 15 403 fiches depuis le 11/09 ; au même
  moment 16 024 fiches neuves, TOUTES au nouveau domaine, ont été créées ; 2 267 travaux =
  remplacement complet ; 27 travaux seulement n'ont rien recréé (vraies suppressions).
- Base normale avant la bascule : 20 fiches supprimées / 18 annonces par semaine.
- Par vagues : 26-28/09 ≈ 9 700 fiches ; 15/10 : 4 283 ; ET ACTIF AUJOURD'HUI : 30 annonces /
  599 fiches remplacées entre 02:07 et 02:35 par le lot « historical » de la nuit.
- 5 848 fichiers du cloud antérieurs au 11/09 n'ont plus de fiche (7,4 Go) ; 2 531 ont un
  homonyme recréé. Orphelins du disque du serveur local : NON MESURÉ.
CE QUI RESTE À RISQUE :
- 27 966 fiches à l'ancien domaine, sur 6 198 annonces, ≈ 39 Go de fichiers (15 855 dans le
  cloud, 12 094 en local seul). Chacune sera remplacée à la prochaine synchro complète de son
  annonce (changement réel de documents, ou campagne de rattrapage).
- Dont 27 962 de forme standard `https://<hôte>/admin/documents/biens/<N>/<nom>?flag=lbiDocumentsSecure`
  et 4 « liens orphelins » (sans nom de fichier : annonces 16664, 20023, 43007, 53684) que le
  code ignore déjà → NE PAS les migrer.
CE QUI N'EST PAS TOUCHÉ : ImmoSign et « Mes documents » (clés immosign-doc-N / hektor-doc-N,
indépendantes du domaine) ; app_dossier_cadastre (21 lignes, aucune ne pointe l'ancien
domaine) ; le journal des suppressions (0 ligne) ; les photos (NON MESURÉ — son identifiant
vient du CDN, pas de l'adresse, mais à vérifier).
L'EMPREINTE DE CONTENU (documentContentFingerprint, ~l.1208) ne retient que le NOM de fichier :
le changement de domaine ne déclenche donc rien tout seul.
LA RÉPARATION SUR PLACE EST POSSIBLE :
- nouveau numéro = sha1(ancienne adresse avec l'hôte remplacé) : 17/17 sur les paires de
  l'annonce 59578 ;
- 27 966/27 966 anciennes fiches : numéro cohérent avec leur adresse, préfixe attendu, numéro
  d'annonce cohérent dans le chemin ; 0 doublon interne après recalcul ; les seules collisions
  avec une fiche existante (17) sont celles de 59578 ;
- les 162 838 fiches du nouveau domaine ont exactement la même forme de chemin ;
- extensions.digest(texte,'sha1') existe en SQL et redonne le même hex que le sha1 du worker ;
- la table app_console_document (275 Mo) n'a AUCUN déclencheur, n'est pas dans la publication
  temps réel ; rien hors du worker ne lit metadata_json.console_url ; la seule fonction SQL qui
  mentionne hektor_document_id avec cette table est la RPC de création (elle écrit NULL).

━━ 3. L'ANNONCE 59578 (le cas particulier, créé par la conversation précédente) ━━
Pour prouver le correctif du 409, une synchro (sync_console_documents, travail 7877ec31) a été
posée sur 59578 : elle a indexé 17 documents sous le nouveau domaine (fiches neuves, SANS
fichier, créées vers 12:22 UTC) et marqué les 17 anciennes « plus chez Hektor » (absent_depuis =
2026-10-20 12:22:20.221+00) ; elle est tombée en erreur au téléchargement (UND_ERR_SOCKET)
AVANT le prune — c'est pour ça que les anciennes existent encore. Ces 17 paires sont à traiter
à part : on garde l'ANCIENNE fiche (elle a son fichier cloud et son historique), on supprime la
neuve (vide), puis on re-clé l'ancienne. La fiche AVENANTS 87K (id 6b97082e-…, source 'app',
numéro 716119466c…) est SAINE et ne doit pas être touchée.

━━ 4. CE QUI EST DÉJÀ FAIT (commit local 642813d, NON POUSSÉ) ━━
Bug voisin (409 « app_console_document_pkey » sur une fiche créée par l'app) corrigé et prouvé :
adoptExistingAppRows, statut qui ne ment plus, script de reprise qui ne renvoie plus une ligne
déjà chez Hektor, patch SQL de la distribution des tâches APPLIQUÉ en production (empreinte
corps sans CR 7dc530e4…). Tests verts : Console/test_adoption_ligne_app.js,
test_envoi_hektor_differe.js, test_reprendre_envois.js, test_refus_coffre_documents.js,
test_aucune_fausse_promesse.js, test_nettoyage_temporaire.js, test_pagination_triee.js.
Le faux Supabase de test_adoption_ligne_app.js (qui applique la clé primaire ET l'unicité
annonce+source+numéro) est réutilisable tel quel pour tester les correctifs ci-dessous.
Mémoire à lire : document-hektor-id-sha1-url-domaine-prune-remplace-les-fiches.md.

━━ 5. LE CORRECTIF PROPOSÉ (à re-vérifier TOI-MÊME avant de le défendre) ━━
Ordre : A0 → A (+A1) → C → B → D. Le plus urgent est A : la perte continue chaque nuit.

A0 — ESSAI SUR UNE ANNONCE. Choisir une annonce de l'ancien domaine (petite, 2-4 documents,
  aucun travail en cours), appliquer à elle SEULE la migration A, puis poser une vraie
  sync_console_documents dessus (3 lectures chez Hektor, avec mon accord). PREUVE ATTENDUE :
  compte rendu `pruned: 0`, mêmes `id`, aucune fiche neuve, numéros inchangés. Si ce n'est pas
  le cas : STOP, l'hypothèse « même chemin sous les deux domaines » est fausse pour cette
  annonce — me le dire, ne pas lancer A.

A — MIGRATION SUR PLACE des 27 962 fiches. Une seule transaction, file de travaux vide exigée.
  BROUILLON (à vérifier, éprouver en RÉPÉTITION avec ROLLBACK, comparer les comptes) :

    BEGIN;
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM public.app_console_job WHERE status IN ('pending','running'))
      THEN RAISE EXCEPTION 'file non vide : on ne migre pas pendant une synchro'; END IF;
    END $$;

    CREATE TABLE public.app_console_document_avant_rekey_domaine_20261020 AS
    SELECT id, hektor_annonce_id, source, hektor_document_id AS ancien_numero,
           metadata_json->>'console_url' AS ancienne_url,
           present_in_hektor, absent_depuis, updated_at
    FROM public.app_console_document
    WHERE source LIKE 'hektor_console_uploaded%'
      AND metadata_json->>'console_url' ~
          '^https://groupe-gti-immobilier\.la-boite-immo\.com/admin/documents/biens/[0-9]+/[^/?]+\?flag=lbiDocumentsSecure$';

    DO $$ DECLARE n int; v_supp int; v_maj int; BEGIN
      SELECT count(*) INTO n FROM public.app_console_document_avant_rekey_domaine_20261020;
      IF n <> 27962 THEN RAISE EXCEPTION 'attendu 27962, trouve %', n; END IF;

      -- A1 : supprimer les fiches NEUVES VIDES de 59578 (jamais une fiche qui porte un fichier)
      DELETE FROM public.app_console_document nv
       USING public.app_console_document_avant_rekey_domaine_20261020 b
       WHERE nv.hektor_annonce_id = b.hektor_annonce_id AND nv.source = b.source AND nv.id <> b.id
         AND nv.hektor_document_id = encode(extensions.digest(replace(b.ancienne_url,
               'https://groupe-gti-immobilier.la-boite-immo.com','https://www.gti-immobilier.fr'),'sha1'),'hex')
         AND nv.storage_path IS NULL AND NOT (nv.metadata_json ? 'local_archive_path')
         AND nv.created_at >= '2026-10-20 12:00+00';
      GET DIAGNOSTICS v_supp = ROW_COUNT;
      IF v_supp <> 17 THEN RAISE EXCEPTION 'attendu 17 fiches neuves vides, supprime %', v_supp; END IF;

      -- A : re-clé (id, fichier, métadonnées INTACTS ; seuls numéro et adresse changent)
      UPDATE public.app_console_document d SET
        hektor_document_id = encode(extensions.digest(replace(b.ancienne_url,
              'https://groupe-gti-immobilier.la-boite-immo.com','https://www.gti-immobilier.fr'),'sha1'),'hex'),
        metadata_json = jsonb_set(d.metadata_json, '{console_url}', to_jsonb(replace(b.ancienne_url,
              'https://groupe-gti-immobilier.la-boite-immo.com','https://www.gti-immobilier.fr'))),
        present_in_hektor = CASE WHEN d.absent_depuis = '2026-10-20 12:22:20.221+00' THEN true ELSE d.present_in_hektor END,
        absent_depuis     = CASE WHEN d.absent_depuis = '2026-10-20 12:22:20.221+00' THEN NULL ELSE d.absent_depuis END,
        updated_at = now()
      FROM public.app_console_document_avant_rekey_domaine_20261020 b WHERE d.id = b.id;
      GET DIAGNOSTICS v_maj = ROW_COUNT;
      IF v_maj <> 27962 THEN RAISE EXCEPTION 'attendu 27962 mises a jour, fait %', v_maj; END IF;
    END $$;
    -- puis des SELECT de contrôle : 0 fiche standard restante à l'ancien domaine ; 100 % des
    -- numéros = sha1(adresse) ; 59578 : 0 absente ; le nombre de lignes de la table = avant - 17.
    COMMIT;

  RETOUR ARRIÈRE : un fichier INVERSE qui remet ancien_numero / ancienne_url depuis la table
  de sauvegarde (valable tant que rien n'a resynchronisé ces fiches) ; les 17 fiches neuves
  supprimées étaient vides et se recréent à la synchro suivante.
  À RELIRE avant de livrer : le timestamp exact d'absent_depuis des 17 anciennes (le relever
  en base, ne pas le recopier d'ici) ; le fait que les fiches neuves de 59578 ont bien
  storage_path NULL ; les index uniques (annonce, source, numéro) et (bucket, chemin).

C — GARDE-FOU DU PRUNE (code, Console/console_job_worker.js, pruneDeletedDocuments) : si la
  suppression emporte au moins 3 fiches ET plus de la moitié des fiches déposées de l'annonce,
  ne rien supprimer, écrire au journal du travail « suppression en bloc refusée », et laisser
  le marquage « plus chez Hektor » (3e du 13/10) qui conserve la fiche avec mention. Test avec
  le faux Supabase, deux sens (le refus ET la vraie suppression d'un document isolé).
  Redémarrage de HektorConsoleWorkerDocuments, file vide.

B — RÉCONCILIATION PAR CHEMIN (code, upsertConsoleDocuments) : si le numéro d'une entrée est
  inconnu, retrouver la fiche existante de la même annonce et même source dont le chemin (adresse
  sans l'hôte) est identique ; la RE-CLÉER par un PATCH (hektor_document_id + console_url) AVANT
  l'upsert — sinon on retombe dans le 409 « pkey » déjà corrigé pour les fiches 'app' (même
  famille de défaut : l'id est repris, la clé d'unicité ne retrouve rien). Protège de tout
  futur changement de domaine. Alternative écartée : hacher le chemin seul (oblige à migrer les
  190 000 fiches et à déployer le code au même instant).

D — NETTOYAGE (après A, jamais avant mon accord) : les 5 848 fichiers cloud orphelins (7,4 Go),
  les orphelins du disque local (à mesurer), la table de sauvegarde quand A est validée.

CE QUE A NE RÉPARE PAS : les 15 403 fiches déjà remplacées gardent leurs nouveaux id ; leurs
dates d'envoi/signature (metadata_json.signature.sent_at / signed_at, reconstruites à zéro)
sont probablement perdues — à CHIFFRER, pas à supposer.

━━ 6. CE QUI N'EST PAS PROUVÉ (dis-le, ne le suppose pas) ━━
1. Pourquoi ces 30 annonces précisément ont été relues cette nuit (vrai changement de
   documents ? rotation de la détection ? campagne ?). Voir Console/enqueue_console_sync_jobs.js
   (mode --detect) et scheduled/run_entretien_documents.ps1.
2. Que le chemin est identique sous les deux domaines pour d'AUTRES annonces que 59578 (preuve
   structurelle forte, preuve directe sur une seule annonce) → c'est le rôle de A0.
3. Le nombre de dates de signature perdues, et la présence éventuelle de fiches signées
   (metadata_json.signed_document) parmi les fiches supprimées : le journal est vide.
4. Les photos : même défaut ou non.
5. Les 4 liens orphelins : à laisser, mais à confirmer que le prune les supprimera sans
   dommage à la prochaine synchro.

━━ 7. COORDINATION ET PIÈGES ━━
- Une AUTRE SESSION prépare la pose de la « pièce ② des brouillons » (CLAUDE.md §2 « Ce qui
  attend », point ①) : patch SQL à coller + git push + redémarrage de Documents. Un `git push`
  de sa part enverra aussi le commit 642813d. Ne pas redémarrer deux fois pour rien : se
  coordonner sur le redémarrage (file vide obligatoire).
- Le service Documents a été redémarré à 14:31 le 20/10 avec le code du commit 642813d.
- L'entretien de nuit : 22:00 (detection + synchros), le lot « historical » tourne dans la nuit
  (les remplacements d'aujourd'hui datent de 02:07-02:35 Paris). Une migration A posée après
  22:00 aura déjà laissé une nuit de dégâts : proposer le moment (avant 22:00 si possible) et
  la file vide.
- Le 20/10, un travail de test (priorité -100) de juin traîne dans app_console_job : ce n'est
  pas un reste de répétition.
- Fins de ligne : Console/console_job_worker.js est en CRLF dans la copie de travail, LF dans
  l'index (git le gère). Utilise Edit, pas un remplacement global.
- Les écrans ne lisent pas `source` sur les documents ; la purge nocturne ne touche que les
  sources qui commencent par hektor_console (donc une fiche source='app' n'est jamais purgée).

━━ 8. CE QUE JE T'ATTENDS COMME PREMIÈRE RÉPONSE ━━
Ligne de position, puis : (a) tu relis CLAUDE.md §0 et la mémoire citée ; (b) tu REVÉRIFIES en
lecture seule les 4 chiffres qui portent la décision (fiches à migrer = 27 962 ; paires de 59578
= 17 ; file vide ; annonces à l'ancien domaine = 6 198) — ils ont pu bouger depuis ; (c) tu me
dis par où tu commences (A0) et ce que ça demande de ma part ; (d) tu t'arrêtes et tu attends
mon « vas-y ». Tu ne poses rien en production sans mon accord.
```
