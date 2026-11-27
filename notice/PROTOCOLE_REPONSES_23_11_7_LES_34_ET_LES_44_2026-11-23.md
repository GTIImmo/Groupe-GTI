L3 · chantier classeur · ㉑ duodecies · 23/11 : les 34 lignes sans pièce ou sans bien sont mesurées, et la cause n'est
pas celle qu'on attendait. Les 44 pièces du verrou sont tranchées en partie : une règle proposée, R7c, en tranche 10, ce
qui libère 12 lignes. Rien n'est écrit, ni en base, ni dans le Sheet, ni chez Hektor, et rien n'est poussé.

# Ton mot du 23/11 (12) : les 34, puis les 44

Ton mot : `C:\Hektor\mot_du_23_11_ton_motif_oui_et_les_69_apres.md`. Carnet : § 20.22. Les CSV, ligne par ligne :
`notice/PROTOCOLE_LES_34_SANS_PIECE_OU_SANS_BIEN_PASSAGE_23_2026-11-23.csv` et
`notice/PROTOCOLE_LES_44_PIECES_DU_VERROU_PASSAGE_23_2026-11-23.csv`.

## 1. Les 34 : la mesure que tu demandais en premier

**Pour les 23 « bien sans pièce », le bien est bien nommé** : 21 sont dans l'index des archivés et 2 dans
`app_dossier_current`. Aucun ne manque.

**Mais « pas dans current » n'explique pas « pas de pièce », et je te contredis avec ces mesures :**
- le protocole ne lit jamais `app_dossier_current` (0 occurrence dans ses trois scripts) ;
- le registre a des pièces pour 1 670 biens archivés et pour 8 859 biens vendus ou clos ;
- le registre des mandats couvre 17 375 biens archivés.

**La vraie cause : ces 22 biens n'ont aucune transaction.** Il y a 0 pièce en production. Dans notre miroir local de
Hektor, d'où le registre est construit, on trouve 0 offre, 0 compromis et 0 vente.

**Ce que dit le Sheet de ces 23 lignes :**
- 18 lignes disent « Annulée » ;
- **5 lignes disent une affaire vivante ou réglée, sans une seule pièce chez nous** :
  - 3 « Vente réglée » (QXDW8EQA, 2U5QPKRC, MQ6H8TVQ), sur des biens archivés ;
  - 1 « Vente fixée » (a8aaeb2b), sur un bien vivant ;
  - 1 « Compromis en attente » (130d81ac).
- Ces 5 lignes cachent peut-être un trou d'import. Je ne l'ai pas mesuré : il faudrait lire chez Hektor.

**Pour les 11 « sans bien » :**
- **7 portent un vieux numéro de mandat (3423 à 4182) que les index donnent à 2 ou 3 biens à la fois.** Hektor numérote
  par agence et réutilise ses numéros : on trouve un bien de 2011-2014 et un ou deux de 2019-2021.
- **4 n'ont aucun bien, même dans les index** :
  - I3TFR2KG porte « NON TROUVÉ », alors que c'est une vente réglée avec un compromis signé ;
  - le mandat 17081 est au registre, mais sans bien ;
  - aucun mandat ne porte le numéro 92560 ;
  - 54376c72 porte une offre d'achat du 11/11/2026, sur un mandat 18993 qui n'est dans aucun index.

**Une piste mesurée, puis refusée par son témoin.** J'ai essayé « le mandat dont la période contient la première date de
la ligne ». Sur les lignes déjà tranchées dont le mandat nomme plusieurs biens, elle garde le bon bien seul 477 fois,
mais un autre bien 47 fois. Avec 47 erreurs, elle est refusée. Le témoin a aussi attrapé une faute de ma part au premier
tour : je lisais mal les cases de date, et la piste ne gardait alors aucun bien sur 1 488 lignes.

**Le front, comme tu le demandais.** Je n'y trouve aucune morsure nouvelle. La recherche par numéro d'annonce passe déjà
par les trois index (`api.ts:3340`). Les deux appelants de la lecture « vivante » retombent sur les vendus et les
archivés (`App.tsx:9927`), ou sur la liste étendue (`App.tsx:16601`). Les trois autres usages sont voulus.

**La règle que je propose, R8** : « une ligne dont le bien n'a aucune pièce chez nous n'a pas de dossier à nommer : il n'y
a rien à écrire dans sa case A. Elle sort du reste à vider, sous un verdict à part, et elle est rejugée à chaque
passage : si une pièce arrive, elle rentre d'elle-même. »

## 2. Les 44 : ta mesure est confirmée, et une règle en tranche 10

