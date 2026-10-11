-- ═══════════════════════════════════════════════════════════════════════════════
-- PURGER 24 TRAVAUX EN ERREUR -- AUCUN N'EST UN REFUS DE HEKTOR   11/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Aucun redemarrage, aucun deploiement.
--
-- ─── POURQUOI ───────────────────────────────────────────────────────────────────
-- 24 travaux sont en erreur, et l'alarme `data.travaux_en_erreur` (seuil 0) est
-- rouge. Un travail en erreur n'est JAMAIS rejoue, et la regle a une raison
-- precise, ecrite dans enqueue_empreinte_lot.js :
--     « job en erreur sur cette annonce -> NE JAMAIS REJOUER
--       (les 403 repetes ont fait bannir l'IP) »
--
-- ⭐ LA REGLE PROTEGE CONTRE UN REFUS DE HEKTOR. Or aucun de ces 24 n'en est un.
--    Les 24, lus un par un le 11/10 :
--
--     12  refresh_console_data           TypeError ligne["ann"]            05/10
--             ✅ DEJA CORRIGE le 06/10 (3607d29, acces par position).
--                Ce sont des traces d'AVANT le correctif.
--                notice/CHANTIER_EN_ATTENTE_MANDAT_2026-10-06.md, partie 5.
--      6  update_hektor_contact (5)      contact fantome 145561           09/10
--         + update_hektor_mandant_contact (1)
--             « Formulaire edition contact Hektor introuvable pour 145561 » : le
--             contact N'EXISTE PLUS chez Hektor. Sujet REPORTE par Frederic le
--             09/10. La purge n'y change rien (voir GARDE-FOU 3).
--      3  refresh_console_data (2)       « database is locked »      01, 05, 08/10
--         + refresh_console_contact_data (1)
--             ⚠ MEME CAUSE QUE 2 DES 15 PURGES LE 01/10 : ELLE REVIENT. Le
--               correctif (le `busy_timeout` manquant sur pull_from_supabase.py)
--               est note depuis le 06/10. La purge eteint l'alarme, PAS la cause.
--      1  refresh_console_data           timeout apres 90 000 ms (58931)  09/10
--      1  sync_console_documents         document non servi par Hektor    09/10
--             bien 24148 -- et c'est LUI que la purge libere (voir plus bas).
--      1  unlink_hektor_mandant          retrait NON PROUVE               03/10
--             contact 603953, annonce 62964. « Non prouve » n'est pas « non
--             fait » : le worker exige une confirmation de l'API et ne l'a pas eue.
--     --------------------------------------------------------------------
--      0  403 de Hektor            VERIFIE le 11/10 (403/banni/forbidden/rate
--                                  limit : 0 sur 24), et le GARDE-FOU 1 le REVERIFIE
--
-- CE QUE LA PURGE REND : les annonces redeviennent eligibles au rattrapage
-- (l'exclusion porte sur `status = error`). Sans elle, le bien 24148 et son
-- document ne seraient PLUS JAMAIS scannes -- punis a vie pour une panne du 09/10
-- qui n'etait pas la leur.
--
-- CE QUE LA PURGE N'ETEINT PAS : il reste deux alarmes critical, et ce sont LA
-- MEME LIGNE -- `data.contact_conflit` et `data.contact_push_bloque`, le contact
-- fantome en attente (conflict = true, push_attempts = 5). Tant qu'elles sont la,
-- AUCUN mail « retour a la normale » ne peut partir : la regle d'envoi exige ZERO
-- critical (check_gti_health.py:2843).
--
-- ⚠ CE QUE LA PURGE EMPORTE AUSSI : app_console_job_log.job_id est en CASCADE.
--   179 lignes de journal detaille partiront avec les 24 travaux. Le resume, lui,
--   reste dans app_console_job_error_archive -- et, DIFFERENCE AVEC LE 01/10, on y
--   ecrit le MESSAGE D'ERREUR ENTIER et non ses 150 premiers caracteres, puisque
--   la colonne `motif` est un `text` sans limite. On garde donc plus de trace
--   qu'au geste precedent.
--
-- ─── LE PRECEDENT ───────────────────────────────────────────────────────────────
-- Ce geste a deja ete fait DEUX FOIS : le 21/08/2026 (214 lignes archivees) et le
-- 01/10/2026 (15 travaux, patch_purge_erreurs_infra_2026-10-01.sql). Meme table
-- d'archive, meme methode, memes garde-fous.
--
-- ─── RETOUR ARRIERE ─────────────────────────────────────────────────────────────
-- Les travaux supprimes ne reviennent pas, MAIS rien d'exploitable n'est perdu :
-- leur motif ENTIER, leur type, combien et leurs premiere/derniere occurrences
-- restent dans app_console_job_error_archive, et les annonces seront rescannees.
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
  IF combien <> 24 THEN
    RAISE EXCEPTION 'ARRET : % travaux en erreur, 24 attendus. Des erreurs neuves '
                    'sont apparues : les examiner avant de purger.', combien;
  END IF;
END $$;

-- ⛔ GARDE-FOU 3, NEUF LE 11/10 : AUCUN GESTE NE DOIT REPARTIR.
--   Une saisie en attente est relancee par la barriere du 5b tant qu'elle a
--   `conflict = false` (patch_5b_barriere_attente_2026-09-21.sql l. 44). Si une
--   ligne pointait un travail purge SANS etre en conflit, la purge pourrait la
--   faire repartir -- et rejouer un geste irreparable. Mesure du 11/10 : 1 ligne
--   pointe un travail purge, et elle est EN CONFLIT (donc parquee). On le reverifie.
DO $$
DECLARE repartirait int;
BEGIN
  SELECT count(*) INTO repartirait
    FROM public.app_contact_pending p
    JOIN public.app_console_job j ON j.id = p.push_job_id
   WHERE j.status = 'error' AND p.conflict IS NOT TRUE;
  IF repartirait > 0 THEN
    RAISE EXCEPTION 'ARRET : % saisie(s) en attente repartirait(ent) apres la purge '
                    '(conflict = false). Les examiner avant.', repartirait;
  END IF;
END $$;

-- ① LE RESUME PART A L'ARCHIVE, un par (type, motif ENTIER).
INSERT INTO public.app_console_job_error_archive (purge_at, job_type, motif, combien, premier, dernier)
SELECT now(), job_type, coalesce(error_message, ''),
       count(*), min(created_at), max(created_at)
  FROM public.app_console_job
 WHERE status = 'error'
 GROUP BY job_type, coalesce(error_message, '');

-- ② LES TRAVAUX S'EN VONT (et leurs 179 lignes de journal, par CASCADE).
DELETE FROM public.app_console_job WHERE status = 'error';

-- ⛔ GARDE-FOU 4 : apres le geste, plus aucune erreur, et l'archive a grossi.
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
  RAISE NOTICE 'OK : 0 travail en erreur, % ligne(s) archivee(s) a l''instant.', archive;
END $$;

COMMIT;

-- ─── A LIRE APRES LE COMMIT ─────────────────────────────────────────────────────
-- SELECT count(*) FROM public.app_console_job WHERE status = 'error';   -- doit valoir 0
--
-- SELECT purge_at, job_type, combien, left(motif, 90) AS motif
--   FROM public.app_console_job_error_archive
--  WHERE purge_at::date = current_date ORDER BY combien DESC;
--
-- IL RESTERA 2 CRITICAL, et c'est NORMAL : le contact fantome en attente
-- (`data.contact_conflit` et `data.contact_push_bloque`, la meme ligne).
-- ⏰ Le mail « retour a la normale » ne partira que quand les TROIS seront a zero.
--
-- Puis, des le rattrapage de 21 h, le bien 24148 repassera dans la file --
-- l'exclusion « job en erreur » ne l'ecarte plus.
