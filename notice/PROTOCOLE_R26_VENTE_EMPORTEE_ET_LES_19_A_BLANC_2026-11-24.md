# R26 à blanc, et les 19 expliqués (24/11/2026, son 3e mot)

> Son ordre : « Tu mesures R26 AVANT tout le reste [...] puis tes 19 expliquées une par une, puis la liste des 42 RÉVISÉE
> après R26 ». ⛔ **Rien n'est écrit** : ni base, ni Sheet, ni Hektor, pas de push, pas de pull. L'interrupteur des coupes
> reste éteint. Le vrai passage 79 et ses fichiers ne bougent pas.

Outils (lecture seule) :
- `phase2/checks/protocole_r26_vente_emportee_a_blanc_2026-11-24.py` — R26 posée sur une **copie en mémoire** de
  `protocole_portes.py` (quatre ancres), jouée dans un dossier à part (`C:\Hektor\chantier_classeur_q6_cache\protocole_a_blanc_r26`) :
  copie du socle, des caches de rejeu A et B, du fichier des mises de côté du passage 79. Le rejeu E est refait avec le
  brouillon de R26. Sortie : `protocole_a_blanc_r26\r26_a_blanc.json`.
- `protocole_realignement_temps1_a_blanc_2026-11-24.py` et `..._temps2_repartition_a_blanc_2026-11-24.py` : option `--r26`
  (l'état d'arrivée avec R26), et sa règle des dates d'annulation (② de son mot) dans le geste.

Fichiers : `notice/PROTOCOLE_REALIGNEMENT_TEMPS1_LES_ANOMALIES_PASSAGE_79_AVEC_R26_2026-11-24.csv`,
`..._LE_GESTE_A_BLANC_PASSAGE_79_AVEC_R26_2026-11-24.csv` (les 42 révisés), `..._LES_TROUS_PASSAGE_79_AVEC_R26_2026-11-24.csv`,
`notice/PROTOCOLE_REALIGNEMENT_TEMPS2_REPARTITION_A_L_ARRIVEE_PASSAGE_79_AVEC_R26_2026-11-24.csv`, `..._LA_GARDE_..._AVEC_R26_...csv` (vide).

---

## 1. R26 — « la coupe emporte avec la ligne la vente qui n'appartient qu'à elle »

**La cause**, lue dans le code : la vague écrit au brouillon, pour une ligne à couper, un morceau = ses pièces **prouvées**
(+ R7a : ses pièces à part déjà dans son dossier). Une vente que le protocole ne prouve pas par sa date n'y est pas ; elle
reste avec le reste de l'ancien dossier. Pour 3 des 5, le protocole la range même « à part sans effet sur l'étiquette »
(8BUW2ZVH : 12181 12182 ; 8BJKJ6XP : 21661 21662 ; HPNJ32UM : 28146 ; ZYVO6KK1 : 16019), ce qui ne l'emporte pas.

**La règle, telle que mesurée** — pour une ligne tranchée :
- ses pièces du protocole ne portent **aucune** vraie vente ;
- le dossier d'aujourd'hui de ses pièces (rejeu A) porte **une seule** vraie vente hors d'elles ;
- cette vente est à **elle seule** au gel, et **aucune** ligne tranchée ne la tient ;
- → son morceau l'**emporte**, et la ligne est jugée juste avec elle.

Elle ne change **aucun verdict, aucune pièce, aucune étiquette du protocole** : seulement le morceau que la vague coupe.

**Ce qu'elle désigne** : 49 lignes. 44 ont la porte RIEN (leur vente est déjà avec elles : la règle n'y fait rien) ;
**5 ont une coupe neuve : ce sont exactement les 5.** Le brouillon change de 5 morceaux, ni plus ni moins
(`12178 12180` → `12178 12180 12182`, etc.).

### ⭐ Le témoin positif : 5 / 5

- WJ8NY16C, vente 7126 : laissée derrière → **avec sa ligne**, D2024-0086
- 8BUW2ZVH, vente 12182 : → **avec sa ligne**, D2019-0128
- ZYVO6KK1, vente 16019 : → **avec sa ligne**, D2023-0481
- 8BJKJ6XP, vente 21662 : → **avec sa ligne**, dans son dossier NEUF (la ligne y va déjà sans R26)
- HPNJ32UM, vente 28147 : → **avec sa ligne**, D2024-0023

### ⛔ Le témoin inverse : 0 autre vente

**17 pièces changent de compagnie, dont 5 ventes : les 5.** Les 12 autres sont leurs compagnes : les pièces de la ligne
qui reçoivent la vente (7122 7124, 12178 12180, 16015 16016, 21659 21660, 28145), et les pièces que la vente quitte,
tenues par **personne** (12179 compromis annulé, 21658 compromis annulé, 28146 offre).
**Aucune pièce d'une autre ligne, aucune ligne en attente, rien hors des biens des lignes tranchées.**

