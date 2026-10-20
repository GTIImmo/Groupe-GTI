-- ============================================================================
-- REPETITION -- la galerie suit le retrait d'une photo (chantier 7-8)
-- 20/10/2026
-- ============================================================================
-- ⚠⚠ A COLLER EN UNE SEULE FOIS, EN ENTIER. Le `begin;` de la premiere ligne et
--    l'ERREUR VOLONTAIRE de la derniere font que RIEN n'est ecrit : ni la fonction,
--    ni les galeries.
--
-- ⭐ ICI LE CAS EXISTE DEJA EN PRODUCTION (57 galeries trop longues, mesure du
--   20/10) : pas besoin de le fabriquer. L'epreuve joue donc sur les VRAIES
--   donnees, dans l'ordre reel :
--     1-avant   : ce qu'on mesure avant (57 trop longues, 0 deja ciblees)
--     2-temoin  : SANS le patch, relancer la fonction sur 720 h ne repare RIEN
--                 (preuve que le defaut est bien dans le critere de ciblage)
--     3-patch   : LE VRAI PATCH, copie conforme (avec son recalcul et ses controles)
--     4-apres   : 0 trop longue, 0 trop courte, les galeries JUSTES inchangees,
--                 et le cas d'ecole V320063214 : 26 -> 12
--     5-inverse : LE VRAI INVERSE, copie conforme, puis l'empreinte revenue
--
-- LE MESSAGE ATTENDU si tout va bien :
--   1-avant   | empreinte de depart                    = b87f6c6827fbedf0c8d8e8709d62a334
--   1-avant   | ancres (1 et 2)                        = 1 fois et 1 fois
--   1-avant   | galeries trop longues                  = 57
--   1-avant   | dont ciblees par le patch / avant      = 57 / 0
--   1-avant   | V320063214 : galerie / photos valides  = 26 / 12
--   2-temoin  | sans patch, trop longues apres relance = 57 (le defaut tient)
--   4-apres   | trop longues / trop courtes            = 0 / 0 ou 1  -- OK (1 = ajout de photos tout recent)
--   4-apres   | galeries justes dont le contenu change = 0 sur ~10 200 (ou quelques-unes recalculees a juste titre)
--   4-apres   | V320063214 : galerie / couverture      = 12 / presente
--   5-retour  | empreinte revenue                      = oui, a l octet pres
-- ============================================================================

begin;

set local lock_timeout = '10s';

create temporary table essai_mesures (id serial, etape text, mesure text, valeur text) on commit drop;

