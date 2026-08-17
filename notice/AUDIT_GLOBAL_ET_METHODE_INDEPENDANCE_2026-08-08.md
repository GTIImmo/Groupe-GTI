# Audit global du projet + méthode recommandée pour l'indépendance Hektor

**Date : 2026-08-08. Synthèse Claude — vérifiée sur le code réel + la base live (`dwaqxfrinihnychuoptk`), corrections utilisateur intégrées.**
**Consolide et prime sur : `ETUDE_FAISABILITE_DECOUPLAGE_HEKTOR_APP_FIRST`, `INVENTAIRE_WORKERS_ET_PLAN_INDEPENDANCE`, `ANALYSE_IDENTITE_IDS_HEKTOR` (tous 2026-08-08).**
**Règle : aucun code. Analyse et méthode.**

---

## 1. Le projet en une image (architecture hybride « local + cloud »)

Trois lieux, pas deux :
- **Serveur local (Windows)** — le **backend lourd** : miroir `data\hektor.sqlite`, couche métier `phase2\phase2.sqlite` (~1,9 Go), **archive documents** `C:\Hektor\HektorConsoleDocuments`, les **workers** (pipeline + Console).
- **Cloud (Supabase + Vercel)** — la **face applicative** : tables `app_*`, RPC, front React, Supabase Storage (copie **sélective** de documents).
- **Hektor** — le **CRM historique** : source des imports de nuit + destination des push + héberge encore les **photos** (CDN) et 3 services externes.

**Maître réel des données aujourd'hui = ton serveur local**, projeté vers le cloud (Supabase) et recopié vers Hektor. Hektor n'est déjà plus le maître des données ni des documents — **sauf les photos.**

---

## 2. Qui est maître de quoi (tableau corrigé — c'est la clé)

| Contenu | Maître réel | Copie cloud | Copie Hektor | Indépendant de Hektor ? |
|---|---|---|---|---|
| Données dossiers/contacts | ✅ serveur local (sqlite) → Supabase | Supabase `app_*` | miroir | **Oui** (déjà écrit direct pour les éditions) |
| **Documents** (mandats, estimations, cadastre PDF) | ✅ serveur local (`HektorConsoleDocuments`, écrit EN PREMIER) | Supabase Storage **sélectif** (Actif/offre/compromis/estimation) | `upload_document_to_hektor` | **Oui** pour les docs générés par l'app |
| **Photos** | ❌ **Hektor CDN** (`staticlbi`, URLs dans `app_console_photo`) | — | Hektor | **NON — le seul vrai trou binaire** |
| Estimation, rapprochement, relances, alertes, agenda, espace client, email | ✅ app-native | Supabase | — | **Oui, 100%** |

---

## 3. Ce qui reste vraiment couplé à Hektor (la liste courte)

Après vérification, il ne reste que **4 dépendances réelles** (le reste est de la synchro) :

1. **Photos** — binaires hébergés chez Hektor (à télécharger + stocker chez toi/cloud).
2. **Numéro de mandat** — `create_hektor_mandat_auto_number` (moteur protexa). → API partenaire.
3. **Signature** — `relance_signature` + `cancel_signature_procedure` + `upload_document_to_hektor` (prérequis ImmoSign) + `sync_console_documents` (récupère le PDF signé). → Yousign.
4. **Diffusion portails** — `hektor_diffusion_writeback` + `hektor_bridge` + edge fn. → agrégateur de flux.

Tout le reste des workers Hektor = **surcouche de synchro** (push optimiste, read-through, import de nuit) → disparaît quand l'app est autoritaire. (Inventaire complet : voir note `INVENTAIRE_WORKERS_...`.)

---

## 4. Le défaut structurel unique (rappel, confirmé mais nuancé)

Hektor est **SOURCE** (import de nuit `push_upgrade`/`push_contacts_to_supabase.py`) **et DESTINATION** (push optimiste). Nuance vérifiée : l'import de nuit est un **UPSERT « merge-duplicates »** qui **ne réécrit que les colonnes qu'il porte** et **saute déjà les lignes en cours d'édition** (`fetch_dirty_*`) + **préserve les champs app-only non portés** (naissance/matrimonial). Donc l'« écrasement » est **étroit**, pas massif. Le chantier = **basculer l'autorité** (l'app gagne sur ses champs), pas réparer une destruction.

**Identité** : les dossiers ont **déjà** une clé app-owned (`app_dossier_id` ≠ ID Hektor) ; seuls les **contacts** sont encore clés sur `hektor_contact_id`. La coupure = « continuer la suite » (émetteur unique + high-water mark incluant archivés/supprimés). Détail : note `ANALYSE_IDENTITE_IDS_HEKTOR`.

---

## 5. LA MÉTHODE recommandée — « Strangler Fig » (étranglement progressif)

