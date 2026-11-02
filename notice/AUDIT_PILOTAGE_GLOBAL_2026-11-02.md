# Audit du PILOTAGE GLOBAL (réseau d'agences) — 02/11/2026

> Demande de Frédéric (02/11) : « écran Pilotage dédié en commençant par Ventes, puis propose-moi Mandats,
> Estimations, etc. ; audit complet des outils actuels (Google, bons de visite, états des lieux…) ; un design à la
> hauteur des derniers CRM métiers ». **Audit en LECTURE SEULE** : aucune écriture en base, aucun appel à Hektor,
> Google, ImmoSign ou Youtrust, aucun script lancé. Quatre audits menés en parallèle, puis mesures complémentaires.
> L'onglet Ventes est déjà audité dans `AUDIT_GESTES_REGISTRE_TRANSACTIONS_2026-10-30.md` § 16
> (maquette https://claude.ai/artifact/CJ9v7PnqkNvYHNGsG8R1Qr). **RIEN CODÉ.**

Grille objets × gestes : le pilotage ne fait que **lire**. Objets lus : transaction, mandat, annonce (stock,
estimation), contact, recherche, document / signature, RDV / visite. Aucun geste créer / modifier / supprimer.

## 1. Les outils Google (un seul canal : clé de service Workspace, au nom d'accueil@)

`backend/app/settings.py:121-130`, `backend/app/services/google_workspace_service.py:19-68` ; droits gmail.send,
gmail.readonly, calendar.freebusy, calendar.events, spreadsheets.

- **Classeur « Offres en cours et compromis »** (AppSheet, Sheet1, 4 775 lignes, 98 % rattachées par
  `app_classeur_lien`, 12 413 liens gelés). Lu À LA MAIN par `phase2/checks/apparier_classeur.py` & co ; l'écrivain
  `scheduled/push_suivi_appsheet.py` est DORMANT (aucune tâche ne l'appelle). ⭐ **Seule source** de : la commission
  saisie (P `Commission TTC`, Q `Charge Commission`), la répartition à plusieurs (I-N, 659 lignes à deux personnes),
  l'**encaissement** (Y `Vente Réglée`) et le **numéro de facture** (AA, 365/367), les dates « vente prévue / fixée /
  annulée ». **0 valeur du classeur n'est entrée chez nous.** Onglets calculés (Calcul Salaire, 12 mois lissants, CA
  Mensuel, Reporting, Estimation = 916 factures d'estimation) écrits par des Apps Script JAMAIS LUS (verrou V1, à
  Frédéric). **Aucun onglet d'objectifs trouvé.**
- **Google Agenda** : nous → Google seulement (créer / modifier / supprimer, créneaux libres). DORMANT :
  `app_google_calendar_event_link` = 11 lignes, toutes du 02 au 15/06. Rien ne lit l'agenda.
- **Gmail envoi** : alertes (en service) ; envois clients quasi à l'arrêt (`app_email_envoi` 84 du 24/06 au 12/10 ;
  relances auto bloquées par défaut, `relance_worker.py:64,112`). **Gmail lecture** : les e-mails d'un contact dans sa
  fiche (80 usages), rien de stocké.
- **Prise de RDV publique** : 2 292 liens (435 actifs) mais **0 demande** (`app_appointment_request`).
- Drive, Maps : non utilisés (géocodage = BAN).

## 2. Visites, états des lieux, signatures, estimations, documents

- **Visites : pas de source fiable.** 2 226 bons de visite déposés (≈ 1 600 dossiers) **sans date** (elle n'est que
  dans le PDF) ; 978 « modèles » ne sont pas des visites ; demandes de visite de l'espace acquéreur : 3 ; agenda Hektor
  importé nulle part (`notice/HISTORIQUE_VISITES_HEKTOR_2026-10-15.md`, pistes A/B/C non décidées).
- **États des lieux : n'existent pas ici.** Aucun bien en location (`offre_type` ∈ {0, 6, 10}), aucun écran ni travail.
- **Signatures ImmoSign (via Hektor), EN SERVICE** : `app_console_document.metadata_json.signature` — **456 signés**
  (397 dossiers ; févr. 2 · mars 58 · avr. 48 · mai 66 · juin 71 · juil. 51 · août 38 · sept. 60 · oct. 62), **56 en
  attente** ; presque tous des mandats. `sent_at` peu fiable (heure où la synchro l'a vu). Youtrust : DORMANT (off,
  0 ligne).
