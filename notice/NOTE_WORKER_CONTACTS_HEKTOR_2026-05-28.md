# Worker contacts Hektor - 2026-05-28

## Objectif

Ajouter aux contacts la meme logique applicative que les annonces :

App -> Supabase job securise -> worker local -> Hektor Console -> miroir local -> Supabase leger -> app.

## Flux ajoute

- `create_hektor_contact` : creation d'un contact global Hektor, sans rattachement automatique a une annonce.
- `update_hektor_contact` : modification de l'identite/contact Hektor.
- `refresh_console_contact_data` : relecture ciblee du `ContactById`, normalisation locale, reconstruction de la couche contacts et push Supabase leger.

Le flux cible uniquement le contact cree/modifie. Il ne lance pas le backfill global des 340k contacts.

## Garde-fous

- Les relations mandants des annonces restent gerees par `create_hektor_mandant_contact`, `update_hektor_mandant_contact` et `link_hektor_mandant`.
- La creation/modification globale ne change pas les relations annonce.
- Un verrou de file Supabase evite deux jobs simultanes sur le meme `hektor_contact_id`.
- L'app fait un controle doublon leger avant creation, sans bloquer definitivement l'utilisateur.

## Fichiers principaux

- `Console/console_job_worker.js`
- `phase2/sync/sync_contact_details.py`
- `normalize_source.py`
- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/types.ts`
- `supabase/patch_console_contact_actions_2026-05-28.sql`
