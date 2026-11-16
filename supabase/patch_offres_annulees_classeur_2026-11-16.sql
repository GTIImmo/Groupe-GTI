-- ════════════════════════════════════════════════════════════════════════════
-- C5 / LOT B -- LES 96 OFFRES « ANNULEE » DU CLASSEUR
-- 16/11/2026 . chantier classeur, tache 3.3 lot B . genere par
-- phase2/checks/poser_offres_annulees_classeur_2026-11-16.py
-- ════════════════════════════════════════════════════════════════════════════
--
-- CE QU'ON POSE : 96 offres que le classeur porte et que nous n'avons pas, dont
--   l'etat au classeur est « Annulee ». Elles entrent en `state = 'refused'`, donc
--   AUCUNE des 4 regles de chainage ne se declenche -- c'est exactement le cas
--   eprouve en reel par l'essai A2 dans la nuit du 15 au 16/11.
--
-- ⛔ LA MARQUE EST DANS LE MEME INSERT (piece 1) : `transaction_origine = 'classeur'`.
--   Une ligne du classeur DEMARQUEE, meme une seconde, et le filet du worker lui
--   collerait le numero d'une transaction Hektor EXISTANTE.
--
-- ⛔ NI acquereurs_json NI mandants_json : le nom de l'acquereur va dans
--   app_affaire_note (origine 'classeur'), decision de Frederic du 16/11. Sans eux,
--   le declencheur app_affaire_partie_suivre ne cree aucune partie, et la regle [D]
--   « meme acheteur -> dossiers reunis » ne peut pas jouer.
--
-- LE NUMERO EST FRAPPE PAR SUPABASE : nextval('app_affaire_id_app_seq').
-- LE RATTACHEMENT (chaine, dossier, annonce) est PRIS sur la transaction que le gel
--   relie deja a la meme ligne du classeur -- rien n'est devine.
--
-- RETOUR ARRIERE : patch_offres_annulees_classeur_2026-11-16_INVERSE.sql
-- CONTROLES      : patch_offres_annulees_classeur_2026-11-16_REPETITION.sql
-- ════════════════════════════════════════════════════════════════════════════

begin;

-- ── LES GARDES : le patch S'ARRETE plutot que d'ecrire a moitie
do $$
declare
  deja integer;
begin
  if not exists (select 1 from information_schema.columns
                  where table_schema = 'public' and table_name = 'app_affaire_ledger'
                    and column_name = 'transaction_origine') then
    raise exception 'ARRET : la colonne transaction_origine manque -- poser la piece 1 d abord';
  end if;

  select count(*) into deja from app_affaire_ledger where transaction_origine = 'classeur';
  if deja <> 0 then
    raise exception 'ARRET : %s ligne(s) sont deja marquees classeur -- ce patch est le PREMIER, il ne doit pas etre rejoue', deja;
  end if;

  if not exists (select 1 from pg_class where relname = 'app_affaire_id_app_seq') then
    raise exception 'ARRET : la sequence app_affaire_id_app_seq est introuvable';
  end if;
end $$;

