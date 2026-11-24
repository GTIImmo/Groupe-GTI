# Ses quatre réponses du 24/11 : ce que j'ai posé, mesuré à blanc, et ce qui t'attend

L3 · chantier classeur · ㉔ · 24/11 — réponse à `C:\Hektor\MOT_DU_24_11_MES_QUATRE_REPONSES.md`.

⛔ **Rien n'est écrit.** Ni base, ni Sheet, ni Hektor ; rien n'est tiré ni poussé. Le seul geste est dans le protocole de mesure (v21), et le commit est local. La mesure à blanc du ② s'est faite sur une copie du socle et sur une copie du module de nuit, hors du dépôt. `affaire_ledger.py` n'est pas touché, et l'interrupteur `APP_CHAINAGE_DETACHEMENTS` reste éteint.

**Le run de la nuit** était fini quand j'ai commencé (tâche « GTI Quotidien » prête, dernier résultat 0, aucun python en cours). J'ai gardé l'image du 23/11 08:02 : tu as écrit que le sol n'avait pas bougé.

Les outils, tous en lecture seule, sont dans `phase2/checks/` :
- `protocole_retrait_exclusions_e_a_blanc_2026-11-24.py` (le ②) ;
- `protocole_a1_a2_a3_le_remede_a_blanc_2026-11-24.py` (le ③) ;
- `protocole_commission_agence_ce_qu_elle_porte_2026-11-24.py` (le ④) ;
- `protocole_controle_sheet_contre_registre_2026-11-24.py`, refait (le § 7).

---

## ① 19814 va à 4G2UHO35 : posé, passage 79

**Le geste.** 19814 sort du suspens et entre dans `PIECE_DONNEE_PAR_DECISION`, vers 4G2UHO35, avec ta preuve de date : acte prévu le 17/05/2020, 4G2UHO35 annulée le 20/05/2020. Le témoin de tes décisions suit ton mot : 4G2UHO35 = 19814, 19819, 19820 ; R7NU9NPM = 19815, 19818. Le mécanisme du suspens reste dans le code, vide, pour un prochain doute.

