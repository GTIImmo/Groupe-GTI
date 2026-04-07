# Note recreation projet Supabase

Date: 2026-03-28

## Objet

Documenter l'ordre exact pour supprimer l'ancien projet Supabase, en recreer un nouveau, puis remettre l'application en service proprement.

## Pourquoi cette option

Dans le contexte actuel :

- le SQL Editor Supabase timeout
- les suppressions REST massives timeout aussi
- repartir d'un projet vierge est plus simple qu'une purge lourde

## Fichiers de reference

Schema principal :

- `supabase/schema_v1.sql`

Patch workflow demandes diffusion :

- `supabase/patch_diffusion_request_workflow_2026-03-27.sql`

Patch couche `current` / upgrade Annonces :

- `supabase/patch_annonces_current_upgrade_2026-03-27.sql`

Notes utiles :

- `notice/NOTE_SCHEMA_SUPABASE_V1_REACT_2026-03-24.md`
- `notice/NOTE_SYNC_SUPABASE_EXECUTION_2026-03-24.md`
- `notice/NOTE_UPGRADE_ANNONCES_CURRENT_2026-03-27.md`
- `notice/NOTE_PERIMETRE_ANNONCES_ACTIVES_2026-03-28.md`

## Ordre recommande

### 1. Creer un nouveau projet Supabase

Recuperer ensuite :

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## 2. Charger le schema principal

Dans le SQL Editor du nouveau projet :

- executer `supabase/schema_v1.sql`

Ce schema cree notamment :

- les tables snapshot `Annonces`
- les tables `current` `Annonces`
- les tables `Mandats`
- les vues applicatives
- les policies RLS

## 3. Appliquer les patchs

### 3.1 Workflow diffusion

Executer :

- `supabase/patch_diffusion_request_workflow_2026-03-27.sql`

But :

- enrichir `app_diffusion_request`
- ajouter les champs admin / relance / motif

### 3.2 Upgrade `current` Annonces

Executer :

- `supabase/patch_annonces_current_upgrade_2026-03-27.sql`

But :

- activer la couche `current`
- ajouter `app_delta_run`
- faire lire l'app depuis `current` apres premier upgrade reussi

## 4. Mettre a jour `.env`

Dans `C:\Users\frede\Desktop\Projet\.env`, remplacer :

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

avec les valeurs du nouveau projet.

## 5. Refaire un full propre

Depuis `C:\Users\frede\Desktop\Projet` :

### 5.1 Full `Annonces`

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_to_supabase.py
```

Important :

- le payload `Annonces` est maintenant limite a :
  - annonces non archivees
  - `statut_annonce = 'Actif'`

Donc le full ne recharge plus tout l'ancien parc historique.

### 5.2 Flux `Mandats`

Par defaut, il n'y a plus de push Mandats obligatoire.

Le full `Annonces` alimente aussi :

- `app_mandat_current`
- `app_mandat_broadcast_current`

Ce qui suffit pour :

- `Liste des mandats`
- `Suivi des mandats`

Le script dedie reste disponible seulement en secours :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_mandat_to_supabase.py
```

## 6. Tester ensuite l'upgrade `Annonces`

Une fois le full termine :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py
```

Version prudente :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py --dossier-batch-size 50 --detail-batch-size 25 --work-item-batch-size 50 --filter-batch-size 50
```

## 7. Recharger le front

Si besoin :

```powershell
cd C:\Users\frede\Desktop\Projet\apps\hektor-v1
npm.cmd run dev
```

Puis navigateur :

- `http://127.0.0.1:5175`
- `Ctrl + F5`

## Resume ultra court

1. nouveau projet Supabase
2. `schema_v1.sql`
3. `patch_diffusion_request_workflow_2026-03-27.sql`
4. `patch_annonces_current_upgrade_2026-03-27.sql`
5. MAJ `.env`
6. `push_to_supabase.py`
7. `push_upgrade_to_supabase.py`

Option secours seulement :

8. `push_mandat_to_supabase.py`

## Point de vigilance

Si le nouveau projet doit aussi conserver les utilisateurs internes, il faudra recreer :

- les comptes auth
- les lignes `app_user_profile`

Le reset du projet Supabase ne conserve pas ces donnees.
