# Audit du registre des mandats — et du mandat qui porte le corps d'un autre

**05/10/2026.** Demandé par Frédéric après avoir constaté que des lignes récentes
nommaient un mandant qui n'était pas le propriétaire du bien.

---

## LE VERDICT EN UNE LIGNE

**L'identité du registre est parfaite. C'est son CONTENU qui est atteint, sur
91 mandats, et la cause est chez Hektor.**

---

# 1. LA CHAÎNE, DE BOUT EN BOUT

| étape | où | ce qu'elle fait |
|---|---|---|
| ① scrape de la fiche annonce | `hektor_annonce_detail.mandats_json` | table **permanente** — survit à la purge des réponses d'API |
| ② reconstruction du miroir | `hektor_mandat` (25 012) | `normalize_source` ; filet `backfill_hektor_mandats.py` (run l. 466, ~1 s) |
| ③ les champs que l'app possède | `magasin_mandat_app.py` + `appliquer_contrat_mandat.py` (l. 525-528) | magasin → contrat → applicateur |
| ④ **notre registre** | `mandat_ledger.py --refresh --push` (l. 839) → `app_mandat` (26 835) | la table durable |
| ⑤ la projection | `build_mandat_register_rows` → `app_mandat_register_current` (24 487) | push de nuit **ou** push par annonce (~1 min) |

---

# 2. CE QUI EST SAIN — SEPT CONTRÔLES, SEPT ZÉROS

```
mandats                                    : 26 835
app_mandat_id nul                          :      0
app_mandat_id en doublon                   :      0
couple (annonce, numero) en doublon        :      0
numero_mandat vide                         :      0
ids dans la plage reservee a l'app         :      0   <- le run n'a jamais envahi
present_in_hektor = 0                      :      0
du registre, absents de app_mandat         :      0   <- la projection n'invente rien
```

⭐ **Et l'autonomie fonctionne** : `origine = annonce` 2 072 · `detail` 24 675 ·
`miroir` 88. Les **2 072 sans `hektor_mandat_id`** portent quand même le nôtre.

⭐ **LA DÉCISION QUI A SAUVÉ LE REGISTRE.** La clé est le couple
**(annonce, numéro)**, pas `hektor_mandat_id` — parce que Hektor recycle ses
identifiants (23 452 distincts pour 23 840 mandats, mesuré en août).
Preuve sur les cas atteints : **182 lignes du miroir → 182 couples → 182 de nos
lignes, aucune fusion.** Avec une clé sur l'identifiant de Hektor, 91 mandats
auraient disparu et deux annonces se seraient écrasées l'une l'autre à chaque run.

---

# 3. LES DEUX ÉCARTS DE COMPLÉTUDE — MESURÉS ET EXPLIQUÉS

### ⚠ 94 lignes du miroir sans annonce — mais UN SEUL vrai manque

```
annonce (VIDE)   numero 16485   debut 2023-12-08   hektor_id 569
annonce (VIDE)   numero 14558   debut 2022-04-25   hektor_id 616
```

Leur `hektor_annonce_id` est vide, donc la clé (annonce, numéro) ne peut pas les
placer. **MAIS CE NE SONT PAS 94 MANDATS PERDUS** — mesuré le 05/10 :

```
sur les 94 : le MEME numero existe AUSSI avec son annonce : 91
             vraiment orphelins                           :  3
numeros presents dans app_mandat                          : 93 sur 94
numeros presents au registre                              : 92 sur 94
```

⚠ **91 des 94 viennent d'UNE SEULE vague, le 27/08/2026** (116 lignes écrites ce
jour-là) : des doublons posés sans identifiant d'annonce. Le mandat, lui, est bien
chez nous sous son annonce.

➡ **Le vrai manque est de 1 mandat dans `app_mandat`, 2 au registre.** J'avais
annoncé 94 : c'était ma cinquième erreur de comptage de la journée sur ce dossier
(voir le journal des erreurs en §7).

