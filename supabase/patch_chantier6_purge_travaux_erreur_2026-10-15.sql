-- ═══════════════════════════════════════════════════════════════════════════════
-- LE VRAI PATCH — purge des travaux documents en erreur     15/10/2026, chantier 6
-- ═══════════════════════════════════════════════════════════════════════════════
-- ⛔ A COLLER SEULEMENT APRES :
--     1. la repetition (…_REPETITION.sql), message recopie ;
--     2. ⚠⚠ LE REDEMARRAGE DES 4 SERVICES WORKER.
--        31 des 33 erreurs sont des REFUS DEFINITIFS du coffre (415 type hors liste
--        blanche : .odt, .ods, .html, sans extension ; 413 fichier de plus de 50 Mo).
--        Sans le correctif du 15/10 -- refusDefinitifDuCoffre() + la tolerance armee
--        dans handleSyncConsoleDocuments -- elles RETOMBERONT en erreur des cette nuit
--        et l'alerte reviendra. Avec lui : le document refuse reste sur notre serveur,
--        sa ligne porte une marque durable (metadata_json.cloud_refuse), ses VOISINS
--        sont enfin telecharges et l'annonce va au bout.
--
-- CE QUE CA FAIT, et pourquoi c'est autorise : la sentinelle `data.travaux_en_erreur`
-- (seuil 0, critical) dit « soit on rejoue, soit on PURGE EN ECRIVANT POURQUOI ». Les
-- causes sont ecrites dans la repetition et dans la note du chantier.
-- ⭐ Effacer la ligne ne fait pas que taire l'alerte : le composeur de lot exclut « pour
--    toujours » toute annonce portant un travail en erreur. La retirer REND l'annonce
--    eligible -- c'est le but : ces 33 annonces (dont 30 reveillees par la passe du
--    matin) repasseront et, cette fois, iront au bout.
--
-- ⚠ LE PATCH NE CODE AUCUN CHIFFRE : il purge ce qui est en erreur au moment du collage
--   (le compte peut avoir bouge depuis la mesure de 14:00) et rend le compte rendu.
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

-- Le compte rendu : ce qui a ete garde, dont combien de refus definitifs, et ce qui reste.
select (select count(*) from public.app_console_job_erreurs_avant_purge_2026_10_15) as lignes_sauvegardees,
       (select count(*) from public.app_console_job_erreurs_avant_purge_2026_10_15
         where error_message like '%InvalidMimeType%' or error_message like '%EntityTooLarge%') as dont_refus_definitifs,
       (select count(*) from public.app_console_job
         where job_type = 'sync_console_documents' and status = 'error') as en_erreur_restants;

commit;
