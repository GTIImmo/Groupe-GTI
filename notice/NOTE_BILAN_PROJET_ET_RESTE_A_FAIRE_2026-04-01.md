# Bilan projet et reste a faire au 2026-04-01

## 1. Objectif du projet

Le projet a evolue vers une application React + Supabase, alimentee par la phase 1 Hektor puis par une couche phase 2 metier. Le but est de piloter :

- le stock d'annonces / dossiers
- la lecture mandatee et le suivi Pauline
- la demande de diffusion
- la diffusion effective sur les passerelles Hektor

Le socle retenu aujourd'hui est :

- source brute Hektor -> `sync_raw.py`
- normalisation source -> `normalize_source.py`
- index dossier -> `build_case_index.py`
- phase 2 locale -> `phase2/bootstrap_phase2.py` + `phase2/refresh_views.py`
- push vers Supabase -> `phase2/sync/push_upgrade_to_supabase.py`
- front React -> `apps/hektor-v1`

## 2. Modifications deja apportees

### 2.1. Socle donnees / phase 1 / phase 2

- Remise en place de la chaine locale phase 2 avec `app_view_generale` et `app_view_demandes_mandat_diffusion`.
- Abandon de la dependance front locale a `app_mandats_current`.
- Bascule front sur `app_dossiers_current` pour les vues mandats / suivi.
- Correction des filtres commerciaux par remise en compte des ressources `negos` et `agences` dans le flux de sync.
- Ajout / exposition de `agence_nom` dans le contrat de donnees utilise par le front.
- Ajout / exposition de `photo_url_listing` pour le listing.
- Ajout / exposition de `negociateur_email` afin de croiser l'utilisateur Supabase avec le nego Hektor.
- Correction du `full-rebuild` dans `push_upgrade_to_supabase.py` pour qu'il republie vraiment le stock au lieu de rester sur une logique delta.

### 2.2. Supabase

- Mise en place du schema V1 React / app.
- Creation et usage de `app_diffusion_request`.
- Preparation / creation de `app_diffusion_request_event`.
- Ajout de `agence_nom`, `photo_url_listing`, `negociateur_email` dans le contrat cible quand necessaire.
- Suppression du vieux contrat mandat devenu obsolete :
  - `app_mandat_current`
  - `app_mandats_current`
  - `app_mandat_broadcast_current`

### 2.3. Front React

- Vue `Mandats` et vue `Suivi` branchees sur la source actuelle.
- Filtres nettoyes :
  - `Statut` = statut Hektor phase 1
  - `Statut global` = filtre distinct
  - filtre `Validation diffusion`
  - filtre `Agence`
  - `Negociateur = Sans`
- Listing retravaille :
  - 1re colonne = `Statut`
  - colonne type lisible + reference dossier
  - colonne `Passerelles`
  - colonne `Photo` juste avant `Actions`
- Bouton d'etat colore dans les listings selon l'etat de la demande / diffusion.
- Clic ligne / detail revu plusieurs fois ; etat actuel : popup detail reemployant le detail annonce.
- Header refait :
  - suppression des blocs environnement / compteurs inutiles
  - ajout d'une carte utilisateur
  - croisement email utilisateur -> nego/agence Hektor
  - bouton `Se deconnecter` integre dans la carte

### 2.4. Demande de diffusion

- Regle de base en place :
  - non diffusable -> entree `Demande de diffusion`
  - diffusable -> entree `Diffusion`
- Etats de bouton branches dans les listings.
- Distinction des modes :
  - mode nego
  - mode Pauline
- Motifs type de refus Pauline branches.
- Correction du bug de doublon :
  - une correction nego ne recree plus une nouvelle demande
  - la meme demande repasse a traiter
- Historique par evenements amorce via `app_diffusion_request_event`.
- Fallback local si tables Supabase manquantes.

### 2.5. Console diffusion / passerelles

- Console diffusion front creee.
- Enregistrement des cibles de passerelles via `app_diffusion_target` ou fallback local.
- Distinction :
  - etat observe
  - cible enregistree
  - brouillon courant
- `Tester sur Hektor` et `Appliquer sur Hektor` branches en local.
- Script de write-back Hektor ajoute :
  - `phase2/sync/hektor_diffusion_writeback.py`

## 3. Etat actuel de la demande de diffusion

### 3.1. Ce qui fonctionne deja

- Le bouton de ligne change selon l'etat.
- L'ouverture mene soit au popup de demande, soit a la console diffusion.
- Le workflow nego / Pauline est deja engage.
- Pauline peut accepter / refuser avec motif type.
- Le nego peut renvoyer une correction sans recreer une seconde demande.
- Un historique d'evenements commence a etre stocke.

### 3.2. Ce qui n'est pas encore finalise

- Le popup `Demande de diffusion` n'est pas encore au niveau UX final.
- L'historique n'est pas encore un vrai fil lisible et complet.
- Les messages humains et les evenements systeme ne sont pas encore separes proprement.
- Les relances automatiques et l'escalade manager ne sont pas encore branchees de bout en bout.
- La console `Diffusion` existe mais son design peut encore etre professionnalise.

## 4. Commandes utiles deja stabilisees

### 4.1. Rebuild local phase 2

