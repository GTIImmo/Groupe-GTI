-- vague_du_soir_2026-11-25_A_BLANC_COMPLET -- genere par phase2/checks/vague_a_blanc_complet.py
-- ⛔ N'ECRIT RIEN : la derniere instruction ANNULE toute la transaction (erreur voulue). AUCUN commit dans ce fichier.
-- Les chaines de la vague (798 pieces), la VRAIE pose des etiquettes, A2, A1, A3, leurs controles, leurs inverses.
begin;
create temporary table vab_avant on commit drop as select
  (select count(*) from public.app_affaire_repartition) n_rep, (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition) e_rep,
  (select count(*) from public.app_affaire_repartition_mise_de_cote) n_mdc,
  (select count(*) from public.app_classeur_realignement_journal) n_j,
  (select md5(coalesce(string_agg(concat_ws('|', id_unique, app_dossier_uuid, app_dossier_numero), ';' order by id_unique), '')) from public.app_classeur_avis) e_av, (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id), ';' order by app_affaire_id), '')) from public.app_affaire_note) e_no,
  (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, rang, app_chaine_id), ';' order by app_affaire_id, rang), '')) from public.app_affaire_condition) e_co,
  (select count(*) from public.app_affaire_note n join public.app_affaire_ledger l on l.app_affaire_id = n.app_affaire_id where n.app_chaine_id is distinct from l.app_chaine_id) no_faux, (select count(*) from public.app_affaire_condition c join public.app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id where c.app_chaine_id is distinct from l.app_chaine_id) co_faux, (select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l where l.app_chaine_id = r.app_chaine_id)) orph, (select coalesce(string_agg(c::text, ',' order by c), '') from (
    select distinct l.app_chaine_id c from public.app_affaire_ledger l
     where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null
       and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) x) vr,
  (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id, app_dossier_uuid, app_dossier_numero), ';'
           order by app_affaire_id), '')) from public.app_affaire_ledger) e_lab,
  (select md5(coalesce(string_agg(concat_ws('|', annee, dernier), ';' order by annee), '')) from public.app_dossier_numero_compteur) e_cpt;

-- ─── 1. LES CHAINES DE LA VAGUE ───────────────────────────────────────────────────────────────────────────────────
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
-- ─── 2. LA VRAIE POSE DES ETIQUETTES (celle que la poussee appelle) ───────────────────────────────────────────────
create temporary table vab_pose on commit drop as select * from public.app_poser_etiquettes_dossier();
create temporary table vab_vague on commit drop as select
  (select count(*) from public.app_affaire_repartition) n_rep, (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition) e_rep,
  (select count(*) from public.app_affaire_repartition_mise_de_cote) n_mdc,
  (select count(*) from public.app_classeur_realignement_journal) n_j,
  (select md5(coalesce(string_agg(concat_ws('|', id_unique, app_dossier_uuid, app_dossier_numero), ';' order by id_unique), '')) from public.app_classeur_avis) e_av, (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id), ';' order by app_affaire_id), '')) from public.app_affaire_note) e_no,
  (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, rang, app_chaine_id), ';' order by app_affaire_id, rang), '')) from public.app_affaire_condition) e_co,
  (select count(*) from public.app_affaire_note n join public.app_affaire_ledger l on l.app_affaire_id = n.app_affaire_id where n.app_chaine_id is distinct from l.app_chaine_id) no_faux, (select count(*) from public.app_affaire_condition c join public.app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id where c.app_chaine_id is distinct from l.app_chaine_id) co_faux, (select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l where l.app_chaine_id = r.app_chaine_id)) orph, (select coalesce(string_agg(c::text, ',' order by c), '') from (
    select distinct l.app_chaine_id c from public.app_affaire_ledger l
     where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null
       and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) x) vr,
  (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id, app_dossier_uuid, app_dossier_numero), ';'
           order by app_affaire_id), '')) from public.app_affaire_ledger) e_lab,
  (select md5(coalesce(string_agg(concat_ws('|', annee, dernier), ';' order by annee), '')) from public.app_dossier_numero_compteur) e_cpt;

-- ─── 4. A2, A1, A3 ────────────────────────────────────────────────────────────────────────────────────────────────

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
  if to_regclass('public.app_affaire_repartition_avant_a2vague_20261125') is not null then
    raise exception '⛔ G0 : la sauvegarde app_affaire_repartition_avant_a2vague_20261125 existe deja -- ce patch ne se rejoue pas';
  end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'a2_vague_2026-11-25';
  if n <> 0 then raise exception '⛔ G0 : % ligne(s) du lot a2_vague_2026-11-25 deja au journal', n; end if;
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
create table public.app_affaire_repartition_avant_a2vague_20261125 as select * from public.app_affaire_repartition;
revoke all on public.app_affaire_repartition_avant_a2vague_20261125 from public, anon, authenticated;

-- ─── ④ LE JOURNAL : chaque part, sa ligne d'origine, sa place de depart et d'arrivee, l'ancienne valeur ────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   lot_origine, pourquoi, ecrit_par)
select 'a2_vague_2026-11-25', row_number() over (order by k, s, cote, rang, piece), 'repartition',
       'app_affaire_repartition (' || cote || ', rang ' || rang || ')', geste, s, null, s, null, null,
       piece, vk, vch, vnum, valeur, ancienne, lignes, 'A2 v3 (passage 82, image 2026-11-25_072625)', pourquoi,
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
       'a2_vague_2026-11-25:' || p.lignes
  from a2_paires p
  join public.app_affaire_repartition r on r.app_chaine_id = p.s
  join public.app_affaire_ledger v on v.app_affaire_id = p.piece;
insert into public.app_affaire_repartition_mise_de_cote
  (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment,
   pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select r.app_chaine_id, v.app_chaine_id, r.app_chaine_id, r.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
       r.pourcentage, r.origine, r.ecrit_le, r.ecrit_par, 'patch_a2_vague_2026-11-25',
       'A2 de la vague (regle 6) : ' || m.motif
  from a2_mises m
  join public.app_affaire_repartition r on r.app_chaine_id = m.s
  left join public.app_affaire_ledger v on v.app_affaire_id = m.vers_piece;
delete from public.app_affaire_repartition r using a2_mises m where r.app_chaine_id = m.s;
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select v.app_chaine_id, v.app_dossier_id, 'sortie', 1, '73', 'Claudie FERNANDEZ', 50, 'classeur_reconstitue', now(),
       'a2_vague_2026-11-25:NRZVKH85'
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
  if n <> (select count(*) from public.app_affaire_repartition_avant_a2vague_20261125) + 57 then
    raise exception '⛔ controle : % parts au lieu de % + 199 - 143 + 1', n, (select count(*) from public.app_affaire_repartition_avant_a2vague_20261125);
  end if;
  -- chaque part recopiee est sur la chaine de sa piece, telle que sur sa chaine de depart (la sauvegarde le prouve)
  select count(*) into n from a2_paires p
    join public.app_affaire_repartition_avant_a2vague_20261125 s on s.app_chaine_id = p.s
    join public.app_affaire_ledger v on v.app_affaire_id = p.piece
    join public.app_affaire_repartition r on r.app_chaine_id = v.app_chaine_id and r.cote = s.cote and r.rang = s.rang
     and r.hektor_user_id = s.hektor_user_id and r.pourcentage = s.pourcentage and r.origine is not distinct from s.origine
     and r.nom_au_moment is not distinct from s.nom_au_moment and r.ecrit_par = 'a2_vague_2026-11-25:' || p.lignes;
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
    join public.app_affaire_repartition_avant_a2vague_20261125 s on s.app_chaine_id = m.ancien_app_chaine_id and s.cote = m.cote and s.rang = m.rang
     and s.hektor_user_id = m.hektor_user_id and s.pourcentage = m.pourcentage and s.origine is not distinct from m.origine
     and s.ecrit_le = m.ecrit_le and s.ecrit_par is not distinct from m.ecrit_par
     and s.nom_au_moment is not distinct from m.nom_au_moment and s.app_dossier_id is not distinct from m.app_dossier_id
   where m.mise_de_cote_par = 'patch_a2_vague_2026-11-25';
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
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'a2_vague_2026-11-25' and ligne_origine is not null;
  if n <> 343 then raise exception '⛔ controle : % ligne(s) au journal (avec ligne d''origine) sur 343', n; end if;
  -- les parts qui ne sont pas du lot sont INTACTES (la sauvegarde, privee des chaines mises de cote)
  select count(*) into n from (
    (select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_a2vague_20261125 where app_chaine_id not in (select s from a2_mises)
     except all
     select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition)
  ) z;
  if n <> 0 then raise exception '⛔ controle : % part(s) hors du lot ont change', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition);
  null;
  raise notice '✅ A2 : 199 recopiees (97 paires), 143 mises de cote entieres (70 chaines), 1 completee, 0 vente reglee sans part, 343 lignes au journal ; empreinte apres %', e;
end $$;


-- ═══ A1 : LE REFLET DES AVIS (app_classeur_avis), PAR PIECES -- lot a1_vague_2026-11-25 ═══════════════════════════════════
do $$
declare n int; e text;
begin
  if to_regclass('public.app_classeur_avis_reflets_avant_a1vague_20261125') is not null then
    raise exception '⛔ A1 G0 : la sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'a1_vague_2026-11-25';
  if n <> 0 then raise exception '⛔ A1 G0 : % ligne(s) du lot deja au journal', n; end if;
  select count(*), md5(coalesce(string_agg(concat_ws('|', id_unique, app_dossier_uuid, app_dossier_numero), ';' order by id_unique), '')) into n, e from public.app_classeur_avis;
  if n <> 2588 or e <> 'bd1c64166733d05072388144a40a22ea' then
    raise exception '⛔ A1 G1 : les avis ont change depuis la fabrication (% lignes, empreinte % au lieu de 2588, bd1c64166733d05072388144a40a22ea)', n, e;
  end if;
