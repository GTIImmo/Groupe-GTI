# Correctifs — Garde-fou anti-écrasement ANNONCE (porte 2) + 2ᵉ modale contact en édition optimiste

**Date :** 2026-06-23
**Périmètre :** worker Hektor (`Console/console_job_worker.js`), pipeline porte 2 (`phase2/sync/`), front (`apps/hektor-v1/src/App.tsx`)
**Supabase :** projet `dwaqxfrinihnychuoptk` · **Repo :** `C:\Hektor\Projet`, branche `refonte-mobile` (= `main`), déploiement Vercel + worker en service Windows
**Statut :** **déployé + validé en prod** (test end-to-end concluant pour le garde-fou annonce)

---

## Contexte — les 2 portes d'authentification Hektor

Hektor (la-boite-immo) expose **deux portes d'auth distinctes** :

- **Porte 1 — web/admin** (XMLRPC `?mode=...`) : **cookie de session** (login navigateur Playwright). Sert à **écrire**. C'est ce qu'utilise le **worker Node** (`console_job_worker.js`).
- **Porte 2 — API REST** (`/Api/Contact/ContactById`, `/Api/Annonce/AnnonceById/`…) : **JWT** via OAuth (`HEKTOR_CLIENT_ID`/`HEKTOR_CLIENT_SECRET`). Sert à **lire**. C'est ce qu'utilise le **pipeline Python** (run quotidien).

**Conséquence clé :** le worker Node n'a **PAS** de JWT → ses appels directs `/Api/...ById` font **403 « You must be logged in »**.

---

## Correctif 1 — Garde-fou anti-écrasement ANNONCE réparé (commit `86aa1ad`)

### Symptôme / cause
Le garde-fou anti-écrasement annonce (Tier 2, dans `handleUpdateHektorAnnonceFields`) relit la `date_maj` Hektor du bien **avant** d'écrire un push optimiste `from_pending` : si le bien a été modifié dans Hektor **depuis** l'édition optimiste (date_maj plus récente que la photo `base_snapshot._date_maj`), il doit **bloquer** l'écriture (conflit) au lieu d'écraser.

Or il lisait cette date via un **appel Node direct** `fetchHektorAnnonceDetailKeyDataBestEffort` → **403** (pas de JWT) → `freshDateMaj = null` → la condition `if (freshDateMaj && freshDateMaj > baseDateMaj)` était **toujours fausse** → le garde-fou **n'a jamais bloqué** (best-effort : il écrivait toujours). **Garde-fou dormant.**

### Fix (miroir exact du garde-fou contact, Lot B)
1. **Nouveau Python léger** `phase2/sync/annonce_datemaj_from_api.py` (porte 2 / JWT OAuth, comme le run quotidien) :
   - Appelle `GET /Api/Annonce/AnnonceById/` (⚠️ **slash final obligatoire**, **sans** param `version`).
   - Lit `payload["annonce"]["keyData"]["datemaj"]` (cf. `refresh_annonce_nego_from_api.py`).
   - **AUCUN re-sync, AUCUNE écriture** locale/Supabase. Best-effort : sort `{"datemaj":"..."}` ou `{}`.
2. **Helper worker** `fetchAnnonceDateMajFromApi(job, annonceId, step)` (miroir de `fetchContactDateMajFromApi`) : lance ce Python via `runProjectPythonScript`, parse la dernière ligne JSON.
3. **Garde-fou** : remplacé l'appel Node direct par `const freshDateMaj = await fetchAnnonceDateMajFromApi(...)`. L'appel Node direct est **conservé** pour les flux confirm (`hektor_annonce_confirm_api` / `_admin_api`) — non orphelin.

### Compatibilité des formats (vérifié)
La comparaison `freshDateMaj > baseDateMaj` est **lexicographique** → les deux formats doivent être identiques.
- `base._date_maj` = `app_dossier_detail_current.detail_payload_json.date_maj`, ex. `"2026-03-12 17:16:34"`.
- API `AnnonceById` `keyData.datemaj`, ex. `"2026-06-15 15:27:59"`.
- Même format `YYYY-MM-DD HH:MM:SS` → comparaison correcte. ✅

