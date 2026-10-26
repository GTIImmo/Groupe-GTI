-- ════════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE DU LOT 3 (A.2 SIGNATURE YOUTRUST)                        26/10/2026
-- ⚠ IL NE JUGE QUE SA PART (lecon 31) : il retire SEULEMENT ce que le patch a ajoute.
-- ⛔ IL NE DETRUIT AUCUNE DONNEE : si une demande ou un avis est deja enregistre, il
--   S'ARRETE (des signatures reelles ne se jettent pas par un retour arriere de structure).
-- ⛔ IL REFUSE s'il reste un travail youtrust_ en attente ou en cours : les solder d'abord
--     update public.app_console_job set status='error', finished_at=now(),
--            error_message='Annule : retour arriere du lot 3 A.2 (26/10/2026)'
--      where job_type like 'youtrust\_%' and status in ('pending','running');
-- ════════════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
BEGIN
    IF EXISTS (SELECT 1 FROM public.app_console_job
                WHERE job_type LIKE 'youtrust\_%' AND status IN ('pending', 'running')) THEN
        RAISE EXCEPTION 'ARRET : des travaux youtrust_ sont en attente ou en cours -- les solder d''abord (voir l''en-tete).';
    END IF;
    IF to_regclass('public.app_signature_request') IS NOT NULL
       AND EXISTS (SELECT 1 FROM public.app_signature_request) THEN
        RAISE EXCEPTION 'ARRET : app_signature_request contient des demandes -- ce retour arriere ne detruit pas de donnees.';
    END IF;
    IF to_regclass('public.app_signature_event') IS NOT NULL
       AND EXISTS (SELECT 1 FROM public.app_signature_event) THEN
        RAISE EXCEPTION 'ARRET : app_signature_event contient des avis -- ce retour arriere ne detruit pas de donnees.';
    END IF;
END
$garde$;

-- ── VERROU 1 : la contrainte ───────────────────────────────────────────────────
DO $garde$
DECLARE
    src     text;
    ancre   text := $a$, 'youtrust_send_signature'::text, 'youtrust_sync_signature'::text, 'youtrust_remind_signer'::text, 'youtrust_cancel_signature'::text, 'youtrust_signing_link'::text$a$;
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

-- ── VERROUS 2 ET 3 : can_request_job et claim_next_job ─────────────────────────
DO $garde$
DECLARE
    ancre   text := $a$'youtrust_send_signature','youtrust_sync_signature','youtrust_remind_signer','youtrust_cancel_signature','youtrust_signing_link',$a$;
    nom     text;
    src     text;
    combien int;
BEGIN
    FOREACH nom IN ARRAY array['app_console_can_request_job', 'app_console_claim_next_job'] LOOP
        SELECT replace(pg_get_functiondef(oid), chr(13), '') INTO src FROM pg_proc WHERE proname = nom;
        combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
        IF combien = 0 THEN
            RAISE NOTICE '%', format('%s : rien a retirer.', nom);
        ELSIF combien <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : ancre vue %s fois dans %s.', combien, nom);
        ELSE
            EXECUTE replace(src, ancre, '');
        END IF;
    END LOOP;
END
$garde$;

