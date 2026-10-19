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

---

# ❓ « POURQUOI LA LIGNE 4 PHOTOS DANS UNE TÂCHE DOCUMENTS ? » — audit du 18/10

*Frédéric : « nous avons normalement déjà des run quotidiens pour les photos et celui de
22h n'aurait pas dû toucher aux photos, on a sûrement fait une erreur ».*

## La réponse : le placement est JUSTE, le NOM et la DÉCLARATION étaient faux

**⭐ IL Y A UNE RAISON TECHNIQUE, ET ELLE EST SOLIDE.** `accorder_photos_miroir` ne lit
**pas** Supabase : il compare **deux copies locales** — le **miroir Hektor**
*(`hektor.sqlite`, rafraîchi par le run vers **06:47**)* et **notre registre**
*(`phase2/phase2.sqlite`, rafraîchi par la **descente de 07:45**, `pull_from_supabase.py`)*.

| moment | miroir Hektor | notre copie |
|---|---|---|
| **05:00** *(le run)* | de la veille | de la veille |
| 07:45 | frais | **la descente la rafraîchit** |
| **22:00** *(l'entretien)* | **frais** | **frais** |

➡ **À 05:00 aucune des deux n'est à jour ; à 22:00 les deux le sont.** La ligne 4 est au
**seul endroit possible**. *(La note du ch. ⑥ l'avait déjà mesuré : « tant que la descente
n'a pas ramené la copie, il recalcule les mêmes 440 / 1 662 ».)*

## ⭐ ET LES CINQ ÉTAPES NE FONT PAS LA MÊME CHOSE

| quand | étape | elle |
|---|---|---|
| 05:00 | `rattrapage_photos` | **AJOUTE** — télécharge les nouvelles |
| 05:00 | `generer_derives_photos` | **AJOUTE** — fabrique les dérivés publics |
| 05:00 | `remplir_adresses_photos` | **AJOUTE** — pose nos adresses |
| 05:00 | `sonde_photos_manquantes` | **SURVEILLE** |
| **22:00** | **`accorder_photos_miroir`** | ⚠ **LE SEUL QUI RETIRE** — `present_in_hektor = false` |

➡ **Ce ne sont pas des doublons.** Mais **le seul dangereux est caché dans une tâche
appelée « Documents ».**

## ⛔ LES DEUX VRAIES FAUTES, ET ELLES SONT À MOI

**1. L'en-tête du script a menti pendant trois jours.** Écrit à **09:47** le 15/10 :
*« ⛔ DORMANT : aucune tache ne l'appelle »*. Branché à **12:35** le même jour
*(`87ff456`)*. **Le commentaire n'a pas suivi.** ⭐ Et il **m'a trompé moi-même** : le
17/10 j'ai affirmé à Frédéric que le script était dormant, avant de devoir me corriger.
**Corrigé le 18/10** — commentaire seul, `git diff` ne porte aucune ligne de code.

**2. La décision citée ne portait que TROIS lignes.** Le commit `87ff456` attribue à
Frédéric : *« on éteint le rattrapage, on allume la tâche de 22:00 », l'ordre étant
*« l'index des actifs le + important, ensuite estimation, ensuite vendu/clos »*. **La
quatrième ligne — les photos — n'est pas dans cette phrase.** Elle était dans la note
*(point 6d)*, mais **pas dans ce qu'on lui a fait dire**. ➡ *Une ligne ajoutée dans le
même geste qu'une décision n'est pas couverte par cette décision.*

## LE COÛT RÉEL DE CES DEUX FAUTES

La ligne 4 a marqué **440 photos** sa première nuit *(15/10, 23:23)* — **dont les 103
masquées**, à tort. La note du ch. ⑥ portait déjà le chiffre « 440 » et l'heure « 23:23 »
**sans voir que 103 d'entre elles n'étaient pas des supprimées.**

---

# ⚠⚠ L'ANGLE MORT DES MASQUÉES AVANT LA COUPURE — audit du 18/10

## 1. La commande qui les a ramenées : `sync_hektor_photos`

**Un seul chemin du projet lit les photos masquées** : le travail `sync_hektor_photos`,
qui appelle `fetchConsolePhotoEntries` *(`console_job_worker.js:4482`)* — **DEUX guichets**,
`mode=vignettes` *(visible: true)* et `mode=vignettes_hidden` *(visible: false)*.

**Qui le déclenche** : un **bouton à l'écran**, bien par bien *(`handleSyncPhotos`,
App.tsx:11684 → `createSyncHektorPhotosJob` → `app_console_create_sync_photos_job`)*.
**Jamais une tâche, jamais le run.** ➡ **313 travaux en tout, 304 annonces, le dernier le
17/08** — c'est le soir où les 103 sont entrées, entre 18:40 et 19:52.

## 2. Ce que le PLAN prévoit pour les photos — et ce qu'il ne prévoit pas

`PLAN_DEV_ACTUALISE`, ligne 91 *(25/09)* :
> ⛔ **LES PHOTOS NE SURVIVRONT PAS À LA COUPURE** *(mesuré)* — « trois pièces :
> **rapatrier ~125 Go** · le worker écrit sur le serveur d'abord · le chemin d'affichage ».

✅ **La pièce 1 est FAITE** : 172 Go rapatriés les 25-26/09, et le run entretient.

⛔⛔ **MAIS LE MOT « MASQUÉE » N'APPARAÎT NULLE PART** — ni dans le plan, ni dans la liste,
à propos des photos *(vérifié le 18/10 : toutes les occurrences parlent d'autre chose —
boutons masqués, défauts masqués)*. **Ce n'est pas une décision écrite : c'est un ANGLE
MORT.** Le rattrapage lit le miroir, le miroir vient de l'API, l'API ne donne que les
visibles — et personne n'a écrit ce que ça laissait dehors.

## 3. Le coût d'un rattrapage des masquées — chiffré

Il faut **1 appel Hektor par annonce** *(`vignettes_hidden`)*. Cadence sûre du projet :
**1 appel/seconde** *(`sonde_photos_manquantes`)*. Le bannissement du 20/08 est arrivé vers
**18 000 requêtes/nuit**.

| périmètre | annonces | appels | durée à 1/s | tient en une nuit ? |
|---|---|---|---|---|
| **les VIVANTES** | **10 259** | 10 259 | **≈ 2 h 51** | ✅ **oui**, loin sous le seuil |
| tout le parc à photos | 49 188 | 49 188 | ≈ 13 h 40 | ⛔ non — plusieurs nuits, avec plafond |

⭐ **Le téléchargement des fichiers, lui, est GRATUIT** : il passe par le **CDN public**,
hors quota Hektor *(0 refus sur 435 000 en septembre)*. **Seule la LECTURE de la liste
coûte.**

❓ **À TRANCHER PAR FRÉDÉRIC** : veut-on les masquées avant la coupure, et sur quel
périmètre ? *(Aujourd'hui : **0 masquée sur 10 biens vivants sondés en direct** — l'agence
ne semble pas s'en servir sur le parc actif.)*

---

## ⭐ LA FILIATION DE LA LIGNE 4 — Frédéric avait raison *(18/10)*

*« pourquoi il y a une ligne sur les photos dans le run de rattrapage document de 22h,
anciennement 21h ? »* — **Les deux générations précédentes n'y touchaient pas.**

| génération | fichier | ligne photos ? |
|---|---|---|
| **1. le rattrapage** *(21 h, désactivé le 15/10)* | `run_rattrapage_documents.ps1` *(existe encore)* | ⛔ **0 occurrence de « photo »** |
| **2. la détection** *(14/10, 22 h, dormante)* | `run_detection_documents.ps1` *(`9811a21`)* | ⛔ **0 occurrence** |
| **3. l'entretien** *(15/10 **12:35**, `87ff456`)* | `run_entretien_documents.ps1` | ✅ **la ligne 4/4 PHOTOS** |

➡ **La ligne photos est NÉE le 15/10 à 12:35**, dans le commit qui refondait la tâche en
quatre lignes — **3 heures après** que le script `accorder_photos_miroir.js` ait été écrit
« DORMANT » *(09:47, `75e6c37`)*.

### Les deux raisons — l'une écrite, l'autre seulement mesurée après coup

**Écrite dans le commit** : *« ⭐ LA LIGNE 4 empêche le retour des ~7 photos/jour ».*

**Mesurée le 18/10, jamais écrite à l'époque** : le script compare **deux copies
locales** — le miroir Hektor *(rafraîchi par le run vers 06:47)* et notre registre
*(`phase2.sqlite`, rafraîchi par la **descente de 07:45**)*. **À 05:00 aucune n'est à
jour ; à 22:00 les deux le sont.** C'est une vraie contrainte, et elle justifie l'heure.

### ⛔ CE QUI N'A PAS ÉTÉ FAIT, ET QUI EST LA FAUTE

1. **Elle n'a pas été soumise à Frédéric comme une décision à part.** Le commit lui
   attribue « actifs, puis estimation, puis vendu/clos » — **trois lignes de documents**.
2. **Elle a été logée dans une tâche « Documents »** au lieu d'avoir la sienne, alors
   qu'elle est **la seule des cinq étapes photos qui RETIRE**.
3. **L'en-tête du script a continué de dire « DORMANT »** pendant trois jours.

**Le coût : 103 photos rayées à tort dès la première nuit.**

### ❓ TROIS SORTIES POSSIBLES, À TRANCHER PAR FRÉDÉRIC

| | quoi | ce que ça coûte |
|---|---|---|
| **A** | **sortir la ligne 4** dans sa propre tâche « GTI Entretien **Photos** » *(22:30)* | une tâche Windows à enregistrer *(son geste)* + 1 nom au moniteur ; le détecteur d'échec ne mélange plus les deux objets |
| **B** | **renommer** la tâche « Documents **et Photos** » | 30 secondes, aucun code |
| **C** | **laisser** | rien — mais le nom reste un piège |

---

# ✅ « GTI ENTRETIEN PHOTOS » EST ENREGISTRÉE — 19/10/2026, 21:00

*Option A, choisie par Frédéric. La ligne 4/4 quitte la tâche Documents et prend son
nom, son journal et sa surveillance.*

## Les 9 réglages, comparés un par un à une sœur qui marche

| | la neuve | la sœur *(Entretien Documents)* |
|---|---|---|
| `LogonType` / `RunLevel` / `UserId` | **S4U / Limited / admin** | identiques |
| `Compatibility` / `MultipleInstances` | **Win7 / IgnoreNew** | identiques |
| `DisallowOnBatteries` / classe du déclencheur | **true / MSFT_TaskDailyTrigger** | identiques |
| **durée max** | **PT1H** | PT4H — *voulu : la tâche dure ~2 min* |
| **heure** | **21:00** | 22:00 — *voulu* |

**État : `Ready`**, prochain passage **19/10 21:00:00**, action sur le bon script.

## Et le moniteur la reconnaît

- le nom concorde **au caractère près** *(20 caractères)* entre Windows et le code ;
- présente dans **`TASK_CRITICALITY`** *(gravité **`warning`**)* **et** dans la liste ;
- ⭐ **les 10 tâches surveillées existent toutes dans Windows** — aucune « absente ».

## ⚠ CE QUI CHANGE DÈS CE SOIR

| | |
|---|---|
| **21:00** | la nouvelle tâche — **sa toute première nuit** |
| **22:00** | l'entretien documents, désormais à **3 lignes** — il ne touche plus aux photos |

## ⏰ LE CONTRÔLE DE DEMAIN MATIN — ce qu'il faut regarder

```
logs/scheduled/entretien_photos_2026-10-19_21-00-*.log
```
1. **le journal existe** — s'il est vide ou absent, la tâche n'a pas tourné ;
2. il porte **« --- 1/1 les PHOTOS »** — le marqueur prouve que le détecteur d'échec
   écrit bien au journal *(c'est le défaut des six fois)* ;
3. il finit par **« la ligne est passee »** et le résultat Windows vaut **0** ;
4. ⭐ **le nouveau compteur `sautees_masquee` apparaît** — il vaudra **0**, et c'est
   normal : aucune photo masquée-et-présente n'existe aujourd'hui ;
5. et le journal de **22:00** ne porte plus que **3 lignes**, sans photos.

⚠ **Si la tâche échoue, le moniteur le dira à l'écran Santé SANS e-mail** *(elle est en
`warning`)*. C'est voulu — la raison est écrite dans `check_gti_health.py`.

---

# ⚠⚠ LA SONDE TOURNE EN ROND — trouvé le 19/10 en chiffrant le rapatriement

`sonde_photos_manquantes.js` *(l. 1695 du run)* répond chaque nuit
**« ✅✅ Aucune photo manquante sur cet echantillon »** — **22 nuits de suite**, du 01/10
au 19/10. On pourrait croire à **550 annonces** sondées *(22 × 25)*.

⛔ **FAUX. C'est 25 annonces, lues 22 fois.**

Preuve : le journal imprime « la plus ancienne : … », et c'est **la même date —
`2025-10-24 15:08:55` — DIX NUITS DE SUITE** *(10/10 au 19/10)*.

**LA CAUSE** est dans son propre code : `lireLeMiroir()` fait
`ORDER BY COALESCE(s.date_maj,'') ASC LIMIT 400`, puis la boucle prend
`.slice(0, 25)`. Les 25 plus anciennement modifiées **ne changent pas** tant que leur
`date_maj` ne bouge pas — et par construction, **les plus anciennes sont justement
celles qui ne bougent jamais**.

⚠ Son en-tête l'explique et le justifie : *« Elle prend les annonces les PLUS
ANCIENNEMENT modifiees. C'est la que l'ecart se verrait »*. **Le raisonnement est juste
pour détecter un défaut de la DATE** *(est-ce qu'ajouter une photo fait bouger
`date_maj` ?)* — **mais il ne balaie pas le parc**. Et c'est pour ça qu'il ne dit RIEN
des photos masquées : il regarde **0,04 % du parc**, toujours le même.

⭐ **Famille connue** : *« un contrôle vert peut mesurer autre chose »*
*([[battement-cle-non-enregistree-part-dans-le-vide]])*. Le vert est **vrai**, et il ne
répond pas à la question qu'on croit lui poser.

➡ **Conséquence pour le rapatriement** : **nous n'avons AUCUN échantillon exploitable**
du taux de photos masquées sur le parc. Les seuls chiffres sont **304 annonces d'août**
*(dont 14 avec des masquées — 4,6 %, mais échantillon probablement biaisé)* et **10 biens
vivants sondés en direct — 0**.

---

# ⭐ OÙ SONT LES LIENS DES PHOTOS MASQUÉES — audit + test du 19/10

*Frédéric : « comment faire ? les liens photos sont accessibles où ? cherche dans mon
projet, on les a déjà trouvés à plusieurs reprises. Fais des tests si nécessaire. »*

## ✅ LE TEST, EN DIRECT SUR L'ANNONCE 32704 (19 masquées)

`?mode=vignettes_hidden&id=32704` rend **19 items**, et chacun porte **tout** :

```
id      : item_311060                                 <- le numero Hektor
src     : .../staticlbi.com/wx200/images/biens/11/... <- la VIGNETTE
srcHD   : .../staticlbi.com/wa/images/biens/11/...    <- la GRANDE IMAGE
delete_img('2e6de5af....jpg', 32704, '311060', ...)   <- le NOM DE FICHIER
visibiliteVignette( present                           <- la bascule est possible
```

➡ **UN SEUL appel Hektor par annonce suffit.** Le worker sait déjà tout en tirer :
`extractConsolePhotoEntries` rend `hektor_photo_id`, `url_preview`, `url_hd`,
`filename`, `legend`, `sort_order` **et** `actions.can_change_visibility`.

⚠ **ET LES ADRESSES NE SONT PAS DEVINABLES** : le chemin porte des hachés
*(`/images/biens/11/265d1769012cf77f8b7a602756031b24/...`)*. Pas de formule, pas de
raccourci — **il faut l'appel**.

## ⛔ LES DEUX IMPASSES VÉRIFIÉES

| piste | verdict |
|---|---|
| le miroir `images_json` | ⛔ **ne porte que les visibles** *(`visible` vaut `'1'` sur 17 535/17 535)* |
| `hektor_annonce_console_detail` *(miroir Console)* | ⛔ **aucune photo** — 168 lignes, et son payload ne porte que chauffage, diagnostics, DPE/GES, honoraires, pièces, secteur |

## ⭐⭐ ET LA COMMANDE DE BASCULE EST TROUVÉE — bien meilleure que les deux listes

Dans le JS de Hektor *(capture du 12/06)* :

```js
function visibiliteVignette(id, visible) {
  var data_url = 'mode=vignette_visibilite&id=' + id
               + '&idann=' + $j('#idannonceVignette').val()
               + '&visible=' + visible;
  $j.ajax({ type: "GET", url: "xmlrpc.php", data: data_url, ... });
}
```

➡ **`mode=vignette_visibilite&id=<photo>&idann=<annonce>&visible=<0|1>`** — **un GET,
UNE photo à la fois**. C'est **plus sûr** que `ordonne_photos`, qui exige de renvoyer
les DEUX listes entières *(et donc de risquer d'en emporter d'autres)*.
⭐ Et le worker la **détecte déjà** sur chaque photo : `can_change_visibility`.
⚠ **Jamais éprouvée en écriture** — c'est un GET, donc un relevé ne suffira pas à la
prouver : il faudra un vrai essai sur le bac à sable 62774.

---

# ⭐⭐ LE TAUX RÉEL DE PHOTOS MASQUÉES — mesuré le 19/10 sur 200 annonces

*Frédéric : « fais 1 mais sur 200 annonces ».*

```
200 annonces lues, AUCUN refus de Hektor
  3 annonces avec des masquees   ->  taux 1,5 %
  7 photos masquees au total     ->  2,3 par annonce concernee
  projection : ~732 annonces, ~1 709 photos sur les 48 820
```

**Les trois** : `59068` *(archive, 2)* · `62189` *(VIVANT, 3)* · `63005` *(VIVANT, 2)* —
et **0 masquée chez nous** pour les trois : ce sont des photos qu'on **n'a pas du tout**.

⭐ **LA RÉPARTITION COMPTE** : **2 sur 55 vivants = 3,6 %** · **1 sur 145 archives = 0,7 %**.
Les masquées sont surtout sur les biens **VIVANTS** — logique : on masque une photo d'un
bien qu'on commercialise.
⚠ **Petits nombres** : 3 sur 200 donne un intervalle large *(grossièrement 0,3 % à 4,3 %)*.
La projection n'est **pas** une mesure, et le compte rendu de la sonde le dit lui-même.

## ⚠ ET JE ME SUIS TROMPÉ SUR LE SEUIL DE BANNISSEMENT

J'ai cité plusieurs fois « ~18 000 requêtes/nuit ». **La mémoire ne dit pas ça.** Elle dit
*(incident du 19-20/08)* :
> « **DEUX causes, pas une** : ① **le débit** — ~3 requêtes par annonce à 1,3 s l'annonce =
> **2 à 3 req/s en continu pendant des heures** ; ② **les 403 répétés** — ~1 300 identiques
> depuis la même IP, déclencheur classique de fail2ban. »

➡ **Ce n'est pas le VOLUME, c'est le DÉBIT et les erreurs répétées.** À **1 appel/seconde**
on est **2 à 3 fois en dessous**, et la sonde du 19/10 a fait **200 appels sans un refus**.
⭐ *(Et le run fait déjà ~61 340 lectures de détail par nuit sans être banni — mais par
l'API, pas par la Console. La prudence reste due sur le canal Console.)*

## CE QUE ÇA CHANGE POUR LE RAPATRIEMENT

Le coût est **les appels**, pas le volume : **~1 709 photos à télécharger**, c'est
**trois fois rien** *(le CDN est gratuit et hors quota)*.

| option | quoi | nuits à 1 appel/s | ce qu'on récupère |
|---|---|---|---|
| **A** | **les VIVANTS d'abord** *(13 491)* | **~4 nuits** à 3 500/nuit *(58 min)* | ⭐ là où le taux est **3,6 %** — ~490 annonces, ~1 100 photos |
| **B** | **tout** *(48 820)* | ~14 nuits | tout |
| **C** | **en continu**, un curseur qui tourne en boucle dans « GTI Entretien Photos » | ~500/nuit, sans fin | tout, **sans aucune nuit lourde** |

⭐⭐ **RECOMMANDATION : A puis C.** Les vivants d'abord *(c'est là que ça compte et que le
taux est fort)*, puis le reste **en continu**. Et **C est AUSSI le « run de mise à jour »**
que Frédéric demande pour les prochaines : **un seul mécanisme fait les deux** — il
repasse indéfiniment et attrape les masquées nouvelles au passage suivant.


---

## ⑦-8 — « POURQUOI NE PAS FAIRE COMME LE RUN DES PHOTOS VISIBLES ? » *(question de Frédéric, 19/10)*

**Il a raison, et la réponse était déjà écrite dans le projet.** Ma proposition de la veille
*(balayer les 13 491 vivants chaque nuit, ou en cycle de 3 jours)* était **450 fois trop chère**.

### 1. Pourquoi le run des photos visibles ne coûte RIEN à Hektor

`Console/rattrapage_photos.js`, en tête du fichier, l'écrit en majuscules :

> ⚠⚠ **CE SCRIPT NE PARLE JAMAIS A HEKTOR.** Les adresses sont DEJA sur ce serveur, dans le
> miroir local (`data/hektor.sqlite`, `hektor_annonce_detail.images_json`). On lit en local,
> on telecharge sur le CDN public. -> AUCUNE requete contre le quota Hektor.

Et il descend à `--parallele 4`, `--intervalle 100` *(≈17 photos/s)*, parce que **staticlbi n'est
pas Hektor** : *« le 20/08 il repondait en 55 ms pendant que l'admin nous bannissait »*.

➡ **La liste des photos visibles arrive GRATUITEMENT, chaque nuit, dans le miroir** — c'est l'API
détail qui la porte. Le rattrapage n'est qu'une **lecture locale + un téléchargement CDN**.

### 2. Ce qui ne peut PAS être recopié : la DÉCOUVERTE

Le miroir ne porte **aucune** photo masquée *(l'API détail ne livre que les visibles — mesuré le
19/10 sur 32704 : `.images` = 12 alors que Hektor en a 19 masquées + 12 visibles, et **aucun
compte total** nulle part)*. Donc pour une masquée, **la liste ne peut pas venir du local** : il
faut un appel Console par annonce. ⭐ Mais une fois l'adresse connue, **le téléchargement
redevient gratuit** — même CDN, même cadence.

### 3. ⭐⭐ Ce qui PEUT être recopié : LE DÉCLENCHEUR — et la règle existe depuis le 26/09

`LISTE_TACHES_A_COCHER_2026-08-29.md:1437`, point **G.7** :

> *« Mesure qui, elle, tient : ajouter une photo dans Hektor FAIT BOUGER la date_maj de
> l'annonce -> **pas de balayage necessaire**. »*

**Mesures du 19/10 qui rendent ce déclencheur utilisable :**

| mesure | résultat |
|---|---|
| le signal est-il frais ? | ⭐ **61 431 lignes sur 61 431** de `hektor_annonce` portent `synced_at = 2026-10-19` — le run descend **tout l'index chaque nuit**, vivants **et** archives |
| combien d'annonces vivantes bougent par jour ? | **2, 3, 23, 25, 26, 29, 30, 34, 35, 41, 53, 96** sur les 19 derniers jours — **médiane ≈ 29** *(une pointe à 684 le 01/10)* |
| coût d'un run de MAJ piloté par `date_maj` | **≈ 30 appels/nuit = 30 secondes**, au lieu de 13 491 = 3 h 45 |

➡ **450 fois moins cher**, et c'est exactement le patron du run visible : **un signal local déjà
payé décide qui on va voir.**

### 4. ⚠ MAIS LE SIGNAL EST AVEUGLE AU PASSÉ — mesuré sur les 3 annonces trouvées la veille

| annonce | état | `date_maj` | le signal aurait parlé ? |
|---|---|---|---|
| **59068** *(2 masquées)* | **archivée** | **31/03/2026** | ⛔ non — 7 mois |
| **62189** *(3 masquées)* | vivante | 15/09/2026 | ⛔ non — 1 mois |
| **63005** *(2 masquées)* | vivante | 01/10/2026 | ✅ oui — 18 jours |

**1 sur 3.** Leurs photos masquées sont **antérieures** à tout mouvement récent : **aucune date ne
les révélera jamais.**

➡ **C'est la preuve des deux étages**, et non d'un seul :
- **① un balayage UNIQUE** — le seul moyen d'aller chercher les ~1 709 masquées **déjà là** ;
- **② un run de MAJ piloté par `date_maj`** — pour tout ce qui arrive **à partir de maintenant**.

### 5. ⚠⚠ L'AVERTISSEMENT DU PROJET, ÉCRIT DEUX FOIS — il vise mon balayage

`LISTE:1038` *(D.0-f)* **et** `LISTE:1318` :

> *« ⚠⚠ ET UN BALAYAGE DU PARC ENTIER COUTE 56 867 REQUETES = **4x LE SEUIL** (memoire) : la
> detection quotidienne doit rester PLAFONNEE. »*

Ce n'est pas un veto sur l'étage ①, mais **la condition** : plafond par nuit, curseur, cadence 1/s,
arrêt net au premier refus. **Un balayage sans plafond est précisément ce que cette ligne
interdit.**

### 6. ⛔ CE QUE JE NE SAIS PAS MESURER, et il faut le dire

G.7 a mesuré **AJOUTER** une photo. **MASQUER une photo déjà ancienne**, est-ce que ça bouge
`date_maj` ? **Non mesuré** — et le mesurer demande une **écriture chez Hektor** *(masquer une
photo sur le bac à sable 62774)*, donc ça appartient à la **pièce C** de ⑦-8, pas ici.

- Si **oui** → l'étage ② voit tout, l'étage ① ne sert qu'une fois.
- Si **non** → l'étage ② voit les **arrivées** *(une photo masquée est d'abord une photo
  **déposée**, et le dépôt, lui, bouge la date)* et **manque les masquages tardifs** → il faut
  alors **repasser l'étage ① périodiquement** sur le parc vivant seulement *(13 491 = 1 nuit)*.
  **Cadence = décision de Frédéric, pas la mienne.**


---

## ⑦-8 — AUDIT COMPLET DE LA FAMILLE « QUI PUBLIE UNE PHOTO ? » *(19/10, demandé par Frédéric)*

> *« il faut penser aussi aux vitrines Android, écran rapprochement, mes futurs envois pub
> etc... pour ne pas publier des photos masquées. »*

**Balayage de famille** *(leçon 9)* : je n'avais audité que la vitrine publique. Il y a
**neuf** surfaces, et **deux programmes de vitrine**, pas un.

### 1. LE POINT DE PASSAGE : comment une masquée entre dans un blob

`app_photos_remplir_adresses_app` *(patch du 27/09, l. 77-92)* :

```sql
-- la COUVERTURE
order by p.app_dossier_id, p.visible desc nulls last, p.sort_order asc nulls last, p.id
-- la GALERIE
jsonb_agg(...) order by p.visible desc nulls last, p.sort_order asc nulls last, p.id
where p.present_in_hektor and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
```

⭐⭐ **`visible desc` est un TRI, JAMAIS UN FILTRE** *(la règle que le projet connaît déjà)* :

- **la couverture** prend la **première** ligne → donc une visible **tant qu'il en existe une** ;
- **la galerie** `jsonb_agg` prend **TOUT** → les masquées y sont, **à la fin** ;
- ⭐ **et la vraie barrière d'aujourd'hui est la clause `where` : LES DÉRIVÉS.** Une photo
  masquée sans `w400`/`w1600` **n'entre nulle part**.

### 2. LA FAMILLE, MESURÉE — 7 objets en base, ni un de plus

Mesure *(`pg_get_viewdef` / `pg_get_functiondef` sur tout `public`)* :

| objet | porte |
|---|---|
| `app_photos_remplir_adresses_app` | **le fabricant** — galerie + couverture |
| `app_photos_remplir_adresses_registre` | le recopieur — galerie + couverture |
| `app_dossiers_current` *(vue)* | ⭐ **galerie + couverture** — c'est ELLE qui sert les surfaces publiques |
| `app_registre_mandats_current` *(vue)* | galerie + couverture *(interne)* |
| ⭐ **`app_get_rapprochements`** | **COUVERTURE SEULE** |
| `app_dossier_match_attrs` *(vue)* | **COUVERTURE SEULE** |
| `app_photos_placeholder_sans_photo` | **COUVERTURE SEULE** |

### 3. LES NEUF SURFACES, une ligne par surface

| surface | reçoit | filtre `visible` ? | une masquée peut-elle sortir ? |
|---|---|---|---|
| **vitrine Android publique** `Ecrans Android/export_project_vitrine.py:167` | **galerie `_app`**, demandée explicitement | ⚠ **écrit mais INERTE** *(la clé manque au blob)* | ⚠ **OUI** → **pièce A** |
| **espace client** *(page sécurisée du vendeur)* `espace_client.py:88` → vue `app_dossiers_current` | **galerie `_app`** *(la vue coalesce)* | ⛔ **AUCUN**, et il **RE-TRIE par `order`** | ⚠⚠ **OUI, et en PREMIER** → **pièce B** |
| **portail de rapprochement** *(envoyé par e-mail à l'acquéreur)* `espace_portal` ← `espace_client._photos` l. 476 | **la même galerie**, 8 photos | ⛔ **AUCUN** *(même code)* | ⚠⚠ **OUI** → **pièce B** |
| ⭐ **écran Rapprochement** `app_get_rapprochements` | **couverture seule** | le tri `visible desc` | ✅ **non** — sauf annonce 100 % masquée |
| **attributs de rapprochement** `app_dossier_match_attrs` | couverture seule | idem | ✅ idem |
| **e-mails de rapprochement** `rapprochement_email.py:214` | `photo_url_listing` *(couverture)* | idem | ✅ idem |
| **RDV publics** `appointment_service.py:194,282` | `photo_url_listing` *(couverture)* | idem | ✅ idem |
| **app front** *(cockpit, fiches, vignettes, registre)* | galerie `_app` | aucun | ⭐ **VOULU** : le négociateur DOIT voir ses masquées |
| ⭐ **ancienne vitrine** `Ecrans Android/vitrine6.py:477` | Hektor `modes = ["vignettes"]  # PUBLIC only` | — | ✅✅ **sûre par construction** — elle ne lit jamais `vignettes_hidden` |
| **portails / diffusion pub** | — | — | ✅ **aucun code photo** *(grep vide sous `backend/app/services/`)* ; gelée depuis juillet |

### 4. L'ÉTAT D'AUJOURD'HUI, mesuré en production *(19/10, lecture seule)*

| mesure | valeur |
|---|---|
| photos masquées, total | **103** |
| dont présentes chez Hektor *(réparées le 19/10)* | **103** |
| dont avec `w400` → **entrent dans la couverture** | ⭐ **0** |
| dont avec `w400`+`w1600` → **entrent dans la galerie** | ⭐ **0** |
| annonces concernées | 14 |
| dont **vivantes** | ⭐ **0** |
| annonces où **TOUTES** les photos sont masquées *(le trou du tri)* | ⭐ **0** |

➡ ✅ **ZÉRO FUITE AUJOURD'HUI.** ⚠ **Mais par accident, pas par conception** : les 103 n'ont pas
de dérivés et vivent sur des archives. **Rien dans le code ne l'empêche.**

### 5. ⭐⭐ LA PIÈCE QUE JE N'AVAIS PAS VUE — un seul endroit protège TOUT

`Console/generer_derives_photos.js` **n'a aucun filtre sur `visible`** *(mesuré : 0 occurrence)*
et il sert **les annonces vivantes** *(`app_dossier_current`)*. **C'est lui qui ouvre la vanne.**

➡ **Ne pas fabriquer de dérivé pour une photo masquée** protège **d'un seul geste** :
la vitrine publique, l'espace client, le portail de rapprochement, **et toutes les surfaces
publiques pas encore écrites** — ses futurs envois pub comprises. C'est la **barrière amont**,
là où les pièces A et B sont deux barrières aval à poser surface par surface.

⭐ **Et ça ne cache rien au négociateur** : `prefererNosPhotos` *(api.ts:7980)* fait
`if (!notreApercu && !notreGrande) return photo` → **une photo sans dérivé garde l'adresse
Hektor et s'affiche quand même** dans le panneau photos.

### 6. ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS — la question de la coupure

Sans dérivé, une photo masquée est visible **tant que Hektor vit**. **Le jour de la coupure,
elle devient une image morte dans l'app** *(l'original est sur notre serveur — le coffre privé —
mais l'app ne sait afficher que les dérivés ou Hektor)*.

- ⭐ **Le mécanisme de secours existe** : règle **G.8**, *« un dérivé retiré → REGÉNÉRABLE à la
  demande (comme "Préparer") »*.
- ⛔ **Mais ce n'est pas à moi d'en décider** : fabriquer les dérivés d'une masquée et les
  filtrer partout, ou ne pas les fabriquer et les regénérer au besoin, **c'est un arbitrage de
  Frédéric**. Les deux chemins sont tenables ; ils ne coûtent pas la même chose.

### 7. Ce que je n'ai PAS pu mesurer

- **Masquer** une photo ancienne bouge-t-il `date_maj` ? → écriture chez Hektor, **pièce C**.
- **Personne n'a vu l'écran** du panneau photos avec une masquée dedans *(0 annonce vivante en
  porte une aujourd'hui)*.


---

## ⭐⭐⭐ ⑦-8 — « MAIS ON PEUT PAS FAIRE DEUX BOÎTES ? » *(Frédéric, 19/10)* — SA SOLUTION EST LA BONNE

**Et la deuxième boîte EXISTE DÉJÀ.** Mes options A et B étaient toutes les deux moins bonnes.

| la boîte | contient | qui la lit |
|---|---|---|
| **la boîte PUBLIQUE** = `images_preview_json_app` | ⚠ aujourd'hui **TOUT**, masquées comprises | la vitrine Android · l'espace client · le portail de rapprochement · la galerie de la fiche |
| **la boîte COMPLÈTE** = la table `app_console_photo` | **tout**, avec le drapeau `visible` | ⭐ **le panneau photos** *(`loadConsolePhotos`, api.ts:7991 — il lit la TABLE, jamais la boîte)* — là où vivra le bouton masquer/afficher |

➡ **Il n'y a pas de deuxième boîte à construire. Il y a UNE boîte à nettoyer.**

### Le geste : une condition, dans UNE fonction

`app_photos_remplir_adresses_app`, aux **deux** endroits de cette même fonction *(la couverture
`tmp_principale` et la galerie `tmp_galerie`)* : ajouter `and p.visible is not false` au `where`
qui exige déjà les dérivés.

⚠ **Et `is not false`, pas `not visible`** : un `NULL` doit rester **visible** — c'est la règle
que le projet porte déjà *(`coalesce(img->>'visible','1')`)*. On recopie, on n'invente pas.

### Ce que ça règle d'un seul coup

| surface | code à écrire |
|---|---|
| vitrine Android publique | ✅ **zéro ligne** |
| espace client | ✅ **zéro ligne** |
| portail de rapprochement | ✅ **zéro ligne** |
| ⭐⭐ **les futurs envois pub** | ✅ **protégés pour toujours** — une page qui ouvre la boîte publique **ne PEUT PAS** y trouver une masquée |
| la couverture | ✅ **structurellement** impossible à masquer *(le trou « annonce 100 % masquée » se ferme)* |

⭐ **Et les dérivés continuent d'être fabriqués** → le bouton « afficher » de la pièce C reste
**instantané**. C'est l'avantage de l'option B, **gardé**.

⭐⭐ **LA PIÈCE A ET LA PIÈCE B DEVIENNENT INUTILES.** Plus de clé à poser, plus de filtre à
recopier surface par surface, **plus de sentinelle à écrire** : la discipline est remplacée par
une impossibilité.

### Ce que ça change à l'écran — à dire, pas à cacher

- La **galerie de la fiche annonce** *(App.tsx:18699-18706)* ne montrerait plus que les visibles.
  ⭐ **C'est juste** : elle montre ce que le public voit. Le **panneau photos** — le vrai outil de
  travail — montre tout, puisqu'il lit la table.
- ⭐⭐ **C'est exactement le dessin de Hektor lui-même** : deux galeries, `mode=vignettes` et
  `mode=vignettes_hidden`. On ne copie pas une idée nouvelle, on copie la sienne.
- Une annonce dont **toutes** les photos sont masquées afficherait « Sans photo ».
  **C'est juste aussi** — et **0 annonce** est dans ce cas aujourd'hui *(mesuré)*.

### ⚠ Le seul prix, dit clairement

Le dérivé d'une photo masquée serait dans le coffre **public** : **listé nulle part**, mais
ouvrable par quelqu'un qui connaîtrait l'adresse exacte. ⭐ C'est déjà le cas de **toutes** nos
photos *(le coffre est public par conception — règle G.8)*. Pour que ce ne soit PAS le cas, il
faudrait ne pas les redimensionner — et le bouton « afficher » redeviendrait lent.
**Arbitrage de Frédéric.**

### ⚠ LE CONTRÔLE QUI A FAILLI ME TROMPER — la règle des jumeaux

Mesure : **deux** fonctions font un `jsonb_agg` sur `app_console_photo`. J'ai cru à un jumeau.
Vérifié avant de conclure : `app_console_photo_couverture_optimistic` fabrique **l'état d'avant**
pour le retour arrière, et **n'écrit PAS** dans la boîte *(`images_preview_json_app` : **0**
occurrence ; `photo_url_listing_app` : **0**)*. ⭐ Mieux : **elle exige déjà que la photo choisie
comme couverture soit VISIBLE** — une garde qui existait, non cherchée.

➡ **`app_photos_remplir_adresses_app` est le SEUL fabricant de la boîte.** Une fonction, un patch.


---

## ⑦-8 — SECOND AUDIT : CÔTÉ **ÉCRITURES**, ET LE RATTRAPAGE *(19/10, « refais un audit pour être sûr »)*

Le premier audit a mesuré **qui lit** la boîte. Celui-ci mesure **qui écrit** — le drapeau, la
boîte, et ce que le rattrapage va y verser.

### 1. QUI ÉCRIT LA BOÎTE ? — **une seule fonction, et un seul appelant**

| mesure | résultat |
|---|---|
| code *(JS / Python / PS1)* qui écrit `images_preview_json_app` ou `photo_url_listing_app` | ⭐ **AUCUN** — la vitrine ne fait que les **lire** |
| fonctions en base qui les écrivent | `app_photos_remplir_adresses_app` *(le fabricant)* + `app_photos_remplir_adresses_registre` *(il RECOPIE)* |
| qui appelle le fabricant | ⭐ **un seul** : `Console/remplir_adresses_photos.js:65`, étape du run |
| le jumeau soupçonné `app_console_photo_couverture_optimistic` | ✅ **innocent** — son `jsonb_agg` fabrique **l'état d'avant** du retour arrière ; il écrit la boîte **0 fois**, et ⭐ **il exige déjà une cible VISIBLE** |

➡ **Une fonction à toucher. Pas de jumeau.** *(Vérifié, pas supposé — la règle des jumeaux.)*

### 2. QUI ÉCRIT LE DRAPEAU `visible` ? — et peut-il être écrasé ?

⭐⭐ **Le drapeau n'est jamais DEVINÉ : il est passé par l'appelant.**
`extractConsolePhotoEntries(html, visible)` → `visible: Boolean(visible)` *(worker l. 1298)*.

| chemin d'écriture | ce qu'il pose | sûr ? |
|---|---|---|
| **le worker** `sync_hektor_photos` *(l. 4486-4518)* | lit **LES DEUX** galeries : `mode=vignettes` → `visible: true` · `mode=vignettes_hidden` → `visible: false` | ✅ **juste** |
| **le rattrapage** `rattrapage_photos.js:172` | `!["0","false","non"].includes(String(e.visible)...)` — avec un booléen `false`, `String(false)` = `"false"` → **dans la liste** → `visible: false` | ✅ **juste** ⚠ mais `undefined` → **visible** : l'entrée DOIT porter le drapeau |
| ⭐⭐ **`accorder_photos_miroir.js`** | **RIEN.** En-tête l. 88 : *« ON NE TOUCHE PAS AU DRAPEAU `visible` »* ; `visible_divergent` *(l. 303)* n'est **qu'un compteur** | ✅✅ **aucun écrasement possible** |

➡ **Le miroir — qui ne connaît que les visibles — ne peut PAS « corriger » une masquée en
visible.** C'était le risque le plus grave ; il est fermé **par une décision déjà prise le 15/10**.

### 3. ⭐⭐ ET LE PROJET AVAIT DÉJÀ ÉCRIT LA SOLUTION

`accorder_photos_miroir.js`, en-tête l. 92-96 :

> ⭐ **ET LE RESTE SE CORRIGE TOUT SEUL.** `patch_photos_adresses_app_2026-09-27.sql` recalcule
> `photo_url_listing_app` et `images_preview_json_app` […] Donc la vignette du listing, celle du
> registre des mandats et **LA GALERIE DU SITE PUBLIC redeviennent justes au passage suivant du
> run, sans toucher une ligne de front.**

**C'est exactement le dessin des deux boîtes.** Corriger le fabricant, et les trois surfaces
publiques se remettent d'aplomb **seules**, au run suivant.

### 4. LE RATTRAPAGE — ce qu'il doit faire, et dans quel ORDRE

| | |
|---|---|
| lire `mode=vignettes_hidden` et appeler l'extracteur avec **`false`** | ✅ prouvé : le drapeau vient de l'appelant |
| les dérivés seront fabriqués *(pas de filtre dans `generer_derives_photos.js`)* | ⭐ **voulu** dans ce dessin : le bouton « afficher » reste instantané |
| la boîte sera reconstruite | ✅ le fabricant re-cible une annonce dès qu'une de ses photos bouge *(`m.dernier > adresses_app_le`)* — donc **chaque annonce balayée** passe par le filtre |

⚠⚠ **DONC L'ORDRE EST IMPOSÉ : LA CONDITION D'ABORD, LE BALAYAGE ENSUITE.** Sinon les boîtes
construites pendant le balayage porteraient des masquées, et rien ne garantirait leur
reconstruction.

⭐ **Et il n'y a rien à nettoyer derrière** : mesure du 19/10, **0** masquée a un dérivé, donc
**aucune boîte n'en contient une aujourd'hui**.

### 5. VERDICT

**La condition unique tient sur TOUS les chemins mesurés.** Un seul fabricant, un seul appelant,
aucune écriture directe du code, aucun écrasement du drapeau possible, et la reconstruction
est automatique. ⚠ **Reste non mesuré** : si **masquer** une photo ancienne bouge `date_maj`
*(écriture Hektor → pièce C)*.


---

## ⚠⚠⚠ ⑦-8 — AUDIT DU BANNISSEMENT : LE BALAYAGE QUE J'AI PROPOSÉ ÉTAIT DANGEREUX *(19/10)*

> *« J'ai peur de l'IP ban sur le run de balayage proposé, peut-être des pauses non ? audit un
> peu mon historique à ce sujet. »* — **Frédéric avait raison sur les deux points.**

### 1. MON ERREUR, ET C'EST LA DEUXIÈME FOIS

J'ai calculé **sur le TEMPS libre de la nuit** *(3 h 42 → 13 300 appels à 1/s)*. **Le mur n'est
pas le temps.** La mémoire du projet le dit mot pour mot, et elle dit aussi que **j'avais déjà
fait cette erreur** :

> **MESURE DÉCISIVE (20/08/2026) : c'est un quota de VOLUME, pas de débit.**
> ```
> blocage 1   5 572 annonces   ~16 700 requêtes   sur 5 h 06   à 1,5 req/s
> blocage 3   4 540 annonces   ~13 600 requêtes   sur 6 h 30   à 0,6 req/s
> ```
> Même ordre de grandeur **malgré un débit divisé par deux**. **« Ralentir ne fait que retarder
> l'échéance »** — vérifié à nos dépens. ➡ **Seuil estimé : 13 000 à 17 000 requêtes par période.**

> *« CE QUE J'AVAIS OUBLIÉ DE CETTE NOTE : le chiffre qui compte n'est pas les "61 h de
> traitement" que j'ai calculés, mais **le nombre de requêtes par nuit**. »* *(25/09)*

➡ **Mon balayage à 10 000 appels/nuit était à la limite du seuil À LUI SEUL.**

### 2. L'HISTORIQUE : QUATRE BLOCAGES, TROIS MÉCANISMES DIFFÉRENTS

| date | cause | signature |
|---|---|---|
| **19-20/08** | **volume cumulé** *(3 blocages)* — et des **403 répétés** *(68 annonces × 19 lots ≈ 1 300 refus identiques)* | plus aucune réponse TCP sur **tout le cluster** ; le CDN répondait en 55 ms depuis la **même IP** |
| **26/08** | ⚠ **MES PROPRES SONDES D'AUDIT** — 300 contacts à 0,25 s *(4× le débit que le projet s'impose)*, des boucles par agence… | identique ; Frédéric a débloqué |
| **17/09** | **une rafale de LOGINS** — un client reconstruit en boucle = **17 logins OAuth en 22 s**, bloqué au 16ᵉ | *« un login est la requête la plus chère qui soit pour un pare-feu »* |
| **18/09** | **relire des objets SUPPRIMÉS** — des 404/403 rejoués chaque nuit | coupé par `VERIFIER_CHEZ_HEKTOR=False` |

⭐ **Et la phrase qui vise exactement mon plan** *(worker, l. 3069-3072)* :

> *« Le frein du 20/08 avait corrigé le DÉBIT ; il restait **LA DURÉE D'EXPOSITION**, qui est
> précisément ce que son propre en-tête désignait comme la cause du blocage du 19/08. »*
> *« Le blocage du 19/08 est survenu après **QUATRE HEURES de flux ininterrompu à ~1,5 req/s,
> sans la moindre erreur**. »*

⚠⚠ **Mon plan : 3 h 42 de flux ininterrompu à 1/s. C'est LA FORME EXACTE du blocage du 19/08.**

### 3. ⭐⭐ IL A RAISON : LES PAUSES EXISTENT — ET ELLES NE SONT PAS DANS MA SONDE

Les règles du projet, **en code** *(`console_job_worker.js:3069-3112`)* :

```
 1 000 ms  intervalle minimum entre deux appels     HEKTOR_MIN_REQUEST_INTERVAL_MS
    60 s   de respiration tous les 100 appels       HEKTOR_PAUSE_EVERY_N_REQUESTS
   300 s   de pause de vague tous les 2 000         HEKTOR_WAVE_EVERY_N_REQUESTS
    15 s   de recul après un 503/429/timeout        HEKTOR_BACKOFF_AFTER_REJECT_MS
```
*(« La méthode de référence travaille par lots de 100 suivis de 60 s, soit **45 %** de charge. »)*

**Mesure, script par script :**

| script | intervalle | pause/100 | vague/2 000 |
|---|---|---|---|
| `console_job_worker.js` | ✅ | ✅ | ✅ |
| `enqueue_console_sync_jobs.js` | ✅ | ✅ | ✅ |
| `sonde_photos_manquantes.js` | ⚠ 1 s codé à la main | ⛔ **non** | ⛔ **non** |
| ⚠⚠ **`sonde_taux_photos_masquees.js`** *(la mienne, 19/10)* | 1 s à la main | ⛔ **non** | ⛔ **non** |
| `rattrapage_photos.js` | — | — | ⭐ **normal** : il parle au **CDN**, pas à Hektor *(réglages séparés, 150 ms / 500)* |

➡ **Ma sonde est moins protégée que le worker.** Elle n'a tourné que sur 200 annonces, donc sans
dommage — mais **le balayage, bâti sur elle, aurait tourné 10 000 fois.**

### 4. LE BUDGET RÉEL DE LA NUIT, MESURÉ *(19/10)*

| ce qui consomme | requêtes Hektor |
|---|---|
| **« GTI Entretien Documents » (22:00)** — journal du 18/10 : *« 800 lectures, cap 300 »* + *« 2 000 lectures, cap 100 »* + *« 2 000 lectures, cap 300 »* | ⚠ **jusqu'à 4 800 lectures** + jusqu'à ~2 100 pour les synchronisations des 700 qui bougent ➡ **~6 900** |
| **le run de 05:00** | ⭐ **léger aujourd'hui** — il est incrémental *(`Pages=0`, « 1 page »)* et **0 trace de frein** dans son journal, donc jamais 100 appels d'affilée |
| les 4 workers en journée | variable, non mesuré |

**Le seuil est 13 000–17 000. La règle de Frédéric du 20/08 : rester 40 % en dessous.**

➡ ⚠⚠ **La marge réelle pour un balayage est de ~2 000 à 3 000 appels par nuit. PAS 10 000.**

### 5. LE PLAN CORRIGÉ

| | avant *(faux)* | **après** |
|---|---|---|
| appels/nuit | 10 000 | ⭐ **1 500 les 3 premières nuits, puis 2 500** |
| freins | 1 s seulement | ⭐ **les 4 freins du projet**, repris du worker, **pas réécrits** |
| forme | 3 h 42 de flux continu | ⭐ **45 % de charge** : 100 appels → 60 s, 2 000 → 300 s |
| périmètre | 48 820 d'un coup | ⭐ **les vivants d'abord** *(3,6 % de masquées contre 0,7 % aux archives)* |
| durée | « 5 nuits » | **~7 nuits pour les vivants**, les archives ensuite **sur décision** |
| en plus | — | ⭐ **un compteur de requêtes journalisé**, pour qu'on SACHE où on est |

⭐⭐ **ET LA PRUDENCE DE FRÉDÉRIC DU 20/08, CONSEILLÉE ET JAMAIS APPLIQUÉE, LE SERA CETTE FOIS** :
*« 2 000/jour les 3 premiers jours, le temps de vérifier si leur compteur se réinitialise par
journée civile ou glisse sur 24-48 h. »* La mémoire note : **« n'a PAS été appliquée »**.

### 6. ⚠ Ce que je ne sais pas mesurer

- **La période exacte du quota** *(journée civile ? 24 h glissantes ?)* — inconnue depuis le 20/08.
- **Le débit acceptable selon Ma Boîte Immo** : la note dit *« à demander »*, **jamais demandé**.
- **Ce que les 4 workers consomment en journée.**

➡ **Donc le budget ci-dessus est une estimation prudente, pas une mesure.** C'est une raison de
plus de commencer à 1 500 et de regarder.


---

## ✅ ⑦-8 MARCHE 1 — ÉCRITE ET DORMANTE *(19/10, go « oui vas y »)*

**Trois fichiers** : `supabase/patch_chantier7_8_deux_boites_2026-10-19.sql` + `_INVERSE` +
`_REPETITION`. ⛔ **Rien n'est collé** — ma session ne peut pas écrire en production.

### L'état de départ, mesuré dans la BASE *(pas dans le fichier)*

| mesure | valeur |
|---|---|
| empreinte de `app_photos_remplir_adresses_app` *(sans CR)* | **`682e386007b59eda6e5dc54056c87693`** |
| retours chariot dans le corps stocké | ⭐ **0** |
| taille | 4 826 |
| déjà patchée ? | **non** |
| signature | `(p_heures integer default 48, p_tout boolean default false)` |
| plancher interne | refuse si `app_dossier_current < 5000` → on en a **13 491**, il ne mordra pas |

### ⭐ L'ANCRE : une seule, et elle corrige LES DEUX `where`

```
where p.present_in_hektor and p.derives_json
   ->  where p.present_in_hektor and p.visible is not false and p.derives_json
```

Elle apparaît **exactement 2 fois** *(ligne 50 = la COUVERTURE, ligne 62 = la GALERIE)*, donc
**un seul remplacement les traite toutes les deux**, et le patch **vérifie le compte = 2** avant
d'écrire — si une 3ᵉ apparaissait un jour, il **refuse**.

### ⭐⭐ ÉPREUVE DU TRANSPORT — la leçon 30, prouvée en lecture seule

Je ne peux pas jouer la répétition *(écriture en production, même annulée)*, mais le mécanisme
du piège se prouve sans rien écrire. Simulation de l'arrivée en CRLF, **des deux côtés** :

| cas | l'ancre est trouvée |
|---|---|
| retours chariot **dans** mon ancre | ⭐ **0** → elle est **sur une seule ligne** |
| LF / LF | **2 fois** |
| CRLF / LF | **2 fois** |
| CRLF / CRLF | **2 fois** |
| guéri *(chr(13) retiré des deux côtés — ce que fait le patch)* | **2 fois** |

➡ **Les quatre cas donnent 2.** Une ancre **sans retour chariot dedans** est **immunisée** : le
CRLF n'a rien à corrompre. C'est la première fois que ce piège est **structurellement** écarté
plutôt que contourné.

**Contrôles des fichiers** : 2 / 2 / 4 littéraux protégés par `replace(…, chr(13), '')`,
⭐ **0 multi-ligne**, 0 `\gset`, et la répétition a **1 `begin;`, 0 `commit;`, 1 `rollback;`**.
Types vérifiés en base : `id` = **uuid**, `visible` = **boolean**, `derives_json` = jsonb.

### ⚠⚠ DEUX PIÈGES TROUVÉS EN ÉCRIVANT L'ÉPREUVE

1. **Les tables temporaires de la fonction sont `on commit drop`.** La répétition l'appelle
   **deux fois** dans une transaction jamais validée → le second appel aurait échoué sur
   *« relation tmp_maj already exists »*. ➡ `drop table if exists tmp_maj, tmp_cibles,
   tmp_principale, tmp_galerie;` **entre les deux passages**.
2. ⭐ **`now()` est FIGÉ dans une transaction** *(leçon 28)*. Après le 1ᵉʳ appel,
   `adresses_app_le = now()`, donc le test `m.dernier > d.adresses_app_le` serait **faux**
   (égal, pas supérieur) et l'annonce **ne serait pas re-ciblée**. ➡ on remet
   `adresses_app_le = null` avant le 2ᵉ passage.

### CE QUE LA RÉPÉTITION PROUVE — elle FABRIQUE le cas

⚠ **Il fallait le faire** : **0** masquée a un dérivé aujourd'hui, donc une épreuve naïve serait
**verte avant comme après** et ne prouverait rien *(« un contrôle vert peut mesurer autre
chose »)*. Elle prend donc **deux annonces vivantes** et leur fabrique le cas :

- **annonce A** : une photo **masquée** *(avec ses dérivés)* + une photo à **`visible` NULL** ;
- **annonce B** : **toutes** ses photos masquées → le trou « annonce 100 % masquée ».

| étape | ce qui est exigé |
|---|---|
| **2-témoin** *(sans le patch)* | A : la masquée **EST** dans la boîte · B : sa couverture **EST** une masquée — ⭐ **si le témoin ne montre pas le défaut, l'épreuve se déclare non concluante** |
| **3-après** | A : la masquée **n'y est plus** · ⭐ la photo à **NULL y est toujours** *(un NULL reste visible — la règle du projet, sinon le patch serait trop strict)* · A : la couverture est une **visible** · B : couverture **et** galerie **VIDES** · ⭐ **le panneau photos voit toujours tout** *(on reproduit son filtre exact : `present_in_hektor` seul)* |
| **4-retour** | l'empreinte revient à `682e3860…`, **0 trace** de la condition |

### ⛔ RESTE

**Frédéric colle la répétition**, puis le patch. ➡ Ensuite : **marche 2** *(le balayage, au profil
corrigé : 1 500/nuit, les 4 freins du worker, les vivants d'abord)*.


### ⚠ ⑦-8 MARCHE 1 — LA RÉPÉTITION A ÉCHOUÉ AU COLLAGE, ET C'ÉTAIT MON ÉPREUVE QUI AVAIT TORT

**Frédéric colle, et la base refuse :**
`ERROR: 23502: null value in column "visible" of relation "app_console_photo" violates not-null
constraint`

**Ce que j'avais manqué** : j'avais vérifié le **TYPE** de la colonne *(`boolean`)* et **pas sa
NULLABILITÉ**. Mesure après l'échec :

| mesure | valeur |
|---|---|
| `app_console_photo.visible` | ⭐ **NOT NULL, défaut `true`** |
| photos à `visible` NULL en base | **0** sur 441 363 |
| les 4 autres colonnes que la répétition écrit | ✅ **toutes nullables** — `visible` était la seule |
| ⭐ **empreinte de la fonction après l'échec** | **`682e386007b59eda6e5dc54056c87693`** — **INCHANGÉE : rien n'avait été écrit** |

➡ **Le patch n'a pas bougé d'une ligne.** La branche « un NULL reste visible » que mon épreuve
voulait prouver **ne peut pas exister** : la contrainte l'interdit. La forme `visible is not false`
reste la bonne — elle est **défensive** *(elle tiendrait si la contrainte sautait)* et elle recopie
la règle du projet. **C'est l'épreuve qui avait tort, pas le code** *(3ᵉ fois ce motif ; déjà payé
le 15/10 sur `test_masquee_pas_supprimee.js` et sur `test_porte_contacts`)*.

**Version 2 de la répétition** : la photo à NULL est remplacée par une **photo TÉMOIN qui reste
VISIBLE** — et c'est un **meilleur** contrôle, parce que sans elle **un patch qui viderait TOUT
serait vert**. Et le cas du NULL est **déclaré impossible**, mesuré depuis le catalogue, plutôt
qu'oublié.

**Contrôles mécaniques de la v2** : 0 `visible = null` · 0 `\gset` · 1 `begin;` / 0 `commit;` /
1 `rollback;` · 4 ancres protégées, **0 multi-ligne** · 2 effacements des tables temporaires ·
2 appels au fabricant · 16 lignes de mesure.

⭐ **Et la leçon à retenir, plus large que ce patch** : *avant d'écrire une épreuve qui FABRIQUE
un cas, vérifier que la base ACCEPTE ce cas* — `information_schema.columns` donne le type **et**
`is_nullable`, et je ne lisais que le premier.


### ✅✅ RÉPÉTITION v2 COLLÉE — **16 MESURES, 16 VERTES** *(19/10)*

```
1-avant  | empreinte de depart              = 682e386007b59eda6e5dc54056c87693
1-avant  | l ancre apparait                 = 2 fois
1-avant  | masquees AVEC derive en prod      = 0  (d ou la fabrication)
1-avant  | annonce A choisie / photos        = 118 / 20
1-avant  | annonce B choisie / photos        = 311 / 2
2-temoin | A : la masquee EST dans la boite  = OUI -- c est bien le defaut qu on corrige
2-temoin | B : sa couverture EST une masquee = OUI -- c est bien le trou « 100 % masquee »
3-apres  | A : la masquee est dans la boite  = NON -- le filtre mord
3-apres  | A : la photo VISIBLE y est encore = OUI -- le patch n est PAS trop strict
3-apres  | le cas « visible NULL » possible  = NON (NOT NULL, defaut true) -> DEFENSIF
3-apres  | A : sa couverture est VISIBLE     = OUI
3-apres  | A : photos dans la boite          = 19 (il y en avait 20, une est masquee)
3-apres  | B : couverture et galerie         = VIDES -- 0 % publiable, le trou est ferme
3-apres  | le panneau photos voit tout       = 20 photos dont 1 masquee -- OUI, il les voit
4-retour | empreinte revenue                 = oui, a l octet pres
4-retour | aucune trace de la condition      = oui
```

⭐⭐ **CE QUE CES LIGNES PROUVENT, ET QUI NE SE DEVINAIT PAS :**

1. **Le défaut existait vraiment.** Sans le patch, la masquée **EST** dans la boîte publique de
   l'annonce 118, et la couverture de l'annonce 311 **EST** une masquée. ➡ **Les deux témoins
   inverses ont montré le défaut** — sans eux, « le filtre mord » n'aurait rien voulu dire.
2. ⭐ **Le trou « annonce 100 % masquée » était réel** : l'annonce 311 n'a que 2 photos, les deux
   masquées → avant le patch elle publiait une masquée en couverture, après elle n'a **ni
   couverture ni galerie**. 0 annonce est dans ce cas en production *aujourd'hui*, mais le trou
   est désormais **fermé par construction**.
3. ⭐ **L'arithmétique est exacte** : 20 photos → **19** dans la boîte, une seule retirée.
4. ⭐⭐ **Le négociateur ne perd rien** : « le panneau photos voit tout = **20 photos dont 1
   masquée** ». La boîte publique est filtrée, **la boîte complète ne l'est pas** — c'est
   exactement le dessin des deux boîtes de Frédéric.
5. **Le patch n'est pas trop strict** : la photo témoin restée visible est **toujours** dans la
   boîte. Sans ce contrôle, un patch qui aurait vidé TOUT serait passé pour vert.
6. **Le retour arrière retombe à l'octet près**, 0 trace.

### ⚠ CE QU'IL FAUT SAVOIR POUR LE CONTRÔLE D'APRÈS

⚠ **Rien ne changera visiblement ce soir.** Mesure : **0** masquée a un dérivé en production,
donc **aucune boîte n'en contient une**. Ce patch est un **verrou préventif** — il mord le jour
où le balayage (marche 2) ramènera des masquées sur des biens vivants.

⚠ **Ne PAS rejouer la répétition après avoir collé le patch** : son bloc patch dirait
« DEJA FAIT » et sauterait, donc ses mesures « 2-temoin » n'auraient plus de sens. Le contrôle
d'après est une **lecture** : la condition apparaît 2 fois, l'empreinte a changé, et 0 masquée
n'est dans une boîte.


### ✅✅✅ MARCHE 1 **EN PRODUCTION** — contrôle du 19/10, **7 contrôles verts**

Frédéric a collé le patch. Mesure en lecture seule, **on vérifie, on ne croit pas** :

| contrôle | résultat |
|---|---|
| a. la condition est posée | **2 fois** *(la couverture ET la galerie)* |
| b. ancre nue oubliée | **0** |
| c. empreinte | `682e386007b59eda6e5dc54056c87693` → **`b87f6c6827fbedf0c8d8e8709d62a334`** |
| d. ⭐ **retours chariot injectés par le collage** | **0** — le transport a tenu *(leçon 30)* |
| e. masquées présentes dans une boîte publique | **0** |
| f. masquées avec un dérivé *(la vanne)* | **0** |
| g. ⭐ le panneau photos voit toujours les masquées | **103** — le négociateur ne perd rien |

### ⭐ ET LA QUESTION DE FRÉDÉRIC QUI A FAIT LA DIFFÉRENCE : « mais le patch a pas changé »

Il avait raison de la poser. Le patch n'a **pas** changé entre la v1 et la v2 de l'épreuve — **mais
encore fallait-il prouver que l'épreuve avait bien joué LE patch, et pas une imitation.** Mesure,
ligne par ligne :

| les 5 lignes QUI AGISSENT | patch | épreuve |
|---|---|---|
| `v_ancre text := replace('where p.present_in_hektor and p.derives_json', chr(13), '')` | 1 | 1 |
| `v_neuf  text := replace('…visible is not false…', chr(13), '')` | 1 | 1 |
| `v_emp   constant text := '682e3860…'` | 1 | 1 |
| `v_new := replace(v_src, v_ancre, v_neuf);` | 1 | 1 |
| `execute v_new;` | 1 | 1 |

➡ **Identiques.** Les seules divergences du diff sont **la mise en forme** *(une ligne contre
plusieurs)*, **le libellé des refus**, et **3 contrôles d'APRÈS-ÉCRITURE que le patch a en plus**
*(relecture en base, ancre nue résiduelle, les `raise notice`)*. ⭐ Ceux-là ne peuvent que
**refuser** — et un refus annule la transaction, donc l'écriture est défaite : **le mode d'échec
est sûr**. C'est la règle « éprouver LE code, pas une doublure » appliquée au patch lui-même.

### ⛔ CE QUI RESTE DE ⑦-8

| | |
|---|---|
| **marche 2 — le balayage** | au profil **corrigé** : **1 500/nuit** les 3 premières nuits puis 2 500, **les 4 freins du worker**, **les vivants d'abord** · ⛔ **le lancer = accord de Frédéric** |
| **marche 3 — le run de MAJ** | piloté par `date_maj`, ~30 appels/nuit, greffé sur « GTI Entretien Photos » (21:00) |
| **marche 4 — le bouton masquer/afficher** | `mode=vignette_visibilite`, **jamais prouvé en écriture** · son essai sur le bac à sable **62774** répond AUSSI à la question laissée ouverte *(masquer bouge-t-il `date_maj` ?)* |

⚠ **Rien ne changera visiblement** tant que la marche 2 n'a pas tourné : **0** masquée a un
dérivé aujourd'hui. Ce verrou est **préventif**, et c'est voulu — il devait précéder le balayage.


---

## ✅✅✅ ⑦-8 MARCHE 2 — L'ESSAI RÉEL EST VERT, ET IL PROUVE TOUT *(19/10, 09:47)*

**Décision de Frédéric : option A — 2 000 annonces/nuit, 7 nuits, on ne touche PAS au run de 22 h.**
Puis : *« fais le toi même »* → ⛔ impossible *(garde-fou de session sur les écritures prod)*, donc
j'ai réduit sa part à **une seule ligne** et relevé l'état d'avant moi-même.

### LA PRÉDICTION, ÉCRITE AVANT L'ESSAI

> `hidden = 3` · `visible = 4` · `total = 7` · 7 lignes dont 3 à `visible = false` ·
> **la boîte publique reste à 4, PAS 7**

### LE COMPTE RENDU DU BRAS — chaque chiffre est celui prédit

```
status             photos_synced
total              7      <- prédit 7
visible            4      <- prédit 4
hidden             3      <- ⭐⭐ PRÉDIT 3
photos_downloaded  3      <- les 3 masquées sont sur le serveur (2,7 Mo)
photos_unchanged   4      <- ⭐ les 4 visibles N'ONT PAS été retéléchargées
photos_failed      0
```

⭐ **`photos_unchanged: 4` prouve que le téléchargement est bien INCRÉMENTAL** — c'est la réponse,
en réel, à la question de Frédéric « des empreintes pour ne pas tout retélécharger » : **c'est déjà
le cas, et le fichier lui-même est l'empreinte.**

### LES 8 CONTRÔLES EN BASE

| contrôle | résultat |
|---|---|
| a. photos chez nous | **4 → 7** |
| b. dont **masquées** | **0 → 3** |
| c. marquées absentes *(dégât collatéral)* | ⭐ **0** |
| d. les 4 visibles intactes | **4** |
| e. masquées **avec un dérivé** | **3** — le worker les fabrique aussitôt |
| f. la boîte publique | **4** |
| g. le panneau photos du négociateur | **7 photos dont 3 masquées** |
| h. fichier sur le serveur | **3 sur 3** |

### ⭐⭐⭐ ET LE TÉMOIN INVERSE SUR DONNÉES RÉELLES — LA PREUVE DU DESSIN

⚠ « la boîte est à 4 » ne prouvait **rien** par soi-même : elle pouvait être à 4 simplement parce
qu'elle **n'avait pas encore été recalculée** *(leçon « un contrôle vert peut mesurer autre
chose »)*. J'ai donc rejoué **les deux versions du calcul à la main**, en lecture seule :

```
ANCIENNE regle (sans le verrou)  ->  7 photos dont 3 MASQUEES
NOUVELLE regle (avec le verrou)  ->  4 photos dont 0 MASQUEE
la COUVERTURE choisie            ->  une visible (sort_order 1)
l annonce est-elle RE-CIBLEE ?   ->  OUI, sa boite sera refaite CETTE NUIT
```

➡ ⚠⚠ **SANS LE VERROU COLLÉ CE MATIN, CES 3 PHOTOS MASQUÉES PARTAIENT CE SOIR** sur la vitrine
Android, l'espace client et le portail de rapprochement. **La marche 1 a précédé la marche 2 de
quelques heures, et c'était la bonne décision.**

⭐ Et les lignes **e + f ensemble** prouvent le dessin des deux boîtes : les 3 masquées **ont déjà
leurs dérivés** *(donc dans le coffre public, prêtes à s'afficher instantanément si on les
démasque — l'avantage de l'option B de Frédéric)*, **et pourtant la galerie publique les exclut.**

### CE QUE L'ESSAI A ÉTABLI, ET QUI N'ÉTAIT PAS ACQUIS

1. ⭐⭐ **Le bras ramène bien les masquées.** Les 314 travaux existants portaient **tous**
   `hidden: 0` — ce chemin n'avait **jamais** été vu en ramener une. C'est fait, c'est mesuré.
2. **Aucun dégât collatéral** : 0 photo marquée absente, les 4 visibles intactes.
3. **Un seul service le prend** : `NS31851120:documents:service:v9` — donc **un seul frein**.
4. **Durée mesurée : ~30 s pour une annonce** *(2 appels Hektor + 3 téléchargements)*.
5. **Coût : 2 requêtes Hektor.**

### ⛔ RESTE POUR LA MARCHE 2 — et maintenant on peut l'écrire

| | |
|---|---|
| **l'empileur** | il choisit 2 000 annonces/nuit et pose les travaux — **copié sur `enqueue_empreinte_lot.js`** et ses 3 exclusions *(déjà faite · en erreur → NE JAMAIS REJOUER · déjà en file)* |
| **la tâche Windows** | à 00:00, fenêtre jusqu'à 02:30 |
| **le calibrage** | **1 200 les 2 premières nuits** *(la prudence du 20/08, jamais appliquée)* |
| ⛔ **le lancer** | **accord de Frédéric**, à part |


---

## ✅ ⑦-8 MARCHE 2 — ÉCRITE ET ÉPROUVÉE, PAS ENCORE ENREGISTRÉE *(19/10, go « DONC ? »)*

**Trois fichiers neufs, deux fichiers élargis. Rien n'est enregistré dans Windows, rien ne tourne.**

### CE QUI A ÉTÉ ÉCRIT

| fichier | quoi |
|---|---|
| `Console/enqueue_photos_masquees_lot.js` | **l'empileur** — il pose des travaux, ⚠ **il ne parle JAMAIS à Hektor** |
| `scheduled/run_balayage_photos_masquees.ps1` | **la tâche** (00:00), `Invoke-Ligne` recopiée **à l'octet près** |
| `scheduled/test_detecteur_echec_entretien.ps1` | ⭐ **élargi** — voir ci-dessous |
| `monitoring/check_gti_health.py` | la tâche **déclarée AVANT** d'être enregistrée, en **`critical`** |

### ⭐⭐ LE DESSIN, ET CE QUI L'A IMPOSÉ

**Pourquoi passer par le worker et pas écrire un script à nous** *(question de Frédéric :
« on se sert des workers dans le balayage ? »)* : un script séparé aurait **son propre frein**,
et les deux s'additionneraient — *« un frein ne protège QU'À L'INTÉRIEUR d'un client »*, la cause
du bannissement du 17/09. Mesure du 19/10 : `sync_hektor_photos` n'est réclamé que par
`worker_kind = 'documents'` ➡ **un seul processus, un seul frein.**

**Un seul lot, deux parts** *(question : « on fait les deux en même temps ? »)*. Deux tâches
séparées se bloqueraient : la part MAJ poserait ~29 travaux, puis le balayage verrait « la file
n'est pas vide » et **refuserait son lot entier**. Donc un lot, rempli dans cet ordre :
**① les annonces dont la date a bougé · ② les jamais visitées**. ⭐⭐ **Et quand le balayage sera
fini, le lot tombera tout seul à ~29/nuit et DEVIENDRA le run de mise à jour** — pas
d'interrupteur, pas de 2ᵉ tâche.

**1 000 et pas 2 000** — ⚠ **la contrainte a changé de nature en cours de route.** Je calculais
sur le quota Hektor ; la vraie borne est **le temps de digestion du worker** : médiane **10 s**
par travail sur les 315 réels *(moyenne 12 s, max 79 s)* ➡ 2 h 30 de creux = **~868 annonces**,
3 h 42 = **~1 285**. Un lot de 2 000 aurait pris **5,8 à 6,6 h** et débordé sur les recherches de
03:00 puis le run de 05:00.

**Les vivantes seules** — décision du 19/10, **déclarée** dans `HORS_AUTO` : une archive n'est
publiée **nulle part** *(la vitrine filtre `archive=0` et statut Actif/Sous offre/Sous compromis)*,
son taux de masquées est **0,7 % contre 3,6 %**, et les **44 277** archives + historiques
coûteraient **44 nuits pour ~700 photos**. `--scope archive` reste ouvert **à la main**.
⚠ Déclarer était obligatoire : sans ça l'alarme « périmètre oublié » sortirait en code 1 chaque nuit.

### ⚠⚠ L'ÉPREUVE DU DÉTECTEUR NOMMAIT SA JUMELLE EN DUR — élargie

Le contrôle ④ ajouté le 19/10 comparait `Invoke-Ligne` à **une** jumelle nommée en dur
*(`run_entretien_photos.ps1`)*. ➡ **Ma 3ᵉ tâche lui aurait échappé EN SILENCE** — exactement le
trou que ce contrôle est censé boucher. Il **balaie maintenant le dossier** : toute tâche de
`scheduled\` portant `Invoke-Ligne` est comparée, qu'elle existe aujourd'hui ou qu'on l'écrive
demain. **C'est la règle du balayage de famille appliquée à l'épreuve elle-même.**

**Résultat : 13 contrôles verts**, dont *« 2 autres tâches porteuses trouvées »* et les deux
comparaisons **325 caractères contre 325**.

### LES DEUX REFUS, ET POURQUOI ILS SORTENT EN 1

| code | quoi | pourquoi il doit SONNER |
|---|---|---|
| **3** | la file n'est pas vide | ⭐ **c'est la garde qui régule la taille toute seule.** Sans e-mail, le balayage s'arrêterait en silence et les 14 nuits n'arriveraient **jamais** — c'est le défaut mesuré le 14/10 sur le rattrapage documents : *« UN SEUL TRAVAIL posé, et il sortait EN SUCCÈS »* |
| **4** | ≥ 10 erreurs en 24 h | Hektor nous rejette — la signature du 20/08. *« Un 403 arrête tout, on ne rejoue jamais. »* |

⭐ **Et la fenêtre de pose** : la tâche **refuse de poser passé 01:00**. On borne le **départ** —
un lot posé à 02:00 ferait travailler le worker jusqu'à 05:00 et au-delà.

### L'ESSAI À BLANC — tous les chiffres se recoupent

```
annonces du perimetre      13 491      le parc vivant
deja visitees                 305      (surtout des archives, d aout)
part MISE A JOUR                3      deja vues ET leur date a bouge
part BALAYAGE              13 487
lot pose                    1 000      dont 3 de MAJ, 997 de balayage
ecartees pour erreur            0
sans date au miroir             0      le miroir couvre tout le parc
requetes Hektor attendues   2 000
nuits restantes                14
exemples : 24113, 62853, 63157, puis 102, 104, 108...
```

⭐ **L'ordre est le bon** : les 3 modifiées **en tête**, puis les jamais vues. Et **62189, visitée
ce matin, est correctement exclue** — c'est la 4ᵉ vivante déjà vue, celle dont la date n'a pas bougé.

### ⭐ LES DEUX PIÈGES ANTICIPÉS, PAS DÉCOUVERTS

1. **La date de Hektor est LOCALE, celle des travaux en UTC** *(piège payé le 13/10 : « deux
   heures d'erreur, l'inverse de la vérité »)*. ➡ **Marge de 3 h, dans le sens SÛR** : revisiter
   pour rien coûte 2 requêtes, en manquer une perd des photos pour toujours.
2. **L'exclusion pour erreur est COMPTÉE ET NOMMÉE**, pas silencieuse. Le projet a payé deux fois
   l'exclusion définitive muette *(les 527 brouillons, les 33 annonces bloquées par le coffre)*.
   On ne les rejoue pas tout seul — **mais on les VOIT** dans le compte rendu.

### ⛔ RESTE À FRÉDÉRIC

| | |
|---|---|
| **enregistrer la tâche Windows** | à 00:00, quotidienne · ⚠ **comparer réglage par réglage** à une sœur qui marche *(S4U / Limited / Win7 / moteur unifié / limite 4 h / IgnoreNew)* — la leçon du 15/10, où la tâche neuve était en « Interactive », **seule des 9** |
| **le calibrage** | ⭐ **`-Limite 1200` les 2 premières nuits** puis 1 000 en régime *(ou plus si le worker va plus vite que les 10 s médianes — la 1ʳᵉ nuit le dira)* |
| ⛔ **le premier lancement** | **accord à part** |


### ⚠⚠ L'INSTALLEUR NE PASSAIT PAS LE PARSEUR — UN PIÈGE D'ENCODAGE *(19/10)*

`scheduled/installer_tache_balayage_photos.ps1` : *« Accolade fermante } manquante **ligne 121** »*
— alors que l'accolade de la 121 était parfaitement fermée. **Le parseur signale où le bloc
COMMENCE, pas où est la faute.** Trouvé en balayant **ligne par ligne isolément** :

```
⛔  =  U+26D4  =  UTF-8  E2 9B 94
lu en cp1252  ->  â (E2)   › (9B)   ” (94)
```

⚠⚠ **PowerShell traite `”` comme un guillemet délimiteur.** Donc
`Write-Host "⛔ $($rouges.Count) reglage(s)..."` se terminait **au milieu**.

⭐ **Inoffensif en COMMENTAIRE, FATAL dans une CHAÎNE** — c'est pourquoi `run_entretien_photos.ps1`
vit très bien avec ses `⛔` : ils sont dans des `#`.

**Mesure du parc** : sur les **21** `.ps1` de `scheduled/`, **4 seulement ont un BOM**. Les autres
n'ont jamais cassé **par chance**. ➡ **BOM UTF-8 ajouté aux deux fichiers neufs** : ça supprime
toute la classe du problème, et les `⚠`/`⭐` s'afficheront juste dans le journal.
⭐ Et le BOM **ne change pas les octets d'une fonction interne** : l'épreuve qui compare
`Invoke-Ligne` à l'octet près reste verte, **325 caractères contre 325**.

### ✅ LES DEUX ÉPREUVES APRÈS CORRECTION

| | |
|---|---|
| `test_detecteur_echec_entretien.ps1` | **13 verts**, dont les 2 comparaisons 325 = 325 |
| ⭐ **la tâche de bout en bout** *(`-DryRun -IgnorerFenetre`)* | **code 0**, le marqueur `--- 1/1 l'EMPILEUR` au journal, le bilan complet, et *« la ligne est passee »* |

➡ **Ce n'est plus seulement l'empileur qui est éprouvé : c'est la TÂCHE, telle que Windows la
lancera.** *(Leçon du 03/10 : « l'épreuve de la veille testait une imitation, pas le vrai code ».)*

### L'INSTALLEUR, ET CE QU'IL VÉRIFIE LUI-MÊME

`scheduled/installer_tache_balayage_photos.ps1` — à lancer **en PowerShell administrateur**.
⭐ Il recopie les réglages de **« GTI Entretien Documents »** *(relevés le 19/10 : admin / S4U /
Limited / Win7 / moteur unifié / IgnoreNew / StartWhenAvailable False / MSFT_TaskDailyTrigger
interval 1)*, puis **il relit la tâche enregistrée et compare RÉGLAGE PAR RÉGLAGE** — **13 lignes
nommées**, une par réglage, jamais un « 13 sur 13 ».
⭐⭐ **C'est la leçon du 15/10 transformée en code** : les deux défauts de cette nuit-là *(principal
« Interactive », limite à 72 h)* **sortiraient en ROUGE ici**. « Enregistrée » ne veut pas dire
« configurée comme ses sœurs ».
⚠ Seule divergence **voulue et vérifiée comme telle** : `ExecutionTimeLimit = PT1H` et non PT4H —
l'empileur sort en moins d'une minute.

⚠ **Correction de mon propre plan** : j'avais écrit *« 1 200 les 2 premières nuits puis 1 000 »* —
**c'était à l'envers**, un calibrage part EN DESSOUS de la cible. ➡ La tâche tourne au **défaut de
1 000**, et ⭐ **le calibrage est automatique** : si le worker ne digère pas son lot, la nuit
suivante le refus « file non vide » sort en 1 et le dit. Pas de rampe à la main.


---

## ⑦-8 — « IL Y A UNE LIMITE DE 12 PHOTOS ? » *(question de Frédéric, 19/10)* — **c'est 5, et elle ne mord plus**

**Sa mémoire était juste sur le fond, fausse sur le chiffre et sur l'endroit.**

### LA LIMITE EXISTE : `MAX_EXPORTED_IMAGES = 5`

`phase2/sync/export_app_payload.py:32`, appliquée par `trim_json_array_field` *(l. 2917-2921)* à
**`images_json`** ET **`images_preview_json`** du **payload de détail**.

⚠ Le « 12 » qu'il avait en tête est probablement la mesure que je lui ai montrée le 19/10 :
`.images` = **12** pour l'annonce 32704 — c'était son **nombre de visibles chez Hektor**, pas une
limite.

### ⭐⭐ MAIS IL Y A TROIS CHEMINS DE PHOTOS, ET UN SEUL EST TRONQUÉ

| chemin | limite | mesure du 19/10 |
|---|---|---|
| **la table `app_console_photo`** → `loadConsolePhotos` *(le PANNEAU PHOTOS)* | ⭐ **`.limit(500)`** | annonce 118 : **20** · 62189 : **7** · 63005 : **14** |
| **notre boîte `images_preview_json_app`** *(la galerie de la fiche, la vitrine…)* | ⭐ **AUCUNE** | 118 : **20** · 63005 : **14** |
| ⚠ **le payload de détail** `app_dossier_detail_current` | ⛔ **5** | 118 : **5** · 63005 : **5** |

### ⭐⭐⭐ ET ELLE NE MORD PLUS — mesuré, pas supposé

L'app lit **notre boîte** quand elle existe *(`api.ts` substitue `images_preview_json_app` dans
`images_preview_json` via `galerieAppEnTexte`)*, et elle ne retombe sur le payload que si notre
boîte est absente.

| mesure | valeur |
|---|---|
| vivantes **sans** notre boîte *(donc qui retomberaient sur 5)* | **3 236** sur 13 491 |
| ⭐ **dont ZÉRO photo chez nous** | **3 236 sur 3 236** |
| **annonces vraiment tronquées** *(sans boîte ET plus de 5 photos)* | ⭐⭐ **0** |

➡ **Les 3 236 n'ont aucune photo** — la limite de 5 ne leur enlève rien. *(C'est exactement ce que
disait déjà le commentaire d'`App.tsx:18694` : « les 3 222 qui n'ont pas notre galerie sont
EXACTEMENT celles qui n'ont aucune photo », mesure du 27/09.)*

### ⭐ POUR LE BOUTON MASQUER/AFFICHER (pièce C) : AUCUNE LIMITE

Le panneau photos — là où vivra le bouton — lit **la table**, avec `.limit(500)`. **Il voit tout**,
visibles et masquées. ⚠ Et c'est déjà **prouvé en réel** : après l'essai du 19/10, le panneau de
l'annonce 62189 voit **7 photos dont 3 masquées**, alors que sa boîte publique n'en porte que 4.

### ⚠ LE PIÈGE LATENT, NOTÉ ET NON TRAITÉ

La limite de 5 **est toujours là, dormante**. Si notre boîte disparaissait un jour pour une annonce
**qui a des photos**, l'app n'en montrerait **que 5, en silence**. Aujourd'hui : **0 annonce dans
ce cas**. ➡ **Noté, pas corrigé** — ce n'est pas le chantier en cours, et le remède serait de
monter `MAX_EXPORTED_IMAGES` ou de retirer la troncature du payload *(décision de Frédéric)*.


---

## ✅ ⑦-8 — LA TACHE EST ENREGISTREE, ET LE CONTROLE DE DEMAIN EST ECRIT *(19/10)*

### L'ENREGISTREMENT : 13 REGLAGES VERTS

Frédéric a lancé l'installeur. **Vérifié de mon côté, pas cru** :

| | |
|---|---|
| état | **Ready** |
| prochaine passe | ⭐ **20/10/2026 00:00:00** |
| dernier résultat | **267011** = « jamais lancée » — l'un des `ACCEPTABLE_TASK_RESULTS`, **le moniteur ne criera pas** |
| script appelé | le bon |
| les 11 tâches surveillées | toutes **Ready**, sauf « Rattrapage Documents » **Disabled** *(voulu)* |

**Et la file est libre pour cette nuit** *(sinon le refus « file non vide » serait sorti en 1 pour
rien)* : **0** travail `sync_hektor_photos` en attente · **0** erreur sur 24 h · **0** travail
**tous types confondus** · le service `documents` bat depuis **27 s**.

### LE CONTROLE DE DEMAIN : `phase2/checks/controle_balayage_photos_masquees.py`

Écrit **la veille**, pour que le contrôle du lendemain **ne dépende d'aucune conversation**.
Huit points, sortie 0/1/2, et la **référence du 19/10 figée dedans** *(106 masquées sur
15 annonces · 3 avec un dérivé · **0 dans une boîte** · 13 490 à faire · 305 visitées)*.

⭐ **Les deux points qui portent tout :**
- **④ le rythme réel** — c'est lui qui dira si on peut monter au-dessus de 1 000 ;
- **⑦⭐⭐ le verrou** — **zéro masquée dans une boîte publique**. ⚠ Et s'il **ne peut pas** mesurer,
  il sort **ROUGE par prudence**, pas vert.

### ⭐ TEMOIN INVERSE JOUE LE SOIR MEME — 5 oranges, 0 rouge

Joué **avant** la nuit, il doit crier ; sinon un vert demain ne prouverait rien.
```
🟠 la tache n'a pas encore tourne (resultat 267011)
🟠 1 travaux poses au lieu de ~1000
🟠 rythme NON CONCLUANT : 1 travail mesure, il en faut 20
🟠 aucune masquee ramenee
🟠 le curseur n'a pas avance
✅ les marqueurs du journal · 0 erreur · 0 refus Hektor · LE VERROU TIENT
```

### ⚠⚠ ET LE TEMOIN INVERSE A TROUVE UN DEFAUT DANS MON PROPRE CONTROLE

Sa 1ʳᵉ version conseillait **« baisser le plafond à 114 »** — calculé sur **UN SEUL travail**,
celui de l'essai du matin, qui était **le plus lent des 315** *(78,9 s : il téléchargeait 3 photos
et fabriquait leurs dérivés)*. **Un verdict sur un échantillon de 1 n'est pas un verdict.**

