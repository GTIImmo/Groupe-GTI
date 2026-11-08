-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — patch_annonce_un_nom_par_case_2026-11-08.sql
-- ═══════════════════════════════════════════════════════════════════════════
-- Remet app_edit_annonce_optimistic EXACTEMENT telle que lue le 08/11 (empreinte 5eb2c1a46bf77dfcb2327d993fafc5c1).
-- GARDE : ne touche à rien si la fonction ne porte pas la marque du patch (« UN nom par case »).
-- Les attentes déjà écrites sous les noms Hektor restent justes : le worker et la base lisent les deux familles.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
BEGIN
  IF pg_get_functiondef('public.app_edit_annonce_optimistic(bigint,jsonb,integer)'::regprocedure) NOT LIKE '%UN nom par case%' THEN
    RAISE EXCEPTION 'ARRET : le patch du 08/11 n''est pas en place. Rien n''est ecrit.';
  END IF;
END
$garde$;

CREATE OR REPLACE FUNCTION public.app_edit_annonce_optimistic(target_dossier_id bigint, edit_fields jsonb, debounce_seconds integer DEFAULT 600)
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
begin
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode='22023'; end if;
  if not public.app_console_can_request_job('update_hektor_annonce_fields', target_dossier_id, d.hektor_annonce_id::text) then
    raise exception 'forbidden_update_annonce' using errcode='42501'; end if;
  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;

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
         coalesce((coalesce(detail_payload_json,'{}')::jsonb)->'app_optimistic_overlay','{}'::jsonb) || edit_fields
       )
  )::text
  where app_dossier_id = target_dossier_id;

  if v_scoring then perform public.app_refresh_rapprochements_for_dossier(target_dossier_id); end if;

  insert into app_annonce_pending(app_dossier_id, hektor_annonce_id, base_snapshot, push_fields, push_after, source, dirty_by)
  values (target_dossier_id, d.hektor_annonce_id::text, v_base, edit_fields,
          now() + make_interval(secs => greatest(debounce_seconds,30)), 'nego_app', auth.uid()::text)
  on conflict (app_dossier_id) do update set
    push_fields = (coalesce(app_annonce_pending.push_fields,'{}'::jsonb) || excluded.push_fields),
    push_after  = now() + make_interval(secs => greatest(debounce_seconds,30)),
    push_job_id = null, conflict = false, push_attempts = 0,
    partial = false, skipped_fields = null, updated_at = now();

  return jsonb_build_object('ok', true, 'app_dossier_id', target_dossier_id,
                            'fields_count', (select count(*) from jsonb_object_keys(edit_fields)),
                            'recomputed', v_scoring);
end $function$;

DO $verif$
BEGIN
  IF md5(pg_get_functiondef('public.app_edit_annonce_optimistic(bigint,jsonb,integer)'::regprocedure)) <> '5eb2c1a46bf77dfcb2327d993fafc5c1' THEN
    RAISE EXCEPTION 'ARRET : la definition remise ne porte pas l''empreinte du 08/11. Annule.';
  END IF;
END
$verif$;

COMMIT;
