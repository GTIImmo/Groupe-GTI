# PLAN DE DÉVELOPPEMENT — l'app alimente le classeur de suivi des ventes

> **Ouvert le 14/10/2026.** Hors des 8 chantiers de l'étape 2 : c'est un projet à part,
> demandé par Frédéric. Il ne prend la place d'aucun chantier et ne touche à aucun.
>
> **Rien n'a encore été écrit dans le classeur.** Tout ce qui suit est mesuré, pas supposé.

**Les trois documents de ce projet** — ce plan dit *quoi faire et dans quel ordre* ; les deux
autres portent le savoir :

| | |
|---|---|
| l'inventaire du classeur, les types de champs, saisi / calculé / généré | `notice/AUDIT_CLASSEUR_SUIVI_TRANSACTIONS_2026-10-13.md` |
| les gestes de l'app, geste par geste, et ce que chacun écrit | `notice/PROPOSITION_GESTES_VERS_APPSHEET_2026-10-14.md` |

---

## 1. L'objectif, en une phrase

**Quand un négociateur pose une offre, un compromis ou une vente dans l'app, la ligne du
classeur de suivi se crée et avance toute seule** — sans qu'on ressaisisse, et sans jamais
écraser ce que Delphine y écrit.

### Ce qui est dans le périmètre

- les **9 gestes de transaction** de l'app qui partent chez Hektor, plus la **répartition de
  commission** et les **corrections** qui restent chez nous ;
- l'écriture dans **`Sheet1`** du classeur `1wFd3pQYItvOrbk10W0r--bmhOaV1R4tWgZ3dq1XCipk` ;
- un **champ commission + sa charge dès l'offre**, qui n'existent nulle part aujourd'hui.

### Ce qui n'y est pas

- **l'historique** : on ne reprend pas les 4 760 lignes existantes *(décision de Frédéric,
  13/10 : « d'abord uniquement les nouvelles lignes »)* ;
- **le rapport d'écarts** app ↔ classeur, et les **4 offres au montant divisé par dix**
  *(18426, 18602, 18374, 18406)* : rangés, ils ne repartent que sur demande ;
- les **9 autres onglets** : on n'écrit que dans `Sheet1`. ⚠ Mais voir § 7, ils en vivent ;
- **Hektor** : il ne reçoit rien de nouveau. Aucun geste existant n'est modifié.

---

## 2. L'état des lieux — mesuré

### Le classeur

| | |
|---|---|
| `Sheet1` | **4 760 lignes**, 38 colonnes, aucune formule, ligne 1 figée, 8 vues filtrées nommées par personne |
| l'application | AppSheet `b0d483a9-e4d2-4a8d-9249-8b085ec8ff50` — **la production** |
| état du parc | Vente réglée 3 734 · Annulée 894 · Vente prévue 67 · Offre d'achat 23 · Vente fixée 22 · Compromis en attente 19 |
| accès | clé de service Workspace, identité `accueil@`, scope `spreadsheets` **autorisé le 13/10** |

⛔ **L'API AppSheet est fermée** : la licence AppSheet Core remet `[EnableAPI]` à `N` par
politique. On écrit donc **dans la source de données Google Sheets**, où l'application lit.
Le code de la voie AppSheet reste en place (`--voie appsheet`) si la licence change.

### Notre registre

`app_affaire_ledger` : **31 061 affaires**, **12 707 chaînes** (`app_chaine_id` à 100 %), plus
`app_affaire_repartition` (16 051), `app_affaire_console` (18 511), et deux tables créées mais
vides : `app_affaire_note`, `app_affaire_condition`.

**95,5 %** des mandats du classeur existent chez nous.

### Ce qui manque des deux côtés

