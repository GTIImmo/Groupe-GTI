# Note drill-down KPI mandats

Date : 02/04/2026

## Objet

Permettre depuis les KPI de la vue mandats d'ouvrir directement la liste correspondante, sans popup supplementaire.

## Choix retenu

Le KPI ne ouvre pas une modale.

Un clic sur certains KPI applique automatiquement les filtres de la vue mandats et affiche la liste correspondante.

## KPI concernes

- `Offres en cours`
- `Offres refusees`
- `Compromis en cours`
- `Compromis annules`
- `Demande envoyee`
- `Correction en attente`
- `Demandes a traiter`
- `Demandes acceptees`
- `Demandes rejetees`

## Navigation appliquee

### Offres en cours

- ouvre la vue `mandats`
- applique :
  - `Transactions = Offre d'achat`
  - `Etat offre = En cours`

### Offres refusees

- ouvre la vue `mandats`
- applique :
  - `Transactions = Offre d'achat`
  - `Etat offre = Refusee`

### Compromis en cours

- ouvre la vue `mandats`
- applique :
  - `Transactions = Compromis`
  - `Etat compromis = En cours`

### Compromis annules

- ouvre la vue `mandats`
- applique :
  - `Transactions = Compromis`
  - `Etat compromis = Annule`

### Demande envoyee

- ouvre la vue `mandats`
- applique un filtre `Demandes = Envoyees`
- filtre techniquement les annonces dont la derniere demande a `request_status in ('pending', 'in_progress')`

### Correction en attente

- ouvre la vue `mandats`
- applique un filtre `Demandes = Correction en attente`
- filtre techniquement les annonces dont la derniere demande a `request_status in ('waiting_commercial', 'refused')`

### KPI demandes dans la vue suivi

- `Demandes a traiter` => ouvre `suivi` et filtre `pending` ou `in_progress`
- `Demandes acceptees` => ouvre `suivi` et filtre `accepted`
- `Demandes rejetees` => ouvre `suivi` et filtre `refused`

## UX retenue

- pas de popup supplementaire
- reutilisation du systeme de filtres existant
- retour utilisateur plus lisible et plus maintenable
- les KPI demandes de la vue commerciale restent dans `Liste des annonces`
- les KPI demandes de la vue `suivi` filtrent `Suivi des mandats`

## Fichiers concernes

- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/styles.css`
