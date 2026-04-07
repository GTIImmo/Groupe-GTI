# Etat d'avancement avance du projet au 2026-04-01

## 1. Methode d'audit

Cet etat d'avancement a ete etabli en croisant :

- les notes de cadrage et d'execution du dossier `notice`
- le schema cible `supabase/schema_v1.sql`
- les scripts phase 2 et sync
- l'etat reel du front `apps/hektor-v1`

Cet audit distingue :

- `valide` : encore coherent avec le code et le contrat retenu
- `partiel` : idee encore valable mais implementation ou contrat ont evolue
- `obsolete` : note depassee par les decisions etat actuel

## 2. Etat global du projet

### 2.1. Niveau d'avancement global

Le projet est maintenant dans un etat **intermediaire avance** :

- le socle data Hektor -> phase 2 -> Supabase -> front est en place
- les vues React principales existent et sont exploitables
- la surcouche `Demande de diffusion` est engagee fonctionnellement
- la console `Diffusion` existe et le write-back Hektor a une premiere couche technique

Mais le projet n'est **pas encore en phase de cloture** car il manque encore les briques qui rendent le workflow complet et robuste :

- messages persistants nego / Pauline
- relances automatiques
- emails nego / manager
- archivage des demandes
- finition UX des popups
- nettoyage final documentation / GitHub / livraison

### 2.2. Estimation d'avancement par bloc

- phase 1 / phase 2 / reconstruction locale : `80%`
- contrat Supabase applicatif : `75%`
- front React global : `75%`
- vues Mandats / Suivi : `80%`
- detail annonce / popup detail : `70%`
- demande de diffusion : `60%`
- diffusion / passerelles : `65%`
- automatisation relances / emails / manager : `15%`
- documentation finale / GitHub / industrialisation : `40%`

## 3. Notes de reference encore valides

### 3.1. Valides comme base structurante

#### `NOTE_SCHEMA_SUPABASE_V1_REACT_2026-03-24.md`

Statut : `valide`

Toujours juste sur les principes :

- front ne doit pas lire directement la complexite interne phase 2
- exposition via tables / vues applicatives stabilisees
- RLS et profils applicatifs

#### `NOTE_CORRECTIFS_SURCOUCHE_DEMANDE_DIFFUSION_2026-03-31.md`

Statut : `valide`

Toujours la meilleure note de cadrage fonctionnel sur :

- logique de demande
- acceptation / refus
- motifs type
- relances
- bouton `J'ai corrige`
- separation `Demande de diffusion` / `Diffusion`

#### `NOTE_POPUP_ETATS_DEMANDE_DIFFUSION_2026-03-31.md`

Statut : `valide avec ajustements partiels`

La structure UI retenue reste bonne :

- bouton d'etat par ligne
- etats nego / Pauline
- popup dedie
- historique
- echanges

Mais une partie de la mise en oeuvre reelle reste encore partielle.

#### `NOTE_WRITEBACK_HEKTOR_DIFFUSION_2026-03-31.md`

Statut : `valide`

La note reste correcte sur :

- script local `hektor_diffusion_writeback.py`
- logique `seed-default-targets`
- logique `apply-targets`
- endpoints Hektor mobilises

## 4. Notes partiellement valides

### 4.1. Toujours utiles, mais a relire avec l'etat actuel

#### `NOTE_CROISEMENT_UTILISATEUR_NEGO_EMAIL_2026-03-31.md`

Statut : `partiel`

Le principe est bon et a ete branche.
Mais il depend encore de la stabilite du schema expose a Supabase.

#### `NOTE_VUES_MANDATS_ET_PUSH_DELTA_2026-03-27.md`

Statut : `partiel`

La logique de vues mandats reste utile historiquement, mais la realite actuelle a evolue vers la couche `app_dossiers_current`.

#### `NOTE_VRAI_UPGRADE_V2_ANNONCES_2026-03-27.md`

Statut : `partiel`

Toujours utile pour comprendre le push upgrade, mais il faut la lire avec la correction recente sur le vrai `--full-rebuild`.

#### `NOTE_UPGRADE_ANNONCES_CURRENT_2026-03-27.md`

Statut : `partiel`

Valable sur l'intention technique, mais pas suffisant seul car le comportement `full-rebuild` a ete corrige depuis.

#### `NOTE_COMMANDE_UPGRADE_PHASE1_VERS_APP_2026-03-27.md`

Statut : `partiel`

La chaine reste utile, mais les ressources `negos` et `agences` sont a reintegrer explicitement dans les commandes de reference.

## 5. Notes devenues obsoletes ou a forte vigilance

### 5.1. Notes a ne plus utiliser comme verite actuelle

#### `NOTE_UNIFICATION_FLUX_ANNONCES_MANDATS_2026-03-28.md`

Statut : `obsolete`

La note dit encore :

- `Liste des mandats` lit `app_mandats_current`
- `Suivi des mandats` lit `app_mandats_current`
- le flux principal alimente encore `app_mandat_current`

Ce n'est plus la verite actuelle retenue.

La realite actuelle est :

- front mandate / suivi -> `app_dossiers_current`
- l'ancien contrat mandat a ete purgé / supprimé