end $$;
-- LA LISTE « ligne -> ses vraies pieces » (le jugement du protocole), une seule fois
create temporary table a1_m (x text) on commit drop;
insert into a1_m select unnest(string_to_array('009c70c1:28784,28785,28786;00edc3c1:21491,21492,21493;00f1ad41:30690,30745;0108T49T:24306,24307,24308;0176b44e:28798,28800;01I7TZTF:19496,19497,19498;01SK2H67:7717,7718;01YWCL74:16202,16203,16204;0268440f:25689,25690,25691;029DGJZ1:25894,25895,25896;029Y7HH5:2594,2595,2596;02D98HM6:16229,16230,16231;02Q7GAMQ:28132,28133;02d74ec7:19999,20000,20001;02ed033a:25675,25676,25677;03BAPZFZ:24365,24366,24367;043047f7:28740,28741,28742;045ecde7:28557,28559,28560;0477ef1d:28879,28880,28946;04R9MOFV:7236,7237,7238;057f78c7:28643;067766b8:11129,11130,11131;06DV4H5E:22106,22109,22110;06J8UABI:23213,23214,23215;06b51bd6:17121,17122,17123;06b9e256:15851,15852,15853;07104c22:28682,28683,28684;0719d67e:30646,30681;07H13UWE:1577,1578,1579;07HHTU3I:3852,3853;07cec9e1:27345,27346;084VMGMQ:11399,11401;088MHDC0:6107,6108,6109;08GV8OMZ:6340,6342;08f0df46:28940,28983;095aae70:28938,28939,30686;0BCCAFRS:15919,15920,15921;0BM4UFWS:22993,22994;0BQ0EW4J:21982,21983,21984;0CXSF0NW:20273,20274,20275;0D43U0CB:19781,19782,19783;0D81Q0LO:7638,7639,7640;0DB7SP3Q:27077,27078,27079;0DEMPT05:15012,15013,15014;0EAT2Q0H:21499,21500,21501;0EGUOSHB:6496,6497,6498;0ETUT8ZN:19800,19801,19802;0F0IX00S:1947,1948,1949;0FFZI3NF:26254,26255,26256;0G326ZDG:12095,12096,12097;0GV2LNV2:4745,4747,4749;0HG85UKB:25729,25730,25731;0HOARO39:22134,22135,22136;0IIWDD9V:19728,19729;0IW4ZBYL:21995,21996,21997;0J3PO6EL:22128,22129,22130;0K6ZJ7BS:10045,10046,10047;0K8OCBEH:23047,23048,23049;0KNWQYSJ:22186,22187,22188;0M1I4028:24303,24304,24305;0NCCXW95:9432,9433,9434;0ND00J6E:21953,21954,21955;0NE1IL93:22056,22057,22058;0ODZTGMI:7440,7441,7442;0OI5KSEB:26059,26060;0OOBEXCX:11537,11538,11539;0ORGPGDV:21959,21960,21961;0OUV0YIY:7496,7497,7498;0QODF0LV:25975,25976,25978;0SK7XFK9:16058,16059,16060;0SO49QWE:7732,7733,7734;0W7D9P8T:16286,16287,16288;0WGGZ5S6:20415,20416,20417;0WWIS23S:17268,17269,17270;0X4QMLOL:27245,27246,27248;0XL8HMKN:6539,6540,6541;0YMUMZ69:11387,11388,11389;0Z6ILHFG:1930,1931,1932;0ZHOJG6W:9463,9464,9465;0ZTPUE4C:9873,9874,9875;0ab75a63:25596,25597,25598;0adab219:21539,21540,21541;0bae20da:28669,29012;0bc98552:21804,21806,30674;0be40a45:28916,28918,28992;0c0d4fd6:28867,28868,30683;0c3629d5:25713,25714;0c9f89ce:28854,28856;0d208379:28708,28709,28710;0d5701c2:28872,28873,28950;0d6cad26:3695,3696;0ef0fb5f:7069,7070;0f322ed1:6122,6123,6124;10XQQ0JQ:4243,4244,4245;112cddef:28666,28668;11478642:28734,28735,30717;11FWA9JU:4,5,6;11YC16DL:15994,15995,15996;1239NIDA:4174,4175,4176;125888d3:23984,23985,23986;12HYUR5Q:17348,17349,17350;12XGFHHI:9995,9996,9997;12ZJW8IG:4431,4433;12a4bf9f:28627,28629;12cbf83a:1000064,1000130,1000247;1305bd20:28771,28772,28773;138a2f16:14047,14048;13d5eab6:21451,21452,21453;142abca6:28942,1000322;144V0WIY:949,950,951;14853166:4200,4202;14K7Y459:24247,24248;14dcf146:28583,28585,28943;1524db30:7,8,9;153aff70:28598,28599,28600;155a437c:19409,19410;15763448:28933,28934,30704;15F5T9OA:209,210,211;161EC3F4:17867,17868,17869;1649864f:16815,16816;16DYZQR4:220,221,222;16a85b1d:28674,28675,28676;174XZYI1:6160,6161,6162;17PGLT7K:25882,25883,25884;17S58J78:14091,14092,14093;18cb1251:971,972,973;18f3d501:19399,19400,19401;19288566:8885,8886,8887;1A8WNLLX:19060,19061,19062;1AYSC1AW:92,93,94;1AYUGDUM:21575,21576,21577;1AZS9HQA:19083,19084,19085;1BACT1XD:9396,9397,9398;1BKO0G50:10034,10035,10036;1C9DZI2B:9973,9974,9975;1CDRP7NF:7696,7697,7698;1CM5I5IE:9867,9868,9869;1CZTJQZB:25660,25661,25662;1DJGWHDJ:7642,7643,7644;1DJIEGDX:14997,14998,14999;1DJNVHJN:27399,27400,27401;1DTXI9RV:9448,9449,9450;1DVXUI6C:20029,20030,20031;1E06KUDX:16176,16177,16178;1EJAH885:20433,20434,20435;1F6LUQGR:14965,14967,14970;1F7YRMFE:4324,4325,4326;1GE3834K:16416,16417,16418;1H9UNJIV:24082,24083,24084;1HE1JOE6:277,278,279;1HWOICZ2:20175,20176,20177;1I0QFFIX:4575,4576,4577;1I5IF1R0:24032,24033,24034;1IBNHTTQ:24272,24273,24274;1IKZFR4O:8870,8871,8872;1J0A8V69:16307,16308,16309;1KYEKHED:134,135,136;1LLBSCX3:27309,27310,27311;1LLD7D54:11444,11445,11446;1LPEXQHF:26128,26129,26130;1MC9CP0P:4404,4405,4406;1N7UY3LR:7789,7790,7791;1OW8IQ2M:241,242,243;1P3YGT8O:7752,7753,7754;1QJA9DBN:9290,9292;1RCW869L:6475,6476,6477;1RHINB9O:7775,7776,7777;1T19A55V:6348,6349,6350;1TH5OEUJ:24661,24662,24663;1TI9SIL4:6463,6464,6465;1TZEGF2D:26604,26608,26609;1UAEV86Q:4753,4754,4755;1UZOB4I6:266,267,268;1VOKJVLP:83,84,85;1W2O0DSU:28341,28342;1WFEKQ7Y:24101,24102,24103;1XIOPRMU:24257,24258,24259;1Y4OWDQZ:2520,2521,2522;1Y8NUTDC:19675,19676,19677;1ZFH9RJ8:27464,27465,27466;1ZRXIC6J:16319,16320,16321;1ZSEDIN0:9853,9854,9855;1a8fddc4:28217,28218,28219;1aab2b81:19035,19036,19037;1c7b38f9:21521,21522,21523;1cc703d9:14007,14008,14009;1cdb03cf:7099,7100,7101;1cf326f1:8882,8884;1d5cfc36:28848,28849,28850;1daaa899:6173,6174;1e212af4:28903,28904,1000311;1e9a3bb3:28949,29027;1efa579f:21502,21503,21504;1f7cee20:20046,20047,20048;200WAIW0:1024,1025,1026;205f62be:14034,14035,14036;20H67EQL:17271,17272,17273;20TYFXVT:10072,10073,10074;218dab2c:3673,3674,3675;21ABEL0K:2409,2410,2411;21f6e095:23003;22814536:28607,28608,28948;228CJLMV:11603,11604,11605;22ff7a0a:28541,28542,30654;238d801e:2198,2199,2200;23a2a8e1:28928,28929,30737;23bb9818:15887,15888,15889;23cdc9cf:28774,28775,28776;24OLTZ2Y:16277,16278,16279;25TVZHM6:6448,6449,6451;25ZCM7J9:11534,11535,11536;261a38cc:28601,28602,28603;265fd510:7090,7091,7092;267ba75c:21463,21464,28960;26HNGR8Z:11569,11570,11571;26RPMNTJ:7601,7602,7603;26b32d8a:28648,28998;26d67848:2361,2362,2363;273RLJDU:23894,23895,23896;2740db19:25672,25673,25674;279b98c5:9856,9857,9858;27BPA8UZ:16857,16859,16860;28EIQBRN:7229,7230,7231;28XY2GSB:4527,4528,4529;28a264a6:28758,28760;29277933:21513,21514;2962d089:21518,21519;29YBUBYA:11655,11656,11658;29b1da92:19043,19044,19045;2BBUE8TV:257,261,265;2BS2IIKF:11681,11682,11683;2BSOAYOR:16009,16010,16011;2BTI2Q2M:1953,1954,1955;2CIS1JB7:9444,9445,9446;2CWKADAS:16289,16290,16291;2DUPM26R:6157;2DWP0520:7573,7574,7575;2EEY4M3S:24560,24561,24562;2EPBUXAJ:27500,27501,27502;2ETX5Q7I:21494,21496;2EX8MDJW:7604,7607,7608;2F64CSTW:2784,2785,2786;2FMFX5PS:19716,19717,19718;2GS9PIHU:4208,4209,4210;2H961YH5:20014,20015,20016;2ID4OKM7:25623,25624,25625;2J66W3DT:58,59,60;2KPVMT72:7527,7528,7529;2KRN14IO:26045,26046,26047;2KYM13D9:2582,2583,2584;2LEM6124:4246,4247,4248;2LX682K2:6401,6402,6403;2NKNZLJ4:214,215,216;2NTTF0TG:2514,2515,2516;2OLJ4K0B:22115,22116,22118;2PBOPY2L:28247,28248,28249;2PZ3WQHV:78,79,80;2QG1OS74:27024,27025,27026;2QKBWT0U:22246,22247,22248;2SCBZXMH:7778,7780,7782;2SEHLUX1:2412,2413,2414;2SH3WZVW:1936,1937,1938;2W5BJEJA:26610,26611,26612;2Y2TYMT9:9414,9415,9416;2Y8GQ4NZ:27365,27366,27367;2YR078LL:23497,23498,23499;2YWBWVJI:24353,24354,24355;2c7f8c57:11140,11142,11143;2d77f8cb:9332,9333,30739;2ffd65ec:28796,28797,30761;303Q0SC7:24232,24233,24234;305KAY9W:24125,29003;306641a4:28685,28686;309ca5f6:16809,16810,16811;30AHMXB2:2224,2225,2226;30KAEJNA:23227,23228,23229;31a899b0:11849,11850,11851;3250892d:25700,25701,25702;33023764:14029,14030,14031;3308P0UX:4483;33255600:28671,28672,28673;33593a3c:15885,15886,30697;33O2BWCL:4294,4295,4296;34JO2UUN:19611,19613,19615;34TO46L2:27211,27212,27213;34ef22af:30680,30746;357775b2:23007,23008,23009;35AHHGR6:23889,23890,23891;35IL2CBM:25590,25592;35J32PVF:6518,6519,6520;35ORKPUF:1888,1889,1890;35QP4LXL:9426,9427,9428;36bffefc:20225,20226,30774;3768cfcb:28711,28712,28713;37SIHFKA:2489,2491,2492;38BJ3BSJ:1583,1584;38EF19KY:2751,2752,2753;38f13b81:28737,28739;39466db7:1000313;39IBNQ34:1168,1169,1170;39T628OY:4464,4465,4466;3A2EL02E:7609,7612,7613;3AQIWID7:20160,20161,20162;3ASFZ7XJ:4521,4522,4523;3B4CEGF9:20748,20750,20752;3BAWUIHV:25611,25612,25613;3C2V114G:4359,4360,4361;3CFL52U1:9329,9330,9331;3CZPP1A2:17021,17022,17023;3DL786FO:27278,27279,27281;3E8RWOWP:20480,20481,20482;3F73CQJ6:17199,17200,17201;3F7VC13S:6300,6301,6302;3FCDF7WB:271,272,273;3FFJJWZ9:22073,22074,22075;3G7EANJ6:24275,24276,24277;3GNX3MGS:23224,23225,23226;3HFNC732:6612,6613,6614;3HHV4V95:19493,19494,19495;3IB0HTMD:17314,17315,17316;3JBKDAK2:14011,14012,14013;3JCD1J0M:21969,21970,21971;3L7JRWLZ:22236,22237,22238;3LFJUQ5J:6345,6346,6347;3LN6Y8PH:27270,27271,27272;3M0AC95F:4223,4224,4225;3NXRT2XL:7632,7633,7634;3NZV32LJ:22260,22261,22262;3ON4OG5A:8833,8834,8835;3QOTL68Y:14023,14024,14025;3RAOD92E:17240,17241,17242;3S9846F1:25599,25601;3SU08SS4:20368,20369,20370;3TLH0CNW:176,179,180;3WN15OU4:2435,2436,2437;3X3UPF1Q:4509,4512,4514;3XNKL94C:7268,7269,7270;3XXMBS29:4606,4607,4608;3YLUOAXP:2424,2425,2426;3aa01998:3591,3592,3593;3b5db3cc:28777,29019,30812;3bc00e81:28788,28790;3be04102:28888,28889,29028;3bfa4f49:28824,28826;3c6f7684:15892,15893,15894;3c81b824:14825,14826,14827;3cc4b9fe:15882,15883,15884;3cf3ef37:28845,28846,28847;3d4a1902:21515,21516,21517;3db7a773:28639,28640,28641;3ec39fae:28223,28224,28225;3f86df48:6382,6383;40CFJ3RL:9337,9338,9339;40RP5B9C:11642,11643,11644;40bcdff6:21533,21534,21535;4182DD44:4582,4583,4584;41VWYV3R:2418,2419,2420;41a41a7a:3686,3687,3688;4205088d:24484,24485;42369b1f:28886,28887,30664;42QQG82N:21605;430C57QM:14841,14842,14843;433OQXSS:2573,2574,2575;4371R2HG:11520,11521,11522;43OASNAI:20377,20378,20379;43UTWUQD:19396,19397,19398;4441ce38:20055,20056,20057;44a4c19f:28556,1000003;454L4JKL:15861,15862,15863;45545ae2:19566,19568;45GMIDHA:12041,12042,12043;45HPZ3WU:11572,11573,11574;45T9KQVX:27172,27173,27174;45VS5K1P:16039,16040,16041;45b4a499:24278,24279,24280;45d36afd:11135,11136,11137;45fa3495:27009,27010,27011;469e2b24:7084,7085,7086;46b0a92c:25840,25841,25842;4713d9c3:28822,28823,30718;47474dda:19046,19047,19048;47Q455FG:23460,23461,23462;47R8E7CL:16025,16026,16027;486IQ51K:19580,19581,19582;487433bc:28805,28806,28807;48GPS1HM:4259,4260,4261;48f565f0:28573,28574,28575;495433c8:28925,28926,30651;49XISYV3:11554,11555,11556;4AC7NNBT:6367,6368,6369;4B5QW193:27252,27253,27254;4DHDQ4HV:22041,22042,22043;4G1EJWCK:21934,21935,21936;4HFL7JVA:6407,6408,6409;4HKBYFHE:23421,23422,23423;4HWJL63R:2364,2365,2366;4I4D4L23:9187,9188,9189;4IBBBGXA:1021,1022,1023;4IUU8985:17282,17283,17284;4K3XL013:1927,1928,1929;4KLGP3F7:22065,22066,22067;4MAH1NSU:2480,2481,2482;4MIPE9QM:17374,17375,17376;4MMN2HGK:7119,7120,7121;4NP9HV92:14931,14933;4O60KJCU:26084,26085,26086;4P3NDLAC:7592,7593,7594;4PI2Z7X7:52,53,54;4PPF07IF:1072,1073,1074;4QLLKE26:27870,27871,27872;4SB5VJWK:7567,7568,7569;4TR4Z6VT:27506,27507,27508;4U1PJXC3:7515,7516,7517;4U2U4D1K:1879,1880,1881;4UFUQRZG:5296,5297,5298;4UI3SAYB:4398,4399,4400;4V1DM3IC:24471,24472,24473;4VV3H0MY:20313,20314,20315;4WNFQ6MP:17578,17579,17580;4WPT577T:19449,19450,19451;4WR8WXK2:26955,26956,26957;4Z13GX9T:4305,4306,4307;4ZOVTD3G:2564,2565,2566;4ZZBZNXO:11426,11428;4aefa9ae:28976,30668;4bb1cda4:3680,3681,3682;4df5b515:20052,20053,20054;4efd0283:946,947,948;4fbf66ae:16800,16801,16802;50G3GV2U:22207,22208,22211;510YKN3L:17132,17134,17137;512f903b:929,930;52b073c5:23806,23807,23808;52e59e36:28755,28756,28757;532d70be:7049,7050,7051;53474VBI:9356,9357,9358;53LOM73O:24488,24489;53T2QCFH:28265,28266,28267;541LYAON:2221,2222,2223;5470e7ed:28645,28646,28647;547bad32:28935,30682;5494P9OV:16341,16345,16346;55OCP1ZW:25633,25634,25635;55f5b770:20163,20164,20165;566d1a48:987,988;56LKI7YY:26053,26054,26055;56d8eba3:16779,16780,16781;5719BR56:98,99,100;576ea0b9:28623,28624,30653;57DUTP1Q:21572,21573,21574;57J67ZK5:20515,20516,20517;58047368:1000107,1000143,1000258;5828VPJR:11659,11660,11661;583c2fdc:7187,7188,7189;58FB0P8N:27393,27394,27395;58I5AO17:7908,7909,7910;58e46fe7:28861,28862,30777;591418b3:28205,28206;59GBKFQ3:24035,24036,24037;59OFXNKX:64,65,66;5B8X6LY3:17244,17245,17246;5BJG4CLW:20699,20700,20701;5BKINDRJ:2615,2616,2617;5CIL9RER:19641,19642,19643;5CQU38JE:9466,9467,9468;5DW1C6Q1:7284,7285,7286;5DYD65NB:1000056,1000254;5EG908G9:24185,24186,24187;5F42BD4G:20336,20337,20338;5FBXXILM:15049,15050,15052;5FTT9SP4:6472,6473,6474;5GZVT548:17320,17322,17324;5H4OZC3Q:21482,21483,21484;5H96YY2I:25684,25685;5HW2BQ09:25739,25740,25741;5HZT3LHZ:7281,7282,7283;5IF4RDCL:232,233,234;5IMC8F4X:27532,27534,27535;5JLNBOVZ:20385,20386,20387;5JUPA6VS:6133,6134,6135;5L7GSXEB:3587,3589,3590;5LUGIH2H:14094,14095,14096;5NAOUTP0:27080,27083,27084;5OLUP6QS:6372,6373,6374;5OP12VPW:26078,26079,26080;5Q2BQQU4:17300,17302,17304;5Q3YGH60:157,158,159;5QOHD0CJ:16259,16260,16261;5SPO8UO2:4595,4597,4599;5U0W56XB:6765,6766,6767;5U86CXZ5:17311,17312,17313;5UD45RH7:20130,20131,20132;5UFURT61:1959,1960,1961;5VC1NO4O:1069,1070,1071;5VV5SP9N:25866,25868,25869;5VZDGQC3:15061,15062,29004;5WFSNMI1:24085,24086,24087;5WI74A7W:15009,15010,15011;5WJHFD8I:24038,24039,24040;5WPO57HP:21470,21471,21472;5XWBF7OE:17208,17210,17212;5Y2CWM3N:27446,27447,27450;5YL8ZOZB:2612,2613,2614;5YUGE9KA:11132,11133,11134;5ZW6RWW0:2609,2610,2611;5a717f6c:6181,28990,30730;5a742dff:24324,24326;5a91e2f5:7093,7094,7095;5ad1ea2f:26621,26622,26623;5af640fa:14004,14005,30698;5b5c8c66:28691,28692,28693;5cb8c234:28620,28621,28622;5de0be9c:20049,20050,20051;5e112aba:11104,11105,11106;5e145a14:2207,2208,2209;5e92dd1f:28791,28792,28793;5f46d641:24235,24236,24237;5f47de79:28179,28180,28181;5f4cf5c5:28764;5fc7eeb0:28895,28896,29033;606d68e9:23395,23396,30696;6095c819:28809,28811,28812;60b3f02e:28564,28565,28566;61639PNV:2597,2598,2599;61FHI22S:9542,9543,9544;61K16K4C:24516,24517,24518;63CYGF2U:17250,17251,17252;63K32NM9:9393,9394,9395;63b1e2fd:15896,15897,30783;63db99cb:28657,28658,28659;64K6KWZF:6271,6272,6273;650e65c8:21531,21532;6541SIMN:6370,6371;65bd4e73:955,956,957;67c7a802:46,47,48;684TO14K:14929,14930;68A4KM66:1000068,1000140,1000257;68Q076CV:19744,19745,19747;69TG10RL:6404,6405,6406;69d23176:978,979,980;6AU5VX4X:7233,7234,7235;6CBWVCW3:280,281,282;6CF7XT5Z:7668,7669,7670;6CG28M7D:2567,2568,2569;6DYSOEAD:4367,4368,4369;6EEWK8E3:25654,25655,25656;6FBMFO6U:19026,19027,19028;6FMNGNAA:28253,28254;6FQO29C8:19131,19133;6G5DJA9H:17416,17417,17418;6GHVY80Q:17005,17006,17007;6GX26LI1:20328,20329,20330;6HIW70JT:14985,14986,14987;6HUT0ETQ:11408,11409,11410;6I1D9N3O:16160,16161,16162;6ILZ6XFX:20023,20024,20025;6IPCFPMB:6533,6534,6535;6IY3VVUQ:27236,27237,27238;6J0AU3KS:23343,23344,23345;6JKPVWX1:27156,27158,27160;6K4ITA4T:15848,15849,15850;6K9IZIPV:940,941,942;6MJMLTHV:11525,11526,11527;6P5EM9HL:23406,23407,23408;6QDR3G7V:17720,17721,17722;6QR3M5JY:26965,26966,26968;6R6123OM:2468,2469,2470;6R6ZR3G2:1593,1594,1595;6RQHYD7U:11531,11532,11533;6RULQ2NJ:10066,10067,10068;6TJIOKEA:20250,20251,20252;6UEAD904:15083,15085;6VBX4YLW:7963,7964,7966;6VGXJUT5:19127,19128,19129;6WFAZ9ZC:16232,16233,16234;6XETN9PH:17551,17552,17553;6XWFYK3S:14994,14995,14996;6YKUO62M:17717,17718,17719;6Z098I23:20436,20437,20438;6ZE75DBW:20457,20458,20459;6a320ab0:20044,20045,28994;6ad818c7:4226,4227,30752;6afb6571:3683,3684,3685;6b02c91a:19038,19039;6d229f85:25707,25708;6db2801c:3666,3667,3668;6e1e24ce:28837,28954,30760;6e8be87a:28743,28744,28745;6f879518:28235,28236,28237;705bbb13:28230,28231,28232;706b952c:28781,28782,28783;7149ZIW4:17632,17633,17634;717OUUED:11595,11597,11599;71VPG6PX:21869,21870,21871;72314U7K:27187,27188,27189;727SM4SV:14974,14976;72CTZS1C:6501,6502,6503;72GQRHVB:6391,6392,6393;73APAMTV:24224,24225,24226;742MDGIX:19647,19648,19649;74854124:28649,28650,30719;74IL9C8F:23487,23489;74RNZPZ3:27467,27468,27469;74T2MR9V:2446,2447,2448;74d04bf0:28968,30738;754V9Q3A:24300,24301,24302;7567cd82:28906,29016;75EZY5GJ:16806,16807,16808;76666160:28901,28902,28963;7672fc36:28876,28877,28878;76EAHTFL:16854,16855,16856;76f7cbe0:19013,19014;776fd52e:25696,25697,25698;77VVY2X6:27483,27485,27487;77e6f1fc:21527,21528;78004641:8851,8852,30778;785ea663:20058,20059,20060;78PCLN4Q:223,224,225;78bb247a:30663,30727,30833;795O8VCL:86,87,88;79AD7HMD:16244,16245,16246;79ID9955:19108,19109,19110;7AUWSQ63:2189,2190,2191;7AVDC9G2:9353,9354,9355;7B1AAM6X:4518,4519,4520;7B38TY8F:1097,1099;7BPVD7K4:6434,6435,6437;7BZZY4CE:16875,16876,16877;7C0OT6KG:7614,7615,7616;7C50AGYF:26961,26962,26963;7CDXOG0U:19786,19787,19788;7D1IO8FG:3657,3658,3659;7DPTFY6Z:27457,27458,27459;7EHO53K6:15074,15075,15076;7F59H0TI:19022,19023,19024;7G2I4DSK:1939,1940,1941;7GF5I159:16179,16180,16181;7IGKO9VS:23990,23991,23992;7IGSK8JH:17466,17468;7IHI7YTJ:4234,4235,4236;7ITH92WI:19656,19658,19660;7J5QV6HQ:2496,2497,2498;7JND4065:26096,26097,26098;7JOXVZ23:7253,7254,7255;7K2HFNGG:7244,7245,7246;7KCYCV86:4474,4475,4476;7KKK0TSO:16199,16200,16201;7M4U001G:28290,28291,28293;7M74BYEP:23221,23222,23223;7MADXZ2Y:16122,16123,16124;7MTCHRAP:2486,2487,2488;7NC58WP2:22001,22002,22003;7P1JJ2PP:24407,24408,24410;7PUU8PAI:19111;7QTXLPBL:16499,16500,16501;7QUMMSWV:21578,21579,21580;7SC6W1KU:15924,15926;7TXZXESY:24411,24413,24415;7VXZOP18:4454,4455,4456;7W7XUBPO:2160,2161;7WC4GUJR:23424,23425,23427;7WHU1DT4:9454,9455,9456;7YASOEY0:19593,19594,19595;7YV7IETX:24041,24042,24043;7ZD2MYD0:2709,2710,2711;7ZGTJYOT:16205,16206,16207;7ZLPXI6S:21940,21941,21942;7ZNUC8G4:1165,1166,1167;7ZX6MPPQ:7550,7551,7552;7a334e36:28617,28618,28619;7bebbb6c:25843,25845;7c4c9b43:931,932,933;7c7b5d8e:1009,1010;7c85c150:28971,29017,30772;7d246e2a:28696,28697;7d3d223f:28604,28605,28606;7d77ed61:28851,28852,28853;7df5b3c8:991,992,993;7e1dded4:21529,21530;7e363d94:25703,30660;7f7c8e48:7078,7079;7fadb312:28174,28176,28177;807EP75U:20020,20022;807RWEKX:27415,27416,27417;80MEFC10:24091,24092,24093;80Y4THPR:2406,2407,2408;80c3a047:28923,28924,30693;80c94a1b:23010,23011,23012;811NQQY7:19032,19033,19034;81HHBRQ1:17381,17382,17383;81LLHEM6:25898,25899,25901;82C59OXD:21479,21480,21481;82TBULHC:28306,28307,28308;82UHN3YU:15927,15928,15929;83199885:3663,3664,3665;83N9H47O:21800,21801,21802;83e01cf8:2201,2202,2203;83f61b89:7435,7436,7437;84331d2b:6179,6180;84c4d260:28705,28706,28707;84c91bb8:28233,28234,30835;85FUBH2D:21881,21882,21883;861af493:28134,28135;8620da41:28893,28894,30733;867206a1:28586,28587,28588;867f573c:6156,6158,6159;86EGQN3Y:19636;86R3QN24:2603,2604,2605;86a190de:25969,25970;86ad8c0f:3670,3671,3672;87AO8TGY:16084,16085,16086;87eb399e:999,1001,1002;87f9cb03:28829,28830,30716;8845ae2e:25711,25712,28961;88C905M6:26958,26959,26960;88PMHJRA:22085,22088,22091;88dcff6d:21919,21920,30751;890INIAL:19016,19017,19018;89cbcce9:15890,15891;8A6MTXR1:23349,23350,23351;8AE0CAKN:20109,20110,20111;8BHJO7BJ:10069,10070,10071;8C9DZZC4:2177,2178,2179;8DCNS3RG:173,174,175;8DN9BT3W:184,185,186;8E46TMRW:9891,9892,9893;8EH5BG4P:4415,4416,4417;8EOXZX9M:27046,27047,27048;8EPPP1IZ:16274,16275,16276;8EZC7U40:24316,24317,24318;8F2JYZ35:7553,7554,7555;8FVDV6VI:17279,17280,17281;8FXDZW12:4386,4390,4391;8H6NY8DA:27362,27363,27364;8H7ILBFJ:16097,16098,16099;8HAY4TVG:24208,24209,24210;8HYCN8TR:24260,24261,24262;8I79G718:7942,7944,7945;8IPEBC52:17253,17254,17255;8LN5K98E:11175,11176,11177;8M0HWPWL:17469,17470,17471;8N3EMC5I:1616,1617,1618;8NAKFE09:26992,26993,26994;8NLAKLBU:7275,7276,7277;8O7W1KRD:20511,20512,20514;8OYWI0VJ:28106,28107,28108;8P7VVQFX:20648,20649,20650;8PJ1N21V:27037,27038;8PNOJVSF:27436,27438;8PV3YF82:6478,6479,6480;8QWJCY5J:1056,1057,1058;8R27QL3E:19599,19600,19601;8RTOI6J0:17256,17257,17258;8SN9K77U:19124,19125,19126;8T62BDRS:27297,27298,27299;8TW4PGGP:24132,24133,24134;8UPNWS5I:19405,19406,19407;8XJNSYHA:4220,4221,4222;8YQDITBF:24387,24388,24389;8Z6HYWFP:14845,14846,14848;8ZK6BS4N:4457,4458,4459;8ZVLH4R3:4334,4335;8a6ed45e:28543,28544,28545;8ce0f58c:22976,22977,22978;8cf0e171:26598,26599;8d182b8e:14900,14901,14902;8d503c61:11152,11153,11154;8d9fae75:28766,28767;8f3a4326:14050,28991,30847;90384R13:22026,22027,22028;90582b26:25704,25705,25706;90MYWCBT:27368,27369,27370;90bbdd0f:6100,6101,6102;90e99ae5:30743;910O0A2Q:4622,4624,4626;912HFZLL:11370,11371,11372;91AQ72B8:19490,19491,19492;91XDUTRE:17297,17298,17299;91ZZXE12:17438,17440,17442;91a8e31a:28911,28912,30677;92286015:25657,25658,25659;924EUVMF:27396,27397,27398;92CSXXLX:23941,23942,23943;92N9831F:1081,1082,1083;93584IPG:9475,9476,9477;93A3J0VI:14836,14839,14840;93ae35b3:2195,2196,2197;93c35494:28719,28720,28721;93e2cfb6:28589,28590,29029;9428014f:28552,28553,28554;94XV0YU2:16093,16094,16095;94a61c2f:28813,28814,28815;952JCAL2:7673,7674,7675;959AJX8B:9293,9294,9295;959b7669:28569;95WH4KUS:28197,28198,28199;964bdbbd:28932,28978;96E9XLK6:25749,25750,25751;96b196c9:28870,28871,30678;97092f0e:3855,3856,3857;978V88C7:24465,24467;97H944ZA:1113,1114,1115;97PU74R3:2570,2571,2572;97SQ9BOF:3621,3622,3623;98N5YM26:26223,26224,26225;99FDOQIW:27264,27265,27266;99LCZHML:27124,27125,27126;9A0HZ07P:2379,2380,2381;9ANFLEHR:9303,9304,9305;9AVWDF9S:23452,23453,23454;9BHGMU2G:24115,24116,24117;9C5FXNQI:1000106,1000144,1000259;9CQ325R6:24157,24158,24159,24160,24161;9CYQ9PQX:6385,6386,6387;9DME4QXD:2618,2619,2620;9EX1PC4K:1541,1542,1543;9FLP7L7T:2471,2472,2473;9FO6F3TN:6354,6355,6356;9G4ZZN02:17398,17399,17400;9IGUHUR6:1900,1901,1902;9JQSS8G2:6575,6576,6577;9JV9ZJA2:3578,3579,3580;9K4Y3S4N:21598,21600;9KPP6QFM:2239,2240,2241;9L3GE4JE:19653,19654,19655;9LDOQR90:4868,4869,4871;9LHNTO9R:4349,4350;9MHDONFP:25732,25733,25734;9MPPVXIJ:21432,21433,21434;9MT0M0TS:6197,6199;9NIW1DW7:11509,11510,11511;9ODGGXPB:2397,2398,2399;9OEBWAYN:2174,2175,2176;9P6YZ926:1116,1117,1118;9Q0FHAKK:;9Q9C7V3F:20656,20657,20658;9QD533ZY:2373,2375;9ROFAWKX:21423,21424,21425;9RS4YRJV:4489,4490,4491;9S0EP8FN:27147,27148,27149;9S4HJP9G:6637,6638,6639;9SPHK3ZP:19465,19467,19469;9SY0ND20:5038,5039,5040;9SZ9NT7F:11600,11601,11602;9U14DPXK:105,106,107;9UBGWC8I:11575,11576,11577;9ULQ7QQN:4282,4283,4284;9V4UEKS1:12073,12074,12075;9VETV09S:3724,3725,3726;9W3RJP5Z:4428,4429,4430;9X3KFS4Q:21591,21592,21593;9XOETXTS:23346,23347,23348;9YMO87QS:24056,24057,24058;9ZBS2W4M:1585,1586;9a09e537:28117,28119;9a0fd939:27291,27292,27293;9af5657f:28778,28779,28780;9ba77ae1:21510,21511,21512;9bd8f1e7:25669,25670,25671;9c9d164c:28883,28884,30748;9cdf7d5f:28914,28915;9d99fd80:26624,26625,26626;A07EC3DH:1875,1876,1878;A07X16EX:27442,27443,27444;A0QIPC9F:23437,23438,23439;A0TC6ADU:4217,4218,4219;A29BL1XX:4228,4229,4230;A2LO2EFH:3730,3731,3732;A2UA8RFR:7045,7046,7047;A393O1VF:20400,20401,20402;A3F85X1I:1000077,1000163,1000274;A3IXOFIH:27409,27410,27411;A4AC9VPV:4579,4580,4581;A4MEB5W8:21972,21973,21974;A58BLZGW:24029,24030,24031;A6L1NKL9:16217,16218,16219;A6VBL896:27375,27376,27377;A7W44V4B:24079,24080,24081;A8AU5HH8:26090,26091,26092;A8LNQDOQ:19511,19513,19514;A94E7E0K:8857,8858,8860;A99V9USP:24170,24171,24172;A9C5F3L1:2576,2577,2578;A9URFMZ2:10010,10012,10013;A9WP0B93:7509,7510,7511;ABCW0V5Z:16081,16082,16083;AC6B1EYZ:25743,25744,25745;ACB4D8WI:4328,4332,4333;ACITRM9X:11769,11770,11771;AD6G01S6:19134,19135,19136;AD6SMTR5:24330,24332,24334;AD70RCU2:1278,1279,1280;ADTCO6I0:14917,14918,14919;AE80P2TI:20445,20446,20447;AE8NQXIM:24104,24105,24106;AEHA8CD7:16247,16248,16250;AEKDQX2V:17419,17421;AFVACLQV:4956,4957,4958;AGAT3Q18:8836,8837,8838;AGF1K88A:17658,17659,17660;AH2GGUC5:6351,6352,6353;AH5BJAIP:16125,16126,16127;AIV9UI0I:16337,16338,16340;AJFQ4QIG:283,284,285;AJHNGUGJ:24139,24140,24141;AK9WMIEB:16238,16239,16240;AKAW0OUQ:17128,17129,17130;AKHX3TCV:31,32,33;AKREV339:2218,2219,2220;ALAB69XM:17259,17260,17261;ALRS1BW3:1871,1872,1873;AM1B13UH:20035,20036,20037;AMKJIRYN:16310,16311;AN4BWR9Q:14934,14937,14938;ANQDAQW4:11693,11694,11695;ANS54O77:238,239,240;ANV9HNA3:7133,7134,7135;AO8JF1M3:22038,22039,22040;AOEJIBRU:23469,23470,23471;AOPBUAOJ:126,127;APLQJVJN:11645,11646,11647;APTTKSTT:27180,27181,27182;APZBHCME:22227,22228,22229;ARJ4Y9LM:6200;ARODI4YG:15022,15023,15024;AUV4TI69:1174,1175,1176;AUZDT6B7:19632,19633,19634;AVFUZAEJ:4467,4468,4469;AX0D3TOT:2627,2628,2629;AXGN70RT:3630,3632,3633;AY0PMLHP:6524,6525,6526;AYIHPHF5:14109,14112,14115;AYQ5SMMS:23056,23059,23060;AZ18U3JY:19705,19706,19707;B16X241B:7783,7784,7785;B2HB5LDC:23998,23999,24000;B33WWDW5:24070,24071,24072;B3C2CB1T:28109,28110,28111;B3C8PQGH:19713,19714,19715;B42TJP7E:7518,7519,7520;B4WLVJEL:1000078,1000135,1000252;B5HZ3OV5:16267,16268;B5VKBMW0:16262,16263;B68QSKTS:24293,24294,24295;B7S1TVUB:11636,11637,11638;B8UXUHU4:3581,3583;B948G554:16003,16004,16005;B96G8ECQ:170,171,172;BA9A0Q81:16394,16395,16396;BAGJC6MS:10006,10007,10008;BB2OWPW9:6441,6442,6443;BC08X5LY:17228,17229,17230;BC254AOX:11904,11905,11906;BC40IDWM:7918,7919,7920;BC90JB94:20352,20353,20355;BC9OKKVF:17274,17275,17276;BCSZ6SL5:23397,23398,23399;BCT398F3:15053,15054,15055;BD7M1JGH:4425,4426,4427;BD7ZWASQ:2421,2422,2423;BETUXDEN:24451,24452,24455;BF4FP5ZP:14820,14821,14822;BF5RIBMY:4963,4964,4965;BFCRN1QB:16028,16029,16030;BG6Q9NIE:19508,19509,19510;BGTL0M31:217,218,219;BKP5DA2J:19644,19645,19646;BKX6G4YK:12083,12084,12085;BLKP7JFQ:7720,7721,7723;BNEBDGH1:24468,24469,24470;BNWNKPJH:4561,4562,4564;BPBV4QVT:21991,21992,21993;BSEGQWGC:27536,27537,27538;BSMR25F1:4355,4356,4357;BTTDTNVP:26008,26009;BVKEZBRG:27520,27521,27522;BW9RYL57:20118,20119,20120;BWFGBRYK:7512,7513,7514;BWTAN0NP:11405,11406,11407;BWWE2ZIJ:24050,24051,24052;BYHW5U8A:2415,2416,2417;BYNESCM0:14122,14124;BYZQI2YS:27071,27072,27073;BZDTPD98:2211,2212,2214;BZFXYPSN:23795,23796,23797;BZSP2BWR:20178,20179,20180;BZZEO0DQ:24189,24190,24192;C04C279G:17593,17594,17595;C0U52ILC:19691,19692,19695;C1UQP8HC:7735,7736,7737;C1V7JESN:4249,4250,4251;C2O7FFNJ:4376,4377,4378;C2P0M9M0:24419,24420,24421;C3J6HEIX:4894,4895,4896;C41PK6Z5:24148,24149,24150;C6DW4P12:25651,25652,25653;C6XFV1E5:19736,19738,19740;C6XM14PU:11164,11165,11166;C7HUHRRO:16087,16088,16089;C85K8ZLH:4301,4302,4304;C947RKQH:9882,9883,9884;C9H01WIM:16283,16284,16285;C9I0OCYY:11633,11634,11635;C9MBFOW5:19672,19673,19674;C9O91L4N:20463,20464,20465;C9PG9NPR:6419,6420,6421;CAF6JZR2:28162,28163,28164;CAOJONEH:25579,25581;CBA3XGKB:8876,8877,8878;CBF8PNY9:14062,14063,14064;CBHVIV3W:2474,2475,2476;CC88IS0J:9457,9458,9459;CC8TJTBR:26614,26616,26617;CCZOFA5Q:15069,15070,15071;CDASNEH5:22092,22093,22094;CDRD9IDE:7247,7248,7249;CDZF1ALC:28185,28186,28187;CEOL50VM:22017,22020,22021;CG0ROEZB:27371,27373,27374;CGW1H61C:19760,19761,19762;CHLR0HVC:20316,20317,20318;CIMPCLSK:20259,20260,20261;CIUO120S:7749,7750,7751;CJ07UQWX:6104,6105,6106;CJB3LRD7:7239,7240,7241;CJFDMG2J:4256,4257,4258;CJJ8CSAG:4336,4337,4338;CK77C5WV:25642,25643,25644;CKISRI2B:11500,11502,11503;CLKZN0EC:22076,22077,22078;CLRKAT15:7506,7507,7508;CNFLXM7E:21878,21879,21880;CO52ZHNJ:6143,6144,6145;COME7253:22004,22005,22006;CRXCHGPS:2500,2501,2502;CSJ5MGIY:1903,1905,1907;CSL29RHC:16113,16115,16117;CT2UFEOP:16061,16062,16063;CT6BPS70:17294,17295,17296;CV6D6YTY:7055,7056,7057;CVJR1QB1:11118,11119,11120;CW7UD6HH:23490,23491,23492;CWVO3WYX:23479,23480,23481;CYZA6GYS:19512;CZ2GNXH6:8844,8846,8847;CZPL165P:17378,17379,17380;D018N09A:25582,25583;D070WYC9:17408,17409,17412;D0PLDUDA:1,2,3;D2CBMF2U:27088,27089,27090;D2GMUK8Z:27326,27327,27328;D2IXPWVZ:19019,19020,19021;D2YXK31U:16292,16293,16294;D3893GVZ:11612,11613,11614;D3BYFB1K:4211,4212,4213;D456WEDH:24338,24339,24340;D45Y6X2M:25605,25606,25607;D4FC4DLW:2503,2504,2505;D4OEPLWC:1341,1342,1343;D5H7ATMX:16078,16079,16080;D5KU9GNT:7647,7648,7651;D5VZQMCV:17334,17335,17336;D6KVI9JD:2376,2377,2378;D7TT1R34:23022,23023,23024;D917QKSF:27204;D9VB4DKQ:114,115,116;DAKHJ3Y2:7127,7128,7129;DB6OCOTH:1128,1129,1130;DBR6LG5W:4177,4180,4183;DBRDHEGH:23051,23052,23055;DBW7G9W0:23038,23039,23040;DCTHXYMC:22047,22048,22049;DD2JQZQX:27249,27250,27251;DD79K5TQ:9976,9977,9978;DDTQOF6Y:26125,26126,26127;DDXGPUEP:937,938,939;DEX3P3JI:1119,1120,1121;DEZK3NBU:28268,28270,28272;DEZSEY8J:14087,14089,14090;DF25RA8D:89,90,91;DFSNWHXF:9847,9848,9849;DG7EFXXD:10021,10022,10023;DGORBXET:23466,23468;DGWSZC6U:6667,6668,6669;DHVT8P1C:4119,4120,4121;DHXRAK9O:9370,9371,9372;DIMTCW2I:7096,7097,7098;DIPMTY2A:14513,14514,14515;DKH6IOKA:26029,26032,29007;DKSXOZD1:27439,27440;DKTK22F2:14940,14942,14944;DLSBDRL1:2558,2559,2560;DM84SH34:11454,11455,11456;DM9HTZC8:16458,16459,16460;DMFBOFHI:19627,19628,19629;DMGMSBBH:11606,11607,11608;DMRMXEUR:226,227,228;DMUIUVFQ:2400,2401,2402;DNFK5ZS5:20287,20288,20289;DNKLOCCF:19115,19116,19117;DPK4WZC3:7500,7501,7502;DQ11TIUT:26103,26104,26105;DQPCLV1C:1000075,1000139,1000256;DQQN78N1:19838,19840,19841;DSFSNFUZ:10031,10032,10033;DTMCJI4L:22029,22030,22031;DTODYSI2:7242,7243;DU3LKV3R:16794,16795,16796;DUVIKNH5:20365,20366,20367;DVWJP201:37,39;DW7YH4G0:17817,17818,17819;DWEQNLYL:17138,17139,17140;DWKNZ4M4:6455,6456,6457;DXSH7AWE:2171,2172,2173;DY4JG42E:16842,16844,16845;DYJXJJ3B:108,109,110;E03J9N03:7676,7677,7678;E1QEDCAG:28200,28201;E255O48P:19478,19479,19480;E2PH0BQG:27359,27360,27361;E3URN2QW:9296,9297,9298;E4D5DRBU:21440,21441,21442;E4PZ4EEO:26862,26863,26864;E4R47HOP:28159,28160,28161;E4YFD8SD:2761,2762,2763;E5A7D39M:4317,4318,4319;E5OPC7JN:14130,14133,14134;E5UYTPXS:122,123,124;E678L6IS:19000,19001,19002;E7CL0P7E:14017,14018,14019;E85RT90A:27342,27343,27344;E85URD1T:27337,27339,27341;E8BASB3A:16012,16013,16014;E8C3FG92:20066,20067,20068;E8ES4530:4953,4954,4955;E92N1FYQ:4392,4393,4394;E9547JBA:1587,1588;EB3U9XZC:16322,16323,16324;EC65SIRK:25902,25903,25904;ECQ52VLB:11699,11700,11701;EDKRS0MP:12540,12541,12542;EE2HRQCW:6469,6470,6471;EESFPH3H:975,976,977;EGR8KXOL:6555,6556,6559;EHJYHXTT:19487,19488,19489;EHR9GJI2:27294,27295,27296;EIGT160X:25870,25871,25872;EIRU945E:102,103,104;EJ442T3K:6452,6453,6454;EKM6OKZR:11648,11649,11650;ELCMORND:22032,22033,22034;EM1J3UWS:3603,3604,3605;EM6DW5F3:20442,20443,20444;ENYKQQN1:7626,7627,7628;EOCO2LBV:24253,24254,24255;EON3CUH3:25663,25664;EOR7KNV1:3637,3638,3639;EOXT1O7B:20448,20449,20450;EPONYJOP:9998,9999,10000;EQDPILFB:27381,27382,27383;EQFG0LM0:20380,20381,20382;EQGOJVEI:8830,8831,8832;EQGWXMYB:20505,20506,20507;EQKMFOM0:9423,9424,9425;ER8AYXY7:7743,7744,7745;ES8MXVG1:12584,12585,12586;ET0YDXIR:16048,16049,16050;ET305Q40:21557,21558,21559;ETTPTLQ6:24215,24216,24217;EUQBKEAK:28168,28169;EUTK44PO:28156,28157,28158;EV7BH3SS:14103,14104,14105;EV8U7HFD:8853,8854,8855;EVL6O71X:6536,6537,6538;EWHVPSCC:4495,4497,4499;EWHWFF0Y:24608,24609,24611;EWYNDTIG:21548,21549,21550;EX80R6FM:27065,27066,27067;EYJ6AX4M:7746,7747,7748;EYTJCWYK:15997,15998,15999;EYWTMFAG:9469,9470,9471;F0JV3BXW:11592,11593,11594;F128MOIZ:20222,20223,20224;F173WNCZ:8930,8932;F25UMAML:15144,15145,15146;F265FKS4:19722,19723,19724;F27OJORQ:27205,27206,27207;F28X67LZ:4486,4487,4488;F2KWY5U6:16256,16257,16258;F2X4O1SG:20121,20122,20123;F53BW7O8:22125,22126,22127;F5X1DYML:14953,14954,14955;F6V4LBK1:67,68,69;F6XBD2IU:1161,1162,1164;F79M417U:12608,12609,12610;F7VKZ164:19684,19685,19686;F81YOPCS:26014,26015,26017;F8TWYG3W:23016,23017,23018;F9CETWHZ:17351,17352,17353;FAJR5456:20322,20323,20324;FCO0UZWT:15080,15081,15082;FCQNJGKR:4214,4215,4216;FCXBT98C:10060,10061,10062;FD4EXQ4F:27193,27194;FDUY69ZF:11178,11179,11180;FFYQOPUE:11696,11697,11698;FGIUADWF:24459,24460,24461;FH2WTW0W:27267,27268,27269;FHKMD2XM:24179,24180,24181;FIVHNLH5:23883,23885,23887;FK39CS8H:28188,28189,28190;FKIBZWI0:12079,12080,12081;FKKR2XG5:23,25,28;FL4KNBGT:28260,28261,28262;FMRL8ZYG:10051,10052,10053;FN87CMIQ:22990,22991,22992;FOBDBQWH:15036,15037,15038;FOZ6HZLK:4125,4127,4129;FP2SPUQ2:8905,8906,8907;FPSA7KE4:17328,17329,17330;FPV6ZNJ4:7226,7227,7228;FREWYGOW:23443,23444;FRIVDO0X:7827,7828;FRKC71T9:49,50,51;FRROUPY0:24282,24284,24285;FRSKUOF3:21998,21999,22000;FU8AWTH6:1908,1909,1910;FU8F1L0G:14851,14852,14853;FUCTPMD6:19856,19857,19858;FV0H1RN3:16606,16607,16608;FW0QY39A:16482,16483,16484;FWT21EO3:2585,2586,2587;FX6SIZ5H:11489,11490,11491;FXBKKGJR:16333,16334,16335;FY0BVGFW:19475,19476,19477;FY73D3U2:28250,28251;FYAV2O2R:17305,17306,17307;FYNZEKI6:4534,4535,4537;FYSW84O8:11420,11421,11422;FYXXCZ4V:9876,9877,9878;FZ1CP5FR:21542,21543,21544;FZTCGO43:22097,22098,22099;FZZG9HTT:23352,23353,23354;G07NPSVK:73,76,77;G11K36ZS:9351,9352;G1SWM3Q5:10057,10058,10059;G1XYQLDH:27255,27256,27257;G23C2DGZ:11363,11364,11366;G2VO8VM2:22180,22181,22182;G33Z2MUM:24227,24228;G3JCCGT0:6484,6485,6486;G40MDUZ7:15879,15881;G48NM1TM:15962,15963,15964;G4NYA2PZ:20234,20235,20236;G58FN51A:11578,11580,11582;G6P1S0QJ:27892,27893,27894;G8ND5KJ7:28295,28296,28298;G8R5IFTL:27406,27407,27408;G8YSAI5Z:1000050,1000132,1000133,1000249,1000250;G9TTO1MQ:23333,23334,23336;G9Z3UBNI:26081,26082,26083;G9ZWA133:14828,14829,14830;GBW57LF7:24196,24197,24198;GFQLZOLH:20362,20363,20364;GG9F4045:27321,27322,27323;GGXA3HYH:6357,6358,6359;GH5EN8A0:19733,19734,19735;GI56PPVS:4448,4449,4450;GIPFO7R9:11172,11173,11174;GJIVM7IT:20284,20285,20286;GK635OJV:20502,20503,20504;GKSQXHST:2236,2237,2238;GLHEM0EM:21563,21565;GM2IM8PP:25873,25874,25875;GM8VDVK2:21597,21599,21601;GMWSIZKV:7545,7548,7549;GNZJ2ZYV:14530,14531,14532;GO6J9CFL:204,207,208;GOUQV7P6:27021,27022,27023;GOWNGN8S:4547,4548,4549;GQCBSQNY:27133,27137,27142;GRUQHIOY:21964,21967,21968;GRXSAOAR:19505,19506,19507;GSHQY9K0:27027,27028,27029;GT9F0H9A:10054,10055,10056;GUASGG0E:7856,7857,7858;GUIC6VBV:23400,23401,23402;GVF94FSP:27378,27379,27380;GWAP2ROG:19620,19621,19623;GWEROU6H:11557,11559,11562;GXFOHORW:19624,19625,19626;GY87XO6T:23026,23027,23028;GYTP2UYR:24098,24099,24100;GZJ06CVZ:25639,25640,25641;H0ABQPLB:19678,19679,19680;H0Y3TLFQ:27692,27693,27694;H2GKG338:19094,19096,19098;H2JZ0S63:25718,25719,25720;H32V7ME1:7087,7088,7089;H35LON73:3584,3585,3586;H3SQXY47:17277,17278;H4M5L5GN:23449,23450,23451;H4NS22M2:4538,4539,4540;H4WHY23T:6458,6460,6462;H5D4U5Y1:1894,1895,1896;H5DK4S30:26627,26628,26629;H5JSBRAB:17384,17385,17386;H5YNNNX9:25876,25878,25881;H6AJI9MN:20243,20244,20245;H6CTRVR6:11413,11415,11416;H70X3EDL:24664,24665,24666;H89GWGOV:26969,26970,26971;H8RZIY4I:11987,11988,11989;H8VX2LLI:19103,19106,19107;H963BXRC:19066,19067,19068;H9IM4JRQ:17196,17197,17198;H9PO7G2C:20290,20291,20292;H9QKBCJJ:28152,28153,28154;HA56XRWB:15864,15865,15866;HAPU77CQ:7664,7665,7666;HBNJQN4Q:26116,26117,26118;HCLVDB1F:28279,28280;HD3F6BGF:20388,20389,20390;HD7U3EEW:22059,22060,22061;HDC9YSN1:20397,20398,20399;HE93GNBP:26292,26294;HE9R3NJJ:3654,3655,3656;HEWFIPKX:9373,9374,9375;HFEVYW5E:16020,16021,16022;HG9N6SL4:28286,28287,28288;HGXAVYKA:16775,16776,16777;HIVVE142:9888,9889,9890;HIZ2ZCQW:3640,3641,3642;HJAGRII7:19063,19064,19065;HK8WW9DG:19669,19670,19671;HKV76CWT:2245,2246,2247;HLK9DTJZ:16128,16129,16130;HM3WMK2C:23013,23014,23015;HM8X1IG6:4470,4471,4473;HMVS1CZT:19664,19667,19668;HMYJF0O0:6360,6361,6362;HNZ05DUM:6530,6531,6532;HOPCBVKM:10,11,12,13;HP16J20P:24519,24520,24521;HP4B2ZOC:27387,27388,27389;HPNJ32UM:28145;HQQGOU80:11990,11991,11992;HREOJILU:24205,24206,24207;HRU4PFH3:2385,2386,2387;HRWZTSNC:7262,7263,7264;HU1V9LBD:20454,20455,20456;HUVTKXUT:6416,6417,6418;HV0ACHIX:16356,16357,16358;HVAJLH8C:19030,19031;HVF3U14A:21875,21876,21877;HVZ6HSY1:20339,20340,20341;HWQD93VG:24350,24351,24352;HX5NN35J:9460,9461,9462;HXXKR5TP:19585,19586,19587;HYCZT2HJ:23019,23020,23021;HZQQ9AX2:27412,27413,27414;HZRKTHUD:20231,20232,20233;HZYSLQ5J:25648,25649,25650;I09CXYZU:11795,11797;I0JZC7TB:17392,17393,17394;I0OK39I3:19080,19081;I0Q1IGYI:16862,16863,16864;I17665Y8:27167,27168,27169;I1NGZTNW:12337,12338,12339;I2771YD1:2180,2181,2182;I324JRN9:24486,24487;I426D2G8:15056,15057,15058;I4Q1XZJ6:27497,27498,27499;I5ARNGYL:9989,9990,9991;I5QMB5PV:148,149,150;I65VOGNZ:25584,25585,25586;I66K78EN:2540,2541,2542;I688IIJ5:4881,4883;I6K8CXAP:20496,20497,20498;I847SPN3:3699;I9O4W3LM:4085,4086,4087;IALX34JP:4311,4312,4313;IC8KSHWL:28112,28113,28114;IDMDRA7L:1000121,1000145,1000260;IF7RW7VN:9367,9368,9369;IFKJRVHP:20424,20425,20426;IFQAPGOL:7767,7770,7771;IFSEZ6DB:1000104,1000149,1000262;IHEKKLM2:17220,17221,17222;IJ42Z3K7:23230,23231,23232;IJF39T1O:12086,12087,12088;IKCRZV7P:6572,6573,6574;ILLT1P86:7429,7430,7431;ILTW7QKH:17016,17017,17018;ILTX6MV0:24238,24239,24240;IM4K1DBC:11378,11379,11380;IN3KY9QC:27049,27050,27051;IN5LCYF5:15187,15188,15189;IN5XB4PK:6487,6488,6489;INRQQSKA:16183,16184,16187;IOLUI9TL:20736,20737,20738;IP6JC3BS:28026,28027,28028;IQW33SKW:16064,16065,16066;ISJ2J1M0:10075,10076,10077;IT99US9E:6444,6446,6447;ITB5YIE4:14947,14948,14949;IU9KLQVL:20711,20712,20713;IW0KT7XJ:28276,28277,28278;IW3Y1ZZU:7579,7581,7583;IX0CFEUE:154,155,156;IX6FX4TX:9451,9453;IYE5P9E2:27062,27063,27064;IZYGS5FM:20403,20404,20406;J0ED1SSA:25614,25615,25616;J1DM99LV:15000,15001,15003;J1FFNJH4:7265,7266,7267;J27C35H4:4297,4298,4299;J3NUPZNP:3727,3728,3729;J4DOS29T:23823,23824,23825;J5B4V6B3:7620,7621,7622;J5IEKMWT:23403,23404,23405;J62NO1EG:199,202,203;J8L7PT78:26064,26065,26066;J8QOCNNW:3600,3601,3602;JA52GFJR:4524,4525,4526;JBB3BUXX:20097,20098,20099;JCNDYJEU:11618,11619,11620;JDQN4UGW:11506,11507,11508;JE08GC83:27130,27131,27132;JEBATKQL:6670,6671,6672;JEO7H9DU:24396,24397,24398;JF5TYP2X:17262,17263,17264;JF9GF481:20262,20263;JGUXYKCW:22079,22080,22081;JI5UQDSB:7686,7687,7689;JI9CTYNV:20069,20070,20071;JIU6189Y:27175,27176,27177;JIV9AJWI:28318,28320;JJZLI10B:9429,9430,9431;JKJ1NZH6:27217,27219,27221;JKMJG7DB:3643,3644,3645;JKWTLJJM:1865,1866,1867;JKX1MEBG:9420,9421,9422;JLR9NO56:17413,17414,17415;JLS50SKM:7287,7288,7289;JMNO7B14:6119,6120,6121;JMSA9ZRK:24020,24021,24022;JNI5UWIA:2588,2590;JO9Y99TZ:4113,4114,4115;JOCUY924:1281,1282,1283;JOYUZOWP:16241,16242,16243;JP4IN6AG:27433,27434,27435;JQ0BKQPT:25885,25886,25887;JQCIRP9W:11589,11590,11591;JQN4SA1N:27059,27060,27061;JR8FCQAV:28165,28166,28167;JRHU9P08:2403,2404,2405;JS426CSL:20325,20326,20327;JS55BNSV:1000079,1000131,1000248;JS89MEQZ:15086,15087,15088;JSXZFNG8:27053,27054,27055;JT1HIN62:4237,4238,4239;JTSWFEKZ:7704,7705,7706;JUTS27P6:16379,16381,16384;JV1JZ18X:24374,24375,24376;JV5FHQLA:3634,3635,3636;JV7S9HGE:11639,11640,11641;JVQQJGYK:27015,27016,27017;JW2E2FL8:19605,19606,19607;JX4KYMZO:7052,7053,7054;JXT6ZZ10:19602,19603,19604;JYQMI0MP:8912,8913,8914;K013ZH03:20265,20266,20269;K16D7031:229,230,231;K1INSSDW:19562,19563,19565;K491Z8WX:24504,24506,24507;K4Y7GWGB:95,96,97;K4YTZW7I:19121,19122,19123;K5AZ1IJ5:9417,9418,9419;K63Q8CYH:2600,2601,2602;K6XHBKGY:25666,25667,25668;K6Y3C4UY:19091,19092,19093;K7MRXTLC:10078,10079,10080;K9CTTNG7:6425,6426,6427;KA2RTLHJ:10028,10029,10030;KAGN4Z5G:1356,1357,1358;KAHSA1U3:26826,26828,26830;KBZR2ND6:25636,25637,25638;KC75NGPR:21872,21873,21874;KC7U7OZF:15018,15019,15021;KC924C8D:7576,7577,7578;KCW3YIEY:17223,17224,17225;KESYJU5O:7682,7683,7684;KF4AQRF9:26975,26976,26977;KF8WAN6Z:16036,16037,16038;KFNNT1IH:7635,7636,7637;KG9P4U74:11804,11805,11806;KH0P77SE:9844,9845,9846;KH2N9GHB:3606,3607,3608;KHMY5SZ8:15177,15178,15179;KI59EC11:4585,4586,4588;KI5Z8YFW:20488,20489,20490;KI7NY0Q5:27030,27031,27032;KICW2PCT:4409,4410,4411;KIK6CWTD:1075,1076,1077;KJLFHPLW:17402,17403,17404;KK2DEIRB:23431,23432,23433;KKSCIZJV:23482,23483,23484;KL301NVN:11687,11688,11689;KLZONDVO:16368,16370;KMPKMGGM:2230,2231,2232;KOP1J2ZN:25863,25864,25865;KQCK2MH1:27350,27351,27352;KRRAWTGW:21962;KS03M13U:16214,16215,16216;KSE09IGN:20483,20484,20485;KSOIJZ4C:19558,19559,19560;KSX5SRRF:20702,20703,20704;KT0601S6:24289,24292;KT9ILGOT:190,191,192;KTZJRCR2:16144,16145,16146;KUX4Y2SP:20297,20298,20299;KVL5JEQP:7130,7131,7132;KVY9YYF9:9970,9971,9972;KW41HVC6:15922,15923;KW48G6H8:9472,9473,9474;KXHMHZEA:19088,19089,19090;KXVP12T4:2546,2547,2548;KZODE7UN:20011,20012,20013;L18LNLDB:4434,4435,4436;L1BQ6VMZ:15908,15909,15910;L1ZAEBNM:14808,14809,14811;L27W8O79:24064,24065,24066;L2P2AX33:2537,2538,2539;L2T2Z1NM:7064,7065,7066;L2YLL0YE:26067,26068,26069;L31D0YNA:27012,27013,27014;L3I7VZF6:20342,20343,20344;L49QA7XK:25760,25762;L4HEO3NF:26156,26157,26160;L597FO6M:4445,4446,4447;L59DOXX3:23428,23429,23430;L5HRRR07:6163,6164,6165;L5M1PJOU:21924,21925,21926;L6QVPQOV:20430,20431,20432;L7SFED60:24126,24127,24128;L93GS1NW:16166,16167,16168;L93RUMWZ:17317,17318,17319;LAD52IZY:17012,17013,17015;LBLUSSEN:7570,7571,7572;LC3AU1J0:16220,16221,16222;LCQAF7EX:23820,23821;LEFOZOYV:16211,16212,16213;LEMAR6RO:14,15,16;LEMYC08F:27225,27226,27227;LEPRB2QV:17,18,19;LHT7NBNU:2621,2622,2623;LHWHYC4B:16226,16227,16228;LIKYP82F:2456,2457,2458;LIQKZBVX:1000098,1000157,1000269;LJ0GISH6:11161,11162,11163;LJ4YRZNU:16023,16024;LJNPKCPE:28149,28150,28151;LK1DSLQ3:19661,19662,19663;LKKTWNDA:20466,20467,20468;LKV91LE2:7533,7534,7535;LL3QYQUY:7655,7656,7657;LLQHD7MG:1000115,1000147,1000261;LLWPR0BH:7758,7759,7760;LM92ULIF:16928,16929,16930;LMK46KPW:4314,4315,4316;LMOE3MIC:19569,19570,19571;LMV1HON9:24107,24109,24111;LNXDZPMF:28273,28274,28275;LOPEKPV7:16789,16790,16791;LPNYG0XH:27085,27086,27087;LQ0YR680:14920,14921,14923;LQ5R8CY7:4515,4516,4517;LQ8JLDBT:27303,27304,27305;LQJ5I70F:14977,14978,14979;LR9THA9V:1912,1913,1914;LRE8Q7HV:17331,17332,17333;LTEUXCWK:26056,26057,26058;LVG0EZD3:24646,24647,24648;LXTVI816:9390,9391,9392;LYHWNOMX:165,166,167;LZT1A0R2:9364,9365,9366;M030DK5Q:23440,23441,23442;M05E7Z7L:7658,7659,7660;M1RLTMGC:1000038,1000134,1000251;M1XEBY1E:24129,24130,24131;M2Z9YBQ9:27103,27104,27105;M4Z4I759:25836,25837,25838;M793F1E8:22070,22071,22072;M7BUT7CY:11367,11368,11369;M8991E0Y:2215,2216,2217;M8N2ITO9:11396,11397,11398;M8QJWMBM:17423,17424,17426;M98ISAVT:27097,27098,27099;M9XFKSZI:3609,3610,3611;MARGMHTK:21921,21922,21923;MBV47M2Z:6150,6151,6152;MC0J51Z4:25905,25906,25907;MCD6CRNB:7080,7081,7082,7083;MCTOE3DB:9992,9993,9994;MDGSWBOW:2382,2383,2384;MDOXOBIC:2163,2164,2165;MDTOPVTS:15006,15007,15008;MDZ6ZH5J:17368,17369,17370;MEWWFHQF:2511,2512,2513;MFJVYB3U:27127,27128,27129;MFOO63DR:19003,19004,19005;MHIOJTPG:6507,6508,6509;MHMM880K:26217,26218,26219;MHPMT7V9:21488,21489,21490;MJ5LTS7N:16157,16158,16159;MJKSOMIO:4565,4566;MJO3ZLTC:24112,24113,24114;MKNKVYOX:26995,26996,26997;ML3PD5CI:1338,1340;MMEP9MCE:24244,24245,24246;MMGRH7QL:20064,20065;MOE8UH8G:23445,23446,23448;MOF0L7HU:7536,7537,7538;MOM16UTM:7542,7543,7544;MOQWP51Q:19402,19403,19404;MOTRLVUY:26170,26171,26172;MP5KBU53:22160,22162;MPESWZZJ:20136,20137,20138;MPF7E8N7:1000127,1000150,1000263;MPKKINRZ:27334,27335,27336;MRWTC3N5:27509,27510,27511;MT37C6LK:17118,17119,17120;MT99SJI5:2186,2187,2188;MUY4HFLP:7933,7934,7935;MVH2K98H:40,41,42;MWYEE36F:21937,21938,21939;MXWCS2S3:21454,21455,21456;MYEK8UA6:2532,2534,2536;MYEWH7PK:23204,23206,23207;MYK7WA9Z:25736,25737,25738;N01JXKPR:27228,27229,27230;N0418MJ2:28315,28316,28317;N0P2M218:20308,20310,20312;N10XSR47:2438,2440,2442;N1CUULMN:4481,4482,4485;N1MQWYYB:10024,10025,10026;N1Z0ILG0:19696,19697,19698;N2FTML16:20124,20125,20126;N2NFBJ9V:3618,3619,3620;N39HYHPN:6545,6546,6547;N46SJV0D:9838,9839,9840;N4RE5UJC:16280,16281,16282;N575U0Z6:21560,21561,21562;N6AYV6AQ:18088,18089,18090;N6T3CVUA:20331,20332,20333;NA3R1PPN:1942,1943,1944;NBEMYAG6:14924,14925,14926;NC089PX3:6281,6282,6283;NC5IRBSR:16312,16313,16314;NCGWUUCF:14906,14907,14908;NE0791VE:196,197,198;NE17WKHG:2506,2508,2510;NF16EL5Q:6493,6494,6495;NF6IEV35:11907,11908,11909;NFD02UMU:6147,6148,6149;NGJVOO7W:11343,11344,11345;NIM52D3H:21588,21589,21590;NIZQUMUC:19393,19394,19395;NJ6BRVP5:9405,9406,9407;NJNUHFEY:24422,24423,24424;NL0Q8VTD:4418,4420;NM9ZXJWK:25999,26000,26001;NNVT3ED1:17455,17456,17457;NP6RY9H6:17213,17214,17216;NQA7PM8J:20253,20254,20255;NQKREEU1:4339,4340,4341;NQTMN2F0:11121,11122,11123;NRJXQ56X:14988,14989,14990;NRZVKH85:22979,22981,22983;NSFUMOB6:17395,17396,17397;NSP35NJL:8891,8892,8893;NTL6SUD3:2430,2431,2432;NU9SV8D0:23457,23458,23459;NUBQNV1K:21462;NV9LN1YO:1171,1172,1173;NVRWUFA0:27222,27223,27224;NW7LNICB:24263,24264,24265;NWN3DI1N:2523,2524,2525;NX2P6AID:27384,27385,27386;NX2Y0FGT:24474,24475,24476;NX46K1JA:21885,21886,21887;NX6UUZZ1:24229,24230,24231;NYDBE0X8:9438,9439,9440;NYJWYGM8:12205,12206,12207;NYX7VGK8:15015,15016,15017;NZPH9TR2:25602,25603,25604;NZQPRK5S:20439,20440,20441;O00ATDUA:19484,19485,19486;O0L0Z6O7:21436,21437,21438;O1EA7CF8:61,62,63;O1HZ8L80:20334,20335;O1IYMQV4:2529,2530,2531;O1M5TV0O:20407,20409,20411;O2AH0TJH:16295,16296,16297;O2AL7LGC:16925,16927;O2CJIXFV:1125,1126,1127;O3NMUZP2:14909,14910,14911;O4DMZFW0:6275,6276,6277;O4ZIK2ZW:11540,11541,11542;O593FMV4:26113,26114,26115;O5JN05QJ:5178,5179,5180;O66V64QY:9287,9289;O8B6002J:19519,19520,19521;O8J45GX1:23000,23001,23002;O8YBDJL4:17356,17357,17358;O92DT30Z:16107,16109;O932566J:23197,23198,23199;OABB9QOR:27234,27235;OACFDKZK:28139,28140,28141;OAK983RU:15867,15868,15869;OAQDRTNC:25627,25628,25629;OBBBCH0X:17202,17204,17207;OBVOD999:11390,11391,11392;OC7DPUBP:24151,24152,24153;OCNTE01G:7183,7184;ODJRIJGW:17524,17527,17528;ODSISSRU:16848,16849,16850;OE0A207H:6515,6516,6517;OEYQTJ9I:27208,27209,27210;OFBLBD48:959,960,961;OFCFPC15:26618,26619,26620;OFX7IOMJ:11528,11529,11530;OG6HK0FX:27306,27307,27308;OGX0SMES:24067,24068,24069;OH5MPXQD:7058,7059,7060;OHB1MX1C:19481,19482,19483;OHNPJ6O7:4231,4232,4233;OHQMG9V5:1891,1892,1893;OHRSRQ23:22007,22009,22011;OI0BABSC:22035,22036,22037;OI16EGU3:7564,7565,7566;OIM32Y6H:17702,17703,17704;OIT006F3:145,146,147;OJ34Z95B:16253,16254;OJWBRLCG:24347,24348,24349;OJYLJ270:15335,15336,15337;OK1APVUR:15043,15044,15045;OK8XLQ2P:9411,9412,9413;OKSH02SY:16264,16265,16266;OLXLY7GP:4288,4291,4292;OMNYWU2P:2543,2544,2545;ONGIVCGX:27197,27198,27199;ONNVM3PM:16269,16270,16271;OOG6QNVC:20460,20461,20462;OP0TGDTN:16826,16827,16828;OQDKVZN5:27474,27475,27476;OQHE2DK5:19073,19075,19077;OQQA94LZ:24145,24146,24147;OQQEE6VD:7850,7851,7852;ORGFC5YK:17463,17464,17465;OS42NFPY:14182,14183,14184;OUPAY835:24313,24314,24315;OVEX2YHX:2549,2550,2551;OVW04W7A:1084,1087,1091;OWEGE5JT:19118,19119,19120;OWVIV4TQ:7661,7662,7663;OX1XQWC0:19455,19457,19459;OXD9J648:19546,19547,19548;OXFA236M:24182,24183,24184;OXQ0HMZT:11346,11347,11348;OYON7ZYN:1956,1957,1958;OZ17Y89W:23472,23474;OZLBWBWI:20017,20018,20019;P0HNAW9A:968,969,970;P0YMQODU:118,119,121;P2LAJILG:19549,19550,19551;P2YBVYDO:27153,27154,27155;P39HEZUO:27460,27462,27463;P3CSA1R7:2391,2392,2393;P3RCYIQ5:23434,23435,23436;P62C5QYD:6481,6482,6483;P65UX5RR:23340,23341,23342;P67I3E7D:16055,16056,16057;P6JPT3CI:24218,24219,24220;P6LBPM8O:26050,26051,26052;P7BIMB3M:21985,21986,21987;P8RGWZBN:24568,24569,24570;P9CNPUEZ:25721,25722,25723;PA9R9LAV:16163,16164,16165;PB3ASE0N:23413,23414,23416;PC7VF7HB:4362,4363,4364;PCXJZGHG:20687,20688,20689;PCZDI8P1:7559,7561,7563;PDPM212C:3612,3613,3614;PEE1XTR8:26018,26021,26022;PEHERR0C:27353,27354,27355;PFX8LGZD:17285,17286,17287;PFY3DMKM:27819;PGB65M29:20115,20116,20117;PHCS7BZM:17917,17918,17919;PHMDLLZ6:9662,9663,9664;PHYXLBYD:8866,8867,8869;PI0C3OCY:16000,16001,16002;PIO4P8I4:28303,28304,28305;PIUTIK7D:14950,14951,14952;PJ1XXRGN:11384,11385,11386;PJ8JVHWA:7072,7073,7074;PJBE2G9J:19499,19500,19501;PKJX0WJA:28123,28124,28125;PKMWG62D:15033,15034,15035;PKZUYAG4:15029,15030,15031;PLHF5Z3V:7586,7587,7588;PMD88XZH:20474,20475,20476;PMNCF58W:15991,15992,15993;PMS3SFKT:9493,9495;PMYVJZBD:26093,26094,26095;PNIVSCF9:1122,1123,1124;PNWVDXG3:6140,6141,6142;PPCKX6OZ:24162,24167,24169;PRK2K7D7:21807,21808,21809;PSZU8JIS:20359,20360,20361;PT6F0QCO:6563,6564,6565;PT9H88B3:4887,4888,4889;PTHKW848:7764,7765,7766;PUX34NX8:10042,10043,10044;PVD3K2TX:2526,2527,2528;PVGCBYS4:7539,7540,7541;PVJZBEPP:4108,4109,4110;PVRG1SNH:1868,1869,1870;PVTVCZY6:27539,27540,27541;PWQL1L1B:7259,7260,7261;PWX2LMOK:20451,20452,20453;PXEJCFTK:24142,24143,24144;PYI57A2H:9850,9851,9852;PZC21H3Q:24136,24137,24138;Q06WJ6NG:28182,28183,28184;Q15NIMC9:4637,4638,4639;Q16XHX6U:23463,23464,23465;Q1EUT011:1066,1067,1068;Q20JKY62:4351,4352,4354;Q2L7SPZ4:26119,26120,26121;Q39ZMMS8:24525,24526,24527;Q413IXBZ:11662,11663,11664;Q5237UOE:7293,7295,7297;Q63BAWAV:27183,27184,27186;Q67WQHOT:8873,8874,8875;Q7DMUA40:6396,6397,6398;Q7PZAY7B:22165,22166,22167;Q97BMVQT:24362,24363,24364;Q9FIC570:15066,15067,15068;Q9KV1UR1:7679,7680,7681;QA3YYC33:11512,11513,11514;QCEM25NP:3849,3850,3851;QCXV3AP9:2591,2592,2593;QD0IDK52:2233,2234,2235;QDTRNIAN:15858,15859,15860;QDVKY0O8:21927,21928,21929;QEW738MV:14805,14806,14807;QEY51528:11713,11714,11715;QFI4JHC5:27164,27165,27166;QFICOUL9:17362,17363,17364;QGGAFU70:4477,4478,4479;QH6672TZ:24449;QHGPXAIT:4442,4443,4444;QHGYH1SQ:20374,20375,20376;QHLOXBAE:19596,19597,19598;QICLABKK:24076,24077,24078;QJ4GUHIU:24434,24435,24436;QJLJV4NX:15135,15136,15137;QJP0N5I9:7223,7224,7225;QJQ9M4OF:17365,17367;QJU46KKK:4346,4347,4348;QK862LXG:9879,9880,9881;QL70KV8I:12567,12568,12570;QL81PBD7:17028,17029,17030;QLT8OW7M:20306,20307;QLW5VE14:20427,20428,20429;QM6JKBDR:10063,10064,10065;QNAJI0PK:6125,6126,6127;QNZGACHP:7623,7624,7625;QO23AD0H:6413,6414,6415;QP26TS7E:943,944,945;QPTIEJFO:19755,19757,19759;QR9IIH3J:9441,9442,9443;QSGG2EBF:11566,11567,11568;QTKU39GT:2227,2228,2229;QTVBE8KJ:20477,20478,20479;QUU381VS:6527,6528,6529;QW7MPWOM:20072,20074,20076;QWF38CXX:7728,7729,7730;QWYGJXPX:27300,27301,27302;QXVJG0DJ:4552,4553,4554;QXWGOSEM:4460,4461,4462;QZV0ZZ6U:16052,16053,16054;R03TJJ5J:2388,2389,2390;R04753EK:17217,17218,17219;R070XQ39:4609,4610,4611;R08KB192:24377,24378,24379;R0L2SZC8:21554,21555,21556;R2HJLVHX:4240,4241,4242;R3CAYTF6:17566,17568;R4HK87S5:20524,20525,20526;R4U9QUFA:19681,19682,19683;R5MKXHIX:4252,4253,4254;R5PWNYWD:981,982,983;R5S0LNQL:20584,20585,20586;R6L1IWSQ:6438,6439,6440;R70FUX7V:19552,19553,19554;R79SBRC1:6600,6601,6602;R7CGYH0N:24193,24194,24195;R8QDIL5W:19572,19573,19574;R9PYYVDH:20112,20113,20114;RA0BIRUZ:24014,24015,24016;RADU0HKT:11609,11610,11611;RAIL6A59:14935,14936;RB4G6A1I:9360,9361,9363;RCLAWGJX:7426,7427,7428;RD4LZYW0:19665,19666;RENUD125:24053,24054,24055;RF9KYWSY:24382,24383;RFEZ25M9:23029,23030,23031;RJC433LQ:27109,27110,27111;RK4L2XRM:2427,2428,2429;RKM4A2WB:20085,20087;RM2OGXLP:4285,4286,4287;RM3XTABO:4618,4619,4620;RNEVNBLG:21930,21931,21932;ROHVD3MD:20228,20229,20230;ROWC4ZPG:20469,20471,20473;RP6QV2UG:19638,19639,19640;RQCLM4UY:24437,24438,24439;RQLBJWHG:2493,2494,2495;RRWJ50QK:6116,6117,6118;RSSGIOLT:27161,27162,27163;RSXI8J24:4439,4440,4441;RTBA4XP2:8879,8881;RTR0UJB3:27477,27478,27479;RTVILAMS:4759,4760,4761;RU9MP1SI:6265,6266,6267;RUQ25V8G:23418,23419,23420;RVCK6H69:25678,25679,25680;RVYN85E0:7061,7062,7063;RX2XG5UZ:21566,21567,21568;RYH45INM:1933,1934,1935;RYPG0XKB:128,129,130;RZ7G4WCS:4422,4423,4424;RZTG65JT:252,253,254;S00O8X6C:142,143,144;S2B9H1VA:20276,20278,20280;S2QNR2G8:21459,21460;S36UMYOD:15025,15026,15027;S4MKVSOF:25587,25588,25589;S53P2N17:962,963,964;S56FD3YI:20938,20939,20940;S6I76I5Z:19650,19651,19652;S6W3SGLH:21448,21449,21450;S74I3OYY:26600,26601,26602;S8BKB6FL:4412,4413,4414;S8NROICE:9387,9388,9389;S8YMR6YH:11551,11552,11553;S9760LNV:9399,9400,9401;SC58GWXX:11709,11710,11712;SCFSQH5A:14014,14015,14016;SCUZVTCD:20348,20349,20350;SCYKLY77:24319,24323;SE61ICEK:21943,21944,21945;SGH9QJ1V:27312,27313,27314;SGMDWFC8:24199,24200,24201;SI0FDAP1:17513,17514,17515;SJDMG47N:11630,11631,11632;SK7LKP1B:9408,9409,9410;SK7MKPAZ:20739,20740,20741;SKGHLSB8:1882,1883,1884;SLNKUZRA:6388,6389,6390;SMLTQHZD:1134,1135,1136;SN3I44JX:6521,6522,6523;SNDD1833:4401,4402,4403;SNYEXYR6:24359,24360,24361;SOX79BR1:17308,17309,17310;SQK8N3XF:2579,2580,2581;SS4I5EZW:17289,17292,17293;SSRSYV0B:15126,15127,15128;STDKDDT9:55,56,57;STR40VK3:24061,24062,24063;SUVPN4BH:4721,4723,4724;SUYYZVXP:7755,7756,7757;SV6TED6Z:6410,6411,6412;SVEZK89X:20345,20346,20347;SWDW99J5:7711,7713,7714;SWDZH7MB:15077,15078,15079;SWN5WF45:4379,4380,4381;SX0QOBEP:6504,6505,6506;SX51ZN2B:25971,25972,25973;SXJDHXKF:8016,8019;SXNVHYXL:7075,7076,7077;SY9WK12I:4865,4866,4867;SYPIFKLC:7995,7996,7997;T05X18EK:26099,26100,26101;T1CKQW77:20256,20257,20258;T210JNTQ:24023,24024,24025;T47ZI6GS:22149,22150;T4Q7NNKH:11651,11652,11653;T4ZQM532:9381,9382,9383;T6AQXNC4:21581,21582,21583;T6CEOCJE:7715,7716;T6IYD1W1:27919,27920,27922;T6VYFKQY:16104,16105,16106;T7WGSAOL:17008,17009,17010;T80TPX4Y:22062,22063,22064;T8CEJBSL:19522,19523,19524;T9L2E8YZ:16797,16798,16799;TAB8P9BG:20133,20134,20135;TBBP5VPJ:6278,6279,6280;TBLMRMC6:23217,23219,23220;TDR8CA3V:19590,19591,19592;TDXZ6NGR:23944,23945,23946;TEB86EF5:11381,11382,11383;TEJLIEID:17345,17346,17347;TEXTOJLH:27239,27242,27244;TEY7CMF6:9384,9385,9386;TFK7BD9K:17388,17391,29006;TGUBHQEH:22012,22013;TI1FYB0N:20391,20392,20393;TIXESE7R:14956,14957,14958;TKJ1E08X:7786,7787,7788;TL9AFW0O:4371,4373,4374;TLYNAYHS:70,71,72;TM0FR8C8:23938,23939,23940;TMS863YQ:17449,17450,17451;TN4ABBJ7:19470,19471,19474;TNQ94ZZI:20421,20422,20423;TNSJGF0S:12098,12099,12100;TNWG7B82:4395,4396,4397;TNZFB2FD:23044,23045,23046;TOCYJOZ3:9347,9348,9350;TQ5M3NKI:24250,24251,24252;TRJ5Y59U:23994,23995,23997;TSDKHYNF:4451,4452,4453;TSXMEIQY:25960,25961,25962;TT0LDTCX:28312,28313,28314;TT2G8RLO:17679,17680,17681;TTCHS7M4:20127,20128,20129;TU4T1J4R:27402,27403,27405;TU7917AM:27190,27191,27192;TUOKKC1Z:14100,14101,14102;TUXODSJQ:1596,1597,1598;TV282TM4:131,132,133;TVBYSZKS:19702,19703,19704;TVHICGXF:249,250,251;TW020RDX:6375,6376,6377;TWI85GXR:2552,2553,2554;TX6THRVK:22996,22997,22998;TXIM9I78:162,163,164;TXZ4Z0VC:21476,21477,21478;TZZ9WJ5G:7530,7531,7532;U06Q8JI9:187,188,189;U27QANPU:25996,25997,25998;U2I0BAKY:21426,21427,21428;U2MR1JAN:16042,16043,16044;U3FN35MU:181,182,183;U43BNSQW:7700,7701,7703;U4O5Q370:24309,24310,24312;U4QIN7P9:6268,6269,6270;U61PRYUZ:7976,7977,7978;U64U6LSO:4603,4604,4605;U6DV715T:11393,11394,11395;U7PSYCBY:21569,21570,21571;U7Q562NP:22014,22015,22016;U8739KRW:8841,8842,8843;UAT76PHG:27275,27276,27277;UBSIJYPW:9980,9982,9985;UCE4DF1D:17359,17360,17361;UD7190MW:7271,7272,7274;UDZ14VIW:27356,27357,27358;UEHSB544:17325,17326,17327;UEW1NKJJ:22044,22045,22046;UF2CNTD1:11107,11108,11109;UGORR1K6:9510,9511,9512;UH2FKU5P:193,194,195;UHSVF7CF:4308,4309,4310;UHVX3QH1:16032,16033,16035;UI2ACHOI:26010,26011,26012;UIAPNKNN:28255,28256,28257;UIKXBYP6:7629,7630,7631;UIQ27HHM:24508,24509,24510;UIVEOWYC:22053,22054,22055;UJ7MJ438:6490,6491,6492;UKGTBFNH:23987,23988,23989;UKPLYR0I:11750,11751,11752;UKUE86V3:27214,27215,27216;UKV9T1AR:21956,21957,21958;UMPMFNZS:1921,1922,1923;UN16IZHV:24173,24174,24175;UN7UYGLX:11563,11564,11565;UNQHXUMA:25966,25967,25968;UNXJP860:20281,20282,20283;UOQI7404:1897,1898,1899;UP5NHYED:6284,6285,6286;URCX3YN0:3594,3595,3596;URIA2CIG:14971,14972,14973;URM9H7DN:15063,15064,15065;US20MCSG:24241,24242,24243;USJHJKD8:111,112,113;USL9H5AJ:2358,2359,2360;UUAQQO7W:20418,20419,20420;UV0JWYBL:11373,11375,11377;UVIYCPZR:20026,20027,20028;UWHEEB39:26639,26640,26641;UX0Q5OR1:9539,9540,9541;UXBIOA5K:23798,23799,23800;UXIHQ9ST:4116,4117,4118;UY443H27:4269,4270,4273;UY4ODJOS:2443,2444,2445;UYZ4TONY:24026,24027,24028;UZ7HB9VH:11168,11169,11171;V02J741E:11624,11625,11626;V0I6GXJB:27421,27422,27423;V0QL8N3G:20383,20384;V0SKRKVC:27329,27330,27331;V1PLRGAM:20412,20413,20414;V1UZSR6U:25620,25621,25622;V36UT7AN:24154,24155,24156;V3KD6N0A:22151,22152,22153;V4ZT6YWU:24368,24369,24370;V58H35L3:7707,7708,7709;V5AVNAQ7:11417,11418,11419;V5TPLF0M:27895,27896,27897;V5TRCLJ8:16837,16839,16840;V5US1P4V:11112,11113,11114;V6ALAK8N:27451,27452,27453;V7XCM6KP:16851,16852,16853;V8XXMEIC:20240,20241,20242;V94ZYIRQ:20079,20080,20081;V9XQQN1L:27390,27391,27392;VD1SBQNT:7738,7739,7740;VD523E29:24286,24287,24288;VD72B0EW:16235,16236,16237;VD847TVB:2561,2562,2563;VFB0SQTN:7801,7802,7803;VFDAZLUY:6378,6380,6381;VFRHOV3Q:4660,4662,4664;VGOCC2K0:14026,14027,14028;VGOMR58U:7556,7557,7558;VHE3HXC3:4707,4709,4710;VHJAVXL5:27315,27316,27317;VIK8F0XF:20002,20003,20004;VIOEENU5:24202,24203,24204;VIOHDV8D:7589,7590,7591;VIPTF7IN:11615,11616,11617;VIQ3NW90:4382,4383,4384;VJ2TZCWI:7178,7182;VJNE2W88:21609,21610,21611;VKXHFSZO:17340,17341,17342;VMRYHJ4Q:23041,23042,23043;VNK6GU21:24599,24602,24604;VP0SXHVY:19708,19709,19710;VP0ZOOKA:17371,17372,17373;VPKKP2BX:27018,27019,27020;VQGDX0H1:27273,27274;VRBZSLP2:1157,1158,1159;VRQLOQ3N:16006,16007,16008;VSW01KRM:4342,4343,4345;VSWPYCTD:25645,25646,25647;VSXQY55I:25727,25728;VT4I9322:17596,17597,17598;VTOC1ADX:2183,2184,2185;VTVUQWO4:14814,14815,14818;VUBOUBEH:24221,24222,24223;VUTMXDGT:9885,9886,9887;VUWL9WH4:19859,19860,19861;VUYYG58K:11583,11584,11585;VV6FF88U:6560,6561,6562;VVGMC0QW:24341,24343;VVMO1423:11181,11183,11185;VVYU49JF:3624,3625,3626;VW135ZYW:34,35,36;VWC2AWXU:2606,2607,2608;VWX7KBDH:14833,14834,14835;VX5RZL6B:4650,4652,4656;VX8N6VEC:2370,2371,2372;VXO92JDO:21988,21989,21990;VXT0ATF6:151,152,153;VY0A78E0:26061,26062,26063;VZ7CTJKI:15905,15906,15907;W0WVI46F:4492,4493,4494;W1P4TZ4B:28283,28284,28285;W2APLGL3:14959,14960,14963;W3AM5JBJ:19099,19100,19101;W3FOB23A:15039,15040,15041;W3GO717J:10037,10038,10039;W404YVFF:7693,7694,7695;W4X5O4KV:24327,24328,24329;W56A3XJ3:2242,2243,2244;W5BQWAG8:11477,11478,11479;W74B497A:2483,2484,2485;W79RISV0:23476,23478;W7GLCQVI:11423,11424,11425;W7T6LZX7:20008,20009,20010;W8XBSEJT:11349,11350,11351;W8YA91ZK:244,246,248;W9OTU03E:22050,22051,22052;WAI4VH68:1918,1919,1920;WASYQROW:3651,3652,3653;WB8MQBHU:6130,6131,6132;WC4VADON:25608,25609,25610;WCNEHLL1:28136,28137,28138;WDQE9LS3:19699,19700,19701;WECT3RIT:7114,7116,7118;WF5TA3HB:21497,21498;WF7A6FHO:10001,10004,10005;WFPLL1KR:19687,19688,19689;WG6J4YO9:17265,17266,17267;WGNB8ADV:4643,4644,4645;WHX1AG4T:6113,6114,6115;WIA7ITRD:20300,20302,20304;WJ8NY16C:7122,7124;WMRYXYM3:1000122,1000136,1000253;WN35O98C:4186,4187,4188;WNOJM912:21485,21486,21487;WNON7SJK:9402,9403,9404;WO5IQTLW:19575,19577,19579;WOPF65BX:1924,1925,1926;WP1JTJ12:26107,26108,26109;WP2XNWD6:20319,20320,20321;WPGZK930:4501,4502,4504;WPSKU3QA:27426,27428,27429;WPX95FH3:27040,27041,27042;WQ0XANEW:19460,19461,19462;WQAD7SIS:27056,27057,27058;WQC4QCGC:26110,26111,26112;WQOL8HJG:19452,19453,19454;WSSZ9J0W:2453,2454,2455;WTDF2NWA:19010,19011,19012;WTRGB7W4:16110,16112;WU5ATPU3:16830,16831,16832;WUMCX9TP:8848,8849,8850;WUMJMKOF:24344,24345,24346;WUQR2TXZ:26087,26088,26089;WUTV4EWO:19006,19007,19008;WVHNXRH8:9435,9436,9437;WVIVROKA:22984,22985,22986;WVMPHHDQ:4278,4280,4281;WWCZTMVK:24088,24089,24090;WWSM4TI0:6262,6263,6264;WYU5W2JD:25724,25725,25726;WZTCQC00:11429,11430,11431;X0U0B171:20491,20493,20495;X1P5U150:1962,1963,1964;X1RR6QUW:27418,27419,27420;X2714E92:17027;X34WN5XK:7652,7653,7654;X3BFH2GS:16785,16786,16787;X3NWQ2MK:23233,23234,23235;X3VTVAHB:18080,18081,18082;X53YW5IP:139,140,141;X5O9BIM3:20082,20083,20084;X783FQFX:24095,24096,24097;X78L3DND:15870,15871,15872;X81N8PVH:27034,27035,27036;X89SXIQZ:11547,11549,11550;X8YOD0FK:7423,7424,7425;X9CMKHIE:27261,27262,27263;X9S2R604:27288,27289,27290;XAEYY42I:274,275,276;XARY95AG:16559,16560,16561;XB9141JL:21429,21430,21431;XBGMB7XP:14912,14914,14916;XBXM90PX:6422,6423,6424;XC76JB1X:7772,7773,7774;XCDJKV5G:4320,4322,4323;XCI5MCF1:6136,6137,6139;XFOZFXSX:1353,1354,1355;XGTOEK0V:25630,25631,25632;XH2TQ1CH:11586,11587,11588;XH5KZ9LI:24590,24592;XH9K681O:4189,4190,4191;XHCYJN7C:15988,15989,15990;XJ65R80W:20041,20042,20043;XJ94X1RN:4841,4842,4843;XKT0XLM0:24356,24357,24358;XL3XTGGY:21975,21976,21977;XNK4HVYF:6512,6513,6514;XO7IV6GV:20170,20172,20174;XQ8W9BZI:20675,20676,20677;XQO7FN0I:27231,27232,27233;XR6SJG85:27094,27095,27096;XRQ1NZ50:20745,20746,20747;XSNUX2O7:9299,9301,9302;XSQ4OB73:2394,2395,2396;XUT6AJMT:24044,24045,24046;XVCNVCD2:1107,1108,1109;XW3QZA6M:27454,27456;XWR4O58X:27150,27151,27152;XXJFQFI3:24266,24268,24270;XXVPHABV:14097,14098,14099;XYEJW1HI:26005,26006,26007;XZ4E5MS6:10048,10049,10050;Y03LMI61:2477,2478,2479;Y294GLY7:11352,11353,11354;Y2RGON9O:9986,9987,9988;Y3DLWQ7O:15876,15877,15878;Y4OO983I:15911,15912;Y7I8TSC9:23409,23410,23411;Y8O4NJSY:3660,3661,3662;YAC24V2K:7595,7596,7597;YAIFQFSX:4262,4263,4264;YAJMECGY:27953,27954,27956;YAXAY7HQ:934,935,936;YB3C5LX5:19540,19541,19542;YC8G8VZ9:12124,12125,12126;YCBFN5DS:27430,27431,27432;YCNVVLK1:4122,4123,4124;YDX41M2F:24073,24074,24075;YEUKB2IQ:17337,17338,17339;YFF3BE0E:6337,6338,6339;YFG56M7O:11480,11481,11482;YFHG0850:19137,19138,19139;YFSLMGEC:19719,19720,19721;YFW9EVEI:20394,20395,20396;YFYEUA0U:4505,4506,4507;YG4ZZJ4Z:19725,19726,19727;YH5HP2QP:1915,1916,1917;YI25Y3TH:27548,27549,27550;YJ2Z9R1O:16299,16300,16302;YJEJEM6Z:25617,25618,25619;YJGOUQVU:20032,20033,20034;YKN8V5GT:19616,19617,19618;YLAVM0I7:26071,26073,26075;YM69JZI5:19555,19556,19557;YMEKXZK3:11668,11669,11671;YON2Q29J:19608,19609,19610;YP3CF98R:6394,6395;YPNDHILU:1060,1062,1063;YPNRFNS1:16303,16304;YPZK1MDB:4205,4206,4207;YQ49KB7X:20356,20357,20358;YQADK696:11360,11361,11362;YQOXF0Q1:16803,16804,16805;YRMAHAM3:4274,4275,4276;YS03CFJ9:1110,1111,1112;YSOX4N12:2354,2355,2356;YSPP69QC:23337,23338,23339;YTU92H6F:7617,7618,7619;YVAXRV6O:1078,1079,1080;YVE4J5HH:20371,20372,20373;YVGVOTOT:20237,20238,20239;YX1KZRCZ:3597,3598,3599;YZ1B0Q44:4857,4859,4861;YZENR70O:24017,24018,24019;YZNYLXAF:21623,21624,21625;Z0ARUJPP:11515,11517,11519;Z0BDVNBZ:4541,4543,4546;Z0FC7PJC:11438,11439,11440;Z0PQ82KA:5004,5005,5006;Z17SL154:16090,16091,16092;Z1JZHATZ:235,236,237;Z26YWUJV:28142,28143,28144;Z2MGHSU5:22987,22988,22989;Z3O8WHR1:12018,12019,12020;Z41742PX:7290,7291,7292;Z4AQ3TZN:14020,14021,14022;Z4DY2ISS:25908,25909,25910;Z5YAX0QP:25754,25755,25756;Z603ZEAU:7256,7257,7258;Z7ISG8YE:27074,27075,27076;Z7SO8H1E:14991,14992,14993;Z8C7KQMG:1950,1951,1952;Z8PN1KUX:1885,1886,1887;Z9JB6B3P:6466,6467,6468;Z9VVPOG6:14980,14981,14982;Z9W6R57H:28126,28128;ZAN3Y0YN:11627,11628,11629;ZAUS9SXH:7278,7279,7280;ZBP2LMWP:27491,27492,27493;ZBSGE12I:11621,11622,11623;ZC6T2OUW:15046,15047,15048;ZCAUB4YG:27091,27092,27093;ZD51BM7G:23034,23035,23036;ZEQQ37M0:27318,27319,27320;ZETGTUV4:1000076,1000138,1000255;ZETH4WI9:24371,24372,24373;ZFLFAQ0T:17461,17462;ZGY9VWTQ:22022,22023,22025;ZH58NLKV:11124,11125,11126;ZH92AQUY:17019,17020;ZHLNO5RZ:4612,4613,4614;ZIL1BV24:24118,24119,24120;ZIVFVUDG:16208,16209,16210;ZJNL8QTH:11543,11544,11545;ZJVJ5U6P:2555,2556,2557;ZK78Y1B7:27043,27045;ZK8GGVPC:1092,1093;ZKOJSRJR:6428,6429,6430;ZLY1CLKF:2167,2168,2170;ZM4C6XD4:1094,1095,1096;ZM9G2P2N:26636,26637,26638;ZMB8FCMG:27258,27259,27260;ZMQZSE9Q:4670,4671,4673;ZN47FIR7:1100,1102,1106;ZNGS1WAU:26002,26003,26004;ZOJDHHL9:3720,3721,3723;ZPFPYYLY:2367,2368,2369;ZR6B25ZB:7690,7691,7692;ZRCRLVXZ:6694,6695,6696;ZRHW9SPU:11355,11357,11359;ZU2VWX2G:27347,27348,27349;ZUKKVTH1:25746,25747,25748;ZVMTVY7M:21950,21951,21952;ZW1M74N0:11435,11436,11437;ZWQZL32J:27200,27201,27202;ZXLFUP4A:44;ZXR866O4:923,924,925;ZXTB269A:17247,17248,17249;ZY6JULC4:6615,6616,6617;ZYVO6KK1:16015,16016;ZZ70QOTJ:7899,7900,7901;ZZDUWIUA:2517,2518,2519;ZZHASC7S:5021,5024;ZZL6H37I:27068,27069,27070;a14cde7f:21473,21474,21475;a1b5a834:6176,6177,6178;a1e455f8:6182,6184;a2095b9f:29030,30732;a2214d9f:965,966,967;a2b6e193:21505,21506;a410dd79:14038,14039,14040;a49d96ef:28227,28228,28229;a52a2026:30649,30728;a5480fb7:15856,15857,30655;a56ce827:30828,1000246;a57353f9:30671,30672,30773;a5cb141f:6172;a6ae15b1:21443,21444,21445;a6d41ca1:28941,28972,30846;a75aef8c:15854,15855;a89cbbdd:3693,3694;a8aaeb2b:;a8b6c8cc:14044,14046;a8c54a8f:952,953,954;a90396a7:18997,18998,18999;aab26f5d:1014,1015,1016;ab46403f:20061,20062,20063;ab7a374e:11115,11116,11117;ab968616:7109,7110;abd4b2f2:25681,25682,25683;ac50d162:1580,1581,1582;ac55af23:28957,30667;ad8681cd:2192,2193,2194;afd672fa:23329,23331;b0776a7e:28890,28891,30694;b1ace455:16101,16102,16103;b1b0d2cc:28726,28727,28993;b2334671:28635,28637;b28a56bc:28570,28571,28572;b43cb39d:28919,28920,1000310;b4c3d482:23803,23804,23805;b4cbb54d:20246,20248,20249;b502bdc8:1003,1004,1005;b57839d6:28663,28664,28665;b628d12b:20166,20167,20168;b68c04af:28899,28962;b6ddee9b:29032;b74e5378:28717,28718,30673;b7620d96:25993,25994,25995;b7aa3cf9:9841,9842,9843;b7aabaf3:24001,24002,24003;b7ce3671:28843,28844,28955;ba54cb6c:1006,1007,1008;bae71264:17124,17125,17126;bb7c101c:984,985,986;bce3d047:28576,28577,28578;bdb1d881:28677,28678,28679;bdb548a3:21551,21552,21553;bead5c67:7111,7112,7113;bebb337f:28819,28820,28821;beeaf847:28547,28548,30762;bef252f4:28858,28859,28860;bf277762:6364,6365,6366;bf303c82:24390,24391,24392;bfdfe3a0:28703,28704;c08ff7cb:3677,3678,3679;c0a73edd:28611,28612,28613;c13da218:6168,6169,6170;c196d814:9334,9335,9336;c3780906:6291,6292;c4522482:28171,28172,28173;c48c81e0:11155,11156,11157;c52fac99:25593,25594,25595;c5b51b75:25693,25694,25695;c5e267b6:28874,28875,30800;c610ee3f:20038,20039,20040;c67855b1:25846,25847;c6c8bc29:28761,28763,30819;c6ea97ca:28337,28338,28339;c7ecdf98:28207,28208,28209;c9136f21:28630,28632,30749;cb3de0a2:1011,1012,1013;cbc5a95b:28549,28550,28551;cc33cc38:23330,23332,28965;cc7e0367:16812,16813,16814;ccbbf3c8:24011,24012,24013;cd17dcd4:15873,15874,15875;cd3303c8:28661,28662;ce4986d9:25686,25687,25688;cf0b11a5:7432,7433,7434;cf2914ec:28749,28750,28751;cf44fe75:19040,19041,19042;cf491d4a:7102,7103,7104;cf79d46b:3615,3616,3617;d04a2488:19411,19412,19413;d056e2db:28835,28836,30724;d07aa54c:28651,28652,28653;d1484acb:14041,14042,14043;d1cb8dd7:28831,28832,28834;d1cbf239:14903,14904,14905;d3c96dd6:16782,16783,16784;d4339325:28220,28221,28222;d47d6790:3690,3691,3692;d49969e0:28594,28595,28596;d4ce2304:28947,30662;d4d38980:28752,28753,28754;d57e7da9:28638,28958,30807;d6479b93:28210,28211,28212;d6f57a72:1018;d76abf43:28688,28689,28690;d77d9ae1:28951,30780;d7c432fe:28746,28747,28748;d810369c:28202,28203,28204;d85b9e8d:21467,21468,21469;d8d42dbd:28561,28562,28563;d9a0630c:28625,28626,30834;d9d8e7be:28722,28723,30652;da3ee904:8861,8862,8863;da7f9290:15898,15899,15900;da9b4a05:7503,7504,7505;db173f65:21507,21508,21509;dbb75100:6153,6154,6155;dc17c839:16931,16932,16933;de930281:14510,14511,14512;deb987f1:20005,20006,20007;df0ce30c:23802,28952,30813;df7c70df:24176,24177,24178;dfe48dde:926,927;e07b051d:23004,23005,23006;e1e5b9af:28909,28910,30710;e282e059:14053,30711;e2d0bda2:30679,30766;e3e2e53a:23892,1000005,1000007;e44619b0:28816,28817,28818;e48a523c:24005,24006,24007;e6965776:28654,28655,28656;e7d28a7c:28730,28732,30695;e9260960:11146,11147,11148;e9525d76:7106,7107;e966a307:28700,28702,1000314;e9c2f197:24047,24048;ea546cc2:28768,28769,28770;eab17b23:2204,2205,2206;eb077729:8888,8889;eb72f869:994,995,996;ee1e47a2:21536,21537,21538;ef08b63a:990,30666,30844;f00057ea:9859,9860,9861;f023c1d4:6166,6167;f02dc184:25715,25716,25717;f02de336:28794,28795;f0b601b5:28863,28864,30689;f0d731fa:28865,28866,30781;f0ec39fc:28841,28842,30782;f1aedc01:28966,29001;f22d8269:19583,19584,29023;f276bd71:21524,21525,21526;f46de18b:28129,28130,28131;f4e5d6dd:28694,28695,30657;f5fe8a6c:11149,11150;f60afee4:28714,28715,28716;f85babee:28885,28969,30799;f930e4e9:11158,11159,11160;fa73bf9a:19502,19503,19504;fa891570:28591,28592,28593;fa8f6fa8:19025,30709;fadf8c6c:28191,28192,28194;fb243db5:30747;fbd1ec5f:28213,28215,28216;fc0e9e4a:28579,28580,28581;fe36a16f:6185,30750,1000323;fe80ac95:6110,6111', ';'));
create temporary table a1_lignes (id_unique text primary key) on commit drop;
insert into a1_lignes select split_part(x, ':', 1) from a1_m;
create temporary table a1_pieces (id_unique text, piece bigint) on commit drop;
insert into a1_pieces select split_part(x, ':', 1), p::bigint
  from a1_m cross join lateral unnest(string_to_array(split_part(x, ':', 2), ',')) p
 where p <> '';
