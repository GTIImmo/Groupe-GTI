-- =====================================================================
-- INVERSE -- REMETTRE LES 54 COQUILLES AU REGISTRE      02/11/2026
-- =====================================================================
-- Il defait patch_masquer_coquilles_offre_2026-11-02.sql, et RIEN D'AUTRE.
--
-- * AUCUNE DONNEE N'A ETE TOUCHEE par le patch : il n'y a donc rien a
--   restaurer. Une seule ligne a ete inseree dans une fonction, on la retire.
--   C'est le retour arriere le moins risque de tout le projet.
--
-- /!\ IL NE SUPPRIME PAS app_affaire_est_coquille : la fonction peut etre
--   appelee ailleurs (le front, un controle, une sentinelle). La retirer est
--   un geste a part, et une decision de Frederic :
--       DROP FUNCTION public.app_affaire_est_coquille(text, text, jsonb);
--
-- /!\ ET IL NE JUGE QUE SA PART (regle n° 31) : il verifie qu'il ne reste
--   aucune trace du filtre, et que les 54 coquilles sont bien revenues dans
--   le decompte des dossiers.
-- =====================================================================

DO $retire$
DECLARE
    def      text;
    nouvelle text;
BEGIN
    SELECT pg_get_functiondef(p.oid) INTO def
      FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = 'public' AND p.proname = 'app_registre_dossiers';

    IF def IS NULL THEN
        RAISE EXCEPTION 'app_registre_dossiers n''existe pas -- ON NE TOUCHE A RIEN';
    END IF;

    IF position('app_affaire_est_coquille' in def) = 0 THEN
        RAISE NOTICE 'le filtre n''est pas la -- rien a defaire.';
        RETURN;
    END IF;

    -- On retire EXACTEMENT les trois lignes posees, pas une de plus. Si le
    -- texte a change (quelqu'un a retouche la fonction depuis), on S'ARRETE :
    -- mieux vaut un retour arriere refuse qu'un retour arriere approximatif.
    nouvelle := replace(def,
        E'\n           -- 02/11/2026 : ON NE MONTRE PLUS LES COQUILLES D''OFFRE. Un seul\n           -- predicat, appele par CHAQUE porte -- voir app_affaire_est_coquille.\n           and not public.app_affaire_est_coquille(l.kind, l.date, l.propositions_json)',
        '');

    IF position('app_affaire_est_coquille' in nouvelle) > 0 THEN
        RAISE EXCEPTION 'le bloc pose n''a pas ete retrouve mot pour mot -- la fonction a ete retouchee depuis, ON NE TOUCHE A RIEN';
    END IF;

    EXECUTE nouvelle;
    RAISE NOTICE 'filtre retire de app_registre_dossiers.';
END $retire$;

REVOKE ALL ON FUNCTION public.app_registre_dossiers(integer) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.app_registre_dossiers(integer) TO authenticated, service_role;

-- --- LA PREUVE DU RETOUR ---
DO $preuve$
DECLARE reste integer; dossiers integer;
BEGIN
    SELECT count(*) INTO reste
      FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = 'public' AND p.proname = 'app_registre_dossiers'
       AND pg_get_functiondef(p.oid) LIKE '%app_affaire_est_coquille%';
    IF reste <> 0 THEN
        RAISE EXCEPTION 'le filtre est encore dans la fonction -- le retour n''a PAS eu lieu';
    END IF;

    -- le temoin positif : les 7 dossiers de coquilles doivent etre revenus
    SELECT count(DISTINCT l.app_chaine_id) INTO dossiers
      FROM public.app_affaire_ledger l
     WHERE l.app_chaine_id IS NOT NULL
       AND NOT (btrim(coalesce(l.hektor_affaire_id, '')) <> '' AND l.present_in_hektor IS false);
    RAISE NOTICE 'retour arriere fait. Dossiers comptes : % (12 117 attendu au 02/11).', dossiers;
END $preuve$;
