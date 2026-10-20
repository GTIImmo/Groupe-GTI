-- ═══════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE DE LA PIECE ④ -- on retire exit_hektor_draft_annonce des 3 verrous
--                                                                    20/10/2026
-- ⚠ IL NE JUGE QUE SA PART (lecon 31) : il ne touche QUE ce que le patch a ajoute.
-- ⛔ SOLDER D'ABORD les travaux de ce type qui attendent, sinon ils resteraient
--   orphelins (plus personne ne les reclamerait) :
--     update public.app_console_job set status='error', finished_at=now(),
--            error_message='Annule : retour arriere de la piece 4 (20/10/2026)'
--      where job_type='exit_hektor_draft_annonce' and status in ('pending','running');
-- ⚠ Une annonce DEJA sortie du brouillon chez Hektor le reste : ce retour arriere
--   ne defait pas les gestes faits, il ferme la porte. Pour refaire un brouillon,
--   c'est etatAnnonce = 2 chez Hektor, a la main.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
DECLARE
    src     text;
    ancre   text := $a$, 'exit_hektor_draft_annonce'::text$a$;
    combien int;
BEGIN
    SELECT replace(pg_get_constraintdef(oid), chr(13), '')
      INTO src FROM pg_constraint WHERE conname = 'app_console_job_job_type_check';
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien = 0 THEN
        RAISE NOTICE 'VERROU 1 : rien a retirer.';
    ELSIF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : ancre vue %s fois dans la contrainte.', combien);
    ELSE
        EXECUTE 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
        EXECUTE 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check '
                || replace(src, ancre, '');
    END IF;
END
$garde$;

DO $garde$
DECLARE
    src     text;
    ancre   text;
    combien int;
BEGIN
    -- ⚠ lecon 30 : ancre MULTI-LIGNE -> on la normalise, sinon un fichier passe en
    --   CRLF ne retirerait RIEN en se croyant deja fait.
    ancre := replace($a$    -- ⑦ piece ④ (20/10/2026) : sortir du brouillon est un deplacement STRUCTUREL
    --   du bien, comme l'archivage et le changement de statut. Meme reserve.
    if target_job_type in ('archive_hektor_annonce', 'change_hektor_annonce_status', 'exit_hektor_draft_annonce') then$a$,
                    chr(13), '');
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_can_request_job';
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien = 0 THEN
        RAISE NOTICE 'VERROU 2 : rien a retirer.';
    ELSIF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : ancre vue %s fois dans can_request_job.', combien);
    ELSE
        EXECUTE replace(src, ancre,
            $b$    if target_job_type in ('archive_hektor_annonce', 'change_hektor_annonce_status') then$b$);
    END IF;
END
$garde$;

DO $garde$
DECLARE
    src     text;
    ancre   text := $a$,'exit_hektor_draft_annonce',$a$;
    combien int;
BEGIN
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_claim_next_job';
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien = 0 THEN
        RAISE NOTICE 'VERROU 3 : rien a retirer.';
    ELSIF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : ancre vue %s fois dans claim_next_job.', combien);
    ELSE
        EXECUTE replace(src, ancre, ',');
    END IF;
END
$garde$;

-- ── LE CONTROLE DU RETOUR : aucune trace, et rien d'autre n'a bouge ──────────
SELECT 1 AS "#", 'aucune trace dans la contrainte' AS controle,
       CASE WHEN (SELECT position('exit_hektor_draft_annonce' in pg_get_constraintdef(oid)) = 0
                    FROM pg_constraint WHERE conname = 'app_console_job_job_type_check')
            THEN 'OK' ELSE '⛔ IL EN RESTE' END AS verdict
UNION ALL SELECT 2, 'aucune trace dans can_request_job',
       CASE WHEN (SELECT position('exit_hektor_draft_annonce' in prosrc) = 0
                    FROM pg_proc WHERE proname = 'app_console_can_request_job')
            THEN 'OK' ELSE '⛔ IL EN RESTE' END
UNION ALL SELECT 3, 'aucune trace dans claim_next_job',
       CASE WHEN (SELECT position('exit_hektor_draft_annonce' in prosrc) = 0
                    FROM pg_proc WHERE proname = 'app_console_claim_next_job')
            THEN 'OK' ELSE '⛔ IL EN RESTE' END
UNION ALL SELECT 4, 'TEMOIN INVERSE -- archivage et statut toujours reserves admin',
       CASE WHEN (SELECT position('archive_hektor_annonce' in prosrc) > 0
                     AND position('change_hektor_annonce_status' in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_can_request_job')
            THEN 'OK' ELSE '⛔ J''AI CASSE AUTRE CHOSE' END
UNION ALL SELECT 5, 'TEMOIN INVERSE -- le detail brouillon (piece ②) est intact',
       CASE WHEN (SELECT position('prepare_brouillon_annonce_detail' in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_claim_next_job')
            THEN 'OK' ELSE '⛔ J''AI CASSE LA PIECE 2' END
ORDER BY 1;

COMMIT;
