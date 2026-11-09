-- RÉPÉTITION — patch_partenaire_du_client_2026-11-09.sql : pose la fonction et l'index DANS le bloc, essaie, finit par une erreur volontaire qui porte
-- les verdicts : RIEN n'est gardé. Attendu : 9 OK, 0 KO.
DO $essai$
DECLARE
  v_admin uuid; v_app text; v_client text; v_autre text; r jsonb; v_refus text; n int;
  ok int := 0; ko int := 0; journal text := '';
BEGIN
  SET LOCAL lock_timeout = '3s';
  EXECUTE $def$CREATE UNIQUE INDEX app_partenaire_lien_un_client_uidx ON public.app_partenaire_lien (role, client_contact_id, partenaire_id)
  WHERE objet = 'client' AND retire_le IS NULL$def$;
  EXECUTE $def$CREATE FUNCTION public.app_partenaire_du_client(p_role text, p_client text, p_partenaire text, p_retirer boolean DEFAULT false)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  v_client text := nullif(btrim(coalesce(p_client, '')), '');
  v_partenaire text := nullif(btrim(coalesce(p_partenaire, '')), '');
  v_metiers text[] := CASE p_role WHEN 'apporteur' THEN ARRAY['apporteur', 'parrain'] WHEN 'courtier' THEN ARRAY['courtier', 'banque'] END;
  v_id bigint;
BEGIN
  -- 09/11/2026 (note partenaires §28.17, lot 7) : relier un partenaire à un CLIENT (Q1 « A », dès le premier jour) —
  -- « Noter une affaire apportée ». Écrit CHEZ NOUS seulement (rien chez Hektor). Un même lien actif n'existe qu'une fois ;
  -- un retrait garde la trace (qui, quand). Rôle apporteur (métier apporteur ou parrain) ; courtier (courtier ou banque)
  -- préparé pour le lot 6.
  IF NOT public.is_app_user_active() THEN
    RAISE EXCEPTION '%', 'Compte inactif : le lien ne peut pas être écrit.' USING ERRCODE = '42501';
  END IF;
  IF v_metiers IS NULL THEN
    RAISE EXCEPTION '%', 'Rôle inconnu pour un client (apporteur ou courtier).';
  END IF;
  IF v_client IS NULL OR v_partenaire IS NULL THEN
    RAISE EXCEPTION '%', 'Le client et le partenaire sont obligatoires.';
  END IF;
  IF v_client = v_partenaire THEN
    RAISE EXCEPTION '%', 'Un partenaire ne peut pas s''apporter lui-même.';
  END IF;

  IF coalesce(p_retirer, false) THEN
    UPDATE public.app_partenaire_lien SET retire_le = now(), retire_par = auth.uid()
     WHERE objet = 'client' AND role = p_role AND client_contact_id = v_client AND partenaire_id = v_partenaire AND retire_le IS NULL
    RETURNING id INTO v_id;
    IF v_id IS NULL THEN RAISE EXCEPTION '%', 'Ce lien n''existe pas (ou il est déjà retiré).'; END IF;
    RETURN jsonb_build_object('action', 'retire', 'retire_id', v_id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM public.app_partenaire_metier
                  WHERE contact_id = v_partenaire AND metier = ANY (v_metiers) AND retire_le IS NULL) THEN
    RAISE EXCEPTION '%', 'Ce contact n''a pas le métier ' || array_to_string(v_metiers, ' ou ') || ' au catalogue des partenaires.';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.app_contact_current WHERE hektor_contact_id::text = v_client) THEN
    RAISE EXCEPTION '%', 'Client introuvable.';
  END IF;

  SELECT id INTO v_id FROM public.app_partenaire_lien
   WHERE objet = 'client' AND role = p_role AND client_contact_id = v_client AND partenaire_id = v_partenaire AND retire_le IS NULL;
  IF v_id IS NOT NULL THEN RETURN jsonb_build_object('action', 'inchange', 'id', v_id); END IF;

  INSERT INTO public.app_partenaire_lien (partenaire_id, role, objet, client_contact_id, origine, pose_par)
  VALUES (v_partenaire, p_role, 'client', v_client, 'app', auth.uid())
  RETURNING id INTO v_id;
  RETURN jsonb_build_object('action', 'pose', 'id', v_id);
