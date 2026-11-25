# La nuit de la vague : la procédure, et qui pose A2 — 24/11 (son 9e mot)

> Son mot : « ⛔ ET TRANCHE-MOI ÇA DANS LA PROCÉDURE, C'EST LE SEUL VRAI TROU QUI RESTE : QUI POSE A2 JUSTE APRÈS LE CHAÎNAGE ?
> Si c'est toi à la main à 4 h du matin, ce n'est pas une procédure, c'est un pari. A — A2 devient UNE ÉTAPE DU RUN ; B — la
> vague se joue à une heure où quelqu'un est réveillé ; C — autre chose, et tu me l'expliques. »

**Ce document ne lance rien.** Il décrit la nuit de la vague telle que je la propose. Chaque pièce attend ton accord.

---

## Ma réponse : C — « la vague du soir », une seule commande, un point de non-retour contrôlé, et le run de 05:00 pour témoin

**En une phrase.** La vague ne se joue pas dans le run de 05:00. Elle se joue **le soir**, à une heure où nous sommes
réveillés tous les deux. Une **seule commande écrite** enchaîne les étapes et **s'arrête d'elle-même** à la première garde
qui ne passe pas. A2 est posé **automatiquement** par cette commande, juste après le chaînage, avec ses gardes. Le run de
05:00 rejoue ensuite tout à l'identique et devient le **témoin**. Au matin, on a le verdict de la vague, d'A2 et du verrou.

**Pourquoi pas A (A2, étape du run de 05:00).**
- **A2 dépend du résultat du chaînage.** S'il trouve un écart à 05:30, sa garde refuse, et personne n'est là pour trancher. La
  matinée s'ouvre avec la vague posée et sans A2, c'est-à-dire 94 ventes réglées sans part. A n'est pas plus sûr que C : dans
  les deux, A2 est posé par la machine, avec ses gardes. La différence, c'est qu'en C quelqu'un est là au seul moment
  irréversible.
- **A ajoute au run de nuit une étape qui ne servira qu'une fois.** Elle resterait ensuite dormante dans le pipeline : un
  « mécanisme installé à moitié », qui a déjà mordu deux fois dans ce projet. Elle demanderait aussi ton « vas-y » sur une
  modification du run.

