-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ÉTAPE 2 « au geste » : le type se calcule chez nous au geste               27/10/2026
-- Les essais RÉELS des portes (sous le compte de Frédéric, admin) sont faits dans des sous-blocs TOUJOURS annulés :
-- aucun lien, aucun travail, aucun type n'en reste.
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TEMP TABLE IF NOT EXISTS repetition_tag (n int, controle text, verdict text);
TRUNCATE repetition_tag;

DO $rep$
DECLARE
    marque text := '  -- ⑧ ÉTAPE 2 (27/10/2026) : LE TYPE SE CALCULE CHEZ NOUS AU GESTE (note des types §45).' || chr(10);
    pt record; f text; ok_portes int := 0; ok_temoins int := 0;
    diff int; echant int;
    t0 timestamptz; ms numeric; v_ann text; v_doss bigint; v_contact text; v_hektor text;
    avant jsonb; pendant jsonb; apres jsonb; ret jsonb; err text := '';
    a_id bigint; ach text;
BEGIN
    -- 1. les fonctions, et leurs droits (internes)
    INSERT INTO repetition_tag
    SELECT 1, 'les 3 fonctions existent, internes (ni anon ni authenticated), SECURITY DEFINER',
           CASE WHEN count(*) = 3 AND bool_and(pr.prosecdef)
                 AND NOT bool_or(has_function_privilege('authenticated', pr.oid, 'EXECUTE'))
                 AND NOT bool_or(has_function_privilege('anon', pr.oid, 'EXECUTE'))
                 AND bool_and(has_function_privilege('service_role', pr.oid, 'EXECUTE')) THEN 'OK' ELSE '⛔ ECHEC' END
      FROM pg_proc pr JOIN pg_namespace s ON s.oid = pr.pronamespace
     WHERE s.nspname = 'public' AND pr.proname IN ('app_type_depuis_nos_registres', 'app_recalculer_type_contacts', 'app_recalculer_type_du_bien');

    -- 2-3. les 6 portes portent la ligne ; TÉMOIN INVERSE : sans elle, chacune retrouve son empreinte d'avant
    FOR pt IN SELECT * FROM (VALUES
        ('app_link_mandant_optimistic',           '22b3c52700ff323b773e477382022779', '  perform public.app_recalculer_type_du_bien(target_hektor_annonce_id, target_app_dossier_id);'),
        ('app_create_mandant_contact_optimistic', '04a25df1327d4b7b19413a757f861aeb', '  perform public.app_recalculer_type_du_bien(target_hektor_annonce_id, target_app_dossier_id);'),
        ('app_unlink_mandant_optimistic',         '3469d98941d345d6abd58afb39f25db2', '  perform public.app_recalculer_type_du_bien(target_hektor_annonce_id, target_app_dossier_id);'),
        ('app_change_annonce_status_optimistic',  '93be71b41e9ff172de9e8c3e261233a5', '  perform public.app_recalculer_type_du_bien(d.hektor_annonce_id::text, target_dossier_id);'),
        ('app_modifier_affaire_optimistic',       '910e79470819a1111d21b608625f95b8', '  perform public.app_recalculer_type_du_bien(a.hektor_annonce_id::text, a.app_dossier_id);'),
        ('app_geste_affaire_optimistic',          '89d5399db696e004ba5cc59454e1c75a', '  PERFORM public.app_recalculer_type_du_bien(a.hektor_annonce_id::text, a.app_dossier_id);')
    ) x(nom, empreinte, ligne) LOOP
        SELECT pg_get_functiondef(pr.oid) INTO f FROM pg_proc pr JOIN pg_namespace s ON s.oid = pr.pronamespace
         WHERE s.nspname = 'public' AND pr.proname = pt.nom;
        IF position(marque || pt.ligne || chr(10) in f) > 0 THEN ok_portes := ok_portes + 1; END IF;
        IF md5(replace(f, marque || pt.ligne || chr(10), '')) = pt.empreinte THEN ok_temoins := ok_temoins + 1; END IF;
    END LOOP;
    INSERT INTO repetition_tag VALUES (2, 'les 6 portes portent la ligne, a sa place', CASE WHEN ok_portes = 6 THEN 'OK' ELSE '⛔ ECHEC (' || ok_portes || '/6)' END);
    INSERT INTO repetition_tag VALUES (3, 'TEMOIN INVERSE : sans la ligne, les 6 portes retrouvent leur empreinte d''avant', CASE WHEN ok_temoins = 6 THEN 'OK' ELSE '⛔ ECHEC (' || ok_temoins || '/6)' END);

    -- 4. le calcul rend le type de la nuit : 2 000 contacts de l'annuaire
    SELECT count(*), count(*) FILTER (WHERE public.app_type_depuis_nos_registres(k.hektor_contact_id) IS DISTINCT FROM
             (SELECT coalesce(jsonb_agg(e ORDER BY e COLLATE "C"), '[]'::jsonb) FROM jsonb_array_elements_text(k.relation_roles_json) e))
      INTO echant, diff
      FROM (SELECT hektor_contact_id, relation_roles_json FROM public.app_contact_current ORDER BY hektor_contact_id LIMIT 2000) k;
    INSERT INTO repetition_tag VALUES (4, 'le calcul rend le type de la nuit (' || echant || ' contacts, a l''ordre pres)',
        CASE WHEN diff <= 7 THEN 'OK (' || diff || ' ecart(s), connus §34.2)' ELSE '⛔ ECHEC (' || diff || ' ecarts)' END);

    -- 5. un bien chargé se recalcule vite (le geste ne doit pas attendre)
    SELECT l.hektor_annonce_id::text INTO v_ann FROM public.app_affaire_partie p JOIN public.app_affaire_ledger l ON l.app_affaire_id = p.app_affaire_id
     GROUP BY 1 ORDER BY count(DISTINCT p.app_contact_id) DESC LIMIT 1;
    t0 := clock_timestamp();
    PERFORM public.app_recalculer_type_du_bien(v_ann, NULL);
    ms := round(extract(epoch FROM clock_timestamp() - t0) * 1000);
    INSERT INTO repetition_tag VALUES (5, 'le bien le plus charge (annonce ' || v_ann || ') se recalcule en moins de 1 000 ms',
        CASE WHEN ms < 1000 THEN 'OK (' || ms || ' ms)' ELSE '⛔ ECHEC (' || ms || ' ms)' END);
    -- 6. une seconde fois : rien à écrire
    INSERT INTO repetition_tag SELECT 6, 'recalculer deux fois n''ecrit rien la seconde (on n''ecrit que si le type change)',
        CASE WHEN public.app_recalculer_type_du_bien(v_ann, NULL) = 0 THEN 'OK' ELSE '⛔ ECHEC' END;

    PERFORM set_config('request.jwt.claims', json_build_object('sub', 'd4b1685f-948b-4ce8-af15-671b94a725e6', 'role', 'authenticated')::text, true);

    -- 7. ESSAI RÉEL : RATTACHER un acheteur comme mandant d'un bien sous mandat -> « mandant » au clic
    SELECT d.app_dossier_id, d.hektor_annonce_id::text INTO v_doss, v_ann FROM public.app_dossier_current d
     WHERE nullif(btrim(coalesce(d.numero_mandat, '')), '') IS NOT NULL ORDER BY d.app_dossier_id DESC LIMIT 1;
    SELECT k.hektor_contact_id INTO v_contact FROM public.app_contact_current k
     WHERE k.relation_roles_json = '["acquereur_offre"]'::jsonb
       AND NOT EXISTS (SELECT 1 FROM public.app_relation r WHERE r.app_contact_id_texte = k.hektor_contact_id AND r.hektor_annonce_id = v_ann)
     ORDER BY k.hektor_contact_id LIMIT 1;
    avant := (SELECT relation_roles_json FROM public.app_contact_current WHERE hektor_contact_id = v_contact);
    BEGIN
        ret := to_jsonb(public.app_link_mandant_optimistic(v_doss, v_ann, v_contact, 'essai type au geste', NULL));
        pendant := (SELECT relation_roles_json FROM public.app_contact_current WHERE hektor_contact_id = v_contact);
        RAISE EXCEPTION 'annule_l_essai';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM <> 'annule_l_essai' THEN err := SQLERRM; END IF;
    WHEN OTHERS THEN err := SQLERRM;
    END;
    apres := (SELECT relation_roles_json FROM public.app_contact_current WHERE hektor_contact_id = v_contact);
    INSERT INTO repetition_tag VALUES (7, 'RATTACHER (contact ' || v_contact || ', bien ' || v_ann || ') : le type gagne « mandant » AU CLIC, puis l''essai est annule',
        CASE WHEN err = '' AND pendant @> '["mandant"]'::jsonb AND NOT avant @> '["mandant"]'::jsonb AND apres = avant
             THEN 'OK (' || avant::text || ' -> ' || pendant::text || ')' ELSE '⛔ ECHEC (' || coalesce(err, '') || ' ' || coalesce(avant::text, '-') || ' -> ' || coalesce(pendant::text, '-') || ')' END);

    -- 8. ESSAI RÉEL : SUPPRIMER une vente -> l'acheteur perd « acquereur_vente » AU CLIC
    err := '';
    SELECT l.app_affaire_id, p.app_contact_id_texte INTO a_id, ach
      FROM public.app_affaire_ledger l JOIN public.app_affaire_partie p ON p.app_affaire_id = l.app_affaire_id AND p.role = 'acquereur'
      JOIN public.app_contact_current k ON k.hektor_contact_id = p.app_contact_id_texte
     WHERE l.kind = 'vente' AND l.present_in_hektor AND btrim(coalesce(l.hektor_affaire_id, '')) <> '' AND l.app_dossier_id IS NOT NULL
       AND k.relation_roles_json = '["acquereur_vente"]'::jsonb
     ORDER BY l.app_affaire_id DESC LIMIT 1;
    avant := (SELECT relation_roles_json FROM public.app_contact_current WHERE hektor_contact_id = ach);
    BEGIN
        ret := public.app_geste_affaire_optimistic(a_id, 'supprimer', NULL);
        pendant := (SELECT relation_roles_json FROM public.app_contact_current WHERE hektor_contact_id = ach);
        RAISE EXCEPTION 'annule_l_essai';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM <> 'annule_l_essai' THEN err := SQLERRM; END IF;
    WHEN OTHERS THEN err := SQLERRM;
    END;
    apres := (SELECT relation_roles_json FROM public.app_contact_current WHERE hektor_contact_id = ach);
    INSERT INTO repetition_tag VALUES (8, 'SUPPRIMER une vente (' || a_id || ', acheteur ' || ach || ') : le type perd « acquereur_vente » AU CLIC, puis l''essai est annule',
        CASE WHEN err = '' AND NOT pendant @> '["acquereur_vente"]'::jsonb AND avant @> '["acquereur_vente"]'::jsonb AND apres = avant
             THEN 'OK (' || avant::text || ' -> ' || pendant::text || ')' ELSE '⛔ ECHEC (' || coalesce(err, '') || ' ' || coalesce(avant::text, '-') || ' -> ' || coalesce(pendant::text, '-') || ')' END);

    -- 9. une erreur du calcul ne fait pas échouer le geste (annonce absurde -> 0, pas d'exception)
    INSERT INTO repetition_tag SELECT 9, 'une annonce absurde ne fait pas echouer l''appelant',
        CASE WHEN public.app_recalculer_type_du_bien('pas-un-numero', NULL) = 0 THEN 'OK' ELSE '⛔ ECHEC' END;
END
$rep$;

-- 10. rien n'est resté des essais
INSERT INTO repetition_tag
SELECT 10, 'les essais n''ont rien laisse (aucun lien d''essai, aucun travail de rattachement ou de suppression recent)',
       CASE WHEN (SELECT count(*) FROM public.app_relation_provisional WHERE contact_label = 'essai type au geste') = 0
             AND (SELECT count(*) FROM public.app_console_job WHERE job_type IN ('link_hektor_mandant', 'delete_hektor_vente') AND requested_at > now() - interval '5 minutes') = 0
            THEN 'OK' ELSE '⛔ ECHEC' END;

-- 11. LA RÈGLE POUR LES PORTES DE DEMAIN (leçon « une règle à part doit être appelée par chaque porte ») :
--     toute fonction qui écrit un lien ou une transaction appelle le recalcul, SAUF celles DÉCLARÉES ici
--     (elles ne changent aucun rôle : montants, chaînes, champs ; ou elles tiennent la table des parties).
INSERT INTO repetition_tag
SELECT 11, 'toute fonction qui ecrit un lien ou une transaction appelle le recalcul (sauf les 5 declarees)',
       CASE WHEN count(*) = 0 THEN 'OK' ELSE '⛔ ECHEC (' || string_agg(pr.proname, ', ') || ')' END
  FROM pg_proc pr JOIN pg_namespace s ON s.oid = pr.pronamespace
 WHERE s.nspname = 'public'
   AND (pr.prosrc ~* '(insert\s+into|update)\s+(public\.)?app_relation\y'
        OR pr.prosrc ~* '(insert\s+into|update|delete\s+from)\s+(public\.)?app_affaire_ledger\y')
   AND position('app_recalculer_type_du_bien' in pr.prosrc) = 0
   AND pr.proname NOT IN ('app_affaire_commission_ecrire', 'app_attribuer_chaines_affaire', 'app_edit_affaire_optimistic',
                          'app_affaire_partie_suivre', 'app_affaire_partie_reconstruire');

SELECT * FROM repetition_tag ORDER BY 1;
