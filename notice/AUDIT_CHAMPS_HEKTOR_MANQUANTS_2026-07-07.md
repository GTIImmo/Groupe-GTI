# Audit — champs Hektor manquants dans l'app / le patron / le scan

Date : 2026-07-07. Sources croisées :
- **Hektor (vérité)** : `Console/console_job_worker.js` → `WIZARD_FIELD_GROUPS` (tous les champs par groupe, terrain/copro/piscine inclus).
- **Scan OCR** : `backend/app/services/openai_listing_sheet_service.py` → `FIELD_KEYS`.
- **Patron** : `notice/PATRON_FICHE_SAISIE_draft_annonce_v1.html`.
- **App** : modale estimation `initialDraft` + wizard annonce.

La capture live du wizard n'a pas été nécessaire : le worker définit déjà toute la taxonomie.

---

## A) Manquants PARTOUT (ni scan, ni patron, ni app) — à créer de zéro

### A1. Bloc TERRAIN (groupe `terrain`) — 7 champs
Seul `surfterrain` (= "Surface terrain") est capté. Manquent :
- `terrain_constructible` (oui/non)
- `terrain_surface_constructible` (m²)
- `terrain_viabilise` (oui/non)
- `terrain_raccordement_eau` (oui/non)
- `terrain_raccordement_gaz` (oui/non)
- `terrain_raccordement_electricite` (oui/non)
- `terrain_raccordement_telephone` (oui/non)

### A2. Bloc DIAGNOSTIQUES (groupe `diagnostiques`) — gros bloc manquant
Le scan a DPE/GES/année/coûts. Manquent (chacun = présence + date + commentaire) :
- `diag_termites`, `diag_amiante`, `diag_electrique`, `diag_plomb`, `diag_gaz`,
  `diag_assainissement`, `diag_risques_nat_tech`, `diag_loi_carrez`
- + `diagnostiqueur`, `syndic`

### A3. Copropriété — 1 champ manquant au scan
- `copropriete_statut_syndicat` (procédure d'alerte / redressement / en cours / pas de procédure)
- (`copropriete_quote_part`, `montant_fonds_travaux`, `copropriete_lot`, plan sauvegarde : **déjà dans le scan** mais pas dans le patron — voir B)

### A4. Autres
- `SURFACE_JARDIN` (surface du jardin — le scan a jardin oui/non seulement)
- `climatisationspec` (précision clim)

### A5. Piscine = oui — CONFIRMÉ via capture live (wizard Maison, idtype=1)
Hektor révèle bien un **sous-bloc piscine complet**, absent **même du worker** :
- `PISCINE_TYPE`, `PISCINE_NATURE`, `PISCINE_DETAILS`, `PISCINE_DIMENSIONS`,
  `PISCINE_TRAITEMENT`, `POOL_HOUSE`, `PISCINE_CHAUFFEE`, `PISCINE_COUVERTE`

### A6. Autres champs découverts en live (absents même du worker → à ajouter au worker AUSSI)
- **Groupe `construction_recente`** (bien récent) — nouveau groupe entier :
  `garantie_decennale`, `assurance_dommages_ouvrage`, `certificat_conformite`,
  `declaration_achevement_travaux`
- **Terrain (extras)** : `SHON`, `terrain_arbore`, `terrain_piscinable`
- **Maison** : `PLAIN_PIED` (de plain-pied)
- **Diagnostiques** : `globalCondition` (état global)

> ⚠️ A5+A6 sont absents du worker `WIZARD_FIELD_GROUPS` → il faudra les ajouter là aussi
> (nouveau groupe `construction_recente`, champs piscine/terrain), pas seulement au front.

---

## B) Captés par le SCAN mais absents du PATRON / de la modale — à exposer

Le scan sait les lire (`FIELD_KEYS`) mais le patron n'a pas de case et/ou la modale ne les montre pas :
- **Balcon** : `balcony`, `balconyCount`, `balconySurface` (BALCON/NB_BALCON/SURFACE_BALCON)
- **Copropriété** : `coproQuotePart`, `coproWorksFund`, `coproLot`, `safeguardPlan` (plan sauvegarde)
- **Mitoyenneté** structurée : `partyWalls` (MURS_MITOYENS) — aujourd'hui noyé dans le texte libre
- **Résidence** : `residenceType` (TYPE_RESIDENCE)
- **Cave** : `cellarSurface` (SURFACE_CAVE)
- **Niveaux/étage** : `floorsCount` (NB_ETAGES), `topFloor` (DERNIER_ETAGE)
- **Équipements** : `disabledAccess` (ACCES_HANDI), `tripleGlazing`, `caretaker` (gardien),
  `smokeDetector` (détecteur fumée), `waterDistribution` (DISTRIBUTION_EAU), `waterEnergy` (ENERGIE_EAU)
- **Cuisine** : `kitchenEquipment` (CUISINE_EQUIPEMENT)
- **Visite** : `keys` (CLES), `availabilityDate`

---

## Plan d'implémentation (étapes suivantes)
1. **Scan/patron** (Tâche 3) : ajouter A1–A4 aux `FIELD_KEYS` + `_schema` + prompt `scan_fiche`, et
   ajouter les cases correspondantes au patron ; exposer B dans le patron. Relancer l'éval OCR.
2. **Workers/read-through/calque** (Tâche 2) : mapper les nouveaux champs (le worker connaît déjà les
   noms Hektor → surtout câbler front → payload → worker + read-through + calque optimiste).
3. **Modale ajouter/modifier + fiche détail** : afficher A+B.
