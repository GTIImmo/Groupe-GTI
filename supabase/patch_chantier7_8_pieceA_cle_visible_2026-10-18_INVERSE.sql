-- ============================================================================
-- INVERSE de (7)-8 piece A -- retirer la cle `visible` de la galerie
-- 18/10/2026
-- ============================================================================
-- Il retire EXACTEMENT ce que le patch a ajoute, puis verifie qu'il retombe sur
-- l'empreinte d'origine.
--
-- ⚠ LECON DU 15/10 (un retour arriere ne juge que SA part) : si une AUTRE
--   modification est passee entre-temps, il defait quand meme sa part, le DIT,
--   et NE BLOQUE PAS. L'empreinte globale n'est pas une condition, c'est un
--   compte rendu ; la vraie condition est « il ne reste aucune trace ».
--
-- ⚠ APRES CET INVERSE, les galeries DEJA ECRITES gardent la cle jusqu'au
--   prochain passage de la fonction (run de 05:00, etape « adresses photos »).
--   Ce n'est pas grave : la cle en trop est ignoree par tous les consommateurs
--   sauf la vitrine, qui lira '1' partout tant qu'aucune photo n'est masquee.
--   ⭐ Si on veut les nettoyer tout de suite, il suffit de forcer le recalcul :
--     update public.app_dossier_current set adresses_app_le = null;
--     select public.app_photos_remplir_adresses_app(p_tout => true);
--   (non fait ici : ce serait une ecriture de masse, elle se decide a part.)
-- ============================================================================

begin;

set local lock_timeout = '5s';

do $do$
declare
  v_src   text;
  v_new   text;
  v_apres text;
  v_ancre text := replace('''legend'', p.legend)', chr(13), '');
  v_neuf  text := replace('''legend'', p.legend, ''visible'', case when p.visible is false then ''0'' else ''1'' end)', chr(13), '');
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';

  if v_src is null then
    raise exception 'STOP : app_photos_remplir_adresses_app introuvable';
  end if;

  if position(v_neuf in v_src) = 0 then
    raise notice 'RIEN A RETIRER : la cle visible n est pas dans la galerie (deja propre)';
    return;
  end if;

  v_new := replace(v_src, v_neuf, v_ancre);

  -- LA VRAIE CONDITION : plus aucune trace de ce qu'on devait retirer.
  if position(v_neuf in v_new) > 0 then
    raise exception 'STOP : il reste une trace du texte ajoute apres retrait';
  end if;

  execute v_new;

  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_apres
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';

  if md5(v_apres) = '682e386007b59eda6e5dc54056c87693' then
    raise notice 'RETIRE : empreinte d origine retrouvee (682e3860...)';
  else
    raise notice 'RETIRE (0 trace), mais l empreinte est % et non 682e3860... -- un AUTRE patch est passe sur cette fonction depuis le 18/10. Ce n est PAS une erreur de cet inverse.', md5(v_apres);
  end if;
end
$do$;

commit;
