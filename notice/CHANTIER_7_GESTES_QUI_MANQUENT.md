# CHANTIER ⑦ — LES GESTES QUI MANQUENT

> **Note ouverte le 14/10/2026.** Le chantier n'est pas commencé : cette note **rassemble** ce qui
> s'y accumule, pour qu'on n'ait pas à le retrouver dans trois endroits le jour venu.
> *(Les items venaient de `CLAUDE.md` l. 115, 267 et 424.)*

**Ordre de Frédéric : ① ⑤ ④ ② puis ③ → ⑥ → ⑦ ⑧.**

---

## 📋 LES POINTS DU CHANTIER ET LEUR ÉTAT — *tableau ouvert le 15/10, à tenir à jour*

| # | le point | état |
|---|---|---|
| ⑦-1 | **archiver / désarchiver un contact** | 🔎 audité le 14/10, **re-audité le 15/10** — en cours |
| ⑦-2 | **le cas Gladys DURIEUX** *(fiche archivée, mandante d'une annonce active)* | ⬜ va avec ⑦-1 *(sa décision du 14/10)* |
| ⑦-3a | **clôturer un mandat à la main** + le **crayon** de la date de clôture *(périmètre élargi par Frédéric le 16/10 : toutes les entrées, droits admin/manager, dates modifiables)* | 🔎 **audité à fond le 16/10** — voir la section en bas de note |
| ⑦-3b | l'**écran du journal des suppressions** | ⬜ reçu du chantier ③ |
| ⑦-3c | **réordonner / choisir la photo principale** *(`mode=ordonne_photos` connu)* | ⬜ reçu du chantier ③ |
| ⑦-4 | le **bandeau qui ment** *(« désarchiver » promis à un bien non archivé)* | ⬜ |
| ⑦-5 | relancer / abandonner depuis le monitoring, biens cliquables | ✅ **fait le 15/10** |
| ⑦-6 | « Abandonner » **défait** le geste | ✅ **fait le 15/10** |
| ⑦-7 | **modifier ou prolonger un mandat** *(audit 08/10 : ni RPC ni travail worker ; l'avenant ne change que le prix)* | ⬜ |
| ⑦-8 | **photos : rendre visible / masquer** *(E.0-bis ; « retirer » est fait depuis le 14/10)* | ⬜ |
| ⑦-9 | **renommer un document** *(audit 08/10, § Documents C2)* | ⬜ |
| ⑦-10 | `app_brouillon_annonce_detail_cache` **vide et rien ne la remplit** *(venu du chantier ⑥, 14/10)* | ⬜ **question** : seulement si Frédéric en a l'usage |

> ⚠ Les points ⑦-7, ⑦-8, ⑦-9 viennent du **§2 ⑦ de l'audit du 08/10** et ⑦-10 du chantier ⑥ :
> ils manquaient à cette note, qui ne portait que ce que les sessions y avaient déposé.
> **L'ordre de traitement ne se décide pas sans Frédéric.**

---

## ⑦-1 · ARCHIVER ET DÉSARCHIVER UN CONTACT — *audité le 14/10, à la demande de Frédéric*

### La réponse : **l'app ne sait pas le faire**, et c'est établi par quatre chemins

| source | ce qu'elle dit |
|---|---|
| **la base** *(ce qui a réellement tourné)* | **9** types de gestes « contact » depuis mai : `refresh_console_contact_data` (477) · `update_hektor_contact_search` (24) · `update_hektor_contact` (23) · `create_hektor_mandant_contact` (17) · `create_hektor_contact` (16) · **`delete_hektor_contact` (13)** · `update_hektor_mandant_contact` (10) · `add_hektor_contact_search` (4) · `delete_hektor_contact_search` (3). **Aucun archivage.** |
| **le worker** | il sait archiver une **recherche** — `archiveHektorContactSearch()`, mode Hektor `contacts-contactProfile-modifDateArchiveCritere`. Pour la **fiche contact**, il **lit** `archive` *(l. 2202)* mais **ne l'écrit jamais**. |
| **l'écran** | **aucun bouton** « archiver » ni « désarchiver » sur une fiche contact. |
| **la liste des gestes du chantier ②** | elle porte « **supprimer un contact** » — **pas** « archiver ». |

*Et dans `git log`, tous les commits « archiver / désarchiver » concernent **les annonces**.*

### L'asymétrie, qui est le vrai sujet

| objet | archiver | désarchiver | supprimer |
|---|---|---|---|
| **annonce** | ✅ | ✅ | ✅ |
| **recherche** | ✅ | ❌ | ✅ |
| **contact** | ❌ | ❌ | ✅ *(13 fois)* |

> **Sur un contact, l'app ne connaît que le tout ou rien : on le supprime, ou on le garde.**
> Or **archiver** un contact est un geste courant — un acquéreur qui a acheté, un vendeur parti.

### ⚠ CE QU'IL FAUDRA TROUVER D'ABORD

**La commande Hektor pour archiver une FICHE CONTACT est INCONNUE.** Le worker connaît
`modifDateArchiveCritere` **pour une recherche** ; l'équivalent sur la fiche n'a jamais été
relevé.

➡ **Même méthode que « supprimer une photo »** *(audit du 25/09 : « les trouver d'abord »,
commande trouvée le 14/10 par un relevé en lecture seule)* : **un relevé, en lecture seule,
avant d'écrire la moindre ligne.**

### 🔎 RE-AUDIT DU 15/10 — *le geste manque toujours, et **la commande était chez nous***

**Verdict : CONFIRMÉ** pour le geste, **FAUX** pour « la commande est inconnue ».

⭐⭐ **La commande Hektor dormait dans une capture du 01/06** —
`Console/exports/impersonate_create_annonce_2026-06-01T09-42-48-999Z/labs_contactsRefonte.js:436`
*(fichier servi par `…/admin/?call=getJs&js=labs/contacts/labs_contactsRefonte.js`, URL dans
le `report.json` de la capture)* :

```
POST xmlrpc.php   mode=contacts-contactProfile-archiveContact & id=<idContact> & archive=<0|1>
```

enveloppée dans `setArchiveContact(archive)` *(l. 422-441)*, avec la confirmation de Hektor
« êtes-vous sûr de vouloir **archiver** / **activer** ce contact ? ».
⭐ **UN SEUL mode pour les deux sens** : c'est le paramètre `archive` qui décide — donc
« désarchiver » ne demande rien de plus que « archiver ».
*(Troisième fois qu'une commande dite inconnue était déjà payée : `delete_img` le 13/05,
`archiveUnarchiveContactRecherche` dans `Console/exports/probe_recherche_tab.txt`.)*
⚠ `git log -S "archiveContact"` : **0 commit**, **0 note** — jamais utilisée, jamais écrite.

**Les quatre chemins du 14/10, re-mesurés le 15/10 :**

| | mesure du 15/10 |
|---|---|
| **la base** | 11 types de travaux « contact » ou « archive » ont tourné ; le seul archivage est **`archive_hektor_annonce` (7, dernier le 13/10)** — **aucun archivage de fiche contact** |
| **verrou 1 — la contrainte** | `app_console_job_job_type_check` porte **43 types**, aucun pour archiver un contact |
| **verrou 2 — les droits** | `app_console_can_request_contact_job` ne nomme que 5 types *(création + modification + les 3 recherches)* ; admin et manager passent partout |
| **verrou 3 — la distribution** | `app_console_claim_next_job` : `delete_hektor_contact` est dans la liste du service **« gestes d'état »** — c'est là qu'irait l'archivage |
| **le worker** | il modifie un contact par `mode=contacts-saveDataEditContact` *(l. 17202+13)*, archive une **recherche** par `modifDateArchiveCritere` *(l. 18340)* ; `archive` n'est que **LU** *(l. 2217 et 2252)* |
| **l'écran** | `contactArchiveLabel` *(App.tsx:35591)* ne sert qu'à **afficher** une pastille *(:42242)* et à filtrer l'annuaire *(api.ts:2367-2368, 2459-2460)* ; `isArchived` existe **en deux copies** *(:40070 fiche V1, :40737 fiche V2)* et ne commande **aucun bouton** |

**⑦-2 Gladys DURIEUX, mesurée le 15/10** : toujours **archivée**, `ville` =
**Saint-Romain-Lachalm** *(la note du 14/10 disait Saint-Étienne : c'est son **agence**)*,
**1 recherche active**, éligible pour **deux** raisons
*(`["active_annonce_relation","active_search"]`)*.

**⚠ Non mesuré** *(règle du prompt : aucun appel à Hektor pendant un audit)* : si la commande
a changé depuis juin, et si archiver la **fiche** entraîne l'archivage de ses **critères**
*(la page porte un « autoarchivage »)*. **C'est l'objet du relevé en lecture seule.**

### 🔬 AUDIT APPROFONDI DU 15/10 — *demandé par Frédéric : « tes explications sont un peu légères »*

> **Audit limité à l'objet CONTACT, geste ARCHIVER / DÉSARCHIVER.** Les autres objets ne sont
> mesurés que là où ils touchent ce geste.

#### ① Le bouton de Hektor, retrouvé une SECONDE fois — et c'est un INTERRUPTEUR

`Console/exports/probe_search_listing_603882_2026-06-12…/fiche.html` *(capture d'une vraie
fiche contact, 12/06 — onze jours après l'autre, et elles concordent)* :

```
.switchButtonState  rel="on"  -> setArchiveContact(true, …)   = archiver
.switchButtonState  rel="off" -> setArchiveContact(false, …)  = reactiver
```

⭐ **Et la fonction de rappel ne fait QUE de l'animation** *(elle bascule l'image de
l'interrupteur et cache un bloc)* : **dans la page, archiver un contact ne touche à rien
d'autre.** Le doute sur les critères ne peut donc plus venir que du **serveur de Hektor**,
invisible pour nous — c'est tout ce qui reste à relever.

#### ② L'ampleur : archiver est un geste du QUOTIDIEN chez Hektor, impossible chez nous

| mesure du 15/10 | |
|---|---|
| contacts dans le miroir local *(`data/hektor.sqlite`, lecture seule)* | **356 515**, dont **184 128 archivés** = **52 %** |
| contacts dans notre cloud | **62 234**, dont **22 643 archivés** (36 %) — tous **éligibles** *(0 non éligible)* |
| archivages faits **par l'app** depuis toujours | **0** |
| suppressions faites par l'app | **13** — et ⭐ **les 13 sont des fiches d'ESSAI** *(603745, 603746, 603751, 603796, 604135, 605093-95, 605414/429/450/453, et 10355757 le contact d'essai du projet)*. **Aucun vrai client n'a jamais été supprimé par l'app.** |

➡ **Le seul geste que l'app possède sur ce sujet (« supprimer ») n'a jamais servi en vrai, et
le geste dont l'agence se sert tous les jours (« archiver ») n'existe pas.**

#### ③ Des fiches archivées portent encore du travail en cours

Fiches **archivées** qui sont **mandantes** d'une annonce du parc vivant *(jointure sur
`app_dossier_current`)* :

| statut de l'annonce | contacts archivés | annonces |
|---|---|---|
| Estimation | 160 | 76 |
| **Actif** | **44** | **42** |
| Sous offre | 6 | 5 |
| Sous compromis | 5 | 5 |

➡ **Gladys n'est pas « le dernier cas »** : elle est le dernier cas de **sa** famille
*(fiche archivée **+ recherche active**)*. La famille **« fiche archivée + mandat en cours »**
compte **55 contacts sur 52 biens réellement en vente** *(215 / 128 en comptant les
estimations)*. *(Leçon 9 : ce que Frédéric signale est un symptôme, jamais le périmètre.)*

#### ④ Ce que l'archivage change AUJOURD'HUI, mesuré geste par geste

| | effet, et sa preuve |
|---|---|
| l'annuaire des contacts | **la fiche disparaît de la liste** : le filtre par défaut est « actifs » *(`App.tsx:379`)* |
| la fiche elle-même | une pastille « Archivé » *(`:42242`)* ; **on peut toujours la modifier** *(aucun contrôle sur `archive` dans `app_edit_contact_optimistic`)*, et ⭐ **Hektor accepte d'écrire sur une fiche archivée** *(mesuré le 09/10 : 4 archivés + 2 actifs, tous ont répondu)* |
| le rapprochement | **il continue** : il regarde la **RECHERCHE**, pas la fiche. ⭐ Preuve : **Gladys a 2 rapprochements éligibles, meilleur score 100/100** — et elle est **le seul** contact archivé dans tout le moteur *(2 lignes sur 52 020)* |
| notre cloud | **la fiche reste** : l'éligibilité ne regarde pas `archive` *(`build_contacts_layer.py:1749-1753`)* |
| ⚠⚠ le vrai danger | si la **recherche** est archivée en même temps **et** qu'il n'y a pas d'annonce active, la fiche **sort de l'éligibilité → elle est SUPPRIMÉE de notre cloud la nuit suivante** *(`-ContactsEligibleOnly -AllowStaleSupabaseDeletes`, `find_stale_row_keys`)*. C'est ce qui est arrivé aux **35 fiches** du 14/10 |
| les internautes | **rien** : **0 droit** pour un visiteur non connecté sur `app_contact_current` et `app_contacts_current` |

#### ⑤ Le pourquoi : le projet avait DÉJÀ prévu ce geste, en juin

`CAHIER_CHARGES_DOUBLONS_CONTACTS_2026-06-29.md` nomme **deux actions** qui demandent
exactement ce geste *(l. 236-237)* :
`restore_archive_error` = *« cas archivé à tort, après validation »* · et
`archive_secondary_candidate` = *« proposition d'archivage, non automatique »*.
⚠ **Et la même note interdit l'« archivage direct » dans les premiers lots** *(l. 243)*, avec
*« ne pas archiver automatiquement »* en priorité 4 *(l. 184)*. **Lecture à confirmer par
Frédéric** : cette interdiction porte sur l'**outil doublons** *(qui doit proposer, pas agir)*
— pas forcément sur un **bouton manuel** sur une fiche. **Je ne tranche pas.**

#### ⑤-bis ✅ LE RELEVÉ EST FAIT — *15/10, accord de Frédéric (« 1. oui »)*

**Outil** : `Console/sonde_archive_contact.js` *(patron de `sonde_photos_suppression.js`)*.
**Contrat tenu** : session du worker **réutilisée et non réécrite**, aucune connexion, **aucun
POST**, aucun appel à `xmlrpc.php`, aucune fiche touchée — **un GET** sur le fichier
JavaScript de la page Contacts *(`/admin/?call=getJs&js=labs/contacts/labs_contactsRefonte.js`,
**200**, 74 891 caractères)*. La copie est gardée dans
`Console/exports/sonde_archive_contact_2026-10-15/` : **plus besoin de rappeler Hektor.**

**Résultat : la commande est CONFIRMÉE, inchangée depuis juin.**

```
POST xmlrpc.php   mode=contacts-contactProfile-archiveContact
                  id=<idContact>   archive=<true|false>
```

| | |
|---|---|
| `setArchiveContact` | **identique** à juin — empreinte `fc22f6b4…` des **deux** côtés |
| `deleteContact` *(témoin)* | identique **à l'octet près** |
| le fichier entier | **différent** *(74 217 → 74 891)* : Hektor a bougé **ailleurs**, pas ici |

⚠ **Et un piège évité par la mesure** : au premier passage, l'empreinte **brute** de
`setArchiveContact` différait → *« la commande a changé ! »*. **Faux.** La capture de juin
avait été écrite avec un **encodage abîmé** *(« Ãªtes-vous sÃ»r » au lieu de « êtes-vous
sûr »)* : la seule différence était **deux accents**. La sonde porte désormais une **seconde
empreinte, sans les accents** — et elle rend **IDENTIQUE**. *(Même famille que les retours
chariot : la différence était dans la **mesure**, pas dans la chose.)*

**La cascade sur les recherches : rien dans le navigateur.** Dans le fichier d'aujourd'hui,
ni `modifDateArchiveCritere`, ni « autoarchivage », ni « critère » n'apparaissent **dans**
`setArchiveContact` *(ils existent ailleurs dans le fichier, pour les recherches)*.
➡ **Il ne reste qu'une inconnue : ce que le serveur de Hektor fait en recevant l'ordre.**
Aucune lecture ne peut le dire — **seul un essai sur une fiche d'essai**, avec accord.

#### ⑤-ter OÙ VA LE BOUTON — *et quelle fiche contact est RÉELLEMENT en ligne (question de Frédéric)*

**Il n'existe PAS de fiche contact V3.** Le front n'a que **deux** fiches et **un** interrupteur :
`ContactDetailPopup` *(App.tsx:41845)* → `ContactDetailPopupV2` *(:40667)* si
`VITE_APP_CONTACT_V2_ENABLED`, sinon `ContactDetailPopupBase` *(:39714)*. Les **3** endroits
qui ouvrent une fiche passent par ce même aiguillage *(:21083, :42109, :42256)* → **le bouton
ne s'écrit qu'une fois par fiche.**

⚠ **Deux numérotations se croisent, et c'est la source de la confusion** :

| | |
|---|---|
| le **code** | la fiche portée s'appelle **V2** *(`contact-detail-v2.css`, classes `fa-cx-*`)* |
| les **maquettes** | `maquettes/detail-contact-v26 … v30` — la V2 du code **est le portage de `detail-contact-v30-dashboard.html`** *(`PLAN_DEV_CONTACT_V2.md`)*, et un commentaire du cockpit parle même de « Contact v34 » |
| le seul **V3** du front | **Mandat V3** *(`fa-mandat-v3.css`, `VITE_APP_MANDAT_V3_ENABLED`)* — facile à confondre |

**Preuve que la V2 est en ligne, par un SECOND chemin** *(je n'ai pas pu lire la variable chez
Vercel : **403, droit refusé**)* : dans le fichier que l'app sert *(`/assets/index-Cwrhht31.js`,
2,27 Mo)*, les **trois** interrupteurs valent `"true"`, et l'aiguillage du contact s'y lit
`KI ? <V2> : <Base>` avec `KI = "true"` *(les deux autres gardent le cockpit `fa-ck-` et le
mandat)*. Concordant avec `plan-portage-contact-v2` *(flag allumé en prod le 19-24/07,
vérifié à l'écran par Frédéric à l'époque)*.

**La place du bouton** : dans le menu **« … »** de l'en-tête de la fiche V2
*(`fa-cx-act-menu`, App.tsx:41314-41326)*, **juste au-dessus de « Supprimer »**, libellé
« Archiver ce contact » / « Réactiver ce contact » selon `isArchived` *(déjà calculé :40737)*.
La pastille **« Actif / Archivé »** est à côté *(:41366)* : l'effet se voit au même endroit.
Le **même item** va dans le menu de la fiche Base *(`menu-pop`, :40136-40142)*, avec **un seul
morceau de code partagé** — sinon le jour où l'interrupteur serait éteint, le bouton
disparaîtrait.

**Le droit à utiliser** : `canManageContacts` *(:18325 — admin, manager **et commercial**)*,
celui qui garde déjà « Modifier » — **c'est exactement l'option B de Frédéric, et il n'y a rien
à brancher**. ⚠ Mais au front ce droit ne connaît que le **rôle**, pas « ce contact est-il à
moi » : un négociateur verrait l'item sur le contact d'un collègue et la base refuserait —
**comme « Modifier » aujourd'hui**. ➡ Soit on garde ce comportement avec un **refus en
français clair**, soit le front recalcule « à moi » *(il n'en connaît que la moitié)*.
**Question posée, non tranchée.**

#### ⑤-quater LE PATCH EST ÉCRIT *(15/10, dormant — rien n'est appliqué)*

**Les décisions de Frédéric, appliquées** : `2 = B` *(le négociateur sur ses contacts)* ·
`3 = un seul geste` *(le sens est dans la charge, comme Hektor)* · `1 = le menu « … »` ·
`2 = a` *(le bouton reste visible, le refus s'explique → la fonction lève une **phrase en
français**, pas un code machine)* · **Gladys seule** *(les 54 autres ne sont pas touchées)*.

| fichier | ce qu'il fait |
|---|---|
| `supabase/patch_chantier7_archiver_contact_2026-10-15.sql` | les **3 verrous** + la fonction de saisie |
| `…_INVERSE.sql` | retire tout ; **refuse** s'il reste un travail de ce type |
| `…_REPETITION.sql` | avant → patch → mesures → inverse → retour → **erreur volontaire** qui annule tout |

**Le choix du service : `actions`, pas `admin`.** Ce n'est pas un goût : c'est la règle écrite
dans le worker pour cette liste — *« même session négociateur, même objet, même famille de
geste »*. `admin` travaille avec la **session admin** et porte les gestes réservés
*(supprimer un contact)*, que le négociateur n'a pas.

**Mesuré avant d'écrire une ligne** *(15/10)* : les **3 ancres apparaissent exactement 1 fois**,
le type n'est **nulle part**, la fonction de saisie n'existe pas, `app_console_job` porte
**95 483 lignes** *(coût de la revalidation de la contrainte)*, `archive` est un **booléen**,
et **aucun autre consommateur** ne connaît ce geste *(les 5 objets qui nomment
`delete_hektor_contact` sont les 3 verrous + ses 2 fonctions de saisie)*.

⚠ **Le filet de rejeu n'est PAS touché** : un échec sonnera dans l'écran Santé. Et **un travail
de contact n'a pas de bandeau « Abandonner »** *(le bandeau exige un numéro d'annonce)* —
dit, pas découvert.
⚠ **Collage** : **0 ancre multi-ligne, 0 texte inséré multi-ligne** → la panne du 15/10 *(CRLF
sur une ancre multi-ligne)* ne peut pas se reproduire ici ; et les corps réécrits sont lus
**sans retours chariot**, donc aucun CR n'entre dans la base.
⭐ **Les mesures de la répétition sont elles-mêmes éprouvées** *(en lecture seule, 15/10)* :
l'extraction de la branche « actions » trouve `unlink_hektor_mandant` **oui** et la branche
« admin » **non** *(témoin inverse : l'extraction isole vraiment la branche)*, la lecture d'un
droit par signature rend `authenticated` **oui** / `anon` **non**, et « supprimer un contact »
est bien **hors** de la liste du commercial.
⚠ **Et le témoin de l'insert ne dépend plus de ce que l'épreuve annule** *(leçon du 13/10)* :
le résultat passe par une **variable**, écrite **après** le point de reprise.

#### ⑤-quinquies ✅ LA RÉPÉTITION EST PASSÉE — *23 lignes sur 23, 16/10 au matin*

Frédéric l'a collée : **le message rendu est mot pour mot celui que la note annonçait.**

| | |
|---|---|
| **avant** | le type n'est ni dans la contrainte, ni dans les droits, ni dans la distribution ; la fonction de saisie est absente ; les **3 empreintes** sont celles mesurées la veille |
| **après** | type dans la contrainte **oui** · dans les droits **oui** · dans la branche **actions oui** · dans la branche **admin non** · fonction **présente** · `authenticated` **oui** / `anon` **non** · **insert d'un vrai travail du type : accepté** *(puis annulé)* · « supprimer un contact » **toujours hors de la liste du commercial** |
| **retour** | tout retiré, fonction absente, et les **3 empreintes IDENTIQUES** |

⭐ **Les deux sens sont prouvés** *(leçon 2)* : le patch **a changé** quelque chose, et
l'inverse **revient à l'octet près**. → le vrai patch peut être collé.

#### ⑤-sexies ✅✅ LE PATCH EST EN PRODUCTION — *collé par Frédéric le 16/10 vers 00:25, contrôle 8/8*

| contrôle en base | résultat |
|---|---|
| verrou 1, la contrainte | **oui** |
| verrou 2, les droits | **oui** |
| verrou 3, branche **actions** | **oui** |
| verrou 3, branche **admin** | **non** — le geste n'a PAS rejoint la session admin |
| la fonction de saisie | **présente** (1) |
| droit `authenticated` / `anon` | **oui** / **non** |
| « supprimer un contact » | **toujours hors de la liste du commercial** |

**Empreintes d'APRÈS, à citer dans tout futur inverse** *(sans les retours chariot)* :
droits **19d0fc0b1f4f22b0a91a05809ebe94bb** · distribution **4da660742838e4e0849bbd70b7b9a7f5** ·
fonction de saisie **85e3c91dc701b4a60d9e2fb07d805e4d**.

⚠ **Un détail mesuré, pas deviné** : la **fonction neuve** porte des **retours chariot** dans
son corps *(collée depuis Windows)*, les **deux fonctions modifiées non** — parce que le patch
les a lues avec `replace(..., chr(13), '')`. **Sans conséquence aujourd'hui** *(l'inverse la
supprime par sa signature, le front l'appelle par son nom)*, mais un futur patch qui voudrait
s'ancrer **dans** ce corps se ferait mordre. Nettoyage possible en 6 lignes
*(relire + réexécuter ; `CREATE OR REPLACE` garde les droits)* — proposé, non fait.

#### ⑤-septies LE WORKER ET L'ÉCRAN SONT ÉCRITS — *16/10, go « ENCHAINE »*

**Le worker** *(`Console/console_job_worker.js`)* — **les 5 endroits**, tous additifs :

| | |
|---|---|
| `ACTION_JOB_TYPES` *(l. 97)* | le type rejoint la **session négociateur**, pas `ADMIN_JOB_TYPES` — même règle que la branche `actions` en base |
| le bras `archiverHektorContact` | `POST xmlrpc.php` · `mode=contacts-contactProfile-archiveContact` · `id` · `archive=true|false` — **tel que le relevé l'a lu**, avec le `Referer` de la fiche contact |
| `handleArchiveHektorContact` | patron de `handleUpdateHektorContact` recopié : traduction **identité → cible**, contexte d'exécution, bascule dans le compte du négociateur, puis **un rafraîchissement de la fiche** *(c'est Hektor qui confirme)* |
| l'aiguillage *(l. 21205)* | `case 'archive_hektor_contact'` |
| les libellés et la liste à notifier | « L'archivage (ou la réactivation) du contact » — **vrai dans les deux sens**, puisqu'un seul type les porte |

⭐ **Le sens ne s'invente jamais** : sans le booléen dans la charge, le bras **refuse**.
Un défaut à `false` aurait pu **désarchiver** un contact qu'on voulait archiver.
⛔ **Inerte jusqu'au redémarrage des QUATRE services.**

**L'écran** — l'item est dans le menu « … » des **deux** fiches *(V2 `fa-cx-menu-item`,
Base `menu-item`)*, **au-dessus de « Supprimer »**, libellé **« Archiver » / « Réactiver »**
selon l'état. ⭐ **Un seul morceau de code pour les deux fiches** *(`useArchivageContact`)* :
deux copies divergeraient. Le droit utilisé est **`canManageContacts`** *(admin, manager **et**
commercial)* — l'option B, **sans rien brancher**. Le `confirm` **dit la vérité** *(« sa fiche
sort de l'annuaire, rien n'est supprimé, le geste se défait par le même bouton »)*, et le
refus de la base s'affiche **tel quel**.

**Épreuves** : `node --check` sur le worker *(il ne le LANCE pas)* · **`npm run build` vert**
*(bundle neuf `index-CRuWIgLd.js`)* · et **3 suites du projet rejouées, toutes vertes** :
`test_porte_contacts` **23/23**, `test_suite_creation_avertie`, `test_envoi_hektor_differe`.
⚠ **Rien n'est poussé** : l'écran n'existera qu'après le push de Frédéric.

#### ✅✅⭐ L'ESSAI RÉEL A RÉUSSI DU PREMIER COUP — *16/10, 07:29:36 → 07:30:08*

**Gladys DURIEUX est réactivée, et c'est l'app qui l'a fait.**

| étape | mesure |
|---|---|
| le travail | **1 seule tentative**, `done` · demandé **07:29:36**, pris **07:29:46**, fini **07:29:52** — **16 secondes** |
| **le service qui l'a pris** | ⭐ **`actions`** *(`NS31851120:actions:service:v9`)* — exactement celui choisi, **pas** `admin` |
| la charge | `archive: false`, et l'**état d'avant** (`{archive: true}`) est bien dedans |
| **la réponse de Hektor** | ⭐ **`{"success": "Modification archivage ok"}`** — dans ses propres mots |
| **les deux numéros** | notre identité **10059959** → cible Hektor **113412** : la traduction a marché en production, du premier coup |
| le rafraîchissement | `refresh_console_contact_data` enfilé tout seul, **fini 07:30:08**, `synced` |

**⭐⭐ ET LA DERNIÈRE INCONNUE EST FERMÉE — par le VRAI chemin.** Après le
rafraîchissement *(donc **relu chez Hektor**, pas notre écriture optimiste)* :

| | avant, 07:28:12 | après, 07:30:26 |
|---|---|---|
| sa fiche | archivée | ✅ **active** |
| sa recherche **n° 0** | archivée | **archivée** — inchangée |
| sa recherche **n° 1** | active | **active** — inchangée |
| son éligibilité | les 2 raisons | les 2 raisons |

➡ **Réactiver une fiche ne touche PAS ses recherches.** Ses deux recherches, l'une archivée
et l'autre active, étaient la **sonde parfaite** : aucune des deux n'a bougé.
⚠ **Ce qui reste à prouver, et je ne l'extrapole pas** : l'autre sens *(**archiver**)* pourrait
être asymétrique côté serveur Hektor *(archiver une fiche pourrait auto-archiver ses
critères)*. Le risque est **beaucoup plus faible** qu'hier *(la page ne fait rien d'autre, et
le serveur n'a rien cascadé dans ce sens-là)*, mais ça se mesure **sur une fiche jetable**,
pas sur un client.

**À ce stade, le point ⑦-1 est FAIT** : base en production, worker vivant *(4 services
redémarrés 07:25:26)*, écran en ligne *(commit `1fbce99`, déploiement Vercel READY, les
textes neufs dans le fichier servi)*, et **un vrai client réparé**. ⭐ **Et le cas ⑦-2 est
réglé par la même occasion.**

#### ⚠⚠⚠ 16/10 — **CE QUE L'ESSAI A VRAIMENT MONTRÉ** *(et l'erreur de vocabulaire que j'ai faite)*

> ⚠⚠ **CORRECTION DU 16/10, après que Frédéric a regardé dans Hektor et n'y a RIEN vu.**
> J'avais écrit « la cascade ARCHIVE ses recherches ». **Mauvais mot, et le projet l'avait
> déjà écrit** : `AUDIT_RECHERCHES_ORPHELINES_2026-10-14.md` dit noir sur blanc
> — *« le champ qui porte l'état d'une recherche s'appelle… **`archive`** » · **« sur une
> RECHERCHE, archive veut dire INACTIVE »** · *« normalement une recherche est active ou
> inactive »* (Frédéric) — **deux objets, deux sens, un seul mot**.
> ➡ Il n'y a donc **rien à voir dans l'écran de Hektor** : une recherche ne s'« archive » pas,
> elle est **active ou inactive**. *(Le champ « Auto-archivage le » de l'écran est une date
> **programmée** — vide ici.)* Et la chaîne de conséquences que j'ai présentée comme une
> découverte est **exactement les 7 maillons** de l'audit du 14/10.

**Ce qui est MESURÉ : la recherche n° 1 de Gladys est passée d'ACTIVE à INACTIVE entre deux
lectures fraîches de Hektor**, et c'est le champ dont **toute l'app dépend** *(éligibilité,
rapprochement)*.
**Ce qui N'EST PAS ÉTABLI : qui l'a rendue inactive.** Mon attribution à notre geste repose sur
notre avant/après, pas sur une preuve directe.

**La démonstration tient à DEUX LECTURES FRAÎCHES qui encadrent le geste** *(donc ce n'est pas
une supposition : c'est Hektor qui parle, deux fois)* :

| heure | ce qui s'est passé | sa recherche n° 1 |
|---|---|---|
| **07:30:08** | relecture chez Hektor **réussie** *(après la réactivation)* | **ACTIVE** |
| **07:56:26** | **archiver** la fiche — Hektor : *« Modification archivage ok »* | *(relecture de 07:57 **échouée** : verrou de la descente → on n'a rien vu)* |
| **08:14:18** | **réactiver** la fiche — Hektor : *« ok »* | |
| **08:14:39** | relecture chez Hektor **réussie** | ⚠ **INACTIVE** |

**Les dégâts, mesurés sur Gladys** *(un vrai client)* :

| | avant | après |
|---|---|---|
| sa fiche | archivée | ✅ **active** *(réparé)* |
| sa recherche n° 1 *(prix max 123 456)* | **active** | ⚠ **inactive** |
| `active_search_count` | 1 | **0** |
| ses raisons d'éligibilité | annonce active **+ recherche active** | **annonce active** seule |
| ses rapprochements éligibles | **2** *(dont un à **100/100**)* | ⚠ **0** |

⭐ **ET C'EST EXACTEMENT POURQUOI ELLE AVAIT ÉTÉ CHOISIE** : avec son annonce active, elle
**ne peut pas tomber du cloud**. Sur une fiche sans annonce active et sans transaction,
l'archivage lui aurait fait perdre **sa dernière raison d'être là** → **supprimée du cloud à
la nuit suivante**, comme les 35 fiches du 14/10. **Le risque annoncé était le bon risque.**

⚠ **ET LA RÉPARATION NE PEUT PAS SE FAIRE DEPUIS L'APP** : il n'existe **aucun geste
« désarchiver une recherche »** *(c'est l'asymétrie du tableau de ⑦-1 : la recherche
s'archive, elle ne se désarchive pas)*. Sa recherche n° 1 doit être rouverte **à la main dans
Hektor**. ⭐ Le mode existe pourtant chez eux — `contacts-contactProfile-recherche-archiveUnarchiveContactRecherche`, vu dans `Console/exports/probe_recherche_tab.txt` — donc le geste
est **trouvable**, c'est un point à ouvrir.


**⭐ LA MESURE QUI SITUE LE CAS, refaite le 16/10** *(le même tableau que l'audit du 14/10)* :

| | avec une recherche **active** | sans |
|---|---|---|
| fiche **non archivée** | **3 961** | 151 |
| fiche **ARCHIVÉE** | ⚠ **0** *(c'était **1** le 14/10 : Gladys)* | 6 157 |

➡ **Sur 6 157 fiches archivées, AUCUNE n'a de recherche active.** Gladys était la dernière
exception ; elle ne l'est plus. La règle « fiche archivée ⇒ recherches inactives » est donc
**très fortement suggérée** par les nombres — mais **suggérée, pas prouvée** : seul un essai
sur une fiche **jetable** trancherait.

**La réparation, dans les bons mots** : sa recherche n° 1 doit être **remise ACTIVE** dans
Hektor *(pas « désarchivée »)*. L'app ne sait pas le faire : elle sait **rendre inactive**
*(`modifDateArchiveCritere`)*, pas **réactiver**.

### 🔎 CE QUE DISENT LES NOTES SUR LES RECHERCHES — *audit demandé le 16/10*

**① CONFIRMÉ — le geste de l'app rend la recherche INACTIVE en POSANT UNE DATE.** Trois
sources concordantes :

| source | ce qu'elle dit |
|---|---|
| `LISTE_TACHES_A_COCHER` l. 686-687 | *« **CE N'EST PAS UNE SUPPRESSION mais un ARCHIVAGE** : le worker appelle `archiveHektorContactSearch` et rend « status: archived ». **Hektor ne sait pas supprimer une recherche, il pose une date.** »* |
| `AUDIT_RECHERCHES_AUTONOMIE_2026-09-21` | **Supprimer** : *« Sans objet — Hektor ne sait pas supprimer une recherche, **il archive** »* · **Archiver** : 3 archivages depuis l'app |
| le worker *(l. 18331-18345)* | `modifDateArchiveCritere` avec **`dateArchive` = la date du jour** |

**② NON CONFIRMÉ — « sans possibilité de la remettre active ».** **Aucune note du projet ne le
dit**, et **le code de Hektor d'aujourd'hui dit le contraire** *(relevé du 15/10,
`labs_contactsRefonte.js`)* :

```
function archiveUnarchiveContactRecherche(idCritere, idContact)   <- une BASCULE
    POST xmlrpc.php  mode=contacts-contactProfile-recherche-archiveUnarchiveContactRecherche

function updateDateAutoArchiveCritere(idCritere)                  <- le champ DATE de l'ecran
    POST ... modifDateArchiveCritere & dateArchive=<date saisie>
    success: if (data['desarchiveCritere']) archiveUnarchiveContactRecherche(...)
```

➡ **Changer la date d'auto-archivage REACTIVE la recherche** : le serveur répond
`desarchiveCritere`, et la page bascule l'état. *(Dans la capture de juin, une recherche
**active** portait « Auto-archivage le **05-06-2028** » — une date **future**.)*
⚠ **Je lis le code du navigateur, je ne l'ai pas exécuté.** Le test décisif est de trente
secondes, et il est **chez Frédéric**.

**③ EN REVANCHE, C'EST VRAI DE NOTRE APP** : elle ne connaît **que** `modifDateArchiveCritere`
*(poser une date)*. **Elle ne sait pas réactiver** — c'est l'asymétrie déjà notée.

**④ ⭐ ET LE DÉTAIL QUI CHANGE LE DIAGNOSTIC DE GLADYS** : à l'écran de Hektor, sa recherche
porte **« Auto-archivage le » VIDE**. Or le seul geste d'archivage que l'app sache faire
**pose une date**. ➡ **Sa recherche n'a donc PAS été désactivée par une date** — ni par l'app,
ni par un auto-archivage programmé. **C'est un autre mécanisme qui a basculé l'état**, ce qui
reste cohérent avec la règle « fiche archivée ⇒ recherches inactives » *(0 sur 6 157)*, sans
la prouver.

### ✅ VU DE MES YEUX DANS HEKTOR — *16/10, session Chrome de Frédéric, lecture seule*

**① LE MARQUEUR EXISTE DANS L'ÉCRAN : c'est un CADENAS.** Les deux recherches de Gladys
portent **🔒** à côté de leur nom *(« Recherche 1 🔒 », « Recherche 2 🔒 »)*, et les deux sont
`archive = "1"` dans l'API. ⭐ **Témoin** : dans la capture de juin *(`probe_recherche_tab.txt`,
contact 603882, recherche **active**)*, le libellé « Recherche 1 » **ne porte aucun cadenas**.

**② ⚠ ET J'AVAIS DIT « la date d'auto-archivage est VIDE » : C'ÉTAIT FAUX.** Elle vaut
**22-06-2028** *(exactement « création + 2 ans » : créée le 22-06-2026)*. Je l'avais lue avec
une extraction de **texte**, qui **ne voit pas la valeur d'un champ de saisie**. **Deuxième
mesure de la matinée faussée par la même famille d'erreur : lire une vue dérivée au lieu de la
source.**

**③ CHANGER LA DATE NE RÉACTIVE PAS.** Frédéric l'a passée à **22-06-2029** : après
rechargement complet, la date est bien enregistrée **et les deux cadenas sont toujours là**.
➡ Le chemin `desarchiveCritere` *(vu dans le code)* **ne s'est pas déclenché**.

**④ ⭐⭐ MAIS LE GESTE EXISTE — DANS LE MENU « ⋮ » DE LA RECHERCHE :**

```
Modifier la recherche
Mandat de recherche
DÉSARCHIVER LA RECHERCHE      <-- il est là
Supprimer la recherche
```

➡ **Deux conclusions d'un coup** : la recherche **EST** bien archivée *(sinon le menu dirait
« Archiver »)* — ce qui **confirme l'API et le cadenas** — et **elle se désarchive en un clic**.
➡ **Donc « il faut en recréer une autre » est FAUX dans le Hektor d'aujourd'hui.** *(Ce qui
reste vrai : **notre app** ne sait pas le faire — elle ne connaît que « poser une date ».)*

### 🔎 AUDIT DU BOUTON « SUPPRIMER UNE RECHERCHE » — *demandé le 16/10*

| maillon | ce qu'il fait vraiment |
|---|---|
| **l'écran** | l'icône dit **« Supprimer »**, mais sa confirmation dit **la vérité** : *« **Archiver** cette recherche dans Hektor ? Elle disparaîtra des recherches actives. »* → le message est juste, **le libellé ment** |
| **la base** | `app_console_create_delete_contact_search_job` écrit `archive=true, is_active=false` **dans la même transaction**, garde une **photo d'avant** et pose un verrou |
| **le worker** | `archiveHektorContactSearch` → `modifDateArchiveCritere` + **la date du jour** → rend `status: archived` |

**⭐ LA QUESTION A DÉJÀ ÉTÉ POSÉE ET TRANCHÉE** — commit **`f48d55a`** *(31/08)* :
> *« SUPPRIMER UNE RECHERCHE ÉTAIT DÉJÀ FAIT depuis le 30/08 … ⚠ **Et ce n'est pas une
> suppression mais un ARCHIVAGE** »* · *« LES DEUX VRAIES SUPPRESSIONS SONT CLASSÉES SANS
> OBJET, **sur décision de Frédéric, à revoir APRÈS la coupure des workers** »* — motif :
> **une suppression est IRRÉVERSIBLE**, et « écrire d'abord » ne protège rien quand il n'y a
> rien à sauvegarder.

**⚠⚠ ET UNE CROYANCE DU PROJET EST FAUSSE.** Deux documents disent *« **Hektor ne sait pas
supprimer une recherche**, il pose une date »* *(liste l. 686-687 ; audit du 21/09)*.
**C'est faux** : le menu « ⋮ » d'une recherche porte **« Supprimer la recherche »**, et le mode
`contacts-contactProfile-recherche-deleteContactRecherche` existe dans son code *(capture de
juin **et** fichier relevé le 15/10)*. ➡ **Hektor sait supprimer ; c'est NOTRE app qui ne
l'utilise nulle part** *(0 occurrence dans tout le dépôt)*. La décision reste bonne, mais elle
doit se dire autrement : **« on a choisi de ne pas »**, et non « on ne peut pas ».

**⭐ ET L'INTUITION RGPD EST JUSTE** : Hektor pose une **date d'auto-archivage à
« création + 2 ans »** — mesuré deux fois *(créée 22-06-2026 → 22-06-2028 ; 05-06-2026 →
05-06-2028)*. L'archivage d'une recherche est donc **d'abord un mécanisme de durée de
conservation**, pas un geste de suppression déguisé.

### 🔎 CE QUI EXISTE DÉJÀ SUR LES RECHERCHES, ET CE QUI MANQUE — *audit du 16/10*

| | état réel, mesuré |
|---|---|
| **archiver une recherche** | ✅ **fait, et bien fait** — écrit **chez nous dans la même transaction**, garde l'**état d'avant** *(`app_search_pending.base_snapshot`)*, pose un **verrou au numéro du travail** *(effacé au succès, réarmé à l'échec)*. C'est le bouton **« Supprimer »**, mal nommé |
| **désarchiver une recherche** | ❌ **n'existe NULLE PART chez nous.** Des **5** fonctions qui écrivent `app_contact_search_current`, **aucune** ne remet `archive=false`/`is_active=true` ; les **3** types de travail « recherche » sont *add / update / delete* ; et le mode `archiveUnarchiveContactRecherche` **n'apparaît nulle part dans le dépôt** |
| **l'auto-archivage à 2 ans** | ❌ **on ne le voit même pas.** L'API ne rend que `offre, archive, types, villes, quartiers, particularites, criteres` — **aucune date** ; notre table *(23 colonnes)* n'en a pas non plus. La date n'existe que dans **la page HTML** de Hektor *(`valueInputAutoarchivage` — chez Gladys : **22-06-2028**, soit création + 2 ans)*. ➡ **on ne peut ni l'anticiper ni l'afficher**, on constate le basculement **après coup** |
| **désigner UNE recherche** | ⚠ cassé — mais ⭐ **le correctif est déjà écrit** *(note du 31/08)* : *« le HTML porte pourtant l'identifiant, proprement : un attribut **`data-search-id`**, une balise par recherche, dans l'ordre »*. **Il n'est toujours pas lu** : `console_job_worker.js:17757` ratêble encore `dropDownMenu_|contentDrop_|valueInputAutoarchivage|rel=` |

➡ **Donc ce qui manque vraiment, et Frédéric l'a dit avant moi** : non pas « un geste
archiver/désarchiver » à inventer, mais **les deux AUTOMATISMES** — *« soit lors de
l'archivage du contact, soit au bout de 2 ans »* :

| | ce qu'il faut |
|---|---|
| **A** | archiver un contact ⇒ **archiver ses recherches actives CHEZ NOUS d'abord**, même patron que ci-dessus *(état d'avant + verrou)* — ⭐ **et ici aucun problème d'identification** : on prend **toutes** ses recherches actives, aucun index à deviner |
| **B** | **désarchiver une recherche** : geste neuf *(mode connu depuis juin + `data-search-id` à lire)* |
| **C** | *(optionnel)* **capter la date d'auto-archivage** pour la montrer et l'anticiper — elle n'est que dans le HTML |

### ✅ TRANCHÉ PAR FRÉDÉRIC — *16/10*

| | sa décision |
|---|---|
| **A** — archiver un contact archive ses recherches **chez nous d'abord** | ✅ **OUI** — *« on garde la corbeille, cela me va »* → patch écrit *(`patch_chantier7_archiver_contact_recherches_2026-10-16.sql`)* |
| **B** — un geste « désarchiver une recherche » dans l'app | ❌ **NON, inutile** — ➡ et donc `data-search-id` n'est pas urgent non plus |
| **C** — capter la date d'auto-archivage | ❌ **NON ici** — à développer comme **un auto-archivage conforme RGPD**, et *« c'est un autre dev »* |

### ✅ A EST EN PRODUCTION — *16/10, répétition 9/9 puis contrôle 7/7*

**La répétition a servi à quelque chose** : au premier passage elle a rendu
`3-retour | empreinte DIFFERENTE` — mon patch insérait **une ligne vide** entre l'ancre
et la borne, que l'inverse ne reprenait pas. Le bloc partait bien *(0 trace)*, mais le
corps ne retombait pas à l'octet près. **Un seul saut de ligne.** Corrigé → second
passage **IDENTIQUE**. *(Même famille que la leçon 31 : un retour arrière ne juge que
sa part — ici c'était lui le fautif, pas le patch.)*

| contrôle en base | |
|---|---|
| le bloc est posé | ✅ |
| le verrou `app_search_pending` | ✅ |
| le garde `if p_archive then` *(archivage seulement)* | ✅ |
| **0 retour chariot** dans le corps | ✅ *(le `replace(chr(13))` autour du texte inséré a tenu)* |
| `authenticated` / `anon` | ✅ **oui / non** |
| « supprimer un contact » reste fermé au négociateur | ✅ |

**Empreinte après, pour tout futur patch** : **`d089fbf1bb0922030c3fe87ad8dd4371`**
*(l'inverse, lui, vise toujours `85e3c91d…`, l'état d'avant — c'est correct)*.

⏰ **La preuve en réel viendra au prochain archivage** : ses recherches actives doivent
passer inactives **tout de suite** chez nous, et `app_search_pending` porter l'état
d'avant + le numéro du travail.

### ➡ CE QUE ÇA CHANGE POUR LE GESTE — **à trancher par Frédéric**

« Archiver un contact » n'est **pas** un geste anodin : il peut emporter une recherche
active, et avec elle l'éligibilité de la fiche. Trois sorties :

| | |
|---|---|
| **A** | **refuser** l'archivage quand le contact a une **recherche active** *(message clair : « ce contact a une recherche active, archiver la fermerait »)* |
| **B** | **avertir** dans la confirmation — nommer ce qui va être emporté, et laisser décider |
| **C** | refuser seulement quand l'archivage ferait **perdre la dernière raison d'éligibilité** *(ni annonce active, ni transaction)* — le plus précis, le plus de code |

**Rien n'est décidé. Le geste reste ouvert tel quel en attendant.**

#### ⑥ LA CHAÎNE DES CONTACTS, de Hektor à l'app — *question de Frédéric, 15/10 : « as-tu bien compris ? »*

> ⚠ **Et une correction de moi** : j'avais écrit « l'éligibilité tient à DEUX règles ».
> **Il y en a TROIS.** La troisième a été ajoutée le **11/09** justement parce que les deux
> premières laissaient des trous *(`phase2/contacts/elargir_perimetre_console.py`)*.

```
Hektor (API)  ->  data/hektor.sqlite        356 515 contacts   (184 128 archives)
                  phase2.sqlite             356 515 lignes, dont 62 170 ELIGIBLES
                  push (scope « eligible ») ->  Supabase : 62 234 fiches
```

**Les TROIS règles d'éligibilité** *(mesurées des deux côtés, local et cloud)* :

| règle | ce qu'elle dit | local | cloud |
|---|---|---|---|
| `active_annonce_relation` | lié à une annonce **ACTIVE** | 55 349 | 55 379 |
| `active_search` | a une **recherche active** | 3 787 | 3 821 |
| `console_transaction_party` | **nommé dans une transaction** lue par la console *(ajoutée le 11/09)* | 2 786 | 2 786 |
| les deux premières | | 248 | 248 |

*(Écart de 64 entre local et cloud : les fiches rafraîchies ou créées depuis le run de 05:00
écrivent directement dans Supabase. Explication probable, **non prouvée**.)*

**Pourquoi la 3ᵉ règle existe** *(son en-tête le dit)* : les deux premières ne gardaient que
l'**actif**, donc elles laissaient dehors les parties d'une transaction **déjà faite** — **1 191
mandants, 465 acquéreurs** — et **les notaires** *(137 sur 143 : ils n'entrent dans **aucune**
relation, l'API ne les rend jamais)*. ⚠ Sa **place dans le run** est délibérée *(déplacée le
12/09)* : **après** la construction de la couche *(qui remet l'éligibilité à zéro)*, **après**
l'entretien qui remplit sa source, **avant** le push qui lit son résultat.

**⚠ CE QUE LA RÈGLE N'EST PAS** *(l'intuition de Frédéric, corrigée sur un point)* : le cloud
**n'est pas** construit depuis **notre registre des relations** `app_relation`, mais depuis les
**liens de Hektor sur une annonce ACTIVE**. Mesure :

| | |
|---|---|
| `app_relation` *(notre registre)* | **132 757 lignes**, **96 164 contacts** distincts |
| ces contacts présents au cloud | **45 202** |
| ces contacts **absents** du cloud | **50 962** |
| ⭐ dont sur un bien **vivant** | **0** |
| sur un bien **non vivant** *(vendu, clos, archivé)* | 50 961 *(+1 relation sans dossier)* |
| contacts nommés par le registre sur un bien vivant | **20 991**, **0 absent du cloud** |

➡ **Aucun trou sur les biens vivants.** Les 50 962 absents sont les relations que notre
registre **garde pour toujours** *(delete-never)* sur des biens qui ne sont plus actifs —
exactement ce que la règle écarte, et ce que la 3ᵉ règle rattrape quand une **transaction**
les nomme.
➡ **`archive` n'est PAS un critère** : archiver une fiche ne la fait **jamais** sortir du
cloud. Seule la perte des trois raisons l'en fait sortir.

**➡ Et ça répond à une question ouverte de `CLAUDE.md` §2** *(« pourquoi 62 000 contacts
seulement au cloud sur 356 000 ? »)* : **par décision, pas par accident** — on ne monte que
ce qui sert *(16,5 % au 11/09, 17,5 % aujourd'hui)*.

---

## ⑦-2 · LE CAS GLADYS DURIEUX — *à régler en même temps* **(décision de Frédéric, 14/10)**

**Mesuré le 14/10** — c'est la **dernière** incohérence « fiche archivée + recherche active »
sur **64 054** fiches archivées.

| | |
|---|---|
| contact | **Gladys DURIEUX** · `10059959` · Groupe GTI Saint-Étienne · `accueil@gti-immobilier.fr` |
| sa **fiche** | **archivée**, mise à jour le **23/06/2026** |
| **mandante** de | **40608** — *« Villa d'architecte lumineuse avec piscine — 166 m² — Saint-Romain-Lachalm »* · **annonce ACTIVE** |
| **propriétaire** de | **58916** · annonce **active** |
| ses recherches | n° 0 archivée *(prix max 222 222)* · n° **1 ACTIVE** *(prix max **123 456**, « Saint-Étienne » saisi deux fois)* |

> ⚠ **Une cliente avec un mandat en cours a sa fiche contact archivée.**
> **Ce n'est pas un défaut technique : c'est une erreur de saisie métier.**

**Ce qui l'a protégée** : elle est éligible pour **deux** raisons —
`["active_annonce_relation", "active_search"]`. Sans son annonce active, elle serait tombée comme
les 35 autres *(voir `AUDIT_RECHERCHES_ORPHELINES_2026-10-14.md`)*.

⚠ **Et aujourd'hui, on ne peut pas la désarchiver depuis l'app** — il faut ouvrir Hektor. **C'est
exactement pourquoi ⑦-1 et ⑦-2 vont ensemble.**

*(Les prix 222 222 et 123 456 et les villes saisies deux fois ressemblent à un essai laissé sur
une vraie fiche. À confirmer avec l'agence.)*

---

## ⑦-5 · ✅ FAIT LE 15/10 — *« l'alerte est à un endroit, le bouton à un autre »*

*Frédéric : « mais dans le monitoring je n'ai pas de bouton pour relancer ou annuler ? »,
puis « FAIS LES 2 ».* **Deux trous, fermés ensemble.**

### B · Un travail que plus rien ne rejouera devient VISIBLE

**Le défaut** : l'écran Santé disait *« Travaux console en erreur : 3 »*, et Frédéric ne pouvait
en trancher que **deux**. Le bandeau exige **5 tentatives** — or le filet de rejeu
*(patch c4bis du 30/08)* ne rejoue que **9 types idempotents**, et `sync_console_documents` n'y
est pas, **délibérément** : *« sans vérification absolue, le rejeu transforme un succès en échec,
ou double une création »*.
➡ **Un travail non rejouable qui échoue était invisible ET éternel.**

**Le remède** *(`supabase/patch_bandeau_erreurs_definitives_2026-10-15.sql` + INVERSE)* :
la règle devient **« 5 tentatives épuisées OU plus de 3 heures »**. On ne touche **ni** au filet,
**ni** à la liste des types rejouables — on élargit seulement ce que le bandeau **montre**.

⚠ **Les 3 heures sont mesurées, pas choisies** : le filet attend 5, 10, 15 puis 20 minutes, soit
**50 minutes** pour épuiser les 5 tentatives. Passé 3 h *(marge ×3,6)*, un travail qui n'y est pas
ne le sera **jamais**.
⚠ **Ma première version disait 24 h** *(la constante du filet)*. **L'épreuve a montré qu'elle ne
changeait rien aujourd'hui** — le travail 47824 a 12 h. **J'aurais fait attendre jusqu'à 19:00
pour rien.**

**Éprouvé en lecture seule, sur la vraie base** : `47824` *(1 tentative, 12 h)* → **apparaît** ;
`62963` et `61672` *(5 tentatives)* → **inchangés**. **Exactement +1 ligne.**

### A · Les biens cités par une alerte deviennent CLIQUABLES

**Le défaut** : l'alerte nomme les biens *(« annonce 61672 | annonce 62963 »)*, mais il fallait
aller les chercher à la main pour trouver le bandeau qui porte les boutons.

**Le remède, entièrement côté front — rien en base** : les sondes joignent déjà un **aperçu** à
leur résultat *(le `sample` ajouté le 01/09, après la question de Frédéric « comment je le
retrouve ? »)*, et `details_json` **était déjà chargé** par l'écran. Un clic sur le bien ouvre sa
fiche, donc son bandeau.

⚠ **Le pont se fait au clic**, pas au chargement : la sonde rend un **numéro Hektor**, l'écran
ouvre par `app_dossier_id`. On n'interroge la base que pour la ligne sur laquelle on clique.
⚠ **La prop est facultative** : sans elle, l'écran se comporte exactement comme avant.

`npm run build` **vert**. ⬜ **À pousser par Frédéric** *(front → Vercel se déploie)*, et le patch
SQL **à coller**.

---

## ⑦-6 · ✅ FAIT LE 15/10 — *« ABANDONNER » DÉFAIT, au lieu de seulement faire taire*

*Frédéric : « comment dire a mon apps d'annuler le worker et annuler le changement dans
l'apps c'est a dire remettre le montant comme hektor », puis « oui fais A ».*

**Détail complet : `notice/ABANDON_DEFAIT_LE_GESTE_2026-10-15.md`.** En trois points :

**Le défaut** — depuis le chantier ③ l'app écrit *chez nous d'abord*, et les **deux** boutons
du bandeau faisaient la même chose : un `INSERT` dans `app_pending_resolution`, qui ne sert
qu'à **faire taire l'alerte**. La valeur écrite par l'app **restait en place pour toujours**
alors que Hektor n'avait jamais reçu le geste.

**Le remède** — « Abandonner » veut dire *« ce geste n'a pas eu lieu »* : la fiche reprend
l'état d'avant *(déjà posé dans la charge du travail par les RPC optimistes — « pour que le
worker sache quoi restaurer »)*, et **la ligne de carnet est EFFACÉE**, ce qui rend la parole
à Hektor *(contrat d'autorité : « l'app n'a rien → ON NE TOUCHE À RIEN »)*. « J'ai refait »
n'est pas touché.

⭐ **Le garde-fou est un IDENTIFIANT, pas une approximation** : la RPC écrit le carnet et crée
le travail dans la **même transaction**, donc `ecrit_le = requested_at` **à la microseconde**
*(mesure : un seul couple à 0,000 s sur 21 ; les autres à 44 s, 124 s, 8 006 s, 473 236 s)*.
⚠ **Et il n'est pas décoratif** : sur **61672** et **62963**, la ligne de carnet a été écrite
par un geste **plus récent** *(+2 h 14 et +2 min)* — sans lui, abandonner effaçait du vrai.
⚠⚠ **Les 4 gestes d'affaire sont hors de portée, exprès** : le worker les restaure **déjà**
*(`restaurerEtatAffaire`)*, au moment même où le filet de rejeu s'arrête. Un second retour
arrière serait un **double** retour arrière.

**11 contrôles verts sur la vraie base en transaction annulée, dont un TÉMOIN INVERSE** qui
montre l'ancien code laisser la fiche fausse, le carnet plein **et l'alerte éteinte**.

⚠⚠ **ET UN SECOND DÉFAUT TROUVÉ EN CHEMIN** : la vue corrigée hier *(⑦-5 B)* montre les
travaux de plus de 3 heures, **mais `app_action_status` et `app_action_resolve` sont restées
à `>= 5` tentatives**. Donc **47824** sonnait, était visible, et **n'avait aucun bouton** — le
clic était refusé **en silence** (`resolved: false`, que le front jetait).

✅ **ALIGNÉ LE 15/10** *(Frédéric : « OUI ALIGNE LES 2 »)* —
`patch_aligner_seuil_trancher_2026-10-15.sql` + INVERSE.
⚠ **Le prix, dit** : un travail de 4 h à 2 tentatives devient tranchable alors que le filet
pourrait encore le reprendre *(fenêtre 24 h)*. ⭐ Mais le filet ne couvre que **9 types
idempotents**, et les 2 travaux du jour n'en sont pas — **rien à rejouer, rien à perdre**.

⚠⚠ **ET UN TROISIÈME MUR, que seule la mesure a trouvé** : aligner les seuils **n'aurait pas
suffi**. `app_action_status` lève `dossier_not_found` si le bien n'est pas dans
`app_dossier_current` — et **47824 est VENDU** *(« Maison de village à rénover », VM8012)*,
donc dans l'index des vendus/clos depuis le 20/05. **Le front avalait l'erreur et le bandeau
ne s'affichait JAMAIS.** ⭐ Même supposition fausse que le défaut **5a du 08/10**, fausse pour
**44 259 biens** : balayée ici **dans sa dernière case**. Les **archives** sont incluses
exprès — trancher une alerte ne modifie pas le bien.

**11 contrôles avant/après sur les vrais travaux**, dont `ERREUR dossier_not_found` →
`abandonnes=1`, et **61439 (1 h 30) reste `rien_a_trancher`** — la règle des 3 h n'ouvre pas
tout. **Les deux retours arrière retombent à l'octet près.**

### Où sont les boutons *(question de Frédéric)*

**Pas dans l'écran Santé** : sur **la fiche du bien** — cockpit onglet **« Le Bien »**
*(masqué si la fiche est en lecture seule)*, et **au-dessus de la barre d'onglets** de la
fiche classique *(toujours)*. Chemin court : **Santé → cliquer le bien cité par l'alerte**
*(le lien de ⑦-5 A)*.

---

## ⑦-3 · CE QUI VIENT DU CHANTIER ③ *(décisions de Frédéric, 13 et 14/10)*

| | |
|---|---|
| **le crayon** de la date de clôture dans la **rubrique Mandat** | `setMandatClotureApp` n'a **qu'un seul appelant**, la modale de statut. Le crayon hors modale demande une vérification à l'œil. |
| **l'écran du journal des suppressions** | réservé aux admins ; **aucun écran ne le lit** aujourd'hui. |
| **réordonner / choisir la photo principale** | ⭐ `mode=ordonne_photos` est **désormais connu** *(relevé du 14/10)* — le plus dur est fait. |

---

## ⑦-4 · UN BANDEAU QUI MENT

L'index léger promet encore **« désarchiver »** à un bien **qui n'est pas archivé**.
*(Repéré pendant le chantier ③, 12/10.)*

---

## La règle qui vaut pour tout ce chantier

⚠ **Avant d'écrire un geste, trouver la commande Hektor par un RELEVÉ EN LECTURE SEULE.**
Le projet s'est fait avoir deux fois *(suppression de photo, archivage de recherche)*, et la
méthode du relevé a fonctionné les deux fois.

---

# ⑦-3a — CLÔTURER UN MANDAT À LA MAIN — AUDIT DU 16/10/2026

> Demande de Frédéric, 16/10 : *« audit la clôture d'un mandat se fait actuellement
> uniquement par le worker annulation de mandat suite à l'acceptation d'une demande par
> Pauline. On peut ajouter la possibilité de clôturer manuellement un mandat mais il faut
> auditer toutes les entrées — cockpit rubrique mandat, aussi dans l'annonce, il y a aussi
> notre registre des mandats (je crois qu'il n'y a pas de colonne, à vérifier où se
> sauvegardent les dates), mais il y a la vue registre des mandats et la fiche mandats —
> analyse tous les points, puisque ce bouton doit être accessible uniquement par les
> admin / manager, sinon visible mais lié à la demande d'annulation de mandat existante.
> Rendre ces dates modifiables. Mais À VÉRIFIER AUSSI : il n'est pas nécessaire de
> communiquer avec Hektor sur les dates de clôture de mandats, je crois que nous l'avions
> déjà décidé, à vérifier. »*

**Périmètre de cet audit : le MANDAT, geste « clôturer » et geste « modifier la date de
clôture ».** Les autres objets ne sont pas mesurés ici.

## 1. SA PREMIÈRE PHRASE EST VRAIE — ET LE CHEMIN N'A JAMAIS SERVI

L'acceptation d'une demande d'annulation **enchaîne bien** une clôture
*(`App.tsx:17204-17221`, commentaire « A5 »)* : elle crée un travail
`change_hektor_annonce_status` avec `targetStatus: 'closed'`, que le worker traite.
Commit `fd8a042`, **30/07/2026**.

⚠ **Mais il n'est pas le seul, et il n'a jamais tourné.** Mesures :

| ce qui a été mesuré | résultat |
|---|---|
| demandes d'annulation de mandat, tous états | **4**, toutes `accepted` |
| quand | **13 et 14 mai 2026**, toutes sur **la même annonce 24113**, toutes traitées par Frédéric |
| le chaînage A5 qui les aurait closes | arrivé le **30/07**, soit **2 mois et demi APRÈS** |
| les 4 ont-elles une date de clôture à nous ? | **0 sur 4** |
| travaux ayant journalisé une clôture locale | **25**, tous de type `change_hektor_annonce_status` |
| sur combien de biens ? | **4 : 62966, 62774, 24933, 62963** |
| et ces 4 biens sont… | ⭐ **les 4 biens d'ESSAI du projet** *(liste de la mémoire de reprise)* |
| l'annonce 24113 apparaît-elle dans ces 25 lignes ? | **non, jamais** |

➡ **Le chemin « demande acceptée → clôture » existe dans le code depuis le 30/07 et n'a
jamais été emprunté une seule fois.** Et **aucun mandat réel n'a jamais été clos par
l'app** — conclusion identique à celle du 13/10 *(§ ①-ter de `CLAUDE.md`)*, re-mesurée ici
par un autre chemin.

## 2. LES DEUX CHEMINS QUI CLÔTURENT, AUJOURD'HUI

Les deux passent par **la modale de changement de statut** et par le worker :

| | ce qui déclenche | où |
|---|---|---|
| **a** | l'annonce passe au statut **« Mandat clos »** | `submitHektorClosedStatus` → `cloturerMandatLocalement` *(`console_job_worker.js:13795`)* |
| **b** | l'annonce passe à **« Vendu »** | `target === "sold"` → `cloturerMandatLocalement` *(l. 15209)* |

Et **a** est atteint de deux façons : à la main dans la modale *(`App.tsx:16942`)*, ou par
le chaînage A5 ci-dessus. **Il n'y a pas d'autre écriture de clôture dans le projet.**

## 3. OÙ SE SAUVEGARDENT LES DATES — TROIS ENDROITS, UN SEUL FAIT FOI

| objet | lignes | clôtures | rôle |
|---|---|---|---|
| **`app_mandat_champ_app`** *(le carnet)* | — | **3** *(origine `cloture_app`)* | ⭐ **CE QUI FAIT FOI**. 1 sans auteur, 1 par Frédéric, 1 par GONZALEZ |
| **`app_mandat_register_current.mandat_date_cloture_app`** *(la vitrine)* | 24 564 | **3** | confort d'affichage, **sans autorité** |
| **`app_mandat_register_current.mandat_date_cloture`** | 24 564 | **213** | ⚠ **la colonne de HEKTOR** — l'app ne l'écrit plus depuis le 13/10 |
| **`app_mandat.date_cloture`** | 26 912 | **91** | ⛔ **aucun écran ne la lit** |
| **vue `app_registre_mandats_current`** | *(vue)* | — | expose les trois : `mandat_date_cloture` *(la nôtre d'abord)*, `_app`, `_hektor` |

⚠⚠ **Et la vitrine est détruite chaque nuit** pour les annonces du parc vivant
*(`delete`+`insert` du registre)* : c'est pourquoi la **pièce 4 du chantier ③** repose la
date après le push *(RPC `app_reposer_cloture_mandat_app`, prouvée le 14/10)*. **Le carnet,
lui, survit** — c'est la seule raison pour laquelle les 3 dates sont encore là.

## 4. LES ENTRÉES À L'ÉCRAN — IL A RAISON : LE REGISTRE N'A PAS DE COLONNE

| entrée | ce qu'elle lit | notre date s'y voit-elle ? |
|---|---|---|
| **cockpit, parcours / pastille / jauge** | `ckClotureDe()` → la résultante de la vue *(`App.tsx:27139-27146`, `27223`, `28662`)* | ✅ **oui** |
| **cockpit, historique des mandats V3** | `firstNonEmpty(ckClotureDe(num), cur.cloture)` *(l. 27967)* | ✅ **oui** |
| **fiche annonce classique, rubrique Mandat** | `current.cloture` *(données Hektor)* puis `detail.mandat_date_cloture` *(colonne Hektor)* — `mandatDetails`, `App.tsx:18513` et `18530`, passé à **3 écrans** | ❌ **non** — la ligne est même **masquée si vide** |
| **écran Registre, le tableau** | 2 colonnes de date : **début** et **fin** *(l. 24312-24313)* | ❌ **aucune colonne clôture** |
| **écran Registre, la fiche mandat** | `selectedMandateLines` — **9 lignes** : Numéro, Type, Début, Fin, Montant, Validation, Diffusable, Commercial, Agence *(l. 24142-24153)* | ❌ **aucune ligne « Clôture »** |

⭐ **MAIS LE REGISTRE N'EST PAS AVEUGLE** : sa colonne **« Mandat »** est calculée par
`mandatStatutForRegister` *(l. 7671)*, qui met **« Clos »** dès qu'une date de clôture
existe — et elle lit la **résultante**, donc **la nôtre**. Poser une date fait donc
**basculer la pastille** et **déplace la ligne dans le filtre par statut**
*(`applyMandatStatutFilter`, `api.ts:95`)*, sans que la date soit écrite nulle part à
l'écran. **La conséquence est déjà visible ; seule la valeur est invisible.**

## 5. LES DROITS — LE TROU EST RÉEL

`app_set_mandat_cloture_optimistic(target_annonce, target_numero_mandat, cloture_date)` :

| | |
|---|---|
| `security definer` | **oui** |
| droits | `authenticated` ⚠ **tout utilisateur connecté** |
| garde interne | ⛔ **AUCUNE** — l'étape ① ne demande que *« es-tu authentifié ? »* |
| appelants | **un seul** : `App.tsx:16942`, la modale de statut, quand `statusChangeStatus === 'closed'` |

➡ **La fonction est ouverte à la clé publique** : quelqu'un de connecté peut l'appeler
**directement**, sans passer par l'écran, et écrire une date sur n'importe lequel des
24 564 mandats — exactement la famille du **chantier ①**.

⭐⭐ **MAIS LE GESTE LUI-MÊME EST DÉJÀ RÉSERVÉ — correction du 16/10, j'avais dit faux.**
`app_console_can_request_job` réserve `change_hektor_annonce_status` **et**
`archive_hektor_annonce` à `admin`/`manager` : c'est sa **toute première règle**, posée au
**chantier ②**, et `app_change_annonce_status_optimistic` **appelle bien cette garde**.
Épreuve du 16/10, en empruntant les identités, en lecture seule :

| qui | son rôle | `can_request_job('change_hektor_annonce_status')` |
|---|---|---|
| legrand | `commercial` | ⛔ **false** |
| codex.test | `admin` | ✅ **true** |

Les **deux** chemins de clôture *(« Mandat clos » et « Vendu »)* passent par ce même type de
travail. ➡ **Un négociateur ne peut donc pas clôturer un mandat.** Ce que Frédéric demande
est **déjà vrai pour le geste** ; la pièce 2 ne ferme que **la porte de derrière**.

⭐ **ET LE DROIT DEMANDÉ EXISTE DÉJÀ** : `is_app_manager_or_admin()` est en base
*(chantier ②, « manager = admin »)*, et le front porte déjà `isManagerOrAdmin`
*(`App.tsx:18012`)*, déjà utilisé pour l'archivage d'annonce *(l. 22580)*. **Rien à inventer.**

## 6. « PAS BESOIN DE COMMUNIQUER À HEKTOR » — DÉCISION ÉCRITE, RETROUVÉE

> *« la date de clôture doit donc être une colonne supplémentaire, et cette colonne doit
> être maj éventuellement par Hektor mais **surtout pas l'app** — mais cette demande n'a
> pas à être transmise à Hektor. »*
> **Frédéric, 13/10** *(`CHANTIER_3_HEKTOR_DABORD_2026-10-12.md`, l. 1873-1875)*

Et la raison technique, du **28/08** *(même note, l. 1253-1258)* : le formulaire de clôture
de Hektor **exige un numéro de mandat** et **échouait sur 98,8 % du parc** — il a été
débranché, et un geste qui marchait *(le changement de statut)* était pris en otage.

**État mesuré du code** : `CLOTURE_MANDAT_CHEZ_HEKTOR` *(`console_job_worker.js:13533-13534)`*
vaut `false` par défaut, et **aucun fichier du dépôt ne pose `CONSOLE_HEKTOR_CLOTURE_MANDAT`**.
La porte reste ouverte, elle n'est pas franchie. Le texte de l'écran a d'ailleurs été
corrigé le 13/10 : **« motif et date gardés chez nous »** *(`App.tsx:20068`)*.

➡ **Sa mémoire est juste, c'est écrit deux fois, et le code le respecte. Rien à changer sur
ce point.**

## 7. CE QUE L'AUDIT N'A PAS PU MESURER

- **Aucune capture d'écran** : je ne peux pas voir l'écran Registre ni la fiche mandat avec
  une session. Les absences du § 4 sont lues **dans le code**, pas constatées à l'œil.
- **Pourquoi les 4 demandes d'annulation de mai portent toutes la même annonce 24113** : pas
  mesuré *(probablement des essais de Frédéric, mais je ne le prouve pas)*.
- `app_mandat.date_cloture` **91 lignes** : je n'ai pas cherché **qui** les a écrites.
- ⚠ **Une autre session travaille le registre aujourd'hui** *(les mandats de recherche,
  `App.tsx:9219-9236`)* : tout code sur l'écran Registre devra relire `git log` d'abord.

## 8. LES DÉCISIONS DE FRÉDÉRIC — 16/10/2026

> *« 1. dans l'ordre recommandé · 2. NON LA CLÔTURE PAS LES DATES D'ORIGINE DU MANDAT !! ·
> 3. Une colonne en + »*

| | décision | ce que ça ferme |
|---|---|---|
| **ordre** | **pièce 1** *(la bonne date gagne)*, **pièce 2** *(les droits)*, puis **3** *(la date visible)* et **4** *(le bouton)* | le périmètre et la taille sont tranchés |
| **quelles dates** | ⛔ **LA CLÔTURE SEULE.** Les dates **d'origine** du mandat *(enregistrement, début, fin)* **restent en lecture** — elles viennent de Hektor et n'auront pas de colonne « à nous » | ⚠ **ne pas relancer ce sujet de soi-même** |
| **le registre** | ✅ **une colonne clôture EN PLUS** dans le tableau | ⚠ **à concilier avec la doctrine « aucune colonne ajoutée » écrite le 16/10 par l'autre session** *(mandats de recherche)* : relire `git log` avant d'écrire la pièce 3 |

### ⭐ PIÈCE 1 — LE REMÈDE ÉTAIT DÉJÀ À MOITIÉ POSÉ

`cloturerMandatLocalement` lit `payload.close_date || payload.date_cloture ||
payload.transaction_date` *(`console_job_worker.js:13674`)* — **`close_date` est son PREMIER
choix, et personne ne l'envoie jamais** *(0 occurrence de `closeDate`/`close_date` dans
`api.ts`)*. Donc il retombe sur `transaction_date`, c'est-à-dire **l'autre champ date de la
modale**, qui vaut **aujourd'hui** par défaut.

➡ **Deux lignes dans le front suffisent** : `closeDate` dans l'entrée de
`createChangeHektorAnnonceStatusJob`, et `close_date: input.closeDate?.trim() || null` dans
la charge *(la charge est construite en snake_case explicite, l. 6078+)*.
⭐ **Aucune modification du worker, aucun redémarrage des 4 services.**

⛔ **ET SURTOUT PAS en détournant `transactionDate`** : il part **aussi chez Hektor**
*(`setHektorAnnonceStatusValue`, `console_job_worker.js:11929`)*, et le chemin `closed_form`
passe par cette même fonction. Le détourner changerait ce que Hektor reçoit.

### PIÈCE 2 — ÉCRITE, DORMANTE, ET ÉPROUVÉE À BLANC

| fichier | ce qu'il fait |
|---|---|
| `supabase/patch_chantier7_3a_piece2_droits_cloture_2026-10-16.sql` | insère une garde `is_app_manager_or_admin()` dans `app_set_mandat_cloture_optimistic`, **sans retirer le `grant`** *(un refus lisible valant mieux qu'une erreur de permission que le front avale)* |
| `..._INVERSE.sql` | retire la garde entre deux bornes, vérifie **0 trace**, puis **dit** si l'empreinte d'origine revient *(lesson du 15/10 : un inverse ne juge que sa part)* |
| `..._REPETITION.sql` | mesures avant *(dont le **témoin inverse** : le négociateur doit être **accepté** avant le patch)* → patch → **les 3 identités** → inverse → retour → erreur volontaire |

**Contrôle à blanc du 16/10, 100 % en lecture, 7 contrôles verts** *(le texte patché est
fabriqué puis repassé par l'inverse, sans jamais être exécuté)* :

```
a  le texte patche grandit de 962 caracteres
b  2 bornes (attendu 2)
c  l appel NOT public.is_app_manager_or_admin() est present
d  les apostrophes sont justes (service_role, droits_insuffisants, le message)
e  zero retour chariot introduit
f  l INVERSE retombe sur l original  -> OUI, A L OCTET PRES
g  empreinte apres l inverse         -> IDENTIQUE (09280b46...)
```

⚠ **Ce que la répétition ne pourra pas prouver** : il n'y a **aucun manager actif**
aujourd'hui *(mesure : 4 admin, 2 commercial, 0 manager)*. La branche « manager » repose sur
`is_app_manager_or_admin()`, déjà en production, qui teste `role in ('admin','manager')`.
**Non éprouvée en réel, et c'est dit.**

⚠⚠ **CORRECTION DU 16/10 — J'AVAIS ÉCRIT FAUX ICI.** J'avais annoncé que la pièce 2
n'empêcherait pas un négociateur de clôturer un mandat. **Mesuré : il ne peut déjà pas.**
`change_hektor_annonce_status` est réservé à `admin`/`manager` depuis le chantier ②
*(détail et épreuve au § 5)*. La pièce 2 ferme **la porte de derrière** — l'appel direct à
la RPC avec la clé publique — et **pas** le geste, qui est déjà fermé.
➡ **Leçon : avant d'annoncer qu'un garde-fou « ne suffira pas », mesurer les garde-fous qui
existent déjà AILLEURS sur le même geste.** Frédéric a tiqué sur la phrase ; elle était
fausse.

## 9. CE QUI EST ÉCRIT — 16/10/2026, pièces 1, 3 et 4

**Go de Frédéric : « Option a »** → pièce 1, puis 3 et 4 ; la pièce 2 reste dormante.
**Aucun redémarrage de worker, aucune écriture en base, rien de poussé.**

### Pièce 1 — la bonne date gagne *(2 endroits, 3 lignes utiles)*

| fichier | ce qui change |
|---|---|
| [`lib/api.ts`](../apps/hektor-v1/src/lib/api.ts) | `closeDate?: string` en entrée de `createChangeHektorAnnonceStatusJob`, et `close_date: input.closeDate?.trim() \|\| null` dans la charge |
| [`App.tsx`](../apps/hektor-v1/src/App.tsx) | `closeDate: statusChangeStatus === 'closed' ? statusChangeCloseDate : undefined` au seul site d'appel de la modale |

⭐ **Le worker lit `close_date` en PREMIER depuis toujours** — il n'a pas été touché, donc
**pas un seul des 4 services n'a besoin de redémarrer**.
⛔ **On n'a PAS détourné `transactionDate`** : il part *aussi* chez Hektor
*(`setHektorAnnonceStatusValue`)*, et le chemin « Mandat clos » passe par cette fonction.
⚪ **Le chemin « Vendu » est laissé tel quel, exprès** : il clôt sur la **date de vente**
*(le worker y passe `transaction_date` en dur)*, ce qui est juste.
⚪ **L'acceptation d'une demande d'annulation n'envoie rien** : elle n'a pas de champ date,
donc la clôture prend **le jour de l'acceptation**. Voulu.

### Pièce 3 — la date devient visible *(3 entrées sur 4 ; le cockpit l'était déjà)*

| entrée | avant | après |
|---|---|---|
| **tableau du Registre** | aucune colonne | ⭐ **colonne « Date de clôture »**, après « Date de fin » *(décision de Frédéric : « une colonne en + »)*. Vide = non clos, **sans tiret** : sur l'écran le plus officiel de l'app, un tiret se lit « donnée manquante » |
| **fiche mandat du Registre** | 9 lignes, aucune clôture | ligne **« Cloture »** après « Fin » *(ici le `-` est juste : toutes les lignes voisines l'emploient)* |
| **rubrique Mandat de la fiche annonce** | lisait `detail.mandat_date_cloture`, **toujours vide** *(la colonne n'existe pas dans la fiche)* | lit **notre date d'abord** via `clotureParMandat`, alimenté par `loadRegisterCycleAffaires` |
| CSS | — | `min-width` du tableau : **1084 → 1180 px** *(la colonne ajoute 96 px fixes ; sans ce report, « Mandant(s) » — en `width:auto` — les aurait perdus)* |

⚠ **Le prix de la 3ᵉ ligne, dit** : c'est une **seconde lecture** du même registre pour la
même annonce quand le cockpit est ouvert à côté. L'alternative — piocher dans l'état
`mandats` de l'écran Registre — a été **écartée** : cette liste est **filtrée et paginée**,
donc une fiche ouverte depuis l'écran Annonces n'y serait pas et on retomberait sur une
ligne vide **sans erreur**. *Une absence est pire qu'une erreur.*

### Pièce 4 — le geste, dans la fiche mandat du Registre

Un bloc **« Clôture du mandat »** sous la jauge du cycle de vie, qui recopie le cadre de son
voisin `.md-lifecycle` *(aucune couleur ni variable nouvelle)* :

| qui | ce qu'il voit |
|---|---|
| **manager / admin** | **« Clôturer ce mandat »** → un champ date → **Enregistrer** ; si déjà clos : **« Corriger la date de clôture »** + **« Rouvrir le mandat »** *(vider la date efface la nôtre et fait réapparaître celle de Hektor — le retour arrière était déjà prévu par la RPC)* |
| **négociateur** *(validation accordée)* | **« Demander l'annulation de ce mandat »** → le circuit qui existe depuis toujours, + la phrase qui explique. ⭐ **On n'a pas fabriqué un second circuit** |
| **négociateur** *(sans validation)* | une phrase : clôturer est réservé aux managers |
| ⚠ **mandat de recherche** | **lecture seule, et on DIT pourquoi** |

⚠⚠ **LE PÉRIMÈTRE EXCLU EST DÉCLARÉ** *(mesure du 16/10)* : les **38 mandats de recherche**
entrés au registre le 16/10 par l'autre session **n'ont ni annonce ni dossier — 0 sur 38**.
Or notre carnet a pour clé le couple **(annonce, n° de mandat)** et la demande d'annulation
exige un `app_dossier_id`. Ni le crayon ni le renvoi ne peuvent les servir : la fiche affiche
la date en lecture et explique, **au lieu d'offrir un bouton qui échouerait en
`mandat_introuvable`**.

⭐ **`messageRefusCloture()`** traduit les codes de la RPC en français — y compris
**`droits_insuffisants`, qui n'existe pas encore en base** : c'est la pièce 2, dormante. Le
message est posé **d'avance**, exprès, pour que le jour du collage l'écran sache déjà quoi
dire.

⭐ **Le dépliant « Tous les champs » lit la MÊME valeur que le bloc** *(`clotureCourante`)* :
juste après une saisie, la liste du registre porte encore l'ancienne date, et les deux
endroits de la même fiche auraient dit deux choses.

### Les épreuves

| | |
|---|---|
| `npm run build` | ✅ **vert** *(`tsc -b && vite build`)* |
| ⭐ **le build vérifie-t-il VRAIMENT les types ?** | **témoin inverse** : un `const x: number = "texte"` posé exprès → `error TS2322` ; retiré, le build repasse au vert. Sans ce témoin, « build vert » ne voulait rien dire |
| témoins dans le fichier SERVI | `close_date` 1 · `Date de clôture` 4 · `Clôturer ce mandat` 1 · `Corriger la date de clôture` 1 · `Rouvrir le mandat` 1 · `Demander l'annulation de ce mandat` 1 · la phrase du mandat de recherche 1 · `md-cloture` **12 fois dans la CSS** |
| l'autre session | `git log` relu **avant** d'écrire : son registre est **commité** *(`8149f44`, 11:37)*, et le diff de mes 2 fichiers de code ne contenait **que mes lignes** |

### ⛔ CE QUI N'EST PAS FAIT, ET QUI DOIT ÊTRE DIT

1. ⚠⚠ **PERSONNE N'A VU L'ÉCRAN.** Je n'ai pas de session pour ouvrir la fiche mandat : tout
   est prouvé par le **build** et par les **textes présents dans le fichier servi**, pas à
   l'œil. La colonne du registre et le bloc de clôture **restent à regarder**.
2. ⛔ **Rien n'est poussé** — et c'est Frédéric qui pousse *(Vercel se déploie seul)*.
3. 🔸 **La pièce 2 reste dormante** : la RPC est toujours ouverte à `authenticated` sans garde
   *(la porte de derrière)*. Le geste, lui, est déjà réservé.
4. ⬜ **L'essai réel** : clôturer un mandat d'essai avec une date **différente du jour**, et
   vérifier que le carnet porte **la date saisie**. ⚠ Se mesure sur **la valeur**, pas sur
   l'heure : le `PATCH` du worker ne rafraîchit pas `ecrit_le` *(24933 porte une valeur du
   18/09 avec un horodatage du 03/09)*.

## 10. POUSSÉ ET VÉRIFIÉ EN LIGNE — 16/10/2026, 12:3x

**Go de Frédéric : « Vas y pousse ».** ⚠ C'est la première fois que je pousse moi-même ;
jusqu'ici c'était toujours lui *(« ce n'est pas moi qui pousse »)*.

### Ce qui est parti — et deux commits sur trois ne sont pas de moi

`a392053 → 9662fd8`, soit **3 commits** :

| commit | heure | de qui | quoi |
|---|---|---|---|
| `8149f44` | 11:37 | **l'autre session** | les mandats de recherche entrent au registre *(10 fichiers, dont `export_app_payload.py` et `mandat_ledger.py`)* |
| `cfedd78` | 12:22 | **moi** | ⑦-3a pièces 1, 3 et 4 |
| `9662fd8` | 12:27 | **l'autre session** | des `title` au survol sur la colonne « Nature » *(12 lignes, `App.tsx` seul)* |

⭐ **Vérifié avant de pousser** : `9662fd8` ne touche **que** les `<span>` de la colonne
« Nature et situation » — **aucun chevauchement avec ma colonne « Date de clôture »**.
⚪ Les fichiers `phase2/` de `8149f44` ne sont **pas déployés** *(Vercel et Render ne servent
que le front et le backend)* : ils attendent le run de nuit.

### La preuve en ligne

Vercel a pris le push tout seul *(`dpl_3ri9Hx…`, commit `9662fd8`, cible production)*, et la
sonde a attendu le **vrai fichier servi** avant de conclure *(leçon du 08/10 : on ne parle
qu'après avoir sondé)* :

```
paquet servi : /assets/index-DaU4SQsX.js  (2 278 495 octets)
  Clôturer ce mandat                      1 fois
  Date de clôture                         4 fois
  close_date                              1 fois
  Rouvrir le mandat                       1 fois
  Demander l'annulation de ce mandat      1 fois
  md-cloture (CSS)                       12 fois  (/assets/index-CnKjrIHw.css)
```

Outil : `scratchpad/sonder_deploye.sh` *(24 essais max, 15 s d'écart ; il a suffi du premier)*.

### ⭐ ET LE DOUTE QUI RESTAIT SUR LA PIÈCE 1 EST LEVÉ

J'avais écrit que `close_date` arriverait au worker **sans l'avoir prouvé** : la charge passe
par une RPC, et une RPC qui reconstruirait l'objet clé par clé aurait **jeté** ma nouvelle
clé en silence — exactement la famille du « nouveau type de travail, trois verrous ».

Mesure dans `app_change_annonce_status_optimistic` :

| ligne | ce qu'elle fait |
|---|---|
| 79 | `v_payload := coalesce(job_payload, '{}'::jsonb)` — **la charge est prise telle quelle** |
| 287-288 | `payload_json` reçoit **`v_payload` en entier** *(seulement fusionné avec `app_affaire_id` s'il y a une affaire)* |
| 268-270 | elle lit déjà `close_etat`, `close_raison`, `close_reason` |

➡ **`close_date` traverse intact jusqu'à `app_console_job.payload_json`**, que le worker lit.
Et ma clé **rejoint une famille qui existait déjà** dans cette charge.

### ⛔ CE QUI RESTE, APRÈS LE PUSH

1. ⚠⚠ **PERSONNE N'A TOUJOURS PAS VU L'ÉCRAN.** Le fichier servi porte les textes — ça ne
   dit pas que le bloc est **beau**, ni que la colonne tient dans la page. **À regarder :**
   écran **Mandats**, ouvrir une fiche, le bloc est **sous la jauge du cycle de vie**.
2. ⬜ **L'ESSAI RÉEL**, et c'est lui qui compte : clôturer un mandat d'essai avec une date
   **différente d'aujourd'hui**, puis vérifier que le carnet porte **la date saisie**.
   ⚠ Se mesure sur **la valeur**, pas sur l'heure : le `PATCH` du worker **ne rafraîchit pas**
   `ecrit_le` *(24933 porte une valeur du 18/09 avec un horodatage du 03/09)*.
3. 🔸 **La pièce 2 reste dormante** *(la porte de derrière : la RPC est encore ouverte à
   `authenticated` sans garde)*. Le **geste**, lui, est déjà réservé depuis le chantier ②.
