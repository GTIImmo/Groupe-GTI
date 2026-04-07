# Definition vue 1 - Vue generale

Date: 23/03/2026

## Objet

Cette note redefine la premiere vue de l'outil.

La vue 1 ne doit plus etre la file Pauline.

La vue 1 doit devenir :

- la vue generale de l'outil

## Pourquoi ce changement

La premiere proposition etait de commencer par une vue `Demandes mandat / diffusion`.

Cette vue reste utile, mais elle n'est pas la meilleure porte d'entree principale.

Le besoin reel montre qu'il faut d'abord une vue centrale, transversale et partagee par tous les profils.

Cette vue generale doit permettre :

- de voir l'etat des dossiers
- de filtrer rapidement
- d'ouvrir ensuite la fiche dossier
- puis de basculer vers les vues specialisees

## Distinction importante

### Vue generale

Rôle :

- tableau central de pilotage
- lecture synthetique
- tri et filtres
- point d'entree principal

Granularite :

- 1 ligne = 1 dossier / bien / mandat

### Fiche dossier

Rôle :

- detail complet d'un dossier
- lecture approfondie
- historique
- notes
- relances
- diffusion detaillee
- suivi transactionnel

Conclusion :

- la vue generale ne remplace pas la fiche dossier
- elle sert a reperer puis a ouvrir la fiche dossier

## Role de la vue generale

La vue generale doit repondre vite aux questions suivantes :

- quel est ce bien ?
- qui le porte ?
- est-il valide ?
- est-il diffusable ?
- est-il reellement diffuse ?
- y a-t-il une offre, un compromis ou une vente ?
- y a-t-il un blocage ?
- faut-il agir ?

## Public cible

La vue generale doit etre utile a :

- Pauline
- Delphine
- les managers
- les negociateurs

Elle doit donc rester :

- synthétique
- transversale
- lisible

## Structure recommandees de la vue generale

### 1. Identification

- `hektor_annonce_id`
- `numero_dossier`
- `numero_mandat`
- `titre_bien`
- `ville`
- `type_bien`
- `prix`

But :

- identifier rapidement le dossier

### 2. Responsable

- `commercial_nom`
- `hektor_negociateur_id`

But :

- savoir qui porte le dossier

### 3. Etat annonce / mandat

- `statut_annonce`
- `archive`
- `diffusable`
- `valide`
- `mandat_type`
- `mandat_date_debut`
- `mandat_date_fin`
- `mandat_date_cloture`

But :

- lire rapidement le cadre administratif du bien

### 4. Diffusion

- `validation_diffusion_state`
- `etat_visibilite`
- `nb_portails_actifs`
- `has_diffusion_error`
- `portails_resume`

But :

- distinguer :
  - bien non valide
  - bien autorise
  - bien visible
  - bien en erreur

### 5. Transaction

- `offre_id`
- `compromis_id`
- `vente_id`
- `vente_date`
- `etat_transaction`

But :

- lire vite l'avancement transactionnel

### 6. Surcouche interne

- `internal_status`
- `priority`
- `has_open_blocker`
- `motif_blocage`
- `next_action`
- `date_relance_prevue`
- `commentaire_resume`

But :

- porter la logique interne qui n'existe pas dans Hektor

### 7. Etat global

Champ essentiel recommande :

- `etat_global_dossier`

Valeurs cibles possibles :

- `a_valider`
- `pret_diffusion`
- `diffuse`
- `offre_en_cours`
- `compromis_en_cours`
- `vente_en_cours`
- `termine`
- `bloque`

But :

- donner une lecture immediate et transversale du dossier

## Filtres indispensables

La vue generale doit pouvoir etre filtree au minimum par :

- commercial
- ville
- type de bien
- validation diffusion
- etat de visibilite
- etat global dossier
- priorite
- blocage
- offre / compromis / vente

## Actions attendues depuis la vue generale

La vue generale doit permettre :

- ouvrir la fiche dossier
- filtrer
- trier
- reperer les urgences
- reperer les blocages
- basculer vers une vue specialisee

Elle ne doit pas porter a elle seule tout le detail.

## Place des vues specialisees

La vue generale devient la vue 1.

Les vues specialisees deviennent des vues 2, 3, 4...

Ordre logique :

1. `Vue generale`
2. `Fiche dossier`
3. `Demandes mandat / diffusion`
4. `Diffusion passerelles`
5. `Suivi transaction`
6. `Pilotage global`

## Consequence de conception

Le modele de donnees doit maintenant privilegier :

- une vue centrale `app_view_generale`

Puis des vues derivees / specialisees.

La vue Pauline deja amorcee ne disparait pas.

Elle change simplement de statut :

- elle n'est plus la vue 1
- elle devient une vue specialisee

## Conclusion

La premiere vue de l'outil doit etre une vue generale, pas une file specialisee.

La logique retenue devient :

- vue 1 = tableau central des dossiers
- fiche dossier = detail
- vues specialisees = filtres et files metier
