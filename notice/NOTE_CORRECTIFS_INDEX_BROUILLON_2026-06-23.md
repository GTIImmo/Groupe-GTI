# Note — Correctifs « index Brouillon » (En création) — chronologie complète

Date : **2026-06-23**. Cette note récapitule **tous les correctifs/implémentations** réalisés pour gérer les annonces « En création » (brouillons Hektor) côté local → Supabase → front → run.
Fait suite à l'analyse : [NOTE_ANNONCES_EN_CREATION_BROUILLON_2026-06-22.md](NOTE_ANNONCES_EN_CREATION_BROUILLON_2026-06-22.md) (diagnostic, marqueur `isDraft`).

> Rappel marqueur : un brouillon = **`isDraft: true`**, exposé **uniquement** par la GraphQL Console (`PropertyListing`), **pas** par l'API REST (`sync_raw`, aveugle). Un brouillon porte quand même un `status` (Actif / Estimation / null). Répartition réelle des **331** brouillons du groupe : **Actif 158 / Estimation 143 / null 30**.

---

## 1. Architecture retenue — VARIANTE (index séparé + front-merge)

- **Données séparées** : les brouillons ne sont PAS dans l'index principal. Nouvelle table dédiée, clone du patron Vendu/Clos.
- **Exclusion de l'actif** : au push, les `isDraft` sont retirés du scope actif (`app_dossier_current`) ET des estimations.
- **Front** : les brouillons sont **fusionnés au front** dans le listing Annonces (comme Vendu/Clos), badgés **« En création »**, + une **option de filtre Archive « Brouillons »** pour les afficher seuls.
- **Transition automatique** : un brouillon finalisé (`isDraft→false`) quitte l'index brouillon et réintègre son scope (estimation→Estimations, actif→Annonces) au run/read-through.

---

## 2. Backend / données (commits)

