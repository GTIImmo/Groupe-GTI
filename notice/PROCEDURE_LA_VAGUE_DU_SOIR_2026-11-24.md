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
