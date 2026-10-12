# CHANTIER ② — LES DROITS DU NÉGOCIATEUR

> **Ouvert le 09/10/2026.** Audit par objet du 08/10, §2 ② et §3 (critère C8) ·
> plan : section « 🧭 LES CHANTIERS DE L'ÉTAPE 2 », ligne ② · CLAUDE.md §2.
> **Audit REFAIT et élargi le 12/10/2026** à la demande de Frédéric : voir la section
> « AUDIT DU 12/10 » en bas — elle **corrige trois erreurs** de l'audit du 09/10.

## LES POINTS DU CHANTIER — *proposition de découpage, à valider*

| # | point | état |
|---|---|---|
| **2a** | **L'état des lieux et LA DÉCISION** : qui peut quoi aujourd'hui, par quelle porte | 🔎 audit fait le 09/10, **refait et élargi le 12/10** → 💬 **attend 4 réponses** |
| 2b | **Annonce** : modifier les champs, changer le statut, archiver / désarchiver, changer de négociateur, supprimer | ⬜ |
| 2c | **Mandant** : rattacher, retirer, créer, modifier | ⬜ |
| 2d | **Transaction** : offre, compromis, vente (+ faut-il un circuit de demande ?) | ⬜ |
| 2e | **Documents et photos** : générer (avis de valeur, mandat, cadastre), supprimer, ajouter une photo, resynchroniser | ⬜ |
| 2f | **Numéro de mandat** : demander un numéro | ⬜ |
| 2g | **Les comptes** : 43 adresses de négociateur portent le parc, 2 comptes commerciaux actifs, 0 manager | ⬜ |
| 2h | **L'écran** : les boutons que le front cache à tout le monde sauf l'admin | ⬜ |
| **2i** | **LES CONSULTATIONS** *(point NEUF, 12/10)* : le cloisonnement « ses biens » est un filtre d'affichage, pas une serrure | 🔴 **trouvé le 12/10** |

### Les réponses de Frédéric (12/10)

```
Q1  que fait un negociateur seul ?      -> « normalement c'est B » (le quotidien seul,
                                           une DEMANDE pour les gestes graves)
                                           + « mais normalement tout existe deja » -> verifie, c'est VRAI
Q2  le role manager ?                   -> « pour l'instant faire idem que admin »
Q3  pilote ou tous les comptes ?        -> « oui il faut tester avant de deployer a tous les comptes »
CONTRAINTE FERME                        -> « cela ne doit surtout pas changer les worker »
```

---

## 2a · L'ÉTAT DES LIEUX — *mesuré le 09/10/2026 vers 14 h, en lecture seule*

### Verdict : CONFIRMÉ, et plus simple qu'annoncé — **il n'y a que CINQ portes**

L'audit du 08/10 disait vrai sur tous les gestes refusés. Mais il ne disait pas
l'essentiel : **une seule fonction commande presque tout**.

| porte | ce qu'elle commande | qui passe |
|---|---|---|
| **1. `app_console_can_request_job`** | **16 fonctions RPC** *(annonce, mandant, photos, n° de mandat, matterport…)* **ET la règle RLS d'écriture de `app_console_job`** (`app_console_job_insert_scope`) — donc aussi les travaux que le front insère en direct, sans passer par une fonction : avis de valeur, PDF de mandat, plan cadastral, photo, suppression d'un document | admin : tout · manager : tout **sauf** statut et archiver · commercial : **7 types de documents** sur **ses** biens |
| **2. `app_console_can_request_contact_job`** | contacts et recherches acquéreur (12 fonctions) | admin, manager : tout · **commercial : OUI, sur ses contacts** *(déjà ouvert)* |
| **3. `is_app_admin()`** | **6 fonctions « affaire »** : offre, compromis, vente, note, conditions, écart de personne | **admin seul** |
| **4. contrôle écrit en dur** | créer un brouillon d'annonce *(commercial accepté, dans une agence où il porte déjà un bien)* · supprimer une annonce *(admin seul + mot de confirmation `SUPPRIMER <n°>`)* | — |
| **5. le front** | `isAdmin = profile?.role === 'admin'` — **49 endroits** dans `App.tsx` | un **manager** ne voit à l'écran rien de plus qu'un commercial |

➡ **Conséquence pour le correctif** : ouvrir les gestes au négociateur se joue d'abord
dans **UNE fonction** (porte 1), qui sert à la fois les RPC et la règle RLS. C'est la
raison pour laquelle ce chantier est beaucoup moins lourd qu'il en avait l'air — mais
**le front doit bouger en même temps**, sinon les boutons restent cachés.

### Ce qu'un négociateur (rôle `commercial`) peut faire, geste par geste

*Mesuré sur la définition réelle des fonctions (`pg_get_functiondef`) et sur
`pg_policies`, pas sur les notes.*

| geste | travail envoyé à Hektor | admin | manager | commercial |
|---|---|---|---|---|
| modifier les champs d'une annonce | `update_hektor_annonce_fields` | oui | oui | **NON** |
| changer le statut | `change_hektor_annonce_status` | oui | **NON** | **NON** |
| archiver | `archive_hektor_annonce` | oui | **NON** | **NON** |
| désarchiver | `restore_hektor_annonce` | oui | oui | **NON** |
| changer de négociateur | `assign_hektor_annonce_negotiator` | oui | oui | **NON** |
| supprimer une annonce | `delete_hektor_annonce` | oui | **NON** | **NON** |
| créer un brouillon d'annonce | `create_hektor_draft_annonce` | oui | oui | **oui** *(son agence)* |
| rattacher / retirer un mandant | `link_` / `unlink_hektor_mandant` | oui | oui | **NON** |
| créer / modifier un mandant | `create_` / `update_hektor_mandant_contact` | oui | oui | **NON** |
| offre, compromis, vente | 4 types | oui | **NON** | **NON** |
| répartition de commission | *(aucun travail Hektor)* | oui | **NON** | **NON** |
| contact : créer, modifier, supprimer | `*_hektor_contact` | oui | oui | **oui** *(ses contacts)* ⚠ **FAUX pour SUPPRIMER — corrigé le 12/10** |
| recherche acquéreur | `*_hektor_contact_search` | oui | oui | **oui** *(ses contacts)* |
| documents : préparer, envoyer, resynchroniser, relancer ou annuler une signature | 7 types | oui | oui | **oui** *(ses biens)* |
| générer un avis de valeur, un PDF de mandat, un plan cadastral | `generate_*` | oui | oui | **NON** |
| supprimer un document chez Hektor | `delete_document_from_hektor` | oui | oui | **NON** |
| ajouter une photo · resynchroniser les photos | `upload_hektor_photo` · `sync_hektor_photos` | oui | oui | **NON** |
| demander un numéro de mandat | `create_hektor_mandat_auto_number` | oui | oui | **NON** |

