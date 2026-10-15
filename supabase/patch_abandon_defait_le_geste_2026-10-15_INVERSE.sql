-- =============================================================================
--  RETOUR ARRIERE du patch « abandonner defait le geste »         15/10/2026
-- =============================================================================
--  Il retire les quatre morceaux ajoutes et verifie qu'il retombe sur l'empreinte
--  mesuree AVANT le patch (5590da3aff0e57512d8fb69c13abab2d). Si ce n'est pas le
--  cas, il annule tout : mieux vaut ne rien faire que laisser un hybride.
--
--  ⚠ CE QU'ON PERD EN REVENANT EN ARRIERE : « Abandonner ce geste » redevient un
--    bouton qui ne fait QUE masquer l'alerte. La valeur ecrite par l'app reste en
--    place alors que Hektor ne l'a jamais recue, et plus rien ne le dit. C'est
--    exactement le defaut du 15/10.
--
--  ⚠ CE PATCH NE REND PAS LES VALEURS DEJA DEFAITES. Un abandon deja clique a
--    efface une ligne de carnet et remis une valeur de fiche : revenir en arriere
--    sur la FONCTION ne les remet pas. Le compte-rendu de chaque abandon est garde
--    dans app_pending_resolution.payload_json->'defait' -- c'est la qu'on lit ce
--    qui a ete defait, et c'est de la qu'on le remettrait a la main :
--      SELECT resolved_at, app_dossier_id, payload_json->'defait'
--        FROM app_pending_resolution
--       WHERE objet = 'geste' AND mode = 'abandon'
--         AND jsonb_array_length(coalesce(payload_json->'defait','[]'::jsonb)) > 0
--       ORDER BY resolved_at DESC;
-- =============================================================================

DO $patch$
DECLARE
  v_corps text;
  v_apres text;
  v_debut int;
  v_fin   int;
BEGIN
  SELECT pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure) INTO v_corps;

  IF position('@abandon-debut' in v_corps) = 0 THEN
    RAISE NOTICE 'RIEN A FAIRE : le patch n''est pas pose.';
    RETURN;
  END IF;

  -- ② le bloc de retour arriere, entre ses deux bornes nommees
  v_debut := position('  -- @abandon-debut' in v_corps);
  v_fin   := position('  -- @abandon-fin' in v_corps);
  IF v_debut = 0 OR v_fin = 0 OR v_fin <= v_debut THEN
    RAISE EXCEPTION 'STOP : les bornes @abandon-debut / @abandon-fin sont introuvables ou inversees';
  END IF;
  v_corps := left(v_corps, v_debut - 1)
          || substr(v_corps, v_fin + length('  -- @abandon-fin') + 2);

  -- ① les declarations
  v_corps := replace(v_corps,
    $vieux$  -- @abandon (15/10/2026) : de quoi defaire ce que l'app avait ecrit.
  v_defait jsonb := '[]'::jsonb;
  v_champ  record;
  v_avant  text;
  v_fiche  int;
$vieux$, '');

  -- ③ la trace
  v_corps := replace(v_corps,
    $vieux$     jsonb_build_object('defait', v_defait,
                        'job_id', target_job_id::text,$vieux$,
    $vieux$     jsonb_build_object('job_id', target_job_id::text,$vieux$);

  -- ④ le compte-rendu
  v_corps := replace(v_corps,
    $vieux$  return jsonb_build_object('resolved', true, 'mode', mode, 'job_type', j.job_type,
                            'defait', v_defait,
                            'champs_defaits', jsonb_array_length(v_defait));$vieux$,
    $vieux$  return jsonb_build_object('resolved', true, 'mode', mode, 'job_type', j.job_type);$vieux$);

  EXECUTE v_corps;

  SELECT md5(replace(pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure), chr(13), ''))
    INTO v_apres;

  IF v_apres <> '5590da3aff0e57512d8fb69c13abab2d' THEN
    RAISE EXCEPTION 'STOP : on ne retombe PAS sur l''empreinte d''origine (%). Rien n''est sur, on annule tout.', v_apres;
  END IF;

  RAISE NOTICE 'RETIRE : la fonction est revenue a son empreinte du 15/10 avant patch.';
END $patch$;

COMMENT ON FUNCTION public.app_action_resolve(uuid,text) IS
  'Trancher un geste abandonne (C.4-bis, 01/09/2026). Les deux modes ecrivent une '
  'trace dans app_pending_resolution, qui fait sortir la ligne du bandeau. Le '
  'travail lui-meme n''est pas touche : il est de l''historique.';

-- Controle : plus aucune trace du correctif.
SELECT (position('@abandon' in pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure)) = 0) AS doit_valoir_true,
       md5(replace(pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure), chr(13), '')) AS empreinte;
