# CHANTIER — CORRIGER LA RÈGLE DE CHAÎNAGE

**20/10/2026.** Décidé par Frédéric.

> ⭐ **LA RÈGLE DU § 3 EST FIGÉE** : elle a été posée point par point, et Frédéric a
> tranché les trois questions ouvertes le 20/10 — **① oui · ② annulés seuls · ③ NON**.
> C'est elle, et pas une autre, qui doit être codée.

**Audit : `notice/AUDIT_REGLE_CHAINAGE_2026-10-20.md`.**
**Tout ce qui suit est encore en LECTURE SEULE : rien n'est codé, rien n'est écrit.**

---

## 0-bis. FAIT ET EN PRODUCTION — le 20/10/2026 au soir

**La règle V2 est allumée, poussée et vérifiée.** Le chantier est clos.

| | mesure finale, lue chez Supabase |
|---|---|
| registre | **31 084 lignes · 12 290 chaînes** *(12 715 avant)* |
| répartition | 16 071 lignes · **2 orphelines**, toutes d'origine `saisie` |
| les 4 contrôles de `verifier_regle_chainage.py` | **verts, sortie 0** |
| `écarts base ↔ règle` | **0** — la base EST le résultat de la V2 |
| ARNAUD Jean-Luc *(offre 28132 + vente 28133)* | **UNE chaîne** |
| l'échec du bien 171 *(offre refusée + compromis annulé)* | **UNE chaîne** |

⭐ **Les 2 orphelines restantes sont celles d'AVANT** — l'affaire 1001347, disparue du
registre, qui porte une des deux seules répartitions saisies à la main. **La V2 n'en a
laissé aucune derrière elle.**

### Ce qui a été lancé, et dans quel ordre

```
1. phase2/sync/affaire_ledger.py --refresh     (local : 12 276 chaines)
2. phase2/sync/affaire_ledger.py --push        (31 084 lignes, 0 ecartee)
3. APP_CHAINAGE_V2=1 pose dans .env            (chemin PROUVE : rend True)
4. repartition_commission.py --purger-orphelines --pousser
      purge   : derivees_supprimees 27 · saisies_orphelines_gardees 2
      pousse  : lignes_ecrites 27 · dossiers_ecrits 14 · refuses 0
5. git push                                    (fusion du front « bienvu » comprise)
```

⚠ **Les gestes 4 et 5 ont été lancés par Frédéric** : le garde-fou de l'outil m'a refusé
l'écriture partagée et la publication. C'est la règle du projet, pas un incident.

⭐ **Et la répartition s'est réparée par le chemin du projet, sans aucun patch.**
`app_repartition_purger_orphelines` ne supprime que `origine LIKE 'hektor%'` *(dérivé,
donc refabricable)* et **garde les saisies humaines en les comptant**. La garde du 15/09
a fait le travail : j'allais écrire 14 `UPDATE` pour rien.

### Ce qui reste, nommé

```
- les 213 transactions SANS DATE (dont les compromis a 0000-00-00) : la 3e faille,
  ENTIERE. Ni mesure ni correctif dans ce chantier.
- 42 ventes seules · 6 ventes ambigues · 4 abstentions de compromis : elles
  restent SEULES ET DITES AU JOURNAL. C'est voulu : on ne devine pas.
- le § 3.4 (vente -> offre refusee) et le § 2.3 pour un compromis VIVANT :
  ECARTES PAR FREDERIC, ce n'est pas un oubli.
- le retour arriere reste GRATUIT : APP_CHAINAGE_V2=0 dans .env, et le run de la
  nuit suivante repose les anciens numeros. Aucune donnee a reparer.
```

### Ce que ça débloque

- l'appariement avec le classeur se refait **sur une base saine** : les 37 « ventes
  manquantes » devraient tomber à ~3 *(à remesurer)* ;
- le registre des transactions cesse de montrer deux affaires là où il n'y en a qu'une.

---

## 1. L'OBJECTIF, EN UNE PHRASE

Une affaire réelle doit faire **une seule chaîne** — que son déroulé soit
`offre → vente` sans compromis, ou `offre refusée → compromis annulé`.

---

## 2. L'ARRIVÉE, CHIFFRÉE

*Simulation validée : elle rejoue la règle actuelle à **31 065 / 31 066 = 100,00 %**.*

