# Note correctif creation annonce Hektor - 2026-05-15

## Objectif

Remplacer le comportement de creation d'annonce Hektor depuis l'app.

Avant le correctif, le worker Console utilisait le bouton/fonction Hektor :

```text
saveBrouillon()
```

Ce flux creait une annonce Console avec :

```text
isDraft = true
```

Apres correction, le worker utilise le bouton/fonction Hektor :

```text
saveAndQuitte()
```

Ce flux correspond au bouton Console :

```text
Enregistrer et terminer
```

Le but est de creer directement une annonce non brouillon, visible comme annonce Hektor classique, sans la diffuser automatiquement.

## Fichiers modifies

```text
Console/console_job_worker.js
apps/hektor-v1/src/App.tsx
```

## Detail du correctif worker

Dans `Console/console_job_worker.js`, la creation Playwright attend maintenant :

```text
window.saveAndQuitte
```

Puis execute :

```text
window.saveAndQuitte()
```

La verification GraphQL ne cherche plus une annonce brouillon. Elle confirme maintenant une nouvelle annonce :

```text
isArchived != true
isDraft != true
```

Les logs techniques utilisent maintenant l'etape :

```text
hektor_annonce
```

avec le message :

```text
Annonce Hektor finalisee confirmee par GraphQL
```

## Point important sur le nom du job

Le type de job Supabase reste actuellement :

```text
create_hektor_draft_annonce
```

C'est un nom technique historique conserve volontairement pour eviter une migration SQL immediate et risquee.

Depuis le correctif du 2026-05-15, ce nom ne signifie plus que le worker cree un brouillon.

Comportement reel actuel :

```text
create_hektor_draft_annonce
=> worker Console
=> contexte negociateur Hektor
=> page ajout annonce
=> saveAndQuitte()
=> annonce Hektor creee en non-brouillon
```

Une future migration pourra renommer proprement le job en :

```text
create_hektor_annonce
```

mais ce n'est pas obligatoire pour le fonctionnement.

## Detail du correctif app

Les libelles visibles dans l'app ont ete corriges pour eviter la confusion :

```text
Nouveau brouillon annonce -> Nouvelle annonce Hektor
Creer le brouillon -> Creer l annonce
Brouillon seulement -> Creation sans diffusion
```

Le formulaire precise maintenant que la creation se fait dans le contexte negociateur selectionne, sans diffusion automatique.

## Regle de contexte Hektor pour les ecritures

Toute ecriture metier envoyee a Hektor depuis l'app doit etre executee avec le contexte Hektor du negociateur concerne.

Regle retenue :

```text
commercial connecte dans l'app
=> utiliser son acces negociateur Hektor

admin / manager connecte dans l'app
=> choisir le negociateur Hektor cible dans l'app
=> executer l'action dans ce contexte negociateur
```

Cette regle concerne notamment :

```text
creation annonce
modification annonce
ajout / association mandant
modification contact
upload document Hektor
suppression document Hektor
```

Exception volontaire :

```text
suppression annonce Hektor
=> action administrative
=> retour en session ADMIN Hektor obligatoire
```

Correctif worker applique :

- les ecritures creation annonce, upload document et suppression document exigent maintenant un contexte negociateur resolu ;
- si le worker ne sait pas determiner le `idUser` Hektor cible, le job passe en erreur au lieu d'utiliser par accident la session Hektor courante ;
- les futurs jobs de modification annonce / contact devront appeler le meme garde-fou `ensureHektorExecutionContext(..., { required: true })`.

## Test effectue

Job Supabase de test :

```text
id = f3695f65-896b-4244-8491-4c29cb474fcc
job_type = create_hektor_draft_annonce
payload test = test_codex_save_and_finish
hektor_user_id = 48
agence = Groupe GTI Firminy
```

Le worker a d'abord detecte une session Hektor invalide, a relance automatiquement Playwright login, puis a retente la commande.

Resultat worker :

