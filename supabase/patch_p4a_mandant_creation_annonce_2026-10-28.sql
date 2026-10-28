-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES §53 P4-a — LE MANDANT EXISTANT CHOISI À LA CRÉATION D'UNE ANNONCE, CHEZ NOUS AU CLIC          28/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §53 (audit) et §53.4 (code).
--
-- POURQUOI : à la création d'une annonce, le mandant choisi ne partait que dans la charge du travail ; le worker le liait
--   chez Hektor sans rien écrire chez nous, et le lien n'arrivait qu'à la nuit (à la coupure : jamais). Décision de Frédéric
--   (28/10) : « P4-a puis audit P4-b » — faire comme « lier un mandant ».
-- CE QUE CE PATCH FAIT, ET RIEN D'AUTRE (1 bloc ajouté dans la branche « l'annonce naît dans l'app » de
--   `app_create_annonce_job_optimistic`, juste après la naissance complète, avant la création du travail) :
--   chaque mandant EXISTANT de la charge (`initial_mandant_contact_ids`, sinon `initial_mandant_contact_id`) reçoit son lien
--   au bien, comme `app_link_mandant_optimistic` : `source = 'app'`, `present_in_hektor = false`, clé `app:<jeton>:<contact>`,
--   et — c'est la seule différence — rangé par NOTRE numéro de dossier, le numéro Hektor du bien encore VIDE (il n'existe pas
--   encore). Le type du mandant est recalculé aussitôt.
--   La suite est au worker (§53.4) : il pose le numéro Hektor sur ces liens en même temps que sur la fiche du bien, les marque
--   établis quand Hektor confirme, les défait s'il refuse, et les retire de l'écran si la création échoue.
--   · Pas de traduction du contact → PAS DE LIGNE (comme `link_mandant` : mieux vaut pas de ligne qu'une ligne fausse).
--   · BEST-EFFORT, comme `link_mandant`, mais DIT (WARNING) : rien ici ne fait échouer la création.
--   · L'autre branche (interrupteur `c9_annonce_nait_dans_app` éteint) n'est pas touchée.
-- ⚠ ① ci-dessous : `app_relation.hektor_annonce_id` était NOT NULL chez Supabase — l'essai du 28/10 l'a trouvé (le lien était
--   refusé, et dit par le WARNING). Le patch le rend facultatif.
-- ⚠ Le mandant NEUF (`initial_mandant`) n'est pas concerné : il n'existe pas encore chez nous au clic (P4-b, à auditer).
-- Le bloc vérifie l'empreinte de la fonction (celle du 21/10, 8a pièce 2) et S'ARRÊTE si elle a changé.
-- Retour arrière : patch_p4a_mandant_creation_annonce_2026-10-28_INVERSE.sql
-- Contrôle       : patch_p4a_mandant_creation_annonce_2026-10-28_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- ① LE LIEN PEUT ATTENDRE SON NUMÉRO HEKTOR DE BIEN. Chez Supabase seulement : la base locale (phase2.sqlite) ne reçoit
--    jamais une telle ligne — sa nuit n'adopte un lien du cloud que s'il a un numéro de bien (relation_ledger, `cle_sb[1]`),
--    et sa copie `app_relation__sb` accepte déjà le vide. L'unicité (contact, bien) laisse passer un bien vide.
--    Mesuré le 28/10 avant la pose : 0 ligne sans numéro de bien (la contrainte le garantissait).
ALTER TABLE public.app_relation ALTER COLUMN hektor_annonce_id DROP NOT NULL;

DO $p$
DECLARE
    d     text := pg_get_functiondef('public.app_create_annonce_job_optimistic(uuid,jsonb,jsonb,integer)'::regprocedure);
    -- ⚠ ancre sur UNE SEULE LIGNE (leçon 30)
    ancre text := '  -- === fin 8a piece 2 ===';
    bloc  text := E'\n\n  -- @P4a-debut (28/10/2026, types §53) : le mandant EXISTANT choisi a la creation, chez nous au clic.\n'
        || E'  declare\n'
        || E'    v_p4_ids     text[];\n'
        || E'    v_p4_id      text;\n'
        || E'    v_p4_app     bigint;\n'
        || E'    v_p4_hektor  text;\n'
        || E'    v_p4_poses   text[] := ''{}'';\n'
        || E'  begin\n'
        || E'    v_p4_ids := array(\n'
        || E'      select distinct nullif(trim(e), '''')\n'
        || E'        from jsonb_array_elements_text(case\n'
        || E'               when jsonb_typeof(draft_payload->''initial_mandant_contact_ids'') = ''array''\n'
        || E'                 then draft_payload->''initial_mandant_contact_ids''\n'
        || E'               else jsonb_build_array(coalesce(draft_payload->>''initial_mandant_contact_id'', '''')) end) as e\n'
        || E'       where nullif(trim(e), '''') is not null);\n'
        || E'    foreach v_p4_id in array v_p4_ids loop\n'
        || E'      v_p4_app := null; v_p4_hektor := null;\n'
        || E'      select c.hektor_contact_id::bigint, c.hektor_target_id into v_p4_app, v_p4_hektor\n'
        || E'        from public.app_contact_current c\n'
        || E'       where c.hektor_contact_id = v_p4_id or c.hektor_target_id = v_p4_id\n'
        || E'       limit 1;\n'
        || E'      if v_p4_app is not null and v_p4_app >= 10000000 then\n'
        || E'        insert into public.app_relation\n'
        || E'          (app_relation_id, app_contact_id, app_dossier_id, hektor_annonce_id, hektor_contact_id,\n'
        || E'           fait, role_hektor, source, relation_key, first_seen_at, last_seen_at, present_in_hektor, absent_depuis)\n'
        || E'        values\n'
        || E'          (nextval(''public.app_relation_id_app_seq''), v_p4_app, v_id, null,\n'
        || E'           coalesce(v_p4_hektor, case when v_p4_id ~ ''^[0-9]+$'' and v_p4_id::bigint < 10000000 then v_p4_id end),\n'
        || E'           ''proprietaire_du_bien'', null, ''app'', ''app:'' || p_token::text || '':'' || v_p4_app::text,\n'
        || E'           now()::text, now()::text, false, null);\n'
        || E'        v_p4_poses := v_p4_poses || v_p4_app::text;\n'
        || E'      end if;\n'
        || E'    end loop;\n'
        || E'    if cardinality(v_p4_poses) > 0 then\n'
        || E'      perform public.app_recalculer_type_contacts(v_p4_poses);\n'
        || E'    end if;\n'
        || E'  exception when others then\n'
        || E'    raise warning ''P4-a : lien du mandant choisi a la creation non pose pour % (%)'', v_id, sqlerrm;\n'
        || E'  end;\n'
        || E'  -- @P4a-fin';
    n int;
BEGIN
    IF md5(d) <> 'a5e70b5734876f74ecd0083681a1ebe8' THEN
        RAISE EXCEPTION '%', format('ARRET : app_create_annonce_job_optimistic a change depuis l''audit du 28/10 (empreinte %s au lieu de a5e70b57...) ; rien n''est ecrit.', md5(d));
    END IF;
    n := (length(d) - length(replace(d, ancre, ''))) / length(ancre);
    IF n <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre est trouvee %s fois (1 attendue) ; rien n''est ecrit.', n);
    END IF;
    EXECUTE replace(d, ancre, ancre || bloc);
END
$p$;

COMMIT;
