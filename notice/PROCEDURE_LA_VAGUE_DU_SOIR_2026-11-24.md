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