| | aujourd'hui | après |
|---|---|---|
| chaînes | **12 702** | **12 278** *(−424)* |
| ventes qui partent seules | **132** | **42** |
| ventes ambiguës *(plusieurs compromis)* | 8 | 6 |
| échecs coupés en deux | **333** | **0** *(4 abstentions déclarées)* |
| transactions qui changent de chaîne | — | **426** |
| biens concernés | — | **420**, dont **5 vivants** |
| invariants de cohérence | ✅ tiennent | ✅ **tiennent** |

⭐ **Seulement 5 biens vivants** : l'essentiel porte sur l'historique *(vendus, clos,
archivés)*. L'impact visible à l'écran est minuscule.

---

## 3. ⭐⭐⭐ LA RÈGLE — **version figée, à coder telle quelle**

### § 0 — Le cadre *(inchangé)*

| | |
|---|---|
| **0.1** | On travaille **bien par bien**. |
| **0.2** | On écarte les transactions **effacées chez Hektor** *(numéro Hektor présent ET `present_in_hektor` faux)*. Celles **nées dans l'app**, sans numéro Hektor, restent. |
| **0.3** | On prend les transactions **dans l'ordre des dates**. À date égale : offre, puis compromis, puis vente. |
| **0.4** | La date d'une **offre** est celle de sa **première proposition**. Les autres gardent leur date. |
| **0.5** | Une transaction **sans date utilisable** *(vide ou `0000-00-00`)* est **seule dans sa chaîne**. *(213 cas — hors chantier.)* |
| **0.6** | « **nom commun** » = au moins **un mot de 3 lettres ou plus** identique dans le nom ou le prénom de l'acquéreur. |

### § 1 — UNE OFFRE *(inchangé)*

| | |
|---|---|
| **1.1** | Elle cherche une chaîne **ouverte**, **sans compromis**, avec un **nom commun**. |
| **1.2** | Trouvée → elle la rejoint. |
| **1.3** | Sinon → elle **ouvre sa propre chaîne**. |
| **1.4** | Si **toutes** les offres de la chaîne sont alors refusées → la chaîne se **ferme**. |

### § 2 — UN COMPROMIS

| | |
|---|---|
| **2.1** | Il cherche **l'unique** chaîne ouverte avec une **offre acceptée** et **sans compromis**. Exactement une → il la rejoint. *(inchangé)* |
| **2.2** | 🆕 **Plusieurs** → le **nom commun** départage. Une seule au nom commun → il la rejoint. *(+2)* |
| **2.3** | 🆕 **LE POINT 4 — ⚠ SEULEMENT SI CE COMPROMIS EST ANNULÉ** *(décision ② du 20/10)*. Aucune chaîne trouvée → avant d'ouvrir la sienne, il cherche parmi les chaînes **déjà fermées de ce bien** une chaîne qui : **n'a pas de compromis**, **dont toutes les offres sont refusées**, et qui a un **nom commun** avec lui. |
| **2.3.a** | Une seule → il la rejoint, et cette chaîne **redevient la chaîne courante**. *(+333)* |
| **2.3.b** | Plusieurs → **abstention** : il ouvre la sienne, **et c'est écrit dans le journal**. *(4 cas)* |
| **2.4** | Sinon → il ouvre sa propre chaîne. *(inchangé)* |
| **2.5** | S'il est **annulé** → la chaîne se **ferme**. *(inchangé)* |

⛔ **Un compromis VIVANT n'est PAS concerné par le § 2.3** — décision de Frédéric. Les
**21 cas** mesurés gardent le comportement actuel : ils ouvrent leur propre chaîne.

### § 3 — UNE VENTE

