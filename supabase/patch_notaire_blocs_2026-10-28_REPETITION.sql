-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ⑧ notaire, les 4 blocs : le carnet des interlocuteurs et la fiche enrichie                 28/10/2026
-- LECTURE SEULE : aucun contrôle n'écrit d'interlocuteur (les gestes d'écriture sont éprouvés à part, dans une transaction
-- annulée -- eprouver_blocs.js -- pour ne laisser aucune fausse saisie en production).
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TEMP TABLE IF NOT EXISTS repetition_blocs (n int, controle text, verdict text);
TRUNCATE repetition_blocs;

DO $rep$
DECLARE u record; j jsonb; ms numeric; t0 timestamptz; nb int; vus int; aff bigint; notaire text;
BEGIN
    -- 1. la table : RLS, lecture seule pour les comptes, rien pour anon
    INSERT INTO repetition_blocs
    SELECT 1, 'la table : RLS active, les comptes LISENT seulement, anon rien',
           CASE WHEN c.relrowsecurity
                 AND has_table_privilege('authenticated', c.oid, 'SELECT')
                 AND NOT has_table_privilege('authenticated', c.oid, 'INSERT')
                 AND NOT has_table_privilege('authenticated', c.oid, 'UPDATE')
                 AND NOT has_table_privilege('authenticated', c.oid, 'DELETE')
                 AND NOT has_table_privilege('anon', c.oid, 'SELECT') THEN 'OK' ELSE '⛔ ECHEC' END
      FROM pg_class c WHERE c.oid = 'public.app_notaire_interlocuteur'::regclass;

    -- 2. la fonction d'écriture : SECURITY DEFINER, comptes oui, anon non
    INSERT INTO repetition_blocs
    SELECT 2, 'la fonction d''ecriture : SECURITY DEFINER, authenticated oui, anon non',
           CASE WHEN count(*) = 1 AND bool_and(pr.prosecdef)
                 AND bool_and(has_function_privilege('authenticated', pr.oid, 'EXECUTE'))
                 AND NOT bool_or(has_function_privilege('anon', pr.oid, 'EXECUTE')) THEN 'OK' ELSE '⛔ ECHEC' END
      FROM pg_proc pr WHERE pr.pronamespace = 'public'::regnamespace AND pr.proname = 'app_notaire_interlocuteur_ecrire';

    -- 3. la fiche garde ses dossiers, et porte les clés neuves
    j := public.app_notaire_fiche('10166165');
    SELECT count(*) FILTER (WHERE e ? 'conditions' AND e ? 'documents'), count(*) INTO nb, vus FROM jsonb_array_elements(j->'dossiers') e;
    INSERT INTO repetition_blocs VALUES (3, 'la fiche garde ses 800 dossiers ; chacun porte conditions et documents ; la fiche porte interlocuteurs',
        CASE WHEN vus = 800 AND nb = vus AND j ? 'interlocuteurs' THEN 'OK (' || vus || ')' ELSE '⛔ ECHEC (' || nb || ' sur ' || vus || ')' END);

    -- 4. les documents : seulement pour un compromis SANS vente (les pièces d'un dossier vivant)
    SELECT count(*) INTO nb FROM jsonb_array_elements(j->'dossiers') e
     WHERE jsonb_array_length(e->'documents') > 0 AND (e->>'kind' <> 'compromis' OR (e->'vente_chaine') IS NOT NULL AND e->'vente_chaine' <> 'null'::jsonb);
    INSERT INTO repetition_blocs VALUES (4, 'des documents seulement sur un compromis sans vente',
        CASE WHEN nb = 0 THEN 'OK' ELSE '⛔ ECHEC (' || nb || ')' END);

    -- 5. ⚠ TÉMOIN POSITIF des documents : le notaire qui a le plus de dossiers en cours (acte à venir) -> des noms de documents
    j := public.app_notaire_fiche('10352963');
    SELECT count(*) INTO nb FROM jsonb_array_elements(j->'dossiers') e WHERE jsonb_array_length(e->'documents') > 0;
    INSERT INTO repetition_blocs VALUES (5, 'TEMOIN POSITIF : le notaire aux 7 dossiers en cours (10352963) a des documents sur ses compromis',
        CASE WHEN nb > 0 THEN 'OK (' || nb || ' compromis avec documents)' ELSE '⛔ ECHEC (aucun)' END);

    -- 6. les conditions : une transaction du registre des conditions, vue par un de ses notaires, porte ses conditions
    SELECT c.app_affaire_id, p.app_contact_id_texte INTO aff, notaire
      FROM public.app_affaire_condition c JOIN public.app_affaire_partie p ON p.app_affaire_id = c.app_affaire_id
     WHERE p.role IN ('notaire_vendeur', 'notaire_acquereur') AND p.app_contact_id_texte IS NOT NULL LIMIT 1;
    IF aff IS NULL THEN
        INSERT INTO repetition_blocs VALUES (6, 'les conditions du registre arrivent dans la fiche du notaire', 'OK (sans objet : aucune condition sur une transaction a notaire)');
    ELSE
        j := public.app_notaire_fiche(notaire);
        SELECT jsonb_array_length(e->'conditions') INTO nb FROM jsonb_array_elements(j->'dossiers') e WHERE (e->>'app_affaire_id')::bigint = aff;
        SELECT count(*) INTO vus FROM public.app_affaire_condition WHERE app_affaire_id = aff;
        INSERT INTO repetition_blocs VALUES (6, 'les conditions du registre arrivent dans la fiche du notaire (transaction ' || aff || ')',
            CASE WHEN nb = vus AND vus > 0 THEN 'OK (' || nb || ')' ELSE '⛔ ECHEC (' || coalesce(nb, -1) || ' contre ' || vus || ')' END);
    END IF;

    -- 7-8. les temps, sous deux comptes réels (le notaire le plus chargé)
    FOR u IN SELECT * FROM (VALUES
        (7, 'Frederic (admin)', 'd4b1685f-948b-4ce8-af15-671b94a725e6', 1500),
        (8, 'un commercial',    'c8a61bde-2899-443f-831b-3a4f5a8ec36b', 1500)) x(n, nom, sub, seuil) LOOP
        PERFORM set_config('request.jwt.claims', json_build_object('sub', u.sub, 'role', 'authenticated')::text, true);
        EXECUTE 'set local role authenticated';
        FOR i IN 1..2 LOOP
            t0 := clock_timestamp();
            EXECUTE 'select public.app_notaire_fiche(''10166165'')' INTO j;
            ms := round(extract(epoch FROM clock_timestamp() - t0) * 1000, 1);
        END LOOP;
        EXECUTE 'reset role';
        INSERT INTO repetition_blocs VALUES (u.n, 'fiche du notaire le plus charge, ' || u.nom || ' : moins de ' || u.seuil || ' ms',
            CASE WHEN ms < u.seuil THEN 'OK (' || ms || ' ms)' ELSE '⛔ ECHEC (' || ms || ' ms)' END);
    END LOOP;
END
$rep$;

SELECT * FROM repetition_blocs ORDER BY 1;
