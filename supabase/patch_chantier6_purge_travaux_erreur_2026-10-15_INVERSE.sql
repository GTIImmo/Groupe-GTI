-- ═══════════════════════════════════════════════════════════════════════════════
-- L'INVERSE — remettre les travaux en erreur qui avaient ete purges   15/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Remet exactement les lignes gardees par la sauvegarde datee, et seulement celles
-- qui ne sont pas deja revenues (`not exists` sur l'id) -- pour qu'un double collage
-- ne casse rien.
--
-- ⚠ Apres cet inverse, les annonces concernees redeviennent EXCLUES du rattrapage
--   (« on ne rejoue jamais »), et l'alerte `data.travaux_en_erreur` repart en rouge.
--   C'est l'etat d'avant, rendu a l'identique.
-- ═══════════════════════════════════════════════════════════════════════════════
begin;
set local statement_timeout = '30s';

insert into public.app_console_job
select s.*
  from public.app_console_job_erreurs_avant_purge_2026_10_15 s
 where not exists (select 1 from public.app_console_job j where j.id = s.id);

select (select count(*) from public.app_console_job
         where job_type = 'sync_console_documents' and status = 'error') as en_erreur_apres_retour;

commit;

-- Et quand le sujet sera definitivement clos, on nettoie la sauvegarde :
--   drop table public.app_console_job_erreurs_avant_purge_2026_10_15;
