-- ═══════════════════════════════════════════════════════════════════════════
-- C4 (3e patch) -- LOT 1 : 80 TEXTES DE F . LOT 2 : 28 CONDITIONS DE CREDIT
-- Genere le 2026-11-17 par phase2/checks/c4_generer_lots_1_et_2_2026-11-17.py
--
-- ⭐⭐⭐ SA CORRECTION DU 17/11 : « MA REGLE SUR LES DONNEES DES TRANSACTIONS EN
--   COURS NE PORTAIT PAS SUR LES NOTES ». Sa regle protege contre LE CONFLIT ; la
--   bonne question est « HEKTOR PORTE-T-IL CETTE DONNEE ? », et la mesure dit NON
--   deux fois : aucune note chez Hektor, et `conditions_suspensives` est remplie
--   0 FOIS SUR 18 591 (il ne rend qu'un catalogue de 2 choix).
--
-- ⛔⛔ J'AVAIS ANNONCE 47 TEXTES PERDUS : ILS SONT 80. Mon critere cherchait le
--   nom d'entete « G » (c'est la LETTRE de la 7e colonne, entete COMMENTAIRES) --
--   un zero par construction -- puis, corrige, il confondait « la ligne a un
--   commentaire G » avec « LE TEXTE DE F est pose ». Ce sont deux textes.
--
-- ⭐⭐ LE LOT 1 EST UN COMPLEMENT, PAS UN REMPLACEMENT : la cle de app_affaire_note
--   est app_affaire_id SEUL, et 80 transactions portent deja une note. On AJOUTE
--   un paragraphe marque « [classeur F, suivi en cours au 17/11/2026] », et la sauvegarde datee garde le texte
--   d'avant pour que l'inverse le restaure a l'octet.
--
-- ⛔ L'ORIGINE DES NOTES COMPLETEES NE BOUGE PAS -- sinon les controles des 4 325
--   notes du 2e patch deviendraient faux. La marque est le PREFIXE du paragraphe.
--
-- RETOUR ARRIERE : patch_c4_lots_1_et_2_2026-11-17_INVERSE.sql
-- CONTROLES      : patch_c4_lots_1_et_2_2026-11-17_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════
begin;

-- ① LE GARDE-FOU : si le lot est deja pose, on ne rejoue pas
do $$
declare n_note integer; n_cond integer;
begin
  select count(*) into n_note from app_affaire_note
   where position('[classeur F, suivi en cours au 17/11/2026]' in texte) > 0;
  select count(*) into n_cond from app_affaire_condition
   where origine = 'classeur:F-credit';
  if n_note > 0 or n_cond > 0 then
    raise exception '⛔ DEJA POSE : % notes marquees et % conditions. '
      'Jouer l INVERSE d abord.', n_note, n_cond;
  end if;
end $$;

-- ② LA SAUVEGARDE DATEE : le texte EXACT d'avant, pour les notes qu'on complete
drop table if exists app_c4_note_avant_20261117;
create table app_c4_note_avant_20261117 as
  select app_affaire_id, texte, origine, now() as sauve_le
    from app_affaire_note
   where app_affaire_id in (3701, 16792, 1000137, 28568, 27285, 30754, 28921, 7106, 28897, 28625, 28944, 30688, 28964, 30810, 30702, 30818, 29022, 30714, 30747, 30699, 1000320, 30721, 1000318, 30798, 28985, 30771, 998, 30715, 28995, 30755, 29015, 30757, 30703, 29020, 30729, 30731, 30753, 30728, 30692, 30791, 30658, 30765, 30789, 30779, 30805, 30790, 30788, 30707, 30706, 30705, 30713, 30769, 30793, 30735, 30811, 30744, 30742, 30741, 30770, 30756, 30759, 30758, 30764, 30763, 30768, 30775, 30785, 30784, 30786, 30792, 30803, 30797, 30796, 30804, 30802, 30806, 30808, 30817, 30816, 30815);

