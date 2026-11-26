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

### La vague1d ÉCRITE : 500 lignes (25/11, 15:33, son accord) ; les 500 relues contre le protocole ; 600 cases — arrêt

> « ⭐ VAS-Y, ÉCRIS LA VAGUE1D. Empreintes a766058b78083c2a et 8c7f1f6afe33a075. [...] FAIS-LE TOI, ET RENDS-MOI LE CHIFFRE :
> sur les 500, combien ont leur étiquette ÉGALE au dossier de leurs pièces du protocole, et combien de dossiers distincts.
> [...] je veux les 500, pas 125. ⛔ Et tu t'arrêtes après. »

**L'écriture.** L'interrupteur a été donné à la commande seule : il n'est dans aucun `.env`, vérifié avant. L'heure était
15:33, hors de la fenêtre de la nuit.
- **Le résultat :** sortie 0 ; 5 paquets de 100, chacun relu juste après son écriture (100 sur 100 à chaque fois) ;
  **500 écrites, 0 sautée, 0 contre le protocole.**
- **Les 6 critères de l'outil sont verts.**
- **La sauvegarde et le rapport :** `C:\Hektor\Backups\classeur_colonne_a\2026-11-25_153343_vague1d_ECRIRE`.

**Sa demande : les 500 relues une par une contre le protocole, par un autre chemin que l'écrivain.**
- **L'outil :** `phase2/checks/relire_la_colonne_a_contre_le_protocole_2026-11-25.py`, en lecture seule. Il lit le Sheet
  par `apparier_classeur`, le verdict par le socle (passage 81) et les étiquettes par SQL direct.
- **Pour chaque ligne, il exige :**
  - qu'elle soit tranchée ;
  - que le dossier de SES pièces (effectives) soit à la fois la case A, l'étiquette à l'arrivée et l'étiquette du fichier.
- **La vague1d : 500 lignes justes sur 500, 0 fausse, 500 dossiers distincts, 0 à plusieurs dossiers.** Elle compte 489
  ventes réglées au Sheet, et toutes ses lignes sont à leur place de la préparation.
- **La vague1a et la vague1c :** toujours 50 sur 50 chacune, 50 dossiers distincts chacune.
- **La colonne entière :**
  - **600 cases A remplies, exactement les trois vagues** ;
  - 0 case hors des vagues, 0 manquante, 0 étiquette sur deux lignes ;
  - 0 ligne non tranchée par le protocole dont la case est remplie ;
  - ses 4 doubles, P252U1JH et d2108609 sont VIDES.

**⛔ ARRÊT :** 600 lignes sont écrites. La suite attend qu'il ait regardé son Sheet. Rien chez Hektor, pas de push.

### Ses décisions du 20/11 au passage 81 ; la vente de 9Q0FHAKK ; la vague de 2 000 prête (25/11, soir) — RIEN ÉCRIT

> « MA DÉCISION DU 20/11 SUR LES 19 EST DEVENUE INUTILE [...] MESURE D'ABORD, PUIS JE LÈVE [...] FAIS LE MÊME TEST SUR MES 9
> DE LA DÉCISION B [...] 9Q0FHAKK : SA VENTE EXISTE [...] RIEN NE S'ÉCRIT SUR TOUT ÇA. Finis d'abord la colonne A [...] »

L'outil de mesure : `phase2/checks/mesurer_ses_decisions_du_20_11_et_9q0fhakk_2026-11-25.py`, en lecture seule.

**① Les 19 de sa décision du 20/11 : 19 sur 19 sont TRANCHÉES au passage 81.** Chacune a un seul dossier, porte
l'étiquette du 81, est seule sur son dossier, et son étiquette n'est pas déjà dans la colonne A.
- **5 portent une vente réglée :** TL9AFW0O (D2023-0585), RF9KYWSY (D2022-0672), 3250892d (D2025-0295), 87eb399e
  (D2026-0033) et 0bc98552 (D2026-0049).
  - Leurs pièces sont exactement celles qu'a vues son contrôleur : sans les doublons 21803/21805, 25699 et 998, et sans
    les compromis de BELMONT (4370) et de SCIORTINO (24380).
- **Les 14 autres** sont des annulées sans vente, chacune avec son propre dossier. Elles comprennent les 2 lignes que
  BELMONT et SCIORTINO tiennent désormais : FWCFAN6O (4370) et 9KHYVR1M (24380).
- **L'inverse : 0.**
  - L'écrivain n'écrit que des cases VIDES : il n'écrase jamais.
  - 0 étiquette des 19 n'est déjà dans la colonne A, et aucune n'est partagée avec une autre ligne tranchée.
  - Les remettre dans une vague ne change donc l'étiquette d'aucune ligne déjà écrite.

**② Les 9 de sa décision B : 9 sur 9 ont pour étiquette prévue celle de LEUR VENTE.**
- **Le passage 81, après la vague, a fait ce que G2 devait faire :**
  - chaque ligne tient sa vente, réglée : WG8CG5T2 → D2020-0638 (vente 22273), R9ANL92S → D2020-0615, SA7DWYEZ →
    D2020-0660, ANHQ1PK7 → D2019-0655, MFMR0U6A → D2019-0665, V5NJER40 → D2019-0661, JBCC1KBT → D2019-0664, A6OS2TTJ →
    D2019-0659, QL70KV8I → D2018-0537 ;
  - la tentative ratée garde, de son côté, l'étiquette d'avant G2 (pour WG8CG5T2 : 22269 et 22272 sous aec7c50b).
- **⇒ G2 n'a plus d'objet pour elles.**

**③ 9Q0FHAKK (ligne 286, 18 000 €) : j'arrive au même endroit que lui, plus une pièce.**
- **Le protocole l'a mise en ATTENTE** (AUCUNE_PIÈCE_PROUVÉE : « bien 5617 : 3 pièces jugées, aucune pour elle »). Il a
  cherché sur le bien du mandat 17253, qui est l'annonce 5617 (VA31338) et une autre affaire :
  - PAGÈS EYRAUD, offre du 04/10/2024 et compromis du 22/10/2024 ;
  - vente réglée le 11/02/2025, facture GGTI00003900, 7 800 € ;
  - cette affaire est tenue par 7W7XUBPO.
- **Sa vente est sur l'annonce 8395 (VM68160, mandat 17010).** Quatre colonnes de sa ligne tombent au jour près sur ses
  pièces :
  - **l'offre du Sheet, 23/08/24,** est la proposition de l'offre **3648** (POTTIER, 460 000) ;
  - **le compromis, 11/09/2024,** est le **3647** (SOUCHON, 460 000) ;
  - **la vente fixée, 22/01/2025,** est la vente **3650** ;
  - **la Commission TTC, 18 000 €,** est égale aux honoraires de 3647 et de 3650.
- **3647 et 3650 forment la chaîne 3647 (D2024-0511), tenue par PERSONNE**, ni au 81 ni au gel.
- **Ce qui ne colle pas :**
  - le Mandat (17253) et le Prix (112 800) ;
  - mais 112 800 figure sur **8 lignes** du Sheet : ce n'est pas un prix qui prouve.
- **L'audit du 18/11 l'avait déjà vu :** A_RATTACHER, avec l'offre 3648, le compromis 3647 et la vente 3650, et une
  question : « POTTIER et SOUCHON forment-ils le même ménage acquéreur ? ».
- **La chaîne 3648 : c'est l'offre de SA ligne,** du 23/08/2024, au nom de POTTIER.
  - La date du « 11/11/2026 » est celle de NOTRE geste des 11 et 12/11, qui a réécrit la colonne `date` de 1 205 offres.
    Le protocole lit la vraie date dans les propositions.
  - Elle est seule dans sa chaîne parce que son acquéreur (POTTIER) n'est pas celui du compromis et de la vente
    (SOUCHON).
- **La réparation proposée, à sa décision, RIEN FAIT :**
  - une décision de rattachement dans le protocole, comme ses 5 du 23/11 : 9Q0FHAKK ← 3647 + 3650, étiquette D2024-0511.
    L'offre 3648 reste « à part, sans effet sur l'étiquette », sauf s'il dit que POTTIER et SOUCHON sont un seul ménage ;
  - puis un passage officiel, « plus tard, avec les autres restes » ;
  - puis les 2 valeurs sur la vente 3650 : réglée le 24/01/2025, facture GGTI00003842.
  - **⚠ Elles ne sont PAS dans mes 47.** Les 47 ne portent que sur des lignes tranchées, et 9Q0FHAKK ne l'est pas. Ce
    seront la 48e et la 49e.
  - Son Mandat au Sheet (17253 au lieu de 17010) est à corriger par lui : l'écrivain ne touche que la colonne A.

**④ La vague de 2 000, vague1e : préparée, PAS écrite.**
- **Le classement a été refait d'abord :** 600 cases A, 4 097 lignes en VAGUE_1, tous les témoins verts, une fiche neuve.
- **L'à blanc :** 20 paquets de 100, **2 000 à écrire, 0 sautée, 0 contre le protocole.** L'empreinte de la vague est
  **642d0fe875a76243**, celle de la colonne A **80f0b162fa7dba57**.
  - Rapport : `C:\Hektor\Backups\classeur_colonne_a\2026-11-25_174523_vague1e_A_BLANC`.
- **Ma vérification par un autre chemin :** 2 000 sur 2 000 ont une étiquette prévue égale au dossier de SES pièces du
  protocole, et à l'étiquette à l'arrivée. Les 2 000 étiquettes sont distinctes.
- **Son contenu :** les lignes 605 à 2611, soit **1 998 ventes réglées**, 1 vente prévue et 1 annulée. 22 de ces lignes
  ne s'écrivent que grâce au protocole.
- **Ce qu'elle laisse dans la plage : 7 lignes.**
  - 4 de sa décision B : WG8CG5T2, R9ANL92S, SA7DWYEZ et ANHQ1PK7 ;
  - 2 de ses 19 : TL9AFW0O et RF9KYWSY ;
  - 1 non tranchée : PEE1XTR8.
- **Après cette vague, il restera 2 097 lignes en VAGUE_1.**
- **Le bon à lire :** `notice/CLASSEUR_VAGUE_vague1e_2026-11-25_LE_BON_A_LIRE.txt` (local seulement).
- **Lever ses décisions** demande de retirer leurs listes de l'écrivain (la décision B est écrite dans son code, les 19
  dans un fichier). C'est un changement, donc à son mot. Les 6 lignes de la plage pourront alors partir dans une vague
  suivante.

**⛔ Rien n'est écrit dans le Sheet, rien chez Hektor, pas de push.**

### La vague1e ÉCRITE : 2 000 lignes (25/11, 19:24, son accord) ; 2 600 cases ; ses trois « paires partagées »

> « Accord pour la vague de 2 000. [...] donne-moi ton chiffre d'étiquettes écrites à la fin [...] Trois des lignes sorties
> partagent leur dossier avec une AUTRE ligne du Sheet [...] Ton relevé dit « aucune n'est partagée » : nos deux mesures sont
> peut-être justes sans mesurer la même chose. »

**L'écriture.** L'interrupteur a été donné à la commande seule (aucun `.env`). Il était 19:24.
- **Le résultat :** sortie 0 ; 20 paquets de 100, chacun relu juste après son écriture ; **2 000 écrites, 0 sautée,
  0 contre le protocole.**
- **Les 6 critères de l'outil sont verts.**
- **La sauvegarde :** `C:\Hektor\Backups\classeur_colonne_a\2026-11-25_192440_vague1e_ECRIRE`.
- **Avant d'écrire, j'ai vérifié** qu'aucune des 6 lignes de ses paires n'était dans la vague ni déjà écrite.

