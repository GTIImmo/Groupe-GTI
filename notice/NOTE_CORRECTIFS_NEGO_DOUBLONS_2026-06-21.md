# Correctifs — Résolution négociateur, écritures différées & doublons dossiers

Date : `2026-06-21`
Branche : `refonte-mobile` → `main` (Vercel + scripts locaux)

Synthèse d'une session de correctifs autour de : la **résolution du négociateur**
(qui bloquait les écritures Hektor), la **liste des négos** dans les formulaires,
le **read-through** à l'ouverture des annonces, et un **audit complet de la data**
avec nettoyage de doublons.

---

## 1. Contexte / racine commune

La plupart des problèmes venaient d'**une seule racine** : la table
`app_user_directory` ne contenait que les **~12 utilisateurs directs du compte
parent** de l'API (dont **2 NEGO** seulement), car alimentée par
`/Api/User/UsersOfParent/`. Or :

- les **formulaires** (création annonce/estimation/contact, réaffectation,
  pré-sélection négo en fiche contact) listaient les négos via cette table → **2 négos** au lieu de ~30 ;
- la **résolution du négo** (worker `resolveHektorExecutionUser` +
  `loadHektorDirectoryUserById/ByEmail` + RPC `app_console_resolve_contact_hektor_user`)
  **dépend de `app_user_directory (user_type=NEGO)`** → tout négo absent (ex. franck user 2)
  = écriture Hektor bloquée (« Contexte negociateur Hektor requis »).

Le vrai actif (`listNegos actif=1`) = **~30 négociateurs**.

---

## 2. Correctifs CODE (commits)

| Commit | Fichier(s) | Problème | Correctif |
|---|---|---|---|
| `a336c92` | `apps/hektor-v1/src/lib/api.ts`, `App.tsx` | Modale « modifier un contact » ne pré-sélectionnait pas le négo du contact | `loadNegotiatorOptionForContact` (annuaire complet, sans le filtre cassé) + injection/pré-sélection dans `ContactEditModalV2` |
| `cec7b24` | `api.ts`, `push_hektor_directory_to_supabase.py` | Liste négo bloquée à 2 (filtre `app_user_directory`) | `loadHektorNegotiatorOptions` filtre sur la colonne `is_active` de l'annuaire ; `is_active` dérivé de `listNegos actif=1` (~30) au lieu de `UsersOfParent` |
| `5258aa3` | `push_hektor_directory_to_supabase.py` | Écritures Hektor bloquées : résolution worker+RPC dépend de `app_user_directory` (2 NEGO) | Les négos actifs deviennent de **vrais utilisateurs NEGO** dans `app_user_directory` (`fetch_active_negos`+`build_nego_user_rows`, fusionnés dans `user_rows` → conservés par le purge) |
| `0c86376` | `push_hektor_directory_to_supabase.py` | Cas « compte NEGO sur l'API mais ADMIN dans le parent » casserait la résolution | Garde-fou : un négo actif est forcé en `NEGO` même s'il est aussi ADMIN (rien ne lit `user_type=ADMIN` ; le rôle admin app vient du profil) |
| `4b23efa` | `push_single_annonce_to_supabase.py` | Read-through annonce plantait en **409 duplicate key** sur `app_mandat_register_current` | INSERT → **UPSERT** (PK `register_row_id`) — robuste aux doublons de dossier |
| `39ca6d5` | `push_single_annonce_to_supabase.py` | Un changement d'id de dossier laissait un **dossier fantôme** (purge périmés désactivée par sécurité) | `reconcile_annonce_dossiers` : à chaque read-through, supprime les app_dossier de la **même annonce** dont l'id diffère (ciblé par `hektor_annonce_id`, re-pointe le registre) |

Rappel (déjà en place avant la session, validés ici) : `0bb8990` (Tier 2 édition
optimiste des biens), `963a1df` (read-through anti-spam 30 min contact+bien).

---

## 3. Correctifs DATA (SQL, sur l'index courant — sans ré-extraction)

