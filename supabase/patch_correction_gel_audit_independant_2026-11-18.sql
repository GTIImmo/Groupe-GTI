-- ═══════════════════════════════════════════════════════════════════════════════
-- LA CORRECTION DU GEL TIREE DE L'AUDIT INDEPENDANT                    18/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- ⛔ DORMANT : il ne se joue qu'avec l'accord explicite de Frederic.
-- SOURCE : notice/AUDIT_INDEPENDANT_CLASSEUR_2026-11-18.md et
--          notice/AUDIT_INDEPENDANT_CLASSEUR_OPERATIONS_GEL_2026-11-18.csv
--   55 liens RETIRES (faux, ou deplaces) . 109 liens AJOUTES (rattachements et
--   destinations des deplacements). 350 lignes jugees, 107 contre-expertises.
-- ⛔ CE QU'IL NE FAIT PAS : il ne touche NI les transactions (les copies de C5 se
--   retirent APRES, quand plus aucun lien ne les vise), NI les valeurs posees par
--   C2/C3/C4/C8/C9 sur une mauvaise transaction (geste a part), NI Hektor.
-- ⛔ LES LIGNES INCERTAINES (8) NE SONT PAS TOUCHEES : elles attendent sa reponse.
-- RETOUR ARRIERE : patch_correction_gel_audit_independant_2026-11-18_INVERSE.sql . CONTROLE : patch_correction_gel_audit_independant_2026-11-18_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════════
begin;

-- ── ① LA GARDE : le gel est EXACTEMENT celui que l'audit a lu ────────────────────
do $$
declare n int; manque int; deja int; cible_absente int;
begin
  select count(*) into n from app_classeur_lien;
  if n <> 12787 then
    raise exception '⛔ garde : le gel porte % liens au lieu de 12787 -- quelqu''un est passe, rien n''est ecrit', n;
  end if;
  select count(*) into manque from (values
    ('045ecde7', 28558),
    ('08GV8OMZ', 6341),
    ('1D7EIYKW', 27512),
    ('1ESJE28Q', 12952),
    ('1ESJE28Q', 12953),
    ('3308P0UX', 4480),
    ('3S4ZWOFK', 1001580),
    ('3W10AEIK', 4747),
    ('427UDDSF', 3648),
    ('427UDDSF', 3650),
    ('45225170', 30712),
    ('45225170', 1001361),
    ('5a956cad', 30776),
    ('61OW86CS', 4496),
    ('739a0db1', 27195),
    ('739a0db1', 1001520),
    ('774aa002', 11138),
    ('87QOXR64', 1001534),
    ('8Q3LHGZ4', 8321),
    ('8Q3LHGZ4', 8322),
    ('8RWTD0YX', 4385),
    ('8RWTD0YX', 1001477),
    ('9UO5NUN6', 11958),
    ('9WQ204HP', 1001532),
    ('A07EC3DH', 1001563),
    ('CITFQGOB', 16378),
    ('DAMOO7OU', 23995),
    ('E9GL6MUS', 11415),
    ('EGR8KXOL', 6554),
    ('FLPUUSY3', 1876),
    ('KT0601S6', 24291),
    ('NEFHS7JI', 26395),
    ('NEFHS7JI', 26397),
    ('OXQSBZ9V', 17427),
    ('OXQSBZ9V', 17430),
    ('Q602VZJX', 6555),
    ('QJQ9M4OF', 17366),
    ('R0JRVFDC', 1001542),
    ('RX6J289Y', 16377),
    ('SBH4QWDW', 23050),
    ('TR42PT5H', 27196),
    ('TRJ5Y59U', 1001561),
    ('UTLG66LE', 1001482),
    ('V3FO5NDA', 19131),
    ('V3FO5NDA', 19133),
    ('VEP1DVQ4', 7780),
    ('VMWFLLW4', 1001540),
    ('WJ3KA32F', 10730),
    ('Y51UMZHY', 19277),
    ('a8aaeb2b', 998),
    ('a8aaeb2b', 1000),
    ('ea6a28a7', 14033),
    ('f1aedc01', 28967),
    ('fa06e4e5', 28930),
    ('fa06e4e5', 1001553)
  ) v(id_unique, app_affaire_id)
  where not exists (select 1 from app_classeur_lien l
                     where l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id);
  if manque <> 0 then raise exception '⛔ garde : % lien(s) a retirer introuvable(s)', manque; end if;