**Son chiffre, par un autre chemin** (`relire_la_colonne_a_contre_le_protocole_2026-11-25.py`).
- **La vague1e : 2 000 étiquettes écrites ; 2 000 sur 2 000 égales au dossier de leurs pièces du protocole** (et à la case
  A, à l'étiquette à l'arrivée et à celle du fichier) ; **2 000 dossiers distincts** ; 0 à plusieurs dossiers ; 1 998
  ventes réglées ; toutes à leur ligne de la préparation.
- **La colonne entière : 2 600 cases remplies, exactement les quatre vagues écrites** (50 + 50 + 500 + 2 000).
  - 0 case hors des vagues, 0 manquante, 0 étiquette sur deux lignes ;
  - 0 ligne non tranchée remplie ;
  - ses doubles et les 2 lignes de la liste E sont vides.
  - La vague1b n'a jamais été écrite : elle a été remplacée par la vague1c.
- **Une ligne neuve dans le Sheet :** **a360d9e3** (ligne 4809, Offre d'achat). Elle est absente du passage 81, donc
  l'écrivain la saute. Elle attendra le passage officiel.

**Ses trois paires : nos deux mesures sont justes, mais elles ne lisent pas la même chose.**
- **Lui lit le GEL.** Le gel relie encore chaque ligne-partenaire au compromis de l'autre ligne :
  - 4PW2L3MG → le compromis 24450 ;
  - E1WD68ZB → le compromis 20264 ;
  - 60CLRO51 → le compromis 17387.
  Par le gel, la paire partage donc un dossier.
- **Moi, je lis le PROTOCOLE.** Il a délié ces trois liens (ils font partie des 256), et chaque ligne a son dossier.
  - **6U5DQQ4J → D2021-0638** : son compromis 24450 du 28/10/2021, qui est exactement la colonne « Compromis » de SA
    ligne, plus son offre 24453 du 14/09/2021 ;
  - **4PW2L3MG → D2022-0047** : son offre 24454 du 28/01/2022, seule. Sa ligne n'a pas de compromis.
  - **EO8MXFE9 → D2023-0484** : son compromis 20264 du 15/04/2024 et son offre 20267 du 06/03/2024 ;
  - **E1WD68ZB → D2023-0599** : son offre 20268 du 06/11/2023, seule.
  - **S3HOG6UL → D2021-0648** : son compromis 17387 du 03/11/2021 et son offre 17390 du 08/10/2021 ;
  - **60CLRO51 → D2021-0791** : son offre 17389 du 13/12/2021, seule.
- **⇒ Il n'y a rien à arbitrer.** Chaque compromis va à la ligne dont la colonne « Compromis » porte sa date, et chaque
  ligne-partenaire ne tient que son offre. Les six étiquettes sont distinctes, et aucune n'est déjà en A.
- **C'est le défaut du gel une fois de plus :** il lie encore les ligne-partenaires au compromis de l'autre.

**⛔ Rien chez Hektor, pas de push.** Ses décisions du 20/11 ne sont pas levées : c'est à son mot.

### Ses deux décisions du 20/11 LEVÉES ; la dernière vague (vague1f, 2 125) prête — PAS écrite (25/11, soir)

> « Vague de 2 000 : accordée, et recomptée de mon côté [...] 2 600 étiquettes toutes différentes. Ton chiffre est exact. [...]
> Mes trois paires : tu as raison, et c'est mon erreur. [...] Oui, lève-les. [...] dis-moi les deux empreintes et ton chiffre
> d'étiquettes à la fin de la vague. »

**La levée, dans l'écrivain** (`ecrire_colonne_a_du_sheet_2026-11-20.py`, sur son mot).
- **Ce qui change :**
  - `DECISIONS_LEVEES` nomme les deux décisions et pourquoi elles sont levées ;
  - `lire_hors_vague()` ne rend plus que les décisions NON levées, c'est-à-dire aucune ;
  - `decisions_du_20_11()` relit toujours les deux listes (9 et 19 lignes, avec leurs contrôles de compte), pour
    l'histoire et pour l'épreuve.
- **L'épreuve (`simuler`) : 38 verdicts, 0 rouge.** Une ligne de B (A6OS2TTJ) et une des 19 (0bc98552), glissées dans la
  vague, doivent maintenant S'ÉCRIRE : c'est le témoin positif de la levée. Les deux s'écrivent.
- **⚠ Un défaut de l'épreuve, corrigé.** Avec 2 600 cases écrites, la première case vide « libre » (qui sert au témoin
  UUID_DÉJÀ_DANS_LE_SHEET) était devenue une ligne non tranchée, CQGLHH2X. Le témoin PAS_TRANCHÉE la prenait aussi : deux
  témoins tombaient sur la même ligne, d'où 1 rouge. La case libre est désormais prise dans la VAGUE_1, hors de la vague.
- **Le classement, refait avec sa fiche neuve :**
  - 2 600 cases A ; **2 125 lignes en VAGUE_1** (2 097 + ses 28) ;
  - 74 non tranchées (73 + la ligne neuve a360d9e3) et 4 doubles.
  - Le témoin du danger inverse attend désormais 8NZ6V6XB en VAGUE_1 : sa décision est levée, et elle s'écrit avec
    l'étiquette du PROTOCOLE, pas avec celle du gel.

**La dernière vague, vague1f : 2 125 lignes, c'est-à-dire TOUT LE RESTE. Préparée, PAS écrite.**
- **L'à blanc :** 22 paquets (21 de 100, 1 de 25) ; **2 125 à écrire, 0 sautée, 0 contre le protocole.** L'empreinte de
  la vague est **47dc1d66d067d7b8**, celle de la colonne A **97800fd45bbde9da**.
  - Rapport : `C:\Hektor\Backups\classeur_colonne_a\2026-11-25_202427_vague1f_A_BLANC`.
- **Ma vérification par un autre chemin :** 2 125 sur 2 125 ont une étiquette prévue égale au dossier de SES pièces du
  protocole et à l'étiquette à l'arrivée. Les 2 125 étiquettes sont distinctes, et **aucune n'est parmi les 2 600 déjà
  écrites.**
- **Son contenu :**
  - **ses 28 décisions levées : 28 sur 28** (19 + 9) ;
  - ses trois paires, avec six étiquettes distinctes ;
  - les lignes 825 à 4808 : 1 191 ventes réglées, 799 annulées, 55 ventes prévues, 39 ventes fixées, 23 compromis en
    attente et 17 offres d'achat ;
  - 159 de ces lignes ne s'écrivent que grâce au protocole.
- **Après elle, la colonne A sera finie : 4 725 cases.** Il restera **78 cases vides** :
  - 74 lignes que le protocole n'a pas tranchées : 58 « rien à étiqueter », P252U1JH et d2108609, 9Q0FHAKK, la ligne neuve
    a360d9e3, et les autres impossibles ;
  - ses 4 doubles de saisie.
- **Le bon à lire :** `notice/CLASSEUR_VAGUE_vague1f_2026-11-25_LE_BON_A_LIRE.txt` (local seulement).

**⛔ Rien n'est écrit : la vague attend son accord sur ces deux empreintes.** Rien chez Hektor, pas de push.

### ⭐ LA COLONNE A EST FINIE : la vague1f ÉCRITE (2 125, 25/11, 20:38, son accord) — 4 725 cases

> « Oui, écris-la. [...] Donne-moi les deux chiffres à la fin : le nombre d'étiquettes écrites, et le total de cases
> remplies dans la colonne. »

**L'écriture.** L'interrupteur a été donné à la commande seule (aucun `.env`). Il était 20:38, hors de la fenêtre de nuit.
- **Le résultat :** sortie 0 ; 22 paquets, chacun relu juste après son écriture ; **2 125 écrites, 0 sautée, 0 contre le
  protocole.**
- **Les 6 critères de l'outil sont verts.**
- **La sauvegarde :** `C:\Hektor\Backups\classeur_colonne_a\2026-11-25_203804_vague1f_ECRIRE`.

**Ses deux chiffres, relus par un autre chemin** (`relire_la_colonne_a_contre_le_protocole_2026-11-25.py` : le Sheet relu,
le socle du protocole, SQL direct).
- **① Étiquettes écrites par la vague1f : 2 125.**
  - 2 125 sur 2 125 sont égales au dossier de leurs pièces du protocole (et à la case A, à l'étiquette à l'arrivée et à
    celle du fichier) ;
  - 2 125 dossiers distincts, 0 à plusieurs dossiers, 1 191 ventes réglées ;
  - ses 28 décisions levées en font partie, 8NZ6V6XB compris.
- **② Cases remplies dans la colonne : 4 725**, soit 50 + 50 + 500 + 2 000 + 2 125.
  - **4 725 étiquettes, toutes différentes** ;
  - 0 case hors des vagues, 0 manquante ;
  - chaque vague est encore juste à 100 % sur sa propre ligne.
- **Les 78 cases vides,** comme prévu :
  - 74 lignes que le protocole n'a pas tranchées, dont P252U1JH, d2108609, 9Q0FHAKK et la ligne neuve a360d9e3 ;
  - ses 4 doubles de saisie.
  - Aucune ligne non tranchée n'a sa case remplie.
- **Le compte boucle :** 4 725 + 74 + 4 = 4 803, c'est-à-dire ses 4 802 lignes plus la ligne neuve.

**Ce qui reste, à son mot, et rien n'en est fait :**
- ses 4 doubles (VIALLARD et PAOLONE) ;
- les 74 lignes non tranchées : un passage officiel du protocole plus tard, « avec les autres restes », dont P252U1JH et
  d2108609 (la liste E) et la ligne neuve ;
- 9Q0FHAKK : le rattachement proposé à 3647 et 3650 ;
- les 47 valeurs jamais posées, plus les 2 de 9Q0FHAKK ;
- la sentinelle « lignes sans lien » (compter les 15 impossibles, seuil 15).

**⛔ Rien chez Hektor, pas de push.**

### Les trois petits blocages et la méthode des 47 (25/11, soir) — RIEN ÉCRIT, deux règles PROPOSÉES

> « On continue par les trois petits blocages, puis les 47 valeurs. [...] Propose-moi donc UNE règle [...] Je tranche
> ensuite. [...] N'écris rien. [...] je veux voir ta méthode avant qu'on y touche. »

L'outil de mesure : `phase2/checks/mesurer_trois_blocages_et_les_47_2026-11-25.py`, en lecture seule. Il lit le socle du
protocole (passage 81), le registre, le gel, le miroir local de la nuit et l'image du Sheet.

**① Une règle pour les deux lignes sur un même dossier (R27 proposée).**
- **Ce que montre la mesure, paire par paire :**
  - **VIALLARD** (3308P0UX, ligne 3785 ; YRUF0S9H, ligne 3796 ; D2022-0644). Le mandat, l'acquéreur, la commission
    (6 100), le prix et l'offre (02/02/2022) sont identiques. Seule la date d'annulation diffère : 22/05 contre 22/04/2022.
    Le dossier ne tient que l'offre 4483. Le gel la donne à 3308P0UX ; YRUF0S9H n'a aucun lien. C'est bien la même affaire
    saisie deux fois.
  - **PAOLONE** (T2GZOY5O, ligne 3856 ; O6R10ZQA, ligne 3887 ; D2021-0797). Tout est identique, sauf l'annulation :
    21/11 contre 21/09/2021. Or le compromis 20073 porte DÉJÀ le 21/09/2021, celui d'O6R10ZQA, que sa décision du 24/11 a
    dit « la bonne ». Même affaire saisie deux fois.
  - **PEE1XTR8** (ligne 1495, vente réglée) **et 9B7U8221** (ligne 3845, annulée), D2021-0331. Le mandat (13502),
    l'acquéreur (SABOT), le prix (58 000) et la commission (5 700) sont identiques.
    - **⚠ Ce n'est pas une saisie double : ce sont deux TENTATIVES du même acheteur.** Leurs pièces sont distinctes,
      chacune prouvée par sa propre ligne :
      - 9B7U8221 a l'offre 26020 du 25/05/2021 (refusée) et le compromis 26019 annulé le 01/12/2021 ;
      - PEE1XTR8 a l'offre 26021 du 15/12/2021 (acceptée), le compromis 26018 du 22/12/2021 et la vente 26022 du
        18/05/2022.
    - Le chaînage les a réunies dans une seule chaîne.
    - R13 ne les prenait pas, parce que les dates d'offre diffèrent.