- **`app_hektor_negotiator_agency_directory.is_active`** matérialisé sur l'index
  courant (overlay 3 colonnes), puis re-calculé à 30 par le sync corrigé.
- **`app_user_directory`** : overlay des négos actifs en NEGO (transitoire), puis
  rendu **durable** par le code `push_hektor_directory` (cf `5258aa3`). État : 40
  users (12 parent + 30 négos), **vérifié sans risque user/Google** (0 collision /
  doublon d'email → pas de conflit `_resolve_hektor_google_identity` ; 29/30 emails
  Workspace `@gti-immobilier.fr`).
- **Annonce de test VA6482** (`app_dossier 1068399`, hektor 24113) : négo remis
  correctement (franck, négo 1 / user 2) ; valeurs de test restaurées (prix 128001,
  surface 12) après le test e2e.
- **Suppression de 6 doublons app_dossier** (fantômes) — cf §5.

---

## 4. Validations réelles effectuées

- **Tier 2 (édition optimiste annonce) bout-en-bout** : édition → recompute →
  pending → cron `app-annonce-push-due` → worker → **écriture Hektor réelle
  confirmée via API `AnnonceById`** (prix/surface reçus, `datemaj` bumpé), puis
  restauré.
- **Anti-spam read-through** : 3 appels rapprochés → **1 seul job** (dédup pending
  + TTL 30 min), mécanisme confirmé dans les RPC.
- **Résolution négo** : `app_console_resolve_contact_hektor_user(603798)` → user 2 ✅
  (échouait avant, `null`).

---

## 5. Audit complet de la data (recherche de propagation)

Crainte d'une propagation de doublons → **audit complet : data SAINE.**

| Vérification | Résultat |
|---|---|
| `app_contact_current` (57 127) | 0 doublon |
| `app_contact_search_current` | 0 doublon |
| `app_dossier_detail_current` / `work_item` / `broadcast` | 0 orphelin, 0 doublon |
| `app_mandat_register_current` (23 635) | **sain par design** : 731 courants liés + 22 904 historiques à id synthétique **négatif** distinct (lignes autonomes, vue `app_registre_mandats_current`) ; **0 vrai orphelin positif** |
| `app_dossier_current` | **6 doublons** (seul défaut réel) |

**Les 6 doublons** : une seule annonce Hektor (et 1 seul dossier local), mais **2
lignes dans Supabase** — une ancienne (id bas, fantôme) + la bonne (id haut, =
index local). Résidu de ré-indexations passées, l'ancien id non purgé.

| Annonce | N° dossier | ✅ Bon id | 👻 Fantôme supprimé |
|---|---|---|---|
| 10003 | EM18604 | 1336058 | 3 |
| 11682 | EM65910 | 1337922 | 597 |
| 11837 | VM70151 | 1338094 | 714 |
| 33220 | VI446 | 1361217 | 8405 |
| 47347 | VT9340 | 1376740 | 14416 |
| 59625 | EM71401 | 1387062 | 19425 |

→ **Nettoyés** (dossier+detail+work_item+broadcast, registre intact). Résultat :
0 doublon, 13 510 dossiers = 13 510 annonces. Et **durci** (`39ca6d5`) pour qu'ils
ne se reforment plus.

---

## 6. Outils / fichiers utiles

- `refresh_annonce_nego_from_api.py --hektor-annonce-id <id>` : re-fetch
  `AnnonceById`, met à jour le négo + `datemaj` en local (chirurgical), refuse si
  négo orphelin. Suivi de `python -m phase2.sync.push_single_annonce_to_supabase --hektor-annonce-id <id>`.

---

## 7. Points ouverts / à surveiller

- **Durabilité `app_user_directory`** : assurée par le code (`5258aa3`) tant que
  `push_hektor_directory` tourne ; le sync planifié l'entretient (30 négos actifs).
- **Trou `datemaj`** (connu, hors scope ici) : un changement Hektor qui ne bumpe
  pas `datemaj` reste invisible au delta de sync (cf note sync recherche).
- **Chantier idnego** (réaffectation des entités à négo orphelin/supprimé) : non
  traité, séparé.
