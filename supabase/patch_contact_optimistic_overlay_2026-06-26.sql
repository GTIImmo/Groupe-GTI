-- =====================================================================
-- CONTACT — affichage instantané étendu (équivalent du calque optimiste annonce,
-- version « modèle plat »). 2026-06-26.
-- app_edit_contact_optimistic écrivait 8 colonnes ; il en écrit désormais 12 :
-- + adresse, birth_date, birth_place, marital_status. Comme le contact est plat
-- (le front lit les colonnes de app_contact_current), écrire la colonne EST
-- l'affichage instantané -> pas besoin d'overlay séparé.
--
-- SEULS changements vs patch_contact_optimistic_2026-06-22 : col_map (+4) et le
-- bloc UPDATE (+4 colonnes). Garde-fou date_maj / pending / sweep INCHANGÉS.
-- =====================================================================

create or replace function public.app_edit_contact_optimistic(
  target_contact_id text, edit_fields jsonb, debounce_seconds integer default 600)
 returns jsonb language plpgsql security definer set search_path to 'public'
as $function$
declare
  c app_contact_current%rowtype;
  v_base jsonb := '{}'::jsonb;
  ef jsonb := '{}'::jsonb;
  alias_map jsonb := '{"nom":"last_name","name":"last_name","prenom":"first_name",
                       "civilite":"civility","telephone":"phone","mobile":"phone",
                       "telephone2":"phone_secondary","phoneSecondary":"phone_secondary",
                       "adresse":"address","ville":"city","code_postal":"postal_code"}'::jsonb;
  col_map jsonb := '{"last_name":"nom","first_name":"prenom","civility":"civilite",
                     "email":"email","phone":"phone_primary","phone_secondary":"phone_secondary",
                     "city":"ville","postal_code":"code_postal",
                     "address":"adresse","birth_date":"birth_date","birth_place":"birth_place","marital_status":"marital_status"}'::jsonb;
  k text;
begin
  select * into c from app_contact_current where hektor_contact_id = target_contact_id;
  if not found then raise exception 'contact_not_found' using errcode='22023'; end if;
  if not public.app_console_can_request_contact_job('update_hektor_contact', target_contact_id, c.negociateur_email) then
    raise exception 'forbidden_update_contact' using errcode='42501'; end if;
  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;

  for k in select jsonb_object_keys(edit_fields) loop
    ef := ef || jsonb_build_object(coalesce(alias_map->>k, k), edit_fields->>k);
  end loop;

  if exists (select 1 from app_contact_pending p where p.hektor_contact_id = target_contact_id) then
    select base_snapshot into v_base from app_contact_pending where hektor_contact_id = target_contact_id;
  else
    for k in select jsonb_object_keys(ef) loop
      if col_map ? k then v_base := v_base || jsonb_build_object(k, to_jsonb(c) ->> (col_map->>k)); end if;
    end loop;
    v_base := v_base || jsonb_build_object('_date_maj', c.date_maj);
  end if;

  -- écriture optimiste des colonnes mappées (12 colonnes ; date_maj NON touché)
  update app_contact_current set
    nom             = case when ef ? 'last_name'       then ef->>'last_name'       else nom end,
    prenom          = case when ef ? 'first_name'      then ef->>'first_name'      else prenom end,
    civilite        = case when ef ? 'civility'        then ef->>'civility'        else civilite end,
    email           = case when ef ? 'email'           then ef->>'email'           else email end,
    phone_primary   = case when ef ? 'phone'           then ef->>'phone'           else phone_primary end,
    phone_secondary = case when ef ? 'phone_secondary' then ef->>'phone_secondary' else phone_secondary end,
    ville           = case when ef ? 'city'            then ef->>'city'            else ville end,
    code_postal     = case when ef ? 'postal_code'     then ef->>'postal_code'     else code_postal end,
    adresse         = case when ef ? 'address'         then ef->>'address'         else adresse end,
    birth_date      = case when ef ? 'birth_date'      then ef->>'birth_date'      else birth_date end,
    birth_place     = case when ef ? 'birth_place'     then ef->>'birth_place'     else birth_place end,
    marital_status  = case when ef ? 'marital_status'  then ef->>'marital_status'  else marital_status end
  where hektor_contact_id = target_contact_id;

  insert into app_contact_pending(hektor_contact_id, base_snapshot, push_fields, push_after, source, dirty_by)
  values (target_contact_id, v_base, ef,
          now() + make_interval(secs => greatest(debounce_seconds,30)), 'nego_app', auth.uid()::text)
  on conflict (hektor_contact_id) do update set
    push_fields = (coalesce(app_contact_pending.push_fields,'{}'::jsonb) || excluded.push_fields),
    push_after  = now() + make_interval(secs => greatest(debounce_seconds,30)),
    push_job_id = null, conflict = false, push_attempts = 0, updated_at = now();

  return jsonb_build_object('ok', true, 'hektor_contact_id', target_contact_id,
                            'fields_count', (select count(*) from jsonb_object_keys(ef)));
end $function$;
