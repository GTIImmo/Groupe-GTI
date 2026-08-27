# FEUILLE DE ROUTE — mise à jour le 25/08/2026, au soir

> **Refaite entièrement le 25/08 au soir**, après une journée d'essais en vraie grandeur qui a
> trouvé **cinq défauts que la relecture de code n'avait pas vus** — dont un que j'avais
> introduit le matin même. La méthode a changé : **on ne livre plus sans avoir exercé.**

**33 faites · 18 restantes · 4 supprimées · 1 dissoute · 1 annulée**

*Comptes recomptés tâche par tâche dans le plan maître le 25/08 au soir. « Faites » inclut les
sous-tâches d'identité (2bis, 4quinquies…), ce que les versions précédentes de cette feuille ne
faisaient pas — d'où l'écart avec le « 20 faites » d'hier. Les **18 restantes** sont la liste
exacte ci-dessous, et elles incluent **26bis**, qui n'avait jamais eu de numéro.*

---

## L'OBJECTIF, dans tes mots (21/08)

> *« Je veux que mon app et mon serveur fonctionnent comme une vraie solution métier, sauf que
> dans un premier temps les données rafraîchies proviennent d'une API avec Hektor, et que chaque
> modification doit lui être envoyée pour qu'il reste à jour — mandat, pub, etc. »*

Précisé le 25/08 : **Hektor n'est pas coupé d'un coup — il est réduit à un miroir** qui ne garde
que quatre services : **la diffusion portails · les numéros de mandat · la signature électronique ·
(peut-être) la clôture**. Tout le reste doit vivre chez nous.

Et c'est déjà mesuré : **7 workers sur 34 marchent sans Hektor · 3 seulement en dépendent
vraiment** — numéro de mandat, relance et annulation de signature. Soit exactement **A.1 et A.2**.

### Deux règles qui ne bougent pas

| | |
|---|---|
| **Les recherches sont la seule exception** | elles ne remontent plus à Hektor *(C.3, faite)* — mais voir l'**arbitrage ① ci-dessous : la création, elle, remonte encore** |
| **Les workers sont MAINTENUS, pas refondus** | *(règle ajoutée le 25/08)* un robot d'écriture qui fonctionne ne se touche que s'il est **cassé**. Ils meurent tous à la coupure : les rendre autonomes de Hektor n'a **pas de sens**. C'est ce qui a fait annuler C.5 |

---

## LES TROIS ÉTAPES · LES TROIS PISTES

```
   ETAPE 1  (aujourd'hui)   tout se fait dans HEKTOR ; seul Frederic a l'app
   ETAPE 2                  les negociateurs passent sur L'APP, Hektor leur est INTERDIT
   ETAPE 3                  la coupure

   PISTE 1 -- LE CODE       se construit maintenant, dormant  -> ne depend de personne
   PISTE 2 -- LES GENS      quand tu veux, un par un          -> ne depend que de toi
   PISTE 3 -- LES CONTRATS  A.1 / A.2 / A.3                   -> ne depend pas de toi
```

> ⚠ **Rien de la piste 1 ne rapproche la coupure.** Elle te rend **prêt**, pas **libre**.
> ⚠ **Quatre drapeaux dorment depuis 29 à 38 jours sans avoir jamais été allumés.**
> Construire dormant est facile ; **c'est l'allumage qui ne se fait pas.**

---

## OÙ NOUS EN SOMMES VRAIMENT — les quatre piliers de l'autonomie

| pilier | état |
|---|---|
| **Des identifiants propres** | annonce ✅ · contact ✅ · affaire ✅ · recherche ⏳ *(autre session)* |
| **Le serveur apprend de l'app** | ✅ la descente *(B.1)* · le domicile *(C.6)* · le contrat d'autorité *(C.7)* |
| **L'app sait écrire** | 🟡 en cours — **C.4 lot 1 fait**, le reste devant nous |
| **Un stockage propre** | ❌ **LE TROU** — voir **26bis**, la tâche la plus urgente |

### Le trou, mesuré le 25/08

```
   app_contact             355 687 lignes    -> les contacts ont un CORPS
   app_search_registry      76 889 lignes    -> les recherches ont un CORPS
   app_dossier              56 899 lignes ... mais 10 COLONNES  (identite pure)
   app_annonce_champ_app         0 ligne     (le domicile existe, il est vide)
```

**L'annonce a une identité chez nous, mais pas de corps.** Ses ~200 champs sont recomposés chaque
nuit **à partir du miroir de Hektor**. Le jour où il s'éteint, le serveur n'a plus de quoi les
recalculer.

### Et l'identité n'est pas encore distribuée

| objet | qui donne le numéro | quand |
|---|---|---|
| **affaire** | **l'app elle-même** *(plage réservée, séquence à 1 000 000)* | **à l'instant** — prouvé 2× le 25/08 |
| contact | le serveur local, script de nuit | le lendemain matin |
| annonce | le serveur local, script de nuit | le lendemain matin |

`app_dossier.id` et `app_contact_id` sont des **AUTOINCREMENT locaux** remplis la nuit : ce sont des
**registres** *(ils enregistrent après coup)*, pas des **distributeurs** *(ils ne délivrent pas au
moment de la création)*. Aujourd'hui c'est invisible — **Hektor donne l'identité, instantanément**.
Le jour J, plus personne ne la donne. → **E.4**, et le patron existe déjà : celui de l'affaire.

