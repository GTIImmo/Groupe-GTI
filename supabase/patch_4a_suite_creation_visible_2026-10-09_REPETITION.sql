-- =====================================================================
-- REPETITION DU PATCH 4a -- N'ECRIT RIEN, TOUT EST ANNULE A LA FIN
-- Date : 2026-10-09
--
-- Elle joue LE VRAI patch, puis LE VRAI retour arriere, mesure tout au passage,
-- et finit par une ERREUR VOLONTAIRE qui annule la transaction entiere.
-- A coller dans l'editeur SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
-- Puis me recopier le message d'erreur. Il doit dire, dans cet ordre :
--
--   ESSAI ANNULE -- 4a
--   empreinte_avant=2ef0749361e2bb309df7cb7cdab9cbec
--   lignes_avant=0  colonnes_avant=7
--   acl_avant={postgres=arwdDxtm/postgres,service_role=arwdDxtm/postgres}
--   empreinte_apres=<NOUVELLE, a noter : elle devient la reference>
--   lignes_apres=0  branche1_apres=0  branche2_apres=0  colonnes_apres=7
--   acl_apres=IDENTIQUE
--   commentaire_pose=oui
--   branche2_sans_fenetre=4   <= LA PREUVE : la branche neuve retrouve bien les
--                                4 cas mesures (62437, 62637, 62657, 62965) ;
--                                ils sont hors des 30 jours, d'ou lignes_apres=0
--   exemple=annonce 62657 -> annonce creee chez Hektor, mais : champs saisis a la creation
--   empreinte_retour=2ef0749361e2bb309df7cb7cdab9cbec  (identique a avant)
--   acl_retour=IDENTIQUE  commentaire_retour=vide
--
-- Si UN seul chiffre differe, on ne colle pas le vrai patch.
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='120s';

CREATE TEMP TABLE mesures_4a (ordre int, cle text, valeur text) ON COMMIT DROP;

-- ---------------------------------------------------------------------
-- A. AVANT
-- ---------------------------------------------------------------------
INSERT INTO mesures_4a
SELECT 1, 'empreinte_avant',
       md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''));
INSERT INTO mesures_4a SELECT 2, 'lignes_avant', count(*)::text FROM app_en_attente_humain;
INSERT INTO mesures_4a SELECT 3, 'colonnes_avant', count(*)::text FROM information_schema.columns
 WHERE table_name='app_en_attente_humain'
   AND column_name IN ('objet','reference','libelle','nature','cause','tentatives','depuis');
INSERT INTO mesures_4a SELECT 4, 'acl_avant', coalesce(c.relacl::text,'(vide)')
 FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
 WHERE ns.nspname='public' AND c.relname='app_en_attente_humain';

-- =====================================================================
-- B. LE VRAI PATCH (copie mot pour mot, sans son BEGIN/COMMIT)
-- =====================================================================
DO $$
DECLARE v_empreinte text; n int;
BEGIN
  IF to_regclass('public.app_en_attente_humain') IS NULL THEN
    RAISE EXCEPTION 'STOP : la vue app_en_attente_humain est introuvable';
  END IF;
  SELECT md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''))
    INTO v_empreinte;
  IF v_empreinte <> '2ef0749361e2bb309df7cb7cdab9cbec' THEN
    RAISE EXCEPTION 'STOP : la vue n''est plus celle mesuree le 09/10 (empreinte %) -- une autre session est passee', v_empreinte;
  END IF;
  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_name = 'app_en_attente_humain'
     AND column_name IN ('objet','reference','libelle','nature','cause','tentatives','depuis');
  IF n <> 7 THEN RAISE EXCEPTION 'STOP : la vue n''a pas ses 7 colonnes (%)', n; END IF;
  IF to_regclass('public.app_pending_resolution') IS NULL THEN
    RAISE EXCEPTION 'STOP : app_pending_resolution est introuvable';
  END IF;
  SELECT count(*) INTO n FROM pg_attribute
   WHERE attrelid='public.app_console_job'::regclass
     AND attname IN ('result_json','job_type','status','requested_at','updated_at')
     AND NOT attisdropped;
  IF n <> 5 THEN RAISE EXCEPTION 'STOP : app_console_job n''a pas les 5 colonnes attendues (%)', n; END IF;
END $$;

