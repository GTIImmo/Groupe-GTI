-- ============================================================================
-- INVERSE -- la galerie suit le retrait d'une photo (chantier 7-8, 20/10/2026)
-- ============================================================================
-- Remet app_photos_remplir_adresses_app EXACTEMENT comme avant le patch :
--   empreinte de retour  b87f6c6827fbedf0c8d8e8709d62a334
--
-- ⚠ CE RETOUR ARRIERE NE TOUCHE QUE LA FONCTION. Les galeries recalculees par le
--   patch RESTENT : elles sont JUSTES (elles ne contiennent plus les photos
--   retirees), les remettre dans leur ancien etat serait remettre le defaut.
--
-- Lecon 31 : un retour arriere verifie d'abord qu'il ne reste aucune trace de ce
-- qu'il devait retirer -- et il refuse de jouer si la fonction n'est pas celle du patch.
-- ============================================================================

begin;

set local lock_timeout = '5s';

do $inv$
declare
  v_src   text;
  v_new   text;
  v_pose1 text := replace('select p.app_dossier_id, max(greatest(p.derives_generes_le, p.absent_depuis)) as dernier', chr(13), '');
  v_nue1  text := replace('select p.app_dossier_id, max(p.derives_generes_le) as dernier', chr(13), '');
  v_pose2 text := replace('where p_tout or greatest(p.derives_generes_le, p.absent_depuis) >= quand - make_interval(hours => greatest(1, p_heures))', chr(13), '');
  v_nue2  text := replace('where p_tout or p.derives_generes_le >= quand - make_interval(hours => greatest(1, p_heures))', chr(13), '');
  v_apres constant text := 'ec8066616381cdb90df38ec561f1441f';
  v_avant constant text := 'b87f6c6827fbedf0c8d8e8709d62a334';
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';
  if v_src is null then raise exception 'STOP : fonction introuvable'; end if;

  if md5(v_src) = v_avant then
    raise notice 'RIEN A DEFAIRE : la fonction est deja dans l etat d avant le patch (%).', v_avant;
    return;
  end if;
  if md5(v_src) <> v_apres then
    raise exception 'STOP : empreinte % -- ce n est ni l etat d avant (%) ni l etat du patch (%). La RELIRE.', md5(v_src), v_avant, v_apres;
  end if;

  v_vu := (length(v_src) - length(replace(v_src, v_pose1, ''))) / length(v_pose1);
  if v_vu <> 1 then raise exception 'STOP : la forme 1 apparait % fois (attendu 1)', v_vu; end if;
  v_vu := (length(v_src) - length(replace(v_src, v_pose2, ''))) / length(v_pose2);
  if v_vu <> 1 then raise exception 'STOP : la forme 2 apparait % fois (attendu 1)', v_vu; end if;

  v_new := replace(replace(v_src, v_pose1, v_nue1), v_pose2, v_nue2);
  if md5(v_new) <> v_avant then
    raise exception 'STOP : le texte rendu a l empreinte % au lieu de % -- il ne serait pas l original', md5(v_new), v_avant;
  end if;

  execute v_new;

  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';
  if md5(v_src) <> v_avant then
    raise exception 'STOP : apres ecriture, l empreinte est % au lieu de %', md5(v_src), v_avant;
  end if;
  if position('absent_depuis' in v_src) > 0 then
    raise exception 'STOP : il reste une trace de absent_depuis dans la fonction';
  end if;

  raise notice 'REMIS : la fonction est revenue a l etat du 19/10, a l octet pres (%).', md5(v_src);
end
$inv$;

commit;
