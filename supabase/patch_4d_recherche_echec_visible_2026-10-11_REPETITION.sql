-- =====================================================================
-- REPETITION DU PATCH 4d -- N'ECRIT RIEN, TOUT EST ANNULE A LA FIN
-- Date : 2026-10-11  ·  ASSEMBLEE depuis les deux vrais fichiers de patch
--                       (generateur : scratchpad/faire_repetition_4d.py)
--
-- Elle joue LE VRAI patch, puis LE VRAI retour arriere, mesure tout au passage,
-- et finit par une ERREUR VOLONTAIRE qui annule la transaction entiere.
-- A coller dans l'editeur SQL :
--   https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
-- Puis me recopier le message. Il doit dire, dans cet ordre :
--
--   ESSAI ANNULE -- 4d
--   vue_empreinte_avant=e2c015e16d1339fee080b6b2cc7bcb2b
--   balayage_empreinte_avant=8031dd042d33e3785a27da0c4e106498
--   vue_lignes_avant=0   colonnes_avant=7
--   acl_avant={postgres=arwdDxtm/postgres,service_role=arwdDxtm/postgres}
--   vue_empreinte_apres=<NOUVELLE, a noter : elle devient la reference>
--   balayage_empreinte_apres=<NOUVELLE, a noter>
--   vue_lignes_apres=0  branche3_apres=0  colonnes_apres=7  acl_apres=IDENTIQUE
--   erreurs_a_7_jours=4   linked_a_24h=4   visible_a_15min=4
--      <- B a bien change LA SEULE branche voulue : 4 erreurs a 7 jours, et les
--         4 purges « linked » comme les 4 passages a 15 min n'ont PAS bouge
--   branche3_sans_fenetre=0
--      <- normal : AUCUN travail de recherche n'a jamais echoue
--   plomberie_si_erreur=4
--      <- LA PREUVE que la branche TROUVE : meme requete, meme extraction des
--         criteres, mais en visant les travaux « done » -- elle en trouve 4
--   exemple=contact 605... -> recherche 120000 a 250000 EUR
--   vue_empreinte_retour=e2c015e16d1339fee080b6b2cc7bcb2b      (identique a avant)
--   balayage_empreinte_retour=8031dd042d33e3785a27da0c4e106498 (identique a avant)
--   acl_retour=IDENTIQUE
--
-- Si UN seul chiffre differe, on ne colle pas le vrai patch.
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='120s';

CREATE TEMP TABLE mesures_4d (ordre int, cle text, valeur text) ON COMMIT DROP;

-- ---------------------------------------------------------------------
-- A. AVANT
-- ---------------------------------------------------------------------
INSERT INTO mesures_4d SELECT 1, 'vue_empreinte_avant',
       md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''));
INSERT INTO mesures_4d SELECT 2, 'balayage_empreinte_avant',
       (SELECT md5(replace(pg_get_functiondef(p.oid), chr(13), '')) FROM pg_proc p
          JOIN pg_namespace ns ON ns.oid = p.pronamespace
         WHERE ns.nspname='public' AND p.proname='app_sweep_stale_provisionals');

INSERT INTO mesures_4d SELECT 3, 'vue_lignes_avant', count(*)::text FROM app_en_attente_humain;
INSERT INTO mesures_4d SELECT 4, 'colonnes_avant', count(*)::text FROM information_schema.columns
 WHERE table_name='app_en_attente_humain'
   AND column_name IN ('objet','reference','libelle','nature','cause','tentatives','depuis');
INSERT INTO mesures_4d SELECT 5, 'acl_avant', coalesce(c.relacl::text,'(vide)')
 FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
 WHERE ns.nspname='public' AND c.relname='app_en_attente_humain';

