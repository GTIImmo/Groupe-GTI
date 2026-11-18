-- INVERSE -- retirer le mecanisme d'exclusion des lignes du classeur.
-- ⛔ Un retour arriere ne juge que SA part : il refuse de tourner si quelqu'un a
--   ajoute d'autres exclusions depuis, parce qu'il les perdrait en silence.
-- ⚠ A JOUER AVEC le debranchement cote script : une porte qui lit une table
--   disparue tombe. Voir poser_offres_annulees_classeur_2026-11-16.py.
begin;

do $$
declare n int;
begin
  if to_regclass('public.app_classeur_ligne_exclue') is null then
    raise exception '⛔ la table n''existe pas -- le patch n''a pas ete joue';
  end if;
  select count(*) into n from public.app_classeur_ligne_exclue;
  if n <> 1 then
    raise exception '⛔ % exclusions au lieu de la seule posee le 18/11 -- '
                    'd''autres decisions seraient perdues. Les lire d''abord.', n;
  end if;
end $$;

drop table public.app_classeur_ligne_exclue;

do $$
begin
  if to_regclass('public.app_classeur_ligne_exclue') is not null then
    raise exception '⛔ la table est toujours la';
  end if;
  raise notice '✅ mecanisme retire -- penser a debrancher le script';
end $$;

commit;