| | mesure |
|---|---|
| la **commission à l'offre** | **0 sur 11 182** dans notre registre · **aucun champ** à l'écran · ta feuille la porte sur **22 offres sur 22** |
| la **charge** de la commission | ne se déduit pas : sur 25 lignes où le classeur dit « Acquéreur », **13 sont rangées côté vendeur** chez Hektor |
| la **date d'annulation** d'un compromis | n'existe nulle part chez nous |
| la **répartition à l'offre** | affichée dans la modale, mais saisie **1 fois sur 8 026** |

---

## 3. Les décisions de Frédéric, déjà prises

| | |
|---|---|
| **le périmètre** | les lignes nouvelles seulement ; l'historique « on verra ensuite » *(13/10)* |
| **le suivi** | option **A** : une ligne créée par nous est ensuite **faite avancer** par nous *(13/10)* |
| **la commission** | vient de la modale, **à ajouter dès l'offre**, va dans notre registre **et** dans le classeur, **jamais chez Hektor** *(14/10)* |
| **la forme** | **(a)** les mêmes champs qu'au compromis, **plus le choix de la charge** *(14/10)* |
| **supprimer** | oui, l'état **redescend** quand l'affaire est supprimée *(14/10)* |
| **la mémoire** de ce qu'on écrit | oui, à créer *(14/10)* |
| **les conditions suspensives** | « à voir » — **hors lot pour l'instant** |
| **le script de facturation** | à auditer avant de poser « Vente fixée » |
| **qui exécute** | ma session **ne peut écrire** ni en base de production, ni dans le classeur : **je prépare et j'éprouve, Frédéric colle, pousse et lance** |

---

## 4. L'architecture

```
   l'écran (modale « changer le statut »)
        │
        ├── app_change_annonce_status_optimistic ──┐
        ├── app_modifier_affaire_optimistic        │  l'affaire NAÎT CHEZ NOUS
        ├── app_geste_affaire_optimistic           │  + un travail dans app_console_job
        │                                          │
        ├── app_repartition_commission_set     ────┤  (reste chez nous, pas de travail)
        └── app_edit_affaire_optimistic        ────┘
                   │                                        │
                   │                            le worker ──┴──> HEKTOR ──> confirme (status=done)
                   │                                                             │
                   ▼                                                             ▼
        ┌──────────────────────────────────────────────────────────────────────────┐
        │  scheduled/push_suivi_appsheet.py    toutes les 5 minutes                │
        │  lit : app_console_job (status=done) · app_affaire_repartition · le      │
        │        registre · app_sheet_ecrit (ce que NOUS avons déjà écrit)         │
        │  écrit : Sheet1, par l'API Google Sheets                                 │
        └──────────────────────────────────────────────────────────────────────────┘
```

**Pourquoi après la confirmation de Hektor** : s'il refuse, le worker **restaure le statut**
et il ne faut rien avoir écrit dans le classeur. Délai : quelques minutes.

**Pourquoi une tâche planifiée et pas le worker** : le worker est partagé par **4 services**
qu'il faudrait tous redémarrer. Une tâche séparée ne touche rien et s'arrête d'un clic.

**Ce qu'on ne modifie jamais** : aucune fonction de la base existante, aucune ligne du worker,
aucun redémarrage de service, aucun champ envoyé à Hektor.

### Les trois règles d'écriture — elles ne se discutent pas

