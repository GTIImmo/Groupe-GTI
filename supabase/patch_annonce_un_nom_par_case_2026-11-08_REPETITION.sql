-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — patch_annonce_un_nom_par_case_2026-11-08.sql
-- ═══════════════════════════════════════════════════════════════════════════
-- Pose la NOUVELLE fonction (dans le bloc) puis essaie les gestes, DANS UNE TRANSACTION TOUJOURS ANNULÉE : le bloc finit par une
-- erreur volontaire « RÉPÉTITION (annulée) : … » qui porte les verdicts. Rien n'est gardé (ni fonction, ni attente,
-- ni prix). Admin simulé, un bien vivant sans attente en cours. Aucun déclencheur des tables touchées n'appelle l'extérieur (vérifié).
-- Attendu : 10 OK, 0 KO.
-- ═══════════════════════════════════════════════════════════════════════════

DO $essai$
DECLARE
  v_admin uuid; v_nego uuid; v_app bigint;
  pf jsonb; ov jsonb; v_prix numeric;
  ok int := 0; ko int := 0; journal text := '';
  v_refus text;
BEGIN
  -- la nouvelle fonction est posee DANS ce bloc : une seule instruction, annulee d'un coup par l'erreur finale.
  EXECUTE $def$CREATE OR REPLACE FUNCTION public.app_edit_annonce_optimistic(target_dossier_id bigint, edit_fields jsonb, debounce_seconds integer DEFAULT 600)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  d app_dossier_current%rowtype;
  v_detail jsonb;
  v_base jsonb := '{}'::jsonb;
  v_json_set jsonb := '{}'::jsonb;
  v_scoring boolean := false;
  v_price text;
  col_map jsonb := '{"price":"prix","city":"ville","postalCode":"code_postal","mandateNumber":"numero_mandat",
                     "prix":"prix","villepublique":"ville","codepublique":"code_postal","ESTIMATION_MONTANT":"prix"}'::jsonb;
  json_map jsonb := '{"surface":"surface","roomCount":"nb_pieces","bedroomCount":"nb_chambres","landSurface":"surface_terrain_detail","latitude":"latitude_detail","longitude":"longitude_detail","garageCount":"garage_box_detail",
                      "surfappart":"surface","nbpieces":"nb_pieces","NB_CHAMBRES":"nb_chambres","surfterrain":"surface_terrain_detail","GARAGE_BOX":"garage_box_detail"}'::jsonb;
  scoring_keys text[] := array['price','postalCode','surface','roomCount','bedroomCount','landSurface','latitude','longitude','garageCount',
                               'prix','codepublique','villepublique','surfappart','nbpieces','NB_CHAMBRES','surfterrain','GARAGE_BOX','ESTIMATION_MONTANT'];
  k text;
  -- 08/11/2026 (note partenaires §28.9 ter) : UN nom par case. Ancien nom de l'app -> nom Hektor, d'apres les alias
  -- du worker (HEKTOR_CLEANFIELD_*_KEYS : chaque paire y designe la MEME case). Jamais l'adresse, la commune, le code
  -- postal, le mandat, les pieces ni latitude/longitude (identifiants de commune, chemins a part).
  v_traduction jsonb := '{"price":"prix","netSellerPrice":"PRIXNETVENDEUR","surface":"surfappart","roomCount":"nbpieces",
                        "bedroomCount":"NB_CHAMBRES","levelCount":"NB_NIVEAUX","landSurface":"surfterrain","garageCount":"GARAGE_BOX",
                        "garageSurface":"SURFACE_GARAGE","title":"titre","description":"corps","fees":"HONORAIRES",
                        "carrezSurface":"SURF_CARREZ","bathroomCount":"NB_SDB","showerRoomCount":"NB_SE","wcCount":"NB_WC",
                        "parkingInsideCount":"NB_PARK_INT","parkingOutsideCount":"NB_PARK_EXT","terraceCount":"NB_TERRASSE","constructionYear":"ANNEE_CONS",
                        "dpeValue":"dpe_cons","gesValue":"dpe_ges","kitchen":"CUISINE","exposure":"EXPOSITION",
                        "view":"vuee","interiorState":"etat_interieur","exteriorState":"etat_exterieur","garden":"JARDIN-",
                        "pool":"PISCINE-","coproLots":"copropriete_nb_lot","coproCharges":"CHARGES","coproQuotePart":"copropriete_quote_part",
                        "coproWorksFund":"montant_fonds_travaux"}'::jsonb;
  v_anciens text[];
