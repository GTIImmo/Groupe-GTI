# Étude des correspondances : le registre des mandats de l'app face aux classeurs d'historique

**27/10/2026 · lecture seule** — rien n'a été écrit en base, rien n'est commité.
Demande de Frédéric : *« propose-moi une étude de correspondance entre mon app et les classeurs
disponibles que j'ai fournis, un rapport détaillé pour m'aider »*, **année par année**, et
*« Hektor change la réf du produit, cela risque de poser problème à la vue de mon registre ? »*

Cette étude porte sur deux des trois choses à ne pas confondre :

| | quoi | ici |
|---|---|---|
| **① la data** | `app_mandat` — 26 932 lignes, dont **24 584** dans le périmètre du registre | ✅ étudiée |
| **② la vue** | le registre des mandats affiché (`app_registre_mandats_current`) | ✅ étudiée |
| ③ le futur registre électronique | générer nous-mêmes le numéro, à la place de PROTEXA | ⛔ hors sujet, chantier suivant |

> Audit limité à l'objet **mandat**, geste **lire / remonter**. Créer, modifier, supprimer un
> mandat et les autres objets ne sont pas mesurés.

---

## 1. L'essentiel en une page

```
LA DATA RETROUVE PRESQUE TOUT CE QUE PORTENT LES CLASSEURS
   export Modelo        24 038 / 24 054 mandats retrouvés   (99,9 %)
   registre légal       7 153 / 7 841 de son périmètre       (91 %)  - 623 absents, surtout des RECHERCHES
   registre Hektor 2026   493 / 495                          (99,6 %)
   liste de février        76 / 80   ·   protexa recherche 16 / 16

CE QUI EST FAUX OU MANQUE DANS LA DATA
   ⛔ ~14 430 dates de début et ~13 390 dates de fin À LA VEILLE        2009 -> février 2026
   ⛔ 518 mandats de recherche + 99 ventes du registre légal absents   2014 -> 2024
   ⚠ ~555 des 561 natures « inconnue » et ~150 des 561 types vides : les classeurs savent les remplir
   ⚠ aucune date de NUMÉRO, aucune date de SIGNATURE dans la data
   ⚠ la RÉF bouge chez Hektor : la vue affiche et cherche une réf qui n'est plus la bonne

CE QUI EST JUSTE
   ✅ 2026 : 488 dates sur 493 identiques au registre Hektor, 509 types sur 509 identiques
   ✅ l'identité d'une ligne ne dépend pas de la réf (annonce:numéro)
   ✅ aucun mandat inventé : tout ce que porte la data existe dans un classeur, sauf 57 lignes expliquées (§4.5)
```

---

## 2. Les classeurs, ce que chacun sait dire

