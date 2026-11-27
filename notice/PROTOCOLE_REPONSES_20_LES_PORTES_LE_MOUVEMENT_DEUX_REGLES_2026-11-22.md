# Le protocole, après tes réponses au rapport ⑳ : les portes, le mouvement, deux règles à juger (22/11/2026)

> L3 · chantier classeur · ⑳ · 22/11 après-midi · ⛔ **rien d'écrit** : rien dans ton Sheet, chez Hektor ou en base,
> aucun run. Tout est mesuré sur l'**image du 22/11 à 12:42**. Le **vrai code du chaînage** (affaire_ledger.py) est
> rejoué sur une **copie en mémoire** du registre de l'image.
>
> Les fichiers :
> - `notice/PROTOCOLE_PASSAGE_13_LA_PORTE_DE_CHAQUE_LIGNE_2026-11-22.csv` : une ligne par ligne tranchée, avec sa porte,
>   ses pièces de trop, son gel d'aujourd'hui et d'arrivée, son étiquette d'aujourd'hui et d'arrivée ;
> - `notice/PROTOCOLE_REGLES_R7A_R7B_LES_38_LIGNES_MESUREES_2026-11-22.csv` : les 38 lignes que les deux règles
>   proposées libèrent ;
> - `notice/PROTOCOLE_DJEBBOUR_TES_TROIS_LIGNES_COTE_A_COTE_2026-11-22.md` : tes trois lignes de DJEBBOUR.

## 1. Tes cinq réponses, appliquées

