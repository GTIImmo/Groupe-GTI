# Note schema Supabase V1 React

Date: 24/03/2026

## Objet

Definir le schema cible Supabase de la V1 React a partir du contrat `sync` de phase 2.

## Source de verite fonctionnelle

Le schema V1 part du contrat :

- `phase2/docs/APP_PAYLOAD_V1_SAMPLE.json`

Il ne repart pas directement du schema brut Hektor.

## Choix retenu

Pour la V1, on ne cherche pas encore une normalisation parfaite.

On retient une couche applicative denormalisee :

- `app_sync_run`
- `app_summary_snapshot`
- `app_dossier_v1`
- `app_work_item_v1`
- `app_user_profile`

## Pourquoi ce choix

Ce schema colle au besoin reel de la V1 React :

- tableau de bord
- liste dossiers
- file de travail
- authentification et profils

Il permet :

- d'aller vite
- de garder un contrat stable cote front
- de limiter l'exposition de la complexite SQL interne

## Tables

### `app_user_profile`

Profil applicatif lie a `auth.users`.

Role V1 :

- `admin`
- `manager`
- `commercial`
- `lecture`

### `app_sync_run`

Trace chaque import depuis la phase 2.

But :

- savoir quelle generation alimente l'app
- garder une tracabilite simple

### `app_summary_snapshot`

Stocke les compteurs du dashboard pour un `sync_run_id`.

### `app_dossier_v1`

Table principale pour la liste dossiers et la fiche simple.

Elle reprend les champs utiles de `app_view_generale`.

### `app_work_item_v1`

Table principale pour la file `Demandes mandat / diffusion`.

Elle reprend les champs utiles de `app_view_demandes_mandat_diffusion`.

## Vues exposees

Le schema ajoute aussi :

- `app_latest_sync_run`
- `app_dashboard_v1`
- `app_dossiers_current`
- `app_work_items_current`

But :

- simplifier les requetes du front React
- toujours lire le dernier import disponible

Les vues sont definies avec :

- `security_invoker=on`

But :

- executer la vue avec les droits du user appelant
- mieux respecter le modele RLS des tables sous-jacentes
- reduire le risque d'exposition involontaire

## Securite retenue en V1

Principe simple :

- seul un utilisateur authentifie et actif peut lire les donnees app
- `RLS` active sur les tables applicatives
- profils stockes dans `app_user_profile`

Ce choix est volontairement simple pour une V1 interne.

## Point important

La V1 React ne doit pas lire directement :

- les tables Hektor
- les structures JSON lourdes
- les objets internes de reconstruction phase 2

Elle doit lire uniquement les objets stabilises exposes par le schema applicatif Supabase.