begin
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode='22023'; end if;
  if not public.app_console_can_request_job('update_hektor_annonce_fields', target_dossier_id, d.hektor_annonce_id::text) then
    raise exception 'forbidden_update_annonce' using errcode='42501'; end if;
  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;

  -- 08/11/2026 (§28.9 ter) : les anciens noms sont TRADUITS avant tout le reste (cartes, prix, attente). Dans une meme
  -- saisie, le nom Hektor l'emporte sur son jumeau. Puis on note les anciens noms des cases touchees : on les RETIRE de
  -- l'attente et du calque a la fusion -- sinon une correction d'avant (« price ») et une d'apres (« prix ») restaient
  -- cote a cote, et le worker, qui lit l'ancien nom d'abord, renvoyait la PLUS ANCIENNE.
  edit_fields := coalesce((select jsonb_object_agg(v_traduction->>e.key, e.value)
                             from jsonb_each(edit_fields) e where v_traduction ? e.key), '{}'::jsonb)
                 || coalesce((select jsonb_object_agg(e.key, e.value)
                                from jsonb_each(edit_fields) e where not (v_traduction ? e.key)), '{}'::jsonb);
  select coalesce(array_agg(t.key), '{}'::text[]) into v_anciens
    from jsonb_each_text(v_traduction) t where edit_fields ? t.value;

  v_price := coalesce(nullif(trim(edit_fields->>'price'),''), nullif(trim(edit_fields->>'prix'),''), nullif(trim(edit_fields->>'ESTIMATION_MONTANT'),''));
  if v_price is not null and v_price !~ '^[0-9]+([.,][0-9]+)?$' then
    raise exception 'invalid_price' using errcode='22023'; end if;
-- L2-A (12/10/2026) : le PRIX reste sous demande pour un negociateur
-- (decision B1 de Frederic). Il passe par « Demande de baisse de prix ».
if v_price is not null and public.app_console_current_role() = 'commercial' then
raise exception 'prix_sur_demande' using errcode='42501'; end if;

  select detail_payload_json::jsonb into v_detail from app_dossier_detail_current where app_dossier_id = target_dossier_id;
  v_detail := coalesce(v_detail, '{}'::jsonb);

  if exists (select 1 from app_annonce_pending p where p.app_dossier_id = target_dossier_id) then
    select base_snapshot into v_base from app_annonce_pending where app_dossier_id = target_dossier_id;
  else
    for k in select jsonb_object_keys(edit_fields) loop
      if col_map ? k then
        v_base := v_base || jsonb_build_object(k, to_jsonb(d) ->> (col_map->>k));
      elsif json_map ? k then
        v_base := v_base || jsonb_build_object(k, v_detail ->> (json_map->>k));
      end if;
    end loop;
    v_base := v_base || jsonb_build_object('_date_maj', v_detail->>'date_maj');
  end if;

  for k in select jsonb_object_keys(edit_fields) loop
    if k = any(scoring_keys) then v_scoring := true; end if;
    if json_map ? k then
      v_json_set := v_json_set || jsonb_build_object(json_map->>k, edit_fields->>k);
    end if;
  end loop;

  update app_dossier_current set
    prix          = case when v_price is not null
                         then replace(replace(v_price,' ',''), ',', '.')::numeric
                         else prix end,
    ville         = coalesce(nullif(edit_fields->>'city',''), nullif(edit_fields->>'villepublique',''), ville),
    code_postal   = coalesce(nullif(edit_fields->>'postalCode',''), nullif(edit_fields->>'codepublique',''), code_postal),
    numero_mandat = coalesce(nullif(edit_fields->>'mandateNumber',''), numero_mandat)
  where app_dossier_id = target_dossier_id;

  update app_dossier_detail_current
  set detail_payload_json = (
    (coalesce(detail_payload_json,'{}')::jsonb || v_json_set)
    || jsonb_build_object(
         'app_optimistic_overlay',
         (coalesce((coalesce(detail_payload_json,'{}')::jsonb)->'app_optimistic_overlay','{}'::jsonb) - v_anciens) || edit_fields
       )
  )::text
  where app_dossier_id = target_dossier_id;

  if v_scoring then perform public.app_refresh_rapprochements_for_dossier(target_dossier_id); end if;

  insert into app_annonce_pending(app_dossier_id, hektor_annonce_id, base_snapshot, push_fields, push_after, source, dirty_by)
  values (target_dossier_id, d.hektor_annonce_id::text, v_base, edit_fields,
          now() + make_interval(secs => greatest(debounce_seconds,30)), 'nego_app', auth.uid()::text)
  on conflict (app_dossier_id) do update set
    push_fields = ((coalesce(app_annonce_pending.push_fields,'{}'::jsonb) - v_anciens) || excluded.push_fields),
    push_after  = now() + make_interval(secs => greatest(debounce_seconds,30)),
    push_job_id = null, conflict = false, push_attempts = 0,
    partial = false, skipped_fields = null, updated_at = now();

  return jsonb_build_object('ok', true, 'app_dossier_id', target_dossier_id,
                            'fields_count', (select count(*) from jsonb_object_keys(edit_fields)),
                            'recomputed', v_scoring);
