-- patch_3bis_commentaires_avis_2026-11-27 -- ETAPE 3 BIS, LOT A (COMMENTAIRES + AVIS), chez nous seulement, jamais chez Hektor
-- Genere par phase2/checks/etape_3bis_commentaires_et_avis_generer_patch_2026-11-27.py (passage officiel 84, image 2026-11-26_094931)
-- Retour arriere : ..._INVERSE.sql . Controle : ..._REPETITION.sql

begin;
-- 1. LA GARDE : rien de ce lot n'est deja pose, et les sauvegardes n'existent pas
do $$ begin
  if exists (select 1 from public.app_affaire_note where ecrit_par = 'classeur:3bis:2026-11-27')
     or to_regclass('public.app_affaire_note_avant_3bis_20261127') is not null or to_regclass('public.app_classeur_avis_avant_3bis_20261127') is not null then
    raise exception '⛔ garde : le lot 3 bis A est deja (en partie) pose -- ce patch ne se rejoue pas'; end if;
end $$;
-- 2. LES SAUVEGARDES DATEES (ce que l'inverse rendra a l'octet), RLS allumee, aucun droit ouvert
create table public.app_affaire_note_avant_3bis_20261127 as select * from public.app_affaire_note where app_affaire_id in (3699, 7106, 9965, 15854, 16787, 16792, 19409, 19415, 19634, 23881, 27285, 28569, 28703, 28764, 28853, 28897, 28914, 28921, 28944, 28964, 28970, 28972, 28978, 28979, 28985, 28989, 28991, 28995, 29001, 29022, 30661, 30676, 30681, 30687, 30688, 30691, 30692, 30701, 30702, 30706, 30709, 30715, 30722, 30729, 30735, 30736, 30741, 30744, 30746, 30747, 30754, 30755, 30756, 30757, 30759, 30763, 30764, 30765, 30766, 30768, 30770, 30771, 30779, 30780, 30784, 30789, 30791, 30796, 30797, 30798, 30804, 30806, 30808, 30815, 30816, 30817, 1000320, 1000321);
create table public.app_classeur_avis_avant_3bis_20261127 as select * from public.app_classeur_avis where id_unique in ('0b25afef', '14fdb07f', '1d3bc808', '35996b7e', '3b5db3cc', '4d354b1a', '606bb180', '6d4d0aee', '78bb247a', '84c91bb8', '8bcc3b63', 'a10a87c8', 'a2780e6f', 'a56ce827', 'a6d41ca1', 'a75aef8c', 'afd672fa', 'bfe07c3b', 'c6c8bc29', 'c9fe7ffa', 'd9a0630c', 'db0d5e8d', 'df0ce30c', 'e2779d8b', 'e2951cb3', 'e6b0043e', 'f1f51b2c');
alter table public.app_affaire_note_avant_3bis_20261127 enable row level security; revoke all on public.app_affaire_note_avant_3bis_20261127 from public, anon, authenticated;
alter table public.app_classeur_avis_avant_3bis_20261127 enable row level security; revoke all on public.app_classeur_avis_avant_3bis_20261127 from public, anon, authenticated;
-- 3. LES NOTES NEUVES (47)
insert into public.app_affaire_note (app_affaire_id, app_dossier_id, app_chaine_id, origine, texte, ecrit_par)
values
  (30825, 7589455, 30825, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 19.11 PUV 8 Décembre à11h
17.11 OFFRE ok
CI ok', 'classeur:3bis:2026-11-27'),
  (17770, 1366312, 17769, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (1000313, 2407417, 30699, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 16.11 VENTE mercredi 16 décembre 2026 de 18:00
29.10 ADP mess tél à NADEGE : FISE reçue par la cliente. ODP va suivre. La client ne veut signer que mi-décembre.
ADP pj. Capital protect (Sophie Bernaud) du 16 oct.
22.10 ADP demandée à Nadège
01.10 PUV ok
28.09 copie PUV demandée à Nadège
15.09 PUV fixée vendredi 25 septembre chez Maître Barbier
❗MANDAT : M. Jacky Bussy (gendre) doit également signer car il a hérité de son épouse Sandrine Chapignac même s''il s''agissait d''un bien propre de Mme, M. hérite de tout son patrimoine avec ses enfants Pierre et Julie. Jacky absent du mandat mais signataire de la PUV (proc à sa fille signée en présence de Me Barbier)
10.09 rdv PUV : Nadège a relancé le notaire ce matin, la clerc doit la rappeler
02.09 OFFRE ok Nadège envoie le dossier au notaire ce jour
28.08 OFFRE en attente manque 1/6 vend.
ok Sonia Chapignac
CI ok
Notaire : Barbier à Tence pour les deux parties . 
"Je suis en attente du reste des signatures mais j’ai eu l’accord oral . J’ai également un accord de principe que je joindrais au dossier. "', 'classeur:3bis:2026-11-27'),
  (30830, 1384856, 30830, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 18.11 OFFRE ok MDR car MDV 18053 expiré. Vu avec Franck 100% Nico
CI ok
Nico : "Le contrôle de raccordement tout à l''égout a eu lieu ce matin.
En principe Maître BRISSON à Thiers, devrait s''occuper du dossier tout seul et on devrait faire une vente directe. J''attends que M. BELOEIL me confirme ça.
Dès réception du rapport du contrôle, j''envoie le dossier complet au notaire"', 'classeur:3bis:2026-11-27'),
  (30837, 1344361, 30837, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 24.11 OFFRE pas encore contresignée
19.11 OFFRE prix mandat signé 3 gérants de la SCI en attente acceptation vendeurs
CI ok', 'classeur:3bis:2026-11-27'),
  (30845, 7589154, 30845, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 24.11 OFFRE ok
CI ok', 'classeur:3bis:2026-11-27'),
  (7910, 1342473, 7908, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (14228, 1356559, 14224, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (30842, 1388373, 30842, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 23.11 OFFRE ok CI-ok
🅿 simul. en attente', 'classeur:3bis:2026-11-27'),
  (30820, 1388303, 30820, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 20.11 PUV lundi 7 décembre 2026 à 11 h 00.
16.11 OFFRE ok 🏠cpmis signé
CI ok', 'classeur:3bis:2026-11-27'),
  (19133, 1368501, 19131, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- ind.TROUILLET SOUVIGNHEC/POCHELON PARLANTI - 80 000 € -', 'classeur:3bis:2026-11-27'),
  (30824, 3824828, 30824, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 17.11 OFFRE ok cdt : Cub + prêt + absence pollution des sols + absence cuves ou assainissement + absence servitude
CI ok', 'classeur:3bis:2026-11-27'),
  (6393, 1338568, 6391, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- BARRI/DELAUNAY - 254 000 €', 'classeur:3bis:2026-11-27'),
  (4236, 1391873, 4234, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- ind.Ledda/Bonnefoi - 278 000 €', 'classeur:3bis:2026-11-27'),
  (7115, 1340968, 7115, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (19154, 1368538, 19152, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (4783, 1336308, 4781, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (3650, 1390780, 3647, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- LAFFONT/POTTIER - 460 000 €', 'classeur:3bis:2026-11-27'),
  (27987, 1384486, 27984, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (2490, 1387286, 2490, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (17366, 1365248, 17366, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (9372, 1345612, 9370, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- Blanchet/Vallentin et Charvolin - 200 000 €', 'classeur:3bis:2026-11-27'),
  (27714, 1383988, 27712, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (6590, 1339151, 6588, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (28145, 1384835, 28145, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- Messadaa / Chambon - 92 000 €', 'classeur:3bis:2026-11-27'),
  (24620, 1377830, 24618, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (4930, 1336492, 4928, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (15170, 1359102, 15169, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (27170, 1383342, 27170, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (14121, 1356267, 14119, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- Lucht/Simonet vendu avec réf 3955', 'classeur:3bis:2026-11-27'),
  (2165, 1385496, 2163, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- RIVOLIER/sarl BEMATID (Berthaut) - 42 000 €', 'classeur:3bis:2026-11-27'),
  (26698, 1382351, 26695, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (6341, 1338495, 6341, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (1029, 1347703, 1027, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (4414, 1392151, 4412, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- C02/3Reporté ok20/1 Auboyer déssaisie LONG Juge surendettement vend. > MDR', 'classeur:3bis:2026-11-27'),
  (7122, 1340983, 7122, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- Losego Marthon/Lagrenee - 16 000 €', 'classeur:3bis:2026-11-27'),
  (27528, 1383776, 27527, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- réglée', 'classeur:3bis:2026-11-27'),
  (30827, 3654535, 30713, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 17.11 PUV ok
p12 🅿80K 20a 3.7% < 13 JANV
****
16.11 PUV copie demandée à Sandrine
29.10 PUV 13 nov. 9h.
27.10 rdv CPMIS : relance Sandrine
>> J''ai relancé ce matin et le spanc doit passer la semaine prochaine mais ce n''est pas ça qui bloque je pense, c''est juste long...
20.10 Sandrine en congé. Retour 27oct. Pour l''instant cpmis pas encore fixé
06.10 OFFRE : manque commune du bien et nom de Mme Boursier dans les propriétaires. 
CI ok
Etude de financement CM ok', 'classeur:3bis:2026-11-27'),
  (30848, 7589465, 30848, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 25.11 OFFRE ok
CI ok 
Le contrôle assainissement est prévu le mardi 1er décembre
Le notaire en charge du dossier devrait être Maître LABIDOIRE à Thiers', 'classeur:3bis:2026-11-27'),
  (30826, 1387075, 30826, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 25.11 PUV rdv demandé à Marion
17.11 OFFRE charge acq. avec MDR alors que MDV 18286 en cours et publié charge vendeur. Mess. tél. à Marion pour savoir pk ? Elle a vu avec Franck, pour éviter de négocier les honos.
CI ok', 'classeur:3bis:2026-11-27'),
  (30841, 4052215, 30841, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 23.11 OFFRE ok CI ok
Mme CHASTAGNER divorcée le 3sept.2026 de M. LINOSSIER signe la vente de sa maison avec Stéphanie le 17déc.2026', 'classeur:3bis:2026-11-27'),
  (30836, 5701204, 30836, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 25.11 OFFRE ok
notaire Maître Latour à Craponne et envoi du dossier semaine dès réception des diags prévus vendredi. 
20.11 Finalement M. Flory ne voulant pas régler les 4000€ préfère vendre. En attente offre contresignée
19.11 Envoi à Marion d''un protocole d''accord prévoyant le règlement d''une indemnité à hauteur de nos honoraires pour qu''elle le fasse signer et récupère le chèque. Une facture d''indemnité lui sera envoyé acquittée une fois le chèque encaissé.
18.11 Marion a eu le vendeur, il persiste et ne veut plus vendre, attendra le décès de son père, il s''agit de son ancien hangar de menuiserie, mais serait ok pour payer les honoraires d''agence.
10.11 OFFRE prix mandat sans prêt.
LITIGE : le père du vendeur ne veut pas que son fils vende à ce prix (donateur avec  interdiction de vendre sans son accord).', 'classeur:3bis:2026-11-27'),
  (30809, 7589284, 30809, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 10.11 OFFRE 17000€ H1000€ signée
MANDAT 17000€ H1500€
CI ok', 'classeur:3bis:2026-11-27'),
  (30821, 1386619, 30821, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 24.11 PUV Mardi 8 décembre, à 15 heures.
17.11 Notaire : Maître  BIONDA / Tél : 04 66 57 00 25 / Mail : aramon@30013.notaires.fr.
"Concernant la date de la signature de l'' acquisition, j''aimerais qu'' elle soit au 15 février 2027 ?
Le dépôt de garantie serait de 3 % , soit la somme de 2382€ ?
Merci de m'' informer si ces demandes sont acceptées .
Cordialement  Franck SICARD"
16.11 OFFRE ok
CI ok
Notaire acq. en attente', 'classeur:3bis:2026-11-27'),
  (30843, 1386927, 30843, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 23.11 OFFRE ok CI-A ok SIMUL BP
BOREL Sebastien 0612211141 agnes.borel@live.fr
Notaire  Maître Begon à Celles sur Durolle pour le dossier Serre : Vendeurs et acquéreurs', 'classeur:3bis:2026-11-27'),
  (30801, 7589442, 30801, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 20.11 LISTE MOBILIER en attente : Elodie doit faire une liste de mobilier pour le 27 mais ses acq. sont partis de la région et elle devait voir avec eux les meubles restants. Je lui ai dit de le faire une visio.
16.11 rdv C27/11-9h à confirmer
M. Laurembourle achèterait également un PP par Elodie, en cours de négo.
13.11 DOSSIER transmis aux notaires
06.11 OFFRE SCI ok MDR ok mais en nom propre
CI ok
L''acquéreur (sci royale) sera représenté par Maître Monteiro Nuno (idem vente st etienne sur usson Lilou Martins), et le vendeur par Maître Rimoux Rogue Christelle à St Amand Tallende.', 'classeur:3bis:2026-11-27'),
  (30829, 1387873, 30829, 'classeur:G', 'G : COMMENTAIRES du classeur, relu le 26/11/2026 -- 18.11 OFFRE ok sous réserve liste des matériaux (V) pour finir les travaux (A)
Ils ont rdv ce Dimanche ensemble pour lister.
CI ok', 'classeur:3bis:2026-11-27');
-- 4. LES PARAGRAPHES DATES AJOUTES (78 pieces) -- le texte d'avant reste intact au-dessus
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] PB parcelle d''accès au garage (AZ-430 10m²) CNPF non propriétaire (succ. de 7 propriétaires)

31.08.2026 rpse CNPF :
vous avez pris contact avec notre ingénieur territorial Monsieur Geoffroy que je mets en copie et qui a pris la suite de Monsieur Couvin, parti à la retraite. J''ai tenté de vous joindre à l''instant mais votre ligne était occupée et la personne qui a pris l''appel m''a confirmé que je pouvais vous envoyer ce mail d''explication.
Notre établissement est toujours désireux de vendre ce garage. Etant par définition établissement public nous avions pour obligation règlementaire de consulter les Domaines en vue d''une estimation avant de pouvoir procéder à un vote en Conseil d''Administration du CNPF dont nous sommes devenus délégation régionale.
Avec l''aide de mon correspondant parisien du CNPF nous avions accéléré les demandes et présenté nos requêtes sous diverses formes mais malheureusement les Domaines n''ont répondu que trop tardivement par rapport à la date de vente prévue le 7 juillet dernier. Aussi le CNPF n''a pas été en mesure de présenter sa délibération au vote du CA comme convenu. 
A ce jour nous savons donc par les Domaines que dans notre cas le CNPF peut procéder directement à la vente. Notre prochain CA est prévu le 18 novembre prochain et j''ai préparé personnellement un projet de délibération accompagné de toutes les pièces que j''ai archivées depuis que je suis ce dossier.
Entre temps notre dernier bilan amiante allait forcément dépasser la durée de validité légale et nous en avions commandé un nouveau qui a été réalisé le 3 juillet dernier.
Le garage est toujours à la vente, je ne manquerai pas de vous transmettre la délibération lorsqu''elle aura été votée et signée par qui de droit.
En remerciant par avance les époux MACHABERT pour leur compréhension, 
28.08.2026 CNPF relancé par Nico étude Chalet
06.07.2026 relance Christèle
>> "vente reportée pour cnpf - pas de date pour le service des domaines"
02.07 Demande à Christèle si vente bien reportée ?
16.06.2026 CHRISTELE : je viens d''avoir MJEOFFROY, pour les diags, pas de souci de ce côté Là
En revanche, il m''a informé que le CNPF avait l''obligation de faire intervenir le service des domaines pour une estimation. Par conséquent,  la vente prévue le 07 juillet pourrait être reportée ...
09.06.2026 VENTE fixée 07 juillet à 14h
29.05.2026 Nico attend encore une formalité
congés Christèle 8 au 25 mai
29.04.2026 Nico (clerc) attend le DPU. Christèle ne sait pas sous quel délai.
24.04.2026 relance Christèle
Congés Christèle 30 mars au 1er avril
18.03.2026 Idem
27.02.2026 Idem
26.01.2026 RDV vente relance Christèle
12.01.2026 RDV vente relance Christèle
22.12.2025 RDV vente pas encore fixé
15.12.2025 RDV vente demandé à Christèle ?
>> "J’ai pas encore de date J’ai relancé 
01.12.2025 M.COUVIN ayant quitter ses fonctions, merci d''envoyer toute correspondance au sujet de la vente à l''attention de la Directrice Mme AL Soleihavoup al.soleilhavoup@cnpf.fr
et en copie au bureau du Puy le-puy@cnpf.fr
l''interlocuteur est M.JEOFFROY au 06 62 25 32 36 - mail perso : eric.jeoffroy@cnpf.fr
27.11.2025 Christele : Je viens d’informer M. Machabert que Maître CHALET peut établir la vente du garage sans avoir à régulariser la petite parcelle AZ 430, ce qui évite ainsi les frais supplémentaires.
En conséquence, M. Machabert confirme qu’il souhaite rester sur l’offre initiale afin d’éviter toute modification susceptible de retarder encore la signature de l’acte.
Dans l''attente du rendez-vous pour signer l''acte
27.6.2025 avancement dossier ? @Christele
>> eu Christèle, Nico Reynaud lui a dit que ça ne servait à rien de le relancer sur ce dossier qui ne bougera pas avant 2026 selon lui, du fait de la complexité de contacter les 7 propriétaires et qu''il s''en occupe à temps perdu
21.5.2025 PB parcelle d''accès Nico Reynaud s''en est occupé, il y a 7 propriétaires à contacter pour une cession à titre gratuit. Christèle vient de lui transmettre l''accord des parties CNPF et Machabert pour un partage des frais de notaire.

---------------------------
Delphine BLANCHARD
8 févr. 2023
Relance CHRISTELE le 30/1 : n''a pas le temps de s''occuper du dossier... me demande de m''en charger.
Relance Me Bonnichon
Delphine BLANCHARD
Delphine BLANCHARD
8 févr. 2023
>rpse Me Bonnichon : "En réponse à votre demande, je vous indique avoir essayé de contacter les consorts KAEPPELIN, au nombre de cinq, agés, et suis sans réponse de leur part."
>DECISION ACQ ? : demande à Christele d''en avertir son acq. et de voir s''il achète tjrs sans pouvoir lui dire quand il pourra signer
Afficher moins
Delphine BLANCHARD
Delphine BLANCHARD
20 févr. 2023
DECISION ACQ : relance Christele
Delphine BLANCHARD
Delphine BLANCHARD
17 mars 2023
DECISION ACQ : Christèle me dit qu''elle n''a toujours pas le temps de s''en occuper, le fera quand elle pourra. Je lui a répondu que je ne voulais pas garder ce dossier pour rien, que déjà je relance régulièrement le notaire mais si l''acquéreur n''achète plus je ne vois pas l''intérêt.
Afficher moins
Delphine BLANCHARD
Delphine BLANCHARD
21 mars 2023
RPSE CHRISTELE M.MACHABERT est toujours intéressé
Delphine BLANCHARD
Delphine BLANCHARD
21 mars 2023
MAIL au notaire pour savoir s''il y a une solution ?
Delphine BLANCHARD
Delphine BLANCHARD
16 juin 2023
Eu Christèle, elle relance le notaire car n''a pas non plus de nouvelle
Delphine BLANCHARD
Delphine BLANCHARD
28 juil. 2023
Mail à Christèle: As-tu eu des nouvelles pour ce dossier?
Delphine BLANCHARD
Delphine BLANCHARD
13 oct. 2023
Christèle a demandé à un autre notaire de l''étude de se pencher sur le dossier car pas de solution pour Me Bonnichon
Delphine BLANCHARD
Delphine BLANCHARD
13 mars 2024
Point dossier demandé à Christèle
Delphine BLANCHARD
Delphine BLANCHARD
10 avr. 2024
Christèle posera la question au notaire mais pense que rien n''a bougé car certains indivisaires propriétaires de la petite parcelle ne répondent pas
Delphine BLANCHARD
Delphine BLANCHARD
3 juin 2024
Christèle relance le notaire cette semaine mais elle pense qu''il a abandonné le dossier. Si tjrs pas avancé, on annulera l''affaire.
Delphine BLANCHARD
Delphine BLANCHARD
21 juin 2024
Christèle a à nouveau relancé le notaire mais à priori rien n''a avancé. Je lui fais un mail également de mon côté ce jour
Delphine BLANCHARD
Delphine BLANCHARD
15:14 20 mars 2025
Christèle a repris contact avec CNPF et M. Machabert qui souhaitent toujours poursuivre l''affaire et sont ok pour changer de notaire. Elle envoie le dossier à Me Chalet
Le dossier avait été annulé Me Bonnichon ne cherchant aucune solution.' where app_affaire_id = 3699;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 24.11 DP voisin : demande à Claire si elle a réussi à le voir ?
>> "non après 2 courriers mis dans sa boite non plus mais Jean marc a contacté un avocat et un courrier va lui être envoyé cette semaine avec les mentions de l''avocat et les répercussions et préjudice causé s''il ne se manifeste pas..."
16.11 DP voisin point demandé à Claire, recours tiers ? Claire a laissé des courriers dans la boîte aux lettres sans réponse. Elle doit y passer à nouveau ce jeudi. La DP a plus de 15ans donc pas de recours possible.
04.11 AVNT signé pj.
30.10 PROROGATION DB30oct > 29janv. rédigée, en cours de signature
21.10 REUNION ACQ+VEND+CLAIRE :
à la suite de notre rendez vous entre acquéreurs et vendeur à la maison objet de la vente pré-citée ce jour,  il a été convenu:
- une prorogation de 3 mois de la promesse 
- Mr Sagouis va contacter un avocat en droit immobilier 
- Récupération des DP/ DAACT auprès de la mairie concernant le voisin et son bloc clim et parabole. 
- Nous allons essayer de nous réunir tous les 4 et le voisin après les vacances scolaires.
21.10 Voisin serait en règle suite DP autorisée. La secrétaire de mairie recherche le document car il devrait y avoir une réserve du fait que les tvx nécessitaient une servitude privée.
15.10 CLAIRE a conservé le RDV mais attend que M. Sagouis l''appelle lorsque son voisin est présent chez lui pour lui faire retirer sa PAC et sa parabole. Il n''est jamais allé cherché la LRAR du notaire donc pas averti.
13.10 conf. V29/10 ? mess. tél à Claire
08.10 REPORT V29/10-17H30 à confirmer parties.
06.10 BLOC + PARABOLE à enlever par le voisin : Claire a rdv ce vendredi avec lui.
17.09 BLOC + PARABOLE à enlever par le voisin : tél Claire : sur rép.
09.09  BLOC + PARABOLE à enlever par le voisin : "Après échanges avec Mr Sagouis, il souhaite que le courrier soit remis par voie d''huissier au voisin , il prend à sa charge les frais inhérents  et attend les informations quant à cet envoi. 
Nous avons noté la modification de la date de réitération au mercredi 14 octobre à 16h comme convenu hier par téléphone.
J''informe les acquéreurs ce jour."
02.09 Mail de Claire au notaire pour avoir confirmation parabole + bloc
01.09 Demande faite à Claire de vérifier que la cdt est levée ou qu''elle le soit avant la vente.
17.08 condition suspensive réalisée ?
>>"la notaire s''en est occupé , on va leur laisser le temps de passer le mois d''aout afin sur ce point là.
27.07 Conditions suspensives p.11 : Absence de servitude : suppression de la parabole et du bloc climatisation 
23.07 mail à Claire pour copie
RPSE: c''est le 27 !! 
- congés Claire du 6 au 12 juillet
06.07 PUV fixée 21 JUILLET à 10h
29.06 Claire n''a pas eu de nvelle du notaire, elle la relance
24.06 DOSSIER envoyé à Me Bouron-O.
CI ok
18.06 OFFRE ok sans condition
CI-A et notaire en attente
MANDAT expiré 14mai2026' where app_affaire_id = 7106;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 19.11 AVNT signé de l''acq. et transmis à Me Regent pour signatures vendeurs. En attente.
06.11 AVNT tjrs pas signé car le notaire avait laissé un partie stabilotée non complétée, du coup il faut que les notaires se mettent d''accord. Me Regent est très difficilement joignable.
30.10 AVNT signé ?
23.10 AVNT signé ? Les vendeurs ne l''ont tjrs pas signé, Stéphanie a relancé le notaire.
12.10 AVNT signé ?
>> "il est entrain de se signer. Mr Lewandoski a déjà signé, les vendeurs cette semaine.
28.09 RENEGO 270K net. 280K FAI acceptée par les vendeurs, Stéphanie a fait une demande d''avenant auprès du notaire la semaine dernière, elle le relance car n''a pas eu de nouvelle.
21.09 RENEGO : M. Lewandowski propose 280K, en cours de réflexion du côté des vendeurs.
31.08 RENEGO : nouvelle offre en cours
05.08 RENEGO : la mairie a supprimé toutes les OAP du secteur et a mis les permis en sursis à statuer, une partie du terrain est devenu inconstructible.
M. Lewandowski est parti en congé. A son retour il fera une nouvelle offre autour de 280K pour réhabiliter les 2 maisons et faire 3 constructions.
31.07 PA mail à Stéphanie : le permis d''aménager devait être obtenu au plus tard aujourd''hui. C''est le cas?
>>RPSE message vocal Stéphanie: RDV ce matin avec le service d''urbanisme, il va falloir refaire un avenant car surface terrain divisé par 2+permis de sursis à statuer. Lundi RDV sur place avec l''acquéreur pour nouvelle proposition prix 
05.06 AVNT pj. modif : prix 415K > 390K et délais PA 31juil. purgé au 1er nov. ODP < 6 nov. 2026 DB14nov. + ajout condition particulière de création de servitude de passage sur AB147 au profit de AB128 conforme à l''OAP.
25.05 relance Stéph. AVNT
>> "Il est entrain de ce signer. Je dois le récupérer jeudi. 
18.05 tél. Stéph : AVNT rédigé, les parties sont en train de le signer.
congés retour Stéph. 18 mai
 07.05 AVNT relance Stéphanie
>> "J''ai relancer deux fois cette semaine. Je suis entrain de les rappeler"
23.04 AVNT rédigé, Me Régent doit le validé avant l''envoi aux parties
21.04 Relance Stéph. La date butoir du compromis est dans moins d''un mois (15 mai 2026), sais-tu si M. Lewandowski a trouvé une solution et sous quel délai il pourra réaliser l''achat ?
Sinon, je te laisse faire le point avec lui et revenir vers moi stp.
>> On attend l''avenant du notaire.  Je te tiens informée 
18.03 Relance Stéph. Sais-tu si les devis ont été réalisés pour l''accès et si vendeurs et acquéreurs ont trouvé une entente pour poursuivre la vente ? 
>> On devrait l avoir aujourd''hui. 
J''ai relancer 3 fois....
13.02 Stéph. Il faudrait un budget de 100K pour faire l''accès. Le vendeur est prêt à participer pour 25K. Les clients voulaient que Stéph s''occupe d''obtenir des devis, elle leur a dit à raison que ce n''était pas son travail.
L''acq n''a pas déposé un PC complet car savait qu''il aurait un refus. Mais de ce fait, s''il a un refus pour défaut de pièce il sera en tort.
ACQ en congés
06.02 suite RDV parties du 04 fév. ? tél Steph. NRP
16.01 Pas encore la réponse de la mairie. Stéphanie organise un rdv entre vend et acq la sem du 9 fév. pour faire le point
09.01 PA Eu Stéphanie : il sera refusé car la mairie ne veut pas que l''accès se fasse par l''accès actuel de la maison. M. Lewandowski ne lâche pas le projet mais doit négocier avec Cogecoop pour passer sur l''OAP ce qui leur enlèvera 1 parcelle constructible et il aura certainement la voirie à ses frais. De ce fait il va certainement renégocier le prix.
En attente de la réponse officielle de la mairie 
13.11 récépissé PA ok PA 042 147 25 00006 déposé le 01 oct. 2025 instruction 3 mois > 01 janv. 2026
07.11 demande à Stéphanie si un accord avec la mairie a été trouvé ?
>> j''ai relancer semaine dernière...je le relance
01.10 PA déposé dans le délai. M. Lewandowski lui envoie les docs. Par contre, il a rdv avec la mairie car elle l''oblige à passer sur la voirie de l''OAP à côté (cogecoop+Loire Habitat) alors que le projet de l''OAP a été validé sans voirie... Cela modifierai tout le projet. + revoir le nbre de maison à la baisse (4) mais ça, ça ne poserait pas de pb.
26.9 PA déposé ? Stéphanie l''appelle et me tient informée
ind. Varona / Lewandowski Cie Immobilière d''Amenagement 415 000 €' where app_affaire_id = 9965;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 Dernière relance SMS. Franck n''engagera pas de frais de procédure si pas de réponse.
16.11 Fin des 15j pour paiement : Vu Franck : faire une relance d''ici fin de semaine
30.10 AR ce jour
26.10 LRAR Mise en demeure de paiement à Mme Bouthier et M. Guilloton
08.10 SMS à Mme Bouthier : si pas de réponse avant la fin de semaine, lancement de la procédure.
07.10 Mme Bouthier ne m''a pas rappelée
06.10 TEL à Mme Bouthier 06.43.10.72.93 : au travail. Me rappelle demain 9h15/30
M. Guilloton 07.89.86.01.70
25.09 TEL à Mme Bouthier pour lui dire que si nous trouvons une entente amiable, nous ne demanderons pas les 7000€ dus mais une partie seulement. Elle en discute avec son conjoint et reviens vers moi en début de semaine prochaine.
22.09 Mme Bouthier ne signera pas le protocole car les vendeurs lui ont dit que c''était le notaire qui demandait une indemnité mais que de leur côté ils ne la souhaitent pas.
TEL à Mme et M. Staraci : dans 1 premier temps ils me disent qu''ils suivent ce que leur notaire leur conseil et dans un 2nd temps, me disent qu''ils ne souhaite plus entendre parler de l''affaire et ne demanderont pas l''indemnité... Je leur ai conseillé de se rapprocher de leur notaire et de revenir vers moi avec une décision claire.
RAPPEL de Mme Staraci : ne poursuivent pas la demande d''indemnité.
15.09 Me Daeschler a bien transmis le protocole mais pas de retour à ce jour. Copie du doc demandé à Me Thone pour relance des clients directement.
10.09 relance faite à Mme Desanti Me Thone
Je vous confirme que le protocole de résiliation modifié a bien été envoyé au notaire des ACQUEREURS en date du 03 septembre.
N’ayant pas de retour je vous invite à contacter ladite étude notarial afin d’en connaître l’avancement.
>> protocole modifié envoyé. A ce jour, pas de retour
01.09 Demande faites au notaire vendeur (tél+mail) de modifier le protocole d''accord. Notaire acq. averti par tél. et Olivier aussi
31.08 réception Protocole d''accord avec renoncement à nos honoraires, vu avec Franck : demander les 7000€
25.08 Olivier relance le notaire et m''envoie le mail d''annulation
- congés Olivier 16 au 23 août -
11.08 Me Thone veut mettre fin à la promesse avec signature de toutes les parties dont Olivier. Je lui ai dit de ne rien signer sans l''accord de Franck. Il nous envoie le document à réception.
10.08 ! Expiration du mandat 12 août 2026
06.08 Affaire annulée car Mme Bouthier a fait une capture de son compte et falsifier le montant pour dire qu''elle avait l''argent, elle a dit que le virement était fait, le notaire a contacté le conseiller bancaire : pas la somme sur le compte. M. Guilloton n''était pas au courant, il a déposé du matériel de valeur (travaille dans le BTP) et a fait des tvx dans le bien.
05.08 mail à Olivier : rdv vente à fixer avant le 28 août : peux-tu voir avec le notaire des acquéreurs s''ils ont transmis les docs nécessaires (renonciation prêt + attestation somme dispo) et les relancer si besoin stp
30.07 le notaire souhaite une attestation des acquéreurs comme quoi ils renoncent à la condition suspensive de prêt+relevé de compte, Olivier voulait les relancer mais ils ne lui répondent pas...
28.07 mail à Olivier pour date de vente à fixer
- congé Olivier 11 au 26 juil. inclus -
09.07 La notaire acq. a posé pb car voulait absolument une ODP du fait de la présence de la condition, ODP sur ancienne maison non achetée mais argent débloqué envoyée, elle demande ensuite une renonciation > envoyée, puis une capture des comptes avec présence de l''argent > envoyé, une attestation d''assurance > envoyée ce jour... Le rdv initial du 17 juillet n''a pas été conservé. La vente ne se fera certainement qu''au retour des vacances de chacun...
06.07 SAFER < 7 juil. Date de RDV dans la semaine
15.06 La SAFER a été envoyée tout de suite après la signature du compromis ce qui porte à mi-juillet. Olivier n''a pas la date exacte.
PRET : les acq. ont déjà la somme sur leur compte.
VENTE se signera sûrement fin juillet.
11.05 PUV ok
On dépend de la SAFER plus que du financement qui est déjà débloqué, c''est de l''achat comptant en fait 
24.04 PUV fixée 7 mai à 14h30, en visio depuis les études respectives des clients.
Le RDV pour le contrôle d''assainissement est prévu lundi, je ferai le nécessaire pour avoir le rapport d''ici là.
21.04 SPANC : Olivier doit les appeler à 15h30 pour prendre rdv
15.04 CI acquéreurs OK et le dossier est envoyé aux notaires.
Par contre j''ai relancé le SGEB, mais le gars qui gère les assainissements indivs est en congés cette semaine...
14.04 OFFRE ok 💰 sans condition
"Elle est un peu poussiéreuse depuis le temps que je la garde, mais voici ci-jointe l''offre d''achat de Mr Guilloton et Mme Bouthier pour le bien de Mr et Mme Staraci à Champagnac le Vieux.
Dossier quasi complet, j''attends le retour du SPANC pour caler un rdv pour le contrôle d''assainissement.
Je mets les CNI acquéreurs sous Hektor."' where app_affaire_id = 15854;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 16.11.2026 cf suivi sur Agenda Delph. PIECES sur Drive Delph. dossier "LITIGES"
27.10.2026 RDV TEL HORDOT :
Fuites toit terrasse p.15 : problème d''étanchéité évoqué au cpmis
DPE D : présence d''une Pompe à chaleur déconnectée p19 "système de chauffage" prise en compte dans le DPE. DPE commandité par la fille de Mme Faurite titulaire d''une habilitation familiale pour représenter sa mère (pas commandé par GTI)
Vérifier que le DPE F ait été réalisé par une entreprise certifiée.
Hugo Labbé a transmis les coordonnées du conseil France rénov'' au client pour qu''ils se renseignent
RPSE HORDOT : il va demander au juge de nous sortir de la procédure car : 
- DPE : GTI ne peut pas être tenu responsable de l''incompétence du diagnostiqueur si toutefois sa responsabilité est reconnue
- INFILTRATIONS : des cuves de récupération ont été découvertes sous le faux-plafond > caché pour les ACQ = caché pour nous.
Il n''a pas encore reçu les pièces adverses.
20.10.2026 Affaire renvoyée au 29 oct.
Me Hordot va demander un nouveau renvoi.
RDV tél avec Me Hordot le 27 oct. 17h.
15.10.2026 Réception d''une assignation à comparaître le 8 octobre 2026, délivrée le 18 août 2026 à GTI Annonay déposée en boite aux lettres et trouvée qu''aujourd''hui par Corinne suite à une levée de courrier.
Erreur sur l''adresse du siège sur l''assignation
Envoi ce jour à Me HORDOT
⚠ 3 avr. 2025 PB après VENTE
M. Policante a appelé Hugo pour qu''il lui fasse une estimation du bien avec un DPE F car d''après lui le DPE D n''est pas bon, il serait en F.  Il veut faire une procédure, mais d''après Hugo pas contre l''agence, s''entend bien.
DPE D fait en 2024 par un diagnostiqueur choisi par la vendeuse.
Hugo avait conseillé à l''acq de se rapprocher d''un conseiller en rénovation qu''il connait et fait des projection de DPE et qui trouvait un DPE F mais il ne serait pas certifié.
Beaucoup de travaux dans le bien, le prix de vente en tenait compte.
Hugo ne fera pas l''estim. je lui ai dit qu''il avait raison.
---- 
Delphine BLANCHARD 2 août 2024
CI V s/bien. CI A à joindre
Delphine BLANCHARD 26 août 2024
Nous venons de fixer la date du 28/08 pour la réitération du dossier ci-dessus.
Caro, peux-tu me faire parvenir la facture de nos honoraires ?
Les avis peuvent être envoyés aux deux parties.
Delphine BLANCHARD 29 août 2024
CI toutes ok
Delphine BLANCHARD' where app_affaire_id = 16787;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 25.11 rdv GUY : relance Stéphanie.
>> Je n''ai toujours pas eu de retour de sa part, et il ne me répond pas non plus suite au message vocal que je lui ai laissé.
10.11 rdv VEND.+GUY+GTI pas fixé, Guy ne lui a pas encore répondu.
03.11 rdv VEND.+GUY+GTI : 
"J''ai deux dates pour Guy : le 9 novembre ou le 11 décembre. J''attends sa confirmation et je te tiens au courant dès que j''ai sa réponse."
27.10 PROMESSE expire le 30OCT2026. Stéphanie informée, elle appelle Me Courtes pour savoir s''il a des infos car Guy ne lui a pas répondu.
>> Me Courtes en vacances toute la semaine. La secrétaire laisse un mess. à Me Crescini pour tenir informée Stéph. Stéph essaie aussi de rappeler Guy.
DECISION : Stéph a réussi à avoir Guy, il souhaite un rdv à l''agence avec les vendeurs pour refaire un point. Il prolongera la PUV
20.10 RPSE de Guy ?
>> "Je viens de lui envoyer un mail à ce sujet. J''attends sa réponse et je reviens vers toi dès que j''en sais plus."
20.10 suite RDV MAIRIE + vendeurs :
"Bonjour Madame Martinez et Monsieur Bourgin,
Comme convenu suite à notre réunion fin juillet, nous avons pris rendez-vous avec le service d’urbanisme de la Mairie d’Annonay pour leur faire part de notre déception et incompréhension par rapport au second refus de permis de construire. Nous leur avons signifié que le temps passait et nous n’avions toujours pas vendu ce terrain qu’ils ont en partie intégré à une OAP sans que nous en soyons averti. De plus nous ne comprenions pas le recours de tiers car ils avaient accepté le second permis de construire puisqu’il était en adéquation avec le nouveau PLU.
Nous avons rencontré Madame Cécile RIBAUD et Madame Claire-Marie GREINER qui nous ont informés qu’à la suite de votre réunion fin juin, vous deviez déposer un nouveau permis de construire en corrigeant les anomalies remarquées suite au recours des tiers soit :
  - Mise en conformité de l’étude des sols pour l’évacuation des eaux pluviales suite à ajout de maisons et modification des voieries
  - Modification de l’implantation de la maison en partie sud du terrain pour satisfaire le voisin
  - Éventuellement prévoir un drainage sur le mur au sud de la propriété
Le refus du permis de construire accordé devait servir à purger tous les recours et contentieux que la mairie avait reçue et elles étaient dans l’attente d’un nouveau permis de construire plus solide afin d’éviter les litiges et pouvoir s’y opposer le cas échéant.
Elles nous ont également dit que les voisins au sud de la propriété avaient intégré le fait que l’OAP induisait la présence de constructions quoi qu’il arrive sur le terrain et que votre projet était de loin bien moins gênant qu’une batterie de logements sociaux.
En bref, ces dames nous ont rassurés sur leur volonté d’aller au bout du projet avec votre entreprise et Madame Ribaud devait vous contacter cette semaine pour connaitre l’avancement du nouveau permis de construire convenu lors de votre dernière réunion.
Nous avons de notre côté le ressenti que la mairie est très favorable à votre projet de construction et si le dossier est mis en conformité administrativement, elle l''acceptera et sera alors en mesure de le faire passer bien plus facilement auprès des riverains.
Nous espérons que vous allez pouvoir poursuivre dans cette voie et que nous allons maintenant tous mener à bien ce projet plus sereinement. Nous vous remercions de bien vouloir nous tenir informé de l’avancement des étapes que vous avez convenu avec la Mairie.
Bien cordialement,
Christian et Serge Jay
13.10 point rdv Mairie + Voisin ? Stéphanie se renseigne auprès de Guy
11.08 La mairie doit organiser une réunion avec les voisins début sept. Guy est prêt à modifier son projet mais risque d''être refusé le PLUi a changé, il faudrait que la mairie force l''accord.
- congés 03 au 09 juillet -
- congés 20 au 26 juillet -
08.07 Steph. en rdv, me rappelle. RDV 27 juillet avec proprio + Bourgin à l''agence.
23.06 Steph a laissé un mess à Guy mais n''a pas encore de retour
11.06 réception let. mairie pour retrait de permis
09.06 recours contentieux au Tribunal Administratif GOUDARD pj.
12.05 Plusieurs recours de voisins ont été adressés en mairie.
Affichage 6 mai > 6 juillet pour derniers recours > 6 septembre pour réponse mairie > 6 novembre pour saisie du Tribunal Admin.
06.05 PC affiché
15.04 PC accordé le 14.04.2026 pj. Attente recours 3mois > 14/7
25.03 PC : promotion@appart-patrimoine.fr "Des pièces complémentaires ont été déposées en février.
Nous sommes toujours dans l’attente de l’accord."
24.03 accord PC demandé à Stéphanie
-----------------------------------2025
22.12 nv PC déposé le 18déc., instruction 3mois > 18mars
07.10 esquisse de nv projet 9 maisons déposé en mairie, en attente de rdv mairie
30.7.2025 Demande à Stéphanie si nouvelle promesse ou prorogation ?
Prorogation promesse. Accord pj.
Nouveaux délais : durée de validité de la promesse de vente jusqu’au 30 octobre 2026 avec une date de dépôt de permis de construire au 31 décembre 2025, et une date d’obtention de permis de construire au 30 juin 2026.
11.7 eu Stéphanie, Guy Bourgin est obligé de tout recommencer à 0 (plan, permis de construire...) suite aux nouvelles prescriptions du PLUI
04.7 Stéphanie : "Juste pour te dire que j’ai rendez-vous mercredi à 17h avec Guy pour le dossier JAY concernant les maisons pour Annonay
24.6 Guy voit avec son avocat mais à priori il redéposera un permis. Il doit revoir tout le projet.
20.6 PC refusé pj. En attente décision G.Bourgin.
10.6 Guy a transmis à son avocat qui fera lui-même la réponse à la mairie en demandant l''acceptation du projet tel que déposé.
06.6 réception mail de l''agglo résumant les modifs à apporter au projet. Guy y réfléchit.
03.6 Stéphanie a assisté à la réunion : la mairie demande de se conformer aux nouvelles prescriptions du PLUI suite OAP sur la parcelle AY-132. Demande la construction de 17 maisons à distance de 6m chacune, nouveau plan avant 10j, fin d''instruction. 
Guy a appelé son avocat qui lui a dit qu''un recours administratif est possible car il n''y a pas eu de sursis à statuer dans le 1er mois du pc,  mais n''empêchera pas la mairie de refuser le PA.
La mairie doit envoyer un mail avec les prescription à Guy pour qu''il étudie une solution.
27.5 mail de la mairie > Guy Bourgin
Dans le cadre de votre projet PC 007 010 24 A0036 sur Annonay relatif à la construction de neuf maisons, nous aimerions vous proposer un temps d''échange entre nos services, le SCOT des Rives du Rhône et vous même le mardi 3 juin à 14h.
En effet, la règlementation applicable aux autorisations d''urbanisme sur l''Agglomération a évolué récemment et nous souhaiterions pouvoir aborder avec vous plusieurs sujets qui présentent des difficultés avant la fin du délai d''instruction de votre autorisation.
21.5 tél à Stéphanie, elle a eu Guy Bourgin, le permis ne devrait plus tarder.

-----------------------------------------------------
21/5/2024
relance Stéphanie CI 4 vendeurs
+ rdv cpmis fixé ?
>>congés Stéphanie retour 27/5
Delphine BLANCHARD
Delphine BLANCHARD
27 mai 2024
Rdv sous peu. CI relancé Stéphanie
Delphine BLANCHARD
Delphine BLANCHARD
6 juin 2024
relance Stéphanie CI+rdv cpmis
Delphine BLANCHARD
Delphine BLANCHARD
12 juin 2024
Cpmis en juillet retard suite négo versement dépôt DG rdv 05/7 à conf.
Delphine BLANCHARD
Delphine BLANCHARD
18 juin 2024
cpmis confirmé 05/7-17h
Delphine BLANCHARD
Delphine BLANCHARD
8 juil. 2024
rappel Stéph CNI 4V
cdt PC 10 maisons jumelée en 2 blocs + démolition existant.
Delphine BLANCHARD
Delphine BLANCHARD
25 sept. 2024
rappel Steph CI manque 3V
Christian Jay ok
Delphine BLANCHARD
Delphine BLANCHARD
15 oct. 2024
DPE-E risque d''être soumis à l''audit energetique mais Bourgin veut détruire le bâti pour construire, peut-être peut-il dispenser le vendeur ?
Delphine BLANCHARD
Delphine BLANCHARD
14:20 27 nov.
Steph a vu l''archi. dépôt de permis en cours, ne devrait plus tarder. Stéph récupèrera le récépissé.
Relance CNI manque celles de Max, Serge et Philippe Jay
Delphine BLANCHARD
Delphine BLANCHARD
08:50 29 nov.
PC déposé le 27/11/24 pj
Instruction 3mois > 27/02/25
Delphine BLANCHARD
Delphine BLANCHARD
17:27 18 févr.
Eu Stéph au tél. Elle fait le point avec Guy pour le PC
Rappel manque CI-3V
Delphine BLANCHARD
Delphine BLANCHARD
15:25 4 mars
relance Stéph idem
Delphine BLANCHARD
Delphine BLANCHARD
09:57 11 mars
Eu Stéph au tél. : étude de sol réalisée le 25/02
Elle le rappelle à 12h pour savoir si pc accordé ou si retard
Delphine BLANCHARD
Delphine BLANCHARD
13:59 13 mars
Stéph a eu Guy au tél : 
PC retardé car études complémentaires demandées en cours d''execution.' where app_affaire_id = 16792;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 Les venderesses sont disponibles mais elles ne se déplaceront pas pour le rendez-vous
Le notaire de l’acquéreur vient de reprendre contact avec moi, le rendez-vous est finalement décalé au 21 décembre prochain à 14 heures (en visio).
J’informerai Mesdames VAGANAY-MARION ainsi que le liquidateur de cette modification.
19.11 mess laissé aux Mmes Marion pour excuser GTI
Mail à Mme Couland pour excuser GTI et savoir si le rdv a été confirmé par les parties ?
17.11 VENTE jeudi 3 décembre 2026 à 9h 30 (vu avec Franck excuser l''absence de GTI)
"Je vous informe que Madame DEINEZ souhaite renoncer aux conditions suspensives (d’obtention de permis de construire et d’emprunt) prévues dans la promesse d’achat de votre terrain situé à TENCE, Les Mazeaux.
Je vous propose donc un rendez-vous de signature de l’acte de vente le jeudi 3 décembre 2026 à 9h 30 en l’Office Notarial de TENCE (sous réserve du retour de l’ensemble des documents nécessaire à la signature de l’acte notamment ceux relatifs à la liquidation judiciaire)"
12.11 PC récépissé de dépôt demandé à Mme Deinez
31.08 AVNT ok pj.
- congés Sylvie 17 au 30 août -
06.08 Sylvie relance le notaire manque AVNT signé de Mme Marion
10.07 AVNT signé Mme Deinez pj en attente signature Mme Marion
Report DB de avril à juin 2027 
dépôt PC 12 nov.2026 
accord PC + ODP 26 février 2027
30.06 accord juge pj.
Pour information, Madame DEINEZ souhaite régulariser un avenant afin de proroger tous les délais de 2 mois.
02.06 PUA ok
p3 liquidation de Mme Marion mais prix de vente très haut dessus de la dette donc pas de soucis pour l''accord + paiement hono.
p8. autorisation de la vente avant le 31 juillet 2026
p9 dépôt PC 30 sept. PC 30 janv.27
01.06 relance Sylvie
29.05 tél à Sylvie PUA bien signée, Sylvie relance
28.05 copie PUA demandée à Sylvie
29.04 PUA pas signée, lecture de l''acte ok mais signature que sous 1mois. Raison demandée à Sylvie : l''acq veut attendre d''avoir un chiffrage plus précis de ses travaux
15.04 Mme Marion est en liquidation, il faut donc l''accord du juge. Ce sera une PUA
08.04 PUA 29 avril
01.04 OFFRE ok
CI-A demandée à Sylvie
! MANDAT expire le 20 avril 2026' where app_affaire_id = 19409;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 17.11 ODP tél à M. Fuzier : il a passé les 10 jours ODP transmis à son notaire directemnt, mais il a demandé un avenant pour prolonger la promesse pour une signature en janvier 
04.11 ODP redemandée à M. Fuzier (mail)
30.10 ODP+VENTE : tél à Dumas : Caroline la clerc a bien eu mon mail et me répondra dès que possible...
27.10 ODP+VENTE : mail à Me Dumas pour savoir si ODP ok et me prévenir dès qu''un rdv sera fixé ?
15.10 ODP : tél à M. FUZIER l''aurait reçue, il me la transmet d''ici semaine prochaine, il souhaite la faire viser par son notaire avant. Sylvie lui a transmis mon adresse mail.
30.09 PAS besoin de présence à la vente d''après Sylvie.
- congés Sylvie 17 au 30 août -
13.08 accord PC reçu par les clients et le notaire.
07.08 AVNT signé pj. report délais ODP
06.08 conseiller bancaire en vacances, ODP pas avant septembre.
05.08 sylvie relance M. FUZIER pour ODP et notaire pour copie AVNT suite report accord défrichement 12 août (tacite) déjà signé par les parties
28.07 eu Sylvie, va contacter les acquéreurs pour connaitre l''avancement dans leur démarche de prêt 
23.07 mail à Sylvie pour savoir si elle a eu des nouvelles des acq. concernant leur prêt
15.07 Sylvie se charge d''appeler Mr Fuzier
13.07 rappel délai ODP à Sylvie et demande de point financement
02.07 récépissé PC redemandé à Sylvie ok
>> pj. mail de la mairie instruction PC 2 mois à compter du 15juin > 15 août
24.06 CI-1A + récépissé PC : relance Sylvie
CI-A ok
17.06 DEFRICHEMENT récépissé dépôt demande défrichement 15 mai. Dossier complet accord 03 août max sinon tacite.
PC déposé : Sylvie demande le récépissé
CI-Mme Fuzier : Sylvie relance
15.06 relance Sylvie : accord défrichement + CI-A
02.06 dossier incomplet à la DREAL, Sylvie appelle la personne qui a fait le dépôt (ami de M. Fuzier de la chambre d''agriculture). Elle informe M. Fuzier et lui redemande la CNI de Françoise
26.05 CI Pierre-Dominique ok. Manque Françoise Fuzier
15.05 CI-A Sylvie les demande
12.05 CPMIS ok
p7 autorisation de défricher < 15 juin
p7 dépôt PC < 30 juin 20 gges + 4 box containers accord PC < 31 août
CI-A demandés à Sylvie
11.05 copie : relance Sylvie
06.05 copie tjrs en attente Sylvie relance
29.04 copie CPMIS relance Sylvie
24.04 DAATC reçue auj. par la mairie. Faute de frappe surface s/cpmis, M. Mounier a vu avec Rocher, il modifie signe et renvoie.
22.04 M. Mounier aurait envoyé la Daatc, la mairie ne l''avait pas reçue hier. PUV pas encore reçue non plus
15.04 M. Mounier doit signer la promesse par courrier. M. Fuzier l''a bien signée hier. M. Mounier doit déposer la Daatc avant le 24 avril sinon passera inconstructible.
Délai 35j. pour réponse DREAL après signature PUV.
01.04 M. Fuzier a reçu un retour de la mairie suite au dépôt de permis, il doit construire à 5m de chaque côté car chemins communaux. Il va essayer de demander une dérogation.
M. Fuzier faire son affaire du dessouchage
Bornage fait.
FIN AVRIL le terrain ne sera plus constructible.
18.03 congés Sylvie > Retour 30 mars
19.02 mess tél à Sylvie pour savoir si elle a réussi à joindre M. Mounier
>> OUI mais il n''a même pas fait faire un devis. Sylvie l''a averti que le terrain n''allait plus être constructible en AVRIL.
11.02 Sylvie n''arrive pas à joindre M. Mounier pour le désouchage. Cependant ce dernier a demandé au géomètre de prendre rdv avec Sylvie pour le bornage. Sylvie avertie qu''elle ne peut pas signer au nom du propriétaire.
Elle relance M. Mounier.
02.02 M. Mounier a signé le cpmis
M. Fuzier veut faire des modifs sur le cpmis
Il manque la déclaration à la DREAL pour déboisement
Et engagement du vendeur sur l''enlèvement des souches sur la totalité de la parcelle, veut le faire que sur l''emplacement de la maison
28.01 Sylvie a relancé Benjamin
21.01 Projet envoyé au vendeur. Le vendeur a fait des devis pour broyer les souches : trop cher, il veut le faire juste à l''emplacement des maisons. Sylvie lui a dit que non, qu''il devait le faire sur la parcelle entière. Me Rocher se rapproche du vendeur pour lui expliquer car Sylvie n''a pas obtenu son accord.
19.01 OFFRE ok pj
"offre contresignée. Le compromis tournant est en route."
14.01 Sylvie n''a pas encore reçu l''offre signée
10.01 AR Mounier OFFRE ce jour. 
09.01 Dossier envoyé à Me Rocher
06.01 OFFRE en attente signature vendeur prix mandat
Envoi LRAR à Monaco ce jour.' where app_affaire_id = 19415;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 24.11.2026 PB après vente : les acq ne reproche plus que l''assainissement mais des vices cachés, notamment d''humidité, moisissures et demandent l''annulation de la vente. Nadège ne sait pas exactement où ils en sont de la procédure. Un expert, payé par acq. et vend. pour moitié chacun, est passé et a indiqué que les vendeurs ne pouvaient pas ignorer les vices. L''avocat des vendeurs est pessimiste suite au passage de l''expert 40K de travaux si vente pas annulée. Ils demandent à Nadège une attestation qui indiquerait qu''au moment des visites la maison était propre et saine, sans aucune odeur d''humidité. > FRANCK ne veut pas que l''on intervienne pour l''une ou l''autre partie tant que l''agence n''est pas sollicité par un juge.

16.01.2026 PB après vente : les acq demandent 10K aux vendeurs (amis de Nadège) car présence d''une fosse septique non indiquée au compromis : devis mise en conformité + indemnité suite dégradations débordement de la fosse et frais d''huissier.
Ils étaient prêts à payer la moitié de la mise en conformité mais les acq n''ont pas attendu pour leur envoyer la LRAR.
>> j''ai dit à Nadège qu''ils se rapproche d''un avocat car sur le CPMIS
les vendeurs ont déclaré qu''ils ne garantissaient pas la conformité de l''assainissement et ont fait appel à une entreprise pour faire les tvx de raccordement.
Sinon ils faut qu''ils négocient le montant avec les acquéreurs.

24.07.2025 Vente signée
01.07.2025 Vente fixée le 24 juillet 16h chez Maître Simonet.
26.6 relance @Nadège ODP+rdv Vente ?
>>rpse "Offre de prêt reçu hier ils doivent la retourner à partir du 11 juillet. Nous sommes en attente de Maître ROCHE pour fixer une date.
20.6 Edition ODP auj normalement
19.6 mess T/Nadege
CI ok
02.6 Toujours en attente de l''ODP
23.5 ODP autour du 17/6 - DP ok
14/5 ADP vousfinancer reçue. 
Relance Nadège pour CI et dépôt DP ou non opp. régul. panneaux
CI MANQUANTES :
Giry Courbon Frédérique
verso Giry Ludovic
verso Sagnol Julien
----------------------------
Delphine BLANCHARD
14:29 13 mars
MDR sans durée : Eu Franck, valider quand même. Nadège prévenu, attention prochains.
Mme M. GIRY achète un bien en direct, signature en cascade chez Simonet.
CI : Nadège les a demandées
BV x : ne fait pas signer sur ce logiciel, je lui ai dit de bien faire signer les prochains car pas plus compliqué que sur sphère
Afficher moins
Delphine BLANCHARD
Delphine BLANCHARD
14:06 17 mars
PUV 7 Avril à 17h
Delphine BLANCHARD
Delphine BLANCHARD
14:11 17 mars
manque
CI Giry Ludovic verso
CI Courbon Frédérique
CI Poveda
CI Sagnol
Delphine BLANCHARD
Delphine BLANCHARD
15:16 8 avr.
manque toujours
CI verso Giry Ludovic
CI Giry Courbon Fredérique
CI Poveda Virginie
CI verso  Sagnol Julien
Delphine BLANCHARD
Delphine BLANCHARD
15:17 8 avr.
PUV ok
p13 236K€ 25a 3.3%
p28 DP+non opp. (V) régul panneaux photovoltaïques
Delphine BLANCHARD
Delphine BLANCHARD
16:34 7 mai
relance Nadège
- CI tjrs manquantes :
Giry Courbon Frédérique
verso Giry Ludovic
verso Sagnol Julien
- ADP
- dépôt DP régul panneaux' where app_affaire_id = 19634;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 FOURNIER a demandé les coordonnées de l''acq. à Nico pour le bornage > transmis ce jour.
19.11 VENTE 03 décembre à confirmer car le notaire attend le PV de bornage de M. Fournier, géomètre pour une borne manquante en haut à droite de la parcelle. Nico l''a déjà relancé à plusieurs reprises. Christiane Salichon ne l''a tjrs pas signé (très particulière, ne veut plus rien signer, s''oppose à ses co-indivisaires systématiquement)
18.11 VENTE rdv demandé à Nico mess. tél.
03.11 AVNT DB30/10 > 11/12 signé Christiane pj. Nico a eu conf. que les autres vendeurs ont également signé mais n''aura pas le doc (rétention notaire Layet)
SAFER : Nico relance la SAFER, M. Pépin ne sait pas non plus à quelle date elle a été envoyée par Me Layet. Il a demandé à Me Layet de fixer le RDV de VENTE.
PRET : M. Grange achète que le terrain sans prêt finalement.
27.10 copie AVNT + date notif. SAFER ?
06.10 RDV VENTE : relance Nico
>> "Les parties voulaient signer en octobre. Le notaire a fait une demande à la Safer…. Mais au nom propre de l’acquéreur et vendredi à force de les harceler pr avoir une date de vente… Ils ont regardé le dossier … promesse date de 12 mois , et réalisé que pr ce terrain il faut demander à la Safer et cette fois au nom de la SCI.
Donc signature d’un avenant demandé."
28.09 RDV VENTE : M. Grange ok pour signer en octobre, Nico a demandé un RDV aux notaires
25.09 RDV VENTE : Nico relance M. Grange pour fixer un rdv avant le 30 oct. Il n''a pas encore le retour du CM mais aurait des clients pour racheter le terrain s''il n''est pas vendu à M. Grange
04.09 ordre du jour CM accord cession ? oui CM le 24 sept.
03.08 Nico a eu le maire il y a 15 jours, il aurait reçu l''estimation des Domaines. Pour l''instant pas à l''ordre du jour du prochain conseil.
L''acq ne peut pas déposer son prêt sans cet accord.
- congé Nico 27 au 2 août -
16.06 AVNT signé Grange ok pj. + p2 signé Christiane pj.
Eu M. Pépin directement : il n''a pas l''avenant Salichon signé de tous, il a celui signé de M. Grange (en pj.) et Mme Christiane Salichon ne lui a renvoyé que la dernière page en mauvaise qualité, il n''aura pas mieux...
10.06 relance Nico
Avenant reçu en partie (p2) avec report ODP 27 juillet. et signé de Mme Salichon et M. Grange, manque délai DB
Nico a demandé le doc entier.
08.06 Je vais relancer Maître Berinchy en appelant l’étude, jeudi il m’a dit qu’il le ferait. Et par la même occasion : voir pour l’avenant Salichon / Grange.
30.05 AVNT demandé à Nico
>> Ci-joint le retour du notaire pour l''avenant auprès de Mme Salichon, date au 24 juillet. Elle devra être prolongée a priori.
J''ai relancé par email les deux notaires, mon premier mail date du 27 avril... pour avoir l''avenant signé.
J''ai échangé avec le maire de ST Didier, il a fait la demande d''évaluation aux domaines, le retour doit être fait en juin. Le maire me l''a confirmé. Ensuite, il fera un écrit certifiant que la mairie vendra le terrain afin de débloquer, je l''espère le financement et ne pas attendre un an avant que la vente se fasse.
J''ai compris le frein et la lenteur de la mairie ....  Monsieur Grange a peut-être en location à venir dans son bâtiment jouxtant au terrain sous promesse des kinés. La mairie a déjà installé des kinés sur la commune et leur loue un local... Ils ont entendu parler du projet.... Le maire n''est pas favorable à ce qu''il y ait plus de kinés... Bien compliqué pour un talus...
Donc Monsieur Grange va gérer ce point directement avec le maire.
21.05 NICO J’ai échangé avec M Grange .
Le maire lui a confirmé verbalement qu’il n’y a aucune possibilité pr que ce ne soit pas accepté mais niveau délai… il avait parlé de début juin. 
Le maire avant l’élection lui avait promis de s’en occuper rapidement.
Je vais le relancer directement en accord avec M Grange car ils vont aussi le faire évaluer avant de pouvoir mettre un prix.
19.05 AVNT + ODP : relance Nico
23.04 accord PC du 01avril2026 pj.
21.04 AVNT + accord PC : relance Nico
17.04 AVNT + récépissé PC redemandés à Nico
>"M Grange a obtenu son permis de construire, déjà relancé la semaine dernière pr avoir la copie, Je vais le relancer. "
Nico relance aussi l''AVNT
30.03 M. GRANGE a demandé un avenant, Nicolas récupère le doc signé. La mairie va céder le talus, ce qui a été confirmé à Nicolas par le maire. Il a déposé sa demande de PC.
02.02 n''a pas encore la validation de la mairie pour le talus, le maire ne veut pas donner son accord avant les élections.
N''a pas forcément besoin du PC car ne sait pas encore quoi en faire.
14.01 dPC : relance Nico
>> un peu de retard ds le dépôt sera fait d''ici fin janvier.
06.01 dPC : récépissé demandé à Nico
16.12 dPC : M. Grange devrait déposer le pc d''ici fin déc. il est propriétaire de la maison en dessous et achète pour construire (électricien) et revendre ou louer mais il souhaite acq en parallèle un talus qui sépare sa parcelle de celle achetée et qui appartient à la mairie.
03.11 PUV ok
27.10 PUV doit se signer ce vendredi 31/10 à 11h. Elle avait été reportée la semaine dernière après 1h30 … 
22.10 mail à Nico pour copie cpmis
RPSE : Le deuxième compromis n''a pas eu lieu. J''allais t''envoyer un message mais il me manque tjs la date du report... car reporté....
Je me suis pressé pour faire Tence / St Etienne chez Maître Gevrinchy.... Rdv à 17H30. On a attendu Maître Layet, le notaire des vendeurs, avec Maître Gevrinchy + l''acquéreur jusqu''à 19H15... et Mme Salichon sur place.... Finalement trop de tard... et reporté... Au top !
6.10 PUV 20oct rdv confirmé
30.9 CI ok. PUV le 20oct. à confirmer
24.9 CI tjrs manquante. Dossier envoyé aux notaires mais pas encore de rdv
19.9 CI M. Grange demandée à Nico' where app_affaire_id = 23881;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 18.1 VENTE  8 décembre à 18H.
13.11 ODP ok pj. Transmise à Me Sauret par Nico pour rdv VENTE.
Antoine : "Comme convenu au téléphone, voici en PJ l’offre de prêt concernant l’achat de Mme Da Silva et Mr Croze.
Ils pourront la signer à partir du 24 novembre. Tous les feux sont donc aux verts pour une signature à partir du vendredi 27 novembre."
12.11 ODP tjrs en attente, pas d''AVNT pour l''instant. Nico attend d''être sûr de la réponse du CE avant de demander un AVNT. Le CE demandait un rapatriement des comptes que Mme Da Silva a refusé, donc à suivre
04.11 ODP : Nico a eu Antoine, la demande vient juste d''être signée à la CE, la banque suivrait.
29.10 Congés Nico retour semaine pro
28.10 ODP : relance Antoine
22.10 ODP : CE Antoine n''a tjrs pas de réponse. Nico a averti les vendeurs.
15.10 ODP : Nico n''a pas eu de nouvelle. Il relance Antoine et me tient informée
28.09 ODP rpse Antoine : "le Crédit Agricole ne veut pas accorder le PTZ à cause d’un problème d’adressage sur les avis d’impôt de Mme.
J’ai envoyé le projet à la Caisse d’Epargne qui est en train de faire la demande de financement. Je fais au mieux pour aller au plus vite."
24.09 ODP : demande à Hortense de faire le point avec Antoine
17.09 AVNT pj. REPORT DB du 2sept. au 2 nov.
Doc envoyé à Antoine avec point prêt
16.09 copie AVNT demandé à Nico et Hortense
11.09 Demande à Nico si acq bien présent ce mardi pour signer ? OUI confirmé par Hortense
ODP PTZ ? point demandé à Hortense : D''après Antoine 
>> il manque encore l’attestation de propriété des parents pour finaliser le PTZ. Il pense que celui-ci devrait être validé d’ici la fin de semaine prochaine. Les offres de prêt pourront ensuite être éditées.
04.09 Nico a eu Sophie qui convoque le reste de l''indivision pour le 15.
Antoine doit représenter tout le dossier car la conseillère est partie et le dossier a été repris par la Directrice d''agence.
03.09 AVENANT Mardi 15 septembre 2026 à 18H00, au bureau annexe de CUNLHAT, 2 rue de Bellevue.
28.08 mail au notaire : "Madame,
Je fais suite à mon mail de ce matin, j''ai eu entre-temps la réponse du courtier concernant le prêt (ci-dessous). Il semblerait qu''un avenant à la promesse soit nécessaire afin de laisser le temps aux acquéreurs de recevoir les offres de prêt. 
J''ai prévenu par téléphone l''ensemble des vendeurs de ce retard. 
Je me permets de vous laisser le soin de joindre les parties pour la signature de l''avenant.
Pour information, M. Moulin Gérard part demain en vacances et ne sera de retour que le 8 septembre. Il est cependant joignable sur le portable de son épouse 0687548814
Bien à vous,
28.08 ODP demandée à Antoine : bcp d''irrégularités pour le PTZ (pas fait de changement d''adresse). Il attend de recevoir la certification auj. puis édition puis 18 jours pour déblocage de fonds.
06.08 PTZ en cours de modif.
05.08 J''ai eu un retour du notaire concernant la vente Moulin / Croze. Le délai de la SAFER prend fin le 10 août prochain. En revanche Mme Gacon, la collaboratrice du notaire en charge de ce dossier, est actuellement en congés et l''étude est fermée jusqu''au 24 août. Il nous a donc été demandé de reprendre contact avec elle à compter du 25 août à 9h afin de faire le point sur la suite de la vente. 
Par ailleurs, j''attends également le retour d''Antoine, le courtier, concernant l''offre de prêt de M. et Mme Croze. Dès que j''aurais sa réponse, je reviendrai vers vous afin de vous tenir informée. 
- congés Sauret 15 au 30 août. Arrêt Céline à compter du 7 juillet -
03.08 mail à Nico pour ODP + rdv VENTE
18.06 SAFER à purger d''ici début août. Prêt déposé avec Antoine hier. Acq aimeraient signer au plus tôt
03.06 PUV ok
13.05 PUV 02 juin 18h : les vendeurs ne voulaient pas payer des procs et ne s''entendent pas. L''une d''entre eux doit accoucher par césarienne le 6 juin. On espère que le rdv sera maintenu.
06.05 rdv CPMIS demandé à Céline
30.04 actu diags reçu ce matin envoyé à Me Sauret pour rdv mi mai
22.04 OFFRE du 10janv. reçue auj. pas de date de contresignature, j''ai mis le 22 avril.
Céline : " le dossier est parti aujourd''hui chez Sauret. J''ai dû attendre car mes clients avaient un problème avec leur avis d''imposition qui vient d''être réglé" : Les acq. n''avaient jamais déclarer leurs revenus donc n''avaient pas d''avis d''impôt à fournir pour le prêt. Situation régularisée.
CI ok
SIMUL Vousfinancer du 21.04.2026 pj.
CONTACTS : Gérard (n° de son épouse), Bernard (fixe à env. 9h), Sophie prévient son frère (Fréderic) et sa mère (Anita)' where app_affaire_id = 27285;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] CLE en agence CONTACT (V) Mme Tholy 0760231296 (A) M. Nicole (pasteur) 06.52.77.32.84
17.11 la clerc Mme Lhermet demande à L. Rocher de me rappeler
17.11 Mme Tholy n''a aucune nouvelle, elle a eu confirmation que la demande a bien été transmise au Ministère mais à ce jour, n''a reçu aucune réponse.
10.11 mess. tél à Mme Tholy pour faire un point
09.10 M. Nicole (pasteur) 06.52.77.32.84 n''a pas de contact avec M. Haffner mais essaie de prendre des infos auprès de Sœur Violaine, je lui ai également soumis l''idée que la fondation redépose une demande en dissociant la maison. Il me dit que même si la maison a peu de valeur, il s''agit de l''obligation de maintien du patrimoine et que suite à une expropriation par la SNCF, la fondation a déjà perdu en patrimoine et doit procéder à des achats et non pas des ventes.
08.10 Eu Mme Tholy : elle n''a pas de nouvelle, c''est directement le DGA Michel Haffner qui aurait fait la demande au Ministère. Elle pense que la demande a été faite dans un lot de plusieurs biens de plus grande importance et que le Ministère ne donne pas son accord de ce fait.
Il s''agit de biens en garantie de la dotation initiale de 1.5M€. Je lui ai proposé de demander s''il était possible de dissocier la maison vendue du reste de la demande. Elle se renseigne.
Me conseille de faire intervenir directement M. Nicole qui est pasteur auprès de M. Haffner et/ou de Soeur Violaine qu''il aurait en contact.
17.09 AR le 16 sept. pj.
14.09 LRAR 1A21787374887
11.09 Personne n''a de nouvelle. J''envoie une LRAR à la fondation
04.09 accord ministère : mail à Sylvie pour qu''elle relance Me Rocher
05.08 Sylvie n''a tjrs pas de nouvelle
22.07 Sylvie "message vocal à Mme Tholy pour savoir si elle avait eu des nouvelles"
08.07 toujours en attente de l''autorisation du Ministère
24.06 La Soeur est montée à Versailles, à priori pas de soucis sur la vente mais ce serait juste un pb administratif.
17.06 Sylvie a relancé L. Rocher mais il n''a aucune nouvelle de l''avancement.
22.05 courrier fait par l''acq. à la fondation pour faire bouger
21.05 
- demander le n° de la personne qui a fait la demande d''autorisation au ministère et qui est en charge du dossier.
- savoir si elle a un accusé de réception de la demande et le date
- savoir si le ministère a demandé un complément de dossier
délai moyen si dossier complet : 2-4 mois jusqu''à 9 mois si incomplet
- Me Rocher aurait pu signer un compromis ou une promesse en mettant en condition suspensive l''autorisation.
👉 En droit, une promesse de vente peut exister avec une condition suspensive d’autorisation administrative.
C’est même une pratique courante dans les dossiers :
- collectivités,
- établissements publics,
- Fondation Reconnue d''Utilité Publique > notre cas.
20.05 Sylvie a appelé 2x cette semaine et la semaine dernière mais la clerc ne la prends pas au tél. Elle ne doit pas avoir de réponse. A priori pas de signature de la PUA tant que le ministère n''aura pas validé la vente...
06.05 Sylvie n''a pas réussi à joindre la clerc. Elle relance
29.04 relance Sylvie
20.04 Sylvie a demandé à Lucas un rdv PUA, elle le relance auj.
15.04 La préf. n''a pas reçu de demande. Lucas s''en occupe. La demande a été faite au ministère de l''intérieur en février.
03.04 Mme Tholy toujours en attente de l''accord de la préf.
Mme M. Nicole ne font plus de prêt car ils ont signé un cpmis sur leur maison.
01.04 Sylvie relance Mme Tholy (contact fondation) suite CA du 27mars
18.03 congés Sylvie > Retour 30 mars
19.02 CA : relance  Sylvie mess tél
>> Sylvie a relancé mais n''a pas réussi à avoir le notaire, ni son contact.
11.02 CA : Sylvie n''a pas relancé, elle s''en occupe.
02.02 CA : Sylvie n''a pas encore le retour, elle relance
28.01 L.Rocher signera une PUA à l''issue du CA.
23.01 Sylvie a eu la juriste qui a la gestion du dossier pour la Fondation.
Elle a activé les choses auprès du DG. L''offre d''achat sera validée le 29 janvier lors du CA. Ensuite il faudra l''accord de la préfecture pour sortir le bien de la dotation et pouvoir vendre (délai 3/4 mois). Je lui ai dit de proposer la signature d''une PUA avec cette condition après le PV du CA 29janv. acceptant l''offre.
La juriste lui a dit que s''il n''était pas possible de vendre, Sylvie devait lui envoyer la facture et elle la lui règlerait.
21.01 PUV proc envoyée DG ?
>> En attente d''un conseil d''administration pour autoriser la vente (Mars) et du complément du titre de propriété.
CI ok
12.01 OFFRE en attente signature du DG de la fondation, la prieure générale (à Versaille) et la sœur (à Tence) qui s''occupe du dossier ont donné leur accord verbal mais le DG n''a tjrs pas signé. Sylvie a envoyé le dossier à Lucas Rocher qui prépare le projet de la PUV, il fera signer directement la PUV.
HONO. divisés par 2 car acq. trouvé par le vend.
CI-A demandées à Sylvie' where app_affaire_id = 28569;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 VENTE 1er décembre à 17h. Date confirmée seulement ce matin.
19.11 VENTE reportée au 01 décembre à confirmer par le notaire.
Cause : SCI soumise à la loi Scrivener, fonds pas dispos pour le 20 nov.
13.11 VENTE 20 novembre 10h
03.11 ODP : Le prêt est parti à l''édition (soeur de Nico tvlle au siège) mais il manquerait encore un doc que la conseillère CA n''a pas demandé...
29.10 ODP + DP : "Ci-joint l''arrêté de non opposition de ce jour, pour le changement de destination des bureaux en habitation;
A priori, c''était ce dernier document qui bloquait l''édition de l''offre de prêt. 
Normalement : retour en début de semaine. Vendeur informé.
27.10 ODP ? Non, j''ai relancé directement la banque hier et ce matin. Ils doivent répondre rapidement.
Leur conseillère était partie en congés la semaine dernière en connaissant la date butoir...
Et hier, elle demande une simulation de la retraite de Madame...Heureusement, elle en avait une.
Dès que le retour est obtenu, je te le communique.
20.10 ODP pas encore reçue
13.10 rectif de Nico : DP non encore obtenue contrairement à ce que l''acq. lui avait dit.
Le délai d''instruction a été porté à 2MOIS (ABF abbaye) se termine le 14 novembre. Courrier mairie en pj.
06.10 accord DP + départ locataires + vente Maman (pour valider le prêt car achat en SCI) ? >> ADP CA sci La Semène ok le 03 oct 2026
"Ci-joint l’attestation de la demande de financement. Ils devraient être dans les temps pr fin octobre.
Les locaux sont libres (ils étaient loués à des sociétés du vendeur)
La maman a bien vendu son appartement fin septembre. Elle a déménagé tous ses meubles à la Seauve chez un client Jourda qui loue des espaces. Donc c’est en bonne voie. Long …"
"Pour la DP obtenu, c’est ok. J’ai demandé plusieurs"
fois, je vais relancé.  
10.09 Nico n''a pas encore le récépissé de la DP. Il relance
 Mère et fils dans la sci. Dépôt prêt auj. en banque.
04.09 dépôt DP + création SCI ? SCI créée mais prêt pas encore déposé. DP serait déposée, Nico demande le récépissé. Vente acq. apt. 25 sept. pas en condition.
- congés Nico 24 au 31 août -
21.08 ADP + dépôt DP demandées à Nico
>> "Je les ai rencontré la semaine dernière pour revisiter avec les grands parents et relancé. Achat réalisé par la maman et le fils, il crée une SCI. Point soulevé lors de la promesse.
Création en cours, réalisée par leur notaire. La maman a vendu (sous compromis) son appartement ds l''Hérault pour le financement du projet, la vente se fait fin septembre."
23.07 PROMESSE ok  
Mémo délais :
- dépôt demande de prêt < 21 août
- dépôt DP tvx changement de destination local en hab. < 01 sept.
- la libération des lieux par les locataires actuels et départ effectif <30 sept. (p17)
- obtention DP tvx < 01 oct.
- obtention offre de prêt < 21 oct.
- signature vente < 20 nov. 2026
01.07 relance Nico rdv PUV
21 juillet à 16h pr le compromis.
24.06 Nico :"Concernant le dossier Sci Les Adreyts / Charrel, le compromis va bien se faire. Le notaire doit nous faire le retour de proposition de dates. Long mais çà avance un peu. "
16.06 Eu Nico : le vendeur souhaite attendre que les acq trouvent une solution de financement, ne souhaite pas remettre en vente tt de suite.
Nico a eu les acq, Coraline aurait trouvé une solution, il l''appelle pour avoir confirmation
03.06 relance Nico
>> Ils ont eu plusieurs refus. Cette semaine, ils devraient avoir d''autres retours avec un délai plus long.
Le vendeur est informé des difficultés de financement.
Je te fais un retour rapidement soit pour confirmer une date de promesse de vente soit le retrait de l''offre.
20.05 retour banques ?
>> "Je l’avais relancé en début semaine. Il pense avoir des retours sérieux cette semaine. Si refus, il demandera sur 25 ans au lieu de 20 ans."
12.05 cpmis bien signé ? copie demandée à Nicolas si ok
NON reporté : "Désolé .... au dernier moment le compromis a été reporté. Les acquéreurs n''ont pas encore eu leur accord de principe.
M CHARREL a fait une erreur : il est allé voir le Crédit Agricole puis la courtière qui ne savait pas dc elle a fait une dde à la même banque.
Il attend un retour à nouveau en direct du CA et la courtière a refait une demande pr d''autres banques.
Si cela ne passe pas, il allongera sa durée à 25."
Nico préfère attendre la réponse avant de signer le cpmis car dossier  d''emprunt pas gagné
21.04 CI ok Simulation Vousfinancer ok
notaire: Maître M. LETESSIER Norbert 42570 à St-Héand
Date promesse de vente à confirmer par les parties, a priori le 11 mai à 15h.
20.04  OFFRE ok
Choix notaire à définir. CI acquéreurs en attente de réception.' where app_affaire_id = 28703;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 17.11 VENTE confirmée  lundi 23 novembre. Le notaire dit qu''il n''y a pas d''erreur de sa part concernant la succession et que le vendeur a pour obligation de signer au plus tard le 30 NOV.
13.11 VENTE à confirmer le 23 novembre mais 1 des frères qui a proc pour la gd mère et la soeur ne veut pas signer car le notaire aurait fait des erreurs sur la succession et leur devrait de l''argent. Il ne veut pas signer tant que le notaire n''a pas réglé le problème. Maubert et Meyer sont dans la même étude mais ont chacun un clerc qui s''occupe du dossier, Tatiana essaie d''appeler celui de Meyer car celle de Maubert ne lui a pas répondu.
09.11 ODP CA reçue par les clients et transmis directement au notaire sans passer par le courtier ni Tatiana. Tatiana a essayé d''appeler le notaire + envoyé un mail pour RDV VENTE
05.11 ODP pas encore éditée car Mme Richter a pris un nouvel emploi et a terminé sa période d''essai le 29 oct. La banque attend l''embauche définitive pour éditer l''ODP.
VENDEURS mécontents du temps que cela prend, ne PAS envoyer d''AVIS ni à l''ACQ qui ne répond plus à Tatiana depuis juillet, elle communique avec le courtier.
04.11 ODP mess tél à Tatiana
16.10 ADP courtier pense qu''ils valideront la demande de prêt semaine prochaine
01.10 AVNT DB30sept. reporté au 30 novembre pj.
25.09 Vacq.30sept. rdv CA solde crédits 6 oct. représente le 12 oct. sur AVNT DB30nov.
24.09 AVNT demandé à Tatiana :
>> La signature est toujours en cours, mes clients ont reçu le mail ce début de semaine. J’attends un retour, je te tiens au courant.
10.09 le notaire va rédiger un avenant pour prolonger à fin novembre car ne peut pas passer la vente de la RP de M. Richter avant octobre.
Tatiana prévient ses vendeurs
03.09 rpse courtier : en attente vente RP de M. Richter pour édition ODP.
- congés Tatiana 9 au 23 août -
06.08 report vente de l''acq. donc de l''ODP
cependant accord de principe en pj.
courtier : "Bonsoir Maître MAUBERT-DELAMORINIERE, bonsoir Maître MEYER et bonsoir Madame CROIZIER,
Je suis le courtier en prêt en charge de la demande de financement de Monsieur RICHTER et Madame DESPIERRES.
Vous n''êtes pas sans savoir que la bonne finalisation de ce projet est liée à la vente de la RP actuelle de Monsieur RICHTER, vente initialement prévue le 26 juillet 2026 mais malheureusement reportée à la fin août à cause du diagnostic amiante qui n''était plus valable suite à la division copro... Bref, nous perdons 1 mois entre les congés de chacun pour acter cette vente mais tout le monde est informé y compris l''acquéreur et la banque de l''acquéreur qui attend la nouvelle convocation pour lancer le déblocage des fonds.
De notre côté, nous avons tout de même maintenu le rendez-vous de ce jour au CIC pour avancer sur le dossier (notamment sur la partie conformité bancaire) mais également pour pouvoir vous transmettre l''accord du CIC malgré les réserves évidentes de remboursements de crédits liés à la vente du bien.
Je vous joins donc l''accord du CIC en attendant de pouvoir valider définitivement le projet et vous transmettre au plus tôt les offres de prêt.
Je mets en copie de ce message Monsieur RICHTER, Madame DESPIERRES et Monsieur BONNEVIALLE du CIC.
03.08 ODP demandée à Tatiana
>> "Il va signer sont offre de prêt le 5 aout à la banque.. "
13.07 ADP ok pj.
Suite à notre échange d''hier, je vous envoie donc l''attestation de dépôt de dossier et la simulation "définitive" du CIC pour le futur financement de Mme DESPIERRES et M RICHTER.
Attention, comme évoqué ensemble, et ce n''est pas un secret, je suis contraint d''attendre la vente effective de la RP actuelle de M RICHTER pour pouvoir finaliser le dossier immo avec le CIC. En effet, la vente de M RICHTER est soumise à l''acceptation de main-levée d''hypothèque partielle de la part du crédit agricole ; certes c''est en cours mais l''accord écrit n''a pas encore été transmis au notaire donc tout est en "stand by" pendant encore quelques jours.
09.07 prêt déposé, il n''y aura pas de soucis, elle n''a pas l''attestation.
06.07 ADP demandée à Tatiana
>> "J''attends un retour de mon client et je reviens vers toi."
18.05 PUV le 3 juin
CI ok
15.05 relance PUV + CI Richter
06.05 rdv PUV demandé à Tatiana + CI Richter
>> J''attends un retour du clerc et reviens vers toi rapidement.
Je vais récupérer la CI ce soir normalement 
27.04 OFFRE ok
CI demandées à Tatiana Mme DESPIERRES ok manque M. RICHTER' where app_affaire_id = 28764;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11.2026 rpse VENDEURS ci-dessous transmise à M. VERNET 
isabelle.cros-1@orange.fr  "Bonjour, je suis la nièce de Mr Paul Jourdy . J’ai contacté EDF OA pour la résiliation du contrat. Les démarches sont en cours. J’ai dû contacter Enedis qui me dit qu’ils ont relancé plusieurs fois Mr Vernet pour une attestation de propriété qu’ils n’avaient toujours pas ( depuis août).Ils vont de nouveau le relancer je ne possède pas ce document. Le contrat de production photovoltaïque déclenche une prime de 900 euros qu’il touchera puisque mon oncle n’avait pas terminé les démarches sinon il faut passer le contrat à notre nom puis le transférer au sien.
Je vous tiendrais informé de la suite.
10.11.2026 PB étanchéité : M. Vernet a visité uniquement par beau temps pendant la canicule, n''a pas relevé de trace d''humidité. N''a pas fait de déclaration à l''assurance. L''eau s''infiltre par le faîtage et la cheminée dans la maison et par la véranda dans le garage au niveau du tableau électrique. M. Vernet vit dans des bâches et voudrait être mis en relation avec les vendeurs. FRANCK : demander à Sylvie (en arrêt) de contacter les vendeurs
tél à SYLVIE : trace d''humidité mise sur le compte du fait que la maison est inhabitée depuis 1 an et condensation avec la chaleur caniculaire. Ce sont les frères et soeurs du défunt qui ont hérité, ne connaissent pas la maison. Elle les avertit du problème et leur donne les coordonnées de M. Vernet. Elle va également appeler ce dernier après les avoir eu.
>> SYLVIE a eu Mme Combien qui avait l''info par le notaire et a demandé à ses co-héritiers si quelqu''un connaissait l''existence des infiltrations > NON, et ne comptent pas recontacter l''acq. SYLVIE a rappelé M. Vernet pour lui dire et lui conseiller de faire une déclaration à son assurance.
Il n''a pas non plus réussit à reprendre le contrat photovoltaïque car les vendeurs doivent contacter la compagnie. Sylvie lui a dit de me faire un mail pour transmettre aux vendeurs. 
06.11.2026 PB : l''acq. a appelé Nico Bouchet (Sylvie en arrêt) car il a des d''infiltrations au niveau du toit et de la véranda toit et sol. Nico lui a demandé un mail et comptait lui envoyer les coordonnées du vendeur.
Je lui ai dit de me transférer le mail pj.
29.07 VENTE signée
09.07 DP volet roulant pj.
22.06 RDV confirmé  mercredi 29 juillet 2026 à 14 heures.
18.06 Offre de prêt VERNET. pj. RDV de principe pour vente 28 juillet 15h00.
17.06 ODP M. VERNEY l''a reçue, il est dans le délai Scrivener. Il l''envoie à Sylvie pour qu''elle prenne un rdv de vente.
17.06 Volets roulants ok
ADP : Sylvie a laissé un message
10.06 ADP + volets roulants demandés à Sylvie
13.05 PUV ok
p16 (V) réparation volets roulants < 12 juin
🅿160K 25a
30.04 PUV mardi 12 mai prochain à 15 heures
29.04 CI-A + envoi Rocher demandé à Sylvie OK
28.04 OFFRE ok
CI M. VERNET demandée à Sylvie' where app_affaire_id = 28853;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 ODP demandée à Christèle ?
04.11 AVNT signé pj. DB15nov.> 15DEC. ODP15oct.>15NOV.
ODP : sms de Acq. "Oui les devis sont passés auprès de Nicolas et à la banque. Nous signons l’offre de prêt jeudi 12. Si tout va bien suite à cela la SCM sera créée avec le compte bancaire les statuts sont ok en attente. Voilà tout roule je vous tient informer suite au jeudi 12. Merci bonne journée"
30.10 AVNT demandé à Christele
21.10  REPORT DELAI : <nicolas.valladier@vousfinancer.com>
À christèle, gagne.emeline@gmail.com, moi
Bonjour Christelle,
Je reviens vers toi suite au rdv de vendredi avec Mme GAGNE et Mr ESQUIS. A ce jour le maître d’œuvre a donné une enveloppe globale pour les travaux, mais n’a pas encore remis les devis définitifs. Sans cela nous ne pouvons avancer sur le montage définitif du prêt.
Il serait souhaitable de d’avoir un délai complémentaire pour la vente, car avec les délais bancaires incompressibles nous ne pourront pas être prêt pour le 15 Novembre.
Merci de voir si il est possible de décaler la date buttoir au 15/12/2026.
19.10 AVIS de valeur locative envoyée par Christèle aux clients pour leur prêt + demande de presser les artisans
16.10 ODP relance Christèle
>> Les devis ne sont pas encore chiffrés !!!! donc le courtier n'' a pas pu présenter le dossier , il va falloir faire un avenant
12.10 ODP reçue ?
congés Christèle 6 au 21 sept.
28.08 Prêt déposé nicolas.valladier@vousfinancer.com 06.07.33.34.67 24 juil. suite demande répartition prix local co / logement
28.07 mail du notaire à Christèle : J’ai bien reçu le dépôt de garantie, et la provision sur frais.
Je n’ai pas reçu l’extrait Kbis et les statuts. Je vous précise que cela n’est pas bloquant pour l’instruction du dossier à aujourd’hui.
06.07 rdv PUV demandé à Christèle :  vend. 17 juil. à 15h30
26.06 CI ok
22.06 OFFRE ok
CI-A + simul en attente' where app_affaire_id = 28897;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 VENTE reportée MARDI 15 DECEMBRE à 16 H 00 en VISIO.
06.11 VENTE fixée  lundi 23 novembre à 15H
02.11 relance ARNAUD
>> le notaire de banque doit contacter Me Breuil pour le RDV
30.10 ARNAUD NRP
23.10 Relance ARNAUD
12.10 ODP + rdv Vente : relance Arnaud
Clients ont déjà une SCI, création d''une nouvelle ?
23.09 ODP rappel Arnaud J-7
RPSE clients : Nous avons l’accord de principe pour le prêt, il nous manque simplement les statuts définitifs et l’immatriculation de la société pour finaliser le tout. Je vous tiens au courant dès que tout est prêt.
CLAUSE SUBSTITUTION bien prévue p28
04.09 ADPx Pas de soucis de financement, le dossier était presque bouclé lors de la signature du cpmis
28.08 ADP ? mess tél à Arnaud
>>  Ils sont en congés...
21.08 ADP demandée à Arnaud
- congés Arnaud 10 au 19 août -
03.07 PUV vendredi 17 juil.
01.07 OFFRE ok
CI ok' where app_affaire_id = 28914;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 ODP pj.
19.11 idem relance Christine par mail
>> offre reçue qui doit se signer à partir du 29.11..... Date de vente à définir
18.11 AVNT signé ? mess tél à Christine 
12.11 l''ODP est bloqué car le délai du compromis est passé. La BP demande un AVNT...
09.11 Le vendredi 06/11 sa conseillère bancaire lui dit que son dossier est parti à l''édition. Ça ne devrait plus tarder !
27.10 ODP : demande à Christine de relancer le courtier gregory.basty@ac-courtage.com 04 73 92 25 19
congés Christine 19 au 25 oct.
16.10 ODP "Mme Rous a choisi la banque populaire pour la représenter..... toujours en attente de l''édition de l''offre"
15.10 ODP : relance Christine
02.10 ODP : Mme Rous a envoyé un mail au notaire cc/Christine pour expliquer le retard. A ce jour le financement n''est pas encore validé.
24.09 ODP J-7 : rappel Christine
26.08 J''ai eu Mme Rous au téléphone, elle signe la ventes de sa maison vendredi 28 et elle a rdv avec sa banque samedi...🤞🤞🤞
25.08 relance Christine
17.08 ADP + rdv Vente acq. demandés à Christine
22.07 CPMIS ok
💡Mémo délais :
- Demande de prêt avant le 17 août
- Vente du bien de Mme Rous avant le 24 août
- Offre de prêt avant le 1er octobre
- Signature vente avant le 30 octobre 2026
20.07+21.07 relance copie
07.07 mess tél à Christine rdv Me Labidoire ?
PUV  vendredi 17 juillet à 09h45 avec Maître Delphine VALADIER.
congés Christine jusqu''au 5 juillet
16.06 Eu Christine, le Vendeur n''a pas de mail pour envoyer l''offre, sa maman est au courant de l''offre et ok pour signer une proc à son fils pour le CPMIS. Christine envoie le dossier et fera ajouter la mention à son retour de congés
16.06 OFFRE en attente 1 signature
🏡 cpmis signé 19 mai
🅿 SIMUL AC COURTAGE GREGORY BASTY 04 73 92 25 19 du 07 mai 2026
"Il me manque encore quelques documents pour envoyer les 2 dossiers chez Maître Labidoire."
CI ok' where app_affaire_id = 28921;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 24.11 PC dépôt en attente SPANC :
" Bonjour Madame Reynaud,
Merci pour votre message et pour votre suivi concernant le terrain à Ponsas.
Nous comprenons tout à fait l''enjeu lié à l''échéance du 30 novembre prévue au compromis de vente et tenons à vous rassurer sur notre pleine mobilisation. Pendant la période estivale de juillet-août, l''avancement a été ralenti car, comme c''est souvent le cas à cette période, les architectes n''étaient pas disponibles pour répondre à nos consultations.
Malgré tous nos efforts pour faire avancer le projet depuis, le dossier n''est pas encore finalisé : nous sommes actuellement dans l''attente de la validation de l''assainissement par l''administration (SPANC). Ce document est indispensable pour constituer un dossier complet et nous déposerons la demande de permis de construire dès sa réception. Pour information, il ne sera pas possible de se raccorder sur l’assainissement commun existant et cela nécessite de faire valider la solution d’assainissement individuel retenue.
Vous trouverez ci-joint l’étude de faisabilité d’assainissement autonome qui a été déposée (SPANC). Il a fallu attendre que l’implantation de la construction soit définie avant de faire réaliser cette étude.
Nous ne manquerons pas de vous tenir informée dès que nous aurons le retour de l''administration et que le dépôt sera engagé.
23.11 PC récépissé de dépôt demandé à Corinne
>> "Je suis en attente de l''envoi de ce récépissé, j''ai demandé aux acquéreurs de me le transmettre. Dès réception, je te l''enverrai."
22.07 RDV 31 juillet
21.07 mail à Corinne : est-ce que le notaire a tous les éléments pour fixer une date de compromis ?
13.07 OFFRE ok VENTE 18406 + 18393
CI ok' where app_affaire_id = 28944;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 PC mail à Nico pour qu''il relance son acq.
23.10 PC pas encore déposé car l''architecte a fait des erreurs. Ne sera déposé que mi novembre
EAU : le déplacement sera accordé avec permis
🏡 Vfixée 4 novembre
16.10 relance Nico et demande d''appeler la mairie si pas de réponse des clients pour avoir la date exacte de dépôt.
>> "J’ai demandé au client. J’attends son retour.
Si je n’ai rien semaine pro je contacte la mairie. "
12.10 relance Nico récépissé PC
>> Je viens de faire la demande. 
02.10 PC déposé cette semaine, Nico va recevoir le récépissé. Les acq ont fait aussi une demande pour l''eau.
20.08 relance Nico : oui tout est bon
18.08 Nico se renseigne pour savoir si cpmis bien signé
- en congés du 27 juillet au au 17 août -
07.08 PUV ok
p11 - accord déplacement eau potable < 1er mars
        - PC maison 120m² < 31 déc.
p13 - Vente bien cpmis 18 août 2026

06.08 copie demandée à Me Chazottes + Me Barre
rpse Me Barre : l''attend copie de la PUV par son confrère
21.07 Promesse de vente le 5 août à 18h. 
OFFRE+CNI ok
Conditions : obtention PC+accord service des eaux déplacement conduite d''eau' where app_affaire_id = 28964;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 25.11 VENTE vendredi 4 décembre à 11h30 à l’Etude avec Maître BARRE.
21.09 Vente Bien Mme M. REGNIER 18711 : C14sept. ODP14nov. DB14déc.
25.06 PUV mercredi 5 août à 17h à l’Etude avec Maître BARRE.
22.06 OFFRE ok
CI ok' where app_affaire_id = 28970;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] M. Rosinski 06.40.64.48.16

25.11 APPEL de CEGELEC pour avoir les coordonnées du nouveau propriétaire afin de signer une convention pour installer une armoire électrique à l''angle de la maison devant la haie.
M. ROSINSKI : le rappeler vers 17h.
SERVITUDE noté dans la promesse :
"Le PROMETTANT déclare qu’un projet d’installation d’une armoire de coupure HTA pour réseaux souterrains existe. Le PROMETTANT déclare n’avoir donné aucun accord à ce titre et s’engage à ne rien faire à ce sujet. Le BENEFICIAIRE déclare être parfaitement informé de ce projet et vouloir en faire son affaire personnelle. Il est annexé à la minute des présentes la documentation de ce projet. "
20.11 VENTE signée, att. pj.
CLE en agence remises à M. Rosinski 06.40.64.48.16 par Guillaume Perret lors de la signature de la vente chez Lucht.
VISITE avant vente : Guillaume n''a pas pu faire le relevé de compteur d''eau car pas accessible, il aurait fallu une échelle pour descendre dans la cavité mais élec. ok. Maison vidée ok.
02.11 MESS tél à M. DESAGE
30.10 NICO et ARNAUD pas dispo, déjà en rdv notaire. Vu avec Franck pour envoyer GUILLAUME ok pour lui.
28.10 VENTE confirmée 20 NOV. 16h. chez Lucht. Nico et Arnaud avertis, en attente de savoir qui ira ?
27.10 ODP reçue par M. Rosinski, fin des 11 jours ok, le notaire a proposé le 20 nov. 18h puis 16h car pas possible du côté vendeur.
reste à confirmer.
Fin SAFER 02 NOV
30.09 ADP : Sylvie la demande. M. ROSINSKI a signé sa demande, il devrait avoir l''offre d''ici peu. Il y a une SAFER à purger, elle a demandé à Rocher de la rappeler pour connaître le délai.
10.08 PUV ok
Prêt relais sur maison à Ste Sigolène pas GTI car c''est le père Rosinski qui rachète la maison.
27.07 signature cpmis le 7.08 à 14h à l''étude de Me Rocher Tence
23.07 mail à Sylvie pour date cpmis 
15.07 offre Géraldine + CNI ok. Dossier envoyé ce jour à Me Lucht 
13.07 OFFRE manque la signature de Géraldine
CI-A en attente' where app_affaire_id = 28972;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] NE PAS APPELER Mme GARCIA (souffre de bipolarité), son mari se charge de venir signer avec elle ou proc.
18.11 VENTE bien signée. ATTESTATION pj.
28.10 VENTE 17 novembre 14 ou 16h à confirmer l''heure.
20.10 rdv VENTE : relance Alice
>> "Je l''ai relancée la semaine dernière, elle me contactera début novembre pour proposer un rdv car pour le moment tant que la safer n''est pas passé, elle ne veut pas fixer le rdv."
06.10 VENTE : Mme et M. Garcia passent à l''étude pour signer une proc. au cas où ce serait nécessaire, en fonction de l''état de santé de sa femme.
Alice relancera pour le rdv de VENTE
28.09 VENTE : Alice relancera pour fixer le rdv sur novembre
11.09 facture nettoyage fosse pj. et transmise à Me Coulaud
01.09 SAFER à purger :
"Chère Madame, Cher Monsieur,
Je me permets de vous écrire concernant votre acquisition,
La mairie vient seulement de me transmettre les éléments nécessaires pour savoir s’il y a lieu de purger la SAFER.
Nous devons purger cette préemption ; Maître Tessier vient de signer le droit de préemption.
Nous devons attendre deux mois pour pouvoir signer car la SAFER ne répond pas quand elle ne préempte pas.
La signature pourra avoir lieu début novembre.
Je ne manquerai pas de revenir vers vous pur fixer une date de signature.
Vous en souhaitant bonne réception,
Bien Cordialement
14.08 CPMIS pj.
13.08 RENEGOCIATION 95000€ au lieu de 100K pour participation vendeur au remplacement de la toiture à venir.
27.07 retour offre contresignée mais d''un seul propriétaire
OFFRE envoyée en LRAR aux vendeurs car pas de contresignature - dossier envoyé ce jour au notaire
Alice : J''ai eu une offre concernant le mandat 18645 qui a été acceptée par les vendeurs. 
Toutefois ils n''ont pas de mail, je leur ai envoyé par courrier l''offre à contresigner mais ils ne l''ont pas reçu donc je leur ai demandé de me faire un petit courrier d''acceptation qu''ils m''ont transmis par sms.
Je vous joins donc l''offre des acquéreurs et l''acceptation à part.
Je prépare les éléments pour le notaire.' where app_affaire_id = 28978;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 19.11 ODP : relance Nico > refusé car taux d''usure trop haut suite 300€ d''assurance pour Monsieur.
Demande de prêt refaite assurance au nom de Mme uniquement, attend un retour dans la semaine du CA
AVNT pas nécessaire car CPMIS 
12.11 ODP : Nico n''a pas rappelé, il s''en occupe
04.11 ODP : assurance ok RDV CA auj. pour signer le prêt
29.10 Congés Nico retour semaine pro
21.10 ODP : l''assurance externe n''a tjrs pas donné de réponse.
15.10 ODP : M. a des pb de santé, recherche d''une assurance externe ou fera sans assurance.
15.09 ADP CA du 11sept. pj.
14.09 ADP demandée à Nico
- congés Nico 15 au 31 août -
17.08 CPMIS ok
💡Mémo délais
- dépôt dossier en banque avant le 14 sept.
- offre de prêt avant le 14 oct.
- révision de la chaudière gaz (V)
- signature vente avant le 14 nov. 2026
****
04.08 CPMIS le 14 Août 2026 à 15H
28.07 RPSE: Je l''ai reçu et ai envoyé le dossier complet au notaire à réception, vendredi dernier 
28.07 mail à Nico pour attestation TAE + notaire vendeurs ?
Il ne me manque que le test de raccordement au tout à l''égout qui est prévu le 23 juillet
Vendeurs ne savent pas encore s''ils prennent Me Labidoire, Nico nous tient au courant' where app_affaire_id = 28979;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 G1 : rdv pas encore fixé. Sandrine avait bien prévenu son vendeur de l''obligation de la réaliser mais n''a pas voulu le faire tant que le notaire ne lui a pas confirmé.
PC : Sandrine relance Mme Klaja, car n''a pas encore eu le retour.
16.11 rdv G1 + rpse PC demandés à Sandrine
06.11 copie demandée à Sandrine
>> Le compromis n''a pas été signé hier, on attend la date pour l''étude des sols car il s''avère qu''il est sur une portion argileuse, de plus nous avons la réponse le 14 novembre concernant l''acceptation ou non du permis de construire.
Le notaire ne veut donc pas fixer une date tant que tout cela n''est pas fait.
20.10 CPMIS fixé 5 nov. 9h30
13.10 RDV CPMIS M. Ben Brahim a appelé Me Auboyer. Pas encore de rdv fixé.
06.10 RDV CPMIS : Sandrine relance Me Auboyer.
30.09 RDV CPMIS : Sandrine relance Me Auboyer. 
CI ok
28.09 RDV CPMIS + CNI : relance Sandrine
21.09 Mme Klaja a vu le maire, elle a déposé une demande de CUb qui sera en condition suspensive. Sandrine envoie le dossier à Me Auboyer. Elle a la CNI de Mme Klaja.
14.09 Mme Klaja veut voir d''abord le maire pour savoir si la construction est réalisable ou pas, la mairie aurait dit au vendeur et à Sandrine qu''elle ne répondrait pas à une demande de CU !?
02.09 MANDAT exp. le 5 sept. 2026
Conditions PC+en att. CU + zone Ub mais SEVEZO' where app_affaire_id = 28985;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 17.11 VENTE fixée 27 Novembre. La notaire s''est renseignée auprès du CRIDON pour passer la vente en l''état.
17.11 DP maison revenue négative. Stéphanie demande la DP de division à la mairie pour savoir exactement ce qui a été demandé car la notaire dit que la DP de division est lié à la construction de la parcelle voisine et à notre vente
06.11 DP rpse mairie ? >> J''ai demandé a caler la date de vente quand meme.  On devrait tout a voir d ici 15 jours. J attends le retour du notaire.
27 NOVEMBRE A 14H , soit pour la vente ou pour rediger la convention d''occupation 
23.10 DP retour mairie ? >> La mairie a transmis à Loire Forez, normalement ça devrait passer, en attente du retour. ACQ passent leur vente le 8 DEC. donc signature avant obligatoire
16.10 régul. mairie ok ?
>> On attend le retour de la mairie. Dossier déposé complet y a 3 semaines.
28.09 M. KOCK dépose auj. un nouveau dossier en mairie
La clerc n''a pas répondu à Stéphanie sur le fait que le refus de PC concernant la maison voisine et pas celle qu''on vend.
21.09 DIA : personne en charge à la mairie revient qu''auj. de congés > la clerc l''appelle.
15.09 DIA : Stéph. rappelle la clerc pour savoir en quoi le refus de permis de la maison de la parcelle voisine empêche notre vente ?
14.09 ODP ok
09.09 PB DIA cf mail
03.09 PUV ok
p24 contrôle TAE avant vente
05.08 CI ok
05.08 CI Mme ok, M. pas bon car permis. CI demandée à Stéphanie
04.08 compromis le 2 septembre chez maître Depierre feche a montbrison, changement de notaire pour nous faciliter la tâche pour la création de la servitude avec les voisins
[accès par BH-24 propriété Bourlinchon ?]
CI-A relance Stéphanie
31.07 OFFRE: adresse du bien vendu incomplète, manque code postal et ville
MANQUE CNI A' where app_affaire_id = 28989;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 VENTE signée att. pj.
15.10 VENTE fixée 20 NOV. 9h30 > Emmanuelle a remplacé Vince''.
08.10 Eu Mme VEROT, Mme DAVID, clerc Me Macret. RDV 20 nov. dans le matin, à confirmer Me Pauze
07.10 ODP reçue
mess. tél à Mme Verot pour connaître ses dispos.
Vendredi 20 matin, Mardi 24 matin, Vendredi 27 matin.
tél à Me Pauze : n''a pas encore le retour de la mairie mais réponse en générale assez rapide.
06.10 ODP M. Epalle Mme David m''envoie leur offre de prêt. Ils ont pris les mesures avec la propriétaire et ont vu avec elle pour une signature autour du 20 novembre mais aimerait avancer si possible.
DISPO ACQ. : mardis matin ou début d''après-midi ou vendredis toute la journée.
03.09 PUV ok
p17 dépôt avt 1er oct.
29.07 compromis le 01sept. à 18h30…
OFFRE ok - Prêt bancaire
* CONTACTS : 
Me Macret clerc : c.vernay.42002@notaires.fr
Me Pauze clerc : nicole.varlet@42031.notaires.fr
(V) Madame Isabelle VEROT Téléphone mobile : 07.60.32.19.40 Courriel : isa.777@hotmail.fr
(A) Monsieur Thomas EPALLE Téléphone mobile : 06.66.82.91.17 Courriel : thomas.epalle@icloud.com
Madame Kathleen DAVID Téléphone mobile : 07.63.00.87.14 Courriel : kathleen_david@outlook.fr' where app_affaire_id = 28991;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 26.11 PUV ok M. Chauvet assisté de son curateur M. Bresson
p34 (V) enlèvement cuve fioul
23.11 PUV copie demandée à Arnaud
02.11 PUV fixée 20 novembre 14h30
M. Chauvet est en fait divorcé depuis le 13 nov. 2018, a acquis le bien le 8 juin 2017 mais en nom propre car partage réalisé 7 nov. 2015. Intervention de Mme Berroyer à l''acte.
12.10 relance Arnaud : accord Mme Chauvet née Berroyer pour signer ?
>>  M. Bresson a dû faire une nouvelle demande au juge concernant les nouvelles conditions et l''intervention de Mme Chauvet. Comme c''est le tribunal de la Loire, ça risque d''être long...
21.09 M. CHAUVET /s curatelle renforcée a un accord du juge à 40K pour lui, or le divorce n''a jamais été prononcé, sa femme Jocelyne BERROYER est donc propriétaire de la moitié (pas de contrat de mariage).
11.09 Arnaud relance Me Latour
04.09 OFFRE ok
CI ok' where app_affaire_id = 28995;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 VENTE décalée au 4 décembre
13.11 VENTE 25 novembre à 18h30.
12.11 ODP ok pj. p1 
VENTE : "la date de la vente reste à confirmer pour le 27 novembre, je te le confirme rapidement.
03.11 Nico appelle sa cliente pour ODP PTZ
22.10 ADP ok CA avec avis favorable pj.
15.10 ADP : L''acquéreur va nous fournir d''ici vendredi sa demande de prêt, un peu de retard car PTZ et besoin d''avoir les  retours de devis.
Cela devrait aller vite ensuite.
13.10 ADP : Nico relance son client pour son prêt.
06.10 ADP + dépôt DP panneaux : demandés à Nico
>> non opp. DP ok pj. du 12sept.2023 (retrouvée par le vendeur)
ADP : Nico la demande
07.09 PUV ok
p31 (V) accord mairie panneaux photovoltaiques
04.09 PB HEKTOR résolu.
07.08 PB HEKTOR ticket car l''offre n''apparaît pas sur le bien.
La date de la promesse de vente est fixée au 4/09 à 17h chez Maître Robin
CI-A' where app_affaire_id = 29001;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 CUb ok pj.
19.11 VENTE 09 décembre à 11h chez Chassaint
13.11 CUb + VENTE : relance Christele
10.11 CUb : Christèle n''a pas reçu l''accord du CUb, il est indiqué sur le récépissé de dépôt, qu''en l''absence de réponse sous 2 mois, le récépissé vaudra CU d''information tacite (aucun intérêt puisque pas d''info...). Christèle a envoyé un mail au notaire ce jour et rappelle la clerc jeudi.
09.11 accord CUb demandé à Christèle avec rdv Vente ?
10.09 PUV ok
p12 CUb construction maison 120m²
20.08 PUV fixée 9 septembre prochain à 16 Heures à AIGUILHE
12.08 CI ok
11.08 OFFRE ok
CI acq en attente' where app_affaire_id = 29022;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 25.11 VENTE vendredi 4 décembre à 11h à l’Etude avec Maître BARRE.
20.11 VENTE relance Christèle pour date rdv ?
13.11 VENTE rdv fixé ? > pas de réponse
05.11 ODP ok pj.
16.10 ADP demandée à Christèle ok
Accord de principe de financement CA valable jusqu''au 9 sept.26 pj.
- congés Christèle 7 au 21 sept. -
18.09 PUV ok
Mme M. REGNIER achètent 18638
16.09 copie PUV demandée directement à Me Barre
27.08 PUV lundi 14 septembre à 17h30
27.08 OFFRE ok
CI ok' where app_affaire_id = 30661;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 25.11 PRET VENDEUR accepté par notaire et parties ?
18.11 PRET : Monsieur Meunier a eu trois refus prêts . Monsieur lui propose de faire un "prêt vendeur " . Il étudie sa proposition pour nous faire un retour définitif fin de semaine
[*CREDIT VENDEUR l''accord est officialisé dans l''acte authentique de vente qui fixe les échéances, le taux et les garanties. Les intérêts (V) sont taxé à 31.4% Flat Tax ou 18.6%+barème impôt sur le revenu si intégrés dans les revenus.
Obligation de déclarer le prêt Cerfa 2062.
Garanties pour le vendeur : hypothèque ou PPD, caution solidaire, clause résolutoire (récupération du bien), assurance décès-invalidité.
Apport versé à la vente.]
09.11 PRET : Monsieur Meunier a eu deux refus de prêt . Il essaye une dernière tentative sur 20 ans avec de l''apport 
27.10 ADP : refus de la banque dans laquelle sa tante travaille car ne voulait pas investir son apport. Il passe finalement par un courtier. En attente de l''accord.
21.10 ADP demandée à Mélanie
24.09 PUV ok
14.09 CI-A relance Mélanie ok
10.09 Puv fixée le 24 septembre 
03.09 OFFRE ok
CI en attente' where app_affaire_id = 30676;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 25.11 VENTE confirmée Jeudi 10 décembre à 15H.
25.09 CPMIS ok "Je vous informe que la signature de l’acte de vente a été fixé au 10 décembre à 15h."
SAFER à purger
15.09 Compromis prévu le 24 septembre à 15H.
OFFRE ok  CI ok' where app_affaire_id = 30681;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 La notaire a eu M. Celik, il a rdv ce mardi avec une autre banque.
12.11 rétractation : relance Manue pour qu''elle demande au notaire d''intervenir.
09.11 rétractation : M. CELIK n''a pas encore transmis les refus. J''ai dit à Manue de passer par le notaire pour les obtenir si nécessaire.
05.11 rétractation : M. CELIK a laissé un mess à Manue pour lui dire qu''un artisan a fait un devis à 70K et qu''il ne peut emprunter que 36K. 
Manue lui a laissé un mess en retour lui indiquant que le montant des tvx semble très élevé (isolation ext. ?) et que s''il ne souhaite plus acheter il doit fournir 2 refus de prêt à 161K 25a 4%
03.11 ADP x
29.10 BANQUE trouvée montage dossier en cours. ADP demandée par Manue
28.10 ADP demandée à Manue
29.09 PUV ok
p11 ODP28nov.
p31 SERVITUDE CHAUDIERE "De plus, les parties déclarent que la chaudière se trouve dans le garage restant à la propriété du PROMETTANT.  Par conséquent, ce dernier s’engage consentir au profit du lot appartement une servitude d’implantation de la chaudière existante équipant l’appartement et située dans le lot deux (garage) appartenant au PROMETTANT, avec droit de passage pour réglage, entretien et réparation de la chaudière. Cette servitude sera caduque si le BENEFICIAIRE acquière le lot 2, ou s’il décide ou est contraint de changer de chaudière, s’engageant dans ce cas à l’implanter dans l’appartement lot 3. "
24.09 M. Celik achète finalement avec sa compagne Mme YILMAZ Médine 
02.09 Condition sur offre : déplacement chaudière
Compromis 28.09 à 17h' where app_affaire_id = 30687;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 24.11 VENTE 14 décembre à 14H
17.11 ODP pj.
16.11 FISE CA pj. Nico averti qu''il ne s''agit pas de l''ODP mais les acq ont dû la recevoir à la suite.
rappel CI-V à récupérer
04.11 nv dépôt CA accord de principe. La Bq Chalus n''a pas donné de réponse.
29.10 Congés Nico retour semaine pro
22.10 refus CA > dépôt banque Chalus (sa banque), en attente de réponse
29.09 CPMIS ok 
CI-V relance Nico
p10 🅿24nov. 134K 25a
28.09 COPIE CPMIS demandé à Nico
24.09 CPMIS Nico signature auj. rappel CI-V
04.09 En attente accord du juge (Marie Elloy sous tutelle) pour signer CPMIS. La mamie est très âgée donc, signature d''un compromis au cas où.
CI-V : Nico les demandera au cpmis.
06.08 Nico a bien mis la mention comme quoi la mandataire signe pour l''ensemble des indivisaires et s''en porte fort et garant, il a eu tous les vendeurs par téléphone. Il récupèrera les CNI. Notaire Lemaître pour les 2. DOSSIER complet transmis au notaire, actuellement en congé et ensuite ce sera Nico, donc signature au retour de Nico.
31.07 mail à Nico pour conf. diags+TAE envoyés au notaire ?+ m''envoyer CNI V et not. acq.
RPSE: dossier envoyé ce jour, date début septembre normalement
OFFRE contresignée de la mandataire judiciaire mais aucune signature vendeurs. Vu avec Franck d''enregistrer comme ça. Nico essaye d''avoir les signatures - manque condition de prêt sur offre (135 000€ sur 20 ans)
Les diags sont prévus le 28 juillet et le test tout à l''égout le 21
Notaire acq? : Je ne sais pas encore au sujet du notaire mais ils vont probablement prendre le leur.
Je te tiens au courant.
MANDAT DE RECHERCHE 18730 sur EM70300' where app_affaire_id = 30688;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 24.11 délai ODP rappelé à Christèle : elle a laissé un mess à Mme Abrial
30.10 PRET déposé à la BP
30.09 PUV ok
23.09 PUV mardi 29 septembre 2026 à 14h00 au bureau de Pradelles
- congés Christèle 7 au 21 sept. -
04.09 OFFRE ok
CI ok' where app_affaire_id = 30691;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 PUV copie : mess tél relance Claire > REPORTÉ
>> "nous avons reculé la date de signature car il s''est avéré qu''une cuve au fioul est tjours présente couplé à un systeme de chauffage au gaz, nous n''avions pas connaissance qu''elle était tjrs en service...
La notaire de l''acquéreur souhaite que des devis soient faits rapidement et voire pour renégocier.
Avec Mr Paillasseur nous nous occupons de faire intervenir plombier et pour la cuve de toute urgence pour rapidement signer , ce qui est la volonté de tous.
Désolée le mail était dans mes brouillons.
19.11 PUV copie demandée à Claire
12.11 Je vous confirme le rendez vous de l''audit jeudi 12 novembre, le rapport vous sera envoyé lundi 16;
Je vous confirme également ma présence pour la signature du compromis en vos locaux le 18 novembre à 10h.
03.11 manque Audit E. sous 15j.
21.10 Vendeuse retour 12 novembre
19.10 RDV : notaires relancés auj.
09.10 DOSSIER envoyé hier 08 oct. aux notaires
CI ok
06.10 Claire en VV : me rappelle
30.09 RENEGO : 230K H12000€ > 220K H11000€
manque signature de M. Gaillard + CNI-A : mess tél à Claire
18.09 OFFRE ok
CI-A en attente' where app_affaire_id = 30692;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 26.11 FIN MANDAT
19.11 ADP x rappel délai ODP à Nico
04.11 ADP : rdv CA 16 nov. PTZ
29.10 Congés Nico retour semaine pro
02.10 CPMIS ok
p5 Lié à l''achat du bien Genestoux 18790
01.10 copie CPMIS demandé à Nico
16.09 Le compromis est prévu le mercredi 30 septembre à 15H30
15.09 Nico a eu les diags mais en attente rdv demain avec Me Labidoire pour constitution de servitude sur le dossier lié GENESTOUX
04.08 OFFRE ok liée à Genestoux / Chataigner
rdv diags 8/09
CI ok BV ok' where app_affaire_id = 30701;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 19.11 ADP x
04.11 ADP : rdv CA 16 nov. PTZ
CHAUDIERE : Nico demande la fact. d''entretien
SERVITUDES :  OK formulaires signés par voisins transmis au notaire par Nico
29.10 Congés Nico retour semaine pro
02.10 CPMIS ok
p6 lié achat 17383
p7 🅿11K 25a 1.99% + 65K 25a 3.45% + PTZ40K 20a < 15dec.
p9 intervention codonataires Michelle et Josette Maraudon, famille OK
p10+p21 constitution servitude
p24 facture entretien chaudière fioul, Nico le demande
--- 
01.10 copie CPMIS demandé à Nico
16.09 Le compromis est prévu le mercredi 30 septembre à 16H15
15.09 Spanc passé, en attente rapport. RDV demain Me Labidoire pour constitution servitudes
Dossier lié à DEVILLERS / CHATAIGNER
04.09 Pas encore de rdv spanc. Demande faite début août sans retour du service. Hortense relance.
rdv servitude à constituer par Me Labidoire
- congés Nico 15 au 31 août -
06.08 SPANC : Nico a rempli le formulaire de demande de rdv, le spanc a 1 mois pour répondre... si demande urgente 150€ de plus que le prix du contrôle qui a déjà augmenté à 250€...
04.08 OFFRE ok liée à l''offre 17383 hangar
diags rdv 8 sept.
rdv ANC en attente SPANC
CI ok BV ok MDR ok
BIEN V810062813' where app_affaire_id = 30702;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 25.11 PUV copie relance Arnaud
23.11 PUV copie redemandée à Arnaud
20.11 PUV copie demandée à Me Didier directement
18.11 PUV copie tél à Arnaud : bien signé mais n''a tjrs pas reçu la copie. La secrétaire qui remplace celle partie en maternité est incompétente et fait beaucoup d''erreurs. Je lui ai dit de demander la copie à Mme Faudon si c''est plus rapide.
13.11 PUV copie demandée à Arnaud
27.10 PUV copie demandée à Arnaud
>> "Le rdv de signature a été décalé au 12 novembre.
Il y a eu un décès dans la famille de Mme Chareyron."
16.10 rdv PUV demandé à Arnaud ?
>> pour ces 2 promesses les notaires ont proposé le même créneau de rdv, le lundi 26/10 à 10h...
En attente de confirmation
05.10 OFFRE ok 🅿+cub
CI ok' where app_affaire_id = 30706;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] CLE à l''agence ACQ ne parlent pas français.
25.11 PRET relance mail M. Corjan rpse banque ?
>> en attente réponse du CIC 
mail de Mme Lhermet : "Madame, Bonjour,
Je viens d’avoir Monsieur CORJAN au téléphone qui m’indique qu’il devrait avoir le retour de la banque cette semaine pour le prêt de ses parents.
Je vous tiendrai au courant dès qu’il m’aura fait parvenir l’offre.
Restant à votre entière disposition pour tout renseignement complémentaire,
Je vous prie de croire en l’assurance de mes sentiments dévoués.
17.11 Tél à Mme Lhermet (clerc) : elle a demandé par mail si M. Corjan avait un délai de réponse des banques, elle n''a pas eu de retour, elle essaiera de l''appeler demain. Elle rédigera l''avenant si nécessaire.
16.11 Eu Mme Hardouin : elle était déjà informée par la clerc de notaire Laura Lhermet et elle avait eu Nico Bouchet qui lui a dit d''attendre un second refus pour remettre en vente. Ok pour un AVNT DB+1mois.
Mail à M. Corjan pour qu''il me tienne informée dès rpse des banques et demande un avenant s''il ne les a pas d''ici le 23 novembre.
13.11 REFUS CA pj. M. Corjan attend la réponse de 2 autres banques.
12.11 ODP + rdv VENTE : relance Me Rocher + M. Corjan
05.11 ODP demandée à M. Corjan par mail (Ukrainien)
03.11 ODP : mail à L.Rocher pour savoir si contrat reçu car délai dépassé et si rdv Vente fixé ?
05.10 copie PUV demandée à Me Rocher OK
p11 🅿60K 15a <24oct. : Me Rocher n''a pas modifié les délais alors que la PUV a été reportée. Difficile d''obtenir l''ODP en si peu de temps.
25.09 PUV reportée 3 oct 15h00
10.09 sous réserve dispo traductrice C25sept.15h
04.09 Proc Monique + rdv PUV demandées à Sylvie
- congés Sylvie 17 au 30 août -
- Lucas Rocher en vces jusqu''au 17 août
12.08 relance Sylvie signature Monique > elle ne sait pas faire, elle passera chez le notaire le 24 pour signer une proc.
10.08 nvelle offre 60000€ H5000€ ok Agnès pj.
en attente Monique
05.08 renégociation 5000€ hono. Notaire en vacances, rdv sera fixé pour septembre
27.07 compromis reporté car à la fin du rdv, les acquéreurs ont souhaité renégocier le prix. Procuration établie au prix de l''offre donc promesse pas signée.
Sylvie doit les rappeler dans 10 jours pour connaître leur nouvelle proposition
02.07 PUV vendredi 24 juillet à 15 heures.
Madame Monique VILATE, les acquéreurs et la traductrice seront présents. Je n’attends plus que le retour de Madame HARDOUIN.
24.06 rdv pas encore fixé
18.06 CI ok
16.06 DOSSIER envoyé au notaire ce jour car Sylvie attendait la réponse du CA si dossier faisable car Ukrainiens > oui sous réserve de docs.
10.06 rdv PUV demandé à Sylvie
04.06 OFFRE ok Acq. Ukrainiens offre signée en présence d''un traducteur.
Financement prêt : ont pris rdv au CIC de Tence > refus' where app_affaire_id = 30709;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 19.11 VENTE 18 décembre à 11h.
16.11 retrait reçu en attente recours à l''agglo. puis rdv Vente
04.11 retrait DP : LRAR rédigée pour M. Brechet à l''attention de la Mairie pour retrait de la DP envoyée à Elodie 
03.11 retrait DP ok ? Non, la mairie n''a rien reçu.
15.10 RETRAIT DP Chevallier : J''ai réussi à l''avoir au tel. Parait il qu''il a envoyé une lettre AR à la mairie hier...
J''y crois pas du tout mais bon, on va attendre un peu pour voir...
06.10 PUV ok sans condition. DPU à purger.
M. CHEVALLIER doit retirer sa DP qui a été accordé par la mairie pour un changement de destination de grange en habitation.
05.10 copie demandée à Elodie
08.09 PUV le 2 octobre à 10h chez Maitre Bouron Oliver à St Germain.
03.09 OFFRE ancienne version + adresse incomplète bien vendu + manque nom du propriétaire. Elodie avertie
CI ok
MANDAT exp. 29 OCT. 2026' where app_affaire_id = 30715;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 PRET : M. Sauvadet vend sa ferme et souhaite acheter sans emprunt car le prêt relais lui couterait trop cher. Il signe sa PUV dans 15 jours, son acheteur ne sollicite pas de prêt. Il demande à reporter l''achat à courant février. Me Brion fera les 2 ventes (fermé le lundi). Sandrine la rappelle demain.
16.11 ADP relance Sandrine
08.11 ADP demandée à Sandrine
08.10 CPMIS ok
01.10 Alice ne pourra pas être présente car a déjà un rdv client et en plus à Issoire
30.09 CPMIS fixé le 8 oct. 9h15
CI : n''a pas mis les bonnes sur Hektor. Mess tél à Sandrine.
28.09 RDV CPMIS + CNI : relance Sandrine
21.09 DOSSIER envoyé début sem. dernière. Sandrine relance Me Brion pour le rdv de CPMIS. Elle a la CNI, les ajoute
08.09 OFFRE ok
CI en attente' where app_affaire_id = 30722;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 18.11 ADP redemandée à M. Palazon > il voit avec sa banque. Il souhaite refaire une visite pour reprendre des mesures > dit d''appeler Emmanuelle pour qu''elle l''organise et transmis à Emmanuelle.
09.11 ADP demandée à M. Palazon mess tél. 07 81 46 93 42
pierrickpalazon90@gmail.com
>> M. Palazon a rdv ce samedi au CA. Il vient de perdre son grand-père et a repoussé le 1er rdv prévu. Il m''envoie l''attestation par mail.
09.10 PUV ok
11.09 OFFRE ok MDR ok CI-A ok
CI-V en attente
Il faut trouver un logement à Mme Peyrache. Intéressée par l''apt de Vince > trop cher
pas de MDV bien Hektor V480062922' where app_affaire_id = 30729;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 25.11 PUV ok
- p7 DIA sera adressée dans les 30 jours suivant l''accord de PC.
- p8 SERVITUDE de passage sur BO-274 accord de la mairie ou commune
- p8 RACHAT Comcom : accord du conseil communautaire de l''achat à 5€/m² d''une partie du terrain à détacher purgé de recours (+2mois)
- p10 PC dépôt < 30 AVRIL 2027
- p9 PC arrêté et attestation de NON RECOURS : pc valant permis de démolir < 24 NOV.2027 pour construction d''un parc Batterie de stockage d''électricité de 12MW +3moi si demande de pièces complémentaires.
- p11 à 15 conditions de faisabilité du projet
- p15 PRET < 1mois avant soit 24 OCT.2028
CI-A : tjrs ABSENTE plusieurs sociétés en cascade gérant Charles Nucci > vu avec Franck : ne pas insister.
****
19.11 idem relance Christine par mail
>>  en attente de la signature du PDG de l''acquéreur... Mme Childeric a signé une procuration à l''étude pour signer à sa place. Nous étions en visio avec le notaire de l''acquéreur et avons vu tous les points du dossier avec Maître Labidoire.
18.11 CPMIS copie demandée à Christine avec relance CA sur mess. tél.
27.10 Cpmis fixé 16 novembre à 16h chez Labidoire
congés Christine 19 au 25 oct.
08.10 OFFRE Sté Isolaris représentée par son DG délégué M. Duclaux ok vu avec Franck 
PROJET : parc batterie sté ISOSOLARIS sous réserve de conditions 
- projet réalisable avec seuil de rentabilité puissance mini 12MVa
- revente à la ComCom 5€HT/m² de la superficie non utilisée
- études géotechniques (financées par la sté acq.)
- autorisations administratives
- contrats de raccordement EDF et contrat de fournisseur d''élec
- 🅿
* CALENDRIER PREVISIONNEL : 
PUV M+2 (= décembre)
dPC M+4 (=février27)
oPC M+8 (=juin27)
oConvention de raccordement M+16 (février28)
Vente définitive M+24 (octobre28)' where app_affaire_id = 30735;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 19.11 idem relance Christine par mail
>> "Rien de nouveau . L''édition de l''offre de prêt de Mme Lerest ne devrait pas tarder"
>>> Demande à Christine de ne pas attendre le dernier moment pour s''assurer que les docs de la DP ont bien été transmis par M. Caulier au notaire.
18.11 ADP + Daact et non opp. : relance Christine mess. tél.
12.11 ADP + Daact et non opp. demandés à Christine, s''en occupe.
13.10 CPMIS ok
p9 DP Obtention d’une attestation de non-contestation de la conformité en ce qui concerne le ravalement de façade. DP déjà déposée et obtenue, ne manque que la Daact et sa non opp.
---
24.09 RDV cpmis relance Christine mail car tél sur rép.
17.09 RDV cpmis demandé à Christine
08.09 OFFRE ok CI ok
Christine va essayer de ne prendre que Me Labidoire pour aller plus vite.
Mme LEREST a une maison à la vente avec Nico n°18615, se sépare de son compagnon M. GENESTAT mais Christine me dit qu''il n''est pas nécessaire de vendre pour acheter. Financement vérifié.' where app_affaire_id = 30736;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 18.11 PUV ok
30.10 rdv PUV : mail à Nadège
>> Il y a eu un peu de changement cette semaine. MR VEYRAT achète finalement la maison seul ( car il va financer avec la vente d’un bien personnel)
Nous signerons la promesse le mardi 17/11 à 11h .
29.10 rdv PUV : mess tél à NADEGE
22.10 rdv PUV : mail à Nadège
>> On m’a proposé une date qui n’accordait pas mais lorsque j’ai rappelé ce lundi la clerc était en vacances .
14.10 OFFRE ok MANDAT ok FIN 22.11.2026
CI-A ok
💰 attestation de disposition des fonds conseillé à Nadège :
>> Je viens de leur faire acheter leur résidence principale à Riotord 17953 où tout s’est bien passé. Ils sont en train de vendre leur maison: signature de la vente définitive courant novembre .
Ils ne pourront pas verser les 5% car ils auront les fonds que quelques semaines plus tard mais les vendeurs sont au courant' where app_affaire_id = 30741;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 PUV ok VENTE le 14 décembre à 15H.
16.11 Les parties souhaitent signer la vente le 20 décembre. Claire en a fait la demande aux notaires
PUV rédigée, la notaire a anticipé les demandes en mairie afin de pouvoir signer la vente dans le délai.
28.10 PUV fixée 19 novembre à 16h30.
21.10 DOSSIER envoyé aux notaires
Claire me dit que Me Monteiro a tous les éléments, pas de soucis pour le financement, ce serait plutôt une donation de la SCI, les parents viennent en fin de semaine à Issoire. Tous veulent signer avant Noël
20.10 relance Elodie att. dispo des FONDS ? Financement par SCI des ses parents qui prêtent l''argent. Le notaire a déjà le justificatif.
Recherche : une SCI ne peut pas consentir de prêt. Financement possible soit par
- distribution de dividende (si bénéfices)
- réduction du capital social qui entraine un remboursement d''une partie de l''apport de l''associé
- remboursement d''un prêt consenti par l''associé à la SCI
14.10 OFFRE manque nom des vendeurs et mess à Elodie pk 275K meuble ?
> Claire a mis du blanc sur l''offre pour enlever "meuble" après le prix
>> rpse à Claire : le blanc après signature risque d''invalider l''offre (refaire signer avec une condition que le prix comprend les meubles listés en annexe ou à lister pour le cpmis)
>>> Claire : "Il y aura une liste de mobilier ventilée mais la mention n''a pas à être nommée dans l''offre sinon garde l''ancienne offre"
CI-ok
💰 Attestation bancaire de disposition des fonds demandée à Elodie + Claire' where app_affaire_id = 30744;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 24.11 VENTE signée. Attestation pj.
06.11 VENTE mardi 24 novembre à 15h30
06.11 ODP pj. Manue l''envoie au notaire et demande un rdv de VENTE.
04.11 FISE pj. en attente ODP
29.10 PROPO CA du 21 oct. pj.
16.10 PUV ok
30.09 PUV jeudi 15 octobre 2026 à 15h30.
29.09 RDV en attente règlement de copro demandé à l''étude Zilic
25.09 OFFRE ok CI ok' where app_affaire_id = 30746;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 19.11 ADP : eu Alice, Mme Gissinger rappelle M. Bakri car a pris rdv mercredi prochain avec 2 artisans pour les 2 derniers devis pour le PTZ. M. Bakri n''habite pas dans les lieux et c''est le voisin qui a la clé. Si M. Bakri refuse, Alice l''appellera et si tjrs réticent, on fera un mail.
19.11 ADP : mess tél à Alice suite à son mail ci-dessous :
"J''ai échangé hier avec Mme Gissinger qui a eu 2 refus de prêt sur sa demande initiale mais la banque lui conseille de faire une demande de prêt à taux 0 avec l''aide de l''Anah pour que ça passe éventuellement, pour cela elle a besoin de retourner mercredi prochain pour des devis et Mr Bakri refuse cela.
Elle va essayer de voir avec lui à nouveau et contacter le notaire pour avoir son avis. Qu''en penses-tu ? 
Mr Bakri ne peut pas refuser tant qu''il n''a pas les refus de prêt ? Comme Mme Gissinger veut vraiment cette maison elle veut tenter cette proposition, après ça me parait bizarre car les travaux seront chiffrés en plus de la vente mais peut-être en y intégrant le taux à 0%, cela ferait baisser le coût de l''emprunt ?
J''attends son retour et je te tiens au courant mais ça risque de capoter.
16.11 ADP demandée à Alice
15.10 PUV ok
p16 🅿100K 25a 4% < 15 décembre
******
08.10 Nous signerons le compromis le 15 octobre à 11h pour laisser Mme Gissinger prendre le temps à la relecture étant donné qu''elle a pris seulement connaissance de certains documents, travaux etc....le projet lui a seulement été envoyé hier soir.
Elle est ok mais veut juste refaire le point avec ses parents 🤞
Elle a demandé si la direction était ok pour la négociation de la com, je lui ai dit qu''effectivement nous avions baissé par 2 fois, elle n''a rien dit.😅
Elle reste bien motivée, en espérant qu''elle ne change pas d''avis, rien n''est signé ! je reste optimiste 😁
06.10 PROJET transmis au notaire vend.
02.10 CPMIS 13 octobre à 15h30
30.09 CPMIS jeudi 8 octobre à 14h sous réserve de confirmation du notaire.
28.09 rdv CPMIS : notaires relancés ce jour par Alice.
Mme Gissinger a essayé de négocier à nouveau les honos directement auprès de Franck par l''intermédiaire de Daniel Mourlevat. Franck a déjà accordé -500€ au moment de l''offre. Ne bougera plus. Alice en informera Mme Gissinger
congés Alice 17 au 27 sept.
09.09 Alice "j''ai eu le notaire du vendeur qui me dit que c''est Sauret qui a la plume, donc dès que J''ai Mme Del Barco je lui demande une date en sachant qu''apparemment elle vient juste de prendre le dossier en main. De toute façon, ça ne se fera pas avant fin septembre, début octobre à la demande de Mr Bakri.
08.09 relance des notaires par Alice par mail. Demande faite à Alice de les appeler ou de faire appeler son vendeur
02.09 CI ok
01.09 rdv CPMIS + CI-V redemandés à Alice
CI ok, liste de mobilier adressée au notaire par le vendeur directement.
24.08 OFFRE ok
21.08 OFFRE acceptée par mail mais en attente de contresignature
MDR car pas de MDV
PRET + apport 50% (autoentrepreneur)
CPMIS fin sept. début oct. à la demande du vendeur.' where app_affaire_id = 30747;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 24.11 VENTE 17 décembre à 15H30.
24.11 ODP + rdv VENTE demandé au notaire par Claire :
"J''ai eu Antoine le Courtier, les ODP sont éditées ce vendredi Sachant que les agendas sont plein sur décembre, pensez vous que nous puissions bloquer une date de signature entre le 15/12 et le 20/12 s''il vous plaît?
16.11 Plomb bien transmis au notaire + acq. + PRET déposé en banque par Antoine ? >> "tout est ok , les ODP arrivent sous 10 jours pour réitérer  vers le 15/12"
20.10 rdv PLOMB ? >> "oui aujourd''hui ils viennent!"
19.10 CPMIS signé
p10 🅿128K 25a 3.75% < 16 DEC.
p18 diag. Plomb à actualiser
*****
13.10 rdv Cpmis confirmé ? mess. tél à Claire
08.10 Cpmis 16 oct. 15h30 à conf. Mme Duvert
07.10 Cpmis 22 ou 23 oct. 16h. En attente conf. Mme Duvert curatrice de M. Chabaud. 
clerc : "En fait, Monsieur Serge CHABAUD est soumis au régime de la curatelle renforcée. Il signe donc la procuration avec l’assistance de l’ATNA
Et comme il donne pouvoir à un clerc de l’étude, l’ATNA n’est pas obligée d’assister au rendez-vous mais ils peuvent effectivement demander à être présents.
J’ai envoyé un courriel à Madame DUVERT
Je vous tiens au courant de son retour"
06.10 Claire en VV : me rappelle
24.09 Me Bougon en attente de :
- PLOMB à actualiser, 
- TP à récupérer auprès de Me Coulaud. 
- PROC de Serge à faire signer par la tutelle. 
- PROC de Marie certifiée en mairie.
22.09 DOSSIER envoyé à Me Bougon ce jour.
21.09 Claire retire le dossier à Me Lesturgeon et l''envoie à Me Bougon cette semaine
17.09 Claire a laissé un ultimatum à la notaire pour obtenir une date d''ici fin de semaine, sinon changera de notaire
congés Claire 11 au 15 sept.
07.09 Claire j''ai la notaire vendredi soir qui ne répondait pas à mon email et elle m''a dit que nous allions avoir une date de fixée cette semaine.
01.09 relance notaire par Claire
24.08 en attente rdv avec le mandataire pour signer la proc. Il est revenu auj. de congés, la clerc le contacte;
10.08 rdv PUV ? "malheureusement toujours pas de news a la suite de mon dernier email a la notaire. je vais relancer, au final je me demande si on devrait pas changer de notaire ....
Ps: la tutelle est en congés jusqu''au 23 août."
- congés Claire 5-6-7 août -
31.07 mail de Claire à l''étude: peux tu me dire où nous en sommes précisément et si une date de signature pour la promesse peut être envisagée fin août ? ( Mme DUVERT étant absente du 4 au 24 août )
30.07 mail à Claire pour savoir si elle a eu des nouvelles du dossier
23.07 RPSE de l''ass: Bonjour Mme RIBBES 
Je tiens par ce mail à rétablir les faits dans ce dossier 
J''ai informé l''étude notarial le 10 juillet dernier que Mr CHABAUD ne pouvait se rendre au rdv. J''ai immédiatement envoyé les pouvoirs de signature de mon chef de service afin que ces derniers puissent établir une délégation de signature. Je les ai également informés que ma collègue se rendait au domicile de Mr CHABAUD ce début de semaine et que s''ils souhaitaient une signature rapide nous aurions besoin de la délégation pour cette date. Je leur ai également rappelé que Mr CHABAUD étant en mesure de curatelle, donc sous un régime d''assistance, son absence impliquait la notre de fait.
Ils m''ont répondu le 17 juillet dernier ne pas pouvoir me fournir les délégations de signature à temps pour la visite de ma collègue au domicile de Mr CHABAUD 
Je précise qu''aucune demande de jugement ne nous a été faite, dans le cas contraire nous aurions fourni les éléments demandés bien entendu.
Nous nous sommes montrés plus que diligents dans ce dossier 
Si la signature ne peut se faire rapidement cela n''est en aucun cas à cause de notre structure qui ne bloque aucunement l''avancement du dossier comme vous le laissez entendre.
Je vous mets les échanges que j''ai eu qui vous prouverons notre bonne foi dans ce dossier 
Je joins également le jugement qui semble faire défaut dans ce dossier
23.07 mail de Claire: 
Dans le cadre du dossier pré cité pour lequel nous avons un acquéreur en attente pour la vente de la propriété en indivision de la famille CHABAUD, le notaire m''informe ne pas pouvoir avancer sur le dossier pour plusieurs points:
- elle n''a toujours pas reçu de votre part le jugement de Monsieur Chabaud Serge qui lui permet de rédiger la procuration pour Mr Serge que vous devez lui faire signer, pourriez vous lui transmettre s''il vous plaît à l''adresse suivante: laetitia.chassard.63038@notaires.fr
- nous attendons vos disponibilités pour fixer une date de signature de promesse d''achat, vous pouvez vous rapprocher de l''étude de Maître Lesturgeon Blanchard ou sur le même email de Mme Chassard.

Les consorts Chabaud vendent la propriété de famille afin de payer l''EHPAD de la maman, malheureusement il y a caractère assez urgent.
Nous sommes conscients de l''énorme travail de chacun et disponibilités mais si le notaire ne peut pas avancer cela risque de remettre en question l''acquisition par notre acquéreur et mettre en difficulté la famille.
21.07 mail à Claire pour savoir si elle a eu des nouvelles 
15.07 je viens de relancer et on attend le retour de la tutelle et de ses dispos ....
C''est une catastrophe!!!!
Je vais avoir un retour sous 48H 
13.07 rdv fixé ?
- congés Claire du 6 au 12 juillet -
01.07 DOSSIER envoyé au notaire
CI-A ok
29.06 DOSSIER pas encore envoyé, Claire s''en occupe et met la CI de l''acq.
22.06 OFFRE + MANDAT ok.
Antoine est en copie car s''occupe du financement acquéreur.
Envoi du DOSSIER demain à Me Bougon
CI-A demandée à Claire
15.06 relance Claire : "As-tu des nouvelles de la signature du mandat et de l''offre par la curatrice et son protégé stp ?"
>> Relance faite ce jour à Mme Duvert, curatrice h.duvert@atna-asso.fr
01.06  Ce sera un peu long car la curatrice ne peut pas se déplacer rapidement pour faire signer M. Chabaud.
27.05 OFFRE en attente signature M. Serge Chabaud et sa curatrice (ok oralement).
CI-A en attente' where app_affaire_id = 30754;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 VENTE 30 Novembre. 
28.10 Il n''y a pas de droit de préemption à purger mais Me Pailhès n''a pas voulu fixer de rdv le jour du compromis. On attend donc qu''il veuille bien fixer un rdv pour la vente.
16.10 copie PUV demandée à Lucile
05.10 PUV fixée 15 oct.
29.09 rdv PUV ?
>>"Non toujours pas !!! Il manquait l''amiante je le fait faire demain matin 
Je te tiens informée"
congé Lucile 21 au 27 sept.
16.09 DOSSIER pas encore envoyé car l''acq veut attendre d''avoir vu son notaire, il est séparé mais pas divorcé et remploi des fonds propres. Il appelle Lucile demain après son rdv notaire et elle fera partir le dossier à la suite.
09.09 CI ok
07.09 OFFRE ok
CI en attente :  je le vois mercredi il doit venir avec ses documents.' where app_affaire_id = 30755;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 19.11 PUV ok sans condition
18.11 PUV copie demandée à Claire
17.11 VENTE rdv fixé au cpmis :  "Nous sommes en cours de signature, la date de réitération est prévue le mercredi 20/01 à 11h. Mme Ottavi sera sous procuration .
Pour info , je serai en congés en Thailande, Elodie s''occupera des relevés et présence chez notaires."
29.10 DOSSIER transmis ce jour.
21.10 PUV fixée 17 NOVEMBRE A 10 h en votre étude. 
20.10 OFFRE ok cdt autorisation copro clim
CI-A ok
Achat comptant suite à la vente de leur maison (réitération déjà passée)
Attestation bancaire de disposition des fonds conseillée à Elodie' where app_affaire_id = 30756;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 ADP demandée à Arnaud
21.09 PUV lundi 19 octobre. TAE ok
p18 🅿 245535 4% 20a < 18 JANV.
11.09 manque contrôle TAE
09.09 OFFRE ok
CI ok en attente de rdv' where app_affaire_id = 30757;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 24.11 PUV ok
p14 (V) Retrait cuve de gaz
02.11 PUV mardi 24 novembre à 11h chez Caroline BARRE
21.10 OFFRE ok
CI ok
Attestation bancaire de disposition des fonds conseillé à Christèle' where app_affaire_id = 30759;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 26.11 PUV ok
p16 🅿218K 20a 3% < 25 JANV.27
25.11 PUV copie demandée à Simon
03.11 PUV 23 Novembre à 16h chez Maitre CHALET
30.10 CNI ok Noms notaires + envoi demandé à Simon
23.10 OFFRE ok
"Notaires à définir.  Les cartes d''identités arrivent."' where app_affaire_id = 30763;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 PUV avancée au 25 novembre
05.11 PUV fixée vendredi 4 décembre
03.11 Notaire-A + envoi DOSSIER redemandé à Lucile ?
>> " leur notaire est Maitre Cyrille Prebost à Cremieu. 
Il on reçu le dossier que je leur ai transmis mais ne m''on pas encore proposer de date de signature de promesse."
28.10 Lucile en arrêt jusqu''au 30 nov. mais s''occupe des ses dossiers.
Notaire Acq. à Lyon, elle envoie le dossier demain et me donnera son nom car ne l''a pas sous la main.
23.10 OFFRE ok mais nom vendeur pas repris en haut
! MANDAT expiré depuis le 1er octobre.
CI-ok' where app_affaire_id = 30764;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 VENTE 11 décembre à 18h Me Goutorbe
ODP ok ? Oui, ils ont reçu leur offre.
Dossier rapide car seulement 2 visites et pas gagné... car juste au-dessus de la double voie à St Just Malmont...
Transmise directement au notaire même si j''avais ddé une copie...
A priori tout est ok. Date de vente bien confirmée.
**** 23.10 PUV ok
p12 🅿 266K 25a 4.10% < 23 DEC.
p25 fact. entretien cuve fuel
****
30.09 PUV 23oct. à 9h chez Me Goutorbe . Un seul notaire.
28.09 rdv PUV Nico a relancé Me Goutorbe, il demande à M. Crapanne de la relancer aussi car pas de réponse.
25.09 CI ok 
Les deux parties prennent Maître Goutorbe. Relancé deux fois pour la date... encore aujourd''hui. Je te communique la date dès confirmation.
22.09 OFFRE ok
CI-A et notaires en attente' where app_affaire_id = 30765;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 17.11 VENTE reportée car refus CA alors que validé en amont par la conseillère mais changement de Directeur et endettement trop haut.
l''acq redépose au CM.
23.10 PUV ok Vente fixée 2 décembre 14h
p13 ODP avant 20 déc.
p38 entretien chaudière
22.10 copie PUV pas encore reçue. Marion relance demain.
29.09 PUV fixée mercredi 21 octobre à 14H en acte à distance (les vendeurs chez nous, et les acquéreurs chez leur notaire).
24.09 OFFRE ok
CI ok
Notaire A : Me Sauret (Del Barco)' where app_affaire_id = 30766;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 CPMIS ok
p6 🅿100K 25a 3.75% dépôt < 20DEC - ODP< 20JANV.
05.11 CPMIS 20 novembre à 11h chez Maître Tessier
29.10 SIMUL Vousfinancer ok pj.
rappel CI OK
26.10 OFFRE ok 🅿
CI + notaires + simul en attente' where app_affaire_id = 30768;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 ADP demandée à Corinne.
>> "Mon client envoie sa courtière ce soir pour valider son prêt."
26.10 PUV ok
SIMUL x 🅿85K 25a 4.2% < 31DEC.
14.10 OFFRE ok
CI ok
🅿 simul demandée à Corinne > RDV courtier 20 oct.
"Pour répondre à ta demande, je n''ai pas encore la simulation bancaire.
Sache toutefois que le client avait déjà consulté cette banque par le passé. Je connais très bien cette personne et sa famille, il n''y aura donc aucun souci de financement. Je l''ai d''ailleurs dirigé vers un courtier qui le reçoit en rendez-vous le 20 octobre prochain."' where app_affaire_id = 30770;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 18.11 VENTE  11 décembre à 17h
14.10 CPMIS fixé 23 octobre à 14H30. Le compromis est fixé le 23 octobre à 16 h et non 14H30
12.10 rdv CPMIS :
"Je viens d''avoir Julie Barbier pour le compromis de vente Goguely, elle m''a transmis 3 créneaux à demander au notaire acquéreur, et ce parce que je l''ai appelé ce matin afin de la presser depuis le 4 septembre envoi des documents.
Elle n''a toujours pas travaillé dessus alors qu''elle a tous les éléments puisque c''est elle qui avait fait la vente, elle s''est plainte de trop de travail, de problèmes informatiques etc.... et que je la pressais et comprenais pas, bref du coup elle m''a donné 3 dates possibles, j''ai envoyé l''info au notaire des acquéreurs en attente de son retour pour fixer une date semaine prochaine."
08.10 rdv CPMIS : relance Me Sauret par Alice
"Mr Goguely me dit qu''il n''a toujours pas reçu la procuration pour le compromis de vente et n''arrive pas à vous joindre par téléphone.
Nous sommes dans l''attente d''une date de compromis de vente en sachant que les documents ont été envoyés le 4 septembre ?
Merci de nous tenir informés du suivi du dossier car les clients s''impatientent."
06.10 rdv CPMIS : relance Me Sauret
29.09 rdv CPMIS : Me Huck vient juste d''attribuer un clerc au dossier et demander le projet à Me Sauret.
28.09 rdv CPMIS : Alice relance les notaires
congés Alice 17 au 27 sept.
03.09 Dossier envoyé aux notaires
CI ok
02.09 Prêt bancaire
Manque notaire vendeur' where app_affaire_id = 30771;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 24.11 ADP demandée à Nico
28.10 PUV ok
p14 🅿224300€ 25a 4% < 05 JANV.
****
27.10 copie demandée à Nico
>> "J’ai relancé, il a dû oublier. Dès réception je te transmets."
21.10 La promesse de vente pour Colombet VanHaelen est fixée au 26OCT à 10h chez Maître Barbier.
20.10 rdv PUV
>> La date du compromis n’est pas encore fixée... Notaires relancés hier par e-mail et ce matin par téléphone pr celle du Var qui n’a pas répondu aux propositions de Maître Barbier... Je te la confirme rapidement. A priori le 26/10 ?…
15.10 rdv PUV finalement pas encore fixé. 
Nico "Concernant ce dossier, j''avais fait un p''tit raccourci car pas eu toutes les  infos complètes:  l''acte devait être rédigé cette fin de semaine et que la promesse serait possible à compter du 19/10. D''ici ce soir, l''acte de la promesse sera rédigé, en famille, demain la procuration (au notaire) sera signée côté vendeur car ils partent (fille et gendre qui s''occupe du dossier pour la maman) au Japon 3 semaines...
Entre temps la promesse de vente sera fixée (date sera validée, les notaires voulaient faire ds cet ordre... pas compris pourquoi on ne peut pas bloquer une date auparavant... ). La notaire aura l''autorisation de faire qq modifs si besoin au dernier moment pdt la promesse.
Concernant le décès de M Colombet début octobre : succession uniquement pour son épouse et sa fille. La notaire (vendeur) organisera la succession pdt le délai de la promesse, peut être 
qu''il sera porté à 4 mois si besoin. Acquéreurs informés.
13.10 RDV pas encore confirmé. Nico a appelé déjà hier les notaires, il rappelle les acq. M. DECES de Jean-Marie Colombet. Sa fille Chantal et ses petits-enfants Philippe Gambarini et Christian Warner avaient une habilitation familiale donc ok pour vendre. Son épouse Philippine n''a pas souhaité être co-habilitée du fait de son âge 87ans.
AUTRES ENFANTS ?

06.10 rdv CPMIS demandé à Nico
>> On va avoir la confirmation de la date rapidement, parce qu’il attendait avec l’accord des vendeurs la finalisation de leur budget travaux. Ils s’étaient positionnés rapidement.
A priori le lundi 19/10 mais à confirmer.
28.09 Nico a tout envoyé aux notaires 
25.09 CI ok
24.09 OFFRE ok
CI en attente
MANDAT Philippine sous habilitation familiale' where app_affaire_id = 30779;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 19.11 VENTE : le report serait maintenu au 4 car le notaire n''aurait pas purgé la SRU des enfants qui voulaient intervenir à la vente puis ont renoncé, ne sont ni sur l''offre, ni sur le compromis. Alice appelle le notaire pour comprendre car Mme Connan veut vraiment signer le 27.
Alice a eu l''étude du notaire acq. qui lui a dit que c''était Mme Connan qui voulait reporté ce qui est faux, elle a fait un mail à la clerc en le lui indiquant. La clerc de Sauret l''a rappelée en lui disant que les enfants ont fait jouer la clause de substitution et qu''elle n''a pas envoyé la SRU et que de ce fait on ne peut pas signer avant le 4. Elle n''a certainement pas voulu assumer son erreur devant le notaire acquéreur et lui a dit que c''était la vendeuse qui ne voulait pas signer avant le 4.
18.11 VENTE à confirmer car mail d''Alice à Sauret : "Je viens d''avoir Mme CONNAN pour l''informer du changement de date, elle n''est pas du tout contente ni d''accord de changer de date car elle s''est déjà organisée, elle est à 500 km et a déjà prévenu l''assurance pour stopper au 27 novembre l''assurance de la maison.
Elle va vous appeler directement pour voir tout cela avec vous.
De mon côté je reste dans l''attente d''une date convenue avec tous pour pouvoir convenir d''un rdv avec Mr et Mme Cornet et Mme Connan pour le relevé des compteurs et l''état des lieux.
18.11 VENTE reportée 4 décembre à 15H30.
29.10 PUV ok VENTE fixée 27 novembre à 16h.
13.10 RDV PUV  29 octobre à 14H30
08.10 RENEGO :
Un prix net venderesse de 121 150 € 
Des honoraires agence à la charge vendeur de 8850 € soit 
Un prix de 130 000€ frais d''agence inclus.
06.10 DECISION ACQ ? : M. Cornet devait tenir informé son notaire. Alice n''a pas de retour, elle le relance.
01.10 Nv rapport SPANC pj. NON CONFORME. Mail d''Alice aux notaires :
"Mme Connan a fait repasser le spanc pour un nouveau contrôle de la fosse septique qui n''est pas conforme car les eaux prétraitées sont rejetées en sous-sol.
Je vous transmets le rapport non signé car pour cela il faut encore attendre 3 semaines.
Je l''ai adressé à une société dont les coordonnées m''ont été données par M° Sauret afin d''avoir un devis sur les travaux à réaliser pour la remettre en conformité. Ils ne peuvent pas faire de devis sur simple rapport, il faut pour cela faire une demande au préalable au spanc d''une déclaration d''installation, et en fonction de ce qu''ils préconisent le coût peut varier entre 5000 et 15000 euros en fonction des travaux et de ce que veulent les acquéreurs.
Cette déclaration serait à demander par les acquéreurs car cela est à leur demande et a un coût de 200 €.
Pour information, Mme Connan vend en l''état et a déjà négocié le prix avec Mr et Mme Cornet, elle ne souhaite pas négocier à nouveau. J''en ai déjà informé Mme Cornet que j''ai eu au téléphone et qui doit vous contacter.
Merci de nous tenir au courant de la suite à donner."
28.09 Rapport SPANC mercredi directement au notaire : Mme CONAN a refait passer le SPANC car le technicien n''a pas vue l''aération lors de la réactualisation alors que le 1er rapport était conforme et l''aération présente.
21.09 DEVIS ANC Mme Conan a fait vidanger la fosse mais Sandrine ne s''est pas occupée du devis pour la mise aux normes de la fosse. Elle n''a pas le rapport Spanc. Je lui ai dit de se rapprocher de Me Sauret et de l''envoyer à l''ent. DUMEIL TP.
10.09 cpmis pas signé car les acq. demandent un devis pour la mise aux normes de l''ANC alors qu''ils avaient toutes infos en amont, l''ANC date de 2022, il manque seulement un chapeau et le technicien n''a pas vu l''épandage le jour de la visite donc ressort non conforme. Ils n''achèteront pas si le montant dépasse 5000€. Alice a contacté l''ent. Dumeil.
Cette condition n''a pas pu être ajoutée lors du rdv car Mme Connan avait donné procuration. 
29.08 rdv cpmis :
AR > Du coup Mme Connan ne sera pas là et les acquéreurs qui pouvaient ne seront plus disponibles avant le 26 septembre.
DB >> Et une proc ?
AR >>> Finalement elle va demander une procuration. On maintient le rdv
28.08 relance Alice rpse Sauret ?
>>  le 10 septembre 
- Alice abste 20 au 25 août -
19.08 Me Sauret relancé par Alice mais en congés.
10.08 rdv PUV ? Alice a relancé auj. par mail les notaires
05.08 OFFRE complétée envoyée à l''acq. 
DOSSIER envoyé notaires ce jour
04.08 OFFRE manque charge honos. Mail à Alice pour qu''elle l''ajoute et envoie une copie aux parties en précisant la modif apportée.' where app_affaire_id = 30780;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 CPMIS ok
p5 entretien chaudière
p9 (A) dépôt DP < 30NOV. non opp. DP changement fenêtres conformes ABF < 31JANV.
p9 🅿110K 20a 3.9% <31JANV.
p18 actualisation PLOMB exp. 21.12.2026
*****
19.11 CPMIS copie demandée à Elodie
18.11 CPMIS copie demandée à Claire
05.11 CPMIS 17 novembre à 11h30 chez Maître Bougon
30.10 OFFRE ok
CI ok
SIMUL ok
DOSSIER envoyé aux notaires' where app_affaire_id = 30784;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 ADP demandée à Sandrine
02.11 PUV ok
p11 🅿120K 20 4.2% < 8 janv.
19.10 PUV reporté au 30 oct. p/r dispos acq.
05.10 Sauret a tout, Mme Durand et Sandrine sont passé à l''étude
30.09 PUV fixée 16 oct. pm. sous réserve TP
28.09 Alice demande l''attestation immobilière au décès de Serge Durand pour vérifier qu''il n''y a pas d''héritier.
23.09 OFFRE ok CI ok
MANDAT Alice : Mme a acheté mariée en communauté avec M. Serge Durand mais Sandrine ne sait pas si les enfants sont ceux de M. Durand ou ceux de M. Averty mari prédécédé.' where app_affaire_id = 30789;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 17.11 DP déposée ce jour. Récépissé pj.
PRET déposé ? >> Marion : "Oui il a rdv dans 15 jours je crois (il me la dit hier au tel mais je ne me souviens plus de la date)"
03.11 PUV ok
p14 DP agrandissement entre les 2 chalets dépôt <16DEC (ABF) accord<31JANV.
p15 🅿164K 25a 4% <05JANV
****
02.10 PUV 02nov. à 15H30 (signature de Mme Barone)
Signature M. HUYNH par proc. : "Je vous confirme que je vais recevoir mon client le 22.10 à 10H pour la signature d’une procuration"
23.09 rdv PUV ? notaires relancés
18.09 OFFRE ok 
*PC pour agrandissement entre les 2 chalets
CI ok' where app_affaire_id = 30791;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 compromis le vendredi 27 novembre à 10h chez Sauret à Cunlhat
19.11 PUA rdv : relance Christine par mail
18.11 PUA rdv demandé à Christine sur mess. tél.
12.11 Christine a bien reçu l''attestation de solde du CA + épargne Bfor banque. (env.300K) Le dossier a été envoyé à Me Sauret, elle lui précise de signer une PUA pour obtenir l''accord du juge (en congé mat)
05.11 OFFRE ok Roger étant sous HABILITATION familiale de Michel
CI-A ok
💰 attestation bq disposition des fonds conseillée à Christine' where app_affaire_id = 30796;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 Ci joint le passeport de l''acquéreur la date de signature de promesse est demain le 24 Novembre. 
19.11 CI-A + PUV demandés à Lucile
09.11 PUV en attente visite avec artisans
05.11 OFFRE ok
CI-A + SIMUL en attente' where app_affaire_id = 30797;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 17.11 VENTE mercredi 16 décembre à 16H30.
05.11 PUV ok
ACHAT en usufruit pour Mme M. Gutierrez et en nue-propriété pour leur fils Charlélie.
rdv VENTE : pour fin d''année car paiement de la SAFER
****
22.10 PUV mercredi 4 novembre à 17 H
21.10 DECISION ACQ ACHETENT TJRS ?  oui oui jai relancé les 2 notaires mardi ;) ca va etre sympa de caler une date rapidement de nouveau tiens ....
14.10 PUV reportée : giraud-viallet.vienne@notaires.fr "Cher Maître, Je viens d’échanger à l’instant avec l’acquéreur concernant la création de la cave et de l’atelier, compte tenu de l’absence d’autorisation, il souhaite se renseigner avant de s’engager.
Il demande donc le report du rendez-vous de demain.
Il va se rapprocher de la mairie et revient vers moi dés qu’il aura obtenu des informations.
J’adresse ce mail en copie à l’agence,
22.09 PUV mercredi 14 octobre à 9H30
14.09 Marion relance notaires auj. pour date promesse RELANGE / GUTTIEREZ
03.09 OFFRE ok
 DOSSIER parti à l''instant chez Maître Exbrayat et Maitre Giraud Viallet à Vienne
31.08 OFFRE en attente signature Mme Bonin, envoyée par courrier le 26 août.
SCI à créer 
CI ok' where app_affaire_id = 30798;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 23.11 PUV lundi 7 décembre a 17h.
19.11 PUV en attente diag TAE, alors que la maison a été construite en 2020 et raccordé en réseaux séparatifs conformes... Le Diag passe lundi. Stéph devrait avoir un rdv sous peu pour la PUV.
13.11 PUV rdv demandé à Stéph. >>rpse "J''ai relancé ce matin"
06.11 OFFRE ok 🅿🏠vente apt. cpmis signé ? 
>> Il passe la vente le 19 novembre Cpmis signé 3pages pj. 40K
CI-A ok' where app_affaire_id = 30804;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] Arrêt Lucile > 25NOV. inclu
23.11 ANNULATION : Mme Poliakova se rétracte. Conf. écrite demandée à Lucile avant remise en pub. OK
18.11 nom du notaire vendeur + rdv CPMIS demandés à Lucile
09.11 OFFRE ok
CI-A ok Ukrainiens
Lucile demande une vente directe
Attestation bancaire de disponibilité des fonds conseillée à Lucile' where app_affaire_id = 30806;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 19.11CI ok PUV 30 novembre
17.11 CI-A + rdv PUV demandés à Nico mess. tél.
10.11 OFFRE ok
CI-A en attente' where app_affaire_id = 30808;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 25.11 PUV copie relance Arnaud
23.11 PUV copie demandée à Arnaud
12.11 OFFRE ok CI ok
la promesse devrait être signée le vendredi 20/11 chez Me Didier.
Me Josserand représente les acquéreurs.' where app_affaire_id = 30815;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 20.11 ANNULATION offre pj. MANDAT expire 21.11.2026 Demande à Nico de signer un nouveau mandat.
12.11 OFFRE ok 💰pc
CI ok' where app_affaire_id = 30816;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 18.11 PUV mardi 24 novembre 15h
12.11 OFFRE ok 💰
M.DAUBORD Rémi 0684953424 remsdaubs@hotmail.com 
CI ok' where app_affaire_id = 30817;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 24.11 ancien EDD récupéré ?
13.11 CPMIS reporté : Me Bougon s''est aperçu qu''un EDD avait déjà été fait sur la maison d''à côté, il devrait donc y avoir un lot qui appartient à la maison qu''on vend. Le géomètre ne s''en était pas aperçu visiblement. Il faut donc récupérer l''EDD qui est à l''étude Coulaud pour voir ce qu''il en est. Signature en janvier d''après Claire car plusieurs secrétaires et clerc ont démissionné et n''ont pas été remplacées.
05.11 compromis 13 novembre 17H15
04.11 rdv CPMIS demandé par Claire : "Je reviens vers vous dans le cadre du dossier pré-cité, après l''avoir eu au téléphone hier, le géomètre m''envoie le projet lundi prochain 🥳.
Notre acquéreur qui bénéficie d''un PTZ dans son crédit, souhaiterait pouvoir signer avec le 15/11 afin de bénéficier des délais que l''état nous impose pour le dépôt des dossiers PTZ (avant le 16/11 sinon réouverture au 10/01😞).
Pensez vous avoir un petit créneau à nous communiquer s''il vous plaît 🥳🙏.
Votre horaire sera le nôtre bien évidemment.
30.10 CI ok DOSSIER envoyé à Me Bougon (sans EDD)
21.10 Géomètre passé hier pour EDD.
21.10 Avocat ne veut pas lever l''hypothèque sur le 18821, il y aurait plusieurs biens mais la notaire n''arrive pas à obtenir la liste, il faudrait que M. Guillouet la demande à son avocat et nous la transmette.
Claire a un rdv visio cet après-midi avec le vendeur.
Claire va envoyer ce dossier pour appuyer la demande de lever.
13.10 relance Claire : elle n''a pas encore envoyé le dossier, elle attend l''autorisation de vendre de l''avocat de la banque pour SCI VP avant d''envoyer celui-ci.
RDV EDD pris
06.10 Claire en VV : me rappelle
24.09 Claire prend rdv pour l''EDD
MONTANT DE LA DETTE ? 
>> "oui il nous a tout envoyé pour la dette... elle est colossale... bon je sais qu''il a un autre appart à Clermont quil faut qUil vende..."
21.09 EDD : Claire remet demain le prix de l''estimation à la voisine, elle pense qu''elle voudra vendre plus cher donc, EDD sera nécessaire. Il sera à la charge de M. Guillouet.
M. Guillouet a un fait un dossier de surendettement mais d''après Claire, il a les moyens de payer l''EDD.
PRET (ANTOINE) : remboursement prêt auto nécessaire et validation PTZ au nom que de Mme car M. ne peut pas emprunter (offre au nom de Madame)
- congés Claire 11 au 15 sept.-
09.09 Propriété voisine imbriquée dans celle qu''on vend. RDV vendredi 18 avec la voisine pour estimation pour un éventuel achat par les acq. sinon EDD nécessaire. La voisine n''est à ce jour pas vendeuse.
31.08 OFFRE ok
CI-A en attente
CHARGE ACQ : SURENDETTEMENT vendeur. MISE AUX ENCHERE prévue mars 2027 si pas de vente amiable. Montant de la dette demandée à Claire.' where app_affaire_id = 1000320;
update public.app_affaire_note set texte = texte || E'\n\n' || '[classeur G, relu le 26/11/2026] 18.11 VENTE 24 Novembre à 16H 
16.11 DIVISION docs pj. et transmis au notaire par Stéph. avec demande de rdv VENTE
10.11 DIVISION : Stéphanie appelle le géomètre sté JULIEN pour savoir s''il peut relancer le cadastre car jeudi dernier le vendeur n''avait tjrs rien.
22.10 point DIVISION ? Document modificatif signé et renvoyé au géomètre fin de semaine dernière pour envoi au cadastre.
16.10 ODP CA ok 14 oct. pj.
DIVISION PARCELLAIRE effectuée ?
12.10 ADP CA ok le 10 oct. pj.
09.10 ADP demandée à Stéphanie
>> Je viens d''avoir M. Drouet au téléphone. Il m''a indiqué que l''offre de prêt devrait être émise d''ici la semaine prochaine.
31.08 CPMIS ok
p5 Division à effectuer
25.08 rdv cpmis fixé ?
>> "J’attends le retour du notaire pour samedi 29 Août  à 10h"
19.08 OFFRE ok manque juste la commune du bien, Stéph. avertie
CI ok' where app_affaire_id = 1000321;
-- 5. LES AVIS (31 cases, 17 lignes neuves)
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('0b25afef', 'classeur', 'classeur:3bis:2026-11-27', 'f7756aad-5084-4e6e-a7f5-d2dcbc22b634'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('14fdb07f', 'classeur', 'classeur:3bis:2026-11-27', '2c76b658-123f-42ca-886a-cd8f52d6c5aa'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('1d3bc808', 'classeur', 'classeur:3bis:2026-11-27', 'a164cb26-0469-46d9-b0f8-e142e3f17074'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('35996b7e', 'classeur', 'classeur:3bis:2026-11-27', '1879ffb3-d6f4-462b-995d-9168e89ef1ff'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('4d354b1a', 'classeur', 'classeur:3bis:2026-11-27', 'd22075a4-24f9-4fce-abf7-0d881c905fd4'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('606bb180', 'classeur', 'classeur:3bis:2026-11-27', '4a7a302f-0045-4d3b-87fe-2754f7cc1bd8'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('6d4d0aee', 'classeur', 'classeur:3bis:2026-11-27', '281cbd52-7ebd-4304-aca3-3a27670c6e2c'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('8bcc3b63', 'classeur', 'classeur:3bis:2026-11-27', '218e5a48-28af-4e6f-a18a-290b4c09599c'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('a10a87c8', 'classeur', 'classeur:3bis:2026-11-27', 'd2c98598-011b-4a71-a5e1-868493951f73'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('a2780e6f', 'classeur', 'classeur:3bis:2026-11-27', '8796c587-a494-4d55-987d-0181ca624b71'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('bfe07c3b', 'classeur', 'classeur:3bis:2026-11-27', '1252a15a-7135-4b05-a0a3-78003356fa52'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('c9fe7ffa', 'classeur', 'classeur:3bis:2026-11-27', '4b4e0faf-0d22-4d85-8449-186e3ea53073'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('db0d5e8d', 'classeur', 'classeur:3bis:2026-11-27', 'e47fbc60-828f-42ae-9737-10dc289bb4a3'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('e2779d8b', 'classeur', 'classeur:3bis:2026-11-27', '00876048-76bc-45e4-9281-b4394cc062bd'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('e2951cb3', 'classeur', 'classeur:3bis:2026-11-27', '32b1a204-ba89-4110-831c-b2f157ce9aec'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('e6b0043e', 'classeur', 'classeur:3bis:2026-11-27', '6fc8fbbd-734e-4b13-9283-6ddc51a830fb'::uuid);
insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values ('f1f51b2c', 'classeur', 'classeur:3bis:2026-11-27', '9ddd907b-8e99-4d93-9223-ff98016c4f71'::uuid);
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '0b25afef';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '14fdb07f';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '1d3bc808';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '35996b7e';
update public.app_classeur_avis set avis_envoye = 'Marion', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '3b5db3cc';
update public.app_classeur_avis set avis_a_envoyer = 'NON vend. et OUI acq.', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '4d354b1a';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '606bb180';
update public.app_classeur_avis set avis_a_envoyer = 'NON vendeurs / Voir Nico pour acq.', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '6d4d0aee';
update public.app_classeur_avis set commentaire_avis = 'NON VENDEURS', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '6d4d0aee';
update public.app_classeur_avis set avis_envoye = 'Marion', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '78bb247a';
update public.app_classeur_avis set avis_a_envoyer = 'NON', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '84c91bb8';
update public.app_classeur_avis set avis_envoye = 'X', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '84c91bb8';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = '8bcc3b63';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'a10a87c8';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'a2780e6f';
update public.app_classeur_avis set avis_envoye = 'ok', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'a56ce827';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'a6d41ca1';
update public.app_classeur_avis set avis_a_envoyer = 'NON', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'a75aef8c';
update public.app_classeur_avis set avis_envoye = 'X', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'a75aef8c';
update public.app_classeur_avis set avis_envoye = 'X', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'afd672fa';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'bfe07c3b';
update public.app_classeur_avis set avis_envoye = 'ok', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'c6c8bc29';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'c9fe7ffa';
update public.app_classeur_avis set avis_envoye = 'ok', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'd9a0630c';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'db0d5e8d';
update public.app_classeur_avis set avis_a_envoyer = 'NON', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'df0ce30c';
update public.app_classeur_avis set avis_envoye = 'X', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'df0ce30c';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'e2779d8b';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'e2951cb3';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'e6b0043e';
update public.app_classeur_avis set avis_a_envoyer = 'oui', ecrit_par = 'classeur:3bis:2026-11-27', ecrit_le = now() where id_unique = 'f1f51b2c';
-- 6. LES CONTROLES
do $$ declare n int; begin
  select count(*) into n from public.app_affaire_note where ecrit_par = 'classeur:3bis:2026-11-27';
  if n <> 47 then raise exception '⛔ controle : % notes neuves (attendu 47)', n; end if;
  select count(*) into n from public.app_affaire_note where texte like '%[classeur G, relu le 26/11/2026]%';
  if n <> 78 then raise exception '⛔ controle : % notes portent le paragraphe (attendu 78)', n; end if;
  select count(*) into n from public.app_affaire_note;
  if n <> 4571 then raise exception '⛔ controle : % notes en tout (attendu 4571)', n; end if;
  select count(*) into n from public.app_affaire_note a join public.app_affaire_note_avant_3bis_20261127 s using (app_affaire_id)
   where left(a.texte, length(s.texte)) <> s.texte;
  if n <> 0 then raise exception '⛔ controle : % note(s) dont le texte d''avant n''est plus intact', n; end if;
  select count(*) into n from public.app_classeur_avis where ecrit_par = 'classeur:3bis:2026-11-27';
  if n <> 27 then raise exception '⛔ controle : % lignes d''avis marquees (attendu 27)', n; end if;
  raise notice '✅ lot 3 bis A : 47 notes neuves, 78 paragraphes, 27 lignes d''avis touchees';
end $$;
commit;
