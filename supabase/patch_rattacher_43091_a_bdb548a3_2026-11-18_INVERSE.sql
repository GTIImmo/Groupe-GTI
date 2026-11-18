-- INVERSE -- remettre l'offre 32791 et le compromis 17016 sur la ligne 227 (GIBERT).
-- ⛔ Un retour arriere ne juge que SA part : il verifie que le deplacement a bien eu
--   lieu, que la sauvegarde est complete, et il ne touche a rien d'autre.
begin;

do $$
declare n227 int; n4505 int; g int;
begin
  select count(*) into n227 from app_classeur_lien where ligne_classeur=227;
  if n227 <> 0 then
    raise exception '⛔ la ligne 227 porte deja % lien(s) -- le patch n''a pas ete joue', n227; end if;
  select count(*) into n4505 from app_classeur_lien where ligne_classeur=4505;
  if n4505 <> 3 then raise exception '⛔ la ligne 4505 porte % liens au lieu de 3', n4505; end if;
  select count(*) into g from app_classeur_lien_avant_rattachement_43091_20261118;
  if g <> 2 then raise exception '⛔ sauvegarde : % lignes au lieu de 2', g; end if;
end $$;

delete from app_classeur_lien where ligne_classeur=4505 and app_affaire_id in (21551,21552);
insert into app_classeur_lien
  select * from app_classeur_lien_avant_rattachement_43091_20261118;

do $$
declare n227 int; n4505 int; total int;
begin
  select count(*) into n227 from app_classeur_lien where ligne_classeur=227;
  select count(*) into n4505 from app_classeur_lien where ligne_classeur=4505;
  select count(*) into total from app_classeur_lien;
  if n227 <> 2 then raise exception '⛔ ligne 227 : % liens au lieu de 2', n227; end if;
  if n4505 <> 1 then raise exception '⛔ ligne 4505 : % liens au lieu de 1', n4505; end if;
  if total <> 12787 then raise exception '⛔ % liens au total au lieu de 12 787', total; end if;
  raise notice '✅ retour arriere fait : 227 reprend ses 2 liens, 4505 retrouve sa vente seule';
end $$;

commit;