Principe éprouvé pour remplacer un système historique **sans big-bang** : l'app entoure déjà Hektor ; on **coupe un fil à la fois**, chaque étape a de la valeur seule et est **réversible**. Ordre du plus rentable/moins risqué au plus lourd.

### Phase 0 — Fondations (invisible utilisateur, prérequis)
- **0a. Geler l'identité interne.** Confirmer que `app_dossier_id` est **immuable** (⚠ à vérifier : ne doit pas être réassigné au rebuild). Décider pour les contacts : garder `hektor_contact_id` gelé comme app-owned, ou introduire `app_contact_id`. `hektor_*_id` = **attribut de correspondance**, plus autorité.
- **0b. Contrat d'autorité.** Lister les champs « possédés par l'app » (le mécanisme existe déjà pour naissance/matrimonial contact — on l'étend).
- **0c. Sécurité.** `ENABLE ROW LEVEL SECURITY` sur `app_rapprochement_search_state` (+ policy) — exposé aujourd'hui.
- **0d. CORRIGER L'IDENTITÉ DES RECHERCHES (planifié 2026-08-10, cf. §5ter + §5ter-bis).** Deux défauts **distincts**, à traiter ensemble :
  - **0d-1 — La clé** : remplacer `contact_search_key = hash(contenu)` par une clé **stable**, idéalement adossée à l'`idCritere` natif Hektor (déjà lisible par le worker via le scrape Console, `console_job_worker.js:10700`) ; à défaut, surrogate app persistant façon `ON CONFLICT DO UPDATE` des dossiers. **Obligatoire** : table de réconciliation ancienne→nouvelle clé (11 tables concernées, 13 353 rapprochements déjà orphelins) — ne rien supprimer, c'est irréversible.
  - **0d-2 — Le ciblage Hektor par position** (le risque de perte de donnée) : faire remonter l'`idCritere` jusqu'à l'app (aujourd'hui `api.ts:7204` envoie `target_critere_id: null` en dur), puis **supprimer le repli `|| list[0]`** et le défaut `index = 0` dans `resolveContactSearchTargetCritereId`, **au minimum pour la suppression** (`handleDeleteHektorContactSearch`, sans garde-fou aujourd'hui). Priorité : borné à 143 contacts multi-recherches, mais **perte de donnée client** possible.
  - **⚠ NE PAS reprendre** le correctif planifié en 2026-06 (`hash(contact_id, index)`) : il déplace l'instabilité vers la position et entérine 0d-2.
  - **Ordre conseillé** : 0d-2 d'abord (risque de perte, correctif petit et localisé), puis 0d-1 (plus large, nécessite la migration de réconciliation).

### Phase 1 — Hektor cesse d'être SOURCE (tue les bugs + rend ultra-réactif)
- **But** : l'écriture de l'app est **finale**, plus jamais écrasée, zéro attente worker dans le parcours.
- **1a.** Neutraliser l'autorité du **read-through** (`refresh_console_*` ne reconstruit plus les données app-owned).
- **1b.** **Simplifier le calque** : supprimer overlay / `base_snapshot` / `conflict` (ils n'existaient que pour cohabiter avec le read-through). Édition = écrire la colonne, fini.
- **1c.** Étendre le **dirty-skip** de l'import de nuit à **tous** les champs app-owned.
- **Valeur seule** : fin de la classe de bugs d'effacement + réactivité immédiate. **Réversible.**

- **1d. Protéger le socle d'identité (AJOUTÉ 2026-08-10, vérifié).** `app_dossier_id` est **stable** (`INSERT ... ON CONFLICT(hektor_annonce_id) DO UPDATE`, `AUTOINCREMENT`, table `IF NOT EXISTS`) — mais il vit **uniquement** dans `phase2/phase2.sqlite` (1,9 Go) qui n'a **aucune sauvegarde automatique** (seul un `.bak` manuel du 18/05, 521 Mo). Perte/corruption = réattribution de tous les `id` = casse des références de 42 tables Supabase. **Voir §5bis pour la méthode économe en disque.**

### Phase 2 — Hektor devient pure DESTINATION (la migration 2×/jour)
- **But** : un seul flux sortant app → Hektor, 2×/jour ; rien n'attend Hektor sauf les 3 services.
- **2a.** Regrouper les push (`update_hektor_*`, créations, cycle de vie) dans **un worker global 2×/jour** (variante A : décaler le débounce vers le créneau ; variante B : orchestrateur `SyncCrmPort` — un login, un lot, une réconciliation).
- **2b.** Rendre **optimistes les créations + cycle de vie** (étendre le pattern `app_annonce_provisional`).
- **2c.** Garder **synchrones uniquement** : numéro de mandat, signature, diffusion.
- **Valeur seule** : c'est le **jalon à présenter aux négo** (« vos données sont ici, ça se recopie vers Hektor 2×/jour »).

### Phase 3 — Fermer le trou binaire (photos)
- **3a.** Télécharger les photos depuis Hektor → stocker **serveur local + Supabase Storage** (comme les documents).
- **3b.** Étendre la copie cloud aux biens **archivés** (aujourd'hui `local_only` → l'app web dépend du serveur local pour eux).
- **Valeur seule** : si Hektor tombe, les photos ne cassent plus.

### Phase 4 — Remplacer les 3 prises externes (chacune indépendante, derrière un flag, en parallèle de Hektor)
- **4a. Numéro de mandat** : API partenaire + registre app ; **handover de séquence** (numéro suivant, même format légal).
- **4b. Signature** : **Yousign direct** (PDF déjà générés par l'app), suivi par webhook.
- **4c. Diffusion** : agrégateur de flux (Ubiflow/Poliris) ou dépôt manuel au début.

### Phase 5 — Couper
- Arrêter la migration 2×/jour. Hektor → lecture seule → archive → off. Nouveaux ID mintés app-side (suite de séquence). **Non-événement** car l'identité était déjà app-owned.

---

## 5bis. Sauvegarde du socle d'identité — SANS saturer le disque (contrainte Frédéric)

**Constat disque (2026-08-10)** : `C:` = 806 Go libres / 894 Go (90 % libre). Pas serré aujourd'hui, MAIS une copie naïve de 1,9 Go chaque nuit = **~58 Go/mois, ~700 Go/an** → saturation en un an. Il faut donc une stratégie **étagée**, pas un `copy` quotidien.

**L'insight clé : on n'a PAS besoin de sauvegarder 1,9 Go pour protéger l'identité.**
Ce qui est irremplaçable, c'est la **table de correspondance** `app_dossier.id ↔ hektor_annonce_id` (13 214 lignes). Tout le reste de `phase2.sqlite` est **reconstructible** depuis Hektor (c'est ce que fait le pipeline chaque nuit) — mais l'`id` surrogate, lui, est **perdu à jamais** s'il disparaît.

**Stratégie recommandée (3 niveaux, coût disque négligeable) :**

| Niveau | Contenu | Fréquence | Taille | Rétention | Coût/an |
|---|---|---|---|---|---|
| **1. Mapping d'identité** (le vital) | export `id,hektor_annonce_id` (+ contacts) en CSV/JSON compressé | chaque nuit (fin de pipeline) | **~200 Ko** | 90 jours | **~20 Mo** |
| **2. Snapshot compacté** | `VACUUM INTO` + compression | hebdomadaire | ~300-500 Mo | 4 semaines | **~2 Go** |
| **3. Copie hors-machine** | niveau 1 (et/ou 2) vers cloud/NAS | hebdomadaire | idem | 3 mois | — |

**Points de méthode :**
- Utiliser **`VACUUM INTO`** (SQLite) plutôt qu'une copie brute : produit un fichier **compacté et cohérent** même base ouverte (le `.bak` de mai fait 521 Mo vs 1,9 Go aujourd'hui → beaucoup d'espace récupérable).
- **Ne jamais** faire un `copy` à chaud d'un SQLite en écriture (risque de fichier corrompu) — `VACUUM INTO` ou `.backup` gèrent ça proprement.
- **Rétention glissante obligatoire** (purge des vieux fichiers), sur le patron déjà en place pour les logs (`run_quotidien.ps1` purge > 30 jours).
- **Le niveau 1 seul suffit** à reconstruire l'identité en cas de sinistre : on rejoue le pipeline (qui rebâtit tout depuis Hektor) puis on **réinjecte les `id` d'origine** depuis le mapping. Les niveaux 2/3 ne sont que du confort/rapidité.
- **Cible long terme** : ancrer l'identité dans **Supabase** (déjà sauvegardé, cloud) plutôt que dans un fichier local — c'est l'aboutissement naturel du chantier « app source de vérité » (§6).

**Bonus constaté** : orphelins de mapping (enfants pointant un `app_dossier_id` absent de `app_dossier_current`) = 838 sur `app_rapprochement`, 11 sur `app_dossier_estimation`, 0 ailleurs (~1,4 %). Ce n'est **pas** une dérive d'identité mais un **trou de nettoyage en cascade** quand un bien quitte l'actif. À nettoyer + trancher la politique (cascade vs delete-never façon ledger d'affaires).

**⚠ Précision importante sur le périmètre d'identité (vérifié)** : seul l'**actif (13 214)** possède un surrogate `app_dossier_id`. Les **~43 649 autres** — archivés (34 444), historiques (8 802), brouillons (403) — sont identifiés **uniquement par `hektor_annonce_id`**. L'univers réel ≈ **57 K annonces**. Donc « identité déjà découplée » n'est vrai **que pour l'actif** ; la stratégie de coupure doit gérer **les deux clés** (surrogate sur l'actif + ID Hektor gelé sur les archivés — couverts par le high-water mark 62 868).

