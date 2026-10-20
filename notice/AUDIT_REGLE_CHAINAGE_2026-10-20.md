# AUDIT — LA RÈGLE DE CHAÎNAGE, RELUE DANS LE CODE

**20/10/2026. LECTURE SEULE** — rien n'a été modifié, la simulation tourne en mémoire.

Demandé par Frédéric : *« Non, ce n'est pas normal, une vente doit aussi s'ajouter à une
offre acceptée ou non s'il y a correspondance. Revérifie la règle de chaînage en détail
et explique-moi. »*

> ⭐ **Il a raison, et c'est chiffré** : la correction qu'il demande réunit **97 chaînes**
> et fait tomber les anomalies de **140 à 42**.

---

## 0. LA VALIDATION DE LA MESURE — à lire en premier

J'ai **recopié la règle** de `phase2/sync/affaire_ledger.py` (l. 1164-1327) dans une
simulation, et je l'ai rejouée sur le parc.

```
31 065 / 31 066 affaires retombent sur LE MEME numero de chaine  ->  100,00 %
un seul ecart (affaire 24291)
```

➡ **La simulation reproduit la règle réelle.** Les chiffres qui suivent valent donc
quelque chose. *(Sans ce contrôle, ce document serait une opinion.)*

---

## 1. LA RÈGLE, TELLE QU'ELLE EST ÉCRITE

Pour **chaque bien**, les transactions sont prises **dans l'ordre des dates**
*(offre avant compromis avant vente à date égale)*, et le programme tient une liste des
**chaînes encore ouvertes**.

### Une OFFRE *(l. 1210-1252)*

```
elle cherche une chaine ouverte qui
      n'a PAS encore de compromis
  ET  partage AU MOINS UN NOM d'acquereur
sinon -> elle ouvre sa propre chaine

si TOUTES les offres de la chaine sont refusees -> la chaine se FERME
```

✅ **C'est la seule des trois branches qui regarde le NOM.**

### Un COMPROMIS *(l. 1254-1266)*

```
il cherche L'UNIQUE chaine ouverte qui
      porte une OFFRE ACCEPTEE
  ET  n'a pas encore de compromis
s'il y en a plusieurs, ou aucune -> il ouvre sa propre chaine

s'il est annule -> la chaine se FERME
```

⚠ **Il ne regarde pas le nom.** Il se fie à l'unicité.

### Une VENTE *(l. 1268-1309)*

```
elle cherche L'UNIQUE chaine ouverte qui PORTE UN COMPROMIS
s'il y en a plusieurs, ou aucune -> elle part SEULE, et se ferme aussitot
```

⚠⚠ **Elle ne regarde ni le nom, ni les offres acceptées.** C'est la branche la plus
pauvre des trois, alors que c'est elle qui conclut l'affaire.

### L'asymétrie, en un tableau

| | regarde le **nom** ? | à quoi elle se raccroche | repli si ça échoue |
|---|---|---|---|
| **offre** | ✅ **oui** | une chaîne sans compromis, **même nom** | elle ouvre la sienne |
| **compromis** | ❌ non | l'**unique** chaîne à offre acceptée | il ouvre la sienne |
| **vente** | ❌ non | l'**unique** chaîne à **compromis** | ⛔ **aucun** — elle part seule |

---

## 2. LES TROIS FAILLES, MESURÉES

| | nombre | ce qui se passe |
|---|---|---|
| **vente sans compromis ouvert** | **132** | l'affaire va de l'offre à la vente sans compromis enregistré → **deux chaînes** |
| **vente : plusieurs compromis ouverts** | **8** | elle renonce *(« on ne devine pas »)* alors que **le nom suffirait** |
| **transaction sans date exploitable** | **213** | chacune seule — dont les compromis à `0000-00-00` *(le « vide » de Hektor)* |

### Un cas réel, pour voir

```
bien 54699 · ARNAUD Jean-Luc
   affaire 28132   offre ACCEPTEE  10/11/2024   chaine 28132
   affaire 28133   VENTE           08/02/2025   chaine 28133   <- une AUTRE chaine
```

