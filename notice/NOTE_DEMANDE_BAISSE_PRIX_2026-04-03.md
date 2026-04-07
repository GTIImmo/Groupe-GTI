# Note demande baisse de prix

Date : 03/04/2026

## Objet

Ajouter un second type de demande metier dans l'application :

- `Demande de validation`
- `Demande de baisse de prix`

Le moteur de workflow reste unique et reutilise `app_diffusion_request` avec un `request_type` distinct.

## Regle metier

La `Demande de baisse de prix` n'est autorisee que si :

- `validation_diffusion_state` correspond a une validation positive
- lecture appliquee dans le front via `isValidationApproved(...)`

Lecture utilisateur :

- si le mandat n'est pas sous validation, la demande de baisse de prix est desactivee
- si le mandat est sous validation, le negociateur peut la creer

## Ergonomie retenue

Dans la liste des annonces et dans le suivi :

- une seule colonne `Action`
- cette colonne affiche `1` ou `2` boutons selon l'etat de l'annonce
- plus de colonne dediee supplementaire pour les demandes
- chaque bouton est compose de `2` segments visuels
  - segment gauche : type fixe
  - segment droit : action / etat courant

Grammaire visuelle retenue :

- types
  - `Valider`
  - `Baisse de prix`
  - `Diffusion`
- actions / etats cote commercial
  - `Ajouter`
  - `Corriger`
  - `Envoyee`
  - `En cours`
  - `Modifier`
- actions / etats cote suivi
  - `A traiter`
  - `A corriger`
  - `Refusee` / `Rejetee`
  - `Acceptee`

Code couleur :

- couleur de type stable quel que soit l'etat
  - `Valider` : ambre
  - `Baisse de prix` : vert sauge
  - `Diffusion` : bleu petrole
- couleur d'action stable quel que soit le type
  - `Ajouter` : neutre clair
  - `Envoyee` / `En cours` / `A traiter` : jaune doux
  - `Corriger` / `A corriger` : orange
  - `Refusee` / `Rejetee` : brique
  - `Acceptee` : vert confirme
  - `Modifier` : bleu diffusion

Regle d'affichage :

- si `validation != oui`
  - afficher un bouton `Demande de validation`
  - si une demande validation active existe deja, le libelle du bouton reprend son etat
- si `validation = oui`
  - afficher un bouton `Diffusion`
- si `validation = oui`
  - ajouter un bouton `Demande de baisse de prix`
  - si une demande baisse de prix active existe deja, le libelle du bouton reprend son etat

Donc une annonce a au maximum 2 boutons visibles dans `Action`.

Lecture par vue :

- vue liste
  - `Valider + Ajouter` ou `Valider + Corriger`
  - `Baisse de prix + Ajouter` ou `Baisse de prix + Corriger`
  - `Diffusion + Modifier`
- vue suivi
  - `Valider + A traiter / A corriger / Refusee / Acceptee`
  - `Baisse de prix + A traiter / A corriger / Rejetee / Acceptee`

Demande active :

- statuts actifs retenus : `pending`, `in_progress`, `waiting_commercial`
- statuts clotures : `accepted`, `refused`

Pour `demande_baisse_prix` :

- une fois `accepted` ou `refused`, le bouton revient a `Demande de baisse de prix`
- l'historique de la demande precedente est conserve dans la fiche bien
- plusieurs demandes de baisse de prix sont donc possibles dans le temps, mais une seule active a la fois
- dans la vue liste, cela se traduit par le retour a `Baisse de prix + Ajouter`

Pour `demande_diffusion` / `Validation` :

- une fois `accepted`, la vue liste ne montre plus `Valider`
- l'action disponible devient `Diffusion + Modifier`
- dans la vue suivi, la demande reste visible comme `Valider + Acceptee`

Dans la modale de demande :

- le negociateur peut choisir le `Type de demande`
  - `Validation`
  - `Baisse de prix`
- pour `Baisse de prix`, un champ `Nouveau prix demande` est obligatoire
- un rappel de contexte est affiche :
  - prix actuel
  - validation requise
  - controle attendu de l'avenant signe

Dans la vue Pauline :

- le type de demande est affiche avec un badge dedie
- la decision reste dans le meme workflow :
  - `in_progress`
  - `accepted`
  - `refused`
  - `waiting_commercial`

Compatibilite `Suivi des mandats` :

- la vue traite les demandes par type
- une diffusion et une baisse de prix peuvent donc coexister sur la meme annonce
- par defaut, le suivi affiche les demandes actives
- les KPI de suivi peuvent encore cibler les demandes `accepted` et `refused`

## Traitement Pauline

Pour `Demande de validation` :

- comportement existant conserve
- en cas d'acceptation, l'application appelle toujours le traitement Hektor existant
- le bien passe en `diffusable = oui`
- les passerelles par defaut de l'agence restent activees automatiquement

Pour `Demande de baisse de prix` :

- Pauline controle la presence et la conformite de l'avenant signe dans Hektor
- si la demande est acceptee, elle valide metierement la baisse
- aucun appel automatique a `acceptDiffusionRequestOnHektor(...)` n'est declenche pour ce type

## Motifs de refus

Pour `Diffusion` :

- liste existante conservee

Pour `Baisse de prix` :

- `avenant_signe_absent`
- `erreur_sur_avenant`
- `autre`

## KPI et filtres

Les KPI `Demandes` restent agreges :

- `Demande envoyee`
- `Correction en attente`

Ils cumulent :

- `demande_diffusion`
- `demande_baisse_prix`

Deux KPI cliquables supplementaires ont ete ajoutes :

- `Mandats valides`
- `Mandats non valides`

Ils pilotent un drill-down sur le filtre `Validation`.

Un filtre distinct a ete ajoute :

- `Type de demande`
  - `Diffusion`
  - `Baisse de prix`

Ce filtre existe dans :

- `Vue stock`
- `Liste des annonces`
- `Suivi des mandats`

## Historique

Le detail de la demande reste conversationnel :

- message initial
- retour Pauline
- correction du commercial
- decision finale

Le detail de l'annonce conserve un historique distinct par type :

- `Historique diffusion`
- `Historique baisse de prix`

Cela permet de masquer la demande cloturee dans `Action` tout en conservant sa trace metier dans la fiche bien.

## Emails

Les emails de decision restent emis par le meme transport, mais le contenu depend maintenant de `request_type`.

Pour `demande_baisse_prix` :

- sujet adapte
- texte adapte
- action attendue adaptee
- plus aucune reference a la diffusion dans le corps du message

Pour `demande_diffusion` :

- le vocabulaire visible utilisateur est recadre en `validation`
- le sujet et le contenu ne parlent plus de `demande de diffusion`

## Impact technique

Pas de migration SQL complementaire necessaire pour porter le type :

- `request_type` existe deja dans `app_diffusion_request`

Le projet reste compatible avec le schema actuel.

## Fichiers concernes

- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
