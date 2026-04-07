# Regle Sans Mandat

Date: 23/03/2026

## Objet

Cette note fixe la regle de calcul du statut global `Sans mandat`.

## Regle retenue

Le statut global `Sans mandat` doit etre calcule ainsi :

- `mandat_id IS NULL`
- et aucun statut plus prioritaire ne doit deja s'appliquer

## Point important

`statut_name` ne doit pas etre utilise pour calculer `Sans mandat`.

Exception unique conservee :

- `Annule` continue d'utiliser `statut_name = 'Clos'`

En dehors de ce cas :

- `statut_name` n'entre pas dans la regle `Sans mandat`

## Priorite de calcul retenue

Ordre de priorite avant `Sans mandat` :

1. `Vendu`
2. `Annule`
3. `Vente fixee`
4. `Compromis signe`
5. `Compromis fixe`
6. `Offre recue`
7. `Diffuse`
8. `Valide`
9. `A valider`
10. `Sans mandat`

## Sous-statuts retenus

Quand `statut_global = 'Sans mandat'` :

- `Estimation` si `mandat_id IS NULL` et `statut_name = 'Estimation'`
- `Mandat attendu` sinon

## But

Eviter que des dossiers sans mandat restent non qualifies alors qu'ils doivent tomber en `Sans mandat`.
