-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION — patch_catalogue_notaires_numeros_2026-11-09.sql
-- ═══════════════════════════════════════════════════════════════════════════
-- Pose l'index et la fonction DANS le bloc, essaie, puis finit par une erreur volontaire « RÉPÉTITION (annulée) : … »
-- qui porte les verdicts : RIEN n'est gardé. Hors du run de nuit (l'index bloque les écritures ~0,2 s ; lock_timeout 3 s).
-- Attendu : 8 OK, 0 KO.
-- ═══════════════════════════════════════════════════════════════════════════

DO $essai$
DECLARE
  v_admin uuid; v_nego uuid;
  ids text[]; anciens text[]; nb_new int; nb_old int; t0 timestamptz; ms_new numeric; ms_old numeric; p text := ''; r record;
  ok int := 0; ko int := 0; journal text := ''; v_refus text;
BEGIN
  SET LOCAL lock_timeout = '3s';
  EXECUTE $def$CREATE INDEX idx_app_contact_current_relation_roles_gin ON public.app_contact_current USING gin (relation_roles_json jsonb_path_ops)$def$;
  EXECUTE $def$CREATE FUNCTION public.app_catalogue_notaires_ids()
 RETURNS text[]
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $f$
BEGIN
  -- 09/11/2026 (note partenaires §28.10) : les NUMEROS des notaires du catalogue, et rien d'autre (ni nom, ni telephone,
  -- ni e-mail). Sous la regle d'acces, « @> » n'est pas LEAKPROOF : l'index des roles y est inutilisable et la lecture
  -- parcourait les 94 895 contacts (delai de 8 s depasse le 09/11 a 07:14, pendant le run). Ici, sans la regle, l'index
  -- sert (3,5 ms) ; l'ecran relit ensuite les fiches PAR NUMERO, sous la regle habituelle : le perimetre ne change pas.
  -- Meme regle qu'avant (CataloguePartenaires.tsx) : les deux cotes de la table des parties, archives compris.
  IF NOT public.is_app_user_active() THEN
    RAISE EXCEPTION '%', 'Compte inactif.' USING ERRCODE = '42501';
  END IF;
  RETURN coalesce((SELECT array_agg(c.hektor_contact_id ORDER BY c.hektor_contact_id)
                     FROM public.app_contact_current c
                    WHERE c.relation_roles_json @> '["notaire_vendeur"]'::jsonb
                       OR c.relation_roles_json @> '["notaire_acquereur"]'::jsonb), '{}'::text[]);