- **Estimations** : les **12 807 « Estimation »** de `app_dossier_current` sont **toutes les fiches jamais passées en
  mandat depuis 2017** (statut par défaut d'une annonce Hektor), vraies estimations et simples fiches mêlées ; 2026 =
  780 créées, 2025 = 1 222 encore à ce statut (biais du survivant). Outils propres à l'app quasi vides (33 estimations,
  37 PDF, 8 e-mails). ⚠ **Le taux estimation → mandat n'est pas calculable proprement** : pas d'historique des statuts,
  et un bien vendu / clos perd sa date de création (les index archive / historique n'ont que `date_maj`).
- **Documents** : 193 152 fiches ; règle « tout sur le serveur, copie au coffre pour les biens vivants ».

## 3. Inventaire de la base pour les autres onglets (mesures du 02/11, « à même date » = 01/01 → 02/11)

- **Mandats** (`app_mandat_register_current`, hors origine `recherche`) : **682 débutés en 2026 contre 685** ; exclusifs
  **253 contre 315 (37 % contre 46 %)**. Par mois 2026 : 64, 79, 74, 72, 69, 82, 53, 52, 59, 62 ; 2025 : 68, 68, 78, 55,
  85, 57, 64, 49, 79, 64, 48, 52. Par agence 2026 / 2025 (exclusifs 2026) : Issoire 71/31 (44), Saint-Étienne 62/63 (7),
  Craponne 61/46 (35), Ambert 57/46 (27), Courpière 55/51 (27), Annonay 49/49 (28), Firminy 47/62 (15), Le Puy 45/52
  (23), Yssingeaux 43/50 (16), Tence 40/62 (4), Dunières 32/26 (10), Brioude 25/38 (3), Monistrol 18/30 (3),
  Saint-Didier 18/14 (4), Saint-Just 16/13 (1), Saint-Bonnet 15/20 (1), Montbrison 12/14 (5).
  ⚠ Agences en trois écritures (« Groupe GTI Ambert␣␣␣ », « Groupe Gti Le Puy en Velay », « COURPIÈRE ») → il faut
  une **table d'alias**, pas seulement `trim`. La date de clôture est inutilisable pour comparer (212 lignes).
- **Stock** (`app_dossier_current`, photo du jour, **aucune comparaison N-1 possible**) : 570 Actif (332 diffusés),
  43 Sous offre, 86 Sous compromis ; âge moyen 189-210 j ; 18 mandats actifs échoient sous 30 j, 26 déjà échus ;
  159 sans date de fin, 157 sans numéro de mandat. Par agence (actifs / engagés) : Issoire 81/14, Craponne 60/15,
  Courpière 56/18, Yssingeaux 39/14, Firminy 39/5, Saint-Étienne 39/10, Ambert 38/11, Annonay 35/6, Dunières 32/4,
  Brioude 31/1, Le Puy 27/12, Tence 23/6, Monistrol 17/1, Saint-Didier 17/7, Saint-Just 16/2, Montbrison 11/2,
  Saint-Bonnet 9/1. ⚠ **Baisses de prix surcomptées** : 169 actifs « avec changement », seulement **87 vraies baisses**
  (médiane −6,2 %), 21 hausses, 59 sans ancien prix ; détection depuis le 20/06/2026 seulement.
- **Acquéreurs** : 4 240 recherches actives, dont 560 touchées depuis moins de 3 mois et 1 315 depuis plus d'un an ;
  fiches acquéreur créées **1 450 contre 1 353**. ⚠ Aucune date de création de recherche ; auto-archivage Hektor à 2 ans.
- **Contacts** : 3 157 créés contre 3 659 en brut, mais **2 387 contre 2 299** en « personne seule » (la nature des
  fiches a changé : couples) — le total brut ferait croire à −14 %. **Aucune origine de lead** en base.
- **Diffusion** (photo du jour) : etreproprio 292, superimmo 290, leboncoin 270 (7 en erreur), bienici 218 ; 16 actifs
  diffusables sans aucun portail en succès, 73 pas sur Leboncoin.
- **Rapprochements** : 54 899 (28 322 à 80 ou plus) depuis le 13/06 ; seulement 15 propositions — ce n'est pas une
  activité.
- **Activité des négociateurs** : mesurable = mandats, exclusifs, contacts, stock détenu, ventes, honoraires.
  ⛔ `app_console_job` mesure l'usage de l'app (93 675 synchros de documents sur 111 856), pas l'activité commerciale.
  Visites, appels, RDV : non disponibles.
- **Réutilisable** : `RapprochementStats.tsx:17` (+ `app_get_rapprochement_stats`, `app_stat_negociateur_v`),
  `SanteSystemeScreen.tsx:288` (fraîcheur), `homeDateWithinDays` (App.tsx ~26004). ⚠ Les compteurs de l'accueil et
  `loadMandatStats` (api.ts:7159) comptent sur des listes paginées : pas fiables pour un compte réseau.

## 4. Bonnes pratiques retenues (recherche web, détail des sources dans le compte rendu de conversation)

Sources fiables : aides officielles Reapit, Rex, Lofty, HubSpot, Salesforce, Linear, Pipedrive, Attio ; recherche UX
NN/g ; Carbon (IBM). Les éditeurs français ne documentent presque rien.
1. Une **barre de filtres unique** (période, agence, négociateur, comparaison N-1) gardée dans l'adresse.
2. **Chaque chiffre ouvre la liste filtrée**, et le compte doit concorder (piège documenté chez HubSpot).
3. En tête, **4 à 6 cartes** : valeur, écart signé avec flèche (jamais la couleur seule), mini-courbe 12 mois.
4. Modules : activité, mandats & stock, estimations, ventes & honoraires, classements, objectifs (Reapit, Rex).
5. **Entonnoir sur une cohorte datée**, distinct de la **photo du stock** (Attio).
6. Indicateurs français en tête : exclusivité, transformation estimation → mandat, délais, baisses de prix.
7. Honoraires **toujours dits HT ou TTC**.
8. Classements en **barres triées**, ni podium, ni jauge ronde, ni camembert (NN/g) ; objectif en barre-repère.
9. Objectifs exprimés en **rythme** (« en avance / en retard au jour J »).
10. **Date de fraîcheur** sur chaque carte, mention « estimé » quand c'en est un, export PDF / CSV, téléphone réduit
    aux cartes de tête.

## 5. Proposition (NON décidée) — l'écran Pilotage

Écran dédié dans le groupe « Pilotage » du menu (admins), une barre de filtres commune, des onglets :
- **Vue d'ensemble** : 6 cartes (honoraires, ventes, actes datés, mandats rentrés, exclusivité, stock engagé),
  le **tableau des agences** (honoraires, ventes, mandats, exclusivité, stock, engagés), les alertes (mandats échus).
- **Ventes** : maquette faite (§ 16 de la note du registre).
- **Mandats** : rentrés par mois / agence / négociateur, exclusivité, signés électroniquement, échéances.
- **Stock** : photo du jour — actifs, engagés, âge, vraies baisses de prix, non diffusés, échus.
- **Acquéreurs** : recherches actives et fraîches, demande face au stock par agence.
- **Équipe** : une ligne par négociateur, tous domaines.
- **Estimations : PAS en V1** — le chiffre serait faux (§ 2). Il faut d'abord une **photo quotidienne des statuts**.

## 6. Décisions qui reviennent à Frédéric

1. **Une photo quotidienne** (statut, prix, agence, négociateur de chaque annonce, et diffusion) : écriture nouvelle en
   base, dans le run de nuit. C'est elle qui rendra possibles la transformation estimation → mandat, le délai de vente,
   le stock d'il y a un an. Elle ne vaut que pour L'AVENIR (un journal ne sait rien d'avant sa naissance).
2. **Faire entrer chez nous les colonnes du classeur** (commission saisie, encaissement, facture, répartition à
   plusieurs) — c'est le chantier classeur (phase B), et ses Apps Script restent à lire.
3. **Les objectifs** : n'existent nulle part ; les saisir chez nous ?
4. **Les visites** : pistes A / B / C de la note du 15/10.
5. **HT ou TTC** par défaut à l'écran.
6. **Une table d'alias des agences**, pour qu'une agence ait un seul nom partout.

## 7. Maquette (02/11 soir) — https://claude.ai/artifact/CJ9v7PnqkNvYHNGsG8R1Qr

Deux planches, vraies données : **Vue d'ensemble** (onglets, barre de filtres commune collante, bascule TTC / HT,
6 cartes « résultat / avancé / à venir / photo du jour » avec mini-courbe 2026 et 2025 en pointillé, « ce qui rentre,
ce qui se vend » par mois, « À surveiller » cliquable, tableau des 17 agences) et **Ventes** (passée dans l'écran
Pilotage, la bascule du Registre est abandonnée). Mesure ajoutée : **171 biens actifs ont un mandat d'avant le
02/05/2026** (plus de 6 mois), 159 actifs sans date de mandat. ⏳ Attend son avis, RIEN CODÉ.

## 8. Correction (02/11 soir, question de Frédéric) — les visites, l'app les GÈRE

Mon § 2 disait « visites : pas de source fiable » sans dire que l'app sait **prendre un RDV de visite** et **générer
le bon de visite**. Relu dans le code :
- **Prendre le RDV** : depuis la recherche d'un acquéreur (« Planifier une visite », App.tsx ~24134), la fiche du bien
  et l'écran Agenda (`GoogleAgendaGlobalScreen`) ; le RDV est créé dans l'agenda Google du négociateur
  (`createGoogleCalendarEvent`, App.tsx ~38277) et noté chez nous dans `app_google_calendar_event_link` (type
  `visite`, bien, contact, heure, auteur, `bon_visite_ready`).
- **Le bon de visite** : fabriqué à la volée depuis ce RDV (`visitVoucherHtml`, `openVisitVoucherPrint`
  App.tsx:43152), ouvert dans une fenêtre pour impression. ⚠ **Il n'est enregistré nulle part** : aucune trace qu'il
  a été imprimé, aucun PDF gardé.
- **Usage mesuré** : 19 RDV créés (5 personnes), tous du 01 au 19/06 ; 11 liens en base (10 visites, 8 actives) ;
  **aucun depuis le 19/06**. L'agenda, lui, est consulté : 208 demandes de disponibilités, la dernière le 28/10.
- **Pour le pilotage** : un compteur « visites planifiées dans l'app » est possible tout de suite et juste (source
  `app_google_calendar_event_link`), mais il vaut ~0 tant que les agences prennent leurs visites ailleurs (agenda tapé
  à la main, Hektor). Pistes : garder une trace à chaque bon imprimé ; lire les agendas Google des négociateurs
  (note du 31/07) ; ou les bons déposés chez Hektor (2 226, sans date). À décider par Frédéric.

