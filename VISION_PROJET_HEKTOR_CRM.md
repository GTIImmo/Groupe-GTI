# Vision du projet Hektor CRM

Date: 23/03/2026

## But reel du projet

Le projet ne vise pas seulement a synchroniser l'API Hektor dans une base SQLite locale.

Le vrai objectif est de recuperer la base Hektor via l'API afin de construire un outil metier au-dessus de Hektor :

- une couche Hektor fiable et synchronisee localement
- une surcouche metier personnalisable

Cette surcouche doit permettre de creer un CRM, des vues de pilotage, des outils de relance, des analyses et des reportings adaptes au besoin reel de l'activite.

## Logique generale

Le projet repose sur deux niveaux.

### 1. Couche Hektor locale

Cette couche sert a :

- recuperer les donnees Hektor par API
- les stocker proprement en SQL
- reconstruire une vision locale plus fiable et plus exploitable que l'API brute
- suivre les annonces, mandats, offres, compromis, ventes, contacts et diffusions

Cette couche est le socle technique.

Elle ne constitue pas a elle seule le produit final.

### 2. Surcouche metier personnalisable

Cette couche doit permettre d'ajouter une logique qui n'existe pas nativement dans Hektor ou qui est difficile a exploiter directement dans Hektor.

Exemples :

- vues personnalisees
- CRM commercial
- outils de relance
- analyse de relance automatique
- reporting
- suivi de diffusion
- suivi de validation mandat
- suivi de commercialisation mandat
- enrichissements locaux non remontees dans Hektor

## Finalites metier visees

Le projet doit permettre de :

- suivre la diffusion des mandats
- suivre la validation des mandats
- suivre la commercialisation des mandats
- construire des vues metier par equipe ou par commercial
- donner a chaque commercial une vue claire de ses biens diffuses
- selectionner des biens selon des criteres metier
- preparer des actions metier sur ces biens
- renvoyer ensuite certaines actions vers Hektor via l'API

## Donnees locales complementaires

Le projet doit aussi permettre d'ajouter des donnees qui :

- se cumulent dans le temps
- restent utiles au pilotage interne
- ne remontent pas forcement dans Hektor

Exemples de donnees locales :

- annotations internes
- statuts internes
- historique de relance
- priorites commerciales
- classifications personnalisees
- indicateurs calcules
- decisions de suivi

## Vision produit a retenir

Le pipeline principal actuel doit etre compris comme le socle de donnees du projet.

Le but final n'est pas seulement :

- de synchroniser Hektor

Le but final est :

- de construire un outil metier exploitable au quotidien
- de piloter l'activite commerciale
- d'enrichir localement la donnee
- d'analyser l'activite
- de produire des vues et reportings utiles
- et a terme de permettre certaines actions de retour vers l'API Hektor

## Perimetre de travail actif

Au 23/03/2026 :

- le projet actif est le pipeline principal
- `ACTIF` est abandonne pour l'instant

Le pipeline principal doit donc etre considere comme :

- la base de donnees locale de reference
- le point d'appui pour la future surcouche CRM et metier

## Consequence pour les prochaines decisions

Les prochains chantiers doivent etre arbitres selon cette question :

- est-ce que cela rapproche le projet d'un vrai outil metier au-dessus de Hektor ?

Les evolutions les plus coherentes seront donc celles qui servent :

- les vues metier
- le suivi commercial
- la diffusion
- les relances
- le reporting
- les futurs retours API sur des biens selectionnes
