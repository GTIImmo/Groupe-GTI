# Registre des transactions — audit des gestes depuis un bien VENDU (30/10/2026)

> **Audit limité à l'objet TRANSACTION** (offre, compromis, vente), vu depuis la future vue
> « Registre des transactions ». Les autres objets ne sont pas mesurés ici.
> Lecture seule : code + base. Rien n'est écrit, rien n'est codé.
> Maquette : https://claude.ai/artifact/3FA3yDqWuDWuqLdZAkvS8x · mémoire : `vue-registre-transactions-maquette`.

## 1. La question

La maquette promet, sur chaque ligne du registre, un menu « ··· » qui rouvre **les fenêtres qui
existent déjà**. Pour un dossier vendu : « Modifier la vente », « Répartition des honoraires »,
« Supprimer la vente ». Ces gestes marchent-ils pour un bien vendu, alors que ce bien a quitté
`app_dossier_current` ?

## 2. Ce que fait le code aujourd'hui

- La fenêtre de statut s'ouvre par `openStatusChangeModal(dossier: Dossier)` (App.tsx ~17737).
  Elle lit les transactions du bien par `loadAffairesForDossier(dossier.app_dossier_id)`
  (api.ts:1974, filtre `app_affaire_ledger.app_dossier_id`).
- Elle n'a que **deux appelants**, les deux fiches annonce (bureau ~24347, téléphone ~25410),
  et seulement pour un gestionnaire ou un admin.
- Dans la fiche au bureau, le bouton « Faire évoluer le statut » est **caché** si la fiche est
  « légère » (App.tsx:32518 : `!isLightweightDetail && ckStage !== 'archive'`).
- Une fiche est légère (App.tsx:440, `isReadOnlyLightweightDetail`) si le bien est archivé, si
  c'est un brouillon, ou s'il est au statut historique **sans fiche complète en cache**.
- Pour un bien historique, la fiche complète est lue dans `app_historical_annonce_detail_cache`,
  **et seulement si `expires_at` n'est pas dépassé** (api.ts, `loadLightweightAnnonceDetailCache`).

## 3. Ce que dit la base (30/10)

Les **287 biens** qui ont une vente datée de 2026 :
- **0** sont dans `app_dossier_current` ;
- **257** sont dans l'index historique et **30** dans l'index des archives. Tous les biens sont donc
  joignables ;
- pour les 257 historiques, le numéro interne `app_historical_id` est **égal** à l'`app_dossier_id`
  du registre (257/257). Le lien entre la fiche et ses transactions est donc bon ;
- **mais seuls 7 ont une fiche complète en cache, et 0 de ces caches est encore valide.**

## 4. Conclusion

⚠⚠ **Aujourd'hui, une fois qu'un bien vendu a quitté les annonces vivantes, aucun geste de
transaction n'est accessible depuis l'écran** : ni modifier, ni supprimer la vente, ni
la répartition par la fenêtre de statut. La fiche s'ouvre en lecture seule (fiche légère, ou
archive) et le bouton de statut est caché.

Pourtant l'écran dit lui-même, quand on tente une nouvelle transaction sur un bien vendu :
« Pour revenir en arrière, il faut d'abord supprimer la vente » (App.tsx ~18795). Ce geste
n'est donc possible **que tant que le bien est encore dans les annonces vivantes**.

