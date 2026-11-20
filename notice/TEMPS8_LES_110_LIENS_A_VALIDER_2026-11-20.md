# Les 110 liens « a valider » contre l'audit du 18/11 (genere par temps8_les_110_liens_et_l_audit_du_18_2026-11-20.py, 2026-11-20T11:30)

```
photo du Sheet et du registre : 2026-11-19T20:09:50 ; export temps6 : 2026-11-19T20:09:50
TEMOIN 0 -- le classement recopie redonne l'etat 5 de temps6 : 0 ecart(s) sur 4797 lignes (attendu 0) []
TEMOIN 1 -- la confiance lue LIEN PAR LIEN donne le meme classement : 0 ecart(s) (attendu 0) []
VAGUE 1 -- etat 5 : 4082 lignes ; moins les 9 de B (9) et les 19 du 20/11 (19 lues dans le CSV de temps7) : 4054

LES LIGNES « LIEN A VALIDER » a l'etat 5 : 110 (attendu 110)
   la confiance de leurs liens : {'à valider': 86, 'bonne': 21, 'bonne + sûre': 1, 'sûre + à valider': 2}
   ⚠ « bonne » = un lien AJOUTE par le patch V2 (il ecrit « bonne », pas « sure ») -- la case le compte comme « a valider »

Q1 -- LES LIGNES QUE L'AUDIT DU 18/11 JUGE « JUSTE »
   87 lignes ; confiance de l'audit : {'certaine': 80, 'forte': 7}
   ⭐ CONFIRMEES PAR LES DEUX AUDITS, liens identiques a ceux que le 18/11 garde, rien dans V2 : 85
      dont confiance du 18/11 « certaine » : 79, « forte » : 6
      l'etage du gel qui les avait trouvees : {'9 sans mandat (acquéreur + vendeur)': 73, '9 sans mandat (acquéreur + vendeur) + exclusivité': 10, '10 acquéreur + date (mandat différent) + exclusivité': 1, '9 sans mandat (acquéreur + vendeur) / v2 additif (13/11) : >= 3 familles': 1}
   ⚠ NKDC0I1M (JUSTE/forte) : l'audit du 19/11 dit PARTIEL_NON_PROUVE (CERTAINE)
   ⚠ T47ZI6GS (JUSTE/certaine) : l'audit du 19/11 dit JUSTE mais SOLIDE

Q2 -- LES FAUX, ET CE QUE FAIT LE PATCH V2
   8RWTD0YX : liens d'aujourd'hui [4387] ({'bonne': 1}) ; audit 18/11 : {4385: 'RETIRER', 1001477: 'DEPLACER'}, a rattacher [] ; audit 19/11 : NON_PROUVE+C5_COPIE (SOLIDE) ; V2 : ['retire 4385', 'retire 1001477', 'ajoute 4387 (bonne)']
      raison 18/11 : Le gel a fabrique une offre en double et rattache un compromis annule d'une autre affaire du meme bien ; le vrai dossier est la chaine 4387.
   fa06e4e5 : liens d'aujourd'hui [28931] ({'bonne': 1}) ; audit 18/11 : {28930: 'DEPLACER', 1001553: 'RETIRER'}, a rattacher [] ; audit 19/11 : FAUX (CERTAINE) ; V2 : ['retire 1001553', 'retire 28930', 'ajoute 28931 (bonne)']
      raison 18/11 : Les deux offres du 15/07 tombent au jour pres, mais seule 28931 porte le nom de l'acquereur et sa date de chute ; le compromis cree depuis le Sheet n'a jamais existe.
   le patch V2 touche 65 lignes ; leur verdict du 18/11 : {'PARTIEL': 28, 'FAUX': 11, 'A_RATTACHER': 26}
   leur case a l'etat 5 : {'AUDIT_NON_JUSTE': 28, 'ETIQUETTE_PARTAGEE': 10, 'SANS_LIEN': 6, 'PLUSIEURS_DOSSIERS': 9, 'LIEN_A_VALIDER': 12}
   les 12 FAUX de tout l'audit du 18/11 : V2 en touche 11 ; case a l'etat 5 : {'SANS_LIEN': 6, 'AUDIT_NON_JUSTE': 3, 'LIEN_A_VALIDER': 2, 'EN_ATTENTE': 1}

Q3 -- REBRANCHER L'AUDIT SUR LE GEL (copie) : la vague 1 de reference = 4054 lignes
   A  les 85 JUSTES confirmees passent « sure »
      lignes de la vague 1 dont l'ETIQUETTE changerait : 0 []
      lignes de la vague 1 qui en SORTIRAIENT : 0 []
      lignes qui ENTRERAIENT en vague 1 : 85
      les 110 apres : {'VAGUE_1': 85, 'LIEN_A_VALIDER': 25}
   B  + les 2 autres JUSTES (celles qui ont une reserve)
      lignes de la vague 1 dont l'ETIQUETTE changerait : 0 []
      lignes de la vague 1 qui en SORTIRAIENT : 0 []
      lignes qui ENTRERAIENT en vague 1 : 87
      les 110 apres : {'VAGUE_1': 87, 'LIEN_A_VALIDER': 23}
   C  + TOUT ce que l'audit du 18/11 dit des autres (retirer, deplacer, rattacher)
      lignes de la vague 1 dont l'ETIQUETTE changerait : 0 []
      lignes de la vague 1 qui en SORTIRAIENT : 0 []
      lignes qui ENTRERAIENT en vague 1 : 87
      les 110 apres : {'VAGUE_1': 87, 'LIEN_A_VALIDER': 9, 'AUDIT_NON_JUSTE': 12, 'GEL_SEUL': 2}
   D  la plus large : les lignes « a valider » ou « audit non juste » dont les liens apres V2 sont EXACTEMENT ceux des deux audits : 136 ({'les deux audits': 127, "l'audit du 19/11 seul (CERTAINE)": 9})
      leur case a l'etat 5 : {'LIEN_A_VALIDER': 108, 'AUDIT_NON_JUSTE': 28}
   D  (le verdict du 18/11 compte comme JUSTE quand V2 l'a deja corrige a l'identique)
      lignes de la vague 1 dont l'ETIQUETTE changerait : 0 []
      lignes de la vague 1 qui en SORTIRAIENT : 0 []
      lignes qui ENTRERAIENT en vague 1 : 118
      les 110 apres : {'VAGUE_1': 99, 'GEL_SEUL': 9, 'LIEN_A_VALIDER': 2}
      ⚠ « audit du 19/11 seul » = jamais vue le 18/11 : UN avis independant, pas deux
      reste hors vague 1 : 1eec6575 (etat 5 AUDIT_NON_JUSTE) -> GEL_SEUL ; liens [30825] ; juge : 30825:personne
      reste hors vague 1 : 58I5AO17 (etat 5 LIEN_A_VALIDER) -> GEL_SEUL ; liens [7908, 7909, 7910] ; juge : 7908:personne | 7909:personne | 7910:personne
      reste hors vague 1 : 5e4c8881 (etat 5 AUDIT_NON_JUSTE) -> GEL_SEUL ; liens [30820] ; juge : 30820:personne
      reste hors vague 1 : 70740f2f (etat 5 AUDIT_NON_JUSTE) -> GEL_SEUL ; liens [30824] ; juge : 30824:personne
      reste hors vague 1 : 72GQRHVB (etat 5 LIEN_A_VALIDER) -> GEL_SEUL ; liens [6391, 6392, 6393] ; juge : 6391:personne | 6392:personne | 6393:personne
      reste hors vague 1 : 7IHI7YTJ (etat 5 LIEN_A_VALIDER) -> GEL_SEUL ; liens [4234, 4235, 4236] ; juge : 4234:personne | 4235:personne | 4236:personne
      reste hors vague 1 : A5RW8ZVO (etat 5 LIEN_A_VALIDER) -> GEL_SEUL ; liens [28155] ; juge : 28155:personne
      reste hors vague 1 : CS38OO8R (etat 5 LIEN_A_VALIDER) -> GEL_SEUL ; liens [27984, 27986, 27987] ; juge : 27984:personne | 27986:personne | 27987:personne
      reste hors vague 1 : DHXRAK9O (etat 5 LIEN_A_VALIDER) -> GEL_SEUL ; liens [9370, 9371, 9372] ; juge : 9370:personne | 9371:personne | 9372:personne
      reste hors vague 1 : ESMCO1NC (etat 5 AUDIT_NON_JUSTE) -> GEL_SEUL ; liens [6588, 6589, 6590] ; juge : 6588:personne | 6589:personne | 6590:personne
      reste hors vague 1 : JL8GV7RQ (etat 5 AUDIT_NON_JUSTE) -> GEL_SEUL ; liens [15169, 15170] ; juge : 15169:personne | 15170:personne
      reste hors vague 1 : KAYC29B7 (etat 5 LIEN_A_VALIDER) -> GEL_SEUL ; liens [27170] ; juge : 27170:personne
      reste hors vague 1 : O8BY6AC8 (etat 5 LIEN_A_VALIDER) -> GEL_SEUL ; liens [1000105, 1000141] ; juge : 1000105:personne | 1000141:personne
      reste hors vague 1 : S8BKB6FL (etat 5 LIEN_A_VALIDER) -> GEL_SEUL ; liens [4412, 4413, 4414] ; juge : 4412:personne | 4413:personne | 4414:personne
      reste hors vague 1 : TR42PT5H (etat 5 AUDIT_NON_JUSTE) -> GEL_SEUL ; liens [27195] ; juge : 27195:personne
      reste hors vague 1 : a2abd36c (etat 5 AUDIT_NON_JUSTE) -> GEL_SEUL ; liens [30713, 30827] ; juge : 30713:personne | 30827:personne
      reste hors vague 1 : b43e76f5 (etat 5 AUDIT_NON_JUSTE) -> GEL_SEUL ; liens [30826] ; juge : 30826:personne
      reste hors vague 1 : b884cbd4 (etat 5 AUDIT_NON_JUSTE) -> GEL_SEUL ; liens [30821] ; juge : 30821:personne
   E  D + « gel seul » leve pour ces 136 lignes (deux audits valent le juge)
      lignes de la vague 1 dont l'ETIQUETTE changerait : 0 []
      lignes de la vague 1 qui en SORTIRAIENT : 0 []
      lignes qui ENTRERAIENT en vague 1 : 136
      les 110 apres : {'VAGUE_1': 108, 'LIEN_A_VALIDER': 2}
   TEMOIN POSITIF -- un lien seme de 019X1RO0 vers la transaction 28784 de 009c70c1 (vague 1) : 009c70c1 devient ETIQUETTE_PARTAGEE -> VU

LE RESTE -- 25 lignes sur 110 (les autres sont confirmees par deux audits independants)
   par verdict du 18/11 : {'JAMAIS_VUE': 9, 'PARTIEL': 1, 'A_RATTACHER': 9, 'FAUX': 2, 'JUSTE_SANS_PREUVE_FORTE': 2, 'JUSTE': 2}
   0TECT361 nan MUNOZ                18/11 JAMAIS_VUE/ · 19/11 JUSTE/CERTAINE · liens [26024, 26025] {'bonne': 2} · V2 - · apres C : LIEN_A_VALIDER
   3S4ZWOFK nan DI FORTI ROLLAND     18/11 PARTIEL/certaine · 19/11 C5_COPIE/SOLIDE · liens [11956, 11958, 11960] {'sûre': 2, 'bonne': 1} · V2 ['retire 1001580', 'ajoute 11958 (bonne)'] · apres C : AUDIT_NON_JUSTE
   50OUISUB nan SCARAMUZZI REVRET    18/11 JAMAIS_VUE/ · 19/11 JUSTE/CERTAINE · liens [23037] {'bonne': 1} · V2 - · apres C : LIEN_A_VALIDER
   58I5AO17 nan D'AMARIO             18/11 A_RATTACHER/certaine · 19/11 SANS_LIEN_GEL/A_RATTACHER/SOLIDE · liens [7908, 7909, 7910] {'bonne': 3} · V2 ['ajoute 7909 (bonne)', 'ajoute 7908 (bonne)', 'ajoute 7910 (bonne)'] · apres C : AUDIT_NON_JUSTE
   72GQRHVB nan DELAUNAY             18/11 A_RATTACHER/certaine · 19/11 SANS_LIEN_GEL/A_RATTACHER/SOLIDE · liens [6391, 6392, 6393] {'bonne': 3} · V2 ['ajoute 6392 (bonne)', 'ajoute 6391 (bonne)', 'ajoute 6393 (bonne)'] · apres C : AUDIT_NON_JUSTE
   7IHI7YTJ nan BONNEFOI             18/11 A_RATTACHER/forte · 19/11 SANS_LIEN_GEL/A_RATTACHER/SOLIDE · liens [4234, 4235, 4236] {'bonne': 3} · V2 ['ajoute 4235 (bonne)', 'ajoute 4234 (bonne)', 'ajoute 4236 (bonne)'] · apres C : AUDIT_NON_JUSTE
   8RWTD0YX nan VAN ROSSUM           18/11 FAUX/forte · 19/11 NON_PROUVE+C5_COPIE/SOLIDE · liens [4387] {'bonne': 1} · V2 ['retire 4385', 'retire 1001477', 'ajoute 4387 (bonne)'] · apres C : AUDIT_NON_JUSTE
   A5RW8ZVO nan LESAULT              18/11 JUSTE_SANS_PREUVE_FORTE/forte · 19/11 JUSTE/SOLIDE · liens [28155] {'à valider': 1} · V2 - · apres C : GEL_SEUL
   CS38OO8R nan KAEY                 18/11 A_RATTACHER/forte · 19/11 SANS_LIEN_GEL/A_RATTACHER/SOLIDE · liens [27984, 27986, 27987] {'bonne': 3} · V2 ['ajoute 27986 (bonne)', 'ajoute 27984 (bonne)', 'ajoute 27987 (bonne)'] · apres C : AUDIT_NON_JUSTE
   D4GZG5QI nan CONTE                18/11 JAMAIS_VUE/ · 19/11 JUSTE/CERTAINE · liens [25752] {'bonne': 1} · V2 - · apres C : LIEN_A_VALIDER
   DHXRAK9O nan CHARVOLIN VALLENTIN  18/11 A_RATTACHER/forte · 19/11 SANS_LIEN_GEL/A_RATTACHER/SOLIDE · liens [9370, 9371, 9372] {'bonne': 3} · V2 ['ajoute 9371 (bonne)', 'ajoute 9370 (bonne)', 'ajoute 9372 (bonne)'] · apres C : AUDIT_NON_JUSTE
   JL6I6JDG nan LECLERC              18/11 JAMAIS_VUE/ · 19/11 JUSTE/CERTAINE · liens [4633] {'bonne': 1} · V2 - · apres C : LIEN_A_VALIDER
   KAYC29B7 nan ROMEUF GALVAING      18/11 A_RATTACHER/certaine · 19/11 SANS_LIEN_GEL/A_RATTACHER/SOLIDE · liens [27170] {'bonne': 1} · V2 ['ajoute 27170 (bonne)'] · apres C : AUDIT_NON_JUSTE
   M2G1Z1K8 nan SAS 2511 INVEST Heyr 18/11 JUSTE_SANS_PREUVE_FORTE/forte · 19/11 QUESTION_BIEN/CERTAINE/BIEN_SANS_TRANSACTION · liens [16829] {'à valider': 1} · V2 - · apres C : GEL_SEUL
   MDOXOBIC nan BERTHAUT             18/11 A_RATTACHER/certaine · 19/11 SANS_LIEN_GEL/A_RATTACHER/SOLIDE · liens [2163, 2164, 2165] {'bonne': 3} · V2 ['ajoute 2164 (bonne)', 'ajoute 2163 (bonne)', 'ajoute 2165 (bonne)'] · apres C : AUDIT_NON_JUSTE
   NKDC0I1M nan DUMEIL DUCHAMP       18/11 JUSTE/forte · 19/11 PARTIEL_NON_PROUVE/CERTAINE · liens [27740, 27741, 27742] {'à valider': 2, 'sûre': 1} · V2 - · apres C : VAGUE_1
   O8BY6AC8 nan SCI 2NBD             18/11 A_RATTACHER/forte · 19/11 SANS_LIEN_GEL/A_RATTACHER/CERTAINE · liens [1000105, 1000141] {'bonne': 2} · V2 ['ajoute 1000105 (bonne)', 'ajoute 1000141 (bonne)'] · apres C : AUDIT_NON_JUSTE
   PJ7OXF0X nan GONZALES             18/11 JAMAIS_VUE/ · 19/11 JUSTE/CERTAINE · liens [4790] {'bonne': 1} · V2 - · apres C : LIEN_A_VALIDER
   S8BKB6FL nan JOHN                 18/11 A_RATTACHER/certaine · 19/11 SANS_LIEN_GEL/A_RATTACHER/SOLIDE · liens [4412, 4413, 4414] {'bonne': 3} · V2 ['ajoute 4413 (bonne)', 'ajoute 4412 (bonne)', 'ajoute 4414 (bonne)'] · apres C : AUDIT_NON_JUSTE
   SNDD1833 nan MOUGENOT             18/11 JAMAIS_VUE/ · 19/11 JUSTE/CERTAINE · liens [4401, 4402, 4403] {'bonne': 3} · V2 - · apres C : LIEN_A_VALIDER
   T47ZI6GS nan MAIRIE ESTIVAREILLE  18/11 JUSTE/certaine · 19/11 JUSTE/SOLIDE · liens [22149, 22150] {'à valider': 2} · V2 - · apres C : VAGUE_1
   WG029IGN nan FOUET                18/11 JAMAIS_VUE/ · 19/11 JUSTE/CERTAINE · liens [27052] {'bonne': 1} · V2 - · apres C : LIEN_A_VALIDER
   XMOGLM8G nan COLLARD              18/11 JAMAIS_VUE/ · 19/11 JUSTE/CERTAINE · liens [14229, 14230, 14231] {'bonne': 3} · V2 - · apres C : LIEN_A_VALIDER
   f9b55f79 Mme M. GENILLIER Adrien  18/11 JAMAIS_VUE/ · 19/11 JUSTE/CERTAINE · liens [14823] {'bonne': 1} · V2 - · apres C : LIEN_A_VALIDER
   fa06e4e5 M. BILDINICI Ihsam       18/11 FAUX/forte · 19/11 FAUX/CERTAINE · liens [28931] {'bonne': 1} · V2 ['retire 1001553', 'retire 28930', 'ajoute 28931 (bonne)'] · apres C : AUDIT_NON_JUSTE

CSV : TEMPS8_LES_110_LIENS_A_VALIDER_2026-11-20.csv (110 lignes)
VERDICT DES TEMOINS : VERTS
```
