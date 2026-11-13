-- ============================================================================
-- LE RE-GEL ADDITIF -- lots A, B et C                          13/11/2026
-- ============================================================================
-- Plan : notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md, section 1.7
-- Liste relue par Frederic : notice/REGEL_ADDITIF_A_RELIRE_2026-11-13.csv
-- Sauvegarde : public.app_classeur_lien_avant_regel_20261113
--              12 422 lignes, fidelite verifiee (0 triplet manquant)
--
-- ⛔ CE PATCH REVERIFIE TOUT EN BASE AU MOMENT DE L'ECRITURE. Il ne croit pas
--   la liste figee : entre sa fabrication et son execution, la base bouge.
--   Lecon du menage du coffre (21/10) : 365 fichiers de fiches VIVANTES avaient
--   ete sauves parce que le script reverifiait a la volee au lieu de se fier a
--   une liste preparee la veille.
--
--   A  CORRIGER    9 liens -- le gel se trompe de bien (etage « 1 mandat seul »)
--                            contre-audite depuis le CLASSEUR : pour chacun,
--                            2 noms ET 3 dates au jour exact du cote de v2
--   B  RETIRER     2 liens -- poses sur une ligne DOUBLON du classeur
--   C  AJOUTER   177 liens -- « v2 seul », >= 3 familles, transaction LIBRE
--                            (48 ecartes : transaction deja prise ailleurs)
--
-- POUR REVENIR EN ARRIERE, EN UN GESTE :
--   begin;
--     delete from public.app_classeur_lien;
--     insert into public.app_classeur_lien
--       select * from public.app_classeur_lien_avant_regel_20261113;
--   commit;
begin;

-- ------------------------------------------------------------------- LOT A
create temporary table _a(ligne int, role text, tx_gel bigint, tx_v2 bigint) on commit drop;
insert into _a values
       (3229,'compromis',18062,26254),
       (3229,'offre',18063,26255),
       (3229,'vente',18064,26256),
       (3370,'vente',23087,21634),
       (3370,'compromis',23085,21632),
       (3370,'offre',23086,21633),
       (3390,'compromis',15210,14608),
       (3390,'offre',15211,14609),
       (3390,'vente',15212,14610);

-- Garde-fou : chaque lien a corriger doit exister TEL QU'ATTENDU, et sa cible
-- doit etre libre. Sinon on ne touche a RIEN (la transaction entiere est annulee).
do $gardeA$
declare n int;
begin
  select count(*) into n
    from _a a join public.app_classeur_lien g
      on g.ligne_classeur = a.ligne and g.role = a.role and g.app_affaire_id = a.tx_gel;
  if n <> 9 then
    raise exception 'LOT A : % liens trouves sur 9 attendus -- RIEN FAIT', n;
  end if;
  select count(*) into n
    from _a a where exists (select 1 from public.app_classeur_lien g
                             where g.app_affaire_id = a.tx_v2);
  if n <> 0 then
    raise exception 'LOT A : % transactions cibles DEJA prises -- RIEN FAIT', n;
  end if;
  select count(*) into n
    from _a a join public.app_affaire_ledger l on l.app_affaire_id = a.tx_v2;
  if n <> 9 then
    raise exception 'LOT A : % transactions cibles existent sur 9 -- RIEN FAIT', n;
  end if;
end $gardeA$;

update public.app_classeur_lien g
   set app_affaire_id = a.tx_v2,
       confiance      = 'sûre',
       etage          = 'v2 : 2 noms + 3 dates au jour (corrige le 13/11)',
       gele_le        = now(),
       gele_par       = 'regel additif 13/11 -- lot A'
  from _a a
 where g.ligne_classeur = a.ligne and g.role = a.role and g.app_affaire_id = a.tx_gel;

