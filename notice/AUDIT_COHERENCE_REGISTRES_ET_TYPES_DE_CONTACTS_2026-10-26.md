# LA COHÉRENCE DES REGISTRES ET LES 4 TYPES DE CONTACTS — audit complet du 26/10/2026

*(Frédéric, 26/10 : « cette pièce 5 est bien plus compliquée que j'avais prévu ; refais un audit complet de mon projet […] il y a 4 types
dans mon projet : acquéreur, acheteur, propriétaire et mandant ; comprends parfaitement le sujet — notes, code actuel et historique —
puis redonne-moi ton audit avec explication et proposition sur la cohérence entre mes registres contact, mandat, annonce, transaction et
relations ; elles sont toutes liées ; il faut un mécanisme logique et correspondant à ce qui se fait habituellement dans ce type de
logiciel ; sois le plus complet possible, mais ne code rien » — et : « il y a aussi le registre des recherches »)*

**Lecture seule. Rien n'est codé, rien n'est écrit en base.** Sources : le code actuel (`App.tsx`, `lib/api.ts`,
`phase2/contacts/build_contacts_layer.py`, `phase2/sync/relation_ledger.py`, `affaire_ledger.py`, `export_app_payload.py`,
`mandat_ledger.py`), la base Supabase (mesures du 26/10), les notes (`ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md` §31-39 et
§58, `AUDIT_REGISTRE_RELATIONS_AUTONOME_2026-09-30.md`, `AUDIT_5_QUESTIONS_REGISTRE_RELATIONS_2026-10-10.md`, `PLAN_DEV_CONTACT_V2.md`,
`JOURNAL_DE_BORD.md`), la mémoire, l'historique git (commits `7d45209` 29/06, `c42f9b8` 24/07, `5dc5354` 23/10…).

---

## 1. Les six registres, tels qu'ils sont aujourd'hui

| registre | table(s) | ce qu'il porte | qui l'écrit | ses numéros |
|---|---|---|---|---|
| **contacts** | `app_contact` (serveur, 356 649) → `app_contact_current` (cloud, ~62 000 éligibles) | la personne ; `typologies_json` (Hektor) ; `relation_roles_json`, `active_search_count` (calculés **la nuit**) | la création / modification dans l'app (au clic, 8a) ; la nuit (Hektor) | les deux (le nôtre ≥ 10 M, celui de Hektor) |
| **annonces** | `app_dossier` → `app_dossier_current` (parc vivant), index historique / archives | le bien, son statut, son n° de mandat **courant**, `proprietaires_json` (détail Hektor) | l'app (au clic, 8a) ; la nuit | les deux |
| **mandats** | `app_mandat` (26 929) → `app_mandat_register_current` | le mandat (n°, dates, type, clôture) ; les mandants : **`mandants_texte` = un TEXTE de Hektor** (nom + adresse, aucun numéro) ; `mandants_json` du registre **recalculé à chaque envoi depuis le registre des relations** | la nuit (Hektor) ; la clôture dans l'app ; ⛔ la création reste chez Hektor (étape 3) | `app_mandat_id`, n° Hektor |
| **relations** | `app_relation` (132 841) | **personne ↔ bien**, un seul fait : « propriétaire du bien » ; mandant / propriétaire est un **libellé dérivé** | la nuit (propriétaires de l'annonce chez Hektor) ; au clic : lier, créer, retirer un mandant | les quatre |
| **transactions** | `app_affaire_ledger` (31 103) + carnet | **personne ↔ affaire** : l'acquéreur principal, la liste des acquéreurs, la liste des **mandants de la transaction** (`mandants_json`, relue chez Hektor), les notaires | la création / modification au clic (R1) ; la nuit (Hektor) ; R2-R4 | nos numéros pour les acquéreurs et notaires ; ⚠ **pas pour les mandants** |
| **recherches** | `app_contact_search_current` (11 525), registre des recherches | le **projet d'achat** d'un contact (critères, actif / archivé) ; rapprochements (`app_rapprochement`), statut acquéreur ↔ bien (`app_bien_acquereur_statut`) | la création dans l'app passe par Hektor (mémoire « créer une recherche passe par Hektor ») ; la nuit | clé `contact_search_key`, `app_search_id` |

**Une table de nuit à part** : `app_contact_relation_current` (refaite chaque nuit depuis six fenêtres de Hektor) — elle fournit encore les
**acquéreurs** à la fiche contact (branche 2 de la vue `app_contact_relations_current`) et **les rôles de tous les contacts**
(`relation_roles_json`, donc les 4 types).

---

## 2. Les 4 types : la définition en vigueur, et son histoire

**En vigueur depuis le 24/07/2026** (commit `c42f9b8`, `App.tsx` `contactDirectoryCategories` l. 37491) — non exclusifs, priorité du type
dominant **Mandant > Acheteur > Propriétaire > Acquéreur** :
| type | règle du code | source réelle |
|---|---|---|
| **Mandant** | le contact a un lien `mandant` | lien « propriétaire du bien » **et le bien a AUJOURD'HUI un n° de mandat** (`build_contacts_layer.py` l. 1393-1397 : le rôle est réécrit d'après `numero_mandat` du dossier) |
| **Propriétaire** | lien `proprietaire` | lien « propriétaire du bien » **et le bien n'a PAS de n° de mandat** (estimations…) |
| **Acheteur** | un rôle `acquereur_offre` / `_compromis` / `_vente` | les listes d'offres / compromis / ventes **de Hektor** (table de nuit) |
| **Acquéreur** | `active_search_count > 0` | une recherche active |
**Version d'avant** (29/06, `7d45209`) : `proprietaire` s'affichait « **Vendeur** » (« lié à une transaction ») — **remplacée le 24/07**, mais un
**résidu** subsiste : la liste **mobile** utilise encore `contactToneFromRoles` (« Vendeur » pour un propriétaire, « Acquereur » pour un
acheteur, « Multi-role » au-delà d'un type), et le cockpit écrit « Vendeur · mandant » (`App.tsx` l. 31391, 31439). ⇒ **le même contact a deux
types selon l'écran.**
**La règle de Frédéric (23/10)** : « **l'acquéreur reste acquéreur pour toujours, jamais propriétaire ; le propriétaire reste le mandant** ».

---

## 3. Ce que l'audit a trouvé — les défauts de cohérence, mesurés le 26/10

| | le défaut | mesure | effet |
|---|---|---|---|
| **C1** | **« Mandant » ne veut pas dire « a signé un mandat »** : c'est « propriétaire d'un bien qui porte AUJOURD'HUI un n° de mandat » | règle du code ; 2 339 biens « mandant » ne sont pas au registre des mandats (mémoire, 08/10) | le type change quand le bien change de mandat ; un ancien mandant devient « propriétaire » si le n° disparaît |
| **C2** | ⛔ **les mandants d'un MANDAT ne sont gardés nulle part sous forme de personnes** : Hektor ne les donne qu'en texte ; le registre des mandats les **recalcule à chaque envoi depuis les propriétaires ACTUELS** du bien | `mandants_texte` texte sur 26 793 / 26 929 ; `app_mandat.app_contact_id` renseigné sur **40** seulement | ⚠⚠ **sur 76 des 84 biens vendus depuis le 17/07 présents au registre des mandats, l'ACHETEUR figure parmi les mandants du mandat** — un mandat signé par le vendeur montre l'acheteur comme mandant |
| **C3** | **l'acheteur rangé « Mandant » du bien qu'il a acheté** : depuis le 17/07, Hektor met l'acheteur dans les propriétaires ; la nuit le recopie au registre des relations, puis le rebaptise « mandant » | **151 liens, 127 actifs** (115 le 23/10 ; il en arrive à chaque vente) | type dominant faux (« Mandant » au lieu d'« Acheteur ») ; registre des mandats (C2) ; activité du contact (les biens achetés y entrent) ; rubrique Contact du bien |
| **C4** | **les mandants d'une TRANSACTION sans notre numéro** | **58 550 personnes** dans `mandants_json` (compromis 31 307, ventes 27 243) | à la coupure, les vendeurs d'une affaire ne sont plus reliés à leur fiche ; aucun lien fiable avec le registre des relations (seulement par le n° de Hektor : 731/735 ventes, 593/606 compromis 2026) |
| **C5** | **les acheteurs lus dans une table de nuit** (pas dans notre registre des transactions) | 35 005 liens ; la projection les retrouve tous (§58) | un acheteur saisi dans l'app n'apparaît qu'après la nuit ; perdu à la coupure (c'était la pièce 5) |
| **C6** | **les types sont calculés LA NUIT** (`relation_roles_json`) | — | un mandant lié ou une offre créée dans l'app ne change le type du contact que le lendemain |
| **C7** | **la recherche de l'acheteur reste active après l'achat** | **48 des 278 acheteurs de 2026** ont encore une recherche active | il reste « Acquéreur », reçoit des rapprochements et des relances pour un projet réalisé |
| **C8** | **deux logiques de type dans l'écran** (desktop `contactDirectoryCategories`, mobile `contactToneFromRoles`) | code | « Vendeur » / « Acquereur » / « Multi-role » sur mobile, « Propriétaire » / « Acheteur » sur desktop |
| **C9** | **les propriétaires d'un bien ont deux sources à l'écran** : la rubrique Contact prend `proprietaires_json` de Hektor « s'il a fourni le blob riche », sinon notre registre des relations (`App.tsx` l. ~25319) | code | deux vérités possibles sur la même fiche |
| **C10** | **les gestes ne se répondent pas** : « Supprimer la vente » ne retire pas l'acheteur-propriétaire ; « Retirer un mandant » ne touche ni le mandat ni les transactions | §35-36 | une vente annulée laisse l'acheteur « mandant » |
| **C11** | **un lien de propriété n'a pas de durée** : pas de « depuis » ni « jusqu'à » (le registre est né le 30/09 : `first_seen_at` ne dit rien d'avant) | `app_relation` | impossible de dire « vendeur jusqu'à l'acte du 23/10 », ni « nouveau propriétaire depuis » |
Chiffres d'ensemble (contacts actifs du cloud, 39 675) : **17 856 mandants, 14 692 propriétaires, 5 870 acheteurs, 4 102 acquéreurs** ; 737
à la fois mandant et acheteur (dont les cas C3), 245 acheteur et acquéreur, 81 mandant et acquéreur, 617 sans type.

---

## 4. Ce qui se fait habituellement dans ce type de logiciel *(pratique générale des logiciels de transaction immobilière et obligation
légale — à confirmer par Frédéric sur ses propres usages)*

1. **Une personne = une fiche**, et des **rôles** qui en découlent, jamais saisis à la main : le rôle se **déduit** des faits (un mandat signé,
   une offre, une recherche), il ne se stocke pas.
2. **Le mandat porte ses mandants, figés à la signature.** C'est aussi une **obligation légale** : le registre des mandats (loi Hoguet et son
   décret de 1972) inscrit pour chaque mandat un numéro d'ordre, la date et **le nom et l'adresse du mandant** — tels qu'au jour de la
   signature, sans rature. Les mandants d'un mandat **ne se recalculent pas** d'après les propriétaires d'aujourd'hui.
3. **La propriété d'un bien est datée** : propriétaire *depuis* / *jusqu'à* (la vente y met fin). Les logiciels gardent l'historique
   (ancien propriétaire, nouveau propriétaire).
4. **La transaction porte ses parties** : les **vendeurs** (= les mandants du mandat sous lequel elle se fait), les **acquéreurs** (et
   co-acquéreurs), les **notaires** ; et son **étape** (offre → compromis → acte).
5. **L'acquéreur est un PROJET** (une recherche) qui a un **statut** : actif, en pause, **réalisé** (il a acheté), abandonné. L'achat clôt (ou
   propose de clore) la recherche.
6. **Les événements font avancer les rôles** : estimation → propriétaire ; mandat signé → mandant ; offre → acheteur (offre) ; compromis →
   acheteur (compromis) ; acte → la vente est faite, le mandat est clos, la recherche de l'acheteur est réalisée, la propriété du vendeur
   prend fin.

---

## 5. La proposition — « un fait, une source ; le type se déduit » *(rien n'est codé ; chaque point attend une décision)*

