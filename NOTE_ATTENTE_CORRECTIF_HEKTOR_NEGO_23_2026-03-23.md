# Note attente correctif Hektor - ID negociateur 23

Date : `2026-03-23`

## Constat retenu

Le point bloquant principal sur les negociateurs semble concentre sur l'ID `23`.

Constats verifies :

- des annonces Hektor portent `NEGOCIATEUR = 23`
- l'ID `23` est utilise sur `708` annonces
- le CRM Hektor semble bien afficher le collaborateur sur les fiches concernees
- en revanche, l'API `listNegos` ne renvoie pas l'ID `23`

Point de comparaison utile :

- `Vincent-Lucas GONZALEZ` remonte via `listNegos`
- mais sous les IDs `95` et `97`

## Lecture de travail

A ce stade, l'hypothese la plus prudente est :

- il existe une incoherence cote Hektor / API sur l'ID negociateur `23`
- ce point ne doit pas etre corrige artificiellement dans la surcouche locale

## Decision retenue

Comme pour les autres anomalies de source Hektor :

- ne pas corriger localement la phase 1
- ne pas completer localement les annonces a partir d'une source de substitution
- documenter le point
- attendre un correctif Hektor ou une clarification de mapping

## Consequence

Pour l'instant :

- l'ID `23` est considere comme une anomalie source Hektor
- la phase 2 reste strictement alignee sur la phase 1
- l'ecart reste visible dans l'outil tant que Hektor n'a pas corrige ou explique ce point
