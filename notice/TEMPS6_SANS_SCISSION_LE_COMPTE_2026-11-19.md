# Le compte de la question 3 du 19/11 au soir (genere par temps6_les_803_lignes_et_ce_qui_les_debloque_2026-11-19.py)

```
LES 520 LIGNES « PLUSIEURS DOSSIERS » ET « ETIQUETTE PARTAGEE » D'AUJOURD'HUI -- CE QUI LES LIBERE (la premiere couche qui les sort de ces deux cases)
                                                                                      PLUSIEURS  PARTAGEE  TOTAL
   1 la nuit des 10 menages (decidee, joue cette nuit)                                        0         0      0
   2 le patch V2 du gel (ton « vas-y »)                                                       0         0      0
   3 la regle E (ton allumage ; 26613 et 21520 exclues)                                       0         0      0
   4 les 8 lignes de 5.6 (ta lecture)                                                         8         0      8
   5 la regle C5 « a l'export » (DECIDEE le 19/11 au soir : une regle de l'outil d'ecriture)       102         0    102
   6 relecture du gel (un patch a valider, sans scission)                                    26         4     30
   7 reunir (lignes de rattachement, ta decision ligne a ligne, sans scission)                7         0      7
   8 meme acheteur sur deux lignes (DECIDE : l'etiquette sur la seule ligne vivante)          1         8      9
   9 melange -> SCISSION                                                                     79       284    363
   10 non tranche (le juge ne voit pas une des lignes)                                        0         0      0
   11 en attente de ta reponse (une transaction EXCLUE de la regle E)                         1         0      1
   TOTAL                                                                                    224       296    520

CE QUE DEVIENNENT LES LIGNES LIBEREES PAR LES COUCHES 1 A 5 (leur case dans cet etat) :
   couche 4 -> VAGUE_1                   8
   couche 5 -> GEL_SEUL                 16
   couche 5 -> VAGUE_1                  86

AU-DELA DE 5 -- LES GROUPES (lignes + dossiers relies) que ces lignes forment :
   6 relecture du gel (un patch a valider, sans scission)                               30 groupes,   33 lignes,   30 dossiers
   7 reunir (lignes de rattachement, ta decision ligne a ligne, sans scission)           7 groupes,    7 lignes,   15 dossiers
   8 meme acheteur sur deux lignes (DECIDE : l'etiquette sur la seule ligne vivante)     5 groupes,   10 lignes,    5 dossiers
   9 melange -> SCISSION                                                               178 groupes,  371 lignes,  241 dossiers
   10 non tranche (le juge ne voit pas une des lignes)                                   0 groupes,    0 lignes,    0 dossiers
   11 en attente de ta reponse (une transaction EXCLUE de la regle E)                    1 groupes,    1 lignes,    1 dossiers

LES MELANGES (couche 9) -- leur forme :
   SIGNATURE DU DEFAUT                                             108 groupes,  222 de nos lignes
   annulee + vivante, sans transaction au nom de l'annulee          60 groupes,  119 de nos lignes
   que des lignes annulees                                          10 groupes,   22 de nos lignes

ET 20 LIGNES Y ENTRENT apres la nuit et le patch V2 (elles sont ailleurs aujourd'hui) : {'PATCH_V2': 16, 'VAGUE_1': 1, 'SANS_LIEN': 3}

LES LIGNES DE LA VAGUE 1 D'AUJOURD'HUI DONT L'ETIQUETTE CHANGERAIT (la pose garde celle de la plus petite transaction) :
   apres la nuit des 10   :   0 ligne(s) 
   apres + la regle E     :  11 ligne(s) 205f62be 5f47de79 86ad8c0f ESVJUR12 KO6QPUV7 MCD6CRNB SC58GWXX SUVPN4BH UY443H27 beeaf847 ccbbf3c8
   apres + les 8 lignes   :  11 ligne(s) 205f62be 5f47de79 86ad8c0f ESVJUR12 KO6QPUV7 MCD6CRNB SC58GWXX SUVPN4BH UY443H27 beeaf847 ccbbf3c8

LES 4797 LIGNES DU SHEET, CASE PAR CASE, a chaque etat :
   etat 1 : VAGUE_1 3998 . ETIQUETTE_PARTAGEE 296 . PLUSIEURS_DOSSIERS 224 . LIEN_A_VALIDER 100 . SANS_LIEN 94 . PATCH_V2 39 . GEL_SEUL 23 . EN_ATTENTE 23
   etat 2 : VAGUE_1 3997 . ETIQUETTE_PARTAGEE 307 . PLUSIEURS_DOSSIERS 233 . LIEN_A_VALIDER 112 . SANS_LIEN 74 . AUDIT_NON_JUSTE 28 . GEL_SEUL 23 . EN_ATTENTE 23
   etat 3 : VAGUE_1 3987 . ETIQUETTE_PARTAGEE 320 . PLUSIEURS_DOSSIERS 232 . LIEN_A_VALIDER 110 . SANS_LIEN 74 . AUDIT_NON_JUSTE 28 . GEL_SEUL 23 . EN_ATTENTE 23
   etat 4 : VAGUE_1 3995 . ETIQUETTE_PARTAGEE 320 . PLUSIEURS_DOSSIERS 224 . LIEN_A_VALIDER 110 . SANS_LIEN 74 . AUDIT_NON_JUSTE 28 . GEL_SEUL 23 . EN_ATTENTE 23
   etat 5 : VAGUE_1 4081 . ETIQUETTE_PARTAGEE 340 . LIEN_A_VALIDER 110 . PLUSIEURS_DOSSIERS 101 . SANS_LIEN 74 . GEL_SEUL 40 . AUDIT_NON_JUSTE 28 . EN_ATTENTE 23

LA REGLE E FAIT SORTIR 10 LIGNE(S) DE LA VAGUE 1 (etat 2 -> etat 3) :
   205f62be (Vente réglée, Mme M. SOLEILHAC Robin COLAS A) -> ETIQUETTE_PARTAGEE ; avec ea6a28a7 (Annulée, Mme DONNADIEU Estelle M. KOSIN) ; acheteurs DIFFERENTS
   5f47de79 (Vente réglée, M. ESCAILLET Frederic) -> ETIQUETTE_PARTAGEE ; avec 5a4371b5 (Annulée, Mme M. MORAINES) ; acheteurs DIFFERENTS
   86ad8c0f (Vente réglée, M. RUAULT Philippe) -> ETIQUETTE_PARTAGEE ; avec caea1510 (Annulée, M. LAFFONT Jérémie Mme KAMPIRE) ; acheteurs DIFFERENTS
   C6XFV1E5 (Vente réglée, nan AOMAR) -> ETIQUETTE_PARTAGEE ; avec 3WBNBNY4 (Annulée, nan COLLY MONTMARTIN) ; acheteurs DIFFERENTS
   FOZ6HZLK (Vente réglée, nan GIORGETTI) -> ETIQUETTE_PARTAGEE ; avec P252U1JH (Annulée, nan CHAPTARD GAIGA) ; acheteurs DIFFERENTS
   SC58GWXX (Vente réglée, nan ZENNAF) -> ETIQUETTE_PARTAGEE ; avec VYNGKCR0 (Annulée, nan COURCELLE) ; acheteurs DIFFERENTS
   WO5IQTLW (Vente réglée, nan PATOUILLARD) -> ETIQUETTE_PARTAGEE ; avec YQG8CN5T (Annulée, nan VIALLARD VALOUR) ; acheteurs DIFFERENTS
   XBGMB7XP (Vente réglée, nan FAREL HUBBARD) -> ETIQUETTE_PARTAGEE ; avec AVXWIZTU (Annulée, nan PEYRET FAVIER) ; acheteurs DIFFERENTS
   beeaf847 (Vente réglée, M. FLEUROT Baptiste Mme CHIROL) -> ETIQUETTE_PARTAGEE ; avec b42affe7 (Annulée, M. FLEUROT Baptiste Mme CHIROL) ; MEME ACHETEUR
   ccbbf3c8 (Vente réglée, Mme M. GRANGEON Joanny CHAMBER) -> ETIQUETTE_PARTAGEE ; avec 1f3d536a (Annulée, Mme M. PALLANDRE Mathieu RICHA) ; acheteurs DIFFERENTS

LE SHEET JUGE LA REGLE E -- ses 32 reunions, cote par cote (les acquereurs AB des lignes reliees par le gel) :
   le Sheet ne voit qu'un cote (ou aucun)                    18
   LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste  11
   MEME ACHETEUR des deux cotes                               3
      dossier 1296 : le Sheet ne voit qu'un cote (ou aucun) -- 1296 [1296 compromis/cancelled BEDRE, 1298 offre/refused BEDRE] lignes NNKTA480(BEDRE) || 1297 [1297 compromis/cancelled BEDRE] lignes -
      dossier 1334 : le Sheet ne voit qu'un cote (ou aucun) -- 1334 [1334 compromis/cancelled THEVENON, 1337 offre/refused THEVENON] lignes JAKQXFWK(FAQRAOUI) || 1335 [1335 compromis/cancelled THEVENON] lignes -
      dossier 3669 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 3669 [3669 compromis/cancelled RUAULT] lignes caea1510(KAMPIRE LAFFONT) || 3670 [3670 compromis/active RUAULT, 3671 offre/accepted RUAULT, 3672 vente/None RUAULT] lignes 86ad8c0f(RUAULT)
      dossier 4125 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 4125 [4125 compromis/active GUERIN, 4127 offre/accepted GIORGETTI, 4129 vente/None GUERIN] lignes FOZ6HZLK(GIORGETTI) || 4126 [4126 compromis/cancelled GUERIN] lignes P252U1JH(CHAPTARD GAIGA)
      dossier 4267 : le Sheet ne voit qu'un cote (ou aucun) -- 4267 [4267 compromis/cancelled LAMBINET] lignes - || 4268 [4268 compromis/cancelled LAMBINET] lignes - || 4269 [4269 compromis/active LAMBINET, 4270 offre/accepted LAMBINET, 4273 vente/None LAMBINET] lignes UY443H27(LAMBINET RESLER)
      dossier 4495 : le Sheet ne voit qu'un cote (ou aucun) -- 4495 [4495 compromis/active GALLOT, 4497 offre/accepted FAUCHEZ/NOIRJEAN, 4499 vente/None GALLOT] lignes EWHVPSCC(FAUCHEZ NOIRJEAN) || 4496 [4496 compromis/cancelled GALLOT] lignes -
      dossier 4649 : le Sheet ne voit qu'un cote (ou aucun) -- 4649 [4649 compromis/cancelled DUVET, 4650 compromis/active DUVET, 4652 offre/accepted OLIVIERI/OSTRE, 4654 offre/refused DUVET, 4656 vente/None BERCOT] lignes 2FOH8HE4(DUVET) VX5RZL6B(OLIVIERI OSTRE) || 4651 [4651 compromis/cancelled DUVET] lignes -
      dossier 4720 : le Sheet ne voit qu'un cote (ou aucun) -- 4720 [4720 compromis/cancelled GARNIER] lignes - || 4721 [4721 compromis/active GARNIER, 4723 offre/accepted , 4724 vente/None GARNIER] lignes SUVPN4BH(ROBERT)
      dossier 7080 : le Sheet ne voit qu'un cote (ou aucun) -- 7080 [7080 compromis/cancelled PASSERIEUX] lignes - || 7081 [7081 compromis/active PASSERIEUX, 7082 offre/accepted PASSERIEUX, 7083 vente/None PASSERIEUX] lignes MCD6CRNB(PASSERIEUX)
      dossier 7448 : le Sheet ne voit qu'un cote (ou aucun) -- 7448 [7448 compromis/active GUERIN, 7449 compromis/cancelled GUERIN, 7451 offre/accepted MASSARD, 7453 offre/refused GUERIN, 7454 vente/None MASSARD] lignes 65M3RZSX(MASSARD) HRRSO81C(GUERIN) || 7450 [7450 compromis/cancelled GUERIN] lignes -
      dossier 7604 : le Sheet ne voit qu'un cote (ou aucun) -- 7604 [7604 compromis/active MALLARD, 7607 offre/accepted MALLARD, 7608 vente/None MALLARD] lignes 2EX8MDJW(MALLARD) || 7605 [7605 compromis/cancelled MALLARD] lignes -
      dossier 11204 : le Sheet ne voit qu'un cote (ou aucun) -- 11204 [11204 compromis/cancelled KERROUM, 11207 offre/refused KERROUM] lignes - || 11205 [11205 compromis/cancelled KERROUM] lignes -
      dossier 11578 : le Sheet ne voit qu'un cote (ou aucun) -- 11578 [11578 compromis/active BARRE/NEVEU, 11580 offre/accepted BARRE, 11582 vente/None BARRE] lignes G58FN51A(BARRE NEVEU) || 11579 [11579 compromis/cancelled BARRE/NEVEU] lignes -
      dossier 11708 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 11708 [11708 compromis/cancelled ZENNAF] lignes VYNGKCR0(COURCELLE) || 11709 [11709 compromis/active ZENNAF, 11710 offre/accepted ZENNAF, 11712 vente/None ZENNAF] lignes SC58GWXX(ZENNAF)
      dossier 14033 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 14033 [14033 compromis/cancelled COLAS/SOLEILHAC] lignes ea6a28a7(DONNADIEU KOSINSKI) || 14034 [14034 compromis/active COLAS/SOLEILHAC, 14035 offre/accepted COLAS, 14036 vente/None COLAS] lignes 205f62be(COLAS SOLEILHAC)
      dossier 14051 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 14051 [14051 compromis/cancelled DUVERT, 14055 offre/refused DUVERT] lignes 30898aa2(BERNIER FROEYEN WENDLING) || 14052 [14052 compromis/cancelled DUVERT] lignes 4fc6b33a(CHATAIGNIER)
      dossier 14109 : le Sheet ne voit qu'un cote (ou aucun) -- 14109 [14109 compromis/active GENOUX, 14111 compromis/cancelled GENOUX, 14113 offre/refused GENOUX, 14115 vente/None GENOUX] lignes AYIHPHF5(BLANC MOURETTE) Z3DYDC4X(GENOUX) || 14110 [14110 compromis/cancelled GENOUX] lignes -
      dossier 14912 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 14912 [14912 compromis/active FOREL/HUBBARD, 14914 offre/accepted FOREL/HUBBARD, 14916 vente/None FOREL/HUBBARD] lignes XBGMB7XP(FAREL HUBBARD) || 14913 [14913 compromis/cancelled FOREL/HUBBARD] lignes AVXWIZTU(FAVIER PEYRET)
      dossier 16197 : le Sheet ne voit qu'un cote (ou aucun) -- 16197 [16197 compromis/active FRESSENON] lignes - || 16198 [16198 vente/None FRESSENON, 1001578 offre/accepted ] lignes KO6QPUV7(FRESSENON)
      dossier 17131 : le Sheet ne voit qu'un cote (ou aucun) -- 17131 [17131 compromis/cancelled GALLONET] lignes - || 17132 [17132 compromis/active GALLONET, 17133 compromis/cancelled GALLONET, 17134 offre/accepted MASSARDIER, 17135 offre/refused GALLONET, 17137 vente/None GALLONET] lignes 510YKN3L(MASSARDIER) DEZQM9HM(GALLONET)
      dossier 19069 : MEME ACHETEUR des deux cotes -- 19069 [19069 compromis/cancelled POCHELON, 19072 offre/refused POCHELON] lignes 8SZDU4F5(POCHELON) 9HLRYNLE(FANGET) || 19070 [19070 compromis/cancelled POCHELON] lignes 8SZDU4F5(POCHELON)
      dossier 19575 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 19575 [19575 compromis/active PATOUILLARD, 19577 offre/accepted PATOUILLARD, 19579 vente/None PATOUILLARD] lignes WO5IQTLW(PATOUILLARD) || 19576 [19576 compromis/cancelled PATOUILLARD] lignes YQG8CN5T(VALOUR VIALLARD)
      dossier 19736 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 19736 [19736 compromis/active AOMAR, 19738 offre/accepted AOMAR, 19740 vente/None AOMAR] lignes C6XFV1E5(AOMAR) || 19737 [19737 compromis/cancelled AOMAR] lignes 3WBNBNY4(COLLY MONTMARTIN)
      dossier 19814 : le Sheet ne voit qu'un cote (ou aucun) -- 19814 [19814 compromis/cancelled CHEVALLET, 19816 compromis/active CHEVALLET, 19817 offre/accepted CHEVALLET, 19821 vente/None CHEVALLET] lignes MYILWKZQ(CHEVALLET) || 19815 [19815 compromis/cancelled CHEVALLET] lignes -
      dossier 20088 : MEME ACHETEUR des deux cotes -- 20088 [20088 compromis/cancelled DEBARD] lignes 5QE9107L(DEBARD) || 20089 [20089 offre/refused DEBARD, 20090 offre/refused DEBARD] lignes 5QE9107L(DEBARD) ZW7MKTWH(DEBARD)
      dossier 24010 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 24010 [24010 compromis/cancelled CHAMBERY/GRANGEON] lignes 1f3d536a(PALLANDRE RICHARD) || 24011 [24011 compromis/active CHAMBERY/GRANGEON, 24012 offre/accepted CHAMBERY/GRANGEON, 24013 vente/None CHAMBERY/GRANGEON] lignes ccbbf3c8(CHAMBERY GRANGEON)
      dossier 24330 : le Sheet ne voit qu'un cote (ou aucun) -- 24330 [24330 compromis/active BRUGERON/HEYRAUD, 24332 offre/accepted BRUGERON, 24334 vente/None BRUGERON] lignes AD6SMTR5(BRUGERON HEYRAUD) || 24331 [24331 compromis/cancelled BRUGERON/HEYRAUD] lignes -
      dossier 24649 : le Sheet ne voit qu'un cote (ou aucun) -- 24649 [24649 compromis/cancelled MORISON] lignes - || 24650 [24650 compromis/active MORISON, 24651 offre/accepted MORISON, 24654 vente/None MORISON] lignes ESVJUR12(MORISON)
      dossier 26023 : le Sheet ne voit qu'un cote (ou aucun) -- 26023 [26023 compromis/cancelled MUNOZ] lignes - || 26024 [26024 compromis/cancelled MUNOZ, 26025 offre/refused MUNOZ] lignes 0TECT361(MUNOZ)
      dossier 27133 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 27133 [27133 compromis/active ALONSO, 27134 compromis/cancelled ALONSO, 27140 offre/refused ALONSO, 27142 vente/None FARIA/MATOS] lignes 2HOL5ISX(ALONSO) GQCBSQNY(FARIA MATOS) || 27135 [27135 compromis/cancelled ALONSO] lignes JRE23R1G(GENESTAS)
      dossier 28178 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 28178 [28178 compromis/cancelled ESCAILLET] lignes 5a4371b5(MORAINES) || 28179 [28179 compromis/active ESCAILLET, 28180 offre/accepted ESCAILLET, 28181 vente/None ESCAILLET] lignes 5f47de79(ESCAILLET)
      dossier 28546 : MEME ACHETEUR des deux cotes -- 28546 [28546 compromis/cancelled CHIROL/FLEUROT] lignes b42affe7(CHIROL FLEUROT) || 28547 [28547 compromis/active FLEUROT, 28548 offre/accepted FLEUROT, 30762 vente/None FLEUROT] lignes beeaf847(CHIROL FLEUROT)
   ➡ tant que la regle E et les 8 lignes ne sont pas jouees, ces 11 lignes SORTENT de la vague 1

LA GARDE « LA DATE BAT LE NOM » DANS LA REGLE D -- MESUREE SEULEMENT (copie du code hors du depot, rejouee sur le scenario 3 : la nuit des 10 + E + les 8 lignes)
   G1 = un cote a un COMPROMIS VIVANT dont l'acquereur n'est pas dans l'autre cote -> pas de reunion
   G2 = un cote a une OFFRE ACCEPTEE DATEE dont l'acquereur n'est pas dans l'autre cote -> pas de reunion ; G12 = l'une OU l'autre
   la vague 1 de reference = l'etat 5 (patch V2 + E + 8 lignes + C5) : 4081 lignes
   G1   dossiers coupes   19 (dont   13 que le Sheet voit) . reunions nouvelles   0 . VAGUE 1 :   2 etiquette(s) changee(s),   1 ligne(s) qui en sortent -> vague 1 = 4090
        melanges (couche 9, etat 5) : 10 ligne(s) liberee(s), 3 groupe(s) resolu(s) dont 3 coupes EXACTEMENT comme le Sheet le propose ; par famille {'F1': 3}
        lignes SEULES a l'etat 5 qui deviennent PLUSIEURS / PARTAGEE : 1 50LQ2VSA
        vague 1 -- etiquette changee : 50LQ2VSA A6OS2TTJ
        vague 1 -- en sortent : 50LQ2VSA(PLUSIEURS_DOSSIERS)
        LES 19 DOSSIERS COUPES, JUGES PAR LE SHEET : CONFIRMEE (acheteurs differents) 7 . INVISIBLE (aucune ligne du Sheet) 6 . DEMENTIE (une ligne sur deux morceaux) 4 . NEUTRE (un seul morceau a des lignes) 2
           ex. CONFIRMEE (acheteurs differents)           4177 6156 8840 16341 17408 20246 1000125
           ex. DEMENTIE (une ligne sur deux morceaux)     2166 6554 11355 24630
           ex. INVISIBLE (aucune ligne du Sheet)          3486 14419 14460 14471 18675 1000044
           ex. NEUTRE (un seul morceau a des lignes)      4680 17153
        les INVISIBLES par annee (la plus ancienne transaction du dossier) : 2007 3 . 2008 1 . 2009 1 . 2011 1
        les INVISIBLES -- ce qui se DETACHE (le morceau sans la plus petite transaction) : offre(refused) 6
   G2   dossiers coupes  437 (dont  156 que le Sheet voit) . reunions nouvelles   0 . VAGUE 1 :  10 etiquette(s) changee(s),   0 ligne(s) qui en sortent -> vague 1 = 4289
        melanges (couche 9, etat 5) : 214 ligne(s) liberee(s), 98 groupe(s) resolu(s) dont 96 coupes EXACTEMENT comme le Sheet le propose ; par famille {'F1': 93, 'F2': 1, 'F3': 4}
        lignes SEULES a l'etat 5 qui deviennent PLUSIEURS / PARTAGEE : 0 
        vague 1 -- etiquette changee : A6OS2TTJ ANHQ1PK7 JBCC1KBT MFMR0U6A QL70KV8I R9ANL92S SA7DWYEZ SUVPN4BH V5NJER40 WG8CG5T2
        vague 1 -- en sortent : 
        LES 437 DOSSIERS COUPES, JUGES PAR LE SHEET : INVISIBLE (aucune ligne du Sheet) 281 . CONFIRMEE (acheteurs differents) 112 . NEUTRE (un seul morceau a des lignes) 42 . DEMENTIE (une ligne sur deux morceaux) 2
           ex. CONFIRMEE (acheteurs differents)           1059 1228 1265 2449 2633 2641 4125 4131 4177 4480 4500 4508
           ex. DEMENTIE (une ligne sur deux morceaux)     2166 11355
           ex. INVISIBLE (aucune ligne du Sheet)          312 403 483 569 669 709 726 738 768 807 823 831
           ex. NEUTRE (un seul morceau a des lignes)      1242 4342 4495 4720 4796 4823 4850 4868 5021 7895 8941 11194
        les INVISIBLES par annee (la plus ancienne transaction du dossier) : 1990 1 . 2006 2 . 2007 31 . 2008 30 . 2009 24 . 2010 31 . 2011 31 . 2012 29 . 2013 29 . 2014 25 . 2015 19 . 2016 12 . 2017 16 . 2018 1
        les INVISIBLES -- ce qui se DETACHE (le morceau sans la plus petite transaction) : offre(refused) 153 . compromis(cancelled)+offre(refused) 69 . compromis(active)+offre(accepted)+vente(-) 47 . compromis(cancelled)+compromis(cancelled)+offre(refused) 5 . offre(refused)+offre(refused) 3 . compromis(cancelled)+offre(refused)+offre(refused) 1 . compromis(cancelled)+compromis(cancelled)+compromis(cancelled)+offre(refused) 1 . compromis(cancelled) 1 . compromis(active)+offre(accepted)+offre(refused)+vente(-) 1
   G12  dossiers coupes  442 (dont  159 que le Sheet voit) . reunions nouvelles   0 . VAGUE 1 :  11 etiquette(s) changee(s),   1 ligne(s) qui en sortent -> vague 1 = 4288
        melanges (couche 9, etat 5) : 214 ligne(s) liberee(s), 98 groupe(s) resolu(s) dont 96 coupes EXACTEMENT comme le Sheet le propose ; par famille {'F1': 93, 'F2': 1, 'F3': 4}
        lignes SEULES a l'etat 5 qui deviennent PLUSIEURS / PARTAGEE : 1 50LQ2VSA
        vague 1 -- etiquette changee : 50LQ2VSA A6OS2TTJ ANHQ1PK7 JBCC1KBT MFMR0U6A QL70KV8I R9ANL92S SA7DWYEZ SUVPN4BH V5NJER40 WG8CG5T2
        vague 1 -- en sortent : 50LQ2VSA(PLUSIEURS_DOSSIERS)
        LES 442 DOSSIERS COUPES, JUGES PAR LE SHEET : INVISIBLE (aucune ligne du Sheet) 283 . CONFIRMEE (acheteurs differents) 112 . NEUTRE (un seul morceau a des lignes) 43 . DEMENTIE (une ligne sur deux morceaux) 4
           ex. CONFIRMEE (acheteurs differents)           1059 1228 1265 2449 2633 2641 4125 4131 4177 4480 4500 4508
           ex. DEMENTIE (une ligne sur deux morceaux)     2166 6554 11355 24630
           ex. INVISIBLE (aucune ligne du Sheet)          312 403 483 569 669 709 726 738 768 807 823 831
           ex. NEUTRE (un seul morceau a des lignes)      1242 4342 4495 4680 4720 4796 4823 4850 4868 5021 7895 8941
        les INVISIBLES par annee (la plus ancienne transaction du dossier) : 1990 1 . 2006 2 . 2007 31 . 2008 31 . 2009 25 . 2010 31 . 2011 31 . 2012 29 . 2013 29 . 2014 25 . 2015 19 . 2016 12 . 2017 16 . 2018 1
        les INVISIBLES -- ce qui se DETACHE (le morceau sans la plus petite transaction) : offre(refused) 155 . compromis(cancelled)+offre(refused) 69 . compromis(active)+offre(accepted)+vente(-) 47 . compromis(cancelled)+compromis(cancelled)+offre(refused) 5 . offre(refused)+offre(refused) 3 . compromis(cancelled)+offre(refused)+offre(refused) 1 . compromis(cancelled)+compromis(cancelled)+compromis(cancelled)+offre(refused) 1 . compromis(cancelled) 1 . compromis(active)+offre(accepted)+offre(refused)+vente(-) 1

LES MELANGES (couche 9) PAR FAMILLE -- groupes, lignes, et l'etat de la coupe que le Sheet propose :
   F1 le nom de l'ANCIEN acheteur sur une piece VIVANTE du nouveau (le defaut de Hektor)        108 groupes 222 lignes . coupe {'DISPUTEE': 12, 'NETTE': 96} . resolus par la garde {'g1': 3, 'g2': 93, 'g12': 93}
   F2 le nom du NOUVEL acheteur sur la piece de l'ancien (la date du Sheet le dement)            50 groupes  98 lignes . coupe {'A COMPLETER': 1, 'NETTE': 49} . resolus par la garde {'g1': 0, 'g2': 1, 'g12': 1}
   F3 annulee + vivante, la piece porte un autre nom ou aucun                                    10 groupes  21 lignes . coupe {'A COMPLETER': 6, 'NETTE': 4} . resolus par la garde {'g1': 0, 'g2': 4, 'g12': 4}
   F4 que des lignes annulees                                                                    10 groupes  22 lignes . coupe {'A COMPLETER': 1, 'NETTE': 9} . resolus par la garde {'g1': 0, 'g2': 0, 'g12': 0}
   (le detail, groupe par groupe, est dans la colonne « ce_qui_la_debloque » du fichier)

LES LIGNES « SANS DATE » -- elles ont une date, dans l'AUTRE format du Sheet (« 20 fevrier25 »)
   les 803 non ecrites, par forme de la date d'offre : {'jj/mm/aaaa': 631, 'jj mois aa': 162, 'VIDE': 10}
   les 172 qui ne sont pas en jj/mm/aaaa (dont 67 en etiquette partagee), par ANNEE :
      annee    par le Sheet   par nos transactions    dont etiquette partagee
      2011                0                      1                          0
      2012                0                      2                          0
      2014                0                      1                          0
      2017                2                      1                          0
      2018                2                      2                          0
      2019               12                     11                          4
      2020               35                     30                         21
      2021               30                     25                         15
      2022               22                     20                          8
      2023               16                     15                          6
      2024               32                     29                         10
      2025               11                     11                          2
      2026                0                      2                          0
      aucune             10                     22                          1
      les deux sources donnent la MEME annee pour 134 des 145 lignes ou elles existent toutes les deux
   sur TOUT le Sheet : 968 dates d'offre dans l'autre format, 34 vides, 3795 en jj/mm/aaaa

LES LIGNES DU SHEET PAR ANNEE DE L'OFFRE (les deux formats) -- toutes, et les non ecrites :
      annee     total    vague 1 non ecrites     part
      2017          4          1          3      75 %
      2018        305        288         17       6 %
      2019        557        523         34       6 %
      2020        625        505        120      19 %
      2021        786        622        164      21 %
      2022        638        537        101      16 %
      2023        560        483         77      14 %
      2024        485        379        106      22 %
      2025        451        341        110      24 %
      2026        352        291         61      17 %
      aucune       34         24         10      29 %
   2025 + 2026 : 803 lignes au Sheet, dont 171 NON ECRITES (110 en 2025, 61 en 2026)
      ton filtre (le texte « 2025 » ou « 2026 » dans la date d'offre) : 160 non ecrites sur 753 -- il manque les 11 ecrites « jj mois aa »
      les 171 non ecrites 2025-2026, par case : PLUSIEURS_DOSSIERS 87 . SANS_LIEN 23 . ETIQUETTE_PARTAGEE 19 . LIEN_A_VALIDER 16 . GEL_SEUL 12 . PATCH_V2 9 . EN_ATTENTE 5
```
