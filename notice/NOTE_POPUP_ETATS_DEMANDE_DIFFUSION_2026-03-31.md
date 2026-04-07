# Note popup etats demande diffusion

Date: 2026-03-31

## Objet

Figer le comportement UI des deux vues `Mandats` et `Suivi des mandats` autour de la surcouche `demande de diffusion`.

Objectif :

- remplacer le bouton actuel par un bouton d'etat unique par ligne
- faire varier ce bouton selon la situation de l'annonce
- ouvrir un popup dedie a la demande
- afficher dans ce popup l'historique et les echanges
- preparer les relances et les aller-retour entre negociateur et Pauline

## Modules

Deux modules restent distincts :

- `demande de diffusion`
- `Diffusion`

Regle :

- si le bien n'est pas diffusable : on travaille sur la `demande de diffusion`
- si le bien est diffusable : on bascule sur `Diffusion`

## Etats d'affichage retenus

### Cote negociateur

- `Demande de diffusion`
- `Demande envoyee`
- `A corriger`
- `Diffusion`

### Cote Pauline

- `A traiter`
- `Refusee`
- `Acceptee`

## Regles de mapping

### Vue negociateur

- `Demande de diffusion`
  - si `diffusable != 1`
  - et aucune demande ouverte

- `Demande envoyee`
  - si une demande existe
  - et qu'elle est en attente de traitement Pauline

- `A corriger`
  - si Pauline a refuse
  - et qu'une correction est attendue du negociateur

- `Diffusion`
  - si `diffusable = 1`

### Vue Pauline

- `A traiter`
  - si une demande existe
  - et qu'elle n'a pas encore ete traitee

- `Refusee`
  - si Pauline a refuse la demande
  - le negociateur voit alors `A corriger`
  - si le negociateur renvoie une correction, la meme demande repasse ensuite en `A traiter`

- `Acceptee`
  - si le bien est deja diffusable
  - ou si la demande a ete acceptee

## Colonnes a ajouter dans les listings

### Vue `Mandats`

- `Etat diffusion`
- `Derniere action`
- `Prochaine relance`
- `Dernier message`

Colonnes deja conservees :

- `Dossier`
- `Mandat`
- `Bien`
- `Negociateur`
- `Agence`
- `Statut phase 1`

### Vue `Suivi des mandats`

- `Etat traitement`
- `Motif`
- `Derniere action`
- `Prochaine relance`
- `Nb relances`
- `Dernier message`

Colonnes deja conservees :

- `Dossier`
- `Mandat`
- `Bien`
- `Negociateur`
- `Agence`
- `Statut phase 1`

## Popup demande diffusion

Le bouton d'etat ouvre toujours un popup dedie a la demande.

Important :

- le shell du popup peut etre commun
- mais le contenu ne doit pas etre identique entre le negociateur et Pauline
- `Demande envoyee` cote negociateur et `A traiter` cote Pauline ne sont pas le meme ecran metier

Le popup doit donc avoir deux variantes :

- `mode nego`
- `mode Pauline`

Structure retenue :

1. resume du bien
2. etat courant
3. historique
4. echanges
5. zone de saisie unique
6. bouton principal unique

## Variante `mode nego`

Etats concernes :

- `Demande de diffusion`
- `Demande envoyee`
- `A corriger`

Usage :

- creer une demande
- suivre une demande envoyee
- envoyer une correction ou un message complementaire

Bouton principal :

- `Envoyer la demande`
- `Envoyer la correction`
- `Demande deja envoyee` si la demande est seulement en suivi passif

## Variante `mode Pauline`

Etats concernes :

- `A traiter`
- `Refusee`
- `Acceptee`

Usage :

- lire la demande
- prendre une decision
- revoir un refus avec son historique
- ouvrir la console diffusion si la demande est acceptee

Champs specifiques Pauline :

- decision
- motif de refus
- message Pauline

Bouton principal :

- `Accepter`
- `Refuser`
- `Enregistrer le traitement`

Important :

- Pauline ne choisit plus manuellement un etat `En attente correction`
- un refus place simplement la demande cote negociateur en `A corriger`
- quand le negociateur renvoie sa correction, la meme demande revient cote Pauline en `A traiter`
- l'historique doit conserver :
  - le refus initial
  - le motif
  - le message Pauline
  - puis le retour de correction du negociateur

## Resume du bien

Afficher :

- dossier
- mandat
- bien
- negociateur
- agence
- statut phase 1
- etat diffusion / etat traitement

## Historique

Bloc timeline contenant les evenements metier :

- creation de la demande
- message initial du negociateur
- acceptation Pauline
- refus Pauline
- correction declaree
- relance envoyee
- manager notifie
- bascule en diffusion

Chaque ligne contient :

- date
- auteur
- type d'action
- message

## Echanges

Bloc de conversation dedie aux vas-et-vient entre negociateur et Pauline.

Cette zone est distincte de l'historique systeme.

Modele cible :

- messages horodates
- auteur
- role auteur
- texte

Table cible a ajouter :

- `app_diffusion_request_message`

Champs cibles :

- `id`
- `diffusion_request_id`
- `author_user_id`
- `author_name`
- `author_role`
- `message`
- `created_at`

## Zone de saisie unique

Il n'y a pas de bouton `Repondre`.

Le popup contient une seule zone de saisie, utilisee selon le contexte :

- demande initiale
- message complementaire
- correction negocateur
- commentaire Pauline
- relance Pauline

## Bouton principal unique

Le libelle depend de l'etat et du role.

### Cote negociateur

- `Envoyer la demande`
- `Envoyer le message`
- `Envoyer la correction`
- `Ouvrir la diffusion`

### Cote Pauline

- `Accepter`
- `Refuser`
- `Envoyer la relance`
- `Ouvrir la diffusion`

## Regle d'acceptation

Quand Pauline accepte :

- la demande passe en decision positive
- le bien devient diffusable
- les passerelles par defaut sont activees automatiquement
- le bouton de ligne devient `Diffusion`

Le choix fin des passerelles reste dans la console `Diffusion`.

## Regle de refus

Quand Pauline refuse :

- le motif est obligatoire
- le message de refus est stocke
- l'etat negociateur devient `A corriger`
- l'etat Pauline devient `En attente correction`
- la prochaine relance est calculee automatiquement

## Relances

Les relances restent un mecanisme et non un statut principal.

Informations a afficher dans le popup :

- derniere relance
- prochaine relance
- nombre de relances
- manager notifie ou non

Actions Pauline :

- `Envoyer la relance`
- `Notifier manager`

Actions negociateur :

- `Envoyer la correction`

Condition d'arret :

- le negociateur signale la correction
- la relance automatique s'arrete

## Donnees a suivre sur la demande

- `request_status`
- `correction_required`
- `requested_at`
- `decision_at`
- `refusal_reason`
- `processing_comment`
- `last_reminder_at`
- `next_reminder_at`
- `reminder_count`
- `manager_notified_at`
- `corrected_at`

## Ordre de mise en oeuvre

1. remplacer le bouton actuel par un bouton d'etat unique dans les deux vues
2. ajouter les colonnes de suivi dans les deux listings
3. creer le popup dedie avec historique et echanges
4. ajouter la zone de saisie unique et le bouton principal unique
5. brancher le workflow Pauline
6. ajouter la table de messages
7. brancher ensuite les relances automatiques
