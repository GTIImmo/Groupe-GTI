-- ============================================================================
-- REPETITION -- la cle `visible` dans notre galerie ((7)-8 piece A)
-- 18/10/2026
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS, EN ENTIER. Le `begin;` de la premiere ligne et
--    l ERREUR VOLONTAIRE de la derniere font que RIEN n est ecrit.
--
-- Elle joue, dans l ordre REEL : mesures AVANT (dont le TEMOIN INVERSE : une
-- photo masquee serait-elle publiee aujourd hui ?) -> LE VRAI PATCH -> mesures
-- APRES -> LE VRAI INVERSE -> mesure du RETOUR -> erreur volontaire.
--
-- ⚠ LE PIEGE TRAITE : app_photos_remplir_adresses_app cree quatre tables
--   TEMPORAIRES `on commit drop`. L appeler DEUX FOIS dans la meme transaction
--   echouerait sur « relation deja existante ». On les detruit entre les deux
--   passages -- sinon la repetition casserait pour une raison qui n a rien a
--   voir avec le patch.
--
-- ⚠ L essai masque une photo de 62774 (LE BAC A SABLE du projet, 4 photos) et
--   force le recalcul de ses adresses. Tout est DANS la transaction, donc
--   ANNULE. Rien ne reste.
--
-- LE MESSAGE ATTENDU si tout va bien :
--    1-avant  | empreinte de la fonction        = 682e386007b59eda6e5dc54056c87693
--    1-avant  | ancre vue combien de fois       = 1
--    1-avant  | galeries portant la cle visible = 0 sur 10259
--    1-avant  | TEMOIN INVERSE : la masquee est PUBLIEE = OUI, et sans marque -- le trou est reel
--    2-apres  | la cle est dans la fonction     = oui
--    2-apres  | la fonction compile             = oui (elle a ete reexecutee)
--    2-apres  | la masquee porte visible        = 0
--    2-apres  | les 3 autres portent visible    = 1
--    2-apres  | la vignette reste une VISIBLE   = oui
--    2-apres  | le nombre d entrees n a pas bouge = oui (4)
--    3-retour | la cle est dans la fonction     = non
--    3-retour | empreinte de la fonction        = IDENTIQUE
-- ============================================================================

begin;

create temporary table essai_mesures (
  id serial, etape text, mesure text, valeur text
) on commit drop;

create temporary table essai_cible (
  app_dossier_id bigint, photo_id uuid
) on commit drop;

-- =============================== 1. AVANT ==================================

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'empreinte de la fonction       ',
       md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_photos_remplir_adresses_app';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'ancre vue combien de fois      ',
       (((length(s) - length(replace(s, 'p.legend)', ''))) / length('p.legend)')))::text
from (select replace(pg_get_functiondef(p.oid), chr(13), '') as s
        from pg_proc p join pg_namespace n on n.oid = p.pronamespace
       where n.nspname='public' and p.proname='app_photos_remplir_adresses_app') q;

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'galeries portant la cle visible',
       count(*) filter (where images_preview_json_app::text like '%"visible"%')::text
       || ' sur ' || count(*)::text
from app_dossier_current where images_preview_json_app is not null;

-- ⭐ LE TEMOIN INVERSE. Sans lui, on poserait une cle sur un trou qu on n a pas
--   prouve. On masque une photo du bac a sable, on force le recalcul, et on
--   regarde si la vitrine la publierait.
do $temoin$
declare
  v_dossier bigint;
  v_photo   uuid;
  v_url     text;
  v_gal     jsonb;
begin
  select d.app_dossier_id into v_dossier
    from app_dossier_current d where d.hektor_annonce_id = 62774;
  if v_dossier is null then
    raise exception 'STOP : le bac a sable 62774 est introuvable';
  end if;

  select p.id into v_photo
    from app_console_photo p
   where p.app_dossier_id = v_dossier and p.present_in_hektor
     and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
   order by p.sort_order desc nulls last, p.id desc
   limit 1;
  if v_photo is null then
    raise exception 'STOP : aucune photo prete sur 62774';
  end if;

  insert into essai_cible (app_dossier_id, photo_id) values (v_dossier, v_photo);

  -- on la masque, DANS la transaction
  update app_console_photo set visible = false where id = v_photo;
  select 'https://dwaqxfrinihnychuoptk.supabase.co/storage/v1/object/public/gti-photo/'
         || (derives_json->'w400'->>'chemin') into v_url
    from app_console_photo where id = v_photo;

  -- on force le recalcul de CETTE annonce
  update app_dossier_current set adresses_app_le = null where app_dossier_id = v_dossier;
  perform public.app_photos_remplir_adresses_app();

  select images_preview_json_app into v_gal
    from app_dossier_current where app_dossier_id = v_dossier;

  insert into essai_mesures (etape, mesure, valeur) values
    ('1-avant ', 'TEMOIN INVERSE : la masquee est PUBLIEE',
     case when v_gal::text like '%' || (select derives_json->'w400'->>'chemin'
                                          from app_console_photo where id = v_photo) || '%'
          then case when v_gal::text like '%"visible"%'
                    then 'OUI, mais elle porte une marque (le patch est deja la ?)'
                    else 'OUI, et sans marque -- le trou est reel' end
          else 'NON -- elle est deja ecartee, le patch ne servirait a rien' end);
end
$temoin$;

-- ====================== 2. LE VRAI PATCH, copie conforme ====================

