-- =====================================================================
-- CHANTIER ① SÉCURITÉ -- FERMER LA CLÉ PUBLIQUE (rôle anon)
-- Date : 2026-10-08 · Détail : notice/CHANTIER_1_SECURITE_2026-10-08.md
--
-- POURQUOI. La clé « anon » est lisible par tout le monde dans le navigateur. Le 08/10 :
-- 105 fonctions de l'app (94 à pleins droits) et ~170 tables, vues et compteurs étaient
-- atteignables avec elle seule, sans connexion -- dont app_bascule_identite_contact_annuler.
-- C'est la suite de la « dette assumée » 0.7 du 24/08, et la cause de la rechute est écrite
-- depuis le 29/08 : Supabase OUVRE à anon toute fonction, table et séquence NEUVE.
--
-- CE QUI NE CHANGE PAS (vérifié, voir la note) :
--   · l'app connectée (rôle authenticated) garde ses droits ; elle ne charge rien avant la
--     connexion (bootstrapApp ne part qu'avec une session) ;
--   · le worker, la synchro, la surveillance, le backend Render (clé de service) ;
--   · les crons (postgres) ; les fonctions appelées par d'autres fonctions (toutes à pleins
--     droits) ; les règles RLS et du stockage ;
--   · les INTERNAUTES : photos (coffre public gti-photo), vitrine (JSON statique), espace
--     client, RDV et estimation publics, liens des e-mails -> stockage public ou Render ;
--   · pg_trgm (31 fonctions d'extension) : pas touchées.
--
-- CE QUE FAIT LE PATCH, en une transaction (une erreur = rien n'est appliqué) :
--   0. garde-fou d'entrée : la base est celle qu'on a mesurée, le patch n'est pas déjà passé
--   1. PHOTO D'AVANT : tous les droits anon / PUBLIC / authenticated touchés sont copiés dans
--      app_securite_droits_avant_20261008 -> le script inverse les rend à l'identique
--   A. fonctions de l'app : retirer PUBLIC et anon (authenticated et service_role gardés)
--   B. 20 fonctions que seul le serveur appelle : retirer aussi authenticated
--   C. tables, vues, séquences : retirer anon ; 13 vues de surveillance réservées au
--      serveur ; les 2 vues lues par le front deviennent LECTURE SEULE pour authenticated
--   D. 2 tables sans RLS : réservées au serveur, RLS activée
--   E. défauts : un objet NEUF ne naîtra plus ouvert à anon (ni à PUBLIC pour les fonctions)
--   9. contrôle de sortie : si un seul point est faux -> exception -> tout est annulé
--
-- RETOUR ARRIÈRE : supabase/patch_chantier1_fermer_anon_2026-10-08_INVERSE.sql
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 0. GARDE-FOU D'ENTRÉE
-- ---------------------------------------------------------------------
DO $$
DECLARE n int;
BEGIN
  IF to_regclass('public.app_securite_droits_avant_20261008') IS NOT NULL THEN
    RAISE EXCEPTION 'STOP : le patch est deja passe (la photo d''avant existe)';
  END IF;

  SELECT count(*) INTO n FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
   WHERE ns.nspname='public' AND p.prokind='f' AND pg_get_userbyid(p.proowner)='postgres'
     AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.deptype='e')
     AND NOT (coalesce(p.proacl::text,'') ~ 'service_role=X');
  IF n > 0 THEN RAISE EXCEPTION 'STOP : % fonction(s) sans droit explicite pour service_role -- le serveur les perdrait', n; END IF;

  SELECT count(*) INTO n FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
   WHERE ns.nspname='public' AND p.prokind='f' AND pg_get_userbyid(p.proowner)='postgres'
     AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.deptype='e')
     AND has_function_privilege('authenticated', p.oid, 'EXECUTE')
     AND NOT (coalesce(p.proacl::text,'') ~ 'authenticated=X');
  IF n > 0 THEN RAISE EXCEPTION 'STOP : % fonction(s) ou l''app connectee ne passe que par PUBLIC -- elle les perdrait', n; END IF;