-- =====================================================================
-- B. LE VRAI PATCH (assemble depuis le fichier, non recopie)
-- =====================================================================
-- ---------------------------------------------------------------------
-- 0. GARDE-FOU D'ENTREE : la base est bien celle qu'on a mesuree.
--    L'empreinte se compare TOUJOURS sans les retours chariot (un collage
--    depuis Windows met le corps en CRLF).
-- ---------------------------------------------------------------------
DO $$
DECLARE v_vue text; v_fn text; n int;
BEGIN
  IF to_regclass('public.app_en_attente_humain') IS NULL THEN
    RAISE EXCEPTION 'STOP : la vue app_en_attente_humain est introuvable';
  END IF;
  SELECT md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''))
    INTO v_vue;
  IF v_vue <> 'e2c015e16d1339fee080b6b2cc7bcb2b' THEN
    RAISE EXCEPTION 'STOP : la vue n''est plus celle du patch 4a (empreinte %) -- une autre session est passee', v_vue;
  END IF;
  SELECT md5(replace(pg_get_functiondef(p.oid), chr(13), '')) INTO v_fn
    FROM pg_proc p JOIN pg_namespace ns ON ns.oid = p.pronamespace
   WHERE ns.nspname = 'public' AND p.proname = 'app_sweep_stale_provisionals';
  IF v_fn IS NULL THEN
    RAISE EXCEPTION 'STOP : app_sweep_stale_provisionals est introuvable';
  END IF;
  IF v_fn <> '8031dd042d33e3785a27da0c4e106498' THEN
    RAISE EXCEPTION 'STOP : le balayage n''est plus celui mesure le 11/10 (empreinte %)', v_fn;
  END IF;
  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_name = 'app_en_attente_humain'
     AND column_name IN ('objet','reference','libelle','nature','cause','tentatives','depuis');
  IF n <> 7 THEN RAISE EXCEPTION 'STOP : la vue n''a pas ses 7 colonnes (%)', n; END IF;
END $$;

-- ---------------------------------------------------------------------
-- A. LA VUE : branches 1 et 2 inchangees + branche 3 neuve
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
          WHERE r.objet = 'geste'::text AND (r.payload_json ->> 'job_id'::text) = j.id::text))
-- ── BRANCHE 3 (4d, 11/10/2026) : UNE RECHERCHE CREEE EN ECHEC ────────────────
--    On tranche sur l'ETAT DU TRAVAIL, jamais sur l'horloge (regle de 4c).
--    La ligne provisoire, elle, sera effacee (7 jours apres le patch B) -- mais
--    le travail reste, avec les criteres saisis : on les redonne ici, pour que
--    le negociateur n'ait pas a les retrouver de memoire.
UNION ALL
 SELECT 'geste'::text AS objet,
    COALESCE('contact '::text || NULLIF(COALESCE(j.payload_json ->> 'hektor_contact_id',
                                                 j.payload_json ->> 'contact_id'), ''::text),
             'sans contact'::text) AS reference,
    'recherche ' || COALESCE(NULLIF(j.payload_json -> 'search' ->> 'priceMin', ''), '?')
                 || ' a ' || COALESCE(NULLIF(j.payload_json -> 'search' ->> 'priceMax', ''), '?')
                 || ' EUR' AS libelle,
    'recherche creee en echec'::text AS nature,
    (j.job_type || ' : '::text) || "left"(COALESCE(j.error_message, 'sans message'::text), 90) AS cause,
    COALESCE(j.attempt_count, 0) AS tentatives,
    j.updated_at AS depuis
   FROM app_console_job j
  WHERE j.job_type = 'add_hektor_contact_search'::text
    AND j.status = 'error'::text
    AND j.requested_at > (now() - '30 days'::interval)
    AND NOT (EXISTS ( SELECT 1
           FROM app_pending_resolution r
          WHERE r.objet = 'geste'::text AND (r.payload_json ->> 'job_id'::text) = j.id::text));

COMMENT ON VIEW public.app_en_attente_humain IS
  'Ce qui attend un humain. Branche 1 : gestes abandonnes (>= 5 tentatives). '
  'Branche 2 (4a, 09/10/2026) : creation d''annonce « done » dont la SUITE a rate '
  '(champs ou mandant) -- le travail reste done a dessein, l''annonce existe chez Hektor. '
  'Branche 3 (4d, 11/10/2026) : recherche creee en echec -- on tranche sur l''etat du '
  'travail, jamais sur l''horloge, et on redonne les criteres saisis. '
  'Se solde dans app_pending_resolution (objet=geste, payload_json->>job_id).';