Je retrouve tes chiffres à l'unité : 69 lignes et 44 pièces, dont 25 « plusieurs acheteurs », 9 « aucune ligne », 9
« honoraires inconnus », et 14033, ta décision B3.

**Un point du code.** R7a et R7b traitent déjà toutes les pièces possibles pour une seule ligne. Les 44 sont donc toutes
possibles pour plusieurs lignes.

**Ce qui compte n'est pas la famille, mais ton témoin inverse : une preuve pourrait-elle encore venir ?**
- **Les 25 « plusieurs acheteurs »** sont des compromis annulés, et toutes ont le prix et les honoraires d'une ligne. Une
  preuve existe donc, mais elle désigne plusieurs lignes : elles continuent à bloquer.
- **Les 9 « aucune ligne »** sont des compromis annulés sans date. 6 sont hors du dossier de toutes leurs lignes, 3 sont
  dedans.
- **Les 9 « honoraires inconnus »** sont 7 offres refusées et 2 compromis annulés. La date de chaque offre n'est sur
  aucune case, et chaque ligne possible porte déjà la date de sa propre offre : il ne reste aucune case vide à remplir.
  4 sont hors du dossier de leurs lignes, 5 sont dedans.

**La règle proposée, R7c** (une variante, jamais appliquée sans ton mot) : « une pièce à part, plus petite, possible pour
plusieurs lignes, qu'aucune preuve ne peut donner à aucune d'elles, et qui n'est dans le dossier d'aucune d'elles, est
tranchée. Elle est mise de côté comme avec R7b : avec son dossier, et elle garde son ancien numéro. » Aucune preuve
possible, cela veut dire : ni date au jour exact, ni prix et honoraires d'une ligne, ni case de date vide qu'on pourrait
remplir de sa date.

**Sa mesure :**
- **sans la variante, le passage 24 est égal au passage 23** : aucun verdict ne change, donc le code modifié ne change
  rien de lui-même ;
- **avec la variante (passage 25, marqué « variante non validée »), 10 pièces sont tranchées et 12 lignes quittent le
  verrou.** On passe de 4 573 lignes tranchées à 4 585 ;
- aucun verdict déjà rendu ne change ;
- les 19 écarts des témoins sont les mêmes, ligne à ligne ;
- **DEBARD attend toujours**. Sa pièce 20088 est dans le dossier de ses deux lignes, et la règle ne la touche pas : c'est
  son témoin ;
- **les 10 pièces gardent leur ancien numéro** dans la pose simulée ;
- **tes lignes 40 et 105 gardent D2025-0107 et D2025-0039**, et les deux autres lignes des 2 560 gardent aussi leur
  numéro ;
- une seule ligne reçoit un numéro neuf : WW88Z2AC, dont la case A est vide et qui n'est pas dans les 2 560.

**Six des 10 pièces sont tenues par le gel d'une ligne « copie seule »** : LTJYTEVC, MIO9L8C9, SYA8MH79, af8d7986,
SHN6RKDI et C0HXVVCW. C'est l'affaire annulée de cette ligne. R7c lui donne son propre dossier, avec son ancien numéro.
Ces lignes restent en attente jusqu'à la mise de côté des copies.

**Pas encore vérifié : le rejeu exact sur le vrai chaînage.** Le script des portes refuse de compter une variante, et
c'est voulu. Le rejeu se fera si tu valides R7c.

**Ce qui reste au verrou : 57 lignes, retenues par 34 pièces.**
- **les 25 « plusieurs acheteurs »** : une preuve désigne plusieurs lignes, donc c'est ta main qui décide, pièce par
  pièce. Le CSV donne, pour chacune, ses lignes possibles et celles dont elle a le prix et les honoraires ;
- **8 pièces sans preuve, mais qui sont dans le dossier d'une de leurs lignes**, dont 20088 de DEBARD ;
- **14033, ta décision B3** : elle est à part par ta décision, mais elle est dans le dossier d'une de ses lignes, et elle
  a son prix et ses honoraires.

## Ce qui attend ta décision

1. **R8 (les 23 « bien sans pièce »)** : je la mets dans les règles validées ?
2. **Les 5 lignes vivantes ou réglées sans pièce** : je les lis chez Hektor (5 lectures, en lecture seule), pour savoir si
   c'est un trou d'import ?
3. **R7c (10 pièces, 12 lignes)** : je la valide dans le code, puis je fais un nouveau passage et le rejeu exact ?
4. **Les 25 « plusieurs acheteurs »** : tu les tranches à la main, pièce par pièce, ou on les laisse au verrou ?
5. **14033** : ta B3 voulait-elle dire « à part pour toujours » ?
