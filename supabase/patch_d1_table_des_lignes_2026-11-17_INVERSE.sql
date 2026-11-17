-- ═══════════════════════════════════════════════════════════════════════════
-- LE RETOUR ARRIERE DE L'AJOUT DES 21 LIGNES -- 2026-11-17
--
-- ⭐ Il retire EXACTEMENT les 21 id_unique ajoutes, nommement. Il ne touche a
--   aucune des 4773 lignes d'origine, et a aucun lien.
-- ⛔ ET IL JUGE SA PROPRE PART : la table doit revenir a 4773, et les
--   lignes d'origine etre intactes face a la sauvegarde.
-- ═══════════════════════════════════════════════════════════════════════════
begin;

delete from app_classeur_ligne_id
 where id_unique in ('cd29653f', '1a474908', '63790b81', 'b251d01e', 'dad56e75', 'f9a2b718', '918d3b44', '800693bd', 'dedeafeb', 'c6233284', 'd7cbb8fa', 'b7439331', 'c67ccc6a', 'fbf9799a', 'c6e5299a', '7543e4fb', 'b884cbd4', '5e4c8881', 'b43e76f5', '1eec6575', '70740f2f');

do $$
declare n integer;
begin
  select count(*) into n from app_classeur_ligne_id;
  if n <> 4773 then
    raise exception '⛔ LA TABLE PORTE % lignes au lieu de 4773', n;
  end if;
  select count(*) into n
    from app_classeur_ligne_id_avant_20261117 s
    left join app_classeur_ligne_id g on g.id_unique = s.id_unique
   where g.id_unique is null or g.ligne_classeur is distinct from s.ligne_classeur;
  if n <> 0 then raise exception '⛔ % lignes d origine abimees', n; end if;
  select count(*) into n from app_classeur_lien;
  if n <> 12790 then raise exception '⛔ LE GEL A BOUGE : % liens', n; end if;
  raise notice '✅ RETOUR ARRIERE COMPLET';
end $$;

commit;
