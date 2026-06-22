# Note — Annonces « En création » (brouillons) Hektor → App

Date : 2026-06-22. **Analyse seule, aucun correctif appliqué.** Déclencheur : agence Groupe GTI Tence (`hektor_agence_id=9`), annonce **62283** absente de l'app. Conclusion **confirmée en live** par requête GraphQL Console (lecture seule).

> ⚠️ Cette note remplace les hypothèses intermédiaires erronées (marqueur `valide`, puis `statut=null`). **Le vrai marqueur est `isDraft`.**

## 1. Le marqueur officiel = `isDraft` (GraphQL Console, PAS l'API REST)
- Un brouillon Hektor est identifié par le flag booléen **`isDraft: true`**, exposé **uniquement** par la GraphQL de la Console la-boite-immo (`PropertyListing`), **pas** par l'API REST (`AnnonceById`/`ListAnnonces`) que consomme `sync_raw`.
- Un brouillon **porte quand même un `status`** : le plus souvent `status=2` (Actif), parfois `status=null` s'il vient d'être créé. Donc le statut/REST ne permet PAS de le distinguer — c'est pour ça que les brouillons « ressemblent » à des Actif côté app.
- `valide` n'est PAS le marqueur (des vrais Actif sont `valide=0`).

## 2. Confirmation live (Tence, 2026-06-22, lecture seule)
Requête `PropertyListing` réelle, scope groupe (22 178 biens courants) :
- 7 candidats Tence → **tous `isDraft=true`** : `61761, 61762, 61776, 62074, 62125, 62317` (`status=2`, prix 0, `isValid=false`) et `62283` (`status=null`).
- Témoins vrais actifs `62308 / 62316` → **`isDraft=false`** (`status=2`, `isBroadcasted=true`, `isValid=true`, prix>0).
- 62283 **est listé** par GraphQL (donc récupérable). Seules les fiches dont aucune étape wizard n'a été enregistrée échappent au listing (cf. cas `62202` du rapport).

## 3. La route documentée pour les retrouver
- Doc : [Console/RAPPORT_TECHNIQUE_CONSOLE_HEKTOR.md](../Console/RAPPORT_TECHNIQUE_CONSOLE_HEKTOR.md) §4.1 et §5.3.
- Endpoint : `POST https://groupe-gti-immobilier.la-boite-immo.com/ws/GraphQL_Web`, operation `PropertyListing` (champs `isDraft/isBroadcasted/isValid/status/price`).
- Filtres : `{limit:50, offers:["SALE"], status:"ALL", page, order:"LATEST", sources:["local"], archived:false}`. **Pas de filtre « drafts only »** → on filtre côté client sur `isDraft===true`.
- Auth : Cookie + `Authorization: Bearer <token>` lus depuis `Console/sessions/storage_state_*.json` ; scope = utilisateur/agence (impersonation pour scoper à une agence).
- Déjà codé : `fetchLatestHektorProperties()` ([Console/console_job_worker.js:1962](../Console/console_job_worker.js)) via `hektorGraphQLOperation()` ([:1928](../Console/console_job_worker.js)). Le worker lit `isDraft` (scoring/exclusion [:2491](../Console/console_job_worker.js)) mais **ne le persiste nulle part** dans l'index annonce/app.

## 4. Pourquoi l'app se trompe aujourd'hui
- Le pipeline app = **run REST `GTI Quotidien` → `sync_raw`**, **aveugle à `isDraft`**. Un brouillon lui apparaît `statut=Actif` (ou null).
- Conséquences (proxy REST « voie Actif + coquille vide : prix=0 ET sans mandat ») :
  - **Tence** : 26 vrais Actif / 7 brouillons → 6 affichés « Actif » à tort + 1 (62283, status null) invisible (détail `AnnonceById` renvoie vide → jamais stocké, jamais retenté → accumulation).
  - **Global** : ~541 vrais Actif / **~219 brouillons** → **~189 affichés « Actif » à tort** + **~30 invisibles** (status null) qui s'accumulent.

## 5. Durée d'un balayage GraphQL (mesurée)
- ~**3,0 s/page** (50 biens/page, séquentiel) ; latence dominée par le serveur Hektor.
- Scope groupe 22 178 biens → ~**444 pages ≈ ~22 min** séquentiel.
- Réductible : **concurrence** (5–10 parallèles → ~2–4 min) ou **scope par agence** (impersonation → quelques pages/agence).

## 6. Pistes (NON appliquées — à cadrer)
- Faire porter la classification `state=brouillon` par la **couche Console** (balayage `isDraft` → persister vers un panier brouillon), pas par le run REST.
- Filet REST séparé pour les coquilles `status=null` sans détail (`last_detail_sync_at IS NULL`), indépendant de `date_maj`, pour qu'elles se **transforment en Actif** une fois remplies.
- Décider l'affichage front : sortir les brouillons de la liste « Actif » et les regrouper sous `state=brouillon`.

## 7. Contrôle live du worker de modification (2026-06-22)
Test maîtrisé sur annonce jetable **62556** (Firminy, créée puis supprimée), file vide (zéro effet de bord) :
- **Création** (`create_hektor_draft_annonce`) : ✅ crée une annonce **non-draft** (`is_draft=false`, `is_broadcasted=false`) — confirme que depuis le 15/05 le worker fait `saveAndQuitte()`, pas de brouillon.
- **Modification intérieur** (`update_hektor_annonce_fields`) : ✅✅ groupe `ag_interieur` → `{"result":"1","message":"mise à jour effectuée."}` (surface→surfappart, room_count→nbpieces, bedroom_count→NB_CHAMBRES) + description OK. **Aucun « Credential Error » en contexte propre.**
- **Conclusion** : le « Credential Error » des jobs réels (annonces 10023, 24113) est **spécifique au contexte/droits de ces annonces**, PAS un défaut du worker. Le worker de modif est sain.
- **Suppression** : exige un jeton `confirm_text="SUPPRIMER {id}"` (garde-fou). ✅ 62556 supprimée (API 404, Supabase nettoyé).
- **NON testé / à vérifier** : `link_hektor_mandant` (rattacher un mandat, 0 exécution prod) + prix (refusé hors workflow mandat). → c'est la pièce manquante pour **finaliser** un brouillon (mandat + prix), pas pour le compléter en descriptif.

Lié à [[annonces-en-creation-brouillon]], [[bug-annonces-archivees-fantomes-table-active]], [[hektor-sync-trou-recherche]].
