# Réponses 21 ter — le rejeu du patch, les lignes en attente, les lignes 23 et 535

> L3 · chantier classeur · ㉑ ter · 22/11 soir. Son mot : `C:\Hektor\mot_du_22_11_reponses_21ter.md`.
> **Rien n'est écrit** : ni en base, ni dans le Sheet, ni chez Hektor. Rien n'est poussé.
> Aucune règle du protocole ne change (protocole v3.1). Tout ce qui suit est mesuré en lecture seule, ou sur des copies en mémoire.

---

## 1. Le patch du journal — ta preuve n'est pas encore faite, et il me manque un moteur

**Je te contredis sur un point, parce que je l'ai mesuré.** L'outil de ce matin (« zéro écart sur 31 368 ») ne rejoue pas la fonction SQL. Il rejoue une **copie en Python** des règles de la pose (`coupe_preuve_interne.pose_de_nuit`). Il ne voit donc pas le patch. Refaire ce rejeu-là ne prouverait rien sur la fonction modifiée.

**La vraie preuve demande de faire tourner la vraie fonction**, le texte lu chez Supabase, sur une copie. Il n'y a **aucun Postgres sur la machine** : ni installé, ni portable, ni dans WSL (aucune distribution). Je ne le fais pas tourner en production, même dans une transaction annulée : tu as dit « sur une copie ».

**L'outil est prêt** : `phase2/checks/rejeu_patch_journal_sur_copie.py`, en deux étapes.

