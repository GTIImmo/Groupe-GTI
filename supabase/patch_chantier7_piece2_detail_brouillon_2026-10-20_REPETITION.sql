-- ═══════════════════════════════════════════════════════════════════════════════
-- TEMOIN DE LA PIECE ② -- a coller APRES le patch.           20/10/2026
--
-- ⛔ IL N'ECRIT RIEN. Tout est en lecture, et la transaction finit par ROLLBACK --
--   necessaire parce qu'on EMPRUNTE une identite (set_config) pour eprouver les
--   droits comme les vivrait un negociateur.
--
-- CE QU'IL PROUVE, et pourquoi chaque ligne existe :
--   1. les 3 verrous portent la famille brouillon          (sinon « pending » a vie)
--   2. ⚠ LES DEUX SOEURS SONT INTACTES                     (le temoin inverse : un
--      patch qui ajoute une famille ne doit pas emporter les deux qui marchent)
--   3. la table du cache et ses 2 politiques sont la
--   4. ⭐⭐ UN NEGOCIATEUR PEUT VRAIMENT LIRE SON BROUILLON -- c'est LE test du
--      defaut muet : avant le patch, `app_console_can_access_dossier` rendait
--      FAUX pour tout brouillon, donc 0 ligne et aucune erreur.
--   5. et il rend encore FAUX pour le brouillon de QUELQU'UN D'AUTRE
--      (sinon on aurait ouvert le perimetre de tout le monde -- bien pire)
--
-- Toute ligne « ECHEC » doit etre regardee avant d'aller plus loin.
-- ═══════════════════════════════════════════════════════════════════════════════

BEGIN;

DO $temoin$
DECLARE
    echecs        int := 0;
    v             boolean;
    nego_email    text;
    nego_id       uuid;
    mon_brouillon text;
    son_brouillon text;
    mon_app_id    bigint;
