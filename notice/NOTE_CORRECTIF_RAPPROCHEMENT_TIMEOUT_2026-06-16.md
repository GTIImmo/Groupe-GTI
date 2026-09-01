# Correctif — « Rapprocher les biens » HS (crash React #310) + timeout + cron cassé

> ⚠️ **CAUSE RÉELLE DU « PLANTAGE » VISIBLE = crash React, PAS le timeout.**
> Vérifié en ligne dans le navigateur (prod `groupe-gti.vercel.app`, session authentifiée) :
> l'écran « Rapprocher les biens » lançait **`Minified React error #310`** (*rendered more
> hooks than during the previous render*) → écran blanc. Cause : dans `RechercheAcquereur.tsx`,
> les hooks `newAlertsCount` (`useMemo`) et `openNotif` (`useCallback`) — ajoutés pour le bloc
> « Nouveaux rapprochements » (commit `42b7f66`) — étaient placés **APRÈS** `if (!open) return null`.
> À l'ouverture de l'overlay le nombre de hooks changeait → crash. **Corrigé commit `53017fe`**
> (hooks remontés avant tout return anticipé). **Vérifié en ligne** : overlay ouvert, 40 biens,
> score moyen 83 %, **console propre, plus aucune erreur**.
>
> Important : l'app lit Supabase avec un utilisateur **`authenticated`** (RLS), pas `anon`.
> Les tests REST faits avec la clé `anon` (timeout 3 s) ne reflétaient donc pas exactement le
> runtime. Le timeout et le cron cassé (ci-dessous) étaient de **vrais** problèmes corrigés,
> mais ce n'était pas ce que l'utilisateur voyait comme « planté » — c'était le React #310.
>
> 🧭 Leçon : pour un « écran qui plante », vérifier d'ABORD la **console JS en ligne** (erreur
> React/runtime) avant de plonger dans la couche données.

**Date :** 2026-06-16
**Périmètre :** moteur de rapprochement acquéreur ↔ biens (écrans Recherche Acquéreur & Rapprochement Mandat)
**Supabase :** projet `dwaqxfrinihnychuoptk` · **Front :** repo `C:\Hektor\Projet`, branche `refonte-mobile` (= `main`), Vercel
**Statut :** bug bloquant **corrigé** ; 2 correctifs de fond (cron + anti-boucle) **rédigés, en attente de validation** (non appliqués).

---

## 1. Symptôme

Clic sur **« Rapprocher les biens »** (fiche contact → écran Recherche Acquéreur) : écran vide / cassé **en ligne** pour une partie des contacts. Reproduit en prod.

## 2. Diagnostic (confirmé, pas supposé)

Test des 5 appels REST que fait l'écran, avec la clé **`anon`** (celle du navigateur) sur la prod :

| Appel RPC | Résultat |
|---|---|
| `app_get_rapprochements` | **HTTP 500 — `statement timeout` (57014)** |
| `app_get_search_statuts` / `app_list_relances` / `app_get_search_timeline` / `app_notifications_for_search` | 200 OK |

Causes empilées :

1. **`anon` a `statement_timeout = 3 s`** (vs `authenticated` = 8 s). Le navigateur utilise `anon`.
2. **`app_get_rapprochements` n'est PAS en lecture pure** : si la recherche n'a jamais été calculée (ou périmée > 24 h), elle lance un **recompute synchrone** (`app_refresh_rapprochements_for_search`, qui score *tous* les biens actifs un par un) **dans le chemin de lecture** → > 3 s → 500.
3. **1048 recherches actives sur 3772 n'avaient jamais été calculées** (`computed_at` NULL) → c'est pour ces contacts que l'écran plantait. Les 2724 « fraîches » répondaient vite.
4. **Le cron de calcul `rapprochement-dirty` échouait à CHAQUE passage** (timeout 2 min + rollback total → 0 progrès) : `app_process_rapprochement_dirty(200)` recalcule 200 recherches/appel via la fonction lente → ne finit jamais. Bug **antérieur** ; la file ne s'est jamais vidée seule.

> ⚠️ Le bug n'était **pas** causé par les commits front (alertes symétriques / isolation notifications) de la même journée. Une erreur d'analyse initiale l'avait attribué aux notifications — invalidée par le test REST (notifications = 200).

## 3. Ce qui a été appliqué (en prod, validé au coup par coup)

### Front (poussé sur `main`)
- **`a5d81f2`** `fix(rapprochement): isole le chargement des notifications du chemin critique`
  Les notifications (`loadNotificationsForSearch` / `loadNotificationsForDossier`) étaient chaînées dans le `Promise.all` des biens → leur échec faisait tomber tout l'écran. Désormais **chargées à part avec leur propre `catch`** dans `RechercheAcquereur.tsx` et `RapprochementMandat.tsx`. Dégradation gracieuse.