do $$
declare n int;
begin
  select count(*) into n from public.app_classeur_avis a where not exists (select 1 from a1_lignes g where g.id_unique = a.id_unique);
  if n <> 0 then raise exception '⛔ A1 G2 : % avis hors de la liste des lignes', n; end if;
  select count(*) into n from a1_pieces p where not exists (select 1 from public.app_affaire_ledger l where l.app_affaire_id = p.piece);
  if n <> 0 then raise exception '⛔ A1 G2 : % piece(s) de la liste absentes du registre', n; end if;
end $$;
-- LA CIBLE : une etiquette parmi les vraies pieces de la ligne -> elle ; plusieurs ou aucune -> VIDE
create temporary table a1_cible on commit drop as
select g.id_unique, case when count(distinct l.app_dossier_uuid) = 1 then min(l.app_dossier_uuid::text)::uuid end as uuid
  from a1_lignes g left join a1_pieces p on p.id_unique = g.id_unique
  left join public.app_affaire_ledger l on l.app_affaire_id = p.piece
 group by g.id_unique;
alter table a1_cible add column numero text;
update a1_cible c set numero = (select l.app_dossier_numero from public.app_affaire_ledger l
                                 where l.app_dossier_uuid = c.uuid and l.app_dossier_numero is not null limit 1)
 where c.uuid is not null;
