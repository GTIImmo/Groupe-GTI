# Note synchro annuaire Hektor pour RDV

Date: 2026-04-30

## Objet

Supprimer la dependance aux appels externes au chargement public du module RDV.

Le principe retenu est :

- synchroniser quotidiennement les users Hektor
- synchroniser quotidiennement les agences Hektor
- stocker ces donnees dans Supabase
- faire lire le module RDV uniquement depuis Supabase

## Verification API

Les controles live ont confirme :

- `GET /Api/User/UsersOfParent/`
  - necessite `page=1`
  - les coordonnees sont dans `coordonnees.mail`, `coordonnees.tel`, `coordonnees.portable`
  - sur l'instance GTI, l'appel `page=1` remonte deja la liste utile et `metadata.nextPage` ne doit pas etre suivi aveuglement
  - les pages suivantes peuvent rejouer un sous-ensemble deja present
- `GET /Api/Agence/ListAgences/`
  - necessite `page=0`
  - les coordonnees agence sont a la racine `mail`, `tel`

Donc :

- `UsersOfParent` suffit pour les users / commerciaux
- `ListAgences` suffit pour les contacts agence
- pour `UsersOfParent`, la synchro quotidienne lit uniquement `page=1` puis dedoublonne par `id_user` en garde-fou

## Tables Supabase ajoutees

- `app_user_directory`
- `app_agence_directory`

Ces tables servent d'annuaire local pour :

- `commercial_id`
- `commercial_nom`
- `negociateur_email`
- `negociateur_phone`
- `negociateur_mobile`
- `agence_nom`
- `agence_phone`
- `agence_email`

## Script de synchro

Nouveau script :

- `phase2/sync/push_hektor_directory_to_supabase.py`

Ce script :

1. appelle `UsersOfParent` sur `page=1`
2. appelle `ListAgences`
3. upsert les users dans `app_user_directory`
4. upsert les agences dans `app_agence_directory`
5. purge les ids absents du listing source

## Correctif 2026-04-30

Une premiere version du script suivait `metadata.nextPage` sur `UsersOfParent`.

Sur l'instance GTI, cela provoquait un rejeu partiel des users deja vus et donc :

- un lot d'upsert avec plusieurs lignes portant le meme `id_user`
- une erreur Supabase `ON CONFLICT DO UPDATE command cannot affect row a second time`

Le correctif retenu est :

- lecture unique de `UsersOfParent?page=1`
- dedoublonnage de securite par `id_user` avant envoi Supabase

Le probleme ne venait donc pas d'un doublon stocke dans Supabase, mais d'une collecte trop agressive cote script.

## Effet sur le module RDV

Le service RDV :

- ne fait plus d'appel externe pour charger les contacts
- lit d'abord `app_user_directory`
- lit ensuite `app_agence_directory`
- garde seulement un fallback local de parsing texte depuis `detail_payload_json`

## Commande quotidienne recommandee

Depuis `C:\Users\frede\Desktop\Projet` :

```powershell
.\.venv\Scripts\python.exe sync_raw.py --mode update --resources annonces contacts mandats offres compromis ventes broadcasts --missing-only
.\.venv\Scripts\python.exe normalize_source.py
.\.venv\Scripts\python.exe build_case_index.py
.\.venv\Scripts\python.exe phase2\bootstrap_phase2.py
.\.venv\Scripts\python.exe phase2\refresh_views.py
.\.venv\Scripts\python.exe phase2\checks\run_quality_checks.py
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py --dossier-batch-size 50 --detail-batch-size 25 --work-item-batch-size 50 --filter-batch-size 50
.\.venv\Scripts\python.exe phase2\sync\push_hektor_directory_to_supabase.py
```

## Point de vigilance

Le patch SQL suivant doit etre applique dans Supabase avant usage :

- `supabase/patch_hektor_directory_sync_2026-04-30.sql`

Le patch suivant reste aussi requis pour le lien RDV :

- `supabase/patch_appointment_public_link_enrichment_2026-04-29.sql`
