# Le compte de la question 3 du 19/11 au soir (genere par temps6_les_803_lignes_et_ce_qui_les_debloque_2026-11-19.py)

```
LES 520 LIGNES « PLUSIEURS DOSSIERS » ET « ETIQUETTE PARTAGEE » D'AUJOURD'HUI -- CE QUI LES LIBERE (la premiere couche qui les sort de ces deux cases)
                                                                                      PLUSIEURS  PARTAGEE  TOTAL
   1 la nuit des 10 menages (decidee, joue cette nuit)                                        0         0      0
   2 le patch V2 du gel (ton « vas-y »)                                                       0         0      0
   3 la regle E (ton allumage)                                                                0         0      0
   4 les 8 lignes de 5.6 (ta lecture)                                                         8         0      8
   5 le choix C5 « a l'export » (question posee en ⑥, attend ta reponse)                    102         0    102
   6 relecture du gel (un patch a valider, sans scission)                                    23         4     27
   7 reunir (lignes de rattachement, ta decision ligne a ligne, sans scission)                7         0      7
   8 meme affaire sur plusieurs lignes (doublon du classeur ; contre le point ⑤)              1         8      9
   9 melange -> SCISSION                                                                     78       273    351
   10 non tranche (le juge ne voit pas une des lignes)                                        5        11     16
   TOTAL                                                                                    224       296    520

CE QUE DEVIENNENT LES LIGNES LIBEREES PAR LES COUCHES 1 A 5 (leur case dans cet etat) :
   couche 4 -> VAGUE_1                   8
   couche 5 -> GEL_SEUL                 16
   couche 5 -> VAGUE_1                  86

AU-DELA DE 5 -- LES GROUPES (lignes + dossiers relies) que ces lignes forment :
   6 relecture du gel (un patch a valider, sans scission)                               27 groupes,   27 lignes,   27 dossiers
   7 reunir (lignes de rattachement, ta decision ligne a ligne, sans scission)           7 groupes,    7 lignes,   15 dossiers
   8 meme affaire sur plusieurs lignes (doublon du classeur ; contre le point ⑤)         5 groupes,   10 lignes,    5 dossiers
   9 melange -> SCISSION                                                               172 groupes,  359 lignes,  234 dossiers
   10 non tranche (le juge ne voit pas une des lignes)                                  10 groupes,   20 lignes,   11 dossiers

LES MELANGES (couche 9) -- leur forme :
   SIGNATURE DU DEFAUT                                             104 groupes,  214 de nos lignes
   annulee + vivante, sans transaction au nom de l'annulee          58 groupes,  115 de nos lignes
   que des lignes annulees                                          10 groupes,   22 de nos lignes

ET 20 LIGNES Y ENTRENT apres la nuit et le patch V2 (elles sont ailleurs aujourd'hui) : {'PATCH_V2': 16, 'VAGUE_1': 1, 'SANS_LIEN': 3}

LES LIGNES DE LA VAGUE 1 D'AUJOURD'HUI DONT L'ETIQUETTE CHANGERAIT (la pose garde celle de la plus petite transaction) :
   apres la nuit des 10   :   0 ligne(s) 
   apres + la regle E     :  12 ligne(s) 1c7b38f9 205f62be 5f47de79 86ad8c0f ESVJUR12 KO6QPUV7 MCD6CRNB SC58GWXX SUVPN4BH UY443H27 beeaf847 ccbbf3c8
   apres + les 8 lignes   :  12 ligne(s) 1c7b38f9 205f62be 5f47de79 86ad8c0f ESVJUR12 KO6QPUV7 MCD6CRNB SC58GWXX SUVPN4BH UY443H27 beeaf847 ccbbf3c8

LES 4797 LIGNES DU SHEET, CASE PAR CASE, a chaque etat :
   etat 1 : VAGUE_1 3998 . ETIQUETTE_PARTAGEE 296 . PLUSIEURS_DOSSIERS 224 . LIEN_A_VALIDER 100 . SANS_LIEN 94 . PATCH_V2 39 . GEL_SEUL 23 . EN_ATTENTE 23
   etat 2 : VAGUE_1 3997 . ETIQUETTE_PARTAGEE 307 . PLUSIEURS_DOSSIERS 233 . LIEN_A_VALIDER 112 . SANS_LIEN 74 . AUDIT_NON_JUSTE 28 . GEL_SEUL 23 . EN_ATTENTE 23
   etat 3 : VAGUE_1 3986 . ETIQUETTE_PARTAGEE 321 . PLUSIEURS_DOSSIERS 232 . LIEN_A_VALIDER 110 . SANS_LIEN 74 . AUDIT_NON_JUSTE 28 . GEL_SEUL 23 . EN_ATTENTE 23
   etat 4 : VAGUE_1 3994 . ETIQUETTE_PARTAGEE 321 . PLUSIEURS_DOSSIERS 224 . LIEN_A_VALIDER 110 . SANS_LIEN 74 . AUDIT_NON_JUSTE 28 . GEL_SEUL 23 . EN_ATTENTE 23
   etat 5 : VAGUE_1 4080 . ETIQUETTE_PARTAGEE 342 . LIEN_A_VALIDER 110 . PLUSIEURS_DOSSIERS 101 . SANS_LIEN 74 . GEL_SEUL 39 . AUDIT_NON_JUSTE 28 . EN_ATTENTE 23

LA REGLE E FAIT SORTIR 11 LIGNE(S) DE LA VAGUE 1 (etat 2 -> etat 3) :
   1c7b38f9 (Vente réglée, Mme M. MARTIN Laurent EPARVIER) -> ETIQUETTE_PARTAGEE ; avec d2108609 (Annulée, Mme M. CHOUVELLON Henriette et) ; acheteurs DIFFERENTS
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

LE SHEET JUGE LA REGLE E -- ses 33 reunions, cote par cote (les acquereurs AB des lignes reliees par le gel) :
   le Sheet ne voit qu'un cote (ou aucun)                    18
   LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste  11
   MEME ACHETEUR des deux cotes                               3
   ACHETEURS DIFFERENTS, la ligne annulee DATE un compromis -- E douteuse   1
      dossier 1296 : le Sheet ne voit qu'un cote (ou aucun) -- 1296 [1296 compromis/cancelled BEDRE, 1298 offre/refused BEDRE] lignes NNKTA480(BEDRE) || 1297 [1297 compromis/cancelled BEDRE] lignes -
      dossier 1334 : le Sheet ne voit qu'un cote (ou aucun) -- 1334 [1334 compromis/cancelled THEVENON, 1337 offre/refused THEVENON] lignes JAKQXFWK(FAQRAOUI) || 1335 [1335 compromis/cancelled THEVENON] lignes -
      dossier 3669 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 3669 [3669 compromis/cancelled RUAULT] lignes caea1510(KAMPIRE LAFFONT) || 3670 [3670 compromis/active RUAULT, 3671 offre/accepted RUAULT, 3672 vente/None RUAULT] lignes 86ad8c0f(RUAULT)
      dossier 4125 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 4125 [4125 compromis/active GUERIN, 4127 offre/accepted GIORGETTI, 4129 vente/None GUERIN] lignes FOZ6HZLK(GIORGETTI) || 4126 [4126 compromis/cancelled GUERIN] lignes P252U1JH(CHAPTARD GAIGA)
      dossier 4267 : le Sheet ne voit qu'un cote (ou aucun) -- 4267 [4267 compromis/cancelled LAMBINET] lignes - || 4268 [4268 compromis/cancelled LAMBINET] lignes - || 4269 [4269 compromis/active LAMBINET, 4270 offre/accepted LAMBINET, 4273 vente/None LAMBINET] lignes UY443H27(LAMBINET RESLER)
      dossier 4495 : le Sheet ne voit qu'un cote (ou aucun) -- 4495 [4495 compromis/active GALLOT, 4497 offre/accepted FAUCHEZ/NOIRJEAN, 4499 vente/None GALLOT] lignes EWHVPSCC(FAUCHEZ NOIRJEAN) || 4496 [4496 compromis/cancelled GALLOT] lignes -
      dossier 4649 : le Sheet ne voit qu'un cote (ou aucun) -- 4649 [4649 compromis/cancelled DUVET, 4650 compromis/active DUVET, 4652 offre/accepted OLIVIERI/OSTRE, 4654 offre/refused DUVET, 4656 vente/None BERCOT] lignes 2FOH8HE4(DUVET) VX5RZL6B(OLIVIERI OSTRE) || 4651 [4651 compromis/cancelled DUVET] lignes -
      dossier 4720 : le Sheet ne voit qu'un cote (ou aucun) -- 4720 [4720 compromis/cancelled GARNIER] lignes - || 4721 [4721 compromis/active GARNIER, 4723 offre/accepted , 4724 vente/None GARNIER] lignes SUVPN4BH()
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
      dossier 21520 : ACHETEURS DIFFERENTS, la ligne annulee DATE un compromis -- E douteuse -- 21520 [21520 compromis/cancelled EPARVIER/MARTIN] lignes d2108609(CHOUVELLON) || 21521 [21521 compromis/active EPARVIER/MARTIN, 21522 offre/accepted MARTIN, 21523 vente/None MARTIN] lignes 1c7b38f9(EPARVIER MARTIN)
      dossier 24010 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 24010 [24010 compromis/cancelled CHAMBERY/GRANGEON] lignes 1f3d536a(PALLANDRE RICHARD) || 24011 [24011 compromis/active CHAMBERY/GRANGEON, 24012 offre/accepted CHAMBERY/GRANGEON, 24013 vente/None CHAMBERY/GRANGEON] lignes ccbbf3c8(CHAMBERY GRANGEON)
      dossier 24330 : le Sheet ne voit qu'un cote (ou aucun) -- 24330 [24330 compromis/active BRUGERON/HEYRAUD, 24332 offre/accepted BRUGERON, 24334 vente/None BRUGERON] lignes AD6SMTR5(BRUGERON HEYRAUD) || 24331 [24331 compromis/cancelled BRUGERON/HEYRAUD] lignes -
      dossier 24649 : le Sheet ne voit qu'un cote (ou aucun) -- 24649 [24649 compromis/cancelled MORISON] lignes - || 24650 [24650 compromis/active MORISON, 24651 offre/accepted MORISON, 24654 vente/None MORISON] lignes ESVJUR12(MORISON)
      dossier 26023 : le Sheet ne voit qu'un cote (ou aucun) -- 26023 [26023 compromis/cancelled MUNOZ] lignes - || 26024 [26024 compromis/cancelled MUNOZ, 26025 offre/refused MUNOZ] lignes 0TECT361(MUNOZ)
      dossier 27133 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 27133 [27133 compromis/active ALONSO, 27134 compromis/cancelled ALONSO, 27140 offre/refused ALONSO, 27142 vente/None FARIA/MATOS] lignes 2HOL5ISX(ALONSO) GQCBSQNY(FARIA MATOS) || 27135 [27135 compromis/cancelled ALONSO] lignes JRE23R1G(GENESTAS)
      dossier 28178 : LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste -- 28178 [28178 compromis/cancelled ESCAILLET] lignes 5a4371b5(MORAINES) || 28179 [28179 compromis/active ESCAILLET, 28180 offre/accepted ESCAILLET, 28181 vente/None ESCAILLET] lignes 5f47de79(ESCAILLET)
      dossier 28546 : MEME ACHETEUR des deux cotes -- 28546 [28546 compromis/cancelled CHIROL/FLEUROT] lignes b42affe7(CHIROL FLEUROT) || 28547 [28547 compromis/active FLEUROT, 28548 offre/accepted FLEUROT, 30762 vente/None FLEUROT] lignes beeaf847(CHIROL FLEUROT)
   ➡ tant que la regle E et les 8 lignes ne sont pas jouees, ces 12 lignes SORTENT de la vague 1
```
