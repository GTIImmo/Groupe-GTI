# NOTE — Moteur de rapprochement acquéreur ↔ biens (écran « Recherche Acquéreur »)

**Date :** 2026-06-14
**Auteur :** développement assisté (Claude) + Frédéric Gerphagnon
**Statut :** livré et déployé en production (Vercel `groupe-gti`, `origin/main` @ `cd1aac2`)
**Périmètre :** app `apps/hektor-v1` (React 19 / Vite / TS) + Supabase `dwaqxfrinihnychuoptk` + intégration Gmail (backend FastAPI `backend/`)

---

## 1. Objectif

Construire un **moteur de rapprochement immobilier professionnel** (niveau Hektor natif / Apimo / Perizia) — pas un calcul jetable côté front — avec :

1. **Rapprochements persistés** en base (scores sauvegardés, pas recalculés à chaque ouverture).
2. **Recalcul automatique sur événement** (nouveau bien en stock, critères acquéreur modifiés, baisse de prix).
3. **Score vivant** : une baisse de prix fait remonter le bien ; le score évolue avec la donnée.
4. **Traçabilité complète** : chaque proposition tracée (bien, acquéreur, date, canal, négociateur) ; statut par couple bien/recherche ; relances rattachées.
5. **Statistiques / reporting** : taux de proposition par négociateur, délai rapprochement→proposition, biens les plus écartés, recherches dormantes, santé des critères.

Le rapprochement existait déjà **dans Hektor** (`iris-refreshRapprochementByCommune`) mais n'était pas exploité par l'app ; ce moteur est **natif app**, indépendant, et **app-only** (aucune écriture retour vers Hektor pour les propositions/statuts).

---

## 2. Décisions d'architecture (et pourquoi)

| Décision | Choix retenu | Raison |
|---|---|---|
| Où vit le score | **Fonction SQL Supabase + persistance** (`app_match_score`) | Objectif « persisté / score vivant » = par nature serveur. Le front ne calcule rien, il lit la table déjà calculée → ouverture instantanée. |
| Recalcul auto | **File `dirty` + `pg_cron`** (option ① sur 3) | Le pipeline quotidien pousse ~13 000 lignes ; un trigger qui recalcule en synchrone saturerait la base. Les triggers se contentent d'**empiler** l'id modifié (coût quasi nul) ; un cron draine la file par lots. Anti-storm. |
| Champs physiques du bien | Lus depuis `app_dossier_detail_current.detail_payload_json` (jsonb) | Surface/pièces/chambres/géoloc ne sont **pas** en colonnes de l'index principal mais présents en clés de 1er niveau du blob détail → exploitables en SQL sans migration du pipeline. |
| Traçabilité | Tables dédiées **app-only** (`app_proposition`, `app_bien_acquereur_statut`, `app_relance_rapprochement`) | Pas de retour Hektor (décision métier). Écriture via RPC `SECURITY DEFINER`, lecture RLS `authenticated`. |
| Envoi email | **Réutilise** `sendGoogleWorkspaceCrmEmail` (backend FastAPI existant) | Ne pas recréer l'intégration Gmail ; même mécanisme que le composer de la fiche contact. |

---

## 3. Filtre du stock vendable

Le « stock rapprochable » est restreint dès la source :

```
statut_annonce = 'Actif'  AND  diffusable = '1'
```

Mesures (2026-06) : sur 13 416 dossiers, seuls **~381** sont Actif+diffusable (le reste : ~12 467 Estimations, ~403 Actif non-diffusables, ~165 sous offre/compromis). Complétude des champs sur ces 381 : prix/CP/ville/type/photo ≈ 100 %, surface 97,6 %, pièces 78 %, chambres 73 %, **géoloc 100 %**, ~10,9 photos/bien en moyenne (max 57).

Côté recherches : **3 772 actives**. Complétude critères : type 99 %, prix_max 95 %, secteur 82 %, surface_min 71 %, chambres 62 %, pièces 42 %, prix_min 10 %.

---

## 4. Modèle de données (Supabase, 5 migrations)

