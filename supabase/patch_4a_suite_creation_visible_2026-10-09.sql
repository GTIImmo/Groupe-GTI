-- =====================================================================
-- CHANTIER ④ · POINT 4a -- LA SUITE D'UNE CREATION QUI RATE DEVIENT VISIBLE
-- Date : 2026-10-09 · Detail : notice/CHANTIER_4_ECHECS_SILENCIEUX_2026-10-09.md
--
-- LE PROBLEME. La creation d'une annonce fait TROIS choses : creer chez Hektor,
-- remplir la fiche (167 champs), rattacher le mandant. Les deux dernieres sont
-- attrapees par un `catch` dans le worker -- a raison -- et le travail CONTINUE :
-- il finit donc « done ». Personne n'est prevenu, rien n'est rejoue, et le seul
-- lecteur du compte rendu est un script d'inventaire hors ligne.
-- Mesure du 09/10 sur les 79 creations : 3 fiches perdues EN ENTIER (07/06, 07/07,
-- 08/07 -- aucune ligne « running » au journal : rien n'avait ete envoye) et
-- 1 faux negatif de mandant (28/08, le lien existe : app_relation 107234).
-- Les quatre causes ont ete bouchees depuis (09/06, 10/07, 31/08) ; ce qui reste,
-- c'est LE SILENCE -- la quatrieme cause, on ne la connait pas encore.
--
-- LE CORRECTIF, ADDITIF. On garde la vue mot pour mot et on lui ajoute une SECONDE
-- branche `UNION ALL` : les creations « done » dont le compte rendu porte un echec.
-- La sentinelle `data.geste_abandonne` (seuil 0, monitoring/check_gti_health.py:342)
-- les voit alors SANS AUCUNE LIGNE DE CODE EN PLUS -- pas de nouvelle sentinelle.
-- L'autre moitie du point 4a est dans le worker (avertissement au negociateur,
-- interrupteur CONSOLE_ALERTE_SUITE_CREATION) : elle est independante de ce patch.
--
-- ⚠ ON NE FAIT PAS TOMBER LE TRAVAIL, et c'est voulu : l'annonce EXISTE deja chez
--   Hektor. La decision du 22/09 (commit a19d9c5) refuse de faire retomber le lot ;
--   l'enveloppe ...WithProvisional afficherait « Erreur de creation » sur une
--   annonce bien creee ; et rejouer une CREATION la DOUBLERAIT (regle C.4-bis).
--   `create_hektor_draft_annonce` est d'ailleurs absent de `types_rejouables`.
--
-- CE QUI NE CHANGE PAS (verifie, voir la note du chantier) :
--   · LES 7 COLONNES, leur ordre et leurs types -> le `sample` du moniteur
--     (objet, reference, libelle, cause) lit exactement pareil ;
--   · la branche existante : copiee au caractere pres, aucune condition touchee ;
--   · `objet = 'geste'` dans la branche neuve -> le mecanisme « c'est traite »
--     (app_pending_resolution, objet='geste' + payload_json->>'job_id') marche
--     a l'identique sur les nouvelles lignes ;
--   · le chantier ① : `create or replace view` CONSERVE l'ACL de la vue
--     (postgres + service_role ; anon et authenticated ont ete retires le 08/10)
--     et ses reloptions (vides). Ce patch ne fait JAMAIS `drop view`.
--   · LA SENTINELLE RESTE VERTE AUJOURD'HUI : la branche neuve rend 4 lignes au
--     total, mais 0 sur les 30 derniers jours (mesure du 09/10, lecture seule).
--   · le front, le worker, le run de nuit, les crons, phase2, les pages publiques :
--     aucun ne lit cette vue (grep complet du depot : un seul lecteur, le moniteur).
--
-- RETOUR ARRIERE : supabase/patch_4a_suite_creation_visible_2026-10-09_INVERSE.sql
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='60s';

-- ---------------------------------------------------------------------
-- 0. GARDE-FOU D'ENTREE : la base est bien celle qu'on a mesuree.
-- ---------------------------------------------------------------------
DO $$
DECLARE v_empreinte text; n int;
BEGIN
  IF to_regclass('public.app_en_attente_humain') IS NULL THEN
    RAISE EXCEPTION 'STOP : la vue app_en_attente_humain est introuvable';
  END IF;
  -- L'empreinte se compare TOUJOURS sans les retours chariot : un collage depuis
  -- Windows met le corps en CRLF et l'empreinte brute ne correspond jamais.
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

-- ---------------------------------------------------------------------
-- 1. LA VUE : branche 1 inchangee + branche 2 neuve
-- ---------------------------------------------------------------------
create or replace view public.app_en_attente_humain as
-- ── BRANCHE 1 : les gestes abandonnes (inchangee, 5 tentatives et plus) ──────
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
-- ── BRANCHE 2 (4a, 09/10/2026) : la creation a REUSSI, mais pas sa SUITE ─────
--    Le travail est « done » -- et il doit le rester : l'annonce existe chez
--    Hektor, la rejouer la doublerait. Ce qui manque est dans le compte rendu.
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

-- ---------------------------------------------------------------------
-- 2. CONTROLE DE SORTIE : les 7 colonnes et les droits sont intacts.
-- ---------------------------------------------------------------------
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

COMMIT;
