-- =====================================================================
-- RETOUR ARRIERE DU PATCH 4a (vue app_en_attente_humain)
-- Date : 2026-10-09
--
-- Remet la vue EXACTEMENT dans l'etat mesure le 09/10/2026 : la seule branche
-- « gestes abandonnes », sans la branche de la suite de creation.
-- Empreinte attendue APRES ce script (sans les retours chariot) :
--     2ef0749361e2bb309df7cb7cdab9cbec
--
-- `create or replace view` conserve l'ACL (postgres + service_role) : ce script
-- ne fait JAMAIS `drop view`, qui rouvrirait la vue et casserait le chantier ①.
-- Le commentaire de la vue est remis a NULL, son etat d'avant le patch.
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='60s';

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

-- Controle : l'empreinte est bien revenue a celle du 09/10.
DO $$
DECLARE v_empreinte text; v_acl text;
BEGIN
  SELECT md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''))
    INTO v_empreinte;
  IF v_empreinte <> '2ef0749361e2bb309df7cb7cdab9cbec' THEN
    RAISE EXCEPTION 'STOP : le retour arriere n''a pas rendu la vue d''origine (empreinte %)', v_empreinte;
  END IF;
  SELECT c.relacl::text INTO v_acl FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
   WHERE ns.nspname='public' AND c.relname='app_en_attente_humain';
  IF v_acl LIKE '%anon=%' OR v_acl LIKE '%authenticated=%' THEN
    RAISE EXCEPTION 'STOP : la vue s''est rouverte a anon/authenticated (%)', v_acl;
  END IF;
END $$;

COMMIT;