### ✔ 2 348 mandats de `app_mandat` ne sont pas au registre — tous expliqués

```
1 699  origine = annonce, sans date, sans identifiant Hektor  -> AUCUN corps a projeter
  649  origine = detail/miroir, annonces de 2017-2022         -> hors perimetre
         dont l'annonce est dans un de nos quatre index : 0
         dont l'annonce n'est nulle part                : 649
```

Les quatre périmètres : `app_dossier_current` 13 467 · archive 35 309 ·
historique 8 931 · brouillon 499. Ces 649 annonces ne sont dans **aucun**.
Rien de perdu : `app_mandat` les garde, le registre ne les montre pas.

---

# 4. LE VRAI DÉFAUT — UN MANDAT QUI PORTE LE CORPS D'UN AUTRE

## La preuve, sur la réponse brute de Hektor (descente du 05/10, 04:21)

```
hektor_mandat_id = 105 sert DEUX annonces, avec le MEME corps :
   annonce   454   numero 14898   debut 2022-07-20   montant 62000   « Marie-José BANO »
   annonce 39707   numero 18523   debut 2026-04-10   montant 62000   « Marie-José BANO »

l'annonce 39707 : « Maison de bourg », Montregard, prix 112 500, archivee
ses proprietaires selon Hektor : M. Paul SOUVIGNET
```

**Les deux blocs viennent de la MÊME réponse** : le bloc mandats nomme BANO, le
bloc propriétaires nomme SOUVIGNET. Et BANO est propriétaire de l'annonce **454**
dans notre registre des liens. Ce n'est donc pas un appariement raté de notre
côté : **c'est la donnée de Hektor qui est contradictoire.**

## Le mécanisme, établi sur les 91 cas

```
les 91 identifiants Hektor valent moins de 2000     (min 3, max 660)   100 %
89 des 91 apparient un mandat ancien (2022-2024) a un mandat de 2026
l'annonce ancienne a un identifiant bas (29, 447, 450, 454, 460, 36)
l'annonce neuve un identifiant haut (61650, 61794, 61878, 61429, 61688)
```

➡ **Hektor a recommencé sa numérotation de mandats à 3.** Les mandats de 2026 ont
reçu des identifiants **déjà pris**, et son point d'entrée « détail de l'annonce »
rend, pour le mandat **neuf**, le corps de l'**ancien** — en gardant le numéro et
les dates neufs.

## Ce qui est contaminé, et ce qui ne l'est pas

| champ | état |
|---|---|
| numéro de mandat, date de début, date de fin | **justes** — ce sont ceux du mandat neuf |
| **mandants** | ceux de l'autre annonce |
| **montant** | ceux de l'autre annonce |

Second signal, mesuré : **montant du mandat ≠ prix de l'annonce dans 92 % des
lignes atteintes, contre 9 % des lignes saines.**

## ⚠ LA PRESSION MONTE, ET C'EST LE PLUS INQUIÉTANT

```
2026 :  611 mandats,  456 a identifiant deja pris   (75 %)
2025 :  911 mandats,   45                           ( 5 %)
2024 :  942 mandats,   71                           ( 8 %)
```

Le phénomène est **neuf et massif** : trois quarts des mandats de l'année portent
un identifiant recyclé. Tous ne sont pas contaminés aujourd'hui (91 le sont), mais
le terrain est posé pour que ça empire.

## Le cas légitime, à ne jamais confondre

**117 identifiants** partagent le même corps **et** le même numéro : c'est **un
mandat qui couvre plusieurs lots**. Normal. La sentinelle les compte à part.

---

# 5. CE QUI A ÉTÉ FAIT, ET CE QUI RESTE

### ✔ Fait le 05/10 — le mandant affiché est déjà le bon

