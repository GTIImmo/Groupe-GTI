# Google Workspace - mise en place Domain Wide Delegation

Objectif : permettre au backend GTI d'utiliser Gmail et Google Agenda sans demander une autorisation manuelle a chaque collaborateur.

## Etape 1 - Google Cloud

Dans la console Google Cloud :

1. Creer ou choisir un projet Google Cloud GTI.
2. Activer les API :
   - Gmail API
   - Google Calendar API
   - People API plus tard, seulement pour les contacts.
3. Creer un compte de service, par exemple `gti-workspace-orchestrator`.
4. Activer la delegation au niveau du domaine pour ce compte de service.
5. Creer une cle JSON et la placer hors du front, par exemple :

```text
C:\Hektor\Projet\secrets\google-workspace-service-account.json
```

Ne jamais mettre ce fichier dans `apps/hektor-v1`, ni dans Supabase, ni dans Git.

## Etape 2 - Admin Google Workspace

Dans la console admin Google Workspace en francais :

1. Aller dans `Securite`.
2. Ouvrir `Controle des acces et des donnees`.
3. Ouvrir `Commandes des API`.
4. Ouvrir `Gerer la delegation au niveau du domaine`.
5. Ajouter un nouveau client.
6. Coller le `Client ID` du compte de service.
7. Coller les scopes initiaux :

```text
https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/calendar.freebusy,https://www.googleapis.com/auth/calendar.events
```

## Etape 3 - Variables backend

Ajouter les lignes suivantes dans le fichier existant :

```text
C:\Hektor\Projet\.env
```

Ne pas creer un deuxieme fichier `.env` si le fichier racine existe deja.

```text
GOOGLE_WORKSPACE_DOMAIN=gti-immobilier.fr
GOOGLE_WORKSPACE_AUTH_MODE=domain_wide_delegation
GOOGLE_WORKSPACE_DWD_CLIENT_ID=<client_id_du_compte_de_service>
GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE=C:\Hektor\Projet\secrets\google-workspace-service-account.json
GOOGLE_WORKSPACE_SUBJECT_EMAIL=accueil@gti-immobilier.fr
GOOGLE_WORKSPACE_SCOPES=https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/calendar.freebusy,https://www.googleapis.com/auth/calendar.events
```

## Etape 4 - Controle

Endpoint backend ajoute :

```text
GET /google-workspace/status
POST /google-workspace/calendar/freebusy-test
POST /google-workspace/calendar/event-test
```

Il permet a un admin de verifier :

- domaine GTI ;
- fichier compte de service present ;
- client ID coherent avec le fichier JSON ;
- scopes initiaux autorises/configures ;
- compte sujet de test `accueil@gti-immobilier.fr`.

## Creation utilisateur dans l'application

La creation d'un utilisateur GTI dans l'app doit rester la source des droits metier.

Regle appliquee cote backend :

- creation reservee aux emails `@gti-immobilier.fr` ;
- creation du compte Supabase Auth ;
- creation du profil `app_user_profile` avec le role app ;
- creation automatique de la liaison `app_google_workspace_identity` ;
- pour un role `commercial`, croisement avec l'annuaire Hektor synchronise :
  - `app_user_directory` pour trouver le `id_user` Hektor actif issu de l'API ;
  - `app_hektor_negotiator_agency_directory` pour trouver le rattachement negociateur/agence actif ;
- si le croisement Hektor est ambigu, la liaison passe en `conflict` ;
- si un commercial n'a aucun croisement Hektor, la liaison passe en `pending` ;
- pour un admin/manager, la liaison Google peut etre `linked` meme sans negociateur Hektor.

Cette regle evite de donner a un utilisateur Google le contexte Hektor d'un mauvais negociateur.

## Journalisation avant orchestrateur

Une table Supabase dediee trace les appels Google Workspace :

```text
public.app_google_workspace_action_log
```

Elle journalise :

- utilisateur app demandeur ;
- compte Google Workspace sujet ;
- type d'action ;
- succes ou erreur ;
- mode `dryRun` ;
- metadonnees techniques limitees.

Elle ne doit pas stocker :

- cle JSON Google ;
- access token ;
- corps complet d'email ;
- description complete de rendez-vous ;
- contenu Gmail.

Cette table sera la base d'audit pour les futurs workers et agents IA.

## Scopes futurs a ne pas activer tout de suite

Pour afficher des emails dans le CRM ou preparer les agents IA :

```text
https://www.googleapis.com/auth/gmail.metadata
https://www.googleapis.com/auth/gmail.readonly
```

Ces scopes donnent acces a des donnees plus sensibles. Ils doivent attendre la journalisation, le cadrage RGPD et les droits metier dans l'application.
