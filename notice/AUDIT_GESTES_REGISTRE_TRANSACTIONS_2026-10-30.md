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

