-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (2e patch) -- RETOUR ARRIERE
-- ⭐⭐ ET C'EST ICI QUE LE PREALABLE PAIE : il suffit de viser `classeur:F` et
--   `classeur:G`. Sans ces deux origines distinctes, il aurait fallu viser
--   `classeur` -- et EMPORTER LES 195 NOTES DE C5 avec.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $$
declare n integer;
begin
  select count(*) into n from public.app_affaire_note
   where origine in ('classeur:F','classeur:G','classeur:F+G');
  if n <> 4325 then
    raise exception '⛔ ARRET : % notes de C4 au lieu de 4325.', n;
  end if;
  raise notice '✅ 4325 notes de C4 retrouvees.';
end $$;

delete from public.app_affaire_note
 where origine in ('classeur:F', 'classeur:G', 'classeur:F+G')
   and ecrit_par = 'classeur:C4:2026-11-17';

do $$
declare reste integer; c5 integer;
begin
  select count(*) into reste from public.app_affaire_note
   where origine in ('classeur:F','classeur:G','classeur:F+G');
  if reste <> 0 then
    raise exception '⛔ il reste % note(s) de C4.', reste;
  end if;
  select count(*) into c5 from public.app_affaire_note where origine = 'classeur';
  if c5 <> 195 then
    raise exception '⛔⛔ % notes de C5 au lieu de 195 : LE RETOUR ARRIERE A '
      'DEBORDE. GRAVE.', c5;
  end if;
  raise notice '✅ 4325 notes retirees . LES 195 DE C5 SONT INTACTES.';
end $$;

commit;
