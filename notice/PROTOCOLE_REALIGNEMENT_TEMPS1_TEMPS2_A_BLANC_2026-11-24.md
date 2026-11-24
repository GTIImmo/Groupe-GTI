# Le réalignement des écritures rapatriées — temps 1 et temps 2, à blanc (24/11/2026)

> Réponse à son mot du 24/11 (2e) : « je te demande de RÉALIGNER les écritures rapatriées — en deux temps ».
> ⛔ **Rien n'est écrit** : ni base, ni Sheet, ni Hektor, pas de push, pas de pull. L'interrupteur des coupes reste éteint.
> Passage 79 (v21), image du 23/11 08:02, registre : `phase2.sqlite` de la descente du jour.

Outils (lecture seule) :
- `phase2/checks/protocole_realignement_temps1_a_blanc_2026-11-24.py` (temps 1 : audit, décisions, geste, inverse, témoin)
- `phase2/checks/protocole_realignement_temps2_repartition_a_blanc_2026-11-24.py` (temps 2 : la répartition à l'arrivée, la garde)
- `phase2/checks/protocole_a1_a2_a3_le_remede_a_blanc_2026-11-24.py` (+ A3 bis : les conditions)

Fichiers (tous ligne par ligne) :
- `notice/PROTOCOLE_REALIGNEMENT_TEMPS1_LES_ANOMALIES_PASSAGE_79_2026-11-24.csv` — chaque écriture qui n'est pas « juste », avec ses trois clés, sa décision proposée et sa raison
- `notice/PROTOCOLE_REALIGNEMENT_TEMPS1_LES_TROUS_PASSAGE_79_2026-11-24.csv` — le témoin inverse : chaque ligne dont le Sheet porte la valeur sans que sa pièce l'ait, avec sa cause
- `notice/PROTOCOLE_REALIGNEMENT_TEMPS1_LE_GESTE_A_BLANC_PASSAGE_79_2026-11-24.csv` — les 42 déplacements et leur inverse
- `notice/PROTOCOLE_REALIGNEMENT_TEMPS2_REPARTITION_A_L_ARRIVEE_PASSAGE_79_2026-11-24.csv` — les 89 lignes dont la répartition ne correspond pas à l'arrivée
- `notice/PROTOCOLE_REALIGNEMENT_TEMPS2_LA_GARDE_VENTES_REGLEES_PASSAGE_79_2026-11-24.csv` — les 5 chaînes de la garde
- `notice/PROTOCOLE_REALIGNEMENT_TEMPS2_PARTS_SANS_LIGNE_A_L_ARRIVEE_PASSAGE_79_2026-11-24.csv` — les 21 chaînes à parts du classeur sans ligne d'arrivée

Le nom du compte admin : 0 occurrence dans les six fichiers ; le témoin positif (le Sheet de l'image) en porte 4.

---

## 0. Ce qui existait déjà (lu AVANT de mesurer)

- **Les rapports des lots disent la ligne de chaque écriture** : c'est la clé de tout l'audit, pas une devinette.
  C8 `notice/C8_VENTE_REGLEE_ET_FACTURE_2026-11-16.csv` · C3 `notice/C3_OU_SE_POSENT_LES_DATES_ANNULATION_2026-11-16.csv` ·
  C4 `notice/C4_LES_MOTIFS_RETENUS_2026-11-17.csv`, `notice/C4_LES_NOTES_A_POSER_2026-11-17.csv`, `notice/C4_LOTS_1_ET_2_2026-11-17.csv` ·
  C5 `phase2/checks/poser_offres_annulees_classeur_2026-11-16.py` (la ligne est écrite dans le texte de la note) ·
  C2 `notice/C2_LES_COMMISSIONS_A_POSER_2026-11-17.csv` · C9 `notice/C9_LES_AVIS_DU_CLASSEUR_2026-11-16.csv` ·
  la charge : `phase2/checks/poser_charge_classeur_2026-11-04.py`.
- **La commission** : `notice/LES_38_COLONNES_CONSOLIDE_2026-10-28.md` l. 120 (« Commission TTC → `honoraires_entree_app`, classe A »)
  et l. 268-280, 404-412 ; l'artefact « Classeur, les 38 choix », colonne P (« le classeur note une part, nous le total ») ;
  le lot C2 et sa décision « Les 62 seules ». ⛔ `commission_agence` est **sortie du contrôle**, et c'est déclaré dans l'outil.
- **Les décisions de C4 sur la colonne F** : `notice/C4_LE_DECODAGE_DE_LA_COLONNE_F_2026-11-16.md` l. 190-199 :
  « V » seul écarté (1 537), pictogramme seul écarté (427), prénom derrière un V écarté (28).

## 1. Ses réponses, reprises

- ① le retrait des exclusions de E : posé **dans la nuit de la vague seulement**, avec ses 4 morceaux.
- ② **U0GQ3KTO** : rien recopié, laissé, en réserve. **NRZVKH85** : complété de la part de sortie FERNANDEZ 50 %,
  l'existante intacte — fait dans le remède à blanc (temps 2).
- ③ `commission_agence` sortie du contrôle ; la Commission TTC comparée à `honoraires_entree`.
- ④ A3 : son 155 datait d'avant le run ; 161 est le bon.
- ⑤ pas de « vas-y » pour A1-A2-A3 : rien n'est codé, tout est à blanc.

---

## 2. TEMPS 1 — ce qui ne bougera plus

### ① L'audit, écriture par écriture (38 721 écritures)

Chaque écriture est jugée par **trois clés côte à côte** : la ligne que **le gel** désigne (sa définition), la ligne
que **le protocole** donne (le chaînage corrigé), et **la ligne d'où elle vient** (le rapport du lot).

- **Vente Réglée** 3 729 : 3 678 justes · 44 sur une pièce neutre de leur ligne · 5 que la vague sortirait · 2 de lignes en attente.
- **Numéro de facture** 3 671 : 3 620 justes · 43 neutres · 5 que la vague sortirait · 1 sur une vente hors de sa ligne (3701, I847SPN3) · 2 en attente.
- **Annulée** 450 : 426 justes · 4 neutres · 12 de lignes en attente · 6 sur le compromis d'une autre ligne · 2 hors de leur dossier.
- **Le motif** 169 : 161 justes · 4 en attente · 4 mal placés.
- **Commission TTC** (`honoraires_entree_app`) 66 : 59 justes · 1 neutre · 1 mal placée · 1 en attente · 4 saisies dans l'app (pas rapatriées).
- **Les notes** 4 524 : 4 130 justes · 190 sur la transaction que le lot C5 a créée pour leur ligne · 51 neutres ·
  38 dont la case du Sheet s'est allongée depuis le lot · 51 dont la case a changé · 17 de lignes en attente · 9 saisies humaines ·
  1 juste pour la ligne qui tient la pièce (9WQ204HP) · 37 mal placées.
- **Les conditions** 33 : 18 justes · 10 dont la case a changé · 5 saisies humaines.
- **La charge** (sur le mandat) 853 : 850 justes · 3 de lignes en attente (BR8ZTN5F, 6684bcf1, HUY49KEC).
- **Les trois avis** 2 588 (clé = la ligne elle-même) : 2 584 justes · 4 dont la case a changé depuis le 16/11.

⭐ **« Pièce neutre »** : la pièce est à sa ligne au gel, seule, dans son dossier aujourd'hui et à l'arrivée ; le protocole
ne la prouve pas (sa date n'est pas celle du Sheet) mais ne la donne à personne. L'écriture y est à sa place.

### ⭐ Ses 8, retrouvés une par une — et deux de plus

Sa définition (la valeur ne colle à aucune ligne que le gel désigne, et colle à une autre) rend **10** écritures :
ses 6 notes (6555, 14111, 16377, 21551, 23050, 27196), ses 2 dates (16377, 27195), **plus** la note de **27195**
(l'autre moitié de la paire croisée : 27195 porte le contenu de 739a0db1, 27196 celui de TR42PT5H) et le **motif de 16378**
(le motif de CITFQGOB posé sur le compromis de RX6J289Y).

Par la **transaction** (le protocole), j'en trouve **61** : ses 10 et 51 autres que le gel ne peut pas voir, parce que
le gel lui-même pointe vers la ligne d'origine (la pièce est à elle au gel, mais le protocole la donne à une autre ligne
ou à personne, ou la vague la sortira de son dossier).

### ⚠ Ses 266 notes « qui ne collent à aucune ligne »

Par morceau (F et G séparés, préfixes retirés), je trouve : **190** notes du lot C5 (leur texte est une phrase fabriquée,
« Acquéreur au classeur : … », pas une case du Sheet), **38** dont le texte est toujours dans la case, qui a grandi depuis
le 17/11 (journaux datés, récents en haut), et **51** dont la case a changé. Ça fait 279 ; l'écart avec ses 266 vient
sans doute de la comparaison brute. **Confirmé : ce sont des cases modifiées, pas des erreurs — rien à corriger.**

### ⛔ Le témoin inverse, colonne par colonne (les lignes tranchées dont le Sheet porte la valeur)

- **Vente Réglée** 3 757 : 3 722 portées par leur pièce · 30 écartées par C8 (aucune vente) · 5 portées ailleurs (les 5 de la vague).
- **Numéro de facture** 3 746 : 3 663 portées · 66 écartées par C8 · 11 remplies après le lot · 6 portées ailleurs.
- **Commission TTC** 4 725 : 4 397 portées · 235 annulées écartées par C2 (« Les 62 seules ») · 31 conflits de montant
  (« prendre les vides » : on ne corrige pas) · 15 facteur 2 (une part) · 28 trous (aucune pièce n'a de commission) ·
  18 que C2 voyait sur une pièce du gel que le protocole ne leur donne plus · 1 trou.
- **COMMENTAIRES** 4 090 : 4 030 portées · 35 remplies après le lot · 21 portées ailleurs (les mal placées) · 4 sur une pièce hors de leur ligne.
- **En attente de** 3 038 : 846 portées · 1 559 « V » / « V prénom » écartés par C4 · 411 pictogrammes seuls écartés par C4 ·
  153 portées par le motif traduit · 23 remplies après le lot · 40 portées ailleurs · le reste nommé.
- **Annulée** 829 : 430 portées · 381 écartées par C3 (offre seule 260, date antérieure 105, aucune transaction 12, compromis pas annulé 4) ·
  8 portées ailleurs · 7 dont la pièce porte une autre date · 2 trous · 1 remplie après le lot.
- **Charge** 953 : 914 portées par le carnet de leur mandat · 20 mandats sans charge · 16 lignes sans mandat · 3 autre charge (Hektor).
- **Avis** 2 598 : 2 588 portés · 10 remplis après le 16/11.

### ② Les décisions proposées (une par anomalie, au fichier)

- **DÉPLACER — 42 écritures** : 36 notes, 4 motifs, 1 date d'annulation (16377 → 16378, le compromis de RX6J289Y),
  1 commission (28568 → 28569, l'offre de 959b7669). Chaque fois vers la pièce que le protocole donne à la ligne d'origine,
  choisie par la règle du lot qui l'avait posée, et **libre**. Dont **l'échange de la paire croisée** (les notes de 27195 et 27196),
  et 27134 ↔ 27141 (2HOL5ISX / IEYXREWQ).
- **REMONTE — 19 écritures mal placées, nommées** :
  - **10 = les 5 ventes réglées que la vague détacherait** de leur ligne (règlement + facture sur 7126, 12182, 16019, 21662, 28147) :
    la question est au **protocole**, pas à l'écriture (voir le temps 2) ;
  - **5 dates d'annulation sur le compromis d'une autre tentative du même bien** (17387, 24450, 27134, 27195, 4385) :
    la ligne d'origine n'a qu'une offre (la règle de C3 n'y pose pas de date) et la ligne qui tient le compromis a
    **sa propre date, différente**. Proposition : **mettre de côté** la date déplacée ; la case de l'autre ligne
    devient un trou que C3 remplirait par sa règle, à son accord ;
  - 2 dates sur un compromis hors de leur ligne (11138, 4496) ; 1 facture sur une vente hors de sa ligne (3701) ;
  - 1 note de 53ZS73KW (ligne en attente, sans aucun lien au gel aujourd'hui) posée sur 21551, la pièce de bdb548a3 :
    proposition, la mettre de côté.
- **REMONTE, bien placées, à confirmer pas à corriger** : 51 notes, 10 conditions, 4 avis dont la case a changé.
- **LAISSER** : les pièces neutres (143), les 190 notes C5, les cases allongées (38), les lignes en attente, les saisies humaines.

### ③ Le geste, à blanc, et son inverse

Les 42 déplacements sont **simultanés** (un échange libère sa cible en même temps qu'il la prend). L'ancienne place de
chaque écriture va **au journal** (règle 6). L'inverse rejoue le journal et repose l'état de départ :
**empreinte de départ 0038d306 → après le geste 65191702 → après l'inverse 0038d306 : identique**.
Conservation : 38 721 écritures avant, 38 721 après.

⭐ Une écriture **porte sa ligne d'origine** quand elle bouge (sans ça, le contrôle d'après-geste la perdait et pouvait
passer pour de faux — trouvé et corrigé pendant la mesure).

### ④ Le témoin de fin

- **Sans le geste : 61 écritures mal placées.**
- **Après le geste : 19, toutes NOMMÉES (remontées), et 0 hors des nommées.**
- Le témoin inverse monte d'autant : COMMENTAIRES 4 030 → 4 054, En attente de 846 → 873, Annulée 430 → 431, Commission 4 397 → 4 398.

---

## 3. TEMPS 2 — la répartition, sur l'état d'arrivée

Le rejeu E du passage 79 (la vague) + le remède A2 à blanc + ses deux décisions. Comparaison **par personne**, après la
résolution des noms du 13/11 (qui absorbe les variantes).

### Le remède, corrigé en mesurant

- **v1** (celui du matin) **vidait 19131 et 19814** alors que la ligne qui y arrive (6FQO29C8, 4G2UHO35) **reconnaît
  exactement ces parts** : c'est sa découverte 1, et c'était un défaut de ma règle, pas un cas à part.
- **v2** : une chaîne n'est **jamais vidée** quand une ligne tranchée qui y arrive reconnaît ses parts — elle les garde, et la
  ligne qui part en reçoit une copie (13 chaînes) ; plus **l'échange** de la paire croisée (739a0db1 ↔ TR42PT5H) ; plus les
  lignes dont les parts sont sur une autre de leurs chaînes que celle du gel (3).
- **v2 : 503 parts recopiées (dont 4 par échange), 147 mises de côté avec leur ancien numéro, 1 complétée (NRZVKH85),
  2 conflits ; conservation 18 264 = 17 907 − 147 + 503 + 1 : boucle.**
- **19131 n'est plus touchée** : elle garde TEYSSONNIER 50 + 50 pour 6FQO29C8 (vente réglée). V3FO5NDA (annulée) en reçoit une
  copie — à lui de dire s'il la veut (une annulée ne verse rien).

### ① L'audit à l'arrivée (4 725 lignes tranchées)

- **Après le remède v2 : 4 636 justes.** Sans le remède : 4 388. Le remède en rend justes **248** et n'en rend **aucune fausse**.
- **89 restent, toutes nommées** :
  - **60 sans part** : **49 annulées**, 9 offres, 2 compromis en attente, **aucune vente réglée** (sans le remède : 94 ventes
    réglées seraient sans part). 32 annulées partageaient leur chaîne avec une autre tentative et c'est la répartition de
    l'autre qui avait été écrite (règle du 14/11 : une répartition par chaîne) ; 28 lignes n'ont jamais eu de part chez nous ;
  - **22 noms non résolus** : 21 apporteurs avec une part (meilleursagents 15, GTI 5, DENOPCE 1), mis en quarantaine par la
    règle du 13/11, et 1 nom absent de l'annuaire (PITIOT) ;
  - **6 noms qui diffèrent**, tous des **suppositions de Hektor jamais remplacées** (`hektor_partage_suppose`) :
    A07EC3DH, DHXRAK9O, 72GQRHVB, 7IHI7YTJ, QXDW8EQA, CS38OO8R ;
  - **1 conflit nommé** (U0GQ3KTO, sa décision).
- **21 chaînes à parts du classeur sans ligne d'arrivée** : 12 attendent avec les lignes en attente (les impossibles),
  9 n'ont plus de ligne au gel.

### ② ⛔ La garde : 5 chaînes, pas une seule

**Après le rejeu, 5 chaînes gardent une vente réglée sans aucune part.** Ce n'est pas 19131 (le remède v2 la garde).
Ce sont **les 5 mêmes ventes que le temps 1** :
8BJKJ6XP (vente 21662), 8BUW2ZVH (12182), HPNJ32UM (28147), WJ8NY16C (7126), ZYVO6KK1 (16019).

**La cause est la vague, pas le remède** : pour ces 5 lignes, la « coupe neuve » du protocole emporte l'offre et le
compromis de la ligne dans un dossier neuf et **laisse la vente derrière** (preuve : le brouillon des coupes du passage 79,
lignes `protocole_coupe_neuve` de ces 5 lignes). Le protocole ne prouve pas la vente parce que **la date Hektor de la vente
a une faute de saisie** (l'année ou le mois) : 2019-06-20 contre 20/03/2019, 2020-05-22 contre 18/05/2020,
2024-01-28 contre 28/01/2025, 2024-03-13 contre 13/03/2025, 2025-06-10 contre 10/03/2025 — chaque fois réglée quelques jours
après la « Vente Fixée » du Sheet. On ne corrige pas une date.

Sur les 237 coupes neuves, **19 pièces neutres** sont laissées derrière : ces 5 ventes réglées, 7 offres, 7 compromis.

➡ **Proposition de règle (R26)** : *« une coupe neuve emporte la VENTE neutre de sa ligne — seule vente de son dossier
aujourd'hui, à elle seule au gel, que personne ne tient »*. Elle ne touche que la vente (l'argent), pas les 7 offres et
7 compromis. Attendu : la garde tombe à 0. **Pas mesurée** : il faut un passage du protocole et un rejeu E.

⛔ **Donc A2 ne s'écrit pas** : la garde n'est pas nulle, elle est expliquée, et sa cause est en amont (le protocole).

### ③ Le témoin de fin

Après le remède : **89** lignes dont la répartition ne correspond pas, toutes nommées par verdict ; sans le remède : **337**.

### A3 bis — les conditions (sa 4e table)

Les **28 conditions du classeur** ont leur reflet juste aujourd'hui **et après la nuit** (0). Les 5 « faux » sont les
**5 saisies d'essai du 23/10**, sur des transactions de la plage app absentes de l'image (1001388, 1001391, 1001394).

---

## 4. La solution durable, chiffrée : une colonne de transaction pour la répartition

**Mon avis : oui, et c'est la seule fermeture définitive.** Aujourd'hui la part est accrochée au numéro de chaîne, qui
est une conclusion recalculée chaque nuit ; c'est la 4e famille du même défaut (avis, honoraires, notes, conditions).

- **Ce que ça fermerait** : le remède A2 lui-même, les orphelines du moniteur, le recalcul de D8 (« la répartition suit son
  dossier »), et la question « de quelle vente vient cette part ».
- **La reprise, mesurée** : sur 8 837 chaînes à parts, **8 809 (17 851 parts, 99,7 %) ont une transaction de tête unique**
  — la vente (8 082 chaînes), sinon le compromis (453), sinon l'offre (274). **56 parts restent à décider** :
  30 sur des chaînes à plusieurs compromis ou offres, 26 sur des chaînes absentes de l'image (les 26 orphelines).
- **La clé** : la transaction de tête **et**, pour les parts du classeur, la ligne d'origine (`id_unique`) dans une
  colonne fixe — la traçabilité qui manque aujourd'hui pour prouver un réalignement.
  `app_chaine_id` devient un reflet, recalculé depuis la transaction, comme les notes.
- **Ce que ça toucherait** (lu dans le code) : le front (`apps/hektor-v1/src/lib/api.ts`, `pilotage.ts`), le worker
  (`Console/console_job_worker.js`, 1 endroit), la synchro (`phase2/sync/pull_from_supabase.py`, `repartition_commission.py`,
  `backup_critical.py`), `phase2/identite/convertir_repartition_commission.py`, et les fonctions posées par les patchs
  `supabase/` (la RPC de saisie du 14/09, la garde du 15/09, D8 du 28/10, le 3e rang du 02/11, le registre des négociateurs
  du 04/11, la sentinelle des orphelines). Le front lit par chaîne : il ne change pas si le reflet est tenu.
- ⚠ **La question à trancher** : quand la vague détache la vente de sa ligne (les 5), la part attachée à la vente suit la
  vente. C'est juste si la vente est la bonne (R26 d'abord).

⛔ **« On supprime tout et on repasse » : je ne vois pas mieux que sa règle**, « replacer depuis ce qui ne bouge pas,
garder l'ancien en garde ». Une seule chose de plus : **chaque écriture déplacée doit porter sa ligne d'origine** (c'est ce
qui permet de prouver le réalignement, et ce qui a manqué à mon premier témoin de fin).

---

## 5. Ce qui attend sa décision

1. **Les 42 déplacements du temps 1** : le « vas-y » pour les écrire (patch, inverse, répétition) — ou des retraits.
2. **Les 5 dates d'annulation** posées sur le compromis d'une autre tentative : mettre de côté ?
3. **R26** (la vente part avec sa ligne) : la mesurer par un passage du protocole, avant toute vague.
4. **V3FO5NDA** (annulée) : lui donner la copie de TEYSSONNIER, ou rien ?
5. Les 6 suppositions de Hektor jamais remplacées, et les 49 annulées sans part : laisser, ou reprendre du classeur ?
6. La colonne de transaction : chantier à part, quand il le dira.