create table public.app_classeur_avis_reflets_avant_a1vague_20261125 as
  select id_unique, app_dossier_uuid, app_dossier_numero, now() as copie_le from public.app_classeur_avis;
revoke all on public.app_classeur_avis_reflets_avant_a1vague_20261125 from public, anon, authenticated;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, valeur, ancienne_valeur, ligne_origine, lot_origine, pourquoi, ecrit_par)
select 'a1_vague_2026-11-25', row_number() over (order by a.id_unique), 'reflet', 'app_classeur_avis (app_dossier_uuid, app_dossier_numero)',
       'RAFRAICHIR LE REFLET (A1)', coalesce((select min(p.piece) from a1_pieces p where p.id_unique = a.id_unique), 0),
       coalesce(c.numero, 'VIDE') || ' ' || coalesce(c.uuid::text, '-'),
       coalesce(a.app_dossier_numero, 'VIDE') || ' ' || coalesce(a.app_dossier_uuid::text, '-'), a.id_unique,
       'A1 (passage 82, image 2026-11-25_072625)',
       'SON MOT du 24/11 : un reflet n''est pas une cle -- le reflet suit les vraies pieces de la ligne (une etiquette -> elle ; plusieurs ou aucune -> VIDE)',
       'patch_a1_vague'
  from public.app_classeur_avis a join a1_cible c on c.id_unique = a.id_unique
 where a.app_dossier_uuid is distinct from c.uuid or a.app_dossier_numero is distinct from c.numero;
