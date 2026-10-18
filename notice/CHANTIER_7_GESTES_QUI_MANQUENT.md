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
| ⑦-3b | l’**écran du journal des suppressions** *(4 journaux, 128 lignes)* | ✅ **écrit le 16/10** — dans Santé, admin strict, tout ; témoin inverse 128/0 |
| ⑦-3c | **réordonner / choisir la photo principale** *(`mode=ordonne_photos` connu)* | ⬜ reçu du chantier ③ |
| ⑦-4 | le **bandeau qui ment** | ✅ **traité le 16/10, et le verdict a changé en route** — ⚠ **la production ne mentait pas** *(c’est le cockpit qui s’affiche, et il dit « depuis une fiche d’index léger »)*. Le menteur était l’**ancienne fiche**, le repli du drapeau. ✅ Corrigé quand même *(sa décision : « ça répare le repli et ça ne coûte rien »)*, ⭐ et le **mobile**, lui, mentait VRAIMENT aux **527 brouillons** — c’est la part vivante |
| ⑦-5 | relancer / abandonner depuis le monitoring, biens cliquables | ✅ **fait le 15/10** |
| ⑦-6 | « Abandonner » **défait** le geste | ✅ **fait le 15/10** |
| ⑦-7 | **modifier ou prolonger un mandat** | ⛔ **FERMÉ PAR DÉCISION le 18/10** — Frédéric : « je ne souhaite pas pouvoir modifier un mandat ou prolonger ». **Ne pas relancer.** L'audit reste en bas de note : il a servi à autre chose *(202 biens en vente à mandat échu, et la commande des dates identifiée)* |
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

## 11. L'APRÈS-MIDI : DEUX CORRECTIONS, DONT UNE DE MOI — 16/10/2026

### ⚠⚠ J'AI CASSÉ LA MISE EN PAGE DU REGISTRE, ET C'EST L'ŒIL QUI L'A VU

Frédéric : *« Ouvre, tu as accès Chrome, et donne-moi aussi ton avis »*. J'ai ouvert l'écran
dans son Chrome — et **la première chose mesurée a été un défaut à moi** :

| mesure, dans la page | valeur |
|---|---|
| largeur du conteneur | **1 089 px** |
| largeur du tableau | **1 180 px** *(mon nouveau `min-width`)* |
| **débordement** | **91 px → barre de défilement horizontal** |
| la colonne était remplie sur | **0 ligne sur les 50 affichées** |

Et le commentaire CSS que j'avais remplacé disait, mot pour mot :
*« calées pour tenir dans la page **sans défilement horizontal** »*.
**Je l'ai lu, et je l'ai déplacé quand même** — c'est la leçon 27 de `CLAUDE.md`
*(« un seuil qui porte un raisonnement ne se monte pas pour faire taire »)*, prise en flagrant
délit sur une largeur au lieu d'une alerte.

⭐ **Et la mesure donnait le vrai prix** : sur **24 564 lignes du registre, 215 ont une
clôture — 0,88 %**. Une colonne vide 99 % du temps coûtait **96 px et une barre de
défilement à tout le monde, tous les jours**.

**Option C, choisie par Frédéric.** La colonne est retirée, `min-width` revient à **1 084**,
et la clôture s'affiche **en sous-ligne de « Date de fin »** quand elle existe :
`Clos 14/10/2027`, en petit et en gris. ⭐ **Le patron n'est pas inventé** : c'est celui de la
colonne « Montant » juste à droite, qui porte déjà sa sous-ligne « 1 modif prix · … »
*(`register-price-history`)*. **Zéro pixel ajouté.**

### 2ᵉ CONSIGNE : CLÔTURER PASSE TOUJOURS PAR LA DEMANDE, MÊME EN ADMIN

> *« il faudrait que le clic sur clôturer le mandat passe systématiquement par la demande
> d'annulation de mandat. Même avec un compte admin / manager. »* — Frédéric, 16/10

Le bloc a donc **deux parties, et une seule porte pour clôturer** :

| | qui | ce qu'il voit |
|---|---|---|
| **① clôturer** | **tout le monde**, admin compris | **« Demander l'annulation de ce mandat »** → le circuit qui existe depuis toujours. Pour un manager la phrase dit pourquoi : *« même pour toi : c'est ce qui en garde la trace »* |
| **② corriger** | manager / admin, **et seulement si une date existe déjà** | **« Corriger la date de clôture »** — ce n'est pas clôturer, c'est redresser. C'est le *« rendre ces dates modifiables »* du matin |

⚠⚠ **ET UNE CONDITION N'A PAS ÉTÉ RECOPIÉE, EXPRÈS.** Le menu `MandatActionMenu` exige un
mandat **validé** pour proposer la demande. Mesure du 16/10 :

| état de validation | lignes | dont actifs |
|---|---|---|
| `a_controler` *(non validé)* | **22 759** | 245 |
| `valide` | 1 767 | 502 |
| `(null)` *(mandats de recherche)* | 38 | 0 |

➡ Avec cette condition, **93 % des mandats n'auraient AUCUN bouton**. Et c'est logique :
**la validation concerne la DIFFUSION, la clôture concerne la VIE DU MANDAT.** Divergence
**assumée et déclarée dans le code**, pas un oubli.

### ⛔ CE QUE JE DOIS DIRE, ET QUI N'EST PAS RÉGLÉ

1. ⚠⚠ **« Clôturer » reste atteignable autrement** : la **modale de changement de statut**
   *(annonce → « Mandat clos » ou « Vendu »)* clôt toujours le mandat sans passer par la
   demande. Elle est déjà réservée `admin`/`manager`, mais la consigne « systématiquement par
   la demande » **n'est donc vraie que pour ce bouton-ci**. À trancher par Frédéric.
