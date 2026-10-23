-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE N — le notaire du vendeur d'une offre gardé chez nous    23/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste, ni les
--   fonctions modifiées, ni l'interrupteur, ni les transactions créées, ni le carnet, ni les travaux.
-- Le VRAI PATCH, puis les fonctions appelées COMME L'ÉCRAN, au nom de Frédéric, sur VA6482 (dossier
-- 1068399) et son offre 33114 (1001384, essai 3 du 23/10).
--   T1 ÉTEINT : créer une offre avec notaire du vendeur → pas de ligne (le témoin inverse : le défaut)
--   T2 allumé : créer une offre avec notaire du vendeur → id 10355906 et nom au carnet
--   T3 allumé : créer une offre SANS notaire du vendeur → aucune ligne
--   T4 allumé : les AUTRES lignes du carnet de la création sont les mêmes qu'éteint (rien d'autre ne change)
--   T5 allumé : modifier l'offre 1001384, notaire du vendeur AFFIRMÉ et tapé → les deux lignes
--   T6 allumé : modifier, NON affirmé → aucune ligne
--   T7 l'inverse rend f9d02447 et 0dac8c86.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    res jsonb;
    neuf bigint;
    neuf_eteint bigint;
    autres_eteint text;
    autres_allume text;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.app_affaire_ledger WHERE app_affaire_id = 1001384 AND kind = 'offre') THEN
        RAISE EXCEPTION '%', 'ARRET : l''offre d''essai 1001384 n''existe plus -- la repetition ne prouverait rien.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    insert into public.app_setting (key, value, description, updated_at)
    values ('offre_notaire_vendeur', 'off',
            'Chantier 8 / N 23/10/2026 : on = le notaire du VENDEUR saisi sur une OFFRE est garde au carnet (notaire_mandant_id / notaire_mandant_nom), a la creation et a la modification s''il est affirme (voir supabase/patch_n_offre_notaire_vendeur_2026-10-23.sql). Hektor ne le garde pas sur une offre. off = comportement d''avant (il se perd).',
            now())
    on conflict (key) do nothing;
    EXECUTE $exec_c$ DO $pose_c_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($ca1$        ('notaire_id',         v_payload->>'buyer_notary_id'),$ca1$, chr(13), '')];
    neufs text[] := array[
        replace($cn1$        ('notaire_id',         v_payload->>'buyer_notary_id'),
        -- N (23/10/2026, chantier 8) : le notaire du VENDEUR d'une OFFRE. Hektor ne le garde pas sur une
        --   offre (0 sur 11 190) : le carnet le garde, et le compromis de la chaine le reprend.
        --   Interrupteur 'offre_notaire_vendeur'. Compromis et vente : inchanges (R1 les ecrit au registre).
        ('notaire_mandant_id',  case when v_kind = 'offre' and coalesce((select s.value from public.app_setting s where s.key = 'offre_notaire_vendeur'), 'off') = 'on'
                                 then v_payload->>'seller_notary_id' end),
        ('notaire_mandant_nom', case when v_kind = 'offre' and coalesce((select s.value from public.app_setting s where s.key = 'offre_notaire_vendeur'), 'off') = 'on'
                                  and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                                 then v_payload->>'seller_notary_nom' end),$cn1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE NOTICE '%', 'Deja pose : app_change_annonce_status_optimistic porte deja l''empreinte 44697dd5. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> 'f9d024471d0740fa21fffa532e9aa2ae' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, attendu f9d02447 (mesuree le 23/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte neuf a l''empreinte %s, attendu 44697dd5 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) <> '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE EXCEPTION '%', 'ARRET : app_change_annonce_status_optimistic, apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_c_rep$ $exec_c$;
    EXECUTE $exec_m$ DO $pose_m_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($ma1$      ('notaire_id',         v_payload->>'buyer_notary_id',                             null::text),$ma1$, chr(13), ''),
        replace($ma2$             when 'notaire_id'         then array['buyer_notary_id']$ma2$, chr(13), '')];
    neufs text[] := array[
        replace($mn1$      ('notaire_id',         v_payload->>'buyer_notary_id',                             null::text),
      -- N (23/10/2026) : le notaire du VENDEUR d'une OFFRE, s'il est AFFIRME (voir la creation).
      ('notaire_mandant_id',  case when a.kind = 'offre' and (v_payload->'notaires_affirmes'->>'mandant') = 'true' and coalesce((select s.value from public.app_setting s where s.key = 'offre_notaire_vendeur'), 'off') = 'on'
                               then v_payload->>'seller_notary_id' end,                null::text),
      ('notaire_mandant_nom', case when a.kind = 'offre' and (v_payload->'notaires_affirmes'->>'mandant') = 'true' and coalesce((select s.value from public.app_setting s where s.key = 'offre_notaire_vendeur'), 'off') = 'on'
                                and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                               then v_payload->>'seller_notary_nom' end,               null::text),$mn1$, chr(13), ''),
        replace($mn2$             when 'notaire_id'         then array['buyer_notary_id']
             when 'notaire_mandant_id'  then array['seller_notary_id']
             when 'notaire_mandant_nom' then array['seller_notary_id']$mn2$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE NOTICE '%', 'Deja pose : app_modifier_affaire_optimistic porte deja l''empreinte 43247de7. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, attendu 0dac8c86 (mesuree le 23/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte neuf a l''empreinte %s, attendu 43247de7 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) <> '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE EXCEPTION '%', 'ARRET : app_modifier_affaire_optimistic, apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_m_rep$ $exec_m$;

    -- T1 ETEINT
    res := public.app_change_annonce_status_optimistic(1068399, 'offer', jsonb_build_object('amount', '115000', 'sale_price', '128787', 'transaction_date', '2026-10-23', 'validity_days', '15', 'retraction_days', '10', 'buyer_fees', '5000', 'buyer_fees_rate', '4.35', 'buyer_contact_id', '20000013', 'buyer_notary_id', '10064499', 'seller_notary_id', '10355906', 'seller_notary_nom', 'Me. Eric PAILHES', 'numero_dossier', 'VA6482', 'hektor_annonce_id', '24113'), 9);
    neuf := coalesce((res->>'app_affaire_id')::bigint,
                     (select (j.payload_json->>'app_affaire_id')::bigint from public.app_console_job j where j.id::text = res->>'job_id'));
    delete from public.app_console_job where id::text = res->>'job_id';
    neuf_eteint := neuf;
    select string_agg(champ || '=' || valeur_app, ',' order by champ) into autres_eteint
      from public.app_affaire_champ_app where app_affaire_id = neuf_eteint;
    total := total + 1;
    IF neuf_eteint is not null and (select valeur_app from public.app_affaire_champ_app where app_affaire_id = neuf_eteint and champ = 'notaire_mandant_id') is null THEN ok := ok + 1; r := r || ' | T1 OK eteint : pas de notaire du vendeur au carnet';
    ELSE r := r || ' | T1 ECHEC eteint : pas de notaire du vendeur au carnet : ' || coalesce(coalesce((select valeur_app from public.app_affaire_champ_app where app_affaire_id = neuf_eteint and champ = 'notaire_mandant_id'), res::text), 'null'); END IF;

    update public.app_setting set value = 'on' where key = 'offre_notaire_vendeur';
    -- T2 ALLUME, AVEC
    res := public.app_change_annonce_status_optimistic(1068399, 'offer', jsonb_build_object('amount', '115000', 'sale_price', '128787', 'transaction_date', '2026-10-23', 'validity_days', '15', 'retraction_days', '10', 'buyer_fees', '5000', 'buyer_fees_rate', '4.35', 'buyer_contact_id', '20000013', 'buyer_notary_id', '10064499', 'seller_notary_id', '10355906', 'seller_notary_nom', 'Me. Eric PAILHES', 'numero_dossier', 'VA6482', 'hektor_annonce_id', '24113'), 9);
    neuf := coalesce((res->>'app_affaire_id')::bigint,
                     (select (j.payload_json->>'app_affaire_id')::bigint from public.app_console_job j where j.id::text = res->>'job_id'));
    delete from public.app_console_job where id::text = res->>'job_id';
    total := total + 1;
    IF (select valeur_app from public.app_affaire_champ_app where app_affaire_id = neuf and champ = 'notaire_mandant_id') = '10355906' and (select valeur_app from public.app_affaire_champ_app where app_affaire_id = neuf and champ = 'notaire_mandant_nom') = 'Me. Eric PAILHES' THEN ok := ok + 1; r := r || ' | T2 OK allume : id et nom au carnet';
    ELSE r := r || ' | T2 ECHEC allume : id et nom au carnet : ' || coalesce(concat_ws(' / ', (select valeur_app from public.app_affaire_champ_app where app_affaire_id = neuf and champ = 'notaire_mandant_id'), (select valeur_app from public.app_affaire_champ_app where app_affaire_id = neuf and champ = 'notaire_mandant_nom'), res::text), 'null'); END IF;
    -- T4 RIEN D'AUTRE NE CHANGE
    select string_agg(champ || '=' || valeur_app, ',' order by champ) into autres_allume
      from public.app_affaire_champ_app where app_affaire_id = neuf and champ not in ('notaire_mandant_id', 'notaire_mandant_nom');
    total := total + 1;
    IF autres_allume is not distinct from autres_eteint THEN ok := ok + 1; r := r || ' | T4 OK les autres lignes du carnet sont les memes';
    ELSE r := r || ' | T4 ECHEC les autres lignes du carnet sont les memes : ' || coalesce(autres_allume || ' <> ' || coalesce(autres_eteint, 'null'), 'null'); END IF;
    -- T3 ALLUME, SANS
    res := public.app_change_annonce_status_optimistic(1068399, 'offer', jsonb_build_object('amount', '115000', 'sale_price', '128787', 'transaction_date', '2026-10-23', 'validity_days', '15', 'retraction_days', '10', 'buyer_fees', '5000', 'buyer_fees_rate', '4.35', 'buyer_contact_id', '20000013', 'buyer_notary_id', '10064499', 'seller_notary_id', '10355906', 'seller_notary_nom', 'Me. Eric PAILHES', 'numero_dossier', 'VA6482', 'hektor_annonce_id', '24113') - 'seller_notary_id' - 'seller_notary_nom', 9);
    neuf := coalesce((res->>'app_affaire_id')::bigint,
                     (select (j.payload_json->>'app_affaire_id')::bigint from public.app_console_job j where j.id::text = res->>'job_id'));
    delete from public.app_console_job where id::text = res->>'job_id';
    total := total + 1;
    IF (select valeur_app from public.app_affaire_champ_app where app_affaire_id = neuf and champ = 'notaire_mandant_id') is null and (select valeur_app from public.app_affaire_champ_app where app_affaire_id = neuf and champ = 'notaire_mandant_nom') is null THEN ok := ok + 1; r := r || ' | T3 OK allume, sans notaire du vendeur : aucune ligne';
    ELSE r := r || ' | T3 ECHEC allume, sans notaire du vendeur : aucune ligne : ' || coalesce((select valeur_app from public.app_affaire_champ_app where app_affaire_id = neuf and champ = 'notaire_mandant_id'), 'null'); END IF;

    -- T5 MODIFICATION, AFFIRME
    delete from public.app_affaire_champ_app where app_affaire_id = 1001384 and champ in ('notaire_mandant_id', 'notaire_mandant_nom');
    res := public.app_modifier_affaire_optimistic(1001384, jsonb_build_object('amount', '115000', 'transaction_date', '2026-10-23', 'validity_days', '15', 'seller_notary_id', '10355906', 'seller_notary_nom', 'Me. Eric PAILHES', 'notaires_affirmes', jsonb_build_object('acquereur', false, 'mandant', true), 'champs_touches', jsonb_build_array('seller_notary_id')), 9);
    delete from public.app_console_job where id::text = res->>'job_id';
    total := total + 1;
    IF (select valeur_app from public.app_affaire_champ_app where app_affaire_id = 1001384 and champ = 'notaire_mandant_id') = '10355906' and (select valeur_app from public.app_affaire_champ_app where app_affaire_id = 1001384 and champ = 'notaire_mandant_nom') = 'Me. Eric PAILHES' THEN ok := ok + 1; r := r || ' | T5 OK modification affirmee : les deux lignes';
    ELSE r := r || ' | T5 ECHEC modification affirmee : les deux lignes : ' || coalesce(concat_ws(' / ', (select valeur_app from public.app_affaire_champ_app where app_affaire_id = 1001384 and champ = 'notaire_mandant_id'), res::text), 'null'); END IF;
    -- T6 MODIFICATION, NON AFFIRME
    delete from public.app_affaire_champ_app where app_affaire_id = 1001384 and champ in ('notaire_mandant_id', 'notaire_mandant_nom');
    res := public.app_modifier_affaire_optimistic(1001384, jsonb_build_object('amount', '115000', 'transaction_date', '2026-10-23', 'validity_days', '15', 'seller_notary_id', '10355906', 'seller_notary_nom', 'Me. Eric PAILHES', 'notaires_affirmes', jsonb_build_object('acquereur', false, 'mandant', true), 'champs_touches', jsonb_build_array('seller_notary_id')) || jsonb_build_object('notaires_affirmes', jsonb_build_object('acquereur', false, 'mandant', false)), 9);
    delete from public.app_console_job where id::text = res->>'job_id';
    total := total + 1;
    IF (select valeur_app from public.app_affaire_champ_app where app_affaire_id = 1001384 and champ = 'notaire_mandant_id') is null THEN ok := ok + 1; r := r || ' | T6 OK modification non affirmee : aucune ligne';
    ELSE r := r || ' | T6 ECHEC modification non affirmee : aucune ligne : ' || coalesce((select valeur_app from public.app_affaire_champ_app where app_affaire_id = 1001384 and champ = 'notaire_mandant_id'), 'null'); END IF;

    -- T7 L'INVERSE
    EXECUTE $exec_ic$ DO $retour_c_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($ca1$        ('notaire_id',         v_payload->>'buyer_notary_id'),$ca1$, chr(13), '')];
    neufs text[] := array[
        replace($cn1$        ('notaire_id',         v_payload->>'buyer_notary_id'),
        -- N (23/10/2026, chantier 8) : le notaire du VENDEUR d'une OFFRE. Hektor ne le garde pas sur une
        --   offre (0 sur 11 190) : le carnet le garde, et le compromis de la chaine le reprend.
        --   Interrupteur 'offre_notaire_vendeur'. Compromis et vente : inchanges (R1 les ecrit au registre).
        ('notaire_mandant_id',  case when v_kind = 'offre' and coalesce((select s.value from public.app_setting s where s.key = 'offre_notaire_vendeur'), 'off') = 'on'
                                 then v_payload->>'seller_notary_id' end),
        ('notaire_mandant_nom', case when v_kind = 'offre' and coalesce((select s.value from public.app_setting s where s.key = 'offre_notaire_vendeur'), 'off') = 'on'
                                  and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                                 then v_payload->>'seller_notary_nom' end),$cn1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = 'f9d024471d0740fa21fffa532e9aa2ae' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_change_annonce_status_optimistic porte deja l''empreinte d''avant (f9d02447).';
        RETURN;
    END IF;
    IF md5(d) <> '44697dd59587c644cdc021bd8f52108d' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, ni 44697dd5 (posee) ni f9d02447 (avant). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> 'f9d024471d0740fa21fffa532e9aa2ae' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic, le texte rendu a l''empreinte %s, attendu f9d02447. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour_c_rep$ $exec_ic$;
    EXECUTE $exec_im$ DO $retour_m_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($ma1$      ('notaire_id',         v_payload->>'buyer_notary_id',                             null::text),$ma1$, chr(13), ''),
        replace($ma2$             when 'notaire_id'         then array['buyer_notary_id']$ma2$, chr(13), '')];
    neufs text[] := array[
        replace($mn1$      ('notaire_id',         v_payload->>'buyer_notary_id',                             null::text),
      -- N (23/10/2026) : le notaire du VENDEUR d'une OFFRE, s'il est AFFIRME (voir la creation).
      ('notaire_mandant_id',  case when a.kind = 'offre' and (v_payload->'notaires_affirmes'->>'mandant') = 'true' and coalesce((select s.value from public.app_setting s where s.key = 'offre_notaire_vendeur'), 'off') = 'on'
                               then v_payload->>'seller_notary_id' end,                null::text),
      ('notaire_mandant_nom', case when a.kind = 'offre' and (v_payload->'notaires_affirmes'->>'mandant') = 'true' and coalesce((select s.value from public.app_setting s where s.key = 'offre_notaire_vendeur'), 'off') = 'on'
                                and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                               then v_payload->>'seller_notary_nom' end,               null::text),$mn1$, chr(13), ''),
        replace($mn2$             when 'notaire_id'         then array['buyer_notary_id']
             when 'notaire_mandant_id'  then array['seller_notary_id']
             when 'notaire_mandant_nom' then array['seller_notary_id']$mn2$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_modifier_affaire_optimistic porte deja l''empreinte d''avant (0dac8c86).';
        RETURN;
    END IF;
    IF md5(d) <> '43247de7ff89e395d3b6e970353a891b' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, ni 43247de7 (posee) ni 0dac8c86 (avant). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic, le texte rendu a l''empreinte %s, attendu 0dac8c86. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour_m_rep$ $exec_im$;
    total := total + 1;
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) = 'f9d024471d0740fa21fffa532e9aa2ae' and md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) = '0dac8c866a73517032bf23a9bd307b71' THEN ok := ok + 1; r := r || ' | T7 OK l inverse rend les deux empreintes';
    ELSE r := r || ' | T7 ECHEC l inverse rend les deux empreintes : ' || coalesce('empreinte differente', 'null'); END IF;

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
