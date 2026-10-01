-- ═══════════════════════════════════════════════════════════════════════════════
-- PURGER 15 TRAVAUX EN ERREUR -- AUCUN N'EST UN REFUS DE HEKTOR   01/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Aucun redemarrage, aucun deploiement.
--
-- ─── POURQUOI ───────────────────────────────────────────────────────────────────
-- 15 travaux sont en erreur, et l'alarme `data.travaux_en_erreur` (seuil 0) est
-- rouge depuis le 28/09. Un travail en erreur n'est JAMAIS rejoue, et la regle a
-- une raison precise, ecrite dans enqueue_empreinte_lot.js :
--     « job en erreur sur cette annonce -> NE JAMAIS REJOUER
--       (les 403 repetes ont fait bannir l'IP) »
--
-- ⭐ LA REGLE PROTEGE CONTRE UN REFUS DE HEKTOR. Or aucun de ces 15 n'en est un :
--
--     13  sync_console_documents   12 « Supabase 500 » + 1 chien de garde
--                                  (« execution running trop ancienne »)
--      2  refresh_console_data     « database is locked » sur phase2.sqlite
--     --------------------------------------------------------------------
--      0  403 de Hektor            VERIFIE, et le garde-fou ci-dessous le REVERIFIE
--
-- Ce sont des defaillances de NOTRE infrastructure, pendant la collision entre le
-- rattrapage documents de 23 h et le run de 5 h -- collision corrigee le 01/10
-- (rattrapage decale a 22:00, lot ramene a 2 500).
--
-- CE QUE LA PURGE REND : les 13 annonces documents redeviennent eligibles au
-- rattrapage (l'exclusion porte sur `status = error`). Sans elle, elles ne
-- seraient JAMAIS scannees -- punies a vie pour une panne qui n'etait pas la leur.
-- Les 2 autres annonces sont deja a jour (le run de nuit les a rattrapees) : seule
-- l'alarme reste a eteindre.
--
-- ─── LE PRECEDENT ───────────────────────────────────────────────────────────────
-- Ce geste a deja ete fait le 21/08/2026 : meme table d'archive, meme methode --
-- un resume par motif, puis la suppression. 214 lignes y sont deja.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- Les travaux supprimes ne reviennent pas, MAIS rien n'est perdu : leur resume
-- (type, motif, combien, premiere et derniere occurrence) reste dans
-- app_console_job_error_archive, et les annonces seront rescannees.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ⛔ GARDE-FOU 1 : PAS UN SEUL REFUS DE HEKTOR dans le lot.
--   C'est la seule chose que la regle « ne jamais rejouer » protege. Si un 403,
--   un bannissement ou un rejet apparait, on n'y touche pas -- du tout.
DO $$
DECLARE refus int;
BEGIN
  SELECT count(*) INTO refus FROM public.app_console_job
   WHERE status = 'error'
     AND (error_message ILIKE '%403%' OR error_message ILIKE '%banni%'
       OR error_message ILIKE '%forbidden%' OR error_message ILIKE '%rate limit%');
  IF refus > 0 THEN
    RAISE EXCEPTION 'ARRET : % travail(aux) portent un refus de Hektor. La regle '
                    '« ne jamais rejouer » les protege. Aucune purge.', refus;
  END IF;
END $$;

-- ⛔ GARDE-FOU 2 : le compte doit etre celui qu'on a mesure.
--   Si d'autres erreurs sont apparues depuis, elles n'ont pas ete examinees :
--   on s'arrete plutot que de purger ce qu'on n'a pas regarde.
DO $$
DECLARE combien int;
BEGIN
  SELECT count(*) INTO combien FROM public.app_console_job WHERE status = 'error';
  IF combien <> 15 THEN
    RAISE EXCEPTION 'ARRET : % travaux en erreur, 15 attendus. Des erreurs neuves '
                    'sont apparues : les examiner avant de purger.', combien;
  END IF;
END $$;

-- ① LE RESUME PART A L'ARCHIVE, un par (type, motif).
INSERT INTO public.app_console_job_error_archive (purge_at, job_type, motif, combien, premier, dernier)
SELECT now(), job_type, left(coalesce(error_message, ''), 150),
       count(*), min(created_at), max(created_at)
  FROM public.app_console_job
 WHERE status = 'error'
 GROUP BY job_type, left(coalesce(error_message, ''), 150);

-- ② LES TRAVAUX S'EN VONT.
DELETE FROM public.app_console_job WHERE status = 'error';

-- ⛔ GARDE-FOU 3 : apres le geste, plus aucune erreur, et l'archive a grossi.
DO $$
DECLARE reste int; archive int;
BEGIN
  SELECT count(*) INTO reste FROM public.app_console_job WHERE status = 'error';
  SELECT count(*) INTO archive FROM public.app_console_job_error_archive
   WHERE purge_at >= now() - interval '1 minute';
  IF reste <> 0 THEN
    RAISE EXCEPTION 'Il reste % travaux en erreur', reste;
  END IF;
  IF archive = 0 THEN
    RAISE EXCEPTION 'Rien n''a ete archive : on ne supprime pas sans trace';
  END IF;
END $$;

COMMIT;

-- ─── A LIRE APRES LE COMMIT ─────────────────────────────────────────────────────
-- SELECT count(*) FROM public.app_console_job WHERE status = 'error';   -- doit valoir 0
-- SELECT purge_at, job_type, motif, combien FROM public.app_console_job_error_archive
--  WHERE purge_at::date = current_date ORDER BY combien DESC;
--
-- Puis, des le rattrapage de 22 h, les 13 annonces documents repasseront dans la
-- file -- l'exclusion « job en erreur » ne les ecarte plus.
