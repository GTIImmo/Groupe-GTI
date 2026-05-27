# Rapport audit integration contacts app - 2026-05-27

## Objectif

Mettre en place l'integration Contacts dans l'app sans attendre le backfill complet des 340k fiches detail, en exploitant les fiches deja recuperees localement.

Regle conservee :
- local SQLite = copie globale Hektor, listing contacts, details disponibles, relations, recherches acquereurs, doublons ;
- Supabase = couche limitee aux contacts utiles a l'app ;
- aucun push Git ou Supabase sans accord explicite.

## Etat data controle

Dernier controle local :
- contacts listing local : 354380 dans `sync_contact_state` ;
- fiches detail ContactById recuperees : 82966 ;
- fiches detail restantes : 271414 ;
- erreurs ContactById : 5015, dont 4998 404 et 14 timeout/connect ;
- contacts Hektor quarantaine 404 : 4272 ;
- contacts phase 2 : 354353 ;
- contacts actifs phase 2 : 216039 ;
- contacts eligibles Supabase/app : 56649 ;
- relations contacts-annonces : 156231 ;
- relations sur annonces actives : 76956 ;
- relations transactionnelles : 32803 ;
- recherches acquereurs : 19545 ;
- recherches acquereurs actives : 3227 ;
- contacts avec recherche active : 3074 ;
- groupes doublons : 36454 ;
- groupes high/critical : 24797 ;
- suspicion transfert archive massif : 13750.

## Corrections appliquees

### App React

Fichiers modifies :
- `apps/hektor-v1/src/types.ts`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/styles.css`

Ajouts principaux :
- consommation de `app_contact_searches_current` ;
- chargement des recherches acquereurs sur la fiche contact ;
- affichage des recherches actives dans le detail contact ;
- filtre Contacts "Recherche" : active, avec recherche, sans recherche ;
- KPI "Recherches actives" dans l'ecran Contacts ;
- affichage table "Liens / recherches" ;
- affichage des IDs transactionnels offre/compromis/vente dans les relations ;
- champs TypeScript alignes sur les tables Supabase contacts.

### Monitoring

Fichier ajoute :
- `phase2/checks/contact_sync_status.py`

Ce controle produit :
- `phase2/docs/RAPPORT_CONTACT_SYNC_STATUS.md`

Il verifie :
- etat du dernier run ContactById ;
- volume detail recupere/restant ;
- 404 et erreurs timeout/connect ;
- couche contacts phase 2 ;
- relations, recherches, doublons ;
- etat local de push Supabase contacts.

Le pipeline quotidien `run_full_pipeline.ps1` lance maintenant ce rapport apres les controles qualite phase 2.

## Supabase

Le push contact reste volontairement explicite :
- le run quotidien ne pousse pas les contacts sauf option `-PushContactsToSupabase` ;
- le push quotidien utilise `--push-mode update` et `--contacts-scope active_or_eligible` ;
- `active_or_eligible` = tous les contacts actifs en listing leger + les archives deja utiles a l'app ;
- les recherches poussees par defaut sont seulement les recherches actives ;
- les relations poussees par defaut sont seulement celles liees a des annonces actives ;
- les doublons restent locaux/admin sauf option explicite.

Etat controle apres push le 2026-05-27 :
- `app_contact_current` : 233324 contacts dans Supabase ;
- `has_contact_detail` : 70485 contacts du perimetre Supabase ont une fiche detail locale connue ;
- `app_contact_relation_current` : 77010 relations ;
- `app_contact_search_current` : 3227 recherches actives ;
- payloads bruts `ContactById` pousses : 0.

Apres le push, l'etat local `app_contact_supabase_push_state` confirme un dry-run a 0 ligne a renvoyer.

## Tests effectues

OK :
- compilation Python des scripts contacts/monitoring ;
- test unitaire `phase2/contacts/test_contacts_layer.py` ;
- controles qualite `phase2/checks/run_quality_checks.py` ;
- rapport monitoring contacts ;
- dry-run push contacts Supabase ;
- build React `npm run build` ;
- serveur local Vite repond en HTTP 200 sur `http://127.0.0.1:5174/`.

Limite :
- controle visuel automatise par navigateur non disponible dans cette session, faute de module navigateur/Playwright accessible. Le build TypeScript et le demarrage HTTP sont OK.

## Reste a faire avant mise en ligne complete

1. Ouvrir l'app et verifier l'ecran Contacts avec un compte authentifie.
2. Reprendre plus tard le backfill ContactById manquant, en blocs, quand Hektor/IP est stable.
3. Lancer le run quotidien normal avec details delta et monitoring.
4. Traiter les doublons uniquement par audit/classement, sans suppression automatique.
