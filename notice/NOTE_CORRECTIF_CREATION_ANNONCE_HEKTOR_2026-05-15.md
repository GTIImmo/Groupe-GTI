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

## Limites connues

Le formulaire actuel ouvre le wizard et valide le type par defaut `Appartement`.

Les champs libres transmis dans le payload, par exemple titre, ville, prix ou surface, sont conserves dans le resultat de job mais ne sont pas encore injectes dans le wizard Hektor.

L'annonce creee est donc une base Hektor active/non brouillon a completer ensuite dans Hektor ou dans un futur flux d'enrichissement.

## Impact sur les documents et uploads

Aucun changement n'a ete fait sur :

```text
upload_document_to_hektor
delete_document_from_hektor
sync_console_documents
prepare_document_cloud
archive_cloud_documents
```

Le correctif est limite au flux de creation annonce.
