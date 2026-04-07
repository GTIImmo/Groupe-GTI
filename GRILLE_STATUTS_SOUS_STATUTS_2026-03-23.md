# Grille statuts et sous-statuts

Date: 23/03/2026

## Objet

Cette note fixe une grille de travail pour :

- les statuts globaux
- les sous-statuts
- les regles de correspondance entre la data et la lecture metier

But :

- rendre la vue generale lisible
- separer le cycle metier, les sous-situations et les alertes

## Structure retenue

Pour chaque dossier, on distingue :

- `statut_global`
- `sous_statut`
- `alerte_principale`

### Statut global

Le statut global indique l'etape principale du dossier dans son cycle metier.

### Sous-statut

Le sous-statut precise la situation operationnelle a l'interieur du statut global.

### Alerte principale

L'alerte principale indique une attention ou un probleme :

- `Bloque`
- `A relancer`
- `Erreur diffusion`

Elle ne doit pas etre melangee avec le statut global.

## Statuts globaux retenus

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

## Grille detaillee

### 1. Sans mandat

Source principale :

- phase 1

Regle cible :

- `mandat_id IS NULL`

Sous-statuts proposes :

- `Estimation`
- `Mandat attendu`
- `Dossier incomplet`

### 2. A valider

Source principale :

- phase 2

Regle :

- demande explicite de validation creee par le commercial

Sous-statuts proposes :

- `Demande envoyee`
- `En controle Pauline`
- `En attente correction commercial`
- `Refuse`

### 3. Valide

Source principale :

- phase 1

Regle retenue :

- `diffusable = 1`

Sous-statuts proposes :

- `Non diffuse`
- `Pret a diffuser`
- `Choix passerelles a faire`

### 4. Diffuse

Source principale :

- phase 1

Regle retenue :

- `diffusable = 1`
- et diffusion reelle sur au moins une passerelle

Sous-statuts proposes :

- `Diffuse partiellement`
- `Diffuse multi-portails`
- `Diffusion minimale`
- `Diffusion a optimiser`

### 5. Offre recue

Source principale :

- phase 2

Regle :

- Delphine recoit l'offre par mail
- creation d'un evenement metier local

Sous-statuts proposes :

- `Mail recu`
- `A saisir`
- `Saisie en cours`
- `A relancer`

### 6. Compromis fixe

Source principale :

- phase 2

Regle :

- evenement metier local

Sous-statuts proposes :

- `Date fixee`
- `En attente signature`
- `Pieces en attente`

### 7. Compromis signe

Source principale :

- phase 1

Regle retenue :

- `compromis_id IS NOT NULL`
- `compromis_state = 'active'`
- `date_start` depassee

Sous-statuts proposes :

- `Acte a fixer`
- `Pret en attente`
- `Dossier notaire`
- `A relancer`

### 8. Vente fixee

Source principale :

- phase 2

Regle :

- evenement metier local

Sous-statuts proposes :

- `Date acte fixee`
- `Avant acte`
- `Pieces finales en attente`

### 9. Vendu

Source principale :

- phase 1

Regle retenue :

- `vente_id IS NOT NULL`

Sous-statuts proposes :

- `Vente recente`
- `A cloturer`
- `Cloture administrative`

### 10. Annule

Source principale :

- phase 1

Regle retenue :

- `statut_name = 'Clos'`

Point important :

- si `vente_id IS NOT NULL`, la priorite reste a `Vendu`
- `Clos` ne doit donc pas ecraser un dossier deja vendu

Sous-statuts retenus pour la V1 :

- `Mandat annule`
- `Annule sans mandat`
- `Annule apres offre`

Regles candidates :

#### Mandat annule

- `statut_name = 'Clos'`
- `mandat_id IS NOT NULL`
- `offre_id IS NULL`
- `vente_id IS NULL`

#### Annule sans mandat

- `statut_name = 'Clos'`
- `mandat_id IS NULL`

#### Annule apres offre

- `statut_name = 'Clos'`
- (`offre_id IS NOT NULL` ou `compromis_id IS NOT NULL`)
- `vente_id IS NULL`

## Regle de priorite d'affichage

Le statut global affiche doit etre le plus avance ou le plus determinant.

Ordre de priorite recommande :

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

## Regle sur les alertes

Les alertes ne doivent pas remplacer le statut global.

Alertes principales retenues :

- `Bloque`
- `A relancer`
- `Erreur diffusion`

Exemples de lecture :

- `Valide` + `Non diffuse` + alerte `A relancer`
- `Diffuse` + `Diffuse partiellement` + alerte `Erreur diffusion`
- `Compromis signe` + `Dossier notaire` + alerte `Bloque`

## Conclusion

Cette grille sert de base pour :

- recalculer `statut_global`
- ajouter `sous_statut`
- conserver `alerte_principale` a part

Elle doit maintenant servir de reference pour retravailler la vue generale.