update public.app_classeur_avis a set app_dossier_uuid = c.uuid, app_dossier_numero = c.numero
  from a1_cible c
 where c.id_unique = a.id_unique and (a.app_dossier_uuid is distinct from c.uuid or a.app_dossier_numero is distinct from c.numero);
do $$
declare n int; j int;
begin
  select count(*) into n from public.app_classeur_avis a join a1_cible c on c.id_unique = a.id_unique
   where a.app_dossier_uuid is distinct from c.uuid or a.app_dossier_numero is distinct from c.numero;
  if n <> 0 then raise exception '⛔ A1 controle : % reflet(s) d''avis encore decolle(s)', n; end if;
  select count(*) into j from public.app_classeur_realignement_journal where lot = 'a1_vague_2026-11-25';
  select count(*) into n from public.app_classeur_avis a join public.app_classeur_avis_reflets_avant_a1vague_20261125 s using (id_unique)
   where a.app_dossier_uuid is distinct from s.app_dossier_uuid or a.app_dossier_numero is distinct from s.app_dossier_numero;
  if n <> j then raise exception '⛔ A1 controle : % reflet(s) change(s) pour % ligne(s) au journal', n, j; end if;
  if 107 >= 0 and j <> 107 then
    raise exception '⛔ A1 controle : % ecriture(s) au lieu des 107 mesurees par l''essai a blanc complet', j; end if;
  raise notice '✅ A1 : % reflet(s) d''avis rafraichi(s), tous au journal ; 0 decolle', j;
