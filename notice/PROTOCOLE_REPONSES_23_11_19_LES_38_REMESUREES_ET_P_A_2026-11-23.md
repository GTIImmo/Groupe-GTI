L3 · chantier classeur · ㉒ · 23/11 au soir : tes points 2 à 5. J'ai refait les mesures qui fondaient les 38, mis de côté les deux affaires non saisies, et le préalable P-a est expliqué. Rien n'est écrit (ni base, ni Sheet, ni Hektor), rien n'est tiré, rien n'est poussé.

# Les 38 remesurées, et le préalable P-a

Carnet : § 20.35. Passage de référence : 75 (v18).

Outils, tous en lecture seule :
- `phase2/checks/protocole_les_38_remesurees_2026-11-23.py` ;
- `phase2/checks/protocole_les_introuvables_du_rejeu_2026-11-23.py` ;
- `phase2/checks/protocole_portes.py` (le rejeu exact).

Témoin de l'outil : chaque bien rejugé en mémoire redonne le passage 73 ligne par ligne, sur les 95 lignes jugées. Aucun écart.

## 1. Les deux affaires non saisies : mises de côté (ton point 2)

- **130d81ac** : bien 62503, mandat 18728.
- **a8aaeb2b** : bien 61592, mandat 18398.

Le motif reste « rien à étiqueter », donc hors du reste à vider. Le texte dit maintenant : « AFFAIRE NON SAISIE (pas introuvable) », avec le numéro de mandat, les dates du mandat, « ni chez Hektor ni dans l'app », et « rejugée à chaque passage ».

Ce n'est pas un verdict figé. Le texte ne joue que tant que le bien n'a aucune pièce.

Témoin : j'ai prêté en mémoire une pièce au bien 62503. La ligne 130d81ac passe alors l'épreuve E2 et elle est jugée par les épreuves ordinaires. Elle rentrera donc seule dès que la saisie sera faite.

Passage 74 contre 73 : 0 verdict rendu ne bouge, 0 motif ne change, seuls ces deux textes changent.

## 2. Tes 20 pièces à part : la mesure du 21/11, refaite sur l'état d'aujourd'hui

**La mesure d'alors**, retrouvée dans son code (`temps12_v3_fabriquer`) : une pièce à part est « neutre » quand elle n'est la plus petite d'aucun morceau où elle pourrait aller, les dates étant compatibles. C'est ton critère 2.

⚠ Ce que le code d'alors faisait aussi : une pièce qui n'a aucun morceau possible était comptée « non neutre » par défaut. Elle entrait donc dans les 20 sans déplacer d'étiquette.

**Aujourd'hui**, j'applique la même fonction aux morceaux de la coupe finale du protocole, avec toutes les règles validées. J'y ajoute la pose de nuit simulée, qui dit quelle étiquette bouge vraiment et pour quelle ligne.

**Témoin : les 20 neutres du 22/11.**
- 17 restent neutres.
- 3 ont été données depuis par des règles validées : 4544 à 40ELE6SQ, 23054 à SBH4QWDW, 27556 à XHITO8HE.
- 0 divergence.

**Les 15 qui déplacent encore une étiquette** :
- 3741, 4126, 4327, 4533, 4542, 4560, 4621, 4669, 7710 ;
- 14110, 16382, 20088, 21520, 26613, 28116.

Pour chacune, il existe au moins un morceau possible où elle serait la plus petite. La pose simulée y change bien l'étiquette. Exemples :
- 4621 ferait passer 0EMKY4ZS de D2021-0282 à D2020-0462 ;
- 21520 ferait passer 1c7b38f9 de D2025-0263 à D2025-0427 ;
- 4126 ferait passer P252U1JH de D2021-0567 à D2020-0592.

Trois d'entre elles sont déjà mises de côté avec leur dossier par R7c, une règle validée : 16382, 26613 et 28116.

**Les 5 pour qui c'est non :**
- **1059, 24600 et 27512** n'ont aucun morceau possible, ni le 21/11 ni aujourd'hui. Elles étaient dans les 20 « par défaut ». Leur place ne déplace rien.
- **24124** est bien la plus petite du morceau de 305KAY9W, mais elle est déjà dans son dossier (R7a). La pose simulée ne bouge rien.
- **14033** n'est plus à part : ta décision B l'a donnée à DONNADIEU.

**Ce que ça change.** J'ai sorti les 4 encore à part des 20, en mémoire. Aucun verdict ne bouge sur leurs 4 biens : toutes leurs lignes sont déjà tranchées, et les 4 pièces restent à part sans morceau.

Elles n'ont donc plus de raison d'être à part, et ça ne coûte rien. À l'écriture, elles seront traitées comme les 19 qui attendent : on ne paie pas de dette pour elles. Je ne touche pas la liste dans le code, parce qu'elle sert de témoin.