## 9. Réponses de Frédéric (02/11 soir)

- **Où sont pris les RDV de visite aujourd'hui** : dans Google Agenda directement et dans Hektor ; **ensuite
  uniquement dans l'app**, avec une synchro Google déjà prévue.
- **Compter les visites** : les **RDV pris dans l'app** (`app_google_calendar_event_link`, type `visite`), plus une
  trace à chaque bon de visite imprimé (à concevoir). Le chiffre montera avec l'adoption de l'app.
- **Objectifs** : pas maintenant (le pilotage compare à l'année précédente).
- **Accès et unité** : **administrateurs seuls**, honoraires **HT par défaut** (TTC d'un clic). La maquette est passée
  en HT par défaut. ⚠ HT = TTC / 1,2 dans la maquette : à vérifier au code (taux de TVA unique ?).

## 10. Onglets Mandats et Stock maquettés (02/11 soir, même lien)

**Mandats** (2026 à date contre 2025 à date, hors origine `recherche`) : par type — Simple **356 contre 277**,
Exclusif **253 contre 314**, Accord **54 contre 76** (prix médian au mandat 122 000 / 139 000 / 192 000 €) : le réseau
rentre autant de mandats mais en SIMPLE. Exclusivité par mois 2026 : 42, 43, 38, 43, 35, **28, 53, 31, 27**, 42 %.
Par négociateur (31 personnes) : BILLIG DURAND 61 (46), RIBBES 38 (25), PEREIRA 37 (27), DELAVAUD 34 (40), POUGET 33
(5), FORLICO 33 (31), PEYRARD 32, GENTES 32, TEYSSONNIER 31 (42, 4 exclusifs), REYNAUD 28 (1)… Signés
électroniquement : 456 (févr. → oct.), 56 en attente.
⚠ « ACCORD » : sens métier non vérifié (à demander à Frédéric).
**Stock** (photo du jour) : 570 en vente, **80,8 M€ affichés**, prix médian 120 000 € ; âge depuis le mandat : < 3 mois
127, 3-6 mois 113, 6-12 mois 131, > 1 an 40, sans date 159 (médiane 156 j) ; ⚠⚠ **238 actifs non diffusables (42 %)**,
dont 52 sur 81 à Issoire et 42 sur 60 à Craponne ; 16 diffusables sans aucun portail ; composition : simple 226,
exclusif 148 (26 %), accord 36, autre / vide 160 ; vraies baisses 87 (médiane −6,8 %) ; mandats échus encore en vente
26, dont **10 à Courpière** ; âge médian par agence de 58 j (Saint-Bonnet) à 283 j (Saint-Didier).
⏳ Attend son avis, RIEN CODÉ.

**02/11 soir — Frédéric : le type « ACCORD » = SEMI-EXCLUSIF.** Maquette renommée. Exclusifs + semi-exclusifs :
2026 (253 + 54) / 682 = **45 %** contre 2025 (314 + 76) / 685 = **57 %** (−12 points). L'indicateur principal reste
l'exclusif seul (37 % contre 46 %) ; le cumul s'affiche en second.

## 11. Stock : le C.A POTENTIEL mis en avant (02/11 soir, demande de Frédéric)

Frédéric : « il faut surtout mettre en avant le montant de C.A potentiel, donc les honoraires et non le prix de vente ».
**Source** : `app_dossier_detail_current.detail_payload_json` → clé `honoraires_json` (texte JSON : liste de
`{id, taux, charge}`, où `taux` est un MONTANT en euros — 919 entrées, toutes > 100, de 500 à 125 000 € ; `charge`
= `vendeur` 886 ou `Acheteur` 33). ⚠ Hektor y garde des COPIES : 426 biens ont 1 entrée, d'autres 2, 3, 5 ou 6
entrées identiques → règle : par bien et par charge, l'entrée au plus grand `id`, puis somme des charges.
**Mesuré (TTC supposé, comme le registre)** : biens en vente **3 768 418 €** sur 406 / 570 biens (taux médian 6,51 %
du prix, honoraires médians 8 000 €) ; sous compromis 624 855 € (76 / 86), sous offre 291 710 € (39 / 43) ;
164 biens sans honoraires saisis (prix non couvert 14 204 409 € → ≈ 924 707 € estimés au taux médian), **dont 122
parmi les 159 biens sans date de mandat** ; Issoire : 51 sur 81 sans honoraires. Par ancienneté : < 3 mois 944 512,
3-6 mois 1 046 657, 6-12 mois 1 029 233, > 1 an 274 680, sans date 473 336. Par type : simple 1 703 952, exclusif
1 235 670, semi-exclusif 349 460, non renseigné 479 336. **Biens non diffusables : 943 735 €** d'honoraires.
Au rythme 2026 (2,17 M€ TTC en 10 mois), le stock vaut ≈ 17 mois d'honoraires. Maquette Stock refaite autour de ce
chiffre (HT par défaut) ; la 6e carte de la Vue d'ensemble devient « C.A potentiel du stock ».
⚠ À vérifier au code : que ces honoraires d'annonce sont bien TTC ; les écarts avec les honoraires du registre
pour les biens engagés (deux sources pour un même compromis).

## 12. CODÉ (02/11 soir, « go code ») — commit 12dcff1, NON POUSSÉ, patch base NON POSÉ

- **Écran** `PilotageScreen.tsx` + `pilotage.css` (préfixe `pl-`), **lectures et calculs** `lib/pilotage.ts`, entrée de
  menu « Pilotage » (bureau et téléphone) **pour les admins seuls** (`isAdmin`, garde qui renvoie vers Annonces),
  adresse `?ecran=pilotage`. Quatre onglets (vue d'ensemble, ventes, mandats, stock) + « Estimations bientôt ».
  Filtres : période (2007 → année en cours « à date »), agence (clé unique `cleAgence`, 3 écritures en base),
  comparer à N-1 « à la même date », HT (défaut) / TTC. Onglet et HT/TTC gardés dans le navigateur.
- **Sources** : `app_registre_dossiers` N et N-1 + `app_affaire_repartition` (par paquets de 150 dossiers) ;
  `app_mandat_register_current` depuis le 1er janvier N-1 (hors origine `recherche`) ; `app_console_document`
  (signatures signées / en attente) ; `app_mandat_broadcast_current` (portails) ; **`app_pilotage_stock()`** (nouvelle).
  Une source qui ne se lit pas n'éteint que son bloc (« n'a pas pu être lu » + Réessayer, détail en console).
- **Base** : `supabase/patch_pilotage_stock_2026-11-02.sql` (+ `_INVERSE`, `_REPETITION`) — fonction en LECTURE seule,
  admins seuls (0 ligne sinon), clé publique refusée. Éprouvée en transaction annulée : 699 biens, 521 avec
  honoraires, Actif 3 768 418 €, 0 honoraire > 20 % du prix, **0,4 s**. ⏳ **À POSER avec l'accord de Frédéric** ;
  tant qu'elle n'est pas posée, l'onglet Stock et les cartes qui en dépendent affichent « n'a pas pu être lu ».
- **Contrôles** : `npm run build` vert ; maquette locale (données inventées, sans base) à 1 440 px et 375 px :
  4 onglets rendus, 0 erreur console, 0 débordement mesuré ; onglet actif ramené en vue sur téléphone.
  ⚠ **Non vu sur les vraies données** (il faut le push, puis le patch).
- **Pas dans cette version** (dit à Frédéric) : filtre négociateur ; clic d'un chiffre vers la liste filtrée d'un autre
  écran (le clic change d'onglet ou filtre l'agence) ; export ; visites ; objectifs (décision : pas maintenant).

**02/11 nuit — `app_pilotage_stock()` POSÉE EN PRODUCTION** (accord de Frédéric : « Oui, pose-la »), par migration
`patch_pilotage_stock_2026_11_02`, bloc de preuve passé (0 ligne sans utilisateur, clé publique refusée).
Répétition avec les droits de Frédéric : **5/5 OK** — 699 / 699 biens, 521 avec honoraires, Actif 3 768 418 €,
0 honoraire au-delà de 20 % du prix. **Témoin inverse** : un compte négociateur (pereira) → 0 ligne, `is_app_admin` faux.
Retour arrière : `supabase/patch_pilotage_stock_2026-11-02_INVERSE.sql`. ⏳ Reste : le push (Frédéric), puis voir
l'écran sur les vraies données.

## 13. Stock : le périmètre à revoir (02/11 nuit, Frédéric) — « une annonce active ne veut pas dire qu'il y a un mandat »

Mesuré (lecture seule) sur les annonces « Actif » : **413 sur 570 ont un mandat** — numéro de mandat ET ligne au
registre des mandats (origine `actif`), les deux concordent à l'unité ; 157 n'en ont aucun. L'entonnoir, honoraires TTC :
- 570 annonces actives — 3 768 418 € ;
- **413 avec mandat** — 3 320 082 € (157 sans mandat, dont 35 portent pourtant 448 336 € d'honoraires) ;
- **387 mandat en cours** (date de fin non passée ; 2 sans date de fin) — **3 140 652 €** ; 26 échus ;
- **315 diffusables** — 2 695 283 € ;
- **301 en ligne** sur au moins un portail — 2 619 983 €.
42 biens avec mandat n'ont pas d'honoraires saisis. Engagés : sous compromis 81 / 86 avec mandat (57 en cours, 24 échus),
sous offre 43 / 43 (36 en cours, 7 échus).
⚠ Pour le coder juste, `app_pilotage_stock()` doit rendre `numero_mandat` (la date de début manque sur 2 biens qui ont
un numéro) : changement de la fonction = écriture en base, à faire avec son accord. RIEN CODÉ.

## 14. Stock = les 699 biens, rangés par l'ESCALIER de l'app (02/11 nuit, demande de Frédéric)

**Comment l'app distingue un bien** (code, pas les notes) — `listingProgressLabel` (App.tsx:8214) : Estimation →
Vendu (`vente_id`) → Compromis en cours (`compromis_id`) → Offre en cours (`offre_id`) → « Annonce créée · mandat
manquant » (pas de `numero_mandat`) → « Mandat à valider » (`validation_diffusion_state` ≠ validé : c'est la
validation de Pauline) → « Diffusé » (`diffusable` = 1 ET `nb_portails_actifs` > 0) → « Mandat validé · non diffusé »
(diffusable mais sur aucun portail) → « Mandat validé · diffusion à ouvrir » (diffusable = 0). En plus : le statut
Hektor (`statut_annonce` Actif / Sous offre / Sous compromis), l'état des transactions (`offre_state` proposée /
acceptée / refusée, `compromis_state` en cours / annulé), la date d'acte prévue (registre des transactions), le mandat
échu (`mandat_date_fin` passée, `isMandateEndDateStillValid`), la signature du mandat (document : à envoyer / envoyé /
signé, `metadata_json.signature`). Il n'existe ni `statut_global` ni `sous_statut` rempli (0 sur 699).
⚠ **Défaut de l'escalier, mesuré** : il range par PRÉSENCE de `offre_id` / `compromis_id`, pas par leur état —
10 biens « Actif » avec une offre REFUSÉE et 3 avec un compromis ANNULÉ y sont classés « offre / compromis en cours ».
Proposé pour le pilotage : le statut de Hektor d'abord (Sous compromis, Sous offre), l'escalier du mandat ensuite.
**Mesure (honoraires d'annonce, TTC / HT)** :
1. annonce active sans mandat 157 — 448 336 / 373 613 (35 seulement ont des honoraires) ;
2. mandat à valider 69 — 397 425 / 331 188 (8 échus) ;
3. mandat validé · diffusion à ouvrir 14 — 97 974 / 81 645 ;
4. diffusable · sur aucun portail 14 — 75 300 / 62 750 ;
5. **diffusé 316 — 2 749 383 / 2 291 153** (15 échus) ;
6. offre en cours 43 — 291 710 / 243 092 ;
7. compromis, acte daté à venir 72 — 521 580 / 434 650 ; compromis, date d'acte dépassée 14 — 103 275 / 86 063.
Total 699 — 4 684 983 / 3 904 153. Mandats échus parmi eux : 57.
⚠ Deux sources pour les biens engagés : honoraires de l'ANNONCE (compromis à venir 521 580 €) et du REGISTRE des
transactions (actes datés 808 003 €, onglet Ventes) — à aligner au code. RIEN CODÉ, attend son avis.

## 15. Analyse : un raisonnement PROPRE à chaque onglet (02/11 nuit, demande de Frédéric)

Frédéric : « je ne voulais pas imposer ce raisonnement ; il y a encore Mandats et Acquéreurs, donc le Stock doit avoir
un raisonnement propre ». Principe proposé : **chaque onglet répond à UNE question, avec SON périmètre et SON unité de
temps**, et les onglets s'enchaînent comme le métier : la demande (acquéreurs) et l'offre qui entre (mandats) → ce
qu'on a à vendre (stock) → ce qui sort (ventes).

**Mesures nouvelles (lecture seule, droits de Frédéric)** :
- **Devenir des mandats, par cohorte** (mandats débutés en 2024 / en 2025, état au 02/11/2026) :
  exclusif 2024 : 357 → **59 % vendus**, 36 % sortis sans vente, médiane mandat → vente 203 j (→ compromis 107 j) ;
  simple 2024 : 419 → **28 % vendus**, 69 % sortis sans vente, 235 j (→ compromis 127 j) ;
  semi-exclusif 2024 : 121 → 40 % vendus, 56 % sortis. Cohorte 2025 : exclusif 48 %, simple 30 %, semi 28 % (encore
  ouverte : 4-6 % engagés, 5-6 % en vente). Prix obtenu ≈ 93 à 97 % du prix du mandat (médiane).
  ⚠ « sorti sans vente » mêle les biens retirés, vendus par un confrère (mandat simple) et les cas où la vente n'est pas
  reliée au mandat (identifiants recyclés de 2026) : à éprouver avant de l'afficher comme un taux.
- **Aboutissement d'un compromis** (dossiers 2022-2025) : 1 691 vendus, 249 annulés, 10 encore en cours → **≈ 87 %**.
- **Rythme de vente** : 347 ventes sur les 12 derniers mois (≈ 29 / mois). **Stock sous mandat : 537 biens**
  (413 disponibles, 43 sous offre, 81 sous compromis), **4 219 647 € TTC** d'honoraires ; 387 disponibles à mandat en
  cours → **≈ 13 mois de stock** au rythme actuel.

**Proposition (NON décidée)** :
- **Stock** = « qu'avons-nous à vendre AUJOURD'HUI, combien ça vaut, est-ce que ça s'écoule ? » — périmètre = les biens
  SOUS MANDAT (537), disponibles / engagés. Cinq questions : ce qu'on a ; ce que ça vaut (C.A potentiel ET C.A attendu
  pondéré par les taux mesurés) ; est-ce que ça s'écoule (mois de stock, âge face au délai médian de vente, vraies
  baisses) ; est-ce exposé (diffusé / pas en ligne / mandat à valider) ; est-ce en règle (mandat échu, honoraires non
  saisis). Les 157 annonces actives sans mandat SORTENT du stock et vont dans Mandats (« à régulariser »).
- **Mandats** = « rentre-t-on assez de BONS mandats, et que deviennent-ils ? » — flux de la période (rentrés,
  exclusivité, prix) + cohortes (vendus / engagés / en vente / sortis, délais) + la production (annonces sans mandat,
  mandats à signer, à valider, échéances).
- **Ventes** = le résultat (inchangé), + l'aboutissement des compromis.
- **Acquéreurs** = « a-t-on les acheteurs de notre stock ? » — recherches actives et fraîches, budgets, rapprochements,
  visites prises dans l'app (choix du 02/11), demande face au stock par agence.
- **Vue d'ensemble** = l'équation : entrées (mandats) → stock → sorties (ventes, retraits), + le C.A attendu total
  (actes datés + stock pondéré).
Prérequis signalé : la photo quotidienne (évolution du stock, sorties sans vente datées). RIEN CODÉ.

## 16. Re-audit et proposition OPTIMISÉE, + le PRÉVISIONNEL DES ENCAISSEMENTS (02/11 nuit)

**Re-audit** :
- Cohortes de mandats : les « sortis sans vente » sont à **98 % des annonces passées « Clos »** (simple 275 / 280,
  exclusif 120 / 126, semi 65 / 65) ; 4 seulement sont des ventes mal reliées, 1 vente antérieure au mandat. La mesure tient.
- Taux d'aboutissement : compromis → vente ≈ **87 %** ; offre acceptée → vente ≈ **86 %** (1 594 / 1 862, 2022-2025).
- ⛔ **Deux ERREURS DE SAISIE dans le registre des transactions faussent les « actes déjà datés »** : dossier 1386917
  (183 700 € d'honoraires pour 193 000 € de prix, acte prévu 15/06/2027) et 1388289 (93 000 € pour 100 000 €, acte
  14/11/2026). Sans eux, les actes datés valent **531 303 € TTC**, pas 808 003 € (les honoraires d'annonce disent 527 580 €).
  L'onglet Ventes codé (12dcff1) affiche donc 808 k€ : à corriger (écarter et signaler tout honoraire > 20 % du prix).
- Stock sous mandat : **537 biens, 3 516 373 € HT** de C.A potentiel, **1 778 600 € HT** attendus une fois pondérés
  (compromis 87 %, offre 86 %, exclusif 59 %, semi 40 %, simple 28 % — taux des cohortes 2024) ; 150 disponibles sur
  411 datés dépassent le délai médian de vente (203 j) ; 106 disponibles n'ont AUCUN acquéreur rapproché à 80 ou plus
  (307 en ont au moins un, médiane 14).
- **Offre et demande par prix** (disponibles sous mandat / recherches actives) : < 100 k€ 183 / 1 012 (5,5 acheteurs
  par bien) · 100-150 k€ 63 / 802 (12,7) · 150-200 k€ 56 / 637 (11,4) · 200-300 k€ 63 / 942 (15,0) · ≥ 300 k€ 42 / 645
  (15,4). 45 % du stock est sous 100 k€, là où la demande par bien est la plus faible.

**Prévisionnel des encaissements** (demande de Frédéric : « il faut quelque part un prévisionnel des futurs
encaissements »). Les honoraires s'encaissent à l'acte. Trois couches par mois, HT, pondérées :
1. actes déjà datés (registre, sans les 2 erreurs) × 87 % ; 2. offres en cours : acte estimé à la date de l'offre +
120 j (médiane mesurée offre → acte), × 86 % ; 3. stock disponible pondéré (1,13 M€ HT), réparti sur les mois +4 à +12
— INDICATIF. Total 12 mois ≈ **1,80 M€ HT**, à comparer aux **2,19 M€ HT** encaissés sur les 12 derniers mois : l'écart
(≈ 0,39 M€) viendra des mandats encore à rentrer. ⚠ L'encaissement réel (date « Vente réglée ») n'est que dans le
classeur Google : tant qu'il n'est pas chez nous, « encaissé » = « acte signé ».

**Proposition optimisée** (onglets, chacun une question) : Vue d'ensemble (prévisionnel, équation du réseau, tableau
des agences) · Ventes (résultat) · Mandats (entrées et devenir) · Stock (portefeuille sous mandat, potentiel / attendu,
écoulement, mise en marché, en règle) · Acquéreurs (demande, offre face à la demande par prix, biens sans acheteur).
Design : une couleur par domaine (validées au contrôle de palette : Stock #1a9a6c, Mandats #2f6fd0, Ventes #c5005f,
Acquéreurs #6a55d8), dégradés ordonnés validés, pas d'anneau ni de camembert, une seule échelle par graphique.

## 17. Maquette v2 (02/11 nuit) — https://claude.ai/artifact/CJ9v7PnqkNvYHNGsG8R1Qr, 5 planches, RIEN CODÉ

- **Vue d'ensemble** : en tête le **prévisionnel des encaissements sur 12 mois** (1,80 M€ HT pondérés ; trois couches :
  actes datés × 87 %, offres × 86 % à + 4 mois, stock disponible pondéré en texture « tendance » ; trait = encaissé le
  même mois l'an passé ; « à combler : 0,39 M€ par les mandats à venir ») ; **l'équation du réseau** (682 mandats →
  537 sous mandat → 287 ventes ; « 4 mandats sur 10 deviennent une vente ») ; 6 cartes ; **tableau des agences**
  (honoraires et mandats avec écart, exclusivité avec repère réseau, disponibles, mois de stock teinté vite / lent,
  C.A attendu, biens sans acheteur).
- **Mandats** : 4 cartes (dont « taux de vente d'un mandat » 42 %) ; **le devenir des mandats 2024 par type** en barres
  100 % (exclusif 59 % vendus en 203 j, semi 40 %, simple 28 % en 235 j) ; mandats par mois exclusifs / autres avec
  trait 2025 ; **la production à faire** (157 annonces sans mandat, 69 à valider, 56 signatures, 18 échéances, 26 échus) ;
  agences et négociateurs.
- **Stock** (périmètre affiché : SOUS MANDAT) : **C.A potentiel 3,52 M€ HT et C.A attendu 1,78 M€ HT** côte à côte,
  barre par étape (compromis, offre, exclusif, semi, simple ; plein = attendu) ; disponibles 413, **13,4 mois de stock**,
  36 % au-delà du délai habituel, 106 sans acheteur ; **mise en marché** 413 → 344 validés → 330 diffusables → 316 en
  ligne ; âge mesuré (< 3 mois 127 · 3-6 113 · 6-9 91 · 9-12 40 · > 1 an 40) avec le repère 203 j ; « en règle ? » ;
  agences triées par C.A attendu.
- **Acquéreurs** (nouveau) : 4 240 recherches actives, 560 récentes, 1 450 nouveaux acquéreurs (+7 %), 106 biens sans
  acheteur ; **offre face à la demande par prix** en barres opposées avec « acheteurs par bien » (5,5 sous 100 k€ contre
  15 entre 200 et 300 k€) ; couverture du stock (230 / 77 / 106) ; demande par agence (5 premières) ; visites app = 0.
- **Ventes** : planche v1 gardée, actes datés corrigés à 531 303 € (2 aberrants écartés).
Design : palettes passées au validateur (domaines + dégradés ordonnés), barres et barres 100 %, aucune jauge ronde,
une échelle par graphique, chiffres en tabulaires, couleur jamais seule (signes ▲ ▼, étiquettes).
⚠ Le code en place (12dcff1, non poussé) suit encore la maquette v1 : à refaire après validation de la v2, et l'onglet
Ventes y affiche 808 k€ d'actes datés (les 2 aberrants) — à corriger dans la même passe.