```powershell
.\.venv\Scripts\python.exe normalize_source.py
.\.venv\Scripts\python.exe build_case_index.py
.\.venv\Scripts\python.exe phase2\bootstrap_phase2.py
.\.venv\Scripts\python.exe phase2\refresh_views.py
```

### 4.2. Push upgrade standard

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py
```

### 4.3. Push full rebuild

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py --full-rebuild --dossier-batch-size 50 --detail-batch-size 25 --work-item-batch-size 50 --filter-batch-size 50
```

### 4.4. Purge des tests de demandes de diffusion

```sql
delete from public.app_diffusion_request_event;
delete from public.app_diffusion_request;
```

## 5. Reste a faire sur `Demande de diffusion`

### 5.1. Priorite haute

1. Finaliser le popup `Demande de diffusion`
- clarifier la structure nego
- clarifier la structure Pauline
- rendre le contenu plus compact, plus metier, plus lisible

2. Finaliser l'historique
- vraie timeline
- distinction claire entre :
  - creation
  - refus
  - correction
  - acceptation
  - relance

3. Ajouter un vrai fil d'echanges
- table dediee type `app_diffusion_request_message`
- messages nego / Pauline
- separation entre messages et evenements systeme

4. Finaliser le workflow correction
- etat nego `A corriger`
- etat Pauline de retour `A traiter`
- conservation totale du contexte

### 5.2. Priorite metier suivante

5. Formaliser la relance automatique
- calcul de `next_reminder_at`
- increment `reminder_count`
- arret automatique si correction recue

6. Brancher les emails au negociateur
- email refus
- email relance
- email acceptation si besoin

7. Ajouter l'escalade manager
- seuil de retard
- email manager
- trace dans l'historique

8. Rendre la relance visible dans le popup Pauline
- derniere relance
- prochaine relance
- nombre de relances
- bouton `Relancer maintenant`

## 6. Reste a faire sur `Diffusion / passerelles`

1. Finir l'ergonomie de la console
- hierarchie visuelle plus claire
- meilleure lisibilite des cibles par portail
- meilleur retour visuel apres enregistrement / test / application

2. Finaliser le write-back Hektor de bout en bout
- verification de `diffusable`
- ajout de passerelle
- retrait de passerelle
- retour de succes / erreur lisible

3. Eventuellement ajouter un historique d'application
- qui a applique
- quand
- resultat

## 7. Reste a faire sur le front en general

1. Harmoniser les popups
- detail annonce
- demande de diffusion
- diffusion / passerelles

2. Finir la qualite visuelle
- popups encore a professionnaliser
- hierarchie des CTA
- densite des cartes

3. Revoir les colonnes de suivi utiles
- derniere action
- prochain rappel
- dernier message
- motif de refus

4. Ajouter l'archivage des demandes
- au lieu de purger a la main
- garder l'historique
- masquer les demandes closes des vues actives

## 8. Reste a faire sur Supabase / donnees

1. Verifier le schema final des tables diffusion
- `app_diffusion_request`
- `app_diffusion_request_event`
- `app_diffusion_target`
- future `app_diffusion_request_message`

2. Verifier les policies RLS
- lecture utilisateur actif
- insert utilisateur actif
- update Pauline / admin / manager selon la regle retenue

3. Documenter les patchs SQL restants
- pour eviter les recreations manuelles au fil de l'eau

4. Stabiliser les vues exposees au front
- `app_dossiers_current`
- `app_work_items_current`
- `app_diffusion_requests_current`

## 9. Reste a faire sur GitHub / industrialisation

1. Nettoyer la documentation technique
- garder une note de cadrage globale
- referencer les notes historiques sans les multiplier inutilement

2. Structurer les patchs SQL
- scripts versionnes
- ordre d'application clair

3. Stabiliser une checklist de livraison
- rebuild local
- push full si changement de contrat
- verification Supabase
- verification front

4. Verifier ce qui doit etre commit / push en priorite
- front `apps/hektor-v1`
- scripts `phase2/sync`
- `supabase/schema_v1.sql`
- notes de cadrage utiles

5. Preparer le travail GitHub final
- tri des commits
- message de commit clair
- PR de synthese
- note de recette

## 10. Ordre recommande jusqu'a la fin du projet

1. Finaliser le popup `Demande de diffusion`
2. Ajouter les messages dedies et la timeline propre
3. Brancher les relances automatiques et emails nego
4. Ajouter l'escalade manager
5. Finir la console `Diffusion`
6. Ajouter l'archivage des demandes
7. Stabiliser le schema Supabase final
8. Nettoyer la documentation
9. Preparer le lot GitHub / recette / livraison

## 11. Definition du done cible

Le sujet sera considere comme termine quand :

- le nego peut envoyer une demande, la corriger et suivre les retours
- Pauline peut traiter, refuser, relancer, accepter sans perdre l'historique
- les echanges sont visibles et persistants
- les relances email et l'escalade manager fonctionnent
- la console `Diffusion` applique vraiment les cibles Hektor avec retour exploitable
- les vues `Mandats` et `Suivi` sont stables, lisibles, et alignees avec le workflow
- le schema Supabase est propre, versionne et documente
- le lot final peut etre pousse / recette / livre proprement sur GitHub
