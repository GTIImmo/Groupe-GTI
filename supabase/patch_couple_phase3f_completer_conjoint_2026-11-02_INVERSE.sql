-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PIÈCE F — RETOUR ARRIÈRE                                   02/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Remet app_edit_conjoint_optimistic dans sa définition de la pièce E (« nommé » seulement), si la version en
-- place est bien celle de la pièce F (empreinte POSÉE e5ac0baa… ; la répétition donnait 43faf014… -- même logique, lignes vides en plus), puis vérifie l'empreinte d'origine (77bcfa92…).
-- ⛔ Avant : retirer du front le bouton « Compléter le conjoint » (sinon il recevrait « pas_de_conjoint_nomme »).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
BEGIN
  IF md5(pg_get_functiondef('public.app_edit_conjoint_optimistic(text,jsonb)'::regprocedure)) <> 'e5ac0baa5169265f5a49a73024fc12c2' THEN
    RAISE EXCEPTION 'ARRET : la fonction n''est pas celle de la piece F. Rien n''est ecrit.';
  END IF;
END
$garde$;

create or replace function public.app_edit_conjoint_optimistic(target_contact_id text, edit_fields jsonb)
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

DO $controle$
BEGIN
  IF md5(pg_get_functiondef('public.app_edit_conjoint_optimistic(text,jsonb)'::regprocedure)) <> '77bcfa92e8c0acc27a1f32f3c97a82ab' THEN
    RAISE EXCEPTION 'ARRET : la definition remise n''est pas celle de la piece E. Tout est annule.';
  END IF;
END
$controle$;

COMMIT;
