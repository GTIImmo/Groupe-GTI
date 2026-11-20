-- INVERSE de patch_sheet_ecrit_memoire_colonne_a_2026-11-20.sql -- 20/11/2026
-- Retire la table app_sheet_ecrit, ET SEULEMENT SI ELLE EST VIDE.
--
-- ⛔ Lecon 31 : un retour arriere ne juge que SA part. Le patch a pose une table VIDE ;
--   l'inverse ne retire donc qu'une table vide. Si elle porte une seule ligne, c'est que
--   l'outil d'ecriture a ecrit dans le Sheet : la retirer ferait perdre le moyen de
--   reconnaitre NOS cases parmi celles des humains. Il faut alors D'ABORD defaire la
--   vague par l'outil (ecrire_colonne_a_du_sheet_2026-11-20.py defaire ...), puis
--   decider a part de ce qu'on fait de la memoire.

do $garde$
declare n bigint; existe integer;
begin
  select count(*) into existe from information_schema.tables
   where table_schema = 'public' and table_name = 'app_sheet_ecrit';
  if existe = 0 then
    raise notice 'app_sheet_ecrit n''existe pas : rien a retirer.';
    return;
  end if;
  select count(*) into existe from information_schema.columns
   where table_schema = 'public' and table_name = 'app_sheet_ecrit' and column_name = 'id_unique';
  if existe <> 1 then
    raise exception 'ARRET : app_sheet_ecrit n''a pas la forme du 20/11 (pas de colonne id_unique) -- '
                    'ce n''est pas la table de ce patch, on n''y touche pas.';
  end if;
  execute 'select count(*) from public.app_sheet_ecrit' into n;
  if n > 0 then
    raise exception 'ARRET : app_sheet_ecrit porte % ligne(s) -- la memoire de cases ECRITES dans le Sheet. '
                    'Defaire d''abord la vague par l''outil ; ne pas retirer la table.', n;
  end if;
end $garde$;

-- (la politique de lecture part avec la table)
drop table if exists public.app_sheet_ecrit;

do $garde$
declare existe integer;
begin
  select count(*) into existe from information_schema.tables
   where table_schema = 'public' and table_name = 'app_sheet_ecrit';
  if existe <> 0 then
    raise exception 'La table est toujours la';
  end if;
  raise notice 'OK : app_sheet_ecrit retiree (elle etait vide).';
end $garde$;
