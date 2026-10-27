-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — ÉTAPE 2, la nuit : le calcul pour tous et la ligne de suivi                 27/10/2026
-- ⚠ Le contrôle 4 APPELLE le calcul pour tous POUR DE VRAI : il remet nos registres là où le type diffère (c'est son
--   métier ; mesuré le 27/10 : 7 contacts, §34.2). Le contrôle 3 dit d'abord combien il va en toucher.
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TEMP TABLE IF NOT EXISTS repetition_tnuit (n int, controle text, verdict text);
TRUNCATE repetition_tnuit;

DO $rep$
DECLARE avant int; n1 int; n2 int; t0 timestamptz; ms numeric; ecarts_regle int;
BEGIN
    INSERT INTO repetition_tnuit
    SELECT 1, 'la fonction existe, interne (ni anon ni authenticated), SECURITY DEFINER',
           CASE WHEN count(*) = 1 AND bool_and(pr.prosecdef)
                 AND NOT bool_or(has_function_privilege('authenticated', pr.oid, 'EXECUTE'))
                 AND NOT bool_or(has_function_privilege('anon', pr.oid, 'EXECUTE'))
                 AND bool_and(has_function_privilege('service_role', pr.oid, 'EXECUTE')) THEN 'OK' ELSE '⛔ ECHEC' END
      FROM pg_proc pr JOIN pg_namespace s ON s.oid = pr.pronamespace
     WHERE s.nspname = 'public' AND pr.proname = 'app_recalculer_tous_les_types';
    INSERT INTO repetition_tnuit
    SELECT 2, 'la ligne de suivi supabase.type_contacts existe (copiee de sa soeur, etape facultative)',
           CASE WHEN count(*) = 1 AND bool_and(w.frequency = 'optional_pipeline_step' AND w.status = 'active'
                                              AND w.script_path = 'phase2/sync/recalculer_types_contacts.py') THEN 'OK' ELSE '⛔ ECHEC' END
      FROM public.app_worker_registry w WHERE w.worker_key = 'supabase.type_contacts';

    -- 3. combien de contacts le calcul va toucher (ceux dont le type diffère de nos registres)
    -- ⚠ ENSEMBLISTE (une lecture de la vue) : appeler le calcul d'UN contact sur les 62 339 prendrait plus de 13 min
    WITH v AS (SELECT d.c, jsonb_agg(d.r ORDER BY d.r COLLATE "C") AS roles
                 FROM (SELECT DISTINCT x.hektor_contact_id AS c, x.role_contact AS r FROM public.app_contact_relations_current x) d GROUP BY d.c)
    SELECT count(*) INTO avant FROM public.app_contact_current k LEFT JOIN v ON v.c = k.hektor_contact_id
     WHERE k.relation_roles_json IS DISTINCT FROM coalesce(v.roles, '[]'::jsonb);
    INSERT INTO repetition_tnuit VALUES (3, 'avant le calcul : contacts dont le type differe de nos registres', 'OK (' || avant || ')');

    -- 4-5. le calcul pour tous, puis une seconde fois (rien à écrire)
    t0 := clock_timestamp();
    n1 := public.app_recalculer_tous_les_types();
    ms := round(extract(epoch FROM clock_timestamp() - t0) * 1000);
    INSERT INTO repetition_tnuit VALUES (4, 'le calcul pour tous touche exactement ces contacts, en moins de 20 s',
        CASE WHEN n1 = avant AND ms < 20000 THEN 'OK (' || n1 || ' contact(s), ' || ms || ' ms)' ELSE '⛔ ECHEC (' || n1 || ' contre ' || avant || ', ' || ms || ' ms)' END);
    n2 := public.app_recalculer_tous_les_types();
    INSERT INTO repetition_tnuit VALUES (5, 'une seconde fois, il n''ecrit rien', CASE WHEN n2 = 0 THEN 'OK' ELSE '⛔ ECHEC (' || n2 || ')' END);

    -- 6. LA MÊME RÈGLE que le calcul au geste : après le calcul pour tous, plus AUCUN écart avec app_type_depuis_nos_registres
    -- (sur 2 000 contacts pris dans tout l'annuaire, un sur 31 : le calcul d'UN contact coute ~13 ms)
    SELECT count(*) INTO ecarts_regle
      FROM (SELECT hektor_contact_id, relation_roles_json, row_number() OVER (ORDER BY hektor_contact_id) rn FROM public.app_contact_current) k
     WHERE k.rn % 31 = 0 AND k.rn <= 62000
       AND k.relation_roles_json IS DISTINCT FROM public.app_type_depuis_nos_registres(k.hektor_contact_id);
    INSERT INTO repetition_tnuit VALUES (6, 'la meme regle qu''au geste : 0 ecart avec le calcul d''un seul contact (2 000 contacts sur tout l''annuaire)',
        CASE WHEN ecarts_regle = 0 THEN 'OK' ELSE '⛔ ECHEC (' || ecarts_regle || ')' END);
END
$rep$;

SELECT * FROM repetition_tnuit ORDER BY 1;
