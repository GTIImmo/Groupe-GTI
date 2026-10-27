-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — P3 (préalable) : la vue des liens compte les transactions « vivantes chez nous »     27/10/2026
-- Lecture seule pour la base : une table temporaire de résultats, une vue temporaire « d'avant » (témoin inverse),
-- et un ESSAI SUR UNE VRAIE TRANSACTION fait dans un sous-bloc qui est TOUJOURS annulé (RAISE capturé) :
-- rien n'en reste, ni dans le registre ni dans la table des parties.
-- ⚠ Les temps se mesurent sous le compte de l'utilisateur (rôle authenticated + son identifiant).
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TEMP TABLE IF NOT EXISTS repetition_p3v (n int, controle text, verdict text);
TRUNCATE repetition_p3v;

DO $rep$
DECLARE
    v      text := replace(pg_get_viewdef('public.app_contact_relations_current'::regclass), chr(13), '');
    regle  text := '(NOT ((btrim(COALESCE(l.hektor_affaire_id, ''''::text)) <> ''''::text) AND (l.present_in_hektor IS FALSE)))';
    cols   text;
    ecarts int;
    j      json;
    plan   text;
    ms     numeric;
    u      record;
    i      int;
    a_id   bigint;
    c_id   text;
    cle    text;
    neuve_nee int; avant_nee int; neuve_suppr int; avant_suppr int;
    parties_apres_annulation int; parties_avant int;
