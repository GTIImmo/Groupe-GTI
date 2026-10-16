-- ============================================================================
-- INVERSE de patch_chantier7_archiver_contact_recherches_2026-10-16.sql
-- 16/10/2026
-- ============================================================================
-- Il retire le bloc « les recherches actives » de
-- app_console_archiver_contact_optimistic, et RIEN d'autre.
--
-- ⚠ IL NE DEFAIT PAS LES DONNEES. Les recherches deja archivees par le geste
--   restent archivees, et leurs etats d'avant restent dans `app_search_pending`
--   (c'est justement a ca qu'ils servent). Retirer le code n'est pas revenir en
--   arriere sur ce qui a ete ecrit.
--
-- ⚠ IL COUPE ENTRE DEUX BORNES, pas avec une regex : le bloc est encadre par
--     -- BLOC RECHERCHES ARCHIVEES -- DEBUT
--     -- BLOC RECHERCHES ARCHIVEES -- FIN
--   Il verifie ensuite qu'il ne reste AUCUNE trace, puis AFFICHE si l'empreinte
--   d'origine est retrouvee (85e3c91d...). L'empreinte n'est pas un veto : si un
--   autre patch est passe sur cette fonction depuis, il le DIT au lieu de bloquer
--   (lecon du 15/10 : un retour arriere ne juge que SA part).
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
  v_borne_d text := replace('  -- BLOC RECHERCHES ARCHIVEES -- DEBUT', chr(13), '');
  v_borne_f text := replace('  -- BLOC RECHERCHES ARCHIVEES -- FIN', chr(13), '');
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_console_archiver_contact_optimistic';

  if v_src is null then
    raise exception 'STOP : app_console_archiver_contact_optimistic introuvable';
  end if;

  if position('BLOC RECHERCHES ARCHIVEES' in v_src) = 0 then
    raise notice 'RIEN A RETIRER : le bloc n''est pas la (deja propre)';
    return;
  end if;

  v_debut := position(v_borne_d in v_src);
  v_fin   := position(v_borne_f in v_src);
  if v_debut = 0 or v_fin = 0 or v_fin <= v_debut then
    raise exception 'STOP : bornes introuvables ou dans le desordre (debut=%, fin=%)', v_debut, v_fin;
  end if;

  -- on coupe de la borne de debut jusqu'a la fin de la borne de fin, saut de ligne compris
  v_new := substr(v_src, 1, v_debut - 1) || substr(v_src, v_fin + length(v_borne_f) + 1);
  execute v_new;

  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_apres
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_console_archiver_contact_optimistic';

  if position('BLOC RECHERCHES ARCHIVEES' in v_apres) > 0
     or position('app_search_pending' in v_apres) > 0 then
    raise exception 'STOP : il reste une trace du bloc dans la fonction';
  end if;

  if md5(v_apres) = '85e3c91dc701b4a60d9e2fb07d805e4d' then
    raise notice 'RETIRE : empreinte d''origine retrouvee (85e3c91d...)';
  else
    raise notice 'RETIRE (0 trace), mais l''empreinte est % et non 85e3c91d... -- un AUTRE patch est passe sur cette fonction depuis le 16/10. Ce n''est pas une erreur de cet inverse.', md5(v_apres);
  end if;
end
$do$;

commit;
