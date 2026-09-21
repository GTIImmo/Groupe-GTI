-- ═══════════════════════════════════════════════════════════════════════════
-- L4-b — LE CONTACT NAIT DANS L'APP                               21/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Avant : la creation posait une ligne PROVISOIRE et attendait Hektor -- 18
-- secondes quand tout va bien, indefiniment quand il ne repond pas. Pendant ce
-- temps, rien ne pouvait s'accrocher au contact : ni recherche, ni rapprochement.
--
-- Maintenant : le contact recoit son numero (plage de l'app) et ENTRE DANS LA
-- TABLE PRINCIPALE immediatement. Hektor le recevra ensuite, et son numero se
-- rangera dans la case cible.
--
-- RETOUR ARRIERE : la definition d'avant est dans le commit de ce patch.
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_create_contact_optimistic(contact_payload jsonb, job_priority integer DEFAULT 18)
 RETURNS app_console_job
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  created_job    public.app_console_job;
  target_email   text;
  target_user_id text;
  v_token        uuid := gen_random_uuid();
  v_identite     text;
begin
  -- â”€â”€ les garde-fous, repris mot pour mot de app_console_create_contact_job â”€â”€
  if coalesce(jsonb_typeof(contact_payload), '') <> 'object' then
    raise exception 'invalid_contact_payload' using errcode = '22023';
  end if;

  if nullif(trim(coalesce(contact_payload->>'last_name', contact_payload->>'nom', contact_payload->>'name', '')), '') is null then
    raise exception 'missing_contact_name' using errcode = '22023';
  end if;

  if nullif(trim(coalesce(contact_payload->>'email', contact_payload->>'phone', contact_payload->>'telephone', contact_payload->>'mobile', contact_payload->>'phone_secondary', '')), '') is null then
    raise exception 'missing_contact_reachable' using errcode = '22023';
  end if;

  target_email := nullif(trim(coalesce(
      contact_payload->>'hektor_user_email',
      contact_payload->>'negociateur_email',
      contact_payload->>'target_hektor_user_email', '')), '');
  target_user_id := nullif(trim(coalesce(
      contact_payload->>'hektor_user_id',
      contact_payload->>'hektor_id_user',
      contact_payload->>'target_hektor_user_id', '')), '');

  if target_email is null and target_user_id is null then
    raise exception 'missing_contact_hektor_context' using errcode = '22023';
  end if;

  if not public.app_console_can_request_contact_job('create_hektor_contact', null, target_email) then
    raise exception 'forbidden_create_contact' using errcode = '42501';
  end if;

  -- â”€â”€ 1. CHEZ NOUS D'ABORD : la ligne provisoire â”€â”€
  -- On n'inscrit QUE ce qu'on sait dire. Un champ absent reste vide plutot que
  -- d'etre invente -- Â« l'app gagne seulement quand elle a quelque chose a dire Â».
  -- ═══════════════════════════════════════════════════════════════════════
  -- L4-b 21/09/2026 : LE CONTACT NAIT DANS L'APP, POUR DE BON
  -- ═══════════════════════════════════════════════════════════════════════
  -- CE QUI L'EN EMPECHAIT, et le commentaire du worker le disait mot pour mot :
  -- « app_contact_current a pour cle primaire hektor_contact_id ; un contact ne
  -- dans l'app n'a pas de numero Hektor, il ne peut pas entrer dans la table
  -- principale ». Il vivait donc dans une ligne provisoire, en attendant Hektor
  -- -- 18 secondes quand tout va bien, jamais quand Hektor ne repond pas.
  --
  -- L'OPTION B DU 21/09 A LEVE CE VERROU : cette colonne n'est plus « le numero
  -- de Hektor », c'est L'IDENTITE du contact. Elle accepte donc un numero A NOUS,
  -- pris dans une plage que Hektor n'atteindra jamais (>= 10 000 000).
  --
  -- ⚠ hektor_target_id RESTE VIDE : Hektor ne connait pas encore ce contact. La
  --   porte du worker refuse d'envoyer un numero de cette plage, et la barriere
  --   fait attendre ses travaux -- jusqu'a ce que le worker rapporte le vrai
  --   numero et le range dans cette case.
  v_identite := nextval('public.app_contact_identite_seq')::text;

  insert into public.app_contact_current(
    hektor_contact_id, app_contact_id, nom, prenom, display_name, email, phone_primary,
    negociateur_email, agence_nom, archive, date_enregistrement, date_maj,
    typologies_json, source_hash, refreshed_at)
  values (
    v_identite, v_identite::bigint,
    nullif(trim(coalesce(contact_payload->>'last_name', contact_payload->>'nom', '')), ''),
    nullif(trim(coalesce(contact_payload->>'first_name', contact_payload->>'prenom', '')), ''),
    trim(coalesce(contact_payload->>'first_name', contact_payload->>'prenom', '') || ' ' ||
         coalesce(contact_payload->>'last_name', contact_payload->>'nom', '')),
    nullif(trim(coalesce(contact_payload->>'email', '')), ''),
    nullif(trim(coalesce(contact_payload->>'phone', contact_payload->>'telephone', '')), ''),
    target_email,
    nullif(trim(coalesce(contact_payload->>'target_agency_label', contact_payload->>'agence_nom', '')), ''),
    false, now()::date::text, now()::text,
    '[]'::jsonb, 'app_creation_' || v_identite, now());

  insert into public.app_contact_provisional(
    creation_token, nom, prenom, societe, email, telephone,
    negociateur_email, agence_nom, status, created_by)
  values (
    v_token,
    nullif(trim(coalesce(contact_payload->>'last_name', contact_payload->>'nom', '')), ''),
    nullif(trim(coalesce(contact_payload->>'first_name', contact_payload->>'prenom', '')), ''),
    nullif(trim(coalesce(contact_payload->>'company_name', contact_payload->>'sociale', '')), ''),
    nullif(trim(coalesce(contact_payload->>'email', '')), ''),
    nullif(trim(coalesce(contact_payload->>'phone', contact_payload->>'telephone', '')), ''),
    target_email,
    nullif(trim(coalesce(contact_payload->>'target_agency_label', contact_payload->>'agence_nom', '')), ''),
    'pending',
    auth.uid()::text);

  -- La ligne provisoire reste -- mais elle ne sert plus a AFFICHER le contact
  -- (la vraie ligne existe deja) : elle porte le jeton, seul lien entre la
  -- creation et le travail, et c'est par lui que le worker retrouve quoi
  -- completer au retour de Hektor.
  update public.app_contact_provisional
     set hektor_contact_id = v_identite
   where creation_token = v_token;

  -- â”€â”€ 2. PUIS le travail, qui EMPORTE le jeton â”€â”€
  -- C'est lui qui permettra au worker de retrouver la ligne au retour.
  insert into public.app_console_job (
      job_type, app_dossier_id, hektor_annonce_id, payload_json,
      status, priority, requested_by, requested_at)
  values (
      'create_hektor_contact', null, null,
      contact_payload || jsonb_build_object(
          'hektor_user_email',        target_email,
          'target_hektor_user_email', target_email,
          'hektor_user_id',           target_user_id,
          'target_hektor_user_id',    target_user_id,
          'creation_token',           v_token,
          -- L4-b : le worker s'en sert pour ranger le numero de Hektor dans la
          -- case cible de CETTE ligne, sans jamais toucher a son identite.
          'app_identite',             v_identite,
          'creation_mode', coalesce(nullif(trim(contact_payload->>'creation_mode'), ''), 'contact_global_identity')),
      'pending', coalesce(job_priority, 18), auth.uid(), now())
  returning * into created_job;

  return created_job;
end;
$function$
;
