# Reprise phase 1 - 22/03/2026 update

Date: 22/03/2026

## Etat global retenu

La phase 1 est globalement stabilisee.

Points acquis :

- le bootstrap `ListAnnonces` a ete corrige
  - bootstrap stable en `sort=id` / `way=ASC`
- le parc annonces a ete reconstitue
- les details annonces ont ete rattrapes
- les cas commerce sans annonce source ont ete identifies proprement
- la couche diffusion a ete structuree pour la lecture actuelle et une future ecriture

## Etat de la base au moment de cette note

Tables consolidees :

- `hektor_annonce` : parc source courant
- `hektor_annonce_detail` : details annonce
- `hektor_mandat`
- `hektor_offre`
- `hektor_compromis`
- `hektor_vente`
- `case_dossier_source`

Cas metier isoles :

- `case_kind = 'transaction_commerce'`
- `annonce_source_status = 'present' | 'missing'`

Interpretation retenue :

- `missing + transaction_commerce` = cas metier reconnu
- ce n'est plus une anomalie brute de synchronisation

## Point contacts retenu apres verification API

Le comportement reel de l'API contacts sur l'instance a ete verifie le 22/03/2026.

Constat :

- le tri `sort=dateLastTraitement` est accepte par l'API
- mais les items de `ListContacts` ne renvoient pas `dateLastTraitement`
- les items renvoient bien `datemaj`
- sur plusieurs pages testees, l'ordre observe sur `datemaj` est coherent avec le tri demande

Decision de correction appliquee dans `sync_raw.py` :

- conserver `sort=dateLastTraitement` pour l'appel API
- utiliser `datemaj` comme horloge observable stockee localement
- comparer les contacts sur `datemaj`
- alimenter les curseurs contacts avec `datemaj`

## Cursors en base

Etat releve au moment de cette note :

- `annonce_cursor_active = 2026-03-21 10:47:22`
- `annonce_cursor_archived = 2026-03-20 15:43:53`
- `contact_cursor_active = 2026-03-22 08:39:12`
- `contact_cursor_archived = 2026-03-20 17:01:11`

Important :

- les curseurs contacts ont ete backfilles depuis le brut deja present en base
- cela evite de relire inutilement tout `ListContacts` comme un premier update vierge

## Couche diffusion retenue

Lecture :

- `hektor_broadcast`
- `hektor_broadcast_listing`
- `hektor_broadcast_portal`
- `hektor_annonce_broadcast_state`

Preparation de l'ecriture future :

- `hektor_annonce_broadcast_target`

Lecture metier a retenir :

- `state` = etat courant observe
- `target` = etat voulu a appliquer plus tard

## Run update quotidien

Commande quotidienne retenue :

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode update --resources annonces contacts mandats offres compromis ventes broadcasts; .\.venv\Scripts\python.exe normalize_source.py; .\.venv\Scripts\python.exe build_case_index.py
```

Parametrage quotidien retenu dans le code :

- `offre_recent_limit = 1000`
- `compromis_recent_limit = 1000`
- `vente_lookback_months = 12`

But :

- elargir la reprise quotidienne transactionnelle sans alourdir le lancement par une longue ligne d'arguments

Commande de suivi :

```powershell
.\.venv\Scripts\python.exe sync_progress.py --watch 2
```

## Run en cours au moment de cette note

Etat observe dans `sync_run` :

- run `#9`
- `status = running`
- debut : `2026-03-22T14:49:58Z`
- heartbeat : `2026-03-22T14:52:03Z`
- etape courante :
  - `current_step = listing`
  - `current_resource = compromis`
  - `current_endpoint = list_compromis_update`
  - `progress_done = 24`
  - `progress_total = 522`
  - `progress_unit = pages`

## Historique recent utile

- run `#8` :
  - `success`
  - sert de point stable recent
- run `#7` :
  - `abandoned`
  - ancien test update interromptu sur les contacts
- run `#6` :
  - `success`
  - rattrapage des `annonce_detail` manquants

## Fichiers de reference a relire en reprise

- `REPRISE_SYNC_2026-03-21.md`
- `REPRISE_API_PARAMS.md`
- `notice/TRANSACTION_COMMERCE_NOTE.md`
- `notice/BROADCAST_WRITE_MODEL_NOTE.md`

## Point de reprise si interruption

1. verifier le dernier `sync_run`
2. si le run `update` est encore `running`, le suivre avec :
   - `.\.venv\Scripts\python.exe sync_progress.py --watch 2`
3. si le run est termine :
   - verifier rapidement les compteurs
   - puis enchaine normalement :
     - `normalize_source.py`
     - `build_case_index.py`

## Regles a ne pas perdre

- ne pas confondre :
  - stock brut `raw_api_response`
  - tables sources consolidees
- `transaction_commerce` est un cas metier reconnu
- pour les contacts :
  - tri API = `dateLastTraitement`
  - horloge observable = `datemaj`
- pour la diffusion :
  - lecture actuelle = `state`
  - ecriture future = `target`
