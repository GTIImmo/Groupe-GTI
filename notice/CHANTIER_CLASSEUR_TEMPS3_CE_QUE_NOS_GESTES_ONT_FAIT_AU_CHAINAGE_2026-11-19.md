# TEMPS 3 — CE QUE NOS GESTES DE MASSE ONT FAIT AU CHAÎNAGE, PROUVÉ PAR LE REJEU
### 19/11/2026 · chantier classeur, conduit par `notice/PROMPT_FINIR_LE_CHANTIER_CLASSEUR_2026-11-19.md`

> ⛔ **LECTURE SEULE DE BOUT EN BOUT.** `phase2.sqlite` et les photos sont ouverts en `mode=ro` ;
> tout le travail se fait dans des bases **en mémoire**, jetées à la fin. Rien n'est écrit en base,
> chez Hektor ni dans le Sheet.
>
> **Rejouer la mesure** (~3 min) — décompresser d'abord la photo du 10/11 hors du projet :
> ```
> gzip -dc C:\Hektor\Backups\critical\critical_20261110_080002.sqlite.gz > <dossier>\critical_20261110.sqlite
> .venv\Scripts\python.exe -X utf8 phase2\checks\temps3_rejeu_du_chainage_sans_nos_gestes_2026-11-19.py --photo <dossier>\critical_20261110.sqlite
> ```
> Sortie 0 le 19/11 (2 si un témoin échoue). Il écrit `notice/TEMPS3_PAIRES_CHANGEES_2026-11-19.csv`
> (196 paires) et `notice/TEMPS3_DOSSIERS_CHANGES_2026-11-19.csv` (85 dossiers).

---

## 0. EN UNE PAGE

```
⭐ LA PHOTO D'AVANT EXISTE. La sauvegarde locale de 08:00 (C:\Hektor\Backups\critical)
   contient app_affaire_ledger EN ENTIER, chaque jour : celle du 10/11 a 08:00 porte
   31 145 transactions, AVANT le premier geste (16:13). Le dossier disait le contraire --
   il n'avait regarde que les sauvegardes datees de Supabase.

NOS 1 236 GESTES D'ETAT (temps 1), rejoues avec la VRAIE fonction et les regles d'aujourd'hui :
   sans eux 11 511 dossiers . avec eux 11 590
   82 dossiers ont change de composition, TOUS sur les biens touches :
      79 COUPES . 3 REUNIS
   250 transactions y ont change de compagnie, dont 78 touchees par nos gestes et
   172 par RICOCHET ; les 1 139 autres transactions touchees n'ont PAS bouge -- la regle § 2.3
   (« le compromis annule rejoint l'offre refusee du meme acquereur ») les a gardees :
   elle recolle 863 compromis avec nos gestes, 338 sans eux.

LES 79 DOSSIERS COUPES, au verdict de leur pire paire separee :
    5  CASSE           le MEME numero d'acquereur se retrouve dans deux dossiers
   10  CASSE PROBABLE  le MEME nom de famille sous deux fiches Hektor
   48  A JUGER         37 noms differents a moins d'un mois et meme montant (le contact a
                       pu changer chez Hektor) . 2 montants differents . 9 sans acquereur
   16  CORRECTION      deux acheteurs differents a plus d'un mois : le geste a SEPARE deux
                       affaires que le chainage avait melangees
   -> 74 de B (rattrapage de la cascade, 11/11 19:01) . 4 de A (refus par la table)
      . 1 RICOCHET de D (fermeture du 12/11) . 0 de E

LES 190 CREATIONS C5 (16/11), l'autre geste de masse, hors du journal des travaux :
    3 dossiers de HEKTOR recomposes (1 casse : bien 33458 ; 2 sur les biens CROISES
      5262 et 24733) . 135 creations seules dans leur dossier

§ 8.3 ① CONFIRME PAR LE REJEU : defaire l'ETAT seul, en gardant les dates et les journaux
   d'aujourd'hui, redonne EXACTEMENT le meme resultat. Les 1 205 dates deplacees n'ont RIEN
   fait au chainage. Tout vient de l'etat.

LES TEMOINS -- tous verts
   positif       aujourd'hui rejoue = la base, 0 ecart sur 31 359
   aller-retour  refaire nos gestes sur l'etat d'avant redonne aujourd'hui, 0 ecart
   inverse       0 transaction d'un bien NON touche ne change de dossier
   la photo      etat 1 215/1 217, journal 1 217/1 217 (les 2 ecarts s'expliquent, § 2)
```

