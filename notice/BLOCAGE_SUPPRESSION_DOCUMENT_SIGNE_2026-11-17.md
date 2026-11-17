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

## 5. CODÉ le 17/11 (sur « Vas-y ») — règle retenue : « annulé » et « refusé » restent supprimables

- **Worker** : `documentSignatureEngagee` (exportée) ; `handleDeleteDocumentFromHektor` lit le document AVANT d'ouvrir la
  session Hektor et refuse `[REFUS D'ETAT] document signe ou en cours de signature` (jamais rejoué). Essai
  `Console/test_garde_suppression_document_signe.js` : 17 contrôles verts — 6 cas bloqués refusés SANS AUCUN appel
  (Hektor, coffre, serveur, ligne), 4 cas libres supprimés comme avant (trace AVANT la destruction), et le TÉMOIN INVERSE :
  le worker d'avant supprimait les 6 cas bloqués. `test_garde_r1_signature.js` reste vert.
- **Écran** : `documentSignatureEngagee` et `TEXTE_SIGNE_NE_SE_SUPPRIME_PAS` dans `lib/choixSignature.ts` ; sur une ligne
  engagée, « Signé : ne se supprime pas » à la place du bouton, et `handleDeleteDocument` refuse aussi. `npm run build` vert.
- **Base** : `supabase/patch_suppression_document_signe_garde_2026-11-17.sql` (+ `_INVERSE`, `_REPETITION` : 7 contrôles,
  dont le témoin inverse garde coupé, tout annulé par ROLLBACK). **PAS ENCORE APPLIQUÉ** (son accord).
- **Reste, avec son accord** : appliquer le patch puis la répétition ; pousser ; redémarrer les 4 services worker (lui,
  file vide) ; essai réel : le bouton absent sur un document signé de test, et un travail posé à la main refusé.

## 6. EN PRODUCTION (17/11, sur « Oui, applique et pousse »)

- **Base** : patch appliqué par `Console/apply_sql_patch.js` (pooler), puis la RÉPÉTITION sans erreur (7 contrôles, chacun
  lève s'il échoue) ; vérifié ensuite : le garde est actif (`tgenabled O`) à côté des 3 autres gardes intacts, 43 travaux
  de suppression comme avant (aucun essai resté), la règle reconnaît le mandat signé de 61398.
- **Poussé** : `36313b3` (Vercel en ligne avec « ne se supprime pas » ; Render sert `6d13e6e`, aucun fichier serveur n'a
  changé entre les deux — rien à redéployer).
- ⏰ **Reste** : le redémarrage des 4 services worker par Frédéric, FILE VIDE (elle l'était à la vérification), pour activer
  le 3e verrou ; puis l'essai réel (bouton absent sur le document signé de 61398).

## 7. ✅ LES TROIS VERROUS EN SERVICE (17/11) — prouvés

- **Worker** : Frédéric a redémarré les 4 services, file vide ; preuve par l'heure des processus : 4 processus Node
  démarrés à 11:39:38-39, APRÈS le commit du verrou (11:21). Les 4 services `Running`.
- **Essai réel, en lecture seule** (61398 n'est plus parmi les biens en cours) : fiche du bien EN COURS 63506 « Spécial
  investisseurs », « Médias & pièces » : le « Mandat 19006 » signé le 16/11 à 13:43 affiche « Signé : ne se supprime
  pas » à la place du bouton ; tous les documents non signés gardent « Supprimer ». Capture :
  `notice/preuve_blocage_suppression_signe_2026-11-17.jpg`. Aucun clic d'écriture.
- Non éprouvé en réel (volontairement, ce serait une suppression) : le refus du worker et de la base sur un travail posé
  à la main — prouvés hors ligne (17 + 7 contrôles, témoins inverses compris).