Le registre et la fiche lisent **notre registre des liens**, plus le texte de
Hektor. Donc sur ces 89 lignes, l'écran montre **SOUVIGNET et non BANO**. La
décision du matin, prise pour une autre raison, neutralise le symptôme principal.

### ✔ Fait le 05/10 — la sentinelle

`phase2/checks/mandat_corps_recopie.py` :

```
corps recopie sur une autre annonce : 91   (connu au 05/10 : 91)
   lignes de mandat atteintes       : 182
   dont montant != prix annonce     : 94 sur 182
un mandat sur plusieurs lots (NORMAL): 117
```

⭐ Elle alerte sur l'**aggravation**, pas sur le niveau : 91 est l'état subi,
ce qui doit réveiller c'est qu'il monte.

### ⛔ Ce qui reste faux, et qu'on ne peut pas réparer seuls

**Le montant et, pour partie, les dates de ces 89 mandats.** Les redemander
exigerait un point d'entrée « mandat par son numéro », pas la fiche annonce — à
vérifier côté Hektor / La Boîte Immo. **C'est un défaut à leur signaler** : il
touche une mention contractuelle (le montant d'un mandat), sur 89 mandats de
l'année en cours.

### ⛔ Et les 94 mandats sans annonce

Ils existent chez Hektor, pas chez nous. Chantier séparé.

---

# 6. LA LEÇON

> **Posséder la ligne ne garantit pas la donnée.**

`app_mandat_id` et la clé par couple ont réglé l'**identité** — et ils l'ont fait
parfaitement, c'est mesuré. Mais une étiquette juste sur la boîte ne dit pas ce
qu'il y a dans la boîte. **La vérification de ce qu'on reçoit était la seule pièce
absente de cette chaîne**, qui est par ailleurs la mieux construite du projet.
C'est désormais le rôle de la sentinelle.

---

# 7. LA RÉPARATION EXISTE — Frédéric avait raison sur la cause

> *« si on récupère les éléments du mandat dans Hektor à l'aide de l'id annonce
> c'est pour cela que je te dis qu'il y a un problème »*

**Exact, et c'est l'énoncé juste du défaut.** La seule porte que le projet utilise
est `AnnonceById.mandats` : on demande les mandats **par l'annonce**, donc on hérite
de la jointure que Hektor fait chez lui — celle qui se trompe.

## ⭐ Mais une deuxième porte existe déjà, et elle est déjà codée

`phase2/sync/manual_mandat_corrections.py` lit un **export Hektor « liste mandat »**
(.xlsx), **indexé par NUMÉRO DE MANDAT** — pas par annonce. Il en tire exactement
les champs contaminés :

```
mandate_number · contact_full_name · contact_full_address
date_start · date_end · fees · linked_product_ref (prix) · exclusivity
```

Fichier présent : `liste mandat du 02_02_2026 au 28_02_2026.xlsx` — **80 mandats,
numéros 18340 à 18419**. Lu par `.venv` (openpyxl y est ; le python système ne l'a
pas).

## Ce qu'il manque, précisément

```
les 89 mandats atteints : numeros 18420 -> 18842
                          du 2026-03-02 au 2026-08-28
   mars    30     juin     9
   avril   23     juillet 11
   mai     15     aout     1

l'export dont on dispose (fevrier, 18340-18419) couvre 0 des 89
```

➡ **Demander à Hektor l'export « liste mandat » du 01/03/2026 au 31/08/2026.**
Il porte le vrai mandant **et le vrai montant**, par numéro de mandat, hors de la
jointure fautive.

## ⚠ Et une ligne de code à changer

`inject_manual_mandat_if_missing()` ne remplit que si le détail n'a **aucun**
mandat :

```python
if isinstance(mandats, list) and mandats:
    return data        # <- il renonce des qu'un mandat existe, meme contamine
```

Pour réparer les 89 il doit pouvoir **corriger** un corps suspect, pas seulement
combler un vide. La condition est à étendre : corriger quand le numéro figure dans
l'export **et** que le corps vient d'un identifiant partagé (ce que la sentinelle
sait déjà désigner).

⛔ **À ne pas faire sans l'export** : sans lui, « corriger » n'aurait aucune source
et ne ferait qu'effacer.

---

# 8. LE NUMÉRO DE MANDAT N'EST PAS UNE SÉRIE UNIQUE — ET IL A UN LIBELLÉ

Frédéric : *« si il faut regarder devant il y a hektor ou protexa en libellé »*.
Exact, et c'est la pièce qui explique une grande partie des collisions.

```
app_mandat.famille :  HEKTOR 23 132  ·  PROTEXA 3 703
```

**Deux registres, donc deux séries de numéros.** `mandat_ledger.py` le dit déjà :
`famille = DE QUEL REGISTRE vient le numéro`.

## L'ampleur de la réutilisation

```
numeros de mandat servant UNE annonce        : 13 941
numeros servant PLUSIEURS annonces           :  4 268   (jusqu'a 10 annonces)
   un mandat couvrant plusieurs lots (normal):    143   ( 3 %)
   reutilisation du numero                   :  4 120   (97 %)

sur les 4 458 numeros multi-annonces de app_mandat :
   les FAMILLES different                    :  1 536   -> deux series, PAS une collision
   une seule famille                         :  2 922   -> vraie reutilisation dans la serie
```

```
numero « 1 »   : PROTEXA LOCATION (55776, 58109) + HEKTOR VENTE (23485 2011,
                 40503 2014, 24113 2021)
numero « 10 »  : HEKTOR 2011 MENDOLA  +  PROTEXA 2014 CARROT
numero « 1003 »: 2011 CYRIL DENIS · 2015 REYROLLE · 2016 MAILLET
```

⚠ **Pour un registre des mandats, c'est un fait lourd** : le numéro est une mention
légale censée former une série cotée sans discontinuité. Chez Hektor il repart de
bas au moins trois fois (2014-2016, puis 2026).

## ⭐ MAIS LA CLÉ DU PROJET RÉSISTE, ET C'EST MESURÉ

```
couples (annonce, numero) portant DEUX familles chez nous : 0
```

La clé est **par annonce**, donc la réutilisation d'un numéro sur une *autre*
annonce ne la gêne pas. Et aucune annonce ne porte le même numéro dans deux
familles. **`famille` n'a donc pas besoin d'entrer dans la clé** — elle reste utile
à l'affichage et au tri, pas à l'identité.

## Le cas 1020 / 1032 — le registre ne mélange rien

```
champ                    annonce 1020              annonce 1032
register_row_id          1020:4613                 1032:4069
numero_dossier           VA22690                   VA22914
numero_mandat            4613                      4069
titre_bien               ENTRE CARNOT ET MONTAUD   bel appartement renove secteur carnot
prix                     152 000                   158 685
mandat_source_id         219                       231
mandat_date_debut        2012-04-20                2012-04-26
mandat_montant           152 000                   158 685
adresse_privee_listing   16 BLD ALBERT PREMIER     16 boulevard albert1er
```

**Dix champs diffèrent.** La seule chose commune est le mandant — et
`mandants(idAnnonce)` de Hektor rend **les deux mêmes mandants pour les deux
annonces** : `M. THIERRY BOURGEAT (258606)` et `Mr./Mme (530218)`. C'est donc la
donnée de l'agence : le même propriétaire possédait les deux biens en 2012, à
Saint-Étienne, et son adresse est la même sur les deux fiches.

⚠ Et deux faits à savoir pour ne pas crier au loup :
- les **photos sont différentes** (je les avais crues identiques : préfixe Supabase
  commun, troncature à 32 caractères) ;
- `app_dossier_id` **négatif** sur les 23 742 lignes `historique` et positif sur les
  745 `actif` : c'est l'identifiant de substitution des annonces sans dossier dans
  l'app, **pas** un défaut.
