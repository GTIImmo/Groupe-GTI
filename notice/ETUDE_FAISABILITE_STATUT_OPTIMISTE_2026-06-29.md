# Étude de faisabilité — Changement de statut optimiste (calque + read-through)

Date : 29/06/2026
Question : peut-on rendre la modale « changer statut » optimiste (affichage instantané), comme les autres calques optimistes (édition champs / contact / recherche) + read-through ?

## Réponse courte
**Oui, faisable, et même plus SIMPLE que l'édition de champs** — mais avec **une nuance clé** : le statut s'affiche via des **colonnes dérivées dans le listing**, donc le calque doit être en **modèle « colonnes plates » (façon contact)**, lu EN PREMIER par le badge — PAS le calque niché `app_optimistic_overlay` (façon édition de champs, qui n'est lu qu'à l'ouverture du détail).

## Ce qui existe déjà (et qu'on réutilise)
- **Le changement de statut est une action IMMÉDIATE** : `createChangeHektorAnnonceStatusJob` insère un job `change_hektor_annonce_status` → worker change dans Hektor → **`handleChangeHektorAnnonceStatus` fait DÉJÀ un read-through** (`enqueueRefreshConsoleDataJobBestEffort`). Donc la réconciliation existe déjà ; il manque seulement l'affichage instantané entre le clic et le retour read-through (~quelques secondes).
- Pas de debounce (≠ édition champs débouncée 10 min) → on n'a PAS besoin de la machinerie pending/cron-sweep/push. C'est plus proche du **calque de CRÉATION** (marqueur transitoire → réconcilie → nettoie) que du calque d'édition.
- Garde-fous existants annonce (dirty-skip, `base_snapshot._date_maj`) déjà en place.

## La nuance technique (le point à ne pas rater)
Le badge statut est calculé à partir de colonnes PLATES de `app_dossier_current`, lues directement par le listing :
- **Vendu** = `vente_id != null`
- **Sous compromis** = `compromis_id != null && compromis_state ≠ annulé`
- **Offre reçue** = `offre_id != null && offre_last_proposition_type ∈ {proposition, accepte}`
- sinon **`statut_annonce`** (Actif, …)

Conséquences :
1. Le calque doit écrire des **colonnes** (le listing ne lit pas l'overlay niché). → modèle contact, pas modèle annonce-overlay.
2. **On ne connaît pas encore les vrais IDs** (offre_id/compromis_id/vente_id sont créés par Hektor). Il ne faut **PAS falsifier** ces colonnes (les IDs servent aussi à l'annulation, aux jointures, à `etat_transaction`). → introduire un **marqueur transitoire dédié** que le badge lit EN PREMIER.

## Architecture proposée (additive, calque colonne + read-through)
1. **Colonne(s) transitoire(s)** sur `app_dossier_current` (additif) :
   - `optimistic_status_target` (text : 'active'|'offer'|'compromise'|'sold'|'closed', null sinon)
   - `optimistic_status_at` (timestamptz) pour le TTL.
2. **RPC `app_change_annonce_status_optimistic(target_dossier_id, target, …)`** : écrit la/les colonne(s) transitoire(s) instantanément, PUIS crée le job `change_hektor_annonce_status` existant (ou laisse le front le créer). Service role / RLS comme les autres RPC.
3. **Badge lit le transitoire EN PREMIER** : dans `avStatut` (listing) et le badge détail, si `optimistic_status_target` est posé → afficher le statut cible (avec une nuance visuelle « en cours… », pastille qui pulse comme la création), sinon dérivation actuelle (vente_id/compromis/offre/statut_annonce). Modif chirurgicale dans `hasOffreAchatEnCours`/`hasCompromisEnCours`/`avStatut` OU surcouche au-dessus.
4. **Front instantané** : au clic, on patche aussi la ligne en mémoire (badge flippe tout de suite) + on appelle le RPC ; persistance assurée par la colonne au prochain refetch (poll 5 s / dataReloadKey).
5. **Nettoyage au read-through** : `handleChangeHektorAnnonceStatus` (qui fait déjà le read-through) efface `optimistic_status_target` une fois le vrai statut dans Supabase (comme le cleanup de la création). + **garde-fou dirty-skip** pendant la fenêtre.
6. **TTL sweep** (cron, comme la création) : si le worker meurt, on efface le transitoire après X min (retour au statut réel) — pas d'« erreur » bloquante car le statut réel reste valide ; éventuellement un badge « changement non confirmé ».

## Périmètre par cible (ce qu'on affiche instantanément)
| Cible | Badge instantané | Réconciliation |
|---|---|---|
| active | « Actif » | read-through |
| offer | « Offre reçue » | read-through (offre_id réel) |
| compromise | « Sous compromis » | read-through (compromis_id réel) |
| sold | « Vendu » | read-through (vente_id réel) |
| closed | « Archivé/Clos » | read-through |

Le calque n'affiche que le **badge de tête** instantanément ; les détails de transaction (montant, dates, acquéreur, honoraires) restent reconstruits par le read-through (on ne duplique pas la logique Hektor). C'est suffisant pour l'UX (le badge est ce que l'utilisateur attend de voir bouger).

## Effort / risques
- **Effort** : moyen. 1 migration (colonnes + RPC + TTL/cron + clear), worker (clear au read-through, ~10 lignes), front (badge lit le transitoire + patch mémoire au clic). Pas de debounce/pending à construire.
- **Risques** : faibles si additif. Le seul piège = ne pas polluer les vrais IDs ; le marqueur dédié l'évite. Bien gérer le cas « cible = active » (lever offre/compromis) côté badge.
- **Réutilisation** : ~80 % des briques existent (read-through, garde-fous, pattern create-calque, cron sweep).

## Recommandation
Faisable et cohérent. Procéder par lots, derrière un flag (comme la création) :
- **Lot 1** : migration (colonnes + RPC + clear au read-through) + badge listing/détail lit le transitoire + patch mémoire au clic. Tester sur 1 cible simple (sold ou active).
- **Lot 2** : TTL sweep + nuance visuelle « en cours… » + garde-fou dirty-skip.
- **Lot 3** : couvrir les 5 cibles + tests E2E par cible.

Lié : calque création optimiste (même esprit transitoire+réconcilie+nettoie), édition champs optimiste (RPC+overlay+pending), read-through transaction (offre/compromis/vente).
