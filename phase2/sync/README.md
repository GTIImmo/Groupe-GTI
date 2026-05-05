# Sync

Ce dossier accueillera les sorties de phase 2 vers la future application.

Cible :

- synchronisation Supabase
- exports techniques temporaires pendant la migration

Scripts utiles :

- `push_upgrade_to_supabase.py`
  - pousse les annonces, details et work items
- `push_hektor_directory_to_supabase.py`
  - synchronise l'annuaire Hektor `users + agences` vers Supabase
  - sert notamment au module RDV pour eviter les appels externes au chargement public
- `sync_matterport_models.py`
  - scanne Matterport en lecture seule
  - matche les modeles avec Hektor par numero de mandat
  - pousse les groupes/liens Matterport dans Supabase avec `--supabase-upsert`
  - ne modifie jamais Matterport : pas de rename, pas de state, pas de visibility, pas de `internalId`
