# Architecture de synchronisation Hektor ↔ App — Document de référence (consolidé)

Date : 2026-06-19. **Aucun code modifié — référence d'architecture.**
Consolide : `RAPPORT_ANALYSE_SYNC`, `RAPPORT_ARCHITECTURE_CIBLE`, `PLAN_CORRECTIFS_ET_PLANNING`.

---

# PARTIE A — L'EXISTANT (audit corrigé)

## A.1 Le run quotidien actuel (≈40 min, 18 étapes, INCHANGÉ)
`sync_raw` (negos, annonces, contacts, mandats, offres, compromis, ventes, broadcasts) → `normalize` → **détail contacts** (delta date_maj) → `build_case_index` / `bootstrap` / `refresh_views` → **build couche contacts** → contrôles qualité → **chauffages** (scrape Console) → champs manquants *(opt-in, off)* → **push annonces** → push annuaire → push contacts *(opt-in)* → **documents** *(opt-in, off)* → **Matterport** → liens RDV → vitrine Android *(opt)*.

## A.2 Comment chaque domaine détecte un changement (tableau définitif)
| Domaine | Extraction | Détection | Verdict |
|---|---|---|---|
| **Annonces** | listing + détail API | **`date_maj`** (à la seconde) + hash | 🟢 fiable |
| **Contacts (identité)** | listing + détail | **`date_maj` delta** (`--changed-only`) | 🟢 fiable |
| **Recherches** (dans le contact) | dans `ContactById` | **`date_maj` du CONTACT** | 🔴 **aveugle** (date_maj ne bouge pas) |
| **Mandats** | `MandatsByIdAnnonce` (avec le détail de l'annonce) | avec l'annonce | 🟢 seule source à jour |
| ~~**Mandats** via `ListMandat`~~ | ~~toutes pages~~ | ~~listing complet~~ | 🔴 **tronqué côté Hektor** (voir ci-dessous) |
| **Relations** (mandant/proprio/transactions) | détail contact + listes offres/compromis/ventes + lien annonce | listes quotidiennes + chemin annonce | 🟢 faible risque |
| **Vignette DPE/GES** | **API** (classe énergie) → **URL calculée** | avec l'annonce | 🟢 fiable |
| **Détail chauffage** | **scrape Console** (Playwright) | `date_maj DESC` + `source_hash`, **50/jour**, backstop 30 j | 🟢 priorisé (modifs/nouvelles d'abord) |
| **Photos affichées** (`photo_url_listing`, `images_preview_json`) | **dans l'annonce** | avec l'annonce | 🟢 fiable |
| **Documents** | scrape Console | présence | ⚪ **opt-in, OFF par défaut** |
| **Matterport** | API Matterport | hash | 🟢 fiable |

> **Correctif du 21/07/2026 — `ListMandat` est tronqué à la source.** La ligne « listing complet / pas d'oubli » ci-dessus était fausse, et contredisait déjà `notice/NOTE_MODIFS_MANDATS_UPDATE_2026-03-24.md` (« même s'ils ne remontent pas dans `ListMandat` »).
>
> Mesuré par appels API réels le 21/07/2026 : `ListMandat` expose les mandats **n° 1 à 18339** (le dernier daté du 30/01/2026) et **s'arrête là**. Les **392** mandats suivants — n° **18340 à 18767**, jusqu'au 16/11/2026 — n'y figurent pas. La coupure est exactement à la charnière 18339/18340, sans chevauchement ni trou.
>
> Ce n'est ni un effet du tri, ni de la fenêtre `beginDate`/`endDate` : testé jusqu'à `2000-01-01 → 2099-12-31`, le maximum reste le 30/01/2026, et le listing s'arrête à la page 324. Le rapatriement **complet** du 30/03/2026, deux mois après la coupure, avait déjà ramené 6 490 mandats sans aucun postérieur au 30/01. Indice supplémentaire : les libellés de type changent à la charnière (`SIMPLE`/`EXCLUSIF` avant, `Mandat de vente exclusif en cas de démarchage` après) — deux sources distinctes.
>
> **Conséquence : aucun « filet » par listing ne peut fonctionner** tant que la source reste figée. La fraîcheur des mandats repose entièrement sur `MandatsByIdAnnonce`, appelé avec le détail de chaque annonce — d'où l'entrelacement détail+mandats introduit le 21/07 (commit `be18e94`), qui ne marque une annonce « à jour » qu'une fois ses mandats obtenus.
>
> À signaler au support Ma Boîte Immo.

## A.3 Les clés d'identité
Tout est **stable** (`hektor_annonce_id`, `app_dossier_id`, `hektor_contact_id`, `register_row_id=annonce:numero`, `relation_key` structurelle, UUID Matterport) — **SAUF `contact_search_key`** = hash du **contenu** → change à chaque édition.

## A.4 Particularités à retenir
- **DPE = API calculée** (pattern `DPE_IMAGE_BASE_URL` + classe), pas un scrape.
- **Chauffage = LE seul scrape Console encore actif** ; priorisé `date_maj`/`source_hash`, 50/jour ; une **nouvelle annonce** = en tête (récente + missing_cache) → scrapée ~le lendemain.
- **Photos affichées = colonnes de l'annonce** → suivent l'annonce (pas un trou).
- **Documents = opt-in** (`-EnqueueConsoleDocuments`), off par défaut.
- **Mandats = listing complet paginé** (≠ contacts en datemaj) → aucun oubli.
- **Relations = clé stable** (exclut état/montant/date) → maj en place, pas d'orphelin.
- 2 vues mandat (détail annonce + registre) = **2 tables** mais **un seul `refresh_single_annonce` les met à jour ensemble**.

## A.5 Les faiblesses (ciblées)
| Problème | Annonce | Mandat | **Recherche** |
|---|---|---|---|
| Détection (angle mort `date_maj`) | 🟢 | 🟢 | 🔴 |
| Orphelinage (clé qui bouge) | 🟢 | 🟢 | 🔴 |
| Écrasement Hektor (rebuild depuis Supabase) | 🟢 | 🟢 | 🔴 |
| **Latence** (pas temps réel — attend le run) | 🟠 | 🟠 | 🟠 |
→ La **recherche** cumule les 4. **Annonce/mandat n'ont que la latence** (réglée par le read-through).

---

# PARTIE B — L'ARCHITECTURE CIBLE

## B.1 Principe
**Frais au point d'usage** (read-through), **`date_maj` là où c'est fiable** (annonce/contact), **empreinte là où `date_maj` ment** (recherche), **filet de fond** pour le reste.

## B.2 Les 3 mécanismes (séparés)
1. **Quotidien actuel** — INCHANGÉ (tout : annonces, contacts, mandats, chauffages, DPE, documents, Matterport, Android…).
2. **Quotidien recherches actives** — NOUVEAU, **dédié** : balaie les ~3 800 recherches actives par **empreinte**, indépendant du gros run.
3. **Read-through** — à l'**ouverture** d'une fiche (événementiel).

## B.3 Le read-through (les règles)
- Raisonne par **« paquet »** :
  - **paquet annonce** = annonce + photos + **vignette DPE** + mandats + propriétaires → 1 `refresh_single_annonce` rafraîchit tout, **signal `date_maj`**.
  - **paquet contact** = identité + **recherches** → 1 `sync_contact_details --contact-id`, **signal hash** pour les recherches.
- **Détail** = read-through ; **Liste** = cache + run (comme l'annuaire contacts et la liste annonces). *(option future : read-through « fenêtré » sur les lignes visibles, pour toutes les listes.)*
- **Écrit TOUJOURS via le pipeline** : `Hektor → LOCAL (SQLite) → rebuild → SUPABASE`. **Jamais** de patch direct Supabase → sinon le run suivant écraserait Supabase avec le local périmé.
- **Optimisation « rien n'a changé »** : après le fetch, on compare empreinte/`date_maj` → si identique, **on s'arrête (~1-2 s)**, pas de push/recalcul.
- Le **chauffage** n'est **pas** re-scrapé au read-through (trop lourd, ne change jamais) → reste sur sa file dédiée.

## B.4 Les 4 correctifs
| # | Correctif | But |
|---|---|---|
| 1 | **Écriture sûre** | `update_hektor_contact_search` recharge Hektor d'abord (comme `update_hektor_contact`) → plus d'écrasement |
| 2 | **Clé recherche stable** | `hash(contact, index)` + remap orphelines → plus d'orphelins |
| 3 | **Read-through ouverture** | annonce/contact (`date_maj`) + recherche (hash) → l'immédiat |
| 4 | **Empreinte recherches actives** | balayage du périmètre → plus d'angle mort |

## B.5 Garde-fous transverses
TTL (~5 min) · garde-fou empreinte/`date_maj` (gros travail seulement si changé) · plafond concurrence Hektor + verrou anti-chevauchement · résilience session (403→refresh) · **toujours via le pipeline (local+Supabase)** · stale-while-revalidate (jamais vide) · audit des appels.

---

# PARTIE C — PLANNING HORAIRE

## C.1 Les niveaux d'exécution Windows
- **Services** (continus) = les 4 workers Console (jobs + read-through).
- **Tâches planifiées** (heure fixe) = les **runs** (quotidien actuel + recherches actives + relances).
- **pg_cron** (chaque minute) = recalcul rapprochement.
- **Événementiel** = read-through (à l'ouverture).

## C.2 Créneaux (à finaliser avec tes heures)
| Tâche planifiée | Cadence | Contenu |
|---|---|---|
| `GTI Quotidien` *(existant, inchangé)* | 1×/jour (heure actuelle) | TOUT (doc, Matterport, chauffage, Android…) |
| `GTI Recherches Actives` *(nouveau)* | **à définir** (1×/jour ou 2-3×/jour) | balayage empreinte des recherches actives |
| `GTI Relances Email` *(existant)* | 08:00 | relances |
| Read-through | continu (workers) | à l'ouverture |
| pg_cron | chaque minute | recalcul rapprochement |

---

# PARTIE D — ROADMAP

| Ordre | Chantier | Taille |
|---|---|---|
| **1** | Écriture sûre (recherche) | petit · **urgent** |
| **2** | Formaliser les tâches planifiées (squelette horaire) | petit (ops) |
| **3** | Read-through annonce/contact (`date_maj`) | moyen |
| **4** | Clé stable recherche + remap | moyen |
| **5** | Read-through recherche (hash) + quotidien recherches actives | moyen |
| **6** | Garde-fous (TTL, plafond, audit) | transverse |
| **7** | Tier 2 — Supabase-first (push Hektor différé sur le créneau du matin) | gros, stratégique |

---

## Synthèse en 5 lignes
1. **L'archi est saine** — annonces, mandats, contacts, relations, DPE (API), photos, Matterport : bien gérés (clés stables, hash, listing complet).
2. **Le seul vrai trou = la recherche** (détection aveugle + orphelinage + écrasement).
3. **La latence** (tout attend le run) touche tout le monde → réglée par le **read-through** (frais à l'ouverture, par paquet, via le pipeline local+Supabase).
4. **Le chauffage** = l'unique scrape Console restant, priorisé et plafonné — laissé sur sa file dédiée.
5. **On ajoute** : read-through + quotidien recherches actives + 4 correctifs recherche + garde-fous + planning fixe. **On ne refait rien.**
