-- =====================================================================
-- RETOUR ARRIERE DU PATCH 4d  (vue app_en_attente_humain + balayage)
-- Date : 2026-10-11
--
-- Remet les deux objets EXACTEMENT dans l'etat mesure le 11/10, avant 4d :
--   la vue      -> ses 2 branches du patch 4a   empreinte e2c015e16d1339fee080b6b2cc7bcb2b
--   le balayage -> ses erreurs purgees a 24 h   empreinte 8031dd042d33e3785a27da0c4e106498
--
-- `create or replace` conserve l'ACL (postgres + service_role pour la vue) : ce
-- script ne fait JAMAIS `drop`, qui rouvrirait l'objet et casserait le chantier ①.
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='60s';

-- ── LA VUE, telle que le patch 4a l'a laissee ────────────────────────────────
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

-- ── LE BALAYAGE, avec ses erreurs purgees a 24 h ─────────────────────────────
CREATE OR REPLACE FUNCTION public.app_sweep_stale_provisionals()
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  -- ── 1) CE QUI TRAINE « EN COURS » DEVIENT UNE ERREUR VISIBLE ─────────────
  update app_annonce_provisional
     set status = 'error',
         error_message = coalesce(nullif(trim(error_message), ''), 'Création expirée (le bien n''a pas été confirmé dans le délai)'),
         updated_at = now()
   where status not in ('linked', 'error') and created_at < now() - interval '15 minutes';

  update app_contact_provisional
     set status = 'error',
         error_message = coalesce(nullif(trim(error_message), ''), 'Création expirée (le contact n''a pas été confirmé dans le délai)'),
         updated_at = now()
   where status not in ('linked', 'error') and created_at < now() - interval '15 minutes';

  update app_search_provisional
     set status = 'error',
         error_message = coalesce(nullif(trim(error_message), ''), 'Création expirée (la recherche n''a pas été confirmée dans le délai)'),
         updated_at = now()
   where status not in ('linked', 'error') and created_at < now() - interval '15 minutes';

  update app_relation_provisional
     set status = 'error',
         error_message = coalesce(nullif(trim(error_message), ''), 'Création expirée (le lien n''a pas été confirmé dans le délai)'),
         updated_at = now()
   where status not in ('linked', 'error') and created_at < now() - interval '15 minutes';

  -- ── 2) PURGE : l'objet reel est LA, ou plus rien ne viendra ───────────────
  -- (a) reconcilie : le bien / le contact existe dans la couche -> la ligne
  --     provisoire n'a plus d'objet, on l'efface sans attendre.
  delete from app_annonce_provisional p
   where p.status = 'linked'
     and exists (select 1 from app_dossier_current d
                  where d.hektor_annonce_id::text = p.hektor_annonce_id::text);

  delete from app_contact_provisional p
   where p.status = 'linked'
     and exists (select 1 from app_contact_current c
                  where c.hektor_contact_id = p.hektor_contact_id
                     or c.hektor_target_id  = p.hektor_contact_id);

  -- (b) le filet : passe 24 h, le run de nuit est passe. Ce qui n'est toujours
  --     pas reconcilie ne le sera jamais (objet supprime chez Hektor, essai
  --     abandonne...). Vaut pour les quatre tables, y compris la recherche et
  --     la relation, qui n'ont pas de cle simple a rapprocher de la couche.
  delete from app_annonce_provisional  where status = 'linked' and updated_at < now() - interval '24 hours';
  delete from app_contact_provisional  where status = 'linked' and updated_at < now() - interval '24 hours';
  delete from app_search_provisional   where status = 'linked' and updated_at < now() - interval '24 hours';
  delete from app_relation_provisional where status = 'linked' and updated_at < now() - interval '24 hours';

  -- (c) les erreurs anciennes : l'utilisateur a eu le temps de les voir.
  delete from app_annonce_provisional  where status = 'error' and updated_at < now() - interval '24 hours';
  delete from app_contact_provisional  where status = 'error' and updated_at < now() - interval '24 hours';
  delete from app_search_provisional   where status = 'error' and updated_at < now() - interval '24 hours';
  delete from app_relation_provisional where status = 'error' and updated_at < now() - interval '24 hours';
end;
$function$;

-- ── Controle : les deux empreintes sont bien revenues ────────────────────────
DO $$
DECLARE v_vue text; v_fn text; v_acl text;
BEGIN
  SELECT md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''))
    INTO v_vue;
  IF v_vue <> 'e2c015e16d1339fee080b6b2cc7bcb2b' THEN
    RAISE EXCEPTION 'STOP : la vue n''est pas revenue a son etat 4a (empreinte %)', v_vue;
  END IF;
  SELECT md5(replace(pg_get_functiondef(p.oid), chr(13), '')) INTO v_fn
    FROM pg_proc p JOIN pg_namespace ns ON ns.oid = p.pronamespace
   WHERE ns.nspname = 'public' AND p.proname = 'app_sweep_stale_provisionals';
  IF v_fn <> '8031dd042d33e3785a27da0c4e106498' THEN
    RAISE EXCEPTION 'STOP : le balayage n''est pas revenu a son etat du 11/10 (empreinte %)', v_fn;
  END IF;
  SELECT c.relacl::text INTO v_acl FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
   WHERE ns.nspname='public' AND c.relname='app_en_attente_humain';
  IF v_acl LIKE '%anon=%' OR v_acl LIKE '%authenticated=%' THEN
    RAISE EXCEPTION 'STOP : la vue s''est rouverte a anon/authenticated (%)', v_acl;
  END IF;
END $$;

COMMIT;