END $$;

-- ---------------------------------------------------------------------
-- 1. PHOTO D'AVANT (pour le retour arrière)
-- ---------------------------------------------------------------------
CREATE TABLE public.app_securite_droits_avant_20261008 (
  objet_type  text NOT NULL,          -- 'FUNCTION' | 'TABLE' | 'SEQUENCE'
  objet       text NOT NULL,          -- signature complète, schéma compris
  beneficiaire text NOT NULL,         -- 'PUBLIC' | 'anon' | 'authenticated'
  privilege   text NOT NULL,
  pris_le     timestamptz NOT NULL DEFAULT now()
);

INSERT INTO public.app_securite_droits_avant_20261008 (objet_type, objet, beneficiaire, privilege)
SELECT 'FUNCTION', format('public.%I(%s)', p.proname, pg_get_function_identity_arguments(p.oid)),
       CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END, a.privilege_type
  FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace, aclexplode(p.proacl) a
 WHERE ns.nspname='public' AND p.prokind='f' AND pg_get_userbyid(p.proowner)='postgres'
   AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.deptype='e')
   AND (a.grantee = 0 OR pg_get_userbyid(a.grantee) IN ('anon','authenticated'));

INSERT INTO public.app_securite_droits_avant_20261008 (objet_type, objet, beneficiaire, privilege)
SELECT CASE WHEN c.relkind='S' THEN 'SEQUENCE' ELSE 'TABLE' END, format('public.%I', c.relname),
       CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END, a.privilege_type
  FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace, aclexplode(c.relacl) a
 WHERE ns.nspname='public' AND c.relkind IN ('r','v','m','S','p') AND pg_get_userbyid(c.relowner)='postgres'
   AND c.relname <> 'app_securite_droits_avant_20261008'
   AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid='pg_class'::regclass AND d.objid=c.oid AND d.deptype='e')
   AND (a.grantee = 0 OR pg_get_userbyid(a.grantee) IN ('anon','authenticated'));

-- la photo elle-même n'est lisible que par le serveur
REVOKE ALL ON TABLE public.app_securite_droits_avant_20261008 FROM PUBLIC, anon, authenticated;
ALTER TABLE public.app_securite_droits_avant_20261008 ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------
-- A. FONCTIONS DE L'APP : retirer PUBLIC et anon
-- ---------------------------------------------------------------------
DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT format('public.%I(%s)', p.proname, pg_get_function_identity_arguments(p.oid)) sig
      FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
     WHERE ns.nspname='public' AND p.prokind='f' AND pg_get_userbyid(p.proowner)='postgres'
       AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.deptype='e')
  LOOP
    EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM PUBLIC, anon', r.sig);
  END LOOP;
END $$;