> **1. On remplit un vide. On ne corrige jamais un plein** *(sauf si la case porte encore
> notre propre valeur — c'est à quoi sert la mémoire du lot 2).*
> **2. Un état ne recule jamais** *(sauf suppression explicite, lot 6).*
> **3. Devant un doute, on s'abstient ET on le dit** *(règle du chantier ④).*

### La règle de l'état — éprouvée 4 760 fois sur 4 760

```
« Annulée » remplie                -> Annulée
« Vente Réglée » remplie           -> Vente réglée      (jamais posée par nous)
« Vente Fixée » remplie            -> Vente fixée
« Vente Prévue » remplie ET Signé  -> Vente prévue
« Compromis » rempli               -> Compromis en attente
sinon                              -> Offre d'achat
```

⭐ **On ne pose jamais un état : on pose une date, et l'état suit.**

### Les gardes, chacune née d'une mesure

| garde | ce qu'elle évite |
|---|---|
| repérer le neuf par **`first_seen_at`**, jamais par `date` | 54 offres portaient la même seconde : **54 lignes vides par jour** |
| ne pas créer si la dernière date réelle a **plus de 90 jours** | **1 617 chaînes** « nouvelles » le même jour (réalignement du 15/09), dont un compromis de 2022 |
| la plage d'ajout démarre **après le dernier trou** | `Sheet1` a 5 lignes vides ; la ligne serait partie en **3541, au milieu** |
| clé `ID Unique` en **hexadécimal minuscule** | les 500 dernières le sont ; une clé au vieux format rend la ligne **non éditable** dans l'app |
| de **vrais booléens**, de **vraies dates**, des **nombres nus** | `"Y"` ferait une case texte dans une colonne de cases à cocher |
| **renoncer** si le mandat est déjà dans le classeur sans notre numéro | le doublon avec la saisie de Delphine |
| la part d'un négociateur = **somme entrée + sortie** | Hektor coupe en deux côtés ; 295 chaînes sur 300 font alors 100 % |
| ne pas créer sans mandat, prix, référence **et** négociateur | une ligne creuse n'apprend rien, et le négociateur porte la commission |

---

## 5. Les lots

### Lot 0 — auditer les Apps Script du classeur ⏳ *bloqué*

**But** : savoir si un script réagit quand **nous** écrivons, en particulier celui qui
fabrique le `Numéro de facture` à « Vente fixée ».

**Ce qu'on sait** : un script génère `12 mois lissants` *(« Généré le 13/10 22:45 »)*, et
probablement `Calcul Salaire`, `Reporting`, `CA Mensuel` — ces onglets portent des montants
calculés **sans une seule formule**. `Utilisateurs.ID Facture` pointe deux documents Google.

**Ce qu'il faut** : depuis le classeur, *Extensions → Apps Script*, puis **l'URL de l'éditeur**.
L'API Sheets ne donne pas accès au code, et la console en liste **plus de 50 projets** tous
nommés « Groupe GTI ». ⛔ **Bloquant pour le lot 3 (G9)** : rien d'autre.

⚠ Règle connue à éprouver : un déclencheur **simple** (`onEdit`) **ne part pas** sur une
écriture par API ; un déclencheur **installable** (`onChange`) ou horaire, peut-être.

---

### Lot 1 — la commission et sa charge dès l'offre

**But** : saisir la commission et savoir qui la paie, dès l'offre. *Demande de Frédéric.*

| | | qui exécute |
|---|---|---|
| **1a** | **patch SQL** : 3 colonnes de classe A dans `app_affaire_ledger` — `honoraires_entree_app`, `honoraires_sortie_app`, `charge_commission_app`. **Hors du `ON CONFLICT DO UPDATE`** et absentes de `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS` : le run de nuit ne les écrase jamais *(patron de `jours_validite`, `taux_honoraires`, `notaire_id`)*. Même colonne du côté local, `phase2/sync/affaire_ledger.py` ⚠ `DDL_SQLITE` est une f-string : aucune accolade dans ses commentaires. ⚠ **Supabase d'abord, local ensuite** : le push fait `SELECT *` | je prépare · **Frédéric colle** |
| **1b** | **patch SQL** : la RPC qui écrit ces trois colonnes, appelée **après** le geste — comme la clôture de mandat et la répartition. Un échec n'annule pas le changement de statut | je prépare · **Frédéric colle** |
| **1c** | **le front**, 7 points de couture *(voir le détail ci-dessous)* | je code · **Frédéric pousse** |

**Le détail du front** — relevé sur le champ jumeau `statusChangeHonorairesEntree` :

| # | où | quoi |
|---|---|---|
| 1 | `App.tsx:12528` | les `useState` + un **drapeau « touché »** par champ : on n'envoie que ce qui a été saisi |
| 2 | `15782-15785` | vider à l'ouverture de la modale |
| 3 | `16139`, `16478` | **préremplir en modification** depuis le registre — sinon une sauvegarde effacerait la valeur |
| 4 | `19401` *(bloc offre)* | **« Honoraires vendeur (agence) »** *(nouveau ici)* · « Honoraires acquéreur » *(déjà présent, intact)* · **« Charge de la commission »** Vendeur / Acquéreur, **nouveau partout**, défaut « Vendeur » (99,8 % des cas) |
| 5 | `16699-16705` | ⚠ **ne rien ajouter à la charge Hektor** : appel séparé, après le geste |
| 6 | `api.ts:1582` | ⭐ **ajouter les colonnes au `select`, qui les nomme une par une** — sinon elles existent en base et l'écran ne les voit jamais *(le projet s'est fait prendre deux fois le 13/10)* |
| 7 | ~~`App.tsx:26624`~~ | ⛔ **RETIRÉ LE 16/10 — CE POINT ÉTAIT FAUX.** Il demandait que la rubrique lise notre valeur « d'abord » à la place de `commission_agence`. Or **ce ne sont pas la même grandeur** : mesure sur **9 259 ventes**, `(honoraires entrée+sortie) / commission_agence` vaut **4,8** dans 43 % des cas, **1,2** dans 34 %, **2,4** dans 9 % — soit la **TVA**, puis la division par le **nombre d'agences qui partagent**. `commission_agence` est donc **la part HT de l'agence après partage**, et nos colonnes portent un **total TTC**. Les substituer aurait affiché un TTC là où s'affiche un HT. ➡ reste à faire : **afficher nos valeurs à l'OFFRE**, où Hektor n'a rien — à côté des honoraires, pas à la place de la commission |

