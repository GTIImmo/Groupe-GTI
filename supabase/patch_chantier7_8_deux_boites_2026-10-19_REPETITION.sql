-- ============================================================================
-- REPETITION -- les deux boites (⑦-8, marche 1)
-- 19/10/2026
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS, EN ENTIER. Le `begin;` de la premiere ligne et
--    l'ERREUR VOLONTAIRE de la derniere font que RIEN n'est ecrit.
--
-- ⭐⭐ POURQUOI ELLE DOIT FABRIQUER LA SITUATION. Mesure du 19/10 : sur les 103
--   photos masquees, ZERO a un derive, et ZERO est sur une annonce vivante.
--   Donc une epreuve qui se contenterait de regarder la production serait VERTE
--   AVANT COMME APRES LE PATCH -- elle ne prouverait rien du tout.
--   (C'est la lecon « un controle vert peut mesurer autre chose ».)
--   Elle prend donc deux annonces VIVANTES et leur fabrique le cas, dans une
--   transaction annulee :
--     annonce A : une photo MASQUEE (avec ses derives) + une photo TEMOIN qui
--                 reste VISIBLE (sans elle, un patch qui viderait TOUT serait vert)
--     annonce B : TOUTES ses photos masquees  <- le trou « annonce 100 % masquee »
--
-- ⚠ VERSION 2 (19/10). La v1 a ECHOUE AU COLLAGE : elle passait une photo a
--   `visible = NULL` et la base a refuse (colonne NOT NULL, defaut `true`).
--   J'avais verifie le TYPE de la colonne, pas sa NULLABILITE. Le patch, lui,
--   n'a pas bouge -- et l'empreinte de la fonction est restee INTACTE
--   (682e3860..., verifie apres l'echec) : rien n'avait ete ecrit.
--
-- ELLE JOUE DANS L'ORDRE REEL : mesures AVANT -> TEMOIN INVERSE (sans le patch,
-- la boite DOIT contenir la masquee) -> LE VRAI PATCH -> mesures APRES ->
-- LE VRAI INVERSE -> mesure du RETOUR -> erreur volontaire.
--
-- LE MESSAGE ATTENDU si tout va bien :
--   1-avant   | empreinte de depart            = 682e386007b59eda6e5dc54056c87693
--   1-avant   | l ancre apparait               = 2 fois (couverture + galerie)
--   1-avant   | masquees AVEC derive en prod   = 0 -- d ou la fabrication
--   1-avant   | annonce A choisie / photos     = <id> / 3 ou +
--   1-avant   | annonce B choisie / photos     = <id> / 2 ou +
--   2-temoin  | A : la masquee EST dans la boite        = OUI (c est le defaut)
--   2-temoin  | B : sa couverture EST une masquee       = OUI (c est le defaut)
--   3-apres   | A : la masquee est dans la boite        = NON
--   3-apres   | A : la photo VISIBLE y est encore       = OUI (pas trop strict)
--   3-apres   | le cas « visible NULL » est-il possible = NON (colonne NOT NULL)
--   3-apres   | A : sa couverture est une VISIBLE       = OUI
--   3-apres   | A : nb de photos dans la boite          = (avant - 1)
--   3-apres   | B : couverture et galerie               = VIDES (0 % publiable)
--   3-apres   | le panneau photos voit toujours tout    = OUI
--   4-retour  | empreinte revenue                       = oui, a l octet pres
-- ============================================================================

begin;

set local lock_timeout = '10s';

create temporary table essai_mesures (id serial, etape text, mesure text, valeur text) on commit drop;
create temporary table essai_cibles (role text primary key, dossier bigint, photo_masquee uuid,
                                     photo_temoin uuid, url_masquee text, nb_avant integer) on commit drop;

-- =========================== 1. AVANT ======================================

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'empreinte de depart            ',
       md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname='public' and p.proname='app_photos_remplir_adresses_app';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'l ancre apparait               ',
       ((length(s) - length(replace(s, 'where p.present_in_hektor and p.derives_json', '')))
        / length('where p.present_in_hektor and p.derives_json'))::text || ' fois'
  from (select replace(pg_get_functiondef(p.oid), chr(13), '') as s
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname='public' and p.proname='app_photos_remplir_adresses_app') z;

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'masquees AVEC derive en prod   ', count(*)::text || '  (d ou la fabrication)'
  from app_console_photo
 where visible is false and present_in_hektor and derives_json ? 'w400' and derives_json ? 'w1600';

-- ── LE CHOIX DES CIBLES : des annonces VIVANTES dont les photos ont les 2 derives
insert into essai_cibles (role, dossier, nb_avant)
select 'A', p.app_dossier_id, count(*)::integer
  from app_console_photo p join app_dossier_current d on d.app_dossier_id = p.app_dossier_id
 where p.present_in_hektor and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
   and p.visible is true
 group by p.app_dossier_id having count(*) >= 3
 order by p.app_dossier_id limit 1;

insert into essai_cibles (role, dossier, nb_avant)
select 'B', p.app_dossier_id, count(*)::integer
  from app_console_photo p join app_dossier_current d on d.app_dossier_id = p.app_dossier_id
 where p.present_in_hektor and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
   and p.visible is true
   and p.app_dossier_id <> (select dossier from essai_cibles where role='A')
 group by p.app_dossier_id having count(*) between 2 and 6
 order by p.app_dossier_id limit 1;

do $garde$
begin
  if (select count(*) from essai_cibles) <> 2 then
    raise exception 'STOP : impossible de trouver deux annonces vivantes avec des photos derivees -- epreuve non concluante, RIEN mesure.';
  end if;
end $garde$;

-- la photo que l'on va MASQUER sur A (la derniere dans l'ordre), et une photo
-- TEMOIN qui reste visible (l'avant-derniere) : on garde leurs identifiants.
-- ⭐ LE TEMOIN SERT A PROUVER QUE LE PATCH N'EST PAS TROP STRICT : si elle
--   disparaissait aussi, le filtre viderait des galeries legitimes.
update essai_cibles c set
  photo_masquee = (select p.id from app_console_photo p where p.app_dossier_id = c.dossier
                    and p.present_in_hektor and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
                   order by p.sort_order desc nulls first, p.id desc limit 1),
  photo_temoin  = (select p.id from app_console_photo p where p.app_dossier_id = c.dossier
                    and p.present_in_hektor and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
                   order by p.sort_order desc nulls first, p.id desc offset 1 limit 1)
 where c.role = 'A';

update essai_cibles c
   set url_masquee = 'https://dwaqxfrinihnychuoptk.supabase.co/storage/v1/object/public/gti-photo/'
                     || (select p.derives_json->'w400'->>'chemin' from app_console_photo p where p.id = c.photo_masquee)
 where c.role = 'A';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'annonce A choisie / photos     ', dossier::text || ' / ' || nb_avant::text
  from essai_cibles where role='A';
insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'annonce B choisie / photos     ', dossier::text || ' / ' || nb_avant::text
  from essai_cibles where role='B';

-- ──────────────── LA FABRICATION DU CAS (annulee au rollback) ───────────────
-- ⚠⚠ CORRIGE LE 19/10 APRES UN ECHEC AU COLLAGE : ma 1re version passait une
--   photo a `visible = NULL` pour eprouver la regle « un NULL reste visible ».
--   LA BASE A REFUSE : app_console_photo.visible est NOT NULL, defaut `true`
--   (et 0 ligne a NULL sur 441 363). J'avais verifie le TYPE de la colonne, pas
--   sa NULLABILITE. => Un NULL est IMPOSSIBLE ici, donc cette branche n'avait
--   rien a eprouver. La forme `visible is not false` reste la bonne : elle est
--   DEFENSIVE (elle tiendrait si la contrainte sautait un jour) et elle recopie
--   la regle du projet. C'est l'EPREUVE qui avait tort, pas le patch.
--   Le temoin « pas trop strict » est desormais une photo qui RESTE VISIBLE.
--
-- A : une photo masquee, le reste visible (dont la photo temoin).
update app_console_photo set visible = false, derives_generes_le = now()
 where id = (select photo_masquee from essai_cibles where role='A');
-- B : TOUTES ses photos masquees.
update app_console_photo set visible = false, derives_generes_le = now()
 where app_dossier_id = (select dossier from essai_cibles where role='B');
-- et on rend les deux annonces « a refaire » pour le fabricant.
update app_dossier_current set adresses_app_le = null, photo_url_listing_app = null,
       images_preview_json_app = null
 where app_dossier_id in (select dossier from essai_cibles);

-- ============== 2. LE TEMOIN INVERSE : sans le patch, ca FUIT ===============
-- ⚠ LES TABLES TEMPORAIRES DE LA FONCTION SONT `on commit drop` : comme on ne
--   valide jamais, il FAUT les effacer entre deux appels, sinon le second
--   echoue sur « relation tmp_maj already exists ».

drop table if exists tmp_maj, tmp_cibles, tmp_principale, tmp_galerie;
do $appel$ begin perform public.app_photos_remplir_adresses_app(1, false); end $appel$;

insert into essai_mesures (etape, mesure, valeur)
select '2-temoin', 'A : la masquee EST dans la boite',
       case when exists (
         select 1 from app_dossier_current d, jsonb_array_elements(d.images_preview_json_app) e
          where d.app_dossier_id = c.dossier and e->>'url' = c.url_masquee)
            then 'OUI -- c est bien le defaut qu on corrige'
            else 'NON -- ATTENTION : le temoin ne prouve rien, epreuve a revoir' end
  from essai_cibles c where c.role='A';

insert into essai_mesures (etape, mesure, valeur)
select '2-temoin', 'B : sa couverture EST une masquee',
       case when d.photo_url_listing_app is not null
            then 'OUI -- c est bien le trou « annonce 100 % masquee »'
            else 'NON -- ATTENTION : le temoin ne prouve rien' end
  from app_dossier_current d join essai_cibles c on c.dossier = d.app_dossier_id
 where c.role='B';

-- ===================== 3. LE VRAI PATCH, copie conforme =====================

do $do$
declare
  v_src   text;
  v_new   text;
  v_ancre text := replace('where p.present_in_hektor and p.derives_json', chr(13), '');
  v_neuf  text := replace('where p.present_in_hektor and p.visible is not false and p.derives_json', chr(13), '');
  v_emp   constant text := '682e386007b59eda6e5dc54056c87693';
  v_vu    integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';
  if v_src is null then raise exception 'STOP : fonction introuvable'; end if;
  if position(v_neuf in v_src) > 0 then raise notice 'DEJA FAIT'; return; end if;
  if md5(v_src) <> v_emp then
    raise exception 'STOP : empreinte % au lieu de %', md5(v_src), v_emp;
  end if;
  v_vu := (length(v_src) - length(replace(v_src, v_ancre, ''))) / length(v_ancre);
  if v_vu <> 2 then raise exception 'STOP : l ancre apparait % fois (attendu 2)', v_vu; end if;
  v_new := replace(v_src, v_ancre, v_neuf);
  if (length(v_new) - length(replace(v_new, v_neuf, ''))) / length(v_neuf) <> 2 then
    raise exception 'STOP : la forme neuve n apparait pas 2 fois';
  end if;
  if position(v_ancre in replace(v_new, v_neuf, '')) > 0 then
    raise exception 'STOP : il reste une ancre non traitee';
  end if;
  if v_new = v_src then raise exception 'STOP : le patch n a RIEN change'; end if;
  execute v_new;
end
$do$;

-- =============================== 4. APRES ==================================
-- on remet les deux annonces « a refaire » et on rejoue LE MEME fabricant.

update app_dossier_current set adresses_app_le = null, photo_url_listing_app = null,
       images_preview_json_app = null
 where app_dossier_id in (select dossier from essai_cibles);

drop table if exists tmp_maj, tmp_cibles, tmp_principale, tmp_galerie;
do $appel2$ begin perform public.app_photos_remplir_adresses_app(1, false); end $appel2$;

insert into essai_mesures (etape, mesure, valeur)
select '3-apres ', 'A : la masquee est dans la boite',
       case when exists (
         select 1 from app_dossier_current d, jsonb_array_elements(d.images_preview_json_app) e
          where d.app_dossier_id = c.dossier and e->>'url' = c.url_masquee)
            then 'OUI -- ECHEC, le filtre ne mord pas' else 'NON -- le filtre mord' end
  from essai_cibles c where c.role='A';

-- ⭐ LE TEMOIN « PAS TROP STRICT » : une photo restee VISIBLE doit TOUJOURS
--   etre dans la boite. Sans ce controle, un patch qui viderait TOUT serait vert.
insert into essai_mesures (etape, mesure, valeur)
select '3-apres ', 'A : la photo VISIBLE y est encore',
       case when exists (
         select 1 from app_dossier_current d, jsonb_array_elements(d.images_preview_json_app) e
          where d.app_dossier_id = c.dossier
            and e->>'url' = 'https://dwaqxfrinihnychuoptk.supabase.co/storage/v1/object/public/gti-photo/'
                            || (select p.derives_json->'w400'->>'chemin' from app_console_photo p where p.id = c.photo_temoin))
            then 'OUI -- le patch n est PAS trop strict' else 'NON -- ECHEC : il vide des photos visibles' end
  from essai_cibles c where c.role='A';

-- ⭐ ET LA REGLE DU NULL EST DECLAREE MOOT, PAS OUBLIEE (mesure du 19/10) :
--   la colonne est NOT NULL avec defaut `true`, donc le cas ne peut pas exister.
insert into essai_mesures (etape, mesure, valeur)
select '3-apres ', 'le cas « visible NULL » est-il possible',
       case when is_nullable = 'NO'
            then 'NON (colonne NOT NULL, defaut ' || coalesce(column_default,'?') || ') -> « is not false » est DEFENSIF'
            else 'OUI -- alors il FAUT eprouver cette branche' end
  from information_schema.columns
 where table_schema='public' and table_name='app_console_photo' and column_name='visible';

insert into essai_mesures (etape, mesure, valeur)
select '3-apres ', 'A : sa couverture est VISIBLE   ',
       case when d.photo_url_listing_app is null then 'NON -- plus de couverture du tout'
            when d.photo_url_listing_app = c.url_masquee then 'NON -- ECHEC : la couverture est la masquee'
            else 'OUI' end
  from app_dossier_current d join essai_cibles c on c.dossier = d.app_dossier_id where c.role='A';

insert into essai_mesures (etape, mesure, valeur)
select '3-apres ', 'A : photos dans la boite        ',
       coalesce(jsonb_array_length(d.images_preview_json_app), 0)::text
       || ' (il y en avait ' || c.nb_avant::text || ', une est masquee)'
  from app_dossier_current d join essai_cibles c on c.dossier = d.app_dossier_id where c.role='A';

insert into essai_mesures (etape, mesure, valeur)
select '3-apres ', 'B : couverture et galerie       ',
       case when d.photo_url_listing_app is null
             and coalesce(jsonb_array_length(d.images_preview_json_app), 0) = 0
            then 'VIDES -- 0 % publiable, le trou est ferme'
            else 'ECHEC : couverture=' || coalesce(d.photo_url_listing_app,'(nulle)')
                 || ' galerie=' || coalesce(jsonb_array_length(d.images_preview_json_app),0)::text end
  from app_dossier_current d join essai_cibles c on c.dossier = d.app_dossier_id where c.role='B';

-- ⭐ ET LE NEGOCIATEUR, LUI, VOIT TOUJOURS TOUT : le panneau photos lit la TABLE
--   (loadConsolePhotos, api.ts:7991, filtre present_in_hektor seul). On reproduit
--   EXACTEMENT son filtre.
insert into essai_mesures (etape, mesure, valeur)
select '3-apres ', 'le panneau photos voit tout     ',
       count(*)::text || ' photos sur A dont ' || count(*) filter (where p.visible is false)::text
       || ' masquee(s) -- OUI, il les voit'
  from app_console_photo p join essai_cibles c on c.dossier = p.app_dossier_id
 where c.role='A' and p.present_in_hektor is true;

-- ========================== 5. LE VRAI INVERSE =============================

do $inv$
declare
  v_src  text;
  v_pose text := replace('where p.present_in_hektor and p.visible is not false and p.derives_json', chr(13), '');
  v_nue  text := replace('where p.present_in_hektor and p.derives_json', chr(13), '');
  v_vu   integer;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname='public' and p.proname='app_photos_remplir_adresses_app';
  v_vu := (length(v_src) - length(replace(v_src, v_pose, ''))) / length(v_pose);
  if v_vu = 0 then raise notice 'RIEN A DEFAIRE'; return; end if;
  if v_vu <> 2 then raise exception 'STOP : la condition apparait % fois (attendu 2)', v_vu; end if;
  execute replace(v_src, v_pose, v_nue);
end
$inv$;

-- =============================== 6. RETOUR =================================

insert into essai_mesures (etape, mesure, valeur)
select '4-retour', 'empreinte revenue              ',
       case when md5(s) = '682e386007b59eda6e5dc54056c87693'
            then 'oui, a l octet pres'
            else 'NON : ' || md5(s) end
  from (select replace(pg_get_functiondef(p.oid), chr(13), '') as s
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname='public' and p.proname='app_photos_remplir_adresses_app') z;

insert into essai_mesures (etape, mesure, valeur)
select '4-retour', 'aucune trace de la condition   ',
       case when position('visible is not false' in s) = 0 then 'oui' else 'NON' end
  from (select replace(pg_get_functiondef(p.oid), chr(13), '') as s
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname='public' and p.proname='app_photos_remplir_adresses_app') z;

-- ================== 7. L ERREUR VOLONTAIRE : tout est annule ================
-- ⚠ Le compte rendu voyage DANS le message : un SELECT d une transaction qui
--   echoue n est pas toujours rendu par l editeur SQL.

do $fin$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id)
    into v_txt from essai_mesures;
  raise exception '%', 'ESSAI ANNULE -- rien n a ete ecrit, ni la fonction ni les photos.'
    || chr(10) || v_txt;
end
$fin$;

rollback;