### Tables
- **`app_rapprochement`** — cœur : `(contact_search_key, hektor_contact_id, app_dossier_id, score, score_components jsonb, eligible, first_seen_at, computed_at)`, UNIQUE(search, dossier), index `(search, score DESC)`.
- **`app_rapprochement_score_history`** — historique append-only des scores (`reason` : `init`/`new_bien`/`maj_bien`/`change`), écrit seulement si nouveau ou changé.
- **`app_bien_acquereur_statut`** — statut courant du couple : `jamais_vu | propose | visite | ecarte | offre` (PK search+dossier).
- **`app_proposition`** — journal des envois (canal, status_after, note, négociateur, date).
- **`app_relance_rapprochement`** — relances (`due_date`, `status` a_faire/fait/reporte), relance auto J+5 à chaque proposition.
- **`app_rapprochement_dirty`** — file de recalcul coalescée (UNIQUE entity_type+entity_id, `reason` new/changed).
- **`app_notification`** — alertes négociateur (index unique partiel : ≤ 1 alerte non lue par négo/bien/type).

### Vues
- **`app_dossier_match_attrs`** — projection JSON → colonnes (surface, nb_pieces, nb_chambres, surface_terrain, lat, lng, date_maj). Lecture/reporting.
- **`app_stat_negociateur_v`** — métriques agrégées par négociateur.

### Fonctions
- **`app_num(text)`** — parse numérique tolérant (NULL si invalide).
- **`app_match_score(p_search jsonb, p_dossier jsonb) → jsonb`** — scoring PUR (IMMUTABLE), `{score, eligible, components}`.
- **`app_refresh_rapprochements_for_search(key)`** — recalcule tout le stock pour une recherche (upsert + historique + purge des inéligibles), via temp table.
- **`app_upsert_one_rapprochement(search, dossier)`** — score d'UN couple (utilisé par le recalcul événementiel).
- **`app_get_rapprochements(key, max_age=1440)`** — API de lecture : **refresh paresseux** si > 24 h ou absent, puis renvoie le feed scoré + display (titre, prix, ville, photo_url, surface, pièces…).
- **`app_process_rapprochement_dirty(limit=200)`** — draine la file : `search` → refresh complet ; `dossier/new` → scan des recherches candidates (type+budget, hors recherches sans type NI secteur) + alerte si ≥ 80 % ; `dossier/changed` → maj des recherches déjà liées (score vivant).
- **`app_record_proposition`, `app_set_bien_statut`, `app_get_search_statuts`, `app_list_relances`, `app_relance_set_status`** — traçabilité.
- **`app_get_search_timeline(key)`** — historique réel (propositions + relances + nouveaux biens).
- **`app_get_dossier_photos(dossier_id) → text[]`** — galerie ordonnée depuis `images_json` (visibles uniquement).
- **`app_get_rapprochement_stats()`, `app_mark_notification_read(id)`**.

### Triggers + cron
- `trg_dossier_dirty` (AFTER INSERT/UPDATE OF prix, statut_annonce, diffusable, type_bien sur `app_dossier_current`) → `app_enqueue_dirty('dossier', id, new|changed)`.
- `trg_search_dirty` (AFTER INSERT/UPDATE sur `app_contact_search_current`, gardé sur changement réel de critères) → `app_enqueue_dirty('search', key)`.
- **`pg_cron`** : job `rapprochement-dirty` toutes les **2 minutes** → `app_process_rapprochement_dirty(200)`.

---

## 5. Algorithme de scoring (`app_match_score`)

Score 0–100, **pondération renormalisée sur les seuls critères disponibles** (un champ absent des deux côtés est exclu du numérateur ET du dénominateur → jamais de pénalité injuste, jamais de valeur inventée).

