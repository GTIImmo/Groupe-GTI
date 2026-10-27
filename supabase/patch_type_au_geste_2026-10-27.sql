-- ═══════════════════════════════════════════════════════════════════════════
-- ⑧ TYPES, ÉTAPE 2 (version simple « au geste ») — LE TYPE SE CALCULE CHEZ NOUS AU GESTE         27/10/2026
-- Note : notice/AUDIT_COHERENCE_REGISTRES_ET_TYPES_DE_CONTACTS_2026-10-26.md, §43 à §45.
--
-- LE PRINCIPE (Frédéric, 27/10 : « on calcule nous-mêmes le type suite au geste ») : le type d'un contact
--   (relation_roles_json) est un RÉSUMÉ de nos registres (liens, transactions). Il se calcule donc chez nous, depuis la
--   vue des liens d'un contact, au moment où une porte de l'app change un registre -- comme les autres écritures.
--
-- CE QUE CE PATCH FAIT :
--   1. TROIS FONCTIONS (internes : seuls la base et la clé de service peuvent les appeler) :
--        app_type_depuis_nos_registres(contact)        le type depuis la vue, trié comme la nuit (COLLATE "C") ;
--        app_recalculer_type_contacts(contacts[])      l'écrit dans app_contact_current, SEULEMENT s'il change ;
--        app_recalculer_type_du_bien(annonce, dossier) le fait pour tous les contacts liés au bien (ses liens, même
--                                                      retirés, et les parties de ses transactions) ; ne fait JAMAIS
--                                                      échouer l'appelant (une erreur est notée, -1 est rendu).
--   2. UNE LIGNE dans chacune des 6 PORTES qui changent un rôle (§43.2), juste avant leur sortie finale :
--        app_link_mandant_optimistic, app_create_mandant_contact_optimistic, app_unlink_mandant_optimistic,
--        app_change_annonce_status_optimistic, app_geste_affaire_optimistic, app_modifier_affaire_optimistic.
--      Chaque porte vérifie son empreinte et l'ancre d'UNE ligne (leçon 30) ; elle garde ses droits et SECURITY DEFINER.
-- ⚠ PAS DANS CE PATCH (leurs propres pas) : la nuit qui n'écrit plus le type, et les 3 retours arrière du worker.
--   Tant qu'ils ne sont pas posés, la nuit continue de réécrire le type -- avec le même résultat pour 62 332 contacts
--   sur 62 339 (§34.2) : sans dommage.
-- ⛔ RIEN CHEZ HEKTOR. Le patch n'écrit dans aucune table : seules les fonctions, à leur appel, écrivent le type.
-- Retour arrière : patch_type_au_geste_2026-10-27_INVERSE.sql · Contrôle : _REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- ── 1. LES TROIS FONCTIONS ─────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.app_type_depuis_nos_registres(p_contact text)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $f$
    -- ⚠ COLLATE "C" : la nuit trie les rôles octet par octet (Python, sorted()) ; la base trie en en_US.
    SELECT coalesce(jsonb_agg(x.r ORDER BY x.r COLLATE "C"), '[]'::jsonb)
      FROM (SELECT DISTINCT v.role_contact AS r
              FROM public.app_contact_relations_current v
             WHERE v.hektor_contact_id = p_contact) x;
$f$;

CREATE OR REPLACE FUNCTION public.app_recalculer_type_contacts(p_contacts text[])
RETURNS integer LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $f$
DECLARE n integer := 0;
BEGIN
    IF p_contacts IS NULL OR cardinality(p_contacts) = 0 THEN RETURN 0; END IF;
    -- n'écrit QUE si le type change ; ne touche ni à refreshed_at ni à la cible (déclencheurs de la table)
    UPDATE public.app_contact_current k
       SET relation_roles_json = t.roles
      FROM (SELECT c, public.app_type_depuis_nos_registres(c) AS roles
              FROM (SELECT DISTINCT unnest(p_contacts) AS c) u WHERE c IS NOT NULL) t
     WHERE k.hektor_contact_id = t.c
       AND k.relation_roles_json IS DISTINCT FROM t.roles;
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END
$f$;

CREATE OR REPLACE FUNCTION public.app_recalculer_type_du_bien(p_hektor_annonce_id text, p_app_dossier_id bigint DEFAULT NULL)
RETURNS integer LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $f$
DECLARE
    v_ann      text := nullif(btrim(coalesce(p_hektor_annonce_id, '')), '');
    v_contacts text[];
BEGIN
    IF v_ann IS NULL AND p_app_dossier_id IS NOT NULL THEN
        SELECT d.hektor_annonce_id::text INTO v_ann FROM public.app_dossier_current d WHERE d.app_dossier_id = p_app_dossier_id;
    END IF;
    IF v_ann IS NULL OR v_ann !~ '^[0-9]+$' THEN RETURN 0; END IF;
    SELECT array_agg(DISTINCT x.c) INTO v_contacts FROM (
        SELECT r.app_contact_id_texte AS c FROM public.app_relation r WHERE r.hektor_annonce_id = v_ann
        UNION
        SELECT p.app_contact_id_texte FROM public.app_affaire_partie p
          JOIN public.app_affaire_ledger l ON l.app_affaire_id = p.app_affaire_id
         WHERE l.hektor_annonce_id = v_ann::bigint AND p.app_contact_id IS NOT NULL) x
     WHERE x.c IS NOT NULL;
    RETURN public.app_recalculer_type_contacts(v_contacts);