- **La règle R27 proposée : « deux lignes, un dossier ».**
  - **Elle s'applique quand** deux lignes tombent sur le même dossier ET disent la même affaire : même Mandat, même
    Acquéreur, même Commission TTC. Si l'une de ces trois colonnes diffère, ce sont deux affaires, et la paire reste en
    attente, nommée pour lui.
  - **Elle donne l'étiquette à UNE ligne, par trois critères dans l'ordre :**
    - ① **l'argent :** si le dossier tient une vente, la ligne dont la vente fixée (ou l'état « Vente réglée ») prouve
      cette vente → **PEE1XTR8** ;
    - ② **l'annulation déjà posée :** sinon, la ligne dont la date « Annulée » est déjà sur le compromis du dossier →
      **O6R10ZQA** ;
    - ③ **le gel :** sinon, la ligne que le gel tient déjà sur ce dossier, selon sa convention des jumelles du 20/11 (« celle
      que le gel tient déjà ; l'autre sans étiquette ») → **3308P0UX**.
    - Si aucun des trois critères ne tranche, la paire reste en attente, nommée pour lui.
  - **L'autre ligne** reçoit le verdict « rien à étiqueter : doublon (ou première tentative) de X ». Elle reste vide.
- **Ses jumeaux : la règle ne touche que ces 3 paires.** Sur tout le passage, il n'y a que 2 dossiers tenus par deux lignes
  tranchées, plus une seule paire en ATTENTE « deux lignes, un dossier ».
- **Son effet :** 3 étiquettes débloquées, dont 5 700 € pour PEE1XTR8. 3 lignes restent vides et nommées : YRUF0S9H,
  T2GZOY5O et 9B7U8221.
- **Pour 9B7U8221, une autre voie existe :** couper sa tentative (26019 et 26020) dans un dossier à elle, comme la vague
  l'a fait pour la décision B. Ce serait un geste de chaînage, donc à lui.
- **Où elle se pose :** dans le juge, au prochain passage officiel, avec les autres restes. Le passage 81 reste la seule
  référence d'ici là.

**② HUY49KEC (ligne 3248, 5 000 €) et le motif « copie seule » (R28 proposée).**
- **Ce que voit la mesure.** Sa seule pièce est la copie 1001587, dans la chaîne 3741. Cette chaîne tient la VRAIE vente
  3741 de Hektor (annonce 8671) : acquéreur CANIVET Guillaume, mandat 2332, honoraires 5 000 €, datée du 23/11/2018.
- **⚠ Deux nuances, à lui :**
  - **La facture et la date de règlement de la vente 3741 sont NOTRE recopie de son Sheet** (posée le 16/11). Les prendre
    pour preuve, c'est se prouver par sa propre copie, exactement ce que la règle interdit. Hektor ne connaît ni facture
    ni règlement.
  - **La date ne colle pas au jour près.** Sa ligne porte le 16/11/2018 dans TOUTES ses colonnes de date (offre,
    compromis, vente prévue, vente fixée), alors que Hektor date la vente du 23/11/2018 : 7 jours d'écart.
- **La règle R28 proposée.** Elle lève « copie seule » quand la chaîne de la copie tient une VRAIE vente de Hektor qui
  concorde avec la ligne par des champs de HEKTOR :
  - même mandat ;
  - même acquéreur ;
  - honoraires égaux à la Commission TTC ;
  - et une date de vente à moins de N jours d'une date de la ligne. **N est à lui** : 7 jours suffisent pour HUY49KEC.
  - La facture et le règlement ne comptent pas.
- **Combien d'autres lignes elle débloquerait : aucune.** Le motif « copie seule » compte 4 lignes. Les 3 autres (BR8ZTN5F,
  C0HXVVCW, SHN6RKDI) sont des annulées dont la chaîne de la copie ne tient aucune pièce de Hektor. Elle débloque donc 1
  ligne, HUY49KEC.

**③ 9Q0FHAKK : ce que Hektor sait de la vente.** C'est le miroir local de la nuit ; rien n'a été lu en direct chez Hektor.
- **La vente 3650** (8654 chez Hektor) : datée du 22/01/2025, 460 000 €, honoraires 18 000 €.
  - **Elle ne nomme qu'un acquéreur : SOUCHON Christine.**
  - Les mandants sont CHABANON et LAFFONT, avec un mandat exclusif ouvert le 19/06/2024. Il n'y a ni apporteur ni
    rétrocession.
  - Le compromis 3647 (23328) est aussi au nom de SOUCHON : il date du 11/09/2024, avec un acte prévu le 11/12/2024.
- **Les dates de modification :**
  - Hektor ne date pas les modifications d'une vente ou d'un compromis (aucun champ dans ce qu'il nous rend). La vente est
    vue chez nous depuis le 31/07/2026, et encore présente cette nuit.
  - **L'annonce 8395 a été modifiée pour la dernière fois le 22/02/2026 à 12:19.**
  - La fiche de POTTIER Dominique date du 12/09/2024 (Annemasse) ; celle de SOUCHON Christine du 26/03/2025 (St Victor sur
    Loire).
- **Le couple :** Hektor ne les relie PAS en couple. Aucun lien de couple n'existe entre les deux fiches.
- **POTTIER ailleurs ?**
  - POTTIER Dominique n'apparaît que sur l'annonce 8395, avec une seule offre, du 23/08/2024, refusée.
  - Le seul autre POTTIER du registre est POTTIER Paloma : une vente de 2012 sur l'annonce 45299, absente des annonces
    d'aujourd'hui. C'est une autre personne, et rien n'indique que ce soit le même bien.
  - **⇒ Aucune autre annonce ne porte POTTIER sur ce bien.**
- **Sa ligne (ligne 286), colonne par colonne :**
  - acquéreur POTTIER ; offre du 23/08/2024, qui est celle de POTTIER ;
  - compromis du 11/09/2024 et vente du 22/01/2025, qui sont ceux de SOUCHON ;
  - réglée le 24/01/2025, facture GGTI00003842 ;
  - mandat 17253, qui est faux.
- **Les factures :** le registre ne connaît aucune facture par lui-même. Celles qu'il porte sont nos recopies de son Sheet
  (le 16/11).
  - GGTI00003842 n'y est pas, parce que la ligne n'a jamais été reliée.
  - GGTI00003843 n'est pas une facture à part : elle est citée dans la case facture de P3CSA1R7 (« apporteur 10 % [...]
    déjà déduit »), que nous avons recopiée sur la vente 2393.

**④ La méthode des 47 (+2), pour qu'il la lise avant tout geste.**
- **La mesure d'aujourd'hui :** les 47 cases cibles sont toujours VIDES. Les 18 ventes ont toutes des parts : 0 vente
  réglée sans part, donc le moniteur ne criera pas. Mais **5 de ces chaînes n'ont que des parts supposées par la nuit**
  (`hektor%`) : EJN79TJ1, 2U5QPKRC, I3TFR2KG, 91IHSGNC et MQ6H8TVQ. Les poser réglées les ferait entrer dans les ventes
  réglées sur supposition. Recopier d'abord leurs parts du classeur, comme A2, serait sa décision.
- **La méthode, sur le modèle du geste des 4 dates du 25/11 :**
  - **Un fichier source par famille,** avec la pièce cible et sa preuve, la colonne (`vente_reglee_app` et
    `numero_facture_app` ; `date_annulation_app`) et la valeur prise mot pour mot dans le Sheet (la date au format ISO,
    selon sa règle).
  - **Les gardes du patch :** la case cible encore VIDE ; la pièce encore dans le dossier attendu ; la ligne encore
    tranchée au 81 sur cette pièce. Si une seule garde tombe, rien de la famille n'est écrit.
  - **La sauvegarde datée** des lignes touchées, et un journal : la place, la ligne d'origine, l'ancienne valeur.
  - **Le patch n'écrit que des cases vides,** et exige l'empreinte d'après.
  - **L'à blanc sur une copie** (begin … rollback), puis le geste par la connexion de la commande, puis la répétition en
    lecture seule. L'inverse est prêt.
  - **Le lendemain,** le témoin de la nuit : les colonnes `_app` ne sont pas écrasées par Hektor, mais on le prouve.
- **L'ordre proposé :**
  - 1) les 8 ventes réglées qui concordent ;
  - 2) les 7 dont seul le Prix du Sheet est fautif ;
  - 3) les 23 dates posables.
  - **Restent à lui :**
    - G8YSAI5Z (un 2e règlement sur un même dossier) ;
    - les écarts d'honoraires de df0ce30c et de 78bb247a ;
    - MQ6H8TVQ, qui n'a pas de facture ;
    - les 3 dates antérieures au compromis ;
    - O6R10ZQA, qui attend R27 ;
    - les 2 valeurs de 9Q0FHAKK, qui attendent son choix d'acquéreur.

**⛔ Rien n'est écrit, rien chez Hektor, pas de push.**

### R27 sans le gel, R28 « un mandat, une seule vente », R29 « la ligne suit la vente de sa commission » : les trois chiffres (25/11, soir) — RIEN ÉCRIT

> « R27 [...] pas ton troisième critère, celui du gel [...] R28 [...] je ne veux pas fixer un nombre de jours [...] Dis-moi
> combien de mandats portent plusieurs ventes [...] 9Q0FHAKK : je tranche SOUCHON. L'étiquette est D2024-0511. [...] Fais-en
> une règle, pas un cas [...] Rien n'est écrit tant que je n'ai pas vu ces trois chiffres. »

L'outil de mesure : `phase2/checks/mesurer_r27_r28_r29_2026-11-25.py`, en lecture seule. Il ne lit que des champs de Hektor :
mandat, honoraires, acquéreurs et journal des offres, jamais nos recopies de son Sheet.

**① R27, le 3e critère sans le gel.** Il ne sert que pour deux lignes ANNULÉES, quand le dossier ne tient aucune vente.
- **VIALLARD :**
  - 3308P0UX est annulée le 22/05/2022, YRUF0S9H le 22/04/2022 ;
  - le dossier ne tient que l'offre 4483 ;
  - **le journal de Hektor ne départage pas** : l'offre y est proposée et refusée le même jour, le 02/02/2022 ;
  - aucune date d'annulation n'est déjà posée.
- **La proposition :**
  - ③ **la date d'annulation que prouve le journal de Hektor** (le refus de l'offre, ou l'annulation du compromis). C'est
    une preuve ; ici, elle ne tranche pas ;
  - ④ **à défaut, et seulement quand aucun euro n'est en jeu, la plus ancienne date d'annulation.** C'est une
    convention, et non une preuve.
- **Ce que cela donne :**
  - VIALLARD → **YRUF0S9H** porte D2022-0644, et 3308P0UX reste vide (doublon). C'est l'inverse du choix du gel ;
  - PAOLONE ne change pas : O6R10ZQA par le critère ②, et le ④ dit la même chose ;
  - PEE1XTR8 garde ses 5 700 € par le critère ①.