| Critère | Poids | Logique |
|---|---|---|
| **Type de bien** | gate | `dossier.type_bien` doit figurer dans les clés de `types_json` (codes numériques alignés). Sinon → exclu. |
| **Prix** | 35 | Dans `[prix_min..prix_max]` → 100 %. Au-delà de prix_max mais ≤ marge (`ITEM_PRIX_MARGE` ou 10 % par défaut) → décroissance linéaire. Au-delà de la marge → **exclu**. Sous prix_min → 70 %. |
| **Secteur** | 25 | Code postal du bien ∈ CP extraits de `villes_json` → 100 %. Hors secteur → 0 (mais pas exclu : « secteur mou »). `villes_json` vide → critère neutre. |
| **Surface** | 20 | ≥ surface_min → 100 % ; entre 80 % et 100 % du min → décroissance ; < 80 % → hors critère. |
| **Pièces** | 10 | ≥ pieces_min → 100 % ; sinon proportionnel. |
| **Chambres** | 10 | ≥ chambre_min → 100 % ; sinon proportionnel. |

**Score final** = `round(Σ contributions / Σ poids applicables × 100)`. `score_components` (jsonb) renvoie chaque critère `{k, ok, v}` → alimente directement le tooltip « Pourquoi X % ? ».

**Éligibilité** = Actif + diffusable + type OK + prix dans la marge.

**Classes d'affichage** (front) : ≥ 85 vert, ≥ 70 or, sinon rouge.

**Seuil d'alerte négociateur** : **≥ 80 %** (nouveau bien matchant → notification).

---

## 6. L'écran « Recherche Acquéreur » (front)

