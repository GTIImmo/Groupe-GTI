# AUDIT — LA FAMILLE « RECHERCHES » · 3 alertes · 14/10/2026

*Demandé par Frédéric : « vas y audit ».* **Lecture seule, rien n'a été touché.**

---

## En trois lignes

1. **Ce n'est pas 4 022 problèmes, c'est 35 recherches.** Les 4 022 sont des lignes d'historique
   accrochées à ces 35.
2. **24 d'entre elles ont disparu CETTE NUIT** *(du 13 au 14/10)*. Les 11 autres étaient déjà là.
3. ⚠ **Elles existent toujours chez Hektor.** Ce n'est donc **pas** une suppression légitime :
   c'est **notre synchro** qui a cessé de les remonter.

---

## 1. Les trois alertes ne font qu'un seul sujet

| alerte | valeur | ce que c'est |
|---|---|---|
| `data.orphelins_recherche` | **4 022** | des lignes qui pointent vers une recherche absente |
| `data.recherche_disparue` | **35** | des contacts qui ont **perdu** des recherches |
| `data.recherche_orphelin_bloque` | **37** | des orphelins que le robot de nuit ne sait pas réparer |

**Les 4 022 se répartissent ainsi :**

| table | lignes | **recherches distinctes** |
|---|---|---|
| `app_rapprochement_score_history` | 3 791 | **28** |
| `app_rapprochement` | 183 | 21 |
| `app_rapprochement_search_state` | **35** | **35** |
| `app_notification` | 8 | 4 |
| `app_relance_rapprochement` | 5 | 1 |

➡ **35 recherches**, dont une seule *(l'historique des scores)* traîne **3 791** lignes à elle
seule. **Le chiffre de 4 022 est un effet de volume, pas une mesure de gravité.**

---

## 2. Quand ? — la courbe est sans ambiguïté

| passage | lignes accrochées | recherches disparues |
|---|---|---|
| **12/10, toute la journée** | 11 | 6 |
| 13/10 · 01:48 → 05:48 | 11 | 6 |
| 13/10 · 07:48 → 11:48 | ⚠ *journaux illisibles* | |
| **13/10 · 13:48** | **247** *(+236)* | 8 |
| 14/10 · 01:48 → 03:48 | 247 | 8 |
| 14/10 · 05:48 | ⚠ *journal illisible* | |
| **14/10 · 07:48** | **4 022** *(+3 775)* | **35** *(+27)* |

➡ **Deux sauts, tous deux pendant la nuit**, encadrant le **run de 05:00** et la **descente de
07:45**.
⚠ *Les journaux des heures clés font partie des **43 illisibles** signalés dans l'audit du
monitoring. Le trou m'a coûté la précision ici même.*

---

## 3. ⭐ MAIS LES LIGNES ORPHELINES SONT VIEILLES — ce n'est pas elles qui sont nées

Les 35 états de rapprochement devenus orphelins ont été **calculés** :

| calculé le | combien |
|---|---|
| **18/08** | **29** |
| 19/08 · 01/09 · 04/09 · 12/09 | 6 |

**Aucune n'est du 13 ou du 14 octobre.** ➡ **Ce ne sont pas les lignes qui sont apparues, ce sont
les recherches qui ont disparu sous elles.**

Et les repères *(`app_search_count_high_water`)* le confirment :

| repère posé le | contacts | recherches au repère | aujourd'hui |
|---|---|---|---|
| **21/08** | **33** | 34 | **0** |
| 04/09 | 1 | 1 | 0 |
| 12/09 | 1 | 1 | 0 |

---

## 4. ⚠⚠ LE FAIT QUI COMPTE : elles sont toujours chez Hektor

Le **journal quotidien des doublures** *(`app_doublure_journal`, écrit par la Descente)* compare
ce que nous avons à ce que Hektor a :

| relevé | **en accord** *(chez nous)* | **chez Hektor seul** |
|---|---|---|
| 01/10 | 11 427 | 65 694 |
| … *(montée régulière)* … | | |
| 12/10 | 11 471 | 65 699 |
| **13/10** | **11 477** | 65 701 |
| **14/10** | **11 453** ⬇ **−24** | **65 729** ⬆ **+28** |

> **Jusqu'au 13/10, le compte ne faisait que MONTER.** Cette nuit, il a **baissé de 24** — et
> dans le même temps, le compte « Hektor seul » a **augmenté de 28**.

➡ **Les recherches n'ont pas été supprimées : elles sont sorties de NOTRE périmètre.** Elles sont
passées de « chez nous » à « chez Hektor seulement ».

*(Le chiffre de 65 729 « chez Hektor seul » est normal et structurel : nous ne remontons qu'une
partie des recherches — les éligibles. Ce qui est anormal, c'est le **transfert** de 24 lignes
d'un côté à l'autre en une nuit.)*

---

## 5. Ce que je n'ai PAS établi

⬜ **Pourquoi ces 24 recherches sont sorties du périmètre cette nuit.** Deux pistes, non mesurées :

1. **leur contact n'est plus éligible** *(`supabase_sync_eligible`)* — un contact qui sort du
   périmètre emporte ses recherches ;
2. **la recherche n'est plus « active »** chez Hektor — et nous ne remontons que les actives
   *(cf. la note « index actives vs complet »)*.

⬜ **Et je n'ai pas prouvé que notre travail des 12-14/10 n'y est pour rien.** Le chantier ②
*(12/10)* a remplacé **8 politiques de lecture** et trois politiques de rapprochement.
⚠ **En principe** cela ne peut pas être la cause — `service_role` contourne la RLS, et c'est lui
qui fait tourner le run et la descente — **mais je l'écris comme une présomption, pas comme une
mesure.** C'est la première chose à vérifier.

---

## 6. Ce que je recommande

| | | |
|---|---|---|
| **1** ⭐ | **identifier les 24** et regarder **un** cas de bout en bout *(le contact, son éligibilité, sa recherche chez Hektor)* | ~1 h · **c'est là que se trouve la réponse** |
| **2** | vérifier la présomption « la RLS n'y est pour rien » | ~20 min |
| **3** | réparer les **43 journaux illisibles** du moniteur | ils m'ont coûté la précision deux fois aujourd'hui |
| ⛔ | **ne surtout pas purger les 4 022** avant d'avoir compris | ce sont des historiques de rapprochement, pas des déchets |

⛔ **Rien n'est décidé, rien n'a été touché.**
