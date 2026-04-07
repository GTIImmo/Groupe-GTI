# Note pagination + detail React / Supabase

## Objet

Faire evoluer l'app React V1 pour :

- sortir du chargement limite a `200` lignes locales
- utiliser des requetes Supabase filtrees et paginees
- reintroduire une page `Annonce complete` proche de l'ancienne app HTML

## Changements realises

### Front React

Fichiers modifies :

- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/types.ts`
- `apps/hektor-v1/src/styles.css`
- `apps/hektor-v1/src/lib/mockData.ts`

Effets :

- navigation par ecrans : `Dashboard`, `Stock`, `Annonce`
- pagination serveur des dossiers
- pagination serveur des work items
- filtres envoyes a Supabase au lieu de filtrer uniquement un echantillon local
- chargement detail dossier a la demande via `app_dossiers_current`
- nouvelle page `Annonce complete` avec :
  - hero de synthese
  - galerie photo
  - descriptifs riches
  - fiche bien
  - bloc transaction
  - bloc pilotage CRM
  - mandat / valorisation
  - contacts proprietaires
  - demandes liees

### Sync phase 2 -> Supabase

Fichiers modifies :

- `phase2/sync/export_app_payload.py`
- `phase2/sync/push_to_supabase.py`
- `supabase/schema_v1.sql`

Effets :

- ajout d'un champ `detail_payload_json` dans le payload dossier
- ce champ embarque le detail riche issu de `app_view_generale`
- la sync le pousse ensuite vers `public.app_dossier_v1`

## Verification faite

- build React OK :
  - `npm.cmd run build`
- regeneration locale du payload OK :
  - `phase2/sync/export_app_payload.py --limit 1`
- presence verifiee de `detail_payload_json` dans le payload local

## Action manuelle restante dans Supabase

Le projet Supabase distant doit recevoir la nouvelle colonne avant la prochaine sync.

SQL a executer dans `SQL Editor` :

```sql
alter table public.app_dossier_v1
    add column if not exists detail_payload_json text;
```

## Commandes a relancer apres le SQL

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_to_supabase.py
cd C:\Users\frede\Desktop\Projet\apps\hektor-v1
npm.cmd run dev
```

Puis recharger le navigateur avec `Ctrl + F5`.

## Resultat attendu apres sync

- le stock React reste pagine
- les filtres couvrent le parc Supabase
- le bouton / ecran `Annonce` affiche un detail riche alimente par `detail_payload_json`

## Point de vigilance

Le detail riche depend maintenant de la presence de `detail_payload_json` dans Supabase.
Si la colonne n'est pas ajoutee puis resynchronisee, la page `Annonce` reste structurellement visible mais pauvre en contenu detaille.
