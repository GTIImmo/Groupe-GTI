## Objet

Stabiliser le workflow `Demande de diffusion` et `Diffusion` autour d'un principe simple :

- l'acceptation Pauline rend le bien diffusable
- les passerelles par défaut du seul dossier accepté sont préparées
- la console `Diffusion` ne doit plus rendre un bien diffusable "par accident"
- le write-back Hektor ne doit plus remonter d'erreurs techniques brutes quand le problème réel est métier

## Corrections déjà appliquées

### Console Diffusion

- la console `Diffusion` n'essaie plus de basculer `diffusable`
- elle applique uniquement les passerelles
- l'affichage de la console repart de l'état lu par l'API Hektor
- les anciennes cibles mémorisées n'écrasent plus visuellement l'état lu
- le bouton d'action a été fusionné en un seul bouton :
  - `Enregistrer dans Hektor`

### Write-back Python

Dans `phase2/sync/hektor_diffusion_writeback.py` :

- ajout du root projet dans `sys.path` pour retrouver `hektor_pipeline`
- si aucune cible n'existe pour le dossier :
  - seed automatique des cibles par défaut avant application
- le seed par défaut n'utilise plus tout le catalogue writable
- le seed lit maintenant l'agence du dossier dans `app_view_generale`
- le seed alimente les cibles depuis une table de configuration locale :
  - `app_diffusion_agency_target`
- la table de configuration est créée automatiquement si elle n'existe pas
- les mappings d'agence par défaut sont semés automatiquement si absents
- relancer le seed remet aussi le dossier à plat sur les passerelles prévues pour son agence
- tentative `POST` d'abord sur :
  - `/Api/Passerelle/addAnnonceToPasserelle/`
  - `/Api/Passerelle/removeAnnonceToPasserelle/`
- fallback en `GET` seulement si le endpoint répond `405`
- normalisation des messages Hektor bruts

Dans `hektor_pipeline/common.py` :

- connexion SQLite durcie :
  - `timeout=30`
  - `PRAGMA busy_timeout=30000`

### Acceptation Pauline

Le flux local de dev existe maintenant :

- endpoint Vite local :
  - `/api/hektor-diffusion/accept`
- sous-commande Python :
  - `accept-request`

Ordre exécuté :

1. rendre le bien diffusable via `/Api/Annonce/Diffuse/`
2. relire l'annonce Hektor
3. seulement si `diffusable = 1` :
   - seed des passerelles par agence
   - application des passerelles
4. relire les passerelles Hektor
5. seulement après succès :
   - le front marque la demande `accepted`
   - le dossier passe en `diffusable = oui` dans l'application

## Intention cible

Le modèle métier visé est :

1. Pauline clique `Accepter`
2. la demande passe en `accepted`
3. le bien passe en `diffusable = oui`
4. les passerelles par défaut sont cochées pour ce seul dossier
5. Hektor doit ensuite revenir aligné
6. tant que Hektor n'est pas aligné :
   - l'interface peut signaler une attente
7. dès que Hektor revient aligné :
   - le message d'attente disparaît

## Paramétrage par agence

Le seed par défaut repose désormais sur :

- `agence_nom` du dossier
- une table locale `app_diffusion_agency_target`

Structure :

- `agence_nom`
- `portal_key`
- `hektor_broadcast_id`
- `is_active`

Exemple métier :

- `Groupe GTI Craponne-sur-Arzon`
  - `bienicidirect -> 5`
  - `leboncoinDirect -> 42`

Le dossier test :

- `app_dossier_id = 20124`
- `hektor_annonce_id = 61909`
- `agence_nom = Groupe GTI Craponne-sur-Arzon`

est maintenant bien ramené à :

- `bienicidirect = 5`
- `leboncoinDirect = 42`

## Ce qui reste à finaliser

### Nettoyage UX

Il reste à clarifier :

- la phrase exacte d'attente pour `diffusable`
- la phrase exacte d'attente pour les passerelles
- le moment exact où ces phrases disparaissent

## Commandes utiles

Compilation front :

```powershell
npx.cmd tsc -b
```

Compilation Python :

```powershell
.\.venv\Scripts\python.exe -m py_compile hektor_pipeline\common.py phase2\sync\hektor_diffusion_writeback.py
```

Re-seed local d'un dossier depuis son agence :

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py seed-default-targets --app-dossier-id 20124
```

Dry-run local ensuite :

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py apply-targets --app-dossier-id 20124 --dry-run
```

Test local du flux complet d'acceptation :

```powershell
.\.venv\Scripts\python.exe phase2\sync\hektor_diffusion_writeback.py accept-request --app-dossier-id 20124 --dry-run
```

Push complet Supabase :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py --full-rebuild --dossier-batch-size 50 --detail-batch-size 25 --work-item-batch-size 50 --filter-batch-size 50
```

Purge demandes de test :

```sql
delete from public.app_diffusion_request_event;
delete from public.app_diffusion_request;
```
