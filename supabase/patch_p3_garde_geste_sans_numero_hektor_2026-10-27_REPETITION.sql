-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — P3 : la garde « pas de geste sans numéro Hektor » dans app_geste_affaire_optimistic     27/10/2026
-- Les deux essais RÉELS de la fonction (sous le compte de Frédéric, admin) sont faits dans des sous-blocs
-- TOUJOURS annulés : aucun état, aucun travail, aucune ligne n'en reste.
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TEMP TABLE IF NOT EXISTS repetition_p3g (n int, controle text, verdict text);
TRUNCATE repetition_p3g;

DO $rep$
DECLARE
    f        text;
    garde    text := '  -- ⑧ P3 (27/10/2026) : PAS DE GESTE SANS NUMÉRO HEKTOR, comme l''écran (note des types §38).' || chr(10)
                  || '  IF btrim(coalesce(a.hektor_affaire_id::text, '''')) = '''' THEN' || chr(10)
                  || '    RAISE EXCEPTION ''sans_numero_hektor: Cette transaction n''''a pas encore de numéro Hektor : le geste ne peut pas partir.'' USING errcode = ''22023'';' || chr(10)
                  || '  END IF;' || chr(10) || chr(10);
    a_id     bigint;
    msg_sans text := '';
    ret_avec jsonb;
    msg_avec text := '';
    jobs_avant int; jobs_apres int; etat_avant text; etat_apres text;
BEGIN
    SELECT replace(pg_get_functiondef(p.oid), chr(13), '') INTO f FROM pg_proc p JOIN pg_namespace s ON s.oid = p.pronamespace
     WHERE s.nspname = 'public' AND p.proname = 'app_geste_affaire_optimistic';
    INSERT INTO repetition_p3g VALUES (1, 'la fonction porte la garde, a sa place (avant « etat_avant := a.state; »)',
        CASE WHEN position(garde || '  etat_avant := a.state;' in f) > 0 THEN 'OK' ELSE '⛔ ECHEC' END);
    INSERT INTO repetition_p3g
    SELECT 2, 'SECURITY DEFINER, proprietaire et droits gardes',
           CASE WHEN p.prosecdef AND p.proowner::regrole::text = 'postgres'
                 AND p.proacl::text = '{postgres=X/postgres,authenticated=X/postgres,service_role=X/postgres}' THEN 'OK' ELSE '⛔ ECHEC (' || p.proacl::text || ')' END
      FROM pg_proc p JOIN pg_namespace s ON s.oid = p.pronamespace WHERE s.nspname = 'public' AND p.proname = 'app_geste_affaire_optimistic';
    INSERT INTO repetition_p3g VALUES (3, 'TEMOIN INVERSE : sans la garde, la fonction retrouve son empreinte d''avant (seule la garde a change)',
        CASE WHEN md5(replace(f, garde, '')) = 'a65692290a679d603916b9d635192b80' THEN 'OK' ELSE '⛔ ECHEC (' || md5(replace(f, garde, '')) || ')' END);

    -- un compromis vivant, avec numéro Hektor, sur un bien que l'admin voit
    SELECT l.app_affaire_id INTO a_id FROM public.app_affaire_ledger l
     WHERE l.kind = 'compromis' AND l.present_in_hektor AND btrim(coalesce(l.hektor_affaire_id, '')) <> ''
       AND lower(coalesce(l.state, '')) NOT IN ('cancelled', 'annule') AND l.app_dossier_id IS NOT NULL
       -- ⚠ pas de vente dans son dossier : sinon la fonction refuse AVANT la garde (« compromis verrouillé »)
       AND NOT EXISTS (SELECT 1 FROM public.app_affaire_ledger v
                        WHERE v.app_chaine_id = l.app_chaine_id AND v.kind = 'vente'
                          AND NOT (btrim(coalesce(v.hektor_affaire_id, '')) <> '' AND v.present_in_hektor IS FALSE))
     ORDER BY l.app_affaire_id DESC LIMIT 1;
    SELECT count(*) INTO jobs_avant FROM public.app_console_job WHERE job_type = 'cancel_hektor_compromis';
    SELECT state INTO etat_avant FROM public.app_affaire_ledger WHERE app_affaire_id = a_id;

    PERFORM set_config('request.jwt.claims', json_build_object('sub', 'd4b1685f-948b-4ce8-af15-671b94a725e6', 'role', 'authenticated')::text, true);
    -- 4. SANS numéro Hektor : le geste est REFUSÉ, avec le message de l'écran
    BEGIN
        UPDATE public.app_affaire_ledger SET hektor_affaire_id = NULL WHERE app_affaire_id = a_id;
        BEGIN
            PERFORM public.app_geste_affaire_optimistic(a_id, 'annuler', NULL);
            msg_sans := 'PASSE';
        EXCEPTION WHEN OTHERS THEN
            msg_sans := SQLERRM;
        END;
        RAISE EXCEPTION 'annule_l_essai';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM <> 'annule_l_essai' THEN msg_sans := 'ERREUR INATTENDUE : ' || SQLERRM; END IF;
    END;
    INSERT INTO repetition_p3g VALUES (4, 'SANS numero Hektor : le geste est refuse, avec le message de l''ecran (compromis ' || a_id || ')',
        CASE WHEN msg_sans LIKE 'sans_numero_hektor:%' THEN 'OK' ELSE '⛔ ECHEC (' || left(msg_sans, 160) || ')' END);
    -- 5. AVEC son numéro : le geste PASSE comme avant (état posé, travail créé) -- puis tout est annulé
    BEGIN
        BEGIN
            ret_avec := public.app_geste_affaire_optimistic(a_id, 'annuler', NULL);
        EXCEPTION WHEN OTHERS THEN
            msg_avec := SQLERRM;
        END;
        RAISE EXCEPTION 'annule_l_essai';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM <> 'annule_l_essai' THEN msg_avec := 'ERREUR INATTENDUE : ' || SQLERRM; END IF;
    END;
    INSERT INTO repetition_p3g VALUES (5, 'AVEC son numero : le geste passe comme avant (travail cree, etat pose)',
        CASE WHEN msg_avec = '' AND (ret_avec->>'ok')::boolean AND ret_avec->>'job_type' = 'cancel_hektor_compromis' AND ret_avec->>'job_id' IS NOT NULL
             THEN 'OK' ELSE '⛔ ECHEC (' || coalesce(left(msg_avec, 160), '') || ' ' || coalesce(ret_avec::text, '') || ')' END);
    -- 6. rien n'en reste
    SELECT count(*) INTO jobs_apres FROM public.app_console_job WHERE job_type = 'cancel_hektor_compromis';
    SELECT state INTO etat_apres FROM public.app_affaire_ledger WHERE app_affaire_id = a_id;
    INSERT INTO repetition_p3g
    SELECT 6, 'les essais n''ont rien laisse (aucun travail, etat et numero du compromis intacts)',
        CASE WHEN jobs_apres = jobs_avant AND etat_apres IS NOT DISTINCT FROM etat_avant
              AND btrim(coalesce(l.hektor_affaire_id, '')) <> '' THEN 'OK' ELSE '⛔ ECHEC' END
      FROM public.app_affaire_ledger l WHERE l.app_affaire_id = a_id;
END
$rep$;

SELECT * FROM repetition_p3g ORDER BY 1;