-- ---------------------------------------------------------------------
-- B. LE BALAYAGE : les ERREURS durent 7 JOURS au lieu de 24 h
--    Tout le reste est recopie AU CARACTERE PRES depuis la version du 11/10 :
--    les 4 passages a « erreur visible » apres 15 min, la purge (a) des
--    reconcilies, et la purge (b) des 'linked' a 24 h. SEULE la branche (c)
--    change, et seulement sa duree.
-- ---------------------------------------------------------------------
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

  -- (c) les erreurs anciennes.
  --     ⚠ 4d (11/10/2026) -- 24 HEURES DEVIENNENT 7 JOURS, decide par Frederic.
  --     La phrase d'origine disait « l'utilisateur a eu le temps de les voir » :
  --     c'est FAUX s'il est absent deux jours, et la saisie disparaissait alors
  --     de l'ecran sans que personne ne l'ait jamais comptee. 7 jours couvrent
  --     un week-end et une absence courte. Rien n'est perdu pour autant : les
  --     criteres restent dans la charge du travail, que rien ne purge, et la
  --     branche 3 de app_en_attente_humain les redonne.
  delete from app_annonce_provisional  where status = 'error' and updated_at < now() - interval '7 days';
  delete from app_contact_provisional  where status = 'error' and updated_at < now() - interval '7 days';
  delete from app_search_provisional   where status = 'error' and updated_at < now() - interval '7 days';
  delete from app_relation_provisional where status = 'error' and updated_at < now() - interval '7 days';
end;
$function$;

-- ---------------------------------------------------------------------
-- 3. CONTROLE DE SORTIE : colonnes, droits, et les 7 jours bien poses.
-- ---------------------------------------------------------------------
DO $$
DECLARE n int; v_acl text; v_src text;
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

  SELECT p.prosrc INTO v_src FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
   WHERE ns.nspname='public' AND p.proname='app_sweep_stale_provisionals';
  -- 4 erreurs a 7 jours, et les 4 'linked' toujours a 24 h : on ne s'est pas
  -- trompe de branche.
  IF (length(v_src) - length(replace(v_src, '''7 days''', ''))) / length('''7 days''') <> 4 THEN
    RAISE EXCEPTION 'STOP : le balayage ne porte pas exactement 4 fois « 7 days »';
  END IF;
  IF (length(v_src) - length(replace(v_src, '''24 hours''', ''))) / length('''24 hours''') <> 4 THEN
    RAISE EXCEPTION 'STOP : les 4 purges « linked » a 24 h ont bouge, ce n''etait pas voulu';
  END IF;
  IF (length(v_src) - length(replace(v_src, '''15 minutes''', ''))) / length('''15 minutes''') <> 4 THEN
    RAISE EXCEPTION 'STOP : les 4 passages a « erreur visible » apres 15 min ont bouge';
  END IF;
END $$;

-- ---------------------------------------------------------------------
-- C. APRES LE PATCH
-- ---------------------------------------------------------------------
INSERT INTO mesures_4d SELECT 6, 'vue_empreinte_apres',
       md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''));
INSERT INTO mesures_4d SELECT 7, 'balayage_empreinte_apres',
       (SELECT md5(replace(pg_get_functiondef(p.oid), chr(13), '')) FROM pg_proc p
          JOIN pg_namespace ns ON ns.oid = p.pronamespace
         WHERE ns.nspname='public' AND p.proname='app_sweep_stale_provisionals');

INSERT INTO mesures_4d SELECT 8, 'vue_lignes_apres', count(*)::text FROM app_en_attente_humain;
INSERT INTO mesures_4d SELECT 9, 'branche3_apres', count(*)::text FROM app_en_attente_humain
 WHERE nature = 'recherche creee en echec';
INSERT INTO mesures_4d SELECT 10, 'colonnes_apres', count(*)::text FROM information_schema.columns
 WHERE table_name='app_en_attente_humain'
   AND column_name IN ('objet','reference','libelle','nature','cause','tentatives','depuis');
INSERT INTO mesures_4d
SELECT 11, 'acl_apres',
       CASE WHEN coalesce(c.relacl::text,'(vide)') = (SELECT valeur FROM mesures_4d WHERE cle='acl_avant')
            THEN 'IDENTIQUE' ELSE 'DIFFERENTE : ' || coalesce(c.relacl::text,'(vide)') END
 FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
 WHERE ns.nspname='public' AND c.relname='app_en_attente_humain';