end $$;

-- ── ② LA SAUVEGARDE DATEE, FERMEE DES SA NAISSANCE ─────────────────────────────
create table app_classeur_lien_avant_audit_independant_20261118 as select * from app_classeur_lien;
revoke all on app_classeur_lien_avant_audit_independant_20261118 from public, anon, authenticated;

-- ── ③ RETIRER (les liens faux, et l'origine des deplacements) ───────────────────
delete from app_classeur_lien l
 using (values
    ('045ecde7', 28558),
    ('08GV8OMZ', 6341),
    ('1D7EIYKW', 27512),
    ('1ESJE28Q', 12952),
    ('1ESJE28Q', 12953),
    ('3308P0UX', 4480),
    ('3S4ZWOFK', 1001580),
    ('3W10AEIK', 4747),
    ('427UDDSF', 3648),
    ('427UDDSF', 3650),
    ('45225170', 30712),
    ('45225170', 1001361),
    ('5a956cad', 30776),
    ('61OW86CS', 4496),
    ('739a0db1', 27195),
    ('739a0db1', 1001520),
    ('774aa002', 11138),
    ('87QOXR64', 1001534),
    ('8Q3LHGZ4', 8321),
    ('8Q3LHGZ4', 8322),
    ('8RWTD0YX', 4385),
    ('8RWTD0YX', 1001477),
    ('9UO5NUN6', 11958),
    ('9WQ204HP', 1001532),
    ('A07EC3DH', 1001563),
    ('CITFQGOB', 16378),
    ('DAMOO7OU', 23995),
    ('E9GL6MUS', 11415),
    ('EGR8KXOL', 6554),
    ('FLPUUSY3', 1876),
    ('KT0601S6', 24291),
    ('NEFHS7JI', 26395),
    ('NEFHS7JI', 26397),
    ('OXQSBZ9V', 17427),
    ('OXQSBZ9V', 17430),
    ('Q602VZJX', 6555),
    ('QJQ9M4OF', 17366),
    ('R0JRVFDC', 1001542),
    ('RX6J289Y', 16377),
    ('SBH4QWDW', 23050),
    ('TR42PT5H', 27196),
    ('TRJ5Y59U', 1001561),
    ('UTLG66LE', 1001482),
    ('V3FO5NDA', 19131),
    ('V3FO5NDA', 19133),
    ('VEP1DVQ4', 7780),
    ('VMWFLLW4', 1001540),
    ('WJ3KA32F', 10730),
    ('Y51UMZHY', 19277),
    ('a8aaeb2b', 998),
    ('a8aaeb2b', 1000),
    ('ea6a28a7', 14033),
    ('f1aedc01', 28967),
    ('fa06e4e5', 28930),
    ('fa06e4e5', 1001553)
 ) v(id_unique, app_affaire_id)
 where l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id;

-- ── ④ AJOUTER (les rattachements et la destination des deplacements) ────────────
insert into app_classeur_lien
  (ligne_classeur, app_affaire_id, role, confiance, preuves, etage, gele_le, gele_par, id_unique)
values
    (1943, 4747, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre BELLAT Martine, première proposition le 11/03/2021 (0 j), 20 000. Elle est aujourd''hui tenue à tort par la soeur 3W10AEIK, qui doit passer à 474', now(), 'audit_independant_2026-11-18', '0GV2LNV2'),
    (4799, 30825, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Ceaux Christian, premiere proposition 13/11/2026 (0 j), 42 000 EUR = prix du Sheet, annonce 63490 = lien CRM.', now(), 'audit_independant_2026-11-18', '1eec6575'),
    (1866, 7780, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre de DE OLIVEIRA Sonia, première proposition 2021-05-04 (0 j), 220000 €. Elle est seule dans la chaîne 7780 et aujourd''hui reliée à tort à la sœur', now(), 'audit_independant_2026-11-18', '2SCBZXMH'),
    (3323, 17769, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 03/07/2018 = Sheet (0 j). Acte prévu le 03/10/2018 contre le 28/09 au Sheet (5 j).', now(), 'audit_independant_2026-11-18', '2U5QPKRC'),
    (3323, 17770, 'vente', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente du 14/12/2018 = vente fixée (0 j).', now(), 'audit_independant_2026-11-18', '2U5QPKRC'),
    (2388, 11958, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Copie créée par C5 depuis cette ligne, absente chez Hektor ; la vraie offre est 11958 (CIMINO, 12/06/2020, 0 j).', now(), 'audit_independant_2026-11-18', '3S4ZWOFK'),
    (3988, 4748, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : 4747 est l''offre BELLAT du 11/03/2021 (49 j), qui appartient à la soeur 0GV2LNV2 (0 j). L''offre VINCENT Fabienne 4748 du 21/01/2021 tombe à 0 j.', now(), 'audit_independant_2026-11-18', '3W10AEIK'),
    (3477, 3649, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : 3648 est l''offre POTTIER du 23/08/2024 (22 j). L''offre SOUCHON 3649 tombe le 01/08/2024 (0 j, 450 000) et aucune ligne ne la prend.', now(), 'audit_independant_2026-11-18', '427UDDSF'),
    (4117, 19819, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : offre BROCHIER proposee le 2020-02-24 = Sheet 24/02/2020 (0 j), 69 000', now(), 'audit_independant_2026-11-18', '4G2UHO35'),
    (3810, 17428, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis annulé du 24/02/2022 = Sheet (0 j), hon 11 500 = commission.', now(), 'audit_independant_2026-11-18', '515RUEN3'),
    (3810, 17430, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : 1re proposition le 10/02/2022 = Sheet (0 j), LECOMTE Benjamin, 184 000 €.', now(), 'audit_independant_2026-11-18', '515RUEN3'),
    (2809, 7908, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 21/05/2019 (0 j).', now(), 'audit_independant_2026-11-18', '58I5AO17'),
    (2809, 7909, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Première proposition le 23/04/2019 (0 j), 66 500.', now(), 'audit_independant_2026-11-18', '58I5AO17'),
    (2809, 7910, 'vente', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente du 23/09/2019 = vente fixée (0 j).', now(), 'audit_independant_2026-11-18', '58I5AO17'),
    (3378, 14224, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis 2018-07-05 (0 j), 120000 €, hon 5000. Libre. Ne pas prendre 14225 ni 14226 : c''est la tentative PERRONNET de 2016 à 139000 €, que cette lign', now(), 'audit_independant_2026-11-18', '5H70KQZA'),
    (3378, 14227, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre PERRONNET 2018-04-10 (0 j). Libre.', now(), 'audit_independant_2026-11-18', '5H70KQZA'),
    (3378, 14228, 'vente', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente 2021-01-07 = Vente Fixée (0 j), réglée le 11/01/2021 (+4 j). Libre.', now(), 'audit_independant_2026-11-18', '5H70KQZA'),
    (4754, 30684, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : 30776 est l''offre renégociée du 27/10/2026 (82 218 €), à 36 j de l''offre du Sheet. Le 21/09/2026 du Sheet est la première proposition de 30684 (89 000', now(), 'audit_independant_2026-11-18', '5a956cad'),
    (4797, 30820, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : 1re proposition le 16/11/2026 = offre du Sheet (0 j).', now(), 'audit_independant_2026-11-18', '5e4c8881'),
    (589, 19131, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 08/12/2023 = Sheet (0 j). 80 000 € dont 6 000 € d''honoraires, notaire BARBIER comme au Sheet.', now(), 'audit_independant_2026-11-18', '6FQO29C8'),
    (589, 19133, 'vente', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente du 04/06/2024 = vente fixée (0 j). Réglée le 11/06 (+7 j). Honoraires 6 000 € = factures GGTI00003625 + GGTI00003664.', now(), 'audit_independant_2026-11-18', '6FQO29C8'),
    (4800, 30824, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Proposition du 17/11/2026 à 17:40 = Sheet (0 j), GUILLOT Antoine, 54 800 € (0 %), mandat 18773.', now(), 'audit_independant_2026-11-18', '70740f2f'),
    (579, 6391, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis 2023-11-30 (0 j) ; acte prévu 2024-02-29 = Vente Prévue (0 j). Libre.', now(), 'audit_independant_2026-11-18', '72GQRHVB'),
    (579, 6392, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre 2023-11-17 (0 j), 254000 €. Libre.', now(), 'audit_independant_2026-11-18', '72GQRHVB'),
    (579, 6393, 'vente', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente 2024-01-25 = Vente Fixée (0 j), réglée le 29/01 (+4 j). Libre.', now(), 'audit_independant_2026-11-18', '72GQRHVB'),
    (4668, 27196, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre HALLAERT-THEYS du 18/06/2026 (0 j), 199 000 € ; portée aujourd''hui à tort par la ligne TR42PT5H.', now(), 'audit_independant_2026-11-18', '739a0db1'),
    (692, 4234, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 21/11/2023 = Sheet (0 j), vendeurs LEDDA, hon 12 000 = commission.', now(), 'audit_independant_2026-11-18', '7IHI7YTJ'),
    (692, 4235, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : 1re proposition le 14/08/2023 = Sheet (0 j).', now(), 'audit_independant_2026-11-18', '7IHI7YTJ'),
    (692, 4236, 'vente', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Acte du 04/03/2024 = vente fixée (0 j) ; réglée le 05/03 (+1 j).', now(), 'audit_independant_2026-11-18', '7IHI7YTJ'),
    (3552, 7115, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis annule du 05/01/2024 (0 j), honoraires 3 500 = commission (« copie06/01 » au commentaire).', now(), 'audit_independant_2026-11-18', '7JXLR3JQ'),
    (3552, 7117, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Premiere proposition 10/11/2023 (0 j), 35 000 EUR.', now(), 'audit_independant_2026-11-18', '7JXLR3JQ'),
    (3829, 17427, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Copie créée par C5 depuis cette ligne, absente chez Hektor. Le compromis Hektor du 11/02/2022 existe : 17427, à 184 000 € / 11 500 €.', now(), 'audit_independant_2026-11-18', '87QOXR64'),
    (3175, 19152, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 20/03/2019 = Sheet (0 j).', now(), 'audit_independant_2026-11-18', '8ATXF2EZ'),
    (3175, 19153, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Première proposition le 06/02/2019 = Sheet (0 j).', now(), 'audit_independant_2026-11-18', '8ATXF2EZ'),
    (3175, 19154, 'vente', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente du 28/09/2019 = vente fixée (0 j). Réglée le 01/10.', now(), 'audit_independant_2026-11-18', '8ATXF2EZ'),
    (3795, 4387, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Creee depuis le Sheet alors que l''offre existe chez Hektor : 4387, VANROSSUM Garance, 25/02/2022 (0 j), 88 400 EUR = prix du Sheet.', now(), 'audit_independant_2026-11-18', '8RWTD0YX'),
    (2780, 4781, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 18/09/2019 (0 j) ; acte prévu le 18/12/2019 = vente prévue (0 j).', now(), 'audit_independant_2026-11-18', '91IHSGNC'),
    (2780, 4782, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Première proposition le 04/07/2019, 3 j après le 01/07 du Sheet ; c''est la seule offre de la chaîne, 44 900.', now(), 'audit_independant_2026-11-18', '91IHSGNC'),
    (2780, 4783, 'vente', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente du 18/12/2019 = vente fixée (0 j).', now(), 'audit_independant_2026-11-18', '91IHSGNC'),
    (4145, 23931, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre COMBETTES du 06/02/2020 (0 j), 168 000 €.', now(), 'audit_independant_2026-11-18', '9706WM9J'),
    (286, 3647, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 11/09/2024 (0 j), 460 000, hon 18 000. Il n''est lié à aucune ligne.', now(), 'audit_independant_2026-11-18', '9Q0FHAKK'),
    (286, 3648, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre POTTIER Dominique de 460 000, proposée et acceptée le 23/08/2024 (0 j). Elle est aujourd''hui tenue à tort par 427UDDSF.', now(), 'audit_independant_2026-11-18', '9Q0FHAKK'),
    (286, 3650, 'vente', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente du 22/01/2025 = vente fixée (0 j), 460 000, hon 18 000. Elle est aujourd''hui tenue à tort par 427UDDSF (lien v2 du 13/11).', now(), 'audit_independant_2026-11-18', '9Q0FHAKK'),
    (4113, 11959, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : 11958 est l''offre CIMINO du 12/06/2020 (15 j), qui appartient à la soeur 3S4ZWOFK (0 j). L''offre SOUDANI 11959 du 28/05/2020 tombe à 0 j, à 49 500.', now(), 'audit_independant_2026-11-18', '9UO5NUN6'),
    (3763, 4480, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Copie créée par C5 depuis cette ligne, absente chez Hektor. Le compromis Hektor du 15/06/2022 existe : 4480, à 87 000 € / 6 000 €.', now(), 'audit_independant_2026-11-18', '9WQ204HP'),
    (535, 1876, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Copie créée par C5 depuis cette ligne, absente chez Hektor. C''est un doublon de l''offre Hektor 1876 (GUERIN, première proposition le 12/01/2024, 0 j, ', now(), 'audit_independant_2026-11-18', 'A07EC3DH'),
    (3263, 27984, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : 02/11/2018 (0 j), honoraires 3 000 = commission ; nom CABEZOS = reliquat Hektor du premier acquereur.', now(), 'audit_independant_2026-11-18', 'CS38OO8R'),
    (3263, 27986, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : KEAY John et Claudia (KAEY au Sheet), premiere proposition 04/09/2018 (0 j), 15 000 EUR.', now(), 'audit_independant_2026-11-18', 'CS38OO8R'),
    (3263, 27987, 'vente', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Acte du 15/03/2019 (0 j).', now(), 'audit_independant_2026-11-18', 'CS38OO8R'),
    (3735, 17366, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre ROBERT Joel du 25/08/2022 (0 j), 213 000 € ; aujourd''hui portée à tort par la sœur QJQ9M4OF.', now(), 'audit_independant_2026-11-18', 'D9MMB7OU'),
    (3518, 23996, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : 23995 est l''offre GAY Frédèric du 25/03/2024 (26 j), qui appartient à la soeur TRJ5Y59U. L''offre MAITRIAS 23996 du 28/02/2024 tombe à 0 j et aucune li', now(), 'audit_independant_2026-11-18', 'DAMOO7OU'),
    (566, 9370, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 22/12/2023 = Sheet (0 j). Acte prévu le 22/03/2024 (9 j).', now(), 'audit_independant_2026-11-18', 'DHXRAK9O'),
    (566, 9371, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Première proposition le 01/12/2023 = Sheet (0 j).', now(), 'audit_independant_2026-11-18', 'DHXRAK9O'),
    (566, 9372, 'vente', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente du 12/03/2024 = vente fixée (0 j). Réglée le 14/03 (+2 j).', now(), 'audit_independant_2026-11-18', 'DHXRAK9O'),
    (3958, 11414, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : 11415 est l''offre MERCIER du 18/05/2021 (42 j), qui appartient à la soeur H6CTRVR6 (0 j). La seule offre du 06/04/2021 est 11414 (295 000, 0 j).', now(), 'audit_independant_2026-11-18', 'E9GL6MUS'),
    (1902, 6555, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Les deux compromis du bien tombent le 30/04/2021 (0 j). Mais 6554 est l''annulé à 90 000 € / 6 500 € (prix de l''offre BARDY), alors que 6555 est l''acti', now(), 'audit_independant_2026-11-18', 'EGR8KXOL'),
    (2485, 27712, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 03/06/2020 (0 j) ; acte prévu le 03/09/2020 = vente prévue (0 j).', now(), 'audit_independant_2026-11-18', 'EJN79TJ1'),
    (2485, 27713, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Première proposition le 27/02/2020 (0 j), 213 000.', now(), 'audit_independant_2026-11-18', 'EJN79TJ1'),
    (2485, 27714, 'vente', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente du 04/09/2020 = vente fixée (0 j).', now(), 'audit_independant_2026-11-18', 'EJN79TJ1'),
    (2914, 6588, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 26/05/2020 (0 j) ; acte prévu le 26/08/2020 = vente prévue (0 j).', now(), 'audit_independant_2026-11-18', 'ESMCO1NC'),
    (2914, 6589, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Première proposition le 14/05/2019 (0 j), 728 000.', now(), 'audit_independant_2026-11-18', 'ESMCO1NC'),
    (2914, 6590, 'vente', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente du 20/07/2020 = vente fixée (0 j).', now(), 'audit_independant_2026-11-18', 'ESMCO1NC'),
    (3540, 1877, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : 1876 est l''offre GUERIN du 12/01/2024 (35 j), qui appartient à la soeur A07EC3DH. L''offre PAYSAC 1877 du 08/12/2023 tombe à 0 j.', now(), 'audit_independant_2026-11-18', 'FLPUUSY3'),
    (1841, 11415, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre MERCIER, 1re proposition 18/05/2021 (0 j), 295 000 € ; aujourd''hui gelée sur la sœur annulée E9GL6MUS, qui doit prendre 11414 (06/04/2021, 0 j).', now(), 'audit_independant_2026-11-18', 'H6CTRVR6'),
    (2665, 24618, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 19/11/2019 (0 j) ; acte prévu le 19/02/2020, contre une vente prévue le 20/02/2020 (1 j).', now(), 'audit_independant_2026-11-18', 'I3TFR2KG'),
    (2665, 24619, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Première proposition le 22/10/2019 (0 j), 76 000.', now(), 'audit_independant_2026-11-18', 'I3TFR2KG'),
    (2665, 24620, 'vente', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente du 24/04/2020 = vente fixée (0 j).', now(), 'audit_independant_2026-11-18', 'I3TFR2KG'),
    (2774, 4928, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis daté du 2019-11-18 contre le 18/10/2019 au Sheet : même jour, un mois d''écart, sans doute une faute de mois. Libre.', now(), 'audit_independant_2026-11-18', 'J6RGX0CQ'),
    (2774, 4929, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre de DELABAR Soline, première proposition 2019-10-02 (0 j). Libre.', now(), 'audit_independant_2026-11-18', 'J6RGX0CQ'),
    (2774, 4930, 'vente', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente 2019-12-12 = Vente Fixée (0 j), réglée le 17/12 (+5 j). Libre.', now(), 'audit_independant_2026-11-18', 'J6RGX0CQ'),
    (3328, 15169, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : compromis du 2018-06-26 = Sheet 26/06/2018 (0 j), acte prevu 2018-09-26 (1 j de la vente prevue), SYLVAIN / MORISOT, hon 2 500 = commission', now(), 'audit_independant_2026-11-18', 'JL8GV7RQ'),
    (3328, 15170, 'vente', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : vente du 2018-10-10 = vente fixee 10/10/2018 (0 j)', now(), 'audit_independant_2026-11-18', 'JL8GV7RQ'),
    (3635, 27170, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : offre proposee et acceptee le 2023-05-10 = offre du Sheet 10/05/2023 (0 j), annonce 53371, vendeurs BOUTRY / DOUBTSOF', now(), 'audit_independant_2026-11-18', 'KAYC29B7'),
    (2298, 14119, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 04/09/2020 = Sheet (0 j).', now(), 'audit_independant_2026-11-18', 'LUX9SDIL'),
    (2298, 14120, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Première proposition le 17/07/2020 = Sheet (0 j).', now(), 'audit_independant_2026-11-18', 'LUX9SDIL'),
    (2298, 14121, 'vente', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente du 07/01/2021 = vente fixée (0 j). Réglée le 13/01.', now(), 'audit_independant_2026-11-18', 'LUX9SDIL'),
    (301, 2163, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis 2024-09-03 (0 j), 42000 €, vendeur RIVOLIER René. Libre.', now(), 'audit_independant_2026-11-18', 'MDOXOBIC'),
    (301, 2164, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre acceptée de la SARL BEMATID, première proposition 2024-08-08, le jour de « 8 août 24 » (0 j), 42000 €. Libre.', now(), 'audit_independant_2026-11-18', 'MDOXOBIC'),
    (301, 2165, 'vente', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente 2024-12-03 = Vente Fixée (0 j), réglée le 5 déc (+2 j). Libre.', now(), 'audit_independant_2026-11-18', 'MDOXOBIC'),
    (3383, 26695, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : 27/12/2017 (0 j), vendeur HDHILI, honoraires 1 000 = commission.', now(), 'audit_independant_2026-11-18', 'MQ6H8TVQ'),
    (3383, 26696, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Premiere proposition 14/12/2017 (0 j), 38 000 EUR (acquereur Hektor KABAB Julian).', now(), 'audit_independant_2026-11-18', 'MQ6H8TVQ'),
    (3383, 26698, 'vente', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Acte du 06/07/2018 (0 j).', now(), 'audit_independant_2026-11-18', 'MQ6H8TVQ'),
    (3498, 6341, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : CAMBRESY ET HEBRARD, premiere proposition 10/05/2024 (0 j), 126 000 EUR.', now(), 'audit_independant_2026-11-18', 'O1099YC0'),
    (3906, 1000105, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Seule offre de SCI 2NBD sur ce local. Première proposition le 23/07/2021, 16 j après le Sheet (07/07/2021, jour d''ouverture du mandat 13655).', now(), 'audit_independant_2026-11-18', 'O8BY6AC8'),
    (3906, 1000141, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis annulé du 01/09/2021 = Sheet (0 j).', now(), 'audit_independant_2026-11-18', 'O8BY6AC8'),
    (3961, 17431, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : 17430 est l''offre LECOMTE du 10/02/2022 (355 j), qui appartient à la soeur 515RUEN3 (0 j). L''offre CAGNARD 17431 du 20/02/2021 tombe à 0 j, et ses 195', now(), 'audit_independant_2026-11-18', 'OXQSBZ9V'),
    (3927, 24291, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : offre refusee du 2021-06-24 a 78 400 (0 j), aujourd''hui gelee en trop sur la soeur KT0601S6', now(), 'audit_independant_2026-11-18', 'PPIM4947'),
    (3970, 6554, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : 6555 (actif, 87 000 €, honoraires 6 000) est le compromis de la vente GLAZIOU (soeur EGR8KXOL). Celui de BARDY est 6554 : même date du 30/04/2021, 90 ', now(), 'audit_independant_2026-11-18', 'Q602VZJX'),
    (2559, 1027, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 29/05/2020 (0 j).', now(), 'audit_independant_2026-11-18', 'QXDW8EQA'),
    (2559, 1028, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Première proposition le 11/01/2020 (0 j), 1 358 840.', now(), 'audit_independant_2026-11-18', 'QXDW8EQA'),
    (2559, 1029, 'vente', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Vente du 04/11/2020 = vente fixée (0 j).', now(), 'audit_independant_2026-11-18', 'QXDW8EQA'),
    (4014, 16377, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Créé par C5 depuis cette ligne et absent chez Hektor, il double 16377, le compromis Hektor de cette affaire.', now(), 'audit_independant_2026-11-18', 'R0JRVFDC'),
    (3968, 16378, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : 16377 (27/10/2020, 249 000, honoraires 15 000, acte prévu 27/01/2021) est le compromis de la soeur R0JRVFDC. 16378 porte 244 000, des honoraires de 10', now(), 'audit_independant_2026-11-18', 'RX6J289Y'),
    (1546, 4412, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis du 14/03/2022 (0 j).', now(), 'audit_independant_2026-11-18', 'S8BKB6FL'),
    (1546, 4413, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre THOMAS John du 12/11/2021 (0 j).', now(), 'audit_independant_2026-11-18', 'S8BKB6FL'),
    (1546, 4414, 'vente', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Acte du 21/04/2022 (0 j).', now(), 'audit_independant_2026-11-18', 'S8BKB6FL'),
    (173, 27195, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis MORAND Thomas / ZIMMER Emma du 24/01/2025, 209 000, hon 9 000, vendeurs BELONJE/BIEL, annulé. Le Sheet ne date pas le compromis, mais c''est ', now(), 'audit_independant_2026-11-18', 'TR42PT5H'),
    (457, 23995, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Creee depuis le Sheet alors que l''offre existe chez Hektor : 23995 de GAY Frederic (le Sheet dit « MARTINEZ GAY »), premiere proposition 25/03/2024 (0', now(), 'audit_independant_2026-11-18', 'TRJ5Y59U'),
    (4131, 5055, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Créée par C5 depuis cette ligne, elle ne prouve rien. Hektor porte déjà l''offre STAUFFER 5055, proposée et acceptée le 18/12/2019 (0 j), 16 900.', now(), 'audit_independant_2026-11-18', 'UTLG66LE'),
    (3962, 7781, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : 7780 est l''offre DE OLIVEIRA du 04/05/2021 (33 j, 220 000), qui appartient à la soeur 2SCBZXMH (0 j). L''offre COLOMBET 7781 du 01/04/2021 tombe à 0 j,', now(), 'audit_independant_2026-11-18', 'VEP1DVQ4'),
    (3910, 23050, 'compromis', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : cree depuis le Sheet alors que Hektor porte deja ce compromis : 23050 du 2021-06-17 a 70 000, hon 4 400', now(), 'audit_independant_2026-11-18', 'VMWFLLW4'),
    (4126, 1337, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre de THEVENON Frederic, première proposition 2020-02-10 (0 j), 38500 €, annonce 3481 = MODELO du mandat 12224 (BOUALI). Libre.', now(), 'audit_independant_2026-11-18', 'Z6P7KE5R'),
    (4119, 11206, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre du 02/12/2019 à 280 000 €, sans nom d''acquéreur chez Hektor.', now(), 'audit_independant_2026-11-18', 'ZZ5WKMWM'),
    (4761, 30827, 'compromis', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Compromis actif du 13/11/2026 (0 j), ALLEPUZ, 90 000 € / 6 580 €. L''acte prévu le 13/02/2027 est la vente prévue du Sheet (0 j). Arrivé chez nous aprè', now(), 'audit_independant_2026-11-18', 'a2abd36c'),
    (4798, 30826, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre BUGNON du 17/11/2026 (0 j), 160 000 €.', now(), 'audit_independant_2026-11-18', 'b43e76f5'),
    (4796, 30821, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : 1re proposition le 15/11/2026 = offre du Sheet (0 j).', now(), 'audit_independant_2026-11-18', 'b884cbd4'),
    (4789, 30801, 'offre', 'sûre', 0, 'audit independant 18/11 (juge + contre-expertise) : offre proposee le 2026-11-04 = Sheet 04/11/2026 (0 j), 485 000, annonce 63463 du lien CRM, MARTINS', now(), 'audit_independant_2026-11-18', 'c6233284'),
    (4455, 19050, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : Offre POULY et CHARTOIRE à 93 000 €, seule offre du bien, tenue par aucune ligne. Date non mesurable : le journal n''a aucune date avant le refus du 12', now(), 'audit_independant_2026-11-18', 'f90b0418'),
    (4674, 28931, 'offre', 'bonne', 0, 'audit independant 18/11 (juge + contre-expertise) : 28930 est une offre sans acquereur, refusee le jour meme ; la correction du 17/11 l''a retenue sur la seule date, que les deux offres partagent. 28931 ', now(), 'audit_independant_2026-11-18', 'fa06e4e5');

-- ── ⑤ LE CONTROLE, DANS LA MEME TRANSACTION ─────────────────────────────────────
do $$
declare n int; doubles int; poses int; garde int; temoin int;
begin
  select count(*) into n from app_classeur_lien;
  if n <> 12787 - 55 + 109 then
    raise exception '⛔ le gel porte % liens, attendu 12841', n;
  end if;
  -- ⭐ L'EXCLUSIVITE : aucune transaction prise par deux lignes (la base ne la garantit pas)
  select count(*) into doubles from (select app_affaire_id from app_classeur_lien
                                      group by 1 having count(distinct id_unique) > 1) x;
  if doubles <> 0 then raise exception '⛔ % transaction(s) prises par deux lignes', doubles; end if;
  -- chaque cible existe et porte le genre de son role
  select count(*) into poses from app_classeur_lien l
    left join app_affaire_ledger a on a.app_affaire_id = l.app_affaire_id
   where l.gele_par = 'audit_independant_2026-11-18' and (a.app_affaire_id is null or a.kind <> l.role);
  if poses <> 0 then raise exception '⛔ % lien(s) pose(s) vers une transaction absente ou d''un autre genre', poses; end if;
  select count(*) into garde from app_classeur_lien_avant_audit_independant_20261118;
  if garde <> 12787 then raise exception '⛔ sauvegarde : % au lieu de 12787', garde; end if;
  -- ⭐ TEMOIN INVERSE : les liens que l'audit ne touche pas sont IDENTIQUES
  select count(*) into temoin from app_classeur_lien l
    join app_classeur_lien_avant_audit_independant_20261118 s using (id_unique, app_affaire_id)
   where (l.role, l.confiance, l.etage, l.gele_par) is distinct from (s.role, s.confiance, s.etage, s.gele_par);
  if temoin <> 0 then raise exception '⛔ temoin inverse : % lien(s) non vise(s) ont change', temoin; end if;
  raise notice '✅ gel corrige : -% +%, exclusivite tenue, voisins intacts', 55, 109;
end $$;

commit;
