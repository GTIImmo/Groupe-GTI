## Croisement utilisateur Supabase -> nego Hektor

Objectif :
- enrichir la carte utilisateur du header
- rapprocher `session.user.email` du `listNegos` Hektor
- afficher le nom nego et l'agence quand l'email correspond

Chaine mise a jour dans le repo :
- `build_case_index.py` expose deja `negociateur_email`
- `phase2/pipeline/view_generale.py` projette maintenant `negociateur_email`
- `phase2/sync/export_app_payload.py` conserve `negociateur_email` dans le payload dossier
- `phase2/sync/push_upgrade_to_supabase.py` pousse `negociateur_email` vers `app_dossier_current`
- front `apps/hektor-v1` lit ce champ pour enrichir la carte utilisateur

Patch SQL Supabase a appliquer :

```sql
alter table public.app_dossier_current
add column if not exists negociateur_email text;

alter table public.app_dossier_v1
add column if not exists negociateur_email text;
```

Si la vue `app_dossiers_current` n'expose pas encore le champ, la recreer en ajoutant `d.negociateur_email` dans les deux branches.

Commande ensuite :

```powershell
.\.venv\Scripts\python.exe phase2\refresh_views.py
```

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py --full-rebuild --dossier-batch-size 50 --detail-batch-size 25 --work-item-batch-size 50 --filter-batch-size 50
```

Controle SQL :

```sql
select commercial_nom, negociateur_email, agence_nom
from public.app_dossiers_current
where coalesce(trim(negociateur_email), '') <> ''
limit 20;
```

## Correctif daily sur les IDs nego manquants

Constat confirme sur la phase 1 brute :

- certaines annonces portent un `NEGOCIATEUR` absent de `listNegos`
- cause confirmee par Romain :
  - `listNegos` ne retourne que les comptes actifs / non expires
  - il faut completer via `GET /Api/Negociateur/getNegoById?id=<id>`

Correctif applique :

- `sync_raw.py`
  - detecte les IDs nego presents sur les annonces mais absents du stock courant `list_negos`
  - appelle ensuite `getNegoById` pour completer les fiches manquantes
- `normalize_source.py`
  - reconstruit `hektor_negociateur` a partir de :
    - `list_negos`
    - `nego_by_id`

Validation faite localement :

- avant correctif :
  - `3695` annonces avec `idnego` inconnu
- apres relance :
  - `0`

Commande de mise a jour complete jusqu'a l'app :

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode update --resources annonces contacts mandats offres compromis ventes broadcasts --missing-only
.\.venv\Scripts\python.exe normalize_source.py
.\.venv\Scripts\python.exe build_case_index.py
.\.venv\Scripts\python.exe phase2\bootstrap_phase2.py
.\.venv\Scripts\python.exe phase2\refresh_views.py
.\.venv\Scripts\python.exe phase2\checks\run_quality_checks.py
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py
```

Commande watch du run local :

```powershell
.\.venv\Scripts\python.exe sync_progress.py --watch 2
```