➡ Corrigé : **minimum 20 travaux mesurés**, sinon il écrit *« rythme NON CONCLUANT […] Aucun
conseil de plafond »*. ⭐ C'est la règle *« quand on ne peut pas savoir, on dit non concluant, on
ne crie pas »* — et c'est **l'épreuve qui a trouvé le défaut, pas la relecture.**

➡ Le rappel est aussi posé dans **`CLAUDE.md` §2**, item **⓿**, pour qu'il survive à la fin de
cette conversation.


---

## 🔧 ⑦-8 MARCHE 4 — LE BOUTON MASQUER / AFFICHER : LES 4 PIÈCES SONT ÉCRITES *(19/10)*

**Go de Frédéric** : *« Oui »*, puis *« audit sérieusement il faut être sûr »*, puis *« est-tu sûr
de toi cette fois »*. ⛔ **Rien n'est actif** : aucun patch collé, les 4 services tournent sur
l'ancienne version du worker, le front n'est pas poussé.

### ⭐⭐⭐ LA COMMANDE EST PROUVÉE PAR LE CODE DE HEKTOR LUI-MÊME

`Console/exports/extract_contact_search_2026-06-12…/js/labs_Header.js`, **l. 6816** :

```javascript
function visibiliteVignette(id, visible) {
    var data_url = 'mode=vignette_visibilite&id=' + id
                   + '&idann=' + $j('#idannonceVignette').val() + '&visible=' + visible;
    $j.ajax({ type: "GET", url: "xmlrpc.php", data: data_url,
              success: function () { vignettes(); vignettes_hidden(); } });
}
```

