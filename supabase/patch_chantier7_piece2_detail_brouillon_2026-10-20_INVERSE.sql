-- ═══════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE DE LA PIECE ② -- on retire la famille brouillon des 3 verrous
-- et des droits.                                                     20/10/2026
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- ⚠ CE QU'IL FAUT SAVOIR AVANT DE LE COLLER.
--
--   1. UN RETOUR ARRIERE NE JUGE QUE SA PART (lecon 31 du projet). Celui-ci ne
--      touche QUE ce que le patch a ajoute : le type `prepare_brouillon_annonce_detail`
--      dans les 3 verrous, et le 4e bloc de `app_console_can_access_dossier`. Il ne
--      touche NI la table `app_brouillon_annonce_detail_cache` (elle existait avant
--      le patch), NI ses politiques, NI les deux familles soeurs.
--
--   2. ⛔ IL NE SUPPRIME PAS LES LIGNES DE CACHE DEJA POSEES. Elles perimeront
--      toutes seules (24 h) et le front ne les lira plus de toute facon, puisque
--      le bouton ne sera plus la. Pour les retirer tout de suite :
--        delete from public.app_brouillon_annonce_detail_cache;
--      (la politique _delete_admin le permet)
--
--   3. ⚠ DES TRAVAUX « pending » DE CE TYPE RESTERAIENT ORPHELINS : plus personne
--      ne les reclamerait, et la contrainte refuserait d'en creer de nouveaux. Les
--      solder AVANT de coller ceci :
--        update public.app_console_job set status = 'error', finished_at = now(),
--               error_message = 'Annule : retour arriere de la piece 2 (20/10/2026)'
--         where job_type = 'prepare_brouillon_annonce_detail'
--           and status in ('pending', 'running');
--      Sinon la contrainte, qui est NOT VALID, les laissera en place sans erreur --
--      mais ils ne partiront jamais.
--
--   4. Le code (worker, front, script python) reste en place : il devient inerte,
--      puisque le travail ne peut plus etre cree.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── VERROU 1 : la contrainte ──────────────────────────────────────────────────
DO $garde$
DECLARE
    src      text;
    ancre    text := $a$, 'prepare_brouillon_annonce_detail'::text$a$;
    combien  int;
BEGIN
    SELECT replace(pg_get_constraintdef(oid), chr(13), '')
      INTO src FROM pg_constraint WHERE conname = 'app_console_job_job_type_check';
    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : la contrainte est introuvable.';
    END IF;
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien = 0 THEN
        RAISE NOTICE 'VERROU 1 : rien a retirer (le type n''y est pas) -- deja revenu en arriere.';
    ELSIF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois (il en faut 1).', combien);
    ELSE
        EXECUTE 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
        EXECUTE 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check '
                || replace(src, ancre, '');
        RAISE NOTICE 'VERROU 1 retire.';
    END IF;
END
$garde$;

-- ── VERROU 2 : app_console_can_request_job ────────────────────────────────────
DO $garde$
DECLARE
    src     text;
    ancre   text;
    combien int;
BEGIN
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_can_request_job';
    -- ⚠⚠ LECON 30, ET C'EST ICI QUE CA COMPTE LE PLUS : cette ancre est MULTI-LIGNE.
    --   Si ce fichier .sql est en CRLF (git le fait au checkout sous Windows), elle
    --   porterait des CR que la source normalisee n'a pas -> AUCUNE CORRESPONDANCE,
    --   et LE RETOUR ARRIERE NE RETIRERAIT RIEN, en se croyant deja fait.
    ancre := replace($a$
            -- ⑦ piece ② (20/10/2026) : la troisieme soeur. C'est une LECTURE -- elle
            -- reconstruit la fiche depuis NOTRE miroir, sans un seul appel a Hektor.
            'prepare_brouillon_annonce_detail',$a$, chr(13), '');
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien = 0 THEN
        RAISE NOTICE 'VERROU 2 : rien a retirer.';
    ELSIF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois dans can_request_job.', combien);
    ELSE
        EXECUTE replace(src, ancre, '');
        RAISE NOTICE 'VERROU 2 retire.';
    END IF;
END
$garde$;

-- ── VERROU 3 : app_console_claim_next_job ─────────────────────────────────────
DO $garde$
DECLARE
    src     text;
    ancre   text := $a$,'prepare_brouillon_annonce_detail'))$a$;
    combien int;