BEGIN
    -- ── 1. LES 3 VERROUS ─────────────────────────────────────────────────────
    SELECT position($a$'prepare_brouillon_annonce_detail'$a$ in replace(pg_get_constraintdef(oid), chr(13), '')) > 0
      INTO v FROM pg_constraint WHERE conname = 'app_console_job_job_type_check';
    IF coalesce(v, false) THEN RAISE NOTICE '  OK   (1) verrou 1 : la contrainte accepte le type';
    ELSE RAISE NOTICE 'ECHEC  (1) verrou 1 : la contrainte REFUSE le type'; echecs := echecs + 1; END IF;

    SELECT position($a$'prepare_brouillon_annonce_detail'$a$ in prosrc) > 0
      INTO v FROM pg_proc WHERE proname = 'app_console_can_request_job';
    IF coalesce(v, false) THEN RAISE NOTICE '  OK   (2) verrou 2 : can_request_job connait le type';
    ELSE RAISE NOTICE 'ECHEC  (2) verrou 2 : can_request_job ne le connait pas'; echecs := echecs + 1; END IF;

    SELECT position($a$'prepare_brouillon_annonce_detail'$a$ in prosrc) > 0
      INTO v FROM pg_proc WHERE proname = 'app_console_claim_next_job';
    IF coalesce(v, false) THEN RAISE NOTICE '  OK   (3) verrou 3 : le worker DOCUMENTS le reclamera';
    ELSE RAISE NOTICE 'ECHEC  (3) verrou 3 : PERSONNE ne le reclamera -- pending a vie'; echecs := echecs + 1; END IF;

    SELECT position('app_brouillon_annonce_index_current' in prosrc) > 0
      INTO v FROM pg_proc WHERE proname = 'app_console_can_access_dossier';
    IF coalesce(v, false) THEN RAISE NOTICE '  OK   (4) droits : can_access_dossier connait le 4e index';
    ELSE RAISE NOTICE 'ECHEC  (4) droits : le 4e index est toujours inconnu'; echecs := echecs + 1; END IF;

    -- ── 2. LE TEMOIN INVERSE : LES DEUX SOEURS SONT INTACTES ─────────────────
    SELECT position($a$'prepare_archived_annonce_detail'$a$ in prosrc) > 0
       AND position($a$'prepare_historical_annonce_detail'$a$ in prosrc) > 0
      INTO v FROM pg_proc WHERE proname = 'app_console_claim_next_job';
    IF coalesce(v, false) THEN RAISE NOTICE '  OK   (5) TEMOIN INVERSE : Archive et Historique toujours reclames';
    ELSE RAISE NOTICE 'ECHEC  (5) TEMOIN INVERSE : j''ai casse une famille qui marchait !'; echecs := echecs + 1; END IF;

    SELECT position('app_archive_annonce_index_current' in prosrc) > 0
       AND position('app_historical_annonce_index_current' in prosrc) > 0
      INTO v FROM pg_proc WHERE proname = 'app_console_can_access_dossier';
    IF coalesce(v, false) THEN RAISE NOTICE '  OK   (6) TEMOIN INVERSE : les 2 index soeurs sont encore lus';
    ELSE RAISE NOTICE 'ECHEC  (6) TEMOIN INVERSE : un index soeur a disparu des droits !'; echecs := echecs + 1; END IF;

    -- ── 3. LA TABLE ET SES POLITIQUES ────────────────────────────────────────
    SELECT count(*) = 2 INTO v FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid
     WHERE c.relname = 'app_brouillon_annonce_detail_cache';
    IF coalesce(v, false) THEN RAISE NOTICE '  OK   (7) le cache brouillon a bien ses 2 politiques';
    ELSE RAISE NOTICE 'ECHEC  (7) les politiques du cache brouillon ne sont pas 2'; echecs := echecs + 1; END IF;

    -- ── 4. ⭐⭐ LE VRAI TEST : UN NEGOCIATEUR, SUR SON PROPRE BROUILLON ───────
    -- On cherche un negociateur ACTIF, de role commercial, qui possede un brouillon.
    SELECT lower(b.negociateur_email), b.hektor_annonce_id::text, b.app_brouillon_id
      INTO nego_email, mon_brouillon, mon_app_id
      FROM public.app_brouillon_annonce_index_current b
      JOIN public.app_user_profile p
        ON lower(p.email) = lower(b.negociateur_email)
     WHERE p.is_active = true
       AND p.role::text = 'commercial'
       AND nullif(trim(b.negociateur_email), '') IS NOT NULL
     LIMIT 1;

    IF nego_email IS NULL THEN
        RAISE NOTICE '  ⚠    (8) NON MESURE : aucun negociateur actif de role commercial ne possede';
        RAISE NOTICE '                        de brouillon -- le test des droits ne peut pas tourner.';
    ELSE
        SELECT id INTO nego_id FROM public.app_user_profile WHERE lower(email) = nego_email LIMIT 1;
        -- un brouillon qui N'EST PAS a lui, pour le test en negatif
        SELECT b.hektor_annonce_id::text INTO son_brouillon
          FROM public.app_brouillon_annonce_index_current b
         WHERE lower(coalesce(b.negociateur_email, '')) <> nego_email
         LIMIT 1;

        PERFORM set_config('request.jwt.claims',
                           json_build_object('sub', nego_id::text, 'role', 'authenticated')::text,
                           true);

        v := public.app_console_can_access_dossier(mon_app_id, mon_brouillon);
        IF coalesce(v, false) THEN
            RAISE NOTICE '  OK   (8) %, role commercial, PEUT lire le cache de son brouillon %',
                         nego_email, mon_brouillon;
        ELSE
            RAISE NOTICE 'ECHEC  (8) % ne peut PAS lire son propre brouillon % -- le defaut muet est toujours la',
                         nego_email, mon_brouillon;
            echecs := echecs + 1;
        END IF;

        IF son_brouillon IS NOT NULL THEN
            v := public.app_console_can_access_dossier(NULL, son_brouillon);
            IF coalesce(v, false) THEN
                RAISE NOTICE 'ECHEC  (9) ⛔ il peut lire le brouillon de QUELQU''UN D''AUTRE (%) -- perimetre ouvert !',
                             son_brouillon;
                echecs := echecs + 1;
            ELSE
                RAISE NOTICE '  OK   (9) et il ne peut PAS lire celui de quelqu''un d''autre (%)', son_brouillon;
            END IF;
        ELSE
            RAISE NOTICE '  ⚠    (9) NON MESURE : pas de brouillon appartenant a un autre.';
        END IF;

        PERFORM set_config('request.jwt.claims', '', true);
    END IF;

    RAISE NOTICE ' ';
    IF echecs > 0 THEN
        RAISE EXCEPTION '%', format('%s controle(s) en ECHEC -- la piece 2 n''est pas en etat.', echecs);
    END IF;
    RAISE NOTICE 'TEMOIN VERT : la famille brouillon est posee, les deux soeurs sont intactes,';
    RAISE NOTICE 'et un negociateur voit SES brouillons -- et seulement les siens.';
END
$temoin$;

ROLLBACK;