**Trois choses qu'on ne devinait pas :** ⭐ **une photo à la fois** *(l'autre route,
`mode=ordonne_photos`, réécrit les DEUX listes entières — écartée)* · **aucune cascade serveur**
*(le rappel ne rafraîchit que l'affichage)* · ⭐⭐ **et Hektor nous dit comment finir : il RELIT
SES DEUX GALERIES.**

### LE SENS DE LA VIE DU GESTE — la règle de Frédéric

> *« il faut d'abord écrire chez nous, ensuite envoyer l'information à Hektor, et sinon il y a le
> run quotidien pour l'autre sens »*

⭐⭐ **Et l'autre sens est DÉJÀ écrit** : c'est le balayage de la marche 2. Si un négociateur
masque une photo **directement dans Hektor**, le lot de la nuit le voit. **La boucle est complète,
et il n'en manquait qu'un quart.**

### ⭐⭐ « CHEZ NOUS » A DEUX ÉTAGES — le point de conception

| « chez nous » | qui le lit | à jour en |
|---|---|---|
| la **table** `app_console_photo` | le **panneau photos** | **immédiat** |
| la **boîte** `images_preview_json_app` | vitrine · espace client · portail | ⚠ sinon : **le lendemain** |

⛔ **Ce qu'on ne fait PAS** : recopier le calcul de la boîte *(il vit dans
`app_photos_remplir_adresses_app`, et « deux copies divergeraient au premier ajustement »)*.
✅ **Ce qu'on fait** : la RPC remet `adresses_app_le` **à blanc sur les 4 index** — l'annonce
redevient une **cible** du fabricant — et le **worker réveille le fabricant** juste après son
appel Hektor. ➡ **Une seule copie de la règle, et la boîte est juste en quelques SECONDES.**
⭐ Le « post-it » n'est pas une invention : `adresses_app_le IS NULL` est **exactement la première
condition de ciblage du fabricant**.
⚠ **La vitrine Android, elle, est un export statique poussé par le run** : rien ne la changera
avant la nuit. **Dit, pas caché** — et écrit dans l'infobulle du bouton.

