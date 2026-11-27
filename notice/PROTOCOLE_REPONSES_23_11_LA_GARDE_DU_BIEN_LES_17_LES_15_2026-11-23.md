L3 · chantier classeur · ㉑ sexies · 23/11, nuit : ta garde (a) est écrite et prouvée sur le 11/11, la liste (b) est
fabriquée, la question (c) a sa réponse. Rien d'écrit en base, chez Hektor ni dans ton Sheet, rien de poussé.

# Ton mot du 23/11 : la garde du bien, les 17, les 15

Ton mot : `C:\Hektor\mot_du_23_11_les_17_offres_et_tes_deux_questions.md`. Le cap ne change pas :
- **le patch du journal n'est pas encore collé** : à 00:20, le contrôle dit encore « colonne absente », fonction
  815e956f. Dès que tu l'as collé, je lance `apres-collage` et je te donne tes trois points en clair ;
- la coupe « C5 aux portes » vient à la fin du protocole ;
- puis la mise de côté de la famille 1 : 1001563, 1001580, et 1001482 sur sa cause établie. Elle est fabriquée et
  répétée sur copie, mais pas jouée.

## 1. Tes deux réponses, prises telles quelles

- **1001561 reste à part.** Ton critère est meilleur que le mien : ce qui sépare les familles, c'est l'état de l'offre
  d'origine chez Hektor, pas la certitude.
- **1001482, un seul fait à rectifier, sans rien changer à ta conclusion.** Tu écris que son bien n'est touché par
  aucun de nos gestes. La mesure dit le contraire :
  - notre lot « table » a refusé l'offre 5055 (n° 382, bien 10527) le 11/11 à 18:21, alors qu'elle était acceptée ;
  - mais ce refus était juste : le bien ne porte aucune vente, seulement un compromis annulé. C'est une des 1 127 ;
  - la copie (refusée) double donc une offre aujourd'hui refusée. Elle reste bien en famille 1.

## 2. (a) La garde du bien : écrite, et ton témoin tombe juste au numéro près

**Où elle est.** `Console/enqueue_refus_offres_mortes_lot.js`, garde ⑤ :
- une offre dont le bien porte une vente n'est pas touchée, quel que soit le dossier où se trouve cette vente ;
- elle cherche la vente par `hektor_annonce_id`, en plus de la chaîne ;
- elle vit dans le tri, qui sert aux deux modes : un seul endroit, donc les deux modes ont la même garde ;
- **toutes les ventes comptent**, même supprimées chez Hektor, même reprises du classeur. Elle ne fait que retenir un
  geste : dans le doute, on ne refuse pas. C'est la leçon du dossier 3699 ;
- **une lecture ratée ne vaut pas « aucune vente »** : la liste des ventes porte un témoin positif, la vente 23997 du
  bien 47557. S'il n'est pas lu, le lot s'arrête en code 2 et n'enfile rien.

**Ce que j'ai changé au code existant, et seulement ça.**
- La sélection « cascade » et le tri sont sortis de `main()` pour être rejoués tels quels. C'est le même code : hors
  ajouts, 4 lignes ont changé, et ce sont les paramètres.
- Le lot ne se lance plus quand on le requiert. Appelé directement, il fait ce qu'il faisait.
- L'ancien essai de la garde de l'origine reste vert, 15 sur 15.

**Le témoin, sur l'état du 11/11** (sauvegarde datée de 08:00, avant le lot de 17:21, 31 151 lignes ; essai
`Console/test_garde_du_bien_refus_offres.js`, **24 sur 24**) :
- **sans la garde, le vrai code du lot retrouve exactement ce qu'il a posé ce jour-là** : 661 refus en « cascade » et
  523 en « table », sans une offre de plus ni de moins. Sans ce point, le rejeu ne prouverait rien ;
- **avec la garde, il retient 36 offres** : tes 17, chacune sur le bien que tu as écrit, 13 en « cascade » et 4 en
  « table », plus les 19 déjà réacceptées le 12/11 ;
- **et aucune autre.** Parmi les offres restées refusées, il en retient exactement 17 ;
- les 19 sont le même défaut, déjà réparé : c'est ton « le total est 36 ». Une garde juste doit donc les retenir aussi.

⭐ **Ta crainte « le défaut remordra » se mesurait, et il remordait.** Je lui ai demandé ce qu'elle ferait AUJOURD'HUI, à
blanc. **Le mode « cascade » refusait encore 2 offres chez Hektor**, sur des biens vendus :
- 8018 (bien 16073, vente n° 7076) ;
- 13984 (bien 28242, vente n° 6536).

