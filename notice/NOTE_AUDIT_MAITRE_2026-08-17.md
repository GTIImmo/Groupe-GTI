# Audit maître — état réel du système GTI (2026-08-17)

**6 explorations parallèles au niveau DONNÉE (pas seulement structure), croisées avec la base live et le code.**
**Remplace les affirmations antérieures en cas de contradiction. Aucun code écrit.**

> **Pourquoi cet audit** : les audits précédents cartographiaient les *mécanismes* sans inventorier les *contenus*. Cette lacune a produit une recommandation fausse (geler le blob annonce) qui aurait figé la diffusion, les affaires, les mandats et les photos. Ici, chaque affirmation est adossée à une lecture de contenu.

---

## 0. Corrections de mes affirmations antérieures

| J'avais dit | Réalité vérifiée |
|---|---|
| « le blob `detail_payload_json` est descriptif » | **FAUX.** Sur 130 clés : ~55 sont de l'**état vivant Hektor**, ~48 descriptives éditables, ~27 brutes/dérivées. |
| « 2 tâches pg_cron » | **8** tâches actives. |
| « `app_contact_override` = source de vérité app » | **Table vide (0 ligne).** Les écritures vont dans `app_contact_current`. |
| « phase2.sqlite = 1,9 Go, le gros fichier local » | `phase2.sqlite` = 1,97 Go **mais `hektor.sqlite` = 3,89 Go**. Total ≈ 5,9 Go. |
| « mapping d'identité ≈ 13 k lignes (~200 Ko) » | `app_dossier` = **56 867 lignes** (couvre aussi les archivées). |
| « les photos = 42 lignes dans `app_console_photo` » | La vraie dépendance : **13 214/13 214 annonces** pointent le CDN Hektor via `images_preview_json`. |
| « le front rend 2 arbres à maintenir » | **Un seul point de bascule** (`App.tsx:17773`). Zone à risque = ce qui est déclaré **hors `appModals`**. |

---

## 1. Le blob annonce — l'inventaire qui manquait

`app_dossier_detail_current.detail_payload_json` (**TEXT**, pas jsonb) — 130 clés, liste faisant autorité : `export_app_payload.py:380-515`.