### ⚠⚠⚠ CE QUE L'AUDIT SÉRIEUX A TROUVÉ : PERSONNE NE REMETTRAIT NOTRE DRAPEAU

Vérifié sur **trois** chemins :

| | |
|---|---|
| l'« Abandonner » du bandeau | ne touche que `app_annonce_champ_app` — ⛔ `app_console_photo` **n'y apparaît pas** |
| le `base_snapshot` du geste **couverture** | ⛔ **personne ne le lit** — *« exprès pour ça »* veut dire **préparé**, pas fait |
| un retour arrière générique | ⛔ **il n'en existe aucun** *(la l. 18432 est un garde-fou de recherche contact)* |

➡ **Donc le geste se défait LUI-MÊME dans le worker** : une colonne, une ligne, et la charge porte
`etat_avant`. ⚠ Si la remise échoue, **il le dit et il jette quand même** — *un drapeau faux qui
se croit juste est pire qu'une erreur visible*.
📌 **NOTÉ, PAS TRAITÉ** : le geste **couverture** du 16/10 a **le même trou**.

### ⚠ ET ON N'ACCEPTE JAMAIS LE 200 COMME PREUVE

Le handler frère l'écrit : *« un 200 vide est la signature d'un refus »*, et la mémoire le paie
depuis l'affaire des offres *(78 % refusées en silence)*. ➡ Le handler **relit les deux galeries et
EXIGE que le drapeau ait basculé** — ⭐ ce qui est exactement ce que fait Hektor. **Une action,
deux usages : la preuve ET l'état.**
⭐ Et il vérifie que Hektor **PROPOSE le bouton** : `source_json.actions.can_change_visibility`,
relevé par l'extracteur **depuis mai**.

### LES 4 PIÈCES