**Passage 79 contre 78 (même image) :**
- 2 verdicts changent, ni plus ni moins : R7NU9NPM et 4G2UHO35, qui passent de VERROU_PIECE_PLUS_PETITE à TRANCHEE.
- 0 verdict déjà rendu ne bouge. Les preuves des autres lignes ne changent pas.
- 4 725 lignes tranchées et 73 en attente, dont 58 rien à étiqueter. **Le reste à vider passe de 17 à 15.**
- Les étiquettes :
  - 4G2UHO35 prend **D2020-0091**, le numéro de 19814, sa plus petite pièce (la pose de nuit, que je n'ai pas touchée).
  - R7NU9NPM reçoit un **numéro neuf**. 19815 est sa plus petite pièce, mais le numéro de sa chaîne part avec 19814.
  - Le dossier D2020-0043, celui de l'offre 19818, n'est plus l'étiquette d'aucune ligne.
  - MYILWKZQ, déjà rendue, ne change pas : elle avait déjà un numéro neuf au passage 78.
- Les témoins : tes décisions 45 accords, 0 écart, 2 en attente (P252U1JH, d2108609). Les autres témoins sont identiques au 78.
- **Le rejeu exact du passage 79 est vert :**
  - 0 « introuvable » (451 détachements décidés à la main, 179 déjà obtenus) ;
  - 4 725 lignes justes sur 4 725, et l'étiquette exacte sur 4 725 ;
  - R7b : 21 dossiers sur 21 ;
  - 0 pièce ne bouge hors des biens, 0 ligne en attente dont le dossier bouge.

**Ta vérification : 19815, sans date, n'est pas invisible à la nuit.** Deux raisons, chacune mesurée :
- elle n'est pas dans `EXCLUES_DE_LA_REGLE_E` (seules 26613, 21520, 4126, 4496 et 4720 y sont) ;
- elle n'est pas seule dans sa chaîne : elle est dans la chaîne 19814, avec 19814, 19816, 19817 et 19821.

Le témoin positif : le rejeu exact trouve son morceau (19815 avec 19818) sans aucun « introuvable », et R7NU9NPM est juste à l'arrivée. **R7NU9NPM ne rejoint donc pas P252U1JH et d2108609.**

---

## ② Retirer 4126 et 21520 des exclusions de E : mesuré à blanc. ⛔ Ce n'est pas 2, je m'arrête

La mesure a trois volets, contre le passage 79 : le protocole, la vague (l'outil de coupe allumé, avec le brouillon) et **la nuit telle qu'elle tourne aujourd'hui**, interrupteur des coupes éteint.

- **Le protocole : exactement 2 lignes changent.**
  - P252U1JH passe à TRANCHEE avec 4126 et 4128, et prend D2020-0592.
  - d2108609 passe à TRANCHEE avec 21520 et la copie 1001495, et prend D2025-0427.
  - Les témoins : 2 écarts V3 nouveaux, et ce sont ces deux lignes (ta décision du 21/11, renversée). Tes décisions passent à 47 accords, 0 écart, 0 en attente.
- **La vague : rien d'autre ne bouge.** 0 autre ligne, 4 727 lignes justes et étiquettes exactes sur 4 727, R7b 21 sur 21, 0 hors, 0 ligne en attente.
  - ⚠ Mais le brouillon gagne 4 morceaux au lieu de 2.
  - FOZ6HZLK et 1c7b38f9, deux lignes **déjà rendues**, passent de « rien à faire » à « coupe neuve ».
- ⛔ **La nuit telle qu'elle tourne (coupes éteintes, comme l'exige A2) : 4 lignes bougent.**
  - Retirer l'exclusion rend 4126 et 21520 visibles à la règle E. Puis la règle D les réunit au dossier du même acheteur, ce que l'exclusion empêchait justement.
  - **FOZ6HZLK** (4125, 4127, 4129) reçoit 4126. Elle garde D2022-0233, et D2020-0592 disparaît.
  - ⛔ **1c7b38f9** (21521, 21522, 21523) reçoit 21520 et **PERD D2025-0263**. Elle prend D2025-0427, parce que 21520 est la plus petite pièce : un numéro déjà rendu qui change.
  - Les deux pièces de P252U1JH et de d2108609 se fondent dans ces dossiers.

**Les deux lignes que tu n'as pas demandées : FOZ6HZLK et 1c7b38f9.**

Ce que ça veut dire : le retrait ne peut se poser que **dans la même nuit que la vague**, l'outil de coupe allumé avec ces 4 morceaux, jamais avant. Sinon 1c7b38f9 perd son numéro dès la nuit suivante (R15 : un témoin parfait ne rachète pas un effet de bord sur du déjà-rendu). Et l'interrupteur reste éteint tant qu'A2 n'est pas corrigé : **② attend donc A2.**

Le détail est dans `C:\Hektor\chantier_classeur_q6_cache\protocole_a_blanc_retrait_e\retrait_e_a_blanc.json`.

---

## ③ A1, A2 et le reflet des notes : le remède mesuré à blanc, son contrôle à zéro (passage 79)

**Le même remède trois fois** (ton ⑥) : replacer par ce qui ne bouge pas (la ligne, la transaction), après la nuit, en gardant l'ancien numéro.

### A1 : le reflet des avis
- 2 588 lignes. 10 décollés aujourd'hui, et **81 après la nuit sans remède**.
- Le remède (recalcul depuis `id_unique`) change 107 reflets.
- ⭐ **Contrôle après le remède : 0 décollé.**

### A2 : les honoraires

**Ta règle de lecture, vérifiée par mes propres comptes.** La population : les lignes tranchées dont la chaîne porte des parts du Sheet du 13/11. Les parts sont lues telles qu'elles sont, sans filtre de signature ; un filtre aurait comparé le Sheet à lui-même.
- **Un nom à 100 % au Sheet → une seule personne au registre : 3 959 fois sur 3 971.**
  - Les 12 autres sont nommées : 2DUPM26R, 3936NZOO, 739a0db1, 7HDK9XOG, 8GIIDS5T, F5GA770R, JRE23R1G, JYOLFY1A, PCDZXTIY, T58W1AXB, WW88Z2AC, Z1EU0WC6.
- **Le témoin inverse, deux noms au Sheet → deux personnes : 624 fois sur 635.**
  - 10 n'ont qu'une seule personne : 17S58J78, 25QYWG2U, 2c2566d7, G41FTEZ8, GYGF5F1X, MSL64YBY, QV5AYD2K, TND2I31B, TR42PT5H, Z624CX4D.
  - XHITO8HE en a trois.
- On y retrouve des lignes du verrou, dont la chaîne porte la répartition de la ligne de la vente, et la paire croisée TR42PT5H / 739a0db1. Mais je n'ai pas fait la cause de chacune.
- Nos deux mesures se rejoignent : le même nom dans 99,7 % (toi : 2 726 sur 2 727, sur ta population).
- ⛔ **Le remède ne compte jamais « deux parts » comme « partagée »** : il recopie les parts telles qu'elles sont (le côté, la personne, la part), et c'est le nom qui dit le partage.

**Le remède, chaîne par chaîne (8 837 chaînes à répartition) :**
- 3 712 restent avec leur ligne. 4 888 ne sont reconnues par aucune ligne tranchée et ne bougent pas : on n'y touche pas.
- 213 sont recopiées sur la chaîne de leur ligne après la nuit. 149 sont gardées pour une ligne et recopiées pour l'autre.
- 61 sont mises de côté avec leur ancien numéro : aucune de leurs lignes ne garde la chaîne.
- 13 étaient déjà sur la cible, avec les mêmes parts (un doublon pur) : pas de recopie.
- **Les orphelines que la nuit fabriquerait :** 9 sont ramenées par le chemin de D8, puis mises de côté ; 5 sont des doublons purs, mis de côté.
- ⭐ **Le compte des deux, ta règle 6 : 452 parts recopiées** (vivantes, sur 222 chaînes cibles), **151 mises de côté avec leur ancien numéro** (75 chaînes).

**Le contrôle après le remède :**
- **4 087 lignes justes**, 2 conflits nommés, **0 faux non nommé**.
- Le témoin : sans le remède, 212 de ces lignes seraient fausses à l'arrivée.
- La conservation boucle : 17 907 parts aujourd'hui ; 18 208 vivantes après le remède, dont 452 recopiées, et 151 mises de côté. 18 208 − 452 + 151 = 17 907.

**Les 2 conflits, à toi : rien n'est recopié.**
- **U0GQ3KTO** : sa chaîne d'arrivée 4385 porte déjà une autre répartition (une seule personne des deux côtés), qu'aucune ligne tranchée ne reconnaît. C'est la paire croisée U0GQ3KTO / 8RWTD0YX du contrôle.
- **NRZVKH85** : sa chaîne d'arrivée 22979 porte une seule part (l'entrée à 50 %), qu'aucune ligne ne reconnaît.

