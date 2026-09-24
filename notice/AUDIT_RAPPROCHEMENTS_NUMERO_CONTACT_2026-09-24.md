# Audit — rapprochements, clés, numéro de contact dans les tables satellites

*24/09/2026 au soir, demandé par Frédéric (« audit et vérifier mes codes et mon projet en
profondeur sur les rapprochements, clés etc. »). Lecture seule : Supabase (structure,
fonctions, tâches cron, données), code local, front. Rien n'a été écrit.*

**Audit limité à :** la désignation d'un CONTACT et d'une RECHERCHE dans les tables
satellites de Supabase (rapprochements et voisines). Les annonces (C.9) et les relations
(carnet C.9-d) ne sont pas re-mesurées ici.

## 1. Le constat de départ

Un contact créé chez Hektor passait une nuit sous son numéro Hektor (corrigé le 24/09 par la
seconde passe du build, `541c0ca`). Tout ce que l'app lui accrochait ce jour-là gardait
l'ancien numéro. Question : est-ce grave, et où d'autre ?

## 2. Les deux clés — l'une tient, l'autre non

| clé | état mesuré |
|---|---|
| **`contact_search_key`** (la recherche) | **SAINE.** 50 204 rapprochements : 100 % pointent une recherche active existante. Historique des scores 452 149 lignes : 0 clé introuvable. Seules 2 demandes de visite (`app_espace_visite_request`) ont une recherche introuvable. La clé est figée par son nom : elle ne change pas quand le contact change de numéro (vérifié en répétition, 5/5). |
| **`hektor_contact_id`** (le contact) | **FRAGILE.** Voir ci-dessous. |

## 3. Qui écrit le numéro de contact — et ne le met jamais à jour

| table | écrivains | que fait la mise à jour ? |
|---|---|---|
| `app_rapprochement` | `app_upsert_one_rapprochement`, `app_refresh_rapprochements_for_dossier`, `app_refresh_rapprochements_for_search`, `app_bulk_recompute_chunk` (cron chaque minute) | `ON CONFLICT … DO UPDATE SET score, score_components, eligible, computed_at` — **jamais `hektor_contact_id`** |
| `app_bien_acquereur_statut`, `app_proposition` | `app_set_bien_statut`, `app_record_proposition` | idem : statut, canal, dates — **jamais le contact** |
| `app_search_count_high_water` | `app_refresh_search_count_high_water` (cron 06:00) | **clé primaire = le numéro de contact** : un contact qui change de numéro repart à zéro, l'ancienne ligne reste orpheline |
| `app_relance_rapprochement`, `app_search_provisional` | insertions simples | numéro figé à la naissance |

**Et rien ne déclenche de recalcul quand un contact change de numéro** : le déclencheur
`trg_search_dirty` ne réagit qu'aux CRITÈRES de la recherche (prix, villes, types…) et à
`is_active`. Même recalculée, une ligne existante ne voit que son score mis à jour.

➡ **Un rapprochement garde à vie le numéro de contact qu'il avait à sa naissance.**

## 4. Qui lit par ce numéro — ce que voit l'utilisateur

| fonction | appelée par | effet d'un numéro périmé |
|---|---|---|
| `app_get_rapprochements_for_dossier` | écran « acquéreurs rapprochés » d'un bien (`api.ts:3412`, `RapprochementMandat.tsx`) | `LEFT JOIN app_contact_current ON hektor_contact_id` → **ligne sans nom, email, téléphone, négociateur** ; le numéro rendu ouvre une fiche qui n'existe plus |
| `app_count_rapprochements_for_contact(s)` | compteur « N biens » de la fiche et de l'annuaire (`api.ts:3563`, `:3576`) | filtre PAR ce numéro → **non compté** |
| `app_generate_rapprochement_alerts` | cron toutes les 5 min | `JOIN app_contact_current ON hektor_contact_id` → **pas d'alerte** pour ce contact |
| `app_get_dossier_timeline`, `app_contact_activite`, `app_get_search_timeline` | frises d'activité | jointures par numéro → événements absents de la frise |

## 5. L'ampleur, sur tout le parc (24/09 ~19 h)

