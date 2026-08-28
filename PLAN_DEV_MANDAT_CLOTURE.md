# PLAN_DEV — Lot A : principe de clôture de mandat

> 🔴 **AVERTISSEMENT AJOUTÉ LE 28/08/2026 — LES DEUX LIGNES CI-DESSOUS SONT FAUSSES.**
>
> Elles ont été écrites comme un plan, **dans le même commit que le code qui les rendait
> caduques** (`1b6ef04`, 30/07), et jamais relues. Résultat : pendant un mois, ce document
> a fait croire que rien n'était livré et que tout dormait derrière un drapeau.
>
> **En réalité, au 30/07 :** A1 *(worker)*, A2 *(pipeline)*, A3 *(modale)*, A5
> *(annulation)* et A7 *(registre)* étaient **codés et actifs en production**. Et le
> drapeau `VITE_APP_MANDAT_CLOTURE_ENABLED` **n'existe nulle part dans le code** — le
> front n'en connaît que quatre. **Rien n'était éteint.**
>
> ➡ **L'état à jour est dans `notice/PLAN_DEV_ACTUALISE_2026-08-20.md`**, sections C.13-a,
> C.13-b et C.13-c. Le chantier a changé de nature le 28/08 : **la clôture ne passe plus
> par Hektor**, elle vit dans le serveur et l'app.
>
> Ce document reste utile pour ce qu'il documente bien : **le relevé exact du formulaire
> de Hektor**, motifs et sous-motifs compris. C'est à ce titre qu'il est conservé.

> ~~Statut : **cadrage validé, dev non commencé.** Rien de codé.~~
> ~~Flag global : `VITE_APP_MANDAT_CLOTURE_ENABLED` (OFF par défaut).~~
> Contraintes : additif/chirurgical (la rubrique mandat actuelle continue de marcher) ; écritures Hektor testées par l'utilisateur (garde-fou harness) ; build `npm run build` ; staging fichier par fichier.

## Contexte mécanique (contrôlé en direct sur VA6482 / annonce 24113, 2026-07-30)

- **Endpoint réel de clôture** (≠ ancien code worker `annonce-SuiviVente-saveMandatClos`, obsolète) :
  - Ouverture modale : `GET admin/xmlrpc.php?mode=popins-StatutBien-statutBienDispatcher&context=clos&idAnnonce=<id>&idMandat=`
  - **Sauvegarde** : `POST admin/xmlrpc.php` `mode=popins-StatutBien-statutBienDispatcher&context=validerClos&idAnnonce=<id>` + champs form.
  - Flip statut annonce (séparé) : `mode=upval&id=<annonce>&champ=status&val=<2..6>&idReporting=<id>`.
- **Champs du formulaire `PopinClos`** :
  - `id_mandat` (SELECT) — **cible le mandat via son ID INTERNE** (ex. 9887/553), PAS le numéro.
  - `choiceBags` (motif racine) ∈ `choiceNonRenouv` | `choiceVendu` | `choiceAutre`
    - `choiceNonRenouv` ∈ `concurence` | `vendre_seule` | `noReason`
    - `choiceVendu` ∈ `agence` | `confrere` | `proprietaire` (+ `confrereId`/`confrereTxt`/`confrerePrice` ou `propPrice`)
    - `choiceAutre` → `autreTxt` (libre)
  - hidden `alreadySold` (0/1).
  - Deux boutons : **« Enregistrer & laisser actif »** (clos non archivé) et « Enregistrer & archiver ».
- **Effets vérifiés** : la clôture pose un marqueur **« Clos » par mandat** (option devient « … - Clos »). **Irréversible** : réactiver l'annonce (statut BIEN ACTIF) ne dé-clôture PAS le mandat.

## Déclencheurs validés (spec user)

| Déclencheur | Mandat | Annonce |
|---|---|---|
| Modale « changer le statut » → **Clos** (enrichie des motifs) | Clos | Clos (laisser actif) |
| Même modale → **Vendu** | Clos (motif vendu) | Vendu |
| **Bouton clôture** rubrique Mandat, **Admin uniquement** | Clos | Clos |
| **Annulation acceptée** | Clos | Clos |
| **Échu** | reste « en cours » | inchangé → **alerte négo** (rubrique Mandat + cloche) |

## Arbitrages verrouillés (2026-07-30)

1. **« Clos » app = bouton « laisser actif » uniquement** (clos non archivé). Pas de case « archiver aussi ».
2. **Alerte échu générée au run quotidien worker.**
3. **Colonne « Statut du Mandat » placée juste avant « État »** dans le registre — attention aux largeurs (`registre-v2.css`).
4. **Cible `id_mandat` = mandat courant par défaut** ; choix explicite seulement dans la modale multi-mandat.
5. Dérivation statut mandat : **Clos** (`mandat_date_cloture` non vide) → **Échu** (`mandat_date_fin` < today) → **Actif**.

## Sous-lots

### A0 — Verrouiller le format exact `validerClos` *(lecture seule, sans coder)*
Confirmer la sérialisation exacte (noms/valeurs des params du POST `validerClos`) et si un appel init `context=clos` est requis avant, en lisant la fonction de build de `labs/biens/labs_popinStatutBien.js`. **Livrable : tableau param→valeur définitif.**

