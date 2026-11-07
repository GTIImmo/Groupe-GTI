-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — patch_partenaire_bien_sans_numero_2026-11-06.sql
-- ═══════════════════════════════════════════════════════════════════════════
-- A. Le contrôle de structure (lecture seule) : chaque ligne doit dire OK.
-- B. L'essai des gestes, DANS UNE TRANSACTION QUI EST TOUJOURS ANNULÉE : le bloc finit
--    par une erreur volontaire « RÉPÉTITION (annulée) : … » qui porte les verdicts.
--    Rien n'est gardé, ni lien ni modification. Attendu : 9 OK, 0 KO.
-- ═══════════════════════════════════════════════════════════════════════════

-- A. STRUCTURE
SELECT 'index syndic par notre numéro' AS controle,
       CASE WHEN to_regclass('public.app_partenaire_lien_un_syndic_dossier_uidx') IS NOT NULL THEN 'OK' ELSE 'KO' END AS verdict
UNION ALL SELECT 'index diagnostiqueur par notre numéro',
       CASE WHEN to_regclass('public.app_partenaire_lien_un_diag_dossier_uidx') IS NOT NULL THEN 'OK' ELSE 'KO' END
UNION ALL SELECT 'lecture générique à 3 paramètres, l''ancienne retirée',
       CASE WHEN to_regprocedure('public.app_partenaire_du_bien_lire(text,bigint,bigint)') IS NOT NULL
             AND to_regprocedure('public.app_partenaire_du_bien_lire(text,bigint)') IS NULL THEN 'OK' ELSE 'KO' END
UNION ALL SELECT 'lecture du syndic à 2 paramètres, l''ancienne retirée',
       CASE WHEN to_regprocedure('public.app_partenaire_syndic_du_bien_lire(bigint,bigint)') IS NOT NULL
             AND to_regprocedure('public.app_partenaire_syndic_du_bien_lire(bigint)') IS NULL THEN 'OK' ELSE 'KO' END
UNION ALL SELECT 'gestes : la règle « sans numéro Hektor » est posée',
       CASE WHEN pg_get_functiondef('public.app_partenaire_du_bien(text,bigint,bigint,text,boolean)'::regprocedure) LIKE '%Étape 1 du plan (06/11)%'
             AND pg_get_functiondef('public.app_partenaire_syndic_du_bien(bigint,bigint,text,boolean)'::regprocedure) LIKE '%Étape 1 du plan (06/11)%' THEN 'OK' ELSE 'KO' END
UNION ALL SELECT 'lectures ouvertes aux utilisateurs, pas au public',
       CASE WHEN has_function_privilege('authenticated', 'public.app_partenaire_du_bien_lire(text,bigint,bigint)', 'EXECUTE')
             AND has_function_privilege('authenticated', 'public.app_partenaire_syndic_du_bien_lire(bigint,bigint)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_partenaire_du_bien_lire(text,bigint,bigint)', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_partenaire_syndic_du_bien_lire(bigint,bigint)', 'EXECUTE') THEN 'OK' ELSE 'KO' END
UNION ALL SELECT 'complétion : service_role seulement',
       CASE WHEN has_function_privilege('service_role', 'public.app_partenaire_lien_completer_numeros()', 'EXECUTE')
             AND NOT has_function_privilege('authenticated', 'public.app_partenaire_lien_completer_numeros()', 'EXECUTE')
             AND NOT has_function_privilege('anon', 'public.app_partenaire_lien_completer_numeros()', 'EXECUTE') THEN 'OK' ELSE 'KO' END
UNION ALL SELECT 'tâche horaire à :50',
       CASE WHEN EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'partenaire-lien-numeros' AND schedule = '50 * * * *' AND active) THEN 'OK' ELSE 'KO' END
UNION ALL SELECT 'liens existants inchangés (84 actifs, tous avec numéro Hektor)',
       CASE WHEN (SELECT count(*) FROM public.app_partenaire_lien WHERE objet = 'bien' AND retire_le IS NULL AND hektor_annonce_id IS NULL) = 0 THEN 'OK' ELSE 'KO' END;

-- B. LES GESTES, ESSAYÉS PUIS ANNULÉS
DO $essai$
DECLARE
  v_admin uuid;
  v_app bigint; v_hk bigint;
  v_s1 text; v_s2 text; v_d1 text;
  r jsonb; ok int := 0; ko int := 0; journal text := '';
  v_lien bigint;