**Les 26 lignes** sont toutes retenues par 14 des 15 pièces qui déplacent encore une étiquette. La mesure d'aujourd'hui refonde donc leur place sur la liste : aucune des pièces libérées ne retient une ligne.

## 3. Les 5 affaires sur un autre bien : la preuve, et le rattachement simulé

**Le constat commun aux cinq.**
- Chacune est une vente réglée.
- Le Sheet la met sur un bien par sa colonne « Mandat », et souvent aussi par le Lien CRM. Ce bien n'a aucune pièce.
- Le bien réel porte un dossier complet : son compromis tombe au jour exact sur la case « Compromis », ses honoraires sont la commission de la ligne, et le vendeur de la ligne est parmi ses mandants. Sa vente tombe au jour sur « Vente Fixée ».
- Le bien réel n'a aucune ligne au Sheet aujourd'hui. Aucune de ses pièces n'est tenue par une ligne, ni au gel ni au passage.

**2U5QPKRC** (ligne 3323, mandat 5030, nommée sur le bien 51585) : la preuve est sur le bien 37875.
- Compromis 17769 du 03/07/2018 : 95 000 €, honoraires 6 800.
- Vente 17770 du 14/12/2018.
- Rattachée : tranchée au numéro D2018-0271 (existant), pièces 17769 et 17770.

**EJN79TJ1** (ligne 2485, mandat 12234, nommée sur le bien 19637) : la preuve est sur le bien 53953.
- Offre 27713 du 27/02/2020 et compromis 27712 du 03/06/2020 : 213 000 €, honoraires 13 000.
- Vente 27714 du 04/09/2020.
- Rattachée : D2020-0110, avec les 3 pièces. Le Prix « 42 » du Sheet est faux.

**MQ6H8TVQ** (ligne 3383, mandat 8644, nommée sur le bien 45938 par le seul mandat) : la preuve est sur le bien 52460.
- Offre 26696 du 14/12/2017 et compromis 26695 du 27/12/2017 : 38 000 €, honoraires 1 000.
- Vente 26698 du 06/07/2018.
- Rattachée : D2017-0313, avec ces 3 pièces. L'offre refusée 26697 du 29/06/2017 n'est pas à elle : elle reste à part, sans effet.

**QXDW8EQA** (ligne 2559, mandat 13411, nommée sur le bien 24464) : la preuve est sur le bien 2070.
- Offre 1028 du 11/01/2020 et compromis 1027 du 29/05/2020 : 1 358 840 €, honoraires 39 000.
- Vente 1029 du 04/11/2020.
- Rattachée : D2020-0014, avec les 3 pièces.

**91IHSGNC** (ligne 2780, mandat 611, nommée sur le bien 1223) : la preuve est sur le bien 10229.
- Compromis 4781 du 18/09/2019 : 44 900 €, honoraires 4 900.
- Vente 4783 du 18/12/2019, au jour sur « Vente Prévue » et « Vente Fixée ».
- Rattachée : D2019-0311, pièces 4781 et 4783. L'offre 4782 du 04/07/2019, à 3 jours de sa case, reste à part, sans effet.

**Les deux colonnes, pour les cinq :**
- **Quel numéro** : chacune prend le numéro existant du dossier de son bien réel. Aucune ne reçoit un numéro neuf. Aucune n'est parmi les 2 560, donc il n'y a pas de numéro du 16/11 à perdre.
- **Quelle étiquette bouge, qui perd quoi** : rien. J'ai rejugé en mémoire le bien réel et le bien nommé : aucune autre ligne ne change. Aucune pièce n'est prise à une autre ligne.

Ce qui reste, c'est ta décision de changer le bien de la ligne, comme pour I3TFR2KG.

## 4. Les deux paires écartées de R13

⚠ **Une précision sur leur origine**, d'après le carnet (§ 20.27) :
- **E9XL0N5B** a été sortie par ton mot du 23/11 : « R13 : OUI, MAIS SUR TROIS PAIRES, PAS QUATRE. SORS E9XL0N5B ».
- **IAYQ5OG2** a été sortie par ma vérification, celle que ce même mot demandait : « vérifie que tes 3 paires sont bien des doublons ».

**Les faits, bien 48145.**
Hektor porte une seule affaire :
- offre 24441 du 07/07/2020, 149 400 € ;
- compromis 24440 du 30/07/2020, 149 400 €, honoraires 9 400 ;
- vente 24442 du 26/10/2020.

Les deux lignes :
- **DTZ227ER** : vente réglée, commission 9 400. Ses dates d'offre, de compromis et de vente fixée tombent au jour.
- **E9XL0N5B** : annulée le 20/07/2020, commission 10 400. Elle porte les mêmes cases d'offre et de compromis, donc un compromis daté après sa propre annulation. Le même acquéreur, avec les deux noms dans l'autre ordre.