-- ---------------------------------------------------------------------
-- B. RÉSERVÉES AU SERVEUR (worker, phase2, crons, ou appelées par d'autres fonctions)
--    Aucun appel depuis le front (git grep), aucun appelant SQL en droits d'appelant,
--    aucune règle RLS : vérifié le 08/10.
-- ---------------------------------------------------------------------
DO $$
DECLARE r record; n int := 0;
BEGIN
  FOR r IN
    SELECT format('public.%I(%s)', p.proname, pg_get_function_identity_arguments(p.oid)) sig
      FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
     WHERE ns.nspname='public' AND p.prokind='f' AND p.proname = ANY (ARRAY[
       'app_annonce_pending_solder_hektor','app_annonce_reappliquer_saisies',
       'app_attribuer_chaines_affaire','app_bascule_identite_contact',
       'app_bascule_identite_contact_annuler','app_photo_marquer_sortie_vitrine',
       'app_photos_placeholder_sans_photo','app_photos_remplir_adresses_app',
       'app_photos_remplir_adresses_registre','app_photos_vignettes_archives_a_faire',
       'app_refresh_rapprochements_for_dossier','app_refresh_rapprochements_for_search',
       'app_repartition_absorber','app_repartition_purger_orphelines',
       'app_acquereurs_json','app_console_resolve_contact_hektor_user',
       'app_dossier_equipements','app_dossier_match_payload',
       'app_match_score_v2','app_upsert_one_rapprochement'])
  LOOP
    EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM authenticated', r.sig);
    n := n + 1;
  END LOOP;
  IF n <> 20 THEN RAISE EXCEPTION 'STOP : lot B attendait 20 fonctions, trouve %', n; END IF;
END $$;

-- ---------------------------------------------------------------------
-- C. TABLES, VUES, SÉQUENCES
-- ---------------------------------------------------------------------
-- C.1 anon ne garde rien (les tables restent aussi protégées par leurs règles RLS)
DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT c.relname, c.relkind
      FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
     WHERE ns.nspname='public' AND c.relkind IN ('r','v','m','S','p') AND pg_get_userbyid(c.relowner)='postgres'
       AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid='pg_class'::regclass AND d.objid=c.oid AND d.deptype='e')
  LOOP
    EXECUTE format('REVOKE ALL ON %s public.%I FROM anon',
                   CASE WHEN r.relkind='S' THEN 'SEQUENCE' ELSE 'TABLE' END, r.relname);
  END LOOP;
END $$;

-- C.2 les 13 vues de surveillance et de synchro : réservées au serveur
--     (elles contournent la RLS ; lues seulement par monitoring/ et phase2/, clé de service)
REVOKE ALL ON TABLE
  public.app_affaires_sans_numero_hektor,
  public.app_annonces_sans_numero_hektor,
  public.app_dossier_match_attrs,
  public.app_en_attente_humain,
  public.app_stat_negociateur_v,
  public.app_v_contacts_en_double_identite,
  public.app_v_contacts_sans_cible,
  public.app_v_correspondance_identite_cible,
  public.app_v_couples_non_traduits,
  public.app_v_envois_en_attente_hektor,
  public.app_v_orphelins_recherche,
  public.app_v_plages_numeros,
  public.app_v_plages_trop_proches
FROM authenticated;

-- C.3 les 2 vues lues par le front : LECTURE SEULE (le front ne fait que des select, vérifié)
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER, MAINTAIN ON TABLE
  public.app_registre_mandats_current,
  public.app_contact_relations_current
FROM authenticated;

-- ---------------------------------------------------------------------
-- D. LES 2 TABLES SANS RLS : réservées au serveur
--    app_rapprochement_search_state : écrite par le worker (clé de service) et par des
--    fonctions à pleins droits ; app_console_job_error_archive : aucun lecteur.
-- ---------------------------------------------------------------------
REVOKE ALL ON TABLE public.app_console_job_error_archive, public.app_rapprochement_search_state FROM authenticated;
ALTER TABLE public.app_console_job_error_archive  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_rapprochement_search_state ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------
-- E. LES DÉFAUTS : un objet NEUF ne naîtra plus ouvert
--    (seules les fonctions de l'app existent en dehors des extensions, toutes dans public,
--     vérifié : le retrait global de PUBLIC ne touche donc que les fonctions futures)
-- ---------------------------------------------------------------------
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE EXECUTE ON FUNCTIONS FROM anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON TABLES FROM anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