| pièce | fichier | contrôle |
|---|---|---|
| **1 — la base** | `supabase/patch_chantier7_8_marche4_visibilite_2026-10-19.sql` *(+ INVERSE)* | les 3 ancres **uniques**, sur une ligne ; les 4 index ont bien `adresses_app_le` |
| **2 — le worker** | `Console/console_job_worker.js`, **les 5 endroits** *(128 · 8733 · 18183 · 18215 · 21475)* | ✅ **`node --check` passe** |
| **3 — l'écran** | `api.ts` · `App.tsx` *(refus, handler, bouton)* · `styles.css` *(3ᵉ créneau, `right: 72px`)* | ✅ **build vert**, et ⭐ **témoin inverse** : `TS2322` avec une faute volontaire, vert sans elle |
| **4 — la répétition** | `supabase/…_REPETITION.sql`, ⭐ **GÉNÉRÉE** par `supabase/generer_repetition_marche4.py` | voir ci-dessous |

### ⭐⭐⭐ LA RÉPÉTITION EST GÉNÉRÉE, PAS RECOPIÉE

J'allais recopier **190 lignes** de patch à la main dans la répétition — **c'est exactement là
qu'on introduit une divergence invisible**, et on éprouve alors **une imitation**
*(avertissement du 03/10)*. ➡ Un générateur **extrait le patch verbatim** et **le vérifie** :

```
corps extrait  11 838 caracteres   empreinte f393d40dba5308294fee13b6c50d64bd
LE CORPS EXTRAIT EST-IL DANS LA REPETITION, A L'OCTET PRES ?  OUI
la RPC complete y est : True   ·   1 begin / 1 rollback / 0 commit
ancres protegees : 9   ·   multi-lignes : 0
```

**Ce qu'elle prouve** : les 3 verrous posés · la RPC existe et `anon` **ne** peut pas l'appeler
*(la leçon du 08/10 : Supabase pose un GRANT à `authenticated` sur toute fonction neuve)* · le
masquage écrit le drapeau, **pose le post-it**, met `adresses_app_le` **à blanc** et crée **un
travail du bon type avec l'état d'avant** · ⭐ **rejouer le même masquage ne dérange pas Hektor** ·
⭐ **le témoin inverse du geste : on la réaffiche** · les deux refus · et **l'inverse complet**.

### ⛔ CE QUI N'EST PAS ÉPROUVÉ, ET JE LE DIS

1. **La branche des DROITS n'est pas exercée.** L'éditeur SQL tourne en superutilisateur, et le
   seul commercial actif *(legrand)* a un périmètre **`reseau`** → la garde l'**autoriserait**, donc
   le refus ne se prouverait pas. *(Même honnêteté que le 16/10 : « la répétition ne pourra pas
   prouver la branche manager : 0 manager actif ».)*
2. **Le worker n'a jamais tourné.** `node --check` prouve **la syntaxe**, pas la logique.
3. ⚠ **Et un doute trouvé en répondant à Frédéric, pas avant** : le handler réveille le fabricant,
   **qui traite TOUTES ses cibles**. Mesure du 19/10 : **23 cibles vivantes + 55 sur les autres
   index** → ça passe. ⚠ **Mais pendant les 14 nuits du balayage, chaque annonce balayée devient
   une cible** → un clic au petit matin pourrait dépasser les **8 s de PostgREST**. C'est en *best
   effort* *(le geste chez Hektor est déjà fait et prouvé)*, **mais la photo masquée resterait
   visible au vendeur jusqu'au lendemain, ces nuits-là.**

### ⛔ RESTE

**Frédéric colle la répétition**, puis le patch · **redémarrer les 4 services** *(accord à part)* ·
**pousser le front** · puis **l'essai réel sur le bac à sable 62774** — ⭐ **et c'est lui qui
répondra à la question restée ouverte : masquer une photo fait-il bouger `date_maj` ?**
*(ce qui tranche la marche 3)*.


### ✅✅✅ RÉPÉTITION v2 COLLÉE — **22 MESURES, 22 JUSTES** *(19/10)*

```
1-avant  | contrainte / droits / distribution / RPC  = non, non, non, non
1-avant  | 62774 : photos / visibles                 = 4 / 4
1-avant  | la photo 482253 est                       = visible
2-patch  | contrainte / droits / distribution        = OUI, OUI, OUI
2-patch  | la RPC existe                             = OUI (4 parametres)
2-patch  | anon peut l appeler                       = NON  (authenticated : oui)
3-garde  | SANS identite : la garde refuse           = droits_insuffisants -- LA GARDE MORD
3-garde  | identite empruntee : auth.uid()           = 0548613b-7654-42fa-a65d-d9adc815d2c0
3-garde  | AVEC identite : la garde laisse           = oui
4-masque | le retour est ok                          = oui, visible=false
4-masque | la photo 482253 est devenue               = masquee
4-masque | LE POST-IT (index marques)                = 1
4-masque | adresses_app_le de 62774                  = A BLANC -- le fabricant la reciblera
4-masque | le travail cree, du bon type              = set_hektor_photo_visibility (pending)
4-masque | sa charge : l etat d avant                = true, demande=false, base_snapshot=4
4-masque | visibles restantes / derniere             = 3 / plus_aucune_visible=false
5-rejoue | rejouer le MEME masquage                  = deja_dans_cet_etat -- Hektor non derange
6-affich | on la REAFFICHE                           = oui, visible=true
6-affich | la photo 482253 est revenue               = visible
6-affich | deux travaux distincts crees              = oui
7-refus  | une photo inconnue                        = photo_introuvable_chez_hektor
7-refus  | des parametres vides                      = parametres_incomplets
8-retour | la RPC a disparu                          = oui
8-retour | les 3 verrous ne connaissent plus         = oui, aucune trace
```

### ⭐⭐ CE QUE CES LIGNES PROUVENT, ET QUI NE SE DEVINAIT PAS

1. ⭐⭐ **LA GARDE EST PROUVÉE DANS LES DEUX SENS** — `droits_insuffisants` **sans** identité,
   `oui` **avec**. C'est le contrôle que **l'échec du 1ᵉʳ collage m'a offert** : je ne l'avais pas
   écrit. Sans lui, « le geste marche » n'aurait rien dit sur la sécurité.
2. ⭐ **LE POST-IT EST POSÉ** : `index_marques_a_refaire = 1`, et `adresses_app_le` passe **à
   blanc**. ➡ Le fabricant **reciblera** l'annonce, donc la boîte publique sera juste en quelques
   secondes au lieu d'une nuit. **Le mécanisme que je n'avais pas pu prouver est prouvé.**
3. ⭐ **HEKTOR N'EST PAS DÉRANGÉ DEUX FOIS** : rejouer le même masquage rend
   `deja_dans_cet_etat`. **Aucun second travail**, donc aucune requête inutile — et c'est la règle
   qui a coûté le bannissement du 20/08.
4. ⭐⭐ **LE GESTE EST RÉVERSIBLE, ÉPROUVÉ** : on la masque, on la réaffiche, **deux travaux
   distincts**. C'est le témoin inverse **du geste lui-même**, pas seulement du patch.
5. **LA CHARGE PORTE LE RETOUR ARRIÈRE** : `etat_avant = true`, `demande = false`, et
   `base_snapshot` contient **les 4 photos**. ➡ Le worker a de quoi remettre le drapeau si Hektor
   refuse — ce que **rien d'autre ne ferait** *(audit du 19/10)*.
6. **LES DEUX REFUS SONT NOMMÉS**, pas génériques, donc traduisibles à l'écran.
7. **L'INVERSE NE LAISSE AUCUNE TRACE** — ni la RPC, ni les 3 verrous.

➡ **LA PIÈCE 1 EST PROUVÉE.** ⛔ Reste, dans l'ordre : coller le patch · **redémarrer les 4
services** · **pousser le front** · puis **l'essai réel sur 62774**, le seul qui prouvera le geste
**chez Hektor** — et qui répondra à la question restée ouverte : **masquer une photo fait-il bouger
`date_maj` ?**


### ✅✅ MARCHE 4 PIÈCE 1 **EN PRODUCTION** — 7 contrôles, et une attente de MOI qui était fausse

Frédéric a collé le patch. Mesure en lecture seule :