| | |
|---|---|
| **3.0** | 🆕 **GARDE GÉNÉRALE** : une chaîne qui **porte déjà une vente** est exclue de **tous** les cas ci-dessous. ⚠ *Sans elle, la simulation produisait une chaîne à deux ventes.* |
| **3.1** | Elle cherche **l'unique** chaîne ouverte portant un **compromis**. Exactement une → elle la rejoint. *(inchangé)* |
| **3.2** | 🆕 **Plusieurs** → le **nom commun** départage. *(+2)* |
| **3.3** | 🆕 Rien → une chaîne ouverte portant une **offre acceptée** sans compromis : |
| **3.3.a** | une seule au **nom commun** → elle la rejoint *(+36)* |
| **3.3.b** | sinon **l'unique** chaîne à offre acceptée, **même sans nom commun** → elle la rejoint *(+54)* — **décision ① du 20/10 : OUI** |
| **3.4** | ⛔ **ÉCARTÉ — décision ③ du 20/10 : NON.** *(On ne rattache PAS une vente à une offre refusée, même au même nom. Les 5 cas mesurés restent seuls.)* |
| **3.5** | Sinon → elle **part seule**, **et c'est écrit dans le journal**. *(42 cas)* |
| **3.6** | Une vente **ferme toujours** la chaîne qu'elle rejoint — **y compris celle qu'elle ouvre elle-même**. *(inchangé — correctif du 08/09)* |

### § 4 — LA FERMETURE *(inchangé, sauf une exception)*

Une chaîne se ferme quand : **une vente** la rejoint · **toutes** ses offres sont refusées
*(et pas de compromis)* · **son compromis est annulé**.

⚠ **Seule exception, nouvelle** : le **§ 2.3** — une chaîne fermée par refus peut être
**rouverte** par un compromis **annulé** du même nom. *(Elle se refermera aussitôt par le
§ 2.5, puisque ce compromis est annulé.)*

### § 5 — LE NUMÉRO *(inchangé)*

Le numéro d'une chaîne est le **plus petit `app_affaire_id`** de ses membres, attribué
**à la fin**, quand la chaîne est complète.

### § 6 — CE QU'ON REFUSE DE FAIRE

On **n'invente jamais**. Dans le doute, la transaction part **seule** et c'est **écrit
dans le journal du run** :

```
42  ventes seules            6  ventes ambigues (plusieurs compromis)
 4  abstentions de compromis  213  sans date (hors chantier)
```

---

## 4. OÙ VIT LA RÈGLE — **quatre endroits, trois rôles différents**

| | rôle | à modifier ? |
|---|---|---|
| `phase2/sync/affaire_ledger.py:1068` `recalculer_les_chaines` | ⭐ **il ASSIGNE** — il décide, chaque nuit | ✅ **oui** |
| Supabase `app_chaine_pour` *(`patch_chaine_regle_sequence_2026-09-05.sql`)* | **il ASSIGNE aussi**, pour une affaire **née dans l'app**, avant le run | ✅ **oui** — sinon elle change de chaîne ~24 h plus tard |
| `apps/hektor-v1/src/App.tsx:27478-27496` | il ne fait que **JUGER l'ouverture** à partir du `app_chaine_id` reçu | ⛔ **NON — vérifié** |
| `phase2/checks/verifier_regle_chainage.py:126` `fermee_selon_le_run` | il porte **sa propre copie** de la règle | ✅ **oui** — sinon il criera au loup |

### ⭐ Pourquoi le front n'a rien à changer — vérifié, pas supposé

```js
const ouvert = !vente && (!aCompromis || compromisVivant) && (aCompromis || !aOffre || offreVivante)
```

| la chaîne après fusion | ce que le front en dit |
|---|---|
| offre acceptée **+ vente** | `!vente` faux → **fermée** ✅ |
| offre refusée **+ compromis annulé** | `aCompromis` vrai, `compromisVivant` faux → **fermée** ✅ |

Le front **groupe par `app_chaine_id`** et déduit tout le reste.

---

## 5. ⭐⭐⭐ LA MÉTHODE — **audit du 20/10 : c'est beaucoup plus simple que prévu**

Frédéric : *« refais un audit pour déterminer la meilleure manière de corriger mon
registre des transactions sans rien casser, simplement »*. J'ai suivi le chemin qu'un
numéro de chaîne parcourt, de son calcul à l'écran. **Mon plan en 6 lots était trop lourd.**

### 5.1 Le chemin réel d'un numéro de chaîne

```
1. le run, en local : recalculer_les_chaines()  -> ecrit app_chaine_id      0,09 s
2. le PUSH : ledger_rows_for_push() fait SELECT * moins les exclusions
      -> app_chaine_id A QUITTE la liste des exclusions le 04/09
      -> IL EST DONC POUSSE, et l'upsert le met a jour sur les lignes existantes
3. apres le push : rpc/app_attribuer_chaines_affaire COMBLE LES TROUS seulement
      -> mesure Supabase : 0 ligne sans chaine. Il n'a rien a faire.
4. le front : il GROUPE par app_chaine_id et deduit tout le reste.
```