---

## 5ter. ⚠️ DÉFAUT D'IDENTITÉ CONFIRMÉ — la clé des recherches dérive du contenu (2026-08-10)

**Le défaut** — `phase2/contacts/build_contacts_layer.py:820-827` :
```python
for index, search in enumerate(recherches):          # <- index POSITIONNEL
    key_payload = {"contact_id": contact_id, "index": index, "search": search}
    search_key = stable_hash(key_payload)[:24]        # <- hash du CONTENU COMPLET
```
`contact_search_key` (clé primaire de `app_contact_search_current`) est un **hash du contenu entier** de la recherche, et `search_index` est **positionnel**. Donc :
- **modifier** une recherche ⇒ hash différent ⇒ **nouvelle clé** ⇒ tout ce qui pointait l'ancienne devient orphelin ;
- Hektor **réordonne/supprime** une recherche ⇒ les `search_index` **glissent** (or `app_search_pending` est clée sur `(hektor_contact_id, search_index)`).

**Mesure réelle en base** : **13 353 rapprochements orphelins / 46 097 (29 %)**. Décomposition : 13 164 (98,6 %) = contact sans plus aucune recherche (dette de nettoyage) ; **189 (1,4 %) = contact ayant TOUJOURS des recherches mais cette clé précise disparue → signature de l'instabilité**. 912 contacts concernés. Aussi : `app_bien_acquereur_statut` 2 orphelins / 7.

