# Note De Reprise

Date : 2026-03-23

## Où nous en sommes

Le projet est désormais structuré en 2 couches distinctes :

- `phase 1` : socle de vérité Hektor, conservé intact par principe
- `phase 2` : surcouche métier locale + vues + mini app HTML

La règle `phase 1 intouchable` reste le cadre de travail par défaut.

## Phase 1

Socle concerné :

- `data/hektor.sqlite`
- `sync_raw.py`
- `normalize_source.py`
- `build_case_index.py`

La phase 1 n’a pas été refondue aujourd’hui.

En revanche, plusieurs diagnostics importants ont été posés :

### 1. Statuts archivés Hektor

Constat :

- un gros volume d’annonces archivées avec mandat, non vendues, reste encore en `statut_name = 'Actif'`
- métierment, une partie de ces biens devrait probablement être en `Clos`
- ce défaut perturbe le calcul de `Annulé` dans l’app

Décision retenue :

- ne pas surcorriger localement
- conserver la règle : `Annulé = statut_name = 'Clos'`
- attendre le correctif Hektor

Note liée :

- [NOTE_ATTENTE_CORRECTIF_HEKTOR_STATUT_ARCHIVES_2026-03-23.md](C:/Users/frede/Desktop/Projet/NOTE_ATTENTE_CORRECTIF_HEKTOR_STATUT_ARCHIVES_2026-03-23.md)

### 2. Négociateurs manquants

Constat global dans `case_dossier_source` :

- `56100` dossiers au total
- `32773` sans négociateur affichable
- `31966` sans `hektor_negociateur_id`
- `807` avec `hektor_negociateur_id` mais sans nom/prénom résolu

Détail des `807` :

- ID `23` : `712`
- ID `0` : `94`
- ID `93` : `1`

Constat API :

- les annonces peuvent porter `NEGOCIATEUR = 23`
- l’API `listNegos` ne renvoie pas l’ID `23`
- `Vincent-Lucas GONZALEZ` remonte dans `listNegos` sous `95` et `97`

Décision retenue :

- considérer qu’il s’agit d’une anomalie Hektor/API
- ne pas corriger localement en réaffectant un faux négociateur
- attendre le correctif ou l’explication Hektor

Notes liées :

- [NOTE_ATTENTE_CORRECTIF_HEKTOR_NEGOCIATEURS_2026-03-23.md](C:/Users/frede/Desktop/Projet/NOTE_ATTENTE_CORRECTIF_HEKTOR_NEGOCIATEURS_2026-03-23.md)
- [NOTE_ATTENTE_CORRECTIF_HEKTOR_NEGO_23_2026-03-23.md](C:/Users/frede/Desktop/Projet/NOTE_ATTENTE_CORRECTIF_HEKTOR_NEGO_23_2026-03-23.md)

## Phase 2

Base locale :

- [phase2.sqlite](C:/Users/frede/Desktop/Projet/phase2/phase2.sqlite)

Schéma local créé :

- `app_dossier`
- `app_work_item`
- `app_note`
- `app_internal_status`
- `app_followup`
- `app_blocker`
- `app_broadcast_action`

Vue générale active :

- `app_view_generale`

Script principal de reconstruction :

- [refresh_views.py](C:/Users/frede/Desktop/Projet/phase2/refresh_views.py)

## Grille métier retenue

### Statuts globaux

- `Sans mandat`
- `À valider`
- `Validé`
- `Diffusé`
- `Offre reçue`
- `Offre validée`
- `Compromis fixé`
- `Compromis signé`
- `Vente fixée`
- `Vendu`
- `Annulé`

### Source des statuts

Phase 1 :

- `Sans mandat`
- `Validé`
- `Diffusé`
- `Offre validée`
- `Compromis signé`
- `Vendu`
- `Annulé`

Phase 2 :

- `À valider`
- `Offre reçue`
- `Compromis fixé`
- `Vente fixée`

### Règles importantes déjà fixées