⭐⭐ **CONCLUSION : le local est le maître, et une seule fonction décide.**
Le commentaire du code le dit mot pour mot *(l. 1451-1453)* :
> *« app_chaine_id a quitté cette liste le 04/09. Depuis la refonte de la règle
> (`recalculer_les_chaines`), c'est **LE LOCAL** qui les calcule, à chaque run, pour
> toutes les lignes. **Il doit donc les pousser.** »

➡ **Modifier cette seule fonction suffit. La correction monte d'elle-même au premier
run.** Aucune migration, aucun patch SQL, aucune ligne de front, aucun redémarrage.

### 5.2 Ce que j'ai vérifié côté Supabase *(lecture seule)*

| | |
|---|---|
| déclencheurs sur `app_affaire_ledger` | **0** |
| `app_chaine_id` est-elle une colonne calculée ? | **non** |
| lignes sans chaîne *(ce que la RPC comblerait)* | **0** |
| politiques RLS | 1 *(et `service_role` porte `rolbypassrls`)* |

➡ **Rien ne s'oppose à ce que le push écrive la nouvelle valeur.**

### 5.3 ⭐ LE RETOUR ARRIÈRE EST GRATUIT — et c'est ce qui rend tout simple

Une chaîne est une **déduction**, refaite **entièrement** chaque nuit en 0,09 s. Donc :

```
interrupteur sur 1  -> le run de la nuit pose les nouveaux numeros
interrupteur sur 0  -> le run de la nuit suivante REPOSE les anciens
```

**Il n'y a RIEN à migrer, donc RIEN à défaire à la main.** Le patron existe déjà dans
le projet *(`APP_REGISTRE_DEPUIS_APP_MANDAT`, `export_app_payload.py:842`)* :

```python
CHAINAGE_V2 = os.environ.get("APP_CHAINAGE_V2", "0") == "1"   # ETEINT par defaut
```

⚠ **Et on l'IMPRIME dans le journal du run**, comme le fait
`registre_mandats_upsert.py:80` — sinon on ne saura pas quelle règle a tourné cette nuit.

### 5.4 ✅ LA RÉPARTITION : le piège que je cherchais n'existe pas

La clé primaire de `app_affaire_repartition` est **`(app_chaine_id, cote, rang)`** :
deux chaînes qui fusionnent pourraient **télescoper** leurs lignes. **Mesuré :**

```
16 chaines de repartition disparaissent
   14  la chaine cible n'a AUCUNE repartition  -> simple deplacement
    2  cible ambigue                           -> a la main
    0  TELESCOPAGE                             <- aucun
```

⚠ **Mais on ne la touche PAS tout de suite** : déplacer ces 14 lignes rendrait le retour
arrière non gratuit. **On attend d'être sûr.**

### 5.5 ✅ SUPABASE N'EST PLUS UN PRÉREQUIS

`app_chaine_pour` n'assigne que pour une affaire **née dans l'app**, entre deux runs.
**Mesure du rythme réel :**

```
octobre 2026 :  1 affaire nee dans l'app
septembre    : 15
aout         : 315   (une reprise en masse, pas le quotidien)
```

➡ **1 à 15 par mois**, et la divergence dure **moins de 24 h** *(le run suivant
recalcule et pousse)*. Le lot Supabase passe donc **après**, et il n'est pas bloquant.

---

## 5-bis. ✅ ÉTAPES 1 ET 2 — **FAITES le 20/10, et éprouvées**

### Ce qui est écrit

| | |
|---|---|
| l'interrupteur | `CHAINAGE_V2 = os.environ.get("APP_CHAINAGE_V2", "0") == "1"` — **éteint par défaut** |
| la règle | `recalculer_les_chaines` : § 2.2, § 2.3 *(annulés seuls)*, § 3.0, § 3.2, § 3.3 — **un seul fichier** |
| le journal | le run imprime `chainage : N chaines (V2 -- replis actifs | regle d avant)` |
| l'épreuve | `phase2/checks/test_chainage_v2.py` — **elle s'exécute dans les deux sens, en deux processus** |

### Le résultat mesuré, en appelant **la vraie fonction** sur une copie jetable

