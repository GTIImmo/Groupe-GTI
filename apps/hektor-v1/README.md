# Hektor V1

Squelette React/Vite de la future application.

## Positionnement

Ce front lit le schema applicatif Supabase V1, pas les tables Hektor.

Tables / vues ciblees :

- `app_dashboard_v1`
- `app_dossiers_current`
- `app_work_items_current`

## Demarrage

1. Installer les dependances
2. Copier `.env.example` vers `.env`
3. Renseigner les variables Supabase
4. Avoir un utilisateur `auth.users` actif dans Supabase
5. Avoir une ligne correspondante dans `public.app_user_profile`
6. Lancer `npm run dev`

## Etat actuel

- dashboard simple
- liste dossiers
- lignes dossiers cliquables
- fiche dossier V1
- file de travail
- fallback local si Supabase n'est pas configure
- ecran de connexion si Supabase est configure
- lecture reelle des vues seulement apres session utilisateur valide