Les honoraires de la seule affaire (9 400) sont ceux de DTZ227ER. Aucune pièce ne porte 10 400.

**Les faits, bien 9705.**
Hektor porte une seule affaire :
- offre 4446 du 10/12/2021, 20 000 € ;
- compromis 4445 du 28/03/2022, honoraires 3 500 ;
- vente 4447 du 08/06/2022.

Les deux lignes :
- **L597FO6M** : vente réglée. Ses dates de compromis et de vente fixée tombent au jour.
- **IAYQ5OG2** : annulée le 01/02/2022. Elle porte un compromis au 24/02/2022, après sa propre annulation, et Hektor n'en a aucun à cette date. Même acquéreur, même prix, même commission.

**Ce qu'il faudrait pour les trancher.**
Dans chaque bien, une seule affaire existe chez Hektor. Toutes les dates au jour et les honoraires désignent la ligne réglée. La ligne annulée n'a aucune pièce à elle.

La seule question qui reste ouverte est : une affaire écrite deux fois, ou deux affaires dont la première n'a laissé aucune pièce ? Elle ne change pas le verdict. Dans les deux cas, la réglée prend le dossier et l'annulée n'a rien à étiqueter.

Simulé en mémoire :
- DTZ227ER → D2020-0274, hors des 2 560 ; E9XL0N5B : rien à étiqueter.
- L597FO6M → D2021-0711, **exactement son numéro du 16/11** ; IAYQ5OG2 : rien à étiqueter.
- Rien d'autre ne bouge.

**Pourquoi ce n'est pas à moi.** La règle qui les prendrait seule est celle que tu as refusée le 23/11 : « une règle n'avale pas son propre écart ; deux affaires → exception NOMMÉE, jamais implicite ». Il faut donc ton exception nommée : une phrase par paire.

## 5. Le bien 39845 : la vue

**Les trois pièces**, un seul dossier, D2023-0189 (chaîne 19131). Aucune n'est tenue par une ligne au passage.
- **Offre 19132** : 87 000 €, acceptée, du 19/04/2023. Elle tombe au jour sur la case « Offre Achat » de V3FO5NDA.
- **Compromis 19131** : 80 000 €, du 08/12/2023, honoraires 6 000. Sa date tombe au jour sur la case « Compromis » de 6FQO29C8. Ses 6 000 sont la commission de 6FQO29C8, et aussi celle de SOF45TS3.
- **Vente 19133** : 80 000 €, du 04/06/2024. Elle tombe au jour sur la case « Vente Fixée » de 6FQO29C8.

**En face, trois lignes, pas deux :**
- **V3FO5NDA** (ligne 3632, acquéreur BAUDOIN PETIPAS, mandat 15459) : annulée le 23/06/2023, offre du 19/04/2023, commission 7 000.
- **6FQO29C8** (ligne 589, acquéreur POCHELON, mandat 16263) : vente réglée, compromis du 08/12/2023, vente fixée au 04/06/2024, réglée le 11/06/2024, commission 6 000.
- **SOF45TS3** (ligne 3587, acquéreur DIGONNET, mandat 15920) : annulée le 23/09/2023, aucune date, commission 6 000. Elle est rattachée par le seul Lien CRM.

**Le rappel que tu demandais.** Le gel tient les trois pièces à V3FO5NDA, « à valider », à l'étage 9, « sans mandat (acquéreur + vendeur) ». Je l'ai relu dans la copie locale de `app_classeur_lien`. Elles sont donc rangées par les NOMS.

Chez Hektor, les trois pièces portent le nom BAUDOIN ET PETIPAS. C'est le contact du premier acheteur, que Hektor recopie sur les pièces suivantes. C'est pour ça que tu voulais les voir.

## 6. Le préalable P-a : les signaux « transaction introuvable », expliqués

**Ce que dit le rejeu exact du passage 73.** Je l'ai fait d'abord, et il n'était pas vert :
- 3 signaux « [X] détachement : transaction introuvable » ;
- 2 lignes tranchées pas justes à l'arrivée : 3THZJOOG et f1aedc01.

Il avait d'abord planté : l'outil ne savait pas lire la phrase de preuve de R21. C'est corrigé dans l'outil, en lecture seule.

**Les trois signaux, nommés un par un.** J'ai rejoué le même module, avec une seule ligne d'espion. Ce sont trois compromis annulés SANS DATE :
- 4496 (bien 9769) ;
- 4720 (bien 10129) ;
- 26613 (bien 52166).

**La cause.** Tous trois sont dans la liste `EXCLUES_DE_LA_REGLE_E`, par tes décisions des 19 et 20/11 : « on met de côté, on ne tranche pas ».

Une transaction sans date exclue de la règle E, et seule dans sa chaîne, n'entre jamais dans la liste des dossiers du bien. Le fichier des coupes ne la trouve donc pas, et il ignore le morceau entier.