**11 tables référencent `contact_search_key`** : `app_rapprochement`, `app_rapprochement_score_history`, `app_rapprochement_search_state`, `app_proposition`, `app_relance_rapprochement`, `app_espace_message`, `app_espace_visite_request`, `app_email_envoi`, `app_notification`, `app_bien_acquereur_statut`, `app_contact_searches_current`.

**Pourquoi c'est critique pour CE chantier** : l'édition de recherche est **un des 3 flux optimistes**. Cycle observé : l'app édite (clé préservée côté Supabase) → push Hektor → **le rebuild de nuit recalcule le hash depuis le nouveau contenu → NOUVELLE clé** → propositions/relances/messages espace client rattachés à l'ancienne clé = orphelins. **Une identité ne doit jamais dériver du contenu** — c'est le principe que la Phase 0 doit poser.

**Piste de correction (à concevoir, non codée)** : clé stable indépendante du contenu — soit un identifiant de recherche natif Hektor s'il existe dans le payload (à vérifier), soit un surrogate app persistant (mapping `(contact, signature stable) → clé` conservé d'un run à l'autre, façon `ON CONFLICT DO UPDATE` des dossiers). Prévoir aussi une **table de réconciliation** ancienne clé → nouvelle pour ne pas perdre l'historique existant.

### 5ter-bis. CONTRE-AUDIT (2026-08-10) — la RAISON du défaut, et une conséquence NON anticipée

**A. La raison est légitime : l'API Hektor ne renvoie AUCUN id de recherche.**
`RAPPORT_ANALYSE_FICHES_DETAIL_CONTACT_HEKTOR_2026-05-25.md:171-193` documente la forme d'un objet recherche de `ContactById` : `offre`, `archive`, `types`, `villes`, `criteres`… **pas de champ `id`**. Le constructeur n'avait donc que `(contact_id, position)` comme prises. Le hash a été employé comme **générateur de PK**, pas comme modèle d'identité.