**② R28, le verrou « un mandat, une seule vente ».**
- **Les mandats chez Hektor** (sans les copies) : 9 288 ventes réparties sur 6 218 mandats.
  - **553 mandats portent plusieurs ventes**, soit 1 142 ventes : 517 en ont 2, et 36 en ont 3.
  - Les ventes d'un même mandat ont souvent des années d'écart (2012 et 2023, par exemple) : Hektor recycle ses numéros
    de mandat.
  - 5 665 mandats ne portent qu'une seule vente.
  - 2 481 ventes n'ont pas de numéro de mandat : le verrou ne les prend jamais.
- **La forme sans jours :** un seul mandat, une seule vente dessus, les honoraires de Hektor égaux à la Commission TTC, le
  même acquéreur. La date ne sert que si le mandat porte plusieurs ventes.
  - **Elle débloque HUY49KEC** (vente 3741, D2018-0476) **et AUCUNE autre ligne.** Les 3 autres « copies seules » restent
    bloquées :
    - BR8ZTN5F : aucune vente sur son mandat ;
    - C0HXVVCW : la vente de son mandat est d'un autre acquéreur, et déjà tenue par 9a09e537 ;
    - SHN6RKDI : même chose, la vente est tenue par CC8TJTBR.
- **⚠ Le témoin de portée : R28 doit rester limitée à son motif.** Hors de lui, le verrou prendrait 3 autres lignes en
  attente :
  - PEE1XTR8 et 9B7U8221, qui réclament toutes les deux la même vente : c'est la paire de R27 ;
  - 5C80H7ZF, une première tentative de PRADIER (annulée le 20/06/2020). Sa vente du 15/01/2021 appartient à 6VSA6EOZ,
    et R11/R24 l'ont déjà dite « rien à étiqueter ».

**③ R29, « une ligne suit la vente qui porte sa commission, même quand le nom noté est celui d'un acquéreur refusé ».**
- **Ses conditions, toutes requises :**
  - le nom noté par la ligne est celui d'une offre REFUSÉE chez Hektor, au jour de l'« Offre Achat » de la ligne ;
  - le mandat de l'annonce de cette offre ne porte qu'UNE vente ;
  - les honoraires de Hektor sur cette vente sont égaux à la Commission TTC de la ligne ;
  - la vente est au nom d'un AUTRE acquéreur ;
  - aucune autre ligne ne tient cette vente.
- **Elle ne touche qu'UNE ligne : 9Q0FHAKK → la vente 3650, D2024-0511.**
  - POTTIER est l'offre refusée du 23/08/2024, sur l'annonce 8395 (mandat 17010) ;
  - la vente est celle de SOUCHON ;
  - 18 000 € d'honoraires, égaux à la Commission TTC.
- **Les 3 autres candidates sont écartées, chacune par une condition :**
  - 3THZJOOG et P252U1JH : la vente est déjà tenue par une autre ligne (SUVPN4BH, FOZ6HZLK) ;
  - 9B7U8221 : la vente est au MÊME nom (SABOT). C'est la paire de R27, pas un acquéreur refusé.

**La suite, à son accord :** poser R27 (sans le gel), R28 (dans son motif seulement) et R29 dans le juge, pour le prochain
passage officiel. On attendrait alors 5 étiquettes de plus : PEE1XTR8, O6R10ZQA, YRUF0S9H, HUY49KEC et 9Q0FHAKK.
⛔ Rien n'est écrit, rien chez Hektor, pas de push.

### R27, R28, R29 posées dans le juge (v23), éprouvées sur une copie du passage 81 — et les refus du 11-12/11 comptés (25-26/11) — RIEN ÉCRIT

> « Oui, les trois -- avec une réserve sur R29. [...] R29 : ⛔ change le mot « refusée », il ne prouve rien [...] réécris
> la condition avec un fait d'époque [...] Puis pose les trois. » ; « Et dis-moi, séparément : sur ces 1 206 refus du 11
> et 12 novembre, combien viennent de nous ? »

Le juge passe en v23 (`phase2/checks/protocole_classeur.py`, code dbda6f7a, empreinte du juge 810c9cfb). Les trois
règles sont dans REGLES_VALIDEES, avec ses mots pour source. L'épreuve : `rejouer_le_passage_81_sur_copie_2026-11-25.py`
avec les entrées du 81 remises, sur une copie (`prepa_25_11/rejeu_81_juge_v23_r27_r28_r29`). Le vrai socle n'a pas bougé
(b23e2b3a, 07:26:47), et aucun passage officiel n'a été lancé.

**① R27 joue juste : 4 verdicts changent sur 4 802, exactement ceux qui étaient attendus.**
- **PEE1XTR8** : de « deux lignes, un dossier » à **TRANCHÉE, D2021-0331**, par le critère ① (la vente 26022 n'est prouvée
  qu'à elle).
- **9B7U8221** : rien à étiqueter. C'est une autre tentative du même acquéreur, SABOT.
- **3308P0UX** : de tranchée à rien à étiqueter (doublon). **YRUF0S9H** garde D2022-0644 par le critère ④ : la plus
  ancienne annulation, une convention et non une preuve.
- **T2GZOY5O** : de tranchée à rien à étiqueter (doublon). **O6R10ZQA** garde D2021-0797 par le critère ②.
- YRUF0S9H et O6R10ZQA ne changent que dans le texte de leur preuve : R27 y remplace l'exception nommée. Leurs pièces et
  leur étiquette restent les mêmes.
- DEBARD reste une exception nommée : sa commission est de 4 700 contre 0.
- Le critère ③ ignore nos refus de masse des 11 et 12/11/2026.

**② R28 est posée, mais elle ne prend RIEN : 3741 est l'une de ses neuf pièces gardées à part.**
- Il les a mises à part le 21/11, et l'a redit le 24/11 : « les NEUF autres restent à part ».
- ⛔ **Ma mesure de R28 ne l'avait pas vu.** Elle tournait hors du juge, sans ses gardes. Le juge, lui, ne donne jamais une
  de ses pièces à part, comme pour R9, R19 et R25.
- Tout le motif « copie seule » est fait de ses pièces à part (3741, 28116, 26613), ou de lignes sans vente (BR8ZTN5F).
- **Simulé en mémoire, sans rien écrire :** si 3741 sortait de ses neuf, R28 la donnerait à HUY49KEC (D2018-0476), et
  aucune autre ligne ne bougerait.

**③ R29 est posée, mais sa garde du déjà-rendu l'a arrêtée sur 9Q0FHAKK.**
- **Ce qui bougerait :** sur le bien 5617, la vente 2162 (EYRAUD PAGÈS, 22/01/2025, honoraires 7 800 €, égaux à la
  commission de 7W7XUBPO) tombe le même jour que la case « Vente Fixée » de **deux** lignes, 7W7XUBPO et 9Q0FHAKK.
  - Tant que 9Q0FHAKK est sur ce bien, la preuve par la date désigne deux acheteurs, et la vente reste à part.
  - Si 9Q0FHAKK s'en va, la vente rejoint 7W7XUBPO, qui est déjà rendue.
- **Pour 7W7XUBPO :** son étiquette ne change pas (D2024-0357, déjà écrite en colonne A, vague1d). Seule sa liste de
  pièces gagne sa propre vente.
- ⛔ **Ma mesure de R29 ne l'avait pas vu non plus.**
- **Simulé en mémoire, sans rien écrire :** si sa garde acceptait ce gain, 9Q0FHAKK prendrait 3647, 3648 et 3650, et
  irait à D2024-0511.
  - 427UDDSF ne bougerait pas.
  - ⚠ L'offre 3648 de POTTIER quitterait son dossier D2024-0306, qui ne garderait alors aucune pièce.
- **R29 ne lit jamais l'état d'une offre.** Le bien est trouvé par un fait d'époque : la 1re proposition de l'offre de
  POTTIER, au jour de la case « Offre Achat ».

**④ Les témoins : 825 de chaque côté, 3 changent, et tous sont nommés.**
- Les deux paires de jumelles passent à l'attendu de R27, que son accord a écrit dans le code (VIALLARD → YRUF0S9H,
  PAOLONE → O6R10ZQA). Les deux sont en accord.
- coupes_29 : l'ancien écart de 3308P0UX devient une attente. Sa coupe du 20/11 lui donnait 4480 et 4483, alors que le 81
  ne lui donnait que 4483 ; c'est désormais YRUF0S9H qui porte.
- Les 5 dossiers que ces règles poseraient (D2021-0331, D2022-0644, D2021-0797, D2018-0476 et D2024-0511) ne sont dans
  aucune vague écrite.

**⑤ Les refus datés du 11 et du 12/11/2026 : 1 202, et tous viennent de nous.**
- L'outil de comptage : `phase2/checks/compter_nos_refus_des_11_12_11_2026-11-25.py`, en lecture seule.
- **Par origine :**
  - rattrapage_cascade_annulation : 661 ;
  - enqueue_refus_offres_mortes_lot : 523 ;
  - enqueue_fermeture_dossiers_impossibles : 17 ;
  - cascade_annulation_compromis : 1 ;
  - **aucune offre n'a été refusée sans un de nos travaux.**
- **Avant le refus :** 1 196 avaient été acceptées (1 194 juste avant le refus), et 6 ne l'avaient jamais été.
- **Aujourd'hui :** 1 183 sont encore refusées ; 19 ont été remises acceptées par nous le 12/11.
- **Le témoin :** 1 137 offres portent un refus d'une autre date. Total : 2 339.
- **Contre ses chiffres :** il compte 1 206 et 1 133, soit le même total de 2 339. 4 offres changent donc de côté selon la
  définition, et je ne sais pas encore laquelle. Il compte aussi 1 181 offres acceptées avant le refus, contre mes 1 196.
- **La liste des 1 202 numéros, sans aucun nom,** pour que son contrôleur fasse la différence :
  `notice/CLASSEUR_NOS_REFUS_DES_11_12_11_LES_OFFRES_2026-11-25.csv`.
- **C'est un chantier à part. Rien n'y est lancé.**

