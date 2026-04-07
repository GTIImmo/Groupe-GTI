# Note upgrade Annonces current

Date: 2026-03-27

## Objet

Mettre en place un vrai mode `upgrade` pour la vue `Annonces`, distinct du `push_to_supabase.py` snapshot complet.

## Principe

Le nouveau flux ne pousse plus un nouveau `sync_run` snapshot a chaque fois.

Il :

- lit le payload local complet phase 2
- compare les hashes avec les tables `current`
- upsert seulement les dossiers modifies
- upsert seulement les details modifies
- remplace les work items uniquement pour les dossiers impactes
- reconstruit le catalogue de filtres courant
- journalise l'operation dans `app_delta_run`

## Tables ajoutees

- `app_dossier_current`
- `app_dossier_detail_current`
- `app_work_item_current`
- `app_filter_catalog_current_store`
- `app_delta_run`

## Vues basculees

Les vues lues par l'app gardent leur nom :

- `app_dossiers_current`
- `app_dossier_details_current`
- `app_work_items_current`
- `app_filter_catalog_current`

Mais elles lisent maintenant :

- les tables `current` si un `app_delta_run` `completed` existe pour `annonces_current`
- sinon le dernier snapshot classique `app_latest_sync_run`

Donc :

- avant premier upgrade reussi : l'app reste sur le snapshot historique
- apres premier upgrade reussi : l'app lit le stock courant `current`

## Fichiers ajoutes

- script upgrade :
  - `phase2/sync/push_upgrade_to_supabase.py`
- patch SQL :
  - `supabase/patch_annonces_current_upgrade_2026-03-27.sql`

## Commandes

### 1. Appliquer le patch SQL

Dans Supabase SQL Editor :

- executer `supabase/patch_annonces_current_upgrade_2026-03-27.sql`

### 2. Lancer l'upgrade Annonces

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py
```

### 3. Forcer un rebuild complet des tables current si besoin

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py --full-rebuild
```

## Batch sizes retenus

- dossiers : `100`
- details : `50`
- work items : `100`
- filtres : `100`

Le detail reste volontairement plus petit a cause des timeouts Supabase.

## Difference avec les autres scripts

### Snapshot lourd historique

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_to_supabase.py
```

Role :

- cree un nouveau `sync_run`
- republie un snapshot complet

### Upgrade courant Annonces

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py
```

Role :

- met a jour le stock courant sans creer de nouveau snapshot

### Flux Mandats / Diffusion

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_mandat_to_supabase.py
```

Role :

- script de secours uniquement
- utile si on veut forcer un rattrapage Mandats isole
- le flux normal `push_to_supabase.py` + `push_upgrade_to_supabase.py` maintient deja :
  - `app_mandat_current`
  - `app_mandat_broadcast_current`

## Limite actuelle

Le script est un vrai mode `current` avec comparaison de hashes, mais pas encore un delta detecte directement depuis la phase 1.

Autrement dit :

- il compare l'etat local phase 2 courant avec l'etat `current` distant
- il pousse seulement les differences detectees

La prochaine etape plus fine serait :

- ne construire localement que les dossiers impactes par la phase 1
