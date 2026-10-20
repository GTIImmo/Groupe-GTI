# LA LIAISON ENTRE LE REGISTRE DES TRANSACTIONS ET LE CLASSEUR

**19/10/2026 — analyse d'expert. LECTURE SEULE** : aucune écriture dans le classeur, ni
en base, ni chez Hektor.

*Version 2, réécrite après l'audit du chaînage — qui a renversé la conclusion.*
*(La v1 est sauvegardée dans le scratchpad de la session.)*

> ⚠ **Ne remplace pas `PLAN_DEV_SUIVI_TRANSACTIONS_SHEET.md`**, qui porte les décisions
> des 13-14/10 et les 8 lots. Ce document traite les **deux choses que ce plan ne couvre
> pas** : **l'historique** *(reporté le 13/10)* et **le sens classeur → app** *(jamais
> abordé : tout le plan est à sens unique)*.

---

## 0. LA RÉPONSE, EN UNE PAGE

**Oui, la mise à jour dans les deux sens est possible.** Elle tient en quatre pièces, et
**trois tournent déjà en production chez nous**.

```
PIECE 1  l'ancre      app_affaire_id de l'etape pivot (cle primaire, jamais recalculee)
PIECE 2  le journal   un declencheur Apps Script -> onglet `_journal` : qui, quoi, quand
PIECE 3  la maison    COALESCE(valeur_app, valeur_hektor) + classe A   -- DEJA EN PROD
PIECE 4  l'arbitre    le plus recent gagne, sinon personne n'ecrit
```

**Ce qui bloquait n'existait pas.** Le chaînage ne dérive pas *(1 chaîne sur 8 031 en
33 jours)*, et le journal règle d'un coup les deux vraies difficultés : *qui a modifié
quoi*, et *ne pas relire sa propre écriture*.

**Trois prérequis, tous chez Frédéric** : lire les Apps Script existants, accorder la
pose du déclencheur, coller le patch `app_sheet_ecrit` du 16/10.

---

## 1. LES TROIS MONDES, AUJOURD'HUI

```
   HEKTOR  ─────────►  NOTRE APP              LE CLASSEUR
   le CRM              elle lit Hektor        tape a la main (AppSheet)
                       chaque nuit            10 onglets, 4 766 lignes
                                              ^
                                         il ne recoit rien,
                                         il n'envoie rien
```

**Mesure qui le confirme** : la colonne `affair_uuid`, celle qui porterait notre numéro,
est **vide sur 4 765 lignes sur 4 766**. Rien n'a jamais été écrit.

⭐ **Et le classeur n'est pas une copie : c'est une source originale.** Il détient des
choses que **personne d'autre n'a** — mesuré :

| | |
|---|---|
| le **partage entre deux négociateurs** | **670 affaires** · Hektor n'en connaît qu'une dans **525 cas sur 649** |
| le **numéro de facture** | 3 499 lignes |
| **vente prévue / fixée / réglée**, **date d'annulation** | aucune colonne chez nous |
| la **charge** de la commission | 862 lignes · chez nous : **0** |

C'est pour cela qu'on ne peut pas « l'aligner sur nos données » : **sur plusieurs
colonnes, c'est lui qui a raison, et il est seul à savoir.**

---

## 2. L'IDENTITÉ — sur quoi on ancre le lien

### 2.1 L'appariement : **4 329 lignes sur 4 766 (90 %)**

```
4 766 lignes au classeur
  297  aucune chaine candidate chez nous
  140  refusees par le VERROU DU NOM
─────
4 329 appariees ET confirmees par le nom de l'acquereur
```

⚠ **Le verrou du nom n'est pas négociable** : sans lui, **44 lignes** se collaient sur
l'affaire d'un **autre acquéreur** — un désistement jamais saisi dans Hektor.
*Un faux lien ne se voit pas ; une case vide, si.*

Il tolère la faute de frappe *(45 rattrapées : `CHALENDAR`/`CHALENDARD`,
`GUILLOUIS`/`GUILLOIS`, `PRHDHON`/`PRUDHON`…)* et refuse les **132** où c'est vraiment
quelqu'un d'autre.

