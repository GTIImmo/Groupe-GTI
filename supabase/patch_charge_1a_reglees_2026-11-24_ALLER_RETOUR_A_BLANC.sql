-- patch_charge_1a_reglees_2026-11-24 -- genere par phase2/checks/cases_vides_generer_patchs_2026-11-24.py (son 5e mot du 24/11 : « rien ne s'ecrit sans mon accord sur le patch »)
-- Retour arriere : patch_charge_1a_reglees_2026-11-24_INVERSE.sql . Controle : patch_charge_1a_reglees_2026-11-24_REPETITION.sql
-- ⛔ A BLANC : le patch PUIS son inverse, dans la MEME transaction ; aucun commit ; erreur voulue a la fin.

begin;

-- ─── ① LES GARDES : chaque mandat est VIDE au carnet et au reflet, et il existe au registre ────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_mandat_register_current_avant_charge_1a_reglees_20261124') is not null then
    raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas';
  end if;
  if to_regclass('public.app_classeur_realignement_journal') is null then
    raise exception '⛔ garde : le journal du realignement n''existe pas (patch des 42 d''abord)';
  end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'charge_1a_reglees_2026-11-24';
  if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_mandat_champ_app k join (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481')) m(annonce, numero)
      on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission';
  if n <> 0 then raise exception '⛔ garde : % mandat(s) portent DEJA une charge au carnet -- on n''ecrase jamais', n; end if;
  select count(*) into n from public.app_mandat_register_current r join (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481')) m(annonce, numero)
      on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero
   where nullif(btrim(coalesce(r.mandat_charge_honoraires_app, '')), '') is null;
  if n <> 3 then raise exception '⛔ garde : % mandat(s) au registre avec un reflet vide sur 3', n; end if;
  select count(*) into n from public.app_mandat_register_current r where r.hektor_annonce_id::text in ('17548', '23297', '47542');
  if n <> 3 then raise exception '⛔ garde : les annonces portent % mandat(s) au registre au lieu de 3', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', m.annonce, m.numero, coalesce(k.valeur_app, '-'), coalesce(k.origine, '-'), coalesce(k.ecrit_par, '-'), coalesce(r.mandat_charge_honoraires_app, '-')), ';' order by m.annonce, m.numero), '')) from (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481')) m(annonce, numero) left join public.app_mandat_champ_app k on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission' left join public.app_mandat_register_current r on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero);
  if e <> 'fba1a157b7512a77f8495cc721151dc3' then raise exception '⛔ garde : empreinte % au lieu de fba1a157b7512a77f8495cc721151dc3', e; end if;
  raise notice '✅ gardes : 3 mandats vides au carnet et au reflet ; empreinte %', e;
end $$;

-- ─── ② LA SAUVEGARDE DATEE : les lignes du registre des mandats de ces annonces (le reflet) ──────────────────────────────
create table public.app_mandat_register_current_avant_charge_1a_reglees_20261124 as
  select * from public.app_mandat_register_current where hektor_annonce_id::text in ('17548', '23297', '47542');
revoke all on public.app_mandat_register_current_avant_charge_1a_reglees_20261124 from public, anon, authenticated;

-- ─── ③ LE JOURNAL : chaque ecriture avec SA LIGNE D'ORIGINE (id_unique, n° au Sheet) et SA PLACE (le mandat) ──────────
alter table public.app_classeur_realignement_journal add column if not exists mandat_annonce text;
alter table public.app_classeur_realignement_journal add column if not exists mandat_numero text;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, valeur, ligne_origine, ligne_origine_num, lot_origine, pourquoi, ecrit_par, mandat_annonce, mandat_numero)
select 'charge_1a_reglees_2026-11-24', v.n, 'charge_commission', 'app_mandat_champ_app.valeur_app (charge_commission)', 'POSER (case vide)',
       v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, d.app_dossier_uuid, null, v.valeur, v.ligne, v.num,
       'Sheet (colonne Charge Commission) -- son 5e mot du 24/11', v.pourquoi, 'patch_charge_1a_reglees_2026-11-24', v.annonce, v.numero
  from (values
    (1, '125888d3', 4211, 23986, '47542', '17840', 'acquereur', '① LES VENTES REGLEES D''ABORD (son 5e mot du 24/11) ; etat au Sheet : Vente reglee ; Commission TTC 9000 EUR'),
    (2, '5YUGE9KA', 3, 11134, '23297', '17564', 'acquereur', '① LES VENTES REGLEES D''ABORD (son 5e mot du 24/11) ; etat au Sheet : Vente reglee ; Commission TTC 5000 EUR'),
    (3, '78004641', 4550, 30778, '17548', '17481', 'acquereur', '① LES VENTES REGLEES D''ABORD (son 5e mot du 24/11) ; etat au Sheet : Vente reglee ; Commission TTC 7000 EUR')
  ) v(n, ligne, num, piece, annonce, numero, valeur, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = v.piece;

-- ─── ④ LE GESTE : le carnet (la valeur LUE AU JOURNAL), puis le reflet, annonce par annonce (jamais tout le registre) ────
insert into public.app_mandat_champ_app (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, ecrit_par, ecrit_le)
select j.mandat_annonce, j.mandat_numero, 'charge_commission', j.valeur, 'classeur', 'classeur:' || j.ligne_origine, now()
  from public.app_classeur_realignement_journal j where j.lot = 'charge_1a_reglees_2026-11-24'
on conflict (hektor_annonce_id, numero_mandat, champ) do nothing;
select public.app_reposer_charge_mandat_app('17548', 10000);
select public.app_reposer_charge_mandat_app('23297', 10000);
select public.app_reposer_charge_mandat_app('47542', 10000);

-- ─── ⑤ LES CONTROLES ─────────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_mandat_champ_app k on k.hektor_annonce_id = j.mandat_annonce and k.numero_mandat = j.mandat_numero
     and k.champ = 'charge_commission' and k.valeur_app = j.valeur and k.origine = 'classeur'
     and k.ecrit_par = 'classeur:' || j.ligne_origine
   where j.lot = 'charge_1a_reglees_2026-11-24';
  if n <> 3 then raise exception '⛔ controle : % charge(s) au carnet sur 3', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_mandat_register_current r on r.hektor_annonce_id::text = j.mandat_annonce and r.numero_mandat::text = j.mandat_numero
     and r.mandat_charge_honoraires_app = j.valeur
   where j.lot = 'charge_1a_reglees_2026-11-24';
  if n <> 3 then raise exception '⛔ controle : % reflet(s) pose(s) sur 3', n; end if;
  -- rien d'autre n'a bouge dans le registre de ces annonces
  select count(*) into n from public.app_mandat_register_current r
    join public.app_mandat_register_current_avant_charge_1a_reglees_20261124 s
      on s.hektor_annonce_id = r.hektor_annonce_id and s.numero_mandat = r.numero_mandat
   where r.mandat_charge_honoraires_app is distinct from s.mandat_charge_honoraires_app
     and (r.hektor_annonce_id::text, r.numero_mandat::text) not in (select mandat_annonce, mandat_numero
                                                                   from public.app_classeur_realignement_journal where lot = 'charge_1a_reglees_2026-11-24');
  if n <> 0 then raise exception '⛔ controle : % autre(s) reflet(s) ont bouge', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'charge_1a_reglees_2026-11-24' and ligne_origine is not null and ligne_origine_num is not null;
  if n <> 3 then raise exception '⛔ controle : % ligne(s) d''origine au journal sur 3', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', m.annonce, m.numero, coalesce(k.valeur_app, '-'), coalesce(k.origine, '-'), coalesce(k.ecrit_par, '-'), coalesce(r.mandat_charge_honoraires_app, '-')), ';' order by m.annonce, m.numero), '')) from (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481')) m(annonce, numero) left join public.app_mandat_champ_app k on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission' left join public.app_mandat_register_current r on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero);
  if e <> '04f45cf7db6dfb1617d27ce972f9810f' then raise exception '⛔ controle : empreinte apres % au lieu de 04f45cf7db6dfb1617d27ce972f9810f', e; end if;
  raise notice '✅ 3 charges au carnet, 3 reflets, 0 autre reflet, ligne d''origine au journal ; empreinte apres %', e;