**À sa décision :**
- sortir 3741 de ses neuf pièces à part ;
- accepter, dans la garde de R29, qu'une ligne déjà rendue gagne une pièce de son propre dossier quand son étiquette ne
  change pas (c'est une règle, et ici elle ne touche que 7W7XUBPO).

⛔ Rien n'est écrit dans le Sheet, rien chez Hektor, pas de passage officiel, pas de push.

### 3741 sortie de ses neuf à part ; ses deux cases de la ligne 286 simulées sur copie ; ce que devient D2024-0306 (26/11, nuit) — RIEN ÉCRIT

> « HUY49KEC : oui, sors 3741 de mes neuf pièces à part. [...] La raison de la mise à part a disparu. » ; « 9Q0FHAKK :
> ⛔ NE touche PAS à la garde. Le défaut est dans mon classeur. [...] Je corrige mes deux cases -- mandat 17010, prix
> 460 000. Dis-moi d'abord [...] Mesure-le sur une copie et montre-moi les verdicts qui bougent. » ; « je ne veux pas
> d'un dossier vide dans le registre. »

Les refus du 11-12/11 : **il confirme 1 202** (1 185 le 11 et 17 le 12). Ses 4 offres d'écart venaient de son filtre,
qui prenait aussi le 10/11 (3 offres) et le 16/11 (1). C'est un chantier à part, et on n'y touche pas.

**① 3741 sort de ses neuf pièces à part (juge v23.1).**
- Elle passe dans SORTIES_DES_20_PAR_DECISION et dans SES_DECISIONS, avec ses mots. Il en reste HUIT à part.
- R28 la donne à HUY49KEC, comme il l'a demandé : la décision ne donne pas la pièce, c'est la règle qui le fait.

**② Les deux rejeux, sur des copies du socle, avec les entrées du 81 remises.**
- **Le rejeu A** prend l'image du 81 telle quelle (son Sheet d'aujourd'hui). Il change 5 lignes :
  - les 4 lignes de R27 ;
  - HUY49KEC, qui devient TRANCHÉE avec D2018-0476 (pièces 3741 et 1001587).
  - 9Q0FHAKK attend toujours : R29 s'abstient, sa garde tient.
- **Le rejeu B** prend la même image, avec ses deux cases de la ligne 286 corrigées par
  `simuler_ses_deux_cases_de_9q0fhakk_2026-11-26.py` (mandat 17253 → 17010, prix 112 800 → 460 000). Le registre et le
  gel restent ceux du 81, octet pour octet, et la copie est rangée hors de `protocole/images`. Il change 7 lignes : les
  5 du rejeu A, plus deux :
  - **9Q0FHAKK** passe du bien 5617 au bien 8395, par son mandat 17010, sans aucune règle. Elle devient TRANCHÉE avec les
    pièces 3647, 3648 et 3650, et l'étiquette « NEUVE:3647 », c'est-à-dire **D2024-0511** aujourd'hui.
  - **7W7XUBPO** passe des pièces 2160 et 2161 à 2160, 2161 et 2162 : la vente de PAGÈS EYRAUD, prouvée par sa case
    « Vente Prévue » du 22/01/2025. **Son étiquette ne change pas** (D2024-0357, déjà écrite en colonne A, ligne 245).
- **Ses trois questions :**
  - 9Q0FHAKK sort-elle du bien 5617 toute seule ? **Oui**, par le mandat.
  - La vente revient-elle à 7W7XUBPO sans que son étiquette change ? **Oui.**
  - R29 travaille-t-elle sans franchir de garde ? **Elle n'a même plus à jouer.** Sur le bon bien, trois dates au jour
    exact suffisent : le compromis 3647 (11/09/2024), l'offre 3648 de POTTIER (23/08/2024) et la vente 3650 (22/01/2025,
    sa case « Vente Fixée »). La garde du déjà-rendu nomme les deux mêmes biens qu'à chaque passage (25921 et 37243).
  - 427UDDSF ne bouge pas : D2024-0278, pièces 3646 et 3649.
- **Les deux lignes qui ne changent que dans le texte de leur preuve :** YRUF0S9H et O6R10ZQA (R27).
- **Les témoins : 825 dans chaque rejeu, et les mêmes 6 changements dans A et dans B.**
  - Les deux jumelles passent à l'attendu de R27 : accord.
  - coupes_29 : l'écart de 3308P0UX devient une attente.
  - a_part_20 : 3741 n'est plus attendue « à personne ».
  - ses_decisions : HUY49KEC reçoit 3741, en accord.
  - ⚠ v3 : HUY49KEC passe d'une attente à un **écart**, ce qui en fait 13 au lieu de 12. La V3 du 22/11 attendait sa
    copie seule, puisque 3741 était alors à part. C'est la même famille que ses onze pièces levées le 24/11 (PYG8JZ0C,
    PCDZXTIY, RGCEC677…), qui figurent déjà parmi les 12 écarts connus. Le témoin reste tel quel, et cet écart est nommé.
- Le vrai socle est intact (b23e2b3a, 07:26:47).
- ⚠ Le passage officiel devra se faire sur une image **prise après sa correction** : le juge ne lit que l'image.

**③ D2024-0306 : il ne restera pas de dossier vide.**
- **Un dossier, dans le registre, n'est pas une ligne d'une table.** C'est l'étiquette que portent ses pièces
  (app_affaire_ledger). Les numéros viennent d'un compteur qui, d'une nuit à l'autre, ne recule pas : un numéro rendu
  reste brûlé et n'est pas redonné.
- **Son histoire :** D2024-0306 n'a jamais porté que l'offre 3648 de POTTIER.
  - Le 12/11, les étiquettes ont été posées trois fois depuis zéro (11:38, 14:40, 22:08 UTC), et ce numéro a changé de
    dossier à chaque fois. Depuis la pose de 22:08, il appartient à 3648.
  - Le chaînage n'a jamais relié cette offre à la chaîne de SOUCHON.
- **Si le passage officiel puis la vague réalisent le verdict de 9Q0FHAKK** (3648 rejoint 3647 et 3650), la pose fait une
  FUSION :
  - la chaîne garde l'étiquette de sa plus petite pièce (3647, donc D2024-0511) ;
  - le journal des étiquettes écrit que D2024-0511 absorbe D2024-0306 ;
  - D2024-0306 n'est alors plus porté par aucune pièce. Il ne reste pas vide : il disparaît, son numéro reste brûlé,
    et sa trace reste dans le journal (sa pose du 12/11, puis la fusion).
- **Rien ne s'appuie sur lui :** 0 case de la colonne A, 0 avis du classeur, 0 part d'honoraires sur la chaîne 3648.
  Ce qui suit l'offre 3648 (sa partie, 1 ligne ; ses relations de contact, 2 lignes) est attaché à la pièce, pas au
  dossier.
- ⚠ L'offre 3648 est l'une de nos refusées du 11/11 : elle avait été acceptée le 23/08/2024, puis l'affaire a été vendue.
  Cela relève du chantier à part, et on n'y touche pas.

⛔ Rien n'est écrit dans le Sheet, rien chez Hektor, pas de passage officiel, pas de push. ⏰ Rien n'est mesuré entre
04:00 et 07:30. Demain matin, avant tout le reste : `temoin_de_la_nuit_2026-11-25.py comparer`.

### Le matin du 26/11 : la nuit vérifiée, le témoin de la nuit du 25 comparé, les parts de 9Q0FHAKK mesurées — RIEN ÉCRIT

> « Vérifie-le de ton côté et donne-moi la comparaison du témoin de la nuit du 25 [...] ⏰ Attends la fin de la descente
> [...] 9Q0FHAKK passe donc en premier, plus en dernier. [...] ses deux parts doivent porter DECHAUD 50 et GENTES 50, comme
> mon classeur, et plus une supposition. Dis-moi comment tu t'y prendrais, sans rien écrire. »

**① La nuit, vue de mon côté.**
- **Le run :** « Run quotidien termine 2026-11-26 06:58:43 (exit 0) ». Aucune étape n'a rendu de code non nul, et la
  tâche GTI Quotidien rend 0.
- **La descente :** elle a démarré à 06:59:11, après 14 minutes d'attente du run, et s'est terminée à 07:30:24. La tâche
  rend **1**. 235 tables sont descendues (1 664 983 lignes), et deux défauts sont nommés :
  - ⚠ **3 tables en échec, toutes des sauvegardes de la vague du 25/11** : app_affaire_repartition_avant_a2vague_20261125,
    …_avant_vague_20261125_080931 et …_avant_vague_20261125_090205.
    - Le compte : 17 895 lignes lues sur 17 907 attendues, et l'ancienne copie locale est gardée.
    - La cause, déjà connue : ces copies ont été créées par `create table … as select`, donc sans clé primaire.
      Elles dépassent le plafond de 15 000 lignes de la relecture par rang, posé le 15/11.
    - Aucune table vivante n'est touchée. Mais la descente sortira en code 1 chaque nuit tant que rien n'est fait.
  - L'étape 4/4 (rattrapage du carnet) s'est arrêtée net à la fermeture de Node (exit −1073740791), APRÈS avoir fait son
    travail (« rien a poser »). La descente ne compte pas cet échec.
- Je n'ai rien mesuré avant 07:30:24.

**② Le témoin de la nuit du 25 (relu à 07:31, contre la photo du 25/11 à 10:01) : la vague a tenu, et les orphelines
sont restées à 0.**
- **Le chaînage :** 0 pièce de la photo n'a changé de chaîne, et 0 n'a changé d'étiquette. 3 pièces sont neuves (30848,
  30849, 30850), et aucune n'a disparu.
- **8016 (SXJDHXKF, ROMERA 100) :** inchangée, et protégée.
- **Les reflets :** avis, notes et conditions sont tenus.
- **Les comptes :**
  - orphelines 0 → 0 ; ventes réglées sans part 0 → 0 ;
  - journal du réalignement 809 → 809 ; mise de côté 158 → 158 ;
  - les gestes du 24/11 sont tenus.
- **Une seule ligne change : les étiquettes distinctes, 11 605 → 11 606.** C'est l'offre neuve 30848 (acceptée le
  25/11, annonce 63500), qui reçoit D2026-0400. Les deux compromis neufs rejoignent des dossiers déjà étiquetés
  (D2026-0331, D2026-0339). C'est la vie normale du registre.
- **Le registre des parts :** 0 chaîne changée, apparue ou disparue. Empreinte globale inchangée (17 968 parts). Le
  témoin du comparateur voit bien une part retouchée exprès.
- **2 chaînes réécrites à l'identique, en supposition :** **3647** (celle de 9Q0FHAKK) et **27136**.
  - 27136 : D2024-0316, sur le bien 53342, avec HERITIER en supposition. Aucune ligne du classeur ne porte cette
    étiquette. Même motif que 3647 ; je n'y ai pas touché.

**③ Les parts de 9Q0FHAKK : ce que la nuit a fait, et pourquoi.**
- **Sur 3647** (compromis 3647, vente 3650, D2024-0511) : GENTES 50 en entrée et 50 en sortie, en
  hektor_partage_suppose, réécrites à 05:35:07.
  - C'est une supposition, et la nuit la réécrit chaque nuit.
  - Elle était déjà sur la photo du 25/11 à 10:01. Elle a donc été posée le 25/11, entre la vague (09:02) et la photo,
    et pas cette nuit. Cette nuit, elle a seulement été réécrite à l'identique.
- **Sur 3646** (la première tentative de SOUCHON : compromis 3646 et offre 3649, D2024-0278) : GENTES 50/50 en
  **classeur_reconstitue**. Ces parts ont été posées par le rapatriement du 13/11, depuis **427UDDSF** (GENTES 100 ;
  `notice/A5_RAPATRIEMENT_REPARTITION_2026-11-13.csv`, lignes 979-980).
  - Le 13/11, la vente 3650 était encore dans cette chaîne.
  - La vague a sorti 3647 et 3650 dans une chaîne neuve. Les parts du classeur sont restées avec les pièces de 427UDDSF,
    ce qui est juste pour cette ligne.
  - 9Q0FHAKK, elle, n'a jamais reçu de parts : elle n'était reliée à aucun dossier.