do $$
declare n integer;
begin
  select count(*) into n from app_c4_note_avant_20261117;
  if n <> 80 then
    raise exception '⛔ LA SAUVEGARDE PORTE % lignes au lieu de 80', n;
  end if;
end $$;

-- ②bis LE CATALOGUE -- LES 2 CLAUSES NEUVES (sa decision du 17/11)
--    ⛔ `id` est TEXT, NOT NULL, SANS DEFAUT : on le FOURNIT (max numerique + 1).
--    ⭐ 91 jours est MESURE : sur les 2 lignes du classeur portant DPC *et* OPC,
--      l'ecart est de 90 et 91 jours -- les 3 mois d'instruction d'un permis.
insert into app_condition_catalogue (id, libelle, jours_defaut, rang)
values
    ('5', 'Depot du permis de construire', 0, 5),
    ('6', 'Obtention du permis de construire', 91, 6)
on conflict (id) do nothing;

-- ③ LOT 1 -- COMPLETER LES 80 NOTES EXISTANTES
--    ⭐ on AJOUTE un paragraphe, on ne remplace rien. Et la clause `position`
--      rend le geste IDEMPOTENT : rejoue, il n'ajoute pas deux fois.
update app_affaire_note n
   set texte = n.texte || chr(10) || v.fragment
  from (values
    (3701, '[classeur F, suivi en cours au 17/11/2026] 20/11 délib. CA18/11 Me Chalet'),
    (16792, '[classeur F, suivi en cours au 17/11/2026] 17/11 rdv VGuyStéph. DB30/10 - CI Philippe, Max et Serge Jay manquantes'),
    (1000137, '[classeur F, suivi en cours au 17/11/2026] 30/11 tél. M. Badiou suite rdv mairie'),
    (28568, '[classeur F, suivi en cours au 17/11/2026] 16/11 relance Mme Tholy att. accord ministère L. Rocher'),
    (27285, '[classeur F, suivi en cours au 17/11/2026] 19/11 rdv Vente DB02/11 Sauret 75KPTZ N. Coudert'),
    (30754, '[classeur F, suivi en cours au 17/11/2026] 07/12 10j. ODP16/12 DB15/1 Me Bougon  Antoine'),
    (28921, '[classeur F, suivi en cours au 17/11/2026] 19/11 retard ODP01/10 DB30/10 Me Labidoire'),
    (7106, '[classeur F, suivi en cours au 17/11/2026] 23/11 DP voisin DB29/1 Me Bouron'),
    (28897, '[classeur F, suivi en cours au 17/11/2026] 20/11 ODP15/11vousfinancer DB15/12 (avnt) Me Rochette'),
    (28625, '[classeur F, suivi en cours au 17/11/2026] C. Bravard'),
    (28944, '[classeur F, suivi en cours au 17/11/2026] 30/11 DPC30/11 OPC01/3 DB15/6 Me BDH / Me Damas  18393 à archiver après vente'),
    (30688, '[classeur F, suivi en cours au 17/11/2026] 24/11 rdv VenteCI-VODP DB24/12 Lemaître  EM70300'),
    (28964, '[classeur F, suivi en cours au 17/11/2026] 20/11 retard dPC30/9 PC31/12 accord eau DB01/3  Me Chazottes-Leconte/Barre'),
    (30810, '[classeur F, suivi en cours au 17/11/2026] 08/12ADP08/12 ODP08/01 DB05/02  Me Bérinchy'),
    (30702, '[classeur F, suivi en cours au 17/11/2026] 19/11 ADP30/10 PTZ ODP15/12  fact. chaudière  achat17383 DB30/1 Me Labidoire'),
    (30818, '[classeur F, suivi en cours au 17/11/2026] 19/11 prêt ok ? PUA SAFER DB30/4 PUV SAFER DB30/6 Me Robin'),
    (29022, '[classeur F, suivi en cours au 17/11/2026] 20/11 CUb  rdv Vente Me Chassaint DB09/12'),
    (30714, '[classeur F, suivi en cours au 17/11/2026] 03/12 ODP5/12  (V)cuve  accord juge contentieux DB05/1 Me Carton'),
    (30747, '[classeur F, suivi en cours au 17/11/2026] 23/11 ! ADP15/11 envoi SAFER ODP15/12 DB15/01  MDR bien V330062851'),
    (30699, '[classeur F, suivi en cours au 17/11/2026] 119500K'),
    (1000320, '[classeur F, suivi en cours au 17/11/2026] 23/11 EDD Coulaud Me Bougon  PTZ Antoine'),
    (30721, '[classeur F, suivi en cours au 17/11/2026] 01/12 ODP02/12  factures V. DB02/01 Me Goutorbe'),
    (1000318, '[classeur F, suivi en cours au 17/11/2026] 02/01 DPU Me Bouron-Oliver / Me Rongy (Ardes)Vente directe'),
    (30798, '[classeur F, suivi en cours au 17/11/2026] 02/12 SAFER DB04/2 Me Exbrayat/Giraud-Viallet38'),
    (28985, '[classeur F, suivi en cours au 17/11/2026] 23/11 rdv G1  rpse PC14/11 Auboyer pc'),
    (30771, '[classeur F, suivi en cours au 17/11/2026] 21/12 formalités DB23/1 M.Sauret/Fay67'),
    (998, '[classeur F, suivi en cours au 17/11/2026] Vente directe GGE'),
    (30715, '[classeur F, suivi en cours au 17/11/2026] 23/11 rpse agglo retrait DP DB15/12 Me Bouron-Oliver'),
    (28995, '[classeur F, suivi en cours au 17/11/2026] 23/11 copie C20/11 Me Latour'),
    (30755, '[classeur F, suivi en cours au 17/11/2026] 15/12 rdv VENTE DB15/1 Me Pailhes'),
    (29015, '[classeur F, suivi en cours au 17/11/2026] 14/12 ADP13/12 ODP13/01 DB13/2  Me Bougon / Me Besse'),
    (30757, '[classeur F, suivi en cours au 17/11/2026] 20/11 ADP19/11 ODP18/01 DB20/02 Me Sanial245K'),
    (30703, '[classeur F, suivi en cours au 17/11/2026] 23/11 7j. ODP30/11 DB29/12 Me Cornu/Lancry'),
    (29020, '[classeur F, suivi en cours au 17/11/2026] 01/12 rdv Me Cornu Gge Vente directe DEC.'),
    (30729, '[classeur F, suivi en cours au 17/11/2026] 18/11 ADP09/11 ODP15/12 relogmt-V DB27/3  E. Pereira / départ VL Gonzalez 09sept.'),
    (30731, '[classeur F, suivi en cours au 17/11/2026] 15/12 dPC15/12 oPC15/3 DB01/7 Latour / Boixadera PC'),
    (30753, '[classeur F, suivi en cours au 17/11/2026] 27/11 choix bq ODP16/12 DB16/1 Me Faure'),
    (30728, '[classeur F, suivi en cours au 17/11/2026] 30/11 DP  ADP30/11 ODP31/12 DB15/3 150Kpc maison inachevée'),
    (30692, '[classeur F, suivi en cours au 17/11/2026] 19/11 copie C18/11 Me Argoeuves / Pougalan'),
    (30791, '[classeur F, suivi en cours au 17/11/2026] 16/12 dDP16/12ADP ODP05/1 DP31/1 31/3 Latour/Ravel-D. pc'),
    (30658, '[classeur F, suivi en cours au 17/11/2026] 11/12 copie C10/12 Me Letessier pc'),
    (30765, '[classeur F, suivi en cours au 17/11/2026] 24/11 ADP23/11 ODP23/12 DB23/01 Me Goutorbe'),
    (30789, '[classeur F, suivi en cours au 17/11/2026] 30/11 ADP30/11 ODP08/1 DB01/2 Me Sauret'),
    (30779, '[classeur F, suivi en cours au 17/11/2026] 24/11 ADP26/11 ODP05/1 DB26/01'),
    (30805, '[classeur F, suivi en cours au 17/11/2026] 05/12 ADP05/12 ODP15/1 DB05/2 Me Macret'),
    (30790, '[classeur F, suivi en cours au 17/11/2026] 03/12 ADP03/12 ODP03/1 DB03/2 Me Roux'),
    (30788, '[classeur F, suivi en cours au 17/11/2026] 30/11 ADP30/11 ODP10/1 DB30/1 Breuil'),
    (30707, '[classeur F, suivi en cours au 17/11/2026] 11/12 ADP10/12 ODP11/1 DB31/1 Me Sanial / Zilic'),
    (30706, '[classeur F, suivi en cours au 17/11/2026] 17/11 ! copie C12/11 Me Didier cub'),
    (30705, '[classeur F, suivi en cours au 17/11/2026] 08/12 copie C7/12 Me Chomarat subvention Région'),
    (30713, '[classeur F, suivi en cours au 17/11/2026] 17/11 copie C13/11 Me Sauret'),
    (30769, '[classeur F, suivi en cours au 17/11/2026] 27/11 ADP26/11  DP(V) ODP26/12 DB26/1 Marion/Serpantié'),
    (30793, '[classeur F, suivi en cours au 17/11/2026] 18/12 18/12DPdivision DB30/1 Me Didier/Giroux69'),
    (30735, '[classeur F, suivi en cours au 17/11/2026] 17/11 CI-A  copie C16/11 Labidoire'),
    (30811, '[classeur F, suivi en cours au 17/11/2026] 08/12 ADP08/12 ODP08/01 DB08/02 Me Rigaud'),
    (30744, '[classeur F, suivi en cours au 17/11/2026] 20/11 C19/11-16h30 Me Mory/Monteiro'),
    (30742, '[classeur F, suivi en cours au 17/11/2026] 15/12 ADP13/12 ODP13/01 DB22/2 Me Brisson'),
    (30741, '[classeur F, suivi en cours au 17/11/2026] 18/11 copie C17/11 Robin fin nov.'),
    (30770, '[classeur F, suivi en cours au 17/11/2026] 23/11 ADP23/11 ODP31/12 DB01/2 Me Guillauma'),
    (30756, '[classeur F, suivi en cours au 17/11/2026] 18/11 copie C17/11 Bouron-O.'),
    (30759, '[classeur F, suivi en cours au 17/11/2026] 25/11 copie C24/11 C. Barre / Chomarat'),
    (30758, '[classeur F, suivi en cours au 17/11/2026] 28/11 copie C27/11 liée vente 18786 DEGROOTE / IMAW C18/11'),
    (30764, '[classeur F, suivi en cours au 17/11/2026] 07/12 copie C04/12 Metay / Prebost'),
    (30763, '[classeur F, suivi en cours au 17/11/2026] 24/11 copie C23/11 Chalet/Chassang46'),
    (30768, '[classeur F, suivi en cours au 17/11/2026] 23/11 copie C20/11 Me Tessier Antoine'),
    (30775, '[classeur F, suivi en cours au 17/11/2026] 02/12 copie C01/12 rdv Me Didier'),
    (30785, '[classeur F, suivi en cours au 17/11/2026] 25/11 copie C24/11 Christèle Me Chomarat'),
    (30784, '[classeur F, suivi en cours au 17/11/2026] 18/11 copie C17/11 Bougon/Khouri'),
    (30786, '[classeur F, suivi en cours au 17/11/2026] 02/12 copie C01/12 Me Latour'),
    (30792, '[classeur F, suivi en cours au 17/11/2026] 08/12 copie C07/12 Poyet'),
    (30803, '[classeur F, suivi en cours au 17/11/2026] 26/11 copie C25/11 Poyet / Chabanat'),
    (30797, '[classeur F, suivi en cours au 17/11/2026] 19/11 CI-A  Me Poyet/Chazotte'),
    (30796, '[classeur F, suivi en cours au 17/11/2026] 19/11 rdv PUA accord du juge habilitation Sauret'),
    (30804, '[classeur F, suivi en cours au 17/11/2026] 20/11 rdv Garde 134K40K 19/11'),
    (30802, '[classeur F, suivi en cours au 17/11/2026] 27/11 copie C26/11 Simonet'),
    (30806, '[classeur F, suivi en cours au 17/11/2026] 17/11 att. fonds notaire V'),
    (30808, '[classeur F, suivi en cours au 17/11/2026] 17/11 CI-A  rdv Me Sabot'),
    (30817, '[classeur F, suivi en cours au 17/11/2026] 20/11 rdv Me Champelovier'),
    (30816, '[classeur F, suivi en cours au 17/11/2026] 20/11 rdv Me Lucht-Rocher pc'),
    (30815, '[classeur F, suivi en cours au 17/11/2026] 19/11 copie C20/11  Me Didier/Josserand')
  ) as v(app_affaire_id, fragment)
 where n.app_affaire_id = v.app_affaire_id
   and position(v.fragment in n.texte) = 0;