**⭐ Les 26 orphelines du moniteur (13 chaînes) se vident par la vague, sans geste.** La vague recrée chacune des 13 chaînes, et la ligne qui l'aura à l'arrivée y porte exactement ces parts :
- 3670 : 86ad8c0f ; 11709 : SC58GWXX ; 14034 : 205f62be ; 14052 : 4fc6b33a ;
- 14913 : AVXWIZTU ; 19070 : 8SZDU4F5 ; 19576 : YQG8CN5T ; 19737 : 3WBNBNY4 ;
- 20089 : ZW7MKTWH ; 24011 : ccbbf3c8 ; 27135 : JRE23R1G ; 28179 : 5f47de79 ; 28547 : beeaf847.

⚠ Ce sont aussi les décollés d'A1 d'aujourd'hui (même cause) : c'est bien ton motif, déjà en place.

### A3 : le reflet des notes
- La note est accrochée à la transaction (`app_affaire_id`), qui ne bouge jamais. `app_chaine_id` n'est qu'un reflet.
- **Aujourd'hui, 161 reflets sur 4 524 sont faux** : 161 contre l'image, et 161 contre le registre local de ce matin.
  - ⚠ Toi, tu en comptes 155. Je n'explique pas les 6 d'écart : nos mesures ne sont pas faites sur la même base ni au même moment. Ma liste est dans le fichier.
