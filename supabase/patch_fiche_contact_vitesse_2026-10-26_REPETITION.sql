-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — la vitesse de la fiche contact                                                26/10/2026
-- Lecture seule (une table temporaire de résultats, et une vue temporaire « d'avant » pour le témoin inverse).
-- À rejouer après la pose, puis le lendemain de la première nuit.
-- ⚠ LES TEMPS SE MESURENT SOUS LE COMPTE DE L'UTILISATEUR (rôle authenticated + son identifiant), JAMAIS en
--   service_role : le service_role ignore la RLS, et c'est elle qui coûtait (mesures du matin du 26/10 : 2,8 ms en
--   service_role pour une fiche qui mettait 2,4 s à Frédéric).
-- Comptes : Frédéric (admin) et un commercial actif. Contact témoin : 10354701 (M. Emrick HUGUES, 4 liens).
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TEMP TABLE IF NOT EXISTS repetition_fiche_contact (n int, controle text, verdict text);
TRUNCATE repetition_fiche_contact;

DO $rep$
DECLARE
    v      text := pg_get_viewdef('public.app_contact_relations_current'::regclass);
    j      json;
    plan   text;
    ms     numeric;
    ms_neuf numeric;
    u      record;
    k      text;
    i      int;
BEGIN
    -- le témoin inverse : la vue D'AVANT, reconstituée (les deux conversions), en vue temporaire
    v := replace(v, 'r.app_contact_id_texte AS hektor_contact_id', '(r.app_contact_id)::text AS hektor_contact_id');
    v := replace(v, 'p.app_contact_id_texte AS hektor_contact_id', '(p.app_contact_id)::text AS hektor_contact_id');
    IF md5(v) <> '84ca1b2e8f8ef513f0fdb166469b7b87' THEN
        INSERT INTO repetition_fiche_contact VALUES (0, 'la vue d''avant se reconstitue a l''octet', '⛔ ECHEC (' || md5(v) || ')');
        RETURN;
    END IF;
    EXECUTE 'create or replace temp view vue_d_avant with (security_invoker = true) as ' || rtrim(rtrim(v), ';');
    GRANT SELECT ON vue_d_avant TO authenticated;

    FOR u IN SELECT * FROM (VALUES (1, 'Frederic (admin)', 'd4b1685f-948b-4ce8-af15-671b94a725e6', 200),
                                   (2, 'un commercial',    'c8a61bde-2899-443f-831b-3a4f5a8ec36b', 400)) x(n, nom, sub, seuil) LOOP
        PERFORM set_config('request.jwt.claims', json_build_object('sub', u.sub, 'role', 'authenticated')::text, true);
        FOREACH k IN ARRAY ARRAY['public.app_contact_relations_current', 'vue_d_avant'] LOOP
            EXECUTE 'set local role authenticated';
            FOR i IN 1..2 LOOP            -- deux fois : on garde la mesure « a chaud »
                EXECUTE 'explain (analyze, format json) select * from ' || k || ' where hektor_contact_id = ''10354701''' INTO j;
            END LOOP;
            -- ⚠ le plan se lit dans le JSON entier : un « explain format text » rend une ligne PAR noeud,
            --   et EXECUTE ... INTO n'en garde que la PREMIERE (essai du 26/10 : faux rouge).
            plan := j::text;
            EXECUTE 'reset role';
            ms := round((j->0->>'Execution Time')::numeric, 1);
            IF k = 'vue_d_avant' THEN
                -- ⚠ la vue d'avant profite AUSSI de la regle enveloppee (elle porte sur la TABLE) : elle ne revient pas
                --   aux ~2 400 ms, elle tombe vers ~230 ms (essai du 26/10). Le temoin dit donc : SANS les colonnes texte,
                --   c'est nettement plus lent -- ce sont bien elles qui font le reste du gain.
                INSERT INTO repetition_fiche_contact VALUES (10 + u.n, 'TEMOIN INVERSE, ' || u.nom || ' : la vue d''avant (conversion) reste nettement plus lente',
                    CASE WHEN ms > 1.5 * ms_neuf THEN 'OK (' || ms || ' ms contre ' || ms_neuf || ' ms)'
                         ELSE '⚠ A REGARDER (' || ms || ' ms contre ' || ms_neuf || ' ms : les colonnes ne font-elles rien ?)' END);
            ELSE
                ms_neuf := ms;
                INSERT INTO repetition_fiche_contact VALUES (u.n, 'fiche contact, ' || u.nom || ' : moins de ' || u.seuil || ' ms',
                    CASE WHEN ms < u.seuil THEN 'OK (' || ms || ' ms)' ELSE '⛔ ECHEC (' || ms || ' ms)' END);
                INSERT INTO repetition_fiche_contact VALUES (2 + u.n, 'fiche contact, ' || u.nom || ' : les DEUX index texte servent',
                    CASE WHEN position('"idx_app_relation_contact_id_texte"' in plan) > 0
                          AND position('"idx_app_affaire_partie_contact_id_texte"' in plan) > 0 THEN 'OK'
                         ELSE '⛔ ECHEC (plan sans les index)' END);
            END IF;
        END LOOP;

        -- le cote BIEN de la meme vue (api.ts l. 9708 et 9825) : ne doit pas ralentir
        EXECUTE 'set local role authenticated';
        EXECUTE 'explain (analyze, format json) select * from public.app_contact_relations_current where app_dossier_id = 3828957' INTO j;
        EXECUTE 'explain (analyze, format json) select * from public.app_contact_relations_current where app_dossier_id = 3828957' INTO j;
        EXECUTE 'reset role';
        ms := round((j->0->>'Execution Time')::numeric, 1);
        INSERT INTO repetition_fiche_contact VALUES (4 + u.n, 'personnes d''un bien (dossier 3828957), ' || u.nom || ' : moins de 500 ms',
            CASE WHEN ms < 500 THEN 'OK (' || ms || ' ms)' ELSE '⛔ ECHEC (' || ms || ' ms)' END);
        EXECUTE 'set local role authenticated';
        EXECUTE 'explain (analyze, format json) select * from public.app_contact_relations_current where hektor_annonce_id = ''62774''' INTO j;
        EXECUTE 'explain (analyze, format json) select * from public.app_contact_relations_current where hektor_annonce_id = ''62774''' INTO j;
        EXECUTE 'reset role';
        ms := round((j->0->>'Execution Time')::numeric, 1);
        INSERT INTO repetition_fiche_contact VALUES (6 + u.n, 'personnes d''un bien (annonce 62774), ' || u.nom || ' : moins de 500 ms',
            CASE WHEN ms < 500 THEN 'OK (' || ms || ' ms)' ELSE '⛔ ECHEC (' || ms || ' ms)' END);
    END LOOP;
    DROP VIEW IF EXISTS vue_d_avant;
