-- =====================================================================
-- RETOUR ARRIERE de l'etape (1) de la charge -- 04/11/2026
-- =====================================================================
-- ⚠ IL DEFAIT DEUX CHOSES, ET IL FAUT CHOISIR : lire les deux blocs avant
--   de coller. Le bloc 2 est commente EXPRES -- il efface des donnees.
--
-- RAPPEL : un retour arriere ne juge que SA part. Il verifie d'abord qu'il
-- ne reste aucune trace de ce qu'il devait retirer.
-- =====================================================================

-- ---------------------------------------------------------------------
-- BLOC 1 -- REMETTRE LES DEUX FONCTIONS DANS LEUR ETAT D'AVANT
-- ---------------------------------------------------------------------
-- ⛔⛔ NE PAS COLLER CE BLOC SEUL SI LES 837 LIGNES SONT ENCORE EN BASE :
--   la repose redeviendrait aveugle au classeur et, au premier appel,
--   EFFACERAIT les 837 valeurs du registre (son NOT EXISTS ne verrait
--   plus les lignes 'classeur'). Dans ce cas, coller le BLOC 2 D'ABORD.
do $$
declare src text; vue text;
begin
  if exists (select 1 from public.app_mandat_champ_app
              where champ='charge_commission' and origine='classeur') then
    raise exception 'ARRET : des lignes origine=classeur sont encore en base. '
                    'Coller le BLOC 2 d abord, sinon la repose les effacera du registre.';
  end if;

  for src in
    select s.definition from public.app_sauvegarde_fonction_20261104 s
     where s.nom in ('app_reposer_charge_mandat_app','app_set_mandat_charge_optimistic')
  loop
    execute src;
  end loop;

  select md5(pg_get_functiondef(p.oid)) into vue
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where p.proname='app_reposer_charge_mandat_app' and n.nspname='public';
  if vue <> 'f84d178ea95e06e030a5c5a2681dfb6f' then
    raise exception 'ARRET : la repose n est pas revenue a son etat d avant (md5 %)', vue;
  end if;
  select md5(pg_get_functiondef(p.oid)) into vue
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where p.proname='app_set_mandat_charge_optimistic' and n.nspname='public';
  if vue <> '9c96157ba520c57156a82fd987f193f0' then
    raise exception 'ARRET : la porte de saisie n est pas revenue a son etat d avant (md5 %)', vue;
  end if;
end $$;

-- ---------------------------------------------------------------------
-- BLOC 2 -- RETIRER LES 837 LIGNES DU CLASSEUR
-- ---------------------------------------------------------------------
-- ⚠ COMMENTE EXPRES : il EFFACE des donnees justes. Ne le decommenter que
--   si Frederic revient sur sa decision du 04/11 (« oui, elle fait foi »).
--   Il ne touche QUE les lignes origine='classeur' : une saisie humaine
--   faite depuis (origine='mandat_app') est INTOUCHEE.
--
-- with retires as (
--   delete from public.app_mandat_champ_app
--    where champ='charge_commission' and origine='classeur'
--   returning 1)
-- select (select count(*) from retires) as lignes_retirees;
-- select public.app_reposer_charge_mandat_app(null, 10000) as repose;
-- -- ⚠ la repose doit alors annoncer « effacees » = le nombre retire.

-- ---------------------------------------------------------------------
-- CONTROLE DU RETOUR ARRIERE
-- ---------------------------------------------------------------------
select
  (select md5(pg_get_functiondef(p.oid)) = 'f84d178ea95e06e030a5c5a2681dfb6f'
     from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where p.proname='app_reposer_charge_mandat_app' and n.nspname='public')
    as A_la_repose_est_revenue,
  (select md5(pg_get_functiondef(p.oid)) = '9c96157ba520c57156a82fd987f193f0'
     from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where p.proname='app_set_mandat_charge_optimistic' and n.nspname='public')
    as B_la_saisie_est_revenue,
  (select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.proname='app_reposer_charge_mandat_app'
      and pg_get_functiondef(p.oid) like '%''classeur''%') = 0
    as C_aucune_trace_du_classeur_dans_la_repose,
  (select count(*) from public.app_mandat_champ_app
    where champ='charge_commission' and origine='mandat_app')
    as D_les_saisies_humaines_restantes,
  (select count(*) from public.app_sauvegarde_charge_avant_20261104)
    as E_le_carnet_d_avant_est_toujours_sauve;
