# Règle Responsable d'Affichage

Date : 2026-03-23

## Principe

Dans la mini-app phase 2, le champ affiché comme responsable suit une règle locale de présentation :

- si le négociateur est connu dans `case_dossier_source`, on affiche le négociateur ;
- sinon, si l'agence est connue, on affiche l'agence ;
- sinon, on affiche `Non attribué`.

## Objet

Cette règle ne modifie pas la donnée Hektor.

Elle sert uniquement à améliorer la lecture métier dans l'interface quand une annonce n'a pas de négociateur exploitable, tout en évitant de fabriquer un faux négociateur.

## Source de vérité

- négociateur : phase 1 (`case_dossier_source`)
- agence : phase 1 (`hektor_agence`)
- choix d'affichage : phase 2 uniquement

## Important

- on ne complète pas le négociateur avec les commerciaux présents dans les passerelles ;
- on ne corrige pas localement l'anomalie Hektor sur l'ID négociateur `23` ;
- cette règle est un repli d'affichage, pas une correction de référentiel.

## Valeurs produites

- `responsable_type = negociateur`
- `responsable_type = agence`
- `responsable_type = non_attribue`

- `responsable_affichage = nom du négociateur`
- ou `responsable_affichage = nom de l'agence`
- ou `responsable_affichage = Non attribué`

## Portée actuelle

Cette règle est intégrée dans la mini-app HTML phase 2, notamment sur :

- le filtre responsable ;
- la colonne responsable du stock global ;
- la colonne responsable des vues diffusion et transaction ;
- la fiche rapide du dossier.
