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

---

## 6. LE CORRECTIF EST POSÉ — *« Oui » de Frédéric, 14/10*

### Ce qui change, en une phrase

> **Une recherche qui a déjà existé dans Supabase n'en est plus retirée parce que son contact
> s'est endormi.**

| fichier | ce qui change |
|---|---|
| `phase2/sync/push_contacts_to_supabase.py` | une **option** `--garder-recherches-deja-poussees`, **éteinte par défaut**, qui élargit le périmètre d'un `OR` |
| `run_full_pipeline.ps1` | le switch `-GarderRecherchesDejaPoussees` |
| `scheduled/run_quotidien.ps1` | **l'option est allumée** pour le run de 05:00 |

**Le comportement par défaut ne change pas.** Syntaxe PowerShell validée sur les deux scripts.

### ⭐ LE TÉMOIN INVERSE A RATTRAPÉ UN CORRECTIF MORT-NÉ

**Ma première version s'appuyait sur l'état de push des RECHERCHES.** Mesure : **+0**.
**Elle n'aurait rien fait.** Et elle serait partie en production sans que rien ne le dise.

**Pourquoi** : le push **met à jour son état en même temps qu'il supprime**. L'état de push des
recherches a donc **déjà oublié** les 36 lignes. Une clause bâtie dessus ne pouvait rien voir.

➡ **La bonne version s'appuie sur l'état de push des CONTACTS**, qui est **intact** : le contact
n'est jamais supprimé de Supabase, il cesse seulement d'être mis à jour.

### L'épreuve, sur la VRAIE base, en lecture seule

| | |
|---|---|
| option **éteinte** | **11 453** recherches poussées |
| option **allumée** | **11 489** — soit **+36** |
| les 36 lignes en plus | **toutes inactives**, pour **35 contacts** |
| et ce sont | **exactement** les 36 absentes de Supabase aujourd'hui |
| 5 contacts testés sur 5 | **retrouvent une recherche** → le ménage de 05:00 aura une cible |

**Ni plus, ni moins que ce qu'on voulait.** Témoin inverse : ✅

### ⚠ Et une erreur de pose, attrapée par le diff

Mon premier patch du run a modifié **le commentaire** au lieu de **la ligne de commande** *(la
chaîne cherchée apparaissait deux fois)*. **Vu immédiatement en faisant imprimer le diff**,
annulé, refait sur l'ancre exacte. *(Leçon 7 du projet : un remplacement ne se relit qu'en le
faisant imprimer.)*

### ⬜ CE QUI RESTE À CONTRÔLER — demain matin

1. **Le run de 05:00** doit repousser les **36** recherches → Supabase passe à **~11 489**.
2. **Le ménage de 05:00** *(`app_sweep_search_orphans`)* doit alors **rattacher** les 4 022.
3. **Les 3 alertes** doivent tomber : `orphelins_recherche`, `recherche_disparue`,
   `recherche_orphelin_bloque`.

⚠ **L'ordre compte** : le ménage tourne à 05:00 **et le push aussi**. S'il passe **avant** le
push, le rattrapage n'aura lieu que **le surlendemain**. **À vérifier dans le journal du run.**

⛔ **Rien n'est poussé. Rien n'a été lancé à la main.**

---

## 7. ⭐⭐ LE PROJET AVAIT DÉJÀ TRANCHÉ — *le 21 août, mot pour mot*

*Question de Frédéric : « mais le périmètre de Supabase c'est uniquement les recherches actives,
non ? »* — **Non, et la mesure le dit :**

| Supabase contient | |
|---|---|
| recherches **inactives** | **7 203** *(63 %)* |
| recherches **actives** | **4 250** *(toutes celles qui existent en local, à l'unité près)* |
| **total** | **11 453** |

Le périmètre n'est donc pas « les actives » : c'est **toutes les recherches, actives et
inactives, des contacts ÉLIGIBLES**.

### Et ce n'était pas un hasard — c'est écrit dans le run

> **`-IncludeArchivedContactSearches` (21/08/2026)** : *« on cesse de supprimer de Supabase une
> recherche que Hektor vient d'archiver. **Sa ligne disparaissait, et tout ce qui pointait sur sa
> clé — propositions, relances, retours acquéreur, rapprochements — devenait orphelin.** Désormais
> elle reste, marquée inactive. Le moteur de rapprochement ne la calcule plus *(verrou posé le
> même jour)* et **le front ne la liste plus**. »*

⭐⭐ **Même problème, même analyse, même remède — posés il y a deux mois.**

➡ **Mon correctif n'invente rien : il achève une décision déjà prise.** Le 21/08, le projet a
fermé **la première porte** *(la recherche est archivée)*. Il restait **la seconde**, par laquelle
les 36 sont sorties : **le contact perd son éligibilité**.

### Et ça répond d'avance à deux inquiétudes

| | ce que dit le commentaire du 21/08 | |
|---|---|---|
| le moteur de rapprochement va-t-il recalculer ces 36 ? | *« ne la calcule plus, verrou posé le même jour »* | ✅ **non** |
| vont-elles réapparaître à l'écran ? | *« le front ne la liste plus »* | ✅ **non** — et je l'avais vérifié séparément : `app_contact_searches_current` filtre sur `is_active` |

*(Leçon 15 du projet : **chercher si le projet a déjà tranché, avant de proposer une forme**.
Ici il avait tranché, et il avait raison.)*

---

## 8. ⚠⚠ L'ORDRE DES DEUX ÉTAPES EST UNE COURSE — et elle est perdue de 48 secondes

**L'inconnue signalée en section 6 est levée, et la réponse n'est pas bonne.**

| | quand, en heure locale |
|---|---|
| **le ménage** `app-sweep-search-orphans` *(cron Supabase, `0 5 * * *` en UTC)* | **07:00:00** |
| **le push des contacts** *(étape du run)* | **07:00:48** le 14/10 · **07:04:00** le 13/10 |

➡ **Le ménage passe AVANT le push, de 48 secondes.**

### Trois conséquences

1. **Le rattrapage des 4 022 n'aura pas lieu demain matin.** Les 36 remonteront à 07:00:48, mais
   le ménage sera déjà passé. **Ce sera le 16/10.**
2. ⚠ **C'est une COURSE, pas un ordre.** 48 s un jour, 4 min l'autre — **l'ordre peut s'inverser
   n'importe quand**. Ça explique peut-être pourquoi le ménage rattrape **370 lignes** certains
   jours et **0** les 11, 12 et 13/10.
3. **Le ménage dépend du run sans que rien ne le dise** : l'un est un cron Supabase, l'autre une
   étape PowerShell. **Personne ne garantit leur enchaînement.**

### ❓ Trois sorties — à trancher

| | | |
|---|---|---|
| **A** | **décaler le cron** à `0 6 * * *` *(08:00 locale)* | 1 ligne SQL · ⚠ **écriture en base de production** |
| **B** ⭐ | **appeler le ménage DEPUIS le run**, juste après le push | l'ordre devient **certain** au lieu d'aléatoire · ~30 min |
| **C** | ne rien faire | le rattrapage a lieu le **16/10**, et la course reste |

**Je recommande B** : c'est la seule qui supprime la course. **Rien n'est décidé.**