-- ---------------------------------------------------------------------
-- 9. CONTRÔLE DE SORTIE -- un seul point faux et TOUT est annulé
-- ---------------------------------------------------------------------
DO $$
DECLARE n int; manque text;
BEGIN
  -- plus aucune fonction de l'app atteignable par anon
  SELECT count(*) INTO n FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
   WHERE ns.nspname='public' AND p.prokind='f' AND pg_get_userbyid(p.proowner)='postgres'
     AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.deptype='e')
     AND has_function_privilege('anon', p.oid, 'EXECUTE');
  IF n > 0 THEN RAISE EXCEPTION 'CONTROLE : % fonction(s) encore ouvertes a anon', n; END IF;

  -- plus aucune table, vue ou séquence atteignable par anon
  SELECT count(*) INTO n FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
   WHERE ns.nspname='public' AND c.relkind IN ('r','v','m','S','p') AND pg_get_userbyid(c.relowner)='postgres'
     AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid='pg_class'::regclass AND d.objid=c.oid AND d.deptype='e')
     AND coalesce(c.relacl::text,'') ~ 'anon=';
  IF n > 0 THEN RAISE EXCEPTION 'CONTROLE : % table(s)/vue(s)/sequence(s) encore ouvertes a anon', n; END IF;

  -- le serveur garde TOUT
  SELECT count(*) INTO n FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
   WHERE ns.nspname='public' AND p.prokind='f' AND pg_get_userbyid(p.proowner)='postgres'
     AND NOT has_function_privilege('service_role', p.oid, 'EXECUTE');
  IF n > 0 THEN RAISE EXCEPTION 'CONTROLE : le serveur a perdu % fonction(s)', n; END IF;

  -- l'app connectée garde ce dont elle a besoin (échantillon des fonctions vitales)
  SELECT string_agg(f, ', ') INTO manque FROM unnest(ARRAY[
      'is_app_user_active','is_app_admin','can_access_current_dossier','can_access_v1_dossier',
      'app_console_can_access_dossier','app_console_can_request_job','app_get_rapprochements',
      'app_edit_annonce_optimistic','app_edit_search_optimistic','app_create_search_optimistic',
      'app_cockpit_activite','app_contact_activite','app_dvf_comparables',
      'app_update_mandant_contact_optimistic','app_link_mandant_optimistic']) f
   WHERE NOT EXISTS (SELECT 1 FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
                      WHERE ns.nspname='public' AND p.proname=f AND has_function_privilege('authenticated', p.oid, 'EXECUTE'));
  IF manque IS NOT NULL THEN RAISE EXCEPTION 'CONTROLE : l''app connectee a perdu : %', manque; END IF;

  -- l'app connectée garde au total les 124 - 20 = 104 fonctions qu'elle avait, moins le lot B
  SELECT count(*) INTO n FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
   WHERE ns.nspname='public' AND p.prokind='f' AND pg_get_userbyid(p.proowner)='postgres'
     AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.classid='pg_proc'::regclass AND d.objid=p.oid AND d.deptype='e')
     AND has_function_privilege('authenticated', p.oid, 'EXECUTE');
  IF n <> 104 THEN RAISE EXCEPTION 'CONTROLE : l''app connectee a % fonctions, 104 attendues', n; END IF;

  -- les 2 vues du front : lecture oui, écriture non
  IF NOT has_table_privilege('authenticated','public.app_registre_mandats_current','SELECT')
     OR NOT has_table_privilege('authenticated','public.app_contact_relations_current','SELECT') THEN
    RAISE EXCEPTION 'CONTROLE : le front ne peut plus lire le registre ou les liens';
  END IF;
  IF has_table_privilege('authenticated','public.app_registre_mandats_current','UPDATE')
     OR has_table_privilege('authenticated','public.app_contact_relations_current','UPDATE') THEN
    RAISE EXCEPTION 'CONTROLE : les 2 vues du front sont encore modifiables';
  END IF;

  -- les 2 tables : RLS active
  IF NOT (SELECT relrowsecurity FROM pg_class WHERE oid='public.app_rapprochement_search_state'::regclass)
     OR NOT (SELECT relrowsecurity FROM pg_class WHERE oid='public.app_console_job_error_archive'::regclass) THEN
    RAISE EXCEPTION 'CONTROLE : RLS non active sur les 2 tables';
  END IF;

  -- la photo d'avant n'est pas vide
  SELECT count(*) INTO n FROM public.app_securite_droits_avant_20261008;
  IF n < 1000 THEN RAISE EXCEPTION 'CONTROLE : photo d''avant trop maigre (% lignes)', n; END IF;

  RAISE NOTICE 'CHANTIER 1 : controle de sortie OK -- photo d''avant : % lignes', n;
END $$;

COMMIT;
