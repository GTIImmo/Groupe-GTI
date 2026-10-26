-- ════════════════════════════════════════════════════════════════════════════════
-- A.2 SIGNATURE YOUTRUST -- LOT 3 : LES FONDATIONS EN BASE                26/10/2026
-- Plan : notice/PLAN_DEV_SIGNATURE_YOUTRUST_2026-10-26.md (lot 3) · audit :
--        notice/AUDIT_SIGNATURE_YOUTRUST_2026-10-26.md
-- ════════════════════════════════════════════════════════════════════════════════
--
-- CE QUE FAIT CE PATCH -- ADDITIF, ET RIEN NE S'ALLUME :
--   1. l'interrupteur 'signature_youtrust' = 'off' (lu par le front depuis le lot 2) ;
--   2. app_signature_request : une ligne par demande de signature Youtrust ;
--   3. app_signature_event   : chaque avis (webhook) recu, event_id UNIQUE = pas de doublon ;
--   4. lecture des deux tables = LA MEME REGLE QUE LES DOCUMENTS (lecteur global, ou ses
--      biens) ; anon exclu ; ecriture reservee au worker et a la fonction (service_role) ;
--   5. 5 types de travaux, LES TROIS VERROUS (memoire « nouveau-type-de-travail-trois-verrous ») :
--        youtrust_send_signature · youtrust_sync_signature · youtrust_remind_signer ·
--        youtrust_cancel_signature · youtrust_signing_link
--      -> distribues au worker DOCUMENTS ; negociateur : SUR SES BIENS seulement ;
--   6. le fil d'activite du cockpit (app_cockpit_activite) connait aussi les demandes
--      Youtrust (provider_request_id) et le mot « expiree » (decision du 26/10).
--
-- CE QU'IL NE FAIT PAS : aucun worker ne sait encore traiter ces types (lot 4). Un travail
--   pose avant le lot 4 serait mis EN ERREUR visible par le worker, jamais laisse en attente.
--   Personne ne peut en poser : l'interrupteur est eteint et l'ecran ne propose rien.
--   « Signe a la main » n'est PAS touche (D14 : on fait comme avec ImmoSign).
--
-- ⚠ METHODE (celle du chantier 7) : aucune fonction n'est retapee. On lit la definition
--   VIVANTE, on verifie son EMPREINTE (mesuree le 26/10), on verifie que chaque ancre y est
--   UNE SEULE FOIS, on remplace. Ancres sur UNE ligne (lecon 30), textes inseres normalises
--   chr(13). ⛔ SI UNE EMPREINTE A CHANGE (une autre session est passee), LE PATCH S'ARRETE
--   ET N'ECRIT RIEN : redemander une mesure.
-- ⭐ LE COCKPIT SE CONTROLE LUI-MEME : avant et apres, il calcule l'empreinte de TOUTES les
--   lignes d'activite des dossiers qui ont une signature ; si elles different, le patch
--   s'arrete. Une demande ImmoSign ne porte ni provider_request_id ni 'expired' : rien ne
--   doit bouger.
--
-- Retour arriere : ..._INVERSE.sql · Controles : ..._REPETITION.sql
-- Apres : RIEN a redemarrer (aucun worker ne porte encore ces types).
-- ════════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── 0. LA GARDE : jamais deux fois ─────────────────────────────────────────────
DO $garde$
BEGIN
    IF to_regclass('public.app_signature_request') IS NOT NULL
       OR to_regclass('public.app_signature_event') IS NOT NULL THEN
        RAISE EXCEPTION 'ARRET : les tables de signature existent deja -- patch deja applique ?';
    END IF;
    IF EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'signature_youtrust') THEN
        RAISE EXCEPTION 'ARRET : l''interrupteur signature_youtrust existe deja -- patch deja applique ?';
    END IF;
END
$garde$;