Même bien, même acheteur, offre puis vente. La vente cherche un **compromis** ouvert, n'en
trouve aucun *(il n'y en a jamais eu)*, et **part seule**. L'écran montre alors une affaire
« offre acceptée » et une affaire « vendue » là où il n'y en a qu'une.

---

## 3. CE QUE LA CORRECTION DE FRÉDÉRIC DONNE

### ① Repli sur l'offre acceptée + le nom qui départage

```
chaines : 12 702  ->  12 611        (-91)
transactions reattachees : 93

  51  vente SANS NOM rattachee a l unique offre acceptee
  36  vente rattachee a une offre acceptee, NOM COMMUN
   3  vente avec un nom, rattachee a l unique offre acceptee
   2  le NOM a departage plusieurs compromis ouverts

reste : 42 ventes vraiment seules  +  6 ambigues
```

### ② Et « acceptée **ou non** », comme il le demande

```
chaines : 12 611  ->  12 605        (-6 de plus)
   6  vente rattachee a une offre NON acceptee, NOM COMMUN
reste : 38 ventes vraiment seules  +  4 ambigues
```

### Le bilan

| | aujourd'hui | corrigé |
|---|---|---|
| chaînes | 12 702 | **12 605** *(-97)* |
| anomalies de vente | **140** | **42** |

---

## 4. CE QUE JE PROPOSE, ET CE QUE JE NE PROPOSE PAS

### ✅ La correction, en trois replis, dans cet ordre

```
1. l'UNIQUE chaine ouverte a compromis            (la regle actuelle, inchangee)
2. sinon, le NOM departage plusieurs compromis    (+2)
3. sinon, une chaine a OFFRE ACCEPTEE :
      a. une seule au NOM COMMUN                  (+36)
      b. sinon l'unique, meme sans nom            (+54)
4. sinon, une chaine a offre NON acceptee au NOM COMMUN   (+6)
5. sinon -> elle part seule, ET ON LE DIT          (38 restantes)
```

⭐ **Le repli 3b reprend exactement la logique que le compromis applique déjà** *(« l'unique
candidate »)* : ce n'est pas une invention, c'est une symétrie rétablie.

### ⛔ Ce que je ne propose PAS

- **deviner quand il y a plusieurs candidates sans nom commun** — les 38 + 4 restantes
  doivent rester seules **et signalées**. *« Dans le doute on s'abstient ET on le dit. »*
- **toucher aux 213 sans date** — c'est un autre sujet *(les `0000-00-00` de Hektor)*,
  à traiter séparément.

---

## 5. ⚠ CE QUE ÇA TOUCHE AILLEURS — obligatoire avant tout « vas-y »

| | |
|---|---|
| **les écrans** | 93 transactions changent de chaîne → les fiches qui montraient deux affaires n'en montreront qu'une. **C'est le but**, mais ça se voit |
| **`app_affaire_repartition`** | elle porte `app_chaine_id` : **16 062 lignes** à revérifier après coup *(aujourd'hui 1 orpheline ; il ne faut pas en créer 97)* |
| **le classeur** | l'appariement des 4 329 lignes se refait sur une base saine — **les 37 « ventes manquantes » tombent à ~3** |
| **le push nocturne** | `recalculer_les_chaines` tourne à chaque run *(0,09 s)* : la correction s'applique d'elle-même, **sans migration** |
| **le retour arrière** | une **photo des chaînes avant** se prend comme le 04/09 *(`CHAINES_AVANT_REFONTE_2026-09-04.json`, avec son champ `retour_arriere`)* |

⚠ **Et la règle vit à QUATRE endroits** *(le commentaire du code le dit)* : le run, le
front, Supabase, et le contrôle `fermee_selon_le_run()`. **Changer le run seul recréerait
la divergence corrigée le 16/09.** Les quatre doivent être balayés.

---

## 5-bis. ⚠ UNE QUATRIÈME OBSERVATION — **470 cas, et je ne dis PAS que c'est un défaut**

En sortant des cas réels pour illustrer, j'ai vu ceci :

```
bien 171 :
   offre     75   REFUSEE    04/08/2023   Sokol DAKAI    chaine 75
   compromis 74   ANNULE     21/09/2023   Sokol DAKAI    chaine 74   <- autre chaine
   offre     76   acceptee   02/11/2023   Ayache OMARI   chaine 73
   compromis 73   active     02/11/2023   Ayache OMARI   chaine 73
   vente     77              22/12/2023   Ayache OMARI   chaine 73
```

La tentative DAKAI, qui a échoué, compte **deux chaînes** : l'offre refusée d'un côté,
le compromis annulé de l'autre. **Mesure : 470 compromis annulés dont l'offre refusée du
même nom est sur une autre chaîne.**

⛔ **MAIS CE N'EST PEUT-ÊTRE PAS UN DÉFAUT**, et c'est à Frédéric de le dire. Sa propre
règle du 04/09 pose que *« l'état ferme la chaîne, pour permettre d'en ouvrir une
autre »* : une offre refusée **ferme**. Si un compromis arrive ensuite avec le même
acheteur, est-ce **la même affaire qui a repris**, ou **une seconde tentative** ?

⚠ **Et c'est 3,5 fois plus gros que le problème des ventes** (470 contre 132). Je ne
propose rien dessus tant que la question n'est pas tranchée.

---

## 6. CE QUI RESTE À TRANCHER PAR FRÉDÉRIC

```
1. On applique les replis 1 a 4, ou seulement 1 a 3 (sans les offres non acceptees) ?
2. Le repli 3b -- rattacher SANS nom commun, sur la seule unicite -- est le plus
   gros gain (54) et le moins sur. On le garde ?
3. Les 213 transactions sans date : autre chantier, ou tout de suite ?
4. Les 4 ecritures de la regle : on les aligne toutes en meme temps ?
```

**Simulation** *(scratchpad, non versionnée)* : `simuler_chainage.py` — elle rejoue la
règle réelle, la corrige, et compare. Aucune écriture.