⭐ **La réponse à la question de Frédéric** (« nos écritures de masse ont-elles perturbé ou cassé du
chaînage ? ») : **oui, mais peu, et c'est localisé.** 1 236 gestes ont recomposé 82 dossiers sur
11 590. **15 sont des casses** (5 sûres, 10 probables), **16 des corrections**, **48 se jugent**. Et
toutes les casses sûres ont **une seule et même cause** : un **compromis annulé sans date** (§ 4).

---

## 1. ⭐ LA PHOTO D'AVANT — elle existait, chaque matin

`phase2/sync/backup_critical.py` sauve chaque jour à 08:00 vingt tables locales, dont
**`app_affaire_ledger`** (l. 116 : *« la série d'identité des transactions »*). Rétention 90 jours.

```
photo          transactions   dossiers   ce qu'elle porte
10/11 08:00        31 145      12 140    AVANT TOUT GESTE (le 1er essai est a 16:13)
11/11 08:00        31 151      12 109    apres les 3 essais et la nuit (les regles A, B, C
                                         ecrites le 10/11 a 14:27 ; leur allumage n'est date
                                         nulle part)
12/11 08:00        31 151      12 174    apres A (523) et B (661) : +65 dossiers
13/11 08:00        31 157      11 442    apres D, E et LA REGLE D : -732 dossiers
```

⭐ Le « témoin 31 145 / 31 145 » des simulations du 10/11 est **cette photo-là**. ⚠ Le dossier
écrivait *« il n'existe AUCUNE photo complète du registre d'avant »* : c'était vrai des sauvegardes
datées **de Supabase** (178, 5, 2 et 1 lignes), pas des sauvegardes **locales**.

---

## 2. LA MÉTHODE — la vraie fonction, trois registres en mémoire

```
N   le registre local d'aujourd'hui (lu en mode=ro), recalculer_les_chaines() rejouee dessus
R   le meme, NOS 1 236 GESTES DEFAITS :
       l'etat     celui d'avant le PREMIER geste de chaque transaction, lu dans la charge
                  (et reconstitue depuis B pour les 19 de E -- temps 1)
       le journal les entrees « refus » / « accepte » du 10 au 12/11 retirees (1 224)
       la date    reprise de la PHOTO du 10/11 (elle n'est dans aucune charge) -- 1 217/1 217
C   N sans les 190 transactions creees depuis le classeur (C5)
➡ MEME FONCTION, MEMES REGLES (les 9 interrupteurs d'aujourd'hui, les 6 rattachements a la
  main), MEMES DONNEES A NOS GESTES PRES. Toute difference N / R est l'effet de nos gestes
  d'etat ; toute difference N / C, l'effet de C5.
```

**La photo juge la reconstitution** : sur les 1 217 transactions touchées, le journal est
identique 1 217 fois, l'état 1 215 fois. Les 2 écarts (offres **9557** et **16255**) ne sont pas
des erreurs : elles sont passées d'« acceptée » à « proposée » **entre le 10/11 et le 11/11 à
08:00** (la photo du 11/11 le montre), avant notre geste du 11/11 à 17:38. La charge dit donc vrai.

**Le classement d'une paire du même bien séparée par le geste** (les numéros d'acquéreur d'abord,
comme la règle ; le nom **seulement pour classer**, jamais pour réunir) :

```
CASSE            le MEME numero d'acquereur des deux cotes
CASSE PROBABLE   numeros differents, MEME nom de famille, meme bien (deux fiches Hektor)
A JUGER          noms differents a 31 jours ou moins (meme montant : le contact a pu
                 changer chez Hektor dans la meme affaire, 501 cas connus) ; montants
                 differents ; un cote sans acquereur ; une date qui manque
CORRECTION       noms differents a plus de 31 jours : deux acheteurs successifs
```
Un dossier coupé prend le verdict de **sa pire paire**.

---

## 3. CE QUE NOS 1 236 GESTES D'ÉTAT ONT FAIT

### 3.1 Combien, et dans quel sens

```
dossiers          11 511 sans nos gestes -> 11 590 avec (+79)
recomposes        82, TOUS sur des biens touches (le temoin inverse le prouve)
   coupes         79
   reunis          3   (biens 28422, 39360, 47557 -- deux portent une creation C5, § 5)
paires changees  183   (124 offre-compromis . 38 offre-offre . 12 offre-vente
                        . 6 compromis-compromis . 3 compromis-vente)
dont 25 RICOCHETS : aucun des deux membres n'a ete touche -- le chainage recompose le BIEN
                    entier quand une seule de ses transactions change d'etat
```

