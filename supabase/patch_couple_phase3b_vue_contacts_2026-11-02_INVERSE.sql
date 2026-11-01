-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PHASE 3-B — RETOUR ARRIÈRE                                02/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- ⛔ D'ABORD : retirer du front (et redéployer) tout ce qui demande les 7 colonnes,
--   sinon l'annuaire tombe en erreur.
-- Une vue ne perd pas de colonnes par « create or replace » : on la RECRÉE à
-- l'identique de la définition relevée le 02/11 (43 colonnes), dans une seule
-- transaction (aucun dépendant), avec security_invoker et les mêmes droits.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

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

COMMIT;

-- CONTROLE : colonnes 43, security_invoker, authenticated lit, anon non
select
  (select count(*) from information_schema.columns where table_schema='public' and table_name='app_contacts_current') as colonnes,
  (select reloptions::text from pg_class where oid='public.app_contacts_current'::regclass) as options,
  has_table_privilege('authenticated', 'public.app_contacts_current', 'SELECT') as authenticated_lit,
  has_table_privilege('anon', 'public.app_contacts_current', 'SELECT') as anon_lit;
