-- =====================================================================
-- CONTROLE de l'etape (1) de la charge -- 04/11/2026
-- A COLLER APRES le patch ET les donnees. Les 14 colonnes doivent etre vertes.
-- =====================================================================
-- ⚠ Un ZERO ne se croit pas sans temoin positif : C09 et C10 montrent une
--   valeur REELLE dans chaque classe, donc les zeros de C03, C05, C06 et
--   C11 ont un sens.
-- ⚠ Un controle qui AGREGE perd ce qui sert a agir : C15 et C16 NOMMENT.
-- =====================================================================

select
  -- LE CARNET FAIT FOI
  (select count(*) from app_mandat_champ_app where champ='charge_commission') = 837
    as c01_le_carnet_porte_837,
  (select count(*) from app_mandat_champ_app
    where champ='charge_commission' and origine='classeur') = 837
    as c02_toutes_viennent_du_classeur,
  (select count(*) from app_mandat_champ_app where champ='charge_commission'
     and valeur_app not in ('vendeur','acquereur')) = 0
    as c03_aucune_valeur_hors_vocabulaire,

  -- LE REGISTRE EST LE REFLET, ET IL EST FIDELE
  (select count(*) from app_mandat_register_current
    where nullif(trim(coalesce(mandat_charge_honoraires_app,'')),'') is not null) = 837
    as c04_le_registre_porte_837,
  (select count(*) from app_mandat_champ_app k
     join app_mandat_register_current r
       on r.hektor_annonce_id::text=k.hektor_annonce_id
      and r.numero_mandat::text=k.numero_mandat
    where k.champ='charge_commission'
      and coalesce(r.mandat_charge_honoraires_app,'') <> k.valeur_app) = 0
    as c05_aucun_ecart_carnet_registre,
  (select count(*) from app_mandat_register_current r
    where nullif(trim(coalesce(r.mandat_charge_honoraires_app,'')),'') is not null
      and not exists (select 1 from app_mandat_champ_app k
                       where k.champ='charge_commission'
                         and k.hektor_annonce_id=r.hektor_annonce_id::text
                         and k.numero_mandat=r.numero_mandat::text)) = 0
    as c06_aucune_valeur_orpheline_au_registre,

  -- LA REPARTITION, conforme au classeur (894/61 avant le pont)
  (select count(*) from app_mandat_champ_app
    where champ='charge_commission' and valeur_app='vendeur') = 801 as c07_801_vendeur,
  (select count(*) from app_mandat_champ_app
    where champ='charge_commission' and valeur_app='acquereur') = 36 as c08_36_acquereur,

  -- ⭐ TEMOINS POSITIFS, mesures par le script, un par CLASSE
  (select valeur_app from app_mandat_champ_app
    where champ='charge_commission' and hektor_annonce_id='10702'
      and numero_mandat='2154') = 'vendeur' as c09_temoin_vendeur_10702,
  (select valeur_app from app_mandat_champ_app
    where champ='charge_commission' and hektor_annonce_id='11820'
      and numero_mandat='17888') = 'acquereur' as c10_temoin_acquereur_11820,

  -- ⭐ TEMOIN INVERSE : les 2 mandats en CONFLIT ne doivent PAS y etre.
  --   (ma 1re version du script les avait poses avec une valeur ARBITRAIRE :
  --    la premiere rencontree. Retirees, et le script corrige ecarte.)
  (select count(*) from app_mandat_champ_app where champ='charge_commission'
     and (hektor_annonce_id, numero_mandat)
         in (('46338','17322'),('47174','17639'))) = 0
    as c11_les_2_conflits_ne_sont_pas_poses,

  -- LE MECANISME TIENT
  (select pg_get_functiondef(p.oid) like '%in (''mandat_app'', ''classeur'')%'
     from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where p.proname='app_reposer_charge_mandat_app' and n.nspname='public')
    as c12_la_repose_voit_le_classeur,
  (select (select count(*) from regexp_matches(pg_get_functiondef(p.oid),
             'origine\s*=\s*''mandat_app'',', 'g')) = 1
     from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where p.proname='app_set_mandat_charge_optimistic' and n.nspname='public')
    as c13_la_saisie_humaine_garde_la_main,
  (select count(*) from app_sauvegarde_fonction_20261104) >= 4
    as c14_les_sauvegardes_existent;

-- ---------------------------------------------------------------------
-- CE QUI RESTE A LA MAIN -- on NOMME, on n'agrege pas
-- ---------------------------------------------------------------------
-- C15 : les 2 mandats dont le classeur se contredit. A trancher par Frederic.
select '46338/17322' as mandat, 'acquereur (ID afd672fa) contre vendeur (ID cc33cc38)' as le_desaccord
union all
select '47174/17639', 'vendeur (ID 2c2566d7) contre acquereur (ID df0ce30c)';

-- C16 : les mandats du classeur ECARTES de la 1re passe, par motif.
--   29 liens « a valider » ou « bonne » . 25 lignes non reliees par le gel
--   . 4 affaires sans annonce ni mandat . 3 mandats absents du registre
--   -> voir notice/POSE_CHARGE_CLASSEUR_2026-11-04.md, qui les liste.
