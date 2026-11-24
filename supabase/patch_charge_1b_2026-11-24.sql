-- patch_charge_1b_2026-11-24 -- genere par phase2/checks/cases_vides_generer_patchs_2026-11-24.py (son 5e mot du 24/11 : « rien ne s'ecrit sans mon accord sur le patch »)
-- Retour arriere : patch_charge_1b_2026-11-24_INVERSE.sql . Controle : patch_charge_1b_2026-11-24_REPETITION.sql

begin;

-- ─── ① LES GARDES : chaque mandat est VIDE au carnet et au reflet, et il existe au registre ────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_mandat_register_current_avant_charge_1b_20261124') is not null then
    raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas';
  end if;
  if to_regclass('public.app_classeur_realignement_journal') is null then
    raise exception '⛔ garde : le journal du realignement n''existe pas (patch des 42 d''abord)';
  end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'charge_1b_2026-11-24';
  if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_mandat_champ_app k join (values ('63490', '18999'), ('59164', '18127'), ('59339', '18143'), ('54734', '18053'), ('17597', '18973'), ('62336', '18648'), ('62766', '18773'), ('11695', '17296'), ('59637', '18286'), ('62934', '18950'), ('63299', '18942'), ('39684', '17987'), ('61893', '18996')) m(annonce, numero)
      on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission';
  if n <> 0 then raise exception '⛔ garde : % mandat(s) portent DEJA une charge au carnet -- on n''ecrase jamais', n; end if;
  select count(*) into n from public.app_mandat_register_current r join (values ('63490', '18999'), ('59164', '18127'), ('59339', '18143'), ('54734', '18053'), ('17597', '18973'), ('62336', '18648'), ('62766', '18773'), ('11695', '17296'), ('59637', '18286'), ('62934', '18950'), ('63299', '18942'), ('39684', '17987'), ('61893', '18996')) m(annonce, numero)
      on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero
   where nullif(btrim(coalesce(r.mandat_charge_honoraires_app, '')), '') is null;
  if n <> 13 then raise exception '⛔ garde : % mandat(s) au registre avec un reflet vide sur 13', n; end if;
  select count(*) into n from public.app_mandat_register_current r where r.hektor_annonce_id::text in ('11695', '17597', '39684', '54734', '59164', '59339', '59637', '61893', '62336', '62766', '62934', '63299', '63490');
  if n <> 13 then raise exception '⛔ garde : les annonces portent % mandat(s) au registre au lieu de 13', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', m.annonce, m.numero, coalesce(k.valeur_app, '-'), coalesce(k.origine, '-'), coalesce(k.ecrit_par, '-'), coalesce(r.mandat_charge_honoraires_app, '-')), ';' order by m.annonce, m.numero), '')) from (values ('63490', '18999'), ('59164', '18127'), ('59339', '18143'), ('54734', '18053'), ('17597', '18973'), ('62336', '18648'), ('62766', '18773'), ('11695', '17296'), ('59637', '18286'), ('62934', '18950'), ('63299', '18942'), ('39684', '17987'), ('61893', '18996')) m(annonce, numero) left join public.app_mandat_champ_app k on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission' left join public.app_mandat_register_current r on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero);
  if e <> 'e2233fb6a82167215aad364f12843c82' then raise exception '⛔ garde : empreinte % au lieu de e2233fb6a82167215aad364f12843c82', e; end if;
  raise notice '✅ gardes : 13 mandats vides au carnet et au reflet ; empreinte %', e;
end $$;

-- ─── ② LA SAUVEGARDE DATEE : les lignes du registre des mandats de ces annonces (le reflet) ──────────────────────────────
create table public.app_mandat_register_current_avant_charge_1b_20261124 as
  select * from public.app_mandat_register_current where hektor_annonce_id::text in ('11695', '17597', '39684', '54734', '59164', '59339', '59637', '61893', '62336', '62766', '62934', '63299', '63490');
revoke all on public.app_mandat_register_current_avant_charge_1b_20261124 from public, anon, authenticated;