```text
status = done
hektor_annonce_id = 62243
wizard_id = 62243
folder_number = V480062243
is_draft = false
is_broadcasted = false
is_valid = false
created_at_hektor = 2026-05-15T12:12:35
```

Verification API Hektor classique `AnnonceById` :

```text
hektor_annonce_id = 62243
NO_DOSSIER = V480062243
statut.id = 2
statut.name = Actif
archive = 0
diffusable = 0
NO_MANDAT = vide
prix = 0
surface = 0
```

Conclusion du test :

```text
OK - la creation depuis le worker ne produit plus un brouillon.
OK - l'annonce ressort cote API Hektor comme Actif.
OK - la diffusion reste inactive.
OK - la validation reste inactive.
```

## Correctif complementaire : apparition immediate dans l'app

Apres confirmation GraphQL de la creation Hektor, le worker anticipe maintenant la prochaine synchronisation quotidienne.

Il lance automatiquement la mini-chaine locale suivante :

```text
phase2/sync/refresh_single_annonce.py --id-annonce {hektor_annonce_id}
build_case_index.py
phase2/bootstrap_phase2.py
phase2/refresh_views.py
phase2/sync/push_upgrade_to_supabase.py
```

Objectif :

```text
creation annonce dans l'app
=> creation Hektor
=> refresh local API Hektor cible
=> recalcul Phase 2
=> push delta Supabase
=> annonce visible dans l'app sans attendre la sync quotidienne
```

Les logs du job utilisent l'etape :

```text
hektor_annonce_sync
```

Le resultat du job contient maintenant :

```text
immediate_sync.status = done | error | skipped
```

Important : cette sync immediate est volontairement non bloquante pour eviter une double creation.

Si Hektor cree bien l'annonce mais que le refresh/push Supabase echoue, le job reste termine avec l'id Hektor et `immediate_sync.status = error`. Il ne faut pas relancer automatiquement le job de creation, car cela pourrait creer une deuxieme annonce. Dans ce cas, relancer seulement la sync ciblee ou la sync quotidienne.

## Test sync immediate

Un test complementaire a cree l'annonce :

```text
hektor_annonce_id = 62244
folder_number = V480062244
job = 93163a51-fd19-44ec-9f4b-475d90d71409
```

La creation Hektor, `refresh_single_annonce`, `build_case_index`, `phase2/bootstrap_phase2.py` et `phase2/refresh_views.py` ont reussi.

Le premier essai de push Supabase a echoue car le script enfant Python recevait `VITE_SUPABASE_URL`, mais pas `SUPABASE_URL`. Le worker a ete corrige pour transmettre explicitement :

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
```

a tous les scripts Python lances par la sync immediate.

## Limites connues

Le formulaire historique ouvrait le wizard et validait le type par defaut `Appartement`.

Les champs libres transmis dans le payload, par exemple titre, ville, prix ou surface, sont conserves dans le resultat de job mais ne sont pas encore injectes dans le wizard Hektor.

L'annonce creee est donc une base Hektor active/non brouillon a completer ensuite dans Hektor ou dans un futur flux d'enrichissement.

## Correctif complementaire - 2026-05-16 : creation HTTP directe

Le worker tente maintenant la creation Hektor sans ouvrir Playwright.

Flux prioritaire :

```text
GET  /admin/xmlrpc.php?mode=ajoutebien&offredem=0&idType=2&statutAnnonce=2
POST /admin/xmlrpc.php
     mode=ajoutebien_wizardBien
     offredem=0
     idType=2
     statutAnnonce=2
     idann={idannWizard}
     programme_neuf=0
