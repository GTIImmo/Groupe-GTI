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

## Ce que ces essais ont coûté et rapporté

| | |
|---|---|
| **coûté** | 3 contacts d'essai dans le CRM · 2 offres et 2 mandants sur l'annonce 62774 |
| **rapporté** | C.5 annulée avant de nuire · le défaut de clôture trouvé avant le dev de C.13 · le bouton manquant de C.4 · `idCritere` non capturé · le distributeur d'identité rendu visible |
