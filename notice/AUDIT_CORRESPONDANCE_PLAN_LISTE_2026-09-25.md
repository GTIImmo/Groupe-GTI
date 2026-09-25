# Audit — le plan et la liste ne parlent pas la même langue

*25/09/2026, demandé par Frédéric (« mais e3 et L5 ne sont pas dans le plan ? » puis
« avant, audit pour être sûr, ensuite réorganise »). Lecture seule : plan, liste, code,
les deux bases. Rien n'a été modifié pendant l'audit.*

## 1. Le constat

**Les deux documents nomment les mêmes travaux différemment**, et aucun ne porte la table
de correspondance :

- **le plan** (`PLAN_DEV_ACTUALISE_2026-08-20.md`) raisonne en **lots** : `L0` … `L9` ;
- **la liste** (`LISTE_TACHES_A_COCHER_2026-08-29.md`) raisonne en **tâches historiques** :
  `C.9`, `D.0`, `E.0-bis`, `A.2`, `0.3`…

D'où la question de Frédéric : **`e3` et `L5` y sont bien**, mais sous d'autres noms —
`e3` est la 3ᵉ pièce de `C.9-e` (liste, l. 420), et `L5` s'appelle `E.0-bis` (liste, l. 901).

## 2. La table de correspondance — établie en lisant les deux documents

| lot du plan | = ces tâches de la liste | état réel |
|---|---|---|
| **L0** ✅ | `C.1'` la relecture efface une saisie · le renvoi partiel sans fin · `C.4` · `C.17-ter` | fini le 20/09 — **2 cases restées ouvertes à tort**, voir §3 |
| **L1** ✅ | `5b` · `4-suite` · clé des relations · `E.4`/`6.1-6.3` le distributeur | fini le 21/09 (`E.4` « le jour J » reste, c'est un **geste**, pas du code) |
| **L2** ✅ | `26bis-CONTACTS` · `-RELATIONS` · `-COUPLES` · `-RECHERCHES` · `INVENTAIRE` | fini le 21/09 |
| **L3** ✅ | la carte des champs · protection par champ · chantier 2 · **`C.16`** | fini le 21/09 — **3 cases `C.16` restées ouvertes à tort**, voir §3 |
| **L4-b′** ✅ | les 9 sortants · `normalizeMandatContactIds` · la qualification | fini le 22/09 |
| **L4-c** ✅ | ① à ⑥, la bascule d'identité du contact | jouée le 23/09 — **2 cases restées ouvertes** |
| **L4** 🟡 | `L4-a` · `L4-b` · **`C.9`** · `C.9-couple` · `26bis-TRANSACTIONS` · `4.3` | **C.9 codé de a à f** ; restent 3 gestes + 3 tâches |
| **L5** | **`E.0-bis`** *(mandat existant, photos, fusion de doublons)* · les **102 + 40 champs** · `C.13` · supprimer une annonce · brouillons · retirer les liens « Ouvrir Hektor » | **rien de commencé** |
| **L6** | **`D.0`** documents et mandats signés · signature · diffusion · n° de mandat | **`D.0` à l'arrêt depuis le 23/08** |
| **L7** | `D.1a` · `D.1` · `D.2` · garder la copie des photos | rien de commencé |
| **L8** | `C.4-bis` élargi · `E.3` · `0.3`/`E.1` rattrapages · `E.2` | rien de commencé |
| **L9** | `A.3-technique` · les 3 couches de numérotation · `C.13-c` · le négociateur manquant | ⚠ **se remplit depuis le miroir : à finir AVANT la coupure** |
| *hors lot* | `A.1` portails · `A.2` signature · `A.3` juridique | **à zéro — fixent la date de coupure** |
| *hors lot* | `C.19` transactions *(3.5, 2.4, 3.2c, 4.1…)* · `C.11` ménage · `B.3` · `F.1` | petits ou après la coupure |

## 3. Onze cases périmées — vérifiées dans le code, pas déduites

| l. | la case dit | ce que dit le code ou la base |
|---|---|---|
| 245 | « la bascule : faire lire `app_contact_id` » | **jouée le 23/09** ; l'audit du 22/09 avait montré que les 87 points d'API et ~60 du front n'avaient rien à changer |
| 249 | « le registre des recherches, dans le même geste » | fait le même jour |
| 270 | « le numéro figé dans le JSON d'agenda » | **9 traduits** ; reste **1** lien vers le contact 603496, qui n'existe **nulle part** — contact supprimé chez Hektor, pas un reste de bascule |
| 299 | « C.9 la création d'annonce » | **a → f codés** ; restent 3 gestes, aucun n'est du code |
| 420 | « C.9-e » | e1, e2, e3 cochés dessous ; **seul l'allumage de e3 reste** |
| 530 | « 7 annonces invisibles » | 3 revenues, **3 sont des brouillons** *(étiquetés tels dans le miroir)* ; **reste 63122** |
| 832 | « la relecture efface une saisie en conflit » | **corrigé le 20/09** : `push_single_annonce_to_supabase.py` ne supprime plus la ligne en conflit *(commentaire daté dans le code, l. 681)* |
| 835 | « une saisie partielle se renvoie sans fin » | **corrigé** : `app_annonce_enqueue_due_pushes` filtre bien `partial` *(vérifié dans la fonction Supabase)* |
| 843 | « marquer disparues les 825 actives » | **le mécanisme tourne chaque nuit** *(`marquer_contacts_disparus.py`, run l. 517)* : **7 660 fiches marquées**, dont 7 658 ce matin |
| 844 | « traiter les 5 454 archivées » | couvert par le même mécanisme : il marque **toutes** les fiches inconnues de Hektor |
| 845 | « poser le mécanisme *un contact a quitté le listing* » | **posé** — c'est ce script |

⚠ **Mais `C.16` a un défaut connu, noté le 24/09 et non traité** : le registre lève chaque
nuit les 7 658 marques, que `C.16` repose aussitôt. L'état final est juste, **la date
« absent depuis » est réécrite chaque nuit**. À traiter, mais ce n'est plus « poser le
mécanisme ».

## 4. Le compte, corrigé

| | |
|---|---|
| cases ouvertes dans tout le document | 121 |
| dont **archive répétée** *(après la l. 944 : les mêmes tâches sous d'anciennes sections)* | 72 |
| **liste vivante** *(sections 1 à 12 + page de tête)* | **49** |
| dont **périmées** *(§3)* | **11** |
| **tâches réellement ouvertes** | **38** *(+ les 5 gestes de Frédéric)* |

⭐ **Après correction (25/09) : 41, pas 38.** Corriger les 11 cases périmées a **révélé
trois vraies tâches** qu'elles masquaient : le lien d'agenda vers le contact 603496 · la
seule annonce vraiment anormale, 63122 · le va-et-vient C.16 ↔ registre sur la date
« absent depuis ». Une case périmée ne cache pas que du vide.

## 5. Ce que la réorganisation doit faire

1. **Poser la table de correspondance** (§2) en tête de la liste — elle n'existe nulle part.
2. **Corriger les 11 cases périmées**, avec leur mesure, sans en effacer l'histoire.
3. **Nommer l'archive** : marquer clairement où s'arrête la liste vivante (l. 944), pour que
   les 72 répétitions ne soient plus recomptées.
