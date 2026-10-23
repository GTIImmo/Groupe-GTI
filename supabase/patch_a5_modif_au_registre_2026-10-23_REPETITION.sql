-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE A5 — la modification écrit au registre ce qu'elle envoie    23/10/2026
-- ⛔ ELLE S'ANNULE TOUTE SEULE (erreur volontaire « ESSAI ANNULE -- … ») : rien ne reste, ni la
--   fonction modifiée, ni l'interrupteur, ni le registre, ni le carnet, ni les travaux.
-- Le VRAI PATCH, puis la fonction appelée COMME L'ÉCRAN, au nom de Frédéric, sur trois
-- transactions d'essai : l'offre 33026 (1000001, bac à sable 62774), le compromis 50131 (1001379)
-- et la vente 23354 (1001380) de VA6482 (essai complet du 23/10).
--   T1 A5 ÉTEINT, validité tapée          → registre inchangé (le témoin inverse : le défaut)
--   T2 offre : validité, honoraires, taux  → les trois au registre
--   T3 liste vide                          → rien      · T4 SANS liste (écran d'avant) → rien
--   T5 compromis : tout tapé, notaires affirmés, mandant désigné → acte, séquestre, net, les deux
--      honoraires, taux, fin de rétractation = date + 12, les deux notaires et leurs noms, 1 mandant
--   T6 compromis : seule la date d'acte tapée → elle seule bouge (séquestre et net restent)
--   T7 compromis : notaire tapé mais NON affirmé → le notaire ne bouge pas
--   T8 vente : net vendeur ET commission tapés → la commission bouge, PAS le net vendeur
--   T9 séquestre tapé VIDE                 → « vide ne gagne pas »
--   T10 la photo du carnet reste la valeur d'AVANT · T11 l'inverse rend 049643b8.
-- ═══════════════════════════════════════════════════════════════════════════

DO $repetition$
DECLARE
    sub text := (select id::text from public.app_user_profile where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr' and role::text = 'admin' and is_active limit 1);
    o_offre public.app_affaire_ledger%rowtype;
    o_comp  public.app_affaire_ledger%rowtype;
    o_vente public.app_affaire_ledger%rowtype;
    l public.app_affaire_ledger%rowtype;
    res jsonb;
    photo text;
    r text := '';
    ok int := 0;
    total int := 0;
BEGIN
    select * into o_offre from public.app_affaire_ledger where app_affaire_id = 1000001;
    select * into o_comp  from public.app_affaire_ledger where app_affaire_id = 1001379;
    select * into o_vente from public.app_affaire_ledger where app_affaire_id = 1001380;
    IF coalesce(o_offre.hektor_affaire_id, '') = '' OR coalesce(o_comp.hektor_affaire_id, '') = ''
       OR coalesce(o_vente.hektor_affaire_id, '') = '' OR o_offre.present_in_hektor IS FALSE
       OR o_comp.present_in_hektor IS FALSE OR o_vente.present_in_hektor IS FALSE THEN
        RAISE EXCEPTION '%', 'ARRET : une transaction d''essai n''est plus modifiable (numero Hektor ou presence) -- la repetition ne prouverait rien.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'affaire_modif_champs_touches' AND value = 'on') THEN
        RAISE EXCEPTION '%', 'ARRET : le point E est eteint -- A5 en depend, la repetition ne prouverait rien.';
    END IF;
    PERFORM set_config('request.jwt.claims', json_build_object('sub', sub, 'role', 'authenticated', 'email', 'frederic.gerphagnon@gti-immobilier.fr')::text, true);
    PERFORM set_config('request.jwt.claim.sub', sub, true);

    -- LE VRAI PATCH
    insert into public.app_setting (key, value, description, updated_at)
    values ('affaire_modif_au_registre', 'off',
            'Chantier 8 / A5 23/10/2026 : on = en MODIFICATION d''une transaction, ce qui a ete TAPE (liste champs_touches du point E) est ecrit AUSSI au registre, colonne par colonne, au clic (voir supabase/patch_a5_modif_au_registre_2026-10-23.sql). off, ou liste absente = comportement d''avant (montant et date seulement).',
            now())
    on conflict (key) do nothing;
    EXECUTE $exec_pose$ DO $pose_rep$
DECLARE
    d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  -- ─── LE CARNET, QUE LE RUN NE TOUCHE JAMAIS ───$a1$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  -- ─── A5 (23/10/2026, chantier 8) : LA MODIFICATION ECRIT AU REGISTRE CE QU'ELLE ENVOIE ───
  -- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, section 20.
  -- R1 (22/10) l'avait promis « creation + modification » : la modification n'ecrivait que le
  -- montant et la date. Interrupteur 'affaire_modif_au_registre', ET la liste du point E : seul
  -- ce qui a ete TAPE ; les notaires s'ils sont AFFIRMES, les mandants s'ils sont DESIGNES --
  -- exactement ce que le worker envoie comme intention. « Vide ne gagne pas ».
  -- ⚠ ON N'ECRIT QUE CE QUE HEKTOR RELIT au retour, ou ce qu'aucun verdict ne juge sur le
  --   registre : sinon l'ancien verdict (marquerLeCarnetRestant) comparerait la saisie A ELLE-MEME.
  --   D'ou : PAS le net vendeur d'une VENTE (Hektor n'en a pas), PAS le numero de mandat (relu
  --   la nuit seulement).
  -- ⚠ La photo du carnet, plus bas, se prend dans `a`, lu AVANT : elle reste la valeur d'avant.
  -- ⚠ Une erreur ici ne fait JAMAIS echouer le geste (WARNING), comme R1.
  if v_touches is not null
     and coalesce((select s.value from public.app_setting s
                    where s.key = 'affaire_modif_au_registre'), 'off') = 'on' then
    begin
      update public.app_affaire_ledger l set
        jours_validite = case when a.kind in ('offre') and v_touches ? 'validity_days'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'validity_days', '')), ''), l.jours_validite)
                                     else l.jours_validite end,
        date_acte = case when a.kind in ('compromis') and v_touches ? 'signature_date'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'signature_date', '')), ''), l.date_acte)
                                     else l.date_acte end,
        sequestre = case when a.kind in ('compromis') and v_touches ? 'sequestration'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'sequestration', '')), ''), l.sequestre)
                                     else l.sequestre end,
        prix_net_vendeur = case when a.kind in ('compromis') and v_touches ? 'net_seller_price'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'net_seller_price', '')), ''), l.prix_net_vendeur)
                                     else l.prix_net_vendeur end,
        honoraires_entree = case when a.kind in ('compromis', 'vente') and v_touches ? 'seller_fees'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'seller_fees', '')), ''), l.honoraires_entree)
                                     else l.honoraires_entree end,
        honoraires_sortie = case when v_touches ? 'buyer_fees'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'buyer_fees', '')), ''), l.honoraires_sortie)
                                     else l.honoraires_sortie end,
        taux_honoraires = case when v_touches ? 'buyer_fees_rate'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'buyer_fees_rate', '')), ''), l.taux_honoraires)
                                     else l.taux_honoraires end,
        date_fin_retractation = case when a.kind = 'compromis' and v_touches ? 'retraction_days'
                                      and btrim(coalesce(v_payload->>'retraction_days', '')) ~ '^\d{1,3}$'
                                      and coalesce(l.date, '') ~ '^\d{4}-\d{2}-\d{2}'
                                     then to_char(left(l.date, 10)::date
                                                  + btrim(v_payload->>'retraction_days')::int, 'YYYY-MM-DD')
                                     else l.date_fin_retractation end,
        notaire_acquereur_id = case when a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'acquereur') = 'true'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), ''), l.notaire_acquereur_id)
                                     else l.notaire_acquereur_id end,
        notaire_acquereur_nom = case when a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'acquereur') = 'true'
                                      and nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), '') is not null
                                     then nullif(btrim(coalesce(v_payload->>'buyer_notary_nom', '')), '')
                                     else l.notaire_acquereur_nom end,
        notaire_mandant_id = case when a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'mandant') = 'true'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), ''), l.notaire_mandant_id)
                                     else l.notaire_mandant_id end,
        notaire_mandant_nom = case when a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'mandant') = 'true'
                                      and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                                     then nullif(btrim(coalesce(v_payload->>'seller_notary_nom', '')), '')
                                     else l.notaire_mandant_nom end,
        mandants_json = case when a.kind in ('compromis', 'vente')
                              and jsonb_typeof(v_payload->'mandant_contact_ids') = 'array'
                              and jsonb_array_length(v_payload->'mandant_contact_ids') > 0
                             then public.app_acquereurs_json(array(
                                    select nullif(btrim(e), '')
                                      from jsonb_array_elements_text(v_payload->'mandant_contact_ids') e
                                     where nullif(btrim(e), '') is not null))
                             else l.mandants_json end
       where l.app_affaire_id = a.app_affaire_id;
    exception when others then
      raise warning 'A5 affaire_modif_au_registre : colonnes non posees pour l''affaire % (%)', a.app_affaire_id, sqlerrm;
    end;
  end if;

  -- ─── LE CARNET, QUE LE RUN NE TOUCHE JAMAIS ───$n1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE NOTICE '%', 'Deja pose : app_modifier_affaire_optimistic porte deja l''empreinte 0dac8c86. Rien n''est ecrit.';
        RETURN;
    END IF;
    IF md5(d) <> '049643b8a2042904544586f400eb8fe3' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, attendu 049643b8 (mesuree le 23/10, apres E2). Quelqu''un est passe avant : rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(ancres, 1) LOOP
        nb := (length(d) - length(replace(d, ancres[i], ''))) / length(ancres[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : l''ancre %s est trouvee %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, ancres[i], neufs[i]);
    END LOOP;
    IF md5(d) <> '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte neuf a l''empreinte %s, attendu 0dac8c86 (calcule d''avance). Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) <> '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE EXCEPTION '%', 'ARRET : apres la pose, l''empreinte n''est pas celle attendue.';
    END IF;
END
$pose_rep$ $exec_pose$;

    -- T1 ETEINT
    update public.app_setting set value = 'off' where key = 'affaire_modif_au_registre';
    res := public.app_modifier_affaire_optimistic(1000001, (jsonb_build_object('amount', '120000', 'sale_price', '128787', 'transaction_date', '2026-08-29', 'validity_days', '17', 'retraction_days', '10', 'buyer_fees', '3000', 'buyer_fees_rate', '2.5', 'selected_mandat', '18836')) || jsonb_build_object('champs_touches', '["validity_days"]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = 1000001;
    total := total + 1;
    IF l.jours_validite is not distinct from o_offre.jours_validite THEN ok := ok + 1; r := r || ' | T1 OK eteint : registre inchange';
    ELSE r := r || ' | T1 ECHEC eteint : registre inchange : ' || coalesce(l.jours_validite, 'null'); END IF;
    update public.app_affaire_ledger set montant = o_offre.montant, date = o_offre.date, jours_validite = o_offre.jours_validite, date_acte = o_offre.date_acte, sequestre = o_offre.sequestre, prix_net_vendeur = o_offre.prix_net_vendeur, honoraires_entree = o_offre.honoraires_entree, honoraires_sortie = o_offre.honoraires_sortie, taux_honoraires = o_offre.taux_honoraires, date_fin_retractation = o_offre.date_fin_retractation, notaire_acquereur_id = o_offre.notaire_acquereur_id, notaire_acquereur_nom = o_offre.notaire_acquereur_nom, notaire_mandant_id = o_offre.notaire_mandant_id, notaire_mandant_nom = o_offre.notaire_mandant_nom, mandants_json = o_offre.mandants_json where app_affaire_id = 1000001;

    update public.app_setting set value = 'on' where key = 'affaire_modif_au_registre';
    -- T2 OFFRE
    res := public.app_modifier_affaire_optimistic(1000001, (jsonb_build_object('amount', '120000', 'sale_price', '128787', 'transaction_date', '2026-08-29', 'validity_days', '17', 'retraction_days', '10', 'buyer_fees', '3000', 'buyer_fees_rate', '2.5', 'selected_mandat', '18836')) || jsonb_build_object('champs_touches', '["validity_days", "buyer_fees", "buyer_fees_rate"]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = 1000001;
    total := total + 1;
    IF l.jours_validite = '17' and l.honoraires_sortie = '3000' and l.taux_honoraires = '2.5' THEN ok := ok + 1; r := r || ' | T2 OK offre : validite, honoraires, taux';
    ELSE r := r || ' | T2 ECHEC offre : validite, honoraires, taux : ' || coalesce(concat_ws(' / ', l.jours_validite, l.honoraires_sortie, l.taux_honoraires), 'null'); END IF;
    update public.app_affaire_ledger set montant = o_offre.montant, date = o_offre.date, jours_validite = o_offre.jours_validite, date_acte = o_offre.date_acte, sequestre = o_offre.sequestre, prix_net_vendeur = o_offre.prix_net_vendeur, honoraires_entree = o_offre.honoraires_entree, honoraires_sortie = o_offre.honoraires_sortie, taux_honoraires = o_offre.taux_honoraires, date_fin_retractation = o_offre.date_fin_retractation, notaire_acquereur_id = o_offre.notaire_acquereur_id, notaire_acquereur_nom = o_offre.notaire_acquereur_nom, notaire_mandant_id = o_offre.notaire_mandant_id, notaire_mandant_nom = o_offre.notaire_mandant_nom, mandants_json = o_offre.mandants_json where app_affaire_id = 1000001;
    -- T3 LISTE VIDE
    res := public.app_modifier_affaire_optimistic(1000001, (jsonb_build_object('amount', '120000', 'sale_price', '128787', 'transaction_date', '2026-08-29', 'validity_days', '17', 'retraction_days', '10', 'buyer_fees', '3000', 'buyer_fees_rate', '2.5', 'selected_mandat', '18836')) || jsonb_build_object('champs_touches', '[]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = 1000001;
    total := total + 1;
    IF l.jours_validite is not distinct from o_offre.jours_validite and l.honoraires_sortie is not distinct from o_offre.honoraires_sortie THEN ok := ok + 1; r := r || ' | T3 OK liste vide : rien';
    ELSE r := r || ' | T3 ECHEC liste vide : rien : ' || coalesce(concat_ws(' / ', l.jours_validite, l.honoraires_sortie), 'null'); END IF;
    update public.app_affaire_ledger set montant = o_offre.montant, date = o_offre.date, jours_validite = o_offre.jours_validite, date_acte = o_offre.date_acte, sequestre = o_offre.sequestre, prix_net_vendeur = o_offre.prix_net_vendeur, honoraires_entree = o_offre.honoraires_entree, honoraires_sortie = o_offre.honoraires_sortie, taux_honoraires = o_offre.taux_honoraires, date_fin_retractation = o_offre.date_fin_retractation, notaire_acquereur_id = o_offre.notaire_acquereur_id, notaire_acquereur_nom = o_offre.notaire_acquereur_nom, notaire_mandant_id = o_offre.notaire_mandant_id, notaire_mandant_nom = o_offre.notaire_mandant_nom, mandants_json = o_offre.mandants_json where app_affaire_id = 1000001;
    -- T4 SANS LISTE
    res := public.app_modifier_affaire_optimistic(1000001, (jsonb_build_object('amount', '120000', 'sale_price', '128787', 'transaction_date', '2026-08-29', 'validity_days', '17', 'retraction_days', '10', 'buyer_fees', '3000', 'buyer_fees_rate', '2.5', 'selected_mandat', '18836')), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = 1000001;
    total := total + 1;
    IF l.jours_validite is not distinct from o_offre.jours_validite and l.taux_honoraires is not distinct from o_offre.taux_honoraires THEN ok := ok + 1; r := r || ' | T4 OK sans liste : rien';
    ELSE r := r || ' | T4 ECHEC sans liste : rien : ' || coalesce(concat_ws(' / ', l.jours_validite, l.taux_honoraires), 'null'); END IF;
    update public.app_affaire_ledger set montant = o_offre.montant, date = o_offre.date, jours_validite = o_offre.jours_validite, date_acte = o_offre.date_acte, sequestre = o_offre.sequestre, prix_net_vendeur = o_offre.prix_net_vendeur, honoraires_entree = o_offre.honoraires_entree, honoraires_sortie = o_offre.honoraires_sortie, taux_honoraires = o_offre.taux_honoraires, date_fin_retractation = o_offre.date_fin_retractation, notaire_acquereur_id = o_offre.notaire_acquereur_id, notaire_acquereur_nom = o_offre.notaire_acquereur_nom, notaire_mandant_id = o_offre.notaire_mandant_id, notaire_mandant_nom = o_offre.notaire_mandant_nom, mandants_json = o_offre.mandants_json where app_affaire_id = 1000001;

    -- T5 COMPROMIS, TOUT
    delete from public.app_affaire_champ_app where app_affaire_id = 1001379 and champ = 'date_acte';
    res := public.app_modifier_affaire_optimistic(1001379, (jsonb_build_object('amount', '120000', 'sale_price', '115000', 'transaction_date', '2026-10-23', 'signature_date', '2027-02-01', 'sequestration', '7000', 'net_seller_price', '106000', 'seller_fees', '9000', 'buyer_fees', '4000', 'buyer_fees_rate', '3.33', 'retraction_days', '12', 'selected_mandat', '18787', 'buyer_notary_id', '10064499', 'buyer_notary_nom', 'NOTAIRE ACQ ESSAI', 'seller_notary_id', '10355906', 'seller_notary_nom', 'NOTAIRE VEND ESSAI', 'notaires_affirmes', jsonb_build_object('acquereur', true, 'mandant', true), 'mandant_contact_ids', jsonb_build_array('10354641'))) || jsonb_build_object('champs_touches', '["signature_date", "sequestration", "net_seller_price", "seller_fees", "buyer_fees", "buyer_fees_rate", "retraction_days", "buyer_notary_id"]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = 1001379;
    total := total + 1;
    IF l.date_acte = '2027-02-01' and l.sequestre = '7000' and l.prix_net_vendeur = '106000' and l.honoraires_entree = '9000' and l.honoraires_sortie = '4000' and l.taux_honoraires = '3.33' and l.date_fin_retractation = '2026-11-04' and l.notaire_acquereur_id = '10064499' and l.notaire_acquereur_nom = 'NOTAIRE ACQ ESSAI' and l.notaire_mandant_id = '10355906' and l.notaire_mandant_nom = 'NOTAIRE VEND ESSAI' and jsonb_array_length(l.mandants_json) = 1 THEN ok := ok + 1; r := r || ' | T5 OK compromis : tout tape';
    ELSE r := r || ' | T5 ECHEC compromis : tout tape : ' || coalesce(concat_ws(' / ', l.date_acte, l.sequestre, l.prix_net_vendeur, l.honoraires_entree, l.honoraires_sortie, l.taux_honoraires, l.date_fin_retractation, l.notaire_acquereur_nom, l.notaire_mandant_nom, l.mandants_json::text), 'null'); END IF;
    -- T10 LA PHOTO
    select valeur_hektor_au_moment into photo from public.app_affaire_champ_app where app_affaire_id = 1001379 and champ = 'date_acte';
    total := total + 1;
    IF photo is not distinct from o_comp.date_acte THEN ok := ok + 1; r := r || ' | T10 OK la photo du carnet reste la valeur d avant';
    ELSE r := r || ' | T10 ECHEC la photo du carnet reste la valeur d avant : ' || coalesce(photo, 'null'); END IF;
    update public.app_affaire_ledger set montant = o_comp.montant, date = o_comp.date, jours_validite = o_comp.jours_validite, date_acte = o_comp.date_acte, sequestre = o_comp.sequestre, prix_net_vendeur = o_comp.prix_net_vendeur, honoraires_entree = o_comp.honoraires_entree, honoraires_sortie = o_comp.honoraires_sortie, taux_honoraires = o_comp.taux_honoraires, date_fin_retractation = o_comp.date_fin_retractation, notaire_acquereur_id = o_comp.notaire_acquereur_id, notaire_acquereur_nom = o_comp.notaire_acquereur_nom, notaire_mandant_id = o_comp.notaire_mandant_id, notaire_mandant_nom = o_comp.notaire_mandant_nom, mandants_json = o_comp.mandants_json where app_affaire_id = 1001379;
    -- T6 SEULE LA DATE D'ACTE
    res := public.app_modifier_affaire_optimistic(1001379, (jsonb_build_object('amount', '120000', 'sale_price', '115000', 'transaction_date', '2026-10-23', 'signature_date', '2027-02-01', 'sequestration', '7000', 'net_seller_price', '106000', 'seller_fees', '9000', 'buyer_fees', '4000', 'buyer_fees_rate', '3.33', 'retraction_days', '12', 'selected_mandat', '18787', 'buyer_notary_id', '10064499', 'buyer_notary_nom', 'NOTAIRE ACQ ESSAI', 'seller_notary_id', '10355906', 'seller_notary_nom', 'NOTAIRE VEND ESSAI', 'notaires_affirmes', jsonb_build_object('acquereur', true, 'mandant', true), 'mandant_contact_ids', jsonb_build_array('10354641'))) || jsonb_build_object('champs_touches', '["signature_date"]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = 1001379;
    total := total + 1;
    IF l.date_acte = '2027-02-01' and l.sequestre is not distinct from o_comp.sequestre and l.prix_net_vendeur is not distinct from o_comp.prix_net_vendeur THEN ok := ok + 1; r := r || ' | T6 OK compromis : la date d acte seule';
    ELSE r := r || ' | T6 ECHEC compromis : la date d acte seule : ' || coalesce(concat_ws(' / ', l.date_acte, l.sequestre, l.prix_net_vendeur), 'null'); END IF;
    update public.app_affaire_ledger set montant = o_comp.montant, date = o_comp.date, jours_validite = o_comp.jours_validite, date_acte = o_comp.date_acte, sequestre = o_comp.sequestre, prix_net_vendeur = o_comp.prix_net_vendeur, honoraires_entree = o_comp.honoraires_entree, honoraires_sortie = o_comp.honoraires_sortie, taux_honoraires = o_comp.taux_honoraires, date_fin_retractation = o_comp.date_fin_retractation, notaire_acquereur_id = o_comp.notaire_acquereur_id, notaire_acquereur_nom = o_comp.notaire_acquereur_nom, notaire_mandant_id = o_comp.notaire_mandant_id, notaire_mandant_nom = o_comp.notaire_mandant_nom, mandants_json = o_comp.mandants_json where app_affaire_id = 1001379;
    -- T7 NOTAIRE NON AFFIRME
    res := public.app_modifier_affaire_optimistic(1001379, (jsonb_build_object('amount', '120000', 'sale_price', '115000', 'transaction_date', '2026-10-23', 'signature_date', '2027-02-01', 'sequestration', '7000', 'net_seller_price', '106000', 'seller_fees', '9000', 'buyer_fees', '4000', 'buyer_fees_rate', '3.33', 'retraction_days', '12', 'selected_mandat', '18787', 'buyer_notary_id', '10064499', 'buyer_notary_nom', 'NOTAIRE ACQ ESSAI', 'seller_notary_id', '10355906', 'seller_notary_nom', 'NOTAIRE VEND ESSAI', 'notaires_affirmes', jsonb_build_object('acquereur', true, 'mandant', true), 'mandant_contact_ids', jsonb_build_array('10354641')) - 'notaires_affirmes' || jsonb_build_object('buyer_notary_id', '999999')) || jsonb_build_object('champs_touches', '["buyer_notary_id"]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = 1001379;
    total := total + 1;
    IF l.notaire_acquereur_id is not distinct from o_comp.notaire_acquereur_id THEN ok := ok + 1; r := r || ' | T7 OK compromis : notaire non affirme, inchange';
    ELSE r := r || ' | T7 ECHEC compromis : notaire non affirme, inchange : ' || coalesce(l.notaire_acquereur_id, 'null'); END IF;
    update public.app_affaire_ledger set montant = o_comp.montant, date = o_comp.date, jours_validite = o_comp.jours_validite, date_acte = o_comp.date_acte, sequestre = o_comp.sequestre, prix_net_vendeur = o_comp.prix_net_vendeur, honoraires_entree = o_comp.honoraires_entree, honoraires_sortie = o_comp.honoraires_sortie, taux_honoraires = o_comp.taux_honoraires, date_fin_retractation = o_comp.date_fin_retractation, notaire_acquereur_id = o_comp.notaire_acquereur_id, notaire_acquereur_nom = o_comp.notaire_acquereur_nom, notaire_mandant_id = o_comp.notaire_mandant_id, notaire_mandant_nom = o_comp.notaire_mandant_nom, mandants_json = o_comp.mandants_json where app_affaire_id = 1001379;
    -- T9 VIDE NE GAGNE PAS
    res := public.app_modifier_affaire_optimistic(1001379, (jsonb_build_object('amount', '120000', 'sale_price', '115000', 'transaction_date', '2026-10-23', 'signature_date', '2027-02-01', 'sequestration', '7000', 'net_seller_price', '106000', 'seller_fees', '9000', 'buyer_fees', '4000', 'buyer_fees_rate', '3.33', 'retraction_days', '12', 'selected_mandat', '18787', 'buyer_notary_id', '10064499', 'buyer_notary_nom', 'NOTAIRE ACQ ESSAI', 'seller_notary_id', '10355906', 'seller_notary_nom', 'NOTAIRE VEND ESSAI', 'notaires_affirmes', jsonb_build_object('acquereur', true, 'mandant', true), 'mandant_contact_ids', jsonb_build_array('10354641')) || jsonb_build_object('sequestration', '')) || jsonb_build_object('champs_touches', '["sequestration"]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = 1001379;
    total := total + 1;
    IF l.sequestre is not distinct from o_comp.sequestre THEN ok := ok + 1; r := r || ' | T9 OK sequestre vide : inchange';
    ELSE r := r || ' | T9 ECHEC sequestre vide : inchange : ' || coalesce(l.sequestre, 'null'); END IF;
    update public.app_affaire_ledger set montant = o_comp.montant, date = o_comp.date, jours_validite = o_comp.jours_validite, date_acte = o_comp.date_acte, sequestre = o_comp.sequestre, prix_net_vendeur = o_comp.prix_net_vendeur, honoraires_entree = o_comp.honoraires_entree, honoraires_sortie = o_comp.honoraires_sortie, taux_honoraires = o_comp.taux_honoraires, date_fin_retractation = o_comp.date_fin_retractation, notaire_acquereur_id = o_comp.notaire_acquereur_id, notaire_acquereur_nom = o_comp.notaire_acquereur_nom, notaire_mandant_id = o_comp.notaire_mandant_id, notaire_mandant_nom = o_comp.notaire_mandant_nom, mandants_json = o_comp.mandants_json where app_affaire_id = 1001379;

    -- T8 VENTE
    res := public.app_modifier_affaire_optimistic(1001380, (jsonb_build_object('amount', '120000', 'sale_price', '120000', 'transaction_date', '2026-10-23', 'net_seller_price', '99999', 'seller_fees', '7777', 'selected_mandat', '18787')) || jsonb_build_object('champs_touches', '["net_seller_price", "seller_fees"]'::jsonb), 0);
    select * into l from public.app_affaire_ledger where app_affaire_id = 1001380;
    total := total + 1;
    IF l.honoraires_entree = '7777' and l.prix_net_vendeur is not distinct from o_vente.prix_net_vendeur THEN ok := ok + 1; r := r || ' | T8 OK vente : la commission oui, le net vendeur NON';
    ELSE r := r || ' | T8 ECHEC vente : la commission oui, le net vendeur NON : ' || coalesce(concat_ws(' / ', l.honoraires_entree, l.prix_net_vendeur), 'null'); END IF;
    update public.app_affaire_ledger set montant = o_vente.montant, date = o_vente.date, jours_validite = o_vente.jours_validite, date_acte = o_vente.date_acte, sequestre = o_vente.sequestre, prix_net_vendeur = o_vente.prix_net_vendeur, honoraires_entree = o_vente.honoraires_entree, honoraires_sortie = o_vente.honoraires_sortie, taux_honoraires = o_vente.taux_honoraires, date_fin_retractation = o_vente.date_fin_retractation, notaire_acquereur_id = o_vente.notaire_acquereur_id, notaire_acquereur_nom = o_vente.notaire_acquereur_nom, notaire_mandant_id = o_vente.notaire_mandant_id, notaire_mandant_nom = o_vente.notaire_mandant_nom, mandants_json = o_vente.mandants_json where app_affaire_id = 1001380;

    -- T11 L'INVERSE
    EXECUTE $exec_inv$ DO $retour$
DECLARE
    d text := replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '');
    ancres text[] := array[
        replace($a1$  -- ─── LE CARNET, QUE LE RUN NE TOUCHE JAMAIS ───$a1$, chr(13), '')];
    neufs text[] := array[
        replace($n1$  -- ─── A5 (23/10/2026, chantier 8) : LA MODIFICATION ECRIT AU REGISTRE CE QU'ELLE ENVOIE ───
  -- Note : notice/ARCHITECTURE_REGISTRE_TRANSACTIONS_CHEZ_NOUS_2026-10-22.md, section 20.
  -- R1 (22/10) l'avait promis « creation + modification » : la modification n'ecrivait que le
  -- montant et la date. Interrupteur 'affaire_modif_au_registre', ET la liste du point E : seul
  -- ce qui a ete TAPE ; les notaires s'ils sont AFFIRMES, les mandants s'ils sont DESIGNES --
  -- exactement ce que le worker envoie comme intention. « Vide ne gagne pas ».
  -- ⚠ ON N'ECRIT QUE CE QUE HEKTOR RELIT au retour, ou ce qu'aucun verdict ne juge sur le
  --   registre : sinon l'ancien verdict (marquerLeCarnetRestant) comparerait la saisie A ELLE-MEME.
  --   D'ou : PAS le net vendeur d'une VENTE (Hektor n'en a pas), PAS le numero de mandat (relu
  --   la nuit seulement).
  -- ⚠ La photo du carnet, plus bas, se prend dans `a`, lu AVANT : elle reste la valeur d'avant.
  -- ⚠ Une erreur ici ne fait JAMAIS echouer le geste (WARNING), comme R1.
  if v_touches is not null
     and coalesce((select s.value from public.app_setting s
                    where s.key = 'affaire_modif_au_registre'), 'off') = 'on' then
    begin
      update public.app_affaire_ledger l set
        jours_validite = case when a.kind in ('offre') and v_touches ? 'validity_days'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'validity_days', '')), ''), l.jours_validite)
                                     else l.jours_validite end,
        date_acte = case when a.kind in ('compromis') and v_touches ? 'signature_date'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'signature_date', '')), ''), l.date_acte)
                                     else l.date_acte end,
        sequestre = case when a.kind in ('compromis') and v_touches ? 'sequestration'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'sequestration', '')), ''), l.sequestre)
                                     else l.sequestre end,
        prix_net_vendeur = case when a.kind in ('compromis') and v_touches ? 'net_seller_price'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'net_seller_price', '')), ''), l.prix_net_vendeur)
                                     else l.prix_net_vendeur end,
        honoraires_entree = case when a.kind in ('compromis', 'vente') and v_touches ? 'seller_fees'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'seller_fees', '')), ''), l.honoraires_entree)
                                     else l.honoraires_entree end,
        honoraires_sortie = case when v_touches ? 'buyer_fees'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'buyer_fees', '')), ''), l.honoraires_sortie)
                                     else l.honoraires_sortie end,
        taux_honoraires = case when v_touches ? 'buyer_fees_rate'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'buyer_fees_rate', '')), ''), l.taux_honoraires)
                                     else l.taux_honoraires end,
        date_fin_retractation = case when a.kind = 'compromis' and v_touches ? 'retraction_days'
                                      and btrim(coalesce(v_payload->>'retraction_days', '')) ~ '^\d{1,3}$'
                                      and coalesce(l.date, '') ~ '^\d{4}-\d{2}-\d{2}'
                                     then to_char(left(l.date, 10)::date
                                                  + btrim(v_payload->>'retraction_days')::int, 'YYYY-MM-DD')
                                     else l.date_fin_retractation end,
        notaire_acquereur_id = case when a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'acquereur') = 'true'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), ''), l.notaire_acquereur_id)
                                     else l.notaire_acquereur_id end,
        notaire_acquereur_nom = case when a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'acquereur') = 'true'
                                      and nullif(btrim(coalesce(v_payload->>'buyer_notary_id', '')), '') is not null
                                     then nullif(btrim(coalesce(v_payload->>'buyer_notary_nom', '')), '')
                                     else l.notaire_acquereur_nom end,
        notaire_mandant_id = case when a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'mandant') = 'true'
                                     then coalesce(nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), ''), l.notaire_mandant_id)
                                     else l.notaire_mandant_id end,
        notaire_mandant_nom = case when a.kind in ('compromis', 'vente') and (v_payload->'notaires_affirmes'->>'mandant') = 'true'
                                      and nullif(btrim(coalesce(v_payload->>'seller_notary_id', '')), '') is not null
                                     then nullif(btrim(coalesce(v_payload->>'seller_notary_nom', '')), '')
                                     else l.notaire_mandant_nom end,
        mandants_json = case when a.kind in ('compromis', 'vente')
                              and jsonb_typeof(v_payload->'mandant_contact_ids') = 'array'
                              and jsonb_array_length(v_payload->'mandant_contact_ids') > 0
                             then public.app_acquereurs_json(array(
                                    select nullif(btrim(e), '')
                                      from jsonb_array_elements_text(v_payload->'mandant_contact_ids') e
                                     where nullif(btrim(e), '') is not null))
                             else l.mandants_json end
       where l.app_affaire_id = a.app_affaire_id;
    exception when others then
      raise warning 'A5 affaire_modif_au_registre : colonnes non posees pour l''affaire % (%)', a.app_affaire_id, sqlerrm;
    end;
  end if;

  -- ─── LE CARNET, QUE LE RUN NE TOUCHE JAMAIS ───$n1$, chr(13), '')];
    i int;
    nb int;
