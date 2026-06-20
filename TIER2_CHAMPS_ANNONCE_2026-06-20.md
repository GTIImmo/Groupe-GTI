# Tier 2 — Liste des champs annonce éditables (référence)

_2026-06-20. Champs que le worker `update_hektor_annonce_fields` sait écrire dans Hektor (source : `HektorAnnonceUpdateFields` api.ts:5984 + groupes MEF worker). Colonnes "Supabase" = où écrire pour l'affichage optimiste instantané ; "Scoring" = déclenche le recompute rapprochement._

Légende Supabase : **COL** = colonne `app_dossier_current` · **JSON** = clé dans `app_dossier_detail_current.detail_payload_json`.

## Identité / textes
| Champ | Clé push (worker) | Supabase | Scoring | Groupe Hektor |
|---|---|---|---|---|
| Titre | `title` | JSON `texte_principal_titre` | – | principal_text |
| Description | `description` | JSON `texte_principal_html` | – | principal_text |
| Profil de bien | `propertyProfile` | (filtre champs) | – | — |
| Adresse | `address` | JSON `adresse_detail` | – | secteur |
| Code postal | `postalCode` | **COL `code_postal`** | ✅ | secteur |
| Ville | `city` | **COL `ville`** | – | secteur |
| Immeuble | `building` | JSON | – | secteur |
| Transports | `transport` | JSON | – | secteur |
| Proximité | `proximity` | JSON | – | secteur |
| Environnement | `environment` | JSON | – | secteur |
| Latitude | `latitude` | JSON `latitude_detail` | ✅ | secteur |
| Longitude | `longitude` | JSON `longitude_detail` | ✅ | secteur |

## Prix / financier (groupe mandat_infofi)
| Champ | Clé push | Supabase | Scoring |
|---|---|---|---|
| **Prix** | `price` | **COL `prix`** | ✅ |
| Prix net vendeur | `netSellerPrice` | JSON | – |
| Honoraires | `fees` | JSON | – |
| Charges (copro) | `coproCharges` | JSON | – |
| **Montant estimation** (estimations) | `ESTIMATION_MONTANT` | JSON `mandat_infofi_json` | – |

## Surfaces (ag_interieur / terrain / ag_exterieur)
| Champ | Clé push | Supabase | Scoring |
|---|---|---|---|
| Surface habitable | `surface` | JSON `surface` | ✅ |
| Surface Carrez | `carrezSurface` | JSON | – |
| Surface terrain | `landSurface` | JSON `surface_terrain_detail` | ✅ |
| Surface jardin | `gardenSurface` | JSON | – |
| Surface garage | `garageSurface` | JSON | – |

## Composition (ag_interieur)
| Champ | Clé push | Supabase | Scoring |
|---|---|---|---|
| Nb pièces | `roomCount` | JSON `nb_pieces` | ✅ |
| Nb chambres | `bedroomCount` | JSON `nb_chambres` | ✅ |
| Nb niveaux | `levelCount` | JSON | – |
| Nb SDB | `bathroomCount` | JSON | – |
| Nb salles d'eau | `showerRoomCount` | JSON | – |
| Nb WC | `wcCount` | JSON | – |
| Cuisine | `kitchen` | JSON | – |
| Exposition | `exposure` | JSON | – |
| Vue | `view` | JSON | – |
| État intérieur | `interiorState` | JSON | – |
| État extérieur | `exteriorState` | JSON | – |
| **Pièces détaillées** | `compositionPieces[]` | JSON | – |

## Extérieur (ag_exterieur)
| Champ | Clé push | Supabase | Scoring |
|---|---|---|---|
| Nb terrasses | `terraceCount` | JSON | ✅ (terrasse oui/non) |
| Nb garages/box | `garageCount` | JSON `garage_box_detail` | ✅ (garage oui/non) |
| Parkings intérieurs | `parkingInsideCount` | JSON | – |
| Parkings extérieurs | `parkingOutsideCount` | JSON | – |
| Jardin (oui/non) | `garden` | JSON | – |
| Piscine (oui/non) | `pool` | JSON | – |

## Diagnostics (diagnostiques)
| Champ | Clé push | Supabase | Scoring |
|---|---|---|---|
| DPE (classe énergie) | `dpeValue` | JSON `diagnostiques_json` | – |
| GES (classe) | `gesValue` | JSON `diagnostiques_json` | – |
| Année construction | `constructionYear` | JSON | – |
| Commentaire risques | `diagnosticRiskComment` | JSON | – |
| Note diagnostic | `diagnosticNote` | JSON | – |

## Copropriété (copropriete)
| Champ | Clé push | Supabase | Scoring |
|---|---|---|---|
| Nb lots | `coproLots` | JSON `copropriete_json` | – |
| Quote-part | `coproQuotePart` | JSON | – |
| Fonds travaux | `coproWorksFund` | JSON | – |

## Mandat (mandat_infofi)
| Champ | Clé push | Supabase | Scoring |
|---|---|---|---|
| N° mandat | `mandateNumber` | **COL `numero_mandat`** | – |
| Type mandat | `mandateType` | JSON `mandat_type` | – |
| Date début | `mandateStartDate` | JSON `mandat_date_debut` | – |
| Date fin | `mandateEndDate` | JSON `mandat_date_fin` | – |

---

## Synthèse pour la RPC générique
- **Champs qui déclenchent le recompute** (lus par `app_dossier_match_payload`) : `prix`, `code_postal`, `latitude`, `longitude`, `surface`, `roomCount`, `bedroomCount`, `landSurface`, `garageCount`, `terraceCount`, `type_bien`. → recompute uniquement si l'un d'eux change.
- **Écriture optimiste Supabase** : 3 colonnes directes (`prix`, `ville`, `code_postal`, `numero_mandat`) ; **tout le reste = patch du blob JSON** `detail_payload_json`.
- **Push Hektor** : `push_fields` = TOUS les champs édités (clés push ci-dessus) → le worker écrit tout via les groupes MEF.
- **Estimations** : la valeur = `ESTIMATION_MONTANT` (JSON), pas de scoring.
