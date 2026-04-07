# Note vues Mandats et push delta app

Date: 2026-03-27

## Objectif

Faire evoluer l'application sans toucher a la phase 1.

Le but est double :

- ajouter deux vues metier dediees aux mandats et a la diffusion
- ameliorer le mode de mise a jour de l'app pour eviter de repousser inutilement les details annonce lourds

La phase 1 reste la source de verite et n'est pas modifiee.

## Decision de cadrage

Le projet doit etre separe en deux couches de lecture distinctes :

- couche `Annonces`
- couche `Mandats / Diffusion`

La couche `Annonces` garde :

- le listing principal
- la fiche annonce detaillee
- les transactions
- les blocs riches issus du detail annonce

La couche `Mandats / Diffusion` sert a :

- suivre le parc mandats
- consulter les passerelles
- demander une diffusion
- traiter les demandes de diffusion
- suivre les erreurs et l'etat reel de diffusion

Ces deux usages n'ont pas le meme besoin de donnees ni le meme besoin de frequence de mise a jour.

## Vue 1 - Liste des mandats

Acces :

- tous les commerciaux

Usage :

- voir leurs mandats
- voir l'etat de diffusion
- voir les passerelles actives
- demander une diffusion a Pauline
- consulter ou modifier les passerelles selon les droits retenus

Contenu minimal recommande :

- numero dossier
- numero mandat
- titre bien
- ville
- commercial
- agence
- statut phase 1
- archive
- diffusable
- nb_portails_actifs
- portails_resume
- has_diffusion_error
- offre_id
- compromis_id
- vente_id
- statut demande diffusion
- date demande diffusion
- commentaire demande

Actions recommandees :

- `Demander diffusion`
- `Voir passerelles`
- `Modifier passerelles`

## Vue 2 - Suivi des mandats

Acces :

- administrateurs uniquement
- Pauline incluse

Usage :

- voir l'etat du parc mandat
- voir les demandes de diffusion emises par les commerciaux
- traiter les demandes
- surveiller les mandats diffusable non visibles
- surveiller les erreurs diffusion

Contenu minimal recommande :

- tout ou partie du stock mandat courant
- file des demandes diffusion
- statut de traitement
- auteur de la demande
- date de la demande
- priorite
- erreurs diffusion
- mandats sans diffusion active
- mandats diffusable non visibles

Actions recommandees :

- `Prendre en charge`
- `Traitee`
- `Refuser`
- `Commenter`
- `Mettre a jour les passerelles`

## Regle importante

Ces deux vues ne doivent pas dependre du detail annonce lourd.

Le detail annonce actuel contient :

- images
- textes
- proprietaires
- notes
- contenu JSON lourd

Ces informations sont inutiles pour les vues mandats / diffusion. Il ne faut donc pas les inclure dans leur pipeline de mise a jour rapide.

## Architecture cible sans toucher a la phase 1

La phase 1 reste intacte.

Les changements se font uniquement dans la couche app / Supabase / phase 2 applicative.

Il faut creer une couche `current` pour l'exploitation quotidienne.

### Tables cibles recommandees

#### 1. `app_dossier_current`

Role :

- stock courant complet des annonces lues par l'app

Contient :

- une ligne courante par dossier
- sans logique snapshot obligatoire pour la lecture

Utilisation :

- vue Annonces
- filtres globaux
- base de pilotage

#### 2. `app_dossier_detail_current`

Role :

- fiche annonce detaillee

Contient :

- une ligne courante par dossier
- detail lourd conserve a part

Utilisation :

- seulement pour la vue detail annonce

#### 3. `app_work_item_current`

Role :

- file de travail metier courante

Contient :

- demandes et actions operationnelles

Utilisation :

- vues transverses
- suivi administratif

#### 4. `app_mandat_current`

Role :

- source principale des deux nouvelles vues Mandats

Contient uniquement les champs utiles mandat / diffusion :

- dossier
- mandat
- commercial
- agence
- statut phase 1
- archive
- diffusable
- nb_portails_actifs
- portails_resume
- has_diffusion_error
- offre_id
- compromis_id
- vente_id
- dates de mise a jour

Cette table doit etre legere et rapide a recalculer.

#### 5. `app_mandat_broadcast_current`

Role :

- vue detaillee des passerelles par annonce

Une ligne =

- un dossier ou une annonce
- une passerelle

Contient :

- annonce_id
- app_dossier_id
- passerelle_key
- current_state
- export_status
- is_success
- is_error
- commercial_id
- commercial_nom

Utilisation :

- filtre par passerelle
- consultation precise de la diffusion
- actions futures de modification passerelles

#### 6. `app_mandat_diffusion_request_current`

Role :

- demandes de diffusion emises par les commerciaux

Contient :

- request_id
- app_dossier_id
- demandeur
- date_demande
- statut_demande
- commentaire_demande
- traite_par
- date_traitement
- commentaire_traitement