create or replace view public.app_en_attente_humain as
 SELECT 'geste'::text AS objet,
    COALESCE('annonce '::text || NULLIF(j.hektor_annonce_id, ''::text), 'sans annonce'::text) AS reference,
    COALESCE(d.titre_bien, j.job_type) AS libelle,
    'geste abandonne'::text AS nature,
    (j.job_type || ' : '::text) || "left"(COALESCE(j.error_message, 'sans message'::text), 90) AS cause,
    COALESCE(j.attempt_count, 0) AS tentatives,
    j.updated_at AS depuis
   FROM app_console_job j
     LEFT JOIN app_dossier_current d ON d.hektor_annonce_id::text = j.hektor_annonce_id
  WHERE j.status = 'error'::text AND COALESCE(j.attempt_count, 0) >= 5 AND j.requested_at > (now() - '30 days'::interval) AND NOT (EXISTS ( SELECT 1
           FROM app_pending_resolution r
          WHERE r.objet = 'geste'::text AND (r.payload_json ->> 'job_id'::text) = j.id::text))
UNION ALL
 SELECT 'geste'::text AS objet,
    COALESCE('annonce '::text || NULLIF(j.hektor_annonce_id, ''::text), 'sans annonce'::text) AS reference,
    COALESCE(d.titre_bien, j.result_json -> 'requested_payload' ->> 'title', j.job_type) AS libelle,
    'suite de creation incomplete'::text AS nature,
    'annonce creee chez Hektor, mais : '::text || concat_ws(', ',
        CASE WHEN j.result_json -> 'initial_fields_update' ->> 'status' IN ('error','partial')
             THEN 'champs saisis a la creation' END,
        CASE WHEN j.result_json -> 'initial_mandant_create' ->> 'status' = 'error'
             THEN 'mandant cree a la creation' END,
        CASE WHEN j.result_json -> 'initial_mandant_links' ->> 'status' = 'partial_error'
             THEN 'mandant choisi non rattache' END) AS cause,
    COALESCE(j.attempt_count, 0) AS tentatives,
    j.updated_at AS depuis
   FROM app_console_job j
     LEFT JOIN app_dossier_current d ON d.hektor_annonce_id::text = j.hektor_annonce_id
  WHERE j.job_type = 'create_hektor_draft_annonce'::text
    AND j.status = 'done'::text
    AND j.requested_at > (now() - '30 days'::interval)
    AND (j.result_json -> 'initial_fields_update' ->> 'status' IN ('error','partial')
      OR j.result_json -> 'initial_mandant_create' ->> 'status' = 'error'
      OR j.result_json -> 'initial_mandant_links' ->> 'status' = 'partial_error')
    AND NOT (EXISTS ( SELECT 1
           FROM app_pending_resolution r
          WHERE r.objet = 'geste'::text AND (r.payload_json ->> 'job_id'::text) = j.id::text));

COMMENT ON VIEW public.app_en_attente_humain IS
  'Ce qui attend un humain. Branche 1 : gestes abandonnes (>= 5 tentatives). '
  'Branche 2 (4a, 09/10/2026) : creation d''annonce « done » dont la SUITE a rate '
  '(champs ou mandant) -- le travail reste done a dessein, l''annonce existe chez Hektor. '
  'Se solde dans app_pending_resolution (objet=geste, payload_json->>job_id).';

DO $$
DECLARE n int; v_acl text;
BEGIN
  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_name = 'app_en_attente_humain'
     AND column_name IN ('objet','reference','libelle','nature','cause','tentatives','depuis');
  IF n <> 7 THEN RAISE EXCEPTION 'STOP : la vue a perdu une colonne (%)', n; END IF;
  SELECT c.relacl::text INTO v_acl FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
   WHERE ns.nspname='public' AND c.relname='app_en_attente_humain';
  IF v_acl LIKE '%anon=%' OR v_acl LIKE '%authenticated=%' THEN
    RAISE EXCEPTION 'STOP : la vue vient de se rouvrir a anon/authenticated (%) -- chantier ①', v_acl;
  END IF;
END $$;

-- ---------------------------------------------------------------------
-- C. APRES LE PATCH
-- ---------------------------------------------------------------------
INSERT INTO mesures_4a
SELECT 5, 'empreinte_apres',
       md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''));
INSERT INTO mesures_4a SELECT 6, 'lignes_apres', count(*)::text FROM app_en_attente_humain;
INSERT INTO mesures_4a SELECT 7, 'branche1_apres', count(*)::text FROM app_en_attente_humain
 WHERE nature = 'geste abandonne';
INSERT INTO mesures_4a SELECT 8, 'branche2_apres', count(*)::text FROM app_en_attente_humain
 WHERE nature = 'suite de creation incomplete';
INSERT INTO mesures_4a SELECT 9, 'colonnes_apres', count(*)::text FROM information_schema.columns
 WHERE table_name='app_en_attente_humain'
   AND column_name IN ('objet','reference','libelle','nature','cause','tentatives','depuis');
INSERT INTO mesures_4a
SELECT 10, 'acl_apres',
       CASE WHEN coalesce(c.relacl::text,'(vide)') = (SELECT valeur FROM mesures_4a WHERE cle='acl_avant')
            THEN 'IDENTIQUE' ELSE 'DIFFERENTE : ' || coalesce(c.relacl::text,'(vide)') END
 FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
 WHERE ns.nspname='public' AND c.relname='app_en_attente_humain';