| Bucket | Nb | Exemples | Règle |
|---|---|---|---|
| **B — État vivant Hektor** | **~55** | diffusion (3), offres (9), compromis (10), ventes (9), mandats (13), notes (3), statut, valide, + 14 clés de scrape Console | **Doit continuer à se rafraîchir** |
| **A — Descriptif éditable app** | **~48** | dont **9 blobs de groupe** portant ~150 champs wizard (`ag_interieur_json`, `ag_exterieur_json`, `terrain_json`, `equipements_json`, `diagnostiques_json`, `copropriete_json`, `mandat_infofi_json`, `mandat_mandatdispo_json`, `organiser_visite_json`) | Peut devenir app-owned |
| **C — Brut / dérivé / système** | ~27 | `detail_raw_json`, `annonce_list_raw_json` (ré-embarquent tout l'état vivant), price_change (7), surcouche locale (7) | Système |

### Bugs découverts dans le blob
1. **`prix_publique` / `prix_net_vendeur` viennent du COMPROMIS**, pas de l'annonce (`view_generale.py:331-332`), mais le front les lit comme prix d'annonce (`App.tsx:2531-2532`) → **NULL sans compromis, valeur fausse avec**. Le vrai prix vit dans `mandat_infofi`.
2. **`Particularites`** : champ wizard existant, mais absent de tous les groupes de push worker → **saisie silencieusement jetée**.
3. **Photos tronquées à 5** (`MAX_EXPORTED_IMAGES`) alors que `nb_images` compte le total → la fiche annonce plus de photos qu'elle n'en montre.
4. **`motif_blocage`, `is_blocked`, `is_followup_needed`** : toujours vides (`app_blocker`/`app_followup` = 0 ligne). Poids mort dans chaque payload.
5. **`console_missing_fields_json` duplique** 6 clés déjà présentes séparément → double transport.
6. **`app_optimistic_overlay` non déclaré** dans `DETAIL_PAYLOAD_FIELDS` → toute reconstruction l'efface par construction.
7. **Scrape Console fusionné seulement si `status=='done'`** → un scrape échoué laisse des NULL silencieux.

---

## 2. La surface d'écriture de l'app

- **173 clés Hektor distinctes** éditables (wizard, 14 groupes) + un jeu camelCase parallèle à la création.
- **Deux espaces de noms** écrivent dans la **même** RPC `app_edit_annonce_optimistic`, qui **ne valide ni l'un ni l'autre** — tout ce qui est passé est transmis. Source de bugs silencieux.
- **Non poussables en inline** : `diffusable` (option unique « Non » — interrupteur à sens unique), `latitude`, `longitude` (recalculés par géocodage).
- **`levelCount`** déclaré mais jamais mappé sur le chemin job → silencieusement perdu.
- **8 clés wizard orphelines** (dans aucune liste de profil).
- **Contact** : 12 colonnes plates (aucun blob) — le contrat contact est donc **solide et indépendant** du problème du blob.

---

## 3. Modèle Supabase

85 tables, 22 vues, 79 fonctions `app_*`, 2 triggers, **8 pg_cron**, ≈1,6 Go.

**Aucune contrainte FK sur les clés métier** (`app_dossier_id`, `hektor_annonce_id`, `hektor_contact_id`, `contact_search_key`) → orphelins accumulés :

| Relation | Orphelins | Note |
|---|---|---|
| `app_contact_relation_current` → dossier | **75 576 (98 %)** | plus gros trou de traçabilité |
| `score_history` → dossier / recherche | 177 841 / 112 926 | **jamais purgé** (98 % > 30 j) |
| `app_rapprochement` → recherche | 13 353 (29 %) | famille connue (clé instable) |
| `app_console_document` → dossier | **60 / 202 (30 %)** | documents peut-être inaccessibles depuis l'UI |
| `app_appointment_public_link` → dossier | 558 / 2 140 (26 %) | liens QR vers biens disparus |
| `app_dossier_estimation` → dossier | 11 / 30 (37 %) | |

**Autres** : aucun job de purge nulle part ; 6 tables legacy vides encore lues en UNION par 4 vues ; `detail_payload_json` + 5 colonnes du registre sont **TEXT** (tout `->>` échoue) ; `app_contact_consent` vide malgré 82 envois ; `app_rapprochement.eligible = true` à 100 % (ne discrimine rien).

---

## 4. Le front (produit)

**9 écrans**, dont **`annonces` inaccessible** (réécrit vers `mandats` au routage) → `StockScreen`, `AnnonceScreen`, `MobileDossierCards` + ~15 branches = **morts par routage**.

**Bugs / manques**
- **Modale admin « Utilisateurs » non rendue sur mobile** alors que l'action est câblée → charge la liste, n'affiche rien.
- **Cloche de notifications absente sur mobile**.
- **Tablettes (768–1180 px) reçoivent la version mobile** → pas de cockpit, ni carte secteur, ni cadastre.

**Dette** : ~1 000 lignes de composants jamais référencés ; ~600 lignes de **Mandat V3** dont le drapeau n'existe dans **aucun** fichier d'environnement ; `espace_portal.py` (645 l.) fini mais non branché ; **`ContactDetailPopupV2` duplique ~25 hooks verbatim** de la V1 → *c'est la cause structurelle du bug corrigé en `310ee99`*.

**Drapeaux** lus **à la compilation** → bascule Vercel = redéploiement.

---

## 5. La couche locale — ce qui n'existe QUE sur le disque

| Donnée | Volume | Ré-obtenable ? | Conséquence de la perte |
|---|---|---|---|
| **`app_dossier`** (mapping d'identité) | 56 867 lignes | Seulement en ré-émettant des ID AUTOINCREMENT | **Toutes les lignes Supabase clées sur `app_dossier_id` deviennent orphelines.** Impact n°1. |
| **Caches de scrape** (`hektor_contact_missing_detail` 43 995, `hektor_annonce_chauffage_detail` 56 792, `_console_detail` 154, `_draft_state` 435) | ~100 k lignes | Oui, mais **re-scrape Playwright de plusieurs jours** | Les valeurs sont dans Supabase ; le cache « déjà fait » ne l'est pas. |
| **`hektor_price_change_event`** | 162 (depuis 05/06) | **Non** — dérivé de diffs non rejouables | Historique de prix perdu définitivement. |
| **`sync_meta`** (curseurs delta) | **4 lignes** | Non | Le delta repart de zéro → re-pull complet de l'API. |
| **`raw_api_response`** | 464 854 / 1,51 Go | Re-pull complet | Source de rejeu de toute normalisation. |
| **`app_internal_status`** | 22 213 | Partiellement | Statut interne / next_action / auteur perdus. |
| **`app_diffusion_*`** (config) | 85 | À la main | Routage et politique de diffusion perdus. |
| **Documents `local_only`** | 58 Mo / 41 fichiers | **Non** pour les PDF générés (ImmoSign signés, estimations) | Copie cloud **uniquement** si statut actif/offre/compromis/estimation. |

⚠️ **Les deux SQLite sont en mode WAL** → une copie de fichier brute pendant un run est **incohérente**. Toute sauvegarde doit utiliser `VACUUM INTO` ou l'API backup.

### Deux comportements destructifs à connaître
1. **`prune_annonce_scope`** : toute annonce absente du listing courant est **supprimée de 9 tables** — y compris `hektor_price_change_event` (données locales non rejouables).
2. **Upsert contact** : `archive`, `date_maj`, `raw_json` et les 2 clés étrangères sont **écrasés inconditionnellement, y compris par NULL** → un rafraîchissement listing-only peut vider `hektor_negociateur_id` et **dégrader `raw_json`** d'un payload détaillé vers un payload listing.

---

## 6. Sécurité (constats principaux)

**Vérifiés par moi**
- **Énumération publique** : `/public/appointments/annonce/{ref}` accepte un **numéro d'annonce brut** et crée le lien à la volée → moisson non authentifiée de prix + **nom, email, fixe et portable personnel du négociateur** (`appointment_service.py:192-206`).
- **La vitrine publie déjà ces données** : `catalogue_vitrine.json` public sur GitHub Pages avec `numero_dossier`, `numero_mandat` et **portable personnel**.
- **Secrets mal placés** : `SUPABASE_SERVICE_ROLE_KEY` + `SMTP_PASS` dans `apps/hektor-v1/.env` (pas de fuite au build, mais mauvais emplacement).
- **Repli HMAC → clé service_role** si `EMAIL_TRACKING_SECRET` absente (4 endroits) — **la variable est définie**, donc latent.

**Rapportés, non revérifiés** : jetons RDV sans expiration et sans revérification d'état ; aucune limitation de débit sur les écritures publiques ; jeton « espace contact » 60 j non révocable ; email négociateur transféré → création d'événement agenda ; **PAT GitHub en clair** ; `Console/.env.txt` = **copie obsolète en clair des identifiants Hektor** (à supprimer) ; `HEKTOR_TOTP_SECRET` = secret le plus sensible de la machine.

**Bien fait** : RLS active sans policy anonyme partout où les routes publiques touchent ; jetons HMAC en comparaison à temps constant ; IP hashées ; envoi réel d'emails coupé par défaut ; PDF servis en URL signée 900 s ; build front vérifié sans secret.

---

## 7. Ce que l'audit change pour le chantier

1. **Le contrat d'autorité doit être écrit clé par clé**, pas « le blob ». La matière existe désormais (buckets A/B/C).
2. **Le contrat CONTACT est prêt** — 12 colonnes plates, aucun blob, aucune dépendance au problème découvert.
3. **Le contrat RECHERCHE reste bloqué** par C4 puis C3.
4. **La sauvegarde (C2) doit couvrir bien plus que le mapping** : caches de scrape, price events, curseurs `sync_meta`, statut interne, config diffusion, documents `local_only` — et utiliser `VACUUM INTO` (mode WAL).
5. **Nouveaux correctifs à ajouter** : le bug `prix_publique`/`prix_net_vendeur`, `Particularites` jeté, la modale admin mobile, la cloche mobile, les tablettes en version mobile, la purge des historiques, `.env.txt` à supprimer.
