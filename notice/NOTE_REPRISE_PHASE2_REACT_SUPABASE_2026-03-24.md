# Note reprise phase 2 React Supabase

Date: 24/03/2026

## Objet

Figer l'etat du chantier au moment ou :

- la phase 2 a ete re-rangee
- le socle `pipeline / rules / checks / sync` a ete pose
- le schema Supabase V1 a ete defini
- le squelette React V1 a ete cree et build

Cette note sert de point de reprise direct.

## Etat atteint

### 1. Phase 2 re-organisee

La phase 2 n'est plus pensee comme un export HTML monolithique.

Organisation actuelle :

- `phase2/pipeline`
- `phase2/rules`
- `phase2/checks`
- `phase2/sync`
- `phase2/docs`
- `phase2/legacy_front`

Le front HTML historique reste present pour reference, mais n'est plus la cible technique.

### 2. Regles et vues decouplees

Les statuts et fragments SQL ont ete sortis de `refresh_views.py`.

Fichiers cle :

- `phase2/rules/status_rules.py`
- `phase2/rules/sql_fragments.py`
- `phase2/pipeline/view_common.py`
- `phase2/pipeline/view_demandes_mandat_diffusion.py`
- `phase2/pipeline/view_generale.py`
- `phase2/refresh_views.py`

`refresh_views.py` est maintenant un orchestrateur court.

### 3. Checks de coherence en place

Une premiere couche de controle qualite est disponible.

Fichiers :

- `phase2/checks/quality_checks.py`
- `phase2/checks/run_quality_checks.py`

Rapport genere :

- `phase2/docs/RAPPORT_QUALITE_PHASE2.md`

Constats importants au moment de cette note :

- `missing_titles = 0`
- `view_generale_without_dossier = 0`
- `demandes_without_view_generale = 0`
- `null_statut_global = 15332`
- `archive_actif_without_statut = 15078`
- `sans_mandat_count = 31683`

Lecture retenue :

- les titres vides sont corriges
- la coherence entre vues est bonne
- le gros sujet restant est la qualite source Hektor sur les archives / statuts et les collisions no_mandat / id mandat

### 4. Contrat sync V1 defini

La phase 2 produit maintenant un contrat de sortie local pour la future app.

Fichiers :

- `phase2/sync/export_app_payload.py`
- `phase2/docs/APP_PAYLOAD_V1_SAMPLE.json`
- `notice/NOTE_COUCHE_SYNC_PHASE2_REACT_SUPABASE_2026-03-24.md`

Contrat V1 :

- `meta`
- `summary`
- `dossiers`
- `work_items`

### 5. Schema Supabase V1 defini

Le schema cible de la V1 React est pret.

Fichiers :

- `supabase/schema_v1.sql`
- `notice/NOTE_SCHEMA_SUPABASE_V1_REACT_2026-03-24.md`

Tables principales :

- `app_user_profile`
- `app_sync_run`
- `app_summary_snapshot`
- `app_dossier_v1`
- `app_work_item_v1`

Vues principales :

- `app_dashboard_v1`
- `app_dossiers_current`
- `app_work_items_current`

### 6. Squelette React V1 cree

Le front de depart a ete cree dans :

- `apps/hektor-v1`

Points importants :

- React + Vite + TypeScript
- lecture ciblee sur Supabase
- fallback mock local si Supabase n'est pas configure
- build Vite valide

Fichiers cle :

- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/lib/supabase.ts`
- `apps/hektor-v1/src/lib/mockData.ts`
- `apps/hektor-v1/src/styles.css`
- `notice/NOTE_SQUELETTE_REACT_V1_2026-03-24.md`

### 7. Sync Supabase preparee

Le script de push vers Supabase est ecrit mais n'a pas encore ete execute faute de credentials.

Fichiers :

- `phase2/sync/push_to_supabase.py`
- `notice/NOTE_SYNC_SUPABASE_EXECUTION_2026-03-24.md`

Variables attendues :

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## Commandes utiles de reprise

### Recalcul phase 2

```powershell
.\.venv\Scripts\python.exe phase2\refresh_views.py
```

### Rapport qualite

```powershell
.\.venv\Scripts\python.exe phase2\checks\run_quality_checks.py
```

### Export payload local

```powershell
.\.venv\Scripts\python.exe phase2\sync\export_app_payload.py --limit 200
.\.venv\Scripts\python.exe phase2\sync\export_app_payload.py --full
```

### Front React

```powershell
cd apps\hektor-v1
npm.cmd install
npm.cmd run build
```

### Sync Supabase

Test echantillon :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_to_supabase.py --sample-limit 200
```

Run complet :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_to_supabase.py
```

## Point bloqueur actuel

Le seul vrai bloqueur de passage a la suite applicative est :

- absence de `SUPABASE_URL`
- absence de `SUPABASE_SERVICE_ROLE_KEY`

Tant que ces variables ne sont pas renseignees, la sync reelle vers Supabase ne peut pas etre executee.

## Prochaine etape recommandee

Ordre conseille pour reprendre :

1. creer le projet Supabase
2. charger `supabase/schema_v1.sql`
3. renseigner `SUPABASE_URL` et `SUPABASE_SERVICE_ROLE_KEY`
4. lancer une sync test `--sample-limit 200`
5. verifier les vues :
   - `app_dashboard_v1`
   - `app_dossiers_current`
   - `app_work_items_current`
6. brancher le front React sur les vraies donnees
7. ajouter ensuite :
   - login
   - filtres
   - fiche dossier

## Decision de fond a retenir

La trajectoire retenue n'est plus :

- phase 2 -> export HTML -> app

La trajectoire retenue est :

- phase 1 extrait
- phase 2 consolide
- sync pousse vers Supabase
- React lit Supabase
