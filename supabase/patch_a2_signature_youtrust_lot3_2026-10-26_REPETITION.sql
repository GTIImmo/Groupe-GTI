-- ════════════════════════════════════════════════════════════════════════════════
-- REPETITION DU LOT 3 (A.2 SIGNATURE YOUTRUST) -- les controles, APRES le collage 26/10/2026
-- N'ECRIT RIEN : tout se joue dans une transaction ANNULEE a la fin (ROLLBACK). Les
-- « essais » d'ecriture ci-dessous doivent ECHOUER -- c'est ce qu'on verifie.
-- Chaque ligne doit dire OK. Une seule autre valeur = ne PAS continuer, coller l'inverse.
-- ════════════════════════════════════════════════════════════════════════════════

BEGIN;

CREATE TEMP TABLE _rep (n int, controle text, verdict text) ON COMMIT DROP;

-- 1-7 : la structure
INSERT INTO _rep
SELECT 1, 'interrupteur signature_youtrust = off',
       CASE WHEN (SELECT value FROM public.app_setting WHERE key = 'signature_youtrust') = 'off' THEN 'OK' ELSE '⛔ ' || coalesce((SELECT value FROM public.app_setting WHERE key = 'signature_youtrust'), 'ABSENT') END
UNION ALL SELECT 2, 'les deux tables existent, RLS active',
       CASE WHEN (SELECT bool_and(relrowsecurity) FROM pg_class WHERE oid IN ('public.app_signature_request'::regclass, 'public.app_signature_event'::regclass))
            THEN 'OK' ELSE '⛔' END
UNION ALL SELECT 3, 'anon ne lit NI n''ecrit rien',
       CASE WHEN NOT has_table_privilege('anon', 'public.app_signature_request', 'select,insert,update,delete')
             AND NOT has_table_privilege('anon', 'public.app_signature_event', 'select,insert,update,delete')
            THEN 'OK' ELSE '⛔ anon a un droit' END
UNION ALL SELECT 4, 'authenticated : lecture seule (aucune ecriture)',
       CASE WHEN has_table_privilege('authenticated', 'public.app_signature_request', 'select')
             AND NOT has_table_privilege('authenticated', 'public.app_signature_request', 'insert,update,delete')
             AND NOT has_table_privilege('authenticated', 'public.app_signature_event', 'insert,update,delete')
            THEN 'OK' ELSE '⛔' END
UNION ALL SELECT 5, 'contrainte : les 5 types youtrust_',
       CASE WHEN (SELECT (length(d) - length(replace(d, 'youtrust_', ''))) / 9 FROM (SELECT pg_get_constraintdef(oid) d FROM pg_constraint WHERE conname = 'app_console_job_job_type_check') c) = 5
            THEN 'OK' ELSE '⛔' END
UNION ALL SELECT 6, 'claim : les 5 types, DANS la liste du worker documents',
       CASE WHEN (SELECT position('youtrust_send_signature' in s) > position($$worker_kind = 'documents'$$ in s)
                     AND position('youtrust_signing_link' in s) < position($$worker_kind = 'admin'$$ in s)
                     AND (length(s) - length(replace(s, 'youtrust_', ''))) / 9 = 5
                    FROM (SELECT prosrc s FROM pg_proc WHERE proname = 'app_console_claim_next_job') p)
            THEN 'OK' ELSE '⛔' END
