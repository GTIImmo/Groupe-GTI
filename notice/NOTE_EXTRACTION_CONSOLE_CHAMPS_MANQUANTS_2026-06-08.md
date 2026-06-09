# Note extraction console champs manquants - 2026-06-08

## Objectif

Completer les donnees que l'API Hektor `AnnonceById` ne renvoie pas, sans remplacer la source API.

La console Hektor est utilisee uniquement pour les champs confirmes absents ou incomplets dans l'API :

- textes secteur : `immeuble`, `TRANSPORT`, `PROXIMITE`, `ENVIRONNEMENT` ;
- chauffage detaille ;
- contacts diagnostics : `diagnostiqueur`, `syndic` ;
- details honoraires du formulaire mandat/prix ;
- champs location/rendement si presents ;
- indice de disponibilite des details fins de composition des pieces.

Les vignettes DPE/GES ne sont plus considerees comme un champ manquant console : elles sont maintenant reconstruites depuis les donnees diagnostics renvoyees par l'API Hektor `AnnonceById` dans `phase2/sync/export_app_payload.py`. La lecture console peut encore servir de controle/fallback, mais la source normale du payload app est l'API.

Pour le chauffage detaille, un extracteur plus leger existe maintenant : `phase2/sync/sync_hektor_chauffages.py`. Il lit uniquement le groupe Hektor `equipements` et alimente `chauffage_console_json`. Il doit etre privilegie pour le quotidien et les gros rattrapages chauffage. Le present extracteur console global reste reserve aux controles complets et aux autres champs manquants.

Les endpoints documents ne sont pas appeles.

## Stockage local

Le cache local est cree dans `data/hektor.sqlite` :

`hektor_annonce_console_detail`

Colonnes principales :

- `hektor_annonce_id`
- `status`
- `console_payload_json`
- `source_hash`
- `detail_synced_at`
- `extracted_at`
- `storage_state_path`
- `forbidden403`
- `error`

## Emplacement Supabase

Aucune migration Supabase n'est necessaire pour ce premier niveau.

Les donnees sont poussees dans l'emplacement existant :

`app_dossier_detail_current.detail_payload_json`

Nouvelles cles exposees dans le JSON detail :

- `console_missing_fields_json`
- `console_missing_fields_extracted_at`
- `console_missing_fields_status`
- `secteur_console_json`
- `chauffage_console_json`
- `diagnostics_contacts_console_json`
- `honoraires_detail_console_json`
- `location_rendement_console_json`
- `pieces_detail_console_json`
- `dpe_image_url`
- `ges_image_url`
- `dpe_image_urls_json`

Les deux vignettes DPE/GES ont donc un emplacement dedie dans le payload Supabase, alimente en priorite par l'API Hektor :

- `dpe_image_url`
- `ges_image_url`

Les memes cles sont aussi injectees dans les details temporaires sur demande :

- `app_historical_annonce_detail_cache.detail_payload_json.detail`
- `app_archive_annonce_detail_cache.detail_payload_json.detail`

## Run quotidien

`run_full_pipeline.ps1` garde l'extraction console complete disponible, mais ne la lance plus par defaut dans le quotidien.

L'objectif est de conserver ce travail comme outil de controle/rattrapage sans ralentir le run courant et sans multiplier les lectures console Hektor.

Pour l'activer volontairement dans le pipeline, utiliser :

`-RunConsoleMissingFields`

Le script appele reste :

`phase2/sync/sync_console_missing_fields.py`

Quand l'etape est activee :

- maximum 25 annonces par defaut ;
- scope extraction console `all` : toutes les annonces locales de `phase2.app_view_generale` peuvent etre mises en cache console ;
- cache rejoue si absent, en erreur, modifie cote API, ou plus vieux que 30 jours ;
- verification des jobs console `pending/running` avant d'appeler Hektor ;
- stop immediat si Hektor renvoie un vrai 403 ;
- une erreur non-403 est stockee en cache et ne bloque pas le pipeline ;
- les erreurs recentes ne sont pas rejouees avant expiration du cache, sauf `--force` ;
- pas d'appel documents.
- session Playwright par defaut : `Console/sessions/storage_state_admin.json`.

Parametre de securite conserve pour forcer la desactivation meme si `-RunConsoleMissingFields` est donne :

`-SkipConsoleMissingFields`

Parametre pour revenir a l'ancien scope limite aux annonces courantes de l'app :

`-ConsoleMissingFieldsAnnonceScope current`

Important : ce scope concerne seulement la recuperation console locale. Le push Supabase/app reste filtre par les annonces courantes :

- non archivees ;
- statut `Actif`, `Sous offre`, `Sous compromis`, `Estimation`.

## Detail sur demande archive/historique

Le worker `documents` lance maintenant une extraction console ciblee avant de reconstruire un detail sur demande :

