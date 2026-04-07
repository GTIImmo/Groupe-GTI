# Correspondance statuts globaux

Date: 23/03/2026

## Objet

Cette note fixe les premieres correspondances entre les statuts globaux metier et la data disponible.

But :

- eviter les interpretations techniques floues
- separer le statut global du dossier et les alertes
- documenter ce qui vient de la phase 1 et ce qui devra venir de la phase 2

## Principe general

Le `statut_global` doit decrire l'etape principale du dossier dans son cycle metier.

Il ne doit pas melanger :

- progression metier du dossier
- alertes
- relances
- erreurs

Les alertes comme :

- `Bloque`
- `A relancer`
- `Erreur diffusion`

doivent rester des alertes ou des flags, pas des statuts globaux.

## Liste de statuts globaux retenue

Ordre metier retenu :

1. `Sans mandat`
2. `A valider`
3. `Valide`
4. `Diffuse`
5. `Offre recue`
6. `Compromis fixe`
7. `Compromis signe`
8. `Vente fixee`
9. `Vendu`
10. `Annule`

## Correspondances validees a ce stade

### 1. A valider

Interpretation metier :

- le commercial a demande une validation de diffusion
- Pauline doit controler le dossier

Point important :

- ce statut ne peut pas etre calcule proprement depuis Hektor seul
- il devra venir de la surcouche metier phase 2

Conclusion :

- `A valider` = donnee locale phase 2
- pas une deduction directe de `diffusable = 0`

### 2. Valide

Interpretation metier :

- le dossier est autorise a etre diffuse

Correspondance retenue :

- `diffusable = 1`

Source :

- `case_dossier_source.diffusable`

Conclusion :

- `Valide` = `diffusable = 1`

### 3. Diffuse

Interpretation metier :

- le dossier est valide
- et il est effectivement diffuse sur au moins une passerelle

Correspondance retenue :

- `diffusable = 1`
- et au moins une diffusion reelle active

Lecture metier :

- `Diffuse` implique deja `Valide`
- mais tous les `Valide` ne sont pas encore `Diffuse`

Source technique :

- `case_dossier_source.diffusable = 1`
- plus `hektor_annonce_broadcast_state.current_state = 'broadcasted'` sur au moins une ligne

Conclusion :

- `Diffuse` = `diffusable = 1` + effectivement diffuse

## Observation utile sur les champs existants

Les releves faits sur la base montrent :

Dans `case_dossier_source` :

- `diffusable = 1` : `1308`
- `diffusable = 0` : `54792`
- `valide = 1` : `1380`
- `valide = 0` : `54720`

Conclusion utile :

- `valide = 1` est plus large que `diffusable = 1`
- donc `valide` ne semble pas etre le bon champ pour definir seul le statut global `Valide`
- le meilleur candidat retenu est bien `diffusable`

## Regle de priorite

Le statut global affiche doit etre le statut metier le plus avance.

Exemple :

- un dossier `Diffuse` est deja `Valide`
- mais on doit afficher `Diffuse`, pas `Valide`

Donc :

- `Diffuse` a priorite sur `Valide`

## Ce qu'il reste a trancher

Les correspondances suivantes restent a travailler :

- `Sans mandat`
- `Offre recue`
- `Compromis fixe`
- `Compromis signe`
- `Vente fixee`
- `Vendu`
- `Annule`

## Conclusion

Les premieres regles solides retenues sont :

- `A valider` = surcouche phase 2
- `Valide` = `diffusable = 1`
- `Diffuse` = `diffusable = 1` + diffusion reelle sur au moins une passerelle