### A1 — Worker : clôture réelle ciblée — `Console/console_job_worker.js`
- Réécrire `submitHektorClosedStatus` sur `popins-StatutBien-statutBienDispatcher` / `context=validerClos`.
- Résoudre `id_mandat` via `AnnonceById.mandats` (mandat courant par défaut / id passé par la modale multi-mandat).
- Mapper motif app → `choiceBags`/sous-motif/`autreTxt`/confrere/prop/`alreadySold`, bouton « laisser actif ».
- Chemin « Vendu » : après `submitHektorTransactionStatus(sold)`, enchaîner `validerClos` motif *vendu* sur le mandat courant.
- Étendre le payload du job `change_hektor_annonce_status` (additif) + enqueue read-through après succès.
- *Déploiement : restart worker (user). Test : job clôture sur mandat cobaye.*

### A2 — Pipeline : remonter `date_cloture` au registre (D6) — `phase2/sync/export_app_payload.py` + vue + `types.ts`
- Ajouter `mandat_date_cloture` au dict racine des lignes registre (~1451) + colonne `app_registre_mandats_current` + champ `MandatRecord`.
- Vérifier peuplement via read-through / refresh_views après clôture.

### A7 — Registre : colonne « Statut du Mandat » — `MandatRegisterScreen` (App.tsx ~20267/20399 desktop, ~29732 mobile) + `registre-v2.css`
- Nouvelle dérivation `mandatStatut(item)` (Clos→Échu→Actif), distincte de `mandateLifecycleState`.
- Colonne **juste avant « État »** ; ajuster largeurs sans casser la mise en page.
- Source `mandat_date_cloture` racine (après A2) ; fallback parse JSON avant.

### A3 — Front : modale « changer le statut » enrichie — `App.tsx` `openStatusChangeModal` ~14164 / submit ~14273
- Ajouter sélecteur mandat (si multi-mandat), motif (`choiceBags`+sous-motifs), `autreTxt`, confrere/prop.
- « Clos » → job closure (laisser actif). « Vendu » → vente + clôture (chaînée A1).
- Garde-fou confirmation (irréversible). Derrière flag.

### A4 — Front : bouton clôture Admin (rubrique Mandat)
- Visible si `isAdmin` → même flux de clôture. Même flag.

### A5 — Annulation acceptée → clôture réelle — `handleUpdateDiffusionRequest` ~14420 (branche ~14433)
- À l'acceptation d'une `demande_annulation_mandat` : en plus de dévalider+dépublier, enqueue le job closure. Garde-fou + flag.

### A6 — Alerte « mandat échu » — run quotidien worker + couche `app_alert`/notif
- Détecter mandats échus (fin < today, non clos, courant) → alerte idempotente au négo (« demander l'annulation ou refaire un mandat »), visible rubrique Mandat + cloche.

## Modèle « issue de cycle » (ajouté 2026-07-30 — pont Lot A ↔ Lot B)

Constat : une annonce enchaîne plusieurs cycles de mandat, donc `statut_annonce` (scalaire écrasé) ne peut PAS servir à qualifier l'issue d'un cycle. Le stage terminal doit se dériver **par cycle** :
```
issueCycle(cycle) =
   Vendu     si une Vente (affaire) est rattachée au mandat de ce cycle
   sinon Clos    si mandat_date_cloture posée sur ce mandat
   sinon Échu    si mandat_date_fin < aujourd'hui
   sinon En cours
```
Asymétrie actuelle du cockpit : Offre/Compromis viennent de l'affaire (`hasOffreAchatEnCours`/`hasCompromisEnCours`, api.ts:1355/1378) MAIS « Vendu » venait de `statut_annonce` (regex `/vendu|vente|clos/`) — et amalgamait `clos`.

**FAIT (cockpit, cycle COURANT)** : split `pVendu` vs `pClos` (App.tsx ~22171), stage `clos` dédié (« Mandat clos », ≠ « Vendu »), badge VIE DU MANDAT « Clos », `ckPhase` terminal. `pVendu`=/vendu|vente/ ; `pClos`=`mandat_date_cloture` (courant) ou statut clos/clôtur. Le déclencheur de statut reste visible en `clos`/`vendu` (condition `ckStage !== 'archive'`) → réouverture possible.

**RESTE (Lot B) : Vendu PAR cycle (cycles passés inclus)** — aujourd'hui l'affaire (`offre_/compromis_/vente_id`) est un scalaire unique écrasé au re-mandatement. Il faut **remonter les affaires par mandat** depuis Hektor (transactions rattachées à `mandat`/`idMandat`). Investigation préalable : ce que Hektor expose par mandat (`AnnonceById.mandats` ou endpoint affaires dédié). = Mécanique ② du Lot B. Ensuite : brancher `issueCycle` complet sur cockpit + registre + VIE DU MANDAT (plus jamais `statut_annonce`).

## Ordre de livraison
**A0 → A1 + A2 → A7 → [cockpit clos-split cycle courant ✅] → A3 → A4 → A5 → A6 → Lot B (affaires par mandat → issueCycle complet).**