BEGIN
    IF md5(d) = '049643b8a2042904544586f400eb8fe3' THEN
        RAISE NOTICE '%', 'Rien a retirer : app_modifier_affaire_optimistic porte deja l''empreinte d''avant (049643b8).';
        RETURN;
    END IF;
    IF md5(d) <> '0dac8c866a73517032bf23a9bd307b71' THEN
        RAISE EXCEPTION '%', format('ARRET : app_modifier_affaire_optimistic a l''empreinte %s, ni 0dac8c86 (posee) ni 049643b8 (avant). Rien n''est ecrit.', md5(d));
    END IF;
    FOR i IN 1 .. array_length(neufs, 1) LOOP
        nb := (length(d) - length(replace(d, neufs[i], ''))) / length(neufs[i]);
        IF nb <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : le texte neuf %s est trouve %s fois (attendu 1). Rien n''est ecrit.', i, nb);
        END IF;
        d := replace(d, neufs[i], ancres[i]);
    END LOOP;
    IF md5(d) <> '049643b8a2042904544586f400eb8fe3' THEN
        RAISE EXCEPTION '%', format('ARRET : le texte rendu a l''empreinte %s, attendu 049643b8. Rien n''est ecrit.', md5(d));
    END IF;
    EXECUTE d;
END
$retour$ $exec_inv$;
    total := total + 1;
    IF md5(replace(pg_get_functiondef('public.app_modifier_affaire_optimistic(bigint,jsonb,integer)'::regprocedure), chr(13), '')) = '049643b8a2042904544586f400eb8fe3' THEN ok := ok + 1; r := r || ' | T11 OK l inverse rend 049643b8';
    ELSE r := r || ' | T11 ECHEC l inverse rend 049643b8 : ' || coalesce('empreinte differente', 'null'); END IF;

    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s sur %s%s', ok, total, r);
END
$repetition$;
