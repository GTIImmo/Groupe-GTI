# Note correctifs workflow demandes

Date : 14/05/2026

## Objet

Documenter les correctifs ajoutes pendant le clavardage autour des demandes metier de l'app :

- demande de validation classique
- demande de baisse de prix
- demande d'annulation de mandat
- popups de confirmation Pauline
- boutons action listing / detail / suivi
- coherence passerelles listing / detail

Cette note complete les anciennes notes `NOTE_DEMANDE_BAISSE_PRIX_2026-04-03.md` et `NOTE_REPRISE_VACANCES_PROJET_2026-04-09.md`.

## Commits concernes

Correctifs recents pousses sur `main` :

- `d429c81` - `Fix price drop approval publishing`
- `0310779` - `Add validation confirmation popup`
- `d639743` - `Refresh action modal design`
- `d2bf2f5` - `Prioritize portal summary badges`
- `361d389` - `Add mandate cancellation requests`
- `954ed6b` - `Show cancellation requests in follow-up`
- `75c2d07` - `Fix request filters by type`
- `16a2428` - `Isolate mandate cancellation decisions`
- `19180d4` - `Confirm mandate cancellation unpublish`

## 1. Demande de baisse de prix

### Regle metier

Une demande de baisse de prix reste un type dedie :

- `request_type = demande_baisse_prix`

Elle est accessible uniquement si l'annonce / le mandat est deja valide cote diffusion, sauf lorsqu'une demande de baisse de prix existe deja et doit rester ouvrable pour correction ou suivi.

### Acceptation Pauline

Lorsqu'une baisse de prix est acceptee :

1. l'app extrait le montant demande dans la demande
2. l'app appelle le controle prix Hektor
3. si le prix Hektor ne correspond pas au montant demande :
   - la validation est bloquee
   - popup :
     - `Operation refusee : Prix different Hektor`
   - bouton lien Hektor
4. si le prix Hektor correspond :
   - popup :
     - `Operation valide ! Voulez vous diffuse et activer toute les passerelles ?`
   - boutons `Oui` / `Non`

Comportement des boutons :

- `Non` :
  - accepte la demande
  - n'active pas les passerelles
  - ne modifie pas `Validation`
  - ne modifie pas `Diffusable`
- `Oui` :
  - accepte la demande
  - active les passerelles par defaut
  - ne doit pas invalider l'annonce
  - ne doit pas decocher `Diffusable`

Bug corrige :

- apres clic `Oui`, une annonce deja validee et diffusee pouvait repasser en non validee / non diffusee
- la baisse de prix ne doit plus produire cet effet

## 2. Demande de validation classique

### Type

La demande classique conserve :

- `request_type = demande_diffusion`

Dans l'interface, elle est presentee comme une demande de validation, meme si le nom technique historique reste lie a la diffusion.

### Acceptation Pauline

Lorsqu'une demande de validation classique est acceptee, une popup de confirmation est affichee avant automatisme Hektor.

Popup :

- titre :
  - `Lancer la validation Hektor ?`
- logique :
  - proposer de lancer ou non l'automatisme complet

Comportement :

- `Oui` :
  - accepte la demande
  - demande `Validation = oui`
  - active `Diffusable`
  - applique les passerelles par defaut
- `Non` :
  - accepte la demande
  - ne lance pas l'automatisme Hektor

En cas de refus Hektor :

- la demande ne doit pas etre acceptee comme si tout etait OK
- popup de refus avec explication
- lien Hektor vers la fiche mandat / prix

Format du lien Hektor attendu dans les popups de refus :

```text
https://groupe-gti-immobilier.la-boite-immo.com/admin/?page=/mes-biens/mon-bien/mandat-prix&id=24113
```

Le `id` est remplace par l'identifiant annonce Hektor du dossier concerne.

## 3. Popups et design

Les popups accessibles depuis `Action` ont ete harmonisees :

- demande de validation classique
- demande de baisse de prix
- demande d'annulation de mandat
- console de diffusion

Objectif :

- design plus professionnel
- mise en page moderne
- pictogrammes visuels
- conserver les textes et fonctions metier existants

Important :

- les textes fonctionnels demandes ne doivent pas etre changes sans validation
- les popups doivent rester des confirmations metier, pas des pages explicatives

## 4. Passerelles listing / detail

Probleme observe :

- incoherence possible entre listing et fiche detail sur les passerelles affichees
- exemple discute : id `59624`
- question particuliere : `Leboncoin` visible / non visible selon les zones

Correctif applique :

- affichage prioritaire des passerelles importantes :
  - `LBC`
  - `BI`
  - `GTI`
- puis completer avec les autres passerelles
- afficher un compteur du type `+2` apres les premieres passerelles visibles

Objectif :

- rendre le listing plus lisible
- eviter qu'une passerelle importante soit masquee par une passerelle secondaire
- rapprocher le listing de la synthese detail

## 5. Demande d'annulation de mandat

### Type dedie

La demande d'annulation de mandat a son propre type :

- `request_type = demande_annulation_mandat`

Elle ne doit pas etre confondue avec :

- `demande_diffusion`
- `demande_baisse_prix`

Des alias defensifs ont ete ajoutes cote front pour limiter les erreurs si une ancienne donnee locale est mal nommee :

