# LE STATUT DES ARCHIVES — 09/10/2026

> Ouvert le 09/10 après un signalement de Frédéric : *« je n'ai plus que 201 annonces dans
> mon index archivé »*. **Note de reprise : tout est mesuré, rien n'est corrigé.**
> Aucun code n'a été modifié pour ce sujet, aucun appel d'écriture, aucun déploiement.

---

## 1. LE SIGNALEMENT, ET CE QU'IL ÉTAIT VRAIMENT

**La base n'a rien perdu : 35 317 lignes dans `app_archive_annonce_index_current`.**

Les 201 venaient d'un **second filtre resté allumé**. En basculant ARCHIVE → « Archives »,
le filtre STATUT PHASE 1 reste sur « Actif / offre / compromis ». Or dans les archives il n'y
a que **199 « Actif » + 2 « Sous offre » = 201**. Reproduit à l'écran, puis levé : en passant
le statut à « Tous », l'écran affiche **34 502**.

⚠ **Ce n'est lié ni au run du 09/10, ni au chantier ⑤.** Le seul commit front des trois
derniers jours (`78e6574`) ne touche que deux conditions de la fiche détail.

---

## 2. MAIS 34 502 ≠ 35 317 — LE VRAI DÉFAUT

| | |
|---|---|
| dans la table | **35 317** |
| ce que l'écran peut montrer, au mieux | **34 502** |
| **statut vide → invisibles quoi qu'on fasse** | **785** |
| « Estimation », exclues volontairement | 30 |

Quand aucun statut n'est choisi, l'écran applique toujours
`query.neq('statut_annonce', 'Estimation')` — [api.ts:2744](../apps/hektor-v1/src/lib/api.ts)
pour les archives, [api.ts:2387](../apps/hektor-v1/src/lib/api.ts) pour le parc vivant.
**En SQL, « différent de » rejette aussi les cases vides.** Les 785 archives sans statut sont
donc inatteignables : aucun filtre ne les affiche, et la recherche passe par le même chemin.

---

## 3. LE TROU EST-IL AILLEURS ? NON — vérifié sur les trois index

| index de l'app | lignes | statut NULL | chaîne vide |
|---|---|---|---|
| parc vivant (`app_dossier_current`) | 13 471 | **0** | 0 |
| vendus / clos (`app_historical_…`) | 8 939 | **0** | 0 |
| **archives** (`app_archive_…`) | 35 317 | **785** | 0 |

Côté serveur : **3 241 archivées** sans fiche détail, **69 non archivées**, **0** côté vendus.

**Pourquoi les vendus sont épargnés** : un bien vendu porte `archive = 0`. Le balayage a
**10 variantes** ([sync_raw.py:28](../sync_raw.py)) — les **5 « active » téléchargent le
détail, les 5 « archived » jamais** :

```
scope active           archive=0   detail : OUI
scope archived         archive=1   detail : NON
scope active_neuf      archive=0   detail : OUI
scope archived_neuf    archive=1   detail : NON
scope active_pro       archive=0   detail : OUI
scope archived_pro     archive=1   detail : NON
scope active_loc       archive=0   detail : OUI
scope archived_loc     archive=1   detail : NON
scope active_loc_pro   archive=0   detail : OUI
scope archived_loc_pro archive=1   detail : NON
```

⚠ **Seule exception** : les **423 biens à la fois « Vendu » ET archivés** sont gelés comme les
autres archives.

---

## 4. LA CHAÎNE DE LA CAUSE, BOUT À BOUT

1. **Le statut n'existe qu'à un seul endroit chez nous** : la fiche détail
   (`hektor_annonce_detail.statut_name`), remplie par un appel `AnnonceById`.
   La table du listing n'en est qu'une **copie** — [build_case_index.py:169](../build_case_index.py)
   prend `d.statut_name`.
   Preuve : **58 065 lignes avec statut ⇔ 58 065 ont une fiche détail · 3 310 sans statut ⇔
   3 310 n'ont pas de fiche détail** (3 exceptions).