do $do$
declare
  v_src   text;
  v_new   text;
  v_ancre text := replace('''legend'', p.legend)', chr(13), '');
  v_neuf  text := replace('''legend'', p.legend, ''visible'', case when p.visible is false then ''0'' else ''1'' end)', chr(13), '');
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';

  if v_src is null then
    raise exception 'STOP : app_photos_remplir_adresses_app introuvable';
  end if;

  if position(v_neuf in v_src) > 0 then
    raise notice 'DEJA FAIT : la cle visible est dans la galerie';
    return;
  end if;

  if md5(v_src) <> '682e386007b59eda6e5dc54056c87693' then
    raise notice 'ATTENTION : empreinte % (attendue 682e3860...)', md5(v_src);
  end if;

  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 1 then
    raise exception 'STOP : l ancre apparait % fois (attendu 1)', v_vu;
  end if;

  v_new := replace(v_src, v_ancre, v_neuf);
  execute v_new;
end
$do$;

-- =============================== 3. APRES ==================================

insert into essai_mesures (etape, mesure, valeur)
select '2-apres ', 'la cle est dans la fonction    ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%''visible''%'
            then 'oui' else 'non' end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_photos_remplir_adresses_app';

-- ⚠ LES TABLES TEMPORAIRES DU PREMIER PASSAGE : on les detruit, sinon le second
--   appel leve « relation tmp_maj deja existante » et on accuserait le patch.
drop table if exists tmp_maj, tmp_cibles, tmp_principale, tmp_galerie;

do $apres$
declare
  v_dossier bigint;
  v_photo   uuid;
  v_chemin  text;
  v_gal     jsonb;
  v_vis     text;
  v_autres  text;
  v_n       integer;
begin
  select app_dossier_id, photo_id into v_dossier, v_photo from essai_cible limit 1;
  select derives_json->'w400'->>'chemin' into v_chemin
    from app_console_photo where id = v_photo;

  update app_dossier_current set adresses_app_le = null where app_dossier_id = v_dossier;
  perform public.app_photos_remplir_adresses_app();

  insert into essai_mesures (etape, mesure, valeur) values
    ('2-apres ', 'la fonction compile            ', 'oui (elle a ete reexecutee)');

  select images_preview_json_app into v_gal
    from app_dossier_current where app_dossier_id = v_dossier;

  select e->>'visible' into v_vis
    from jsonb_array_elements(v_gal) e
   where e->>'url' like '%' || v_chemin || '%';

  select string_agg(distinct coalesce(e->>'visible','(absente)'), ', ') into v_autres
    from jsonb_array_elements(v_gal) e
   where e->>'url' not like '%' || v_chemin || '%';

  v_n := jsonb_array_length(v_gal);

  insert into essai_mesures (etape, mesure, valeur) values
    ('2-apres ', 'la masquee porte visible       ', coalesce(v_vis, '(ABSENTE DE LA GALERIE)')),
    ('2-apres ', 'les autres portent visible     ', coalesce(v_autres, '(aucune autre)')),
    ('2-apres ', 'la vignette reste une VISIBLE  ',
       case when (select photo_url_listing_app from app_dossier_current
                   where app_dossier_id = v_dossier) like '%' || v_chemin || '%'
            then 'NON -- la vignette est la masquee (ANORMAL)' else 'oui' end),
    ('2-apres ', 'le nombre d entrees            ',
       v_n::text || case when v_n = 4 then ' (inchange)' else ' (ATTENDU 4)' end);
end
$apres$;

-- ========================== 4. LE VRAI INVERSE =============================

do $inv$
declare
  v_src   text;
  v_new   text;
  v_ancre text := replace('''legend'', p.legend)', chr(13), '');
  v_neuf  text := replace('''legend'', p.legend, ''visible'', case when p.visible is false then ''0'' else ''1'' end)', chr(13), '');
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';

  if position(v_neuf in v_src) = 0 then
    raise notice 'RIEN A RETIRER';
    return;
  end if;

  v_new := replace(v_src, v_neuf, v_ancre);
  if position(v_neuf in v_new) > 0 then
    raise exception 'STOP : il reste une trace du texte ajoute';
  end if;
  execute v_new;
end
$inv$;

-- =============================== 5. RETOUR =================================

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'la cle est dans la fonction    ',
       case when replace(pg_get_functiondef(p.oid), chr(13), '') like '%''visible''%'
            then 'oui (ANORMAL)' else 'non' end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_photos_remplir_adresses_app';

insert into essai_mesures (etape, mesure, valeur)
select '3-retour', 'empreinte de la fonction       ',
       case when md5(replace(pg_get_functiondef(p.oid), chr(13), '')) = '682e386007b59eda6e5dc54056c87693'
            then 'IDENTIQUE'
            else 'DIFFERENTE : ' || md5(replace(pg_get_functiondef(p.oid), chr(13), '')) end
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname='public' and p.proname='app_photos_remplir_adresses_app';

-- ================== 6. L ERREUR VOLONTAIRE : tout est annule ================
-- ⚠ Le compte rendu voyage DANS le message : un SELECT d une transaction qui
--   echoue n est pas toujours rendu par l editeur SQL.

do $fin$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id)
    into v_txt from essai_mesures;
  raise exception '%', 'ESSAI ANNULE -- rien n a ete ecrit.' || chr(10) || v_txt;
end
$fin$;

rollback;
