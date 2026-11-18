-- ═══════════════════════════════════════════════════════════════════════════
-- GED · LOT G — RÉPÉTITION (rien ne reste)                                  18/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Joue le PATCH dans une transaction, sous l'identité d'un ADMIN, sur un VRAI couple « nommé » (principale 10335289,
-- conjoint 10335292, sans date de naissance) et deux témoins, mesure, rejoue l'INVERSE et vérifie l'empreinte d'origine,
-- puis LÈVE « ESSAI ANNULE » : tout est annulé (fonction comprise, fiches comprises).
-- Attendu : 01 ok · 02 conjoint=ok (date ET lieu sur 10335292) · 03 principale=ok (sa fiche n'a pas bougé)
--           · 04 vide=ok(naissance_sans_conjoint_nomme) · 05 seule=ok(pas_de_conjoint_nomme) · 06 anon=ok
--           · 07 avant=ok (l'ancien envoi -- prénom seul -- marche toujours) · 08 inverse=ok (empreinte e5ac0baa…)
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

CREATE TEMP TABLE _rep(t text) ON COMMIT DROP;
INSERT INTO _rep VALUES ('');

-- ── LE PATCH (corps, tel que dans le fichier) ──
CREATE OR REPLACE FUNCTION public.app_edit_conjoint_optimistic(target_contact_id text, edit_fields jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  c app_contact_current%rowtype;
  v_etat text;
  v_conjoint text;
  v_resume jsonb;
  v_fiche_ecrite boolean;
begin
  select * into c from app_contact_current where hektor_contact_id = target_contact_id;
  if not found then raise exception 'contact_not_found' using errcode='22023'; end if;
  if not public.app_console_can_request_contact_job('update_hektor_contact', target_contact_id, c.negociateur_email) then
    raise exception 'forbidden_update_contact' using errcode='42501'; end if;
  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;

  v_etat := coalesce(c.couple_json->>'etat', '');
  if v_etat not in ('nomme', 'vide') then
    return jsonb_build_object('ok', false, 'raison', 'pas_de_conjoint_nomme');
  end if;
  v_conjoint := nullif(trim(c.couple_json->'conjoint'->>'id'), '');
  if v_conjoint is null or v_conjoint = target_contact_id then
    return jsonb_build_object('ok', false, 'raison', 'conjoint_inconnu');
  end if;
  -- GED lot G (18/11/2026) : une naissance seule ne nomme pas un conjoint -- sur une case VIDE, rien
  if v_etat = 'vide' and (edit_fields ? 'spouse_birth_date' or edit_fields ? 'spouse_birth_place')
     and not (edit_fields ? 'spouse_last_name' or edit_fields ? 'spouse_first_name') then
    return jsonb_build_object('ok', false, 'raison', 'naissance_sans_conjoint_nomme');
  end if;

  update app_contact_current set
    nom           = case when edit_fields ? 'spouse_last_name'  then edit_fields->>'spouse_last_name'  else nom end,
    prenom        = case when edit_fields ? 'spouse_first_name' then edit_fields->>'spouse_first_name' else prenom end,
    email         = case when edit_fields ? 'spouse_email'      then edit_fields->>'spouse_email'      else email end,
    phone_primary = case when edit_fields ? 'spouse_phone'      then edit_fields->>'spouse_phone'      else phone_primary end,
    birth_date    = case when edit_fields ? 'spouse_birth_date'  then edit_fields->>'spouse_birth_date'  else birth_date end,
    birth_place   = case when edit_fields ? 'spouse_birth_place' then edit_fields->>'spouse_birth_place' else birth_place end
  where hektor_contact_id = v_conjoint
    and hektor_couple_contact_id = target_contact_id;
  v_fiche_ecrite := found;
  if not v_fiche_ecrite and v_etat = 'nomme' then
    return jsonb_build_object('ok', false, 'raison', 'conjoint_absent', 'conjoint', v_conjoint);
  end if;

  v_resume := coalesce(c.couple_json->'conjoint', '{}'::jsonb);
  if edit_fields ? 'spouse_last_name'  then v_resume := v_resume || jsonb_build_object('nom', edit_fields->>'spouse_last_name'); end if;
  if edit_fields ? 'spouse_first_name' then v_resume := v_resume || jsonb_build_object('prenom', edit_fields->>'spouse_first_name'); end if;
  if edit_fields ? 'spouse_email'      then v_resume := v_resume || jsonb_build_object('email', edit_fields->>'spouse_email'); end if;
  if edit_fields ? 'spouse_phone'      then v_resume := v_resume || jsonb_build_object('telephone', edit_fields->>'spouse_phone'); end if;
  update app_contact_current
     set couple_json = jsonb_set(jsonb_set(couple_json, '{conjoint}', v_resume), '{etat}', '"nomme"'::jsonb)
   where hektor_contact_id = target_contact_id;

  return jsonb_build_object('ok', true, 'conjoint', v_conjoint, 'complete', v_etat = 'vide', 'fiche_conjoint_ecrite', v_fiche_ecrite);
end
$function$;

DO $appel$
DECLARE r jsonb; r_vide jsonb; r_seule jsonb; r_avant jsonb; avant text; apres text;
BEGIN
  select md5(row(nom, prenom, email, phone_primary, birth_date, birth_place)::text) into avant from app_contact_current where hektor_contact_id = '10335289';
  perform set_config('request.jwt.claims',
    json_build_object('sub', (select id from auth.users where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr'), 'role', 'authenticated')::text, true);
  perform set_config('role', 'authenticated', true);
  r := public.app_edit_conjoint_optimistic('10335289', '{"spouse_birth_date": "1982-07-14", "spouse_birth_place": "Saint-Etienne"}'::jsonb);
  r_vide := public.app_edit_conjoint_optimistic('10070635', '{"spouse_birth_date": "1982-07-14"}'::jsonb);
  r_seule := public.app_edit_conjoint_optimistic((select hektor_contact_id from app_contact_current where nature_fiche = 'personne_seule' and archive is not true limit 1), '{"spouse_birth_date": "1982-07-14"}'::jsonb);
  r_avant := public.app_edit_conjoint_optimistic('10335289', '{"spouse_first_name": "RepetitionG"}'::jsonb);
  perform set_config('role', 'postgres', true);
  select md5(row(nom, prenom, email, phone_primary, birth_date, birth_place)::text) into apres from app_contact_current where hektor_contact_id = '10335289';
  update _rep set t =
       ' | 01 ' || case when coalesce((r->>'ok')::boolean, false) and (r->>'fiche_conjoint_ecrite')::boolean then 'ok' else 'FAUX:' || r::text end
    || ' | 02 conjoint=' || coalesce((select case when birth_date = '1982-07-14' and birth_place = 'Saint-Etienne' then 'ok' else 'FAUX:' || coalesce(birth_date, '-') || '/' || coalesce(birth_place, '-') end
                                       from app_contact_current where hektor_contact_id = '10335292'), 'ABSENT')
    || ' | 03 principale=' || case when avant = apres then 'ok' else 'FAUX' end
    || ' | 04 vide=' || case when coalesce((r_vide->>'ok')::boolean, true) = false and r_vide->>'raison' = 'naissance_sans_conjoint_nomme' then 'ok(' || (r_vide->>'raison') || ')' else 'FAUX:' || r_vide::text end
    || ' | 05 seule=' || case when coalesce((r_seule->>'ok')::boolean, true) = false then 'ok(' || (r_seule->>'raison') || ')' else 'FAUX:' || r_seule::text end
    || ' | 06 anon=' || case when has_function_privilege('anon', 'public.app_edit_conjoint_optimistic(text,jsonb)', 'EXECUTE') then 'FAUX' else 'ok' end
    || ' | 07 avant=' || case when coalesce((r_avant->>'ok')::boolean, false) and (select prenom from app_contact_current where hektor_contact_id = '10335292') = 'RepetitionG' then 'ok' else 'FAUX:' || r_avant::text end;
END
$appel$;

-- ── L'INVERSE (corps, tel que dans le fichier) : l'empreinte d'origine doit revenir ──
CREATE OR REPLACE FUNCTION public.app_edit_conjoint_optimistic(target_contact_id text, edit_fields jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  c app_contact_current%rowtype;
  v_etat text;
  v_conjoint text;
  v_resume jsonb;
  v_fiche_ecrite boolean;
begin
  select * into c from app_contact_current where hektor_contact_id = target_contact_id;
  if not found then raise exception 'contact_not_found' using errcode='22023'; end if;
  if not public.app_console_can_request_contact_job('update_hektor_contact', target_contact_id, c.negociateur_email) then
    raise exception 'forbidden_update_contact' using errcode='42501'; end if;
  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;

  v_etat := coalesce(c.couple_json->>'etat', '');
  if v_etat not in ('nomme', 'vide') then
    return jsonb_build_object('ok', false, 'raison', 'pas_de_conjoint_nomme');
  end if;
  v_conjoint := nullif(trim(c.couple_json->'conjoint'->>'id'), '');
  if v_conjoint is null or v_conjoint = target_contact_id then
    return jsonb_build_object('ok', false, 'raison', 'conjoint_inconnu');
  end if;

  update app_contact_current set
    nom           = case when edit_fields ? 'spouse_last_name'  then edit_fields->>'spouse_last_name'  else nom end,
    prenom        = case when edit_fields ? 'spouse_first_name' then edit_fields->>'spouse_first_name' else prenom end,
    email         = case when edit_fields ? 'spouse_email'      then edit_fields->>'spouse_email'      else email end,
    phone_primary = case when edit_fields ? 'spouse_phone'      then edit_fields->>'spouse_phone'      else phone_primary end
  where hektor_contact_id = v_conjoint
    and hektor_couple_contact_id = target_contact_id;
  v_fiche_ecrite := found;
  if not v_fiche_ecrite and v_etat = 'nomme' then
    return jsonb_build_object('ok', false, 'raison', 'conjoint_absent', 'conjoint', v_conjoint);
  end if;

  v_resume := coalesce(c.couple_json->'conjoint', '{}'::jsonb);
  if edit_fields ? 'spouse_last_name'  then v_resume := v_resume || jsonb_build_object('nom', edit_fields->>'spouse_last_name'); end if;
  if edit_fields ? 'spouse_first_name' then v_resume := v_resume || jsonb_build_object('prenom', edit_fields->>'spouse_first_name'); end if;
  if edit_fields ? 'spouse_email'      then v_resume := v_resume || jsonb_build_object('email', edit_fields->>'spouse_email'); end if;
  if edit_fields ? 'spouse_phone'      then v_resume := v_resume || jsonb_build_object('telephone', edit_fields->>'spouse_phone'); end if;
  update app_contact_current
     set couple_json = jsonb_set(jsonb_set(couple_json, '{conjoint}', v_resume), '{etat}', '"nomme"'::jsonb)
   where hektor_contact_id = target_contact_id;

  return jsonb_build_object('ok', true, 'conjoint', v_conjoint, 'complete', v_etat = 'vide', 'fiche_conjoint_ecrite', v_fiche_ecrite);
end
$function$;

DO $essai$
DECLARE v text; e text;
BEGIN
  SELECT md5(pg_get_functiondef('public.app_edit_conjoint_optimistic(text,jsonb)'::regprocedure)) INTO e;
  select _rep.t || ' | 08 inverse=' || case when e = 'e5ac0baa5169265f5a49a73024fc12c2' then 'ok' else 'FAUX:' || e end into v from _rep;
  RAISE EXCEPTION 'ESSAI ANNULE --%', v;
END
$essai$;

ROLLBACK;
