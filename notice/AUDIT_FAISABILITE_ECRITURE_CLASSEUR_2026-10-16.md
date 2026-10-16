# AUDIT DE FAISABILITÉ — ÉCRIRE DANS LE CLASSEUR DE SUIVI

**16/10/2026.** Demande de Frédéric, mot pour mot :

> « pouvoir ajouter des nouvelles lignes dans le google sheets et pouvoir les modifier
> et aussi **modifier les anciennes lignes** »

Le troisième point est **nouveau** : le plan du 14/10 excluait l'historique
*(« d'abord uniquement les nouvelles lignes », décision du 13/10)*. Cet audit dit ce
qu'il coûte de l'inclure.

⚠ **Aucune écriture n'a été faite.** Tout ce qui suit est mesuré en lecture seule.

---

## 1. ✅ PEUT-ON ÉCRIRE ? Oui — cinq obstacles vérifiés, un seul reste

| obstacle | mesure | verdict |
|---|---|---|
| le **scope** Google | `spreadsheets` (lecture **et** écriture) autorisé dans la délégation | ✅ |
| une **protection** sur `Sheet1` | 1 protection, mais **`warningOnly = true`** | ✅ l'API écrit ; Google n'avertit que l'humain |
| une protection **dure** ailleurs | `TOTAUX` : `warningOnly = false`, aucun éditeur listé | ⛔ on n'y touche jamais *(et cet onglet est mort : 535 formules `#REF!`)* |
| des **cellules fusionnées** | **0 fusion** dans `Sheet1` | ✅ c'était un risque du plan, il n'existe pas |
| la **langue** du classeur | `fr_FR` | ✅ `16/10/2026` sera lu comme une **date**, pas du texte |
| que `accueil@` soit **Éditeur** | ⬜ **non prouvé** | il faut **un essai de 2 secondes** — écrire puis effacer une cellule à l'écart. À autoriser par Frédéric |

---

## 2. ⚠ AJOUTER UNE LIGNE — le piège de l'ajout automatique

`Sheet1` porte **5 lignes vides au milieu du tableau** : **3541, 3693, 3837, 4019, 4070**.

Or `values.append` ne cherche pas la dernière ligne du tableau : il cherche **la fin du
premier bloc continu**. Sur `Sheet1!A:AL`, il écrirait donc **en ligne 3541, au milieu
des données**.

### ⭐ La parade

On n'utilise **jamais** `append`. On lit la dernière ligne non vide (**4772** au 16/10) et
on écrit **explicitement en 4773** avec `values.update`. Un numéro de ligne en clair ne
peut pas se tromper de place, et un contrôle d'atterrissage le relit juste après.

---

## 3. ⛔ MODIFIER UNE LIGNE — il faut une clé, et le classeur n'en a aucune

Mesuré sur les 4 771 lignes :

| colonne | remplie | distinctes | verdict |
|---|---|---|---|
| `[0] affair_uuid` | **1** / 4 771 | 1 *(la valeur est « E »)* | ⛔ vide |
| `[1] product_ref` | 694 | 594 | ⛔ partielle |
| `[2] Mandat` | 4 766 | 4 047 | ⛔ **719 doublons** — Hektor recycle ses numéros |
| `[37] ID Unique` | 4 766 | **4 766** | ⚠ unique, mais **générée de leur côté** (AppSheet) : inconnue de nous à l'écriture |

### ⭐ La parade

**Nous remplissons la colonne A** (`affair_uuid`, vide et nommée pour ça) avec notre
`app_chaine_id`. Elle devient la clé que nous maîtrisons ; `ID Unique` reste la leur.
⚠ Le « E » déjà présent n'est pas touché : on ne corrige pas ce qu'on n'a pas écrit.

---

## 4. ⭐⭐ MODIFIER LES ANCIENNES LIGNES — 90 % possible, et c'est mesuré

Pour modifier une ancienne ligne, il faut d'abord **savoir laquelle**. Cascade essayée
sur les 4 760 lignes qui portent un numéro de mandat :

```
le n° de mandat désigne UNE seule chaîne      2 985   62 %
sinon, l'ACQUÉREUR tranche                    1 058   22 %
sinon, le PRIX tranche                           233    4 %
sinon, ACQUÉREUR + PRIX ensemble                  38    1 %
──────────────────────────────────────────────────────────
APPARIABLES AVEC CERTITUDE                     4 314   90 %

reste ambigu                                     264    5 %
mandat inconnu chez nous                         182    3 %
```

### Ce que ça permet, concrètement

Une **passe unique** écrit notre `app_chaine_id` dans la colonne A des **4 314** lignes
appariées. À partir de là, **elles se modifient exactement comme les nouvelles** — le
problème de l'historique disparaît pour 90 % du classeur.

### ⛔ Et les 446 autres (10 %) ne sont PAS touchées

264 restent ambiguës, 182 portent un mandat que nous ne connaissons pas. **On ne devine
pas.** Elles gardent leur colonne A vide, et notre code les saute — avec un rapport qui
les nomme, pour que Frédéric puisse en trancher à la main s'il le veut.

---

## 4-bis. ⭐ RÉVISION DU 16/10, APRÈS DEUX DE MES PROPRES ERREURS — **95 %**

Frédéric a demandé si **se limiter aux lignes de 2020 à 2026** améliorait le taux, puis
de travailler les trois groupes de ratés. Les deux questions ont fait tomber deux
erreurs **de ma mesure**, pas de ses données.

### ① Non, la période ne change rien — le taux est PLAT

```
2018  92 %     2021  92 %     2024  84 %
2019  92 %     2022  91 %     2025  92 %
2020  89 %     2023  88 %     2026  92 %

de 2020 à 2026 : 90 %   ← identique au total
de 2023 à 2026 : 89 %   ← légèrement moins bien
```

Les ratés ne sont pas vieux, ils sont répartis. ⭐ **Mais limiter le périmètre reste
utile — pas pour la précision, pour la CONTENANCE** : 1 302 lignes touchées (2024-2026)
au lieu de 4 766, dans un classeur qui nourrit la paie.

### ② ⚠ MON PARSEUR DE PRIX ÉTAIT CASSÉ, et il gonflait le score

`re.sub(r"[^\d]", "", x)` retirait **le point décimal** : `55000.00` devenait **5 500 000**.
Le critère « prix » ne collait donc jamais aux compromis ni aux ventes, et ne désignait
une chaîne unique **que par accident**. Corrigé, il colle à plusieurs chaînes et
discrimine moins : **le taux retombe de 94 % à 92 %.** Mon 94 % était dû au bug.

### ③ ⭐⭐ ET 163 DES 178 « AMBIGUÏTÉS » N'EN SONT PAS

Ce sont **des doublons de NOTRE chaînage** : plusieurs `app_chaine_id` pour la même
affaire réelle, sur **le même bien**. Vérifié : les chaînes à égalité partagent toutes
la même annonce. Prendre le plus petit identifiant les résout, et c'est juste — elles
décrivent la même transaction.

```
appariées                                4 563   95 %
aucun critère ne parle                      15
mandat inconnu chez nous                   182
ligne sans numéro de mandat                  6
───────────────────────────────────────────────
non appariées                              203    5 %
```

### La méthode retenue : un SCORE, pas une cascade

| critère | points |
|---|---|
| le nom de l'acquéreur se retrouve | **3** |
| le prix concorde à l'euro | 2 |
| la date de l'offre concorde | 2 |
| la date du compromis concorde | 2 |

On garde la chaîne au meilleur score, **et seulement si elle est seule** — sauf si les
ex æquo portent sur le même bien, auquel cas on prend le plus petit identifiant.
⛔ Score nul = on ne tranche pas.

### Ce qui reste, et ce qu'on en fait

| | quoi | décision |
|---|---|---|
| **15** | aucun critère ne parle | on saute, et on les liste |
| **182** | mandat inconnu de notre registre — dont **77 présents dans `app_mandat`**, et parmi eux les **mandats de recherche** importés le 15/10 *(17758, 17705, 17651, 17642…)*. Passer par le registre ne récupère que **4** lignes : les autres sont des mandats **sans bien**, dont la transaction réelle est sur un AUTRE bien | à creuser par le CONTACT, si Frédéric le veut |
| **6** | pas de numéro de mandat | on saute |

---
## 4-ter. ⭐⭐⭐ LA MÉTHODE COMPLÈTE — **98 %**, chaque échelon avec un cas réel

Frédéric : « explique-moi mieux les correspondances et comment, avec du détail ».

### Le principe

**Une ligne du classeur = une affaire chez nous = un `app_chaine_id`.** La chaîne relie
l'offre, le compromis et la vente d'un même acquéreur sur un même bien. Trouver la bonne
chaîne, c'est pouvoir écrire notre clé en colonne A — et ensuite modifier la ligne quand
on veut.

### Les quatre informations comparées, et leur poids

| information | poids | pourquoi ce poids |
|---|---|---|
| le **nom de l'acquéreur** se retrouve | **3** | c'est ce qui ment le moins : un nom ne se négocie pas |
| le **prix** concorde à l'euro | 2 | il bouge entre l'offre et le compromis (4,1 % des chaînes) |
| la **date de l'offre** concorde | 2 | précise, mais parfois vide |
| la **date du compromis** concorde | 2 | idem |

On garde la chaîne au **meilleur score**, et **seulement si elle est seule**.
⛔ **Score nul = on ne tranche pas.** Jamais.

### Les 8 échelons

**① Le numéro de mandat suffit — 2 985 lignes (62 %)**
```
ligne 4   mandat 17522 · REYNARD/DHINNIN · 195 000 · offre 06/05 · compromis 03/07
une seule chaîne : 28182, bien 54785, 195 000, mêmes dates      -> 28182
```

**② Le NOM tranche — 1 058 lignes (22 %)**
```
ligne 72  mandat 17285 · CHESNE Gregory · 18 000
   chaîne 6363  compromis  bien 12273  16 000      score 3  (nom)
   chaîne 6364  offre      bien 12273   7 600      score 0
-> 6363, seule à marquer
```

**③ Le PRIX tranche — 89 lignes.** Quand le nom du classeur ne colle à aucune.
```
ligne 112 mandat 17004 · « SCI 3P » · 67 000 · compromis 10/03/2025
   chaîne 23883  67 000 le 10/03/2025   score 4  (prix + date)
   chaîne 23884  68 000                 score 0
-> 23883
```

**④ Plusieurs critères ensemble — 7 lignes.**
```
ligne 2   mandat 17488 · DUCHET Cédric · 18 160
   chaîne 28174  16 660   score 0
   chaîne 28175  18 160   score 5  (nom + prix)      -> 28175
```

**⑤ La DATE seule — 266 lignes (6 %).** Ni le nom ni le prix ne parlent, mais une date au
jour près suffit.

**⑥ Les combinaisons — 2 lignes.**

**⑦ ⭐ Les EX ÆQUO SUR LE MÊME BIEN — 163 lignes, et ce ne sont PAS des ambiguïtés**
```
ligne 67  mandat 14769 · MACHABERT Philippe · 6 800
   chaîne 3698  compromis  bien 8494  6 800   score 5
   chaîne 3699  compromis  bien 8494  6 800   score 5
   chaîne 3700  offre      bien 8494  6 800   score 5
   chaîne 3701  vente      bien 8494  6 800   score 5
-> toutes sur LE BIEN 8494 : c'est la MÊME affaire réelle, découpée en 4 chaînes
   par notre chaînage. On prend la plus petite (3698), et c'est juste.
```

**⑧ ⭐⭐ LE NOM + LA DATE, SANS LE MANDAT DU TOUT — 121 lignes**

C'est l'échelon qui règle les « mandats inconnus », et il explique enfin leur cause :
```
ligne 3   mandat 17758 · SAGNARD Léna / FAURE Lucas · offre 09/05 · compromis 06/06
          -> AUCUNE affaire ne porte le mandat 17758

POURQUOI : 17758 est un MANDAT DE RECHERCHE (importé le 15/10). L'équipe a écrit
le mandat de RECHERCHE dans la colonne Mandat ; notre registre connaît la
transaction sous le mandat de VENTE 17564.
   chaîne 11132 · bien 23297 · offre 09/05/2025 · compromis 06/06/2025 · « Faure »
   les dates collent AU JOUR.                                     -> 11132
```
⚠ Cet échelon **ignore le mandat** : il ne compare que le nom et la date. C'est donc le
plus faible — il vient **en dernier**, et seulement si une seule chaîne ressort.

⭐ **Le détour du 15/10 sur les mandats de recherche sert exactement à ça** : sans eux,
ces 121 lignes restaient non seulement non appariées, mais **incompréhensibles**.

### Le compte final

```
① n° de mandat                    2 985   62 %
② le nom                          1 058   22 %
③ le prix                             89    2 %
④ nom + prix                           7    0 %
⑤ la date                            266    6 %
⑥ combinaisons                         2    0 %
⑦ ex æquo sur le même bien           163    3 %
⑧ nom + date, sans le mandat         121    3 %
────────────────────────────────────────────
APPARIÉES                          4 684   98 %

aucune candidate (pas chez nous)      50
plusieurs candidates                  11
aucun critère ne parle                15
sans numéro de mandat                  6
────────────────────────────────────────────
non appariées                         82    2 %
```

### ⛔ Et les 82, on n'y touche pas

Elles gardent leur colonne A vide, le code les saute, et la liste est donnée à Frédéric.
**Deviner sur 82 lignes qui nourrissent une paie n'a aucun intérêt** : le gain serait de
1,7 %, et le risque une erreur de salaire.

---
## 5. ⚠⚠ LE VRAI DANGER N'EST PAS TECHNIQUE — `Sheet1` NOURRIT LA PAIE

`Calcul Salaire`, `CA Mensuel`, `Reporting` et `12 mois lissants` portent des montants
calculés **sans une seule formule** : un script les écrit depuis `Sheet1`.

Donc **toute écriture dans `Sheet1` peut se propager jusqu'aux salaires**, par un chemin
que nous ne voyons pas.

### Conséquence sur l'ordre des travaux

Le **lot 0** *(auditer les Apps Script)* n'est plus optionnel. Il était « bloquant pour le
seul `Numéro de facture` » ; avec la modification des anciennes lignes, il devient
**bloquant pour tout**. Il demande une seule chose à Frédéric : depuis le classeur,
*Extensions → Apps Script*, puis l'URL de l'éditeur.

⚠ Règle connue à éprouver chez nous : un déclencheur **simple** (`onEdit`) **ne part pas**
sur une écriture par API ; un déclencheur **installable** (`onChange`) peut partir. Tant
que ce point n'est pas vérifié **chez toi**, on ne sait pas si nos écritures réveillent
tes scripts ou les laissent muets — et les deux réponses sont des problèmes différents.

---

## 6. CE QUE JE PROPOSE, DANS CET ORDRE

| | | ce qu'il faut de Frédéric |
|---|---|---|
| **A** | **l'essai d'écriture** : une cellule à l'écart, écrite puis effacée. Prouve que `accueil@` est Éditeur | **son accord** (2 secondes) |
| **B** | **le lot 0** : lire les Apps Script, savoir lesquels réagissent à une écriture API | **l'URL de l'éditeur** |
| **C** | **la passe de clés** : écrire `app_chaine_id` en colonne A sur les 4 314 appariées. À blanc d'abord, puis **10 lignes**, puis le reste | son accord après le rapport à blanc |
| **D** | **l'expéditeur** : créer et modifier, par numéro de ligne explicite, jamais par `append` | — |

⭐ **A et B avant C**, et ce n'est pas de la prudence de principe : écrire 4 314 clés dans
un classeur qui nourrit la paie, sans savoir quels scripts se réveillent, c'est le genre
de geste qu'on ne peut pas défaire.

---

## 7. CE QUI RESTE OUVERT, ET QUE JE NE TRANCHE PAS

1. **La ligne naît au clic, ou le lendemain après le run ?** *(la dernière des trois
   questions du 13/10)* Au clic, elle naît **incomplète** : au moment du geste, on connaît
   le bien, l'étape et la date ; le notaire, l'acquéreur et le n° de mandat ne redescendent
   qu'à la descente.
2. **Les 446 lignes non appariées** : les laisser, ou te donner la liste pour les trancher
   à la main ?
3. **Les 5 lignes vides du milieu** : les laisser (on les contourne), ou les supprimer une
   fois pour toutes ? ⚠ Supprimer une ligne décale tout ce qui suit — à ne faire qu'en
   sachant quels scripts lisent des numéros de ligne.
