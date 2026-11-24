# Ses six décisions : les cases vides à blanc — 24/11 (son 5e mot)

> Son mot : « TES SIX DÉCISIONS SONT PRISES. VOICI LES RÈGLES, PAR FAMILLE. Rien ne s'écrit sans mon accord sur le patch ;
> chaque famille se joue À BLANC puis avec son inverse. » L'ordre : ⑥ et ① d'abord, puis ④, puis les 2 de ⑤, puis ③ et ② en
> réserve nommée ; le reste attend la vague.

**Rien n'est écrit dans ce temps.** Les patchs sont fabriqués et joués à blanc chez Supabase. Chaque essai fait
l'aller-retour dans une même transaction : le patch, puis son inverse, puis le retour exigé à l'empreinte d'avant, et une
erreur voulue à la fin. Après coup, le journal porte toujours ses 46 lignes du matin, et il ne reste ni sauvegarde, ni
colonne neuve, ni charge, ni date.

Outil : `phase2/checks/cases_vides_generer_patchs_2026-11-24.py`.

---

## ① La Charge : 16 mandats prêts, 2 mandats contredits par le Sheet

**État mesuré chez Supabase.** Les 18 mandats des 20 lignes ont un carnet vide et un reflet vide. Chacun est le seul mandat de
son annonce.

**⛔ Deux mandats portent deux lignes du Sheet qui se contredisent.** La Charge vit sur le mandat, qui ne porte qu'une
valeur :
- **46338 / 17322** : cc33cc38 (vente réglée, 6 000 €) dit « Vendeur » ; afd672fa (annulée) dit « Acquéreur ».
- **47174 / 17639** : df0ce30c (vente réglée, 5 000 €) dit « Acquéreur » ; 2c2566d7 (annulée) dit « Vendeur ».

Ces deux mandats ne sont dans aucun patch. Je ne choisis pas à ta place. Ma proposition : la valeur de la vente réglée,
celle de l'affaire qui a abouti.

**Les patchs, « case vide = pas d'écrasement » :**
- **①a, les 3 ventes réglées sans contradiction** (21 000 € ; les deux autres réglées sont sur les mandats contredits) :
  125888d3, 5YUGE9KA, 78004641, toutes « acquéreur ».
  - Fichier : `supabase/patch_charge_1a_reglees_2026-11-24.sql`.
  - Aller-retour à blanc **VERT** : empreinte avant fba1a157, après 04f45cf7, retour fba1a157.
- **①b, les 13 autres** (offres, compromis en attente, annulées).
  - Fichier : `supabase/patch_charge_1b_2026-11-24.sql`.
  - Aller-retour à blanc **VERT** : avant e2233fb6, après 44fc64cd, retour e2233fb6.

**Ce que fait chaque patch :**
- **Les gardes** : la case est vide au carnet et au reflet ; le mandat existe au registre ; l'empreinte d'avant est exigée.
- **La sauvegarde datée** : les lignes du registre des mandats de ces annonces.
- **Le journal** (le même que pour les 42) : deux colonnes neuves, `mandat_annonce` et `mandat_numero`. Chaque écriture
  y porte **sa ligne d'origine** (identifiant, numéro au Sheet) et **sa place** (le mandat, et la pièce qui le porte).
- **Le carnet** reçoit l'écriture comme le lot C1 du 14/11 : origine `classeur`, `ecrit_par = 'classeur:<ligne>'`, et
  « on conflict do nothing ».
- **Le reflet** est reposé par `app_reposer_charge_mandat_app`, **annonce par annonce**, jamais sur tout le registre.
- **Les contrôles** : charges au carnet, reflets posés, **0 autre reflet bougé**, ligne d'origine au journal, empreinte
  d'après exigée.
- **L'inverse** ne retire que ce que le lot a posé, repose le reflet et exige l'empreinte d'avant.

## ② Les 3 Charges contraires : en réserve nommée

« Case déjà remplie : on n'écrase JAMAIS. » Ce sont JEK94D31 (43787 / 4247), KBZR2ND6 (49495 / 17107) et XQGPK8LV
(33220 / 14253). Ce sont les désaccords jugés le 03/11. Je n'y touche pas.

## Les 6 dates : prêtes, deux sont signalées

Chacun des 6 compromis est annulé et sans date depuis le geste du matin. Chaque Sheet porte une date.
- TR42PT5H → 27195 : 20/05/2025.
- U0GQ3KTO → 4385 : 22/11/2022.
- IEYXREWQ → 27134 : 01/02/2024.
- R0JRVFDC → 16377 : 21/01/2021.
- ⚠ **S3HOG6UL → 17387 : 21/10/2021**, antérieure au compromis du 03/11/2021.
- ⚠ **6U5DQQ4J → 24450 : 21/10/2021**, antérieure au compromis du 28/10/2021.

