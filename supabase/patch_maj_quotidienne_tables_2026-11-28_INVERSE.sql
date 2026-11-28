-- INVERSE de patch_maj_quotidienne_tables_2026-11-28 : retire les deux tables neuves, SEULEMENT si elles sont vides
-- (une table qui porte deja le routeur ou un journal ne se retire pas : on s'arrete et on regarde).

begin;
do $$ begin
  if (select count(*) from public.app_champ_destination) <> 0 or (select count(*) from public.app_classeur_difference) <> 0 then
    raise exception '⛔ inverse : une des deux tables n''est plus vide -- rien n''est retire'; end if;
end $$;
drop table public.app_champ_destination;
drop table public.app_classeur_difference;
commit;
