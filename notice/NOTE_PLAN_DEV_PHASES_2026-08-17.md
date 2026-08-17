# Plan de développement — phases corrigées après l'audit maître

**2026-08-17. Fondé sur `NOTE_AUDIT_MAITRE_2026-08-17.md` (6 explorations au niveau donnée).**
**Remplace le découpage antérieur. Aucun code écrit.**

## Principe directeur
> L'app devient la source de vérité, réactive, puis autonome — **sans jamais casser les workers avant la coupure finale** (invariant Frédéric).

## Ce qui a changé par rapport au plan précédent
1. Une **Phase 0 de sécurisation** apparaît **avant** tout travail de découplage : l'audit a montré que des données irremplaçables n'ont aucune sauvegarde, et que des données personnelles sont exposées publiquement. Ces risques existent **indépendamment** du chantier et le précèdent.
2. Le contrat d'autorité se décompose : **contacts prêts**, **annonce clé par clé** (matière disponible), **recherches bloquées**.
3. Un **chantier parallèle « dette & bugs »** regroupe ce qui est indépendant et peut avancer à tout moment.

---

# PHASE 0 — Sécuriser l'existant *(préalable, sans lien avec Hektor)*

**Pourquoi d'abord** : perdre le disque = perdre l'identité de tout le système. Et des données personnelles sont publiques aujourd'hui.

### 0.1 — Sauvegarde de l'irremplaçable 🔴
Couvrir **plus que le mapping** (mon estimation précédente était insuffisante) :

| À sauvegarder | Volume | Pourquoi |
|---|---|---|
| `app_dossier` (mapping identité) | 56 867 lignes | sa perte orpheline **toute** la base Supabase |
| Caches de scrape (contact_missing, chauffage, console, drafts) | ~100 k lignes | sinon re-scrape Playwright de plusieurs jours |
| `hektor_price_change_event` | 162 | **non ré-dérivable** |
| `sync_meta` (curseurs) | 4 lignes | sinon re-pull complet de l'API |
| `app_internal_status`, `app_diffusion_*` | ~22 300 | saisies et config non rejouables |
| Documents `local_only` | 58 Mo | PDF signés/estimations **sans source amont** |

**Méthode** : `VACUUM INTO` obligatoire (**mode WAL** → une copie brute pendant un run est incohérente) ; export léger quotidien des tables critiques ; snapshot compressé hebdomadaire ; rétention glissante. Ordre de grandeur : quelques Mo/nuit, ~2 Go/an — pas 700 Go.

### 0.2 — Fermer les expositions de données personnelles 🔴
- Retirer le **portable personnel des négociateurs** de `catalogue_vitrine.json` (fichier public, indexable, historisé).
- Fermer l'**énumération** par identifiant numérique sur l'endpoint RDV public.
- Ajouter **expiration + revérification d'état** sur les liens publics.
- Limiter le débit sur les écritures publiques (anti-spam/inondation).
- Déplacer `SUPABASE_SERVICE_ROLE_KEY`/`SMTP_PASS` hors du dossier front ; supprimer `Console/.env.txt` (copie en clair des identifiants) ; sortir le PAT GitHub du disque.
- RLS + policy sur `app_rapprochement_search_state` (seule table ouverte).

### 0.3 — Versionner la documentation ✅ **FAIT** (`e161020`)

---

# PHASE 1 — L'app devient autoritaire *(le cœur)*

**But** : ce que le négociateur écrit est **définitif** ; plus rien ne l'écrase ; rien ne l'attend.
**Mécanisme** : soustraction — retirer un champ du payload de nuit suffit (UPSERT merge). Patron déjà éprouvé sur 3 champs contact.

### 1.1 — Contacts *(PRÊT, aucun blocage)*
12 colonnes plates, **aucun blob**. Faire passer les 9 champs restants de la protection temporaire ① à la protection permanente ②. Retirer le « Hektor gagne » explicite.

### 1.2 — Annonce, clé par clé *(matière disponible)*
Appliquer le contrat aux **~48 clés du bucket A** + aux colonnes de `app_dossier_current` déjà validées.
⛔ **Ne jamais toucher aux ~55 clés du bucket B** (diffusion, offres, compromis, ventes, mandats, notes, statut) : elles doivent continuer à se rafraîchir.

### 1.3 — Rétrograder le read-through
Il garde le droit de **remplir**, perd celui d'**écraser** ce que l'app possède. Même liste blanche que 1.1/1.2.

