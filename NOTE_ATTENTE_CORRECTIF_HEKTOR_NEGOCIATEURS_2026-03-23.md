# Note attente correctif Hektor - negociateurs manquants

Date : `2026-03-23`

## Constat

Un controle sur la phase 1 montre qu'une partie des annonces ne peut pas etre enrichie correctement avec le negociateur affiche.

Sur `case_dossier_source` :

- total dossiers : `56100`
- sans negociateur affichable : `32773`

Detail :

- sans `hektor_negociateur_id` : `31966`
- avec `hektor_negociateur_id` mais sans nom/prenom : `807`

Les `807` cas avec ID mais sans nom se repartissent ainsi :

- `23` : `712`
- `0` : `94`
- `93` : `1`

## Verification API / phase 1

Le controle montre que :

- les annonces peuvent porter un `hektor_negociateur_id`
- mais le referentiel `hektor_negociateur` ne contient pas toujours la fiche correspondante
- l'endpoint API `listNegos` ne remonte pas tous les IDs utilises par les annonces

Cas confirmes :

- l'ID `23` est utilise par les annonces
- l'ID `93` est utilise par les annonces
- ni `23` ni `93` ne remontent via l'API `listNegos`

En revanche, l'API `listNegos` remonte bien `Vincent-Lucas GONZALEZ`, mais sous d'autres IDs :

- `95`
- `97`

Donc il existe un ecart entre :

- les IDs negociateur portes par les annonces / transactions
- et les IDs exposes par le referentiel API des negociateurs

## Conclusion

Le probleme est un probleme amont Hektor / API.

La phase 2 ne doit pas corriger localement ce point en reutilisant le commercial des passerelles comme verite de reference.

Decision retenue :

- ne pas completer localement les annonces sans negociateur par la liste des passerelles
- laisser visible l'ecart reel dans la phase 2
- attendre un correctif Hektor ou une explication de mapping cote API

## Consequence de travail

Pour l'instant :

- la phase 1 reste la reference
- la phase 2 n'ajoute plus de repli depuis `hektor_annonce_broadcast_state`
- le sujet doit etre remonte a Romain

## Message cle

Le point bloquant n'est pas un bug de l'interface.
Le point bloquant est un ecart entre les IDs negociateurs utilises par les annonces et ceux renvoyes par l'API negociateurs.
