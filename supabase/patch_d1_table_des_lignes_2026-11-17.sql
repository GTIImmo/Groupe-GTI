-- ═══════════════════════════════════════════════════════════════════════════
-- D1 -- REMETTRE `app_classeur_ligne_id` A JOUR : 21 LIGNES RECENTES
-- Genere le 2026-11-17 par phase2/checks/d1_remettre_la_table_des_lignes_2026-11-17.py
--
-- LE BESOIN : la table portait 4773 lignes quand le Sheet en a 4794.
--   Les manquantes sont LES PLUS RECENTES. Or c'est elle qui donne LE NUMERO DE
--   LIGNE : sans elle, un re-gel ne sait pas quoi accrocher, et la sentinelle B2
--   (« lignes du classeur sans lien ») SOUS-COMPTE, puisqu'elle la lit.
--
-- ⛔⛔ LE CONTROLE IMPERATIF A ETE PASSE AVANT DE GENERER CE PATCH : sur les
--   4773 id_unique connus des deux cotes, **AUCUN n'a change de numero**.
--   C'etait la condition absolue : `ligne_classeur` fait partie de la CLEF
--   PRIMAIRE des 12 790 liens. Si une ligne avait glisse, la table et les liens
--   auraient cesse de parler de la meme ligne EN SILENCE -- et ce patch serait
--   une migration, pas un ajout. Le generateur refuse de l'ecrire dans ce cas.
--
-- ⭐ LE GESTE EST UN AJOUT PUR : `where not exists`. Aucune ligne existante n'est
--   modifiee, aucun numero n'est deplace, aucun lien n'est touche.
--
-- ⚠ ET ON NE RETIRE RIEN : la table porte peut-etre des id_unique que le Sheet
--   n'a plus ; des liens les pointent sans doute. Les supprimer casserait le pont.
--
-- RETOUR ARRIERE : patch_d1_table_des_lignes_2026-11-17_INVERSE.sql
-- ═══════════════════════════════════════════════════════════════════════════
begin;

-- ① LA SAUVEGARDE DATEE
drop table if exists app_classeur_ligne_id_avant_20261117;
create table app_classeur_ligne_id_avant_20261117 as
  select * from app_classeur_ligne_id;

do $$
declare n integer;
begin
  select count(*) into n from app_classeur_ligne_id_avant_20261117;
  if n <> 4773 then
    raise exception '⛔ LA SAUVEGARDE PORTE % lignes au lieu de 4773', n;
  end if;
end $$;

-- ② L'AJOUT
insert into app_classeur_ligne_id (ligne_classeur, id_unique)
values
    (4780, 'cd29653f'),
    (4781, '1a474908'),
    (4782, '63790b81'),
    (4783, 'b251d01e'),
    (4784, 'dad56e75'),
    (4785, 'f9a2b718'),
    (4786, '918d3b44'),
    (4787, '800693bd'),
    (4788, 'dedeafeb'),
    (4789, 'c6233284'),
    (4790, 'd7cbb8fa'),
    (4791, 'b7439331'),
    (4792, 'c67ccc6a'),
    (4793, 'fbf9799a'),
    (4794, 'c6e5299a'),
    (4795, '7543e4fb'),
    (4796, 'b884cbd4'),
    (4797, '5e4c8881'),
    (4798, 'b43e76f5'),
    (4799, '1eec6575'),
    (4800, '70740f2f')
on conflict do nothing;

-- ③ LES CONTROLES, DANS LA MEME TRANSACTION
do $$
declare n integer;
begin
  select count(*) into n from app_classeur_ligne_id;
  if n <> 4794 then
    raise exception '⛔ LA TABLE PORTE % lignes au lieu de 4794', n;
  end if;

  -- ⭐⭐ AUCUNE LIGNE D'ORIGINE N'A BOUGE -- compare a la sauvegarde, pas compte
  select count(*) into n
    from app_classeur_ligne_id_avant_20261117 s
    left join app_classeur_ligne_id g on g.id_unique = s.id_unique
   where g.id_unique is null or g.ligne_classeur is distinct from s.ligne_classeur;
  if n <> 0 then
    raise exception '⛔ % lignes d origine ont disparu ou change de numero', n;
  end if;

  -- ⭐ LES 12 790 LIENS SONT INTACTS : ce patch ne les touche pas
  select count(*) into n from app_classeur_lien;
  if n <> 12790 then raise exception '⛔ LE GEL PORTE % liens au lieu de 12 790', n; end if;

  -- ⭐ et plus aucun lien ne pointe un id_unique absent de la table
  select count(*) into n from (select distinct k.id_unique from app_classeur_lien k
    where not exists (select 1 from app_classeur_ligne_id g
                       where g.id_unique = k.id_unique)) s;
  if n <> 0 then
    raise notice '⚠ il reste % id_unique pointes par un lien et absents de la table', n;
  else
    raise notice '✅ plus aucun lien orphelin de la table des lignes';
  end if;

  raise notice '✅ 21 lignes ajoutees, la table passe a 4794';
end $$;

commit;
