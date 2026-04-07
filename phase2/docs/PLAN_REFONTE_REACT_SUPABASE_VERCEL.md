# Plan Refonte React Supabase Vercel

## Objectif

Transformer la phase 2 actuelle en socle data stable pour une future application React hebergee sur Vercel et alimentee par Supabase.

## Perimetre a reprendre

Le modele cible doit couvrir au minimum :

- annonces
- mandats
- transactions
- contacts
- passerelles / diffusions
- negociateurs / responsables
- statuts metier
- anomalies de consolidation
- traçabilite des imports

## Contrat de la future phase 2

La future phase 2 ne doit plus generer l'application. Elle doit produire :

- un modele consolide clair
- des regles metier centralisees
- des controles qualite
- des sorties prêtes a synchroniser vers Supabase

## Decoupage cible

### `pipeline/`

Responsabilite :

- chargement des sources normalisees
- assemblage des objets metier consolides
- preparation des vues de consommation

Livrables attendus :

- construction des tables consolidees
- gestion des cles techniques et numeros metier

### `rules/`

Responsabilite :

- statut_global
- sous_statut
- diffusable / non_diffusable
- cas sans mandat
- detection des cas incoherents

Regle :

- toute regle metier doit vivre ici ou dans SQL explicitement rattache a ce bloc

### `checks/`

Responsabilite :

- controles de coherence
- comptages
- dossiers sans titre
- annonces sans mandat
- collisions identifiant / numero
- verification de presence des objets attendus

### `sync/`

Responsabilite :

- export vers la future couche app
- dans la cible : synchronisation Supabase
- en transition : exports de debug ou vues de comparaison

## Strategie de migration

1. Conserver `phase2.sqlite` comme reference fonctionnelle temporaire.
2. Reprendre les regles dans `refresh_views.py` et les isoler proprement.
3. Definir le schema cible pour Supabase.
4. Construire une V1 React :
   - login
   - liste annonces
   - fiche annonce
   - filtres
5. Ajouter ensuite transactions, contacts et passerelles sans casser le socle.

## Point de discipline

- pas de logique metier critique dans le front
- pas de confusion entre identifiants techniques et numeros metier
- pas d'exports HTML consideres comme source de verite