**La LECTURE, elle, est déjà faite.** `app_dossier_current` et `app_contact_current`
portent une règle RLS qui limite un commercial à **ses** biens et **ses** contacts
(`can_access_negotiator_email`, `can_access_current_dossier`) ; un admin, un manager et
un rôle `lecture` voient tout. **Le trou est donc uniquement du côté de l'écriture.**

> 🔴 **CETTE DERNIÈRE PHRASE EST FAUSSE. Corrigée le 12/10 — voir le point 2i.** La règle
> existe bien sur les **tables**, mais l'écran lit des **vues qui l'ignorent**.

### Les mesures

```
COMPTES (app_user_profile)   4 admins actifs · 2 commerciaux actifs · 0 manager
                             0 compte « lecture » · 1 admin et 1 commercial desactives
                             (le role connait 4 valeurs : admin, manager, commercial, lecture)
LE PARC                      43 adresses de negociateur portent 21 149 lignes d'annonce ;
                             SEULES 4 ont un compte actif
LES 2 COMMERCIAUX ACTIFS     portent 125 et 916 lignes : ce sont de vrais negociateurs
USAGE REEL                   0 travail demande par un commercial, depuis toujours
                             (86 217 par les services, 3 351 par des admins)
LE CIRCUIT DE DEMANDE EXISTE app_diffusion_request, 3 types (diffusion, baisse de prix,
                             annulation de mandat) : 9 demandes EN TOUT, toutes posees par
                             un ADMIN, la derniere le 02/06/2026 -> il dort
FONCTIONS JOIGNABLES         les 11 RPC de gestes sont executables par « authenticated » et
                             fermees a « anon » : le chantier ① tient, c'est bien le controle
                             de role INTERNE qui refuse, pas un droit d'execution
NON MESURE                   la derniere connexion de chaque compte : le schema « auth »
                             refuse mes lectures (3 essais, connexion coupee)
```

### L'HISTORIQUE — *pourquoi c'est comme ça*

- **20/05/2026** — la liste du commercial naît avec **3** types de documents
  (`patch_archive_annonce_detail_request_2026-05-20.sql`), elle grandit jusqu'à **7**.
- **21/05/2026** — statut et archivage sont **réservés à l'admin**
  (`patch_console_change_annonce_status_2026-05-21.sql`, l. 48) : **aucune raison écrite**,
  ni dans le patch, ni au journal des décisions.
- **24/08/2026** *(journal des décisions)* — « **À l'étape 2, les négociateurs n'ouvrent
  plus Hektor** » : la décision de les faire travailler dans l'app est prise depuis
  six semaines ; les droits n'ont jamais suivi.
- **25/08/2026 (E.0)** — la décision suppose un **circuit de demande de validation** pour
  les transactions : **il n'en existe aucun** (seulement diffusion, baisse de prix,
  annulation de mandat).
- **30/08/2026** — `patch_c4_droits_jamais_null` garde le cas particulier mais le rend
  sûr : un rôle inconnu rendait `NULL`, et `not NULL` vaut `NULL`, donc le garde-fou ne
  se déclenchait pas. **C'était un correctif de sécurité, pas une décision métier** : il
  ne dit rien sur ce qu'un négociateur doit pouvoir faire.
- Le plan prévoit déjà un **pilote** avant l'ouverture à tous (liste des étapes, nº 10 :
  « LE PILOTE S'OUVRE : quelques négociateurs », puis nº 14 « puis tous les négociateurs »).

### CE QUI ATTEND FRÉDÉRIC — *la décision, en trois questions*

1. **Que fait un négociateur seul sur SES biens ?** → **répondu le 12/10 : option B**
2. **Le rôle `manager`** → **répondu le 12/10 : idem admin pour l'instant**
3. **Les comptes** : pilote d'abord → **répondu le 12/10 : oui, tester avant**

---
---

# AUDIT DU 12/10/2026 — *refait et élargi, en lecture seule*

> Demandé par Frédéric : *« Refait un audit […] mais cela ne doit surtout pas changer les
> worker […] normalement tout existe déjà audit mieux »*, puis *« tu n'as pas audité les
> consultations ? »*.
> Tout ce qui suit est **mesuré ce jour** sur la base et le code. Aucune écriture.

## A. CE QUI N'A PAS BOUGÉ depuis le 09/10

| vérification | résultat |
|---|---|
| le corps des 2 portes et de `is_app_admin` | **identiques** *(relus par `pg_get_functiondef`)* |
| comptes : 4 admins actifs, 2 commerciaux actifs, 0 manager, 1+1 désactivés | **identique** |
| travaux demandés par un commercial | **toujours 0** |
| `isAdmin` dans `App.tsx` | **toujours 49** |
| les 6 fonctions « affaire » réservées à l'admin | **exactement 6** |
| commits touchant aux droits depuis le 09/10 | **aucun** |

## B. « TOUT EXISTE DÉJÀ » — Frédéric avait raison

Le circuit de demande n'est pas un squelette : **c'est l'option B, déjà codée de bout en
bout, pour 3 gestes.**

| ce qui existe | preuve |
|---|---|
| la table porte : type, statut, commentaire, motif, réponse de l'admin, motif de refus, qui a traité et quand, **relances**, **suivi à rappeler** | 25 colonnes de `app_diffusion_request` |
| un **journal / fil de discussion** entre le négociateur et le validateur | `app_diffusion_request_event` |
| **deux rôles d'écran déjà séparés** : `nego` (demande) et `pauline` (traite) | `App.tsx:8103`, 11792, 12632 |
| **trois tableaux de bord d'accueil** : `admin`, `commercial`, `pauline` | `App.tsx:305`, branché l. 21316 |
| **`request_type` est un texte SANS contrainte** → ajouter un type **ne demande aucun patch SQL** | `pg_constraint` : seulement la clé et 2 clés étrangères |
| la limite des 3 types est **une seule ligne du front** | `App.tsx:302` |

