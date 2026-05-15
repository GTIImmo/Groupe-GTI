# Note projet - modification d'annonce Hektor depuis l'app

Date : 2026-05-15

## Objectif

Préparer la modification d'une annonce Hektor depuis l'application en ligne, sans exposer Hektor au front.

Le principe reste identique aux documents, créations, suppressions et mandants :

App en ligne -> Supabase job -> PC worker local -> Hektor Console -> sync locale/Supabase -> App en ligne

## Ce qui est ajouté

### Supabase

Patch appliqué :

- `supabase/patch_console_update_annonce_fields_2026-05-15.sql`

Ce patch ajoute le type de job :

- `update_hektor_annonce_fields`

Et la fonction RPC :

- `public.app_console_create_update_annonce_job(target_app_dossier_id, target_hektor_annonce_id, update_fields, update_priority)`

Sécurité :

- `admin` : peut créer ce job.
- `manager` : peut créer ce job.
- `commercial` : peut créer ce job uniquement sur un dossier accessible selon les règles agence/dossier existantes.

### Worker local

Fichier modifié :

- `Console/console_job_worker.js`

Nouveau handler :

- `handleUpdateHektorAnnonceFields`

Le worker se place d'abord dans le bon contexte négociateur Hektor avec `ensureHektorExecutionContext`, comme pour l'upload document et l'association mandant.

Champs supportés dans cette première version :

- `title` : titre du texte principal Hektor
- `description` : corps du texte principal Hektor
- `price` : prix public Hektor
- `net_seller_price` : prix net vendeur
- `surface` : surface habitable
- `carrez_surface` : surface Carrez
- `room_count` : nombre de pièces
- `bedroom_count` : nombre de chambres

Après sauvegarde Hektor, le worker lance la synchronisation immédiate :

- `phase2/sync/refresh_single_annonce.py --id-annonce ...`
- `build_case_index.py`
- `phase2/bootstrap_phase2.py`
- `phase2/refresh_views.py`
- `phase2/sync/push_upgrade_to_supabase.py`

Cela évite d'attendre l'upload quotidien pour revoir l'annonce modifiée dans l'app.

### Front/API

Fichiers modifiés :

- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/types.ts`

Fonction ajoutée côté front :

- `createUpdateHektorAnnonceFieldsJob(...)`

Cette fonction crée le job Supabase via la RPC sécurisée.

## Endpoints Hektor identifiés

### Texte principal

Lecture formulaire :

- `GET /admin/xmlrpc.php?mode=chargeAnnonceText&modeText=editer&typeText=principal&fromCallback=false&idann={id}&lang=fr`

Sauvegarde :

- `POST /admin/xmlrpc.php`
- `mode=annonce-update_infos_textes`
- `idann={id}`
- `titre=...`
- `corps=...`
- `idModule=0`

### Pièces, chambres, surfaces

Lecture formulaire :

- `GET /admin/xmlrpc.php?mode=ihmChargeGroupe&idAnnonce={id}&group=ag_interieur&consultMode=editer&ajax=ajax`

Sauvegarde :

- `POST /admin/xmlrpc.php`
- `mode=update_annonce_MEF`
- `idann={id}`
- `MEFgroup=ag_interieur`

Champs confirmés :

- `nbpieces`
- `NB_CHAMBRES`
- `surfappart`
- `SURF_CARREZ`

### Prix

Lecture formulaire :

- `GET /admin/xmlrpc.php?mode=ihmChargeGroupe_MandatPrix&idAnnonce={id}&group=mandat_infofi&consultMode=editer&ajax=ajax`

Sauvegarde :

- `POST /admin/xmlrpc.php`
- `mode=update_annonce_MEF`
- `idann={id}`
- `MEFgroup=mandat_infofi`

Champs confirmés :

- `prix`
- `PRIXNETVENDEUR`

## Test réalisé

Annonce test :

- `62243`
- dossier Hektor : `V480062243`
- contexte négociateur Hektor : `48`

Job de test :

- `b9419ff7-0681-4012-b14a-869fd41f4add`

Résultat :

- job `done`
- Hektor a confirmé `result = 1`
- sync immédiate terminée
- relecture Hektor confirmée :
  - `nbpieces = 1`
  - `NB_CHAMBRES = 1`
  - `surfappart = 12`
  - `title = TEST CODEX modification depuis app`

## Limites volontaires de cette première passe

Non activés pour l'instant :

- ville
- code postal
- adresse complète avancée
- type de bien
- statut Hektor
- offre/type transaction

Raison : ces champs utilisent des listes, autocomplete ou effets de bord Hektor plus sensibles. Ils doivent être capturés et testés séparément avant d'être proposés dans l'app.

## Important

Cette modification ne change pas le mécanisme d'upload document existant.

Les handlers existants restent séparés :

- `upload_document_to_hektor`
- `delete_document_from_hektor`
- `link_hektor_mandant`
- `create_hektor_draft_annonce`
- `delete_hektor_annonce`

Le nouveau handler ne s'exécute que pour :

- `update_hektor_annonce_fields`