GET  /admin/xmlrpc.php?mode=upval&champ=etatAnnonce&val=1&id={idannWizard}
GET  /admin/xmlrpc.php?mode=upval&champ=diffusable&val=0&id={idannWizard}
GET  /admin/xmlrpc.php?mode=upval&champ=partage&val=0&id={idannWizard}
```

Objectif :

```text
creation annonce app
=> contexte negociateur Hektor
=> commandes HTML directes
=> annonce active/non brouillon
=> diffusion desactivee
```

Playwright reste uniquement en secours si la commande directe echoue avant qu'un `idannWizard` soit cree. Si Hektor a deja cree un identifiant annonce et qu'une etape suivante echoue, le worker ne relance pas Playwright afin d'eviter une double creation.

Point separe : le changement de contexte negociateur peut encore utiliser Playwright en secours si l'autologin HTTP Hektor ne renvoie pas un token verifiable. Dans ce cas Playwright sert uniquement a prendre l'identite Hektor du negociateur, puis la creation annonce reste executee par commandes HTTP directes.

Correction d'identite Hektor :

```text
le token Hektor reste la source principale d'identite
le localStorage impersonate est conserve comme information secondaire
les marqueurs impersonate 0 / 1 ne doivent pas masquer le token actif
```

Variables utiles :

```text
CONSOLE_CREATE_HEKTOR_HTTP_DIRECT=true
CONSOLE_CREATE_HEKTOR_PLAYWRIGHT_FALLBACK=true
CONSOLE_HEKTOR_CONTEXT_SWITCH_FALLBACK_PLAYWRIGHT=true
```

## Correctif complementaire - 2026-05-16 : workers separes

Le worker unique a ete separe logiquement en plusieurs roles prudents :

```text
actions
  creation annonce
  modification annonce
  ajout mandant

documents
  upload document
  preparation cloud
  suppression document
  sync documents console

admin
  suppression annonce

sync_light
  refresh_console_data

sync_full
  archive_cloud_documents