-- ── 1. L'INTERRUPTEUR, ETEINT ──────────────────────────────────────────────────
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'signature_youtrust';
-- ETEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'signature_youtrust';
INSERT INTO public.app_setting (key, value, description, updated_at)
VALUES ('signature_youtrust', 'off',
        'A.2 26/10/2026 : on = les mandats et avenants partent en signature par Youtrust (reperes dans le PDF, envoi, suivi, preuves). off = comportement d''avant (ImmoSign via Hektor). La lecture ImmoSign n''est JAMAIS coupee.',
        now());

-- ── 2. LES DEUX TABLES ─────────────────────────────────────────────────────────
CREATE TABLE public.app_signature_request (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    provider                text NOT NULL DEFAULT 'youtrust' CHECK (provider IN ('youtrust')),
    provider_request_id     text UNIQUE,              -- id Youtrust ; NULL tant que la creation n'a pas abouti
    sandbox                 boolean NOT NULL,
    app_console_document_id uuid REFERENCES public.app_console_document (id) ON DELETE SET NULL,
    app_dossier_id          bigint,
    hektor_annonce_id       text,
    document_kind           text NOT NULL CHECK (document_kind IN ('mandat', 'avenant', 'autre')),
    -- le vocabulaire de YOUTRUST (la traduction vers la langue commune est dans metadata_json.signature)
    status                  text NOT NULL DEFAULT 'draft'
                            CHECK (status IN ('draft', 'approval', 'rejected', 'ongoing', 'paused', 'declined',
                                              'expired', 'deleted', 'canceled', 'done', 'failed')),
    -- [{index, role:'mandant'|'mandataire', nom, email, telephone, provider_signer_id, status,
    --   notified_at, link_opened_at, signed_at}] -- dans l'ORDRE des reperes s1..sN+1
    signers                 jsonb NOT NULL DEFAULT '[]'::jsonb,
    external_id             text,                     -- envoye a Youtrust = l'id de notre document
    expiration_at           timestamptz,
    activated_at            timestamptz,
    done_at                 timestamptz,
    canceled_at             timestamptz,
    expired_at              timestamptz,
    signed_storage_path     text,
    proofs                  jsonb NOT NULL DEFAULT '[]'::jsonb,   -- un audit trail par signataire
    last_event_at           timestamptz,
    last_synced_at          timestamptz,
    erreur                  text,
    requested_by            uuid,
    created_at              timestamptz NOT NULL DEFAULT now(),
    updated_at              timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_app_signature_request_dossier  ON public.app_signature_request (app_dossier_id);
CREATE INDEX idx_app_signature_request_document ON public.app_signature_request (app_console_document_id);
-- le rattrapage de nuit (lot 7) ne relit que les demandes non terminees
CREATE INDEX idx_app_signature_request_en_cours ON public.app_signature_request (status)
    WHERE status IN ('draft', 'approval', 'ongoing', 'paused');

CREATE TABLE public.app_signature_event (
    event_id            text PRIMARY KEY,            -- event_id Youtrust, globalement unique
    provider            text NOT NULL DEFAULT 'youtrust' CHECK (provider IN ('youtrust')),
    event_name          text NOT NULL,
    provider_request_id text,
    provider_signer_id  text,
    sandbox             boolean,
    event_time          timestamptz,
    payload             jsonb NOT NULL,
    received_at         timestamptz NOT NULL DEFAULT now(),
    processed_at        timestamptz,
    erreur              text
);
CREATE INDEX idx_app_signature_event_demande  ON public.app_signature_event (provider_request_id, event_time);
CREATE INDEX idx_app_signature_event_a_traiter ON public.app_signature_event (received_at) WHERE processed_at IS NULL;

-- ── 3. LES DROITS : LA REGLE DES DOCUMENTS, ET RIEN POUR anon ──────────────────
ALTER TABLE public.app_signature_request ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_signature_event   ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.app_signature_request FROM anon, authenticated;
REVOKE ALL ON public.app_signature_event   FROM anon, authenticated;
GRANT SELECT ON public.app_signature_request TO authenticated;
GRANT SELECT ON public.app_signature_event   TO authenticated;

-- meme expression que app_console_document_select_scope
CREATE POLICY app_signature_request_select_scope ON public.app_signature_request
    FOR SELECT TO authenticated
    USING ((SELECT public.is_app_global_reader())
           OR app_dossier_id    IN (SELECT m.id  FROM public.app_mes_biens_portefeuille() m(id, hid))
           OR hektor_annonce_id IN (SELECT m.hid FROM public.app_mes_biens_portefeuille() m(id, hid)));

-- un avis se lit si sa demande se lit (la politique de la demande s'applique dans la sous-requete)
CREATE POLICY app_signature_event_select_scope ON public.app_signature_event
    FOR SELECT TO authenticated
    USING (EXISTS (SELECT 1 FROM public.app_signature_request r
                    WHERE r.provider_request_id = app_signature_event.provider_request_id));

-- ── 5. VERROU 2 : can_request_job -- le negociateur SUR SES BIENS ──────────────
-- Les 5 types vont dans la liste « commercial », a cote de la relance et de l'annulation
-- ImmoSign : le perimetre vient de app_console_can_access_dossier. Admin et manager : deja tout.
DO $garde$
DECLARE
    src     text;
    ancre   text := $a$'sync_console_documents','relance_signature','cancel_signature_procedure',$a$;
    combien int;
BEGIN
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_can_request_job';
    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : app_console_can_request_job est introuvable.';
    END IF;
    IF md5(src) <> '8b2c43784957e08986786d70ac853a05' THEN
        RAISE EXCEPTION '%', format(
            'ARRET : app_console_can_request_job a change. Attendue '
            '8b2c43784957e08986786d70ac853a05, trouvee %s.', md5(src));
    END IF;
    IF position('youtrust_' in src) > 0 THEN
        RAISE EXCEPTION 'ARRET : un type youtrust_ est DEJA dans can_request_job.';
    END IF;
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois dans can_request_job.', combien);
    END IF;
    EXECUTE replace(src, ancre,
        $b$'sync_console_documents','relance_signature','cancel_signature_procedure','youtrust_send_signature','youtrust_sync_signature','youtrust_remind_signer','youtrust_cancel_signature','youtrust_signing_link',$b$);
END
$garde$;

-- ── 6. VERROU 3 : claim_next_job -- le worker DOCUMENTS ─────────────────────────
DO $garde$
DECLARE
    src     text;
    ancre   text := $a$'relance_signature','cancel_signature_procedure',$a$;
    combien int;
BEGIN
    SELECT replace(pg_get_functiondef(oid), chr(13), '')
      INTO src FROM pg_proc WHERE proname = 'app_console_claim_next_job';
    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : app_console_claim_next_job est introuvable.';
    END IF;
    IF md5(src) <> '4aa93a31736a538e0c5a4098ec75337f' THEN
        RAISE EXCEPTION '%', format(
            'ARRET : app_console_claim_next_job a change. Attendue '
            '4aa93a31736a538e0c5a4098ec75337f, trouvee %s.', md5(src));
    END IF;
    IF position('youtrust_' in src) > 0 THEN
        RAISE EXCEPTION 'ARRET : un type youtrust_ est DEJA dans claim_next_job.';
    END IF;
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois dans claim_next_job.', combien);
    END IF;
    EXECUTE replace(src, ancre,
        $b$'relance_signature','cancel_signature_procedure','youtrust_send_signature','youtrust_sync_signature','youtrust_remind_signer','youtrust_cancel_signature','youtrust_signing_link',$b$);
END
$garde$;

-- ── 7. LE FIL D'ACTIVITE DU COCKPIT -- QUI SE CONTROLE LUI-MEME ─────────────────
DO $garde$
DECLARE
    src     text;
    nouveau text;
    avant   text;
    apres   text;
    a1 text := $a$when 'cancelled' then 'signature annulée' else 'signature' end,$a$;
    b1 text := $b$when 'cancelled' then 'signature annulée' when 'expired' then 'signature expirée' else 'signature' end,$b$;
    a2 text := $a$and (d.metadata_json->'signature'->>'status') in ('signed','pending','cancelled')$a$;
    b2 text := $b$and (d.metadata_json->'signature'->>'status') in ('signed','pending','cancelled','expired')$b$;
    a3 text := $a$and ((d.metadata_json->'signature'->>'procedure_id') is not null$a$;
    b3 text := $b$and ((d.metadata_json->'signature'->>'procedure_id') is not null or (d.metadata_json->'signature'->>'provider_request_id') is not null$b$;
    ancres text[];
    i int;
    combien int;
BEGIN
    SELECT replace(pg_get_functiondef('public.app_cockpit_activite(bigint,integer)'::regprocedure), chr(13), '')
      INTO src;
    IF md5(src) <> '8b96ef0298419689c046c58c64e929d9' THEN
        RAISE EXCEPTION '%', format(
            'ARRET : app_cockpit_activite a change. Attendue '
            '8b96ef0298419689c046c58c64e929d9, trouvee %s.', md5(src));
    END IF;
    ancres := array[a1, a2, a3];
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        combien := (length(src) - length(replace(src, ancres[i], ''))) / length(ancres[i]);
        IF combien <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre %s du cockpit apparait %s fois (il en faut 1).', i, combien);
        END IF;
    END LOOP;

    -- LE TEMOIN, AVANT : toutes les lignes d'activite des dossiers ou le changement PEUT jouer
    -- (un document signe / en attente / annule / expire, ou portant un id Youtrust) -- ailleurs le
    -- fil n'a aucune ligne de signature, ni avant ni apres. 407 dossiers le 26/10, ~6 s.
    SELECT md5(coalesce(string_agg(t::text, '|' ORDER BY x.id, t.at, t.kind, t.lead, t.rest), ''))
      INTO avant
      FROM (SELECT DISTINCT app_dossier_id AS id FROM public.app_console_document
             WHERE app_dossier_id IS NOT NULL
               AND (metadata_json->'signature'->>'status' IN ('signed','pending','cancelled','expired')
                    OR metadata_json->'signature' ? 'provider_request_id')) x
      CROSS JOIN LATERAL public.app_cockpit_activite(x.id, 100) t;

    nouveau := replace(replace(replace(src, a1, b1), a2, b2), a3, b3);
    EXECUTE nouveau;

    -- LE TEMOIN, APRES : rien ne doit avoir bouge
    SELECT md5(coalesce(string_agg(t::text, '|' ORDER BY x.id, t.at, t.kind, t.lead, t.rest), ''))
      INTO apres
      FROM (SELECT DISTINCT app_dossier_id AS id FROM public.app_console_document
             WHERE app_dossier_id IS NOT NULL
               AND (metadata_json->'signature'->>'status' IN ('signed','pending','cancelled','expired')
                    OR metadata_json->'signature' ? 'provider_request_id')) x
      CROSS JOIN LATERAL public.app_cockpit_activite(x.id, 100) t;
    IF avant IS DISTINCT FROM apres THEN
        RAISE EXCEPTION '%', format(
            'ARRET : le fil d''activite a CHANGE pour un document existant (avant %s, apres %s) -- rien n''est ecrit.',
            avant, apres);
    END IF;
    RAISE NOTICE 'COCKPIT : temoin identique avant et apres (%).', avant;
END
$garde$;

-- ── 8. VERROU 1 : la contrainte des types de travaux -- EN DERNIER : l'ALTER TABLE
--    verrouille app_console_job jusqu'au COMMIT ; pose a la fin, le verrou ne dure qu'un instant ───────────────────────────
DO $garde$
DECLARE
    src     text;
    ancre   text := $a$'set_hektor_photo_visibility'::text]$a$;
    nouveau text;
    combien int;
BEGIN
    SELECT replace(pg_get_constraintdef(oid), chr(13), '')
      INTO src FROM pg_constraint WHERE conname = 'app_console_job_job_type_check';
    IF src IS NULL THEN
        RAISE EXCEPTION 'ARRET : la contrainte app_console_job_job_type_check est introuvable.';
    END IF;
    IF md5(src) <> 'e59646dcb0629c50e5d19145708b1caa' THEN
        RAISE EXCEPTION '%', format(
            'ARRET : la contrainte a change depuis la mesure du 26/10. Attendue '
            'e59646dcb0629c50e5d19145708b1caa, trouvee %s.', md5(src));
    END IF;
    IF position('youtrust_' in src) > 0 THEN
        RAISE EXCEPTION 'ARRET : un type youtrust_ est DEJA dans la contrainte.';
    END IF;
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois dans la contrainte (il en faut 1).', combien);
    END IF;
    nouveau := replace(src, ancre,
        $b$'set_hektor_photo_visibility'::text, 'youtrust_send_signature'::text, 'youtrust_sync_signature'::text, 'youtrust_remind_signer'::text, 'youtrust_cancel_signature'::text, 'youtrust_signing_link'::text]$b$);
    EXECUTE 'ALTER TABLE public.app_console_job DROP CONSTRAINT app_console_job_job_type_check';
    EXECUTE 'ALTER TABLE public.app_console_job ADD CONSTRAINT app_console_job_job_type_check ' || nouveau;
END
$garde$;

-- ── LE TABLEAU DE FIN : un silence ne dit pas si c'est pose ────────────────────
SELECT 1 AS "#", 'interrupteur signature_youtrust' AS objet,
       coalesce((SELECT 'POSE, valeur = ' || value FROM public.app_setting WHERE key = 'signature_youtrust'), '⛔ PAS POSE') AS etat
UNION ALL SELECT 2, 'tables app_signature_request + app_signature_event',
       CASE WHEN to_regclass('public.app_signature_request') IS NOT NULL
             AND to_regclass('public.app_signature_event') IS NOT NULL THEN 'POSEES' ELSE '⛔ PAS POSEES' END
UNION ALL SELECT 3, 'verrou 1 -- contrainte (5 types youtrust_)',
       (SELECT (length(d) - length(replace(d, 'youtrust_', ''))) / 9 || ' sur 5'
          FROM (SELECT pg_get_constraintdef(oid) d FROM pg_constraint WHERE conname = 'app_console_job_job_type_check') c)
UNION ALL SELECT 4, 'verrou 2 -- can_request_job (5 types youtrust_)',
       (SELECT (length(prosrc) - length(replace(prosrc, 'youtrust_', ''))) / 9 || ' sur 5'
          FROM pg_proc WHERE proname = 'app_console_can_request_job')
UNION ALL SELECT 5, 'verrou 3 -- claim_next_job (5 types youtrust_)',
       (SELECT (length(prosrc) - length(replace(prosrc, 'youtrust_', ''))) / 9 || ' sur 5'
          FROM pg_proc WHERE proname = 'app_console_claim_next_job')
UNION ALL SELECT 6, 'cockpit -- provider_request_id + expiree',
       CASE WHEN (SELECT position('provider_request_id' in prosrc) > 0 AND position('signature expirée' in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_cockpit_activite') THEN 'POSE' ELSE '⛔ PAS POSE' END
UNION ALL SELECT 7, 'TEMOIN INVERSE -- relance/annulation ImmoSign toujours au worker documents',
       CASE WHEN (SELECT position('relance_signature' in prosrc) > 0 AND position('cancel_signature_procedure' in prosrc) > 0
                    FROM pg_proc WHERE proname = 'app_console_claim_next_job') THEN 'INTACTES' ELSE '⛔ CASSEES -- COLLER L''INVERSE' END
ORDER BY 1;

COMMIT;
