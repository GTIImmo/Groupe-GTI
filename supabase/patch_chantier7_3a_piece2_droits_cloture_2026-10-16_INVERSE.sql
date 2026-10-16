-- ============================================================================
-- INVERSE de patch_chantier7_3a_piece2_droits_cloture_2026-10-16.sql
-- 16/10/2026
-- ============================================================================
-- Il retire la garde manager/admin de app_set_mandat_cloture_optimistic, et
-- RIEN d autre. La fonction redevient ouverte a tout utilisateur connecte, comme
-- elle l etait jusqu au 16/10 (decision du 13/10).
--
-- ⚠ IL NE DEFAIT PAS LES DONNEES : les dates de cloture deja ecrites restent
--   ecrites. Retirer une garde n est pas revenir en arriere sur ce qui a ete
--   saisi -- et de toute facon cette garde n ecrit rien, elle refuse.
--
-- ⚠ IL COUPE ENTRE DEUX BORNES, pas avec une regex :
--     -- GARDE MANAGER ADMIN -- DEBUT
--     -- GARDE MANAGER ADMIN -- FIN
--   Il verifie ensuite qu il ne reste AUCUNE TRACE (ni les bornes, ni l appel a
--   is_app_manager_or_admin, ni le mot droits_insuffisants), PUIS il AFFICHE si
--   l empreinte d origine est retrouvee (09280b46...). L empreinte n est pas un
--   veto : si un autre patch est passe sur cette fonction depuis, il le DIT au
--   lieu de bloquer (lecon du 15/10 : un retour arriere ne juge que SA part).
--
-- ⚠ Toutes les bornes sont enveloppees de replace(..., chr(13), '') : collees
--   depuis Windows elles arriveraient en CRLF et ne se retrouveraient pas dans
--   un corps stocke en LF (lecon du 15/10, la 3e fois).
-- ============================================================================

begin;

set local lock_timeout = '5s';

do $do$
declare
  v_src     text;
  v_new     text;
  v_apres   text;
  v_debut   integer;
  v_fin     integer;
  v_borne_d text := replace('  -- GARDE MANAGER ADMIN -- DEBUT', chr(13), '');
  v_borne_f text := replace('  -- GARDE MANAGER ADMIN -- FIN', chr(13), '');
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_set_mandat_cloture_optimistic';

  if v_src is null then
    raise exception 'STOP : app_set_mandat_cloture_optimistic introuvable';
  end if;

  if position('GARDE MANAGER ADMIN' in v_src) = 0 then
    raise notice 'RIEN A RETIRER : la garde n est pas la (deja propre)';
    return;
  end if;

  v_debut := position(v_borne_d in v_src);
  v_fin   := position(v_borne_f in v_src);
  if v_debut = 0 or v_fin = 0 or v_fin <= v_debut then
    raise exception 'STOP : bornes introuvables ou dans le desordre (debut=%, fin=%)', v_debut, v_fin;
  end if;

  -- on coupe de la borne de debut jusqu a la fin de la borne de fin, saut de
  -- ligne compris : le texte doit retomber EXACTEMENT sur celui d avant.
  v_new := substr(v_src, 1, v_debut - 1) || substr(v_src, v_fin + length(v_borne_f) + 1);
  execute v_new;

  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_apres
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_set_mandat_cloture_optimistic';

  if position('GARDE MANAGER ADMIN' in v_apres) > 0
     or position('is_app_manager_or_admin' in v_apres) > 0
     or position('droits_insuffisants' in v_apres) > 0 then
    raise exception 'STOP : il reste une trace de la garde dans la fonction';
  end if;

  if md5(v_apres) = '09280b46e6832db15dce53ca5e30e9db' then
    raise notice 'RETIRE : empreinte d origine retrouvee (09280b46...)';
  else
    raise notice 'RETIRE (0 trace), mais l empreinte est % et non 09280b46... -- un AUTRE patch est passe sur cette fonction depuis le 16/10. Ce n est pas une erreur de cet inverse.', md5(v_apres);
  end if;
end
$do$;

commit;
