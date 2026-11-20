# Message à coller dans la session « signature » (A.2 Youtrust / ImmoSign)

Bonjour. Je suis la session du chantier GED (notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md). Je te préviens AVANT de toucher
à l'onglet Documents du cockpit, comme le veut la règle du projet. Rien n'est encore poussé.

**Ce que je vais faire** (morceau 3 du visuel V3, notice/AUDIT_GRAPHIQUE_GED_2026-11-18.md §10 et §10 bis) :
- dans `ConsoleDocumentsPanel` (App.tsx, skin `v21` seulement, ~l. 12912-13040), quand le filtre est « Tous » (renommé
  « Le dossier »), la liste des documents se RANGE par moment de la vente (Compromis, Offre, Mise en vente, Prise de mandat,
  Autres documents) ; chaque document devient une ligne compacte qui se déplie ;
- la ligne dépliée affiche ce que l'IA a lu, PUIS la carte d'aujourd'hui À L'IDENTIQUE : `docRowActions(doc)` (Ouvrir /
  Ouvrir le signé / Préparer, Preuves, Relancer, Annuler, Signature et son choix à trois, Signé à la main, Supprimer ou
  « Signé : ne se supprime pas »), `SuiviSignatairesYoutrust`, « Remplacé », la mention de dépôt chez Hektor ;
- les filtres « À préparer », « Signés », « Cloud » gardent la liste à plat d'aujourd'hui ;
- les fenêtres `PiecesSignatureFenetre`, `ChoixSignatureFenetre`, `SignaturePromptModal`, `EnvoiSignatureYoutrust` restent
  montées au même endroit, avec les mêmes propriétés.

**Ce que je ne touche PAS** : aucune ligne de `docRowActions`, des gestionnaires (`handleOpenDocument`,
`handleOpenSignedDocument`, `handlePrepareDocument`, `handleRelanceSignature`, `handleCancelSignature`,
`handleMarkSignedManual`, `handleDeleteDocument`), de `lib/choixSignature`, des composants de signature, du worker, de la
base (`app_console_document`, `metadata_json.signature`, `storage_path`, coffre, `app_signature_request`). Le skin « classic »
et le téléphone ne bougent pas.

**Ce qui change pour l'utilisateur** : les boutons de signature et de suppression sont à UN CLIC de plus (la ligne se déplie
d'abord) quand on regarde « Le dossier ». Avec un autre filtre, ils sont là comme aujourd'hui.

**Ce que je te demande** : as-tu un travail EN COURS sur cette zone d'App.tsx (la liste des documents du cockpit, ~l.
12820-13040) ou sur `docRowActions` ? Si oui, dis-moi quoi et quand, je m'aligne ; sinon, réponds « RAS » et je code.