2. **Le listing de Hektor ne porte AUCUN statut.** Vérifié sur la réponse brute réelle de
   l'annonce 63053, 19 champs : `NEGOCIATEUR, NO_DOSSIER, NO_MANDAT, agence, archive, corps,
   dateenr, datemaj, diffusable, id, idtype, localite, offredem, partage, photo, prix,
   surface, titre, valide`. Ni `statut`, ni `state`, ni `etat`.
3. **Le détail n'est lu que si l'annonce a changé** — [sync_raw.py:1657](../sync_raw.py) :
   `detail_ids = sorted(changed_annonce_ids)` (le run ne passe pas `--force-annonce-detail-full`),
   et une variante `archived` n'y entre jamais (`sync_details: False`).
4. **C'est une décision écrite, pas un oubli** : *« COÛT : seules les actives téléchargent un
   détail… ATTENTION AU FREIN DE DÉBIT : notre IP a déjà été bannie une fois »*
   (commentaire du code, et feuille de route du 24/08).
5. **Le garde-fou censé rattraper les manques est MORT** : le run passe `--missing-only`, mais
   la fonction qui l'implémente porte *« SANS APPELANT depuis le 21/07/2026 »*. L'option est
   passée tous les soirs et **ne fait rien**. → matière pour le **chantier ④**.

**Il n'existe aucune copie du statut ailleurs chez nous.** Inventaire pour 10 annonces témoins :
`hektor_annonce_detail` 0/10 · réponses brutes `annonce_detail` 0/10 ·
`hektor_annonce_console_detail` 0/10 · `hektor_annonce_chauffage_detail` 0/10 ·
cache de détail d'archive de l'app : **9 fiches en tout**, 0 parmi les 785.

### ✅ Et Hektor, lui, a bien le statut — vérifié par 10 appels API

| annonce | statut chez Hektor | archive |
|---|---|---|
| 63053, 62927 | **Actif** | 1 |
| 62541 | **Estimation** | 1 |
| 62484, 58635, 58413, 58412, 58411, 58408, 58407 | **Clos** | 1 |

---

## 5. L'OUTIL EXISTE DÉJÀ, ET IL FAIT EXACTEMENT CE QU'IL FAUT

**`sync_archived_annonce_details.py`**, lanceur **`run_archived_annonce_details.ps1`**.
Ses candidats ([l. 101](../sync_archived_annonce_details.py)) sont les archives qui

- **n'ont pas de fiche détail**, **ou**
- **n'ont jamais été marquées synchronisées**, **ou**
- dont la **`date_maj` est postérieure à `last_detail_sync_at`** ← *les archives modifiées
  chez Hektor depuis notre dernière lecture : exactement le point soulevé par Frédéric*

Lancé en `--dry-run --skip-listing-refresh` le 09/10, **sans un seul appel à Hektor** :

```
Archived detail candidates: 5246 / total=37773 with_detail=34532 marked_synced=34532
       5 246  =  3 241 sans detail  +  ~2 005 modifiees depuis leur lecture
```

⚠ **Il n'est branché NULLE PART** : aucune tâche planifiée, absent du run de nuit. Il a servi
une fois à la main pour le grand rattrapage, puis il a été oublié.

### Le coût de le faire tourner chaque nuit est dérisoire

```
archives modifiees dans les dernieres 24 h :      1
dans les 7 derniers jours                  :     14   (~2 par nuit)
dans les 30 derniers jours                 :  1 639
plus ancien                                : 36 119
```

Et **aucun risque de lecture de masse au premier soir** : les 37 773 archives ont déjà leur
marqueur de date à jour dans `sync_annonce_state`, **0 divergence**.

---

## 6. LE PLAN — rien n'est fait, tout est chiffré

| | quoi | coût | ce qu'il faut |
|---|---|---|---|
| **①** | **Rattraper les 5 246 détails** avec l'outil existant | ~2 h 20 à 2 300 lectures/h | **accord de Frédéric — ça appelle Hektor** |
| **②** | **Envoyer le statut à l'app** | **rien à coder** : l'outil enchaîne `normalize_source` → `build_case_index` recopie le statut → `app_view_generale` → le push de nuit remplit l'index | — |
| **③** | **Brancher l'outil dans le run de nuit** (les archives modifiées redeviennent actuelles) | **~2 appels par nuit** | « vas-y » (modif du run) |
| **④** | **Le filet côté écran** : `statut vide OU différent de Estimation`, aux deux endroits | front | « vas-y » + **déploiement Vercel** |

**La première marche, et c'est la méthode du projet** : un **palier de 50** (`--limit 50`),
pour mesurer la vraie cadence et vérifier que le statut arrive jusqu'à l'app. Puis le reste.

⚠ **Pas pendant que le rattrapage des documents tourne** : c'est lui qui a déjà fait bannir
notre IP.

---

## 7. OÙ ON EN EST AU MOMENT DE LA PAUSE — 09/10, ~11 h 40

- **Le lot de documents de la nuit est terminé** : 2 500 posés à 21 h, **2 495 faits,
  1 en erreur, 4 en cours à 11 h 37** — fini vers 11 h 40. Il n'y avait rien à arrêter.
- **L'erreur** : annonce **24148**, coupure réseau sur un PDF
  (`UND_ERR_SOCKET`). Une sur 2 500. ⚠ **Mais le composeur de lot ne rejoue JAMAIS une annonce
  en erreur** (*« les 403 répétés ont fait bannir l'IP »*) : **24148 est désormais écartée
  définitivement** du rattrapage des documents. À traiter à la main un jour.
- **Le lot du soir est passé à 1 000** *(décision de Frédéric, commit `c6ddcec`)* : la file
  sera vide avant le run. Reste ~6 910 annonces → ~7 nuits, fin vers le 16-17/10.
  ⚠ **À remettre à 2 500** quand les vendus/clos seront finis.
- **G.1-b** : les 515 brouillons ne seront atteints que la **nuit du 15 au 16/10**.

### Pour reprendre

1. Relire cette note (elle contient toutes les mesures, rien à refaire).
2. Décider l'ordre entre ①②③④ ci-dessus.
3. Commencer par le **palier de 50**, hors des heures du rattrapage des documents.

---

## 8. FAIT LE 09/10 — LE CORRECTIF ① ET LE PALIER DE 50

### ① Le filet côté écran — **codé, build vert, PAS déployé** *(commit `933286a`)*

```
avant :  query.neq('statut_annonce', 'Estimation')
apres :  query.or('statut_annonce.is.null,statut_annonce.neq.Estimation')
```

Aux **deux** branches par défaut : `applyDossierFiltersToQuery` (parc vivant) et
`applyArchiveIndexFiltersToQuery` (archives). `npm run build` vert en **5,77 s**.
⚠ **Les deux branches jumelles `annonceSearchListingsFilterValue` portent le même défaut**
et ne sont **pas** touchées — périmètre à décider par Frédéric.
⚠ **Rien n'est en ligne tant que le push n'est pas fait** (pousser = déployer).

### ② Le palier de 50 — **réussi, chaîne prouvée de bout en bout**

```
sync_archived_annonce_details.py --limit 50 --batch-size 50 --skip-listing-refresh
     50 fiches en 51 s   (~1,0 s par annonce)
