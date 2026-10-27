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

## 19. LA FICHE CONTACT MET ~4 s — AUDIT DU REMÈDE *(26/10 après-midi, hors ⑧, lecture seule, rien posé)*

> Frédéric : « il faut que tu audites de nouveau afin d'être sûr que ton correctif soit la bonne idée, qu'il soit compatible avec le reste des mécanismes ».

### 19.1 La cause (mesurée sous SON compte, pas en service_role)
- La fiche lit `app_contact_relations_current?hektor_contact_id=eq.<n°>`. La vue fabrique ce champ par **conversion** (`app_contact_id::text`) dans ses deux branches.
- Sous RLS, une conversion n'est pas « leakproof » : Postgres applique la règle **avant**, sur **toutes** les lignes → lecture complète.
- `app_relation` : règle `is_app_user_active()` **non enveloppée** → appelée **132 879 fois** → **2 175 ms**. `app_affaire_partie` : 274-437 ms.
- ⚠ Mes mesures du matin étaient en service_role (qui ignore la RLS) : 2,8 ms. Mémoire `rls-et-conversion-texte-tuent-l-index`.
- ⚠ La colonne existante `app_relation.hektor_contact_id` porte le numéro **de Hektor** (132 879 sur 132 879) : inutilisable.

### 19.2 Les trois lectures de la vue par l'écran (`api.ts`)
| lecture | filtre | aujourd'hui admin / commercial |
|---|---|---|
| fiche contact (l. 3607) | `hektor_contact_id` | **2 183-3 342 ms / 2 191-2 481 ms** |
| personnes d'un bien (l. 9708, 9825) | `app_dossier_id` | 18-164 ms / 132 ms |
| idem, sans dossier | `hektor_annonce_id` | 100-328 ms / 195-388 ms |

### 19.3 Les remèdes comparés (copies en transaction annulée)
| remède | liens seuls | fiche entière (admin, à chaud) |
|---|---|---|
| aujourd'hui | 2 175 ms | 2 400 ms |
| D — envelopper la règle `(select is_app_user_active())`, rien d'autre | **38 ms** | — |
| D + colonne texte calculée sur `app_affaire_partie` (**le remède léger**) | 38 ms | **82 ms** |
| + colonne texte calculée aussi sur `app_relation` (**complet**) | 0,3 ms | 37 ms |
- **Mêmes lignes** : vue entière comparée par `EXCEPT ALL` dans les deux sens, **0 perdue, 0 en trop**, admin (167 825) **et** commercial (132 866).
- Côté bien : inchangé ou mieux (dossier 18 → 1,7 ms admin).
- Commercial : la règle de `app_affaire_partie` (EXISTS sur le registre, lui-même filtré par `app_mes_biens_portefeuille()`) garde ~130 ms.

### 19.4 Compatibilité — ce que j'ai balayé
| | créer | modifier | supprimer | lire |
|---|---|---|---|---|
| **relation** (`app_relation`) | RPC `app_create_mandant_contact_optimistic`, `app_link_mandant_optimistic` : colonnes **nommées** ; nuit `relation_ledger.py` : `colonnes_poussees()` nommées | worker PATCH champs nommés (l. 16750, 16963, 17005) ; RPC `app_unlink_mandant_optimistic` UPDATE nommé | worker DELETE (l. 20507) ; `delete_local_contact.py` = local | écran (3 lectures) ; `app_contact_activite` (definer) ; doublure `pull_from_supabase --table app_relation` (copie **complète**, pas delta) |
| **transaction → parties** | déclencheur `app_affaire_partie_suivre` : INSERT **nommé** | idem | idem | vue de la fiche ; `app_v_affaire_partie_ecarts` (colonnes nommées) ; descente (copie complète) |
| contact, annonce, recherche, mandat, document, RDV | non touchés | | | |
- Le worker, la nuit et les RPC passent en service_role ou en propriétaire : **la RLS ne les concerne pas**.
- La règle enveloppée a **le même sens** (même utilisateur pour toute la requête) : personne ne voit plus ni moins.
- Une colonne calculée ne peut pas être écrite : tous les écrivains nomment leurs colonnes → aucun ne casse. ⚠ Un futur retour arrière `INSERT … SELECT *` depuis une sauvegarde échouerait (bruyamment) : nommer les colonnes.
- Ajouter la colonne **réécrit** la table : `app_affaire_partie` 20 Mo (< 1 s) ; `app_relation` 94 Mo (verrou de quelques secondes) → raison de ne PAS la faire sur `app_relation`.
- La vue garde ses colonnes, leurs types et ses lignes : **aucun changement d'écran** (pas de conflit avec la session navigation).
- À suivre si posé : le générateur `gen_table_des_parties/` (la branche de la vue) et l'empreinte de la vue dans la répétition du 26/10.

### 19.5 La famille (leçon 9) — NOTÉE, pas décidée
- **~57 règles** du schéma appellent une fonction sans `(select …)`. Les grosses : `app_console_job_log` (372 k lignes), `app_relation`, `app_console_job` (104 k), `app_mandat_register_current` (219 Mo), `app_affaire_console`.
- ⭐ `app_registre_mandats_current` : **7 ms** en service_role, **387 ms** sous le compte de Frédéric → probablement une bonne part des **25 lectures à ~850 ms** au chargement de l'app.
- Hors base : l'agenda (1,5 s) et le fait que l'écran relise le registre 25 fois.

## 20. LE REMÈDE « COMPLET » ÉCRIT ET ÉPROUVÉ *(26/10 après-midi, Frédéric : « non, première idée »)* — **RIEN N'EST POSÉ**

