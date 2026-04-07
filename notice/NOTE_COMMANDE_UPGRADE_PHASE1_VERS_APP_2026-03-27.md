# Note commande upgrade phase 1 vers app

Date: 27/03/2026

## Objet

Conserver la chaine correcte pour faire une mise a jour `update` de la phase 1 jusqu'a l'application, avec la commande de suivi du run.

## Important

La note plus ancienne avec `--lookback-days` n'est plus alignee avec la version reelle de `sync_raw.py`.

La version actuelle du script supporte notamment :

- `--mode update`
- `--missing-only`
- `--mandat-recent-limit`
- `--offre-recent-limit`
- `--compromis-recent-limit`
- `--vente-lookback-months`
- `--update-max-pages`
- `--update-detail-limit`

Elle ne supporte pas :

- `--lookback-days`

## Commande watch

Dans un terminal separe, pour suivre le run local en direct :

```powershell
.\.venv\Scripts\python.exe sync_progress.py --watch 2
```

Version plus lente si besoin :

```powershell
.\.venv\Scripts\python.exe sync_progress.py --watch 5
```

Etat instantane sans watch :

```powershell
.\.venv\Scripts\python.exe sync_progress.py
```

## Chaine complete update phase 1 -> app

Depuis `C:\Users\frede\Desktop\Projet` :

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode update --resources annonces contacts mandats offres compromis ventes broadcasts --missing-only --mandat-recent-limit 500 --offre-recent-limit 1000 --compromis-recent-limit 1000 --vente-lookback-months 12 --update-max-pages 5 --update-detail-limit 200
.\.venv\Scripts\python.exe normalize_source.py
.\.venv\Scripts\python.exe build_case_index.py
.\.venv\Scripts\python.exe phase2\bootstrap_phase2.py
.\.venv\Scripts\python.exe phase2\refresh_views.py
.\.venv\Scripts\python.exe phase2\checks\run_quality_checks.py
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py
```

## Version courte conseilee

Si tu veux laisser les limites par defaut du script :

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode update --resources annonces contacts mandats offres compromis ventes broadcasts --missing-only
.\.venv\Scripts\python.exe normalize_source.py
.\.venv\Scripts\python.exe build_case_index.py
.\.venv\Scripts\python.exe phase2\bootstrap_phase2.py
.\.venv\Scripts\python.exe phase2\refresh_views.py
.\.venv\Scripts\python.exe phase2\checks\run_quality_checks.py
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py
```

## Ordre a retenir

1. `sync_raw.py --mode update`
2. `normalize_source.py`
3. `build_case_index.py`
4. `bootstrap_phase2.py`
5. `refresh_views.py`
6. `run_quality_checks.py`
7. `push_upgrade_to_supabase.py`
8. `push_mandat_to_supabase.py` seulement en secours

## Detail des 2 pushes Supabase

### 1. Upgrade vue Annonces

Commande :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py
```

Role :

- met a jour la couche `current` pour la vue `Annonces`
- compare les hashes locaux avec Supabase
- pousse seulement les differences detectees sur :
  - `app_dossier_current`
  - `app_dossier_detail_current`
  - `app_work_item_current`
  - `app_filter_catalog_current_store`
- journalise l'operation dans :
  - `app_delta_run`

Important :

- avant la premiere utilisation, il faut executer le patch SQL :
  - `supabase/patch_annonces_current_upgrade_2026-03-27.sql`

### 2. Push vues Mandats

Commande :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_mandat_to_supabase.py
```

Role :

- script de secours uniquement
- a utiliser seulement si tu veux forcer un rattrapage Mandats
- le flux normal `push_to_supabase.py` + `push_upgrade_to_supabase.py` alimente deja :
  - `app_mandat_current`
  - `app_mandat_broadcast_current`

### 3. Cas pratiques

Si tu veux mettre a jour seulement `Annonces` :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py
```

Si tu veux forcer seulement les vues `Mandats` :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_mandat_to_supabase.py
```

Si tu veux mettre a jour tout l'app :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py
```

Si un rattrapage Mandats est necessaire :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_mandat_to_supabase.py
```

## Usage recommande

1. lancer `sync_raw.py --mode update`
2. dans un autre terminal lancer :

```powershell
.\.venv\Scripts\python.exe sync_progress.py --watch 2
```

3. quand la phase 1 est finie, enchaîner :
   - `normalize_source.py`
   - `build_case_index.py`
   - phase 2
   - checks
   - push `Annonces`
   - push `Mandats` seulement si tu veux un rattrapage manuel

## Front React

Seulement si besoin de relancer le front :

```powershell
cd C:\Users\frede\Desktop\Projet\apps\hektor-v1
npm.cmd run dev
```

Puis recharger :

- `http://127.0.0.1:5175`
- `Ctrl + F5`