INSERT INTO mesures_4a
SELECT 11, 'commentaire_pose',
       CASE WHEN coalesce(obj_description('public.app_en_attente_humain'::regclass,'pg_class'),'') LIKE '%Branche 2 (4a%'
            THEN 'oui' ELSE 'NON' END;

-- LA PREUVE QUE LA BRANCHE NEUVE TROUVE : memes conditions, SANS la fenetre de
-- 30 jours (les 4 cas reels datent du 07/06 au 28/08, donc hors fenetre).
INSERT INTO mesures_4a
SELECT 12, 'branche2_sans_fenetre', count(*)::text
  FROM app_console_job j
 WHERE j.job_type = 'create_hektor_draft_annonce' AND j.status = 'done'
   AND (j.result_json -> 'initial_fields_update' ->> 'status' IN ('error','partial')
     OR j.result_json -> 'initial_mandant_create' ->> 'status' = 'error'
     OR j.result_json -> 'initial_mandant_links' ->> 'status' = 'partial_error');

-- Le texte que la sentinelle montrerait, sur le cas du 08/07.
INSERT INTO mesures_4a
SELECT 13, 'exemple', 'annonce ' || j.hektor_annonce_id || ' -> ' ||
       'annonce creee chez Hektor, mais : ' || concat_ws(', ',
         CASE WHEN j.result_json -> 'initial_fields_update' ->> 'status' IN ('error','partial')
              THEN 'champs saisis a la creation' END,
         CASE WHEN j.result_json -> 'initial_mandant_create' ->> 'status' = 'error'
              THEN 'mandant cree a la creation' END,
         CASE WHEN j.result_json -> 'initial_mandant_links' ->> 'status' = 'partial_error'
              THEN 'mandant choisi non rattache' END)
  FROM app_console_job j
 WHERE j.hektor_annonce_id = '62657' AND j.job_type = 'create_hektor_draft_annonce';

-- =====================================================================
-- D. LE VRAI RETOUR ARRIERE (copie mot pour mot, sans son BEGIN/COMMIT)
-- =====================================================================
create or replace view public.app_en_attente_humain as
 SELECT 'geste'::text AS objet,
    COALESCE('annonce '::text || NULLIF(j.hektor_annonce_id, ''::text), 'sans annonce'::text) AS reference,
    COALESCE(d.titre_bien, j.job_type) AS libelle,
    'geste abandonne'::text AS nature,
    (j.job_type || ' : '::text) || "left"(COALESCE(j.error_message, 'sans message'::text), 90) AS cause,
    COALESCE(j.attempt_count, 0) AS tentatives,
    j.updated_at AS depuis
   FROM app_console_job j
     LEFT JOIN app_dossier_current d ON d.hektor_annonce_id::text = j.hektor_annonce_id
  WHERE j.status = 'error'::text AND COALESCE(j.attempt_count, 0) >= 5 AND j.requested_at > (now() - '30 days'::interval) AND NOT (EXISTS ( SELECT 1
           FROM app_pending_resolution r
          WHERE r.objet = 'geste'::text AND (r.payload_json ->> 'job_id'::text) = j.id::text));

COMMENT ON VIEW public.app_en_attente_humain IS NULL;

-- ---------------------------------------------------------------------
-- E. APRES LE RETOUR ARRIERE
-- ---------------------------------------------------------------------
INSERT INTO mesures_4a
SELECT 14, 'empreinte_retour',
       md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''));
INSERT INTO mesures_4a
SELECT 15, 'acl_retour',
       CASE WHEN coalesce(c.relacl::text,'(vide)') = (SELECT valeur FROM mesures_4a WHERE cle='acl_avant')
            THEN 'IDENTIQUE' ELSE 'DIFFERENTE : ' || coalesce(c.relacl::text,'(vide)') END
 FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
 WHERE ns.nspname='public' AND c.relname='app_en_attente_humain';
INSERT INTO mesures_4a
SELECT 16, 'commentaire_retour',
       CASE WHEN obj_description('public.app_en_attente_humain'::regclass,'pg_class') IS NULL
            THEN 'vide' ELSE 'RESTE : ' || obj_description('public.app_en_attente_humain'::regclass,'pg_class') END;

-- =====================================================================
-- F. L'ERREUR VOLONTAIRE : elle annule TOUT et rend les mesures
-- =====================================================================
DO $$
DECLARE v_rapport text;
BEGIN
  SELECT string_agg(cle || '=' || valeur, '  ' ORDER BY ordre) INTO v_rapport FROM mesures_4a;
  RAISE EXCEPTION 'ESSAI ANNULE -- 4a  %', v_rapport;
END $$;

ROLLBACK;
