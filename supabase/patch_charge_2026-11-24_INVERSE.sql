-- patch_charge_2026-11-24 -- genere par phase2/checks/cases_vides_generer_patchs_2026-11-24.py (son 5e mot du 24/11 : « rien ne s'ecrit sans mon accord sur le patch »)
-- Retour arriere : patch_charge_2026-11-24_INVERSE.sql . Controle : patch_charge_2026-11-24_REPETITION.sql
-- L'INVERSE : il retire ce que le lot a pose, et EXIGE le retour a l'empreinte d'avant. Le journal et la sauvegarde restent (la trace).

begin;

-- ─── LE RETOUR : retirer du carnet CE QUE CE LOT A POSE (et seulement cela), reposer le reflet ; le journal et la sauvegarde restent
do $$
declare n int;
begin
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_mandat_champ_app k on k.hektor_annonce_id = j.mandat_annonce and k.numero_mandat = j.mandat_numero
     and k.champ = 'charge_commission' and k.valeur_app = j.valeur and k.origine = 'classeur' and k.ecrit_par = 'classeur:' || j.ligne_origine
   where j.lot = 'charge_2026-11-24' and j.geste = 'POSER (case vide)';
  if n <> 18 then raise exception '⛔ garde du retour : % charge(s) du lot retrouvee(s) sur 18 (une saisie est passee ?)', n; end if;
end $$;
delete from public.app_mandat_champ_app k using public.app_classeur_realignement_journal j
 where j.lot = 'charge_2026-11-24' and j.geste = 'POSER (case vide)' and k.hektor_annonce_id = j.mandat_annonce and k.numero_mandat = j.mandat_numero
   and k.champ = 'charge_commission' and k.valeur_app = j.valeur and k.origine = 'classeur' and k.ecrit_par = 'classeur:' || j.ligne_origine;
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
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_mandat_register_current r
    join public.app_mandat_register_current_avant_charge_20261124 s on s.hektor_annonce_id = r.hektor_annonce_id and s.numero_mandat = r.numero_mandat
   where r.mandat_charge_honoraires_app is distinct from s.mandat_charge_honoraires_app;
  if n <> 0 then raise exception '⛔ controle du retour : % reflet(s) differents de la sauvegarde', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', m.annonce, m.numero, coalesce(k.valeur_app, '-'), coalesce(k.origine, '-'), coalesce(k.ecrit_par, '-'), coalesce(r.mandat_charge_honoraires_app, '-')), ';' order by m.annonce, m.numero), '')) from (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481'), ('46338', '17322'), ('47174', '17639'), ('63490', '18999'), ('59164', '18127'), ('59339', '18143'), ('54734', '18053'), ('17597', '18973'), ('62336', '18648'), ('62766', '18773'), ('11695', '17296'), ('59637', '18286'), ('62934', '18950'), ('63299', '18942'), ('39684', '17987'), ('61893', '18996')) m(annonce, numero) left join public.app_mandat_champ_app k on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission' left join public.app_mandat_register_current r on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero);
  if e <> '950158733b79f7ee5083153d754453ab' then raise exception '⛔ controle du retour : empreinte % au lieu de 950158733b79f7ee5083153d754453ab (celle d''AVANT)', e; end if;
end $$;

commit;
