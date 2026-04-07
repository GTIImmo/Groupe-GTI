# Reprise sync 21/03/2026

## Objet

Documenter la refonte du pipeline principal apres reprise de la logique `ACTIF` pour la partie annonces / contacts, et simplification de la partie transactionnelle.

## Changement de logique general

Le script principal `sync_raw.py` a ete refondu.

Nouvelle logique retenue :

- annonces + contacts :
  - logique de sync inspiree de `ACTIF`
  - gestion d'un premier run de bootstrap
  - gestion des updates quotidiennes via etat local
- transactions :
  - conservation du pipeline principal
  - mais simplification forte de la collecte sur :
    - offres
    - compromis
    - ventes

## Annonces

### Source retenue

- `ListAnnonces archive=0`
- `ListAnnonces archive=1`

### Logique retenue

- stockage d'un etat local dans la base :
  - `sync_annonce_state`
- comparaison locale par :
  - `hektor_annonce_id`
  - `datemaj`
- si base vide :
  - bootstrap automatique
  - recharge complet du parc annonces
- si base non vide :
  - mode update pilote par le delta local

### Details annonces

- `AnnonceById` reste la source de verite detaillee
- il est rejoue seulement sur les annonces utiles :
  - nouvelles
  - modifiees
  - liees a des contacts modifies

## Contacts

### Source retenue

- `ListContacts`
- tri retenu :
  - `sort=dateLastTraitement`
  - `way=DESC`

### Logique retenue

- stockage d'un etat local dans la base :
  - `sync_contact_state`
- detection des contacts modifies par :
  - `dateLastTraitement`
- rattachement annonce/contact stocke dans :
  - `sync_annonce_contact_link`
- si un contact change :
  - on ne rejoue pas `ContactById`
  - on retrouve les annonces qui le referencent
  - on rejoue `AnnonceById` sur ces annonces

### Decision importante

`ContactById` n'est plus utilise dans le pipeline principal.

La source de verite retenue pour les contacts lies a une annonce devient :

- le bloc contact present dans `AnnonceById`

## Mandats

La logique mandat detaillee est conservee.

Le script continue a utiliser :

- `ListMandat`
- `MandatById`
- `MandatsByIdAnnonce`

## Offres

### Ancienne logique

- `ListOffres`
- puis `OffreById` systematique

### Nouvelle logique

- `ListOffres` devient la source principale
- `OffreById` n'est plus rejoue systematiquement

### Raison

Les tests API ont montre que sur l'instance :

- `ListOffres` embarque deja un objet riche
- la structure observee est equivalente au detail `OffreById` sur l'echantillon teste

### Consequence normalize

La normalized travaille maintenant directement a partir du listing offre.

### Nouveau champ derive

Ajout d'une lecture metier :

- `offre_state`

Regle actuelle :

- si `propositions` contient `type = accepte` :
  - `offre_state = accepted`
- sinon si `propositions` contient `type = proposition` :
  - `offre_state = proposed`
- sinon :
  - `offre_state = NULL`

Ajout aussi de :

- `offre_event_date`

But :

- conserver la date d'evenement la plus utile issue de `propositions`
- mieux classer les offres lors du build

## Compromis

### Ancienne logique

- `ListCompromis`
- puis `CompromisById` systematique

### Nouvelle logique

- `ListCompromis` devient la source principale
- `CompromisById` n'est plus rejoue systematiquement

### Raison

Les tests API ont montre que sur l'instance :

- `ListCompromis` embarque deja un objet riche
- la structure observee est equivalente a `CompromisById` sur l'echantillon teste
- le listing contient deja :
  - `annonce`
  - `mandat`
  - `mandants`
  - `acquereurs`
  - dates
  - montants
  - `status`

### Nouveau champ derive

Ajout d'une lecture metier :

- `compromis_state`

Regle actuelle :

- `status = 1` :
  - `compromis_state = active`
- `status = 2` :
  - `compromis_state = cancelled`
- autre valeur :
  - `compromis_state = NULL`

Le champ brut `status` est conserve.

## Ventes

### Ancienne logique

- `ListVentes`
- puis `VenteById` systematique

### Nouvelle logique