### 5.1 Qui porte quel fait (une seule source chacun)
| fait | registre source | aujourd'hui | proposé |
|---|---|---|---|
| la personne | **contacts** | ✅ | inchangé |
| le projet d'achat | **recherches** | ✅ | + un **statut « réalisé »** posé par l'acte (C7) |
| « X est propriétaire de ce bien » | **relations** | ✅ sans durée | + **depuis / jusqu'à** et **l'origine** (déclaré dans l'app, Hektor, acte) (C11) |
| « X a signé ce mandat » | **mandats** | ⛔ texte seulement | ⭐ **les mandants du mandat, des personnes à nos deux numéros, FIGÉS** (C2) — repris des propriétaires **à la signature**, puis jamais recalculés |
| « X fait cette offre / ce compromis / cet acte » | **transactions** | ✅ acquéreurs (numéros) | inchangé ; + **les vendeurs à nos numéros** (C4) |
| « X est notaire de l'affaire » | **transactions** | ✅ | inchangé |

### 5.2 Les 4 types, déduits de ces faits
| type | se déduit de | change à |
|---|---|---|
| **Mandant** | il figure parmi les mandants d'**au moins un mandat** (registre des mandats) — « en cours » si le mandat l'est | la signature, la clôture |
| **Propriétaire** | il est propriétaire (relation **en cours**) d'un bien **sans mandat en cours** — le vendeur potentiel (estimation) | l'estimation, la signature |
| **Acheteur** | il est acquéreur (ou co-acquéreur) d'au moins une transaction (registre des transactions) — avec son étape | l'offre, le compromis, l'acte |
| **Acquéreur** | il a une recherche **active** (registre des recherches) | la création, la clôture de la recherche |
Et la règle de Frédéric s'écrit d'elle-même : **un acheteur ne devient jamais « Mandant » parce qu'il a acheté** (il n'a signé aucun mandat) ;
s'il revend un jour, il signera un mandat et deviendra mandant **à ce moment-là**.

### 5.3 Les événements et leurs effets (le « mécanisme »)
| événement | effet sur les registres |
|---|---|
| **estimation créée** | relation : le(s) propriétaire(s) du bien (origine : saisi) → type **Propriétaire** |
| **mandat signé** | mandats : la liste des **mandants figée** (proposée depuis les propriétaires du bien, corrigeable) → type **Mandant** |
| **offre / compromis** | transactions : acquéreurs (+ co-acquéreurs), vendeurs = mandants du mandat → type **Acheteur** (étape) |
| **acte (vente)** | transactions : la vente ; mandats : le mandat clos ; relations : la propriété du vendeur **prend fin à la date de l'acte** ; recherches : la recherche de l'acheteur **passe « réalisé »** (ou on le propose) ; ⛔ l'acheteur n'est **pas** ajouté comme mandant — *(et comme « nouveau propriétaire » ? décision D2)* |
| **vente supprimée** | défait **ce que l'acte a fait** : la propriété du vendeur reprend, la recherche de l'acheteur revient, rien d'autre |
| **Hektor ajoute l'acheteur aux propriétaires** (depuis le 17/07) | la nuit **ne le range pas** comme propriétaire / mandant de ce bien (sauf s'il l'était avant la vente) ; on le note (C3) |

### 5.4 Ce qui découle pour l'écran
- **Une seule fonction de type**, partagée par l'annuaire, la fiche, le mobile et le cockpit (C8).
- **Les types se calculent à la lecture**, depuis les registres, pas la nuit (C6) — ou la nuit **et** au geste, à décider.
- **La rubrique Contact d'un bien** ne lit plus que nos registres (C9) : propriétaires (relations), mandants (le mandat), acheteurs (transactions).

### 5.5 Les décisions qui t'appartiennent
| | la question | ce que je recommande |
|---|---|---|
| **D1** | « Mandant » = **a signé un mandat** (figé au mandat), plutôt que « propriétaire d'un bien sous mandat » ? | **oui** — c'est la loi et la pratique, et c'est ce qui règle C1, C2, C3 |
| **D2** | après l'acte, l'acheteur est-il inscrit **« nouveau propriétaire »** du bien (sans être mandant), ou pas du tout ? | ta règle dit « jamais propriétaire » ; l'usage le garde comme nouveau propriétaire **daté** (utile s'il revend). À toi |
| **D3** | le vendeur après l'acte : il reste **Mandant** (mandat clos, historique) — affiché « Mandant (vendu) » ? | oui, historique |
| **D4** | la recherche de l'acheteur à l'acte : **close automatiquement**, ou **proposée** à la clôture ? | proposée (un clic), car un acheteur peut chercher un second bien |
| **D5** | les 127 liens « acheteur = mandant » et les 76 mandats qui montrent l'acheteur : **rattrapage** (marqués, jamais supprimés) ? et chez Hektor : ne rien toucher, ou délier ? | rattraper chez nous, **ne rien toucher chez Hektor** |
| **D6** | les mandants des mandats existants (26 929, texte seulement) : les reconstruire **une fois** depuis les propriétaires connus **avant la date de signature**, et marquer « reconstitué » ? | oui, avec la marque « reconstitué » ; les mandats créés ensuite seront figés à la signature (étape 3) |
| **D7** | les types : calcul **à la lecture** (toujours juste, un peu plus de calcul) ou **la nuit + au geste** ? | à la lecture, si la mesure de vitesse le permet (comme pour la pièce 5) |
| **D8** | l'ordre | voir 5.6 |

### 5.6 L'ordre proposé (des chantiers séparés, chacun audit → proposition → « vas-y »)
1. **Arrêter l'hémorragie (C3)** : la règle d'import de nuit — l'acheteur d'une vente n'est pas rangé propriétaire / mandant de ce bien. *(petit,
   additif, derrière un interrupteur ; décisions D2, D5)*
2. **Les mandants du mandat (C2, C1)** : une liste de personnes au mandat, reconstituée une fois (D6), puis le registre des mandats et le type
   « Mandant » la lisent. *(le plus gros ; touche le registre des mandats et l'étape 3)*
3. **Nos numéros dans les vendeurs des transactions (C4)** : comme les pièces 1-2 pour les acquéreurs.
4. **La pièce 5 (C5)** et **les types à la lecture (C6, C8)** : une seule fonction de type, qui lit les registres.
5. **L'acte et ses effets (C7, C10, C11)** : propriété datée, recherche « réalisé », la vente supprimée qui défait l'acte.
6. **La rubrique Contact d'un bien sur nos seuls registres (C9).**

### 5.7 Ce que ça pourrait casser ailleurs (à auditer à chaque chantier)
Le registre des mandats (affichage, export, l'étape 3) ; le reporting mandant ; `app_contact_activite` ; le rapprochement (les acquéreurs) ; les
relances ; le classeur Sheet (en attente de ⑧) ; l'annuaire et ses filtres serveur (`contactRole`, `contactSearchScope`) ; la vitrine et les RDV
publics (liens sur n° Hektor) ; le push des contacts ; et **la règle « Hektor confirme, il n'écrase pas »** tant que Hektor vit (les mandants
figés ne doivent pas être réécrits par la nuit).

---

## 6. LES DÉCISIONS DE FRÉDÉRIC

### ⛔ D1 — 26/10 : **NON.** *(« Non, un propriétaire d'un bien avec numéro de mandat ; on améliorera plus tard »)*
**« Mandant » reste = propriétaire d'un bien qui porte un numéro de mandat** (la règle du 24/07, `build_contacts_layer.py` l. 1393-1397). Les
mandants figés au mandat (C1, C2) **sont reportés** — « on améliorera plus tard » (c'est aussi l'étape 3 : notre registre électronique des
mandats). **Ne pas relancer sans lui.**
**Ce que ça change à l'ordre du §5.6** : le chantier 2 (les mandants du mandat) sort de la liste pour l'instant. ⚠ **Le défaut C2 demeure** : le
registre des mandats continue d'afficher les propriétaires **actuels** du bien comme mandants — donc l'acheteur, tant que C3 n'est pas réglé.
⭐ **Avec cette définition, régler C3 règle aussi l'essentiel de C2** : si la nuit ne range plus l'acheteur comme propriétaire du bien qu'il a
acheté, il n'est plus « mandant » (il n'a plus de lien au bien), et le registre des mandats ne le montre plus parmi les mandants.

### ⛔ D2 — 26/10 : **B.** *(« oui, l'acheteur devient nouveau propriétaire daté de l'acte, sans être mandant »)*
**Ce que ça impose, avec D1** : aujourd'hui « mandant » = propriétaire d'un bien qui porte un numéro de mandat. L'acheteur devenu propriétaire
d'un bien qui porte encore le numéro du mandat **du vendeur** serait donc rangé « mandant » par la règle actuelle — exactement C3. Pour tenir
« sans être mandant », **le lien de propriété doit savoir D'OÙ et DEPUIS QUAND il vient** (C11) :
- un lien né **de l'acte** (origine « acte », depuis la date de la vente) = **propriétaire**, jamais « mandant » du mandat sous lequel il a acheté ;
- il ne deviendra « mandant » que si un **nouveau** mandat est signé sur ce bien **après** son acte (il revend) ;
- le registre des mandats ne le montre pas parmi les mandants du mandat du vendeur.
Dans l'annuaire, il apparaîtra **Acheteur** et **Propriétaire** (type dominant : Acheteur, par la priorité Mandant > Acheteur > Propriétaire >
Acquéreur). Les 127 liens actuels « acheteur = mandant » deviennent, une fois rattrapés, des liens « propriétaire depuis l'acte ».

### ⛔ D3 — 26/10 : **oui.** *(« le vendeur reste Mandant après l'acte, en historique (mandat clos) »)*
Le vendeur garde le type **Mandant** après la vente : son lien de propriété prend fin à la date de l'acte (« jusqu'à »), mais il reste le
mandant **du mandat qu'il a signé**, mandat clos. À l'écran : « Mandant » (historique, mandat clos). C'est ce que fait déjà la règle
actuelle (le bien vendu garde son numéro de mandat) : **rien à changer** pour lui, sinon dater la fin de sa propriété (C11).

### ⛔ D4 — 26/10 : **proposée.** *(« la clôture de la recherche de l'acheteur est PROPOSÉE à l'acte (un clic), pas automatique »)*
À l'acte, l'app **propose** de clore la (les) recherche(s) active(s) de l'acheteur — un clic ; rien ne se ferme seul (un acheteur peut chercher
un second bien). ⚠ Clore une recherche **passe par Hektor** tant qu'il vit (mémoire « créer une recherche passe par Hektor ») : le geste
d'archivage : le worker sait déjà archiver une recherche (dans la qualification de l'acquéreur, montage décidé le 18/09, `console_job_worker.js` l. ~15855) ; je n'ai **pas** trouvé de geste d'écran « clore cette recherche » — à mesurer au chantier. ⚠ **Corrigé au §7.2 le même
jour : le geste d'écran EXISTE** (« Archiver cette recherche dans Hektor », fiche contact, `handleDeleteContactSearch`). Les **48** recherches actives d'acheteurs de 2026 : **on n'y touche pas** sans décision
(D5 traitera le rattrapage).

---

## 7. L'ACHETEUR APRÈS LA VENTE — ce que fait Hektor, ce que fait l'app *(audit du 26/10, lecture seule, rien codé)*

> Frédéric, 26/10 : « avant de répondre il faut savoir comment se comporte aussi Hektor ; vérifie les 127 actifs ; et surtout,
> après la vente, il ne faut pas archiver la fiche contact de l'acquéreur mais juste rendre inactive sa recherche ».

**Périmètre** : les liens « acheteur rangé propriétaire » du registre des relations (`app_relation`, vivants) et les acheteurs des ventes de
2026. Objets touchés : contact, recherche, relation, transaction. **Annonce, mandat, documents, RDV : non mesurés ici.**

### 7.1 Les liens « acheteur = propriétaire » : il y en a TROIS familles, pas une

Mesure du 26/10 sur la base : **150 lignes vivantes** où l'acheteur d'une vente est rangé « propriétaire du bien » qu'il a acheté.

| famille | lignes | d'où elles viennent | visibles à l'écran ? |
|---|---|---|---|
| **A** — recopiées de Hektor | **~120** (`sync_annonce_contact_link`, `api_annonce_detail_proprietaires`) | Hektor met l'acheteur dans les propriétaires ; la nuit le recopie | ✅ oui (`present_in_hektor = true`) |
| **B** — nées du FILET | **49** (`role_hektor` = `acquereur_compromis` 48, `acquereur_vente` 1 ; source `app_seule`) | `relation_ledger.py` l. 393-432 : le filet `app_relation_app_seule` (21/09) recense les liens que Supabase porte et que le serveur ignore — **acquéreurs compris** — et les verse dans le registre **avec le fait « propriétaire du bien »**, du 02 au 24/10 | ❌ non : `present_in_hektor = false`, la vue ne les montre pas ; le registre des mandats les écarte (`ROLES_MANDANT`) |
| **C** — mandants que Hektor ne montre plus | 6 (59057, 9371, 59629, 17640, 59125, 59269 ; source `app_seule`) | même filet | ❌ non |

