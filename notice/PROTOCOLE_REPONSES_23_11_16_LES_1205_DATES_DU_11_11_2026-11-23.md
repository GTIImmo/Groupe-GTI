L3 · chantier classeur · ㉑ duo et vicies · 23/11 : la mesure des dates du 11/11 est faite. Dix lignes du reste touchent
une de ces offres, ce n'est donc pas zéro. Mais le protocole lit déjà leur vraie date, depuis le 20/11, et la date écrasée
ne retient aucune ligne. Le sujet est clos pour le protocole. Rien n'est écrit, ni en base, ni dans le Sheet, ni chez
Hektor, et rien n'est poussé.

# Les 1 205 offres datées de notre geste du 11/11

Ton mot : `C:\Hektor\mot_du_23_11_les_1205_dates_faussees_du_11_11.md`. Carnet : § 20.31.

## 1. L'image retrouve ton compte

1 166 offres au 11/11 et 39 au 12/11 font 1 205 offres, sur 1 205 biens, dont 1 183 refusées et 22 acceptées. C'est le même
compte que ta mesure en production. Aucune pièce d'un autre genre n'est touchée.

## 2. Le lecteur du protocole lit déjà la vraie date

Ton mot dit que le protocole lit la colonne `date`. C'est vrai qu'il n'y a aucune occurrence dans `protocole_classeur.py`,
mais ce fichier ne lit aucune date lui-même. Il passe par l'outil de coupe, `coupe_preuve_interne.py`, dont la ligne 123
dit depuis le 20/11 : « la date d'une offre = sa 1re proposition (la colonne date ment) ». Cela vaut pour toutes les offres,
pas seulement pour les 1 205. Tous les lecteurs de date du protocole passent par cet outil.

- **Le témoin positif 11206** : la colonne `date` dit le 11/11/2026 à 18:40:50, la première proposition dit le 02/12/2019,
  et **le protocole lit le 02/12/2019**.
- **Sur les 1 205** : 1 192 sont lues à leur proposition, et 13 n'ont pas de date. Aucune n'est lue au 11 ou au 12/11.
- **Les 13 sans date n'en ont nulle part.** Pour 7 d'entre elles, la proposition porte « 0000-00-00 » chez Hektor. Les 6
  autres n'ont qu'un refus daté du 12/11, sans aucune proposition. Aucun lecteur ne peut leur rendre une date. Une seule est
  dans un gel : 19050, tenue à part chez f90b0418, qui est tranchée par R9b sur son compromis.
- **Le témoin d'usage.** 302 lignes tranchées tiennent une de ces offres.
  - 299 sont prouvées par sa vraie date, au jour exact.
  - Les 3 autres le sont autrement : EKDZCRI1 et FC41ET5P par R9b, bdb548a3 par sa chaîne.
  - Aucune preuve ne cite le 11 ou le 12/11.

Ton hypothèse sur R9 et R9b ne tient donc pas : elles n'ont pas contourné une date écrasée. R9b n'a pris que deux de ces
offres, et c'était pour un écart entre la vraie date et la case du Sheet (un an pour EKDZCRI1, un jour pour FC41ET5P).

## 3. Ta mesure, au mot près

- **Passage 47 (97 lignes)** : 4 lignes touchent une telle offre par leur gel, et 9 par leur gel ou leur bien.
- **Passage 51 (91 lignes)** : 4 par leur gel, et 10 par leur gel ou leur bien. Ce sont 6 lignes du verrou, 3 de « pièces à
  part » et 1 de « copie seule ».

**Ce n'est pas zéro, mais le protocole lit déjà la vraie date pour les 10.** Pour chacune, la pièce et la date lue :
- 5QE9107L et ZW7MKTWH : 20089, lue au 20/07/2021 ;
- BQAVSRA1 : 4192, lue au 01/03/2024 ;
- KPDROR30 et SBT1INZT : 10017, lue au 15/09/2023 ;
- L2B2WGCF et Z3DYDC4X : 14112, lue au 25/03/2021 ;
- RKWNRBV1 : 17377, lue au 16/09/2023 ;
- XBR8QD6L : 25735, lue au 05/06/2023 ;
- ZZ5WKMWM : 11206, lue au 02/12/2019.

Ce qui les retient est déjà nommé : des offres refusées sous le prix, à 1, 2 et 81 jours de leur case, un prix partagé, et le
verrou.

**Conclusion.** Le remède que tu proposes, lire `propositions_json` au lieu de `date`, est déjà en place. Il n'y a rien à
poser, donc pas de règle à prouver. **Le sujet est clos pour le protocole, et le verrou ne se réduira pas par cette voie.**

**Une piste, non mesurée.** La première proposition est souvent écrite à « 22:00:00 » ou « 22:59:59 ». Si c'est une heure UTC,
la date locale serait le lendemain pour certaines offres : FC41ET5P a justement un jour d'écart. Je ne conclus rien, mais
c'est à mesurer avec le verrou, pour les offres à un jour de leur case (BQAVSRA1).

## 4. 11204

Il reste avec la famille du verrou, de jour, comme tu l'as dit. Avec ZZ5WKMWM, cette famille compte maintenant 56 lignes.

## Ce qui attend ta décision

1. Le sujet des dates du 11/11 : je le tiens pour clos pour le protocole, comme le dit ton critère ?
2. La piste de l'heure UTC : je la mesure en ouvrant le verrou, ou avant ?