- **269 seraient faux après la nuit sans remède.**
- ⭐ **Recalculé depuis la transaction : 0.** Aucune note n'est déplacée, seul son reflet change (269).
- ⚠ Je n'ai pas mesuré le reflet du dossier (`app_dossier_id`).

**Les fichiers :**
- `notice/PROTOCOLE_A2_PARTS_RECOPIEES_A_BLANC_PASSAGE_79_2026-11-24.csv` (452) ;
- `notice/PROTOCOLE_A2_PARTS_MISES_DE_COTE_A_BLANC_PASSAGE_79_2026-11-24.csv` (151) ;
- `notice/PROTOCOLE_A3_REFLETS_DES_NOTES_A_RECALCULER_A_BLANC_PASSAGE_79_2026-11-24.csv` (269) ;
- `notice/PROTOCOLE_A1_REFLETS_A_RECALCULER_A_BLANC_PASSAGE_79_2026-11-24.csv` (107).

⚠ **Rien de ce remède n'est codé** : c'est une mesure. L'écrire touche au registre et à la nuit.

---

## ④ La commission : mon analyse, avec ses témoins

⚠ **Sur l'indépendance, je dois te le dire d'abord.** Ce matin, avant de mesurer, j'ai lu la note de mémoire qu'une autre session a écrite à 06:33 sur ce sujet. Elle nomme la bascule de 2025 et la fausse piste de la colonne Charge. Sur ces deux points, mon analyse n'est donc pas aveugle. Ce qui suit est mesuré par moi, sur d'autres sources, et je dis où ça converge.

**La source, avant toute statistique.**
- `commission_agence` est le champ `commissionAgence` de la vente, tel que l'API de Hektor le rend. Il est recopié tel quel : `normalize_source.upsert_ventes` → `hektor_vente` → `app_affaire_ledger` (« `commission_agence AS commission` »).
- C'est Hektor qui le calcule, et rien ne l'écrit chez nous. Le lot C2 du 17/11 a écrit `honoraires_entree_app`, pas ce champ.
- Le miroir compte 9 285 ventes. `honoraires` = `honorairesEntree` + `honorairesSortie` sur 9 285 sur 9 285 ; `commissionAgence` est rempli sur 8 078.
- Deux sources indépendantes servent ici : **le formulaire de la vente lu dans la console de Hektor** (`app_affaire_console.intervenants_json`, 7 968 ventes) et **le Sheet**.

**① La distribution complète** (la part du HT que porte le champ : `commissionAgence` × 1,2 / honoraires TTC), sur toutes les ventes, par époque :
- avant 2015 (3 875 ventes) : **le quart** du HT dans 98 % ;
- 2015-2016 (870) : **vide** dans 77 %, la moitié dans 21 % ;
- 2017-2024 (3 890) : **le tout** dans 77 %, la moitié 12 %, le quart 5 %, vide 5 %, les trois quarts 18 cas ;
- 2025 (353) : **la moitié** 42 %, le tout 38 %, vide 15 % ;
- 2026 (297) : **vide** dans 86 %.

**Mois par mois, la bascule est datée.**
- Jusqu'en avril 2025, le tout domine (74 à 89 % par mois).
- Mai 2025 : 53 % le tout, 35 % la moitié. Juin : 59 % la moitié. Juillet : 61 %.
- À partir de février et mars 2026, le champ n'est plus rempli : vide à 68 % en février, 86 % en mars, 95 à 100 % de mai à novembre.

**Le formulaire de Hektor contredit son propre champ.**
- Dans 7 957 ventes sur 7 968, le formulaire porte la même personne aux deux côtés, à 100 %.
- Avant 2015, `commissionAgence` y vaut le quart de la somme des parts dans 99 %. En 2015-2016, un seul côté dans 93 %. En 2017-2024, la somme dans 82 %. En 2025, un seul côté dans 49 % ; en 2026, dans 71 %.
- Hektor ne calcule donc pas ce champ depuis le formulaire que nous lisons.
- ⚠ Et ce formulaire ne porte pas le partage : 11 ventes seulement y ont deux personnes, contre 16 % au Sheet.

**② Le Sheet : 3 704 lignes tranchées tiennent une vente et une Commission TTC.**
- Le témoin de base : « Commission TTC » = les honoraires de Hektor sur 3 675 sur 3 704.

