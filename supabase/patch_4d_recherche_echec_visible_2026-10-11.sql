-- =====================================================================
-- CHANTIER ④ · POINT 4d -- UNE RECHERCHE CREEE EN ECHEC SE VOIT, ET DURE
-- Date : 2026-10-11 · Detail : notice/CHANTIER_4_ECHECS_SILENCIEUX_2026-10-09.md
--
-- LE PROBLEME, MESURE LE 11/10. Une creation de recherche qui rate s'affiche
-- « Erreur de creation » pendant 24 h, puis la ligne provisoire est EFFACEE --
-- branche (c) du balayage, justifiee ainsi dans le code : « les erreurs
-- anciennes : l'utilisateur a eu le temps de les voir ». Cette premisse est
-- FAUSSE si le negociateur est absent deux jours. Et PERSONNE ne compte ces
-- echecs : ni sentinelle, ni alerte, ni bouton « reessayer ».
--   ⭐ Rien n'est physiquement perdu : les criteres vivent EN ENTIER dans la
--     charge du travail (payload_json->search) et les travaux ne sont jamais
--     purges (91 609 conserves). La saisie devient INVISIBLE, pas detruite.
--   0 cas reel : les 4 travaux add_hektor_contact_search sont tous « done ».
--
-- CE PATCH FAIT DEUX CHOSES, decidees par Frederic le 11/10 (« A et b ») :
--   A. ON COMPTE   -- 4e branche de app_en_attente_humain. La sentinelle
--      `geste_abandonne` (seuil 0) sonne seule, sans une ligne de code en plus.
--   B. ON LAISSE PLUS DE TEMPS -- la purge des ERREURS passe de 24 h a 7 JOURS.
--
-- ⚠⚠ PERIMETRE DE B, A LIRE AVANT DE COLLER. La branche (c) traite les QUATRE
--    tables provisoires d'un seul geste (annonce, contact, recherche, lien) et
--    sa justification est la MEME pour les quatre. Je passe donc les quatre a
--    7 jours. Si tu ne veux QUE la recherche, dis-le : c'est une ligne a retirer.
--    Volume en jeu : AUCUN (0 ligne 'error' aujourd'hui, sur les 4 tables).
--
-- A : LA COUPURE EST L'ETAT DU TRAVAIL, JAMAIS L'HORLOGE (regle de 4c, nee
--     d'une question de Frederic). Mesure du 11/10 : l'attente normale d'une
--     creation peut atteindre 44 MINUTES, file comprise -- tout delai aurait
--     sonne faux. Ici : le travail `add_hektor_contact_search` est en `error`.
--     `pending` / `running` / `done` -> on se tait.
--
-- CE QUI NE CHANGE PAS (verifie, voir la note du chantier) :
--   · LES 7 COLONNES de la vue, leur ordre et leurs types -> le `sample` du
--     moniteur (objet, reference, libelle, cause) lit exactement pareil ;
--   · les branches 1 (gestes abandonnes), 2 (suite de creation, 4a) et 3 : elles
--     sont recopiees au caractere pres, aucune condition touchee ;
--   · `objet = 'geste'` dans la branche neuve -> le mecanisme « c'est traite »
--     (app_pending_resolution) marche a l'identique ;
--   · le 15 MINUTES qui rend l'erreur VISIBLE n'est pas touche. Mesure : le bout
--     en bout d'une recherche plafonne a 32 s, soit 28 fois de marge ;
--   · le chantier ① : `create or replace` CONSERVE l'ACL de la vue
--     (postgres + service_role) et de la fonction. Jamais de `drop`.
--   · le front, le worker, le run de nuit, phase2, les pages publiques :
--     aucun ne lit cette vue (un seul lecteur : monitoring/check_gti_health.py).
--   · LA SENTINELLE RESTE VERTE AUJOURD'HUI : 0 travail de recherche en erreur,
--     depuis toujours.
--
-- RETOUR ARRIERE : supabase/patch_4d_recherche_echec_visible_2026-10-11_INVERSE.sql
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='60s';

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

COMMIT;