end $$;


-- ═══ A3 : LE REFLET DE CHAINE DES NOTES ET DES CONDITIONS, PAR LA TRANSACTION -- lot a3_vague_2026-11-25 ═════════════════
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_note_reflets_avant_a3vague_20261125') is not null then
    raise exception '⛔ A3 G0 : la sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'a3_vague_2026-11-25';
  if n <> 0 then raise exception '⛔ A3 G0 : % ligne(s) du lot deja au journal', n; end if;
  select count(*), md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id), ';' order by app_affaire_id), '')) into n, e from public.app_affaire_note;
  if n <> 4524 or e <> '174ab8ac5e52d6b3910153299b82e2c5' then
    raise exception '⛔ A3 G1 : les notes ont change depuis la fabrication (% , %)', n, e; end if;
  select count(*), md5(coalesce(string_agg(concat_ws('|', app_affaire_id, rang, app_chaine_id), ';' order by app_affaire_id, rang), '')) into n, e from public.app_affaire_condition;
  if n <> 33 or e <> '1a303f39ab051366587a0c2fc936b5af' then
    raise exception '⛔ A3 G1 : les conditions ont change depuis la fabrication (% , %)', n, e; end if;
end $$;
create table public.app_affaire_note_reflets_avant_a3vague_20261125 as
  select app_affaire_id, app_chaine_id, now() as copie_le from public.app_affaire_note;
