# Note correctifs surcouche demande de diffusion

Date: 2026-03-31

## Objet

Figer la liste des correctifs a apporter a la surcouche `demande de diffusion` avant implementation.

Objectif cible :

- le negociateur cree une demande depuis `Liste des mandats`
- le bouton `Demande de diffusion` n'est visible que si le bien n'est pas diffusable
- le bouton `Diffusion` est visible si le bien est deja diffusable
- Pauline traite la demande dans une interface dediee
- la demande suit un statut simple :
  - `en_cours`
  - `accepte`
  - `refuse`
- en cas d'acceptation :
  - le bien devient diffusable automatiquement
  - les passerelles par defaut autorisees sont selectionnees automatiquement
  - l'information est stockee dans l'application
  - un email est envoye au negociateur
- en cas de refus :
  - Pauline choisit un motif de refus type
  - le motif applique un texte et des delais de relance
  - un email est envoye au negociateur
  - des relances automatiques continuent tant que le negociateur n'a pas corrige
  - si necessaire le manager est prevenu

## Constat actuel

La surcouche actuelle couvre une demande simple, mais il manque plusieurs briques metier :

- pas de vrai workflow de decision Pauline
- pas de separation claire entre demande initiale et pilotage de diffusion
- pas de motifs types de refus parametrables
- pas de gestion robuste des relances
- pas de trace complete des notifications envoyees
- pas de bouton explicite cote negociateur pour indiquer qu'une correction a ete faite
- pas d'interface Pauline optimisee pour le traitement rapide
- pas de console de diffusion dediee pour les biens deja diffusable

## Correctifs a apporter

### 1. Stabiliser le workflow metier

Conserver un statut principal unique sur la demande :

- `en_cours`
- `accepte`
- `refuse`

Regle :

- `en_cours` = demande ouverte ou en attente de traitement
- `accepte` = decision positive finale Pauline
- `refuse` = decision negative finale Pauline

Les relances ne doivent pas etre un statut principal.

### 2. Enrichir l'objet `demande de diffusion`

La demande doit stocker au minimum :

- identifiant dossier / annonce / mandat
- createur de la demande
- date de creation
- commentaire initial
- statut courant
- decideur Pauline
- date de decision
- commentaire de decision

Si `accepte` :

- `accepted_set_diffusable`
- `accepted_default_portals_json`
- `accepted_email_sent_at`

Si `refuse` :

- `refusal_reason_code`
- `refusal_reason_label`
- `refusal_message`
- `correction_required`
- `corrected_at`
- `refused_email_sent_at`
- `last_reminder_at`
- `next_reminder_at`
- `reminder_count`
- `manager_notified_at`

### 3. Ajouter une table de motifs types de refus

Chaque motif doit porter :

- `code`
- `label`
- `default_refusal_message`
- `default_reminder_message`
- `default_manager_message`
- `first_reminder_delay_days`
- `reminder_interval_days`
- `manager_escalation_delay_days`
- `is_active`

Liste V1 retenue :

- `elements_manquants`
- `mandat_non_valide`
- `bien_non_diffusable`
- `photos_non_conformes`
- `texte_annonce_incomplet`
- `bareme_honoraire_non_respecte`
- `validation_interne_requise`
- `correction_fiche_bien`
- `autre`

### 4. Refondre l'action `Accepter`

Quand Pauline accepte une demande, l'interface doit lui permettre de :

- ajouter un commentaire si besoin
- valider la decision

Effets attendus :

- la demande passe en `accepte`
- le bien passe automatiquement en `diffusable`
- les passerelles autorisees par defaut sont selectionnees automatiquement
- l'information est stockee dans l'app
- le mail d'acceptation est envoye au negociateur
- le lien `Diffusion` devient visible sur la ligne de l'annonce

Regle :

- le choix fin des passerelles ne se fait plus dans l'ecran de validation Pauline
- il se fait dans la console `Diffusion`

