-- ============================================================================
-- CHANTIER 7-8 -- LA GALERIE SUIT LE RETRAIT D'UNE PHOTO CHEZ HEKTOR
-- 20/10/2026
-- ============================================================================
-- CE QUI A ETE VU (mesure du 20/10, lecture seule) :
--   la fiche de l'annonce V320063214 (app_dossier_id 7589201) disait « 26 photos »
--   alors que la gestion des photos en montrait 12.
--     · 26 lignes dans app_console_photo : 12 presentes chez Hektor, 14 RETIREES
--       (present_in_hektor = false, absent_depuis du 15/10) -- le negociateur a
--       remplace ses photos (anciennes 4871xx, nouvelles 4876xx).
--     · images_preview_json_app (la GALERIE de la boite publique) : 26 entrees.
--   -> la galerie garde les 14 photos retirees.
--
-- LA CAUSE : app_photos_remplir_adresses_app fabrique la galerie avec le BON
--   filtre (present_in_hektor et visible is not false), mais ne CIBLE un dossier
--   que si une photo a un `derives_generes_le` plus recent que `adresses_app_le`
--   (ou si les adresses sont NULL). Marquer une photo ABSENTE (absent_depuis) ne
--   touche pas `derives_generes_le` : la galerie n'est donc jamais refaite.
--
-- L'AMPLEUR (20/10) : 10 260 dossiers avec galerie, 10 203 justes, 57 TROP
--   LONGUES, 354 photos en trop, toutes « retirees chez Hektor » (absences du 15
--   au 18/10), 0 masquee. Le defaut GROSSIT a chaque photo remplacee chez Hektor.
--   Les 57 ont toutes encore des photos valides (0 dossier a 0 photo) : la
--   fonction les recalculera. AVANT le patch, 0 de ces 57 est cible ; APRES, les 57.
--
-- QUI LIT CETTE GALERIE : la fiche (App.tsx, `images`), la vitrine Android
--   (Ecrans Android/export_project_vitrine.py:167, :221), l'espace client.
--
-- CE QUE CE PATCH FAIT, EN DEUX TEMPS DANS UNE SEULE TRANSACTION :
--   1. dans `tmp_maj`, la date de reference d'une photo devient
--        greatest(derives_generes_le, absent_depuis)
--      (greatest ignore les NULL : une photo sans derive mais retiree compte). Deux
--      remplacements, deux ancres sur UNE ligne chacune, chacune presente 1 fois.
--   2. il RELANCE la fonction une fois, sur 720 heures, pour reparer les 57 tout de
--      suite (la nuit, la fenetre est de 48 h : les retraits du 15 au 17/10 seraient
--      sortis de la fenetre). Puis il VERIFIE : plus aucune galerie trop longue,
--      aucune trop courte. Sinon : STOP, et RIEN n'est ecrit.
--
-- CE QUE CA NE CHANGE PAS : le filtre de la galerie (deja bon), le drapeau
--   `visible`, la couverture des dossiers deja justes. Les galeries justes ne
--   sont pas touchees (la repetition le MESURE).
--
-- ⚠ LIMITE CONNUE, NON TRAITEE ICI : un dossier dont la DERNIERE photo valide est
--   retiree n'aura pas de ligne dans tmp_galerie, donc sa galerie ne sera pas
--   videe. 0 cas aujourd'hui (mesure du 20/10). A traiter si le cas apparait.
-- ⚠ SYMETRIQUE, MESURE A ZERO : une photo qui REVIENT chez Hektor ne declenche pas
--   non plus le recalcul. 0 galerie trop courte aujourd'hui.
--
-- RETOUR ARRIERE : patch_chantier7_8_galerie_photo_retiree_2026-10-20_INVERSE.sql
--   (il remet la fonction ; les galeries recalculees restent JUSTES).
-- EPREUVE       : patch_chantier7_8_galerie_photo_retiree_2026-10-20_REPETITION.sql
--
-- ⚠⚠ ANCRES SUR UNE SEULE LIGNE + replace(chr(13)) DES DEUX COTES (lecon 30).
-- EMPREINTE de depart  b87f6c6827fbedf0c8d8e8709d62a334  (fonction patchee le 19/10)
-- EMPREINTE attendue   ec8066616381cdb90df38ec561f1441f  (calculee en lecture seule le 20/10)
-- ============================================================================

begin;

set local lock_timeout = '5s';

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

commit;
