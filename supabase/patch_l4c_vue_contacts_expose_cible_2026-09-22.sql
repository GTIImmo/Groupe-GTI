-- ═══════════════════════════════════════════════════════════════════════════
-- L4-c ③ — LA VUE DU FRONT EXPOSE LA CASE CIBLE                 22/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- CE QU'ON A EVITE DE JUSTESSE. Le front venait d'apprendre a demander
-- `hektor_target_id` dans sa requete de l'annuaire. Mais il ne lit pas la table,
-- il lit la vue `app_contacts_current` -- et elle ne l'exposait pas.
-- Deployer le front avant ce patch aurait fait repondre 400 a CHAQUE
-- chargement de l'annuaire : ecran blanc pour les negociateurs, et une erreur
-- qui n'aurait rien dit d'utile.
--
-- ⚠ L'ORDRE COMPTE, ET IL EST DANS CE SENS-LA : la vue d'abord, le front
--   ensuite. L'inverse casse. Une vue qui expose une colonne de plus ne gene
--   personne ; un front qui demande une colonne absente tombe.
--
-- CE QU'ON AJOUTE, et rien d'autre (aucune colonne retiree, aucune renommee) :
--     hektor_target_id   LE numero pour viser Hektor. Le front s'en sert pour
--                        le lien « Ouvrir Hektor » -- le seul endroit du front
--                        qui envoie un numero chez lui hors de tout travail.
--     app_contact_id     la doublure. Elle ne sert a personne aujourd'hui,
--                        mais c'est elle que la bascule (L4-c) fera lire :
--                        autant que la vue la porte des maintenant, pour que
--                        ce jour-la il n'y ait plus qu'un interrupteur.
--
-- RETOUR ARRIERE : rejouer la definition sans les deux dernieres colonnes.
-- ═══════════════════════════════════════════════════════════════════════════

create or replace view public.app_contacts_current as
 select hektor_contact_id,
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
    app_contact_id
   from app_contact_current;

comment on view public.app_contacts_current is
  'Vue de l''annuaire lue par le front. L4-c 22/09/2026 : expose en plus hektor_target_id (le numero pour viser Hektor -- le lien « Ouvrir Hektor » s''en sert) et app_contact_id (la doublure, que la bascule fera lire).';
