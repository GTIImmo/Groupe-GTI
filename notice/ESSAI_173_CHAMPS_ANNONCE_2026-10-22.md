# Essai des 173 champs d'une annonce — champ par champ — 22/10/2026

> Chantier ⑧ · pièce 2. Source de vérité : la fiche de l'app (`draftAnnonceWizardGroups`, App.tsx:1414-1696, **173 champs distincts**).
> L'essai : l'estimation **10000006 / 63330** (maison, Firminy, PEREIRA), créée par l'écran le 21/10 à 23:52. Photo de la naissance : table `essai_8a2b_naissance_20261021`. Retour : la fiche relue à 23:55.
> Le lot : les **500 annonces ACTIVES les plus récentes** (`statut_annonce = 'Actif'`, non archivées, avec un numéro Hektor), lues comme l'écran les lit (noms à plat, puis les 11 groupes bruts). « rempli » = non vide ; « utile » = ni `0`, ni `NON`, ni une date nulle. ⚠ Le chauffage est lu par l'écran dans une AUTRE clé (`chauffage_console_json`) : ses 0 ici ne veulent pas dire « absent ». Lecture seule, 22/10.

## 1. Ce que j'ai rempli : **116 champs envoyés**, 57 non envoyés

| pourquoi pas envoyé | nb | champs |
|---|---|---|
| fabriqué par Hektor | 3 | `NO_DOSSIER`, `dateenr`, `diffusable` |
| pas proposé pour une MAISON (filtre par type de bien) | 24 | `immeuble`, `floorState`, `ETAGE`, `DERNIER_ETAGE`, `BALCON`, `NB_BALCON`, `SURFACE_BALCON`, `RESIDENCE`, `TYPE_RESIDENCE`, `ASCENSEUR`, `gardien`, `cable`, `syndic`, `diag_loi_carrez`, `diag_loi_carrez_date`, `diag_loi_carrez_commentaire`, `clearing`, `copropriete`, `copropriete_lot`, `copropriete_nb_lot`, `copropriete_quote_part`, `montant_fonds_travaux`, `copropriete_plan_sauvegarde`, `copropriete_statut_syndicat` |
| masqué : piscine = NON | 8 | `PISCINE_TYPE`, `PISCINE_NATURE`, `PISCINE_DIMENSIONS`, `PISCINE_TRAITEMENT`, `PISCINE_CHAUFFEE`, `PISCINE_COUVERTE`, `POOL_HOUSE`, `PISCINE_DETAILS` |
| pas proposé pour une maison (TERRAIN seulement) | 7 | `terrain_constructible`, `terrain_surface_constructible`, `terrain_viabilise`, `terrain_raccordement_eau`, `terrain_raccordement_gaz`, `terrain_raccordement_electricite`, `terrain_raccordement_telephone` |
| proposé, laissé à sa valeur par DÉFAUT -> pas envoyé | 3 | `formatChauff`, `typeChauff`, `energieChauff` |
| proposé, laissé vide par moi (contradictoire avec un DPE saisi) | 3 | `dpe_non_concerne`, `dpe_vierge`, `isDpeAltitude` |
| masqué : honoraires vendeur = NON | 3 | `_tauxHonoraire3`, `_pourcentHonoraire3`, `_detailHonoraire3` |
| proposé, laissé vide par moi | 1 | `masque` |
| pas proposé pour une VENTE (location) | 5 | `TAXE_HABITATION`, `Loc_EstimationLoyer`, `Loc_ChargeLocative`, `Loc_RendementBrut`, `Loc_Occupation` |

## 2. Ce qui n'est pas revenu de Hektor : **10** sur 116

