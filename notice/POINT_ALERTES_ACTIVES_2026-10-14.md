# POINT SUR LES ALERTES ACTIVES — 14/10/2026, passage de 11:48

*Demandé par Frédéric : « il faut traiter chaque erreur de monitoring une par une pour que les
erreurs s'actualisent, mais il faut d'abord faire un point sur les alertes actuelles ».*

**Méthode retenue : on corrige les CAUSES, on ne masque rien.** Lecture seule.

---

## En une page

**8 alertes affichées — mais seulement 5 sujets réels**, parce que trois d'entre elles décrivent
la même chose, et une n'est pas une alerte.

| # | alerte | depuis | sujet réel | qui agit |
|---|---|---|---|---|
| 1 | 🔴 **Travaux console en erreur : 2** | 13/10 | **les 2 gestes plantés** | **Frédéric**, 2 min |
| 5 | 🟠 Gestes abandonnés : 2 | 13/10 | ⤷ *les mêmes 2* | ⤷ *même clic* |
| 3 | 🟠 2 jobs en erreur (48 h) | 13/10 | ⤷ *les mêmes 2, vus sur 48 h* | ⤷ **s'éteint seule demain** |
| 2 | 🔴 **GTI monitor summary** | **14/09** | **ce n'est pas une alerte** | moi, 10 min |
| 4 | 🟠 **Écarts statut / Hektor : 6** *(seuil 4)* | 22/09 | **2 redescentes nouvelles** | à regarder, ~30 min |
| 6 | 🟠 **Lignes accrochées à une recherche disparue : 4 022** | 30/09 | **⚠ la famille « recherches »** | **audit** |
| 7 | 🟠 Recherches disparues : 35 | 30/09 | ⤷ *même famille* | ⤷ |
| 8 | 🟠 Orphelins non rattachables : 37 | 13/10 | ⤷ *même famille* | ⤷ |

---

## 1 + 5 + 3 — LES DEUX GESTES PLANTÉS · 🔴 *depuis le 13/10 à 13:48*

**Trois alertes pour un seul problème**, vu sous trois angles.

| le bien | ce qui s'est passé | faut-il refaire le geste ? |
|---|---|---|
| **61672** « Villa de PP de 1999 » | le travail a échoué *(« Réponse Hektor JSON invalide »)* **mais chez Hektor le bien EST en « Sous offre »** | **non** — le geste a abouti |
| **62963** « TEST C15 entrepot » | **bien d'essai**. La demande le dit : *« Essai du correctif 3c du 14/10 — à remettre en Actif »* | **non** — ce n'est pas un vrai bien |

### ✅ Ce qu'il faut faire — **par Frédéric, 2 minutes**

Ouvrir **la fiche de chaque bien**, et dans le bandeau rouge cliquer **« J'ai refait »**.
⚠ **Pas** le bouton « Résolu » de l'écran Santé : celui-là ne compte pas pour ces alertes.

**Effet** : les alertes **1** et **5** s'éteignent **au passage suivant** *(mon correctif de ce
matin les écoute)*. L'alerte **3** compte les travaux en erreur **des 48 dernières heures** : elle
s'éteindra **toute seule demain**, quand les deux travaux auront dépassé 48 h. **Rien à faire.**

---

## 2 — « GTI monitor summary » · 🔴 *en alerte 318 passages sur 318*

**Ce n'est pas une alerte, c'est le compte rendu du passage** : *« 1 critical, 6 warning »*.
Il est compté comme un incident et s'affiche **au-dessus du vrai incident**.
**Jamais vert depuis un mois — par construction.**

### ✅ Ce qu'il faut faire — **moi, 10 minutes**
Le sortir de « Alertes à traiter », comme je l'ai déjà sorti de l'e-mail ce matin.
*(Front → il faudra pousser.)*

---

## 4 — ÉCARTS ENTRE LA RÈGLE DE STATUT ET HEKTOR : 6 · 🟠 *depuis le 22/09*

Le seuil 4 n'est pas arbitraire. Le code dit : *« les quatre sont des **remontées** […]
**un cinquième écart veut dire que quelque chose a bougé : c'est celui-là qu'on veut voir** »*.

| n° de dossier | Hektor dit | la règle dit | |
|---|---|---|---|
| 18594 · 18865 · VM66700 · VS046 | Actif / Sous offre | Sous offre / Sous compromis | **remontées** — les 4 connues |
| **VT9437** | Sous offre | **Actif** | ⚠ **redescente — nouvelle** |
| **⚠ *(aucun numéro)*** | Sous offre | **Actif** | ⚠ **redescente — et sans numéro** |

⚠ **La ligne sans numéro de dossier** heurte l'une des cinq règles du projet *(« un numéro ne se
perd jamais »)*, et c'était déjà la cause du **défaut 5a** du chantier ③.

### ✅ Ce qu'il faut faire — **~30 min, à décider**
Regarder ces **deux** lignes : pourquoi la règle veut-elle les redescendre, et d'où vient celle
sans numéro. **Puis** l'alerte retombera d'elle-même à 4.

---

## 6 + 7 + 8 — LA FAMILLE « RECHERCHES » · 🟠 *le plus gros sujet*

Trois alertes, **toutes apparues fin septembre**, et qui parlent probablement du même incident.

| | valeur | depuis | ce que le projet en dit |
|---|---|---|---|
| **6** lignes accrochées à une recherche disparue | **4 022** | 30/09 | *« la cause a été corrigée dans le worker le 20/09 et **146 orphelins purgés** le même jour. **Cette sonde dit si ça revient.** »* |
| **7** recherches disparues *(rang qui glisse)* | **35** | 30/09 | *« le nombre de recherches d'un contact ne peut que **CROÎTRE**. Une diminution est **impossible par construction** »* |
| **8** orphelins non rattachables | **37** | 13/10 | *« le balayage nocturne ne sait PAS les réparer : le contact a **plusieurs** recherches vivantes, on ne sait pas laquelle choisir. **Une seule ligne = un cas nouveau à regarder.** »* |

⚠⚠ **Lu ensemble, c'est préoccupant :**

1. La cause des orphelins a été **réparée le 20/09**, et **146** avaient été purgés. Il y en a
   aujourd'hui **4 022** — **27 fois plus**. ➡ **ça revient, et plus fort.**
2. Une baisse du nombre de recherches est dite **impossible par construction** — et **35**
   contacts en ont perdu.
3. Le code attendait **« une seule ligne »** comme signal d'un cas nouveau. Il y en a **37**.

### ✅ Ce qu'il faut faire — **un audit, et c'est le prochain vrai chantier**
**Je n'ai pas encore cherché la cause.** Les trois ont démarré **fin septembre**, ce qui suggère
un seul événement. À faire avant de toucher aux seuils : **ce ne sont pas des réglages, ce sont
des pertes de données possibles.**

---

## L'ordre que je recommande

| | | effet |
|---|---|---|
| **1** | **Frédéric clique « J'ai refait » sur les 2 biens** *(2 min)* | **−2 alertes** au prochain passage, **−3 demain** |
| **2** | je sors le résumé de la liste *(10 min + push)* | **−1 alerte**, et le vrai incident repasse en tête |
| **3** | **l'audit de la famille « recherches »** | le seul sujet qui peut cacher une **perte de données** |
| **4** | les 2 redescentes de statut | **−1 alerte** |

➡ **Après 1 et 2 : il ne resterait que 4 alertes**, et toutes seraient de vrais sujets.

⛔ **Rien n'est décidé, et je n'ai touché à rien.**
