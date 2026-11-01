-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PHASE 3-B — LA VUE DE L'ÉCRAN VOIT LA NATURE ET LE COUPLE   02/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A APPLIQUER avec l'accord de Frédéric, APRES la répétition.
-- Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §14.
--
-- CE QUE FAIT CE PATCH — ADDITIF : la vue app_contacts_current (celle que lit
-- l'annuaire, lib/api.ts `contactsCurrentView`) gagne SEPT colonnes, À LA FIN :
--   couple_json (P2), nature_fiche, couple_deuxieme, civilite_app, civilite_source,
--   suit_principale_archivee, supprimee_chez_hektor (phase 2).
-- Les 43 colonnes existantes ne bougent pas (même ordre, même définition).
-- Le front actuel ne les demande pas : RIEN NE CHANGE À L'ÉCRAN tant que les
-- pièces C et D ne sont pas en ligne.
--
-- ⛔ ORDRE : ce patch AVANT tout front qui demande ces colonnes (sinon l'annuaire
--   entier tombe en erreur « column does not exist »).
-- ⛔ GARDE : la vue n'est remplacée que si sa définition est celle relevée le 02/11
--   (empreinte 8004d105…). Elle garde security_invoker=true et ses droits
--   (create or replace conserve les droits ; on les revérifie quand même).
-- RETOUR ARRIÈRE : supabase/patch_couple_phase3b_vue_contacts_2026-11-02_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

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

COMMIT;

-- CONTROLE (lecture seule) : colonnes 50, security_invoker garde, anon 0, lignes = table
select
  (select count(*) from information_schema.columns where table_schema='public' and table_name='app_contacts_current') as colonnes,
  (select reloptions::text from pg_class where oid='public.app_contacts_current'::regclass) as options,
  has_table_privilege('anon', 'public.app_contacts_current', 'SELECT') as anon_lit,
  has_table_privilege('authenticated', 'public.app_contacts_current', 'SELECT') as authenticated_lit,
  (select count(*) from public.app_contacts_current) as lignes_vue,
  (select count(*) from public.app_contact_current) as lignes_table;
