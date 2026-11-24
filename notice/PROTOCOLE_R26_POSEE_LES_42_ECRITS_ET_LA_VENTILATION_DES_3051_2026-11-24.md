# R26 posée, les 42 écrits, la ventilation des 3 051 — 24/11 (son 4e mot)

> Son mot : « GO SUR R26 — JE L'AI CONTRÔLÉ PAR MES PROPRES MESURES ET ÇA TIENT. ⛔ MAIS TON COMPTE RENDU NE REND PAS
> COMPTE [...] ». « LE GO PORTE SUR R26 ET LES 42 RÉVISÉS, dans TON ordre : R26 -> les 42 -> A2 (la garde est à 0) -> le
> retrait des exclusions de E dans la MÊME nuit que la vague. » « Au geste réel je veux LES DEUX écrites. » « LES TROIS
> POINTS DE LA PARTIE 2 NE BLOQUENT PAS R26 — ils se répondent PENDANT. Mais je ne clôture pas le réalignement tant que les
> 3 051 ne sont pas ventilés. »

Ce qui est écrit aujourd'hui : **le code de R26** (protocole_portes.py) et **le patch des 42 chez Supabase**. Rien dans le
Sheet, rien chez Hektor, pas de push, pas de pull. L'interrupteur des coupes reste éteint. A2 n'est pas écrit.

---

## 1. R26 posée dans le code

- Les 4 ancres de la mesure à blanc, chacune trouvée une fois, posées dans `phase2/checks/protocole_portes.py`.
- Sauvegardes avant la pose (dossier de travail) : `brouillon_detachements_protocole_passage_79_avant_r26_20261124.csv`,
  `portes_passage_79_avant_r26_20261124.json`, `PROTOCOLE_PASSAGE_79_LA_PORTE_DE_CHAQUE_LIGNE_avant_r26_20261124.csv`.
- Passage 79 relancé avec le vrai code (rejeu E puis les portes) : **le brouillon de la vague, le fichier des portes et
  la porte de chaque ligne sont identiques, octet pour octet, à la mesure à blanc** (brouillon 86a6668e des deux côtés).
- 49 lignes désignées, 5 coupes neuves = les 5 ventes ; faux 0, étiquettes changées 0, hors 0, mises de côté fausses 0.
- R26 n'agit qu'à la vague : tant que l'interrupteur est éteint, rien ne bouge en base.

## 2. Les 42 : écrits chez Supabase, avec les deux clés

**L'état d'avant, vérifié chez Supabase et pas dans la copie locale.** Le temps 1 a maintenant une option `--supabase` : il lit
l'état du registre chez Supabase, en lecture seule. Le 24/11 après-midi, il rend la même empreinte que la copie locale,
**0038d306**, avec 46 écritures mal placées.

**Le patch** : `supabase/patch_realignement_42_ecritures_2026-11-24.sql`. Il est fabriqué par
`phase2/checks/realignement_42_generer_patch_2026-11-24.py`, à partir du journal complet du temps 1.
- **Ses gardes** exigent, écriture par écriture :
  - la valeur mesurée sur chacune des 11 sources du registre, et la case vide sur chacune des 6 cibles ;
  - pour chacune des 31 notes, son origine et l'empreinte md5 de son texte ;
  - les 4 nommées à leur place ;
  - l'empreinte des 65 pièces touchées : 37add335, lue en lecture seule.
- **La sauvegarde datée** : les lignes entières des 65 pièces, dans `app_affaire_ledger_avant_realignement_20261124` et
  `app_affaire_note_avant_realignement_20261124`, fermées à l'app.
- **Le journal permanent `app_classeur_realignement_journal`** : 46 lignes, les 42 gestes et les 4 nommées. Chacune porte
  ⭐ **LES DEUX CLÉS** :
  - **l'ancienne place** : la transaction, sa chaîne, son numéro de dossier ;
  - **la ligne d'origine** : l'identifiant, le numéro au Sheet et le lot.

  Les 5 dates mises de côté vivent là, avec leur ancienne place (règle 6). Le fichier des 42 porte maintenant aussi la
  ligne d'origine (`notice/PROTOCOLE_REALIGNEMENT_TEMPS1_LE_GESTE_A_BLANC_PASSAGE_79_AVEC_R26_2026-11-24.csv`).
- **Le geste se fait d'un seul coup** :
  - le registre est vidé, puis posé ;
  - les notes passent par un numéro négatif provisoire, parce que leur clé est unique (l'échange 27195 ↔ 27196, la suite
    27141 → 27134 → 27140) ;
  - le reflet de chaque note (dossier, chaîne) suit la transaction qui la reçoit.

**L'ordre joué :**
1. **À blanc** (le même corps, sans commit, qui finit par une erreur voulue) : toutes les gardes et tous les contrôles
   passent, empreinte d'après **072b3cb3**. Vérifié ensuite : rien n'est resté, ni sauvegarde, ni journal, ni note
   déplacée.
