# Audit — les recherches acquéreur, état réel au 31/08/2026

**Lecture seule.** Demandé par Frédéric avant de toucher au chemin de résolution de l'idCritere :
*« les recherches ne fonctionnent pas comme le reste, il ne faut pas casser ce qui marchait
avant, donc il faut comprendre. »*

Trois études existaient déjà (20 et 21/08). Elles restent justes et ne sont pas répétées ici.
Ce document mesure **où on en est dix jours après**, et ce que l'essai d'aujourd'hui a révélé.

> Voir `ETUDE_ORIGINE_CLE_RECHERCHE_2026-08-21.md` (pourquoi la clé est un haché),
> `ETUDE_HISTORIQUE_RECHERCHES_ACQUEREUR_2026-08-21.md` (la décision d'autonomie du 19/06),
> `ANALYSE_RENOMMAGE_ET_CLE_RECHERCHE_2026-08-20.md` (flux par flux).

---

## 1. Pourquoi la recherche n'est pas comme le reste — en une phrase

**L'annonce et le contact ont un numéro chez Hektor. La recherche n'en a pas.**

```
   annonce    hektor_annonce_id     donné par l'API, stable
   contact    hektor_contact_id     donné par l'API, stable
   recherche  — rien —              l'API rend un TABLEAU ANONYME
```

Tout le reste en découle. Ce n'est pas un défaut de conception : c'est la matière que Hektor
accepte de donner. Chaque particularité des recherches est une réponse à ce manque.

Un identifiant existe pourtant chez Hektor — **l'idCritere** — mais il n'apparaît que dans le
HTML de la console, jamais dans l'API. Il n'a jamais été stocké nulle part dans l'app.

---

## 2. Ce qui a été décidé, et ce qui est réellement en place

| Décision | Quand | État réel au 31/08, **vérifié** |
|---|---|---|
| Les critères appartiennent à l'app, Hektor est prévenu ensuite | 19/06 | ✅ en place (`editSearchOptimistic`, push débouncé, `app_search_pending`) |
| Le run de nuit ne réécrit pas une recherche affinée | 19/06 | ✅ en place |
| Une recherche archivée n'est plus supprimée | 21/08 | ✅ 72 874 archivées conservées |
| Un numéro propre par recherche (`app_search_id`) | 21/08 | ✅ **10 911 / 10 911**, aucune sans numéro |
| **Figer le nom au lieu de le recalculer** | 21/08 | ✅ **ACTIF**, pas seulement observé |

### Le point à corriger dans nos propres notes

`assign_search_ids()` porte encore le commentaire *« EN DOUBLURE (21/08) : ce numéro n'est
encore la clé de rien. On l'observe. »*

**Le code, lui, ne se contente plus d'observer.** Il fait :

```python
row["contact_search_key"] = nom_fige      # build_contacts_layer.py
```

Le nom n'est plus recalculé à partir du contenu : il est **rendu** depuis le registre.
La facette A — l'orphelinage par clé instable — n'est donc plus « en cours d'observation »,
elle est **corrigée**. Le commentaire est en retard sur le code, et c'est précisément le genre
d'écart qui fait prendre une mauvaise décision plus tard.

---

## 3. L'état de santé, mesuré aujourd'hui

```
   recherches dans l'app                10 911     dont 4 051 actives
   recherches en local                  76 924     dont 72 874 archivées
   toutes portent un numéro             10 911 / 10 911
```

*L'écart 76 924 / 10 911 est voulu : c'est le même filtre `supabase_sync_eligible` que pour les
contacts (355 770 en local, 58 732 dans l'app). Il porte sur le CONTACT, pas sur la recherche —
un contact poussé emmène toutes ses recherches, donc les rangs restent cohérents.*

**Les cinq sentinelles sont à zéro :**

```
   recherches disparues                      0
   numéro en double                          0
   recherche sans numéro                     0
   orphelins non rattachables                0
   rapprochements sur recherche archivée     0
```

**Et rien n'est bloqué :** `app_search_pending` = 0 ligne, 0 conflit.

> **Le système des recherches est sain aujourd'hui.** Ce n'est pas une panne qu'on répare,
> c'est une fragilité qu'on veut lever sans rien casser.

---

## 4. Ce qui a réellement circulé — et qui remet le risque à son échelle

```
   add_hektor_contact_search        3 réussis    depuis le 12/06
   update_hektor_contact_search    24 réussis    dernier le 21/08
   delete_hektor_contact_search     2 réussis    tous deux en juin
```

**29 travaux en deux mois et demi.** Ces chemins ne servent presque jamais — et c'est
**normal, c'est la décision du 19/06** : l'édition d'une recherche passe par
`editSearchOptimistic`, qui ne crée aucun travail.

Cela change l'échelle du risque signalé aujourd'hui (§5) : il porte sur **26 gestes en
2,5 mois**, pas sur un flux quotidien.

### Un angle mort de mesure, à signaler

`app_search_pending` est effacée au succès et `app_search_pending_audit` est **vide**.
**On ne sait donc pas combien d'affinages ont eu lieu depuis juin.** Le mécanisme central de
l'autonomie des recherches ne laisse aucune trace comptable. Ce n'est pas grave aujourd'hui —
mais on ne peut pas mesurer ce qu'on ne compte pas.

---

## 5. Le risque signalé aujourd'hui, énoncé sans le grossir

**Mesure**, contact 605030, une recherche créée, aucune avant :
`fetchHektorContactSearchList` rend **3 identifiants**.

La regex ratisse cinq motifs. Les quatre premiers porteraient le **même** idCritere pour une
recherche donnée — ils seraient donc dédupliqués. Les 3 valeurs étant différentes, il y a du
bruit, et `rel="…"` est le motif le plus large.

**Pourquoi ça compte :**

```
   handleUpdateHektorContactSearch  ->  resolveContactSearchTargetCritereId
   handleDeleteHektorContactSearch  ->  resolveContactSearchTargetCritereId
                                        « prends l'entrée d'index N de cette liste »
```

Si la liste contient du bruit, l'index ne désigne pas la recherche voulue.

**Ce qu'on ne sait pas, et qu'il ne faut pas supposer :** peut-être que la première entrée est
toujours la bonne et que le bruit vient après — auquel cas index 0 tape juste, les 26 gestes
passés étaient corrects, et le défaut ne se voit qu'à partir de la deuxième recherche.

### ÉTABLI LE 31/08 — et **mon diagnostic du matin était faux**

Trois contacts lus directement, en lecture seule, depuis la session Hektor :

| contact | recherches dans l'app | `data-search-id` trouvés | regex actuelle du worker |
|---|---|---|---|
| **78000** | 8 | **8** ✅ | **1** ❌ |
| **151844** | 3 | **3** ✅ | **1** ❌ |
| **605030** | 1 | **1** ✅ | **1** ✅ |

**La liste ne sur-compte pas : elle SOUS-COMPTE.** Elle ne rend jamais que le **premier**
identifiant, quel que soit le nombre de recherches. J'avais conclu l'inverse le matin, à partir
d'un `criteres_apres: 3` observé côté worker — une mesure juste, une inférence fausse.

**Le HTML porte pourtant l'identifiant, proprement** : un attribut `data-search-id`, **une
balise par recherche**, dans l'ordre. Pour le contact 78000 :

```
   13589  13590  13591  13592  13595  13596  13597  13598
                              ^^ le saut montre que l'idCritere est attribue
                                 globalement chez Hektor, pas par contact
```

La regex actuelle ne le regarde pas. Elle ratisse `dropDownMenu_`, `contentDrop_`,
`valueInputAutoarchivage`, `rel=` — **qui ne portent que le premier** — et `getWizardCritere`,
**absent du HTML** (0 occurrence sur les trois contacts).

### La conséquence exacte, et elle est sérieuse

```js
list.find(entry => entry.index === index) || list[0]     // resolveContactSearchTargetCritereId
```

Si la liste ne contient qu'une entrée (index 0) :

```
   search_index = 0   ->  trouve l'entree 0        ->  CORRECT
   search_index = 1+  ->  ne trouve rien           ->  RETOMBE SUR list[0]
                                                       = LA PREMIERE RECHERCHE
```

**Modifier ou supprimer la 2ᵉ recherche d'un contact agit sur la 1ʳᵉ. Sans erreur, sans trace.**

### Mais le défaut n'a JAMAIS mordu — vérifié un par un

Les **26 gestes** `update` / `delete` depuis le 12/06 portent **tous** `search_index = 0`.
Un seul concernait un contact à 2 recherches (113412), et sa suppression portait en plus un
`idCritere` explicite (17985) — donc sans passer par la résolution par index.

> **Le risque est réel et DORMANT.** Il ne s'est jamais réalisé parce que personne n'a encore
> touché à une deuxième recherche. Il mordra au premier geste qui le fera.

### Ce qui reste non expliqué, et qu'il ne faut pas balayer

Côté worker, le contact 605030 avait donné **3** identifiants ; depuis ma session je n'en compte
**1**. La différence : le worker agit en **contexte négociateur**, moi en **admin root** — et on
sait déjà (documents, août) que Hektor masque des blocs selon le compte. **Je n'ai donc pas
vérifié que `data-search-id` est présent en contexte négociateur.**

**Conséquence sur la façon de corriger** : lire `data-search-id` **en premier**, garder
l'ancienne regex en repli, et **journaliser les deux** — puis observer en conditions réelles
avant de s'y fier. C'est la méthode de la doublure, celle du registre des recherches.
Pas de bascule sur une lecture faite depuis le mauvais compte.

⚠️ **Ne pas supprimer la recherche d'essai du contact 605030** tant que ce point n'est pas
établi : la suppression emprunte ce même chemin.

### Le périmètre exposé a quintuplé depuis l'estimation du 20/08

```
   20/08     184 contacts à 2+ recherches   (sur 3 961 recherches)
   31/08     933 contacts à 2+ recherches   (sur 10 911)
```

Ce n'est pas une dégradation : c'est la conséquence directe d'avoir **conservé les archivées**
(décision 4bis du 21/08). Le rang d'une recherche se compte désormais parmi toutes celles du
contact, actives et archivées. Le raisonnement du 20/08 — *« 95 % du parc est hors risque »* —
reste vrai en proportion (**90 %** aujourd'hui), mais le nombre absolu de contacts concernés a
été multiplié par cinq. **C'est ce chiffre-là qu'il faut retenir, pas celui de la note d'août.**

---

## 6. Deux découvertes de cet audit

### 6.1 Supprimer un contact laisse ses rapprochements orphelins

**Mesuré :** 138 lignes de `app_rapprochement` (et autant dans l'historique de score) pointent
sur des recherches qui n'existent plus — **3 recherches distinctes, nées entre 11:55 et 12:22
aujourd'hui**, appartenant aux contacts d'essai **605093, 605094, 605095** que j'ai créés puis
supprimés ce matin. Aucun des trois contacts n'existe encore.

`delete_hektor_contact` purge bien `app_contact_search_current` (son résultat le dit :
`app_contact_search_current: 1`) mais **ne touche ni `app_rapprochement` ni
`app_rapprochement_score_history`**.

**Ce n'est pas un défaut des recherches** : c'est un trou dans le chemin de suppression d'un
contact. Il ne s'était jamais manifesté parce que personne n'avait encore supprimé un contact
**qui portait une recherche** — le seul contact supprimé auparavant (604135, en juin) n'en avait
pas.

Proportion : 138 sur 49 055 rapprochements, soit **0,28 %**, et ce sont mes propres déchets
d'essai.

**NETTOYÉ le 31/08** — 279 lignes sur trois tables (`app_rapprochement` 138,
`app_rapprochement_score_history` 138, `app_rapprochement_search_state` 3). Les huit autres
tables portant `contact_search_key` ne contenaient rien pour ces clés, et les trois contacts
étaient bien absents de `app_contact_current` (témoin vérifié avant suppression).
Contrôle après : **0 rapprochement orphelin**.

**Reste à corriger dans le handler** : `delete_hektor_contact` doit purger les rapprochements
et leur historique, comme il purge déjà la recherche.

### 6.2 La modale n'écrit toujours que 7 critères sur 12

Constat de l'étude du 21/08, **toujours vrai** : `offerCode`, `priceMin`, `priceMax`,
`surfaceMin`, `roomsMin`, `bedroomsMin`, `landSurfaceMin` (+ types et villes).

Manquent : `ITEM_SURFACE_MAX`, `ITEM_PIECES_MAX`, `ITEM_CHAMBRE_MAX`,
`ITEM_SURFACE_TERRAIN_MAX`, `ITEM_PRIX_MARGE`, `ITEM_QUARTIER_PONDERATION`.

C'est ce qui a fait échouer la 25ᵉ modification le 21/08 — le garde-fou anti-écrasement a
protégé Hektor contre une recherche que l'app ne savait pas porter entièrement. **Le garde-fou
a bien fonctionné.** La cause, elle, n'est pas corrigée.

*(À noter : la mémoire du projet dit « les critères max ne sont pas stockés » côté app —
c'est le même trou, vu de l'autre bout.)*

---

## 7. Ce que ça implique pour la suite

**Ce qui marche et ne doit pas bouger :**

```
   la clé figée par le registre        (facette A corrigée, sentinelles à zéro)
   l'affinage optimiste                (décision du 19/06, en place)
   le garde-fou anti-écrasement        (il a fait son travail le 21/08)
   les archivées conservées            (4bis)
```

**L'ordre que je recommande, du moins risqué au plus engageant :**

1. ~~Établir le comportement de la liste scrapée~~ **FAIT le 31/08** (§5). Le défaut existe,
   il est dormant, et le bon attribut est identifié : `data-search-id`.
   **Suite** : lire `data-search-id` d'abord, garder l'ancienne regex en repli, journaliser les
   deux, observer — puis basculer. Ne PAS basculer sur une seule lecture faite en admin.
2. **Corriger la purge des rapprochements** à la suppression d'un contact — trou net, isolé,
   sans effet sur les recherches.
3. **Trancher la question restée ouverte depuis le 19/06** : *les recherches remontent-elles
   encore chez Hektor, oui ou non ?* Tant qu'elle n'est pas tranchée, le système reste dans
   l'état intermédiaire décrit le 21/08 — l'app garde sa valeur, Hektor garde la sienne, et
   rien ne le signale au négociateur.

**Ce que je ne recommande pas** : capturer l'idCritere « proprement » avant d'avoir établi le
point 1. On ajouterait de la logique par-dessus un scrape dont on ne connaît pas le
comportement.
