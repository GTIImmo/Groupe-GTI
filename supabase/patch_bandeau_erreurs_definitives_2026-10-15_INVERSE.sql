-- =============================================================================
--  RETOUR ARRIERE du patch « bandeau : erreurs definitives »      15/10/2026
-- =============================================================================
--  Il remet la condition d'origine (5 tentatives SEULEMENT) et verifie qu'il
--  retombe sur l'empreinte mesuree avant le patch.
--
--  ⚠ CE QU'ON PERD EN REVENANT EN ARRIERE : les travaux dont le type n'est PAS
--    rejouable redeviennent invisibles dans l'app, tout en continuant a faire
--    sonner data.travaux_en_erreur. C'est exactement le defaut du 15/10.
-- =============================================================================

DO $$
DECLARE
  v_corps text;
  v_neuf  CONSTANT text := '(COALESCE(j.attempt_count, 0) >= 5 OR j.requested_at < (now() - ''3 hours''::interval))';
  v_ancre CONSTANT text := 'COALESCE(j.attempt_count, 0) >= 5';
  v_apres text;
BEGIN
  SELECT pg_get_viewdef('public.app_en_attente_humain'::regclass, true) INTO v_corps;

  IF position(v_neuf in v_corps) = 0 THEN
    RAISE NOTICE 'RIEN A FAIRE : le patch n''est pas pose.';
    RETURN;
  END IF;

  v_corps := replace(v_corps, v_neuf, v_ancre);
  EXECUTE 'CREATE OR REPLACE VIEW public.app_en_attente_humain AS ' || v_corps;

  SELECT md5(replace(pg_get_viewdef('public.app_en_attente_humain'::regclass, true), chr(13), ''))
    INTO v_apres;

  IF v_apres <> '8ae7e3abdf139acf519027762539ce58' THEN
    RAISE EXCEPTION 'STOP : on ne retombe PAS sur l''empreinte d''origine (%). Rien n''est sur, on annule.', v_apres;
  END IF;

  RAISE NOTICE 'RETIRE : la vue est revenue a son empreinte du 15/10 avant patch.';
END $$;

COMMENT ON VIEW public.app_en_attente_humain IS
  'Ce qui attend un humain. Branche 1 : les gestes abandonnes (5 tentatives). '
  'Branche 2 : la creation reussie dont la suite a echoue (4a, 09/10/2026).';

-- Controle : 0 ligne de moins de 5 tentatives doit rester.
SELECT count(*) FILTER (WHERE tentatives < 5) AS doit_valoir_zero,
       count(*)                               AS total_affiche
  FROM public.app_en_attente_humain;
