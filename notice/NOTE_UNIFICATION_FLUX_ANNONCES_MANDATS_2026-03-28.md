# Note unification flux Annonces / Mandats

Date: 2026-03-28

## Objet

Figer la decision de fonctionnement stable apres recreation du projet Supabase.

## Decision retenue

Les vues :

- `Annonces`
- `Liste des mandats`
- `Suivi des mandats`

restent conservees dans le front.

En revanche, le flux principal retenu pour l'alimentation quotidienne devient :

- `phase2/sync/push_to_supabase.py`
- `phase2/sync/push_upgrade_to_supabase.py`

Le script :

- `phase2/sync/push_mandat_to_supabase.py`

ne devient plus obligatoire dans le run normal.

## Ce que fait maintenant le push principal

Le push principal `Annonces` alimente :

- les snapshots `Annonces`
- la couche `current` `Annonces`
- `app_mandat_current`
- `app_mandat_broadcast_current`

Donc :

- les vues Mandats peuvent continuer a lire leurs tables dediees
- sans exiger un push Mandats separe dans le run quotidien

## Ce qui reste a part

La table :

- `app_diffusion_request`

reste une table metier applicative.

Elle n'est pas reconstruite par la phase 2.

## Procedure quotidienne recommandee

Depuis `C:\Users\frede\Desktop\Projet` :

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode update --resources annonces contacts mandats offres compromis ventes broadcasts --missing-only
.\.venv\Scripts\python.exe normalize_source.py
.\.venv\Scripts\python.exe build_case_index.py
.\.venv\Scripts\python.exe phase2\bootstrap_phase2.py
.\.venv\Scripts\python.exe phase2\refresh_views.py
.\.venv\Scripts\python.exe phase2\checks\run_quality_checks.py
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py --dossier-batch-size 50 --detail-batch-size 25 --work-item-batch-size 50 --filter-batch-size 50
```

## Cas de secours uniquement

Utiliser :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_mandat_to_supabase.py
```

seulement si :

- un rattrapage Mandats isole est souhaite
- ou si on veut recharger explicitement `app_mandat_current` / `app_mandat_broadcast_current`

## Etat du front

Le front reste stable :

- `Annonces` lit `app_dossiers_current`
- `Liste des mandats` lit `app_mandats_current`
- `Suivi des mandats` lit `app_mandats_current`
- le detail passerelles lit `app_mandat_broadcasts_current`

La difference est uniquement :

- ces tables Mandats sont maintenues par le flux principal
- et non plus obligatoirement par un push dedie
