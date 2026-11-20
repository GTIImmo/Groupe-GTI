# Les 132 coupes mesurees, l'outil corrige, tes deux criteres (20/11, soir)

> Lecture seule. Genere par `phase2/checks/temps11_les_132_mesurees_et_tes_criteres_2026-11-20.py` (l'outil : `coupe_preuve_interne.py`), gel vivant.

```
gel vivant : 12820 liens ; lignes rattachees a un bien : 4868

1. LES 132 COUPES : 627 pieces -- {'PROUVEE PAR LA DATE': 623, 'PROUVEE PAR SA CHAINE': 2, 'SANS PREUVE INTERNE': 1, 'PROUVEE PAR PRIX + HONORAIRES': 1}
   coupes : {'PROUVEE': 129, 'PROUVEE (une offre par sa chaine)': 2, 'SANS PREUVE': 1}
   TEMOIN du critere 2 -- la regle de la plus petite transaction contre la simulation de la pose (ecrire, puis corriger dans tous les sens), sur chaque piece des 132 : 583 d'accord (dont 329 ou rien ne bouge), 0 en desaccord []

2. L'OUTIL CORRIGE CONTRE L'ANCIEN : {"132 / LE NEUF S'ABSTIENT": 3, '132 / MEME LIGNE': 624, 'classeur / LE NEUF CORRIGE': 10, "classeur / LE NEUF S'ABSTIENT": 15, 'classeur / LE NEUF TRANCHE UNE DISPUTE': 12, 'classeur / MEME LIGNE': 202}
   groupe 7, piece 16382 [date] : l'ancien -> R0JRVFDC ; le neuf -> - (date 2020-09-23 sur aucune case, honoraires inconnus) -- LE NEUF S'ABSTIENT
   groupe 7, piece 16378 [nom seul] : l'ancien -> JUTS27P6 ; le neuf -> RX6J289Y (PROUVEE PAR PRIX + HONORAIRES) -- LE NEUF CORRIGE
   groupe 8, piece 17131 [nom seul] : l'ancien -> DEZQM9HM ; le neuf -> ZV3QRSJG (PROUVEE PAR PRIX + HONORAIRES) -- LE NEUF CORRIGE
   groupe 17, piece 27134 [nom seul] : l'ancien -> 2HOL5ISX ; le neuf -> IEYXREWQ (PROUVEE PAR PRIX + HONORAIRES) -- LE NEUF CORRIGE
   groupe 17, piece 27135 [nom seul] : l'ancien -> 2HOL5ISX ; le neuf -> JRE23R1G (PROUVEE PAR PRIX + HONORAIRES) -- LE NEUF CORRIGE
   groupe 22, piece 4533 [case vide] : l'ancien -> PCDZXTIY ; le neuf -> - (prix + honoraires de plusieurs acheteurs (FYNZEKI6 PCDZXTIY)) -- LE NEUF S'ABSTIENT
   groupe 25, piece 4649 [nom seul] : l'ancien -> 2FOH8HE4 ; le neuf -> HHQZC2QP (PROUVEE PAR PRIX + HONORAIRES) -- LE NEUF CORRIGE
   groupe 25, piece 4651 [nom seul] : l'ancien -> 2FOH8HE4 ; le neuf -> N9J2533O (PROUVEE PAR PRIX + HONORAIRES) -- LE NEUF CORRIGE
   groupe 28, piece 7450 [nom seul] : l'ancien -> HRRSO81C ; le neuf -> DN5U3GER (PROUVEE PAR PRIX + HONORAIRES) -- LE NEUF CORRIGE
   groupe 28, piece 7453 [nom seul] : l'ancien -> HRRSO81C ; le neuf -> - (date 2020-05-18 sur aucune case, honoraires inconnus) -- LE NEUF S'ABSTIENT
   groupe 29, piece 7710 [case vide] : l'ancien -> 9DK01H85 ; le neuf -> - (prix + honoraires de plusieurs acheteurs (9DK01H85 SWDW99J5)) -- LE NEUF S'ABSTIENT
   groupe 40, piece 14110 [nom seul] : l'ancien -> Z3DYDC4X ; le neuf -> - (prix + honoraires de plusieurs acheteurs (AYIHPHF5 L2B2WGCF Z3DYDC4X)) -- LE NEUF S'ABSTIENT
   groupe 40, piece 14115 [disputee] : l'ancien -> - ; le neuf -> AYIHPHF5 (PROUVEE PAR LA DATE) -- LE NEUF TRANCHE UNE DISPUTE
   groupe 50, piece 4560 [case vide] : l'ancien -> QV5AYD2K ; le neuf -> - (prix + honoraires de plusieurs acheteurs (BNWNKPJH QV5AYD2K)) -- LE NEUF S'ABSTIENT
   groupe 50, piece 4564 [disputee] : l'ancien -> - ; le neuf -> BNWNKPJH (PROUVEE PAR LA DATE) -- LE NEUF TRANCHE UNE DISPUTE
   TEMOIN de l'outil -- les 4 lectures justes que j'avais refaites a la main sont retrouvees : VERT []
   TEMOIN de l'outil -- il s'abstient sur les 4 indecidables (4533, 7710, 4560, 14110) : VERT []

3. LES LIGNES OUBLIEES : sur 180 groupes, 27 ont une ligne du meme bien HORS du groupe qui RECLAME une de leurs pieces (date au jour exact ou prix + honoraires), 37 en ont une contemporaine qui ne reclame rien
   groupe 11 (section 1, ATTENDRE) E1WD68ZB K013ZH03 -> reclame : EO8MXFE9
   groupe 17 (section 1, A) 2HOL5ISX GQCBSQNY -> reclame : IEYXREWQ
   groupe 20 (section 1, ATTENDRE) 3308P0UX N1CUULMN -> reclame : 9WQ204HP YRUF0S9H
   groupe 24 (section 1, NON) 910O0A2Q TND2I31B -> reclame : 0EMKY4ZS
   groupe 25 (section 1, A) 2FOH8HE4 VX5RZL6B -> reclame : HHQZC2QP
   groupe 40 (section 2, OUI) AYIHPHF5 Z3DYDC4X -> reclame : L2B2WGCF
   groupe 53 (section 3, A) 3308P0UX -> reclame : 9WQ204HP YRUF0S9H
   groupe 58 (section 3, A) E9GL6MUS -> reclame : H6CTRVR6
   groupe 59 (section 3, A) H6CTRVR6 -> reclame : E9GL6MUS
   groupe 61 (section 3, A) O6R10ZQA -> reclame : QW7MPWOM T2GZOY5O
   groupe 62 (section 3, REGLEE) P252U1JH -> reclame : FOZ6HZLK
   groupe 63 (section 3, A) QJQ9M4OF -> reclame : D9MMB7OU
   groupe 66 (section 3, A) T2GZOY5O -> reclame : O6R10ZQA
   groupe 68 (section 3, A) V3FO5NDA -> reclame : 6FQO29C8
   groupe 74 (section 3, A) d2108609 -> reclame : 1c7b38f9
   groupe 76 (section 4, OUI) 2FBR2M9U E6RLLKMN -> reclame : JX1K7DWB ZN47FIR7
   groupe 78 (section 4, OUI) FJS4IJGZ SWSN80FQ -> reclame : VTVUQWO4
   groupe 108 (section 7, MA) 2c2566d7 -> reclame : df0ce30c
   groupe 111 (section 7, MA) 3TLH0CNW -> reclame : XCK96Z01
   groupe 113 (section 7, MA) 4PW2L3MG -> reclame : 6U5DQQ4J
   groupe 116 (section 7, MA) 7JXLR3JQ -> reclame : WECT3RIT
   groupe 126 (section 7, MA) KT0601S6 -> reclame : PPIM4947
   groupe 127 (section 7, MA) LNWLBVKG -> reclame : ODF1PWJ0
   groupe 128 (section 7, MA) LPBAZ1D4 -> reclame : 1cc703d9
   groupe 129 (section 7, MA) PPIM4947 -> reclame : KT0601S6
   groupe 132 (section 7, MA) VYNGKCR0 -> reclame : SC58GWXX
   groupe 133 (section 7, MA) XCK96Z01 -> reclame : 3TLH0CNW
   TEMOIN : FARGE-DEBISE (L2B2WGCF) est vue sur le groupe 40 : VERT
   sur les 132 coupes : 9 ont une ligne hors de la coupe qui reclame une piece [('11', ['ISJ3UPP0']), ('32', ['ZFRCK5QG']), ('37', ['OCNTE01G']), ('44', ['OHMP44NF']), ('47', ['T2GZOY5O']), ('87', ['JZSYFT94']), ('97', ['SHN6RKDI']), ('107', ['2PPLFRGI'])]

4. TES 23 QUESTIONS, TES DEUX CRITERES
   A1 GANDON-BERAUD (1D7EIYKW) : A PART (critere 1) -- 27512 : pas de preuve (date 2021-02-17 sur aucune case, prix 51000.0 + honoraires 4000.0 : ceux d'aucune ligne) et sa place deplacerait une etiquette -> A PART
   A2 RIGAUD (87QOXR64) : SORT DE TA LISTE (critere 2) -- ta reponse ne deplace aucune piece : une date d'annulation
   A3 SOUBEYRAND / MERCIER (E9GL6MUS H6CTRVR6) : TRANCHEE PAR LA PREUVE -- 11414 -> E9GL6MUS (PROUVEE PAR LA DATE)
   A4 BAUDOIN-PETIPAS (V3FO5NDA) : TRANCHEE PAR LA PREUVE -- 19131 -> 6FQO29C8 (PROUVEE PAR LA DATE) ; 19133 -> 6FQO29C8 (PROUVEE PAR LA DATE)
   A5 DEBARD (deux affaires) (5QE9107L ZW7MKTWH) : A PART (critere 1) -- 20088 : pas de preuve (sans date, prix 50000.0 + honoraires 5000.0 : ceux d'aucune ligne) et sa place deplacerait une etiquette -> A PART
   A6 MEJEAN-MARIAGE / FAU-PIETTE (RGCEC677) : A PART (critere 1) -- 4542 : pas de preuve (sans date, prix 108000.0 + honoraires 8000.0 : ceux d'aucune ligne) et sa place deplacerait une etiquette -> A PART
   A7 IMAW / BLACHON / MADER (2dfa6ef3 5a956cad d1cb8dd7) : SORT DE TA LISTE (critere 2) -- ta reponse ne deplace aucune piece : le role d'une offre dans un dossier qui ne change pas
   A8 VIALLARD (+ MARCOS) et PAOLONE (3308P0UX 9WQ204HP O6R10ZQA T2GZOY5O) : SORT DE TA LISTE (critere 2) -- ta reponse ne deplace aucune piece : laquelle des deux saisies d'une meme affaire porte l'etiquette (meme dossier)
   A9 AFFONSO (soeur ROBERT) (QJQ9M4OF) : TRANCHEE PAR LA PREUVE -- 17366 -> D9MMB7OU (PROUVEE PAR LA DATE)
   B1 MOSNIER (SHN6RKDI) : A PART (critere 1) -- 26613 : pas de preuve (sans date, honoraires inconnus) et sa place deplacerait une etiquette -> A PART
   B2 CHOUVELLON (d2108609) : A PART (critere 1) -- 21520 : pas de preuve (prix + honoraires de plusieurs acheteurs (1c7b38f9 d2108609)) et sa place deplacerait une etiquette -> A PART
   B3 DONNADIEU-KOSINSKI (ea6a28a7) : TRANCHEE PAR LA PREUVE -- 14033 -> ea6a28a7 (PROUVEE PAR PRIX + HONORAIRES)
   B4 DUPARANT-BACHELET (TA5QUCD4) : SORT DE TA LISTE (critere 2) -- ta reponse ne deplace aucune piece : une date d'offre
   B5 GERPHAGNON-JOINAUX (Y9A2L3X4) : SORT DE TA LISTE (critere 2) -- ta reponse ne deplace aucune piece : une date de compromis
   B6 CANIVET (HUY49KEC) : SORT DE TA LISTE (critere 2) -- ta reponse ne deplace aucune piece : un compromis a creer : il entrerait dans le dossier avec un numero plus grand
   B7 SCI LA FELOLIE (c0a73edd) : SORT DE TA LISTE (critere 2) -- ta reponse ne deplace aucune piece : un dossier sur une AUTRE annonce (le chainage ne traverse jamais deux biens)
   => sortent de ta liste (aucune etiquette ne bouge) : 7 questions, 12 lignes

5. LES PIECES DE MES CORRECTIONS, AU CRIBLE DU NEUF
   groupe 7, 16378 -> RX6J289Y (PROUVEE PAR PRIX + HONORAIRES)
   groupe 17, 27135 -> JRE23R1G (PROUVEE PAR PRIX + HONORAIRES)
   groupe 17, 27134 -> IEYXREWQ (PROUVEE PAR PRIX + HONORAIRES)
   groupe 25, 4649 -> HHQZC2QP (PROUVEE PAR PRIX + HONORAIRES)
   groupe 25, 4651 -> N9J2533O (PROUVEE PAR PRIX + HONORAIRES)
   groupe 28, 7450 -> DN5U3GER (PROUVEE PAR PRIX + HONORAIRES)
   groupe 8, 17131 -> ZV3QRSJG (PROUVEE PAR PRIX + HONORAIRES)
   groupe 22, 4533 -> A PART (prix + honoraires de plusieurs acheteurs (FYNZEKI6 PCDZXTIY))
   groupe 29, 7710 -> A PART (prix + honoraires de plusieurs acheteurs (9DK01H85 SWDW99J5))
   groupe 50, 4560 -> A PART (prix + honoraires de plusieurs acheteurs (BNWNKPJH QV5AYD2K))
   groupe 40, 14110 -> A PART (prix + honoraires de plusieurs acheteurs (AYIHPHF5 L2B2WGCF Z3DYDC4X))
   groupe 40, 14115 -> AYIHPHF5 (PROUVEE PAR LA DATE)
   groupe 50, 4564 -> BNWNKPJH (PROUVEE PAR LA DATE)

6. OU CA TOMBE -- 203 biens, 433 morceaux, 39 pieces A PART (19 dont la place ne bougerait aucune etiquette)
   lignes : {'ECRITE': 395, 'NON ECRITE': 6} ; offres acceptees rangees par leur compromis : 5, par sa convention de renegociation : 1
   non ecrites : HUY49KEC (il ne lui reste que sa copie C5 (1001587) ; ses pieces Hektor : 3741 a part (date 2018-11-23 sur aucune case, ) ; SBH4QWDW (ses pieces sont a part ou ailleurs : 23054 (date 2021-01-26 sur aucune case, honoraires inconnus)) ; SHN6RKDI (il ne lui reste que sa copie C5 (1001457) ; ses pieces Hektor : 26613 a part (sans date, honoraires inconnus)) ; XHITO8HE (ses pieces sont a part ou ailleurs : 27556 (date 2020-05-23 sur aucune case, honoraires inconnus)) ; d2108609 (il ne lui reste que sa copie C5 (1001495) ; ses pieces Hektor : 21520 a part (prix + honoraires de plusieurs a) ; ea6a28a7 (ses pieces sont a part ou ailleurs : 14033 (B3, sa decision du 20/11 soir))
   A1 GANDON-BERAUD : 1D7EIYKW ECRITE -- morceau 27513
   A2 RIGAUD : 87QOXR64 ECRITE -- morceau 17427+17429+1001534
   A3 SOUBEYRAND / MERCIER : E9GL6MUS ECRITE -- morceau 11412 | H6CTRVR6 ECRITE -- morceau 11413+11415+11416
   A4 BAUDOIN-PETIPAS : V3FO5NDA ECRITE -- morceau 19132
   A5 DEBARD (deux affaires) : 5QE9107L ECRITE -- morceau 20090 | ZW7MKTWH ECRITE -- morceau 20089
   A6 MEJEAN-MARIAGE / FAU-PIETTE : RGCEC677 ECRITE -- morceau 4545
   A7 IMAW / BLACHON / MADER : 2dfa6ef3 ECRITE -- morceau 30656+30692 | 5a956cad ECRITE -- morceau 30684+30776+30790 | d1cb8dd7 ECRITE -- morceau 28831+28834
   A8 VIALLARD (+ MARCOS) et PAOLONE : 3308P0UX ECRITE -- morceau 4483 (avec YRUF0S9H) | 9WQ204HP ECRITE -- morceau 4480+4484+1001532 | O6R10ZQA ECRITE -- morceau 20073+20075+1001480+1001536 (avec T2GZOY5O) | T2GZOY5O ECRITE -- morceau 20073+20075+1001480+1001536 (avec O6R10ZQA)
   A9 AFFONSO (soeur ROBERT) : QJQ9M4OF ECRITE -- morceau 17365+17367
   B1 MOSNIER : SHN6RKDI NON ECRITE -- il ne lui reste que sa copie C5 (1001457) ; ses pieces Hektor : 26613 a part (sans date, honoraires inconnus)
   B2 CHOUVELLON : d2108609 NON ECRITE -- il ne lui reste que sa copie C5 (1001495) ; ses pieces Hektor : 21520 a part (prix + honoraires de plusieurs acheteurs (1c7b38f9 d2108609))
   B3 DONNADIEU-KOSINSKI : ea6a28a7 NON ECRITE -- ses pieces sont a part ou ailleurs : 14033 (B3, sa decision du 20/11 soir)
   B4 DUPARANT-BACHELET : TA5QUCD4 ECRITE -- morceau 28362+28364
   B5 GERPHAGNON-JOINAUX : Y9A2L3X4 ECRITE -- morceau 11996+11997+11998
   B6 CANIVET : HUY49KEC NON ECRITE -- il ne lui reste que sa copie C5 (1001587) ; ses pieces Hektor : 3741 a part (date 2018-11-23 sur aucune case, honoraires inconnus)
   B7 SCI LA FELOLIE : c0a73edd ECRITE -- morceau 28611+28612+28613
   les 274 lignes des 132 coupes : 273 ecrites, 1 non -> SBH4QWDW (ses pieces sont a part ou ailleurs : 23054 (date 2021-01-26 sur aucune case, honoraires inconnus))
   gestes sur le gel pour y arriver (a faire seulement sur ton accord) : 83 (relier 42, delier 41)
   A PART : 4669 compromis cancelled 16800.0 (bien 10043) -- prix + honoraires de plusieurs acheteurs (GYGF5F1X ZMQZSE9Q)
   A PART : 7453 offre refused 143000.0 (bien 15087) -- date 2020-05-18 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 7710 compromis cancelled 135000.0 (bien 15672) -- prix + honoraires de plusieurs acheteurs (9DK01H85 SWDW99J5)
   A PART : 1059 compromis cancelled 195000.0 (bien 2208) -- date 2023-12-18 sur aucune case, prix 195000.0 + honoraires 12000.0 : ceux d'aucune ligne
   A PART : 11670 offre refused 129000.0 (bien 24484) -- date 2021-02-13 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 14033 compromis cancelled 140500.0 (bien 28506) -- B3, sa decision du 20/11 soir
   A PART : 14110 compromis cancelled 113000.0 (bien 28653) -- prix + honoraires de plusieurs acheteurs (AYIHPHF5 L2B2WGCF Z3DYDC4X)
   A PART : 16019 vente None 11000.0 (bien 32929) -- date 2025-06-10 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 16382 offre refused 249000.0 (bien 34066) -- date 2020-09-23 sur aucune case, honoraires inconnus
   A PART : 17136 offre refused 47500.0 (bien 36320) -- date 2021-02-22 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 17436 offre refused 65700.0 (bien 37192) -- date 2024-04-17 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 20088 compromis cancelled 50000.0 (bien 41481) -- sans date, prix 50000.0 + honoraires 5000.0 : ceux d'aucune ligne
   A PART : 21520 compromis cancelled 282000.0 (bien 43050) -- prix + honoraires de plusieurs acheteurs (1c7b38f9 d2108609)
   A PART : 23054 offre refused 75000.0 (bien 45891) -- date 2021-01-26 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 1001561 offre accepted None (bien 47557) -- C5 sans ligne d'origine -- sa place ne bouge aucune etiquette
   A PART : 24124 offre accepted 11800.0 (bien 47776) -- date 2023-04-17 sur aucune case, honoraires inconnus
   A PART : 24321 offre accepted 9800.0 (bien 48013) -- date 2021-08-04 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 24591 offre refused 19200.0 (bien 48311) -- date 2019-08-29 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 24600 compromis cancelled 39000.0 (bien 48321) -- date 2019-05-17 sur aucune case, prix 39000.0 + honoraires 4000.0 : ceux d'aucune ligne
   A PART : 24601 offre refused 39000.0 (bien 48321) -- date 2019-04-03 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 25891 offre refused 80000.0 (bien 49941) -- date 2024-05-18 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 26613 compromis cancelled 210000.0 (bien 52166) -- sans date, honoraires inconnus
   A PART : 27141 vente None 89000.0 (bien 53342) -- date 2025-04-23 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 27512 compromis cancelled 51000.0 (bien 53740) -- date 2021-02-17 sur aucune case, prix 51000.0 + honoraires 4000.0 : ceux d'aucune ligne
   A PART : 27555 offre accepted 112000.0 (bien 53803) -- date 2020-10-02 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 27556 offre refused 118000.0 (bien 53803) -- date 2020-05-23 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 28116 compromis cancelled 60000.0 (bien 54676) -- sans date, prix 60000.0 + honoraires 5000.0 : ceux d'aucune ligne
   A PART : 28118 offre accepted 53000.0 (bien 54676) -- date 2026-03-23 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 28363 offre accepted 110000.0 (bien 55203) -- date 2018-12-11 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 28833 offre accepted 129000.0 (bien 61599) -- date 2026-04-15 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 3741 vente None 54500.0 (bien 8671) -- date 2018-11-23 sur aucune case, honoraires inconnus
   A PART : 4126 compromis cancelled 77000.0 (bien 9232) -- prix + honoraires de plusieurs acheteurs (FOZ6HZLK P252U1JH)
   A PART : 4327 compromis cancelled 55000.0 (bien 9556) -- prix + honoraires de plusieurs acheteurs (ACB4D8WI G41FTEZ8 PYG8JZ0C)
   A PART : 4533 compromis cancelled 99000.0 (bien 9868) -- prix + honoraires de plusieurs acheteurs (FYNZEKI6 PCDZXTIY)
   A PART : 4542 compromis cancelled 108000.0 (bien 9877) -- sans date, prix 108000.0 + honoraires 8000.0 : ceux d'aucune ligne
   A PART : 4543 offre accepted 72000.0 (bien 9877) -- date 2022-03-16 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 4544 offre refused 108000.0 (bien 9877) -- date 2021-09-10 sur aucune case, honoraires inconnus -- sa place ne bouge aucune etiquette
   A PART : 4560 compromis cancelled 60000.0 (bien 9902) -- prix + honoraires de plusieurs acheteurs (BNWNKPJH QV5AYD2K)
   A PART : 4621 compromis cancelled 50000.0 (bien 9961) -- prix + honoraires de plusieurs acheteurs (0EMKY4ZS 910O0A2Q)

ecrit : TEMPS11_LES_132_MESUREES_ET_TES_CRITERES_2026-11-20.md et .csv
RESULTAT : VERT

- **coupe 58 -- PROUVEE (une offre par sa chaine)** (critere 2 : la place des pieces en doute ne change aucune etiquette) : `2166 comp(cancel)+2169 offr(refuse) -> 1W9FJJLB GOUDET | 2167 comp(active)+2168 offr(accept)+2170 vent -> ZLY1CLKF FOURNEL `
  - 2168 -> ZLY1CLKF : PROUVEE PAR SA CHAINE -- offre acceptee, seule du bien, suivie 9 j plus tard par le compromis actif 2167 (prouve)
- **coupe 67 -- SANS PREUVE** (critere 2 : une etiquette en depend) : `23050 comp(cancel)+23053 offr(refuse) -> VMWFLLW4 PARRELLA | 23051 comp(active)+23052 offr(accept)+23055 vent -> DBRDHEGH DUPUY | 23054 offr(refuse) -> SBH4QWDW SOTTON `
  - 23054 -> SBH4QWDW : SANS PREUVE INTERNE -- date 2021-01-26 sur aucune case, honoraires inconnus
- **coupe 90 -- PROUVEE (une offre par sa chaine)** (critere 2 : la place des pieces en doute ne change aucune etiquette) : `26027 comp(cancel)+26030 offr(refuse) -> YV95DVKD MANDOLI | 26028 comp(cancel)+26031 offr(refuse) -> YFITUAFH BORNE | 26029 offr(accept)+26032 vent+29007 comp(active) -> DKH6IOKA PIERA `
  - 26029 -> DKH6IOKA : PROUVEE PAR SA CHAINE -- offre acceptee, seule du bien, suivie 22 j plus tard par le compromis actif 29007 (prouve)