---

# ✅ CE QUI EST FAIT — on n'y revient plus

| bloc | tâches |
|---|---|
| **Identité** | **1** irremplaçable rattaché · **2** recalculable supprimé · **3** numéro d'annonce nullable · **4** identité des transactions *(28 980 affaires numérotées, clé basculée)* |
| **0 — protéger** | **0.1** sauvegarde de nuit · **0.2** règle « le miroir ne se supprime jamais » · **0.4 0.5 0.6** fermetures d'accès public · **0.7** audit des 85 fonctions · **0.8** correctif `conflict = false` |
| **B — le serveur apprend** | **B.1** la descente *(110 tables, 1 337 162 lignes)* · **B.2** 10 doublures *(174 720 lignes)* · **B.4** le comparateur · **B.5** la tâche `GTI Descente` 07:30 |
| **C — l'app auteur** | **C.3** porte des recherches fermée · **C.1'** une saisie ne se perd jamais · **C.2a** relecture contacts · **C.2b** `app_contact` *(355 687 numéros)* · **C.12** sortie de conflit contacts · **C.6** domicile de l'annonce · **C.7** contrat d'autorité · **C.14** titre français + calque lu par l'en-tête |
| **C.4 lot 1** | **une affaire peut naître dans l'app** — séquence réservée à 1 000 000, adoption au retour de Hektor. **Prouvé 2 fois le 25/08** |
| **E** | **E.0** l'étude « où en sommes-nous » |
| ❌ dissoute | **C.8** — ses deux moitiés n'étaient pas des tâches |
| ❌ **annulée** | **C.5** — voir ci-dessous |

## ❌ C.5 — annulée le jour même, et pourquoi ça compte

C.5 (matin du 25/08) faisait décider l'app du mandat d'une transaction. **Résultat : l'offre est
partie sans mandat, en silence.**

Hektor n'identifie pas un mandat par un nombre : son formulaire attend **`<id>-<FAMILLE>`** —
`648-PROTEXA`, `9887-HEKTOR` — parce qu'il tient **deux registres parallèles**. C.5 envoyait `648`.
Aucune option ne correspond → *« mandat non renseigné »*, **sans erreur**.

**Le retour arrière a été fait et vérifié en vraie grandeur** : offre 33026 *(avec C.5)* → **sans
mandat** ; offre 33027 *(après)* → **mandat 648**. Même annonce, même acquéreur.

> **La leçon, à garder** : le worker **recopie** la valeur de Hektor, il ne la reconstruit pas.
> Et la justification que j'avais donnée — *« il n'y aura plus de HTML à lire à la coupure »* —
> **était sans objet : le worker meurt avec Hektor.**

---

# 🛤 PISTE 1 — LE CODE · *se construit maintenant, dormant · n'attend personne*

## ⚠ C.16 — LES CONTACTS NE SONT JAMAIS REBALAYÉS · **et 611 « contacts » n'existent pas**

*Trouvé le 26/08, parce que Frédéric a demandé : « as-tu vérifié entièrement mon projet ? »*

### Le run des contacts est en delta, pas en balayage

Contrairement aux annonces *(balayage complet chaque nuit — 2 847 pages)*, **les contacts ne sont
revus que s'ils ont bougé**. Le listing complet n'a pas été rebalayé **depuis mai** : 284 269
contacts ont pour dernière vue `2026-05`.

> **Si Hektor archive ou supprime un contact, nous ne l'apprenons pas.**

### L'écart, et ce que l'essai a montré

Hektor déclare **348 053** contacts · notre miroir en a **355 712** — **+7 659**.

Échantillon stratifié de **300 contacts**, interrogés un par un :

| strate | population | échantillon | existent | absents |
|---|---|---|---|---|
| actifs | 171 001 | 120 | **120** | **0** |
| archivés | 184 100 | 120 | 117 | **3** *(2,5 % ≈ 4 600)* |
| sans indicateur | 611 | 60 | 0 | **60** *(100 %)* |

### 🔴 Les 611 ne sont pas des contacts supprimés — ce n'en ont jamais été

```
   hektor_contact_id  56974
   nom / prenom       GRASSET / Damien
   raw_json           {"id": "56974"}     <-- la charge ne contient QUE l'identifiant
```

Ce sont des **références orphelines** : une annonce, une offre ou un mandat de Hektor cite un
identifiant de contact, nous en gardons le nom — et `ContactById` répond **404**. **C'est une
incohérence dans les données de Hektor**, que le miroir a fidèlement recopiée.

Ce n'est **pas** de la déduplication : sur 11 absents testés, **2 seulement** appartiennent à un
groupe de doublons *(le parc en compte pourtant 37 144)*.

### Écarté, avec preuve

doublons d'identifiant *(355 712 = 355 712, en texte comme en entier)* · périmètre d'agence *(la
somme par agence **égale exactement** le total)* · filtre `type` *(`type=0` rend le total ; les
types se chevauchent — un contact peut être propriétaire **et** acquéreur)*.

### ⚠ Une erreur à moi, corrigée

J'avais expliqué les 7 659 par « des contacts supprimés que nous accumulons ». **Faux deux fois** :
la règle « on ne supprime jamais » date du **22/08**, elle ne peut pas expliquer un écart
antérieur ; et **les actifs ne montrent aucune suppression**. Frédéric a refusé l'explication, il
avait raison.

---

