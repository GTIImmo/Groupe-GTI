-- =====================================================================
-- TIER 2 — RPC générique : édition optimiste de N'IMPORTE QUEL champ annonce
-- 2026-06-20. Remplace la version prix-only. push_fields = TOUS les champs
-- édités (envoyés à Hektor). Affichage optimiste : colonnes (prix/ville/CP/
-- mandat) + patch blob JSON pour les champs scoring "plats". Recompute si un
-- champ scoring change. Les champs non mappés sont quand même PUSHÉS (affichage
-- après synchro).
-- =====================================================================

create or replace function public.app_edit_annonce_optimistic(
  target_dossier_id bigint, edit_fields jsonb, debounce_seconds integer default 600)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $function$
declare
  d app_dossier_current%rowtype;
  v_detail jsonb;
  v_base jsonb := '{}'::jsonb;
  v_json_set jsonb := '{}'::jsonb;
  v_scoring boolean := false;
  -- clé push -> colonne app_dossier_current
  col_map jsonb := '{"price":"prix","city":"ville","postalCode":"code_postal","mandateNumber":"numero_mandat"}'::jsonb;
  -- clé push -> clé JSON detail_payload_json (champs "plats")
  json_map jsonb := '{"surface":"surface","roomCount":"nb_pieces","bedroomCount":"nb_chambres","landSurface":"surface_terrain_detail","latitude":"latitude_detail","longitude":"longitude_detail","garageCount":"garage_box_detail"}'::jsonb;
  scoring_keys text[] := array['price','postalCode','surface','roomCount','bedroomCount','landSurface','latitude','longitude','garageCount'];
  k text;
begin
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode='22023'; end if;
  if not public.app_console_can_request_job('update_hektor_annonce_fields', target_dossier_id, d.hektor_annonce_id::text) then
    raise exception 'forbidden_update_annonce' using errcode='42501'; end if;
  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;
  if (edit_fields ? 'price') and coalesce(nullif(trim(edit_fields->>'price'),''),'x') !~ '^[0-9]+([.,][0-9]+)?$' then
    raise exception 'invalid_price' using errcode='22023'; end if;

  select detail_payload_json::jsonb into v_detail from app_dossier_detail_current where app_dossier_id = target_dossier_id;
  v_detail := coalesce(v_detail, '{}'::jsonb);

  -- base_snapshot : photo pré-édition (figée si un pending existe déjà)
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
    -- référence anti-écrasement : date de modif Hektor du bien au moment de l'édition
    v_base := v_base || jsonb_build_object('_date_maj', v_detail->>'date_maj');
  end if;

  -- détecter scoring + préparer le patch JSON
  for k in select jsonb_object_keys(edit_fields) loop
    if k = any(scoring_keys) then v_scoring := true; end if;
    if json_map ? k then
      v_json_set := v_json_set || jsonb_build_object(json_map->>k, edit_fields->>k);
    end if;
  end loop;

  -- écriture optimiste COLONNES (inchangé si la clé n'est pas éditée)
  update app_dossier_current set
    prix          = case when (edit_fields ? 'price') and nullif(trim(edit_fields->>'price'),'') is not null
                         then replace(replace(edit_fields->>'price',' ',''), ',', '.')::numeric
                         else prix end,
    ville         = coalesce(nullif(edit_fields->>'city',''), ville),
    code_postal   = coalesce(nullif(edit_fields->>'postalCode',''), code_postal),
    numero_mandat = coalesce(nullif(edit_fields->>'mandateNumber',''), numero_mandat)
  where app_dossier_id = target_dossier_id;

  -- écriture optimiste BLOB JSON (champs plats mappés)
  if v_json_set <> '{}'::jsonb then
    update app_dossier_detail_current
    set detail_payload_json = (coalesce(detail_payload_json,'{}')::jsonb || v_json_set)::text
    where app_dossier_id = target_dossier_id;
  end if;

  if v_scoring then perform public.app_refresh_rapprochements_for_dossier(target_dossier_id); end if;

  -- pending : push_fields = TOUS les champs édités (accumulés si ré-édition)
  insert into app_annonce_pending(app_dossier_id, hektor_annonce_id, base_snapshot, push_fields, push_after, source, dirty_by)
  values (target_dossier_id, d.hektor_annonce_id::text, v_base, edit_fields,
          now() + make_interval(secs => greatest(debounce_seconds,30)), 'nego_app', auth.uid()::text)
  on conflict (app_dossier_id) do update set
    push_fields = (coalesce(app_annonce_pending.push_fields,'{}'::jsonb) || excluded.push_fields),
    push_after  = now() + make_interval(secs => greatest(debounce_seconds,30)),
    push_job_id = null, conflict = false, push_attempts = 0, updated_at = now();

  return jsonb_build_object('ok', true, 'app_dossier_id', target_dossier_id,
                            'fields_count', (select count(*) from jsonb_object_keys(edit_fields)),
                            'recomputed', v_scoring);
end $function$;
