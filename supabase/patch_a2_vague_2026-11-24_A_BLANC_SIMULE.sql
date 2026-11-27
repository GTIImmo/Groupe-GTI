-- patch_a2_vague_2026-11-24_A_BLANC_SIMULE -- ⛔ N'ECRIT RIEN : la derniere instruction ANNULE toute la transaction (erreur voulue).
-- L'ETAT D'ARRIVEE SIMULE : les 798 pieces qui changent de chaine a la vague recoivent la chaine que le rejeu prevoit
-- (le numero de chaine n'a aucun declencheur : seuls acquereurs, mandants, contacts, notaires et presence en ont un).
begin;
do $$
declare n int; e text;
begin
  e := (select coalesce(string_agg(c::text, ',' order by c), '') from (
    select distinct l.app_chaine_id c from public.app_affaire_ledger l
     where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null
       and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) x);
  raise notice 'AVANT la simulation : ventes reglees sans part [%]', e;
end $$;
create temporary table a2_sim_avant on commit drop as
  select count(*) n_rep, md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) e_rep,
         (select count(*) from public.app_affaire_repartition_mise_de_cote) n_mdc,
         (select count(*) from public.app_classeur_realignement_journal) n_j
    from public.app_affaire_repartition;
update public.app_affaire_ledger l set app_chaine_id = v.c from (values
    (11, 10), (22, 22), (24, 22), (26, 26), (27, 21), (118, 118), (119, 118), (120, 117),
    (121, 118), (126, 126), (127, 126), (177, 177), (200, 200), (201, 200), (988, 987), (1060, 1060),
    (1061, 1061), (1062, 1060), (1063, 1060), (1103, 1101), (1104, 1104), (1161, 1161), (1162, 1161), (1163, 1160),
    (1164, 1161), (1229, 1229), (1231, 1229), (1258, 1258), (1266, 1266), (1268, 1266), (1335, 1335), (1336, 1334),
    (1337, 1335), (2167, 2167), (2168, 2167), (2170, 2167), (2211, 2211), (2212, 2211), (2213, 2210), (2214, 2211),
    (2358, 2358), (2359, 2358), (2360, 2358), (2451, 2451), (2507, 2507), (2509, 2507), (2533, 2533), (2535, 2533),
    (2634, 2634), (2635, 2634), (2637, 2634), (2642, 2642), (2643, 2642), (3588, 3588), (3647, 3647), (3650, 3647),
    (3670, 3670), (3671, 3670), (3672, 3670), (3677, 3677), (3678, 3677), (3679, 3677), (3720, 3720), (3721, 3720),
    (3722, 3719), (3723, 3720), (4128, 4126), (4132, 4132), (4135, 4132), (4178, 4178), (4179, 4179), (4181, 4179),
    (4182, 4178), (4197, 4197), (4268, 4268), (4269, 4269), (4270, 4269), (4271, 4267), (4272, 4268), (4273, 4269),
    (4278, 4278), (4279, 4277), (4280, 4278), (4281, 4278), (4289, 4289), (4290, 4289), (4329, 4329), (4330, 4329),
    (4353, 4353), (4371, 4371), (4372, 4370), (4373, 4371), (4374, 4371), (4388, 4385), (4481, 4481), (4482, 4481),
    (4483, 4483), (4484, 4480), (4485, 4481), (4501, 4501), (4502, 4501), (4504, 4501), (4509, 4509), (4510, 4510),
    (4511, 4510), (4512, 4509), (4514, 4509), (4534, 4534), (4535, 4534), (4537, 4534), (4542, 4542), (4545, 4542),
    (4561, 4561), (4562, 4561), (4564, 4561), (4596, 4596), (4598, 4596), (4622, 4622), (4624, 4622), (4626, 4622),
    (4650, 4650), (4651, 4651), (4652, 4650), (4653, 4649), (4654, 4654), (4655, 4651), (4656, 4650), (4661, 4661),
    (4663, 4661), (4670, 4670), (4671, 4670), (4673, 4670), (4707, 4707), (4709, 4707), (4710, 4707), (4746, 4746),
    (4748, 4746), (4771, 4771), (4773, 4771), (4797, 4797), (4800, 4797), (4851, 4851), (4853, 4851), (4854, 4851),
    (4858, 4858), (4860, 4858), (4907, 4906), (4909, 4909), (4911, 4909), (4912, 4909), (4932, 4931), (5055, 5054),
    (6157, 6157), (6341, 6341), (6434, 6434), (6435, 6434), (6437, 6434), (6555, 6555), (6556, 6555), (6557, 6557),
    (6559, 6555), (7115, 7115), (7117, 7115), (7294, 7294), (7296, 7294), (7449, 7449), (7450, 7450), (7452, 7450),
    (7453, 7453), (7546, 7546), (7547, 7546), (7580, 7580), (7582, 7580), (7600, 7599), (7605, 7605), (7606, 7605),
    (7610, 7610), (7611, 7610), (7646, 7646), (7647, 7647), (7648, 7647), (7649, 7646), (7651, 7647), (7700, 7700),
    (7701, 7700), (7703, 7700), (7711, 7711), (7713, 7711), (7714, 7711), (7720, 7720), (7721, 7720), (7723, 7720),
    (7768, 7768), (7769, 7768), (7779, 7779), (7780, 7778), (7781, 7779), (7904, 7903), (7943, 7943), (8017, 8017),
    (8018, 8017), (8019, 8016), (8841, 8841), (8842, 8841), (8843, 8841), (8857, 8857), (8858, 8857), (8860, 8857),
    (8868, 8868), (9497, 9497), (9498, 9497), (9499, 9496), (9500, 9497), (11146, 11146), (11147, 11146), (11148, 11146),
    (11168, 11168), (11169, 11168), (11171, 11168), (11182, 11182), (11184, 11182), (11188, 11188), (11205, 11205), (11206, 11205),
    (11356, 11356), (11358, 11356), (11374, 11374), (11376, 11374), (11413, 11413), (11414, 11412), (11415, 11413), (11416, 11413),
    (11501, 11501), (11516, 11516), (11518, 11516), (11547, 11547), (11549, 11547), (11550, 11547), (11558, 11558), (11579, 11579),
    (11581, 11579), (11655, 11655), (11656, 11655), (11657, 11654), (11658, 11655), (11668, 11668), (11669, 11668), (11671, 11668),
    (11709, 11709), (11710, 11709), (11711, 11708), (11712, 11709), (11729, 11729), (11731, 11729), (11791, 11791), (11793, 11791),
    (12012, 12012), (12014, 12012), (12017, 12012), (12179, 12179), (12567, 12567), (12568, 12567), (12570, 12567), (14008, 14007),
    (14034, 14034), (14035, 14034), (14036, 14034), (14052, 14052), (14110, 14110), (14111, 14111), (14112, 14109), (14113, 14111),
    (14131, 14131), (14132, 14131), (14142, 14141), (14143, 14143), (14148, 14148), (14149, 14148), (14152, 14148), (14172, 14172),
    (14225, 14225), (14517, 14517), (14519, 14517), (14810, 14810), (14816, 14816), (14817, 14813), (14913, 14913), (14915, 14913),
    (14928, 14927), (14940, 14940), (14941, 14941), (14942, 14940), (14943, 14939), (14944, 14940), (15005, 15005), (15060, 15059),
    (15061, 15061), (15062, 15061), (15096, 15096), (15097, 15096), (16017, 16017), (16032, 16032), (16033, 16032), (16035, 16032),
    (16114, 16114), (16116, 16114), (16144, 16144), (16145, 16144), (16146, 16144), (16337, 16337), (16338, 16337), (16340, 16337),
    (16342, 16342), (16343, 16343), (16344, 16342), (16364, 16364), (16378, 16378), (16379, 16379), (16380, 16378), (16381, 16379),
    (16384, 16379), (16838, 16838), (16842, 16842), (16843, 16841), (16844, 16842), (16845, 16842), (16870, 16870), (16871, 16870),
    (16879, 16878), (17027, 17027), (17132, 17132), (17133, 17133), (17134, 17132), (17135, 17133), (17137, 17132), (17154, 17154),
    (17155, 17154), (17158, 17154), (17206, 17203), (17209, 17209), (17211, 17209), (17289, 17289), (17290, 17288), (17292, 17289),
    (17293, 17289), (17301, 17301), (17303, 17301), (17321, 17321), (17322, 17320), (17323, 17321), (17366, 17366), (17388, 17388),
    (17389, 17389), (17390, 17387), (17391, 17388), (17410, 17410), (17411, 17411), (17423, 17423), (17424, 17423), (17426, 17423),
    (17429, 17427), (17431, 17431), (17433, 17433), (17434, 17434), (17435, 17432), (17436, 17436), (17437, 17434), (17525, 17525),
    (17526, 17525), (17542, 17542), (17544, 17542), (17547, 17547), (17548, 17547), (17550, 17547), (17651, 17651), (17652, 17651),
    (17913, 17913), (17914, 17913), (17916, 17913), (19070, 19070), (19071, 19069), (19072, 19070), (19074, 19074), (19076, 19074),
    (19095, 19095), (19097, 19095), (19104, 19104), (19105, 19104), (19132, 19132), (19142, 19142), (19456, 19456), (19512, 19512),
    (19576, 19576), (19578, 19576), (19612, 19612), (19614, 19612), (19620, 19620), (19621, 19620), (19622, 19619), (19623, 19620),
    (19657, 19657), (19659, 19657), (19665, 19665), (19666, 19665), (19691, 19691), (19692, 19691), (19694, 19690), (19695, 19691),
    (19712, 19711), (19737, 19737), (19739, 19737), (19815, 19815), (19816, 19816), (19817, 19816), (19818, 19815), (19819, 19814),
    (19820, 19814), (19821, 19816), (19830, 19830), (19863, 19863), (19864, 19863), (19866, 19863), (20073, 20073), (20075, 20073),
    (20089, 20089), (20247, 20247), (20265, 20265), (20266, 20265), (20267, 20264), (20268, 20268), (20269, 20265), (20277, 20277),
    (20279, 20277), (20301, 20301), (20303, 20301), (20309, 20309), (20311, 20309), (20408, 20408), (20410, 20408), (20492, 20492),
    (20494, 20492), (20513, 20513), (20673, 20673), (20749, 20749), (20785, 20785), (20786, 20785), (20795, 20795), (20796, 20795),
    (20798, 20795), (21585, 21585), (21586, 21585), (21598, 21598), (21600, 21598), (21616, 21616), (21618, 21616), (21659, 21659),
    (21660, 21659), (21662, 21659), (21799, 21798), (21947, 21947), (21948, 21946), (21949, 21947), (21965, 21965), (21966, 21965),
    (22008, 22008), (22010, 22008), (22018, 22018), (22019, 22018), (22024, 22024), (22086, 22086), (22087, 22087), (22089, 22087),
    (22090, 22086), (22209, 22209), (22256, 22256), (22257, 22256), (22270, 22270), (22271, 22270), (22273, 22270), (22981, 22979),
    (22982, 22982), (22983, 22979), (23051, 23051), (23052, 23051), (23053, 23050), (23054, 23054), (23055, 23051), (23057, 23057),
    (23058, 23057), (23335, 23335), (23413, 23413), (23414, 23413), (23415, 23412), (23416, 23413), (23426, 23426), (23476, 23476),
    (23478, 23476), (23994, 23994), (23995, 23994), (23997, 23994), (24005, 24005), (24006, 24005), (24007, 24005), (24011, 24011),
    (24012, 24011), (24013, 24011), (24108, 24108), (24110, 24108), (24123, 24122), (24124, 24124), (24125, 24124), (24159, 24157),
    (24160, 24157), (24282, 24282), (24284, 24282), (24285, 24282), (24311, 24311), (24320, 24320), (24321, 24321), (24322, 24320),
    (24331, 24331), (24333, 24331), (24381, 24380), (24382, 24382), (24383, 24382), (24401, 24401), (24407, 24407), (24408, 24407),
    (24409, 24406), (24410, 24407), (24412, 24412), (24414, 24412), (24444, 24444), (24445, 24443), (24446, 24444), (24447, 24444),
    (24451, 24451), (24452, 24451), (24453, 24450), (24455, 24451), (24495, 24495), (24497, 24495), (24500, 24500), (24501, 24500),
    (24502, 24499), (24503, 24500), (24512, 24512), (24514, 24512), (24564, 24564), (24566, 24564), (24573, 24573), (24590, 24590),
    (24591, 24591), (24592, 24590), (24599, 24599), (24600, 24600), (24601, 24600), (24602, 24599), (24603, 24598), (24604, 24599),
    (24610, 24610), (24631, 24631), (24633, 24631), (24650, 24650), (24651, 24650), (24654, 24650), (25627, 25627), (25628, 25627),
    (25629, 25627), (25840, 25840), (25841, 25840), (25842, 25840), (25877, 25877), (25879, 25877), (25890, 25890), (25898, 25898),
    (25899, 25898), (25901, 25898), (26016, 26016), (26024, 26024), (26025, 26024), (26026, 26023), (26028, 26028), (26029, 26029),
    (26030, 26027), (26031, 26028), (26032, 26029), (26034, 26034), (26036, 26034), (26043, 26043), (26072, 26072), (26074, 26072),
    (26155, 26155), (26156, 26156), (26157, 26156), (26158, 26155), (26159, 26154), (26160, 26156), (26189, 26188), (26190, 26190),
    (26604, 26604), (26605, 26605), (26607, 26605), (26608, 26604), (26609, 26604), (26615, 26615), (26833, 26833), (26835, 26833),
    (26884, 26884), (26885, 26884), (26886, 26884), (26890, 26884), (27101, 27101), (27134, 27134), (27135, 27135), (27137, 27133),
    (27138, 27134), (27139, 27135), (27140, 27140), (27240, 27240), (27241, 27240), (27427, 27427), (27448, 27445), (27449, 27449),
    (27484, 27484), (27486, 27484), (27513, 27513), (27555, 27555), (27556, 27556), (27560, 27560), (27609, 27609), (27656, 27656),
    (27657, 27656), (27659, 27656), (27661, 27661), (27662, 27661), (27679, 27679), (27681, 27679), (27687, 27687), (27722, 27722),
    (27723, 27722), (27725, 27722), (27807, 27807), (27809, 27807), (27823, 27823), (28146, 28146), (28179, 28179), (28180, 28179),
    (28181, 28179), (28269, 28269), (28271, 28269), (28547, 28547), (28548, 28547), (28802, 28801), (28832, 28831), (28833, 28833),
    (28931, 28930), (29003, 24124), (29004, 15061), (29005, 11598), (29006, 17388), (29007, 26029), (29009, 26833), (30762, 28547),
    (1000095, 1000095), (1000116, 1000116), (1000126, 1000126), (1000127, 1000127), (1000148, 1000116), (1000150, 1000127), (1000167, 1000095), (1000250, 1000050),
    (1000263, 1000127), (1001425, 28175), (1001426, 20247), (1001427, 21439), (1001428, 1911), (1001429, 30), (1001430, 6157), (1001431, 16788),
    (1001432, 15895), (1001433, 974), (1001434, 7068), (1001435, 14010), (1001436, 6363), (1001437, 24271), (1001438, 928), (1001439, 14084),
    (1001440, 28115), (1001441, 21462), (1001442, 6261), (1001443, 23893), (1001444, 7499), (1001445, 25626), (1001446, 25965), (1001447, 23794),
    (1001448, 2357), (1001449, 23162), (1001450, 16096), (1001452, 11110), (1001454, 8840), (1001455, 27101), (1001456, 8845), (1001458, 7422),
    (1001459, 27033), (1001460, 7067), (1001461, 3588), (1001462, 101), (1001463, 8839), (1001464, 958), (1001465, 11111), (1001466, 3627),
    (1001467, 7232), (1001468, 11501), (1001469, 15961), (1001470, 14083), (1001471, 27039), (1001472, 160), (1001473, 20305), (1001474, 25877),
    (1001475, 1000142), (1001476, 19456), (1001478, 16838), (1001479, 16329), (1001480, 20073), (1001481, 17567), (1001483, 16100), (1001484, 3628),
    (1001485, 21435), (1001486, 24004), (1001487, 23003), (1001488, 14032), (1001489, 7105), (1001490, 3629), (1001491, 11103), (1001492, 24135),
    (1001493, 997), (1001494, 24010), (1001495, 21520), (1001496, 11144), (1001497, 3669), (1001498, 28120), (1001499, 25709), (1001500, 25839),
    (1001501, 7048), (1001502, 19408), (1001503, 6290), (1001504, 28214), (1001505, 6103), (1001506, 25692), (1001507, 14037), (1001508, 6146),
    (1001509, 15901), (1001511, 22999), (1001512, 3689), (1001513, 21933), (1001514, 28178), (1001515, 28597), (1001516, 11145), (1001517, 28582),
    (1001518, 4195), (1001519, 28546), (1001521, 23983), (1001522, 20264), (1001523, 26), (1001524, 8918), (1001525, 8910), (1001526, 8926),
    (1001527, 17377), (1001528, 26070), (1001529, 14813), (1001530, 4370), (1001531, 4289), (1001532, 4480), (1001533, 24380), (1001534, 17427),
    (1001535, 11558), (1001536, 20073), (1001537, 17387), (1001538, 24450), (1001539, 1101), (1001541, 27445), (1001543, 7903), (1001544, 20227),
    (1001545, 28762), (1001546, 28857), (1001547, 28905), (1001548, 28908), (1001549, 28907), (1001550, 16223), (1001551, 3697), (1001552, 25710),
    (1001554, 1000316), (1001555, 30645), (1001561, 1001561), (1001568, 17027), (1001579, 20672), (1001593, 14007)) v(a, c)
 where l.app_affaire_id = v.a;
