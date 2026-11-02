-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PIÈCE F — « COMPLÉTER LE CONJOINT » : LA FONCTION ACCEPTE LA CASE VIDE   02/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A APPLIQUER avec l'accord de Frédéric, APRES la répétition. Note : synthèse couples §34.
--
-- Remplace app_edit_conjoint_optimistic (posée le 02/11, pièce E) -- GARDE : seulement si sa définition est
-- celle posée (empreinte 77bcfa92…). Ce qui change :
--   · l'état « vide » (seconde fiche VIDE que Hektor connaît comme place 2 : 994 couples actifs au 02/11) est
--     accepté en plus de « nommé » ;
--   · la fiche du conjoint est écrite SI elle est chez nous (469 sur 994) ; le résumé couple_json l'est TOUJOURS,
--     et passe à l'état « nomme » (l'onglet montre le conjoint saisi) -- la fiche arrive à la relecture ;
--   · pour « nommé », RIEN ne change (fiche absente -> refus « conjoint_absent », comme avant).
-- RETOUR ARRIÈRE : …_INVERSE.sql (remet la définition de la pièce E, vérifie son empreinte).
-- RÉPÉTITION JOUÉE le 02/11 (dans une transaction annulée, admin simulé, couple d'essai 20000031/32) :
--   01 vide_fiche=ok · 02 vide_sans_fiche=ok · 03 temoin_nomme_absent=ok · 04 anon=ok · 05 empreinte=43faf0146165f3a23635523e7e7e0ff2
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
BEGIN
  IF md5(pg_get_functiondef('public.app_edit_conjoint_optimistic(text,jsonb)'::regprocedure)) <> '77bcfa92e8c0acc27a1f32f3c97a82ab' THEN
    RAISE EXCEPTION 'ARRET : app_edit_conjoint_optimistic a change depuis sa pose. Rien n''est ecrit.';
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

revoke all on function public.app_edit_conjoint_optimistic(text, jsonb) from public, anon;
grant execute on function public.app_edit_conjoint_optimistic(text, jsonb) to authenticated, service_role;

COMMIT;

select md5(pg_get_functiondef('public.app_edit_conjoint_optimistic(text,jsonb)'::regprocedure)) as nouvelle_empreinte,
       has_function_privilege('anon', 'public.app_edit_conjoint_optimistic(text,jsonb)', 'EXECUTE') as anon_execute;
