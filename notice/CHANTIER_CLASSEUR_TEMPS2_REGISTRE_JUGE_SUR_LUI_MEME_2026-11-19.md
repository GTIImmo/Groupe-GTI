# TEMPS 2 — LE REGISTRE DES TRANSACTIONS JUGÉ SUR LUI-MÊME, SANS LE GEL
### 19/11/2026 · chantier classeur, conduit par `notice/PROMPT_FINIR_LE_CHANTIER_CLASSEUR_2026-11-19.md`

> ⛔ **LECTURE SEULE DE BOUT EN BOUT.** Aucune écriture en base, chez Hektor ni dans le Sheet.
> ⛔ **NI LE GEL NI LE SHEET N'ONT ÉTÉ LUS.** Le registre est jugé sur ses propres règles.
>
> **Rejouer la mesure** (lecture seule, ~2 min) :
> ```
> .venv\Scripts\python.exe -X utf8 phase2\checks\temps2_registre_juge_sur_lui_meme_2026-11-19.py
> .venv\Scripts\python.exe -X utf8 phase2\checks\verifier_regle_chainage.py
> ```
> Le premier sort 0 le 19/11 et écrit **`notice/TEMPS2_REGISTRE_ANOMALIES_2026-11-19.csv`**
> (671 lignes, une par cas). Le second est le contrôleur du projet (08/09), lancé tel quel.

---

## 0. EN UNE PAGE

```
LE REGISTRE      31 359 transactions . 11 590 dossiers . 11 590 etiquettes . 11 590 numeros
                 LOCAL ET SUPABASE IDENTIQUES : 0 ecart sur 31 359 (chaine, etiquette, etat,
                 genre, numero Hektor)

LES INVARIANTS DURS -- TOUS A ZERO, chacun avec son temoin seme vu
  deux ventes dans un dossier                      0
  deux compromis vivants dans un dossier           0
  un dossier sur deux biens                        0
  etiquette / chaine / numero pas en bijection     0
  numero de chaine different du plus petit membre  0
  transaction sans chaine, etiquette ou numero     0
  meme numero Hektor sur deux lignes               0
  transaction du classeur portant un numero Hektor 0
  transaction sans bien . genre inconnu            0 . 0
  nee dans l'app et jamais numerotee               0
⭐ LA VRAIE FONCTION DU CHAINAGE, REJOUEE SUR UNE COPIE : 0 ECART avec la base
  (verifier_regle_chainage.py, test ⑤) -- la base EST le resultat de la regle.

CE QUI EST A JUGER -- des constats, pas des pannes
  24  transactions du CLASSEUR qui doublent une transaction de Hektor, TOUTES dans un
      AUTRE dossier que leur original  <- nos creations C5
  15  blocs dates APRES la vente de leur dossier (14 au meme acheteur)
 275  offres datees plus de 31 jours APRES le compromis de leur dossier (266 dossiers)
  11  offres dont l'etat contredit le journal de Hektor (aucune touchee par nous)
  13  numeros de dossier sans annee vraie (D0000 x6, D1990 x7)
   2  transactions PRESENTES que le run ne revoit plus depuis le 26/10 (bien 61672)
   1  dossier a deux offres acceptees -- c'est la consequence des 2 ci-dessus
   1  offre refusee PAR NOUS dans un dossier vendu : 14420, laissee par decision
   1  « fusion » d'etiquette qui n'en est pas une (18/11) -- § 4

DEUX CORRECTIONS AU DOSSIER (§ 6 du 19/11)
  « dossiers a deux offres acceptees : 2 »  -> 1 aujourd'hui, et il vient d'une LECTURE
  « ventes sans aucune offre : 461 »        -> 460
```

⭐ **Le registre tient debout.** Ses invariants durs sont tous à zéro et le chaînage en base est
exactement ce que la règle produit. Ce qui reste est **à juger cas par cas** : des dates fausses
chez Hektor, nos copies C5, et une lecture qui ne marque pas deux offres disparues.

---

## 1. LA MÉTHODE

