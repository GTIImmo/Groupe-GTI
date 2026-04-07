# Note commande mise a jour complete

Date: 25/03/2026

## Objet

Conserver la chaine de commandes exacte pour remettre a jour tout le projet :

- phase 1
- normalisation
- phase 2
- checks
- sync Supabase
- front React

## Resume simple

Ordre retenu :

1. sync brut API
2. normalisation
3. bootstrap phase 2
4. refresh des vues phase 2
5. checks qualite
6. sync Supabase
7. front React si besoin

## Commandes

### 1. Update brut API

```powershell
.\.venv\Scripts\python.exe sync_raw.py
```

Role :

- recupere les donnees brutes depuis l'API Hektor
- alimente la couche raw locale

### 2. Normalisation

```powershell
.\.venv\Scripts\python.exe normalize_source.py
```

Role :

- transforme le brut en tables normalisees exploitables
- alimente `data/hektor.sqlite`

### 3. Bootstrap phase 2

```powershell
.\.venv\Scripts\python.exe phase2\bootstrap_phase2.py
```

Role :

- met a jour `app_dossier`
- regenere les `app_work_item` du workflow `mandat_diffusion`
- initialise / met a jour `app_internal_status`

En clair :

- construit la base metier interne de la phase 2
- prepare les dossiers et la file de travail

### 4. Refresh des vues phase 2

```powershell
.\.venv\Scripts\python.exe phase2\refresh_views.py
```

Role :

- recalcule `app_view_generale`
- recalcule `app_view_demandes_mandat_diffusion`

En clair :

- construit les vues de lecture metier a partir de la base phase 2

### 5. Checks qualite

```powershell
.\.venv\Scripts\python.exe phase2\checks\run_quality_checks.py
```

Role :

- controle la coherence de la phase 2
- genere un rapport dans `phase2/docs/RAPPORT_QUALITE_PHASE2.md`

### 6. Sync vers Supabase

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_to_supabase.py
```

Role :

- pousse le contrat applicatif V1 vers Supabase
- met a jour :
  - `app_sync_run`
  - `app_summary_snapshot`
  - `app_dossier_v1`
  - `app_work_item_v1`

### 7. Front React

Seulement si le serveur n'est pas deja lance :

```powershell
cd C:\Users\frede\Desktop\Projet\apps\hektor-v1
npm.cmd run dev
```

Puis recharger le navigateur avec :

- `Ctrl + F5`

## Nombre de commandes

### Mise a jour complete metier + Supabase

- `6 commandes`

### Avec relance du front React

- `7 commandes`

## Chaine complete a retenir

```powershell
.\.venv\Scripts\python.exe sync_raw.py
.\.venv\Scripts\python.exe normalize_source.py
.\.venv\Scripts\python.exe phase2\bootstrap_phase2.py
.\.venv\Scripts\python.exe phase2\refresh_views.py
.\.venv\Scripts\python.exe phase2\checks\run_quality_checks.py
.\.venv\Scripts\python.exe phase2\sync\push_to_supabase.py
```

## Point important

Pour la nouvelle application React / Supabase :

- il n'est plus necessaire de regenerer les anciens exports HTML

Donc :

- `phase2/export_mini_app_html.py` : non necessaire pour l'app React
- `phase2/export_vue_generale_html.py` : non necessaire pour l'app React

## Regle memoire

- `bootstrap_phase2` construit la base metier interne
- `refresh_views` construit les vues de lecture
