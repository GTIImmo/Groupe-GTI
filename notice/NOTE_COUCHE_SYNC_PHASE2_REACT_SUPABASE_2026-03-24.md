# Note couche sync phase 2 -> React / Supabase

Date: 24/03/2026

## Objet

Documenter la couche `sync` ajoutee a la phase 2 pour preparer la future alimentation de l'application React / Supabase.

## Positionnement

La phase 2 ne doit plus etre pensee comme l'application.

Elle doit produire :

- une base consolidee fiable
- des regles metier explicites
- des controles qualite
- une sortie de consommation stable pour la future app

La couche `sync` correspond a ce dernier point.

## Decision retenue

Avant de pousser vers Supabase, on introduit un contrat de sortie local simple.

But :

- figer un format de donnees lisible
- verifier les champs exposes a l'app
- limiter les dependances directes de l'UI au schema SQL interne

## Contrat V1 retenu

Le payload de sortie V1 contient 4 blocs :

- `meta`
- `summary`
- `dossiers`
- `work_items`

### `meta`

Informations techniques sur la generation :

- source
- nom du contrat
- script generateur

### `summary`

Compteurs rapides pour un futur tableau de bord :

- total dossiers
- total demandes
- total sans mandat
- total bloques
- total valides diffusion
- total visibles
- total statuts globaux nuls

### `dossiers`

Liste de dossiers orientee vue generale.

Champs exposes en V1 :

- `app_dossier_id`
- `hektor_annonce_id`
- `numero_dossier`
- `numero_mandat`
- `titre_bien`
- `ville`
- `type_bien`
- `prix`
- `commercial_id`
- `commercial_nom`
- `statut_annonce`
- `validation_diffusion_state`
- `etat_visibilite`
- `statut_global`
- `sous_statut`
- `alerte_principale`
- `priority`
- `has_open_blocker`
- `commentaire_resume`
- `date_relance_prevue`
- `dernier_event_type`
- `dernier_work_status`

### `work_items`

Liste de travail orientee `Demandes mandat / diffusion`.

Champs exposes en V1 :

- `app_dossier_id`
- `hektor_annonce_id`
- `numero_dossier`
- `numero_mandat`
- `titre_bien`
- `commercial_nom`
- `type_demande_label`
- `work_status`
- `internal_status`
- `priority`
- `validation_diffusion_state`
- `etat_visibilite`
- `motif_blocage`
- `has_open_blocker`
- `next_action`
- `date_relance_prevue`
- `date_entree_file`
- `date_derniere_action`
- `age_jours`

## Script ajoute

Script :

- `phase2/sync/export_app_payload.py`

Sortie generee :

- `phase2/docs/APP_PAYLOAD_V1_SAMPLE.json`

## Pourquoi cette etape est utile

Elle permet :

- de preparer l'app React sans brancher directement le front sur tout le schema SQL
- de clarifier le contrat de donnees avant migration Supabase
- de reduire le couplage entre SQL interne et interface

## Suite logique

Apres validation de ce contrat local :

1. figer les champs reellement utiles a la V1 React
2. creer le schema cible Supabase
3. remplacer l'export JSON local par une vraie synchronisation `phase2 -> Supabase`

## Regle de discipline

Le payload sync ne doit pas embarquer tout Hektor.

Il doit exposer :

- les champs utiles a l'app
- les statuts consolides
- les identifiants necessaires

Mais il ne doit pas devenir un dump generaliste de la base source.
