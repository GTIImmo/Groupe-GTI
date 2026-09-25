# Ce qui reste vraiment — le front et les chantiers oubliés

*25/09/2026, après une question de Frédéric : « je ne comprends pas, il y avait pourtant
encore des choses à faire au niveau de l'autonomie… a-t-on fini la partie front ? Il y avait
un problème sur l'avenant. Peux-tu vraiment vérifier ? »*

⚠ **Il avait raison, et ma réponse précédente était trop rapide.** J'avais conclu « le reste
du plan fonctionne » à partir d'une seule mesure : *36 types de travaux, 0 en erreur*. **Cela
prouve que rien n'est bloqué, pas que les chantiers sont finis.** Un geste jamais lancé ne
produit aucune erreur.

## 1. Le front — trois chantiers que la mémoire croyait éteints sont ALLUMÉS

Les trois grands chantiers d'écran vivent derrière un drapeau, lu au moment de la
**compilation** : Vite fige sa valeur dans le fichier livré. **Lu dans le code déployé le
25/09** *(`index-BIEZJmYI.js`)* :

```
S0 = ["true","1","on","yes"].includes("true"...)   COCKPIT_V2   -> ALLUME
kI = ["true","1","on","yes"].includes("true"...)   CONTACT_V2   -> ALLUME
ES = ["true","1","on","yes"].includes("true"...)   MANDAT_V3    -> ALLUME
```

| chantier | ce que disait la mémoire | **la réalité, mesurée** |
|---|---|---|
| **Cockpit V2** | *« mergé, flag OFF »* | **ALLUMÉ en production** |
| **Fiche contact V2** | *« en attente »* | **ALLUMÉ en production** |
| **Mandat V3** | *« flag OFF, Lot 1 fait, reste 2-7 »* | **ALLUMÉ en production** |
| **Création optimiste** | *« flag OFF, reste commit ④ + flip »* | **ALLUMÉE** — `PROVISIONAL_CREATION_ENABLED = true`, en dur dans le code |

➡ **Quatre entrées de mémoire étaient périmées.** Les utilisateurs voient déjà ces écrans.
⚠ **Mais « allumé » ne veut pas dire « fini »** : ce qui restait à coder dans chaque lot
*(les relances et l'agrégateur d'activité du contact V2, les lots 2 à 7 du mandat V3, les
rubriques du cockpit non re-skinnées)* **n'a pas été vérifié écran par écran** — et ça ne
peut se faire qu'en regardant l'app connectée, avec toi.

## 2. L'avenant — codé, déployé, mais le manque est ailleurs

- Le commit `3e5188b` *(30/06)* **est dans `main`**, donc déployé. La mémoire disait *« non
  poussé »* : **périmé**.
- L'éditeur existe bel et bien : 121 occurrences dans `App.tsx`, un sélecteur
  `mandat / avenant`, un PDF dédié, et le champ `avenantNewPrice` porté jusqu'au worker.

**Le vrai manque est celui que la liste décrit en `E.0-bis`** *(ligne 1071)* :

> **modifier un MANDAT existant (dates, durée, avenant qui prolonge)** — **seuls prix,
> honoraires et surface le sont.**

➡ **L'avenant sait changer le PRIX. Il ne sait pas PROLONGER un mandat** (dates, durée).
C'est un des trois gestes de `L5`, chiffré 2-3 j.

## 3. Ce qui reste, honnêtement

### Chantiers d'écran — allumés, mais pas nécessairement finis
| | à vérifier avec Frédéric, écran par écran |
|---|---|
| Fiche contact V2 | les relances et l'agrégateur d'activité |
| Mandat V3 | les lots 2 à 7 |
| Cockpit V2 | les rubriques non re-skinnées *(`documents`, `mandat`, `rdv` le sont)* |
| Refonte vue Estimation | la mémoire dit *« non commité »* — **à revérifier** |
| PDF estimation + mail | la mémoire dit *« planifié, pas codé »* — **à revérifier** |

### Gestes manquants — mesurés, confirmés
| | |
|---|---|
| **prolonger un mandat** *(dates, durée)* | 2-3 j — `L5` |
| **photos** : supprimer, réordonner, principale | 2-3 j — `L5`, ⚠ commandes Hektor **inconnues** |
| **fusionner des doublons** | 2-4 j — `L5`, **arbitrage de Frédéric** |

### Chantiers de fond
| | |
|---|---|
| **`D.0`** documents | **arrêté depuis 33 jours** — le plus urgent |
| **photos** | 13 437 vignettes chez Hektor, 1,7 % rapatriées, **chemin d'affichage à trancher** |
| **`L9`** registre des mandats | ⚠ **avant** la coupure, il se remplit depuis le miroir |
| **`A.1` / `A.2`** portails, signature | **à zéro** — ils fixent la date |

## 4. La leçon

**« Zéro erreur » n'est pas « terminé ».** Mesurer les travaux en échec dit seulement que rien
n'est coincé. Pour savoir si un chantier est fini, il faut **regarder ce qu'il devait
produire**, pas ce qu'il n'a pas cassé.

**Et la mémoire vieillit** : quatre entrées disaient « flag OFF » alors que les écrans sont
allumés depuis un moment. ➡ **Avant de répondre sur l'état d'un chantier, lire le code
déployé, pas la note.** C'est déjà la règle du projet *(CLAUDE.md §4)* ; elle vaut aussi
pour la mémoire.
