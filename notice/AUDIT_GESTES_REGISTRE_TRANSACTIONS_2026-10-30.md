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
