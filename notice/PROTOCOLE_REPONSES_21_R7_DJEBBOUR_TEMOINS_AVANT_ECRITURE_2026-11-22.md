# Tes réponses au rapport ㉑ : appliquées, et ce que j'ai vérifié avant la première écriture (22/11/2026, après-midi)

> L3 · chantier classeur · ㉑ · 22/11 après-midi. **Rien n'est écrit** : ni dans ton classeur, ni chez Hektor, ni en
> base. Tout est mesuré sur l'image du 22/11 à 12:42, et le vrai chaînage est rejoué sur une copie.
> **La référence est maintenant le passage 20 : 4 573 lignes tranchées + 225 en attente = 4 798.**
> Le passage 21 a été refait après mes derniers ajouts de code : 0 verdict changé.

## 1. Tes trois réponses

### R7a : appliquée

- **Le passage.** 26 lignes passent. Aucun verdict déjà rendu ne bouge.
- **Ce que le rejeu exact a trouvé.** Le brouillon des coupes doit **emporter la pièce à part avec la ligne** quand
  cette ligne est coupée d'autre chose. Sinon la coupe la laisse dans le reste de l'ancien dossier, et sépare ce que
  R7a dit de ne pas séparer.
  - C'était le cas de 305KAY9W : sa 24124 restait derrière.
  - C'est corrigé, et le rejeu est vert.

### R7b : appliquée, avec ta règle

**Le défaut trouvé.** Mise de côté **seule**, comme je te l'avais décrite, la pièce aurait coupé son dossier dans
2 cas sur 13. L'autre pièce de ce dossier aurait reçu un numéro neuf, contre ta règle :
- **Bien 37243 :** le dossier D2021-0326 tient les deux pièces 17459 et 17460, toutes les deux mises de côté. 17460
  aurait reçu un numéro neuf.
- **Bien 54990 :** le dossier D2020-0527 tient 28294 et l'offre 28297 de THOURY. 28297 aurait reçu un numéro neuf.

**Ce que fait donc R7b.** La pièce est mise de côté **avec son dossier d'aujourd'hui**, c'est-à-dire tout ce
qu'aucun morceau ne prend. Le fichier des coupes fige ce dossier tel quel.

**Le résultat.** 13 pièces, en 12 dossiers, pour 12 lignes. **Les 12 gardent leur ancien numéro**, et le vrai chaînage
rejoué le confirme.

**Ce qui va dans le fichier des coupes : 8 lignes.**
- 4 des 12 dossiers sont des pièces **supprimées chez Hektor** : 3698, 19414, 28568 et 28959. Le chaînage les fige
  déjà dans leur dossier, qui ne les contient qu'elles. Une ligne dans le fichier serait refusée chaque nuit
  (« transaction introuvable »), donc je n'en écris pas.
- Les 8 autres, chacune avec son ancien numéro écrit sur sa ligne :
  - D2024-0449 ;
  - D2025-0412 ;
  - D2025-0415 ;
  - D2024-0464 ;
  - D2022-0500 ;
  - D2021-0326 ;
  - D2020-0527 ;
  - D2026-0297.

⚠ **Deux de ces dossiers figés sont ceux de tes lignes en attente :**
- 3QZ4DAD1, VACHER PEYRARD : D2021-0326, pièces 17459 et 17460 ;
- ARF57GC5, THOURY : D2020-0527, pièces 28294 et 28297.

Le fichier ne les change pas, il les fige. Une décision future sur ces deux lignes devra passer par cette ligne du
fichier.

### Le compte, rejoué sur toutes les lignes

- **Du passage 13 au passage 20 :** 38 verdicts changent. Ce sont tous des lignes du verrou E7 qui passent, et aucun
  verdict déjà rendu ne bouge.
- **Le verrou :** il retient maintenant 69 lignes au lieu de 107.
- **Les témoins :** 21 écarts avant, 21 après, sur les mêmes lignes. Aucun n'est neuf.

### DJEBBOUR : trois affaires, comme le protocole les tranchait déjà