-- ⑤ LOT 2 -- LES 28 CONDITIONS « Obtention Credit »
--    etat : la valeur par defaut 'attente'. On n'affirme JAMAIS une levee.
insert into app_affaire_condition
    (app_affaire_id, rang, libelle, jours, date_echeance, catalogue_id,
     app_dossier_id, app_chaine_id, note, origine)
values
    (30754, 1, 'Obtention Crédit', null, '2026-12-16'::date, '2', 1340947, 7108, '07/12 10j. ODP16/12 DB15/1 Me Bougon  Antoine', 'classeur:F-credit'),
    (28921, 1, 'Obtention Crédit', null, '2026-10-01'::date, '2', 1388157, 28921, '19/11 retard ODP01/10 DB30/10 Me Labidoire', 'classeur:F-credit'),
    (28897, 1, 'Obtention Crédit', null, '2026-11-15'::date, '2', 1388015, 28897, '20/11 ODP15/11vousfinancer DB15/12 (avnt) Me Rochette', 'classeur:F-credit'),
    (28944, 1, 'Depot du permis de construire', 0, '2026-11-30'::date, '5', 1386917, 28729, '30/11 DPC30/11 OPC01/3 DB15/6 Me BDH / Me Damas  18393 à archiver après vente', 'classeur:F-credit'),
    (28944, 2, 'Obtention du permis de construire', 91, '2027-03-01'::date, '6', 1386917, 28729, '30/11 DPC30/11 OPC01/3 DB15/6 Me BDH / Me Damas  18393 à archiver après vente', 'classeur:F-credit'),
    (28964, 1, 'Depot du permis de construire', 0, '2026-09-30'::date, '5', 1372469, 21810, '20/11 retard dPC30/9 PC31/12 accord eau DB01/3  Me Chazottes-Leconte/Barre', 'classeur:F-credit'),
    (30810, 1, 'Obtention Crédit', 31, '2027-01-08'::date, '2', 1387713, 28869, '08/12ADP08/12 ODP08/01 DB05/02  Me Bérinchy', 'classeur:F-credit'),
    (30702, 1, 'Obtention Crédit', 46, '2026-12-15'::date, '2', 4052229, 30702, '19/11 ADP30/10 PTZ ODP15/12  fact. chaudière  achat17383 DB30/1 Me Labidoire', 'classeur:F-credit'),
    (30714, 1, 'Obtention Crédit', null, '2026-12-05'::date, '2', 1670823, 28977, '03/12 ODP5/12  (V)cuve  accord juge contentieux DB05/1 Me Carton', 'classeur:F-credit'),
    (30747, 1, 'Obtention Crédit', 30, '2026-12-15'::date, '2', 4393130, 28981, '23/11 ! ADP15/11 envoi SAFER ODP15/12 DB15/01  MDR bien V330062851', 'classeur:F-credit'),
    (30721, 1, 'Obtention Crédit', null, '2026-12-02'::date, '2', 1387726, 30721, '01/12 ODP02/12  factures V. DB02/01 Me Goutorbe', 'classeur:F-credit'),
    (30757, 1, 'Obtention Crédit', 60, '2027-01-18'::date, '2', 1388301, 29018, '20/11 ADP19/11 ODP18/01 DB20/02 Me Sanial245K', 'classeur:F-credit'),
    (30703, 1, 'Obtention Crédit', null, '2026-11-30'::date, '2', 5998325, 29021, '23/11 7j. ODP30/11 DB29/12 Me Cornu/Lancry', 'classeur:F-credit'),
    (30729, 1, 'Obtention Crédit', 36, '2026-12-15'::date, '2', 5530493, 29026, '18/11 ADP09/11 ODP15/12 relogmt-V DB27/3  E. Pereira / départ VL Gonzalez 09sept.', 'classeur:F-credit'),
    (30731, 1, 'Depot du permis de construire', 0, '2026-12-15'::date, '5', 1379509, 29031, '15/12 dPC15/12 oPC15/3 DB01/7 Latour / Boixadera PC', 'classeur:F-credit'),
    (30731, 2, 'Obtention du permis de construire', 91, '2027-03-15'::date, '6', 1379509, 29031, '15/12 dPC15/12 oPC15/3 DB01/7 Latour / Boixadera PC', 'classeur:F-credit'),
    (30753, 1, 'Obtention Crédit', null, '2026-12-16'::date, '2', 1390884, 30644, '27/11 choix bq ODP16/12 DB16/1 Me Faure', 'classeur:F-credit'),
    (30728, 1, 'Obtention Crédit', 31, '2026-12-31'::date, '2', 1365082, 30649, '30/11 DP  ADP30/11 ODP31/12 DB15/3 150Kpc maison inachevée', 'classeur:F-credit'),
    (30791, 1, 'Obtention Crédit', null, '2027-01-05'::date, '2', 1387820, 30659, '16/12 dDP16/12ADP ODP05/1 DP31/1 31/3 Latour/Ravel-D. pc', 'classeur:F-credit'),
    (30765, 1, 'Obtention Crédit', 30, '2026-12-23'::date, '2', 6854385, 30665, '24/11 ADP23/11 ODP23/12 DB23/01 Me Goutorbe', 'classeur:F-credit'),
    (30789, 1, 'Obtention Crédit', 39, '2027-01-08'::date, '2', 2124147, 30669, '30/11 ADP30/11 ODP08/1 DB01/2 Me Sauret', 'classeur:F-credit'),
    (30779, 1, 'Obtention Crédit', 40, '2027-01-05'::date, '2', 1388070, 30670, '24/11 ADP26/11 ODP05/1 DB26/01', 'classeur:F-credit'),
    (30805, 1, 'Obtention Crédit', 41, '2027-01-15'::date, '2', 1386443, 30675, '05/12 ADP05/12 ODP15/1 DB05/2 Me Macret', 'classeur:F-credit'),
    (30790, 1, 'Obtention Crédit', 31, '2027-01-03'::date, '2', 5189126, 30684, '03/12 ADP03/12 ODP03/1 DB03/2 Me Roux', 'classeur:F-credit'),
    (30788, 1, 'Obtention Crédit', 41, '2027-01-10'::date, '2', 1388126, 30700, '30/11 ADP30/11 ODP10/1 DB30/1 Breuil', 'classeur:F-credit'),
    (30769, 1, 'Obtention Crédit', 30, '2026-12-26'::date, '2', 1387633, 30712, '27/11 ADP26/11  DP(V) ODP26/12 DB26/1 Marion/Serpantié', 'classeur:F-credit'),
    (30811, 1, 'Obtention Crédit', 31, '2027-01-08'::date, '2', 4904743, 30725, '08/12 ADP08/12 ODP08/01 DB08/02 Me Rigaud', 'classeur:F-credit'),
    (30770, 1, 'Obtention Crédit', 38, '2026-12-31'::date, '2', 4393129, 30740, '23/11 ADP23/11 ODP31/12 DB01/2 Me Guillauma', 'classeur:F-credit')
