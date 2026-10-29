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

## 31. P2 — LA FICHE CONTACT : UN BIEN = UNE LIGNE AVEC TOUS SES RÔLES — audit du 27/10 *(Frédéric : « on reprend par P2 ; commence par l'audit »)* — lecture seule, rien codé

> Audit limité à l'objet **relation** (lire / remonter) dans la fiche contact. Les gestes créer / modifier / supprimer un lien ne
> changent pas avec P2 (P2 n'écrit rien) : non mesurés ici, ils l'ont été au §27.6.

### 31.1 Où ça se passe
- **Une seule fiche affichée** : `ContactDetailPopupV2` (production, vérifié le 27/10 : `fa-cx-root` est dans le paquet servi). La V1
  (`ContactDetailPopupBase`) est le repli de l'interrupteur `VITE_APP_CONTACT_V2_ENABLED`. Les **3** points d'ouverture (fiche
  d'annonce, annuaire du bureau, cartes du téléphone) ouvrent la même fiche avec les mêmes `props.relations`.
- **Le dédoublonnage** : App.tsx l. ~44637 (V2) et l. ~43913 (V1), même code : clé = `app_dossier_id`, sinon `hektor_annonce_id`.
  **On garde la PREMIÈRE ligne du bien et on jette les autres** : leurs rôles, dates et montants ne sont montrés nulle part.
- **L'ordre** vient de `loadContactRelations` (`lib/api.ts` l. 3604) : `order('last_seen_at', desc)`.
  ⛔ **Correction du §28.13** : ce n'est pas « l'horaire de la nuit ». La colonne `last_seen_at` de la vue est du **TEXTE**, sous deux
  formes : `2026-10-27T04:52:00+00:00` (liens du bien) et `2026-10-27 04:48:59+00` (registre des transactions). Le même jour, le
  `T` passe devant l'espace : **le lien du bien (mandant, propriétaire) sort toujours premier**, quel que soit l'ordre des étapes de nuit.
  Et entre les lignes du registre (offre, compromis, vente de la même personne), **les dates sont ÉGALES** : l'ordre est laissé au hasard
  de Postgres.

### 31.2 La mesure (vue `app_contact_relations_current`, 27/10)
167 846 lignes · 109 743 contacts · **148 970 couples personne + bien**. **11 582 couples ont plusieurs lignes** (11 290 contacts), dont
**11 541 avec des rôles différents** et **501** avec un même rôle répété (deux offres, ou un compromis annulé puis un autre).
**11 444 / 11 582 ont des lignes à égalité en tête** : la ligne affichée est tirée au hasard. Aucun couple n'a de clé de bien ambiguë
(0 mélange dossier / sans dossier).

| rôles sur le même bien | couples | ligne affichée aujourd'hui |
|---|---|---|
| offre + compromis + vente | 6 533 | une ligne du registre (mesuré : le compromis) |
| offre + compromis | 2 377 | une ligne du registre |
| compromis + vente | 2 340 | une ligne du registre (mesuré : le compromis) |
| offre + vente | 153 | une ligne du registre (mesuré : l'offre) |
| acheteur + **propriétaire** (les « propriétaires depuis la vente ») | 117 | **Propriétaire** — l'achat est caché |
| acheteur + **mandant** (il a acheté chez nous, puis nous a confié la revente) | 21 | **Mandant** — l'achat est caché |
| un seul rôle répété | 41 | une des lignes |

➡ **Ce que voit le négociateur aujourd'hui** :
- **9 026 acheteurs dont la vente est signée** (6 533 + 2 340 + 153) peuvent voir « Acheteur — compromis » ou « — offre » au lieu de
  « Acheteur — vente », avec la date et le montant de cette étape-là ;
- le sous-titre de la ligne est **l'état BRUT, en anglais** (`relationSub = transaction_state`) : `active`, `cancelled`, `accepted`,
  `refused`, `proposed`, `vente` ; et « annonce liée » pour un mandant ou un propriétaire ;
- 138 biens (117 + 21) cachent le rôle d'acheteur.

### 31.3 Qui lit la vue — ce que deux colonnes de plus pourraient casser
- **Front** : `loadContactRelations` (`select *`, la fiche) ; `loadAnnonceContactInvitees` et `loadAnnonceMandants` (colonnes NOMMÉES →
  intouchés). Le tableau `props.relations` sert aussi au **bon de visite** (photo) et aux **modales** (e-mail, RDV) : P2 ne touche **pas**
  ce tableau, seulement la liste affichée.
- **Base** : `app_contact_activite` (lit `hektor_contact_id`, `role_contact`, `app_dossier_id` → intouchée) ; `app_unlink_mandant_optimistic`
  (la cite en commentaire seulement). **Aucune vue dépendante.** Droits : `authenticated` SELECT ; `security_invoker = true`.
- **Run de nuit** : la vue est dans `VUES_NON_DESCENDUES` (`pull_from_supabase.py` l. 160) → **elle ne descend pas** ; aucun script local
  ne la lit.
- Les deux colonnes existent dans `app_relation` : `origine` (texte) et `proprietaire_depuis` (texte), **116** lignes chacune.

### 31.4 La proposition — À TRANCHER PAR FRÉDÉRIC
**Base** (un patch, son inverse, sa répétition ; à coller avec son accord) : la vue gagne **deux colonnes À LA FIN**, `origine` et
`proprietaire_depuis` (lues dans `app_relation` ; `NULL` pour les lignes du registre). Les 18 colonnes gardent leur ordre, et la vue garde
`security_invoker` et ses droits. Le patch vérifie l'empreinte de la définition actuelle et s'arrête si quelqu'un est passé avant.

**Écran** (interrupteur, V2 **et** V1 par une seule fonction) : une ligne par bien qui porte **tous** ses rôles, dans un ordre fixe :
1. **Mandant** ;
2. **Propriétaire**, « depuis le 25/09/2026 » quand il vient de la vente ;
3. **Acheteur**, une seule étape : **la vente si elle existe, sinon la plus récente** (à égalité de date, compromis avant offre). La
   ligne prend la date et le montant de cette étape, en français : « Vente signée le … », « Compromis du … », « Compromis annulé »,
   « Offre acceptée », « Offre en cours », « Offre refusée ».

La couleur de la ligne suit le premier rôle. Le compteur « N biens » ne change pas (même clé). **Le résultat ne dépend plus de l'ordre
des lignes.** Le sous-titre en anglais disparaît.

**Ce que ça pourrait casser** : rien n'est retiré, ni de la vue ni du tableau. À surveiller :
- le temps de la fiche (39 ms admin / 131 ms commercial ce matin) : deux colonnes sans jointure de plus ;
- la ligne à 375 px avec trois pastilles (le CSS passe déjà à la ligne sous 640 px) ;
- le mode sombre du téléphone ;
- le repli V1.

**Essais** :
- un essai qui **exécute** la vraie fonction (comme `test_type_contact_unique.cjs`) sur JACQUIER (61730), les 16 combinaisons mesurées
  et les répétitions ;
- **témoin inverse** : le même lot mélangé dans un autre ordre doit donner le même résultat, alors que l'ancien code en change ;
- mutant : l'interrupteur éteint doit redonner l'ancien affichage ;
- base : le patch éprouvé dans une transaction annulée, puis la répétition (18 colonnes identiques sur échantillon, 116 non vides, temps) ;
- l'écran, après ton push : bureau et 390 px.

**Questions** :
(1) la règle de l'étape d'acheteur : la vente, sinon la plus récente ?
(2) afficher « Propriétaire depuis le … » (c'est P2 qui le rend visible) ?
(3) une offre refusée ou un compromis annulé : on les montre (en gris) ou on les cache ?

### 31.5 ✅ P2 CODÉ — *(27/10, Frédéric : « vas-y pour P2 : (1) la vente, sinon la plus récente ; (2) oui, afficher « Propriétaire depuis le … » ; (3) montrer l'offre refusée et le compromis annulé, en gris »)* — NON POSÉ, NON POUSSÉ, PAS VU À L'ÉCRAN

**Base** — `supabase/patch_p2_fiche_un_bien_tous_roles_2026-10-27.sql` (+ `_INVERSE`, `_REPETITION`) :
- la vue gagne `origine` et `proprietaire_depuis` **à la fin** ;
- le patch vérifie l'empreinte (`d4350c63…`), utilise des ancres d'une ligne et exige 20 colonnes ;
- l'inverse **recrée** la vue (Postgres ne sait pas retirer une colonne) et exige de retrouver l'empreinte d'avant, les droits (comparés
  **sans ordre**) et le commentaire.

**Éprouvé dans UNE transaction annulée** (pooler, 27/10) : patch → répétition → inverse → contrôle de l'inverse, **11 / 11 verts**.

| contrôle | résultat |
|---|---|
| 18 colonnes inchangées + 2 neuves | OK |
| `security_invoker` et droits gardés | OK |
| la vue d'avant se reconstitue à l'octet | OK |
| mêmes lignes que la vue d'avant, dans les deux sens | OK (116 contacts) |
| fiche de JACQUIER, admin | 26,4 ms |
| fiche de JACQUIER, commercial | 132,3 ms (les deux index texte servis) |
| 116 « nés de la vente » portent origine et date | OK |
| une ligne d'origine « vente » n'est jamais « mandant » | OK |
| JACQUIER propriétaire de 61730 depuis le 2026-09-25 | OK |
| l'inverse rend l'empreinte, les 18 colonnes, les droits et le commentaire d'avant | OK |

Après l'annulation, la base est **intacte** : empreinte `d4350c63…`, 18 colonnes.

- ⚠ **Un premier essai a donné un faux rouge** : l'inverse comparait les droits **dans un ordre fixe**, et une vue recréée les liste dans un
  autre ordre. Corrigé (comparaison triée), puis relancé vert.
- **Avaries volontaires** : une empreinte faussée **arrête** le patch ; une colonne trafiquée **arrête** l'inverse. La base est intacte
  après chacune.

**Écran** — `App.tsx`, interrupteur `FICHE_UN_BIEN_TOUS_ROLES = true` :
- une seule fonction, `regrouperRelationsParBien`, sert les **deux** fiches (V2 en production, et le repli V1) ;
- elle garde **la même clé et le même ordre de biens** que l'ancien dédoublonnage : le i-ème bien reste le i-ème ;
- **pastilles** Mandant · Propriétaire · Acheteur, chacune à la couleur de l'annuaire ; gris = offre refusée ou compromis annulé ;
- **sous-titre** en français : « Propriétaire depuis le 25/09/2026 · Vente signée le 25/09/2026 », « Compromis du … »,
  « Compromis annulé (du …) », « Offre acceptée / en cours / refusée (du …) » ;
- **montant** : celui de l'étape d'acheteur retenue ;
- `props.relations` n'est **pas** touché (bon de visite, modales) ;
- sans le patch de la vue (`origine` absente), tout marche, mais sans la date de propriété ;
- `types.ts` : trois champs optionnels (`relation_key`, `origine`, `proprietaire_depuis`) ; `contact-detail-v2.css` : 2 règles ajoutées ;
- à l'interrupteur éteint, l'ancien code est intact.

**Essai** `apps/hektor-v1/test_fiche_un_bien_tous_roles.cjs` — **21 / 21 verts**. Il exécute le vrai code et contient :
- les 13 cas (JACQUIER, deux offres, compromis annulé, vente puis offre plus récente, mandant + acheteur, même jour, avant le patch…) ;
- la même suite de biens que l'ancien code, ligne sans clé comprise ;
- **témoin inverse** sur 44 ordres : le nouveau ne bouge pas, l'**ancien change de rôle affiché** ;
- **mutant** (sans « la vente d'abord ») : attrapé ;
- le branchement des deux fiches et le chemin d'avant gardé.

L'essai de P1 reste vert, et `npm run build` passe.

**Sur les VRAIES lignes** (lecture seule, script hors dépôt) : tous les contacts qui ont plusieurs lignes sur un bien, soit 32 737
lignes, **11 290 contacts, 13 861 biens**.

| mesure | résultat |
|---|---|
| vente signée non affichée | **0** |
| mot anglais | **0** |
| achat caché | **0** |
| résultat qui change selon l'ordre | **0** |
| lignes en gris | 734 |
| « Propriétaire depuis le … » | 116 |

⬜ **Reste, dans l'ordre** :
1. Frédéric **colle** le patch, puis la répétition (11 verts attendus) ;
2. il **pousse** (P1, P2 et les commits locaux) ;
3. je **regarde l'écran** avec sa session : JACQUIER (61730), un vendeur, un acheteur en cours, au bureau **et** à 390 px ;
4. le mode sombre du téléphone (≤ 1180 px) : les pastilles reprennent la règle `.fa-cx-lk-role` d'avant, **non vu**.

**Retour arrière** : l'interrupteur (écran) ; `_INVERSE.sql` (base) ; les deux sont indépendants, l'écran marchant avec ou sans le patch.

### 31.6 ✅ LE PATCH P2 EST POSÉ EN BASE — 27/10 *(Frédéric : « fais-le toi-même, tu as mon accord »)*

**Posé par moi**, par le pooler, avec le fichier tel quel (`BEGIN` … `COMMIT`). L'empreinte de la vue est passée de `d4350c63…` à
**`0021f0f1…`**, et la vue a maintenant **20 colonnes**.

**Répétition** :
- **1er passage : 10 verts, 1 rouge.** La fiche de JACQUIER sous le compte admin a pris **457,9 ms** (seuil 200), alors que l'essai annulé
  donnait 26,4 ms. Le commercial était vert (131,8 ms).
- **Rejouée 3 fois** (lecture seule) : **0 rouge** à chaque passage. Admin 24,5 / 27,0 / 26,0 ms, commercial 131,5 / 138,1 / 131,8 ms.

➡ Le rouge était le **premier passage juste après le changement de la vue**, quand Postgres refait ses plans. On l'a vu une seule fois, et
il ne s'est pas reproduit. C'est le même phénomène que le 26/10 (304 ms au premier passage, puis 14 verts).

**L'app en ligne n'est pas gênée** : elle lit la vue par `select *`, donc elle reçoit deux champs de plus et ne les lit pas tant que P2
n'est pas poussé. Les deux autres lecteurs à l'écran et les deux en base nomment leurs colonnes.

⬜ **Reste** :
1. **Pousser** (Frédéric) ;
2. **regarder l'écran** : JACQUIER (61730), un vendeur, un acheteur en cours, au bureau et à 390 px, plus le mode sombre du téléphone ;
3. **rejouer la répétition** le lendemain de la première nuit.

**Retour arrière** : `_INVERSE.sql`, éprouvé le 27/10 dans une transaction annulée.

### 31.7 ✅ P2 VU À L'ÉCRAN — 27/10 *(Frédéric : « j'ai poussé ; regarde l'écran de la fiche contact »)*

Vercel sert `index-DB_j7vD8.js`, qui contient le code de P2 (`fa-cx-lk-roles`, « Propriétaire depuis le », « Vente signée »). Contrôle fait
dans le Chrome de Frédéric (sa session), dans un onglet à moi, refermé à la fin.

| fiche | ce que montre la ligne du bien | verdict |
|---|---|---|
| JACQUIER (10354352, mandat 18563) | **Propriétaire** · **Acheteur** — « Propriétaire depuis le 25/09/2026 · Vente signée le 25/09/2026 » — 210 000 € | ✅ |
| un acheteur en cours (10001775) | **Acheteur** — « Compromis du 17/09/2026 » — 45 000 € | ✅ |
| un compromis annulé (10000087) | **Acheteur** en gris (`rgb(138,127,110)`) — « Compromis annulé (du 09/11/2017) » — 189 000 € | ✅ |
| un mandant devenu acheteur (10016576) | **Mandant** · **Acheteur** — « Vente signée le 03/06/2019 » — 22 000 € ; son 2e bien : **Mandant**, « annonce liée » | ✅ |
| un mandant seul (10000045) | **Mandant** — « annonce liée », sans montant | ✅ |

- **Bureau** (1280 px, la fenêtre ne descend pas plus bas) : aucun débordement (`scrollWidth = clientWidth`).
- **Téléphone, vrai rendu mobile** : la même adresse ouverte dans un cadre de 390 px **dans l'onglet de sa session** (même origine, donc
  même connexion). Les pastilles passent sous le titre, le montant reste à côté, **rien ne déborde**. ⚠ Le sous-titre est **coupé par des
  points de suspension** : « Propriétaire depuis le 25/09/2026 · Ve… ».
- **Mode sombre du téléphone : NON VU** (le Chrome de Frédéric est en clair, et je ne peux pas l'imiter dans sa session).

⬜ **Deux petites questions** :
1. au téléphone, laisser le sous-titre aller **à la ligne** au lieu de le couper (une règle CSS sous 640 px) ?
2. sur un compromis annulé, on montre encore **son montant** (189 000 €) : le garder, le griser ou le retirer ?

⚠⚠ **TROUVAILLE, NOTÉE, PAS TRAITÉE — OUVRIR UNE FICHE PEUT FAIRE RECULER LE TYPE DU CONTACT.**
- L'en-tête de JACQUIER dit « **Mandant · Acheteur** » : en ligne, son type est `["acquereur_offre","mandant"]`. Or la nuit lui avait donné
  propriétaire + acheteur (vente) : 115 des 116 « nés de la vente » l'ont bien en ligne ; **JACQUIER est le seul en retard**.
- La cause mesurée : **deux relectures à l'ouverture de sa fiche** (`refresh_console_contact_data`, raison `read_through_open`, 27/10 à
  10:25 et 14:29 UTC). Cette relecture d'**un seul** contact recalcule le type et le pousse — et **pas comme la nuit**.
- Sur les **12** contacts relus en 24 h : **2** ont perdu la vente dans leur type, 1 le compromis, 1 le propriétaire. Ça dure **jusqu'à la
  nuit suivante**, et ça recommence à chaque ouverture.
- La ligne du bien (P2) est **juste**, parce qu'elle lit les registres et non le type : c'est l'**en-tête** et l'**annuaire** qui reculent.
- **Cause NON cherchée** (le chantier 1 est bien allumé dans `.env`, l. 76 ; `refresh_contact_inproc.py` le charge-t-il, et avec quelles
  relations ?). C'est exactement le sujet de **P3** (le type suit le geste) : **à auditer en premier dans P3**.

## 32. P3 — AUDIT : OUVRIR UNE FICHE FAIT RECULER LE TYPE *(27/10, Frédéric : « ouvre P3 par l'audit de la relecture à l'ouverture d'une fiche qui fait reculer le type »)* — lecture seule, rien codé

> Audit limité à la **relecture d'un seul contact** (lire / remonter le type). Les autres objets ne sont pas touchés par ce chemin.

### 32.1 Le chemin
1. **L'ouverture d'une fiche** appelle `app_console_request_contact_refresh` (base). La fonction pose un travail
   `refresh_console_contact_data` (raison `read_through_open`), au plus une fois par délai.
2. **Le worker** (`runContactRefreshPipeline`, `console_job_worker.js` l. 4355) lance `phase2/sync/refresh_contact_inproc.py`, qui enchaîne
   4 étapes : relire le détail chez Hektor, normaliser, **construire** (`build_contacts_layer.py --contact-id`), **pousser** vers Supabase.
3. ⚠ **Les gestes sur un contact passent par le même chemin** : création, modification, archivage, ajout ou suppression d'une recherche,
   relecture de garde (`search_overwrite_guard`). Sur 30 jours : **115 relectures à l'ouverture (41 contacts)** et une trentaine de gestes.

### 32.2 La cause, dans le code
`load_relations` (`build_contacts_layer.py` l. 1075), **en mode « un seul contact »**, saute trois sources sur six, chacune gardée par
`and not contact_filter` (depuis le commit `8ef77ba` du **01/06/2026** ; les acheteurs sont dans un JSON qu'une requête ne filtre pas) :

| source | nuit | un seul contact |
|---|---|---|
| propriétaires de la fiche d'annonce (`hektor_annonce_detail`) — 72 031 liens | ✅ | ⛔ sautée (l. 1212) |
| liens annonce ↔ contact (`sync_annonce_contact_link`) | ✅ | ✅ |
| offres (`hektor_offre`) | ✅ | ✅ |
| **compromis** (`hektor_compromis`) | ✅ | ⛔ sautée (l. 1289) |
| **ventes** (`hektor_vente`) | ✅ | ⛔ sautée (l. 1314) |
| annonces du détail du contact | ✅ | ✅ |

Ensuite, `refresh_contact_slice` (l. 2114) **garde bien les anciennes lignes de liens** (`merge_relation_rows`), mais il calcule le **type**
et l'**éligibilité** à partir des **seules lignes relues** (`roles_by_contact` de `load_relations`). Trois effets :
- **compromis et vente disparaissent du type** ;
- **la règle du chantier 1 ne trouve plus la vente**, donc le propriétaire né de la vente redevient « mandant » (le bien a un numéro de
  mandat). Le journal du worker le dit pour JACQUIER : « [acheteur proprietaire] **0** lien(s) né(s) d'une vente » ; la règle est bien
  allumée ;
- un contact dont tous les liens viennent des sources sautées se retrouve **sans type**, et **non éligible**.

### 32.3 La mesure (27/10, après mes ouvertures de l'après-midi)
- **5 contacts** ont un type en désaccord avec les registres ; **tous ont été relus aujourd'hui** (le reste de l'annuaire est d'accord :
  la nuit répare tout) :
  - JACQUIER (10354352) : `offre + mandant` au lieu de propriétaire + offre + compromis + vente ;
  - 10191800 : l'offre seule, la vente perdue ;
  - ⚠ **trois de MES ouvertures du contrôle de P2** : 10016576 (`offre + mandant`, perdu compromis et vente), 10001775 (perdu le
    compromis), **10000087 (CHILLET) : type VIDE et « non éligible »** (il est encore dans l'annuaire).
- **Ça dure jusqu'à la nuit suivante**, qui recalcule tout. Et ça recommence à chaque ouverture.
- **Qui est exposé** : tout contact qui a un compromis ou une vente (≈ 13 000 acheteurs), et tout lien de propriété qui ne vient que de
  la fiche d'annonce. 45 933 contacts n'ont **que** cette source (beaucoup sont sur le serveur seulement).
- **Ce qui ne bouge pas** : la ligne du bien dans la fiche (P2 lit la vue des registres, pas le type), le registre des liens
  (`app_relation`) et la table des parties. Le chemin ne les écrit pas.

### 32.4 Le coût des sources sautées, si on les lisait (mesuré sur JACQUIER)
- compromis **55 ms**, ventes **50 ms** ;
- fiche d'annonce **2 563 ms** : 61 417 lignes de JSON à balayer.

### 32.5 La proposition — À TRANCHER PAR FRÉDÉRIC
**A' (recommandée)** — dans `refresh_contact_slice` seulement, calculer le **type** et l'**éligibilité** à partir des lignes **FUSIONNÉES**
(celles de la nuit, gardées, plus celles relues), en réappliquant **la même règle** de mandant / propriétaire et du chantier 1. Le bloc
de la règle sort de `load_relations` en une fonction partagée : **une seule règle, deux appelants**.
- **Aucune lecture de plus chez Hektor.**
- Un rôle **neuf** arrive tout de suite. Un rôle **retiré** chez Hektor reste jusqu'à la nuit, qui confirme.

**A** — lire en plus compromis et ventes pour ce contact (≈ 0,1 s), et éventuellement la fiche d'annonce (+2,6 s par ouverture).
Plus frais, plus lent, plus de code.

**B** — ne plus recalculer le type à la relecture (garder celui de la nuit). Simple, mais un rôle neuf attendrait la nuit.

**Ce que ça pourrait casser** :
- **le calcul de nuit** (même fichier) : la règle déplacée doit rendre **exactement** les mêmes types. Témoin prévu : un calcul complet sur
  une **copie** de la base, avant et après, avec des empreintes identiques ;
- **les essais existants** du mode un seul contact (`test_substitution_identite.py`, `test_c9d_carnet_des_liens.py`,
  `test_c9f_numero_bien_dans_cle.py`) ;
- ⚠ **le worker lance Python à chaque travail** : un fichier modifié sur cette machine est **en production dès son écriture**. Aucun
  redémarrage nécessaire, mais **aucun filet non plus**. Donc : écrire et éprouver sur une copie, ne poser qu'avec ton « vas-y ».

**Essais** :
- sur une copie de `phase2.sqlite`, la relecture de JACQUIER, des 4 autres et d'un échantillon d'une centaine de contacts de tous
  types : le type doit égaler celui des registres (la vue) ;
- **témoin inverse** : le code d'aujourd'hui doit donner les 5 désaccords mesurés ;
- mutant : sans la fusion, ils doivent revenir.

**Réparer les 5 contacts** : **rien à faire**. La nuit les recalcule ; à vérifier demain matin.

Le vrai P3 (le type suit le **geste**, dans la base, au clic) vient **après** : sans A', chaque ouverture de fiche défairait ce qu'il pose.

## 33. ✅ P3 « B » POSÉ — LA RELECTURE D'UN SEUL CONTACT NE TOUCHE PLUS À CE QUI VIENT DES LIENS *(27/10, Frédéric : « B » ; « nos registres sont autonomes […] il faut B pour ne pas écraser ce que nous avons fait dans l'app » ; « oui, pose B »)*

**Le code** : `phase2/contacts/build_contacts_layer.py`, **72 lignes ajoutées, rien de retiré**, fins de ligne CRLF gardées.
- **Trois fonctions neuves** : `load_existing_contact_link_fields`, `garder_le_type_de_la_nuit`, `relecture_garde_le_type`.
- **Deux appels** dans `refresh_contact_slice`.
- **Ce qui est gardé** de la ligne déjà connue : le type (`relation_roles_json`), le nombre de biens liés (`linked_annonce_count`) et les
  raisons d'éligibilité, **sauf** `active_search`, qui est relue.
- **Tout le reste est relu** comme avant. Un contact sans ligne connue est calculé comme avant.
- **La nuit n'est pas touchée** : elle n'appelle pas `refresh_contact_slice`.
- **Interrupteur** : `APP_RELECTURE_GARDE_LE_TYPE`, allumé par défaut ; `0` dans `.env` = l'ancien calcul, à l'identique (prouvé).
- ⚠ Le worker relance Python à chaque travail : **en production depuis l'écriture du fichier (27/10, ~16:20)**, sans redémarrage.

**L'essai, sur deux copies de `phase2.sqlite`** (sauvegarde cohérente de 14 s) : l'ancien code sur l'une, B sur l'autre, **104 contacts**
tirés parmi tous les types, avec les valeurs de la nuit.

| contacts | l'ancien code fait reculer | B fait reculer |
|---|---|---|
| acheteurs avec vente (30) | 30 | **0** |
| « nés de la vente » (10) | 10 | **0** |
| compromis sans vente (10) | 10 | **0** |
| entrés par l'élargissement `console_transaction_party` (20) | 20 (**rendus non éligibles**) | **0** |
| propriétaires (15) | 0 | 0 |
| mandants (9) | 2 | **0** |
| avec une recherche active (10) | 0 | 0 |

- Le reste de la fiche est **identique** entre l'ancien code et B, recherches comprises.
- Un contact rendu « tout neuf » donne le **même résultat** qu'avant (`["mandant"]`, éligible).
- Exemple d'un « né de la vente » : nuit `compromis + vente + propriétaire` → ancien code `propriétaire` → **B, celui de la nuit**.
- **Interrupteur éteint** : B redonne exactement l'ancien code (les mêmes 72 reculs, 0 autre écart).
- **Mutant** (sans la ligne qui garde les raisons de l'élargissement) : 20 + 4 reculs, **attrapé**. ⚠ Mon premier mutant n'avait pas été
  posé (une erreur d'échappement dans mon script) : je l'ai vu, refait, et c'est le second qui compte.

⭐ **Une deuxième cause confirmée en passant** : **2 801 contacts** sont dans l'app par la raison `console_transaction_party`, posée par
l'élargissement de nuit (`elargir_perimetre_console.py`). La relecture ne la connaissait pas, donc une simple ouverture de leur fiche les
rendait **non éligibles**. B la garde.

**Essais existants, sur le vrai fichier** :
- `test_c9d_carnet_des_liens.py` **19/19** ✅ ;
- `test_c9f_numero_bien_dans_cle.py` **15/15** ✅ ;
- `test_contacts_layer.py` **1/1** ✅ (il demande `PYTHONPATH=.`) ;
- `test_substitution_identite.py` : **rouge** sur deux points (② « la recherche ne pend pas sous l'identité » et ④ « aucun témoin
  trouvé »). ⚠ **Le même rouge revient avec l'ancien code** (interrupteur à 0) : il **existait avant B**. L'essai le dit lui-même : « le
  critère de sélection a vieilli […] ce contrôle ne testait plus rien » ; le fichier n'a pas bougé depuis le 23/09. Noté, pas touché.
  Il demande aussi `PYTHONIOENCODING=utf-8` pour s'afficher.

⬜ **À vérifier** :
1. au prochain travail `refresh_console_contact_data`, le journal doit dire « [relecture] ce qui vient des liens est gardé pour 1
   contact(s) » ;
2. **demain matin**, les 5 contacts reculés aujourd'hui doivent avoir retrouvé leur type de nuit (B les garde dans l'état d'aujourd'hui
   jusque-là).

**Retour arrière** : `APP_RELECTURE_GARDE_LE_TYPE=0` dans `.env`, effet au travail suivant ; ou `git revert` du commit.

## 34. LE VRAI P3 — LE TYPE SUIT LE GESTE, DANS LA BASE : audit du 27/10 *(Frédéric : « pourquoi on ne fait pas le type […] suivre le geste dans la base ? » ; « oui »)* — lecture seule, rien codé

> Audit limité au **type** du contact (`relation_roles_json`) : qui l'écrit, qui le lit, d'où il peut se calculer. L'éligibilité et le
> compte des recherches (« Acquéreur ») ne sont **pas** mesurés ici.

### 34.1 Qui écrit le type, qui le lit
- **Un seul écrivain** : l'envoi depuis la machine (`push_contacts_to_supabase.py`), la nuit et à chaque relecture d'un seul contact.
  Aucune fonction de la base ne l'écrit. Il n'y a aucun déclencheur sur `app_relation`, ni sur `app_affaire_partie` (cette dernière est
  tenue par des déclencheurs sur `app_affaire_ledger`).
- **Les lecteurs** :
  - la vue `app_contacts_current`, donc l'annuaire, avec son filtre par type (`contains`, `lib/api.ts` l. 2556) ;
  - les cartes et l'en-tête de la fiche ;
  - la recherche globale (l. 5437).

### 34.2 Les registres peuvent-ils donner le type ? Oui
Le type calculé depuis la vue des liens (`app_contact_relations_current`, nos registres) est **identique pour 62 332 contacts sur
62 339**. Les 7 écarts :
- **5 sont les reculs d'aujourd'hui** (§32), que B n'a pas défaits : il garde l'état connu jusqu'à la nuit ;
- **2 sont des contacts dont le lien a disparu chez Hektor** (10324835 absent depuis le 10/10, 10205503 depuis le 01/10). Les registres
  disent « plus de lien », mais le type stocké dit encore « Mandant » ou « Propriétaire ». Pour ces deux-là, **le type stocké a tort et les
  registres ont raison** (la nuit ne renvoie plus ces fiches).

Le temps : un contact se recalcule en **≈ 13 ms** ; le **rapprochement complet** des 62 339 contacts prend **1,8 s**.

### 34.3 Les portes qui écrivent nos registres
- **App** (fonctions de la base, appelées par l'utilisateur connecté) :
  - **liens** : `app_link_mandant_optimistic`, `app_create_mandant_contact_optimistic`, `app_unlink_mandant_optimistic` ;
  - **transactions**, puis la table des parties par ses déclencheurs : `app_geste_affaire_optimistic`, `app_modifier_affaire_optimistic`,
    `app_edit_affaire_optimistic`, `app_change_annonce_status_optimistic`, `app_affaire_commission_ecrire`, `app_attribuer_chaines_affaire`.
- **La nuit et le worker** : par l'API, avec la **clé de service**. Le worker écrit `app_relation` (confirmer, défaire) et
  `app_affaire_ledger` ; la nuit, `relation_ledger.py` et `affaire_ledger.py`.

### 34.4 Le piège du volume
En 24 h, la nuit a **recalculé 105 690 lignes de la table des parties (39 643 contacts)**, et elle a vu 132 828 liens. ⚠ La table des
parties est réécrite par **suppression puis réinsertion** (`app_affaire_partie_suivre`). Un déclencheur naïf recalculerait donc ~40 000
contacts chaque nuit : **≈ 9 minutes de plus**.

### 34.5 La proposition — À TRANCHER PAR FRÉDÉRIC
**P3-a — au geste** : des déclencheurs sur `app_relation` et `app_affaire_partie` recalculent le type des **seuls** contacts touchés,
**uniquement quand l'écriture vient d'un utilisateur de l'app** (le jeton de la requête dit `authenticated`). Les écritures de la nuit et
du worker (clé de service) passent sans recalcul : **zéro coût pour la nuit**. Trois règles :
- on n'écrit que si le type **change** ;
- on ne touche pas à `refreshed_at`, que lit le contrôle des modifications (`app_contact_saisie_modif_juge_trg`) ;
- **jamais** on ne fait échouer le geste d'origine : une erreur est notée, le geste passe.

**P3-b — la nuit confirme sans effacer** : une fonction `app_types_depuis_les_registres()` fait le rapprochement complet (1,8 s) et remet
le type des registres là où il diffère. Elle est jouée **en fin de nuit**, après l'envoi des contacts, et **chaque heure** (pg_cron).
Elle couvre ce que P3-a ne voit pas :
- l'envoi de nuit qui réécrit le type d'après le miroir de Hektor ;
- un « défaire » du worker quand Hektor refuse ;
- les deux fiches figées ;
- les 5 reculs d'aujourd'hui, **dès son premier passage**.

**Ce que ça pourrait casser** :
- **le temps des gestes** : ≈ 13 ms par contact touché ;
- **le temps de la nuit** : nul pour P3-a (contrôle du jeton) ; 1,8 s pour P3-b. Les deux sont à mesurer dans une transaction annulée,
  avec un lot de nuit rejoué sous la clé de service ;
- **les déclencheurs déjà posés** sur `app_contact_current` (cible, contrôle des modifications) ;
- **le moniteur** : une tâche pg_cron neuve se déclare et se surveille (leçons : lire les CHECK de la table du moniteur, une lecture
  ratée n'est jamais un vert) ;
- **B reste utile** : la relecture ne réécrit plus le type, donc elle ne défait pas P3-a.

**Essais prévus (transaction annulée)** :
- un mandant rattaché, une offre créée, un mandant retiré, sous le jeton d'un utilisateur : **le type change à l'instant** ;
- les mêmes écritures sous la clé de service : **aucun recalcul** ;
- le rapprochement : **7 → 0** écarts, puis **0** au second passage ;
- un lot de la table des parties rejoué sous la clé de service : temps inchangé ;
- **témoin inverse** : sans les déclencheurs, le type ne bouge pas ;
- **mutant** : sans le contrôle du jeton, le temps du lot de nuit explose.

**Questions** :
(1) **les registres font foi** pour le type : la nuit confirme, et n'efface jamais ce qui est dans nos registres ?
(2) le rapprochement **chaque heure**, en plus de la fin de nuit ?
(3) l'ordre : **P3-b d'abord** (il répare tout de suite les 7 écarts et ne touche aucun geste), **puis P3-a** ?

## 35. P3 — LA RÈGLE DE FRÉDÉRIC : LE TYPE SE DÉDUIT CHEZ NOUS **QUAND HEKTOR A ACCEPTÉ LE GESTE** *(27/10 : « suis la règle de rattachement ; même mieux, on déduit chez nous le type uniquement si le geste a été accepté chez Hektor » ; et avant : « on garde notre valeur, on signale juste le conflit à l'admin »)* — audit, rien codé

**La règle, en clair** :
1. **Au clic**, le geste est écrit dans nos registres, et la ligne du bien dans la fiche le montre (déjà fait). **Le type ne bouge pas.**
2. **Hektor accepte** : on déduit le type chez nous **à ce moment-là**.
3. **Hektor refuse** : le geste est défait, selon la règle du rattachement (déjà faite) ; **le type n'a jamais bougé**.
4. **La nuit** : si son type diffère de ce que disent nos registres confirmés, **on garde le nôtre** et on **signale le conflit à l'admin**.
5. **Un geste fait dans Hektor** arrive la nuit dans nos registres, comme aujourd'hui.

Cette règle **remplace** P3-a et P3-b du §34 : plus de déclencheur au clic, plus de rapprochement qui corrige en silence.

### 35.1 Le moment « accepté », geste par geste (lu dans le worker)
- **Rattacher un mandant** : à l'accord, le worker passe la ligne de `present_in_hektor = false` à `true` (`console_job_worker.js`
  l. 17256, « relation_etablie »). Un refus la défait (`annulerRattachementOptimiste`).
- **Retirer un mandant** : le retrait est écrit **au clic** (`retire_le`). L'accord **ne laisse aucune trace** dans `app_relation` ; seul
  un refus défait (`annulerRetraitOptimiste`).
- **Les transactions** : le worker écrit le registre des transactions à l'accord (l. 21792, 22109).
- ➡ **Le seul moment commun à TOUS les gestes, c'est le travail qui passe à « terminé »** (`app_console_job.status = 'done'`).

### 35.2 Les travaux concernés (60 jours, ≈ 235)
| type de travail | nombre | ce que la charge nomme |
|---|---|---|
| `change_hektor_annonce_status` | 152 | affaire, acheteurs, mandants |
| `change_hektor_offre_status` | 28 | affaire |
| `delete_hektor_compromis` / `cancel_hektor_compromis` / `delete_hektor_vente` | 44 | affaire |
| `link_hektor_mandant` / `unlink_hektor_mandant` | 8 | contact |
| `create_hektor_mandant_contact` / `update_hektor_mandant_contact` | 3 | (le contact, après coup) |

Tous portent leur **annonce**. **La nuit ne crée aucun de ces travaux** : le mécanisme ne lui coûte rien.

### 35.3 La proposition — À TRANCHER PAR FRÉDÉRIC
**Une fonction** `app_type_confirme(contact)` calcule le type depuis nos registres, **en ne comptant que ce que Hektor a confirmé** :
- les liens `present_in_hektor = true` ;
- les transactions présentes chez Hektor (`transaction_presente`).

Elle coûte ≈ 13 ms par contact.

**Un déclencheur** sur `app_console_job` : quand un travail d'une **liste déclarée** (les 9 types ci-dessus) passe à « terminé »,
il recalcule le type de **chaque contact lié à l'annonce de ce travail** (ses liens et ses parties, quelques contacts) :
- on n'écrit que si le type change ;
- on ne touche pas à `refreshed_at` ;
- une erreur ne fait **jamais** échouer le travail (elle est notée).

Un travail en erreur, ou défait, ne recalcule rien.

**En fin de nuit**, une fonction compare le type envoyé par la nuit avec `app_type_confirme`. **Là où ils diffèrent, on garde le nôtre**
et on **signale** l'écart au moniteur, une ligne par contact, avec les deux valeurs. Les 7 écarts d'aujourd'hui seraient ainsi
**remis et signalés** dès le premier passage.

**Ce que ça pourrait casser** :
- `app_console_job` est la table la plus active (photos, documents…). Le déclencheur filtre d'abord sur le changement de statut **et** le
  type de travail, et ne fait rien pour tout le reste. Son coût est à mesurer dans une transaction annulée ;
- le **retrait** : entre le clic et l'accord, la ligne est déjà cachée (`retire_le`). Si un **autre** travail du même bien se termine dans
  cet intervalle, le type perdrait « Mandant » un peu tôt. C'est un cas rare, que j'écris pour le traiter si tu le veux ;
- le **moniteur** : une ligne neuve se déclare et respecte les CHECK de sa table (leçon du 25/10) ;
- **B reste utile** : la relecture ne réécrit plus le type.

**Essais prévus (transaction annulée)** :
- un travail `link_hektor_mandant` passé à « terminé » doit mettre « Mandant » dans le type ;
- le même travail en « erreur » ne doit rien changer ;
- un travail de photos qui se termine ne doit rien déclencher ;
- un travail de statut « vendu » doit donner à l'acheteur « Acheteur » et « Propriétaire » (avec la règle du chantier 1) ;
- la comparaison de fin de nuit doit passer de 7 écarts à 0, avec 7 signalements ;
- **témoin inverse** : sans le déclencheur, le type ne bouge pas ;
- **mutant** : sans le filtre sur le type de travail, un travail de photos doit être attrapé.

### 35.4 ⛔ ABANDONNÉ PAR FRÉDÉRIC (27/10) — « non, oublie cette idée, on sera dépendant d'Hektor »
Attendre l'accord de Hektor pour déduire le type, c'est rester **dépendant de Hektor**, l'inverse du but. **Le §35.3 n'est pas à coder.**

**La règle retenue** (Frédéric, 27/10, deux messages plus tôt) : **on calcule nous-mêmes le type au geste**, puis on envoie le geste à
Hektor. Soit il confirme, soit il ne confirme pas : en cas de **refus**, on suit **la règle du rattachement** (le geste est défait, et le
type suit) ; **la nuit, on garde notre valeur et on signale le conflit à l'admin**.

**Ce qui reste utile du §35** : tous les gestes qui changent un type passent par un travail d'une **liste déclarée** de 9 types, posé par
la fonction de l'app, **dans la même transaction que l'écriture du registre**. Ce travail sert donc de **signal du geste**, au clic, sans
attendre Hektor :
- **au clic** : quand l'app pose le travail, on recalcule le type des contacts de l'annonce depuis **tous** nos registres (y compris la
  ligne encore non confirmée). Le déclencheur est **différé à la fin de la transaction**, pour voir le registre déjà écrit ;
- **à la fin du travail** : quand il passe à « terminé » ou en « erreur », on recalcule de nouveau. Un refus défait le geste (règle du
  rattachement), donc le type revient ;
- **la nuit** ne crée aucun de ces travaux : **zéro coût** ;
- **en fin de nuit** : on compare le type envoyé par la nuit avec celui de nos registres ; on **garde le nôtre** et on **signale** l'écart.

## 36. P3 — AUDIT DU PROBLÈME, ET LA MEILLEURE SOLUTION AU VU DU PROJET *(27/10, Frédéric : « audite le problème et dis-moi si c'est la meilleure des solutions au vu de mon projet »)* — lecture seule, rien codé

### 36.1 Le problème, en une phrase
Le **type** d'un contact (Mandant, Propriétaire, Acheteur) est **calculé sur la machine, à partir du miroir de Hektor**, et seulement là :
la nuit, et à la relecture d'un contact (que B a neutralisée). Nos **registres** (liens, transactions, table des parties), eux, sont à jour
**au clic**. Le type est donc en retard sur nos registres jusqu'à la nuit, et **il dépend de Hektor**. Le jour de la coupure, il ne
bougerait plus du tout.

### 36.2 Ce que doit respecter la solution (le projet)
1. **L'app autonome** : « chez nous d'abord, Hektor complète » (méthode du 07/10, reprise dans ⑧ : « anticiper la coupure »).
2. **Survivre à la coupure** : plus de miroir de Hektor, plus de travaux vers Hektor.
3. **Juste quel que soit l'auteur** du changement : un geste de l'app, le worker (confirmer, défaire), la nuit, et demain d'autres portes.
4. **Ne pas alourdir la nuit** : la table des parties y est réécrite pour ~40 000 contacts (105 690 lignes en 24 h).
5. **Un mécanisme que le projet connaît déjà**, plutôt qu'une invention.
6. **Réversible** par un interrupteur.

### 36.3 Les solutions, jugées sur ces critères
| solution | autonome | survit à la coupure | juste pour tout auteur | coût de nuit | délai | déjà dans le projet |
|---|---|---|---|---|---|---|
| ① type à l'accord de Hektor (§35.3) | ✗ | ✗ | ✗ | 0 | à l'accord | non |
| ② signal par le travail du worker (§35.4) | ✓ | **✗** (plus de travaux après la coupure) | ✗ (seules les portes qui posent un travail) | 0 | 1 s | non |
| ③ déclencheur au clic, filtré « utilisateur de l'app » (§34 P3-a) | ✓ | ✓ | ✗ (ignore le worker et la nuit, il faut un rapprochement en plus) | 0 | 1 s | non |
| ④ rapprochement complet chaque heure ou toutes les 5 min | ✓ | ✓ | ✓ | 1,8 s par passage | 5 à 60 min | non |
| ⑤ type calculé à chaque lecture, sans le stocker | ✓ | ✓ | ✓ | 0 | 0 | non ; le filtre « Mandants » de l'annuaire passe de 0,1 s à ~1 s |
| **⑥ « à recalculer » marqué par nos registres, recalcul chaque minute** | **✓** | **✓** | **✓** | **faible** (lots en arrière-plan) | **≤ 1 min** | **oui : `rapprochement-dirty`** |

⚠ **Ma proposition ② avait un défaut que je n'avais pas vu** : elle se branchait sur les travaux du worker, c'est-à-dire sur la
**plomberie vers Hektor**. Après la coupure, plus de travaux, donc plus de recalcul. C'est encore une dépendance à Hektor, cachée.

### 36.4 La recommandation : ⑥, sur le modèle de `rapprochement-dirty`
Le projet fait **déjà** exactement cela pour les rapprochements : `trg_dossier_dirty` et `trg_search_dirty` marquent ce qui a bougé dans
`app_rapprochement_dirty`, et deux tâches pg_cron, **chaque minute**, recalculent par lots (`app_process_rapprochement_dirty(200)`,
`app_bulk_recompute_chunk(80)`).

Pour le type :
1. **Marquer** : un petit déclencheur sur `app_relation` et un sur `app_affaire_partie`. À **chaque** écriture, quel qu'en soit l'auteur,
   il ajoute le numéro du contact à une table « types à recalculer » (« s'il n'y est pas déjà » ; quelques microsecondes).
2. **Recalculer** : une tâche pg_cron, **chaque minute**, prend un lot de contacts marqués. Elle calcule leur type **depuis nos registres**
   (la même règle que la vue, déjà identique à la nuit pour 62 332 contacts sur 62 339) et **n'écrit que s'il change**.
3. **La nuit confirme sans effacer** : si l'envoi de nuit pose sur un contact un type différent de nos registres, ce contact est marqué
   lui aussi (un déclencheur sur `app_contact_current`, quand le type change). Au passage suivant, **notre valeur revient**, et l'écart est
   **signalé à l'admin**, une ligne par contact avec les deux valeurs. C'est le « conflit » de Frédéric.

**Avec ses deux exemples** :
- **geste dans l'app** : le registre est écrit au clic, le contact est marqué, **le type change dans la minute**, sans attendre Hektor ;
- **refus de Hektor** : le worker défait le lien (règle du rattachement), le contact est marqué, le type revient dans la minute ;
- **geste dans Hektor** : la nuit écrit nos registres, les contacts touchés sont marqués et recalculés par lots en arrière-plan ;
- **après la coupure** : il n'y a plus que nos registres, et **rien n'est à changer**.

**Le coût de la nuit** : marquer ~40 000 contacts (quelques secondes), puis les recalculer par lots chaque minute, en arrière-plan. Un
calcul complet des 62 339 contacts prend 1,8 s : un lot de 5 000 coûte donc environ 0,15 s. **À mesurer dans une transaction annulée.**

**Ce que ça pourrait casser** :
- les déclencheurs existants sur `app_contact_current` (cible, contrôle des modifications) : on n'y touche pas à `refreshed_at` ;
- une boucle (notre écriture marque de nouveau le contact) : coupée, puisqu'on n'écrit que si le type change ;
- le moniteur : une tâche pg_cron neuve se déclare, et sa ligne respecte les CHECK de sa table ;
- B reste utile ; l'envoi de nuit n'est pas modifié (pas de Python touché).

**Ce que ⑥ ne couvre pas** (non mesuré ici) : « Acquéreur » (recherche active) et l'éligibilité, qui ont leurs propres chemins.

**Retour arrière** : un interrupteur dans la fonction de recalcul (elle ne fait plus rien), ou désactiver la tâche pg_cron.

### 36.5 ⚠⚠ LA DÉPENDANCE CACHÉE : LA VUE COMPTE LES TRANSACTIONS « PRÉSENTES CHEZ HEKTOR » *(27/10, Frédéric : « attention, il ne faut pas qu'à la coupure le changement de type soit dépendant de l'accord de Hektor »)* — mesuré, rien codé

**Le mécanisme ⑥ lui-même ne dépend pas de Hektor** : il recalcule depuis nos registres, dès qu'ils sont écrits. **Mais il ne vaut que ce
que dit la vue qu'il lit**, et la vue `app_contact_relations_current` a deux règles différentes selon le registre :
- **les liens** (mandant, propriétaire) : `present_in_hektor OR (source = 'app' AND absent_depuis IS NULL)` et `retire_le IS NULL`. Un lien
  posé dans l'app **compte tout de suite**, sans Hektor ✅ ;
- **les transactions** (acheteur d'une offre, d'un compromis ou d'une vente) : `p.transaction_presente`, c'est-à-dire
  `app_affaire_ledger.present_in_hektor`. ⛔ **Une transaction ne compte que si elle est PRÉSENTE CHEZ HEKTOR.**

**Ce que ça fait aujourd'hui** (lu dans le code) :
- une offre, un compromis ou une vente **créés dans l'app** entrent au registre avec `present_in_hektor = false` et **sans numéro Hektor**
  (`app_change_annonce_status_optimistic`, « Hektor ne la connaît pas encore ») ;
- ils ne passent à `true` que lorsque le **worker** reçoit le numéro de Hektor (`poserIdTransactionSurAffaire`, l. ~22100) ;
- **entre les deux, l'acheteur n'apparaît ni dans la fiche contact (P2) ni dans son type.**
- ⛔ **Après la coupure, il n'apparaîtrait JAMAIS** : plus de worker vers Hektor, donc plus de `true`.

**Le même drapeau porte deux sens** : « Hektor l'a », et « supprimée ». Le geste « Supprimer » le passe à `false` au clic, et un refus de
Hektor le remet à `true` (`restaurerEtatAffaire`). Aujourd'hui : 31 096 transactions à `true`, **17 à `false`** (retirées), aucune sans
numéro Hektor.

**Ce qu'il faut, pour que le type ne dépende jamais de Hektor** : compter une transaction parce qu'elle est **vivante chez nous**, et non
parce qu'elle est **présente chez Hektor**, exactement comme les liens. Une transaction est vivante tant qu'elle n'est pas **supprimée** ;
il faut donc **un marqueur de suppression à nous** (comme `retire_le` pour les liens), au lieu de lire « présente chez Hektor ».

⚠ **Ce qu'il ne faut pas casser** :
- la règle « le registre porte la valeur de Hektor, le carnet la nôtre » (« le gel », 16/09) : elle porte sur les **champs** d'une
  transaction. Ici, il s'agit de son **existence** ;
- **delete-never** ;
- les 17 transactions retirées chez Hektor (elles doivent rester hors du type) ;
- le filet qui rejoue un envoi échoué (C.4-bis).

➡ **C'est un préalable au mécanisme ⑥, et il touche le registre des transactions : un audit à part, avant tout code.** Il porte sur les
gestes créer / supprimer une transaction, la détection d'une suppression par la nuit, et le sens de `present_in_hektor` pour chaque lecteur.

### 36.6 Audit corrigé *(27/10, Frédéric : « nous enregistrons bien la transaction au geste dans notre app, on attend juste la confirmation pour y ajouter l'id de Hektor, mais nos transactions sont portées par leur propre id »)*

**Frédéric a raison, et c'est mesuré.** Nos transactions existent **dès le geste**, sous **notre** numéro (`app_affaire_id` ≥ 1 000 000),
et le numéro Hektor n'est ajouté qu'à la confirmation. **341** transactions sont nées dans l'app depuis le 25/08 (147 offres,
124 compromis, 70 ventes) ; toutes sont confirmées aujourd'hui. Leur existence ne dépend donc pas de Hektor.

**La dépendance tient à UNE condition, dans UNE vue** : la vue des liens d'un contact (`app_contact_relations_current`, 2ᵉ branche) ne
garde que `p.transaction_presente`, c'est-à-dire `present_in_hektor`. C'est le seul lecteur qui **filtre** dessus. Les fonctions de la table
des parties ne font que tenir la colonne à jour, et la sentinelle `app_v_affaire_partie_ecarts` ne fait que la comparer.

**Le projet a DÉJÀ la bonne règle, indépendante de Hektor**, dans `app_geste_affaire_optimistic` (le verrou d'une offre). Une transaction
est **vivante**, sauf si elle porte un numéro Hektor **et** qu'elle n'est plus chez Hektor :
`NOT (btrim(coalesce(l.hektor_affaire_id, '')) <> '' AND l.present_in_hektor IS FALSE)`.
- née chez nous, pas encore confirmée (sans numéro Hektor) → **vivante** ✅ ;
- confirmée → **vivante** ✅ ;
- supprimée (le geste « Supprimer » la passe à `false`) ou retirée chez Hektor, avec son numéro → **hors du compte** ✅ (les 17 d'aujourd'hui).

**Le correctif** : dans la vue, remplacer `p.transaction_presente` par **cette même règle** (la vue joint déjà `l`). C'est un seul
changement, sur la règle que le projet applique déjà ailleurs.
- **Aujourd'hui, il ne change aucune ligne** : les 341 sont confirmées, et les 17 retirées ont leur numéro.
- **Demain**, une transaction créée dans l'app apparaît **au clic** dans la fiche contact (P2) **et** dans le type (⑥).
- **Après la coupure**, elle n'aura jamais de numéro Hektor, et elle comptera quand même.

⚠ **Le seul cas qui restera à régler, à la coupure (étape 3)** : une transaction **née chez nous et supprimée avant d'avoir un numéro
Hektor**. Le geste « Supprimer » ne pose aujourd'hui que `present_in_hektor = false` : sans numéro, la règle la croirait vivante. Il lui
faudra un marqueur de suppression à nous (comme `retire_le` pour les liens). C'est rare aujourd'hui (supprimer passe par Hektor, qui exige
son numéro) ; noté pour l'étape 3, **pas un préalable**.

**L'ordre, corrigé** :
1. **ce correctif de la vue** (patch + inverse + répétition, éprouvés dans une transaction annulée, avec le même témoin de vitesse que
   P2) ;
2. **puis ⑥** (« à recalculer » marqué par nos registres, recalcul chaque minute, conflits signalés).

## 37. ✅ P3, LE PRÉALABLE CODÉ — LA VUE COMPTE LES TRANSACTIONS « VIVANTES CHEZ NOUS » *(27/10, Frédéric : « oui, et explique-moi »)* — NON POSÉ

**Les fichiers** : `supabase/patch_p3_transactions_vivantes_chez_nous_2026-10-27.sql` (+ `_INVERSE`, `_REPETITION`).

**Le changement, une seule condition** : dans la 2ᵉ branche de `app_contact_relations_current` (les acheteurs), `p.transaction_presente`
(« présente chez Hektor ») devient la règle « vivante » que le projet applique déjà dans `app_geste_affaire_optimistic` :
`NOT (btrim(COALESCE(l.hektor_affaire_id, '')) <> '' AND l.present_in_hektor IS FALSE)`.
- Ancre d'une seule ligne, trouvée une fois ; empreinte de départ = celle de P2 (`0021f0f1…`).
- Les 20 colonnes, `security_invoker` et les droits sont gardés.
- L'inverse reprend `create or replace` (mêmes colonnes) et **exige l'empreinte de P2**.

**Éprouvé dans UNE transaction annulée** (pooler, 27/10), patch → répétition → inverse → contrôle de l'inverse :

| contrôle | résultat |
|---|---|
| 20 colonnes, `security_invoker`, droits inchangés | OK |
| la vue lit la règle « vivante », plus « présente chez Hektor » | OK |
| la vue d'avant (P2) se reconstitue à l'octet | OK |
| **aujourd'hui, la vue entière rend les mêmes lignes**, dans les deux sens | OK (167 846 lignes) |
| **une vraie transaction rendue « née chez nous »** (sans numéro Hektor) : l'acheteur **apparaît**, la vue d'avant le cachait | OK (affaire 1001409) |
| la même rendue « supprimée » (avec numéro, plus chez Hektor) : **hors du compte**, comme avant | OK |
| l'essai sur la vraie transaction n'a rien laissé (sous-bloc toujours annulé) | OK |
| fiche de JACQUIER, commercial | 130,2 ms |
| fiche de JACQUIER, admin | ⚠ 1er passage **305,8 ms** (rouge, seuil 200) ; **relancé deux fois : 31,7 et 31,5 ms** (verts) |
| l'inverse rend l'empreinte de P2, les 20 colonnes et le commentaire sans P3 | OK |

- Le rouge du 1er passage est le même motif que pour P2 : le premier passage juste après le changement de la vue, quand Postgres refait ses
  plans. Il ne se reproduit pas.
- **Avaries volontaires** : une empreinte faussée **arrête** le patch ; une règle volontairement fausse (qui oublie les transactions nées
  chez nous) est **attrapée** par la répétition (n° 4). La base est intacte après chaque essai : aucune transaction sans numéro ni d'essai.

**Ce que ça change, concrètement** :
- **aujourd'hui** : rien (0 ligne de différence) ;
- **dès la pose** : une offre, un compromis ou une vente créés dans l'app font apparaître l'acheteur **au clic** dans la fiche contact (P2),
  sans attendre Hektor ; et demain dans son type (⑥) ;
- **après la coupure** : idem, sans numéro Hektor.

⬜ **Reste** :
1. **poser** (accord de Frédéric), puis la répétition ;
2. **⑥** : le type marqué « à recalculer » par nos registres, recalculé chaque minute, conflits signalés ;
3. **à l'étape 3** : le marqueur de suppression à nous, pour une transaction supprimée avant son numéro Hektor (§36.6).

## 38. LA SUPPRESSION D'UNE TRANSACTION — audit, et la meilleure solution *(27/10, Frédéric : « d'abord audit, et cherche si c'est la seule et meilleure solution »)* — lecture seule, rien codé

### 38.1 Ce que fait le projet aujourd'hui (code lu)
1. **L'écran** refuse **tout** geste sur une transaction **sans numéro Hektor** : refuser, accepter, annuler et supprimer
   (`App.tsx` l. ~18686, « Cette transaction n'a pas encore de numéro Hektor : le geste ne peut pas partir »).
2. **Au clic**, `app_geste_affaire_optimistic` (« supprimer ») :
   - passe la transaction à `present_in_hektor = false` : elle disparaît de la fiche **tout de suite** ;
   - fait redescendre le statut de l'annonce, et l'écrit aussi au **carnet de l'annonce** (`app_annonce_champ_app`, « survit à la coupure »).
   ⚠ La fonction, elle, **n'exige pas** de numéro Hektor : seule la porte de l'écran le fait.
3. **Le worker** (`handleDeleteHektorCompromis` / `…Vente`) :
   - exige le numéro Hektor, sinon il s'arrête net ;
   - vérifie que la transaction existe chez Hektor, la supprime, puis **vérifie qu'elle n'y est plus**. C'est la preuve.
4. **Avec la preuve** : il inscrit la suppression au **journal `app_affaire_supprimee`** (`origine = geste_app`, preuve, auteur, date ;
   25 lignes, jamais effacées), **puis efface la ligne** du registre en ligne. La nuit (`appliquer_les_suppressions`, `affaire_ledger.py`)
   lit ce journal et efface la ligne locale.
   ➡ C'est la **décision de Frédéric du 07/09** : « si suppression, la ligne doit ENTIÈREMENT DISPARAÎTRE de mon serveur et de mon app ».
5. **Refus ou preuve manquante** : le worker **remet** la transaction présente (`restaurerEtatAffaire`), sauf si l'envoi doit être rejoué.
6. **Ce que Hektor supprime dans son coin** : la nuit le découvre et **garde la ligne**, marquée absente (delete-never). On ne sait pas
   pourquoi elle a disparu.

### 38.2 Le « trou » que je craignais existe-t-il ? Non, pas aujourd'hui
Avec le correctif « vivante chez nous » (§37), une transaction supprimée ne réapparaîtrait que si elle était **supprimée sans numéro
Hektor**. Or **l'écran l'interdit**. Toute transaction supprimée a donc son numéro Hektor, et la règle l'écarte bien. **Le correctif du
§37 est complet tel quel pour aujourd'hui.**

⚠ **Un défaut voisin, qui existe déjà sans mon correctif** (à noter, pas à corriger ici) : si la suppression passait **avant** la
confirmation de la création, la confirmation (`poserIdTransactionSurAffaire`) remettrait la transaction présente sans condition. Elle
ressusciterait. L'écran l'empêche aujourd'hui ; la fonction de la base, non.

### 38.3 Les solutions comparées (pour la coupure)
| solution | conforme au 07/09 (« disparaît entièrement ») | survit à la coupure | ce qu'elle touche | verdict |
|---|---|---|---|---|
| ① une colonne neuve « supprimée le » sur la transaction | ✗ (la ligne reste, une 2ᵉ façon de supprimer) | ✓ | registre + fonction + vue | **non recommandée** : elle double le journal et contredit la décision |
| ② écrire au journal **au clic** | ✗ (le journal veut dire « Hektor a confirmé, preuve à l'appui » ; la nuit effacerait avant l'accord) | ✓ | sens du journal | **non** |
| ③ **ne rien ajouter aujourd'hui** ; l'écran bloque déjà le cas | ✓ | (voir ④) | rien | **oui, aujourd'hui** |
| ③ bis : **la même garde dans la fonction de la base** (« pas de geste sans numéro Hektor ») | ✓ | — | une ligne dans `app_geste_affaire_optimistic` | **recommandé** : ferme aussi la porte des autres appelants et la résurrection du §38.2 |
| ④ **à la coupure** : la suppression se fait **chez nous**. La fonction fait elle-même ce que fait le worker après la preuve : inscrire au journal (`origine = geste_app`, preuve « suppression locale »), puis effacer la ligne | ✓ | ✓ | la fonction, et la garde de l'écran | **oui, à l'étape 3** |

⭐ **Pourquoi ④ et pas une colonne** : le projet a déjà son mécanisme de suppression, décidé par Frédéric et rodé (le journal plus
l'effacement). À la coupure, il ne manque qu'une chose : que **la preuve ne vienne plus de Hektor**, mais du geste lui-même. On ne crée pas
une seconde façon de supprimer.

⚠ **Et la coupure demandera plus que la suppression** : la garde de l'écran bloque **tous** les gestes sur une transaction sans numéro
Hektor. Après la coupure, aucune n'en aura. Refuser, accepter, annuler et supprimer seraient donc **tous** impossibles. C'est un chantier
de l'étape 3 : **les gestes sur les transactions sans Hektor**.

### 38.4 La recommandation
1. **Poser le correctif de la vue du §37 tel quel** : il est complet pour aujourd'hui.
2. **En option, à ton « vas-y »** : la garde « pas de geste sans numéro Hektor » **aussi dans la fonction de la base**, et pas seulement à
   l'écran. Une ligne, avec son essai.
3. **Noter pour l'étape 3** : les gestes sur les transactions sans Hektor (④ pour la suppression, et la garde de l'écran à revoir).

## 39. ✅ POSÉS EN BASE LE 27/10 (accord de Frédéric : « pose les deux ») — et pourquoi le type Notaire n'est toujours pas visible

### 39.1 Le correctif de la vue « transactions vivantes chez nous » (§37) — POSÉ
- **Posé par moi**, par le pooler. L'empreinte de la vue passe de `0021f0f1…` à **`8c4d28d3…`**.
- **Répétition** : les 9 contrôles de fond sont verts. La vue entière rend les mêmes 167 846 lignes ; une transaction rendue « née chez nous »
  fait apparaître l'acheteur ; une transaction « supprimée » reste hors du compte ; l'essai n'a rien laissé.
- ⚠ **Le temps de la fiche admin a rougi** dans la répétition (277 ms, puis 430 ms, puis vert au 3ᵉ passage). Mesuré **seul**, 5 fois sur
  3 contacts : **32 à 48 ms**. Seule la **toute première** lecture d'un contact, à froid, monte à 200-277 ms. Le commercial reste stable
  à 130 ms.
  ➡ Ce n'est **pas** une régression : dans la répétition, la mesure admin vient juste après la comparaison de la vue **entière**, qui
  vide le cache. ⬜ À améliorer dans le banc (mesurer avant la comparaison).

### 39.2 La garde « pas de geste sans numéro Hektor » dans `app_geste_affaire_optimistic` (§38) — POSÉE
Fichiers : `supabase/patch_p3_garde_geste_sans_numero_hektor_2026-10-27.sql` (+ `_INVERSE`, `_REPETITION`).
- **Le changement** : 4 lignes, juste avant `etat_avant := a.state;`, après les contrôles existants (droits, genre, verrou de l'offre,
  « déjà dans cet état »). Elles portent le **même message que l'écran**. Propriétaire, droits et `SECURITY DEFINER` sont gardés.
- **Éprouvée dans une transaction annulée**, puis **posée**, puis répétée : **6/6 verts**.
  - sans numéro Hektor : le geste est **refusé** (compromis 1000322, sous le compte de Frédéric) ;
  - avec son numéro : il **passe comme avant** (travail créé, état posé), le tout annulé ;
  - **rien n'en reste**, vérifié aussi de façon indépendante : 0 travail d'annulation en 30 min, le compromis 1000322 intact (`active`,
    50056, présent), 0 transaction sans numéro.
- **Témoin inverse** : la répétition jouée **sans** la garde donne « PASSE » au contrôle 4. Sans elle, le geste partait bien sur une
  transaction sans numéro. **Avarie d'empreinte** : le patch s'arrête.
- ⚠ **Un premier banc était faux**, et je l'ai vu : il avait choisi un compromis suivi d'une vente, que la fonction refusait **avant** la
  garde, pour une autre raison (« compromis verrouillé par sa vente »). Le témoin a été resserré (aucune vente dans son dossier).
- **Retour arrière** : `_INVERSE.sql` (il exige de retrouver l'empreinte `a6569229…`).

### 39.3 Pourquoi le type Notaire n'est toujours pas visible *(Frédéric, 27/10)* — mesuré
**Ce n'est pas une panne : il n'a jamais été construit.** La décision « faire vivre le type Notaire » (C, §29.3) a été posée le 27/10, sans
réponse. Ensuite, on a fait la maquette de la fiche (v2 validée comme base), puis P2 et P3. Rien n'a été codé pour le type.

Les notaires **existent** chez nous : dans la table des parties, `notaire_vendeur` (16 573 lignes, **886** contacts) et `notaire_acquereur`
(6 778 lignes, **882** contacts). **1 110** sont dans l'annuaire. Mais **quatre maillons** manquent, tous mesurés :

| maillon | aujourd'hui | ce qu'il faudrait |
|---|---|---|
| **la vue des liens d'un contact** | elle ne prend dans la table des parties **que** `role = 'acquereur'` : aucun notaire n'y figure (0 ligne) | une branche de plus : les notaires (`notaire_vendeur`, `notaire_acquereur`), avec la même règle « vivante » |
| **le type stocké** | **0** contact a un rôle notaire dans son type : ni la nuit ni la relecture ne le calculent | il viendrait de la vue (⑥, « à recalculer »), ou du calcul de nuit |
| **l'écran** | `contactDirectoryCategories` ne connaît que **Mandant, Acheteur, Propriétaire, Acquéreur** ; pas de catégorie Notaire, pas de bouton dans l'annuaire. Le menu « Rôle contact » propose `notaire_entree` / `notaire_sortie`, des mots qui ne correspondent à rien | une catégorie « Notaire » (rang, couleur bleu encre, symbole balance), un bouton dans l'annuaire, le menu corrigé (`notaire_vendeur` / `notaire_acquereur`) |
| **la fiche notaire** | maquette v2 validée, rien de codé | à coder après le type |

⚠ **Ce que ça pourrait casser**, et qu'il faudra auditer :
- dans la fiche contact (P2), un notaire listerait **tous** ses dossiers (des centaines pour certains) : c'est la vocation de la fiche
  notaire, pas de la fiche contact ;
- le **rang** du type : un notaire qui est aussi propriétaire, que montre-t-on en premier ?
- le temps de la fiche et de l'annuaire, avec 23 351 lignes de plus dans la vue.

⬜ **À trancher par Frédéric** : on ouvre le type Notaire ? (Les quatre maillons, dans cet ordre : la vue, le type, l'écran, puis la fiche.)

## 40. LE TYPE NOTAIRE — AUDIT DES QUATRE MAILLONS *(27/10, Frédéric : « on ouvre le type Notaire ; commence par l'audit des quatre maillons (vue, type, écran, fiche), sans rien coder »)* — lecture seule

### 40.1 Maillon 1 — la vue des liens d'un contact
- **La source existe** : la table des parties porte `notaire_vendeur` (16 573 lignes) et `notaire_acquereur` (6 778 lignes). Cela fait
  **23 351 lignes pour 1 330 notaires**, toutes sur des transactions vivantes (11 637 compromis, 11 713 ventes, 1 offre).
- **La vue ne les prend pas** : sa 2ᵉ branche filtre `p.role = 'acquereur'`.
- **Le volume par notaire** : médiane **2** lignes, **50 notaires au-delà de 100**, 3 au-delà de 500 ; le plus chargé en a **810** (410
  biens). Lu sans les règles d'accès : **93 ms** pour ce notaire. ⬜ À mesurer sous le compte d'un commercial (avec la RLS, ×3 à ×4).
- **Le recouvrement** : 20 notaires sont aussi liés à un bien (mandant ou propriétaire), 15 sont aussi acheteurs, aucun n'a de recherche
  active.
- **Ce que la branche toucherait** :
  - `loadContactRelations` (la fiche, P2) : les lignes « Notaire » apparaîtraient ; le regroupement les range en famille « autre »,
    il faut leur donner un libellé et une couleur ;
  - `loadAnnonceContactInvitees` (les invités d'un RDV) : le notaire de l'annonce deviendrait invitable. ⬜ C'est sans doute souhaitable
    (signature), à confirmer ;
  - `loadAnnonceMandants`, `app_contact_activite` : intouchés, ils filtrent sur leurs rôles ;
  - le bon de visite : intouché.

### 40.2 Maillon 2 — le type stocké
- **0 contact** a un rôle notaire dans son type. Le calcul de nuit (`load_relations`) ne lit aucun notaire, alors que le miroir les
  connaît (registre local : `notaire_mandant_id`, `notaire_acquereur_id`).
- **Deux chemins possibles** :
  - **(a)** apprendre les notaires au calcul de nuit (Python) ;
  - **(b) ⭐ les tirer de nos registres**, par le mécanisme ⑥ (« à recalculer », §36.4) : la vue ajoutée au maillon 1 suffit, sans Python.
    ⭐ C'est le même chemin que pour tous les autres types, et il survit à la coupure.
- **L'annuaire** : 1 110 notaires y sont déjà, par l'élargissement de nuit (`elargir_perimetre_console.py` lit les notaires de la
  console). **220** restent sur le serveur : l'élargissement lit la console, pas la table des parties.

### 40.3 Maillon 3 — l'écran (tous les endroits relevés)
| endroit | aujourd'hui | à faire |
|---|---|---|
| `ContactDirectoryType` et `contactDirectoryCategories` (l. ~39191) | mandant, propriétaire, acheteur, acquéreur | ajouter **notaire**, à son rang |
| `contactDirectoryTypeLabel` | 4 mots | « Notaire » |
| en-tête de la fiche V2 (`typeClass`, `categoryColor`, l. ~44757) | 4 couleurs, 4 symboles | `ty-notaire` (bleu encre, balance), déjà dessiné dans la maquette v2 |
| cartes de l'annuaire (`ci-av has-sym`, `ci-role`, l. ~46118) | 4 symboles | le symbole et la pastille « Notaire » |
| ton du téléphone et de la pastille (P1, `contactToneFromRoles`) | le ton `notary` existe déjà, jamais atteint | le relier à la catégorie |
| filtre par rôle (`applyContactRoleFilter`, `api.ts` l. ~2549) et ses **deux menus** (l. ~24071, ~24810) | `notaire_entree` / `notaire_sortie`, **ne trouvent personne** | « Notaire », qui vise `notaire_vendeur` **et** `notaire_acquereur` |
| recherche globale (`rolesContact`) | 4 mots | « Notaire » |
| fiche contact, lignes de biens (P2) | — | libellé « Notaire — côté vendeur / acquéreur », et sa couleur |

### 40.4 Maillon 4 — la fiche notaire (maquette v2) : ce que les données permettent
| bloc de la maquette | la donnée | état |
|---|---|---|
| dossiers en cours, les 4 étapes | compromis vivants sans vente (125 dans toute l'agence aujourd'hui) | ✅ |
| date d'acte prévue | `date_acte` réelle sur **10 436 / 10 640** compromis | ✅ |
| fin de rétractation | `date_fin_retractation` réelle sur **340** seulement (champ récent) | ⚠ partiel |
| condition de prêt (échéance) | **aucune colonne** | ⛔ absent |
| séquestre | renseigné sur **1** compromis | ⛔ quasi vide |
| honoraires, net vendeur, prix | `honoraires_entree`, `prix_net_vendeur`, `montant` | ✅ |
| côté (vendeur / acquéreur) et confrère (le notaire d'en face) | les rôles de la table des parties, sur la même transaction | ✅ |
| ventes signées et délai compromis → acte | la vente et le compromis de la même chaîne (`app_chaine_id`) | ✅ |
| avec nous (par agence), confrères fréquents | calculables | ✅ |
| interlocuteurs de l'étude, liste des pièces | — | ⛔ à créer |
| échanges (e-mails, RDV) | existants | ✅ |

### 40.5 L'ordre proposé, et les questions — À TRANCHER PAR FRÉDÉRIC
**Ordre** :
1. **la vue** : une branche « notaires », même règle « vivante » ; patch, inverse et répétition, avec le temps sous un commercial ;
2. **⑥** : le type tiré de nos registres, notaires compris ;
3. **l'écran** : la catégorie, les couleurs et symboles, le filtre et ses menus, la fiche contact ;
4. **la fiche notaire**, avec les blocs dont les données existent.

**Questions** :
(1) **le rang** : un notaire qui est aussi mandant ou acheteur (35 cas), « Notaire » en premier ?
(2) **la fiche contact** d'un notaire (jusqu'à 410 biens) : toutes les lignes, ou un résumé « Notaire sur N dossiers » en attendant la
    fiche notaire ?
(3) **les 220 notaires restés sur le serveur** : les faire entrer dans l'annuaire (l'élargissement lirait aussi la table des parties) ?
(4) **les invités d'un RDV** : le notaire de l'annonce devient invitable, d'accord ?
(5) **les blocs absents** de la fiche (condition de prêt, séquestre, interlocuteurs, pièces) : masqués pour l'instant, ou à créer ?

### 40.6 ✅ LES DÉCISIONS DE FRÉDÉRIC (27/10) — « 1. Oui 2. Trouve une solution ergonomique pour pouvoir filtrer les en cours, vendus, etc., afin de ne pas surcharger la vue. 3. NON. 4. Oui. 5. Les créer, et noté dans le front « en construction » »
1. **Rang** : **« Notaire » en premier**, même s'il est aussi mandant, propriétaire ou acheteur (35 cas). Les autres rôles suivent en
   pastilles.
2. **La fiche contact d'un notaire** : **pas toutes les lignes à plat**. Un filtre ergonomique (en cours / vendus / tous…) pour ne pas
   surcharger la vue. Proposition et maquette au §40.7.
3. **Les 220 notaires du serveur** : **NON**, ils restent sur le serveur. L'élargissement n'est pas touché.
4. **Les invités d'un RDV** : **oui**, le notaire de l'annonce devient invitable.
5. **Les blocs sans données** (condition de prêt, séquestre, interlocuteurs de l'étude, liste des pièces) : **à créer**. En attendant,
   ils sont **montrés dans l'écran, marqués « en construction »**.

### 40.7 La solution ergonomique pour ne pas surcharger la fiche (décision 2) — maquette, rien codé
**Fichier** : `maquettes/fiche-contact-biens-filtres.html`.
- Données **fictives** : 410 biens, répartis comme pour le notaire le plus chargé.
- La **vraie** feuille de la fiche contact.
- Les **puces de filtre déjà utilisées** par la fiche, dans « Activité & relation » (`fa-cx-aflt`).

**La bande « Biens & mandats liés »**, quand un contact a beaucoup de biens :
- **filtre par état**, avec les nombres toujours visibles : **En cours · Vendus · Annulés · Biens · Tous** ;
- **pour un notaire, son côté** : tous les côtés · côté vendeur · côté acquéreur ;
- **une recherche** (ville, n° de mandat, vendeur, acheteur), qui porte sur **toutes** les lignes et recompte les puces ;
- **un tri** : les plus récents, l'échéance la plus proche, le prix ;
- **10 lignes à la fois**, puis « Afficher 10 de plus », et le compte « 10 sur 386 · vendus » ;
- en pied : « Fiche notaire : en construction » (décision 5).

**Les règles proposées** :
- le filtre n'apparaît qu'à partir de **7 biens** ; en dessous, rien ne change (P2) ;
- à l'ouverture, **« En cours »** s'il y en a, sinon « Tous » ;
- **En cours** = offre ou compromis vivant sans vente ; **Vendus** = vente signée ; **Annulés** = compromis annulé ou offre refusée ;
  **Biens** = mandant ou propriétaire sans transaction ;
- le **même filtre pour tout contact** chargé (un mandant de 12 biens en profite aussi).

**Vérifiée** :
- au bureau (1440 px) : « Vendus » affiche 10 sur 386, puis 20 avec « Afficher 10 de plus » ; la recherche « firminy » recompte les
  puces (52 au total) ; le côté acquéreur ramène à 11 ; une recherche vide propose « Tout afficher » ;
- au téléphone (375 px) : aucun débordement. Les puces prennent 4 rangées : au codage, une seule rangée qui défile.

⬜ À valider par Frédéric : la maquette, et les règles (le seuil de 7, « En cours » à l'ouverture, les 4 états).

### 40.8 ⛔ Correction (27/10, Frédéric : « non, je voulais que la page ressemble plutôt à ta maquette fiche-notaire-v2 ») — maquette v3
J'avais appliqué la décision 2 à la **fiche contact générique** (§40.7). Frédéric veut la **page notaire de la v2**, avec le filtre dedans.
`maquettes/fiche-contact-biens-filtres.html` reste pour mémoire ; **la référence est désormais `maquettes/fiche-notaire-v3.html`**
(données fictives).

**Ce que la v3 ajoute à la v2** (tout le reste est identique) :
- **décision 2** : la bande « Ventes signées · 12 mois » devient **« Historique des dossiers »**, filtrable :
  - état : **Vendus · Annulés · Tous**, avec les nombres ;
  - côté : **tous · vendeur · acquéreur** ;
  - période : **12 derniers mois · 3 ans · depuis le début** ;
  - **recherche** (ville, n° de mandat, vendeur, acheteur, **confrère**) ;
  - tri : récents, prix, délai compromis → acte ;
  - **10 lignes à la fois**, puis « Afficher 10 de plus », avec le compte « 10 sur 386 · vendus » ;
  - les **dossiers en cours** restent en haut, en cartes, avec leurs 4 étapes. Seul l'historique, qui fait le volume, est filtré ;
- **décision 5** : les blocs sans données sont **montrés et marqués « en construction »** : Interlocuteurs ; Pièces du dossier ;
  Condition de prêt (fait du dossier, et ligne de « À venir ») ; Séquestre. La valeur affichée est « — », plus aucun chiffre inventé.

**Vérifiée** :
- au bureau : 10 sur 38 vendus en 12 mois ; « depuis le début » 386 vendus et 10 annulés ; 20 lignes avec « Afficher 10 de plus » ;
  « collet » trouve 79 dossiers ; 5 marques « en construction » ; les pastilles dans le bleu notaire ; aucun débordement ;
- au téléphone (375 px) : aucun débordement, les puces passent sur une rangée qui défile.

Le chiffre « Ventes · 12 mois » du haut est aligné sur l'historique (38).

### 40.9 ✅ DÉCISION DE FRÉDÉRIC (27/10) : « non, je préfère fiche-notaire-v2 »
**La référence de la fiche notaire est `maquettes/fiche-notaire-v2.html`**, telle quelle. La v3 (§40.8) et la maquette du filtre de la
fiche contact (§40.7) restent dans le dossier, **pour mémoire seulement : elles ne sont pas à coder**.

Ce que la v2 fait déjà pour ne pas surcharger la page (décision 2) :
- les **dossiers en cours** en cartes, avec leurs 4 étapes ;
- les **ventes signées limitées aux 12 derniers mois** ;
- « À venir » et les chiffres en tête.

La décision 5 (les blocs sans données « en construction ») s'appliquera **au codage**, sur la v2.

## 41. ✅ NOTAIRE, ÉTAPE 1 CODÉE — LES NOTAIRES DANS LA VUE DES LIENS *(27/10, Frédéric : « vas-y pour l'étape 1, éprouvé dans une transaction annulée avant toute pose »)* — NON POSÉE

**Fichiers** : `supabase/patch_notaire_etape1_vue_2026-10-27.sql` (+ `_INVERSE`, `_REPETITION`).

**Le changement**, dans la 2ᵉ branche de `app_contact_relations_current` : trois remplacements d'une ligne chacun. L'ordre compte : le
filtre d'abord, parce que les deux autres ajouts contiennent son texte.
1. le filtre prend `acquereur`, `notaire_vendeur` et `notaire_acquereur` ;
2. `role_contact` vaut le rôle de la partie pour un notaire, et reste `acquereur_<genre>` pour un acheteur ;
3. `relation_key` reçoit le suffixe `_<rôle>` **pour les notaires seulement**. La même personne a **deux rôles sur la même transaction 619
   fois** (le même notaire des deux côtés) : sans ce suffixe, les clés se répéteraient. Les clés des acheteurs restent identiques.

**Éprouvée dans UNE transaction annulée** (pooler), patch → répétition → inverse → contrôle : **12 / 12 verts**.

| contrôle | résultat |
|---|---|
| 20 colonnes, `security_invoker`, droits | OK |
| fiche de JACQUIER : admin / commercial | 32,2 ms / 130,9 ms |
| fiche du notaire le plus chargé (10166165, 811 lignes) : admin / commercial | **173,4 ms / 157,0 ms** |
| la vue d'avant se reconstitue à l'octet (seuls les 3 remplacements) | OK |
| **toutes les lignes d'avant** sont là, à l'identique, clés des acheteurs comprises | OK (167 846) |
| **les lignes neuves = exactement les notaires** de la table des parties | OK (23 351 : `notaire_acquereur`, `notaire_vendeur`) |
| aucune clé en double de plus qu'avant | OK (0 et 0) |
| le notaire 10166165 a ses deux côtés | OK (811 lignes) |
| l'inverse rend l'empreinte d'avant (`8c4d28d3…`) et le commentaire sans la marque | OK |

- Les temps sont mesurés **avant** la comparaison de la vue entière (leçon du §39.1) : aucun faux rouge « à froid ».
- **Avaries volontaires** : une empreinte faussée **arrête** le patch ; une règle qui oublie `notaire_acquereur` est **attrapée deux
  fois** (n° 7 : la vue d'avant ne se reconstitue plus ; n° 11 : 700 lignes au lieu de 811, le côté acquéreur manque). La vue est intacte
  après chaque essai.
- ⚠ **Un premier essai s'est arrêté net, et c'est la garde qui l'a fait** : une fois la vue recréée, Postgres **réécrit à sa façon** les
  deux `CASE`, sur plusieurs lignes. L'inverse ne trouvait donc plus « la forme posée », et il a refusé (tout annulé). L'inverse et la
  répétition portent maintenant **la forme rendue par Postgres**, construite par `chr(10)` (leçon 30). ⚠ Et en la recopiant, j'avais écrit
  **3 parenthèses au lieu de 4** en tête de la clé : l'ancre aurait été trouvée, mais le remplacement aurait laissé une parenthèse
  orpheline. Vu en relisant, corrigé **avant** l'essai.

**Ce que l'écran montrerait dès la pose, sans l'étape 3** (lu dans le code) :
- **la fiche contact** des 1 110 notaires de l'annuaire listerait leurs dossiers (médiane 2, jusqu'à 811). `contactDirectoryRoleLabel` ne
  connaît pas ces rôles : il afficherait le **mot brut** `notaire_vendeur`, et `relationRowClass` la couleur par défaut (orange) ;
- **les invités d'un RDV** sur une annonce incluraient son notaire (décision 4), avec le même mot brut. Ils sont limités à 24 par
  annonce, et un bien n'a que quelques notaires : personne n'en serait chassé ;
- **intouchés** : la rubrique « Contact » d'une annonce (`loadAnnonceMandants`, rôles du bien), `app_contact_activite`, le bon de visite,
  le type stocké.

⬜ **À trancher par Frédéric** : poser la vue **maintenant** (les mots bruts se verraient jusqu'à l'étape 3), ou **avec l'étape 3**
(l'écran), le même jour ? Je recommande **avec l'étape 3**.

## 42. ÉTAPE 2 (⑥) — LE TYPE TIRÉ DE NOS REGISTRES : audit détaillé et plan de code *(27/10, Frédéric : « vas-y » ; lu comme : la vue des notaires se pose avec l'étape 3, on enchaîne sur l'audit de l'étape 2)* — lecture seule, rien codé

### 42.1 Ce qui existe et que l'on reprend
- **Le modèle `rapprochement-dirty`**, en production :
  - la table `app_rapprochement_dirty` (`id`, `entity_type`, `entity_id`, `reason`, `enqueued_at` ; RLS active) ;
  - `app_enqueue_dirty(type, id, raison)`, appelée par des déclencheurs légers (`trg_dossier_dirty` :
    `AFTER INSERT OR UPDATE OF prix, statut_annonce, diffusable, type_bien`) ;
  - deux tâches pg_cron **chaque minute** qui vident par lots.
- **La sentinelle d'écart**, en production : une **vue des écarts** (`traite_le` vide tant que l'admin ne l'a pas vu), une fonction
  « marquer vu », une entrée **warning** dans `monitoring/check_gti_health.py` (patron `data.contact_modif_ecart`).
- **Le calcul** : la vue des liens d'un contact, qui donne déjà le même type que la nuit pour 62 332 contacts sur 62 339 (§34.2).
  `relation_roles_json` est un **jsonb**.

### 42.2 Ce que la nuit fait au type (mesuré, nuit du 27/10)
- **L'envoi des contacts** (`push_contacts_to_supabase.py`) renvoie la fiche **entière** de chaque contact qui a changé
  (`merge-duplicates`), type compris : **4 102 fiches** cette nuit (04:44 → 06:10). ⚠ **Sans garde, il écraserait le type tiré de nos
  registres.**
- La table des parties est réécrite pour **39 643 contacts** ; le registre des liens met à jour `last_seen_at` de ~132 800 liens ; **11**
  liens sont nés.
- ⚠ **La nuit ne connaît pas les notaires** (§40.2) : son type n'en porte jamais.

### 42.3 Le plan (base seulement, aucun Python touché, aucun redémarrage)
1. **La file** `app_type_contact_a_recalculer` (`app_contact_id` texte en clé, `raison`, `valeur_nuit`, `marque_le`). Elle est protégée par
   les règles d'accès, et seule la base y écrit.
2. **Les déclencheurs qui marquent** (quelques microsecondes : une ligne dans la file, « si elle n'y est pas déjà ») :
   - `app_relation` : création, suppression, et **modification des seules colonnes qui changent un rôle** (`present_in_hektor`,
     `retire_le`, `absent_depuis`, `source`, `origine`, `app_contact_id`, `hektor_annonce_id`, `role_hektor`), et seulement **si elles
     changent vraiment**. La mise à jour nocturne de `last_seen_at` (~132 800 liens) **ne réveille rien** ;
   - `app_affaire_partie` : création et suppression (elle est réécrite par suppression puis réinsertion) ;
   - le bien (`app_dossier_current`) : quand son **numéro de mandat** change, ses contacts sont marqués (c'est ce qui sépare « mandant »
     de « propriétaire »).
3. **La garde du type** (avant l'écriture, sur `app_contact_current`) : quand un envoi (la nuit, ou une relecture) veut **changer** le type,
   **on garde le nôtre**, on note dans la file la valeur que l'envoi voulait (`valeur_nuit`), et on marque le contact. Seule la fonction de
   recalcul passe outre la garde, par un drapeau de session. Un contact **neuf** (création) garde le type de l'envoi, puis il est marqué.
4. **Le recalcul**, toutes les minutes (pg_cron), par lots de 5 000 (≈ 0,15 s le lot ; 1,8 s pour les 62 339 contacts) : le type depuis la
   vue ; **on n'écrit que s'il change** ; on vide la file.
5. **Le conflit, signalé à l'admin** (décision de Frédéric : « on garde notre valeur, on signale juste le conflit ») : si la `valeur_nuit`
   diffère de nos registres, une ligne d'écart est écrite (contact, valeur de la nuit, notre valeur, date). La vue
   `app_v_type_contact_ecarts` alimente la sentinelle **warning** `data.type_contact_ecart`, avec un échantillon. Le geste « vu » est le
   même que pour les sœurs.
   ⚠ **On ignore une seule différence connue** : les rôles **notaire**, que la nuit ne calcule pas. Sinon, chaque nuit, chaque notaire
   renvoyé serait un faux conflit.
6. **Le premier passage** : on marque les 62 339 contacts. Le premier recalcul remet les **7 écarts** d'aujourd'hui (§34.2) et les
   **signale**.

### 42.4 Ce que ça pourrait casser, et les essais
- **Les déclencheurs existants** sur `app_contact_current` (`trg_app_contact_current_cible` avant l'écriture,
  `app_contact_saisie_modif_juge_trg` après, sur `refreshed_at`) : on ne touche ni à `refreshed_at` ni à la cible. Ordre des déclencheurs
  à vérifier, par leur nom.
- **Le temps de la nuit** : une ligne de file par contact touché, dans la même écriture. À mesurer dans une transaction annulée, en
  rejouant un lot de la table des parties et un lot d'envoi de fiches sous la clé de service.
- **Une boucle** : notre propre écriture repasse par la garde ; le drapeau de session la laisse passer, et elle ne marque rien.
- **B** (la relecture) reste en place ; sa fiche repasse aussi par la garde, sans effet puisqu'elle ne change plus le type.
- **Le moniteur** : la ligne neuve respecte les CHECK de sa table (leçon du 25/10). La tâche pg_cron se déclare.

**Essais (transaction annulée)** :
- un lien posé, retiré ou rétabli : le contact est marqué, et le recalcul donne le bon type ;
- une partie réinsérée : marquée ;
- `last_seen_at` seul : **rien** n'est marqué ;
- un envoi qui change le type : **refusé**, valeur gardée, écart écrit ;
- un envoi égal à nos registres : pas d'écart ;
- un rôle notaire seul de différence : pas d'écart ;
- le premier passage : 7 → 0 écart, et 7 signalements ;
- le temps d'un lot de nuit rejoué ;
- **témoin inverse** : garde éteinte, l'envoi écrase ;
- **mutant** : sans le filtre des colonnes, `last_seen_at` marquerait tout.

**Retour arrière** : désactiver la tâche pg_cron et la garde (un interrupteur), puis l'inverse retire tout. Le type reste celui de la
dernière écriture.

### 42.5 Questions — À TRANCHER PAR FRÉDÉRIC
(1) **la cadence** : toutes les minutes, par lots de 5 000 ?
(2) **les notaires** : ignorer cette différence connue dans les conflits (la nuit ne les calcule pas) ?
(3) **le premier passage** sur les 62 339 contacts, qui remet les 7 écarts et les signale : d'accord ?

## 43. ÉTAPE 2, LA VERSION SIMPLE « AU GESTE » — audit *(27/10, Frédéric : « mais pourquoi est-ce si compliqué par rapport aux autres écritures du projet ? » ; « audite cette idée simple et explique-moi le principe et les changements pour l'app »)* — lecture seule, rien codé

**Pourquoi le §42 était compliqué** : le type n'est pas une saisie, c'est un **résumé calculé** de plusieurs registres ; et la **nuit
réécrit la même colonne** avec son propre calcul. Le §42 voulait couvrir tous les auteurs automatiquement **sans toucher au programme
de nuit** : d'où la file, la tâche chaque minute, la garde et le signalement. **On retire la seconde particularité, et tout redevient
simple.**

### 43.1 Le principe
1. **Une seule fonction de calcul**, dans la base : le type d'un contact depuis la vue des liens (nos registres). On sait déjà qu'elle
   donne le même résultat que la nuit pour 62 332 contacts sur 62 339 (§34.2).
2. **Chaque porte de l'app qui change un rôle l'appelle**, en une ligne, à la fin de son travail : le type change **au clic**, comme les
   autres écritures.
3. **Le worker l'appelle** quand il défait un geste refusé par Hektor.
4. **La nuit n'écrit plus le type** : elle envoie le reste de la fiche, puis appelle une fois le calcul pour tous (1,8 s). C'est ainsi
   que les changements faits **dans Hektor** arrivent dans le type.

### 43.2 Les portes, mesurées
| porte (fonction de la base) | change un rôle ? | contacts à recalculer |
|---|---|---|
| `app_link_mandant_optimistic` | ✅ crée un lien | le contact |
| `app_create_mandant_contact_optimistic` | ✅ crée le contact et son lien | le nouveau contact |
| `app_unlink_mandant_optimistic` | ✅ retire un lien | le contact |
| `app_change_annonce_status_optimistic` | ✅ crée l'offre, le compromis ou la vente (acheteurs, notaires) | les parties de la transaction créée |
| `app_geste_affaire_optimistic` | ✅ seulement « Supprimer » (la transaction sort du compte) | les parties de la transaction |
| `app_modifier_affaire_optimistic` | ✅ peut changer les **notaires** | les parties **avant et après** |
| `app_edit_affaire_optimistic`, `app_affaire_commission_ecrire`, `app_attribuer_chaines_affaire` | ✗ montants, champs, chaînes | — |

**Le worker** (les retours arrière) :
| chemin | à recalculer ? |
|---|---|
| `annulerRattachementOptimiste` (Hektor refuse un rattachement) | ✅ le contact |
| `annulerRetraitOptimiste` (Hektor refuse un retrait) | ✅ le contact |
| `restaurerEtatAffaire` (Hektor refuse une suppression : la transaction revient) | ✅ les parties |
| confirmation d'un lien, numéro Hektor posé sur une transaction, effacement après preuve | ✗ le type ne change pas : le lien comptait déjà ; la transaction supprimée était déjà hors du compte depuis le clic |

**La nuit** (`push_contacts_to_supabase.py`, le seul écrivain du type aujourd'hui, §34.1) :
- elle envoie la fiche entière (`merge-duplicates`) de **4 102** contacts la nuit du 27/10 ;
- ⭐ si la colonne du type **n'est plus dans l'envoi**, un contact existant **garde la sienne** (l'envoi ne réécrit que les colonnes
  envoyées). Un contact **neuf** reçoit la valeur par défaut `[]`, puis le calcul de fin d'envoi le remplit ;
- l'**empreinte** de chaque fiche reste calculée avec le type : aucun envoi massif de rattrapage ;
- les autres écrivains de la fiche (l'outil de rattrapage de la console, les deux fonctions de création de contact) ne touchent pas
  au type, ou en posent un au départ.

### 43.3 Les changements, un par un
| où | quoi | qui le pose |
|---|---|---|
| **base** | 2 fonctions : `app_type_depuis_nos_registres(contact)` et `app_recalculer_type_contacts(contacts[])` (n'écrit que si le type change) | un patch, avec son inverse et sa répétition |
| **base** | **une ligne** dans chacune des **6 portes** | le même patch (chaque fonction vérifie son empreinte) |
| **worker** | **une ligne** dans 3 chemins de retour arrière (un appel de la fonction) | ⚠ **redémarrage des 4 services, file vide** (par Frédéric) |
| **nuit** | dans l'envoi des contacts : ne plus envoyer la colonne du type, puis appeler le calcul (tous la nuit, le seul contact à la relecture). Derrière un **interrupteur** | ⚠ le run de nuit (accord) |
| **écran** | **rien** : il lit déjà le type stocké | — |

### 43.4 Ce que l'utilisateur verra
- **Au clic** : rattacher ou retirer un mandant, saisir une offre, un compromis ou une vente, en supprimer une. Le type de la personne
  (en-tête de la fiche, pastille de l'annuaire, recherche globale) **change tout de suite**. Aujourd'hui il attend la nuit.
- **Si Hektor refuse** : le geste est défait (règle du rattachement), et le type revient.
- **Un geste fait dans Hektor** arrive le lendemain matin, comme aujourd'hui.
- ⚠ Une liste de l'annuaire **déjà ouverte** garde son affichage jusqu'à son rechargement (point 7c, « liste déjà vue »). La fiche, elle,
  se relit après le geste.
- **Les notaires** : quand la vue des notaires sera posée (étape 1), le calcul de nuit leur donnera leur rôle **dès la première nuit**,
  et la porte « modifier une transaction » le tiendra à jour. Il faudra l'étape 3 pour que l'écran l'affiche.

### 43.5 Ce que ça pourrait casser, et les essais
- **Une porte future qui oublierait sa ligne** : un essai liste les fonctions qui écrivent un lien ou une transaction, et **exige**
  qu'elles appellent le calcul (leçon « une règle à part doit être appelée par chaque porte »). Il échoue si une porte neuve l'oublie.
- **Le temps d'un geste** : ≈ 13 ms par contact (2 à 4 contacts par transaction).
- **La nuit** : 1,8 s de plus ; l'envoi reste identique, une colonne en moins.
- **L'ordre de la nuit** : le calcul doit passer **après** l'écriture des liens et des transactions. Le 27/10, l'envoi des contacts a
  fini à 06:10, après les liens (04:52) et les transactions (04:48). ⬜ À vérifier dans `run_quotidien.ps1` au codage.
- **Ce qu'on perd** : le signalement automatique « la nuit dit autre chose que nous ». On pourra l'ajouter plus tard, par un contrôle du
  matin qui compare le type calculé la nuit (base locale) au nôtre.
- **Essais** :
  - **base** : dans une transaction annulée, chaque porte appelée sous le compte de Frédéric doit changer le type ;
  - **worker** : un essai qui joue les 3 chemins ;
  - **nuit** : un essai hors ligne (la fiche envoyée n'a plus le type, son empreinte ne change pas) et un passage du calcul complet
    (7 écarts → 0) ;
  - **témoin inverse** et **mutant** : une porte sans sa ligne doit être attrapée.

### 43.6 Questions — À TRANCHER PAR FRÉDÉRIC
(1) cette version simple **à la place** du §42 ?
(2) l'ordre : la base (fonctions et 6 portes), puis la nuit, puis le worker (le seul qui demande un redémarrage) ?

## 44. « ET SI HEKTOR NE RÉPOND PLUS ? » — et le rappel de la solution retenue *(27/10, Frédéric)*

### 44.1 Quand Hektor ne répond pas (panne, délai dépassé) — lu dans le worker
- **Le type** (version simple, §43) ne dépend d'aucune réponse de Hektor : il est calculé depuis nos registres, au clic et en fin de nuit.
- **La règle de chaque geste**, elle, en dépend :
  - **rattacher un mandant** : au **premier échec**, quel qu'il soit, le worker **défait** le lien (`annulerRattachementOptimiste`), sans
    rejouer ;
  - **retirer un mandant** : au premier échec, il **remet** le lien (`annulerRetraitOptimiste`) ;
  - **refuser, accepter, annuler, supprimer une transaction** : le **filet** du 29/08 (C.4-bis) **garde l'état et rejoue** pendant
    **24 h**, 5 essais au plus (`FILET_FRAICHEUR_MS`, `FILET_MAX_TENTATIVES`). Ensuite seulement, il remet l'état d'avant ;
  - **créer une transaction** : elle reste chez nous, sous notre numéro. L'effet d'un échec du worker n'est **pas mesuré** ici.
- ⬜ **Décision à prendre** : le rattachement et le retrait d'un mandant doivent-ils avoir **le même filet de 24 h** que les transactions,
  plutôt que d'être défaits tout de suite ? C'est un changement du worker, qui demande son propre audit.

### 44.2 ⬜ Pour l'étape 3 (la coupure), à ne pas oublier
1. Les portes de l'app **posent des travaux pour Hektor**. Après la coupure, ces travaux échoueraient, et le worker **défairait chaque
   geste**. Il faudra que les portes cessent de les poser, ou que le worker les tienne pour réussis.
2. La garde de l'écran et celle de la base (« pas de geste sans numéro Hektor ») bloqueraient **tous** les gestes sur les transactions
   (§38.3).
3. La suppression d'une transaction devra se faire **chez nous** : la fonction inscrit au journal, puis efface (§38.3 ④).
4. La nuit disparaît : il ne reste que nos registres et le calcul du type au geste. **Rien à changer** pour le type.

## 45. ✅ ÉTAPE 2, LA BASE CODÉE — LE TYPE SE CALCULE CHEZ NOUS AU GESTE *(27/10, Frédéric : « oui » à la solution rappelée)* — NON POSÉE

**Fichiers** : `supabase/patch_type_au_geste_2026-10-27.sql` (+ `_INVERSE`, `_REPETITION`).

**Ce que fait le patch** :
1. **trois fonctions internes** (ni `anon` ni `authenticated` ; la clé de service et la base seulement) :
   - `app_type_depuis_nos_registres(contact)` : le type depuis la vue des liens, trié comme la nuit (`COLLATE "C"`, car la base trie en
     `en_US`) ;
   - `app_recalculer_type_contacts(contacts[])` : écrit le type **seulement s'il change**, sans toucher à `refreshed_at` ni à la cible ;
   - `app_recalculer_type_du_bien(annonce, dossier)` : tous les contacts liés au bien (ses liens, même retirés, et les parties de ses
     transactions). Il ne fait **jamais** échouer l'appelant : une erreur est notée, et il rend -1 ;
2. **une ligne dans chacune des 6 portes** (§43.2), juste avant leur sortie finale. Ancre d'une ligne, empreinte vérifiée ; droits et
   `SECURITY DEFINER` gardés. Pour « Supprimer », qui a une sortie précoce, l'ancre vise la sortie finale.

**Éprouvé dans UNE transaction annulée** (pooler) : patch → répétition → inverse → contrôle, **12 / 12 verts**.

| contrôle | résultat |
|---|---|
| 3 fonctions internes, `SECURITY DEFINER` | OK |
| les 6 portes portent la ligne, à sa place | OK |
| **témoin inverse** : sans la ligne, les 6 portes retrouvent leur empreinte d'avant | OK |
| le calcul rend le type de la nuit (2 000 contacts) | OK (2 écarts, déjà connus, §34.2) |
| le bien le plus chargé (annonce 10555) se recalcule | **9 ms** |
| un second calcul n'écrit rien | OK |
| **essai réel, RATTACHER** (contact 10000167 sur le bien 63354, sous mandat) | `["acquereur_offre"]` → **`["acquereur_offre", "mandant"]` au clic** |
| **essai réel, SUPPRIMER une vente** (1000289, acheteur 10099691) | `["acquereur_vente"]` → **`[]` au clic** |
| une annonce absurde ne fait pas échouer l'appelant | OK |
| les essais n'ont rien laissé | OK |
| **la règle des portes de demain** : toute fonction qui écrit un lien ou une transaction appelle le recalcul, sauf 5 déclarées (commission, chaînes, champs, et les deux qui tiennent la table des parties) | OK |
| l'inverse rend les 6 portes à leur empreinte et retire les 3 fonctions | OK |

Après l'annulation : les 6 portes sont intactes et il ne reste aucune fonction neuve.

- **Avaries volontaires** :
  - une empreinte faussée **arrête** le patch ;
  - une porte privée de sa ligne (« Supprimer ») est **attrapée trois fois** : n° 2 (5 sur 6), n° 8 (la vente reste dans le type),
    n° 11 (**la règle la nomme** : `app_geste_affaire_optimistic`).
- ⚠ **Deux arrêts en route, tous deux des gardes, la base intacte chaque fois** :
  1. dans la répétition, une variable de boucle `p` portait le même nom que l'alias `p` de la table des parties, et PL/pgSQL les
     confondait. Renommée ;
  2. ⭐ le **retour arrière** a refusé : deux portes (**rattacher** : 116 CR ; **retirer** : 103 CR) ont un **corps en fins de ligne
     Windows**. Mon patch retirait les CR par réflexe (leçon 30). La fonction marchait, mais elle ne retrouvait plus son empreinte
     d'avant. Le patch **ne retire plus les CR** des fonctions : les ancres tiennent sur une ligne, la ligne ajoutée ne porte qu'un LF,
     et l'inverse la retire à l'octet. ➡ **Leçon** : retirer les CR est juste pour une **ancre** ; pour le **corps** d'une fonction
     qu'on doit rendre à l'identique, c'est faux.

**Ce qui n'est pas dans ce patch** (leurs propres pas, §43.3) :
- **la nuit** : elle n'écrit plus le type, puis lance le calcul pour tous. Tant qu'elle n'est pas faite, elle réécrit le type la nuit,
  avec le même résultat pour 62 332 contacts sur 62 339 : sans dommage ;
- **les 3 retours arrière du worker**.

⬜ **Reste** :
1. **poser** ce patch (accord de Frédéric), puis la répétition ;
2. **la nuit** (`push_contacts_to_supabase.py`, derrière un interrupteur) ;
3. **le worker** (3 lignes ; redémarrage des 4 services, file vide).

### 45.1 ✅ POSÉE EN BASE LE 27/10 *(Frédéric : « vas-y »)*
- **Posé par moi**, par le pooler, avec le fichier tel quel. **Répétition : 11 / 11 verts au premier passage.**
  - les 6 portes portent la ligne ;
  - les essais réels de rattachement et de suppression sont verts, puis annulés ;
  - le calcul rend le type de la nuit ;
  - le bien le plus chargé se recalcule en 10 ms ;
  - la règle des portes de demain est verte.
- ⚠ **Ce que la répétition écrit pour de vrai** : les contrôles 5 et 6 appellent le recalcul du bien le plus chargé (annonce 10555) **hors**
  d'un sous-bloc annulé. Mesuré aussitôt : **41 contacts** sur ce bien, **aucun** parmi les 7 écarts connus. Ils sont tous égaux à nos
  registres ⇒ **aucune réécriture réelle**. ⬜ À rejouer, la répétition le refera sans dommage (elle n'écrit que si le type diffère).
- **Rien n'est resté des essais** : aucun lien d'essai, aucun travail de rattachement ou de suppression récent. Les deux contacts des
  essais (10000167, 10099691) gardent leur type d'avant.
- **À partir de maintenant**, un rattachement, un retrait, une création de mandant, un statut (offre, compromis, vente), une suppression
  ou une modification de transaction **met le type à jour au clic**.
- ⚠ **Tant que la nuit n'est pas faite** (§43.3), l'envoi de nuit réécrit encore le type. Avec le même résultat (62 332 / 62 339), et
  il l'aligne sur Hektor pour un geste que Hektor n'aurait pas encore reçu : un rattachement du jour pourrait **perdre « Mandant » à la
  nuit**, puis le retrouver au geste suivant sur ce bien. ⬜ C'est la raison de faire la nuit vite.

## 46. ✅ ÉTAPE 2, LA NUIT CODÉE — ELLE N'ÉCRIT PLUS LE TYPE, ET LE CALCUL PASSE EN FIN DE BLOC *(27/10, Frédéric : « vas-y »)* — NON POSÉE, INTERRUPTEUR ÉTEINT

**Les pièces** :
| où | quoi |
|---|---|
| `phase2/sync/push_contacts_to_supabase.py` | `rows_pour_envoi(loaded)` retire `relation_roles_json` **d'une copie** des fiches contact envoyées. L'empreinte est calculée sur la fiche entière, et l'état d'envoi enregistre `loaded`, inchangé : **aucun envoi massif**. À la relecture d'un seul contact (envoi ciblé), l'envoi appelle ensuite `app_recalculer_type_contacts` pour ce contact. Interrupteur `APP_TYPE_PAR_NOS_REGISTRES` (éteint : envoi identique). 39 lignes ajoutées, fins de ligne CRLF gardées. |
| `phase2/sync/recalculer_types_contacts.py` (neuf) | appelle `app_recalculer_tous_les_types()`. Éteint, il le dit et sort en 0 ; un échec de l'appel sort en 1 (étape facultative). |
| `run_full_pipeline.ps1` | **une étape facultative** « phase2 type des contacts depuis nos registres » (`-WorkerKey "supabase.type_contacts"`), en **fin du bloc des contacts** : après l'envoi des contacts (l. ~1408), la propagation des numéros et « contacts devenus acquéreurs ». Les registres des transactions (l. ~911) et des liens (l. ~1044) sont écrits avant. BOM et CRLF gardés ; **9 lignes** (vu en ignorant les fins de ligne : git garde ce fichier en LF) ; syntaxe PowerShell vérifiée (0 erreur). |
| `supabase/patch_type_nuit_2026-10-27.sql` (+ `_INVERSE`, `_REPETITION`) | `app_recalculer_tous_les_types()` (ensembliste, **même règle** qu'au geste, interne) et la **ligne de suivi** `supabase.type_contacts`, **copiée** de sa sœur `hektor.carnet_acquereurs` (leçon du 13/10 : un battement sans ligne part dans le vide). |

**Essais** :
- **hors ligne**, `phase2/sync/test_type_par_nos_registres.py` : **9 / 9**. Il exécute le vrai code :
  - éteint, l'envoi est identique ; allumé, les fiches partent sans le type, avec des clés uniformes (PGRST102) ;
  - les autres colonnes et les autres tables sont intactes ;
  - **l'empreinte est inchangée**, et `loaded` n'est pas modifié ;
  - **mutant** (retirer le type de la fiche locale) : attrapé ;
  - le script de fin de nuit, éteint, sort en 0 ;
- l'essai existant `phase2/sync/test_dirty_guards.py` reste vert (4/4 ; il demande `PYTHONPATH=.`) ;
- **la base, dans une transaction annulée** : **7 / 7 verts**.
  - avant le calcul, **7** contacts diffèrent de nos registres (les écarts connus du §34.2) ;
  - le calcul pour tous corrige **exactement ces 7**, en **1,6 s** ; une seconde fois, il n'écrit rien ;
  - **même règle qu'au geste** : 0 écart sur 2 000 contacts répartis dans tout l'annuaire ;
  - l'inverse retire la fonction et la ligne de suivi.
- ⚠ Ma répétition appelait d'abord le calcul d'**un** contact sur les 62 339 (plus de 13 min, le pooler coupe à 120 s) : vu en relisant,
  remplacé par un calcul d'ensemble et un échantillon de 2 000, **avant** l'essai.

⚠ **Le programme d'envoi et le pipeline sont en service dès leur écriture** : la nuit et la relecture d'un contact les utilisent. **Avec
l'interrupteur éteint, leur effet est nul** : envoi identique, et l'étape neuve dit « éteint » puis sort en 0. Rien ne change cette nuit
tant que la pose n'est pas faite.

⬜ **La pose, dans cet ordre** (accord de Frédéric) :
1. **la base** : `patch_type_nuit_2026-10-27.sql`, puis sa répétition. Elle remet les 7 écarts d'après nos registres ;
2. **l'interrupteur** : `APP_TYPE_PAR_NOS_REGISTRES=1` dans `.env`. Effet à la prochaine relecture d'un contact, et à la prochaine nuit ;
3. **demain matin** : lire le journal du run (l'étape « phase2 type des contacts depuis nos registres » et son compte) et le battement
   `supabase.type_contacts` ; vérifier que les fiches envoyées ont gardé leur type.

Ensuite : **les 3 retours arrière du worker** (§43.3, redémarrage des 4 services, file vide).

### 46.1 ✅ POSÉE LE 27/10 À 23:01 — BASE ET INTERRUPTEUR *(Frédéric : « A », les deux)*

- **Essais voisins relancés avant la pose** : `test_seconde_passe_contacts_neufs.py` 7/7 (ordre du pipeline), `test_resolution_mandat.py`
  vert, `test_type_par_nos_registres.py` 9/9. `test_c4_suppressions.py` : ses 8 contrôles sont verts. ⚠ Ses 2 « PREUVES » rougissent
  **depuis le 23/09**, car elles comparent à `HEAD`, qui porte le correctif C-4 depuis son commit (`f01217b`). Aucun lien avec ce
  changement ; noté, pas touché.
- **La base** : `patch_type_nuit_2026-10-27.sql` passé (COMMIT), répétition **6 / 6 verte du premier coup**. **7** contacts différaient
  de nos registres : les 7 sont remis, en 1 585 ms. Une seconde fois, il n'écrit rien. Sur 2 000 contacts, la nuit et le geste donnent
  le même type, **0 écart**.
- **L'interrupteur** : `APP_TYPE_PAR_NOS_REGISTRES=1` ajouté en fin de `.env` (CRLF, avec un commentaire). Sauvegarde du `.env` d'avant
  dans le bloc-notes de la session.
- **Éprouvé allumé, pour de vrai** :
  - `recalculer_types_contacts.py` répond `0 contact(s) remis d'apres nos registres, en 1.7 s`, sortie 0 (rien à faire juste après la
    pose : c'est le résultat attendu) ;
  - l'appel ciblé de la relecture (`rpc/app_recalculer_type_contacts`, clé de service) sur JACQUIER 10354352 répond `0`. Son type est
    `acquereur_compromis, acquereur_offre, acquereur_vente, proprietaire`.
- ⚠ **Pas de battement pour ces appels à la main** : seule l'étape du pipeline écrit `supabase.type_contacts`.

⏰ **Demain matin, 28/10** :
1. dans le journal du run, l'étape « phase2 type des contacts depuis nos registres » et son compte. Il doit être petit : seuls les gestes
   faits dans Hektor dans la journée, et les contacts neufs ;
2. le battement `supabase.type_contacts` (`last_status`, `last_duration_ms`) ;
3. l'envoi des contacts n'est pas reparti en masse (empreinte inchangée) ;
4. aucun contact n'a perdu un rôle que nos registres portent (refaire le compte du contrôle 3 de la répétition : il doit valoir 0).

**Retour arrière** : retirer la ligne de `.env` (effet immédiat), puis `patch_type_nuit_2026-10-27_INVERSE.sql`.
**Ensuite** : les 3 retours arrière du worker (§43.3).

## 47. ÉTAPE 2, LE WORKER — audit des écritures qui changent le type sans passer par une porte *(27/10, Frédéric : « on enchaîne »)* — lecture seule, rien codé

**La question** : les 6 portes de la base recalculent le type au clic. Mais le worker écrit aussi dans nos registres **sans passer par
elles**. Lesquelles de ces écritures changent ce que la vue `app_contact_relations_current` montre, donc le type ?

**La vue, relue en base le 27/10** :
- branche des liens : `(present_in_hektor OR (source='app' AND absent_depuis IS NULL)) AND retire_le IS NULL` ;
- branche des transactions : la partie doit être `acquereur`, et la transaction **vivante chez nous**. L'**état** (refusée, annulée…) ne
  change pas le rôle (`'acquereur_' || kind`).
- ⚠ `app_affaire_partie` **suit** `app_affaire_ledger` par 3 déclencheurs (`app_affaire_partie_suivre`, après insert, update et
  delete) : réécrire la liste des acquéreurs du registre **change les parties**.

**Les écritures du worker, une par une** (`Console/console_job_worker.js`) :
| où | ce qu'elle fait | change le type ? |
|---|---|---|
| `annulerRattachementOptimiste` (l. ~17500) | Hektor refuse un rattachement : `absent_depuis` posé | **OUI**, le lien sort de la vue (le contact perd « mandant ») |
| `annulerRetraitOptimiste` (l. ~17459) | Hektor refuse un retrait : `retire_le` remis à vide | **OUI**, le lien revient |
| `restaurerEtatAffaire` (l. ~21775), geste « supprimer » | Hektor refuse une suppression : `present_in_hektor` remis à vrai | **OUI**, la transaction redevient vivante |
| `restaurerEtatAffaire`, autres gestes | l'ancien état est remis | non (l'état ne compte pas), appel sans effet |
| `reporterAuRegistre` (l. ~15824) | après une création ou une modification, le registre reçoit **les acquéreurs et les mandants que Hektor a retenus** | **OUI, si Hektor a écarté quelqu'un en silence** : les déclencheurs changent les parties. ⭐ Ce 4e chemin n'était pas dans le §43.3 |
| marquage « lien établi » (l. ~17250) | `present_in_hektor` false → true, sur un lien de l'app sans `absent_depuis` | non (il était déjà dans la vue) |
| `retirerAffaireDuRegistre` (l. ~22874) | après la suppression **confirmée** par Hektor, la ligne du registre est effacée | non : le clic l'avait déjà rendue non vivante. Appel à ajouter quand même par prudence (coût ≈ 13 ms) |
| suppression d'un contact (l. ~21284) | ses liens sont effacés | non pour les autres contacts ; le contact lui-même disparaît |

**Le correctif proposé** : une petite fonction `recalculerTypeDuBien(job, annonceId, contexte)`, sur le modèle de l'appel déjà présent
au worker (`rpc/app_photos_remplir_adresses_app`, l. ~9841). Elle appelle `rpc/app_recalculer_type_du_bien` (droit service vérifié, et la
fonction ne fait jamais échouer). Elle **ne jette jamais** et écrit une ligne au journal. Elle est appelée après chacune des **5**
écritures marquées ci-dessus : 4 qui changent le type, plus la suppression confirmée.
- **Sans elle** : le type est faux jusqu'à la fin de la nuit suivante, où le calcul pour tous (§46) le remet. C'est donc un gain de
  délai, pas un défaut de fond.
- **Essai prévu** : un essai hors ligne qui exige l'appel après chacune des 5 écritures (le **mutant** : on en retire un, il doit rougir),
  et la fonction jouée sur un faux `supabaseRequest`.

⚠ **Coordination** : le fichier du worker porte **130 lignes non commitées de l'autre session** (signature Youtrust), écrites à 14:33,
donc **après** le redémarrage de 10:23. **Un redémarrage chargerait aussi ce code-là.** Mon commit ne prendra que mes lignes (contenu
déposé à part dans git) ; mais le redémarrage, lui, chargera le fichier entier.

### 47.1 ✅ CODÉ LE 27/10 (commit `a5b1676`) — EN ATTENTE DU REDÉMARRAGE *(Frédéric : « code le correctif, redémarre et informe juste le chat voisin »)*

- **Le code** :
  - `journalDuType`, `recalculerTypeDuBien`, `contactsDeLAffaire`, `recalculerTypeDesContacts` (avant `annulerRetraitOptimiste`) ;
  - 5 branchements : retrait défait, rattachement défait (seulement si une ligne est défaite), suppression défaite (le bien de la ligne
    **relue**), liste retenue par Hektor (parties lues **avant et après** : l'acquéreur écarté perd son rôle), suppression confirmée
    (parties lues **avant** l'effacement) ;
  - 77 lignes, aucune retirée. **Jamais bloquant** : ni la base qui refuse, ni le journal qui tombe ne lèvent d'exception.
- **Essais** : `Console/test_type_apres_ecriture_worker.js` **9 / 9**, sur le code réel découpé dans le worker. Il porte 2 témoins inverses,
  un refus de la base, une panne du journal, et un **mutant attrapé**.
  - `test_relecture_garde_nos_numeros.js` rougissait (`contactsDeLAffaire is not defined` : son bac à sable ne connaissait pas les aides).
    Je lui ai ajouté les 4 morceaux : il est vert, ses 6 contrôles inchangés. `test_controle_carnet_r3.js` est vert.
  - ⚠ `test_report_retractation.js` rougit **déjà sur la version d'avant** (`GARDER_NOS_NUMEROS_A_LA_RELECTURE is not defined`, ancien
    défaut de son bac à sable) : noté, pas touché.
- **Le commit ne porte que mes lignes** : un correctif appliqué à l'index seul. Les 130 lignes Youtrust de l'autre session restent hors
  commit, dans la copie de travail ; la session voisine est **prévenue** (message du 27/10, 23:27).
- **Redémarrage** : ⛔ **refusé à mon compte** (« Impossible d'ouvrir le service »), il revient à Frédéric.
  - **Admin, Actions et SyncLight** : file vide pour eux (0 en attente, 0 en cours, mesuré à 23:25). Ce sont eux qui portent les liens et
    les transactions.
  - **Documents** : il traitait le balayage des photos (877 en attente, 1 en cours à 23:24). **Il ne porte aucun des 5 chemins** : on le
    redémarre plus tard, file vide.
  - ⚠ Le redémarrage chargera **aussi** le code Youtrust non commité de l'autre session. Il reste derrière son interrupteur ; ses types
    `youtrust_*` sont au service Documents.
- **Preuve à faire après le redémarrage** : l'heure de départ des processus doit être après 23:22:32 (dernière écriture du fichier). Le
  premier geste défait, ou la première liste retenue par Hektor, écrit une ligne `type_des_contacts` au journal du travail.

**Décision de Frédéric (27/10, 23:30)** : *« je redémarrerai demain matin, file vide, les 4 services ensemble »*. ⏰ 28/10 au matin : comparer l'heure de départ des 4 processus à 23:22:32.

## 48. ✅ NOTAIRE, ÉTAPE 3 CODÉE — L'ÉCRAN DES NOTAIRES *(28/10, Frédéric : « oui », pendant la reprise du run)* — NON POUSSÉE, À POSER AVEC L'ÉTAPE 1

**Interrupteur** : `TYPE_NOTAIRE_ECRAN` (App.tsx). Sans rôle notaire dans les données, l'écran ne change pas. Aujourd'hui aucun contact n'en
porte : ils arriveront avec la vue de l'étape 1, puis le calcul du type depuis nos registres.

**Les changements** (maillon 3 du §40.3, décisions du §40.6) :
| endroit | ce qui change |
|---|---|
| `contactDirectoryCategories` | la catégorie `notaire`, **en premier** (décision 1) : `notaire_vendeur` ou `notaire_acquereur` |
| `contactDirectoryTypeLabel` · `contactDirectoryTypeSymbol` | « Notaire » · la balance de la maquette v2 |
| `contactToneFromRoles` | dominant notaire → le ton `notary` (téléphone, pastille), déjà libellé « Notaire » |
| en-tête de la fiche V2 | `ty-notaire` (le bleu encre `#3b4a8c` de la maquette v2), la balance dans l'avatar, pastilles en bleu |
| cartes de l'annuaire | avatar, mot et statut (« Notaire · Côté vendeur / acquéreur / côtés vendeur et acquéreur ») |
| lignes de biens de la fiche (P2) | famille `notaire`, **en premier sur la ligne** ; « Notaire — côté vendeur / acquéreur / côtés vendeur et acquéreur » ; l'étape du dossier dans le sous-titre, même règle que l'acheteur (la vente si elle existe, sinon la plus récente ; compromis annulé ou offre refusée **en gris**) ; ligne bleue `r-notaire` |
| filtre de l'annuaire (2 menus) + `contactRoleFilterValues` (`lib/api.ts`) | « Notaire entrée / sortie », qui ne trouvaient personne, devient « Notaire », qui vise **les deux côtés** |
| recherche globale (`RechercheGlobale.tsx`) | « Notaire » en premier |
| styles (`annuaire-contacts-v2.css`, `contact-detail-v2.css`) | avatar, mot et statut de l'annuaire ; variables `ty-notaire`, balance, `r-notaire` |

Les invités d'un RDV (décision 4) : rien à coder. La vue de l'étape 1 suffit, et le libellé passe par `contactDirectoryRoleLabel`.

**Essais** :
- `apps/hektor-v1/test_notaire_ecran.cjs` : **22 / 22**. Il exécute le code réel (App.tsx, `lib/api.ts`, `RechercheGlobale.tsx`) et
  contrôle le rang, le ton, les mots, les lignes de biens (vente retenue, deux côtés, annulé en gris, ordre reçu indifférent), le filtre, la
  recherche globale, les menus et les styles. **Témoin inverse** : un contact sans notaire donne le même écran, allumé comme éteint.
  **Mutant** (sans « notaire en premier ») : attrapé.
- `test_fiche_un_bien_tous_roles.cjs` et `test_type_contact_unique.cjs` rougissaient : leur bac à sable ne connaissait pas les nouvelles
  aides. Elles leur sont ajoutées ; ils sont verts, leurs contrôles inchangés.
- `npm run build` : vert.
- ⬜ **Pas vu à l'écran** : aucune donnée ne porte encore de rôle notaire. À voir au bureau et au téléphone **après la pose de l'étape 1**.

⚠ **Ce qui reste à trancher (décision 2)** : jusqu'à la fiche notaire (étape 4), la fiche contact d'un notaire liste **tous ses biens à
plat**, jusqu'à 410 pour le plus chargé. La décision 2 dit « pas toutes les lignes à plat ».

⬜ **La pose, dans cet ordre, avec l'accord de Frédéric** :
1. **rejouer l'essai de l'étape 1 dans une transaction annulée**. La base a changé depuis l'essai du 27/10 : le type au geste et le calcul
   pour tous lisent cette vue ;
2. poser la vue (étape 1) et sa répétition. Au prochain calcul du type (la nuit, ou `app_recalculer_tous_les_types`), les 1 110 notaires de
   l'annuaire reçoivent leur rôle ;
3. pousser le front (Frédéric) ;
4. voir l'écran, au bureau et au téléphone.

### 48.1 ✅ DÉCISION 2, CODÉE *(28/10, Frédéric : « A : au-delà de 10 biens, montrer les 10 plus récents et un bouton « Tout afficher » »)*
- `indicesBiensAffiches` (App.tsx) : pour un contact **dont la catégorie dominante est « Notaire »** et qui a **plus de 10 biens**, les
  **10 plus récents** (la date de transaction la plus récente du bien), du plus récent au plus ancien. Un bouton
  « **Tout afficher · N biens** » montre les autres, dans le même ordre. Il revient replié quand on change de contact.
- **Hors notaire, ou à 10 biens et moins : rien ne change** (tous, dans l'ordre d'avant).
- ⚠ Les biens **gardent leur numéro** : la fonction choisit lesquels montrer, elle ne réordonne ni `linkedRelations` ni le
  regroupement de P2. Les deux fiches (V1 et V2) parcourent les numéros choisis. Le nombre de biens de l'en-tête reste le total.
- Essais : `test_notaire_ecran.cjs` **28 / 28**. 6 contrôles neufs : les 10 bons biens, numéros alignés, lignes mélangées ;
  « Tout afficher » ; les deux témoins ; les deux fiches ; **mutant** sans la limite, attrapé. P2 et le type unique restent verts.
  `npm run build` (vérification des types comprise) vert.

### 46.2 ⚠ LA 1RE NUIT (run relancé le 28/10, reprise de 08:48) — l'étape a échoué sur un chemin, corrigé *(28/10)*
- **L'envoi des contacts sans le type** : 09:28:12 → 09:28:50, soit **38 s**, contre 35 s la veille. **Pas d'envoi massif** : l'empreinte
  est inchangée, comme prévu.
- **L'étape « phase2 type des contacts depuis nos registres »** : `exit 2` à 09:29:16. Python : `can't open file '...phase2\sync<CR>ecalculer_types_contacts.py'`.
  En insérant la ligne du pipeline par une chaîne Python non brute, le `\r` de `\recalculer` est devenu un **retour chariot**. C'est ma
  faute, et mon essai ne l'a pas vu : il vérifiait la syntaxe et le diff, sans **exécuter** l'étape. Le même caractère faisait classer le
  fichier « non texte » par git (§46).
- **Corrigé** (commit `a9e0d55`) : un octet, plus aucun retour chariot isolé, syntaxe vérifiée. L'étape étant facultative, le run a continué.
- **Rattrapé à 09:30:57** : `recalculer_types_contacts.py` lancé à la main remet **15 contacts** d'après nos registres, en 16,7 s. Ce sont
  les gestes faits chez Hektor, que le run venait d'écrire dans nos registres, et les contacts neufs.
- ⚠ Le battement `supabase.type_contacts` reste en **erreur** (09:29) jusqu'au run de cette nuit.
- ⏰ **Cette nuit** : l'étape doit sortir en 0, avec un compte de quelques contacts.

### 48.2 ✅ L'ÉTAPE 1 REJOUÉE (28/10, 09:55), APRÈS LE TYPE TIRÉ DE NOS REGISTRES — rien posé
- **L'essai de l'étape 1, dans une transaction annulée** : **12 / 12**.
  - Temps de lecture : fiche de JACQUIER 46 ms (admin) et 134 ms (commercial) ; le notaire le plus chargé (810 rôles) 150 ms et 158 ms.
  - Les 167 862 lignes d'avant sont identiques ; 23 355 lignes neuves, exactement les notaires de la table des parties (23 351 la veille).
  - L'inverse est propre, et la vue est intacte après l'annulation.
- **L'effet sur le type, mesuré dans une transaction annulée** :
  - **1 110 contacts** recevraient leur rôle de notaire : ce sont les notaires de l'annuaire (§40.2). Aucun autre contact ne bouge.
  - Le calcul pour tous les écrit en **2,6 s**. Au geste, le type du notaire le plus chargé se calcule en **12 ms**.
  - **0 écart** restant ; rien n'est gardé après l'annulation.
- **Le front déployé** (groupe-gti.vercel.app, après la poussée de Frédéric) contient l'étape 3 et la décision 2.
- ⬜ **La pose, avec l'accord de Frédéric** : `patch_notaire_etape1_vue_2026-10-27.sql` et sa répétition, puis le calcul pour tous
  (`recalculer_types_contacts.py`), pour que l'écran les montre tout de suite. Ensuite : la vérification à l'écran, au bureau et au téléphone.

### 48.3 ✅ POSÉE LE 28/10 À 10:29 — la vue des notaires, puis le type ; VU À L'ÉCRAN *(Frédéric : « oui vas-y »)*
- **La vue** : `patch_notaire_etape1_vue_2026-10-27.sql` passé (COMMIT), répétition **11 / 11 verte du premier coup**. Les temps de lecture
  restent au plus 159 ms (le notaire le plus chargé, sous un commercial : 156 ms) ; 167 862 lignes d'avant identiques, 23 355 neuves.
- **Le type** : `recalculer_types_contacts.py` à 10:29:36 remet **1 110 contacts en 2,7 s**, exactement la mesure de l'essai.
  - Exemple : le notaire le plus chargé, 10166165 « Pierre office notarial Ambert », porte
    `notaire_acquereur, notaire_vendeur, proprietaire`.
- **Vu à l'écran**, dans le Chrome de Frédéric (front déployé) :
  - **l'annuaire** (recherche « office notarial Ambert ») : avatar bleu avec la balance, « Notaire · Propriétaire », statut « Notaire ·
    Côtés vendeur et acquéreur » ;
  - **la fiche** : `ty-notaire`, la balance dans l'avatar, les pastilles « Notaire » et « Propriétaire », 411 biens ;
    - **10 lignes**, du plus récent (« Compromis du 13/01/2026 ») au plus ancien (« Vente signée le 16/12/2024 »), toutes
      « NOTAIRE — CÔTÉS VENDEUR ET ACQUÉREUR » ou « — CÔTÉ ACQUÉREUR », ligne bleue `#3b4a8c` ;
    - le bouton « **Tout afficher · 411 biens** » montre les 411 puis disparaît ; le bien sans transaction (propriétaire) arrive en dernier ;
  - **le téléphone** (cadre de 390 px, rendu mobile) : cartes `is-notary` « Notaire » ; la fiche avec la balance, « Notaire · Propriétaire »
    et « Tout afficher » ; aucun débordement (386 px).
- ⚠ **Trouvé à l'écran, et que mon audit n'avait pas** : l'annuaire affiché ne filtre pas par les menus « Rôle contact » (les deux que
  j'avais modifiés), mais par une **rangée de pastilles** (Tous · Propriétaires · Mandants · Acheteurs · Acquéreurs). Aucune pastille
  « Notaires » n'existait : c'est encore la leçon « vérifier QUEL composant s'affiche ».
  - **Ajoutée** : la pastille « Notaires » (point bleu), qui choisit le même filtre `notaire` (les deux côtés).
  - Essai : `test_notaire_ecran.cjs` **29 / 29** ; P2 et le type unique restent verts ; build vert.
  - ⬜ À pousser par Frédéric, puis à voir à l'écran.
- **Retour arrière** : `patch_notaire_etape1_vue_2026-10-27_INVERSE.sql`, puis le calcul pour tous retire les rôles.
- ✅ **La pastille « Notaires », vue à l'écran le 28/10 à 10:42** (déploiement Vercel de 10:40:15) : un clic la rend active, l'annuaire
  compte **602 contacts**, et les 50 cartes de la page sont toutes « Notaire ».
  - Pourquoi 602 et pas 1 110 : **1 110 = 618 actifs + 492 archivés**. L'annuaire montre les actifs par défaut, comme pour tout contact.
  - Le petit reste (602 au lieu de 618) suit le même écart que l'annuaire entier : « Tous » affiche 39 496 contacts actifs, alors que la
    table en compte 39 695. C'est un filtre d'écran qui existait déjà, pour tous les contacts. ⬜ Non mesuré, noté seulement.

## 49. NOTAIRE, ÉTAPE 4 — AUDIT DE LA FICHE NOTAIRE (maquette v2) *(28/10, Frédéric : « oui, audit étape 4 »)* — lecture seule, rien codé

**Audit limité à l'objet « contact notaire » et à ses transactions (lire).** La fiche ne crée, ne modifie ni ne supprime rien de neuf :
ses boutons d'action (modifier, archiver, RDV, ouvrir dans Hektor) existent déjà dans la fiche V2.

### 49.1 Les 8 blocs de la maquette, et leur donnée (mesuré le 28/10, sur toute l'agence et sur 10166165, 411 biens)
| bloc | donnée | état |
|---|---|---|
| volet identité (nom, étude, téléphones, e-mail, adresse, négociateur) | la fiche contact | ✅ existe |
| « Interlocuteurs de l'étude » | aucune | ⛔ en construction (décision 5) |
| « Partenaire depuis » | 1re date de dossier (10166165 : 14/09/2006) | ✅ |
| chiffres : dossiers en cours, actes ≤ 30 j, ventes 12 mois et honoraires, délai compromis → acte | registre des transactions + chaînes | ✅. Médiane de l'agence : **89 jours** (626 couples compromis → vente depuis 2025) |
| dossiers en cours, en cartes avec leurs 4 étapes | compromis vivants sans vente dans leur chaîne : **123** dans l'agence, **120 notaires** concernés | ⚠ voir 49.2 |
| — dans la carte : vendeurs → acheteurs, côté, notaire d'en face, négociateur, prix, honoraires, net vendeur | table des parties, registre, parc | ✅ |
| — fin de rétractation, acte prévu | `date_fin_retractation`, `date_acte` | ✅ (rétractation : champ récent, partiel) |
| — séquestre | `sequestre` : « 0.00 » presque partout, « 8000.00 » une fois | ⚠ montré seulement s'il est non nul |
| — condition de prêt | aucune colonne | ⛔ en construction |
| — pièces du dossier (7 sur 11, envoyer à l'étude) | aucune | ⛔ en construction |
| « À venir » (rétractation, acte, condition de prêt) | les mêmes dates | ✅ sauf la condition de prêt |
| ventes signées 12 mois | **348** dans l'agence ; **0** pour 10166165 (sa dernière : 14/10/2025) | ✅ |
| « Avec nous » : dossiers par agence, côté, confrères fréquents | `agence_nom` (parc et archives), rôles des parties | ✅ calculables |
| activité & relation, qualité | composants existants de la fiche V2 | ✅ existe |

### 49.2 Ce que les mesures ont trouvé
1. **Des « en cours » fantômes** : sur les 123 compromis vivants sans vente, **36 ont une date d'acte DÉJÀ PASSÉE**, et 41 ont plus de 6 mois.
   Exemple : pour 10166165, le seul « en cours » est un compromis du **31/10/2024** (annonce 9303), sans vente ni annulation. C'est un
   dossier abandonné ou une vente jamais saisie. Sans règle, la fiche l'afficherait comme un dossier vivant.
2. **Le notaire n'est pas toujours sur la vente** : pour 11729 et 11840, il est sur le compromis (janvier 2026) mais pas sur la vente
   (avril et mars 2026). Sa fiche contact (étape 3) montre donc « Compromis du 13/01/2026 » sur un bien vendu. La fiche notaire devra
   lire **la chaîne** : la vente de la chaîne compte comme l'issue du dossier, même si le notaire n'y figure pas.
3. **Un notaire des deux côtés compte double** si l'on compte les lignes de parties : on compte par transaction.
4. **Les droits** : `app_affaire_ledger` ne montre à un négociateur que les biens de **son portefeuille** (`app_mes_biens_portefeuille`).
   Les comptes qui voient toute l'agence voient tout. Sans décision, un négociateur verrait une fiche notaire limitée à ses propres dossiers,
   et des chiffres partiels (« avec nous », confrères, médiane).

### 49.3 Où la fiche vivrait, et ce que ça pourrait casser ailleurs
- **Dans la fiche V2 existante**, quand la catégorie dominante est « Notaire » (`ty-notaire`, déjà posé) : la maquette garde le volet
  identité, l'activité et la qualité, et remplace « Recherche & rapprochement » (sans objet pour un notaire) par les blocs notaire. Un notaire
  qui a une recherche active la garderait.
- **Une fonction de lecture neuve** dans la base, en `security invoker` (les règles d'accès s'appliquent) : elle rendrait, pour un notaire,
  ses dossiers (chaîne, parties, confrère, dates, montants, agence). Le calcul se fait côté base, pas sur les 810 lignes dans l'écran.
- **Ce que ça ne touche pas** : la vue des liens, le type, le bon de visite, les autres catégories, la fiche V1. Derrière un interrupteur.
- ⚠ **La bande « Biens & mandats liés »** (10 plus récents + « Tout afficher », §48.1) : la maquette ne l'a pas, mais sans elle l'historique
  au-delà de 12 mois disparaîtrait de la fiche.

### 49.4 Questions — À TRANCHER PAR FRÉDÉRIC
1. **Les droits** : un négociateur voit-il tous les dossiers du notaire dans l'agence, ou seulement les siens ? (Aujourd'hui : les siens.)
2. **« En cours »** : un compromis vivant sans vente, **et** dont l'acte prévu n'est pas passé (ou, sans date d'acte, qui a moins de 6 mois) ?
   Les autres (36 à date d'acte passée) iraient dans un groupe « À vérifier ».
3. **L'historique** : garder la bande « Biens & mandats liés » (10 + « Tout afficher ») sous les ventes des 12 mois ?
4. **Les honoraires encaissés** : quel champ ? (`commission_agence`, `honoraires_entree`, `honoraires_sortie` sont tous remplis sur les ventes.)
5. **« Exporter »** les ventes : à coder maintenant, ou « en construction » ?

### 49.5 Les droits, MESURÉS *(28/10, Frédéric : « je ne suis pas sûr, normalement les négociateurs voient tous les biens et tous les contacts »)*
Mesuré **sous l'identité des 2 commerciaux actifs**, dans une transaction annulée (`droits_commercial.js` : la clé de l'utilisateur dans
`request.jwt.claims`, rôle `authenticated`). Les 4 autres comptes actifs sont admin et voient tout.
- **Les biens : tout.** 13 490 dossiers sur 13 490.
- **Les contacts : tout.** 62 346 sur 62 346.
- **Les transactions : seulement leur portefeuille.** 43 et 479 sur 31 117 (portefeuilles de 138 et 1 048 biens).
- **Les liens du notaire 10166165 : 1 sur 811** (le lien de propriétaire). Ses 810 lignes de notaire viennent des transactions.
- **C'est une décision écrite**, pas un oubli : le chantier ② (`notice/CHANTIER_2_DROITS_NEGOCIATEUR_2026-10-09.md`, L4.5, 12/10) a
  rangé « affaires + **commissions** » dans **« ses biens »**, et « annonces, contacts, liens, archives, vendus, photos » dans **« tout le
  réseau »**. Frédéric a raison pour les biens et les contacts ; ma phrase était juste pour les transactions.
- ⚠ **La conséquence, déjà vraie aujourd'hui** :
  - le **type** est calculé avec tous les droits et stocké dans la fiche contact, que tout le monde lit : l'annuaire dit « Notaire »
    ou « Acheteur » à un commercial ;
  - mais la **fiche** (lignes de biens de P2) ne lui montre que les transactions de ses biens. Le notaire le plus chargé y a 1 ligne
    au lieu de 411, et un acheteur hors de son portefeuille n'y a aucune ligne d'achat.
- **Question 1 reformulée** :
  - **(a)** on garde la décision du 12/10 : la fiche notaire d'un commercial ne montre que ses dossiers ;
  - **(b)** une lecture **réduite**, pour toute l'agence : dates, étapes, biens, côtés, confrères, **sans aucun montant ni honoraire**. Les
    montants restent visibles sur ses seuls biens. Elle passerait par une fonction de la base qui ne rend que ces champs.

### 49.6 ✅ DÉCISION 1 (28/10, Frédéric : « A »)
**On garde la décision du 12/10** : la fiche notaire d'un négociateur ne montre que **ses** dossiers (les transactions de son portefeuille). La fonction de lecture de la fiche notaire sera donc en `security invoker`, sous les règles d'accès actuelles : rien d'ouvert en plus. Les chiffres « avec nous », confrères et médiane seront ceux de ce qu'il voit. Questions 2 à 5 : ouvertes.

### 49.7 ✅ DÉCISIONS 2 À 5 (28/10, Frédéric : « oui, les quatre » — mes recommandations)
2. **« En cours »** : un compromis vivant sans vente dans sa chaîne, **dont l'acte prévu n'est pas passé**, ou, sans date d'acte, **de moins
   de 6 mois**. Les autres vont dans un groupe **« À vérifier »**, replié, visible, jamais caché (36 à date d'acte passée le 28/10).
3. **L'historique** : la bande « Biens & mandats liés » (10 plus récents + « Tout afficher », §48.1) **reste**, sous les ventes des
   12 mois.
4. **Les honoraires encaissés** : `commission_agence`.
5. **« Exporter »** les ventes : **en construction**.

**Le plan de code** (à faire sur un « vas-y ») :
- **la base** : une fonction de lecture `app_notaire_fiche(p_contact text)` en `security invoker` (décision 1). Elle rend les dossiers du
  notaire, comptés par transaction et non par ligne de partie, avec leur chaîne (la vente de la chaîne compte comme l'issue, même sans le
  notaire), les parties, le confrère d'en face, les dates, les montants, l'agence et le négociateur. Patch, inverse et répétition, avec les
  temps sous un commercial, essayés dans une transaction annulée ;
- **l'écran** : les blocs notaire dans la fiche V2 quand la catégorie dominante est « Notaire », derrière un interrupteur, à la place de
  « Recherche & rapprochement » (gardé si le notaire a une recherche active). Les blocs sans données sont marqués « en construction » ;
- **les essais** : sur le code réel (règle « en cours », chaîne, double compte, droits) ; puis la vérification à l'écran, au bureau et au
  téléphone.

### 49.8 ✅ ÉTAPE 4 CODÉE *(28/10, Frédéric : « oui, vas-y »)* — NON POSÉE, NON POUSSÉE
**La base** : `supabase/patch_notaire_etape4_fiche_2026-10-28.sql` (+ `_INVERSE`, `_REPETITION`) crée `app_notaire_fiche(p_contact)`,
en lecture seule et en `security invoker`. Une ligne par transaction vivante, avec son ou ses côtés, l'issue de la chaîne, le compromis
de la chaîne, les vendeurs, acheteurs et confrères, le bien (parc, sinon archives, sinon historique), et la médiane de l'agence
compromis → acte (3 ans, ce que le compte voit).
- **Essai dans une transaction annulée : 13 / 13**, rien gardé.
  - Temps sur le notaire le plus chargé : 252 ms (admin), 360 ms (commercial).
  - 800 transactions, aucune en double.
  - Le compromis de 11729 porte la vente du 03/04/2026, où il n'est pas.
  - Il n'est jamais son propre confrère ; 402 ventes sur 407 portent leur compromis ; chaque ligne porte son bien.
  - JACQUIER : 0 ligne, sans erreur. Médiane de l'agence : 85 j.
  - ⭐ **Témoin positif des droits** : le premier contrôle sous un commercial passait sur **0** dossier (le notaire le plus chargé n'est pas
    dans son portefeuille), donc il ne prouvait rien. Ajouté : le notaire le plus présent chez ce commercial (10164856) → **6 vus sur 301**,
    tous sur ses biens.

**L'écran** : `apps/hektor-v1/src/FicheNotaire.tsx` (neuf), interrupteur `FICHE_NOTAIRE_V2` ; styles `fiche-notaire-v2.css` (99 règles
reprises de la maquette v2, plus 4 propres à l'app), importée par `main.tsx`.
- Les règles sont des fonctions pures : `construireVueNotaire(fiche, aujourdhui)`.
- Dans la fiche V2 (App.tsx), quand la catégorie dominante est « Notaire » :
  - les chiffres en tête au-dessus du tableau ;
  - les dossiers en cours (étapes Rétractation · Acte prévu · Date à fixer · Conditions **en construction**), et « À vérifier » replié ;
  - « À venir » en tête de la colonne de côté, au-dessus de « À faire », qui reste ;
  - les ventes des 12 mois, puis « Avec nous » et les confrères, avant « Activité & relation » ;
  - dans le volet, « Interlocuteurs de l'étude » **en construction** et « Partenaire depuis … ».
- « Recherche & rapprochement » est masqué pour un notaire **sans** recherche active. « Biens & mandats liés » reste (décision 3).
- Dans une carte : la condition de prêt et les pièces du dossier sont **en construction**, le séquestre n'apparaît que s'il est non nul.
  « Exporter » est **en construction**.
- ⚠ **Écart avec la maquette, assumé** : l'étape « Conditions » de la maquette suppose la condition de prêt, qui n'existe pas. Elle est
  montrée « en construction » au lieu d'un chiffre inventé (décision 5).
- **Essais** : `apps/hektor-v1/test_fiche_notaire.cjs` **25 / 25**, sur le code réel, à date fixe. Il contrôle « en cours » et
  « À vérifier », la chaîne, les étapes et leur ordre, les côtés, les actes ≤ 30 j, ventes et honoraires, les médianes, « À venir »,
  « un dossier = une chaîne », agences, confrères, une fiche vide, la date `0000-00-00`, l'ordre reçu, le branchement dans App.tsx.
  **Mutant** sans la borne des 6 mois : attrapé.
  - Sur données **réelles** (lues dans une transaction annulée, jamais versionnées) : 10164856 → 0 en cours, 4 ventes en 12 mois,
    délai 76 j contre 85 j pour l'agence, 14 agences, 4 confrères, depuis 2007 ; 10166165 → 0 en cours, **1 à vérifier** (le compromis de
    2024), 0 vente en 12 mois, délai 77 j, depuis 2006. Moins de 5 ms chacun.
  - `test_notaire_ecran`, P2 et le type unique restent verts ; `npm run build` vert.
- ⚠⚠ **Décision 4 à reconfirmer — mon conseil était mal mesuré** : sur les 348 ventes des 12 mois, `commission_agence` n'est **non nulle
  que sur 82** (somme 269 321 €). `honoraires_entree` l'est sur **330**, `honoraires_sortie` sur 19 (somme des deux : 2 614 758 €). J'avais
  vérifié qu'un champ « existe », pas qu'il porte un montant. Le choix est à un seul endroit (`honorairesDuDossier`, FicheNotaire.tsx), et
  la fonction rend les trois champs.
- ⛔ **L'ordre de pose compte** : la fonction **avant** le front. Un front poussé sans elle afficherait « Fiche notaire indisponible » sur
  la fiche des 1 110 notaires. Le reste de la fiche ne bougerait pas.

### 49.9 ✅ DÉCISION 4 RECONFIRMÉE (28/10, Frédéric : « oui, vas-y ») — honoraires = entrée + sortie
`honorairesDuDossier` = `honoraires_entree` + `honoraires_sortie`. Réel : 10164856 passe de 3 750 € à **27 000 €** sur ses 4 ventes des 12 mois. Essai 25 / 25, build vert. ⛔ **La pose de la fonction a été REFUSÉE à mon outil** (classée « déploiement en production ») : elle est à **coller par Frédéric** dans l'éditeur SQL de Supabase — d'abord `patch_notaire_etape4_fiche_2026-10-28.sql`, puis `_REPETITION.sql` (12 lignes, toutes « OK » ; la 13e de mon essai contrôlait le retour arrière, elle n'est pas dans la répétition). **Ensuite seulement**, pousser le front.

### 49.10 ✅ FONCTION POSÉE LE 28/10 À 13:04 *(Frédéric : « fais-le toi-même, tu as mon accord »)*
`patch_notaire_etape4_fiche_2026-10-28.sql` passé (COMMIT), répétition **12 / 12 verte du premier coup** (notaire le plus chargé : 260 ms admin, 363 ms commercial ; témoin positif 6 vus sur 301 ; médiane de l'agence 85 j). ⬜ Front à pousser par Frédéric, puis à voir à l'écran (bureau et téléphone).

### 49.11 ✅ LA FICHE NOTAIRE EST EN LIGNE, VUE À L'ÉCRAN *(28/10, déploiement de 13:10:18, Chrome de Frédéric)*
- **10352963, Me Damien LABIDOIRE** (le notaire qui a le plus de dossiers en cours) :
  - chiffres : **7** dossiers en cours (0 vendeur · 2 acquéreur · 5 les deux), **4** actes ≤ 30 jours (le prochain le 30/10/2026),
    **2** ventes en 12 mois pour 24 000 € d'honoraires, **91 j** de compromis à acte, « 6 j plus lent que la médiane (85 j) » ;
  - étapes : 0 Rétractation · 7 Acte prévu · 0 Date à fixer · Conditions « en construction » ;
  - les cartes : bien, vendeurs → acheteurs, côté, « Face : » le confrère, négociateur, prix, « Acte le 30/10/2026 ». Le détail déplié
    montre compromis, fin de rétractation, condition de prêt « en construction », acte prévu, honoraires 9 000 €, net vendeur 120 000 € ;
  - « À venir » : 5 signatures d'acte, dans l'ordre (30/10, 04/11, 14/11, 21/11, 02/01) ;
  - « Recherche & rapprochement » masqué ; « Interlocuteurs de l'étude » « en construction ».
- **10164856** : 0 en cours, 4 ventes en 12 mois · 27 000 €, 76 j (9 j plus vite que la médiane), 14 agences (Firminy 55 en tête),
  4 confrères, « Partenaire depuis 2007 ». Aucun « indisponible ».
- **Téléphone** (cadre de 390 px, rendu mobile) : la fiche, ses 4 chiffres et ses 7 cartes ; page à 386 px, sans défilement horizontal.
  - ⚠ La ligne « vendeurs → acheteurs » d'une carte coupait les acheteurs. **Corrigé** : elle passe à la ligne sous 640 px
    (`fiche-notaire-v2.css`). Build vert ; ⬜ à pousser, puis à revoir.
  - ⚠ **Défaut qui existait déjà, noté et pas touché** : sous 640 px, les boutons « RDV » et « Email » de l'en-tête « Activité &
    relation » sortent du cadre (440 et 526 px pour 386), **sur toutes les fiches**. Mesuré aussi sur JACQUIER, fiche acheteur. Ce n'est pas
    la fiche notaire.

### 49.12 ⚠ TROUVÉ EN VÉRIFIANT LES INVITÉS D'UN RDV : « le propriétaire » pouvait être le notaire — corrigé *(28/10)*
- **Les invités d'un RDV (décision 4 du 27/10)** : `loadAnnonceContactInvitees` lit la vue des liens **sans filtrer les rôles**. Le notaire
  de l'annonce y est donc. Mesuré en base : l'annonce 59132 (mandat 18232) porte `notaire_acquereur` et `notaire_vendeur` parmi ses
  contacts. ⬜ Pas vu dans la fenêtre de l'agenda : elle demande l'agenda Google chargé et un créneau.
- ⚠⚠ **Mais la même liste sert aussi à trouver LE PROPRIÉTAIRE d'une annonce** (`resolveAnnonceOwnerContact`, `handleCallAnnonceOwner` :
  appel, RDV, avis de valeur depuis les estimations). Son tri `annonceOwnerRoleRank` met en tête tout rôle qui contient
  `propri|vendeur|mandant` : **`notaire_vendeur` contient « vendeur »**. Le notaire pouvait donc passer devant le vrai propriétaire.
  Mesure : **8 annonces en estimation** portent un notaire (et 88 sous compromis, 1 actif, 1 sous offre). Ma pose de l'étape 1 (10:29)
  l'a rendu possible. **C'est le « ce que ça pourrait casser ailleurs » que mon audit de l'étape 1 avait manqué** : j'avais vu ce lecteur
  comme « invitable, souhaitable », pas comme le chercheur de propriétaire.
- **Corrigé** (App.tsx, une ligne) : `if (r.startsWith('notaire')) return -1`. Un notaire passe après tout le monde, même un contact sans
  rôle. Essai `test_notaire_ecran.cjs` : **contrôle ajouté**, vert. **Témoin inverse** : sans la ligne, notaire et propriétaire ont le même
  rang (3), le contrôle aurait rougi. Les 4 essais du front sont verts, le build aussi. ⬜ À pousser.
- Autres lecteurs de cette liste, relus : la fenêtre de l'agenda (`googleAgendaRelationRoleLabel` → « Notaire vendeur », juste) et la
  fiche contact. Aucun autre tri sur « vendeur ».

## 50. LES 4 BLOCS « EN CONSTRUCTION » DE LA FICHE NOTAIRE — audit *(28/10, Frédéric : « créer les blocs en construction : interlocuteurs de l'étude, pièces du dossier, condition de prêt, export des ventes »)* — lecture seule, rien codé

**Audit limité à ces 4 blocs.** Aucun ne demande d'écrire chez Hektor : ce sont des données ou des gestes de l'app.

### 50.1 La condition de prêt — un registre EXISTE déjà, presque vide
- Hektor ne la donne pas par l'API : les clés de `payload_json` d'un compromis, relevées sur les 276 compromis de 2026, n'en portent
  aucune.
- **Mais le projet la lit déjà dans la console Hektor** (`lireConditionsSuspensives`, worker, l. ~13160 : les conditions « retenues »
  avec leur nombre de jours). Il la range **chez nous** dans `app_affaire_condition` (libellé, jours, échéance, état, levée le, note),
  avec un catalogue `app_condition_catalogue` : « Préemption mairie (0 j) », « Obtention Crédit (45 j) ». Une fonction l'écrit,
  `app_conditions_affaire_ecrire`.
- **Mesure** : 5 conditions sur **3** compromis, toutes « attente », **aucune échéance**, écrites le 23/10.
- ➡ La fiche peut lire ce registre. L'échéance vaut la date saisie, sinon la date du compromis + les jours de la condition (45 j pour le
  crédit). Aujourd'hui, presque toutes les cartes diraient « aucune condition enregistrée ».

### 50.2 Les pièces du dossier — reconnaissables par le NOM des documents
- Les documents n'ont **pas de type** (`document_type` vaut « document » sur les 192 981) : seul le **nom** les distingue.
- Sur les **75 annonces** dont le compromis est en cours avec un acte à venir : **1 924 documents**, tous avec au moins un document.
  Reconnus par leur nom : compromis 75, mandat 74, cadastre 65, pièce d'identité 62, diagnostics 43, titre de propriété 41,
  taxe foncière 32, offre de prêt 18, assainissement 9, notification SRU 1.
- ➡ Une liste de pièces **calculée par le nom**, avec « à demander » pour les manquantes. ⚠ C'est une **déduction** : un document mal
  nommé passe pour absent. Il faudrait pouvoir corriger à la main.
- « Envoyer les pièces à l'étude » serait un e-mail avec pièces jointes. Un envoi de documents existe déjà côté estimations ; il est à
  regarder avant de le réutiliser.

### 50.3 Les interlocuteurs de l'étude — à SAISIR, on ne peut pas les deviner
- Hektor n'a pas de notion d'« étude ». J'ai essayé le domaine de l'e-mail : 613 contacts actifs en `@…notaires.fr` (579 notaires,
  34 autres), sur 61 domaines. Mais des domaines comme `notaires.fr` sont partagés par des études différentes. Seuls **3** domaines
  réunissent un notaire et un collègue.
- ➡ Un petit registre **chez nous** : nom, rôle (clerc, formaliste, associé…), téléphone, e-mail, rattaché au notaire. On le saisit dans
  la fiche. Rien chez Hektor, rien de deviné.

### 50.4 L'export — simple
- Un fichier CSV (ouvrable par Excel), fabriqué dans le navigateur à partir des dossiers déjà chargés. Aucune donnée neuve.
- Il n'exporte **que ce que le compte voit** (décision 1).

### 50.5 Ce que ça pourrait casser ailleurs
- La condition de prêt : **lecture seule** d'un registre existant. L'écran qui l'écrit (`app_conditions_affaire_ecrire`) n'est pas touché.
- Les pièces : **lecture seule** des documents.
- Les interlocuteurs : une **table neuve**, avec sa règle d'accès ; rien d'existant n'est touché.
- L'export : rien côté base.

### 50.6 Questions — À TRANCHER PAR FRÉDÉRIC
1. **Condition de prêt** : afficher les conditions du registre existant, l'échéance étant la date saisie ou la date du compromis + les jours
   du catalogue, en sachant que 3 compromis seulement en ont aujourd'hui ?
2. **Pièces** : la liste calculée d'après le nom des documents (avec « à demander »), et plus tard une correction à la main ? « Envoyer à
   l'étude » maintenant ou plus tard ?
3. **Interlocuteurs** : un petit registre chez nous, saisi dans la fiche : qui peut ajouter et modifier, tout le monde ou les admins ?
4. **Export** : les ventes des 12 mois seulement, ou tous les dossiers du notaire ?

## 51. ✅ LES 4 BLOCS CODÉS *(28/10, Frédéric : « je valide toutes tes recommandations »)* — NON POSÉS, NON POUSSÉS
**Décisions** :
1. condition de prêt : le registre existant, l'échéance étant la date saisie ou la date du compromis + les jours ;
2. pièces : calculées d'après le nom des documents, avec « à demander » ; la correction à la main et « Envoyer à l'étude » plus tard ;
3. interlocuteurs : un carnet chez nous, que tout compte actif peut écrire ;
4. export : tous les dossiers que le compte voit.

**La base** : `supabase/patch_notaire_blocs_2026-10-28.sql` (+ `_INVERSE`, `_REPETITION`), fabriqué par un script à partir de la fonction de
l'étape 4, sans recopie à la main.
- Une table neuve `app_notaire_interlocuteur` : RLS, lecture par les comptes actifs, aucune écriture directe, jamais effacée
  (`retire_le`).
- `app_notaire_interlocuteur_ecrire` : ajouter, modifier, retirer ; auteur et heure écrits.
- `app_notaire_fiche` rend en plus `conditions`, `documents` (noms, compromis sans vente seulement) et `interlocuteurs`.
- L'inverse **garde la table** : un numéro ne se perd jamais.
- **Essai dans une transaction annulée : 17 / 17**, rien gardé :
  - la table est protégée ; les 800 dossiers sont gardés ; des documents seulement sur un compromis sans vente ; **témoin positif** : le
    notaire aux 7 dossiers en a sur ses 7 compromis ; les conditions arrivent (transaction 1001394) ; 260 ms admin, 365 ms commercial ;
  - **sous un commercial** : il ajoute (nom nettoyé), modifie (champ vide → NULL) et retire ; une écriture directe dans la table est
    refusée, un nom vide aussi ; la trace reste (auteur et retrait), anon ne lit pas ;
  - l'**inverse** redonne la fiche de l'étape 4 **à l'octet** (même empreinte).

**L'écran** (FicheNotaire.tsx, App.tsx, fiche-notaire-v2.css) :
- **la condition** : dans la carte, chaque condition avec son échéance ou « levée le … » (sinon « aucune enregistrée ») ; l'étape
  **« Conditions »** compte et filtre les dossiers avec une condition en attente ; « À venir » porte les échéances des conditions ;
- **les pièces** : « Pièces du dossier · N sur 11 », avec ✓ « documents » ou « à demander ». « Envoyer les pièces à l'étude » reste
  **en construction** (décision 2) ;
- **les interlocuteurs** : dans le volet, la liste, « + Ajouter », modifier, retirer (avec confirmation), puis la fiche se relit ;
- **l'export** : « Exporter » télécharge `dossiers-notaire-<id>.csv`, 16 colonnes, « ; » et BOM pour Excel, le plus récent d'abord.

**Essais** : `test_fiche_notaire.cjs` **33 / 33** :
- échéance (saisie, puis compromis + jours), levée, l'étape « Conditions », « À venir » ;
- les pièces : accents et majuscules, et les **vrais noms du mandat 18593** ;
- l'export : BOM, ordre, guillemets, honoraires ;
- **mutant** sans retrait des accents : attrapé.

Le build est vert, `test_notaire_ecran`, P2 et le type unique restent verts.
- Sur données réelles (10352963, lues dans une transaction annulée), les premiers réglages laissaient passer **4 ratés et 1 fausse
  détection**, vus sur les vrais noms : « AUDIT ENERGETIQUE », « TF 2025 », « DONATION », « Parcelles », et un « mail… retard prêt » pris
  pour une offre de prêt. **Corrigés** : 18593 passe de 4 à **7 sur 11**. Les autres dossiers : 18489 6, 18683 5.
- ⚠ Écrire un motif avec `\b` ou `\u` en passant par Python ou par l'outil d'édition peut changer les caractères : `̀-ͯ` est
  écrit en caractères réels dans le fichier, ce qui marche pareil. Le mutant est découpé par ses bornes, sans motif.
- ⛔ **L'ordre de pose** : la base **avant** le front. Sinon le carnet proposerait un geste sans fonction derrière, et les pièces et
  conditions resteraient vides.

### 51.1 ✅ POSÉ LE 28/10 À 13:45 *(Frédéric : « oui, pose »)*
`patch_notaire_blocs_2026-10-28.sql` passé (COMMIT ; le seul message est l'avis normal « policy … does not exist, skipping » du DROP POLICY IF EXISTS), répétition **8 / 8 verte du premier coup** (800 dossiers gardés, documents seulement sur les compromis sans vente, témoin positif 7 compromis avec documents, conditions de la transaction 1001394, 260 ms admin, 364 ms commercial). ⬜ Front à pousser par Frédéric (6 commits), puis à voir à l'écran.

### 51.2 ✅ EN LIGNE ET VU À L'ÉCRAN *(28/10, déploiement de 13:49:28, Chrome de Frédéric)*
- **Bureau, 10352963 (Me Damien LABIDOIRE)** :
  - étapes « 0 Rétractation · 7 Acte prévu · 0 Date à fixer · **0 Conditions** » ;
  - la carte dépliée (mandat 18593) : « Conditions : aucune enregistrée » et « **Pièces du dossier · 7 sur 11** », chaque pièce avec ✓
    « documents » ou « à demander » ;
  - les boutons : « Ouvrir l'annonce » et « Envoyer les pièces à l'étude · en construction » ;
  - « + Ajouter » ouvre le formulaire (nom, rôle, téléphone, e-mail) ; **refermé sans rien enregistrer** (le premier vrai ajout revient
    à Frédéric) ; « Exporter » est là.
- ⬜ **Non vu à l'écran** :
  - **une condition affichée**. La seule transaction à notaire qui en porte (compromis du 23/10 sur l'annonce 24113) est vendue, donc pas
    « en cours ». Vérifié par les essais (33 / 33) seulement ;
  - **le fichier de l'export** : il n'a pas été téléchargé dans le Chrome de Frédéric, ce qui serait un téléchargement sans son accord.
    Vérifié par les essais seulement.
- **Téléphone** (cadre de 390 px) : la ligne « vendeurs → acheteurs » **passe à la ligne** (32 px, dans le cadre) ; les 11 pièces sont
  là ; **aucun débordement** dans les blocs notaire ; page à 386 px.
- **Les deux corrections sont dans le front déployé** : le tri du propriétaire (`startsWith("notaire")?-1`, §49.12) et la ligne des parties
  (`fa-cx-dos-parties{white-space:normal`).

## 52. L'ACTE ET SES EFFETS — audit *(28/10, Frédéric : « ok » à « commencer par les effets de l'acte »)* — lecture seule, rien codé

**Périmètre** : la vente (créée, supprimée) et ce qu'elle doit changer sur le **contact** (type), la **recherche** de l'acheteur, la
**relation** au bien (propriétaire / mandant). ⚠ Annonce, mandat (sa clôture à la vente est ⑦-3a, déjà en production), documents,
RDV : **non mesurés ici**. Ce qui reste du plan des types (§29) : **P5** (le « propriétaire depuis la vente » au geste), **P6** (les
acheteurs d'avant le 17/07, décision A / B / C en attente), **C10** (la vente supprimée), **D4** (proposer de clore la recherche).
Le « jusqu'à » du vendeur (C11) **n'est plus demandé** (§28.5).

### 52.1 Les gestes, objet par objet
- **Créer une vente dans l'app** : registre des transactions au clic (R1), table des parties, type de l'acheteur (worker, §47.1).
  ❌ le lien « propriétaire depuis la vente » n'arrive qu'**à la nuit** (la règle reclasse le lien que Hektor ajoute après la vente).
- **Créer une vente dans Hektor** (le cas réel) : tout arrive **la nuit**, et la nuit le fait **juste**.
- **Supprimer une vente** (app ou Hektor) : la ligne quitte le registre, le type est recalculé. ❌ le lien de l'acheteur au bien
  **reste chez Hektor** (Hektor ne le retire pas) ; la nuit **lève** « né de la vente » (`a_lever`, `relation_ledger.py` ~774) et le
  lien redevient un lien ordinaire : sur un bien sous mandat, **l'acheteur devient « Mandant »** (C10).
- **La recherche de l'acheteur** : rien ne la touche à la vente (D4 : la clôture doit être **proposée**, pas automatique). Le geste
  existe déjà : « Archiver cette recherche dans Hektor » (fiche contact, `handleDeleteContactSearch`, ciblage corrigé le 27/10).

### 52.2 Les mesures (28/10)
- **Les ventes réelles des 60 derniers jours** (hors biens d'essai) : **55 ventes, 57 acheteurs — 57 « propriétaire depuis la
  vente »**, 0 lien sans origine, 0 sans lien. ⭐ La règle de nuit fait son travail.
- **Ventes créées dans l'app** sur ces 60 jours, hors essais : **0**. Toutes les ventes sont saisies **dans Hektor**. ➡ un geste
  « au moment de la vente dans l'app » (P5, ou une proposition D4 dans la modale) ne servirait aujourd'hui **à personne** ; il servira
  à la coupure.
- **C10, prouvé sur le bien d'essai 24113** : les 4 acheteurs des ventes supprimées le 23/10 (20000011, 20000012, 20000013,
  20000014) sont aujourd'hui **« Mandant »** dans l'annuaire (lien `role_hektor = mandant`, `origine` vide) ; le 5e, dont la vente
  vit (20000015), est bien « Propriétaire depuis le 23/10 ». Hors essais : **aucune vente réelle supprimée** connue (1 vente « plus
  dans Hektor » au registre).
- **D4** : **53 acheteurs de 2026** ont encore une recherche active (**12** sur les 60 derniers jours), aucun n'a sa fiche archivée ;
  **149** toutes dates confondues. ⚠ On ne sait pas si la recherche a été créée **après** l'achat (un second projet) : la table des
  recherches ne porte pas sa date de création.

### 52.3 La proposition — À TRANCHER PAR FRÉDÉRIC
- **A — C10, la vente supprimée ne fait plus de l'acheteur un « Mandant »** · base + règle de nuit. Quand la nuit lève « né de la
  vente » **parce que la vente a disparu** (et non parce que la personne est nommée dans un nouveau mandat), elle marque le lien
  « vente annulée » au lieu de le rendre ordinaire ; la vue, le registre des mandats et le type l'ignorent (ni mandant ni propriétaire).
  Le geste « Supprimer la vente » de l'app fait la même marque **au clic**. Rien chez Hektor (D5). ⚠ Ce que ça pourrait casser :
  4 lecteurs à mettre d'accord (vue `app_contact_relations_current`, registre des mandats, type de nuit `build_contacts_layer.py`, type
  SQL) ; un acheteur qui **re-signe** ensuite un mandat sur ce bien doit redevenir mandant (le critère « nommé dans le mandat » le dit).
  Aujourd'hui : 4 contacts d'essai seulement.
- **B — D4, proposer de clore la recherche** · écran seulement. Puisque les ventes se saisissent dans Hektor, la proposition vit sur
  **la fiche contact** : « A acheté le … — sa recherche est toujours active » + le bouton d'archivage qui existe déjà, recherche par
  recherche ; rien ne se ferme seul. Optionnel : la même liste pour les négociateurs (les 53). ⚠ Ce que ça pourrait casser : rien en base ;
  l'archivage passe par Hektor (en différé, la nuit) ; une recherche d'un second projet reste au choix de l'humain.
- **C — P5, le lien au geste de la vente dans l'app** · base + règle de nuit. Utile à la coupure, **0 usage aujourd'hui**. Recommandé :
  **plus tard**, avec la coupure.
- **D — P6, les acheteurs d'avant le 17/07** : la décision A / B / C du §28.4 est toujours ouverte.

### 52.4 Précision *(28/10, Frédéric : « l'audit n'est pas à jour, nous avons énormément travaillé sur les types ; un acheteur devient propriétaire, pas mandant, normalement ? »)*
- **Oui, et c'est mesuré** : le type se calcule désormais **chez nous**, depuis nos registres (`app_type_depuis_nos_registres`, au geste
  et la nuit, §45-47), et la vue range un lien « né de la vente » en **Propriétaire** (`origine = 'vente'` → `proprietaire`). Les 57
  acheteurs des 60 derniers jours sont Propriétaires ; sur 24113, 20000015 (vente vivante) est
  `acquereur_compromis, acquereur_offre, acquereur_vente, proprietaire`.
- **Le défaut C10 ne vient donc PAS du type**, il vient de **ce qu'on lui donne** : quand la vente est **supprimée**, la ligne quitte le
  registre (décision du 07/09), la nuit lève `origine = 'vente'` (plus de vente pour la justifier) — mais le lien que Hektor avait
  ajouté **reste** chez Hektor, rangé « mandant ». Recalculé **aujourd'hui avec le code actuel** (pas une valeur périmée) : 20000011,
  20000012, 20000013 et 20000014 → `acquereur_offre, mandant` ; liens vus : `mandant@24113` + leur offre.
- ➡ La pièce A du §52.3 ne touche pas au calcul du type : elle dit seulement à la nuit (et au geste « Supprimer la vente ») de ne pas
  laisser ce lien redevenir un lien de mandant.

### 52.5 DÉCISIONS DE FRÉDÉRIC (28/10) et la vérification demandée — rien codé
> « A, mais à vérifier : le geste doit aussi modifier la relation de propriétaire à acheteur, même sur affaires annulées, tant qu'une
> transaction est présente ; si la vente est supprimée, il faut aligner le type ensuite ; vérifie si Hektor fait de même ; dans tous les
> cas on garde notre écriture et on prévient l'admin en cas de conflit, sauf si Hektor le fait systématiquement : alors le conflit peut
> être mis en silence. ENSUITE B, mais pas automatiquement : une fenêtre Oui / Non « Voulez-vous archiver la recherche de l'acheteur ? ».
> ENSUITE explique-moi C et D. »

**Ce que fait Hektor — vérifié sur toutes les ventes supprimées connues** (journal `app_affaire_supprimee`, 10 ventes, toutes sur des
biens d'essai) :
- **24113** : les 4 acheteurs des ventes supprimées le **23/10** (605963, 605967, 605973, 605975) sont liés au bien, rangés
  **« mandant »** chez Hektor, liens **vus pour la 1re fois la nuit du 24/10** — donc ajoutés par Hektor à la vente et **jamais retirés**
  à la suppression ; toujours présents le 28/10. Il leur reste une **offre refusée** chacun.
- **24933** : 605030 (6 ventes supprimées en septembre) est lié « mandant » ; il lui reste 4 offres (refusées / proposée). ⚠ Ambigu :
  ce contact était déjà un mandant d'essai, on ne peut pas dire si le lien vient des ventes.
- ➡ **Hektor ne retire jamais l'acheteur quand la vente est supprimée** : 4 sur 4 sans ambiguïté, 5 sur 5 en comptant 605030.

**La règle, telle que je la comprends (A)** : sur un bien, une personne qui est **acquéreur d'une transaction encore présente** (offre,
compromis, même refusée ou annulée), **sans vente vivante**, et que Hektor range « mandant » ou « propriétaire », est un **acheteur** :
le lien est marqué (origine « acheteur »), il ne fait plus d'elle ni un mandant ni un propriétaire, et son type est recalculé (il reste
`acquereur_offre`, etc.). Notre marque gagne toujours ; un désaccord avec Hektor est un **conflit**.

**⛔ La garde indispensable, trouvée par la mesure** : sans elle, la règle toucherait **4 vrais mandants** (10414 FOUGEROUSE, 39032
GINOT, 39291 BROCHET, 36244 JOLIVET) — des vendeurs que Hektor porte AUSSI comme « acquéreur » d'une offre ou d'un compromis de leur propre
bien (erreurs de saisie anciennes, 2009-2020). Ils sont **nommés dans le mandat** ou **vendeurs des transactions** : c'est le même critère que
la règle du chantier 1 (« jamais un acheteur nommé dans le mandat de sa vente »), il les protège. **Avec la garde : 0 vrai contact touché**,
seulement les 6 liens d'essai.

**Où la règle vit** : au geste « Supprimer la vente » (si le lien existe déjà) **et** la nuit (cas de 24113 : le lien n'existait pas encore
au moment de la suppression). Lecteurs à mettre d'accord : la vue `app_contact_relations_current`, le registre des mandats
(`export_app_payload.py` l. ~2052, qui écarte déjà `origine = 'vente'`), la règle de nuit (`regle_acheteur_proprietaire.py`, partagée),
`relation_ledger.py` (qui pose la marque). Rien chez Hektor.

**Le conflit** : Hektor le fait **systématiquement** (5 / 5) → proposé : le compter dans Santé **sans prévenir** l'admin, et prévenir
seulement si un cas sort de la règle (Hektor retire le lien, ou le range autrement).

**B** : une fenêtre Oui / Non « Voulez-vous archiver la recherche de l'acheteur ? », jamais automatique ; Oui lance le geste d'archivage qui
existe (une recherche après l'autre). Où : après une vente faite dans l'app, et depuis la fiche d'un acheteur qui a une recherche active
(les ventes se saisissent dans Hektor : 0 vente faite dans l'app en 60 jours).

**⬜ À trancher avant le code** : quand il ne reste **plus aucune** transaction de la personne sur le bien (tout supprimé), le lien laissé par
Hektor est-il aussi marqué « acheteur » (recommandé : oui — elle n'est ni propriétaire ni mandante), ou laissé à Hektor ?

### 52.6 ⛔ La règle A ne touche QUE des acquéreurs *(28/10, Frédéric : « pour la règle A on parle des acquéreurs, il ne faut pas retirer mandant ou propriétaire, attention »)*
- **Rien n'est jamais retiré** : ni le lien, ni le rôle de Hektor (`role_hektor` reste « mandant »). On **ajoute une marque** (origine
  « acheteur ») qui dit pourquoi ce lien ne fait pas un mandant ; l'interrupteur l'efface.
- ⚠ **Mesure : le critère « vendeur des transactions » ne protège PAS** — il est pollué par Hektor lui-même : une fois l'acheteur ajouté aux
  mandants du bien, les transactions suivantes le portent comme vendeur (les 4 testeurs de 24113 sont « vendeurs » de leur offre refusée).
  Il protégerait trop, et ne distingue rien.
- ⭐ **La garde qui distingue : NOUS AVONS VU HEKTOR AJOUTER LE LIEN APRÈS LA TRANSACTION** — le lien est né dans notre registre
  **après sa naissance (30/09)** et **après** la 1re transaction de la personne sur ce bien. Plus la garde du chantier 1 : jamais une personne
  nommée dans le texte Hektor d'un mandat du bien.
- **Sur les 10 liens « acquéreur sans vente vivante, rangé mandant / propriétaire »** : **4 visés** — les testeurs de 24113 (liens vus le
  24/10 à 04:55, transactions vues à 04:52) ; **6 intacts** — les 4 vrais mandants (10414, 39032, 39291, 36244 : liens antérieurs au registre),
  605030 sur 24933 et 10354490 sur 62774 (mandants d'essai, liens antérieurs). **0 vrai contact touché.**
- **Une personne qui n'a plus AUCUNE transaction sur le bien** n'est plus un acquéreur : la règle **ne la touche pas** (lien laissé à Hektor).

### 52.7 ✅ A ET B CODÉS *(28/10, Frédéric : « ok »)* — A NON POSÉ (interrupteur éteint, vue non posée), B NON POUSSÉ
**A — l'acquéreur sans vente** (commit `a2e3fe3`)
- **Nuit** : `relation_ledger._acheteurs_sans_vente` + `regle_acheteur_proprietaire.couples_acheteurs_sans_vente` (une seule règle,
  ses gardes écrites dans le module). Interrupteur **`APP_RELATION_ACHETEUR_SANS_VENTE`**, qui n'agit que si
  `APP_RELATION_ACHETEUR_PROPRIETAIRE` est allumé ; **éteint**, la nuit remet à vide ses marques. Le bilan de nuit compte les désaccords
  avec Hektor (`acheteur_sans_vente_conflits_hektor`) **sans alerte** (Hektor le fait systématiquement, décision de Frédéric).
- **Registre des mandats** (`export_app_payload.py`) : écarte `origine IN ('vente', 'acheteur')`.
- **Vue des liens** (`supabase/patch_acheteur_sans_vente_vue_2026-10-28.sql`, + INVERSE, REPETITION) : cache la ligne « lien au bien »
  marquée `acheteur`, et dès le clic celle d'un lien « né de la vente » dont la vente a disparu alors qu'une transaction reste (fonction
  `app_lien_vente_devenu_acheteur`, SECURITY DEFINER). Rien n'est effacé.
- **Essais** : règle **22/22** (dont JOLIVET, que seule la garde de naissance protège) ; **mutant** sans la garde de naissance → 2 contrôles
  tombent ; **copie réduite de phase2.sqlite, vraie fonction de nuit : 10/10** — sur tout le registre, **exactement les 4 testeurs de 24113**
  sont marqués, les 119 « propriétaires depuis la vente » inchangés, les 4 vrais mandants et les 2 mandants d'essai intacts, le registre
  des mandats de 24113 passe de 9 à 5 mandants (les 4 testeurs), une 2e nuit ne change rien, l'interrupteur éteint rend l'état d'avant ;
  **vue, transactions annulées : 14/14**, témoin inverse compris, l'inverse rend l'empreinte `647c3285`.
- ⛔ **Deux défauts trouvés par les essais, corrigés avant tout** : (1) `NOT (origine = 'vente' AND …)` sur un lien SANS marque rend
  « inconnu » et la vue **cachait 10 lignes, dont les 4 vrais mandants** → `COALESCE(origine, '')` ; (2) la règle écrite dans la vue, jugée
  sous RLS, faisait passer la fiche d'un commercial de **155 à 430 ms** → rangée dans une fonction SECURITY DEFINER appelée seulement pour
  un lien « né de la vente » : **155 → 155 ms**, et la même réponse pour tous les comptes.
- ⏰ **À poser, dans cet ordre, à son accord** : 1. la vue (patch, puis la répétition, 6 lignes « OK ») ; 2. `APP_RELATION_ACHETEUR_SANS_VENTE=1`
  dans `.env` ; 3. la nuit suivante marque les 4 testeurs, pousse, et l'étape des types les recalcule (ligne 6 de la répétition).
  Le code Python est déjà là, **éteint** : la nuit de ce soir ne change rien.

**B — proposer d'archiver la recherche de l'acheteur** (commit `6c25c59`, écran seulement)
- Fiche contact V2 (celle en ligne) : un bandeau « A acheté le … — sa recherche est toujours active » + **« Archiver la recherche… »** →
  la fenêtre **« Voulez-vous archiver la recherche de l'acheteur ? »** avec la liste des recherches, **Non** (rien ne part) / **Oui, archiver**
  (le même travail que la corbeille de chaque carte, une recherche après l'autre). Réservé à qui peut gérer les contacts.
- « Acheteur » = une **vente vivante** (`acquereur_vente`) ; une recherche en création ou déjà en archivage n'est pas reproposée.
- Essai `apps/hektor-v1/test_archiver_recherche_acheteur.cjs` **12/12**, témoin inverse ; `npm run build` vert. ⚠ **Pas vu à l'écran.**
- ⚠ **Le bandeau se verra sur ~149 fiches** (acheteurs de toutes dates avec une recherche active, dont 53 de 2026) — y compris d'anciens
  acheteurs qui cherchent peut-être un second bien : c'est une proposition, rien ne part sans « Oui ».
- ⬜ **Non fait** : la même fenêtre juste après une vente faite DANS l'app (0 vente faite dans l'app en 60 jours) — à son choix.

### 52.8 ✅ A POSÉ LE 28/10 VERS 19:55 *(Frédéric : « oui »)*
- **La vue** : patch posé, répétition **6/6 OK** (ligne 6 : « marque pas encore posée : 4 encore mandants », attendu) ; nouvelle empreinte
  `ce06623f` ; **191 217 lignes, comme avant**.
- **L'interrupteur** : `APP_RELATION_ACHETEUR_SANS_VENTE=1` ajouté à `.env` sous `APP_RELATION_ACHETEUR_PROPRIETAIRE=1` (sauvegarde
  `env_avant_acheteur_sans_vente_20261028` dans le scratchpad) ; relu par le module : les deux règles **allumées**.
- ⏰ **29/10 matin** : dans le journal du run, la ligne « acquereur sans vente : 4 lien(s) marque(s) « acheteur » (4 neuf(s), 0 leve(s)) ;
  4 en desaccord avec Hektor » ; puis la répétition, ligne 6 → « OK (marque posée, plus aucun mandant) » ; et le type des 4 testeurs
  → `acquereur_offre` seul. ⛔ Si la ligne n'apparaît pas ou compte autre chose que 4 : regarder avant tout.
- **Retour arrière** : `APP_RELATION_ACHETEUR_SANS_VENTE=0` (la nuit remet les marques à vide), puis le patch inverse de la vue.

### 52.9 ⛔ Correction (28/10, Frédéric : « C, cela a déjà été fait, on pose propriétaire depuis — refais un audit et mets à jour le plan »)
- **Oui, c'est fait — la nuit.** Audit du code : `relation_ledger._poser_les_liens_nes_de_la_vente` pose `origine = 'vente'` et
  `proprietaire_depuis` ; la fiche affiche « Propriétaire depuis le … » (`App.tsx` ~39543) ; mesuré **57 / 57** sur les ventes des 60 jours.
- **Ce que C désignait, et qui manque seulement** : **aucune fonction de la base ni le worker** ne pose `proprietaire_depuis` (recherche dans
  toutes les fonctions et dans `console_job_worker.js` : 0). La nuit **reclasse** le lien que Hektor ajoute à la vente
  (`couples_nes_de_la_vente` exige un lien au bien) : (1) **entre le clic et la nuit**, une vente faite dans l'app ne rend pas l'acheteur
  propriétaire (24113 : vente du 23/10, lien vu le 24/10 à 04:55) ; (2) **à la coupure**, Hektor n'ajoutera plus de lien → plus personne ne
  deviendrait propriétaire. ➡ C reste pour **l'étape 3** (0 vente faite dans l'app en 60 jours) ; mon « C » du §52.3 était mal dit.
- **Les 726 annonces du balayage photos** : traitées le 28/10 par `ecb3241` (poussé) — une erreur de **panne** n'écarte plus une annonce à vie,
  elles reprennent leur place dans le lot (à constater au balayage du 28/10 à 23:00). Plus rien à décider.
- **Le plan est à jour** (ligne ⑧ réécrite, journal du 28/10).

### 52.10 Audit refait (28/10, Frédéric : « avec le chantier des types, les types sont posés d'abord par mon app selon les gestes — audite de nouveau »)
- **Oui : le TYPE est posé par l'app, au clic.** Les 6 portes (§45 : créer / modifier une transaction, ses gestes, lier / créer / retirer un
  mandant) appellent `app_recalculer_type_du_bien` ; `app_change_annonce_status_optimistic` (créer l'offre, le compromis, la vente) le fait
  (vérifié dans son code ce soir). Essai réel du 27/10 : rattacher → « mandant » au clic ; supprimer une vente → l'acheteur perd la vente au clic.
- **Rejoué ce soir pour une vente faite dans l'app** (transaction annulée : 20000015 sans le lien que Hektor ajoute la nuit) : le type juste
  après le clic est `acquereur_compromis, acquereur_offre, acquereur_vente` → **« Acheteur — Vente »** à l'écran (`contactDirectoryCategories`).
- **Ce qui n'est pas posé au clic, et seulement ça** : le **lien au bien** « Propriétaire depuis le … » — `app_change_annonce_status_optimistic`
  n'écrit pas dans `app_relation` (ses écritures : registre des transactions, carnet, dossier, carnet d'annonce, travail). Il arrive la nuit,
  en reclassant le lien de Hektor. C'est le seul objet de « C » (étape 3).

### 52.11 ✅ C CODÉ — « Propriétaire depuis le … » au clic de la vente, comme les autres gestes *(28/10, Frédéric : « oui dès le clic » ; « fais comme les autres gestes »)* — NON POSÉ
- **Le patron** : `app_link_mandant_optimistic` (lier un mandant) — la ligne est écrite **au clic** dans le registre des liens
  (`source = 'app'`, `present_in_hektor = false`, clé `app:…`) ; la vue la montre ; la nuit l'adopte en **gardant son numéro**
  (`app_relation__sb`) quand Hektor la redescend, et la règle de nuit lui repose `origine = 'vente'`. **Ni le worker, ni la nuit ne changent**
  (aucun redémarrage).
- **Le patch** `supabase/patch_proprietaire_au_clic_vente_2026-10-28.sql` (+ INVERSE, REPETITION) : un bloc dans
  `app_change_annonce_status_optimistic`, juste avant le recalcul du type. Pour une **vente** : chaque acquéreur (table des parties) reçoit
  son lien au bien, `origine = 'vente'`, `proprietaire_depuis` = la date de la vente. Un couple déjà connu **n'est pas réécrit** — sauf une
  ligne marquée « acheteur » (vente supprimée avant, §52 A), qui redevient « née de la vente ». Best-effort comme `link_mandant`, mais **dit**
  (WARNING) au lieu de se taire. Ni l'offre ni le compromis (D2).
- **Éprouvé par une VRAIE vente du geste de l'app** (bien d'essai 62965, acheteur 20000013, transactions annulées) : **11 / 11** — témoin
  inverse (fonction d'avant : aucun lien, pas propriétaire) ; avec le patch : lien posé au clic, vue « propriétaire », **type recalculé au
  clic** « propriétaire + acheteur (vente) » ; une marque « acheteur » repasse « vente », datée, rôle de Hektor gardé ; un vrai mandant déjà
  lié **n'est pas réécrit** ; un compromis ne pose rien ; l'inverse rend l'empreinte `fce35139` ; aucun travail ni transaction restés.
- ⚠ **Limite connue, déclarée** : si la vente faite dans l'app est supprimée **avant la nuit** et qu'il ne reste **aucune autre transaction** de
  l'acheteur sur le bien, le lien posé au clic reste « propriétaire » jusqu'à la nuit (la règle A ne touche pas une personne sans transaction).
- ⏰ **À poser à son accord** (puis la répétition, 4 lignes « OK »). **C n'est plus à l'étape 3** pour le clic ; à la coupure, il restera que la
  nuit ne pourra plus « reconnaître » ce lien par celui de Hektor (sa règle de reclassement) — à reprendre avec l'étape 3.

### 52.12 ✅ C POSÉ LE 28/10 VERS 22:00 *(Frédéric : « vas-y »)*
- Patch posé, répétition **4/4 OK** ; nouvelle empreinte de `app_change_annonce_status_optimistic` : `446df246`.
- Actif tout de suite pour la prochaine vente faite dans l'app (aucun redémarrage). ⏰ La première vraie vente faite dans l'app : vérifier
  son lien au bien (`source = 'app'`, `origine = 'vente'`, la date) et, la nuit suivante, son adoption (même numéro, `present_in_hektor`
  passé à vrai, `origine = 'vente'` gardée).
- Retour arrière : `patch_proprietaire_au_clic_vente_2026-10-28_INVERSE.sql`.

## 53. P4 — LES MANDANTS SAISIS À LA CRÉATION D'UNE ANNONCE : audit *(28/10, Frédéric : « audit P4 »)* — lecture seule, rien codé

**Périmètre** : la relation (le lien mandant / propriétaire au bien) et le type du contact, aux gestes qui posent un mandant AUTREMENT
que par « lier un mandant ». Annonce, mandat, documents : non mesurés ici, sauf ce qui touche ces liens.

### 53.1 Les portes, lues dans le code
- **« Lier un mandant » et « créer un mandant »** (`app_link_mandant_optimistic`, `app_create_mandant_contact_optimistic`) : ✅ le lien est
  écrit **au clic** (`source = 'app'`, `present_in_hektor = false`), le type recalculé, le worker le marque **établi** quand Hektor
  confirme (`relation_etablie`) ou le **défait** s'il refuse (`annulerRattachementOptimiste`). C'est le patron.
- **Le n° de mandat automatique** (`create_hektor_mandat_auto_number`) : **ne pose aucun lien** — il EXIGE que les mandants soient déjà liés
  (« crée ou associe un mandant avant de générer le numéro », `console_job_worker.js` ~17861). ➡ **Hors de P4.**
- **La création d'une annonce** (`app_create_annonce_job_optimistic`) : le formulaire propose **un mandant existant**
  (`initial_mandant_contact_id`) **ou un mandant neuf** (nom, e-mail, téléphone… `initial_mandant`). Au clic, la fonction pose la fiche du
  bien chez nous (naissance dans l'app, 8a pièce 2) — **mais rien pour le mandant** : ni lien, ni recalcul du type. Le worker, APRÈS avoir
  créé l'annonce chez Hektor et posé son numéro sur notre ligne (`poserNumeroHektorSurLigneApp`), lie le mandant existant
  (`linkHektorMandantContact`) ou crée le mandant neuf (`createHektorMandantContact`) — **sans rien écrire dans notre registre des liens**.
  Le lien n'arrive chez nous qu'**à la nuit**, en relisant Hektor. ⛔ Et à la coupure, plus jamais.

### 53.2 Les mesures (28/10)
- **82 créations d'annonce par l'app** depuis le 15/05 ; **19 avec un mandant** : **1 existant** (62965, 28/08, lien en erreur partielle),
  **18 neufs** (dernier le 28/08). **Aucune depuis le 21/10** (annonce née dans l'app) : la porte n'a jamais tourné avec le nouveau mécanisme.
- **La particularité** : à la création, l'annonce **n'a pas encore son numéro Hektor** (il arrive ~90 s plus tard) ; or le registre des liens
  est rangé par (contact, annonce Hektor) — contrainte `app_relation_couple_unique`. La vue sait lire une ligne `source = 'app'`, et la
  fiche contact range un bien par **notre** numéro de dossier (`app_dossier_id`), qui existe dès le clic.

### 53.3 La proposition — À TRANCHER PAR FRÉDÉRIC
- **P4-a — le mandant EXISTANT, au clic, comme « lier un mandant »** · base + worker (4 services à redémarrer, file vide)
  - au clic : la ligne du lien (`source = 'app'`, `present_in_hektor = false`), **rangée par notre numéro de dossier**, le numéro Hektor du
    bien encore vide ; le type recalculé ;
  - le worker, au moment même où il pose le numéro Hektor sur la fiche du bien, le pose aussi sur ces liens ; puis, quand Hektor confirme le
    rattachement, il les marque **établis** (le même code que « lier un mandant ») ; s'il refuse, il les **défait** ;
  - si la création de l'annonce échoue chez Hektor : le lien est marqué comme la fiche (« Erreur de création »), jamais laissé vivant.
  - ⚠ ce que ça pourrait casser : la nuit adopte un lien par (contact, annonce Hektor) — une ligne au numéro encore vide est **ignorée** par
    elle (rien n'est écrasé), puis adoptée normalement une fois le numéro posé ; la contrainte d'unicité laisse passer une annonce vide
    (`NULL`), donc rien ne bloque ; la vue range le rôle par le n° de mandat du bien (« propriétaire » tant qu'il n'y en a pas).
- **P4-b — le mandant NEUF** · plus gros : au clic, le contact **n'existe pas encore chez nous** (le worker le crée chez Hektor). Pour l'avoir
  au clic, il faut d'abord **créer le contact chez nous** (comme la création de contact, 8a pièce 1 : « il naît complet »), puis lui poser le
  lien comme en P4-a, et que le worker **reconnaisse** ce contact au lieu d'en fabriquer un second (la règle « un numéro ne se perd jamais » :
  risque de doublon, déjà payé le 21/10).
- **Recommandé** : **P4-a d'abord** (petit, même patron, aucune donnée réelle touchée aujourd'hui) ; **P4-b ensuite**, avec son propre
  audit du rapprochement contact app ↔ contact Hektor. Rien n'est envoyé de plus chez Hektor par aucune des deux.

### 53.4 ✅ P4-a CODÉ *(28/10, Frédéric : « P4-a puis audit P4-b »)* — NON POSÉ, worker NON REDÉMARRÉ
- **Base** (`supabase/patch_p4a_mandant_creation_annonce_2026-10-28.sql`, + INVERSE, REPETITION) : dans la branche « l'annonce naît dans
  l'app » de `app_create_annonce_job_optimistic`, chaque mandant **existant** de la charge reçoit son lien **au clic**, comme
  `app_link_mandant_optimistic` (`source = 'app'`, `present_in_hektor = false`, clé `app:<jeton>:<contact>`), **rangé par notre numéro de
  dossier**, le numéro Hektor du bien vide ; son type est recalculé. Pas de traduction du contact → pas de ligne. Best-effort, mais dit.
- ⛔ **Trouvé par l'essai, avant toute pose** : `app_relation.hektor_annonce_id` était **NOT NULL** chez Supabase — le lien était refusé (et dit
  par le WARNING). Le patch le rend **facultatif**, chez Supabase seulement : la base locale ne reçoit jamais une telle ligne (sa nuit n'adopte un
  lien du cloud qu'avec un numéro de bien, `cle_sb[1]` ; sa copie `app_relation__sb` accepte déjà le vide). L'inverse ne la rend obligatoire
  que si aucun lien n'attend son numéro (sinon il le dit et s'arrête).
- **Worker** (`Console/console_job_worker.js`, +92 lignes, mes seules lignes committées — les lignes Youtrust de l'autre session restent hors
  commit) : `poserNumeroSurLiensDeLaCreation` (le numéro Hektor posé sur les liens **en même temps** que sur la fiche du bien) ·
  `marquerLienDeLaCreationEtabli` (Hektor confirme → établi, puis le type) · en cas de refus, **le même** `annulerRattachementOptimiste` que
  « lier un mandant » · `retirerLiensDeLaCreationEchouee` (la création échoue → les liens nés au clic quittent l'écran, la trace reste).
- **Essais** : base, **une vraie création d'annonce** par le geste de l'app (transactions annulées) **13/13** — témoin inverse, lien au clic,
  vue, type, les requêtes du worker trouvent le lien (numéro, établi, refus, échec), sans mandant / mandant neuf / contact inconnu : rien,
  le mandant donné sous son numéro Hektor reconnu, l'inverse rend `a5e70b57` et la colonne obligatoire, base intacte ;
  worker `Console/test_p4a_mandant_creation.js` **13/13** (vraies fonctions, fausse base, branchements lus dans le code, témoin inverse) ;
  `test_type_apres_ecriture_worker.js` **9/9**.
- ⚠ **Effet de bord de mon premier essai** : un `(fonction()).*` appelait la création **une fois par colonne** — toutes en transaction annulée,
  donc rien de gardé, mais **~130 numéros de dossier de l'app ont été consommés** (10000029 → 10000161 environ) : la prochaine annonce née
  dans l'app aura un numéro plus haut. Aucune fiche, aucun numéro **attribué** n'est perdu.
- ⏰ **À poser à son accord** : 1. le patch, puis la répétition (5 lignes « OK ») ; 2. le worker : **redémarrer les 4 services, file vide**
  (le code est déjà écrit dans le fichier ; sans redémarrage, les liens nés au clic ne reçoivent pas leur numéro de bien — d'où l'ordre :
  redémarrer d'abord, poser ensuite). Usage réel : 0 création avec mandant depuis le 21/10.

### 53.5 P4-b — LE MANDANT NEUF SAISI À LA CRÉATION D'UNE ANNONCE : audit *(28/10, Frédéric : « P4-a puis audit P4-b »)* — lecture seule, rien codé
**Le patron existe déjà, et il a réglé le doublon** : le geste « créer un mandant » sur une annonce existante
(`app_create_mandant_contact_optimistic`) :
1. tire **notre numéro** du contact au clic (`app_contact_identite_seq`) ;
2. crée la fiche chez nous (`app_contact_current`, « naît complet », 8a) et le lien (`source = 'app'`) ;
3. passe ce numéro au worker dans la charge (`app_identite`) ;
4. le worker, après la création chez Hektor (`executerCreationMandantContact`), **pose le numéro de Hektor dans la case cible de NOTRE fiche**
   (`hektor_target_id`) — c'est ce qui empêche le doublon (« un numéro ne se perd jamais ») ; la nuit relie ensuite les deux.

**Ce que fait la création d'annonce avec un mandant neuf** (`initial_mandant`, 18 fois, dernière le 28/08) : **rien au clic** ; le worker appelle
la fonction de bas niveau `createHektorMandantContact` **directement** — pas `executerCreationMandantContact` — donc **sans fiche chez nous,
sans lien, et sans la case cible**. La fiche du mandant n'arrive chez nous qu'avec la descente de nuit, sous un numéro neuf.

**La proposition (P4-b), comme le geste voisin** :
- **base** (même fonction que P4-a, même bloc) : au clic, si la charge porte un mandant neuf (nom ou e-mail), tirer notre numéro, créer sa fiche
  chez nous (les mêmes colonnes que le geste voisin, et « naît complet »), poser son lien rangé par notre numéro de dossier (comme P4-a), recalculer
  son type, et **mettre ce numéro dans la charge** (`initial_mandant.app_identite`) ;
- **worker** : après `createHektorMandantContact` dans la création d'annonce, **poser la case cible** sur notre fiche — le bloc du geste voisin, à
  l'identique (il est lui-même copié de la création de contact globale, avec son piège déjà payé : n'envoyer QUE la case cible) ; le lien reçoit
  son numéro de bien par P4-a et est relié par la nuit, comme pour le geste voisin ; si la création échoue, P4-a retire déjà le lien de l'écran.
- ⚠ **Ce que ça pourrait casser** : (1) **le doublon** si la case cible n'est pas posée — c'est exactement ce que le bloc copié évite, et
  l'essai le mesurera (une fiche, deux numéros, aucune seconde fiche) ; (2) une fiche **orpheline** chez nous si Hektor refuse la création — la
  même limite que le geste voisin aujourd'hui (la fiche reste, son lien quitte l'écran) ; (3) le **redémarrage** des 4 services (file vide),
  à faire en même temps que P4-a.
- **Essais prévus** : une vraie création avec mandant neuf par le geste de l'app, en transactions annulées (fiche, lien, type, numéro dans la
  charge) ; le bloc du worker sur sa fausse base ; témoin inverse.

### 53.6 AUDIT DU CORRECTIF P4-a *(28/10, Frédéric : « audit pour être sûr de ton correctif »)* — deux corrections, essais rejoués
**Tout ce qui lit ou écrit le registre des liens chez Supabase**, face à un lien sans numéro de bien (mesuré dans la base et le code) :
- **5 fonctions** : la vente (`app_change_annonce_status_optimistic`, C), « lier / créer / retirer un mandant » (par numéro de bien :
  une ligne vide n'est ni trouvée ni touchée), `app_recalculer_type_du_bien` (par numéro de bien : elle ne la voit pas — d'où le recalcul
  **par contact** au clic) ; **1 vue** (`app_contact_relations_current` : la montre, rangée par notre dossier, rôle « propriétaire » faute de
  n° de mandat) ; **1 règle de lecture** (comptes actifs, sans lien au bien) ; **aucun déclencheur**.
- **Hors de la base** : le **worker** est le seul à lire le registre par l'API ; l'écran passe par la vue ; la **nuit** copie le cloud
  dans `app_relation__sb` (le vide y est accepté) **juste avant** l'étape du registre des liens, n'adopte que les lignes qui ont un numéro de
  bien, et pousse par numéro de ligne ; `push_single_annonce_to_supabase.py` n'écrit pas ce registre.
- ⚠ **Une fenêtre de quelques minutes, la nuit** : une annonce créée avec un mandant PENDANT la copie du cloud et l'étape du registre (~04-05 h)
  pourrait faire buter le push des liens sur l'unicité (contact, bien) — il échouerait cette nuit-là et se réparerait la suivante (la copie
  aurait alors le numéro). Aucune création n'a lieu à cette heure ; noté, non corrigé.
- ⚠ **Sur la fiche contact**, pendant les ~90 s où le bien n'a pas son numéro Hektor, la ligne du bien n'a **pas de titre** (la vue cherche le
  titre par ce numéro). Noté, non corrigé.

**Deux défauts trouvés par cet audit, corrigés** :
1. **Un contact que Hektor ne connaît pas encore** (né dans l'app, sans numéro Hektor) : le worker ne peut pas le lier chez Hektor (la porte
   refuse un numéro de notre plage), et son retour arrière cherche par numéro Hektor — le lien posé au clic serait resté **affiché à tort**.
   ➡ La base **ne pose plus de ligne** sans numéro Hektor du contact. Essai ajouté (contact sans numéro → aucune ligne).
2. **La création échoue** : les liens quittaient l'écran mais **le type du mandant ne suivait pas**. ➡ Le worker recalcule le type des
   contacts touchés. Essai ajouté.
- **Le témoin inverse** de l'essai du worker lisait HEAD, qui porte désormais P4-a : il est fixé sur le parent du commit `412a0bf` (leçon du 27/10).
- **Essais rejoués** : vraie création, transactions annulées **14/14** ; worker **14/14** ; voisin `test_type_apres_ecriture_worker.js` **9/9**.

### 53.7 ✅ P4-b CODÉ *(28-29/10, Frédéric : « oui P4-b, ensuite les deux »)* — NON POSÉ, worker NON REDÉMARRÉ
- **Base** (même patch que P4-a, bloc à part `@P4b`) : au clic, un mandant **neuf** de la création (nom ou e-mail) reçoit, comme
  `app_create_mandant_contact_optimistic`, **notre numéro** (`app_contact_identite_seq`), **sa fiche** (les mêmes colonnes, puis « naît
  complet » par `app_contact_champs_naissance`), **son lien** (rangé par notre dossier, comme P4-a), **son type** ; et, **en dernier**, son
  numéro part dans la charge (`initial_mandant.app_identite`). Un échec de P4-b ne défait pas P4-a et ne fait jamais échouer la création.
- **Worker** (+66 lignes, mes seules lignes committées) : `poserCaseCibleDuMandantNeuf` — **dès que Hektor a créé la personne**, son numéro va
  dans la **case cible** de NOTRE fiche (bloc du geste voisin, avec son piège payé : rien d'autre dans le PATCH) — c'est ce qui empêche la
  seconde fiche ; `suivreLienDuMandantNeuf` — rattachement confirmé → lien **établi** sous le numéro Hektor de la personne, type recalculé,
  et **relecture du contact** demandée (comme le geste voisin) ; échec → le lien quitte l'écran, la fiche reste (limite du geste voisin).
- **Essais** : base, vraie création en transactions annulées **19/19** (dont 2 témoins inverses : la fonction d'avant ne donne ni lien ni
  numéro ni fiche) — fiche complète (nom, prénom, e-mail, téléphone, civilité, ville, CP, adresse), lien, type, numéro dans la charge ;
  existant + neuf = deux liens ; sans nom ni e-mail = rien ; base intacte, aucune fiche d'essai restée ; répétition **6/6** dans une transaction
  annulée ; worker **22/22** (dont les branchements lus dans le code, témoin inverse sur `412a0bf^`) ; voisin **9/9**.
- ⚠ Les essais consomment des numéros (transactions annulées) : contacts à partir de **20000017**, dossiers de l'app — aucune fiche attribuée
  n'est perdue ; la prochaine fiche aura simplement un numéro plus haut.
- ⏰ **L'ordre de pose, et pourquoi** : **1. redémarrer les 4 services, file vide** (par Frédéric) — sans le nouveau worker, un mandant neuf aurait
  sa fiche chez nous MAIS sa case cible ne serait jamais posée → la nuit fabriquerait une **seconde fiche** ; **2. poser le patch** (P4-a + P4-b),
  puis la répétition (6 lignes « OK »). ⚠ Le redémarrage charge aussi les lignes Youtrust non committées de l'autre session (déjà chargées depuis
  le 27/10, interrupteur éteint).

### 53.8 ✅ P4-a + P4-b POSÉS le 29/10 *(Frédéric : « fais »)*

- **L'ordre a été tenu** : les 4 services tournent depuis le **29/10 à 07:17:56-57** (heure des processus `node`), APRÈS le commit P4-b
  `15ea354` (29/10 00:10:36) → le worker qui tourne connaît déjà `poserCaseCibleDuMandantNeuf` / `suivreLienDuMandantNeuf`.
- **Rejeu dans une transaction annulée** juste avant : 6/6. **Pose** (`patch_p4a_mandant_creation_annonce_2026-10-28.sql`, son propre
  BEGIN/COMMIT) : empreinte de `app_create_annonce_job_optimistic` **a5e70b57 → 5e43b9b7**. **Répétition** : **6/6 OK**, 0 lien en attente
  de son numéro de bien.
- ⏰ **À prouver à la première création d'annonce AVEC un mandant** dans l'app : le lien naît au clic (numéro de bien vide), reçoit son numéro
  quand Hektor crée l'annonce, puis est ÉTABLI ; pour un mandant neuf, sa case cible reçoit le numéro Hektor (pas de seconde fiche la nuit).
- Retour arrière : `..._INVERSE.sql` (il retire @P4a-debut → @P4b-fin, puis remet NOT NULL seulement s'il ne reste aucun lien sans numéro).

---

## 54. C9 — LA RUBRIQUE CONTACT D'UN BIEN SUR NOS SEULS REGISTRES : audit *(29/10, Frédéric : « C9 : rubrique Contact »)* — lecture seule, rien codé

### 54.1 Ce que fait l'écran aujourd'hui — quatre endroits, trois déjà sur nos registres
- **La fiche annonce** (bureau et téléphone : `MobileDossierDetail` reçoit la même liste) : **NOTRE registre d'abord** depuis le **02/10
  (③c)** — `loadDossierDetail` attache `mandants_registre_json` (vue `app_contact_relations_current`, rôles mandant + propriétaire,
  interrupteur `VITE_RUBRIQUE_CONTACT_REGISTRE`, allumé par défaut) ; le blob de Hektor `proprietaires_json` n'est qu'un **repli si la
  lecture échoue**. Une liste vide est respectée. ✅
- **La fiche mandat du registre** (`selectedContactItems`) : « Hektor d'abord s'il a fourni le blob » — **mesuré le 29/10 : 0 ligne sur
  24 560** porte ce blob ; c'est donc **toujours** `mandants_json` (NOTRE liste, 24 485 lignes) qui sert. ✅ dans les faits.
- **L'éditeur du mandat dans la fiche annonce** reçoit la liste de la fiche (registre d'abord). ✅
- ⛔ **L'éditeur du mandat ouvert depuis le REGISTRE DES MANDATS** (`editorFullContacts` / `editorPartialContacts`) : lit **le seul blob de
  Hektor**. Chargé complet : `proprietaires_json` du détail (non vide sur 12 693 des 13 500 biens vivants) — la copie de Hektor, qui ne voit
  ni un mandant saisi dans l'app avant la redescente, ni nos retraits, et qui se fige à la coupure. Chargement partiel (bien sans dossier, ou
  chargement raté) : le blob du registre, **absent des 24 560 lignes → aucun mandant pré-rempli, jamais**.
  ➡ **C'est le seul endroit où la rubrique a encore deux vérités** : le même mandat ne se pré-remplit pas pareil selon qu'on l'ouvre par
  l'annonce ou par le registre.

### 54.2 Ce que la mesure a écarté (et qui n'est PAS C9)
- La fiche annonce montre plus de personnes que la liste du registre des mandats sur 138 biens vivants (236 personnes) et 9 483 biens sortis —
  **même source** (notre registre des liens), **autre regroupement** : la fiche fusionne par **ménage** (`hektor_couple_contact_id`), la nuit
  dédoublonne par **personne** (ex. 63342 : trois fiches de la même personne — la fiche simple, la fiche de couple « Mr./Mme », une seconde
  fiche sans ménage). C'est un sujet de **doublons de contacts**, pas de source. Et le registre exclut **exprès** l'origine `vente` /
  `acheteur` (D2, A).

### 54.3 Le correctif proposé (à valider)
- **Un seul endroit, l'éditeur ouvert depuis le registre**, aligné sur la fiche annonce : complet → `mandants_registre_json` d'abord (déjà
  attaché par `loadDossierDetail`, même interrupteur), `proprietaires_json` en repli ; partiel → `mandants_json` (nos noms, sans adresse) au
  lieu du blob vide. Additif, front seul, aucune écriture en base, aucun nouveau chemin vers Hektor.
- **Ce que ça pourrait casser ailleurs** : les champs que l'éditeur pré-remplit (nom, adresse, téléphone) viennent alors de nos fiches au lieu
  du blob — les mêmes que la fiche annonce montre depuis le 02/10 (0 ligne perdue sur 2 265 biens, +341 personnes) ; `mandants_json` ne porte
  que les noms ; le piège des numéros du 05/10 (dans `mandants_json`, `hektor_contact_id` est celui de Hektor) ne mord pas ici, l'éditeur ne
  détache personne.
