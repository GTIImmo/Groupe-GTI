# Note squelette React V1

Date: 24/03/2026

## Objet

Documenter le squelette React/Vite prepare pour la future application.

## Dossier cree

- `apps/hektor-v1`

## Choix retenu

Le front V1 reste volontairement simple.

Il expose 3 blocs :

- dashboard
- liste dossiers
- file de travail

## Sources de donnees visees

Le front lit :

- `app_dashboard_v1`
- `app_dossiers_current`
- `app_work_items_current`

Il ne lit pas directement :

- `phase2.sqlite`
- les tables Hektor
- les gros JSON de detail

## Mode de fonctionnement

Deux modes sont prevus :

- mode `Supabase` si les variables d'environnement sont renseignees
- mode `mock local` sinon

Ce choix permet de travailler le front sans attendre toute la chaine de sync.

## Fichiers principaux

- `src/App.tsx`
- `src/lib/api.ts`
- `src/lib/supabase.ts`
- `src/lib/mockData.ts`
- `src/types.ts`
- `src/styles.css`

## Utilite de ce squelette

Il permet :

- de figer les premiers ecrans de la V1
- de verifier le contrat de donnees
- de commencer le front avant la sync Supabase finale

## Suite logique

1. ecrire le script `phase2 -> Supabase`
2. brancher le front sur de vraies donnees Supabase
3. ajouter login, filtres et fiche dossier
