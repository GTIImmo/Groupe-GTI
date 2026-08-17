# Étude de faisabilité — Rendre l'app « source de vérité » et découpler Hektor (app-first)

**Date : 2026-08-08. Auteur : audit Claude (5 explorations parallèles code + base réelle) à la demande de Frédéric.**
**Statut : ANALYSE (rien codé). Prolonge et met à jour `NOTE_STRATEGIE_COUPURE_HEKTOR_2026-07-01.md`.**
**Mémoire liée : `architecture-app-et-coupure-hektor`.**

---

## 0. Ta demande, reformulée

1. Les éléments **saisis/modifiés dans l'app ne doivent plus dépendre du retour Hektor** (l'app affiche « fait » sans attendre Hektor).
2. **Garder pour l'instant** certains workers indispensables — explicitement **la génération du numéro de mandat**, et de fait la signature et la diffusion.
3. Construire **un worker global toutes les 24 h** qui envoie à Hektor (au lieu du push par édition + réimport de nuit).
4. **Ne rien casser.**

**Verdict global : faisable, à risque maîtrisé si progressif. ~70 % du socle existe déjà.** Le pattern « écrire chez soi + pousser en différé » (outbox) tourne déjà pour 3 entités. Le chantier n'est pas une réécriture : c'est **inverser l'autorité** (arrêter le réimport de nuit qui écrase) + **généraliser l'outbox** + **regrouper les push en un batch 24 h**. Les 3 verrous externes (numéro de mandat/création, signature, diffusion) **restent branchés** — c'est compatible avec ta demande.

---

## 1. Ce que l'audit a confirmé (état des lieux réel)

