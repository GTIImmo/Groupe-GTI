-- INVERSE de patch_3bis_lot_c_repartitions_2026-11-27 : retire SES parts (ecrit_par = classeur:3bisC:2026-11-27), rien d'autre (lecon 31).

begin;
delete from public.app_affaire_repartition where ecrit_par = 'classeur:3bisC:2026-11-27';
do $$ begin if exists (select 1 from public.app_affaire_repartition where ecrit_par = 'classeur:3bisC:2026-11-27') then
  raise exception '⛔ inverse : une part du lot reste'; end if;
  raise notice '✅ inverse : le lot 3 bis C est retire';
end $$;
commit;
