# Note correctif reconciliation `app_dossier` phase 2

Date: 2026-03-30

## Objet

Completer la chaine locale :

- phase 1 normalisee
- `case_dossier_source`
- phase 2 app

pour eviter le cumul de dossiers orphelins dans `app_dossier` lors des upgrades quotidiens.

## Constat

La reconciliation etait deja correcte sur :

- `normalize_source.py`
  - purge des annonces hors listing actif
  - purge des details / offres / compromis / ventes / broadcasts lies
- `build_case_index.py`
  - reconstruction complete de `case_dossier_source`

En revanche, `phase2/bootstrap_phase2.py` faisait seulement :

- insertion des nouveaux `app_dossier`
- mise a jour des `app_dossier` existants

Il ne supprimait pas :

- les `app_dossier` qui ne sont plus presents dans `hektor.case_dossier_source`

Consequence :

- la phase 2 locale pouvait conserver des dossiers orphelins
- les vues locales pouvaient encore les relire via `app_dossier`
- le cumul local n'etait donc pas completement elimine

## Correctif applique

Ajout d'une etape `reconcile_app_dossier()` au debut de :

- `phase2/bootstrap_phase2.py`

Cette etape :

1. compare `app_dossier` avec `hektor.case_dossier_source`
2. detecte les dossiers absents du perimetre `annonce_source_status = 'present'`
3. supprime les enregistrements lies dans :
   - `app_broadcast_action`
   - `app_blocker`
   - `app_followup`
   - `app_internal_status`
   - `app_note`
   - `app_work_item`
4. supprime ensuite les lignes orphelines de `app_dossier`

Puis le bootstrap standard rejoue :

- l'upsert des `app_dossier` valides
- la regeneration des `app_work_item` `mandat_diffusion`

## Effet attendu

Sur un upgrade quotidien phase 1 -> app :

- ajout : conserve
- modification : conserve
- suppression / sortie du perimetre : maintenant repercutee aussi dans `app_dossier`

Donc la chaine locale devient coherente de bout en bout.

## Commande quotidienne

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode update --resources annonces contacts mandats offres compromis ventes broadcasts --missing-only
.\.venv\Scripts\python.exe normalize_source.py
.\.venv\Scripts\python.exe build_case_index.py
.\.venv\Scripts\python.exe phase2\bootstrap_phase2.py
.\.venv\Scripts\python.exe phase2\refresh_views.py
.\.venv\Scripts\python.exe phase2\checks\run_quality_checks.py
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py --dossier-batch-size 50 --detail-batch-size 25 --work-item-batch-size 50 --filter-batch-size 50
.\.venv\Scripts\python.exe phase2\sync\push_hektor_directory_to_supabase.py
```

La synchro annuaire en fin de run alimente aussi :

- `app_user_directory`
- `app_agence_directory`

pour les futurs uploads et les modules publics comme RDV.

## Point de vigilance

Ce correctif traite la reconciliation locale phase 2.

Le script :

- `phase2/sync/push_upgrade_to_supabase.py`

a aussi ete ajuste pour calculer les `stale_ids` a chaque run en comparant :

- le stock distant `app_dossier_current`
- les `app_dossier` locaux

Donc les suppressions de dossiers ne dependent plus uniquement de `--full-rebuild`.

La vigilance restante concerne surtout :

- les details eventuellement residuels si un dossier reste present localement mais perd son detail
- les limites reseau / timeout Supabase deja documentees