## 🔴 C.15 — LE RUN NE VOIT QU'UN TYPE D'OFFRE SUR SIX · **LE PLUS GROS TROU CONNU**

*Trouvé le 26/08, parce que Frédéric a refusé deux fois ma conclusion.*

`sync_raw.py` appelle `ListAnnonces` **sans le paramètre `offre`**. Sans lui, Hektor ne rend
**que les ventes**.

| type d'offre | actives | archivées | total |
|---|---|---|---|
| **`0` vente** — tout ce que le run voit | 22 424 | 34 487 | **56 911** |
| `2` location | 621 | 2 248 | 2 869 |
| `10` vente immo pro | 251 | 782 | 1 033 |
| `11` location immo pro | 54 | 208 | 262 |
| `6` neuf · `8` saisonnier | 1 | 0 | 1 |
| **INVISIBLES** | **927** | **3 238** | **4 165** |

**Mesuré par trois chemins indépendants qui donnent le même chiffre** : GraphQL 61 076 − REST
56 911 · la somme des totaux par type · et `offre_type = 0` sur **les 56 910 lignes du miroir,
sans exception**.

### La décision (Frédéric, 26/08)

```
   LE SERVEUR          tous les types          61 076   (+4 165)  -> il devient le maitre
   SUPABASE / FRONT    offre 0 + 10 + 6        57 945   (+1 034)
   au serveur seul     location 2 + 11 + 8      3 131   -> n'apparait PAS dans l'app
```

### ⚠ Et les quatre index Supabase — *point relevé par Frédéric*

Ce n'est pas « un seau » : **les quatre index sont tous dérivés de `app_view_generale`**. Ajouter
les types au serveur les ferait donc partir vers Supabase **automatiquement**, locations comprises.

| index | condition |
|---|---|
| `app_dossier_current` *(actives)* | `archive='0'` ET statut ∈ (`Actif`, `Sous offre`, `Sous compromis`, `Estimation`) |
| `app_archive_annonce_index_current` | `archive='1'` |
| `app_historical_annonce_index_current` | `archive='0'` ET statut ∈ (`Vendu`, `Clos`) |
| `app_brouillon_annonce_index_current` | `archive='0'` ET id ∈ brouillons |

**La colonne existe déjà** : `app_view_generale.offre_type` vaut `0` sur les 56 910 lignes.

> 🔑 **L'ordre à respecter, et il est gratuit.** Poser le filtre `offre_type IN ('0','10','6')`
> **AVANT** d'ouvrir le run. Aujourd'hui il est **totalement inerte** — tout vaut 0. Une fois posé,
> on ouvre le robinet, et **il n'existe aucun instant où une location peut fuir vers Supabase**.
> L'inverse revient à publier 3 131 locations puis à courir après.

---

### ⚠ Le piège à ne pas rater

`reconcile_active_annonce_scope` calcule `known_ids − active_annonce_ids` et **supprime** la
différence — état, liens contacts, détail brut. **Si le balayage couvre les six types mais que la
réconciliation compare à un seul, elle effacera les 4 165 à chaque run.** Elle doit être scopée
par type d'offre.

### ❗ Quatre autres écarts, relevés sur tous les endpoints du run

| endpoint | Hektor | miroir | écart |
|---|---|---|---|
| **mandats** | 26 409 | 24 130 | **+2 279** |
| **ventes** | 9 211 | 7 537 | **+1 674** |
| offres | 11 108 | 10 992 | +116 |
| compromis | 10 571 | 10 455 | +116 |
| agences | 20 | 19 | +1 — *« Gestion site »* |

**Hypothèse à remesurer APRÈS C.15** : ce sont vraisemblablement les mandats et les ventes des
**4 165 annonces absentes** — le mandat arrive par le détail de l'annonce, donc une annonce absente
emporte le sien. **Un mandat manquant sur un registre légal n'est pas une nuance d'affichage.**

---

### ✅ La séquence, en quatre temps — *ne pas intervertir*

| | | |
|---|---|---|
| **①** | **Scoper la réconciliation par type d'offre** | **le préalable absolu** — tant qu'elle compare six types à un seul balayage, elle **efface les 4 165 à chaque run** · *vérif : balayage partiel → **0 suppression*** |
| **②** | **Poser le filtre `offre_type IN ('0','10','6')`** sur les 4 index **et** sur `ANNONCES_SCOPE_WHERE` | **gratuit** — inerte aujourd'hui · *vérif : les comptes Supabase doivent rester **identiques au caractère près*** |
| **③** | **Mesurer l'aval AVANT d'ouvrir** — vues, registre, rapprochements, statistiques | **la photo d'avant** : tout a été calculé sur un parc amputé ; sans elle on ne distinguera pas un effet voulu d'une régression |
| **④** | **Ouvrir un type à la fois** — `6` *(**1 seule annonce**, le canari)*, puis `10` *(1 033)*, puis `2` et `11` *(serveur seul)* | surveiller le **frein de débit** à chaque palier — l'IP a déjà été bannie une fois |


---

### ✅ ④ — **LE CANARI EST POSÉ** *(27/08, code écrit — pas encore passé dans un run)*

**Le canari a un nom.** Un seul appel `ListAnnonces(archive=0, offre=6)` :

```
   id            62483        APPARTEMENT BOURG ARGENTAL
   prix          281 300 EUR  surface 97,69 m2   Bourg-Argental 42220
   dossier       V550062483   mandat 18699
   diffusable    1            <<< EN LIGNE sur les portails depuis le 11/06/2026
   offredem      '6'
```

