-- ═══════════════════════════════════════════════════════════════════════════════
-- LA CORRECTION DU GEL, AFFINEE PAR LE SECOND AUDIT INDEPENDANT           19/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- ⛔ DORMANT : il ne se joue qu'avec l'accord explicite de Frederic.
-- ⛔⛔ IL PORTE SON `commit;` : joue « pour voir », IL SE COMMITE. Ne jamais le jouer a blanc.
-- SOURCE : le patch de l'autre session (supabase/patch_correction_gel_audit_independant_2026-11-18.sql)
--   et notice/AUDIT_INDEPENDANT_V2_2026-11-19.md (§ 8). Genere par
--   phase2/checks/audit_v2_generer_patch_affine_2026-11-19.py -- ne pas le retoucher a la main.
-- CE QU'IL FAIT : 45 liens RETIRES . 78 liens AJOUTES . le gel passe de 12787 a 12820.
--   Chaque operation est SOUTENUE par les deux audits independants (18/11 et 19/11).
-- CE QUI A CHANGE PAR RAPPORT AU PATCH DU 18/11 :
--   ① `etage` = un libelle court et constant ; `preuves` = le vrai compte de familles (2 a 8),
--     jamais 0 (0 veut deja dire « cree par C5, aucune preuve »).
--   ② les 18 lignes a question ouverte SORTENT (sa decision), avec QJQ9M4OF (indivisible de
--     D9MMB7OU) et, en cascade, 4 operations dont la cible resterait tenue (6FQO29C8 x2,
--     H6CTRVR6, 9WQ204HP) : 37 operations sorties en tout, listees dans
--     notice/AUDIT_INDEPENDANT_V2_OPERATIONS_AFFINEES_2026-11-19.csv.
--   ③ la garde lit l'EMPREINTE du gel (pas seulement son compte), et un controle en tete
--     verifie que chaque cible existe, porte le bon genre et sera libre.
-- CE QU'IL NE FAIT PAS : il ne touche NI les transactions (les copies de C5 se retirent APRES,
--   des DEUX cotes), NI les valeurs posees par C2/C3/C4 sur une mauvaise transaction (geste
--   suivant, a ENCHAINER : la repetition les compte), NI Hektor, NI les 8 lignes incertaines.
-- RETOUR ARRIERE : patch_correction_gel_audit_v2_2026-11-19_INVERSE.sql
-- CONTROLE       : patch_correction_gel_audit_v2_2026-11-19_REPETITION.sql (lecture seule)
-- ═══════════════════════════════════════════════════════════════════════════════
begin;