### 2.2 ⭐⭐ L'ANCRE : `app_affaire_id`, **pas** `app_chaine_id`

**Audit du chaînage, demandé le 19/10. Verdict : il ne dérive pas.**

Ce que dit le code *(`phase2/sync/affaire_ledger.py`)* :

```
« LE NUMERO DE LA CHAINE : le PLUS PETIT app_affaire_id de ses transactions.
  Ni sequence, ni compteur : stable · unique · refaisable. »

« app_affaire_id intact. Seules les affaires NOUVELLES prennent un numero. »
      -> attribue en MAX+1
```

➡ Une étape qui arrive a **toujours** un numéro plus grand : le minimum d'une chaîne **ne
peut jamais descendre**. *Impossible par construction, pas par chance.*

| mesure | résultat |
|---|---|
| chaînes dont le numéro est **encore** le plus petit `app_affaire_id` | **12 713 / 12 713 — 100 %** |
| chaînes écrites le 16/09 **qui n'existent plus** | **1 sur 8 031** *(0,01 % en 33 j)* |
| lignes de répartition dont le **dossier** a changé | **0 sur 16 060** |
| affaires **disparues** depuis la photo du 04/09 | **0 sur 29 321** |
| chaînes **fermées par une vente**, donc hors d'atteinte | **9 264 / 12 713 — 72 %** |

⭐ **La renumérotation massive du 04/09 était un ÉVÉNEMENT voulu** *(changement de règle
1.7 → 1.8, décidé par Frédéric)*, et le projet avait gardé une photo complète avec son
champ `retour_arriere` — *« réinjecter `app_chaine_id` ligne à ligne par
`app_affaire_id` »*. **Vue, voulue, réversible.**

**Décision :**

| | |
|---|---|
| **ancre** | **`app_affaire_id` de l'étape pivot** *(vente, sinon compromis, sinon offre)* — clé primaire, attribuée **une seule fois**, **jamais recalculée** |
| à côté, pour la lecture | `app_chaine_id`, **jamais** comme ancre |

### 2.3 ⭐ L'ancre est **double** : chacun porte l'identifiant de l'autre

```
dans le classeur   colonne A `affair_uuid`  <-  notre app_affaire_id pivot
chez nous          une colonne `sheet_id`   <-  son ID Unique (4 766 distinctes)
```

Si une ligne est supprimée puis recréée *(nouvel `ID Unique`)*, notre numéro est **encore
dans sa colonne A**. Si la colonne A est effacée, son `ID Unique` est **encore chez
nous**. **Aucun point de rupture unique.**

### 2.4 ⚠ Le vrai risque : **la disparition, pas la renumérotation**

L'unique orpheline, `1001347`, **n'a pas changé de numéro : l'affaire n'existe plus**. Et
elle portait **une des deux seules répartitions saisies à la main** de toute la base
*(Christèle GENTES / Alice RONDEAU, `origine = saisie`)* — **elle pointe dans le vide.**

⚠ Et un numéro peut être **réutilisé** : l'attribution est `MAX+1`, donc supprimer
l'affaire **la plus haute** libère son numéro. *Mesure du jour : `1001347 < 1001361`,
donc pas de réutilisation en cours — mais la mécanique existe.*

➡ **Il faut une sentinelle** : *« une liaison pointe une affaire qui n'existe plus »*.
Aujourd'hui **1**. Elle doit rester à 0, ou être expliquée.

---

## 3. ⭐⭐⭐ LA MATRICE CHAMP PAR CHAMP

Sur les 4 329 lignes. **REMPLIT** = nous sommes vides et le classeur sait → gain net.
**CONFLIT** = les deux pleins et différents → il faut une règle.