Une annonce **active, mandatée, diffusée depuis deux mois et demi**, et absente de tout :

| | |
|---|---|
| `miroir.hektor_annonce` · `hektor_annonce_detail` · `hektor_mandat` | **0** *(témoin annonce 4 : 1)* |
| `miroir.raw_api_response` | **0** — 🔑 **Hektor ne nous l'a jamais dite : nous ne l'avons jamais demandée** |
| `serveur.app_dossier` · `app_view_generale` | **0** |
| mandats orphelins dans le miroir | **0 sur 24 037** — le cas est pur, aucun résidu |

**Le champ dans la RÉPONSE s'appelle `offredem` ; le paramètre de la REQUÊTE s'appelle `offre`.**
*(`normalize_source.py:508` — `offre_type` vient de `item.get("offredem")`.)* C'est **le même piège
qui a coûté la journée du 26/08**, et le troisième de la série *(`mandat`/`id_mandat`,
`offredem`/`offre`)*. Vérifié en direct : `offredem = '6'` → le filtre de routage `IN ('0','10','6')`
enverra bien 62483 vers Supabase.

#### Les deux modifications, **couplées — ensemble ou rien**

```
   sync_raw.py           variante "active_neuf" : archive=0, offre=6, scope PROPRE
                         + params["offre"] pose UNIQUEMENT si la variante le declare
   normalize_source.py   les 2 noms d'endpoint AJOUTES a ANNONCE_ENDPOINTS
```

> 🔑 **Pourquoi couplées.** `active_annonce_ids_from_raw()` ne lit **que** les endpoints de
> `ANNONCE_ENDPOINTS`, et `prune_annonce_scope()` supprime tout ce qui n'y figure pas. Une variante
> ajoutée dans `sync_raw` **sans son nom là** ferait entrer l'annonce **puis l'effacerait au même
> run**. C'est le piège du § précédent, sous une autre forme.

Le `scope` est propre *(`active_neuf`)*, donc son curseur `annonce_cursor_active_neuf` est distinct :
**la fenêtre delta du scope `active` n'est pas perturbée.**

#### Non-régression vérifiée par banc *(avant tout run)*

```
   active     -> {archive:0, sort, way, page, version}              pas de cle "offre"  OK
   archived   -> {archive:1, sort, way, page, version}              pas de cle "offre"  OK
   active_neuf-> {archive:0, ..., offre:6}                                              OK
   les 6 noms d'endpoint            inscrits dans ANNONCE_ENDPOINTS                     OK
   load_annonce_ids_missing_detail_sync (filtre listing_variant='active')  CODE MORT, jamais appele
```

#### Les attendus, écrits AVANT le run — *la règle du 25/08*

```
   miroir.offre_type            0 : 56 911        6 : 1        <<< aujourd'hui 0 : 56 911 seul
   miroir.hektor_annonce        56 911  ->  56 912
   miroir.hektor_annonce_detail +1  (62483)
   serveur.app_view_generale    +1
   index.actives                +1   (62483 est active et diffusable)
   les 3 autres index           0 ailleurs
   Supabase app_dossier_current +1
   [reconcile] supprimees       TOUJOURS 0        <<< le signal d'alarme
   cout Hektor                  1 page + 1 detail
```

**Le signal d'alarme est `[reconcile] 0`.** S'il supprime quoi que ce soit, le couplage a échoué et
il faut arrêter avant le palier suivant *(`10`, 1 033 annonces)*.


---

### Ce que ça explique

Les trois annonces que Frédéric m'a fait chercher — **62815, 62823, 62825** — sont des **ventes
immo pro**. Elles ne sont pas « tombées » du miroir : elles n'auraient jamais dû y entrer, et n'y
sont entrées que par le canal brouillon, avant d'être effacées par cette même réconciliation.

### À VÉRIFIER AVANT DE CODER

- le volume de détails à rapatrier au premier run *(+927 `AnnonceById`)* et le **frein de débit** —
  notre IP a déjà été bannie une fois ;
- l'effet sur `app_view_generale`, le registre, les rapprochements et les statistiques, **tous
  calculés jusqu'ici sur un parc amputé** ;
- le sort d'un contact rattaché à une location, absente de Supabase.

---

## ⚡ 26bis — DONNER UN CORPS À L'ANNONCE · **LA PLUS URGENTE**

> **Elle était décrite dans le plan depuis le 21/08 mais n'avait AUCUN numéro de tâche.**
> Ajoutée ici le 25/08 pour qu'elle cesse d'être invisible.

**Le problème.** Le serveur local n'a de l'annonce que son identité *(10 colonnes)*. Le contenu est
fabriqué chaque nuit **par le miroir de Hektor**. À la coupure, le miroir cesse d'être alimenté :
plus rien à recalculer.

**La contrainte, non négociable.** Le remplissage initial doit se faire **pendant que Hektor vit
encore**. Après, il serait trop tard. **C'est la seule tâche du plan qui devient impossible si on
la remet à plus tard.**

| | action |
|---|---|
| **26bis-(1)** | **créer + remplir** les tables d'annonces du serveur local · débloquée depuis le 21/08 *(le numéro de recherche est figé)* |
| **26bis-(2)** | **observer** en parallèle — personne ne lit, on compare chaque matin |
| **26bis-(3)** | **basculer** — collée à C.9 et au contrat d'autorité |