2. 🔸 **« Rouvrir le mandat » a disparu** avec la réécriture *(il n'était offert que dans
   l'éditeur de clôture)*. La RPC sait toujours effacer une date ; plus aucun écran ne le
   demande. ⭐ Au passage, ça referme le défaut que j'avais signalé : **il effaçait sans
   confirmation**.
3. ⬜ **Le poids visuel du bouton** : il est maintenant en bouton discret *(`ghost-button`)*,
   plus en rose plein. Ce n'était pas demandé explicitement, mais la réécriture l'a fait.
4. ⬜ **Non vérifié à l'œil** : la vue du négociateur *(je suis admin dans cette session)* et
   celle d'un mandat de recherche.

### Les épreuves

`npm run build` **vert**. Témoins **dans les deux sens** sur le fichier construit :
**disparus** — `Clôturer ce mandat` 0, `Rouvrir le mandat` 0, l'en-tête de colonne 0,
« réservé aux managers et aux administrateurs » 0 ;
**présents** — `Demander l'annulation de ce mandat` 1, `Corriger la date de clôture` 1,
« c'est ce qui en garde la trace » 1, `register-cloture` 1 *(et 1 dans la CSS)*,
`min-width:1084px` 1. ⚠ Le `min-width:1180px` qui reste dans la CSS est une **média-query de
`layout-overrides.css`**, touchée pour la dernière fois le **23/06** — rien à voir.

### ✅ POUSSÉ ET REVÉRIFIÉ À L’ŒIL — 16/10, 13:0x

Commit `6217a0d`, déploiement Vercel **READY**, puis mesures **dans la page** :

| ce qui a été mesuré | avant | après |
|---|---|---|
| colonnes du tableau | 9 + actions | **8 + actions** *(« Date de clôture » partie)* |
| largeur du tableau | 1 180 px | **1 089 px** |
| `min-width` de `.register-table` | 1 180 | **1 084** |
| **débordement** | **91 px, défilement horizontal** | **0 px**, `DEFILE: false` |

Et la fiche mandat, **sous le compte admin de Frédéric**, rend exactement sa consigne :

```
CLOTURE DU MANDAT | Non clos | Demander l'annulation de ce mandat |
Cloturer passe toujours par une demande, meme pour toi : c'est ce qui en garde
la trace. | Cette date reste dans nos donnees : Hektor n'en est pas informe.
```

boutons = [« Demander l’annulation de ce mandat »] · champs date = **0**

⭐ **Et le mandat ouvert (18946) est `a_controler`, donc NON VALIDÉ** — le bouton est là
quand même. C’est la **preuve en réel** que ne pas recopier la condition de validation
était la bonne décision : avec elle, cette fiche n’aurait eu **aucun** bouton.

### ⚠⚠ LA SONDE DE DÉPLOIEMENT M’A APPRIS QUELQUE CHOSE

Ma première sonde a répondu **« EN LIGNE » sur l’ANCIEN paquet** : elle ne cherchait que
les textes qui devaient **apparaître**, et ils y étaient déjà.

➡ **Une sonde de déploiement se fait DANS LES DEUX SENS** — ce qui doit être là **et** ce
qui doit avoir **disparu**. Même règle que le témoin inverse d’une répétition SQL.
`phase2/checks/sonder_front_deploye.sh` est réécrit ainsi, et il l’a prouvé sur place :

```
essai 1 : index-DaU4SQsX.js -- presents 3/4 · disparus 0/2   <- REFUSE (ancien paquet)
essai 2 : index-QjC7_VDG.js -- presents 4/4 · disparus 2/2   <- ACCEPTE
```

### ⬜ CE QUI N’A PAS ÉTÉ VU

La **sous-ligne « Clos 14/10/2027 »** n’a pas pu être observée : la vue par défaut du
registre ne contient **aucun mandat clos** *(0 sur les 50 affichées ; les mandats 18836 et
11939 sont hors de ce périmètre)*. Son rendu n’est prouvé que par le code et par la
présence de `register-cloture` dans la CSS servie.

### ⚠⚠⚠ ET UN PIÈGE D’OUTILLAGE, LA TROISIÈME FOIS AUJOURD’HUI

Cette section a d’abord été écrite par un `python -c "..."` lancé depuis bash. **Les
accents graves du Markdown ont été pris pour des substitutions de commande** : `a_controler`,
`min-width`, `DEFILE: false` et `register-cloture` ont été **effacés**, et
`phase2/checks/sonder_front_deploye.sh` a été **réellement EXÉCUTÉ**, sa sortie collée dans
la note à la place du texte.

➡ **Règle : du texte Markdown ne passe JAMAIS par une chaîne bash entre guillemets
doubles.** On écrit un fichier `.py` et on le lance. *(Déjà arrivé le matin même sur
`CLAUDE.md`, où « fd8a042 » avait disparu du texte.)*

---

## 12. LA DATE DE CLÔTURE SE DÉCIDE EN ACCEPTANT LA DEMANDE — 16/10/2026

> *« il faut donc que ce soit dans la vue suivie et la tâche pour Pauline annulation de
> mandat qui gère la date de clôture et l’affiche »* — Frédéric, 16/10

**C’est la suite logique de sa consigne précédente.** Si clôturer passe toujours par la
demande d’annulation, alors c’est **l’acceptation qui clôt** — et la date doit se décider
là, pas ailleurs.

### Ce que l’audit a trouvé avant de coder

| | |
|---|---|
| le chemin de celui qui traite | la modale de demande → statut « accepté » → une **fenêtre de confirmation** *(« Finaliser l’annulation ? », Oui/Non)* → `handleUpdateDiffusionRequest` |
| qui clôt vraiment | **le « Oui » seulement** : la clôture A5 est dans `if (status === 'accepted' && unpublishAfterCancellation)` |
| ce que la charge portait | `requestId, status, response, refusalReason, followUpNeeded, followUpDays, relaunchCount, cancellationChecked, unpublishAfterCancellation` — **aucune date** |
| donc la clôture valait | **toujours le jour de l’acceptation** *(le worker retombait sur son repli)* |
| ce que la vue Suivi montre par demande | type, n°, date de demande, n° de mandat, bien, commercial, statut, motif — **aucune date de clôture** |

### Ce qui est écrit

1. **`closeDate` entre dans la charge de l’action** *(`UpdateDiffusionRequestAction`)*.
2. **Un champ « Date de clôture du mandat » dans la fenêtre de confirmation**, posé au
   **jour courant** à l’ouverture et modifiable par qui traite la demande. Il est montré **avant** le choix Oui/Non,
   pour que la date soit décidée **avant** le clic et pas après.
   ⚠ Il ne sert qu’au « Oui » : c’est lui seul qui clôture. C’est dit dans le code.
3. **Le chaînage A5 la transmet** : `closeDate` → `close_date` dans la charge du travail.
   ⭐ **C’est exactement ce pour quoi la pièce 1 avait été faite** le matin même : le worker
   lit `close_date` **en premier**. Rien à changer de son côté, **aucun redémarrage**.
4. **Et la date s’écrit CHEZ NOUS tout de suite** *(`setMandatClotureApp`)*, doctrine du
   chantier ③. Sans ça, la vue Suivi ne la montrerait qu’après le passage du worker
   (~30 s), et celui qui vient d’accepter le croirait perdu.
   ⭐ **Les deux écritures ne peuvent plus se contredire**, puisqu’on vient de donner la
   même valeur au worker — c’était tout l’objet de la pièce 1.
   ⚠ Un échec ici **ne fait pas échouer le geste** *(la demande est déjà acceptée, le
   travail déjà créé)* — mais il est **dit à l’écran**, traduit en français par
   `messageRefusCloture()`, pas avalé.
5. **La vue Suivi l’affiche** : une sous-ligne **« Clos le 14/10/2027 »** sous le numéro de
   mandat, dans le tableau des demandes. Rien quand le mandat n’est pas clos — pas de tiret.
6. **Deux classes CSS neuves** : `price-drop-popup-field` *(reprend le cadre de
   `price-drop-popup-detail` juste au-dessus)* et `suivi-cloture` *(même rôle que
   `register-cloture`)*. Aucune variable de couleur nouvelle.

### Les épreuves

`npm run build` **vert**. Témoins dans le fichier construit : « Date de clôture du mandat »
**2** *(la modale de statut + la nouvelle fenêtre)*, `close_date` **1**, « Clos le » **2**,
`suivi-cloture` **1** *(et 1 dans la CSS)*, `price-drop-popup-field` **1** *(et 4 dans la
CSS)*.

### ⛔ CE QUI RESTE À DIRE

1. ⚠⚠ **Ce chemin n’a jamais tourné en production** : les 4 demandes
   d’annulation acceptées datent de **mai**, le chaînage A5 est de **juillet**
   *(§ 1 de cette note)*. Ce code est donc **écrit mais jamais éprouvé en réel** — il le
   sera à la première vraie demande acceptée.
2. ⚠ **« Non » ne clôture pas**, donc la date saisie est alors sans effet. C’est le
   comportement d’avant, inchangé — mais la fenêtre montre le champ dans les deux cas.
   À trancher par Frédéric s’il veut que « Non » le cache.
3. ⚠ **La modale de statut clôt toujours sans passer par la demande** *(déjà réservée
   admin/manager)* — rappel du § 11, toujours à trancher.

### ⚠ « PAULINE » EST UN RÔLE, PAS UNE PERSONNE — précision de Frédéric, 16/10

> *« quand je dis Pauline c’est pour t’aider, car ce sont les comptes Admin et manager qui
> voient aussi dans le suivi des demandes »*

**Mesuré, et le comportement était déjà juste** : le bouton « Suivi » de la navigation est
derrière `isManagerOrAdmin`, et l’écran reçoit `isAdmin={isManagerOrAdmin}`.
⚠ **Le nom de la prop est trompeur** — `isAdmin` porte en fait « manager ou admin » — mais
la mesure, elle, ne l’est pas. **Aucun code à changer.**

En revanche **mes commentaires parlaient d’une personne** : ils sont redressés *(6 endroits)*
et disent maintenant « tout compte admin ou manager ».
⭐ **Je n’ai PAS purgé le mot « Pauline » du reste de l’app** : il y apparaît **35 fois** et
c’est le vocabulaire du projet pour ce rôle *(« Vue Pauline », « File Pauline »,
« Décision Pauline », `isPaulineAdministrativeProfile`…)*. Le renommer serait un autre
chantier, et il ne m’a pas été demandé.

---

# ⑦-3b — L'ÉCRAN DU JOURNAL DES SUPPRESSIONS — 16/10/2026

## 1. L'AUDIT : IL N'Y A PAS UN JOURNAL, IL Y EN A QUATRE

Et la phrase du chantier ③ — *« aucun écran ne le lit »* — est **exacte, re-mesurée** :
**zéro occurrence** des quatre tables dans tout le front.

| journal | lignes | sans demandeur | sans l'état d'avant | période |
|---|---|---|---|---|
| **annonce** | **114** | ⚠ **79** *(69 %)* | ⚠ **46** *(40 %)* | 15/05 → 29/08 |
| **contact** | **13** | 10 | **0** | 29/05 → 08/10 |
| **document** | **0** | — | — | — |
| **photo** | **1** | 0 | 0 | 14/10 |

**Trois choses que ces chiffres disent :**

① ⚠⚠ **Le journal des annonces est largement muet.** Le patch du 13/10 annonçait
*« une ligne a `before_json` vide et aucun demandeur »* — c'est en réalité **69 % et 40 %**.
Exemple réel du 29/08 : cible `99999999`, pas de demandeur, pas de motif, état d'avant
**VIDE**. On a détruit **sans savoir quoi ni qui**.

② ⛔ **Le journal des documents est à 0, et le restera pour le passé** : les **34 documents
détruits du 14/05 au 22/07** sont **antérieurs à la table** (créée le 13/10). Ils n'y sont
pas et n'y seront jamais. **Un journal vide ne veut pas dire « rien détruit ».**

③ ⭐ **La seule ligne de photo** (14/10) est la photo d'essai supprimée sur 62774 — la
**preuve que le mécanisme neuf écrit vraiment**.

### Les droits étaient déjà propres

| | |
|---|---|
| lire | `authenticated` **+ `app_console_current_role() = 'admin'`** → **admin STRICT** |
| écrire | `service_role` seulement |
| modifier / effacer | ⭐ **aucune politique** → la RLS refuse tout : le journal est **inaltérable** |

⭐ **Et l'écran Santé colle exactement à cette règle** : il reçoit `isAdmin={isAdmin}` —
l'admin **strict**, la seule exception du chantier ②. C'est le seul écran de l'app dont le
périmètre égale celui de ces tables.

## 2. LES DÉCISIONS DE FRÉDÉRIC — 16/10

> *« A ; dans santé. 2. Admin strict. 3. Tout »*

**Dans Santé** · **admin strict** *(la RLS n'est PAS touchée)* · **tout**, sans filtre de date.

## 3. CE QUI EST ÉCRIT

| pièce | où | quoi |
|---|---|---|
| **1** | `lib/api.ts` | `loadJournalSuppressions()` — **code neuf** : lit les 4 tables, les ramène à **une seule forme**, trie par date, et traduit `requested_by` en nom |
| **2** | `SanteSystemeScreen.tsx` | un bloc **« Journal des suppressions »**, patron du bloc « Agents IA » juste au-dessus |

⭐ **Aucune CSS nouvelle** : `ss-group`, `ss-rows`, `ss-row`, `ss-dot`, `ss-age` existaient
tous, et `timeAgo()` aussi.

**Quatre choix qui méritent d'être dits :**

- ⚠ **Chaque lecture tombe toute seule** (`try/catch` + `.catch(() => [])`). L'écran Santé
  charge en `Promise.all` : **une lecture qui jette ferait une page blanche** au lieu d'un
  bloc vide. C'est le seul vrai risque de cette pièce, et il est traité exprès.
- ⚠ **Pas de clic sur la ligne**, volontairement : **ces objets sont détruits**. Ouvrir la
  fiche d'un bien supprimé échouerait — un bouton qui ment.
- ⚠ **La pastille passe à l'orange quand l'état d'avant est vide** *(46 lignes sur 114)*.
  Ce n'est pas un détail décoratif : ces lignes disent qu'on a détruit **sans savoir quoi**.
- ⭐ **Une seule requête pour tous les noms**, pas une par ligne ; et si elle échoue on garde
  l'identifiant brut — **un identifiant affiché vaut mieux qu'une ligne manquante**.

## 4. LES ÉPREUVES

`npm run build` **vert**. Et le **témoin inverse promis à l'étape 2**, joué en empruntant les
deux identités, **en lecture seule** :

| qui | rôle | annonces | contacts | documents | photos | profils lisibles |
|---|---|---|---|---|---|---|
| codex.test | `admin` | **114** | **13** | 0 | **1** | **8** |
| legrand | `commercial` | **0** | **0** | **0** | **0** | **1** *(le sien)* |

✅ **128 lignes pour l'admin** — exactement le total annoncé *(114 + 13 + 0 + 1)*.
✅ **0 ligne pour le négociateur, SANS erreur** → l'écran montrera un bloc vide, pas une
panne. C'était la question qui comptait.
✅ La traduction des noms marchera : l'admin lit **8 profils**, le négociateur **1**.

## 5. CE QUI RESTE À DIRE

1. ⚠ **Le bloc ne s'affiche pas s'il est vide** (`suppressions.length > 0`). Pour un
   négociateur il n'existera donc pas du tout — mais il n'a pas accès à Santé de toute
   façon *(`isAdmin` strict dans la navigation)*.
2. ⚠ **Le manager ne le verra pas**, par décision du 16/10. L'ouvrir voudrait dire
   **remplacer les 4 politiques RLS** — une politique ne se complète pas.
3. ⬜ **Rien ne purge ce journal.** 128 lignes aujourd'hui, et il ne fera que grandir. Ce
   n'est pas un problème à cette taille ; ça le deviendra. Non traité, non demandé.

---

# ⑦-3c — METTRE UNE PHOTO EN COUVERTURE — 16/10/2026

> *« fais juste 1, le but est de finir le chantier 7 »* — Frédéric, 16/10

## 1. L'AUDIT : LA MOITIÉ DU TRAVAIL TOURNAIT DÉJÀ

⭐ **La commande de Hektor n'est pas seulement connue : elle est écrite dans le worker et
jouée tous les jours.** Quand on supprime une photo, il **renumérote** en renvoyant la liste
*(`mode=ordonne_photos`, `console_job_worker.js` l. 8725-8745, éprouvé le 14/10 sur 62774)*.
Elle n'avait jamais été un geste, seulement une conséquence.

⭐ **Et il n'y a pas deux gestes.** « Photo principale » n'est pas une notion à part chez
Hektor : c'est **la première de la liste**. Réordonner et choisir la couverture sont **le
même ordre** — le commentaire du worker le disait déjà.

| ce que notre base savait déjà | |
|---|---|
| photos | **441 302**, **toutes** avec un rang |
| visibles / masquées | **441 199** / **103**, zéro inconnue |
| la galerie à l'écran | **déjà triée** `visible` puis rang → la 1ʳᵉ tuile EST la couverture |
| le cockpit | l'étiquette déjà « Couverture » en CSS *(`:first-child`)* |

### ⚠⚠ LA MESURE QUI A ÉVITÉ UNE ERREUR SUR 47 584 ANNONCES

J'allais écrire « la couverture, c'est le rang **1** ». **C'est faux :**

| plus petit rang de l'annonce | annonces |
|---|---|
| **0** | ⭐ **47 584** *(97 %)* |
| 1 | 1 561 |
| 2, 3, 4, 6, 8, 10… | **37** — des listes **à trous** |

➡ On ne cherche donc **jamais** « le rang 1 » : on **renumérote de 0 à n-1**. Effet de bord
déclaré : ça **répare** les 37 listes trouées au passage.

### Ce qui manquait vraiment

⛔ aucun type de travail *(donc **les 3 verrous**)* · ⛔ aucun bouton à l'écran

## 2. LE CHOIX DE FRÉDÉRIC

Trois façons lui ont été présentées, chiffrées sur **10 259 biens vivants avec photos**
*(médiane **3** photos ; **5 463** en ont **3 ou moins** ; **1 418** en ont **plus de 15**)* :
① un clic « mettre en couverture » · ② des flèches · ③ le glisser-déposer.
➡ **① seul**, pour finir le chantier. Le glisser-déposer reste un point à part.

**Les droits** : le **négociateur sur SES biens**. Ce n'est pas mon choix — c'est la règle que
le projet applique **déjà** aux deux autres gestes photo *(`upload_hektor_photo` et
`delete_hektor_photo` sont dans la liste du commercial, mesuré le 16/10)*.

## 3. CE QUI EST ÉCRIT

| | où | quoi |
|---|---|---|
| **base** | `patch_chantier7_3c_photo_couverture_2026-10-16.sql` *(+ inverse + répétition)* | les **3 verrous** + la RPC `app_console_photo_couverture_optimistic` |
| **worker** | `console_job_worker.js` | **5 endroits** + `handleReorderHektorPhotos` |
| **front** | `types.ts`, `lib/api.ts`, `App.tsx`, `styles.css` | `mettrePhotoEnCouverture()` + le bouton ★ sur la tuile |

**Six choix qui méritent d'être dits :**

- ⭐ **La RPC fait les deux ou aucun** : elle renumérote **chez nous** ET crée le travail dans
  **la même transaction**. Si l'insertion échouait après la renumérotation, la galerie
  montrerait un ordre que Hektor n'aurait jamais reçu.
- ⭐ **Le worker n'invente pas l'ordre** : il le **porte**, depuis la charge. S'il le
  recalculait, il pourrait dire autre chose que l'écran — **exactement le défaut payé le
  matin même sur la date de clôture**.
- ⚠ **Les deux listes, pas une** : `liste_photos` et `liste_photos_hidden`. Les masquées
  repartent **dans leur ordre inchangé**, sinon elles remonteraient dans la galerie publique.
- ⚠ **Garde-fou de liste vide** *(leçon du chantier ③)* : une `liste_photos` vide dirait à
  Hektor « ce bien n'a plus de photo visible ». On **refuse bruyamment**.
- ⚠ **Pas de `confirm`** : le geste est **réversible**. Demander confirmation pour un geste
  réversible use la confirmation de celui qui ne l'est pas *(la suppression, juste à côté)*.
- ⚠ **Le bouton n'apparaît pas sur la 1ʳᵉ tuile** : elle **est** déjà la couverture. Un bouton
  qui ne fait rien est un bouton qui ment.

## 4. LES ÉPREUVES

`npm run build` **vert** · `node --check` sur le worker **vert** · **8 contrôles à blanc, 100 %
en lecture** sur les trois verrous *(dont les trois « retour à l'identique à l'octet près »)*.

### ⭐ LA RÉPÉTITION, COLLÉE PAR FRÉDÉRIC — TOUT EST VERT SAUF UNE LIGNE

```
1-avant  | 62774 : 4 visibles, 1ere 482253, rangs 1..4
2-apres  | contrainte / droits / distribution      = oui / oui / oui
2-apres  | RPC : authenticated / anon              = oui / non (correct)
2-apres  | ESSAI 487604 en couverture              = ok : 1 renumerotees
2-apres  | 62774 apres l'essai                     = 1ere 487604, rangs 0..3
2-apres  | le travail porte les 2 listes           = 4 visibles / 0 masquees
2-apres  | l'ordre d'AVANT est garde               = 4 photos
2-apres  | RE-ESSAI (deja en couverture)           = ok, et AUCUN nouveau travail
3-retour | le type a disparu des 3 / la RPC aussi  = oui / oui
3-retour | empreintes d'origine                    = 2 sur 3      <- LA SEULE
```

⭐ **L'essai réel a marché du premier coup** : la dernière photo est passée au rang **0**, les
autres à 1-3, et le re-essai n'a **créé aucun travail en double**.

### ⚠ ET LA LIGNE QUI N'EST PAS VERTE EST, JE CROIS, UN DÉFAUT DE MA MESURE

**Hypothèse** : l'inverse repose la contrainte **`NOT VALID`** — il ne peut pas lancer
`VALIDATE CONSTRAINT` dans une transaction annulée — et `pg_get_constraintdef` **ajoute ce
suffixe au texte**. L'empreinte diffère donc d'exactement ça. Le **vrai** patch et le **vrai**
inverse, eux, lancent tous deux `VALIDATE` à la fin : en production la contrainte revient
propre.

⚠ **Sur le moment je ne l'avais PAS prouvé** : il n'existe aucune contrainte non validée
dans la base à laquelle comparer. ➡ Plutôt que d'affirmer, j'ai **corrigé la répétition
pour qu'elle le dise elle-même** : trois lignes explicites au lieu d'un compteur, et la
contrainte mesurée **suffixe retiré**.

### ✅✅ ET LE SECOND COLLAGE DE FRÉDÉRIC L'A TRANCHÉ

```
3-retour | contrainte (texte nu)    = IDENTIQUE (suffixe NOT VALID present -- normal en repetition)
3-retour | droits (empreinte)       = IDENTIQUE
3-retour | distribution (empreinte) = IDENTIQUE
```

**Les trois reviennent à l'identique.** C'était bien **ma mesure**, pas le patch : la
contrainte ne portait que le suffixe `NOT VALID`, que le vrai patch retire en lançant
`VALIDATE CONSTRAINT`. ⭐ **La répétition est donc verte de bout en bout**, essai réel
compris, et le patch peut être collé.

⚠⚠ **Et la leçon vaut pour toutes mes répétitions** : « 2 sur 3 » est **juste mais muet** —
il ne dit pas LEQUEL, et il a coûté un aller-retour. **Un contrôle qui agrège perd
l'information qui sert à agir.** *(Et ma première correction l'avait rendu **tautologique**,
comparant la contrainte à elle-même : un contrôle qui passe toujours est pire que rien.)*

## 5. CE QUI RESTE

1. ⛔ **Le patch n'est pas collé** — attend une dernière répétition ou son go.
2. ⛔ **Les 4 services n'ont pas redémarré** : sans ça le geste crée un travail que
   **personne ne réclame**.
3. ⛔ **Rien n'est poussé.**
4. ⬜ **Le glisser-déposer** reste à faire, s'il le veut un jour.

### ✅ LE PATCH EST COLLÉ — CONTRÔLE DU 16/10, 5 VERTS SUR 6

« Vérifié, pas cru » : Frédéric a dit « j'ai collé », j'ai mesuré.

| contrôle | résultat |
|---|---|
| la contrainte connaît le type | ✅ **oui, et elle est VALIDÉE** |
| les droits : collé à `delete_hektor_photo` | ✅ oui |
| la distribution : branche **documents** | ✅ oui, collé à ses deux sœurs |
| la RPC existe | ✅ oui — `authenticated` **oui**, `anon` **non** |
| zéro retour chariot dans la RPC | ⚠ **NON : 112 sur 118 lignes** |

### ⚠ LE 6ᵉ : LES RETOURS CHARIOT, ET POURQUOI CE N'EST PAS UN DÉFAUT

Le fichier du dépôt est en **LF** : les 112 retours chariot viennent du **TRANSPORT**
*(le copier-coller depuis Windows)*. **4ᵉ fois aujourd'hui que cette famille se manifeste.**

✅ **Ce n'est pas un défaut de fonctionnement**, et c'est mesuré, pas supposé :
- **aucune chaîne ne traverse de ligne** — les 3 lignes à apostrophes impaires sont des
  **commentaires français** *(« L'ETAT », « n'aurait », « l'insertion »)* ;
- **preuve par l'exemple** : `app_set_mandat_cloture_optimistic` porte **102** retours
  chariot, elle est en production depuis le **13/10**, et elle a tourné correctement
  aujourd'hui.

⚠ **Mon premier test disait « DANGER » — c’était une mauvaise expression de ma part**
*(elle attrapait `);` en fin de ligne)*. Refait proprement, il dit non.

⭐ **MAIS ÇA MORDRA PLUS TARD**, et la cause mérite d’être sue :

| le patch… | résultat |
|---|---|
| **LIT** la fonction en base et la réécrit *(archiver un contact)* | **0** retour chariot — il enveloppe déjà `replace(…, chr(13), '')` |
| **CRÉE** la fonction depuis le texte collé *(celle-ci)* | **emporte le CRLF tel quel** |

Tout patch futur qui voudra modifier cette fonction par **ancre** ne la retrouverait pas
*(leçon du 15/10, écrite trois fois)*. ➡ **`patch_chantier7_3c_nettoyer_crlf_rpc_2026-10-16.sql`**
la relit et la réécrit sans retours chariot. **5 lignes, aucun changement de comportement,
pas d’inverse** *(remettre des CRLF n’aurait aucun sens)*.

### ⭐⭐⭐ L'ESSAI RÉEL A RÉUSSI DU PREMIER COUP — 16/10, 15:41

⚠ **62774 n'était pas une cible possible** : c'est une **ARCHIVE**, sa fiche est en lecture
seule, elle n'a pas de galerie. Il fallait un bien **vivant** — et comme changer une
couverture change **l'annonce publique**, j'ai cherché une cible **sans effet dehors** et je
l'ai fait valider : **63261 « Maison individuelle Saugues »**, *Actif*, **0 portail,
non diffusable**, 3 photos, rangs **1..3** *(donc 1-based — ce qui éprouve aussi la
renumérotation)*.

**État d'avant, figé :** `487540` (rang 1) · `487541` (rang 2) · `487542` (rang 3).
**Geste :** clic sur le ★ de la **3ᵉ tuile**, depuis l'écran, sous le compte de Frédéric.

| ce qui a été mesuré | résultat |
|---|---|
| l'écran, avant le clic | 3 tuiles, **2 boutons ★** — **aucun sur la 1ʳᵉ**, qui porte le badge « Couverture » |
| nos photos après | ✅ `487542` **rang 0** · `487540` rang 1 · `487541` rang 2 |
| le travail | ✅ `reorder_hektor_photos` / **done**, pris par **`…:documents:service:v9`** — la branche visée |
| la liste envoyée | ✅ `["487542","487540","487541"]` |
| l'ordre d'avant | ✅ gardé, 3 photos |
| le journal | `claim → running → done → sync_queue → finish` en **2 secondes** |

### ⭐ ET HEKTOR L'A PRIS — vérifié CHEZ LUI, pas déduit

⚠ **La relecture ne prouvait rien** : elle a bien tourné *(13:41:33 → 13:42:08, done)*, mais
nos lignes portaient encore **notre propre** horodatage *(13:41:31)* et celui du matin
*(05:16:5x)* — donc **elle n'avait rien réécrit**. En conclure « Hektor a confirmé » aurait
été *une avarie qui ne change rien ne prouve rien*, à l'envers.

➡ **Je suis allé regarder sa page**, comme Frédéric me l'a appris le matin même
*(« tu as accès à la session chrome de Hektor, vérifie toi-même »)* :

| position chez Hektor | fichier | c'est… |
|---|---|---|
| **1** | `photo_3a03b621…` | ⭐ **487542**, celle mise en couverture |
| 2 | `photo_1197f9e7…` | 487540 *(était 1ʳᵉ)* |
| 3 | `photo_881cf27f…` | 487541 |

**Exactement la liste envoyée.** ✅ Le geste marche de bout en bout : écran → RPC → travail
→ worker documents → Hektor.

⚠ **Une observation, pas un défaut** : la vignette du *résumé* du bien montrait encore la
façade juste après. La galerie, elle, était bien réordonnée. Hektor a peut-être un champ
« photo principale » distinct de l'ordre, ou une vignette en cache — **non mesuré, donc non
conclu**. À regarder si ça gêne.

⚠ **À DÉCIDER** : la couverture de ce bien réel est maintenant **une chambre** au lieu de la
façade. Le bien n'est pas diffusé, donc **aucun effet public** — mais il faut **remettre la
façade** si Frédéric le veut (un clic sur le ★ de la façade suffit : le geste est réversible,
c'est tout son intérêt).

### ✅ LA FAÇADE EST REMISE — et le geste a prouvé sa réversibilité

Sur sa demande, un second clic sur le ★ de la façade *(487540)* :

| | |
|---|---|
| chez nous | ✅ `487540` **rang 0** · `487542` rang 1 · `487541` rang 2 |
| chez Hektor | ✅ `photo_1197f9e7…` **en premier** — la façade |
| les travaux | **2 sur 2 en `done`**, **0 en erreur** |

⭐ **Le geste marche donc dans les deux sens, et en quelques secondes.**

⚠⚠ **MAIS IL NE RESTAURE PAS UN ORDRE, ET IL FAUT LE SAVOIR.** L'ordre d'origine était
`487540 · 487541 · 487542` ; il est maintenant `487540 · 487542 · 487541` — **les 2ᵉ et 3ᵉ ont
permuté**. C'est la définition même du geste ① : il **met une photo en tête** et laisse les
autres dans leur ordre courant. Ce n'est pas un « annuler ».

⭐ **L'ordre d'avant est pourtant gardé** dans `base_snapshot` de chaque travail : un futur
geste « remettre comme avant » aurait tout ce qu'il lui faut. **Non demandé, non fait.**
*(Sur ce bien : 3 photos, 0 portail — sans conséquence.)*

### ⭐⭐ COMPRENDRE L'ORDRE CHEZ HEKTOR — sur la mise en garde de Frédéric

> *« peux tenter de comprendre l'ordre chez hektor, attention il y a aussi visible / non
> visible »*

**Mesure sur nos données** : les **103 photos masquées** sont sur **14 annonces**, et sur
chacune les deux numérotations **se chevauchent complètement** :

| annonce | rangs des visibles | rangs des masquées |
|---|---|---|
| 59434 | **1..13** | **1..14** |
| 61521 | **1..10** | **1..10** |
| 40563 | **0..5** | **1..14** |

➡ **Ce ne sont pas deux parties d'une même liste : ce sont DEUX LISTES SÉPARÉES**, chacune
numérotée depuis le début. C'est exactement pourquoi la page de Hektor appelle `saveOrder`
**deux fois**, une par `div`.

### ⭐ ET LE POINT QUI SIMPLIFIE TOUT : HEKTOR NE REÇOIT JAMAIS DE NUMÉRO

Ce que le worker lui envoie, c'est **une suite d'identifiants**, pas des positions :

```
liste_photos[]=487540&liste_photos[]=487542&liste_photos[]=487541
&mode=ordonne_photos&div=liste_photos&idann=63261
```

➡ **Notre `sort_order` n'est qu'un rang INTERNE.** Qu'il commence à 0 ou à 1 est **sans
importance pour Hektor** — il ne lit que **l'ordre des identifiants**. C'est pour cela que
l'essai a marché du premier coup sur un bien numéroté **1..3**, alors que 97 % du parc est
numéroté **à partir de 0**.

### Ce que ça veut dire pour le geste — et c'est rassurant

| | |
|---|---|
| **masquer une photo** | la sortir de `liste_photos`, l'entrer dans `liste_photos_hidden` — **et les deux se renumérotent** |
| **la couverture** | la **1ʳᵉ de `liste_photos`**, rien d'autre |
| **notre geste** | envoie **les deux listes**, les masquées **dans leur ordre inchangé** ✅ |
| ⚠ **les 103 masquées d'aujourd'hui** | elles ont **toutes** `present_in_hektor = false` — Hektor ne les a plus. La RPC les **exclut**, la liste masquée part **vide**, et le worker **saute** une liste vide au lieu de dire « il n'y a plus de photos masquées » ✅ |

⭐ **Rien ne casse de ce côté**, et **⑦-8** *(rendre visible / masquer)* aura la commande toute
prête : c'est la même, avec la photo qui **change de liste**.

⚠ **Non mesuré** : ce qui se passe quand une photo masquée est **encore chez Hektor**
*(`present_in_hektor = true`)* — il n'en existe **aucune** aujourd'hui. Le code la traiterait
*(elle partirait dans `liste_photos_hidden` avec son rang)*, mais ce chemin **n'a jamais été
emprunté**.

---

# ⑦-4 — LE BANDEAU QUI MENT — 16/10/2026

## 1. L'AUDIT : IL MENT À 9 462 BIENS, ET IL MENT DEUX FOIS

Le code disait tout :

```tsx
const lightweightDetailLabel = dossier.archive === '1' ? 'archivee' : 'historique'
...
<p>Cette annonce {lightweightDetailLabel} … il faut d'abord la desarchiver.</p>
<button>Demander le desarchivage</button>
```

**Seul le MOT changeait.** La phrase et le bouton parlaient toujours de désarchivage.

| qui voit ce bandeau | biens | le bandeau |
|---|---|---|
| **archivés** | **35 325** | ✅ dit vrai |
| **vendus / clos** *(sans détail en cache)* | **8 935** | ⛔ **ment** |
| **brouillons** | **527** | ⛔ **ment** — cas que l'énoncé ne mentionnait pas |
| vendus/clos avec détail | 8 | pas de bandeau |

⭐ Le **brouillon** est la trouvaille : c'est une **saisie en cours**, en lecture seule **par
décision** (23/06). Lui dire « désarchive-la » n'a aucun sens, et l'app avait déjà le bon
bouton ailleurs : **« Reprendre la saisie »**.

### ⚠⚠ ET LE SECOND MENSONGE EST PIRE QUE LE PREMIER

Le bouton crée un `restore_hektor_annonce`, qui envoie à Hektor
`mode=upval&champ=archive&val=0`. Or **les 8 935 vendus/clos ont DÉJÀ `archive=0`**
*(mesuré : **0** sur 8 943 à `'1'`)*. L'ordre ne changerait rien — **mais le contrôle final
du worker exige `archive == "0"`, donc il serait SATISFAIT et le travail passerait `done`.**

➡ **Le bouton dirait « Désarchivage demandé », le travail réussirait, et le bien resterait
en lecture seule.** C'est *« une avarie qui ne change rien ne prouve rien »*, retournée :
**une réussite qui ne fait rien**.

⭐ **Personne n'a encore été trompé** : les **15** désarchivages demandés portent tous sur
**4 biens d'ESSAI** *(62965, 78, 62774, 24113)*.

## 2. ⭐ LE PATRON EXISTAIT DÉJÀ — DANS LA VERSION MOBILE

Avant d'inventer quoi que ce soit : la **fiche mobile** distinguait **déjà** l'archive du
vendu/clos, avec le bon message **et** le bon bouton *(« Changer le statut »)*. Le mensonge
n'était donc que côté **desktop**. On a recopié sa logique au lieu d'en écrire une seconde.

## 3. CE QUI EST ÉCRIT *(pièce 1 seule — sa décision)*

**Trois états, trois messages, et un seul bouton — celui qui sert :**

| état | titre | bouton |
|---|---|---|
| **archivé** | « Fiche archivée » | **Demander le désarchivage** *(inchangé)* |
| **vendu / clos** | « Bien vendu ou clos » | **Charger le détail** *(son choix)* |
| **brouillon** | « Saisie en cours chez Hektor » | **Reprendre la saisie dans Hektor** |

⭐ **Aucun des trois boutons n'est neuf.** « Désarchiver » était là ; « Charger le détail »
et « Reprendre la saisie » existaient **ailleurs dans l'app**. On ne les invente pas, **on
les met au bon endroit**.

⭐⭐ **ET LA FAMILLE EST BALAYÉE EN ENTIER** *(leçon du 08/10)* : le **mobile** aussi disait
« Cette fiche vendue ou close » à un brouillon. Il a désormais son 3ᵉ cas, avec le même
bouton. **S'arrêter au desktop aurait laissé 527 biens avec le mensonge.**

⚠ **Une plomberie à dire** : le bouton « Charger le détail » a demandé une **prop neuve**
*(`onOpenLightweightDetail`)*, déclarée sur **4 composants** et passée aux **3 sites
d'appel** — une prop déclarée mais non passée aurait donné un bouton qui **ne s'affiche
jamais**, ce qui est pire qu'un bouton qui ment. *(C'est exactement le piège payé le matin
même sur ⑦-1.)*

## 4. LES ÉPREUVES

`npm run build` **vert**, et témoins **dans les deux sens** sur le fichier construit :

```
DISPARUS : "il faut d'abord la desarchiver"      0
           "Lecture seule jusqu'a desarchivage"  0
           "Fiche consultee depuis l'index leger" 0
PRESENTS : "Charger le détail"                   1
           "Reprendre la saisie dans Hektor"     2   <- desktop ET mobile
           "Bien vendu ou clos"                  1
           "Saisie en cours chez Hektor"         1
           "Cette fiche vendue ou close"         1   <- mobile, toujours juste
           "il faut d'abord la désarchiver"      1   <- la seule branche qui le mérite
```

## 5. CE QUI RESTE À DIRE

1. ⚠ **Deux boutons différents pour le même cas** : pour un vendu/clos, le **desktop** offre
   désormais « **Charger le détail** » *(son choix)* et le **mobile** offre « **Changer le
   statut** » *(qui existait avant)*. Les deux se défendent — charger pour consulter, changer
   le statut pour le ramener au parc — mais **ce n'est pas aligné**. À trancher.
2. ⛔ **La pièce 2 n'est pas faite** *(sa décision : « juste la 1 »)* : le worker répondrait
   toujours `done` à un désarchivage inutile. Plus personne ne peut cliquer ce bouton à tort,
   mais le trou reste **si un autre chemin rappelait ce geste**.
3. ⛔ **Rien n'est poussé**, et **personne n'a vu l'écran** — tout est prouvé par le build et
   les textes servis.

### ⚠⚠⚠ CORRECTION MAJEURE — LE BANDEAU MENTEUR EST DANS L'ANCIENNE FICHE

**Je me suis trompé de composant, et il faut le dire avant tout le reste.**

En allant montrer les trois cas à l'écran, j'ai découvert que :

```tsx
return APP_COCKPIT_V2_ENABLED ? <CockpitDetail {...props} /> : <DossierDetailLayoutBase {...props} />
```

➡ **J'ai corrigé `DossierDetailLayoutBase` — que la production NE REND PAS.** Le drapeau est
allumé *(cockpit v2 en prod)*, et c'est `CockpitDetail` qui s'affiche.

**Preuve observée deux fois, en direct** : les fiches ouvertes rendent `fa-ck-hero-photo`,
`fa-ck-mb`, `fa-ck-rub` — classes qui n'existent QUE dans `CockpitDetail` — et
`.detail-readonly-banner` était **toujours absent**.

### ⭐ ET LE COCKPIT, LUI, NE MENT PAS

Ses messages de lecture seule disent **« depuis une fiche d'index léger »**, jamais
« désarchiver » :

> « Les documents ne peuvent pas être modifiés **depuis une fiche d'index léger**. »
> « Le mandat ne peut pas être édité **depuis une fiche d'index léger**. »

⭐ **Et le premier écran d'un vendu/clos ne ment pas non plus** : c'est la fenêtre d'import,
qui dit déjà « **VENDU** · Détail à charger » et offre « Télécharger le détail de la fiche ».
*(Mesuré sur 62966, un bien d'essai : après l'import, la fiche s'ouvre en cockpit, sans
aucun bandeau.)*

### CE QUE MON TRAVAIL VAUT DONC, EXACTEMENT

| | |
|---|---|
| **le mobile** *(`MobileDossierDetail`)* | ✅ **VIVANT** — il mentait vraiment aux **527 brouillons**, et il est corrigé |
| **`DossierDetailLayoutBase`** | ⚠ **code que la prod ne rend pas** — mais c'est le **filet de secours** : si le drapeau du cockpit était éteint *(rollback prévu, garde-fou n° 2 du plan)*, cette fiche reviendrait, **et elle mentirait**. La corriger n'est donc pas inutile : c'est réparer le repli |
| **ce que je t'avais annoncé** | ⛔ « le bandeau ment à 9 462 biens » — **faux en production**. Il aurait menti à 9 462 biens **si le cockpit était éteint** |

⚠⚠ **LA FAUTE DE MÉTHODE, nommée** : j'ai lu le code, mesuré la base, compté les biens — et
**je n'ai pas vérifié QUEL COMPOSANT S'AFFICHE** avant d'écrire. C'est la règle « mesurer LE
GESTE DE L'ÉCRAN, pas un geste plausible » *(leçon 1 de `CLAUDE.md`)*, et un drapeau de
bascule la rend encore plus impérative : **deux composants répondent au même nom, un seul
s'affiche**.

➡ À TRANCHER PAR FRÉDÉRIC : garder la correction *(elle répare le repli, coût nul)*, ou la
retirer. Et **le second mensonge reste entier** : le bouton « désarchiver » d'un vendu/clos
réussirait sans rien faire — mais puisque ce bandeau ne s'affiche pas, **personne ne peut le
cliquer** aujourd'hui.

### ✅ SA DÉCISION, 16/10 : ON GARDE

> *« garde-la, ça répare le repli et ça ne coûte rien »*

La correction de `DossierDetailLayoutBase` reste donc en place : le jour où le drapeau
`APP_COCKPIT_V2_ENABLED` serait éteint — c’est un **rollback prévu**, le garde-fou n° 2 du
plan — l’ancienne fiche reviendra **sans son mensonge**.

⭐ **Et la part vivante tient debout** : le mobile ne dit plus « Cette fiche vendue ou close »
aux **527 brouillons**, il leur propose « Reprendre la saisie dans Hektor ».

---

# ⑦-8 — VISIBLE / MASQUER UNE PHOTO — AUDIT DU 16/10/2026

> ⚠ **CET AUDIT A ÉTÉ REFAIT DEUX FOIS, SUR DEMANDE DE FRÉDÉRIC.** Ma première conclusion
> était fausse, la seconde était fondée sur une preuve qui n'en était pas une. Ce qui suit
> est la troisième version, celle qui est mesurée de bout en bout — et c'est **lui** qui a
> donné la bonne direction : *« regarde dans le serveur ??? cherche dans les notes »*.

## 1. LA CHAÎNE COMPLÈTE — serveur Hektor → app → coffre → vitrine

| étage | ce que c'est | le drapeau `visible` |
|---|---|---|
| **① Hektor, serveur** | **deux** listes : `liste_photos` *(visibles)* et `liste_photos_hidden` *(masquées)*. Deux guichets de lecture : `mode=vignettes` et `mode=vignettes_hidden` | **la source de vérité** |
| **② l'API detail** *(celle du run)* | remplit le miroir `data/hektor.sqlite` *(**4 Go**)*, table `hektor_annonce_detail`, colonne `images_json` | ⭐ **la clé `visible` existe — et vaut `'1'` partout** |
| **③ notre table** `app_console_photo` | **441 302** lignes, dont **440 862** posées par `rattrapage_photos.js` *(`source: "miroir_local"`)* | colonne `visible`, **true sur 441 199** |
| **④ le coffre public** `gti-photo` | les dérivés `w400` / `w1600` de ③ | — |
| **⑤ la vitrine** | `espace_client.py:88` lit **`app_dossiers_current`** *(la **vue**)* → `COALESCE(images_preview_json_app::text, images_preview_json)` | ⭐ **NOTRE galerie gagne** |

### ⭐⭐ LA RÉPONSE À « ÇA FONCTIONNAIT » : C'EST VRAI, ET CE N'EST PAS NOUS

**Mesure du 16/10, en lecture seule, sur le miroir** *(échantillon de 3 000 annonces,
17 535 photos)* : chaque entrée de `images_json` porte **7 clés** — `id, order, img,
visible, legende, path, pathTumb` — et **`visible` vaut `'1'` pour les 17 535**.

➡ **L'API de Hektor ne nous livre QUE les photos visibles.** Une photo masquée chez Hektor
**n'arrive jamais jusqu'à nous** par le chemin de masse. Ce n'est pas un filtre de notre
part : c'est Hektor qui ne la donne pas.

⭐ **Et ce n'est pas qu'un échantillon** : `accorder_photos_miroir.js` a comparé, le 15/10,
notre drapeau à celui du miroir et trouvé **0 divergence sur 441 238 photos**. Le parc
entier est donc couvert.

### LES CHIFFRES DE NOTRE TABLE, AU 16/10

| `visible` | `present_in_hektor` | photos | annonces | ce que c'est |
|---|---|---|---|---|
| **true** | **true** | **440 862** | 49 188 | le cas normal |
| true | false | 337 | 53 | retirées chez Hektor *(« delete-never »)* |
| **false** | **false** | **103** | **14** | les masquées — **toutes absentes de Hektor** |
| **false** | **true** | **0** | **0** | ⭐ **CE CAS N'EXISTE PAS AUJOURD'HUI** |

Les 103 masquées viennent des **304 annonces** passées par `sync_hektor_photos` *(le seul
chemin qui interroge `vignettes_hidden` — `console_job_worker.js:4491`)*, et le dernier
travail de ce type date du **27/09**.

⚠ **À rapprocher de la note du 25/09** *(`AUDIT_PHOTOS_2026-09-25.md`)*, qui comptait
**1 252 visibles sur 1 397** : **145 masquées existaient alors**. Le chargement de masse
depuis le miroir les a noyées dans 441 000 lignes toutes marquées visibles.

## 2. ⚠⚠ LE DÉFAUT RÉEL : `visible` EST UN TRI, JAMAIS UN FILTRE — SAUF UNE FOIS

**Quatre endroits lisent le drapeau. Un seul filtre.**

| # | qui | ce qu'il fait de `visible` | qui le voit |
|---|---|---|---|
| 1 | `app_photos_remplir_adresses_app` *(étape « adresses photos » du run)* | ⛔ `order by p.visible desc nulls last` — **TRI** | **la vitrine publique** + la vignette du listing et du registre |
| 2 | `app_get_dossier_photos`, **source principale** | ⛔ `row_number() over (order by p.visible desc …)` — **TRI** | l'écran **Rapprochement acquéreur** *(`RechercheAcquereur.tsx:534`)* |
| 3 | `app_get_dossier_photos`, **repli** | ✅ `and coalesce(img->>'visible','1') = '1'` — **FILTRE** | le même écran, quand notre table est vide |
| 4 | `loadConsolePhotos` *(front)* | ⛔ `order('visible', desc)` — **TRI**, et c'est **VOULU** | le panneau photos de l'app *(il faut voir une masquée pour la démasquer)* |

⭐ **Le projet SAVAIT** : le repli ③ porte la bonne règle. Elle a été **perdue en passant
du repli à la source principale** — c'est-à-dire le jour où le chargement de masse a rempli
`app_console_photo`. Avant, la source principale était vide *(1 397 photos sur 229
annonces au 25/09)* et **le repli faisait tout le travail**.

### ⚠⚠ ET LA VITRINE DÉTRUIT LA SEULE PROTECTION QUI RESTAIT

La galerie publique est un **tableau** dont l'ordre porte la protection *(`visible desc`
d'abord)*. Mais `espace_client.py::_photos` **re-trie par le champ `order`** :

```python
order = int(it.get("order"))        # ... ordered.sort(key=lambda x: x[0])
```

➡ Une photo masquée **ne serait même pas en dernier** : elle reprendrait **sa place
naturelle**, donc possiblement **en première page du site public**.

⭐ *(La **vignette** d'accroche, elle, reste protégée : `photo_url_listing_app =
g.entrees->0->>'url'` prend la **première entrée du tableau**, donc une visible.)*

## 3. ⭐⭐ LA COMMANDE DE MASQUAGE EST DÉJÀ ENTRE NOS MAINS

**Rien à relever chez Hektor.** Le geste de suppression du 14/10 renumérote **les deux
listes** *(`console_job_worker.js:8832`)* :

```js
for (const [div, visible] of [["liste_photos", true], ["liste_photos_hidden", false]]) {
  const ids = apres.filter((e) => Boolean(e.visible) === visible) ...
  // ...&mode=ordonne_photos&div=${div}&idann=...
}
```

➡ **Déplacer un id de `liste_photos` vers `liste_photos_hidden`, c'est masquer.** C'est
`mode=ordonne_photos`, **déjà connu, déjà écrit, déjà prouvé en production** le 14/10
*(suppression)* et le 16/10 *(réordonnancement de ⑦-3c)*.

⚠ **À NE PAS CONFONDRE avec les deux boutons que Frédéric a en mémoire** : ceux de
`App.tsx` *(~11929 « Visible »/« Masquée » et ~19363 « Masquer »/« Rendre visible »)*
agissent sur des photos **pas encore envoyées** — le brouillon de création et le panneau
de dépôt. Le worker choisit alors `#fileupload` ou `#fileuploadHidden`
*(`console_job_worker.js:8264`)*. **Aucun des deux ne touche une photo existante.**

## 4. CE QUI N'A PAS PU ÊTRE MESURÉ

- **Hektor a-t-il des photos masquées aujourd'hui ?** Le savoir exigerait d'interroger
  `vignettes_hidden`, donc **un appel à Hektor par annonce** — non fait, et hors feu vert.
  Ce qu'on sait : il en avait **145** au 25/09 sur les 229 annonces alors indexées.
- **Le compte complet du miroir** *(hors échantillon)* tournait encore à la rédaction ;
  les 0 divergences du 15/10 sur 441 238 le remplacent.

---

## 5. L'AUDIT APPROFONDI DU 16/10 — demandé par Frédéric, mesuré dans la CONSOLE HEKTOR

> *« retrouve nos essais lors de la création de code ajouter photo et également le coffre
> privé et public, pourquoi nous n'avons pas téléchargé les photos non visibles […]
> regarde dans la console Hektor Chrome »*

### 5.1 ⭐⭐ CE QUE HEKTOR DIT, DANS SES PROPRES MOTS

Relevé **en direct le 16/10** sur `…/?page=/mes-biens/mon-bien/photos&id=62774` :

```
Photos visibles sur votre site et dans vos exports        [ VISIBLES ]
  « cliquez et glissez les photos dans l'ordre que vous désirez »
  1  2  3  4        [+ Ajouter des photos]

Photos non visibles sur votre site et dans vos exports    [ NON VISIBLES ]
  « cliquez et glissez les photos dans l'ordre que vous désirez »
  (vide)            [+ Ajouter des photos]
```

⭐ **DEUX ZONES, deux bandeaux, deux boutons d'ajout** — et **on masque en GLISSANT** une
photo de l'une à l'autre. C'est **mot pour mot** `mode=ordonne_photos` avec ses deux `div`
*(`liste_photos` / `liste_photos_hidden`)* : un classeur à deux listes reliées.

➡ **« Visible » veut dire : sur votre SITE et dans vos EXPORTS** *(donc les portails)*.
C'est la définition de Hektor, pas une interprétation.

### 5.2 NOS ESSAIS DU GESTE « AJOUTER UNE PHOTO » — 19 envois, 7 biens, 22/05 → 14/10

| date | bien | durée | remarque |
|---|---|---|---|
| **22/05 06:59** | 24113 | **889 s, 3 tentatives** | ⭐ **le tout premier**, et le seul qui ait peiné |
| 22/05 07:34 · 03/06 · 22/06 | 24113 | 20 / 22 / 36 s | |
| 29/05 · 30/05 | 62354, 62356 | 16 / 32 s | |
| 30/06 · 02/07 ×2 | 24935 | 54 / 58 / 45 s | |
| 23/07 ×2 | 62774 | 24 / 27 s | |
| 05/08 ×4 | 62853 | 18 à 34 s | |
| **26/09 07:32** | 63146 | 18 s | ⭐ celui qui a prouvé qu'**ajouter une photo fait bouger la date de l'annonce** |
| 11/10 ×2 · 14/10 | 62774 | 29 / 49 / 32 s | lot 3d, puis la suppression |

⭐⭐ **ET LA MESURE QUI COMPTE** : la clé `visible` est présente dans **les 19 charges**,
et elle vaut **`true` dans les 19**. ➡ **`#fileuploadHidden` n'a JAMAIS été emprunté.**
La branche « masqué » du code existe depuis le 22/05 et **n'a jamais été exécutée**.

### 5.3 LES DEUX COFFRES

| | **coffre PRIVÉ** | **coffre PUBLIC** |
|---|---|---|
| où | **notre serveur Windows**, disque | Supabase Storage, bucket **`gti-photo`** *(`public = true`)* |
| quoi | **l'original** de chaque photo | **les dérivés** `w400` + `w1600` |
| combien | **441 302** lignes d'index, **≈ 172 Go** | **189 807** fichiers *(= 114 025 + 75 779)* |
| qui en a | **tout le parc** | ⭐ **les vivantes à 100 %** *(75 260/75 260)* ; vendues **8 %**, archivées **11 %** |

⭐ **La règle G.8 est donc vraie et mesurée** : *« les dérivés sont la VITRINE »*. Une
annonce qui sort du parc vivant garde son original chez nous et **perd peu à peu sa
présence publique**.

### 5.4 ⭐⭐ POURQUOI NOUS N'AVONS PAS TÉLÉCHARGÉ LES NON VISIBLES — la réponse, datée

`Console/rattrapage_photos.js`, en-tête du **25/09/2026** :

```
// ⚠⚠ CE SCRIPT NE PARLE JAMAIS A HEKTOR.
//    Les adresses sont DEJA sur ce serveur, dans le miroir local (data/hektor.sqlite,
//    hektor_annonce_detail.images_json -- 57 967 annonces). On lit en local, on
//    telecharge sur le CDN public.
//    -> AUCUNE requete contre le quota Hektor, aucun risque de bannissement
```

➡ **Ce n'est pas un oubli, c'est une conséquence.** Le rattrapage a été écrit pour **ne
jamais appeler Hektor**, après le **bannissement d'IP du 20/08**. Or le miroir est nourri
par **l'API detail**, et l'API detail **ne liste que les visibles** *(mesure : `visible`
vaut `'1'` sur 17 535/17 535 entrées)*. Les masquées ne vivent que derrière
`mode=vignettes_hidden`, **un appel Hektor par annonce** — exactement ce que le script
devait éviter.

**LE RATTRAPAGE, NUIT DU 25 AU 26/09 :**

| passe | départ | résultat |
|---|---|---|
| 1 | **25/09 23:07** | 444 431 photos au miroir · 434 626 lignes créées · **260 233 rapatriées, 174 433 en échec, 102,8 Go**, 14,8 ph/s |
| 2 *(reprise)* | **26/09 04:16** | **174 433 rapatriées, 0 échec, 69,2 Go**, 23,7 ph/s |

⛔ **8 013 photos de 583 annonces ont été ÉCARTÉES** : pas de numéro app.

### 5.5 ⚠⚠ LE DÉFAUT TROUVÉ — UNE PHOTO MASQUÉE EST PRISE POUR UNE PHOTO SUPPRIMÉE

Les **103** photos masquées de notre table *(14 annonces)* ont été :
- **créées le 17/08/26, 18:40 → 19:52**, source `hektor_console` *(donc lues par
  `sync_hektor_photos`, le seul chemin qui interroge les DEUX guichets)* ;
- **déclarées « absentes de Hektor » le 15/10/26 à 21:23** — **les 103 à la même minute**.

**PREUVE EN DIRECT, 16/10, que c'est FAUX :**

| annonce | masquées chez **Hektor** | chez **nous** | visibles chez **Hektor** | chez **nous** |
|---|---|---|---|---|
| **32704** | **19** | **19** | **12** | **12** |
| **59434** | **14** | **14** | — | 11 |

**Les comptes collent exactement : ces photos sont TOUJOURS chez Hektor.**

⭐ **LA CAUSE** : le rapprochement compare notre registre au **miroir**, qui ne contient
que les visibles. Une photo masquée n'y figure pas ⇒ elle **ressemble trait pour trait à
une photo supprimée**, et les trois conditions de garde du script
*(`accorder_photos_miroir.js`, verrou 2)* ne la protègent pas : elle a un
`hektor_photo_id`, elle est plus ancienne que la lecture du miroir, et ce n'est pas un
envoi `app` en cours.

⚠ **Et le compte rendu ne pouvait pas le voir** : `visible_divergent` n'est calculé que
pour les photos **trouvées dans le miroir**. Une masquée n'y est pas du tout, donc elle
tombe dans `a_marquer`, jamais dans `visible_divergent`. ➡ **Le « 0 divergence sur
441 238 » est exact ET aveugle à ce cas précis.**

**CONSÉQUENCE MESURÉE** : `loadConsolePhotos` filtre `present_in_hektor = true`, donc ces
**103 photos ont disparu du panneau photos de l'app**. ⭐ **Gravité limitée, et il faut le
dire : les 14 annonces sont TOUTES des ARCHIVES** *(14/14)* — en lecture seule, hors
vitrine, sans dérivés voulus.

### 5.6 L'AGENCE SE SERT-ELLE DE CETTE ZONE ? — sondage en direct du 16/10

**10 biens interrogés chez Hektor, 10 fois `vignettes_hidden` VIDE** : 63261, 62774, et
les **8 biens vivants les plus photographiés** *(5836, 59396, 61554, 8474, 10139, 61547,
8484, 5843 — de 91 à 107 photos, 792 photos en tout)*.

➡ **Sur le parc VIVANT, la zone « non visibles » n'est pas utilisée aujourd'hui.** Les
seules masquées connues sont les **103 d'archives**, posées en **août**.

⛔ **Ce qui reste non mesuré, et je le dis** : les 49 188 annonces n'ont pas été sondées —
ce serait **un appel Hektor par annonce**. ⭐ **L'outil existe pourtant depuis le 26/09** :
`Console/sonde_photos_manquantes.js` lit les deux guichets et les compare au miroir —
**mais il n'est enregistré dans AUCUNE tâche** *(0 référence dans `scheduled/`,
`phase2/`, `monitoring/`)*. Il n'a donc jamais tourné.

### 5.7 LES TROIS QUESTIONS DE FRÉDÉRIC, MESURÉES *(16/10, fin d'après-midi)*

**Q1 — « dans le serveur il y a 170 Go, il y a aussi le masqué ? »** ➡ **OUI.**

| | photos | fichier pesé | poids | empreinte | **dérivé public** |
|---|---|---|---|---|---|
| **les masquées** | **103** | **103** | **69 Mo** | **103** | ⭐ **0** |
| tout le parc | 441 302 | 441 300 | **171 Go** | 441 300 | 114 025 |

⭐⭐ **La règle que Frédéric décrivait est donc RESPECTÉE** : les masquées sont **sur le
serveur** *(coffre privé, `local_only`)* et **PAS dans le coffre public** — **0 dérivé sur
103**.

**Q2 — « dans l'app uniquement les annonces visibles des annonces vivantes ? »** ➡ **NON,
c'est plus large.** `loadConsolePhotos` filtre **`present_in_hektor`**, jamais `visible`,
et ne regarde aucun monde en particulier :

| monde | photos en index | **vues au panneau** | cachées | annonces |
|---|---|---|---|---|
| **vivant** | 75 260 | **74 927** | 333 | 10 259 |
| vendu / clos | 104 830 | 104 830 | 0 | 8 489 |
| **archive** | 260 269 | 260 162 | **107** | 30 271 |
| brouillon | 941 | 941 | 0 | 167 |

⚠ **Nuance d'écran** : le panneau n'est rendu que sur une fiche **complète** ; sur une
fiche d'index léger *(vendu/clos sans détail, brouillon)* il n'est pas affiché du tout —
donc `loadConsolePhotos` n'y est jamais appelé *(décision du chantier ⑥, 6a-bis)*.
⭐ Les **440 cachées** *(333 + 107)* sont exactement le `a_marquer 440` de la référence du
15/10 : des photos marquées « absentes de Hektor », dont **103 ne le sont pas** (§ 5.5).

**Q3 — « les vitrines/écrans utilisent bien NOS photos ? Pas celles du miroir Hektor ? »**
➡ ⭐⭐ **OUI, à une annonce près.**

| sur **13 493** annonces vivantes | |
|---|---|
| **notre vignette** d'accroche | **13 493 / 13 493** — **0 de Hektor** |
| **notre galerie** | **10 259** |
| « galerie Hektor » | 3 234 — ⭐ mais **3 233 sont des COQUILLES VIDES** : `[{"url":null,"full":null,"legend":null,"order":null}]`, et `_photos()` saute toute adresse qui ne commence pas par `https://` ⇒ **rien ne s'affiche**, le repli est **notre** vignette |
| ⚠ **vraie adresse Hektor servie** | **1 seule : 63299** |

⚠ **L'EXCEPTION, 63299** — « GARAGE / ENTREPOT 36 m² », Saint-Étienne, **ACTIVE et
DIFFUSABLE** : sa galerie pointe `groupe-gti-immobilier.staticlbi.com` *(le CDN de
Hektor)* pendant que notre vignette dit `gti-photo/marque/sans-photo.jpg`. **Le site
montre donc la photo de Hektor ET « sans photo ».**
⭐ **Ce n'est pas une fuite, c'est un délai** : elle a été **enregistrée le 15/10**, elle
n'a **aucune photo chez nous** et `adresses_app_le` est **null**. La ligne photos de
« GTI Entretien Documents » *(22:00)* doit la rapatrier **ce soir**. ⏰ **À recontrôler
demain matin : si 63299 a toujours 0 photo chez nous, le rattrapage quotidien ne tient
pas.**

⭐ **Et le rattrapage quotidien tient, mesuré** : sur les annonces vivantes enregistrées
depuis août — **oct. 48/59 · sept. 118/134 · août 94/107 ont nos photos** ; les autres
n'ont **aucune photo du tout**, chez personne *(ce sont les coquilles vides)*.

### 5.8 ⚠⚠ CORRECTION — J'AVAIS RATÉ UN CONSOMMATEUR, ET LES NOTES LE DISAIENT

Frédéric : *« non c'est bizarre, retrouve des notes qui le disent clairement »*. **Il avait
raison** : j'avais grepé `backend/`, `apps/`, `supabase/`, `Console/` et `phase2/*.py` —
**jamais `Ecrans Android/`**. Or `AUDIT_DEUX_COFFRES_PHOTOS_DOCUMENTS_2026-09-26.md`
liste **CINQ** consommateurs, dont **`Ecrans Android/export_project_vitrine.py` (8 points,
la vitrine publique GitHub)**. **Il y a bien DEUX vitrines.**

#### Les notes qui le disent clairement

**`NOTE_PHOTOS_HEKTOR_API_CONSOLE_2026-05-18.md`** *(la note fondatrice, 18/05)* :
> *« Les photos **VISIBLES** issues de l'API Hektor restent stockées sous forme d'URLs »*
> *(`images_json`, `images_preview_json`, `photo_url_listing`, `nb_images`)*
> *« Une couche Console **séparée** a été ajoutée […] Elle stocke uniquement l'index :
> […] **visible / masquée** »* · le worker lit **`vignettes` ET `vignettes_hidden`**
> *« les badges `API`, `Visible`, `Masquée` ; un formulaire `Ajouter une photo`
> visible / masquée »*
> *« Les futures actions photos restent à faire […] : modifier une légende ;
> **MASQUER / AFFICHER** ; supprimer ; réordonner. »*

⭐⭐ **DEUX FLUX, ÉCRITS DEPUIS LE 18/05 — c'est la clé de tout** : le **flux API**
*(quotidien, miroir)* ne connaît **que les visibles** ; la **couche Console**
*(`sync_hektor_photos`, à la demande)* connaît **visible ET masquée**. ➡ Les **103**
masquées viennent de la couche Console *(17/08)*, les **441 000** du flux API
*(25-26/09)*. **Les deux affirmations étaient vraies, elles ne parlaient pas du même
chemin.**

⭐ **`AUDIT_DEUX_COFFRES…_2026-09-26.md`** confirme la date : *« travaux
`sync_hektor_photos` : **313 en tout, le dernier le 17/08** »* — et mesure le serveur à
*« 481 527 fichiers · 229,4 Go (documents 60 + **photos 169**) »*.

#### ⭐⭐ ET LA VITRINE PUBLIQUE, ELLE, PORTE LE BON FILTRE — DEPUIS TOUJOURS

`Ecrans Android/export_project_vitrine.py`, fonction **`visible_photos()`** :

```python
for img in ordered:
    if str(img.get("visible", "1")).strip() == "0":
        continue          # elle ECARTE les masquees
```

Sa doctrine **G.15 (27/09)**, en en-tête du fichier :
> *« LA VITRINE PUBLIQUE PUBLIE **NOS** ADRESSES DE PHOTOS »* · *« la vitrine ne publie
> que les annonces non archivées + diffusables + actives/sous offre/sous compromis »* ·
> *« Mesure du 27/09 : sur les 459 annonces publiées, **459 ont notre vignette et 458
> notre galerie** »* · *« ⚠⚠ SI SUPABASE NE RÉPOND PAS, ON PUBLIE LES ADRESSES HEKTOR —
> JAMAIS RIEN »*

#### ⛔ MAIS CE FILTRE EST INERTE — mesuré le 16/10

`images_preview_json_app` *(notre galerie)* porte **4 clés : `full, legend, order, url`**.
**`visible` n'y est PAS** — sur **0 des 10 259 galeries**. Et `visible_photos` lit
`img.get("visible", "1")`, donc **défaut « visible »**.

➡ **Le projet a écrit le bon filtre, notre galerie ne lui donne pas le champ.** Le
commentaire le frôle : *« LE FORMAT TOMBE JUSTE SANS CONVERSION : nos entrées sont
{url, full, order, legend} »* — l'auteur a vérifié `url` et `order`, **sans voir que
`visible` manquait**.

#### LE TABLEAU CORRIGÉ — CINQ consommateurs, et le correctif qui en découle

| # | consommateur | source | `visible` |
|---|---|---|---|
| 1 | **vitrine publique** GitHub/Android | **nos colonnes `_app`** | ✅ **FILTRE** — ⛔ **inerte, clé absente** |
| 2 | **espace client** *(`espace_client.py`)* | la vue `COALESCE` | ⛔ **aucun filtre**, et il **re-trie par `order`** |
| 3 | **écran Rapprochement** *(`app_get_dossier_photos`)* | notre table / repli Hektor | ⛔ TRI · ✅ **FILTRE** au repli |
| 4 | **panneau photos de l'app** | notre table | ⛔ TRI — **et c'est VOULU** |
| 5 | **RDV public + e-mails** de rapprochement | `photo_url_listing` | ✅ protégé *(1ʳᵉ entrée = visible)* |

⭐⭐ **LE CORRECTIF DEVIENT MINUSCULE** : ajouter **`'visible', p.visible`** au
`jsonb_build_object` de `app_photos_remplir_adresses_app`. **Une clé** — et le filtre que
le projet a déjà écrit le 27/09 se met à fonctionner tout seul sur la vitrine publique.
Restent alors **2** et **3** à aligner.

### 5.9 LE RATTRAPAGE GLOBAL DES PHOTOS — **il était prévu, il EXISTE, il tourne**

Frédéric : *« on a fait des run de téléchargement des photos et je pense qu'on avait prévu
une mise à jour ou rattrapage globale, cherche des notes »*. **Il a raison, et c'est en
place.**

#### La note qui le prévoit — `AUDIT_ETAPE_PHOTOS_DANS_LE_RUN_2026-09-26.md`

> *« Hektor **DATE** les photos […] donc pas de balayage à construire — juste une étape au
> bon endroit. »* · fenêtre imposée : **après `push upgrade to supabase`** *(sinon les
> photos d'une annonce née cette nuit sont écartées faute de numéro d'app)* et **avant
> l'export vitrine**. · *« Les photos n'ont pas ce problème [de quota] — CDN public, hors
> quota, **0 refus sur 435 000 téléchargements** »*, donc **dans le run**, pas en tâche
> séparée. · réglages : **non bloquante**, **`--limite 2000`**, sonde
> **`-WorkerKey "phase2.rattrapage_photos"`**.

#### ✅ LES QUATRE ÉTAPES SONT DANS `run_full_pipeline.ps1`

| ligne | étape | sonde | ce matin |
|---|---|---|---|
| **1600** | `rattrapage_photos.js` *(télécharge)* | `phase2.rattrapage_photos` | ✅ 05:12 |
| **1628** | `generer_derives_photos.js` *(coffre public)* | `phase2.derives_photos` | ✅ 05:12 |
| **1657** | `remplir_adresses_photos.js` *(nos adresses)* | `phase2.adresses_photos` | ✅ 05:12 |
| **1695** | `sonde_photos_manquantes.js` *(25 annonces/nuit)* | `phase2.sonde_photos` | ✅ 05:13 |

⚠ **Je m'étais trompé deux fois et il faut le dire** : j'avais écrit que la sonde n'était
*« enregistrée dans aucune tâche »*. **Faux** — elle est **ligne 1695 du run**. Mon grep
cherchait dans `scheduled/`, or **`run_full_pipeline.ps1` est à la RACINE**. Même erreur
que pour `Ecrans Android/` : **je cherche là où je pense, pas partout.**

#### Le journal du 16/10 — ce que la chaîne a fait cette nuit

```
07:07:59  rattrapage photos : miroir 463 249 · deja dans l'index 441 238
          ⛔⛔ ECARTEES (pas de numero app) : 22 403 photo(s), 2 809 annonce(s)
          64 photo(s) rapatriee(s) · 0 en echec · 61,0 Mo
07:12:20  derives : 87 photos sans derives
07:12:52  adresses photos (app_photos_remplir_adresses_app : 0,5 s)
07:13:46  sonde : ✅✅ Aucune photo manquante sur cet echantillon  (25 annonces)
```

#### ⚠⚠ LE TROU QUE LE JOURNAL MONTRE SANS LE DIRE : **22 403 PHOTOS ÉCARTÉES CHAQUE NUIT**

C'était **8 013 photos / 583 annonces** le 25/09. C'est **22 403 / 2 809** aujourd'hui.

⭐ **Mesuré dans le miroir, ce sont EXACTEMENT les LOCATIONS** — et le compte tombe à
l'unité :

| `offre_type` | libellé *(`mandat_ledger.py:943`)* | annonces | |
|---|---|---|---|
| `0` | vente | 57 249 | ✅ admis |
| `10` | vente immo pro | 1 043 | ✅ admis |
| `6` | neuf | 1 | ✅ admis |
| **`2`** | **LOCATION** | **2 869** | ⛔ écartée |
| **`11`** | **LOCATION immo pro** | **262** | ⛔ écartée |

**3 131 annonces de location, toutes avec des photos, et `22 403` photos — le chiffre exact
du journal.** Le périmètre « vente seulement » est **écrit** dans le projet
*(`TYPES_ADMIS_AU_REGISTRE = ("0","10","6")` · `TYPES_LOCATION = ("2","11","8")`)*.

⛔⛔ **MAIS L'EXCLUSION N'EST PAS DÉCLARÉE — et c'est la leçon du projet, prise en
flagrant délit.** `rattrapage_photos.js` *(l. 260-264)* **imprime une ligne et continue** :

```js
if (sansNumeroApp.length) {
  console.log(`  ⛔ ECARTEES (pas de numero app) : ...`);
}
```

**Aucune alerte, aucun code de sortie, aucun battement en erreur.** Le script **ne sait pas
que ce sont des locations** — il dit seulement *« pas de numéro app »*. Donc : si un jour
de vraies annonces de **vente** tombaient dans ce panier, **elles s'y perdraient sans un
bruit**, noyées dans les 22 403.

➡ **QUESTION POUR FRÉDÉRIC, et elle n'est pas technique** : **veut-on les photos des
locations ?** Aujourd'hui elles n'existent **que chez Hektor** — ni sur notre serveur, ni
dans le coffre public. **Au jour de la coupure, ces 22 403 photos meurent.**
⭐ Le rapatriement coûterait peu : ~22 400 photos à 12-25 photos/s = **15 à 30 minutes**,
sur le **CDN public, hors quota Hektor**.

### 5.10 ⭐⭐ LA REPONSE A LA QUESTION DE FREDERIC — **NON**, en une mesure

*« je t'ai demandé de faire tout cela pour savoir si notre rattrapage récupère les photos
non visibles de Hektor ? »* — **La réponse est NON.** Preuve sur **l'annonce 32704**,
16/10 :

| | |
|---|---|
| **chez Hektor** *(lu en direct)* | **19 masquées** + **12 visibles** |
| **dans le miroir** *(la seule source du rattrapage)* | **12 photos**, toutes `visible='1'` — `451251, 451250, 311055, 311093, 311102, 311106, 311111, 311113, 311114, 311116, 311128, 451252` |
| **les 19 masquées cherchées dans le miroir** | ⛔ **0 trouvée, 19 absentes** |

➡ **Le rattrapage ne peut pas les voir** : il lit `hektor_annonce_detail.images_json`,
et elles n'y sont pas. Ce n'est pas un réglage à changer — **la matière n'arrive jamais
jusqu'à lui**.

⭐ **Les 19 que nous avons viennent d'un AUTRE chemin** : `source = hektor_console`,
créées le **17/08/26 à 19:34** par `sync_hektor_photos` — **le seul qui interroge
`vignettes_hidden`** — et **ce chemin est arrêté depuis le 17/08** *(313 travaux, le
dernier ce jour-là)*.

⚠ **Donc les 103 masquées que nous avons sont un PLANCHER, pas un total.** Seules **304**
annonces sur 49 188 sont jamais passées par ce guichet. Ce que Hektor garde de masqué sur
les 48 884 autres est **inconnu** — et **invisible pour nous**.

---

# ✅ CONTROLE DU 17/10/2026 — après le run de nuit

*Demandé par Frédéric : « le run du 17 est passé, vérifie ton travail ».*

## Ce qui était à prouver, et ce que ça donne

| contrôle | attendu | **mesuré le 17/10** |
|---|---|---|
| **63299** *(enregistrée le 15/10, servait le CDN Hektor)* | rapatriée à 22:00 | ✅ **2 photos, NOTRE galerie**, adresses calculées **05:17** |
| annonces vivantes servant une **vraie** adresse Hektor | 0 | ✅ **0** *(c'était 1)* — les 3 234 restantes sont **toutes** des coquilles vides |
| **⑦-3c la couverture** *(63261 et 63046)* | tient après le run | ✅ `487540` et `485272` toujours en tête, **après DEUX runs** |
| **⑦-3a en ligne** *(sonde `sonder_front_deploye.sh`)* | 4 présents / 2 disparus | ✅ **4/4 et 2/2** sur `/assets/index-1nL-Mwzp.js` — « Clôturer ce mandat » et « Rouvrir le mandat » **ont bien disparu** |
| **les 103 masquées** | inchangées *(rien n'a été corrigé)* | ✅ 103, toujours marquées absentes — **le diagnostic tient** |

## Le run du 17 — les 4 étapes photos

```
07:13:16  rattrapage : 46 photo(s) rapatriee(s) · 0 en echec · 44,3 Mo
          ⛔⛔ ECARTEES : 22 403 photo(s), 2 809 annonce(s)   <- IDENTIQUE au 16/10
07:17:14  derives : 47 photos
07:17:40  adresses photos (app_photos_remplir_adresses_app : 0,8 s)
07:18:34  sonde : ✅✅ Aucune photo manquante sur cet echantillon
```

⭐ **Le chiffre des écartées est EXACTEMENT le même deux nuits de suite** : c'est bien un
**ensemble figé** *(les locations)*, **pas une fuite qui grandit**. Mon analyse du 16/10
est confirmée par un second jour.

## La santé des photos — `accorder_photos_miroir.js` *(lecture seule)*

| | référence du 15/10 | **17/10** |
|---|---|---|
| `a_marquer` | **440** *(67 annonces)* | ✅ **12** *(4 annonces)* |
| `a_reordonner` | **1 662** *(290 annonces)* | ✅ **93** |
| `visible_divergent` | 0 | ✅ **0** |
| `manquantes_chez_nous` | — | ⚠ **22 403** — **le même chiffre, par un second chemin** |

## L'entretien documents — le point ⑧ qui attendait depuis le 16

`python phase2/checks/controle_entretien_documents.py` : la tâche a tourné **le 17/10 à
22:00:01, résultat 0**, **4 lignes sur 4**, aucune en échec, **33/33 empreintes** sur les
annonces libérées, **2 725 empreintes vérifiées** dans la nuit.
⭐⭐ **ET LE TÉMOIN QUI COMPTAIT EST VERT** : **46 lignes portent `cloud_refuse`**
*(référence de la veille : **0**)* — **le correctif du coffre a travaillé en réel.**

⚠ **Le seul rouge est un FAUX rouge** : « la file est vide : 292 travaux ». Mesure : ce
sont **291 `sync_console_documents` créés 6 minutes plus tôt**, **1 en cours**, **36
terminés dans l'heure**, le dernier **il y a 4 secondes**, et les **4 services battent**
*(documents `success`, les 3 autres `idle` à 29-49 s)*. **La file se vide en direct.**
➡ Le contrôle exige « file vide », ce qui ne peut pas être vrai juste après un entretien
qui vient d'enfiler du travail. **Le critère est à revoir**, pas la file.

---

# ✅ ⑦-3a PIÈCE 2 — **EN PRODUCTION LE 18/10/2026**

*La porte de derrière est fermée. Go de Frédéric : « Oui puis colle ».*

## La répétition — **verte 14 sur 14**, collée par Frédéric

```
1-avant  | la garde est dans la fonction  = non
1-avant  | empreinte de la fonction       = 09280b46e6832db15dce53ca5e30e9db
1-avant  | ancre vue combien de fois      = 1
1-avant  | TEMOIN INVERSE negociateur     = ACCEPTE (ok=true) -- le trou est reel
2-apres  | la garde est dans la fonction  = oui
2-apres  | la fonction compile            = oui (elle a ete reexecutee sans erreur)
2-apres  | negociateur (legrand)          = REFUSE : droits_insuffisants
2-apres  | le refus est en francais       = oui
2-apres  | admin (codex.test)             = ACCEPTE (ok=true)
2-apres  | service_role (worker/re-pose)  = ACCEPTE (ok=true)
3-retour | la garde est dans la fonction  = non
3-retour | trace is_app_manager_or_admin  = non
3-retour | trace droits_insuffisants      = non
3-retour | empreinte de la fonction       = IDENTIQUE
ERROR: ESSAI ANNULE -- rien n a ete ecrit.
```

⭐ **La ligne qui comptait était la 4ᵉ** : `TEMOIN INVERSE negociateur = ACCEPTE`. Sans
elle, on aurait posé une garde sur un trou qui n'existait pas.

## Le contrôle après collage — **mesuré, pas cru**

⚠ Frédéric a dit « c'est collé » **sans joindre le résultat**. J'ai donc mesuré la base
au lieu de le croire sur parole.

| contrôle | résultat |
|---|---|
| la garde est posée | ✅ **OUI** |
| elle appelle `is_app_manager_or_admin` | ✅ oui |
| le refus est lisible *(`droits_insuffisants`)* | ✅ oui |
| `service_role` exempté *(worker + re-pose)* | ✅ oui |
| **empreinte** | `09280b46…` → **`03d520f5b76880fc5e81e5b22b50cb35`** |
| **retours chariot** | ⭐ **0** — le collage n'a pas introduit de CRLF *(leçon du 15/10 tenue)* |
| droits | `postgres` · `authenticated` · `service_role` — **`anon` absent** |

**Le tri des rôles, éprouvé EN PRODUCTION** *(identités empruntées, lecture seule)* :
`legrand` (commercial) → **REFUSÉ** · `codex.test` (admin) → **ACCEPTÉ**.

**Et le bout de la chaîne tient** : le paquet servi `/assets/index-1nL-Mwzp.js` porte
`droits_insuffisants` **2 fois** et « manager ou un administrateur » **1 fois** — un
négociateur verra donc **une phrase, pas un code**. Rien à pousser pour ça.

⚠ **CE QUI N'EST PAS ÉPROUVÉ, ET JE LE DIS** : la branche **« manager »**. Il y a
**5 admin et 3 commercial, ZERO manager** dans `app_user_profile`. Elle repose sur
`is_app_manager_or_admin()`, déjà en production et qui teste `role in ('admin','manager')`.

## Deux commentaires périmés corrigés le même jour

1. **L'en-tête du patch** annonçait « un changement d'avis assumé ». **Inexact** : le 13/10
   tranchait **QUI APPELLE** *(l'écran → `authenticated`, la nuit → `service_role`)*, et la
   question du **RÔLE** derrière l'écran n'avait jamais été posée. Les deux décisions
   **se complètent**. Réécrit, **0 ligne exécutable touchée** *(prouvé par `git diff`)*.
2. **`App.tsx:7700`** disait « `droits_insuffisants` n'existe PAS ENCORE en base ». Faux
   depuis le collage. Corrigé, **commentaire seul** *(4 insertions, 3 suppressions,
   aucune ligne de code)*. ⚠ Il n'atteindra la production qu'au prochain push.

---

# ⑦-7 — MODIFIER OU PROLONGER UN MANDAT — AUDIT DU 18/10/2026

> ## ⛔⛔ DÉCISION DE FRÉDÉRIC, 18/10/2026 — **ON NE LE FERA PAS**
>
> *« Mais je ne souhaite pas pouvoir modifier un mandat ou prolonger »*, dit **pendant**
> cet audit, avant toute ligne de code. **Le point ⑦-7 est FERMÉ. Ne pas le relancer de
> soi-même.**
>
> ⭐ **C'est cohérent** : un mandat est un **contrat signé**. Le prolonger depuis l'app
> engagerait l'agence sur un acte juridique, et Hektor reste la source de cet acte — même
> logique que la clôture, qu'on a décidé le 13/10 de **ne jamais transmettre à Hektor**.
>
> ### ⚠ MAIS L'AUDIT A SERVI, ET DEUX CHOSES RESTENT SUR LA TABLE
>
> 1. **202 biens EN VENTE ont un mandat échu et non clos** *(sur 741)*, et **26 arrivent
>    à échéance sous 30 jours**. Ce n'est pas un trou de code — c'est un fait métier que
>    cet audit a mis au jour. **Question ouverte à Frédéric : que fait-on de ces 202 ?**
>    *(rien · les clore · une alerte)* — et la clôture, elle, **existe déjà** depuis ⑦-3a.
> 2. **La commande des dates est identifiée** *(`protexa-valideStep3`)* et **le GET de
>    lecture aussi** *(`protexa-mandat&mandat=<n>`)*. **Écrit ici pour ne pas être
>    recherché deux fois**, si la question se rouvrait un jour.
>
> ⚠ Ce qui suit est l'audit tel qu'il a été mené avant la décision. Il est conservé pour
> ses mesures, **pas comme un plan de travail**.


## 1. LE TABLEAU DES GESTES SUR UN MANDAT — mesuré, pas recopié

| geste | base (RPC) | worker | écran | chez Hektor |
|---|---|---|---|---|
| **créer un n°** | ✅ `app_console_create_mandat_auto_number_job` | ✅ `create_hektor_mandat_auto_number` | ✅ | ✅ PROTEXA step1→5 |
| **clôturer** | ✅ `app_set_mandat_cloture_optimistic` *(⑦-3a ; manager/admin depuis le 18/10)* | écrit en direct | ✅ | ⛔ **jamais transmis** *(décision du 13/10)* |
| **générer un document** | — | ✅ `generate_mandat_document` | ✅ | — |
| **modifier le PRIX** | ⬜ | ✅ `ihmChargeGroupe_MandatPrix` *(bloc `mandat_infofi`)* | ✅ l'avenant *(PDF)* | ✅ |
| ⛔ **PROLONGER (dates, durée)** | ⛔ **rien** | ⛔ **rien** | ⛔ **rien** | 🔎 **commande identifiée, jamais éprouvée** |
| **alerter « échu »** | ✅ `app_generate_mandat_echu_alerts` | — | ✅ | — |

⭐ **L'ÉNONCÉ DU 08/10 EST PÉRIMÉ SUR UN POINT** : il dit *« il n'y a ni travail worker ni
RPC […] il faut ouvrir Hektor »*. **Faux pour le prix** — le worker écrit **déjà** dans le
bloc mandat de Hektor *(`console_job_worker.js:11132`)*. Juste pour les **dates**.

## 2. L'AMPLEUR — et le chiffre qui parle n'est pas celui du registre

| | |
|---|---|
| lignes au registre | **24 568** · dont **23 614 échues** ⚠ *mais c'est tout l'historique* |
| ⭐ **mandats de biens VIVANTS** | **741** |
| ⚠⚠ **déjà échus ET non clos** | **202** — *des biens en vente sans mandat valide* |
| échéance sous 30 j · 90 j | **26** · **84** |
| au-delà de 90 j | 443 |

⚠ **Trouvé en plantant la mesure** : **2 dates `0000-00-00`** et **30 sans date de fin**
dans le registre — la date vide à la mode Hektor. Toute RPC de prolongation devra les
refuser proprement au lieu de lever.

## 3. CE QUE LE PROJET AVAIT DÉJÀ ÉCRIT

**`E.0-bis`** *(liste des tâches, l. 1071, repris dans
`AUDIT_FRONT_ET_RESTE_DU_PLAN_2026-09-25.md`)* :
> *« modifier un MANDAT existant (dates, durée, avenant qui prolonge) — **seuls prix,
> honoraires et surface le sont**. »*

Chiffré **2-3 jours**, classé `L5`. Et le commit `a56eef2` du 25/09 le résume :
*« tous les écrans en service et complets ; **seul manque = l'avenant ne prolonge pas** »*.

⭐ L'avenant actuel *(`App.tsx:5012`)* est un **PDF** dont le texte dit lui-même :
*« les parties conviennent […] de modifier **le prix de commercialisation** du bien, sans
novation »*. **Il ne touche ni nos données, ni Hektor, ni les dates.**

## 4. ⭐⭐ LA COMMANDE DES DATES EST IDENTIFIÉE

Dans le geste de création *(`console_job_worker.js`, step 3)* :

```js
mode: "protexa-valideStep3",
id: annonceId,
numMandat: numeroMandat,      // <- un numero DEJA EXISTANT
date_debut: mandat.dateDebut,
duree: mandat.duree,
TR: mandat.taciteReconduction,
```

➡ **`valideStep3` porte exactement les dates, et il prend un numéro existant.** C'est
`step1` avec `numMandat: "0"` qui, lui, **consomme un numéro neuf**.

**Et pour OUVRIR un mandat existant, le code de Hektor lui-même** *(capture du 12/06,
`labs_Header.js`)* :

```js
function load_protexa_mandat(numMandat) {
  var dataToSend = { mode: "protexa-mandat", mandat: numMandat, idann: idann };
  $j.ajax({ type: "GET", url: 'xmlrpc.php', data: dataToSend, ... });
}
```

⭐ **C'est un GET → relevable EN LECTURE SEULE.** Le worker ne l'appelle qu'avec
`mandat=0`. *(À ne pas confondre avec `protexa-saveProtexa` / `protexa-duree`, qui sont
les réglages de l'AGENCE — login PROTEXA et durée par défaut — pas un mandat.)*

## 5. ⛔ CE QUE JE N'AI PAS PU MESURER, ET JE LE DIS

1. **Hektor accepte-t-il `valideStep3` sur un mandat déjà finalisé** *(step5 passé)* ?
   **Inconnu.** C'est un POST qui écrit : impossible à éprouver en lecture.
2. **Que rend `protexa-mandat&mandat=<numéro réel>` ?** **Jamais relevé** — le projet ne
   l'a appelé qu'avec `mandat=0`.
3. ⚠⚠ **LE RISQUE QUI DOMINE TOUT** : un numéro de mandat est **NON ANNULABLE** — écrit
   noir sur blanc dans `sonde_mandat_prix_web.js` *(05/10)*. **Si rejouer step3 CRÉE au
   lieu de MODIFIER, on brûle un numéro à chaque essai.**

---

# ⑦-8 — AUDIT EN PROFONDEUR DU 18/10 : **la pièce A n'était pas le sujet**

*Frédéric a refusé de coller : « j'ai besoin de bien comprendre ». Il avait raison —
l'audit qui suit a trouvé **deux choses plus graves** que la clé `visible`.*

## ⭐ CE QUI EXISTE DÉJÀ, ET QUE JE N'AVAIS PAS VU

**1. Le worker sait DÉJÀ masquer.** `handleReorderHektorPhotos` prend **deux listes**
dans la charge *(`liste_photos`, `liste_photos_hidden`)* et envoie chacune à son guichet.
➡ Masquer = déplacer un id d'une liste à l'autre. **0 nouveau type de travail, 0 des
3 verrous, 0 redémarrage des 4 services.**

**2. La RPC de couverture fait déjà les 9/10 du travail** : elle construit les deux
listes **depuis `visible`** (⑦), garde **`visible` dans son `base_snapshot`** (③, donc le
retour arrière existe), et pose le travail. Une RPC « masquer » serait **la même, avec une
seule différence** : basculer `visible` au lieu de renuméroter.
⚠ Elle porte **112 retours chariot** *(jamais nettoyés — patch du 16/10 non collé)* :
écrire « masquer » comme un patch à ancre **dans** cette fonction casserait. ➡ **nouvelle
fonction, pas un patch de celle-là.**

## ⚠⚠ LE VRAI SUJET N° 1 — LE GESTE SERAIT À SENS UNIQUE

Enchaînement mesuré :
1. on masque → Hektor déplace la photo dans sa liste cachée ;
2. **l'API detail cesse de la lister** → elle disparaît du miroir ;
3. **chaque nuit à 22:00**, `accorder_photos_miroir.js` tourne **avec `--appliquer`**
   *(`run_entretien_documents.ps1` : `if (-not $DryRun) { $argsPhotos += "--appliquer" }`)* ;
4. sa branche de marquage ne regarde **PAS** `visible` :
   `if (!chezEux) { ... aMarquer.get(aid).push(r.id); }` → **present_in_hektor = false** ;
5. ⛔ `loadConsolePhotos` filtre `present_in_hektor` → **la photo sort du panneau de
   l'app**, et la RPC exige `present_in_hektor IS TRUE` → **on ne peut plus la
   démasquer**.

⭐ **CE N'EST PAS UNE HYPOTHÈSE : c'est exactement ce qui est arrivé aux 103**, le 15/10
à 21:23. Et la preuve du 16/10 : 32704 porte **19 masquées + 12 visibles chez Hektor**,
nos comptes exacts — elles n'avaient jamais disparu.

➡ **REMÈDE : UNE LIGNE** dans `accorder_photos_miroir.js`, avant le marquage — *une
masquée n'est pas une supprimée*. **À poser AVANT le bouton**, sinon le premier masquage
est irréversible au bout d'une nuit.

## ⚠ LE VRAI SUJET N° 2 — MASQUER NE RETIRE PAS LA PHOTO D'INTERNET

`app_photo_marquer_sortie_vitrine` *(08:30)* ne marque `hors_vitrine_depuis` que pour les
photos dont **l'annonce n'est plus vivante** — elle ne regarde **ni `visible` ni
`present_in_hektor`**. ➡ **Une photo masquée d'un bien EN VENTE garde son dérivé dans
`gti-photo` indéfiniment**, et son adresse publique continue de servir à qui la connaît.

*(Mesure : 472 photos marquées absentes, dont **365 ont encore un dérivé public**. Les 103
masquées, elles, sont toutes sorties du coffre — **parce que leurs 14 annonces sont des
ARCHIVES**, pas parce qu'elles sont masquées.)*

❓ **À TRANCHER PAR FRÉDÉRIC** : « masquer » veut-il dire *« retirer de la galerie »* ou
*« plus personne ne peut la voir »* ? La seconde demande un travail en plus.

## L'ORDRE QUI EN DÉCOULE — et il n'est plus celui que j'avais proposé

| # | pièce | pourquoi à cette place |
|---|---|---|
| **1** | **une masquée n'est pas une supprimée** *(1 ligne JS)* | sans elle, le geste est à sens unique |
| **2** | la clé `visible` *(pièce A, écrite)* | ferme la fenêtre entre le masquage et la nuit |
| **3** | l'espace client *(pièce B)* | il ne filtre pas, et re-trie par `order` |
| **4** | la RPC + le bouton *(pièce C)* | **le plus petit**, tout le reste existe |
| ? | le coffre public | **décision de Frédéric d'abord** |