| classeur (dossier `Projet/`) | période | numéros | clé possible | dates portées | ce qu'il apporte |
|---|---|---|---|---|---|
| `mandats_extraits.xlsx` — export **Modelo**, 27/02/2026 | 2009 → 02/2026 | 1 → 6 301 055, 26 404 lignes (24 054 hors locations) | **n° + réf** | début, fin, date du mandat — **en UTC** | dates justes, type, nature, réf d'origine |
| `Ancien registre des mandat.csv` — **registre légal** | 15/12/2014 → 19/12/2024 | 9001 → 17441, continu | **n° seul** (pas de réf) | **date du numéro** | absents, date du numéro, nature, mandants |
| `Export_RT14405_12598.xls` — **registre légal Hektor** | 02/03 → 15/10/2026 | 18420 → 18943 | **n° + annonce** (réf `V<agence><annonce>`) | date du mandat = **réservation du numéro** | contrôle 2026, réf d'origine, date du numéro |
| `liste mandat du 02_02_2026 au 28_02_2026.xlsx` | février 2026 | 18340 → 18419 | n° + réf | début, fin (UTC) | contrôle février |
| `liste des mandats de recherche protexa.xlsx` | 2026 | 16 recherches | n° seul | date du mandat | contrôle des recherches |
| *(dans l'app)* signatures **ImmoSign** | 02 → 10/2026 | 432 mandats, 377 annonces | annonce | **date de signature** | date de signature |

⚠ **Deux fichiers sont des copies exactes** (même empreinte) : `Probleme id nego/Registre de 2014  2024 .csv` et
`Probleme id nego/mandats_extraits.xlsx`. Inutile de les traiter.
⚠ **Pas de registre légal 2025 → février 2026** (n° 17442-18419) : décidé « pas nécessaire » le 27/10 —
ces années s'appuient sur l'export Modelo seul.

---

## 3. La méthode

**La clé.** Une ligne de la data est le couple **(numéro, annonce)** — c'est la clé de `app_mandat`
et l'identifiant de la vue (`register_row_id = "annonce:numéro"`). Un numéro seul ne suffit pas :
18 271 numéros pour 24 579 lignes (lots multiples, numéros d'avant 2014, numéros recyclés).

**Quatre façons de rattacher une ligne de classeur**, dans cet ordre :
1. **numéro + réf** identiques ;
2. **numéro + annonce**, l'annonce lue dans la réf 2026 (`V39 0061680` → annonce 61680) ;
3. **numéro seul**, s'il ne désigne qu'une ligne ;
4. **numéro + nom** du mandant, s'il désigne plusieurs lignes et qu'un seul bien partage un nom.
Sinon : **ambigu** (à trancher à la main).

**Trois précautions.**
- Les dates UTC sont **ramenées à l'heure de Paris** avant comparaison.
- Le périmètre est celui du registre : vente, vente pro, neuf, et les recherches. Les locations
  et gestions sont **hors périmètre** par décision du 28/09 : elles ne comptent pas comme absentes.
- **Témoins** : les totaux bouclent (24 038 + 14 absents + 2 ambigus = 24 054 pour Modelo ;
  7 153 + 623 + 65 + 502 = 8 343 pour le registre légal) ; le décalage d'un jour n'apparaît **que**
  sur les dates stockées à minuit heure de Paris (22-23 h UTC), jamais sur les autres (165 sur 165 justes).

---

## 4. Année par année

### 4.1 Le tableau

« veille » = notre date est la veille de celle du classeur (le défaut d'un jour) ·
« numéro ≠ » = la date du registre légal (le numéro) diffère de notre début d'un vrai écart.

| année | data | registre légal : lignes · retrouvés · **absents** · veille · numéro ≠ | Modelo : lignes · retrouvés · absents · **début veille** · **fin veille** · nature à remplir · mandants ? | 2026 (Hektor + février) : lignes · retrouvés · absents · dates ≠ |
|---|---|---|---|---|
| 2009 | 30 | — | 30 · 30 · 0 · 16 · 19 · 0 · 0 | — |
| 2010 | 260 | — | 260 · 260 · 0 · 172 · 163 · 0 · 1 | — |
| 2011 | 2 548 | — | 2 548 · 2 548 · 0 · **1 582** · 1 143 · 1 · 10 | — |
| 2012 | 2 045 | — | 2 045 · 2 045 · 0 · **1 291** · 1 469 · 0 · 12 | — |
| 2013 | 2 278 | — | 2 278 · 2 278 · 0 · **1 301** · 1 316 · 6 · 4 | — |
| 2014 | 2 171 | 49 · 27 · 2 · 1 · 11 | 2 171 · 2 171 · 0 · **1 280** · 1 272 · 7 · 7 | — |
| 2015 | 1 766 | 932 · 592 · **117** · 321 · 61 | 1 766 · 1 766 · 0 · **1 085** · 1 077 · **93** · 0 | — |
| 2016 | 1 786 | 942 · 632 · **105** · 265 · 110 | 1 776 · 1 776 · 0 · 954 · 904 · **165** · 0 | — |
| 2017 | 1 750 | 784 · 645 · 68 · 297 · 109 | 1 750 · 1 750 · 0 · **1 086** · 1 008 · **120** · 3 | — |
| 2018 | 1 525 | 579 · 556 · 21 · 341 · 31 | 1 524 · 1 524 · 0 · 972 · 936 · 40 · 1 | — |
| 2019 | 1 434 | 536 · 521 · 12 · 304 · 15 | 1 433 · 1 433 · 0 · 886 · 925 · 13 · 0 | — |
| 2020 | 1 207 | 439 · 418 · 21 · 231 · 21 | 1 201 · 1 201 · 0 · 639 · 658 · 45 · 1 | — |
| 2021 | 1 183 | 823 · 761 · 55 · 483 · 38 | 1 184 · 1 183 · 0 · 710 · 709 · 24 · 2 | — |
| 2022 | 1 109 | 1 181 · 1 104 · 70 · **650** · 60 | 1 109 · 1 109 · 0 · 693 · 663 · 15 · 0 | — |
| 2023 | 1 083 | 1 153 · 1 014 · **114** · **598** · 39 | 1 083 · 1 083 · 0 · 680 · 647 · 14 · 0 | — |
| 2024 | 912 | 925 · 883 · 38 · 496 · 27 | 930 · 925 · 5 · 522 · 481 · 10 · 1 | — |
| 2025 | 814 | *pas de registre* | 821 · 815 · 6 · **486** · **0** · 0 · 14 | — |
| 2026 | 675 | *pas de registre* | 144 · 140 · 3 · 76 · 0 · 0 · 3 | 575 · 569 · 5 · 80 *(76 février + 4)* |
| sans date | 8 | — | 1 · 1 · 0 · 0 · 1 · 0 · 0 | — |
| **total** | **24 584** | **8 343 · 7 153 · 623 · 3 987 · 522** *(+ 65 ambigus, 502 hors périmètre)* | **24 054 · 24 038 · 14 · 14 431 · 13 391 · 553 · 59** | **575 · 569 · 5 · 80** |

### 4.2 2009 → 2013 : avant le registre légal

Seul l'export Modelo couvre ces années. **Tout est retrouvé (7 161 sur 7 161).** Le seul défaut est
la **date à la veille, sur 53 à 66 % des lignes selon l'année** (4 362 débuts, 4 110 fins).
Aucune date de numéro n'existe pour ces années : aucun classeur ne la porte.

### 4.3 2014 → 2024 : le registre légal existe

- **Les absents sont des recherches.** 623 mandats du registre légal ne sont pas dans la data :
  **518 recherches**, 99 ventes (souvent des lots : un appartement et deux garages, n° 9084-9086),
  6 locations. Pics : 2015 (117), 2016 (105), 2023 (114).
- **La date du registre légal est la date du numéro**, pas celle du début : 2 644 identiques,
  3 987 « veille » (notre défaut d'un jour), **522 vrais écarts** numéro ≠ début. Mesuré à part :
  **89 % des mandats sont signés le jour du numéro**, 398 portent une signature **antérieure** au
  numéro (136 en 2022, 0 en 2024).
- **La nature « inconnue » se remplit** : 553 lignes par l'export (pics 2015-2017), 180 par le
  registre légal.
- **65 numéros ambigus** : le numéro est chez nous sur plusieurs biens, aucun ne porte le nom du
  mandant légal. À trancher à la main.

### 4.4 2025 : l'export Modelo seul

815 sur 821 retrouvés, 6 absents. **486 débuts à la veille, mais aucune fin à la veille** : en
2025 les fins sont stockées à 22 h 59 UTC (= 23 h 59 à Paris), le même jour. 14 mandants sans
nom commun : à regarder.

### 4.5 2026 : la data est déjà presque juste

| classeur | lignes | retrouvés | à corriger |
|---|---|---|---|
| février (liste) | 80 | 76 | **76 dates à la veille — défaut de NOTRE script** (`manual_mandat_corrections.py:32`) · 3 absents (18383, 18404, 18408) · 1 ambigu |
| registre Hektor | 495 | 493 | 18502 et 18928 vides (numéro sans corps) · dates 18536 (16/**11** au lieu du 16/04), 18570, 18911, 18437 · absents 18455, 18500 (avenant) |
| protexa recherche | 16 | 16 | 1 date vide, 1 nature à remplir |
| ImmoSign | 432 signatures | — | date de signature disponible (aucune dans la data aujourd'hui) |

Réservations sans mandat que la data porte comme des lignes : **18424, 18647, 18651, 18787
(VA6482, bien d'essai), 18894** — à marquer, jamais supprimer. Mandat d'essai inscrit au registre
légal : **18842 « M. CLOTURE Test »**.

**Les 57 lignes de la data qu'aucun classeur ne couvre** : 28 de 2026 dont 21 d'octobre (après
l'export du 15/10) · 4 recherches posées depuis le registre légal · les lots du **n° 10249** (8
annonces, 2016) et du **n° 1121** (8 annonces, 2016-2020) · 5 réservations ou numéros sans date.

---

## 5. Ce que chaque classeur peut corriger dans la data

| champ de la data | source qui fait foi | lignes à changer | vides à remplir |
|---|---|---|---|
| date de début | Modelo (Paris) jusqu'à 02/2026 · registre Hektor en 2026 | **14 431** + 76 (février) + 4 (2026) | 2 (2026) |
| date de fin | Modelo (Paris) | **13 391** | — |
| nature | Modelo, puis registre légal, puis registre Hektor | — | **~555 sur 561** « inconnue » (Modelo 553, légal 180, 2026 2 — en grande partie les mêmes lignes) |
| type | registre légal surtout, puis registre Hektor | 1 | **~150 sur 561** vides (légal : 126 SIMPLE, 16 EXCLUSIF) + 2 (2026) — les ~410 autres : aucun classeur ne dit le type |
| mandants | **aucune — ne pas écraser** | 0 | 2 (18502, 18928) |
| *nouveau* **date du numéro** | registre légal 2014-2024 · registre Hektor 2026 | — | **7 646** (7 153 + 493) |
| *nouveau* **date de signature** | ImmoSign | — | **432 mandats** (377 annonces) |
| *nouveau* **réf d'origine** | Modelo · registre Hektor 2026 · février | — | ~24 500 dont **312 renommées** (100 + 136 + 76) |
| lignes à ajouter | registre légal · registre Hektor · février · Modelo | — | **518 recherches + 99 ventes** · 18455, 18500 · 3 février · 14 Modelo |

---

## 6. La réf : oui, son changement pose problème à la VUE — mais pas à la DATA

**Ce qui est mesuré.**
- Depuis 2026, Hektor remplace la réf du bien par **le numéro du dernier mandat**, et il continue :
  **20 réfs ont changé entre le 23/09 et aujourd'hui** (`EM70781` → `18611`, `V390061680` → `18442`,
  `VM46636` → `18753`…).
- **244 lignes** de la vue ont une réf qui est un numéro ; **13 affichent le numéro d'un AUTRE mandat**
  (le mandat 17654 de 2025 affiche « 18629 » ; 18869 affiche « 17946 »).

**Ce qui n'est PAS touché.** L'identité d'une ligne de la vue est `annonce:numéro`
([export_app_payload.py:2375](../phase2/sync/export_app_payload.py)) : la réf n'y entre pas. Aucune ligne
ne disparaît ni ne se dédouble quand la réf change.

**Ce qui EST touché.**

| usage | effet du renommage |
|---|---|
| **affichage** (colonne « N° mandat », ligne secondaire, modales, en-têtes de fiche) | la réf affichée est la réf ACTUELLE de l'annonce : un vieux mandat montre le numéro du mandat suivant |
| **recherche** (`search_text`, refait chaque nuit avec la réf actuelle) | chercher l'ancienne réf (« EM70781 ») **ne trouve plus** le mandat |
| **recherche par chiffres** (`listingSearchColumns` cherche aussi dans `numero_dossier`) | taper « 18629 » remonte aussi le mandat 17654, dont la réf est devenue 18629 |
| ⚠ autres usages de la réf (photos, Matterport, vitrine, documents) | **non mesuré** |

**Remède proposé (rien n'est décidé)** : une colonne **`ref_origine`** dans `app_mandat`, posée une
fois (classeurs, puis première réf vue) et **jamais réécrite** ; la vue l'affiche à la place de la
réf actuelle pour les mandats passés ; `search_text` contient **les deux** réfs (le paramètre `extra`
de `build_search_text` existe déjà pour ça).

---

## 7. Les quatre dates d'un mandat

| date | ce que c'est | ce qu'on a | où |
|---|---|---|---|
| **numéro** | réservation / inscription au registre légal | 2014-2024 et 2026 seulement | registre légal · registre Hektor 2026 |
| **signature** | signature du mandant | 2026 seulement (ImmoSign) | `app_console_document.metadata_json.signature.signed_at` |
| **début** | début du contrat | partout — à la veille sur ~60 % jusqu'à 02/2026 | `app_mandat.date_debut` |
| **fin** | fin du contrat | partout — à la veille sur ~58 % de 2009 à 2024, juste en 2025-2026 | `app_mandat.date_fin` |

**En 2026, la date de début de Hektor est la date du NUMÉRO**, pas la signature : sur 432 mandats
signés, la signature arrive **1 à 78 jours après** (1 j : 79 · 2 j : 33 · 3-7 j : 97 · plus : ~100) ;
les 315 où début ≠ signature ont été relus après la signature sans changer. **2 mandats sont signés
avant leur numéro** : 18495 (−3 j), 18938 (−1 j).

**D'où vient la veille.** De l'API Hektor, qui tronque une date UTC (preuve : `payload_json` du n°
16436 porte déjà `2024-06-12` pour un 13/06 à Paris) — et, pour février, de **notre** script.

---

## 8. Où écrire pour que la correction tienne

```
classeurs ──► app_mandat (la DATA) ──► fabrication du registre ──► la VUE
                  ▲
                  └── le run de nuit RÉÉCRIT : type, nature, début, fin, mandants
                      (mandat_ledger.py l. 681-699) — seule la date de clôture est protégée
```

- **Une colonne NEUVE est protégée d'office** : le run ne réécrit que les colonnes qu'il nomme.
  `ref_origine`, `date_numero`, `date_signature` **survivent à la nuit** sans toucher au run.
- **Corriger début, fin, type ou nature** demande une protection, sinon Hektor remet sa valeur la
  nuit suivante. Deux portes existent déjà :
  - `CHAMPS_APP_MANDAT` + le carnet `app_mandat_champ_app` (« l'app gagne quand elle a quelque chose
    à dire », 28/08) — aujourd'hui pour la seule date de clôture ;
  - les colonnes `nature_app` / `type_app` / `source_app`, **déjà utilisées** sur 554 lignes
    (Modelo, registre légal). ⚠ Non vérifié : que la fabrication du registre les préfère à la valeur de Hektor.
- **La vue** lit une table refaite à chaque push : toute colonne neuve doit être ajoutée à la table,
  à la vue **et** au push (piège déjà payé avec `search_text`, 30/07), et `min-width` du tableau
  remonté si une colonne s'affiche.

---

## 9. Plan de mise à jour proposé — par étapes, rien n'est décidé

| étape | ce qu'elle fait | lignes | risque | retour arrière |
|---|---|---|---|---|
| **1. Les trois colonnes neuves** | `ref_origine`, `date_numero`, `date_signature` dans la data, remplies depuis les classeurs et ImmoSign ; la vue les affiche, la recherche lit les deux réfs | ~24 500 · 7 646 · 432 | **faible** : additif, protégé d'office | vider les colonnes |
| **2. Compléter les vides** | nature, type ; 18502 et 18928 entiers | ~555 · ~150 · 2 | faible : on remplit, on n'écrase pas | effacer les valeurs posées (marquées `source_app`) |
| **3. Réparer les dates à la veille** | début et fin depuis Modelo (Paris) ; février ; 4 dates 2026 ; corriger le fuseau de notre script | 14 431 · 13 391 · 80 | **moyen** : touche le run (protection) et 14 000 lignes | sauvegarde datée + carnet effaçable |
| **4. Ajouter les absents** | 518 recherches et 99 ventes (porte `registre_legal` qui existe) · 18455 · 18500 · février · Modelo | ~640 | moyen : recherches sans contact rattaché | lignes marquées par leur origine |
| **5. La revue à la main** | 65 ambigus · 59 + 46 + 14 mandants sans nom commun · 5 réservations · 2 signatures avant le numéro · 18842 et VA6482 (essais) | ~200 | aucun : on regarde | — |

Questions à Frédéric : l'ordre ; le périmètre de l'étape 4 (les 518 recherches de 2014-2024 sont-elles
voulues dans la vue ?) ; pour l'étape 3, protéger par le carnet ou par une colonne « date juste » à côté.

---

## 10. Limites

- Le registre légal n'a pas de réf : rattachement par numéro, puis par nom quand le numéro a plusieurs biens.
- « Mandants sans nom commun » compare des mots de 3 lettres et plus : il repère les noms différents,
  pas les fautes d'orthographe ; et `mandants_texte` est réécrit par nos liens.
- La date de signature n'existe que pour les mandats ImmoSign (2026) : les mandats papier n'en ont pas.
- Les autres usages de la réf (photos, Matterport, vitrine) ne sont pas mesurés.

## 11 bis. Synthèse SANS colonne neuve (demande de Frédéric, 27/10)

> *« Oublie les colonnes supplémentaires pour les dates, garde les colonnes actuelles. »*
> Donc : ni `date_numero`, ni `date_signature`, ni `ref_origine`. Seules les colonnes
> existantes sont touchées. Rien n'est décidé.

| # | anomalie | lignes | correction dans les colonnes actuelles | source |
|---|---|---|---|---|
| A | début à la veille | 14 431 | `date_debut` ← date Modelo ramenée à Paris | Modelo |
| A | fin à la veille | 13 391 | `date_fin` ← idem | Modelo |
| A | février 2026 à la veille (notre script) | 76 | `date_debut` ← liste de février ; corriger `manual_mandat_corrections.py:32` | février |
| A | dates 2026 fausses | 4 (18437, 18536, 18570, 18911) | `date_debut` ← registre Hektor | registre Hektor |
| B | mandats sans corps | 2 (18502, 18928) | remplir début, type, mandants | registre Hektor |
| C | nature « inconnue » | ~555 sur 561 | `nature` (par `nature_app`) | Modelo, légal |
| D | type vide | ~150 sur 561 | `type` (par `type_app`) ; ~410 restent vides | légal, Hektor |
| E | mandats absents | ~640 | lignes à AJOUTER (518 recherches, 99 ventes, 18455, 18500, 3 février, 14 Modelo) | légal, Modelo, Hektor |
| F | réf renommée par Hektor | 20 depuis le 23/09 ; 13 montrent le n° d'un autre mandat | ancienne réf ajoutée dans `search_text` (colonne existante) → de nouveau cherchable ; ⚠ l'AFFICHAGE reste la réf actuelle | Modelo, Hektor 2026 |
| G | à regarder à la main | 65 ambigus · ~120 mandants sans nom commun · 5 réservations sans mandat · 2 essais | aucune écriture automatique ; `mandants_texte` ne s'écrase jamais | — |

**Ce qu'on NE corrige PAS** : les 522 écarts « date du numéro ≠ début » du registre légal — ce
sont deux dates différentes, et sans colonne pour la date du numéro on garde le début du contrat.

⚠ **Condition pour A, C, D** : le run de nuit (`mandat_ledger.py` l. 681-699) réécrit début, fin,
type et nature depuis Hektor. Sans protection (carnet `CHAMPS_APP_MANDAT` ou `nature_app`/`type_app`),
la correction repart la nuit suivante. E (ajouts) et F (`search_text` extra) n'ont pas ce problème.

### 11 ter. Vérification avant la liste (27/10, code + base) — ⚠ elle corrige le §11 bis

- **Le registre affiché ne lit PAS `date_debut`, `date_fin`, `type`, `nature` de `app_mandat`.** Il lit
  `versions_json` (les versions brutes de Hektor, [export_app_payload.py:866](../phase2/sync/export_app_payload.py)),
  réécrit chaque nuit. Corriger les colonnes de `app_mandat` ne changerait RIEN à l'écran.
  Mesure : sur 24 579 lignes du registre, début et fin identiques à la data sur 24 570.
- **Nature : déjà faite.** `nature_app` est posée sur 503 des 561 « inconnue » depuis le 15/10
  (`reparer_nature_depuis_sources_legales.py`). Le registre n'a pas de colonne nature : rien à l'écran.
  Restent 58 « inconnue » sans `nature_app`.
- **Type : déjà rempli mais pas affiché.** `type_app` est posé sur 119 lignes sans type Hektor ;
  le registre leur montre toujours un type VIDE (119/119) : le fabricant ne lit pas `type_app`.
- **Neuf : 9 lignes du registre ont une date vide** alors que la data en porte une
  (17283, 17493, 17349, 16421…). Cause non mesurée.
- **Le patron qui marche existe** : la date de clôture (carnet `app_mandat_champ_app` → colonne
  `mandat_date_cloture_app` du registre → re-posée après chaque push, patch du 13/10). C'est le
  modèle pour protéger une date corrigée.
- Non mesuré : si le chemin du worker (`push_single_annonce_to_supabase.py`) refait le registre par
  la même fonction ; le chemin des mandats sans annonce (`registre_mandats_sans_bien.py`).

### 11 quater. Correctif 3 — CODÉ le 27/10 (« vas-y » de Frédéric), pas encore poussé

- `export_app_payload.py` : interrupteur `APP_REGISTRE_TYPE_APP` (allumé par défaut), `charger_types_app()` ;
  `mandat_type = type Hektor OU type du classeur` sur la ligne ET dans la fiche détaillée.
  `mandat_type_source` reste celui de Hektor (vide). `registre_depuis_app_mandat.py` suit la même règle.
- **Essai hors ligne** (registre fabriqué deux fois, rien envoyé) : 24 584 lignes des deux côtés, mêmes
  identifiants ; **119 lignes changent, aucune autre** ; colonnes touchées : `mandat_type`, fiche détaillée,
  `source_hash` seulement ; vide → SIMPLE 71 · EXCLUSIF 30 · ACCORD 18. Chemin du worker (push ciblé,
  dossier 1339004, ligne 12704:4117) : ACCORD aussi.
- Mise en ligne : au push du code, puis au run de nuit suivant (② fabrique, ③ reçoit). ⏰ Contrôle : compter
  dans Supabase les 119 (témoin du 27/10 : 119 vides).
- Retour arrière : `APP_REGISTRE_TYPE_APP=0` → au push suivant les 119 redeviennent vides.

### 11 quinquies. Correctif 7 — CODÉ le 27/10 (« vas-y » de Frédéric)

- **Cause** : 9 ventes entrées le 15/10 depuis Modelo (`importer_mandats_vente_absents.py`, origine `modelo`)
  ont leurs dates dans les colonnes de `app_mandat` mais **aucune version Hektor** (`versions_json` vide) ;
  le fabricant leur faisait une fiche vide → registre sans date ni type.
- **Correctif** : interrupteur `APP_REGISTRE_REPLI_DEPUIS_LIGNE` (allumé) ; la fiche de repli prend début, fin,
  clôture, type, mandants et note dans la ligne. Les 5 numéros sans rien (origine `annonce`) ne changent pas.
- **Essai hors ligne** : 24 584 lignes des deux côtés, mêmes identifiants, **9 lignes changent, aucune autre**
  (dates, type, note, historique, fiche détaillée ; `search_text` sur 2). ⚠ `mandat_type_source` affiche le type
  du classeur pour ces 9 (la colonne `type` de leur ligne vient du classeur, pas de Hektor).
- **Prérequis du correctif 5** : tout mandat ajouté depuis un classeur n'a pas de version Hektor.
- Retour arrière : `APP_REGISTRE_REPLI_DEPUIS_LIGNE=0`.

### 11 sexies. Correctif 5 — CODÉ le 27/10, NON ÉCRIT en base (accord attendu)

Décision de Frédéric (27/10) : **B** — les 518 recherches et les ventes dont le bien est connu entrent ;
les 99 ventes sans bien connu attendent ; locations et gestions exclues.

- `importer_mandats_recherche.py` lit en plus le registre légal 2014-2024 (`Ancien registre des mandat.csv`) :
  objet « recherche » seulement, réservés/annulés écartés.
- **Défaut trouvé et corrigé dans les deux portes** : les dates Modelo (UTC) étaient coupées à 10 caractères →
  **la veille**. `date_paris()` les ramène à Paris. Les 22 recherches et les 9 ventes posées le 15/10 sont réparées
  au passage (la porte des ventes peut désormais mettre à jour SES lignes au lieu de les refuser).
- `importer_mandats_vente_absents.py` retrouve le bien quand Hektor a renommé sa réf en numéro de mandat
  (18404 → annonce 61607, 18408 → 61615).
- **Essai complet sur une COPIE de phase2.sqlite** (vraie base intacte) : registre 24 584 → **25 104** lignes,
  **+520** (518 recherches sans bien + 18404 + 18408), **0 retirée, 0 sans date** ; 31 lignes existantes changent,
  **uniquement leurs dates (+1 jour)** — 17283 passe au 08/10/2024, comme le registre légal.
- Contacts des 518 : retrouvés pour 381 sur 556 (dont 227 par « homonymie levée »), 106 ambigus laissés vides,
  69 introuvables — la ligne existe quand même. 59 numéros refusés (déjà portés par un mandat sur une annonce).
- Restent hors champ : 18455 (dans le seul registre Hektor 2026, que la porte des ventes ne lit pas), 18500 (avenant),
  18383 et 10 autres ventes à bien inconnu (décision B).

#### ✅ ÉCRIT dans phase2.sqlite le 27/10 vers 16:00 (accord de Frédéric)

- Sauvegarde datée : table `app_mandat_avant_correctif5_20261027` (26 932 lignes), dans phase2.sqlite.
- Contrôle contre la sauvegarde : 26 932 → **27 452** lignes, **+520** (518 `registre_legal_2014_2024` RECHERCHE
  sans bien + 2 VENTE `modelo` 18404/18408), **0 disparue, 0 sans date**, toutes `present_in_hektor = 0`, ids
  dans la plage du run. **47 lignes existantes modifiées** : 31 dates (+1 jour : 22 recherches et 9 ventes du 15/10,
  ex. 17283 → 08/10/2024) et 16 recherches du registre 2026 dont seul `last_seen_at` bouge.
- Retour arrière : `DELETE FROM app_mandat WHERE origine='registre_legal_2014_2024'` + les deux ventes
  (`origine='modelo' AND numero_mandat IN ('18404','18408')`), puis les 31 dates depuis la sauvegarde.
  ⚠ Supabase les recevra par le push de nuit (upsert) : un retour arrière après la nuit devra aussi les retirer là-bas.
- ⏰ Après la nuit : Supabase `app_mandat` = 27 452 lignes ; registre affiché +520.

#### ⛔ 18455 : NE PAS L'AJOUTER — décision de Frédéric, 27/10 (« b »)

Registre légal Hektor 2026 : le 12/03/2026 (Ambert), même mandante, même bien (réf EM71125 = annonce 58908),
**18455 « non exclusif »** puis **18456 « exclusif »**. 18456 est chez nous (12/03/2026 → 11/06/2027).
18455 est tenu pour un **numéro abandonné le jour même** : trou connu et assumé au registre de l'app.
Ne pas relancer. (Le 15/10, il était classé « aucune référence » : la réf existe, c'est la décision qui le tient dehors.)

## 11. Fichiers

- **Détail ligne à ligne, toutes années** (19 908 écarts, nominatif, hors git) :
  `Projet/.tmp/ETUDE_CORRESPONDANCES_PAR_ANNEE_2026-10-27.csv`
  (colonnes : année, source, numéro, réf, écart, valeur classeur, valeur data, annonce)
- Registre Hektor 2026 ligne à ligne : `Projet/.tmp/CORRESPONDANCES_REGISTRE_2026_2026-10-27.csv`
- Audit complet, passes successives : `notice/AUDIT_REGISTRE_MANDATS_CLASSEURS_HISTORIQUE_2026-10-27.md`
- Scripts : `Projet/.tmp/audit_classeurs_2026-10-27/`
