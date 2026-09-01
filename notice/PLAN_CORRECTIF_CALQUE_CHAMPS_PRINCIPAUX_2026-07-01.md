# Plan — Correctif calque optimiste (champs principaux annonce/estimation)

Date : 01/07/2026
Statut : PLAN (non codé). À valider avant code.

## Le bug (rappel)
La modale « Modifier » (`HektorAnnonceUpdateForm`, annonce ET estimation) envoie les champs avec les **clés HEKTOR** (`NB_CHAMBRES`, `surfappart`, `prix`, `nbpieces`, `codepublique`…). Le RPC `app_edit_annonce_optimistic` ne sait écrire « à plat » (colonnes + blob JSON) que des **clés FRONT** (`bedroomCount`, `surface`, `price`, `roomCount`, `postalCode`…). Mismatch. Et l'affichage des champs principaux lit la valeur **à plat** (via le dict `mapped` dans `wizardDetailValue`, App.tsx:2230) **avant** de regarder le calque → le calque (qui a pourtant capté la modif en clé hektor) n'est jamais consulté pour ces champs.

Conséquence : **équipements/détails** (lus via le calque par clé hektor) = ✅ instantanés ; **surface/chambres/pièces/prix/ville/CP/terrain/titre** = ❌ pas instantanés (mais jamais perdus : worker + read-through les ramènent).

---

## PHASE 1 — Affichage instantané du détail (Solution 2, FRONT only)
**But** : que TOUS les champs du détail s'affichent tout de suite après édition.

**Quoi** : dans `wizardDetailValue` (App.tsx:2206-2235), lire **le calque EN PREMIER** (par `field.name`) avant le dict `mapped`.
- Aujourd'hui : `mapped[name]` (plat) → sinon `rawWizardDetailField` (calque) → sinon défaut.
- Cible : `overlay[name]` (calque) → sinon `mapped[name]` (plat) → sinon `rawWizardDetailField` → sinon défaut.
- Le calque contient déjà la modif avec la BONNE clé (hektor = `field.name`, ex. `NB_CHAMBRES`) → match → affiché. Au retour worker, le read-through efface le calque → la vraie valeur reprend (mécanisme existant).

**Couvre** : annonce ET estimation (même fonction), y compris la **valeur d'estimation** (`ESTIMATION_MONTANT`, déjà un champ wizard `mandat_infofi`) dans le DÉTAIL.

**Portée / risque** : 1 fonction, front uniquement. **Aucune** migration, aucun worker, aucune RPC. Pour les champs secondaires : lire le calque d'abord donne le même résultat qu'avant (ils y passaient déjà) → ne casse rien. **Risque minimal.**

**Limites de Phase 1** :
- Corrige le **détail** (la modale/fiche). PAS le **listing** (qui lit les colonnes/valeurs plates, pas `wizardDetailValue`).
- Ne relance PAS le **rapprochement** instantané (display only).

**Test** : éditer chambres + surface + un équipement (ex. cuisine) sur une annonce témoin → vérifier que les 3 s'affichent instantanément dans la fiche ; rouvrir après le worker → valeurs Hektor reprennent, pas de doublon/clignotement.

---

## PHASE 2 — Listing + rapprochement (RPC, backend) — « ensuite »
**But** : (a) que les champs principaux s'actualisent aussi dans le **listing**, (b) qu'une modif prix/surface/pièces **relance le rapprochement** instantanément.

**Cause commune** : le listing lit les **colonnes** (`prix`, etc.) et les **valeurs plates** ; le scoring lit `prix` (colonne) + surface/pièces (blob). Le RPC ne met à jour colonnes/blob/scoring que sur clés FRONT → les clés HEKTOR de la modale ne déclenchent rien.

**Quoi** : étendre le RPC `app_edit_annonce_optimistic` pour **reconnaître AUSSI les alias HEKTOR** (migration additive, on NE change PAS ce que le front envoie → zéro risque pour les champs secondaires qui passent par le calque) :
- `col_map` += `prix→prix`, `codepublique→code_postal`, `villepublique→ville`.
- `json_map` (blob plat) += `surfappart→surface`, `nbpieces→nb_pieces`, `NB_CHAMBRES→nb_chambres`, `surfterrain→surface_terrain_detail`, `GARAGE_BOX→garage_box_detail`, `latitude/longitude` (déjà OK).
- `scoring_keys` += les équivalents hektor (`prix`, `surfappart`, `nbpieces`, `NB_CHAMBRES`, `codepublique`, `surfterrain`…) → recompute déclenché.
- **Estimation** : mapper `ESTIMATION_MONTANT→prix` (colonne) pour que la « valeur estimée » du listing bouge (la colonne `prix` est aussi remplie pour les estimations).

**Effet** : avec Phase 2, les colonnes/blob sont écrits → le **listing** s'actualise, le **scoring** recalcule. (Note : ça rend même Phase 1 redondante pour les champs *mapped* — mais Phase 1 reste utile/sûre pour le détail et les champs non écrits en base.)

**Portée / risque** : 1 migration RPC additive (alias). À tester comme le Lot 1/RPC générique d'origine (via `set_config request.jwt.claims` + appel direct + restauration). Garde-fous existants inchangés (base_snapshot `_date_maj`, pending, dirty-skip). **Vérifier** : le `base_snapshot` doit aussi capturer la valeur de base des alias hektor (sinon le garde-fou anti-écrasement compare mal).

**Décision** : on peut s'arrêter à Phase 1 si seul le détail compte ; Phase 2 si le listing instantané et le rapprochement live sont voulus.

---

## Détail estimation
- **Couvert par Phase 1** pour le détail (même modale, `ESTIMATION_MONTANT` via calque).
- **Valeur estimée dans le listing** (lit la colonne `prix`, App.tsx:~27025) → nécessite **Phase 2** (`ESTIMATION_MONTANT→prix`).
- `EstimationDocumentEditor` (avis de valeur PDF) = **outil distinct** qui LIT les champs, ne les édite pas → non concerné.

## Autres calques optimistes (vérifiés)
- **Contact** = modèle **plat (colonnes directes)** via `app_edit_contact_optimistic` → l'affichage lit les colonnes mises à jour → **pas de calque, pas le bug**. RAS.
- **Recherche** = `app_edit_search_optimistic` (recompute rapprochement) → modèle différent (critères). **À confirmer** rapidement avant code qu'aucun champ recherche ne souffre du même court-circuit, mais a priori non concerné.
- **Création optimiste** (table `app_annonce_provisional`) = autre mécanisme (badge « En création »), **non concerné**.

## Ordre proposé
1. **Phase 1** (front, `wizardDetailValue` overlay-first) → test → commit/push → vérif visuelle.
2. Si validé : **Phase 2** (migration RPC alias hektor + scoring) → test base → vérif listing + rapprochement.
3. Confirmer recherche (rapide).

## Tests d'acceptation
- Détail annonce : chambres/surface/pièces/prix édités → s'affichent instantanément.
- Détail estimation : montant édité → s'affiche.
- (Phase 2) Listing : prix/surface visibles bougent ; rapprochement recalculé sur bien Actif+diffusable.
- Équipements/diagnostics : continuent de s'afficher (non cassés).
- Après worker : le calque s'efface, pas de clignotement, valeurs Hektor correctes.