**ORDRE IMPÉRATIF — ne pas inverser :**
> *« La création app-first écrit dans Supabase. **Sans 26bis, une annonce créée dans l'app n'existe
> QUE là**, et le serveur ne l'apprend que si Hektor la confirme. Ce serait creuser le trou pendant
> qu'on le rebouche. »*

### ❌ Un constat que j'ai retiré le jour même — il était faux

J'avais écrit que le lien bien ↔ mandant n'existait que dans le miroir. **Faux.** Il vit dans
`app_contact_relation_current` — **165 474 lignes sur le serveur, 77 376 dans Supabase** — avec
`hektor_annonce_id`, `app_dossier_id`, le rôle et le numéro de mandat.

> **L'erreur de méthode** : j'ai conclu à une absence après trois recherches par nom, au lieu de
> faire l'inventaire des tables. **Une recherche qui échoue ne prouve pas une absence.**

### ✅ Ce que l'inventaire a établi — le trou est plus précis

| table | comment elle est écrite | possédée ? |
|---|---|---|
| `app_contact` *(identité)* | `CREATE IF NOT EXISTS` + upsert | ✅ |
| `app_contact_current` *(corps, 34 col)* | idem | ✅ |
| `app_contact_relation_current` *(liens)* | idem | ✅ |
| `app_dossier` *(identité annonce)* | AUTOINCREMENT, persistante | ✅ |
| **`app_view_generale` *(corps annonce, 130 col)*** | **`DROP` + `CREATE AS` chaque nuit** | ❌ |

**Le contact possède tout. L'annonce possède son identité, pas son corps.**

### ❌ Et cette phrase-là aussi était fausse — retirée le 26/08

J'avais écrit que le `DROP` de 05:30 effacerait les 56 913 lignes. **Non.** Le miroir **gèle, il ne
disparaît pas** — c'est écrit dans l'en-tête de C.6. Le fichier reste, la reconstruction reproduit
le même contenu. **Les annonces existantes gardent leur corps.**

### ✅ Le trou réel, enfin cerné

Pour les annonces **existantes**, tout est déjà en place : le miroir gelé les redonne, et
`appliquer_contrat.py` **ré-applique chaque nuit ce que l'app détient**, relu dans Supabase. Il ne
manque que l'interrupteur.

**Ce qui manque vraiment est ailleurs** : une annonce **née dans l'app** n'a aucune ligne dans le
miroir → aucune dans `app_view_generale` → **le serveur ne la connaît pas du tout**. Et C.7 sait
*mettre à jour* des lignes, pas en *créer*.

> **26bis n'est donc pas « donner un corps à l'annonce »** — elle en a un — mais **« rendre le
> serveur capable de tenir une annonce que le miroir ignore »**. Plus petit, plus net, et toujours
> à faire avant C.9.

**TESTS ET VÉRIFICATIONS**
- comparer le corps local et la vue actuelle sur **tout le parc** — objectif **0 divergence**,
  comme C.6 *(qui a exigé d'éliminer d'abord 4 faux écarts : `NULL` vs `0.0`, entier `0` vs texte
  `'0'`, la date `0000-00-00`, un jour de décalage)* ;
- vérifier qu'une valeur écrite par l'app **survit au `DROP TABLE` de 05:30** ;
- laisser tourner **plusieurs semaines** avant (3).

---

## C.4 — LES WORKERS · **2 à 3 sem.** · *lot 1 fait*

L'étude du 20/08 donne l'ordre : **statut/affaire → archiver/désarchiver → contact et mandant →
affectation du négociateur EN DERNIER** *(impersonation)*.

| | état |
|---|---|
| ✅ **lot 1** | **l'affaire naît dans l'app** — séquence 1 000 000, adoption au retour. Prouvé 2× |
| ⏳ **lot 2** | archiver / désarchiver / supprimer |
| ⏳ **lot 3** | **le bouton qui manque** *(voir ci-dessous)* |
| ⏳ **lot 4** | affectation du négociateur — **en dernier** |

### 🔧 CORRECTIF — « rattacher un mandant existant » : une fonction sans bouton

**Trouvé par l'essai du 25/08.** Sur 170 494 contacts, l'app ne sait **pas** rattacher un
propriétaire déjà présent à un nouveau bien. Le seul chemin est *« Créer et associer »* — donc
**créer un doublon**.

```
   le worker   handleLinkHektorMandant   existe, complet
   la base     le type de travail        autorise
   le front    cite link_hektor_mandant  6 fois... uniquement pour AFFICHER son avancement
```

**Ce n'est pas un bug : c'est du code sans porte d'entrée.** Et le risque est faible : la routine de
rattachement elle-même *(`linkHektorMandantContact`)* **est éprouvée** — c'est elle qu'utilise
« Créer et associer », validée le 25/08.

**ACTION** : un sélecteur de contact existant + la fonction qui crée le travail. **TEST** : rattacher
un contact déjà présent, vérifier « 2 mandants » dans l'API `AnnonceById`, et **qu'aucun doublon
n'est créé**.

**TESTS ET VÉRIFICATIONS (tout le C.4)**
- rejouer les 3 essais du 25/08 après chaque lot *(voir le protocole en fin de document)* ;
- pour toute écriture nouvelle : **relever le vrai formulaire de Hektor avant de coder** — c'est
  l'omission qui a produit C.5 **et** le défaut de clôture.

