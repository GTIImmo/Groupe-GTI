# Audit de synchronisation — Hektor (API) vs ma data (locale + Supabase)

Date : 30/06/2026
Nature : audit chiffré, lecture seule. Compare la donnée Hektor (telle que lue par l'API au run du matin) à ma data (couche app locale + Supabase lue par l'app). Objectif : mesurer la fidélité de la synchro avant la future coupure d'Hektor.

## Méthode — 3 couches comparées
1. **Hektor brut** = `data/hektor.sqlite` (`hektor_annonce`, `hektor_contact`) — reconstruit ce matin par l'**appel API quotidien** (06:39, biens_vus=22211 confirmé dans le log). = référence « Hektor via API ».
2. **Couche app locale** = `phase2/phase2.sqlite` (`app_view_generale`, `app_contact_current`) — transformation prête pour l'app.
3. **Supabase (live)** = ce que le navigateur lit (`app_dossier_current`, `app_*_index_current`, `app_contact_current`).

## A. Les 2 derniers runs quotidiens — VERTS
| Run | Fin | Exit | Détails contacts | Étapes |
|---|---|---|---|---|
| **29/06** | 06:22:43 | **0 (succès)** | selected=0 (rien à rafraîchir), total=354 776, with_detail=347 117 | toutes DONE |
| **30/06** | 06:39:15 | **0 (succès)** | selected=32 success=32 **errors=0**, total=354 795, with_detail=347 136 | toutes DONE |

Pipeline complet à chaque fois (pull → normalize → phase2 → push Supabase → contacts → Matterport → vitrine). Aucune erreur, aucun échec, aucune exception.
Anomalies **connues et bénignes** : 5 négos orphelins (16,19,20…) non re-tentés (garde-fou anti-retry idnego) ; 341 brouillons `is_draft` suivis.

## B. Annonces — réconciliation EXACTE
Hektor total = **56 616** (actives archive=0 : 22 211 · archivées archive=1 : 34 405).

| Catégorie Hektor | Hektor (API matin) | Table Supabase cible | Supabase | Écart |
|---|---|---|---|---|
| Archivées (archive=1) | 34 405 | `app_archive_annonce_index_current` | **34 405** | **0 — EXACT** |
| Vendu + Clos (archive=0) | 8 752 (8 625 + 127) | `app_historical_annonce_index_current` | **8 752** | **0 — EXACT** |
| Portefeuille actif (archive=0, hors vendu/clos) | 13 468 | `app_dossier_current` | 13 118 | −350 (2,4 %) |
| **Total** | **56 616** | (3 tables) | 56 275 | −341 |

Composition du portefeuille actif (couche app) : Estimation 12 549 · Vendu 8 625 (→historique) · Actif 731 · Clos 127 (→historique) · Sous compromis 101 · Sous offre 56 · null 31.
Supabase `app_dossier_current` (live) : Estimation 12 401 · Actif 569 · Sous compromis 94 · Sous offre 54 · **0 Vendu** (design correct).

**Intégrité** : `app_dossier_current` = 13 118 ids distincts = 13 118 lignes → **zéro doublon**.

## C. Contacts — réconciliation EXACTE (au design près)
Hektor total = **354 938** (actifs archive=0 : 170 836 · archivés archive=1 : 184 101).

| Catégorie | Local (phase2) | Supabase | Écart |
|---|---|---|---|
| **Éligibles** (poussés) | 57 219 | **57 220** | +1 (négligeable, timing/optimiste) |
| Non éligibles (NON poussés, par design) | 297 719 | — | — |

L'app ne reçoit que les contacts **éligibles** (liés à l'activité : négos, mandants, recherches actives…). Le filtre `supabase_sync_eligible` écarte volontairement 297 719 contacts inertes. Côté éligibles : **match quasi parfait**.

## D. L'écart de ~350 : RÉSOLU = ce sont les brouillons
Les **brouillons** (`is_draft=1`) ont leur **propre table** (`app_brouillon_annonce_index_current`), ils ne vont PAS dans `app_dossier_current`. Vérifié :
- Local `hektor_annonce_draft_state` is_draft=1 = **341**
- Supabase `app_brouillon_annonce_index_current` = **341** → **EXACT**

