# Correctifs contacts / transactions - 2026-05-25

## Decisions confirmees

1. La regle de choix du dossier affiche ne change pas.
   `case_dossier_source` reste la synthese annonce : une offre, un compromis et une vente de reference.
2. L'historique complet des transactions est stocke dans une couche separee de relations contacts-annonces.
3. Le miroir local reste la source complete Hektor.
4. Supabase reste une couche legere pour l'app : pas de payload brut `AnnonceById`, pas de payload brut `ContactById`.

## Correctifs appliques

### Run quotidien

Le run quotidien `run_full_pipeline.ps1` integre maintenant :

1. `sync_raw.py --mode update`
2. `normalize_source.py`
3. `sync_contact_details.py --changed-only`
4. `normalize_source.py` une seconde fois pour integrer les derniers `ContactById`
5. `build_case_index.py`
6. phase 2 / vues / checks
7. construction locale contacts
8. push contacts Supabase uniquement si l'option explicite `-PushContactsToSupabase` est utilisee

Parametres ajoutes :

- `-SkipContactDetails`
- `-ContactDetailLimit` (defaut `1000`)
- `-ContactDetailSleepSeconds` (defaut `0.35`)
- `-PushContactsToSupabase`
- `-ContactsEligibleOnly`
- `-IncludeArchivedContactRelations`
- `-IncludeArchivedContactSearches`

Le delta quotidien `ContactById` utilise `--changed-only`, qui couvre les contacts nouveaux ou dont la date locale observee a evolue.

### Backfill initial ContactById

Ajout du script :

- `run_contact_details_backfill.ps1`

Il traite les fiches manquantes par lots reprenables, avec `--missing-only`.

Exemple :

```powershell
.\run_contact_details_backfill.ps1 -BatchSize 5000
```

Le gros backfill n'a pas ete lance automatiquement.

Apres controle des notices et scripts, aucune limite officielle Hektor de type
appels/minute n'a ete trouvee. La documentation locale confirme surtout la
pagination des listings par 20 elements. Par prudence, le backfill `ContactById`
utilise donc une pause par defaut de `0.35` seconde entre deux appels, avec
reprise par lots et retries HTTP cote client.

### Reprise ventes

Le perimetre full des ventes passe de `2020-01-01` a `2010-01-01`.

Fichier modifie :

- `sync_raw.py`

La logique update quotidienne reste separee : si aucune date n'est fournie en mode update, le script utilise toujours la fenetre recente configuree par `--vente-lookback-months`.

### Relations transactionnelles

La table locale `app_contact_relation_current` ne se limite plus a une relation par contact/annonce/role.

Elle contient maintenant une cle relation propre et les champs transactionnels :

- `relation_key`
- `transaction_type`
- `transaction_id`
- `transaction_state`
- `transaction_date`
- `transaction_amount`
- `is_active_annonce`

Cela permet de conserver plusieurs offres ou plusieurs compromis sur une meme annonce, sans ecrasement.

Roles ajoutes depuis les listings transactionnels :

- `acquereur_offre`
- `acquereur_compromis`
- `acquereur_vente`

### Recherches acquereurs

Ajout d'une table locale normalisee :

- `app_contact_search_current`

Elle est alimentee depuis `ContactById.data.recherches`.

Le champ fiable pour actif/inactif est :

- `archive = 0` : recherche active
- `archive = 1` : recherche archivee

Il n'y a pas de date recherche fiable observee dans les fiches testees. La fraicheur reste portee par la fiche contact (`contact.datemaj`).

### Perimetre Supabase

Le patch Supabase contacts a ete corrige :

- pas de detail annonce brut ;
- pas de detail contact brut ;
- ajout d'une table relations normalisees ;
- ajout d'une table recherches normalisees ;
- par defaut, seules les relations d'annonces actives partent dans le push ;
- par defaut, seules les recherches actives partent dans le push ;
- option possible pour pousser les relations archivees ou recherches archivees si besoin.

Le listing leger de tous les contacts reste possible pour la pagination et les filtres.

## Controle local effectue

Commande de reconstruction locale executee sans push Supabase :

```powershell
.\.venv\Scripts\python.exe phase2\contacts\build_contacts_layer.py --no-reports
```

Resultats observes :

| Indicateur | Volume |
| --- | ---: |
| Contacts total | 354293 |
| Contacts actifs | 215980 |
| Contacts archives | 138313 |
| Relations locales total | 150888 |
| Relations transactionnelles | 27476 |
| Contacts avec relation | 104644 |
| Recherches normalisees actuellement disponibles | 40 |
| Recherches actives disponibles | 3 |
| Contacts eligibles detail Supabase | 53008 |
| Groupes doublons detectes | 36427 |
| Groupes high/critical | 24775 |
| Suspicions transfert archive | 13739 |

## Dry-run Supabase

Dry-run par defaut, sans envoi :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_contacts_to_supabase.py --dry-run
```

Resultat :

| Table | Lignes |
| --- | ---: |
| `app_contact_current` | 354293 |
| `app_contact_relation_current` | 71638 |
| `app_contact_search_current` | 3 |

Dry-run detail eligible :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_contacts_to_supabase.py --dry-run --contacts-scope eligible
```

Resultat :

| Table | Lignes |
| --- | ---: |
| `app_contact_current` | 53008 |
| `app_contact_relation_current` | 71638 |
| `app_contact_search_current` | 3 |

## Tests

Tests executes :

```powershell
.\.venv\Scripts\python.exe -m unittest phase2.contacts.test_contacts_layer
.\.venv\Scripts\python.exe -m py_compile sync_raw.py phase2\contacts\build_contacts_layer.py phase2\sync\sync_contact_details.py phase2\sync\push_contacts_to_supabase.py
```

Resultat : OK.

## Reste a faire avant mise en ligne

1. Relancer la reprise full des transactions avec ventes depuis 2010.
2. Lancer le backfill complet `ContactById` local sur les 354293 contacts, par lots reprenables.
3. Reconstruire la couche contacts apres le backfill complet.
4. Valider le choix Supabase :
   - listing leger complet `354293` contacts ;
   - ou perimetre eligible `53008` contacts pour une premiere mise en ligne plus prudente.
5. Appliquer le patch Supabase en environnement controle.
6. Brancher l'interface contacts avec pagination serveur, filtre actif par defaut et option archives.
7. Ajouter la fiche contact : relations annonces, historique transactions, recherches actives.
8. Garder l'audit doublons en lecture/admin, sans suppression automatique.