### Test end-to-end (prod, concluant)
Job `update_hektor_annonce_fields` enfilé manuellement sur un **bien réel** (`hektor_annonce_id 46053`, `app_dossier_id 1375327`) avec `base_snapshot._date_maj = "2000-01-01 00:00:00"` (conflit garanti) et `push_fields.price` = **prix actuel** (no-op si jamais écrit, pour rendre le test sûr quelle que soit la version du worker).

Résultat : `status = held_conflict`. Log :
```
annonce_overwrite_guard · done
"Bien modifié dans Hektor depuis l'édition : écriture bloquée (anti-écrasement)"
base_date_maj  = "2000-01-01 00:00:00"
fresh_date_maj = "2026-06-15 15:27:59"   ← lu en LIVE via porte 2
```
→ Prouve : (a) worker bien à jour, (b) porte 2 opérationnelle (403 mort), (c) écriture bloquée, **aucun prix envoyé** à Hektor. Bonus : le **fallback agence** a aussi joué (négo résolu via `dossier_commercial_id_agency` → Lionel FLANDIN). **0 résidu** (pas de pending conflit parasite).

> ⚠️ **Piège ids de test :** les vrais `hektor_annonce_id` sont **PETITS** (46053, 59041…). `603798`/`1068399` sont des `app_dossier_id`, pas des `hektor_annonce_id` → 404 sur l'API.

---

## Correctif 2 — 2ᵉ modale contact basculée en édition optimiste (commit `11e72fc`)

### Contexte
Il existe **deux points d'édition contact** dans l'app :
1. `ContactEditModalV2` (App.tsx ~26160) — modale dédiée « Modifier le contact ». Déjà basculée sur `editContactOptimistic` (Lot C).
2. `HektorContactIdentityForm` (App.tsx ~23108) — formulaire **create + update** (prop `mode`), embarqué dans `ContactWorkflowModal`. Sa branche `update` faisait **encore** le job direct `createUpdateHektorContactJob`.

### Fix
Branche `update` de `HektorContactIdentityForm` → bascule sur `editContactOptimistic` (Supabase instantané + push Hektor débouncé via `app_contact_pending` + garde-fou anti-écrasement) + `dispatchEvent('hektor:contact-updated')`. **Chemin `create` strictement inchangé** (`createHektorContactJob` + `onJobCreated` + `onContactInputCreated`).

> ℹ️ Branche **dormante** aujourd'hui : aucun appelant ne rend ce formulaire en `mode="update"` (l'édition réelle passe par `ContactEditModalV2`). Modification faite **par cohérence** (si un jour ce parcours sert à éditer). `tsc -b` → exit 0.

---

## Bilan

Les **deux garde-fous anti-écrasement** (contact via `ContactById`, annonce via `AnnonceById`) sont désormais fonctionnels et **prouvés** sur le même schéma **porte 2 / Python** — le worker ne peut plus écraser une modification faite directement dans Hektor pendant qu'un push optimiste est en attente : il marque le conflit (`held_conflict` + notif négo) au lieu d'écraser. Résolution manuelle = ré-éditer dans l'app (même comportement que recherche/contact).

### Fichiers touchés
| Fichier | Nature |
|---|---|
| `phase2/sync/annonce_datemaj_from_api.py` | **nouveau** (porte 2, lecture date_maj annonce) |
| `Console/console_job_worker.js` | helper `fetchAnnonceDateMajFromApi` + swap 2 lignes du garde-fou |
| `apps/hektor-v1/src/App.tsx` | branche `update` de `HektorContactIdentityForm` → optimiste |

### Action côté exploitation
- **Worker à redémarrer** après tout déploiement de `console_job_worker.js` (code chargé en mémoire). Déjà fait + validé pour ce lot.