Toutes deux font partie des 19 réparées le 12/11. Relancer le lot sans la garde défaisait donc 2 de nos réparations. La
garde les retient toutes les deux. Le mode « table » ne change pas.

## 3. (b) La liste, avec ses preuves : `notice/LISTE_DES_17_OFFRES_REFUSEES_A_TORT_2026-11-23.csv`

Chaque preuve est lue entrée par entrée dans `propositions_json` : la dernière acceptation avant notre refus, notre
refus, le travail qui l'a posé, et la vente du bien, cherchée par le bien. **Je n'ai rien réparé.**

**Tes 14 sont confirmées**, 10 au montant exact et 4 renégociées, et le journal ne porte rien après notre refus. Pour
chacune : l'offre, son bien, l'acceptation, notre refus du 11/11, la vente.
- 531, bien 1387 : acceptée le 10/06/2010 à 74 000 €, refusée à 19:01 ; vente n° 8954 à 74 000 €, le 10/09/2010.
- 3648, bien 8395 : acceptée le 23/08/2024 à 460 000 €, refusée à 19:03 ; vente n° 8654 à 460 000 €, le 22/01/2025.
- 6556, bien 12728 : acceptée le 12/04/2021 à 87 000 €, refusée à 19:07 ; vente n° 7812 à 87 000 €, le 02/09/2021.
- 7780, bien 15722 : acceptée le 04/05/2021 à 220 000 €, refusée à 19:08 ; vente n° 6999 à 220 000 €, le 13/10/2021.
- 14112, bien 28653 : acceptée le 25/03/2021 à 113 000 €, refusée à 19:16 ; vente n° 6591 à 113 000 €, le 28/02/2022.
- 14420, bien 29285 : acceptée le 20/11/2009 à 29 000 €, refusée à 18:45 ; vente n° 6712 à 29 000 €, le 25/07/2008.
  ⚠ **Acceptée 483 jours APRÈS la vente.**
- 17322, bien 36794 : acceptée le 05/12/2022 à 234 000 €, refusée à 19:22 ; vente n° 3671 à 234 000 €, le 24/03/2023.
- 22384, bien 44914 : acceptée le 08/01/2018 à 118 000 €, refusée à 19:28 ; vente n° 2502 à 118 000 €, le 17/04/2018.
- 22446, bien 45081 : acceptée le 22/01/2016 à 149 000 €, refusée à 19:28 ; vente n° 2521 à 149 000 €, le 08/04/2016.
- 24159, bien 47815 : acceptée le 09/09/2022 à 139 700 €, refusée à 19:30 ; vente n° 1496 à 139 700 €, le 05/01/2023.
- 5126, bien 10703 : acceptée le 22/09/2017 à 47 900 €, refusée à 18:23 ; vente n° 319 à 50 000 €, le 30/08/2018.
- 16421, bien 34296 : acceptée le 12/02/2019 à 40 000 €, refusée à 19:20 ; vente n° 4540 à 35 000 €, le 19/06/2020.
- 18600, bien 39032 : acceptée le 12/10/2016 à 120 000 €, refusée à 18:50 ; vente n° 4076 à 115 000 €, le 26/05/2012.
  ⚠ **Acceptée 1 600 jours APRÈS la vente.**
- 21600, bien 43126 : acceptée le 19/10/2021 à 34 000 €, refusée à 19:27 ; vente n° 3287 à 32 000 €, le 20/11/2021.

⚠ **Pour 14420 et 18600 (toutes deux du mode « table »), l'acceptation vient après la vente.** Ce n'est peut-être pas
l'offre de la vente : une seconde tentative sur la même annonce, ou une date de vente fausse. Ce n'est pas à moi de
trancher, mais une réacceptation leur donnerait une offre acceptée qui n'a pas mené à la vente.

⚠⚠ **Tes 3 « moins graves » ne gardent aucune offre acceptée chez Hektor.** L'offre encore acceptée de chacun de ces
biens est **notre copie du classeur** :
- 14008, bien 28422 : acceptée le 28/06/2025 à 100 000 €, refusée par nous à 19:16 ; vente n° 6565 à 100 000 €. La
  seule offre acceptée du bien est la copie 1001593.
- 17025, bien 36165 : acceptée le 15/10/2022 à 67 000 €, refusée par nous à 18:49 ; vente n° 3575 à 67 500 €. La seule
  offre acceptée du bien est la copie 1001568.
