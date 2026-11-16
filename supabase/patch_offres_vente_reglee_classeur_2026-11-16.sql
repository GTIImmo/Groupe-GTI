-- ════════════════════════════════════════════════════════════════════════════
-- C5 / LOT B -- LES 64 OFFRES « ANNULEE » DU CLASSEUR
-- 16/11/2026 . chantier classeur, tache 3.3 lot B . genere par
-- phase2/checks/poser_offres_annulees_classeur_2026-11-16.py
-- ════════════════════════════════════════════════════════════════════════════
--
-- CE QU'ON POSE : 64 offres que le classeur porte et que nous n'avons pas, dont
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
-- RETOUR ARRIERE : patch_offres_vente_reglee_classeur_2026-11-16_INVERSE.sql
-- CONTROLES      : patch_offres_vente_reglee_classeur_2026-11-16_REPETITION.sql
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

  -- ⛔⛔ LA GARDE VISE **CE LOT**, PAS TOUTE LA MARQUE. Sa premiere version
  --   refusait de jouer des qu une ligne portait transaction_origine = classeur
  --   -- juste pour le PREMIER lot, et FAUSSE pour tous les suivants : les
  --   96 offres annulees du 16/11 auraient bloque les compromis. Corrige le 16/11.
  select count(*) into deja from app_affaire_ledger
   where transaction_origine = 'classeur'
     and (payload_json ->> 'classeur_lot') = 'C5 lot B -- offres vente reglee';
  if deja <> 0 then
    raise exception 'ARRET : %s ligne(s) de CE LOT existent deja -- il ne doit pas etre rejoue', deja;
  end if;

  if not exists (select 1 from pg_class where relname = 'app_affaire_id_app_seq') then
    raise exception 'ARRET : la sequence app_affaire_id_app_seq est introuvable';
  end if;
end $$;

