-- ════════════════════════════════════════════════════════════════════════════
-- C5 / LOT B -- LES 35 OFFRES « ANNULEE » DU CLASSEUR
-- 16/11/2026 . chantier classeur, tache 3.3 lot B . genere par
-- phase2/checks/poser_offres_annulees_classeur_2026-11-16.py
-- ════════════════════════════════════════════════════════════════════════════
--
-- CE QU'ON POSE : 35 offres que le classeur porte et que nous n'avons pas, dont
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
-- RETOUR ARRIERE : patch_compromis_annules_classeur_2026-11-16_INVERSE.sql
-- CONTROLES      : patch_compromis_annules_classeur_2026-11-16_REPETITION.sql
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
     and (payload_json ->> 'classeur_lot') = 'C5 lot B -- compromis annules';
  if deja <> 0 then
    raise exception 'ARRET : %s ligne(s) de CE LOT existent deja -- il ne doit pas etre rejoue', deja;
  end if;

  if not exists (select 1 from pg_class where relname = 'app_affaire_id_app_seq') then
    raise exception 'ARRET : la sequence app_affaire_id_app_seq est introuvable';
  end if;
end $$;

-- ── LES 35 OFFRES, ET LEUR NOTE, DANS UNE SEULE INSTRUCTION
with donnees (id_unique, chaine, dossier, annonce, dossier_uuid, dossier_numero, dt) as (
  values
    ('LCQ8H7S0', 23983, 1376945, 47538, 'fcd06ffc-d3da-4a9c-abb3-7dc559ad43fa'::uuid, 'D2025-0097', '2025-06-18'),
    ('EO8MXFE9', 20267, 1370524, 41699, 'f0efe69e-f2f8-4481-a0a0-10b639b8f7c4'::uuid, 'D2024-0080', '2024-04-15'),
    ('CW4IYXO2', 21, 1100105, 53, '86e1b44d-6ec2-417e-9ae6-1805d6f4feb9'::uuid, 'D2024-0041', '2024-03-04'),
    ('HOJ11PVC', 8918, 1344507, 17728, '558f60c1-fef8-4481-b1ea-4ac628b239d1'::uuid, 'D2022-0610', '2023-12-06'),
    ('N67O7CLW', 8910, 1344495, 17717, '7c9bb369-9166-4fea-bf2e-56236e99c871'::uuid, 'D2023-0028', '2023-12-06'),
    ('0TQB1SLL', 8926, 1344527, 17746, 'ad298d5d-8747-4926-9230-d3cbe693f1c2'::uuid, 'D2022-0613', '2023-12-06'),
    ('RKWNRBV1', 17377, 1365332, 36993, '225be8e6-42d6-435d-803a-809e6373046f'::uuid, 'D2023-0412', '2023-10-20'),
    ('WI335HTC', 26070, 1380255, 50574, '40645df2-d3bb-4aae-86fc-913005f85f2e'::uuid, 'D2023-0330', '2023-08-31'),
    ('SWSN80FQ', 14817, 1358179, 30376, 'd132cae5-54ba-45bb-9523-e96e03106cdb'::uuid, 'D2023-0060', '2023-03-16'),
    ('FWCFAN6O', 4372, 1392090, 9608, 'a7a8cb3d-51a1-45b5-8e75-b33e7ddf8c22'::uuid, 'D2022-0299', '2022-07-30'),
    ('LKBO1TOH', 4290, 1391982, 9510, '0af15948-ccc6-4aef-a1ed-c7f1b70a4dd1'::uuid, 'D2022-0563', '2022-12-21'),
    ('9WQ204HP', 4484, 1392245, 9748, '4692c6a5-f03a-48f1-b728-9b8f34e43d11'::uuid, 'D2022-0218', '2022-06-15'),
    ('9KHYVR1M', 24381, 1377555, 48093, 'ed5f7219-fdbd-4496-aeae-89625ca08a65'::uuid, 'D2020-0543', '2020-12-04'),
    ('87QOXR64', 17429, 1365545, 37184, 'af913e02-2b7b-4e97-9225-07427760c7a8'::uuid, 'D2022-0019', '2022-02-11'),
    ('8NZ6V6XB', 11560, 1351504, 24368, '4cedd9e4-7078-491b-a9c7-77dd2af6ab08'::uuid, 'D2021-0725', '2022-01-04'),
    ('T2GZOY5O', 20075, 1370292, 41467, '45d80190-d071-44d9-b9f6-fdbfc0c607c7'::uuid, 'D2021-0382', '2021-07-02'),
    ('S3HOG6UL', 17390, 1365377, 37032, '34ba7c01-bedd-41ed-b64c-30f40b8d7b49'::uuid, 'D2021-0593', '2021-11-03'),
    ('6U5DQQ4J', 24453, 1377623, 48154, '81157531-02ee-418f-9a19-f31fa5ca23c1'::uuid, 'D2021-0536', '2021-10-28'),
    ('2FBR2M9U', 1103, 1351054, 2393, 'ea522c29-a262-4689-96ed-14b59ed4e8fc'::uuid, 'D2021-0312', '2021-06-16'),
    ('VMWFLLW4', 23053, 1375146, 45891, '7ed85d66-e14c-40c1-b783-beb4016f0ac8'::uuid, 'D2021-0339', '2021-06-17'),
    ('JRN2I7TM', 27448, 1383682, 53678, '2bdf7e26-baaa-407f-9a36-cf2a8c7cb07d'::uuid, 'D2021-0272', '2021-05-31'),
    ('R0JRVFDC', 16382, 1362132, 34066, 'baa8f240-6b63-437d-8dc7-735f68043bfe'::uuid, 'D2020-0428', '2020-10-27'),
    ('UAER0F0F', 7904, 1342455, 15881, '027e832e-11b2-43f6-ac4f-150cf7be8939'::uuid, 'D2020-0187', '2020-07-15'),
    ('a277ccfe', 20227, 1370467, 41629, '39247a9c-65cc-40de-9aaa-92db8ee5ba92'::uuid, 'D2025-0330', '2025-11-27'),
    ('545cf27f', 28762, 1387047, 59610, 'aedc0371-1c8c-4510-bf5f-e209ee5b7549'::uuid, 'D2026-0143', '2026-05-13'),
    ('1bbfa76b', 28857, 1387628, 61667, '2b7b9bbb-76a5-4fff-9e3a-cee613ef1eee'::uuid, 'D2026-0144', '2026-06-08'),
    ('a48e8a17', 28905, 1388048, 62055, 'db3e942d-8cdf-43c4-8e59-11e1e29da3f2'::uuid, 'D2026-0159', '2026-07-30'),
    ('037e509b', 28908, 1388060, 62066, 'c7608250-0bc5-4e36-aee0-d5ad6b1d4eab'::uuid, 'D2026-0183', '2026-06-22'),
    ('b21b79f1', 28907, 1388055, 62061, 'f408c5b6-7072-43cb-a47b-2a8178160920'::uuid, 'D2026-0182', '2026-06-30'),
    ('62da86ce', 16223, 1361522, 33517, '1e9029a4-9438-4f30-8a24-f066d61c2eb8'::uuid, 'D2026-0207', '2026-07-17'),
    ('5786a3cc', 3697, 1390884, 8489, '57d6bf25-1159-40c0-937e-05135c1ba27f'::uuid, 'D2026-0206', '2026-07-13'),
    ('af8d7986', 25710, 1379255, 49624, '56e5cc64-25b0-4d23-a876-d65ff3551266'::uuid, 'D2026-0226', '2026-07-31'),
    ('fa06e4e5', 28931, 1388276, 62311, 'b682f6ff-2ca8-4526-a7d0-77163231b4dc'::uuid, 'D2026-0239', '2026-07-28'),
    ('d6cd8868', 1000316, 1379255, 49624, 'ceb0979b-c150-40a3-9f66-9e7afcc45603'::uuid, 'D2026-0277', '2026-10-05'),
    ('c4ef091c', 30645, 1370255, 41433, '926ddaab-0c4b-4e3c-94a4-76cfb009827e'::uuid, 'D2026-0295', '2026-10-08')
),
notes (id_unique, texte) as (
  values
    ('LCQ8H7S0', 'Acquereur au classeur : SCI PINELLI gérant Pinelli Jordan. Reprise de l historique (ligne LCQ8H7S0, mandat 17213) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('EO8MXFE9', 'Acquereur au classeur : nan MARTIN COTTIER. Reprise de l historique (ligne EO8MXFE9, mandat 15909) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('CW4IYXO2', 'Acquereur au classeur : nan TALBI. Reprise de l historique (ligne CW4IYXO2, mandat 16494) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('HOJ11PVC', 'Acquereur au classeur : nan AVCI VELI. Reprise de l historique (ligne HOJ11PVC, mandat 15240) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('N67O7CLW', 'Acquereur au classeur : nan CELIKOZ Abdil. Reprise de l historique (ligne N67O7CLW, mandat 15235) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('0TQB1SLL', 'Acquereur au classeur : nan CELIKOZ Ahmet&Dondu*. Reprise de l historique (ligne 0TQB1SLL, mandat 15234) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('RKWNRBV1', 'Acquereur au classeur : nan THOMAS ROUX. Reprise de l historique (ligne RKWNRBV1, mandat 16169) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('WI335HTC', 'Acquereur au classeur : nan TISSIER RUTZ. Reprise de l historique (ligne WI335HTC, mandat 15892) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('SWSN80FQ', 'Acquereur au classeur : nan GORRY. Reprise de l historique (ligne SWSN80FQ, mandat 14399) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('FWCFAN6O', 'Acquereur au classeur : nan BELMONT. Reprise de l historique (ligne FWCFAN6O, mandat 14159) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('LKBO1TOH', 'Acquereur au classeur : nan PARFAIT. Reprise de l historique (ligne LKBO1TOH, mandat 15104) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('9WQ204HP', 'Acquereur au classeur : nan MARCOS. Reprise de l historique (ligne 9WQ204HP, mandat 4273) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('9KHYVR1M', 'Acquereur au classeur : nan SCIORTINO. Reprise de l historique (ligne 9KHYVR1M, mandat 4117) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('87QOXR64', 'Acquereur au classeur : nan RIGAUD. Reprise de l historique (ligne 87QOXR64, mandat 4231) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('8NZ6V6XB', 'Acquereur au classeur : nan LOPEZ MONOIR. Reprise de l historique (ligne 8NZ6V6XB, mandat 14026) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('T2GZOY5O', 'Acquereur au classeur : nan PAOLONE. Reprise de l historique (ligne T2GZOY5O, mandat 4369) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('S3HOG6UL', 'Acquereur au classeur : nan CHEYNE. Reprise de l historique (ligne S3HOG6UL, mandat 13739) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('6U5DQQ4J', 'Acquereur au classeur : nan BRYCKAERT. Reprise de l historique (ligne 6U5DQQ4J, mandat 3943) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('2FBR2M9U', 'Acquereur au classeur : nan BOUFEDJI. Reprise de l historique (ligne 2FBR2M9U, mandat 13487) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('VMWFLLW4', 'Acquereur au classeur : nan PARRELLA. Reprise de l historique (ligne VMWFLLW4, mandat 12755) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('JRN2I7TM', 'Acquereur au classeur : nan BASTIDE. Reprise de l historique (ligne JRN2I7TM, mandat 4209) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('R0JRVFDC', 'Acquereur au classeur : nan DUPONT PIPPIA. Reprise de l historique (ligne R0JRVFDC, mandat 12921) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('UAER0F0F', 'Acquereur au classeur : nan GIRARD. Reprise de l historique (ligne UAER0F0F, mandat 3789) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('a277ccfe', 'Acquereur au classeur : Mme ROUX Louise. Reprise de l historique (ligne a277ccfe, mandat 17842) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('545cf27f', 'Acquereur au classeur : M. MONTEL Pierre. Reprise de l historique (ligne 545cf27f, mandat 18481) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('1bbfa76b', 'Acquereur au classeur : Mme M. DJAFRI Mathieu et Florence. Reprise de l historique (ligne 1bbfa76b, mandat 18425) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('a48e8a17', 'Acquereur au classeur : Mme M. RIVET-PETIT Olivier et Marie-Anaïs. Reprise de l historique (ligne a48e8a17, mandat 18555) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('037e509b', 'Acquereur au classeur : M. ROUSSEL Edmond. Reprise de l historique (ligne 037e509b, mandat 18549) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('b21b79f1', 'Acquereur au classeur : M. HIMBLOT Christophe. Reprise de l historique (ligne b21b79f1, mandat 18601) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('62da86ce', 'Acquereur au classeur : M. REY Charles Mme TETON Marianne. Reprise de l historique (ligne 62da86ce, mandat 18557) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('5786a3cc', 'Acquereur au classeur : M. LEVITE Noah. Reprise de l historique (ligne 5786a3cc, mandat 18088) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('af8d7986', 'Acquereur au classeur : Mme M. FRAISSE Gérard et Brigitte. Reprise de l historique (ligne af8d7986, mandat 17929) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('fa06e4e5', 'Acquereur au classeur : M. BILDINICI Ihsam. Reprise de l historique (ligne fa06e4e5, mandat 18642) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('d6cd8868', 'Acquereur au classeur : Mme M. BRUYERE Bertrand et Nicole. Reprise de l historique (ligne d6cd8868, mandat 17929) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('c4ef091c', 'Acquereur au classeur : Mme M. PIFFARETTI Corinne et Adrien. Reprise de l historique (ligne c4ef091c, mandat 18038) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.')
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
         'compromis', 'cancelled', d.dt,
         d.annonce, null, false,
         d.dossier_uuid, d.dossier_numero,
         'classeur',
         jsonb_build_object(
           'classeur_id_unique', d.id_unique,
           'classeur_lot', 'C5 lot B -- compromis annules',
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
     and (payload_json ->> 'classeur_lot') = 'C5 lot B -- compromis annules';
  if posees <> 35 then
    raise exception 'ARRET : %s ligne(s) de ce lot au lieu de 35', posees;
  end if;

  select count(*) into notees from app_affaire_note where origine = 'classeur';
  if notees < 35 then
    raise exception 'ARRET : %s note(s) seulement pour 35 offres', notees;
  end if;

  select count(*) into sans_marque from app_affaire_ledger
   where transaction_origine = 'classeur'
     and (payload_json ->> 'classeur_lot') = 'C5 lot B -- compromis annules'
     and (kind <> 'compromis' or state <> 'cancelled' or present_in_hektor
          or hektor_affaire_id is not null or app_chaine_id is null);
  if sans_marque <> 0 then
    raise exception 'ARRET : %s ligne(s) posees ne respectent pas la forme attendue', sans_marque;
  end if;

  select count(*) into avec_numero from app_affaire_ledger
   where transaction_origine = 'classeur'
     and (payload_json ->> 'classeur_lot') = 'C5 lot B -- compromis annules'
     and app_affaire_id < 1000000;
  if avec_numero <> 0 then
    raise exception 'ARRET : %s ligne(s) hors de la plage app (>= 1 000 000)', avec_numero;
  end if;

  -- ⭐ LE TEMOIN DE L'ACQUEREUR : sans acquereurs_json, le declencheur ne doit
  --   avoir cree AUCUNE partie pour ces lignes.
  select count(*) into avec_parties from app_affaire_partie p
    join app_affaire_ledger l on l.app_affaire_id = p.app_affaire_id
   where l.transaction_origine = 'classeur'
     and (l.payload_json ->> 'classeur_lot') = 'C5 lot B -- compromis annules';
  if avec_parties <> 0 then
    raise exception 'ARRET : %s partie(s) creees alors qu aucun acquereur n a ete pose', avec_parties;
  end if;

  raise notice 'OK : 35 offres posees, %s notes, 0 partie creee, toutes dans la plage app', notees;
end $$;

-- ── CE QUI VIENT D'ETRE POSE, a lire dans la sortie
select kind, state, present_in_hektor, transaction_origine,
       count(*) as lignes, min(app_affaire_id) as premier, max(app_affaire_id) as dernier
  from app_affaire_ledger
 where transaction_origine = 'classeur'
 group by 1,2,3,4;

commit;