- **Ta décision devient un témoin.** Elle s'appelle « ses décisions », et ses 3 accords sont faits sur 3 :
  - ZE9WZW22 : 14939 et 14943 ;
  - Q3KTCMVB : 14941 ;
  - DKTK22F2 : 14940, 14942 et 14944.
- **Elle remplace ta coupe des 132 pour ces trois lignes.** Le témoin des 132 passe de 4 écarts à 2. Les deux qui
  restent sont déjà connus : O6R10ZQA (PAOLONE) et T0WL4QE7.
- **Le fichier réel des coupes** (`phase2/sync/detachements_manuels.csv`) porte encore DJEBBOUR en un seul morceau.
  Je n'y touche pas : il sera corrigé quand on posera le fichier du protocole, et c'est toi qui le joueras.

## 2. Avant la première écriture

### Le témoin « lien non sûr » : semé, et il crie

**Le problème.** Il n'existe plus une seule ligne réelle avec un lien « à valider » depuis le patch de confiance.

**La graine.** Je l'ai donc semé sur Y8O4NJSY, une ligne nominale qui s'écrit sans la graine. Sa confiance est
forcée à « à valider », seulement dans le registre simulé.

**Le résultat.** L'écrivain la saute et la nomme : « LIEN_NON_SUR, confiance ['à valider'] ». L'épreuve complète
donne **34 verdicts, 0 rouge** (elle en avait 1). Elle n'a fait qu'un seul GET, aucun POST, et tout s'est passé en
mémoire.

### Les 2 560 numéros de `app_classeur_avis`

⚠ **D'abord, d'où ils viennent, lu dans le code.** Ces numéros n'ont pas été écrits de ta main.
- **Qui les a posés :** le patch C9 du 16/11 à 16:32 (`supabase/patch_c9_avis_etiquette_2026-11-16.sql`), à ta
  demande « Table avec étiquettes ».
- **D'où il les a calculés :** du gel joint au registre de ce jour-là, et seulement quand une ligne désignait UN seul
  dossier.
- **« origine = classeur » :** c'est l'origine des trois colonnes d'avis (AH, AI, AJ), pas celle du numéro.
- **Ce que l'épreuve prouve donc :** l'accord avec le gel et les dossiers du 16/11. Le protocole ne l'a pas
  fabriquée, et elle est plus vieille que lui. Mais elle ne prouve pas l'accord avec toi.
- **Ton classeur, vérifié :** aucune de ses cases ne porte un numéro D20xx-xxxx.

**Ta mesure, refaite à l'unité :** 2 543 lignes dans le même dossier, 10 dans un autre dossier, 7 dans plusieurs.

**Le protocole retrouve 2 452 lignes sur 2 560 au numéro exact :**
- 2 448 des 2 543 qui collaient ;
- 4 des 7 qui avaient plusieurs dossiers : il leur rend le numéro du 16/11. Ce sont 1cc703d9 (D2025-0365), 21f6e095
  (D2025-0225), 2SCBZXMH (D2021-0203) et NUBQNV1K (D2025-0019).

⛔ **Les 63 qui collaient et que le protocole contredit.** Je les ai regardées en premier, et elles sont en tête du
fichier.
- **Leurs pièces :** dans 57 cas sur 63, le protocole leur donne **exactement les vraies pièces que le gel leur
  donne**. Il en garde moins dans 4 cas, et davantage dans 2.
- **D'où vient le désaccord :** du **numéro**, pas des pièces. Leur dossier est coupé, 39 fois par tes 132 coupes
  validées du 20/11, 24 fois par une coupe neuve.
- **Pourquoi la ligne perd son numéro :** la pose de nuit laisse le numéro au morceau de la plus petite transaction.
  - **59 cas :** le dossier porte aussi les pièces d'une autre de tes lignes, et c'est elle qui garde le numéro.
    Dans 57 de ces cas, l'autre ligne n'a pas de ligne d'avis : c'est pour ça que le numéro du 16/11 « collait ».
  - **4 cas :** le numéro reste à une pièce plus ancienne qu'aucune ligne tranchée ne tient, et la vente reçoit un
    numéro neuf. Exemple : AOPBUAOJ, D2022-0001. Le compromis 125 du 03/01/2022 garde le numéro, et l'offre du
    12/12/2022 et la vente du 02/05/2023 en reçoivent un neuf.