### 1.1 L'architecture d'écriture actuelle, en 3 temps
Toute édition suit la même forme :
1. **Écriture optimiste** : une RPC SQL `SECURITY DEFINER` écrit dans les tables `*_current` de Supabase (+ un blob overlay pour l'annonce) et pose une ligne dans une file `*_pending` avec un `push_after` débouncé. Retour instantané → l'utilisateur voit le changement tout de suite.
2. **Mise en file débouncée** : un `pg_cron` (toutes les minutes) transforme les lignes *dues* en jobs `app_console_job` (`update_hektor_*`).
3. **Worker + read-through** : `Console/console_job_worker.js` prend le job, pousse vers Hektor (Playwright/HTTP), vide la ligne pending, puis déclenche un **read-through** (`refresh_console_data`/`refresh_console_contact_data`) qui **re-lit Hektor et reconstruit `*_current` → l'overlay optimiste disparaît** (Hektor gagne).

### 1.2 Ce qui est DÉJÀ « app-first » (édition optimiste, n'attend PAS Hektor)
- **Champs d'annonce/bien** : `app_edit_annonce_optimistic` → `app_dossier_current`/`app_dossier_detail_current` (overlay `app_optimistic_overlay`) + `app_annonce_pending` → job `update_hektor_annonce_fields`.
- **Contact (fiche)** : `app_edit_contact_optimistic` → 12 colonnes de `app_contact_current` (modèle plat) + `app_contact_pending` → job `update_hektor_contact`.
- **Recherche acquéreur (critères)** : `app_edit_search_optimistic` → `app_contact_search_current` + `app_search_pending` → job `update_hektor_contact_search`. Recompute rapprochement immédiat.
- **Débounce actuel** : `debounce_seconds = 600` (10 min), plancher 30 s ; sweeps `app_*_enqueue_due_pushes()` toutes les minutes. Une ré-édition ré-arme `push_after` (coalescence).
- **Garde-fou anti-écrasement** : `base_snapshot._date_maj` + flag `conflict` — si le `date_maj` Hektor a bougé depuis l'édition, on **refuse de pousser** et on part en `conflict` (Hektor gagne).

### 1.3 Ce qui BLOQUE encore sur le retour Hektor (créations + cycle de vie)
Ces flux passent par un **job** et l'app reste en `syncing`/« en cours » jusqu'à ce que le worker + read-through finissent :
- **Créations** : `create_hektor_draft_annonce` (annonce ; atténué par la ligne `app_annonce_provisional` « En création »), `create_hektor_contact`, `create_hektor_mandant_contact`, `add_hektor_contact_search`.
- **Numéro de mandat** : `create_hektor_mandat_auto_number` — le `numero_mandat` n'existe pas tant que le job n'a pas rendu `result_json.numero_mandat` ; **toutes les étapes gâtées par le mandat restent verrouillées**.
- **Cycle de vie annonce** : `change_hektor_annonce_status`, `assign_hektor_annonce_negotiator`, `archive/restore/delete_hektor_annonce`, `delete_hektor_contact` (re-entrance bloquée pendant qu'un job est actif).
- **Binaires** : `upload_hektor_photo`, `sync_hektor_photos`, `upload_document_to_hektor`, `delete_document_from_hektor` (master binaire = Hektor).
- **Synchrones temps réel** : diffusion (`applyDiffusionTargetsOnHektor`) et acceptation de demande — renvoient un flag `waiting_on_hektor` et laissent l'UI en « En attente de mise à jour Hektor ».

### 1.4 Le défaut structurel unique (cause de la majorité des bugs)
**Hektor est à la fois SOURCE et DESTINATION :**
- SOURCE = le réimport de nuit `run_full_pipeline.ps1` → `push_upgrade_to_supabase.py` + `push_contacts_to_supabase.py` **réécrit** `app_dossier_current`, `app_contact_current`, `app_mandat_*` depuis le miroir Hektor.
  ⚠ **Correction vs note 2026-07-01** : le prototype `ACTIF/actif_sync.py` cité comme coupable a été **désactivé le 2026-07-05** (`patch_actif_workers_disabled_2026-07-05.sql`). Le réimport autoritaire réel = les deux scripts `push_*_to_supabase.py` ci-dessus, lancés par `GTI Quotidien` (05:30) avec `-AllowStaleSupabaseDeletes`.
- DESTINATION = le push optimiste.
Cette double casquette = écrasements, read-through qui vide, idnego, trous de sync.

### 1.5 Ce qui est DÉJÀ 100 % indépendant de Hektor (sans risque à la coupure)
Toute la **couche analytique/workflow** possède ses données et ne fait que *référencer* des ids Hektor :
- **Moteur de rapprochement (scoring)** — calcul 100 % Postgres (`app_match_score_v2`, `app_refresh_rapprochements_for_dossier`, `app_process_rapprochement_dirty`), 58 k matches + 445 k historique. **Le point fort** : survit à la coupure dès que le catalogue est seedé.
- **Estimation / avis de valeur** — sources 100 % open-data (DVF 84 k, cadastre IGN, INSEE, Géorisques, loyers) ; PDF interne Puppeteer. Zéro Hektor (clé `app_dossier_id` seulement).
- **Relances, propositions, alertes (`app_alert_state`), notifications, monitoring/heartbeat**.
- **Agenda RDV Google, prise de RDV publique/QR, espace client, tracking email/consentement RGPD, agents IA (scan fiche), Matterport.**

### 1.6 Les entités « hybrides » (en cours d'inversion)
- **Contacts** : `app_contact_override` est déjà **source de vérité app** pour les champs que l'API Hektor ne rend pas (adresse, naissance, statut marital, commentaires, RGPD).
- **Affaires (offre/compromis/vente)** : `app_affaire_ledger` = filet « delete-never » (retenu même si Hektor le retire) — mais **la source reste Hektor** (lu via API). C'est de la *rétention*, pas encore une *origine* app.
- **Mandats/registre** : dérivé du miroir ; clôture désormais app-owned (`register_mandat_cloture`, `mandat_echu_*`).

---

## 2. Le pivot conceptuel (l'image à retenir)

- **Aujourd'hui** : Hektor = *cahier officiel*, l'app = *photocopie recopiée chaque nuit* → la nuit peut effacer ce qu'on a écrit dans la journée.
- **Cible** : **l'app = cahier officiel ; Hektor = copie** qui reçoit un **flux sortant unique** (le worker 24 h). **Sens unique app → Hektor.** Fini le réimport autoritaire.
- **Le jour de la coupure** = débrancher un fil (désactiver le worker de push). Zéro migration, zéro conflit.

Concrètement, 3 bascules :
1. **Neutraliser l'écrasement de nuit** sur les champs/entités « possédés par l'app ».
2. **Tout passe par l'outbox** (généraliser le pattern des 3 entités déjà faites).
3. **Le push devient un batch 24 h** (au lieu du débounce 10 min + réimport).

---

## 3. Ce qui casse / ce qui ne casse pas

### Ne casse pas
- Toute la couche analytique (§1.5) : elle lit le miroir déjà seedé et n'écrit rien vers Hektor. Clé = ids Hektor déjà présents.
- Les 3 éditions déjà optimistes (§1.2) : elles n'attendent déjà pas Hektor.

### Points de vigilance (ce qui PEUT casser si mal fait)
| Risque | Détail | Parade |
|---|---|---|
| **Le combat réimport ↔ app** | Si le batch 24 h pousse ET que le réimport de nuit réécrit par-dessus, ils se battent. | **Étape 1** : liste blanche des « champs app-owned » que `push_*_to_supabase.py` ne réécrit plus. Vérifier d'abord si ces scripts respectent déjà le skip `*_pending`/`override` que fait le read-through mono-annonce (`push_single_annonce_to_supabase.py` saute les lignes dirty). |
| **Sens du garde-fou anti-écrasement** | `base_snapshot/date_maj/conflict` fait aujourd'hui « Hektor gagne ». En mode app-autoritaire, pour les champs app-owned, il faut « l'app gagne ». | Décider par champ : app-owned → l'app gagne (on ne part plus en `conflict`) ; champ Hektor-only → statu quo. |
| **IDs** | Tout est clé par ids Hektor (`app_dossier_id`, `hektor_contact_id`, couple `(annonce, mandat)`). Créer une entité **sans** Hektor exige des IDs app-owned (UUID) + mapping. | **On repousse ce risque** : on GARDE la création via Hektor (numéro de mandat) pour l'instant → pas besoin d'IDs app-owned tout de suite. C'est l'étape 5 (plus tard). |
| **Fenêtre de retard Hektor** | Passer de 10 min à 24 h allonge la fenêtre où Hektor est en retard sur l'app. | OK **tant que l'app est la vérité** et qu'on ne modifie plus dans Hektor en parallèle (règle : **une seule voie d'écriture par entité**). Garder un « push immédiat » pour diffusion/signature. |
| **Sécurité (hors sujet mais relevé)** | `app_rapprochement_search_state` a **RLS désactivé** (exposé `anon`). | À traiter séparément : `ENABLE ROW LEVEL SECURITY` + policy (sinon ça bloque le moteur). Décider avant d'appliquer. |

---

## 4. Le worker global 24 h (le cœur de ta demande)

**But** : au lieu de pousser à chaque édition (débounce 10 min) + réimporter la nuit, **regrouper tous les envois vers Hektor en un seul passage quotidien**.

**Bonne nouvelle** : les briques existent déjà (files `app_*_pending`, sweeps `app_*_enqueue_due_pushes`, `console_job_worker`). Deux variantes :

- **Variante A — minimale (config)** : passer le `debounce_seconds` des éditions de 600 s à « prochain créneau nuit » (p. ex. push_after = 02:00). L'outbox existant **devient** un push quotidien. Réutilise tout, quasi zéro code. *Idéal pour démarrer.*
- **Variante B — propre (orchestrateur dédié « SyncCrmPort »)** : un worker qui, à H fixe, (1) se logue **une seule fois** à Hektor, (2) liste toutes les lignes `*_pending` dues + rejoue les créations en attente, (3) pousse en lot, (4) fait **un seul** read-through de réconciliation à la fin. Plus lisible, plus de travail, meilleure observabilité.

**Recommandation** : commencer par **A** (soulagement immédiat, faible risque), viser **B**.

**IMPORTANT** : garder un **chemin de push immédiat** pour les 2 flux qui ne tolèrent pas 24 h de retard → **numéro de mandat** (tu veux un numéro tout de suite) et **diffusion/signature**. Le batch 24 h ne concerne que les éditions et créations non urgentes.

---

## 5. Ce qu'on garde branché sur Hektor « pour l'instant » (compatible ta demande)

Ces flux restent des **jobs à la demande** (hors batch 24 h), inchangés :
- **Numéro de mandat** (`create_hektor_mandat_auto_number`) — moteur `protexa` Hektor, irremplaçable app-side aujourd'hui. ← ton « worker indispensable ».
- **Création annonce** (`create_hektor_draft_annonce`) — reste via Hektor (mais on peut la rendre plus optimiste à l'affichage, la ligne `app_annonce_provisional` existe déjà).
- **Signature ImmoSign** (`relance_signature`, `cancel_signature_procedure`) — verrou externe.
- **Diffusion portails** — verrou externe (Hektor détient les identifiants portails).

---

## 6. Plan par étapes (valeur à chaque étape, risque croissant)

- **Étape 0 — Contrat d'autorité (préparatoire, 0 risque).** Écrire noir sur blanc la **liste des champs/entités possédés par l'app** (ceux que Hektor ne doit plus écraser). C'est LA décision structurante ; tout le reste en découle.
- **Étape 1 — 🟢 Neutraliser l'écrasement de nuit (gros ROI, invisible utilisateur).** `push_upgrade_to_supabase.py` + `push_contacts_to_supabase.py` ne réécrivent plus les champs app-owned (seed une fois + ne touche plus). Vérifier/étendre le skip `*_pending`/`override`. → **fin de la classe de bugs d'effacement.**
- **Étape 2 — 🟢 Photos/documents « CRM-first ».** Master binaire = **Supabase Storage** (au lieu de Hektor) ; push Hektor différé best-effort ; le bloc Documents lit Supabase.
- **Étape 3 — 🟡 Worker global 24 h.** Variante A (config du débounce → créneau nuit) puis B (orchestrateur `SyncCrmPort`). Garder push immédiat pour mandat/diffusion/signature.
- **Étape 4 — 🟡 Créations optimistes à l'affichage.** Étendre le pattern `app_annonce_provisional` aux créations contact/mandant/recherche : l'utilisateur ne subit plus l'attente même si la création Hektor reste derrière.
- **Étape 5 — 🔴 IDs app-owned + création app-first (plus tard).** L'app génère l'UUID à la création → règle définitivement l'idnego. À faire quand tu voudras vraiment couper.
- **Étape 6 — 🔴 Remplacer les verrous externes (plus tard).** Diffusion → agrégateur de flux (Ubiflow/Poliris) ; signature → Yousign direct (les PDF sont déjà internes).
- **Étape 7 — ✅ Couper Hektor.** Désactiver le worker de push. Hektor → read-only → archive → off.

**Ta demande = Étapes 1 + 3 (+ 4)**, en gardant les verrous branchés. C'est le bloc le plus rentable et le moins risqué.

---

## 7. Méthode de test (E2E, façon cadastre)
Pour chaque étape : bien de test dédié → déclencher l'action → suivre `app_console_job` + les tables `*_pending`/`*_current` → vérifier (a) affichage instantané, (b) push Hektor au bon moment, (c) pas d'écrasement après le réimport de nuit, (d) pas de clignotement/doublon. **Signature : uniquement `frederic.gerphagnon@` (jamais de vrais mandants, facturé).**

---

## 8. Décisions à trancher AVANT de coder
1. **Le contrat d'autorité (Étape 0)** : quels champs deviennent « app-owned » (l'app gagne) ? Proposition de départ : prix, description, champs saisis dans l'app, photos/docs, critères de recherche, identité contact. À valider champ par champ.
2. **Variante du worker 24 h** : A (config, rapide) d'abord, ou directement B (orchestrateur) ?
3. **Créneau du batch** : heure du push quotidien (p. ex. 02:00, avant le pull 05:30 ? ou après ?). L'ordre pull/push doit être décidé pour éviter le combat.
4. **Périmètre du « immédiat »** : confirmer que seuls numéro de mandat + diffusion + signature gardent un push temps réel.
5. **Par où commencer** : reco = Étape 1 (meilleur rapport soulagement/effort), puis Étape 3.

---

## 9. Rappels projet
- Ne rien coder sans « go » explicite ; brancher fichier par fichier (jamais `git add .`) ; valider le front avec `npm run build`.
- Pendant la cohabitation : **une seule voie d'écriture par entité** (l'app). Éviter d'éditer en parallèle dans Hektor.
- Pas de big-bang : Étapes 1 & 2 sont additives, faible risque, invisibles utilisateur.
