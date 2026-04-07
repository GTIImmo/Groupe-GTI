Objectif

- Reduire la volumetrie locale et Supabase au parc utile app.
- Arreter le cumul local genere par les upgrades phase 1.
- Pousser vers l'app uniquement les biens non archives dont le `state_name` est utile.

Perimetre cible

- Phase 1 `sync_raw`:
  - ne conserver que le listing `annonces actives / non archivees`
  - ne plus entretenir le flux `annonces archived`
  - ne synchroniser les details annonce que pour les annonces non archivees
- Reconciliation locale:
  - a chaque run annonces, reconstituer la verite courante du listing actif
  - supprimer localement les annonces absentes du listing actif
  - supprimer aussi les details et enregistrements lies devenus hors perimetre
- Push app:
  - ne pousser que les annonces non archivees dont `state_name` est dans:
    - `Actif`
    - `Sous offre`
    - `Sous compromis`

Raison

- Le listing Hektor expose `archive`, mais pas directement `state_name`.
- Le `state_name` vient du detail annonce.
- Il faut donc filtrer en 2 etages:
  - tot: `archive = 0`
  - apres detail: `state_name` utile app

Decision technique

- `sync_raw.py`:
  - full listing actif systematique pour les annonces
  - purge des anciennes pages raw `annonces`
  - purge des lignes state/detail/relation annonce hors listing actif
- `normalize_source.py`:
  - lecture du seul endpoint raw `list_annonces_active`
  - purge des tables source hors `active_annonce_ids`
- `export_app_payload.py`:
  - perimetre app:
    - `archive = 0`
    - `detail_statut_name` ou `statut_annonce` dans `Actif / Sous offre / Sous compromis`

Procedure de rattrapage apres correctif

1. Purger les data locales polluees si necessaire.
2. Rejouer `sync_raw.py` avec le nouveau comportement annonces.
3. Rejouer `normalize_source.py`.
4. Rejouer `build_case_index.py`.
5. Rejouer `phase2/bootstrap_phase2.py`.
6. Rejouer `phase2/refresh_views.py`.
7. Refaire un full app propre.
8. Valider qu'un upgrade ne cumule plus et supprime bien les sorties du perimetre.
