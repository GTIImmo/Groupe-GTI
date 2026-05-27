# Rapport run quotidien contacts - 2026-05-27

## Objectif

- Stabiliser le run quotidien pour que l'etape `ContactById` ne bloque pas tout le pipeline en cas d'erreur Hektor.
- Ne pas remplacer le script de reprise par blocs de details contacts.
- Retirer les corrections droits / securite ajoutees ensuite sur le module Contacts.

## Retour arriere droits / securite

Corrections retirees :

- suppression du fallback `auth.jwt()->>'email'` dans les fonctions RLS contacts ;
- suppression de l'acces technique `anon` sur les tables et vues contacts ;
- suppression des fichiers SQL locaux de correction securite du 2026-05-27.

Fonctions revenues au fonctionnement precedent :

- `is_app_global_reader()`
- `is_app_manager_or_admin()`
- `can_access_negotiator_email(target_email text)`

Point volontairement conserve :

- les droits d'ecriture larges pour `anon` / `authenticated` n'ont pas ete remis, car ce serait dangereux pour une app exposee.
- `authenticated` conserve `SELECT`.
- `service_role` conserve les droits complets pour les scripts serveur.

Migration appliquee :

- `contacts_revert_email_fallback_and_anon_select_2026_05_27`

## Controles Supabase

Profil global admin :

- `is_app_global_reader()` : `true`
- contacts visibles : `233324`
- relations visibles : `77010`
- recherches visibles : `3227`

Controle technique :

- les 3 fonctions RLS contacts ne contiennent plus de fallback `auth.jwt()->>'email'` ;
- `anon` n'a plus de droit sur les objets contacts ;
- `authenticated` a `SELECT` sur les 8 objets contacts ;
- `service_role` conserve les droits complets sur les 8 objets contacts.

## Stabilisation du run quotidien

Fichier modifie :

- `run_full_pipeline.ps1`

Ajouts :

- `ContactDetailMaxAttempts`, defaut `2`.
- `ContactDetailRetryDelaySeconds`, defaut `120`.
- `FailOnContactDetailsError`, option pour rendre l'erreur detail bloquante si besoin.

Comportement quotidien par defaut :

- si `sync_contact_details.py` reussit, le pipeline normalise ensuite les nouvelles fiches detail ;
- si `sync_contact_details.py` echoue apres les tentatives, le pipeline continue avec les details deja locaux ;
- le rapport de monitoring contacts est quand meme genere ;
- le push Supabase contacts reste delta et explicite avec `-PushContactsToSupabase`.

## Reprise par lots

Fichier conserve :

- `run_contact_details_backfill.ps1`

Modification limitee :

- pause par defaut entre tentatives : `300` secondes -> `120` secondes.

Le fonctionnement de reprise par blocs, y compris les blocs de `2000`, n'a pas ete remplace.

## Controles techniques

OK :

- parse PowerShell `run_full_pipeline.ps1`
- parse PowerShell `run_contact_details_backfill.ps1`
- controle Supabase admin : `233324` contacts visibles
- controle application locale : l'ecran Contacts charge, mais la requete statistiques contacts tombe encore en timeout Supabase

Hors scope pour cette passe :

- optimisation des statistiques Contacts dans le front ;
- rapprochement recherches acquereurs / annonces ;
- bouton de chargement detail a la demande ;
- workflow complet de traitement des doublons.