**P1 : appliquée, puis TOUT rejoué** (passage 10, puis 13 sur l'image de 12:42).
- **59 verdicts changent, dont 0 déjà rendu** : 57 lignes passent tranchées, 1 passe au verrou, 1 passe en « copie
  seule ».
- **Aucun écart neuf** dans les témoins.
- Chaque ligne tranchée par P1 porte sa preuve écrite : « son bien X par la règle P1 (gel + mandat) ; écarté : Y
  (product_ref seul) ».

**Les 106 : gardées en attente.** P1 en a ajouté une, elles sont donc **107**. Je les ai lues par motif : deux règles
en sortent (§ 5). Je ne les ai pas appliquées.

**DJEBBOUR** : tes trois lignes sont côte à côte dans le document à part, sans rien trancher.
- **Tu as écrit deux noms, pas trois** : « HUGON COTTIN » (ligne 3575, 2023), puis « DJEBBOUR » (3461, 2024) et
  « M. DJEBBOUR Jacques » (155, 2025).
- Chaque date de Hektor tombe au jour exact sur une seule case d'une seule de tes lignes.
- Hektor a **six** pièces sur ce bien, pas cinq. La sixième est l'offre **14943**, refusée, du 03/07/2023 : elle tombe
  sur la case « Offre Achat » de ta ligne 3575.

**Ton 4 794 contre mon 4 798 : l'écart est expliqué en entier, mais pas comme tu le pensais.**
- **Tes cinq lignes 3541 · 3693 · 3837 · 4019 · 4070 sont entièrement vides dans ton classeur en direct**, de A à AL.
  Aucune n'a d'identifiant aujourd'hui.
- **Les 4 de plus sont quatre lignes NEUVES, 4801 à 4804**, venues après la copie en base. La copie s'arrête à la
  ligne 4800. Les quatre sont des offres :
  - 54376c72, Offre Achat 11/11/2026, mandat 18993 ;
  - ffcf30e6, 21/10/2026, mandat 18996 ;
  - b72db9d5, 10/11/2026, mandat 18950 ;
  - 55b49232, 19/11/2026, mandat 18973.
- **Les 4 794 identifiants de la copie en base sont tous dans ton classeur, chacun sur le même numéro de ligne**
  (0 différence).
- Le compte : copie de 2 à 4800, moins tes 5 lignes vides, font 4 794 ; ton classeur de 2 à 4804, moins les mêmes 5,
  font 4 798.
- Côté protocole, trois des quatre lignes neuves sont tranchées. La 4801 (mandat 18993) ne nomme encore aucun bien
  chez nous.

**« Rien ne s'écrit » = rien de nouveau : noté. Et ton obligation est tenue : la mesure du matin existe.**
- `protocole_classeur.py mouvement` compare deux images et dit ce qui a bougé entre elles :
  - dans ton Sheet : les lignes nouvelles et disparues, et chaque case lue qui a changé ;
  - dans le registre : chaque pièce, champ par champ (bien, genre, état, date, montant, numéro Hektor, présence,
    mandat, origine, chaîne, étiquette, acquéreurs) ;
  - dans le gel : chaque lien ajouté ou retiré ;
  - et la liste des biens qui ont bougé.
- **`comparer` entre deux images partage chaque verdict changé** : sur une ligne ou un bien que la nuit a déplacé,
  ou sans aucun mouvement de la nuit, donc venu du code.
- **Témoin positif** : j'ai semé trois changements dans une copie d'image (une case, un état, un lien du gel, plus une
  pièce retirée). La mesure les retrouve tous et rien d'autre.
- **Première mesure, de 10:44 à 12:42 : 0 mouvement**, et le passage rejoué sur la nouvelle image redonne **0 verdict
  changé**. C'est attendu : la nuit n'est pas passée.
- **Demain matin**, après la descente : une image, la mesure, un passage, la comparaison. Je te donnerai le nombre de
  ce qui a bougé, et la part de la nuit et la part du code.

## 2. Un défaut du protocole, trouvé par le rejeu exact : 6 verdicts rendus repassent en attente

Le rejeu du vrai chaînage, avec les corrections du protocole, a laissé **6 lignes tranchées impossibles à réaliser** :
0bc98552, 3250892d, 6095c819, 6684bcf1, 87eb399e, dfb32f2b.
- Chacune tient une pièce **supprimée chez Hektor**.
- **Le chaînage fige une pièce supprimée** dans son ancien dossier (affaire_ledger.py, recalculer_les_chaines : « la
  trace garde son dossier »).
- Ni un rattachement ni une coupe ne la trouvent : « transaction introuvable ».
- Ses pièces restent donc dans deux dossiers, et l'écrivain refuserait la ligne.

**Ce que j'ai fait** : un motif déclaré au catalogue, `PIECE_SUPPRIMEE_FIGEE`. Il s'applique quand le morceau tient une
pièce supprimée chez Hektor et que ses pièces sont dans plusieurs dossiers. J'ai ensuite tout rejoué (passage 13).
- **6 verdicts changent, les 6 étaient déjà rendus**, et ce sont exactement ces 6.
- **5 d'entre elles sont tes doublons Hektor**, dont Hektor a déjà supprimé une moitié. Parmi elles, 0bc98552, « la
  réparation des 19 » : deux compromis du 03/04/2026, deux offres du 23/02/2026.
- Tes doublons tranchés passent donc de 16 à **11**.

⚠ **Une piste, que je ne te propose pas encore.** Pour une pièce supprimée chez Hektor, la colonne `app_chaine_id` n'est
plus recalculée par le chaînage. Une correction de cette colonne survivrait donc peut-être à la nuit. Je n'ai pas
vérifié ce qu'en font la pose des étiquettes, le push et la descente. Tant que ce n'est pas mesuré, ces 6 lignes
attendent.

## 3. La porte de chaque ligne tranchée (ta question a)

La mesure porte sur le passage 13 : **4 535 lignes tranchées**, comparées aux dossiers que la nuit fait aujourd'hui.

**Le témoin d'abord.** Le rejeu A (la nuit telle qu'elle tourne, G2 et l'outil de coupe éteints) redonne **les
dossiers de l'image, pièce par pièce : 0 écart sur 31 368**. Sans ce témoin, aucun des chiffres qui suivent ne
vaudrait.

```
RIEN À CORRIGER dans les dossiers     3 985   (dont 3 796 sans rien du tout, et 189 dont seul le gel change)
PAR UNE RÈGLE DÉJÀ ÉCRITE, G2           206   (codée le 20/11, éteinte : voir plus bas)
PAR UN RATTACHEMENT À LA MAIN            85   (des dossiers à réunir, qui ne portent rien d'autre)
PAR UNE COUPE DÉJÀ ÉCRITE               138   (un des 275 morceaux de tes 132 coupes, le fichier éteint)
PAR UNE COUPE NEUVE                     121
PAR TA DÉCISION CHEZ HEKTOR               0   nécessaire pour l'étiquette
                                      -----
                                      4 535
```

- **Sans G2**, ses 206 lignes repassent en coupes : **265 déjà écrites** et **200 neuves**. Le total reste 4 535.
- **Une coupe** est nécessaire quand un des dossiers de la ligne porte aussi une pièce qui n'est pas à elle. Il y en a
  **1 049 à sortir**, comptées ligne par ligne (une même pièce peut compter pour deux lignes) :
  - 991 sont les pièces d'une autre ligne tranchée (deux affaires dans un dossier) ;
  - 49 ne sont à personne (à part, ou sans ligne) ;
  - 9 sont tenues par le gel d'une ligne en attente.
- **Chez Hektor** : **11 lignes** tiennent deux vraies pièces d'un même genre. Elles sont tranchées avec les deux pièces,
  sans effet sur l'étiquette. C'est ta décision, bien par bien, et rien ne t'y oblige pour écrire.
- **G2 n'est pas gratuite.** Elle met justes 206 lignes et n'en casse aucune qui soit juste aujourd'hui. Mais elle
  déplace aussi :
  - **480 pièces hors des biens de tes lignes tranchées** ;
  - les dossiers de **14 lignes en attente**.

  Je n'ai pas jugé ces 480 pièces. **Je ne te propose donc pas G2 comme porte** tant que je ne les ai pas lues.
- **Le gel, notre table** : la nuit ne le recalcule pas. Je l'ai vérifié : aucun programme de `phase2/sync` ni de
  `scheduled` n'écrit `app_classeur_lien`. Le corriger passe par un patch, avec son inverse et ton « vas-y ».

## 4. Le compte du mouvement (ta question b), et ce que ça coûterait à défaire

L'état d'arrivée **E** est la nuit d'aujourd'hui avec un brouillon de coupes du protocole : 548 morceaux, une ligne par
correction. Le brouillon est dans le cache, jamais dans `phase2/sync`. Le **vrai chaînage le rejoue** : 400 morceaux
posés, 148 déjà obtenus, **0 refusé**.
- **4 535 lignes tranchées sur 4 535 sont justes** dans l'état d'arrivée.
- **0 pièce ne bouge hors de leurs biens.**
- **⭐ LE REJEU EXACT DE L'ÉTIQUETTE** : la pose de nuit est faite sur cet état. Les 4 535 lignes y ont **toutes la même
  étiquette que le passage**, sur toutes leurs vraies pièces. L'étiquette n'est plus simulée, elle est rejouée.

**LE GEL.**
- Aujourd'hui, **12 820 liens** :
  - 12 416 sont ceux des lignes tranchées ;
  - 404 sont ceux des lignes en attente, et **on n'y touche pas**.
- Pour les lignes tranchées :
  - **12 208 liens se gardent** ;
  - **208 se délient**, toutes des vraies pièces ;
  - **71 se relient**, dont 69 vraies.
- **266 lignes** voient leur gel changer.

**LES DOSSIERS.**
- **11 551** aujourd'hui, **11 614** à l'arrivée.
- **541 dossiers** d'aujourd'hui se recoupent ou se réunissent, et **604 dossiers** d'arrivée n'existent pas
  aujourd'hui.
- **1 357 pièces** changent de compagnie.

**LES ÉTIQUETTES.**
- **726 pièces** changent d'étiquette dans l'app, dont **570 vers une étiquette NEUVE**.
- **Par ligne tranchée**, en comparant l'étiquette qu'elle a aujourd'hui par son gel à celle qu'elle aura :
  - **4 211** gardent la même ;
  - **245** reçoivent une étiquette NEUVE ;
  - 60 reçoivent une étiquette existante, alors qu'elles en avaient plusieurs ;
  - **16** reçoivent une **autre** étiquette existante ;
  - 3 reçoivent une étiquette existante, alors qu'elles n'en avaient aucune.
- **Les étiquettes qui changent de ligne** :
  - **45** étiquettes d'aujourd'hui iraient (aussi) à une autre ligne ;
  - **46** ne seraient plus l'étiquette d'aucune ligne tranchée.
- ⚠ Ta colonne A est **vide sur tes 4 798 lignes**. Ces mouvements sont donc ceux de l'app, pas ceux de ton Sheet.
- ⚠ **6 lignes en attente** voient quand même un de leurs dossiers bouger, parce qu'une voisine en est coupée :
  305KAY9W, RGCEC677, SBH4QWDW, X2714E92, YZ1B0Q44, Z3DYDC4X. On n'écrit rien sur elles.

**DÉFAIRE.**
- **Les dossiers reviennent exactement** : on retire les lignes du fichier, et la nuit suivante refait les dossiers
  d'aujourd'hui. C'est le rejeu A, déterministe.
- ⚠ **Les étiquettes, non : 214 pièces n'y retrouveraient pas leur étiquette d'aujourd'hui.** Elles en recevraient une
  NEUVE, parce qu'une réunion défaite donne une étiquette neuve au second dossier.
- **Défaire exactement**, c'est donc trois gestes :
  - retirer les lignes du fichier ;
  - rejouer l'inverse du patch du gel ;
  - **restaurer `app_dossier_uuid` de ces 214 pièces** depuis la sauvegarde datée d'avant le geste.

## 5. Deux règles à juger, sorties de la lecture des 107 (par motif)

**Rappel de ton verrou.** Une ligne attend quand une vraie pièce du bien, à part, plus petite que la plus petite des
siennes, peut encore rejoindre son dossier. Elle prendrait alors l'étiquette.

### R7a : la pièce plus petite est DÉJÀ dans le dossier de la ligne, et possible pour elle seule

**Le cas.** La pièce qui retient la ligne est déjà dans le même dossier que toutes les pièces de la ligne. Aucune autre
ligne ne peut la recevoir. Le plus souvent, c'est l'offre acceptée ou le compromis de la ligne, dont ta case n'a pas le
même jour que Hektor.

**Le compte.** **26 lignes**, et 33 pièces gardées : 14 offres acceptées, 13 compromis actifs, 3 compromis annulés,
1 offre refusée.

**La règle.** Le dossier ne peut plus « recevoir » cette pièce : il l'a déjà. Elle **reste à part**, jamais donnée à la
ligne et jamais prouvée par elle. Mais **on ne coupe pas le dossier entre elles**, et l'étiquette de la ligne est celle
du dossier tel qu'il est.

**Ce qu'elle change.**
- **26 verdicts, tous des attentes. 0 verdict déjà rendu ne change, et aucun écart neuf dans les témoins.**
- **25 des 26 gardent l'étiquette de leur dossier d'aujourd'hui.**
- La 26e, 305KAY9W, reçoit une étiquette neuve, et c'est juste : son dossier porte aussi le compromis annulé d'un autre
  acheteur (24122, ta ligne H75WKJ6X), qu'il faut couper.

**Trois exemples.**
- **d6f57a72** (bien 2008, ta ligne 4633, OUARDI). Ta case Offre Achat dit **05/06/2026**, Hektor dit **08/06/2026**
  pour l'offre 1017, dans le même dossier que la vente 1018, que ta Vente Fixée prouve au jour exact. Un seul dossier,
  une seule ligne.
- **OT0CES4C** (bien 38048, ta ligne 3167, LIOZON DELHOUME). Ta case dit **10/04/2019**, Hektor dit **06/04/2019** pour
  l'offre 17874, dans le dossier où ton compromis et ta vente sont prouvés au jour exact.
- **ZXLFUP4A** (bien 126, ta ligne 80, LINGO). Le compromis actif 43 est daté du **11/04/2025** chez Hektor. Ta ligne
  n'a pas de case Compromis, et c'est ta **Vente Fixée** qui dit 11/04/2025. Le compromis reste à part, dans le dossier
  où ton offre est prouvée.

### R7b : la pièce plus petite est dans un AUTRE dossier, et possible pour cette seule ligne

**Le cas.** La pièce qui retient la ligne n'est pas dans son dossier, et elle ne pourrait aller qu'à elle. Le plus
souvent, c'est un compromis annulé sans date.

**Le compte.** **10 lignes**, et 13 pièces mises de côté.

**La règle.** La pièce est **mise de côté** : isolée dans un dossier à elle seule, par une ligne du fichier des coupes.
Elle ne peut plus rejoindre aucun dossier, donc elle ne retient plus la ligne. C'est ta règle 6 (« on ne supprime pas
une part, on la met de côté ») et ta règle R4 du 20/11, que le fichier rend sûre.
- **Elle est plus étroite que R4** : elle ne touche jamais une pièce possible pour deux lignes.
- C'est ce qui l'empêche de casser DEBARD, puisque son compromis 20088 relie justement ses deux lignes.