-- ── ① LA GARDE : le gel est EXACTEMENT celui que les deux audits ont lu ──────────
do $$
declare n int; emp text; manque int; cible_ko int; deja int;
begin
  select count(*), md5(string_agg(id_unique||':'||app_affaire_id||':'||role, ','
                                  order by id_unique collate "C", app_affaire_id))
    into n, emp from app_classeur_lien;
  if n <> 12787 or emp <> '8084e535f51ba904a839bfe0bcc88a55' then
    raise exception '⛔ garde : le gel a bouge (% liens, empreinte %) -- rien n''est ecrit', n, emp;
  end if;
  if to_regclass('public.app_classeur_lien_avant_audit_v2_20261119') is not null then
    raise exception '⛔ garde : la sauvegarde app_classeur_lien_avant_audit_v2_20261119 existe deja -- ce patch a-t-il deja ete joue ?';
  end if;
  -- chaque lien a retirer existe, avec son role
  select count(*) into manque from (values
    ('045ecde7', 28558, 'offre'),
    ('08GV8OMZ', 6341, 'offre'),
    ('1ESJE28Q', 12952, 'compromis'),
    ('1ESJE28Q', 12953, 'offre'),
    ('3S4ZWOFK', 1001580, 'offre'),
    ('3W10AEIK', 4747, 'offre'),
    ('427UDDSF', 3648, 'offre'),
    ('427UDDSF', 3650, 'vente'),
    ('45225170', 30712, 'offre'),
    ('45225170', 1001361, 'offre'),
    ('61OW86CS', 4496, 'compromis'),
    ('739a0db1', 27195, 'compromis'),
    ('739a0db1', 1001520, 'offre'),
    ('774aa002', 11138, 'compromis'),
    ('8Q3LHGZ4', 8321, 'compromis'),
    ('8Q3LHGZ4', 8322, 'offre'),
    ('8RWTD0YX', 4385, 'compromis'),
    ('8RWTD0YX', 1001477, 'offre'),
    ('9UO5NUN6', 11958, 'offre'),
    ('A07EC3DH', 1001563, 'offre'),
    ('CITFQGOB', 16378, 'compromis'),
    ('DAMOO7OU', 23995, 'offre'),
    ('EGR8KXOL', 6554, 'compromis'),
    ('FLPUUSY3', 1876, 'offre'),
    ('KT0601S6', 24291, 'offre'),
    ('NEFHS7JI', 26395, 'compromis'),
    ('NEFHS7JI', 26397, 'offre'),
    ('OXQSBZ9V', 17427, 'compromis'),
    ('OXQSBZ9V', 17430, 'offre'),
    ('Q602VZJX', 6555, 'compromis'),
    ('R0JRVFDC', 1001542, 'compromis'),
    ('RX6J289Y', 16377, 'compromis'),
    ('SBH4QWDW', 23050, 'compromis'),
    ('TR42PT5H', 27196, 'offre'),
    ('TRJ5Y59U', 1001561, 'offre'),
    ('UTLG66LE', 1001482, 'offre'),
    ('VEP1DVQ4', 7780, 'offre'),
    ('VMWFLLW4', 1001540, 'compromis'),
    ('WJ3KA32F', 10730, 'offre'),
    ('Y51UMZHY', 19277, 'offre'),
    ('a8aaeb2b', 998, 'compromis'),
    ('a8aaeb2b', 1000, 'offre'),
    ('f1aedc01', 28967, 'offre'),
    ('fa06e4e5', 28930, 'offre'),
    ('fa06e4e5', 1001553, 'compromis')
  ) v(id_unique, app_affaire_id, role)
  where not exists (select 1 from app_classeur_lien l where l.id_unique = v.id_unique
                       and l.app_affaire_id = v.app_affaire_id and l.role = v.role);
  if manque <> 0 then raise exception '⛔ garde : % lien(s) a retirer introuvable(s)', manque; end if;
  -- chaque cible a ajouter existe au registre et porte le genre de son role
  select count(*) into cible_ko from (values
    ('0GV2LNV2', 4747, 'offre'),
    ('1eec6575', 30825, 'offre'),
    ('2SCBZXMH', 7780, 'offre'),
    ('3S4ZWOFK', 11958, 'offre'),
    ('3W10AEIK', 4748, 'offre'),
    ('427UDDSF', 3649, 'offre'),
    ('515RUEN3', 17428, 'compromis'),
    ('515RUEN3', 17430, 'offre'),
    ('58I5AO17', 7908, 'compromis'),
    ('58I5AO17', 7909, 'offre'),
    ('58I5AO17', 7910, 'vente'),
    ('5H70KQZA', 14224, 'compromis'),
    ('5H70KQZA', 14227, 'offre'),
    ('5H70KQZA', 14228, 'vente'),
    ('5e4c8881', 30820, 'offre'),
    ('70740f2f', 30824, 'offre'),
    ('72GQRHVB', 6391, 'compromis'),
    ('72GQRHVB', 6392, 'offre'),
    ('72GQRHVB', 6393, 'vente'),
    ('739a0db1', 27196, 'offre'),
    ('7IHI7YTJ', 4234, 'compromis'),
    ('7IHI7YTJ', 4235, 'offre'),
    ('7IHI7YTJ', 4236, 'vente'),
    ('7JXLR3JQ', 7115, 'compromis'),
    ('7JXLR3JQ', 7117, 'offre'),
    ('8ATXF2EZ', 19152, 'compromis'),
    ('8ATXF2EZ', 19153, 'offre'),
    ('8ATXF2EZ', 19154, 'vente'),
    ('8RWTD0YX', 4387, 'offre'),
    ('9706WM9J', 23931, 'offre'),
    ('9UO5NUN6', 11959, 'offre'),
    ('A07EC3DH', 1876, 'offre'),
    ('CS38OO8R', 27984, 'compromis'),
    ('CS38OO8R', 27986, 'offre'),
    ('CS38OO8R', 27987, 'vente'),
    ('DAMOO7OU', 23996, 'offre'),
    ('DHXRAK9O', 9370, 'compromis'),
    ('DHXRAK9O', 9371, 'offre'),
    ('DHXRAK9O', 9372, 'vente'),
    ('EGR8KXOL', 6555, 'compromis'),
    ('ESMCO1NC', 6588, 'compromis'),
    ('ESMCO1NC', 6589, 'offre'),
    ('ESMCO1NC', 6590, 'vente'),
    ('FLPUUSY3', 1877, 'offre'),
    ('J6RGX0CQ', 4928, 'compromis'),
    ('J6RGX0CQ', 4929, 'offre'),
    ('J6RGX0CQ', 4930, 'vente'),
    ('JL8GV7RQ', 15169, 'compromis'),
    ('JL8GV7RQ', 15170, 'vente'),
    ('KAYC29B7', 27170, 'offre'),
    ('LUX9SDIL', 14119, 'compromis'),
    ('LUX9SDIL', 14120, 'offre'),
    ('LUX9SDIL', 14121, 'vente'),
    ('MDOXOBIC', 2163, 'compromis'),
    ('MDOXOBIC', 2164, 'offre'),
    ('MDOXOBIC', 2165, 'vente'),
    ('O1099YC0', 6341, 'offre'),
    ('O8BY6AC8', 1000141, 'compromis'),
    ('O8BY6AC8', 1000105, 'offre'),
    ('OXQSBZ9V', 17431, 'offre'),
    ('PPIM4947', 24291, 'offre'),
    ('Q602VZJX', 6554, 'compromis'),
    ('R0JRVFDC', 16377, 'compromis'),
    ('RX6J289Y', 16378, 'compromis'),
    ('S8BKB6FL', 4412, 'compromis'),
    ('S8BKB6FL', 4413, 'offre'),
    ('S8BKB6FL', 4414, 'vente'),
    ('TR42PT5H', 27195, 'compromis'),
    ('TRJ5Y59U', 23995, 'offre'),
    ('UTLG66LE', 5055, 'offre'),
    ('VEP1DVQ4', 7781, 'offre'),
    ('VMWFLLW4', 23050, 'compromis'),
    ('a2abd36c', 30827, 'compromis'),
    ('b43e76f5', 30826, 'offre'),
    ('b884cbd4', 30821, 'offre'),
    ('c6233284', 30801, 'offre'),
    ('f90b0418', 19050, 'offre'),
    ('fa06e4e5', 28931, 'offre')
  ) v(id_unique, app_affaire_id, role)
  left join app_affaire_ledger a on a.app_affaire_id = v.app_affaire_id
  where a.app_affaire_id is null or a.kind <> v.role;
  if cible_ko <> 0 then raise exception '⛔ garde : % cible(s) absente(s) ou d''un autre genre', cible_ko; end if;