### ⭐ Le rejeu exact : 0 recul

- lignes tranchées justes à l'arrivée : **4 725 / 4 725** (comme la référence) ;
- même étiquette que le passage : **4 725 / 4 725** ; numéro d'arrivée de chaque ligne : **0 change** ;
- hors des biens : 0 ; R7b : 0 faux ; lignes en attente qui bougent : 0 ;
- dossiers d'arrivée : 11 605 → 11 603 (3 dossiers neufs de moins : les ventes ne restent plus seules) ;
- portes : COUPE_NEUVE 145 → 143, REGLE_G2 221 → 223 — HPNJ32UM et WJ8NY16C seraient « justes par G2 » (la règle G2,
  codée et éteinte) une fois leur vente comptée avec elles ; **le brouillon, lui, porte bien leur coupe** (il est écrit
  avant G2).

⚠ **Une étiquette déjà rendue change, et je la nomme** : la vente **21662** quitte D2017-0367 pour le dossier neuf de sa
ligne. D2017-0367 **ne bouge pas** : il reste sur 21658 (un compromis annulé, tenu par personne). La ligne 8BJKJ6XP part
déjà dans un dossier neuf **sans R26** (son étiquette NEUVE:21659 est celle du passage) ; R26 fait seulement suivre sa
vente. Pour les 4 autres ventes, R26 **évite** un changement : sans elle, chacune partait dans un dossier NEUF ; avec elle,
elle **garde** le numéro de sa ligne (D2024-0086, D2019-0128, D2023-0481, D2024-0023).

### ⭐ La garde du temps 2, avec R26 : **0**

Plus aucune chaîne à zéro part qui garde une vente réglée (sans R26 : 5). 19131 : gardée. L'audit de la répartition à
l'arrivée ne change pas (4 636 justes, 89 nommées, 0 rendue fausse).

### Ce que mesure sa vérification des 5 dates — ⚠ et ma correction (je me suis trompé pour 12182)

- **21662** (8BJKJ6XP) : Hektor **2019-06-20**, Vente Fixée 20/03/2019, réglée 22/03/2019 → **le mois** (juin pour mars, même jour), réglée 2 jours après.
- **16019** (ZYVO6KK1) : Hektor **2025-06-10**, Vente Fixée 10/03/2025, réglée 12/03/2025 → **le mois**, réglée 2 jours après.
- **28147** (HPNJ32UM) : Hektor **2024-01-28**, Vente Fixée 28/01/2025, réglée 03/02/2025 → **l'année** (365 jours, même jour ; avant son propre compromis du 12/11/2024), réglée 6 jours après.
- **7126** (WJ8NY16C) : Hektor **2024-03-13**, Vente Fixée 13/03/2025, réglée 14/03/2025 → **l'année** (avant son compromis du 15/10/2024), réglée 1 jour après.
- ⚠ **12182** (8BUW2ZVH) : Hektor **2020-05-22**, Vente Fixée 18/05/2020, réglée 25/05/2020 → **4 jours d'écart seulement, ce
  n'est PAS une faute d'un an ou d'un mois** : la date Hektor tombe entre la Vente Fixée et le règlement. J'avais écrit
  « fausse d'un an ou d'un mois » pour les cinq : c'est vrai pour quatre. Le protocole ne la prouve pas parce qu'elle n'est
  pas **égale** à la Vente Fixée, pas parce qu'elle est fausse.

---

## 2. Les 19, un par un (sans R26 → avec R26)

