-- ════════════════════════════════════════════════════════════════════════════
-- C5 / LOT B -- LES 24 OFFRES « ANNULEE » DU CLASSEUR
-- 16/11/2026 . chantier classeur, tache 3.3 lot B . genere par
-- phase2/checks/poser_offres_annulees_classeur_2026-11-16.py
-- ════════════════════════════════════════════════════════════════════════════
--
-- CE QU'ON POSE : 24 offres que le classeur porte et que nous n'avons pas, dont
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
-- RETOUR ARRIERE : patch_compromis_en_attente_classeur_2026-11-16_INVERSE.sql
-- CONTROLES      : patch_compromis_en_attente_classeur_2026-11-16_REPETITION.sql
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
     and (payload_json ->> 'classeur_lot') = 'C5 lot B -- compromis en attente';
  if deja <> 0 then
    raise exception 'ARRET : %s ligne(s) de CE LOT existent deja -- il ne doit pas etre rejoue', deja;
  end if;

  if not exists (select 1 from pg_class where relname = 'app_affaire_id_app_seq') then
    raise exception 'ARRET : la sequence app_affaire_id_app_seq est introuvable';
  end if;
end $$;

-- ── LES 24 OFFRES, ET LEUR NOTE, DANS UNE SEULE INSTRUCTION
with donnees (id_unique, chaine, dossier, annonce, dossier_uuid, dossier_numero, dt) as (
  values
    ('d049cda8', 1000320, 1387763, 61793, '3121e368-0756-46b0-a025-157f20d58757'::uuid, 'D2026-0284', '2026-11-13'),
    ('43faf7d9', 28995, 1897573, 62563, 'dfde452c-2f95-4d67-80ba-7527427299b7'::uuid, 'D2026-0292', '2026-11-20'),
    ('039da22e', 29015, 3824830, 62768, '4f75d714-44b1-405b-ae06-457509fb8ba8'::uuid, 'D2026-0294', '2026-11-13'),
    ('2dfa6ef3', 30656, 4052217, 62802, '28907d1a-a646-4ddc-9b2a-26a0562f427d'::uuid, 'D2026-0309', '2026-11-18'),
    ('c1bbc7a9', 30658, 5998329, 62970, '722bc8fc-eba8-4bbe-a384-530d119697c3'::uuid, 'D2026-0313', '2026-12-10'),
    ('2a4a0c03', 30706, 1386351, 58957, '40f0c0d1-7649-4cd8-a334-4351cc856311'::uuid, 'D2026-0327', '2026-11-12'),
    ('ecfcc143', 30705, 1670795, 62464, '04c93206-e5b1-43f3-8a70-e6966c346d18'::uuid, 'D2026-0325', '2026-12-07'),
    ('a2abd36c', 30713, 3654535, 62740, '8739ae38-889e-48e6-8961-b7ddf984ae38'::uuid, 'D2026-0329', '2026-11-13'),
    ('7cb7142f', 30735, 2804138, 62667, '1e79d666-56c3-46c1-b766-7bd436a98943'::uuid, 'D2026-0331', '2026-11-16'),
    ('35996b7e', 30744, 1387950, 61965, '1879ffb3-d6f4-462b-995d-9168e89ef1ff'::uuid, 'D2026-0337', '2026-11-19'),
    ('351fca42', 30742, 1384927, 54799, '746339cb-c07c-4c76-b0f9-93dfb1277a3a'::uuid, 'D2026-0335', '2026-11-13'),
    ('d66a35e4', 30741, 1386366, 58970, '0fd582af-959f-4e8d-9c5f-e8e69e33b706'::uuid, 'D2026-0334', '2026-11-17'),
    ('e2779d8b', 30756, 4336294, 62832, '00876048-76bc-45e4-9281-b4394cc062bd'::uuid, 'D2026-0341', '2026-11-17'),
    ('42ae8884', 30759, 7589143, 63156, '1fe21cca-3009-4d61-9111-652d0a388bdd'::uuid, 'D2026-0339', '2026-11-24'),
    ('d5d073fc', 30758, 7589240, 63255, '56fbdff5-3d71-43af-8416-7179c1cf55f4'::uuid, 'D2026-0342', '2026-11-27'),
    ('b9872912', 30764, 1346923, 1998, '76f4126c-a92f-4638-a722-b4d347c6828c'::uuid, 'D2026-0333', '2026-12-04'),
    ('5804a343', 30763, 7344113, 63088, '19c0c301-74c9-493e-b0e8-21684e5c58e7'::uuid, 'D2026-0343', '2026-11-23'),
    ('616df9e7', 30768, 1388343, 62381, '5b423ab8-f4ef-4810-857f-11a796a4ea7e'::uuid, 'D2026-0344', '2026-11-20'),
    ('d5b2fa0d', 30775, 1372474, 43453, '562f9364-3eb7-4c62-af11-92c90abb7a23'::uuid, 'D2026-0340', '2026-12-01'),
    ('1a474908', 30784, 1386896, 59471, '9f19a15b-5ffa-4e6a-a0f3-551289601b13'::uuid, 'D2026-0354', '2026-11-17'),
    ('63790b81', 30786, 1379248, 49618, '8bbe564a-66a7-4313-86ba-83810c7dc542'::uuid, 'D2026-0355', '2026-12-01'),
    ('dad56e75', 30803, 7589117, 63129, 'a7fc10c8-cb45-48d9-9efb-59e8931a3a96'::uuid, 'D2026-0363', '2026-11-25'),
    ('dedeafeb', 30802, 4336303, 62840, 'f59aa3f4-c0e3-4373-af78-ee22e4e833b1'::uuid, 'D2026-0357', '2026-11-26'),
    ('7543e4fb', 30815, 7589128, 63140, 'e90270b5-e389-402a-a29d-f3508346d2ac'::uuid, 'D2026-0369', '2026-11-20')
),
notes (id_unique, texte) as (
  values
    ('d049cda8', 'Acquereur au classeur : Mme NGNASOKE Sarah. Reprise de l historique (ligne d049cda8, mandat 18820) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('43faf7d9', 'Acquereur au classeur : Mme M. BARRALLON Noëlle et François. Reprise de l historique (ligne 43faf7d9, mandat 18720) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('039da22e', 'Acquereur au classeur : SCI VP IMMO représentée par Bertrand Valentin et Lopez Paul-André. Reprise de l historique (ligne 039da22e, mandat 18821) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('2dfa6ef3', 'Acquereur au classeur : SAS IMAW représentée par M. Paillasseur Olivier. Reprise de l historique (ligne 2dfa6ef3, mandat 18786) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('c1bbc7a9', 'Acquereur au classeur : M. JAYOL Maxime Mme RUITON Aurélie. Reprise de l historique (ligne c1bbc7a9, mandat 18856) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('2a4a0c03', 'Acquereur au classeur : Mme FAUDON Sophie. Reprise de l historique (ligne 2a4a0c03, mandat 18145) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('ecfcc143', 'Acquereur au classeur : Fédération de pêche de Haute-Loire représentée par son président M. Lionel Martin. Reprise de l historique (ligne ecfcc143, mandat 18690) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('a2abd36c', 'Acquereur au classeur : Mme ALLEPUZ Fanny. Reprise de l historique (ligne a2abd36c, mandat 18788) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('7cb7142f', 'Acquereur au classeur : sté. IRISOLARIS représentée par M. Jérôme Duclaux. Reprise de l historique (ligne 7cb7142f, mandat 18754) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('35996b7e', 'Acquereur au classeur : Mme MARTINS Lilou. Reprise de l historique (ligne 35996b7e, mandat 18505) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('351fca42', 'Acquereur au classeur : M. GUTIERREZ Alan Mme LEPICIER Camille. Reprise de l historique (ligne 351fca42, mandat 18861) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('d66a35e4', 'Acquereur au classeur : M. VEYRAT Romain. Reprise de l historique (ligne d66a35e4, mandat 18208) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('e2779d8b', 'Acquereur au classeur : M. AUZAT Christian Mme AUZAT Maria. Reprise de l historique (ligne e2779d8b, mandat 18798) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('42ae8884', 'Acquereur au classeur : Mme SAHUC Cyrian. Reprise de l historique (ligne 42ae8884, mandat 18913) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('d5d073fc', 'Acquereur au classeur : M. Mme LEVEQUE David et Gabrielle. Reprise de l historique (ligne d5d073fc, mandat 18930) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('b9872912', 'Acquereur au classeur : Mme CAGNIN Edwige M. LOUDJANI Nathan. Reprise de l historique (ligne b9872912, mandat 18054) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('5804a343', 'Acquereur au classeur : M. FRAZIER Théo Mme PAUTAIRE Laurie. Reprise de l historique (ligne 5804a343, mandat 18927) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('616df9e7', 'Acquereur au classeur : M. DE VERA Gabriel. Reprise de l historique (ligne 616df9e7, mandat 18656) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('d5b2fa0d', 'Acquereur au classeur : M. CHAMBON Alain. Reprise de l historique (ligne d5b2fa0d, mandat 18101) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('1a474908', 'Acquereur au classeur : M. RUFFINONI Eloi. Reprise de l historique (ligne 1a474908, mandat 18358) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('63790b81', 'Acquereur au classeur : M/ CONREAU Pascal. Reprise de l historique (ligne 63790b81, mandat 18763) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('dad56e75', 'Acquereur au classeur : Mme M. GIL MENDES Henrique et Selia. Reprise de l historique (ligne dad56e75, mandat 18977) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('dedeafeb', 'Acquereur au classeur : Mme M. GUERIN Daniel et Bernadette. Reprise de l historique (ligne dedeafeb, mandat 18873) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.'),
    ('7543e4fb', 'Acquereur au classeur : M. BIANCHI Damien Mme ARCHER Elsa. Reprise de l historique (ligne 7543e4fb, mandat 18899) -- non resolu en contact, pose en note pour ne pas reveiller le calcul des parties ni la regle [D] du chainage.')
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
         'compromis', 'active', d.dt,
         d.annonce, null, false,
         d.dossier_uuid, d.dossier_numero,
         'classeur',
         jsonb_build_object(
           'classeur_id_unique', d.id_unique,
           'classeur_lot', 'C5 lot B -- compromis en attente',
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
     and (payload_json ->> 'classeur_lot') = 'C5 lot B -- compromis en attente';
  if posees <> 24 then
    raise exception 'ARRET : %s ligne(s) de ce lot au lieu de 24', posees;
  end if;

  select count(*) into notees from app_affaire_note where origine = 'classeur';
  if notees < 24 then
    raise exception 'ARRET : %s note(s) seulement pour 24 offres', notees;
  end if;

  select count(*) into sans_marque from app_affaire_ledger
   where transaction_origine = 'classeur'
     and (payload_json ->> 'classeur_lot') = 'C5 lot B -- compromis en attente'
     and (kind <> 'compromis' or state <> 'active' or present_in_hektor
          or hektor_affaire_id is not null or app_chaine_id is null);
  if sans_marque <> 0 then
    raise exception 'ARRET : %s ligne(s) posees ne respectent pas la forme attendue', sans_marque;
  end if;

  select count(*) into avec_numero from app_affaire_ledger
   where transaction_origine = 'classeur'
     and (payload_json ->> 'classeur_lot') = 'C5 lot B -- compromis en attente'
     and app_affaire_id < 1000000;
  if avec_numero <> 0 then
    raise exception 'ARRET : %s ligne(s) hors de la plage app (>= 1 000 000)', avec_numero;
  end if;

  -- ⭐ LE TEMOIN DE L'ACQUEREUR : sans acquereurs_json, le declencheur ne doit
  --   avoir cree AUCUNE partie pour ces lignes.
  select count(*) into avec_parties from app_affaire_partie p
    join app_affaire_ledger l on l.app_affaire_id = p.app_affaire_id
   where l.transaction_origine = 'classeur'
     and (l.payload_json ->> 'classeur_lot') = 'C5 lot B -- compromis en attente';
  if avec_parties <> 0 then
    raise exception 'ARRET : %s partie(s) creees alors qu aucun acquereur n a ete pose', avec_parties;
  end if;

  raise notice 'OK : 24 offres posees, %s notes, 0 partie creee, toutes dans la plage app', notees;
end $$;

-- ── CE QUI VIENT D'ETRE POSE, a lire dans la sortie
select kind, state, present_in_hektor, transaction_origine,
       count(*) as lignes, min(app_affaire_id) as premier, max(app_affaire_id) as dernier
  from app_affaire_ledger
 where transaction_origine = 'classeur'
 group by 1,2,3,4;

commit;