-- =========================== 1. AVANT ======================================

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'empreinte de depart                   ',
       md5(replace(pg_get_functiondef(p.oid), chr(13), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname='public' and p.proname='app_photos_remplir_adresses_app';

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'ancres (1 et 2)                       ',
       ((length(s) - length(replace(s, 'select p.app_dossier_id, max(p.derives_generes_le) as dernier', '')))
        / length('select p.app_dossier_id, max(p.derives_generes_le) as dernier'))::text || ' fois et '
    || ((length(s) - length(replace(s, 'where p_tout or p.derives_generes_le >= quand - make_interval(hours => greatest(1, p_heures))', '')))
        / length('where p_tout or p.derives_generes_le >= quand - make_interval(hours => greatest(1, p_heures))'))::text || ' fois'
  from (select replace(pg_get_functiondef(p.oid), chr(13), '') as s
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname='public' and p.proname='app_photos_remplir_adresses_app') z;

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'galeries trop longues                 ', t.longues::text
  from (
  with attendu as (
    select p.app_dossier_id, count(*) n from public.app_console_photo p
     where p.present_in_hektor and p.visible is not false and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
     group by 1)
  select count(*) filter (where jsonb_array_length(d.images_preview_json_app) > coalesce(a.n, 0)) as longues,
         count(*) filter (where jsonb_array_length(d.images_preview_json_app) < coalesce(a.n, 0)) as courtes,
         count(*) filter (where jsonb_array_length(d.images_preview_json_app) = coalesce(a.n, 0)) as justes
    from public.app_dossier_current d left join attendu a using (app_dossier_id)
   where d.images_preview_json_app is not null
  ) t;

-- dont : celles que le patch cibleront (retrait posterieur au calcul de la galerie),
-- et celles que la fonction cible deja AVANT le patch
insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'dont ciblees par le patch / avant     ',
       count(*) filter (where dr.ab > d.adresses_app_le)::text || ' / ' || count(*) filter (where dr.dg > d.adresses_app_le)::text
  from public.app_dossier_current d
  join (select p.app_dossier_id, max(p.absent_depuis) ab, max(p.derives_generes_le) dg
          from public.app_console_photo p group by 1) dr using (app_dossier_id)
  left join (select p.app_dossier_id, count(*) n from public.app_console_photo p
              where p.present_in_hektor and p.visible is not false and p.derives_json ? 'w400' and p.derives_json ? 'w1600' group by 1) a using (app_dossier_id)
 where d.images_preview_json_app is not null
   and jsonb_array_length(d.images_preview_json_app) > coalesce(a.n, 0);

insert into essai_mesures (etape, mesure, valeur)
select '1-avant ', 'V320063214 : galerie / photos valides ',
       jsonb_array_length(d.images_preview_json_app)::text || ' / '
       || (select count(*) from public.app_console_photo p where p.app_dossier_id = d.app_dossier_id
            and p.present_in_hektor and p.visible is not false and p.derives_json ? 'w400' and p.derives_json ? 'w1600')::text
  from public.app_dossier_current d where d.numero_dossier = 'V320063214';

-- l'instantane des galeries JUSTES : elles ne doivent pas bouger
create temporary table essai_justes on commit drop as
with attendu as (
  select p.app_dossier_id, count(*) n from public.app_console_photo p
   where p.present_in_hektor and p.visible is not false and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
   group by 1)
select d.app_dossier_id, md5(d.images_preview_json_app::text) as h, d.photo_url_listing_app as couv
  from public.app_dossier_current d left join attendu a using (app_dossier_id)
 where d.images_preview_json_app is not null
   and jsonb_array_length(d.images_preview_json_app) = coalesce(a.n, 0);

-- ============== 2. LE TEMOIN : sans le patch, le defaut TIENT ===============
-- ⚠ LES TABLES TEMPORAIRES DE LA FONCTION SONT `on commit drop` : comme on ne
--   valide jamais, il FAUT les effacer entre deux appels.

drop table if exists tmp_maj, tmp_cibles, tmp_principale, tmp_galerie;
do $appel$ begin perform public.app_photos_remplir_adresses_app(720, false); end $appel$;

insert into essai_mesures (etape, mesure, valeur)
select '2-temoin', 'sans patch, trop longues apres relance', t.longues::text
         || case when t.longues > 0 then '  (le defaut tient : le critere de ciblage est bien la cause)'
                 else '  ATTENTION : le temoin ne prouve rien' end
  from (
  with attendu as (
    select p.app_dossier_id, count(*) n from public.app_console_photo p
     where p.present_in_hektor and p.visible is not false and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
     group by 1)
  select count(*) filter (where jsonb_array_length(d.images_preview_json_app) > coalesce(a.n, 0)) as longues,
         count(*) filter (where jsonb_array_length(d.images_preview_json_app) < coalesce(a.n, 0)) as courtes,
         count(*) filter (where jsonb_array_length(d.images_preview_json_app) = coalesce(a.n, 0)) as justes
    from public.app_dossier_current d left join attendu a using (app_dossier_id)
   where d.images_preview_json_app is not null
  ) t;

-- ===================== 3. LE VRAI PATCH, copie conforme =====================

drop table if exists tmp_maj, tmp_cibles, tmp_principale, tmp_galerie;

do $do$
declare
  v_src    text;
  v_new    text;
  v_a1     text := replace('select p.app_dossier_id, max(p.derives_generes_le) as dernier', chr(13), '');
  v_n1     text := replace('select p.app_dossier_id, max(greatest(p.derives_generes_le, p.absent_depuis)) as dernier', chr(13), '');
  v_a2     text := replace('where p_tout or p.derives_generes_le >= quand - make_interval(hours => greatest(1, p_heures))', chr(13), '');
  v_n2     text := replace('where p_tout or greatest(p.derives_generes_le, p.absent_depuis) >= quand - make_interval(hours => greatest(1, p_heures))', chr(13), '');
  v_emp    constant text := 'b87f6c6827fbedf0c8d8e8709d62a334';
  v_apres  constant text := 'ec8066616381cdb90df38ec561f1441f';
  v_vu     integer;
  v_longues_avant bigint;
  v_longues_apres bigint;
  v_courtes_avant bigint;
  v_courtes_apres bigint;
  v_rep    jsonb;
begin
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';

  if v_src is null then
    raise exception 'STOP : public.app_photos_remplir_adresses_app est introuvable';
  end if;

  -- ⓵ DEJA FAIT ?
  if position(v_n1 in v_src) > 0 and position(v_n2 in v_src) > 0 then
    raise notice 'DEJA FAIT : la fonction porte deja greatest(derives_generes_le, absent_depuis) -- rien a ecrire.';
    return;
  end if;

  -- ⓶ L'EMPREINTE DE DEPART
  if md5(v_src) <> v_emp then
    raise exception 'STOP : empreinte % au lieu de % -- la fonction a change depuis la mesure du 20/10. La RELIRE avant de patcher.',
      md5(v_src), v_emp;
  end if;

  -- ⓷ CHAQUE ANCRE EXACTEMENT UNE FOIS
  v_vu := (length(v_src) - length(replace(v_src, v_a1, ''))) / length(v_a1);
  if v_vu <> 1 then raise exception 'STOP : l ancre 1 (max(derives_generes_le)) apparait % fois (attendu 1)', v_vu; end if;
  v_vu := (length(v_src) - length(replace(v_src, v_a2, ''))) / length(v_a2);
  if v_vu <> 1 then raise exception 'STOP : l ancre 2 (where p_tout or ...) apparait % fois (attendu 1)', v_vu; end if;

  v_new := replace(replace(v_src, v_a1, v_n1), v_a2, v_n2);

  -- ⓸ LES CONTROLES AVANT D'ECRIRE
  if v_new = v_src then raise exception 'STOP : le patch n a RIEN change (lecon 2)'; end if;
  if md5(v_new) <> v_apres then
    raise exception 'STOP : la fonction neuve a l empreinte % au lieu de % -- ce n est pas le texte mesure', md5(v_new), v_apres;
  end if;

  -- les galeries trop longues AVANT (une galerie plus longue que les photos valides)
  with attendu as (
    select p.app_dossier_id, count(*) n from public.app_console_photo p
     where p.present_in_hektor and p.visible is not false and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
     group by 1)
  select count(*) filter (where jsonb_array_length(d.images_preview_json_app) > coalesce(a.n, 0)),
         count(*) filter (where jsonb_array_length(d.images_preview_json_app) < coalesce(a.n, 0))
    into v_longues_avant, v_courtes_avant
    from public.app_dossier_current d left join attendu a using (app_dossier_id)
   where d.images_preview_json_app is not null;

  execute v_new;

  -- ⓹ RELECTURE EN BASE
  select replace(pg_get_functiondef(p.oid), chr(13), '') into v_src
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.proname = 'app_photos_remplir_adresses_app';
  if md5(v_src) <> v_apres then
    raise exception 'STOP : apres ecriture, l empreinte est % au lieu de %', md5(v_src), v_apres;
  end if;

  -- ⓺ ON RECALCULE UNE FOIS, SUR 720 HEURES, ET ON VERIFIE
  v_rep := public.app_photos_remplir_adresses_app(720, false);
  if coalesce(v_rep->>'statut', '') <> 'ok' then
    raise exception 'STOP : la fonction a repondu % -- RIEN n est ecrit', v_rep::text;
  end if;

  with attendu as (
    select p.app_dossier_id, count(*) n from public.app_console_photo p
     where p.present_in_hektor and p.visible is not false and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
     group by 1)
  select count(*) filter (where jsonb_array_length(d.images_preview_json_app) > coalesce(a.n, 0)),
         count(*) filter (where jsonb_array_length(d.images_preview_json_app) < coalesce(a.n, 0))
    into v_longues_apres, v_courtes_apres
    from public.app_dossier_current d left join attendu a using (app_dossier_id)
   where d.images_preview_json_app is not null;

  if v_longues_apres <> 0 then
    raise exception 'STOP : % galerie(s) restent TROP LONGUES apres le recalcul (avant : %) -- RIEN n est ecrit', v_longues_apres, v_longues_avant;
  end if;
  -- ⚠ « trop courtes » : une annonce dont le negociateur vient d'ajouter des photos a une
  --   galerie en retard de quelques minutes (le run normal la rattrape). On ne bloque donc
  --   PAS sur un compte non nul : on bloque seulement si le patch en a CREE (apres > avant).
  --   Mesure du 20/10 a 10 h 15 : 1 (V770063289, photos ajoutees a 9 h 56).
  if v_courtes_apres > v_courtes_avant then
    raise exception 'STOP : % galerie(s) trop courtes apres le recalcul contre % avant -- le patch en a CREE, RIEN n est ecrit', v_courtes_apres, v_courtes_avant;
  end if;

  raise notice 'POSE : la date de reference d une photo est greatest(derives_generes_le, absent_depuis). Empreinte : %', md5(v_src);
  raise notice 'GALERIES TROP LONGUES : % avant, 0 apres. Trop courtes : % avant, % apres. Reponse de la fonction : %', v_longues_avant, v_courtes_avant, v_courtes_apres, v_rep::text;
end
$do$;

-- ============================== 4. APRES ===================================

insert into essai_mesures (etape, mesure, valeur)
select '4-apres ', 'trop longues / trop courtes           ', t.longues::text || ' / ' || t.courtes::text
         || case when t.longues = 0 then '  -- OK (les trop courtes sont des ajouts tres recents, rattrapes par le run normal)' else '  -- ECHEC' end
  from (
  with attendu as (
    select p.app_dossier_id, count(*) n from public.app_console_photo p
     where p.present_in_hektor and p.visible is not false and p.derives_json ? 'w400' and p.derives_json ? 'w1600'
     group by 1)
  select count(*) filter (where jsonb_array_length(d.images_preview_json_app) > coalesce(a.n, 0)) as longues,
         count(*) filter (where jsonb_array_length(d.images_preview_json_app) < coalesce(a.n, 0)) as courtes,
         count(*) filter (where jsonb_array_length(d.images_preview_json_app) = coalesce(a.n, 0)) as justes
    from public.app_dossier_current d left join attendu a using (app_dossier_id)
   where d.images_preview_json_app is not null
  ) t;

insert into essai_mesures (etape, mesure, valeur)
select '4-apres ', 'galeries justes dont le contenu change',
       count(*) filter (where md5(d.images_preview_json_app::text) <> j.h or d.photo_url_listing_app is distinct from j.couv)::text
       || ' sur ' || count(*)::text || '  (attendu 0, ou quelques-unes recalculees a juste titre)'
  from essai_justes j join public.app_dossier_current d using (app_dossier_id);

insert into essai_mesures (etape, mesure, valeur)
select '4-apres ', 'V320063214 : galerie / couverture     ',
       jsonb_array_length(d.images_preview_json_app)::text || ' / '
       || case when d.photo_url_listing_app is not null then 'presente' else 'ABSENTE' end
  from public.app_dossier_current d where d.numero_dossier = 'V320063214';

-- ========================== 5. LE VRAI INVERSE =============================

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

insert into essai_mesures (etape, mesure, valeur)
select '5-retour', 'empreinte revenue                     ',
       case when md5(s) = 'b87f6c6827fbedf0c8d8e8709d62a334' then 'oui, a l octet pres' else 'NON : ' || md5(s) end
  from (select replace(pg_get_functiondef(p.oid), chr(13), '') as s
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname='public' and p.proname='app_photos_remplir_adresses_app') z;

insert into essai_mesures (etape, mesure, valeur)
select '5-retour', 'aucune trace de absent_depuis         ',
       case when position('absent_depuis' in s) = 0 then 'oui' else 'NON' end
  from (select replace(pg_get_functiondef(p.oid), chr(13), '') as s
          from pg_proc p join pg_namespace n on n.oid = p.pronamespace
         where n.nspname='public' and p.proname='app_photos_remplir_adresses_app') z;

-- ================== 6. L ERREUR VOLONTAIRE : tout est annule ================
-- ⚠ Le compte rendu voyage DANS le message : un SELECT d une transaction qui
--   echoue n est pas toujours rendu par l editeur SQL.

do $fin$
declare v_txt text;
begin
  select string_agg(etape || ' | ' || mesure || ' = ' || valeur, chr(10) order by id)
    into v_txt from essai_mesures;
  raise exception '%', 'ESSAI ANNULE -- rien n a ete ecrit, ni la fonction ni les galeries.'
    || chr(10) || v_txt;
end
$fin$;

rollback;