**Je ne touche pas** à `apresSaisieCommission` : il sort si le statut n'est ni compromis ni
vente, et c'est voulu — l'offre n'a pas de net vendeur.

**Contrôle** : `npm run build` *(jamais `tsc --noEmit`)* · une offre d'essai avec commission,
charge **et répartition** · ⭐ **et le lendemain : les valeurs ont-elles survécu au run de
nuit ?** C'est la seule preuve qui compte. Témoin : noter la chaîne et les montants.

**Retour arrière** : les colonnes sont additives ; le champ se retire du front par un push.

⚠ **Ce que ça pourrait casser ailleurs** : le `select` de `api.ts:1582` sert aussi à la
rubrique Affaires et au cockpit — à vérifier qu'une colonne de plus ne dépasse pas une limite
de charge. Et la modale est le point d'entrée **des trois statuts** : un champ mal conditionné
apparaîtrait au compromis en double.

---

### Lot 1-bis — ⭐ LA COMMISSION ET LA CHAÎNE — *audit du 16/10, demandé par Frédéric*

**Sa décision** : « remonte la chaîne à la lecture », **avec un garde-fou** qui prévient
qu'une modification au compromis changera l'offre — *« mais puisqu'une offre acceptée
n'est pas modifiable... donc oui, mais audit pour savoir comment faire »*. Il avait raison
de demander l'audit : **il change la réponse**.

#### ① La commission NE DIVERGE JAMAIS le long d'une chaîne — mesuré

```
9 826 chaînes à plusieurs étapes (sur 12 713)

  montant               400 chaînes divergent   4,1 %   <- le prix bouge, et c'est normal
  honoraires_entree       1 chaîne   diverge    0,0 %
  honoraires_sortie       0
  commission_agence       0
```

⭐ **Ce que Frédéric craint — « changer le montant du compromis écrase celui de l'offre »
— porte sur le MONTANT, qui bouge dans 4,1 % des chaînes. Or ce n'est pas lui qu'on
partage.** La commission, elle, est déjà la même partout : la partager est fidèle au réel,
pas une simplification.