**Les 10 que R26 réaligne seule** (la vente rejoint sa ligne → l'écriture est sur une pièce neutre de sa ligne, à sa place) :
1-2. 7126 : règlement + facture de WJ8NY16C
3-4. 12182 : règlement + facture de 8BUW2ZVH
5-6. 16019 : règlement + facture de ZYVO6KK1
7-8. 21662 : règlement + facture de 8BJKJ6XP
9-10. 28147 : règlement + facture de HPNJ32UM
(Et 5 notes posées sur ces ventes ne sont plus à déplacer : 36 → 31 notes.)

**Les 5 dates d'annulation sur le compromis d'une autre tentative — sa règle : la bonne pièce existe-t-elle ? NON pour les 5 →
MISES DE CÔTÉ avec leur ancienne place** (chaque ligne d'origine n'a qu'une offre ; l'autre ligne tient le compromis et a
**sa propre** date, différente) :
11. 17387 : date de 60CLRO51 (01/12/2021) sur le compromis de S3HOG6UL (21/10/2021) — 60CLRO51 n'a que l'offre 17389
12. 24450 : date de 4PW2L3MG (01/02/2022) sur celui de 6U5DQQ4J (21/10/2021) — offre 24454 seule
13. 27134 : date de 2HOL5ISX (01/08/2023) sur celui de IEYXREWQ (01/02/2024) — offre 27140 seule
14. 27195 : date de 739a0db1 (27/07/2026) sur celui de TR42PT5H (20/05/2025) — offres 27196 et 1001520 (créée par C5)
15. 4385 : date de 8RWTD0YX (22/04/2022) sur celui de U0GQ3KTO (22/11/2022) — offres 4387 et 1001477 (C5)
→ **réalignées par la mise de côté** (le geste à blanc les met de côté : elles ne s'affichent plus sur l'autre affaire).

**Les 4 qui restent, expliqués** :
16. **21551**, la note de **53ZS73KW**, sur le compromis de bdb548a3 : la ligne est EN ATTENTE et n'a **plus aucun lien au
    gel** (son lien du 17/11 a été retiré depuis). Aucune pièce pour la recevoir. **Réalignable par une mise de côté** — sa
    règle des dates s'y applique mot pour mot (« elle ne doit pas rester affichée sur l'affaire d'un autre ») : à lui.
17. **11138**, la date de **774aa002** (02/06/2026) : sur un compromis annulé **sans date**, du même mandat 17631, tenu par
    **personne**, seul dans son dossier aujourd'hui et à l'arrivée. C'est très probablement **son** compromis (le seul du
    mandat ; l'offre 11139 est refusée le 02/06/2026, le jour même), que le protocole ne prouve pas parce qu'il n'a pas de
    date. Elle ne ment sur **aucune autre affaire** → **laissée** (même famille que les pièces sans date invisibles).
18. **4496**, la date de **61OW86CS** (21/06/2021) : sur un compromis annulé **sans date**, même mandat 4235, tenu par personne
    — et 4496 est **l'une des 5 exclusions de la règle E** (26613, 21520, 4126, **4496**, 4720) : la nuit le laisse seul à son
    numéro par décision. Même lecture que 17 → **laissée**, à revoir avec les exclusions de E.
19. **3701**, la facture de **I847SPN3** (« GGTI00004428 reportée ») : sur une vente **supprimée chez Hektor** (present 0), seule,
    tenue par personne ; le Sheet dit encore « Offre d'achat ». La facture attend une vente qui n'existe plus chez Hektor.
    Elle ne ment sur aucune autre affaire → **remonte** (sa vente supprimée : R14, la trace figée).

---

## 3. La liste des 42, révisée après R26 (à blanc)

**37 déplacements + 5 mises de côté = 42 gestes** : 31 notes, 4 motifs, 1 date (16377 → 16378), 1 commission
(28568 → 28569), 5 dates mises de côté. Geste simultané (l'échange 27195 ↔ 27196 compris), ancienne place au journal,
chaque écriture **garde sa ligne d'origine**.

- **Inverse : empreinte 0038d306 → 6d0b8e81 → 0038d306, identique.**
- Conservation : 38 721 = 38 716 + 5 mises de côté au journal.
- **Témoin de fin : 46 mal placées sans le geste → 4 après, toutes nommées (16 à 19), 0 hors des nommées.**

Sans R26, le même geste (47 gestes) laisse 14 restes : les 10 de la vente + ces 4.

---

## 4. Ses décisions, notées

- Les 42 : **oui, mais après R26** — la liste ci-dessus est la révisée ; **son « vas-y » attend**.
- Les 5 dates : bonne pièce ? non → mises de côté (fait dans le geste à blanc).
- **V3FO5NDA : pas de copie** — une affaire annulée ne porte aucune part (même raison que les 270 annulées de C2, 17/11).
  ⚠ Ça touche le remède A2 v2 : sa « copie pour la ligne qui part » ne doit **jamais** aller à une annulée. À poser dans A2.
- Les 49 annulées sans part : **on laisse**, aucune part.
- Les 6 supposées par Hektor : **les 6 portent un négociateur au classeur** (A07EC3DH DECHAUD 50 / GENTES 50, DHXRAK9O
  NICOLOSI 100, 72GQRHVB CAVARD 100, 7IHI7YTJ CHAMPAGNAC 100, QXDW8EQA DIMARIA 50 / TRIOLLIER 50, CS38OO8R CHAMPAGNAC 100)
  → **le classeur fait foi** : à remplacer dans A2, l'ancienne mise de côté avec sa place. Aucune ne reste silencieuse.
- ⭐ **SA RÈGLE (24/11) : chaque écriture déplacée garde SA LIGNE D'ORIGINE** — « une écriture qui ne sait plus d'où elle
  vient ne peut plus être contrôlée ».
- La colonne de transaction : **validée dans son principe**, chantier à part, **après cette vague**. Pas ouverte.
- L'ordre : R26 (à son arbitrage) → les 19 (ci-dessus) → les 42 révisés (son « vas-y ») → A2 (la garde est à 0 avec R26) →
  le retrait des exclusions de E dans la même nuit que la vague.