```
V2 ETEINTE   12 701 chaines · 0 transaction deplacee · invariants propres
V2 ALLUMEE   12 276 chaines · 427 deplacees        · invariants propres

   334  compromis annule rattache a l offre refusee      (le point 4)
    55  vente rattachee a l unique offre acceptee        (§ 3.3.b)
    35  vente rattachee a une offre acceptee, nom commun (§ 3.3.a)
     2  le nom a departage plusieurs compromis           (§ 3.2)
    42  vente sans compromis ouvert    -> SEULE, et dite
     6  vente : plusieurs compromis    -> SEULE, et dite
     4  plusieurs chaines refusees au meme nom -> ABSTENTION, et dite
```

⭐ **Le témoin inverse est le contrôle qui compte** : interrupteur éteint, **aucune
transaction ne bouge**. Le code neuf dort sans rien changer.

### ✅ Et « le front n'a rien à changer » est maintenant MESURÉ

Les deux prédicats de fermeture *(celui du run, celui de `App.tsx:27494`)* appliqués aux
chaînes **V2** :

```
sur les 426 chaines issues d une FUSION   : 0 divergence
sur les 12 290 chaines V2                 : 0 divergence
```

### ⚠⚠ DEUX DE MES PROPRES MESURES ÉTAIENT FAUSSES, et les contrôles les ont attrapées

| mon invariant | ce qu'il accusait | la vérité |
|---|---|---|
| *« une chaîne vendue porte un compromis vivant »* | **9 123 chaînes** sous la règle **actuelle** | l'état normal : *« 7 507 compromis sont antérieurs à une vente et toujours marqués actifs chez Hektor, parce que personne ne les clôt après l'acte »* — **c'est écrit dans le code du chaînage** |
| *« un bloc daté après la vente »*, sur la colonne `date` **brute** | 2 chaînes | la colonne porte le **dernier événement** de l'offre, pas sa place. Avec `_date_de_tri` *(celle du run)* : **0** |

### ⭐⭐ ET LE CONTRÔLE DU PROJET CRIAIT AU LOUP DEPUIS LE 16/09

`phase2/checks/verifier_regle_chainage.py` rendait **deux faux rouges** pour la même
raison : il ordonnait sur la colonne brute, alors que la règle ordonne sur la première
proposition **depuis le 16/09**. Il n'avait jamais suivi.

```
chaine 999  : offre PROPOSEE 02/02, acceptee 18/05 · compromis 12/03 · vente 07/05
chaine 4226 : offre PROPOSEE 26/06, acceptee 14/10 · compromis 30/07 · vente 13/10
   -> les deux sont PARFAITEMENT ordonnees
```

✅ **Corrigé** : il lit `_date_de_tri` *(la fonction du run, pas une copie)*, il demande
`propositions_json`, et il affiche **les deux dates** pour qu'on ne s'y reprenne pas.
**Il passe de rouge à vert (sortie 0), ses quatre contrôles compris.**
⭐ Il n'est lancé par **aucune tâche** : personne n'avait vu ce rouge — mais il rendait
le contrôle **inutilisable**, ce qui est pire qu'une fausse alerte.

✅ **Et `fermee_selon_le_run()` n'a PAS eu besoin de changer** : une chaîne fusionnée
*(offre refusée + compromis annulé)* ressort **fermée** des deux côtés. Vérifié, pas supposé.

### ✅ Les épreuves voisines ne sont pas cassées

```
test_chainage_vente_ferme.py          >>> TOUT PASSE   (sortie 0)
verifier_regle_chainage.py (V2 off)   4 controles verts (sortie 0)
verifier_regle_chainage.py (V2 on)    4 controles verts, et son § 5 DIT
                                      « 427 <<< le prochain run deplacera ces dossiers »
```

⛔ **RIEN N'EST POUSSE, RIEN N'EST EN PRODUCTION.** L'interrupteur est à `0`, et le
code n'a pas été commité — j'attends son accord pour l'étape 3.

---

## 5-ter. OÙ ON EN EST, le 20/10 au soir — **quatre pièces, quatre statuts**

