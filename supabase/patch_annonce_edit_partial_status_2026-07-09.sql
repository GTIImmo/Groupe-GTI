-- =====================================================================
-- TIER 2 — Fidélité de la boucle optimiste (2026-07-09)
--
-- Problème traité : une édition optimiste d'annonce peut être bloquée
-- (conflit Hektor -> job "done" quand même) ou tronquée (un champ <select>
-- non résolu est jeté en silence, le pending est effacé). Dans les deux cas
-- l'utilisateur croit sa modification enregistrée alors qu'elle ne l'est pas.
--
-- Ce patch rend ces deux états COMPTABLES et LISIBLES :
--   1. app_annonce_pending.conflict  (bool) EXISTE déjà -> conflit d'écrasement.
--   2. + app_annonce_pending.partial (bool) + skipped_fields (jsonb) NOUVEAUX
--      -> champs ignorés au push (le pending N'EST PLUS effacé, il est marqué).
--   3. Reset de partial/skipped à chaque ré-édition (miroir de conflict/push_attempts).
--   4. RPC de lecture app_annonce_edit_status(dossier) pour le front (badge).
--
-- Le worker (markAnnoncePartial) et le monitoring (3 sentinelles) lisent/écrivent
-- ces colonnes. Purement additif : aucune colonne/fonction existante supprimée.
--
-- NB : le corps de app_edit_annonce_optimistic ci-dessous est la DÉFINITION LIVE
-- exacte (alias hektor prix/villepublique/codepublique/ESTIMATION_MONTANT du
-- patch 2026-07-01). SEUL ajout = `partial=false, skipped_fields=null` dans la
-- clause ON CONFLICT, pour repartir d'une ardoise propre à la ré-édition.
-- =====================================================================

-- 1. Colonnes de suivi "édition incomplète"
alter table public.app_annonce_pending
  add column if not exists partial        boolean not null default false,
  add column if not exists skipped_fields jsonb;

comment on column public.app_annonce_pending.partial is
  'true si le dernier push worker a ignore au moins un champ (ex: select non resolu). Le pending est conserve, pas efface.';
comment on column public.app_annonce_pending.skipped_fields is
  'Liste JSON des champs ignores au dernier push [{field, reason, value, available_options?}].';

-- 2. Réédition : réinitialiser partial/skipped en plus de conflict/push_attempts.
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

  -- valeur "prix" effective : front 'price', ou alias hektor 'prix' / 'ESTIMATION_MONTANT'
  v_price := coalesce(nullif(trim(edit_fields->>'price'),''), nullif(trim(edit_fields->>'prix'),''), nullif(trim(edit_fields->>'ESTIMATION_MONTANT'),''));
  if v_price is not null and v_price !~ '^[0-9]+([.,][0-9]+)?$' then
    raise exception 'invalid_price' using errcode='22023'; end if;

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

  -- ecriture optimiste BLOB JSON : champs plats mappes (scoring) + CALQUE optimiste.
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

  -- pending : réédition -> ardoise propre (conflict/partial/skipped/push_attempts remis à zéro).
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

-- 3. RPC de lecture pour le front : état d'écriture de la dernière édition d'un dossier.
--    Renvoie {pending:false} si aucune édition en attente, sinon les drapeaux.
create or replace function public.app_annonce_edit_status(target_dossier_id bigint)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $function$
declare
  d app_dossier_current%rowtype;
  p app_annonce_pending%rowtype;
begin
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode='22023'; end if;
  if not public.app_console_can_request_job('update_hektor_annonce_fields', target_dossier_id, d.hektor_annonce_id::text) then
    raise exception 'forbidden_annonce_status' using errcode='42501'; end if;

  select * into p from app_annonce_pending where app_dossier_id = target_dossier_id;
  if not found then
    return jsonb_build_object('pending', false);
  end if;

  return jsonb_build_object(
    'pending',        true,
    'conflict',       coalesce(p.conflict, false),
    'partial',        coalesce(p.partial, false),
    'skipped_fields', coalesce(p.skipped_fields, '[]'::jsonb),
    'push_attempts',  coalesce(p.push_attempts, 0),
    'dirty_at',       p.dirty_at,
    'push_after',     p.push_after
  );
end $function$;

-- Accès : uniquement les utilisateurs connectés (jamais anon) — évite d'alimenter
-- la liste des fonctions DEFINER exécutables par anon signalée par l'advisor.
revoke execute on function public.app_annonce_edit_status(bigint) from public, anon;
grant  execute on function public.app_annonce_edit_status(bigint) to authenticated;