1. `phase2/sync/sync_console_missing_fields.py --hektor-annonce-id <ID> --annonce-scope all --limit 1 --skip-job-check --refresh-session-on-expired`
2. `Console/prepare_historical_annonce_detail.py` ou `Console/prepare_archived_annonce_detail.py`

Le `--skip-job-check` est volontaire dans ce chemin : l'extraction est appelee depuis un job worker deja en cours.

En cas de vrai 403 Hektor, le worker journalise `console_missing_fields` en erreur et stoppe le job avec un message `Hektor 403`.

## Commandes

Controle sans appel Hektor :

```powershell
.\.venv\Scripts\python.exe phase2\sync\sync_console_missing_fields.py --dry-run --limit 10
```

Controle sans appel Hektor, limite aux annonces courantes de l'app :

```powershell
.\.venv\Scripts\python.exe phase2\sync\sync_console_missing_fields.py --dry-run --annonce-scope current --limit 10
```

Controle cible sur une annonce :

```powershell
.\.venv\Scripts\python.exe phase2\sync\sync_console_missing_fields.py --hektor-annonce-id <ID_HEKTOR> --limit 1 --force --delay-seconds 60
```

Petit rattrapage prudent :

```powershell
.\.venv\Scripts\python.exe phase2\sync\sync_console_missing_fields.py --limit 20 --delay-seconds 60 --batch-size 5 --batch-pause-seconds 120
```

Push Supabase apres un petit rattrapage :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py --all-local-current --skip-stale-deletes --detail-batch-size 25 --dossier-batch-size 50 --work-item-batch-size 50 --filter-batch-size 50
```

Puis push Supabase cible si besoin :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py --hektor-annonce-id <ID_HEKTOR> --skip-stale-deletes --detail-batch-size 10 --dossier-batch-size 10 --work-item-batch-size 10 --filter-batch-size 10
```

## Controle effectue le 2026-06-08

- `--dry-run --limit 3` : OK, aucun appel Hektor.
- `62441` et `62442` : session OK apres rafraichissement, pas de 403, mais Hektor renvoie une page 404. Ces annonces de test ne doivent pas servir de controle d'extraction.
- `1918` : extraction console OK, sans 403.
- Vignette DPE reconstruite depuis l'API : `https://groupe-gti-immobilier.staticlbi.com/wa/images/DPEImages/dpe_FR_cons_390_fr_web_V6.jpg`
- Vignette GES reconstruite depuis l'API : `https://groupe-gti-immobilier.staticlbi.com/wa/images/DPEImages/dpe_FR_ges_82_fr_web_V6.jpg`
- Push Supabase cible `1918` : OK, `details_upserted = 1`, aucune suppression.
- Relecture Supabase : les cles `dpe_image_url`, `ges_image_url`, `dpe_image_urls_json` sont presentes dans `app_dossier_detail_current.detail_payload_json`.

Controle worker detail sur demande apres correction :

- jobs pending/running avant test : 0 ;
- sessions recentes presentes : `Console/sessions/storage_state_admin.json`, `storage_state_actions.json`, `storage_state_documents.json` ;
- worker registry Supabase : `actions`, `admin`, `documents`, `sync_light` actifs ;
- annonce historique `59183` : job `prepare_historical_annonce_detail` pris par `documents:scheduled:v9`, extraction ciblee `done`, pas de 403 ;
- DPE historique reconstruit depuis l'API : `https://groupe-gti-immobilier.staticlbi.com/wa/images/DPEImages/dpeg_web491_103_v3.png` ;
- GES historique reconstruit depuis l'API : `https://groupe-gti-immobilier.staticlbi.com/wa/images/DPEImages/ges_103_v3.png` ;
- annonce archive `45687` : job `prepare_archived_annonce_detail` pris par `documents:scheduled:v9`, extraction ciblee `done`, pas de 403 ;
- DPE archive reconstruit depuis l'API : `https://groupe-gti-immobilier.staticlbi.com/wa/images/DPEImages/dpeg_web355_11_v3.png` ;
- GES archive reconstruit depuis l'API : `https://groupe-gti-immobilier.staticlbi.com/wa/images/DPEImages/ges_11_v3.png` ;
- relecture locale `hektor_annonce_console_detail` : `status=done`, `forbidden403=0`, `error=null` pour `59183` et `45687` ;
- relecture Supabase caches detail : `console_missing_fields_status=done`, `secteur_console_json` present, `pieces_detail_console_json` present, DPE/GES presents.

## Securite

Si `status = stopped_on_403`, le script sort en erreur et le run doit s'arreter.

Si la session Playwright est absente ou expiree, il faut utiliser une session recente :

- `Console/sessions/storage_state_actions.json`
- ou `Console/sessions/storage_state_admin.json` selon le besoin.

Ne pas utiliser `Console/storage_state.json` pour ces controles.