-- ─── ③ LE JOURNAL : chaque ecriture avec SA LIGNE D'ORIGINE (id_unique, n° au Sheet) et SA PLACE (le mandat) ──────────
alter table public.app_classeur_realignement_journal add column if not exists mandat_annonce text;
alter table public.app_classeur_realignement_journal add column if not exists mandat_numero text;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, valeur, ligne_origine, ligne_origine_num, lot_origine, pourquoi, ecrit_par, mandat_annonce, mandat_numero)
select 'charge_1b_2026-11-24', v.n, 'charge_commission', 'app_mandat_champ_app.valeur_app (charge_commission)', 'POSER (case vide)',
       v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, d.app_dossier_uuid, null, v.valeur, v.ligne, v.num,
       'Sheet (colonne Charge Commission) -- son 5e mot du 24/11', v.pourquoi, 'patch_charge_1b_2026-11-24', v.annonce, v.numero
  from (values
    (1, '1eec6575', 4799, 30825, '63490', '18999', 'vendeur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Compromis en attente ; Commission TTC 3500 EUR'),
    (2, '2b924f5f', 4498, 28633, '59164', '18127', 'vendeur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Annulee ; Commission TTC 3000 EUR'),
    (3, '4cbc128d', 4492, 28687, '59339', '18143', 'vendeur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Annulee ; Commission TTC 6790 EUR'),
    (4, '54376c72', 4801, 30830, '54734', '18053', 'acquereur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Offre d''achat ; Commission TTC 1800 EUR'),
    (5, '55b49232', 4804, 30837, '17597', '18973', 'vendeur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Offre d''achat ; Commission TTC 5699 EUR'),
    (6, '5e4c8881', 4797, 30820, '62336', '18648', 'vendeur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Compromis en attente ; Commission TTC 6900 EUR'),
    (7, '70740f2f', 4800, 30824, '62766', '18773', 'vendeur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Offre d''achat ; Commission TTC 4800 EUR'),
    (8, '729ba8dc', 4306, 6103, '11695', '17296', 'vendeur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Annulee ; Commission TTC 6130 EUR'),
    (9, 'b43e76f5', 4798, 30826, '59637', '18286', 'acquereur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Offre d''achat ; Commission TTC 10000 EUR'),
    (10, 'b72db9d5', 4803, 30836, '62934', '18950', 'vendeur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Offre d''achat ; Commission TTC 4000 EUR'),
    (11, 'b7439331', 4791, 30809, '63299', '18942', 'vendeur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Offre d''achat ; Commission TTC 1000 EUR'),
    (12, 'f90b0418', 4455, 19049, '39684', '17987', 'acquereur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Annulee ; Commission TTC 7000 EUR'),
    (13, 'ffcf30e6', 4802, 30829, '61893', '18996', 'vendeur', '① les 13 autres (son 5e mot du 24/11) ; etat au Sheet : Offre d''achat ; Commission TTC 8500 EUR')
  ) v(n, ligne, num, piece, annonce, numero, valeur, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = v.piece;

-- ─── ④ LE GESTE : le carnet (la valeur LUE AU JOURNAL), puis le reflet, annonce par annonce (jamais tout le registre) ────
insert into public.app_mandat_champ_app (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, ecrit_par, ecrit_le)
select j.mandat_annonce, j.mandat_numero, 'charge_commission', j.valeur, 'classeur', 'classeur:' || j.ligne_origine, now()
  from public.app_classeur_realignement_journal j where j.lot = 'charge_1b_2026-11-24'
on conflict (hektor_annonce_id, numero_mandat, champ) do nothing;
select public.app_reposer_charge_mandat_app('11695', 10000);
select public.app_reposer_charge_mandat_app('17597', 10000);
select public.app_reposer_charge_mandat_app('39684', 10000);
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
   where j.lot = 'charge_1b_2026-11-24';
  if n <> 13 then raise exception '⛔ controle : % charge(s) au carnet sur 13', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_mandat_register_current r on r.hektor_annonce_id::text = j.mandat_annonce and r.numero_mandat::text = j.mandat_numero
     and r.mandat_charge_honoraires_app = j.valeur
   where j.lot = 'charge_1b_2026-11-24';
  if n <> 13 then raise exception '⛔ controle : % reflet(s) pose(s) sur 13', n; end if;
  -- rien d'autre n'a bouge dans le registre de ces annonces
  select count(*) into n from public.app_mandat_register_current r
    join public.app_mandat_register_current_avant_charge_1b_20261124 s
      on s.hektor_annonce_id = r.hektor_annonce_id and s.numero_mandat = r.numero_mandat
   where r.mandat_charge_honoraires_app is distinct from s.mandat_charge_honoraires_app
     and (r.hektor_annonce_id::text, r.numero_mandat::text) not in (select mandat_annonce, mandat_numero
                                                                   from public.app_classeur_realignement_journal where lot = 'charge_1b_2026-11-24');
  if n <> 0 then raise exception '⛔ controle : % autre(s) reflet(s) ont bouge', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'charge_1b_2026-11-24' and ligne_origine is not null and ligne_origine_num is not null;
  if n <> 13 then raise exception '⛔ controle : % ligne(s) d''origine au journal sur 13', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', m.annonce, m.numero, coalesce(k.valeur_app, '-'), coalesce(k.origine, '-'), coalesce(k.ecrit_par, '-'), coalesce(r.mandat_charge_honoraires_app, '-')), ';' order by m.annonce, m.numero), '')) from (values ('63490', '18999'), ('59164', '18127'), ('59339', '18143'), ('54734', '18053'), ('17597', '18973'), ('62336', '18648'), ('62766', '18773'), ('11695', '17296'), ('59637', '18286'), ('62934', '18950'), ('63299', '18942'), ('39684', '17987'), ('61893', '18996')) m(annonce, numero) left join public.app_mandat_champ_app k on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission' left join public.app_mandat_register_current r on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero);
  if e <> '44fc64cd49b97d0696993552fef532ee' then raise exception '⛔ controle : empreinte apres % au lieu de 44fc64cd49b97d0696993552fef532ee', e; end if;
  raise notice '✅ 13 charges au carnet, 13 reflets, 0 autre reflet, ligne d''origine au journal ; empreinte apres %', e;
end $$;

commit;
