# Backend Python metier

Ce backend a pour but de sortir du serveur Vite local uniquement les actions serveur sensibles du projet :

- administration utilisateurs
- diffusion Hektor depuis la console
- acceptation d'une demande de validation

Il ne remplace ni `Phase 1`, ni `Phase 2`, ni Supabase.

## Principe

- `Phase 1 / Phase 2`
  - restent les moteurs de sync / consolidation
- `Supabase`
  - reste la base prod et l'auth
- `Vercel`
  - reste le front React
- `backend`
  - expose seulement les endpoints metier serveur

## Endpoints vises

- `GET /health`
- `GET /admin/users/list`
- `POST /admin/users/create`
- `POST /admin/users/update`
- `POST /admin/users/send-reset`
- `POST /hektor-diffusion/apply`
- `POST /hektor-diffusion/accept`
- `GET /google-workspace/status`
- `POST /google-workspace/gmail/send-test`
- `POST /google-workspace/calendar/freebusy-test`
- `POST /google-workspace/calendar/event-test`
- `POST /google-workspace/calendar/event-update-test`
- `POST /google-workspace/calendar/event-delete-test`

## Variables d'environnement

Le backend lit en priorite le fichier racine existant :

```text
C:\Hektor\Projet\.env
```

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `APP_BASE_URL`
- `HEKTOR_API_BASE_URL`
- `HEKTOR_CLIENT_ID`
- `HEKTOR_CLIENT_SECRET`
- `HEKTOR_API_VERSION`
- `APPOINTMENT_EMAIL_LOGO_URL` : optionnel, URL de secours du logo si le parametre Supabase `app_setting.appointment_email_logo_url` n'est pas encore present.
- `GOOGLE_WORKSPACE_DOMAIN` : domaine autorise, par defaut `gti-immobilier.fr`.
- `GOOGLE_WORKSPACE_AUTH_MODE` : mode cible, par defaut `domain_wide_delegation`.
- `GOOGLE_WORKSPACE_DWD_CLIENT_ID` : Client ID du compte de service a autoriser dans la console admin Google.
- `GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE` : chemin local du JSON de compte de service, jamais cote front.
- `GOOGLE_WORKSPACE_SUBJECT_EMAIL` : compte Google sujet pour les premiers tests et les envois techniques, idealement `accueil@gti-immobilier.fr`.
- `GOOGLE_WORKSPACE_SCOPES` : scopes autorises separes par virgule.

Scopes initiaux conseilles avant les agents IA :

```text
https://www.googleapis.com/auth/gmail.send,
https://www.googleapis.com/auth/calendar.freebusy,
https://www.googleapis.com/auth/calendar.events
```

Les scopes de lecture Gmail (`gmail.metadata`, `gmail.readonly`) doivent rester une phase ulterieure, apres cadrage RGPD et journalisation.

Important : pour les rendez-vous Agenda, le backend devra deleguer au compte Google du negociateur concerne, pas uniquement au compte `accueil`. Le compte `accueil` sert surtout aux notifications et aux tests techniques.

## Demarrage local

```powershell
cd C:\Users\frede\Desktop\Projet\backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Note :

- les endpoints Hektor reutilisent volontairement les scripts Python existants dans `phase2/sync/`
- l'objectif est de garder le comportement du mode local, pas de le reinventer