- `annulation_mandat`
- `demande_annulation`
- `mandate_cancellation`

### Creation

Le negociateur peut creer une demande d'annulation uniquement si le mandat / l'annonce est deja valide cote diffusion.

Exception importante :

- si une demande d'annulation existe deja, elle doit rester ouvrable meme si l'etat local `Validation` ou `Diffusable` est devenu incoherent
- cela permet de corriger / traiter une demande sans perdre l'acces au bon popup

### Numerotation et suivi

La demande d'annulation :

- utilise son propre type
- garde son numero de demande
- apparait dans la vue `Suivi des mandats`
- apparait comme demande a traiter pour Pauline
- apparait dans l'historique du detail annonce
- doit faire evoluer le bouton `Action` selon son statut :
  - ajouter
  - envoyee
  - en cours
  - a corriger
  - acceptee
  - refusee

### Refus Pauline

Si Pauline refuse une demande d'annulation :

- la demande passe au statut refuse
- le motif / message est enregistre
- un email commercial est envoye si un email negociateur existe
- aucune action Hektor automatique n'est lancee
- `Validation` et `Diffusable` ne doivent pas etre modifies

### Acceptation Pauline avant dernier correctif

Premier comportement stabilise :

- acceptation administrative de la demande
- email commercial
- aucun appel Hektor
- aucune modification de `Validation`
- aucune modification de `Diffusable`
- aucune modification des passerelles

Ce comportement a ete mis en place pour corriger le bug ou une demande d'annulation pouvait faire planter l'app locale et decocher a tort `Valide` / `Diffuse`.

Commit principal :

- `16a2428` - `Isolate mandate cancellation decisions`

### Acceptation Pauline actuelle

Comportement actuel apres le dernier correctif :

1. Pauline clique `Accepter` depuis `Suivi des mandats`
2. une popup de confirmation apparait
3. la popup propose :
   - `Oui`
   - `Non`

Comportement `Non` :

- accepte la demande d'annulation
- envoie l'email commercial si disponible
- ne lance aucun automatisme Hektor
- ne modifie pas `Validation`
- ne modifie pas `Diffusable`

Comportement `Oui` :

- accepte la demande d'annulation
- envoie l'email commercial si disponible
- tente de decocher `Diffusable` via Hektor
- tente de decocher `Validation` via Hektor
- met a jour l'etat local listing / detail avec les valeurs observees

En cas d'erreur Hektor lors du decochement :

- la demande reste acceptee
- l'app affiche un message indiquant que `Valide/Diffuse` n'ont pas pu etre decoches
- cela evite de perdre la decision administrative Pauline

Commit principal :

- `19180d4` - `Confirm mandate cancellation unpublish`

## 6. Isolation des flux par type

Correctif important :

- chaque demande doit etre traitee selon son `request_type`
- une demande d'annulation ne doit jamais passer dans le flux validation classique
- une demande de baisse de prix ne doit jamais passer dans le flux validation classique

Protection ajoutee :

- le type effectif du popup est transmis a `handleUpdateDiffusionRequest`
- le handler utilise ce type comme reference
- une demande d'annulation sort par un chemin dedie

Objectif :

- eviter les popups incorrectes
- eviter les actions Hektor non voulues
- eviter que le bouton `Action` ouvre le mauvais flux

## 7. Verifications realisees

Verifications lancees apres correctifs :

```text
npx.cmd tsc -b
npm.cmd run build
```

Resultat :

- TypeScript OK
- build Vite OK

Note technique :

- `npm run build` via PowerShell peut etre bloque par `npm.ps1`
- utiliser `npm.cmd run build` dans ce contexte Windows

## 8. Points de vigilance

### Donnees deja abimees avant correctif

Si une annonce a deja ete decochee par l'ancien bug avant `16a2428`, le correctif empeche que cela recommence mais ne restaure pas automatiquement l'etat historique.

Action possible :

- resynchroniser le dossier
- ou remettre manuellement `Validation` / `Diffusable` selon Hektor

### Tests locaux reels

Cas deja cites pendant le clavardage :

- id `24113`
- id `59624`

Ces ids ont servi a illustrer les problemes mais ne doivent pas etre reutilises comme donnees de test persistantes sans nettoyage.

### Donnees de test

La demande etait de supprimer les essais sur des annonces, pas de supprimer les fonctions ou boutons.

Regle retenue :

- nettoyer les demandes de test si necessaire
- conserver les workflows fonctionnels
- ne pas retirer les actions metier

## 9. Etat fonctionnel resume

Etat attendu aujourd'hui :

- validation classique :
  - popup Oui / Non
  - `Oui` lance validation + diffusable + passerelles
  - `Non` accepte sans automatisme
- baisse de prix :
  - controle prix Hektor obligatoire avant acceptation
  - refus si prix different
  - popup Oui / Non si prix confirme
  - ne doit pas decocher une annonce deja validee / diffusee
- annulation de mandat :
  - type dedie
  - presente dans `Suivi des mandats`
  - historique detail annonce
  - bouton action coherent
  - refus = email + aucune action Hektor
  - acceptation = popup Oui / Non
  - `Oui` tente de decocher `Valide` et `Diffuse`
  - `Non` accepte sans automatisme