### 1.4 — Simplifier le calque *(en DERNIER)*
Retirer **uniquement** l'overlay d'affichage et la lecture « overlay d'abord » du front.
⛔ **`base_snapshot`, `search_index`, `hektor_*_id`, `idUser` restent** — les workers les lisent (invariant).

### 1.5 — Garde-fou : non bloquant, pas supprimé
Pour les champs app : pousser **et notifier** au lieu de renoncer. Il reste utile tant que des négociateurs travaillent dans Hektor.

---

# PHASE 2 — Réparer l'identité des recherches *(piste parallèle)*

Dans cet ordre, il est important :
- **2.1** — Ciblage par `idCritere` au lieu de la position *(risque de supprimer la mauvaise recherche client)*. Petit, localisé, et **pose la tuyauterie** dont 2.2 a besoin.
- **2.2** — Clé stable + **table de réconciliation** ancienne→nouvelle (11 tables, 13 353 orphelins). Ne rien supprimer : irréversible.
- **2.3** — Alors seulement, le volet **recherches** du contrat devient applicable.

---

# PHASE 3 — Migration globale 2×/jour

Variante A (décaler l'outbox existant vers 2 créneaux) puis B (orchestrateur dédié).
**Contraintes issues de l'audit** : grouper **par négociateur** (l'impersonation coûte un login par négo) et respecter l'**ordre de dépendance** (création → champs → liaison → document → signature).
Restent **immédiats hors lot** : numéro de mandat, signature, diffusion.
À traiter **en même temps** : les seuils de monitoring (sinon fausses alertes).

---

# PHASE 4 — Rapatrier les photos

**100 % des 13 214 annonces actives** dépendent du CDN Hektor. Impacte app, espace client, emails, vitrine.
Décision actée : **statu quo** (serveur maître, cloud sélectif) → conséquence assumée : les photos des ~34 400 archivées seront en local seul.
Étape préalable : mesurer le volume réel (nombre + poids) avant de dimensionner.

---

# PHASE 5 — Remplacer les 3 services externes
Chacun indépendant, derrière un interrupteur, testé **en parallèle** de Hektor :
numéro de mandat (API partenaire, **continuité de séquence**) · signature (Yousign) · diffusion (agrégateur).

---

# PHASE 6 — Couper
Éteindre la migration. Hektor → lecture seule → archive → off.
L'affectation négociateur bascule côté app **à ce moment-là** (elle pilote l'impersonation jusque-là).
**Non-événement** : identité, données et documents sont déjà chez toi ; les photos l'auront été en Phase 4.

---

# CHANTIER PARALLÈLE — dette & bugs *(indépendant, à tout moment)*

| Sujet | Détail |
|---|---|
| **Bug prix** | `prix_publique`/`prix_net_vendeur` viennent du **compromis** mais sont affichés comme prix d'annonce → NULL ou faux |
| **Saisie perdue** | `Particularites` jeté silencieusement par le worker |
| **Mobile** | modale admin non rendue (action câblée), cloche de notifications absente, **tablettes en version mobile** |
| **Photos** | tronquées à 5 alors que le compteur affiche le total |
| **Purges** | aucune : `score_history` (98 % > 30 j), `job_log`, `monitor_event` |
| **Orphelins** | 75 576 relations contact↔annonce, 60/202 documents, 558 liens QR… + politique à trancher (cascade vs delete-never) |
| **Code mort** | ~1 000 lignes non référencées, écran `annonces` inaccessible, Mandat V3 sans drapeau déclaré |
| **Duplication V1/V2** | `ContactDetailPopupV2` duplique ~25 hooks → **cause structurelle** du bug corrigé en `310ee99` |
| **Payload** | `console_missing_fields_json` duplique 6 clés ; 3 clés toujours vides |
| **Legacy** | 6 tables vides encore lues en UNION par 4 vues |

---

## Ordre recommandé
**0.1 → 0.2** (sécuriser) → **1.1** (contacts, prêt) → **2.1** (risque de perte) → **1.2/1.3** (annonce + read-through) → **1.4/1.5** → **2.2** → **3** → **4** → **5** → **6**.
Le chantier parallèle s'insère entre deux phases selon la disponibilité.

## Règle permanente
Avant de retirer quoi que ce soit : **« un worker s'en sert-il pour viser Hektor ? »** Si oui, on garde jusqu'à la coupure.