- `TRANSPORT` — Transport *(console seule)*
- `PROXIMITE` — Proximite *(console seule)*
- `ENVIRONNEMENT` — Environnement *(console seule)*
- `Particularites` — Particularites *(l'API rend son groupe vide)*
- `diagnostiqueur` — Diagnostiqueur *(console seule)*
- `_selecterHonoraires2` — Honoraires acquereur *(console seule)*
- `_tauxHonoraire2` — Montant honoraires acquereur *(console seule)*
- `_pourcentHonoraire2` — Pourcentage honoraires acquereur *(console seule)*
- `_detailHonoraire2` — Detail honoraires acquereur *(console seule)*
- `_selecterHonoraires3` — Honoraires vendeur *(console seule)*

Autres écarts : **11 dates** revenues sous la forme aaaa-mm-jj (même date) · `latitude`, `longitude`, `corps` (coordonnées : la BAN, par nous ; le texte : remplacé par la Description).

## 3. Le lot de 500 annonces actives : **23 champs vides sur les 500**

`immeuble`, `TRANSPORT`, `PROXIMITE`, `ENVIRONNEMENT`, `Particularites`, `formatChauff`, `typeChauff`, `energieChauff`, `diagnostiqueur`, `syndic`, `diag_termites_commentaire`, `_selecterHonoraires2`, `_tauxHonoraire2`, `_pourcentHonoraire2`, `_detailHonoraire2`, `_selecterHonoraires3`, `_tauxHonoraire3`, `_pourcentHonoraire3`, `_detailHonoraire3`, `Loc_EstimationLoyer`, `Loc_ChargeLocative`, `Loc_RendementBrut`, `Loc_Occupation`

### 3 bis. Les 23 vides du lot, expliqués (mesuré le 22/10 sur les mêmes 500)

| champs | combien | pourquoi | ce que le lot a AILLEURS |
|---|---|---|---|
| secteur `immeuble` `TRANSPORT` `PROXIMITE` `ENVIRONNEMENT` · `diagnostiqueur` `syndic` · honoraires ×8 · location ×4 | **18** | **console seule** : l'API ne les donne jamais | le bloc `secteur_console_json` existe pour **47 / 500** — affiché dans un encart à part (App.tsx:31357), **pas** dans la rubrique |
| chauffage `formatChauff` `typeChauff` `energieChauff` | 3 | lu par l'écran dans une **autre clé** | `chauffage_console_json` rempli pour **311 / 500** (run de nuit) |
| `Particularites` | 1 | ⚠ l'API le rend dans un groupe **liste** `particularites` (`[{id, name: "Investissement"}]`), que la rubrique ne lit pas (elle lit les `props` de 11 groupes) | présent pour **7 / 500** ; pour 63330 le groupe revient **vide** — envoyé par le worker ou non : **non vérifié** |
| `diag_termites_commentaire` | 1 | simplement jamais rempli sur ces 500 | — |

## 4. Le tableau complet

| # | nom Hektor | libellé | rubrique | essai : envoi | gardé à la naissance | essai : retour | lot : rempli /500 | lot : utile /500 | d'où il revient |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `prix` | Prix public | 1. Offre | envoyé | oui | revenu identique | 477 | 419 | API |
| 2 | `PRIXNETVENDEUR` | Prix net vendeur | 1. Offre | envoyé | oui | revenu identique | 477 | 357 | API |
| 3 | `surfappart` | Surface habitable | 1. Offre | envoyé | oui | revenu identique | 500 | 453 | API |
| 4 | `surfterrain` | Surface terrain | 1. Offre | envoyé | oui | revenu identique | 496 | 269 | API |
| 5 | `SURFACE_GARAGE` | Surface garage | 1. Offre | envoyé | oui | revenu identique | 260 | 83 | API |
| 6 | `nbpieces` | Pieces | 1. Offre | envoyé | oui | revenu identique | 409 | 367 | API |
| 7 | `NB_CHAMBRES` | Chambres | 1. Offre | envoyé | oui | revenu identique | 395 | 343 | API |
| 8 | `NB_NIVEAUX` | Niveaux | 1. Offre | envoyé | oui | revenu identique | 409 | 254 | API |
| 9 | `JARDIN-` | Jardin | 1. Offre | envoyé | oui | revenu identique | 185 | 151 | API |
| 10 | `PISCINE-` | Piscine | 1. Offre | envoyé | oui | revenu identique | 128 | 18 | API |
| 11 | `GARAGE_BOX` | Garages | 1. Offre | envoyé | oui | revenu identique | 409 | 142 | API |
| 12 | `EXPOSITION` | Exposition | 1. Offre | envoyé | oui | revenu identique | 187 | 187 | API |
| 13 | `vuee` | Vue | 1. Offre | envoyé | oui | revenu identique | 89 | 89 | API |
| 14 | `NO_DOSSIER` | Numero dossier | 1. Offre | non envoyé — fabriqué par Hektor |  |  | 497 | 497 | API |
| 15 | `dateenr` | Date creation | 1. Offre | non envoyé — fabriqué par Hektor |  |  | 500 | 500 | API |
| 16 | `codepublique` | Code postal public | 3. Secteur | envoyé | oui | revenu identique | 488 | 488 | API |
| 17 | `villepublique` | Ville publique | 3. Secteur | envoyé | oui | revenu identique | 488 | 488 | API |
| 18 | `adresse` | Adresse privée (rue) | 3. Secteur | envoyé | oui | revenu identique | 485 | 485 | API |
| 19 | `villeprivee` | Commune privée | 3. Secteur | envoyé | oui | revenu identique | 483 | 483 | API |
| 20 | `codeprive` | Code postal privé | 3. Secteur | envoyé | oui | revenu identique | 488 | 488 | API |
| 21 | `immeuble` | Immeuble | 3. Secteur | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 0 | 0 | console seule |
| 22 | `TRANSPORT` | Transport | 3. Secteur | envoyé | oui | ⚠ **PAS REVENU** | 0 | 0 | console seule |
| 23 | `PROXIMITE` | Proximite | 3. Secteur | envoyé | oui | ⚠ **PAS REVENU** | 0 | 0 | console seule |
| 24 | `ENVIRONNEMENT` | Environnement | 3. Secteur | envoyé | oui | ⚠ **PAS REVENU** | 0 | 0 | console seule |
| 25 | `latitude` | Latitude | 3. Secteur | envoyé | oui | recalculé (BAN, par nous) : 45.397060000 | 500 | 485 | API |
| 26 | `longitude` | Longitude | 3. Secteur | envoyé | oui | recalculé (BAN, par nous) : 4.292822000 | 500 | 485 | API |
| 27 | `Particularites` | Particularites | 5. Détails · Intérieur | envoyé | oui | ⚠ **PAS REVENU** | 0 | 0 | API |
| 28 | `NB_SDB` | Salles de bain | 5. Détails · Intérieur | envoyé | oui | revenu identique | 409 | 161 | API |
| 29 | `NB_SE` | Salles d'eau | 5. Détails · Intérieur | envoyé | oui | revenu identique | 409 | 195 | API |
| 30 | `NB_WC` | WC | 5. Détails · Intérieur | envoyé | oui | revenu identique | 409 | 295 | API |
| 31 | `SURF_CARREZ` | Surface Carrez | 5. Détails · Intérieur | envoyé | oui | revenu identique | 409 | 77 | API |
| 32 | `SURF_SEJOUR` | Surface sejour | 5. Détails · Intérieur | envoyé | oui | revenu identique | 409 | 148 | API |
| 33 | `CUISINE` | Cuisine | 5. Détails · Intérieur | envoyé | oui | revenu identique | 170 | 170 | API |
| 34 | `CUISINE_EQUIPEMENT` | Equipement cuisine | 5. Détails · Intérieur | envoyé | oui | revenu identique | 139 | 139 | API |
| 35 | `MURS_MITOYENS` | Murs mitoyens | 5. Détails · Extérieur & annexes | envoyé | oui | revenu identique | 110 | 38 | API |
| 36 | `floorState` | Indication etage | 5. Détails · Extérieur & annexes | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 54 | 54 | API |
| 37 | `ETAGE` | Etage | 5. Détails · Extérieur & annexes | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 125 | 77 | API |
| 38 | `DERNIER_ETAGE` | Dernier etage | 5. Détails · Extérieur & annexes | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 26 | 14 | API |
| 39 | `NB_ETAGES` | Nombre etages | 5. Détails · Extérieur & annexes | envoyé | oui | revenu identique | 384 | 36 | API |
| 40 | `CAVE` | Cave | 5. Détails · Extérieur & annexes | envoyé | oui | revenu identique | 161 | 136 | API |
| 41 | `SURFACE_CAVE` | Surface cave | 5. Détails · Extérieur & annexes | envoyé | oui | revenu identique | 113 | 28 | API |
| 42 | `BALCON` | Balcon | 5. Détails · Extérieur & annexes | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 84 | 46 | API |
| 43 | `NB_BALCON` | Nombre balcons | 5. Détails · Extérieur & annexes | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 409 | 21 | API |
| 44 | `SURFACE_BALCON` | Surface balcon | 5. Détails · Extérieur & annexes | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 242 | 30 | API |
| 45 | `TERRASSE` | Terrasse | 5. Détails · Extérieur & annexes | envoyé | oui | revenu identique | 152 | 108 | API |
| 46 | `NB_TERRASSE` | Nombre terrasses | 5. Détails · Extérieur & annexes | envoyé | oui | revenu identique | 409 | 61 | API |
| 47 | `SURFACE_TERRASSE` | Surface terrasse | 5. Détails · Extérieur & annexes | envoyé | oui | revenu identique | 354 | 75 | API |
| 48 | `NB_PARK_INT` | Parking interieur | 5. Détails · Extérieur & annexes | envoyé | oui | revenu identique | 473 | 111 | API |
| 49 | `NB_PARK_EXT` | Parking exterieur | 5. Détails · Extérieur & annexes | envoyé | oui | revenu identique | 473 | 87 | API |
| 50 | `RESIDENCE` | Residence | 5. Détails · Extérieur & annexes | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 9 | 9 | API |
| 51 | `TYPE_RESIDENCE` | Type residence | 5. Détails · Extérieur & annexes | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 10 | 10 | API |
| 52 | `PISCINE_TYPE` | Type de piscine | 5. Détails · Piscine | non envoyé — masqué : piscine = NON |  |  | 11 | 11 | API |
| 53 | `PISCINE_NATURE` | Nature piscine | 5. Détails · Piscine | non envoyé — masqué : piscine = NON |  |  | 10 | 10 | API |
| 54 | `PISCINE_DIMENSIONS` | Dimensions piscine | 5. Détails · Piscine | non envoyé — masqué : piscine = NON |  |  | 228 | 0 | API |
| 55 | `PISCINE_TRAITEMENT` | Traitement piscine | 5. Détails · Piscine | non envoyé — masqué : piscine = NON |  |  | 3 | 3 | API |
| 56 | `PISCINE_CHAUFFEE` | Piscine chauffee | 5. Détails · Piscine | non envoyé — masqué : piscine = NON |  |  | 8 | 2 | API |
| 57 | `PISCINE_COUVERTE` | Piscine couverte | 5. Détails · Piscine | non envoyé — masqué : piscine = NON |  |  | 7 | 1 | API |
| 58 | `POOL_HOUSE` | Pool house | 5. Détails · Piscine | non envoyé — masqué : piscine = NON |  |  | 8 | 3 | API |
| 59 | `PISCINE_DETAILS` | Details piscine | 5. Détails · Piscine | non envoyé — masqué : piscine = NON |  |  | 8 | 8 | API |
| 60 | `SURFACE_JARDIN` | Surface jardin | 5. Détails · Terrain | envoyé | oui | revenu identique | 351 | 107 | API |
| 61 | `terrain_constructible` | Terrain constructible | 5. Détails · Terrain | non envoyé — pas proposé pour une maison (TERRAIN seulement) |  |  | 32 | 32 | API |
| 62 | `terrain_surface_constructible` | Surface constructible | 5. Détails · Terrain | non envoyé — pas proposé pour une maison (TERRAIN seulement) |  |  | 32 | 25 | API |
| 63 | `SHON` | SHON | 5. Détails · Terrain | envoyé | oui | revenu identique | 12 | 12 | API |
| 64 | `terrain_viabilise` | Terrain viabilise | 5. Détails · Terrain | non envoyé — pas proposé pour une maison (TERRAIN seulement) |  |  | 36 | 15 | API |
| 65 | `terrain_raccordement_eau` | Raccordement eau | 5. Détails · Terrain | non envoyé — pas proposé pour une maison (TERRAIN seulement) |  |  | 5 | 2 | API |
| 66 | `terrain_raccordement_gaz` | Raccordement gaz | 5. Détails · Terrain | non envoyé — pas proposé pour une maison (TERRAIN seulement) |  |  | 4 | 1 | API |
| 67 | `terrain_raccordement_electricite` | Raccordement electricite | 5. Détails · Terrain | non envoyé — pas proposé pour une maison (TERRAIN seulement) |  |  | 12 | 9 | API |
| 68 | `terrain_raccordement_telephone` | Raccordement telephone | 5. Détails · Terrain | non envoyé — pas proposé pour une maison (TERRAIN seulement) |  |  | 12 | 9 | API |
| 69 | `terrain_arbore` | Terrain arbore | 5. Détails · Terrain | envoyé | oui | revenu identique | 50 | 33 | API |
| 70 | `terrain_piscinable` | Terrain piscinable | 5. Détails · Terrain | envoyé | oui | revenu identique | 35 | 19 | API |
| 71 | `garantie_decennale` | Garantie decennale | 5. Détails · Construction récente | envoyé | oui | revenu identique | 12 | 7 | API |
| 72 | `assurance_dommages_ouvrage` | Assurance dommages-ouvrage | 5. Détails · Construction récente | envoyé | oui | revenu identique | 9 | 4 | API |
| 73 | `certificat_conformite` | Certificat de conformite | 5. Détails · Construction récente | envoyé | oui | revenu identique | 7 | 4 | API |
| 74 | `declaration_achevement_travaux` | Declaration achevement | 5. Détails · Construction récente | envoyé | oui | revenu identique | 8 | 4 | API |
| 75 | `formatChauff` | Format chauffage | 5. Détails · Équipements & confort | non envoyé — proposé, laissé à sa valeur par DÉFAUT -> pas envoyé |  |  | 0 | 0 | chauffage : run de nuit, autre clé |
| 76 | `typeChauff` | Type chauffage | 5. Détails · Équipements & confort | non envoyé — proposé, laissé à sa valeur par DÉFAUT -> pas envoyé |  |  | 0 | 0 | chauffage : run de nuit, autre clé |
| 77 | `energieChauff` | Energie chauffage | 5. Détails · Équipements & confort | non envoyé — proposé, laissé à sa valeur par DÉFAUT -> pas envoyé |  |  | 0 | 0 | chauffage : run de nuit, autre clé |
| 78 | `ASCENSEUR` | Ascenseur | 5. Détails · Équipements & confort | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 63 | 31 | API |
| 79 | `ACCES_HANDI` | Acces handicape | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 81 | 10 | API |
| 80 | `climatisation` | Climatisation | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 90 | 9 | API |
| 81 | `climatisationspec` | Specification climatisation | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 3 | 3 | API |
| 82 | `EAU` | Eau | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 105 | 105 | API |
| 83 | `ASSAINISSEMENT` | Assainissement | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 149 | 149 | API |
| 84 | `DISTRIBUTION_EAU` | Distribution eau | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 96 | 96 | API |
| 85 | `ENERGIE_EAU` | Energie eau | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 109 | 109 | API |
| 86 | `cheminee` | Cheminee | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 75 | 27 | API |
| 87 | `volets_elctriques` | Volets electriques | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 129 | 42 | API |
| 88 | `gardien` | Gardien | 5. Détails · Équipements & confort | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 25 | 1 | API |
| 89 | `double_vitrage` | Double vitrage | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 167 | 143 | API |
| 90 | `triple_vitrage` | Triple vitrage | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 59 | 1 | API |
| 91 | `cable` | Fibre optique | 5. Détails · Équipements & confort | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 69 | 48 | API |
| 92 | `porte_blindee` | Porte blindee | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 42 | 4 | API |
| 93 | `interphone` | Interphone | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 52 | 30 | API |
| 94 | `visiophone` | Visiophone | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 38 | 7 | API |
| 95 | `alarme` | Alarme | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 38 | 6 | API |
| 96 | `digicode` | Digicode | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 41 | 9 | API |
| 97 | `detecteur_fumee` | Detecteur fumee | 5. Détails · Équipements & confort | envoyé | oui | revenu identique | 41 | 21 | API |
| 98 | `ANNEE_CONS` | Annee construction | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 386 | 191 | API |
| 99 | `etat_exterieur` | Etat exterieur | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 52 | 52 | API |
| 100 | `etat_interieur` | Etat interieur | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 155 | 155 | API |
| 101 | `dpe_date` | Date DPE | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu, autre forme (aaaa-mm-jj) | 500 | 295 | API |
| 102 | `dpe_non_concerne` | DPE non concerne | 5. Détails · Diagnostics & énergie | non envoyé — proposé, laissé vide par moi (contradictoire avec un DPE saisi) |  |  | 497 | 41 | API |
| 103 | `dpe_vierge` | DPE vierge | 5. Détails · Diagnostics & énergie | non envoyé — proposé, laissé vide par moi (contradictoire avec un DPE saisi) |  |  | 497 | 7 | API |
| 104 | `isDpeAltitude` | DPE altitude | 5. Détails · Diagnostics & énergie | non envoyé — proposé, laissé vide par moi (contradictoire avec un DPE saisi) |  |  | 436 | 30 | API |
| 105 | `dpe_cons` | DPE consommation | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 349 | 255 | API |
| 106 | `dpe_ges` | GES | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 349 | 255 | API |
| 107 | `valeurEnergieFinale` | Energie finale | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 297 | 44 | API |
| 108 | `dpe_couts_min` | Cout energie min | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 377 | 234 | API |
| 109 | `dpe_couts_max` | Cout energie max | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 377 | 233 | API |
| 110 | `dpe_annee_reference` | Annee reference DPE | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 377 | 377 | API |
| 111 | `diagnostiqueur` | Diagnostiqueur | 5. Détails · Diagnostics & énergie | envoyé | oui | ⚠ **PAS REVENU** | 0 | 0 | console seule |
| 112 | `syndic` | Syndic | 5. Détails · Diagnostics & énergie | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 0 | 0 | console seule |
| 113 | `diag_termites` | Termites | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 17 | 0 | API |
| 114 | `diag_termites_date` | Date termites | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu, autre forme (aaaa-mm-jj) | 436 | 0 | API |
| 115 | `diag_termites_commentaire` | Commentaire termites | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 0 | 0 | API |
| 116 | `diag_amiante` | Amiante | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 25 | 20 | API |
| 117 | `diag_amiante_date` | Date amiante | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu, autre forme (aaaa-mm-jj) | 436 | 17 | API |
| 118 | `diag_amiante_commentaire` | Commentaire amiante | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 13 | 13 | API |
| 119 | `diag_electrique` | Electrique | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 24 | 20 | API |
| 120 | `diag_electrique_date` | Date electrique | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu, autre forme (aaaa-mm-jj) | 436 | 15 | API |
| 121 | `diag_electrique_commentaire` | Commentaire electrique | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 11 | 11 | API |
| 122 | `diag_loi_carrez` | Loi Carrez | 5. Détails · Diagnostics & énergie | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 6 | 6 | API |
| 123 | `diag_loi_carrez_date` | Date loi Carrez | 5. Détails · Diagnostics & énergie | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 436 | 4 | API |
| 124 | `diag_loi_carrez_commentaire` | Commentaire loi Carrez | 5. Détails · Diagnostics & énergie | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 4 | 4 | API |
| 125 | `diag_risques_nat_tech` | Risques naturels | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 27 | 26 | API |
| 126 | `diag_risques_nat_tech_date` | Date risques | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu, autre forme (aaaa-mm-jj) | 500 | 18 | API |
| 127 | `diag_risques_nat_tech_commentaire` | Commentaire risques | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 1 | 1 | API |
| 128 | `diag_plomb` | Plomb | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 22 | 9 | API |
| 129 | `diag_plomb_date` | Date plomb | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu, autre forme (aaaa-mm-jj) | 436 | 7 | API |
| 130 | `diag_plomb_commentaire` | Commentaire plomb | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 5 | 5 | API |
| 131 | `diag_gaz` | Gaz | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 22 | 8 | API |
| 132 | `diag_gaz_date` | Date gaz | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu, autre forme (aaaa-mm-jj) | 436 | 4 | API |
| 133 | `diag_gaz_commentaire` | Commentaire gaz | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 2 | 2 | API |
| 134 | `diag_assainissement` | Assainissement diag. | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 20 | 13 | API |
| 135 | `diag_assainissement_date` | Date assainissement | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu, autre forme (aaaa-mm-jj) | 436 | 2 | API |
| 136 | `diag_assainissement_commentaire` | Commentaire assainissement | 5. Détails · Diagnostics & énergie | envoyé | oui | revenu identique | 6 | 6 | API |
| 137 | `clearing` | Clearing | 5. Détails · Diagnostics & énergie | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 16 | 2 | API |
| 138 | `copropriete` | Copropriete | 5. Détails · Copropriété | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 480 | 84 | API |
| 139 | `copropriete_lot` | Lot copropriete | 5. Détails · Copropriété | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 45 | 43 | API |
| 140 | `copropriete_nb_lot` | Nombre lots | 5. Détails · Copropriété | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 478 | 84 | API |
| 141 | `copropriete_quote_part` | Quote-part | 5. Détails · Copropriété | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 271 | 62 | API |
| 142 | `montant_fonds_travaux` | Fonds travaux | 5. Détails · Copropriété | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 267 | 5 | API |
| 143 | `copropriete_plan_sauvegarde` | Plan sauvegarde | 5. Détails · Copropriété | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 14 | 0 | API |
| 144 | `copropriete_statut_syndicat` | Statut syndicat | 5. Détails · Copropriété | non envoyé — pas proposé pour une MAISON (filtre par type de bien) |  |  | 52 | 52 | API |
| 145 | `DISPO` | Disponible | 5. Détails · Disponibilité & visite | envoyé | oui | revenu identique | 27 | 24 | API |
| 146 | `DATE_LIBER` | Date liberation | 5. Détails · Disponibilité & visite | envoyé | oui | revenu, autre forme (aaaa-mm-jj) | 500 | 1 | API |
| 147 | `DATE_DISPO` | Date disponibilite | 5. Détails · Disponibilité & visite | envoyé | oui | revenu, autre forme (aaaa-mm-jj) | 500 | 4 | API |
| 148 | `CLES` | Cles | 5. Détails · Disponibilité & visite | envoyé | oui | revenu identique | 96 | 96 | API |
| 149 | `moyens_visite` | Moyens visite | 5. Détails · Disponibilité & visite | envoyé | oui | revenu identique | 90 | 90 | API |
| 150 | `_selecterHonoraires2` | Honoraires acquereur | 6. Mandat / Prix | envoyé | oui | ⚠ **PAS REVENU** | 0 | 0 | console seule |
| 151 | `_tauxHonoraire2` | Montant honoraires acquereur | 6. Mandat / Prix | envoyé | oui | ⚠ **PAS REVENU** | 0 | 0 | console seule |
| 152 | `_pourcentHonoraire2` | Pourcentage honoraires acquereur | 6. Mandat / Prix | envoyé | oui | ⚠ **PAS REVENU** | 0 | 0 | console seule |
| 153 | `_detailHonoraire2` | Detail honoraires acquereur | 6. Mandat / Prix | envoyé | oui | ⚠ **PAS REVENU** | 0 | 0 | console seule |
| 154 | `_selecterHonoraires3` | Honoraires vendeur | 6. Mandat / Prix | envoyé | oui | ⚠ **PAS REVENU** | 0 | 0 | console seule |
| 155 | `_tauxHonoraire3` | Montant honoraires vendeur | 6. Mandat / Prix | non envoyé — masqué : honoraires vendeur = NON |  |  | 0 | 0 | console seule |
| 156 | `_pourcentHonoraire3` | Pourcentage honoraires vendeur | 6. Mandat / Prix | non envoyé — masqué : honoraires vendeur = NON |  |  | 0 | 0 | console seule |
| 157 | `_detailHonoraire3` | Detail honoraires vendeur | 6. Mandat / Prix | non envoyé — masqué : honoraires vendeur = NON |  |  | 0 | 0 | console seule |
| 158 | `masque` | Masquer le prix | 6. Mandat / Prix | non envoyé — proposé, laissé vide par moi |  |  | 126 | 2 | API |
| 159 | `ESTIMATION_MONTANT` | Montant estimation | 6. Mandat / Prix | envoyé | oui | revenu identique | 476 | 176 | API |
| 160 | `ESTIMATION_DATE` | Date estimation | 6. Mandat / Prix | envoyé | oui | revenu, autre forme (aaaa-mm-jj) | 476 | 48 | API |
| 161 | `TRAVAUX` | Travaux | 6. Mandat / Prix | envoyé | oui | revenu identique | 14 | 14 | API |
| 162 | `DEPOT_GARANTIE` | Depot garantie | 6. Mandat / Prix | envoyé | oui | revenu identique | 476 | 0 | API |
| 163 | `TAXE_HABITATION` | Taxe habitation | 6. Mandat / Prix | non envoyé — pas proposé pour une VENTE (location) |  |  | 477 | 3 | API |
| 164 | `TAXE_FONCIERE` | Taxe fonciere | 6. Mandat / Prix | envoyé | oui | revenu identique | 477 | 168 | API |
| 165 | `CHARGES` | Charges | 6. Mandat / Prix | envoyé | oui | revenu identique | 500 | 19 | API |
| 166 | `CHARGES_DETAIL` | Detail charges | 6. Mandat / Prix | envoyé | oui | revenu identique | 178 | 3 | API |
| 167 | `Loc_EstimationLoyer` | Estimation loyer | 6. Mandat / Prix | non envoyé — pas proposé pour une VENTE (location) |  |  | 0 | 0 | console seule |
| 168 | `Loc_ChargeLocative` | Charge locative | 6. Mandat / Prix | non envoyé — pas proposé pour une VENTE (location) |  |  | 0 | 0 | console seule |
| 169 | `Loc_RendementBrut` | Rendement brut | 6. Mandat / Prix | non envoyé — pas proposé pour une VENTE (location) |  |  | 0 | 0 | console seule |
| 170 | `Loc_Occupation` | Occupation locative | 6. Mandat / Prix | non envoyé — pas proposé pour une VENTE (location) |  |  | 0 | 0 | console seule |
| 171 | `diffusable` | Diffusable | 7. Diffusion | non envoyé — fabriqué par Hektor |  |  | 500 | 301 | API |
| 172 | `titre` | Titre annonce | 7. Diffusion | envoyé | oui | revenu identique | 356 | 356 | API |
| 173 | `corps` | Texte annonce | 7. Diffusion | envoyé | oui | ⚠ **REMPLACÉ** : « Belle maison familiale a… » | 373 | 373 | API |