2. **Le geste réel**, qui exige les deux empreintes (37add335 avant, 072b3cb3 après) : passé et validé.
3. **La répétition** : 11 contrôles sur 11 au vert, soit 46 lignes au journal, les deux clés sur les 42, 37 déplacements,
   5 mises de côté, 4 nommées, 31 notes sur leur cible, 0 note à un numéro négatif, 6 cibles posées, 11 sources vidées,
   2 sauvegardes et l'empreinte 072b3cb3.
4. **L'inverse, à blanc** : chaque pièce revient exactement à sa sauvegarde, et **l'empreinte d'avant, 37add335, revient**.
   L'inverse est prêt (`_INVERSE.sql`) et n'est pas joué.

**Le témoin de fin, sur la base réelle** (le temps 1 rejoué chez Supabase après le geste) :
- **46 → 4 mal placées, les 4 nommées**, 0 hors de la liste, 0 geste restant ;
- conservation : 38 716 = 38 721 − 5 mises de côté ;
- famille par famille, les données sont **exactement** l'état prévu à blanc :
  - dates 445 (99b859ec), motifs 169 (30b5007c), commissions 66 (e54d2cdc), notes 4 524 (75143170) ;
  - les cinq autres familles n'ont pas bougé.

⚠ **L'empreinte globale du temps 1 ne revient pas à 6d0b8e81 sur la base réelle, et je le dis.** Elle contient aussi la table
des sources. À blanc, la source suit l'écriture déplacée. Sur la base réelle, elle est retrouvée par la pièce. Les données
sont identiques, famille par famille. Le témoin de l'inverse est donc l'empreinte SQL des 65 pièces (37add335), qui revient.