**B. Mais le choix était un OUBLI, pas un design.** Preuves :
- Introduit dans le commit initial `915f6cd` (2026-05-27) et **jamais retouché** (`git log -S "stable_hash(key_payload)"` → 1 seul commit).
- **Aucun document** ne donne de rationnel positif ; aucun test, aucun `COMMENT ON COLUMN`, aucun contrat écrit ; **rien ne dédoublonne** sur cette clé.
- **Décisif** : dans le MÊME fichier, ~300 lignes plus haut, `relation_key` (`build_contacts_layer.py:528-537`) **exclut délibérément** le contenu mutable, et c'est **documenté comme intentionnel** (`ARCHITECTURE_SYNC_FINALE_2026-06-19.md:47` : « Relations = clé stable (exclut état/montant/date) → maj en place, pas d'orphelin »). L'auteur maîtrisait donc le principe et l'a appliqué ailleurs. La clé recherche est l'exception.
- Déjà identifié comme défaut **3 fois** (2026-06-19 ×2, 2026-08-08) : « 🔴 FRAGILE », « le seul vrai trou = la recherche ». Correctif **planifié 4e** (`PLAN_CORRECTIFS_ET_PLANNING_2026-06-19.md:59,95`), **jamais codé**.
- **2 contournements déjà EN PRODUCTION** qui évitent la clé : migration `patch_app_email_envoi_search_index_2026-06-17.sql` (« la contact_search_key change à l'édition ») et `backend/app/services/espace_client.py:626-655` (`_load_search_for_envoi`, 3 niveaux, la PK reléguée en **dernier recours**). Le contrat de fait est donc déjà : « ne pas se fier à cette clé ».

**C. ⚠️ Un id natif EXISTE — `idCritere` — mais seulement via le scrape Console, pas l'API.**
`console_job_worker.js:10700-10702` : « seul endroit qui expose l'idCritere Hektor ». Le pipeline (API) ne le voit jamais ; le worker d'écriture (Console) oui. **C'est la cause racine de tout le design.**

**D. 🚨 CONSÉQUENCE NON ANTICIPÉE (non documentée nulle part) : l'index positionnel cible les ÉDITIONS *et les SUPPRESSIONS* dans Hektor.**
Chaîne vérifiée de bout en bout :
1. `apps/hektor-v1/src/lib/api.ts:7204` — la suppression depuis l'app envoie **`target_critere_id: null` en dur** ⇒ le chemin « idCritere explicite » n'est **jamais** emprunté.
2. `console_job_worker.js:10740-10747` — `resolveContactSearchTargetCritereId` retombe donc sur la position :
   ```js
   const index = /^\d+$/.test(rawIndex) ? Number(rawIndex) : 0;      // absent => 0
   const target = list.find((e) => e.index === index) || list[0];    // pas trouvé => 1re recherche !
   ```
3. `console_job_worker.js:11107-11111` — `handleDeleteHektorContactSearch` **n'a AUCUN garde-fou** (contrairement à l'édition, protégée par `guardContactSearchOverwrite`).
4. **Les deux espaces d'index sont indépendants** : côté API `build_contacts_layer.py:820` numérote la position dans le tableau JSON (**archivées incluses**) ; côté Console `console_job_worker.js:10736` numérote l'**ordre d'apparition des `idCritere` dans le HTML de l'onglet**. Rien ne garantit l'alignement.

⇒ **Si les ordres divergent, supprimer la recherche n°2 peut archiver la n°1 dans Hektor — silencieusement, sans garde-fou.** Idem pour une édition mal ciblée.

**E. Ampleur réelle (mesurée)** : 2 848 recherches / 2 703 contacts ; **143 contacts seulement ont ≥ 2 recherches** (`search_index > 0`) ; 0 archivée présente dans Supabase. Donc pour ~94,7 % des contacts (une seule recherche, index 0 → `list[0]`) le résultat est **juste par construction** : le bug est **masqué**. Le risque est **réel mais borné aux 143 contacts multi-recherches** — et il grandira avec l'usage.

**F. ⚠️ PIÈGE À ÉVITER dans la correction** : le correctif planifié en 2026-06 était `hash(contact_id, index)` — il **déplace** l'instabilité du contenu vers la position et **entérinerait** le défaut (D). À ne PAS reprendre tel quel.

**G. Conclusion du contre-audit** : le redesign est **sûr et déjà décidé** par le projet (aucune dépendance au caractère « contenu » de la clé), mais il doit traiter **deux défauts distincts**, pas un :
- **(1) la clé** `contact_search_key` (dérive du contenu) → clé stable + table de réconciliation ancienne→nouvelle pour les 11 tables et les 13 353 orphelins ;
- **(2) le ciblage Hektor par position** (édition/suppression) → faire remonter l'`idCritere` jusqu'à l'app (le scrape Console sait déjà le lire) et supprimer le repli `|| list[0]` + le défaut `index = 0`, au moins pour la **suppression**.
Prérequis noté : RLS désactivé sur `app_rapprochement_search_state` (à traiter avec sa policy, sinon blocage du moteur).

## 5quater. Périmètre d'identité consolidé (les 4 cas à traiter en Phase 0)

| Entité | Volume | Clé actuelle | État | Action Phase 0 |
|---|---|---|---|---|
| Dossier **actif** | 13 214 | `app_dossier_id` (surrogate local) | ✅ stable, jamais réutilisé | formaliser `hektor_annonce_id` comme simple référence ; **sauvegarder le mapping** (§5bis) |
| Dossier **archivé/historique/brouillon** | ~43 649 | `hektor_annonce_id` **seul** | ⚠️ aucun surrogate | geler l'ID Hektor (high-water mark 62 868) |
| **Contact** | 57 539 | `hektor_contact_id` (= ID Hektor) | ✅ unique, 0 null, **reproductible** (donc peu exposé à la perte de `phase2.sqlite`) | geler, ou introduire `app_contact_id` pour aligner sur les dossiers |
| **Recherche** | 2 848 | **hash de contenu + index positionnel** | ❌ **INSTABLE** (§5ter) | **refaire la clé** — prérequis avant de fiabiliser le flux optimiste recherche |