**Un invariant = une fonction qui rend la liste de ses cas**, dans
`phase2/checks/temps2_registre_juge_sur_lui_meme_2026-11-19.py`. Le registre est lu **chez
Supabase**, et jugé **avec les yeux de la règle** : les dates sont celles de `_date_de_tri` (la
première proposition d'une offre, `affaire_ledger.py` l. 1564), les acquéreurs ceux de
`_acquereurs` (l. 1868), les états morts ceux du code (`ETATS_OFFRE_MORTS` l. 1539,
`ETATS_COMPROMIS_MORTS` l. 1541), et « effacée chez Hektor » est **la définition du run**
(un numéro Hektor ET `present_in_hektor` faux, l. 2009-2012). **Aucune copie de la règle.**

⭐ **Un zéro ne se croit pas sans témoin positif.** Chaque détecteur est rejoué sur le registre
**augmenté d'un jeu semé en mémoire** : un dossier fabriqué par défaut cherché (deux ventes,
deux compromis vivants, une étiquette sur deux chaînes, un bloc après la vente, un doublon de
numéro, une transaction non relue…). **Les 23 détecteurs ont vu leur cas semé.** Si un seul
l'avait manqué, le script sortait en code 2.

**Deux recoupements indépendants :**

```
LOCAL CONTRE SUPABASE   phase2.sqlite (lu en mode=ro) contre Supabase, les 31 359 lignes :
                        0 absente d'un cote, 0 ecart sur chaine . etiquette . etat . genre
                        . numero Hektor
LE CONTROLEUR DU PROJET verifier_regle_chainage.py (08/09), sans rien y changer :
  ① le run contre l'ecran (App.tsx)           0 divergence sur 11 575 chaines vivantes
  ② Supabase (app_chaine_pour) plus permissif 0 cas
  ③ un bloc apres la vente                    1 (+ 14 ecartes : meme acheteur, meme montant)
  ⑤ LA VRAIE FONCTION sur une copie jetable   31 359 lignes, 0 ECART
  ⑥ deux ventes . deux compromis vivants      0 . 0  (temoin : 505 dossiers a plusieurs offres)
```

---

## 2. LES INVARIANTS, UN PAR UN

### 2.1 Le DOSSIER (la chaîne)

```
deux ventes                              0      dur      temoin vu
deux compromis vivants                   0      dur      temoin vu
un dossier sur deux biens                0      dur      temoin vu
numero != plus petit membre vivant       0      dur      temoin vu
dossier tout entier efface chez Hektor  15      constat  998, 3698, 3699, 3701 (le garage
                                                         VS046), 16778, 19029, 19049, 19414,
                                                         19543, 21803 (2), 25699, 28568,
                                                         28808 (2), 28917, 28959
deux offres acceptees                    1      a juger  30712 -- voir 2.5
```

### 2.2 La SÉQUENCE (l'ordre dans le temps)

```
un bloc date APRES la vente du dossier  15      a juger
   14 au MEME acheteur : 2588, 4470, 7122 (x2), 13780 (x2), 14247, 14419, 24341, 24465,
      24741 (x2), 28145 (x2) -- le controleur du projet les classe « la DATE DE LA VENTE
      est fausse chez Hektor » (meme acheteur ET meme montant)
    1 a un AUTRE acheteur : dossier 9451, l'offre 9452 (acceptee) du 02/05/2024 apres la
      vente du 18/03/2024 -- et son journal dit « proposition », pas « acceptee » (2.4)
une vente datee AVANT son compromis      6      a juger  tous dans les 15 ci-dessus
une offre datee > 31 j APRES le          275    a juger  266 dossiers . 81 a moins de 90 j
   compromis (la regle B en tolere 31)                   . 234 a moins d'un an . 41 au-dela
                                                         . 9 seulement portent un de nos
                                                         gestes du temps 1
sans date de tri (ne rejoint jamais     260     constat  196 compromis annules . 48 offres
   par la sequence)                                      sans etat . 9 compromis actifs .
                                                         4 offres acceptees . 2 proposees
                                                         . 1 refusee -- dont 27033 et 28155,
                                                         les 2 compromis SANS DATE que la
                                                         fermeture du 12/11 a annules
```

### 2.3 La TRANSACTION

