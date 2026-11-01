-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PHASE 3-B — RÉPÉTITION (rien ne reste)                    02/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Joue le PATCH, mesure, joue le RETOUR ARRIÈRE, mesure, puis LÈVE « ESSAI ANNULE » :
-- tout est annulé. Fabriquée à partir des deux fichiers (corps entre BEGIN et COMMIT).
-- Attendu : 01 colonnes=50 · 02 invoker=ok · 03 droits=ok · 04 lignes=ok ·
--           05 temoin=ok (10000045 porte sa nature) · 06 retour=43 · 07 empreinte=ok
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

CREATE TEMP TABLE _rep(t text) ON COMMIT DROP;

-- ── LE PATCH ──
DO $garde$
BEGIN
  IF md5(pg_get_viewdef('public.app_contacts_current'::regclass, true)) <> '8004d10588f97fc08b7ab2e3f2508bec' THEN
    RAISE EXCEPTION '%', format('ARRET : app_contacts_current a change depuis le 02/11 (empreinte %s). Rien n''est ecrit.',
                                md5(pg_get_viewdef('public.app_contacts_current'::regclass, true)));
  END IF;
END
$garde$;

create or replace view public.app_contacts_current with (security_invoker = true) as
 SELECT hektor_contact_id,
    hektor_agence_id,
    hektor_negociateur_id,
    negociateur_email,
    commercial_nom,
    agence_nom,
    civilite,
    nom,
    prenom,
    display_name,
    archive,
    date_enregistrement,
    date_maj,
    email,
    phone_primary,
    phone_secondary,
    ville,
    code_postal,
    typologies_json,
    relation_roles_json,
    linked_annonce_count,
    active_search_count,
    total_search_count,
    supabase_sync_eligible,
    eligibility_reasons_json,
    duplicate_group_count,
    duplicate_max_severity,
    duplicate_primary_candidate_id,
    completeness_score,
    search_text,
    source_hash,
    refreshed_at,
    has_contact_detail,
    contact_detail_synced_at,
    adresse,
    birth_date,
    birth_place,
    marital_status,
    hektor_couple_contact_id,
    couple_role,
    hektor_target_id,
    app_contact_id,
    commentaires,
    -- COUPLES (02/11/2026) : à la fin, toujours
    couple_json,
    nature_fiche,
    couple_deuxieme,
    civilite_app,
    civilite_source,
    suit_principale_archivee,
    supprimee_chez_hektor
   FROM app_contact_current;

revoke all on public.app_contacts_current from anon;
grant select on public.app_contacts_current to authenticated;
grant all on public.app_contacts_current to service_role;

INSERT INTO _rep SELECT
  ' | 01 colonnes=' || (select count(*) from information_schema.columns where table_schema='public' and table_name='app_contacts_current')
  || ' | 02 invoker=' || case when (select reloptions::text from pg_class where oid='public.app_contacts_current'::regclass) like '%security_invoker=true%' then 'ok' else 'PERDU' end
  || ' | 03 droits=' || case when has_table_privilege('authenticated','public.app_contacts_current','SELECT') and not has_table_privilege('anon','public.app_contacts_current','SELECT') then 'ok' else 'FAUX' end
  || ' | 04 lignes=' || case when (select count(*) from public.app_contacts_current) = (select count(*) from public.app_contact_current) then 'ok' else 'FAUX' end
  || ' | 05 temoin=' || coalesce((select case when nature_fiche='personne_seule' and civilite_app='Mme.' then 'ok' else 'FAUX:'||coalesce(nature_fiche,'vide') end from public.app_contacts_current where hektor_contact_id='10000045'), 'ABSENT');

-- ── LE RETOUR ARRIÈRE ──
drop view public.app_contacts_current;

create view public.app_contacts_current with (security_invoker = true) as
 SELECT hektor_contact_id,
    hektor_agence_id,
    hektor_negociateur_id,
    negociateur_email,
    commercial_nom,
    agence_nom,
    civilite,
    nom,
    prenom,
    display_name,
    archive,
    date_enregistrement,
    date_maj,
    email,
    phone_primary,
    phone_secondary,
    ville,
    code_postal,
    typologies_json,
    relation_roles_json,
    linked_annonce_count,
    active_search_count,
    total_search_count,
    supabase_sync_eligible,
    eligibility_reasons_json,
    duplicate_group_count,
    duplicate_max_severity,
    duplicate_primary_candidate_id,
    completeness_score,
    search_text,
    source_hash,
    refreshed_at,
    has_contact_detail,
    contact_detail_synced_at,
    adresse,
    birth_date,
    birth_place,
    marital_status,
    hektor_couple_contact_id,
    couple_role,
    hektor_target_id,
    app_contact_id,
    commentaires
   FROM app_contact_current;

revoke all on public.app_contacts_current from anon;
grant select on public.app_contacts_current to authenticated;
grant all on public.app_contacts_current to service_role;

DO $controle$
BEGIN
  IF md5(pg_get_viewdef('public.app_contacts_current'::regclass, true)) <> '8004d10588f97fc08b7ab2e3f2508bec' THEN
    RAISE EXCEPTION 'ARRET : la vue recreee ne correspond pas a celle du 02/11. Tout est annule.';
  END IF;
END
$controle$;

DO $essai$
DECLARE t text;
BEGIN
  select _rep.t into t from _rep;
  t := t || ' | 06 retour=' || (select count(*) from information_schema.columns where table_schema='public' and table_name='app_contacts_current')
         || ' | 07 empreinte=' || case when md5(pg_get_viewdef('public.app_contacts_current'::regclass, true)) = '8004d10588f97fc08b7ab2e3f2508bec' then 'ok' else 'FAUX' end;
  RAISE EXCEPTION 'ESSAI ANNULE --%', t;
END
$essai$;

ROLLBACK;