---

## C.9 — LA CRÉATION PART DE L'APP · **1 à 2 sem.** · *après C.7 ✅ et 26bis*

Créer un bien, un contact, une recherche **dans l'app**, sans passer par Hektor.

### 🔧 CORRECTIF rattaché — l'identifiant de recherche n'est pas capturé

**Trouvé par l'essai du 25/08.** L'app crée une recherche dans Hektor et **ne garde pas sa
poignée** : le travail rend `idCritere: null`. Conséquence déjà connue : une recherche est ensuite
désignée **par sa position dans la liste**, et le worker, s'il ne trouve pas ce rang, **prend la
première** — en silence.

> ⚠ **Ne rien coder ici sans coordination** : le rattrapage des recherches appartient à l'autre
> session.

**TESTS ET VÉRIFICATIONS**
- créer un bien dans l'app **sans Hektor** → il doit exister **dans le serveur local**, pas
  seulement dans Supabase *(c'est ce que 26bis rend possible)* ;
- vérifier qu'il reçoit **un numéro à l'instant**, pas le lendemain *(→ E.4)*.

---

## C.13 — LA CLÔTURE DE MANDAT DANS L'APP · *cadrage validé le 30/07, dev non commencé*

Drapeau `VITE_APP_MANDAT_CLOTURE_ENABLED` **éteint**.

### ⚠ Ce que l'enquête du 25/08 a ajouté au cadrage — À LIRE AVANT DE CODER

**Le formulaire de clôture a deux visages :**

```
   2 mandats ou plus  ->  <option value="9887" data="mandat">
                          <option value="553"  data="protexaMandat">
   1 seul mandat      ->  AUCUNE option, un champ cache :
                          <input id="selectedMandatId" value="648" data="protexaMandat">
```

**Le worker ne sait lire que des `<option>`.** Sur une annonce à mandat unique il n'en trouve
aucune → il refuse de clôturer. Portée mesurée : **694 annonces actives sur 759 (91 %)**. Et sur les
**98 clôtures réellement enregistrées, 74 portent sur une annonce à mandat unique.**

**Pourquoi personne ne l'a vu** : tout le cadrage du 30/07 a été relevé sur **l'annonce 24113**,
l'une des rares à deux mandats. Et son sous-lot **A0** — *« verrouiller le format exact, en lecture
seule, sans coder »* — **n'a jamais été produit** ; A1 a été codé le même jour.

### 📋 LIVRABLE A0, produit le 25/08 *(lu dans le JavaScript de Hektor)*

```js
var mandatFrom = '#selectedMandatId';                  // le CHAMP CACHE par defaut
if ($j('#id_mandat option:selected').length > 0) {     // la liste ne prime QUE si elle existe
    mandatFrom = '#id_mandat option:selected';
}
var idMandat   = $j(mandatFrom).val();
var typeMandat = $j(mandatFrom).attr('data');          // la FAMILLE, jamais un type juridique
```

| paramètre | source chez Hektor |
|---|---|
| `params[idMandat]` | `.val()` du **champ caché**, ou de l'option choisie |
| `params[typeMandat]` | attribut **`data`** de la même source : `mandat` \| `protexaMandat` |
| `params[id_annonce]`, `prix`, `confrere`, `etat`, `raison`, `autre`, `id_confrere`, `id` | champs du formulaire — **noms déjà conformes dans le worker** |

> ⚠ **Faux ami** : `typeMandat` ne désigne **pas** le type juridique du mandat *(SIMPLE, Mandat de
> vente…)* mais **la famille de registre**. Le code actuel laisse `payload.type_mandat` passer
> **avant** la valeur de Hektor : piège armé, à désarmer.

**ACTION** : lire le champ caché en repli · inverser la précédence de `typeMandat` · et refermer
l'asymétrie du garde-fou *(la branche « l'app fournit l'identifiant » **fabrique** une cible sans
vérifier que Hektor la propose ; l'autre branche, elle, refuse)*.

**TESTS ET VÉRIFICATIONS**
- clôturer sur une annonce à **un seul mandat** *(le cas normal)* ;
- clôturer sur une annonce à **deux mandats** *(le cas 24113)* ;
- vérifier que la clôture **refuse** si le mandat visé n'est pas proposé par Hektor —
  **la clôture est IRRÉVERSIBLE côté Hektor**.

---

## C.11 — MÉNAGE DES TABLES MORTES

`app_contact_override` *(vide)* · `app_console_create_update_contact_job` *(remplacée)* · tables
`_v1` vides. **TEST** : vérifier **0 lecture** sur 30 jours avant de supprimer.

---

## C.14-bis — LE MÊME DÉFAUT, CÔTÉ FRONT · *petit, non urgent*

C.14 a corrigé côté serveur le titre pris **au premier bloc quelle que soit sa langue**. Le front a
**son propre repli**, identique :

```
   api.ts:4097   const firstText = textBlocks.find(item => item.html || item.text)
```

Il ne se déclenche que si le champ arrive vide — donc beaucoup moins après C.14 — mais il reste
faux quand il sert. **Portée mesurée** : 701 annonces actives avaient un `texte_principal_titre`
faux *(686 vides)* ; **1 seule** avait son titre visible affecté.

---

## B.3 — LE DÉCLENCHEUR · *en observation*

*(ton idée, 21/08)* — le worker appelle la descente pour la fiche qu'il vient de traiter.

**Ce que ça règle** : la fraîcheur. La doublure ne se rafraîchit qu'à 07:30 ; une modification faite
à 9 h n'apparaît que le lendemain. **Ce que ça ne règle pas** : l'identité — le numéro reste
distribué par le script de nuit *(→ E.4)*.

**CRITÈRE DE DÉCISION, déjà écrit** : si la colonne « app seule » du journal **reste plate 3
semaines**, la tâche est inutile. Si elle grimpe, elle se justifie **avec un chiffre**.

### ❗ Mais ce critère ne peut pas bouger — *corrigé le 26/08*

La descente dit de quoi les **45** sont faits :

```
   app_diffusion_request        9
   app_diffusion_request_event 29
   app_diffusion_target         7
   --------------------------------
                               45   -> QUE des demandes de diffusion
```

**Les seuls objets que Hektor ne connaît pas.** Et les trois essais du 25/08 **ne l'ont pas bougée
d'un point** — normal : tout est passé par Hektor et en est revenu.

> **Attendre trois semaines ne prouverait rien.** Cette colonne ne montera qu'après **26bis et
> C.9**. La décision sur B.3 dépend de 26bis, **pas du calendrier**.

---

# ⚖ LES TROIS ARBITRAGES QUI T'APPARTIENNENT

## ① La recherche part-elle encore chez Hektor ? — **oui, à la création**

**Mesuré le 25/08.** C.3 a fermé **la porte de l'édition**, pas celle de la **création** :

```
   18:00:08  Creation recherche contact Hektor
   18:00:10  Recherche contact Hektor creee
```

C'est défendable *(rééditer appauvrit — 7 critères sur 12 ; créer n'écrase rien)*, mais ce n'est pas
« sauf recherche » : c'est **« sauf modification de recherche »**. **À trancher explicitement.**