EXCEPTION WHEN OTHERS THEN
    -- ⛔ JAMAIS faire échouer le geste pour le type : on le note, la nuit rattrapera.
    RAISE WARNING 'app_recalculer_type_du_bien(%) : %', v_ann, SQLERRM;
    RETURN -1;
END
$f$;

REVOKE ALL ON FUNCTION public.app_type_depuis_nos_registres(text) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.app_recalculer_type_contacts(text[]) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.app_recalculer_type_du_bien(text, bigint) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.app_type_depuis_nos_registres(text) TO service_role;
GRANT EXECUTE ON FUNCTION public.app_recalculer_type_contacts(text[]) TO service_role;
GRANT EXECUTE ON FUNCTION public.app_recalculer_type_du_bien(text, bigint) TO service_role;

-- ── 2. UNE LIGNE DANS CHACUNE DES 6 PORTES ─────────────────────────────────
DO $portes$
DECLARE
    marque text := '  -- ⑧ ÉTAPE 2 (27/10/2026) : LE TYPE SE CALCULE CHEZ NOUS AU GESTE (note des types §45).' || chr(10);
    p record;
    f text;
    n int;
BEGIN
    FOR p IN SELECT * FROM (VALUES
        ('app_link_mandant_optimistic',           '22b3c52700ff323b773e477382022779', '  return created_job;',
         '  perform public.app_recalculer_type_du_bien(target_hektor_annonce_id, target_app_dossier_id);'),
        ('app_create_mandant_contact_optimistic', '04a25df1327d4b7b19413a757f861aeb', '  return created_job;',
         '  perform public.app_recalculer_type_du_bien(target_hektor_annonce_id, target_app_dossier_id);'),
        ('app_unlink_mandant_optimistic',         '3469d98941d345d6abd58afb39f25db2', '  return created_job;',
         '  perform public.app_recalculer_type_du_bien(target_hektor_annonce_id, target_app_dossier_id);'),
        ('app_change_annonce_status_optimistic',  '93be71b41e9ff172de9e8c3e261233a5', '  return jsonb_build_object(''job_id'', v_job_id,',
         '  perform public.app_recalculer_type_du_bien(d.hektor_annonce_id::text, target_dossier_id);'),
        ('app_modifier_affaire_optimistic',       '910e79470819a1111d21b608625f95b8', '  return jsonb_build_object(''ok'', true,',
         '  perform public.app_recalculer_type_du_bien(a.hektor_annonce_id::text, a.app_dossier_id);'),
        -- ⚠ « Supprimer » a aussi une sortie PRÉCOCE (« déjà dans cet état », 4 espaces, sur une ligne) : l'ancre vise la
        --   sortie FINALE, seule à porter « ( » en fin de ligne.
        ('app_geste_affaire_optimistic',          '89d5399db696e004ba5cc59454e1c75a', '  RETURN jsonb_build_object(' || chr(10),
         '  PERFORM public.app_recalculer_type_du_bien(a.hektor_annonce_id::text, a.app_dossier_id);')
    ) x(nom, empreinte, ancre, ligne) LOOP
        SELECT pg_get_functiondef(pr.oid) INTO f FROM pg_proc pr JOIN pg_namespace s ON s.oid = pr.pronamespace
         WHERE s.nspname = 'public' AND pr.proname = p.nom;
        IF position('app_recalculer_type_du_bien' in f) > 0 THEN
            RAISE NOTICE '%', p.nom || ' porte deja la ligne : rien a faire.';
            CONTINUE;
        END IF;
        IF md5(f) <> p.empreinte THEN
            RAISE EXCEPTION '%', format('ARRET : %s a change depuis l''audit du 27/10 (empreinte %s au lieu de %s) ; tout est annule.', p.nom, md5(f), p.empreinte);
        END IF;
        -- ⚠ ON NE RETIRE PAS les CR : 2 portes (rattacher, retirer) ont un corps en fins de ligne Windows ; les retirer
        --   changerait tout le corps et l'inverse ne retrouverait plus l'empreinte (essai du 27/10). L'ancre tient sur une ligne.
        n := (length(f) - length(replace(f, p.ancre, ''))) / length(p.ancre);
        IF n <> 1 THEN
            RAISE EXCEPTION '%', format('ARRET : dans %s, l''ancre est trouvee %s fois (1 attendue) ; tout est annule.', p.nom, n);
        END IF;
        EXECUTE replace(f, p.ancre, marque || p.ligne || chr(10) || p.ancre);
    END LOOP;
END
$portes$;

COMMIT;
