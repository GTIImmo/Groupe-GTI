# Workers GTI

Cette page cartographie les workers et scripts d'exécution réellement présents.

## Pipeline principal

| Worker | Chemin | Déclenchement | Rôle |
| --- | --- | --- | --- |
| Full pipeline | `run_full_pipeline.ps1` | Manuel / tâche planifiée locale | Enchaîne extraction, normalisation, Phase2, qualité, Supabase, Matterport et RDV. |
| Extraction RAW | `sync_raw.py` | Appelé par le pipeline | Synchronise les ressources Hektor vers `data/hektor.sqlite`. |
| Normalisation | `normalize_source.py` | Appelé par le pipeline | Construit les tables locales normalisées. |
| Index dossier | `build_case_index.py` | Appelé par le pipeline | Construit `case_dossier_source`. |
| Bootstrap Phase2 | `phase2/bootstrap_phase2.py` | Appelé par le pipeline | Alimente le modèle métier Phase2. |
| Refresh vues | `phase2/refresh_views.py` | Appelé par le pipeline | Rafraîchit les vues/agrégats Phase2. |
| Qualité | `phase2/checks/run_quality_checks.py` | Appelé par le pipeline | Exécute les contrôles de cohérence. |
| Push Supabase | `phase2/sync/push_upgrade_to_supabase.py` | Appelé par le pipeline | Publie les tables applicatives Supabase. |

## Workers contacts

| Worker | Chemin | Rôle |
| --- | --- | --- |
| Backfill contacts | `phase2/sync/sync_contact_details.py` | Récupère les détails `ContactById` depuis Hektor. |
| Wrapper backfill | `run_contact_details_backfill.ps1` | Relance le backfill contacts avec temporisation/retry. |
| Couche contacts | `phase2/contacts/build_contacts_layer.py` | Construit les contacts, relations et recherches locales. |
| Push contacts | `phase2/sync/push_contacts_to_supabase.py` | Push optionnel de la couche contacts vers Supabase. |

## Worker Console

Le worker Console est `Console/console_job_worker.js`.
Il consomme la file Supabase `app_console_job` via la RPC
`app_console_claim_next_job`.

Kinds supportés :

| Kind | Usage |
| --- | --- |
| `actions` | Actions Hektor métier : contacts mandants, champs annonce, mandat, brouillon. |
| `documents` | Sync, préparation, upload et suppression de documents/photos. |
| `admin` | Suppression, archive, restauration, statut et affectation négociateur. |
| `matterport` | Actions Matterport via Playwright. |
| `sync_light` | Refresh ciblé après action Console. |
| `sync_full` | Jobs plus lourds de synchronisation Console. |
| `sync` | Alias existant vers `sync_light`. |
| `all` | Worker polyvalent. |

Job types observés :

- `link_hektor_mandant`
- `create_hektor_contact`
- `update_hektor_contact`
- `create_hektor_mandant_contact`
- `update_hektor_mandant_contact`
- `update_hektor_annonce_fields`
- `create_hektor_mandat_auto_number`
- `create_hektor_draft_annonce`
- `sync_console_documents`
- `prepare_document_cloud`
- `upload_document_to_hektor`
- `delete_document_from_hektor`
- `sync_hektor_photos`
- `upload_hektor_photo`
- `prepare_archived_annonce_detail`
- `prepare_historical_annonce_detail`
- `delete_hektor_annonce`
- `archive_hektor_annonce`
- `restore_hektor_annonce`
- `change_hektor_annonce_status`
- `assign_hektor_annonce_negotiator`
- `matterport_online`
- `matterport_offline`
- `matterport_archive`
- `matterport_reactivate`
- `refresh_console_data`
- `refresh_console_contact_data`
- `archive_cloud_documents`

Flux contacts globaux :

1. L'app cree `create_hektor_contact` ou `update_hektor_contact` avec un compte Hektor cible obligatoire.
2. Supabase controle le droit app (`admin`, `manager`, `commercial`) et refuse un job sans contexte negociateur.
3. En creation, le formulaire app transmet la typologie Hektor minimale : qualification (`proprietaire`, `acquereur`, `locataire`, `partenaire`), structure (`personne_seule`, `couple`, `personne_morale`), source, categorie, note et option RGPD.
4. En modification, le formulaire standard Hektor verifie par Playwright expose l'identite, les coordonnees, la source, la categorie et la note, mais pas la qualification/statut ; l'app ne modifie donc pas ces deux champs par ce flux.
5. Le worker `actions` relit le contexte contact/dossier si besoin, mappe en creation ces valeurs vers les codes Console Hektor (`qualification` 1/2/3/4 et `statut` 1/2/3), puis ecrit dans Hektor avec le contexte negociateur cible.
6. Le worker cree un job `refresh_console_contact_data` pour relire seulement le `ContactById` concerne.
7. Le worker `sync_light` normalise localement, reconstruit la couche contacts, puis pousse la projection legere Supabase.

Ce flux ne lance pas le backfill 340k contacts et ne modifie pas les relations mandants affichees dans les annonces. Les relations/recherches contact ne sont pas melangees dans la creation d'identite : l'assistant Hektor `ajouter un nouveau contact` possede une etape suivante separee, a traiter par un job dedie apres validation du comportement Console.

Note : `archive_cloud_documents` est référencé mais son handler indique qu'il
reste à implémenter après validation du dimensionnement stockage.

## Matterport

| Worker | Chemin | Rôle |
| --- | --- | --- |
| Sync modèles | `phase2/sync/sync_matterport_models.py` | Synchronise les liens/modèles Matterport vers Supabase. |
| Actions console | `Console/matterport_console_actions.js` | Met en ligne, hors ligne, archive ou réactive un modèle via Playwright. |
| Login | `Console/matterport_playwright_login.js` | Prépare la session Matterport utilisée par le worker. |

## ACTIF

Le pipeline `ACTIF/` est séparé du flux principal.

| Worker | Rôle |
| --- | --- |
| `actif_sync.py` | Synchronisation des données ACTIF. |
| `actif_normalize.py` | Normalisation ACTIF. |
| `actif_build.py` | Construction de la base exploitable ACTIF. |
| `actif_report.py` | Reporting ACTIF. |
| `actif_watch.py` | Surveillance locale du pipeline ACTIF. |

## Principes pour agents IA

- Ne pas modifier un worker sans lecture préalable de son script appelant.
- Ne pas changer les contrats de job Supabase sans vérifier les patchs SQL.
- Ne pas remplacer Playwright : il est une dépendance fonctionnelle de la Console.
- Traiter `data/hektor.sqlite` et `phase2/phase2.sqlite` comme états critiques.