- *(rappel)* **`42b7f66`** alertes symétriques bien↔contact (bloc « Nouveaux rapprochements »).

### Supabase
- **PostgREST schema reload** (`notify pgrst, 'reload schema'`) — exposition des RPC notifications.
- **Migration `harden_get_rapprochements_async`** : `app_get_rapprochements` **ne recompute plus en synchrone**. Si absent/périmé → **enfile la file `app_rapprochement_dirty`** et renvoie immédiatement ce qui est stocké (vide au 1er coup, rempli par le cron). `RETURN QUERY` (colonnes/jointures/tri) **inchangé**.
  → Re-test REST : **HTTP 200 en ~0,5 s** (au lieu de 500). **Bug résolu.**
- **Cron `rapprochement-dirty` passé de `*/2` à `*/1 min`** (jobid 1).
- **Backfill** : enfilé les 1048 recherches manquantes puis **drainé à la main via `app_bulk_recompute_chunk(250)`** (fonction ensembliste **~16× plus rapide** : 30 recherches en 3,16 s vs ~1,7 s/recherche). ~988 traitées.

## 4. Découverte pendant le backfill

Les **1048 recherches « non calculées » ne produisent AUCUN bien à ≥ 60** (plancher de stockage). Réparti :

| Cause | Nb |
|---|---|
| **Aucune commune renseignée** (`villes_json = []`) → secteur plafonné à **55** < 60 | **666** |
| Commune présente mais aucun bien actif proche / géo manquante / détail non synchro | ~382 |
| Sans type | 12 |

Exemple : *Maison, budget 300 k, surface ≥ 100, villes = []* → **score max 55** sur tout le stock (plafond secteur, pas un bug de calcul).

**Conséquence comportementale :** l'écran ne plante plus, mais affiche une **liste vide** pour ces recherches incomplètes (correct). Pour les recherches complètes, il affiche les vrais biens.

**Effet de bord à corriger :** une recherche sans résultat ne stocke aucune ligne → `app_get_rapprochements` la voit toujours « jamais calculée » → la ré-enfile à chaque ouverture (boucle, inoffensive mais gourmande).

## 5. Correctifs de fond — APPLIQUÉS EN PROD (2026-06-16)

Décision utilisateur : « Cron + anti-boucle » (la question scoring #3 reste ouverte). Migrations appliquées et vérifiées.

**① `cron_dirty_dossier_only`** ✅ — `app_process_rapprochement_dirty` ne traite plus que `entity_type='dossier'` (les `search` passent par la fonction rapide). Logique annonces + notifications **inchangée**.

**② `rapprochement_search_state_marker`** ✅ — anti-boucle :
- table interne `app_rapprochement_search_state(contact_search_key PK, computed_at, n_matches)` ;
- `app_bulk_recompute_chunk` écrit le marqueur pour **chaque** recherche du chunk (même 0 résultat) ;
- `app_get_rapprochements` lit la fraîcheur depuis ce marqueur (au lieu des lignes) → plus de ré-enfilage des recherches vides ;
- backfill marqueur des 3772 recherches actives.
- **Correctif `fix_get_rapprochements_ambiguous_computed_at`** ✅ : `computed_at` était ambigu (colonne OUT du `RETURNS TABLE` vs colonne table) → qualifié `st.computed_at` (table aliasée `st`). Sans ça la RPC renvoyait 400 (42702).

**③ Cron** ✅ — nouveau job `rapprochement-dirty-search` (jobid 4) `*/1` = `SELECT app_bulk_recompute_chunk(250);` ; `rapprochement-dirty` (jobid 1) garde `app_process_rapprochement_dirty(200)` (annonces, désormais rapide).

**Vérif post-déploiement (prod) :** file = 0, marqueur = 3772 (2724 avec matches), cron jobid 1 & 4 = `succeeded` (plus de timeout). REST `app_get_rapprochements` : recherche vide → 200/413 ms `[]` ; recherche à 121 matches → 200/764 ms, 121 lignes.

## 6. Reste à décider (métier)

**Politique scoring « sans commune »** : une recherche sans commune doit-elle matcher les biens **partout** (au lieu d'être plafonnée à 55) ? C'est la raison des 666 recherches vides. Touche `app_match_score_v2` (grilles v2) → hors périmètre de ce correctif, à arbitrer séparément.

## 7. Paramètres clés (mémo)

- `statement_timeout` : `anon` 3 s · `authenticated` 8 s · cron ~2 min.
- Seuils scoring : plancher stockage **60**, curseur d'affichage **75**, alerte **80**.
- Triggers d'enfilage (actifs) : `trg_search_dirty` / `trg_dossier_dirty` (AFTER INSERT/UPDATE) → `app_enqueue_dirty` (dédup `ON CONFLICT (entity_type, entity_id)`).
- Crons : jobid 1 `rapprochement-dirty` `*/1`, jobid 2 `rapprochement-alerts` `*/5`.