#### ② Une offre acceptée est DÉJÀ figée, et deux fois

| verrou | où | preuve |
|---|---|---|
| Hektor n'ouvre même pas le formulaire | `createOffre&init=1` | **200 + 0 octet, 9 sur 9** *(mesure du 13/10, `MESURE_MODIFIER_OFFRE_ACCEPTEE_2026-10-13.md`)* |
| l'app verrouille l'offre | `offreVerrouilleeParSonDossier` | dès que la chaîne porte une **vente** ou un **compromis vivant** |

Et **99,9 %** des offres qui ont un compromis sont `accepted` : **9 230 sur 9 235**.

➡ Pour rouvrir la commission d'une offre après le compromis, il faudrait franchir deux
verrous qui existent déjà. **Le conflit redouté est quasi impossible par construction.**

⚠ **La nuance qui reste** : nos trois colonnes ne partent PAS chez Hektor. Son verrou ne
les concerne donc pas *techniquement*. C'est une décision, pas une contrainte.

#### ③ Les trois règles proposées

1. **UNE SEULE VALEUR PAR CHAÎNE**, écrite sur la ligne où on la saisit. Jamais trois
   copies : « deux copies d'une formule divergent tôt ou tard » (règle du projet).
2. **À LA LECTURE** : la valeur de la ligne courante, sinon la plus récemment écrite de la
   chaîne. Saisie au compromis, l'offre l'affiche aussi — c'est ce que Frédéric demande.
3. **LE GARDE-FOU, EN DEUX TEMPS** :
   · *avant d'enregistrer* — si une autre étape porte déjà une commission **différente**,
     la modale le dit : « L'offre n° X porte 8 000 €. En enregistrant 9 000 € ici, l'offre
     affichera 9 000 €. » ;
   · *après* — on garde la valeur précédente, qui, quand : un écrasement doit se voir.
   ⭐ Mesure : cet avertissement se déclenchera **1 fois sur 9 826**. Il protège sans gêner.

#### ④ ⬜ LA SEULE QUESTION QUI RESTE POUR FRÉDÉRIC

**La saisie de la commission suit-elle le verrou de l'offre ?**

| | pour | contre |
|---|---|---|
| **(a) elle le suit** *(recommandé)* | une seule règle dans la modale, cohérente avec ce que l'écran montre déjà ; on saisit au compromis et l'offre lit | on ne peut pas corriger la commission d'une offre déjà engagée |
| **(b) elle ne le suit pas** | plus souple : la commission est à nous, Hektor ne la voit pas | deux règles différentes dans la même modale — un champ grisé à côté d'un champ actif, à expliquer |

---
### Lot 2 — la mémoire de ce que nous écrivons

**But** : pouvoir **remplacer** une valeur sans écraser une correction humaine.

Une table `app_sheet_ecrit` : `app_chaine_id` · `colonne` · `valeur` · `ecrit_le`.
Au geste suivant : la case porte **encore notre valeur** → personne n'y a touché → on
remplace. Elle porte **autre chose** → un humain a corrigé → **on s'abstient et on le dit**.

Rien d'autre à créer : ni colonne dans le classeur, ni colonne dans le registre.
**Table vide et inerte** tant que le lot 5 n'existe pas. *Patch SQL ; Frédéric colle.*

**Débloque** : les lots 4, 5 et 6.

---

### Lot 3 — l'expéditeur : créer la ligne et poser les dates

**But** : le cycle complet d'une affaire. **C'est le cœur du projet.**

Gestes couverts : **G1** créer l'offre · **G3** refuser l'offre · **G5** créer le compromis ·
**G7** annuler le compromis · **G9** créer la vente · **E1** le compromis est signé ·
**E2** la vente est signée.

