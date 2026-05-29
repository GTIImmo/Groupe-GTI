# Annuaire negociateurs actifs / inactifs Hektor

Date : `2026-05-29`

## Constat

Controle API en lecture seule sur `/Api/Negociateur/listNegos/` :

- `actif=1` : `31` negociateurs uniques
- `actif=0` : `32` negociateurs uniques
- sans filtre : `31` negociateurs uniques
- `archive=0` et `archive=1` ne changent pas le resultat sur cette route

La ligne supplementaire retournee par `actif=0` est :

- `id=100`, `idUser=142`, `agence=12`, Sarah ROMUALD, `romuald@gti-immobilier.fr`

Gonzalez est bien expose dans la liste active sous :

- `id=23`, `idUser=48`, `agence=12`

Les anciens rattachements Gonzalez `95/120` et `97/121` restent des lignes historiques issues de la base locale / `getNegoById`, pas des utilisateurs actifs acceptes par la console Hektor.

## Decision

Ne pas supprimer les anciens rattachements negociateurs.

La table `app_hektor_negotiator_agency_directory` doit conserver l'historique, mais porter un statut :

- `is_active=true` si `hektor_user_id` est present dans `app_user_directory` comme `NEGO`
- `is_active=false` sinon

Les formulaires et workers doivent utiliser uniquement les actifs.
Les vues historiques/detail peuvent garder les inactifs pour expliquer les anciennes annonces, contacts et mandats.

## Corrections associees

- `sync_raw.py` conserve l'appel actif actuel et ajoute un second listing `list_negos_inactive` avec `actif=0`.
- `normalize_source.py` normalise `list_negos` et `list_negos_inactive`.
- `push_hektor_directory_to_supabase.py` conserve toutes les lignes locales et marque les rattachements actifs/inactifs si les colonnes Supabase existent.
- patch Supabase : `supabase/patch_hektor_negotiator_agency_active_status_2026-05-29.sql`.