- **Exemples :**
  - 1TZEGF2D (ligne 126, D2024-0235) : le numéro va à HTFNZ9Z2 ;
  - 29YBUBYA (ligne 1521, D2021-0559) : il va à 6NOJ686I ;
  - 305KAY9W (ligne 845, D2023-0029) : il va à H75WKJ6X.

**Les 17 qui ne collent pas aujourd'hui.**

Les 10 qui ont un autre dossier :
- **2 :** la nuit a réuni leur dossier depuis le 16/11, et le protocole garde celui d'aujourd'hui.
  - A07EC3DH : D2023-0541 est devenu D2024-0477.
  - MCD6CRNB : D2025-0129 est devenu D2024-0456.
- **5 :** une coupe neuve leur donne un numéro neuf.
- **3 :** elles attendent au verrou E7.

Les 7 qui ont plusieurs dossiers :
- **4 :** le protocole leur rend le numéro exact du 16/11.
- **3 :** elles reçoivent un numéro neuf.

**Le reste.** 32 des 2 543 qui collaient sont en attente.

Le fichier : `notice/PROTOCOLE_TEMOIN_AVIS_LES_2560_NUMEROS_PASSAGE_20_2026-11-22.csv`.

### Les numéros de dossier

Chaque fichier donne maintenant **le numéro et l'étiquette**, côte à côte : le verdict de chaque ligne, la porte de
chaque ligne et les 2 560.

Un dossier neuf est marqué « NEUF ». Son numéro, c'est la nuit qui le donne : D, l'année de sa plus vieille
transaction, puis le rang suivant.

### Les 6 lignes que la nuit ne peut pas réaliser

- **Elles attendent, et je ne les force pas.**
- **5 sont parmi tes 15 doublons :** dfb32f2b, 3250892d, 87eb399e, 0bc98552 et 6095c819.
  - Pour chacune, **Hektor a déjà supprimé la moitié en double** : un compromis du même jour, et aussi une offre pour
    0bc98552 et 6095c819.
  - **Il ne reste donc rien à trancher chez Hektor pour elles.**
  - La moitié supprimée vit chez nous, seule dans son dossier, sous son propre numéro : D2025-0371, D2025-0333,
    D2026-0086, D2026-0048 et D2026-0052.
- **La 6e, 6684bcf1, n'est pas un doublon.** Elle tient un compromis annulé sans date, supprimé chez Hektor, et une
  offre refusée du 16/09/2025.
- **Les doublons qui restent parmi les lignes tranchées : 11.** Ce sont les 10 autres de tes 15, plus HOPCBVKM,
  qu'R7 vient de faire passer.

### Le coût de défaire, recompté sur le passage 20

- **Les dossiers** reviennent à l'identique.
- **216 étiquettes ne reviennent pas**, sur 215 dossiers (214 au passage 13).

La sauvegarde datée se prendra **avant** l'écriture. Je vérifierai qu'elle est **lisible** : relue, et son empreinte
comparée à celle que donne la base. ⚠ L'outil n'est pas encore fabriqué : c'est ma prochaine pièce avant toute
écriture.

## 3. G2 : ses 480 pièces, lues

- **Où elles sont :** dans **286 biens**. **281 n'ont aucune ligne dans ton classeur.** Les 5 autres n'ont que des
  lignes en attente.
- **Leurs années :** 462 des 480 sont d'avant 2018.
- **Ce que G2 fait :** dans chaque bien, il sort d'un dossier ce qui appartient à un autre acheteur. Ce sont 287
  morceaux :
  - 155 offres refusées seules ;
  - 69 tentatives annulées (un compromis annulé et une offre refusée) ;
  - 53 ventes entières (compromis, offre acceptée et vente), séparées d'une tentative plus ancienne ;
  - 10 autres combinaisons de pièces mortes.