- Composant autonome `src/RechercheAcquereur.tsx` + `src/recherche-acquereur.css` (tout scopé sous `.rech-acq` ; charte beige #f1ece4 / magenta #c2125f / Spectral + Hanken Grotesk).
- **Déclencheur** : bouton « Rapprocher les biens » sur chaque recherche **active** du bloc « Recherches acquéreurs » de la fiche contact (`ContactDetailPopup`). Props : `{open, onClose, contact, search, senderEmail, acquereurEmail}`.
- **Brief** (rail gauche) : type d'offre, localités, prix, surfaces/pièces/chambres/terrain, types, équipements + DPE — tous dérivés des vraies données (`criteres_json`, etc.). Sections vides masquées.
- **Feed** : `loadRapprochements(key)` → cartes scorées triées, **vraie photo** (`photo_url_listing`), specs sans fabrication, tooltip critères, états loading/vide/erreur, cap 60.
- **Actions** : proposer / écarter / visite / rétablir → RPC + maj optimiste ; statut persistant entre 2 ouvertures.
- **Historique** : `app_get_search_timeline` (réel).
- **Alerte** : seuil réel ≥ 80 %, état depuis `is_active`.
- **Insights « À surveiller »** : calculés depuis le feed (biens hors budget, densité secteur).
- **Présentateur plein écran** : carrousel des **vraies photos** du bien (`app_get_dossier_photos`), critères, verdict.
- **Cloche notifications** : `src/NotificationsBell.tsx` (scopé `.gti-notif`) dans le header, badge non-lues, marquage lu.
- **Reporting** : `src/RapprochementStats.tsx` (scopé `.ra-stats`), ouvert depuis le menu ⋯.

---

## 7. Envoi email (intégration Gmail)

- Bouton « Envoyer l'email » → **popup de confirmation obligatoire** (destinataire + expéditeur en clair, avertissement « envoi irréversible »).
- Sur confirmation → `sendGoogleWorkspaceCrmEmail` (lib/api.ts → backend FastAPI `POST /google-workspace/gmail/send`) : `subjectEmail` = Gmail négociateur résolu (`resolveGoogleWorkspaceCalendarEmail`), `to` = email réel acquéreur, `bodyHtml` = message + cartes biens (photo/ref/prix/specs), `relatedEntityType:'contact'`.
- **Proposition tracée uniquement si `res.ok`** (bien → proposé + relance J+5) ; échec → message clair, **aucune** proposition.
- Garde-fous : envoi désactivé si Gmail négo n'est pas `@gti-immobilier.fr` ou si pas d'email acquéreur ; greeting dynamique (nom acquéreur) ; `dryRun` disponible.
- **Backend** : `backend/` (FastAPI, uvicorn port 8010), domain-wide delegation Google (compte de service). En dev local il faut le lancer ; en prod il est en service. Test d'envoi réel non effectué en local (backend non lancé) — code + sécurité validés, à valider en prod.

---

## 8. Découpage du chantier (étapes A→E)

- **Étape 1** — brief acquéreur branché sur les vraies données.
- **A** — rapprochements calculés + persistés (scoring SQL, feed réel).
- **B** — traçabilité (propositions, statuts, relances).
- **C** — recalcul auto (file + pg_cron) + alertes négociateur (+ garde-fou anti-spam : ≤ 1 alerte/négo/bien).
- **D** — score vivant (couvert par le mécanisme de C : trigger prix → re-score + ré-tri).
- **E** — stats & reporting + raffinement (exclusion des recherches sans type NI secteur du scan d'alertes).
- **Finitions** — historique réel, alerte réelle, insights calculés, vraies photos (feed + présentateur), envoi email Gmail.

---

## 9. Techniques notables

- **Scoring SQL pur IMMUTABLE** sur entrées jsonb → testable, cacheable, déterministe.
- **Pondération renormalisée** : robustesse face aux critères/données incomplets, sans inventer de valeurs (règle « En construction » plutôt que mock).
- **File `dirty` + cron batché** : découple le recalcul lourd du push quotidien massif (anti-trigger-storm).
- **Refresh paresseux** (`max_age` 24 h) : la 1re ouverture d'une recherche calcule, les suivantes lisent.
- **Coalescence de la file** (UNIQUE + ON CONFLICT, préférence `new`) : un bien modifié N fois = 1 entrée.
- **Index unique partiel** `WHERE read_at IS NULL` + `ON CONFLICT DO NOTHING` : dédup des notifications (cap ~66 négociateurs).
- **Écritures via RPC `SECURITY DEFINER`** + lecture RLS `authenticated` : pas d'écriture directe client.
- **Parsing JSON limité aux candidats** (≤ 381 biens) au (re)calcul, jamais à la lecture d'écran.
- **CSS 100 % scopé** (`.rech-acq`, `.gti-notif`, `.ra-stats`) → zéro collision avec les ~9 250 `!important` de `styles.css`.
- **Vérification visuelle** via stubs temporaires + introspection DOM/`getComputedStyle` (la preview atteint le vrai Supabase).

---

## 10. Limites connues / backlog

- **Secteur « mou »** : les biens hors secteur restent affichés à score réduit (pas exclus). À arbitrer (filtre dur vs rayon km — géoloc dispo à 100 %).
- **Qualité des critères** : 666 recherches actives sans secteur, 11 totalement vides (déjà exclues du scan d'alertes). → inciter les négociateurs à renseigner type + secteur.
- **Équipements / DPE** : hors scoring (données à ~43 % / lettre DPE non confirmée) — bonus futurs.
- **Badge « nouveautés »** (isNew) : désactivé (pas de date de mise en marché dans le RPC de lecture).
- **RLS notifications/stats** : actuellement `authenticated USING(true)` → à scoper par négociateur.
- **Email** : test d'envoi réel à valider en prod (backend Gmail).
- **Perf** : si `app_rapprochement` grossit fortement, promouvoir surface/pièces/chambres en colonnes de `app_dossier_current` via le pipeline (précédent : `photo_url_listing`).

---

## 11. Fichiers & migrations

**Front** : `src/RechercheAcquereur.tsx`, `src/recherche-acquereur.css`, `src/NotificationsBell.tsx`, `src/notifications-bell.css`, `src/RapprochementStats.tsx`, `src/rapprochement-stats.css`, ajouts dans `src/lib/api.ts`, intégrations additives dans `src/App.tsx` + `src/main.tsx`.

**Migrations Supabase** : `rapprochement_engine_etape_a`, `..._etape_b_tracabilite`, `..._etape_c_recalc_auto`, `..._etape_c_notif_guard`, `..._etape_e_stats`, `recherche_acquereur_timeline_photos`.

**Déploiement** : commits `0306dd3 → cd1aac2` poussés sur `origin/main` (fast-forward), build Vercel `groupe-gti`. Migrations déjà appliquées sur la base prod `dwaqxfrinihnychuoptk`.