BEGIN
  SELECT id INTO v_admin FROM public.app_user_profile WHERE role::text = 'admin' AND is_active LIMIT 1;
  PERFORM set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  PERFORM set_config('request.jwt.claim.sub', v_admin::text, true);

  -- un bien vivant sans syndic ni diagnostiqueur, deux syndics et un diagnostiqueur du catalogue
  SELECT d.app_dossier_id, d.hektor_annonce_id INTO v_app, v_hk FROM public.app_dossier_current d
   WHERE d.hektor_annonce_id IS NOT NULL AND d.archive = '0'
     AND NOT EXISTS (SELECT 1 FROM public.app_partenaire_lien l WHERE l.retire_le IS NULL AND l.objet = 'bien'
                      AND (l.app_dossier_id = d.app_dossier_id OR l.hektor_annonce_id = d.hektor_annonce_id))
   ORDER BY d.app_dossier_id LIMIT 1;
  SELECT contact_id INTO v_s1 FROM public.app_partenaire_metier WHERE metier = 'syndic' AND retire_le IS NULL ORDER BY contact_id LIMIT 1;
  SELECT contact_id INTO v_s2 FROM public.app_partenaire_metier WHERE metier = 'syndic' AND retire_le IS NULL AND contact_id <> v_s1 ORDER BY contact_id LIMIT 1;
  SELECT contact_id INTO v_d1 FROM public.app_partenaire_metier WHERE metier = 'diagnostiqueur' AND retire_le IS NULL ORDER BY contact_id LIMIT 1;

  -- 1. sans numéro Hektor : le geste pose le lien ET reprend le numéro Hektor de la fiche
  r := public.app_partenaire_du_bien('syndic', v_app, NULL, v_s1, false);
  v_lien := (r->>'id')::bigint;
  IF r->>'action' = 'pose' AND (SELECT hektor_annonce_id FROM public.app_partenaire_lien WHERE id = v_lien) = v_hk
    THEN ok := ok + 1; ELSE ko := ko + 1; journal := journal || ' [1 KO ' || r::text || ']'; END IF;

  -- 2. l'ancienne lecture (numéro Hektor seul) le voit
  IF public.app_partenaire_syndic_du_bien_lire(v_hk)->>'partenaire_id' = v_s1
    THEN ok := ok + 1; ELSE ko := ko + 1; journal := journal || ' [2 KO]'; END IF;

  -- 3. un lien SANS numéro Hektor (cas de l'annonce en création), simulé sur la ligne d'essai
  UPDATE public.app_partenaire_lien SET hektor_annonce_id = NULL WHERE id = v_lien;
  IF public.app_partenaire_du_bien_lire('syndic', NULL, v_app)->>'partenaire_id' = v_s1
    THEN ok := ok + 1; ELSE ko := ko + 1; journal := journal || ' [3 KO lecture par notre numéro]'; END IF;

  -- 4. le geste du syndic le retrouve par notre numéro et le CHANGE (pas de 2e syndic actif)
  r := public.app_partenaire_syndic_du_bien(v_app, NULL, v_s2, false);
  IF r->>'action' = 'change' AND (SELECT count(*) FROM public.app_partenaire_lien
        WHERE role = 'syndic' AND objet = 'bien' AND retire_le IS NULL AND (app_dossier_id = v_app OR hektor_annonce_id = v_hk)) = 1
    THEN ok := ok + 1; ELSE ko := ko + 1; journal := journal || ' [4 KO ' || r::text || ']'; END IF;
  v_lien := (r->>'id')::bigint;

  -- 5. la complétion pose le numéro Hektor manquant
  UPDATE public.app_partenaire_lien SET hektor_annonce_id = NULL WHERE id = v_lien;
  r := public.app_partenaire_lien_completer_numeros();
  IF (r->>'completes')::int >= 1 AND (SELECT hektor_annonce_id FROM public.app_partenaire_lien WHERE id = v_lien) = v_hk
    THEN ok := ok + 1; ELSE ko := ko + 1; journal := journal || ' [5 KO ' || r::text || ']'; END IF;

  -- 6. l'appel d'aujourd'hui (les deux numéros) marche comme avant
  r := public.app_partenaire_du_bien('diagnostiqueur', v_app, v_hk, v_d1, false);
  IF r->>'action' = 'pose' THEN ok := ok + 1; ELSE ko := ko + 1; journal := journal || ' [6 KO ' || r::text || ']'; END IF;

  -- 7. retirer par notre numéro seul
  r := public.app_partenaire_du_bien('diagnostiqueur', v_app, NULL, NULL, true);
  IF r->>'action' = 'retire' THEN ok := ok + 1; ELSE ko := ko + 1; journal := journal || ' [7 KO ' || r::text || ']'; END IF;

  -- 8. un bien introuvable est refusé (pas de lien orphelin)
  BEGIN
    r := public.app_partenaire_du_bien('syndic', -1, NULL, v_s1, false);
    ko := ko + 1; journal := journal || ' [8 KO accepté]';
  EXCEPTION WHEN others THEN
    IF SQLERRM LIKE '%introuvable%' THEN ok := ok + 1; ELSE ko := ko + 1; journal := journal || ' [8 KO ' || SQLERRM || ']'; END IF;
  END;

  -- 9. ni numéro ni dossier : refusé
  BEGIN
    r := public.app_partenaire_du_bien('syndic', NULL, NULL, v_s1, false);
    ko := ko + 1; journal := journal || ' [9 KO accepté]';
  EXCEPTION WHEN others THEN
    IF SQLERRM LIKE '%Bien inconnu%' THEN ok := ok + 1; ELSE ko := ko + 1; journal := journal || ' [9 KO ' || SQLERRM || ']'; END IF;
  END;

  RAISE EXCEPTION 'RÉPÉTITION (annulée, rien n''est gardé) : % OK, % KO — bien d''essai %/% %', ok, ko, v_app, v_hk, journal;
END
$essai$;