end $function$
$def$;
  SELECT id INTO v_admin FROM public.app_user_profile WHERE role::text = 'admin' AND is_active LIMIT 1;
  SELECT id INTO v_nego FROM public.app_user_profile WHERE role::text = 'commercial' AND is_active LIMIT 1;
  PERFORM set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  PERFORM set_config('request.jwt.claim.sub', v_admin::text, true);
  -- un bien vivant SANS attente en cours (62774, le bac a sable habituel, n'est plus parmi les vivants le 08/11)
  SELECT d.app_dossier_id INTO v_app FROM public.app_dossier_current d
   WHERE d.hektor_annonce_id IS NOT NULL AND d.archive = '0'
     AND NOT EXISTS (SELECT 1 FROM public.app_annonce_pending p WHERE p.app_dossier_id = d.app_dossier_id)
   ORDER BY d.app_dossier_id DESC LIMIT 1;

  -- 01. un ancien onglet envoie « price » : l'attente ne porte que « prix »
  PERFORM public.app_edit_annonce_optimistic(v_app, '{"price":"111111"}'::jsonb, 600);
  SELECT push_fields INTO pf FROM public.app_annonce_pending WHERE app_dossier_id = v_app;
  IF pf->>'prix' = '111111' AND NOT pf ? 'price' THEN ok := ok + 1; journal := journal || ' 01=ok'; ELSE ko := ko + 1; journal := journal || ' 01=KO ' || coalesce(pf::text, 'null'); END IF;

  -- 02. puis la rubrique Bien envoie « prix » : la DERNIERE gagne
  PERFORM public.app_edit_annonce_optimistic(v_app, '{"prix":"222222"}'::jsonb, 600);
  SELECT push_fields INTO pf FROM public.app_annonce_pending WHERE app_dossier_id = v_app;
  IF pf->>'prix' = '222222' AND NOT pf ? 'price' THEN ok := ok + 1; journal := journal || ' 02=ok'; ELSE ko := ko + 1; journal := journal || ' 02=KO ' || coalesce(pf::text, 'null'); END IF;

  -- 03. le prix de la ligne suit la derniere
  SELECT prix INTO v_prix FROM public.app_dossier_current WHERE app_dossier_id = v_app;
  IF v_prix = 222222 THEN ok := ok + 1; journal := journal || ' 03=ok'; ELSE ko := ko + 1; journal := journal || ' 03=KO ' || coalesce(v_prix::text, 'null'); END IF;

  -- 04. une attente d'AVANT la mise en ligne (price + surface) puis une correction « prix » : l'ancien jumeau part
  UPDATE public.app_annonce_pending SET push_fields = '{"price":"333333","surface":"80"}'::jsonb WHERE app_dossier_id = v_app;

  -- 04. (suite) la correction d'apres gagne, la case non touchee reste
  PERFORM public.app_edit_annonce_optimistic(v_app, '{"prix":"444444"}'::jsonb, 600);
  SELECT push_fields INTO pf FROM public.app_annonce_pending WHERE app_dossier_id = v_app;
  IF pf->>'prix' = '444444' AND NOT pf ? 'price' AND pf->>'surface' = '80' THEN ok := ok + 1; journal := journal || ' 04=ok'; ELSE ko := ko + 1; journal := journal || ' 04=KO ' || coalesce(pf::text, 'null'); END IF;

  -- 05. dans une meme saisie, le nom Hektor l'emporte sur son jumeau
  PERFORM public.app_edit_annonce_optimistic(v_app, '{"title":"ANCIEN","titre":"HEKTOR"}'::jsonb, 600);
  SELECT push_fields INTO pf FROM public.app_annonce_pending WHERE app_dossier_id = v_app;
  IF pf->>'titre' = 'HEKTOR' AND NOT pf ? 'title' THEN ok := ok + 1; journal := journal || ' 05=ok'; ELSE ko := ko + 1; journal := journal || ' 05=KO ' || coalesce(pf::text, 'null'); END IF;

  -- 06. crayon « Honoraires » d'un ancien onglet : fees -> HONORAIRES
  PERFORM public.app_edit_annonce_optimistic(v_app, '{"fees":"9000"}'::jsonb, 600);
  SELECT push_fields INTO pf FROM public.app_annonce_pending WHERE app_dossier_id = v_app;
  IF pf->>'HONORAIRES' = '9000' AND NOT pf ? 'fees' THEN ok := ok + 1; journal := journal || ' 06=ok'; ELSE ko := ko + 1; journal := journal || ' 06=KO ' || coalesce(pf::text, 'null'); END IF;

  -- 07. jamais traduits : latitude, ville, code postal
  PERFORM public.app_edit_annonce_optimistic(v_app, '{"latitude":"45.1","city":"Firminy","postalCode":"42700"}'::jsonb, 600);
  SELECT push_fields INTO pf FROM public.app_annonce_pending WHERE app_dossier_id = v_app;
  IF pf->>'latitude' = '45.1' AND pf->>'city' = 'Firminy' AND pf->>'postalCode' = '42700' THEN ok := ok + 1; journal := journal || ' 07=ok'; ELSE ko := ko + 1; journal := journal || ' 07=KO ' || coalesce(pf::text, 'null'); END IF;

  -- 08. le calque : l'ancien jumeau en est retire, la nouvelle valeur y est sous le nom Hektor
  UPDATE public.app_dossier_detail_current
     SET detail_payload_json = (coalesce(detail_payload_json, '{}')::jsonb || jsonb_build_object('app_optimistic_overlay',
           coalesce((coalesce(detail_payload_json, '{}')::jsonb)->'app_optimistic_overlay', '{}'::jsonb) || '{"surface":"70"}'::jsonb))::text
   WHERE app_dossier_id = v_app;
  PERFORM public.app_edit_annonce_optimistic(v_app, '{"surfappart":"95"}'::jsonb, 600);
  SELECT (detail_payload_json::jsonb)->'app_optimistic_overlay' INTO ov FROM public.app_dossier_detail_current WHERE app_dossier_id = v_app;
  IF ov->>'surfappart' = '95' AND NOT ov ? 'surface' THEN ok := ok + 1; journal := journal || ' 08=ok'; ELSE ko := ko + 1; journal := journal || ' 08=KO ' || coalesce(ov::text, 'null'); END IF;

  -- 09. un negociateur ne peut toujours pas passer le prix, meme par l'ancien nom
  v_refus := 'non refuse';
  BEGIN
    PERFORM set_config('request.jwt.claims', json_build_object('sub', v_nego, 'role', 'authenticated')::text, true);
    PERFORM set_config('request.jwt.claim.sub', v_nego::text, true);
    PERFORM public.app_edit_annonce_optimistic(v_app, '{"price":"1"}'::jsonb, 600);
  EXCEPTION WHEN OTHERS THEN v_refus := SQLERRM;
  END;
  IF v_refus IN ('prix_sur_demande', 'forbidden_update_annonce') THEN ok := ok + 1; journal := journal || ' 09=ok(' || v_refus || ')'; ELSE ko := ko + 1; journal := journal || ' 09=KO ' || v_refus; END IF;

  -- 10. droits inchanges : utilisateurs oui, public non
  IF has_function_privilege('authenticated', 'public.app_edit_annonce_optimistic(bigint,jsonb,integer)', 'EXECUTE')
     AND NOT has_function_privilege('anon', 'public.app_edit_annonce_optimistic(bigint,jsonb,integer)', 'EXECUTE')
  THEN ok := ok + 1; journal := journal || ' 10=ok'; ELSE ko := ko + 1; journal := journal || ' 10=KO droits'; END IF;

  RAISE EXCEPTION 'RÉPÉTITION (annulée) : % OK, % KO --%', ok, ko, journal;
END
$essai$;