end $$;

-- ── ② LA SAUVEGARDE DATEE, FERMEE DES SA NAISSANCE ─────────────────────────────
create table app_classeur_lien_avant_audit_v2_20261119 as select * from app_classeur_lien;
revoke all on app_classeur_lien_avant_audit_v2_20261119 from public, anon, authenticated;
alter table app_classeur_lien_avant_audit_v2_20261119 enable row level security;

-- ── ③ RETIRER (45) ──────────────────────────────────────────────────────────────
delete from app_classeur_lien l
 using (values
    ('045ecde7', 28558, 'offre'),
    ('08GV8OMZ', 6341, 'offre'),
    ('1ESJE28Q', 12952, 'compromis'),
    ('1ESJE28Q', 12953, 'offre'),
    ('3S4ZWOFK', 1001580, 'offre'),
    ('3W10AEIK', 4747, 'offre'),
    ('427UDDSF', 3648, 'offre'),
    ('427UDDSF', 3650, 'vente'),
    ('45225170', 30712, 'offre'),
    ('45225170', 1001361, 'offre'),
    ('61OW86CS', 4496, 'compromis'),
    ('739a0db1', 27195, 'compromis'),
    ('739a0db1', 1001520, 'offre'),
    ('774aa002', 11138, 'compromis'),
    ('8Q3LHGZ4', 8321, 'compromis'),
    ('8Q3LHGZ4', 8322, 'offre'),
    ('8RWTD0YX', 4385, 'compromis'),
    ('8RWTD0YX', 1001477, 'offre'),
    ('9UO5NUN6', 11958, 'offre'),
    ('A07EC3DH', 1001563, 'offre'),
    ('CITFQGOB', 16378, 'compromis'),
    ('DAMOO7OU', 23995, 'offre'),
    ('EGR8KXOL', 6554, 'compromis'),
    ('FLPUUSY3', 1876, 'offre'),
    ('KT0601S6', 24291, 'offre'),
    ('NEFHS7JI', 26395, 'compromis'),
    ('NEFHS7JI', 26397, 'offre'),
    ('OXQSBZ9V', 17427, 'compromis'),
    ('OXQSBZ9V', 17430, 'offre'),
    ('Q602VZJX', 6555, 'compromis'),
    ('R0JRVFDC', 1001542, 'compromis'),
    ('RX6J289Y', 16377, 'compromis'),
    ('SBH4QWDW', 23050, 'compromis'),
    ('TR42PT5H', 27196, 'offre'),
    ('TRJ5Y59U', 1001561, 'offre'),
    ('UTLG66LE', 1001482, 'offre'),
    ('VEP1DVQ4', 7780, 'offre'),
    ('VMWFLLW4', 1001540, 'compromis'),
    ('WJ3KA32F', 10730, 'offre'),
    ('Y51UMZHY', 19277, 'offre'),
    ('a8aaeb2b', 998, 'compromis'),
    ('a8aaeb2b', 1000, 'offre'),
    ('f1aedc01', 28967, 'offre'),
    ('fa06e4e5', 28930, 'offre'),
    ('fa06e4e5', 1001553, 'compromis')
 ) v(id_unique, app_affaire_id, role)
 where l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id and l.role = v.role;

