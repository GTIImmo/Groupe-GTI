# Note correctif RLS app_user_profile

Date: 25/03/2026

## Objet

Documenter le correctif applique apres l'erreur :

- `infinite recursion detected in policy for relation "app_user_profile"`

## Cause

La policy initiale sur `public.app_user_profile` faisait un `select` sur cette meme table pour verifier si l'utilisateur courant etait `admin`.

Exemple de logique fautive :

- policy sur `app_user_profile`
- qui relit `app_user_profile`
- donc recursion RLS

Postgres bloque ce cas avec l'erreur de recursion infinie.

## Correction retenue

La verification de role / activite a ete sortie des policies directes vers des fonctions helper :

- `public.is_app_user_active()`
- `public.is_app_admin()`

Caracteristiques retenues :

- `security definer`
- `set search_path = public`

But :

- eviter la recursion dans les policies
- garder une logique de securite lisible et reutilisable

## Impact schema

Le fichier mis a jour est :

- `supabase/schema_v1.sql`

## SQL minimal a rejouer dans Supabase

```sql
create or replace function public.is_app_user_active()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select exists (
        select 1
        from public.app_user_profile p
        where p.id = auth.uid()
          and p.is_active = true
    );
$$;

create or replace function public.is_app_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select exists (
        select 1
        from public.app_user_profile p
        where p.id = auth.uid()
          and p.role = 'admin'
          and p.is_active = true
    );
$$;

drop policy if exists "profiles_select_self_or_admin" on public.app_user_profile;

create policy "profiles_select_self_or_admin"
on public.app_user_profile
for select
using (
    id = auth.uid()
    or public.is_app_admin()
);
```

## Effet attendu

Apres reexecution de ce bloc :

- plus d'erreur de recursion infinie
- lecture du profil utilisateur possible
- policies des tables applicatives reutilisables sans boucle sur `app_user_profile`
