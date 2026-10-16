-- ═══════════════════════════════════════════════════════════════════════════════
-- PURGER 4 TRAVAUX EN ERREUR SUR LE BIEN D'ESSAI 24933          15/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'editeur SQL Supabase.
-- Aucun redemarrage, aucun deploiement. Meme patron que le 11/10.
--
-- ─── POURQUOI, ET POURQUOI FREDERIC NE POUVAIT PAS LES CLIQUER ─────────────────
-- Le bandeau de l'ecran affiche bien ces 4 gestes, avec ses deux boutons. Mais le
-- CLIC est refuse : app_action_resolve passe derriere app_console_can_request_job,
-- qui appelle app_console_can_access_dossier -- et cette garde NE CONNAIT QUE
-- L'INDEX VIVANT. Mesure du 15/10 :
--
--     annonce 61672   dans app_dossier_current  « Sous offre »   -> clic OK (fait a 09:15)
--     annonce 62963   dans app_dossier_current  « Actif »        -> clic OK (fait a 09:16)
--     annonce 24933   ABSENTE de app_dossier_current             -> ⛔ CLIC REFUSE
--
-- ⚠ C'EST UN DEFAUT DE FOND, ET IL N'EST PAS CORRIGE ICI : une annonce sortie de
--   l'index vivant rend son geste IMPOSSIBLE A CLORE -- donc l'alarme
--   `data.travaux_en_erreur` (seuil 0, critical) devient ETERNELLE. Le jour ou ce
--   sera une vraie annonce vendue, le blocage sera le meme.
--   ⛔ ET LA CORRECTION EVIDENTE EST DANGEREUSE : elargir
--     app_console_can_access_dossier, c'est ouvrir LA PORTE DE 12 FONCTIONS,
--     DONT 10 D'ECRITURE (mesure du 14/10, chantier 6a-bis). A traiter a part.
--
-- ─── LES 4, LUS UN PAR UN LE 15/10 ─────────────────────────────────────────────
--   tous      job_type = change_hektor_annonce_status  (vers « compromise »)
--   tous      hektor_annonce_id = '24933', app_dossier_id = 1352132
--   tous      requested_by = NULL  -> AUCUN HUMAIN ne les a demandes, c'est un script
--   tous      attempt_count = 5    -> le worker a epuise ses reprises (13:13 -> 13:15)
--   tous      « Assistant Sous compromis : l'ouverture n'a rendu aucun panier »
--   payloads  compromis_id 50078, numero_mandat 11939, montants 177000 / 178000
--
--   ⭐ 24933 EST UN BIEN D'ESSAI, et le projet le dit : « 24933 = le bien d'essai
--     des taches 3.2 / 3.4 » (4 fichiers SUPPRESSION_ESSAIS*). Ce ne sont pas des
--     gestes de production perdus.
--
-- ⭐ GARDE-FOU DU PROJET, REVERIFIE : aucun n'est un REFUS DE HEKTOR.
--   La regle (enqueue_empreinte_lot.js) : « job en erreur sur cette annonce ->
--   NE JAMAIS REJOUER (les 403 repetes ont fait bannir l'IP) ». Mesure du 15/10 :
--   0 sur 4 porte 403 / banni / forbidden / rate limit. Le GARDE-FOU 1 le reverifie.
--
-- ⚠ CE QUE LA PURGE EMPORTE AUSSI : app_console_job_log.job_id est en CASCADE.
--   156 lignes de journal detaille partiront (39 par travail). Le resume reste
--   dans app_console_job_error_archive, avec le message d'erreur ENTIER.
--
-- ⚠ CE QU'ELLE NE PURGE PAS : les 2 autres travaux en erreur (61672 du 13/10 et
--   62963 du 14/10). Frederic les a deja tranches a l'ecran ce matin : ils ne
--   comptent plus dans l'alarme, et ils restent comme HISTORIQUE. On n'y touche pas.
--
-- ─── RETOUR ARRIERE ────────────────────────────────────────────────────────────
-- ⛔ IL N'Y EN A PAS : une suppression ne se defait pas. C'est pourquoi le resume
--    est archive AVANT, et pourquoi les 4 ont ete lus un par un. Leur contenu
--    entier figure dans le compte rendu de la session du 15/10.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ⚠⚠ LE TYPE DE hektor_annonce_id N'EST PAS LE MEME PARTOUT -- panne du 15/10 :
--      app_console_job.hektor_annonce_id        text     <- ICI, donc '24933'
--      app_dossier_current.hektor_annonce_id    bigint   <- la, 24933 sans quotes
--    La premiere version de ce patch comparait a un entier et tombait sur
--    « operator does not exist: text = integer ». PostgREST, lui, convertit tout
--    seul (eq.24933 marchait) -- d'ou le piege : la sonde passe, le SQL casse.
-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU 1 : PAS UN SEUL REFUS DE HEKTOR dans le lot.
-- ---------------------------------------------------------------------
DO $garde$
DECLARE n integer;
BEGIN
  SELECT count(*) INTO n
    FROM public.app_console_job
   WHERE status = 'error' AND hektor_annonce_id = '24933'
     AND (lower(coalesce(error_message, '')) LIKE '%403%'
       OR lower(coalesce(error_message, '')) LIKE '%banni%'
       OR lower(coalesce(error_message, '')) LIKE '%forbidden%'
       OR lower(coalesce(error_message, '')) LIKE '%rate limit%'
       OR lower(coalesce(error_message, '')) LIKE '%too many%');
  IF n > 0 THEN
    RAISE EXCEPTION 'ARRET : % travail(aux) portent un refus de Hektor. La regle '
                    'du projet interdit de les purger (les 403 repetes ont fait '
                    'bannir l''IP).', n;
  END IF;