-- ── ④ AJOUTER (78) ─────────────────────────────────────────────────────────────
insert into app_classeur_lien
  (ligne_classeur, app_affaire_id, role, confiance, preuves, etage, gele_le, gele_par, id_unique)
values
    (173, 27195, 'compromis', 'sûre', 7, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'TR42PT5H'),
    (301, 2164, 'offre', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'MDOXOBIC'),
    (301, 2163, 'compromis', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'MDOXOBIC'),
    (301, 2165, 'vente', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'MDOXOBIC'),
    (457, 23995, 'offre', 'bonne', 6, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'TRJ5Y59U'),
    (535, 1876, 'offre', 'sûre', 5, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'A07EC3DH'),
    (566, 9371, 'offre', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'DHXRAK9O'),
    (566, 9370, 'compromis', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'DHXRAK9O'),
    (566, 9372, 'vente', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'DHXRAK9O'),
    (579, 6392, 'offre', 'bonne', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '72GQRHVB'),
    (579, 6391, 'compromis', 'bonne', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '72GQRHVB'),
    (579, 6393, 'vente', 'bonne', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '72GQRHVB'),
    (692, 4235, 'offre', 'bonne', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '7IHI7YTJ'),
    (692, 4234, 'compromis', 'bonne', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '7IHI7YTJ'),
    (692, 4236, 'vente', 'bonne', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '7IHI7YTJ'),
    (1546, 4413, 'offre', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'S8BKB6FL'),
    (1546, 4412, 'compromis', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'S8BKB6FL'),
    (1546, 4414, 'vente', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'S8BKB6FL'),
    (1866, 7780, 'offre', 'bonne', 7, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '2SCBZXMH'),
    (1902, 6555, 'compromis', 'sûre', 6, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'EGR8KXOL'),
    (1943, 4747, 'offre', 'sûre', 7, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '0GV2LNV2'),
    (2298, 14120, 'offre', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'LUX9SDIL'),
    (2298, 14119, 'compromis', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'LUX9SDIL'),
    (2298, 14121, 'vente', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'LUX9SDIL'),
    (2388, 11958, 'offre', 'bonne', 5, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '3S4ZWOFK'),
    (2774, 4929, 'offre', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'J6RGX0CQ'),
    (2774, 4928, 'compromis', 'sûre', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'J6RGX0CQ'),
    (2774, 4930, 'vente', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'J6RGX0CQ'),
    (2809, 7909, 'offre', 'bonne', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '58I5AO17'),
    (2809, 7908, 'compromis', 'bonne', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '58I5AO17'),
    (2809, 7910, 'vente', 'bonne', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '58I5AO17'),
    (2914, 6589, 'offre', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'ESMCO1NC'),
    (2914, 6588, 'compromis', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'ESMCO1NC'),
    (2914, 6590, 'vente', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'ESMCO1NC'),
    (3175, 19153, 'offre', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '8ATXF2EZ'),
    (3175, 19152, 'compromis', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '8ATXF2EZ'),
    (3175, 19154, 'vente', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '8ATXF2EZ'),
    (3263, 27986, 'offre', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'CS38OO8R'),
    (3263, 27984, 'compromis', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'CS38OO8R'),
    (3263, 27987, 'vente', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'CS38OO8R'),
    (3328, 15169, 'compromis', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'JL8GV7RQ'),
    (3328, 15170, 'vente', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'JL8GV7RQ'),
    (3378, 14227, 'offre', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '5H70KQZA'),
    (3378, 14224, 'compromis', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '5H70KQZA'),
    (3378, 14228, 'vente', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '5H70KQZA'),
    (3477, 3649, 'offre', 'sûre', 6, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '427UDDSF'),
    (3498, 6341, 'offre', 'bonne', 7, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'O1099YC0'),
    (3518, 23996, 'offre', 'sûre', 7, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'DAMOO7OU'),
    (3540, 1877, 'offre', 'sûre', 5, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'FLPUUSY3'),
    (3552, 7117, 'offre', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '7JXLR3JQ'),
    (3552, 7115, 'compromis', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '7JXLR3JQ'),
    (3635, 27170, 'offre', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'KAYC29B7'),
    (3795, 4387, 'offre', 'bonne', 5, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '8RWTD0YX'),
    (3810, 17430, 'offre', 'sûre', 6, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '515RUEN3'),
    (3810, 17428, 'compromis', 'sûre', 6, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '515RUEN3'),
    (3906, 1000105, 'offre', 'bonne', 2, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'O8BY6AC8'),
    (3906, 1000141, 'compromis', 'bonne', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'O8BY6AC8'),
    (3910, 23050, 'compromis', 'bonne', 6, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'VMWFLLW4'),
    (3927, 24291, 'offre', 'bonne', 5, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'PPIM4947'),
    (3961, 17431, 'offre', 'sûre', 6, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'OXQSBZ9V'),
    (3962, 7781, 'offre', 'sûre', 7, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'VEP1DVQ4'),
    (3968, 16378, 'compromis', 'sûre', 5, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'RX6J289Y'),
    (3970, 6554, 'compromis', 'bonne', 6, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'Q602VZJX'),
    (3988, 4748, 'offre', 'bonne', 7, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '3W10AEIK'),
    (4014, 16377, 'compromis', 'sûre', 5, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'R0JRVFDC'),
    (4113, 11959, 'offre', 'sûre', 6, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '9UO5NUN6'),
    (4131, 5055, 'offre', 'bonne', 4, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'UTLG66LE'),
    (4145, 23931, 'offre', 'sûre', 3, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '9706WM9J'),
    (4455, 19050, 'offre', 'bonne', 4, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'f90b0418'),
    (4668, 27196, 'offre', 'sûre', 7, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '739a0db1'),
    (4674, 28931, 'offre', 'bonne', 7, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'fa06e4e5'),
    (4761, 30827, 'compromis', 'sûre', 7, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'a2abd36c'),
    (4789, 30801, 'offre', 'sûre', 4, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'c6233284'),
    (4796, 30821, 'offre', 'sûre', 6, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'b884cbd4'),
    (4797, 30820, 'offre', 'sûre', 6, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '5e4c8881'),
    (4798, 30826, 'offre', 'sûre', 5, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', 'b43e76f5'),
    (4799, 30825, 'offre', 'sûre', 7, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '1eec6575'),
    (4800, 30824, 'offre', 'sûre', 7, 'audits independants 18-19/11', now(), 'audit_independant_v2_2026-11-19', '70740f2f');

-- ── ⑤ LE CONTROLE, DANS LA MEME TRANSACTION ─────────────────────────────────────
do $$
declare n int; doubles int; deux_roles int; poses int; mal int; garde int; temoin int; restes int;
begin
  select count(*) into n from app_classeur_lien;
  if n <> 12820 then raise exception '⛔ le gel porte % liens, attendu 12820', n; end if;
  -- ⭐ L'EXCLUSIVITE : aucune transaction prise par deux lignes (la base ne la garantit pas)
  select count(*) into doubles from (select app_affaire_id from app_classeur_lien
                                      group by 1 having count(distinct id_unique) > 1) x;
  if doubles <> 0 then raise exception '⛔ % transaction(s) prises par deux lignes', doubles; end if;
  -- ⭐ et aucune ligne a deux liens pour un MEME role parmi celles que le patch touche
  select count(*) into deux_roles from (select id_unique, role from app_classeur_lien
     where id_unique in (select distinct id_unique from app_classeur_lien where gele_par = 'audit_independant_v2_2026-11-19')
     group by 1, 2 having count(*) > 1) x;
  if deux_roles <> 0 then raise exception '⛔ % ligne(s) a deux liens pour un meme role', deux_roles; end if;
  -- ⭐ TEMOIN POSITIF : les 78 liens poses sont la, chacun vers le bon genre
  select count(*) into poses from app_classeur_lien where gele_par = 'audit_independant_v2_2026-11-19';
  if poses <> 78 then raise exception '⛔ % lien(s) poses, attendu 78', poses; end if;
  select count(*) into mal from app_classeur_lien l
    left join app_affaire_ledger a on a.app_affaire_id = l.app_affaire_id
   where l.gele_par = 'audit_independant_v2_2026-11-19' and (a.app_affaire_id is null or a.kind <> l.role
                                          or l.preuves < 2 or l.etage <> 'audits independants 18-19/11');
  if mal <> 0 then raise exception '⛔ % lien(s) pose(s) mal formes', mal; end if;
  -- ⭐ et les 45 retires sont partis
  select count(*) into restes from app_classeur_lien l join (values
    ('045ecde7', 28558, 'offre'),
    ('08GV8OMZ', 6341, 'offre'),
    ('1ESJE28Q', 12952, 'compromis'),
    ('1ESJE28Q', 12953, 'offre'),
    ('3S4ZWOFK', 1001580, 'offre'),
    ('3W10AEIK', 4747, 'offre'),
    ('427UDDSF', 3648, 'offre'),
    ('427UDDSF', 3650, 'vente'),
    ('45225170', 30712, 'offre'),
    ('45225170', 1001361, 'offre'),
    ('61OW86CS', 4496, 'compromis'),
    ('739a0db1', 27195, 'compromis'),
    ('739a0db1', 1001520, 'offre'),
    ('774aa002', 11138, 'compromis'),
    ('8Q3LHGZ4', 8321, 'compromis'),
    ('8Q3LHGZ4', 8322, 'offre'),
    ('8RWTD0YX', 4385, 'compromis'),
    ('8RWTD0YX', 1001477, 'offre'),
    ('9UO5NUN6', 11958, 'offre'),
    ('A07EC3DH', 1001563, 'offre'),
    ('CITFQGOB', 16378, 'compromis'),
    ('DAMOO7OU', 23995, 'offre'),
    ('EGR8KXOL', 6554, 'compromis'),
    ('FLPUUSY3', 1876, 'offre'),
    ('KT0601S6', 24291, 'offre'),
    ('NEFHS7JI', 26395, 'compromis'),
    ('NEFHS7JI', 26397, 'offre'),
    ('OXQSBZ9V', 17427, 'compromis'),
    ('OXQSBZ9V', 17430, 'offre'),
    ('Q602VZJX', 6555, 'compromis'),
    ('R0JRVFDC', 1001542, 'compromis'),
    ('RX6J289Y', 16377, 'compromis'),
    ('SBH4QWDW', 23050, 'compromis'),
    ('TR42PT5H', 27196, 'offre'),
    ('TRJ5Y59U', 1001561, 'offre'),
    ('UTLG66LE', 1001482, 'offre'),
    ('VEP1DVQ4', 7780, 'offre'),
    ('VMWFLLW4', 1001540, 'compromis'),
    ('WJ3KA32F', 10730, 'offre'),
    ('Y51UMZHY', 19277, 'offre'),
    ('a8aaeb2b', 998, 'compromis'),
    ('a8aaeb2b', 1000, 'offre'),
    ('f1aedc01', 28967, 'offre'),
    ('fa06e4e5', 28930, 'offre'),
    ('fa06e4e5', 1001553, 'compromis')
  ) v(id_unique, app_affaire_id, role) on l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id;
  if restes <> 0 then raise exception '⛔ % lien(s) a retirer encore presents', restes; end if;
  select count(*) into garde from app_classeur_lien_avant_audit_v2_20261119;
  if garde <> 12787 then raise exception '⛔ sauvegarde : % au lieu de 12787', garde; end if;
  -- ⭐ TEMOIN INVERSE : les liens que le patch ne touche pas sont IDENTIQUES, colonne par colonne
  select count(*) into temoin from app_classeur_lien l
    join app_classeur_lien_avant_audit_v2_20261119 s using (id_unique, app_affaire_id)
   where (l.role, l.confiance, l.preuves, l.etage, l.gele_par, l.ligne_classeur, l.gele_le)
         is distinct from (s.role, s.confiance, s.preuves, s.etage, s.gele_par, s.ligne_classeur, s.gele_le);
  if temoin <> 0 then raise exception '⛔ temoin inverse : % lien(s) non vise(s) ont change', temoin; end if;
  raise notice '✅ gel corrige : -45 +78 = 12820 liens, exclusivite tenue, voisins intacts.';
  raise notice '➡ A ENCHAINER (correction 3) : les valeurs posees par nous sur les transactions detachees -- voir la repetition.';
end $$;

commit;
