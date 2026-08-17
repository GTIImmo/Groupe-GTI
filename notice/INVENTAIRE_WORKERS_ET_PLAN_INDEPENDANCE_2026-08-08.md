# Inventaire complet des workers + plan « app indépendante » (ultra-réactive)

**Date : 2026-08-08. Analyse Claude sur le code réel (`Console/console_job_worker.js`, `run_full_pipeline.ps1`, `phase2/sync/*`, `backend/*`, base live).**
**Complément de `ETUDE_FAISABILITE_DECOUPLAGE_HEKTOR_APP_FIRST_2026-08-08.md`.**

## But (reformulé)
L'app était pensée comme une **surcouche** de Hektor. Objectif nouveau : **app indépendante, ultra-réactive, aucun temps d'attente worker dans le parcours utilisateur**, logiciel unique de la société. Ce document liste **tous les workers**, à quoi ils servent, et lesquels **retirer / garder**.

---

## Correction conceptuelle importante (avant de lister)

Tu dis « arrêter les workers calque optimiste et read-through ». Précision sur ce que sont vraiment ces pièces :

- **Le « calque optimiste » n'est PAS un worker.** C'est l'écriture instantanée côté app (RPC `app_edit_*_optimistic` → Supabase). **C'est ELLE qui rend l'app réactive** — on la GARDE. On peut même la **simplifier** (voir plus bas).
- **Le read-through EST un worker** : `refresh_console_data` / `refresh_console_contact_data`. C'est lui qui va relire Hektor et **peut faire « revenir » l'ancienne valeur** → c'est la source du sentiment « ça dépend du chargement Hektor ». → **à neutraliser.**
- **Le push (`update_hektor_*`, créations, cycle de vie)** = workers qui poussent vers Hektor. → **à regrouper dans la migration globale 2×/jour**, puis retirer à la coupure.

**L'insight clé** : l'overlay (`app_optimistic_overlay`), le `base_snapshot`, le flag `conflict` et le read-through forment **un seul sous-système** qui n'existe QUE pour cohabiter avec Hektor comme source. **Rendre l'app autoritaire permet de SUPPRIMER tout ce sous-système** → l'édition devient « écrire la colonne, fini », zéro worker dans le parcours. C'est exactement ça, « ultra-réactive ».