UNION ALL SELECT 7, 'cockpit : provider_request_id + « signature expiree »',
       CASE WHEN (SELECT position('provider_request_id' in prosrc) > 0 AND position('signature expirée' in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_cockpit_activite') THEN 'OK' ELSE '⛔' END;

-- 8-12 : LES DROITS, DANS LA PEAU D'UN VRAI NEGOCIATEUR ET D'UN VRAI ADMIN
DO $rep$
DECLARE
    nego   uuid;
    admin  uuid;
    sien   record;
    autre  record;
    ok_sien   boolean;
    ok_autre  boolean;
    ok_admin  boolean;
    t text;
    tous_sien boolean := true;
    insert_refuse boolean := false;
BEGIN
    SELECT id INTO nego  FROM public.app_user_profile WHERE role = 'commercial' AND is_active ORDER BY id LIMIT 1;
    SELECT id INTO admin FROM public.app_user_profile WHERE role = 'admin'      AND is_active ORDER BY id LIMIT 1;
    IF nego IS NULL OR admin IS NULL THEN
        INSERT INTO _rep VALUES (8, 'droits : un negociateur et un admin actifs', '⛔ PAS DE TEMOIN');
        RETURN;
    END IF;

    PERFORM set_config('request.jwt.claims', json_build_object('sub', nego, 'role', 'authenticated')::text, true);
    PERFORM set_config('request.jwt.claim.sub', nego::text, true);
    SELECT m.id, m.hid INTO sien FROM public.app_mes_biens_portefeuille() m(id, hid) WHERE m.id IS NOT NULL LIMIT 1;
    SELECT d.app_dossier_id AS id, d.hektor_annonce_id::text AS hid INTO autre
      FROM public.app_dossiers_current d
     WHERE d.app_dossier_id NOT IN (SELECT m.id FROM public.app_mes_biens_portefeuille() m(id, hid) WHERE m.id IS NOT NULL)
     LIMIT 1;
    IF sien.id IS NULL OR autre.id IS NULL THEN
        INSERT INTO _rep VALUES (8, 'droits : un bien du negociateur et un bien d''un autre', '⛔ PAS DE TEMOIN');
        RETURN;
    END IF;

    FOREACH t IN ARRAY array['youtrust_send_signature','youtrust_sync_signature','youtrust_remind_signer','youtrust_cancel_signature','youtrust_signing_link'] LOOP
        tous_sien := tous_sien AND coalesce(public.app_console_can_request_job(t, sien.id, sien.hid), false);
    END LOOP;
    ok_autre := coalesce(public.app_console_can_request_job('youtrust_send_signature', autre.id, autre.hid), false);
    INSERT INTO _rep VALUES (8,  'negociateur : les 5 types sur SON bien', CASE WHEN tous_sien THEN 'OK' ELSE '⛔ refuse' END);
    INSERT INTO _rep VALUES (9,  'negociateur : REFUSE sur le bien d''un autre', CASE WHEN NOT ok_autre THEN 'OK' ELSE '⛔ ACCEPTE' END);
    INSERT INTO _rep VALUES (10, 'TEMOIN INVERSE -- negociateur : relance ImmoSign toujours permise sur son bien',
        CASE WHEN coalesce(public.app_console_can_request_job('relance_signature', sien.id, sien.hid), false) THEN 'OK' ELSE '⛔ CASSE' END);

    -- un utilisateur connecte ne peut PAS ecrire une demande (seuls worker et fonction le font)
    BEGIN
        SET LOCAL ROLE authenticated;
        INSERT INTO public.app_signature_request (sandbox, document_kind) VALUES (true, 'mandat');
        RESET ROLE;
    EXCEPTION WHEN insufficient_privilege THEN
        insert_refuse := true;
        RESET ROLE;
    END;
    INSERT INTO _rep VALUES (11, 'utilisateur connecte : ecriture d''une demande REFUSEE', CASE WHEN insert_refuse THEN 'OK' ELSE '⛔ ACCEPTEE' END);

    PERFORM set_config('request.jwt.claims', json_build_object('sub', admin, 'role', 'authenticated')::text, true);
    PERFORM set_config('request.jwt.claim.sub', admin::text, true);
    ok_admin := coalesce(public.app_console_can_request_job('youtrust_send_signature', autre.id, autre.hid), false);
    INSERT INTO _rep VALUES (12, 'admin : permis partout', CASE WHEN ok_admin THEN 'OK' ELSE '⛔ refuse' END);
END
$rep$;

SELECT n AS "#", controle, verdict FROM _rep ORDER BY n;

ROLLBACK;