| | |
|---|---|
| le code | `scheduled/push_suivi_appsheet.py` — **le prototype existe déjà** et tourne à blanc. À reprendre : il lit le registre, pas encore `app_console_job` |
| ce qu'il faut ajouter | lire les travaux **confirmés** (`status = 'done'`, les 5 types de transaction) depuis le dernier passage ; la commission du lot 1 ; la charge |
| la tâche planifiée | `scheduled/run_push_suivi_appsheet.ps1`, patron de `run_gti_health.ps1`, toutes les 5 min. ⚠ **le python du `.venv`** : `google-auth` n'est pas dans celui du système |
| ⭐ la surveillance | **dès le premier envoi réel**, pas après : un battement `app.push_suivi_sheet` dans `monitoring/heartbeat.py` + **la ligne dans `app_worker_registry`** — ⚠ sans elle, un `PATCH` filtré touche **0 ligne**, reçoit **204** et compte un succès *(leçon 4j du 13/10 : 23 battements du run partaient dans le vide)* |

**Contrôle, en trois temps** :
1. **à blanc** (`--dry-run`) : chaque ligne imprimée champ par champ, rien n'est envoyé ;
2. **une seule ligne réelle**, choisie par Frédéric — il la regarde dans l'app, **et surtout
   il vérifie qu'il peut la modifier** : c'est le seul test de la clé que nous fabriquons ;
3. le flux, **plafonné** (`--max`) pendant les premiers jours.

**Retour arrière** : arrêter la tâche planifiée. Les lignes créées portent toutes un
`affair_uuid` : elles se retrouvent et se suppriment en un filtre.

---

### Lot 4 — la répartition de commission *(G12)*

**But** : les négociateurs et leurs parts arrivent dans le classeur. **C'est la paie.**

Lit `app_affaire_repartition` (`ecrit_le` depuis le dernier passage), additionne les parts
entrée + sortie de chaque personne, traduit les noms par l'onglet **`Utilisateurs`** *(règle
mesurée : le premier mot en majuscules ; 13 cas sur 13)*.

⚠ **Si la somme ne fait pas 100 %, on écrit ce qu'on a et on le signale.** On ne complète
jamais au hasard une valeur qui fait un salaire. *(Dépend du lot 2.)*

---

### Lot 5 — modifier *(G4, G6, G10, G13)*

Remplacer montant, dates, parties, notaire **quand la case porte encore notre valeur**.
*(Dépend du lot 2.)*

---

### Lot 6 — supprimer *(G8, G11)*

⚠ *« Annuler » et « supprimer » ne sont pas le même geste* — c'est écrit dans la base.
Supprimer = **corriger une erreur de saisie** : on efface ce que nous avions posé et
**l'état redescend** *(accordé par Frédéric le 14/10)*. Seule exception à la règle 2.
*(Dépend du lot 2.)*

---

### Lot 7 — ce qui vient directement de Hektor *(E3, E4)*

Une affaire saisie dans Hektor sans passer par l'app redescend au run de nuit : créer la
ligne si elle est récente **et** que personne ne l'a saisie. Sans ce lot, les affaires des
négociateurs qui travaillent encore dans Hektor n'arrivent jamais.

---

## 6. L'ordre, et les dépendances

```
Lot 0  audit Apps Script ....... en parallèle, bloque seulement G9 du lot 3
Lot 1  commission + charge ..... 1a -> 1b -> 1c          (la demande de Frédéric)
Lot 2  la mémoire .............. indépendant, inerte
Lot 3  créer + les dates ....... a besoin du lot 1 pour la commission
Lot 4  la répartition .......... a besoin du lot 2
Lot 5  modifier ................ a besoin du lot 2
Lot 6  supprimer ............... a besoin du lot 2
Lot 7  depuis Hektor ........... a besoin du lot 3
```

**Une seule tâche en code à la fois.** À chaque lot : audit → explication *(dont « ce que ça
pourrait casser ailleurs »)* → « vas-y » → code additif → contrôle → ce plan et le journal à
jour.

---

## 7. Les risques, et ce qu'on en fait