- 23995, bien 47557 : acceptée le 25/03/2024 à 44 600 €, refusée par nous à 19:30 ; vente n° 1438 à 44 600 €. La seule
  offre acceptée du bien est la copie 1001561.

**Chez Hektor, ce sont donc 17 biens vendus sans aucune offre acceptée, et non 14.** Une copie du classeur n'existe pas
chez Hektor.

**La 18e, que la mesure a trouvée en route, n'est pas le défaut.** L'offre 23139 (bien 46032) a été refusée le 12/11
par `enqueue_fermeture_dossiers_impossibles.js`, sur ta décision du 12/11, dossier par dossier. Son journal ne porte
aucune acceptation.

## 4. (c) Les 15 biens remis « Sous offre » le 12/11 : la dette est soldée depuis le 13/11

**Tu les as remis « Vendu » toi-même, à la main, le 13/11 au matin.** Je l'avais vérifié bien par bien par l'API à
08:59 : 15 sur 15 en statut 5, et aucune vente fabriquée (commit f4596c2).

**Aujourd'hui, en base :**
- les 15 sont « Vendu » ;
- leur dernière modification chez Hektor date du 13/11, entre 08:44 et 08:57 : ce sont tes corrections ;
- notre dernière lecture date du 14/11 à 05:36.

**Depuis le 13/11, 16 travaux ont touché ces biens, et ce sont tous des lectures** : 15 synchronisations de photos le
14/11 et un import de détail le 18/11. Aucun n'a touché leur statut ni une offre. Le témoin : la même requête voit bien
les 45 travaux du 12/11. La sentinelle des écarts de statut ne compte qu'un écart (55086), et ce n'est pas un des 15.

⚠ **La base ne peut pas voir un geste humain chez Hektor fait après le 14/11.** Pour lire leur statut d'aujourd'hui, il
faut 15 lectures par l'API, en lecture seule, espacées de 1,2 s (une vingtaine de secondes). Je ne l'ai pas fait :
c'est chez Hektor, et ce chantier n'y va pas sans ton mot.

⭐ **Pour la future réparation** : sur tes 17, ce sont des biens vendus. Chaque réacceptation les remettra
« Sous offre », d'où tes deux gestes par offre : réaccepter, puis remettre « Vendu » par `redescendreStatutHektor()`.

## 5. La famille 2 en attente, avec sa raison écrite

C'est écrit au carnet (`notice/CHANTIER_CLASSEUR_TEMPS4_5_FINIR_2026-11-19.md`, § 20.16) :
- **ce qui attend** : 1001561 et 1001593 ne se mettent pas de côté ;
- **pourquoi** : leur offre d'origine est toujours cassée, et la copie est la seule trace de l'offre qui a mené à la
  vente ;
- **dans quel ordre** : la réparation par lot cadre, puis la mise de côté.

Le patch de la famille 1 ne peut pas les toucher : ses gardes visent les 3 copies de la famille 1 par leurs valeurs
exactes.

⚠ **Une troisième copie est dans la même situation, par ton propre critère : 1001568** (bien 36165, ta ligne X2714E92,
MAIRIE DU CHAMBON).
- Son offre d'origine, 17025, acceptée le 15/10/2022, a été refusée par notre lot « table » le 11/11, et jamais réparée.
- La copie est aujourd'hui la seule offre acceptée du bien.
- Elle n'était pas dans mes dix cicatrices : sa date (05/10/2022) n'est pas celle de 17025, donc elle n'a pas de
  jumelle. C'est le filet ⑦ qui la nomme.

Je l'ai notée « en attente » avec les deux autres. C'est à toi de la classer.

## 6. Ce qui ne change pas

- La colonne `date` n'est corrigée nulle part.
- Aucune offre n'est touchée chez Hektor.
- Rien ne se pousse.

## Ce qui attend ta décision

1. **Le patch du journal** : tu le colles, et je lance `apres-collage` pour tes trois points. Ce matin, avant tout le
   reste : `matin` (a), puis (b), puis la mesure du matin.
2. **1001568** : je la range avec la famille 2 (en attente de la réparation de 17025), ou tu la classes autrement ?
3. **14420 et 18600, acceptées après la vente** : elles restent dans la liste de réparation, ou tu veux d'abord leur
   preuve, bien par bien ?
4. **Les 15 biens** : je fais les 15 lectures par l'API pour te donner leur statut d'aujourd'hui (environ 20 secondes,
   lecture seule), ou la base te suffit ?
