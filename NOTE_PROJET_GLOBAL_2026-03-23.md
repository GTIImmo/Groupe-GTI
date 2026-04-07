# Note projet global

Date: 23/03/2026

## Objet

Cette note fixe le sens du projet, son perimetre actif et les prochaines etapes.

Elle sert de point de reprise central.

## But reel du projet

Le projet a pour but de recuperer par API la base Hektor dans une base SQL locale afin de construire un outil metier au-dessus de Hektor.

Le projet ne vise donc pas seulement a synchroniser des donnees.

Le but final est de disposer :

- d'une couche Hektor locale fiable
- d'une surcouche metier personnalisable
- d'un futur CRM / outil de pilotage

## Ce que doit permettre l'outil

L'outil cible doit permettre de :

- suivre la diffusion des mandats
- suivre la validation des mandats
- suivre la commercialisation des mandats
- construire des vues metier par commercial
- voir les biens diffuses par commercial
- ajouter des donnees internes qui ne remontent pas dans Hektor
- cumuler des informations locales utiles dans le temps
- faire des relances et de l'analyse de relance
- produire des reportings
- preparer puis executer plus tard certains retours API vers Hektor

## Architecture logique retenue

Le projet repose sur deux couches.

### 1. Couche Hektor locale

Cette couche sert a :

- synchroniser l'API Hektor
- stocker les donnees dans la base locale
- consolider les objets utiles
- produire une base exploitable localement

Cette couche existe deja principalement dans le pipeline principal.

Scripts principaux :

- `sync_raw.py`
- `normalize_source.py`
- `build_case_index.py`

Base principale :

- `data/hektor.sqlite`

### 2. Surcouche metier

Cette couche doit servir a :

- exposer des vues simples pour l'usage quotidien
- ajouter des notes, statuts, priorites, relances et indicateurs
- permettre ensuite une interface d'utilisation
- preparer des actions de retour vers Hektor

## Perimetre actif au 23/03/2026

Le seul projet actif est le pipeline principal.

Le projet `ACTIF` est abandonne pour l'instant et sort du perimetre de travail courant.

Il reste seulement comme archive technique.

## Etat actuel retenu

Le pipeline principal est globalement stabilise.

Points retenus :

- synchronisation principale en place
- normalisation en place
- build final en place
- base principale alimentee
- cas `transaction_commerce` isoles proprement
- couche diffusion preparee en lecture

Le socle technique existe donc deja.

## Ce qu'il ne faut plus confondre

Le pipeline principal n'est pas le but final du projet.

Le pipeline principal est le socle de donnees.

Le vrai objectif maintenant est de construire la premiere surcouche metier exploitable.

## Prochaine etape retenue

La prochaine etape n'est plus une reprise technique de la sync.

La prochaine etape est de definir puis construire une V1 metier.

Recommendation actuelle :

- commencer par une vue `portefeuille commercial`

## V1 metier recommandee

La premiere version doit rester simple.

Elle peut couvrir :

- portefeuille commercial
- suivi diffusion
- suivi validation mandat
- suivi commercialisation

## Etapes de travail

1. definir l'usage metier prioritaire de la V1
2. definir la vue principale a exposer
3. preparer la couche SQL metier pour cette vue
4. separer clairement :
   - donnees Hektor synchronisees
   - donnees metier locales
   - futures actions de retour API
5. construire ensuite l'interface de consultation et d'action

## Interface envisagee

La piste actuellement retenue est une interface web legere maison au-dessus de la base locale.

Cette interface devra a terme permettre :

- consultation des biens
- filtres par commercial
- lecture de la diffusion
- notes et actions internes
- futures actions API

## Question directrice pour les prochaines decisions

Chaque nouveau chantier doit etre arbitre avec cette question :

- est-ce que cela rapproche le projet d'un vrai outil metier au-dessus de Hektor ?

## Notes a relire en reprise

- `REPRISE_SYNC_2026-03-21.md`
- `REPRISE_API_PARAMS.md`
- `notice/REPRISE_PHASE1_2026-03-22_UPDATE.md`
- `notice/TRANSACTION_COMMERCE_NOTE.md`
- `notice/BROADCAST_WRITE_MODEL_NOTE.md`
- `VISION_PROJET_HEKTOR_CRM.md`