**Le signe trouvé, en 2017-2024 : le nombre de personnes du Sheet, par le nom.**
- **Positif.** Deux noms → **jamais le tout** (3 sur 485). La part est celle d'une des deux personnes dans 479 sur 485 : le négociateur 1 dans 306, l'autre dans 173.
- **Inverse, sur le groupe sain.** Un seul nom → **le tout dans 2 567 sur 2 594 (99 %)**, la moitié 3 fois.
- **③ Les époques de cette colonne.** Le Sheet écrit le partage de la même façon chaque année : deux noms dans 16 % (2017-2024), 9 % (2025), 7 % (2026). Ce n'est pas une colonne récente.

**En 2025-2026, ce signe ne suffit plus.** Les affaires entières au Sheet (un seul nom) portent la moitié : 112 fois contre 132 au tout en 2025, 24 contre 3 en 2026.

J'ai cherché ce qui distingue la moitié du tout dans ce groupe. Chaque signe est mesuré des deux côtés (2025 : moitié / tout) :
- Charge remplie : 99 % / 92 %. La colonne est récente et remplie des deux côtés : **elle n'explique rien** (sur ce point, l'autre note et moi nous rejoignons).
- Charge = acquéreur : 8 % / 4,5 %.
- Mandat simple : 29 % / 36 %.
- Le formulaire de Hektor : une seule personne dans les deux groupes, et `ca_montant` vide dans les deux.
- Les agences et les négociateurs : autour de la moitié partout, sans aucun qui concentre.

**Seule la date distingue.** La date de la vente, mois par mois, comme ci-dessus.

**Ce que porte `commission_agence` (ma conclusion, que tu compareras à la tienne) :**
- **De 2017 à 2024, la part du HT d'une seule personne de l'affaire.** C'est le tout quand un seul nom porte l'affaire, et la part d'un des négociateurs nommés quand deux noms se la partagent.
- Ce n'est donc pas la commission de l'affaire. Il ne tombe sur « Commission TTC » ni sur une affaire partagée, ni avant 2017, ni après le printemps 2025.
- Avant 2015, le quart du HT, sur des affaires que le formulaire de Hektor dit entières : c'est un effet d'époque, et je n'en ai pas la cause.
- Depuis mai-juin 2025, la moitié du HT sur une affaire entière, c'est-à-dire un seul côté du formulaire. Avec ta certitude (aucun changement d'honoraires), c'est une façon de remplir le champ qui change à une date chez Hektor. Ce n'est pas une règle de paie, et je n'en ai pas la cause.
- Depuis février-mars 2026, Hektor ne le remplit plus.
- ⚠ Non mesuré : la règle qui choisit laquelle des deux personnes (le négociateur 1 dans 63 %).

**Mes 453 « moitié » du contrôle, ligne par ligne :**
- **313 sont expliquées par le partage au nom** : la part du négociateur 1 dans 312, celle de l'autre dans 1. Ce sont 295 en 2018-2024, 16 en 2025, 2 en 2026.
- **139 ne sont pas expliquées par le Sheet** : 112 en 2025 et 24 en 2026 (un seul nom), et 3 en 2019, 2021 et 2023.
- 1 ligne tient plusieurs ventes : elle est hors de l'analyse.

**Ce qui reste inexpliqué sur toute la population : 162 lignes** (16 en 2017-2024, 117 en 2025, 29 en 2026). Elles sont nommées en tête de `notice/PROTOCOLE_COMMISSION_AGENCE_CE_QU_ELLE_PORTE_PASSAGE_79_2026-11-24.csv`, et chaque ligne du fichier porte son explication.

⛔ **Aucune écriture, aucune correction, aucun recalcul** : je nomme, je ne touche pas.

---

## ⑤ Le § 7 refait (passage 79)

