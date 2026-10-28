-- =============================================================================
--  REPETITION -- controles apres patch_cloture_photos_panne_hektor_2026-10-28.sql
-- =============================================================================
--  Lecture seule. Chaque ligne doit dire VERT.
-- =============================================================================
with lot as (
  select r.payload_json->>'job_id' as job_id
    from public.app_pending_resolution r
   where r.objet = 'geste' and r.resolved_by = 'cloture_panne_hektor_2026-10-28'
)
select '1. 726 clotures posees' as controle,
       case when (select count(*) from lot) = 726 then 'VERT' else 'ROUGE' end as etat,
       (select count(*) from lot)::text as mesure
union all
select '2. chaque cloture vise un travail photos en erreur, une seule fois',
       case when (select count(*) from lot l join public.app_console_job j on j.id::text = l.job_id
                   where j.job_type = 'sync_hektor_photos' and j.status = 'error') = 726
             and (select count(distinct job_id) from lot) = 726 then 'VERT' else 'ROUGE' end,
       (select count(distinct job_id) from lot)::text
union all
select '3. aucune ligne du carnet n''appartenait a ces travaux (rien a defaire)',
       case when (select count(*) from lot l join public.app_console_job j on j.id::text = l.job_id
                    join public.app_annonce_champ_app c on c.app_dossier_id = j.app_dossier_id
                                                       and c.ecrit_le = j.requested_at) = 0
            then 'VERT' else 'ROUGE' end,
       'carnet intact'
union all
select '4. les travaux sont restes en error (historique garde)',
       case when (select count(*) from lot l join public.app_console_job j on j.id::text = l.job_id
                   where j.status <> 'error') = 0 then 'VERT' else 'ROUGE' end,
       'aucun travail modifie'
union all
select '5. aucun des 726 n''est encore en attente d''un humain',
       case when (select count(*) from public.app_en_attente_humain v
                   where v.cause like 'sync_hektor_photos%'
                     and v.depuis >= '2026-10-27 22:00:00+00') = 0 then 'VERT' else 'ROUGE' end,
       (select count(*) from public.app_en_attente_humain)::text || ' en attente au total (attendu : 1, le contact d''essai 20000016)'
union all
select '6. les autres resolutions sont intactes (18 gestes + 3 annonces avant le patch)',
       case when (select count(*) from public.app_pending_resolution
                   where resolved_by is distinct from 'cloture_panne_hektor_2026-10-28') = 21
            then 'VERT' else 'ROUGE' end,
       (select count(*) from public.app_pending_resolution
         where resolved_by is distinct from 'cloture_panne_hektor_2026-10-28')::text;