-- ── LES 64 OFFRES, ET LEUR NOTE, DANS UNE SEULE INSTRUCTION
with donnees (id_unique, chaine, dossier, annonce, dossier_uuid, dossier_numero, dt) as (
  values
    ('WF5TA3HB', 21497, 1371997, 43023, '6a39cecd-0647-4dc1-a6ea-3ae2cd56667e'::uuid, 'D2025-0174', '2025-06-02'),
    ('G11K36ZS', 9351, 1345489, 18688, 'cba500a0-8b48-4d36-8cfc-410a0f235f3b'::uuid, 'D2025-0122', '2025-03-31'),
    ('D917QKSF', 27203, 1383382, 53407, 'a5d47095-4f9e-422a-bcf3-7a108463bc1b'::uuid, 'D2025-0154', '2025-04-29'),
    ('YP3CF98R', 6394, 1338574, 12317, 'bf3b9c36-4f69-40c0-819f-c3f0227bc534'::uuid, 'D2025-0148', '2025-05-13'),
    ('8PJ1N21V', 27037, 1382966, 53032, '8d9c5a73-204f-43ba-8ea6-ff87cc2cad67'::uuid, 'D2025-0040', '2024-12-18'),
    ('TRJ5Y59U', 23993, 1376959, 47557, '074bbfc0-8a23-480f-a9fe-155594585326'::uuid, 'D2024-0067', '2024-03-25'),
    ('6FMNGNAA', 28253, 1385072, 54929, '02a1bc9e-3a63-49a9-a9c4-d18fef30d2e2'::uuid, 'D2024-0168', '2024-03-09'),
    ('A07EC3DH', 1874, 1382528, 5262, '2c8c4e87-9a5d-4352-ac87-13ad7de8ef9c'::uuid, 'D2023-0541', '2024-01-12'),
    ('DTODYSI2', 7242, 1341303, 14774, '17106ee8-ee77-46d3-8093-b32744558a97'::uuid, 'D2023-0535', '2023-11-13'),
    ('LJ4YRZNU', 16023, 1360935, 32940, '9a81d228-7f88-498c-918c-5421c8e9d667'::uuid, 'D2023-0162', '2023-03-19'),
    ('T6CEOCJE', 7715, 1342225, 15674, 'b6c2cb62-78c4-4707-bbb1-c0e4b154d446'::uuid, 'D2022-0598', '2022-12-15'),
    ('0OI5KSEB', 26059, 1380221, 50543, '12859d16-07db-4351-ad4b-4412be0ca5ed'::uuid, 'D2022-0594', '2022-12-14'),
    ('X2714E92', 17024, 1364464, 36165, '7fba72f8-d27a-4e27-b7a3-25b1ef95d1c6'::uuid, 'D2022-0198', '2022-10-05'),
    ('5TIHSGP4', 15028, 1358717, 30944, 'dcfe8de1-e5b4-48bb-ac84-a9a9264ce7b1'::uuid, 'D2022-0315', '2022-05-31'),
    ('VXGSNU25', 4375, 1392093, 9610, '5eee86e7-9206-4b48-8191-33426de020db'::uuid, 'D2022-0414', '2022-04-11'),
    ('V0QL8N3G', 20383, 1370611, 41777, 'db0a6d0b-2816-4f20-a1b9-d5c0be0bb4d3'::uuid, 'D2022-0091', '2022-01-31'),
    ('B5VKBMW0', 16262, 1361610, 33597, 'a368e67d-ad8d-4c19-a00c-40265df3ef6e'::uuid, 'D2022-0326', '2021-10-29'),
    ('B5HZ3OV5', 16267, 1361618, 33603, 'b9e3d8de-6fa8-4369-bb50-b6a6fde8ad75'::uuid, 'D2022-0327', '2021-10-28'),
    ('AMKJIRYN', 16310, 1361930, 33885, '0e1e809b-24f9-4bbd-b100-2d3145053034'::uuid, 'D2021-0672', '2021-10-07'),
    ('H6CTRVR6', 11412, 1351228, 24119, '138def26-0df0-434e-906c-7d5c5fdadb0c'::uuid, 'D2021-0314', '2021-05-18'),
    ('0GV2LNV2', 4745, 1336237, 10165, '3be58175-9ba3-4c97-90ca-b03690310f37'::uuid, 'D2021-0145', '2021-03-11'),
    ('1290IIOC', 16362, 1362112, 34048, '6a7dd319-3eb8-4d6f-ba6b-076a7dfe6ed8'::uuid, 'D2020-0074', '2020-12-20'),
    ('KO6QPUV7', 16197, 1361456, 33458, '1340beff-a1f4-49d1-838a-83a102fc4dd4'::uuid, 'D2021-0199', '2020-12-03'),
    ('LWZL8V5M', 20672, 1370888, 42025, 'e35ac15b-6349-4c0d-b0e8-6fdcb0d3b003'::uuid, 'D2020-0341', '2020-08-08'),
    ('3S4ZWOFK', 11956, 1351910, 24733, '66da22ce-5956-49d6-aeb1-f7adbc1922a4'::uuid, 'D2020-0214', '2020-06-12'),
    ('ZQD27I3K', 16622, 1363298, 35115, '7298637c-adfa-4edb-af23-e50e04672d31'::uuid, 'D2020-0238', '2020-06-10'),
    ('CSB367SG', 16195, 1361453, 33455, '20916d3d-273a-4825-be5f-74ef3b03196c'::uuid, 'D2020-0143', '2020-03-26'),
    ('DAATY4A7', 16397, 1362272, 34192, '37f95361-1071-4fce-a733-bed276c18723'::uuid, 'D2020-0001', '2019-12-13'),
    ('8WEM4UIX', 16890, 1364021, 35767, 'cccb5226-6ac7-4363-9a05-0b74ff63ef25'::uuid, 'D2019-0303', '2019-06-28'),
    ('ZMB56WW7', 16399, 1362286, 34204, 'cf6a780a-0cdf-4e3e-bc2b-96600593e911'::uuid, 'D2019-0436', '2019-09-08'),
    ('XXNOUH9H', 12060, 1352025, 24837, 'dc3f9354-f77e-465b-8e69-9b3b42985073'::uuid, 'D2019-0030', '2019-01-11'),
    ('HUY49KEC', 3741, 1391087, 8671, '034b7eb1-f25c-45b1-97b9-5bbe8bb5bf62'::uuid, 'D2018-0476', '2018-11-16'),
    ('3RFGZQ1E', 17700, 1366181, 37757, '382607ec-dcef-4843-b6da-0e8c390c81d5'::uuid, 'D2018-0292', '2018-07-04'),
    ('MN8HFEHN', 12122, 1352078, 24885, 'f06f831c-fdf1-4a16-9854-2bbfa01f0ef2'::uuid, 'D2018-0308', '2018-07-11'),
    ('U34PK32L', 16941, 1364265, 35987, 'f59dfc5b-29b1-4557-93bd-7095a2f8dd65'::uuid, 'D2018-0215', '2018-05-02'),
    ('5H96YY2I', 25684, 1379180, 49557, '288107f3-c2c8-4fdd-80eb-ce27c7c83fbb'::uuid, 'D2025-0202', '2025-05-14'),
    ('D018N09A', 25582, 1379013, 49406, '34c36d53-10cf-4e59-95d6-35ca8ce63b9b'::uuid, 'D2025-0239', '2025-05-16'),
    ('1cc703d9', 14007, 1356009, 28422, 'a633d3ec-2546-4a1c-883e-493a2e22f4a6'::uuid, 'D2025-0365', '2025-06-28'),
    ('86a190de', 25969, 1379788, 50102, 'b0ee6241-7330-448b-9587-fec179dc8327'::uuid, 'D2025-0293', '2025-07-21'),
    ('861af493', 28134, 1384820, 54701, 'db8044b3-dfd2-4d2a-8123-9f6baec60353'::uuid, 'D2025-0269', '2025-07-22'),
    ('77e6f1fc', 21527, 1372033, 43056, '06af79d4-ba6e-407f-bef6-cd3da1733796'::uuid, 'D2025-0244', '2025-07-22'),
    ('8cf0e171', 26598, 1381964, 52111, '9d90b2f8-bd6a-4e34-ab30-1c780dadb6d7'::uuid, 'D2025-0277', '2025-07-23'),
    ('2962d089', 21518, 1372025, 43049, '1aef2f48-301b-4f85-8ae1-0580d8aec6fb'::uuid, 'D2025-0268', '2025-07-23'),
    ('591418b3', 28205, 1384967, 54834, '0c490b3e-46b0-42d1-8596-17a2520d590f'::uuid, 'D2025-0273', '2025-07-18'),
    ('29277933', 21513, 1372022, 43046, 'e269b18a-eaa0-48ab-953e-88d62eb1eb95'::uuid, 'D2025-0282', '2025-07-12'),
    ('1649864f', 16815, 1363781, 35550, 'e5cdba4b-82b0-438f-926f-500195c3eaae'::uuid, 'D2025-0305', '2025-07-28'),
    ('89cbcce9', 15890, 1360615, 32652, '273fa6ea-0191-4e53-ac22-fd8de3d05759'::uuid, 'D2025-0315', '2025-08-11'),
    ('07cec9e1', 27345, 1383556, 53564, 'd4182281-8346-4290-9f2a-25de8ba062ed'::uuid, 'D2025-0306', '2025-07-25'),
    ('c08ff7cb', 3676, 1390846, 8454, '1d86aa92-75e5-4928-bc4e-a47814c43abd'::uuid, 'D2025-0254', '2025-08-14'),
    ('6b02c91a', 19038, 1368298, 39662, 'a904a252-4244-4dab-96bc-09d422e38831'::uuid, 'D2025-0288', '2025-08-14'),
    ('7c7b5d8e', 1009, 1346724, 1980, 'cabb7f1b-8efa-4d7d-82d8-a525cab4fc0f'::uuid, 'D2025-0320', '2025-09-22'),
    ('0d6cad26', 3695, 1390871, 8477, '6c6394f1-ada0-48d9-b65d-db5a3f11a72d'::uuid, 'D2025-0329', '2025-09-25'),
    ('4205088d', 24484, 1377686, 48210, 'fa3ffb9e-a010-4eb8-8533-ea86e5316b0a'::uuid, 'D2025-0321', '2025-09-26'),
    ('dfe48dde', 926, 1345254, 1840, '0297a8a1-f032-4cb3-ba5a-e5e787505204'::uuid, 'D2025-0356', '2025-10-16'),
    ('650e65c8', 21531, 1372050, 43071, '4ee341cd-4a84-419f-92b5-5d4e7ca5a6b9'::uuid, 'D2025-0343', '2025-10-17'),
    ('7e1dded4', 21529, 1372034, 43057, 'f4ae893f-e817-401f-9d80-90e89f266f37'::uuid, 'D2025-0353', '2025-10-10'),
    ('512f903b', 929, 1345342, 1848, '3d5a798c-9d99-4ef4-8a8f-0df481ae4621'::uuid, 'D2025-0368', '2025-10-21'),
    ('6d229f85', 25707, 1379241, 49611, '3cbdce49-8ebc-44c4-8c8a-f1f506c48963'::uuid, 'D2026-0026', '2025-10-28'),
    ('f023c1d4', 6166, 1338066, 11811, 'c4426ff4-6c3c-47b3-8bec-880059de04fc'::uuid, 'D2025-0407', '2025-11-04'),
    ('7f7c8e48', 7078, 1340895, 14406, '74478a45-0b26-4a75-bce4-63f68b866bb7'::uuid, 'D2025-0395', '2025-11-12'),
    ('a89cbbdd', 3693, 1390861, 8468, '3c7b4727-3b54-4057-bc6a-6e2157635148'::uuid, 'D2025-0405', '2025-11-17'),
    ('84331d2b', 6179, 1338098, 11840, 'c84553a0-3ac5-4797-9eba-e92219eb4476'::uuid, 'D2026-0001', '2025-12-12'),
    ('0c3629d5', 25713, 1379274, 49641, '5b756d5c-7467-450b-a219-1a908d3697d3'::uuid, 'D2026-0010', '2025-12-16'),
    ('bdb548a3', 21551, 1372072, 43091, '49d3df3c-f694-468d-9438-a853e578aab6'::uuid, 'D2026-0067', '2026-02-06')
),
notes (id_unique, texte) as (
  values
    ('WF5TA3HB', 'Acquereur au classeur : Mme M. OSTERMANN Aurelie GRENIER Ludovic. Reprise de l historique (ligne WF5TA3HB, mandat 17616) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('G11K36ZS', 'Acquereur au classeur : Mme et M. DOYAT Marilyne DERAIL Jessy. Reprise de l historique (ligne G11K36ZS, mandat 16723) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('D917QKSF', 'Acquereur au classeur : Mme GARIN Manuella. Reprise de l historique (ligne D917QKSF, mandat 15868) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('YP3CF98R', 'Acquereur au classeur : M. GENDREAU Joffrey. Reprise de l historique (ligne YP3CF98R, mandat 17405) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('8PJ1N21V', 'Acquereur au classeur : Mme et M. HERRIER Nadine et Gilles. Reprise de l historique (ligne 8PJ1N21V, mandat 16436) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('TRJ5Y59U', 'Acquereur au classeur : nan MARTINEZ. Reprise de l historique (ligne TRJ5Y59U, mandat 16628) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('6FMNGNAA', 'Acquereur au classeur : nan CALAFAT. Reprise de l historique (ligne 6FMNGNAA, mandat 16705) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('A07EC3DH', 'Acquereur au classeur : nan GUERIN. Reprise de l historique (ligne A07EC3DH, mandat 16362) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('DTODYSI2', 'Acquereur au classeur : nan RASCLE. Reprise de l historique (ligne DTODYSI2, mandat 15945) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('LJ4YRZNU', 'Acquereur au classeur : nan DOISNE. Reprise de l historique (ligne LJ4YRZNU, mandat 15388) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('T6CEOCJE', 'Acquereur au classeur : nan BARCOJO. Reprise de l historique (ligne T6CEOCJE, mandat 13884) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('0OI5KSEB', 'Acquereur au classeur : SCI KL. Reprise de l historique (ligne 0OI5KSEB, mandat 15202) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('X2714E92', 'Acquereur au classeur : nan MAIRIE DU CHAMBON. Reprise de l historique (ligne X2714E92, mandat 14443) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('5TIHSGP4', 'Acquereur au classeur : nan MARIANI. Reprise de l historique (ligne 5TIHSGP4, mandat 14553) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('VXGSNU25', 'Acquereur au classeur : nan BEAL. Reprise de l historique (ligne VXGSNU25, mandat 14142) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('V0QL8N3G', 'Acquereur au classeur : nan EDDE DOMERGUE. Reprise de l historique (ligne V0QL8N3G, mandat 14252) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('B5VKBMW0', 'Acquereur au classeur : nan DENNAI. Reprise de l historique (ligne B5VKBMW0, mandat 14846) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('B5HZ3OV5', 'Acquereur au classeur : nan CHENEVIER. Reprise de l historique (ligne B5HZ3OV5, mandat 14847) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('AMKJIRYN', 'Acquereur au classeur : nan REYNAUD. Reprise de l historique (ligne AMKJIRYN, mandat 13865) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('H6CTRVR6', 'Acquereur au classeur : nan MERCIER. Reprise de l historique (ligne H6CTRVR6, mandat 13420) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('0GV2LNV2', 'Acquereur au classeur : nan BELLAT. Reprise de l historique (ligne 0GV2LNV2, mandat 3681) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('1290IIOC', 'Acquereur au classeur : nan MAIRIE DE ST CLAIR. Reprise de l historique (ligne 1290IIOC, mandat 12974) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('KO6QPUV7', 'Acquereur au classeur : nan FRESSENON. Reprise de l historique (ligne KO6QPUV7, mandat 12935) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('LWZL8V5M', 'Acquereur au classeur : nan ROYET. Reprise de l historique (ligne LWZL8V5M, mandat 3277) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('3S4ZWOFK', 'Acquereur au classeur : nan DI FORTI ROLLAND. Reprise de l historique (ligne 3S4ZWOFK, mandat 12864) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('ZQD27I3K', 'Acquereur au classeur : nan CROS. Reprise de l historique (ligne ZQD27I3K, mandat 11941) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('CSB367SG', 'Acquereur au classeur : nan GERY. Reprise de l historique (ligne CSB367SG, mandat 13010) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('DAATY4A7', 'Acquereur au classeur : nan FRANCOIS. Reprise de l historique (ligne DAATY4A7, mandat 12763) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('8WEM4UIX', 'Acquereur au classeur : nan GILIBERT. Reprise de l historique (ligne 8WEM4UIX, mandat 12214) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('ZMB56WW7', 'Acquereur au classeur : nan QUIBLIER. Reprise de l historique (ligne ZMB56WW7, mandat 12712) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('XXNOUH9H', 'Acquereur au classeur : nan BOISSEL. Reprise de l historique (ligne XXNOUH9H, mandat 12243) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('HUY49KEC', 'Acquereur au classeur : nan CANIVET. Reprise de l historique (ligne HUY49KEC, mandat 2332) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('3RFGZQ1E', 'Acquereur au classeur : nan DA-RIN. Reprise de l historique (ligne 3RFGZQ1E, mandat 2919) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('MN8HFEHN', 'Acquereur au classeur : nan ROME. Reprise de l historique (ligne MN8HFEHN, mandat 3030) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('U34PK32L', 'Acquereur au classeur : nan ABRIAL. Reprise de l historique (ligne U34PK32L, mandat 10806) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('5H96YY2I', 'Acquereur au classeur : SCI Les Coeurs Libres Forever, gérants Mme ALCARAS Raphaële M. STEVENIN Franck. Reprise de l historique (ligne 5H96YY2I, mandat 17686) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('D018N09A', 'Acquereur au classeur : Mme M. DRACHE Guy HIEM My. Reprise de l historique (ligne D018N09A, mandat 17704) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('1cc703d9', 'Acquereur au classeur : Mme MATRA Liliane. Reprise de l historique (ligne 1cc703d9, mandat 17667) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('86a190de', 'Acquereur au classeur : Mme GAFFIE Noémie. Reprise de l historique (ligne 86a190de, mandat 17894) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('861af493', 'Acquereur au classeur : Mme M. ROBERTS Camille et Jamie. Reprise de l historique (ligne 861af493, mandat 17169) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('77e6f1fc', 'Acquereur au classeur : Mme LAURENT Isabelle. Reprise de l historique (ligne 77e6f1fc, mandat 17882) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('8cf0e171', 'Acquereur au classeur : Mme RECEVEUR MATHIEU Marion - M. RECEVEUR Florent. Reprise de l historique (ligne 8cf0e171, mandat 17238) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('2962d089', 'Acquereur au classeur : ind. RYCKEMBUSH : Marguerite DE SEAUVE, Gilles RYCKEMBUSH, Louis RYCKEMBUSH, Simon RYCKEMBUSH. Reprise de l historique (ligne 2962d089, mandat 17863) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('591418b3', 'Acquereur au classeur : Mme JANY Priscillia - M. COUPAT Aurélien. Reprise de l historique (ligne 591418b3, mandat 17745) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('29277933', 'Acquereur au classeur : Mme M. ASTIER Valentin FAURE Anaïs. Reprise de l historique (ligne 29277933, mandat 17844) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('1649864f', 'Acquereur au classeur : M. MOULIN Bernard. Reprise de l historique (ligne 1649864f, mandat 17765) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('89cbcce9', 'Acquereur au classeur : Mme ASTIER Céline. Reprise de l historique (ligne 89cbcce9, mandat 17743) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('07cec9e1', 'Acquereur au classeur : M. DE FREITAS PEREIRA Wilson. Reprise de l historique (ligne 07cec9e1, mandat 17426) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('c08ff7cb', 'Acquereur au classeur : M. DEFOUR Jean-Luc. Reprise de l historique (ligne c08ff7cb, mandat 17859) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('6b02c91a', 'Acquereur au classeur : Mme M. SIMON Jean-Christophe et CHANIAL Céline. Reprise de l historique (ligne 6b02c91a, mandat 17915) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('7c7b5d8e', 'Acquereur au classeur : Mme M. ABRHAMYAN Abraham MALERYAN Asya. Reprise de l historique (ligne 7c7b5d8e, mandat 17910) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('0d6cad26', 'Acquereur au classeur : ind. BLANCHARD : Mme et M. Blanchard Didier et Laure, M. Blanchard Florent. Reprise de l historique (ligne 0d6cad26, mandat 18025) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('4205088d', 'Acquereur au classeur : Mme M. BOUZIN Dominique et Cécile. Reprise de l historique (ligne 4205088d, mandat 17909) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('dfe48dde', 'Acquereur au classeur : Mme M. POSTEL Roch TOLLARDO Jessica. Reprise de l historique (ligne dfe48dde, mandat 17338) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('650e65c8', 'Acquereur au classeur : Mme M. BOUNAIX Benjamin et Catherine. Reprise de l historique (ligne 650e65c8, mandat 18035) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('7e1dded4', 'Acquereur au classeur : M. BOUCHET Baptiste. Reprise de l historique (ligne 7e1dded4, mandat 17907) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('512f903b', 'Acquereur au classeur : M. DA SILVA FREITAS José. Reprise de l historique (ligne 512f903b, mandat 17265) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('6d229f85', 'Acquereur au classeur : Mme M. SIREUIL Jean-Louis et Muriel. Reprise de l historique (ligne 6d229f85, mandat 18094) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('f023c1d4', 'Acquereur au classeur : Mme M. LEPRETRE Romain et Guillemette. Reprise de l historique (ligne f023c1d4, mandat 17941) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('7f7c8e48', 'Acquereur au classeur : M. REMIS Jean-Christophe Mme CHOUVET Myriam. Reprise de l historique (ligne 7f7c8e48, mandat 16856) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('a89cbbdd', 'Acquereur au classeur : M. GLAISE Christophe Mme BEAUFORT Aurélie. Reprise de l historique (ligne a89cbbdd, mandat 17935) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('84331d2b', 'Acquereur au classeur : M. OSINGA Niels Mme HUININK Sanne. Reprise de l historique (ligne 84331d2b, mandat 18006) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('0c3629d5', 'Acquereur au classeur : M. CLABAUT Jean-Yves. Reprise de l historique (ligne 0c3629d5, mandat 18080) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('bdb548a3', 'Acquereur au classeur : M. CHAPUIS François. Reprise de l historique (ligne bdb548a3, mandat 16992) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.')
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
         'offre', 'accepted', d.dt,
         d.annonce, null, false,
         d.dossier_uuid, d.dossier_numero,
         'classeur',
         jsonb_build_object(
           'classeur_id_unique', d.id_unique,
           'classeur_lot', 'C5 lot B -- offres vente reglee',
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
  select count(*) into posees from app_affaire_ledger
   where transaction_origine = 'classeur'
     and (payload_json ->> 'classeur_lot') = 'C5 lot B -- offres vente reglee';
  if posees <> 64 then
    raise exception 'ARRET : %s ligne(s) de ce lot au lieu de 64', posees;
  end if;

  select count(*) into notees from app_affaire_note where origine = 'classeur';
  if notees < 64 then
    raise exception 'ARRET : %s note(s) seulement pour 64 offres', notees;
  end if;

  select count(*) into sans_marque from app_affaire_ledger
   where transaction_origine = 'classeur'
     and (payload_json ->> 'classeur_lot') = 'C5 lot B -- offres vente reglee'
     and (kind <> 'offre' or state <> 'accepted' or present_in_hektor
          or hektor_affaire_id is not null or app_chaine_id is null);
  if sans_marque <> 0 then
    raise exception 'ARRET : %s ligne(s) posees ne respectent pas la forme attendue', sans_marque;
  end if;

  select count(*) into avec_numero from app_affaire_ledger
   where transaction_origine = 'classeur'
     and (payload_json ->> 'classeur_lot') = 'C5 lot B -- offres vente reglee'
     and app_affaire_id < 1000000;
  if avec_numero <> 0 then
    raise exception 'ARRET : %s ligne(s) hors de la plage app (>= 1 000 000)', avec_numero;
  end if;

  -- ⭐ LE TEMOIN DE L'ACQUEREUR : sans acquereurs_json, le declencheur ne doit
  --   avoir cree AUCUNE partie pour ces lignes.
  select count(*) into avec_parties from app_affaire_partie p
    join app_affaire_ledger l on l.app_affaire_id = p.app_affaire_id
   where l.transaction_origine = 'classeur'
     and (l.payload_json ->> 'classeur_lot') = 'C5 lot B -- offres vente reglee';
  if avec_parties <> 0 then
    raise exception 'ARRET : %s partie(s) creees alors qu aucun acquereur n a ete pose', avec_parties;
  end if;

  raise notice 'OK : 64 offres posees, %s notes, 0 partie creee, toutes dans la plage app', notees;
end $$;

-- ── CE QUI VIENT D'ETRE POSE, a lire dans la sortie
select kind, state, present_in_hektor, transaction_origine,
       count(*) as lignes, min(app_affaire_id) as premier, max(app_affaire_id) as dernier
  from app_affaire_ledger
 where transaction_origine = 'classeur'
 group by 1,2,3,4;

commit;
