-- INVERSE de patch_types_par_tranche_2026-11-04.sql : retire la fonction par tranches.
-- ⚠ AVANT : remettre phase2/sync/recalculer_types_contacts.py sur l'appel unique (sinon la nuit appellerait
--   une fonction absente ; l'etape est facultative, le run continue, le battement le dit).
-- Ne juge que SA part : app_recalculer_tous_les_types() doit rester intacte.
drop function if exists public.app_recalculer_types_tranche(text, text);
do $controle$
begin
  if exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
              where n.nspname = 'public' and p.proname = 'app_recalculer_types_tranche') then
    raise exception 'CONTROLE : app_recalculer_types_tranche existe encore';
  end if;
  if (select md5(replace(pg_get_functiondef('public.app_recalculer_tous_les_types()'::regprocedure), chr(13), '')))
     <> '22f51f243410779ff74ebcf38fea88d9' then
    raise exception 'CONTROLE : app_recalculer_tous_les_types a change';
  end if;
  raise notice 'INVERSE OK : la fonction par tranches est retiree, celle d''origine est intacte';
end
$controle$;