## ② L'offre 33026, chez Hektor sans mandat

Trace du défaut de C.5. **La supprimer dans Hektor, ou la garder comme témoin ?**

## ③ Les contacts d'essai créés le 25/08

```
   605029   M. Claude TEST CHAINE 25-08     acquereur + 1 recherche (Firminy 42700)
   605030   Mme Sophie TEST MANDANT 25-08   mandant sur l'annonce 62774
   603800   adresse changee en « 12 avenue du Test 25-08 »
```

Leur suppression est **ta** décision.

---

# 🚶 PISTE 2 — LES GENS · *ne dépend que de toi*

**Maintenant :** *tu* passes sur l'app pendant qu'*eux* restent dans Hektor.

Ce n'est pas du confort. Le journal dit `app seule = 45`, **plat**, parce que personne n'utilise
l'app. **Tout ce qu'on croit savoir de « l'app comme auteur » est mesuré sur une app que personne
n'exerce.** La journée du 25/08 l'a prouvé : une heure d'usage réel a trouvé trois défauts que des
semaines de relecture n'avaient pas vus.

**Puis, quand tu veux :** ils basculent **un par un**. Jamais les deux systèmes **pour la même
personne**.

| | | |
|---|---|---|
| ⏳ | **E.1** | **19-R2** — rattrapage des recherches, **la veille de la bascule** · ⚠ dernière occasion |
| ⏳ | **E.2** | la bascule — *décision d'organisation, pas technique* |
| ⏳ | | **les comptes manquants** — 5 actifs, dont 2 commerciaux, pour une douzaine de négociateurs |

> ⚠ **« Pas les deux en même temps » se lit PAR PERSONNE.** Les portefeuilles rendent ça tenable.
> Le risque porte sur les **dossiers partagés** — et c'est ce que le journal verra chaque matin.

---

# ✂ PISTE 3 — LA COUPURE · *ne dépend pas de toi · À ZÉRO*

| | | | |
|---|---|---|---|
| ⏳ | **A.1** | **Portails en nom propre** + reprise des ~350 annonces | *semaines à mois* |
| ⏳ | **A.2** | **Ton contrat de signature** *(Yousign)* | *semaines* |
| ⏳ | **A.3** | Registre de mandats en propre — obligation légale | *après A.1/A.2* |
| ⏳ | **D.1a** | **mesurer d'abord** le périmètre des documents | *1 h* |
| ⏳ | **D.1** | documents — 44 512 indexés, **22 491 déjà locaux** | ⚠ irréversible |
| ⏳ | **D.2** | photos — 1 397 | ⚠ irréversible |
| ⏳ | **E.3** | les workers Hektor deviennent invisibles | |
| ⏳ | **E.4** | **le jour J** | *voir ci-dessous* |
| ⏳ | **F.1** | utilisateurs, rôles et droits — **après** la coupure | |

> ⚠ **D.1/D.2 : notre IP a déjà été bannie une fois** par un rattrapage trop rapide.
> **Ne jamais rejouer les annonces déjà en échec.**

## E.4 — LE JOUR J, en détail

```
   le distributeur demarre a 100 000     (annonces)      <- le patron existe : l'affaire
   le serveur remplit LES DEUX CASES     app + hektor
   le numero est IMPOSE                  plus de negociation avec Hektor
   on eteint l'aspirateur                le miroir cesse
```

**Le patron est déjà écrit et éprouvé** : c'est celui de l'affaire *(C.4 lot 1)* — plage réservée,
numéro délivré à l'instant, case Hektor vide, **adoption au retour**. Il a fonctionné deux fois le
25/08. Il reste à l'appliquer au **contact** et à l'**annonce**.