| contrôle | résultat |
|---|---|
| a. la **contrainte** connaît le type | **OUI** |
| b. les **droits** le connaissent | **OUI** |
| c. la **distribution** le connaît *(service `documents`)* | **OUI** |
| d. la **RPC** existe | **OUI (4 paramètres)** |
| e. `anon` peut l'appeler | ⭐ **NON** · `authenticated` oui · `service_role` oui |
| f. retours chariot injectés | ⚠ **139** *(j'attendais 0)* |
| g. travaux de ce type déjà posés | **0** — normal, le worker n'est pas redémarré |

### ⚠⚠ LES 139 RETOURS CHARIOT : MON ATTENTE ÉTAIT FAUSSE, PAS LE PATCH

Mesure en détail :

| fonction | CR | l'inverse retrouve sa pose ? |
|---|---|---|
| `app_console_can_request_job` | **0, propre** | ✅ **1 fois** |
| `app_console_claim_next_job` | **0, propre** | ✅ **1 fois** |
| `app_console_photo_visibilite_optimistic` | **139** | *(elle se `DROP`, aucune ancre à chercher)* |

⭐⭐ **LA LEÇON, ET ELLE EST NEUVE** : `replace(…, chr(13), '')` protège **les ancres et la
RECHERCHE** — il **ne nettoie pas le corps d'une fonction qu'on CRÉE**. Les deux fonctions
*patchées* sont propres *(le patch les relit en retirant les CR et les réécrit depuis le texte
nettoyé)* ; la RPC, elle, est **créée depuis le texte collé**, donc elle les garde.

**Et c'est l'état NORMAL du projet, mesuré le 19/10 :**
```
fonctions app_* en tout        148
  AVEC des retours chariot      26      = 18 %
les plus chargees : app_bascule_identite_contact (170) ·
                    app_console_photo_visibilite_optimistic (139) ·
                    app_console_photo_couverture_optimistic (112)  <- celle du 16/10
```
➡ **Sans conséquence** : l'inverse de ce geste **supprime** la RPC, il ne cherche pas d'ancre
dedans. ⚠ **Mais à savoir** pour un futur patch qui la modifierait **par ancre** : il devra
retirer les CR des deux côtés — ce que tous les patchs du projet font déjà.

➡ **LA PIÈCE 1 EST EN PRODUCTION.** ⛔ Reste : **redémarrer les 4 services** · **pousser le
front** · puis **l'essai réel sur 62774**.


### ✅✅✅ MARCHE 4 — L'ESSAI RÉEL EST VERT. ⑦-8 EST COMPLET *(19/10, 16:21)*

**Les 4 services redémarrés, vérifiés PAR L'HEURE DES PROCESSUS** *(pas par la croyance)* :
fichier worker modifié à **15:22:14**, les 4 processus node nés à **16:13:07-09** → **après**.
Et le front **poussé** *(écart avec le distant : `0 0`)*.

⚠ **Le 1ᵉʳ appel a rendu `droits_insuffisants`** — ⭐ **exactement ce que la répétition avait
prouvé** : dans l'éditeur SQL `auth.uid()` est nul. Il a fallu **emprunter l'identité dans la même
transaction** *(`begin; set_config(…, true); select …; commit;`)* — un `set_config` seul se perd
entre deux instructions. ⭐ Identité : **codex.test, l'admin d'essai**, pour que la trace du travail
dise « essai » et pas le nom de Frédéric.

**LE RETOUR DE LA RPC, chaque valeur comme prédite :**
```
ok=true · visible=false · deja_dans_cet_etat=false · visibles_restantes=3
plus_aucune_visible=false · index_marques_a_refaire=1   <- LE POST-IT EST POSE
job_id 17655d3f-ff21-49ec-b25e-a2ba27b130c1
```

**LE COMPTE RENDU DU WORKER** — `done`, **1 tentative, 16 secondes**, aucune erreur,
`NS31851120:documents:service:v9` *(le bon service)* :
```
photos_lues 4 · visibles 3 · masquees 1      <- HEKTOR CONFIRME LE BASCULEMENT
boite_publique {"cibles":79,"statut":"ok","vivantes_remplies":2}
```
⭐⭐ **« cibles: 79 » prouve le post-it** : j'avais mesuré **78 cibles** avant l'essai, **plus la
nôtre = 79**. Et `statut: ok` → **le fabricant a tourné dans le budget de 8 s**, donc le doute que
j'avais soulevé ne s'est pas réalisé *(il reste vrai pour les nuits de balayage)*.

**LES 8 CONTRÔLES EN BASE :**

| contrôle | résultat |
|---|---|
| a. la photo 482253 est | **MASQUÉE** |
| b. photos / visibles chez nous | **4 / 3** |
| c. marquées absentes *(dégât collatéral)* | ⭐ **0** |
| d. ⭐⭐ **la BOÎTE PUBLIQUE** | **3** *(elle était à 4)* — **en secondes, pas en une nuit** |
| e. la masquée est-elle DANS la boîte ? | ⭐⭐ **NON — le verrou tient** |
| f. la couverture est une visible ? | **une visible** |
| g. le panneau photos voit toujours tout | ⭐ **4 photos dont 1 masquée** |
| h. `adresses_app_le` reposée par le fabricant | **2026-10-19 14:21:33** — fraîche |

### ⭐⭐⭐ CE QUE CET ESSAI PROUVE, BOUT À BOUT

**La règle de Frédéric du 19/10 est réalisée en entier** : *« il faut d'abord écrire chez nous,
ensuite envoyer l'information à Hektor, et sinon il y a le run quotidien pour l'autre sens »*.

```
le clic          -> notre table : MASQUEE                          immediat
                 -> Hektor appele, et les DEUX galeries RELUES     16 s
                 -> le basculement PROUVE (masquees: 1)            pas deduit d un 200
                 -> la boite publique 4 -> 3                       secondes
                 -> le verrou tient : la masquee n y entre pas
                 -> le panneau photos voit toujours ses 4
```

### ⏰ ET LA DERNIÈRE QUESTION OUVERTE SE MESURE DEMAIN, GRATUITEMENT

**« Masquer une photo fait-il bouger `date_maj` ? »** — ⭐ **la photo 482253 reste MASQUÉE ce soir
exprès** : c'est le témoin. Demain, après le run, il suffit de lire la date de l'annonce 62774 dans
le miroir :

```sql
-- dans data/hektor.sqlite, apres le run du 20/10
select hektor_annonce_id, date_maj from hektor_annonce where hektor_annonce_id = '62774';
```

- si `date_maj` porte le **19/10** → ⭐ **masquer bouge la date**, et le run de mise à jour
  *(marche 3)* verra les masquages tardifs **tout seul** ;
- si elle porte une date **antérieure** → le run de MAJ voit les **arrivées** mais pas les
  masquages tardifs, et il faudra **repasser le balayage périodiquement** *(cadence = décision de
  Frédéric)*.

➡ **Une lecture locale, zéro appel à Hektor, et elle tranche la marche 3.**

### ✅ ⑦-8 EST COMPLET

| marche | état |
|---|---|
| **1 — le verrou de publication** | ✅ **en production** *(et le témoin inverse a prouvé qu'il a servi le jour même)* |
| **2 — le balayage** | ✅ **la tâche est enregistrée**, elle part **cette nuit à 00:00**, ~14 nuits |
| **3 — le run de mise à jour** | ✅ **rien à écrire** : c'est la même tâche, qui y deviendra toute seule ⏰ *(sa cadence dépend de la mesure de demain)* |
| **4 — le bouton masquer / afficher** | ✅ **PROUVÉ EN RÉEL** — base, worker, écran, et 8 contrôles verts |

⛔ **Reste à voir à l'œil** : personne n'a encore **vu le bouton** dans le panneau photos. Le
fichier servi porte le code *(front poussé)*, mais ça ne dit pas qu'il est bien placé.
➡ **Écran d'un bien, panneau Photos, 3ᵉ pastille en haut à droite de chaque tuile.**


### ⭐⭐⭐ LE GESTE EST AUSSI UN MINI-BALAYAGE — trouvé par un clic de Frédéric *(19/10, 14:31)*

**Il a masqué UNE photo sur l'annonce 63073 (V800063073), depuis l'app.** Résultat mesuré :

| | |
|---|---|
| le travail | `set_hektor_photo_visibility`, **done**, posé à **14:31:23** |
| photos chez nous après | **24** — **9 visibles, 15 masquées** |
| la boîte publique | **9** — ⭐ exactement le nombre de visibles |
| `adresses_app_le` reposée | **14:31:56**, soit **33 s après** |

⚠ **Mais 15 masquées, alors qu'on n'en avait AUCUNE sur cette annonce le matin.** La mesure
tranche :

| | combien | créées | dérivé |
|---|---|---|---|
| **la photo qu'il a masquée** *(485375)* | **1** | le 25/09 | ⭐ **oui** — elle était visible chez nous |
| ⭐⭐ **les découvertes** | **14** | ⭐ **le 19/10 à 14:31:56** | **aucun** — jamais vues chez nous |

➡ **Il n'a pas masqué 15 photos. Il en a masqué UNE, et le système en a DÉCOUVERT 14.**

**POURQUOI** : le ⓷ du handler **relit les deux galeries pour PROUVER le basculement** *(on
n'accepte jamais le 200)*. ⭐ Et une relecture ne rend pas une photo : **elle rend les 24 de
l'annonce, des deux galeries**. Donc **la preuve a ramené toute la vérité.**
⭐⭐ C'est exactement l'« autre sens » que Frédéric décrivait — *« sinon il y a le run quotidien
pour l'autre sens »* — **sauf qu'il n'a pas attendu le run : il s'est produit dans le même travail.**
⚠ **Je ne l'avais pas annoncé** : je décrivais le geste comme une écriture. **C'en est une, PLUS
un mini-balayage de l'annonce.**

### ⚠⚠ ET ÇA A DÉCOUVERT UN TROU : LES LIGNES SANS FICHIER

| | la sienne | les 14 découvertes |
|---|---|---|
| sur le serveur | **1** | ⛔ **0** |
| dérivé | **1** | ⛔ **0** |
| `storage_status` | `local_only` | ⚠ **`pending`** |
| adresse Hektor | oui | oui |

⛔ **Et RIEN NE LES AURAIT TÉLÉCHARGÉES** : `rattrapage_photos.js` lit **le miroir**, qui ne porte
que **les visibles**. Elles auraient attendu le balayage — **jusqu'à 14 nuits**.
*(État du parc : **16 lignes en `pending`** sur **3 annonces**, dont **14 masquées**.)*

### ✅ LE REMÈDE, ÉCRIT *(go « Ok »)* — une étape de plus, pas un code de plus

Le handler compare, **avant d'écrire**, ce que Hektor rend avec ce qu'on a. S'il a **découvert**
des lignes, il **pose un `sync_hektor_photos`** — ⭐ **le geste qui sait télécharger depuis mai**
*(preuve du 19/10 : « photos_downloaded: 3 »)*, avec les freins du projet.

| | |
|---|---|
| ⛔ **ce qu'il ne fait pas** | télécharger lui-même — **deux codes de téléchargement divergeraient** |
| ⭐ **il ne coûte rien à vide** | la condition est *« j'ai découvert des lignes »* → un masquage ordinaire reste à **2 appels** |
| ⛔ **aucune boucle** | `sync_hektor_photos` ne pose pas de geste de visibilité |
| ⭐ **il ne double pas** | même garde que les deux `enqueue*` du fichier : si un sync est **déjà en vol**, il ne repose rien |
| ⚠ **best effort** | le masquage est **déjà fait et prouvé** ; si la demande rate, **le balayage repassera**. Elle AMÉLIORE, elle ne CONDITIONNE pas |

⭐ **Et le compte rendu le DIT** : `masquees_decouvertes` et `synchro_photos` sont dans le résultat
du travail — *sans ces deux lignes, 14 photos ramenées passeraient pour un effet de bord invisible.*

**Contrôle** : ✅ `node --check` passe, et les **7 étapes** du handler sont dans l'ordre.
⛔ **Inerte jusqu'au redémarrage des 4 services.**

### ⚠⚠ ET UN CHIFFRE DE MA PROJECTION EST À REVOIR

| | |
|---|---|
| ma projection du 19/10 | **~2,3 masquées** par annonce concernée, **~1 709** au total |
| cette annonce **à elle seule** | ⚠ **14** |

➡ **La récolte des 14 nuits sera bien plus grosse qu'annoncé.** ⭐ Et ces 14 n'ont **aucun dérivé**,
donc elles **ne peuvent pas** sortir sur la vitrine — la boîte est à 9, le nombre de visibles.
**Le contrôle de demain matin dira la vraie ampleur.**


---

## ⑦-9 · RENOMMER UN DOCUMENT — **AUDITÉ LE 19/10, ET LA RÉPONSE EST NON**

**Go de Frédéric : « Renommer ».** Ce point venait de l'audit du 08/10, qui l'avait repéré en
**trois mots** — *« C2 | 🟠 | ⑦ (renommer) »* — **avec sa colonne « preuve » VIDE**. Il n'avait
jamais été audité.

### 1. LE BESOIN EST RÉEL, mesuré

| | |
|---|---|
| documents en tout | **189 809** *(dont 189 808 chez Hektor)* |
| noms qui **ressemblent à un fichier** | ⚠ **187 610 — 99 %** |
| noms qui sont une **vraie étiquette** | **2 199** |
| le nom technique est gardé à part | ✅ **189 807** l'ont dans `metadata_json` |

```
_1_24137_diag_ae2021_.pdf   ·   _194401863817793382_1_.jpg
_20480087_diagnostic_technique.pdf
```
⭐ **Un document a TROIS noms** *(`extractDocumentEntries`, l. 1020)* : le **technique**
*(args[1])*, le **transfert** *(args[2], le `humanname` de `force_transfert`)*, et le
**crmLabel** — celui que Hektor **affiche** dans sa colonne « Nom du document ». ⭐ C'est le
crmLabel que `document_name` garde.

### 2. ⛔ ET HEKTOR NE SAIT PAS LE RENOMMER — relevé en lecture seule

**`Console/sonde_documents_renommage.js`** *(neuve, lecture seule, 2 appels, arrêt net au premier
refus, la session du worker réutilisée et **jamais réécrite**)*.

⭐⭐ **ELLE A TROUVÉ CE QUE MES CAPTURES N'AVAIENT PAS** : le JavaScript **vivant** fait
**218 823 caractères** contre **104 Ko** dans ma capture du 13/05 — *une capture de cinq mois
n'est pas une mesure*. Et il porte **18 modes « doc »**, dont trois que je n'avais jamais vus.

**LES TROIS FAUX AMIS, écartés UN PAR UN en lisant leur corps :**

| mode | champ de nom | ce qu'il renomme VRAIMENT |
|---|---|---|
| `updatedocument` | ⭐ **`titre`** | ⚠ **la BIBLIOTHÈQUE de l'agence** — `onComplete: loadBiblio()`, et `editedocument` ouvre `labs_bibliotheque.js` en portée *agence* |
| `documentTypeUpdateAction` | ⭐ **`nom`** | ⚠ **un MODÈLE de document** — `onComplete: chargemesdocumentstype()` |
| `templateDocument-getNameOrRenameBloc` | — | ⚠ **un BLOC dans un modèle** |

➡ **Pour un document ATTACHÉ À UNE ANNONCE, Hektor n'offre que trois gestes** : le **lister**
*(`UploadedDocument_list`, `documentTypeListUploadedDocs`)*, le **télécharger**
*(`force_transfert`)*, le **supprimer** *(`deleteUploadedDocument`, `delete_doc_simple`,
`deletedocument`)*. ⛔ **Aucun renommage.**

⭐ **Et le précédent le confirme** : pour les photos, Hektor a `legendVignette(` et notre
extracteur relève `can_edit_legend`. **Pour les documents, rien d'équivalent — ni dans la capture,
ni dans le JavaScript vivant.**

⚠ **Ce que la sonde n'a PAS pu lire** : la page `mode=chargeannonce_Documents&idann=…` a rendu
**27 caractères** — mes paramètres sont faux. ⭐ **La sonde l'a DIT au lieu de faire semblant.**
Donc le HTML rendu d'une ligne de document reste non mesuré ; **mais les 18 modes du JS vivant,
eux, sont exhaustifs** — et aucun ne renomme.

### 3. ⚠⚠ ET RENOMMER « CHEZ NOUS » SERAIT EFFACÉ — mesuré, pas supposé

`upsertConsoleDocuments` écrit **`document_name: entry.document_name`**, c'est-à-dire **le nom lu
sur la page de Hektor**. ➡ **Un nom qu'on écrirait dans cette colonne serait écrasé à la
prochaine synchro de l'annonce.** ⚠ **C'est exactement le piège de la date de clôture, payé le
16/10** *(« le worker écrivait notre date dans la colonne de Hektor »)*.

### 4. DONC ⑦-9 EST UNE DÉCISION, PAS UN DÉVELOPPEMENT

| | |
|---|---|
| **A — fermer le point** | comme ⑦-7 le 18/10. **Hektor ne sait pas le faire, donc l'app ne peut pas le lui demander.** Coût : zéro. ⚠ Et les 99 % de noms illisibles restent |
| **B — renommer CHEZ NOUS, avec le patron du projet** | une colonne `document_name_app` + `COALESCE(document_name_app, document_name)`. ⭐ **Ce patron existe déjà deux fois** *(les adresses photos, la date de clôture)*, donc rien à inventer. ⚠ Mais **Hektor afficherait toujours l'ancien nom** : deux vérités, et l'app serait seule à porter la bonne |

⭐ **Mon avis : B**, parce que le besoin est massif *(99 %)* et que **le patron est éprouvé**. ⚠
**Mais c'est un périmètre, donc la décision est de Frédéric** — et A est parfaitement défendable :
un nom que Hektor ne connaît pas est un nom qui disparaît le jour de la coupure... ⭐ **non, l'inverse** :
c'est NOTRE colonne, elle survit à la coupure. **C'est même un argument POUR B.**


### ⭐⭐ ÉTAPE 2 — ET LA MESURE A RETOURNÉ LA QUESTION : `document_name` EST UN IDENTIFIANT

J'allais présenter « renommer chez nous, en acceptant la divergence ». ⚠ **La mesure l'interdit
sous cette forme.**

**`document_name` n'est pas une étiquette : 13 endroits s'en servent pour RECONNAÎTRE un
document.**

| où | ce qu'il reconnaît |
|---|---|
| `App.tsx:5468` · `10970` · `11465` | ⭐ **le MANDAT**, par `/mandat/i` sur le nom |
| `App.tsx:11465` · `28164` | **l'AVENANT**, par `/avenant/i` |
| `App.tsx:10109` → `10120` | le **type de fichier** *(l'icône, le visualiseur)*, par l'extension |
| `App.tsx:11493` | `docTypeOf(...)` — **la rubrique** du document |
| ⭐⭐ `backend/.../supabase_storage.py:33` | **l'AVIS DE VALEUR**, par `ilike 'Avis de valeur%'` |
| `console_job_worker.js:8145` | ⭐⭐ **l'appariement avec la ligne de Hektor**, par le nom |
| `console_job_worker.js:5531` | ⭐ **l'appariement d'une SIGNATURE**, par le nom |
| `console_job_worker.js:4617` | le **tri** de la liste |

**ET VOICI CE QUE ÇA COÛTERAIT DE REMPLACER LE NOM :**

| le motif qui sert de reconnaissance | documents |
|---|---|
| contient « mandat » | ⚠ **18 225** |
| contient « avenant » | ⚠ **7 344** |
| commence par « Avis de valeur » | **44** |
| porte une extension *(`.pdf`, image, bureautique)* | ⚠ **185 852** |
| ⭐⭐ **AUCUN de ces motifs — renommables sans rien casser** | ⛔ **2 093 sur 189 809, soit 1,1 %** |

➡ ⛔ **Donc un renommage qui ÉCRASE `document_name` casserait la reconnaissance de 98,9 % des
documents.** Ce n'est pas une précaution : c'est un chiffre.

### ✅ ET LE PROJET A DÉJÀ TRANCHÉ LA FORME *(leçon 15, une fois de plus)*

Je cherchais « une colonne sœur `_app` » en croyant la trouver **deux fois**. Il y en a
**28, sur 17 tables** — dont `mandat_date_cloture_app`, `photo_url_listing_app`,
`images_preview_json_app`. ⭐⭐ **Et il y a mieux : un mécanisme GÉNÉRIQUE**, trois fois posé :

```
app_annonce_champ_app   (app_dossier_id, champ, valeur_app, origine, ecrit_le, ecrit_par)     9 lignes
app_mandat_champ_app    (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, …)     3 lignes
app_affaire_champ_app   (…, valeur_app, …)                                                   17 lignes
app_document_champ_app  ⛔ N'EXISTE PAS
```

⭐⭐⭐ **ET LE CRITÈRE D'ALLUMAGE DU PROJET RÉPOND AU POINT ⑦-9 TOUT SEUL.** Il est écrit dans
CLAUDE.md, tranché le 13/10 : *« on n'allume qu'un champ que l'APP CRÉE et que HEKTOR
N'ENTRETIENT PAS »*. C'est pour ça que `CHAMPS_APP_ANNONCE` reste **ÉTEINT** : Hektor entretient
les champs d'une annonce.

➡ ⭐ **L'étiquette humaine d'un document est le cas d'école du critère** : **Hektor n'a aucun
renommage**, donc il ne l'entretient pas, donc il ne l'écrasera jamais. **C'est l'inverse exact
du cas qui a fait éteindre l'interrupteur.**

### LES DEUX OPTIONS, TELLES QU'ELLES SONT MAINTENANT

| | |
|---|---|
| **A — fermer le point** | comme ⑦-7. Coût zéro. ⚠ Les 99 % de noms illisibles restent, **et ils sont illisibles pour les négociateurs tous les jours** |
| **B — une étiquette À CÔTÉ, jamais à la place** | `document_name` **ne bouge pas** *(les 13 reconnaissances continuent de marcher)*, et une étiquette humaine s'ajoute. **~12 endroits d'affichage** à passer en `étiquette ?? document_name`. ⭐ **Rien à inventer : le patron est posé 28 fois** |

⭐ **Mon avis : B**, et plus franchement qu'avant la mesure — parce que **le critère du projet est
rempli** *(Hektor n'entretient pas ce champ, il ne sait même pas le lire)* et parce que **le
risque identifié se contourne par construction** : on n'écrase rien.

### ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS *(option B)*

| | |
|---|---|
| ⛔ **les 13 reconnaissances** | **rien** — elles lisent `document_name`, qu'on ne touche pas. ⭐ C'est tout l'intérêt de la colonne à côté |
| ⚠ **le nom du fichier téléchargé** *(`App.tsx:38752`)* | **à TRANCHER** : télécharger « DPE 2021.pdf » est le but, mais ⚠ **l'extension doit survivre** *(sinon le fichier ne s'ouvre plus)* |
| ⚠ **le coffre** *(`4703`, `4807`, `5177`)* | `archive_filename` est **déjà figé** à l'envoi : un renommage **après** ne le change pas → **deux noms**. À déclarer, ou à ne pas toucher |
| ⚠ **la synchro de nuit** | elle écrit `document_name`, **pas** la colonne neuve → ⭐ **rien à modifier dans le worker**. C'est le cœur du choix |
| ⚠ **`app_cockpit_activite`** et **`app_console_creer_document_optimistic`** | les **2 seules** fonctions en base qui citent `document_name` *(0 vue)*. À lire avant d'écrire |
| ⚠ **les droits** | qui peut renommer ? **Question pour Frédéric** *(négociateur sur ses biens, ou admin ?)* |

⛔ **JE N'ÉCRIS RIEN AVANT SON CHOIX.** Un périmètre ne se décide pas sans lui.


### ⭐⭐⭐ LA QUESTION DE FRÉDÉRIC A TUÉ MON PLAN, ET IL AVAIT RAISON *(19/10, soir)*

Il a répondu **« B, négociateur sur ses biens et admin manager »**, puis il a demandé :
> *« mais on peux pas la deviné ? c'est pas un geste manuel ?? »*

⭐⭐ **Il a raison, et ma proposition était mauvaise** : je lui faisais renommer **187 610
documents à la main**, autrement dit **jamais**. Un geste qui demande 187 610 gestes n'est pas un
geste.

### ⚠⚠ ET EN MESURANT, J'AI DÛ CORRIGER MON PROPRE AUDIT

**Mon chiffre « 99 % illisibles » ÉTAIT FAUX** — pas la base : **mon critère**. J'avais compté
« tout nom qui ressemble à un fichier ». Or :

```
vente_odin_rembault.pdf     titre_de_proprie_te_250.pdf     dpe_poulenard.pdf
bon_de_visite_133.pdf       mandat_2093.pdf                 plan_lot_n_7.pdf
acte_donation_page_de_couverture.pdf        2016_5_18_facture_doyen.pdf
```
⭐ **Tous ressemblent à un fichier ET se lisent très bien.** *Leçon : un critère qui ne distingue
pas « laid » de « illisible » ne mesure rien.*

**LA VRAIE MESURE, sur les 189 809 :**

| | documents | |
|---|---|---|
| au moins **2 vrais mots** *(« vente odin rembault »)* | **132 293** | **69,7 %** |
| **un seul** mot *(« titre_120 »)* | **50 226** | **26,5 %** |
| ⛔ **aucun mot** *(« 556.pdf », un hachage)* | **7 290** | **3,8 %** |

### ⛔ LES DEUX SOURCES QUE J'ESPÉRAIS SONT MORTES, mesurées

| | |
|---|---|
| `document_type` | ⛔ **inutile** : **189 808 sur 189 809** valent littéralement le mot `document` |
| `metadata_json->transfer_name` | ⛔ **inutile, et PIRE que le nom** : il existe sur 100 % des documents, il diffère sur 181 450… mais c'est **le même texte sans les séparateurs** — `vente_odin_rembault.pdf` → `venteodinrembault.pdf` |

### ⭐⭐ MAIS LE VOCABULAIRE EST DÉJÀ DANS LES NOMS — relevé, jamais inventé

```
mandat 19 002 · vente 17 424 · offre 11 398 · gti 10 107 · titre 9 006 · avenant 7 590
agence 7 516 · facture 6 747 · dpe 6 529 · cadastre 6 170 · attestation 4 978
propriete 4 795 · cni 4 441 · ggti 4 222 · plan 4 146 · compromis 3 993 · avis 3 959
achat 3 846 · valeur 3 064 · bon 3 048 · visite 3 029 · exclusif 2 969 · taxe 2 885
bv 2 843 · tp 2 452 · accord 2 361 · estimation 2 307 · promesse 2 285 · aae 2 271
acte 2 265 · pret 2 257 · ci 2 242 · diag 2 224 · fonciere 2 196
```

➡ ⭐⭐⭐ **Donc ça ne se DEVINE pas : ça se LIT.** Et le découpage final le prouve :

| | documents | | ce qu'il faut |
|---|---|---|---|
| ⭐ **des mots lisibles** | **182 519** | **96,2 %** | une **mise en forme**, rien de plus |
| ⭐ une **abréviation** du relevé | **3 347** | **1,8 %** | un **petit dictionnaire**, lu dans la base |
| ⭐ une **date** *(`20250716_095119.jpg`)* | **1 184** | **0,6 %** | « **Photo du 16/07/2025** » |
| ⛔⛔ **rien du tout** *(`1.pdf`, `556.pdf`, un UUID)* | **2 759** | **1,5 %** | ⭐ **LÀ SEULEMENT, la main** |

### ⭐⭐⭐ ET ÇA CHANGE TOUT LE COÛT ET TOUT LE RISQUE

**98,5 % se résout SANS RIEN STOCKER** — une fonction d'affichage, dans le front.

| | |
|---|---|
| ⭐⭐ **les 13 reconnaissances** | **intactes PAR CONSTRUCTION** : on ne stocke rien, donc rien ne peut être écrasé |
| ⭐⭐ **la synchro de nuit** | **ne peut pas l'effacer** : il n'y a rien à effacer |
| ⭐ **aucune colonne, aucun DDL, aucun worker** | le patron `_app` n'est plus nécessaire pour 98,5 % |
| ⭐ **réversible à la seconde** | c'est **une fonction** ; on la retire, tout revient |
| ⭐ **ça marche sur les 189 809 d'un coup** | pas un document à la fois |
| ⚠ **et le geste à la main** | ne concerne plus que **2 759 documents** — là, les droits de Frédéric s'appliquent : **négociateur sur ses biens, admin, manager** |

⚠ **UNE QUESTION AVANT D'ÉCRIRE LE DICTIONNAIRE** : **`aae`, 2 271 documents — je ne sais pas ce
que ça veut dire**, et un dictionnaire ne doit **rien inventer**. *(`bv` = bon de visite,
`tp` = titre de propriété, `cni`/`ci` = pièce d'identité, `pv ag` = PV d'assemblée générale,
`diag` = diagnostic — à confirmer par lui.)*


---

## ⑦-9 · AUDIT APPROFONDI DE TOUTE LA CHAÎNE DOCUMENTAIRE *(19/10, sur demande de Frédéric)*

> *« attends il y a tout un travail sur les documents je pense qu'il ne faut surtout rien cassé et
> bien comprendre le fonctionnement avant de proposer un correctif donc refait un audit approfondi
> puis explique moi en detail »*

⭐ **Il avait raison de m'arrêter**, et l'audit a **démoli deux de mes affirmations**.

### 1. LES NOTES DU PROJET D'ABORD — 9 notes mémoire relues

| ce qu'elles apprennent | conséquence pour ⑦-9 |
|---|---|
| la page documents a **4 sections** : ImmoSign, « Mes documents », ECM, Dépôt | deux familles de noms, pas une |
| le HTML **dépend du contexte utilisateur** *(en admin Hektor masque `docBtnSign_`)* | ⚠ un relevé en admin ne prouve rien sur l'affichage négociateur |
| **une ligne = un chemin = UN fichier** *(policy `hektor_console_documents_read_scope`)* | le modèle ne sait pas porter deux fichiers |
| le mécanisme de détection est **installé à moitié** *(`--detect` jamais allumé = G.2/G.6)* | ⚠ **hors ⑦-9**, mais ça veut dire que les noms ne se rafraîchissent pas tous |
| le mur de Hektor est un **quota de volume** | tout relevé en ligne se compte |
| **un document ne bouge pas `date_maj`** | on ne peut pas détecter un ajout par la date |
| ⚠ **la note dit que les blocs ImmoSign ne sont JAMAIS indexés** | ⛔ **PÉRIMÉ : le code les indexe** *(l. 1085)*. **Le code gagne** |

### 2. ⚠⚠ MA PREMIÈRE AFFIRMATION ÉTAIT FAUSSE : « 99 % de noms illisibles »

Mon critère comptait **tout nom qui ressemble à un fichier**. Or `vente_odin_rembault.pdf`,
`bon_de_visite_133.pdf`, `dpe_poulenard.pdf`, `acte_donation_page_de_couverture.pdf`
**ressemblent à un fichier ET se lisent parfaitement.**

| la VRAIE mesure *(189 809)* | documents | |
|---|---|---|
| des **mots lisibles** | **182 519** | **96,2 %** |
| pas de mot, mais une **abréviation** du relevé | **3 347** | **1,8 %** |
| pas de mot, mais une **date** | **1 184** | **0,6 %** |
| ⛔ **rien du tout** *(`1.pdf`, `556.pdf`, un UUID)* | **2 759** | ⭐ **1,5 %** |

➡ **Le besoin réel n'est pas 187 610 documents. Il est de 2 759.**

### 3. ⛔ MA DEUXIÈME PEUR ÉTAIT INFONDÉE : AUCUNE ÉTIQUETTE N'EST JETÉE

J'avais trouvé dans `extractDocumentEntries` *(l. 1038)* :
```js
if (/\.(pdf|jpe?g|png|docx?|xlsx?|csv|txt)$/i.test(text)) labels.push(text);
```
et j'ai cru qu'on **jetait** une colonne « libellé ». ⭐ **Tranché sur une capture locale, sans
appeler Hektor** *(`documents_uploaded_private.html`, annonce 59624, **28 lignes**)* :

```
LIGNE 1  [RETENUE] attestation_devolutive_3_1.pdf          [date] 23/02/2026
LIGNE 2  [RETENUE] attestation_de_propriete_mme_layes_claudette_1.pdf   [date] 23/02/2026
LIGNE 3  [RETENUE] plancadastralnormalise_layes_1.pdf       [date] 23/02/2026
```
⛔ **Une ligne de document déposé porte DEUX cellules : le nom et la date.** Il n'y a **rien**
derrière le filtre. ⭐ **`document_name` EST le nom que Hektor affiche.**

### 4. ⭐⭐ ET LES DEUX FAMILLES SONT NOMMÉES PAR DES RÈGLES DIFFÉRENTES — mesuré

| famille | documents | finit par une extension | **vraie étiquette** |
|---|---|---|---|
| **déposés** privé + partagé | **187 995** | **187 815** | **180** *(et ce sont des `.ods`, `.tif`, `.bmp` — encore des fichiers)* |
| ⭐ **« Mes documents »** *(modèles)* | **1 066** | **0** | ⭐ **1 066 — 100 %** |
| ⭐ **ImmoSign** | **711** | **0** | ⭐ **711 — 100 %** |
| ImmoSign signé | 36 | 1 | 35 |
| **né dans l'app** | **1** | 1 | 0 |

**Pourquoi** : les modèles sont lus par `extractModeloDocumentEntries` *(l. 1143)*, qui prend
`modeloSectionCell(rowHtml, "bxld7")` **sans aucun filtre**. Preuve lue dans la capture :
⭐ **« Bon de Visite Groupe GTI »** — une vraie étiquette, sans extension.

➡ ⭐⭐⭐ **DONC LE « NOM ILLISIBLE » N'EST PAS UN DÉFAUT DE NOTRE CODE.** C'est **le nom que
l'agence a donné au fichier en le déposant**, et Hektor affiche exactement le même.

### 5. ⭐⭐⭐ ET NOMMER UN DOCUMENT MARCHE DÉJÀ — DANS L'APP, AU DÉPÔT

`App.tsx:11378` porte **un champ « Libellé »**, avec pour indication *« Nom visible dans Hektor »* :
```jsx
<label className="filter-field"><span>Libelle</span>
  <input value={uploadLabel} placeholder="Nom visible dans Hektor" /></label>
```
Et `api.ts:8169` en fait **le nom du fichier envoyé** :
```js
const requestedLabel = filenameStem(safeUploadFilename(input.documentLabel ?? '', ''))
const uploadFilename = safeUploadFilename(requestedLabel ? `${requestedLabel}${extension}` : originalName, originalName)
```
⭐ **Le geste « nommer » existe donc déjà.** Ce qui manque, c'est **renommer après coup** — et
c'est ça, et seulement ça, que Hektor ne sait pas faire.

### 6. LE TABLEAU OBJETS × GESTES, rempli par les travaux réellement exécutés

| geste sur un document | travail | exécutés | ⭐ erreurs | dernier |
|---|---|---|---|---|
| **lire / indexer** | `sync_console_documents` | **92 497** | ⭐ **0** | 18/10 |
| **créer / déposer** *(avec son nom)* | `upload_document_to_hektor` | **104** | ⭐ **0** | **19/10** |
| **supprimer** | `delete_document_from_hektor` | **39** | ⭐ **0** | 22/07 |
| **fabriquer** *(cadastre / mandat)* | `generate_*_document` | 38 + 18 | ⭐ **0** | 26/08 |
| **remettre au cloud** | `prepare_document_cloud` | 6 | **0** | 27/07 |
| **relancer / annuler** une signature | `relance_signature`, `cancel_…` | 1 + 1 | **0** | 30/06 |
| ⛔ **RENOMMER** | — | — | — | **n'existe pas** |

⭐⭐ **Zéro erreur sur 92 706 travaux.** *La chaîne documentaire n'est pas fragile : elle marche.*

### 7. L'ÉTAT DU PARC

| | |
|---|---|
| documents | **189 809** *(189 808 chez Hektor, 1 né dans l'app)* |
| volume | ⚠ **265 Go** — *la note de plan parlait de **32 Go** ; écart à noter, hors ⑦-9* |
| sur le serveur seul | **165 187** *(230 Go)* · au cloud **24 622** *(35 Go)* |
| portant une signature | **9 504** · dont **426** avec le PDF signé |
| refusés par le coffre | **46** · sans fichier local **43** |
| ⚠ envoyés vers Hektor | **1 seul** porte un statut d'envoi *(en échec)*, alors que 104 dépôts ont réussi — **incohérence constatée, non élucidée, hors ⑦-9** |

### 8. ⭐⭐ CE QUE J'AI VÉRIFIÉ SUR « NE RIEN CASSER » — les 4 verrous, un par un

| | mesuré |
|---|---|
| ⭐ **les chemins de fichier sont COLLANTS** | `metadata.local_archive_path \|\| …` et `document.storage_path \|\| …` → **une fois posés, réutilisés, jamais recalculés**. ⭐ **Renommer ne déplacerait AUCUN fichier existant** |
| ⭐⭐ **la synchro CONSERVE** | `storage_path`, `file_size`, `sha256`, `archive_policy` repris de l'existant ; **`metadata_json` est FUSIONNÉ** *(`...current.metadata_json`)*. Elle n'écrase que ce qu'elle lit chez Hektor — **dont `document_name`** |
| ⭐⭐⭐ **les 8 écrivains de `metadata_json` fusionnent TOUS** | vérifiés un par un : l. 4692, 4913, 4993 *(relit d'abord !)*, 5109, 5161, 5202, 5321, 8233 *(« Merge non-destructif » écrit en commentaire)*. Le seul qui remplace *(l. 5370)* **crée une ligne neuve** et sort si elle existe. ➡ **une clé à nous SURVIVRAIT, sans colonne ni migration** |
| ⭐ **le front n'écrit JAMAIS la table en direct** | aucun PATCH/POST/UPDATE sur `app_console_document` dans `api.ts` ni dans `backend/` — tout passe par RPC et travaux |
| ⚠ **`archive_filename` est FIGÉ au dépôt** | `${document_name} - ${hektor_doc_id}.pdf` : un renommage après coup ne le change pas → **deux noms** pour les 1 777 modèles |
| ⚠ **13 endroits RECONNAISSENT par le nom** | mandat, avenant, avis de valeur, extension, appariement Hektor, appariement signature, tri. **Un remplacement casse 98,5 % ; un AJOUT ne casse rien** |

### 9. ⛔ CE QUE JE N'AI PAS PU MESURER — et je le dis

1. ⚠ **La capture est du 13/05/2026.** La structure est nette, mais je n'ai **pas relu une page
   vivante aujourd'hui**. Vu : **28 lignes déposées** sur 59624, **5** sur 24113, **4 lignes de
   modèle**. *Une capture n'est pas une mesure du présent.*
2. ⚠ **L'affichage en contexte NÉGOCIATEUR** : la note prouve que Hektor **change son HTML** selon
   l'utilisateur. Toutes mes lectures sont en **admin**. Une colonne de libellé réservée au
   négociateur reste donc **théoriquement possible** — non mesurée.
3. ⛔ **Les trois modes de renommage de Hektor, je les ai LUS, jamais déclenchés** — les déclencher
   est une écriture chez Hektor, donc l'accord de Frédéric. *On ne sait donc pas ce que
   `updatedocument` ferait sur l'id d'un document d'annonce : probablement rien ou une erreur,
   mais c'est une supposition.*
4. ⚠ **`aae`** — **2 271 documents** et **je ne sais pas ce que ça veut dire.**
5. ⚠ Les deux écarts notés sans les traiter : **265 Go contre 32 Go**, et **1 statut d'envoi contre
   104 dépôts réussis**.

### 10. ➡ CE QUE L'AUDIT CHANGE À LA DÉCISION

| | |
|---|---|
| ⛔ **ce qui est cassé** | **RIEN.** 92 706 travaux, 0 erreur. Je n'ai aucun défaut à corriger |
| ⭐ **ce qui existe déjà** | **nommer au dépôt** *(champ « Libellé » → nom du fichier chez Hektor)* |
| ⛔ **ce qui manque** | **renommer après coup**, et **Hektor ne sait pas le faire** |
| ⭐ **le vrai besoin chiffré** | **2 759 documents** sans aucun nom *(1,5 %)*, pas 187 610 |
| ⭐ **la mise en forme** *(souligné → espaces, majuscule)* | **98,5 %**, **sans rien stocker**, donc **sans aucun risque mesurable** : rien à écraser, rien à effacer, réversible à la seconde |
| ⚠ **une étiquette à nous** | techniquement **gratuite** *(`metadata_json` est fusionné)*, **mais elle DIVERGE de Hektor** : le négociateur verrait un nom dans l'app et un autre dans Hektor. **C'est exactement le risque que Frédéric redoutait** |

⛔ **RIEN N'EST ÉCRIT. La décision est à lui.**


### ⛔ ⑦-9 EST FERMÉ PAR DÉCISION *(19/10, soir)*

> *« Non je pense qu'il ne faut rien changer donc il faut que l'utilisateur puisse mettre un
> libellé au début donc rien à changer »*

⭐⭐ **Et son raisonnement est exactement ce que l'audit avait établi** : le nom d'un document se
pose **au dépôt**, pas après coup — et **le champ existe déjà**.

### ✅ CE QUE J'AI VÉRIFIÉ AVANT DE FERMER *(sa prémisse tient-elle ?)*

| | mesuré |
|---|---|
| le champ « Libellé » existe | ✅ `App.tsx:11378`, indication *« Nom visible dans Hektor »* |
| il devient le nom envoyé à Hektor | ✅ `api.ts:8169` — `requestedLabel + extension`, sinon le nom d'origine |
| ⭐ **il est là PARTOUT où l'app dépose** | ✅ `uploadForm` est **le même objet** rendu dans les **deux** habillages *(l. 11528 le tiroir du cockpit, l. 11591 le bureau et le mobile compact)*. ⭐ *Piège du projet évité : « vérifier QUEL composant s'affiche avant de conclure »* |
| ⚠ chez Hektor | ses colonnes sont **« Aperçu \| nom du document \| ajouté le »** — **trois colonnes, aucune étiquette**. ⛔ **Son propre formulaire de dépôt n'est PAS dans ma capture : NON MESURÉ** |

⚠⚠ **ET LA LIMITE DE LA DÉCISION, dite une fois** : le champ « Libellé » n'agit que sur un dépôt
**fait depuis l'app**. Or **189 808 des 189 809 documents ont été déposés dans Hektor**, et **un
seul** est né dans l'app. ⭐ **C'est pour ça que le parc porte des noms de fichiers** — pas par
défaut de code. *Le levier futur est donc « déposer depuis l'app », jamais « renommer ».*
**Noté, non relancé.**

### ⭐ CE QUE CE POINT A RAPPORTÉ MÊME EN ÉTANT FERMÉ

1. ⭐⭐ **La chaîne documentaire est saine** : **92 706 travaux, 0 erreur**. On ne le savait pas.
2. ⭐ **Les deux familles de noms** sont désormais comprises *(déposés = nom de fichier ;
   modèles/ImmoSign = vraie étiquette Hektor à 100 %)*.
3. ⭐⭐ **Les 8 écrivains de `metadata_json` fusionnent tous** — mesuré un par un *(l. 4692, 4913,
   4993, 5109, 5161, 5202, 5321, 8233)*. *Utile le jour où l'app devra garder un champ à elle sur
   un document : aucune colonne, aucune migration.*
4. ⭐ **Les chemins de fichier sont collants** *(`storage_path || …`)* — aucun renommage ne
   déplacerait un fichier déjà rangé.
5. ⭐ **13 endroits reconnaissent un document PAR SON NOM** — à savoir avant d'y toucher un jour.
6. ⚠ **Deux écarts notés, non traités** : **265 Go** de documents contre **32 Go** annoncés dans la
   note de plan ; et **1 seul** document porte un statut d'envoi alors que **104 dépôts** ont réussi.
7. ⚠ **Et une note du projet est PÉRIMÉE** : `hektor-documents-blocs-non-captures` dit que les blocs
   ImmoSign *« ne sont JAMAIS indexés »*. ⛔ **Le code les indexe** *(l. 1085, sur le HTML déjà en
   main, sans appel de plus)*, et la base le confirme *(1 777 lignes)*. **Le code gagne.**

### ⭐ ET DEUX DE MES AFFIRMATIONS ÉTAIENT FAUSSES — pour mémoire

| j'avais dit | la mesure |
|---|---|
| « 99 % des noms sont illisibles » | ⛔ **faux** : mauvais critère — *je confondais **laid** et **illisible***. **96,2 %** portent de vrais mots ; **2 759** seulement n'ont rien |
| « notre filtre jette peut-être l'étiquette de Hektor » | ⛔ **faux** : une ligne de document déposé porte **deux cellules**, le nom et la date. **Rien derrière le filtre** |

➡ **Et le chantier ⑦ n'a plus que ceci d'ouvert** : **⑦-3c réordonner** · **⑦-10** *(une question)* ·
et les **essais réels** de ⑦-1 *(archiver une fiche jetable)* et ⑦-3a *(clôturer à une date ≠
aujourd'hui, et voir l'écran)*. ⛔ **Plus personne n'a vu le bouton des photos à l'œil.**


---

## ⑦-3c · RÉORDONNER LES PHOTOS — AUDIT *(19/10, « Attaque »)*

### 1. ⭐⭐⭐ LA MOITIÉ DU TRAVAIL EST DÉJÀ FAITE, ET ÉPROUVÉE

| pièce | état mesuré |
|---|---|
| **la commande chez Hektor** | ✅ `mode=ordonne_photos&div=liste_photos\|liste_photos_hidden`, **en production depuis le 14/10** *(elle renumérote après une suppression)* |
| **le geste du worker** | ✅ `handleReorderHektorPhotos` *(l. 8923)* — ⭐ **il accepte un ordre QUELCONQUE**, la couverture n'est qu'un cas particulier |
| **le type de travail** | ✅ `reorder_hektor_photos` — ⭐⭐ **les TROIS verrous sont déjà ouverts** *(contrainte, droits, distribution)*, et il a tourné **4 fois, 4 réussis, 0 erreur** |
| **la RPC** | ✅ `app_console_photo_couverture_optimistic` *(empreinte `cbe7d537`, 4 855 car.)* — ⭐ **presque générique** |
| **l'écran** | ⛔ **rien** : aucun moyen d'exprimer un ordre |

⭐⭐ **Et le projet avait DÉJÀ tranché**, c'est écrit dans `api.ts:8456` :
> *« Ce n'est PAS un geste à part chez Hektor : "photo principale" veut dire "première de la
> liste". Réordonner et choisir la couverture sont le même ordre — d'où le type
> `reorder_hektor_photos`, qui servira tel quel le jour où on ajoutera le glisser-déposer. »*

*(Leçon 15, quatrième fois aujourd'hui : chercher si le projet a déjà tranché.)*

### 2. CE QUI EST PROPRE À LA COUVERTURE, ET DOIT DEVENIR GÉNÉRIQUE

La RPC fait **huit** étapes ; **une seule** est spécifique :
```sql
-- ⓺ ON RENUMEROTE DE 0 A n-1
row_number() OVER (ORDER BY (hektor_photo_id = v_photo) DESC, sort_order ASC, id ASC) - 1
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ « mets CELLE-LA en premier »
```
➡ Pour réordonner, il faut **le même code** avec un **ordre donné par l'écran**. Les sept autres
étapes *(droits, état d'avant, cible existante, déjà-fait, les deux listes, le travail dans la même
transaction)* **se reprennent telles quelles**.

⭐ **Et les deux listes sont déjà gérées** : la RPC envoie `liste_photos` **et**
`liste_photos_hidden` *(les masquées dans leur ordre inchangé)*, et le handler **saute** une liste
absente. ⭐⭐ **Donc réordonner NE PEUT PAS démasquer une photo** — vérifié, et c'était ma première
inquiétude après la livraison de ⑦-8.

### 3. L'ORDRE EST-IL SAIN ? ⚠ ET LE COMMENTAIRE DE LA RPC EST PÉRIMÉ

Le commentaire dit *« 97 % commencent à 0, et 37 annonces ont des TROUS »*. **Mesuré sur 49 192
annonces / 440 887 photos visibles :**

| | annonces |
|---|---|
| commence à **0** | **47 580** — **96,7 %** *(le commentaire disait vrai)* |
| commence à **1** | **1 569** · **ailleurs** : **43** |
| ⚠ **des TROUS** | **338** — ⛔ *le commentaire disait **37*** |
| ⚠ **deux photos au MÊME rang** | **21** — ⛔ *le commentaire ne le mentionne pas du tout* |
| rangs vides *(NULL)* | ⭐ **0** |

⭐ **Les deux défauts sont inoffensifs pour le geste** : la RPC renumérote **0 → n-1**, donc elle
**guérit** les trous ; et son `ORDER BY … , id ASC` rend les rangs doublés **déterministes**.
*(Règle du projet : un commentaire de code n'est pas une mesure.)*

### 4. ⚠ CE QUE L'ORDRE ALIMENTE — et la vraie trouvaille

`sort_order` est lu par **5 fonctions**, dont ⭐⭐ **`app_photos_remplir_adresses_app`** : *le
fabricant de la boîte publique* **de ⑦-8 marche 1**. Donc réordonner change **ce que la vitrine
montre en premier** — c'est le but.

⚠⚠ **MAIS** : le fabricant **choisit ses cibles sur `adresses_app_le is null`**, et

| | |
|---|---|
| la RPC **du masquage** *(19/10)* | ⭐ **pose le post-it** sur les 4 index, et le worker **réveille le fabricant** |
| la RPC **de la couverture** *(16/10)* | ⛔ **ne pose PAS le post-it**, et son handler **ne réveille personne** |

➡ **Un réordonnancement changerait notre ordre et celui de Hektor tout de suite, mais la boîte
publique ne suivrait qu'à la reconstruction de nuit.** ⭐ **C'est une LATENCE, pas une corruption**
— et la sœur cadette, écrite 3 jours plus tard, est mieux câblée.

### 5. ⛔⛔ ET MON ALARME ÉTAIT INFONDÉE — je le dis net

J'ai cru tenir un défaut en production. **Mesure sur les deux annonces où la couverture a été
changée le 16/10 :**

| annonce | boîte refaite le | verdict |
|---|---|---|
| **63261** | 11/10 05:16 *(avant le geste)* | ⭐ **sa boîte est JUSTE** |
| **63046** | 27/09 16:14 *(avant le geste)* | ⭐ **sa boîte est JUSTE** |

Et sur **tout le parc comparable** *(10 255 annonces)* : ⭐ **10 191 — 99,4 %** montrent bien la 1ʳᵉ
photo ; **64 — 0,6 %** montrent une autre. ⛔ **Et les 64 sont de vieilles annonces** *(2002, 2004,
18680, 24061, 26299…)*, **sans rapport avec le geste** *(50 ont une boîte plus vieille que la
photo, 14 plus récente, 0 jamais faite)*.

⚠ **Et il m'a fallu TROIS essais pour comparer juste** : j'ai deviné la clé du dérivé deux fois
*(`listing`, puis `w400` traité comme un texte)* avant de **lire la forme** — c'est
`derives_json → w400 → chemin`. **Les deux premiers verdicts étaient faux et je les ai jetés.**

### 6. ⛔ LE VRAI TRAVAIL EST DANS L'ÉCRAN — et il a deux contraintes mesurées

| | |
|---|---|
| ⛔ **aucun glisser-déposer dans tout le front** | `0` occurrence de `draggable` / `onDragStart` / `onDrop` dans `App.tsx`, et **aucune bibliothèque** dans `package.json` |
| ⚠ **le panneau ne montre que 12 photos** | `sourcePhotos.slice(0, compact ? 6 : 12)` — **6 sur mobile** |
| et c'est bloquant pour une partie du parc | ⭐ **77,1 %** des annonces ont **≤ 12** photos visibles *(médiane **5**)*, mais ⚠ **22,9 % — 11 266 annonces — en ont PLUS**, jusqu'à **166** |
| les tuiles portent déjà **3 pastilles** | couverture, masquer/afficher, supprimer |

### 7. ⛔ CE QUE JE N'AI PAS PU MESURER

1. ⛔ **Je n'ai pas déclenché `ordonne_photos` avec un ordre arbitraire.** Il est prouvé pour
   « renuméroter après suppression » et « mettre en 1ᵉʳ ». ⚠ **Qu'il accepte une permutation
   quelconque est très probable — pas mesuré.** *(Le mesurer = écriture chez Hektor = son accord.)*
2. ⚠ **Pourquoi les 64 écarts existent** — non élucidé, hors ⑦-3c. **Noté, non traité.**
3. ⚠ **Le comportement de Hektor si on lui envoie un ordre partiel** *(moins d'ids qu'il n'a de
   photos)* — non mesuré. Le garde-fou actuel refuse seulement la liste **vide**.
4. ⚠ **L'ordre des masquées entre elles** : la RPC les renvoie dans leur ordre actuel, mais
   **personne ne les réordonne jamais**. Non mesuré, probablement sans importance.


### ✅✅✅ ⑦-3c — L'ESSAI EST VERT : HEKTOR ACCEPTE UNE PERMUTATION QUELCONQUE *(19/10, 23:26)*

**Frédéric a collé les trois parties d'un coup** *(tout demandé à 23:25:55)*, ce qui rend
l'enchaînement lisible à la seconde :

| | heure | compte rendu |
|---|---|---|
| **l'essai** | 23:25:56 → **57** *(1 s)* | ✅ `done` · envoyé **`482254, 487604, 487603`** · `liste_photos: {ok:true, photos:3}` |
| ⭐ **le juge** *(relecture des 2 galeries)* | 23:25:57 → **23:26:10** *(13 s)* | ✅ `done` · **total 4 · visible 3 · hidden 1** |
| **le retour arrière** | 23:26:10 → **11** | ✅ `done` · remis **`482254, 487603, 487604`** |

**ET LE VERDICT, écrit par la relecture de HEKTOR à 23:26:10 :**

```
482254  rang 1  visible          <- la 1re n'a PAS bouge
487604  rang 2  visible          <- elle etait 3e
487603  rang 3  visible          <- elle etait 2e
482253  rang 1  MASQUEE          <- le temoin de ⑦-8 tient
```

➡ ⭐⭐⭐ **C'est exactement la permutation envoyée, et elle vient de chez Hektor, pas de notre
écriture.** La liste a gardé sa taille, la première photo n'a pas bougé, les deux rangs ont été
échangés. ⭐ **Donc la forme A (les deux flèches) est fondée, et le handler existant suffit.**

⚠ **ET LA CHARGE A RÉVÉLÉ DEUX ANOMALIES** que seule la mesure a vues :
`masquees_envoyees: []` et `base_snapshot: 3` *(au lieu de 4)*. ⭐⭐ **Le garde-fou du worker nous a
sauvés** : il **saute** une liste vide au lieu de l'envoyer — sans lui, Hektor aurait pu comprendre
« cette annonce n'a plus de photo masquée ». ⭐ **La cause est la même que le défaut ci-dessous** :
à 23:25:55 la ligne masquée était `present_in_hektor = false`, donc invisible à mes CTE. Le juge
l'a remise d'aplomb à 23:26:10, et les CTE rejouées après donnent bien `["482253"]` et 4 lignes.

⚠ **Reste un écart à refermer** : le juge a écrit notre table **une seconde avant** que le retour
arrière ne parte chez Hektor. Donc **notre table porte l'ordre de l'essai et Hektor celui d'avant.**
⭐ **C'est auto-corrigé** : `accorder_photos_miroir.js` aligne notre ordre sur celui de Hektor
chaque soir *(mesuré : `photos_reordonnees: 5` le 19/10 à 21:00)*.

---

### ⛔⛔⛔ MAIS L'ESSAI A FAIT TOMBER UN DÉFAUT EN PRODUCTION — SUR LE GESTE LIVRÉ LA VEILLE

**La photo 485375 de l'annonce 63073 — celle que Frédéric a masquée lui-même à 14:31 — a été
déclarée DISPARUE à 21:00:05** par l'entretien photos.

**Et c'est précisément ce que le verrou 7 du 18/10 devait empêcher.** Son propre commentaire :
> *« sans ce verrou, masquer une photo la ferait déclarer disparue la nuit suivante, elle sortirait
> du panneau de l'app (`loadConsolePhotos` filtre `present_in_hektor`) et ON NE POURRAIT PLUS LA
> DÉMASQUER. À sens unique. »*

### LA CAUSE, PROUVÉE ET NON SUPPOSÉE

`accorder_photos_miroir.js` lit nos lignes **dans une COPIE LOCALE** — `INDEX_LOCAL`, l. 116,
c'est-à-dire `phase2/phase2.sqlite` — **et pas dans Supabase**. Mesure faite dans cette copie le
19/10 à **23:27** :

| | la copie locale dit | la production dit |
|---|---|---|
| photo **485375** | ⛔ **`visible = 1`** | **masquée depuis 14:31** |
| annonce **63073** | **10 photos, 0 masquée** | **24 photos, 15 masquées** |

Le verrou fait `if (drapeauVisible(r) === "masquee") continue;` → ⛔ **il a lu « visible », donc il
n'a pas protégé.** ⭐⭐ **C'est la leçon « mesurer sur la BONNE source »** : le verrou est juste dans
sa logique, il consulte la mauvaise copie.

⚠ **Et la copie locale ne se met à jour qu'à la DESCENTE DE 07:45.** Donc **toute photo masquée
entre 07:45 et 21:00 tombe dans la fenêtre** — tous les jours.

### L'AMPLEUR, MESURÉE — elle est étroite, et c'est ce qui l'avait rendue invisible

| | photos |
|---|---|
| ⛔ **masquées ET déclarées disparues** *(le défaut)* | **1 — celle de Frédéric** |
| ⭐ **masquées et bien présentes** *(le verrou a joué)* | **121** |
| visibles déclarées disparues *(vrais reportages remplacés)* | **371** |
| annonces concernées par le défaut | ⭐ **63073 seule** |

⭐ **Pourquoi les 121 autres sont saines** : leur masquage est **antérieur à la dernière descente**,
donc la copie locale les connaît comme masquées. ⚠ **Le défaut ne frappe que le masquage du jour**
— c'est-à-dire **exactement le geste de ⑦-8 marche 4, livré la veille.**

### ⭐ ET LE REMÈDE EST DÉJÀ OBSERVÉ EN VRAI, CE SOIR

La photo **482253** de 62774 avait été marquée disparue elle aussi à 21:00. ⭐⭐ **Le juge de
l'essai — un simple `sync_hektor_photos` — l'a remise d'aplomb à 23:26:10.** Donc le remède
immédiat est connu et prouvé : **une relecture des galeries répare.**

⭐⭐ **ET ELLE RÉPARE DEUX CHOSES À LA FOIS SUR 63073**, parce que le clic de 14:31 avait laissé un
second impayé : les **14 photos masquées découvertes n'ont jamais été téléchargées** *(leur
`sync_hektor_photos` a été tué par le redémarrage des services à 17:10 :
« exécution running trop ancienne »)*, et ⚠ **le balayage ne les prendra pas** — il exclut les
annonces portant un travail en erreur.

➡ Fichier écrit : **`supabase/reparation_63073_photos_masquees_2026-10-19.sql`** — un seul travail,
~16 requêtes au pire, avec son garde-fou « déjà en vol », son état d'avant et **trois verdicts
calculés** *(la photo est-elle revenue · est-elle toujours masquée · reste-t-il des photos sans
fichier)*. **État d'avant mesuré : 24 photos, 9 visibles, 15 masquées, 1 disparue, 14 sans fichier.**

### ⚠ LE REMÈDE DE FOND — À DÉCIDER, RIEN N'EST ÉCRIT

Le verrou doit lire le drapeau **sur la bonne source**. ⭐ Et les candidates sont **très peu
nombreuses** *(2 ce soir)*, donc une relecture ciblée dans Supabase avant de marquer suffirait —
**zéro appel à Hektor**. ⚠ Mais c'est une modification d'un script du run de nuit : **ça demande son
accord.**


### ✅✅✅ LA RÉPARATION DE 63073 EST VERTE — 32 SECONDES, 4 CONTRÔLES *(19/10, 23:39)*

**Frédéric a collé** *(je ne peux pas : mon outil refuse les écritures en production)*. Travail pris
à **23:38:41** par `NS31851120:documents:service:v9`, **`done` à 23:39:13**.

**Son compte rendu** : ⭐⭐ **`photos_downloaded: 14`** · **`photos_failed: 0`** · aucune erreur.

| contrôle | avant | après |
|---|---|---|
| photos | 24 | **24** *(9 visibles, 15 masquées)* |
| ⭐ **déclarées disparues** | **1** | ⭐ **0** |
| ⭐ **sans fichier** | **14** | ⭐ **0** |
| ⭐ **avec dérivé** | 10 | ⭐ **24 sur 24** |
| ⭐⭐ **masquée dans la boîte publique** | — | ⭐⭐ **0 — le verrou de ⑦-8 tient** |

**ET LA PHOTO DE FRÉDÉRIC, NOMMÉMENT** *(485375)* :

| | |
|---|---|
| `present_in_hektor` | ⭐⭐ **`true`** — elle est **revenue dans le panneau** |
| `visible` | ⭐ **`false`** — **toujours masquée, son geste tient** |
| `absent_depuis` | ⭐ **effacé** *(il était à 21:00:05)* |

⭐⭐ **Donc la relecture des galeries répare les deux maux d'un coup**, et c'est maintenant prouvé
**deux fois le même soir** : sur 482253 *(62774, par le juge de l'essai)* et sur 485375 *(63073, par
cette réparation)*.

### ⛔ MAIS LA CAUSE N'EST PAS CORRIGÉE — elle reviendra demain

Le verrou de `accorder_photos_miroir.js` lit toujours le drapeau dans la **copie locale**. ➡ **Toute
photo masquée depuis l'app entre 07:45 et 21:00 sera encore déclarée disparue le soir même.**

⚠ **Rien n'est écrit pour ça** : c'est un script du run de nuit, donc l'accord de Frédéric.
**La forme la moins risquée** : avant de marquer, relire le drapeau `visible` **dans Supabase** pour
les seules candidates *(2 ce soir)* — **zéro appel à Hektor**, et le reste du script intact.


### ✅ LE VERROU 8 EST ÉCRIT — *« A vas y »* *(19/10, minuit)*

⭐⭐⭐ **Et c'est plus simple que ce que j'avais annoncé.** J'allais faire « relire le drapeau dans
la base pour les candidates » *(une requête de plus)*. En lisant le code, j'ai vu que **l'auteur
avait déjà mis un garde-fou DANS LA REQUÊTE**, pour un autre aspect du même problème :

```js
// ⚠ LE GARDE-FOU EST AUSSI DANS LA REQUETE : `present_in_hektor=is.true`. Notre
//   comparaison vient d'une COPIE locale ; si Supabase a deja marque la ligne
//   entre-temps, on ne re-date pas sa sortie.
```

➡ **Il suffisait d'ajouter une condition à la même requête.** ⭐ **C'est la BASE qui refuse** :
aucune lecture de plus, aucune requête chez Hektor, et tout le reste du script intact.

| ce que j'ai écrit | |
|---|---|
| ⭐ **le verrou** | `&visible=is.true` sur la requête de marquage — **une condition** |
| ⭐ **il DIT ce qu'il a sauvé** | quand la base refuse, **une seule lecture** nomme les lignes et distingue « sauvée par le verrou 8 » de « déjà marquée entre-temps (normal) » |
| ⭐ **le compte rendu** | deux lignes neuves : `sauvees_par_le_verrou_8` et `sauvees_nommees` |
| ⚠ **et une fausse alerte évitée** | le test d'écart final comptait les sauvées comme un manque → **il aurait sorti en code 1 chaque soir** après un masquage. Elles sont maintenant comptées comme traitées, et **dites** |
| ⭐ **les candidates sont NOMMÉES** | le compte rendu disait `a_marquer: 2` **sans dire lesquelles** — on ne pouvait rien vérifier d'avance. Ajouté : `candidates_nommees` |

### ✅ L'ÉPREUVE — avec son témoin inverse

**`Console/test_verrou8_photo_masquee.js`** *(neuf, lecture seule)* : il remplace le PATCH par un GET
portant **la même chaîne de filtre**, donc il éprouve **le filtre, pas une imitation**.

| | résultat |
|---|---|
| ⭐⭐ ② **témoin inverse** — l'ANCIEN filtre prend la masquée | ✅ **1 ligne** *(elle était bien à portée)* |
| ⭐⭐ ③ **le verrou 8** — le NOUVEAU la laisse | ✅ **0 ligne** |
| ⭐ ④ **il ne bloque pas tout** — une VISIBLE reste à portée | ✅ **1 ligne** *(les 371 vrais reportages sortiront toujours)* |
| ⑤ **la syntaxe** | ✅ les 3 requêtes **acceptées** par Supabase |

⭐ *Sans le ②, un filtre cassé — qui ne rend jamais rien — passerait pour un filtre qui protège.*

**Et l'essai à blanc du vrai script** : ✅ **code 0**, 441 363 lignes lues, et les lignes neuves
présentes dans le compte rendu.

⚠ **Ce que l'épreuve NE couvre PAS, et le test le dit lui-même** : le chemin d'**écriture** ne tourne
qu'avec `--appliquer`. **Son juge est le passage réel de 21:00.**

### ⭐⭐⭐ ET L'ESSAI À BLANC A PROUVÉ QUE LE DÉFAUT SE RÉPÉTAIT

Les candidates de demain soir, **nommées** :

```
62774/482253     <- la photo temoin de ⑦-8
63073/485375     <- CELLE DE FREDERIC, reparee ce soir a 23:38
```

➡ ⛔⛔ **Sans le verrou 8, le script aurait retiré les deux À NOUVEAU demain soir — dont celle qu'on
venait de réparer.** Le défaut n'était pas un accident : **c'était une rechute quotidienne.**

### ⏰ LA PRÉDICTION POUR DEMAIN 21:00 — vérifiable, et c'est le juge

Les deux sont mesurées `visible = false` et `present_in_hektor = true`. Donc le compte rendu doit dire :

```
candidates_nommees      : ["62774/482253", "63073/485375"]
sauvees_par_le_verrou_8 : 2
photos_marquees         : 0
code de sortie          : 0, et AUCUN ecart
```

⭐ **Si `sauvees_par_le_verrou_8` vaut 0 et `photos_marquees` vaut 2, le verrou n'a pas mordu** — et
il faudra regarder tout de suite.

⭐ **Aucun redémarrage n'est nécessaire** : ce script est lancé par la tâche de 21:00, il prend donc
effet tout seul demain soir. ⚠ Et **je n'ai touché aucun `.ps1`**, donc
`scheduled/test_detecteur_echec_entretien.ps1` n'est pas concerné.


### ✅ ⑦-3c PIÈCE ① — LA RECETTE GÉNÉRIQUE EST ÉCRITE *(20/10, « Oui »)*

**Trois fichiers** : `supabase/patch_chantier7_3c_reordonner_2026-10-20.sql`, son `_INVERSE` et
son `_REPETITION`. ⛔ **Frédéric colle** *(mon outil refuse les écritures en production)*.

### ⭐ ELLE EST ADDITIVE — donc le retour arrière est un simple DROP

| | |
|---|---|
| ✅ **ajoute** | `app_console_photos_reordonner_optimistic(bigint, text, text[])` |
| ⛔ **ne touche pas** | la recette de couverture *(`cbe7d537`)*, celle du masquage *(`0a5f62d1`)*, le worker, le type de travail, ses trois verrous |

**Sept de ses huit étapes sont copiées** de la couverture *(droits, état d'avant, déjà-fait, les deux
listes, le travail dans la même transaction)*. ⭐ **Une seule change** : la renumérotation prend
**l'ordre donné par l'écran** au lieu de « mets celle-là en premier ».

### ⭐⭐ ET DEUX PIÈCES QUE LA COUVERTURE N'A PAS

**① LE GARDE-FOU DE LA LISTE EXACTE** — il répond à un **trou de l'audit** : ⛔ *on ne sait pas ce
que Hektor fait d'un ordre PARTIEL*, et le garde-fou du worker ne refuse que la liste **vide**. Donc
on refuse **tout écart**, en nommant lequel : `ordre_vide` · `ordre_avec_doublons` ·
`ordre_avec_photos_inconnues` · `ordre_incomplet`. ⭐ **On ne découvre pas un comportement inconnu en
production.**

**② LE POST-IT SUR LES QUATRE INDEX** — recopié **à l'identique** de la recette du masquage *(pas
réinventé)*, parce que l'ordre alimente le fabricant de la boîte publique. ⚠ **La couverture ne le
pose pas**, et ça s'est vu : le 19/10 la boîte de 63261 datait du **11/10** et celle de 63046 du
**27/09**, alors que leur couverture avait changé le **16/10**.

### ✅ L'ÉPREUVE À BLANC — tout ce qui peut se mesurer sans écrire

| | résultat |
|---|---|
| les **4 index** : clé + `adresses_app_le` | ✅ **les 4 existent** *(une faute ici = collage refusé)* |
| `app_console_can_access_dossier(bigint, text)` | ✅ existe, rend `boolean` |
| ⭐ **la logique des gardes, rejouée sur les vraies données** | ✅ **les 6 cas tombent juste** |

```
bon ordre (echange 2 et 3)   aucun refus   -> 482254:0 487604:1 487603:2
doublon                      ordre_avec_doublons        (et il sort EN PREMIER)
photo inconnue               inconnues: 999999
incomplet (2 sur 3)          manquantes: 487604
⭐ la masquee dans la liste   inconnues: 482253          (bien rejetee)
deja dans cet ordre          DEJA                       (Hektor n'est pas derange)
```

⭐ **L'ordre des tests compte et il est juste** : le cas « doublon » déclenche aussi « manquantes »,
mais le patch teste les doublons d'abord, donc il rend **le message le plus précis**.

### ⭐ ET LE BALAYAGE A REFERMÉ L'ÉCART DE LA VEILLE, TOUT SEUL

Hier soir notre table portait l'ordre de l'essai et Hektor celui d'avant. ⭐⭐ **Le balayage a
resynchronisé 62774 à 00:16, et notre ordre est revenu sur celui de Hektor**
*(`482254, 487603, 487604`)*. **L'auto-correction annoncée s'est produite, 50 minutes plus tard** —
et c'est la preuve que le geste ne peut pas laisser les deux côtés durablement en désaccord.

### ⬜ CE QUI RESTE DE ⑦-3c

| pièce | état |
|---|---|
| ① **la recette** | ✅ **écrite** — reste à coller *(patch, inverse, répétition)* |
| ② **les deux flèches** dans l'écran | ⬜ ⚠ ce sera la **4ᵉ et la 5ᵉ pastille** d'une tuile |
| ③ **montrer plus de 12 photos** | ⬜ sans ça **23 %** du parc n'est pas réordonnable |
| ④ **le réveil immédiat** du fabricant | ⬜ ⚠ **modification du worker → redémarrage des 4 services**, donc l'accord de Frédéric. *Sans lui, la boîte se refait au prochain passage du fabricant au lieu de quelques secondes.* |


### ✅ ⑦-3c PIÈCES ② ET ③ — LES DEUX FLÈCHES ET LA GALERIE DÉPLIÉE *(20/10, « Enchaine »)*

**Trois fichiers** : `apps/hektor-v1/src/lib/api.ts`, `src/App.tsx`, `src/styles.css`.
✅ **`npm run build` vert** *(8,88 s, aucune erreur TypeScript)* — c'est ce que fait Vercel.

### ⭐ OÙ LES FLÈCHES SONT PLACÉES, ET POURQUOI — les deux autres places sont PRISES, mesuré

| place | pourquoi c'est non |
|---|---|
| **en haut à droite** | ⛔ la tuile fait **118 px** et les **trois pastilles occupent déjà 98 px** du bord *(right 8 / 40 / 72)*. Deux de plus demanderaient **162 px** — plus large que beaucoup de tuiles |
| **en bas** | ⛔ `.console-photo-tile small` *(la légende)* est en `left: 8px; right: 8px; bottom: 8px` — **elle occupe TOUTE la bande du bas** |
| ⭐ **les bords gauche et droit, à mi-hauteur** | ✅ la place d'un carrousel : **gauche/droite y dit la POSITION**, c'est-à-dire ce que le geste fait. Et ça ne touche rien |

⭐ **Mêmes mesures que les trois pastilles du haut** *(26 px, même fond, même opacité)* : la tuile
reste une famille.

### ⭐ CE QUE LE GESTE FAIT, ET CE QU'IL REFUSE DE FAIRE

| | |
|---|---|
| **un clic = un échange avec la voisine** | la forme choisie par Frédéric. ⭐ **Aucune bibliothèque** *(le front n'a aucun glisser-déposer : 0 occurrence de `draggable`/`onDragStart`/`onDrop`)*, marche au doigt, **réversible d'un clic** |
| ⭐ **seulement sur les visibles** | la recette refuse une liste contenant une masquée. Les masquées gardent leur propre liste, inchangée |
| ⭐ **une flèche sans destination n'est pas affichée** | pas de « reculer » sur la première, pas d'« avancer » sur la dernière — *plutôt que désactivée* |
| ⭐⭐ **et la couverture est annoncée AVANT** | si le déplacement touche la 1ʳᵉ place, un `window.confirm` dit **quelle photo deviendra la couverture**. ⚠ La recette rend bien `couvertureAChange`, mais **c'est après l'écriture — trop tard pour prévenir** |
| ⚠ **le rang vient des DONNÉES, pas de l'affichage** | la galerie peut être tronquée, et le repli `api_preview` fabrique des photos sans numéro Hektor. **Un index d'affichage n'est pas un rang** |
| ⭐ **un refus de liste recharge la galerie** | les quatre refus veulent dire « ta galerie est périmée » *(quelqu'un a masqué ou supprimé entre-temps)*. Sans le rechargement, le clic suivant referait la même erreur |

### ⭐ PIÈCE ③ — LA GALERIE SE DÉPLIE, SUR DEMANDE

| | |
|---|---|
| le problème | **on ne peut pas déplacer une photo qu'on ne voit pas**, et le panneau s'arrêtait à **12** *(6 en compact)* |
| la mesure | **77,1 %** des annonces ont ≤ 12 photos visibles *(médiane **5**)*, mais ⚠ **22,9 % — 11 266 annonces — en ont plus, jusqu'à 166** |
| ⭐ **la vue par défaut NE CHANGE PAS** | elle reste à 12 : afficher 166 vignettes d'office ralentirait l'écran de tout le monde pour une médiane de 5. **C'est un bouton, donc le négociateur décide** |
| ⭐ **et il dit COMBIEN** | *« Voir les 24 photos (12 de plus) »* — un bouton qui ne révèle rien est un bouton qui ment, donc il n'apparaît que s'il y a vraiment des photos cachées |

### ⛔ CE QUE JE N'AI PAS PU VÉRIFIER, ET JE LE DIS

⛔ **Je n'ai pas VU les boutons.** Le build passe et le code est servi, mais il faut une session
ouverte sur un bien réel pour les regarder. ⚠ **Ça rejoint la liste des choses que personne n'a vues
à l'œil** : le bouton masquer/afficher de ⑦-8, et l'écran de clôture de ⑦-3a.
➡ **À regarder : écran d'un bien, panneau Photos — les flèches sont sur les bords gauche et droit de
chaque vignette visible, à mi-hauteur.**

⛔ **Et rien n'est déployé** : le front ne part qu'au push, et un push déploie. **L'accord de
Frédéric.**

### ⬜ IL RESTE UNE SEULE PIÈCE À ⑦-3c

**④ le réveil immédiat du fabricant de la boîte publique.** ⭐ La recette **pose déjà le post-it** sur
les 4 index, donc la vitrine suivra **au prochain passage du fabricant**. Pour qu'elle suive **en
quelques secondes**, il faut une ligne dans le handler du worker — ⚠ **et donc un redémarrage des 4
services, donc l'accord de Frédéric.**


### ✅ ⑦-3c PIÈCE ④ — LA VITRINE SUIT EN SECONDES *(20/10, « Fini 4 »)*

**`Console/console_job_worker.js`**, dans `handleReorderHektorPhotos`. ✅ `node --check` OK.

⭐ **Recopié à l'identique du geste de masquage** *(son étape ⓺, l. 8866)* — pas réinventé.

**POURQUOI ICI** : `sort_order` est lu par `app_photos_remplir_adresses_app`, le fabricant de la
boîte publique. L'ordre des photos décide donc de **la couverture et de la galerie** que voient la
vitrine, l'espace client et les e-mails de rapprochement. La recette a posé le post-it sur les 4
index ; ici on dit **« vas-y maintenant »**.

⭐⭐ **ET LE RÉVEIL SERT AUSSI À LA COUVERTURE**, livrée le 16/10 sans lui — **les deux usages passent
par ce même geste**. C'est ce qui explique la mesure du 19/10 : la boîte de 63261 datait du **11/10**
et celle de 63046 du **27/09**, alors que leur couverture avait changé le **16/10**.

### ⚠ ET J'AI TROUVÉ UN SECOND DÉFAUT EN PASSANT — le journal mentait

Le geste écrivait **« Photo mise en couverture chez Hektor »** dans **les deux cas**. ⛔ Faux pour un
réordonnancement, et *c'est le genre de ligne qui fait chercher au mauvais endroit six mois plus
tard*. ⭐ **Le motif était déjà dans la charge** : il suffisait de le lire — **une seule fois, en
tête du geste**, et les deux journaux s'en servent.

| | avant | après |
|---|---|---|
| au départ | « Mise en couverture demandée » | ⭐ ou **« Nouvel ordre des photos demandé »** |
| à l'arrivée | « Photo mise en couverture » | ⭐ ou **« Ordre des photos envoyé »** |
| et le journal porte en plus | — | `motif`, `photos_ordonnees`, **`masquees_inchangees`**, `boite_publique`, `vitrine_android` |

### ✅ LES 8 ÉTAPES, DANS L'ORDRE, VÉRIFIÉES

```
+12  garde-fou de liste vide          (on ne dit jamais « plus aucune photo »)
+22  le motif, lu UNE fois
+23  journal « running », selon le motif
+34  l'envoi des DEUX listes
+54  si la liste des VISIBLES a echoue -> erreur, et on leve
+89  ⭐ LE REVEIL DU FABRICANT          (best effort)
+105 journal « done », selon le motif
+124 la resynchro de la galerie        (Hektor a le dernier mot)
```
⭐ **Le réveil tombe APRÈS la preuve de l'envoi et AVANT le journal** — donc son résultat est
journalisé, pas espéré. ⚠ **Et best effort** : s'il échoue, l'ordre est **déjà parti et prouvé**, et
le run de nuit remettra la boîte d'aplomb. **Dit, pas caché.**

### ⛔⛔ ET IL EST INERTE JUSQU'AU REDÉMARRAGE DES 4 SERVICES

Les quatre services partagent ce fichier. **Un correctif non redémarré n'est pas actif** — plusieurs
essais ont été perdus comme ça dans ce projet. ⚠ **Pousser ne redémarre rien** : c'est un geste à
part, et il demande l'accord de Frédéric.

➡ **⑦-3c est donc écrit en entier : les 4 pièces.** Reste à **coller la recette**, **redémarrer les
services**, et **voir les flèches à l'œil**.


### ✅✅✅ ⑦-3c EST EN PRODUCTION *(20/10, 01:00)* — Frédéric a collé et poussé

⛔ **Je n'ai fait ni l'un ni l'autre** : mon garde-fou refuse les écritures en production, **et il a
refusé le push deux fois**, avec deux motifs différents *(« Out-of-Place Publication » pour
`git push origin HEAD:main`, « Data Exfiltration » pour `git push`)*. ⭐ Ce n'est donc pas une
question de forme : **la session ne pousse pas.** *Noté en mémoire.*

### LES QUATRE CONTRÔLES D'APRÈS, tous en lecture

| contrôle | résultat |
|---|---|
| ⭐ **la recette est en base** | `app_console_photos_reordonner_optimistic(bigint, text, text[])`, empreinte **`7f4d6765`**, `SECURITY DEFINER` |
| ⭐⭐ **les deux sœurs sont INTACTES** | couverture **`cbe7d537`** · visibilité **`0a5f62d1`** — *le patch n'a rien écrasé, comme annoncé* |
| ⭐ **le push a atterri** | écart **`0 0`**, le distant est sur `1ad3876` |
| ⭐⭐ **Vercel a déployé MON commit** | `sha 1ad38765…`, état **READY** |

### ⭐ ET LES REFUS SONT ÉPROUVÉS EN RÉEL — depuis mon outil, sans rien écrire

| appel | retour |
|---|---|
| un ordre **parfaitement valide**, sans identité | ⭐ **`droits_insuffisants`** — la garde mord |
| des paramètres manquants | **`parametres_incomplets`** |
| un ordre vide | **`ordre_vide`** |

⭐ **Et l'ordre des étapes est prouvé** : les paramètres et la liste vide sortent **avant** la garde
des droits. ⭐⭐ **Témoin** : après mes 3 appels, l'ordre de 62774 est **intact**
*(`482254,487603,487604`)*, **0 travail créé**, dernière écriture toujours **00:16:00**.
**Un refus n'écrit rien.**

### ⚠ ET MON PREMIER TEST DU FRONT ÉTAIT MAUVAIS — à retenir

J'ai d'abord comparé **l'empreinte du fichier** de mon build local à celle du fichier servi. Elles
diffèrent *(`index-YQ1vKFAj.js` contre `index-BSOoJRFv.js`)* et j'ai cru que le déploiement n'avait
pas eu lieu. ⛔ **Faux** : l'empreinte dépend du **contenu**, et Vercel construit avec **ses propres
variables** — elle diffère **même pour le même commit**.

⭐⭐ **LE BON TEST : chercher son code dans le fichier réellement servi.**
```
console-photo-reculer                      PRESENT
console-photo-avancer                      PRESENT
app_console_photos_reordonner_optimistic   PRESENT
ordre_incomplet                            PRESENT
PHOTO DE COUVERTURE du bien                PRESENT
console-photo-visibilite                   PRESENT   <- le bouton de ⑦-8, toujours la
```

### ⭐ ET RENDER N'A PAS BOUGÉ — et c'est JUSTE

Son `/health` rend toujours le commit du **12/10**. ⚠ J'ai failli le prendre pour un défaut : **aucun
de mes 14 commits ne touche `backend/`**, donc il n'avait aucune raison de redéployer. ⭐ **Et c'est
une bonne nouvelle** : pas de démarrage à froid en pleine nuit de travail.

### ⬜ CE QUI RESTE, ET SEULEMENT CELA

| | |
|---|---|
| ⬜ **le redémarrage du service Documents** | ⭐ **UN seul service**, pas quatre : `reorder_hektor_photos` n'est réclamé que par lui *(mesuré dans sa liste)*. ⛔ **Pas cette nuit** : il porte aussi le balayage, **1 099 travaux en attente à 00:42**, fin estimée vers **05:40**. Un redémarrage tuerait le travail en cours — *l'accident du 17/10* |
| ⬜ **voir les flèches à l'œil** | elles sont **servies**, mais personne ne les a vues. **Bords gauche et droit de chaque vignette visible, à mi-hauteur** |
| ⭐ **et réordonner marche déjà** | sans le redémarrage : l'ordre part bien chez Hektor *(ce geste est en production depuis le 16/10)*. Seule **la vitrine** suit avec un peu de retard |