Utilisation :

- vue Suivi des mandats
- vue Liste des mandats

#### 7. `app_filter_catalog_current_store`

Role :

- catalogue courant des filtres

Remarque :

- il doit etre reconstruit depuis les tables courantes
- il ne doit pas dependre d'un snapshot incomplet

#### 8. `app_delta_run`

Role :

- journal des mises a jour delta

Contient :

- id
- started_at
- finished_at
- status
- scope
- dossiers_impactes
- dossiers_rebuild
- details_rebuild
- mandats_rebuild
- work_items_rebuild
- notes

## Vues app recommandees

L'app devrait ensuite lire :

- `app_dossiers_current`
- `app_dossier_details_current`
- `app_work_items_current`
- `app_mandats_current`
- `app_mandat_broadcasts_current`
- `app_mandat_diffusion_requests_current`
- `app_filter_catalog_current`

Important :

- ces vues ne doivent plus etre basees uniquement sur `app_latest_sync_run`
- elles doivent pointer vers les tables `current`

## Strategie de push recommandee

## 1. Push global lourd

Conserver un mode snapshot complet pour :

- reconstruction
- audit
- secours
- reprise apres incident

Ce push global garde son utilite pour :

- `app_dossier_v1`
- `app_dossier_detail_v1`
- `app_work_item_v1`
- `app_filter_catalog_v1`

Mais il ne doit plus etre la seule maniere de tenir l'app a jour.

## 2. Push delta courant

Ajouter un vrai mode delta pour la lecture quotidienne.

Principe :

- detecter les dossiers impactes
- recalculer uniquement les lignes courantes necessaires
- faire des upserts dans les tables `current`
- reconstruire le catalogue de filtres

## 3. Push rapide Mandats / Diffusion

Pour les deux nouvelles vues, ajouter un mode de mise a jour plus rapide.

Ce mode ne doit pas toucher :

- `app_dossier_detail_current`

Il doit mettre a jour seulement :

- `app_mandat_current`
- `app_mandat_broadcast_current`
- `app_mandat_diffusion_request_current`
- `app_filter_catalog_current_store`

Ce sera le mode de refresh privilegie pour Pauline et pour les commerciaux.

## Detection delta recommandee

Le delta doit se baser sur les evolutions phase 1 deja existantes, sans changer la phase 1.

Sources de changement a surveiller :

- annonce modifiee via `datemaj`
- mandat modifie
- offre modifiee
- compromis modifie
- vente modifiee
- changement de diffusion par passerelle
- changement de commercial ou affectation si deja remonte

## Comportement attendu

Le mode delta ne cree pas une petite table des modifications.

Il met a jour une table `current` complete.

Exemple :

- `app_mandat_current` contient tout le stock courant
- le delta recalcule 120 dossiers impacts
- le delta remplace seulement ces 120 lignes
- a la fin, la table contient toujours tout le stock

Donc l'app peut lire `current` sans perdre les annonces non modifiees.

## Droits et acces

### Liste des mandats

Accessible :

- commerciaux
- perimetre a limiter selon le profil si besoin

Actions :

- demander une diffusion
- consulter les passerelles
- modifier les passerelles si droit autorise

### Suivi des mandats

Accessible :

- administrateurs

Actions :

- traiter les demandes de diffusion
- suivre le parc mandat
- surveiller erreurs et visibilite
- piloter les actions administratives

## Rythme de mise a jour recommande

### Quotidien ou plusieurs fois par jour

- mode delta Mandats / Diffusion
- mode delta courant global leger

### Nuit ou hebdomadaire

- snapshot global complet

Cette separation permet :

- des mises a jour rapides pour le metier
- une reconstruction complete quand necessaire

## Benefices attendus

- moins de dependance au detail annonce lourd
- mises a jour plus rapides
- moins de risques de timeout sur Supabase
- vues Mandats mieux adaptees au besoin reel
- Pauline dispose d'une vraie file de suivi diffusion
- les commerciaux disposent d'une vue simple et exploitable
- l'app garde un stock complet courant

## Point d'attention

La mise en place du mode delta ne doit pas etre comprise comme :

- une table qui ne contient que les mises a jour

Le bon modele est :

- `current` = stock complet courant
- `delta` = mecanisme de mise a jour partielle du stock complet

## Prochaine etape recommande

1. creer la couche `current` cote app
2. creer les tables `app_mandat_*_current`
3. creer les deux nouvelles vues UI
4. brancher les droits d'acces
5. separer les commandes :
   - push global complet
   - push delta courant
   - push rapide Mandats / Diffusion

## Conclusion

La bonne direction est :

- ne pas toucher a la phase 1
- garder la phase 1 comme source de verite
- faire evoluer uniquement la couche app / Supabase / phase 2 applicative
- separer le besoin Annonces detaillees du besoin Mandats / Diffusion
- ajouter un vrai mode delta courant
- conserver un snapshot global complet pour la reconstruction
