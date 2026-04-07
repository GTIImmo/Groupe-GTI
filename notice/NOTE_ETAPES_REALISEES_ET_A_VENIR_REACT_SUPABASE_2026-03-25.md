# Note etapes realisees et a venir React Supabase

Date: 25/03/2026

## Objet

Documenter l'etat du chantier apres :

- mise en place de la phase 2 restructuree
- sync complete vers Supabase
- branchement du front React sur les vraies donnees
- ajout d'une premiere fiche dossier cliquable
- ajout des premiers filtres metier React
- enrichissement de la fiche dossier
- liaison file de travail -> fiche dossier

## Etapes realisees

### 1. Phase 2 refondue en socle

Blocs poses :

- `pipeline`
- `rules`
- `checks`
- `sync`

But atteint :

- sortir la logique metier des exports HTML
- preparer un vrai socle application

### 2. Qualite et sync

Realise :

- checks de coherence sur `phase2.sqlite`
- contrat de sortie V1
- sync `phase2 -> Supabase`

Etat atteint :

- schema Supabase charge
- import test OK
- import complet OK

Volumes sync au moment de cette note :

- `55976` dossiers
- `21377` work items

### 3. Front React branche sur Supabase

Realise :

- variables d'environnement configurees
- build React valide
- chargement des vues Supabase

Vues lues :

- `app_dashboard_v1`
- `app_dossiers_current`
- `app_work_items_current`

### 4. Auth front alignee avec RLS

Realise :

- plus de fallback silencieux vers les mocks quand Supabase est configure
- ecran de connexion si pas de session
- lecture reelle des donnees seulement si utilisateur autorise

Condition d'acces retenue :

- utilisateur present dans `auth.users`
- ligne presente dans `public.app_user_profile`
- `is_active = true`

### 5. Premiere UX metier

Realise dans le front :

- liste dossiers chargee depuis Supabase
- lignes dossiers cliquables
- fiche dossier V1 dans le panneau de droite
- fiche dossier enrichie avec lecture metier et demandes liees
- file de travail visible
- file de travail cliquable avec ouverture du dossier lie
- filtres React sur :
  - commercial
  - statut global
  - validation diffusion
  - etat visibilite
  - priorite
  - work status
  - internal status

## Ce qui existe maintenant

Concretement, l'app n'est plus une simple page statique :

- elle se connecte a Supabase
- elle charge les vraies donnees
- elle demande une authentification
- elle permet de selectionner un dossier
- elle affiche une fiche dossier V1
- elle affiche une fiche dossier enrichie
- elle permet deja un filtrage metier de base
- elle relie deja la file de travail au dossier selectionne

## Ce qui manque encore

La V1 reste partielle.

Il manque notamment :

- vraie navigation d'ecran
- fiche dossier encore a completer sur transaction / dates / actions
- detail des work items
- actions utilisateur
- gestion plus fine des roles

## Prochaines etapes recommandees

Ordre conseille :

1. ajouter les filtres React sur :
   - etendre les filtres actuels a des besoins plus fins
   - ajouter reset / presets metier
2. enrichir la fiche dossier :
   - dates utiles
   - alerte
   - resume transaction
   - prochaines actions
3. ajouter un detail plus riche des work items
4. ajouter un ecran ou panneau `dashboard metier` plus riche
5. ajouter ensuite la vraie gestion des roles

## Decision a retenir

On n'est plus dans une logique :

- export HTML puis bricolage d'interface

On est maintenant dans une logique :

- phase 2 consolide
- Supabase stocke
- React lit et affiche
- l'UX metier se construit progressivement au-dessus
