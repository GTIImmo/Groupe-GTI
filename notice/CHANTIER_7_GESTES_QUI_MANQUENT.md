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
| ⑦-3a | le **crayon** de la date de clôture, rubrique Mandat | ⬜ reçu du chantier ③ |
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