```

Ce qui n'a pas ete fait volontairement :

```text
actions_2
```

Raison : le test montre que les actions courantes sont deja rapides. Le vrai gain est de ne plus melanger documents, suppression admin et sync lourde avec les actions negociateur.

Chaque worker utilise maintenant une session Hektor separee :

```text
Console/sessions/storage_state_actions.json
Console/sessions/storage_state_documents.json
Console/sessions/storage_state_admin.json
Console/sessions/storage_state_sync_light.json
Console/sessions/storage_state_sync_full.json
```

Le worker `actions` poll toutes les 5 secondes.
Le worker `documents` poll toutes les 5 secondes.
Le worker `admin` poll toutes les 5 secondes.
Le worker `sync_light` poll toutes les 10 secondes.
Le worker `sync_full` poll toutes les 60 secondes.

Migration Supabase appliquee :

```text
supabase/patch_console_worker_split_2026-05-16.sql
supabase/patch_console_worker_kinds_2026-05-16.sql
```

Cette migration modifie `public.app_console_claim_next_job(p_worker_id, p_worker_kind)` afin que :

```text
worker actions    -> creation/modification/mandant
worker documents  -> documents uniquement
worker admin      -> suppression annonce
worker sync_light -> refresh_console_data
worker sync_full  -> archive_cloud_documents
```

## Correctif complementaire - 2026-05-16 : push Supabase cible

Le push Supabase appele apres une action Hektor est maintenant limite a l'annonce concernee quand c'est possible :

```text
phase2/sync/push_upgrade_to_supabase.py --hektor-annonce-id {id}
```

Le script resout l'annonce Hektor vers son `app_dossier_id`, puis ne pousse que ce dossier dans les tables courantes.

Objectif :

```text
ne plus remplacer tout le registre mandat ni recalculer tout le push apres une simple action utilisateur
```

## Correctif complementaire - 2026-05-16 : affichage web/mobile

Les cartes de jobs visibles dans l'app distinguent maintenant :

```text
Creation en cours
Modification en cours
Mandant en cours
Suppression en cours
```

Le rendu mobile utilise les memes libelles et des couleurs distinctes pour que l'utilisateur comprenne l'action en attente sans ouvrir les logs.

Commandes locales :

```powershell
.\run_console_worker.ps1 -WorkerKind actions
.\run_console_worker.ps1 -WorkerKind documents
.\run_console_worker.ps1 -WorkerKind admin
.\run_console_worker.ps1 -WorkerKind sync_light
.\run_console_worker.ps1 -WorkerKind sync_full
```

Installation Windows :

```powershell
.\install_console_worker_task.ps1 -WorkerKind actions
.\install_console_worker_task.ps1 -WorkerKind documents
.\install_console_worker_task.ps1 -WorkerKind admin
.\install_console_worker_task.ps1 -WorkerKind sync_light
.\install_console_worker_task.ps1 -WorkerKind sync_full
```

Si Windows refuse la creation de taches planifiees sans droits administrateur, utiliser l'installation au demarrage utilisateur :

```powershell
.\install_console_worker_startup_shortcuts.ps1
```

Ce script cree les raccourcis dans le dossier Startup Windows :

```text
Hektor Console Worker Actions.lnk
Hektor Console Worker Documents.lnk
Hektor Console Worker Admin.lnk
Hektor Console Worker Sync Light.lnk
Hektor Console Worker Sync Full.lnk
```

Ils relancent les workers specialises a la prochaine connexion Windows de l'utilisateur.

## Test reel HTTP direct - 2026-05-16

Test effectue via le worker `actions` :

```text
creation job = 414ebfbf-f97a-4830-aaa9-d083c2a77052
hektor_annonce_id = 62250
negociateur = Emmanuelle PEREIRA / idUser 51
transport = http_direct
is_draft = false
is_broadcasted = false
is_valid = false
created_at_hektor = 2026-05-16T01:43:53
```

Routes confirmees pendant le test :

```text
GET  ajoutebien                         status 200
POST ajoutebien_wizardBien              status 200
GET  upval etatAnnonce = 1              status 200
GET  upval diffusable = 0               status 200
GET  upval partage = 0                  status 200
```

Nettoyage effectue :

```text
delete job = 34ad7125-93eb-4663-a7d0-40dde23dff43
annonce 62250 supprimee dans Hektor
after_found = false
documents indexes = 0
fichiers locaux supprimes = 0
fichiers cloud supprimes = 0
```

Conclusion :

```text
OK - la creation ne depend plus de Playwright.
OK - Playwright peut encore servir uniquement au contexte negociateur si Hektor ne confirme pas l'autologin HTTP.
OK - le worker actions traite creation et suppression sans attendre le worker sync.
```

## Test workers specialises - 2026-05-16

Test final apres separation `actions/documents/admin/sync_light/sync_full` :

```text
annonce test = 62254
mandant test = 603489
creation annonce      total  9.3 s  worker actions
ajout mandant         total  9.5 s  worker actions
modification annonce  total  5.9 s  worker actions
suppression annonce   total 21.6 s  worker admin
```

Comparaison au test precedent :

```text
creation annonce      16.4 s ->  9.3 s
ajout mandant          8.6 s ->  9.5 s
modification annonce   9.5 s ->  5.9 s
suppression annonce   41.0 s -> 21.6 s
```

Le `sync_light` cible bien l'annonce et ne bloque plus les actions utilisateur, mais il reste lourd car il lance encore la chaine Phase 2 :

```text
creation_sync_light   total 154.4 s
mandant_sync_light    total 167.5 s
update_sync_light     total 171.9 s
```

Conclusion technique :

```text
OK - les actions utilisateur sont plus rapides et bien isolees.
OK - la suppression passe par le worker admin.
OK - les sessions Hektor sont separees par worker.
A optimiser plus tard - sync_light doit devenir un vrai upsert direct annonce -> Supabase sans bootstrap/refresh_views complet.
```

## Correctif 16/05/2026 - refresh annonce unique direct Supabase

Le `sync_light` ne relance plus la chaine complete :

```text
build_case_index global
bootstrap_phase2 global
refresh_views global
push_upgrade_to_supabase cible
```

Nouveau flux utilise par `refresh_console_data` :

```text
1. refresh_single_annonce.py --id-annonce {id}
   -> relit uniquement l'annonce Hektor dans la base locale