**La colonne Charge, lue des deux côtés avant de compter.**
- Le Sheet la porte sur 980 lignes sur 4 798, dont 953 tranchées.
- Côté registre, je lisais `charge_commission_app`, sur la transaction : **7 pièces sur 31 368**. Mon « 953 jamais rapatriée » d'hier n'était donc pas un désaccord, mais **un trou de lecture**.
- La charge vit sur le mandat : le carnet `app_mandat_champ_app` porte 23 491 mandats. Ce sont 816 vendeur et 37 acquéreur venus du classeur (les 853 du lot C1 du 14/11), 22 542 vendeur et 95 acquéreur venus de Hektor, et 1 de l'app.
- Elle est reflétée sur `app_mandat_register_current` : 23 359 vendeur, 132 acquéreur, 1 676 vides.
- Le champ a déjà été jugé le 03/11 (`JUGE_CHARGE_CLASSEUR_HEKTOR_2026-11-03.md`, classeur ↔ Hektor 368 sur 380) : je ne refais pas ce jugement.
- La clé : le bien et le mandat **des pièces de la ligne**, jamais le mandat du Sheet.

**Le résultat sur la Charge : 953 comparées, 914 d'accord** (908 par le carnet du classeur, 6 par Hektor), **39 écarts nommés.**
- 20 lignes : le carnet ne porte aucune charge pour leur mandat.
- 16 lignes : leurs pièces ne portent aucun numéro de mandat.
- 3 vrais désaccords avec Hektor : 2 où le classeur dit acquéreur et Hektor vendeur, 1 à l'inverse.
- ⚠ La première passe en annonçait 37 de plus : « Acquéreur » contre « acquereur », un accent. C'était mon erreur, corrigée.

**Les notes : mon contrôle les joint par la transaction.** La note est lue sur sa pièce (`app_affaire_id`), jamais par `app_chaine_id`. **Ton 56 tient : 56 écritures sur 38 lignes, le même ensemble aux passages 78 et 79.** Ce sont 6 factures, 5 règlements, 8 annulations, 12 textes F et 25 textes G.

**Le total des écarts passe de 3 963 à 3 051**, surtout par la Charge. La commission reste comparée comme hier (989 écarts), et l'analyse du ④ explique ses 453 « moitié ».

Les fichiers :
- `notice/PROTOCOLE_CONTROLE_SHEET_CONTRE_REGISTRE_PASSAGE_79_2026-11-24.csv`, avec son témoin inverse ;
- `notice/PROTOCOLE_PASSAGE_79_LA_PORTE_DE_CHAQUE_LIGNE_2026-11-22.csv`.

Le nom du compte admin n'est dans aucun fichier. Je l'ai vérifié, et le témoin positif est le Sheet de l'image, qui le porte 4 fois.

---

## Ce qui reste des 17 : 15

La liste, par motif :
- 4 ne tiennent que des copies : HUY49KEC, C0HXVVCW, SHN6RKDI, BR8ZTN5F.
- 3 ont toutes leurs pièces à part : XBR8QD6L, PPIM4947, 3QZ4DAD1.
- 2 tombent dans le même dossier : PEE1XTR8, 9B7U8221 (bien 50307).
- 1 n'a aucune pièce prouvée : 9Q0FHAKK.
- 3 tiennent une pièce sans date invisible à la nuit : 3THZJOOG, P252U1JH, d2108609. Si le ② se fait avec la vague, P252U1JH et d2108609 sortent ; 3THZJOOG reste : son morceau tient 4720 (bien 10129), qui reste exclue de E par ta décision du 20/11.
- 1 tient une pièce supprimée chez Hektor : 6684bcf1.
- 1 nomme plusieurs biens : M2G1Z1K8.

**Avec le ②, il en resterait 13.**

---

## Ce qui attend ta décision

1. **② : poser le retrait des deux exclusions dans la même nuit que la vague, avec ses 4 morceaux, et pas avant.** Sinon, dès la nuit suivante, FOZ6HZLK reçoit 4126 et 1c7b38f9 reçoit 21520 en perdant D2025-0263. Je n'ai rien posé.
2. **A2 : les 2 conflits nommés**, U0GQ3KTO et NRZVKH85. Pour chacune, que fait-on des parts déjà sur sa chaîne d'arrivée ?
3. **La commission : ta mesure**, pour voir si nos deux analyses se rejoignent.
4. **A3 : les 6 d'écart** entre ton 155 et mon 161. Ta liste me permettrait de les nommer.
5. **Écrire le remède A1-A2-A3** (code du registre et de la nuit) : je ne l'écris qu'à ton « vas-y ».