**Les 4 nommées** sont au journal, sans geste : 3701 (facture), 4496 et 11138 (dates d'annulation), 21551 (note de 53ZS73KW).

---

## 3. La ventilation des 3 051

Fichier : `notice/PROTOCOLE_VENTILATION_DES_3051_PASSAGE_79_2026-11-24.csv`. Chaque écart y porte sa catégorie, sa sous-cause,
la décision ou la lecture qui le range, et son devenir. Outil : `phase2/checks/protocole_ventilation_des_3051_2026-11-24.py`.

```
1 307 ECARTS DE LECTURE + 1 595 HORS PERIMETRE PAR UNE DECISION DEJA PRISE + 149 A TRAITER = 3 051
```

### 3.1. Les écarts de lecture : 1 307

- **997 : la commission_agence de la vente.** Cette colonne n'est pas la commission : c'est la part HT d'une seule personne,
  et ce qu'elle porte change selon l'époque (mesure du 24/11, ④). Ta décision du 24/11 (2e mot) : la sortir du contrôle.
- **126 : la commission relue par la bonne colonne.** Le contrôle lisait les honoraires du seul compromis (montant − prix net
  vendeur). Relue par honoraires_entree ou honoraires_entree_app sur les pièces de la ligne (ta consigne du 24/11), elle
  CONCORDE.
- **141 : des écritures sur une pièce neutre de leur ligne** (42 factures, 44 règlements, 4 annulations, 2 textes F, 49
  textes G). La clé du contrôle, les seules pièces prouvées, ne voit pas la pièce neutre. Le temps 1 l'a jugée : elle est à
  sa ligne au gel, seule, dans son dossier à l'arrivée, donc à sa place.
- **26 factures : le registre porte le texte du Sheet, pas un code GGTI.** C8 a pris la case telle quelle, et le contrôle
  attendait un code. Les 24 « le registre porte une facture » ont un texte identique à la case, à la casse près. S'y ajoute
  ADDDWM5S (le code G431710, posé sur une pièce neutre).
- **16 Charges : aucun numéro de mandat sur les pièces.** La clé du contrôle manque : la Charge vit sur le mandat.
- **1 règlement (OS42NFPY)** : la valeur n'est pas une date lisible, et elle est égale au Sheet.

### 3.2. Hors périmètre par une décision déjà prise : 1 595

- **686 dates** (offre 424, compromis 132, vente fixée 130). Elles relèvent du lot 3 « LES DATES », choix du 09/11 :
  - « un écart de date n'est pas une erreur » (réserve du 29/10, fermée le 09/11) ;
  - ta règle : on ne corrige pas une date ;
  - une date est une preuve du protocole, pas une écriture rapatriée.

  Le détail : 381 « aucune pièce datée de ce jour », 303 « pas de pièce de ce genre », 2 cases illisibles.
- **384 dates d'annulation écartées par C3 (16/11).** Ta règle : « la date d'annulation du Sheet est celle du COMPROMIS »,
  sur un périmètre de 450 que tu as arrêté le 16/11. Le détail :
  - 261 lignes sans compromis (une offre refusée porte déjà sa date de refus, règle du 12/11) ;
  - 106 dates antérieures ;
  - 12 lignes sans transaction ;
  - 4 compromis pas annulés.
- **310 commissions (honoraires).** Le détail :
  - **235** affaires annulées : ta décision du 17/11 (C2) est que leur commission n'est pas posée ;
  - **49** où Hektor porte une autre commission, et **26** où nous en portions déjà une ou où aucune transaction n'était
    reliée. C'est le lot 2 « P : LES VIDES » (09/11) : on ne remplit que nos cases vides, et un conflit n'est pas une
    erreur (44 des 83 du 09/11 étaient un facteur 2, une part contre le total).
- **96 factures et règlements écartés par C8 (16/11), faute de vente** (63 factures, dont 3 en texte libre, et 30
  règlements).
- **119 lignes de répartition :**
  - **59** : une annulée n'a aucune part. Ta décision du 24/11 (3e mot, ④) : « ON LAISSE ».
  - **60** : le rapatriement du 13/11 a refusé la ligne. Ce sont tes règles du 13/11 : un apporteur qui a une part n'est
    pas une personne, et un nom non résolu ne se devine pas. La chaîne garde ce qu'elle avait.
  - **1** : le conflit U0GQ3KTO. Ta décision du 24/11 (2e mot) est de le laisser en réserve.

### 3.3. À traiter : 149, et leur devenir

- **52 sont traitées aujourd'hui :**
  - 37 par le geste des 42 : 6 dates d'annulation, 12 textes F et 19 textes G ;
  - 15 par R26 : les factures, règlements et textes G des 5 ventes, que la coupe emporte avec leur ligne.
- **3 sont nommées au journal** : 11138, 4496 et 3701. La 4e (21551) n'est pas dans le contrôle, parce que sa ligne
  53ZS73KW est en attente.
- **30 relèvent d'A2.** Le détail :
  - 20 écarts (13 lignes) sont corrigés à l'arrivée par la vague et A2 : la chaîne porte la répartition d'une autre ligne
    (6), la chaîne n'a aucune répartition (5), la personne ou la part diffère (2) ;
  - 10 écarts sont les suppositions de Hektor, que le classeur remplacera (ta décision du 24/11, ④).
- **22 (11 lignes) : 9 offres et 2 compromis en attente.** Ils n'ont aucune part à l'arrivée et sont nommés au temps 2.
  Aucune décision n'existe : à toi.
- **23 Charges.** Ta décision du 02/11 (§ 3) est que le classeur fait foi. Le détail :
  - 20 mandats dont le carnet ne porte aucune charge : le lot C1 du 14/11 ne les avait pas reliés ;
  - 3 où le carnet porte une autre charge venue de Hektor (jugées le 03/11).
- **12 nouveautés du Sheet** : 11 factures (GTI00004569 à 4579) et 1 date d'annulation (c6e5299a, 20/11/2026), remplies
  après le rapatriement du 16/11. Le rapatriement ne suit pas le Sheet : à toi.
- **6 lignes dont la date d'annulation n'est posée nulle part** : TR42PT5H, U0GQ3KTO, IEYXREWQ, S3HOG6UL, 6U5DQQ4J,
  R0JRVFDC.
  - Leur compromis portait la date d'une autre ligne, que le geste d'aujourd'hui a retirée.
  - C3 avait écarté leur propre date comme « offre seule », d'après le gel du 16/11. Le protocole leur donne aujourd'hui
    le compromis : 27195, 4385, 27134, 17387, 24450, 16377, tous des compromis annulés.
  - ⚠ Pour S3HOG6UL et 6U5DQQ4J, la date du Sheet (21/10/2021) est antérieure à celle du compromis : la règle de C3 les
    écarterait.
  - Ce serait une écriture neuve : je ne la propose qu'avec la règle complète de C3.
- **1 paire de jumelles** : T2GZOY5O et O6R10ZQA tiennent les mêmes pièces. Le compromis 20073 porte la date de O6R10ZQA
  (21/09/2021) ; le Sheet de T2GZOY5O dit 21/11/2021. À toi.

---

## 4. La répartition : les 172 du contrôle contre les 89 du temps 2

Fichier : `notice/PROTOCOLE_REPARTITION_172_CONTRE_89_PASSAGE_79_2026-11-24.csv`, ligne par ligne.

- **Les 172 écarts du contrôle portent sur 102 lignes** : il compte l'entrée et la sortie séparément. Le temps 2 compte
  89 lignes.
- **Les 89 du temps 2 sont toutes parmi les 102, avec le même écart des deux côtés.** Le détail :
  - 30 annulées dont la chaîne porte la répartition d'une autre tentative, plus 11 annulées sans répartition. Sans part à
    l'arrivée, elles sont laissées : ta décision ;
  - 22 refusées le 13/11, qui sont les « noms non résolus » du temps 2. 8 autres refusées le 13/11 sont des annulées ;
  - 9 offres et 2 compromis en attente, sans répartition ;
  - les 6 suppositions de Hektor ;
  - le conflit U0GQ3KTO.
- **Les 13 lignes du contrôle seul** sont fausses aujourd'hui et justes à l'arrivée : la vague et A2 les corrigent.
- **Ce que chacun regarde :**
  - le contrôle regarde l'état d'aujourd'hui (la chaîne de la ligne aujourd'hui), entrée et sortie séparées ;
  - le temps 2 regarde l'état d'arrivée (après la vague et le remède A2), ligne par ligne ;
  - aucune ligne n'est dans le temps 2 seul.

