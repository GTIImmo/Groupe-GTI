# Plan — Édition CONTACT optimiste (homogénéisation avec annonces/recherches)

Date : `2026-06-22`

## Pourquoi
L'édition d'un contact (`createUpdateHektorContactJob`) est un **job DIRECT** : pas
d'affichage instantané, pas de débounce, et **pas de garde-fou anti-écrasement** (risque
d'écraser un changement Hektor concurrent). Les **annonces** et les **recherches** ont,
elles, toute la pile optimiste. Objectif : donner au contact le **même schéma**.

## Modèle de référence (déjà en place, à cloner)
RPC `app_edit_annonce_optimistic` + table `app_annonce_pending` + cron `app-annonce-push-due`
+ worker `handleUpdateHektorAnnonceFields` (guard date_maj + clear pending) + front
`editAnnonceOptimistic` + dirty-skip dans le push. (Idem version recherche.)

---

## Les Lots

### Lot A — Backend Supabase (migrations)
- **A1. Table `app_contact_pending`** (miroir de `app_annonce_pending`) :
  `hektor_contact_id` (PK), `push_fields` jsonb, `base_snapshot` jsonb, `push_after`,
  `conflict`, `source`, `dirty_by`, `push_attempts`, `dirty_at`, `updated_at`.
- **A2. RPC `app_edit_contact_optimistic(target_contact_id, edit_fields, debounce_seconds default 600)`** :
  - permission `app_console_can_request_contact_job` ;
  - **écriture optimiste** des champs édités dans `app_contact_current` (nom, prénom, email,
    tél, adresse, CP, ville, civilité, RGPD/CRM flags…) ;
  - `base_snapshot` = valeurs pré-édition + `_date_maj` (= `app_contact_current.date_maj`)
    pour l'anti-écrasement ;
  - upsert `app_contact_pending` avec `push_fields` + `push_after = now()+debounce`.
  - ⚠️ PAS de recompute (les champs d'identité contact ne pilotent pas le rapprochement ;
    seuls les critères de recherche le font → déjà couvert par `app_edit_search_optimistic`).
- **A3. Cron `app-contact-push-due`** (*/1 min) : balaie `app_contact_pending` où
  `push_after <= now()` → crée un job `update_hektor_contact` avec `from_pending=true` +
  `push_fields` + `base_snapshot`.

### Lot B — Worker (console_job_worker.js)
- **B1. `handleUpdateHektorContact`** : ajouter la branche `from_pending` :
  - garde-fou anti-écrasement (relire le contact Hektor, comparer `date_maj` à
    `base_snapshot._date_maj` ; si plus récent → `markContactPendingConflict` + `held_conflict`) ;
  - puis écriture (existe déjà) ; puis `clearContactPending`.
- **B2. helpers `clearContactPending` / `markContactPendingConflict`** (miroir annonce).
- ✅ L'écriture passe déjà par `ensureHektorExecutionContext` → **bénéficie du fallback
  agence** (contact à négo inactif écrivable).

### Lot C — Front (api.ts + App.tsx)
- **C1. `editContactOptimistic({contactId, fields, debounceSeconds})`** (api.ts) → appelle
  `app_edit_contact_optimistic`.
- **C2. `ContactEditModalV2.handleSave`** : remplacer `createUpdateHektorContactJob` par
  `editContactOptimistic` + `dispatchEvent('hektor:contact-updated')`.
- **C3. Listener `hektor:contact-updated`** → recharge la fiche contact (comme
  `hektor:annonce-updated`).

### Lot D — Sync Python
- **D1. Dirty-skip** dans `push_contacts_to_supabase.py` : exclure les contacts ayant un
  `app_contact_pending` (miroir du dirty-skip annonces dans `push_upgrade`) → éviter que le
  sync écrase la valeur optimiste avant le push.

---

## Chiffrage / effort
≈ même ampleur que le Tier 2 annonce (déjà fait) : **1 table + 1 RPC + 1 cron** (Supabase,
migrations au coup par coup) ; **worker** (2 helpers + guard, additif, restart) ; **front**
(1 fonction api + modale + listener, push main) ; **1 dirty-skip** Python.

## Points d'attention
- Mapper **tous les champs** que la modale édite (identité + RGPD/CRM).
- `app_contact_current.date_maj` = référence de l'anti-écrasement (à confirmer qu'il bouge
  bien quand le contact change dans Hektor).
- Permission : `app_console_can_request_contact_job` (existe).
- Le push contact impersonne le négo du contact → fallback agence OK pour négo inactif.

## Règles
Additif/chirurgical, migrations prod au coup par coup, déploiement front = push main,
worker = restart par l'utilisateur. Tests sur le contact 603798.
