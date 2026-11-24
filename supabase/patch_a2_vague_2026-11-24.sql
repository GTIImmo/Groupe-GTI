-- patch_a2_vague_2026-11-24 -- genere par phase2/checks/a2_vague_generer_patch_2026-11-24.py
-- A2 DE LA VAGUE DU SOIR, PAR PIECES (A2 v3 : sa regle 6, « une annulee ne porte aucune part », NRZVKH85 completee).
-- Export : passage 81, image 2026-11-24_175707. Lot du journal : a2_vague_2026-11-24.
-- ⛔ Ce patch ne se joue qu'a l'ETAPE 7 de la vague, apres le chainage pousse et controle -- et sur SON accord.

begin;

-- ─── ⓪ LES PIECES DU LOT, une seule fois : les chaines touchees, les cibles, les paires, les mises de cote ─────────────
create temporary table a2_touchees (c bigint primary key) on commit drop;
insert into a2_touchees values
    (21), (117), (118), (125), (126), (1059), (1060), (1103), (1160), (1161), (2166), (2167), (2210), (2211), (2357), (2358),
    (2633), (2634), (3676), (3677), (3699), (3701), (3719), (3720), (4196), (4267), (4269), (4271), (4272), (4277), (4278), (4290),
    (4370), (4371), (4372), (4388), (4480), (4481), (4484), (4500), (4501), (4508), (4509), (4533), (4534), (4560), (4561), (4621),
    (4622), (4649), (4650), (4653), (4655), (4669), (4670), (4706), (4707), (4850), (4851), (4908), (4909), (6171), (6172), (6433),
    (6434), (6554), (6555), (7452), (7606), (7645), (7647), (7699), (7700), (7710), (7711), (7719), (7720), (7904), (8019), (8840),
    (8841), (8856), (8857), (9496), (9497), (11145), (11146), (11167), (11168), (11412), (11413), (11546), (11547), (11560), (11581), (11654),
    (11655), (11667), (11668), (12011), (12012), (12566), (12567), (14147), (14148), (14817), (14939), (14940), (15004), (15059), (15061), (16031),
    (16032), (16143), (16144), (16336), (16337), (16362), (16364), (16377), (16379), (16841), (16842), (16869), (17024), (17027), (17131), (17132),
    (17136), (17153), (17154), (17288), (17289), (17387), (17388), (17390), (17422), (17423), (17429), (17546), (17547), (17912), (17913), (19619),
    (19620), (19690), (19691), (19814), (19816), (19818), (19862), (19863), (20073), (20075), (20264), (20265), (20267), (20794), (20795), (21658),
    (21659), (22269), (22270), (22979), (22980), (23050), (23051), (23053), (23412), (23413), (23475), (23476), (23993), (23994), (24004), (24005),
    (24122), (24124), (24281), (24282), (24333), (24380), (24381), (24382), (24406), (24407), (24443), (24444), (24450), (24451), (24453), (24499),
    (24500), (24588), (24590), (24598), (24599), (24630), (24631), (24649), (24650), (25626), (25627), (25839), (25840), (25897), (25898), (26013),
    (26026), (26027), (26029), (26154), (26156), (26603), (26604), (26832), (26833), (27136), (27448), (27512), (27655), (27656), (27721), (27722),
    (28568), (28569), (28931), (1000050), (1000125), (1000127), (1000250);
create temporary table a2_cibles (c bigint primary key) on commit drop;
insert into a2_cibles values
    (118), (126), (1060), (1161), (2167), (2211), (2358), (2634), (3677), (3699), (3720), (4269), (4278), (4371), (4481), (4501),
    (4509), (4534), (4561), (4622), (4650), (4670), (4707), (4851), (4909), (6172), (6434), (6555), (7647), (7700), (7711), (7720),
    (8841), (8857), (9497), (11146), (11168), (11413), (11547), (11655), (11668), (12012), (12567), (14148), (14940), (15061), (16032), (16144),
    (16337), (16364), (16379), (16842), (17027), (17132), (17154), (17289), (17388), (17423), (17547), (17913), (19620), (19691), (19816), (19863),
    (20073), (20265), (20795), (21659), (22270), (23051), (23413), (23476), (23994), (24005), (24124), (24282), (24382), (24407), (24444), (24451),
    (24500), (24590), (24599), (24631), (24650), (25627), (25840), (25898), (26029), (26156), (26604), (26833), (27656), (27722), (28569), (1000050),
    (1000127);
