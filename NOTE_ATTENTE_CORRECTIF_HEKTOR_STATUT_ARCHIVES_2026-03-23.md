# Note attente correctif Hektor - statuts archives

Date: 23/03/2026

## Objet

Documenter un point important de lecture des donnees phase 1 en attendant un correctif cote Hektor.

## Constat

L'analyse de la data montre un gros lot de dossiers avec le profil suivant :

- annonce archivee
- mandat present
- non diffusable
- pas de vente
- souvent pas d'offre ni de compromis
- `statut_name = 'Actif'`

Ce point perturbe actuellement le calcul des statuts globaux dans l'outil.

## Lecture metier retenue

Ces dossiers ne doivent pas etre interpretes comme une erreur de l'app.

La lecture retenue est :

- une partie importante de ces biens devrait en realite etre en `Clos`
- donc tomber ensuite en `Annule` dans l'app
- mais l'information `statut_name = 'Clos'` n'est pas encore correctement alimentee dans Hektor pour ces archives

## Decision retenue

En attendant le correctif Hektor :

- ne pas surcorriger localement ces dossiers
- ne pas les forcer artificiellement en `Annule`
- conserver la regle metier :
  - `Annule` = `statut_name = 'Clos'`

## Pourquoi ne pas surcorriger

Si l'app force ces cas trop tot en `Annule`, on risque :

- de produire une logique locale differente de la logique Hektor cible
- de classer a tort certains dossiers
- de devoir refaire la regle apres correction Hektor

## Regle de travail a retenir

Tant que Hektor n'a pas corrige ses statuts archives :

- `statut_name` reste la source retenue pour `Annule`
- les dossiers archives avec mandat, non vendus, encore marques `Actif` restent des cas en attente de correction amont

## Impact pratique sur l'app

Cela explique pourquoi il reste actuellement un bloc de dossiers sans `statut_global` propre dans la vue generale.

Ce bloc ne doit pas etre traite comme :

- une erreur du pipeline phase 1
- ni une erreur de la logique app

Il s'agit d'un effet temporaire de qualite de donnees cote Hektor.

## Point de reprise plus tard

Quand Hektor corrigera l'alimentation de `statut_name` sur les archives :

- relancer le recalcul de la vue generale
- verifier le basculement naturel des dossiers concernes vers :
  - `Annule`

## Conclusion

En attendant le correctif Hektor :

- on garde la logique actuelle
- on documente le trou de qualite de donnees
- on ne force pas artificiellement l'etat `Annule`
