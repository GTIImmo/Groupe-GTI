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

---

## 9. LA COURSE EST SUPPRIMÉE — *« Oui fais le », 14/10*

**On n'attend plus un cron : le run appelle le ménage lui-même, juste après le push.**

| | |
|---|---|
| `phase2/sync/menage_orphelins_recherche.py` | **neuf** — appelle `rpc/app_sweep_search_orphans`, patron recopié de `repartition_commission.py` |
| `run_full_pipeline.ps1` | une étape **non bloquante**, **juste après** « push contacts », avec 2 essais |
| `supabase/patch_registre_menage_orphelins_2026-10-14.sql` *(+ son INVERSE)* | **à coller** — la ligne de registre |

**Syntaxe PowerShell validée. Les 3 noms importés existent.**

### ⚠ LE CRON N'EST PAS ÉTEINT, ET C'EST VOULU

Il reste **le filet** si le run échoue avant cette étape. La fonction est **idempotente** : la
rejouer ne coûte qu'un passage à vide. *(Et éteindre un cron serait une écriture en production.)*

### ⚠ CE QUE LA MÉMOIRE DU PROJET M'A FAIT VÉRIFIER — et elle avait raison

La clé `phase2.menage_orphelins_recherche` **n'existe pas** dans `app_worker_registry`
*(mesuré)*. Sans elle, **le battement serait parti dans le vide ET aurait compté pour un
succès** — `heartbeat.py` écrit en `PATCH` filtré, une clé sans ligne touche **0 ligne**, reçoit
**204**, et `200 <= status < 300` compte un succès.

➡ **C'est le défaut 4j, trouvé et réparé le 13/10 pour 23 autres étapes.** Je l'aurais refabriqué
le lendemain. **D'où le patch SQL**, recopié sur `phase2.repose_cloture_mandat`, posée la veille
pour exactement le même usage.

### ⛔ Ce que je n'ai PAS fait

**Je n'ai pas lancé le script.** Il appelle une fonction qui **écrit en production** *(elle
rattache des lignes)* : le go portait sur la suppression de la course, pas sur un ménage lancé à
la main. **La première exécution sera celle du run, demain à ~07:01.**

J'ai seulement vérifié, en lecture, que la fonction **sera appelable** :
`proacl = postgres=X | service_role=X` → le run, qui utilise la clé de service, peut l'exécuter,
et elle reste fermée à tout le reste.

### Le calendrier, maintenant

| | |
|---|---|
| **demain ~07:01** | le push remonte les **36**, **puis** le ménage rattache les **4 022** |
| **demain ~07:48 et 09:48** | les **3 alertes** doivent tomber |

➡ **Le rattrapage a lieu demain, et non plus le 16/10** — à condition que le patch de registre
soit collé *(sinon l'étape tourne quand même, mais sa surveillance ment)*.

---

# 15/10/2026 — LE CONTRÔLE

## 10. LE CONTRÔLE DU 15/10 — *le remède marche, mon étape a planté, et elle était inutile*

### ✅ CE QUI A MARCHÉ

| | hier | ce matin |
|---|---|---|
| recherches **chez nous** | 11 453 | **11 498** *(+45)* |
| recherches **chez Hektor seul** | 65 729 | **65 693** *(−36)* |
| nos **5 contacts témoins** | 0 recherche | **6** |
| 🟠 lignes accrochées à une recherche disparue | **4 022** | **0** |
| 🟠 recherches disparues | **35** | **0** |
| 🟠 orphelins non rattachables | **37** | **0** |
| **le moniteur, à 07:48** | 8 avertissements | **4** |

➡ **Les trois alertes sont tombées**, et les deux sondes de notifications corrigées la veille sont
restées vertes. **L'ordre push → ménage est bon** : push 07:02:40 → 07:03:20, ménage 07:03:20.
**La course est supprimée.**

### ❌ MON ÉTAPE A PLANTÉ — deux fois

```
TypeError: SupabaseRestClient.__init__() takes 1 positional argument but 3 were given
```

**Ma faute** : j'ai recopié l'**import** de `repartition_commission.py` sans lire **comment il
instancie**. Les arguments sont **nommés obligatoirement**
*(`def __init__(self, *, base_url, service_role_key, …)`)*.

⚠ **Et cet échec a créé une alerte** : `logs.pipeline.latest` passe en avertissement parce que
mon `Traceback` est dans la queue du journal du run. **Une alerte de plus, causée par moi.**

**Corrigé le 15/10**, et surtout : **le script offre maintenant `--essai-a-vide`**, qui joue tout
*(lecture de l'environnement, construction du client)* **sauf l'appel**.

> ⭐ **LA LEÇON** : le 14/10 j'ai eu **raison** de ne pas lancer un script qui écrit en
> production — mais j'aurais pu éprouver **tout ce qui précède l'écriture**. **Un script qui
> écrit doit offrir un moyen de s'éprouver sans écrire.**

### ⭐⭐ ET LA LEÇON LA PLUS IMPORTANTE : L'ÉTAPE DE MÉNAGE ÉTAIT INUTILE ICI

**Les 4 022 orphelins ont disparu alors que le ménage n'a pas tourné.**

Parce qu'un orphelin n'est pas « une ligne à rattacher ailleurs » : c'est **une ligne dont la
recherche manque**. **Rendre la recherche suffit** — la vue ne les compte plus, point.

➡ **Le correctif B seul suffisait.** L'étape ajoutée le 14/10 *(et le patch de registre que
Frédéric a collé deux fois)* **n'a rien apporté à ce problème-là**.

**Elle garde un intérêt pour l'AUTRE porte** — celle où la recherche **ne revient pas** parce que
sa clé a changé *(le hash du contenu)*. Mais **je l'ai présentée comme nécessaire au rattrapage,
et elle ne l'était pas.** ⚠ **J'aurais dû mesurer ce que B seul produisait avant d'ajouter une
étape au run.**

### ⬜ CE QUI RESTE

1. **Demain matin** : vérifier que l'étape corrigée tourne *(elle aura son premier succès)* et que
   `logs.pipeline.latest` redevient vert.
2. ⚠ **3ᵉ travail en erreur, sans rapport avec ce chantier** : annonce **47824**,
   `sync_console_documents`, 14/10 à 19:00 — *« Unexpected token '<' »*, Hektor a renvoyé une page
   HTML au lieu de JSON. **1 seule tentative.** Non diagnostiqué.