end $$;

do $$ declare e text; begin e := (select md5(coalesce(string_agg(concat_ws('|', m.annonce, m.numero, coalesce(k.valeur_app, '-'), coalesce(k.origine, '-'), coalesce(k.ecrit_par, '-'), coalesce(r.mandat_charge_honoraires_app, '-')), ';' order by m.annonce, m.numero), '')) from (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481')) m(annonce, numero) left join public.app_mandat_champ_app k on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission' left join public.app_mandat_register_current r on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero); raise notice 'APRES %', e; perform set_config('ar.apres', e, true); end $$;

-- ─── LE RETOUR : retirer du carnet CE QUE CE LOT A POSE (et seulement cela), reposer le reflet ; le journal et la sauvegarde restent
do $$
declare n int;
begin
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_mandat_champ_app k on k.hektor_annonce_id = j.mandat_annonce and k.numero_mandat = j.mandat_numero
     and k.champ = 'charge_commission' and k.valeur_app = j.valeur and k.origine = 'classeur' and k.ecrit_par = 'classeur:' || j.ligne_origine
   where j.lot = 'charge_1a_reglees_2026-11-24';
  if n <> 3 then raise exception '⛔ garde du retour : % charge(s) du lot retrouvee(s) sur 3 (une saisie est passee ?)', n; end if;
end $$;
delete from public.app_mandat_champ_app k using public.app_classeur_realignement_journal j
 where j.lot = 'charge_1a_reglees_2026-11-24' and k.hektor_annonce_id = j.mandat_annonce and k.numero_mandat = j.mandat_numero
   and k.champ = 'charge_commission' and k.valeur_app = j.valeur and k.origine = 'classeur' and k.ecrit_par = 'classeur:' || j.ligne_origine;
select public.app_reposer_charge_mandat_app('17548', 10000);
select public.app_reposer_charge_mandat_app('23297', 10000);
select public.app_reposer_charge_mandat_app('47542', 10000);
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_mandat_register_current r
    join public.app_mandat_register_current_avant_charge_1a_reglees_20261124 s on s.hektor_annonce_id = r.hektor_annonce_id and s.numero_mandat = r.numero_mandat
   where r.mandat_charge_honoraires_app is distinct from s.mandat_charge_honoraires_app;
  if n <> 0 then raise exception '⛔ controle du retour : % reflet(s) differents de la sauvegarde', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', m.annonce, m.numero, coalesce(k.valeur_app, '-'), coalesce(k.origine, '-'), coalesce(k.ecrit_par, '-'), coalesce(r.mandat_charge_honoraires_app, '-')), ';' order by m.annonce, m.numero), '')) from (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481')) m(annonce, numero) left join public.app_mandat_champ_app k on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission' left join public.app_mandat_register_current r on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero);
  if e <> 'fba1a157b7512a77f8495cc721151dc3' then raise exception '⛔ controle du retour : empreinte % au lieu de fba1a157b7512a77f8495cc721151dc3 (celle d''AVANT)', e; end if;
end $$;

do $$ declare e text; begin e := (select md5(coalesce(string_agg(concat_ws('|', m.annonce, m.numero, coalesce(k.valeur_app, '-'), coalesce(k.origine, '-'), coalesce(k.ecrit_par, '-'), coalesce(r.mandat_charge_honoraires_app, '-')), ';' order by m.annonce, m.numero), '')) from (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481')) m(annonce, numero) left join public.app_mandat_champ_app k on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission' left join public.app_mandat_register_current r on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero); raise exception 'ALLER-RETOUR A BLANC VERT : apres = % ; retour = % -- RIEN N''EST ECRIT (erreur voulue)', current_setting('ar.apres'), e; end $$;