- **`extraire`** est fait, en lecture seule, le 22/11 à 20:12. La copie a tout ce que la pose lit et écrit, et rien d'autre :
  - le registre : 31 368 pièces, les 8 colonnes que la pose lit ;
  - les années de mandat : 27 511 lignes ;
  - les dates convenues : 5 ;
  - le compteur : 25 années ;
  - le journal : 11 657 lignes ;
  - les 5 fonctions, mot pour mot, dont la pose à l'empreinte du patch (815e956f…).

  Chaque table a son empreinte calculée par Postgres. La copie fait 8,2 Mo et vit dans `C:\Hektor\chantier_classeur_q6_cache\rejeu_patch_journal\2026-11-22_201242\`. Les seuls déclencheurs du registre suivent les parties (acquéreurs, mandants…), et la pose n'y touche pas : la copie n'en a pas besoin.

- **`rejouer`** attend le moteur. Sur un Postgres local, il fera :
  - **la copie relue** : ses empreintes comparées à celles de Supabase, table par table, et les 5 fonctions comparées par leur empreinte ;
  - **le fichier du patch, joué tel quel** sur la copie, exactement celui que tu colleras : sa garde, sa colonne, sa fonction, ses 190 lignes et son contrôle. Puis sa répétition (9 contrôles), et son retour arrière sur une autre copie : la fonction doit revenir à 815e956f ;
  - **cinq états**, chacun rejoué avec la fonction d'aujourd'hui et avec la fonction modifiée, à partir du même départ :
    1. **aujourd'hui** : c'est ta question mot pour mot, les 31 368 pièces doivent garder leurs étiquettes et leurs numéros ;
    2. **l'arrivée du protocole** : ses fusions, ses scissions et ses 275 numéros neufs, comparés aussi à ma prédiction ;
    3. **un état défait** : des groupes sans étiquette, pour exercer la pose et la propagation ;
    4. **l'arrivée à blanc** : rien ne doit bouger ;
    5. **l'état défait avec une limite de 25**.

    On compare chaque pièce (chaîne, étiquette, numéro), le compteur, les lignes neuves du journal et ce que la fonction rend ;
  - **l'ancien numéro écrit** à chaque scission et à chaque fusion, vérifié ligne par ligne ;
  - **un témoin inverse** : le patch faussé exprès (le rang d'une scission + 1) doit faire crier la comparaison, sinon elle est aveugle.

⛔ **Ce qu'il me faut pour le lancer : télécharger un Postgres portable**, de la même version que Supabase (17.6).
- **Le paquet :** `@embedded-postgres/windows-x64`, version `17.6.0-beta.15`, sur le registre officiel npm (registry.npmjs.org).
- **La taille :** environ 101 Mo une fois décompressé.
- **L'installation :** dans `C:\Hektor\outils\postgres17`, hors du dépôt. Aucun service n'est créé. Il écoute seulement sur la machine (port 54329), il est démarré pour le rejeu et arrêté après.

Avec ton accord, le rejeu prend quelques minutes, et je te donne le chiffre.

---

## 2. Les 63 — la règle du plus ancien est appliquée, il n'y a rien à coder

C'est la règle même de la nuit : à une scission, l'étiquette reste au morceau de la plus petite pièce ; à une fusion, on garde celle de la plus petite pièce. Je n'y reviens plus.

Un fait seulement, pour que tu ne le découvres pas plus tard : ta ligne 23 (§ 5) le montre. **Un numéro GARDÉ par une fusion porte l'année de sa propre naissance, pas celle de l'affaire.** C'est le cas de 15 dossiers sur 11 551 aujourd'hui (écarts du témoin de l'année). Par exemple, D2024-0456 est né d'un compromis annulé sans date, daté par son mandat (12/12/2024), alors que l'affaire s'ouvre en 2025. Les **numéros neufs**, eux, portent bien l'année de l'ouverture de leur affaire.

## 3. 86da6949 — ton accord est noté pour les trois

Tes trois lignes figées sont 3942 (D2021-0326), 4015 (D2020-0527) et 4724 (D2026-0297, l'offre 29000 refusée). Elles restent dans le reste à vider, et chaque passage les nomme (protocole v3.1).

---

## 4. Demande A — on LAISSE EN PLACE, et c'est mesuré sur les 225

Outil : `phase2/checks/protocole_en_attente_garde_son_numero.py`. Fichier : `notice/PROTOCOLE_LES_LIGNES_EN_ATTENTE_GARDENT_LEUR_NUMERO_PASSAGE_22_2026-11-22.csv`.

**L'écriture ne vide rien, à aucun des trois endroits où un numéro vit :**

- **la case A de ton Sheet.** Elle est vide pour les 225 lignes en attente, et elle le restera. L'écrivain ne remplit qu'une case vide d'une ligne de la vague. Une ligne en attente n'est dans aucune vague. Une case déjà remplie est sautée (« on n'écrase jamais »). Le seul geste qui vide une case est le retour arrière, et il ne vide que notre propre valeur ;
- **`app_classeur_avis`**, où vit le D2025-0107 de ta ligne 40. Aucun geste du protocole n'y écrit ;
- **le registre** (les étiquettes de la nuit), à l'arrivée :
  - 153 lignes gardent exactement leur dossier et leur numéro ;
  - 69 n'ont aucune pièce au gel, donc aucun numéro à perdre ;
  - 3 changent de numéro (ci-dessous).

**Tes trois premières :**
- ligne 40 (DPK4WZC3) : D2025-0107, et D2025-0107 à l'arrivée ;
- ligne 105 (CC8TJTBR) : D2025-0039, et D2025-0039 à l'arrivée ;
- ligne 311 (UBSIJYPW) : D2024-0279, et D2024-0279 à l'arrivée.

**Tes 35 lignes des 2 560 : les 35 gardent leur numéro.** ⚠ Trois d'entre elles portent déjà un autre numéro que celui du 16/11 : la règle E les a déplacées la nuit du 21/11 (§ 5). C'est le numéro d'aujourd'hui qui est gardé :
- ligne 1700 : D2021-0477 → D2021-0739 ;
- ligne 4291 : D2025-0257 → D2025-0417 ;
- ligne 4626 : D2026-0184 → D2025-0435.

⚠ **Les 3 lignes qui changent de numéro ne sont pas vidées.** Leur dossier est coupé par la porte d'une voisine tranchée. Par la règle du plus ancien, l'ancien numéro reste au morceau de la plus petite pièce, celui de la voisine, et elles en reçoivent un neuf :

- **ligne 3900 (RGCEC677)**, en attente par le verrou :
  - ses pièces 4542 et 4545 passent de D2021-0130 à D2021-0757 ;
  - la vente de la ligne 1379 (Z0BDVNBZ, pièces 4541 et 4546) garde D2021-0130.
- **ligne 3990 (Z3DYDC4X)**, en attente par le verrou :
  - sa pièce 14111 passe de D2021-0025 à D2021-0772 ;
  - la ligne 1932 (AYIHPHF5) garde D2021-0025.
- **ligne 4005 (SBH4QWDW)**, en attente, ses pièces à part :
  - sa pièce 23054 passe de D2021-0041 à D2021-0800 ;
  - la ligne 3910 (VMWFLLW4) garde D2021-0041.

Aucune des trois n'affiche de numéro aujourd'hui : leur case A est vide, et elles ne sont pas dans les 2 560. Rien n'est écrit en face d'elles. Quand leur cas sera tranché, elles prendront le numéro que leur dossier porte alors. **Comme l'écriture ne vide rien, je n'ai pas ajouté de garde.**

---

## 5. Demande B — les lignes 23 et 535, et les 15 autres du même genre

Outil : `phase2/checks/protocole_ce_qui_a_deplace_les_2560_depuis_le_16_11.py`. Fichier : `notice/PROTOCOLE_CE_QUI_A_DEPLACE_LES_2560_DEPUIS_LE_16_11_PASSAGE_22_2026-11-22.csv`.

**Ce n'est pas le protocole qui les déplace : c'est déjà fait, par la nuit.** Leurs pièces portent déjà D2024-0456 et D2024-0477 dans le registre aujourd'hui. Le D2025-0129 et le D2023-0541 du témoin sont ceux du 16/11, recopiés par C9. D'où le « RIEN » dans la colonne de la porte : à l'arrivée, le protocole ne change plus rien à ces deux lignes. Mais tu as raison : il faut nommer ce qui les a déplacées.

### Ta ligne 23 (MCD6CRNB, bien 14414) : la porte est la RÈGLE E, ta décision du 20/11

- **Le journal :**
  - 12/11 : première pose. Le compromis 7080, seul, reçoit D2024-0456. Il n'a pas de date, donc son année vient de son mandat, signé le 12/12/2024. Les pièces 7081 à 7083 reçoivent D2025-0129.
  - **Nuit du 20 au 21/11, ligne 34540 du journal** : une fusion. La règle E, allumée le 20/11 à 07:26 sur ton « Oui, allume E », rattache 7080 au dossier de la vente, puisque c'est le même acheteur. La fusion garde l'étiquette de la plus petite pièce, 7080, donc D2024-0456.
- **C'était annoncé avant l'allumage** : ton compte définitif du 20/11, cas n° 6, disait « étiquette changée sur MCD6CRNB ».
- **La preuve nommée de chaque pièce** (le protocole, passage 22) :
  - 7080 : compromis annulé, sans date, PASSERIEUX. Son prix de 244 000 est celui de ta ligne, et ses honoraires de 11 000 sont ta « Commission TTC » ;
  - 7081 : compromis du 24/06/2025, ta colonne « Compromis » ;
  - 7082 : offre acceptée du 23/04/2025, ta colonne « Offre Achat » ;
  - 7083 : vente du 09/10/2025, ta colonne « Vente Fixée ».
- **Pourquoi l'année recule** : D2024-0456 est le numéro **gardé** de 7080, et son année est celle de son mandat. Si le dossier naissait aujourd'hui, il serait D2025 (§ 2).

### Ta ligne 535 (A07EC3DH, bien 5262) : AUCUNE porte qui survive — elle ne tient que par une COPIE

- **Le journal :**
  - 12/11 : deux dossiers. D2023-0541 pour PAYSAC (1874 et 1877, ta ligne 3540 FLPUUSY3, annulée). Une autre étiquette pour GUERIN (1875, 1876 et 1878, ta ligne 535, vente réglée).
  - **13/11, ligne 34336** : une fusion. La nuit réunit les deux acheteurs dans D2023-0541. C'est donc à cause d'elle que C9 a recopié D2023-0541 sur ta ligne 535 le 16/11.
  - **16/11** : C5 crée la copie 1001563 de l'offre 1876. C'est une création du Sheet.
  - **18/11, lignes 34373 et 34374** : une scission, la première nuit avec les copies. 1875, 1876 et 1878 reçoivent D2024-0477, et la copie reçoit D2024-0505.
- **Le témoin, rejoué sur une copie du registre sans la copie 1001563** : la nuit remet 1875, 1876 et 1878 avec 1874. Les deux acheteurs se retrouvent dans un seul dossier, et rien d'autre ne bouge (3 pièces). **La séparation ne tient donc que par une copie.** Par ta règle C5 (« une création du Sheet ne décide jamais »), ce n'est pas une porte.
- **Sur le fond, la séparation est juste** : deux acheteurs différents. Pour GUERIN, ta ligne 535 :
  - 1875 : compromis du 25/01/2024, ta colonne « Compromis » ;
  - 1876 : offre acceptée du 12/01/2024, ta colonne « Offre Achat » ;
  - 1878 : vente du 10/04/2024, ta colonne « Vente Fixée ».

  PAYSAC, ta ligne 3540, est annulée le 24/01/2024.
- **La famille, mesurée sur tout le registre** (rejeu sans les 190 copies) : seules 5 pièces changent de dossier, sur 2 biens.
  - Le bien 5262 : tes lignes 535 et 3540.
  - Le bien 24733 : ta ligne 2388 (3S4ZWOFK, CIMINO, vente réglée) et ta ligne 4113 (9UO5NUN6, SOUDANI, annulée), séparées par la copie 1001580.
- **La règle que je te propose, par motif, mesurée et non appliquée : « C5 aux portes ».** Une séparation que seule une copie tient s'écrit en coupe, dans le fichier des détachements, comme les autres. Ses effets :
  - 4 lignes passent de la porte RIEN à COUPE_NEUVE ;
  - aucun verdict ne change ;
  - **l'arrivée ne change pas** : sur une copie en mémoire, avec les 4 coupes et les copies, 0 pièce ne change de dossier par rapport à l'arrivée du protocole. La coupe refait ce que la copie fait aujourd'hui ;
  - **et la séparation tient sans les copies** : retirées, les pièces des biens 5262 et 24733 ne bougent plus.

  ⚠ Le même test fait bouger 15 autres pièces, et ce n'est pas le même cas :
  - 14 sont des offres refusées. Leur coupe, déjà écrite par le protocole, **nomme une copie** dans son morceau : retirer la copie défait le morceau. Là, la porte existe, elle cite la copie ;
  - la 15e est la pièce 20673, qui n'a aucune ligne.

  Les copies ne se jettent pas, donc rien n'est à faire. Je le note pour le jour où une copie partirait.

### Les 17 lignes des 2 560 déplacées depuis le 16/11 : 17 causes nommées, 0 à expliquer

- **Règle E**, nuit du 21/11 : 9 lignes (23, 144, 1670, 1700, 4291, 4352, 4373, 4430, 4626).
- **Une copie C5**, 18/11 : 6 lignes (34, 156, 535, 1080, 4199, 4225). Dans 5 d'entre elles, seule la copie a bougé : leurs vraies pièces n'ont pas changé de dossier. Seule la 535 ne tient que par la copie.
- **Aucun déplacement** : 2 lignes (457, 1866). Le gel les relie à deux dossiers depuis la pose du 12/11, par une offre refusée seule dans le sien. Le protocole les traite par une coupe.

---

## 6. Ce qui n'est pas fait

- **Le rejeu du patch** : l'outil est écrit, la copie est extraite, mais le moteur manque. Le patch n'est pas collé.
- **La règle C5 aux portes** : mesurée, pas appliquée.
- **La mesure de la nuit** : demain matin, d'abord ce que la nuit a déplacé, puis le passage, les avis et la comparaison avec le passage 20.
- **Les 225 lignes en attente** : un reste à vider.
- **La vraie sauvegarde** : juste avant la première écriture.

## Ce qui attend ta décision

1. **Le Postgres portable** pour le rejeu du patch : `@embedded-postgres/windows-x64` 17.6, environ 101 Mo, depuis le registre npm. Je le télécharge ?
2. **La règle « C5 aux portes »** : sur les 2 biens et 4 lignes, une séparation que seule une copie tient s'écrit en coupe. Je l'applique ?
