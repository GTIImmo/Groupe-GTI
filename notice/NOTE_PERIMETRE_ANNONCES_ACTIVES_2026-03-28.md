# Note perimetre Annonces actives

Date: 2026-03-28

## Objet

Documenter le nouveau perimetre du flux `Annonces`.

## Regle metier

Le flux `Annonces` ne doit plus embarquer tout le parc.

Il ne doit contenir que :

- annonces non archivees
- annonces avec `statut phase 1 = Actif`

Regle appliquee :

- `archive = 0`
- `statut_annonce = 'Actif'`

## Portee

Cette regle s'applique :

- au push full `Annonces`
- au push upgrade `Annonces`
- au listing `Annonces`
- aux details `Annonces`
- aux work items exposes dans la vue `Annonces`
- au catalogue de filtres `Annonces`
- aux compteurs `app_dashboard_v1` issus du payload `Annonces`

## Ce que cela ne change pas

Cette regle ne s'applique pas aux vues :

- `Liste des mandats`
- `Suivi des mandats`

Ces vues gardent leur flux dedie `Mandats`.

## Effet attendu

- reduction forte du volume `Annonces`
- details annonces moins nombreux
- push full plus leger
- upgrade plus rapide
- suppression automatique du `current` Annonces des dossiers qui sortent du perimetre

## Fichiers touches

- `phase2/sync/export_app_payload.py`
- `phase2/sync/push_to_supabase.py`
- `phase2/sync/push_upgrade_to_supabase.py`

`push_to_supabase.py` et `push_upgrade_to_supabase.py` consomment le payload produit par `export_app_payload.py`.
Le filtrage est donc centralise dans l'exporteur.