2. push_single_annonce_to_supabase.py --hektor-annonce-id {id}
   -> reconstruit seulement le case index de cette annonce
   -> met a jour app_dossier local pour cette annonce
   -> regenere les work items automatiques de cette annonce
   -> cree des vues SQLite temporaires pour cette annonce
   -> upsert directement Supabase :
      app_dossier_current
      app_dossier_detail_current
      app_work_item_current
      app_mandat_broadcast_current
      app_mandat_register_current
```

Point de securite important :

```text
Les vues locales persistantes ne sont pas supprimees ni reconstruites.
Les tables globales ne sont pas purgees.
Le refresh quotidien complet garde son role de consolidation globale.
```

Temps mesure sur annonce existante `62163` :

```text
push direct Supabase seul          4.19 s
lecture Hektor + push direct       7.11 s
ancien sync_light cible       154 a 172 s
```

Conclusion :

```text
OK - l'utilisateur voit les changements beaucoup plus vite apres creation/modification/mandant/suppression.
OK - le worker sync_light reste separe des actions utilisateur.
OK - le refresh complet quotidien reste disponible pour recalage global.
```

## Impact sur les documents et uploads

Le flux document continue d'utiliser les jobs existants :

```text
upload_document_to_hektor
delete_document_from_hektor
sync_console_documents
prepare_document_cloud
archive_cloud_documents
```

Depuis le correctif de contexte Hektor, les ecritures metier sont executees avec le bon contexte negociateur :

```text
commercial app    -> acces Hektor du commercial demandeur
admin / manager   -> negociateur cible transmis par le payload ou le dossier
suppression annonce -> admin uniquement
```

## Correctif mandants / proprietaires

Audit Playwright du 15/05/2026 :

`chargeannonce_contacts` ne correspond pas aux mandants/proprietaires du mandat. Cette route sert aux contacts annexes de l'annonce comme notaire, syndic, diagnostiqueur ou confrere.

Les mandants/proprietaires sont geres dans l'ecran Hektor `chargeannonce_MandatPrix`.

Flux HTML observe :

```text
xmlrpc.php?mode=div_display_prospects_liste&id={hektor_annonce_id}
xmlrpc.php?mode=selectnouveauproprio_sup&id={hektor_contact_id}&idann={hektor_annonce_id}
```

Un nouveau job console a ete prepare :

```text
link_hektor_mandant
```

Role du job :

```text
App -> app_console_job(link_hektor_mandant)
PC serveur -> se place dans le contexte Hektor negociateur
PC serveur -> appelle selectnouveauproprio_sup
PC serveur -> verifie div_display_prospects_liste
PC serveur -> relance une sync ciblee pour faire remonter le mandant dans l'app
```

Point important sur les identifiants :

```text
hektor_negociateur_id local peut correspondre a userObjectId Hektor
autologin Hektor attend idUser
la resolution fiable se fait par email via exports_ap/hektor_users_directory.json
```

Exemple confirme pendant l'audit :

```text
Emmanuelle Pereira
email = pereira@gti-immobilier.fr
idUser autologin = 51
userObjectId Hektor = 26
```

Ne pas reutiliser directement `hektor_negociateur_id` comme `idUser` autologin sans resolution par email.

## Modification future des annonces

Pour les prochaines modifications de fiche annonce, garder la meme regle :

```text
creation annonce       -> contexte negociateur obligatoire
modification annonce   -> contexte negociateur obligatoire
upload document        -> contexte negociateur obligatoire
suppression document   -> contexte negociateur obligatoire
association mandant    -> contexte negociateur obligatoire
suppression annonce    -> contexte administrateur uniquement
```

Les endpoints de modification de champs annonce ne sont pas encore figes. Il faut les capturer proprement avec Playwright avant automatisation pour eviter d'envoyer des commandes HTML partielles ou dans un mauvais contexte.