```
meme numero Hektor sur deux lignes        0     dur      temoin vu
classeur portant un numero Hektor          0    dur      temoin vu
nee dans l'app, jamais numerotee           0    a juger  temoin vu -- les 340 de la plage
                                                         app ont TOUTES un numero Hektor
sans bien . genre inconnu                0 . 0  dur      temoins vus
⭐ TRANSACTION DU CLASSEUR QUI DOUBLE      24   a juger  meme bien, meme genre, meme jour :
   UNE TRANSACTION DE HEKTOR                             10 offres, 14 compromis -- et les 24
                                                         sont dans un AUTRE dossier que leur
                                                         original. Ce sont les « copies de C5 »
                                                         de la 1re session (elle en comptait
                                                         25). Liste nominative dans le CSV.
offre sans etat                           48    constat  toutes sans date non plus
etat d'une offre contraire au journal     11    a juger  7 ont un journal NON DATE
   que tient Hektor                                      (« 0000-00-00 ») : l'ordre n'y veut
                                                         rien dire ; 4 sont datees (7181,
                                                         9452, 27136, 28917). ⭐ AUCUNE n'est
                                                         touchee par nos 1 236 gestes.
```

### 2.4 L'ÉTIQUETTE

```
bijection etiquette <-> chaine <-> numero  0    dur      11 590 = 11 590 = 11 590
transaction sans etiquette ni numero       0    dur      temoin vu
numero sans annee vraie                   13    a juger
   D1990 x7  le compromis du dossier est date 1990-01-01 CHEZ HEKTOR (une date bouche-trou)
   D0000 x6  5 offres seules dont la SEULE date est NOTRE refus du 12/11 (la fermeture des
             dossiers impossibles : 10802, 10810, 10816, 23139, 28724) -- la numerotation a
             REFUSE cette date fabriquee, et c'est juste ; + 1 compromis date 0000 chez Hektor
```

### 2.5 La LECTURE (ce que le run relit)

```
transaction PRESENTE que le run ne revoit  2    a juger
   plus depuis la nuit du 26/10
     offre 30712    Hektor 33094  acceptee  vue la derniere fois le 26/10
     offre 1001361  Hektor 33098  proposee  vue la derniere fois le 26/10
   bien 61672, « Sous compromis » ; le meme dossier porte une offre 30767 (Hektor 33118)
   ACCEPTEE et un compromis 30769, vus cette nuit, nes le 27/10.
   ➡ Tout porte a croire que les deux offres ont ete REMPLACEES chez Hektor le 27/10 ; le
     run ne les voit plus, mais ne les marque pas absentes. C'est la SEULE cause du seul
     dossier « a deux offres acceptees ». ⚠ La cause du drapeau qui ne tombe pas n'est PAS
     mesuree.
```

---

## 3. LES SIX INVARIANTS QUE LE DOSSIER DEMANDAIT D'ÉCRIRE

```
1 l'ordre des dates dans une chaine      15 blocs apres la vente . 6 ventes avant leur
                                          compromis . 275 offres > 31 j apres le compromis
2 une offre refusee posterieure a sa     lu comme « une offre que NOUS avons refusee dans un
  vente                                   dossier qui a abouti » : 1, l'offre 14420 (affaire
                                          14420, dossier 14419), le 20e refus a tort du 11/11,
                                          LAISSEE PAR DECISION. ⭐ Aucun autre n'est apparu
                                          depuis, malgre la regle D et les 138 scissions.
3 un compromis sans mandat               2 713 compromis (2 444 actifs, 269 annules) sans
                                          numero ni identifiant de mandat ; aussi 2 750 offres
                                          et 2 481 ventes. ⚠ C'est de la COMPLETUDE (vieilles
                                          fiches Hektor), le chainage ne lit pas le mandat.
4 une transaction sans bien              0
5 un acquereur absent                    335 compromis . 166 offres . 348 ventes sans aucun
                                          identifiant d'acquereur : le chainage ne peut les
                                          relier que par la SEQUENCE, jamais par le nom
6 une chaine dont tous les membres       2 134 dossiers sans vente ni compromis vivant ni
  sont morts                              offre vivante -- des affaires ECHOUEES, c'est
                                          normal . et 15 dossiers tout entiers effaces chez
                                          Hektor (2.1)
```