on conflict (app_affaire_id, rang) do nothing;

-- ⑥ LES CONTROLES, DANS LA MEME TRANSACTION -- un seul faux et tout tombe
do $$
declare n integer;
begin
  select count(*) into n from app_affaire_note
   where position('[classeur F, suivi en cours au 17/11/2026]' in texte) > 0;
  if n <> 80 then
    raise exception '⛔ LOT 1 : % notes marquees au lieu de 80', n;
  end if;

  select count(*) into n from app_affaire_condition where origine = 'classeur:F-credit';
  if n <> 28 then raise exception '⛔ LOT 2 : % conditions au lieu de 28', n; end if;

  -- ⭐ LES VOISINS SONT INTACTS
  select count(*) into n from app_affaire_note where origine = 'classeur';
  if n <> 195 then raise exception '⛔ LES 195 NOTES DE C5 ONT BOUGE : %', n; end if;
  select count(*) into n from app_affaire_note
   where origine in ('classeur:F', 'classeur:G', 'classeur:F+G');
  if n <> 4325 then raise exception '⛔ LES 4 325 NOTES DU 2e PATCH ONT BOUGE : %', n; end if;
  select count(*) into n from app_affaire_condition where origine = 'saisie';
  if n <> 5 then raise exception '⛔ LES 5 CONDITIONS SAISIES ONT BOUGE : %', n; end if;

  -- ⭐⭐ LE TEXTE D'AVANT EST TOUJOURS LA : on a COMPLETE, pas remplace
  select count(*) into n
    from app_c4_note_avant_20261117 s
    join app_affaire_note a on a.app_affaire_id = s.app_affaire_id
   where position(s.texte in a.texte) = 0;
  if n <> 0 then
    raise exception '⛔ % notes ont PERDU leur texte d origine -- on remplace !', n;
  end if;

  -- ⭐ aucune condition en levee, aucune note vide, echeance et catalogue partout
  select count(*) into n from app_affaire_condition
   where origine = 'classeur:F-credit' and etat <> 'attente';
  if n <> 0 then raise exception '⛔ % conditions ne sont pas en attente', n; end if;
  select count(*) into n from app_affaire_note where coalesce(btrim(texte), '') = '';
  if n <> 0 then raise exception '⛔ % notes vides', n; end if;
  select count(*) into n from app_affaire_condition
   where origine = 'classeur:F-credit' and date_echeance is null;
  if n <> 0 then raise exception '⛔ % conditions sans echeance', n; end if;

  -- ⭐⭐ CHAQUE CONDITION POINTE UNE CLAUSE QUI EXISTE VRAIMENT au catalogue --
  --   une jointure, pas une liste en dur : c'est la base qui repond.
  select count(*) into n from app_affaire_condition c
   where c.origine = 'classeur:F-credit'
     and not exists (select 1 from app_condition_catalogue k
                      where k.id = c.catalogue_id);
  if n <> 0 then raise exception '⛔ % conditions pointent une clause INEXISTANTE', n; end if;

  -- ⭐ LE CATALOGUE EST A 6, et les 4 d'avant sont INTACTES
  select count(*) into n from app_condition_catalogue;
  if n <> 6 then
    raise exception '⛔ LE CATALOGUE PORTE % clauses au lieu de 6', n;
  end if;
  select count(*) into n from app_condition_catalogue
   where id in ('1', '2', '3', '4');
  if n <> 4 then
    raise exception '⛔ LES 4 CLAUSES D ORIGINE ONT BOUGE : %', n;
  end if;

  raise notice '✅ LOT 1 : % textes de F . LOT 2 : % conditions . catalogue a %',
    80, 28, 6;
end $$;

commit;