**Ce qu'elle change.**
- **10 verdicts, tous des attentes. 0 déjà rendu, et aucun écart neuf.**
- Elle ajoute **13 lignes au fichier des coupes**, une par pièce isolée.

**Trois exemples.**
- **7C1ZQYFL** (bien 61, ta ligne 18, AGUIAR). Le compromis annulé 29 est sans date, à 65 000. Hektor le met au nom de
  RAHAL Radia, seul dans son dossier. Il est mis de côté, et ta ligne garde son étiquette `16213394`.
- **I847SPN3** (bien 8494, ta ligne 67, MACHABERT). Le compromis annulé 3698 du 02/08/2022, à 6 800, ne tombe sur aucune
  de tes cases. ⚠ Hektor le met au nom de MACHABERT, comme ta ligne. Le nom n'est qu'un indice : la règle le met de
  côté, elle ne le donne pas.
- **HGXAVYKA** (bien 35453, ta ligne 99, TEYSSIER). Le compromis annulé 16774 est sans date, à 70 000. Hektor le met au
  nom de DESBOS Cedric. Il est mis de côté.

**Les deux ensemble** (passage 16) : **38 lignes** (26 + 10 + 2 qui ont besoin des deux). **0 verdict déjà rendu ne
change, et aucun écart neuf.** Le verrou passe de **107 à 69**.