### Les droits du circuit sont DÉJÀ l'option B, et déjà conformes à la réponse Q2

| règle | ce qu'elle dit | verdict |
|---|---|---|
| poser une demande | `requested_by = moi` **ET** c'est **mon bien** | ✅ un négociateur peut **déjà** demander, sans patch |
| voir les demandes | ses biens ; tout pour admin / manager / lecture | ✅ |
| **traiter une demande** | **`is_app_manager_or_admin()`** = admin **+ manager** | ✅ **« manager = idem admin » est déjà le code en place** |

Et `handleCreateDiffusionRequest` (`App.tsx:16785`) **n'a aucun contrôle de rôle**.

### LE PATRON COMPLET EXISTE — et il ne touche pas aux workers

À l'acceptation d'une demande d'annulation de mandat (`App.tsx:16869-16960`), l'app :
1. enregistre la décision dans la demande ;
2. décoche *Valide* et *Diffuse* chez Hektor ;
3. **crée un travail `change_hektor_annonce_status` (clôture)**, posé par **le compte de
   l'admin qui valide**.

➡ **Le worker reçoit le même travail qu'aujourd'hui, du même type de compte.** C'est le
patron réutilisable pour les gestes manquants, **sans toucher au worker**.

### Les 9 demandes réelles

```
4  demande_annulation_mandat  acceptees   13-14/05/2026
4  demande_baisse_prix        acceptees   13/05/2026
1  demande_diffusion          EN ATTENTE DEPUIS LE 02/06/2026  <-- 4 mois sans reponse
```

## C. LES WORKERS NE BOUGENT PAS — *la contrainte ferme de Frédéric, vérifiée*

| vérification | résultat |
|---|---|
| `app_diffusion_request` dans `Console/` | **0 occurrence** |
| dans `backend/` | **0 occurrence** |
| dans `scheduled/` et les scripts du run | **0 occurrence** |
| la clé du worker | **clé de service** (`SUPABASE_SERVICE_ROLE_KEY`, l. 1265) → **ignore** toutes ces règles |
| les `role` que lit le worker | le rôle du **jeton Hektor** (sans rapport) ; et l. 2397 pour **choisir à qui écrire** : *« si le demandeur est un commercial, envoyer le message à son adresse »* → **déjà prévu** |

➡ Dans `phase2`, `app_diffusion_request` n'apparaît **qu'en descente de doublure** (lecture).

## D. L'IDENTITÉ CHEZ HEKTOR — *question de Frédéric du 12/10*

> *« si je donne accès à la modification des annonces aux commerciaux au sein de l'agence,
> le worker partira toujours à Hektor avec le compte du commercial en charge et non
> l'utilisateur ? »*

**Réponse : OUI, c'est bien le négociateur en charge du bien.** Mécanisme mesuré :

1. le worker se connecte avec le **compte admin technique** ;
2. il **bascule** dans le compte du négociateur cible — autoconnexion Hektor
   `?call=authenticate&mode=autologin&idUser=<cible>` (`switchHektorUserContextWithPlaywright`) ;
3. il **vérifie** l'identité obtenue ;
4. si la bascule n'est pas confirmée **et** qu'une autre identité est visible, **il
   s'arrête avant d'écrire** (`console_job_worker.js:2896`).

### L'ordre de choix du négociateur cible — `resolveHektorExecutionUser` (l. 2334)

| ordre | règle | ligne |
|---|---|---|
| 1 | le négociateur **posé dans la charge du travail** (`hektor_user_id`) gagne toujours | 2335 |
| 2 | sinon **le négociateur en charge du bien** (`commercial_id` → annuaire d'agence) | 2380 |
| 3 | sinon par e-mail : **(a)** le demandeur s'il est commercial · **(b)** le négociateur du bien · **(c)** l'adresse de la charge · **(d)** le demandeur quel qu'il soit | 2395-2400 |
| 4 | rien trouvé → **le travail échoue** (« Contexte negociateur Hektor requis ») | 2825 |

**Le cas 3(a) ne peut pas se produire pour un commercial** : il n'a accès qu'aux biens dont
**il est** le négociateur — les deux identités sont la même personne.

```
MESURE   13 475 annonces vivantes · 4 226 (31 %) SANS commercial_id · 4 227 sans email de nego
         -> ce sont justement celles ou la regle 2 ne s'applique pas, et un commercial
            n'y a de toute facon AUCUN acces (l'acces passe par l'email du negociateur)
```

### Deux réserves

| | |
|---|---|
| **repli par l'agence** | si le négociateur du bien est **inactif chez Hektor**, l'écriture part sous le contexte **de l'agence**. ⚠ **Interrupteur ACTIF** : `CONSOLE_HEKTOR_AGENCY_FALLBACK=true` (`Console/.env:143`) |
| **vérification facultative** | `CONSOLE_HEKTOR_ALLOW_UNVERIFIED_CONTEXT=true` (lanceur l. 37-38 et service l. 217) : si le worker ne peut pas vérifier qui il est devenu, et qu'aucune autre identité n'est visible, **il écrit quand même** |

## E. 🔴 POINT 2i — LES CONSULTATIONS : le cloisonnement est un filtre, pas une serrure

> C'est la deuxième question de Frédéric, et elle **corrige mon audit du 09/10**.

### Les règles existent bien sur les tables

| ce qu'on consulte | règle de lecture | limitée ? |
|---|---|---|
| annonces vivantes (`app_dossier_current`) | lecteur global **ou ses biens** | ✅ |
| contacts (`app_contact_current`) | ses contacts, ou ceux de ses biens | ✅ |
| liens (`app_contact_relation_current`) | ses biens | ✅ |
| recherches (`app_contact_search_current`) | ses contacts | ✅ |
| documents (`app_console_document`) | ses biens | ✅ |
| photos (`app_console_photo`) | ses biens | ✅ |
| **archives** (`app_archive_annonce_index_current`) | `is_app_user_active()` | 🔴 **aucune limite** |
| **vendus / clos** (`app_historical_annonce_index_current`) | `is_app_user_active()` | 🔴 **aucune limite** |
| **mandats** (`app_mandat`) | `is_app_user_active()` | 🔴 **aucune limite** |
| **affaires** (`app_affaire_ledger` : offres, compromis, ventes, **commissions**) | `is_app_user_active()` | 🔴 **aucune limite** |
| comptes (`app_user_profile`) | soi-même ou admin | ✅ |

### Mais l'écran lit des VUES qui ignorent ces règles

Une vue n'applique les règles des tables en dessous que si elle porte le réglage
`security_invoker`. **Sur 24 vues `app_*`, il est absent.** Six sont lisibles par tout
compte connecté :

| vue | ce qu'elle expose | lue par l'écran |
|---|---|---|
| **`app_dossiers_current`** | **toutes les annonces** | **13 fois** — dont la **liste principale** (`dossiersCurrentView`, `api.ts:168`) et « ouvrir une annonce par son n° » |
| **`app_contacts_current`** | **tous les contacts** | **7 fois** (`contactsCurrentView`, `api.ts:169`) |
| **`app_registre_mandats_current`** | **tout le registre des mandats** | **5 fois** |
| `app_contact_relations_current` | tous les liens | via l'écran contacts |
| `app_contacts_sans_numero` · `app_console_action_abandonnees` | listes techniques | non |

Et la seule limite réelle est **un filtre posé par le navigateur** :

```
api.ts:2432     applyNegotiatorScopeToQuery -> .eq('negociateur_email', <son adresse>)
App.tsx:12730   le filtre n'est pose QUE si profile.role === 'commercial'
```

➡ **Filtre d'affichage, pas serrure.** Décidé par l'écran, pas par la base.

### ⚠ Ce n'est PAS un trou public — le chantier ① tient

**Aucune** de ces vues n'est lisible par `anon` (mesuré : `has_table_privilege('anon', …)`
= faux partout). Vitrine, photos publiques, espace client et RDV **ne sont pas concernés**.
C'est un trou **entre collègues**. Il ne se voit pas aujourd'hui parce que les seuls
comptes non-admin sont **2 commerciaux qui n'ont jamais rien fait**.