➡ **Le registre serait le premier endroit où l'on agit sur un dossier vendu après son départ.**
Ce n'est pas un détail d'affichage : c'est une décision de Frédéric.
- **A** — le registre reste **en lecture seule** pour un dossier vendu (comme la fiche
  aujourd'hui), et ses gestes ne concernent que les dossiers en cours.
- **B** — le registre ouvre la fenêtre existante pour un dossier vendu, avec un `Dossier`
  construit à partir de l'index historique ou des archives (le numéro interne concorde, 257/257).
  ⚠ Non éprouvé : que la fenêtre et le worker acceptent un bien qui n'est plus dans les annonces
  vivantes. Il faudrait un essai réel, sur une cible choisie par Frédéric et avec son accord.

## 5. Grille de l'objet transaction (vue Registre)

- **créer** : la fenêtre de statut (offre, compromis ou vente), sur un bien **Actif** seulement.
  Elle est refusée sur un bien vendu, clos ou en estimation (App.tsx ~18790), et une nouvelle
  offre est refusée sur un bien engagé (`nouvelleOffreFermeeSurBienEngage`). Pour le registre,
  cela suffit : « Nouvelle offre » = choisir un bien Actif, puis ouvrir la fenêtre.
- **modifier** : même fenêtre en mode « reprendre » (`modifierAffaireId`). Accessible
  **seulement depuis une fiche complète** (voir § 4). ⬜ Non mesuré : le mode « reprendre » pour
  chacun des trois types (offre, compromis, vente).
- **annuler / refuser / supprimer** : `gesteAffaireOptimistic(app_affaire_id, refus | accepte |
  annuler | supprimer)`. Il ne dépend que du numéro de la transaction, pas de la fiche. Les verrous
  vivent en base :
  - une offre ne bouge plus si son dossier porte un compromis vivant ou une vente (16/09) ;
  - un compromis ne bouge plus si son dossier porte une vente (23/10, interrupteur
    `compromis_verrouille_par_vente`).
- **lire** : aujourd'hui, seulement par bien (`loadAffairesForDossier`). Le registre aura besoin
  d'une lecture **par dossier sur tout le parc** : c'est l'étape « vue en base » du plan.

## 6. Ce qui n'est pas mesuré

- le mode « reprendre » pour chacun des trois types ;
- la répartition (`ecrireAffaireCommission`, RPC de répartition) appelée hors de la fiche ;
- le comportement du worker sur un bien qui n'est plus dans les annonces vivantes ;
- le téléphone (`MobileLayout`, ~38786 et ~38802), qui a ses propres conditions d'affichage.

## 7. Dépendance

Le numéro de dossier (la chaîne) va changer pour une partie des dossiers : le correctif du chaînage
est confié le 30/10 à la conversation « Envoi données vers Google Sheets » (voir
`notice/ANALYSE_28_OFFRES_CHAINAGE_2026-10-30.md` § 5). Le registre doit donc s'appuyer sur la
**référence stable** du dossier, pas sur `app_chaine_id` brut.

## 8. Étape 2 — la liste « une ligne par dossier » et ses droits (31/10/2026)

**Décisions de Frédéric (31/10)** : « chacun ses dossiers : un négociateur voit les siens, un admin
voit tout » ; « il voit les dossiers où il est nommé en 1 ou 2 » ; « il faut que la répartition soit
entièrement visible même si une part n'est pas à son nom ».

**Mesuré avant d'écrire** :
- la règle existait (chantier ②, réponse B) : un négociateur voit les transactions de SES BIENS
  (`app_mes_biens_portefeuille`, vivants + archivés + vendus) ; empreinte de la règle `73d92b58` ;
- elle ratait les parts : 2026 = **17 ventes sur 282** où un négociateur nommé dans la répartition
  n'est pas le négociateur du bien (2022-2026 : 263). Ex. chaîne 1011, bien 1993 : FORLICO sur la fiche
  ET au registre des mandats (mandat du 07/09/2025), parts entrée + sortie à PEREIRA ; ⚠ rien ne montre
  que le bien ait changé de négociateur (mon « après coup » du 31/10 était sans mesure) ;
- la répartition était lisible par TOUT compte connecté (`USING true`, posée le 14/09, avant le
  chantier ② qui ne l'a pas couverte) ;
- un même e-mail porte jusqu'à 3 numéros dans l'annuaire (un par agence) ; rang 1 ou 2 seulement.

**Le patch** : `supabase/patch_registre_dossiers_droits_2026-10-31.sql` (+ `_INVERSE`, `_REPETITION`).
1. `app_mes_chaines_nommees()` : les dossiers où je suis nommé, par tous mes numéros ;
2. règle du registre : + ces dossiers (la fiche du bien 1993 montre ses transactions à PEREIRA) ;
3. règle de la répartition : visible si on voit le dossier → entière chez soi, rien ailleurs ;
4. `app_registre_dossiers(p_annee)` : la liste, filtrée par EXACTEMENT le prédicat de la règle 2.

**Éprouvé le 31/10 dans une transaction annulée** (`eprouver_registre.js`, scratchpad) : 14/14 OK.
- Témoin inverse PEREIRA : avant, 0 transaction visible sur 1011, 2 parts visibles sur 4200 (un dossier
  qui n'est pas le sien), 16 106 parts visibles en tout ; après, 3 sur 1011, 0 sur 4200, 26 en tout ;
  sa fiche passe de 21 à 23 dossiers, la liste en porte 23 dont 13 « nommé ».
- Admin : 12 165 dossiers (= chaînes vivantes du registre) · vendus 9 275 · compromis en cours 121 ·
  compromis annulés 1 372 · offres acceptées 600 · proposées 64 · refusées 733 · 2026 : 287 ventes,
  honoraires 2 173 198 € (= maquette).
- L'inverse retrouve l'empreinte exacte `73d92b58` et la répartition à `true`.
- Temps : liste complète admin 1,3 s, PEREIRA 0,8 s, admin 2026 seule 1,2 s.

**Réserves** : 171 dossiers sans ville (le bien est retrouvé, la ville est vide dans sa source) ;
1 534 sans nom d'acquéreur ; le temps de la liste (le registre des mandats et les contacts sont lus en
entier même pour un négociateur) — à revoir si l'écran le sent. ✅ **POSÉ EN PRODUCTION le 31/10 à 17:33:40
(heure de Paris), avec l'accord de Frédéric** (pooler, `poser_registre.js`) : empreinte de la règle du registre
`73d92b58` → `4cf4e342`, puis la répétition : **14/14 OK**. Retour arrière : `_INVERSE.sql` (éprouvé).

## 9. Étape 3 — l'écran liste, derrière un interrupteur (01/11/2026, ÉCRIT, NON DÉPLOYÉ)

Feu vert de Frédéric le 01/11 (« Vas y » sur « l'écran de la liste derrière un interrupteur »).

**Ce qui est écrit** (front seul, rien en base) :
- `apps/hektor-v1/src/RegistreTransactionsScreen.tsx` + `registre-transactions.css` : un écran neuf, en
  lecture seule. Période (année, de 2006 à l'année en cours, ou toutes), 4 indicateurs (honoraires actés
  entrée + sortie, ventes actées et volume, sous compromis et honoraires attendus, offres en cours), filtres
  par étape avec leur compte, recherche (ville, CP, acquéreur, n° de mandat, de dossier, d'annonce), tri,
  « Où je suis nommé » (seulement si la liste en porte), 50 dossiers par page. Tableau sur ordinateur
  (dossier et étape, bien, acquéreur, parcours offre → compromis → vente ou acte prévu, prix, honoraires,
  répartition), cartes sur téléphone (≤ 760 px). La **répartition** se lit pour la page affichée seulement
  (`loadRepartitionsDesChaines`, déjà existant). Un clic ouvre la **fiche du bien** (`openDossierDetailPage`)
  — la fiche du dossier et ses gestes sont l'étape suivante.
- `lib/api.ts` : `loadRegistreDossiers(annee)` (par paquets de 1 000 triés par n° de dossier, la fonction
  n'ayant pas d'ORDER BY ; une année = un paquet, « toutes » ≈ 13 paquets, 4 à la fois) et
  `loadAppSettingValeur(key)` (la valeur brute d'un interrupteur).
- `App.tsx` : l'écran `transactions` (adresse `?ecran=transactions`), son entrée « Transactions » dans le
  menu de gauche (sous « Mandats »), dans le tiroir et la barre du téléphone (`MobileLayout`, prop `masquer`).
  La barre des annonces (Filtres, Stats, Nouvelle annonce) n'est pas affichée sur cet écran.
- ⛔ Aucun mot « Hektor » à l'écran ; une lecture ratée dit « Les dossiers n'ont pas pu être chargés » + un
  bouton Réessayer, et le détail part en console.

**L'interrupteur** `registre_transactions_ecran` (table `app_setting`), à **trois crans** : absent ou autre
valeur = caché pour tous (état actuel : la ligne n'existe pas) ; `admin` = visible des admins seuls (pour
l'éprouver) ; `on` = visible de tous (chacun voit ses dossiers : la règle est en base, § 8). Lu une fois à la
connexion ; un accès direct par l'adresse renvoie vers Annonces si l'écran n'est pas ouvert à l'utilisateur.

**Contrôles faits** : `npm run build` vert ; mode maquette local (6 dossiers fictifs, un par étape, dans
`lib/mockData.ts`, servis seulement sans base) vu sur ordinateur (1440 px), tablette (800 px) et téléphone
(375 px) ; filtre « Vendu » → 1 ligne ; clic sur le bien → la fiche s'ouvre ; date `2026-07-09 23:00:00`
affichée 10/07/2026 (heure de Paris). La vraie app, déconnectée, affiche bien la page de connexion (pas de
page blanche). ⚠ **Non vu : l'écran sur les VRAIES données** (il faut être connecté) — à voir par Frédéric
avec le cran `admin`.

**Pour l'allumer** (après le déploiement) — une ligne à coller dans Supabase :
`insert into public.app_setting (key, value, description) values ('registre_transactions_ecran', 'admin', 'Registre des transactions 01/11/2026 : admin = ecran visible des admins seuls, on = de tous, autre = cache') on conflict (key) do update set value = excluded.value;`
Retour arrière : `update public.app_setting set value = 'off' where key = 'registre_transactions_ecran';`
(l'écran disparaît à la reconnexion suivante, rien d'autre ne bouge).

**Réserves** : « toutes les années » pour un admin = ~13 appels de ~1,3 s (4 à la fois) ; les indicateurs se
calculent sur la période choisie, comparaison avec l'année précédente non faite (c'est le pilotage, étape à
part, admins seuls) ; pas d'export ; pas de filtre agence / négociateur ; « à traiter » non fait (étape à part).


## 10. Étape 4 — la fiche du dossier : audit et plan (02/11/2026, RIEN CODÉ)

Audit limité à l'objet **transaction** (offre, compromis, vente) et à ses dépendances (répartition, conditions,
note, parties) ; les autres objets ne sont pas mesurés.

**Grille des gestes (transaction), ce qui existe aujourd'hui dans la fiche annonce :**
- **lire** : `loadAffairesForDossier` (ledger par bien), `loadAffairesConsole`, `loadAffaireChampsApp` (carnet),
  `loadRepartitionsDesChaines`, `loadAffairesConditions`, `loadAffairesNotes` — tous par id, aucun ne demande un
  `Dossier`. Regroupement par chaîne : `grouperAffairesParChaine` (App.tsx ~30310), rendu `CkAffaires` (pur).
- **créer / modifier** : la modale de statut `openStatusChangeModal(dossier: Dossier)` (App.tsx ~17763) — elle
  exige un **Dossier complet** et `isManagerOrAdmin` ; modifier = `app_modifier_affaire_optimistic` ; l'affaire
  visée se choisit par `statusChangeAffaireChoisie`. Commission, répartition, conditions et note **n'existent
  que dans cette modale** (pas de fenêtre de répartition à part) et s'écrivent après le travail.
- **refuser / accepter / annuler / supprimer** : `gesteAffaireOptimistic(app_affaire_id, geste)` — un id suffit,
  mais son seul appelant est dans la modale.
- **droits** : écran = manager ou admin pour tout geste ; les RPC de statut exigent admin (commentaire
  api.ts ~11244) ; **aucun contrôle « négociateur du bien »** dans l'écran.

**Base (02/11)** : 12 178 dossiers, au plus 4 lignes par dossier, 0 dossier à deux compromis ou deux ventes,
13 à plusieurs offres ; parties dans `app_affaire_partie` (vendeur 58 577, acquéreur 35 064, notaire vendeur
16 580, notaire acquéreur 6 785) — table **non lue par le front** ; 5 conditions et 9 notes en tout.

⚠⚠ **DÉFAUT DE L'ÉTAPE 3, lu dans le code, non vu à l'écran** : un clic dans le registre sur un dossier dont le
bien est vendu / clos (absent de `app_dossier_current` ET des listes en mémoire) appelle
`openDossierDetailPage` → `selectedDossier = null`, `loadDossierDetail` rend `null`, et comme la fiche n'est
pas « demandée par l'adresse », elle reste ouverte **vide** (App.tsx ~15501-15558). En mode maquette le bien
était en mémoire, d'où le vert. Or les ventes sont le gros du registre (287/287 ventes 2026 hors parc vivant).
Le chemin qui marche existe : `loadHistoricalAnnonceDetailCache(hektor_annonce_id)` puis la fiche légère.

⚠ **Réserve** : `app_affaire_condition` et `app_affaire_note` sont lisibles par tout compte connecté
(`qual true`), comme l'était la répartition avant le 31/10.

**Plan proposé (à valider) :**
- **4A — la fiche en lecture** (additif, dans `RegistreTransactionsScreen` : le clic ouvre la fiche du DOSSIER,
  plus la fiche du bien) : en-tête (étape, bien, mandat, agence, négociateur), 4 chiffres (prix, net vendeur,
  honoraires entrée + sortie, acte prévu ou date de vente), parcours daté, répartition, parties (table des
  parties), conditions, note, historique des lignes de la chaîne. Lu par `app_chaine_id` (la règle du ledger
  laisse voir la chaîne à qui voit le dossier). Bouton « Ouvrir la fiche du bien » qui passe par la fiche
  vivante, **sinon par le cache historique** — ce qui corrige le défaut ci-dessus. Aucune écriture.
- **4B — les gestes sur un dossier dont le bien est vivant** : les boutons de la fiche ouvrent la modale
  EXISTANTE, chargée sur le bien (`loadDossierDetail`), sur la bonne affaire et le bon onglet ; la fiche se
  relit après le geste. Retouche d'App.tsx (un rappel passé à l'écran), la modale n'est pas modifiée. Manager
  ou admin, comme aujourd'hui.
- **4C — l'option B (bien vendu hors parc)** : à part, avec les 3 défauts lus le 30/10 et un essai réel sur une
  cible choisie par Frédéric.

### 10 bis. 4A + 4B ÉCRITS (02/11/2026, « Ensemble »), NON COMMITÉS, NON DÉPLOYÉS

- `RegistreTransactionsScreen.tsx` : un clic sur une ligne ouvre la **fiche du dossier** (composant
  `FicheDossier`, même fichier) : retour au registre, en-tête (étape, « Bien vendu / clos » si le bien
  n'est plus en annonce, type · ville, mandat · agence · négociateur), 4 chiffres (prix, net vendeur,
  honoraires entrée + sortie et % du prix, acte prévu avec « dans N jours / dépassé » ou date de vente),
  parcours (une ligne par transaction de la chaîne, avec validité, fin de rétractation, acte prévu,
  séquestre, acquéreurs ; « supprimée » si elle n'existe plus), répartition avec les montants
  (pourcentage du TOTAL : 8 036 chaînes sur 8 049 somment 100), parties (vendeurs, acquéreurs, notaires,
  personnes de la transaction la plus récente, clic = fiche contact), conditions, notes. Lecture seule.
- `lib/api.ts` : `loadDossierDeLaChaine(chaineId)` (ledger par `app_chaine_id` + `app_affaire_partie` +
  noms + conditions + notes + répartition ; maquette déduite du dossier fictif) et
  `bienEstDansLesAnnonces(appDossierId)` (`app_dossier_current`).
- **4B** — `App.tsx` : `ouvrirGesteDuRegistre` charge le bien (`loadDossierDetail`), ouvre la fenêtre de
  statut EXISTANTE (`openStatusChangeModal`), pose l'onglet et la transaction choisie
  (`setStatusChangeAffaireChoisie`, comme le bouton « Choisir »). Boutons : le geste suivant de l'étape en
  tête (« Accepter ou refuser l'offre », « Passer au compromis », « Enregistrer la vente »), « Ouvrir » sur
  chaque transaction, « Modifier » sur la répartition. Proposés seulement si manager ou admin ET bien
  encore en annonce ; sinon la fiche dit « ce dossier se consulte ici ». La fenêtre n'est pas modifiée ;
  à sa fermeture, la fiche et la liste se relisent.
- **Défaut de l'étape 3 corrigé** — `ouvrirBienDuRegistre` : bien en annonce → fiche vivante ; bien
  Vendu / Clos → `openLightweightDetailImport` (détail gardé, sinon la fenêtre « Charger la fiche
  complète », la même que la liste « Étendre aux archives »). Mesure du 02/11 sur 2026 : le statut
  Vendu / Clos du registre ⇔ bien hors annonces, exactement (0 vivant sur 395, 155 vivants sur 156 pour
  les autres statuts) ; le seul cas restant (statut Actif hors annonces) reçoit un message.
- **Contrôles** : `npm run build` vert ; maquette à 1280 px (deux colonnes, pas de débordement) et
  375 px (une colonne, pas de débordement) ; « Enregistrer la vente » → fenêtre ouverte sur « Vendu » ;
  « Ouvrir » sur l'offre → onglet « Offre » ; fermer → la fiche reste ouverte ; dossier vendu → pas de
  geste + remarque ; « Ouvrir la fiche du bien » sur un vendu → fenêtre « Charger la fiche complète »
  (fermée sans rien demander). ⚠ Le choix de la transaction dans la fenêtre n'a pas pu être vu en
  maquette (la fenêtre n'y lit pas les transactions) ; **rien n'est vu sur les vraies données**.
- Piège payé : la grille de la fiche héritait à l'écran du retrait du bloc « Chargement… » (même nœud
  réutilisé par React) → une clé par état.

## 11. Étape 4C — modifier un dossier dont le bien est vendu : audit (02/11/2026, RIEN CODÉ)

Audit limité à l'objet **transaction** sur un bien **hors annonces** (vendu / clos) ; les autres objets ne
sont pas mesurés. Relu sur le code et la base du 02/11 (`notice/AUDIT_MODALE_STATUT_REGLES_2026-10-30.md`
§ 1.4, 3.6, 4, 6, 7 reste juste).

**Base (02/11)** : 287 biens ont une vente 2026 vivante ; **0** en annonce, **257** dans l'index historique,
**30** dans les archives (refus en base `annonce_archivee_lecture_seule` : ils restent en lecture). 256 des
257 historiques portent un négociateur présent dans l'annuaire. Aucune modification de vente sur un bien
historique n'a jamais été faite (0 travail).

**Les trois défauts du 30/10, toujours là :**
- **(a) base** — `app_modifier_affaire_optimistic` (empreinte `97b1b9d2`) relit `numero_dossier`,
  `titre_bien`, `negociateur_email` dans `app_dossier_current` et les **écrase dans la charge** : NULL pour un
  bien vendu. Effet : messages et notifications sans repère (worker ~20254, ~20339), et le repli du
  contexte négociateur (worker ~2550) perd son e-mail.
- **(b) worker** — la qualification des acquéreurs lit le bien dans `app_dossier_current` (~16670) →
  « qualification impossible, la transaction part quand même ». Ne mord en modification **que si les
  acquéreurs ont été retouchés** (`acquereurs_affirmes`, ~16587).
- **(c) worker** — sur une vente, la clôture locale du mandat est **rejouée à chaque modification**
  (`cloturerMandatLocalement`, ~16975) avec la date de la charge : une date de clôture posée à la main est
  réécrite, et `ecrit_par` prend l'auteur du geste.

**Et deux points de plus :**
- **(d)** SUPPRIMER la vente d'un bien vendu laisse le bien « Vendu » chez nous et chez Hektor (aucune
  redescente) — l'écran ne le dit pas.
- **(e) front** — `ouvrirGesteDuRegistre` charge le bien par `loadDossierDetail` (vivants seulement). Il faut
  un `Dossier` construit depuis l'index historique (`lightweightIndexRowToDossier`, le chemin du téléphone,
  App.tsx ~39044) complété par les numéros de transaction du registre (`hektor_affaire_id` par genre), sinon
  la fenêtre ne trouve la vente que si elle est la seule vivante.

**Non mesuré** : contexte négociateur exigé pour la vente quand le négociateur est inactif ; ce que Hektor
accepte en modification d'une vente sur un bien vendu. ➡ seul l'essai réel le dira.

### 11 bis. 4C ÉCRIT (02/11/2026, « Go », choix « A » pour la clôture), NON POSÉ, NON COMMITÉ

- **(a) base** — `supabase/patch_modifier_vente_bien_vendu_2026-11-02.sql` (+ `_INVERSE`, `_REPETITION`) :
  les trois valeurs viennent de `app_dossier_current`, sinon de l'index historique, sinon de la charge.
  Garde d'empreinte `97b1b9d2` → **`176ee0df`** après pose ; ancres sur une ligne, `chr(13)` retiré.
  **Répétition jouée (transaction annulée, droits de Frédéric)** : vente 25595 (bien historique) vide → VM66432 /
  « Ferme en pierres… » / durand@ ; compromis 30666 (bien en annonce) **identique** avant et après (témoin) ;
  retour arrière → de nouveau vide, empreinte 97b1b9d2 retrouvée. Rien de resté (vérifié).
- **(b) worker** — qualification : si le bien n'est pas dans `app_dossier_current`, l'index historique
  (`hektor_annonce_id`) ; mêmes codes `type_bien` des deux côtés (mesuré).
- **(c) worker** — choix « A » : une correction (`reprendre_transaction`) dont `champs_touches` ne contient pas
  `transaction_date` ne rejoue plus la clôture locale (journal `cloture_mandat_locale` « non rejouée »,
  `saute: true`). Sans liste (écran d'avant), comportement d'avant. `node --check` vert ; ⚠ pas d'essai hors
  ligne du handler (le worker ne se lance pas pour l'inspecter) : l'essai réel le dira.
- **(e) front** — `loadBienHistoriquePourStatut` (api.ts) ; `ouvrirGesteDuRegistre` y retombe pour l'onglet
  vente et pose le numéro exact (`vente_id`…) que le registre connaît ; la fiche propose **« Modifier la
  vente »** (tête), « Modifier » sur la seule ligne de vente et sur la répartition, quand le bien est dans
  l'historique et la vente vivante. Archivé → « se consulte, ne se modifie pas ». Pas de « Supprimer la
  vente » proposé par la fiche (d) — ⚠ mais la fenêtre, elle, l'affiche quand une vente est visée (non modifiée).
- **Contrôles** : `npm run build` vert ; maquette téléphone : fiche vendue → bouton, remarque, fenêtre ouverte
  sur « Vendu » avec le bien et le mandat, fermer → la fiche reste (le 1er essai l'a perdue : rechargement à
  chaud d'`App.tsx` par une autre session à 09:03-09:04, prouvé au journal ; 2e essai marqué : écran non recréé).
  ⚠ Non vu : la fenêtre sur les vraies transactions (« Modifier chez Hektor »), tout le réel.
- **Trouvé en passant** : `app_modifier_affaire_optimistic` ne refuse pas un bien ARCHIVÉ (la vente 48, bien 128
  archivé, a produit un travail dans l'essai annulé) ; c'est le worker (`loadDossier`) qui refuse. Le registre ne
  le propose pas.
- **À poser, avec accord** : coller le patch (puis la répétition n'est plus nécessaire, elle est jouée) ; pousser ;
  redémarrer les 4 services file vide — ⚠ le fichier du worker porte aussi le travail NON COMMITÉ de la session
  Youtrust (signature) : un redémarrage le mettrait en service ; essai réel sur une vente choisie par Frédéric.

- ✅ **(a) POSÉ le 02/11 à 09:33 (heure de Paris), par moi avec l'accord de Frédéric** (« colle-le toi-même ») :
  empreinte vérifiée 97b1b9d2 avant, **176ee0df** après ; SECURITY DEFINER, `search_path=public`, droits inchangés
  (authenticated oui, anon non). Contrôle en transaction annulée, ses droits : vente 25595 → VM66432 / titre /
  durand@ ; compromis 30666 identique. Aucun travail resté. Retour arrière : `_INVERSE.sql`.

### 11 ter. Essai réel 4C (02/11/2026, 09:43, dans le Chrome de Frédéric, avec son accord)

Cible : vente d'essai **23358**, dossier **1001393**, annonce **24113** (bien vendu, historique), 115 000 → 115 001 €.
Services du worker redémarrés à 09:42:00-02 (après le code de 08:59:22, vérifié par l'heure des processus).
- ✅ **Fiche et fenêtre en ligne** : registre 551 dossiers 2026 ; fiche complète (11 parties, 2 notaires nommés) ;
  la fenêtre vise « Vente n° 23358 — dossier n° 1001393 » ; Annuler → la fiche reste.
- ✅ **(a)** la charge du travail `c06b8660` porte VA6482, le titre, gonzalez@ (avant le patch : vides).
- ✅ **(c)** journal : « Cloture du mandat non rejouee : la correction ne touche pas la date de vente » ; la date de
  clôture du mandat 18787 reste écrite le 23/10 à 17:41:55 (témoin inchangé).
- ✅ négociateur propriétaire inactif → écriture par le contexte AGENCE (repli) : le point « non mesuré » est levé.
- ✅ **Hektor porte 115 001** ; travail `done` à 09:44:46.
- ⚠⚠ **DÉFAUT TROUVÉ (antérieur à 4C, toute correction de vente)** : pour une vente, la fenêtre préremplit
  `sale_price` avec le montant de la vente mais laisse `amount` au **prix de l'annonce** (App.tsx ~18263, branche
  `sold`) ; la base fait `montant = coalesce(amount, sale_price)` → **registre et carnet à 128 787** (prix du mandat)
  au lieu de 115 001, et la preuve du worker compare à `amount` → faux « Hektor N'A PAS PRIS » (le travail finit
  `done`). Hektor, lui, reçoit `sale_price` (worker ~14041) : il est juste. Mesure : **1 seule vente touchée, l'essai**.
  Aussi : « honorairesSortie : Hektor porte undefined » dans la même preuve (Hektor ne relit pas ce champ sur une vente).
- ⏳ **Retour à 115 000 non fait** : avec le défaut, il réécrirait 128 787 au registre. Remède proposé : préremplir
  aussi `amount` avec le montant de la vente (une ligne) ; le retour par l'écran remettra alors registre et carnet à
  115 000 d'eux-mêmes.

### 11 quater. Audit : modifier le PRIX d'une vente (02/11/2026, demandé par Frédéric)

Audit limité à la correction du prix d'une VENTE (créer : seulement la base, mesurée ; autres objets non mesurés).
- **Le worker le permet, et depuis le 08/09** (`console_job_worker.js` ~14020, branche `sold && enReprise`) :
  `prixDeVente` = `sale_price`, sinon `amount` ; aussi la date et les honoraires, seulement ce que la charge porte.
  Prouvé chez Hektor : 08/09 sur 24933 (176 500, relu), 18/09 (180 000, relu), 02/11 sur 24113 (115 001, relu).
- **La fenêtre** : pour une vente, la case « Montant / prix public » est CACHÉE exprès (14/09 : « deux cases pour
  une seule valeur ») ; seule « Prix de vente » se voit. Mais `amount` part QUAND MÊME dans la charge
  (App.tsx ~19070), avec le prix de l'ANNONCE posé à l'ouverture (~17904) ; le préremplissage par la vente ne
  remplit que `sale_price` (~18263).
- **La base** (création ET modification) : `montant = coalesce(amount, sale_price)` → c'est le prix de l'annonce qui
  entre au registre et au carnet dès que les deux diffèrent.
- **La preuve du worker** (`CHAMPS_PROUVABLES.vente`, ~15624) garde `amount` avant `sale_price` (ordre de la table),
  alors que l'envoi prend `sale_price` d'abord → faux « Hektor N'A PAS PRIS », et la saisie RESTE au carnet.
- **Pourquoi personne ne l'a vu** : 3 modifications de vente avant aujourd'hui, toutes sur le bac à sable 24933, où
  `amount` était absent (08/09) ou ÉGAL au prix de vente (18/09 : 180 000 = 180 000). Créations : 22 ventes depuis
  l'app, 3 avec `amount` ≠ prix de vente, toutes sur 24933 et supprimées depuis ; la création de vente depuis un
  compromis préremplit les deux cases à l'identique (~18815). Carnet : seule la vente d'essai 1001395 porte un
  montant faux (128 787).
- **Remède proposé (une ligne, front)** : pour une vente, envoyer `amount` = le prix de vente (~19070). La base, la
  preuve et le carnet deviennent justes sans les toucher ; Hektor ne change pas (il reçoit déjà `sale_price`).
  En option : la base préfère `sale_price` pour une vente (protège un écran resté en cache), et la preuve aussi.
- **Non mesuré** : « honorairesSortie : Hektor porte undefined » sur 23358 (relu 1 500 le 18/09 sur 24933).

### 11 quinquies. 4C-prix ÉCRIT (02/11/2026, « Go, ligne + base »), NON POSÉ, NON COMMITÉ

- **Écran** (App.tsx, envoi de la fenêtre) : pour une vente, `amount` = le prix de vente (repli : l'ancien montant).
- **Base** — `supabase/patch_vente_prix_de_vente_dabord_2026-11-02.sql` (+ `_INVERSE`, `_REPETITION`) : dans
  `app_change_annonce_status_optimistic` (création) et `app_modifier_affaire_optimistic` (correction), pour une VENTE
  le montant = `sale_price` d'abord, `amount` en repli ; offre et compromis inchangés (le `case` vaut NULL).
  Empreintes 446df246 / 176ee0df → **11616ec6 / a52966fa**. **Répétition jouée** (transaction annulée, droits de
  Frédéric, chaque appel dans une sous-transaction annulée) : création de vente 128 000 → 101 000 → retour 128 000 ;
  correction 1001395 128 787 → 115 000 → 128 787 ; compromis 30666 témoin 104 000 partout. Rien de resté.
- **Worker** (`CHAMPS_PROUVABLES.vente`) : `sale_price` jugé avant `amount`, comme l'envoi. `node --check` vert.
- `npm run build` vert.
- **À poser, avec accord** : coller le patch ; pousser ; redémarrer les 4 services (pour la preuve) ; puis remettre la
  vente d'essai 23358 à 115 000 par l'écran → registre et carnet doivent revenir à 115 000 et la preuve être conforme.
- ✅ **Base 4C-prix POSÉE le 02/11 vers 10:25 (heure de Paris), par moi avec l'accord de Frédéric** (« Oui, les deux ») :
  empreintes 446df246 / 176ee0df vérifiées avant, **11616ec6 / a52966fa** après ; SECURITY DEFINER et droits
  inchangés. Contrôle annulé, ses droits : correction 1001395 → 115 000 ; compromis 30666 → 104 000 (inchangé).
  Commits : `d786df7` (écran, base, worker), `a8c645f` (note). Reste : pousser, redémarrer les 4 services FILE VIDE,
  remettre 23358 à 115 000 par l'écran.

### 11 sexies. Retour de la vente d'essai à 115 000 — 4C-prix éprouvé en réel (02/11/2026, 10:29)

Poussé (`a8c645f` en ligne, Vercel READY), workers relancés à 10:27:06-08 (code du worker de 10:01:38), file vide.
Par l'écran, dans le Chrome de Frédéric : dossier 1001393 → « Modifier la vente » → 115 000 → « Modifier la transaction ».
- ✅ **Écran** : la charge du travail `a7580263` porte `amount` = `sale_price` = 115000 (avant : 128787 / 115001).
- ✅ **Base** : registre 128 787 → **115 000** ; carnet `montant` 128 787 → **115 000**, `prix_publique` 115 000,
  `prix_net_vendeur` 110 000 — sans écriture à la main.
- ✅ **Preuve** : le prix n'est plus en écart (Hektor 115 000.00). Clôture du mandat **non rejouée** (2e fois).
- ✅ Travail `done`. La vente d'essai est revenue à son état de départ chez Hektor et chez nous (115 000).
- ⚠ **Reste un faux écart, non corrigé** : « honorairesSortie : envoyé 5000.00, Hektor porte undefined ». Hektor PORTE
  bien 5 000 (`honorairesSortie` = 5000.00 dans la fiche lue par le run) : c'est la relecture de la preuve qui ne rend
  pas ce champ pour cette vente (elle l'avait rendu le 18/09 sur 24933 : 1 500). Effet : la preuve finit « error »
  (le travail reste `done`) et la saisie ne quitte pas le carnet — le carnet porte des valeurs ÉGALES à Hektor, donc
  sans dommage. Cause non cherchée : à traiter à part.

### 11 septies. Le faux écart « honorairesSortie : Hektor porte undefined » — cause (02/11/2026, audit, RIEN CODÉ)

Audit limité à la RELECTURE qui sert de preuve après une correction de transaction (offre, compromis, vente).
Lectures faites à Hektor : 7 requêtes GET, aucune écriture.
- La preuve relit par deux scripts Python appelés par le worker : `phase2/sync/transactions_annonce_from_api.py`
  (listes ListOffres / ListCompromis / ListVentes) et `phase2/sync/transaction_etat_from_api.py` (OffreById /
  CompromisById / VenteById). **Seul ListOffres passe `version`** ; les autres appels n'en passent pas.
  Le run de nuit (`sync_raw.py:973`) passe `version` = `v2` partout.
- **Mesure du 02/11, même transaction, avec et sans `version`** :
  - vente 23358 (ListVentes) — sans : clé `sales`, `hono_sortie`, `hono_entree`, `hono_hors_taxe`,
    `commission_agence`, `part_admin` ; avec v2 : clé `data`, `honorairesSortie`, `honorairesEntree`, `honorairesHT`,
    `commissionAgence`, `partAdmin`. Le reste (id, date, prix, acquéreurs, mandants) est identique.
  - compromis 50094 (CompromisById) — sans : `res`, `prix_publique`, `prix_net`, `honoraires_sortie`,
    `honoraires_entree`, `part_admin` ; avec v2 : `data`, `prixPublique`, `prixNetVendeur`, `honorairesSortie`,
    `honorairesEntree`, `dateStart`, `dateSignatureActe`… — les noms qu'attend la preuve (`CHAMPS_PROUVABLES`).
  - offre 33114 (OffreById) — mêmes propositions avec ou sans : **non touchée**.
- **Hektor a changé sa réponse par défaut entre le 23/10 et le 02/11** : le 23/10, sans version, la preuve relisait
  encore `prixPublique` / `honorairesSortie` sur les compromis 50132 et 50136 (« MODIFIE et RELU »). Aucune correction
  de compromis ni de vente n'a été faite entre-temps, d'où le silence.
- **Conséquence aujourd'hui** : toute correction de COMPROMIS finirait en faux « N'A PAS PRIS » (prix public, net,
  honoraires, séquestre non relus) et de VENTE sur les honoraires ; la saisie resterait au carnet, le registre ne
  serait pas reporté par la preuve (le run de nuit, lui, relit bien en v2). Les données chez Hektor ne sont pas en cause.
- **Remède proposé** : passer `version` = `v2` dans les appels ListCompromis, ListVentes, CompromisById (et VenteById par
  cohérence) et lire la clé `data` (repli sur l'ancienne clé). Le geste lirait alors la MÊME forme que le run.
  Ces scripts sont relancés à chaque travail : **pas de redémarrage**, effet immédiat. Essai hors ligne possible en
  lecture (24113 / 23358, 1953 / 50094). Non mesuré : les autres lectures du projet sans `version`.

### 11 octies. Relecture avec `version` : CORRIGÉE ET EN SERVICE (02/11/2026, « go corrige et vérifie ailleurs »)

- **Corrigé** : `transactions_annonce_from_api.py` (ListCompromis, ListVentes) et `transaction_etat_from_api.py`
  (CompromisById, VenteById) passent `version` = `v2` et lisent `data`, l'ancienne clé en repli. L'offre n'est pas
  touchée. ⚠ Ces scripts sont lancés à chaque travail par le worker : **en service dès l'enregistrement**, sans redémarrage.
- **Éprouvé en lecture** : liste des ventes 24113 → `honorairesSortie` 5000.00, `honorairesEntree` 0.00, même prix, date,
  1 acquéreur, 10 mandants ; compromis 50094 par numéro → `prixNetVendeur`, `dateStart`, `dateSignatureActe` ; vente
  23358 → trouvée, 9999999 → non trouvée (vérification des suppressions intacte) ; offre 33114 inchangée. La liste
  ListCompromis v2 rend les mêmes numéros, dans le même ordre, avec les mêmes annonces et `status` que l'ancienne.
- **Ailleurs, recensé (23 fichiers Python qui appellent l'API, + le worker JS)** : tous passent `version` SAUF
  `annonce_datemaj_from_api.py`, `annonce_etat_from_api.py`, `annonce_proprietaires_from_api.py` (AnnonceById) et
  l'annuaire `listNegos` (`push_hektor_directory_to_supabase.py:158`). **Éprouvés le 02/11 sans version : ils rendent
  toujours les champs qu'ils lisent** (keyData.id / datemaj / archive / NEGOCIATEUR / agence, statut id + nom,
  proprietaires ; res[].idUser / prenom / nom / email / telephone / portable). Non touchés. Le worker JS
  (AnnonceById, ~3545) passe déjà la version. Les scripts de `.tmp/`, sondes et copies de travail ne sont pas comptés.
- **Non éprouvé** : une vraie correction de compromis par l'écran avec la nouvelle relecture (aucune depuis le 23/10).

## 12. Registre : audit graphique de l'écran EN LIGNE contre la maquette (02/11/2026, RIEN CODÉ)

Vu dans le Chrome de Frédéric, 1 280 px, vraies données 2026 ; maquette https://claude.ai/artifact/3FA3yDqWuDWuqLdZAkvS8x.
- **Liste** : le tableau (1 113 px) dépasse sa boîte (1 083 px) → la colonne Répartition est COUPÉE. Lignes hautes
  (acquéreur sur 3-4 lignes), parcours en petits points peu lisibles. Civilité brute « M_Mme » (chantier couples).
- **Fiche** : écarts avec la maquette — parcours vertical sans les étapes À VENIR (maquette : frise horizontale offre →
  compromis → fin de rétractation → acte, l'étape du jour en magenta, l'à-venir en pointillé) ; pas d'alerte en tête
  (« Rétractation : dernier jour », acte dépassé) ; « suivi par » donne l'e-mail, pas le nom ; répartition sans barre
  ni avatars ; pas de bloc « Actions du dossier » (gestes épars : boutons « Ouvrir ») ; notes en lecture seule ; pas
  de liste latérale des dossiers ; photo absente → carré gris ; nom de notaire avec virgule finale (« KINTZIG, »).
- **Données (à part)** : 54 offres sans montant ni état, vues depuis le 31/07, portent la DATE DU RUN (29/10 le 29/10,
  02/11 aujourd'hui) → elles remontent en tête du registre (« Offre proposée », prix « — »). Non creusé.

## 13. Maquette graphique v3 et ajouts retenus (02/11/2026) — mesures des données, RIEN CODÉ

Maquette v2 (restructuration) REFUSÉE par Frédéric ; v3 = ses écrans, même structure, habillage seul, Avant/Après :
https://claude.ai/artifact/PSv5yJ3KkyioGLFDKWYv7h. Ajouts retenus : indicateurs cliquables, tri par en-tête, filtre
agence/négociateur (admin), mémoire des filtres, nom du négociateur, délai entre étapes, documents du dossier,
historique des changements, dossier précédent/suivant, période MENSUELLE (en plus de l'année). Maquette v3.1 en cours.

Mesures (02/11, droits de Frédéric) :
- **Nom du négociateur** : quand le registre porte un e-mail, l'annuaire donne le nom dans 100 % des cas
  (6 332/6 332) ; 2026 : 499/502 (3 sans e-mail). Dossiers anciens : 6 332 e-mails sur 12 117.
- **Documents** : tous typés « document » ; famille reconnue par le NOM (libre) sur les biens des transactions 2026 :
  offre 870, compromis/promesse 425, acte 147, mandat 836, diagnostics 569, visite 542, identité 1 109, autres 4 653.
  Rattachés au BIEN, pas à la transaction. **Stockage (mesuré par `storage_status`, re-vérifié le 02/11 à la
  demande de Frédéric)** : biens vivants 3 245/3 246 `cloud_available` ; biens VENDUS 1 046 `cloud_available` et
  6 304 `local_only` (86 %) — TOUS ont leur copie sur le serveur (`local_archive_path`). C'est la RÈGLE (le serveur
  porte tout, le coffre ne copie que les biens vivants, `shouldKeepCloud`). ⛔ **CORRECTION** : j'avais écrit qu'ouvrir
  ces documents demandait un « chantier à part » — FAUX. Le geste existe : un document `local_only` s'affiche
  « À préparer », et `createPrepareConsoleDocumentJob` (api.ts ~8615) pose `prepare_document_cloud`, qui le remonte
  au coffre (6 travaux, tous `done`, médiane 4 s). Le bloc Documents du registre n'a qu'à le réutiliser.
- **Historique** : gestes de l'app sur les biens des dossiers 2026 = 5 biens seulement (essais surtout) ; les
  transactions vivent encore chez Hektor, qui ne livre que l'ÉTAT, sans auteur ni date de modification. Sources
  datées et signées : app_console_job (requested_by), app_affaire_champ_app (ecrit_par/ecrit_le, valeur avant/après),
  app_affaire_repartition (ecrit_par/ecrit_le), ledger (dates des étapes, first_seen_at). → un historique honnête =
  les étapes datées + les corrections faites dans l'app, avec leur auteur.

## 14. Maquette v3.1 CODÉE (02/11/2026, « Oui, code-la »), NON COMMITÉE

Écrit par un agent développeur sur mon cahier des charges, relu par moi : `RegistreTransactionsScreen.tsx`,
`registre-transactions.css` (ajouts en fin de fichier), `lib/api.ts` (ajouts : `loadNomsNegociateurs`,
`HistoriqueDossierLigne`, `loadHistoriqueDuDossier` + aides internes ; mode maquette de `loadConsoleDocuments`).
App.tsx non touché. Lectures seules (annuaire 219 lignes, carnet, répartition, travaux, profils), aucune écriture.
- **A habillage** (maquette « Après ») + **défaut corrigé** : parcours trié par jour (Paris), puis offre < compromis <
  vente, puis n° de transaction.
- **B liste** : indicateurs = filtres (nouveau filtre « Offres en cours »), tri par en-tête (sens), mois (caractères
  6-7 de `date_dernier_evenement`, même règle que l'année en base), agence et négociateur (admin ; filtrent aussi
  indicateurs et compteurs), mémoire `localStorage` « bienvu-registre-transactions » + « Filtres gardés · Réinitialiser ».
- **C fiche** : nom du négociateur (annuaire, repli e-mail), délais entre étapes, précédent/suivant, Documents (de
  transaction d'abord, 8 + « Voir tout » ; `local_only` → `prepare_document_cloud` puis relecture 2 s × 40 s),
  Historique (étapes du registre sans auteur + corrections du carnet + répartition hors « conversion » + gestes
  envoyés ; auteur = profil si lisible — admin seulement —, sinon « un utilisateur »).
- **Contrôles** : `npm run build` vert ; maquette 1 280 px et téléphone par l'agent puis moi (en maquette locale la
  zone fait 891 px à cause du grand menu : colonnes Bien/Acquéreur serrées ; en production, menu en icônes, zone
  ~1 083 px). ⚠ Non vu sur les vraies données : noms, documents réels (dont la préparation), historique réel.

## 15. v3.1 vue EN LIGNE, puis liste retouchée, filtre agence corrigé, fiche v4 (02/11/2026)

**Vérifié en ligne (56d00bc, Chrome de Frédéric, 1 280 px)** : 502 dossiers 2026 ; mois Octobre = 96 ; tri Prix
dans les deux sens ; clic « Ventes actées » = les ventes seules ; filtre négociateur (Alice RONDEAU = 11 dossiers,
indicateurs suivis) ; mémoire rendue au rechargement (puis remise par défaut) ; fiche 28865 : nom du négociateur,
délais, 21 documents, historique ; un document du coffre s'ouvre (lien signé). ⚠ Non essayé : un document
`local_only` (« Préparation… »). À 1 280 px le filtre « Tous les négociateurs » passe sur une 2e ligne (noté).

**Retour de Frédéric** : « la colonne Parcours est trop tassée, le nom des négociateurs pas lisible dans la colonne
Répartition » ; fiche « manque de design, pas très graphique, hausse le niveau ».
- **Liste** : largeurs 140 / Bien (reste) / 9 % / 230 / 86 / 94 / 212 (table mesurée 1 083 px). Nom court dans
  Répartition (`nomCourt` : sans civilité, initiale du prénom, « S. DELAVAUD » ; complet au survol). Mesuré sur la
  page en ligne en injectant les largeurs : 53/53 noms coupés avant, 0 après ; seules 2 villes longues en « … ».
- **Filtre agence vide pour Ambert** (signalé par Frédéric) : les 34 dossiers d'Ambert arrivent en
  « Groupe GTI Ambert␣␣␣ » (3 espaces : `app_dossier_current` 719 biens, index historique 609, archives 1 730 ; le
  registre des mandats les a retirés, d'où le choix sans espaces). La liste des choix retirait les espaces, la
  comparaison non → 0. Corrigé : comparaison `.trim()` des deux côtés. Aucune autre agence n'a d'espaces. ⭐ Famille
  balayée : l'écran Annonces filtre Ambert correctement (Actifs 41 via le registre, Archives 1 293), les autres
  `.eq('agence_nom')` de `api.ts` ne servent que des écrans qui marchent ou les données de maquette.
- **Fiche v4** (maquette https://claude.ai/artifact/TmuBn3hQNKpTvT13XLKNr7, validée « oui code la ») : en-tête
  teinté par l'étape + **frise** (3 jalons, durée entre eux, « de l'offre à l'acte : N jours », acte signé N jours
  après/avant la date prévue au compromis) ; chiffres à **tuiles d'icône**, écart prix de vente / offre, **anneau**
  des honoraires (entrée/sortie, taux au centre) ; parcours en cartes avec étiquettes ; **colonnes rééquilibrées**
  (gauche : parcours + documents ; droite : parties, répartition, conditions/notes, historique) ; parties colorées
  par rôle ; répartition en anneau + jauges + « N % ne sont attribués à personne » quand la somme < 100 ;
  conditions et notes vides = une seule petite carte ; documents en **vignettes** cliquables (même geste qu'avant) ;
  historique à points colorés. Aucune nouvelle lecture, aucune écriture : présentation seule.
- **Contrôles** : `npm run build` vert ; maquette locale 1 280 px (menu replié) et téléphone 375 px (titre caché par
  la photo et montants débordants trouvés puis corrigés ; 0 débordement mesuré) ; frise relue sur les 6 dossiers
  d'essai, une par étape (libellés « Compromis » / « Vente » tant que l'étape n'est pas atteinte).
  ⚠ Non vu sur les vraies données.

**Vu EN LIGNE après le push (dec5821, bundle `index-CAjgNaCB.js`, Chrome de Frédéric, 1 280 px)** :
- liste : colonnes 140 / 224 / 97 / 230 / 86 / 94 / 212, **0 nom coupé sur 53** ; filtre « Groupe GTI Ambert » =
  **34 dossiers** (0 avant) ;
- fiche 28865 : frise « 64 j / 157 j », « de l'offre à l'acte : 221 jours », « acte prévu le 23/08/2026, signé
  65 jours plus tard », écart −30 000 € par rapport à l'offre, anneau 8,6 %, « 50 % des honoraires ne sont
  attribués à personne », historique coloré, colonnes 880 / 939 px ;
- ⭐ **document `local_only` éprouvé** : bien 61476 (68 documents, tous sur le serveur seulement),
  « planCadastralNormalise Parcelle ZK 41.pdf » → « Préparation… » puis lien signé ouvert en **7 s** ; travail
  `prepare_document_cloud` `done` 13:16:56 → 13:17:02, document passé `cloud_available`. Aucune écriture chez Hektor.

## 16. Pilotage (administrateurs) : audit (02/11/2026, RIEN CODÉ)

**Audit limité à l'objet transaction, en LECTURE seule** (vente, compromis, répartition). Le pilotage ne crée,
ne modifie et ne supprime rien : grille des gestes = « lire » seulement ; les autres objets ne sont pas mesurés.

**Ce qui existe** : la maquette du 29/10 (https://claude.ai/artifact/3FA3yDqWuDWuqLdZAkvS8x, écran « Pilotage ») ;
décision du 30/10 : administrateurs seuls, années antérieures, comparaison à l'année précédente. Dans l'app, l'accueil
admin porte une case vide « Reporting agence… quand le module reporting sera disponible » (App.tsx ~26188) ; aucune
fonction de base ne calcule de chiffres par an, par mois, par agence ou par négociateur.

**Sources, mesurées avec les droits de Frédéric (02/11)** :
- `app_registre_dossiers(p_annee)` : l'année est celle du **dernier événement** ; pour une vente, c'est **toujours**
  l'année de l'acte (0 écart sur 12 110 dossiers). Une année = 1 appel de ~1,1 s (2026 : 502 lignes ; 2025 : 403).
  ⚠ Chaque paquet de 1 000 lignes recalcule toute la fonction (~1,2 s) : « tout » = 13 paquets.
- Ventes et honoraires TTC (entrée + sortie) : 2026 = **287 / 2 173 198 €** (36,6 M€ de volume) ; 2025 = 353 /
  2 632 910 € ; à la même date (≤ 02/11) 2025 = **293 / 2 175 330 €** → −2,0 % de ventes, −0,1 % d'honoraires.
  Historique continu depuis **2006** (85 ventes en 2006, puis 400 à 570 par an).
- Mois 2026 : janv. 26 / 180 000 · févr. 28 / 189 000 · mars 44 / 302 950 · avr. 21 / 164 400 · mai 26 / 189 040 ·
  juin 39 / 324 500 · juil. 34 / 265 140 · août 10 / 55 400 · sept. 32 / 272 550 · oct. 27 / 230 218.
- **Actes déjà datés à venir** : 73 compromis en cours, acte prévu ≥ 02/11, **808 003 €** — 72 dans la liste 2026,
  **1 dans la liste 2025** (il faut donc lire N et N-1). 36 compromis ont une date d'acte dépassée sans vente.
- Délais médians 2026 (ventes) : offre → compromis **30 j**, compromis → acte **90 j**.
- Agences 2026 (champ `agence_nom` de la liste, espaces retirés) : 17 agences ; 1re COURPIÈRE 28 / 236 400 €, puis
  Craponne 32 / 232 140 €. ⚠ La maquette du 29/10 lisait le registre des mandats (Courpière 24 / 203 900) : le
  pilotage doit prendre la MÊME agence que la liste, sinon un filtre et un total se contrediraient.
- **Répartition** : la part d'une personne = **honoraires totaux × pourcentage / 100**, entrée et sortie confondues
  (230 ventes 2026 en 50/50 ; c'est la règle de la fiche v4, qui additionne toutes les parts). ⚠ Ma 1re requête
  appliquait le pourcentage à l'entrée OU à la sortie seule et donnait 48 % de répartis : FAUX, corrigé.
  Couverture (somme des parts / honoraires) : 2022 98,7 % · 2023 98,9 % · 2024 98,8 % · **2025 84,7 %** ·
  2026 96,5 %. **Ventes sans aucune répartition** : 2022 12 · 2023 10 · 2024 6 · **2025 55** · 2026 5.
  1er négociateur 2026 : M. BILLIG DURAND 31 dossiers / 221 640 € (= maquette). 33 personnes en 2026.
- ⚠ « Cet utilisateur a été supprimé » porte l'identifiant **0** pour TOUS les supprimés : on ne peut pas les
  séparer (2023 : 16 dossiers / 161 144 €, 4e de l'année). Parts concernées : 2022 52 · 2023 62 · 2024 38 · 2025 24
  · 2026 4.

**Ce que ça pourrait casser ailleurs** : rien si le pilotage reste une VUE de l'écran Registre, en lecture, derrière
le rôle admin : aucune écriture, aucune fonction de base modifiée, la liste et la fiche ne changent pas. Retour
arrière = retirer le commit. ⚠ Charge : 2 appels de ~1,1 s (N et N-1) + 1 lecture de répartition (< 1 000 lignes
par an) ; une vue « 5 ans » coûterait 5 appels.

**Choix à faire par Frédéric** (rien n'est décidé) : l'endroit (bascule « Liste / Pilotage » dans l'écran Registre,
admin seulement — recommandé), le contenu de la 1re version (la maquette du 29/10 : 4 chiffres, honoraires par mois
avec comparaison et actes datés hachurés, négociateurs, agences), et le bloc « Qualité du registre » (le laisser à
l'étape « à traiter », qui vient juste après — recommandé). Méthode : maquette sur les vraies données, au look de la
fiche v4, puis code.