**Pourquoi pas B tel quel (« une heure où quelqu'un est réveillé »).** Une suite de commandes tapées à la main reste un pari
sur la précision du soir. C, c'est B **écrit et garanti** : une seule commande, des gardes, un arrêt automatique.

**Le coût chez Hektor : zéro requête.**
- `affaire_ledger.py` lit la copie locale.
- La doublure et les RPC parlent à Supabase.
- Rien n'appelle Hektor : ni lecture, ni console.

## La journée de la vague (le jour J), dans l'ordre

**J, le matin, après la descente (~08:15) — la préparation, en lecture seule :**
1. **Le témoin de la nuit précédente** (`temoin_de_la_nuit_2026-11-24.py comparer`).
2. **Une image et un passage du jour.** La répétition du 24/11 au soir a donné le passage 80 : 0 verdict changé, 4 lignes
   neuves, et des témoins identiques à ceux de 79.
3. **Le brouillon avec R26 et le retrait de E**, et le **rejeu exact** :
   - 0 faux ;
   - 0 étiquette déjà rendue qui bouge, hors celles que tu as nommées (21662, et 1c7b38f9 avec le retrait) ;
   - R7b sans faux ;
   - la garde du temps 2 à 0.
4. **A2, A1 et A3 remesurés à blanc** sur l'état du jour. Le patch A2 est fabriqué **par pièces**, pas par numéros de chaîne :
   ses cibles sont les chaînes d'arrivée, qui n'existent qu'après le chaînage. Il est joué à blanc chez Supabase **sur l'état
   d'arrivée simulé** : dans une transaction annulée, je pose les chaînes du rejeu, je joue A2, je contrôle, j'annule.
   C'est la vraie preuve d'A2 avant le geste.
5. **La commande du soir**, éprouvée à blanc : ses étapes 0 à 4, toutes réversibles.

**J, l'après-midi — ton accord sur quatre pièces :**
- le brouillon (son empreinte md5) ;
- le retrait de E (le diff du code) ;
- le patch A2 ;
- la commande du soir et son heure.

**J, le soir (~20:30)** — l'agence est fermée, et c'est avant l'entretien des documents de 22:00. **`vague_du_soir`**, une
seule commande :
- **0. Les gardes de départ.**
  - les pièces du jour sont là, avec leurs empreintes ;
  - aucun run ni descente ne tourne ;
  - le fichier des coupes en place est l'ancien (md5) ;
  - l'interrupteur est éteint.
- **1. Les sauvegardes datées :**
  - les chaînes et étiquettes du registre ;
  - `app_affaire_repartition` ;
  - le journal des étiquettes ;
  - l'ancien fichier des coupes ;
  - `.env`.
- **2. La pose.**
  - Le brouillon devient `phase2/sync/detachements_manuels.csv` (l'essai du 20/11, 279 lignes, est sauvegardé).
  - Le retrait de 4126 et 21520 est fait dans `EXCLUES_DE_LA_REGLE_E`.
  - `.env` passe à `APP_CHAINAGE_DETACHEMENTS=1` et `APP_CHAINAGE_GARDE_G2=0`.
- **3. La doublure du ledger** (`pull_from_supabase.py --table app_affaire_ledger`). C'est la même étape que celle du run.
- **4. ⛔ LE POINT DE NON-RETOUR, CONTRÔLÉ.**
  - Le rejeu de la vague tourne sur l'état du soir, en calcul pur, sans aucune écriture.
  - Il est comparé, pièce par pièce, au rejeu exact du matin.
  - **Au moindre écart, la commande remet tout comme avant** (le fichier, le code, `.env`) **et s'arrête.** Rien n'a été
    poussé, tout est réversible.
- **5. Le chaînage et sa poussée** (`affaire_ledger.py --refresh --push`), avec les étiquettes. **C'est le seul geste
  irréversible** : environ 795 étiquettes, dont 612 numéros neufs.
- **6. Le contrôle.** Les chaînes et les étiquettes chez Supabase doivent être celles du rejeu.
- **7. A2, puis A1 et A3.** Leurs gardes exigent que chaque ligne soit arrivée dans la chaîne prévue. Si une garde refuse,
  rien n'est écrit, la commande s'arrête, et nous sommes là pour trancher. Puis leurs répétitions.
- **8. L'étape de répartition** (`repartition_commission.py --purger-orphelines --pousser`). Elle lit la copie locale et
  appelle l'absorbeur chez Supabase, sans Hektor. Le verrou et le rangement des orphelines sont ainsi éprouvés le soir même.
- **9. Arrêt.** Les étapes qui lisent les chaînes (liens, mandats, contacts) tournent à 05:00 : pendant la nuit, personne ne
  travaille dans l'app.

**J+1, 05:00.** Le run rejoue le chaînage avec le même fichier : c'est déterministe, et ce sont les mêmes chaînes. C'est le
**témoin**. **J+1 au matin** : le témoin complet, c'est-à-dire la vague, A2, le verrou et les gestes du 24/11.

**Le retour arrière.**
- **Avant l'étape 5 :** total et automatique.
- **Après l'étape 5 :** on ne revient pas en arrière. Les numéros neufs ne se reprennent pas (« un numéro ne se perd
  jamais »). On avance et on corrige.
- **A2, A1 et A3** ont chacun leur inverse.
- C'est pour cela que l'étape 4 compare **pièce par pièce** avant de pousser.

**Au plus tôt :**
- J = le 25/11, si la préparation du matin est verte et si tu donnes ton accord dans la journée ;
- la soirée du 25/11 ;
- le témoin le 26/11 au matin.

La nuit du 24 au 25 sert au témoin du verrou et des gestes du 24/11.

---

## Le verrou, éprouvé à blanc (24/11, 17:5x)

La vraie fonction de la nuit, `app_repartition_absorber`, a été appelée chez Supabase dans une **transaction annulée** :
- **chaîne 1875** (A07EC3DH, posée par ④), avec la supposition que la nuit enverrait (GENTES 50 / 50,
  `hektor_partage_suppose`) : **`proteges_app = 1`, `lignes_ecrites = 0`, `dossiers_ecrits = 0`**. La chaîne est
  **intacte** : empreinte 37922d3d avant et après.
- **Le témoin inverse, chaîne 49** (qui ne porte que des suppositions, donc n'est pas protégée) : la même fonction la
  **réécrit**, avec **`lignes_ecrites = 2`, `dossiers_ecrits = 1`** (empreinte f1581dee → 61004cdb).
- Vérifié après : la chaîne 49 porte toujours son écriture du 16/09 ; rien n'est resté.

## Le témoin complet de demain matin, prêt

`phase2/checks/temoin_de_la_nuit_2026-11-24.py`. La **photo** a été prise le 24/11 à 16:57 UTC, avant le run : 17 907 parts,
et les quatre empreintes égales aux attendues. Demain, `comparer` dira :
- si ①, ④, ⑤ et les 42 ont **tenu** le run ;
- **le témoin inverse sur tout le registre** : les chaînes dont la répartition a **changé** pendant la nuit, rangées par
  origine (hektor% = réécrites par la nuit ; une autre origine = une saisie de l'app ou ⛔ un écrasement), les chaînes
  apparues et disparues, les chaînes réécrites **à l'identique** (ce que la nuit refait sans rien changer), et les chaînes
  **mixtes** (une part hektor% à côté d'une part protégée).

---

## La répétition générale de la préparation (24/11 au soir) — les pièces 2 à 4, en lecture seule

**② Image et passage du jour** (image 2026-11-24_175707, **passage 80**).
- C'est le passage 79 plus **4 lignes neuves** du Sheet : 3 tranchées, 1 en attente.
- **0 verdict changé.**
- Les témoins portent les **mêmes écarts** qu'aux passages 78 et 79 : déjà nommés, aucun neuf.

**③ Le brouillon avec R26, et le rejeu exact sur le passage 80.**
- Le brouillon a **les mêmes 630 morceaux** qu'au passage 79 ; seul l'en-tête change.
- **4 728 lignes justes sur 4 728**, et **4 728 étiquettes identiques** au passage.
- 0 pièce hors des biens.
- R7b : 21 dossiers figés sur 21, dont 2 nommés qui reçoivent un numéro neuf (14110, 27609).
- 0 ligne en attente qui bouge.
- 795 pièces changent d'étiquette, dont 612 numéros neufs.

**Le retrait de E (4126, 21520), à blanc sur le passage 80 :**
- **se débloquent exactement P252U1JH et d2108609** ;
- avec la vague, **0 autre ligne bouge** (ni au protocole, ni à l'arrivée) ;
- sans la vague, 1c7b38f9 et FOZ6HZLK bougeraient (D2025-0263 → D2025-0427 pour 1c7b38f9). C'est déjà connu, et c'est
  pourquoi le retrait ne se pose qu'avec la vague.

**④ A2, A1 et A3 remesurés sur l'état d'aujourd'hui**, c'est-à-dire après le geste des 42 et après ①, ④ et ⑤. La copie
locale de la répartition et des notes a été rafraîchie à 18:2x (deux tables, 14 et 4 524 lignes, 6 s).

**A2 v3 = v2 + ta décision « une annulée ne porte aucune part » :**
- **158 copies refusées** vers des annulées, dont V3FO5NDA. Leurs parts restent mises de côté, jamais supprimées.
- 199 parts recopiées, 143 mises de côté avec leur ancien numéro.
- NRZVKH85 est complété (sortie FERNANDEZ 50).
- La conservation boucle : 17 964 = 17 907 − 143 + 199 + 1.

**À l'arrivée, avec A2 v3 :**
- 4 495 lignes justes.
- 196 annulées sans part : c'est ta décision.
- 22 noms non résolus : la quarantaine du 13/11.
- 11 offres et 3 compromis en attente, sans part.
- 1 ligne aux noms différents : U0GQ3KTO, en réserve par ta décision.
- **0 vente réglée sans part : la garde est à 0** (sans le remède, ce serait 93 chaînes, dont 94 lignes).
- Le remède rend justes 99 lignes, et **n'en rend aucune fausse**.

**A1, le reflet des avis :** 10 décollés aujourd'hui, 81 après la vague sans remède. Le remède change 107 reflets ;
**contrôle après remède : 0.**

**A3, le reflet des notes :** 161 faux aujourd'hui, 276 après la vague sans remède. Le remède les recalcule ; **contrôle :
0.** Pour les conditions : 5 reflets faux, ce sont les saisies d'essai du 23/10.

**Ce qui reste à faire pour la nuit de la vague, une fois C accordé :**
- le patch A2 v3 **par pièces**, son jeu à blanc sur l'état d'arrivée simulé chez Supabase, et ceux d'A1 et d'A3 ;
- la commande `vague_du_soir` et son essai à blanc, étapes 0 à 4 ;
- refaire les pièces 2 à 4 le matin du jour J, sur l'état du jour.


---

## Le 24/11 au soir : les trois pièces (son 10e mot)

> Son mot : « ⭐ C VALIDÉ. [...] MAIS ON NE GARDE PAS 20:30 [...] ON LANCE DÈS QUE LA PRÉPARATION EST VERTE ET QUE J'AI
> ACCORDÉ LES QUATRE PIÈCES. ⛔ GARDE CES DEUX VERROUS, ILS NE DÉPENDENT PAS DE L'HEURE [...] ⭐ VAS-Y DÈS CE SOIR SUR LES
> TROIS PIÈCES QUI RESTENT. »

**Rien n'a été écrit.** Ni en base (seulement des lectures et des transactions annulées), ni dans le Sheet, ni chez Hektor.
Aucun fichier de la nuit n'a été touché : le fichier des coupes, le module de nuit et `.env` sont ceux du dépôt. Rien n'a été poussé.

**Une correction.** Le run commence à **04:00**, pas à 05:00 (tâche « GTI Quotidien », journal du 24/11).

### Pièce 1 — le patch A2 par pièces, et son essai à blanc sur l'arrivée simulée

**Le générateur.** `phase2/checks/a2_vague_generer_patch_2026-11-24.py`.
- **Son entrée** est l'export d'A2 v3 du script du temps 2. L'option nouvelle `--export-a2` l'écrit.
- **Les deux options ajoutées au temps 2 :**
  - `--export-a2` écrit l'export ;
  - `--retrait-e` mesure l'arrivée de la vague entière, R26 et retrait de E compris.
- **« Par pièces ».** Les parts à déplacer vivent sous l'ancien numéro de chaîne. Leur cible est « la chaîne où arrive la
  pièce P », lue au moment du geste. Le numéro d'une chaîne est le plus petit de ses membres, et la garde des membres le
  rend exact.
- **Les fichiers :** `supabase/patch_a2_vague_2026-11-24.sql`, `_A_BLANC_SIMULE`, `_PREGARDE`, `_INVERSE`, `_REPETITION`.

**Les gardes.** Une seule qui refuse, et rien n'est écrit.
- **G0 :** le patch ne se rejoue pas.
- **G1, les pièces :** les 231 chaînes touchées portent exactement les 480 membres prévus (empreinte 1212c9d9).
- **G2, les parts de départ :** les 272 parts sont celles lues à la fabrication (empreinte e09a38b9), et les 97 cibles sont
  vides.
- **G3 :** à l'arrivée et avant A2, exactement 93 chaînes à vente réglée sans part, nommées une à une.

**Le geste.**
- Une sauvegarde datée de toute la répartition.
- Le journal (lot `a2_vague_<jour>`) : chaque part avec sa ligne d'origine, sa place de départ et d'arrivée, et l'ancienne
  valeur.
- 199 recopies, faites depuis les parts vivantes que G2 vient de prouver.
- 143 parts mises de côté, entières, avec leur ancien numéro, puis retirées de leurs chaînes.
- La complétée de NRZVKH85.

**Chaque mise de côté porte son motif, nommé** (70 chaînes) :
- 34 sont **recopiées** sur la chaîne de leur ligne ;
- 24 voient leur ligne **arriver sur une annulée**, donc aucune part n'y est recopiée (son 3e mot). U0GQ3KTO est nommée
  **en réserve** ;
- 11 **disparaissent à la vague**, et les mêmes parts vivent déjà sur la chaîne d'arrivée ; la preuve est faite part par
  part ;
- 1 est **NRZVKH85**, complétée sur 22979.

⚠ **42 de ces chaînes existent encore à l'arrivée, mais sans aucune ligne.** Elles n'ont plus de part après A2 : 32
recopiées, 9 annulées et NRZVKH85. Aucune ne porte une vente réglée : le contrôle « 0 vente réglée sans part » le prouve.

**L'essai à blanc simulé, joué chez Supabase. Il est VERT.** Dans une transaction annulée :
- les 796 pièces qui changent de chaîne reçoivent la chaîne du rejeu (aucun déclencheur sur cette colonne) ;
- les gardes passent, puis le geste, les contrôles et l'inverse ;
- tout est revenu, puis l'annulation est voulue.

Les chiffres :
- **avant :** 17 907 parts (b531b578), 14 mises de côté, 80 lignes au journal ;
- **après A2 :** 17 964 parts. **Plus aucune vente réglée sans part.** 157 mises de côté, 423 lignes au journal, et
  l'empreinte d'après est **c6978c4ff65ba1be81edfcb0ae11b499** ;
- **après l'inverse :** exactement l'état d'avant ;
- **relu ensuite :** rien n'est resté (17 907 parts, b531b578, 14, 80, aucune sauvegarde, chaînes d'origine).

Le premier essai s'était arrêté sur **mon** contrôle « somme à 100 par côté ». La convention est 100 pour la chaîne
(entrée 50 + sortie 50, comme dans ④). Le contrôle a été corrigé, et rien n'était resté.

**Deux mesures réconciliées.** La simulation SQL trouve **93 chaînes** à vente réglée sans part avant A2. Le script du
temps 2 dit « 94 » en **lignes** et « 93 » en **chaînes** : une chaîne porte deux lignes réglées. Deux calculs
indépendants, en Python et en SQL, donnent les mêmes 93, et toutes sont des cibles d'A2.

**⚠ Un trou de ma préparation, trouvé et fermé.** L'export du passage 80 était mesuré **sans** le retrait de E. Or la vague
le pose dans la même nuit. Sur la vague entière (passage 81 à blanc, `--retrait-e`), le résultat est le même :
- seules deux offres changent de chaîne en plus : 4128 rejoint 4126, et 1001495 rejoint 21520 ;
- aucune des quatre chaînes en jeu ne fait partie des 231 d'A2, et aucune vente réglée n'est concernée ;
- A2 v3 est identique (199, 143, 1, garde 0, 99 rendues justes, 0 fausse) ;
- **le patch réel refabriqué est identique**, à l'étiquette « passage 81 » près.

L'essai joué ce soir est celui du passage 80. Celui de la vague entière diffère de deux couples dans la simulation ; il se
rejoue demain sur l'état du jour.

**Le brouillon de la vague** est donc celui du passage 81 à blanc : 636 lignes, md5 a6d58791. Il compte quatre morceaux de
plus que celui du passage 80 : les coupes de 43050 et de 9232.

### Pièce 2 — la commande du soir : `phase2/checks/vague_du_soir.py`

**À blanc par défaut.** Le geste exige `--geste --accord <md5 du manifeste accordé>`. Les pièces du jour sont dans un
**manifeste** (chemins et empreintes). La répétition de ce soir est `vague_du_soir/manifeste_repetition_2026-11-24.json`.

Les étapes : 0 gardes · 1 sauvegardes · 2 pose · 3 doublure · **4 point de non-retour** · 5 chaînage et poussée · 6 contrôle
· 7 A2 · 8 répartition · 9 arrêt.

Avant l'étape 5, un refus **remet tout comme avant** (fichier, code, `.env`). La commande écrit son compte rendu au fil dans
le dossier de sa scène.

**Le verrou 1, la garde de départ.** Elle vérifie :
- les pièces du jour et leurs empreintes ;
- GTI Quotidien et GTI Descente ;
- **les processus** du run, cherchés par leur ligne de commande (pas par `ps`) ;
- **toutes les tâches GTI** : aucune ne tourne, aucune ne démarre dans les 20 minutes ;
- le fichier des coupes en place, l'interrupteur, les deux exclusions encore au code, `git diff` vide ;
- le registre local = celui de l'image du matin ;
- **aucune pièce née dans l'app** depuis la préparation (lecture Supabase) ;
- la **pré-garde d'A2** : les parts n'ont pas bougé depuis la fabrication. Sinon A2 refuserait après le chaînage, et on
  s'arrête donc avant.

**⭐ Ce soir, elle a mordu pour de vrai.** Elle refuse 21:31, parce que « GTI Relances Email » démarre à 22:00 et que
« GTI Entretien Documents » tourne. C'est le témoin positif de la garde horaire. Toutes ses autres gardes sont vertes.

**Le verrou 2, le point de non-retour.**
- La **vraie fonction** est rejouée : `recalculer_les_chaines` du module **posé**, avec le fichier **posé** et les
  interrupteurs **posés**.
- Elle tourne sur une copie **en mémoire** du registre local, puis est comparée **pièce par pièce** au rejeu exact du matin.
- **Ce soir :** 31 372 pièces, **0 écart**, en 164 à 193 s.
- **⭐ Le témoin inverse :** contre le rejeu **sans** le retrait de E, l'étape trouve exactement les **2** pièces attendues
  (4128 → 4126, 1001495 → 21520) et **REFUSE**.

**Les interrupteurs arrivent au chaînage comme au run.** Les deux passent par `chainage_v2_actif()`, qui charge `.env`
avant de les lire. Le run ne pose aucune autre variable pour ces trois étapes.

### Les deux durées (pour information)

**La commande entière, étapes 0 à 8 : environ 8 minutes.**
- **Mesuré à blanc ce soir :** gardes 3 s, sauvegardes locales 1 s, pose < 1 s, point de non-retour 164 à 193 s.
- **Mesuré au journal du run du 24/11 :** doublure 95 s, chaînage et poussée 139 s, répartition 4 s.
- **Non mesuré :** les sauvegardes Supabase et A2 seul (quelques secondes chacun ; l'essai complet à blanc est revenu en
  quelques dizaines de secondes).

**La fenêtre 5 → 7 : environ 2 min 30 s.** Le chaînage et sa poussée prennent 2 min 19 s au run. S'y ajoutent le contrôle
(une lecture de 31 372 lignes, quelques secondes) et A2.
⚠ Ce soir-là, la poussée porte environ 795 étiquettes qui changent, dont 612 neuves : elle peut être un peu plus longue
qu'une nuit ordinaire.

**Le créneau.** Il n'y a plus d'heure fixe. La garde exige 20 minutes sans aucune tâche GTI :
- **« Relances Email »** démarre à chaque heure pile ;
- **« Health Monitor »** démarre aux heures paires à :48 ;
- le créneau sûr va donc de **hh:02 à hh:25**, et la garde le vérifie au lancement.

### Ce qui reste, et l'ordre de demain

1. **⏰ Le témoin de la nuit**, avant tout autre geste : `temoin_de_la_nuit_2026-11-24.py comparer`.
2. **La préparation sur l'état du jour :**
   - une image et un passage ;
   - les rejeux et les portes ;
   - le retrait à blanc (son passage et son brouillon) ;
   - l'export A2 (`--retrait-e`), le générateur, l'essai à blanc simulé (il rend G3 et l'empreinte d'après), puis le patch
     refabriqué avec ses deux empreintes ;
   - le manifeste du jour.
3. **Son accord sur les quatre pièces :**
   - le brouillon (md5) ;
   - le retrait de E (le diff du code, que l'étape 2 pose par l'arbre de syntaxe et prouve) ;
   - le patch A2 ;
   - la commande avec son manifeste (md5).
4. **Le geste :** `vague_du_soir.py --manifeste ... --geste --accord <md5>`, dans un créneau libre.

⚠ **A1 et A3 ne sont pas encore fabriqués en patch.** Ce sont les reflets des avis, des notes et des conditions : des
reflets, pas de l'argent. La commande les joue à l'étape 7 s'ils sont au manifeste.

### Son 11e mot (24/11, le soir) : A1 et A3 avec la vague ; les 42 nommées ; l'ordre de demain

- **⭐ (a) A1 et A3 AVEC LA VAGUE, à l'étape 7, le même soir.** Son contrôleur compte ce qui porte un reflet de dossier :
  2 560 avis, 4 524 notes et les conditions, soit **plus de 7 000 écritures**. Avec 795 étiquettes qui changent, attendre le
  lendemain laisserait des milliers d'écritures pointer, à l'écran, des dossiers qui n'existent plus.
  - « C'est le geste le moins dangereux de la soirée : **un reflet n'est pas une clé**. » Les avis sont identifiés par la
    ligne du Sheet ; les notes et les conditions par leur transaction. Rafraîchir un reflet ne déplace aucune écriture.
- **⬜ À chiffrer demain matin, avant son accord :** sur ces 7 000, **combien la vague rend faux**, et **combien A1 et A3
  en réparent**. « Je veux savoir ce que je répare. »
- **Les deux gardes : « garde-les telles quelles ».** L'horaire a refusé 21:31. Le point de non-retour a trouvé 0 écart,
  puis a refusé exactement les 2 pièces d'une version fausse. « Une garde qui n'a jamais rien refusé ne vaut rien. »
- **Le brouillon du passage 81** (636 lignes, md5 a6d58791) est le bon.
- **✅ Les 42 chaînes sans ligne ni part à l'arrivée : « ça me va », puisqu'aucune ne porte de vente réglée.** « Tu les
  NOMMES au journal avec leur raison, et on n'y touche pas. »
  - **FAIT :** leur motif dit « RESTE à l'arrivée (membres …) SANS LIGNE NI PART — NOMMÉE (son mot du 24/11 : aucune vente
    réglée, on n'y touche pas) ». Il est au journal et dans la mise de côté.
  - Un contrôle explicite est ajouté au patch : 0 part et 0 vente réglée sur les 42.
  - Gardes et empreinte d'après inchangées (c6978c4f). Ce contrôle se jouera à blanc demain avec le reste.
- **Les durées lui vont :** 8 minutes, et 2 min 30 pour la fenêtre dangereuse. Le créneau hh:02 → hh:25 vérifié par la
  garde lui va : « c'est elle qui choisit, pas moi ».
- **⏰ Demain, dans cet ordre :**
  1. le témoin de la nuit, avant tout autre geste ;
  2. la préparation du jour, A1 et A3 compris, avec leur chiffrage ;
  3. son accord sur les quatre pièces, plus A1 et A3.
- ⛔ Rien cette nuit.

---

## Le témoin de la nuit du 24 au 25/11 (son mot du 25/11, 07:1x) — mesuré AVANT de lire son contrôleur

> Son mot : « LANCE LE TÉMOIN DE LA NUIT MAINTENANT [...] JE VEUX LES DEUX FACES [...] AVEC TON EMPREINTE GLOBALE. ⚠ ET
> MESURE AVANT DE ME LIRE : mon contrôleur a pris sa propre photo hier soir à 22:00 [...] Si les deux ne tombent pas au
> même endroit, on s'arrête. »

**La mesure.** `temoin_de_la_nuit_2026-11-24.py comparer` a lu Supabase en lecture seule le 25/11 à 07:16 (06:16 UTC).
Ma photo date du 24/11 à 17:57 (16:57 UTC). La sortie est gardée dans `protocole/temoin_nuit_comparer_25_11.txt`.
- **Le premier lancement** a planté à la toute dernière ligne : le `%` de « hektor% » n'était pas échappé.
- **Corrigé**, puis complété de l'empreinte globale, de deux témoins et des tables voisines.

**Face 1 — ce qui a tenu : 4 / 4.**
- ① les 18 Charges : b58ba6cb.
- ④ les 12 parts : 91a61e04.
- ⑤ les 2 corrections : adb3c8f8.
- Les 42 écritures : 072b3cb3.

**Face 2 — ce qui a bougé ailleurs sans qu'il le demande : RIEN, dans tout le registre des parts.**
- **0 chaîne changée, 0 apparue, 0 disparue, 0 réécrite à l'identique** : aucun `ecrit_le` n'est neuf.
- 0 chaîne mixte, c'est-à-dire une part `hektor%` à côté d'une part protégée.
- **L'empreinte globale** (la même expression que les patchs) :
  - **photo :** 17 907 parts, **b531b578ece1a45387162d9b8f0f8c9a** ;
  - **maintenant :** 17 907 parts, **b531b578ece1a45387162d9b8f0f8c9a**.
- **Le témoin de la méthode :** la même empreinte recalculée en Python sur les lignes de maintenant est identique au SQL.
- **Le témoin positif du comparateur :** une part de la photo retouchée exprès (chaîne 351) est vue, 1 chaîne changée.

**Les tables voisines :**
- **le journal :** 80 lignes (charge 20, corrections 2, realignement_42 46, suppositions 12). Sa dernière écriture date
  du 24/11 à 15:39.
- **la mise de côté :** 14 (patch_suppositions 12, patch_corrections 2).
- **les notes :** 4 524 (classeur 190, classeur:F 256, classeur:F+G 585, classeur:G 3 484, saisie 9).
- **le carnet des mandats :** 871 Charges du classeur.
- **Écrit depuis la photo :** 0 note, 0 ligne du carnet, 0 part.

**Le zéro a son témoin positif : l'étape de répartition a tourné cette nuit** (06:27:19 → 06:27:22). Elle a envoyé
7 420 lignes ; la base en a protégé 3 710 dossiers, n'a rien refusé et a écrit **0 ligne**.
- **Comparé à la nuit du 24 :** protégés 3 704 → **3 710 (+6)** ; lignes envoyées 7 408 → **7 420 (+12)** ; « déjà à jour »
  4 357 → 4 351 (−6) ; toujours 0 écrite.
- **C'est exactement la taille de ④** (6 chaînes, 12 parts). L'explication : hier après-midi, la copie locale de la
  répartition a été redescendue avec ④ dedans. La nuit, qui compare à cette copie, a renvoyé ces 6 dossiers, et **la base
  les a protégés : c'est le verrou, en production**.
- ⚠ **C'est une concordance de comptes, pas encore une preuve nominative.** Le journal du run ne donne pas la liste. Elle
  se fera après la descente, en rejouant le calcul local sans pousser.

**La descente** a démarré à 06:50:06, après 5 minutes d'attente de la fin du run. À 07:17 elle était encore à l'étape 1/3
et écrivait `phase2.sqlite` : la préparation du jour l'attend.

**Les 26 répartitions « accrochées à un dossier disparu »** (l'alerte `data.repartition_orpheline`, rouge depuis le
21/11) :
- **Leur date :** toutes **du 13/11 à 22:56**, écrites par « rapatriement classeur 13/11/2026 », en
  `classeur_reconstitue`, 50/50. Ce sont **13 dossiers** : 3670, 11709, 14034, 14052, 14913, 19070, 19576, 19737, 20089,
  24011, 27135, 28179, 28547.
- **Aucune ne vient des gestes du 24/11**, et aucune nuit ne les a réécrites.
- **⭐ La vague les fait renaître.** Dans le rejeu de la vague entière (passage 81), **les 13 numéros existent à
  l'arrivée**, dont 6 qui portent une vente réglée (3672, 11712, 14036, 24013, 28181, 30762).
- **L'arrivée, avant A2,** compte 28 chaînes orphelines : ce sont exactement les 28 chaînes qui disparaissent à la vague,
  et **A2 les met toutes de côté**.
- **Donc 0 après A2.** Un contrôle est ajouté au patch A2 (« 0 part orpheline après A2 »), et un compteur à sa répétition.
  Ils se joueront à blanc dans la préparation du jour.
- **À vérifier dans la préparation :** que chacune des 26 est **juste** pour sa ligne d'arrivée (le témoin de fin du
  temps 2). La mesure du 23/11 disait 25 doublons purs et une divergence (27135 → 27133, sortie), que la vague sépare.

---

## Le 25/11 : son accord sur le témoin, la preuve nominative du verrou, la préparation du jour

> Son mot : « ⭐ OUI, NOS CHIFFRES TOMBENT AU MÊME ENDROIT [...] ⚠ nos deux empreintes globales ne sont pas les mêmes (la
> sienne b8e4a6ec, la tienne b531b578), parce que vous ne calculez pas sur les mêmes colonnes. Ce qui compte est que
> CHACUNE soit identique entre la photo et maintenant [...] ⬜ FAIS LA PREUVE NOMINATIVE [...] ⏰ VAS-Y : la préparation du
> jour [...] Rends-moi ensuite les quatre pièces et j'accorde. ⛔ Rien d'écrit avant mon accord. »

### La preuve nominative du verrou (phase2/checks/preuve_nominative_verrou_nuit_2026-11-25.py, lecture seule)

**Le calcul.** La vraie fonction de la nuit (`calculer` de repartition_commission.py) est rejouée **sans pousser**, avec
le python du run. Elle est comparée, par `a_envoyer`, à la copie locale : 17 907 parts, empreinte b531b578, identique à
Supabase.

**① La nuit du 25, rejouée :**
- 7 420 lignes à envoyer, 4 351 dossiers déjà à jour ;
- 3 710 dossiers envoyés, tous protégés par la règle de la base, 0 que la base aurait écrit ;
- **= le journal du run.**

**② La nuit du 24, contrefactuelle.** C'est la même copie, avec ④ et ⑤ défaits (les 12 + 2 parts mises de côté reprennent
leur place) : 7 408 lignes, 4 357 à jour, 3 704 protégés, 0 écrit. **= le journal du run du 24.**

**③ La différence, nommée : exactement les 6 chaînes de ④** (1027, 1875, 4234, 6391, 9370, 27984), et 0 dans l'autre
sens. Pour chacune, la nuit envoyait la supposition de Hektor, et la base portait son classeur ; elle a refusé. Par exemple :
- **1027 :** TRIOLLIER/TRIOLLIER contre DIMARIA/TRIOLLIER ;
- **1875 :** GENTES/GENTES contre DECHAUD/GENTES ;
- **4234 :** BLANCHARD contre CHAMPAGNAC.

**⭐ Le verrou est prouvé par les noms.**

### La préparation du jour

- **L'image** 2026-11-25_072625 a été prise après la descente (07:19:17, code 0). Elle compte 4 802 lignes au Sheet,
  31 375 pièces (3 de plus qu'hier) et 12 820 liens au gel.
- **Le passage 81 :**
  - 4 729 tranchées et 73 en attente ;
  - **un seul verdict change** : 571ffe9e, en attente → tranchée, parce que la nuit a amené sa pièce 30845 (bien
    63167) ; 0 ligne déjà rendue ne change ;
  - **les témoins sont identiques au passage 80** : 825 lignes sur 825, 0 écart neuf. Il sort en code 1 comme les
    passages 78 à 80, sur les mêmes écarts, déjà nommés.

- **Les portes du passage 81 :**
  - le brouillon porte **les mêmes 630 morceaux** qu'au passage 80 ;
  - le rejeu exact : **4 729 lignes justes sur 4 729, 4 729 étiquettes identiques** ;
  - 0 pièce hors des biens ;
  - R7b : 21 dossiers sur 21 (2 numéros neufs nommés : 14110, 27609) ;
  - 795 étiquettes changent, dont 612 neuves.
- **Le retrait de E à blanc** (passage 82 à blanc) :
  - se débloquent **exactement P252U1JH et d2108609** ;
  - avec la vague, **0 autre ligne ne bouge** ;
  - le brouillon de la vague entière compte **634 morceaux** (630 plus les 4 coupes de 43050 et de 9232) ;
  - le rejeu exact : 4 731 lignes justes sur 4 731, et 4 731 étiquettes identiques.
- **A2 v3 sur la vague entière :**
  - 199 recopies, 143 mises de côté, 1 complétée, sur 231 chaînes ;
  - la garde est à 0 (93 chaînes sans le remède) ;
  - 99 lignes rendues justes, 0 rendue fausse.
- **Le témoin de fin, 234 lignes** (233 hier) :
  - 196 annulées (sa décision), 22 noms non résolus (quarantaine du 13/11) ;
  - 12 offres (11 + **571ffe9e**, l'offre CROIZIER que la nuit a fait trancher), 3 compromis en attente ;
  - 1 U0GQ3KTO (réserve), **0 vente réglée**.

### L'essai à blanc complet (la vraie répétition de l'étape 7, après la poussée)

**Ce qu'il joue.** `supabase/vague_du_soir_2026-11-25_A_BLANC_COMPLET.sql`, par **la connexion même de la commande**
(`vague_du_soir.py --a-blanc-sql`). Le fichier est refusé s'il porte un `commit`, il doit lever son erreur voulue, le
retour arrière est explicite, puis une relecture prouve qu'aucune des tables qu'il crée n'existe.
- **Le canal a d'abord été éprouvé :** un fichier avec `commit` est refusé sans être envoyé ; un essai minuscule crée sa
  table (elle existe dans la transaction), tout s'annule, et la relecture le prouve.

**Dans une transaction qui s'annule :**
1. les 798 pièces reçoivent la chaîne de la vague ;
2. la **vraie** pose des étiquettes, `app_poser_etiquettes_dossier()` (son compteur est une table : aucun numéro consommé) ;
3. A2, A1, A3, leurs gardes et leurs contrôles ;
4. les inverses ;
5. le retour vérifié à l'état d'avant.

**VERT sur les versions finales :**
- **Avant :** 17 907 parts (b531b578), 14 mises de côté, journal 80, 155 notes fausses, 0 condition fausse, 26 parts
  orphelines.
- **La vraie pose :** pose 0, propagation 0, **fusion 231 dossiers / 250 lignes**, **scission 295 / 612**.
- **Après la vague, sans remède :** 269 notes fausses, 56 parts orphelines (les 28 chaînes qui disparaissent), 93 chaînes à
  vente réglée sans part.
- **Après A2, A1 et A3 :**
  - 17 964 parts, empreinte **f4e1feb6b43d1cc23698701493cf89a5** ;
  - **0 note fausse, 0 condition fausse, 0 orpheline, 0 vente réglée sans part** ;
  - 157 mises de côté ; journal 799 (A2 343, A1 107, A3 269).
- **Après les inverses :** égal à l'état d'avant. Rien n'est resté.

**⭐ La vraie pose des étiquettes, comparée pièce par pièce à la prévision du protocole**
(`vague_du_soir_2026-11-25_ETIQUETTES_A_BLANC.sql`) :
- **797 pièces** changent d'étiquette, toutes prévues ; 0 change sans l'être ;
- **185** vont vers une étiquette existante : 185 identiques, 0 différente ;
- **612** vont vers une neuve : 295 groupes prévus donnent 295 étiquettes neuves, 0 groupe éclaté.

Les « 250 lignes » de fusion comptent les 185 qui changent, plus 65 lignes des dossiers fusionnés qui portaient déjà
l'étiquette gardée.

⚠ **Au geste, la poussée criera « ATTENTION ÉTIQUETTES : 231 FUSION(S) (seuil 10) »** : c'est attendu, et nommé d'avance.

### Son chiffrage : sur les reflets, combien la vague rend faux, combien A1 et A3 réparent

Les chiffres sont prévus par le rejeu et **MESURÉS identiques** par l'essai complet (la vraie pose) : A1 107, A3 269.

- **Avis** (2 588 lignes, dont 2 560 portent un reflet) :
  - 29 sont faux aujourd'hui ; **la vague en rend faux 81** ;
  - **A1 en écrit 107** : les 81, plus 26 déjà faux aujourd'hui qui le resteraient. 3 faux d'aujourd'hui redeviennent justes
    d'eux-mêmes ;
  - 81 des 107 reçoivent un numéro neuf de la vague, 0 devient VIDE.
- **Notes** (4 524) :
  - 155 sont fausses aujourd'hui ; **la vague en rend fausses 228** ;
  - **A3 en écrit 269** : les 228, plus 41 déjà fausses qui le resteraient. 114 fausses d'aujourd'hui redeviennent justes
    d'elles-mêmes ;
  - 6 notes n'ont plus leur transaction au registre (1001388, 1001389, 1001391, 1001392, 1001394, 1001395) : nommées, pas
    touchées.
- **Conditions** (33) :
  - 0 fausse aujourd'hui, 0 rendue fausse, 0 écrite ;
  - 5 n'ont plus leur transaction (les essais du 23/10 : 1001388/1-2, 1001391/1-2, 1001394/1) : nommées, pas touchées.
- **En tout,** sur 7 117 reflets portés (2 560 + 4 524 + 33) :
  - **la vague en rend faux 309** ;
  - **A1 et A3 en écrivent 376** : les 309, plus 67 déjà faux aujourd'hui ;
  - **après : 0 faux** (mesuré).

### Les pièces de son accord (le manifeste du jour)

`C:\Hektor\chantier_classeur_q6_cache\vague_du_soir\manifeste_vague_2026-11-25.json`, **md5
ba4992c8c778bcb8fc881082c93c301a**. La commande refuse le geste sans cette empreinte, et l'étape 0 revérifie chaque pièce.
1. **Le brouillon :** `brouillon_detachements_protocole_passage_82.csv`, 636 lignes, 634 morceaux, md5 051aee25.
2. **Le retrait de E :** 10 lignes retirées (les entrées 21520 et 4126 d'`EXCLUES_DE_LA_REGLE_E`), 0 ajoutée ; il reste
   4496, 4720 et 26613. L'étape 2 le pose par l'arbre de syntaxe et prouve le diff. Le diff est dans
   `vague_du_soir/retrait_e_diff_2026-11-25.diff`.
3. **Le patch A2 :** `patch_a2_vague_2026-11-25.sql`, md5 0e00a16b.
   - G1 1212c9d9 (480 pièces), G2 e09a38b9 (272 parts), G3 les 93 chaînes nommées ;
   - 199 recopies, 143 mises de côté (70 chaînes, chacune son motif, les 42 NOMMÉES), 1 complétée ;
   - contrôles : 0 orpheline, 0 vente réglée sans part, l'empreinte d'après f4e1feb6 exigée ;
   - son inverse (9e11ebc9) et sa répétition (cf3ee5f9).
4. **La commande :** `vague_du_soir.py`, md5 a643152c, avec son manifeste. Éprouvée à blanc sur l'état du jour :
   - **étape 0 :** verte, sauf l'horaire, qui a mordu à 07:56 (Relances Email et Sauvegarde à 08:00), puis à 08:00 (les
     deux tournaient) ;
   - **étape 2 :** dépôt moins 10 lignes, 0 ajoutée ; `.env` ne change que ses deux interrupteurs ;
   - **étape 4 :** **0 écart sur 31 375 pièces** (164 s).
- **Plus A1 et A3 :**
  - `patch_a1_vague_2026-11-25.sql` (e3d6ecb7) **exige exactement 107 écritures** ;
  - `patch_a3_vague_2026-11-25.sql` (7f5df158) **exige exactement 269 écritures** ;
  - leur inverse est 1ddaef22 ; leurs pré-gardes sont à l'étape 0.

**Ce que l'essai ne couvre pas, et que je dis :**
- **L'étape 8**, la répartition de nuit le soir même. C'est la conversion ordinaire de la nuit : le verrou protège les parts
  du classeur et d'A2, il est prouvé par les noms, et il n'y aura aucune orpheline après A2.
- **La doublure de l'étape 3.**

### Ce que j'ai trouvé et corrigé en préparant (rien n'était encore joué)

- **La pose de l'étape 2 changeait les fins de ligne.** Le module de nuit et `.env` sont en LF ; `write_text` sous
  Windows les réécrivait en CRLF (la pose à blanc d'hier : 3 791 lignes CRLF).
  - La commande garde désormais les fins de ligne d'origine.
  - Elle **prouve** que le module posé est le dépôt moins les seules lignes retirées (aucune ajoutée).
  - Elle prouve que `.env` ne change que les deux interrupteurs ; elle ne nomme jamais une valeur, seulement une clé.
- **Un chemin du générateur A2 avait été abîmé** par l'outil Bash (une barre oblique avalée). Il est corrigé, et aucun
  autre fichier n'a de caractère parasite.
- **Le reflet `app_dossier_id` des notes et des conditions** est le numéro de BIEN de l'app (affaire_ledger.py, l. 55),
  pas l'étiquette : la vague n'y touche pas. A3 ne rafraîchit donc que `app_chaine_id`.

### Le geste de 08:09 : arrêté à l'étape 2 par la commande elle-même, puis remis à la main (25/11)

**Son accord, à 08:0x, porte sur le manifeste ba4992c8.** Le chemin complet du brouillon posé est
`C:\Hektor\chantier_classeur_q6_cache\protocole_a_blanc_retrait_e\brouillon_detachements_protocole_passage_82.csv` : 636
lignes, md5 051aee25fe8fa3c8caa5df93bb61c41d. C'est celui AVEC le retrait de E ; celui à 632 lignes est dans `protocole\`.

**Lancé à 08:09:31. L'étape 0 est verte, sans aucun refus.**
- **L'étape 1** a joué ses sauvegardes chez Supabase, quatre tables, suffixe 20261125_080931 :
  - le registre (chaînes et étiquettes) : 31 375 lignes ;
  - le compteur : 25 ;
  - le journal des étiquettes : 11 664 ;
  - la répartition : 17 907.
- **L'étape 2** a posé le fichier des coupes, puis le module. Puis :
  **« ⛔ ARRÊT : le module posé n'est pas le dépôt moins des lignes (0 ajoutée, 0 retirée) ».**

**Les deux défauts, les miens, dans la commande :**
1. **La preuve de pose, au geste, comparait le module à lui-même.** À blanc, le module posé est une copie dans la scène ; au
   geste, c'est le fichier du dépôt. La comparaison « dépôt contre posé » lisait donc le même fichier. La preuve de `.env`
   avait le même défaut (au geste, elle n'aurait jamais pu mordre).
2. **La remise automatique n'a pas joué.** Elle n'était prévue que si l'étape 2 avait FINI (`pose is not None`), et elle
   n'attrapait que les refus. Le fichier des coupes et le module sont donc restés posés ; `.env` n'avait pas été touché.

**Remis à la main tout de suite** (`--remettre` depuis les sauvegardes de la scène) :
- le fichier des coupes est revenu à f5a0a6d8, le module à a44f58df ; `.env` est resté à 30fd3b99, sans interrupteur ;
- `git diff` est vide.

**Relu chez Supabase :**
- seules les quatre sauvegardes datées sont nées : ce sont des ajouts, rien n'est détruit ;
- la répartition reste b531b578 (17 907), le journal 80, la mise de côté 14 ;
- les chaînes et étiquettes du registre ont la même empreinte que la sauvegarde de 08:09 (5c92aa71) ;
- **l'étape 5 n'a jamais été atteinte : rien n'a été poussé.**

**La correction** (commande a643152c → **5ff83ac6**, 20 lignes ajoutées, 4 retirées ; le diff est dans
`vague_du_soir/commande_diff_a643152c_vers_5ff83ac6.diff`) :
- les originaux (module et `.env`) sont lus AVANT toute écriture, et les deux preuves comparent le posé à eux ;
- la remise joue dès que la pose a COMMENCÉ, pour TOUTE erreur, et **jamais une fois l'étape 5 commencée**. Une poussée
  interrompue se tranche avec lui, et la commande le dit.

**Éprouvée sur le chemin du GESTE, sur des copies** (`test_vague_du_soir_geste_sur_copies.py`). C'est le vrai `main()` en
mode geste ; le `.env` est factice, et Supabase, les programmes et le chaînage sont des leurres.
- **A, une panne pendant la pose :** remis, copies identiques.
- **B, une erreur au point de non-retour :** remis.
- **C, une panne pendant l'étape 5 :** RIEN n'est remis, et la commande le dit.
- **D, le chemin vert :** les étapes 0 à 8 dans l'ordre, la pose prouvée, « 9. ARRÊT ».
- Les vrais fichiers n'ont jamais été touchés.

**Puis rejouée à blanc de 0 à 4 sur l'état du jour :**
- l'étape 0 entièrement verte (08:12, horaire compris) ;
- la pose : 10 lignes en moins, 0 ajoutée, et `.env` = ses deux interrupteurs ;
- le point de non-retour : **0 écart sur 31 375 pièces**.

**Le nouveau manifeste : e65ea11dd4495daa2411c131f058d973.** Il ne change que l'empreinte de la commande ; les autres pièces
sont identiques à ba4992c8. ⛔ **Il attend son accord** : celui de 08:0x portait sur la commande a643152c.

**La leçon.** Une preuve qui compare « avant » et « après » doit lire l'« avant » AVANT d'écrire. Et une remise doit être
prévue pour la panne PENDANT le geste, pas seulement après. L'essai à blanc ne pouvait voir ni l'un ni l'autre : il écrivait
ailleurs. **Un chemin de geste s'éprouve sur des copies EN MODE GESTE, pas seulement à blanc.**

---

## ⭐ LA VAGUE, JOUÉE LE 25/11 DE 09:02 À 09:07:54 (son accord sur le manifeste e65ea11d)

**Les essais :**
- **08:09** : arrêté à l'étape 2 par la commande (voir plus haut), remis ;
- **08:47** : la garde horaire **refuse** (Health Monitor à 08:48, Relances Email à 09:00), code 10, rien touché ;
- **09:02:04** : la garde accepte ; les étapes 0 à 8 passent ; code 0 ; 349 s.

**Le fichier posé**, en chemin complet :
`C:\Hektor\chantier_classeur_q6_cache\protocole_a_blanc_retrait_e\brouillon_detachements_protocole_passage_82.csv` → `C:\Hektor\Projet\phase2\sync\detachements_manuels.csv`.
- 636 lignes, md5 051aee25 (avec le retrait de E ; celui à 632 lignes est dans `protocole\`) ;
- le module : 10 lignes en moins, 0 ajoutée (md5 1f53b03f) ;
- `.env` : `APP_CHAINAGE_DETACHEMENTS=1`, `APP_CHAINAGE_GARDE_G2=0`, **posés en dernier**.

**Les durées, en secondes :** gardes 3, sauvegardes 1, pose 0, doublure 80, **point de non-retour 163**, chaînage et poussée
96, contrôle 0, A2+A1+A3 2, répartition 3. La fenêtre 5 → 7 a duré **98 s**.

**Ce que chaque étape a rendu :**
- **3 — la doublure :** 31 375 lignes en 78 s (119 appels), comme au run.
- **4 — le point de non-retour :** **0 écart sur 31 375 pièces**, 11 590 chaînes.
- **5 — la poussée :**
  - les étiquettes : pose 0, propagation 0, **fusion 231 dossiers / 250 lignes** (le cri attendu), **scission 295 / 612** ;
  - 31 375 lignes redescendues, 0 sans chaîne.
- **6 — le contrôle :** **0 écart** entre Supabase et le rejeu du matin.
- **7 — A2, A1 et A3 :**
  - les gardes d'A2 passent (480 membres, 272 parts, les 93 chaînes nommées) ;
  - A2 recopie 199 parts, en met 143 de côté, en complète 1 ; 343 lignes au journal ; **empreinte d'après f4e1feb6 =
    l'exigée** ;
  - A1 rafraîchit 107 reflets, 0 décollé ; A3 en rafraîchit 269, 0 faux ;
  - la répétition d'A2 : journal 343, parts du lot 200, mises de côté 143, 0 vente réglée sans part, **0 orpheline**,
    membres comme le rejeu, f4e1feb6.
- **8 — la répartition :**
  - le calcul local est identique (16 122) ; 7 419 lignes envoyées, 4 352 dossiers à jour ;
  - la purge : **0 orpheline gardée (26 ce matin), 0 en conflit (13 ce matin)** ;
  - la poussée : **3 706 protégés, 0 refusé, ⚠ 5 lignes écrites dans 3 dossiers**.

**La mesure d'après**, en lecture seule (`vague_mesure_apres_2026-11-25.py`, contre les sauvegardes de 09:02) :
- **798 pièces** ont changé de chaîne, **0 écart** au rejeu du matin ;
- **797 pièces** ont changé d'étiquette, **exactement comme prévu** : 185 vers une existante, 612 vers une neuve, 295
  groupes → 295 étiquettes neuves, 0 éclaté. La liste est dans `notice/LA_VAGUE_DU_25_11_LES_PIECES_QUI_ONT_BOUGE.csv` (798
  pièces : chaîne et étiquette avant → après, la prévision, le verdict) ;
- **le journal des étiquettes** passe de 11 664 à 12 208 : 544 lignes écrites ce matin (fusion 249, scission 295) ;
- **le journal du réalignement** passe de 80 à 799 (a2 343, a1 107, a3 269) ; la mise de côté de 14 à 157 ;
- **les parts orphelines : 0** (26 parts sur 13 chaînes ce matin) ; ventes réglées sans part : 0 ; notes et conditions au
  reflet faux : 0 ;
- **la répartition :** 17 967 parts. L'empreinte valait f4e1feb6 après A2 ; elle vaut **12695d1f** après l'étape 8.

### ⚠ Ce que l'étape 8 a fait autrement que je l'avais annoncé : 3 dossiers écrits

J'avais dit « la conversion ordinaire, sous le verrou ». Elle a écrit 5 lignes dans 3 dossiers, contre 0 les nuits
précédentes :
- **3647** (une chaîne née de la vague : compromis 3647 et vente 3650 non réglée) : **aucune ligne n'y arrive.** La nuit y
  pose la supposition de Hektor (GENTES 50/50), comme sur toute chaîne sans ligne. C'est la conversion ordinaire.
- **27136** (une offre et une vente non réglée), **une des 42 nommées** : **aucune ligne n'y arrive** (IEYXREWQ est sur
  27134, une annulée). A2 avait mis de côté ses parts du classeur (COUDERT 50/50, du 13/11). Vide, elle n'est plus protégée,
  et la nuit l'a remplie comme toute chaîne sans ligne (HERITIER 50/50). Rien n'est perdu : COUDERT est dans la mise de côté.
- **⛔ 8016** (compromis 8016 et **vente réglée 8019, 27/03/2019**) : **SXJDHXKF y arrive**, ROMERA 100 au Sheet.
  - Après A2, elle portait ROMERA 50/50 en supposition de Hektor : **juste**.
  - L'étape 8 a recalculé la chaîne, dont la vague avait changé la composition, et n'y a laissé que la **sortie ROMERA 50** :
    **fausse, à moitié**.

**La cause : ma règle A2, « les mêmes parts y vivent déjà ».** Elle comparait les **valeurs** sans l'**origine**. Pour
8019 → 8016, les parts de la cible étaient des suppositions de Hektor, non protégées ; les parts du classeur de 8019 (ROMERA
entrée 50 + sortie 50) ont été mises de côté. C'est **exactement sa leçon du 24/11 : l'origine est le verrou.** Je l'avais
écrite, et je ne l'ai pas appliquée à cette règle.

**La mesure des 11 chaînes « mêmes parts » :** 10 portent les parts du classeur (protégées, du 13/11) et n'ont pas bougé ;
**seule 8016** portait une supposition. **Le défaut tient en une ligne, SXJDHXKF.**

**Le remède, à son accord, rien n'est fait.** Sur 8016 :
- la part de la nuit (sortie ROMERA 50, `hektor_partage_suppose`) est mise de côté (règle 6) ;
- les parts du classeur de 8019 sont recopiées depuis la mise de côté : ROMERA entrée 50 + sortie 50, `classeur_reconstitue`
  (protégées) ;
- au journal, avec la ligne SXJDHXKF.

Sans remède, la nuit de 04:00 récrira 8016 à l'identique (la moitié) : rien n'empire, mais rien ne se répare.

### ⛔ RÈGLE (son mot du 25/11) : L'INTERRUPTEUR SE POSE EN DERNIER

> « L'ORDRE DE TES ÉTAPES (fichier → module → .env en DERNIER) t'a protégée. Garde-le, et écris-le dans la procédure comme
> une règle. »

**La règle.** Dans toute pose qui change la nuit, l'ordre est :
1. les fichiers que le code lit ;
2. le code ;
3. **l'interrupteur, EN DERNIER.**

Une pose interrompue avant la dernière marche laisse un fichier **inerte** : la nuit ne le lit pas. Le 08:09 l'a prouvé.

**Sa sœur, qui vaut pour tout le projet :** un essai à blanc ne prouve pas un chemin de geste, parce qu'il travaille sur une
copie. Le chemin de geste s'éprouve **EN MODE GESTE, sur des copies, avec des leurres**.

### Son mot du 25/11 : le remède de 8016, et « ta cause est-elle ailleurs ? »

> « ⭐ (a) FABRIQUE LE REMÈDE DE 8016 MAINTENANT, avec son essai à blanc, et montre-le-moi avant de poser [...] ⛔ ET LA VRAIE
> QUESTION [...] : TA CAUSE EST-ELLE AILLEURS ? [...] combien d'AUTRES endroits de A1, A2, A3 et du remède comparent des
> parts, des notes ou des reflets sans regarder l'origine ? Nomme-les-moi, même si la réponse est « aucun » -- mais dis-le
> après avoir cherché, pas avant. »

Son contrôleur a vérifié de son côté :
- 4 chaînes de la base ont une somme qui n'est pas 100, et une seule porte une vente réglée : 8016 ;
- idem pour les chaînes à un seul côté ;
- 0 vente réglée sans part.

**Le remède de 8016**, généré par `remede_8016_generer_patch_2026-11-25.py`. Les fichiers sont
`supabase/patch_remede_8016_2026-11-25.sql` (md5 eccc92b6), `_A_BLANC`, `_INVERSE` et `_REPETITION`.
- **Les gardes portent toutes l'ORIGINE :**
  - G1 : 8016 a exactement les membres 8016 et 8019 ;
  - G2 : sa seule part est celle de la nuit (sortie, 195, Solange ROMERA, 50, `hektor_partage_suppose`, `conversion`) ;
  - G3 : la mise de côté d'A2 porte exactement les deux parts du classeur de 8019 (id 645 et 644 : entrée et sortie,
    SOLANGE ROMERA 50, `classeur_reconstitue`).
- **Le geste :**
  - une sauvegarde datée ;
  - le journal (lot `remede_8016_2026-11-25`, 3 lignes, ligne d'origine SXJDHXKF) ;
  - la part de la nuit mise de côté, entière, puis retirée ;
  - les deux parts du classeur recopiées depuis la mise de côté, où elles restent comme trace d'A2.
- **Les contrôles :**
  - 8016 = ROMERA entrée 50 + sortie 50 du classeur, somme 100, **PROTÉGÉE** (une part hors `hektor%`) ;
  - la part de la nuit est en mise de côté, entière ; 0 orpheline ; 0 vente réglée sans part ; 17 967 + 1 parts ;
  - l'**empreinte d'après 1dccc51297c54a99e38294756d790fc3** est exigée.
- **L'essai à blanc**, par le canal de la commande, est **VERT** : 17 967 parts (12695d1f) → 17 968, 8016 = entrée SOLANGE
  ROMERA 50 classeur + sortie SOLANGE ROMERA 50 classeur, empreinte 1dccc512 → l'inverse rend l'état d'avant. Rien n'est
  resté.
- **⛔ Il n'est PAS posé** : il attend son accord.

**Le balayage de la famille.** `sig_rows`, la signature avec laquelle A2 compare des parts, ne porte que (côté,
négociateur, pourcentage) : **ni l'origine, ni le rang, ni le nom**. Chaque endroit a été mesuré sur l'état du matin, avec
`--familles` (temps 2) et des lectures chez Supabase.
- **A2 ①, recopie sautée quand la cible porte des valeurs égales (l. 225) :** 7 paires, dont **1 seule** où la cible ne
  portait que des suppositions : **8019 → 8016 (SXJDHXKF)**. C'est le défaut.
- **A2 ②, « les mêmes parts y vivent déjà » (l. 241) :** 10 chaînes, 0 sur des suppositions (toutes du classeur, du 13/11).
- **A2 ③, la garde v2, quand une ligne qui arrive « reconnaît » les parts (l. 198) :** 13 chaînes, 0 sur des suppositions.
- **A2 ④, « possède » (l. 189/194) :** 12 chaînes possédées ne portent que des suppositions, mais 0 part d'origine Hektor
  n'a été recopiée. Ces lignes restent sur leur chaîne.
- **A2 ⑤, la complétée de NRZVKH85 (l. 258) :** 22979 est **mixte** (entrée FERNANDEZ en supposition + sortie du
  classeur), donc **protégée**, la supposition y est figée. Exposition 0.
- **A2 ⑥, l'échange (l. 272/281) :** jamais joué.
- **A2 ⑦, le jugement de justesse (le témoin de fin) :** il compare les valeurs, et c'est une mesure, pas une décision.
- **Le générateur A2, la preuve « mêmes parts » :** même signature sans l'origine ; 0 sur des suppositions aujourd'hui.
- **Le patch A2 (SQL) :** ses gardes et contrôles portent l'origine (l'empreinte G2, la recopie, la mise de côté, « hors du
  lot intactes »).
- **A1 :** le reflet est recalculé sans regarder l'origine de la ligne d'avis. Les 2 588 avis sont tous d'origine classeur, et
  les 107 rafraîchis aussi : **exposition 0**.
- **A3 :** les reflets sont recalculés sans regarder l'origine de la note ou de la condition. Les 269 rafraîchis sont tous
  classeur : **0 des 9 notes saisies, 0 des 5 conditions saisies**.
- **Le remède de 8016 :** chaque garde et chaque contrôle porte l'origine.

**⇒ Le défaut tient en UNE chaîne, 8016**, ce que son contrôleur a trouvé par un autre chemin (les sommes).

**⚠ À nommer, sans cause dans A2 :** 12 **ventes réglées** sont **justes aujourd'hui sur des suppositions de Hektor** (non
protégées), et la vague n'a pas changé leur composition. Si Hektor change, la nuit suivra Hektor :
- 2U5QPKRC (VALLA J, chaîne 17769) · 58I5AO17 (DAUDET, 7908) · 8ATXF2EZ (VALLA J, 19152) · 91IHSGNC (CHAMPAGNAC, 4781) ;
- EJN79TJ1 (BRAVARD, 27712) · ESMCO1NC (DELVAUX, 6588) · I3TFR2KG (BILLIG, 24618) · J6RGX0CQ (CHAMPAGNAC, 4928) ;
- JL8GV7RQ (SABATIER, 15169) · LUX9SDIL (DESOUSA, 14119) · MDOXOBIC (GENTES, 2163) · S8BKB6FL (JORAND, 4412).

Les protéger, c'est-à-dire recopier leurs mêmes valeurs en `classeur_reconstitue`, est une décision qui lui revient. Rien
n'est fait.

**Le témoin de demain** (`temoin_de_la_nuit_2026-11-25.py`) a pris sa photo le 25/11 à 09:28, AVANT le remède :
- 17 967 parts (12695d1f), 31 375 pièces, 0 orpheline, 0 vente réglée sans part, journal 799, mise de côté 157, 11 605
  étiquettes ;
- si le remède est posé, la photo sera reprise juste après.

### Le remède de 8016 et les 4 dates d'annulation : UN SEUL GESTE (25/11, 10:0x, son accord)

> « ⭐ VAS-Y, POSE LE REMÈDE DE 8016 [...] ⭐ ET DANS LE MÊME GESTE, POSE LES DATES D'ANNULATION QUI RESTENT -- ma règle : la
> date du Sheet sur SON compromis quand il n'en a pas. Dis-moi combien exactement avant de poser. Les 2 antérieures restent
> écartées. ⛔ UN SEUL GESTE, UN SEUL COMPTE RENDU. »

**Le compte, mesuré avant de poser (après la vague) : 4 dates.**
- Les 6 compromis du 24/11 sont toujours ANNULÉS SANS DATE ; moins les 2 antérieures, il en reste 4.
- Les dates sont relues dans le Sheet du jour :
  - **TR42PT5H** → 27195 : 20/05/2025 ;
  - **U0GQ3KTO** → 4385 : 22/11/2022 ;
  - **IEYXREWQ** → 27134 : 01/02/2024 ;
  - **R0JRVFDC** → 16377 : 21/01/2021.
- **NOMMÉES au journal, rien écrit :**
  - S3HOG6UL (17387) et 6U5DQQ4J (24450), antérieures au compromis, écartées par sa décision ;
  - T2GZOY5O (20073), jumelle en réserve ; O6R10ZQA est la bonne, et son 21/09/2021 est déjà sur 20073.
- **Le patch** (`dates_annulation_generer_patch_2026-11-25.py`, md5 46c9d67a) :
  - les gardes : 4 compromis annulés sans date, et les 7 lignes telles que lues ;
  - une sauvegarde datée, et le journal avec la place, la ligne d'origine et l'ancienne valeur ;
  - le geste ne touche QUE les cases vides de la ligne « POSER » ;
  - les contrôles : les 3 nommées et toutes les autres colonnes intactes ; l'empreinte d'après **ce7e070a** est exigée.
- **L'essai à blanc était VERT** (l'inverse rend 4011dda9).

**Le geste** (`poser_remede_8016_et_dates_2026-11-25.py`, par la connexion de la commande). Il vérifie l'empreinte de chaque
fichier (eccc92b6, 46c9d67a) avant d'envoyer, puis joue les deux patchs et leurs deux répétitions. Résultat : **VERT**.
- **8016** porte entrée SOLANGE ROMERA 50 + sortie SOLANGE ROMERA 50, `classeur_reconstitue` : **PROTÉGÉE**. La part de la
  nuit est en mise de côté (1) ; journal 3 ; 0 orpheline ; 0 vente réglée sans part ; empreinte **1dccc512** = l'exigée.
- **Les dates :** 27195 = 2025-05-20, 4385 = 2022-11-22, 27134 = 2024-02-01, 16377 = 2021-01-21. 17387 et 24450 restent
  sans date, 20073 = 2021-09-21 ; journal 7 ; empreinte **ce7e070a** = l'exigée.

**Ses deux réserves tombées avec la vague, vérifiées par les noms et RAYÉES :**
- **a5cb141f** (RONDEAU 50 / DELAVAUD 50) : la chaîne 6172 porte DELAVAUD + RONDEAU, du classeur ;
- **JRE23R1G** (COUDERT 100) : la chaîne 27135, une des 13 renées de la vague, porte COUDERT des deux côtés, du classeur.

**Le balayage « sans l'origine », redit avec les deux patchs de ce geste.** Il a été fait et mesuré AVANT, plus haut :
- A2 ① : 1 seule chaîne (8016) ; ② 0 ; ③ 0 ; ④ 0 recopie hektor ; ⑤ 22979 mixte, protégée ; ⑥ jamais joué ;
- A1 et A3 : que du classeur ;
- **le remède de 8016 :** chaque garde et chaque contrôle porte l'origine ;
- **le patch des dates :** il ne compare aucune part. Il n'écrit que sur une case VIDE, et toute autre colonne est
  contrôlée.

**⇒ aucun autre endroit.** Les 12 ventes réglées justes sur des suppositions restent nommées, à sa décision, sans cause
dans A2.

**Le témoin de demain** (`temoin_de_la_nuit_2026-11-25.py`) :
- **sa photo est reprise à 10:01, APRÈS ce geste** : 17 968 parts (1dccc512), 0 orpheline, 0 vente réglée sans part,
  journal 809, mise de côté 158, 11 605 étiquettes ;
- **il dira :** la vague a-t-elle tenu (chaînes et étiquettes de chaque pièce) ? les orphelines sont-elles restées à 0 ?
  **8016 est-il protégé du run ?** Et il dira ce que la nuit a réécrit ailleurs ;
- **éprouvé contre lui-même :** tout TENU, et le comparateur voit une part retouchée exprès ;
- **corrigé :** il comparait les 4 gestes du 24/11 à leur empreinte de ce jour-là. Celle des 42 avait changé par les gestes
  accordés du 25/11 (A3 sur des reflets de notes, les dates sur 27195 et 27134). **PROUVÉ :** en retirant ces deux effets
  par leurs sauvegardes, l'empreinte redonne exactement **072b3cb3**. Il compare désormais la photo à maintenant.

### Le 25/11, la suite : le commit de la pose, les 21 ventes réglées, le rejeu du chaînage, la colonne A

**La pose commitée** (35fa604, en local, pas de push). Le message nomme les interrupteurs ALLUMÉS
(`APP_CHAINAGE_DETACHEMENTS=1`, `APP_CHAINAGE_GARDE_G2=0`) : `.env` est ignoré par git. Vérifié avant le commit :
- `detachements_manuels.csv` : 636 lignes, md5 051aee25 ;
- le module : 10 lignes retirées (21520 et 4126), 0 ajoutée ; restent 4496, 4720, 26613.

**Les ventes réglées non protégées. Ses 21 contre mes 12 : ce sont deux populations.**
- **Les 21 de son contrôleur sont celles du REGISTRE** (`vente_reglee_app`) : 3 729 chaînes, dont 3 708 entièrement
  protégées et 21 avec au moins une part `hektor%`. **Recompté identique.**
  - Mélanie LEGRAND en porte **11** chez moi, pas 10 : 49, 78, 98, 102, 165, 204, 249, 1075, 1081, 1116, 1128.
- **Le classeur les nomme TOUTES** : chacune a une ligne tranchée « Vente réglée ».
  - **20 sont 20 des 22 « NOM NON RÉSOLU »** du témoin de fin, motif « nettoyage : apporteur avec une part ». Le Sheet donne
    une part à un **apporteur** qui n'est pas un négociateur : **meilleursagents** sur 15 lignes (souvent 75/25), **GTI** sur 4
    (dont ABED 50 / GTI 50), **DENOPCE 1/2** sur 1. Le rapatriement du 13/11 les a mises en quarantaine, et elles sont restées
    sur la supposition de Hektor, que la nuit réécrit à l'identique.
  - **La 21e est 22979** (NRZVKH85, FERNANDEZ 100) : mixte, juste, protégée.
- **Mes 12 sont des lignes « Vente réglée » AU SHEET dont la vente n'est PAS réglée au registre** (`vente_reglee_app`
  vide), justes sur des suppositions. Aucune n'est dans ses 21.
- **⇒ Réparable ?** Les 20 sont dans le classeur, mais leur part d'apporteur n'a pas de place dans le registre des parts,
  qui ne connaît que des négociateurs. C'est une règle à lui : comment poser la part d'un apporteur. Les 12 se protègent
  mécaniquement (les mêmes valeurs, recopiées en `classeur_reconstitue`) : c'est aussi sa décision.

**② Le rejeu du chaînage : SANS une requête Hektor.** Sa commande (`run_quotidien.ps1 -StartAtLabel « phase2 doublure du
ledger d affaires »`) n'a **PAS** été lancée telle quelle : elle enchaîne aussi l'entretien des compromis et des ventes par la
console (jusqu'à 2 × 150 lectures Hektor) et la sonde des photos (50 requêtes). J'ai joué ses **deux premières étapes** comme
le run les joue (la doublure, puis `affaire_ledger.py --refresh --push`), et rien d'autre.
- **Résultat :** la doublure en 83 s, le chaînage en 98 s, 31 375 lignes poussées.
- **Les empreintes des chaînes** (94db0a65) **et des étiquettes** (8285bce3) sont **IDENTIQUES avant et après**.
- **La pose :** pose 0, propagation 0, fusion 0, scission 0 ; le journal des étiquettes reste à 12 208 ; **0 orpheline** ;
  17 968 parts.
- **La vague est déterministe.**

**③ La colonne A** (`ecrire_colonne_a_du_sheet_2026-11-20.py`, à blanc, aucune écriture dans le Sheet) :
- **`simuler`** rend 34 verdicts, 33 verts, sans aucun POST vers Google. Le rouge est un **témoin non éprouvé** :
  « ETIQUETTE_PARTAGEE », car plus aucune ligne réelle ne montre une étiquette partagée.
- **`preparer --nom vague1a --premieres 50`** : 50 lignes, **0 écartée**
  (`notice/CLASSEUR_VAGUE_vague1a_2026-11-25.csv`, sha 5c2e8a02).
- **`a_blanc`** : **50 À ÉCRIRE, 0 sautée** ; empreinte de la vague 5c2e8a02c756e706 ; colonne A 8b6e4e39eb626cfa (vide sur
  les 4 807 lignes).
- **Le bon à lire**, avec la ligne du Sheet, l'ID, le numéro de dossier et l'acquéreur, est dans
  `notice/CLASSEUR_VAGUE_vague1a_2026-11-25_LE_BON_A_LIRE.txt`.
- **⛔ Rien n'est écrit** : son accord vient après sa lecture de son Sheet.

**Les lignes « à plusieurs dossiers ».**
- **Au 19/11**, 224 lignes étaient dans la case « plusieurs dossiers ». **Après la vague, selon la règle de l'outil :**
  - 19 ont encore plusieurs étiquettes ;
  - 10 relèvent de sa DÉCISION_19 du 20/11 ;
  - les 195 autres passent dans un fichier, et leur à blanc en déclare 192 écrivables (3 sautées).
- **Sur tout le Sheet, 63 lignes** portent aujourd'hui plusieurs étiquettes : 19 « plusieurs dossiers », 17 PATCH_V2, 11
  « étiquette partagée », 6 en attente et 10 de VAGUE_1. **Sans les 10 de VAGUE_1, cela fait 53** : probablement ses 53, à
  confirmer. Elles restent vides et nommées : l'outil les écarte.

**Sa « décision B » du 20/11** (9 lignes : « vague 2, après G2 ») **est accomplie, par la vague**.
- Les 9 lignes (WG8CG5T2, R9ANL92S, SA7DWYEZ, ANHQ1PK7, MFMR0U6A, V5NJER40, JBCC1KBT, A6OS2TTJ, QL70KV8I) ont été coupées
  par les morceaux du brouillon, sans G2.
- Chacune a reçu l'étiquette **neuve** que B prévoyait (par exemple WG8CG5T2 : D2019-0572 → D2020-0638), et porte les parts
  recopiées par A2.
- **L'outil de la colonne A les écarte encore** : sa liste DECISION_B est écrite dans son code et exige 9 lignes. Les
  écrire demanderait de lever cette exclusion, donc un changement de code, à son « vas-y ».

### La colonne A : les 50 premières lignes ÉCRITES (vague1a, 25/11 à 11:13:31, son accord) — puis ARRÊT

> « ⭐ VAS-Y : ÉCRIS LES 50 PREMIÈRES LIGNES DE LA COLONNE A. Empreinte de vague 5c2e8a02c756e706, empreinte de la colonne
> A 8b6e4e39eb626cfa. ⛔ ET TU T'ARRÊTES LÀ. Tu me rends le compte rendu, JE REGARDE MON SHEET DE MES YEUX, et c'est
> seulement après que tu continues. Pas 100, pas 500 : cinquante. »

**La commande.** L'interrupteur `APP_SHEET_ECRIRE_AFFAIR_UUID=1` est donné à elle seule. Il n'est pas dans `.env`, et je
l'ai vérifié avant de lancer :
`python -u -X utf8 phase2/checks/ecrire_colonne_a_du_sheet_2026-11-20.py ecrire --vague notice/CLASSEUR_VAGUE_vague1a_2026-11-25.csv --empreinte-vague 5c2e8a02c756e706 --empreinte-colonne-a 8b6e4e39eb626cfa`
- **Le résultat :** sortie 0 ; **50 écrites, 0 sautée** ; l'empreinte de la vague est vérifiée (5c2e8a02c756e706).
- **La sauvegarde et le rapport** sont dans `C:\Hektor\Backups\classeur_colonne_a\2026-11-25_111331_vague1a_ECRIRE`.
- **Les 5 critères de l'outil sont verts :**
  - les 50 lignes sont relues sur leur ID Unique, 0 fausse ;
  - aucune autre case A n'est modifiée ;
  - rien n'est écrit hors de la colonne A ;
  - l'étiquette écrite est celle des transactions ;
  - aucun uuid n'est sur deux lignes.
- **Ma relecture indépendante**, par `apparier_classeur.lire_classeur()` et non par l'outil :
  - 4 802 lignes lues ; **50 cases A remplies, et ce sont les 50 de la vague** ;
  - chacune est sur la ligne de son ID Unique et porte l'étiquette prévue ;
  - **0 hors de la vague, 0 fausse, 0 manquante** ;
  - les 50 sont à la même ligne qu'à la préparation (lignes 4 à 70).
- **Rien d'autre :** aucune 51e ligne, rien chez Hektor, pas de push. La vague suivante attend qu'il ait regardé son Sheet.

**Les lignes à plusieurs dossiers : 48 aujourd'hui, pas 53, et toutes vides. Je corrige mon chiffre du matin.**
- **Le chiffre du matin :** j'avais compté 63 lignes, soit 53 hors VAGUE_1. Je lisais les transactions du CLASSEMENT du
  19/11.
- **La lecture de l'outil :** il lit le GEL DU JOUR, avec les pièces effectives (une copie ne décide pas de l'étiquette).
  Par cette lecture, il y a **48 lignes**, dont 10 de VAGUE_1, donc **38 hors VAGUE_1** :
  - 19 « plusieurs dossiers » ;
  - 11 « étiquette partagée » ;
  - 6 en attente ;
  - 2 PATCH_V2.
- **L'écart, nommé ligne à ligne : 63 − 17 + 2 = 48.**
  - 17 lignes PATCH_V2 n'ont plus le gel du 19/11 :
    - 15 n'ont plus qu'une étiquette ;
    - 2 n'ont plus de lien (8Q3LHGZ4, a8aaeb2b).
  - 2 lignes sont sur deux étiquettes dans le gel du jour, et ne l'étaient pas le 19/11 : R0JRVFDC et f90b0418.
- **Aucune n'est dans la vague1a, et leur case A est vide :** la relecture ne voit que les 50.
- **La liste nommée :** `notice/CLASSEUR_COLONNE_A_LES_LIGNES_A_PLUSIEURS_DOSSIERS_2026-11-25.csv`. Elle porte la ligne,
  la case du 19/11, les dossiers et les pièces effectives.

**Les 21 ventes réglées sur une supposition, nommées avec leur montant.** Son mot : « Nomme-les proprement, avec leur
montant ». ⬜ **Rien n'est décidé** : la manière de représenter la part d'un apporteur est son chantier à part.
- **La source des montants.** Sur les 21, la commission TTC du Sheet est égale aux honoraires d'entrée du registre (0
  écart). La part d'un apporteur vaut la commission TTC × son pourcentage au Sheet.
- **20 lignes donnent une part à un apporteur :**
  - **meilleursagents, sur 15 lignes : 18 075 € TTC.**
    - À 25 % sur 14 lignes : 49 (1 075 €), 64 (875 €), 78 (1 625 €), 98 (1 750 €), 102 (1 750 €), 165 (1 725 €),
      204 (1 375 €), 249 (1 275 €), 1075 (675 €), 1081 (1 500 €), 1116 (1 250 €), 1128 (1 250 €), 10072 (600 €),
      11432 (750 €).
    - À 10 % sur 1 ligne : 11438 (600 €).
  - **GTI, sur 4 lignes : 9 057,50 €.**
    - 1550 : 50 %, 3 000 € ;
    - 11554 : 25 %, 1 557,50 € ;
    - 11884 : 25 %, 3 250 € ;
    - 14171 : 25 %, 1 250 €.
  - **DENOPCE 1/2, sur 1 ligne : 22319, 50 %, 2 500 €.**
  - **Le total des parts d'apporteurs est de 29 632,50 € TTC**, sur 111 130 € de commissions TTC.
- **La 21e ligne, 22979** (FERNANDEZ 100, 9 000 € TTC), n'a pas d'apporteur. Elle est mixte, juste et protégée.
- **Ce que dit la supposition de la nuit :** 50/50, sur UN SEUL nom, des deux côtés.
  - **Sur 16 lignes**, c'est le négociateur 1 du Sheet, mis à 100 % au lieu de 75, 90 ou 50.
  - **Sur 4 lignes, c'est un autre nom que le Sheet :**
    - 1550 : un compte d'administration, quand le Sheet dit ABED 50 / GTI 50 ;
    - 10072 : Groupe GTI Firminy, quand le Sheet dit ITIM ;
    - 11554 : Groupe GTI Firminy, quand le Sheet dit CHANTUREAU ;
    - 11884 : VIVIER, quand le Sheet dit THOMAS.
- **Un fait mesuré, qui n'est pas une clé.**
  - Sur 18 des 20 lignes, la `commission_agence` du registre vaut exactement la part HT de l'apporteur.
  - Les 2 autres sont 11554 et 22319 : elle y vaut tout le HT.
  - Ce rapport n'est pas propre aux apporteurs. Sur les 3 729 ventes réglées, 184 sont à 25 % et 485 à 50 %.
  - Un reflet n'est pas une clé.
- **Les paiements aux apporteurs.** Sur 10 des 15 lignes de meilleursagents, la case de la facture dit que l'apporteur a
  été payé (« M.AGENT réglé », « meilleur agent virement ok »).
- **La liste nommée :** `notice/CLASSEUR_LES_21_VENTES_REGLEES_SUR_UNE_SUPPOSITION_ET_LEURS_APPORTEURS_2026-11-25.csv`.
  - Elle porte la chaîne, le dossier, l'ID, la ligne, ce que dit le Sheet, l'apporteur, son pourcentage, la commission
    TTC, sa part, la `commission_agence` du registre, les parts d'aujourd'hui, le règlement et la facture.
  - La supposition de 1550 y est écrite « un compte d'administration ».

### ⛔ Les trous de la vague1a, et le classement refait sur l'état d'aujourd'hui (25/11, après-midi)

> « ⛔ ARRÊTE LES VAGUES, J'AI REGARDÉ MON SHEET ET J'AI VU LES TROUS. Entre mes lignes 4 et 70 il y a 17 cases vides [...]
> ELLES SONT ÉCARTÉES PAR TON CLASSEMENT DU 19/11, QUI EST D'AVANT LA VAGUE [...] RECLASSE SUR L'ÉTAT D'AUJOURD'HUI. »
> Et : « Les 50 déjà écrites sont JUSTES [...] On ne touche pas à celles-là. »

**La cause, et elle est à moi.** L'étape `preparer` de l'outil choisit ses lignes dans un fichier de classement, par
défaut celui du 19/11 (`TEMPS5_Q8_...`). Ce fichier était d'avant la vague, et je l'ai réutilisé sans le refaire. Le juge
de l'outil relit pourtant tout à l'instant de l'écriture. Mais une ligne que le classement n'a pas choisie, le juge ne la
voit jamais : de là viennent les trous.

**Le classement neuf** (`phase2/checks/reclasser_colonne_a_apres_la_vague_2026-11-25.py`, en lecture seule).
- **Les règles sont les mêmes que le 19/11, dans le même ordre.** La première raison qui concerne une ligne la range.
- **Trois changements, que je nomme :**
  - **PATCH_V2 et CETTE_NUIT n'existent plus.** Un témoin le prouve : le gel du jour porte les 78 ajouts du patch V2 et
    aucun de ses 45 retraits.
  - **« Plusieurs dossiers » et « étiquette partagée » se lisent comme l'outil les juge à l'écriture**, sur les pièces
    effectives : c'est sa règle C5 du 19/11, où une création du Sheet ne décide pas de l'étiquette.
  - **Les cases EN_ATTENTE et AUDIT_NON_JUSTE ne sont pas levées.** Elles sont relues dans les mêmes fichiers que le
    19/11, car elles viennent de ses décisions et de l'audit.
- **Trois états, pour isoler ce que la vague a fait :**
  - **S0** est le 19/11, celui de ses nombres ;
  - **S1** applique les règles d'aujourd'hui aux chaînes d'AVANT la vague (l'image de 07:26) ;
  - **S2** les applique aux étiquettes d'aujourd'hui.
  - Le passage de S1 à S2, c'est la vague et rien d'autre, puisque le gel est le même.
- **Les témoins sont tous verts :**
  - une étiquette correspond à un dossier, avec 0 écart ;
  - mesurer par les chaînes ou par les étiquettes donne les mêmes cases, avec 0 écart ;
  - les 50 lignes écrites sont rangées VAGUE_1 si l'on ignore leur case A, et elles portent bien l'étiquette du jour (50
    sur 50) ;
  - la VAGUE_1 a 4 478 lignes et 4 478 étiquettes distinctes ;
  - l'à blanc de l'outil, qui est un juge indépendant, met en « à écrire » les 50 lignes de la vague neuve.

**① Le classement d'aujourd'hui, sur les 4 802 lignes du Sheet.**
- **Ce qui est fait ou à faire :**
  - 50 lignes déjà écrites ;
  - **4 478 lignes en VAGUE_1**, dont 17 qu'il a sorties par ses décisions du 20/11 (9 de B, 8 des 19) : l'outil les
    refuse. Il reste donc **4 461 lignes écrivables**.
- **274 lignes restent écartées :**
  - 79 SANS_LIEN, qui n'ont rien à écrire (dont 5 lignes nées depuis le 19/11) ;
  - 47 AUDIT_NON_JUSTE ;
  - 45 GEL_SEUL ;
  - 42 PLUSIEURS_DOSSIERS ;
  - 23 EN_ATTENTE ;
  - 20 LIEN_A_VALIDER ;
  - 18 ETIQUETTE_PARTAGEE.
- **Le compte se boucle :** 50 + 4 461 + 17 + 274 = 4 802.
- **Ce ne sont donc pas 48 lignes qui restent bloquées.** Le 48 ne compte que les lignes à plusieurs étiquettes.
  - Les autres raisons ne dépendent pas de la vague : pas de lien, une décision, l'audit, un lien qui ne tient qu'au gel.
  - Le « 4 670 sur 4 723 » de son contrôleur est mon « 53 par toutes les pièces » : 4 723 − 53 = 4 670. Par les pièces
    effectives (la lecture de l'outil), c'est 48.

**② Ce qui sort de sa case** (du 19/11 à maintenant, et entre parenthèses la part de la vague seule).
- **Sur les 307 « étiquette partagée », 271 passent en VAGUE_1, et la vague en libère 271.**
  - Restent 9 « partagée », 11 « plusieurs », 10 « lien à valider », 5 « audit » et 1 « gel seul ».
- **Sur les 233 « plusieurs dossiers », 175 passent en VAGUE_1, dont 97 par la vague.**
  - Les 78 autres sont libérées avant la vague, par le patch V2 et la règle des pièces effectives.
  - Restent 21 « plusieurs », 20 « gel seul », 8 « partagée », 7 « lien » et 2 « audit ».
- **Sur les 112 « lien à valider », 96 passent en VAGUE_1, et la vague n'y est pour rien** : c'est le patch de confiance
  du 22/11.
- **Ne bougent pas :** SANS_LIEN (74), EN_ATTENTE (23), AUDIT_NON_JUSTE (28) et GEL_SEUL (23).
- **Dans l'autre sens, 11 lignes en VAGUE_1 le 19/11 sont bloquées aujourd'hui** (10 « plusieurs », 1 « partagée »).
- **La vague seule libère 377 lignes et en bloque 19.**
  - Elle libère 297 « partagée » et 80 « plusieurs ».
  - Les 19 bloquées sont 10 « plusieurs » et 9 « partagée ». La vague a coupé une chaîne entre les pièces de la ligne, ou
    l'a laissée avec une autre ligne. Elles sont nommées dans le CSV (case_avant_la_vague = VAGUE_1, case_25_11 autre).
- **Le compte :** 3 997 − 11 + 542 = 4 528 lignes, soit les 4 478 et les 50 écrites.

**Les 17 trous de ses lignes 4 à 70.**
- **14 trous sont maintenant en VAGUE_1, et l'à blanc les met « à écrire ».**
- **3 trous restent bloqués :**
  - **LPBAZ1D4** (ligne 21, Annulée), PLUSIEURS_DOSSIERS : le compromis annulé 14006 est dans D2025-0219, l'offre refusée
    14008 dans D2025-0365. La vague n'y a rien changé.
  - **FYC1KCHQ** (ligne 50, Annulée), GEL_SEUL : le compromis 14010 a la date 0000-00-00, et l'offre 1001435 est une copie
    du Sheet. Aucune colonne indépendante ne retrouve le dossier sur la ligne : le lien ne tient qu'au gel.
  - **I847SPN3** (ligne 67, Offre d'achat), PLUSIEURS_DOSSIERS : trois pièces dans trois dossiers. Le compromis annulé
    3698 est dans D2022-0377, l'offre acceptée 3700 dans D2022-0626, et la vente 3701 du 21/03/2025 dans D2025-0092.

**③ Ses 4 ventes réglées sont toutes les 4 écrivables.** L'à blanc les met « à écrire ».
- **OAQDRTNC** (ligne 12, D2025-0512) était « partagée » le 19/11.
  - Sa chaîne 25626 portait aussi le compromis 25626, relié à la ligne 44ZVGG8Q.
  - **La vague les a séparées :** 25627, 25628 et 25629 forment leur propre dossier, et 44ZVGG8Q garde 25626.
- **USL9H5AJ** (ligne 61, D2025-0500) suit le même chemin : la chaîne 2357 était partagée avec 515UT1WG, et la vague a
  séparé 2358, 2359 et 2360.
- **E1QEDCAG** (ligne 51, D2025-0199) et **95WH4KUS** (ligne 68, D2025-0090) étaient « lien à valider » le 19/11.
  - Leurs liens sont « sûre » depuis le patch de confiance.
  - **Elles étaient écrivables avant même la vague.** Seul le vieux classement les a laissées dehors.

**④ La vague neuve, vague1b, n'est PAS écrite.**
- **Le fichier :** `notice/CLASSEUR_VAGUE_vague1b_2026-11-25.csv`.
  - Ce sont les 50 premières lignes de la VAGUE_1 neuve dans l'ordre du Sheet, sans ses décisions du 20/11.
  - Elle a été préparée par `preparer --source notice/CLASSEMENT_COLONNE_A_APRES_LA_VAGUE_2026-11-25.csv --colonne-case
    case_25_11 --case VAGUE_1 --ids ...`. Le code de l'outil n'a pas été modifié.
- **Son contenu :**
  - les lignes 2 et 3, qui sont au-dessus de sa plage de lignes et étaient elles aussi vides ;
  - 14 de ses 17 trous ;
  - puis les lignes 71 à 105.
  - Selon leur case du 19/11 : 31 VAGUE_1, 11 PLUSIEURS, 4 LIEN et 4 PARTAGÉE.
- **L'à blanc :** 50 à écrire, 0 sautée. L'empreinte de la vague est **9a94fb89e66a4db4**, celle de la colonne A
  **2b60fa4b312a7bc1**. Rapport : `C:\Hektor\Backups\classeur_colonne_a\2026-11-25_121342_vague1b_A_BLANC`.
- **Le bon à lire**, avec la ligne, l'ID, le dossier, la case du 19/11, l'état et l'acquéreur, est dans
  `notice/CLASSEUR_VAGUE_vague1b_2026-11-25_LE_BON_A_LIRE.txt`. Il est local seulement (ignoré par git).
- **⚠ Un piège nommé :** le défaut de `preparer --source` pointe toujours vers le classement du 19/11. Toute vague
  suivante doit passer `--source` et `--colonne-case case_25_11`. Changer ce défaut toucherait le code de l'outil :
  c'est à son mot.
- **⛔ Rien n'est écrit dans le Sheet, rien chez Hektor, pas de push.** Les 50 de la vague1a ne sont pas touchées.

### ⛔ Pourquoi l'écrivain de la colonne A n'accepte pas le verdict du protocole (25/11, après-midi)

> « POURQUOI TON ÉCRIVAIN N'ACCEPTE-T-IL PAS LE VERDICT DU PROTOCOLE ? Le protocole est MON juge [...] Soit ton écrivain a
> une RAISON [...] Soit il applique un critère PÉRIMÉ [...] MESURE-LE ET RÉPONDS-MOI, CAS PAR CAS. »

**L'outil de mesure :** `phase2/checks/colonne_a_contre_le_verdict_du_protocole_2026-11-25.py`, en lecture seule.
- **Le protocole y est lu tel qu'il est :** son socle, passage 81, sur l'image de la vague. Pour chaque ligne : TRANCHÉE
  avec ses pièces, ses preuves et l'étiquette à l'arrivée, ou ATTENTE.
- **Le croisement est reproduit à l'identique :** sur les 274 écartées, 204 sont tranchées et 70 ne le sont pas, avec la
  même répartition par case que son contrôleur.
- **La liste nommée :** `notice/COLONNE_A_LES_ECARTEES_CONTRE_LE_VERDICT_DU_PROTOCOLE_2026-11-25.csv`.

**La réponse : un critère périmé, à deux étages, et une seule raison vraie.**
- **① L'écrivain ne lit pas le protocole, il lit le GEL.**
  - Le gel (`app_classeur_lien`) est la carte des liens du 16/11, corrigée par le patch V2 du 19/11.
  - Le protocole a refait sa propre carte ligne → pièces, en gardant 12 539 liens, en en déliant 256 et en en reliant
    108, sur 324 lignes.
  - La vague a posé ses dossiers et ses étiquettes, mais **jamais ses liens** : le gel n'a pas bougé.
  - **Les deux preuves :**
    - l'étiquette à l'arrivée du protocole est l'étiquette d'aujourd'hui de ses pièces sur **4 729 lignes sur 4 729**
      (les 268 « NEUVE » sont résolues par leur pièce) : la vague a réalisé le protocole ;
    - mais le gel n'est égal aux pièces du protocole que sur 4 405 lignes. **324 lignes diffèrent.**
- **② Le classement ajoute trois portes d'avant le protocole :**
  - GEL_SEUL, qui est le juge ⑤ du 19/11 ;
  - AUDIT_NON_JUSTE, qui est l'audit du 18/11 ;
  - EN_ATTENTE, la liste figée le 19/11.
  - L'écrivain refuse aussi les liens que le gel marque « à valider » ou « bonne ». Ces marques ont été posées entre le 16
    et le 19/11 et n'ont jamais été mises à jour.
- **③ La seule raison vraie : la colonne A ne porte une étiquette que sur UNE ligne.** C'est le critère 5 de l'outil, et
  le protocole ne le vérifie pas.
  - Il met deux doubles de saisie sur un même dossier : VIALLARD (3308P0UX et YRUF0S9H) et PAOLONE (T2GZOY5O et
    O6R10ZQA).
  - Laquelle porte l'étiquette ? C'est à lui de trancher.
  - Les autres vérifications de l'écrivain servent à l'ÉCRITURE et restent nécessaires :
    - la case A doit être vide ;
    - l'ID doit être présent, une seule fois ;
    - l'étiquette du jour doit être celle qui était prévue ;
    - la mémoire doit être cohérente ;
    - les trois verrous.

**⚠ Le danger, dans l'autre sens.** En lisant le gel, l'écrivain écrirait 5 lignes contre le protocole :
- **2 avec une autre étiquette que celle du protocole :**
  - 8NZ6V6XB : le gel relie le compromis 11560, le protocole le compromis 11558 ;
  - ZV3QRSJG : le gel relie 17136, le protocole 17131.
- **3 que le protocole a laissées en ATTENTE :**
  - P252U1JH et 3THZJOOG : un compromis sans date, sorti de la règle E par sa décision ;
  - 3QZ4DAD1 : sa date tombe sur plusieurs acheteurs.
- **Aucune n'est dans les 50 écrites, ni dans la vague1b.** La vague1b reste juste au regard du protocole : 50 sur 50,
  avec la même étiquette.

**Ce que donne la mesure en suivant le protocole : 4 725 lignes écrivables**, les 50 déjà écrites comprises, contre 4 511
aujourd'hui. Cela fait **+214, et non +106.**
- **Le calcul :** 4 511 − 3 non tranchées + 199 des 204 + KT0601S6 + 17 lignes VAGUE_1 que ses décisions du 20/11
  excluent.
- **Ses décisions du 20/11 :** 28 de ces 4 725 lignes en relèvent (9 de B, 19 des 19), et toutes sont tranchées par le
  protocole. Si elles restent dehors, le total tombe à 4 697.

**① Les 59 (40 GEL_SEUL et 19 LIEN_A_VALIDER) : elles sont toutes les 59 écrivables par le protocole.**
- **Les preuves du protocole :**
  - pour les 40 GEL_SEUL : R9 sur 10, R9b sur 13, R22 sur 3, R25 sur 1, R7b sur 1, et 13 par les colonnes de la ligne ;
  - pour les 19 LIEN_A_VALIDER : 18 par les dates de la ligne, 1 par R7b/R7c.
- **Exemple complet : FYC1KCHQ** (ligne 50, Annulée, l'un de ses trous). Elle est rangée GEL_SEUL.
  - **Le gel :** compromis annulé 14010 et offre 1001435, tous deux « sûre », dans un seul dossier, D2024-0461.
  - **Le protocole :** TRANCHÉE, étiquette a387b1d4, qui est bien l'étiquette d'aujourd'hui. Sa preuve sur 14010 : règle
    R9, validée le 23/11. Le gel du 16/11 ne donne cette pièce qu'à cette ligne. Ses honoraires de 6 000 sont égaux à la
    Commission TTC de la ligne, et aucune autre ligne n'a son prix et ses honoraires. L'offre 1001435 est une copie C5 de
    la ligne : elle suit la ligne et ne décide pas.
  - **Ce que l'écrivain exige en plus :** le juge ⑤ du 19/11 veut retrouver une pièce de deux façons.
    - Avec une date : la date de la pièce doit être celle de la ligne, à un jour près, avec en plus le nom, le prix ou le
      mandat.
    - Sans date : la case du genre doit être vide, avec le mandat, le nom et le prix à 1 % près.
    - Or le compromis est daté « 0000-00-00 », et la copie n'est jamais retenue. Ce juge ne connaît ni les honoraires ni
      les règles du protocole.
  - **⇒** Le juge de l'écriture, lui, l'accepterait. Seul le classement la refuse, avec un critère du 19/11.
- **Exemple de LIEN_A_VALIDER : 7BPVD7K4** (ligne 504, Vente réglée).
  - Le gel et le protocole ont les mêmes pièces (6434, 6435, 6437). Le protocole prouve chacune par une date de la ligne :
    compromis du 07/03/2024, offre du 14/02/2024, vente fixée au 25/05/2024.
  - L'écrivain la refuse seulement parce que le gel marque son lien « à valider ».

**② Les 47 AUDIT_NON_JUSTE.**
- **De quel audit :** l'« audit indépendant du classeur » du 18/11 (`AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv`,
  350 lignes). Ses verdicts sur les 47 : FAUX 5, A_RATTACHER 23, PARTIEL 19.
- **Ce qui s'est passé depuis :**
  - Les 47 ont toutes été touchées par le patch V2 du 19/11, qui a été fait à partir de cet audit.
  - Après le V2, le gel est ce que voulait l'audit sur 35 des 47.
  - Le protocole a rejugé les 47. Il retrouve ce que voulait l'audit sur 32 lignes et pose ses propres pièces sur les 15
    autres. Les 47 sont écrivables par le protocole.
- **⇒ Ce n'est plus vrai aujourd'hui.** Le verdict « non juste » décrit le gel du 18/11, d'avant sa correction.

**③ Les deux contradictions : c'est la lecture de l'écrivain qui est fausse.**
- **Les 20 SANS_LIEN tranchées.** Le gel n'a aucun lien pour elles, le protocole en a.
  - On y trouve **ses décisions des 23 et 24/11** :
    - les 5 rattachements : 2U5QPKRC, EJN79TJ1, MQ6H8TVQ, QXDW8EQA et 91IHSGNC ;
    - 6FQO29C8, pour le bien 39845 ;
    - 4G2UHO35, pour 19814.
  - Puis ZZ5WKMWM, I3TFR2KG, D9MMB7OU, YRUF0S9H et Z6P7KE5R.
  - Enfin, **8 lignes nées après le 19/11** (les lignes 4801 à 4808, des offres de novembre 2026), que le gel n'a jamais
    reliées.
  - Ce sont les 108 liens neufs du protocole, jamais posés dans le gel. 7 sont des ventes réglées au Sheet.
  - **19 sont écrivables.** La 20e est YRUF0S9H, le double VIALLARD.
- **Les 21 EN_ATTENTE tranchées.**
  - La liste EN_ATTENTE est figée au 19/11. Elle contient les questions de l'audit du 18/11, et les opérations du V2
    marquées « SORTIE ».
  - Le protocole les a tranchées depuis. Plusieurs questions portent sur une date ou sur un ménage, pas sur le dossier.
  - **18 sont écrivables.** Les 3 autres sont des doubles : la paire PAOLONE, et 3308P0UX avec YRUF0S9H.

**④ Les 57 « à plusieurs dossiers » (42 + 15) : par les pièces du protocole, chacune a UN seul dossier.**
- **Pourquoi l'écrivain en voit plusieurs :** il voit 2 dossiers sur 41 lignes et 3 sur 1. Ce sont les pièces de trop du
  gel, les 256 déliements que le protocole n'a jamais posés. Les 15 autres sont partagées par le gel.
- **56 sont écrivables tout de suite.** KT0601S6 partage son dossier avec PPIM4947, que le protocole laisse en attente
  (« sa date tombe sur plusieurs acheteurs ») : c'est à lui.
- **Les ventes réglées : 18 au Sheet** (16 au registre). Ce sont HPNJ32UM, AOPBUAOJ, X2714E92, RF9KYWSY, SCYKLY77,
  KT0601S6, NKUNH7SY, ZR13FV3K, 50LQ2VSA, SXJDHXKF (la ligne de 8016), 1cc703d9, c08ff7cb, a5cb141f, 1cf326f1, a8b6c8cc,
  14853166, 38f13b81 et df0ce30c.
- **Sur toutes les 204,** 63 sont des ventes réglées au Sheet.

**Le piège de ce matin est traité : l'outil REFUSE un classement plus vieux que la dernière vague.**
- **Le code :** `fraicheur_du_classement`, ajouté à `ecrire_colonne_a_du_sheet_2026-11-20.py` et appelé en tête de
  `preparer`. Il n'y a aucune option pour passer outre.
- **La règle :**
  - un classement porte sa fiche de fabrication (`<csv>.json`, avec son heure et son sha256) ;
  - la dernière vague est le dernier événement qui recoupe les dossiers (fusion ou scission) au journal des étiquettes,
    lu à l'instant chez Supabase. Aujourd'hui, c'est 09:07:40. Une nuit qui fusionne compte aussi.
  - L'outil refuse un classement sans fiche, un classement modifié depuis sa fiche, ou un classement fait avant la
    dernière vague.
- **L'épreuve, sur 4 cas :**
  - le classement du 19/11, sans fiche : REFUS ;
  - le classement neuf avec sa fiche : il passe ;
  - une fiche datée de 08:00 UTC, avant la vague : REFUS ;
  - un classement retouché après sa fiche : REFUS.
- **Le classement neuf a été refait avec sa fiche**, à 13:47 heure de Paris. Il est identique, octet pour octet, à celui
  de midi.
- **⚠ L'épreuve de l'outil (`simuler`) est périmée elle aussi.** Elle donne 9 rouges, avec ou sans ma garde : la même
  liste, vérifiée en rejouant l'outil d'avant ma modification. Elle sème ses témoins sur les premières lignes VAGUE_1 du
  19/11, qui sont aujourd'hui les 50 écrites. **Elle est à refaire avant toute nouvelle écriture.**

**⛔ Rien n'est écrit dans le Sheet, rien chez Hektor, pas de push.** Les 50 de la vague1a ne sont pas touchées. La
vague1b attend.

### ⭐ On suit le protocole : l'écrivain branché sur ses pièces, le classement refait, la vague1c prête (25/11, après-midi)

> « ALORS ON SUIT LE PROTOCOLE. C'est lui mon juge [...] Refais le classement sur SES pièces, pas sur le gel. [...] GARDE
> CE TÉMOIN DANS CHAQUE VAGUE : zéro ligne écrite contre le protocole, et tu t'arrêtes si ce n'est pas zéro. [...] NE TRANCHE
> PAS SEUL : laisse les quatre lignes VIDES et nomme-les. [...] Dis-moi QUI D'AUTRE lit le gel. »

**L'écrivain juge désormais par le protocole** (`ecrire_colonne_a_du_sheet_2026-11-20.py`).
- **Le nouveau juge, `RegistreProtocole` :**
  - les pièces d'une ligne viennent du socle du protocole (passage 81, celui que la vague a réalisé) ;
  - le registre de Supabase ne donne plus que l'étiquette, l'origine et le numéro de chaque transaction, à l'instant ;
  - **le gel n'est plus lu.**
  - Une ligne que le protocole n'a pas tranchée est sautée et nommée (PAS_TRANCHEE_PAR_LE_PROTOCOLE). Toutes les étapes
    passent par lui : preparer, a_blanc, ecrire, simuler.
- **Son témoin, `contre_le_protocole`, gardé dans chaque vague :** chaque ligne à écrire doit être tranchée, et
  l'étiquette écrite doit être son étiquette à l'arrivée, qui est lue dans un autre champ du verdict que ses pièces. Le
  témoin joue trois fois :
  - **avant toute écriture :** toute la vague est jugée avant la sauvegarde et avant d'armer quoi que ce soit. Une seule
    ligne contre le protocole, et **rien ne s'écrit** (refus, code 3). À blanc : rouge, code 1, la ligne nommée ;
  - **avant chaque paquet :** il est relu à l'instant ;
  - **après l'écriture :** c'est le critère ⑥, « zéro ligne écrite contre le protocole ».
- **Le défaut de `preparer`** est maintenant le classement par le protocole, et la garde de fraîcheur reste en tête.

**① Le classement sur les pièces du protocole** (`classer_colonne_a_par_le_protocole_2026-11-25.py`, en lecture seule).
- **Le fichier :** `notice/CLASSEMENT_COLONNE_A_PAR_LE_PROTOCOLE_2026-11-25.csv` et sa fiche de fabrication (13:12:15 UTC).
- **La répartition des 4 802 lignes :**
  - **4 647 en VAGUE_1** ;
  - 50 déjà écrites ;
  - 73 pas tranchées (dont 58 « rien à étiqueter ») ;
  - **4 doubles de saisie** ;
  - 9 lignes de sa décision B et 19 de ses 19.
- **Les lignes écrivables :** 4 697 sans ses 28 décisions (50 écrites + 4 647), et 4 725 avec elles.
- **Par rapport au classement par le gel de midi :** 189 lignes deviennent écrivables, dont **62 ventes réglées** au Sheet.
  3 lignes en sortent, celles que le protocole n'a pas tranchées.
- **Les témoins, tous verts :**
  - l'étiquette à l'arrivée est celle d'aujourd'hui, 4 729 sur 4 729 ;
  - les 50 cases écrites portent l'étiquette du protocole, 50 sur 50 ;
  - la VAGUE_1 a 4 647 étiquettes distinctes, et aucune n'est déjà en A ;
  - les 5 lignes du danger inverse sont à leur place ;
  - les 4 doubles sont nommés ;
  - les totaux 4 725 et 4 697 sont retrouvés.
- **⚠ Une correction :** le danger inverse portait sur **4 lignes, et non 5**. 8NZ6V6XB est l'une de ses 19 décisions du
  20/11 : l'écrivain la refusait déjà.
- **Ses doubles de saisie, laissés VIDES et nommés :**
  - VIALLARD : 3308P0UX et YRUF0S9H, dossier D2022-0644 ;
  - PAOLONE : T2GZOY5O et O6R10ZQA, dossier D2021-0797.
  - L'écrivain les saute de lui-même (ÉTIQUETTE_PARTAGEE : « le dossier porte aussi... »). Laquelle garder, c'est à lui.

**L'épreuve de l'outil (`simuler`) : 38 verdicts, 0 rouge.** Aucun POST n'est parti, et elle a tourné sur 228 lignes
nominales dont la case A était vide.
- **Les témoins neufs :**
  - une ligne réelle non tranchée est glissée dans la vague : elle est sautée, PAS_TRANCHEE (CQGLHH2X) ;
  - le double VIALLARD est vu comme partagé ;
  - PLUSIEURS_DOSSIERS est semé, car aucune ligne réelle ne le montre plus sur les pièces du protocole ;
  - le témoin positif C5 est semé : une copie mise dans un autre dossier, et la ligne s'écrit quand même.
- **Le scénario D (son témoin) :**
  - sans graine, les 3 lignes s'écriraient ;
  - avec la graine, l'à blanc est rouge et nomme L31D0YNA ;
  - l'écriture est refusée en entier : 0 POST, mémoire vide, colonne A inchangée.

**② La vague suivante, vague1c : 50 lignes, PAS écrite.**
- **Le fichier :** `notice/CLASSEUR_VAGUE_vague1c_2026-11-25.csv`, préparé sur le classement par le protocole.
- **L'à blanc :** 50 à écrire, 0 sautée, **0 contre le protocole**. L'empreinte de la vague est **097355f07e338848**,
  celle de la colonne A **2b60fa4b312a7bc1**. Rapport : `C:\Hektor\Backups\classeur_colonne_a\2026-11-25_141523_vague1c_A_BLANC`.
- **Son contenu :**
  - les lignes 2 et 3 ;
  - **ses 17 trous des lignes 4 à 70, tous**, y compris les 3 que le gel bloquait : LPBAZ1D4 (D2025-0219), FYC1KCHQ
    (D2024-0461) et I847SPN3 (D2022-0352, le dossier du protocole) ;
  - puis les lignes 71 à 101, dont LTJYTEVC, elle aussi débloquée par le protocole.
  - On y compte 33 ventes réglées. 46 lignes étaient déjà dans la vague1b, qui est remplacée.
- **Le bon à lire,** avec la ligne, l'ID, le dossier, l'état, la case par le gel et l'acquéreur, est dans
  `notice/CLASSEUR_VAGUE_vague1c_2026-11-25_LE_BON_A_LIRE.txt`. Il est local seulement.

**④ Qui d'autre lit le gel ? Mesuré dans le code, dans la base et dans le moniteur.**
- **La nuit : rien ne le lit.** Aucun script du run ne le lit. La descente se contente de le copier dans la base locale.
- **Les écrans : rien.** Le front ne lit ni le gel ni ses vues.
- **La base :** aucune fonction ne le lit ni ne l'écrit. Deux vues le lisent, et le **moniteur** les surveille :
  - **`data.classeur_lien_casse`** (critique, seuil 0) contrôle qu'un lien pointe une transaction qui existe. Aujourd'hui :
    0 DISPARUE et 6 ABSENTE_CHEZ_HEKTOR, connues. C'est un contrôle d'intégrité, pas de justesse : **il n'est pas
    touché.**
  - **`data.classeur_ligne_sans_lien`** (avertissement, seuil 92, il donne 71) compte les lignes sans lien DANS LE GEL.
    **Elle porte le même défaut, en petit :**
    - le protocole a relié 19 de ces lignes ;
    - sa table des lignes (`app_classeur_ligne_id`, 4 794 lignes) ne connaît pas les 8 lignes les plus récentes du Sheet.
- **Le protocole lui-même lit le gel, et c'est voulu.** Il s'en sert comme d'une **pièce à conviction** (R9 : « le gel du
  16/11 ne la donne qu'à cette ligne »). **⛔ Réécrire le gel en place changerait donc la preuve du protocole.**
- **Les autres outils du chantier qui le lisent** sont des outils d'un seul passage, du 16 au 22/11, et ne tournent plus.
  L'écrivain ne le lit plus depuis aujourd'hui.
- **Le même défaut ailleurs, oui : les valeurs posées une fois à partir du gel, les 16 et 17/11** (ventes réglées et
  factures, dates d'annulation, commissions).
  - **Sur les 256 liens que le protocole délie, 0 valeur n'est mal placée.**
    - 56 pièces portent une valeur posée depuis le classeur.
    - 55 de ces valeurs viennent de la ligne dont le protocole garde le dossier (la pièce y est « à part », mais dans le
      même dossier).
    - La 56e (27134) a été posée aujourd'hui depuis la bonne ligne, IEYXREWQ.
  - **Sur les 108 liens que le protocole relie, 47 valeurs du Sheet n'ont JAMAIS été posées** :
    - **17 ventes réglées sur des chaînes que le registre ne dit PAS réglées**, dont ses rattachements 2U5QPKRC et
      91IHSGNC, et 6FQO29C8 ;
    - 1 vente réglée sur une chaîne déjà réglée par une autre pièce ;
    - **29 dates d'annulation**, dont 6U5DQQ4J, l'une des 2 antérieures qu'il a écartées : elle reste écartée.
  - Les avis, les notes, les conditions et les parts ne sont pas concernés : A1, A3 et A2 les ont réalignés par pièces
    pendant la vague.
- **Ce qui suit, à son mot :**
  - ne pas réécrire le gel ;
  - mettre ses lecteurs sur le protocole : l'écrivain (c'est fait), la sentinelle (à faire) ;
  - poser depuis le protocole les 47 valeurs qui manquent, moins les écartées.

**⛔ Rien n'est écrit dans le Sheet, rien chez Hektor, pas de push.** Les 50 de la vague1a ne sont pas touchées.

### La vague1c ÉCRITE (25/11, 14:44, son accord) ; la sentinelle avec le protocole ; les 47 rangées, rien posé

> « ⭐ OUI, ÉCRIS LA VAGUE1C. Empreintes 097355f07e338848 et 2b60fa4b312a7bc1. [...] ⛔ Puis tu t'arrêtes, je regarde mon
> Sheet, et on continue. »

**L'écriture.** L'interrupteur a été donné à la commande seule : il n'est dans aucun `.env`, vérifié avant.
- **Le résultat :** sortie 0 ; **50 écrites, 0 sautée, 0 contre le protocole.**
- **Les 6 critères de l'outil sont verts**, dont le nouveau ⑥, « zéro ligne écrite contre le protocole ».
- **La sauvegarde et le rapport** sont dans `C:\Hektor\Backups\classeur_colonne_a\2026-11-25_144420_vague1c_ECRIRE`.

**Ma relecture indépendante.** Le Sheet a été relu par `apparier_classeur`, le protocole par son socle, et les étiquettes
par SQL : aucun de ces chemins ne passe par l'outil.
- 4 802 lignes ; **100 cases A remplies, exactement les deux vagues** ; 0 hors des vagues ; 0 ID en double ; 0 étiquette
  sur deux lignes.
- **La vague1c : 50 sur 50.** Chaque ligne est tranchée, et sa case A est à la fois le dossier de SES pièces, l'étiquette
  à l'arrivée et l'étiquette prévue.
- **La vague1a est toujours en place**, 50 sur 50.
- Les lignes sont aux mêmes places qu'à la préparation (lignes 2 à 101).
- **Ses 3 lignes que le gel bloquait** sont écrites : LPBAZ1D4 (ligne 21), FYC1KCHQ (ligne 50) et I847SPN3 (ligne 67).
- **Ses 4 doubles sont toujours vides.**
- ⛔ **ARRÊT :** la vague suivante attend qu'il ait regardé son Sheet.

**La sentinelle `data.classeur_ligne_sans_lien`, avec le protocole : 73 et non 52.**
- **Aujourd'hui elle compte 71, mais à tort sur 26 lignes :**
  - **12 lignes qu'elle compte et que le protocole rattache :** ses 5 rattachements, 6FQO29C8, 4G2UHO35, ZZ5WKMWM,
    I3TFR2KG, D9MMB7OU, YRUF0S9H et Z6P7KE5R ;
  - **14 lignes qu'elle ne compte pas,** parce que le gel les relie, alors que le protocole ne leur donne aucune pièce ;
  - et sa table des lignes ignore les 8 lignes les plus récentes, toutes tranchées.
- **Par le protocole, 73 lignes du Sheet n'ont aucune pièce :**
  - **58 « rien à étiqueter »** : c'est un verdict du protocole, ces lignes sont vides à juste titre ;
  - **15 impossibles** : 3QZ4DAD1, 3THZJOOG, 6684bcf1, 9B7U8221, 9Q0FHAKK, BR8ZTN5F, C0HXVVCW, HUY49KEC, M2G1Z1K8,
    P252U1JH, PEE1XTR8, PPIM4947, SHN6RKDI, XBR8QD6L et d2108609.
- **⇒** Avec un seuil de 92, elle ne crierait jamais. **La proposition :**
  - déclarer les 58 « rien à étiqueter », car ce verdict est une décision ;
  - compter les 15, **avec un seuil de 15**, qui doit baisser à mesure qu'il tranche les impossibles.
- **La réparation demandera trois gestes en base ou dans le moniteur, à son accord. Rien n'est fait :**
  - poser le verdict du protocole dans une table chez Supabase ;
  - redéfinir la vue pour qu'elle lise cette table ;
  - remettre à jour la table des lignes (+8) et le seuil dans `check_gti_health.py`.

**Les 47 valeurs jamais posées, rangées par ce qu'elles valent. ⛔ RIEN N'EST POSÉ.**
- **L'outil :** `phase2/checks/les_47_valeurs_jamais_posees_2026-11-25.py`, en lecture seule. **La liste :**
  `notice/CLASSEUR_LES_47_VALEURS_JAMAIS_POSEES_2026-11-25.csv`.
- **Le registre n'est pas en désaccord avec le Sheet : il est MUET.** La valeur n'a jamais été posée, parce que le gel ne
  reliait pas la pièce à sa ligne. Aucun des deux ne « se trompe » sur le règlement.
- **Les ventes réglées : 17 sur des dossiers non réglés, plus 1 sur un dossier déjà réglé, soit 162 000 € TTC de
  commissions.**
  - **Les preuves lues pour chacune :**
    - au Sheet : l'état, la date de règlement, la facture, la Commission TTC et le Prix ;
    - chez Hektor : la pièce de vente, sa date, son montant et ses honoraires.
  - **Sur les 18, la vente existe chez Hektor et elle est datée AVANT le règlement.** Les honoraires de Hektor sont égaux
    à la Commission TTC sur 16 lignes, et 17 lignes ont un numéro de facture.
  - **8 vraies ventes réglées, où tout concorde :**
    - a6d41ca1 (16 000) ; 8f3a4326 (14 000) ; a56ce827 (12 000) ; 84c91bb8 (11 000) ;
    - AYIHPHF5 (7 000) ; d9a0630c (7 000) ; ef08b63a (7 000) ; LWZL8V5M (2 000).
  - **7 vraies ventes réglées, dont seule la case « Prix » du Sheet est fautive** (« NON TROUVÉ » ou « 42 »). Les
    honoraires, la facture et les dates concordent :
    - QXDW8EQA (39 000, vente de 1 358 840 €) ; EJN79TJ1 (13 000) ; 2U5QPKRC (6 800) ; 6FQO29C8 (6 000) ;
    - I3TFR2KG (6 000) ; 91IHSGNC (4 900) ;
    - MQ6H8TVQ (1 000), **sans numéro de facture au Sheet.**
  - **2 avec un écart d'honoraires :**
    - df0ce30c (5 000 au Sheet, **0 chez Hektor**) ;
    - 78bb247a (2 500 au Sheet, 2 700 chez Hektor).
  - **1 sur un dossier DÉJÀ réglé par une autre pièce :** G8YSAI5Z (1 800, D2025-0035). Ce serait un second règlement
    sur le même dossier.
- **Les 29 dates d'annulation :**
  - **23 posables selon sa règle** (la date du Sheet sur SON compromis) ;
  - 1 qui attend sa décision : O6R10ZQA, son double PAOLONE ;
  - **3 annulées AVANT leur compromis** (LKBO1TOH, 87QOXR64, 8NZ6V6XB) : sa règle les écarte ;
  - 2 qu'il a déjà écartées (S3HOG6UL, 6U5DQQ4J).
- **À traiter quand la colonne A sera finie,** c'est son mot : le dernier morceau du chantier.

**La règle est gravée dans la mémoire.** Une source que le juge lit comme PREUVE ne se réécrit pas avec son verdict : on
fait passer ses LECTEURS au verdict (le fichier `une-preuve-du-juge-ne-se-reecrit-pas-on-fait-passer-ses-lecteurs.md`).

**⛔ Rien chez Hektor, pas de push.** Le gel est intact.

### ⛔ Le juge a-t-il changé ? Le passage 81 rejoué (25/11, 14:51-15:00) — arrêt avant la vague de 500

> « TU VIENS DE MODIFIER protocole_classeur.py -- LE JUGE LUI-MÊME. Dis-moi quoi et pourquoi [...] Je veux savoir si ta
> retouche change UN SEUL verdict du passage 81. [...] Si elle en change un, tu t'arrêtes et on regarde avant la vague
> suivante. »

**Il n'y a pas eu de retouche du juge. C'est mesuré :**
- `protocole_classeur.py` est inchangé depuis le commit 38f8d83 (24/11, 08:41). Sa date de fichier est le 24/11 à 08:03,
  et l'arbre de travail est propre ;
- l'empreinte que le juge calcule sur son propre code (`md5_code`, qui couvre aussi ses deux modules) vaut aujourd'hui
  **b47f603b**. C'est exactement celle qu'a enregistrée l'image de 07:26, sur laquelle le passage 81 a jugé.

**Mais en rejouant le passage 81 avec le code d'aujourd'hui, 2 verdicts changent.** Le rejeu a porté sur la même image,
avec le même code, et sur une copie du socle (`rejouer_le_passage_81_sur_copie_2026-11-25.py`).
- **Les 4 800 autres lignes sont identiques :** même verdict, même étiquette, même motif, mêmes pièces, mêmes preuves.
- **Les 2 lignes qui changent :**
  - **P252U1JH** : en ATTENTE au 81 (pièce sans date invisible), TRANCHÉE au rejeu (pièces 4126 et 4128) ;
  - **d2108609** : même chose, avec les pièces 21520 et 1001495.
- **La cause est prouvée.** Le juge lit EN DIRECT la liste `EXCLUES_DE_LA_REGLE_E` de `phase2/sync/affaire_ledger.py`.
  Ce fichier n'entre pas dans son empreinte.
  - La vague de 09:02 a retiré 4126 et 21520 de cette liste, avec son accord : la sauvegarde de 09:02 la donnait comme
    [4126, 4496, 4720, 21520, 26613] ; elle est aujourd'hui [4496, 4720, 26613].
  - Ce n'est pas un changement de code : c'est une entrée du juge que la vague a posée, et que son empreinte ne voit pas.
- **Pour les lignes écrites, rien ne change.** Aucune des 2 n'est écrite, ni prévue : sous le 81, l'écrivain les saute
  (PAS_TRANCHÉE). Les 100 lignes écrites et toute la VAGUE_1 ont le même verdict aujourd'hui.

**⛔ Mon erreur, réparée.**
- **Ce qui s'est passé :** la 1re version du rejeu ne détournait que `P.DOSSIER`. Or `socle()` ouvre `P.SOCLE`, une
  constante fixée à l'import. Le passage 82 s'est donc écrit dans le VRAI socle : 1 passage, 4 802 verdicts, 825 témoins.
  Sa comparaison mettait le 81 face à lui-même, et ne valait rien.
- **Qui l'a vu :** le témoin du script lui-même (« le VRAI socle : date et empreinte CHANGÉES » → ARRÊT).
- **Ce que j'ai mesuré avant de réparer :**
  - le passage 81 du vrai socle est identique, ligne pour ligne, à la copie prise juste avant le rejeu (4 802 sur 4 802) ;
  - toutes les tables sont identiques à cette copie, au passage 82 près.
- **La remise :**
  - j'ai d'abord gardé l'état pollué en sauvegarde datée
    (`prepa_25_11/socle_AVEC_LE_PASSAGE_82_ECRIT_PAR_ERREUR_20261125_145312.sqlite`) ;
  - puis j'ai remis le socle depuis la copie d'avant le rejeu. Son empreinte est **b23e2b3a**, identique à la copie ; sa
    date est 07:26:47 ; il compte 81 passages et 0 ligne du 82.
- **Le rejeu a été corrigé** (`P.SOCLE` vise aussi la copie) et rejoué sur une vraie copie. Il retrouve les mêmes 2
  lignes, et le vrai socle reste **inchangé**.
- C'est la même leçon que l'arrêt de 08:09 : une copie se prouve copie, et CHAQUE chemin doit être détourné.

**⛔ Arrêt, selon sa règle :** un verdict changerait au rejeu. **La vague de 500 n'est pas préparée.**
- **Ce qui est à lui :**
  - continuer sur le passage 81, les 2 lignes restant vides et nommées ;
  - ou d'abord un passage officiel après la vague, puis le classement et la vague de 500 sur ce passage.
- **Une lacune nommée :** l'empreinte du juge (`md5_code`) devrait couvrir aussi la liste E qu'il lit. C'est un
  changement du juge, donc à son mot.

### On reste sur le passage 81 ; la vague de 500 prête ; le juge voit enfin ses entrées ; le socle verrouillé (25/11, fin d'après-midi)

> « ON RESTE SUR LE PASSAGE 81 [...] Une seule [référence], et c'est le 81. [...] PRÉPARE LA VAGUE DE 500. [...] fais entrer
> dans l'empreinte du juge TOUTES ses entrées vivantes [...] dis-moi si le passage 81 avait d'autres entrées de ce genre qui
> ont bougé depuis ce matin [...] Fais qu'un rejeu sur copie ne PUISSE PLUS écrire dans le vrai socle, même par erreur. »

**La vague de 500, vague1d : préparée sur le passage 81, PAS écrite.**
- **Le classement a d'abord été refait** après la vague1c : 100 cases A remplies, 4 597 lignes en VAGUE_1, tous les
  témoins verts, une fiche de fabrication neuve.
- **L'à blanc :** 5 paquets de 100, **500 à écrire, 0 sautée, 0 contre le protocole.** L'empreinte de la vague est
  **a766058b78083c2a**, celle de la colonne A **8c7f1f6afe33a075**.
  - Fichier : `notice/CLASSEUR_VAGUE_vague1d_2026-11-25.csv`.
  - Rapport : `C:\Hektor\Backups\classeur_colonne_a\2026-11-25_151054_vague1d_A_BLANC`.
- **Son contenu :**
  - les lignes 102 à 604, avec 500 étiquettes distinctes ;
  - **489 ventes réglées**, 10 annulées et 1 vente prévue ;
  - 15 lignes que seul le protocole débloque.
- **Ce qu'elle laisse dehors :** aucun de ses 4 doubles, aucune non tranchée, aucune de ses décisions du 20/11. Dans la
  plage, 3 lignes ne sont pas prises, parce que le protocole ne les a pas tranchées : CQGLHH2X (ligne 162), 53ZS73KW (227)
  et 9Q0FHAKK (286). P252U1JH et d2108609 restent vides et nommées.
- **Le bon à lire** est dans `notice/CLASSEUR_VAGUE_vague1d_2026-11-25_LE_BON_A_LIRE.txt` (local seulement).

**De quoi dépend un verdict : l'inventaire de toutes les lectures du juge pendant un passage.** Il couvre
`protocole_classeur.py`, `coupe_preuve_interne.py` et `piece_copie_ou_vraie.py`.
- **L'image** (sheet.json, registre.sqlite, gel.json, t6_photo.json) : son empreinte est déjà au manifeste.
- **Le code** (les 3 fichiers) : `md5_code()`.
- **Trois entrées lues au moment de juger, qui étaient HORS de l'empreinte :**
  - ① **la liste `EXCLUES_DE_LA_REGLE_E`** de `phase2/sync/affaire_ledger.py`. Elle a bougé à 09:02 avec la vague (4126 et
    21520 retirés) ;
  - ② **« ses 20 à part »** (`a20` de `v3_calcul.json`). Elle n'a pas bougé : le fichier date du 22/11 à 07:17 ;
  - ③ **les mandants de R16** (`mandants_des_biens_2026-11-23.json`). Ils n'ont pas bougé, et le code les gardait déjà par
    leur md5.
- `temoins.json` et les trois CSV du 19 au 22/11 ne servent qu'aux TÉMOINS du passage, jamais aux verdicts.

**Le passage 81 n'avait pas d'autre entrée qui ait bougé : seule la liste E. Son état est RECONSTITUÉ.**
- **La liste E de 07:26 est connue par deux sources, identiques :** la sauvegarde de la vague (09:02, avant sa
  modification), et le dépôt au parent du commit de la pose (35fa604^). Les deux donnent [4126, 4496, 4720, 21520,
  26613].
- **Le rejeu avec cette liste, sur une copie, rend les 4 802 verdicts du 81 à l'identique**, et les 825 lignes de témoin
  aussi.
- **Le rejeu avec la liste d'aujourd'hui** ne change que P252U1JH et d2108609.
- **Les entrées reconstituées du 81 :**
  `notice/PROTOCOLE_PASSAGE_81_SES_ENTREES_VIVANTES_RECONSTITUEES_2026-11-25.json`, avec une copie à côté du socle.
- **⇒ Ses 100 lignes ont été jugées sur un état que l'on sait reconstituer, et qui l'est.**

**Le juge, v22 : je l'ai modifié sur son ordre. Aucune règle de jugement ne change.**
- **Ce qui est ajouté :**
  - `entrees_vivantes()` et `empreinte_du_juge()` : l'empreinte porte sur ce que le juge UTILISE (la liste E, et non tout
    le module), lu par les mêmes fonctions que le jugement ;
  - chaque passage écrit désormais `entrees_passage_<n>.json` à côté du socle (son schéma n'est pas touché) ;
  - le garde `SOCLES_INTERDITS` ;
  - la VERSION v22.
- **Le code passe de b47f603b à 4039688c.**
- **La preuve qu'aucune règle ne change :** le rejeu v22 avec les entrées du 81 rend les 4 802 verdicts identiques.
- **La preuve que la lacune est fermée :** l'empreinte du juge vaut d34413f8 avec les entrées du 81, et 271df49b avec
  celles d'aujourd'hui. **Elle bouge exactement quand la liste E bouge.**

**Un rejeu sur copie ne peut plus écrire dans le vrai socle. Le verrou a deux étages, et chacun est éprouvé à chaque
rejeu :**
- **dans le juge :** le vrai socle est inscrit dans `SOCLES_INTERDITS`, et `socle()` refuse de l'ouvrir. Le témoin essaie
  de l'ouvrir : « INTERDIT à ce processus » ;
- **sur le disque :** le vrai fichier est en lecture seule pendant tout le rejeu, puis rendu. Le témoin du mécanisme, sur
  une copie jetable, répond « attempt to write a readonly database ».
- **Le témoin de fin :** le vrai socle garde son empreinte (b23e2b3a) et sa date (07:26:47), avant et après chacun des 2
  rejeux.
- ⚠ **Un premier essai a échoué sans rien jouer :** une connexion restée ouverte empêchait d'effacer la copie jetable. Le
  vrai socle n'avait pas été touché. C'est corrigé.

**⛔ Rien n'est écrit dans le Sheet, rien chez Hektor, pas de push.** Les 47 valeurs restent rangées, sans rien poser. La
sentinelle viendra après la colonne A.