## F. TROIS ERREURS DE MON AUDIT DU 09/10, corrigées

| ce que j'avais écrit | la vérité mesurée le 12/10 |
|---|---|
| « la lecture est déjà faite, le trou est uniquement en écriture » | **FAUX** : l'écran lit des vues qui contournent les règles (point 2i) |
| « contact : créer, modifier, **supprimer** = oui pour un commercial » | **FAUX pour supprimer** : `delete_hektor_contact` n'est pas dans sa liste, et le bouton est réservé à l'admin (`canDeleteContacts={isAdmin}`) |
| « le front, c'est **49 endroits** à changer » | **TROMPEUR** : une **seule** définition (`App.tsx:17730 const isAdmin = profile?.role === 'admin'`) ; les 48 autres en découlent |

Et **deux compléments** à l'audit du 09/10 :
- la porte 1 commande **18** fonctions, pas 16 — dont **4 qui ne font que LIRE** l'état d'un
  travail (`app_action_status`, `app_annonce_edit_status`, `app_action_resolve`,
  `app_annonce_pending_resolve`) : aujourd'hui un négociateur ne peut pas **voir
  l'avancement** de sa propre saisie ;
- **les répartitions de commission sont attachées exprès au droit « changer le statut »**
  (`app_repartition_commission_set` : *« LE MEME CONTROLE QUE LA MODALE QUI PORTE LA
  SAISIE »*) → ouvrir le statut ouvre les commissions, par construction.

## G. NOTÉ, HORS CHANTIER — à ne pas poursuivre ici

