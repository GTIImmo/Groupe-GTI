-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ⑧ notaire étape 4 : la fonction de lecture de la fiche notaire                     28/10/2026
-- Lecture seule : aucun contrôle n'écrit ailleurs que dans sa table temporaire.
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TEMP TABLE IF NOT EXISTS repetition_not4 (n int, controle text, verdict text);
TRUNCATE repetition_not4;

DO $rep$
DECLARE u record; j jsonb; ms numeric; t0 timestamptz; nb int; attendu int; dbl int; hors int; vente text; cotes text; moi int;
        porte int; vus int;
BEGIN
    -- 1. la fonction : lecture seule, sous les règles d'accès, ouverte aux comptes, pas à anon
    INSERT INTO repetition_not4
    SELECT 1, 'la fonction existe, SECURITY INVOKER, STABLE, authenticated oui, anon non',
           CASE WHEN count(*) = 1 AND NOT bool_or(pr.prosecdef) AND bool_and(pr.provolatile = 's')
                 AND bool_and(has_function_privilege('authenticated', pr.oid, 'EXECUTE'))
                 AND NOT bool_or(has_function_privilege('anon', pr.oid, 'EXECUTE')) THEN 'OK' ELSE '⛔ ECHEC' END
      FROM pg_proc pr JOIN pg_namespace s ON s.oid = pr.pronamespace
     WHERE s.nspname = 'public' AND pr.proname = 'app_notaire_fiche';

    -- 2-3. les temps, sous deux comptes réels (le notaire le plus chargé)
    FOR u IN SELECT * FROM (VALUES
        (2, 'Frederic (admin)', 'd4b1685f-948b-4ce8-af15-671b94a725e6', 1500),
        (3, 'un commercial',    'c8a61bde-2899-443f-831b-3a4f5a8ec36b', 1500)) x(n, nom, sub, seuil) LOOP
        PERFORM set_config('request.jwt.claims', json_build_object('sub', u.sub, 'role', 'authenticated')::text, true);
        EXECUTE 'set local role authenticated';
        FOR i IN 1..2 LOOP
            t0 := clock_timestamp();
            EXECUTE 'select public.app_notaire_fiche(''10166165'')' INTO j;
            ms := round(extract(epoch FROM clock_timestamp() - t0) * 1000, 1);
        END LOOP;
        nb := jsonb_array_length(j->'dossiers');
        EXECUTE 'select count(*) from public.app_mes_biens_portefeuille()' INTO porte;
        -- ⚠ sous le commercial : chaque dossier rendu doit être sur un bien de SON portefeuille
        EXECUTE $q$select count(*) from jsonb_array_elements($1->'dossiers') e
                    where not exists (select 1 from public.app_mes_biens_portefeuille() m
                                       where m.id = (e->>'app_dossier_id')::bigint or m.hid = e->>'hektor_annonce_id')$q$ INTO hors USING j;
        EXECUTE 'reset role';
        INSERT INTO repetition_not4 VALUES (u.n, 'fiche du notaire le plus charge, ' || u.nom || ' : moins de ' || u.seuil || ' ms'
            || (CASE WHEN u.n = 3 THEN ', et rien hors de son portefeuille' ELSE '' END),
            CASE WHEN ms < u.seuil AND (u.n = 2 OR hors = 0)
                 THEN 'OK (' || ms || ' ms, ' || nb || ' dossiers' || (CASE WHEN u.n = 3 THEN ', ' || hors || ' hors portefeuille sur ' || porte || ' biens' ELSE '' END) || ')'
                 ELSE '⛔ ECHEC (' || ms || ' ms, ' || nb || ' dossiers, ' || coalesce(hors, -1) || ' hors portefeuille)' END);
    END LOOP;

    -- 3 bis. ⚠ TÉMOIN POSITIF : le contrôle 3 peut passer sur ZÉRO dossier (le notaire le plus chargé n'a rien dans ce
    --   portefeuille). On prend donc le notaire le PLUS PRÉSENT dans le portefeuille du commercial : il doit voir des dossiers,
    --   tous sur ses biens, et MOINS que l'admin (sinon la règle d'accès ne mord pas).
    PERFORM set_config('request.jwt.claims', json_build_object('sub', 'c8a61bde-2899-443f-831b-3a4f5a8ec36b', 'role', 'authenticated')::text, true);
    EXECUTE 'set local role authenticated';
    EXECUTE $q$select p.app_contact_id_texte from public.app_affaire_partie p
                where p.role in ('notaire_vendeur', 'notaire_acquereur') and p.app_contact_id_texte is not null
                group by 1 order by count(*) desc, 1 limit 1$q$ INTO cotes;
    EXECUTE 'select public.app_notaire_fiche($1)' INTO j USING cotes;
    vus := jsonb_array_length(j->'dossiers');
    EXECUTE $q$select count(*) from jsonb_array_elements($1->'dossiers') e
                where not exists (select 1 from public.app_mes_biens_portefeuille() m
                                   where m.id = (e->>'app_dossier_id')::bigint or m.hid = e->>'hektor_annonce_id')$q$ INTO hors USING j;
    EXECUTE 'reset role';
    nb := jsonb_array_length(public.app_notaire_fiche(cotes)->'dossiers');
    INSERT INTO repetition_not4 VALUES (31, 'TEMOIN POSITIF : le notaire le plus present chez ce commercial -> des dossiers, tous sur ses biens, moins que l''admin',
        CASE WHEN vus > 0 AND hors = 0 AND vus < nb THEN 'OK (' || cotes || ' : ' || vus || ' vus sur ' || nb || ')'
             ELSE '⛔ ECHEC (' || coalesce(cotes, '?') || ' : ' || vus || ' vus, ' || hors || ' hors portefeuille, admin ' || nb || ')' END);
    cotes := NULL;

    -- les contrôles suivants : sans règle d'accès (le compte qui pose)
    j := public.app_notaire_fiche('10166165');

    -- 4. une ligne par TRANSACTION : autant que de transactions vivantes distinctes, aucune en double
    SELECT count(DISTINCT l.app_affaire_id) INTO attendu
      FROM public.app_affaire_partie p JOIN public.app_affaire_ledger l ON l.app_affaire_id = p.app_affaire_id
     WHERE p.app_contact_id_texte = '10166165' AND p.role IN ('notaire_vendeur', 'notaire_acquereur')
       AND NOT (btrim(coalesce(l.hektor_affaire_id, '')) <> '' AND l.present_in_hektor IS FALSE);
    SELECT count(*) - count(DISTINCT e->>'app_affaire_id') INTO dbl FROM jsonb_array_elements(j->'dossiers') e;
    nb := jsonb_array_length(j->'dossiers');
    INSERT INTO repetition_not4 VALUES (4, 'une ligne par transaction vivante (temoin compte a part), aucune en double',
        CASE WHEN nb = attendu AND dbl = 0 THEN 'OK (' || nb || ')' ELSE '⛔ ECHEC (' || nb || ' contre ' || attendu || ', ' || dbl || ' doubles)' END);

    -- 5. un notaire des deux côtés : UNE ligne, deux côtés
    SELECT count(*) INTO nb FROM jsonb_array_elements(j->'dossiers') e WHERE jsonb_array_length(e->'cotes') = 2;
    INSERT INTO repetition_not4 VALUES (5, 'des deux cotes : une ligne, ses deux cotes', CASE WHEN nb > 0 THEN 'OK (' || nb || ' transactions)' ELSE '⛔ ECHEC (aucune)' END);

    -- 6. L'ISSUE DE LA CHAÎNE : le compromis de l'annonce 11729 (janvier 2026) porte la vente du 03/04/2026, où il n'est pas
    SELECT e->'vente_chaine'->>'date' INTO vente FROM jsonb_array_elements(j->'dossiers') e
     WHERE e->>'hektor_annonce_id' = '11729' AND e->>'kind' = 'compromis' LIMIT 1;
    INSERT INTO repetition_not4 VALUES (6, 'l''issue de la chaine : le compromis de 11729 porte la vente du 2026-04-03 (le notaire n''y est pas)',
        CASE WHEN vente = '2026-04-03' THEN 'OK' ELSE '⛔ ECHEC (' || coalesce(vente, 'rien') || ')' END);

    -- 7. jamais lui-même dans ses confrères
    SELECT count(*) INTO moi FROM jsonb_array_elements(j->'dossiers') e, jsonb_array_elements(e->'confreres') c WHERE c->>'id' = '10166165';
    INSERT INTO repetition_not4 VALUES (7, 'il n''est jamais son propre confrere', CASE WHEN moi = 0 THEN 'OK' ELSE '⛔ ECHEC (' || moi || ')' END);

    -- 8. une vente porte le compromis de sa chaîne (le délai compromis -> acte)
    SELECT count(*) FILTER (WHERE e->>'compromis_chaine' IS NOT NULL), count(*) INTO nb, vus FROM jsonb_array_elements(j->'dossiers') e WHERE e->>'kind' = 'vente';
    INSERT INTO repetition_not4 VALUES (8, 'les ventes portent le compromis de leur chaine (delai compromis -> acte)',
        CASE WHEN nb > 0 THEN 'OK (' || nb || ' ventes sur ' || vus || ')' ELSE '⛔ ECHEC (aucune)' END);

    -- 9. le bien est là (mandat ou dossier, agence) sur chaque ligne
    SELECT count(*) FILTER (WHERE e->'bien' IS NULL OR e->'bien' = 'null'::jsonb), count(*) INTO nb, vus FROM jsonb_array_elements(j->'dossiers') e;
    INSERT INTO repetition_not4 VALUES (9, 'chaque dossier porte son bien (parc, archives ou historique)',
        CASE WHEN nb = 0 THEN 'OK (' || vus || ')' ELSE '⛔ ECHEC (' || nb || ' sans bien sur ' || vus || ')' END);

    -- 9 bis. la médiane de l'agence (la référence de « Compromis -> acte ») : un nombre de jours plausible
    ms := (j->>'mediane_agence_jours')::numeric;
    INSERT INTO repetition_not4 VALUES (91, 'la mediane de l''agence compromis -> acte est un nombre de jours plausible (30 a 200)',
        CASE WHEN ms BETWEEN 30 AND 200 THEN 'OK (' || ms || ' j)' ELSE '⛔ ECHEC (' || coalesce(ms::text, 'vide') || ')' END);

    -- 10. un contact qui n'est pas notaire : une fiche vide, pas une erreur
    j := public.app_notaire_fiche('10354352');
    INSERT INTO repetition_not4 VALUES (10, 'un contact qui n''est pas notaire (JACQUIER) : aucune ligne, pas d''erreur',
        CASE WHEN jsonb_array_length(j->'dossiers') = 0 THEN 'OK' ELSE '⛔ ECHEC (' || jsonb_array_length(j->'dossiers') || ')' END);
END
$rep$;

SELECT * FROM repetition_not4 ORDER BY 1;