END
$f$$def$;
  EXECUTE $def$REVOKE ALL ON FUNCTION public.app_catalogue_notaires_ids() FROM PUBLIC$def$;
  EXECUTE $def$REVOKE ALL ON FUNCTION public.app_catalogue_notaires_ids() FROM anon$def$;
  EXECUTE $def$GRANT EXECUTE ON FUNCTION public.app_catalogue_notaires_ids() TO authenticated, service_role$def$;

  SELECT id INTO v_admin FROM public.app_user_profile WHERE role::text = 'admin' AND is_active ORDER BY id LIMIT 1;
  SELECT id INTO v_nego FROM public.app_user_profile WHERE role::text = 'commercial' AND is_active ORDER BY id LIMIT 1;

  -- 01. la fonction passe par l'index (lue comme son proprietaire)
  FOR r IN EXECUTE 'EXPLAIN SELECT hektor_contact_id FROM public.app_contact_current WHERE relation_roles_json @> ''["notaire_vendeur"]''::jsonb OR relation_roles_json @> ''["notaire_acquereur"]''::jsonb' LOOP
    p := p || r."QUERY PLAN"; END LOOP;
  IF p LIKE '%idx_app_contact_current_relation_roles_gin%' THEN ok := ok + 1; journal := journal || ' 01=ok'; ELSE ko := ko + 1; journal := journal || ' 01=KO pas d''index'; END IF;

  -- en admin (role authenticated, jeton simule)
  PERFORM set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  PERFORM set_config('request.jwt.claim.sub', v_admin::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  t0 := clock_timestamp(); ids := public.app_catalogue_notaires_ids(); ms_new := round(extract(epoch FROM clock_timestamp() - t0) * 1000, 1);
  t0 := clock_timestamp(); EXECUTE $q$SELECT array_agg(hektor_contact_id ORDER BY hektor_contact_id) FROM public.app_contact_current WHERE relation_roles_json @> '["notaire_vendeur"]' OR relation_roles_json @> '["notaire_acquereur"]'$q$ INTO anciens; ms_old := round(extract(epoch FROM clock_timestamp() - t0) * 1000, 1);
  -- 02. memes numeros que l'ancienne lecture (meme ordre, meme nombre)
  IF ids = anciens THEN ok := ok + 1; journal := journal || ' 02=ok(' || cardinality(ids) || ' notaires)';
  ELSE ko := ko + 1; journal := journal || ' 02=KO ' || coalesce(cardinality(ids), -1) || ' contre ' || coalesce(cardinality(anciens), -1); END IF;
  -- 03. les fiches relues par numero, sous la regle : autant que l'ancienne lecture
  SELECT count(*) INTO nb_new FROM public.app_contact_current WHERE hektor_contact_id = ANY (ids);
  IF nb_new = cardinality(anciens) THEN ok := ok + 1; journal := journal || ' 03=ok'; ELSE ko := ko + 1; journal := journal || ' 03=KO ' || nb_new; END IF;
  -- 04. plus rapide
  IF ms_new < ms_old THEN ok := ok + 1; journal := journal || ' 04=ok(' || ms_new || ' ms contre ' || ms_old || ' ms)';
  ELSE ko := ko + 1; journal := journal || ' 04=KO ' || ms_new || ' contre ' || ms_old; END IF;
  EXECUTE 'RESET ROLE';

  -- 05. un negociateur : la fonction rend les memes numeros ; ses fiches visibles = celles de l'ancienne lecture
  PERFORM set_config('request.jwt.claims', json_build_object('sub', v_nego, 'role', 'authenticated')::text, true);
  PERFORM set_config('request.jwt.claim.sub', v_nego::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  ids := public.app_catalogue_notaires_ids();
  SELECT count(*) INTO nb_new FROM public.app_contact_current WHERE hektor_contact_id = ANY (ids);
  EXECUTE 'SELECT count(*) FROM public.app_contact_current WHERE relation_roles_json @> ''["notaire_vendeur"]'' OR relation_roles_json @> ''["notaire_acquereur"]''' INTO nb_old;
  IF nb_new = nb_old THEN ok := ok + 1; journal := journal || ' 05=ok(' || nb_new || ' fiches)'; ELSE ko := ko + 1; journal := journal || ' 05=KO ' || nb_new || ' contre ' || nb_old; END IF;
  EXECUTE 'RESET ROLE';

  -- 06. un compte inconnu ou inactif est refuse
  v_refus := 'non refuse';
  BEGIN
    PERFORM set_config('request.jwt.claims', json_build_object('sub', gen_random_uuid(), 'role', 'authenticated')::text, true);
    PERFORM set_config('request.jwt.claim.sub', gen_random_uuid()::text, true);
    EXECUTE 'SET LOCAL ROLE authenticated';
    ids := public.app_catalogue_notaires_ids();
  EXCEPTION WHEN OTHERS THEN v_refus := SQLERRM;
  END;
  EXECUTE 'RESET ROLE';
  IF v_refus = 'Compte inactif.' THEN ok := ok + 1; journal := journal || ' 06=ok'; ELSE ko := ko + 1; journal := journal || ' 06=KO ' || v_refus; END IF;

  -- 07. droits : authenticated oui, anon non
  IF has_function_privilege('authenticated', 'public.app_catalogue_notaires_ids()', 'EXECUTE') AND NOT has_function_privilege('anon', 'public.app_catalogue_notaires_ids()', 'EXECUTE')
  THEN ok := ok + 1; journal := journal || ' 07=ok'; ELSE ko := ko + 1; journal := journal || ' 07=KO droits'; END IF;

  -- 08. l'index ne change PAS le chemin des puces de l'annuaire (elles restent sur leur tri)
  p := '';
  PERFORM set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  PERFORM set_config('request.jwt.claim.sub', v_admin::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  FOR r IN EXECUTE 'EXPLAIN SELECT hektor_contact_id FROM public.app_contacts_current WHERE archive = false AND relation_roles_json @> ''["mandant"]'' ORDER BY duplicate_group_count DESC NULLS LAST, date_enregistrement DESC NULLS LAST, display_name LIMIT 50' LOOP
    p := p || r."QUERY PLAN"; END LOOP;
  EXECUTE 'RESET ROLE';
  IF p NOT LIKE '%idx_app_contact_current_relation_roles_gin%' THEN ok := ok + 1; journal := journal || ' 08=ok'; ELSE ko := ko + 1; journal := journal || ' 08=KO l''annuaire change de chemin'; END IF;

  RAISE EXCEPTION 'RÉPÉTITION (annulée) : % OK, % KO --%', ok, ko, journal;
END
$essai$;
