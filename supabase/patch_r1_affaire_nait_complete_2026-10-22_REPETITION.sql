-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE R1 — la transaction naît complète                         22/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE : tout se passe dans UN bloc qui finit par une erreur
--   volontaire (« ESSAI ANNULE -- … ») ; le message porte le résultat. Rien ne reste :
--   ni la fonction modifiée, ni l'interrupteur, ni les transactions, ni les travaux.
--   (Seule la séquence des numéros avance de 5 : une séquence ne recule jamais.)
-- Elle joue LE VRAI PATCH (mêmes ancres), puis appelle la fonction COMME L'ÉCRAN, au nom
-- de Frédéric, sur l'annonce d'essai 63331 (dossier 10000009, « ESSAI 8A3 ») :
--   T1 ÉTEINT, compromis  → seuls les 4 champs d'avant (le témoin inverse) ;
--   T2 ALLUMÉ, offre      → validité, honoraires acquéreur, taux ; RIEN d'un compromis ;
--   T3 ALLUMÉ, compromis  → les 11 champs du compromis, fin de rétractation = date + 10,
--                           les deux notaires SANS 'saisie', PAS de mandants (non affirmés) ;
--   T4 ALLUMÉ, compromis, mandants AFFIRMÉS → mandants_json porte les deux ;
--   T5 ALLUMÉ, vente      → net, honoraires, notaires ; PAS d'acte, de séquestre, de fin ;
--   T6 le carnet reçoit le même nombre de lignes éteint et allumé ;
--   T7 une date impossible ne fait PAS échouer le geste ;
--   T8 l'inverse rend l'empreinte 3eec3f85.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    dossier bigint := 10000009;
    aid bigint;
    n_eteint int;
    n_allume int;
    l public.app_affaire_ledger%rowtype;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    IF NOT EXISTS (select 1 from public.app_dossier_current where app_dossier_id = dossier) THEN
        RAISE EXCEPTION '%', 'ARRET : le dossier d''essai 10000009 n''est plus dans le parc vivant -- la repetition ne prouverait rien.';
    END IF;
    IF sub IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : le compte admin de Frederic est introuvable.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    insert into public.app_setting (key, value, description, updated_at)
    values ('affaire_nait_complete', 'off',
            'Chantier 8 / R1 22/10/2026 : on = une offre, un compromis ou une vente cree dans l''app pose TOUS ses champs saisis dans leurs colonnes du registre au clic, par genre (voir supabase/patch_r1_affaire_nait_complete_2026-10-22.sql). off = comportement d''avant (4 champs au clic).',
            now())
    on conflict (key) do nothing;
    EXECUTE $exec_pose$ DO $pose_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  v_acq_json      jsonb;$a1$, chr(13), ''),
        replace($a2$    end loop;$a2$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  v_acq_json      jsonb;
  -- R1 22/10/2026 : interrupteur affaire_nait_complete
  v_nait_complete boolean := false;$n1$, chr(13), ''),
        replace($n2$    end loop;

    -- ─── R1 (22/10/2026, chantier 8) : LA TRANSACTION NAIT COMPLETE ───
    -- Avant, 4 champs sur 15 entraient au registre au clic (montant, date, acquereurs,
    -- mandat) ; les autres attendaient la nuit, ou ne vivaient qu'au carnet. Allume, chaque
    -- champ saisi entre dans SA colonne, et SEULEMENT pour le genre ou Hektor le porte
    -- (notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, section 4 D) :
    --   offre      validite, honoraires acquereur, taux
    --   compromis  date d'acte, sequestre, fin de retractation (date + jours), net vendeur,
    --              honoraires vendeur et acquereur, taux, les deux notaires, les mandants
    --   vente      net vendeur, honoraires vendeur et acquereur, taux, les deux notaires,
    --              les mandants
    -- ⚠ Les notaires vont dans notaire_acquereur_* / notaire_mandant_*, PAS dans notaire_id
    --   (colonne inerte depuis le 15/09), et SANS notaires_origine = 'saisie', qui figerait la
    --   ligne pour toujours : la console doit pouvoir la confirmer ou la corriger.
    -- ⚠ Les mandants SEULEMENT s'ils sont affirmes (un tableau) : sinon Hektor les deduit du
    --   mandat (regle du 16/09, decision de Frederic du 22/10).
    -- ⚠ Le carnet ne change pas. Une erreur ici ne fait JAMAIS echouer le geste (WARNING).
    -- Interrupteur eteint : RIEN NE CHANGE.
    v_nait_complete := coalesce((select s.value from public.app_setting s
                                  where s.key = 'affaire_nait_complete'), 'off') = 'on';
    if v_nait_complete then
      begin
        update public.app_affaire_ledger l set
          jours_validite        = case when v_kind = 'offre'
                                       then nullif(btrim(coalesce(v_payload->>'validity_days', '')), '')
                                       else l.jours_validite end,
          date_acte             = case when v_kind = 'compromis'
                                       then nullif(btrim(coalesce(v_payload->>'signature_date', '')), '')
                                       else l.date_acte end,
          sequestre             = case when v_kind = 'compromis'
                                       then nullif(btrim(coalesce(v_payload->>'sequestration', '')), '')
                                       else l.sequestre end,
          date_fin_retractation = case when v_kind = 'compromis'
                                        and coalesce(v_payload->>'transaction_date', '') ~ '^\d{4}-\d{2}-\d{2}'
                                        and btrim(coalesce(v_payload->>'retraction_days', '')) ~ '^\d{1,3}$'
                                       then to_char(left(v_payload->>'transaction_date', 10)::date
                                                    + btrim(v_payload->>'retraction_days')::int, 'YYYY-MM-DD')
                                       else l.date_fin_retractation end,
          prix_net_vendeur      = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'net_seller_price', '')), '')
                                       else l.prix_net_vendeur end,
          honoraires_entree     = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'seller_fees', '')), '')
                                       else l.honoraires_entree end,
          honoraires_sortie     = nullif(btrim(coalesce(v_payload->>'buyer_fees', '')), ''),
          taux_honoraires       = nullif(btrim(coalesce(v_payload->>'buyer_fees_rate', '')), ''),
          notaire_acquereur_id  = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), '')
                                       else l.notaire_acquereur_id end,
          notaire_acquereur_nom = case when v_kind in ('compromis', 'vente')
                                        and nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), '') is not null
                                       then nullif(btrim(coalesce(v_payload->>'buyer_notary_nom', '')), '')
                                       else l.notaire_acquereur_nom end,
          notaire_mandant_id    = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '')
                                       else l.notaire_mandant_id end,
          notaire_mandant_nom   = case when v_kind in ('compromis', 'vente')
                                        and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                                       then nullif(btrim(coalesce(v_payload->>'seller_notary_nom', '')), '')
                                       else l.notaire_mandant_nom end,
          mandants_json         = case when v_kind in ('compromis', 'vente')
                                        and jsonb_typeof(v_payload->'mandant_contact_ids') = 'array'
                                        and jsonb_array_length(v_payload->'mandant_contact_ids') > 0
                                       then public.app_acquereurs_json(array(
                                              select nullif(btrim(e), '')
                                                from jsonb_array_elements_text(v_payload->'mandant_contact_ids') e
                                               where nullif(btrim(e), '') is not null))
                                       else l.mandants_json end
         where l.app_affaire_id = v_affaire_id;
      exception when others then
        raise warning 'R1 affaire_nait_complete : colonnes non posees pour l''affaire % (%)', v_affaire_id, sqlerrm;
      end;
    end if;$n2$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = 'caab6b6c38091ba5b087f8819147756f' THEN
        RAISE NOTICE '%', 'Deja pose : app_change_annonce_status_optimistic porte deja l''empreinte caab6b6c. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> '3eec3f85ad9bcd5ed4b519e229936a23' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, attendu 3eec3f85 (22/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> 'caab6b6c38091ba5b087f8819147756f' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte neuf a l''empreinte %s, attendu caab6b6c (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) <> 'caab6b6c38091ba5b087f8819147756f' THEN
        RAISE EXCEPTION '%', 'ARRET : apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_rep$ $exec_pose$;

    -- T1 ETEINT
    update public.app_setting set value = 'off' where key = 'affaire_nait_complete';
    aid := (public.app_change_annonce_status_optimistic(dossier, 'compromise', jsonb_build_object('amount', '170000', 'sale_price', '180000', 'transaction_date', '2026-10-22',
        'buyer_contact_id', '20000008', 'buyer_fees', '5000', 'buyer_fees_rate', '3',
        'validity_days', '12', 'signature_date', '2027-01-15', 'sequestration', '9000',
        'retraction_days', '10', 'net_seller_price', '160000', 'seller_fees', '10000',
        'buyer_notary_id', '122190', 'buyer_notary_nom', 'Me. ESSAI ACQUEREUR',
        'seller_notary_id', '300465', 'seller_notary_nom', 'Me. ESSAI VENDEUR',
        'numero_mandat', '99999', 'titre_bien', 'ESSAI R1'), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    select count(*) into n_eteint from public.app_affaire_champ_app where app_affaire_id = aid;
    total := total + 1;
    IF l.date_acte is null and l.prix_net_vendeur is null and l.notaire_mandant_id is null and l.montant = '170000' THEN ok := ok + 1; r := r || ' | T1 OK eteint : date d acte, net, notaires restent VIDES';
    ELSE r := r || ' | T1 ECHEC eteint : date d acte, net, notaires restent VIDES : ' || coalesce(row_to_json(l)::text, 'null'); END IF;

    -- T2 ALLUME, OFFRE
    update public.app_setting set value = 'on' where key = 'affaire_nait_complete';
    aid := (public.app_change_annonce_status_optimistic(dossier, 'offer', jsonb_build_object('amount', '170000', 'sale_price', '180000', 'transaction_date', '2026-10-22',
        'buyer_contact_id', '20000008', 'buyer_fees', '5000', 'buyer_fees_rate', '3',
        'validity_days', '12', 'signature_date', '2027-01-15', 'sequestration', '9000',
        'retraction_days', '10', 'net_seller_price', '160000', 'seller_fees', '10000',
        'buyer_notary_id', '122190', 'buyer_notary_nom', 'Me. ESSAI ACQUEREUR',
        'seller_notary_id', '300465', 'seller_notary_nom', 'Me. ESSAI VENDEUR',
        'numero_mandat', '99999', 'titre_bien', 'ESSAI R1'), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    total := total + 1;
    IF l.jours_validite = '12' and l.honoraires_sortie = '5000' and l.taux_honoraires = '3' THEN ok := ok + 1; r := r || ' | T2a OK offre : validite 12, honoraires acquereur 5000, taux 3';
    ELSE r := r || ' | T2a ECHEC offre : validite 12, honoraires acquereur 5000, taux 3 : ' || coalesce(row_to_json(l)::text, 'null'); END IF;
    total := total + 1;
    IF l.date_acte is null and l.sequestre is null and l.prix_net_vendeur is null and l.honoraires_entree is null and l.notaire_acquereur_id is null and l.notaire_mandant_id is null and l.date_fin_retractation is null THEN ok := ok + 1; r := r || ' | T2b OK offre : ni acte, ni sequestre, ni net, ni vendeur, ni notaire';
    ELSE r := r || ' | T2b ECHEC offre : ni acte, ni sequestre, ni net, ni vendeur, ni notaire : ' || coalesce(row_to_json(l)::text, 'null'); END IF;

    -- T3 ALLUME, COMPROMIS, mandants NON affirmes
    aid := (public.app_change_annonce_status_optimistic(dossier, 'compromise', jsonb_build_object('amount', '170000', 'sale_price', '180000', 'transaction_date', '2026-10-22',
        'buyer_contact_id', '20000008', 'buyer_fees', '5000', 'buyer_fees_rate', '3',
        'validity_days', '12', 'signature_date', '2027-01-15', 'sequestration', '9000',
        'retraction_days', '10', 'net_seller_price', '160000', 'seller_fees', '10000',
        'buyer_notary_id', '122190', 'buyer_notary_nom', 'Me. ESSAI ACQUEREUR',
        'seller_notary_id', '300465', 'seller_notary_nom', 'Me. ESSAI VENDEUR',
        'numero_mandat', '99999', 'titre_bien', 'ESSAI R1'), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    select count(*) into n_allume from public.app_affaire_champ_app where app_affaire_id = aid;
    total := total + 1;
    IF l.date_acte = '2027-01-15' and l.sequestre = '9000' and l.prix_net_vendeur = '160000' and l.honoraires_entree = '10000' and l.honoraires_sortie = '5000' and l.taux_honoraires = '3' THEN ok := ok + 1; r := r || ' | T3a OK compromis : acte, sequestre, net, vendeur, acquereur, taux';
    ELSE r := r || ' | T3a ECHEC compromis : acte, sequestre, net, vendeur, acquereur, taux : ' || coalesce(row_to_json(l)::text, 'null'); END IF;
    total := total + 1;
    IF l.date_fin_retractation = '2026-11-01' THEN ok := ok + 1; r := r || ' | T3b OK compromis : fin de retractation = 2026-11-01 (date + 10)';
    ELSE r := r || ' | T3b ECHEC compromis : fin de retractation = 2026-11-01 (date + 10) : ' || coalesce(l.date_fin_retractation, 'null'); END IF;
    total := total + 1;
    IF l.notaire_acquereur_id = '122190' and l.notaire_acquereur_nom = 'Me. ESSAI ACQUEREUR' and l.notaire_mandant_id = '300465' and l.notaire_mandant_nom = 'Me. ESSAI VENDEUR' and l.notaires_origine is null and l.notaire_id is null THEN ok := ok + 1; r := r || ' | T3c OK compromis : les deux notaires avec leur nom, SANS saisie';
    ELSE r := r || ' | T3c ECHEC compromis : les deux notaires avec leur nom, SANS saisie : ' || coalesce(row_to_json(l)::text, 'null'); END IF;
    total := total + 1;
    IF l.jours_validite is null and l.mandants_json is null THEN ok := ok + 1; r := r || ' | T3d OK compromis : pas de validite, pas de mandants (non affirmes)';
    ELSE r := r || ' | T3d ECHEC compromis : pas de validite, pas de mandants (non affirmes) : ' || coalesce(row_to_json(l)::text, 'null'); END IF;
    total := total + 1;
    IF n_eteint = n_allume and n_allume > 0 THEN ok := ok + 1; r := r || ' | T6 OK le carnet recoit autant de lignes eteint et allume';
    ELSE r := r || ' | T6 ECHEC le carnet recoit autant de lignes eteint et allume : ' || coalesce(n_eteint || ' / ' || n_allume, 'null'); END IF;

    -- T4 ALLUME, COMPROMIS, mandants AFFIRMES
    aid := (public.app_change_annonce_status_optimistic(dossier, 'compromise', jsonb_build_object('amount', '170000', 'sale_price', '180000', 'transaction_date', '2026-10-22',
        'buyer_contact_id', '20000008', 'buyer_fees', '5000', 'buyer_fees_rate', '3',
        'validity_days', '12', 'signature_date', '2027-01-15', 'sequestration', '9000',
        'retraction_days', '10', 'net_seller_price', '160000', 'seller_fees', '10000',
        'buyer_notary_id', '122190', 'buyer_notary_nom', 'Me. ESSAI ACQUEREUR',
        'seller_notary_id', '300465', 'seller_notary_nom', 'Me. ESSAI VENDEUR',
        'numero_mandat', '99999', 'titre_bien', 'ESSAI R1', 'mandant_contact_ids', jsonb_build_array('20000009', '20000007')), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    total := total + 1;
    IF jsonb_array_length(l.mandants_json) = 2 and l.mandants_json->0->>'id' = '20000009' THEN ok := ok + 1; r := r || ' | T4 OK compromis : les 2 mandants affirmes, dans l ordre';
    ELSE r := r || ' | T4 ECHEC compromis : les 2 mandants affirmes, dans l ordre : ' || coalesce(l.mandants_json::text, 'null'); END IF;

    -- T5 ALLUME, VENTE
    aid := (public.app_change_annonce_status_optimistic(dossier, 'sold', jsonb_build_object('amount', '170000', 'sale_price', '180000', 'transaction_date', '2026-10-22',
        'buyer_contact_id', '20000008', 'buyer_fees', '5000', 'buyer_fees_rate', '3',
        'validity_days', '12', 'signature_date', '2027-01-15', 'sequestration', '9000',
        'retraction_days', '10', 'net_seller_price', '160000', 'seller_fees', '10000',
        'buyer_notary_id', '122190', 'buyer_notary_nom', 'Me. ESSAI ACQUEREUR',
        'seller_notary_id', '300465', 'seller_notary_nom', 'Me. ESSAI VENDEUR',
        'numero_mandat', '99999', 'titre_bien', 'ESSAI R1'), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    total := total + 1;
    IF l.prix_net_vendeur = '160000' and l.honoraires_entree = '10000' and l.honoraires_sortie = '5000' and l.notaire_mandant_id = '300465' THEN ok := ok + 1; r := r || ' | T5a OK vente : net, vendeur, acquereur, notaires';
    ELSE r := r || ' | T5a ECHEC vente : net, vendeur, acquereur, notaires : ' || coalesce(row_to_json(l)::text, 'null'); END IF;
    total := total + 1;
    IF l.date_acte is null and l.sequestre is null and l.date_fin_retractation is null and l.jours_validite is null THEN ok := ok + 1; r := r || ' | T5b OK vente : ni acte, ni sequestre, ni fin, ni validite';
    ELSE r := r || ' | T5b ECHEC vente : ni acte, ni sequestre, ni fin, ni validite : ' || coalesce(row_to_json(l)::text, 'null'); END IF;

    -- T7 UNE DATE IMPOSSIBLE NE FAIT PAS ECHOUER LE GESTE
    aid := (public.app_change_annonce_status_optimistic(dossier, 'compromise', jsonb_build_object('amount', '170000', 'sale_price', '180000', 'transaction_date', '2026-10-22',
        'buyer_contact_id', '20000008', 'buyer_fees', '5000', 'buyer_fees_rate', '3',
        'validity_days', '12', 'signature_date', '2027-01-15', 'sequestration', '9000',
        'retraction_days', '10', 'net_seller_price', '160000', 'seller_fees', '10000',
        'buyer_notary_id', '122190', 'buyer_notary_nom', 'Me. ESSAI ACQUEREUR',
        'seller_notary_id', '300465', 'seller_notary_nom', 'Me. ESSAI VENDEUR',
        'numero_mandat', '99999', 'titre_bien', 'ESSAI R1') || jsonb_build_object('transaction_date', '2026-13-45'), 0)->>'app_affaire_id')::bigint;
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    total := total + 1;
    IF l.app_affaire_id is not null THEN ok := ok + 1; r := r || ' | T7 OK date impossible : le geste passe, la ligne existe';
    ELSE r := r || ' | T7 ECHEC date impossible : le geste passe, la ligne existe : ' || coalesce(aid::text, 'null'); END IF;

    -- T8 L'INVERSE
    EXECUTE $exec_inv$ DO $retour$
DECLARE
    d text := replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  v_acq_json      jsonb;$a1$, chr(13), ''),
        replace($a2$    end loop;$a2$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  v_acq_json      jsonb;
  -- R1 22/10/2026 : interrupteur affaire_nait_complete
  v_nait_complete boolean := false;$n1$, chr(13), ''),
        replace($n2$    end loop;

    -- ─── R1 (22/10/2026, chantier 8) : LA TRANSACTION NAIT COMPLETE ───
    -- Avant, 4 champs sur 15 entraient au registre au clic (montant, date, acquereurs,
    -- mandat) ; les autres attendaient la nuit, ou ne vivaient qu'au carnet. Allume, chaque
    -- champ saisi entre dans SA colonne, et SEULEMENT pour le genre ou Hektor le porte
    -- (notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, section 4 D) :
    --   offre      validite, honoraires acquereur, taux
    --   compromis  date d'acte, sequestre, fin de retractation (date + jours), net vendeur,
    --              honoraires vendeur et acquereur, taux, les deux notaires, les mandants
    --   vente      net vendeur, honoraires vendeur et acquereur, taux, les deux notaires,
    --              les mandants
    -- ⚠ Les notaires vont dans notaire_acquereur_* / notaire_mandant_*, PAS dans notaire_id
    --   (colonne inerte depuis le 15/09), et SANS notaires_origine = 'saisie', qui figerait la
    --   ligne pour toujours : la console doit pouvoir la confirmer ou la corriger.
    -- ⚠ Les mandants SEULEMENT s'ils sont affirmes (un tableau) : sinon Hektor les deduit du
    --   mandat (regle du 16/09, decision de Frederic du 22/10).
    -- ⚠ Le carnet ne change pas. Une erreur ici ne fait JAMAIS echouer le geste (WARNING).
    -- Interrupteur eteint : RIEN NE CHANGE.
    v_nait_complete := coalesce((select s.value from public.app_setting s
                                  where s.key = 'affaire_nait_complete'), 'off') = 'on';
    if v_nait_complete then
      begin
        update public.app_affaire_ledger l set
          jours_validite        = case when v_kind = 'offre'
                                       then nullif(btrim(coalesce(v_payload->>'validity_days', '')), '')
                                       else l.jours_validite end,
          date_acte             = case when v_kind = 'compromis'
                                       then nullif(btrim(coalesce(v_payload->>'signature_date', '')), '')
                                       else l.date_acte end,
          sequestre             = case when v_kind = 'compromis'
                                       then nullif(btrim(coalesce(v_payload->>'sequestration', '')), '')
                                       else l.sequestre end,
          date_fin_retractation = case when v_kind = 'compromis'
                                        and coalesce(v_payload->>'transaction_date', '') ~ '^\d{4}-\d{2}-\d{2}'
                                        and btrim(coalesce(v_payload->>'retraction_days', '')) ~ '^\d{1,3}$'
                                       then to_char(left(v_payload->>'transaction_date', 10)::date
                                                    + btrim(v_payload->>'retraction_days')::int, 'YYYY-MM-DD')
                                       else l.date_fin_retractation end,
          prix_net_vendeur      = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'net_seller_price', '')), '')
                                       else l.prix_net_vendeur end,
          honoraires_entree     = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'seller_fees', '')), '')
                                       else l.honoraires_entree end,
          honoraires_sortie     = nullif(btrim(coalesce(v_payload->>'buyer_fees', '')), ''),
          taux_honoraires       = nullif(btrim(coalesce(v_payload->>'buyer_fees_rate', '')), ''),
          notaire_acquereur_id  = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), '')
                                       else l.notaire_acquereur_id end,
          notaire_acquereur_nom = case when v_kind in ('compromis', 'vente')
                                        and nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), '') is not null
                                       then nullif(btrim(coalesce(v_payload->>'buyer_notary_nom', '')), '')
                                       else l.notaire_acquereur_nom end,
          notaire_mandant_id    = case when v_kind in ('compromis', 'vente')
                                       then nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '')
                                       else l.notaire_mandant_id end,
          notaire_mandant_nom   = case when v_kind in ('compromis', 'vente')
                                        and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                                       then nullif(btrim(coalesce(v_payload->>'seller_notary_nom', '')), '')
                                       else l.notaire_mandant_nom end,
          mandants_json         = case when v_kind in ('compromis', 'vente')
                                        and jsonb_typeof(v_payload->'mandant_contact_ids') = 'array'
                                        and jsonb_array_length(v_payload->'mandant_contact_ids') > 0
                                       then public.app_acquereurs_json(array(
                                              select nullif(btrim(e), '')
                                                from jsonb_array_elements_text(v_payload->'mandant_contact_ids') e
                                               where nullif(btrim(e), '') is not null))
                                       else l.mandants_json end
         where l.app_affaire_id = v_affaire_id;
      exception when others then
        raise warning 'R1 affaire_nait_complete : colonnes non posees pour l''affaire % (%)', v_affaire_id, sqlerrm;
      end;
    end if;$n2$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '3eec3f85ad9bcd5ed4b519e229936a23' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_change_annonce_status_optimistic porte deja l''empreinte du 22/10 (3eec3f85).';
        RETURN;
    END IF;
    IF md5(d) <> 'caab6b6c38091ba5b087f8819147756f' THEN
        RAISE EXCEPTION '%', format('ARRET : app_change_annonce_status_optimistic a l''empreinte %s, ni caab6b6c (posee) ni 3eec3f85 (d''avant). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '3eec3f85ad9bcd5ed4b519e229936a23' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte rendu a l''empreinte %s, attendu 3eec3f85. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour$ $exec_inv$;
    total := total + 1;
    IF md5(replace(pg_get_functiondef('public.app_change_annonce_status_optimistic(bigint,text,jsonb,integer)'::regprocedure), chr(13), '')) = '3eec3f85ad9bcd5ed4b519e229936a23' THEN ok := ok + 1; r := r || ' | T8 OK l inverse rend 3eec3f85';
    ELSE r := r || ' | T8 ECHEC l inverse rend 3eec3f85 : ' || coalesce('empreinte differente', 'null'); END IF;

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