END
$rep$;

INSERT INTO repetition_fiche_contact
SELECT 20, 'liens : la colonne texte vaut notre numero sur CHAQUE ligne (donc la vue rend les memes lignes)',
       CASE WHEN count(*) FILTER (WHERE app_contact_id_texte IS DISTINCT FROM app_contact_id::text) = 0
            THEN 'OK (' || count(*) || ' lignes)' ELSE '⛔ ECHEC' END FROM public.app_relation
UNION ALL
SELECT 21, 'parties : la colonne texte vaut notre numero sur CHAQUE ligne (y compris apres la nuit)',
       CASE WHEN count(*) FILTER (WHERE app_contact_id_texte IS DISTINCT FROM app_contact_id::text) = 0
            THEN 'OK (' || count(*) || ' lignes)' ELSE '⛔ ECHEC' END FROM public.app_affaire_partie
UNION ALL
SELECT 22, 'la sentinelle de la table des parties ne voit aucun ecart',
       CASE WHEN count(*) = 0 THEN 'OK' ELSE '⛔ ECHEC (' || count(*) || ')' END FROM public.app_v_affaire_partie_ecarts
UNION ALL
SELECT 23, 'la regle des liens est enveloppee',
       CASE WHEN pg_get_expr(polqual, polrelid) ~ '^\(?\s*SELECT is_app_user_active\(\)' THEN 'OK' ELSE '⛔ ECHEC (' || pg_get_expr(polqual, polrelid) || ')' END
  FROM pg_policy WHERE polname = 'app_relation_select_active_users' AND polrelid = 'public.app_relation'::regclass;

SELECT * FROM repetition_fiche_contact ORDER BY 1;