`app_espace_edit_search_optimistic` (modifier une recherche depuis **l'espace client**)
n'a **aucun contrôle de rôle** dans son corps. Elle est probablement protégée par un jeton
ailleurs, **non vérifié**. Sujet du chantier ① (sécurité / public), pas du ②.

## H. CE QUI RESTE NON MESURÉ

- la **dernière connexion** de chaque compte (le schéma `auth` refuse mes lectures) ;
- la répartition des travaux par rôle depuis le 09/10 (requête expirée : le run tournait) ;
- si les boutons de demande sont **visibles** pour un négociateur **à l'écran** : lu dans le
  code, **jamais vu avec un vrai compte commercial** ;
- les gestes **RDV / visite** : le bon de visite est autonome dans l'écran, je n'ai pas
  vérifié s'il est gardé par un rôle.

## I. ⭐ LES DÉCISIONS DE FRÉDÉRIC — *prises le 12/10/2026*

> Prises sur la fiche `notice/CHANTIER_2_REPONSES_A_REMPLIR.md`, qu'il a remplie, puis
> affinées en 7 arbitrages. **La fiche remplie reste la trace d'origine, on ne la modifie pas.**

### I.1 Les décisions de cadrage

| | décision |
|---|---|
| **l'ordre** | **L4 cloisonner les consultations D'ABORD**, puis L2, puis L3, puis L1 |
| **le prix** | reste **sous demande** |
| **le rôle `manager`** | **idem admin**, avec deux exceptions voulues *(voir I.3, point 5)* |
| **le pilote** | **tester avant d'ouvrir à tous**, avec les **comptes déjà créés** |
| **l'agence d'un compte** | **déduite de l'annuaire Hektor** (adresse → agence active) — rien à saisir |
| **contrainte ferme** | *« cela ne doit surtout pas changer les worker »* → **vérifié, aucun changement worker** |

### I.2 ⭐ R2 — LE PÉRIMÈTRE EST UNE PROPRIÉTÉ DU COMPTE, PAS UN NOUVEAU RÔLE

Frédéric voulait *« un type Agent commercial avec uniquement accès à ses annonces, ses
contacts etc… donc bien plus fermé que le compte négociateur »*. **Il a choisi R2.**

- ❌ **PAS** de 5ᵉ valeur de rôle. `app_role` reste **`admin | manager | commercial |
  lecture`**. Raison : une valeur d'énumération PostgreSQL **ne peut jamais être retirée** —
  c'eût été le seul geste irréversible de tout le chantier.
- ✅ À la place : une **case « périmètre » sur le compte**, réversible (une colonne qu'on
  peut retirer), et qui permet de régler deux négociateurs différemment dans la même agence.

### I.3 Les 7 arbitrages du 12/10 — *chacun contre une objection que j'avais soulevée*

| # | mon objection | la décision de Frédéric |
|---|---|---|
| **1** | désarchiver en `S`+`R` laisse un négociateur ressortir **n'importe quelle** annonce du réseau, alors qu'archiver lui est interdit | **« NON, laisse S+R »** — assumé |
| **2** | modifier un contact / ajouter / modifier une recherche en `S`+`R` : il **modifie** ceux des collègues | **« garde comme demandé, ce n'est pas une erreur »** — assumé |
| **3** | supprimer un document chez Hektor est **définitif** (Hektor + serveur + cloud) | **`S`+`B`** — le négociateur le fait seul, sur ses biens |
| **4** | statut, archivage et transactions en `A` → **plus aucune demande n'existe**, le lot L3 devient vide | **« Oui »** — ⚠ *à reconfirmer en une ligne : voir I.5* |
| **5** | Santé admin seul mais Utilisateurs admin+manager : le manager crée des comptes sans voir la surveillance | **« Oui »** — voulu. **Ce sont les 2 exceptions à « manager = idem admin »** |
| **6** | mandants = tout le réseau mais registre des mandats = ses biens : les deux lisent la même matière | **CHANGEMENT** : mandants restent **tout le réseau**, et **la VUE REGISTRE DES MANDATS devient un écran réservé ADMIN + MANAGER, comme la vue Suivi** — le négociateur n'y entre plus du tout |
| **7** | R1 (5ᵉ rôle) ou R2 (case périmètre) | **« Oui R2 »** |

### I.4 Ce que la grille devient — *la règle à coder*

**Deux notions qui se combinent**, et c'est ce qui fait marcher R2 :

1. **la GRILLE DU RÔLE `commercial`** — par objet, la portée que Frédéric a fixée :
   - **tout le réseau** : annonces, contacts, recherches, rapprochements, archives,
     vendus/clos, photos, estimations, mandants, liste des négociateurs ;
   - **ses biens / ses contacts** : affaires, **commissions**, documents, agenda, statistiques ;
   - **écran interdit** : Suivi, Santé, **Registre des mandats** *(décision 6)*.
2. **la CASE « PÉRIMÈTRE » du compte** *(R2)* agit comme un **PLAFOND** qui **abaisse** la
   grille :
   - périmètre *réseau* → le compte obtient la grille telle quelle **(le négociateur)** ;
   - périmètre *portefeuille* → **toutes** les portées retombent à ses biens
     **(l'agent commercial)** ;
   - périmètre *agence* → les portées « réseau » retombent à son agence.

⚠ **Cette lecture en « plafond » est MA proposition de mise en œuvre, pas encore validée.**
Elle évite d'avoir à remplir une deuxième fiche entière pour l'agent commercial.

### I.5 CE QU'IL RESTE À CONFIRMER — 2 lignes, rien de plus

```
(a) decision 4 : le negociateur ne DEMANDE RIEN dans l'app pour le statut, l'archivage
    et les transactions -- il passe par l'agence. Donc le lot L3 est SUPPRIME.
    (cela annule sa reponse C2 « 2 types de demande d'abord »)
(b) le PILOTE : Melanie LEGRAND (Saint-Etienne, 142 vivantes / 774 archivees / 130 vendues)
    et Emanuelle PEREIRA (Firminy, 102 / 24 / 7) -- DEUX AGENCES, aucun compte a creer.
    Frederic avait coche « une agence moyenne » : les comptes existants donnent mieux.
(c) la lecture en « plafond » de I.4 est-elle la bonne ?
```

### I.6 Les lots, après décision

| lot | état |
|---|---|
| **L4** cloisonner les consultations | ✅ **le premier**, et le plus gros |
| **L2** ce que le négociateur fait seul | ✅ confirmé |
| **L5** la notion d'agence *(déduite de l'annuaire)* | ✅ nécessaire *(brouillon d'annonce = son agence)* |
| **L6** la case « périmètre » du compte *(R2)* | ✅ nouveau, réversible |
| **L7** l'écran Registre des mandats réservé admin+manager | ✅ nouveau *(décision 6)* |
| **L3** les demandes qui manquent | ❌ **SUPPRIMÉ** sous réserve de I.5 (a) |
| **L1** manager = admin | ✅ confirmé, **sauf** Santé *(admin seul)* |

**Rien n'est codé. Aucune écriture n'a été faite.**

---
---

# LOT L4 — CLOISONNER LES CONSULTATIONS

> Audit du **12/10/2026**, en lecture seule. Premier lot, choisi par Frédéric.

## L4.1 Trois risques écartés par la mesure

| ce que je redoutais | mesuré |
|---|---|
| casser les **4 workers**, le backend Render, `phase2`, le run de nuit, les crons | ✅ **impossible** : `service_role` a **`rolbypassrls = true`** — la clé de service ignore toute règle RLS, quoi qu'on pose |
| une **erreur de permission** à l'écran *(avec `security_invoker`, l'appelant doit avoir `SELECT` sur les tables sous la vue)* | ✅ **écarté** : `authenticated` a `SELECT` sur **les 13 tables** concernées |
| devoir inventer une règle par objet | ✅ **l'outil existe déjà** : `app_console_can_access_dossier` teste les **3 index** *(vivant, archives, vendus)* et répond « oui » immédiatement pour admin / manager |

## L4.2 🔴 L'ADRESSE DU NÉGOCIATEUR MANQUE SUR LA MOITIÉ DU PASSÉ — et c'est irréparable

| objet | lignes | **sans adresse de négociateur** | sans agence |
|---|---|---|---|
| archives | 35 318 | **23 412 — 66 %** | **0** |
| vendus / clos | 8 940 | **4 536 — 51 %** | **0** |
| registre des mandats | 24 502 | **13 004 — 53 %** | **0** |

**Pas rattrapable** : sur les 23 412 archives sans adresse, **763 seulement** portent un
identifiant ou un nom de négociateur → **22 649 lignes n'ont aucune trace** de qui tenait le
bien. *(Registre : 13 004 sans adresse, dont 87 avec identifiant.)*

➡ **Cloisonner ces trois objets « par négociateur » est techniquement impossible.**
➡ **L'AGENCE, elle, est TOUJOURS là — zéro manquante sur les trois.** C'est le seul axe de
cloisonnement utilisable sur le passé.

**Sans conséquence pour la grille actuelle** *(Frédéric a mis `R` sur archives et vendus)*,
**mais décisif pour R2** : ⭐ **Q1 tranchée le 12/10 → OPTION 3, ASSUMÉE** — un compte au
périmètre « portefeuille » **perd les archives et les vendus qui n'ont pas son adresse**
*(66 % et 51 % du total)*. Décision de Frédéric, à ne pas renverser.

## L4.3 ⚠ Poser la serrure telle quelle IRAIT CONTRE la grille

Frédéric a répondu **`R` (tout le réseau)** pour les annonces, les contacts et les mandants.
Or la règle qui dort sous ces vues dit *« ses biens » / « ses contacts »*. **Poser simplement
`security_invoker` produirait l'inverse de sa décision.**

➡ **CONCLUSION : L4 et L6 (la case « périmètre ») ne peuvent pas être séparés.** Pour dire
« réseau pour un négociateur, portefeuille pour un agent commercial », il faut la case
périmètre **en même temps** que la serrure ; seule, la serrure ne sait exprimer qu'une
portée, et ce n'est pas celle qu'il veut.

## L4.4 ⚠ IL Y A QUATRE VUES À RÉGLER, PAS TROIS

`app_registre_mandats_current` est **elle aussi** une vue sans `security_invoker`. Changer la
règle de sa table (`app_mandat_register_current`) **ne suffirait pas** : la vue continuerait de
tout montrer. Elle doit recevoir le réglage comme les trois autres.

Et ⚠ **chaîne de vues** : `app_contact_relations_current` lit **`app_dossiers_current`**, qui
est elle-même une vue à régler → **les quatre ensemble, ou aucune.**

## L4.5 Ce qui reste à cloisonner, et par quoi

| objet | décision | rattachement | faisable |
|---|---|---|---|
| **affaires + commissions** `app_affaire_ledger` *(31 058 l.)* | ses biens | `app_dossier_id` **rempli 100 %** *(0 vide)* | ✅ |
| **mandats** `app_mandat` *(26 851 l.)* | ⭐ **Q2 → option 1** : le **bandeau mandat reste visible sur ses biens** | `app_dossier_id` **rempli 100 %** | ✅ |
| **registre des mandats** *(l'écran)* | **admin + manager** *(décision 6)* | — | ✅ |
| annonces, contacts, liens, archives, vendus, photos, estimations | tout le réseau | — | ✅ **rien à changer** |

**Mesure du cloisonnement des affaires**, sur les 2 comptes du pilote *(via les 3 index)* :
**Mélanie LEGRAND 479 affaires sur 31 058** · **Emanuelle PEREIRA 42**. Elle garde bien ses
biens vivants **et** archivés **et** vendus.

## L4.6 ⭐ L'ÉTAT D'AVANT — *relevé le 12/10, c'est LE retour arrière*

### Les 6 règles de lecture

| objet | règle | condition | empreinte md5 |
|---|---|---|---|
| `app_dossier_current` | `app_dossier_current_select_scoped_users` | `(SELECT is_app_global_reader()) OR can_access_negotiator_email(negociateur_email)` | `c5109c98cb7801ed5b81b3d38e9d3105` |
| `app_contact_current` | `app_contact_current_select_scoped` | global reader **ou** son adresse **ou** `EXISTS` sur un lien de ses dossiers | `2818e450186a422804f3eda93025da02` |
| `app_contact_relation_current` | `app_contact_relation_current_select_scoped` | global reader **ou** `can_access_current_dossier(app_dossier_id)` | `aba52a7eb4745a58b7ea130c7bfc9e60` |
| `app_affaire_ledger` | `app_affaire_ledger_select_active_users` | `is_app_user_active()` | `71bef22dc7c148dc362e8670c90245b3` |
| `app_mandat` | `app_mandat_select_active_users` | `is_app_user_active()` | `71bef22dc7c148dc362e8670c90245b3` |
| `app_mandat_register_current` | `app_mandat_register_current_select_active_users` | `is_app_user_active()` | `71bef22dc7c148dc362e8670c90245b3` |

*(les 3 dernières partagent la même empreinte : c'est la même condition, mot pour mot)*

### Les 6 vues — **toutes en `security_invoker` NON POSÉ**, toutes lisibles par `authenticated`

| vue | empreinte de la définition | taille | sort prévu |
|---|---|---|---|
| `app_dossiers_current` | `0dad1adca33e590c2f871a4778e3516e` | 1 813 | 🔧 régler |
| `app_contacts_current` | `8004d10588f97fc08b7ab2e3f2508bec` | 919 | 🔧 régler |
| `app_contact_relations_current` | `6c89ceb7052f335a11514c92c47d550f` | 2 595 | 🔧 régler |
| `app_registre_mandats_current` | `ac950ac5f689d4eeae2ca066efe5c132` | 1 875 | 🔧 régler *(L4.4)* |
| `app_contacts_sans_numero` | `df7d08615abf99eb5389a0a90c795117` | 4 547 | 🚫 retirer le droit de lecture *(non lue par l'écran)* |
| `app_console_action_abandonnees` | `71fd3bc298903e3645ef7ce7cee282eb` | 539 | 🚫 retirer le droit de lecture *(non lue par l'écran)* |

## L4.7 ⭐ LA RÉPÉTITION EST EXACTE — *23 mesures sur 23, le 12/10 vers 09:45*

**Option A choisie par Frédéric.** Fichiers : `supabase/patch_l4_cloisonnement_2026-10-12.sql`,
son `_INVERSE.sql`, et la `_REPETITION.sql` **assemblée par**
`supabase/generer_repetition_l4.py` *(leçon du point 4d : aucune divergence possible entre
ce qu'on éprouve et ce qu'on applique)*.

| mesure | AVANT | APRÈS PATCH | APRÈS INVERSE |
|---|---|---|---|
| vues qui regardent leur gardien | **0** | **4** | **0** |
| vues techniques lisibles par un compte | **2** | **0** | **2** |
| case « périmètre » | absente | **présente** | absente |
| comptes hors réseau | 0 | **0** | 0 |
| fonctions neuves présentes | 0 | **4** | 0 |
| fonctions neuves **ouvertes sans compte** | 0 | **0** ✅ *chantier ① intact* | 0 |
| fonctions neuves **utilisables par un compte** | 0 | **4** ✅ *l'écran marchera* | 0 |
| **règles qui ne reviennent pas à leur état d'origine** | — | — | **0** ✅ |

Les **8 empreintes de AVANT sont identiques à celles de APRÈS INVERSE** : le retour arrière
est exact, prouvé, pas supposé.

### ⭐ LES 8 EMPREINTES À RETROUVER APRÈS LE VRAI COLLAGE

*(c'est le contrôle du résultat : si une seule diffère, le patch n'a pas fait ce qu'il a fait
en répétition)*

| règle de lecture | empreinte attendue APRÈS le patch |
|---|---|
| `app_dossier_current` | `bebfbd39f19ada2ad8f37d7b28eef4b4` |
| `app_archive_annonce_index_current` | `bebfbd39f19ada2ad8f37d7b28eef4b4` |
| `app_historical_annonce_index_current` | `bebfbd39f19ada2ad8f37d7b28eef4b4` |
| `app_contact_current` | `075389d63245e6794da9a4c0874edf71` |
| `app_contact_relation_current` | `fd9ce6dd0bdf7ecf29d728e37b028577` |
| `app_affaire_ledger` | `2d3aa9390e6cb527a55d9d347d19d52b` |
| `app_mandat` | `ce33e869d64b7a831686a25795362032` |
| `app_mandat_register_current` | `71f003c898951218afb6036efc2c1279` |

⭐ **Trois règles partagent la même empreinte** *(annonces, archives, vendus)* : c'est normal
et c'est une **preuve de cohérence** — les trois portent la même condition,
`app_voit_cette_ligne(negociateur_email, agence_nom)`.

### Deux défauts de MON code, trouvés avant le collage

1. le garde-fou ne couvrait que **6 des 8** règles remplacées *(archives et vendus oubliés)* ;
2. `like 'regle__%'` : dans un `LIKE`, `_` est un **joker** → remplacé par `starts_with`
   *(piège déjà payé le 08/10 sur une mesure SQLite)*.

### ⚠ Et un troisième, trouvé par le PREMIER essai de Frédéric

```
ERROR 42703: column "perimetre" does not exist
```

**Un `CASE` ne protège pas d'une colonne absente** : PostgreSQL **analyse** toute la requête
avant de l'exécuter, **branche non prise comprise**. Aux étapes AVANT et APRÈS INVERSE la
colonne n'existe pas → l'analyse échouait avant la première mesure.
➡ Corrigé par **`to_jsonb(p) ->> 'perimetre'`**, qui rend NULL quand la colonne est absente :
**la même ligne de code marche aux trois étapes.**
Les 3 autres références directes à la colonne ont été auditées et sont saines *(corps de
fonction analysé après l'`ALTER TABLE` · bloc `DO` compilé à l'exécution · `EXECUTE format`
dynamique)*, et l'inverse supprime bien **la fonction avant la colonne**.

## L4.8 ✅ PATCH L4 APPLIQUÉ par Frédéric le 12/10 vers 09:55 — contrôle

### Ce qui est prouvé

| contrôle | résultat |
|---|---|
| les **8 empreintes** des règles | **8/8 CONFORMES** à la répétition |
| 4 vues réglées · 2 fuites fermées · 4 fonctions neuves | **4 · 0 · 4** |
| fonctions joignables **sans compte** | **0** — chantier ① intact |
| **ADMIN** *(compte de Frédéric, emprunté le temps d'une lecture)* | **rien perdu** : 13 475 annonces · 62 189 contacts · 24 502 registre · 35 318 archives · 8 940 vendus · 26 851 mandats |
| **Mélanie — affaires de SON bien 1346424** | **3** ✅ |
| **Mélanie — affaires du bien 1357257 d'un COLLÈGUE** | **0** ✅ ⭐ **le cloisonnement fonctionne** |
| **Mélanie — écran Registre des mandats** | **0** ✅ fermé |
| Mélanie — annonces | **13 475**, tout le réseau ✅ conforme à la grille |
| Mélanie — son agence déduite de l'annuaire | **Groupe GTI Saint-Étienne** ✅ |
| Mélanie — 50 premiers contacts *(ce que fait une page de liste)* | instantané ✅ |

⭐ **La méthode qui a permis ce contrôle sans toucher au compte de personne** :
`BEGIN; SET LOCAL ROLE authenticated; SET LOCAL request.jwt.claims = '{"sub":"<uuid>"}';
<lectures>; ROLLBACK;` — **à réutiliser pour tout contrôle de droits.** Aucune écriture,
aucun mot de passe, et on voit exactement ce que la personne verrait.

### 🔴 LE DÉFAUT : L'ÉCRAN DES ARCHIVES MET 8,15 s POUR UN NÉGOCIATEUR

**Erreur de forme, pas de fond, et elle est de moi.** J'ai appelé mes fonctions
directement dans les règles — `using (app_voit_cette_ligne(negociateur_email, agence_nom))` —
donc PostgreSQL les évalue **une fois par ligne** *(35 318 fois pour les archives)*, et
chacune rappelle `is_app_global_reader()` et `app_perimetre_courant()` à chaque ligne.
Les règles **d'origine** utilisaient exprès `(select is_app_global_reader())`, une
sous-requête non corrélée évaluée **une seule fois** — forme que **j'avais repérée dans
l'audit L4.1 et citée comme un bon point**, sans l'appliquer.

| touché ? | |
|---|---|
| l'admin | ✅ **jamais** — le court-circuit joue |
| les contacts d'un négociateur | ✅ rapides : l'écran demande un comptage **estimé** (`count: 'planned'`, `api.ts:3169`), pas exact |
| les affaires d'une fiche | ✅ instantané : l'écran les lit **toujours par annonce** (`.eq('app_dossier_id', …)`, `api.ts:1914`, **seul** endroit) |
| **les archives d'un négociateur** | ⚠ **8,15 s** — l'écran y fait un comptage **exact** (`count: 'exact'`, `api.ts:4576`) |
| un comptage de toutes les affaires | ⚠ expire — **mais l'app ne le fait jamais** |

⚠ **DEUX FOIS, MA PREMIÈRE ALERTE A ÉTÉ TROP FORTE** *(et c'est la leçon à garder)* :
j'ai d'abord mesuré un `count(*)` sur 31 058 affaires et annoncé que l'app serait
inutilisable. **Ce geste n'existe nulle part dans l'app.** En regardant comment l'écran lit
vraiment, le seul vrai défaut est celui des archives.
➡ **Mesurer LE GESTE DE L'ÉCRAN, pas un geste plausible.**

**Personne n'est gêné aujourd'hui** : les deux seuls comptes non-admin actifs n'ont jamais
rien fait dans l'app. Mais il faut corriger **avant le pilote**.

## L4.9 LOT L4-BIS — LA VITESSE *(option A de Frédéric, 12/10)*

Fichiers : `supabase/patch_l4bis_vitesse_2026-10-12.sql`, son `_INVERSE.sql`, la
`_REPETITION.sql` assemblée par `supabase/generer_repetition_l4bis.py`.

**Aucune décision n'est revue — la forme seule change.**

| ce qui change | de | à |
|---|---|---|
| les parties constantes | appelées **par ligne** | `(select …)` → **une seule fois** |
| `can_access_negotiator_email(email)` par ligne | une requête par ligne | comparaison à une **sous-requête scalaire** *(le rôle `commercial` est testé dedans, donc un rôle inconnu rend NULL → faux, comme avant)* |
| `app_console_can_access_dossier(id, hid)` par ligne | 3 `EXISTS` par ligne | **deux appartenances** à un ensemble calculé une fois : `app_mes_biens_portefeuille()` |
| les liens | la fonction de périmètre par ligne | `app_mes_biens_selon_perimetre()`, un ensemble |

**Les deux chemins sont conservés** *(`app_dossier_id` **et** `hektor_annonce_id`)*, comme
la fonction d'origine : mesure du 12/10, les deux colonnes sont remplies à **100 %** dans
`app_affaire_ledger` et `app_mandat`, mais on ne supprime pas un chemin sans nécessité.

**La règle du registre des mandats n'est PAS touchée** : elle ne lit aucune colonne, elle
s'évalue déjà une seule fois.

⚠ **Ce que la répétition de L4-bis ne peut PAS prouver** : que les mêmes comptes voient les
mêmes lignes. Elle tourne en propriétaire de la base, qui ignore ces règles. Cette preuve se
fait en **empruntant chaque identité** avant/après le collage — les nombres d'avant sont
dans le tableau de L4.8.

**La chaîne de retour arrière** : `L4-BIS_INVERSE` → état L4 *(la lenteur revient, c'est
voulu)* ; puis `L4_INVERSE` → état d'origine.

### ⭐ RÉPÉTITION L4-BIS : EXACTE — *12/10, les deux contrôles tiennent*

```
REGLES QUI NE REVIENNENT PAS A LEUR ETAT D'ORIGINE : 0   (0 attendu)
REGLES QUE LE PATCH N'A PAS CHANGEES               : 0   (0 attendu)
```

Le **second** contrôle est neuf par rapport à la répétition de L4, et il valait la peine :
un patch qui ne changerait rien passerait le premier sans faire son travail.

| mesure | AVANT | APRÈS PATCH | APRÈS INVERSE |
|---|---|---|---|
| ensembles présents | 0 | **2** | 0 |
| ensembles **ouverts sans compte** | 0 | **0** ✅ | 0 |
| ensembles utilisables par un compte | 0 | **2** ✅ | 0 |
| **fonctions de L4 intactes** | 4 | **4** ✅ *(L4-bis n'en supprime aucune)* | 4 |
| règles de lecture au total | 8 | **8** | 8 |
| registre des mandats réservé | oui | **oui** ✅ *(pas touché)* | oui |

### LES 7 EMPREINTES À RETROUVER APRÈS LE VRAI COLLAGE DE L4-BIS

| règle | empreinte attendue |
|---|---|
| `app_dossier_current` | `0d7da391e87088d5d7ec6c9bcf34763f` |
| `app_archive_annonce_index_current` | `0d7da391e87088d5d7ec6c9bcf34763f` |
| `app_historical_annonce_index_current` | `0d7da391e87088d5d7ec6c9bcf34763f` |
| `app_contact_current` | `8a1da0e3c256e15977233073ac2e2d45` |
| `app_contact_relation_current` | `e9e9ead71ab10b5c128bfae8ea228510` |
| `app_affaire_ledger` | `73d92b58e78ee20e7b249416929fba53` |
| `app_mandat` | `21ff276c6d7ac3c48f73664ed6cf56e3` |

Comme pour L4, **trois partagent la même empreinte** *(annonces, archives, vendus)* : preuve
que la même condition a bien été posée aux trois endroits.

### Les 9 nombres à retrouver, identiques, après le collage

*(relevés avant L4-bis en empruntant chaque identité — c'est la preuve que la forme seule
a changé)*

```
ADMIN     13 475 annonces · 62 189 contacts · 24 502 registre
          35 318 archives · 8 940 vendus · 26 851 mandats
MELANIE   13 475 annonces · 3 affaires sur son bien 1346424
          0 affaire sur le bien 1357257 d'un collegue · 0 au registre
          agence deduite « Groupe GTI Saint-Etienne »
          ARCHIVES : 8,15 s  <<< le seul chiffre qui DOIT changer (vers < 1 s)
```

**Deux versions sans commentaires** ont été produites pour pouvoir être collées depuis un
téléphone *(même code, lignes de commentaire et lignes vides retirées, jamais en milieu de
ligne pour ne pas casser la chaîne « ESSAI ANNULE -- … »)* :
`*_REPETITION_COMPACTE.sql` *(487 lignes au lieu de 733)* et `*_COMPACT.sql`
*(269 au lieu de 378)*.

**NON MESURÉ** : le **coût en temps** d'une règle par ligne sur 31 058 affaires pour un
négociateur *(nul pour un admin : la forme `(SELECT …)` n'est évaluée qu'une fois)*.
**À chronométrer avant de valider.**