#### Toute note parlant encore de `app_mandat_current` ou `app_mandats_current` comme contrat courant

Statut : `obsolete`

Elles restent utiles comme historique de decision, mais plus comme reference de travail.

## 6. Etat reel du code au 2026-04-01

### 6.1. Phase 2 / Sync

Etat : `avance et exploitable`

Faits :

- phase 2 locale reconstruite
- `app_view_generale` alimente le contrat courant
- `agence_nom`, `photo_url_listing`, `negociateur_email` ont ete remontes
- correction du vrai `full-rebuild` dans `push_upgrade_to_supabase.py`

Encore a faire :

- stabiliser definitivement les commandes de sync de reference
- documenter les cas `upgrade simple` vs `full rebuild`

### 6.2. Supabase

Etat : `fonctionnel mais encore en evolution`

Faits :

- schema V1 present
- tables / vues courantes exploitees par le front
- `app_diffusion_request` present
- `app_diffusion_request_event` engage

Encore a faire :

- figer la version finale du schema diffusion
- verifier les policies RLS finales
- ajouter la future table messages
- documenter les patchs SQL encore necessaires

### 6.3. Front React

Etat : `avance et fonctionnel`

Faits :

- vues `Annonces`, `Mandats`, `Suivi`
- filtres nettoyes
- header refondu
- carte utilisateur branchee
- popup detail dedie
- type bien + reference dossier
- photo listing
- colonne passerelles

Encore a faire :

- finition visuelle globale
- harmonisation definitive des popups
- meilleure lisibilite de certains etats / actions

## 7. Etat reel du sujet `Demande de diffusion`

### 7.1. Fait

- distinction `Demande de diffusion` / `Diffusion`
- bouton d'etat en listing
- mode nego et mode Pauline
- motifs type de refus branches
- correction du bug de creation de doublon
- retour de correction sur la meme demande
- historique d'evenements amorce

### 7.2. Partiellement fait

- popup demande
- historique visible
- workflow Pauline
- retour correction -> relecture Pauline

Ces briques existent, mais ne sont pas encore a leur niveau final d'ergonomie ni de robustesse.

### 7.3. Non fait

- vrai fil de messages dedie
- relances automatiques
- emails nego
- emails manager
- suivi des notifications
- archivage des demandes

## 8. Etat reel du sujet `Diffusion / passerelles`

### 8.1. Fait

- console diffusion creee
- sauvegarde cible en base ou fallback local
- test / application Hektor branches
- script Python de write-back disponible

### 8.2. Partiellement fait

- clarification observe / cible / brouillon
- retour de statut
- design de la console

### 8.3. Non fait ou a confirmer

- verification metier complete de tous les cas Hektor
- historique d'application enrichi
- UX finale pro de la console

## 9. Ecart entre ambition cible et etat actuel

Le plus gros ecart n'est plus sur :

- la data
- le branchement general React / Supabase
- les vues principales

Le plus gros ecart est maintenant sur la **couche metier de traitement** :

- discussion / echanges
- relances
- emails
- escalade manager
- archivage
- finitions UX des popups

Autrement dit :

- la base technique existe
- le coeur de la fin de projet est maintenant surtout metier + workflow + finition

## 10. Ce qu'il reste a faire jusqu'a la fin du projet

### 10.1. Lot 1 : cloturer `Demande de diffusion`

1. finaliser le popup nego
2. finaliser le popup Pauline
3. separer messages et evenements
4. ajouter `app_diffusion_request_message`
5. finaliser le workflow complet correction / relecture

### 10.2. Lot 2 : automatisations

6. brancher les relances automatiques
7. brancher les emails au negociateur
8. brancher l'escalade manager
9. tracer les notifications dans l'app

### 10.3. Lot 3 : cloturer `Diffusion`

10. finaliser l'ergonomie de la console
11. verifier le write-back Hektor bout en bout
12. eventuellement ajouter un historique d'application

### 10.4. Lot 4 : finition front

13. harmoniser tous les popups
14. finaliser les colonnes utiles des listings
15. ajouter l'archivage des demandes
16. retoucher la coherence visuelle globale

### 10.5. Lot 5 : cloture technique

17. figer schema Supabase final
18. figer commandes standard de reconstruction et push
19. nettoyer les notes obsoletes
20. rediger une note finale de recette

### 10.6. Lot 6 : GitHub / livraison

21. trier les fichiers a commit
22. preparer les commits logiques
23. pousser le lot final propre
24. rediger une PR ou note de synthese
25. preparer la checklist de livraison

## 11. Conclusion

Le projet n'est plus dans une phase de construction initiale.

Il est dans une phase de **consolidation avancee** :

- les fondations techniques sont la
- le front est deja largement exploitable
- le vrai sujet restant est de terminer proprement le workflow `Demande de diffusion` et les automatismes associes

Le risque principal a partir d'ici n'est plus le manque de socle, mais la dispersion.

La bonne strategie est donc :

- ne plus ouvrir de nouveaux sujets structurels
- terminer maintenant le bloc `Demande de diffusion`
- puis `Relances / Emails`
- puis `Diffusion`
- puis cloturer GitHub / documentation / livraison