| la pièce | son statut |
|---|---|
| **la règle** | ✅ **acquise** — décidée, figée au § 3, codée, éprouvée dans les deux sens |
| **le code** | ✅ commité en local *(`20c811a`)*, ⚠ **non poussé** |
| **les données** | ⚠⚠ **la V2 est EN LIGNE**, mais **l'interrupteur n'est pas dans `.env`** |
| **la répartition** | ⚠ **29 lignes orphelines**, rien de perdu |

### ⭐⭐ LA PIÈCE QUI DÉCIDE : si on ne fait RIEN, tout revient cette nuit

J'ai lancé avec la variable **en ligne de commande**, pas dans `.env`. Le run de 05:00
relira donc l'interrupteur — absent — et **reposera l'ancienne règle**. Mesuré en
rejouant la V1 :

```
chaines en base ce soir (V2)        12 290
chaines que le run reposerait (V1)  12 715
transactions qui REVIENDRAIENT         427

repartition orpheline ce soir        29 lignes (15 chaines)
repartition orpheline apres le run    2 lignes ( 1 chaine)  <- le cas deja connu
```

➡ **Ne rien faire = retour arrière complet et automatique.** Les orphelines
disparaîtraient d'elles-mêmes. **C'est ce que l'interrupteur promettait, et c'est
vérifié sur les données, pas déduit.**

### ✅ ET LES ORPHELINES SONT PLUS SIMPLES QUE JE NE LE CROYAIS

Cartographiées par **les membres de la chaîne** — la bonne clé, pas le dossier, qui
porte plusieurs chaînes :

```
14 chaines -> UNE SEULE cible, sans aucune ambiguite   = 27 lignes
 1 chaine  -> 0 cible : 1001347, L ORPHELINE DEJA CONNUE =  2 lignes
   (l'affaire a disparu du registre ; elle portait une des deux seules
    repartitions saisies a la main -- elle etait deja orpheline AVANT la V2)
```

⭐ **Il n'y a donc AUCUN cas ambigu créé par la V2.** Le rattrapage est **14 UPDATE
entièrement déterminés**, et le télescopage de clé primaire ne se produit pas
*(mesuré : 0)*.

### ⚠ CE QUE LA FENÊTRE D'AUJOURD'HUI COÛTE, dit franchement