**Les autres comptes du § 6 du dossier, remesurés :**

```
dossiers a UNE seule transaction        1 472   ✅ identique
   603 offres refusees PAR NOUS (refus du 10/11 ou apres) . 420 offres refusees par Hektor
   . 220 compromis annules . 135 du CLASSEUR (96 offres refusees, 35 compromis annules,
   4 offres acceptees) . 47 offres acceptees . 29 ventes . 10 compromis actifs . 8 proposees
   ⭐ LES 603 SONT LE DESSIN, PAS UN ACCIDENT : une offre refusee ferme sa propre chaine
     (l. 2101). La question « avions-nous raison de les refuser ? » est celle du temps 3.
ventes sans aucune offre                  460   (le dossier disait 461)
ventes sans aucun compromis               113
dossiers a deux acquereurs ou plus      2 246   ✅ identique (par hektor_acquereur_id) ;
                                                 3 972 si l'on compte chaque membre d'un
                                                 couple -- c'est normal, le contact change
transactions creees depuis le Sheet       190   dont 135 seules dans leur dossier ✅
```

---

## 4. ⭐ LES GESTES, OBJET PAR OBJET — créer, modifier, supprimer, lire

> Règle du 21/09 : un audit balaie les GESTES autant que les OBJETS. Une case non mesurée se dit.

### L'OFFRE, LE COMPROMIS, LA VENTE

```
CREER      par HEKTOR (relues la nuit)        30 829
           par L'APP (plage >= 1 000 000)        340   toutes numerotees par Hektor ; 315
                                                       nees en aout (126 offres, 120 compromis,
                                                       69 ventes) -- ⚠ leur ORIGINE (quel geste,
                                                       quel script en aout) n'est PAS mesuree
           par LE CLASSEUR (C5, patch)           190   24 doublent une transaction de Hektor
                                                       (2.3) ; 5 retirees le 18/11 (doublons)
           ⛔ aucun travail du journal ne CREE une offre seule : la creation passe par le
             statut de l'annonce (Offre / Compromis / Vendu) -- 118 gestes humains, sur
             11 biens seulement (des biens d'essai pour l'essentiel)
MODIFIER   l'ETAT    1 236 gestes de masse (temps 1, dont la cascade d'un geste humain)
                     + 36 autres gestes humains (26 offres, 10 compromis)
                     . 11 etats contraires au journal Hektor, aucun de nous
           les CHAMPS par le carnet app_affaire_champ_app : 49 lignes en tout (creation_app,
                     modification_app ; « arrivee » ou « sans_objet »), protegees par R2
                     . par PATCH : C2, C3, C4, C8 sur les colonnes *_app (temps 1 § 6)
           la DATE   1 205 dates d'offre deplacees par nos refus -- le chainage n'y est pas
                     sensible (_date_de_tri lit la 1re proposition)
SUPPRIMER  par L'APP     28 au journal des suppressions app_affaire_supprimee (16 compromis
                         + 9 ventes « geste_app », 1 + 2 « menage_verifie »), toutes
                         serveur_aligne -- dont les « 3 disparues » du plan (temps 1 § 7)
           par HEKTOR    19 lignes numerotees « absentes » (12 compromis, 6 offres, 1 vente)
                         CONSERVEES (decision du 13/11) ; 15 dossiers entierement effaces
           par PATCH     les 5 doublons C5 (18/11) et le cobaye A2 (16/11) : ⚠ ils ne sont
                         PAS au journal des suppressions (ils ont leur sauvegarde datee)
           une OFFRE     ⛔ aucun geste n'existe pour supprimer une offre (aucun type de
                         travail) -- NON MESURE au-dela
           ce qui reste  6 notes et 5 conditions orphelines, toutes sur les transactions
                         d'essai supprimees du bien 24113 (1001388 a 1001395) ; la
                         sentinelle data.affaire_note_condition_orpheline est VERTE, elles
                         sont declarees
LIRE       le run        toutes les transactions numerotees et presentes relues cette nuit,
                         SAUF 2, non revues depuis le 26/10 (2.5)
           les 2 copies  local = Supabase, 0 ecart
           l'ecran       0 divergence avec le run (controleur ①)
```

