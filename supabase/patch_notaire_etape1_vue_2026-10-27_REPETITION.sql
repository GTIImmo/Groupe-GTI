-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — NOTAIRE étape 1 : les notaires dans la vue des liens d'un contact          27/10/2026
-- Lecture seule (une table temporaire de résultats, une vue temporaire « d'avant » pour le témoin inverse).
-- ⚠ Les temps se mesurent sous le compte de l'utilisateur (rôle authenticated + son identifiant), et AVANT la
--   comparaison de la vue entière (qui vide le cache : faux rouge « à froid » du 27/10, §39.1).
-- Témoins : 10354352 (JACQUIER, acheteur + propriétaire) ; 10166165 (le notaire le plus chargé, 810 rôles).
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TEMP TABLE IF NOT EXISTS repetition_not1 (n int, controle text, verdict text);
TRUNCATE repetition_not1;

DO $rep$
DECLARE
    v        text := replace(pg_get_viewdef('public.app_contact_relations_current'::regclass), chr(13), '');
    f_avant  text := '(p.role = ''acquereur''::text)';
    f_apres  text := '(p.role = ANY (ARRAY[''acquereur''::text, ''notaire_vendeur''::text, ''notaire_acquereur''::text]))';
    -- ⚠ LA FORME RENDUE PAR POSTGRES (vue le 27/10) : les deux CASE sur plusieurs lignes, construites par chr(10) (leçon 30)
    r_apres  text := '    b.titre_bien,' || chr(10) || '        CASE' || chr(10)
                  || '            WHEN (p.role = ''acquereur''::text) THEN (''acquereur_''::text || l.kind)' || chr(10)
                  || '            ELSE p.role' || chr(10) || '        END AS role_contact';
    r_avant  text := '    b.titre_bien,' || chr(10) || '    (''acquereur_''::text || l.kind) AS role_contact';
    k_apres  text := '((((''aff_''::text || (l.app_affaire_id)::text) || ''_''::text) || (p.app_contact_id)::text) ||' || chr(10)
                  || '        CASE' || chr(10) || '            WHEN (p.role = ''acquereur''::text) THEN ''''::text' || chr(10)
                  || '            ELSE (''_''::text || p.role)' || chr(10) || '        END) AS relation_key';
    k_avant  text := '(((''aff_''::text || (l.app_affaire_id)::text) || ''_''::text) || (p.app_contact_id)::text) AS relation_key';
    cols text; j json; plan text; ms numeric; u record; i int; k text;
    nouv int; perdues int; attendues int; doublons_neuf int; doublons_avant int; roles_neufs text;
BEGIN
    -- 1-2. forme de la vue
    SELECT string_agg(attname || ':' || format_type(atttypid, atttypmod), ', ' ORDER BY attnum) INTO cols
      FROM pg_attribute WHERE attrelid = 'public.app_contact_relations_current'::regclass AND attnum > 0 AND NOT attisdropped;
    INSERT INTO repetition_not1 VALUES (1, 'les 20 colonnes inchangees',
        CASE WHEN cols LIKE 'relation_key:text, hektor_contact_id:text,%refreshed_at:text, origine:text, proprietaire_depuis:text' THEN 'OK' ELSE '⛔ ECHEC' END);
    INSERT INTO repetition_not1
    SELECT 2, 'security_invoker garde, droits inchanges',
           CASE WHEN reloptions::text LIKE '%security_invoker=true%'
                 AND (SELECT string_agg(x::text, ',' ORDER BY x::text) FROM unnest(relacl) x)
                     = 'authenticated=r/postgres,postgres=arwdDxtm/postgres,service_role=arwdDxtm/postgres' THEN 'OK' ELSE '⛔ ECHEC' END
      FROM pg_class WHERE oid = 'public.app_contact_relations_current'::regclass;

    -- 3-6. LES TEMPS, D'ABORD (sous deux comptes réels)
    FOR u IN SELECT * FROM (VALUES
        (3, 'Frederic (admin)', 'd4b1685f-948b-4ce8-af15-671b94a725e6', '10354352', 200, 'fiche de JACQUIER'),
        (4, 'un commercial',    'c8a61bde-2899-443f-831b-3a4f5a8ec36b', '10354352', 400, 'fiche de JACQUIER'),
        (5, 'Frederic (admin)', 'd4b1685f-948b-4ce8-af15-671b94a725e6', '10166165', 800, 'fiche du notaire le plus charge (810 roles)'),
        (6, 'un commercial',    'c8a61bde-2899-443f-831b-3a4f5a8ec36b', '10166165', 1500, 'fiche du notaire le plus charge (810 roles)')) x(n, nom, sub, c, seuil, quoi) LOOP
        PERFORM set_config('request.jwt.claims', json_build_object('sub', u.sub, 'role', 'authenticated')::text, true);
        EXECUTE 'set local role authenticated';
        FOR i IN 1..3 LOOP
            EXECUTE format('explain (analyze, format json) select * from public.app_contact_relations_current where hektor_contact_id = %L order by last_seen_at desc', u.c) INTO j;
        END LOOP;
        EXECUTE 'reset role';
        ms := round((j->0->>'Execution Time')::numeric, 1);
        INSERT INTO repetition_not1 VALUES (u.n, u.quoi || ', ' || u.nom || ' : moins de ' || u.seuil || ' ms',
            CASE WHEN ms < u.seuil THEN 'OK (' || ms || ' ms)' ELSE '⛔ ECHEC (' || ms || ' ms)' END);
    END LOOP;

    -- 7. TÉMOIN INVERSE : la vue d'avant se reconstitue à l'octet
    k := replace(replace(replace(v, k_apres, k_avant), r_apres, r_avant), f_apres, f_avant);
    IF md5(k) <> '8c4d28d388a6325582013c5bfd08bc54' THEN
        INSERT INTO repetition_not1 VALUES (7, 'la vue d''avant se reconstitue a l''octet', '⛔ ECHEC (' || md5(k) || ')');
        RETURN;
    END IF;
    INSERT INTO repetition_not1 VALUES (7, 'la vue d''avant se reconstitue a l''octet (seuls les 3 remplacements ont change)', 'OK');
    EXECUTE 'create or replace temp view vue_d_avant with (security_invoker = true) as ' || rtrim(rtrim(k), ';');

    -- 8. RIEN NE SE PERD : toutes les lignes d'avant sont là, identiques (acheteurs, mandants, propriétaires)
    SELECT count(*) INTO perdues FROM (SELECT * FROM vue_d_avant EXCEPT ALL SELECT * FROM public.app_contact_relations_current) x;
    INSERT INTO repetition_not1 VALUES (8, 'toutes les lignes d''avant sont la, a l''identique (cles des acheteurs comprises)',
        CASE WHEN perdues = 0 THEN 'OK (' || (SELECT count(*) FROM vue_d_avant) || ' lignes)' ELSE '⛔ ECHEC (' || perdues || ' perdue(s))' END);
    -- 9. LES LIGNES NEUVES SONT EXACTEMENT LES NOTAIRES de la table des parties (vivants, avec un contact)
    SELECT count(*) INTO nouv FROM (SELECT * FROM public.app_contact_relations_current EXCEPT ALL SELECT * FROM vue_d_avant) x;
    SELECT count(*) INTO attendues FROM public.app_affaire_partie p JOIN public.app_affaire_ledger l ON l.app_affaire_id = p.app_affaire_id
     WHERE p.role IN ('notaire_vendeur', 'notaire_acquereur') AND p.app_contact_id IS NOT NULL
       AND NOT (btrim(coalesce(l.hektor_affaire_id, '')) <> '' AND l.present_in_hektor IS FALSE);
    SELECT string_agg(DISTINCT role_contact, ', ') INTO roles_neufs
      FROM (SELECT * FROM public.app_contact_relations_current EXCEPT ALL SELECT * FROM vue_d_avant) x;
    INSERT INTO repetition_not1 VALUES (9, 'les lignes neuves sont exactement les notaires de la table des parties (' || attendues || ')',
        CASE WHEN nouv = attendues AND roles_neufs = 'notaire_acquereur, notaire_vendeur' THEN 'OK (' || nouv || ' : ' || roles_neufs || ')'
             ELSE '⛔ ECHEC (' || nouv || ' : ' || coalesce(roles_neufs, '-') || ')' END);
    -- 10. aucune clé en double de plus qu'avant
    SELECT count(*) - count(DISTINCT relation_key) INTO doublons_neuf FROM public.app_contact_relations_current;
    SELECT count(*) - count(DISTINCT relation_key) INTO doublons_avant FROM vue_d_avant;
    INSERT INTO repetition_not1 VALUES (10, 'aucune cle en double de plus qu''avant (le meme notaire des deux cotes : cles distinctes)',
        CASE WHEN doublons_neuf <= doublons_avant THEN 'OK (' || doublons_neuf || ' avant ' || doublons_avant || ')' ELSE '⛔ ECHEC (' || doublons_neuf || ' contre ' || doublons_avant || ')' END);
    DROP VIEW IF EXISTS vue_d_avant;
END
$rep$;

-- 11. le notaire le plus chargé : ses dossiers apparaissent, sous ses deux côtés
INSERT INTO repetition_not1
SELECT 11, 'le notaire 10166165 : ses roles apparaissent (vendeur et acquereur)',
       CASE WHEN count(*) FILTER (WHERE role_contact = 'notaire_vendeur') > 0 AND count(*) FILTER (WHERE role_contact = 'notaire_acquereur') > 0
            THEN 'OK (' || count(*) || ' lignes)' ELSE '⛔ ECHEC (' || count(*) || ')' END
  FROM public.app_contact_relations_current WHERE hektor_contact_id = '10166165';

SELECT * FROM repetition_not1 ORDER BY 1;
