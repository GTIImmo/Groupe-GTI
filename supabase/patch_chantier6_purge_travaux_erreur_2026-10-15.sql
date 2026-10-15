-- ═══════════════════════════════════════════════════════════════════════════════
-- LE VRAI PATCH — purge des travaux documents en erreur     15/10/2026, chantier 6
-- ═══════════════════════════════════════════════════════════════════════════════
-- ⛔ A COLLER SEULEMENT APRES :
--     1. la repetition (…_REPETITION.sql) avec le bon message ;
--     2. ⚠ LE REDEMARRAGE DES 4 SERVICES WORKER — sinon l'annonce 61439 retombera en
--        erreur au prochain passage (son document s'appelle « .67-carnetentretien4 » :
--        un nom qui commence par un point, refuse par Supabase Storage ; corrige dans
--        storageSafeFilename le 15/10, actif seulement apres redemarrage).
--
-- CE QUE CA FAIT, et pourquoi c'est autorise : la sentinelle `data.travaux_en_erreur`
-- (seuil 0, critical) dit « soit on rejoue, soit on PURGE EN ECRIVANT POURQUOI ». Les
-- trois causes sont ecrites dans la repetition et dans la note du chantier.
-- ⭐ Effacer la ligne ne fait pas que taire l'alerte : le composeur de lot exclut « pour
--    toujours » toute annonce portant un travail en erreur. La retirer REND l'annonce
--    eligible -- 47824 (vendus/clos), 61439 et 62899 (parc vivant) repasseront donc.
--
-- RETOUR ARRIERE : patch_chantier6_purge_travaux_erreur_2026-10-15_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════════
begin;
set local statement_timeout = '30s';

-- La sauvegarde datee, AVANT de detruire. On la nettoiera quand le sujet sera clos.
create table if not exists public.app_console_job_erreurs_avant_purge_2026_10_15 as
select * from public.app_console_job
 where job_type = 'sync_console_documents' and status = 'error';

delete from public.app_console_job
 where job_type = 'sync_console_documents' and status = 'error';

-- Le compte rendu : ce qui a ete garde, ce qui reste.
select (select count(*) from public.app_console_job_erreurs_avant_purge_2026_10_15) as lignes_sauvegardees,
       (select count(*) from public.app_console_job
         where job_type = 'sync_console_documents' and status = 'error') as en_erreur_restants;

commit;