create table public.app_affaire_condition_reflets_avant_a3vague_20261125 as
  select app_affaire_id, rang, app_chaine_id, now() as copie_le from public.app_affaire_condition;
revoke all on public.app_affaire_note_reflets_avant_a3vague_20261125, public.app_affaire_condition_reflets_avant_a3vague_20261125
  from public, anon, authenticated;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_app_chaine_id, vers_app_affaire_id, vers_app_chaine_id, valeur,
   ancienne_valeur, lot_origine, pourquoi, ecrit_par)
select 'a3_vague_2026-11-25', row_number() over (order by t, a, r), 'reflet', colonne, 'RAFRAICHIR LE REFLET (A3)', a, avant, a,
       apres, coalesce(apres::text, '-'), coalesce(avant::text, '-'), 'A3 (passage 82, image 2026-11-25_072625)',
       'SON MOT du 24/11 : un reflet n''est pas une cle -- le reflet de chaine suit la transaction (le registre)', 'patch_a3_vague'
  from (select 1 t, n.app_affaire_id a, 0 r, 'app_affaire_note.app_chaine_id' colonne, n.app_chaine_id avant, l.app_chaine_id apres
          from public.app_affaire_note n join public.app_affaire_ledger l on l.app_affaire_id = n.app_affaire_id
         where n.app_chaine_id is distinct from l.app_chaine_id
        union all
        select 2, c.app_affaire_id, c.rang, 'app_affaire_condition.app_chaine_id (rang ' || c.rang || ')', c.app_chaine_id, l.app_chaine_id
          from public.app_affaire_condition c join public.app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id
         where c.app_chaine_id is distinct from l.app_chaine_id) x;
