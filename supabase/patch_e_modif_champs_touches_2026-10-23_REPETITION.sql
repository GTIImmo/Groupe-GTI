-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DU POINT E — la modification n'inscrit que ce qui a été tapé    23/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste, ni la
--   fonction modifiée, ni l'interrupteur, ni le carnet, ni le registre, ni les travaux.
-- Le VRAI PATCH, puis la fonction appelée COMME L'ÉCRAN, au nom de Frédéric, sur l'offre
-- d'essai 33026 (app_affaire_id 1000001, bac à sable 62774), avec une charge PRÉREMPLIE :
--   T1 ÉTEINT, liste ['amount']           → les 6 champs au carnet (le témoin inverse : le défaut)
--   T2 ALLUMÉ, liste ['amount']           → le montant SEUL au carnet, montant changé, date non
--   T3 ALLUMÉ, liste vide                 → rien au carnet, registre inchangé
--   T4 ALLUMÉ, SANS liste (écran d'avant) → les 6 champs, comme avant
--   T5 ALLUMÉ, date + validité            → ces deux-là seuls, date changée, montant non
--   T6 ALLUMÉ, prix de vente seul         → montant ET prix public (la paire), montant changé
--   T7 le retour porte `champs_touches` · T8 l'inverse rend a5297281.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    aid bigint := 1000001;
    orig public.app_affaire_ledger%rowtype;
    l public.app_affaire_ledger%rowtype;
    res jsonb;
    vus text[];
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    select * into orig from public.app_affaire_ledger where app_affaire_id = aid;
    IF orig.app_affaire_id IS NULL OR coalesce(orig.hektor_affaire_id, '') = '' OR orig.present_in_hektor IS NOT TRUE THEN
        RAISE EXCEPTION '%', 'ARRET : l''offre d''essai 1000001 n''est plus modifiable (numero Hektor ou presence) -- la repetition ne prouverait rien.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    insert into public.app_setting (key, value, description, updated_at)
    values ('affaire_modif_champs_touches', 'off',
            'Chantier 8 / point E 23/10/2026 : on = en MODIFICATION d''une transaction, seuls les champs que l''ecran declare TAPES (champs_touches) entrent au carnet et au registre ; le prerempli n''y entre plus (voir supabase/patch_e_modif_champs_touches_2026-10-23.sql). off, ou liste absente = comportement d''avant.',
            now())
    on conflict (key) do nothing;
    EXECUTE $exec_pose$ DO $pose_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  v_cible     text;$a1$, chr(13), ''),
        replace($a2$  v_payload := coalesce(job_payload, '{}'::jsonb);$a2$, chr(13), ''),
        replace($a3$     set montant = coalesce(nullif(btrim(coalesce(v_payload->>'amount',$a3$, chr(13), ''),
        replace($a4$                                                  v_payload->>'sale_price', '')), ''), montant),$a4$, chr(13), ''),
        replace($a5$         date    = coalesce(nullif(btrim(coalesce(v_payload->>'transaction_date', '')), ''), date)$a5$, chr(13), ''),
        replace($a6$    if v_valeur is not null then$a6$, chr(13), ''),
        replace($a7$                            'champs_au_carnet', v_au_carnet);$a7$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  v_cible     text;
  v_touches   jsonb;   -- point E 23/10/2026 (interrupteur affaire_modif_champs_touches)
  v_maj       jsonb;$n1$, chr(13), ''),
        replace($n2$  v_payload := coalesce(job_payload, '{}'::jsonb);

  -- ─── POINT E (23/10/2026, chantier 8) : CE QUI A ETE TAPE, PAS CE QUI ETAIT AFFICHE ───
  -- La modale s'ouvre PREREMPLIE et la charge part ENTIERE (le worker de l'offre reconstruit
  -- le formulaire de Hektor avec elle : on ne l'allege pas). Mais tout champ non vide entrait
  -- au carnet -- et le carnet PRIME a l'ecran. Mesure : offre 33094 (13/10), 6 lignes dont au
  -- moins 4 de prerempli (prix de l'annonce 180 000, 10 jours de retractation sur une offre).
  -- L'ecran envoie desormais `champs_touches` : les cles qu'une SAISIE a changees.
  -- Allume ET liste presente : seules ces cles vont au carnet et au registre (montant, date).
  -- Liste absente (ecran d'avant, en cache) ou eteint : comportement d'avant.
  -- ⚠ Le montant se juge sur la PAIRE amount / sale_price : l'une touchee, on garde les deux
  --   comme avant (coalesce(amount, sale_price)) -- sinon un prix de vente touche seul
  --   deviendrait le montant d'un compromis.
  if coalesce((select s.value from public.app_setting s
                where s.key = 'affaire_modif_champs_touches'), 'off') = 'on'
     and jsonb_typeof(v_payload->'champs_touches') = 'array' then
    v_touches := v_payload->'champs_touches';
  end if;
  v_maj := v_payload;
  if v_touches is not null then
    if not (v_touches ?| array['amount', 'sale_price']) then
      v_maj := v_maj - array['amount', 'sale_price'];
    end if;
    if not (v_touches ? 'transaction_date') then
      v_maj := v_maj - 'transaction_date';
    end if;
  end if;$n2$, chr(13), ''),
        replace($n3$     set montant = coalesce(nullif(btrim(coalesce(v_maj->>'amount',$n3$, chr(13), ''),
        replace($n4$                                                  v_maj->>'sale_price', '')), ''), montant),$n4$, chr(13), ''),
        replace($n5$         date    = coalesce(nullif(btrim(coalesce(v_maj->>'transaction_date', '')), ''), date)$n5$, chr(13), ''),
        replace($n6$    if v_valeur is not null
       -- point E : allume avec une liste, seul ce qui a ete TAPE entre au carnet
       and (v_touches is null or v_touches ?| (case v_champ.champ
             when 'montant'            then array['amount', 'sale_price']
             when 'date'               then array['transaction_date']
             when 'date_acte'          then array['signature_date']
             when 'sequestre'          then array['sequestration']
             when 'prix_net_vendeur'   then array['net_seller_price']
             when 'prix_publique'      then array['sale_price']
             when 'honoraires'         then array['buyer_fees']
             when 'honoraires_entree'  then array['seller_fees']
             when 'numero_mandat'      then array['selected_mandat']
             when 'jours_validite'     then array['validity_days']
             when 'jours_retractation' then array['retraction_days']
             when 'notaire_id'         then array['buyer_notary_id']
             when 'taux_honoraires'    then array['buyer_fees_rate']
             else array['--champ-inconnu--'] end)) then$n6$, chr(13), ''),
        replace($n7$                            'champs_au_carnet', v_au_carnet,
                            'champs_touches',   v_touches);$n7$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '049643b8a2042904544586f400eb8fe3' THEN
        RAISE NOTICE '%', 'Deja pose : app_modifier_affaire_optimistic porte deja l''empreinte 049643b8. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> 'a5297281686c699b89ac2fbc61864fe4' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, attendu a5297281 (mesuree le 23/10). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '049643b8a2042904544586f400eb8fe3' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte neuf a l''empreinte %s, attendu 049643b8 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) <> '049643b8a2042904544586f400eb8fe3' THEN
        RAISE EXCEPTION '%', 'ARRET : apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_rep$ $exec_pose$;

    update public.app_setting set value = 'off' where key = 'affaire_modif_champs_touches';
    delete from public.app_affaire_champ_app where app_affaire_id = aid;
    update public.app_affaire_ledger set montant = orig.montant, date = orig.date where app_affaire_id = aid;
    res := public.app_modifier_affaire_optimistic(aid, jsonb_build_object('amount', '151234', 'sale_price', '180000', 'transaction_date', '2026-08-31', 'validity_days', '10', 'retraction_days', '10', 'selected_mandat', '18836', 'champs_touches', '["amount"]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    select coalesce(array_agg(champ order by champ), array[]::text[]) into vus from public.app_affaire_champ_app where app_affaire_id = aid;
    total := total + 1;
    IF vus = array['date', 'jours_retractation', 'jours_validite', 'montant', 'numero_mandat', 'prix_publique']::text[] and l.montant::numeric = 151234 and l.date::date = date '2026-08-31' and (res->>'ok')::boolean THEN ok := ok + 1; r := r || ' | T1 OK eteint : les 6 champs, le defaut d avant';
    ELSE r := r || ' | T1 ECHEC eteint : les 6 champs, le defaut d avant : ' || coalesce(array_to_string(vus, ',') || ' / montant ' || coalesce(l.montant::text, 'null') || ' / date ' || coalesce(l.date::text, 'null'), 'null'); END IF;

    update public.app_setting set value = 'on' where key = 'affaire_modif_champs_touches';
    delete from public.app_affaire_champ_app where app_affaire_id = aid;
    update public.app_affaire_ledger set montant = orig.montant, date = orig.date where app_affaire_id = aid;
    res := public.app_modifier_affaire_optimistic(aid, jsonb_build_object('amount', '151234', 'sale_price', '180000', 'transaction_date', '2026-08-31', 'validity_days', '10', 'retraction_days', '10', 'selected_mandat', '18836', 'champs_touches', '["amount"]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    select coalesce(array_agg(champ order by champ), array[]::text[]) into vus from public.app_affaire_champ_app where app_affaire_id = aid;
    total := total + 1;
    IF vus = array['montant']::text[] and l.montant::numeric = 151234 and l.date = orig.date and (res->>'ok')::boolean THEN ok := ok + 1; r := r || ' | T2 OK allume, montant seul';
    ELSE r := r || ' | T2 ECHEC allume, montant seul : ' || coalesce(array_to_string(vus, ',') || ' / montant ' || coalesce(l.montant::text, 'null') || ' / date ' || coalesce(l.date::text, 'null'), 'null'); END IF;
    delete from public.app_affaire_champ_app where app_affaire_id = aid;
    update public.app_affaire_ledger set montant = orig.montant, date = orig.date where app_affaire_id = aid;
    res := public.app_modifier_affaire_optimistic(aid, jsonb_build_object('amount', '151234', 'sale_price', '180000', 'transaction_date', '2026-08-31', 'validity_days', '10', 'retraction_days', '10', 'selected_mandat', '18836', 'champs_touches', '[]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    select coalesce(array_agg(champ order by champ), array[]::text[]) into vus from public.app_affaire_champ_app where app_affaire_id = aid;
    total := total + 1;
    IF vus = array[]::text[] and l.montant = orig.montant and l.date = orig.date and (res->>'ok')::boolean THEN ok := ok + 1; r := r || ' | T3 OK allume, liste vide : rien';
    ELSE r := r || ' | T3 ECHEC allume, liste vide : rien : ' || coalesce(array_to_string(vus, ',') || ' / montant ' || coalesce(l.montant::text, 'null') || ' / date ' || coalesce(l.date::text, 'null'), 'null'); END IF;
    delete from public.app_affaire_champ_app where app_affaire_id = aid;
    update public.app_affaire_ledger set montant = orig.montant, date = orig.date where app_affaire_id = aid;
    res := public.app_modifier_affaire_optimistic(aid, jsonb_build_object('amount', '151234', 'sale_price', '180000', 'transaction_date', '2026-08-31', 'validity_days', '10', 'retraction_days', '10', 'selected_mandat', '18836'), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    select coalesce(array_agg(champ order by champ), array[]::text[]) into vus from public.app_affaire_champ_app where app_affaire_id = aid;
    total := total + 1;
    IF vus = array['date', 'jours_retractation', 'jours_validite', 'montant', 'numero_mandat', 'prix_publique']::text[] and l.montant::numeric = 151234 and l.date::date = date '2026-08-31' and (res->>'ok')::boolean THEN ok := ok + 1; r := r || ' | T4 OK allume, sans liste : comme avant';
    ELSE r := r || ' | T4 ECHEC allume, sans liste : comme avant : ' || coalesce(array_to_string(vus, ',') || ' / montant ' || coalesce(l.montant::text, 'null') || ' / date ' || coalesce(l.date::text, 'null'), 'null'); END IF;
    delete from public.app_affaire_champ_app where app_affaire_id = aid;
    update public.app_affaire_ledger set montant = orig.montant, date = orig.date where app_affaire_id = aid;
    res := public.app_modifier_affaire_optimistic(aid, jsonb_build_object('amount', '151234', 'sale_price', '180000', 'transaction_date', '2026-08-31', 'validity_days', '10', 'retraction_days', '10', 'selected_mandat', '18836', 'champs_touches', '["transaction_date", "validity_days"]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    select coalesce(array_agg(champ order by champ), array[]::text[]) into vus from public.app_affaire_champ_app where app_affaire_id = aid;
    total := total + 1;
    IF vus = array['date', 'jours_validite']::text[] and l.montant = orig.montant and l.date::date = date '2026-08-31' and (res->>'ok')::boolean THEN ok := ok + 1; r := r || ' | T5 OK allume, date et validite seules';
    ELSE r := r || ' | T5 ECHEC allume, date et validite seules : ' || coalesce(array_to_string(vus, ',') || ' / montant ' || coalesce(l.montant::text, 'null') || ' / date ' || coalesce(l.date::text, 'null'), 'null'); END IF;
    delete from public.app_affaire_champ_app where app_affaire_id = aid;
    update public.app_affaire_ledger set montant = orig.montant, date = orig.date where app_affaire_id = aid;
    res := public.app_modifier_affaire_optimistic(aid, jsonb_build_object('amount', '151234', 'sale_price', '180000', 'transaction_date', '2026-08-31', 'validity_days', '10', 'retraction_days', '10', 'selected_mandat', '18836', 'champs_touches', '["sale_price"]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = aid;
    select coalesce(array_agg(champ order by champ), array[]::text[]) into vus from public.app_affaire_champ_app where app_affaire_id = aid;
    total := total + 1;
    IF vus = array['montant', 'prix_publique']::text[] and l.montant::numeric = 151234 and l.date = orig.date and (res->>'ok')::boolean THEN ok := ok + 1; r := r || ' | T6 OK allume, prix de vente seul : la paire';
    ELSE r := r || ' | T6 ECHEC allume, prix de vente seul : la paire : ' || coalesce(array_to_string(vus, ',') || ' / montant ' || coalesce(l.montant::text, 'null') || ' / date ' || coalesce(l.date::text, 'null'), 'null'); END IF;
    total := total + 1;
    IF res->'champs_touches' = '["sale_price"]'::jsonb THEN ok := ok + 1; r := r || ' | T7 OK le retour porte champs_touches';
    ELSE r := r || ' | T7 ECHEC le retour porte champs_touches : ' || coalesce(res::text, 'null'); END IF;

    -- T8 L'INVERSE
    EXECUTE $exec_inv$ DO $retour$
DECLARE
    d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  v_cible     text;$a1$, chr(13), ''),
        replace($a2$  v_payload := coalesce(job_payload, '{}'::jsonb);$a2$, chr(13), ''),
        replace($a3$     set montant = coalesce(nullif(btrim(coalesce(v_payload->>'amount',$a3$, chr(13), ''),
        replace($a4$                                                  v_payload->>'sale_price', '')), ''), montant),$a4$, chr(13), ''),
        replace($a5$         date    = coalesce(nullif(btrim(coalesce(v_payload->>'transaction_date', '')), ''), date)$a5$, chr(13), ''),
        replace($a6$    if v_valeur is not null then$a6$, chr(13), ''),
        replace($a7$                            'champs_au_carnet', v_au_carnet);$a7$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  v_cible     text;
  v_touches   jsonb;   -- point E 23/10/2026 (interrupteur affaire_modif_champs_touches)
  v_maj       jsonb;$n1$, chr(13), ''),
        replace($n2$  v_payload := coalesce(job_payload, '{}'::jsonb);

  -- ─── POINT E (23/10/2026, chantier 8) : CE QUI A ETE TAPE, PAS CE QUI ETAIT AFFICHE ───
  -- La modale s'ouvre PREREMPLIE et la charge part ENTIERE (le worker de l'offre reconstruit
  -- le formulaire de Hektor avec elle : on ne l'allege pas). Mais tout champ non vide entrait
  -- au carnet -- et le carnet PRIME a l'ecran. Mesure : offre 33094 (13/10), 6 lignes dont au
  -- moins 4 de prerempli (prix de l'annonce 180 000, 10 jours de retractation sur une offre).
  -- L'ecran envoie desormais `champs_touches` : les cles qu'une SAISIE a changees.
  -- Allume ET liste presente : seules ces cles vont au carnet et au registre (montant, date).
  -- Liste absente (ecran d'avant, en cache) ou eteint : comportement d'avant.
  -- ⚠ Le montant se juge sur la PAIRE amount / sale_price : l'une touchee, on garde les deux
  --   comme avant (coalesce(amount, sale_price)) -- sinon un prix de vente touche seul
  --   deviendrait le montant d'un compromis.
  if coalesce((select s.value from public.app_setting s
                where s.key = 'affaire_modif_champs_touches'), 'off') = 'on'
     and jsonb_typeof(v_payload->'champs_touches') = 'array' then
    v_touches := v_payload->'champs_touches';
  end if;
  v_maj := v_payload;
  if v_touches is not null then
    if not (v_touches ?| array['amount', 'sale_price']) then
      v_maj := v_maj - array['amount', 'sale_price'];
    end if;
    if not (v_touches ? 'transaction_date') then
      v_maj := v_maj - 'transaction_date';
    end if;
  end if;$n2$, chr(13), ''),
        replace($n3$     set montant = coalesce(nullif(btrim(coalesce(v_maj->>'amount',$n3$, chr(13), ''),
        replace($n4$                                                  v_maj->>'sale_price', '')), ''), montant),$n4$, chr(13), ''),
        replace($n5$         date    = coalesce(nullif(btrim(coalesce(v_maj->>'transaction_date', '')), ''), date)$n5$, chr(13), ''),
        replace($n6$    if v_valeur is not null
       -- point E : allume avec une liste, seul ce qui a ete TAPE entre au carnet
       and (v_touches is null or v_touches ?| (case v_champ.champ
             when 'montant'            then array['amount', 'sale_price']
             when 'date'               then array['transaction_date']
             when 'date_acte'          then array['signature_date']
             when 'sequestre'          then array['sequestration']
             when 'prix_net_vendeur'   then array['net_seller_price']
             when 'prix_publique'      then array['sale_price']
             when 'honoraires'         then array['buyer_fees']
             when 'honoraires_entree'  then array['seller_fees']
             when 'numero_mandat'      then array['selected_mandat']
             when 'jours_validite'     then array['validity_days']
             when 'jours_retractation' then array['retraction_days']
             when 'notaire_id'         then array['buyer_notary_id']
             when 'taux_honoraires'    then array['buyer_fees_rate']
             else array['--champ-inconnu--'] end)) then$n6$, chr(13), ''),
        replace($n7$                            'champs_au_carnet', v_au_carnet,
                            'champs_touches',   v_touches);$n7$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = 'a5297281686c699b89ac2fbc61864fe4' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_modifier_affaire_optimistic porte deja l''empreinte d''avant (a5297281).';
        RETURN;
    END IF;
    IF md5(d) <> '049643b8a2042904544586f400eb8fe3' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, ni 049643b8 (posee) ni a5297281 (avant). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> 'a5297281686c699b89ac2fbc61864fe4' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte rendu a l''empreinte %s, attendu a5297281. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour$ $exec_inv$;
    total := total + 1;
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) = 'a5297281686c699b89ac2fbc61864fe4' THEN ok := ok + 1; r := r || ' | T8 OK l inverse rend a5297281';
    ELSE r := r || ' | T8 ECHEC l inverse rend a5297281 : ' || coalesce('empreinte differente', 'null'); END IF;

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
