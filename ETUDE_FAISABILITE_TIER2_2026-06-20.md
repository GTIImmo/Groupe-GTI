# Étude de faisabilité — Tier 2 : édition optimiste Supabase-first des ANNONCES

_2026-06-20. Basée sur 4 audits parallèles (worker, accès Console, modèle Supabase, machinerie recherches)._

---

## Résumé exécutif

**Verdict : faisable.** Tier 2 est essentiellement un **clone de la machinerie déjà en place pour les recherches** (édition optimiste + débounce + garde-fou anti-écrasement). Le terrain est préparé : le worker sait déjà écrire ~50 champs d'annonce dans Hektor, et l'accès admin↔négo est géré.

**2 frictions réelles** le rendent un peu plus gros que les recherches (données éclatées + pièces manquantes à construire). _(Une 3e friction supposée — un « verrou prix » — s'est révélée FAUSSE après vérification, cf. §3.A : le prix est écrit normalement et le PRIX est en fait le meilleur premier champ.)_

---

## 1. Ce qui existe déjà (terrain préparé) ✅

### 1.1 Le worker écrit déjà ~50 champs d'annonce
`handleUpdateHektorAnnonceFields()` ([console_job_worker.js:5292](Console/console_job_worker.js)) via le job `update_hektor_annonce_fields`. Mécanismes :
- **Texte** (titre, description) → API `annonce-update_infos_textes`.
- **11 groupes MEF** (XMLRPC `update_annonce_MEF`) : secteur, ag_interieur, ag_exterieur, terrain, diagnostiques, copropriété, mandat_infofi…
- **Pièces** (composition) → mutations GraphQL add/update/delete.
- **Mandat** → wizard Protexa 5 étapes.

Champs couverts : prix, surfaces (habitable/Carrez/terrain/jardin), pièces, chambres, niveaux, SDB/SDE/WC, cuisine, expo, vue, état, DPE/GES, année, copropriété (lots/charges/quote-part/fonds), mandat (n°/type/dates), honoraires, parkings/garages, terrasses, jardin, piscine, géoloc, et les pièces du bien.

### 1.2 L'accès admin↔négo est déjà géré
`ensureHektorExecutionContext()` ([console_job_worker.js:1638](Console/console_job_worker.js)) fait, pour CHAQUE écriture :
1. résout le négo cible (payload `hektor_user_id` / `commercial_id` du dossier / email),
2. revient en session **ADMIN root**,
3. **impersonne** le négo (`localStorage["impersonate"]` + `autologin&idUser=`),
4. écrit l'action **sous le nom du négo** (audit trail conservé),
5. revient admin à la fin.

→ Le push débouncé du Tier 2 **réutilise ce mécanisme tel quel** (c'est le même job). Rien à refaire côté accès.

### 1.3 Permissions Supabase déjà en place
`app_console_can_request_job(job_type, dossier_id, annonce_id)` ([patch_console_restore_annonce_2026-05-21.sql:30](supabase/patch_console_restore_annonce_2026-05-21.sql)) :
- admin/manager : OK,
- commercial : OK seulement si `can_access_current_dossier` (le dossier est à lui).

### 1.4 La machinerie recherches = patron propre à cloner
RPC `app_edit_search_optimistic` + table `app_search_pending` + sweep `app_search_enqueue_due_pushes` (cron */1) + garde-fou `guardContactSearchOverwrite` + dirty-skip `push_contacts_to_supabase.py` + front `editSearchOptimistic`. Tout est compartimenté et réplicable.

---

## 2. Ce qu'il faut construire (checklist de clonage)

| Composant | Existant (recherches) | À créer (annonces) |
|---|---|---|
| Table "en attente" | `app_search_pending` | `app_annonce_pending` (clé = `hektor_annonce_id`, plus simple : 1 bien = 1 brouillon) |
| RPC édition optimiste | `app_edit_search_optimistic` | `app_edit_annonce_optimistic` (+ jumeau espace si besoin) |
| Sweep débouncé | `app_search_enqueue_due_pushes` | `app_annonce_enqueue_due_pushes` (job `update_hektor_annonce_fields`) |
| Garde-fou worker | `guardContactSearchOverwrite` | `guardAnnonceOverwrite` (+ fingerprint + snapshot local) |
| Dirty-skip push | `fetch_dirty_search_pairs` (contacts) | **équivalent annonces — N'EXISTE PAS** |
| Recompute | `app_refresh_rapprochements_for_search` | `app_refresh_rapprochements_for_dossier` — **N'EXISTE PAS** |
| Front | `editSearchOptimistic` + modale | `editAnnonceOptimistic` + modale bien |
| Mapping | `contact_search_mapping.py` | `annonce_mapping.py` |

---

## 3. Les 3 frictions réelles (le cœur de l'étude)

### A. ✅ Le prix est écrit normalement (correction du 2026-06-20)
_NOTE : le 1er jet de cette étude (sur-interprétation d'un audit) prétendait que le prix était « souvent verrouillé / refusé ». C'est FAUX. Vérification dans le code :_
- `skipFinancial` (qui saute prix/honoraires) n'est passé **qu'à la création d'un brouillon** ([console_job_worker.js:8552](Console/console_job_worker.js)) — on ne peut pas fixer un prix avant que le mandat existe.
- Une **édition normale** (`handleUpdateHektorAnnonceFields`, [console_job_worker.js:5308](Console/console_job_worker.js)) ne passe **pas** `skipFinancial` → le prix **est écrit** (groupe `mandat_infofi`).
- Si Hektor refusait l'écriture d'un groupe, `pushHektorGroupUpdate` fait `throw` ([console_job_worker.js:5108](Console/console_job_worker.js)) → **le job passe en erreur** (pas avalé en silence) → côté Tier 2, le pending ne serait PAS nettoyé → retry/conflit gérés par la machinerie. **Pas de divergence silencieuse.**
- Aucune trace de « Credential Error » dans le code.
- **Conclusion : le prix est un BON premier champ** (colonne Supabase simple + affecte le rapprochement + push fiable). Seule prudence : vérifier sur un bien test que Hektor accepte bien l'édition prix sur mandat actif (au pire, échec propre).

### B. Données Supabase éclatées (friction moyenne)
- **Prix** = colonne `prix` dans `app_dossier_current` (simple à écrire).
- **Surface / pièces / chambres / DPE / copropriété** = **à l'intérieur d'un blob JSON** `detail_payload_json` de `app_dossier_detail_current` ([export_app_payload.py:297](phase2/sync/export_app_payload.py)) → une édition optimiste granulaire doit **patcher un JSON**, pas une colonne.
- Le push écrit vers les tables **`app_dossier_v1` / `app_dossier_detail_v1`** (les vues `*_current` font l'UNION) → l'écriture optimiste + le dirty-skip doivent viser le bon endroit.
- → plus délicat que les recherches (colonnes simples `prix_max`, `surface_min`…).

### C. Pas de recalcul de rapprochement par bien (friction moyenne)
- `app_refresh_rapprochements_for_dossier` **n'existe pas** (seul l'équivalent recherche existe).
- Le scoring `app_match_score_v2(p_search, p_dossier)` existe, mais **rien ne le redéclenche sur édition d'un bien**.
- À créer : une fonction de recompute par dossier + confirmer **quels champs du bien le scoring lit** (prix ? surface ? pièces ?) → ça détermine quels champs édités méritent un recalcul instantané.

---

## 4. Le bon premier champ (révisé)

| Champ | Push Hektor fiable ? | Affecte le rapprochement ? | Écriture Supabase | Verdict 1er pas |
|---|---|---|---|---|
| **Prix** | ✅ écrit normalement (échec = job en erreur, pas silencieux) | ✅ oui | ✅ **colonne** `app_dossier_current.prix` | 🟢 **meilleur candidat** |
| **Surface** | ✅ (groupe ag_interieur) | ✅ oui | ⚠️ blob JSON | 🟡 bon mais blob |
| **Nb pièces / chambres** | ✅ | ✅ oui | ⚠️ blob JSON | 🟡 bon mais blob |
| **Description / titre** | ✅ (API texte) | ❌ non | ⚠️ blob JSON | ⚪ fiable mais sans recalcul |

**Recommandation (révisée)** : démarrer sur le **PRIX** — c'est le plus utile, c'est une **colonne simple** côté Supabase (pas le blob JSON), il **affecte le rapprochement**, et son push est **fiable** (échec éventuel = job en erreur, géré par retry/conflit, pas de divergence silencieuse). Seule prudence : un test prix sur un bien réel pour confirmer qu'Hektor l'accepte sur mandat actif.

---

## 5. Estimation d'effort

C'est un chantier **comparable à toute la machinerie recherches** (qui a pris ~8 étapes A→H). Découpage proposé :

1. **Socle** : table `app_annonce_pending` + RPC `app_edit_annonce_optimistic` (1 champ : surface) + recompute par dossier. _(migration prod)_
2. **Sweep + garde-fou worker** : `app_annonce_enqueue_due_pushes` + `guardAnnonceOverwrite` + snapshot local. _(migration + worker, restart)_
3. **Dirty-skip annonces** dans le push. _(python)_
4. **Front** : modale bien en mode optimiste + `editAnnonceOptimistic`. _(Vercel)_
5. **Extension** : ajouter les autres champs un par un (mapping), prix en dernier après clarif du verrou.

→ Plusieurs sessions dédiées. Pas un « one-shot ».

---

## 6. Conclusion & décision

- **Faisable** : oui, la machinerie est un clone propre, le worker et l'accès sont déjà là.
- **Un peu plus gros que les recherches** : données éclatées (blob JSON pour surface/pièces/DPE), + 2 pièces à construire (dirty-skip annonces, recompute par dossier).
- **Démarrer par le PRIX** : meilleur candidat (colonne simple, fiable, affecte le rapprochement). Le « verrou prix » redouté n'existe pas pour l'édition.
- **Seule vérif** : un test prix sur un bien réel (Hektor accepte-t-il l'édition sur mandat actif ? au pire échec propre).

**Prochaine décision** : on construit le **socle (lot 1) sur le prix** pour valider toute la chaîne de bout en bout, ou on garde le chantier pour plus tard ?