- ⚠ **Une correction sur le mécanisme.** Ce n'est pas l'étiquette qui protège un dossier, c'est l'**origine de ses
  parts**.
  - La répartition de nuit (`phase2/sync/repartition_commission.py`) ne lit ni le classeur ni la colonne A.
  - C'est la base qui saute toute chaîne portant une part dont l'origine ne commence pas par « hektor ».
  - Une étiquette seule n'arrêterait donc pas la supposition. Ce qui l'arrête, c'est de remplacer les DEUX parts hektor
    (sa règle du 24/11 : « l'origine n'est pas une étiquette, c'est le verrou »).
  - L'étiquette garde sa place dans la méthode : c'est elle qui prouve que ces parts sont celles de la ligne 286.

**④ La méthode pour DECHAUD 50 / GENTES 50, sans rien écrire.** C'est le modèle du 24/11
(`patch_suppositions_2026-11-24`), qui a déjà fait exactement ce remplacement sur la chaîne 1875 (A07EC3DH).
1. **Ton Sheet :** les deux cases de la ligne 286 corrigées (mandat 17010, prix 460 000).
2. **Une image neuve, puis un passage officiel du protocole** (le 82, dans le vrai socle), comparé au 81. Le rejeu sur
   copie de cette nuit en attend 7 lignes, et je nommerai toute autre ligne qui bouge.
   - L'écrivain de la colonne A passe alors du passage 81 au 82.
3. **La colonne A de 9Q0FHAKK :** une vague d'une ligne, D2024-0511, avec ses deux empreintes et ton accord. Les quatre
   autres étiquettes que le 82 rend écrivables (HUY49KEC, PEE1XTR8, YRUF0S9H, O6R10ZQA) iraient avec elle si tu le veux.
4. **Le patch des parts,** généré et jamais écrit à la main :
   - **Les gardes :** la chaîne 3647 porte EXACTEMENT les 2 suppositions mesurées (uid 32, 50 et 50, empreinte) ; la
     colonne A de 9Q0FHAKK dit 42dd4d66 ; le lot n'est pas déjà au journal.
   - **La sauvegarde datée :** les parts de 3647, avec une CLÉ PRIMAIRE, pour ne pas ajouter une 4e table qui casse la
     descente.
   - **Ta règle 6 :** les deux suppositions sont mises de côté, avec leur place.
   - **Le journal :** chaque part y est écrite avec sa ligne d'origine, 9Q0FHAKK (n° 286).
   - **La pose,** par la décomposition du 13/11 (50/50 : la 1re prend l'entrée) :
     - entrée 1 : 31 SIMON DECHAUD 50 ;
     - sortie 1 : 32 CHRISTELE GENTES 50 ;
     - origine classeur_reconstitue, écrite par « classeur:9Q0FHAKK ».
   - **Les contrôles :**
     - 3647 porte exactement ces 2 parts, et plus aucune part hektor ;
     - 3646 est intacte (les parts de 427UDDSF) ;
     - le total des parts est inchangé.
5. **L'épreuve à blanc,** en rejouant la VRAIE fonction de nuit (app_repartition_absorber) sur une copie : elle doit
   sauter 3647. L'inverse est prêt.
6. **Le témoin,** le lendemain après la répartition de 05:35 : 3647 doit sortir de la liste « réécrite à l'identique »,
   et 0 supposition ne doit revenir.

- Les 9 000 € de DECHAUD : 50 % de la commission de 18 000 €.
- Si la vague réalise ensuite la fusion de l'offre 3648 dans ce dossier, la chaîne garde le numéro de sa plus petite
  pièce, 3647. Les parts ne deviennent pas orphelines.

⛔ Rien n'est écrit, ni dans le Sheet, ni chez Hektor, ni en base. Pas de passage officiel, pas de push.

### Le 26/11 au matin (2) : les sauvegardes datées dans la descente — MESURÉ, RIEN BRANCHÉ

> « est-ce que ces 61 tables ont la moindre raison de descendre, et quelle règle poses-tu pour que les sauvegardes
> futures n'y entrent pas d'elles-mêmes ? Une règle par motif de nom, pas une liste de 61 exclusions à la main. »

Mesure : `phase2/checks/mesurer_les_sauvegardes_dans_la_descente_2026-11-26.py` (lecture seule ; journaux du 01 au 26/11,
pg_class, phase2.sqlite en `mode=ro`, git grep).

- **Son compte et le mien.** Ses 61 tables / 249 862 lignes = les noms en « _avant_ » qui sont descendus. La règle par
  date en prend **69 / 281 017** : ses 61, plus les 3 en échec (« _avant_ » aussi), plus 5 tables datées sans « _avant_ »
  (la photo du chaînage du 10/11, 31 145 lignes ; deux copies de fonctions ; une table d'essai ; un compte supprimé).
- **Aucune raison de descendre :**
  - elles sont figées : 0 des 69 n'a changé de taille en 26 nuits ;
  - personne ne lit leur copie locale. 17 sont nommées dans du code : générateurs de patchs, lecteurs par le pooler ou
    l'API, et un test de la descente qui travaille en mémoire ;
  - une sauvegarde sert à l'inverse d'un geste, et l'inverse se joue dans Supabase ;
  - les 66 copies locales déjà faites restent là (la règle ne supprime rien), et les 3 en échec n'ont jamais été
    écrites en local.
- **La règle proposée (non branchée)** : un nom qui FINIT PAR UNE DATE est une photo figée, et ne descend plus.
  - Le motif : `_AAAAMMJJ`, suivi ou non de `_HHMMSS`, ou bien `_AAAA_MM_JJ`.
  - `--table` la force encore, comme pour les vues, et la descente imprime chaque nuit la liste écartée.
  - « _avant_ » n'ajoute rien (0 nom en « _avant_ » sans date), et il prendrait un jour une table vivante.
  - Le risque est du bon côté : une sauvegarde mal nommée descend comme aujourd'hui (du volume, jamais une perte).
  - Simulée sur cette nuit : 169 tables, 1 383 966 lignes, **0 échec**.
- **La cause, côté générateurs** : 67 des 69 n'ont pas de clé primaire (`create table … as select`). Une sauvegarde
  naît désormais datée, avec une clé primaire et la RLS active, et sans droit pour anon ni authenticated.
- ⚠⚠ **Trouvé en passant, PAS TRAITÉ** :
  - **22 sauvegardes datées n'ont pas de RLS, et `authenticated` y a SELECT, INSERT, UPDATE et DELETE.** C'est le
    privilège par défaut de `postgres` sur le schéma public. Les tables vivantes, elles, filtrent par
    `is_app_global_reader()` ou le portefeuille.
  - Exemple : 3 copies du registre des parts (7 398 lignes), dont toute la répartition de l'agence au 13/11.
  - Qui est concerné : 2 comptes commerciaux actifs et 5 comptes sans profil. Anon ne lit rien.
  - Le remède (`enable row level security`, sans politique) ne change aucun contenu. Le pooler du juge (postgres) et
    la descente (service_role) passent toujours. ⛔ Il attend son accord.
- **Même défaut, autre famille** : 12 vues nées après le 12/10 descendent encore (25 384 lignes), parce que
  VUES_NON_DESCENDUES est une liste.
- **Le crash 0xC0000409 de l'étape 4/4** : il porte « Assertion failed: !(handle->flags & UV_HANDLE_CLOSING) »
  (libuv, à la sortie de Node). Même signature dans la descente du 06/11 et le ménage des 24 et 25/11. Pour le worker,
  la trace n'est pas dans ses journaux : ce n'est pas mesuré.

⛔ Rien n'est écrit en base, la descente n'est pas modifiée, rien n'est poussé.

### Le 26/11 (3) : la ligne 286 corrigée, l'image neuve, le passage 82 JOUÉ À BLANC — le passage officiel N'EST PAS lancé

> « les deux cases sont corrigées. Tu peux partir [...] Rejuge les trois ensemble. Ton passage 82 doit rendre quatre
> témoins, pas un [...] Si le Prix neuf lui en ajoute une par R9b, tu t'arrêtes et tu me la nommes [...] rien d'écrit
> avant que tu m'aies montré les quatre témoins du ①. »

- **L'image neuve** : `protocole/images/2026-11-26_094931`, prise à 09:49:31.
  - Sheet : 4 803 lignes, une de plus qu'au 81. Registre : 31 378 pièces. Gel : 12 820 liens.
- **Les cases changées depuis l'image du 81** (`79_image_26_11_contre_25_11.txt`) :
  - colonne A : 4 725 cases, de vide à remplie (la vague du 25/11) ; aucune case déjà remplie n'a changé ;
  - ses trois cases déclarées : 286 Mandat 17253 → 17010, 286 Prix 112800 → 460000, 245 Prix « NON TROUVÉ » → 112800 ;
  - ⚠ une quatrième sur la 286 : « Charge Commission » vide → « Vendeur ». Le juge ne lit pas cette colonne ;
  - la vie du classeur, sur des colonnes lues : 8 lignes récentes (42ae8884, 43faf7d9, 5804a343, 7cb7142f, bfe07c3b,
    e6b0043e, et 2 sur leurs commentaires seuls) ;
  - une ligne neuve, a360d9e3 : offre du 20/11/2026 (COUDERT, 10 000 €, annonce 63500).
- **Le 82 joué à blanc sur copie, deux fois** : avec les entrées du jour, puis avec celles du 81.
  - Les deux rendent la même empreinte de verdicts (b7dae92e) : les entrées vivantes ne changent rien.
  - Le vrai socle n'est pas touché : b23e2b3a, 07:26:47, passage 81 au sommet.
- **Les quatre témoins :**
  1. **9Q0FHAKK** sort d'AUCUNE_PIECE_PROUVEE et est TRANCHÉE en 42dd4d66 (D2024-0511), sur 3647 + 3650 ⚠ **et 3648**.
     3648 est l'offre du 23/08/2024, refusée par nous le 11/11/2026, et porte aujourd'hui D2024-0306. C'est déjà le cas
     dans la simulation d'hier, et c'est la fusion annoncée de D2024-0306.
  2. **7W7XUBPO** garde 8b711815, 2160 et 2161 ⚠ **et prend 2162** (la vente du 22/01/2025).
     - Elle vient par la date (colonne « Vente Prévue »), pas par R9b.
     - 2162 porte DÉJÀ D2024-0357 dans le registre : rien ne bouge, et sa colonne A n'est pas touchée.
     - Au 81, elle était « à part sans effet sur l'étiquette ».
     - Le Prix neuf de la 245 ne change rien : verdict identique à la simulation sans lui. Il y a 8 lignes au prix de
       112 800, et aucune autre sur le bien 5617.
  3. **427UDDSF** garde 704f50a8 (D2024-0278), 3646 + 3649 : tenu.
  4. **Le compte** : 4 733 tranchées + 70 en attente = 4 803 (81 : 4 729 + 73 = 4 802 ; simulation : 4 730 + 72).
     - Les 7 changements de la simulation sont tous là, à l'identique.
     - En plus : P252U1JH et d2108609, attente → tranchée. C'est le retrait de 4126 et 21520 de la liste E par la vague
       de 09:02, avec son accord (déjà mesuré le 25/11 à 14:51, « Le juge a-t-il changé ? » dans cette procédure).
     - Et a360d9e3, tranchée sur 30848.
     - 266 étiquettes passent de « NEUVE » à réelle (la vague) ; 42ae8884 et 7cb7142f prennent les compromis neufs de la
       nuit, sans changer d'étiquette.
- ⭐ **La colonne A contre le 82** : sur 4 725 cases écrites, le 82 rend la même étiquette pour les 4 725. Aucune n'est
  contredite.
- **Les lignes écrivables au 82** (colonne A vide, tranchée sur une étiquette réelle) : 8 lignes.
  - 9Q0FHAKK, HUY49KEC, O6R10ZQA, YRUF0S9H, PEE1XTR8, P252U1JH, d2108609, a360d9e3.
- **Les témoins du juge** : 30 écarts au lieu de 28 au 81.
  - Nouveaux : HUY49KEC (déjà connu), P252U1JH et d2108609 (v3, même famille, effet du retrait de E).
  - Disparu : 3308P0UX (coupes_29).
- ⛔ **Arrêt avant le passage officiel**, parce que les témoins 1 et 2 portent chacun une pièce qu'il n'a pas nommée.
- **Les comptes (son ③)** : 8 comptes ne sont pas lecteurs globaux, pas 7 — j'avais oublié l'administrateur désactivé.
  - 3 se sont déjà connectés, et 5 sont ouvrables (ni bannis ni supprimés, mail confirmé).
  - Le motif « désactivé dans l'app, ouvrable en base » touche 1 compte. Il n'a ni session ouverte ni jeton actif.
  - Aucun autre registre (identité Workspace, fiche négociateur) n'en ajoute.
  - Voisin : 5 comptes sans profil, dont 4 créés le 13/11 ; 2 sont ouvrables. Réserve nommée, rien touché.
- **Ses accords notés pour la suite** : ② la RLS des 22 après le ①, avec trois témoins ; ④ la règle des dates ce soir.
  - ⚠ La règle par date ne prend AUCUNE des 12 vues. Remplacer leur liste demande une règle par nature (vue ou table,
    lue dans la base), pas par nom.

⛔ Rien n'est écrit : ni passage officiel, ni Sheet, ni base, ni Hektor. Rien n'est poussé.

### Le 26/11 (4) : l'attribution du 82 ligne par ligne, puis le PASSAGE OFFICIEL 82 (10:22) — rien d'autre n'est écrit

> « Montre-moi donc l'attribution, ligne par ligne : ce qui vient de mes cases, ce qui vient de v23.1 et de quelle règle
> [...] Et dis-moi où en sont 3308P0UX et T2GZOY5O [...] Ensuite tu lances le 82 officiel, avec tes témoins après coup. »

**L'attribution** (`phase2/checks/attribuer_le_passage_82_2026-11-26.py`, sortie `88_…`). Elle procède par couches, et
chacune ne change qu'une chose :
- C0 : le 81 ;
- C1 : le juge v23 ;
- C2 : v23.1 ;
- C3 : ses 2 cases de la 286 ;
- C4 : ses 2 autres cases (posées par `simuler_ses_quatre_cases_sur_l_image_du_81_2026-11-26.py`, sur l'image du 81 et
  rien d'autre) ;
- C5 : l'image neuve entière ;
- C6 : les entrées du jour.

Le passage de v21 à v22 ne change rien : le rejeu du 25/11 avait rendu les 4 802 verdicts à l'identique.

284 lignes diffèrent entre le 81 et le 82 :
- **R27, 6 lignes :**
  - 3308P0UX et T2GZOY5O passent de tranchée à attente (RIEN_A_ETIQUETER, non porteuses) ;
  - 9B7U8221 change seulement de motif (de DEUX_LIGNES_UN_DOSSIER à RIEN_A_ETIQUETER) ;
  - PEE1XTR8 passe d'attente à tranchée (porteuse ; avant, c'était DEUX_LIGNES_UN_DOSSIER) ;
  - YRUF0S9H et O6R10ZQA changent seulement de preuve : « R27 » remplace « exception nommée ».
- **R28, par v23.1 (sa décision sur 3741), 1 ligne :** HUY49KEC passe de COPIE_SEULE à tranchée, D2018-0476.
- **R29 : aucune ligne.**
- **Ses deux cases de la 286, 2 lignes :**
  - 9Q0FHAKK passe d'AUCUNE_PIECE_PROUVEE à tranchée, sur 3647, 3648 et 3650 ;
  - 7W7XUBPO prend 2162. Au 81, 2162 était « à part sans effet sur l'étiquette ».
- **Ses deux autres cases (Prix de la 245, Charge Commission de la 286) : aucune ligne, même sur l'image du 81.**
  - ⚠ **LA COÏNCIDENCE, À NOMMER CAR ELLE REVIENDRA :** le montant de 2162 (et de 2160) vaut exactement 112 800, le Prix
    neuf de la 245. Elle a été écartée en rejouant sans ce Prix, puis avec : le verdict de 7W7XUBPO est le même.
  - 2162 vient par la date (colonne « Vente Prévue »), pas par le Prix.
- **L'image neuve, 278 lignes :**
  - 260 lignes changent seulement d'étiquette, de « NEUVE » à réelle : la vague de 09:02 a réalisé ces dossiers.
  - 18 autres :
    - 9Q0FHAKK, YRUF0S9H, O6R10ZQA, ESVJUR12, ULFVA1AQ, Z3DYDC4X, ZZ5WKMWM : l'étiquette réalisée par la vague ;
    - P252U1JH et d2108609 : le retrait de E par la vague (sa décision) ;
    - 42ae8884 et 7cb7142f : les compromis neufs de la nuit, 30850 et 30849 ;
    - a360d9e3 : la ligne neuve, sur 30848 ;
    - b72db9d5 : l'offre 30836 est passée de proposée à acceptée ;
    - L2B2WGCF, OAUI9CKR, ULA087KO : seule la phrase des pièces à part change (« PERD » devient « GARDE » son numéro) ;
    - UAER0F0F et VYNGKCR0 : la preuve d'un compromis sans date passe de R19 à R17.
    - Aucune de ces 18 ne change de verdict, sauf P252U1JH, d2108609 et a360d9e3.
- **Les entrées du jour : aucune ligne.**

**3308P0UX et T2GZOY5O :** en attente, RIEN_A_ETIQUETER par R27 (son accord du 25/11). Elles sont « la même affaire que
YRUF0S9H / O6R10ZQA ».
- Leurs jumelles deviennent tranchées sur une étiquette réelle : YRUF0S9H en D2022-0644, O6R10ZQA en D2021-0797. Pour le
  juge, elles sont donc écrivables.
- ⛔ **La raison nommée :** le classement de la colonne A les garde VIDES. C'est `SES_DOUBLES` (les quatre), par son mot du
  25/11 : « NE TRANCHE PAS SEUL : laisse les quatre lignes VIDES et nomme-les ».
- ⚠ Correction : l'écrivain n'a donc que 6 lignes écrivables, et non les 8 que j'annonçais.

**Le passage OFFICIEL 82** : 10:22:13 → 10:22:27, image 2026-11-26_094931, juge v23.1 (code 45fc0d9b, empreinte du juge
dc5b77ee).
- 4 733 tranchées + 70 en attente = 4 803 : le compte boucle.
- Il sort en code 1 parce qu'un témoin crie : 30 écarts et 3 en attente (le 81 avait 28 écarts et 8 en attente). Ce sont
  les mêmes que sur la copie.

**Ses témoins après coup :**
1. **Les 4 725 cases d'hier :** dans le Sheet relu à 10:22:51, aucune n'a bougé et aucune case n'a été remplie depuis
   09:49. Le 82 officiel rend la même étiquette pour les 4 725.
2. **Le socle neuf :**
   - avant : b23e2b3a, 25/11 07:26:47 ; après : 5ca7c766, 26/11 10:22:27 ;
   - l'empreinte des verdicts du 82 officiel est b7dae92e, identique à la copie ;
   - les 825 lignes des témoins du juge sont identiques à la copie.
3. **Les écrivables :**
   - pour l'écrivain, 6 : 9Q0FHAKK (D2024-0511), HUY49KEC (D2018-0476), PEE1XTR8 (D2021-0331), P252U1JH (D2020-0592),
     d2108609 (D2025-0427), a360d9e3 (D2026-0400) ;
   - 2 sont tenues vides par sa décision : YRUF0S9H et O6R10ZQA.

**L'écrivain lit encore le 81** : `PASSAGE_DU_PROTOCOLE = 81` dans `ecrire_colonne_a_du_sheet_2026-11-20.py`. Le passage au
82 est la première pièce de la vague d'une ligne.

⛔ Rien n'est écrit dans le Sheet, en base ni chez Hektor. Rien n'est poussé.

### Le 26/11 (5) : ses trois attentes du témoin v3 (v23.2), le cas de R29, l'écrivain au passage 82 — ARRÊT avant la vague

> « Mets-les à jour dans le témoin v3 avant ce soir, en nommant chacune par ma décision et sa date [...] R29 ne touche
> aucune ligne au 82 [...] nomme-moi le cas qu'elle devait couvrir [...] Pour 9Q0FHAKK, vas-y dans cet ordre : l'écrivain
> au passage 82 [...] Tu me montres chaque étape avant la suivante. »

**① Le juge v23.2 : le témoin v3 attend ce que ses décisions donnent (HUY49KEC, P252U1JH, d2108609).**
- C'est `V3_ATTENDU_PAR_SA_DECISION` : la décision et sa date sont écrites dans l'attendu du témoin.
- Les trois attentes :
  - HUY49KEC : 3741 + 1001587, sa décision du 25/11 au soir (3741 hors de ses à part, R28) ;
  - P252U1JH : 4126 + 4128, sa décision du 24/11 réalisée par la vague du 25/11 ;
  - d2108609 : 21520 + 1001495, même chose.
- **La preuve, par un rejeu sur copie de l'image de 09:49 :**
  - verdicts b7dae92e, identiques au 82 officiel ;
  - seules ces trois lignes du témoin changent, de l'écart à l'accord ;
  - 27 écarts au lieu de 30. Ce sont les 28 du 81, moins 3308P0UX qui est guéri.
- ⚠ Ces 27 écarts sont plus anciens que le 82, et le juge sort encore en code 1 à cause d'eux. Ils ne sont pas encore
  nommés un par un.

**② R29 : son cas, mesuré DANS le juge** (`mesurer_le_cas_de_r29_2026-11-26.py`, avec sa propre fonction r29_candidat).
- **Témoin positif, l'image du 81 :** sur 68 lignes non tranchées regardées, UN seul candidat, 9Q0FHAKK.
  - Son nom POTTIER est celui de l'offre 3648, proposée le 23/08/2024 sur l'annonce 8395, mandat 17010.
  - La seule vente de ce mandat est 3650, et ses honoraires valent sa Commission.
  - La garde du déjà-rendu l'a arrêté, parce que 7W7XUBPO aurait pris 2162.
- **L'image du 82 :** sur 62 lignes regardées, **aucun candidat**. 56 n'ont aucune offre à leur nom le jour de leur case,
  4 n'ont ni nom ni date, et 2 passent l'offre mais s'arrêtent plus loin.
- **Conclusion :** le cas a existé, une seule fois, et le juge le voyait. C'était une ligne au Mandat emprunté à une autre
  ligne. Sa correction à la source l'a fait disparaître.
  - La protection réelle a été l'ATTENTE visible (AUCUNE_PIECE_PROUVEE), qu'il a lue et corrigée.
  - Je recommande de retirer R29. Elle n'est pas retirée : c'est à son mot.

**③ Étape 1 de 9Q0FHAKK : l'écrivain au passage 82.**
- Quatre outils lisent maintenant le 82 :
  - `ecrire_colonne_a_du_sheet` (PASSAGE_DU_PROTOCOLE = 82) ;
  - `classer_colonne_a_par_le_protocole` (PASSAGE = 82) ;
  - `relire_la_colonne_a_contre_le_protocole` ;
  - `colonne_a_contre_le_verdict_du_protocole`.
- Le classement du 81 reste intact (fichier du 25/11). Celui du 82 va dans un fichier neuf :
  `notice/CLASSEMENT_COLONNE_A_PAR_LE_PROTOCOLE_2026-11-26_PASSAGE_82.csv`.
- Témoin : l'écrivain charge le passage 82 (4 733 tranchées sur 4 803), et voit 9Q0FHAKK sur 3647, 3648 et 3650.

**Le classement du 82 a crié, et chaque cri est nommé :**
- **Témoin 1 (4 732 / 4 733) — 9Q0FHAKK est rangée PLUSIEURS_DOSSIERS.**
  - 3647 et 3650 portent D2024-0511, mais **3648 porte encore D2024-0306** : la nuit la garde dans sa propre chaîne.
  - ⭐ La cause : 3648 est une de NOS refus du 11/11, par le rattrapage_cascade_annulation de 19:03. Elle avait été
    acceptée juste avant.
  - L'écrivain exige une seule étiquette sur toutes les pièces d'une ligne : **la colonne A de 9Q0FHAKK ne peut pas
    s'écrire tant que 3648 n'a pas rejoint la chaîne 3647.**
- **Témoin 5 — ⛔ MA FAUTE.** Je lui avais écrit que le classement tenait YRUF0S9H et O6R10ZQA vides par sa décision.
  - C'est FAUX au 82 : la case DOUBLE_DE_SAISIE ne les prenait que si deux lignes tranchées portaient le même dossier.
  - R27 a mis une des deux jumelles en attente, donc la règle ne les voyait plus. Seul le témoin 5 les arrêtait.
  - **C'est corrigé** : sa décision est désormais une règle, placée avant tout verdict. Les quatre doubles restent vides,
    quoi qu'en dise le juge.
- **Témoin 4 — trois attentes périmées, nommées comme le v3 :**
  - 8NZ6V6XB et ZV3QRSJG ont été écrites le 25/11 à 19:40 UTC par la vague1f ;
  - P252U1JH est sa décision du 24/11, réalisée par la vague du 25/11.
- **Après ces corrections, il ne reste qu'un cri, le témoin 1 (9Q0FHAKK).**
  - Le classement range 4 725 cases déjà remplies, 68 lignes non tranchées, 1 ligne PLUSIEURS_DOSSIERS, 4 doubles et
    5 lignes écrivables : PEE1XTR8, HUY49KEC, P252U1JH, d2108609, a360d9e3.
  - Il n'a PAS de fiche de fabrication : l'écrivain le refuse, et rien ne peut partir.

**La suite proposée, sans rien écrire :** une ligne dans `phase2/sync/rattachements_manuels.csv`.
- C'est son mécanisme du 12/11 : la nuit l'applique, avec 16 lignes aujourd'hui. Le fichier dit « on n'en ajoute
  JAMAIS une sans lui ».
- La ligne serait `3648;3647;8395;2026-11-26;POTTIER -- …`.
- La nuit mettrait 3648 dans la chaîne 3647. La fusion garde l'étiquette de la plus petite pièce, 3647 : D2024-0306
  fusionnerait donc dans D2024-0511.
- Le lendemain : le témoin (3648 en D2024-0511, journal « fusion »), le classement signé, puis la vague d'une ligne.

⛔ Rien n'est écrit dans le Sheet, en base ni chez Hektor. Le fichier des rattachements n'est pas touché, et rien n'est
poussé.

### Le 26/11 (6) : R29 retirée (v23.3), la ligne de rattachement de 3648 éprouvée, la RLS des 22 prête — rien d'écrit

**① R29 RETIRÉE (juge v23.3), sur son mot.**
- Elle passe dans `REGLES_RETIREES`, et `joue()` la refuse, même en variante de mesure.
- La preuve, par un rejeu du 82 sur copie : verdicts b7dae92e identiques, 27 écarts, et plus aucune ligne « R29 ».
- ⭐ **LA LEÇON, DANS SES TERMES :** « Le seul cas qu'elle couvrait était 9Q0FHAKK elle-même, et il a disparu quand j'ai
  corrigé mes deux cases. C'était un pansement sur la cause. Ce qui a protégé cette ligne, c'est qu'elle est restée
  visiblement en attente jusqu'à ce que je la regarde. » — **une garde qui laisse la ligne en attente valait mieux qu'une
  règle qui l'aurait tranchée seule.**
- Et la leçon voisine (son mot) : une décision tenue par un témoin de dernière seconde n'est pas tenue. Les quatre doubles
  sont désormais tenus par une règle.

**② ⛔ RÉSERVE NOMMÉE, LA TROISIÈME FOIS — un chantier à ouvrir pour lui-même.**
- 9Q0FHAKK est bloquée par NOTRE opération des 11 et 12/11 : 1 202 offres refusées, dont 3648 à 19:03 par le
  rattrapage_cascade_annulation, alors qu'elle venait d'être acceptée.
- Son mot : « C'est un chantier à ouvrir pour lui-même, pas à réparer dossier par dossier quand il nous tombe dessus. »
- La ligne de rattachement de 3648 répare CE dossier ; elle ne répare pas l'opération.

**③ La ligne de rattachement, À SA RELECTURE avant la nuit.** Le vrai fichier n'est pas touché.
```
3648;3647;8395;2026-11-26;POTTIER -- l'offre du 23/08/2024 (acceptee, puis refusee le 11/11/2026 par notre rattrapage_cascade_annulation) rejoint son compromis 3647 et sa vente 3650 : la ligne 9Q0FHAKK du classeur (passage 82) -- D2024-0306 fusionne dans D2024-0511
```
- **Éprouvée par la VRAIE fonction de nuit**, `recalculer_les_chaines`, sur une copie en mémoire du registre
  (`rejouer_le_rattachement_de_3648_2026-11-26.py`), avec un fichier temporaire :
  - BASE : le fichier tel qu'il est rend la base, 0 écart ;
  - POSITIF : 3648 passe dans la chaîne 3647, avec 3647 et 3650 ; le compteur « [M] rattachement décidé à la main » passe
    de 16 à 17 ;
  - INVERSE : seule 3648 change de chaîne, et 427UDDSF garde {3646, 3649} ;
  - GARDES : ni deux ventes ni deux compromis vivants de plus dans un dossier ;
  - ÉTIQUETTE : la plus petite pièce, 3647, porte D2024-0511, et plus aucune pièce ne porterait D2024-0306.
  - ⚠ Vu au passage : la nuit applique les rattachements AVANT les coupes à la main. La coupe du bien 8395 n'isole que
    {3646, 3649} (427UDDSF), donc 3648 reste bien avec 3647. Le rejeu le confirme.
- **Le témoin de demain** (`temoin_du_rattachement_de_3648_2026-11-27.py`, à lancer après 07:30) MESURE, à la place du
  compte rendu :
  - la chaîne dans le registre local et dans Supabase ;
  - l'étiquette de chaque pièce, et qui porte encore D2024-0306 ;
  - la fusion inscrite au journal des étiquettes ;
  - et son témoin positif : les 16 autres rattachements sont-ils réunis ?
  - ⭐ **Lancé aujourd'hui, il répond « PAS RÉUNIE » (code 1)**, et voit les 16 autres réunis. C'est son témoin inverse :
    il sait voir les deux états.
- **Une seule vague demain, pas deux** (son mot) : les six lignes d'un coup, sur un classement propre et sans cri — 9Q0FHAKK
  avec PEE1XTR8, HUY49KEC, P252U1JH, d2108609 et a360d9e3.

**④ CE SOIR, dans son ordre, chaque geste à son mot :**
1. **La RLS des 22 seule** (`refermer_les_22_sauvegardes_ouvertes_2026-11-26.py`).
   - Ses gardes sont VERTES dès ce matin, en lecture seule : la liste mesurée à l'instant correspond exactement aux 22
     figées ; aucune n'a de RLS ni de politique, toutes appartiennent à postgres ; et le témoin positif tient (en
     authenticated, chaque table rend ses lignes).
   - ⚠ Mon premier essai à blanc est passé par le pooler du juge, qui ouvre en LECTURE SEULE : la base a refusé l'ALTER,
     et rien n'a été touché. L'essai à blanc et le geste demandent une connexion en écriture, et je ne l'ouvre qu'à son
     mot, ce soir.
   - Puis l'essai à blanc (transaction annulée), puis le geste. Témoin (a) : 0 ligne pour authenticated, et le même compte
     en postgres.
2. **Témoin (b)** : le rejeu du 82 sur copie doit retrouver b7dae92e.
3. **Témoin (c), la descente de contrôle** : `pull_from_supabase.py --table` pour les 22 → 22 tables, 0 échec, le même
   nombre de lignes qu'en postgres.
4. **Seulement après (c) : la règle « un nom qui finit par une date ne descend plus »**, puis le `--dry-run`.
5. **Et la ligne de rattachement**, après sa relecture, avant le run de 04:00.

⛔ Rien n'est écrit en base, dans le Sheet, dans le fichier des rattachements ni chez Hektor. Rien n'est poussé.

### Le 26/11 (7) : la ligne de rattachement VALIDÉE, avec son marqueur ; le témoin du matin lit le journal de la nuit

**① La ligne, validée par lui, avec un seul ajout : le marqueur « [refus 11/11] » en tête du commentaire.**
- Son mot : « pour qu'on retrouve d'un seul coup toutes les réparations nées de cette opération quand on ouvrira ce chantier
  pour lui-même ».
```
3648;3647;8395;2026-11-26;[refus 11/11] POTTIER -- l'offre du 23/08/2024 (acceptee, puis refusee le 11/11/2026 par notre rattrapage_cascade_annulation) rejoint son compromis 3647 et sa vente 3650 : la ligne 9Q0FHAKK du classeur (passage 82) -- D2024-0306 fusionne dans D2024-0511
```
- Rejouée avec le marqueur par la vraie fonction de nuit sur copie : TOUT VERT, à l'identique (seule 3648 bouge, D2024-0511
  gardée, D2024-0306 vidée). Le lecteur rend le commentaire qui commence par « [refus 11/11] ». La ligne est en ASCII.
- ⏰ Elle s'écrit EN DERNIER ce soir, avant 04:00 (son ordre). Le fichier n'est pas touché.

**② Le témoin du matin lit maintenant le journal de la nuit (son mot) :** « Réunie « oui » ne dit pas par quoi : si une règle
l'avait rapprochée d'elle-même, ou si notre ligne n'avait pas été appliquée du tout, le témoin dirait oui dans les deux cas. »
- Le mécanisme écrit cinq messages (affaire_ledger.py, boucle « LES RATTACHEMENTS DECIDES A LA MAIN ») : « [M] rattachement
  decide a la main » est le seul attendu ; « le bien ne correspond pas », « transaction introuvable », « deja obtenu par une
  regle » et le cri « DEUX VENTES » doivent être absents — et tout autre message « [M] ».
- ⚠ **Le journal ne nomme pas le bien** : `signale()` compte par libellé. La preuve se lit donc ainsi : chaque ligne produit
  EXACTEMENT UN des quatre premiers messages (la boucle fait `continue` après chaque refus) ; donc « lignes lues » =
  « décidé à la main » = les lignes du fichier, sans aucun autre « [M] », veut dire que CHAQUE ligne, la nôtre comprise, a
  été appliquée à la main. Plus : l'étape DONE, un journal postérieur à l'écriture du fichier, et « fusion N » avec N ≥ 1.
- ⑤ **Le bien nommé** : la vraie fonction rejouée sur le registre du matin avec SEULE la ligne 3648 (aucune autre décision
  n'est sur 8395) doit dire exactement { « décidé à la main » : 1 }. C'est un rejeu, pas l'enregistrement de la nuit.
- **Ses témoins, pris aujourd'hui :**
  - le lecteur crie sur 4 journaux truqués en mémoire sur 4 (un refus ajouté, DEUX VENTES ajouté, une ligne non appliquée,
    la ligne absente), et se tait sur le vrai ;
  - le journal du 26/11 : 16 lues, 16 « décidé à la main », aucun autre « [M] », étape DONE, fusion 0 → « pas » ;
  - ⑤ positif avec la ligne proposée : 3648 → 3647, { « décidé à la main » : 1 } ; ⑤ inverse sans la ligne : aucun message.

**③ La RLS des 22 : gardes revertes cet après-midi** (22 mesurées = 22 figées, RLS absente, propriétaire postgres, aucune
politique, chacune lisible par authenticated). La connexion en écriture se demande AU MOMENT de la RLS (son mot).

⛔ Rien n'est écrit en base, dans le Sheet, dans le fichier des rattachements ni chez Hektor. Rien n'est poussé.