END
$function$$def$;
  EXECUTE $def$REVOKE ALL ON FUNCTION public.app_partenaire_du_client(text,text,text,boolean) FROM PUBLIC$def$;
  EXECUTE $def$REVOKE ALL ON FUNCTION public.app_partenaire_du_client(text,text,text,boolean) FROM anon$def$;
  EXECUTE $def$GRANT EXECUTE ON FUNCTION public.app_partenaire_du_client(text,text,text,boolean) TO authenticated, service_role$def$;

  SELECT id INTO v_admin FROM public.app_user_profile WHERE role::text = 'admin' AND is_active ORDER BY id LIMIT 1;
  SELECT contact_id INTO v_app FROM public.app_partenaire_metier WHERE metier = 'apporteur' AND retire_le IS NULL ORDER BY id LIMIT 1;
  SELECT hektor_contact_id::text INTO v_client FROM public.app_contact_current
   WHERE relation_roles_json ? 'mandant' AND hektor_contact_id::text <> v_app ORDER BY hektor_contact_id LIMIT 1;
  SELECT contact_id INTO v_autre FROM public.app_partenaire_metier WHERE metier = 'syndic' AND retire_le IS NULL
   AND contact_id NOT IN (SELECT contact_id FROM public.app_partenaire_metier WHERE metier IN ('apporteur','parrain') AND retire_le IS NULL) ORDER BY id LIMIT 1;
  PERFORM set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  PERFORM set_config('request.jwt.claim.sub', v_admin::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';

  r := public.app_partenaire_du_client('apporteur', v_client, v_app, false);
  IF r->>'action' = 'pose' THEN ok := ok + 1; journal := journal || ' 01=ok'; ELSE ko := ko + 1; journal := journal || ' 01=KO ' || r::text; END IF;
  r := public.app_partenaire_du_client('apporteur', v_client, v_app, false);
  IF r->>'action' = 'inchange' THEN ok := ok + 1; journal := journal || ' 02=ok'; ELSE ko := ko + 1; journal := journal || ' 02=KO ' || r::text; END IF;
  EXECUTE 'RESET ROLE';
  SELECT count(*) INTO n FROM public.app_partenaire_lien WHERE objet = 'client' AND client_contact_id = v_client AND partenaire_id = v_app AND retire_le IS NULL AND origine = 'app' AND pose_par = v_admin;
  IF n = 1 THEN ok := ok + 1; journal := journal || ' 03=ok'; ELSE ko := ko + 1; journal := journal || ' 03=KO ' || n; END IF;
  EXECUTE 'SET LOCAL ROLE authenticated';

  v_refus := 'non refuse';
  BEGIN r := public.app_partenaire_du_client('apporteur', v_client, v_autre, false); EXCEPTION WHEN OTHERS THEN v_refus := SQLERRM; END;
  IF v_refus LIKE 'Ce contact n''a pas le métier%' THEN ok := ok + 1; journal := journal || ' 04=ok'; ELSE ko := ko + 1; journal := journal || ' 04=KO ' || v_refus; END IF;
  v_refus := 'non refuse';
  BEGIN r := public.app_partenaire_du_client('syndic', v_client, v_app, false); EXCEPTION WHEN OTHERS THEN v_refus := SQLERRM; END;
  IF v_refus LIKE 'Rôle inconnu%' THEN ok := ok + 1; journal := journal || ' 05=ok'; ELSE ko := ko + 1; journal := journal || ' 05=KO ' || v_refus; END IF;
  v_refus := 'non refuse';
  BEGIN r := public.app_partenaire_du_client('apporteur', v_app, v_app, false); EXCEPTION WHEN OTHERS THEN v_refus := SQLERRM; END;
  IF v_refus LIKE 'Un partenaire ne peut pas%' THEN ok := ok + 1; journal := journal || ' 06=ok'; ELSE ko := ko + 1; journal := journal || ' 06=KO ' || v_refus; END IF;

  r := public.app_partenaire_du_client('apporteur', v_client, v_app, true);
  IF r->>'action' = 'retire' THEN ok := ok + 1; journal := journal || ' 07=ok'; ELSE ko := ko + 1; journal := journal || ' 07=KO ' || r::text; END IF;
  EXECUTE 'RESET ROLE';
  SELECT count(*) INTO n FROM public.app_partenaire_lien WHERE objet = 'client' AND client_contact_id = v_client AND partenaire_id = v_app AND retire_le IS NOT NULL AND retire_par = v_admin;
  IF n = 1 THEN ok := ok + 1; journal := journal || ' 08=ok'; ELSE ko := ko + 1; journal := journal || ' 08=KO ' || n; END IF;
  IF has_function_privilege('authenticated', 'public.app_partenaire_du_client(text,text,text,boolean)', 'EXECUTE') AND NOT has_function_privilege('anon', 'public.app_partenaire_du_client(text,text,text,boolean)', 'EXECUTE')
  THEN ok := ok + 1; journal := journal || ' 09=ok'; ELSE ko := ko + 1; journal := journal || ' 09=KO droits'; END IF;

  RAISE EXCEPTION 'RÉPÉTITION (annulée) : % OK, % KO --% (apporteur %, client %)', ok, ko, journal, v_app, v_client;
END
$essai$;