BEGIN
    -- 1. les 20 colonnes de P2, inchangées
    SELECT string_agg(attname || ':' || format_type(atttypid, atttypmod), ', ' ORDER BY attnum) INTO cols
      FROM pg_attribute WHERE attrelid = 'public.app_contact_relations_current'::regclass AND attnum > 0 AND NOT attisdropped;
    INSERT INTO repetition_p3v VALUES (1, 'les 20 colonnes inchangees',
        CASE WHEN cols LIKE '%refreshed_at:text, origine:text, proprietaire_depuis:text' AND cols LIKE 'relation_key:text, hektor_contact_id:text,%'
             THEN 'OK' ELSE '⛔ ECHEC (' || cols || ')' END);
    -- 2. security_invoker et droits
    INSERT INTO repetition_p3v
    SELECT 2, 'security_invoker garde, droits inchanges',
           CASE WHEN reloptions::text LIKE '%security_invoker=true%'
                 AND (SELECT string_agg(x::text, ',' ORDER BY x::text) FROM unnest(relacl) x)
                     = 'authenticated=r/postgres,postgres=arwdDxtm/postgres,service_role=arwdDxtm/postgres'
                THEN 'OK' ELSE '⛔ ECHEC' END
      FROM pg_class WHERE oid = 'public.app_contact_relations_current'::regclass;
    -- 3. la vue lit la règle « vivante », plus « présente chez Hektor »
    INSERT INTO repetition_p3v VALUES (3, 'la vue lit la regle « vivante » et plus « presente chez Hektor »',
        CASE WHEN position(regle in v) > 0 AND position('p.transaction_presente' in v) = 0 THEN 'OK' ELSE '⛔ ECHEC' END);
    -- 4. TÉMOIN INVERSE : la vue d'avant (P2) se reconstitue à l'octet
    v := replace(v, regle, 'p.transaction_presente');
    IF md5(v) <> '0021f0f1681dcaab4ef12fd21514d254' THEN
        INSERT INTO repetition_p3v VALUES (4, 'la vue d''avant (P2) se reconstitue a l''octet', '⛔ ECHEC (' || md5(v) || ')');
        RETURN;
    END IF;
    INSERT INTO repetition_p3v VALUES (4, 'la vue d''avant (P2) se reconstitue a l''octet (seule la condition a change)', 'OK');
    EXECUTE 'create or replace temp view vue_d_avant with (security_invoker = true) as ' || rtrim(rtrim(v), ';');
    GRANT SELECT ON vue_d_avant TO authenticated;

    -- 5. AUJOURD'HUI, AUCUNE LIGNE NE CHANGE : la vue entière, dans les deux sens
    SELECT count(*) INTO ecarts FROM (
        (SELECT * FROM public.app_contact_relations_current EXCEPT ALL SELECT * FROM vue_d_avant)
        UNION ALL
        (SELECT * FROM vue_d_avant EXCEPT ALL SELECT * FROM public.app_contact_relations_current)) x;
    INSERT INTO repetition_p3v VALUES (5, 'aujourd''hui, la vue rend exactement les memes lignes (vue entiere, deux sens)',
        CASE WHEN ecarts = 0 THEN 'OK (' || (SELECT count(*) FROM vue_d_avant) || ' lignes)' ELSE '⛔ ECHEC (' || ecarts || ' ecart(s))' END);

    -- 6-7. ESSAI SUR UNE VRAIE TRANSACTION, DANS UN SOUS-BLOC TOUJOURS ANNULÉ
    SELECT l.app_affaire_id, p.app_contact_id_texte INTO a_id, c_id
      FROM public.app_affaire_ledger l JOIN public.app_affaire_partie p ON p.app_affaire_id = l.app_affaire_id
     WHERE l.present_in_hektor AND btrim(coalesce(l.hektor_affaire_id, '')) <> '' AND p.role = 'acquereur'
       AND p.transaction_presente AND p.app_contact_id IS NOT NULL
     ORDER BY l.app_affaire_id DESC LIMIT 1;
    cle := 'aff_' || a_id || '_' || c_id;
    SELECT count(*) INTO parties_avant FROM public.app_affaire_partie WHERE app_affaire_id = a_id;
    BEGIN
        -- « née chez nous, pas encore confirmée » : sans numéro Hektor, pas chez Hektor
        UPDATE public.app_affaire_ledger SET hektor_affaire_id = NULL, present_in_hektor = false WHERE app_affaire_id = a_id;
        SELECT count(*) INTO neuve_nee FROM public.app_contact_relations_current WHERE hektor_contact_id = c_id AND relation_key = cle;
        SELECT count(*) INTO avant_nee FROM vue_d_avant WHERE hektor_contact_id = c_id AND relation_key = cle;
        -- « supprimée » : elle a un numéro Hektor, mais n'est plus chez Hektor (le geste « Supprimer »)
        UPDATE public.app_affaire_ledger SET hektor_affaire_id = 'essai_p3_' || a_id WHERE app_affaire_id = a_id;
        SELECT count(*) INTO neuve_suppr FROM public.app_contact_relations_current WHERE hektor_contact_id = c_id AND relation_key = cle;
        SELECT count(*) INTO avant_suppr FROM vue_d_avant WHERE hektor_contact_id = c_id AND relation_key = cle;
        RAISE EXCEPTION 'annule_l_essai';
    EXCEPTION WHEN raise_exception THEN
        NULL;   -- tout ce qui précède dans le sous-bloc est annulé
    END;
    INSERT INTO repetition_p3v VALUES (6, 'une transaction NEE CHEZ NOUS (sans numero Hektor) : l''acheteur apparait ; la vue d''avant le cachait (affaire ' || a_id || ')',
        CASE WHEN neuve_nee = 1 AND avant_nee = 0 THEN 'OK' ELSE '⛔ ECHEC (neuve ' || neuve_nee || ', avant ' || avant_nee || ')' END);
    INSERT INTO repetition_p3v VALUES (7, 'une transaction SUPPRIMEE (avec son numero, plus chez Hektor) : hors du compte, comme avant',
        CASE WHEN neuve_suppr = 0 AND avant_suppr = 0 THEN 'OK' ELSE '⛔ ECHEC (neuve ' || neuve_suppr || ', avant ' || avant_suppr || ')' END);
    SELECT count(*) INTO parties_apres_annulation FROM public.app_affaire_partie WHERE app_affaire_id = a_id AND transaction_presente;
    INSERT INTO repetition_p3v
    SELECT 8, 'l''essai n''a rien laisse : la transaction est intacte, ses parties aussi',
        CASE WHEN l.present_in_hektor AND btrim(coalesce(l.hektor_affaire_id, '')) NOT IN ('', 'essai_p3_' || a_id)
              AND parties_apres_annulation = parties_avant THEN 'OK' ELSE '⛔ ECHEC' END
      FROM public.app_affaire_ledger l WHERE l.app_affaire_id = a_id;

    -- 9-10. le temps de la fiche, sous deux comptes réels
    FOR u IN SELECT * FROM (VALUES (1, 'Frederic (admin)', 'd4b1685f-948b-4ce8-af15-671b94a725e6', 200),
                                   (2, 'un commercial',    'c8a61bde-2899-443f-831b-3a4f5a8ec36b', 400)) x(n, nom, sub, seuil) LOOP
        PERFORM set_config('request.jwt.claims', json_build_object('sub', u.sub, 'role', 'authenticated')::text, true);
        EXECUTE 'set local role authenticated';
        FOR i IN 1..2 LOOP
            EXECUTE 'explain (analyze, format json) select * from public.app_contact_relations_current where hektor_contact_id = ''10354352'' order by last_seen_at desc' INTO j;
        END LOOP;
        EXECUTE 'reset role';
        plan := j::text;
        ms := round((j->0->>'Execution Time')::numeric, 1);
        INSERT INTO repetition_p3v VALUES (8 + u.n, 'fiche de JACQUIER, ' || u.nom || ' : moins de ' || u.seuil || ' ms, index texte servis',
            CASE WHEN ms < u.seuil AND position('"idx_app_relation_contact_id_texte"' in plan) > 0
                  AND position('"idx_app_affaire_partie_contact_id_texte"' in plan) > 0 THEN 'OK (' || ms || ' ms)'
                 ELSE '⛔ ECHEC (' || ms || ' ms)' END);
    END LOOP;
    DROP VIEW IF EXISTS vue_d_avant;
END
$rep$;

SELECT * FROM repetition_p3v ORDER BY 1;