| table | lignes | ancien n° Hektor (identité connue) | introuvable | les 2 colonnes se contredisent |
|---|---|---|---|---|
| `app_rapprochement` | 50 204 | **69** (5 contacts, tous éligibles) | 0 | 17 |
| `app_search_count_high_water` | 10 226 | **3** | 55 | 2 |
| `app_search_provisional` | 2 | **2** (provisoires du 18/09, déjà notés hors plan) | 0 | — |
| `app_console_deleted_contact_log` | 12 | 0 | 12 (normal : contacts supprimés) | 0 |
| `app_contact_provisional` | 2 | 0 | 2 (les provisoires du 18/09) | — |
| `app_google_calendar_event_link` | 11 | 0 | 1 | 0 |
| les 8 autres | 107 | 0 | 0 | 0 |

**0 action de négociateur** (statut, proposition) sur les 69 rapprochements touchés : rien de
ce qu'un humain a fait n'est perdu. **+30 cette nuit** : les rapprochements des 8 contacts neufs
du 24/09, qui recevront leur identité au build de nuit.

## 6. Pourquoi c'était tenu à la main jusqu'ici

- La **bascule du 23/09** (`app_bascule_identite_contact`) a traduit ces **13 tables « figées »**
  une fois, à la main — précisément parce que le build ne les refait pas.
- L'étape de nuit **`app_contact_id_propager`** (31/08, appelée par
  `propager_numeros_contact.py` juste après le push des contacts) parcourt 18 tables… mais
  **ne remplit que `app_contact_id` quand il est vide**. Elle ne corrige jamais un
  `hektor_contact_id` périmé. D'où les 17 lignes « contradictoires » : identité juste dans
  `app_contact_id`, ancien numéro dans `hektor_contact_id` — et c'est ce dernier que lisent
  les écrans.

## 7. Les chemins par lesquels un contact change de numéro

| chemin | état |
|---|---|
| la bascule du 23/09 | fait, tables figées traduites à la main |
| contact neuf créé chez Hektor : une nuit sous son n° Hektor | **fermé le 24/09** (seconde passe) — mais les 8 du 24/09 changeront cette nuit |
| réparation ponctuelle (L4-c-bis, 23 contacts) | fait le 24/09 → a produit les 69 |
| contact né dans l'app (≥ 20 M) | ne change jamais : le n° Hektor va dans `hektor_target_id` |
| fusion de doublons | non mesuré — aucune fusion appliquée à ce jour (audit « sans suppression ») |

## 8. Pièges pour la correction

- **4 index uniques contiennent le numéro de contact** : `app_contact_override` (PK),
  `app_contact_pending` (PK), `app_search_count_high_water` (PK), `app_search_pending`
  (contact, rang). Une traduction aveugle entrerait en collision si l'identité y a déjà sa
  ligne → **sauter ces cas et les compter**, sinon toute la réparation tombe.
- Un numéro < 10 000 000 encore porté par un contact de `app_contact_current` (contact neuf
  pas encore traduit) **ne doit pas** être traduit.
- `hektor_target_id` doit désigner **un seul** contact ; sinon, ambigu → sauter.
- Aucun envoi local ne réécrit ces tables (elles vivent dans Supabase) : une correction ne
  sera pas écrasée.

## 9. Proposition (à valider par Frédéric)

1. **Une fonction Supabase neuve**, `app_contact_retraduire_satellites(p_appliquer boolean default false)`,
   sur les **13 tables figées** de la bascule : remplace un `hektor_contact_id` < 10 M qui
   n'est plus porté par aucun contact par l'identité du contact dont c'est la cible Hektor
   (et remplit `app_contact_id`). À blanc par défaut ; saute et compte les collisions,
   les ambiguïtés, les contradictions ; trace dans un carnet.
2. **Appelée chaque nuit par `propager_numeros_contact.py`, AVANT `app_contact_id_propager`**
   (même étape, non bloquante, juste après le push des contacts).
3. **Une sonde** : lignes des 13 tables sous un ancien numéro Hektor dont l'identité est
   connue — seuil 0.
4. Ce soir : la fonction appliquée par Frédéric, lancée à blanc, puis pour de bon → les 69
   réparés ; cette nuit, les 30 automatiquement.

Non retenu pour l'instant : faire lire les écrans par `app_contact_id` (plus robuste, mais
réécrit 7 fonctions lues par le front) ; faire mettre à jour le numéro par les écrivains du
moteur (ne couvrirait que les rapprochements recalculés).
