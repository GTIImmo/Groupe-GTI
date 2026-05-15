# Suppression annonce Hektor depuis l'app

## Objectif

Reproduire dans l'app le droit Hektor disponible avec un compte administrateur : supprimer une annonce, y compris active, sans donner ce droit aux comptes commerciaux.

## Principe installe

L'app ne supprime jamais directement dans Hektor. Elle cree un job Supabase `delete_hektor_annonce`.

Flux :

1. Un administrateur ouvre une fiche annonce dans l'app.
2. Le bouton `Supprimer` ouvre une confirmation.
3. La confirmation doit etre exactement `SUPPRIMER {hektor_annonce_id}`.
4. Supabase cree le job via la fonction `app_console_create_delete_annonce_job`.
5. Le PC serveur local lit le job.
6. Le worker force une session Hektor administrateur.
7. Le worker appelle la commande Console :
   `GET /admin/xmlrpc.php?mode=supprimeannonce&id={hektor_annonce_id}&path=undefined`
8. Apres suppression Hektor, le worker nettoie :
   - documents cloud Supabase Storage connus pour cette annonce ;
   - fichiers locaux connus via `metadata_json.local_archive_path` ;
   - lignes Supabase courantes liees a l'annonce ;
   - caches SQLite locaux `data/hektor.sqlite` et `phase2/phase2.sqlite`.
9. Un journal technique est conserve dans `app_console_deleted_annonce_log`.

## Securite

La creation du job est limitee au role applicatif `admin`.

Les managers et commerciaux ne peuvent pas creer `delete_hektor_annonce`.

Le worker reverifie aussi la confirmation dans `payload_json.confirm_text`.

## Fichiers principaux

- `supabase/patch_console_delete_annonce_2026-05-15.sql`
- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/types.ts`
- `Console/console_job_worker.js`
- `phase2/sync/delete_local_annonce.py`

## Important

Le nettoyage Supabase/local est lance seulement apres l'appel de suppression Hektor. Si Hektor refuse la suppression ou si la session admin n'est pas active, les donnees locales ne sont pas nettoyees.
