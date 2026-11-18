-- ═══════════════════════════════════════════════════════════════════════════
-- GED · LOT G — RETOUR ARRIÈRE                                              18/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Remet app_edit_conjoint_optimistic EXACTEMENT comme avant le lot G (empreinte e5ac0baa5169265f5a49a73024fc12c2,
-- contrôlée à la fin : sinon tout est annulé). Les naissances déjà écrites restent sur les fiches (des données, pas du
-- code) ; l'écran qui enverrait encore spouse_birth_* verrait seulement ces clés ignorées chez nous.
-- ⚠ Ce retour arrière ne juge que SA part : il ne touche ni le worker ni l'écran (le commit du lot G les porte).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
DECLARE d text;
BEGIN
  SELECT pg_get_functiondef('public.app_edit_conjoint_optimistic(text,jsonb)'::regprocedure) INTO d;
  IF position('spouse_birth_date' in d) = 0 THEN
    RAISE EXCEPTION 'ARRET : la fonction en place ne porte pas le lot G. Rien n''est ecrit.';
  END IF;
END
$garde$;

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

DO $controle$
DECLARE v text;
BEGIN
  SELECT md5(pg_get_functiondef('public.app_edit_conjoint_optimistic(text,jsonb)'::regprocedure)) INTO v;
  IF v IS DISTINCT FROM 'e5ac0baa5169265f5a49a73024fc12c2' THEN
    RAISE EXCEPTION 'ARRET : la fonction remise n''a pas l''empreinte d''avant (%). Tout est annule.', v;
  END IF;
END
$controle$;

COMMIT;
