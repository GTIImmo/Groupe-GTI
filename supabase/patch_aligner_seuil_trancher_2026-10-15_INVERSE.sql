-- =============================================================================
--  RETOUR ARRIERE du patch « aligner le seuil du bouton »         15/10/2026
-- =============================================================================
--  Il remet `>= 5` dans les deux fonctions et retire le repli vendus/clos.
--
--  ⚠ CE QU'ON PERD EN REVENANT EN ARRIERE : un travail dont le type n'est pas
--    rejouable redevient IMPOSSIBLE A TRANCHER (il n'atteindra jamais 5
--    tentatives), et un bien VENDU, CLOS ou ARCHIVE n'affiche plus son bandeau du
--    tout. C'est exactement le defaut du 15/10 : l'alerte sonne, et il n'y a nulle
--    part ou cliquer.
--
--  ⚠ CE PATCH NE DEFAIT PAS LES ABANDONS DEJA CLIQUES. Les lignes de
--    app_pending_resolution restent, et les valeurs deja remises restent remises.
--    Voir le retour arriere du patch frere (patch_abandon_defait_le_geste_*_INVERSE)
--    pour savoir ou lire ce qui a ete defait.
-- =============================================================================

DO $patch$
DECLARE
  v_corps text;
  v_debut int;
  v_fin   int;
  n1 CONSTANT text := $vieux$  -- @seuil-3h (15/10/2026) : la MEME regle que la vue app_en_attente_humain.
  -- Un travail dont le type n'est pas rejouable n'atteindra JAMAIS 5 tentatives :
  -- il etait donc visible dans le moniteur et impossible a trancher. Passe 3 h
  -- (le filet epuise ses 5 tentatives en 50 min : marge x3,6), on laisse l'humain
  -- decider. Les 3 heures sont mesurees, pas choisies.
  if j.status <> 'error'
     or (coalesce(j.attempt_count, 0) < 5
         and j.requested_at >= now() - interval '3 hours') then$vieux$;
  a1 CONSTANT text := '  if j.status <> ''error'' or coalesce(j.attempt_count, 0) < 5 then';
BEGIN
  SELECT pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure) INTO v_corps;
  IF position('@seuil-3h' in v_corps) = 0 THEN
    RAISE NOTICE 'RIEN A FAIRE (app_action_resolve) : le patch n''est pas pose.';
  ELSE
    IF position(n1 in v_corps) = 0 THEN
      RAISE EXCEPTION 'STOP : le bloc du seuil n''est pas celui qu''on a pose -- on ne touche a rien';
    END IF;
    EXECUTE replace(v_corps, n1, a1);
    RAISE NOTICE 'RETIRE : app_action_resolve est revenue a >= 5 tentatives.';
  END IF;
END $patch$;

DO $patch$
DECLARE
  v_corps text;
  v_debut int;
  v_fin   int;
  n1 CONSTANT text := $vieux$     -- @seuil-3h (15/10/2026) : la MEME regle que la vue app_en_attente_humain.
     and (coalesce(j.attempt_count, 0) >= 5
          or j.requested_at < now() - interval '3 hours')$vieux$;
  a1 CONSTANT text := '     and coalesce(j.attempt_count, 0) >= 5';
  a2 CONSTANT text := $vieux$  if d.app_dossier_id is null then
    raise exception 'dossier_not_found' using errcode = '22023';
  end if;$vieux$;
BEGIN
  SELECT pg_get_functiondef('public.app_action_status(bigint)'::regprocedure) INTO v_corps;
  IF position('@repli-trancher' in v_corps) = 0 THEN
    RAISE NOTICE 'RIEN A FAIRE (app_action_status) : le patch n''est pas pose.';
    RETURN;
  END IF;

  -- ① le seuil
  IF position(n1 in v_corps) = 0 THEN
    RAISE EXCEPTION 'STOP : le bloc du seuil (status) n''est pas celui qu''on a pose';
  END IF;
  v_corps := replace(v_corps, n1, a1);

  -- ② le repli, entre sa borne nommee et le dernier `raise dossier_not_found`
  v_debut := position(E'\n\n  -- @repli-trancher' in v_corps);
  v_fin   := position(a2 in v_corps);
  IF v_debut = 0 OR v_fin = 0 OR v_fin <= v_debut THEN
    RAISE EXCEPTION 'STOP : les bornes du repli sont introuvables ou inversees';
  END IF;
  v_corps := left(v_corps, v_debut - 1)
          || E'\n  if not found then raise exception ''dossier_not_found'' using errcode = ''22023''; end if;'
          || substr(v_corps, v_fin + length(a2));

  EXECUTE v_corps;

  IF position('@repli-trancher' in pg_get_functiondef('public.app_action_status(bigint)'::regprocedure)) > 0
     OR position('@seuil-3h' in pg_get_functiondef('public.app_action_status(bigint)'::regprocedure)) > 0 THEN
    RAISE EXCEPTION 'STOP : il reste des traces du patch dans app_action_status';
  END IF;
  RAISE NOTICE 'RETIRE : app_action_status est revenue a >= 5 tentatives, sans repli.';
END $patch$;

COMMENT ON FUNCTION public.app_action_status(bigint) IS
  'Les gestes abandonnes d''un bien, pour le bandeau de sa fiche (C.4-bis, '
  '01/09/2026). Regle : 5 tentatives epuisees, et le bien doit etre dans le parc '
  'vivant.';

-- Controle : plus aucune trace, dans les deux fonctions.
SELECT (position('@seuil-3h' in pg_get_functiondef('public.app_action_resolve(uuid,text)'::regprocedure)) = 0) AS resolve_propre,
       (position('@seuil-3h' in pg_get_functiondef('public.app_action_status(bigint)'::regprocedure)) = 0)     AS status_propre,
       (position('@repli-trancher' in pg_get_functiondef('public.app_action_status(bigint)'::regprocedure)) = 0) AS repli_retire;
