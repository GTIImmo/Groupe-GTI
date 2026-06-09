# Note groupes API detail vers Supabase - 2026-06-08

## Objectif

Exposer dans `detail_payload_json` les groupes deja recuperes par l'API Hektor `AnnonceById`, afin de distinguer clairement :

- les champs disponibles par API mais non indexes proprement dans l'app ;
- les vrais champs absents de l'API, a completer plus tard par extraction console.

Cette note ne couvre pas la creation d'un extracteur console.

## Modification

Le generateur `phase2/sync/export_app_payload.py` derive maintenant les blocs suivants depuis `detail_raw_json` :

- `ag_interieur_json`
- `ag_exterieur_json`
- `equipements_json`
- `diagnostiques_json`
- `terrain_json`
- `copropriete_json`
- `mandat_infofi_json`
- `mandat_mandatdispo_json`
- `organiser_visite_json`

Il reconstruit aussi les URL de vignettes DPE/GES depuis le groupe API `diagnostiques.props` :

- `dpe_image_url`
- `ges_image_url`
- `dpe_image_urls_json`

`terrain_json` et `copropriete_json` existaient deja. Ils sont conserves et seulement completes depuis `detail_raw_json` si la valeur existante est vide ou `null`.

Le type front `DossierDetailPayload` a ete aligne pour declarer ces nouvelles cles.

## Controle attendu

Apres push Supabase, verifier dans `app_dossier_detail_current.detail_payload_json` :

- presence de la cle dediee ;
- valeur `null` si le groupe API est absent ;
- JSON compact si le groupe API est present ;
- coherence avec le groupe correspondant dans `detail_raw_json`.

## Hors perimetre

Les donnees suivantes restent hors API ou incompletes par API et devront etre traitees separement, apres ce controle :

- chauffage detaille `chauffageExist...` ;
- contacts `diagnostiqueur` et `syndic` ;
- textes libres secteur `TRANSPORT`, `PROXIMITE`, `ENVIRONNEMENT`, `immeuble` ;
- details fins de composition des pieces ;
- diagnostics terrain absents de `AnnonceById` ;
- details formulaire honoraires non presents dans `honoraires_json`.

## Controle realise

Controle local :

- syntaxe Python OK sur `phase2/sync/export_app_payload.py` ;
- verification TypeScript OK avec `npx tsc --noEmit -p tsconfig.app.json --pretty false` ;
- generation en memoire du payload app sur 60 dossiers avec les nouvelles cles.

Push Supabase cible :

- annonces poussees : `62436`, `62418`, `62422` ;
- `details_upserted = 3` ;
- `deleted_dossiers = 0` ;
- aucun job console `pending` / `running` apres verification.

Relecture Supabase cible :

| annonce | ag_interieur | ag_exterieur | equipements | diagnostiques | terrain | copropriete | mandat_infofi | mandat_mandatdispo | organiser_visite |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 62418 | 11 | 12 | 9 | 21 | 1 | 2 | 11 | 4 | null |
| 62422 | 10 | 15 | null | 12 | 1 | null | 11 | 4 | null |
| 62436 | 13 | 19 | 20 | 38 | 1 | 6 | 13 | 4 | 2 |

Les comptes relus dans les nouvelles cles dediees sont identiques aux comptes des groupes correspondants dans `detail_raw_json`.

Controle local sur 60 dossiers :

| groupe dedie | rempli | vide |
| --- | ---: | ---: |
| `ag_interieur_json` | 52 | 8 |
| `ag_exterieur_json` | 60 | 0 |
| `equipements_json` | 12 | 48 |
| `diagnostiques_json` | 60 | 0 |
| `terrain_json` | 60 | 0 |
| `copropriete_json` | 60 | 0 |
| `mandat_infofi_json` | 60 | 0 |
| `mandat_mandatdispo_json` | 60 | 0 |
| `organiser_visite_json` | 24 | 36 |

Les vides constates correspondent a des groupes absents dans `detail_raw_json` pour les annonces concernees, pas a une perte introduite par le parser.
