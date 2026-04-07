# Note sync Supabase execution

Date: 24/03/2026

## Objet

Documenter la synchronisation `phase2 -> Supabase` ajoutee apres la definition du schema V1 et du front React.

## Scripts concernes

- `phase2/sync/export_app_payload.py`
- `phase2/sync/push_to_supabase.py`

## Decision retenue

La sync ne pousse pas directement le schema interne de phase 2.

Elle pousse le contrat applicatif V1 :

- `meta`
- `summary`
- `dossiers`
- `work_items`

## Variables attendues

Dans l'environnement ou dans `.env` :

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## Fonctionnement

1. lecture du contrat local phase 2
2. creation d'une ligne `app_sync_run`
3. insertion du snapshot `app_summary_snapshot`
4. insertion par lots dans :
   - `app_dossier_v1`
   - `app_work_item_v1`

## Taille de lot

La sync est batchée.

Valeur par defaut :

- `500`

## Commandes utiles

Export local complet :

```powershell
.\.venv\Scripts\python.exe phase2\sync\export_app_payload.py --full
```

Sync Supabase complete :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_to_supabase.py
```

Sync Supabase en echantillon de test :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_to_supabase.py --sample-limit 200
```

## Point de securite

La sync utilise une `service role key`.

Donc :

- ne jamais exposer cette cle au front React
- ne jamais la mettre dans `VITE_*`
- la reserver au script de sync et aux usages serveur

## But atteint

Avec cette brique, la chaine cible devient :

1. phase 1 extrait
2. phase 2 consolide
3. `sync` pousse vers Supabase
4. React lit Supabase