Les deux signaux du passage 26 sont 4496 et 26613 : ce sont les deux seules lignes du brouillon de ce passage qui les portent. Mon hypothèse du 22/11, l'ordre des coupes dans le bien 52166, était fausse. Ta piste, ce qui est lu au départ, était la bonne.

**Ce qu'ils faisaient** :
- **4496 et 26613** : ce sont des mises de côté (R7b/R7c) d'une pièce seule. Elle est déjà seule à son numéro, et l'arrivée est juste. Mais la ligne du fichier aurait crié chaque nuit. L'outil ne l'écrit plus, comme pour les pièces supprimées chez Hektor.
- **4720** : R19 l'avait donnée à **3THZJOOG** le 23/11, par élimination. La nuit ne peut pas la réunir à son offre 4722, donc le verdict était irréalisable. Et 4720 est une pièce que tu avais mise de côté le 20/11.

**La correction, v18, passage 75.** Une épreuve E9 de plus, sur le modèle de PIECE_SUPPRIMEE_FIGEE. Si une ligne tient une pièce sans date invisible à la nuit et que ses pièces sont dans plusieurs dossiers, elle passe en attente avec le motif PIECE_SANS_DATE_INVISIBLE.

Passage 75 contre 74 :
- **un verdict rendu bouge, et un seul : 3THZJOOG**, de tranchée à en attente. Elle n'est pas parmi les 2 560.
- La vente SUVPN4BH garde D2021-0323, son numéro du 16/11.
- Les témoins sont identiques : 788 sur 788, les mêmes 19 écarts.
- Le reste à vider passe de 53 à 54.

C'est le même geste que celui de la v2 du 22/11 : le rejeu exact trouve un verdict que la nuit ne peut pas réaliser, et il le reprend.

**La deuxième ligne pas juste, f1aedc01, n'avait rien de faux.** Son dossier D2026-0260 garde l'offre 28967, supprimée chez Hektor. C'est la trace d'une saisie refaite : 78 500 €, le même jour, deux minutes après l'offre 28966. R14 la sort du morceau et la laisse figée dans son ancien dossier, et cet ancien dossier est ici celui de la ligne.

C'est l'outil de mesure qui ne savait pas lire R14. Il compte maintenant cette trace comme neutre.

**Le rejeu exact du passage 75** : **vert**.
- 0 signal « transaction introuvable » : le compte rendu ne porte plus que « décidé à la main » 436 et « déjà obtenu » 169.
- 4 689 lignes tranchées sur 4 689 sont justes à l'arrivée.
- L'étiquette exacte est retrouvée sur 4 689 lignes sur 4 689.
- Les 19 dossiers mis de côté sont seuls à l'arrivée et gardent leur ancien numéro. 6 d'entre eux sont déjà figés par le chaînage, dont 4496 et 26613.
- 0 pièce ne bouge hors des biens tranchés.

Un avertissement reste, et je le nomme : 2 lignes en attente voient bouger leur dossier, **RGCEC677** et **Z3DYDC4X**. Ce sont deux lignes du verrou retenues par tes pièces à part 4542 et 14110. La coupe en retire leurs voisines tranchées (Z0BDVNBZ, AYIHPHF5), et elles restent avec le reste de l'ancien dossier. Ce sont les mêmes deux qu'au passage 73. Au passage 26, il y en avait quatre.

## 7. Ta réserve sur app_chaine_id (ton point 4)

Notée : c'est un préalable, plus un blocage. Elle reste à confirmer sur une nuit agitée, comme celle du 21/11 et ses 31 fusions.

## Où en sont les préalables

- **P-a** : expliqué, et corrigé (v18).
- **P-e** (le rejeu exact sur l'état d'arrivée) : **vert au passage 75**. Les deux lignes qu'on n'expliquait pas sont expliquées, et le rejeu est refait sur les règles du jour. Il est à refaire sur l'état exact de la première vague, juste avant l'écriture.
- **P-b** (les lignes tranchées par le seul mandat) : à faire.
- **P-c** : hors de toute vague d'écriture, les 5 affaires sur un autre bien, les 3 lignes de 39845 et I3TFR2KG, tant que tu ne les as pas tranchées. Les deux paires s'y ajoutent.
- **P-d** (la vraie sauvegarde juste avant la première écriture) : au moment de l'écriture.
- **P-f** (app_chaine_id) : allégée par ta mesure ; reste une nuit agitée.

## Ce qui attend ta décision

1. Les 5 affaires sur un autre bien : changer le bien de la ligne, oui ou non, une par une. La preuve et le coût sont au § 3 : rien ne bouge ailleurs.
2. Les deux paires : ton exception nommée, une phrase par paire (§ 4).
3. Le bien 39845 : ta lecture (§ 5).
