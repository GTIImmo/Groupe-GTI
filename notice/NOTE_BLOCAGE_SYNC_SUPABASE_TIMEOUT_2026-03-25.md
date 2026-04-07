# Note blocage sync Supabase timeout

Date : 25/03/2026

## Objet

Documenter le blocage observe lors de la synchronisation complete `phase2 -> Supabase` apres le recadrage des statuts metier.

## Constat

Le recalcul local phase 2 est correct :

- `A valider` : `15277`
- `Valide` : `80`
- `Diffuse` : `269`
- `Offre recue` : `9`
- `Offre validee` : `920`

Mais la sync complete vers Supabase bloque sur :

- `public.app_dossier_v1`
- erreur serveur : `canceling statement due to statement timeout`

## Tentatives deja faites

### 1. Reduction de la taille de lot

Tests :

- `--batch-size 100`
- `--batch-size 50`
- `--batch-size 20`

Resultat :

- plus de marge
- mais la sync complete reste trop longue ou timeout

### 2. Changement de strategie `upsert -> insert`

Le script `phase2/sync/push_to_supabase.py` a ete modifie pour :

- inserer un nouveau `sync_run_id`
- faire des `insert` simples au lieu d'`upsert` sur les tables volumineuses

Resultat :

- la partie conflit a ete supprimee
- mais le timeout subsiste sur `app_dossier_v1`

## Hypothese la plus probable

`app_dossier_v1` accumule les anciennes syncs.

Comme l'app lit uniquement le `latest_sync_run`, conserver tous les anciens runs dans :

- `app_dossier_v1`
- `app_work_item_v1`
- `app_filter_catalog_v1`
- `app_summary_snapshot`
- `app_sync_run`

fait grossir inutilement les indexes et ralentit l'insertion du run suivant.

## Solution la plus probable

Faire un nettoyage distant des anciennes syncs avant de relancer une sync complete.

### Variante simple

Vider les tables applicatives de sync, puis relancer une sync complete propre.

Ordre logique :

1. nettoyer Supabase
2. relancer `push_to_supabase.py`
3. recharger le front

## SQL cible a executer dans Supabase

```sql
delete from public.app_filter_catalog_v1;
delete from public.app_work_item_v1;
delete from public.app_dossier_v1;
delete from public.app_summary_snapshot;
delete from public.app_sync_run;
```

Si Supabase accepte `truncate`, c'est encore mieux :

```sql
truncate table public.app_filter_catalog_v1 restart identity cascade;
truncate table public.app_work_item_v1 restart identity cascade;
truncate table public.app_dossier_v1 restart identity cascade;
truncate table public.app_summary_snapshot restart identity cascade;
truncate table public.app_sync_run restart identity cascade;
```

## Suite apres nettoyage

Relancer :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_to_supabase.py --batch-size 100
```

Puis :

```powershell
cd C:\Users\frede\Desktop\Projet\apps\hektor-v1
npm.cmd run dev
```

et recharger le navigateur avec `Ctrl + F5`.

## Conclusion

Le blocage actuel n'est plus un probleme de regle metier.

Le blocage est devenu un probleme de volumetrie / persistance des anciens runs dans Supabase.
