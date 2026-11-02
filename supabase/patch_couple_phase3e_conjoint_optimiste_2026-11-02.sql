-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PIÈCE E — LE CONJOINT MODIFIÉ S'ÉCRIT CHEZ NOUS TOUT DE SUITE   02/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A APPLIQUER avec l'accord de Frédéric, APRES la répétition.
-- Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §28.
--
-- ADDITIF : une fonction NEUVE, app_edit_conjoint_optimistic(target_contact_id, edit_fields). Rien d'existant
-- n'est modifié. Appelée par l'écran (« Modifier la fiche » d'un couple, interrupteur contacts_couples_modif)
-- APRÈS app_edit_contact_optimistic : celle-ci garde la saisie et l'envoie à Hektor par la PREMIÈRE fiche
-- (bloc _m2) ; celle-ci écrit le conjoint CHEZ NOUS à la seconde :
--   · la fiche du conjoint (nom, prénom, e-mail, portable) -- seulement la seconde fiche NOMMÉE dont le lien
--     de couple pointe la principale (couple_json.etat = 'nomme') ;
--   · le résumé couple_json.conjoint porté par la principale.
-- Mêmes droits que la modification d'un contact (app_console_can_request_contact_job).
-- RETOUR ARRIÈRE : supabase/patch_couple_phase3e_conjoint_optimiste_2026-11-02_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
BEGIN
  IF to_regprocedure('public.app_edit_conjoint_optimistic(text,jsonb)') IS NOT NULL THEN
    RAISE EXCEPTION 'ARRET : app_edit_conjoint_optimistic existe deja. Rien n''est ecrit.';
  END IF;
END
$garde$;

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

COMMIT;

-- CONTROLE : la fonction existe, authenticated l'exécute, anon non
select
  to_regprocedure('public.app_edit_conjoint_optimistic(text,jsonb)') is not null as existe,
  has_function_privilege('authenticated', 'public.app_edit_conjoint_optimistic(text,jsonb)', 'EXECUTE') as authenticated_execute,
  has_function_privilege('anon', 'public.app_edit_conjoint_optimistic(text,jsonb)', 'EXECUTE') as anon_execute;
