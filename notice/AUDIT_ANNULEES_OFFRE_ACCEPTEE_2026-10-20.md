# AUDIT — « Annulée » au classeur, « offre acceptée » chez nous

**20/10/2026, après le chaînage V2 et le § 2.6. LECTURE SEULE.**

Demandé par Frédéric : *« audite les 114 — le dernier gisement côté classeur »*.

> ⚠ **LA MÉTHODE EST CELLE QUI A MARCHÉ SUR LES 37** : on vérifie **d'abord
> l'appariement**, avant de conclure que nos données ont tort. Sur les 37, **33
> n'étaient pas des trous dans nos données — c'était le chaînage.**

---

## 0. LE VERDICT, EN TROIS LIGNES

```
elles sont 87, pas 114 -- le § 2.6 en a regle 27 de plus
  2  mauvais appariement
 85  appariement BON, et la notre app est VRAIMENT en retard
     dont 84 sur des biens vendus/clos/archives  -> consequence cosmetique
     dont  1 sur un bien VIVANT                  -> un vrai probleme, aujourd'hui
```

⭐ **Ce n'est donc pas un gisement : ce sont 84 traces historiques et UN cas réel.**
J'avais annoncé *« le dernier gisement sérieux »* — c'était trop dire.

---

## 1. L'APPARIEMENT : bon à 97 %

```
85  aucune meilleure chaine sur le bien      -> l'appariement tient
 2  un ECHEC existe au MEME NOM              -> mauvais appariement
      L3863  mandat 4139  « DEBARD »         chaine 20089 -> l'echec est 20088
      L3926  mandat 4298  « ROCHELEMAGNE »   chaine 19712 -> l'echec est 19711
```

⚠ **Contraste avec les 37** *(où 33 sur 37 étaient un défaut d'appariement)* : ici
c'est l'inverse, 85 sur 87 sont bien appariées. **Le chaînage n'est plus en cause.**

---

## 2. CE QUE DIT L'HISTOIRE DE L'OFFRE, CHEZ HEKTOR

```
85 sur 85 (100 %)  son historique ne porte QU'UNE acceptation -- AUCUN refus
```

Chaque offre de Hektor porte son journal d'événements *(`proposition`, `accepte`,
`refus`, datés)*. Sur les 85, **aucun refus n'y figure**.

➡ **Personne n'a jamais dit à Hektor que ces offres étaient mortes.** Ce n'est pas une
divergence d'interprétation : l'information n'existe **que** dans le classeur.

---

## 3. L'ÂGE : elles sont gelées

```
82 sur 85 (96 %)  plus de DEUX ANS sans rien derriere
 1  entre 1 et 2 ans
 1  entre 6 et 12 mois
 1  moins de 6 mois   <- le seul cas vivant
```

Une offre acceptée sans rien derrière depuis deux ans n'est pas une offre acceptée.

---

## 4. ET LE CLASSEUR SAIT QUAND

```
85 sur 85 (100 %)  le classeur porte une DATE d'annulation
```

⭐ **Il est la seule source, et il est complet.**

---

## 5. ⚠ LA GRAVITÉ RÉELLE : **un seul bien vivant**

```
84 sur 85 (98 %)  bien vendu / clos / archive  -> consequence cosmetique
 1 sur 85 ( 1 %)  bien VIVANT                  -> il passe pour ENGAGE a tort
```

### Le cas unique, en entier

```
bien 62106 · « Maison d'habitation de 1970 sur sous-sol et terrain » · Bessamorel
   statut de l'annonce        ACTIF
   prix affiche               139 000
   mandat                     06/05/2026 -> 05/07/2027, pas de cloture

   NOUS :    offre 28956 (chaine 28956) ACCEPTEE le 04/08/2026 a 137 000
             historique Hektor : proposition 31/07 · accepte 04/08 · (aucun refus)
   LE CLASSEUR : annulee le 28/09/2026  (mandat 18594, M. CHENET Wilfrid)
```

⚠ **Conséquence concrète, aujourd'hui** : ce bien est **ACTIF et affiché comme engagé**
par une offre acceptée qui est tombée il y a trois semaines. Le négociateur voit un bien
pris alors qu'il est libre.

---

## 6. ⛔ ET VOILÀ LE PROBLÈME DE FOND, QUI EST NOUVEAU

**Nous n'avons aucun endroit pour écrire cette information.**

L'« état » d'une affaire **se déduit** — il n'est stocké nulle part *(mesure du 19/10 :
4 329 accords sur 4 329 entre les deux vocabulaires)*. Pour que notre état dise
« échec », il faut que **le `state` de l'offre passe à `refused`** — et `state` est une
**valeur de Hektor**, réécrite à chaque run.

➡ **C'est le premier champ où le classeur sait quelque chose que nous ne pouvons pas
ranger.** Les trois champs que l'audit du 19/10 lui attribuait *(commission, charge,
répartition)* avaient tous une maison chez nous. Celui-là, non.

### Les trois sorties, et je n'en choisis aucune

| | |
|---|---|
| **A — signaler** | une liste, et rien d'autre. Coût nul, le défaut reste. |
| **B — une colonne de classe A** `state_app` sur l'offre, lue en `COALESCE(state_app, state)` | ⭐ **c'est le patron du projet**, déjà en production pour les photos *(24 497 lignes)*, la clôture de mandat et la commission. Notre écran dirait la vérité, Hektor garderait la sienne. |
| **C — envoyer le refus à Hektor** | ⛔ un geste d'écriture chez Hektor, sur **85 affaires dont 84 archivées**. Disproportionné, et il faudrait son accord. |

⭐ **B est la réponse naturelle** : elle est la seule qui fasse dire la vérité à l'écran
sans toucher à Hektor, et le projet sait déjà la faire. Mais c'est **une colonne de plus
et une décision**, donc elle attend Frédéric.

⚠ **Et pour le seul bien vivant, aucune des trois n'est urgente** : il suffit que
quelqu'un **refuse l'offre dans Hektor** — le geste existe, l'app le sait faire, et le
run le redescendra dans la nuit.

---

## 7. ⚠ UNE ERREUR DE MA PART, DITE

Mon dernier contrôle rendait *« est-il dans l'index des vivants ? False »* pour le bien
62106, en contradiction avec la mesure d'avant. **La colonne est un `integer`** : demander
`hektor_annonce_id = '62106'` *(du texte)* rend **0**, `= 62106` rend **1**.
➡ **Comparer un nombre à du texte en SQLite ne lève pas : ça rend faux en silence.**
Même famille que *« le nom d'une colonne ment »*.

---

## 8. CE QUI RESTE, APRÈS CET AUDIT

```
  1  bien VIVANT a corriger (62106) -- un refus d'offre dans Hektor suffit
  2  mauvais appariements a regarder (mandats 4139 et 4298)
 84  traces historiques : la decision B (colonne de classe A) ou rien
```

**Et le compte des écarts classeur <-> app, après la journée :**

```
avant le chainage V2 :  37 ventes manquantes · 114 « Annulee »
apres                :   4 ventes manquantes ·  87 « Annulee »
                         dont 85 bien appariees, dont UN seul bien vivant
```