---

## 5. Les avis : ses 10, mes 4

- **Mes 4 et ses 10 ne mesurent pas la même chose.**
  - Mon temps 1 jugeait le **contenu** des avis (les trois textes contre le Sheet). Ses 4 (3b5db3cc, 84c91bb8, c6c8bc29,
    df0ce30c) sont des cases du Sheet changées depuis le 16/11.
  - Il ne jugeait **pas le reflet du dossier** (numéro et identifiant). Ce reflet est le sujet d'A1.
- **Ses 10 ont été trouvés deux fois.** Ce sont les 10 « décollés » de ma mesure du 23/11 (« 2 543 d'accord, 10 décollés »).
  Les 10 sont aussi dans la liste A1 à blanc des 107 reflets à recalculer. Mon compte rendu ne les nommait pas : c'est la
  faute.
- **Mesure chez Supabase du 24/11** (la règle de C9 : la ligne, ses liens au gel, les étiquettes d'aujourd'hui), 2 588 au
  total :
  - **2 543 JUSTES** ;
  - **10 FAUX des deux côtés** (exactement ses 10) ;
  - 7 reflets posés sur une ligne qui est à cheval aujourd'hui ;
  - 28 reflets vides : 18 lignes à cheval, 7 lignes à une seule étiquette, 3 sans lien.
  - Ses 2 550 = mes 2 543 + les 7 à cheval ; ses 25 = 18 + 7.
- **Le motif est le même que l'étiquette du 23/11** : la clé est bonne (la ligne), le reflet posé le 16/11 n'a jamais été
  entretenu. Par exemple, 205f62be porte D2025-0257, alors que sa ligne est aujourd'hui sur D2025-0417.
- **Par la vague, pas à part.** Ma proposition :
  - 8 des 10 changent encore de dossier à la vague : A1 à blanc leur donne un numéro neuf. A07EC3DH et MCD6CRNB gardent
    leur numéro d'aujourd'hui.
  - Les rafraîchir aujourd'hui, ce serait écrire deux fois.
  - Personne ne les voit aujourd'hui : la table n'est ouverte ni à authenticated ni à anon, et aucun code ne la lit (ni
    apps, ni backend, ni Console, ni scheduled, ni phase2/sync).
  - A1 les recalcule depuis la ligne, la nuit de la vague, avec un contrôle des décollés à 0.

## 6. Le notaire : une décision, pas un oubli

- Décision du **09/11**, citée dans `notice/DECISIONS_CHAMP_PAR_CHAMP_CLASSEUR_2026-11-02.md` (lot 5, O) : « le notaire on ne
  récupère rien ».
- La raison : nous portons **deux** notaires (acquéreur, mandant), le classeur **un seul** ; remplir nos vides demanderait de
  deviner dans lequel écrire (483 vides au 09/11).
- Les chiffres du 24/11 :
  - le Sheet porte un notaire sur 2 586 lignes, dont 2 541 tranchées ;
  - le registre porte les notaires de Hektor (origine api 8 403, console 8 758 ; notaire acquéreur sur 9 351
    transactions, notaire mandant sur 9 201) ;
  - **503 lignes tranchées** ont un notaire au Sheet et aucun notaire sur leurs pièces chez nous.
- Son « 0 sur 31 372 » est juste pour l'origine « classeur ».

## 7. Ce qui suit

- **A2**, avec ses décisions : aucune copie vers une annulée (V3FO5NDA comprise) ; les 6 suppositions remplacées par le
  classeur, l'ancienne mise de côté avec sa place ; la garde à 0 avec R26. À mesurer à blanc, puis à lui.
- Le retrait des exclusions de E (4126, 21520), **la même nuit que la vague**, jamais avant. L'interrupteur reste éteint
  jusque-là.
- À lui :
  - les 11 offres et compromis en attente sans part ;
  - les 23 Charges ;
  - les 12 nouveautés du Sheet ;
  - les 6 dates à poser (selon la règle de C3) ;
  - la paire T2GZOY5O / O6R10ZQA ;
  - les 4 nommées.
