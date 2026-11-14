-- =====================================================================
-- LES DONNEES DE L ETAPE (1) : LA CHARGE, DEPUIS LE CLASSEUR -- passe du 14/11/2026
-- =====================================================================
-- Genere par phase2/checks/poser_charge_classeur_2026-11-04.py
-- 16 lignes : 15 vendeur, 1 acquereur
-- origine = 'classeur' -- SA DECISION DU 04/11 : elle FAIT FOI.
-- ⛔ A COLLER APRES patch_charge_classeur_2026-11-04.sql, qui elargit
--    app_reposer_charge_mandat_app aux deux origines. Sans lui, la
--    premiere repose EFFACERAIT ces 16 lignes.
-- ON CONFLICT DO NOTHING : on n ecrase JAMAIS une saisie humaine.
-- =====================================================================

insert into public.app_mandat_champ_app
  (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, ecrit_par, ecrit_le)
values
  ('47132', '18874', 'charge_commission', 'vendeur', 'classeur', 'classeur:c67ccc6a', now()),
  ('49618', '18763', 'charge_commission', 'vendeur', 'classeur', 'classeur:63790b81', now()),
  ('49852', '17823', 'charge_commission', 'acquereur', 'classeur', 'classeur:c67855b1', now()),
  ('58958', '18206', 'charge_commission', 'vendeur', 'classeur', 'classeur:c6e5299a', now()),
  ('59390', '18141', 'charge_commission', 'vendeur', 'classeur', 'classeur:cd29653f', now()),
  ('61615', '18514', 'charge_commission', 'vendeur', 'classeur', 'classeur:f0ec39fc', now()),
  ('62091', '18573', 'charge_commission', 'vendeur', 'classeur', 'classeur:b251d01e', now()),
  ('62349', '18892', 'charge_commission', 'vendeur', 'classeur', 'classeur:fbf9799a', now()),
  ('62840', '18873', 'charge_commission', 'vendeur', 'classeur', 'classeur:dedeafeb', now()),
  ('62905', '18824', 'charge_commission', 'vendeur', 'classeur', 'classeur:5a956cad', now()),
  ('63108', '18885', 'charge_commission', 'vendeur', 'classeur', 'classeur:918d3b44', now()),
  ('63129', '18977', 'charge_commission', 'vendeur', 'classeur', 'classeur:dad56e75', now()),
  ('63140', '18899', 'charge_commission', 'vendeur', 'classeur', 'classeur:7543e4fb', now()),
  ('63193', '18946', 'charge_commission', 'vendeur', 'classeur', 'classeur:f9a2b718', now()),
  ('63222', '18920', 'charge_commission', 'vendeur', 'classeur', 'classeur:800693bd', now()),
  ('63231', '18922', 'charge_commission', 'vendeur', 'classeur', 'classeur:d7cbb8fa', now())
on conflict (hektor_annonce_id, numero_mandat, champ) do nothing;

-- Puis on repose le reflet sur la colonne du registre.
select public.app_reposer_charge_mandat_app(null, 10000) as repose;