### 20.1 Les fichiers
- `supabase/patch_fiche_contact_vitesse_2026-10-26.sql` : garde (vue à l'empreinte `84ca1b2e`, celle de 13:21) → colonne `app_contact_id_texte`
  **calculée par la base** + index, sur `app_relation` **et** `app_affaire_partie` → règle des liens enveloppée → la vue lit les deux colonnes
  (deux ancres, chacune trouvée une seule fois) → 6 contrôles. `lock_timeout 5 s` : si la table est occupée, il s'arrête au lieu de bloquer.
- `…_INVERSE.sql` : la vue d'abord (reconstituée, **vérifiée à l'octet** `84ca1b2e` avant d'être posée), la règle d'avant, colonnes et index
  retirés ; il ne retire que sa part (4 contrôles, dont « les index d'origine et la table des parties sont intacts »).
- `…_REPETITION.sql` : les temps **sous le compte de l'utilisateur** (Frédéric et un commercial), les deux index dans le plan, le côté bien,
  le témoin inverse, la colonne juste sur chaque ligne, la sentinelle des parties.

### 20.2 L'épreuve — copies temporaires DU MÊME NOM, tout annulé
- Les copies portent le même nom que les tables : Postgres les cherche en premier, donc **le patch tourne tel quel** sur elles.
  ⚠ Piège attrapé : la définition de la vue doit être lue **avant** de créer les copies, sinon Postgres l'écrit avec `public.` et la vue de
  copie lit les VRAIES tables (empreinte `c02fca1c` au lieu de `84ca1b2e` : c'est ce qui l'a montré).
- **Patch** : 6/6 ; 2,5 s sur une copie de même taille (la vraie table sera bloquée de l'ordre de quelques secondes).
- **Rejoué deux fois** : la 2e ne refait rien. **Inverse** : 4/4, la vue revient à l'octet. **Patch après l'inverse** : même empreinte `d4350c63`.
- **Répétition** : fiche **36,7 ms** (admin, contre ~2 400) et **129,3 ms** (commercial, contre ~2 200) ; les deux index servent ; témoin
  inverse : sans les colonnes, 241,9 et 303,3 ms (la vue d'avant profite aussi de la règle enveloppée) ; côté bien 1,8 à 165 ms.
- **Mêmes lignes** : vue entière avant/après, `EXCEPT ALL` dans les deux sens, admin 167 825 et commercial 132 866 : **0 perdue, 0 en trop**.
- **Les écrivains** : création de lien avec la liste de colonnes des RPC, upsert à la façon de la nuit (le numéro change → la colonne suit),
  retrait façon worker, parties façon déclencheur (101 justes, 0 fausse) ; **écrire dans la colonne est refusé** par Postgres.
- ⚠ Deux faux rouges de MA répétition, corrigés : `EXECUTE … INTO` ne garde que la 1ʳᵉ ligne d'un plan texte (lu désormais dans le JSON) ; et le
  témoin attendait « > 500 ms » alors que la règle enveloppée accélère aussi l'ancienne vue.

### 20.3 Pour la pose (accord de Frédéric)
- En journée, **jamais pendant le run de nuit** ; coller le patch, puis la répétition. En cas de souci : l'inverse.
- Ensuite : mettre à jour la branche de la vue dans `phase2/checks/gen_table_des_parties/` (sinon un patch régénéré remettrait la conversion),
  et noter la nouvelle empreinte de la vue (`d4350c63`) pour les gardes des patchs suivants.
- Les index sur expression d'origine (`idx_app_relation_contact_texte`, `idx_app_affaire_partie_contact_texte`) deviennent inutiles :
  laissés en place (additif) ; leur retrait se décidera à part.

## 21. ✅ LE REMÈDE DE LA FICHE CONTACT EST POSÉ — 26/10 vers 14:45 *(Frédéric : « applique toi-même … maintenant, puis la répétition »)*
- **Patch** : 6/6 (liens 132 879 lignes et parties 116 932 lignes, colonne juste partout ; vue `d4350c63`).
- **Répétition** sous les comptes réels : 14/14 — fiche **36,4 ms** (Frédéric) et **131,1 ms** (commercial), les deux index servent,
  côté bien 1,8 à 159 ms, témoin inverse 236,8 / 296,3 ms sans les colonnes, sentinelle des parties à 0.
- **Preuve dans l'app (Chrome de Frédéric)** : la lecture des liens de la fiche passe de **3 964 / 3 964 / 7 030 ms** (matin) à
  **510 / 716 / 90 ms**. Les deux premières tombent pendant le chargement, au milieu des **25 lectures du registre des mandats**
  (toujours ~820 ms chacune — c'est désormais ce qui pèse, voir §19.5).
- ⚠ **ORDRE DES RETOURS ARRIÈRE** : l'inverse de la table des parties vérifie l'empreinte de la vue (`acf77be8` après retrait de sa
  branche) ; il **refusera** de tourner tant que ce patch est posé (sans rien écrire). Pour défaire les deux : d'abord
  `patch_fiche_contact_vitesse_2026-10-26_INVERSE.sql`, ensuite celui des parties.
- La nouvelle empreinte de la vue est **`d4350c63`** : tout patch futur de cette vue part de là. Le générateur
  `phase2/checks/gen_table_des_parties/` est historique (avertissement dans son LISEZMOI).
- ⏰ La nuit : la répétition est à rejouer demain matin (contrôle 21 : la colonne des parties reste juste après le recalcul de C4).

## 22. LES 25 LECTURES DU REGISTRE DES MANDATS À L'OUVERTURE — AUDIT *(26/10 fin d'après-midi, hors ⑧, lecture seule, rien codé)*

> Frédéric : « vérifie pourquoi 25 relectures » → « c'est nécessaire ou il y a une autre méthode ? pourquoi que le registre des mandats ? » →
> « ok vas-y, bonne chose » (audit de la méthode « catalogue complet »).

### 22.1 Ce qui se passe
- `bootstrapApp` (`App.tsx:13943`) lance en parallèle `loadFilterCatalog` et `loadMandatFilterCatalog` puis **fusionne** (`mergeCatalog`).
- `loadFilterCatalog` (`api.ts:5992`), pour un admin : **une** lecture du catalogue préparé la nuit (`app_filter_catalog_current`).
- `loadMandatFilterCatalog` (`api.ts:5937`) : relit **tout** `app_registre_mandats_current` par pages de 1 000, l'une après l'autre —
  **24 576 lignes = 25 lectures** (~820 ms chacune, dont ~380 ms de règle RLS non enveloppée), pour **~90 valeurs**. Depuis le 07/04 (1er commit).
- **Pourquoi le registre** : le catalogue de la nuit (`export_app_payload.build_filter_catalog_from_db`, poussé par
  `push_upgrade_to_supabase.py:1688`, « tout effacer puis tout réinsérer ») ne porte que **7 types** tirés des **biens vivants**. Il n'a
  **aucune agence (0/28), aucun statut (0/10), aucune validation (0/2)**, et il lui manque **7 anciens négociateurs** (biens vendus/clos).
  Le registre est le seul endroit qui porte tous les mandats.
- ⚠ **La liste des agences ne sert pas qu'aux filtres** : c'est aussi la liste « Agence » du **formulaire de création d'annonce**
  (`App.tsx:20270`, 20408) et la reconnaissance de l'agence d'une fiche scannée (`App.tsx:16148`). Elle ne vient QUE de ces 25 lectures ;
  si elles échouent, `.catch(() => null)` se tait et la liste est vide.
- **Négociateurs** : la règle de `app_mandat_register_current` (`is_app_manager_or_admin()`) ne leur montre **aucune** ligne ; leur
  catalogue vient d'une autre branche (leurs biens et leurs travaux, par pages). Les 25 lectures ne concernent que les **admins**
  (4 actifs). Aucun utilisateur n'a de périmètre « agence » aujourd'hui (tous `reseau`).

### 22.2 Deux méthodes pour le même résultat
| | **N — la nuit complète le catalogue** | **D — le catalogue calcule les valeurs du registre à la lecture** |
|---|---|---|
| lecture à l'ouverture | ~1 ms | **84 ms** admin, **2 ms** commercial (mesuré, une seule lecture, copie avec règle enveloppée) |
| fraîcheur | le lendemain | **toujours à jour** |
| à toucher | la nuit (push du catalogue) + base + écran | **base** (vue du catalogue + règle du registre enveloppée) + écran |
| risque propre | le catalogue est effacé puis réinséré chaque nuit : un raté = liste des agences vide dans le formulaire de création | la règle du registre change de forme (même sens) |
| bonus | — | l'écran Registre (ses propres lectures par pages, `loadMandatRegisterStats`) profite aussi de la règle enveloppée |
- Sans la règle enveloppée, D coûte **2,2 s** (mesuré) : elle en fait partie.
- Plancher sans règle : 112 ms en un passage (service_role).

### 22.3 Ce que ça pourrait casser (les deux)
- **L'écran change dans les deux cas** (`api.ts` : lire les types agence / statut / validation du catalogue — `statuts: []` y est écrit en dur —
  et ne plus appeler `loadMandatFilterCatalog` pour un admin) : c'est le terrain de la **session navigation** → à coordonner ; Vercel se déploie au push.
- **Mêmes listes exigées** : union d'aujourd'hui = catalogue ∪ registre (trim, tri `fr`) ; à prouver valeur par valeur avant/après,
  agences du formulaire comprises (avec leurs anciens noms, « Agences supprimée » compris : on ne trie pas, on reproduit).
- Garder un **repli** : si le catalogue ne rend aucune agence, relire comme aujourd'hui (jamais une liste vide en silence).
- La vue du catalogue a une bascule store / v1 (`app_delta_run`) : la branche du registre doit vivre en dehors.
- Les écrivains du registre (nuit, worker, RPC) passent en service_role ou propriétaire : la règle ne les concerne pas.

### 22.4 Correction de mon point sur ⑧ (journal git)
R2 **fait et allumé** (25/10 20:40 ; allumé 26/10 06:39), R4 **posé** (26/10 07:01-07:09, 2 sentinelles), R5 **rangé à l'étape 3**
(décision B, 26/10 07:32). Ma mémoire de reprise était en retard sur le code.

## 23. LE « CHOIX 1 » ÉCRIT ET ÉPROUVÉ — les menus du registre en UNE lecture *(26/10 soir, Frédéric : « ok fais choix 1, et mets le choix 3 dans l'étape 3 »)* — **RIEN N'EST POSÉ NI POUSSÉ**

### 23.1 Les pièces
- **Base** — `supabase/patch_catalogue_registre_une_lecture_2026-10-26.sql` (+ `_INVERSE`) : la règle du registre enveloppée
  `(select is_app_manager_or_admin())` (même sens) ; une vue **neuve** `app_filter_catalog_registre` (security_invoker) qui rend les
  valeurs **brutes et distinctes** (négociateur, agence, statut, validation, diffusion, portails) ; 3 contrôles. ⛔ Aucune donnée touchée.
- **Écran** — `api.ts` : `CATALOGUE_REGISTRE_EN_UNE_LECTURE = true` et `lireCatalogueDuRegistreEnUneLecture()`, appelée par
  `loadMandatFilterCatalog` **pour un admin seulement** (sans périmètre). Le nettoyage est le MÊME `uniqSorted` qu'avant. **Repli** : si la
  vue manque, échoue ou ne rend aucune agence → l'ancienne lecture par pages, avec un avertissement en console. Négociateur : inchangé.
  `npm run build` vert ; CRLF conservés (+46 lignes).
- **Répétition** — `phase2/checks/comparer_catalogue_registre.mjs . --vue` (après la pose).

### 23.2 L'épreuve
- Vue jouée **dans une transaction annulée**, sous le compte de Frédéric : **137 ms, 93 valeurs** ; commercial : 37 ms, 0 valeur (comme aujourd'hui).
- **Comparaison** ancienne lecture (25 pages, code recopié de `api.ts`) contre nouvelle (valeurs de la vue, même code) :
  **les 7 listes IDENTIQUES, contenu ET ordre** — négociateurs 44, agences 28, statuts 10, validation 2, diffusion 2, portails 5, erreurs 2.
- **Témoin inverse** : une agence retirée (« FIRMINY ») → « DIFFERENT », sortie 1.
- ⚠ Valeurs brutes exprès : les portails arrivent avec des espaces (« etreproprio » et «  etreproprio ») ; c'est le trim JavaScript qui les
  fusionne, comme avant. Un `btrim` SQL n'aurait pas retiré les mêmes caractères.

### 23.3 L'ordre de la pose (à l'accord de Frédéric)
- **L'écran peut partir AVANT la base** : sans la vue, la lecture échoue et le repli refait les 25 pages — rien ne change.
- Ensuite coller le patch (instantané : une règle et une vue), puis `node phase2/checks/comparer_catalogue_registre.mjs . --vue` → 0 écart ;
  puis, dans l'app, le chargement doit ne montrer **qu'une** lecture `app_filter_catalog_registre` et plus les 25 pages.

### 23.4 Le choix 3 dans l'étape 3
- Le chapitre **CH26** existait déjà : « L'annuaire des négociateurs et des agences devient le nôtre » (`L10-11-c`) — mais il ne parlait que
  de créer un collaborateur. **Étape 5 ajoutée** (`notice/CHAPITRES_AUTONOMIE_PROPOSITION_2026-10-07.md`) : les menus Agence et Négociateur
  tirés de nos annuaires, la correspondance des anciens noms d'agence, la remise à jour des annuaires (agences 29/05, rattachements 07/09).
  Ligne ajoutée sous le chapitre 26 dans `notice/PLAN_DEV_ACTUALISE_2026-08-20.md`.

## 24. ✅ LE CHOIX 1 EST POSÉ EN BASE — 26/10 au soir *(Frédéric : « applique toi-même … puis la comparaison --vue ; je pousse ensuite »)*
- **Patch** : 3/3 — règle du registre enveloppée ; vue `app_filter_catalog_registre` (agence 28 · commercial 44 · diffusable 2 · passerelle 7
  valeurs brutes → 5 après nettoyage · statut 10 · validation 2).
- **Comparaison sur la vraie vue** (`comparer_catalogue_registre.mjs . --vue`) : **les 7 listes IDENTIQUES**, sortie 0.
- **Sous le compte de Frédéric** : la vue en **135 ms** (commercial 46 ms, 0 valeur) ; une page de 1 000 lignes du registre en **39 ms**
  (≈ 390 ms avant : la règle enveloppée sert aussi l'écran Registre).
- ⏳ **L'écran n'est pas encore en ligne** : il le sera au push de Frédéric (Vercel). Jusque-là, rien ne lit la vue.
  ⏰ Après le push : ouvrir l'app et vérifier qu'au chargement il n'y a **qu'une** lecture `app_filter_catalog_registre` et plus les 25 pages.

## 25. ✅ PROUVÉ DANS L'APP — 26/10, 16:57 *(Frédéric : « j'ai push » ; Vercel sert `index-CFC0e0A4.js` depuis 16:56:57)*
- **Avant le déploiement de l'écran** (base seule) : toujours 25 lectures du registre, mais **60 à 170 ms** chacune au lieu de ~820 (la règle enveloppée).
- **Après** : au chargement, **0 lecture du registre** pour les menus ; la lecture unique `app_filter_catalog_registre` en **502 / 679 ms**
  (lancée deux fois au démarrage, comme la fiche) ; **aucun repli** (pas d'avertissement en console).
- **Les menus à l'écran Annonces** (panneau « Filtres ») : Agence **28** · Négociateur **49** (registre 44 ∪ catalogue de nuit, comme avant) ·
  Statut **11** (10 + « actives ») · Validation **2** · Passerelle **5**.
- ⚠ La capture d'écran de Chrome a cessé de répondre (fenêtre en arrière-plan) : la lecture des menus s'est faite dans la page, sans capture.

## 26. ✅ LA PREMIÈRE NUIT EST BONNE — contrôle du 27/10 au matin *(Frédéric : « contrôle les résultats des correctifs »)*

Run quotidien du 27/10 : **04:00:01 → 06:12:28, code 0**. Les bilans écrits par la nuit, puis les répétitions rejouées
par moi en lecture seule.

| chantier | attendu | mesuré | verdict |
|---|---|---|---|
| **1** — l'acheteur « propriétaire depuis la vente » | ~113 liens | bilan **116** (`acheteur_nes_de_la_vente`, 116 posés, 0 levé) ; répétition **9/9** (dont JACQUIER 61730 au 2026-09-25, les 10 vrais mandants intacts, la vue ne dit plus « mandant ») ; la vue rend JACQUIER `proprietaire` + `acquereur_offre/compromis/vente` | ✅ |
| **2 a** — les vendeurs à nos numéros (C4) | ~58 514 posés, ~36 sans | bilan **58 526** ; en base, **58 526 sur 58 562** personnes portent `app_contact_id`, **0** dans la plage Hektor (< 10 M) ; les **36** restantes sont toutes sur **12 transactions absentes de Hektor** (`present_in_hektor = false`) | ✅ — les 36 attendent toujours sa décision |
| **2 c** — notre numéro de mandat | ~23 336 | bilan **23 342** ; répétition **4/4** (même clé bien + numéro, aucune transaction sans numéro servie) | ✅ |
| **la table des parties** | sentinelle à 0 | répétition fiche, contrôles **21** (116 965 lignes justes après le recalcul de C4) et **22** (0 écart) | ✅ |
| **la fiche contact** | < 200 ms admin, < 400 ms commercial | **39,4 ms** / **131,2 ms** (hier 36,4 / 131,1), les deux index servent, témoin inverse 389,7 / 266,7 ms ; répétition **14/14** | ✅ |

⚠ **Un faux rouge, attrapé et expliqué** : au **premier** passage, la fiche admin a mesuré **304 ms** (rouge) et le témoin
inverse s'est dit « à regarder ». Cinq mesures à la suite donnent **274 → 39 → 38 → 38 → 39 ms** : c'est le **cache froid**
de la toute première lecture du matin (la répétition garde la 2ᵉ mesure, qui tombait encore dans le froid). Rejouée
ensuite : 14/14. ➡ La répétition gagnerait à faire **une lecture d'échauffement** avant de mesurer — noté, pas changé.

Durées du push (index adresse posés le 26/10 à 17:00) : **push upgrade 5 min 02** (référence 4 min 05 – 4 min 59, hier
4 min 45 : +3 s au-dessus de la fourchette, sans alerte) · **push contacts 35 s** (référence 32-40 s) · registre des
transactions 1 min 56.

Le moniteur de **04:49** affichait « lignes sans numéro : 549 » et « 1 travail en erreur » : il passe **avant** le push de
05:50 (la vue `app_contacts_sans_numero` vaut **0** après le run) ; l'erreur est la relecture du contact d'essai 20000016,
supprimé le 26/10 (attendue).

**Les autres tâches de la nuit** *(Frédéric : « tu n'as pas vérifié le run de 22 h et de 3 h ? » — avec le changement d'heure,
elles tournent à 21:00 et 02:00)* :
- **entretien des documents** 21:00 → 23:21, les 3 lignes passées : vente 685 balayées / 19 changées / **1 lecture ratée**
  (pas un refus : `arret: null`, l'annonce sera relue au passage suivant) ; estimations 2 000 / 0 ; vendus 2 000 / 0 ;
  **68 travaux posés, 68 terminés, 0 erreur**. Mêmes ordres de grandeur que les 23-25/10.
- **recherches actives** 02:00 → 03:48, **4 000 contacts en 6 502 s**, code 0 (les nuits d'avant : 3 973 à 3 999 en
  6 490-6 625 s). ⚠ **Aucun journal le 25/10** : c'était la nuit du changement d'heure, et le déclencheur est réglé à
  `02:00+01:00` (= 01:00 UTC, l'instant même du recul de 03:00 à 02:00). Nuit sautée, une fois par an ; noté, pas traité.
- **entretien des photos** 20:00 : **12 photos marquées absentes** (63280 : 5, connues chez nous depuis le 14/10 ; 63354 : 7, depuis le
  24/10), 520 masquées épargnées, verrou 8 : 0 sauvée. Aucun geste de l'app sur ces photos (seules deux relectures
  d'ouverture). ⚠ **Non tranché** : retirées pour de bon, ou masquées directement chez Hektor ? Seule une relecture des
  photos de ces deux annonces le dirait (lecture chez Hektor, à son accord).
- **descente** 06:45 → 07:05:54, les 4 pas en code 0 ; 4ᵉ pas (rattrapage du carnet R3) : « rien à poser », 0 ligne en attente.
- **balayage des photos** 23:00 : 1 000 / 1 000 terminés, 0 refus, **0 masquée dans une boîte publique** ; récolte 544
  masquées ; reste 6 519 annonces, ~7 nuits ; seul orange : 63073 (connu).

**⚠⚠ Les 12 photos « absentes » : relues chez Hektor le 27/10 à 07:08 (accord de Frédéric, « oui relis » ; il avait
pensé au masque)** — deux travaux `sync_hektor_photos` (af0ff770 / f3f59d34), file vide avant, `done` en 36 s et 6 s :
- **63354** : Hektor rend 4 visibles + **7 masquées** = nos 7 « absentes », **toutes revenues `présente / masquée`** ;
- **63280** : 8 visibles + **14 masquées** ; 1 des 5 (487757) est revenue masquée, **4 ont vraiment disparu** (487758-61),
  et **13 masquées que nous n'avions jamais** ont été ramenées.
➡ **8 sur 12 étaient MASQUÉES, pas supprimées.**

**La cause** (`Console/accorder_photos_miroir.js` l. 266-292) : l'entretien compare nos photos à la liste de l'API détail,
**qui ne contient que les VISIBLES**. Les verrous 7 et 8 ne protègent qu'une photo que **notre base sait masquée**. Une
photo masquée **directement chez Hektor**, que nous croyions visible, ressemble donc trait pour trait à une supprimée → elle
est marquée absente, sort du panneau de l'app (on ne peut plus la démasquer depuis l'app) et serait perdue à la coupure.
Pas de risque de publication (absente = hors des boîtes publiques). Le balayage la rattrapera quand il passera sur
l'annonce, mais rien ne l'y envoie plus tôt.

**L'ampleur, mesurée** : depuis le 18/10, **106 photos sur 11 annonces vivantes** sont marquées absentes **sans aucune
relecture des deux galeries depuis** — 63306 (54), 59203 (30), 62716 (7), 47929 (5), 63079 (3), 63193 (2), 63028, 62726,
63234, 63304, 61831 (1 chacune). Combien sont masquées : **non mesuré** (il faut les relire, 2 requêtes par annonce).
⬜ **À décider par Frédéric** : relire ces 11 annonces ; et le remède de fond (par exemple : l'entretien ne marque plus
« absente », il pose une relecture des deux galeries de l'annonce — le patron du bouton masquer, qui pose déjà un
`sync_hektor_photos` quand il découvre). Rien n'est codé.

## 27. ÉTAPE 4 (suite) — LES TYPES À LA LECTURE (C6 + C8) : audit du 27/10 *(Frédéric : « ok »)* — lecture seule, rien codé

⭐ **La pièce 5 est déjà faite** : depuis la pose de la table des parties (§18, 26/10 13:21), la vue des liens d'un contact
(`app_contact_relations_current`) lit les acheteurs dans **notre** registre des transactions (35 005 / 35 005). Reste : le **type**.

### 27.1 Où le type est calculé — un seul écrivain
`phase2/contacts/build_contacts_layer.py` (l. 1412-1426, 1771, 1806) : `relation_roles_json` = l'ensemble des `role_contact`
des liens du contact. Il tourne **la nuit** (push des contacts) **et** à chaque relecture d'un contact par le worker
(`refresh_contact_inproc.py`, étapes build + push) — mais il lit le **miroir local** de Hektor, pas nos registres.
Valeurs réelles (62 339 contacts de l'annuaire) : `proprietaire` 25 438 · `mandant` 22 912 · `acquereur_compromis` 11 712 ·
`acquereur_vente` 10 287 · `acquereur_offre` 9 640. ⚠ **Aucun rôle `notaire`** dans les données.

### 27.2 La mesure qui change tout
Le type de nuit, comparé au type **recalculé maintenant** depuis la vue (qui lit `app_relation` + `app_affaire_partie`) :
**62 337 identiques sur 62 339**. Les 2 écarts : un contact archivé (10324835, « mandant » sans lien visible) et 10205503
(« propriétaire » sans lien visible) — restes, sans effet. ➡ **Le calcul de nuit est juste** ; C6 n'est qu'une question
de **délai** dans la journée, pas d'exactitude. ⚠ Le délai lui-même n'est **pas mesuré en réel** : `app_relation` n'a eu
**aucun lien né dans la journée** en 7 jours (il n'est écrit que la nuit), et `app_contact_current.refreshed_at` ne bouge
presque jamais le jour (0 à 1 ligne par jour).

### 27.3 La vitesse, sous le compte de Frédéric
| | type de nuit (colonne) | type à la lecture (vue) |
|---|---|---|
| une page de 50 contacts | — | **12,5 ms** |
| le filtre « Mandants » sur tout l'annuaire | **102 ms** | **957 ms** (×9), sans compter la pagination ni le comptage |
➡ **Tout à la lecture ralentirait les filtres de l'annuaire** (Propriétaires / Mandants / Acheteurs), qui portent sur tout l'annuaire.

### 27.4 C8 — TROIS logiques à l'écran, et un mot à deux sens
| où | logique | les mots |
|---|---|---|
| annuaire du bureau (liste + fiche V2) | `contactDirectoryCategories` (App.tsx ~38932) — cumulables, ordre Mandant > Acheteur > Propriétaire > Acquéreur | **Acheteur** = une transaction ; **Acquéreur** = une **recherche active** |
| téléphone (cartes de la liste) + pastille `ContactTypeMark` | `contactToneFromRoles` (~38902) — un seul ton, « Multi-role » dès deux | **Acquéreur** = une **transaction** ; « Vendeur » / « Propriétaire » ; « Notaire » (jamais atteint) |
| recherche globale | `rolesContact` (RechercheGlobale.tsx:78) | **Acquéreur** = une transaction |
| menu « Rôle contact » des filtres (App.tsx ~23867, ~24557) | valeur `acquereur` = les trois rôles de transaction (api.ts 2551) | « Acquereur » (= transaction) ; « Notaire entree / sortie » : **options mortes** (0 contact) |

### 27.5 Ce que je propose — À TRANCHER PAR FRÉDÉRIC
- **C8, un seul vocabulaire** : une seule fonction (celle de l'annuaire du bureau, issue de la refonte de l'annuaire) lue par
  le téléphone, la pastille, la recherche globale et le menu des filtres. Les mots : **Mandant · Acheteur (transaction) ·
  Propriétaire · Acquéreur (recherche active)**. Écran seulement. Ce que ça touche : les couleurs des cartes du téléphone
  (classe `is-<ton>`), les libellés du menu, les deux options « Notaire » (à retirer ou garder).
- **C6, le type tenu à jour au geste** (pas tout à la lecture) : on garde la colonne de nuit pour les listes et les filtres
  (rapides), et un **déclencheur** recalcule `relation_roles_json` du seul contact touché quand ses liens ou ses parties
  changent — le même calcul que la vue, donc le même résultat que la nuit (62 337 / 62 339). Base seulement, additif,
  derrière un interrupteur ; la nuit continue de tout refaire. À éprouver dans une transaction annulée avant la pose.
- **Ou laisser C6** : le type est juste, il a au pire un jour de retard.

### 27.6 « Le registre des relations doit réagir tout de suite chez nous, la nuit confirme » *(Frédéric, 27/10)* — audit des gestes

⛔ **Je me corrige** : au §27.2 j'ai écrit que `app_relation` « n'est écrit que la nuit ». **C'est faux.** Trois portes l'écrivent
**au clic** depuis le 03/10 (lecture du code en base, 27/10) : `app_link_mandant_optimistic`, `app_create_mandant_contact_optimistic`,
`app_unlink_mandant_optimistic`. Ma mesure ne voyait rien parce que ces gestes sont rares (**8 en 30 jours**, tous `done`) et que la
nuit reprend ensuite la ligne à son compte (il ne reste qu'**une** ligne `source = 'app'`).

**Le tableau, objet « relation »** (la règle : chez nous au clic, Hektor confirme) :

| geste | au clic, chez nous | quand Hektor répond | la nuit |
|---|---|---|---|
| lier un mandant existant | ✅ ligne posée (`present_in_hektor = false`) + ligne provisoire | ✅ le worker la marque **établie** (`relation_etablie`) ou la **défait** si refus (`annulerRattachementOptimiste`) | confirme |
| créer un mandant neuf | ✅ idem | ✅ idem | confirme |
| retirer un mandant | ✅ `retire_le` posé | ✅ **défait** si Hektor refuse (`annulerRetraitOptimiste`) | confirme |
| supprimer un contact | — | ✅ ses liens effacés des deux côtés (exception assumée au « jamais supprimer ») | — |
| acheteur d'une offre / d'un compromis / d'une vente | ✅ registre des transactions → table des parties (déclencheur) | ✅ | confirme |
| ⚠ mandants posés **à la création d'une annonce** / au n° de mandat automatique | ❌ **rien au clic** : la liste part au worker, qui lie chez Hektor ; le lien n'arrive chez nous qu'**à la nuit** | — | pose | 
| ⚠ l'acheteur devient « **propriétaire depuis la vente** » | ❌ **la nuit seulement** (règle du chantier 1, `regle_acheteur_proprietaire`) | — | pose |
| ❌ supprimer une vente | ne retire pas l'acheteur-propriétaire (C10) | — | — |
| ⚠ **le type** (l'étiquette de l'annuaire et ses filtres) | ❌ la nuit, ou à la relecture du contact par le worker | — | recalcule |
| lire | ✅ la fiche lit nos deux registres (vue) | | |

Usage mesuré (60 jours) : 5 créations d'annonce par l'app (aucune avec mandant), 5 rattachements, 3 retraits, 1 mandant créé.

### 27.7 La proposition révisée — À TRANCHER PAR FRÉDÉRIC
Compléter « chez nous d'abord » là où il manque, la nuit restant la **confirmation** :
1. **Le type suit le geste** (C6) : un déclencheur sur `app_relation` et sur la table des parties recalcule l'étiquette du seul contact
   touché (même calcul que la nuit : 62 337 / 62 339 identiques). Couvre d'un coup les rattachements, retraits, mandants neufs et
   transactions. ⚠ À mesurer : ce que le recalcul ajoute au push de nuit (des milliers de contacts touchés).
2. **Les mandants de la création d'annonce au clic** : la création écrit la ligne comme la porte « lier un mandant » (même code, même
   défaite si Hektor refuse). Rare aujourd'hui (0 en 60 jours), mais c'est la porte principale le jour de la coupure.
3. **L'acheteur « propriétaire depuis la vente » au geste** de la vente, et retiré quand la vente est supprimée (C10, C11) — la même
   règle que la nuit, appelée au moment du geste. C'est déjà l'étape 5 du chantier des types (« l'acte et ses effets »).
4. **C8** (les mots) : inchangé, écran seulement.

### 27.8 Les acheteurs « propriétaires depuis la vente » (chantier 1) — ce que la proposition doit garder *(Frédéric, 27/10 : « il ne faut pas casser cela »)*

**Le mécanisme, un seul** (`phase2/contacts/regle_acheteur_proprietaire.py`, interrupteur `APP_RELATION_ACHETEUR_PROPRIETAIRE=1`) :
un lien de propriété est « né de la vente » quand (1) la personne est acquéreur d'une vente du bien, (2) son nom n'est pas dans le texte
Hektor d'un mandat du bien, (3) son nom est connu. ⚠ **Il ne CRÉE pas le lien** : il reclasse un lien « propriétaire » **que Hektor a
lui-même ajouté** (Hektor le fait à chaque vente **depuis le 17/07**). La nuit : `build_contacts_layer.py` (le type) et
`relation_ledger.py` (pose `origine = 'vente'` + `proprietaire_depuis`).

**Mesure du 27/10** (ventes vivantes, couples personne + bien) :

| ventes | acheteurs | « propriétaire depuis la vente » | autre lien | lien retiré | **aucun lien** |
|---|---|---|---|---|---|
| depuis le 17/07 | 95 | **95** ✅ | 0 | 0 | 0 |
| avant le 17/07 | 10 440 | 21 | 12 (dont les 10 vrais mandants) | 24 (le filet) | **10 383** |

- Les **116** (95 + 21) : **116 / 116** ont `proprietaire` **et** `acquereur_vente` dans le type de nuit (8 sont aussi mandants d'un autre
  bien), **116 / 116** sont « propriétaire » dans la vue. Annuaire : **Acheteur + Propriétaire** (type dominant Acheteur, D2).
- ⚠ **Les 10 389 acheteurs des ventes d'avant le 17/07 ne sont PAS propriétaires chez nous** : Hektor ne les avait pas ajoutés, la règle
  n'a donc rien à reclasser. Ils sont « Acheteur » seulement ; le bien montre toujours son **vendeur** (10 376 biens ont encore leurs
  propriétaires d'avant — D3, le vendeur reste mandant en historique). 4 seulement ont été revendus depuis par l'agence ; 970 datent de
  2024 ou après. ➡ **D2 dit « l'acheteur devient propriétaire daté de l'acte », mais n'a été appliqué qu'aux ventes où Hektor l'avait
  fait.** Ce n'est écrit nulle part comme une décision : **à trancher par Frédéric**.

**Ce que la proposition du §27.7 leur fait :**
1. **le type suit le geste** : il recalcule depuis la vue, qui dit déjà « propriétaire » pour les 116 → **rien ne change pour eux**.
   L'essai devra le prouver : les 116 gardent `proprietaire` après recalcul (+ JACQUIER 61730), et un mutant qui ignore `origine`
   doit être attrapé.
2. **les mandants de la création d'annonce** : sans rapport.
3. **l'acheteur propriétaire au geste de la vente** (le seul point qui les touche directement) : la ligne posée au clic doit être
   **identique** à celle de la nuit (même clé contact + bien, `origine = 'vente'`, `proprietaire_depuis` = date de la vente), pour que la
   nuit la **reconnaisse** au lieu d'en créer une seconde ; la même règle (jamais un acheteur nommé dans le texte du mandat) ; et
   « supprimer la vente » ne retire **que** une ligne `origine = 'vente'` — jamais un vrai mandant.

## 28. TOUS LES CONTACTS, TOUS LES TYPES — et l'audit du rattrapage des acheteurs anciens *(27/10, Frédéric : « audit un rattrapage » ; « liste les mécanismes chez nous par type de contact, pense au non qualifié ; il y a 300 000 contacts sur le serveur, pourquoi tu n'en parles pas ? »)* — lecture seule, rien codé

⛔ **Je me corrige encore** : toutes mes mesures du §27 portaient sur les **62 339 contacts de l'annuaire** (ceux qui montent dans l'app).
Le serveur en porte **356 674** (`hektor_contact`, dont **184 201 archivés**). Supabase n'a de **fiche** que pour les 62 339
(`app_contact_current`) ; le registre des relations y porte des liens pour 109 743 contacts.

### 28.1 Qui monte dans l'app — la règle (`build_contacts_layer.py` l. 1780-1785, + l'élargissement console du 11/09)
Un contact monte s'il est **lié à une annonce ACTIVE** ou s'il a une **recherche ACTIVE** (ou s'il est nommé dans une transaction lue à la
console). Tous les autres restent **sur le serveur seulement** : leur fiche existe chez nous (le miroir local, sous notre numéro — 100 %
depuis le 07/10), mais **l'app ne la voit pas**.

### 28.2 Les 356 674 contacts, classés avec la règle de l'annuaire (type dominant ; base locale du 27/10, après la nuit)

| type dominant | dans l'annuaire (actifs + archivés) | serveur seulement (actifs + archivés) | total |
|---|---|---|---|
| **Mandant** | 17 720 + 5 140 = 22 860 | 22 199 + 4 160 = **26 359** | 49 219 |
| **Acheteur** (transaction) | 5 220 + 7 866 = 13 086 | 487 + 834 = 1 321 | 14 407 |
| **Propriétaire** | 12 338 + 9 147 = 21 485 | 15 786 + 8 845 = **24 631** | 46 116 |
| **Acquéreur** (recherche active) | 3 631 | 0 | 3 631 |
| ancien prospect (recherches toutes archivées) | 1 | 48 + 56 084 = **56 132** | 56 133 |
| **NON QUALIFIÉ** (aucun lien, aucune recherche) | 618 + 495 = 1 113 | 94 426 + 91 629 = **186 055** | **187 168** |
| **total** | **62 176** | **294 498** | **356 674** |

Les non qualifiés portent tout de même une **typologie de Hektor** : « acquéreur » 92 225, « partenaire » 88 849, « mandant » 8 047
(mandant chez Hektor, mais aucun bien lié chez nous), « locataire » 3. ⚠ Et les **notaires** : 16 573 + 6 778 rôles « notaire » dans la
table des parties, mais **aucun type « notaire »** (ni dans la vue, ni dans le type de nuit — d'où les options mortes du menu des filtres).

### 28.3 Les mécanismes chez nous, type par type (la règle : chez nous au clic, Hektor confirme, la nuit vérifie)

| type | où il vit chez nous | au clic | la nuit | ce qui manque |
|---|---|---|---|---|
| **Mandant** | registre des relations (`app_relation`) ; le mot se déduit du n° de mandat du bien | ✅ lier, créer, retirer un mandant (3 portes, défaites si Hektor refuse) | recopie + confirme | ❌ mandants posés **à la création d'annonce** / au n° de mandat auto ; ⚠ D1 (« mandant = a signé un mandat ») n'est **pas** la règle du code (« propriétaire d'un bien sous mandat ») ; 26 359 hors de l'app |
| **Propriétaire** | `app_relation` (bien sans mandat) | ✅ mêmes portes | recopie | 24 631 hors de l'app ; un lien n'a pas de « jusqu'à » (C11) : le vendeur reste propriétaire après l'acte |
| **Propriétaire depuis la vente** | `app_relation.origine = 'vente'` + `proprietaire_depuis` | ❌ | ✅ la règle du chantier 1 — **seulement si Hektor a ajouté l'acheteur** (depuis le 17/07) | ❌ au geste de la vente ; ❌ retrait si la vente est supprimée (C10) ; ❌ les 10 389 acheteurs d'avant le 17/07 (§28.4) |
| **Acheteur** | registre des transactions + table des parties | ✅ (R1) | confirme (R2, R3) | — |
| **Acquéreur** (recherche active) | `app_contact_search_current` | ⚠ créer = **passe par Hektor** (recherche provisoire affichée) ; supprimer = archivage daté chez Hektor (témoin 20000008 rouge le 27/10) | recopie | la recherche n'est pas « chez nous d'abord » ; l'auto-archivage RGPD de Hektor (création + 2 ans) ne nous parvient pas |
| **Ancien prospect** | `app_contact_search_current` (archivées) | — | recopie | 56 132 hors de l'app |
| **Notaire** | table des parties (`notaire_vendeur` / `notaire_acquereur`) | ✅ (avec la transaction) | confirme | ❌ **pas de type** : invisible comme tel dans l'annuaire |
| **Non qualifié** | la fiche seule (miroir du serveur) + la typologie de Hektor (`typologies_json`) | — | recopie | ❌ **aucun mécanisme chez nous** ; 186 055 hors de l'app ; la typologie de Hektor n'est lue par aucun type |
| **Le type lui-même** (l'étiquette) | `relation_roles_json`, calculé par la nuit | ❌ | ✅ (juste : 62 337 / 62 339) | ne suit pas le geste (C6) ; 3 logiques à l'écran (C8) |

➡ **Le jour de la coupure** : les 294 498 fiches « serveur seulement » sont chez nous (sur le serveur), mais l'app ne les montre pas.
**Aucune décision écrite** ne dit si elles doivent monter, ni lesquelles. ⬜ **À trancher par Frédéric** (sujet à part, gros : poids de
l'annuaire, droits, RGPD pour les 184 201 archivés).

### 28.4 L'audit du rattrapage — les acheteurs des ventes d'avant le 17/07

**Qui** (ventes vivantes, acheteurs sous notre numéro, sans aucun lien au bien) : **10 389 couples** — 10 139 personnes, 8 774 biens,
8 784 ventes. Toutes les fiches sont dans l'annuaire (elles y montent par la transaction). ⚠ **6 218 fiches sont ARCHIVÉES** (60 %) ;
1 063 fiches sans nom (les fiches « couple » de Hektor) ; 1 606 co-acquéreurs. Par date de vente : avant 2010 **1 413** · 2010-2017
**4 228** · 2018-2021 **2 531** · 2022-2023 **1 247** · depuis 2024 **970**. Biens revendus depuis par l'agence : **4** ; biens
revenus au parc : **8**. 10 376 biens ont encore leurs propriétaires d'avant (le vendeur, D3).

**Pourquoi une écriture en base ne suffit pas** (`phase2/sync/relation_ledger.py`) :
1. la règle de nuit **lève** chaque nuit l'origine « vente » qu'elle ne retrouve pas (`a_lever`) — et elle ne cherche que les liens que
   Hektor a ajoutés : un rattrapage posé une fois serait **défait à la première nuit** ;
2. la vue ne montre un lien inconnu de Hektor que s'il vient de l'app (`source = 'app'`, `absent_depuis` vide) ;
3. le type de nuit (`build_contacts_layer.py`) lit le miroir local, pas `app_relation` : il ne verrait pas le nouveau propriétaire.
➡ Le rattrapage est **une extension de la règle** — « l'acheteur d'une vente vivante est propriétaire depuis la vente, que Hektor l'ait
ajouté ou non » — écrite **une fois** dans `regle_acheteur_proprietaire.py` et lue par ses deux lecteurs, plus la vue.

**Ce que ça pourrait casser ailleurs** :
- **des propriétaires qui ne le sont plus** : un acheteur de 2005 a pu revendre **sans** l'agence ; on n'en sait rien. Plus la vente est
  ancienne, plus le risque est grand (1 413 avant 2010) ;
- **deux propriétaires en même temps** : le vendeur garde son lien (pas de « jusqu'à », C11) → le bien montrerait l'ancien et le nouveau.
  C'est déjà le cas pour les 116 d'aujourd'hui ;
- **les biens revendus par l'agence** (4) : seul le **dernier** acheteur est propriétaire ; l'acheteur précédent est devenu vendeur ;
- **l'annuaire** : les comptes « Propriétaires » montent d'environ 10 000 ; les 8 biens revenus au parc rendraient leurs acheteurs « liés à
  une annonce active » ;
- **le registre des mandats** : un acheteur « propriétaire depuis la vente » ne doit pas apparaître parmi les mandants du mandat du vendeur
  (déjà garanti pour les 116 par `origine = 'vente'` — à reprouver) ;
- **Hektor** : rien n'est envoyé (comme pour les 116).

**Les choix — À TRANCHER PAR FRÉDÉRIC** (rien n'est choisi) :
- **A** — ne rien rattraper : les acheteurs anciens restent « Acheteur » ;
- **B** — tout rattraper (10 389), chaque lien daté de sa vente ;
- **C** — rattraper une fenêtre récente (par exemple depuis 2018 : 4 748 ; depuis 2022 : 2 217), là où l'acheteur est très probablement
  encore propriétaire ;
- et dans B ou C : **avant**, poser le « jusqu'à » du vendeur (C11), sinon chaque bien rattrapé montre deux propriétaires.

### 28.5 ⛔ Correction (27/10, question de Frédéric : « pourquoi une date de fin du vendeur ? »)
**Son modèle** : bien sous mandat → le propriétaire est **mandant** ; bien sans mandat → **propriétaire** ; l'acheteur d'une vente →
**propriétaire depuis la vente** ; s'il signe un jour un nouveau mandat sur ce bien → il devient **aussi mandant**, sur une autre période.
C'est exactement D1 + D2 + D3. ➡ **Le « jusqu'à » du vendeur n'est PAS un préalable au rattrapage** : le vendeur reste « Mandant » du mandat
clos (D3, historique) et l'acheteur devient « Propriétaire depuis la vente ». Je retire cette condition du §28.4.
**Ce que le code ne sait pas encore faire de ce modèle** : un seul lien par personne et par bien (clé `app_contact_id + hektor_annonce_id`),
donc **un seul rôle à la fois, sans période**. Quand l'acheteur re-signe, la règle de nuit lève `origine = 'vente'` et **efface la date**
(`a_lever`) : il redevient « mandant » et perd « propriétaire depuis ». Garder les deux périodes demande que le mandant soit rattaché **au
mandat** (ses dates), pas au bien — c'est C2 / D1, à faire plus tard. Sans effet sur le rattrapage.

### 28.6 Les périodes de mandat sur l'annonce (Frédéric, 27/10 : « on avait déterminé des périodes sur les annonces en fonction des dates des mandats ? »)
**Oui, c'est déjà là** : chaque mandat est au registre des mandats (`app_mandat`) avec ses dates (`date_debut`, `date_fin`,
`date_cloture`) — ce sont les « cycles » de mandat de l'annonce (pastilles, fil « Vie du mandat ») ; la tâche 2.7 (16/09) a rattaché
chaque transaction à **son** mandat (cascade : Hektor l'a dit / un seul mandat / la période / le mandant), et depuis le 26/10 au soir
**23 342** transactions portent notre numéro de mandat (`app_mandat_id`, chantier 2 c).
**Ce que ces périodes disent des 10 389** : **8 104** ventes (78 %) sont rattachées à leur mandat ; un mandat **signé après la vente sur la
même annonce** n'existe que pour **79** couples ; dans tout le parc, **53** annonces seulement ont plusieurs mandats distincts.
➡ Une revente passe presque toujours par une **nouvelle annonce** : la période est portée par l'annonce elle-même (annonce A : vendeur
mandant du mandat X, acheteur propriétaire depuis la vente ; annonce B : l'acheteur mandant du mandat Y). La limite « un seul lien par
personne et par annonce » (§28.5) ne touche que ces **79** cas.

### 28.7 ⛔ Correction du §28.6 — les « 79 re-signatures » n'en sont pas (Frédéric, 27/10 : « même numéro, même annonce ? »)
Mesure : sur les 79, le mandat « signé après la vente » porte **le MÊME numéro** que le mandat de la vente (**79 / 79**), sur 58 annonces.
Ce n'est donc **pas un nouveau mandat** : c'est le mandat de la vente, dont la **date de début** est postérieure à la vente — jusqu'à
9 ans (annonce 11659 : vendue le 04/11/2008, mandat 2751 « débuté » le 05/09/2017). Plusieurs portent la même date de début
(16/06/2020) et une fin au 01/01/1970 (date vide). Au registre, 95 mandats commencent le 14/05/2020 et 41 le 16/06/2020 :
**probablement** une ressaisie en masse chez Hektor (hypothèse, non prouvée).
➡ **Zéro re-signature** parmi les 10 389 sur la même annonce : la limite du §28.5 ne mord sur aucun d'eux.
⚠ **Et la leçon pour le rattrapage** : les dates des **vieux** mandats ne sont pas fiables ; la date à retenir pour « propriétaire
depuis » est **la date de la vente**, jamais celle du mandat.

### 28.8 L'explication des mandats « commencés après leur vente » (Frédéric, 27/10 : « retrouve les notes du chantier, sinon il faut la trouver »)
**Les notes du registre des mandats ne l'expliquent pas.** Elles traitent un défaut voisin : les mandats **PROTEXA de 2026**, dont
l'identifiant nu collisionne avec un vieux mandat HEKTOR (`AUDIT_REGISTRE_MANDATS_2026-10-05.md` §12, `CHANTIER_EN_ATTENTE_MANDAT_2026-10-06.md`
partie 2 : « les dates sont PROPRES, ce sont le montant et les mandants qui fuient »). Ici c'est l'inverse : **les mandants sont justes,
ce sont les DATES qui sont fausses**, et sur des mandats HEKTOR anciens.

**Ce que j'ai trouvé** :
- c'est **bien l'ancien mandat** : ses mandants sont **les vendeurs de la vente** (10344 : mandat 3364 = les LACHAIZE, vendeurs du
  02/07/2019 ; 10867 : mandat 1311 = Anne PETIT, vendeuse du 26/04/2016) ;
- la chaîne de la vente est **cohérente** (10344 : offre refusée 23/01/2019, acceptée 24/04, compromis 06/05, vente 02/07/2019) :
  ce sont les **dates du mandat** qui sont fausses, pas celles de la vente ;
- c'est **Hektor** qui les donne ainsi, dans le mandat **et** dans la vente elle-même (`payload_json.mandat`), et notre plus ancienne
  copie (20/05/2026) les portait déjà : le changement date d'**avant** que nous les lisions — nous ne l'avons pas fabriqué ;
- **l'ampleur** : sur **6 784** mandats vendus, **61** (0,9 %) « commencent » après leur vente ; **37** d'entre eux portent l'une des deux
  mêmes dates, **14/05/2020** ou **16/06/2020**, et **40** une fin au 01/01/1970 (date vide). ➡ **Le plus probable** : une opération en
  masse chez Hektor ou à l'agence sur ces deux journées de 2020, qui a réécrit la date de début de vieux mandats (hypothèse, **non
  prouvée** : Hektor ne donne aucune date de modification d'un mandat, et nos archives commencent au 20/05/2026). Les 24 autres sont
  des dates isolées, saisies ou modifiées à la main.

**Ce que ça touche** : l'écran (fil « Vie du mandat », registre) montre un mandat commencé après sa vente pour ces 61 ; la cascade 2.7
(« la période ») ne s'en sert que sur 53 annonces à plusieurs mandats ; **le rattrapage n'est pas touché** s'il prend la date de la
vente (§28.7). ⬜ Signaler ces 61 au registre (« dates incohérentes ») : à décider par Frédéric, rien n'est codé.

### 28.9 ✅ L'EXPLICATION TROUVÉE — les mandats « commencés après leur vente » *(Frédéric, 27/10 : « il faut comprendre pourquoi »)*

**La source qui tranche** : `mandats_extraits.xlsx` (racine du dépôt, 27/02/2026, 26 404 lignes) — un **export du registre des mandats
de Hektor** qui porte, pour chaque fiche, `time_created` (création de la fiche) **et** les dates du mandat **à la seconde**. Notre miroir
ne garde ni l'un ni l'autre (Hektor ne les rend pas par l'API).

**Constat 1 — un numéro de mandat n'est pas unique** : 3364 existe au moins trois fois (2012 « M03364 », 2019, et la fiche de 10344) ;
1311 une douzaine de fois (séries de location « LS… », vente « VM… », ancien préfixe « M0… »). La clé (annonce, numéro) du registre le
savait déjà (§6 de `NOTE_CHAINE_DES_MANDATS_2026-08-25.md`).

**Famille A — 37 mandats : une date posée « à l'instant » sur une fiche ancienne.** Dans l'export, des **séances** remplissent la date
de début avec **l'heure du moment**, sur des fiches **créées avant**, et **sans date de fin** :

| jour | mandats | heures | fiche créée avant | sans fin |
|---|---|---|---|---|
| 14/05/2020 | 88 | 09:08:16 → 10:14:19 | 88 | 88 |
| 16/06/2020 | 37 | 14:17:14 → 14:29:06 | 37 | 36 |
| 02/08/2019 | 26 | 09:07:05 → 09:12:25 | 26 | 26 |
| 24/07/2017 | 21 | 11:38:15 → 11:40:05 | 21 | 21 |
| 03-04/05/2021, 07/08/2020, 05/09/2019 | 15 | | 15 | 15 |

Ex. : mandat 1311 (annonce 10867, fiche créée le 14/07/2015) → 16/06/2020 **14:22:13** ; 1260 → 14:22:19 ; 1152 → 14:22:41.
➡ Ce sont des **séances de ménage** : quelqu'un a repris de vieilles fiches une à une (88 en 66 minutes ≈ 45 s chacune — un rythme
**humain**, pas un script), et **Hektor a rempli la date de début vide avec l'heure de l'enregistrement**. Le mandat d'origine n'avait
**pas de date** (fiches héritées de l'ancien logiciel : clés `c3_main_…`, notes « Numéro : M0xxxx »). Ce n'est donc pas une date fausse
saisie par un humain : c'est **l'absence de date**, comblée par Hektor.

**Famille C — 23 mandats : la fiche de l'ancienne annonce porte le mandat SUIVANT.** Prouvé sur **11659** : vendue le 04/11/2008
(acheteur Henri ROLAND) ; le bien est remis en vente en 2017 sous une **nouvelle** annonce 10483, mandat 2751 du 05/09/2017 (vendue aux
GAVOT le 28/06/2018). Dans l'export, la fiche de mandat de 11659 a été **créée le 22/05/2008** mais porte **le numéro, les dates et le
commentaire du mandat de 2017** (« Mr et Mme DAUPHIN… ») : l'ancien mandat a été **réécrit** par le nouveau. C'est le cas « l'acheteur
re-signe » de Frédéric — mais **sur une autre annonce**, et Hektor a écrasé l'ancienne fiche au lieu de la garder.
Les 22 autres : même signature (fiche créée avec l'annonce, dates déplacées des années plus tard, souvent début + 2 ans), mais **pas de
jumeau** dans notre registre — l'annonce de la revente n'est pas chez nous (brouillon, supprimée, ou hors de notre miroir). Non prouvé
un par un.

⚠ `time_modified` vaut **2025-03-04 12:42:02** sur 23 184 lignes : une opération globale chez Hektor ; elle ne date pas les réécritures.
⚠ Notre app n'y est pour rien : sur ces 61 annonces, **seuls** 67 travaux de **lecture** de documents (17/08 → 19/10/2026), et toutes les
dates sont antérieures au projet.

**Ce que ça change** :
- pour le **rattrapage** : la date « propriétaire depuis » est **la date de la vente**, jamais celle du mandat (confirmé) ;
- pour la **coupure** : notre registre ne connaît d'un mandat que **l'état final** de sa fiche Hektor ; l'historique (le mandat d'origine
  de 11659) n'existe que dans des exports comme celui-ci. ⬜ Garder cet export comme pièce du registre : à décider ;
- pour l'**écran** : 61 mandats affichent une période impossible — ⬜ les signaler (« date reprise par Hektor le … ») : à décider.

### 28.10 « Est-ce NOUS qui avons commis cette erreur en intégrant les corrections du classeur ? » — NON, prouvé (27/10)
⚠ **Correction du §28.9** : `mandats_extraits.xlsx` n'est **pas** un export de Hektor : c'est l'export de **l'ancien logiciel, Modelo**
(`phase2/sync/reparer_nature_depuis_sources_legales.py` l. 88 : « mandats_extraits.xlsx -> l'ANCIEN LOGICIEL, que Frederic appelle Modelo »).
1. **Les deux sources disent la même chose** : pour les 61, la fiche Modelo du **même produit** (`NO_DOSSIER` de l'annonce =
   `linked_product_ref`) et du même numéro porte **la même date de début que Hektor — 61 sur 61** (à un jour près pour le fuseau de Modelo,
   qui range minuit en UTC). Ni l'un ni l'autre n'a de « bonne » date à opposer à l'autre.
2. **Les dates sont plus anciennes que nos écritures** : posées entre 2017 et 2021 (séances datées à la seconde), déjà présentes dans
   l'export Modelo du 27/02/2026 et dans notre première lecture de Hektor du 20/05/2026 ; le dépôt commence le 07/04/2026.
3. **Notre registre ne les a pas modifiées** : sur les 61, **54** viennent du détail Hektor sans aucune marque de nos scripts ; **7**
   portent `source_app = 'modelo'`, posé par `reparer_nature_depuis_sources_legales.py` (16/10), qui n'écrit **que** `nature_app`,
   `type_app`, `source_app` — jamais une date (UPDATE l. 197 et 309).
4. **Les scripts qui ont lu les classeurs ne pouvaient pas les toucher** : `importer_mandats_vente_absents.py` n'insère que des couples
   (annonce, numéro) **libres**, avec `present_in_hektor = 0`, et refuse un écart de date de plus d'un an ; `importer_mandats_recherche.py`
   ne traite que des mandats **sans bien** ; `manual_mandat_corrections.py` (liste de février 2026) ne pose un mandat **que si l'annonce
   n'en a aucun**.
5. **Rien n'a été écrit chez Hektor** sur ces 61 annonces : leurs seuls travaux sont 67 **lectures** de documents.
➡ **Ce n'est pas nous.** Les dates fausses étaient déjà dans les deux logiciels avant le projet.

### 28.11 ✅ L'ANCIEN REGISTRE DES MANDATS — les vraies dates (27/10, classeur déposé par Frédéric)
**Le fichier** : `Ancien registre des mandat.csv` (racine du dépôt, = `Downloads\export.csv`, daté du 20/12/2024 ; UTF-16, tabulations,
champs sur plusieurs lignes ; ⛔ **données personnelles : jamais dans git**). C'est le **registre légal** : 8 441 mandats, numéros
**9001 à 17441**, uniques et chronologiques, du **15/12/2014 au 19/12/2024** (1ʳᵉ ligne : « mandat annulé cause essai nouveau logiciel »).
Colonnes : numéro · date · mandants · type · bien · observations. Lecteur d'essai : `scratchpad/chercher_registre.py` (nom du mandant +
commune du bien, sans accents).

**Résultat sur les 61** : **37 retrouvés** (16 par le même numéro, 21 par le nom), **24 introuvables** — 8 vendus **avant** le début du
registre (2007-2014), et des numéros Hektor « courts » d'agences (Brioude 1399-2487, Monistrol 433-2415, Ambert 985-1311…) qui ne sont
**pas** les numéros du registre légal.

**Famille A (début Hektor = 16/06/2020) : le registre donne la VRAIE date, toujours AVANT la vente** — 12 mandats au même numéro :

| annonce | n° | registre | vente | Hektor |
|---|---|---|---|---|
| 26204 | 9026 | **19/12/2014** | 06/05/2015 | 16/06/2020 |
| 20246 | 9574 | **07/07/2015** | 23/10/2015 | 16/06/2020 |
| 20219 | 9936 | **03/12/2015** | 04/07/2016 | 16/06/2020 |
| 46086 | 9959 | **09/12/2015** | 11/03/2016 | 16/06/2020 |
| 20217 | 10006 | **05/01/2016** | 21/11/2016 | 16/06/2020 |
| 20216 | 10202 | **24/02/2016** | 11/01/2017 | 16/06/2020 |
| 20139 | 11080 | **14/02/2017** | 04/07/2017 | 16/06/2020 |
| 25339 | 11398 | **16/06/2017** | 03/10/2017 | 16/06/2020 |
| 44870 | 11463 | **11/07/2017** | 07/12/2017 | 16/06/2020 |
| 52810 | 11480 | **19/07/2017** | 28/02/2018 | 16/06/2020 |
| 52077 | 11485 | **22/07/2017** | 06/11/2017 | 16/06/2020 |
| 51421 | 11886 | **23/02/2018** | 13/06/2018 | 16/06/2020 |

➡ **Le registre a raison, Hektor (et Modelo) ont perdu la date d'origine** lors de la séance du 16/06/2020 (§28.9). Les mandants et le
bien concordent sur les 12 (même nom, même adresse).

**Famille C (date isolée après la vente) : la date de Hektor est celle d'un NOUVEAU mandat inscrit au registre après la vente**, sur le
même bien et pour les mêmes mandants, sous un **autre** numéro — Hektor a gardé l'**ancien** numéro et pris la **nouvelle** date :

| annonce | n° Hektor | vente | nouveau mandat au registre | Hektor |
|---|---|---|---|---|
| 10376 | 3239 | 06/06/2020 | **n° 13767 du 10/08/2021** (Arlanc, LEGUILLIEZ) | 09/08/2021 |
| 10447 | 2962 | 11/10/2019 | **n° 14446 du 26/03/2022** (Marat, NANINCK) | 26/03/2022 |
| 10414 | 3110 | 31/03/2020 | n° 14638 du 14/05/2022, puis **n° 15914 du 14/06/2023** (Ambert, FOUGEROUSE) | 13/06/2023 |
| 45119 | 9711 | 12/02/2016 | **n° 15793 du 02/05/2023** (Saint-Bonnet, MARDUEL) | 01/05/2023 |
| 9823 | 4208 | 19/10/2021 | **n° 16354 du 20/10/2023** (Beurières, COULOMB) | 19/10/2023 |
| 9626 | 14087 | 18/07/2022 | n° **14087 du 19/11/2021** (l'original, AVANT la vente) puis **n° 16445 du 21/11/2023** (Églisolles, DELORME) | 21/11/2023 |

(un jour d'écart = le fuseau). ➡ Le bien **est revenu** avec un nouveau mandat ; au lieu d'en créer un, la fiche de l'**ancienne**
annonce a été **modifiée** (date seulement). C'est le même geste que 11659 (§28.9), vu sous l'autre angle.

**Deux cas à part** : 50047 (n° 9941, registre **03/12/2015** = Hektor ; la « vente » du 17/05/2010 est une vente **antérieure** du même
bien, sur une annonce **réutilisée** — 2 ventes au registre des transactions) ; 54715 (n° 16884, registre **07/05/2024** = Hektor ; c'est
la **vente** du 28/01/2024 qui est fausse : antérieure au mandat et à la création de l'annonce).

**Ce que ça change** :
- le **rattrapage** prend la date de la **vente** : non touché ;
- ⭐ **notre registre des mandats peut porter les 12 vraies dates** — c'est la question déjà posée le 15/10 pour 6 écarts
  (`PLAN_REGISTRE_MANDATS_RECHERCHE_2026-10-15.md` l. 613 : A `date_debut_app` / B corriger chez Hektor) ; **décision de Frédéric du
  15/10 : « Laisse »**, et « si elles gênent un jour, la voie B est la bonne ». ⬜ À lui de dire si ces 12 changent la réponse ;
- ⬜ le classeur est une **pièce du registre légal** que notre base n'a pas (8 441 mandats datés) : l'importer comme source, ou le garder
  comme référence — à décider.

### 28.12 Le rattrapage doit-il s'appuyer sur NOTRE clé de mandat (`app_mandat_id`) ? *(Frédéric, 27/10)* — vérifié
**Aujourd'hui, non** : la règle du chantier 1 (`regle_acheteur_proprietaire.py`, `charger_textes_des_mandats`) cherche le nom de
l'acheteur dans les textes de **tous** les mandats du bien, retrouvés **par l'annonce** ; elle n'utilise ni le numéro de mandat, ni notre
clé. Et je ne l'avais **pas** prévu dans la proposition du rattrapage.
**Mesure sur les 10 389** (9 305 jugeables : nom connu d'au moins 3 lettres) : **7 131** ventes portent notre clé `app_mandat_id`
(chantier 2 c) ; l'acheteur est nommé dans **le mandat de SA vente** pour **22** d'entre eux (vrais mandants, homonymes de famille, ou
fiche réécrite comme 11659) ; nommé dans un **autre** mandat du bien : **0** — un seul de ces biens porte un second mandat chez nous
(Hektor ne donne que le mandat courant d'une annonce).
➡ **Pour le rattrapage, le résultat est le même** avec ou sans la clé. **Mais la forme doit s'appuyer sur notre clé** :
- le lien « propriétaire depuis la vente » retient **le mandat sous lequel il a acheté** par `app_mandat_id` (jamais le numéro : 3364
  existe trois fois, §28.9) ; un mandat **postérieur** (une autre clé) qui le nomme fera de lui le mandant **de ce mandat-là**, sans
  effacer « propriétaire depuis » — c'est la période que demande Frédéric (§28.5) ;
- les **2 174** ventes jugeables sans notre clé (23 %) gardent le repli par l'annonce, comme aujourd'hui ;
- la **date** reste celle de la vente, jamais celle du mandat (§28.7-28.11).

### 28.13 « Dans la fiche contact, le même bien apparaîtra-t-il deux fois ? » *(Frédéric, 27/10)* — mesuré dans le code et la base, pas vu à l'écran
- La vue rend **une ligne par rôle** : pour JACQUIER, 61730 revient 4 fois (`proprietaire`, `acquereur_offre`, `acquereur_compromis`,
  `acquereur_vente`).
- Les deux fiches contact (V1 l. ~43814, V2 l. ~44537) **dédoublonnent par bien** (« Annonces liées », « Biens & mandats liés ») : le bien
  n'apparaît **qu'une fois** — ✅ pas de doublon.
- ⚠ **Mais elles gardent la PREMIÈRE ligne et jettent les autres rôles**, et l'ordre vient de `loadContactRelations` (api.ts l. ~3603) :
  `order('last_seen_at', desc)`. Ce matin, **116 / 116** affichent « Propriétaire » — **par hasard d'horaire** : le registre des liens a
  tourné à 04:52, après le registre des transactions (04:48:59). Si l'ordre des étapes de nuit changeait, la même fiche afficherait
  « Acquéreur (vente) ». Le rôle d'acheteur du bien n'est montré nulle part dans cette liste.
- ⬜ **Proposition (écran seulement, à son « vas-y »)** : une ligne par bien qui porte **tous** ses rôles, dans un ordre fixe
  (« Propriétaire depuis le … · Acheteur — vente du … »), au lieu du premier venu ; avec les deux colonnes `origine` / `proprietaire_depuis`
  ajoutées à la vue (base).

## 29. LA PROPOSITION COMPLÈTE — l'étape 4 des types, de bout en bout *(27/10, Frédéric : « ok pour ta proposition mais détaille-la de nouveau entièrement »)* — rien codé

**Le but** (Frédéric) : l'app autonome dans les deux sens — **un geste dans l'app est chez nous à l'instant**, **un geste dans Hektor
arrive la nuit** et sert de confirmation ; un seul vocabulaire à l'écran ; « propriétaire depuis la vente » visible, sans nouveau type.
Six pièces, chacune : code → essais (dont témoin inverse) → pose → contrôle ; chacune derrière un interrupteur, avec son retour arrière.

### P1 — Un seul vocabulaire à l'écran (C8) · écran seulement
- **Quoi** : la logique de l'annuaire du bureau (`contactDirectoryCategories`) devient la seule ; elle remplace `contactToneFromRoles`
  (cartes du téléphone l. ~45883, pastille `ContactTypeMark` l. ~39029) et `rolesContact` (`RechercheGlobale.tsx` l. 78).
  Mots : **Mandant · Acheteur** (offre / compromis / vente) **· Propriétaire · Acquéreur** (recherche active). Le menu « Rôle contact »
  (l. ~23867, ~24557) : « Acquereur » → « **Acheteur** » (la valeur filtrée ne change pas : les trois rôles de transaction).
- **À trancher** : les options « Notaire entrée / sortie » du menu ne trouvent **aucun** contact → les retirer, ou les garder pour plus tard.
- **Ce que ça pourrait casser** : les couleurs des cartes du téléphone (classes `is-<ton>`) ; les trois écrans doivent dire la même
  chose qu'avant pour un contact à un seul rôle.
- **Essais** : un essai qui joue les trois anciennes fonctions et la nouvelle sur tous les ensembles de rôles réels (5 rôles, leurs
  combinaisons) ; à l'écran, bureau **et** 390 px. **Retour** : l'interrupteur.

### P2 — La fiche contact : un bien = une ligne avec TOUS ses rôles (§28.13) · base + écran
- **Base** : ajouter à la vue `app_contact_relations_current` les colonnes `origine` et `proprietaire_depuis` (à la fin, la vue garde
  ses 18 colonnes dans le même ordre ; `security_invoker` et l'enveloppe de la règle gardées).
- **Écran** : dans les deux fiches (V1 l. ~43814, V2 l. ~44537), regrouper les lignes d'un même bien au lieu de garder la première ;
  ordre fixe des rôles : Mandant → Propriétaire (« depuis le … ») → Acheteur (étape la plus avancée, date, montant).
- **Ce que ça pourrait casser** : la rubrique Contact d'un bien et les e-mails préremplis lisent la même vue (colonnes en plus, rien de
  retiré) ; le temps de la fiche (39 ms admin / 131 ms commercial ce matin) doit rester dans ses seuils.
- **Essais** : patch + inverse + répétition (la vue d'avant se reconstitue à l'octet, temps sous les comptes réels) ; à l'écran JACQUIER
  (61730), un vendeur, un acheteur en cours. **Retour** : l'inverse de la vue ; l'interrupteur à l'écran.

### P3 — Le type suit le geste (C6) · base seulement
- **Quoi** : un déclencheur sur `app_relation` et sur la table des parties recalcule `relation_roles_json` du **seul** contact touché,
  avec le même calcul que la vue (62 337 / 62 339 identiques au type de nuit). La nuit continue de tout refaire : elle confirme.
- **Ce que ça pourrait casser** : **le temps de la nuit** — le push des 31 113 transactions touche des milliers de contacts ; à mesurer
  dans une transaction annulée avant toute pose (référence : la table des parties a coûté ~22 s). Garde : ne recalculer que si les rôles
  changent ; ne jamais faire échouer l'écriture d'origine.
- **Essais** : transaction annulée (un mandant lié, une offre créée → le type change à l'instant ; le push de nuit rejoué, temps mesuré) ;
  la sentinelle des parties reste à 0. **Retour** : retirer le déclencheur.

### P4 — Les mandants saisis à la création d'une annonce, chez nous au clic · base (+ worker si besoin)
- **Quoi** : `app_create_annonce_job_optimistic` (api.ts l. ~11514) écrit les liens des mandants comme la porte « lier un mandant »
  (`app_link_mandant_optimistic`) : ligne `source = 'app'`, `present_in_hektor = false`, confirmée par le worker (`relation_etablie`)
  ou **défaite** si Hektor refuse.
- **Particularité** : à la création, l'annonce n'a pas encore son numéro Hektor ; or la clé du registre des liens est (contact, annonce
  Hektor). ⚠ **À auditer en détail avant tout code** (la limite est écrite dans `relation_ledger.py` : « le jour où l'app créera un lien
  sur une annonce NÉE DANS L'APP… il faudra basculer la clé »). Usage réel : 0 en 60 jours ; mais c'est la porte principale à la coupure.
- **Retour** : l'interrupteur.

### P5 — L'acheteur « propriétaire depuis la vente » au geste de la vente · base + règle de nuit
- **Quoi** : quand une **vente** est créée dans l'app (`app_change_annonce_status_optimistic`), l'acheteur reçoit tout de suite son lien
  « propriétaire depuis la vente » (origine `vente`, date = **la date de la vente**, et **la clé du mandat de la vente** `app_mandat_id`,
  §28.12) ; **supprimer la vente** retire ce lien — et **uniquement** un lien d'origine `vente`, jamais un vrai mandant (C10).
- **La règle de nuit change** (`regle_acheteur_proprietaire.py`, une seule fois, lue par ses deux lecteurs) : aujourd'hui elle ne
  **reclasse** qu'un lien que Hektor a ajouté, et **lève** chaque nuit ce qu'elle ne retrouve pas (`a_lever`) — elle déferait le lien posé
  au clic. Elle doit reconnaître « l'acheteur d'une vente vivante de notre registre » comme source. Les garde-fous restent : jamais un
  acheteur nommé dans le mandat de **sa** vente (22 cas), jamais une fiche sans nom (1 063).
- **Essais** : transaction annulée puis essai réel sur un bien d'essai (accord). **Retour** : l'interrupteur de la règle.

### P6 — Le rattrapage des acheteurs d'avant le 17/07 · même règle que P5 · ⬜ DÉCISION A / B / C EN ATTENTE
- **Quoi** : la même règle, appliquée aux ventes passées : **A** rien · **B** les 10 389 · **C** une fenêtre (depuis 2018 : 4 748 ;
  depuis 2022 : 2 217). Date = la vente (jamais le mandat : §28.7-28.11). Ancre = notre clé de mandat quand la vente la porte (7 131 /
  9 305), sinon l'annonce.
- **Ce que ça pourrait casser** : des acheteurs anciens qui ont revendu **sans** l'agence deviendraient de faux propriétaires (le risque
  croît avec l'ancienneté) ; le compteur « Propriétaires » monte d'autant ; 6 218 de ces fiches sont archivées (le lien s'y pose quand
  même, la fiche reste archivée) ; le registre des mandats ne doit pas les montrer comme mandants (déjà garanti par `origine`, à reprouver).
- **Essais** : sur une copie, le nombre exact posé, les 10 vrais mandants intacts, JACQUIER intact ; puis la nuit. **Retour** :
  l'interrupteur (la nuit suivante remet à vide, comme le chantier 1).

### L'ordre proposé
**P1** (mots) → **P2** (fiche) → **P3** (type au geste) → **P5 + P6** (une seule règle ; P6 attend la décision) → **P4** (après son audit).
Rien n'est envoyé chez Hektor par aucune pièce.

### 29.1 ✅ P1 CODÉ — un seul vocabulaire *(27/10, Frédéric : « vas-y pour P1 »)* — écran seulement, NON POUSSÉ, PAS VU À L'ÉCRAN
- **Interrupteur** `TYPE_CONTACT_UNIQUE` (App.tsx, avant `contactToneFromRoles` ; le même nom dans `RechercheGlobale.tsx`). Allumé :
  - `contactToneFromRoles` (cartes du téléphone, pastille `ContactTypeMark`) rend le type **dominant** de `contactDirectoryCategories`
    (Mandant > Acheteur > Propriétaire > Acquéreur = recherche active) ; « Mixte » et « Vendeur » disparaissent ;
  - `contactToneLabel` / `contactToneBadgeLabel` : **Acheteur · Propriétaire · Mandant · Acquéreur · Contact** (les mots du bureau) ;
  - `contactDirectoryRoleLabel` (lignes et en-tête des fiches contact) : « Acheteur — offre / compromis / vente », « Propriétaire » ;
  - les deux menus « Rôle contact » : « Acheteur » (la valeur filtrée ne change pas) ;
  - la recherche globale : les mots **et l'ordre** du bureau, plus « Acquéreur » si une recherche est active.
- **Inchangés** : l'annuaire du bureau (la référence) ; les options « Notaire » du menu (en attente de Frédéric) ; les couleurs (mêmes
  classes `is-<ton>` ; « mixed » n'est plus produit, la carte prend la couleur du type dominant).
- **Essai** `apps/hektor-v1/test_type_contact_unique.cjs` : **13 / 13** — les 64 combinaisons des 5 rôles réels × recherche active :
  téléphone, pastille et recherche globale = annuaire du bureau ; JACQUIER « Acheteur » (plus « Mixte ») ; **témoin inverse** : la
  version d'avant était en désaccord (**182** écarts) ; **mutant** (interrupteur à false) : **122** écarts. `npm run build` vert.
- ⚠ **Pas vu à l'écran** : la démonstration (`hektor-mock-bienvu`) n'a aucun contact, et la version réelle locale (`hektor-dist-reel`)
  demande la connexion Google — je ne me connecte pas à la place de Frédéric. À voir après le push : annuaire du bureau (inchangé),
  téléphone 390 px (cartes et pastille), recherche globale, une fiche contact (JACQUIER).
- ⚠ Un contact qui n'a **que** des recherches archivées passait « Recherche » ; il passe « Contact » (l'Acquéreur = recherche ACTIVE).
  Dans l'annuaire : 1 contact.

### 29.2 Les notaires — mesure du 27/10, pour la décision de Frédéric
- Ils **existent** chez nous : la table des parties porte **23 351** rôles de notaire (16 573 côté vendeur, 6 778 côté acquéreur), soit
  **1 768** couples personne + rôle ; **1 521** sont dans l'annuaire, et **1 516** portent chez Hektor la typologie « partenaire ».
  359 ont au moins 10 transactions.
- Mais **aucun type de contact ne les dit** : le type de nuit (`relation_roles_json`) ne lit que les liens au bien (mandant,
  propriétaire) et les acheteurs ; les notaires de la table des parties n'y entrent pas. D'où les deux options « Notaire entrée / sortie »
  du menu, qui ne trouvent **personne**, et la pastille qui les dit « Contact ».
- **Les choix** : **A** retirer les deux options (le menu ne ment plus) ; **B** les garder telles quelles ; **C** faire vivre le type
  « Notaire » : le type lit aussi les notaires de la table des parties (base, même patron que P3) → ~1 500 contacts « Notaire » dans
  l'annuaire, et le filtre marche. ⬜ À trancher.

### 29.3 Le type « Notaire » : où il vit, qui il touche — et le type des contacts du serveur *(27/10, Frédéric : « le type notaire est important, mais où ? ce sont des non qualifiés ? et les contacts du serveur seul ? »)* — lecture seule
**Ce que sont les notaires aujourd'hui** (mesure du 27/10) :
- **1 330 personnes** sont notaires d'au moins une transaction (table des parties : 23 351 rôles). **1 110** sont dans l'annuaire, et
  **1 077** d'entre eux n'y ont **aucun type** : ce sont presque exactement les **1 113 « non qualifiés » de l'annuaire** (§28.2). Ils y
  sont entrés par l'élargissement du 11/09 (`elargir_perimetre_console.py`, raison `console_transaction_party` : 1 083). **220** sont
  restés **sur le serveur seulement** ; 620 sont archivés chez Hektor.
- **Hektor ne connaît pas le mot « notaire »** : 1 304 sur 1 330 portent la typologie « partenaire » (la même que les artisans, les
  diagnostiqueurs…) ; aucun champ métier. **Seul notre registre des transactions sait qu'ils sont notaires**, et il le tient déjà au clic
  (R1) et la nuit (pièce 3 du 25/10 : les notaires sous notre numéro).

**Où le type doit vivre** :
- **pas dans le registre des relations** : il porte les liens **au bien** (mandant, propriétaire) ; un notaire n'est lié qu'à une
  **transaction** — exactement comme l'acheteur ;
- **la source est le registre des transactions** (la table des parties), déjà chez nous ; **le type se calcule depuis elle**, au même
  endroit que « Acheteur » : le calcul de nuit (`build_contacts_layer.py`) et, avec P3, le déclencheur au geste ;
- **l'écran doit s'adapter** (c'est un VRAI nouveau type, contrairement à « propriétaire depuis la vente ») : une catégorie « Notaire » dans
  `contactDirectoryCategories` (son rang dans la priorité, sa couleur, son symbole), un bouton dans les segments de l'annuaire, et les
  options du menu « Rôle contact » qui trouvent enfin quelqu'un (aujourd'hui `notaire_entree` / `notaire_sortie`, mots qui ne
  correspondent à rien : la table des parties dit `notaire_vendeur` / `notaire_acquereur`) ;
- **les 220 du serveur** : l'élargissement lit la **lecture console** (`app_affaire_console`), pas la table des parties. Lui faire lire la
  table des parties les ferait monter — et avec eux tous les autres nommés dans une transaction et absents de l'annuaire : **2 906**
  couples personne + rôle (1 356 acheteurs, 1 303 vendeurs, 247 notaires).

**Le type des contacts restés sur le serveur (294 498)** : il **est calculé**, chaque nuit, par la même fonction, pour les **356 674**
contacts (la table locale `app_contact_current` porte `relation_roles_json` pour tous — c'est elle qui a servi au tableau du §28.2) ;
seuls les **éligibles** sont envoyés à l'app. Ils ont donc leur type sur le serveur, mais l'app ne le voit pas ; et comme aucun geste de
l'app ne peut les toucher, seul la nuit (Hektor) le fait vivre. Le jour où l'un devient éligible (une annonce active, une recherche
active, une transaction), il monte avec son type.

⬜ **À trancher par Frédéric** : (1) faire vivre le type Notaire (base + écran, ~1 330 contacts) ; (2) faire monter les 220 notaires du
serveur — et alors aussi les 2 906 parties absentes ? (3) le sort des 294 498 du serveur reste un sujet à part (§28.3).

## 30. LA FICHE NOTAIRE — maquette v1 *(27/10, Frédéric : « il faut une page contact différente pour ce type ; fais une maquette, sois professionnel ; ce sont des contacts avec qui nous échangeons sur des dossiers en cours ou vendus »)* — rien codé

**Fichier** : `maquettes/fiche-notaire-v1.html` (données **fictives** ; charte bienvu ; serveur de lancement `maquettes`, port 8099).
Vérifiée : bureau 1440 px (aucun débordement) et téléphone 375 px (largeur 375 = page, aucun élément hors écran). Bouton « Origine des
données » : 13 pastilles vertes (existe déjà chez nous) et 5 orange (à créer).

**L'idée** : un notaire n'est ni un vendeur ni un acheteur, c'est un **partenaire de dossiers**. La fiche se lit comme un **tableau de bord
des dossiers communs**, pas comme une fiche client.

| bloc | ce qu'il montre | d'où vient la donnée |
|---|---|---|
| en-tête | nom, étude, type « Notaire », depuis quand, nombre de dossiers, côté vendeur / acquéreur ; Appeler · Écrire · Planifier une signature · **Envoyer un dossier** · ⋯ (Modifier, Archiver, Supprimer) | fiche contact + table des parties |
| 4 chiffres | dossiers en cours · actes dans les 30 jours · ventes signées sur 12 mois (+ honoraires) · délai compromis → acte (contre la médiane agence, **86 j** mesurés) | registre des transactions |
| **À venir** | l'échéancier : fin de rétractation, échéance de la condition de prêt, signatures d'acte, dates à fixer — chacun avec SON geste (prévenir, relancer, ajouter à l'agenda, demander une date) | `date_fin_retractation`, conditions (échéance, point 6 n° 1), `date_acte` |
| **Dossiers en cours** | répartis en 4 étapes (rétractation, conditions, acte fixé, date à fixer) ; par dossier : bien, mandat, négociateur, vendeur → acquéreur, prix, prochaine échéance, **côté** (vendeur, acquéreur, les deux), **confrère** (le notaire d'en face), séquestre, honoraires, pièces | registre (`notaire_mandant_*`, `notaire_acquereur_*`, `sequestre`, `honoraires_*`) |
| **Ventes signées** | 12 mois : date d'acte, bien, côté, prix, honoraires, délai ; export | registre (ventes) |
| L'étude | standard, e-mail, adresse | fiche contact |
| **Interlocuteurs** | notaire, clerc qui suit nos dossiers, formaliste | ⚠ **à créer** (Hektor met parfois plusieurs noms dans UNE fiche « SELARL … ») |
| Avec nous | dossiers par agence ; **confrères fréquents** | calcul sur le registre |
| **Pièces d'un dossier** | liste de contrôle (titre, DDT, état daté du syndic, PV d'AG, taxe foncière, offre de prêt, compromis + preuve SRU, séquestre…) | ⚠ **à créer** (le coffre des documents existe ; la liste par dossier non) |
| Échanges | e-mails, RDV, envois ; note interne | Échanges et agenda existants |

**Anti-perte (règle du projet)** : la fiche actuelle garde toutes ses fonctions — Modifier, Supprimer, Archiver (menu ⋯), Appeler,
Écrire un e-mail, Créer un RDV (« Planifier une signature »), Échanges, Activité, Négociateur, Biens liés (devenus « Dossiers »).
Seul bloc masqué par défaut : **Recherches** (sans objet pour un notaire ; visible s'il en a une).

**Suggestions « métier »** (à arbitrer, aucune n'est décidée) :
1. **L'échéancier est le cœur** : un délai SRU ou une condition de prêt manqués coûtent une vente ; c'est ce que l'agence consulte le matin.
2. **« Envoyer le dossier au notaire » en un geste** : les pièces du coffre de documents, jointes à un e-mail prérempli, tracé dans Échanges.
3. **Relances** : J-7 avant l'acte, fin de rétractation, condition de prêt — par le mécanisme de relances e-mail déjà en place.
4. **La signature dans l'agenda**, l'étude invitée, et la date d'acte du registre mise à jour au même geste.
5. **Le côté et le confrère** : savoir qui appeler (55 % des compromis 2025+ ont le même notaire des deux côtés : 344 sur 628).
6. **Étude ≠ notaire** : une étude a plusieurs notaires et clercs ; à terme une fiche « Étude » et ses interlocuteurs.
7. **Classement des études partenaires** (volume, délai) : utile pour recommander un notaire à un client.
8. **Pas d'archivage automatique** façon particulier : un notaire est un professionnel (RGPD différent).

⬜ **Préalables** (§29.3) : le type « Notaire » doit d'abord exister (base + annuaire) ; la page s'ouvre quand le type dominant est Notaire.

### 30.1 Maquette v2 — dans le style de la fiche contact *(27/10, Frédéric : « un design plus ressemblant au graphisme de la page contact, mais avec les blocs que tu m'as proposés »)* — rien codé

**Fichier** : `maquettes/fiche-notaire-v2.html` (données **fictives**). La v1 reste à côté, pour comparer.

**D'où vient le style** : de la **vraie** fiche contact en production, `ContactDetailPopupV2` (vérifié : `fa-cx-root` est dans le
paquet servi par groupe-gti.vercel.app le 27/10). La feuille `apps/hektor-v1/src/contact-detail-v2.css` est **recopiée telle
quelle** dans la maquette (assemblage par script, sans ses 2 blocs « mode sombre du téléphone »), et la page reprend ses classes
`fa-cx-*` : rail gauche (retour animé, avatar coloré par type, boutons, coordonnées, négociateur et pastilles), bandes de section
avec pastille colorée, cartes blanches arrondies, colonne latérale, fil d'activité, « Qualité de la fiche » repliée.

**La correspondance, bloc par bloc** :

| fiche contact (existe) | fiche notaire (v2) |
|---|---|
| thème de couleur par type (`ty-acq`, `ty-acheteur`, `ty-vendeur`, `ty-mandant`) | **`ty-notaire`**, bleu encre #3b4a8c, et un symbole « balance » dans l'avatar |
| rail : coordonnées | standard de l'étude, ligne directe, e-mail, adresse de l'étude ; **+ Interlocuteurs de l'étude** (à créer) |
| boutons du rail : RDV · Modifier · ⋯ | **Planifier une signature** · **Envoyer un dossier** · Modifier · ⋯ (Ouvrir dans Hektor, Archiver, Supprimer) |
| — | 4 chiffres (dossiers en cours, actes ≤ 30 j, ventes 12 mois + honoraires, délai compromis → acte contre 86 j) |
| Recherche & rapprochement | **masqué** (sans objet ; reviendrait si le notaire en avait une) |
| Biens & mandats liés | **Dossiers en cours** : 4 étapes cliquables, cartes dépliables (côté, confrère, négociateur, prix, échéance, pièces 7/11, puis compromis, rétractation, prêt, séquestre, honoraires, net vendeur, **liste des pièces** et « Envoyer les pièces à l'étude ») |
| colonne « À faire » (relances) | **« À venir »**, même dessin de carte datée : rétractation, signature d'acte, condition de prêt, date à fixer, chacun avec son geste ; « Planifier une signature » |
| — | **Ventes signées · 12 mois** (lignes `fa-cx-lk`, « Vendu », rôle, prix, export) |
| — | **Avec nous** (dossiers par agence, son côté) et **Confrères fréquents** |
| Activité & relation (Fil · Rendez-vous · Échanges) | identique, filtres « Dossiers » et « Envois de pièces » en plus |
| Qualité de la fiche | identique, repliée |

**Vérifié** : bureau 1440 px (aucun débordement, police Fraunces chargée, menu ⋯ fermé par défaut) ; téléphone 375 px (largeur
375 = page ; en une colonne **« À venir » passe AVANT les dossiers**, réglage propre au notaire). Bouton « Origine des données » :
10 blocs « existe », 2 « à créer » (interlocuteurs, liste des pièces).
⚠ **Non couvert** : le mode sombre du téléphone (la vraie fiche en a un, ≤ 1180 px ; les blocs neufs devront l'avoir au codage).
⚠ Vu en passant, **dans la vraie fiche** : sur téléphone le pied « Négociateur » (`fa-cx-foot`, marge −16 px pour 14 px de bord)
dépasse d'**1 px** ; invisible (le panneau coupe), noté, pas touché.

✅ **DÉCIDÉ par Frédéric le 27/10 : « la v2 est la bonne base pour la fiche notaire »** (la v1 reste pour mémoire). Rien n'est codé. Préalable inchangé : le type « Notaire » doit exister (§29.3, décision C encore à prendre).