- **Les numéros :** les 480 recevraient un **numéro neuf dans l'app**.
- ⛔ **Sur 281 biens, aucun témoin de ta main :** la coupe ne reposerait que sur la logique de G2 (« l'offre acceptée
  datée bat le nom »).
- **Les 5 biens à lignes en attente :** 9868, 9902, 9961, 10043 et 15672. G2 y sépare la vente de la tentative
  d'avant. Je les lirai dans le reste à vider.
- **G2 reste en attente**, et je ne te la propose pas.

Le fichier : `notice/PROTOCOLE_G2_LES_480_PIECES_HORS_DES_LIGNES_TRANCHEES_2026-11-22.csv`.

## 4. Les portes et le mouvement du passage 20

**Le témoin.** Le rejeu de la nuit redonne l'image à la pièce près : 0 pièce sur 31 368 dans un autre dossier.

**La porte de chaque ligne tranchée, sans G2 :**
- rien à corriger : 4 010 ;
- mise de côté (R7b) : 10 ;
- rattachement : 86 ;
- coupe déjà écrite dans tes 132 : 266 ;
- coupe neuve : 201.

**Si on comptait G2 d'abord**, il mettrait justes 206 de ces lignes. Mais il déplace les 480 pièces ci-dessus.

**Hektor.** Aucune décision n'y est nécessaire pour une étiquette. 11 lignes tiennent un doublon.

**L'état d'arrivée, rejoué :**
- les 4 573 lignes tranchées sont justes ;
- les 4 573 ont la même étiquette que le passage ;
- les 12 dossiers mis de côté sont seuls et gardent leur numéro ;
- rien ne bouge hors des biens des lignes tranchées ;
- le brouillon compte 559 morceaux, et aucun n'est refusé.

**Le mouvement :**
- **Le gel :** 250 liens se délient et 74 se relient, dont 72 sur de vraies pièces, sur 299 lignes. Les 311 liens des
  lignes en attente ne bougent pas.
- **Les dossiers :** on passe de 11 551 à 11 612. 544 dossiers se recoupent ou se réunissent, 605 sont nouveaux, et
  1 360 pièces changent de compagnie.
- **Les étiquettes, par ligne :** 4 243 lignes gardent la leur et 247 en reçoivent une neuve. 64 reçoivent une
  étiquette existante alors qu'elles n'en avaient pas une seule, 16 une autre étiquette existante, et 3 une étiquette
  alors qu'elles n'en avaient aucune.
- **Les étiquettes qui changent de ligne :** 46.
- **Les lignes en attente :** 4 voient leur dossier bouger.

## 5. Ce qui n'est pas fait, ou pas vérifié

- **La sauvegarde datée et sa relecture :** pas encore fabriquées.
- **La nuit n'est pas encore passée :** demain matin, je ferai l'image, le mouvement, le passage, puis comparer 20
  avec le nouveau. Je donnerai le nombre d'orphelines.
- **Le reste à vider, 225 lignes :**
  - verrou E7 : 69 ;
  - pièces à part : 29 ;
  - aucune preuve : 28 ;
  - plusieurs biens : 23 ;
  - copie seule : 23 ;
  - bien sans pièce : 23 ;
  - sans bien : 11 ;
  - deux lignes : 10 ;
  - figées : 6 ;
  - à ta décision : 3.
- **Le run de jour :** je n'en ai pas eu besoin.

## 6. Ce que j'attends de toi

1. **Les 63 numéros :** quand une coupe sépare deux de tes lignes, la pose de nuit laisse le numéro au morceau de la
   plus petite transaction, et l'autre ligne en reçoit un neuf. Est-ce que cette règle te va ?
2. **R7b :** elle met la pièce de côté avec son dossier d'aujourd'hui, pour que personne ne perde son numéro. Elle
   fige ainsi les dossiers de deux de tes lignes en attente, 3QZ4DAD1 et ARF57GC5, sans les changer. Est-ce que tu es
   d'accord ?