---

# EN PARALLÈLE, SANS ORDRE

| | | |
|---|---|---|
| ⏳ | **0.3** | finir le rattrapage acquéreurs · ≈ 4 h 35 · **autre session, ne pas y toucher** |

---

# ✂ SUPPRIMÉES / ANNULÉES

| | |
|---|---|
| ~~**C.1**~~ | l'arbitrage et ses 3 cas → le cas ③ disparaît quand personne n'ouvre Hektor |
| ~~**la notification de conflit**~~ | plus de conflit à notifier |
| ~~**C.10**~~ | le modèle « au moins » de la modale → sans objet après C.3 |
| ~~**5a**~~ | renommer les 11 paramètres → Postgres refuse le rename |
| ~~**C.8**~~ | dissoute le 25/08 après mesure |
| ❌ **C.5** | **annulée le 25/08 au soir**, le jour même |

---

# LE SEUL VRAI INTERRUPTEUR

```
   phase2/identite/contrat_autorite.py
   CHAMPS_APP_CONTACT = ("birth_date", "birth_place", "marital_status")
   CHAMPS_APP_ANNONCE = ()          # <- VIDE
```

Les trois champs de contact marchent **parce que Hektor ne les connaît pas** — il n'y a rien à
arbitrer. **Côté annonce, aucun champ n'est déclaré.** Donc aujourd'hui, sur une annonce, **Hektor
gagne toujours** — non par arbitrage, mais parce qu'il est **seul dans la pièce**.

Cet interrupteur ne peut s'allumer **qu'après 26bis** : sans corps local, une valeur écrite par
l'app n'a **nulle part où survivre**.

> ❗ **Le jour de la coupure, Hektor n'existe plus : il n'y a plus rien à arbitrer, l'app gagne
> tout.** `statut_annonce`, `negociateur_email` et les champs de mandat ne sont donc pas trois
> décisions de fond sur ton métier — ce sont **trois réglages de transition, réversibles.**

---

# 🧪 LE PROTOCOLE D'ESSAI — la leçon du 25/08

Trois défauts trouvés en une heure d'usage réel, dont deux dormaient depuis des semaines. **Aucun
n'avait été vu par la relecture de code.**

| règle | pourquoi |
|---|---|
| **1. Relever le vrai formulaire de Hektor AVANT de coder** *(lecture seule)* | l'omission de A0 a produit le défaut de clôture ; la même a produit C.5 |
| **2. Exercer depuis le FRONT, pas par la base** | deux des trois défauts n'étaient visibles que par l'écran |
| **3. Suivre la valeur à travers les CINQ supports** | app → Supabase → worker → Hektor → miroir → serveur |
| **4. Se méfier d'un « done »** | l'offre 33026 s'est terminée en succès **sans son mandat** |
| **5. Choisir le cas NORMAL, pas le cas d'essai habituel** | tout le cadrage clôture repose sur 24113, une exception sur 173 |

## Les trois essais de référence, à rejouer après chaque lot

```
   1. modifier l'adresse d'un contact   -> ligne d'attente, debounce 10 min, envoi, relecture
   2. creer un contact + une recherche  -> contact chez Hektor + 1 recherche active en retour
   3. creer un mandant et le rattacher  -> « 2 mandants » lus dans l'API AnnonceById
```

**Résultat du 25/08 : les trois passent.** 12 s, 15 s, 13 s. Aucune erreur, aucun conflit.

## ✅ La vérification du cycle complet — 26/08 au matin

Neuf attendus **écrits la veille au soir, avant les runs**, pour ne pas pouvoir trouver le résultat
normal quoi qu'il arrive.

| | attendu | |
|---|---|---|
| 1 | l'offre 33027 porte toujours le mandat **648** | ✅ |
| 2 | l'affaire 1000002 garde `numero_mandat = 18836` | ✅ |
| 3 | aucun doublon — série locale à **28981** | ✅ |
| 4 | les contacts créés reçoivent leur numéro app | ✅ **355711 · 355712** |
| 5 | l'alerte « affaires sans numéro Hektor » retombe | ✅ *et doublure ledger **0/0*** |
| 6 | l'adresse écrite depuis l'app survit au run | ✅ |
| 7 | ~~le mandant dans `mandants_texte`~~ | ❌ **attendu mal écrit** *(voir 26bis)* |
| 8 | le titre survit à la reconstruction de la vue | ✅ |
| 9 | le magasin reste à **0** | ✅ *0 divergence sur 44 champs* |

**Huit sur neuf — et le neuvième était une erreur d'attendu, pas un défaut.** Le retour arrière de
C.5 **tient le cycle complet** : miroir, vues, registre, doublures, descente.

> **La règle qui en sort** : écrire les attendus **avant** le run. C'est le seul moyen de ne pas
> se convaincre après coup que le résultat est normal — le biais qui a fait valider C.5 le matin
> du 25/08.

## Ce que ces essais ont coûté et rapporté

| | |
|---|---|
| **coûté** | 3 contacts d'essai dans le CRM · 2 offres et 2 mandants sur l'annonce 62774 |
| **rapporté** | C.5 annulée avant de nuire · le défaut de clôture trouvé avant le dev de C.13 · le bouton manquant de C.4 · `idCritere` non capturé · le distributeur d'identité rendu visible |