Cascades vérifiées : recherches orphelines **0**, relations orphelines **0**, `app_work_item_current` **0**, `app_dossier_detail_current` **0**. Orphelins réels : rapprochements (838 côté dossier, 13 353 côté recherche), estimations 11.

## 5quinquies. Santé de l'outbox — VÉRIFIÉ SAIN (2026-08-10) → feu vert pour la Phase 2

Vérification directe de l'état des 3 files d'attente et du taux d'échec des jobs (30 derniers jours) :

**Files `*_pending` : totalement vides.**
| File | Lignes | En conflit | Dues | Tentatives max |
|---|---|---|---|---|
| `app_annonce_pending` | **0** | 0 | 0 | — |
| `app_contact_pending` | **0** | 0 | 0 | — |
| `app_search_pending` | **0** | 0 | 0 | — |

⇒ **Aucun push bloqué, aucun conflit non résolu, aucune ré-tentative en souffrance.** Les garde-fous ajoutés en juin (retry `patch_search_pending_retry`, TTL conflit `patch_search_pending_conflict_ttl`) **fonctionnent**.

**Taux d'échec des jobs (30 j) — les flux de push sont à 0 % d'erreur :**
`update_hektor_annonce_fields` 18 ok / **0 ko** · `update_hektor_contact` 1/0 · `update_hektor_mandant_contact` 1/0 · `upload_document_to_hektor` 21/0 · `upload_hektor_photo` 6/0 · `change_hektor_annonce_status` 6/0 · `assign_hektor_annonce_negotiator` 2/0 · `generate_*` 21/0 · `refresh_console_data` 592/7 (**1 %**) · `refresh_console_contact_data` 133/1 (1 %).

> À comparer à l'historique **tout-temps** (45 erreurs sur `update_hektor_annonce_fields`) : ces échecs datent d'**avant** les correctifs de juin. Sur 30 jours glissants, **le push est fiable**.

**Les deux seuls points d'échec résiduels sont les flux BLOQUANTS de création** (petits volumes, mais ce sont ceux qui bloquent l'utilisateur) :
- `create_hektor_mandat_auto_number` : 1 ok / **1 ko** (50 % — 2 essais seulement)
- `create_hektor_draft_annonce` : 3 ok / **1 ko** (25 % — 4 essais)