-- ── LE COCKPIT : on remet les trois lignes, avec le meme temoin ────────────────
DO $garde$
DECLARE
    src   text;
    avant text;
    apres text;
    a1 text := $a$when 'cancelled' then 'signature annulée' when 'expired' then 'signature expirée' else 'signature' end,$a$;
    b1 text := $b$when 'cancelled' then 'signature annulée' else 'signature' end,$b$;
    a2 text := $a$and (d.metadata_json->'signature'->>'status') in ('signed','pending','cancelled','expired')$a$;
    b2 text := $b$and (d.metadata_json->'signature'->>'status') in ('signed','pending','cancelled')$b$;
    a3 text := $a$and ((d.metadata_json->'signature'->>'procedure_id') is not null or (d.metadata_json->'signature'->>'provider_request_id') is not null$a$;
    b3 text := $b$and ((d.metadata_json->'signature'->>'procedure_id') is not null$b$;
    ancres text[];
    i int;
    combien int;
    trouvees int := 0;
BEGIN
    SELECT replace(pg_get_functiondef('public.app_cockpit_activite(bigint,integer)'::regprocedure), chr(13), '') INTO src;
    ancres := array[a1, a2, a3];
    FOR i IN 1 .. 3 LOOP
        combien := (length(src) - length(replace(src, ancres[i], ''))) / length(ancres[i]);
        IF combien > 1 THEN
            RAISE EXCEPTION '%', format('ARRET : ancre %s vue %s fois dans le cockpit.', i, combien);
        END IF;
        trouvees := trouvees + combien;
    END LOOP;
    IF trouvees = 0 THEN
        RAISE NOTICE 'COCKPIT : rien a retirer.';
        RETURN;
    END IF;
    IF trouvees <> 3 THEN
        RAISE EXCEPTION '%', format('ARRET : seulement %s ancres sur 3 dans le cockpit -- etat inconnu, ne rien toucher.', trouvees);
    END IF;
    SELECT md5(coalesce(string_agg(t::text, '|' ORDER BY x.id, t.at, t.kind, t.lead, t.rest), '')) INTO avant
      FROM (SELECT DISTINCT app_dossier_id AS id FROM public.app_console_document
             WHERE app_dossier_id IS NOT NULL
               AND metadata_json->'signature'->>'status' IN ('signed','pending','cancelled')
               AND coalesce(metadata_json->'signature'->>'provider_request_id', '') = '') x
      CROSS JOIN LATERAL public.app_cockpit_activite(x.id, 100) t;
    EXECUTE replace(replace(replace(src, a1, b1), a2, b2), a3, b3);
    SELECT md5(coalesce(string_agg(t::text, '|' ORDER BY x.id, t.at, t.kind, t.lead, t.rest), '')) INTO apres
      FROM (SELECT DISTINCT app_dossier_id AS id FROM public.app_console_document
             WHERE app_dossier_id IS NOT NULL
               AND metadata_json->'signature'->>'status' IN ('signed','pending','cancelled')
               AND coalesce(metadata_json->'signature'->>'provider_request_id', '') = '') x
      CROSS JOIN LATERAL public.app_cockpit_activite(x.id, 100) t;
    IF avant IS DISTINCT FROM apres THEN
        RAISE EXCEPTION '%', format('ARRET : le fil d''activite ImmoSign a change (avant %s, apres %s).', avant, apres);
    END IF;
END
$garde$;

-- ── LES TABLES ET L'INTERRUPTEUR (vides, verifie plus haut) ────────────────────
DROP TABLE IF EXISTS public.app_signature_event;
DROP TABLE IF EXISTS public.app_signature_request;
DELETE FROM public.app_setting WHERE key = 'signature_youtrust';

-- ── LE CONTROLE DU RETOUR : aucune trace, et rien d'autre n'a bouge ────────────
SELECT 1 AS "#", 'aucune trace dans la contrainte' AS controle,
       CASE WHEN (SELECT position('youtrust_' in pg_get_constraintdef(oid)) = 0
                    FROM pg_constraint WHERE conname = 'app_console_job_job_type_check')
            THEN 'OK' ELSE '⛔ IL EN RESTE' END AS verdict
UNION ALL SELECT 2, 'aucune trace dans can_request_job',
       CASE WHEN (SELECT position('youtrust_' in prosrc) = 0 FROM pg_proc WHERE proname = 'app_console_can_request_job')
            THEN 'OK' ELSE '⛔ IL EN RESTE' END
UNION ALL SELECT 3, 'aucune trace dans claim_next_job',
       CASE WHEN (SELECT position('youtrust_' in prosrc) = 0 FROM pg_proc WHERE proname = 'app_console_claim_next_job')
            THEN 'OK' ELSE '⛔ IL EN RESTE' END
UNION ALL SELECT 4, 'aucune trace dans le cockpit',
       CASE WHEN (SELECT position('provider_request_id' in prosrc) = 0 AND position('signature expirée' in prosrc) = 0
                    FROM pg_proc WHERE proname = 'app_cockpit_activite')
            THEN 'OK' ELSE '⛔ IL EN RESTE' END
UNION ALL SELECT 5, 'tables et interrupteur retires',
       CASE WHEN to_regclass('public.app_signature_request') IS NULL AND to_regclass('public.app_signature_event') IS NULL
             AND NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'signature_youtrust')
            THEN 'OK' ELSE '⛔ IL EN RESTE' END
UNION ALL SELECT 6, 'TEMOIN INVERSE -- relance/annulation ImmoSign intactes',
       CASE WHEN (SELECT position('relance_signature' in prosrc) > 0 AND position('cancel_signature_procedure' in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_claim_next_job')
            THEN 'OK' ELSE '⛔ J''AI CASSE AUTRE CHOSE' END
ORDER BY 1;

COMMIT;