- `À valider` = événement local phase 2
- `Validé` = `diffusable = 1`
- `Diffusé` = `diffusable = 1` + diffusion réelle sur au moins une passerelle
- `Offre reçue` = événement local phase 2
- `Offre validée` = offre acceptée avec date en phase 1
- `Compromis signé` = compromis actif avec date passée
- `Vendu` = vente présente en phase 1
- `Annulé` = `statut_name = 'Clos'`

Règle explicitement retenue :

- `diffusable` ne doit pas servir à déduire `Offre`, `Compromis` ou `Vendu`

Notes liées :

- [CORRESPONDANCE_STATUTS_GLOBAUX_2026-03-23.md](C:/Users/frede/Desktop/Projet/CORRESPONDANCE_STATUTS_GLOBAUX_2026-03-23.md)
- [GRILLE_STATUTS_SOUS_STATUTS_2026-03-23.md](C:/Users/frede/Desktop/Projet/GRILLE_STATUTS_SOUS_STATUTS_2026-03-23.md)

## Mini app HTML

Fichier principal :

- [app_metier.html](C:/Users/frede/Desktop/Projet/phase2/app_metier.html)

Générateur :

- [export_mini_app_html.py](C:/Users/frede/Desktop/Projet/phase2/export_mini_app_html.py)

État actuel de l’app :

- navigation latérale fixe desktop
- écrans `Accueil`, `Stock global`, `Diffusion`, `Transactions`, `Alertes`
- filtres globaux
- pagination sur le stock
- panneau de détail sur la vue stock
- statuts, sous-statuts et alertes intégrés

### Règle d’affichage du responsable

Une règle locale a été intégrée dans la mini app :

- si le négociateur est connu, on affiche le négociateur
- sinon, si l’agence est connue, on affiche l’agence
- sinon, on affiche `Non attribué`

Important :

- ce n’est qu’un repli d’affichage phase 2
- cela ne corrige pas la donnée Hektor
- on n’utilise plus les commerciaux issus des passerelles comme substitut

Note liée :

- [REGLE_RESPONSABLE_AFFICHAGE_2026-03-23.md](C:/Users/frede/Desktop/Projet/REGLE_RESPONSABLE_AFFICHAGE_2026-03-23.md)

Vérification actuelle :

- `responsable_type = agence` : `32675`
- `responsable_type = negociateur` : `23301`

## Ce qui a été explicitement rejeté

- ne pas toucher la phase 1 pour corriger localement les défauts Hektor
- ne pas compléter le négociateur avec le commercial de la liste des passerelles
- ne pas forcer artificiellement les archivés `Actif` en `Annulé`

## Point de situation réel

Le projet n’est plus au stade “récupérer la donnée”.

Nous avons maintenant :

- un socle phase 1 en place
- une phase 2 séparée et exploitable
- une vue générale métier
- une mini app HTML fonctionnelle
- une grille de statuts structurée
- plusieurs anomalies Hektor identifiées et documentées

Le principal reste désormais du côté produit / app, et non du côté extraction brute.

## Prochaine étape

Le prochain chantier souhaité est :

- travailler sur l’app elle-même

Priorités recommandées pour demain :

1. améliorer l’ergonomie métier de la mini app
2. enrichir la fiche dossier
3. rendre les écrans `Diffusion` et `Transactions` plus opérationnels
4. commencer à préparer les vues métier spécialisées derrière la vue générale

## Reprise conseillée demain

Reprendre à partir de :

- [app_metier.html](C:/Users/frede/Desktop/Projet/phase2/app_metier.html)
- [export_mini_app_html.py](C:/Users/frede/Desktop/Projet/phase2/export_mini_app_html.py)
- [refresh_views.py](C:/Users/frede/Desktop/Projet/phase2/refresh_views.py)
- [NOTE_REPRISE_2026-03-23_FIN_JOURNEE.md](C:/Users/frede/Desktop/Projet/NOTE_REPRISE_2026-03-23_FIN_JOURNEE.md)

## Décision de continuité

Pour la reprise :

- ne pas rouvrir le débat phase 1 / phase 2
- considérer les anomalies Hektor déjà documentées comme des points en attente
- concentrer la suite sur l’amélioration de l’application métier