END $garde$;

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU 2 : le compte doit etre celui qu'on a mesure.
--   Si des erreurs NEUVES sont apparues depuis, on s'arrete : elles n'ont
--   pas ete lues, donc on ne les emporte pas en silence.
-- ---------------------------------------------------------------------
DO $garde$
DECLARE n integer;
BEGIN
  SELECT count(*) INTO n FROM public.app_console_job
   WHERE status = 'error' AND hektor_annonce_id = '24933';
  IF n <> 4 THEN
    RAISE EXCEPTION 'ARRET : % travaux en erreur sur 24933, 4 attendus. Des '
                    'erreurs neuves sont apparues : les relire avant de purger.', n;
  END IF;
END $garde$;

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU 3 : aucun de ces travaux ne doit avoir ete DEMANDE PAR UN HUMAIN.
--   Un geste d'un negociateur se tranche a l'ecran, il ne se purge pas.
-- ---------------------------------------------------------------------
DO $garde$
DECLARE n integer;
BEGIN
  SELECT count(*) INTO n FROM public.app_console_job
   WHERE status = 'error' AND hektor_annonce_id = '24933'
     AND requested_by IS NOT NULL;
  IF n > 0 THEN
    RAISE EXCEPTION 'ARRET : % travail(aux) ont ete demandes par un humain. '
                    'Ils se tranchent a l''ecran, pas par une purge.', n;
  END IF;
END $garde$;

-- ---------------------------------------------------------------------
-- 1. LA TRACE D'ABORD -- on n'efface jamais sans resume
-- ---------------------------------------------------------------------
INSERT INTO public.app_console_job_error_archive
       (purge_at, job_type, motif, combien, premier, dernier)
SELECT now(), job_type, coalesce(error_message, ''),
       count(*), min(created_at), max(created_at)
  FROM public.app_console_job
 WHERE status = 'error' AND hektor_annonce_id = '24933'
 GROUP BY job_type, coalesce(error_message, '');

-- ---------------------------------------------------------------------
-- 2. LE GESTE
-- ---------------------------------------------------------------------
DELETE FROM public.app_console_job
 WHERE status = 'error' AND hektor_annonce_id = '24933';

-- ---------------------------------------------------------------------
-- ⛔ GARDE-FOU 4 : apres le geste, plus rien sur 24933, l'archive a grossi,
--   et les 2 travaux deja tranches sont INTACTS.
-- ---------------------------------------------------------------------
DO $garde$
DECLARE reste integer; archive integer; autres integer;
BEGIN
  SELECT count(*) INTO reste FROM public.app_console_job
   WHERE status = 'error' AND hektor_annonce_id = '24933';
  SELECT count(*) INTO archive FROM public.app_console_job_error_archive
   WHERE purge_at > now() - interval '5 minutes';
  SELECT count(*) INTO autres FROM public.app_console_job
   WHERE status = 'error' AND hektor_annonce_id <> '24933';

  IF reste <> 0 THEN
    RAISE EXCEPTION 'Il reste % travaux en erreur sur 24933', reste;
  END IF;
  IF archive = 0 THEN
    RAISE EXCEPTION 'Rien n''a ete archive : on ne supprime pas sans trace';
  END IF;
  IF autres <> 2 THEN
    RAISE EXCEPTION 'Les 2 travaux deja tranches (61672, 62963) devaient rester : '
                    'il y en a %', autres;
  END IF;
  RAISE NOTICE 'OK : 0 erreur sur 24933, % ligne(s) archivee(s), '
               '% autre(s) travail(aux) en erreur conserve(s) (deja tranches).',
               archive, autres;
END $garde$;

-- ─── CONTROLE APRES APPLICATION ────────────────────────────────────────────────
--   SELECT status, count(*) FROM public.app_console_job GROUP BY 1;
--   ATTENDU : error = 2  (61672 et 62963, deja tranches a l'ecran)
--
--   ⚠ L'ALARME `data.travaux_en_erreur` restera ROUGE tant que ces 2-la comptent.
--     Elle les exclut DEJA via app_pending_resolution (correctif du 14/10) :
--     verifier que le prochain passage du moniteur rend bien 0.
