# KPI vues Commercial / Suivi

Date : 2026-04-02

## Contexte

Le champ `statut_global` n'est plus utilisé dans l'application pour piloter les KPI et les filtres.

La lecture métier repose désormais sur :

- `statut_annonce` pour le statut Hektor
- `diffusable` pour le oui/non diffusion
- `portails_resume` pour LeBonCoin / Bien'ici
- `offre_id` / `compromis_id` / `vente_id` pour les affaires en cours
- la dernière demande de diffusion pour les états workflow

## KPI Commercial

Vue concernée : `Liste des mandats`

Grille retenue :

- `Annonces`
- `Mandat non diffusé`
- `Mandat diffusé`
- `Sans mandat`
- `Affaires en cours`
- `Diffusé sur LeBonCoin`
- `Diffusé sur Bien'ici`
- `Demande envoyée`
- `Correction en attente`

Définitions :

- `Annonces` : total de la sélection
- `Mandat non diffusé` : mandat présent et `diffusable != 1`
- `Mandat diffusé` : mandat présent et `diffusable = 1`
- `Sans mandat` : `numero_mandat` vide
- `Affaires en cours` : `offre_id` ou `compromis_id` ou `vente_id`
- `Diffusé sur LeBonCoin` : `portails_resume` contient `leboncoin`
- `Diffusé sur Bien'ici` : `portails_resume` contient `bienici` / `Bien'ici`
- `Demande envoyée` : dernière demande `pending` ou `in_progress`
- `Correction en attente` : dernière demande `waiting_commercial` ou `refused`

Notes :

- les compteurs mandat / diffusion suivent les filtres actifs
- les compteurs demande sont calculés à partir des demandes chargées sur les mandats visibles

## KPI Suivi

Vue concernée : `Suivi`

Grille retenue :

- `Annonces`
- `Demande à traiter`
- `Demande rejetée`
- `Demande acceptée`

Définitions :

- `Annonces` : total de la sélection
- `Demande à traiter` : `pending` + `in_progress`
- `Demande rejetée` : `refused`
- `Demande acceptée` : `accepted`

Note importante :

- les KPI `Suivi` ne sont plus calculés sur la première page chargée
- ils sont recalculés sur l'ensemble des mandats filtrés, puis rapprochés des demandes correspondantes

## Fichiers modifiés

- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`

## Vérification

Commande :

```powershell
cd C:\Users\frede\Desktop\Projet\apps\hektor-v1
npx.cmd tsc -b
```

Résultat :

- compilation OK
