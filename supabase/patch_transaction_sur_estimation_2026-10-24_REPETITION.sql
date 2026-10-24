-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — pas de transaction sur un bien en estimation    24/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste, ni la fonction
--   modifiée, ni l'interrupteur, ni les travaux, ni les lignes du registre.
-- Le VRAI PATCH, puis la création appelée COMME L'ÉCRAN, au nom de Frédéric :
--   sur le bien d'essai 10000009 (annonce 63331, Estimation) et sur un bien ACTIF choisi par la répétition.
--   T1 ÉTEINT : offre sur l'Estimation → acceptée (le témoin inverse : le défaut)
--   T2 allumé : offre sur l'Estimation → REFUSÉE « transaction_sur_estimation »
--   T3 allumé : compromis → REFUSÉ   · T4 allumé : vente → REFUSÉE
--   T5 allumé : « Actif » sur l'Estimation → accepté (le chemin pour en sortir)
--   T6 allumé : offre sur un bien ACTIF → acceptée (rien d'autre ne change)
--   T7 l'inverse rend 44697dd5.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    actif bigint;
    res jsonb;
    err text;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.app_dossier_current WHERE app_dossier_id = 10000009 AND statut_annonce = 'Estimation') THEN
        RAISE EXCEPTION '%', 'ARRET : le bien d''essai 10000009 n''est plus en Estimation -- la repetition ne prouverait rien.';
    END IF;
    SELECT d.app_dossier_id INTO actif FROM public.app_dossier_current d
     WHERE d.statut_annonce = 'Actif' AND btrim(coalesce(d.negociateur_email, '')) <> ''
       AND NOT EXISTS (SELECT 1 FROM public.app_console_job j
                        WHERE j.app_dossier_id = d.app_dossier_id AND j.status IN ('pending', 'running'))
     ORDER BY d.app_dossier_id LIMIT 1;
    IF actif IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : aucun bien Actif libre pour le temoin.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    insert into public.app_setting (key, value, description, updated_at)
    values ('transaction_refusee_sur_estimation', 'off',
            'Chantier 8 / 24/10/2026 : on = la creation d''une OFFRE, d''un COMPROMIS ou d''une VENTE est refusee sur un bien en ESTIMATION (« pas de transaction pour les biens Vendu, Clos ou Estimation » -- regle de Frederic ; Vendu et Clos sont deja refuses hors parc vivant). Voir supabase/patch_transaction_sur_estimation_2026-10-24.sql. off = comportement d''avant.',
            now())
    on conflict (key) do nothing;
    EXECUTE $exec_p$ DO $pose_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  -- @repli-fin$a1$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  -- @repli-fin

  -- ⛔ ─── ⑧ (24/10/2026) : PAS DE TRANSACTION SUR UN BIEN EN ESTIMATION ─── ⛔
  -- La regle de Frederic : « pas de transaction pour les biens en etat Vendu, Clos ou Estimation ; si
  -- l'etat revient a Actif, possibilite de refaire une nouvelle chaine ». Vendu et Clos sont refuses
  -- juste au-dessus (hors parc vivant) ; l'Estimation, elle, est DANS le parc vivant (12 781 biens le
  -- 24/10) et passait. On ne regarde que l'ETAT du bien, jamais ses anciennes transactions.
  -- « Actif » et « Clos » (le chemin pour sortir de l'estimation) ne sont pas touches.
  -- Interrupteur 'transaction_refusee_sur_estimation'.
  if target_status in ('offer', 'compromise', 'sold')
     and lower(btrim(coalesce(d.statut_annonce, ''))) like '%estimation%'
     and coalesce((select s.value from public.app_setting s where s.key = 'transaction_refusee_sur_estimation'), 'off') = 'on' then
    raise exception 'transaction_sur_estimation: ce bien est en Estimation. Une offre, un compromis ou une vente se font sur un bien Actif : passez-le d''abord en Actif.' using errcode = '22023';
  end if;$n1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '93be71b41e9ff172de9e8c3e261233a5' THEN
        RAISE NOTICE '%', 'Deja pose : app_change_annonce_status_optimistic porte deja l''empreinte 93be71b4. Rien n''est ecrit.'; RETURN;
    END IF;
    IF md5(d) <> '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, attendu 44697dd5. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '93be71b41e9ff172de9e8c3e261233a5' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte rendu a l''empreinte %s, attendu 93be71b4 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) <> '93be71b41e9ff172de9e8c3e261233a5' THEN
        RAISE EXCEPTION '%', 'ARRET : app_change_annonce_status_optimistic, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_rep$ $exec_p$;

    -- T1 ETEINT
    update public.app_dossier_current set statut_annonce = 'Estimation' where app_dossier_id = 10000009;
    err := '';
    BEGIN
      res := public.app_change_annonce_status_optimistic(10000009, 'offer', jsonb_build_object('amount', '100000', 'sale_price', '100000'), 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    total := total + 1;
    IF err = '' THEN ok := ok + 1; r := r || ' | T1 OK eteint : une offre sur l estimation est acceptee';
    ELSE r := r || ' | T1 ECHEC eteint : une offre sur l estimation est acceptee : ' || coalesce(err, 'null'); END IF;

    update public.app_setting set value = 'on' where key = 'transaction_refusee_sur_estimation';
    -- T2
    update public.app_dossier_current set statut_annonce = 'Estimation' where app_dossier_id = 10000009;
    err := '';
    BEGIN
      res := public.app_change_annonce_status_optimistic(10000009, 'offer', jsonb_build_object('amount', '100000', 'sale_price', '100000'), 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    total := total + 1;
    IF err like 'transaction_sur_estimation:%' THEN ok := ok + 1; r := r || ' | T2 OK allume : offre sur l estimation refusee';
    ELSE r := r || ' | T2 ECHEC allume : offre sur l estimation refusee : ' || coalesce(nullif(err, ''), 'null'); END IF;
    -- T3
    update public.app_dossier_current set statut_annonce = 'Estimation' where app_dossier_id = 10000009;
    err := '';
    BEGIN
      res := public.app_change_annonce_status_optimistic(10000009, 'compromise', jsonb_build_object('amount', '100000', 'sale_price', '100000'), 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    total := total + 1;
    IF err like 'transaction_sur_estimation:%' THEN ok := ok + 1; r := r || ' | T3 OK allume : compromis sur l estimation refuse';
    ELSE r := r || ' | T3 ECHEC allume : compromis sur l estimation refuse : ' || coalesce(nullif(err, ''), 'null'); END IF;
    -- T4
    update public.app_dossier_current set statut_annonce = 'Estimation' where app_dossier_id = 10000009;
    err := '';
    BEGIN
      res := public.app_change_annonce_status_optimistic(10000009, 'sold', jsonb_build_object('amount', '100000', 'sale_price', '100000'), 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    total := total + 1;
    IF err like 'transaction_sur_estimation:%' THEN ok := ok + 1; r := r || ' | T4 OK allume : vente sur l estimation refusee';
    ELSE r := r || ' | T4 ECHEC allume : vente sur l estimation refusee : ' || coalesce(nullif(err, ''), 'null'); END IF;
    -- T5
    update public.app_dossier_current set statut_annonce = 'Estimation' where app_dossier_id = 10000009;
    err := '';
    BEGIN
      res := public.app_change_annonce_status_optimistic(10000009, 'active', jsonb_build_object('amount', '100000', 'sale_price', '100000'), 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    total := total + 1;
    IF err = '' THEN ok := ok + 1; r := r || ' | T5 OK allume : passer l estimation en Actif reste accepte';
    ELSE r := r || ' | T5 ECHEC allume : passer l estimation en Actif reste accepte : ' || coalesce(err, 'null'); END IF;
    -- T6
    err := '';
    BEGIN
      res := public.app_change_annonce_status_optimistic(actif, 'offer', jsonb_build_object('amount', '100000', 'sale_price', '100000'), 9);
      delete from public.app_console_job where id::text = res->>'job_id';
    EXCEPTION WHEN others THEN err := SQLERRM;
    END;
    total := total + 1;
    IF err = '' THEN ok := ok + 1; r := r || ' | T6 OK allume : une offre sur un bien Actif reste acceptee';
    ELSE r := r || ' | T6 ECHEC allume : une offre sur un bien Actif reste acceptee : ' || coalesce(err || ' (bien ' || actif || ')', 'null'); END IF;

    -- T7 L'INVERSE
    EXECUTE $exec_i$ DO $retour_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  -- @repli-fin$a1$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  -- @repli-fin

  -- ⛔ ─── ⑧ (24/10/2026) : PAS DE TRANSACTION SUR UN BIEN EN ESTIMATION ─── ⛔
  -- La regle de Frederic : « pas de transaction pour les biens en etat Vendu, Clos ou Estimation ; si
  -- l'etat revient a Actif, possibilite de refaire une nouvelle chaine ». Vendu et Clos sont refuses
  -- juste au-dessus (hors parc vivant) ; l'Estimation, elle, est DANS le parc vivant (12 781 biens le
  -- 24/10) et passait. On ne regarde que l'ETAT du bien, jamais ses anciennes transactions.
  -- « Actif » et « Clos » (le chemin pour sortir de l'estimation) ne sont pas touches.
  -- Interrupteur 'transaction_refusee_sur_estimation'.
  if target_status in ('offer', 'compromise', 'sold')
     and lower(btrim(coalesce(d.statut_annonce, ''))) like '%estimation%'
     and coalesce((select s.value from public.app_setting s where s.key = 'transaction_refusee_sur_estimation'), 'off') = 'on' then
    raise exception 'transaction_sur_estimation: ce bien est en Estimation. Une offre, un compromis ou une vente se font sur un bien Actif : passez-le d''abord en Actif.' using errcode = '22023';
  end if;$n1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_change_annonce_status_optimistic porte deja l''empreinte d''avant (44697dd5).'; RETURN;
    END IF;
    IF md5(d) <> '93be71b41e9ff172de9e8c3e261233a5' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, attendu 93be71b4. Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte rendu a l''empreinte %s, attendu 44697dd5 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) <> '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE EXCEPTION '%', 'ARRET : app_change_annonce_status_optimistic, apres l''ecriture, l''empreinte n''est pas celle attendue.';
    END IF;
END
$retour_rep$ $exec_i$;
    total := total + 1;
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) = '44697dd59587c644cdc021bd8f52108d' THEN ok := ok + 1; r := r || ' | T7 OK l inverse rend l empreinte d avant';
    ELSE r := r || ' | T7 ECHEC l inverse rend l empreinte d avant : ' || coalesce('empreinte differente', 'null'); END IF;

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