**Conséquence pour le plan** : (a) la **Phase 2 (migration 2×/jour) part sur une base saine** — l'outbox n'a aucune dette à absorber, le risque est faible ; (b) ces deux créations confirment la priorité de la **Phase 4** (remplacer le numéro de mandat par l'API partenaire) et de la **Phase 1/2b** (rendre les créations optimistes pour que leur fragilité ne bloque plus le négociateur).

## 5sexies. Le trou binaire PHOTOS — mesuré (2026-08-10) : bien plus large qu'estimé

**100 % des annonces actives dépendent du CDN Hektor.**
- `app_dossier_current` : **13 214 / 13 214** dossiers ont un `images_preview_json` non vide, et les URLs pointent **toutes** vers `https://groupe-gti-immobilier.staticlbi.com/original/images/biens/…` (CDN Hektor).
- `app_console_photo` (42 lignes / 6 annonces, 100 % staticlbi) n'est qu'un **sous-ensemble marginal** : la vraie dépendance est `images_preview_json`, présent sur **toutes** les annonces.

**Correction d'estimation** : le trou photos n'est pas « quelques annonces » — c'est **l'intégralité du parc actif**, et il irrigue **tous** les canaux qui affichent une photo : app négociateur, **espace client**, **emails de rapprochement**, **vitrine Android** (`catalogue_vitrine.json` embarque ces URLs), avis de valeur.

⇒ **Si Hektor s'éteint, toutes les photos cassent partout, simultanément.** C'est la dépendance la plus large de tout le projet — devant le numéro de mandat, la signature et la diffusion (qui ne bloquent qu'un flux chacun).
⇒ **La Phase 3 (rapatriement des photos) doit être remontée en priorité** : c'est le seul verrou dont l'échec est *visible par le client final*. Volume à prévoir : ~13 200 annonces × N photos (à estimer avant de dimensionner le stockage, cf. contrainte disque §5bis).

## 5septies. Audit RLS complet (2026-08-10) — posture BONNE, un seul vrai trou

Balayage de toutes les tables `public` sans RLS **ou** sans policy :

| Table | RLS | Policies | Lignes | Verdict |
|---|---|---|---|---|
| **`app_rapprochement_search_state`** | ❌ **false** | 0 | **4 053** | 🔴 **EXPOSÉE** — lecture ET écriture via la clé publique |
| `app_dvf_vente` | ✅ true | 0 | 83 942 | 🟢 verrouillée (RLS sans policy = accès refusé sauf service_role) |
| `app_agent_prompt` | ✅ true | 0 | 3 | 🟢 verrouillée |
| `app_contact_pending` | ✅ true | 0 | 0 | 🟢 verrouillée |
| `app_rapprochement_dirty` | ✅ true | 0 | 0 | 🟢 verrouillée |

**Conclusion** : contrairement à ce que laissait craindre le rapport d'advisors, la posture est **saine**. « RLS activé + 0 policy » = **refus par défaut** (seul le `service_role` des workers passe) — c'est sûr. **Une seule table est réellement ouverte** : `app_rapprochement_search_state` (4 053 lignes).
**Remédiation (0c)** : `ENABLE ROW LEVEL SECURITY` **+** policy alignée sur ses sœurs (`app_rapprochement` en a une). ⚠ Vérifier d'abord par quel chemin le moteur y accède : s'il passe par la clé publique, activer sans policy adaptée **bloquerait le rapprochement**.

## 5octies. LISTE DES CORRECTIFS À FAIRE (consolidée — mise à jour 2026-08-17)

Rien de ce qui suit n'est codé. Liste unique de tout ce qui reste à corriger, tous constats confondus (audit initial + vérifications 2026-08-10 + revue externe 2026-08-17, cf. `NOTE_REVUE_EXTERNE_CHANTIER_INDEPENDANCE_2026-08-17.md`).

| # | Correctif | Origine | Effort | Priorité |
|---|---|---|---|---|
| **C1** | **Sortir le doc d'audit de l'exclusion git et le commiter** — `.git/info/exclude:35` contient `AUDIT_*.md` ; vérifié : ce fichier est **exclu ET non suivi**, il ne vit que sur le disque non sauvegardé (§5bis). Fix : exception `!notice/AUDIT_*.md` **ou** renommer en `NOTE_*`, puis commiter. | revue B (vérifié) | 2 min | 🔴 **la plus haute** (protège tout le reste) |
| **C2** | **Sauvegarder le mapping d'identité** — export nocturne `id ↔ hektor_annonce_id` (~200 Ko), + `VACUUM INTO` hebdo, rétention glissante. Ne PAS copier 1,9 Go/nuit (700 Go/an). | §5bis | petit | 🔴 haute |
| **C3** | **Clé des recherches (0d-1)** — remplacer `contact_search_key = hash(contenu)` par une clé stable adossée à l'`idCritere` natif (lisible par le worker, `console_job_worker.js:10700`). **Obligatoire** : table de réconciliation ancienne→nouvelle (11 tables, 13 353 orphelins). ⚠ NE PAS reprendre `hash(contact_id, index)` (déplace l'instabilité vers la position). | §5ter | moyen | 🔴 haute |
| **C4** | **Ciblage Hektor par position (0d-2)** — remonter l'`idCritere` jusqu'à l'app (`api.ts:7204` envoie `target_critere_id: null` en dur), supprimer le repli `\|\| list[0]` et le défaut `index = 0`, **au minimum pour la suppression** (`handleDeleteHektorContactSearch`, sans garde-fou). **Risque de perte de donnée client** (borné à 143 contacts multi-recherches). | §5ter-bis D | petit | 🔴 haute (faire avant C3) |
| **C5** | **Fenêtre delete+réinsert** — `delete_searches_except_dirty` supprime puis réinsère **toutes** les recherches et relations d'un contact à chaque passage (`push_contacts_to_supabase.py:680-691`, vérifié). *Précision* : une clé déterministe (C3) survit au cycle et suffit pour les orphelins ; reste le problème **distinct** de fenêtre de disponibilité (motif déjà connu côté read-through). | revue D (vérifié) + précision | moyen | 🟠 moyenne |
| **C6** | **Contrat d'autorité + migration ① → ②** — le dirty-skip recouvre **deux** mécanismes : ① temporaire par ligne (`fetch_dirty_*`, relâchée après le trajet ; la l. 446-449 dit explicitement « Hektor gagne ») et ② permanente par champ (`fetch_app_owned_contact_fields`, seulement naissance/lieu/matrimonial). **1b = faire passer les champs du contrat d'autorité de ① à ②**, et retirer la l. 446-449. | revue C | moyen | 🔴 haute |
| **C7** | **Rétrograder le read-through (pas l'arrêter)** — il doit continuer à **remplir**, jamais à **écraser** ce que l'app possède. Le calque (overlay / `base_snapshot` / `conflict`) tombe **après**, en nettoyage, pas en préalable. **Ordre sûr** : rétrograder → simplifier le calque (réactivité) → basculer les négociateurs → allumer le lot 2×/jour. | revue G | — | 🔴 correction d'ordre |
| ~~C8~~ | ~~Prix / statut / photos hors du lot 2×/jour~~ — **ÉCARTÉ (décision Frédéric, 2026-08-17)**. La revue externe (point E) signalait qu'un lot 2×/jour retarderait jusqu'à 12 h l'arrivée d'une baisse de prix sur les portails. **Jugé non nécessaire** : le délai est accepté, tous les champs partent dans le lot. *Conservé ici pour tracer la décision — ne pas re-proposer.* | revue E | — | ⚪ écarté |
| **C9** | **Rapatrier les photos** — **13 214/13 214 annonces (100 %)** pointent sur le CDN Hektor `staticlbi`. Aucun binaire rapatrié (contrairement aux documents). Impacte app, espace client, emails, vitrine Android. Estimer d'abord le volume (nb + poids) pour dimensionner, cf. contrainte disque. | §5sexies | **gros** | 🔴 prérequis de coupure |
| **C10** | **RLS `app_rapprochement_search_state`** — seule table réellement exposée (RLS off, 0 policy, 4 053 lignes). Activer + policy alignée sur `app_rapprochement`. ⚠ vérifier le chemin d'accès du moteur avant, sinon blocage. | §5septies | petit | 🟠 moyenne |
| **C11** | **Nettoyer les orphelins** — 838 rapprochements (côté dossier), 13 353 (côté recherche), 11 estimations, 2 statuts acquéreur. Trancher la politique : cascade vs delete-never (façon ledger d'affaires). | §5quater | moyen | 🟠 moyenne |
| **C12** | **Seuils de monitoring adaptés au rythme 2×/jour** — un worker passant à 2 exécutions/jour déclenchera les alertes de fraîcheur calibrées sur du continu. À traiter **en même temps** que l'allumage du lot, pas après. | revue J | petit | 🟠 (avec la Phase 2) |
| **C13** | **Asymétrie résiduelle `annonceContact`** — le chemin listing possède un effet de reset (`App.tsx:12356-12359`, garde-fou « recherche fantôme ») que le chemin annonce n'a pas. Exposition faible (la fermeture repasse par id vide), non confirmée atteignable dans l'UI. Reliquat du correctif `310ee99`. | revue A (vérifié) | 2 min | 🟢 basse |
| **C14** | **Étapes non critiques du pipeline non bloquantes** — appliquer à `backfill appointment public links` et `android vitrine export` le patron déjà posé sur Matterport (`d4bff42`) : retry + heartbeat d'erreur, sans tuer le run. | incident 2026-08-09 | petit | 🟢 basse |

**Ordre d'attaque suggéré** : C1 → C2 → C4 → C3 → C6 → C7 (ordre général) → C9 → C10/C11/C12 → C13/C14. *(C8 écarté.)*

## 6. La décision d'architecture à trancher (avant Phase 3)
**Serveur local = maître permanent (on-premise + cloud en cache), OU tout basculer dans le cloud (Supabase Storage = maître) ?**
- Local permanent : moins de migration, mais l'app web dépend du serveur pour les binaires archivés (réactivité/disponibilité liées à une machine chez toi).
- Tout-cloud : app 100% autonome et réactive partout, mais migration des binaires + coût stockage.
Cette décision oriente les Phases 3 et 5.

---

## 7. Prérequis / risques à sécuriser en premier
1. ~~**Stabilité de `app_dossier_id`**~~ → **VÉRIFIÉ OK le 2026-08-10.** L'`id` est **stable et jamais réutilisé** (`AUTOINCREMENT` + `ON CONFLICT(hektor_annonce_id) DO UPDATE` + `CREATE TABLE IF NOT EXISTS`). Le max à 4,5 M pour 13 k lignes n'était PAS une réassignation mais l'empreinte normale d'un compteur ayant traversé tout l'historique (biens archivés/supprimés ayant consommé un id). **Risque requalifié** → le vrai danger n'est pas la clé mais **son unique lieu de vie** : `phase2.sqlite` **sans sauvegarde** (voir §5bis).
2. **Photos** = seule dépendance binaire dure (Phase 3).
3. **Règle comportementale négo** : une seule porte d'écriture = l'app. « On ne travaille plus dans Hektor. »
4. **RLS** `app_rapprochement_search_state`.

## 8. Ce qui rend cette méthode « la meilleure »
- **Aucun big-bang** : 5 phases, chacune livrable et réversible seule.
- **Valeur dès la Phase 1** (réactivité + fin des bugs de sync), avant même de toucher aux 3 services.
- **Les 3 prises se remplacent en parallèle**, sans bloquer le reste, chacune derrière un interrupteur.
- **La coupure est un non-événement** parce que l'identité et les masters de données/documents sont **déjà** chez toi. Il ne reste, côté binaire, que les **photos** à rapatrier.
