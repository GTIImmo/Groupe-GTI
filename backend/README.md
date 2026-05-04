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

## Variables d'environnement

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `APP_BASE_URL`
- `HEKTOR_API_BASE_URL`
- `HEKTOR_CLIENT_ID`
- `HEKTOR_CLIENT_SECRET`
- `HEKTOR_API_VERSION`
- `APPOINTMENT_EMAIL_LOGO_URL` : optionnel, URL de secours du logo si le parametre Supabase `app_setting.appointment_email_logo_url` n'est pas encore present.

## Demarrage local

```powershell
cd C:\Users\frede\Desktop\Projet\backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Note :

- les endpoints Hektor reutilisent volontairement les scripts Python existants dans `phase2/sync/`
- l'objectif est de garder le comportement du mode local, pas de le reinventer