update public.app_affaire_note n set app_chaine_id = l.app_chaine_id from public.app_affaire_ledger l
 where l.app_affaire_id = n.app_affaire_id and n.app_chaine_id is distinct from l.app_chaine_id;
update public.app_affaire_condition c set app_chaine_id = l.app_chaine_id from public.app_affaire_ledger l
 where l.app_affaire_id = c.app_affaire_id and c.app_chaine_id is distinct from l.app_chaine_id;
do $$
declare n int; j int;
begin
  select count(*) into n from public.app_affaire_note n join public.app_affaire_ledger l on l.app_affaire_id = n.app_affaire_id
   where n.app_chaine_id is distinct from l.app_chaine_id;
  if n <> 0 then raise exception '⛔ A3 controle : % note(s) au reflet faux', n; end if;
  select count(*) into n from public.app_affaire_condition c join public.app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id
   where c.app_chaine_id is distinct from l.app_chaine_id;
  if n <> 0 then raise exception '⛔ A3 controle : % condition(s) au reflet faux', n; end if;
  -- les notes dont la transaction n'est plus au registre : NOMMEES, pas touchees
  select count(*) into n from public.app_affaire_note n
   where not exists (select 1 from public.app_affaire_ledger l where l.app_affaire_id = n.app_affaire_id);
  if n <> 6 then raise exception '⛔ A3 controle : % note(s) sans transaction au lieu de 6 (1001388, 1001389, 1001391, 1001392, 1001394, 1001395)', n; end if;
  select count(*) into j from public.app_classeur_realignement_journal where lot = 'a3_vague_2026-11-25';
  select (select count(*) from public.app_affaire_note n join public.app_affaire_note_reflets_avant_a3vague_20261125 s using (app_affaire_id)
           where n.app_chaine_id is distinct from s.app_chaine_id)
       + (select count(*) from public.app_affaire_condition c join public.app_affaire_condition_reflets_avant_a3vague_20261125 s
           using (app_affaire_id, rang) where c.app_chaine_id is distinct from s.app_chaine_id) into n;
  if n <> j then raise exception '⛔ A3 controle : % reflet(s) change(s) pour % ligne(s) au journal', n, j; end if;
  if 269 >= 0 and j <> 269 then
    raise exception '⛔ A3 controle : % ecriture(s) au lieu des 269 mesurees par l''essai a blanc complet', j; end if;
  raise notice '✅ A3 : % reflet(s) de chaine rafraichi(s) (notes et conditions), tous au journal ; 0 faux', j;
end $$;

create temporary table vab_milieu on commit drop as select
  (select count(*) from public.app_affaire_repartition) n_rep, (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition) e_rep,
  (select count(*) from public.app_affaire_repartition_mise_de_cote) n_mdc,
  (select count(*) from public.app_classeur_realignement_journal) n_j,
  (select md5(coalesce(string_agg(concat_ws('|', id_unique, app_dossier_uuid, app_dossier_numero), ';' order by id_unique), '')) from public.app_classeur_avis) e_av, (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id), ';' order by app_affaire_id), '')) from public.app_affaire_note) e_no,
  (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, rang, app_chaine_id), ';' order by app_affaire_id, rang), '')) from public.app_affaire_condition) e_co,
  (select count(*) from public.app_affaire_note n join public.app_affaire_ledger l on l.app_affaire_id = n.app_affaire_id where n.app_chaine_id is distinct from l.app_chaine_id) no_faux, (select count(*) from public.app_affaire_condition c join public.app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id where c.app_chaine_id is distinct from l.app_chaine_id) co_faux, (select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l where l.app_chaine_id = r.app_chaine_id)) orph, (select coalesce(string_agg(c::text, ',' order by c), '') from (
    select distinct l.app_chaine_id c from public.app_affaire_ledger l
     where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null
       and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) x) vr,
  (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id, app_dossier_uuid, app_dossier_numero), ';'
           order by app_affaire_id), '')) from public.app_affaire_ledger) e_lab,
  (select md5(coalesce(string_agg(concat_ws('|', annee, dernier), ';' order by annee), '')) from public.app_dossier_numero_compteur) e_cpt;

create temporary table vab_lots on commit drop as
  select lot, count(*) n from public.app_classeur_realignement_journal
   where lot in ('a2_vague_2026-11-25', 'a1_vague_2026-11-25', 'a3_vague_2026-11-25') group by lot;
-- ─── 6. LES INVERSES ──────────────────────────────────────────────────────────────────────────────────────────────

-- ═══ L'INVERSE D'A3 PUIS D'A1 : les reflets reprennent leur valeur sauvegardee, le journal des deux lots est retire ═══
update public.app_affaire_note n set app_chaine_id = s.app_chaine_id from public.app_affaire_note_reflets_avant_a3vague_20261125 s
 where s.app_affaire_id = n.app_affaire_id and n.app_chaine_id is distinct from s.app_chaine_id;
update public.app_affaire_condition c set app_chaine_id = s.app_chaine_id
  from public.app_affaire_condition_reflets_avant_a3vague_20261125 s
 where s.app_affaire_id = c.app_affaire_id and s.rang = c.rang and c.app_chaine_id is distinct from s.app_chaine_id;
update public.app_classeur_avis a set app_dossier_uuid = s.app_dossier_uuid, app_dossier_numero = s.app_dossier_numero
  from public.app_classeur_avis_reflets_avant_a1vague_20261125 s
 where s.id_unique = a.id_unique and (a.app_dossier_uuid is distinct from s.app_dossier_uuid
                                      or a.app_dossier_numero is distinct from s.app_dossier_numero);
delete from public.app_classeur_realignement_journal where lot in ('a1_vague_2026-11-25', 'a3_vague_2026-11-25');
do $$
declare n int;
begin
  select count(*) into n from public.app_classeur_avis a join public.app_classeur_avis_reflets_avant_a1vague_20261125 s using (id_unique)
   where a.app_dossier_uuid is distinct from s.app_dossier_uuid or a.app_dossier_numero is distinct from s.app_dossier_numero;
  if n <> 0 then raise exception '⛔ inverse A1 : % avis differents de la sauvegarde', n; end if;
  select count(*) into n from public.app_affaire_note n join public.app_affaire_note_reflets_avant_a3vague_20261125 s using (app_affaire_id)
   where n.app_chaine_id is distinct from s.app_chaine_id;
  if n <> 0 then raise exception '⛔ inverse A3 : % notes differentes de la sauvegarde', n; end if;
  raise notice '✅ inverse A1 et A3 : les reflets sont revenus a la sauvegarde';
end $$;


-- ─── LE RETOUR ARRIERE : les parts du lot retirees, les mises de cote remises EN PLACE, le journal du lot retire ─────
do $$
declare n int;
begin
  if to_regclass('public.app_affaire_repartition_avant_a2vague_20261125') is null then raise exception '⛔ inverse : la sauvegarde app_affaire_repartition_avant_a2vague_20261125 est absente'; end if;
  select count(*) into n from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_a2_vague_2026-11-25';
  if n <> 143 then raise exception '⛔ inverse : % mise(s) de cote du lot au lieu de 143', n; end if;
end $$;
delete from public.app_affaire_repartition where ecrit_par like 'a2_vague_2026-11-25:%';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select ancien_app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_a2_vague_2026-11-25';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_a2_vague_2026-11-25';
delete from public.app_classeur_realignement_journal where lot = 'a2_vague_2026-11-25';
do $$
declare n int;
begin
  -- la table est revenue EXACTEMENT a la sauvegarde, dans les deux sens
  select count(*) into n from (
    (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_a2vague_20261125
     except all
     select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition)
    union all
    (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition
     except all
     select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_a2vague_20261125)) z;
  if n <> 0 then raise exception '⛔ inverse : % part(s) differente(s) de la sauvegarde', n; end if;
  raise notice '✅ inverse : la repartition est revenue a la sauvegarde, la mise de cote et le journal du lot sont vides';
end $$;

-- ─── 7. TOUT EST-IL REVENU ? puis l'erreur VOULUE, qui annule tout ────────────────────────────────────────────────
create temporary table vab_fin on commit drop as select
  (select count(*) from public.app_affaire_repartition) n_rep, (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition) e_rep,
  (select count(*) from public.app_affaire_repartition_mise_de_cote) n_mdc,
  (select count(*) from public.app_classeur_realignement_journal) n_j,
  (select md5(coalesce(string_agg(concat_ws('|', id_unique, app_dossier_uuid, app_dossier_numero), ';' order by id_unique), '')) from public.app_classeur_avis) e_av, (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id), ';' order by app_affaire_id), '')) from public.app_affaire_note) e_no,
  (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, rang, app_chaine_id), ';' order by app_affaire_id, rang), '')) from public.app_affaire_condition) e_co,
  (select count(*) from public.app_affaire_note n join public.app_affaire_ledger l on l.app_affaire_id = n.app_affaire_id where n.app_chaine_id is distinct from l.app_chaine_id) no_faux, (select count(*) from public.app_affaire_condition c join public.app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id where c.app_chaine_id is distinct from l.app_chaine_id) co_faux, (select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l where l.app_chaine_id = r.app_chaine_id)) orph, (select coalesce(string_agg(c::text, ',' order by c), '') from (
    select distinct l.app_chaine_id c from public.app_affaire_ledger l
     where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null
       and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) x) vr,
  (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id, app_dossier_uuid, app_dossier_numero), ';'
           order by app_affaire_id), '')) from public.app_affaire_ledger) e_lab,
  (select md5(coalesce(string_agg(concat_ws('|', annee, dernier), ';' order by annee), '')) from public.app_dossier_numero_compteur) e_cpt;

do $$
declare a record; v record; m record; f record; p text; l text;
begin
  select * into a from vab_avant;
  select * into v from vab_vague;
  select * into m from vab_milieu;
  select * into f from vab_fin;
  select string_agg(geste || ' ' || dossiers || ' dossiers / ' || lignes || ' lignes', ' ; ') into p from vab_pose;
  select string_agg(lot || ' ' || n, ' ; ' order by lot) into l from vab_lots;
  if f.n_rep <> a.n_rep or f.e_rep <> a.e_rep or f.n_mdc <> a.n_mdc or f.n_j <> a.n_j or f.e_av <> a.e_av
     or f.e_no <> a.e_no or f.e_co <> a.e_co then
    raise exception '⛔ A BLANC COMPLET : les inverses n''ont pas tout rendu (parts %/%, mise de cote %/%, journal %/%, avis %, notes %, conditions %)',
      f.n_rep, a.n_rep, f.n_mdc, a.n_mdc, f.n_j, a.n_j, f.e_av = a.e_av, f.e_no = a.e_no, f.e_co = a.e_co;
  end if;
  raise exception 'A BLANC COMPLET VERT -- RIEN N''EST ECRIT (annulation voulue). AVANT : % parts (%), mise de cote %, journal %, notes fausses %, conditions fausses %, orphelines %. LA POSE DES ETIQUETTES : %. APRES LA VAGUE SANS REMEDE : notes fausses %, conditions fausses %, orphelines %, ventes reglees sans part [%]. APRES A2+A1+A3 : % parts, empreinte des parts %, notes fausses %, conditions fausses %, orphelines %, ventes reglees sans part [%], mise de cote %, journal % (%). APRES LES INVERSES : = AVANT (parts, mise de cote, journal, avis, notes, conditions).',
    a.n_rep, left(a.e_rep, 8), a.n_mdc, a.n_j, a.no_faux, a.co_faux, a.orph, p, v.no_faux, v.co_faux, v.orph, v.vr,
    m.n_rep, m.e_rep, m.no_faux, m.co_faux, m.orph, m.vr, m.n_mdc, m.n_j, l;
end $$;
