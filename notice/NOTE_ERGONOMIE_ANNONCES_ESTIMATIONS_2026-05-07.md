# Note ergonomie annonces / estimations

Date: 2026-05-07

## Objet

Cette note documente le recadrage produit de la navigation React / Supabase autour des annonces actives et des estimations.

## Decision produit

La vue historique "Liste des annonces" est renommee "Annonces actives".

Raison: une annonce active Hektor peut deja etre dans le flux commercial sans avoir encore de numero de mandat. Le terme "annonce active" est donc plus juste que "annonce en mandat".

Une nouvelle vue "Estimations" est ajoutee dans l'application. Elle represente les annonces Hektor dont le statut est `Estimation`, c'est-a-dire les futurs mandats potentiels.

## Perimetre donnees

La Phase 1 recupere deja les estimations. Le blocage etait dans le perimetre d'export applicatif vers Supabase:

`phase2/sync/export_app_payload.py`

Le filtre d'export inclut maintenant:

- `Actif`
- `Sous offre`
- `Sous compromis`
- `Estimation`

Cote application:

- "Annonces actives" force le perimetre `Actif`, `Sous offre`, `Sous compromis`.
- "Estimations" force le perimetre `Estimation`.
- Les deux vues continuent a lire `app_dossiers_current`, donc aucune nouvelle table Supabase ni nouvelle policy RLS n'est necessaire pour cette premiere version.

## Evolution des libelles

La vue "Annonces actives" garde sa mise en page historique. Seul son nom change dans la navigation.

La vue "Estimations" utilise des libelles plus adaptes au suivi de futurs mandats.

Dans cette vue, la colonne "Mandat" devient "Projet".

Elle affiche:

- le numero de dossier;
- le numero de mandat si present;
- sinon "Sans mandat";
- le type de bien et la ville en contexte.

Dans cette vue, la colonne "Statut" devient "Avancement".

Elle affiche une synthese metier calculee a partir des donnees existantes:

- `Estimation en cours`;
- `Annonce creee - mandat manquant`;
- `Mandat a valider`;
- `Mandat valide - non diffuse`;
- `Diffuse`;
- `Offre en cours`;
- `Compromis en cours`;
- `Vendu`.

## Ergonomie de la vue Estimations

La vue "Estimations" reprend la structure de la liste des annonces pour rester rapide a comprendre.

Les actions de validation / diffusion sont masquees dans cette premiere version, car une estimation n'est pas encore un mandat a diffuser.

Le bouton d'action principal devient "Voir le projet".

Les filtres de cette premiere version restent volontairement simples:

- negociateur;
- agence;
- archive;
- recherche rapide.

Les filtres de diffusion, validation, passerelle, offre et compromis restent reserves aux annonces actives / mandats.

## Suite logique

La prochaine evolution utile sera de definir les actions metier propres aux estimations:

- suivre une relance estimation;
- detecter une estimation transformee en mandat;
- distinguer estimation active, abandonnee, gagnee;
- preparer une vue commerciale de conversion estimation -> mandat.

## Correctif detail annonce du 2026-05-08

Probleme observe: au clic sur une ligne, la fiche detail pouvait afficher immediatement les donnees enrichies de l'annonce precedente, puis remplacer l'affichage par la bonne annonce apres chargement.

Cause: le composant conservait temporairement `detail_payload_json` du `selectedDossier` precedent pendant le chargement de `loadDossierDetail(...)`.

Correction appliquee:

- au changement d'annonce, la fiche rapide reprend seulement les donnees de la ligne selectionnee;
- `detail_payload_json` n'est conserve que si l'utilisateur rouvre exactement le meme `app_dossier_id`;
- le chargement detail n'est plus relance quand la liste visible se met simplement a jour.