- `ListVentes` devient la source principale
- `VenteById` n'est plus rejoue systematiquement

### Hypothese retenue

La meme simplification a ete appliquee que pour offres et compromis afin d'alleger fortement le run transactionnel.

### Point de vigilance

La validation empirique de `ListVentes` reste moins documentee que pour offres et compromis.

Si un manque metier apparait sur les ventes :

- reouvrir un mode fallback `VenteById`
- mais ne pas le remettre par defaut sans preuve de besoin

## Normalize

`normalize_source.py` a ete adapte :

- offres :
  - lecture directe depuis le listing
  - ajout :
    - `offre_state`
    - `offre_event_date`
- compromis :
  - lecture directe depuis le listing
  - ajout :
    - `compromis_state`
- ventes :
  - lecture directe depuis le listing

## Build

`build_case_index.py` a ete adapte pour mieux choisir la transaction de reference.

### Ranking offre

Priorite retenue :

- `accepted`
- puis `proposed`
- puis le reste
- puis date la plus recente

### Ranking compromis

Priorite retenue :

- `active`
- puis `cancelled`
- puis le reste
- puis `date_start` la plus recente

### Ventes

Le choix reste base sur la date la plus recente.

## Watch

`sync_progress.py` a ete realigne avec la nouvelle logique.

Changements :

- suppression du faux suivi des details :
  - contacts
  - offres
  - compromis
  - ventes
- conservation du detail :
  - annonces
  - mandats
- ajout des endpoints `_update` dans la lecture de progression

## Nouvelles tables techniques

Ajoutees dans `hektor_pipeline/common.py` :

- `sync_meta`
- `sync_annonce_state`
- `sync_contact_state`
- `sync_annonce_contact_link`

But :

- piloter le bootstrap
- piloter les updates
- garder le lien local annonces / contacts

## Commande de bootstrap propre

```powershell
.\.venv\Scripts\python.exe sync_raw.py --purge --mode update --max-pages 0 --detail-limit 0 --no-with-offer-status --no-with-compromis-status --vente-date-start 2010-01-01 --vente-date-end 2030-12-31
```

Puis :

```powershell
.\.venv\Scripts\python.exe normalize_source.py
```

Puis :

```powershell
.\.venv\Scripts\python.exe build_case_index.py
```

## Commande de suivi

```powershell
.\.venv\Scripts\python.exe sync_progress.py --watch 1
```

## Point de vigilance apres prochain run complet

Verifier en priorite :

- que les volumes offres / compromis / ventes restent coherents sans `ById`
- que `offre_state` est bien alimente sur les offres avec `propositions`
- que `compromis_state` est bien alimente sur les compromis avec `status`
- que le build choisit mieux la transaction de reference

## Correctif ajoute apres analyse du bootstrap

Constat realise apres le premier bootstrap :

- de nombreuses annonces presentes en transaction etaient absentes de `hektor_annonce`
- verification live faite :
  - plusieurs IDs manquants existaient bien dans `ListAnnonces`
  - ils avaient donc ete sautes pendant le bootstrap

Cause retenue :

- le bootstrap utilisait un tri de type update :
  - `sort=datemaj`
  - `way=DESC`
- sur un run long, ce tri est instable
- des objets peuvent bouger entre les pages et etre sautes

Correctif applique dans `sync_raw.py` :

- bootstrap annonces :
  - `sort=id`
  - `way=ASC`
- bootstrap contacts :
  - `sort=id`
  - `way=ASC`
- updates quotidiens inchanges :
  - annonces :
    - `sort=datemaj`
    - `way=DESC`
  - contacts :
    - `sort=dateLastTraitement`
    - `way=DESC`

## Commande de rattrapage sans purge

Si la base existe deja mais que le bootstrap initial a saute des annonces, lancer un rescan complet stable sans tout supprimer :

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode full --max-pages 0 --detail-limit 0 --no-with-offer-status --no-with-compromis-status --vente-date-start 2010-01-01 --vente-date-end 2030-12-31
```

Puis relancer :

```powershell
.\.venv\Scripts\python.exe normalize_source.py
```

Puis :

```powershell
.\.venv\Scripts\python.exe build_case_index.py
```
