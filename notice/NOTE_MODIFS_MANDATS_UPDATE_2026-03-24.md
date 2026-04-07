# Note modifications mandats update - 24/03/2026

Date: 24/03/2026

## Contexte

Pendant l'analyse de la phase 1 / phase 2, un manque a ete confirme sur les `DetailMandat` bruts.

Constat observe:

- `6470` payloads bruts `mandat_detail` stockes
- `16332` annonces avec un `NO_MANDAT` mais sans `DetailMandat` brut rattache par croisement sur le numero de mandat

Le manque principal ne venait pas de `normalize_source.py` ni de `build_case_index.py`, mais de la collecte brute dans `sync_raw.py`.

## Modification apportee dans sync_raw.py

Fichier modifie:

- `sync_raw.py`

Correction appliquee:

- avant correction, le replay `MandatById` pour la ressource `mandats` repartait seulement des IDs trouves dans `ListMandat`
- apres correction, le replay `MandatById` repart de:
  - `ListMandat`
  - et `MandatsByIdAnnonce` quand `annonces` est inclus dans le run

Zone modifiee:

- bloc de `main()` appelant `sync_generic_details(...)` pour `resource_name == "mandats"`

Effet attendu:

- recuperer les `DetailMandat` visibles via la relation annonce -> mandat, meme s'ils ne remontent pas dans `ListMandat`
- ameliorer surtout le comportement du mode `update`
- permettre aussi un rattrapage cible sans purge via:
  - `annonces`
  - `mandats`

## Etat de normalize_source.py

Pas de modification apportee le 24/03/2026.

Rappel utile:

- `normalize_source.py` fusionne deja:
  - `ListMandat`
  - `MandatById`
  - `MandatsByIdAnnonce`
  - liens annonces issus de `NO_MANDAT`
  - liens annonces issus de `AnnonceById.mandats`

Conclusion:

- la logique de fusion mandat etait deja presente
- le manque etait en amont, au niveau du replay des details mandat

## Etat de build_case_index.py

Pas de modification apportee le 24/03/2026.

Rappel utile:

- `build_case_index.py` calcule `mandat_id` de dossier a partir:
  - des transactions quand elles portent un `hektor_mandat_id`
  - sinon du rattachement provenant de `hektor_mandat`
  - avec fallback sur le numero de mandat dans certains cas

Limite toujours a surveiller:

- si `hektor_mandat` reste incomplet, alors `case_dossier_source.mandat_id` peut rester nul
- dans ce cas, la phase 2 continue d'afficher `Sans mandat` meme si `NO_MANDAT` existe

## Commande de rattrapage retenue

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode full --resources annonces mandats --max-pages 0 --detail-limit 0 --mandat-date-start 2010-01-01 --mandat-date-end 2030-12-31
.\.venv\Scripts\python.exe normalize_source.py
.\.venv\Scripts\python.exe build_case_index.py
```

## Commande de suivi du run

```powershell
.\.venv\Scripts\python.exe sync_progress.py --watch 2
```

## Point de vigilance

Ce correctif ne garantit pas de recuperer des mandats totalement absents a la fois de:

- `ListMandat`
- `MandatsByIdAnnonce`

Il corrige le cas ou le mandat etait visible par relation annonce, mais jamais rejoue en `MandatById`.
