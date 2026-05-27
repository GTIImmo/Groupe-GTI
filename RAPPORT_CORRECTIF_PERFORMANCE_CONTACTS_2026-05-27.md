# Rapport correctif performance Contacts - 2026-05-27

## Objectif

Debloquer le listing Contacts dans l'app sans modifier le perimetre fonctionnel des droits.

## Correctifs appliques

- le listing Contacts ne depend plus du chargement des statistiques ;
- le listing Contacts n'utilise plus `count exact` ;
- le listing Contacts ne fait plus de `select('*')`, mais une selection legere des champs affiches ;
- la recherche Contacts passe par `search_text` au lieu d'un `OR` large sur dix colonnes ;
- ajout d'un index trigram sur `app_contact_current.search_text` ;
- ajout d'un index de tri sur `archive`, `duplicate_group_count`, `date_maj`, `display_name`, `hektor_contact_id` ;
- optimisation RLS Contacts avec `(select public.is_app_global_reader())`, comme sur Annonces, sans changer les roles autorises.

## Migration Supabase

- `contacts_listing_performance_2026_05_27`
- fichier local : `supabase/patch_contacts_listing_performance_2026-05-27.sql`

## Resultats mesures

Avant correction :

- recherche Contacts `martinez` : environ `12,9 s` ;
- listing actif Contacts : environ `3,6 s` ;
- timeout possible dans l'app a cause des statistiques.

Apres correction :

- listing actif Contacts : environ `5 ms` cote SQL ;
- recherche Contacts `martinez` : environ `95 ms` cote SQL ;
- admin Supabase : `233324` contacts visibles, `77010` relations, `3227` recherches ;
- app locale : l'ecran Contacts affiche le listing, sans erreur console.

## Verification

- build React OK : `npm run build` ;
- parse PowerShell OK pour `run_full_pipeline.ps1` et `run_contact_details_backfill.ps1` ;
- aucune suppression de donnees ;
- aucun push git effectue.
