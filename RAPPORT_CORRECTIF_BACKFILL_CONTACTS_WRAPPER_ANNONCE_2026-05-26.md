# Correctif backfill ContactById - wrapper type annonce - 2026-05-26

## Verification notices API locales

Documents controles :

- `notice/Hektor API v2 - Documentation 30c05e13c226808bad7ac1d53f9e516b.md`
- `notice/Hektor-API_x_GTIImmo.postman_collection.json`
- `REPRISE_API_PARAMS.md`
- `notice/ROMAIN MAIL 2.txt`
- `notice/DELTA_ANNONCES_CONTACTS_NOTE.md`
- `notice/CONTACTS_ARCHIVED_RUN_NOTE.md`

Points confirmes :

- `GET /Api/Contact/ListContacts/` est pagine par 20.
- `archive=0` donne les contacts actifs.
- `archive=1` donne les contacts archives.
- `GET /Api/Contact/ContactById?id=...` est le detail riche contact, avec les recherches associees.
- le tri API fiable pour le listing contacts est `sort=dateLastTraitement&way=DESC`.
- l'API ne renvoie pas toujours `dateLastTraitement` dans les items ; le champ observable conserve localement reste `datemaj`.

Conclusion : la bonne version est bien le modele listing + ById, comme annonce.

## Regle retenue

Le script `phase2/sync/sync_contact_details.py` suit maintenant le meme principe que `sync_archived_annonce_details.py` :

- rafraichit le listing contacts, sauf `--skip-listing-refresh`
- calcule une liste de candidats une seule fois
- traite par lots
- log les erreurs et continue
- marque `sync_contact_state.last_detail_sync_at` uniquement apres succes
- relance `normalize_source.py` a la fin, sauf `--no-normalize`

Critere candidat hors `--force-full` :

```text
detail absent
OU last_detail_sync_at absent
OU date_maj contact > last_detail_sync_at
```

En mode quotidien, apres le `sync_raw.py --mode update`, le script ajoute aussi :

```text
OU last_seen_at contact > last_detail_sync_at
```

Cette regle applique le retour corrige de Romain : `ListContacts` doit etre trie par `dateLastTraitement`, mais cette date n'est pas renvoyee dans les items. Le fait qu'un contact soit revu dans le listing update devient donc le signal observable local.

Ordre :

1. contacts sans detail
2. contacts avec `date_maj` la plus recente
3. ID contact croissant

## Run quotidien

Le run quotidien utilise maintenant le wrapper contact apres `sync_raw.py` et `normalize_source.py`.

Dans `run_full_pipeline.ps1`, le detail contact quotidien :

- ne relit pas le listing car `sync_raw.py` vient deja de le faire
- utilise `--use-last-seen-as-changed` pour suivre le tri API `dateLastTraitement`
- limite par defaut a 1000 candidats
- traite par lots de 100
- laisse `normalize_source.py` etre relance par le pipeline

Le push contacts Supabase reste optionnel avec `-PushContactsToSupabase`, mais s'il est active il utilise maintenant :

```text
push_contacts_to_supabase.py --push-mode update
```

Ce mode compare un hash local et n'upload que les lignes changees depuis le dernier push contacts reussi.

## Run full contacts

Controle sans API detail :

```powershell
cd C:\Hektor\Projet
.\run_contact_details_backfill.ps1 -DryRun -FullListingRefresh -ListingMaxPages 0
```

Run full pour tout recuperer :

```powershell
cd C:\Hektor\Projet
.\run_contact_details_backfill.ps1 -FullListingRefresh -ListingMaxPages 0
```

Reprise naturelle :

```powershell
.\run_contact_details_backfill.ps1 -SkipListingRefresh
```

## Correctif timeout OAuth

Incident observe le 2026-05-26 : timeout reseau sur `/Api/OAuth/Authenticate/` avant le demarrage du run contact.

Correction ajoutee dans `hektor_pipeline/common.py` :

- l'authentification OAuth Hektor retente maintenant plusieurs fois avant d'abandonner ;
- l'erreur finale masque les parametres sensibles (`client_secret`, `token`) ;
- le run reste reprenable car les details contacts sont marques `last_detail_sync_at` uniquement apres succes.

Correction ajoutee dans `run_contact_details_backfill.ps1` :

- le wrapper relance automatiquement l'extraction en cas d'echec global ;
- defaut : `MaxAttempts=6`, `RetryDelaySeconds=300` ;
- utile si l'API Hektor est temporairement indisponible au moment de l'authentification.

## Optimisation reprise 404 ContactById

Analyse du run global contacts : les lenteurs observees en phase detail venaient principalement de `ContactById` repondant `404 Not Found`, pas de timeouts reseau.

Correction ajoutee :

- les erreurs HTTP 4xx Hektor ne sont plus retry comme des erreurs temporaires ;
- les contacts dont `ContactById` repond `404` sont classes localement dans `sync_contact_detail_skip` avec la raison `http_404_not_found` ;
- la reprise normale exclut ces contacts 404 pour ne pas reperdre du temps ;
- option disponible si besoin d'audit ou de re-test force : `--retry-404`.

Commande de reprise recommandee apres arret du run long :

```powershell
powershell -ExecutionPolicy Bypass -File .\run_contact_details_backfill.ps1 -SkipListingRefresh -NoNormalize -MaxAttempts 12 -RetryDelaySeconds 300
```

Cette commande ne refait pas le listing complet et ne reprend que les contacts sans detail exploitable, en excluant par defaut les 404 deja identifies.

## Tests effectues

- compilation Python
- syntaxe PowerShell
- dry-run du wrapper contacts sans appel detail
- dry-run upload contacts en mode update
- test unitaire contacts
- test local d'un timeout OAuth simule : retry effectif et secrets masques
- parsing PowerShell OK apres ajout des relances automatiques
- compilation Python OK apres optimisation 404

## Important

Aucun push Git.
Aucun push Supabase execute pendant le correctif.
Aucune suppression de contacts ni de doublons.