⚠ **La famille B contredit la décision du 30/09** (« pas d'acquéreurs dans le registre des relations ») : le filet n'a **aucun filtre de
rôle**. Elle **dort** (invisible, écartée du registre des mandats), mais un lecteur futur du registre — la coupure — y lirait 49 acheteurs
« propriétaires ». Le filet a cessé d'en verser : ses 59 lignes acquéreur ont toutes un `absent_depuis` (mesure `phase2/phase2.sqlite`).
➡ **Noté, pas corrigé** (un registre *delete-never* : les retirer demande une décision).

### 7.2 Ce que l'app fait de l'acheteur après la vente — lu dans le code

| geste | ce qu'il touche | mesure |
|---|---|---|
| **archiver une fiche contact** (⑦-1, `archive_hektor_contact`) | la fiche ET, chez Hektor, **toutes ses recherches** (0 recherche active sur 6 157 contacts archivés, 21/10) | **3 travaux en tout**, les essais du 16/10 sur Gladys DURIEUX. ⭐ **Aucun chemin automatique n'archive une fiche** : ni la vente, ni l'acte, ni la nuit |
| **supprimer une recherche** (`delete_hektor_contact_search`) | **archive** la recherche chez Hektor (`modifDateArchiveCritere`, date du jour), **la fiche reste active** | 3 travaux (12/06 → 18/09), un seul auteur |
| **qualification d'un acheteur** (offre / compromis / vente) | Hektor exige un « acquéreur » : si le contact n'en est pas un, le worker **crée une recherche de qualification puis l'archive** après le geste (`qualifierAcquereursAvantTransaction` l. 15892, `archiverRecherchesDeQualification` l. 16023) | c'est l'origine de recherches « toutes archivées » chez des acheteurs |

⭐ **« Recherche inactive » et « recherche archivée » sont LA MÊME CHOSE** : chez Hektor le champ s'appelle `archive`, et chez nous
`is_active = not archive` (`build_contacts_layer.py` l. 1474-1475). La règle de Frédéric — *rendre inactive la recherche, garder la fiche* —
**est exactement le geste « supprimer une recherche » qui existe déjà** — sur la fiche contact, bouton de chaque recherche
(`handleDeleteContactSearch`, App.tsx l. 42985, droit `canManageContacts`, question « Archiver cette recherche dans Hektor ? Elle
disparaîtra des recherches actives »). ⭐ **D4 n'a donc pas de geste neuf à inventer** : la proposition à l'acte appellerait ce même
travail, recherche par recherche. Et elle est **déjà respectée par l'app** : rien n'archive une fiche
d'acheteur à sa place.

### 7.3 Les acheteurs des ventes de 2026, aujourd'hui (307 personnes, base du 26/10)

| | avant le 17/07 | depuis le 17/07 |
|---|---|---|
| fiche active, **au moins une recherche active** | 29 | 22 |
| fiche active, aucune recherche | 158 | 53 |
| fiche active, recherches toutes archivées | 3 | 9 |
| **fiche ARCHIVÉE** | 25 | 8 |
| contact introuvable | 1 | — |

- **51 acheteurs ont encore une recherche ACTIVE** après leur achat — ils continuent de recevoir des rapprochements. C'est le cas que D4
  (proposer la clôture de la recherche à l'acte) réglerait.
- **33 fiches d'acheteurs sont archivées** — **par des humains dans Hektor** (l'app n'a archivé que 3 fiches, toutes d'essai).
  ➡ c'est contraire à la règle de Frédéric, et l'app ne peut pas l'empêcher : ça se passe chez Hektor.

### 7.4 « Ce que ça pourrait casser ailleurs » — l'éligibilité

Un contact ne monte vers l'app que s'il est **lié à une annonce active**, **a une recherche active** (`build_contacts_layer.py` l. 1750-1754)
**ou est nommé dans une transaction lue à la console** (`elargir_perimetre_console.py`, 11/09). Rendre inactive la **dernière** recherche
d'un acheteur sans autre raison l'**endort** (il n'est plus mis à jour, il n'est pas supprimé — 14/10).
Mesure sur les 307 : **2 seulement** ne tiennent que par leur recherche ; les autres tiennent par une annonce active (274) ou par la
transaction (31). ➡ **Le risque est faible et déjà couvert par l'élargissement du 11/09.**

### 7.5 CE QUE FAIT HEKTOR — lu chez lui le 26/10, en lecture seule *(231 appels, 1 par seconde ou moins)*

Pour chaque lien « acheteur = propriétaire » vivant de notre registre (149 paires bien / acheteur, 142 biens, 149 fiches), j'ai lu l'annonce
(`AnnonceById` : propriétaires, mandats, statut) et la fiche de l'acheteur (`ContactById` : archivage, typologie, recherches).
⚠ **Un refus 403 au 60ᵉ appel** (fiche 423771) : la lecture s'est arrêtée net. **Ce n'était pas un bannissement** — cette fiche est refusée
par Hektor **chaque nuit depuis le 26/05** (`data/hektor.sqlite`, `sync_error` : 209 refus sur 27 fiches, dont celle-ci cette nuit à 02:08,
run en code 0), et le worker n'a rien vu. J'ai repris en sautant les 27 fiches connues pour ce refus : **0 autre refus**.

**1. L'acheteur est-il dans les propriétaires du bien chez Hektor ?**
| réponse | paires | lesquelles |
|---|---|---|
| **OUI** | **125** | toute la famille A (recopiée de Hektor) |
| **NON** | **24** | **exactement** les familles B (18 « acquéreur » du filet) et C (6 mandants du filet) : notre registre y garde un lien que Hektor n'a pas |

**2. Comment Hektor TYPE l'acheteur** : dans la liste des propriétaires, les 125 sont typés **« mandant »** (108 « acquéreur + mandant »,
7 « acquéreur + mandant + partenaire », 3 « mandant », 7 « mandant + partenaire »). ⭐ **Hektor fait lui-même de l'acheteur un « mandant »** :
notre nuit ne se trompe pas en recopiant, elle recopie fidèlement un choix de Hektor. (Chez nous, `typologies_json` porte encore souvent
« acquéreur » seul : la nuit le rattrapera.)

**3. Vrai mandant ou acheteur ajouté par la vente ?** J'ai cherché le nom de l'acheteur dans le **texte du mandat** du bien (le champ
`mandants` des mandats, figé à la signature) :
| | paires |
|---|---|
| **absent du texte du mandat** — ajouté par la vente | **92** |
| pas de mandat sur le bien | 21 |
| ⭐ **NOMMÉ dans le texte du mandat — un VRAI mandant** | **10** — toutes des ventes **anciennes** (2007 → 2021) : 10293, 10447, 10776, 19850, 29546, 29822, 39359, 45119, 45172, 9823 |
| fiche sans nom | 2 |
⚠ **Les 10 vrais mandants ne sont PAS le défaut du 17/07** : la vente ancienne nomme comme acheteur une personne qui est aussi mandante
(revente, ou saisie ancienne). Quatre de ces biens sont **revenus en « Estimation »** (10776, 19850, 29546, 45119). **Un rattrapage ne doit
jamais les toucher** : le critère sûr est « nommé dans le texte du mandat ».

**4. Le statut des biens** : 143 « Vendu », 6 « Estimation » (les anciens ci-dessus).

**5. La fiche de l'acheteur chez Hektor** (148 lues) :
| | fiches |
|---|---|
| active | 113 |
| **ARCHIVÉE** | **35** |
⭐⭐ **ET HEKTOR PROGRAMME L'ARCHIVAGE DE LA FICHE** : **75 fiches portent une date d'auto-archivage** (`dateAutoArchiv`), en 2027 (7) et 2028
(68) — **date de création de la fiche + 1 ou 2 ans** (603539 : fiche du 19/05/2026 → 19/05/2028 ; 605976, notre essai du 23/10 →
23/10/2027). C'est l'auto-archivage RGPD de Hektor, **sur la fiche contact**, pas seulement sur les recherches (mesuré le 16/10 pour les
recherches). ⚠ **Et archiver une fiche archive ses recherches** (règle absolue, 21/10).
➡ **La règle de Frédéric — « ne pas archiver la fiche de l'acquéreur » — Hektor ne la tient pas** : ses humains en ont archivé 35, et sa
machine en archivera 75 de plus d'ici 2028. **L'app ne peut pas l'empêcher tant que Hektor vit** ; elle peut seulement **ne pas le faire
elle-même** (c'est le cas) et, à la coupure, **ne pas reprendre cette règle**.

**6. Les recherches de l'acheteur chez Hektor** : **30 avec au moins une ACTIVE**, 33 toutes archivées, 85 aucune.

### 7.6 Ce que ça change à la proposition

- **D2 tient, et Hektor le confirme à moitié** : Hektor fait bien de l'acheteur le **nouveau propriétaire** — mais il le type **« mandant »**,
  et **sans date** (il n'y a ni « depuis » ni « jusqu'à » dans sa liste). Notre règle « propriétaire depuis l'acte, sans être mandant » est donc
  **une règle À NOUS**, qui s'écarte de Hektor : la nuit devra **ne pas recopier** son « mandant » pour un lien né d'une vente.
- **Le critère d'un rattrapage est trouvé** : lien recopié de Hektor (famille A) **ET** l'acheteur **absent du texte du mandat** **ET** une
  vente au registre pour ce bien et cette personne → **92 liens** (les 21 biens sans mandat chez Hektor sont à regarder à part : leur type dépend du numéro de mandat que NOTRE dossier porte).
  Les **10 vrais mandants** sont écartés par construction.
- **La famille B (49 lignes) est un défaut à part**, né du filet (§7.1) : 18 sont absentes chez Hektor, toutes invisibles à l'écran.
- **D4 a déjà son geste** (§7.2) : « Archiver cette recherche dans Hektor » — c'est exactement « rendre inactive la recherche, garder la fiche ».

### ⏳ D5 — À DÉCIDER PAR FRÉDÉRIC (rien n'est choisi, rien n'est codé)

**La question** : que fait-on des liens existants « acheteur = mandant », et des recherches encore actives des acheteurs ?

| | ce qu'on ferait | chez Hektor | ce que ça pourrait casser |
|---|---|---|---|
| **a — le lien de l'acheteur (92)** | le **re-dater** dans notre registre : « propriétaire depuis la date de l'acte », origine « vente », jamais « mandant » | **rien** (Hektor garde son « mandant ») | la nuit le re-recopierait « mandant » si sa règle n'est pas changée en même temps (C3) ; le registre des mandats ne le montrerait plus parmi les mandants (voulu) ; `app_contact_activite` garderait le bien (il en est propriétaire : voulu) |
| **b — les 10 vrais mandants** | **ne rien faire** | rien | — |
| **c — la famille B (49) et C (6)** | les **marquer retirées** (`retire_le`, registre *delete-never*) avec la raison « née du filet, absente chez Hektor » ; et donner au filet un **filtre de rôle** | rien | rien à l'écran (déjà invisibles) ; le filet ne recense plus d'acquéreurs |
| **d — les recherches actives des acheteurs** | **ne rien fermer en masse** ; la proposition D4 s'applique **aux actes futurs** ; pour les ~30 actuels, une **liste** à faire voir aux négociateurs | un geste par recherche, **seulement** si un humain le décide | une fermeture **endort** un contact qui ne tient que par sa recherche : **2** sur 307 acheteurs de 2026 (les autres tiennent par un bien ou par la transaction, élargissement du 11/09) |
| **e — la fiche de l'acheteur** | **ne jamais l'archiver depuis l'app** (déjà le cas) ; écrire la règle pour la coupure | ⚠ Hektor archive quand même (humains : 35 ; machine : 75 programmées) | — |

**Ma recommandation** : **a + b + c + d + e**, dans cet ordre de chantier : d'abord la règle de la nuit (C3, sinon a est défait la nuit
suivante), puis a et c ensemble (un patch, inverse + répétition), d et e n'ont **rien à coder** aujourd'hui. **C'est à toi de trancher.**

### ⛔ D5 — 26/10 : **a + b + c + d + e.** *(« oui a+B+C+D+E mais il faut pas oublier la pièce 5 »)*
- **a** les 92 liens ajoutés par la vente → « propriétaire depuis l'acte », origine « vente », jamais « mandant » (Hektor non touché) ;
- **b** les 10 vrais mandants (anciennes ventes, nommés au texte du mandat) → **on n'y touche pas** ;
- **c** les 49 + 6 liens nés du filet → marqués retirés (`retire_le`, jamais supprimés) + un filtre de rôle dans le filet ;
- **d** les recherches actives des acheteurs → **aucune fermeture en masse** ; la proposition D4 vaut pour les actes futurs ; une liste pour
  les négociateurs ;
- **e** la fiche d'un acheteur → **l'app ne l'archive jamais** (déjà le cas) ; règle écrite pour la coupure.

