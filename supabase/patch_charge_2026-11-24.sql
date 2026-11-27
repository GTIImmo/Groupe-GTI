-- patch_charge_2026-11-24 -- genere par phase2/checks/cases_vides_generer_patchs_2026-11-24.py (son 5e mot du 24/11 : « rien ne s'ecrit sans mon accord sur le patch »)
-- Retour arriere : patch_charge_2026-11-24_INVERSE.sql . Controle : patch_charge_2026-11-24_REPETITION.sql

begin;

-- ─── ① LES GARDES : chaque mandat est VIDE au carnet et au reflet, et il existe au registre ────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_mandat_register_current_avant_charge_20261124') is not null then
    raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas';
  end if;
  if to_regclass('public.app_classeur_realignement_journal') is null then
    raise exception '⛔ garde : le journal du realignement n''existe pas (patch des 42 d''abord)';
  end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'charge_2026-11-24';
  if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_mandat_champ_app k join (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481'), ('46338', '17322'), ('47174', '17639'), ('63490', '18999'), ('59164', '18127'), ('59339', '18143'), ('54734', '18053'), ('17597', '18973'), ('62336', '18648'), ('62766', '18773'), ('11695', '17296'), ('59637', '18286'), ('62934', '18950'), ('63299', '18942'), ('39684', '17987'), ('61893', '18996')) m(annonce, numero)
      on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission';
  if n <> 0 then raise exception '⛔ garde : % mandat(s) portent DEJA une charge au carnet -- on n''ecrase jamais', n; end if;
  select count(*) into n from public.app_mandat_register_current r join (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481'), ('46338', '17322'), ('47174', '17639'), ('63490', '18999'), ('59164', '18127'), ('59339', '18143'), ('54734', '18053'), ('17597', '18973'), ('62336', '18648'), ('62766', '18773'), ('11695', '17296'), ('59637', '18286'), ('62934', '18950'), ('63299', '18942'), ('39684', '17987'), ('61893', '18996')) m(annonce, numero)
      on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero
   where nullif(btrim(coalesce(r.mandat_charge_honoraires_app, '')), '') is null;
  if n <> 18 then raise exception '⛔ garde : % mandat(s) au registre avec un reflet vide sur 18', n; end if;
  select count(*) into n from public.app_mandat_register_current r where r.hektor_annonce_id::text in ('11695', '17548', '17597', '23297', '39684', '46338', '47174', '47542', '54734', '59164', '59339', '59637', '61893', '62336', '62766', '62934', '63299', '63490');
  if n <> 18 then raise exception '⛔ garde : les annonces portent % mandat(s) au registre au lieu de 18', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', m.annonce, m.numero, coalesce(k.valeur_app, '-'), coalesce(k.origine, '-'), coalesce(k.ecrit_par, '-'), coalesce(r.mandat_charge_honoraires_app, '-')), ';' order by m.annonce, m.numero), '')) from (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481'), ('46338', '17322'), ('47174', '17639'), ('63490', '18999'), ('59164', '18127'), ('59339', '18143'), ('54734', '18053'), ('17597', '18973'), ('62336', '18648'), ('62766', '18773'), ('11695', '17296'), ('59637', '18286'), ('62934', '18950'), ('63299', '18942'), ('39684', '17987'), ('61893', '18996')) m(annonce, numero) left join public.app_mandat_champ_app k on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission' left join public.app_mandat_register_current r on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero);
  if e <> '950158733b79f7ee5083153d754453ab' then raise exception '⛔ garde : empreinte % au lieu de 950158733b79f7ee5083153d754453ab', e; end if;
  raise notice '✅ gardes : 18 mandats vides au carnet et au reflet ; empreinte %', e;
end $$;

-- ─── ② LA SAUVEGARDE DATEE : les lignes du registre des mandats de ces annonces (le reflet) ──────────────────────────────
create table public.app_mandat_register_current_avant_charge_20261124 as
  select * from public.app_mandat_register_current where hektor_annonce_id::text in ('11695', '17548', '17597', '23297', '39684', '46338', '47174', '47542', '54734', '59164', '59339', '59637', '61893', '62336', '62766', '62934', '63299', '63490');
revoke all on public.app_mandat_register_current_avant_charge_20261124 from public, anon, authenticated;

-- ─── ③ LE JOURNAL : chaque ecriture avec SA LIGNE D'ORIGINE (id_unique, n° au Sheet) et SA PLACE (le mandat) ──────────
alter table public.app_classeur_realignement_journal add column if not exists mandat_annonce text;
alter table public.app_classeur_realignement_journal add column if not exists mandat_numero text;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, valeur, ligne_origine, ligne_origine_num, lot_origine, pourquoi, ecrit_par, mandat_annonce, mandat_numero)
select 'charge_2026-11-24', v.n, 'charge_commission', 'app_mandat_champ_app.valeur_app (charge_commission)',
       case when v.pourquoi like 'NOMMEE%' then 'NOMMEE (ecartee : la vente reglee fait foi)' else 'POSER (case vide)' end,
       v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, d.app_dossier_uuid, null, v.valeur, v.ligne, v.num,
       'Sheet (colonne Charge Commission) -- son 5e mot du 24/11', v.pourquoi, 'patch_charge_2026-11-24', v.annonce, v.numero
  from (values
    (1, '125888d3', 4211, 23986, '47542', '17840', 'acquereur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Vente reglee ; Commission TTC 9000 EUR'),
    (2, '5YUGE9KA', 3, 11134, '23297', '17564', 'acquereur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Vente reglee ; Commission TTC 5000 EUR'),
    (3, '78004641', 4550, 30778, '17548', '17481', 'acquereur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Vente reglee ; Commission TTC 7000 EUR'),
    (4, 'cc33cc38', 4634, 28965, '46338', '17322', 'vendeur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Vente reglee ; Commission TTC 6000 EUR'),
    (5, 'df0ce30c', 4670, 30813, '47174', '17639', 'acquereur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Vente reglee ; Commission TTC 5000 EUR'),
    (6, '1eec6575', 4799, 30825, '63490', '18999', 'vendeur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Compromis en attente ; Commission TTC 3500 EUR'),
    (7, '2b924f5f', 4498, 28633, '59164', '18127', 'vendeur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Annulee ; Commission TTC 3000 EUR'),
    (8, '4cbc128d', 4492, 28687, '59339', '18143', 'vendeur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Annulee ; Commission TTC 6790 EUR'),
    (9, '54376c72', 4801, 30830, '54734', '18053', 'acquereur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Offre d''achat ; Commission TTC 1800 EUR'),
    (10, '55b49232', 4804, 30837, '17597', '18973', 'vendeur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Offre d''achat ; Commission TTC 5699 EUR'),
    (11, '5e4c8881', 4797, 30820, '62336', '18648', 'vendeur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Compromis en attente ; Commission TTC 6900 EUR'),
    (12, '70740f2f', 4800, 30824, '62766', '18773', 'vendeur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Offre d''achat ; Commission TTC 4800 EUR'),
    (13, '729ba8dc', 4306, 6103, '11695', '17296', 'vendeur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Annulee ; Commission TTC 6130 EUR'),
    (14, 'b43e76f5', 4798, 30826, '59637', '18286', 'acquereur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Offre d''achat ; Commission TTC 10000 EUR'),
    (15, 'b72db9d5', 4803, 30836, '62934', '18950', 'vendeur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Offre d''achat ; Commission TTC 4000 EUR'),
    (16, 'b7439331', 4791, 30809, '63299', '18942', 'vendeur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Offre d''achat ; Commission TTC 1000 EUR'),
    (17, 'f90b0418', 4455, 19049, '39684', '17987', 'acquereur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Annulee ; Commission TTC 7000 EUR'),
    (18, 'ffcf30e6', 4802, 30829, '61893', '18996', 'vendeur', '① LES 20 CHARGES (son 5e mot du 24/11 ; les 5 ventes reglees en tete) ; etat au Sheet : Offre d''achat ; Commission TTC 8500 EUR'),
    (19, 'afd672fa', 4399, 23329, '46338', '17322', 'acquereur', 'NOMMEE, ECARTEE -- SA DECISION du 24/11 (6e mot, ②) : la vente reglee (cc33cc38) fait foi sur ce mandat ; une ligne annulee n''a jamais donne lieu a facture, sa charge n''a jamais ete appliquee ; etat au Sheet : Annulee ; Commission TTC 6000 EUR'),
    (20, '2c2566d7', 4343, 23801, '47174', '17639', 'vendeur', 'NOMMEE, ECARTEE -- SA DECISION du 24/11 (6e mot, ②) : la vente reglee (df0ce30c) fait foi sur ce mandat ; une ligne annulee n''a jamais donne lieu a facture, sa charge n''a jamais ete appliquee ; etat au Sheet : Annulee ; Commission TTC 8000 EUR')
  ) v(n, ligne, num, piece, annonce, numero, valeur, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = v.piece;

-- ─── ④ LE GESTE : le carnet (la valeur LUE AU JOURNAL), puis le reflet, annonce par annonce (jamais tout le registre) ────
insert into public.app_mandat_champ_app (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, ecrit_par, ecrit_le)
select j.mandat_annonce, j.mandat_numero, 'charge_commission', j.valeur, 'classeur', 'classeur:' || j.ligne_origine, now()
  from public.app_classeur_realignement_journal j where j.lot = 'charge_2026-11-24' and j.geste = 'POSER (case vide)'
on conflict (hektor_annonce_id, numero_mandat, champ) do nothing;
select public.app_reposer_charge_mandat_app('11695', 10000);
select public.app_reposer_charge_mandat_app('17548', 10000);
select public.app_reposer_charge_mandat_app('17597', 10000);
select public.app_reposer_charge_mandat_app('23297', 10000);
select public.app_reposer_charge_mandat_app('39684', 10000);
select public.app_reposer_charge_mandat_app('46338', 10000);
select public.app_reposer_charge_mandat_app('47174', 10000);
select public.app_reposer_charge_mandat_app('47542', 10000);
select public.app_reposer_charge_mandat_app('54734', 10000);
select public.app_reposer_charge_mandat_app('59164', 10000);
select public.app_reposer_charge_mandat_app('59339', 10000);
select public.app_reposer_charge_mandat_app('59637', 10000);
select public.app_reposer_charge_mandat_app('61893', 10000);
select public.app_reposer_charge_mandat_app('62336', 10000);
select public.app_reposer_charge_mandat_app('62766', 10000);
select public.app_reposer_charge_mandat_app('62934', 10000);
select public.app_reposer_charge_mandat_app('63299', 10000);
select public.app_reposer_charge_mandat_app('63490', 10000);

-- ─── ⑤ LES CONTROLES ─────────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_mandat_champ_app k on k.hektor_annonce_id = j.mandat_annonce and k.numero_mandat = j.mandat_numero
     and k.champ = 'charge_commission' and k.valeur_app = j.valeur and k.origine = 'classeur'
     and k.ecrit_par = 'classeur:' || j.ligne_origine
   where j.lot = 'charge_2026-11-24' and j.geste = 'POSER (case vide)';
  if n <> 18 then raise exception '⛔ controle : % charge(s) au carnet sur 18', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'charge_2026-11-24';
  if n <> 20 then raise exception '⛔ controle : % ligne(s) au journal sur 20 (dont les ecartees, NOMMEES)', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_mandat_register_current r on r.hektor_annonce_id::text = j.mandat_annonce and r.numero_mandat::text = j.mandat_numero
     and r.mandat_charge_honoraires_app = j.valeur
   where j.lot = 'charge_2026-11-24' and j.geste = 'POSER (case vide)';
  if n <> 18 then raise exception '⛔ controle : % reflet(s) pose(s) sur 18', n; end if;
  -- rien d'autre n'a bouge dans le registre de ces annonces
  select count(*) into n from public.app_mandat_register_current r
    join public.app_mandat_register_current_avant_charge_20261124 s
      on s.hektor_annonce_id = r.hektor_annonce_id and s.numero_mandat = r.numero_mandat
   where r.mandat_charge_honoraires_app is distinct from s.mandat_charge_honoraires_app
     and (r.hektor_annonce_id::text, r.numero_mandat::text) not in (select mandat_annonce, mandat_numero
                                                                   from public.app_classeur_realignement_journal where lot = 'charge_2026-11-24' and geste = 'POSER (case vide)');
  if n <> 0 then raise exception '⛔ controle : % autre(s) reflet(s) ont bouge', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'charge_2026-11-24' and ligne_origine is not null and ligne_origine_num is not null;
  if n <> 20 then raise exception '⛔ controle : % ligne(s) d''origine au journal sur 18', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', m.annonce, m.numero, coalesce(k.valeur_app, '-'), coalesce(k.origine, '-'), coalesce(k.ecrit_par, '-'), coalesce(r.mandat_charge_honoraires_app, '-')), ';' order by m.annonce, m.numero), '')) from (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481'), ('46338', '17322'), ('47174', '17639'), ('63490', '18999'), ('59164', '18127'), ('59339', '18143'), ('54734', '18053'), ('17597', '18973'), ('62336', '18648'), ('62766', '18773'), ('11695', '17296'), ('59637', '18286'), ('62934', '18950'), ('63299', '18942'), ('39684', '17987'), ('61893', '18996')) m(annonce, numero) left join public.app_mandat_champ_app k on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission' left join public.app_mandat_register_current r on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero);
  if e <> 'b58ba6cb9a5cd6c6e20dc01f99bcc266' then raise exception '⛔ controle : empreinte apres % au lieu de b58ba6cb9a5cd6c6e20dc01f99bcc266', e; end if;
  raise notice '✅ 18 charges au carnet, 18 reflets, 0 autre reflet, ligne d''origine au journal ; empreinte apres %', e;
end $$;

commit;
