-- ============================================================================
-- INVERSE -- retirer la condition « visible is not false » des deux where
-- 19/10/2026
-- ============================================================================
-- Il remet app_photos_remplir_adresses_app exactement dans l'etat ou le patch
-- l'a trouvee : empreinte 682e386007b59eda6e5dc54056c87693.
--
-- ⭐ ETAT MESURE APRES LE COLLAGE DU 19/10 (controle, 7 verts) :
--      empreinte APRES le patch ... b87f6c6827fbedf0c8d8e8709d62a334
--      la condition apparait ...... 2 fois (couverture + galerie)
--      ancre nue oubliee .......... 0
--      retours chariot injectes ... 0   <- le transport a tenu (lecon 30)
--    Cet inverse ne se fie PAS a l'empreinte d'apres : il compte la condition
--    (2 attendu), ce qui le rend valide meme si un autre patch passe ensuite.
--
-- ⚠ CE QU'IL FAUT SAVOIR AVANT DE LE JOUER : la boite publique reportera a
--   nouveau les photos MASQUEES des annonces vivantes vers la vitrine Android,
--   l'espace client et le portail de rapprochement -- des le passage suivant de
--   Console/remplir_adresses_photos.js (run de nuit).
--   -> Si des masquees ont ete rapatriees entre-temps (marche 2), les defaire
--      N'EST PAS neutre : regarder d'abord combien de masquees ont des derives.
--      La mesure est dans l'en-tete de la repetition.
--
-- ⭐ IL NE DEFAIT QUE SA PROPRE PART (lecon 31, payee le 15/10 : deux patchs du
--   meme jour sur la MEME fonction, et l'inverse du premier exigeait l'empreinte
--   d'avant LES DEUX -- il defaisait correctement sa part PUIS refusait).
--   Donc ici, dans cet ordre :
--     1. il verifie qu'il ne reste AUCUNE TRACE de ce qu'il devait retirer ;
--     2. l'empreinte d'origine n'est EXIGEE que si rien d'autre n'a touche la
--        fonction. Sinon il le DIT, nomme ce qui diverge, et NE BLOQUE PAS --
--        parce que sa part, elle, est bien defaite.
--
-- ⚠ ANCRE SUR UNE SEULE LIGNE + replace(chr(13)) DES DEUX COTES (lecon 30).
-- ============================================================================

begin;

set local lock_timeout = '5s';

do $do$
declare
  v_src   text;
  v_new   text;
  v_pose  text := replace('where p.present_in_hektor and p.visible is not false and p.derives_json', chr(13), '');
  v_nue   text := replace('where p.present_in_hektor and p.derives_json', chr(13), '');
  v_emp   constant text := '682e386007b59eda6e5dc54056c87693';
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';

  if v_src is null then
    raise exception 'STOP : public.app_photos_remplir_adresses_app est introuvable';
  end if;

  v_vu := (length(v_src) - length(replace(v_src, v_pose, ''))) / length(v_pose);

  if v_vu = 0 then
    raise notice 'RIEN A DEFAIRE : la condition n est pas posee.';
    return;
  end if;
  if v_vu <> 2 then
    raise exception 'STOP : la condition apparait % fois (attendu 2). Quelque chose d autre a touche cette fonction -- ne PAS defaire a l aveugle.', v_vu;
  end if;

  v_new := replace(v_src, v_pose, v_nue);

  if v_new = v_src then
    raise exception 'STOP : le retour arriere n a RIEN change';
  end if;

  execute v_new;

  -- ⓵ SA PART EST-ELLE BIEN DEFAITE ? C'est la SEULE condition bloquante.
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';

  if position('visible is not false' in v_src) > 0 then
    raise exception 'STOP : il reste une trace de « visible is not false » apres le retour arriere';
  end if;

  v_vu := (length(v_src) - length(replace(v_src, v_nue, ''))) / length(v_nue);
  if v_vu <> 2 then
    raise exception 'STOP : les deux where nus ne sont pas revenus (% au lieu de 2)', v_vu;
  end if;

  -- ⓶ L'EMPREINTE D'ORIGINE : attendue, mais PAS bloquante (lecon 31).
  if md5(v_src) = v_emp then
    raise notice 'DEFAIT : la fonction est revenue a son empreinte d origine (%), a l octet pres.', v_emp;
  else
    raise notice 'DEFAIT : ma part est retiree (0 trace, les 2 where nus sont revenus), MAIS l empreinte est % au lieu de %.', md5(v_src), v_emp;
    raise notice 'CELA VEUT DIRE QU UN AUTRE PATCH a touche cette fonction depuis le 19/10. Ce n est PAS une erreur de ce retour arriere : chercher l autre patch et jouer SON inverse.';
  end if;

  raise notice '⚠ LA BOITE PUBLIQUE REPORTERA A NOUVEAU LES MASQUEES au prochain passage de Console/remplir_adresses_photos.js.';
end
$do$;

commit;