## 6. Où on en est

- **Le passage de référence est le 13** : **4 535 tranchées + 263 en attente = 4 798**.
- Avec R7a et R7b, ce serait 4 573 + 225.
- **Les motifs d'attente** (passage 13) :
  - VERROU_PIECE_PLUS_PETITE 107 ;
  - SES_PIECES_A_PART 29 ;
  - AUCUNE_PIECE_PROUVEE 28 ;
  - PLUSIEURS_BIENS 23 ;
  - COPIE_SEULE 23 ;
  - BIEN_SANS_PIECE 23 ;
  - SANS_BIEN 11 ;
  - DEUX_LIGNES_UN_DOSSIER 10 ;
  - PIECE_SUPPRIMEE_FIGEE 6 ;
  - A_SA_DECISION 3.
- **Les témoins** (passage 13) :
  - V3 : 392 accords, 3 écarts, 36 en attente. Les 3 écarts sont les offres refusées d'une autre chaîne, déjà vues.
  - 132 coupes : 265 accords, 4 écarts, 6 en attente. Les 4 écarts sont DJEBBOUR et PAOLONE.
  - 29 faibles : 36 accords, 14 écarts, 9 en attente. Les 14 écarts sont les pièces « nom seul » retirées.
  - Jumelles : 2 accords, 0 écart, 1 en attente.
  - Pièces à part : 10 accords, 0 écart, 10 en attente.
  - Neutres : 14 accords, 0 écart, 1 en attente.
  - Bien 39845 : 3 accords sur 3.
- **Je n'ai pas eu besoin du run de jour.** Le rejeu du vrai chaînage sur copie mesure l'effet sans rien déranger. Je
  te le demanderai le jour où on pose une première correction, et pour cela seulement.
- **Ce qui reste à lire** :
  - les 69 du verrou, presque toutes des pièces possibles pour plusieurs lignes ;
  - les 480 pièces que G2 déplace ailleurs ;
  - les 23 « plusieurs biens », les 29 + 28 sans preuve, les 10 « deux lignes », les 23 « copie seule ».

## 7. Ce qui attend ta décision

1. **R7a** (26 lignes, 0 verdict rendu changé) : oui ou non ?
2. **R7b** (10 lignes, 13 pièces mises de côté dans le fichier des coupes, 0 verdict rendu changé) : oui ou non ?
3. **DJEBBOUR** : une affaire ou deux pour tes lignes 3461 et 155 ? Tu as écrit deux noms, pas trois.