```

| étape | avant | après |
|---|---|---|
| `hektor_annonce_detail` | 58 068 | **58 118** (+50) |
| archives sans fiche détail | 3 241 | **3 191** (−50) |
| `case_dossier_source` sans statut | 3 313 | **3 263** (−50) |
| `app_view_generale`, archives sans statut | 3 241 | **3 191** (−50) |

Témoins **36280 / 36281 / 36426** : `<<vide>>` → **« Clos »** partout, et Hektor confirme
« Clos » par appel direct.

**⚠ DEUX PIÈGES PAYÉS, à ne pas repayer :**
1. **`--no-normalize` ne stocke rien d'exploitable.** L'outil rapporte bien les fiches (réponses
   brutes HTTP 200, 12 774 octets) mais c'est `normalize_source.py` qui les transforme en
   `hektor_annonce_detail`. Sans lui, le compteur ne bouge pas et l'outil dit quand même
   « synced 50/50 ».
2. **Il faut le python du VENV** : `.\.venv\Scripts\python.exe`. Le python global n'a pas
   `openpyxl` et `normalize_source.py` s'arrête dessus.
3. Et lire le miroir **sans `immutable=1`** : ce drapeau sert un instantané figé, on croit
   que rien n'a bougé.

**LA CHAÎNE COMPLÈTE, dans l'ordre**, avec ses temps mesurés :

```
1. sync_archived_annonce_details.py --limit N      ~1,0 s par annonce
2. .venv\Scripts\python.exe normalize_source.py    2 min   (quel que soit N)
3. .venv\Scripts\python.exe build_case_index.py    5 min 37 (quel que soit N)
4. .venv\Scripts\python.exe phase2efresh_views.py 34 s   (quel que soit N)
5. le push vers Supabase  ->  NON FAIT, c'est le run de nuit qui l'emporte
```

⭐ **Les étapes 2 à 4 coûtent ~8 minutes quel que soit le nombre de fiches.** Faire un seul
gros lot puis une seule passe de chaîne est donc bien plus efficace que des paliers répétés.

### Ce qui reste du rattrapage

```
5 196 fiches encore a lire  (5 246 - 50)
      a 1,0 s/fiche          1 h 28
      a la cadence SURE de 2 300 lectures/h  ->  ~2 h 15 avec des pauses
      + ~8 min de chaine, UNE seule fois
```

⚠ **Le palier a tourné à ~3 500 lectures/heure, au-dessus de la cadence prouvée sûre
(2 300/h du run chauffage).** Pour le gros lot, il faut **freiner** — c'est ce débit qui a
déjà fait bannir notre IP.
