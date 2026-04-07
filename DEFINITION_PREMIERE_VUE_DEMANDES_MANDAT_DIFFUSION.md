# Definition premiere vue - Demandes mandat / diffusion

Date: 23/03/2026

## Objet

Cette note definit la premiere vue metier a construire dans la surcouche :

- `Demandes mandat / diffusion`

Cette vue est prioritaire car elle sert de file de travail principale pour Pauline.

## Finalite de la vue

La vue doit permettre a Pauline de voir en un seul endroit tous les dossiers qui demandent une decision, un controle ou un suivi administratif autour :

- de la diffusion
- des avenants
- des annulations
- des mandats generes mais pas encore visibles

## Une ligne = un dossier a traiter

La granularite retenue est :

- 1 ligne = 1 dossier / bien / mandat actuellement a traiter

La vue n'a pas pour but d'afficher tout le parc.

Elle doit afficher seulement les dossiers qui ont une raison d'etre presents dans la file de travail.

## Cas metier a faire remonter dans la vue

Les cas prioritaires a couvrir sont :

- demande de diffusion
- avenant baisse de prix
- annulation de mandat
- mandat genere mais pas encore diffuse
- bien non visible mais non annule
- dossier refuse en attente de correction
- dossier bloque pour piece manquante ou donnee incomplete

## Nom de vue recommande

Nom SQL recommande :

- `app_view_demandes_mandat_diffusion`

## Structure fonctionnelle de la vue

### Identite dossier

- `app_dossier_id`
- `hektor_annonce_id`
- `hektor_mandat_id`
- `numero_dossier`
- `numero_mandat`

But :

- identifier sans ambiguite le dossier

### Identification bien

- `titre_bien`
- `ville`
- `type_bien`
- `prix_affiche`
- `archive`

But :

- reconnaitre rapidement le bien sans ouvrir la fiche detail

### Attribution commerciale

- `commercial_id`
- `commercial_nom`

But :

- savoir qui porte le dossier

### Qualification de la demande

- `workflow_type`
- `event_type`
- `type_demande_label`

But :

- comprendre pourquoi la ligne est dans la file

Valeurs attendues pour `event_type` :

- `demande_diffusion`
- `baisse_prix`
- `annulation_mandat`
- `mandat_non_diffuse`
- `bien_non_visible`
- `piece_manquante`
- `donnee_incomplete`

Valeurs attendues pour `type_demande_label` :

- `Demande diffusion`
- `Avenant baisse prix`
- `Annulation mandat`
- `Mandat non diffuse`
- `Bien non visible`
- `Piece manquante`
- `Donnee incomplete`

### Statut de traitement

- `work_status`
- `internal_status`
- `priority`

But :

- savoir ou en est le traitement administratif

Valeurs recommandees pour `work_status` :

- `new`
- `pending`
- `in_progress`
- `done`
- `refused`

Valeurs recommandees pour `internal_status` :

- `a_controler`
- `en_attente_commercial`
- `pret_diffusion`
- `bloque`

Valeurs recommandees pour `priority` :

- `low`
- `normal`
- `high`
- `urgent`

### Lecture diffusion / visibilite

- `diffusable`
- `validation_diffusion_state`
- `etat_visibilite`
- `nb_portails_actifs`
- `has_diffusion_error`

But :

- distinguer les cas :
  - non valides
  - valides mais non visibles
  - visibles
  - en erreur

Sens metier recommande :

- `validation_diffusion_state`
  - `a_controler`
  - `valide`
  - `refuse`
  - `en_attente_commercial`

- `etat_visibilite`
  - `non_diffusable`
  - `diffusable_non_visible`
  - `visible`
  - `en_erreur`
  - `a_verifier`

### Blocage / raison

- `motif_blocage`
- `reason`
- `has_open_blocker`

But :

- afficher tout de suite pourquoi le dossier ne peut pas avancer

### Action / suivi

- `next_action`
- `last_action_note`
- `date_relance_prevue`
- `date_derniere_action`
- `date_entree_file`
- `age_jours`

But :

- piloter le traitement et les retards

### Resume commentaire

- `commentaire_admin_resume`

But :

- voir la derniere information utile sans ouvrir la fiche dossier

## Champs finaux recommandes

Je recommande ce jeu de colonnes comme V1 concrete :

- `app_dossier_id`
- `hektor_annonce_id`
- `numero_dossier`
- `numero_mandat`
- `titre_bien`
- `ville`
- `type_bien`
- `prix_affiche`
- `commercial_nom`
- `type_demande_label`
- `work_status`
- `validation_diffusion_state`
- `diffusable`
- `etat_visibilite`
- `priority`
- `motif_blocage`
- `next_action`
- `date_relance_prevue`
- `date_entree_file`
- `age_jours`
- `commentaire_admin_resume`

## Ordre de tri recommande

Tri conseille par defaut :

1. `priority` decroissante
2. `age_jours` decroissant
3. `date_entree_file` croissante

But :

- faire remonter d'abord l'urgent
- puis l'ancien

## Filtres indispensables

La vue doit au minimum permettre de filtrer par :

- type de demande
- statut de traitement
- statut validation diffusion
- priorite
- commercial
- biens diffuses / non diffuses
- dossiers bloques
- dossiers en attente commercial

## Actions attendues depuis la vue

La vue doit permettre rapidement :

- ouvrir la fiche dossier
- valider
- refuser
- mettre en attente
- marquer un blocage
- ajouter une note
- definir une prochaine action

## Provenance des donnees

### Depuis la phase 1

Donnees a lire depuis la base principale :

- `case_dossier_source`
- tables annonce / mandat / diffusion consolidees

### Depuis la surcouche locale

Donnees a lire depuis les tables locales :

- `app_dossier`
- `app_work_item`
- `app_internal_status`
- `app_note`
- `app_blocker`
- `app_followup`

## Regles de presence dans la vue

Un dossier apparait dans la vue si au moins une condition est vraie :

- il existe un `app_work_item` actif de type `mandat_diffusion`
- il est en attente de validation diffusion
- il est marque bloque
- il est refuse en attente de correction
- il est diffusable mais non visible

## Exemple de logique SQL de selection

Logique cible a respecter :

- base = `app_work_item` ouverts du workflow `mandat_diffusion`
- enrichissement = `app_dossier` + `case_dossier_source`
- enrichissement = statut interne + blocages + derniere note admin
- calcul = `age_jours`, `etat_visibilite`, resume commentaire

## Role de cette vue dans la V1

Cette vue est la premiere file de travail du projet.

Elle doit devenir :

- le tableau quotidien de Pauline
- le point de reference pour la validation administrative de diffusion
- le modele de conception pour les autres vues metier

## Conclusion

La premiere vue ne doit pas etre une simple liste de biens.

Elle doit etre une vraie file de traitement orientee decision, delai et blocage.