-- ------------------------------------------------------------------- LOT B
-- Les lignes 3818 et 4100 sont des DOUBLONS du classeur (meme mandat, meme
-- acquereur, meme date d'offre que 1397 et 2346), et le gel les a rattachees a
-- un AUTRE bien que leur jumelle. Le lien ne vaut rien dans les deux lectures.
-- ⚠ Les 4 autres groupes de doublons ne sont PAS touches : 3 n'ont deja aucun
--   lien, et 3887 porte le meme bien que sa jumelle (plausible).
delete from public.app_classeur_lien where ligne_classeur in (3818, 4100);

-- ------------------------------------------------------------------- LOT C
-- ⚠ `preuves` est un SMALLINT (mesure du 13/11), pas un texte : c'est le NOMBRE
--   de preuves. Pour v2 c'est donc le NOMBRE DE FAMILLES de temoins (3 a 6).
--   Mon premier essai y a mis une phrase -> « invalid input syntax for type
--   smallint », et la transaction a tout annule : rien n'avait ete ecrit.
create temporary table _c(ligne int, role text, tx bigint, idu text, familles smallint) on commit drop;
insert into _c values
       (3797,'compromis',15059,'U39MLAJD',4),
       (1902,'vente',6559,'EGR8KXOL',4),
       (1857,'offre',24372,'ZETH4WI9',3),
       (4745,'compromis',30791,'bbbaae80',5),
       (1492,'offre',24342,'VVGMC0QW',3),
       (1140,'offre',24160,'9CQ325R6',3),
       (2589,'offre',17505,'ASQO7HID',3),
       (123,'compromis',1000132,'G8YSAI5Z',5),
       (67,'compromis',3698,'I847SPN3',5),
       (3938,'offre',19130,'61OW86CS',3),
       (3627,'compromis',2507,'5H9BOKWJ',3),
       (3813,'compromis',16841,'73FOXX2A',4),
       (3483,'compromis',17203,'LNWLBVKG',3),
       (4067,'compromis',16378,'CITFQGOB',3),
       (4484,'offre',4201,'14853166',4),
       (4695,'compromis',30780,'d77d9ae1',4),
       (4790,'offre',30806,'d7cbb8fa',3),
       (4794,'offre',30816,'c6e5299a',4),
       (4437,'offre',8883,'1cf326f1',6),
       (4190,'offre',19567,'45545ae2',6),
       (2272,'offre',11760,'6LM8A6QK',3),
       (238,'vente',13,'HOPCBVKM',6),
       (829,'vente',4296,'33O2BWCL',3),
       (3736,'compromis',200,'S3J2JV0O',4),
       (3743,'compromis',19576,'YQG8CN5T',3),
       (3874,'compromis',22087,'KOYNCSYB',4),
       (4067,'offre',16383,'CITFQGOB',3),
       (4370,'offre',14928,'05e8ddb5',5),
       (4487,'offre',28685,'306641a4',6),
       (4625,'vente',30819,'c6c8bc29',5),
       (4157,'compromis',27679,'F5GA770R',3),
       (453,'compromis',1868,'PVRG1SNH',3),
       (4552,'compromis',25846,'c67855b1',3),
       (3661,'compromis',19074,'JYOLFY1A',3),
       (328,'compromis',2171,'DXSH7AWE',3),
       (1003,'offre',126,'AOPBUAOJ',4),
       (4105,'compromis',24512,'0IS41BM1',3),
       (210,'compromis',22979,'NRZVKH85',5),
       (388,'vente',25720,'H2JZ0S63',4),
       (3480,'compromis',21,'8GIIDS5T',4),
       (3628,'compromis',7546,'MCMUXOFP',3),
       (4469,'offre',14045,'a8b6c8cc',5),
       (4085,'compromis',11182,'UBISDN7Z',3),
       (4166,'compromis',28341,'1W2O0DSU',4),
       (3970,'compromis',6555,'Q602VZJX',4),
       (4472,'offre',28799,'0176b44e',5),
       (4604,'vente',30782,'f0ec39fc',3),
       (4552,'offre',25847,'c67855b1',3),
       (2440,'offre',22175,'DG9TK2GF',3),
       (4749,'compromis',30789,'34932f4e',5),
       (328,'offre',2172,'DXSH7AWE',3),
       (3651,'offre',17290,'3LMG7EXA',3),
       (77,'offre',9291,'1QJA9DBN',5),
       (210,'offre',22981,'NRZVKH85',5),
       (3625,'compromis',19619,'AA797XO0',3),
       (4504,'offre',28738,'38f13b81',5),
       (3477,'vente',3650,'427UDDSF',4),
       (4111,'compromis',11791,'O9IYE0F0',4),
       (1974,'offre',24466,'978V88C7',5),
       (3781,'compromis',19104,'80MU6MMO',3),
       (4763,'compromis',30793,'945146a0',5),
       (123,'offre',1000050,'G8YSAI5Z',5),
       (4682,'vente',30812,'3b5db3cc',6),
       (3576,'compromis',7646,'MAB7DN65',4),
       (258,'vente',7126,'WJ8NY16C',5),
       (4542,'vente',30781,'f0d731fa',5),
       (4793,'offre',30817,'fbf9799a',3),
       (4660,'vente',30799,'f85babee',6),
       (4028,'offre',17151,'T9F26E45',3),
       (3936,'offre',11670,'13KBCS85',3),
       (453,'offre',1869,'PVRG1SNH',3),
       (3960,'compromis',26027,'YV95DVKD',3),
       (4020,'compromis',26154,'RP4HBTQN',3),
       (1508,'offre',2589,'JNI5UWIA',3),
       (4765,'compromis',30811,'7b00046c',4),
       (3951,'offre',23415,'NOPYBDHI',3),
       (829,'compromis',4294,'33O2BWCL',3),
       (4458,'compromis',28660,'cd3303c8',5),
       (383,'compromis',27094,'XR6SJG85',5),
       (3482,'offre',11358,'N62LJIBY',4),
       (3918,'compromis',11708,'VYNGKCR0',3),
       (3655,'compromis',20309,'676XP6GN',4),
       (238,'offre',12,'HOPCBVKM',6),
       (4471,'offre',28802,'b9dd4eeb',4),
       (3719,'compromis',2533,'7PTB8Z3M',4),
       (3133,'offre',8018,'SXJDHXKF',3),
       (829,'offre',4295,'33O2BWCL',3),
       (3523,'compromis',14913,'AVXWIZTU',3),
       (388,'compromis',25718,'H2JZ0S63',4),
       (3614,'compromis',1160,'G1TVNXJ5',4),
       (3738,'compromis',29005,'GUUVDY2S',3),
       (1282,'compromis',24380,'RF9KYWSY',5),
       (2173,'vente',17451,'TMS863YQ',3),
       (4460,'offre',11147,'e9260960',6),
       (4684,'compromis',30810,'aad89f34',4),
       (4604,'compromis',28841,'f0ec39fc',3),
       (3538,'compromis',20277,'FUDJ9CJC',4),
       (189,'offre',3582,'B8UXUHU4',5),
       (4080,'compromis',17147,'3XMY2OG3',3),
       (4657,'vente',30807,'d57e7da9',5),
       (3530,'vente',27141,'IEYXREWQ',3),
       (1896,'offre',21599,'GM8VDVK2',4),
       (1857,'vente',24373,'ZETH4WI9',3),
       (4051,'compromis',24499,'Q23M98IX',5),
       (4457,'compromis',28568,'959b7669',5),
       (388,'offre',25719,'H2JZ0S63',4),
       (4606,'compromis',11138,'774aa002',5),
       (2297,'offre',22172,'PT1ZTCIQ',3),
       (4604,'offre',28842,'f0ec39fc',3),
       (3455,'compromis',2210,'HRC324JH',5),
       (1011,'vente',17324,'5GZVT548',5),
       (3636,'compromis',4277,'HEQZW1KO',3),
       (3487,'compromis',26605,'G88ISQKI',4),
       (3446,'offre',2169,'1W9FJJLB',3),
       (4068,'compromis',9496,'SC55F4MV',4),
       (3439,'compromis',22,'7NI4WKV5',4),
       (545,'offre',9452,'IX6FX4TX',5),
       (3926,'compromis',19711,'R2U574AC',3),
       (4358,'offre',6172,'a5cb141f',4),
       (3935,'offre',20090,'5QE9107L',3),
       (4123,'compromis',27661,'MDTBQXVO',3),
       (315,'vente',28147,'HPNJ32UM',5),
       (3613,'compromis',117,'7HDK9XOG',4),
       (430,'offre',27137,'GQCBSQNY',4),
       (67,'vente',3701,'I847SPN3',5),
       (3502,'compromis',19612,'644UYQNA',4),
       (3756,'compromis',3719,'TQYCQNY4',3),
       (3817,'offre',24454,'4PW2L3MG',3),
       (4499,'offre',28636,'b2334671',5),
       (3860,'offre',11657,'6NOJ686I',4),
       (2521,'offre',16421,'ZR13FV3K',3),
       (3603,'compromis',17434,'3ID282Y1',4),
       (3828,'compromis',20408,'DHG4SD0N',5),
       (4090,'compromis',24598,'1X9W3VUF',4),
       (4697,'compromis',30818,'ce63cee9',3),
       (4060,'compromis',24443,'BEI93QZ2',4),
       (3768,'compromis',19737,'3WBNBNY4',3),
       (3703,'compromis',177,'XCK96Z01',4),
       (4713,'compromis',30798,'db0d5e8d',4),
       (2789,'offre',27741,'NKDC0I1M',3),
       (3664,'compromis',20301,'HORVRQ6N',4),
       (3832,'compromis',4126,'P252U1JH',3),
       (453,'vente',1870,'PVRG1SNH',3),
       (4154,'compromis',24564,'UWNRN6F2',3),
       (4751,'compromis',30805,'ce56c77b',5),
       (4153,'compromis',17651,'XVRCFWCK',3),
       (328,'vente',2173,'DXSH7AWE',3),
       (4628,'vente',30783,'63b1e2fd',5),
       (3940,'compromis',24406,'D7CZQBZG',3),
       (210,'vente',22983,'NRZVKH85',5),
       (4343,'vente',30813,'2c2566d7',4),
       (4671,'compromis',30787,'c340b94b',4),
       (4766,'compromis',30795,'9ec1e1a6',4),
       (4754,'compromis',30790,'5a956cad',5),
       (4795,'offre',30815,'7543e4fb',3),
       (4792,'offre',30808,'c67ccc6a',3),
       (4039,'compromis',11729,'HBZQXR67',3),
       (3690,'compromis',4329,'G41FTEZ8',3),
       (3660,'compromis',24122,'H75WKJ6X',4),
       (4718,'offre',1000,'a8aaeb2b',3),
       (3568,'compromis',27135,'JRE23R1G',3),
       (3633,'compromis',21965,'UIM5TBKS',4),
       (2107,'compromis',16407,'M4FNSOPF',4),
       (4622,'vente',30800,'c5e267b6',5),
       (2173,'compromis',17449,'TMS863YQ',3),
       (4756,'compromis',30788,'bd0e986f',5),
       (1857,'compromis',24371,'ZETH4WI9',3),
       (1131,'offre',11597,'717OUUED',4),
       (3575,'compromis',14939,'ZE9WZW22',4),
       (4757,'compromis',30794,'91b51c1b',5),
       (2173,'offre',17450,'TMS863YQ',3),
       (3686,'compromis',4510,'VHZ88PLB',3),
       (3968,'compromis',16377,'RX6J289Y',3),
       (3521,'offre',26,'CW4IYXO2',3),
       (3939,'compromis',19690,'YKSL5L2U',5),
       (3969,'compromis',20492,'XCAUACUJ',4),
       (2696,'offre',24631,'50LQ2VSA',3);

-- Garde-fou : on n'ajoute QUE ce qui est encore libre, verifie MAINTENANT.
-- ⭐ Ces deux deletes sont le coeur du patch : ils rendent le geste sur, meme
--   si la base a bouge depuis la fabrication de la liste.
delete from _c where exists
  (select 1 from public.app_classeur_lien g where g.app_affaire_id = _c.tx);
delete from _c where exists
  (select 1 from public.app_classeur_lien g
    where g.ligne_classeur = _c.ligne and g.role = _c.role);

-- Et un plancher : si la liste fond, c'est que quelque chose a change. On le DIT.
do $gardeC$
declare n int;
begin
  select count(*) into n from _c;
  raise notice 'LOT C : % liens encore libres sur 177 prevus', n;
  if n < 150 then
    raise exception 'LOT C : plus que % liens sur 177 -- la base a bouge, RIEN FAIT', n;
  end if;
end $gardeC$;

insert into public.app_classeur_lien
  (ligne_classeur, app_affaire_id, role, confiance, preuves, etage, gele_le, gele_par, id_unique)
select c.ligne, c.tx, c.role, 'sûre',
       c.familles,   -- le nombre de familles de temoins independantes (3 a 6)
       'v2 additif (13/11) : >= 3 familles', now(),
       'regel additif 13/11 -- lot C', c.idu
  from _c c;

commit;
