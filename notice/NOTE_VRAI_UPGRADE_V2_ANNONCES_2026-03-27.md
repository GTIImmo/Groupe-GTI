# Note vrai upgrade v2 Annonces

Date: 2026-03-27

## Objet

Documenter la version 2 du script :

- `phase2/sync/push_upgrade_to_supabase.py`

## Ce qui change

Le script ne reconstruit plus tout le payload local par defaut.

Il fonctionne maintenant ainsi :

1. lit le dernier `app_delta_run` `completed`
2. recupere le `source_watermark` memorise dans `notes`
3. detecte les `app_dossier_id` impactes depuis ce watermark
4. exporte seulement ce sous-ensemble local
5. ne lit dans Supabase que les hashes de ces dossiers cibles
6. upsert uniquement les dossiers / details / work items concernes
7. reconstruit le catalogue de filtres seulement s'il y a un vrai changement

## Sources utilisees pour le delta

Le delta est pilote par les vraies sources de changement :

- `hektor.hektor_annonce.date_maj`
- `hektor.hektor_annonce_detail.synced_at`
- `hektor.hektor_mandat.synced_at`
- `hektor.hektor_offre.synced_at`
- `hektor.hektor_compromis.synced_at`
- `hektor.hektor_vente.synced_at`
- `hektor.hektor_annonce_broadcast_state.synced_at`
- `app_note.created_at`
- `app_followup.created_at`
- `app_followup.done_at`
- `app_blocker.detected_at`
- `app_blocker.resolved_at`

## Ce qui est volontairement ignore

Le script n'utilise pas comme signal delta :

- `app_dossier.updated_at`
- `app_internal_status.updated_at`
- `app_work_item.updated_at`

car `bootstrap_phase2.py` les touche massivement et cela ferait remonter tout le stock a chaque run.

## Consequence pratique

- premier run v2 apres migration :
  - si `current` est vide : reconstruction complete normale
  - si `current` est deja rempli mais sans watermark v2 : adoption de baseline sans repush complet
- runs suivants : doivent etre rapides si rien n'a change
- si aucun dossier n'est detecte et qu'il n'y a aucun stale id, le run doit finir quasi immediatement

## Commande

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py
```

Version prudente si besoin :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_upgrade_to_supabase.py --dossier-batch-size 50 --detail-batch-size 25 --work-item-batch-size 50 --filter-batch-size 50
```
