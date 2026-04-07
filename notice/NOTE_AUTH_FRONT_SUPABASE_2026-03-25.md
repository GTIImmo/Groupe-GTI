# Note auth front Supabase

Date: 25/03/2026

## Objet

Documenter le comportement du front React une fois branche sur Supabase avec RLS active.

## Point important

Le front ne peut pas lire les vues applicatives avec la seule `publishable key`.

Pourquoi :

- les tables Supabase sont protegees par RLS
- les policies verifient qu'un utilisateur authentifie et actif existe
- donc un visiteur anonyme ne doit pas voir les donnees

## Decision retenue

Le front React ne retombe plus silencieusement sur les mocks quand Supabase est configure.

Comportement retenu :

- si Supabase n'est pas configure : mode maquette locale
- si Supabase est configure mais sans session : ecran de connexion
- si session valide : chargement des vues Supabase

## Preconditions pour acceder aux donnees

Il faut :

1. un utilisateur dans `auth.users`
2. une ligne correspondante dans `public.app_user_profile`
3. `is_active = true`

## Fichiers modifies

- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/lib/supabase.ts`
- `apps/hektor-v1/src/styles.css`

## Effet pratique

Le front est maintenant aligne avec la securite reelle du schema Supabase.

On evite ainsi :

- de croire que le front lit les vraies donnees alors qu'il affiche des mocks
- de masquer un probleme RLS ou Auth derriere un fallback silencieux
