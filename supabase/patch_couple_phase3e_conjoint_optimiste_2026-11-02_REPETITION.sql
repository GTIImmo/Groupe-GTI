-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PIÈCE E — RÉPÉTITION (rien ne reste)                       02/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Joue le PATCH dans une transaction, sous l'identité d'un ADMIN (Frédéric), sur le couple d'ESSAI
-- 20000031 (Un) / 20000032 (Deux) -- fiches fictives @example.com --, mesure, puis LÈVE « ESSAI ANNULE » :
-- tout est annulé (fonction comprise).
-- JOUÉE le 02/11 : 01 cree=ok | 02 conjoint=ok | 03 resume=ok | 04 principale=ok | 05 temoin=ok(pas_de_conjoint_nomme) | 06 anon=ok
-- Attendu : 01 cree=ok · 02 conjoint=ok (prénom ET portable écrits sur 20000032) · 03 resume=ok (couple_json
--           de 20000031) · 04 principale=ok (sa fiche n'a pas bougé) · 05 temoin=ok (une fiche sans conjoint
--           nommé -> ok=false, rien écrit) · 06 anon=ok (ne peut pas l'exécuter)
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

CREATE TEMP TABLE _rep(t text) ON COMMIT DROP;
INSERT INTO _rep VALUES ('');

-- ── LE PATCH (corps) ──
create function public.app_edit_conjoint_optimistic(target_contact_id text, edit_fields jsonb)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  c app_contact_current%rowtype;
  v_conjoint text;
  v_resume jsonb;
begin
  select * into c from app_contact_current where hektor_contact_id = target_contact_id;
  if not found then raise exception 'contact_not_found' using errcode='22023'; end if;
  if not public.app_console_can_request_contact_job('update_hektor_contact', target_contact_id, c.negociateur_email) then
    raise exception 'forbidden_update_contact' using errcode='42501'; end if;
  if edit_fields is null or edit_fields = '{}'::jsonb then raise exception 'no_fields' using errcode='22023'; end if;

  if coalesce(c.couple_json->>'etat', '') <> 'nomme' then
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
  if not found then
    return jsonb_build_object('ok', false, 'raison', 'conjoint_absent', 'conjoint', v_conjoint);
  end if;

  v_resume := coalesce(c.couple_json->'conjoint', '{}'::jsonb);
  if edit_fields ? 'spouse_last_name'  then v_resume := v_resume || jsonb_build_object('nom', edit_fields->>'spouse_last_name'); end if;
  if edit_fields ? 'spouse_first_name' then v_resume := v_resume || jsonb_build_object('prenom', edit_fields->>'spouse_first_name'); end if;
  if edit_fields ? 'spouse_email'      then v_resume := v_resume || jsonb_build_object('email', edit_fields->>'spouse_email'); end if;
  if edit_fields ? 'spouse_phone'      then v_resume := v_resume || jsonb_build_object('telephone', edit_fields->>'spouse_phone'); end if;
  update app_contact_current set couple_json = jsonb_set(couple_json, '{conjoint}', v_resume)
  where hektor_contact_id = target_contact_id;

  return jsonb_build_object('ok', true, 'conjoint', v_conjoint);
end
$function$;

revoke all on function public.app_edit_conjoint_optimistic(text, jsonb) from public, anon;
grant execute on function public.app_edit_conjoint_optimistic(text, jsonb) to authenticated, service_role;

-- ── LE DÉCOR (annulé avec le reste) : le résumé « nommé » que la nuit posera sur le couple d'essai ──
update app_contact_current
   set couple_json = jsonb_build_object('etat', 'nomme', 'autres', 0, 'conjoint',
                       jsonb_build_object('id', '20000032', 'prenom', 'Deux', 'nom', 'ESSAI MODIF', 'telephone', null, 'email', 'essai.modif.deux.02112026@example.com'))
 where hektor_contact_id = '20000031';

-- ── L'APPEL, comme l'écran : un ADMIN authentifié ──
DO $appel$
DECLARE r jsonb; v_temoin jsonb; avant text; apres text;
BEGIN
  select md5(row(nom, prenom, email, phone_primary)::text) into avant from app_contact_current where hektor_contact_id = '20000031';
  perform set_config('request.jwt.claims',
    json_build_object('sub', (select id from auth.users where lower(email) = 'frederic.gerphagnon@gti-immobilier.fr'), 'role', 'authenticated')::text, true);
  perform set_config('role', 'authenticated', true);
  r := public.app_edit_conjoint_optimistic('20000031', '{"spouse_first_name": "DeuxRepetition", "spouse_phone": "0600000000"}'::jsonb);
  v_temoin := public.app_edit_conjoint_optimistic('10000045', '{"spouse_first_name": "Personne"}'::jsonb);
  perform set_config('role', 'postgres', true);
  select md5(row(nom, prenom, email, phone_primary)::text) into apres from app_contact_current where hektor_contact_id = '20000031';
  update _rep set t =
       ' | 01 cree=' || case when coalesce((r->>'ok')::boolean, false) then 'ok' else 'FAUX:' || r::text end
    || ' | 02 conjoint=' || coalesce((select case when prenom = 'DeuxRepetition' and phone_primary = '0600000000' then 'ok' else 'FAUX:' || coalesce(prenom, '-') end
                                       from app_contact_current where hektor_contact_id = '20000032'), 'ABSENT')
    || ' | 03 resume=' || coalesce((select case when couple_json->'conjoint'->>'prenom' = 'DeuxRepetition' and couple_json->'conjoint'->>'telephone' = '0600000000' then 'ok' else 'FAUX' end
                                       from app_contact_current where hektor_contact_id = '20000031'), 'ABSENT')
    || ' | 04 principale=' || case when avant = apres then 'ok' else 'FAUX' end
    || ' | 05 temoin=' || case when coalesce((v_temoin->>'ok')::boolean, true) = false then 'ok(' || (v_temoin->>'raison') || ')' else 'FAUX:' || v_temoin::text end
    || ' | 06 anon=' || case when has_function_privilege('anon', 'public.app_edit_conjoint_optimistic(text,jsonb)', 'EXECUTE') then 'FAUX' else 'ok' end;
END
$appel$;

DO $essai$
DECLARE v text;
BEGIN
  select _rep.t into v from _rep;
  RAISE EXCEPTION 'ESSAI ANNULE --%', v;
END
$essai$;

ROLLBACK;
