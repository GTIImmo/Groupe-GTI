# LES CORRECTIFS, MESURÉS AVANT D'ÊTRE ÉCRITS — recherches orphelines · 14/10/2026

*« Continue d'auditer et mesure tes propositions de correctif »* — Frédéric.
**Lecture seule. Aucun correctif n'a été posé.** *(Cause : `notice/AUDIT_RECHERCHES_ORPHELINES_2026-10-14.md`.)*

---

## 0. Ce que la suite de l'audit a d'abord ÉLIMINÉ

| hypothèse | mesure | verdict |
|---|---|---|
| *on a perdu du travail d'utilisateur* | `app_search_pending` = **1** recherche possédée par l'app, dont **0** disparue · `app_search_provisional` = **0** | ⛔ **non — aucun travail perdu** |
| *des clés ont changé (hash du contenu)* | sur les **21** clés orphelines de `app_rapprochement` : **21 = archivage**, **0 = changement de clé** | ⛔ **non — pas réalisé** |

➡ **Une seule cause, confirmée : l'archivage chez Hektor.** Les deux aggravants restent des
**risques théoriques**, pas des dégâts.

---

## 1. ⭐ LE DÉFAUT EXACT : deux mécanismes qui se contredisent

Le nettoyage **existe déjà** et il est **bien conçu** — `app_sweep_search_orphans()` ne supprime
rien, elle **rattache** :

> *« 1) le contact a UNE SEULE recherche ACTIVE → c'est la cible évidente »*
> *« 2) aucune active, mais UNE SEULE recherche en tout → **mieux vaut l'y rattacher que de
> laisser l'historique orphelin** »*

⚠ **Mais elle ne peut rien faire ici** : le push a **supprimé** la recherche de Supabase, donc le
contact n'a plus **aucune** recherche — ni active, ni archivée. **Il n'existe plus aucune cible.**

> **Un mécanisme suppose que la recherche existe encore, même archivée. L'autre la supprime.**
> C'est tout le défaut, et il explique aussi les **37 « orphelins non rattachables »** : la
> fonction tourne, et elle ne trouve rien à quoi rattacher.

---

## 2. LES OPTIONS, MESURÉES

| | ce qu'on change | effet mesuré | coût mesuré |
|---|---|---|---|
| **A** | ne plus supprimer une recherche **déjà poussée** | identique à B en pratique *(l'état de push porte 11 453 clés)* | — |
| **B** ⭐ | **garder les recherches de tout contact DÉJÀ POUSSÉ**, même devenu inéligible | **les 36 ne seraient pas parties**, et le nettoyage retrouve une cible | **11 489 au lieu de 11 453 = +36 lignes** |
| **C** | garder aussi les archivées des contacts éligibles | **aucun effet** — `-IncludeArchivedContactSearches` le fait déjà | 0 |
| **D** | supprimer les 4 022 orphelins | l'alerte s'éteint | ⛔ **on perd l'historique de rapprochement** |

### ⭐ B est le correctif : **il coûte 36 lignes**

Et ces 36 lignes sont **exactement** les recherches perdues. Le principe tient en une phrase :

> **Une recherche qui a déjà existé dans Supabase n'en est plus retirée parce que son contact
> s'est endormi.**

**Ce que ça répare, en chaîne** : la recherche reste *(archivée, `is_active = 0`)* → le contact a
de nouveau « une seule recherche en tout » → **le cas 2 du nettoyage existant se déclenche tout
seul** → l'historique est **rattaché** au lieu d'être orphelin.
**Les deux mécanismes se remettent d'accord, sans rien réécrire du nettoyage.**

---

## 3. ⚠ CE QUE B NE FAIT PAS

**B empêche que ça recommence. Il ne répare pas les 4 022 d'aujourd'hui** — leurs recherches sont
déjà supprimées de Supabase.

**La séquence de réparation serait :**

| | | |
|---|---|---|
| 1 | poser **B** | les 36 remontent au push suivant |
| 2 | laisser tourner `app_sweep_search_orphans()` | elle rattache enfin les 4 022 |
| 3 | contrôler | les 3 alertes doivent tomber à 0 |

### ✅ VÉRIFIÉ : le nettoyage tourne, et il travaille

`app_sweep_search_orphans_log` — **tous les jours à 05:00**, et il rattache pour de vrai :

| passage | rapprochements rattachés | historiques de score |
|---|---|---|
| **14/10 05:00** | **16** | **212** |
| 13/10 · 12/10 · 11/10 | 0 | 0 |
| 10/10 | 27 | 370 |
| 08/10 | 37 | 44 |
| 07/10 | 42 | 242 |

➡ **La fonction marche. Elle échoue UNIQUEMENT là où la recherche a été supprimée de Supabase**
— c'est-à-dire exactement le cas que **B** empêcherait. **Le diagnostic est confirmé par le
comportement observé, pas seulement par la lecture du code.**

---

## 4. CE QUI RESTE NON MESURÉ — et que je ne cache pas

1. ⬜ **Le volume futur de B.** +36 aujourd'hui ; je n'ai pas mesuré combien de contacts
   s'endorment par mois. *(Repère : 11 427 → 11 477 en 12 jours, soit ~+4/jour en montée nette.)*
2. ⬜ **L'aggravant « clé = hash du contenu »**. Non réalisé aujourd'hui *(0 cas sur 21)*, mais le
   code est formel : `stable_hash({contact_id, index, **search**})`. **Un changement de critère
   détacherait l'historique exactement pareil**, et B n'y changerait rien.
3. ⬜ **Ce que Frédéric a signalé** : *« les modifications de recherche ne sont pas envoyées à
   Hektor »*. Aujourd'hui sans conséquence *(1 seule recherche possédée par l'app)* — mais le
   jour où l'app en portera beaucoup, le point 2 deviendra un vrai sujet.
4. ⬜ **Où poser B exactement.** Le filtre vit dans `push_contacts_to_supabase.py` l. 639-644
   *(`search_where`)*, et la suppression dans `find_stale_row_keys` l. 229-246. ⚠ **Le push
   décide en LOCAL**, alors que les références *(rapprochements)* sont **dans Supabase** : on ne
   peut donc pas filtrer sur « est-elle référencée ». **C'est pourquoi B s'appuie sur l'état de
   push local, qui, lui, est disponible.**

---

## 5. Ce que je recommande

| | | |
|---|---|---|
| **1** ⭐ | **mesurer si `app_sweep_search_orphans()` tourne**, et à quelle heure | 15 min · **conditionne tout le reste** |
| **2** ⭐ | **poser B** *(+36 lignes)*, derrière une option, et l'éprouver à vide | ~1 h 30 |
| **3** | contrôler que les 3 alertes tombent, puis documenter | le lendemain |
| **4** | ⬜ décider du sort de l'aggravant « clé-hash » | autre chantier |

⛔ **Rien n'est décidé, rien n'a été touché, rien n'a été purgé.**