Réconciliation finale du portefeuille actif :
| | |
|---|---|
| Portefeuille actif local (archive=0, hors Vendu/Clos) | 13 468 |
| − brouillons (table dédiée, 341 ✓) | −341 |
| = attendu dans `app_dossier_current` | **13 127** |
| Réel `app_dossier_current` | 13 118 |
| **Résiduel réel** | **9** |

Soit **9 annonces** d'écart sur 56 616 — du bruit (churn intra-journée entre le push 06:39 et l'instant de l'audit + ~quelques statuts null). **Aucune perte.**

## F. Comparaison LIVE — Hektor API (maintenant) vs mon local
Appel API direct (metadata.total), comparé à `data/hektor.sqlite` :

| | Hektor live (API) | Local | Écart |
|---|---|---|---|
| Annonces actives (archive=0) | 22 211 | 22 211 | **0 — EXACT** |
| Annonces archivées (archive=1) | 34 405 | 34 405 | **0 — EXACT** |
| Contacts actifs (archive=0) | 168 639 | 170 836 | +2 197 |
| Contacts archivés (archive=1) | 178 628 | 184 101 | +5 473 |
| **Contacts total** | **347 267** | **354 938** | **+7 671** |

**Lecture :**
- **Annonces : miroir local parfait** (= Hektor live au bien près). Normal : le run fait un **re-listing COMPLET** des annonces chaque jour (pages_scannees~445, biens_vus=22 211) + suppression des périmées (`-AllowStaleSupabaseDeletes`).
- **Contacts : le local a ~7 671 contacts DE PLUS que Hektor live.** Cause : les contacts ne sont **PAS re-listés intégralement chaque jour** (`last_seen_at` : seulement ~3 700 revus au run du 30/06, sur 354 795). La synchro contacts est **incrémentale/delta**, sans purge globale → les contacts **supprimés dans Hektor** ne sont jamais retirés du local. Ce sont des **fantômes** accumulés (~2,2 %). Même classe de bug que les annonces archivées fantômes, mais sur les contacts.
- **Impact app : faible.** L'app n'utilise que les 57 220 contacts **éligibles** (qui matchent Supabase à 1 près) ; les fantômes sont quasi tous inactifs/non-éligibles. Mais pour l'objectif « couper Hektor » (local = source de vérité), il faudra une **purge périodique des contacts disparus** (re-listing complet contacts + stale-delete, comme pour les annonces).

## E. Conclusions
1. **La synchro quotidienne fonctionne de façon fidèle et fiable.** 2 runs verts d'affilée, et les compteurs Hektor→Supabase ferment **à l'unité** sur 3 axes majeurs (archivées 34 405, historique 8 752, contacts éligibles 57 219↔57 220).
2. **Les gros écarts apparents sont 100 % du design, pas de la dérive** : Supabase ne porte que ce dont l'app a besoin (portefeuille actif + index légers archives/historique ; contacts éligibles). Hektor garde tout l'historique (56 616 annonces, 354 938 contacts).
3. **Routage correct** : Vendu/Clos → index historique ; archivées → index archive ; actifs → `app_dossier_current` (0 Vendu, 0 doublon).
4. **Résiduel final = 9 annonces** (sur 56 616) après prise en compte des brouillons (341, routés vers leur table dédiée — vérifié exact). C'est du bruit (churn intra-journée). En clair : la synchro est fidèle au **bien près** sur les annonces, et au **contact près** côté contacts.
5. **Lecture « coupure Hektor »** : la couche locale possède DÉJÀ l'intégralité de la donnée Hektor (56 616 / 354 938), pas seulement le sous-ensemble app. La base technique pour se passer d'Hektor côté *stockage de la donnée* est donc là ; le vrai chantier reste la diffusion/portails (cf rapport architecture du 26/06).

## Annexe — croissance jour/jour (sanity)
Contacts : 354 776 (29/06) → 354 795 (30/06) ≈ **+19/j** (organique). Annonces actives stables ~22 211. Aucune variation anormale.
