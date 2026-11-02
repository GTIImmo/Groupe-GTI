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