-- « de la chaine s (l'ancienne, la ou vivent les parts) vers la chaine ou arrive la piece P »
create temporary table a2_paires (s bigint, piece bigint, lignes text) on commit drop;
insert into a2_paires values
    (117, 118, 'P0YMQODU'),
    (125, 126, 'AOPBUAOJ'),
    (1059, 1060, 'YPNDHILU'),
    (1160, 1161, 'F6XBD2IU'),
    (2166, 2167, 'ZLY1CLKF'),
    (2210, 2211, 'BZDTPD98'),
    (2357, 2358, 'USL9H5AJ'),
    (2633, 2634, 'QXOCABQG'),
    (3676, 3677, 'c08ff7cb'),
    (3701, 3699, 'I847SPN3'),
    (3719, 3720, 'ZOJDHHL9'),
    (4267, 4269, 'UY443H27'),
    (4277, 4278, 'WVMPHHDQ'),
    (4370, 4371, 'TL9AFW0O'),
    (4480, 4481, 'N1CUULMN'),
    (4500, 4501, 'WPGZK930'),
    (4508, 4509, '3X3UPF1Q'),
    (4533, 4534, 'FYNZEKI6'),
    (4560, 4561, 'BNWNKPJH'),
    (4621, 4622, '910O0A2Q'),
    (4649, 4650, 'VX5RZL6B'),
    (4669, 4670, 'ZMQZSE9Q'),
    (4706, 4707, 'VHE3HXC3'),
    (4850, 4851, 'R9ANL92S'),
    (4908, 4909, 'GD6CVLJB'),
    (6171, 6172, 'a5cb141f'),
    (6433, 6434, '7BPVD7K4'),
    (6554, 6555, 'EGR8KXOL'),
    (7645, 7647, 'D5KU9GNT'),
    (7699, 7700, 'U43BNSQW'),
    (7710, 7711, 'SWDW99J5'),
    (7719, 7720, 'BLKP7JFQ'),
    (8840, 8841, 'U8739KRW'),
    (8856, 8857, 'A94E7E0K'),
    (9496, 9497, 'JHCF1D3M'),
    (11145, 11146, 'e9260960'),
    (11167, 11168, 'UZ7HB9VH'),
    (11412, 11413, 'H6CTRVR6'),
    (11546, 11547, 'X89SXIQZ'),
    (11654, 11655, '29YBUBYA'),
    (11667, 11668, 'YMEKXZK3'),
    (12011, 12012, 'ANHQ1PK7'),
    (12566, 12567, 'QL70KV8I'),
    (14147, 14148, '5ELT15Q7'),
    (14939, 14940, 'DKTK22F2'),
    (15059, 15061, '5VZDGQC3'),
    (16031, 16032, 'UHVX3QH1'),
    (16143, 16144, 'KTZJRCR2'),
    (16336, 16337, 'AIV9UI0I'),
    (16362, 16364, '1290IIOC'),
    (16377, 16379, 'JUTS27P6'),
    (16841, 16842, 'DY4JG42E'),
    (17024, 17027, 'X2714E92'),
    (17131, 17132, '510YKN3L'),
    (17153, 17154, 'A6OS2TTJ'),
    (17288, 17289, 'SS4I5EZW'),
    (17387, 17388, 'TFK7BD9K'),
    (17422, 17423, 'M8QJWMBM'),
    (17546, 17547, 'V5NJER40'),
    (17912, 17913, '9JCIQYZX'),
    (19619, 19620, 'GWAP2ROG'),
    (19690, 19691, 'C0U52ILC'),
    (19814, 19816, 'MYILWKZQ'),
    (19862, 19863, 'JBCC1KBT'),
    (20075, 20073, '-'),
    (20264, 20265, 'K013ZH03'),
    (20794, 20795, 'MFMR0U6A'),
    (21658, 21659, '8BJKJ6XP'),
    (22269, 22270, 'WG8CG5T2'),
    (23050, 23051, 'DBRDHEGH'),
    (23412, 23413, 'PB3ASE0N'),
    (23475, 23476, 'W79RISV0'),
    (23993, 23994, 'TRJ5Y59U'),
    (24004, 24005, 'e48a523c'),
    (24122, 24124, '305KAY9W'),
    (24281, 24282, 'FRROUPY0'),
    (24380, 24382, 'RF9KYWSY'),
    (24406, 24407, '7P1JJ2PP'),
    (24443, 24444, '45PERG6S'),
    (24450, 24451, 'BETUXDEN'),
    (24499, 24500, 'LLR19GDU'),
    (24588, 24590, 'XH5KZ9LI'),
    (24598, 24599, 'VNK6GU21'),
    (24630, 24631, '50LQ2VSA'),
    (24649, 24650, 'ESVJUR12'),
    (25626, 25627, 'OAQDRTNC'),
    (25839, 25840, '46b0a92c'),
    (25897, 25898, '81LLHEM6'),
    (26027, 26029, 'DKH6IOKA'),
    (26154, 26156, 'L4HEO3NF'),
    (26603, 26604, '1TZEGF2D'),
    (26832, 26833, 'II80B5HW'),
    (27655, 27656, 'E2JTIT1V'),
    (27721, 27722, 'SA7DWYEZ'),
    (28568, 28569, '959b7669'),
    (1000125, 1000127, 'MPF7E8N7'),
    (1000250, 1000050, 'G8YSAI5Z');
create temporary table a2_mises (s bigint, lignes text, vers_piece bigint, motif text) on commit drop;
insert into a2_mises values
    (21, '7NI4WKV5', null, '7NI4WKV5 arrive sur la chaine 22, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 21 reste (membres 21,27) sans aucune ligne'),
    (117, 'P0YMQODU', 118, 'P0YMQODU quitte la chaine 117 -> recopiee sur la chaine de la piece 118 ; la chaine 117 reste (membres 117,120) sans aucune ligne'),
    (125, 'AOPBUAOJ', 126, 'AOPBUAOJ quitte la chaine 125 -> recopiee sur la chaine de la piece 126 ; la chaine 125 reste (membres 125) sans aucune ligne'),
    (1059, 'AHKQI7MX+YPNDHILU', 1060, 'AHKQI7MX+YPNDHILU quitte la chaine 1059 -> recopiee sur la chaine de la piece 1060 ; la chaine 1059 reste (membres 1059) sans aucune ligne'),
    (1103, '-', 1103, 'la chaine 1103 disparait (la piece 1103 rejoint 1101) -> les MEMES parts y vivent deja'),
    (3701, 'I847SPN3', 3699, 'I847SPN3 quitte la chaine 3701 -> recopiee sur la chaine de la piece 3699 ; la chaine 3701 reste (membres 3701) sans aucune ligne'),
    (4196, '5R6RC36Y', null, '5R6RC36Y arrive sur la chaine 4197, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 4196 reste (membres 4196) sans aucune ligne'),
    (4271, 'NSRISB3C', null, 'NSRISB3C arrive sur la chaine 4267, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (4272, '9FP3UICY', null, '9FP3UICY arrive sur la chaine 4268, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (4290, 'LKBO1TOH', null, 'LKBO1TOH arrive sur la chaine 4289, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (4370, 'TL9AFW0O', 4371, 'TL9AFW0O quitte la chaine 4370 -> recopiee sur la chaine de la piece 4371 ; la chaine 4370 reste (membres 4370,4372,1001530) sans aucune ligne'),
    (4372, 'FWCFAN6O', null, 'FWCFAN6O arrive sur la chaine 4370, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (4388, 'U0GQ3KTO', null, 'U0GQ3KTO arrive sur la chaine 4385, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; U0GQ3KTO EN RESERVE (8RWTD0YX, meme mandat 14065)'),
    (4484, '-', 4484, 'la chaine 4484 disparait (la piece 4484 rejoint 4480) -> les MEMES parts y vivent deja'),
    (4500, 'WPGZK930', 4501, 'WPGZK930 quitte la chaine 4500 -> recopiee sur la chaine de la piece 4501 ; la chaine 4500 reste (membres 4500,4503) sans aucune ligne'),
    (4533, 'FYNZEKI6', 4534, 'FYNZEKI6 quitte la chaine 4533 -> recopiee sur la chaine de la piece 4534 ; la chaine 4533 reste (membres 4533,4536) sans aucune ligne'),
    (4560, 'BNWNKPJH', 4561, 'BNWNKPJH quitte la chaine 4560 -> recopiee sur la chaine de la piece 4561 ; la chaine 4560 reste (membres 4560,4563) sans aucune ligne'),
    (4621, '910O0A2Q', 4622, '910O0A2Q quitte la chaine 4621 -> recopiee sur la chaine de la piece 4622 ; la chaine 4621 reste (membres 4621,4625) sans aucune ligne'),
    (4653, 'HHQZC2QP', null, 'HHQZC2QP arrive sur la chaine 4649, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (4655, 'N9J2533O', null, 'N9J2533O arrive sur la chaine 4651, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (4669, 'ZMQZSE9Q', 4670, 'ZMQZSE9Q quitte la chaine 4669 -> recopiee sur la chaine de la piece 4670 ; la chaine 4669 reste (membres 4669,4672) sans aucune ligne'),
    (4850, 'R9ANL92S', 4851, 'R9ANL92S quitte la chaine 4850 -> recopiee sur la chaine de la piece 4851 ; la chaine 4850 reste (membres 4850,4852) sans aucune ligne'),
    (6171, 'a5cb141f', 6172, 'a5cb141f quitte la chaine 6171 -> recopiee sur la chaine de la piece 6172 ; la chaine 6171 reste (membres 6171) sans aucune ligne'),
    (6433, '7BPVD7K4', 6434, '7BPVD7K4 quitte la chaine 6433 -> recopiee sur la chaine de la piece 6434 ; la chaine 6433 reste (membres 6433,6436) sans aucune ligne'),
    (7452, 'DN5U3GER', null, 'DN5U3GER arrive sur la chaine 7450, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (7606, 'R90OQT16', null, 'R90OQT16 arrive sur la chaine 7605, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (7645, 'D5KU9GNT', 7647, 'D5KU9GNT quitte la chaine 7645 -> recopiee sur la chaine de la piece 7647 ; la chaine 7645 reste (membres 7645,7650) sans aucune ligne'),
    (7904, 'UAER0F0F', null, 'UAER0F0F arrive sur la chaine 7903, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (8019, 'SXJDHXKF', 8019, 'la chaine 8019 disparait (la piece 8019 rejoint 8016) -> les MEMES parts y vivent deja'),
    (11560, '8NZ6V6XB', null, '8NZ6V6XB arrive sur la chaine 11558, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 11560 reste (membres 11560) sans aucune ligne'),
    (11581, 'ULFVA1AQ', null, 'ULFVA1AQ arrive sur la chaine 11579, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (12011, 'ANHQ1PK7', 12012, 'ANHQ1PK7 quitte la chaine 12011 -> recopiee sur la chaine de la piece 12012 ; la chaine 12011 reste (membres 12011,12013,12016) sans aucune ligne'),
    (12566, 'QL70KV8I', 12567, 'QL70KV8I quitte la chaine 12566 -> recopiee sur la chaine de la piece 12567 ; la chaine 12566 reste (membres 12566,12569) sans aucune ligne'),
    (14147, '5ELT15Q7', 14148, '5ELT15Q7 quitte la chaine 14147 -> recopiee sur la chaine de la piece 14148 ; la chaine 14147 reste (membres 14147) sans aucune ligne'),
    (14817, '-', 14817, 'la chaine 14817 disparait (la piece 14817 rejoint 14813) -> les MEMES parts y vivent deja'),
    (15004, 'MY2EIUFQ', null, 'MY2EIUFQ arrive sur la chaine 15005, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 15004 reste (membres 15004) sans aucune ligne'),
    (16143, 'KTZJRCR2', 16144, 'KTZJRCR2 quitte la chaine 16143 -> recopiee sur la chaine de la piece 16144 ; la chaine 16143 reste (membres 16143) sans aucune ligne'),
    (16869, 'CA2XNF38', null, 'CA2XNF38 arrive sur la chaine 16870, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 16869 reste (membres 16869,16872) sans aucune ligne'),
    (17136, 'ZV3QRSJG', null, 'ZV3QRSJG arrive sur la chaine 17131, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 17136 reste (membres 17136) sans aucune ligne'),
    (17153, 'A6OS2TTJ', 17154, 'A6OS2TTJ quitte la chaine 17153 -> recopiee sur la chaine de la piece 17154 ; la chaine 17153 reste (membres 17153,17156,17157) sans aucune ligne'),
    (17390, '-', 17390, 'la chaine 17390 disparait (la piece 17390 rejoint 17387) -> les MEMES parts y vivent deja'),
    (17429, '-', 17429, 'la chaine 17429 disparait (la piece 17429 rejoint 17427) -> les MEMES parts y vivent deja'),
    (17546, 'V5NJER40', 17547, 'V5NJER40 quitte la chaine 17546 -> recopiee sur la chaine de la piece 17547 ; la chaine 17546 reste (membres 17546,17549) sans aucune ligne'),
    (17912, '9JCIQYZX', 17913, '9JCIQYZX quitte la chaine 17912 -> recopiee sur la chaine de la piece 17913 ; la chaine 17912 reste (membres 17912,17915) sans aucune ligne'),
    (19818, 'R7NU9NPM', null, 'R7NU9NPM arrive sur la chaine 19815, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (19862, 'JBCC1KBT', 19863, 'JBCC1KBT quitte la chaine 19862 -> recopiee sur la chaine de la piece 19863 ; la chaine 19862 reste (membres 19862,19865) sans aucune ligne'),
    (20075, '-', 20073, 'la chaine disparait, sans ligne : quitte la chaine 20075 -> recopiee sur la chaine de la piece 20073'),
    (20267, '-', 20267, 'la chaine 20267 disparait (la piece 20267 rejoint 20264) -> les MEMES parts y vivent deja'),
    (20794, 'MFMR0U6A', 20795, 'MFMR0U6A quitte la chaine 20794 -> recopiee sur la chaine de la piece 20795 ; la chaine 20794 reste (membres 20794,20797) sans aucune ligne'),
    (21658, '8BJKJ6XP', 21659, '8BJKJ6XP quitte la chaine 21658 -> recopiee sur la chaine de la piece 21659 ; la chaine 21658 reste (membres 21658) sans aucune ligne'),
    (22269, 'WG8CG5T2', 22270, 'WG8CG5T2 quitte la chaine 22269 -> recopiee sur la chaine de la piece 22270 ; la chaine 22269 reste (membres 22269,22272) sans aucune ligne'),
    (22980, 'NRZVKH85', 22979, 'NRZVKH85 quitte la chaine 22980 pour 22979 (qui portait son entree) -> completee de sa sortie ; la chaine 22980 reste (membres 22980) sans aucune ligne'),
    (23053, '-', 23053, 'la chaine 23053 disparait (la piece 23053 rejoint 23050) -> les MEMES parts y vivent deja'),
    (23412, 'PB3ASE0N', 23413, 'PB3ASE0N quitte la chaine 23412 -> recopiee sur la chaine de la piece 23413 ; la chaine 23412 reste (membres 23412,23415) sans aucune ligne'),
    (24333, 'N8M7RKTN', null, 'N8M7RKTN arrive sur la chaine 24331, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (24381, '-', 24381, 'la chaine 24381 disparait (la piece 24381 rejoint 24380) -> les MEMES parts y vivent deja'),
    (24453, '-', 24453, 'la chaine 24453 disparait (la piece 24453 rejoint 24450) -> les MEMES parts y vivent deja'),
    (24588, 'XH5KZ9LI', 24590, 'XH5KZ9LI quitte la chaine 24588 -> recopiee sur la chaine de la piece 24590 ; la chaine 24588 reste (membres 24588) sans aucune ligne'),
    (24630, '50LQ2VSA', 24631, '50LQ2VSA quitte la chaine 24630 -> recopiee sur la chaine de la piece 24631 ; la chaine 24630 reste (membres 24630,24632) sans aucune ligne'),
    (24649, 'ESVJUR12', 24650, 'ESVJUR12 quitte la chaine 24649 -> recopiee sur la chaine de la piece 24650 ; la chaine 24649 reste (membres 24649) sans aucune ligne'),
    (26013, '7MOMHHQ1', null, '7MOMHHQ1 arrive sur la chaine 26016, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 26013 reste (membres 26013) sans aucune ligne'),
    (26026, 'I0K9TUCT', null, 'I0K9TUCT arrive sur la chaine 26023, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (26832, 'II80B5HW', 26833, 'II80B5HW quitte la chaine 26832 -> recopiee sur la chaine de la piece 26833 ; la chaine 26832 reste (membres 26832) sans aucune ligne'),
    (27136, 'IEYXREWQ', null, 'IEYXREWQ arrive sur la chaine 27134, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 27136 reste (membres 27136,27141) sans aucune ligne'),
    (27448, '-', 27448, 'la chaine 27448 disparait (la piece 27448 rejoint 27445) -> les MEMES parts y vivent deja'),
    (27512, '1D7EIYKW', null, '1D7EIYKW arrive sur la chaine 27513, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 27512 reste (membres 27512) sans aucune ligne'),
    (27721, 'SA7DWYEZ', 27722, 'SA7DWYEZ quitte la chaine 27721 -> recopiee sur la chaine de la piece 27722 ; la chaine 27721 reste (membres 27721,27724) sans aucune ligne'),
    (28568, '959b7669', 28569, '959b7669 quitte la chaine 28568 -> recopiee sur la chaine de la piece 28569 ; la chaine 28568 reste (membres 28568) sans aucune ligne'),
    (28931, 'fa06e4e5', null, 'fa06e4e5 arrive sur la chaine 28930, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (1000250, 'G8YSAI5Z', 1000050, 'G8YSAI5Z quitte la chaine 1000250 -> recopiee sur la chaine de la piece 1000050');

-- ─── ① LES GARDES -- une seule qui refuse, et RIEN n'est ecrit ─────────────────────────────────────────────────────
do $$
declare n int; e text; d text;
begin
  -- G0 : le patch ne se rejoue pas
  if to_regclass('public.app_affaire_repartition_avant_a2vague_20261124') is not null then
    raise exception '⛔ G0 : la sauvegarde app_affaire_repartition_avant_a2vague_20261124 existe deja -- ce patch ne se rejoue pas';
  end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'a2_vague_2026-11-24';
  if n <> 0 then raise exception '⛔ G0 : % ligne(s) du lot a2_vague_2026-11-24 deja au journal', n; end if;
  -- G1 : LES PIECES -- chaque chaine touchee porte EXACTEMENT les membres que le rejeu prevoit
  e := (select md5(coalesce(string_agg(x, ';' order by c), '')) from (
     select app_chaine_id c, app_chaine_id || ':' || string_agg(app_affaire_id::text, ',' order by app_affaire_id) x
       from public.app_affaire_ledger where app_chaine_id in (select c from a2_touchees) group by app_chaine_id) m);
  if e <> '1212c9d95f60294c94597da5c02fea35' then
    select string_agg(app_chaine_id || ' (' || count_ || ')', ', ') into d from (
      select app_chaine_id, count(*) count_ from public.app_affaire_ledger where app_chaine_id in (select c from a2_touchees)
       group by 1 order by 1) z;
    raise exception '⛔ G1 : les membres des 231 chaines touchees ne sont pas ceux du rejeu (empreinte % au lieu de 1212c9d95f60294c94597da5c02fea35) -- le chainage n''est pas arrive la ou on l''attendait. Chaines (membres) : %', e, d;
  end if;
  select count(*) into n from public.app_affaire_ledger where app_chaine_id in (select c from a2_touchees);
  if n <> 480 then raise exception '⛔ G1 : % membres au lieu de 480', n; end if;
  -- G2 : LES PARTS DE DEPART sont exactement celles lues a la fabrication ; les cibles sont vides
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id in (select c from a2_touchees));
  if e <> 'e09a38b9a381d71b0c85de525720ac38' then
    raise exception '⛔ G2 : les parts des chaines touchees ont change depuis la fabrication (empreinte % au lieu de e09a38b9a381d71b0c85de525720ac38)', e;
  end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (select c from a2_touchees);
  if n <> 272 then raise exception '⛔ G2 : % parts sur les chaines touchees au lieu de 272', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (select c from a2_cibles);
  if n <> 0 then raise exception '⛔ G2 : % part(s) deja sur les 97 cibles -- elles devaient etre vides', n; end if;
  -- G3 : les ventes reglees sans part, A L'ARRIVEE et avant A2 : exactement la liste prevue
  e := (select coalesce(string_agg(c::text, ',' order by c), '') from (
    select distinct l.app_chaine_id c from public.app_affaire_ledger l
     where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null
       and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) x);
  if e <> '118,126,1060,1161,2167,2211,2358,2634,3677,3720,4269,4278,4371,4481,4501,4509,4534,4561,4622,4650,4670,4707,4851,4909,6434,6555,7647,7700,7711,7720,8841,8857,9497,11146,11168,11413,11547,11655,11668,12012,12567,14148,14940,15061,16032,16144,16337,16364,16379,16842,17027,17132,17154,17289,17388,17423,17547,17913,19620,19691,19816,19863,20265,20795,21659,22270,23051,23413,23476,23994,24005,24124,24282,24382,24407,24444,24451,24500,24590,24599,24631,24650,25627,25840,25898,26029,26156,26604,26833,27656,27722,1000050,1000127' then
    raise exception '⛔ G3 : ventes reglees sans part a l''arrivee : [%] au lieu de [118,126,1060,1161,2167,2211,2358,2634,3677,3720,4269,4278,4371,4481,4501,4509,4534,4561,4622,4650,4670,4707,4851,4909,6434,6555,7647,7700,7711,7720,8841,8857,9497,11146,11168,11413,11547,11655,11668,12012,12567,14148,14940,15061,16032,16144,16337,16364,16379,16842,17027,17132,17154,17289,17388,17423,17547,17913,19620,19691,19816,19863,20265,20795,21659,22270,23051,23413,23476,23994,24005,24124,24282,24382,24407,24444,24451,24500,24590,24599,24631,24650,25627,25840,25898,26029,26156,26604,26833,27656,27722,1000050,1000127]', e;
  end if;
  raise notice '✅ gardes : membres % (480), parts % (272), cibles vides, ventes reglees sans part [118,126,1060,1161,2167,2211,2358,2634,3677,3720,4269,4278,4371,4481,4501,4509,4534,4561,4622,4650,4670,4707,4851,4909,6434,6555,7647,7700,7711,7720,8841,8857,9497,11146,11168,11413,11547,11655,11668,12012,12567,14148,14940,15061,16032,16144,16337,16364,16379,16842,17027,17132,17154,17289,17388,17423,17547,17913,19620,19691,19816,19863,20265,20795,21659,22270,23051,23413,23476,23994,24005,24124,24282,24382,24407,24444,24451,24500,24590,24599,24631,24650,25627,25840,25898,26029,26156,26604,26833,27656,27722,1000050,1000127]',
    '1212c9d95f60294c94597da5c02fea35', 'e09a38b9a381d71b0c85de525720ac38';
end $$;

-- ─── ② LA SAUVEGARDE DATEE : la table ENTIERE (une part n'est jamais supprimee, elle se retrouve) ─────────────────────
create table public.app_affaire_repartition_avant_a2vague_20261124 as select * from public.app_affaire_repartition;
revoke all on public.app_affaire_repartition_avant_a2vague_20261124 from public, anon, authenticated;

-- ─── ④ LE JOURNAL : chaque part, sa ligne d'origine, sa place de depart et d'arrivee, l'ancienne valeur ────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   lot_origine, pourquoi, ecrit_par)
select 'a2_vague_2026-11-24', row_number() over (order by k, s, cote, rang, piece), 'repartition',
       'app_affaire_repartition (' || cote || ', rang ' || rang || ')', geste, s, null, s, null, null,
       piece, vk, vch, vnum, valeur, ancienne, lignes, 'A2 v3 (passage 81, image 2026-11-24_175707)', pourquoi,
       'patch_a2_vague'
  from (
    select 1 k, p.s, r.cote, r.rang, p.piece, 'RECOPIER (A2 : la part suit sa ligne)' geste, v.kind vk,
           v.app_chaine_id vch, v.app_dossier_numero vnum,
           r.hektor_user_id || ' ' || coalesce(r.nom_au_moment, '') || ' ' || r.pourcentage || ' (' || coalesce(r.origine, '-') || ')' valeur,
           'copiee depuis la chaine ' || p.s || ' ; ecrit_par d''origine : ' || coalesce(r.ecrit_par, '-') ancienne, p.lignes,
           'SA REGLE 6 (24/11) : la part recopiee sur la bonne ligne devient la part vivante ; la vague a deplace '
             || p.lignes || ' de la chaine ' || p.s || ' vers la chaine de la piece ' || p.piece pourquoi
      from a2_paires p join public.app_affaire_repartition r on r.app_chaine_id = p.s
      left join public.app_affaire_ledger v on v.app_affaire_id = p.piece
    union all
    select 2, m.s, r.cote, r.rang, m.vers_piece, 'METTRE DE COTE (regle 6 : sa ligne est partie)', v.kind,
           v.app_chaine_id, v.app_dossier_numero, null,
           r.hektor_user_id || ' ' || coalesce(r.nom_au_moment, '') || ' ' || r.pourcentage || ' (' || coalesce(r.origine, '-')
             || ') ; ecrit_par ' || coalesce(r.ecrit_par, '-'), m.lignes,
           'SA REGLE 6 : une part n''est jamais supprimee, elle est mise de cote avec son ancien numero -- ' || m.motif
      from a2_mises m join public.app_affaire_repartition r on r.app_chaine_id = m.s
      left join public.app_affaire_ledger v on v.app_affaire_id = m.vers_piece
    union all
    select 3, 22979, 'sortie', 1, 22979, 'COMPLETER (NRZVKH85 : la part de sortie manquait)', v.kind,
           v.app_chaine_id, v.app_dossier_numero, '73 ' || 'Claudie FERNANDEZ' || ' 50 (classeur_reconstitue)', null,
           'NRZVKH85', 'A2 v3 : la chaine de NRZVKH85 porte son entree ; le classeur porte aussi la sortie -- completee, la part existante intacte'
      from public.app_affaire_ledger v where v.app_affaire_id = 22979
  ) j;

-- ─── ⑤ LE GESTE : les recopies (depuis les parts vivantes que G2 vient de prouver), PUIS les mises de cote ──────────────
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select v.app_chaine_id, v.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment, r.pourcentage, r.origine, now(),
       'a2_vague_2026-11-24:' || p.lignes
  from a2_paires p
  join public.app_affaire_repartition r on r.app_chaine_id = p.s
  join public.app_affaire_ledger v on v.app_affaire_id = p.piece;
insert into public.app_affaire_repartition_mise_de_cote
  (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment,
   pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select r.app_chaine_id, v.app_chaine_id, r.app_chaine_id, r.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
       r.pourcentage, r.origine, r.ecrit_le, r.ecrit_par, 'patch_a2_vague_2026-11-24',
       'A2 de la vague (regle 6) : ' || m.motif
  from a2_mises m
  join public.app_affaire_repartition r on r.app_chaine_id = m.s
  left join public.app_affaire_ledger v on v.app_affaire_id = m.vers_piece;
delete from public.app_affaire_repartition r using a2_mises m where r.app_chaine_id = m.s;
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select v.app_chaine_id, v.app_dossier_id, 'sortie', 1, '73', 'Claudie FERNANDEZ', 50, 'classeur_reconstitue', now(),
       'a2_vague_2026-11-24:NRZVKH85'
  from public.app_affaire_ledger v where v.app_affaire_id = 22979;

-- ─── ⑥ LES CONTROLES ───────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text; d text;
begin
  -- les membres n'ont pas bouge (A2 ne touche jamais une chaine)
  e := (select md5(coalesce(string_agg(x, ';' order by c), '')) from (
     select app_chaine_id c, app_chaine_id || ':' || string_agg(app_affaire_id::text, ',' order by app_affaire_id) x
       from public.app_affaire_ledger where app_chaine_id in (select c from a2_touchees) group by app_chaine_id) m);
  if e <> '1212c9d95f60294c94597da5c02fea35' then raise exception '⛔ controle : les membres ont bouge (%)', e; end if;
  -- conservation : apres = avant + recopiees - mises de cote + completee
  select count(*) into n from public.app_affaire_repartition;
  if n <> (select count(*) from public.app_affaire_repartition_avant_a2vague_20261124) + 57 then
    raise exception '⛔ controle : % parts au lieu de % + 199 - 143 + 1', n, (select count(*) from public.app_affaire_repartition_avant_a2vague_20261124);
  end if;
  -- chaque part recopiee est sur la chaine de sa piece, telle que sur sa chaine de depart (la sauvegarde le prouve)
  select count(*) into n from a2_paires p
    join public.app_affaire_repartition_avant_a2vague_20261124 s on s.app_chaine_id = p.s
    join public.app_affaire_ledger v on v.app_affaire_id = p.piece
    join public.app_affaire_repartition r on r.app_chaine_id = v.app_chaine_id and r.cote = s.cote and r.rang = s.rang
     and r.hektor_user_id = s.hektor_user_id and r.pourcentage = s.pourcentage and r.origine is not distinct from s.origine
     and r.nom_au_moment is not distinct from s.nom_au_moment and r.ecrit_par = 'a2_vague_2026-11-24:' || p.lignes;
  if n <> 199 then raise exception '⛔ controle : % part(s) recopiee(s) a leur place sur 199', n; end if;
  -- les cibles ne portent QUE les parts recopiees, et chaque chaine somme a 100 (entree + sortie, comme le controle de ④)
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (select c from a2_cibles);
  if n <> 199 then raise exception '⛔ controle : % part(s) sur les cibles au lieu de 199', n; end if;
  select string_agg(app_chaine_id || '/' || cote || '=' || s_, ', ') into d from (
    select app_chaine_id, 'total' cote, sum(pourcentage) s_ from public.app_affaire_repartition
     where app_chaine_id in (select c from a2_cibles union all select 22979) group by 1 having sum(pourcentage) <> 100) z;
  if d is not null then raise exception '⛔ controle : sommes differentes de 100 : %', d; end if;
  -- la regle 6 : chaque part mise de cote est ENTIERE (contre la sauvegarde), et sa chaine de depart est vide
  select count(*) into n from public.app_affaire_repartition_mise_de_cote m
    join public.app_affaire_repartition_avant_a2vague_20261124 s on s.app_chaine_id = m.ancien_app_chaine_id and s.cote = m.cote and s.rang = m.rang
     and s.hektor_user_id = m.hektor_user_id and s.pourcentage = m.pourcentage and s.origine is not distinct from m.origine
     and s.ecrit_le = m.ecrit_le and s.ecrit_par is not distinct from m.ecrit_par
     and s.nom_au_moment is not distinct from m.nom_au_moment and s.app_dossier_id is not distinct from m.app_dossier_id
   where m.mise_de_cote_par = 'patch_a2_vague_2026-11-24';
  if n <> 143 then raise exception '⛔ controle : % part(s) mise(s) de cote entiere(s) sur 143', n; end if;
  select count(*) into n from public.app_affaire_repartition r join a2_mises m on m.s = r.app_chaine_id;
  if n <> 0 then raise exception '⛔ controle : % part(s) encore sur les chaines mises de cote', n; end if;
  -- la completee : la chaine de NRZVKH85 porte ses deux cotes
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = 22979;
  if n <> 2 then raise exception '⛔ controle : la chaine 22979 porte % part(s) au lieu de 2', n; end if;
  -- ⭐ LA GARDE DU TEMPS 2 : plus AUCUNE vente reglee sans part a l'arrivee
  e := (select coalesce(string_agg(c::text, ',' order by c), '') from (
    select distinct l.app_chaine_id c from public.app_affaire_ledger l
     where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null
       and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) x);
  if e <> '' then raise exception '⛔ controle : ventes reglees sans part apres A2 : [%]', e; end if;
  -- le journal
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'a2_vague_2026-11-24' and ligne_origine is not null;
  if n <> 343 then raise exception '⛔ controle : % ligne(s) au journal (avec ligne d''origine) sur 343', n; end if;
  -- les parts qui ne sont pas du lot sont INTACTES (la sauvegarde, privee des chaines mises de cote)
  select count(*) into n from (
    (select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_a2vague_20261124 where app_chaine_id not in (select s from a2_mises)
     except all
     select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition)
  ) z;
  if n <> 0 then raise exception '⛔ controle : % part(s) hors du lot ont change', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition);
  if e <> 'c6978c4ff65ba1be81edfcb0ae11b499' then raise exception '⛔ controle : empreinte apres % au lieu de c6978c4ff65ba1be81edfcb0ae11b499', e; end if;
  raise notice '✅ A2 : 199 recopiees (97 paires), 143 mises de cote entieres (70 chaines), 1 completee, 0 vente reglee sans part, 343 lignes au journal ; empreinte apres %', e;
end $$;

commit;