Ta règle de C3 (16/11) écartait une date d'annulation antérieure au compromis (106 cas). Ces deux-là sont dans le patch,
comme tu l'as dit, et le journal porte l'avertissement. Si tu préfères la règle de C3, je les retire.

Fichier : `supabase/patch_dates_a_l_unite_2026-11-24.sql`. Aller-retour à blanc **VERT** : avant df785d76, après 46517bdd,
retour df785d76.

## ⑥ Les 12 nouveautés : aucune n'a sa pièce chez nous

- **Les 11 factures (GGTI00004569 à 4579)** sont toutes « Vente fixée ». Aucune n'a de **vente** chez nous : seulement une
  offre acceptée et un compromis actif. La vente n'est pas encore saisie chez Hektor.
  - Ta règle de C8 (16/11) pose la facture **sur la vente**.
  - La poser sur le compromis serait une règle neuve.
  - Je n'ai rien fabriqué. À toi.
- **c6e5299a (annulée le 20/11/2026)** n'a qu'une **offre refusée** (30816), sans compromis. La règle de C3 ne pose rien
  (une offre refusée porte déjà sa date de refus, règle du 12/11). Je la nomme.

## ③ Les 16 sans part : nommées ; a5cb141f expliquée

**a5cb141f : l'argent a ses négociateurs, sur l'autre chaîne du bien.**
- **Le bien (11820) n'a aucune vente chez Hektor.** Il a un compromis 6171, annulé, sans date (`0000-00-00`), et une
  offre 6172, refusée.
  - Le Sheet dit « Vente réglée 17/01/2026 », 2 000 €, facture « GGTI00004281 **Protocole d'accord** ».
  - Ce sont donc des honoraires encaissés par un protocole d'accord après la chute du compromis, pas une vente.
- **Les parts existent.** Elles ont été posées le 13/11 (origine classeur) **sur la chaîne du compromis 6171** :
  DELAVAUD 50 à l'entrée, RONDEAU 50 à la sortie.
- **La ligne, elle, pointe l'offre 6172**, qui est sur une autre chaîne, sans part.
  - Le chaînage ne peut pas relier les deux : compromis sans date, offre sans acquéreur.
  - C'est un des deux biens que tu m'avais fait mesurer le 10/11.
- **Ce qu'il faut poser : rien à la main.** Le remède A2 à blanc recopie les deux parts de 6171 vers 6172, la chaîne où la
  ligne arrive. Il met de côté celles de 6171 avec leur ancien numéro, puisque aucune ligne n'y arrive plus. À l'arrivée,
  la ligne est juste. Écrire maintenant ferait un doublon.
- **La facture et le règlement ne sont posés nulle part** : C8 n'avait pas de vente. Les poser sur le compromis 6171 serait
  la même question que les 11 factures de ⑥.

**Les 15 autres** (11 offres, 2 compromis en attente, 2 annulées) sont nommées, en réserve : pas de vente, pas de part.

## ⑤ Les 5 déjà justes et JRE23R1G : nommées

- **Les 5 déjà justes** (8NZ6V6XB, 9FP3UICY, FWCFAN6O, LKBO1TOH, IEYXREWQ) : aucune part n'est écrite. La vague les réunit.
- **JRE23R1G** : sa chaîne 27133 garde la vente réglée 27142. Elle attend la vague. Je n'y touche pas.

Les 2 à corriger (739a0db1, TR42PT5H) et ④ suivent ton ordre : après ⑥ et ①.

## La paire jumelle T2GZOY5O / O6R10ZQA, pour que tu tranches

Les deux lignes sont **la même affaire** :
- même mandat, 4369 ; même acquéreur et même vendeur ;
- mêmes dates : offre 14/06/2021, compromis 02/07/2021, vente prévue 04/03/2022 ;
- même commission, 3 500 € ; même négociateur, PEYRARD 100 ; même prix, 34 000 €.

**Elles ne diffèrent que par deux cases :**
- O6R10ZQA (ligne 3887) : Annulée **21/09/2021**, et « En attente de » : « Simonet BVx ADP+dPC ».
- T2GZOY5O (ligne 3856) : Annulée **21/11/2021**, et « En attente de » vide.

**Ce que portent les pièces :**
- **Le compromis 20073** (Hektor, annulé, daté du 02/07/2021) porte la date **21/09/2021**, celle de O6R10ZQA (lot C3,
  16/11). Il porte aussi la note F de O6R10ZQA (« Simonet BVx ADPdPC »). ⚠ Hektor y nomme un autre acquéreur que le Sheet.
- **L'offre 20075** (Hektor, refusée) porte l'acquéreur du Sheet.
- Les deux copies créées le 16/11 pour ces lignes : 1001480 (offre, pour O6R10ZQA) et 1001536 (compromis, pour T2GZOY5O).

Laquelle est la bonne ?
