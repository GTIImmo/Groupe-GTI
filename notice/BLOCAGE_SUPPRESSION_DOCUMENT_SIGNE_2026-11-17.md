# Bloquer la suppression d'un document signé — audit et plan (17/11/2026)

> Demande de Frédéric (17/11) : « d'abord bloque la suppression d'un document signé » (la session annexe proposée n'a
> pas pu démarrer : Git n'ouvrait pas l'état du dépôt pour lui créer sa copie de travail). Trouvé par l'analyse des
> règles du trombone de l'assistant (`ETAPE4_ECRAN_ACCUEIL_ASSISTANT_AUDIT_2026-11-16.md` §51, E.1).
> **Périmètre** : la suppression d'un DOCUMENT (pas des photos, pas des annonces). Rien n'est codé.

## 1. Le défaut, lu dans le code

- **L'écran** : le bouton « Supprimer » est sur TOUTES les lignes de `ConsoleDocumentsPanel` (`App.tsx` ~12520) ; le clic
  insère directement le travail `delete_document_from_hektor` dans la file (`createDeleteDocumentFromHektorJob`,
  `lib/api.ts` ~10066).
- **La base** : seule la règle d'insertion des travaux joue (`app_console_can_request_job` : direction partout,
  négociateur sur SES biens). Elle ne regarde pas la signature.
- **Le worker** (`handleDeleteDocumentFromHektor`, `console_job_worker.js` ~10525) : il supprime chez Hektor, vérifie,
  écrit la trace, puis détruit le fichier au coffre, le fichier serveur et la ligne — sans JAMAIS regarder la signature.
- C'est contraire à la règle écrite de la GED (`CHANTIER_GED_DOCUMENTS_2026-11-06.md` §5.3) : « un document signé ou en
  cours de signature ne peut être ni supprimé ni remplacé ».
- Les autres portes sont déjà gardées : la purge des documents absents chez Hektor épargne les signés (règle R1,
  `signatureProtegee` ~5148) ; le ménage du coffre exclut `signed/` et `immosign/` ; la purge des archives n'existe pas encore.

## 2. Mesure (17/11, en base)

- **544 documents engagés dans une signature** : 485 signés ImmoSign (avec leur copie signée), 57 ImmoSign en attente,
  1 signé Youtrust, 1 Youtrust annulé. 0 marqué « signé à la main ». (9 914 documents portent « à envoyer » : préparés,
  jamais partis — pas engagés.)
- 4 suppressions de document en 30 jours.

## 3. La règle proposée — « engagé dans une signature »

Bloqué : une copie signée rapatriée (`signed_document`), un statut **signé** (quel que soit le prestataire), la marque
**à la main**, une signature **en cours** (en attente, en cours, en approbation).
**Laissé supprimable** (recommandé) : « à envoyer », **annulé**, **refusé** — la signature n'a pas eu lieu et n'est plus
en cours. ⚠ Le worker range aujourd'hui « refusé » ImmoSign et « Youtrust annulé » parmi les lignes à ne pas toucher pour
la SYNCHRO (règle R1) : la règle de SUPPRESSION est une autre question, à trancher par lui.

## 4. Les trois verrous proposés

1. **L'écran** : sur une ligne engagée, pas de bouton « Supprimer » mais la raison (« Signé : ne se supprime pas »).
2. **La base** : un garde à l'insertion du travail `delete_document_from_hektor` — refus `document_signe_non_supprimable`
   si le document visé est engagé (patch + retour arrière + répétition avec témoin inverse, à coller avec son accord).
3. **Le worker** : avant tout appel à Hektor, refus `[REFUS D'ETAT]` (jamais rejoué) si le document est engagé — au cas
   où un travail aurait été posé avant le garde de la base. ⚠ Prend effet au redémarrage des 4 services, file vide
   (0 en attente ET 0 en cours), redémarrage fait par lui.

**Ce que ça pourrait casser ailleurs** : un document signé posé par erreur (doublon) ne se supprimera plus depuis l'app
— il faudra le faire chez Hektor (la synchro gardera alors notre ligne, protégée par R1). Rien d'autre ne pose ce travail
(seul l'écran l'insère). **Retour arrière** : le patch inverse retire le garde ; écran et worker se défont par git.
**Contrôles** : essai du worker hors ligne (scènes signé / en cours / à la main / annulé / à envoyer), répétition SQL avec
témoin inverse, `npm run build`, puis un essai réel sur un document de TEST signé (refus attendu, rien chez Hektor).