**Légende des verdicts :**
- 🟩 **APP-NATIVE** — logique propre, aucun Hektor. Garder toujours.
- 🟦 **SERVICE** — indispensable pour un des 3 services externes. Garder jusqu'à son remplacement.
- 🟥 **SURCOUCHE** — existe uniquement pour le lien Hektor. Disparaît à la coupure (retirer/redispatcher).
- ⚙️ **ETL** — construit la couche métier depuis le miroir Hektor. À revoir (devient inutile quand l'app écrit direct dans Supabase).

---

## PARTIE 1 — Workers Console (`console_job_worker.js`), 4 services Windows

### Service `actions` (`ACTION_JOB_TYPES`, worker.js:28)
| job_type | Fonction | Verdict |
|---|---|---|
| `create_hektor_mandat_auto_number` (:9353) | Génère le **numéro de mandat officiel** (moteur `protexa` Hektor) | 🟦 **SERVICE 1** — garder jusqu'à API partenaire |
| `update_hektor_annonce_fields` (:8378) | Pousse les champs d'annonce édités vers Hektor | 🟥 → migration 2×/jour |
| `create_hektor_draft_annonce` (:12144) | Crée l'annonce dans Hektor (wizard Playwright) | 🟥 → 2×/jour ou app-native |
| `link_hektor_mandant` (:9148) | Lie un mandant à une annonce dans Hektor | 🟥 → 2×/jour |
| `create_hektor_contact` (:10524) | Crée un contact dans Hektor | 🟥 → 2×/jour |
| `update_hektor_contact` (:10557) | Pousse l'édition contact vers Hektor | 🟥 → 2×/jour |
| `add_hektor_contact_search` (:10628) | Ajoute une recherche au contact Hektor | 🟥 → 2×/jour |
| `update_hektor_contact_search` (:11019) | Pousse l'édition de recherche | 🟥 → 2×/jour |
| `delete_hektor_contact_search` (:11107) | Supprime une recherche dans Hektor | 🟥 → 2×/jour |
| `create_hektor_mandant_contact` (:11189) | Crée un mandant dans Hektor | 🟥 → 2×/jour |
| `update_hektor_mandant_contact` (:11339) | Met à jour un mandant dans Hektor | 🟥 → 2×/jour |

### Service `admin` (`ADMIN_JOB_TYPES`, worker.js:56)
| job_type | Fonction | Verdict |
|---|---|---|
| `delete_hektor_annonce` (:11681) | Supprime l'annonce dans Hektor | 🟥 → 2×/jour (état supprimé app-first) |
| `archive_hektor_annonce` (:11854) | Archive dans Hektor | 🟥 → 2×/jour |
| `restore_hektor_annonce` (:11769) | Désarchive dans Hektor | 🟥 → 2×/jour |
| `change_hektor_annonce_status` (:8938) | Change le statut dans Hektor (incl. clôtures) | 🟥 → 2×/jour |
| `assign_hektor_annonce_negotiator` (:9019) | Affecte un négo dans Hektor | 🟥 → 2×/jour |
| `delete_hektor_contact` (:11572) | Supprime un contact dans Hektor | 🟥 → 2×/jour |

> Tout `admin` = **push de cycle de vie**. Cible : l'app change l'état **immédiatement** (colonne app), la migration 2×/jour répercute vers Hektor. Aucun de ces jobs n'a besoin d'être synchrone.

### Service `documents` (`DOCUMENT_JOB_TYPES`, worker.js:41)
| job_type | Fonction | Verdict |
|---|---|---|
| `generate_mandat_document` (:5641) | **Rend le PDF mandat** (Puppeteer, HTML fourni par l'app) puis enchaîne l'upload Hektor | 🟩 **APP-NATIVE** (génération) — garder ; l'upload devient optionnel |
| `generate_estimation_pdf` (:5467) | Rend le PDF d'estimation (app) | 🟩 **APP-NATIVE** |
| `generate_cadastre_document` (:5834) | Rend le doc cadastre (app) | 🟩 **APP-NATIVE** |
| `relance_signature` (:3853) | **ImmoSign** — relance les signataires (XMLRPC) | 🟦 **SERVICE 2** — garder jusqu'à Yousign |
| `cancel_signature_procedure` (:3889) | **ImmoSign** — annule la procédure | 🟦 **SERVICE 2** — garder jusqu'à Yousign |
| `upload_document_to_hektor` (:5934) | Dépose le doc dans Hektor (**prérequis à la signature ImmoSign**) | 🟦/🟥 — garder tant que signature = ImmoSign, sinon retirer |
| `delete_document_from_hektor` (:6112) | Supprime un doc dans Hektor | 🟥 → 2×/jour |
| `upload_hektor_photo` (:6067) | Envoie une photo à l'annonce Hektor | 🟥 → 2×/jour (voir étape « master = Storage ») |
| `sync_hektor_photos` (:3991) | Réconcilie le jeu de photos vers Hektor | 🟥 → 2×/jour |
| `sync_console_documents` (:3931) | **Lit** la liste/blobs de docs depuis Hektor (+ statut signature signé) | 🟥 PULL — garder tant que signature = ImmoSign (récupère le PDF signé), sinon retirer |
| `prepare_document_cloud` (:4037) | Miroir des docs Hektor vers stockage cloud | ⚙️/🟩 — devient archive app |
| `prepare_archived_annonce_detail` (:3185) | Scrape le détail d'une annonce archivée (Console) | 🟥 PULL — inutile une fois le cache seedé |
| `prepare_historical_annonce_detail` (:3218) | Scrape le détail d'une annonce historique | 🟥 PULL — idem |

### Service `sync_light` (`SYNC_LIGHT_JOB_TYPES`, worker.js:70)
| job_type | Fonction | Verdict |
|---|---|---|
| `refresh_console_data` (:3091) | **Read-through annonce** : relit Hektor → reconstruit `app_dossier_*` | 🟥 **le read-through** — neutraliser l'autorité (pré-Phase A), retirer à la coupure |
| `refresh_console_contact_data` (:3154) | **Read-through contact** : relit Hektor → reconstruit `app_contact_current` | 🟥 idem |

### Hors 4 services
| Kind | job_type | Fonction | Verdict |
|---|---|---|---|
| `matterport` | `matterport_online/offline/archive/reactivate` (:12158) | Pilote les visites 3D Matterport (SaaS externe, **PAS Hektor**) | 🟩 garder si Matterport utilisé (indépendant de Hektor) |
| `sync_full` | `archive_cloud_documents` (:12276) | **Stub — lève « will be implemented »** | ignorer |

---

## PARTIE 2 — Pipeline de nuit (`run_full_pipeline.ps1`, tâche `GTI Quotidien` 05:30)

### Extraction depuis Hektor (PULL) — 🟥 SURCOUCHE (retirer à la coupure ; neutraliser l'autorité en Phase A)
`sync_raw.py` (API Hektor → sqlite), `sync_contact_details.py`, `sync_active_searches.py` (tâche 03:00), `sync_hektor_chauffages.py`, `sync_console_contact_missing.py`, `sync_console_missing_fields.py`, `sync_hektor_drafts.py`, `backfill_hektor_mandats.py`, `sync_archived_annonce_details.py`, `refresh_single_annonce.py`, `enqueue_console_sync_jobs.js`.

### ETL / construction de la couche métier — ⚙️ à revoir
`normalize_source.py`, `build_case_index.py`, `bootstrap_phase2.py`, `refresh_views.py`, `build_contacts_layer.py`, `run_quality_checks.py`, `contact_sync_status.py`.
> Ces workers **normalisent le miroir Hektor** puis le poussent à Supabase. Quand l'app écrit **directement** dans Supabase (déjà le cas pour les éditions), **la chaîne sqlite → normalize → push devient inutile** pour tout ce que l'app possède. C'est la plus grosse simplification post-coupure.

### Push local → Supabase (l'app DB) — ⚙️ (deviennent inutiles quand Supabase = maître direct)
`push_upgrade_to_supabase.py` (dossiers), `push_contacts_to_supabase.py` (contacts), `push_hektor_directory_to_supabase.py` (annuaire négo — **source Hektor à remplacer** pour l'identité), `push_single_annonce_to_supabase.py`, `affaire_ledger.py` (filet delete-never — source Hektor aujourd'hui).

### Diffusion — 🟦 SERVICE 3
`hektor_diffusion_writeback.py` + `backend/app/services/hektor_bridge.py` + edge function `supabase/functions/hektor-diffusion/`. Garder jusqu'à l'agrégateur de flux.

### Autres exports — 🟩
`sync_matterport_models.py` (Matterport), `backfill_appointment_public_links.py` (app), `export_project_vitrine.py` (vitrine GitHub).

---

## PARTIE 3 — Workers app-natifs — 🟩 GARDER TOUJOURS (aucun Hektor)
- **Rapprochement / scoring** : RPC Postgres (`app_match_score_v2`, `app_refresh_rapprochements_for_dossier`, `app_process_rapprochement_dirty`) — pas un worker, synchrone.
- **pg_cron** : `app-contact-push-due` (enqueue les éditions → deviendra l'alimentation du 2×/jour), `mandat-echu-alerts` (0 6 * * *).
- **backend Python** : `relance_worker.py`/`relance_engine.py` (auto-send bloqué par défaut), `rapprochement_sender/email`, `estimation_sender/email`, ingestion open-data `ingest_dvf/loyers/insee/georisques`.
- **Monitoring** : `check_gti_health.py`, `heartbeat.py` (`app_worker_registry`).
- **Intégrations** : Google agenda/workspace, prise de RDV/QR, espace client, tracking email/RGPD, agents IA (scan fiche).

---

## PARTIE 4 — Ce qui reste indispensable pour les 3 services (la liste à GARDER)

| Service | Workers à garder | Remplacement cible |
|---|---|---|
| **1. Numéro de mandat** | `create_hektor_mandat_auto_number` | API partenaire + registre app |
| **2. Signature** | `relance_signature`, `cancel_signature_procedure`, `upload_document_to_hektor` (dépôt = prérequis ImmoSign), `sync_console_documents` (récupère le PDF signé + statut) | **Yousign direct** (l'app génère déjà le PDF ; suivi via webhook Yousign) |
| **3. Diffusion** | `hektor_diffusion_writeback` + `hektor_bridge` + edge fn `hektor-diffusion` | Agrégateur de flux (Ubiflow/Poliris) ou dépôt manuel au début |

**Tout le reste des workers Hektor (🟥) = surcouche** : soit redispatché dans la migration 2×/jour (push/cycle de vie), soit retiré (read-through, pull, ETL de miroir) quand l'app est autoritaire.

---

## PARTIE 5 — Séquence proposée (pré-Phase A = « cure d'amaigrissement », puis Phase A)

**Étape 0 — Contrat d'autorité.** Figer la liste des champs/entités possédés par l'app.

**Pré-Phase A — retirer Hektor du parcours utilisateur (ce que tu décris) :**
1. **Neutraliser l'autorité du read-through** : `refresh_console_*` ne reconstruit plus les données app-owned. L'écriture Supabase de l'app est finale.
2. **Simplifier le calque** : supprimer overlay / `base_snapshot` / `conflict` (ils n'existaient que pour cohabiter avec le read-through). Édition = écrire la colonne, fini. **Zéro worker dans le parcours → ultra-réactif.**
3. **Rendre optimistes les créations + cycle de vie** (contact/mandant/recherche/statut/archive) comme l'annonce provisoire : l'app montre tout de suite, le push part en arrière-plan.
4. **Garder synchrones uniquement les 3 services** (mandat/signature/diffusion) — ce sont les seuls appels externes qui restent visibles.

**Phase A — migration globale 2×/jour :**
5. Le push (`update_hektor_*`, créations, cycle de vie) n'est plus déclenché à chaque édition mais **vidé 2×/jour** vers Hektor (un seul login, un seul lot). Sens unique app → Hektor.
6. **Arrêter l'autorité du pipeline de nuit** : `push_upgrade`/`push_contacts` ne réécrivent plus les champs app-owned (le mécanisme existe déjà pour naissance/matrimonial contact — on l'étend).

**Phases B/C** — remplacer les 3 prises une par une (API mandat, Yousign, agrégateur), puis couper = éteindre le worker de migration.

---

## Risque #1 (comportemental, pas technique)
Pendant la cohabitation, **une seule porte d'écriture = l'app**. Si un négo édite aussi dans Hektor, la migration 2×/jour écrasera son geste. → Consigne négo : « on travaille uniquement dans l'app, on ne touche plus Hektor ».

## Sécurité (relevé, à traiter à part)
`app_rapprochement_search_state` a **RLS désactivé** (exposé). `ENABLE ROW LEVEL SECURITY` + policy avant tout, sinon ça bloque le moteur.