⭐ **Pourquoi si peu sur 1 236 gestes.** Refuser une offre ferme sa chaîne (l. 2101), mais la
règle V2 § 2.3 rattache ensuite le compromis annulé à l'offre refusée **du même numéro
d'acquéreur**. Elle a travaillé : **863** rattachements avec nos gestes contre **338** sans. Tout ce
qui portait le même numéro des deux côtés **et une date** est resté ensemble. **Ce qui s'est coupé, c'est ce que
§ 2.3 ne pouvait pas voir** : deux numéros différents, ou un compromis **sans date**.

### 3.2 Les 79 dossiers coupés, par verdict et par campagne

```
CASSE (meme numero)                5   B 4 . ricochet de D 1
CASSE PROBABLE (meme nom)         10   B 10
A JUGER (noms diff., <= 31 j,     37   B 37
   meme montant)
A JUGER (<= 31 j, montants diff.)  2   B 2
A JUGER (un cote sans acquereur)   9   A 4 (des offres refusees + un compromis C5 sans
                                        acquereur) . B 5
CORRECTION                        16   B 16
                                  --
                                  79   B 74 . A 4 . D 1 (ricochet) . E 0
```
➡ **B — le rattrapage de la cascade, 661 offres en 1,3 seconde le 11/11 à 19:01 — porte 74 des
79.** C'est le seul geste qui refusait une offre **à cause** de son compromis annulé, donc le seul
qui ait systématiquement touché des paires offre + compromis.

### 3.3 ⛔ Les 5 casses (le même numéro d'acquéreur dans deux dossiers)

```
bien 41481  DEBARD     compromis 20088 annule SANS DATE | offres 20089 (refusee par B), 20090
            -> PURE : tout est DEBARD. C'est le « 5QE9107L » du dossier § 8.2.
bien 39745  POCHELON   compromis 19070 annule SANS DATE isole de 19069 et 19072 (POCHELON) ;
            l'offre 19071 de SAS FANGET (refusee par B) part a part -> MIXTE : le geste a
            CORRIGE (separe SAS FANGET) ET CASSE (isole le compromis sans date). « 8SZDU4F5 ».
bien 3481   THEVENON   compromis 1335 annule SANS DATE isole de 1334 et 1337 (THEVENON) ;
            l'offre 1336 d'EL FAQRAOUI (refusee par B) part a part -> MIXTE
bien 28653  GENOUX     compromis 14110 annule SANS DATE isole de 14109, 14111, 14113, 14115
            (GENOUX, avec la VENTE) ; l'offre 14112 de MOURETTE (B) part a part -> MIXTE
bien 39360  DEBARD     compromis 18984 et vente 30581 separes -> RICOCHET de D (la fermeture
            du compromis 18985 sur le meme bien, 12/11) ; aucun des deux n'a ete touche
```

⭐⭐ **Une seule cause pour les quatre premières : un COMPROMIS ANNULÉ SANS DATE.** Sans date, il
n'entre pas dans la séquence ; la règle A le rattache à « l'unique offre **acceptée** seule » du bien.
Notre refus a retiré l'« acceptée » : la règle A n'a plus de cible, et § 2.6 refuse une chaîne qui
porte déjà un compromis. **C'est le « trou de règle » du § 8.4 du dossier, et le rejeu prouve
maintenant que NOS GESTES l'ont ouvert** pour ces quatre dossiers.

### 3.4 Les 10 casses probables (le même nom de famille, deux fiches Hektor)

```
bien 10955 RIGHI . 11014 SOULEZ . 27037 DZAMAN . 35702 BOUGEARD . 36712 ARSAC ET DUMAS
. 41584 GAGNE . 42883 VERILHAC . 44276 MILHAS . 52724 PARIS . 55040 HAHNEL
```
Toutes de B, toutes de la forme **offre refusée par nous + compromis annulé, même nom, numéros
différents** : avant, l'offre **acceptée** attirait le compromis ; refusée, elle ne l'attire plus, et
§ 2.3 compare les **numéros**, pas les noms. On y retrouve 4 des 5 cas que le dossier avait nommés
(BOUGEARD, ARSAC ET DUMAS, MILHAS, PARIS) ; ⚠ ROCHELEMAGNE n'y est pas (son nom n'est peut-être pas
écrit de la même façon des deux côtés : non vérifié).

### 3.5 Les 48 à juger, et les 16 corrections

Les **37** « noms différents, moins d'un mois, même montant » sont **ou** la même affaire dont
Hektor a changé le contact (501 cas connus), **ou** un autre acheteur au même prix. ⛔ **Le registre
seul ne peut pas trancher** — c'est précisément ce que le Sheet sait : **une ligne du classeur qui
porte les deux transactions dit « même affaire »**. Le juge de ces 37 est donc **au temps 4**, par le
gel, et pas une règle.

