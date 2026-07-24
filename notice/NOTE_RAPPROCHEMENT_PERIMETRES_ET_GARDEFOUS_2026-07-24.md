# Rapprochement : périmètres, actualisation, garde-fous & pièges d'`app_dossier_id`

_Note technique équipe — 2026-07-24. Rédigée à partir d'un cas réel (annonce Hektor 62444, T4 Firminy, mandat 18678)._

## TL;DR
- Il existe **deux périmètres distincts** : l'écran **rapprochement de l'app** (matchs vivants) et l'**espace client** (historique des biens proposés). Ils ne montrent pas la même chose.
- Un bien n'est **éligible au rapprochement que s'il est `Actif` + `diffusable='1'`** (le moteur exclut Sous offre / Sous compromis / Estimation / Vendu / archivé / non diffusable).
- `app_dossier_id` est un **surrogate local AUTOINCREMENT**, jamais réutilisé : il peut **changer** pour une même annonce (delete+réinsert / rebuild), ce qui crée des **orphelins**.
- Correctifs livrés le 24/07 : réconciliation qui **re-pointe** les retours acquéreur (plus d'orphelin), + **garde-fou d'affichage** (statut re-vérifié à l'affichage), + réparation ponctuelle.

---

## 1. Les deux périmètres

### A) Écran « rapprochement » de l'app = matchs VIVANTS
- Source : table `app_rapprochement`, calculée par la RPC `app_upsert_one_rapprochement(search_key, dossier_id)`.
- **Règle d'éligibilité (au calcul)** :
  `statut_annonce = 'Actif'` **ET** `diffusable = '1'` **ET** `score ≥ 60` **ET** `app_match_score_v2.eligible = true`.
  Sinon → la ligne de rapprochement est **supprimée**.
- Lecture : `app_get_rapprochements(search_key)` → `JOIN app_dossier_current` (strict) + `eligible=true` (+ depuis le 24/07 : `statut='Actif' AND diffusable='1'`, voir §4).

### B) Espace client (`/espace/{token}`) = historique des biens PROPOSÉS
- Source : `app_email_envoi_bien` + `app_bien_acquereur_statut` (ce qui a été **envoyé** au client), **PAS** `app_rapprochement`.
- Chaque bien proposé est affiché **s'il est encore dans `app_dossier_current`** (sinon masqué « vendu/archivé »).
- Sert à montrer l'historique + les **retours du client** (cœur / pouce / motif).

> Conséquence : un bien peut être **dans l'espace** (car proposé un jour) sans être un **match vivant** dans l'app, et inversement.

---

## 2. Actualisation

| | Déclencheur | Appelle Hektor ? | Fraîcheur |
|---|---|---|---|
| **App rapprochement** | Lecture `app_get_rapprochements` : si marqueur `app_rapprochement_search_state.computed_at` > 24 h → enfile un recalcul (`app_rapprochement_dirty`), traité par un worker. Read-through d'une fiche = recompute ciblé. | Non (recalcul en base) | ≤ 24 h, ou immédiat à l'ouverture d'une fiche |
| **Espace client** | Régénéré **en direct à chaque ouverture** du lien. | **Non** — lit `app_dossier_current` à l'instant T | = fraîcheur de `app_dossier_current` (run quotidien + read-throughs ailleurs) |

Le **run quotidien** (`scheduled/run_quotidien.ps1`, ~05:30) synchronise par **delta de `date_maj`** depuis Hektor (2 portes : web/cookies en écriture, **API/JWT en lecture**). Le **read-through** (ouverture d'une fiche) = `refresh_single_annonce.py` (local) + `push_single_annonce_to_supabase.py` (Supabase).

---

## 3. Le piège des `app_dossier_id` (à connaître absolument)

- `app_dossier_id` = clé **surrogate AUTOINCREMENT locale (SQLite)** — `phase2/schema_phase2.sql`. **Ce n'est PAS** l'id Hektor, ni le `numero_dossier`, ni un hash.
- Le compteur ne recule/réutilise **jamais** (~3,9 M pour ~57 k lignes = fort churn historique).
- Quand la ligne locale d'une annonce est **DELETE puis ré-INSERT** (rebuild, purge…), l'annonce reçoit un **id neuf plus élevé** → l'ancien devient **fantôme**.
- **Cas 62444** : id `567590` (ancien, snapshot figé « Actif ») → `1670774` (courant, « Sous offre »). Même annonce, deux ids. La bascule vient d'un rebuild (~20/06), **pas** du changement de statut.
- Le passage **Actif→Sous offre ne mint PAS d'id** et ne sort pas l'annonce du parc (`app_dossier_current` inclut Actif/Sous offre/Sous compromis/Estimation) — mais la sort de l'**éligibilité** rapprochement.

---

## 4. Correctifs livrés (2026-07-24)

1. **Réconciliation anti-orphelin** — `phase2/sync/push_single_annonce_to_supabase.py::reconcile_annonce_dossiers` :
   re-pointe désormais l'ancien `app_dossier_id` → le bon dans **`app_email_envoi_bien`** et **`app_bien_acquereur_statut`** (best-effort). Avant, ces 2 tables étaient oubliées → le retour du client (cœur/pouce/motif) restait collé au fantôme et devenait invisible.
2. **Garde-fou d'affichage** — RPC `app_get_rapprochements` **et** `app_count_rapprochements_for_contact` :
   ajout de `statut_annonce='Actif' AND diffusable='1'` à l'affichage/au comptage. Un bien qui passe non-Actif est **exclu immédiatement**, sans attendre le recalcul (fenêtre ≤ 24 h fermée). Liste et compteur « N biens » restent cohérents.
3. **Réparation ponctuelle** : l'unique retour orphelin (567590 → 1670774) a été re-pointé en base ; le refus « Trop cher » réapparaît sur l'annonce vivante.

---

## 5. Vérifier la vérité côté Hektor (API porte 2, lecture pure)

Depuis `C:\Hektor\Projet` (credentials dans `.env`, venv `.venv`) :

```bash
# date_maj seule
./.venv/Scripts/python.exe phase2/sync/annonce_datemaj_from_api.py --annonce-id 62444
# -> {"datemaj": "2026-07-23 10:24:03"}
```

```python
# statut + date_maj + prix (aucune écriture)
from hektor_pipeline.common import Settings, HektorClient
a = HektorClient(Settings.from_env()).get_json('/Api/Annonce/AnnonceById/', params={'id':'62444'}).get('annonce') or {}
# a['statut'] -> {'id':'3','name':'Sous offre'} ; a['keyData']['datemaj'] -> '2026-07-23 10:24:03'
```

Forcer un read-through complet d'une annonce :
```bash
./.venv/Scripts/python.exe -m phase2.sync.refresh_single_annonce --id-annonce 62444
./.venv/Scripts/python.exe -m phase2.sync.push_single_annonce_to_supabase --hektor-annonce-id 62444
```

> **Attention `source_updated_at`** (dans `app_dossier_current`) ≠ `date_maj` de l'annonce. L'export (`export_app_payload.py:1404`) le dérive d'une ligne source **orientée mandat** (date du mandat), qui prend le dessus. Ne pas l'utiliser comme indicateur de fraîcheur du détail ; la vérité est le `date_maj` local (`data/hektor.sqlite`) ou l'API.

---

## 6. Points ouverts (non corrigés)
- **Latence de recalcul** : le garde-fou d'affichage masque un bien non-Actif immédiatement, mais la ligne `app_rapprochement` (eligible=true) périmée n'est vraiment supprimée qu'au prochain recompute (dirty/24 h ou read-through). Cosmétiquement OK, mais la donnée sous-jacente reste jusqu'au recompute.
- **Espace client** : un bien proposé qui sort de `app_dossier_current` est **masqué** (pas d'historique « ce bien était proposé, il est parti »). À décider si on veut conserver la trace.
- **`app_get_rapprochements_for_dossier`** (vue bien→acquéreurs, cockpit) : non modifiée (vue négociateur, pas un canal de proposition client).
