# Plan d'implémentation — Tier 2 : édition optimiste des annonces (prix d'abord)

_2026-06-20. Suite de [ETUDE_FAISABILITE_TIER2_2026-06-20.md]. Objectif : qu'une modif de prix (ou autre champ) sur un bien s'affiche **instantanément** dans l'app + recalcule le rapprochement, et parte vers Hektor **en arrière-plan débouncé** — comme pour les recherches._

## Principes établis (rappel)
- **Démarrer par le PRIX** : colonne simple (`app_dossier_current.prix`), affecte le rapprochement, push fiable (échec = job en erreur, pas de divergence silencieuse).
- **Un seul chemin à cloner** : la **modification** (`update_hektor_annonce_fields`), pas la création.
- **Annonces + estimations unifiées** : même mécanisme ; seul le champ "valeur" diffère (annonce → `prix`, estimation → `ESTIMATION_MONTANT`). On fait l'annonce d'abord.
- **Tout le reste = clone** de la machinerie recherches (déjà en prod et testée).

---

## PRÉALABLE — à vérifier avant de coder (1 test, 0 code)
**P0.** Sur un **bien de test**, déclencher une modif de prix via le job `update_hektor_annonce_fields` existant et confirmer qu'Hektor **accepte** l'écriture du prix sur mandat actif (et sinon, que le job passe bien en **erreur** proprement). → valide l'hypothèse centrale avant tout investissement.

---

## LOT 1 — Socle base de données _(migration prod)_
**Objectif** : écriture optimiste + recompte instantané + drapeau d'attente.

1. **Table `app_annonce_pending`** (clone de `app_search_pending`, clé = `hektor_annonce_id` ou `app_dossier_id`) :
   colonnes `base_snapshot` jsonb, `push_fields` jsonb (champs à pousser), `push_after`, `source` (nego_app/espace), `push_job_id`, `conflict`, `push_attempts`, `dirty_by`, `updated_at`.
2. **Fonction `app_refresh_rapprochements_for_dossier(app_dossier_id)`** — N'EXISTE PAS, à créer : recalcule les rapprochements du bien (rescore contre les recherches qui matchent). _Sous-étape : confirmer quels champs du bien `app_match_score_v2` lit (prix, surface, type…)._
3. **RPC `app_edit_annonce_optimistic(target_dossier_id, fields jsonb, debounce_seconds=600)`** (clone de `app_edit_search_optimistic`) :
   - vérifie permission (`app_console_can_request_job`),
   - écrit le(s) champ(s) éditable(s) — prix → `app_dossier_current.prix`,
   - appelle `app_refresh_rapprochements_for_dossier` (recompute synchrone),
   - insère/maj `app_annonce_pending` (base_snapshot = photo des champs non éditables + valeur pré-édition).
- **Test** : éditer le prix d'un dossier test → prix màj + rapprochement recalculé + pending créé. Restaurer.

## LOT 2 — Sweep + push débouncé _(migration prod)_
**Objectif** : envoyer la modif à Hektor une seule fois, ~10 min après la dernière édition.

1. **`app_annonce_enqueue_due_pushes()`** (clone de `app_search_enqueue_due_pushes`, cron */1) avec les mêmes garde-fous déjà éprouvés : nettoyage des `done`, ré-armement des échecs (5 retries + backoff), TTL conflit 24h, plafond.
2. Crée un job **`update_hektor_annonce_fields`** avec `from_pending=true` + `base_snapshot` + les champs à pousser.
3. **Vue d'audit** `app_annonce_pending_audit` (clone) — optionnel mais utile.
- **Test** : pending dû → sweep crée le job → vérifier (sans pousser en vrai : `push_fields` neutre).

## LOT 3 — Garde-fou anti-écrasement worker _(worker, restart)_
**Objectif** : ne pas écraser un négo qui aurait changé le prix dans Hektor entre-temps.

1. **`annonceCoreFingerprint(snap)`** + **`guardAnnonceOverwrite(job, dossierId, payload)`** (clone de `guardContactSearchOverwrite`) — compare `base_snapshot` à l'état Hektor **frais lu en LOCAL** (snapshot SQLite, comme pour les recherches).
2. Brancher dans **`handleUpdateHektorAnnonceFields`** : branche `from_pending` → guard → succès = `clearAnnoncePending` / bloqué = `markAnnoncePendingConflict`.
3. Script Python de lecture snapshot local annonce (clone de `read_local_search_snapshot.py`).
- **Test** : simuler un changement Hektor entre l'édition et le push → doit bloquer (conflit), pas écraser.

## LOT 4 — Dirty-skip annonces dans le push _(python)_
**Objectif** : qu'un refresh (read-through / quotidien) n'écrase pas un prix optimiste en attente.

1. **`fetch_dirty_annonce_ids()`** + exclusion du delete/upsert pour les dossiers "dirty" — clone de `fetch_dirty_search_pairs` / `delete_searches_except_dirty`, dans le push annonces (`export_app_payload.py` / push dossiers).
- **Test** : marquer un dossier dirty → un refresh ne doit pas réécraser sa valeur optimiste.

## LOT 5 — Front _(Vercel)_
**Objectif** : édition instantanée côté négo, sans attente.

1. **`editAnnonceOptimistic(dossierId, fields)`** dans `api.ts` (RPC `app_edit_annonce_optimistic`).
2. Champ/modale d'édition prix du bien en **mode optimiste** (au lieu de "créer un job + attendre").
3. Événement `hektor:annonce-updated` → reload fiche + rapprochement (comme `hektor:search-updated`).
- **Test** : éditer un prix dans l'app → bouge tout de suite, rapprochement à jour, push parti en fond.

## LOT 6 — Extension _(itératif)_
1. **Estimations** : même chaîne, champ `ESTIMATION_MONTANT` au lieu de `prix`.
2. **Autres champs** : surface / pièces / chambres (push fiable + effet rapprochement) — attention : ces champs sont dans le **blob JSON** `detail_payload_json` → patch JSON (plus délicat).
3. Champs texte (titre/description) : push fiable, sans recompute.

---

## Dépendances & ordre
`P0` → `Lot 1` → `Lot 2` → `Lot 3` (worker) en parallèle de `Lot 4` (python) → `Lot 5` (front) → `Lot 6`.
Les lots 1-2 sont des migrations prod (confirmation au coup par coup). Lot 3 = restart worker. Lot 5 = push main (Vercel).

## Effort
Comparable à toute la machinerie recherches (~8 étapes A→H) → **plusieurs sessions**. Le Lot 1 (socle + test prix de bout en bout) est le jalon décisif : une fois validé, le reste est de la réplication.

## Risques / points de vigilance
- **P0** : si Hektor refuse l'édition prix sur mandat actif → revoir (avenant requis ?) ; au pire, démarrer sur un champ non-financier.
- **Blob JSON** (lot 6) : surface/pièces nécessitent un patch JSON, pas une colonne.
- **app_match_score_v2** : confirmer les champs bien lus par le scoring (sinon le recompute ne reflète pas l'édition).