-- B a-t-il change LA SEULE branche voulue ?
INSERT INTO mesures_4d
SELECT 12, 'erreurs_a_7_jours',
       ((length(p.prosrc) - length(replace(p.prosrc, '''7 days''', ''))) / length('''7 days'''))::text
  FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
 WHERE ns.nspname='public' AND p.proname='app_sweep_stale_provisionals';
INSERT INTO mesures_4d
SELECT 13, 'linked_a_24h',
       ((length(p.prosrc) - length(replace(p.prosrc, '''24 hours''', ''))) / length('''24 hours'''))::text
  FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
 WHERE ns.nspname='public' AND p.proname='app_sweep_stale_provisionals';
INSERT INTO mesures_4d
SELECT 14, 'visible_a_15min',
       ((length(p.prosrc) - length(replace(p.prosrc, '''15 minutes''', ''))) / length('''15 minutes'''))::text
  FROM pg_proc p JOIN pg_namespace ns ON ns.oid=p.pronamespace
 WHERE ns.nspname='public' AND p.proname='app_sweep_stale_provisionals';

-- La branche 3, sans la fenetre de 30 jours : 0, car aucune recherche n'a
-- jamais echoue. On prouve donc la PLOMBERIE autrement, juste en dessous.
INSERT INTO mesures_4d
SELECT 15, 'branche3_sans_fenetre', count(*)::text
  FROM app_console_job j
 WHERE j.job_type = 'add_hektor_contact_search' AND j.status = 'error';

-- LA PREUVE QUE LA BRANCHE TROUVE : meme requete, meme extraction des criteres,
-- mais en visant les travaux « done ». Elle doit en trouver 4.
INSERT INTO mesures_4d
SELECT 16, 'plomberie_si_erreur', count(*)::text
  FROM app_console_job j
 WHERE j.job_type = 'add_hektor_contact_search' AND j.status = 'done'
   AND NOT EXISTS (SELECT 1 FROM app_pending_resolution r
                    WHERE r.objet = 'geste' AND (r.payload_json ->> 'job_id') = j.id::text);

-- Et le texte que la sentinelle montrerait, sur un cas reel.
INSERT INTO mesures_4d
SELECT 17, 'exemple',
       COALESCE('contact ' || NULLIF(COALESCE(j.payload_json ->> 'hektor_contact_id',
                                              j.payload_json ->> 'contact_id'), ''), 'sans contact')
       || ' -> recherche ' || COALESCE(NULLIF(j.payload_json -> 'search' ->> 'priceMin', ''), '?')
       || ' a ' || COALESCE(NULLIF(j.payload_json -> 'search' ->> 'priceMax', ''), '?') || ' EUR'
  FROM app_console_job j
 WHERE j.job_type = 'add_hektor_contact_search'
 ORDER BY j.requested_at DESC LIMIT 1;

-- =====================================================================
-- D. LE VRAI RETOUR ARRIERE (assemble depuis le fichier)
-- =====================================================================
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

-- ---------------------------------------------------------------------
-- E. APRES LE RETOUR ARRIERE
-- ---------------------------------------------------------------------
INSERT INTO mesures_4d SELECT 18, 'vue_empreinte_retour',
       md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''));
INSERT INTO mesures_4d SELECT 19, 'balayage_empreinte_retour',
       (SELECT md5(replace(pg_get_functiondef(p.oid), chr(13), '')) FROM pg_proc p
          JOIN pg_namespace ns ON ns.oid = p.pronamespace
         WHERE ns.nspname='public' AND p.proname='app_sweep_stale_provisionals');

INSERT INTO mesures_4d
SELECT 20, 'acl_retour',
       CASE WHEN coalesce(c.relacl::text,'(vide)') = (SELECT valeur FROM mesures_4d WHERE cle='acl_avant')
            THEN 'IDENTIQUE' ELSE 'DIFFERENTE : ' || coalesce(c.relacl::text,'(vide)') END
 FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
 WHERE ns.nspname='public' AND c.relname='app_en_attente_humain';

-- =====================================================================
-- F. L'ERREUR VOLONTAIRE : elle annule TOUT et rend les mesures
-- =====================================================================
DO $rep$
DECLARE v_rapport text;
BEGIN
  SELECT string_agg(cle || '=' || valeur, '  ' ORDER BY ordre) INTO v_rapport FROM mesures_4d;
  RAISE EXCEPTION 'ESSAI ANNULE -- 4d  %', v_rapport;
END $rep$;

ROLLBACK;