do $$
declare n int; e text;
begin
  e := (select coalesce(string_agg(c::text, ',' order by c), '') from (
    select distinct l.app_chaine_id c from public.app_affaire_ledger l
     where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null
       and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) x);
  raise notice 'ARRIVEE SIMULEE : ventes reglees sans part [%]', e;
end $$;

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
    (21, '7NI4WKV5', null, '7NI4WKV5 arrive sur la chaine 22, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 21 RESTE a l''arrivee (membres 21,27) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (117, 'P0YMQODU', 118, 'P0YMQODU quitte la chaine 117 -> recopiee sur la chaine de la piece 118 ; la chaine 117 RESTE a l''arrivee (membres 117,120) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (125, 'AOPBUAOJ', 126, 'AOPBUAOJ quitte la chaine 125 -> recopiee sur la chaine de la piece 126 ; la chaine 125 RESTE a l''arrivee (membres 125) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (1059, 'AHKQI7MX+YPNDHILU', 1060, 'AHKQI7MX+YPNDHILU quitte la chaine 1059 -> recopiee sur la chaine de la piece 1060 ; la chaine 1059 RESTE a l''arrivee (membres 1059) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (1103, '-', 1103, 'la chaine 1103 disparait (la piece 1103 rejoint 1101) -> les MEMES parts y vivent deja'),
    (3701, 'I847SPN3', 3699, 'I847SPN3 quitte la chaine 3701 -> recopiee sur la chaine de la piece 3699 ; la chaine 3701 RESTE a l''arrivee (membres 3701) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (4196, '5R6RC36Y', null, '5R6RC36Y arrive sur la chaine 4197, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 4196 RESTE a l''arrivee (membres 4196) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (4271, 'NSRISB3C', null, 'NSRISB3C arrive sur la chaine 4267, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (4272, '9FP3UICY', null, '9FP3UICY arrive sur la chaine 4268, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (4290, 'LKBO1TOH', null, 'LKBO1TOH arrive sur la chaine 4289, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (4370, 'TL9AFW0O', 4371, 'TL9AFW0O quitte la chaine 4370 -> recopiee sur la chaine de la piece 4371 ; la chaine 4370 RESTE a l''arrivee (membres 4370,4372,1001530) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (4372, 'FWCFAN6O', null, 'FWCFAN6O arrive sur la chaine 4370, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (4388, 'U0GQ3KTO', null, 'U0GQ3KTO arrive sur la chaine 4385, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; U0GQ3KTO EN RESERVE (8RWTD0YX, meme mandat 14065)'),
    (4484, '-', 4484, 'la chaine 4484 disparait (la piece 4484 rejoint 4480) -> les MEMES parts y vivent deja'),
    (4500, 'WPGZK930', 4501, 'WPGZK930 quitte la chaine 4500 -> recopiee sur la chaine de la piece 4501 ; la chaine 4500 RESTE a l''arrivee (membres 4500,4503) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (4533, 'FYNZEKI6', 4534, 'FYNZEKI6 quitte la chaine 4533 -> recopiee sur la chaine de la piece 4534 ; la chaine 4533 RESTE a l''arrivee (membres 4533,4536) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (4560, 'BNWNKPJH', 4561, 'BNWNKPJH quitte la chaine 4560 -> recopiee sur la chaine de la piece 4561 ; la chaine 4560 RESTE a l''arrivee (membres 4560,4563) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (4621, '910O0A2Q', 4622, '910O0A2Q quitte la chaine 4621 -> recopiee sur la chaine de la piece 4622 ; la chaine 4621 RESTE a l''arrivee (membres 4621,4625) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (4653, 'HHQZC2QP', null, 'HHQZC2QP arrive sur la chaine 4649, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (4655, 'N9J2533O', null, 'N9J2533O arrive sur la chaine 4651, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (4669, 'ZMQZSE9Q', 4670, 'ZMQZSE9Q quitte la chaine 4669 -> recopiee sur la chaine de la piece 4670 ; la chaine 4669 RESTE a l''arrivee (membres 4669,4672) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (4850, 'R9ANL92S', 4851, 'R9ANL92S quitte la chaine 4850 -> recopiee sur la chaine de la piece 4851 ; la chaine 4850 RESTE a l''arrivee (membres 4850,4852) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (6171, 'a5cb141f', 6172, 'a5cb141f quitte la chaine 6171 -> recopiee sur la chaine de la piece 6172 ; la chaine 6171 RESTE a l''arrivee (membres 6171) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (6433, '7BPVD7K4', 6434, '7BPVD7K4 quitte la chaine 6433 -> recopiee sur la chaine de la piece 6434 ; la chaine 6433 RESTE a l''arrivee (membres 6433,6436) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (7452, 'DN5U3GER', null, 'DN5U3GER arrive sur la chaine 7450, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (7606, 'R90OQT16', null, 'R90OQT16 arrive sur la chaine 7605, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (7645, 'D5KU9GNT', 7647, 'D5KU9GNT quitte la chaine 7645 -> recopiee sur la chaine de la piece 7647 ; la chaine 7645 RESTE a l''arrivee (membres 7645,7650) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (7904, 'UAER0F0F', null, 'UAER0F0F arrive sur la chaine 7903, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (8019, 'SXJDHXKF', 8019, 'la chaine 8019 disparait (la piece 8019 rejoint 8016) -> les MEMES parts y vivent deja'),
    (11560, '8NZ6V6XB', null, '8NZ6V6XB arrive sur la chaine 11558, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 11560 RESTE a l''arrivee (membres 11560) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (11581, 'ULFVA1AQ', null, 'ULFVA1AQ arrive sur la chaine 11579, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (12011, 'ANHQ1PK7', 12012, 'ANHQ1PK7 quitte la chaine 12011 -> recopiee sur la chaine de la piece 12012 ; la chaine 12011 RESTE a l''arrivee (membres 12011,12013,12016) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (12566, 'QL70KV8I', 12567, 'QL70KV8I quitte la chaine 12566 -> recopiee sur la chaine de la piece 12567 ; la chaine 12566 RESTE a l''arrivee (membres 12566,12569) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (14147, '5ELT15Q7', 14148, '5ELT15Q7 quitte la chaine 14147 -> recopiee sur la chaine de la piece 14148 ; la chaine 14147 RESTE a l''arrivee (membres 14147) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (14817, '-', 14817, 'la chaine 14817 disparait (la piece 14817 rejoint 14813) -> les MEMES parts y vivent deja'),
    (15004, 'MY2EIUFQ', null, 'MY2EIUFQ arrive sur la chaine 15005, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 15004 RESTE a l''arrivee (membres 15004) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (16143, 'KTZJRCR2', 16144, 'KTZJRCR2 quitte la chaine 16143 -> recopiee sur la chaine de la piece 16144 ; la chaine 16143 RESTE a l''arrivee (membres 16143) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (16869, 'CA2XNF38', null, 'CA2XNF38 arrive sur la chaine 16870, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 16869 RESTE a l''arrivee (membres 16869,16872) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (17136, 'ZV3QRSJG', null, 'ZV3QRSJG arrive sur la chaine 17131, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 17136 RESTE a l''arrivee (membres 17136) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (17153, 'A6OS2TTJ', 17154, 'A6OS2TTJ quitte la chaine 17153 -> recopiee sur la chaine de la piece 17154 ; la chaine 17153 RESTE a l''arrivee (membres 17153,17156,17157) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (17390, '-', 17390, 'la chaine 17390 disparait (la piece 17390 rejoint 17387) -> les MEMES parts y vivent deja'),
    (17429, '-', 17429, 'la chaine 17429 disparait (la piece 17429 rejoint 17427) -> les MEMES parts y vivent deja'),
    (17546, 'V5NJER40', 17547, 'V5NJER40 quitte la chaine 17546 -> recopiee sur la chaine de la piece 17547 ; la chaine 17546 RESTE a l''arrivee (membres 17546,17549) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (17912, '9JCIQYZX', 17913, '9JCIQYZX quitte la chaine 17912 -> recopiee sur la chaine de la piece 17913 ; la chaine 17912 RESTE a l''arrivee (membres 17912,17915) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (19818, 'R7NU9NPM', null, 'R7NU9NPM arrive sur la chaine 19815, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (19862, 'JBCC1KBT', 19863, 'JBCC1KBT quitte la chaine 19862 -> recopiee sur la chaine de la piece 19863 ; la chaine 19862 RESTE a l''arrivee (membres 19862,19865) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (20075, '-', 20073, 'la chaine disparait, sans ligne : quitte la chaine 20075 -> recopiee sur la chaine de la piece 20073'),
    (20267, '-', 20267, 'la chaine 20267 disparait (la piece 20267 rejoint 20264) -> les MEMES parts y vivent deja'),
    (20794, 'MFMR0U6A', 20795, 'MFMR0U6A quitte la chaine 20794 -> recopiee sur la chaine de la piece 20795 ; la chaine 20794 RESTE a l''arrivee (membres 20794,20797) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (21658, '8BJKJ6XP', 21659, '8BJKJ6XP quitte la chaine 21658 -> recopiee sur la chaine de la piece 21659 ; la chaine 21658 RESTE a l''arrivee (membres 21658) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (22269, 'WG8CG5T2', 22270, 'WG8CG5T2 quitte la chaine 22269 -> recopiee sur la chaine de la piece 22270 ; la chaine 22269 RESTE a l''arrivee (membres 22269,22272) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (22980, 'NRZVKH85', 22979, 'NRZVKH85 quitte la chaine 22980 pour 22979 (qui portait son entree) -> completee de sa sortie ; la chaine 22980 RESTE a l''arrivee (membres 22980) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (23053, '-', 23053, 'la chaine 23053 disparait (la piece 23053 rejoint 23050) -> les MEMES parts y vivent deja'),
    (23412, 'PB3ASE0N', 23413, 'PB3ASE0N quitte la chaine 23412 -> recopiee sur la chaine de la piece 23413 ; la chaine 23412 RESTE a l''arrivee (membres 23412,23415) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (24333, 'N8M7RKTN', null, 'N8M7RKTN arrive sur la chaine 24331, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (24381, '-', 24381, 'la chaine 24381 disparait (la piece 24381 rejoint 24380) -> les MEMES parts y vivent deja'),
    (24453, '-', 24453, 'la chaine 24453 disparait (la piece 24453 rejoint 24450) -> les MEMES parts y vivent deja'),
    (24588, 'XH5KZ9LI', 24590, 'XH5KZ9LI quitte la chaine 24588 -> recopiee sur la chaine de la piece 24590 ; la chaine 24588 RESTE a l''arrivee (membres 24588) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (24630, '50LQ2VSA', 24631, '50LQ2VSA quitte la chaine 24630 -> recopiee sur la chaine de la piece 24631 ; la chaine 24630 RESTE a l''arrivee (membres 24630,24632) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (24649, 'ESVJUR12', 24650, 'ESVJUR12 quitte la chaine 24649 -> recopiee sur la chaine de la piece 24650 ; la chaine 24649 RESTE a l''arrivee (membres 24649) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (26013, '7MOMHHQ1', null, '7MOMHHQ1 arrive sur la chaine 26016, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 26013 RESTE a l''arrivee (membres 26013) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (26026, 'I0K9TUCT', null, 'I0K9TUCT arrive sur la chaine 26023, une ANNULEE (son 3e mot : aucune part) -> aucune recopie'),
    (26832, 'II80B5HW', 26833, 'II80B5HW quitte la chaine 26832 -> recopiee sur la chaine de la piece 26833 ; la chaine 26832 RESTE a l''arrivee (membres 26832) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (27136, 'IEYXREWQ', null, 'IEYXREWQ arrive sur la chaine 27134, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 27136 RESTE a l''arrivee (membres 27136,27141) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (27448, '-', 27448, 'la chaine 27448 disparait (la piece 27448 rejoint 27445) -> les MEMES parts y vivent deja'),
    (27512, '1D7EIYKW', null, '1D7EIYKW arrive sur la chaine 27513, une ANNULEE (son 3e mot : aucune part) -> aucune recopie ; la chaine 27512 RESTE a l''arrivee (membres 27512) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (27721, 'SA7DWYEZ', 27722, 'SA7DWYEZ quitte la chaine 27721 -> recopiee sur la chaine de la piece 27722 ; la chaine 27721 RESTE a l''arrivee (membres 27721,27724) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
    (28568, '959b7669', 28569, '959b7669 quitte la chaine 28568 -> recopiee sur la chaine de la piece 28569 ; la chaine 28568 RESTE a l''arrivee (membres 28568) SANS LIGNE NI PART -- NOMMEE (son mot du 24/11 : aucune vente reglee, on n''y touche pas)'),
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
  -- ✅ LES 42 CHAINES NOMMEES (son mot du 24/11) : elles restent a l'arrivee SANS LIGNE NI PART, et AUCUNE ne
  --    porte de vente reglee -- on n'y touche pas, et on le prouve
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (21, 117, 125, 1059, 3701, 4196, 4370, 4500, 4533, 4560, 4621, 4669, 4850, 6171, 6433, 7645, 11560, 12011, 12566, 14147, 15004, 16143, 16869, 17136, 17153, 17546, 17912, 19862, 20794, 21658, 22269, 22980, 23412, 24588, 24630, 24649, 26013, 26832, 27136, 27512, 27721, 28568);
  if n <> 0 then raise exception '⛔ controle : % part(s) sur les 42 chaines nommees', n; end if;
  select count(*) into n from public.app_affaire_ledger where app_chaine_id in (21, 117, 125, 1059, 3701, 4196, 4370, 4500, 4533, 4560, 4621, 4669, 4850, 6171, 6433, 7645, 11560, 12011, 12566, 14147, 15004, 16143, 16869, 17136, 17153, 17546, 17912, 19862, 20794, 21658, 22269, 22980, 23412, 24588, 24630, 24649, 26013, 26832, 27136, 27512, 27721, 28568)
     and kind = 'vente' and coalesce(vente_reglee_app, '') <> '';
  if n <> 0 then raise exception '⛔ controle : % vente(s) reglee(s) sur les 42 chaines nommees', n; end if;
  -- ⭐ LES ORPHELINES (l'alerte data.repartition_orpheline, 26 depuis le 21/11 : 13 dossiers du rapatriement du 13/11 que
  --    la vague fait RENAITRE, et les chaines qui disparaissent a la vague, mises de cote ci-dessus) : apres A2, AUCUNE
  --    part sur une chaine qui ne porte aucune piece (son mot du 25/11 : « ce rouge doit tomber a 0 ce soir »)
  select count(*), coalesce(string_agg(distinct r.app_chaine_id::text, ','), '') into n, d
    from public.app_affaire_repartition r
   where not exists (select 1 from public.app_affaire_ledger l where l.app_chaine_id = r.app_chaine_id);
  if n <> 0 then raise exception '⛔ controle : % part(s) orpheline(s) apres A2 (chaines %)', n, d; end if;
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
  null;
  raise notice '✅ A2 : 199 recopiees (97 paires), 143 mises de cote entieres (70 chaines), 1 completee, 0 vente reglee sans part, 343 lignes au journal ; empreinte apres %', e;
end $$;

create temporary table a2_sim_milieu on commit drop as
  select count(*) n_rep, md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) e_rep, (select coalesce(string_agg(c::text, ',' order by c), '') from (
    select distinct l.app_chaine_id c from public.app_affaire_ledger l
     where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null
       and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) x) vr_apres,
         (select count(*) from public.app_affaire_repartition_mise_de_cote) n_mdc,
         (select count(*) from public.app_classeur_realignement_journal) n_j
    from public.app_affaire_repartition;

-- ─── LE RETOUR ARRIERE : les parts du lot retirees, les mises de cote remises EN PLACE, le journal du lot retire ─────
do $$
declare n int;
begin
  if to_regclass('public.app_affaire_repartition_avant_a2vague_20261124') is null then raise exception '⛔ inverse : la sauvegarde app_affaire_repartition_avant_a2vague_20261124 est absente'; end if;
  select count(*) into n from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_a2_vague_2026-11-24';
  if n <> 143 then raise exception '⛔ inverse : % mise(s) de cote du lot au lieu de 143', n; end if;
end $$;
delete from public.app_affaire_repartition where ecrit_par like 'a2_vague_2026-11-24:%';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select ancien_app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_a2_vague_2026-11-24';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_a2_vague_2026-11-24';
delete from public.app_classeur_realignement_journal where lot = 'a2_vague_2026-11-24';
do $$
declare n int;
begin
  -- la table est revenue EXACTEMENT a la sauvegarde, dans les deux sens
  select count(*) into n from (
    (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_a2vague_20261124
     except all
     select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition)
    union all
    (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition
     except all
     select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_a2vague_20261124)) z;
  if n <> 0 then raise exception '⛔ inverse : % part(s) differente(s) de la sauvegarde', n; end if;
  raise notice '✅ inverse : la repartition est revenue a la sauvegarde, la mise de cote et le journal du lot sont vides';
end $$;

do $$
declare a record; m record; n_rep int; e_rep text; n_mdc int; n_j int; vr text;
begin
  select * into a from a2_sim_avant;
  select * into m from a2_sim_milieu;
  select count(*), md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) into n_rep, e_rep from public.app_affaire_repartition;
  select count(*) into n_mdc from public.app_affaire_repartition_mise_de_cote;
  select count(*) into n_j from public.app_classeur_realignement_journal;
  if n_rep <> a.n_rep or e_rep <> a.e_rep or n_mdc <> a.n_mdc or n_j <> a.n_j then
    raise exception '⛔ A BLANC : l''inverse n''a pas tout rendu (parts % / %, empreinte % / %, mise de cote % / %, journal % / %)',
      n_rep, a.n_rep, e_rep, a.e_rep, n_mdc, a.n_mdc, n_j, a.n_j;
  end if;
  vr := (select coalesce(string_agg(c::text, ',' order by c), '') from (
    select distinct l.app_chaine_id c from public.app_affaire_ledger l
     where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null
       and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) x);
  raise exception 'A BLANC SIMULE VERT -- RIEN N''EST ECRIT (annulation voulue). Avant : % parts (%), mise de cote %, journal %. Apres A2 : % parts, empreinte apres % , ventes reglees sans part [%], mise de cote %, journal %. Apres l''inverse : % parts (%), mise de cote %, journal % = avant. Ventes reglees sans part a l''arrivee simulee, AVANT A2 : [%]',
    a.n_rep, left(a.e_rep, 8), a.n_mdc, a.n_j, m.n_rep, m.e_rep, m.vr_apres, m.n_mdc, m.n_j, n_rep, left(e_rep, 8), n_mdc, n_j, vr;
end $$;