Entre maintenant et 05:00, l'app montre les chaînes fusionnées. Concrètement :
**5 biens vivants** affichent une affaire au lieu de deux *(c'est le but)*, et
**~15 affaires** n'affichent plus « qui est payé » *(les orphelines)*.

### LE CHOIX, BINAIRE

| | |
|---|---|
| **ne rien poser** | cette nuit tout revient à l'état d'avant. Le code reste dormant, aucune trace. |
| **`APP_CHAINAGE_V2=1` dans `.env`** | la V2 reste, et il faut alors les **14 UPDATE** de répartition |

⚠ **Les 5 commits d'avance de l'autre session ne touchent que `apps/hektor-v1/`**
*(le renommage « bienvu », une visionneuse de photos)* : **aucun conflit** avec `phase2/`.

---

## 6. LE PLAN SIMPLIFIÉ — **4 étapes, ~2 jours, réversible par un interrupteur**

### Étape 1 — LA RÈGLE, DERRIÈRE L'INTERRUPTEUR ⏱ 1 j · *aucun effet tant qu'il est éteint*

Un seul fichier, une seule fonction : `recalculer_les_chaines`
*(`phase2/sync/affaire_ledger.py:1068`)*. Code **additif** : la règle actuelle reste le
premier cas ; les replis du § 2 et du § 3 ne jouent qu'après son échec, **et seulement si
`APP_CHAINAGE_V2=1`**.

**Les contrôles, hors ligne, sur une copie :**

| | |
|---|---|
| l'oracle | la simulation rejoue la règle actuelle à **31 065/31 066 = 100,00 %** |
| interrupteur **éteint** | le code doit rendre **exactement** 12 702 chaînes — *témoin inverse obligatoire* |
| interrupteur **allumé** | **12 278** chaînes, **426** transactions déplacées |
| les 3 invariants | jamais deux ventes · jamais deux compromis vivants · rien après la vente |
| les refus | **42** ventes seules, **6** ambiguës, **4** abstentions — **nommées au journal** |

⛔ **Rien n'est poussé à cette étape.** L'interrupteur reste à 0.

### Étape 2 — LE CONTRÔLE ET LES ÉPREUVES ⏱ 0,5 j

`fermee_selon_le_run()` *(`phase2/checks/verifier_regle_chainage.py:126`)* et les deux
épreuves existantes, **avec le même interrupteur**.
⚠ **Elles doivent passer AU ROUGE d'abord** : c'est le témoin que la correction mord.

### Étape 3 — UNE NUIT, INTERRUPTEUR ALLUMÉ ⏱ *son accord*

```
avant : une PHOTO des chaines (un .json par app_affaire_id) -- la ceinture,
        meme si le retour arriere ne l'exige pas
puis  : APP_CHAINAGE_V2=1 dans .env, et on laisse le run de 05:00 tourner
```

**Le lendemain matin :** le compte *(12 278)* · les 3 invariants sur la base réelle · les
refus nommés au journal · `app_affaire_ledger__sb` *(la doublure)* qui suit · et **les 5
biens vivants regardés à l'œil, un par un**.

⛔ **Si quoi que ce soit cloche : `APP_CHAINAGE_V2=0`, et la nuit suivante remet tout
en place.** Aucune donnée à réparer.

### Étape 4 — CE QUI ATTEND LA CONFIANCE ⏱ 0,5 j, *plus tard*

```
a. les 14 lignes de repartition a deplacer (+2 a la main)  -> APRES 3 nuits propres,
   parce que c'est la SEULE chose qui rend le retour arriere non gratuit
b. Supabase app_chaine_pour                                -> 1 a 15 affaires/mois,
   divergence < 24 h, pas bloquant
c. une sentinelle permanente : « une ligne de repartition pointe une chaine qui
   n'existe plus ». Aujourd'hui : 1 (l'affaire 1001347, deja connue).
```

---

## 7. ⭐ POURQUOI C'EST « SANS RIEN CASSER » — les cinq raisons, chacune mesurée

| | |
|---|---|
| **un seul fichier, une seule fonction** | le push la transporte déjà ; rien d'autre à toucher |
| **un interrupteur, éteint par défaut** | le patron existe déjà dans le projet |
| **le retour arrière est gratuit** | une chaîne est une déduction refaite chaque nuit en 0,09 s |
| **le front n'a rien à changer** | vérifié : il groupe par `app_chaine_id` et juge par `!vente && …` |
| **l'impact visible est minuscule** | **5 biens vivants** sur 420 touchés |

⚠ **ET LE SEUL GESTE IRRÉVERSIBLE EST ISOLÉ** : le déplacement des 14 lignes de
répartition. Il est **sorti du chemin critique** et attend trois nuits propres.

---

## 8. ⛔ LES FEUX VERTS, RÉDUITS À DEUX

| | |
|---|---|
| écrire le code derrière l'interrupteur *(étapes 1-2)* | ✅ **additif et inerte** — j'enchaîne |
| **allumer l'interrupteur pour une nuit** *(étape 3)* | ⛔ **son accord** — 426 numéros réécrits |
| déplacer les 14 lignes de répartition *(étape 4a)* | ⛔ **son accord**, plus tard |

*(Le patch Supabase et la sentinelle ne sont plus des prérequis.)*

---

## 8-bis. CE QUE JE NE FAIS PAS

```
- les 213 transactions SANS DATE (compromis a 0000-00-00) : la 3e faille, ENTIERE.
- le § 3.4 (vente -> offre refusee) : ECARTE par Frederic. 5 ventes restent seules.
- le § 2.3 pour un compromis VIVANT : ECARTE. 21 cas inchanges.
- deviner : 42 + 6 + 4 restent SEULES ET SIGNALEES.
- toucher au front : verifie, il n'en a pas besoin.
- rejouer l'historique : AUCUNE migration. Le run refait tout chaque nuit.
```

---

## 9. CE QUE ÇA DÉBLOQUE AILLEURS

- l'appariement avec le classeur : **les 37 « ventes manquantes » tombent à ~3** ;
- le registre des transactions cesse de montrer deux affaires là où il n'y en a qu'une ;
- la question du classeur *(« 151 affaires où ton classeur peut corriger l'app »)* se
  repose **sur une base saine**.

**Simulation** *(scratchpad, non versionnée)* : `audit_final_chainage.py` — elle rejoue
quatre états *(actuel, vente seule, vente + point 4 large, **la règle retenue**)* et
contrôle les invariants à chaque fois. Aucune écriture.