### 5. Refondre l'action `Refuser`

Quand Pauline refuse une demande, l'interface doit lui permettre de :

- choisir un motif type
- precharger le texte associe
- ajouter un commentaire libre si necessaire
- valider le refus

Effets attendus :

- la demande passe en `refuse`
- le mail initial de refus est envoye au negociateur
- la prochaine relance est programmee automatiquement

### 6. Ajouter le mecanisme de relances automatiques

Sur une demande `refuse` avec correction attendue :

- relance automatique au negociateur selon le motif
- compteur de relances incremente
- mise a jour de `next_reminder_at`
- si delai depasse, email au manager

La relance doit s'arreter quand le negociateur signale qu'il a corrige.

### 7. Ajouter l'action negociateur `J'ai corrige`

Depuis l'application, le negociateur doit pouvoir :

- voir qu'une demande est refusee
- voir le motif
- voir le texte explicatif
- cliquer `J'ai corrige`

Effets attendus :

- `corrected_at` renseigne
- les relances automatiques s'arretent
- la demande peut etre remontee a Pauline pour relecture

### 8. Ajouter l'escalade manager

Sur une demande `refuse` non corrigee apres delai :

- envoi automatique d'un email au manager
- trace de l'escalade dans l'application

Pre-requis :

- connaitre le manager du negociateur
- stocker cette relation proprement

### 9. Refondre l'interface Pauline

Pauline a besoin d'une interface de traitement efficace, avec :

- vue `En cours`
- vue `Acceptees`
- vue `Refusees`
- affichage dossier / mandat / negociateur / statut / motif / relance
- actions rapides :
  - `Accepter`
  - `Refuser`
  - `Voir historique`
  - `Relancer manuellement` si besoin

Pauline doit aussi avoir acces a la console `Diffusion` des biens deja diffusable.

### 10. Ajouter une console `Diffusion`

Cette console est distincte de la demande initiale.

Visibilite :

- visible pour le negociateur si `diffusable = oui`
- visible pour Pauline si `diffusable = oui`
- acces direct depuis un lien `Diffusion` sur la ligne de l'annonce

But :

- voir l'etat courant des passerelles
- piloter les portails souhaites
- demander ajout / retrait si necessaire
- verifier l'etat reel lu dans Hektor

La console doit separer :

- etat observe
- etat souhaite
- historique des actions

### 11. Ajouter un historique clair

Chaque demande doit garder la trace de :

- creation
- decision Pauline
- emails envoyes
- relances
- correction declaree par le negociateur
- escalation manager

## Priorite de mise en oeuvre

### V1 indispensable

- workflow `en_cours / accepte / refuse`
- separation claire entre `Demande de diffusion` et `Diffusion`
- enrichissement de l'objet demande
- table des motifs types de refus
- action `Accepter`
- action `Refuser`
- interface Pauline de base
- affichage conditionnel des boutons `Demande de diffusion` / `Diffusion`
- console `Diffusion` minimale
- bouton negociateur `J'ai corrige`

### V1.5 importante

- relances automatiques
- escalation manager
- historique complet
- traces emails envoye / non envoye

### V2

- parametrage plus fin des delais par agence
- statistiques Pauline
- relances manuelles enrichies
- templates email admin modifiables depuis l'app

## Point de depart recommande

Ordre de travail conseille :

1. figer le modele de donnees de la demande
2. figer la table des motifs de refus
3. figer le principe du bouton `Diffusion` sur bien diffusable
4. implementer les actions Pauline `Accepter` / `Refuser`
5. afficher les statuts propres dans l'app
6. ajouter le bouton `J'ai corrige`
7. brancher les relances automatiques ensuite

## Decision

La prochaine implementation doit commencer par :

- le schema de la demande
- les motifs de refus
- le principe de la console `Diffusion`
- l'interface Pauline

Avant d'ajouter l'automatisation des relances et l'escalade manager.