**L'ordre des chantiers (§5.6, ajusté par D1 et D5)** — chacun : audit → proposition → « vas-y » :
1. **C3 + D5 a/c** : la règle de la nuit (l'acheteur d'une vente n'est plus rangé mandant du bien acheté), puis le rattrapage des 92 et des 55 ;
2. ~~les mandants du mandat (C2, C1)~~ — sorti par D1 ;
3. **C4** : nos numéros dans les vendeurs des transactions (`mandants_json`, 58 550 personnes) ;
4. ⭐ **LA PIÈCE 5 (C5) + les types à la lecture (C6, C8)** — *Frédéric : « il ne faut pas oublier la pièce 5 »*. Elle est **auditée** (§58 de
   la note du registre des transactions : 35 005 / 35 005 liens reproduits, deux index, 0,12 s sans index) ; **deux questions restent à lui** :
   montrer le montant des offres sur la fiche, et faire le point 4 (le worker qui retire notre numéro des co-acquéreurs en journée) avant ou après ;
5. **l'acte et ses effets (C7, C10, C11, D4)** ;
6. **la rubrique Contact d'un bien sur nos seuls registres (C9)**.

---

## 8. CHANTIER 1 — C3 + D5 a/c : l'acheteur n'est plus « mandant » du bien acheté *(audit du 26/10, lecture seule, rien codé)*

### 8.1 Ce que l'audit a établi
- **Quand Hektor ajoute l'acheteur** (mesure, transactions depuis le 17/07) : **à la VENTE** — 92 acheteurs sur 92 rangés propriétaires ;
  au compromis seul 1 sur 72, à l'offre seule 5 sur 119 (des co-propriétaires déjà là). ➡ la règle se déclenche sur **la vente**.
- **Où naît le « mandant »** : `build_contacts_layer.py` l. 1393-1397 rebaptise tout propriétaire « mandant » si le bien a un numéro de mandat ;
  la table de nuit et `relation_roles_json` (les types de l'annuaire) en sortent ; `relation_ledger.py` (run l. 1045, **après** le registre des
  transactions l. 912) recopie le rôle dans `app_relation` ; la vue `app_contact_relations_current` (branche 1) refait le même calcul
  (« mandant » si le bien a un numéro) ; `export_app_payload.py` (`ROLES_MANDANT = {mandant, proprietaire}`) met **tout propriétaire actuel**
  parmi les mandants du registre des mandats.
- ➡ **Il y a donc QUATRE endroits qui décident « mandant » à partir du seul numéro du bien** : la nuit (types), le registre des liens, la vue, le
  registre des mandats. Renommer le rôle à un seul endroit ne suffirait pas : il faut **un fait stocké** que les quatre lisent.
- **Le critère sûr** (mesuré chez Hektor, §7.5) : la personne est **acheteur d'une vente** de ce bien **ET** son nom **n'est pas** dans le texte
  du mandat (`app_mandat.mandants_texte`, figé à la signature, gardé même mandat clos) **ET** sa fiche a un nom. → **113 liens** (92 + 21 biens
  dont Hektor n'expose plus le mandat) ; **écartés : les 10 vrais mandants et les 2 fiches sans nom**.

### 8.2 Ce que ça pourrait casser ailleurs — vérifié
| lecteur | effet | verdict |
|---|---|---|
| **retirer un mandant** (`app_unlink_mandant_optimistic`, écran l. 3590) | le refus se fonde sur le **numéro de mandat du bien**, pas sur le rôle | ✅ inchangé : l'acheteur reste non retirable sur un bien numéroté |
| **registre des mandats** (`mandants_json`) | l'acheteur sort des mandants du mandat du vendeur | ✅ voulu (D2), et c'est l'essentiel de C2 |
| **activité du contact** (`app_contact_activite`) | le bien acheté reste dans son activité, comme propriétaire | ✅ voulu (D2) |
| **annuaire** (types, filtres « Mandants ») | ~113 contacts passent de **Mandant** à **Acheteur** (priorité Mandant > Acheteur > Propriétaire) | ✅ voulu ; le compteur « Mandants » baisse d'autant |
| **push des contacts** | ~113 fiches repoussées (leurs rôles changent) | ✅ négligeable |
| **classeur Sheet, transactions** | lisent `mandants_json` **du registre des transactions**, pas `app_relation` | ✅ non touchés |
| **invités d'un RDV par bien** | l'acheteur y figure « propriétaire » au lieu de « mandant » | ✅ sans effet sur l'envoi |
| **Hektor** | **rien n'est écrit chez lui** ; il continue de dire « mandant » | ⚠ divergence **voulue** et écrite : notre fait est dans nos colonnes, la nuit ne le défait pas |
| **l'acheteur qui revend un jour** | un nouveau mandat le nommera → il redevient « mandant » | ✅ si la règle est **recalculée chaque nuit** (seule la date est figée) |
| **le push du registre des liens** | il envoie la table locale **entière**, `retire_le` compris | ⚠ le marquage de c **doit être fait côté local** (sinon la nuit l'efface) — à éprouver |

### 8.3 La proposition — en 5 pièces, derrière un interrupteur
1. **Base (patch additif, inverse + répétition)** : deux colonnes à `app_relation` — `origine` (« vente » ou vide) et `proprietaire_depuis`
   (date de l'acte) ; la vue : `role_contact = 'proprietaire'` quand `origine = 'vente'`. **Inerte** tant que rien n'écrit `origine`.
2. **La règle, UNE fois, dans un petit module partagé** (lu par la nuit et par le registre des liens) : acheteur d'une vente du bien (lignes
   « acquéreur vente » de la table de nuit, **la même nuit**) + absent du texte du mandat + nom connu → propriétaire depuis la date de la vente.
3. **La nuit** (`build_contacts_layer.py`) : le renommage « mandant » ne s'applique plus à ces liens → les types disent **Acheteur**.
4. **Le registre des liens** (`relation_ledger.py`) : pose `origine` / `proprietaire_depuis` (la date gardée, la règle recalculée) ; **le
   rattrapage des 113 se fait tout seul à la première nuit** — pas de script à part. **Et c** : le filet ne recense plus que les rôles du bien,
   et les 55 lignes nées du filet sont marquées retirées (`retire_par` = « filet_26_10 »), côté local.
5. **Le registre des mandats** (`export_app_payload.py`) : n'inscrit pas parmi les mandants un lien d'origine « vente ».
- **Interrupteur** : `APP_RELATION_ACHETEUR_PROPRIETAIRE=1` dans `.env` (pièces 2-5) ; **retour arrière** : l'éteindre (la nuit suivante
  remet l'ancien calcul) + l'inverse du patch.
- **Essais avant toute pose** : sur une copie de `phase2.sqlite` — 113 liens marqués, 10 + 2 intacts, la liste des types qui changent, le registre
  des mandats avant / après sur les biens vendus ; mutants (critère du nom retiré, date retirée, filtre de rôle retiré).
- **Ce qui attend aussi** : la pièce 5 (chantier 4), qui projette les acquéreurs depuis le registre des transactions — indépendante de celui-ci.

---

## 9. CHANTIER 1 CODÉ — l'acheteur « propriétaire depuis la vente » *(26/10, « VAS Y » de Frédéric)* — **rien n'est posé**

### 9.1 Ce qui est écrit
| pièce | fichier | ce qu'elle fait |
|---|---|---|
| la règle, une fois | `phase2/contacts/regle_acheteur_proprietaire.py` (neuf) | acheteur d'une **vente** du bien + **absent du texte du mandat de Hektor** + nom connu → né de la vente, daté de la (première) vente ; sans registre des mandats, **refuse de juger** |
| la nuit (types) | `phase2/contacts/build_contacts_layer.py` (`load_relations`) | ces liens restent « proprietaire » au lieu d'être rebaptisés « mandant » → l'annuaire dit **Acheteur + Propriétaire** |
| le registre des liens | `phase2/sync/relation_ledger.py` (`_poser_les_liens_nes_de_la_vente`) | pose `origine = 'vente'` et `proprietaire_depuis` (jamais réécrite), recalcule chaque nuit, lève ce qui ne l'est plus ; **D5 c** : le filet ne prend plus que les rôles du bien ; le push nomme les deux colonnes |
| le registre des mandats | `phase2/sync/export_app_payload.py` (`charger_mandants_du_registre_des_liens`) | n'inscrit pas parmi les mandants un lien d'origine « vente » (sert aussi la fiche et `mandat_ledger`) |
| la base | `supabase/patch_acheteur_proprietaire_2026-10-26.sql` + `_INVERSE` + `_REPETITION` | 2 colonnes additives ; la vue : **une ligne** ajoutée au CASE (empreinte `6c89ceb7` vérifiée, aller-retour prouvé par calcul) ; les **55** liens du filet marqués retirés (`filet_26_10`) |

**Interrupteur** : `APP_RELATION_ACHETEUR_PROPRIETAIRE=1` dans `.env` — **éteint** (absent). Éteint, tout se comporte comme avant ; la
nuit où l'on éteint, le registre remet à vide **et pousse ce vide une fois** (sinon la vue resterait allumée).

### 9.2 ⭐ Ce que l'écriture a trouvé — et qui aurait faussé le rattrapage
Ma première version jugeait le nom sur `app_mandat.mandants_texte`. **Elle ne trouvait que 73 liens sur 113.** Cause : `mandat_ledger.py`
(l. 645-668) **remplace** ce texte par nos liens quand le corps de Hektor est suspect ou vide sur une vente — donc par une liste qui
**contient déjà l'acheteur** (« M_Mme Florian JACQUIER » sur 61730). Juger sur lui, c'était juger l'acheteur sur la faute qu'on corrige.
➡ La règle lit le texte **tel que Hektor l'a donné** (`payload_json` / `versions_json`) : **113 / 113**, 0 vrai mandant touché, 0 lien en trop.

### 9.3 Les essais
- `phase2/checks/test_regle_acheteur_proprietaire.py` : **15 / 15** (base en mémoire). **4 mutants attrapés** : sans le critère du nom
  (1 échec), sur notre texte pollué (2), le compromis compté comme la vente (5), juger sans registre des mandats (1) ; témoin intact 0.
- `phase2/checks/test_acheteur_proprietaire_sur_copie.py` sur une **copie** de `phase2.sqlite` (refuse la base de production) : **16 / 16** —
  avant : JACQUIER parmi les mandants de 61730 (le défaut, vu) ; allumé : **113 liens posés**, JACQUIER daté du **2026-09-25**, les 10 vrais
  mandants intacts ; une 2ᵉ nuit **garde la date** ; le registre des mandats **perd JACQUIER et garde les 3 GARCIA**, **109** acheteurs retirés
  des mandants (les 4 autres n'y étaient pas inscrits — sans nom ou dédoublonnés par nom, **non mesuré**) ; le push nomme les colonnes ; éteint : **113 remis à vide**, le vide part une fois, puis
  plus ; le registre des mandats revient à l'ancien calcul.
- la nuit des contacts (types) : **100 contacts cessent d'être « Mandant », 0 le devient** ; JACQUIER : offre + compromis + vente + **propriétaire** → **Acheteur + Propriétaire** (ces 100 ont 113 liens ; certains restent mandants d'un autre bien qu'ils possèdent vraiment). Total de l'essai sur copie : **19 / 19**
- `phase2/contacts/test_contacts_layer.py` (existant) : vert, interrupteur éteint.

### 9.4 ⏳ Ce qui reste — À FRÉDÉRIC (dans cet ordre, jamais l'inverse)
1. **Le patch Supabase** (`supabase/patch_acheteur_proprietaire_2026-10-26.sql`) — écriture en production, **ton accord** ; puis la
   répétition (partie A : lignes 1-5 vertes, 6-9 « en attente de la nuit »).
2. **Pousser** le code (`git push`).
3. **Allumer** `APP_RELATION_ACHETEUR_PROPRIETAIRE=1` dans `.env` — ⛔ **jamais avant le patch** : le push des liens nommerait deux
   colonnes inconnues et le lot entier tomberait.
4. Le lendemain matin : la répétition (partie B), le bilan de la nuit (`acheteur_nes_de_la_vente`, ~113), et l'annuaire sur JACQUIER.
- ⚠ **Aucun service à redémarrer** : la nuit lit le code du dépôt ; le worker n'est pas touché.
- ⚠ **Le code est déjà dans le dossier de travail** et la nuit le lit : interrupteur éteint, il ne change rien (prouvé ci-dessus, état 0 et 5).

### 9.5 ✅ Le patch Supabase est POSÉ — 26/10, par moi, avec l'accord de Frédéric (« applique toi-même »)
- **Avant** : vue à l'empreinte `6c89ceb7` (celle de l'audit), 55 lignes du filet vivantes, colonnes absentes, 2 retraits existants,
  **167 822 lignes** dans la vue.
- **Le patch** : ses 5 contrôles verts.
- **La répétition, partie A** : lignes 1 à 5 **OK** ; 6 à 9 « en attente de la nuit » (normal : interrupteur éteint). Et deux mesures en plus :
  la vue rend **toujours 167 822 lignes** (le changement est inerte tant que `origine` est vide) ; l'inverse retrouverait l'empreinte
  `6c89ceb7` (aller-retour calculé sur la définition réelle). Droits de la vue inchangés (`authenticated` : lecture).
- ⚠ **La nuit de ce soir** (interrupteur éteint) adopte les 55 retraits depuis la doublure ; le code éteint ne pose rien.

**Il reste à Frédéric** : **pousser** (`git push`), puis **allumer** `APP_RELATION_ACHETEUR_PROPRIETAIRE=1` dans `.env` ; le lendemain matin,
la répétition partie B (~113 liens, le témoin JACQUIER au 2026-09-25, les 10 vrais mandants intacts) et l'annuaire sur JACQUIER.

- ✅ **26/10 à 10:17 : poussé par Frédéric (`3831fb4` sur origin/main) et interrupteur ALLUMÉ** (`APP_RELATION_ACHETEUR_PROPRIETAIRE=1` ajouté à `.env`, lu « ALLUMÉ » par le module). ⏰ **Demain 27/10 au matin** : répétition partie B, bilan de la nuit (`acheteur_nes_de_la_vente`), JACQUIER dans l'annuaire.

---

## 10. CHANTIER 2 — C4 : NOS NUMÉROS DANS LES VENDEURS DES TRANSACTIONS *(audit du 26/10, lecture seule, rien codé)*

### 10.1 Ce que l'audit a établi
- **La forme** : `mandants_json` des compromis et des ventes = la liste des fiches Hektor des vendeurs (`id` Hektor, nom, prénom,
  coordonnées…) — **58 550 personnes** (31 307 sur les compromis, 27 243 sur les ventes), **0 avec notre numéro**, toutes en liste (0 objet seul).
- **La traduction** : avec la table que la nuit utilise déjà pour les acquéreurs (`app_contact`, les deux numéros), **58 550 sur 58 550**
  reçoivent notre numéro (côté Supabase, l'annuaire n'en connaîtrait que 57 111 : la nuit est la bonne porte).
- **Le patron existe** : la pièce 2 (24/10) fait exactement cela pour les acquéreurs — `poser_nos_numeros()` (`affaire_ledger.py`
  l. 1364) **ajoute** `app_contact_id` à côté de `id`, ne remplace rien, garde la forme, n'invente rien, et rend le texte d'origine à l'octet
  quand il n'y a rien à poser. Il suffit de l'appliquer aussi à `mandants_json` (l. ~811).
- **Trois écrivains de la liste** :
  | écrivain | aujourd'hui |
  |---|---|
  | la **nuit** (`affaire_ledger.py`) | ⚠ sans notre numéro → **C4** |
  | la **création / modification dans l'app** (`app_change_annonce_status_optimistic`, `app_modifier_affaire_optimistic`, via `app_acquereurs_json`) | ✅ porte déjà nos numéros (pièce 1) |
  | la **relecture du worker en journée** (`console_job_worker.js` l. ~15280, `partiesRelues`) | ⚠ **réécrit `acquereurs_json` ET `mandants_json` avec la liste brute de Hektor — notre numéro disparaît jusqu'à la nuit** (= le **point 4** resté ouvert). Mesure : 28 acquéreurs sans notre numéro dans 20 transactions, dont 8 traduisibles (donc effacés le jour) |
- **Qui lit la liste** : l'écran (`lireMandantsAffaire`, qui lit **déjà** `app_contact_id` depuis la pièce 4 ; `ckPartiesDuJson` pour les
  noms), le classeur Sheet (les noms seulement), la vue `app_registre_mandats_current`, les deux fonctions ci-dessus. **Ni R2 ni R3 ne
  comparent les listes de personnes** : une clé de plus n'y crée aucun écart.

### 10.2 Ce que ça pourrait casser ailleurs
- **Rien à l'écran** : une clé ajoutée ; les lecteurs lisent `id` et le nom, et `lireMandantsAffaire` sait déjà lire notre numéro.
- **Le push de la nuit** : la première nuit, ~31 000 transactions changent (la clé ajoutée) → un push plus gros, une fois (la pièce 2 a fait
  la même chose pour les acquéreurs sans incident).
- **Le worker** (pièce b) : il faut **redémarrer les 4 services**, file vide (0 pending, 0 running) — geste de Frédéric.

### 10.3 La proposition — deux pièces
- **a — la nuit** : `poser_nos_numeros()` appliqué aussi à `mandants_json`, derrière un **interrupteur neuf**
  `APP_AFFAIRE_VENDEURS_DEUX_NUMEROS=1` (séparé de celui des acquéreurs : son propre retour arrière). Essai sur copie : 58 550 posés, 0
  inventé, le texte d'origine gardé à l'octet quand rien n'est à poser.
- **b — le worker (point 4)** : quand il relit les acquéreurs et les vendeurs chez Hektor, **il garde notre numéro** — repris de la liste
  qu'il remplace (même `id`), sinon cherché dans l'annuaire (`app_contact_current.hektor_target_id`) ; inconnu = rien. Pour les **deux**
  listes. Essai hors ligne avec mutants ; puis redémarrage des 4 services.
- **Ordre recommandé** : a puis b, ou les deux ensemble (un seul redémarrage). **À trancher par Frédéric.**

### 10.4 ⚠ POURQUOI CE TROU — audit du 26/10 *(Frédéric : « cela m'étonne que le registre des transactions ne soit pas autonome au niveau
des id […] et n'oublie pas que les workers qui communiquent avec Hektor doivent lui envoyer son propre id, pas le nôtre »)*

**L'inventaire des numéros du registre des transactions** (31 086 transactions vivantes, mesure du 26/10) :
| objet | notre numéro | celui de Hektor | état |
|---|---|---|---|
| la transaction | `app_affaire_id` 31 086 | `hektor_affaire_id` 31 086 | ✅ |
| le bien | `app_dossier_id` 31 086 | `hektor_annonce_id` 31 086 | ✅ |
| la chaîne offre → compromis → vente | `app_chaine_id` 31 086 | (n'existe pas chez Hektor) | ✅ |
| l'acquéreur principal | `app_contact_id` 30 424 | `hektor_acquereur_id` 30 433 | ✅ (pièce 1, G-10) |
| les co-acquéreurs | `acquereurs_json[].app_contact_id` | `acquereurs_json[].id` | ✅ la nuit (pièce 2) — ⚠ effacé le jour par le worker (point 4) |
| les notaires (deux côtés) | `notaire_acquereur_id` 6 772 / `notaire_mandant_id` 16 568, **tous à notre numéro** | trace brute dans `notaires_json` (vente) et `app_affaire_console` (compromis) | ✅ (pièce 3) |
| **les vendeurs** | **aucun** | `mandants_json[].id` 58 550 | ❌ **le trou (C4)** |
| **le mandat** | **aucune colonne** `app_mandat_id` | `hektor_mandat_id` 14 976 (recyclé par Hektor, mémoire du 10/10) + `numero_mandat` 23 336 | ⚠ **second trou, plus petit** : la transaction désigne son mandat par le numéro métier ; les 23 336 se retrouvent au registre des mandats par (bien, numéro), mais notre identifiant n'y est pas stocké |
Les autres registres portent tous leurs deux numéros : liens (`app_relation`, quatre numéros), mandats (`app_mandat_id` + `hektor_mandat_id`, et
la personne sous ses deux numéros), contacts (`hektor_contact_id` = nous + `hektor_target_id` = Hektor), recherches (`app_search_id` + la personne).

**LA CAUSE — une décision étendue au-delà de sa question, puis une réserve jamais reposée.**
1. **22/10** (note ARCHITECTURE, §4 A et décision 1) : « *les mandants : Hektor les déduit du mandat* ». La question était **QUI ÉCRIT la liste**
   (on n'envoie pas de vendeurs à Hektor, il les déduit ; l'app ne les écrit que s'ils sont affirmés dans la modale). Elle ne disait **rien**
   de **comment on désigne** une personne de cette liste.
2. **24/10** (étude des numéros, §6 et §9 pièce 4) : j'ai écrit « *les mandants sont déduits par Hektor (décision du 22/10) : les inclure est
   une question à part* », puis « *non touchés, et c'est voulu* ». ⛔ **C'était une confusion** : que Hektor décide QUI est vendeur n'empêche
   pas que chaque vendeur porte AUSSI notre numéro — exactement comme les acquéreurs, que Hektor relit lui aussi.
3. **La « question à part » ne t'a jamais été reposée.** Les pièces 1 à 4 ont été faites sur les acquéreurs et les notaires ; les vendeurs sont
   restés dehors sans décision. C'est la leçon de la mémoire « *une réserve d'audit non traitée devient le bug* ».
4. **Pourquoi personne ne l'a vu** : la nuit est le maître du registre (elle le refait depuis le miroir de Hektor) ; elle ne pose notre numéro
   que là où on lui a dit de le faire. Rien ne casse à l'écran aujourd'hui (les noms s'affichent) : **le trou ne se voit qu'à la coupure**, où
   58 550 vendeurs ne seraient plus reliés à leur fiche.

**LA RÈGLE « VERS HEKTOR, SON NUMÉRO » — vérifiée dans le code, et le chantier 2 la garde**
- Le worker vise **toujours** le numéro de Hektor : `cibleHektorContact` (l. 2126 : lit `hektor_target_id` ; un numéro de notre plage sans
  correspondance **n'est jamais envoyé**) et `traduireLesPersonnesDeLaTransaction` (C-9, 23/09 : notaires et vendeurs choisis traduits AVANT
  tout envoi ; s'il manque une traduction, **il s'arrête** au lieu de deviner). Le retrait d'un mandant traduit de même (RPC).
- Le chantier 2 **n'y change rien** : dans les listes, `id` reste le numéro de Hektor (c'est lui qu'on lui parle), notre numéro est **ajouté à
  côté** (`app_contact_id`), et aucun envoi ne lit cette clé. C'est le montage de la pièce 2, déjà en production.

**Ce que ça ajoute à la proposition du chantier 2** : une pièce **c** possible — poser `app_mandat_id` sur chaque transaction (la nuit le
retrouve par (bien, numéro de mandat) : 23 336 sur 23 336), pour que la transaction désigne son mandat par NOTRE numéro aussi. **À trancher.**

### 10.5 ⭐ LA PIÈCE c — QUEL NUMÉRO DE MANDAT ? *(Frédéric, 26/10 : « tu parles du numéro de mandat ou de l'id mandat ? […] on a créé
une clé N° de mandat + réf qui évite les doublons […] l'id mandat de Hektor n'est pas utilisable »)*

Mesure du 26/10 sur `app_mandat` (26 929 mandats) :
| candidat | utilisable ? | pourquoi |
|---|---|---|
| l'id mandat de Hektor (`hektor_mandat_id`) | ❌ | **512** identifiants **recyclés** (portés par plusieurs mandats) — c'est ta remarque, et la mémoire du 10/10 |
| le numéro de mandat seul | ❌ | **4 458** numéros portés par **plusieurs biens** (le n° 1311 sur 13 biens) |
| **la clé « bien + numéro de mandat »** (`UNIQUE (hektor_annonce_id, numero_mandat)` d'`app_mandat` ; c'est aussi la clé de ligne du registre affiché, `register_row_id = "<annonce>:<numéro>"`) | ✅ | **0 doublon** ; c'est la clé anti-doublon que tu décris |
| **notre identifiant `app_mandat_id`** | ✅ | il est **né de cette clé** (une ligne par couple bien + numéro), et c'est NOTRE numéro |
➡ **La pièce c ne prendrait NI l'id de Hektor NI le numéro seul** : elle **retrouverait le mandat par ta clé** (bien + numéro de la
transaction) et **poserait notre `app_mandat_id`** sur la transaction. Mesure : les 23 336 transactions qui ont un numéro le retrouvent,
**et aucune ne tombe sur deux mandats**. Les 7 750 sans numéro (surtout des offres) restent sans.
⚠ Une limite à dire : la clé utilise le numéro de **bien de Hektor** (`hektor_annonce_id`). Pour un mandat né dans l'app sur une annonce née
dans l'app, il faudra la clé (`app_dossier_id`, numéro) — la même limite que le registre des liens (écrite le 30/09).
**C n'est pas codé : il attend ta décision.**

---

## 11. CHANTIER 2 CODÉ — a (les vendeurs la nuit) + b (le worker garde nos numéros) *(26/10, « OK pour a et b »)* — **rien n'est posé**

| pièce | fichier | ce qu'elle fait |
|---|---|---|
| **a** | `phase2/sync/affaire_ledger.py` (`vendeurs_deux_numeros_actif`, et la boucle de la nuit) | `poser_nos_numeros()` — le geste de la pièce 2 — appliqué aussi à `mandants_json` ; interrupteur **neuf** `APP_AFFAIRE_VENDEURS_DEUX_NUMEROS` (**éteint**) ; le bilan de la nuit dit « vendeurs avec nos deux numéros : N posés » ou « ÉTEINT » |
| **b** | `Console/console_job_worker.js` (`tableDeNosNumeros`, `poserNosNumerosDansLaListe`, dans `reporterAuRegistre`) | la relecture du jour garde notre numéro sur les acquéreurs ET les vendeurs : repris de la liste remplacée (même `id`), sinon par l'annuaire (`hektor_target_id`) ; hors de notre plage ou inconnu = rien ; panne = la liste brute comme avant, journalisée ; `GARDER_NOS_NUMEROS_A_LA_RELECTURE = true` (retour : `false` + redémarrage) |

**La règle « vers Hektor, son numéro »** : intacte. `id` reste le numéro de Hektor dans toutes les listes (l'essai le contrôle, et le
mutant qui le remplace est attrapé) ; aucun envoi ne lit `app_contact_id`.

**Les essais**
- `Console/test_relecture_garde_nos_numeros.js` : **15 / 15** ; **4 mutants attrapés** (sans la reprise du registre : 5 échecs ; sans la
  garde de notre plage : 1 ; notre numéro qui remplace celui de Hektor : 1 ; la panne qui remonte : 3) ; témoin vert.
- `Console/test_controle_carnet_r3.js` et `test_enqueue_rattrapage_carnet.js` (existants) : verts.
- `phase2/checks/test_vendeurs_deux_numeros_sur_copie.py` sur une copie de `phase2.sqlite` : **8 / 8** — éteint : 0 vendeur avec notre numéro ; allumé : **58 514 sur 58 514** vendeurs des transactions vivantes, **0** numéro hors de notre plage, **0** `id` de Hektor changé, acquéreurs et états **inchangés**, aucune transaction gagnée ni perdue ; éteint de nouveau : **les octets d'avant, exactement** (c'est le témoin inverse). ⚠ **36 vendeurs restent sans notre numéro** : ils sont sur des transactions que Hektor **ne liste plus** (`present_in_hektor = 0` : 30 compromis, 6 ventes) — la nuit ne les revoit pas (delete-never), elle ne réécrit donc pas leur liste. Tous traduisibles. Même limite pour les acquéreurs de ces transactions (pièce 2). ➡ **Un rattrapage à part, à décider.**

**Ce qui reste, à Frédéric, dans cet ordre**
1. **Pousser.**
2. **Redémarrer les 4 services du worker**, file vide (0 pending, 0 running) — b est alors actif.
3. **Allumer** `APP_AFFAIRE_VENDEURS_DEUX_NUMEROS=1` dans `.env` (je peux l'ajouter) — a joue à la nuit suivante.
4. Le lendemain : le bilan de la nuit (« vendeurs … ~58 514 posés ») et une mesure en base (vendeurs avec notre numéro).

### 11.1 ✅ 26/10 — a ALLUMÉ, b ACTIF
- **b** : poussé (`3f64ccc` sur origin/main) et **les 4 services du worker ont redémarré à 10:57:27-29**, après le code (10:45:33) —
  mesuré par l'heure des processus. La relecture du jour garde désormais nos numéros.
- **a** : `APP_AFFAIRE_VENDEURS_DEUX_NUMEROS=1` ajouté à `.env` par moi (accord de Frédéric : « je te laisse allumer »), lu « ALLUMÉ ».
  ⏰ **Première nuit : 27/10** — le bilan doit dire « vendeurs avec nos deux numéros : ~58 514 posés ».

---

## 12. CHANTIER 2 — c CODÉ : la transaction porte NOTRE numéro de mandat *(26/10, « oui ensuite code c »)* — **rien n'est posé**

| pièce | fichier | ce qu'elle fait |
|---|---|---|
| la clé | `phase2/sync/affaire_ledger.py` (`notre_mandat_par_cle`) | lit le registre des mandats local par **la clé « bien + numéro de mandat »** (celle de Frédéric : `UNIQUE (hektor_annonce_id, numero_mandat)`, `register_row_id`) ; **jamais** l'id de Hektor (recyclé), **jamais** le numéro seul ; une clé en double serait écartée et signalée, pas tranchée |
| la nuit | même fichier (la boucle et l'UPSERT) | colonne locale `app_mandat_id` ; **retrouvé → posé** ; **pas retrouvé mais même numéro → gardé** (un mandat neuf arrive au registre la nuit d'après : le registre des mandats tourne après) ; **numéro changé → vidé** (garder serait désigner le mauvais mandat) ; bilan « mandat à notre numéro : N » |
| le push | même fichier (`ledger_rows_for_push`) | la colonne **ne part qu'interrupteur allumé** — le push envoie toutes les colonnes locales, une colonne inconnue de Supabase ferait tomber le lot entier |
| la base | `supabase/patch_transaction_mandat_notre_numero_2026-10-26.sql` + `_INVERSE` + `_REPETITION` | **une colonne additive** `app_mandat_id bigint` |

**Interrupteur** : `APP_AFFAIRE_MANDAT_NOTRE_NUMERO` — **éteint**. Ce soir, la nuit ajoute la colonne en local, ne la remplit pas et
**ne l'envoie pas** (prouvé, essai 1).

**Essai** `phase2/checks/test_mandat_notre_numero_sur_copie.py` sur une copie de `phase2.sqlite` : **9 / 9** — la règle de l'UPSERT jouée à part
(posé / gardé / vidé) et reconnue dans le code ; éteint : 0 posé, la colonne ne part pas ; allumé : **23 336 sur 23 336** transactions vivantes à
numéro rattachées, **0** désignant un autre mandat que celui de leur clé, **0** transaction sans numéro touchée, la colonne part ; un mandat
caché au registre : le numéro de la veille est **gardé**. Aucune clé en double au registre des mandats.
⚠ Pas de mutant joué à part pour c : l'essai 0 joue la règle de l'UPSERT, et l'essai 3 en est le témoin réel.

**Ce qui reste, dans cet ordre** : 1. le **patch Supabase** (ton accord) ; 2. **pousser** ; 3. **allumer**
`APP_AFFAIRE_MANDAT_NOTRE_NUMERO=1` — ⛔ jamais avant le patch ; 4. le lendemain, la répétition partie B (~23 336, chaque numéro sur sa clé).

### 12.1 ✅ 26/10 à 11:16 — la pièce c est POSÉE et ALLUMÉE
- Patch Supabase appliqué par moi (accord de Frédéric) : ses 2 contrôles verts ; répétition A verte (colonne présente, 31 103 transactions intactes), B « en attente de la nuit ».
- Poussé par Frédéric (`f9a8ecd` dans origin/main), puis `APP_AFFAIRE_MANDAT_NOTRE_NUMERO=1` ajouté à `.env` par moi, lu « ALLUMÉ ».
- ⏰ **27/10 au matin** : répétition B (~23 336, chaque numéro sur sa clé, 0 sans numéro touché) ; le bilan de la nuit « mandat à notre numéro : N ».

---

## 13. CHANTIER 3 — LA PIÈCE 5 : les acquéreurs d'un contact lus dans NOTRE registre des transactions *(réaudit du 26/10 après-midi, rien codé)*

L'audit complet est au §58 point 2 de `notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md` (ce matin). Remesuré après les
chantiers 1 et 2 :
- **La projection** (le principal par `app_contact_id` + chaque co-acquéreur de `acquereurs_json` par son `app_contact_id`, transactions que
  Hektor liste encore) retrouve **35 005 liens sur 35 005** de la table de nuit ; **+3** : les offres d'essai nées dans l'app (bien 24933).
- **Les colonnes** (mesure du matin, inchangée) : annonce, dossier, date identiques ; « vente » écrit en toutes lettres pour une vente comme
  la nuit ; `is_active_annonce` = le bien n'est pas dans l'index des archives (0 exception) ; **numéro de mandat** : celui DE LA TRANSACTION
  (20 différences avec la nuit, qui prend le mandat courant du bien — le registre est le juste) ; **montant d'une offre** : la nuit n'en porte
  aucun, le registre en a **11 117** → **nouveau sur la fiche**.
- **La vitesse** : la vue d'aujourd'hui répond en **9,6 ms** pour un contact ; la projection **sans index : 124 ms** (deux lectures complètes du
  registre, 31 103 lignes). ➡ **deux index** : (1) le principal par son numéro **en texte** — le même montage qu'`idx_app_relation_contact_texte`
  du registre des liens ; (2) un index partiel sur les **2 447 transactions à plusieurs acquéreurs**, seules à déplier. ⚠ l'expression de
  l'index doit être **exactement** celle de la vue (mémoire « une fonction autour d'une colonne indexée tue l'index »).
- **Le point 4** (le worker effaçait nos numéros le jour) est **réglé** depuis 10:57 (chantier 2 b) : un co-acquéreur d'une transaction du jour
  apparaîtra tout de suite, plus seulement le lendemain.
- **Les lecteurs** (recensés ce matin, aucun touché aujourd'hui) : la fiche d'un contact (`loadContactRelations`), les invités d'un RDV par
  bien, les mandants d'un bien (branche 1, non touchée) ; en base, `app_contact_activite` et `app_unlink_mandant_optimistic` ne lisent que la
  branche 1 ; **le serveur ne lit pas la vue**. ⚠ Les **types** de l'annuaire (`relation_roles_json`) restent calculés la nuit depuis la table de
  nuit : la pièce 5 ne les change pas (c'est la suite, « les types à la lecture »).

### La proposition
1. **Un patch de base** (inverse + répétition) : les deux index (additifs), puis la vue : **la branche 1 inchangée au caractère près**
   (empreinte vérifiée, celle d'après le chantier 1), **la branche 2 lit le registre des transactions** au lieu de la table de nuit — mêmes
   18 colonnes, mêmes types, `relation_source = 'registre_transactions'`, `relation_key = 'aff_<transaction>_<contact>'`.
2. **La table de nuit n'est pas touchée** : elle reste refaite (elle sert encore aux types) ; retour arrière = l'ancienne vue, à l'octet.
3. **Essais avant la pose** : la répétition compare la vue neuve à l'ancienne sur **tous** les contacts (35 005 retrouvés, les écarts du tableau
   seulement) et **mesure le temps** d'une fiche (cible : du même ordre que 9,6 ms).
4. **Aucun redémarrage, aucun push nécessaire** (une vue en base) ; l'écran lit déjà toutes ces colonnes.

### ⏳ À TRANCHER PAR FRÉDÉRIC
- **Q1 — le montant des offres** sur la fiche d'un contact (nouveau : 11 117 offres) : **le montrer**, ou le **masquer** comme aujourd'hui ?
- **Q2 — le « vas-y »** pour le patch, puis son application (écriture en production).

## 14. LA PIÈCE 5 ÉCRITE *(26/10, « vas-y » de Frédéric)* — **le patch n'est PAS appliqué**

- **Q1 non tranchée** (le montant des offres) : je garde le comportement d'aujourd'hui — **masqué** (`NULL` pour une offre, comme la nuit). Une
  ligne du patch (`WHEN (l.kind = 'offre') THEN NULL`) à retirer si Frédéric choisit de le montrer.
- **La vue écrite** (`supabase/patch_piece5_acquereurs_depuis_registre_2026-10-26.sql`, généré par un script — pas retapé) : la branche 1
  (mandants / propriétaires) **gardée au caractère près** ; la branche des acquéreurs en **deux morceaux** sur le registre des transactions —
  le **principal** (`app_contact_id`) et les **co-acquéreurs** (seulement les listes à plusieurs, ou sans principal ; le principal n'y est pas
  répété) — pour que la lecture **par contact** (la fiche) ET **par bien** (les invités d'un RDV) passent par un index.
- **Deux index additifs** : `idx_app_affaire_ledger_contact_texte` (le principal en texte, l'expression exacte de la vue) et
  `idx_app_affaire_ledger_plusieurs_acquereurs` (partiel, les 2 447 listes à plusieurs).
- ⚠ **Piège évité en écrivant** : Postgres n'évalue pas les conditions dans l'ordre écrit — `jsonb_array_length` plantait sur une liste en
  objet seul (une offre). Protégé par un `CASE`, comme ailleurs dans le projet.
- **Comparaison en lecture seule, sur TOUS les contacts** : **35 005 / 35 005** liens de la nuit retrouvés, **0** clé en double, +3 offres
  d'essai (24933) ; dossier, état, date, montant, bien actif : **identiques** ; numéro de mandat : **20** écarts (le registre a le juste ; les
  7 396 autres apparents n'étaient qu'une chaîne vide contre une valeur nulle) ; date de mise à jour du contact : 1 973 (sans effet) ; n° de
  dossier 4, titre 1.
- **Vérification à blanc du patch** (un bloc qui fait tout, sauf créer la vue, puis s'arrête) : empreinte `acf77be8` reconnue, une seule
  branche trouvée, et Postgres **accepte** la vue reconstituée (`EXPLAIN` sans erreur). Rien écrit.
- **L'inverse** remet la vue d'avant **à l'octet** (empreinte vérifiée avant d'écrire) et retire les deux index. **La répétition** compare la
  vue neuve à la table de nuit et donne les deux mesures de temps (par contact, par bien).
- **Le temps** ne se mesure qu'avec les index posés : ce sera la première chose après l'application (cible : de l'ordre des 9,6 ms d'aujourd'hui).
- **Aucun push, aucun redémarrage** : c'est une vue en base.

### 14.1 ✅ 26/10 à 11:45 — LA PIÈCE 5 EST POSÉE (patch appliqué par moi, accord de Frédéric ; montant des offres masqué, « OK »)
- **Avant** : vue à l'empreinte `acf77be8`, 167 822 lignes dont 35 005 acquéreurs, index absents.
- **Le patch** : 3 contrôles verts (les deux index, la vue lit le registre des transactions et reste `security_invoker`, **35 008** liens
  acquéreurs).
- **La répétition : 5 / 5** — 35 005 / 35 005 liens de la nuit retrouvés ; 0 clé en double ; dossier, état, date, montant, bien actif
  identiques ; numéro de mandat **20** écarts (connus) ; la branche des mandants / propriétaires **inchangée**. La vue : **167 825** lignes (+3).
- **Le temps** (`EXPLAIN ANALYZE`, deux contacts, cache chaud) :
  | lecture | avant | après |
  |---|---|---|
  | **une fiche contact** (par contact) | 9,6 ms | **38 à 42 ms** (+ ~7,6 ms de planification) |
  | **les invités d'un RDV** (par bien) | — | **5,9 ms** |
  ⚠ **La fiche est ~4 fois plus lente qu'avant** (toujours sous 50 ms, à comparer aux ~2,2 s du résumé des RDV que la fiche attend déjà) : tout
  le surcoût vient des **co-acquéreurs** — les 3 109 transactions à plusieurs personnes sont relues à chaque fiche (l'index partiel les trouve,
  mais Postgres ne peut pas chercher DANS la liste par un index). **Si un jour il fallait mieux** : une petite table des co-acquéreurs tenue à
  jour par un déclencheur sur le registre (une projection matérialisée, toujours dérivée du registre — pas une seconde source). **Non fait, à
  décider.**
- **Retour arrière** : `supabase/patch_piece5_acquereurs_depuis_registre_2026-10-26_INVERSE.sql` (la vue d'avant à l'octet, les index
  retirés). La table de nuit continue d'être refaite : on peut revenir n'importe quand.
- ⚠ **À voir à l'écran** : la fiche d'un contact acheteur (ex. JACQUIER, 10354701) — ses offres, compromis et vente doivent apparaître comme
  avant, la source dit désormais « registre_transactions ». Non vu à l'œil.

### 14.2 ⛔ Frédéric, 26/10 : « NON, ce temps n'est pas acceptable » — l'ouverture d'une fiche contact
- **Oui, c'est l'ouverture de la fiche** : la lecture des liens du contact (`loadContactRelations`), une des lectures que la fiche fait en s'ouvrant.
- **Pourquoi c'est lent, et pourquoi la vue seule n'y peut rien** : pour trouver un CO-acquéreur, Postgres doit ouvrir chaque liste à
  plusieurs personnes (3 109 transactions : 2 447 listes de 2 à 8 personnes + 662 sans principal) — il **ne sait pas** chercher une personne
  À L'INTÉRIEUR d'une liste JSON par un index depuis une vue. Mesure des listes : 1 332 de 2, 154 de 3, 930 de 4, 31 de 5 à 8.
- **Le remède qui rend la vitesse d'avant** : une **petite table d'index des acquéreurs** — une ligne par (transaction, personne), avec
  NOTRE numéro et un index sur lui — **tenue à jour par un déclencheur** sur le registre des transactions (à chaque écriture de
  `acquereurs_json`, du principal ou de `present_in_hektor`), remplie une fois au départ. La vue y cherche la personne par l'index, comme la
  table de nuit aujourd'hui : **de l'ordre de 10 ms**. ⚠ Ce n'est **pas** une seconde source (décision du 30/09) : elle est **dérivée** du
  registre, jamais écrite par personne d'autre que le déclencheur, et se reconstruit à l'identique. **À décider.**
- **En attendant** : la vue d'avant se remet en une minute (`…_INVERSE.sql`, à l'octet) → retour à 9,6 ms tout de suite.

---

## 15. AUDIT COMPLET — LES PERSONNES D'UNE TRANSACTION : où elles vivent, qui les écrit, qui les lit, et quel modèle *(26/10 soir, Frédéric : « une vraie analyse, cela touche à tout mon système, sois expert »)* — lecture seule, rien codé

### 15.1 Où vivent les personnes d'une transaction (base, 26/10)
| où | quoi | numéros |
|---|---|---|
| `app_affaire_ledger.app_contact_id` / `hektor_acquereur_id` | l'acquéreur **principal** (colonnes) | nous / Hektor |
| `app_affaire_ledger.acquereur_json` | le principal, **fiche complète** de Hektor (coordonnées comprises) | Hektor + nous (pièce 2) |
| `app_affaire_ledger.acquereurs_json` | **tous** les acquéreurs : 11 173 en **objet seul** (offres), le reste en liste — **23 835 personnes**, au plus **8** ; **le 1er de la liste est TOUJOURS le principal (0 exception)** ; 0 doublon ; 2 sans notre numéro ; **2 375 fiches sans nom** (les fiches « couple » de Hektor, « Mr./Mme ») | Hektor + nous |
| `app_affaire_ledger.mandants_json` | les **vendeurs** (compromis, ventes) — 58 514 | Hektor + nous (C4, ce soir) |
| `notaire_acquereur_id/_nom`, `notaire_mandant_id/_nom` | les notaires (colonnes) | **nous** (pièce 3) ; brut Hektor dans `notaires_json` (vente) et `app_affaire_console` (compromis) |
| `app_affaire_console` (18 552) | la lecture de la console Hektor : `acquereurs`, `mandants`, `notaires_*` (numéros) et `parties_json` (rôles, noms, téléphones) | Hektor |
| `app_affaire_repartition` | les **négociateurs** et leur part de commission, par chaîne | `hektor_user_id` (ce ne sont pas des contacts) |
| `app_affaire_personne_ecart` | R4 : une personne posée par l'app que Hektor n'a pas gardée (2 lignes) | — |
| le carnet `app_affaire_champ_app` | `notaire_id`, `notaire_mandant_id/_nom` (saisies en attente) | — |

### 15.2 Qui les ÉCRIT
1. **La nuit** — `affaire_ledger.py` (depuis le miroir de Hektor : principal, listes, vendeurs ; nos numéros posés par `poser_nos_numeros`) et
   `registre_depuis_console.py` (les notaires, depuis la console).
2. **L'app, au clic** — `app_change_annonce_status_optimistic` (création) et `app_modifier_affaire_optimistic` (modification), par
   `app_acquereurs_json` (nos deux numéros).
3. **Le worker, en journée** — `reporterAuRegistre` (la relecture chez Hektor ; garde nos numéros depuis 10:57) ; `enregistrerLectureConsole`
   (`app_affaire_console`).
4. **Les envois vers Hektor** traduisent TOUJOURS vers son numéro (`cibleHektorContact`, `traduireLesPersonnesDeLaTransaction`, C-9).

### 15.3 Qui les LIT — et comment
- **Transaction par transaction** (la grande majorité) : la rubrique Affaires et la chaîne (`ckPartiesDuJson`, `affaireAcquereursParties`,
  `aliasNumerosAcquereur`), la modale (préremplissage), les noms des notaires, le classeur Sheet (`push_suivi_appsheet.py`), le résumé du
  cockpit et la vue générale (depuis le **miroir**), la vue `app_registre_mandats_current`. ➡ **pour eux, les listes JSON suffisent** : on lit
  UNE transaction et ses personnes.
- **Par personne** (« toutes les transactions de M. X ») — **seulement trois** :
  1. **la fiche d'un contact** (`app_contact_relations_current`, la pièce 5) — c'est là que la liste coûte (38-42 ms) ;
  2. **les types de l'annuaire** (`build_contacts_layer.py`, la nuit, depuis le miroir) — demain « à la lecture » (chantier 4) ;
  3. **le périmètre des contacts** (`elargir_perimetre_console.py`, depuis la console).
- **Par l'acquéreur principal comme CLÉ** : le **chaînage** offre → compromis → vente (`app_chaine_pour`, `app_attribuer_chaines_affaire`) et
  l'**adoption** d'une transaction née dans l'app (worker l. ~21395) — par `hektor_acquereur_id`. ⚠ À ne pas déranger.

### 15.4 Ce que le projet a DÉJÀ décidé (à ne pas rejouer sans le dire)
- **23/09** : le registre garde la **trace brute** de Hektor ; on **ajoute** nos numéros à côté.
- **30/09** : « les acquéreurs **ne se recopient pas** dans le registre des relations ; il les **projettera** depuis le registre des transactions —
  deux copies finissent toujours par dire deux choses ».
- **24/10** (étude des numéros, §8) : ma recommandation « **une table des personnes de l'affaire** » a été **RETIRÉE** sur ta question
  « *on a un registre des contacts et un registre des relations : pourquoi créer encore une liste ?* » → **pas de nouvelle liste** ; nos
  numéros **dans** les listes (pièces 1-4, en production).
- **26/10** : C4 (vendeurs), b (le worker garde nos numéros), pièce 5 (la projection).

### 15.5 Ce que font les logiciels du métier, et l'écart avec le nôtre
Un logiciel de transaction classique a une **table des parties** (une ligne par personne et par transaction, avec son rôle) : c'est la
liaison « plusieurs à plusieurs » ordinaire. **Notre projet porte la même information, mais en listes** dans la transaction (héritage de
Hektor), et **le 24/10 tu as choisi de ne pas créer de liste de plus**. ⭐ **L'audit montre que ce choix tient** : tout ce qui lit
transaction par transaction est servi par les listes, et **il ne manque qu'une seule chose — retrouver UNE personne vite**. Ce n'est pas un
manque de TABLE, c'est un manque d'INDEX.

### 15.6 Les options, jugées contre ces décisions
| | quoi | respecte le 24/10 (« pas de liste de plus ») ? | vitesse | ce qui bouge | risque |
|---|---|---|---|---|---|
| **A — un index par place** | Postgres indexe « le numéro de la 2ᵉ personne », « de la 3ᵉ »… (la 1ʳᵉ est le principal, déjà indexé). **12 places** : 11 petits index ; la vue cherche à chaque place | ✅ **oui** : aucune table, aucune copie | ~10 ms attendus (**à mesurer**) | 11 index + la vue | une limite de places (8 aujourd'hui, 12 prévues) → une sentinelle à 10 |
| B — une table d'index tenue par un déclencheur | une ligne par (transaction, personne), calculée par la base à chaque écriture | ⚠ c'est une liste de plus, même dérivée | ~10 ms | table + déclencheur | le déclencheur s'exécute à **chaque** écriture (nuit, worker, app) : une faute le fait échouer |
| C — la vraie table des parties, maîtresse | les gestes l'écrivent, les listes deviennent la trace de Hektor | ❌ **non** : c'est ce que tu as refusé le 24/10 | ~10 ms | tout : création, nuit, worker, lecteurs | le plus gros chantier ; à reconsidérer seulement pour la coupure (étape 3), si tu le veux |
| D — remettre la vue d'avant | la table de nuit | — | 9,6 ms | rien | on garde la dépendance à Hektor |

### 15.7 Ma recommandation
**A**, parce que c'est la seule qui donne la vitesse **sans revenir sur ta décision du 24/10** ; elle ne touche ni la nuit, ni le worker, ni
l'écran, ni le chaînage ; Postgres tient les index tout seul, quelle que soit l'écriture. **Ce qu'elle pourrait casser** : rien chez les
écrivains ; la vue s'allonge (le temps de préparation est à mesurer) ; une transaction à plus de 12 personnes perdrait la 13ᵉ — d'où la sentinelle.
Elle traite les fiches « couple » exactement comme aujourd'hui (elles sont dans les listes de Hektor). **Et en attendant** : remettre la vue
d'avant (D) tout de suite, puis poser A seulement après l'avoir mesurée (préparation + exécution, par contact et par bien).

### 15.8 ⛔ DÉCISION DE FRÉDÉRIC, 26/10 soir : « oublie ma décision du 24/10, quel serait le meilleur choix ? » → **la vraie table des parties** — « oui »
- **La vue d'avant est REMISE** (26/10 à 13:01, inverse de la pièce 5 appliqué par moi, accord « oui ») : empreinte `acf77be8` retrouvée **à l'octet**,
  les deux index retirés, **167 822** lignes comme avant ; une fiche : **3,9 ms** d'exécution. On est exactement à l'état d'avant la pièce 5.
- La décision du 24/10 (« pas de liste de plus ») est **levée par Frédéric** pour cette table.

---

## 16. LA TABLE DES PARTIES — proposition détaillée *(26/10 soir, rien codé)*

### 16.1 Le principe, en deux temps
1. **Maintenant** : une table `app_affaire_partie` dans sa **forme définitive**, mais **dérivée** des listes du registre par un **déclencheur** —
   elle ne peut pas les contredire ; rien ne change pour la nuit, le worker, l'app ni l'écran ; seule la vue des liens d'un contact la lit.
2. **À la coupure (étape 3)** : les gestes de l'app y écrivent **directement** ; les listes JSON ne restent que la trace de Hektor.

### 16.2 La table
| colonne | rôle |
|---|---|
| `app_affaire_id` | la transaction (NOTRE numéro) |
| `role` | `acquereur` · `vendeur` · `notaire_acquereur` · `notaire_vendeur` |
| `rang` | la place dans la liste (1 = le principal pour les acquéreurs — vrai sur 100 % des listes, mesuré) |
| `app_contact_id` | NOTRE numéro de la personne (indexé) |
| `hektor_contact_id` | celui de Hektor (pour lui parler) |
| `est_principal` | l'acquéreur principal |
| `fiche_sans_nom` | les fiches « couple » de Hektor (« Mr./Mme ») : 2 375 aujourd'hui, gardées comme aujourd'hui, marquées |
| `transaction_presente` | recopie `present_in_hektor` : une transaction retirée chez Hektor garde ses parties, marquées (delete-never) |
| `origine` | `listes_du_registre` (le déclencheur) ; plus tard `app` (étape 3) |
**Volume attendu** : ~117 000 lignes (acquéreurs ~35 000, vendeurs ~58 500, notaires ~23 300).

### 16.3 Le déclencheur
- `AFTER INSERT OR UPDATE` sur `app_affaire_ledger`, **seulement si les personnes ont changé** (`acquereurs_json`, `acquereur_json`,
  `mandants_json`, le principal, les notaires, `present_in_hektor`) — sinon la nuit, qui renvoie les 31 103 transactions, le ferait tourner
  31 103 fois pour rien.
- Il **recalcule les parties de CETTE transaction** (supprime les siennes d'origine « listes », réinsère) — rien d'autre.
- ⛔ **Il ne fait JAMAIS échouer l'écriture qui l'a appelé** (nuit, worker, geste de l'app) : en cas d'erreur, il la note dans un journal et laisse
  passer ; une **sentinelle** quotidienne compare la table aux listes et sonne ; une fonction **reconstruit** tout à l'identique.
- Il couvre **tous les écrivains** sans toucher leur code (c'est une règle de la base) : la nuit (push), le worker (relecture du jour), l'app
  (création, modification), R2, les notaires de la console, les outils d'identité (`app_decaler_doublure`).

### 16.4 Les droits
- La table applique **la même règle que le registre** : un négociateur ne voit que les parties des transactions qu'il voit (politique =
  « la transaction m'est visible », en relisant `app_affaire_ledger` sous ses droits). Aucune écriture permise à l'écran.

### 16.5 Ce qui la lit (ce temps-ci)
- **La vue des liens d'un contact** (pièce 5) : la branche des acquéreurs lit la table des parties au lieu de la table de nuit — par l'index de
  notre numéro, **~ la vitesse d'aujourd'hui** (à mesurer).
- Plus tard : les **types à la lecture**, l'activité d'un contact, « tout ce qu'on sait de M. X ».

### 16.6 Ce que ça pourrait casser — et la garde
| | risque | garde |
|---|---|---|
| la nuit (push des 31 103 transactions) | un déclencheur qui ralentit ou qui échoue | il ne tourne que si les personnes changent ; il n'échoue jamais ; mesure du temps du push avant / après |
| le worker, les gestes | idem | idem |
| les droits | une partie visible hors de son portefeuille | la politique relit le registre sous les droits de l'utilisateur ; essai en négociateur |
| le chaînage, l'adoption | — | **non touchés** (ils gardent leur clé, le principal de Hektor) |
| la table de contacts (refaite chaque nuit) | un lien forcé bloquerait son envoi | **pas de lien forcé** ; une sentinelle vérifie que chaque personne existe |
| la cohérence | la table s'écarte des listes | sentinelle quotidienne + reconstruction |

### 16.7 Les essais, avant toute pose
1. **En lecture seule** : le calcul des parties depuis les listes, comparé aux 35 005 liens acquéreurs de la nuit (les écarts connus seulement).
2. **Dans une transaction ANNULÉE** (accord demandé) : créer la table et le déclencheur, remplir, modifier quelques transactions, vérifier que
   les parties suivent, mesurer la vue — puis **tout annuler** (rien ne reste).
3. **La pose** : patch + inverse + répétition ; sentinelle au moniteur (en lisant les contraintes de sa table — leçon du 25/10).

## 17. LA TABLE DES PARTIES ÉCRITE ET ÉPROUVÉE *(26/10 soir, « vas-y »)* — **RIEN N'EST POSÉ**

### 17.1 Le patch (`supabase/patch_table_des_parties_2026-10-26.sql`, + `_INVERSE`, + `_REPETITION`, générés par script)
- **`app_affaire_partie`** : (transaction, rôle, place) → nos deux numéros, `est_principal`, `fiche_sans_nom`, `transaction_presente`,
  `origine` (`listes_du_registre` aujourd'hui, `app` à l'étape 3) ; index sur notre numéro (en texte, l'expression de la vue).
- **`app_affaire_partie_erreur`** : le journal du déclencheur.
- **Les droits** : RLS ; lecture seule pour `authenticated`, **par la règle du registre** (la politique relit `app_affaire_ledger` sous les droits
  de l'utilisateur) ; aucune écriture ouverte ; `anon` rien.
- **`app_affaire_partie_calculer(ligne)`** : les parties d'une transaction, depuis les listes (liste, objet seul ou rien), les vendeurs, et
  les colonnes des notaires (le numéro de Hektor d'un notaire lu dans l'annuaire).
- **Le déclencheur** (`app_affaire_partie_suivre`, trois déclencheurs : insert, update **seulement si les personnes changent**, delete) :
  recalcule la transaction qui change ; **ne fait jamais échouer l'écriture** (sous-transaction + journal).
- **`app_affaire_partie_reconstruire()`** : tout, à l'identique ; **`app_v_affaire_partie_ecarts`** : la table contre un recalcul complet +
  les erreurs des 24 h (lue par la sentinelle, service seulement).
- **La vue des liens d'un contact** : la branche des acquéreurs lit la table des parties (empreinte `acf77be8` vérifiée avant d'écrire).

### 17.2 L'essai en lecture seule
Le calcul : **116 932 parties** (acquéreurs 35 042, vendeurs 58 550, notaires 6 772 + 16 568) ; **0 clé en double, 0 personne deux fois dans
une transaction** ; les **35 005** liens acquéreurs de la nuit **tous retrouvés** (+3 offres d'essai). Vendeurs sans notre numéro : 58 550 —
normal, **C4 les numérote cette nuit** ; fiches sans nom : 22 528 (19 930 vendeurs, 2 596 acquéreurs — les fiches « couple » de Hektor).

### 17.3 ⭐ L'essai complet DANS UNE TRANSACTION ANNULÉE (le patch entier + 9 épreuves, puis tout annulé — vérifié : rien ne reste)
| épreuve | résultat |
|---|---|
| la pose | 116 932 parties, **0 écart**, 35 008 liens acquéreurs dans la vue |
| **une nuit ordinaire** (les 31 103 transactions renvoyées sans changement) | **2 044 ms sans le déclencheur, 2 099 ms avec** : +55 ms, il ne tourne pas ; parties inchangées |
| **la nuit de C4** (les vendeurs de 19 884 transactions changent) | **21,9 s** (une fois) ; **0 écart** après |
| un acquéreur retiré (transaction 4195) | 3 → 2 parties |
| une transaction retirée chez Hektor (30233) | 3 parties gardées, toutes marquées ; elle sort de la vue |
| **le déclencheur en panne** (contrainte impossible posée exprès) | **l'écriture du registre passe** ; la panne est **au journal** ; **la sentinelle la voit** |
| la reconstruction | tout remis, **0 écart** |
| **le temps** | fiche contact : **4,7 ms** (JACQUIER, 1ʳᵉ fois : 17 ms de préparation) et **2,6 ms** ; **par bien** (invités d'un RDV) : **3,7 ms** — aujourd'hui 3,9 ms |
| **les droits** (un commercial, 142 biens) | 1 585 parties de **ses** 479 transactions ; **0 hors de son portefeuille** ; aucune écriture possible |

### 17.4 Ce qui reste avant la pose
- **La sentinelle au moniteur** (`data.affaire_partie_ecart`, warning, lit `app_v_affaire_partie_ecarts`) : **ajoutée AU MOMENT de la pose**, pas
  avant — sinon le moniteur lirait une vue absente et passerait au rouge (« une lecture ratée n'est jamais un vert »).
- **Le moment** : cette nuit jouent pour la 1ʳᵉ fois chantier 1, C4 et c. Poser la table **ce soir** ajouterait ~22 s au push de la nuit (les
  vendeurs de C4) et une 4ᵉ nouveauté. ➡ **Je recommande de la poser APRÈS la vérification de demain matin** : une nouveauté à la fois.
- **Après la pose** : la répétition, le temps réel d'une fiche, et le push de la nuit suivante (son temps, avant / après).

## 18. ✅ LA TABLE DES PARTIES EST POSÉE — 26/10 à 13:21 *(Frédéric : « non, maintenant, il est 13 h ! mais attention, cette table doit aussi se mettre à jour comme le reste de mon mécanisme si mise à jour Hektor »)*

### 18.1 « Elle doit suivre les mises à jour de Hektor » — vérifié dans le code
Le déclencheur réagit à **toute** écriture du registre des transactions, d'où qu'elle vienne. Recensement des écritures (code, 26/10) :
la **nuit** (`affaire_ledger.py`, la recopie du miroir de Hektor puis l'envoi de tout le registre), les **notaires** lus à la console
(`registre_depuis_console.py`), le **worker** après chaque geste (la relecture chez Hektor, `reporterAuRegistre`, et ses autres PATCH :
numéro Hektor, états), les **gestes de l'app** (création, modification), et les scripts d'identité ponctuels. **Aucun ne range des personnes
ailleurs** : la table suit donc Hektor **dès que le registre le suit** — dans la journée par le worker, la nuit par la recopie ; une
transaction que Hektor ne liste plus (`present_in_hektor` à faux) garde ses parties, marquées.

### 18.2 La pose
- État avant : vue `acf77be8`, table absente, **0 travail en cours**, 31 103 transactions.
- **Le patch** : 6 contrôles verts — 116 932 parties, **0 écart**, la vue lit la table des parties, 35 008 liens acquéreurs, aucune écriture ouverte.
- **La répétition : 7 / 7** — 35 005 / 35 005 liens retrouvés, aucune clé en double, colonnes identiques, mandants / propriétaires inchangés ;
  vendeurs sans notre numéro : 58 550 (C4, cette nuit).
- **Le temps réel**, après `ANALYZE` de la table neuve : **fiche contact 2,8 ms** d'exécution (3,9 ms avant) ; **par bien 3,2 ms**.

### 18.3 ⚠ Deux corrections faites APRÈS la pose — dites franchement
1. **La sentinelle était trop lente** : **7,4 s par l'API**, pour une limite de **8 s** (rôle `authenticator`). Cause : la fonction du calcul
   fixait son `search_path`, ce qui **empêche Postgres de la déplier** — il l'appelait 31 103 fois. Remède : fonction sans `search_path`
   (tables nommées `public.`), et la sentinelle compare par une **jointure sur la clé** au lieu de deux tris. ➡ **2,7-2,9 s par l'API**.
   Témoins positifs (transaction annulée) : une partie retirée, une en trop, une faussée — **les trois vues**.
2. ⛔ **Ce dépliage a cassé le déclencheur** — trouvé par MON essai suivant (transaction annulée, 13:25) : *« invalid input syntax for type
   bigint: "" »* — une fois dépliée, Postgres convertit le numéro du notaire **avant** d'appliquer le filtre ; une colonne vide plantait.
   Le garde-fou a tenu (l'écriture passait, l'erreur allait au journal). **En réel : 0 erreur** (personne n'a écrit dans le registre pendant
   ces minutes — journal lu à 13:27). Remède : **chaque conversion protégée par un `CASE`**. Re-éprouvé (transaction annulée) : un acquéreur
   retiré, une transaction **sans notaire**, un notaire posé — **0 erreur**.
- **État final (13:3x)** : sentinelle **0 écart en 2,9 s**, journal **vide**, 116 932 parties.

### 18.4 Le moniteur
- Sentinelle **`data.affaire_partie_ecart`** (warning) ajoutée à `monitoring/check_gti_health.py` ; contraintes de la table du moniteur
  **lues avant** (domaine `data_quality`, gravité `warning` : acceptés). Jouée comme le moniteur la joue : **0, en 2,9 s**.
- ⚠ **Elle est active au prochain passage du moniteur** (il lit le dépôt). À pousser.

### 18.5 Ce qui vient
- **Cette nuit** : C4 change les vendeurs de ~19 900 transactions → le déclencheur les recalcule (**~22 s** de plus au push, mesuré) ; demain
  matin : la sentinelle à 0, et « vendeurs sans notre numéro » de 58 550 à ~36.
- Le générateur du patch est dans `phase2/checks/gen_table_des_parties/`.
