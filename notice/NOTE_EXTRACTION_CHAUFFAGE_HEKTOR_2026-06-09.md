# Note extraction chauffage Hektor - 2026-06-09

## Objectif

Recuperer rapidement les lignes chauffage absentes de l'API Hektor `AnnonceById`, sans relancer l'extraction console complete.

La source principale reste l'API Hektor. Ce correctif ajoute seulement une lecture console ciblee du groupe `equipements`.

Endpoint lu par annonce :

`/admin/xmlrpc.php?mode=ihmChargeGroupe&idAnnonce=<ID>&group=equipements&consultMode=editer&ajax=ajax`

Les endpoints documents ne sont pas appeles.

## Fichiers

- `Console/extract_hektor_chauffage_only.js` : lit uniquement le groupe `equipements` et parse les tables `chauffageExist...`.
- `phase2/sync/sync_hektor_chauffages.py` : orchestre les lots, gere le cache local, verifie les jobs console et stoppe en cas de vrai 403.

## Stockage local

Cache dedie dans `data/hektor.sqlite` :

`hektor_annonce_chauffage_detail`

Colonnes principales :

- `hektor_annonce_id`
- `status`
- `chauffage_json`
- `source_hash`
- `detail_synced_at`
- `extracted_at`
- `storage_state_path`
- `forbidden403`
- `elapsed_ms`
- `error`

## Injection app

`phase2/sync/export_app_payload.py` injecte le cache dedie dans le meme champ que l'app utilise deja :

- `chauffage_console_json`

Les champs de suivi suivants sont aussi disponibles dans le payload detail :

- `chauffage_console_status`
- `chauffage_console_extracted_at`

Si le cache chauffage dedie et le cache console complet existent, le cache chauffage dedie prend le dessus pour `chauffage_console_json`.

## Run quotidien

`run_full_pipeline.ps1` lance le delta chauffage leger par defaut avant le push Supabase.

Parametres par defaut :

- scope : `current`
- limite : `50`
- pause entre annonces dans un lot : `0.5` seconde
- taille de lot : `50`
- pause entre lots : `30` secondes
- session : `Console/sessions/storage_state_admin.json`
- rafraichissement session si expiree : active par defaut

Pour desactiver l'etape :

`-SkipHektorChauffage`

## Commandes

Controle sans appel Hektor :

```powershell
.\.venv\Scripts\python.exe phase2\sync\sync_hektor_chauffages.py --dry-run --scope current --limit 10
```

Petit test reel :

```powershell
.\.venv\Scripts\python.exe phase2\sync\sync_hektor_chauffages.py --scope current --limit 5 --force --delay-seconds 0.5 --batch-size 5 --batch-pause-seconds 0 --refresh-session-on-expired
```

Rattrapage prudent :

```powershell
.\.venv\Scripts\python.exe phase2\sync\sync_hektor_chauffages.py --scope all --limit 500 --delay-seconds 0.5 --batch-size 100 --batch-pause-seconds 60 --refresh-session-on-expired
```

Avec ces valeurs, le quotidien traite 50 annonces courantes en environ 1 minute selon le temps de reponse Hektor. Le rattrapage reste volontairement plus large : 500 annonces par vague, avec des lots de 100 et des pauses de 60 secondes.

Push Supabase apres extraction :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py --all-local-current --skip-stale-deletes --detail-batch-size 25 --dossier-batch-size 50 --work-item-batch-size 50 --filter-batch-size 50
```

## Securite

- verification des jobs console `pending/running` avant appel Hektor ;
- stop immediat si Hektor renvoie un vrai 403 ;
- pas de bascule negociateur ;
- pas de lecture documents ;
- cache rejoue seulement si absent, force, en erreur/stale ou si la source API a change.