-- ── LES 96 OFFRES, ET LEUR NOTE, DANS UNE SEULE INSTRUCTION
with donnees (id_unique, chaine, dossier, annonce, dossier_uuid, dossier_numero, dt) as (
  values
    ('S13Z3PIN', 28175, 1384897, 54771, 'c7129fac-cfff-494e-9df5-2f115cd23a6a'::uuid, 'D2025-0432', '2025-05-08'),
    ('1P6VET6U', 20246, 1370495, 41672, '96f39473-3868-42d0-8c7b-0cd5eda40e94'::uuid, 'D2025-0169', '2025-04-25'),
    ('7Q6O044E', 21439, 1371949, 42981, '3370d1ee-dbe1-41bb-abc5-b36097cedd99'::uuid, 'D2025-0186', '2025-04-30'),
    ('UC9UOAXE', 1911, 1382874, 5294, 'e37fbd86-9d5c-459f-8c17-a8e7c6af7038'::uuid, 'D2025-0179', '2025-04-30'),
    ('7C1ZQYFL', 30, 1104437, 61, '16213394-2f88-42c1-83f0-b36fdb736f6e'::uuid, 'D2024-0450', '2025-04-25'),
    ('2DUPM26R', 6156, 1338037, 11786, 'aa3edea3-565c-4834-bc8a-ab7fa96dafe9'::uuid, 'D2025-0218', '2025-04-11'),
    ('A4GWQGD5', 16788, 1363705, 35482, '92e62588-346b-4e4c-b42c-0fd6f90c3a5a'::uuid, 'D2025-0140', '2025-04-02'),
    ('DTL3BX47', 15895, 1360624, 32660, '975a24f7-6a76-4fdb-b477-617d3e5b8d94'::uuid, 'D2025-0419', '2025-04-08'),
    ('DCSKQ0CI', 974, 1346113, 1925, '7ee2c642-ed48-458a-b3ee-0b1f83797bd5'::uuid, 'D2025-0143', '2025-04-03'),
    ('BWEF58JV', 7068, 1340869, 14383, '76a9f6f1-6b96-4c55-876e-6b2db25f0279'::uuid, 'D2025-0206', '2025-04-02'),
    ('FYC1KCHQ', 14010, 1356029, 28440, 'a387b1d4-a434-415b-b78e-9c033848f48c'::uuid, 'D2024-0461', '2025-04-01'),
    ('LTJYTEVC', 6363, 1338525, 12273, '55de4335-1e96-47e7-b173-9856e4fb1a8c'::uuid, 'D2024-0453', '2025-04-18'),
    ('RL88RBTY', 24271, 1377423, 47975, '236db102-471b-4e54-b9d7-caffe964e4aa'::uuid, 'D2025-0153', '2025-02-17'),
    ('P4LPJRUF', 928, 1345342, 1848, '2896ac75-2fda-49d4-8af5-21b0a0e75c02'::uuid, 'D2025-0162', '2025-02-19'),
    ('MVSINFVU', 14084, 1356243, 28633, '46707bdb-e81e-4061-8e85-1b2d88c13d6c'::uuid, 'D2025-0082', '2025-01-25'),
    ('54ZD3N3B', 28115, 1384787, 54672, '728a5540-a194-4060-ae7a-0ee036bd9b7f'::uuid, 'D2024-0474', '2025-01-22'),
    ('NUBQNV1K', 21462, 1371961, 42992, '507df4a3-1a34-433b-8687-43cbda54f902'::uuid, 'D2025-0019', '2025-01-07'),
    ('9G7N611Q', 6261, 1338343, 12060, '5c976dff-2080-44e6-8b49-608338ad83dd'::uuid, 'D2025-0009', '2024-11-22'),
    ('W9FCDFGX', 23893, 1376747, 47353, 'eee7f764-1c36-4fd3-b13d-10e1663599f0'::uuid, 'D2025-0061', '2024-12-06'),
    ('SYA8MH79', 7499, 1341722, 15220, '7afd3600-ba2c-428d-b298-8ae56c54543b'::uuid, 'D2024-0458', '2025-02-10'),
    ('44ZVGG8Q', 25626, 1379099, 49484, 'cdaa4869-5d6a-4c5d-b712-3df61831a48c'::uuid, 'D2025-0102', '2025-02-17'),
    ('PYOA2KMY', 25965, 1379764, 50081, 'e856621b-6bd9-4a43-9db9-0f0155df1a5e'::uuid, 'D2025-0016', '2024-11-04'),
    ('KWT1HIHM', 23794, 1376503, 47133, '97a11905-fa59-4164-8147-e0da3b25e35f'::uuid, 'D2024-0470', '2024-12-14'),
    ('515UT1WG', 2357, 1385835, 5838, 'dfe142c9-e9aa-4b63-8c7e-5b75773d6c4b'::uuid, 'D2025-0007', '2024-12-26'),
    ('10MD21J7', 23162, 1375329, 46055, 'c04863c7-a2df-4af9-8dab-08560c5d5821'::uuid, 'D2024-0469', '2024-11-13'),
    ('HF33Q6DM', 16096, 1361151, 33134, 'fdf0a764-d2d3-4a63-9af0-c4b0d242c973'::uuid, 'D2024-0335', '2024-08-29'),
    ('BR8ZTN5F', 7176, 1341192, 14674, '0fad6eae-dd52-4b3d-b125-2b9d6849d263'::uuid, 'D2024-0457', '2025-01-24'),
    ('11QCW55L', 11110, 1350468, 23241, '55119d06-a636-46a1-b210-0f9d56157d3b'::uuid, 'D2025-0033', '2025-01-29'),
    ('C0HXVVCW', 28116, 1384791, 54676, 'c726287b-61ac-4a65-a77f-f21a88104122'::uuid, 'D2024-0475', '2024-12-15'),
    ('ABDXFMQC', 8840, 1344292, 17534, 'd0c56a27-97ad-4c7d-9b47-bad9b4579161'::uuid, 'D2024-0409', '2024-10-02'),
    ('25QYWG2U', 27100, 1383252, 53290, '807cfbfe-7392-4c8b-8b2c-874c9560c8ce'::uuid, 'D2025-0013', '2024-11-26'),
    ('OGVUGDXK', 8845, 1344294, 17536, '04ee1b4e-819c-4ed5-bbe8-490247c3be5a'::uuid, 'D2024-0459', '2025-01-09'),
    ('SHN6RKDI', 26613, 1382024, 52166, '904d160a-3dcc-4f52-9424-bb0514144be9'::uuid, 'D2024-0473', '2024-12-23'),
    ('0FSCB6XY', 7422, 1341575, 15018, '8b027b72-2613-49a7-9b8f-b6be997dc904'::uuid, 'D2024-0408', '2024-10-29'),
    ('JNETQT3P', 27033, 1382947, 53015, '9dbc0474-fb01-43a0-89c7-0a6e204fa130'::uuid, 'D2023-0566', '2024-07-03'),
    ('MIO9L8C9', 7067, 1340869, 14383, '6f2215a4-d1cb-438f-8713-0c2cd09efb00'::uuid, 'D2024-0455', '2024-08-02'),
    ('T58W1AXB', 3587, 1390709, 8330, '27b0369c-5821-4159-aab5-982c1f7d56ae'::uuid, 'D2024-0420', '2024-10-22'),
    ('WDY8CDXZ', 101, 1077844, 327, '623a8ecb-7b4f-4b5a-bee4-aba867473c96'::uuid, 'D2024-0390', '2024-09-19'),
    ('3KK4Z1SJ', 8839, 1344289, 17531, '6561ff98-4331-4db4-9197-9ecdf0282718'::uuid, 'D2024-0403', '2024-10-26'),
    ('IG4XNIZK', 958, 1345847, 1901, 'ab96f1ed-9c6a-4ba0-a58c-044c2f268b46'::uuid, 'D2024-0252', '2024-05-31'),
    ('4Z4M12JB', 11111, 1350472, 23245, '7a744595-8289-4a13-bc7b-8783914023e0'::uuid, 'D2024-0367', '2024-09-26'),
    ('TAG8IVT5', 3627, 1390760, 8377, 'c1e522c2-eb3c-4da8-be5c-f7570c232fdb'::uuid, 'D2024-0260', '2024-06-26'),
    ('723TVD5F', 7232, 1341289, 14761, '3bcb3a73-3e85-4dbc-9ec0-828936a7a8f6'::uuid, 'D2024-0340', '2024-08-12'),
    ('DA57BFXT', 11500, 1351325, 24206, '3b2c1945-f2d3-4a95-b26f-b4173d7d39cc'::uuid, 'D2024-0348', '2024-08-31'),
    ('VEL96ARW', 15961, 1360839, 32854, 'd04256d2-086d-454d-ad8f-178b9fef49ee'::uuid, 'D2024-0310', '2024-05-28'),
    ('LPDGSX81', 14083, 1356243, 28633, '52189d57-897a-46c1-ba01-2e41a2f71965'::uuid, 'D2024-0122', '2024-03-14'),
    ('6KRJ5GFV', 27039, 1382970, 53036, '61a3282b-358f-4c69-9119-8aba27f4e5aa'::uuid, 'D2023-0567', '2024-03-14'),
    ('AVO8HHFE', 160, 1091110, 448, '5f2b3f56-f495-4636-8035-6dc0e706b08d'::uuid, 'D2023-0501', '2023-09-15'),
    ('W5YQIW28', 20305, 1370551, 41722, '4a2dcf1f-5fa3-4d07-8327-ead33492a34e'::uuid, 'D2023-0326', '2023-06-20'),
    ('T0WL4QE7', 25876, 1379588, 49924, '383dc8c3-12db-4aec-aa6b-1e6caa3fc308'::uuid, 'D2023-0164', '2023-03-23'),
    ('K4AAKJU8', 1000142, 5834523, 23841, '4eeab3a4-8f08-4186-b473-a9a388ecda78'::uuid, 'D2023-0169', '2023-03-27'),
    ('I3R03A11', 19455, 1369094, 40378, '45c64723-d210-40d6-8840-92e54cd629c5'::uuid, 'D2022-0441', '2022-07-01'),
    ('8RWTD0YX', 4385, 1392113, 9629, '3408c17c-f9ce-455c-a7c5-13c6104d3fb4'::uuid, 'D2021-0736', '2022-02-25'),
    ('TZ7MOW1S', 16837, 1363925, 35680, '574ee548-0c1b-4661-97af-bb5dcfdb31b9'::uuid, 'D2021-0619', '2021-09-21'),
    ('5TGQ3A2Y', 16329, 1362005, 33952, '07dcee8d-45fb-4730-be3c-74f6290583f4'::uuid, 'D2021-0344', '2021-05-28'),
    ('O6R10ZQA', 20072, 1370292, 41467, 'b0d4c389-d1d1-4712-b511-ef657d887b7e'::uuid, 'D2021-0419', '2021-06-14'),
    ('FBOSPXJX', 17567, 1365863, 37470, 'e2a865f8-3334-4f06-a55b-0062d4bfe0bf'::uuid, 'D2020-0598', '2021-01-16'),
    ('UTLG66LE', 5054, 1336639, 10527, 'a5946e4a-2eeb-4e27-9212-ab6d5e2cbd78'::uuid, 'D2017-0589', '2019-12-18'),
    ('51bee548', 16100, 1361162, 33144, '8a2c390a-ef3f-4571-8f39-c364cf8dd0f6'::uuid, 'D2025-0421', '2025-05-20'),
    ('4a91a4b7', 3628, 1390760, 8377, '894668ae-a4cb-475a-9553-d49cf4ff8aae'::uuid, 'D2025-0180', '2025-05-21'),
    ('4b0f1b1c', 21435, 1371943, 42976, 'd990980c-aeef-4be9-8e5e-a5709f956b15'::uuid, 'D2025-0292', '2025-05-12'),
    ('8c7725f2', 24004, 1376975, 47571, 'c05d79e9-3556-472b-bd81-4a66a53a1bf3'::uuid, 'D2025-0216', '2025-05-28'),
    ('21f6e095', 23003, 1375007, 45766, '9097334f-db25-40f6-88ca-9190f11e89a3'::uuid, 'D2025-0225', '2025-06-05'),
    ('232d82c0', 14032, 1356102, 28506, '9814a5e0-5447-4d38-8b6e-3dc0b3a28b33'::uuid, 'D2025-0235', '2025-06-11'),
    ('e1eec623', 7105, 1340939, 14446, '59fe0e00-cc4f-4a24-9714-2c316c481451'::uuid, 'D2025-0414', '2025-06-18'),
    ('7241c9ce', 3629, 1390765, 8381, '484ac0c4-9f79-44f4-a567-fbaafd5de99e'::uuid, 'D2025-0242', '2025-07-08'),
    ('c24ea869', 11103, 1350464, 23238, 'a314b732-0471-4781-b5ea-a7dad74aec06'::uuid, 'D2024-0460', '2025-07-03'),
    ('875e39cd', 24135, 1377218, 47790, 'd28d5948-0ac4-4f54-8aec-f576cf072054'::uuid, 'D2024-0472', '2025-07-16'),
    ('afc80c2e', 997, 1346590, 1968, '7dbca9ea-1c34-458e-a2c5-9afeebbdbef2'::uuid, 'D2025-0409', '2025-07-17'),
    ('1f3d536a', 24010, 1376978, 47574, 'd5c630d4-923a-4841-b24b-fd6165c47df3'::uuid, 'D2024-0471', '2025-07-18'),
    ('d2108609', 21520, 1372027, 43050, '676ad1fa-24a7-45cf-97b5-e8c0b1d185e8'::uuid, 'D2025-0427', '2025-07-23'),
    ('bf3b08f8', 11144, 1350575, 23338, 'eba08ed1-5f70-4762-a975-358dcb18bd2e'::uuid, 'D2025-0280', '2025-07-29'),
    ('caea1510', 3669, 1390833, 8442, '68bf38b6-68ba-47a6-a55b-c9b94510766c'::uuid, 'D2025-0410', '2025-08-01'),
    ('d6322f88', 28120, 1384800, 54684, 'aa1c6b57-06cb-45f8-8926-c65701a55fda'::uuid, 'D2025-0401', '2025-08-06'),
    ('693b76ff', 25709, 1379255, 49624, '1c045875-fec2-4a95-b30c-c0d166047d32'::uuid, 'D2025-0431', '2025-08-12'),
    ('64225027', 25839, 1379506, 49850, '05471f88-5e8c-4eb4-af4d-1d1fcc103483'::uuid, 'D2025-0360', '2025-08-14'),
    ('aa25807d', 7048, 1340838, 14355, 'f8b431ba-89a3-4096-a0dd-31a0385f3ac2'::uuid, 'D2024-0454', '2025-08-20'),
    ('6348ec91', 19408, 1369016, 40307, 'c580ec92-e14b-4c61-a4bd-b2c4310d57d9'::uuid, 'D2025-0425', '2025-08-22'),
    ('acfdcbca', 6290, 1338395, 12107, '8504dcfa-cb8b-43d9-9ae5-d168cd1410dc'::uuid, 'D2025-0413', '2025-08-27'),
    ('fa4dc6e8', 28214, 1385003, 54867, 'dcc6f100-379e-43ca-bdb9-ad0a119cf50c'::uuid, 'D2025-0434', '2025-08-28'),
    ('729ba8dc', 6103, 1337936, 11695, '7002559d-67c5-46fa-9e93-817e4d5695b5'::uuid, 'D2025-0312', '2025-08-31'),
    ('97e5a34d', 25692, 1379198, 49573, '02ecb25d-b585-490a-ae38-0887095cd4e0'::uuid, 'D2025-0430', '2025-09-04'),
    ('76fff930', 14037, 1356114, 28517, '0b30a4f6-3539-4ad7-bb95-7c244857c7d5'::uuid, 'D2025-0308', '2025-09-08'),
    ('cc9e67f3', 6146, 1338013, 11764, 'e0ed87a3-c621-4307-b483-950d4590c765'::uuid, 'D2024-0452', '2025-09-09'),
    ('29e4a022', 15901, 1360659, 32692, '626d4153-cc88-4a56-bace-9fdb073d0f85'::uuid, 'D2025-0420', '2025-09-13'),
    ('6684bcf1', 19029, 1368237, 39607, '6ebc0e90-3735-4b45-9087-f49d6b45ca84'::uuid, 'D2025-0422', '2025-09-16'),
    ('0241547a', 22999, 1374993, 45753, '401ef40b-7054-48e5-b3e6-7e5620abab48'::uuid, 'D2025-0428', '2025-09-11'),
    ('0a733659', 3689, 1390854, 8461, 'caa947d1-3cf9-48ab-9027-b0b4eac3454a'::uuid, 'D2025-0411', '2025-10-14'),
    ('9343bcb8', 21933, 1372854, 43828, 'df532fe7-964a-4ec6-b561-5f4f687ebba8'::uuid, 'D2024-0468', '2025-10-27'),
    ('5a4371b5', 28178, 1384902, 54776, '7f848e8a-f5bc-466d-94b3-773acf230e2d'::uuid, 'D2025-0433', '2025-11-26'),
    ('c3bbebc2', 28597, 1386471, 59068, '0cf2a81a-cb84-4142-9890-63fce0d192db'::uuid, 'D2025-0406', '2025-12-01'),
    ('4f7b9749', 11145, 1350592, 23353, '6dcf12b8-f79d-4f49-8933-3776a4cd5220'::uuid, 'D2026-0002', '2025-12-02'),
    ('1b7b63c6', 28582, 1386430, 59029, '4b106983-e58a-4aa7-ae10-5b40222be57c'::uuid, 'D2025-0437', '2025-12-11'),
    ('01d21e1c', 4195, 1391817, 9362, '4df73427-2d37-47dd-9e35-12281fdab91c'::uuid, 'D2024-0451', '2025-12-25'),
    ('b42affe7', 28546, 1386296, 58907, '7d195053-633e-458a-b5e7-fdf32b351b5c'::uuid, 'D2025-0435', '2026-01-18'),
    ('739a0db1', 27195, 1383371, 53398, 'b79202ce-5846-4ec3-bd4b-2f240a688f3e'::uuid, 'D2025-0017', '2026-06-18')
),
notes (id_unique, texte) as (
  values
    ('S13Z3PIN', 'Acquereur au classeur : M. DUCHET Cédric. Reprise de l historique (ligne S13Z3PIN, mandat 17488) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('1P6VET6U', 'Acquereur au classeur : Mme GOULOIS Virginie. Reprise de l historique (ligne 1P6VET6U, mandat 16406) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('7Q6O044E', 'Acquereur au classeur : Mme M. BARBIER Gaëtan PIPOLO Marine. Reprise de l historique (ligne 7Q6O044E, mandat 17195) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('UC9UOAXE', 'Acquereur au classeur : Société GRAIL Jo-nathan. Reprise de l historique (ligne UC9UOAXE, mandat 16150) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('7C1ZQYFL', 'Acquereur au classeur : M. AGUIAR Eric. Reprise de l historique (ligne 7C1ZQYFL, mandat 16684) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('2DUPM26R', 'Acquereur au classeur : Mme LIGNIERE Catherine. Reprise de l historique (ligne 2DUPM26R, mandat 17534) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('A4GWQGD5', 'Acquereur au classeur : M. BELKHIR Adel. Reprise de l historique (ligne A4GWQGD5, mandat 16913) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('DTL3BX47', 'Acquereur au classeur : Mme et M. HOUGRAND Yvitte et Jackie. Reprise de l historique (ligne DTL3BX47, mandat 17663) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('DCSKQ0CI', 'Acquereur au classeur : Mme et M. Kevlishvili Ekaterine Gavardashvili Bichiko. Reprise de l historique (ligne DCSKQ0CI, mandat 17514) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('BWEF58JV', 'Acquereur au classeur : Mme et M. STAWSKI Laëtita et Bruno. Reprise de l historique (ligne BWEF58JV, mandat 16975) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('FYC1KCHQ', 'Acquereur au classeur : Mme KIABIYA Zezabel. Reprise de l historique (ligne FYC1KCHQ, mandat 17049) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('LTJYTEVC', 'Acquereur au classeur : M. CHESNE Gregory. Reprise de l historique (ligne LTJYTEVC, mandat 17285) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('RL88RBTY', 'Acquereur au classeur : M. CANIVET Yoann. Reprise de l historique (ligne RL88RBTY, mandat 17224) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('P4LPJRUF', 'Acquereur au classeur : M. KAMDEM Taniselas. Reprise de l historique (ligne P4LPJRUF, mandat 17265) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('MVSINFVU', 'Acquereur au classeur : SAS Foncière Solidaire Monsenior. Reprise de l historique (ligne MVSINFVU, mandat 16366) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('54ZD3N3B', 'Acquereur au classeur : Mme VITRY Catherine. Reprise de l historique (ligne 54ZD3N3B, mandat 17251) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('NUBQNV1K', 'Acquereur au classeur : M. ARRIGHI Michel. Reprise de l historique (ligne NUBQNV1K, mandat 16993) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('9G7N611Q', 'Acquereur au classeur : Société SCI BERR-BOUCHANT représentée par Charlotte Berr. Reprise de l historique (ligne 9G7N611Q, mandat 16439) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('W9FCDFGX', 'Acquereur au classeur : Mme et M. GRANGE Zoé et JALIGOT Karl. Reprise de l historique (ligne W9FCDFGX, mandat 17392) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('SYA8MH79', 'Acquereur au classeur : M. GENILLON René. Reprise de l historique (ligne SYA8MH79, mandat 17196) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('44ZVGG8Q', 'Acquereur au classeur : M. FARDELLA Jerome. Reprise de l historique (ligne 44ZVGG8Q, mandat 17314) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('PYOA2KMY', 'Acquereur au classeur : M. DUPEYRON Yann. Reprise de l historique (ligne PYOA2KMY, mandat 17003) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('KWT1HIHM', 'Acquereur au classeur : Mme PERRIN Maxime. Reprise de l historique (ligne KWT1HIHM, mandat 17288) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('515UT1WG', 'Acquereur au classeur : M. VIGOUROUX Lucas. Reprise de l historique (ligne 515UT1WG, mandat 17420) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('10MD21J7', 'Acquereur au classeur : nan FRAIDEL GERVAIS. Reprise de l historique (ligne 10MD21J7, mandat 16820) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('HF33Q6DM', 'Acquereur au classeur : M. NORVAL Edouard. Reprise de l historique (ligne HF33Q6DM, mandat 16743) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('BR8ZTN5F', 'Acquereur au classeur : Société SCI 2MVR représentée par Mickael Varlet gérant. Reprise de l historique (ligne BR8ZTN5F, mandat 17350) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('11QCW55L', 'Acquereur au classeur : M. RIVOIRE Jean-Jacques. Reprise de l historique (ligne 11QCW55L, mandat 17504) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('C0HXVVCW', 'Acquereur au classeur : M. DUFOUR Marlon. Reprise de l historique (ligne C0HXVVCW, mandat 17168) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('ABDXFMQC', 'Acquereur au classeur : M. WHITELEY Andrew. Reprise de l historique (ligne ABDXFMQC, mandat 17214) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('25QYWG2U', 'Acquereur au classeur : nan LACHAL. Reprise de l historique (ligne 25QYWG2U, mandat 15929) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('OGVUGDXK', 'Acquereur au classeur : M. ROUCHON Fabien. Reprise de l historique (ligne OGVUGDXK, mandat 17286) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('SHN6RKDI', 'Acquereur au classeur : Mme et M. MOSNIER Françoise et Georges. Reprise de l historique (ligne SHN6RKDI, mandat 17434) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('0FSCB6XY', 'Acquereur au classeur : nan BOURRIOT. Reprise de l historique (ligne 0FSCB6XY, mandat 17297) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('JNETQT3P', 'Acquereur au classeur : nan VULLIN LAGRANGE. Reprise de l historique (ligne JNETQT3P, mandat 16462) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('MIO9L8C9', 'Acquereur au classeur : nan MALLARD. Reprise de l historique (ligne MIO9L8C9, mandat 16975) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('T58W1AXB', 'Acquereur au classeur : nan BONNET. Reprise de l historique (ligne T58W1AXB, mandat 17227) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('WDY8CDXZ', 'Acquereur au classeur : nan GHILAS. Reprise de l historique (ligne WDY8CDXZ, mandat 15696) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('3KK4Z1SJ', 'Acquereur au classeur : nan PONTVIANNE. Reprise de l historique (ligne 3KK4Z1SJ, mandat 17248) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('IG4XNIZK', 'Acquereur au classeur : nan MASSIAS. Reprise de l historique (ligne IG4XNIZK, mandat 16787) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('4Z4M12JB', 'Acquereur au classeur : nan RIANI. Reprise de l historique (ligne 4Z4M12JB, mandat 17190) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('TAG8IVT5', 'Acquereur au classeur : nan BERGERT DURAND. Reprise de l historique (ligne TAG8IVT5, mandat 16931) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('723TVD5F', 'Acquereur au classeur : nan VALLAT. Reprise de l historique (ligne 723TVD5F, mandat 16358) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('DA57BFXT', 'Acquereur au classeur : nan DENIS DOS SANTOS. Reprise de l historique (ligne DA57BFXT, mandat 17178) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('VEL96ARW', 'Acquereur au classeur : nan SABATIER. Reprise de l historique (ligne VEL96ARW, mandat 16858) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('LPDGSX81', 'Acquereur au classeur : nan BOZKURT. Reprise de l historique (ligne LPDGSX81, mandat 16366) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('6KRJ5GFV', 'Acquereur au classeur : nan BOST GIRARD. Reprise de l historique (ligne 6KRJ5GFV, mandat 16359) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('AVO8HHFE', 'Acquereur au classeur : nan EDORH. Reprise de l historique (ligne AVO8HHFE, mandat 15937) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('W5YQIW28', 'Acquereur au classeur : nan MILTON BARRAUD. Reprise de l historique (ligne W5YQIW28, mandat 15642) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('T0WL4QE7', 'Acquereur au classeur : nan PORTERAT. Reprise de l historique (ligne T0WL4QE7, mandat 15378) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('K4AAKJU8', 'Acquereur au classeur : nan DRID. Reprise de l historique (ligne K4AAKJU8, mandat 13614) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('I3R03A11', 'Acquereur au classeur : nan RIOS. Reprise de l historique (ligne I3R03A11, mandat 14461) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('8RWTD0YX', 'Acquereur au classeur : nan VAN ROSSUM. Reprise de l historique (ligne 8RWTD0YX, mandat 14065) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('TZ7MOW1S', 'Acquereur au classeur : nan GONZALEZ LARGERON. Reprise de l historique (ligne TZ7MOW1S, mandat 13386) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('5TGQ3A2Y', 'Acquereur au classeur : nan POLICHETTI. Reprise de l historique (ligne 5TGQ3A2Y, mandat 13512) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('O6R10ZQA', 'Acquereur au classeur : nan PAOLONE. Reprise de l historique (ligne O6R10ZQA, mandat 4369) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('FBOSPXJX', 'Acquereur au classeur : nan BENMATALLAH. Reprise de l historique (ligne FBOSPXJX, mandat 4006) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('UTLG66LE', 'Acquereur au classeur : nan STAUFFER. Reprise de l historique (ligne UTLG66LE, mandat 2544) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('51bee548', 'Acquereur au classeur : Mme DEYGAS Aurélie. Reprise de l historique (ligne 51bee548, mandat 17759) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('4a91a4b7', 'Acquereur au classeur : Mme M. MARSAL Coralie et Julien. Reprise de l historique (ligne 4a91a4b7, mandat 16931) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('4b0f1b1c', 'Acquereur au classeur : M. GIBERT Arthur. Reprise de l historique (ligne 4b0f1b1c, mandat 17260) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('8c7725f2', 'Acquereur au classeur : M. LE VELY Cyrille. Reprise de l historique (ligne 8c7725f2, mandat 17208) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('21f6e095', 'Acquereur au classeur : M. PONOT Thomas Mme REPELLIN Laurette. Reprise de l historique (ligne 21f6e095, mandat 17653) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('232d82c0', 'Acquereur au classeur : Mme DENIS Laurie. Reprise de l historique (ligne 232d82c0, mandat 17790) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('e1eec623', 'Acquereur au classeur : M. REMIS Calvin. Reprise de l historique (ligne e1eec623, mandat 17773) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('7241c9ce', 'Acquereur au classeur : Mme M. ASSEMAT Laure et Olivier. Reprise de l historique (ligne 7241c9ce, mandat 17850) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('c24ea869', 'Acquereur au classeur : M. SIMONYAN Gor. Reprise de l historique (ligne c24ea869, mandat 17295) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('875e39cd', 'Acquereur au classeur : M. BOUGHELLAM Mohamed. Reprise de l historique (ligne 875e39cd, mandat 17432) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('afc80c2e', 'Acquereur au classeur : M. GUETAL Farid. Reprise de l historique (ligne afc80c2e, mandat 17761) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('1f3d536a', 'Acquereur au classeur : Mme M. PALLANDRE Mathieu RICHARD Mathilde. Reprise de l historique (ligne 1f3d536a, mandat 16976) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('d2108609', 'Acquereur au classeur : Mme M. CHOUVELLON Henriette et Michel. Reprise de l historique (ligne d2108609, mandat 17877) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('bf3b08f8', 'Acquereur au classeur : Mme VERA CRUZ FERNANDES Arisete. Reprise de l historique (ligne bf3b08f8, mandat 17750) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('caea1510', 'Acquereur au classeur : M. LAFFONT Jérémie Mme KAMPIRE Rachel. Reprise de l historique (ligne caea1510, mandat 17740) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('d6322f88', 'Acquereur au classeur : M. LE GALL Erwann. Reprise de l historique (ligne d6322f88, mandat 17584) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('693b76ff', 'Acquereur au classeur : Mme M. BEAUFILS Stéphane et CROUZET Stéphanie. Reprise de l historique (ligne 693b76ff, mandat 17929) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('64225027', 'Acquereur au classeur : Mme M. THIOLIER Morgan et BONNET Jérômine. Reprise de l historique (ligne 64225027, mandat 17839) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('aa25807d', 'Acquereur au classeur : M. DUBOIS Vincent. Reprise de l historique (ligne aa25807d, mandat 17306) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('6348ec91', 'Acquereur au classeur : SCI "ô petit truc en plus" représentée par Emilie Guérin. Reprise de l historique (ligne 6348ec91, mandat 17494) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('acfdcbca', 'Acquereur au classeur : Mme ROUGIER Jacqueline. Reprise de l historique (ligne acfdcbca, mandat 17986) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('fa4dc6e8', 'Acquereur au classeur : Mme PLANCHE Estelle. Reprise de l historique (ligne fa4dc6e8, mandat 17937) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('729ba8dc', 'Acquereur au classeur : Mme M. PUISSANT Guillaume et ROCHARD Anne. Reprise de l historique (ligne 729ba8dc, mandat 17296) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('97e5a34d', 'Acquereur au classeur : Mme M. ROUX Jacques et Martine. Reprise de l historique (ligne 97e5a34d, mandat 17733) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('76fff930', 'Acquereur au classeur : Mmes AYZA Aurélie et Nathalie. Reprise de l historique (ligne 76fff930, mandat 17880) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('cc9e67f3', 'Acquereur au classeur : Mme M. PENSATO Kévin et MANUEL Mariane-Aurore. Reprise de l historique (ligne cc9e67f3, mandat 17417) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('29e4a022', 'Acquereur au classeur : M. VENEKAS Rémy. Reprise de l historique (ligne 29e4a022, mandat 17977) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('6684bcf1', 'Acquereur au classeur : Mme M. ANDRÉ Roger et Maryse. Reprise de l historique (ligne 6684bcf1, mandat 17808) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('0241547a', 'Acquereur au classeur : Mme M. CAZALBON Brice ROLLAND VILLEMAGNE Corine. Reprise de l historique (ligne 0241547a, mandat 17484) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('0a733659', 'Acquereur au classeur : Mme M. ROUMAZEILLES Damien et Louna. Reprise de l historique (ligne 0a733659, mandat 18075) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('9343bcb8', 'Acquereur au classeur : M. FAURE Marc. Reprise de l historique (ligne 9343bcb8, mandat 16522) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('5a4371b5', 'Acquereur au classeur : Mme M. MORAINES. Reprise de l historique (ligne 5a4371b5, mandat 17927) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('c3bbebc2', 'Acquereur au classeur : Mme FABRE Narima. Reprise de l historique (ligne c3bbebc2, mandat 18112) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('4f7b9749', 'Acquereur au classeur : Mme M. TOSUN Yildiray et Nuran. Reprise de l historique (ligne 4f7b9749, mandat 18019) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('1b7b63c6', 'Acquereur au classeur : Mme LEROI Françoise. Reprise de l historique (ligne 1b7b63c6, mandat 18184) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('01d21e1c', 'Acquereur au classeur : M. DROGO Bruno Mme LALOY Dominique. Reprise de l historique (ligne 01d21e1c, mandat 16590) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('b42affe7', 'Acquereur au classeur : M. FLEUROT Baptiste Mme CHIROL Manon. Reprise de l historique (ligne b42affe7, mandat 18228) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('739a0db1', 'Acquereur au classeur : M. HALLAERT-THEYS Aurélien Mme MAURAIS Audrey. Reprise de l historique (ligne 739a0db1, mandat 18176) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.')
),
posees as (
  insert into app_affaire_ledger (
    app_affaire_id, app_chaine_id, app_dossier_id,
    kind, state, date,
    hektor_annonce_id, hektor_affaire_id, present_in_hektor,
    app_dossier_uuid, app_dossier_numero,
    transaction_origine,
    payload_json, first_seen_at, last_seen_at)
  select nextval('app_affaire_id_app_seq'), d.chaine, d.dossier,
         'offre', 'refused', d.dt,
         d.annonce, null, false,
         d.dossier_uuid, d.dossier_numero,
         'classeur',
         jsonb_build_object(
           'classeur_id_unique', d.id_unique,
           'classeur_lot', 'C5 lot B -- offres annulees',
           'classeur_pose_le', '2026-11-16',
           'etat_au_classeur', 'Annulee'),
         now(), now()
    from donnees d
  returning app_affaire_id, app_chaine_id, (payload_json ->> 'classeur_id_unique') as id_unique
)
insert into app_affaire_note (app_affaire_id, texte, app_dossier_id, app_chaine_id, origine)
select p.app_affaire_id, n.texte, d.dossier, d.chaine, 'classeur'
  from posees p
  join notes   n on n.id_unique = p.id_unique
  join donnees d on d.id_unique = p.id_unique;

-- ── LES CONTROLES, AVANT LE COMMIT : ils annulent tout si un compte ne tombe pas
do $$
declare
  posees integer;
  notees integer;
  sans_marque integer;
  avec_numero integer;
  avec_parties integer;
begin
  select count(*) into posees from app_affaire_ledger where transaction_origine = 'classeur';
  if posees <> 96 then
    raise exception 'ARRET : %s ligne(s) marquees classeur au lieu de 96', posees;
  end if;

  select count(*) into notees from app_affaire_note where origine = 'classeur';
  if notees < 96 then
    raise exception 'ARRET : %s note(s) seulement pour 96 offres', notees;
  end if;

  select count(*) into sans_marque from app_affaire_ledger
   where transaction_origine = 'classeur'
     and (kind <> 'offre' or state <> 'refused' or present_in_hektor
          or hektor_affaire_id is not null or app_chaine_id is null);
  if sans_marque <> 0 then
    raise exception 'ARRET : %s ligne(s) posees ne respectent pas la forme attendue', sans_marque;
  end if;

  select count(*) into avec_numero from app_affaire_ledger
   where transaction_origine = 'classeur' and app_affaire_id < 1000000;
  if avec_numero <> 0 then
    raise exception 'ARRET : %s ligne(s) hors de la plage app (>= 1 000 000)', avec_numero;
  end if;

  -- ⭐ LE TEMOIN DE L'ACQUEREUR : sans acquereurs_json, le declencheur ne doit
  --   avoir cree AUCUNE partie pour ces lignes.
  select count(*) into avec_parties from app_affaire_partie p
    join app_affaire_ledger l on l.app_affaire_id = p.app_affaire_id
   where l.transaction_origine = 'classeur';
  if avec_parties <> 0 then
    raise exception 'ARRET : %s partie(s) creees alors qu aucun acquereur n a ete pose', avec_parties;
  end if;

  raise notice 'OK : 96 offres posees, %s notes, 0 partie creee, toutes dans la plage app', notees;
end $$;

-- ── CE QUI VIENT D'ETRE POSE, a lire dans la sortie
select kind, state, present_in_hektor, transaction_origine,
       count(*) as lignes, min(app_affaire_id) as premier, max(app_affaire_id) as dernier
  from app_affaire_ledger
 where transaction_origine = 'classeur'
 group by 1,2,3,4;

commit;