| champ | REMPLIT | accord | CONFLIT | nous seuls | sa maison chez nous |
|---|---|---|---|---|---|
| **Numéro de facture** | **3 499** | — | — | — | ⛔ **aucune** |
| **Vente Prévue** | **2 967** | — | — | — | ⚠ `date_acte` à **21 %** |
| **Vente Fixée** | **2 811** | — | — | — | ⚠ `date_acte` à **1 %** |
| **Notaire** | **2 341** | 0 | 0 | 0 | ✅ `notaire_id` *(**vide partout**)* |
| **Charge Commission** | **862** | 0 | 0 | 0 | ✅ `charge_commission_app` *(posée 16/10, vide)* |
| **Négociateur(s)** | **833** | 3 095 | **401** | 0 | ✅ `app_affaire_repartition` |
| **Annulée** *(date)* | **682** | — | — | — | ⛔ **aucune** |
| **Commission TTC** | **483** | **3 785** | **43** | 0 | ✅ `honoraires_entree` |
| **Offre Achat** | 165 | 2 914 | **351** | 840 | ✅ `ledger.date (offre)` |
| **Compromis** | 97 | 2 997 | 76 | 756 | ✅ `ledger.date (compromis)` |
| **Vente Réglée** | 41 | — | — | 772 | ⛔ **aucune** *(≠ notre date d'acte)* |
| **Acquéreur** | 25 | **4 253** | 51 | 0 | ✅ `acquereur_json` |
| **Prix** | 0 | 4 193 | **136** | 19 | ✅ `ledger.montant` |
| **État Actuel** | 0 | **4 329** | **0** | 0 | ✅ **déduit**, jamais stocké |

**Trois lectures :**

1. Le classeur sait beaucoup que nous ignorons — et **cinq de ces champs n'ont aucune
   maison chez nous**.
2. Là où les deux savent, **ils sont d'accord** : état 100 %, acquéreur 98 %,
   commission 87 %, prix 97 %, compromis 97 %.
3. Les vrais désaccords font **~1 000 lignes**, pas 10 000.

---

# PARTIE A — LE PATCH D'ALIGNEMENT *(une seule fois)*

**But** : aligner l'existant **avant** toute liaison permanente. Une liaison posée sur des
données désalignées propage le désalignement.

## A.1 Famille ① — le classeur remplit un vide → **on prend**

| champ | lignes | destination |
|---|---|---|
| Notaire | 2 341 | `notaire_id` — ⚠ **après** résolution du nom en identifiant |
| Charge Commission | 862 | `charge_commission_app` *(contrainte `vendeur`/`acquereur`)* |
| Commission TTC | 483 | `honoraires_entree_app` |
| Négociateur manquant | 833 | `app_affaire_repartition`, `origine = 'classeur'` |

**Règle : une case vide chez nous n'est pas une opinion.** Rien à écraser, aucun
arbitrage.
⛔ Le notaire ne descend pas tant que « Jarlier-Durand » n'est pas devenu un identifiant.

## A.2 Famille ② — les deux d'accord → **on ne touche à rien**

18 571 valeurs. Leur seul usage : **prouver que l'appariement est bon**.
⛔ Une écriture identique reste une écriture : elle salit `ecrit_le` et fait croire à un
geste.

## A.3 Famille ③ — les deux divergent → **le patch NE TRANCHE PAS, il liste**

| conflit | cause mesurée | ce qu'il faut |
|---|---|---|
| **401 négociateurs** | dont **1 308 lignes** où nous stockons `« Cet utilisateur a été supprimé »` | ⭐ le classeur gagne : **un nom vaut mieux qu'un fantôme** |
| **351 dates d'offre** | **146** = notre colonne porte le **dernier** événement, pas la 1ʳᵉ proposition · 46 = un jour d'écart · le reste = vrai désaccord | corriger **chez nous** les 146, lister le reste |
| **136 prix** | le prix a bougé entre l'offre et la vente | ⛔ **ne rien écraser** : les deux sont vrais, à deux moments |
| **51 acquéreurs** | fautes de frappe, surnoms, noms de jeune fille | **nous gagnons** *(fiche contact)*, on **propose** |
| **43 commissions** | non expliquées | ⛔ **une par une** |

## A.4 Famille ④ — aucune maison chez nous → **décision d'architecture**

`Numéro de facture` 3 499 · `Vente Prévue` 2 967 · `Vente Fixée` 2 811 ·
`Vente Réglée` 772 · `Annulée` 682.

⛔ **C'est LA question, et elle n'est pas technique :**

> Notre registre suit la vie **juridique** *(offre, compromis, vente)*.
> Le classeur suit la vie **financière** *(prévue, fixée, réglée, facturée)*.
> **Veut-on que le registre porte aussi le financier ?**
> C'est **5 colonnes** et un changement de nature.

## A.5 L'ordre, et le filet

```
0. GELER les 4 329 appariements dans une table, avec la preuve (echelon, score,
   nom confirme).  SANS ELLE, RIEN N'EST REJOUABLE NI VERIFIABLE.
1. Famille ① seule, champ par champ, par risque croissant :
      charge_commission_app      862   (aucune consequence ailleurs)
      honoraires_entree_app      483   (lu par l'ecran, PAS envoye a Hektor)
      app_affaire_repartition    833   (origine='classeur')
      notaire_id               2 341   SEULEMENT apres resolution des noms
2. Famille ③ : un RAPPORT, zero ecriture.
3. Famille ④ : rien, tant que l'architecture n'est pas tranchee.
```

---

# PARTIE B — LA LIAISON PERMANENTE, DANS LES DEUX SENS

## B.1 Ce qui existe déjà *(sens app → classeur)*

`scheduled/push_suivi_appsheet.py` *(822 lignes)* et les **décisions des 13-14/10** :
lignes nouvelles seulement · option A · **une ligne saisie à la main n'est jamais
touchée** · les trois règles *(on remplit un vide / un état ne recule jamais / dans le
doute on s'abstient et on le dit)*.

⛔ **L'API AppSheet est fermée** *(licence Core : `[EnableAPI] = N`)* → on écrit dans la
source Google Sheets. `--voie appsheet` reste prête si la licence change.

**Rien de cela n'est remis en cause.**

## B.2 ⭐⭐ PIÈCE 2 — LE JOURNAL DU CLASSEUR

Un **déclencheur Apps Script** dans le classeur écrit dans un **nouvel onglet** `_journal`
à chaque modification :

```
date/heure · utilisateur · ID Unique de la ligne · colonne · ancienne valeur · nouvelle
```

- ✅ on le lit **avec l'accès qu'on a déjà** : c'est un onglet comme un autre — **aucun
  nouveau droit, aucune nouvelle API, et aucune copie du classeur chez nous** *(ce qui
  respecte la décision du 13/10 : « deux copies d'une vérité divergent tôt ou tard »)* ;
- ✅ il donne **exactement ce que l'API refuse** : qui, quoi, quand, **et la valeur
  d'avant** ;
- ⭐ **il tue la boucle** : nos écritures portent `accueil@`, celles de l'équipe leur
  compte. **On ne devine plus, on lit l'auteur.**

⚠ **Ce qu'il ne voit pas** : une ligne **supprimée**. Parade : comparer à chaque passage
l'**ensemble des `ID Unique`** — une lecture, pas une copie.
⚠ **S'il est coupé**, les modifications de cette période sont perdues → **rapprochement
complet périodique** *(on sait le faire : 4 766 lignes)* **et une sentinelle qui vérifie
que le journal reçoit des lignes** — sinon on croirait que personne ne modifie rien.

## B.3 ⭐⭐ PIÈCE 3 — LA MAISON QUI SURVIT À LA NUIT *(déjà en production)*

C'est la pièce qui rend le double sens possible **même sur les champs qui viennent de
Hektor** :

```
COALESCE(valeur_app, valeur_hektor)
   + colonne EXCLUE du push vers Hektor     (classe A)
   + REPOSEE apres le run                   (les deux chemins qui effacent)
```

| déjà en service | mesure |
|---|---|
| photos *(visible / masquer)* | **24 497 lignes sur 24 505** |
| clôture de mandat `mandat_date_cloture_app` | en production depuis le 13/10 |
| commission `honoraires_*_app`, `charge_commission_app` | **une nuit entière éprouvée le 17/10** |

➡ Une valeur tapée dans le classeur atterrit dans `..._app`, **gagne à l'écran sur celle
de Hektor**, et **survit au run**.

## B.4 PIÈCE 4 — L'ARBITRE : le plus récent gagne

Avec un horodatage **des deux côtés** *(le journal pour lui, `ecrit_le` pour nous)* :

```
saisie au classeur 14h02  >  notre valeur de 11h30  -> le classeur gagne
notre geste 16h00         >  sa saisie de 14h02     -> nous gagnons, on corrige sa cellule
meme minute, ou doute                               -> PERSONNE n'ecrit, c'est signale
```

⚠ **Sécurité** : on n'écrase que si le changement d'en face est **plus récent que la
valeur en place** — pas plus récent que *notre dernière lecture*.

## B.5 Ce que ça donne, champ par champ

| champ | classeur → app | app → classeur | chez nous |
|---|---|---|---|
| Prix | ✅ | ✅ | `montant_app` *(à créer)* |
| Commission, Charge | ✅ | ✅ | **existent déjà** |
| Répartition | ✅ | ✅ | `app_affaire_repartition` — **la garde existe** |
| Dates offre / compromis | ✅ | ✅ | `date_offre_app`, `date_compromis_app` *(à créer)* |
| Acquéreur | ✅ | ✅ | `acquereur_app` *(à créer)* |
| Notaire | ✅ | ✅ | `notaire_id` — **existe** |
| Vente prévue / fixée / réglée, facture, annulation | ✅ | — | **5 colonnes à créer** |
| **État Actuel** | — | — | ⛔ **il se DÉDUIT des dates** |

⭐ **Tout est bidirectionnel sauf l'État** — et l'État n'a pas à l'être : il n'est la
saisie de personne, et les deux côtés sont d'accord **4 329 fois sur 4 329**.

---

## 4. AJOUTER UNE LIGNE — les deux sens tiennent

### app → classeur *(déjà codé, lot 3)*

La ligne naît d'un **geste**, après confirmation de Hektor. Gardes déjà écrites :
`first_seen_at`, pas de création si la dernière date réelle a plus de 90 jours, plage
après le dernier trou *(5 lignes vides au milieu de `Sheet1`)*, `ID Unique` en
hexadécimal minuscule, vrais booléens, renoncer si le mandat est déjà là.
**Volume mesuré : ~35 lignes par mois.**

### classeur → app ✅ **possible, par la salle d'attente**

On ne fabrique pas une affaire de toutes pièces *(elle a besoin d'une annonce et d'un
contact)*. On crée une **affaire en attente** — **le patron existe déjà dans le projet**
*(`app_search_provisional`, les tables `*_pending`)*. Un écran demande au négociateur de
la rattacher à un bien ; une fois rattachée, elle devient une vraie affaire et repart
dans le classeur avec son numéro.

⛔ **Ce qu'on ne fait jamais** : inventer une chaîne dans `app_affaire_ledger`. Celle-là
serait refaite la nuit — c'est une **déduction**, pas une saisie.

---

## 5. LES PRÉREQUIS — il n'y en a que trois

```
1. LOT 0 : lire les Apps Script deja presents dans le classeur.
   Sheet1 nourrit la PAIE (Calcul Salaire, CA Mensuel, Reporting, 12 mois lissants)
   par des scripts que personne n'a jamais lus.
   BLOQUE : il faut que Frederic ouvre l'editeur de scripts.

2. SON ACCORD pour poser le declencheur et l'onglet `_journal` dans SON classeur.
   C'est une modification de son outil de travail.

3. COLLER app_sheet_ecrit (lot 2, patch du 16/10 jamais colle).
   Utile comme ceinture : couvre la periode AVANT le journal, et le cas ou le
   declencheur tomberait.
```

## 6. L'ORDRE PROPOSÉ

```
VERROU 0   coller app_sheet_ecrit
VERROU 1   lot 0 -- lire les Apps Script          (bloque TOUTE ecriture au classeur)
VERROU 2   trancher la famille ④ : 5 colonnes, oui ou non

A.0  geler les 4 329 appariements, avec leur preuve
A.1  le patch d'alignement, famille ① seule, champ par champ
A.3  le rapport des conflits (famille ③), zero ecriture
B.2  poser le declencheur + l'onglet `_journal`, et sa sentinelle
B.3  les colonnes de classe A manquantes
B.4  l'arbitre, champ par champ, en commencant par les 3 qui ont deja leur maison
```

## 7. ⛔ CE QUE JE NE TRANCHE PAS

```
1. Le registre doit-il porter la vie FINANCIERE (facture, prevue, fixee, reglee,
   annulation) ? 5 colonnes, un changement de nature.  -- LA question.
2. Les ~1 000 conflits : par paquet, ou un par un ?
3. Les 401 negociateurs divergents : le classeur gagne-t-il d'office quand nous
   stockons « Cet utilisateur a ete supprime » (1 308 lignes) ?
4. Corrige-t-on nos 146 dates d'offre fausses ? (ecriture dans NOTRE base)
5. Les 297 + 140 lignes non appariees : liste a la main, ou on les laisse ?
6. La colonne 31 avait change de sens en 2021 (departement -> prix) : faut-il
   verifier si D'AUTRES colonnes ont change de sens ?
```

---

## 8. ANNEXE — MES ERREURS DE MESURE, POUR MÉMOIRE

Quatre affirmations fausses de ma part, corrigées par la mesure. Gardées parce qu'**elles
disent où se cachent les pièges**.

| ce que j'affirmais | la vérité mesurée |
|---|---|
| *« le classeur porte la répartition commerciale, que nous n'avons pas »* | **faux** : `app_affaire_repartition`, 16 062 lignes, alimentée par Hektor avec **16 199 montants en euros** |
| **3 502 conflits** de commission | la `Commission TTC` = **`honoraires_entree` SEULS** *(87 %)*. Je sommais entrée + sortie |
| **2 709 conflits** sur la vente | **« Vente Réglée » n'est pas la date d'acte** : +1 à 7 jours dans 88 % des cas, **médiane +3 j**. C'est le **règlement** |
| *« le chaînage est recalculé chaque nuit, donc instable »* | **faux** : *« ni séquence, ni compteur · stable · refaisable »*. J'avais confondu **recalculé** et **instable** |

➡ **Deux règles de méthode qui en sortent :**

1. **Avant d'appeler « divergence » un écart massif et régulier, chercher le décalage de
   définition.** Un facteur 2 exact, ou un écart médian de 3 jours, ne sont jamais des
   fautes de saisie.
2. **Avant de dire « nous n'avons pas », chercher la table ET son alimentation.**

---

## 9. CE QUI A ÉTÉ MESURÉ POUR CE DOCUMENT

| | |
|---|---|
| classeur | 4 766 lignes · 38 colonnes · **10 onglets, aucun caché** |
| appariées et confirmées | **4 329** *(90 %)* |
| rythme du classeur | **~35 lignes/mois** |
| `app_affaire_ledger` | 31 081 affaires · 12 713 chaînes · **0 disparue en 45 j** |
| `app_affaire_repartition` | 16 062 lignes · 8 031 chaînes · **1 orpheline** |
| `app_affaire_console` | 18 524 lignes · 16 210 personnes · lu jusqu'au **18/10** |
| `app_sheet_ecrit` | ⛔ **n'existe pas** |
| `notaire_id` · `charge_commission_app` | ⛔ **vides** |
| API AppSheet | ⛔ **fermée** *(licence Core)* |

**Scripts de mesure** *(scratchpad, non versionnés)* : `matrice_champs.py`, `verifs.py`.

**Documents liés** : `PLAN_DEV_SUIVI_TRANSACTIONS_SHEET.md` *(les 8 lots, les décisions)* ·
`AUDIT_FAISABILITE_ECRITURE_CLASSEUR_2026-10-16.md` *(appariement, divergences)* ·
`AUDIT_REPARTITION_HONORAIRES_2026-10-19.md` *(la répartition)* ·
`ANALYSE_APPSHEET_SUIVI_TRANSACTIONS_2026-10-13.md` *(les 38 colonnes)*.