| risque | mesure | parade |
|---|---|---|
| ⚠⚠ **`Sheet1` nourrit la paie** | `Calcul Salaire`, `CA Mensuel`, `Reporting`, `12 mois lissants` portent des montants calculés **sans formule** : un script les écrit depuis `Sheet1` | commission et répartition **jamais inventées** ; un écart se signale. Lot 0 avant d'y toucher |
| le **doublon** avec la saisie manuelle | 34 abstentions sur 44 en octobre : Delphine saisit avant notre descente | écrire **au geste**, pas à la descente ; renoncer si le mandat est déjà là |
| une **écriture au mauvais endroit** | 5 lignes vides coupent le tableau | plage après le dernier trou + `INSERT_ROWS` + contrôle d'atterrissage |
| un **échec silencieux** | *(le projet en a payé plusieurs)* | battement **avec sa ligne de registre**, dès le lot 3 |
| la **licence AppSheet** | l'API est fermée par politique | on écrit dans la source ; `--voie appsheet` prête si ça change |
| **ma session ne peut pas écrire** en prod | constaté deux fois le 13/10 | je prépare et j'éprouve ; **Frédéric colle, pousse et lance** |

---

## 8. En attente, et hors lot

```
À VOIR          les conditions suspensives (G15) -> « En attente de » ?
TRANCHÉ 16/10   commission_agence EST un montant HORS TAXES, et c'est LA PART DE
                L'AGENCE après partage. Mesure sur les 9 259 ventes :
                (honoraires entrée+sortie) / commission_agence vaut 4,8 (43 %),
                1,2 (34 %) ou 2,4 (9 %) -- la TVA, puis /1, /2 ou /4 selon le
                nombre d'agences. 86 % tombent exactement sur ces trois rapports,
                0 % sur 1,0. ➡ LA NOTE DU PROJET EST FAUSSE sur ce point, et le
                point 7 du lot 1 en découlait : il a été retiré.
SIGNALÉ, non traité (ce sont des anomalies du classeur, pas du projet) :
  - l'onglet TOTAUX est MORT : ses 535 formules pointent vers #REF!
  - « Mois de règlement » (onglet Estimation) s'arrête à mai 2025
  - 5 lignes vides au milieu de Sheet1 (3541, 3693, 3837, 4019, 4070)
  - affair_uuid porte « E » en ligne 77
RANGÉ, sur demande seulement :
  - le rapport d'écarts app <-> classeur
  - les 4 offres au montant divisé par dix : 18426, 18602, 18374, 18406
    (3 sont des affaires EN COURS ; 18602 dort depuis le 05/08)
```

---

## 9. Journal

| date | lot | fait | mesure |
|---|---|---|---|
| 13/10 | — | scope `spreadsheets` ouvert · classeur et registre audités · prototype à blanc | 4 760 / 4 760 sur la règle d'état |
| 14/10 | — | gestes de l'app relevés · les deux commissions auditées · ce plan | 99,8 % des commissions sont au vendeur · la charge ne se déduit pas (13 cas) |
| 16/10 | **1a** | 3 colonnes de classe A posées **des deux côtés** (Supabase + local) · le **filet d'ordre** dans les deux sens | 41 → 44 colonnes · 0 valeur · la contrainte refuse `Vendeur` majuscule · le push prépare 31 074 lignes et **aucune** ne porte une colonne de classe A |
| 16/10 | **1b** | la RPC `app_affaire_commission_ecrire` — écrit sur **UNE** ligne, jamais une autre étape de la chaîne | existe et refuse un id inconnu · **anon → 401 permission denied** · 0 valeur en base |
| 16/10 | audit | ⭐ la commission **ne diverge jamais** le long d'une chaîne · une offre acceptée est **déjà figée deux fois** · Hektor ne garde **aucun** honoraire à l'offre | 1 divergence sur 9 826 · 200 + 0 octet 9/9 · offre 0 % / compromis 99 % / vente 100 % |

