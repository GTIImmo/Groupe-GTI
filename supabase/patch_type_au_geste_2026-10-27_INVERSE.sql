-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIÈRE — ÉTAPE 2 « au geste » : retirer la ligne des 6 portes, puis les 3 fonctions        27/10/2026
-- Chaque porte doit retrouver EXACTEMENT son empreinte d'avant, sinon tout est annulé.
-- Le type déjà écrit reste tel quel (la nuit le réécrit, comme avant).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $inv$
DECLARE
    marque text := '  -- ⑧ ÉTAPE 2 (27/10/2026) : LE TYPE SE CALCULE CHEZ NOUS AU GESTE (note des types §45).' || chr(10);
    p record;
    f text;
BEGIN
    FOR p IN SELECT * FROM (VALUES
        ('app_link_mandant_optimistic',           '22b3c52700ff323b773e477382022779', '  perform public.app_recalculer_type_du_bien(target_hektor_annonce_id, target_app_dossier_id);'),
        ('app_create_mandant_contact_optimistic', '04a25df1327d4b7b19413a757f861aeb', '  perform public.app_recalculer_type_du_bien(target_hektor_annonce_id, target_app_dossier_id);'),
        ('app_unlink_mandant_optimistic',         '3469d98941d345d6abd58afb39f25db2', '  perform public.app_recalculer_type_du_bien(target_hektor_annonce_id, target_app_dossier_id);'),
        ('app_change_annonce_status_optimistic',  '93be71b41e9ff172de9e8c3e261233a5', '  perform public.app_recalculer_type_du_bien(d.hektor_annonce_id::text, target_dossier_id);'),
        ('app_modifier_affaire_optimistic',       '910e79470819a1111d21b608625f95b8', '  perform public.app_recalculer_type_du_bien(a.hektor_annonce_id::text, a.app_dossier_id);'),
        ('app_geste_affaire_optimistic',          '89d5399db696e004ba5cc59454e1c75a', '  PERFORM public.app_recalculer_type_du_bien(a.hektor_annonce_id::text, a.app_dossier_id);')
    ) x(nom, empreinte, ligne) LOOP
        SELECT pg_get_functiondef(pr.oid) INTO f FROM pg_proc pr JOIN pg_namespace s ON s.oid = pr.pronamespace
         WHERE s.nspname = 'public' AND pr.proname = p.nom;
        IF position('app_recalculer_type_du_bien' in f) = 0 THEN
            RAISE NOTICE '%', p.nom || ' ne porte pas la ligne : rien a defaire.';
            CONTINUE;
        END IF;
        IF position(marque || p.ligne || chr(10) in f) = 0 THEN
            RAISE EXCEPTION '%', format('ARRET : dans %s, la ligne n''est pas sous la forme posee ; tout est annule.', p.nom);
        END IF;
        EXECUTE replace(f, marque || p.ligne || chr(10), '');
        IF (SELECT md5(pg_get_functiondef(pr.oid)) FROM pg_proc pr JOIN pg_namespace s ON s.oid = pr.pronamespace
             WHERE s.nspname = 'public' AND pr.proname = p.nom) <> p.empreinte THEN
            RAISE EXCEPTION '%', format('ARRET : %s n''a pas retrouve son empreinte d''avant ; tout est annule.', p.nom);
        END IF;
    END LOOP;
END
$inv$;

DROP FUNCTION IF EXISTS public.app_recalculer_type_du_bien(text, bigint);
DROP FUNCTION IF EXISTS public.app_recalculer_type_contacts(text[]);
DROP FUNCTION IF EXISTS public.app_type_depuis_nos_registres(text);

COMMIT;