| Commit | Lot | Contenu |
|---|---|---|
| `d95feeb` | LOT 3 | `export_app_payload.py` + `push_upgrade_to_supabase.py` : flag env `APP_BROUILLON_BUCKET_ENABLED` (OFF par défaut, **inerte**), `build_brouillon_annonce_index`, `load_brouillon_draft_ids`, `brouillon_active_exclusion_sql()` (exclut isDraft du scope actif), `build_current_brouillon_index_rows` (clone historique, `app_brouillon_id`), bloc push index brouillon (remote/local hashes, upsert/delete) à l'identique du patron Vendu/Clos. |
| `758f81e` | LOT 1b | `phase2/sync/sync_hektor_drafts.py` (NEW) : sweep isDraft via GraphQL `PropertyListing` (lecture seule) → table locale `hektor_annonce_draft_state`. Delta quotidien (scan LATEST jusqu'au watermark) + backstop full (`--full` / périodique, démote `is_draft=0` les finalisés). Session `Console/sessions/storage_state_sync_light.json`. |

**Migration Supabase (LOT 2)** : `create_app_brouillon_index_and_detail_cache` — tables `app_brouillon_annonce_index_current` + `app_brouillon_annonce_detail_cache` (clones de l'historique, RLS `is_app_user_active()` + `app_console_can_access_dossier`, grants identiques). Projet `dwaqxfrinihnychuoptk`.

---

## 3. Front (commits)

| Commit | Contenu |
|---|---|
| `b8f95fd` | **LOT 4.1** couche données `api.ts` (inerte) : `brouillonFilterValue='__brouillon__'`, `applyBrouillonIndexFiltersToQuery` (sans exclusion Estimation), branche `loadDossiersPage` lisant `app_brouillon_annonce_index_current` + `loadBrouillonAnnonceDetailCache`, extensions types/unions. |
| `e8f2639` | LOT 4.2 : option filtre « Brouillons » dans les 2 FilterSelect. **(annulé par `d0638a1`)** |
| `d0638a1` | **LOT 4.2-bis VARIANTE** : `shouldMergeBrouillonIndex` + fetch/merge de l'index brouillon dans la branche active (lignes taguées `is_brouillon`) ; `types.ts: Dossier.is_brouillon?` ; retrait du filtre séparé. |
| `f21b784` | Badge « En création » — **posé d'abord sur les MAUVAIS composants** (`MobileDossierCards` + table écran `annonces` mort), cf. §6. |
| `7ea8a02` | **LOT 4.3** ouverture fiche brouillon : `isLightweightAnnonceRecord`/`isReadOnlyLightweightDetail` reconnaissent `is_brouillon` → flux léger read-only, cache → `loadBrouillonAnnonceDetailCache`, message « reprendre la saisie dans Hektor ». |

---

## 4. Activation en prod (`dcf1128`, 2026-06-22)

1. **Exclusion exécutée** : push `APP_BROUILLON_BUCKET_ENABLED=1 … --all-local-current` → `deleted_dossiers=301` (158 Actif + 143 Estimation retirés de `app_dossier_current` ; 30 null n'y étaient pas). Vérif : `app_dossier_current` **13391 → 13090**, chevauchement actif∩brouillon = **0**.
2. **Front déployé** : `main` FF (Vercel déploie depuis `main`).
3. **Run quotidien câblé** (`run_full_pipeline.ps1`) : `APP_BROUILLON_BUCKET_ENABLED=1` + étape sweep `sync_hektor_drafts.py` (non bloquante) → maintient l'exclusion + `hektor_annonce_draft_state`.

> Désactivation éventuelle : retirer le flag du run + re-push sans flag → les brouillons reviendraient dans l'actif.

---

## 5. Correctifs post-activation (2026-06-22 → 23)

| Commit | Problème corrigé |
|---|---|
| `1ac964e` | Filtre « Brouillons » ré-ajouté (à la demande) — **coexiste** avec le merge : filtre Actives = actifs + brouillons badgés ; filtre Brouillons = uniquement les 331. |
| `33ff340` | Le filtre s'affichait mais **ne filtrait pas** : `usesLightweightAnnonceIndex` (App.tsx) et `shouldUseMergedAnnonceListing` (api.ts) ne reconnaissaient pas `brouillonFilterValue` → l'écran chargeait `loadMandatsPage` (aveugle) au lieu de `loadDossiersPage`. Ajout de `filters.archive === brouillonFilterValue` aux deux. |
| `e26e25e` | Option « Brouillons » **restreinte à la vue Annonces** (`screen === 'mandats'`) ; nettoyage du bloc filtre mort `screen==='annonces'`. |
| `1374260` | Dans la **vue filtre Brouillons** : tag `is_brouillon` sur la branche filtre (→ badge), `applyBrouillonIndexFiltersToQuery` applique le **sous-filtre statut** quand un statut précis est choisi, bouton « Reprendre la saisie » (table desktop). |
| `6d6c6e9` | **Badge sur le VRAI écran Annonces** : le menu Annonces = écran interne `mandats` → rend `MandatsScreen` (desktop) + `MobileMandatCards` (mobile), PAS `MobileDossierCards`. Badge ajouté aux bons composants (`.av-statut` + `mobile-status-row`), `MandatRecord.is_brouillon?`, style `av-pill-brouillon` (annonces-v2.css), libellé bouton « Reprendre/Brouillon ». |
| `1a5734b` | **Option filtre dans le drawer DESKTOP** : l'option « Brouillons » n'existait que dans l'overlay de filtres **mobile** ; le drawer desktop (`filtersOpen`, chaîne par écran) ne l'avait pas sur le bloc `screen==='mandats'`. Ajoutée au bloc Archive desktop. |

---

## 6. Pièges rencontrés (pour le prochain dev)

- **Mapping nav ≠ écran interne** : menu **Annonces** = écran **`mandats`** (rend `MandatsScreen` + `MobileMandatCards`). L'écran interne `annonces` est **MORT** (openScreen redirige `annonces→mandats`). Toute UI listing/filtre annonces doit cibler `mandats`, pas `annonces`.
- **2 drawers de filtres distincts** : overlay **mobile** (`showMobileCommandCard && filtersOpen`) ET drawer **desktop** (`filtersOpen`), chacun avec sa propre chaîne par écran. **~6 FilterSelect `label="Archive"`** dans `App.tsx` — viser le bon (desktop mandats, anchré via le filtre « Detail » qui suit).
- **`dossierToMandatRecord` préserve `is_brouillon`** (spread `...row`) — donc les lignes brouillon arrivent taguées dans `mandats`, il « suffit » de les rendre.
- **Brouillons statut=null (30)** : visibles via filtre Brouillons sans sous-filtre statut ; invisibles si on sous-filtre par un statut nommé (leur `statut_annonce` est null).

---

## 7. Décision : PAS de fusion dans la vue Actives par défaut

Dans la vue Annonces **par défaut** (Archive=Actives + statut=Actifs/Offres/Compromis), la fusion ne se déclenche pas (condition `!statut || Toutes`). Une tentative de **fusionner les brouillons en tête de la vue par défaut** (merge gated `activeListings` + tri brouillons-d'abord dans `mergeDossierPageResults` + garde `is_brouillon` dans `filterMandatRowsForScreen`) a été **développée puis ABANDONNÉE à la demande** (2026-06-23) ; **code restauré**, front laissé tel quel.

➡️ **État final** : les brouillons sont accessibles via le filtre **Archive = Brouillons** (ou statut **Toutes**), **pas** dans la liste Actives par défaut.

---

## 8. État prod final (déployé)

- Tables Supabase : `app_brouillon_annonce_index_current` (**331**) + `app_brouillon_annonce_detail_cache`.
- `app_dossier_current` = **13090** (brouillons exclus, chevauchement 0). Index archive = 34397. Index historique = 8745.
- Run quotidien : flag ON + sweep `sync_hektor_drafts.py` actifs.
- Front : filtre **Archive → Brouillons** (desktop + mobile), badge **« En création »**, bouton **Reprendre**, sous-filtre statut opérationnel, ouverture fiche légère « reprendre la saisie ».
- Commits brouillon présents sur `main` (puis prolongé par d'autres devs : contacts `8e57c93`, garde-fou worker `86aa1ad`).

Lié à [NOTE_ANNONCES_EN_CREATION_BROUILLON_2026-06-22.md](NOTE_ANNONCES_EN_CREATION_BROUILLON_2026-06-22.md), mémoire `[[annonces-en-creation-brouillon]]`, `[[bug-annonces-archivees-fantomes-table-active]]`.
