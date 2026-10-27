-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — P2 : les deux colonnes de la vue des liens d'un contact             27/10/2026
-- Lecture seule (une table temporaire de résultats, une vue temporaire « d'avant » pour le témoin inverse).
-- À rejouer après la pose, puis le lendemain de la première nuit.
-- ⚠ Les temps se mesurent SOUS LE COMPTE de l'utilisateur (rôle authenticated + son identifiant), jamais en
--   service_role (il ignore la RLS) — même méthode que patch_fiche_contact_vitesse_2026-10-26_REPETITION.sql.
-- Contacts témoins : 10354352 (JACQUIER, bien 61730 : propriétaire depuis la vente + offre, compromis, vente)
--                    10354701 (M. Emrick HUGUES, le témoin de la vitesse du 26/10).
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TEMP TABLE IF NOT EXISTS repetition_p2 (n int, controle text, verdict text);
TRUNCATE repetition_p2;

DO $rep$
DECLARE
    v      text := replace(pg_get_viewdef('public.app_contact_relations_current'::regclass), chr(13), '');
    cols   text;
    j      json;
    plan   text;
    ms     numeric;
    u      record;
    i      int;
    ecarts int;
BEGIN
    -- 1. les 20 colonnes : les 18 d'avant, dans le même ordre et du même type, puis les deux neuves
    SELECT string_agg(attname || ':' || format_type(atttypid, atttypmod), ', ' ORDER BY attnum) INTO cols
      FROM pg_attribute WHERE attrelid = 'public.app_contact_relations_current'::regclass AND attnum > 0 AND NOT attisdropped;
    INSERT INTO repetition_p2 VALUES (1, 'les 18 colonnes d''avant inchangees, puis origine et proprietaire_depuis',
        CASE WHEN cols = 'relation_key:text, hektor_contact_id:text, hektor_annonce_id:text, app_dossier_id:bigint, numero_dossier:text, '
                      || 'numero_mandat:text, titre_bien:text, role_contact:text, contact_date_maj:text, relation_source:text, '
                      || 'transaction_type:text, transaction_id:text, transaction_state:text, transaction_date:text, '
                      || 'transaction_amount:text, is_active_annonce:boolean, last_seen_at:text, refreshed_at:text, '
                      || 'origine:text, proprietaire_depuis:text'
             THEN 'OK' ELSE '⛔ ECHEC (' || cols || ')' END);

    -- 2. la vue garde security_invoker et ses droits
    INSERT INTO repetition_p2
    SELECT 2, 'security_invoker garde, droits inchanges',
           CASE WHEN reloptions::text LIKE '%security_invoker=true%'
                 AND (SELECT string_agg(x::text, ',' ORDER BY x::text) FROM unnest(relacl) x) = 'authenticated=r/postgres,postgres=arwdDxtm/postgres,service_role=arwdDxtm/postgres'
                THEN 'OK' ELSE '⛔ ECHEC (' || coalesce(reloptions::text, '-') || ' ' || coalesce(relacl::text, '-') || ')' END
      FROM pg_class WHERE oid = 'public.app_contact_relations_current'::regclass;

    -- 3. TÉMOIN INVERSE : la vue d'avant se reconstitue À L'OCTET en retirant les deux ajouts
    v := replace(v, 'r.last_seen_at AS refreshed_at,' || chr(10) || '    r.origine,' || chr(10) || '    r.proprietaire_depuis',
                    'r.last_seen_at AS refreshed_at');
    v := replace(v, '(l.last_seen_at)::text AS refreshed_at,' || chr(10) || '    NULL::text AS origine,' || chr(10) || '    NULL::text AS proprietaire_depuis',
                    '(l.last_seen_at)::text AS refreshed_at');
    IF md5(v) <> 'd4350c631503f1ecedf99d28bee16c04' THEN
        INSERT INTO repetition_p2 VALUES (3, 'la vue d''avant se reconstitue a l''octet', '⛔ ECHEC (' || md5(v) || ')');
        RETURN;
    END IF;
    INSERT INTO repetition_p2 VALUES (3, 'la vue d''avant se reconstitue a l''octet (seuls les deux ajouts ont change)', 'OK');
    EXECUTE 'create or replace temp view vue_d_avant with (security_invoker = true) as ' || rtrim(rtrim(v), ';');
    GRANT SELECT ON vue_d_avant TO authenticated;

    -- 4. les MÊMES lignes, sur les contacts qui ont plusieurs rôles sur un bien (le périmètre de P2) — dans les deux sens
    DROP TABLE IF EXISTS p2_contacts;
    CREATE TEMP TABLE p2_contacts AS
      SELECT app_contact_id_texte AS c FROM public.app_relation WHERE origine IS NOT NULL
      UNION SELECT '10354352' UNION SELECT '10354701';
    SELECT count(*) INTO ecarts FROM (
        (SELECT relation_key, hektor_contact_id, hektor_annonce_id, app_dossier_id, numero_dossier, numero_mandat, titre_bien,
                role_contact, contact_date_maj, relation_source, transaction_type, transaction_id, transaction_state,
                transaction_date, transaction_amount, is_active_annonce, last_seen_at, refreshed_at
           FROM public.app_contact_relations_current WHERE hektor_contact_id IN (SELECT c FROM p2_contacts)
         EXCEPT ALL
         SELECT * FROM vue_d_avant WHERE hektor_contact_id IN (SELECT c FROM p2_contacts))
        UNION ALL
        (SELECT * FROM vue_d_avant WHERE hektor_contact_id IN (SELECT c FROM p2_contacts)
         EXCEPT ALL
         SELECT relation_key, hektor_contact_id, hektor_annonce_id, app_dossier_id, numero_dossier, numero_mandat, titre_bien,
                role_contact, contact_date_maj, relation_source, transaction_type, transaction_id, transaction_state,
                transaction_date, transaction_amount, is_active_annonce, last_seen_at, refreshed_at
           FROM public.app_contact_relations_current WHERE hektor_contact_id IN (SELECT c FROM p2_contacts))) x;
    INSERT INTO repetition_p2 SELECT 4, 'les memes lignes que la vue d''avant, dans les deux sens (' || count(*) || ' contacts temoins)',
        CASE WHEN ecarts = 0 THEN 'OK' ELSE '⛔ ECHEC (' || ecarts || ' ecart(s))' END FROM p2_contacts;

    -- 6-7. le temps de la fiche, sous deux comptes réels (seuils du 26/10 : 200 ms admin, 400 ms commercial)
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
        INSERT INTO repetition_p2 VALUES (5 + u.n, 'fiche de JACQUIER, ' || u.nom || ' : moins de ' || u.seuil || ' ms, index texte servis',
            CASE WHEN ms < u.seuil AND position('"idx_app_relation_contact_id_texte"' in plan) > 0
                  AND position('"idx_app_affaire_partie_contact_id_texte"' in plan) > 0 THEN 'OK (' || ms || ' ms)'
                 ELSE '⛔ ECHEC (' || ms || ' ms)' END);
    END LOOP;
    DROP VIEW IF EXISTS vue_d_avant;
END
$rep$;

-- 8-11. ce que disent les deux colonnes
INSERT INTO repetition_p2
SELECT 8, 'chaque lien « ne de la vente » visible porte origine et date dans la vue',
       CASE WHEN (SELECT count(*) FROM public.app_contact_relations_current WHERE origine = 'vente' AND proprietaire_depuis IS NOT NULL)
               = (SELECT count(*) FROM public.app_relation r
                   WHERE r.origine = 'vente' AND r.retire_le IS NULL
                     AND (r.present_in_hektor OR (r.source = 'app' AND r.absent_depuis IS NULL)))
             AND (SELECT count(*) FROM public.app_contact_relations_current WHERE origine = 'vente') > 0
            THEN 'OK (' || (SELECT count(*) FROM public.app_contact_relations_current WHERE origine = 'vente') || ')' ELSE '⛔ ECHEC' END
UNION ALL
SELECT 9, 'une ligne d''origine « vente » est toujours « proprietaire » (jamais mandant)',
       CASE WHEN count(*) = 0 THEN 'OK' ELSE '⛔ ECHEC (' || count(*) || ')' END
  FROM public.app_contact_relations_current WHERE origine = 'vente' AND role_contact <> 'proprietaire'
UNION ALL
SELECT 10, 'les lignes du registre des transactions n''ont jamais d''origine (JACQUIER)',
       CASE WHEN count(*) = 0 THEN 'OK' ELSE '⛔ ECHEC (' || count(*) || ')' END
  FROM public.app_contact_relations_current
 WHERE hektor_contact_id = '10354352' AND relation_source = 'registre_transactions' AND (origine IS NOT NULL OR proprietaire_depuis IS NOT NULL)
UNION ALL
SELECT 11, 'JACQUIER : proprietaire de 61730 depuis le 2026-09-25',
       CASE WHEN count(*) = 1 THEN 'OK' ELSE '⛔ ECHEC (' || count(*) || ')' END
  FROM public.app_contact_relations_current
 WHERE hektor_contact_id = '10354352' AND hektor_annonce_id = '61730' AND role_contact = 'proprietaire'
   AND origine = 'vente' AND proprietaire_depuis = '2026-09-25';

SELECT * FROM repetition_p2 ORDER BY 1;