Les **16 corrections** sont des dossiers où une offre **acceptée** d'un premier acheteur, restée
ouverte des années, attirait le compromis d'un **autre** acheteur venu plus d'un mois après. Le refus
les a séparés : **le chaînage a raison**, c'est la famille des « 65 deux acheteurs différents » du
§ 8.2 (une partie seulement : les autres n'étaient pas réunies avant nos gestes).

---

## 4. CE QUE LES 190 CRÉATIONS C5 ONT FAIT AUX DOSSIERS DE HEKTOR

```
3 dossiers de Hektor recomposes par la seule PRESENCE des creations :
   bien 33458   compromis 16197 actif SANS DATE separe de sa vente 16198 (meme acquereur)
                -> CASSE, et encore un compromis SANS DATE
   bien  5262   le dossier 1874 coupe en deux (1874 / 1875) -- l'offre 1876 « croisee »
   bien 24733   le dossier 11956 coupe en deux (11956 / 11957) -- l'offre 11958 « croisee »
                -> ce sont deux des « affaires croisees entre acheteurs successifs » de la
                   1re session : la creation a SEPARE deux acheteurs (a juger, pas une casse)
135 creations seules dans leur dossier (sur 190) . 24 copies de Hektor, toutes dans un autre
dossier que leur original (temps 2)
```
⚠ Et les **3 réunions** du § 3.1 touchent C5 : bien **28422** (le compromis 14006 rejoint par
**1001593**, la copie C5 de l'offre 14008 — c'est la « fausse fusion » d'étiquette du 18/11, temps 2
§ 4) et bien **47557** (la copie **1001561** rejoint le dossier de 23993-23997).

---

## 5. LES DEUX FAUSSES PISTES DU § 8.3

```
① « le geste du 11/11 a casse le chainage par la DATE »  -> FAUX, ET C'EST MAINTENANT PROUVE
   PAR LE REJEU : defaire l'ETAT seul, en gardant les 1 205 dates et les 1 224 entrees de
   journal d'aujourd'hui, redonne EXACTEMENT R (0 ecart). Tout l'effet vient de l'etat.
② « 33 lignes a cheval le 12/11, 255 aujourd'hui »       -> NON TRAITE ICI : c'est une mesure
   SUR LE GEL (des lignes du Sheet), donc du temps 4. Ce temps-ci en donne la part chainage :
   79 dossiers coupes par nos gestes d'etat, 3 + 135 par C5.
```

---

## 6. CE QUI SE RÉPARE PAR UNE RÈGLE, ET CE QUI SE RÉPARE À LA MAIN — *des pistes, rien n'est décidé*

```
LES 4 CASSES « COMPROMIS ANNULE SANS DATE »   UNE REGLE est possible : laisser la regle A
   (+ 33458 de C5, compromis ACTIF sans date)   rattacher un compromis annule sans date a
                                                l'offre du MEME NUMERO d'acquereur meme REFUSEE.
                                                A mesurer d'abord, derriere un interrupteur,
                                                sur tout le registre (le § 8.4 du dossier en
                                                compte 41 de la meme forme). ⛔ Son « vas-y ».
LES 10 « MEME NOM, DEUX FICHES »               A LA MAIN : 10 lignes du fichier des
                                                rattachements manuels -- SA decision. Une regle
                                                par le nom est contraire au principe du projet.
LES 37 + 2 A JUGER                              LE SHEET TRANCHE (temps 4) : une ligne qui porte
                                                les deux transactions dit « meme affaire ».
LES 9 SANS ACQUEREUR                            A LA MAIN, ou par le Sheet.
LES 16 CORRECTIONS                              RIEN : le chainage a raison.
LE RICOCHET 39360 (DEBARD)                      a regarder : deux ventes au meme nom sur le bien
⛔ ET ON NE DEFAIT PAS LES REFUS : B est juste sur le fond (un compromis annule tue l'offre) ;
   c'est le chainage qui ne savait pas garder ensemble ce que le refus n'a pas separe.
```

---

## 7. CE QUE JE N'AI PAS MESURÉ

```
. l'effet de nos gestes avec les regles DE L'EPOQUE (le rejeu applique celles d'aujourd'hui,
  expres : c'est ce qui isole le geste) -- la photo du 12/11 dit seulement +65 dossiers en
  une nuit, regles A B C sans la D
. le lien avec les lignes du Sheet (les 255 « a plusieurs etiquettes ») : temps 4
. pourquoi ROCHELEMAGNE n'est pas dans les « meme nom »
. l'effet des 5 doublons C5 retires le 18/11 et du cobaye A2 (crees puis retires : effet net
  nul sur le registre d'aujourd'hui, non rejoue a part)
```