BEGIN
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_claim_next_job';
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien = 0 THEN
        RAISE NOTICE 'VERROU 3 : rien a retirer.';
    ELSIF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois dans claim_next_job.', combien);
    ELSE
        EXECUTE replace(src, ancre, '))');
        RAISE NOTICE 'VERROU 3 retire.';
    END IF;
END
$garde$;

-- ── LES DROITS : le 4e bloc de app_console_can_access_dossier ─────────────────
DO $garde$
DECLARE
    src     text;
    ancre   text;
    combien int;
BEGIN
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_can_access_dossier';
    -- ⚠⚠ MULTI-LIGNE : on normalise l'ancre elle-meme (lecon 30). Sans ca, un fichier
    --   passe en CRLF ferait echouer le retrait EN SILENCE (« rien a retirer »).
    ancre := replace($a$        )
        -- ⑦ piece ② (20/10/2026) : LE 4e INDEX. Un brouillon n'est dans aucun des
        -- trois ci-dessus, donc un negociateur se voyait refuser la lecture de son
        -- propre brouillon -- en silence, 0 ligne et aucune erreur.
        or exists (
            select 1
            from public.app_brouillon_annonce_index_current target
            where (
                    (target_app_dossier_id is not null and target.app_brouillon_id = target_app_dossier_id)
                 or (nullif(target_hektor_annonce_id, '') is not null and target.hektor_annonce_id::text = target_hektor_annonce_id)
                )
              and lower(coalesce(target.negociateur_email, '')) = lower(coalesce(current_email, ''))
        );$a$, chr(13), '');
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien = 0 THEN
        RAISE NOTICE 'DROITS : rien a retirer.';
    ELSIF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : le 4e bloc apparait %s fois (il en faut 1).', combien);
    ELSE
        EXECUTE replace(src, ancre, '        );');
        RAISE NOTICE 'DROITS retires.';
    END IF;
END
$garde$;

-- ── LE CONTROLE DU RETOUR : AUCUNE TRACE NE DOIT RESTER (lecon 31) ────────────
DO $garde$
DECLARE
    restes text := '';
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'app_console_job_job_type_check'
                 AND position($a$'prepare_brouillon_annonce_detail'$a$ in pg_get_constraintdef(oid)) > 0) THEN
        restes := restes || ' contrainte';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'app_console_can_request_job'
                 AND position($a$'prepare_brouillon_annonce_detail'$a$ in prosrc) > 0) THEN
        restes := restes || ' can_request_job';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'app_console_claim_next_job'
                 AND position($a$'prepare_brouillon_annonce_detail'$a$ in prosrc) > 0) THEN
        restes := restes || ' claim_next_job';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'app_console_can_access_dossier'
                 AND position('app_brouillon_annonce_index_current' in prosrc) > 0) THEN
        restes := restes || ' can_access_dossier';
    END IF;
    IF restes <> '' THEN
        RAISE EXCEPTION '%', format('ARRET : il reste des traces dans :%s -- tout est annule.', restes);
    END IF;

    -- ⚠ ET LES DEUX SOEURS DOIVENT ETRE INTACTES : un retour arriere qui les
    --   emporterait casserait le detail des Archives et des Vendu/Clos.
    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'app_console_claim_next_job'
                     AND position($a$'prepare_archived_annonce_detail'$a$ in prosrc) > 0
                     AND position($a$'prepare_historical_annonce_detail'$a$ in prosrc) > 0) THEN
        RAISE EXCEPTION 'ARRET : les deux familles soeurs ont disparu de claim_next_job -- tout est annule.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'app_console_can_access_dossier'
                     AND position('app_archive_annonce_index_current' in prosrc) > 0
                     AND position('app_historical_annonce_index_current' in prosrc) > 0) THEN
        RAISE EXCEPTION 'ARRET : les index soeurs ont disparu de can_access_dossier -- tout est annule.';
    END IF;

    RAISE NOTICE 'RETOUR ARRIERE COMPLET : aucune trace, et les deux soeurs sont intactes.';
END
$garde$;

COMMIT;

-- ⏰ Puis redemarrer HektorConsoleWorkerDocuments (file vide : 0 pending, 0 running).