### LE DOSSIER

```
CREER      par le recalcul de nuit (11 590) ; par l'app, en optimiste, via app_chaine_pour
           -- ⚠ le controleur le dit : app_chaine_pour ne sait pas refaire la regle B, une
           offre acceptee saisie APRES son compromis ouvrirait un dossier que la nuit recolle
MODIFIER   REDEDUIT chaque nuit sur l'etat final ; rejeu de la vraie fonction : 0 ecart
SUPPRIMER  absorbe par une regle (C, B, D) ou un rattachement manuel ; un dossier tout
           efface chez Hektor GARDE son numero (15)
LIRE       l'ecran (dossiersOuvertsDuBien) : 0 divergence
```

### L'ÉTIQUETTE

```
CREER      pose          11 452 evenements, 31 163 transactions (dont 11 441 le 12/11 a 23:08)
MODIFIER   scission        143 evenements, 147 transactions -- 0 etiquette neuve disparue
           propagation       6 evenements, 6 transactions
SUPPRIMER  fusion            6 evenements, 9 transactions
             5 le 13/11 : de VRAIES absorptions -- les 5 etiquettes absorbees n'existent
               plus, et ce sont exactement les 5 « poses » du 12/11 qu'on ne retrouve plus
               (D2024-0007, D2020-0178, D2025-0131, D2006-0088, D2025-0075) : conforme
             ⚠ 1 le 18/11 (D2025-0219, dossier 14006, « absorbe » a633d3ec) N'EST PAS UNE
               FUSION : elle n'a deplace QU'UNE transaction, 1001593 -- une offre du
               CLASSEUR, copie de l'offre Hektor 14008 -- et l'etiquette « absorbee »
               a633d3ec VIT TOUJOURS sur son dossier (D2025-0365 : 14007 et 14009).
               Le journal l'appelle fusion ; c'est un TRANSFERT d'une transaction.
               ➡ Pour la 5.2 : le controle propose (« un UUID publie qui n'existe plus »)
                 ne verrait pas ce cas-la -- c'est l'APPARTENANCE de 1001593 qui a change.
LIRE       le Sheet (colonne affair_uuid) : 0 ecrite -- c'est l'etape 5.2
```

---

## 5. CE QUI TOUCHE NOS GESTES — sans encore rien attribuer

Ce temps ne rejoue rien (c'est le temps 3). Il dit seulement **quelles anomalies portent une
transaction touchée par un des 1 236 gestes** du temps 1 :

```
l'offre refusee dans un dossier vendu      1 sur 1    14420 -- connue, laissee par decision
les offres > 31 j apres le compromis       9 sur 275
les numeros D0000 / D1990                 10 sur 13   mais la cause est la DATE : 1990 chez
                                                      Hektor (5) ; notre refus, seule date,
                                                      que la numerotation a refuse (5)
les compromis sans date de tri             2 sur 260  27033 et 28155, annules par la
                                                      fermeture du 12/11 -- ils etaient deja
                                                      sans date
les etats contraires au journal            0 sur 11
les blocs apres la vente                   1 sur 15   14420 encore
les dossiers d'une seule transaction     603 sur 1 472  le dessin (une offre refusee ferme sa
                                                      chaine)
les copies du classeur                    24 sur 24   nos creations C5
```

---

## 6. CE QUE JE N'AI PAS MESURÉ

```
. pourquoi le run ne marque pas absentes les offres 30712 et 1001361 (bien 61672)
. l'origine des 315 transactions nees dans l'app en aout (quel geste, quel script)
. les 275 offres > 31 j : correction ou casse -> le rejeu du temps 3
. si les 14 « blocs apres la vente au meme acheteur » sont une date de vente fausse chez
  Hektor ou une revente : le controleur du projet le presume par le montant, je ne l'ai pas
  verifie chez Hektor
. la creation de ventes par le statut « Vendu » bien par bien (reel ou essai)
. l'etat CHEZ HEKTOR des 12 compromis du temps 1, hors du registre
```
