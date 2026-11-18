# L'AUDIT INDÉPENDANT DU CLASSEUR CONTRE LE REGISTRE — 18/11/2026 (session neuve)

> Demandé par Frédéric le 18/11 : *« fais ton propre audit du Sheet contre mon registre
> des transactions » … « trouver pour chaque ligne du Sheet son dossier de transactions —
> donc trouver nos erreurs »*, puis *« ton verdict, ligne par ligne, sur les 277 liens
> “à valider” et les 91 lignes sans lien »*.
>
> ⛔ **Ce document DÉCRIT ; le plan DÉCIDE.** La source de vérité reste
> `notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md`. Rien ici n'est une décision prise.
> ⛔ **Tout est en LECTURE SEULE**, sauf un geste, accordé et noté au plan (§ 4.6).

---

## 0. EN UNE PAGE

```
LE SHEET          4 795 lignes (notre table en connait 4 794 : 1 ligne NEE depuis)
LE GEL            12 787 liens . 4 703 lignes . 11 964 liens tombent AU JOUR PRES
MON APPARIEMENT   fait SANS le gel, sans aucune valeur posee par nous
                  4 402 lignes : MEME dossier que le gel, avec preuve interne
NOS ERREURS       des liens faux par un seul signal faible (nom ou mandat seul)
                  des affaires CROISEES entre acheteurs successifs d'un meme bien
                  25 transactions creees par C5 qui COPIENT une transaction Hektor
                  des valeurs posees (C2, C3, C4) sur la MAUVAISE transaction
                  136 transactions creees, COUPEES de leur dossier cette nuit
UN GESTE FAIT     les 5 doublons du 18/11 retires AUSSI du registre local (§ 4.6)
UN PATCH DORMANT  la correction du gel : 141 operations sur 87 lignes (55 liens retires,
                  109 ajoutes), sans lien 91 -> 60 -- il attend son accord (§ 5 bis) ;
                  la liste complete, les 33 questions et le run/workers : § 5 ter
```

---

## 1. LES MESURES DU § 2 DU DOSSIER DE REPRISE, REJOUÉES (chez Supabase, en direct)

Presque tout tient, au chiffre près : 4 794 lignes connues, 4 703 appariées, 91 sans lien,
12 787 liens sur 12 787 transactions distinctes, confiance 12 484 / 26 / 277, rôles
4 676 / 4 376 / 3 735, 9 liens cassés bénins, 1 ligne hors jeu ; C8 3 729 / 3 671 ;
C3 450 ; C4 169 motifs en 6 libellés, 4 325 notes, 28 conditions, catalogue à 6 ;
C2 66 + 6 ; C1 7 + 853 ; C9 2 588 + 2 560 ; 4 515 affaires avec une note du classeur ;
31 356 transactions.

**Ce qui avait changé, ou était faux :**

```
C5 / D1       190 transactions creees, PAS 195 : les 5 offres en double ont ete
              retirees le 18/11 (59 acceptees, plus 64)
277 liens     = 104 LIGNES seulement, tous de l'etage 9 (« sans mandat,
              acquereur + vendeur »), geles le 29/10
le Sheet      4 795 lignes : 54376c72 est nee (mandat 18993, offre du 11/11/2026,
              en cours -- regle n° 1 : rien a reprendre)
non posees    207, pas 202 : 3 sorties (dont bdb548a3, repare le 18/11), 8 entrees
              -- la ligne hors jeu (2) et 5 offres qui ont PERDU leur lien
              (0GV2LNV2, H6CTRVR6, c08ff7cb : leur vraie offre est tenue par une
              ligne soeur, voir § 4.2)
              ⚠ RELU LE 19/11 : les causes nommees n'expliquent que 7 entrees
              (2 + 5), et le croisement de c08ff7cb (offre 3678 tenue par
              721e650c) n'est PAS regle par le patch (§ 5 ter I)
etiquettes    la nuit du 17 au 18/11 a COUPE 136 transactions creees de leur
              dossier (§ 4.5). Le plan disait le 16/11 « 195/195 heritent ».
```

Les 36 lignes tranchées et les 13 arbitrages : **aucun geste n'est posé**, sauf `53ZS73KW`.
Ses 13 réponses dans la page d'arbitrage (`reponses2`) n'ont pas bougé depuis l'après-midi.

---

## 2. LA MÉTHODE, ET POURQUOI ELLE N'EST PAS CIRCULAIRE

⛔ **Le piège n° 1 (accord circulaire)** : nous avons déjà posé 15 211 valeurs du classeur.
D'où les **règles d'indépendance** :

1. le gel n'est lu **qu'après**, pour comparer — jamais pour choisir ;
2. aucune valeur posée par nous ne sert de preuve (colonnes `*_app`, notes et conditions
   « classeur », répartition `classeur_reconstitue`, carnet des mandats « classeur », avis) ;
3. les 190 transactions **créées depuis le Sheet** sont retirées des candidats ;
4. la date d'une offre est sa **première proposition** (`propositions_json`) ; un refus ou une
   acceptation datés à partir du 11/11/2026 (nos gestes) ne prouvent rien.

**Les familles de preuve, toutes venues de Hektor, de MODELO ou de la ligne elle-même :**

```
lien    l'annonce que L'AGENCE a nommee : lien d'administration (id=), et surtout
        ⭐ la REFERENCE NETTY (VM.../VA..., colonne B ou lien CRM) = le NUMERO DE
        DOSSIER HEKTOR -> l'annonce, pour 646 lignes ; le lien d'administration
        ou du site en designe ~390 autres
mandat  le numero du Sheet porte par une transaction, ou le registre des mandats
modelo  le numero du Sheet dans MODELO -> sa reference produit -> l'annonce
acq     un NOM DE FAMILLE de l'acquereur (les prenoms ne comptent pas)
vend    un NOM DE FAMILLE du vendeur (mandants, registre, MODELO)
dates   ⭐ LA PREUVE INTERNE : une transaction du bon genre AU JOUR PRES
prix    a 1 % pres . ville
```

⚠ Les liens « neosphere / rodacom » (3 800 lignes) portent un identifiant **étranger** : ils
ne désignent rien chez nous.

---

## 3. LE RÉSULTAT GLOBAL

**Par ligne** (4 795) :

```
A1 meme dossier que le gel, avec preuve interne           4 402
A2 meme dossier, sans preuve interne                          22
A3 meme dossier, mais le gel s'etend sur 2-3 chaines         246   (structure, § 4.5)
A4 meme dossier, AUTRE transaction pour un role               11
B1 autre dossier -- le mien prouve, celui du gel non           3
B2 autre dossier -- les deux prouves                          11
B4 autre dossier -- aucun des deux prouve                      8
C1 sans lien -- un dossier avec preuve chez nous              39
C2 sans lien -- un candidat sans preuve                       49
C3 sans lien -- rien                                           2
nouvelle 1 . hors jeu 1
```

**Par lien** (12 787) : 11 964 tombent au jour près sur mon dossier (93,6 %) ; 190 visent une
transaction créée depuis le Sheet (circulaires par nature) ; **255 suspects**, dont :

```
201   seule transaction de ce genre sur le bien  -> desaccord de DATE, lien JUSTE
 41   d'autres transactions, aucune ne colle mieux -> lien vraisemblablement juste
 13   UNE AUTRE transaction du MEME bien tombe au jour exact -> lien FAUX
      (11 libres, 2 tenues par une autre ligne)
```

⚠ *Relu le 19/11 : ces trois comptes font 12 409 liens sur 12 787 — 378 ne sont classés nulle part. Et des
13 « liens FAUX », les juges en confirment 10 : `d1cb8dd7` et `2dfa6ef3` sont jugées JUSTES (c'est la question
de principe du § 5 ter B1), et pour `45225170` la « meilleure » transaction est elle-même un doublon (§ 5 ter I).*

---

## 4. NOS ERREURS — par famille

### 4.1 Des liens faux par UN SEUL signal faible (nom seul, ou mandat seul)

Le motif déjà nommé le 18/11, et l'apparieur le disait (confiance « à valider ») :
`1ESJE28Q`, `8Q3LHGZ4`, `NEFHS7JI`, `WJ3KA32F`, `a8aaeb2b`, `Y51UMZHY`… — le détail est
au verdict ligne par ligne (§ 5).

### 4.2 Des affaires CROISÉES entre acheteurs successifs d'un même bien

Sur un bien revendu, ou repris après une annulation, le gel a donné à une ligne l'offre (ou le
compromis) de l'acheteur **suivant**, et la ligne de l'acheteur suivant est restée sans elle.

```
TR42PT5H <-> 739a0db1   bien 53398 : offre 27196 et compromis 27195 croises
3W10AEIK  -> 0GV2LNV2   l'offre 4747 tombe au jour pres pour 0GV2LNV2
E9GL6MUS  -> H6CTRVR6   l'offre 11415 tombe au jour pres pour H6CTRVR6
VEP1DVQ4 <-> 2SCBZXMH   offres 7780 / 7781
DAMOO7OU  -> TRJ5Y59U   offre 23995
FLPUUSY3  -> A07EC3DH   offre 1876
9UO5NUN6  -> 3S4ZWOFK   offre 11958
427UDDSF  -> 9Q0FHAKK   offre 3648 et vente 3650
OXQSBZ9V  -> 515RUEN3   offre 17430 (515RUEN3 prend aussi le compromis 17428)
OXQSBZ9V  -> 87QOXR64   compromis 17427            [ligne corrigee le 19/11]
RX6J289Y <-> CITFQGOB / R0JRVFDC   compromis 16377 / 16378
Q602VZJX <-> EGR8KXOL   compromis 6554 / 6555
```

⚠ *Relu le 19/11 : le patch règle six croisements de plus que cette liste — 08GV8OMZ → O1099YC0 (6341),
QJQ9M4OF → D9MMB7OU (17366), KT0601S6 → PPIM4947 (24291), 3308P0UX → 9WQ204HP (4480), SBH4QWDW → VMWFLLW4
(23050), V3FO5NDA → 6FQO29C8 (19131, 19133).*

### 4.3 ⛔ C5 a créé 25 COPIES de transactions Hektor

Sur les 190 transactions créées depuis le Sheet, **25 copient une transaction Hektor du même
bien, du même genre, au jour près** (10 offres, 15 compromis) :

```
18   l'originale est tenue par une LIGNE SOEUR (consequence du § 4.2)
 7   l'originale est LIBRE -- C5 l'a cherchee par la colonne `date`, abimee par nos
     gestes du 11-12/11 : la MEME cause que les 5 doublons retires le 18/11, mais
     hors du seul lot (« offres vente reglee ») que le patch avait balaye
```

Liste : `sortie/c5_copies_probables.json` de l'audit (§ 7). Exemples : 1001520 (copie de
27196), 1001482 (5055), 1001480 (20075), 1001536 (20073), 1001540 (23050), 1001561 (23995),
1001563 (1876), 1001580 (11958), 1001534 (17427), 1001542 (16377).

⛔ **Les retirer est une écriture en production, des DEUX côtés** (§ 4.6) — à décider.

### 4.4 Des valeurs posées sur la MAUVAISE transaction

Par un lien faux, C3 et C4 ont posé une date d'annulation, un motif ou une note sur la
transaction d'une **autre** affaire. Exemples relevés par les juges : 27195 (date
2026-07-27 de 739a0db1, l'affaire MORAND/ZIMMER est annulée le 20/05/2025), 12952 (2024-09-24
sur un compromis de 2012), 26395, 8321, 26613, 16377, 4496, 11138. Et C2 : 998 porte
1 000 € de commission du garage de `a8aaeb2b`.
➡ **Avant de poser les 33 commissions tranchées**, retirer de la pose celles dont le lien est
faux ou douteux (au moins `8RWTD0YX`, `0bc98552`, `NEFHS7JI`, `61OW86CS`, `CITFQGOB`,
`774aa002`, `5QE9107L`, `Q602VZJX`).
⚠ *Corrigé le 19/11 : `0bc98552` est jugée JUSTE (son seul problème est le doublon 21803/21805) ; il faut ajouter
`V3FO5NDA` (elle n'aura plus ni compromis ni vente) et `RX6J289Y` (elle passe à 16378, dont les honoraires valent
les 10 000 du Sheet). Et 26613, cité plus haut, ne part pas : sa ligne `SHN6RKDI` est INCERTAINE.*

### 4.5 La SCISSION de cette nuit : 136 transactions créées coupées de leur dossier

Le chaînage de nuit est une **déduction refaite chaque nuit** sur l'état final des
transactions : une offre « refusée » ne porte pas un compromis, un compromis « annulé » ferme
sa chaîne. Les offres refusées et compromis annulés créés par C5 ont donc ouvert **leur propre
chaîne**, et l'étiquette a suivi : journal du 18/11, **138 scissions, 142 transactions, dont 136
créées depuis le Sheet**. Elles n'avaient pas été coupées la nuit du 16 au 17 parce que le
local ne les connaissait pas encore.

```
CONSEQUENCE POUR L'ETAPE 5.2 (ecrire notre identifiant dans affair_uuid) :
   4 448 lignes liees ont UNE etiquette possible
     255 en ont PLUSIEURS (250 meme en ne comptant que les transactions vivantes)
       1 n'a plus aucune transaction vivante
```

**Le remède existe** : `phase2/sync/rattachements_manuels.csv`, lu par le chaînage
(`APP_CHAINAGE_RATTACHEMENT_MANUEL=1`). ⛔ Mais ce fichier est **une décision** : « on n'en
ajoute JAMAIS une sans lui ». Options à trancher : rattacher à la main les 136 (puis fusion
des étiquettes), ou laisser et choisir l'étiquette à l'export (5.2).

### 4.6 ✅ Les 5 doublons du 18/11 restaient dans le registre LOCAL — corrigé le 18/11

Le patch du 18/11 les avait retirés **chez Supabase seulement** ; le local (le maître) les
portait, et le push de 04:00 les aurait recréés sans leur marque `classeur`. Geste accordé et
joué à 16:31 (`phase2/checks/retirer_doublons_classeur_du_local_2026-11-18.py`), tout est au
plan, contrôle du 19/11 au matin compris.

---

## 5. LE VERDICT LIGNE PAR LIGNE — 277 liens (104 lignes) et 91 lignes sans lien

**Le détail, ligne par ligne : `notice/AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv`**
(257 lignes jugées au premier tour, **350 depuis le tour des sœurs** du § 5 bis : verdict,
décision de chaque lien, transaction à rattacher, preuve, raison,
conséquences, question). Méthode : 9 juges sur des fiches complètes (une par ligne, sœurs
comprises), puis une **contre-expertise de chaque verdict qui change quelque chose ou reste
douteux** — 89 contre-expertises : **85 confirment, 4 renversent** (`O6R10ZQA` et `SHN6RKDI`
deviennent INCERTAIN ; `ea6a28a7` devient FAUX ; `V3FO5NDA` garde ses décisions mais sa raison
est corrigée : son compromis et sa vente reviennent à `6FQO29C8`).

```
LES 104 LIGNES « A VALIDER » (277 liens)
   JUSTE 94 . JUSTE SANS PREUVE FORTE 2 . PARTIEL 3 . FAUX 5
   les 277 liens : GARDER 267 . RETIRER 10
   FAUX     1ESJE28Q . 8Q3LHGZ4 . Y51UMZHY . WJ3KA32F . a8aaeb2b  (un nom seul)
            [19/11 : a8aaeb2b, DEUX signaux faibles ; et le patch retire 11 liens
             de ces 104 lignes -- la colonne liens : 269 GARDER, 11 RETIRER]
   PARTIEL  V3FO5NDA . 1D7EIYKW . f90b0418
LES 91 LIGNES SANS LIEN
   A RATTACHER 38      la transaction existe chez nous, au jour pres
   RIEN CHEZ NOUS 51   offre jamais saisie chez Hektor (ou effacee), ligne
                       « Annulee » historique d'une affaire ressaisie, en cours
   INCERTAIN 1 (YRUF0S9H) . HORS JEU 1 (53ZS73KW)
LES 62 AUTRES LIGNES (divergences de l'audit, second tour)
   JUSTE 21 . SANS PREUVE FORTE 9 . PARTIEL 21 . FAUX 7 . INCERTAIN 3 . HORS JEU 1
```

⛔ **CE QUE LA CONSOLIDATION A TROUVÉ : 7 COLLISIONS.** Appliquer les verdicts tels quels
ferait prendre une même transaction par deux lignes (6341, 17366, 6554, 19131, 19133, 4483,
23050), parce que la ligne sœur qui la tient n'a pas été jugée. Et les verdicts **citent 93
lignes sœurs** (« elle doit prendre 4747 », « elle tient déjà la bonne »…). ➡ **Aucune
correction du gel ne se pose avant que ces sœurs soient jugées** : le tour est lancé le
18/11 au soir (3 juges + contre-expertise), le plan de correction viendra après. *(Fait le 18/11 au soir : § 5 bis.)*

⚠ *Liste du premier tour, INCOMPLÈTE : les 33 questions — dont 18 sur des lignes que le patch modifie — sont
au § 5 ter B. Et `3308P0UX` y figure à tort parmi les INCERTAINES : elle est PARTIELLE, et le patch la touche.*

**LES QUESTIONS QUE SEUL FRÉDÉRIC PEUT TRANCHER** (lignes INCERTAIN) :
`YRUF0S9H` / `3308P0UX` (la même offre VIALLARD saisie deux fois : quelle ligne la garde ?) ·
`O6R10ZQA` / `T2GZOY5O` (même affaire PAOLONE, deux lignes) · `SHN6RKDI` (le compromis 26613
était-il préparé pour MOSNIER ?) · `5QE9107L` (le compromis 20088 suit-il la 1re ou la 2e offre
DEBARD ?) · et, dans les PARTIEL : `5a956cad` (une offre renégociée : l'offre d'origine ou
l'acceptée ?), `1D7EIYKW` (un compromis signé après l'annulation : seconde tentative ?),
`E9GL6MUS` (FIGARI est-elle la co-acquéreuse de SOUBEYRAND ?).

---

## 5 bis. LE TOUR DES SŒURS, ET LE PLAN DE CORRECTION DU GEL (18/11 au soir)

Les **93 lignes sœurs** citées par les verdicts ont été jugées à leur tour (3 juges, 18
contre-expertises, toutes confirment). **Bilan total : 350 lignes jugées, 107
contre-expertises, 4 renversements.** Et la consolidation ne laisse **plus aucune collision**.

```
LE PLAN DE CORRECTION    141 operations sur 350 lignes jugees (87 lignes du Sheet touchees)
                         55 liens RETIRES . 109 liens AJOUTES (dont 23 deplacements)
                         0 collision . 0 ligne a deux liens pour un meme role
                         toutes les cibles existent et portent le genre de leur role
LIGNES SANS LIEN         91 -> 60   (38 rattachees ; 7 lignes FAUSSES perdent tout lien,
                         faute d'affaire chez nous : 1ESJE28Q 8Q3LHGZ4 NEFHS7JI WJ3KA32F
                         Y51UMZHY a8aaeb2b ea6a28a7)
COPIES DE C5             10 ne seraient plus visees par aucun lien -> retirables, des DEUX
                         cotes, dans un SECOND geste ; 15 restent tenues par des lignes
                         non encore jugees (les lignes « A3 », a un 4e tour)
                         ⚠ CORRIGE LE 18/11 AU SOIR : 11 transactions C5 a retirer, pas 10
                         (+ 1001553, cree depuis le Sheet, « n'a jamais existe ») ; et 2 des
                         15 sont tenues par des lignes INCERTAINES, pas « non jugees »
                         (§ 5 ter D)
LIGNES INCERTAINES       8, non touchees : elles attendent une reponse
```

**Le patch, DORMANT** : `supabase/patch_correction_gel_audit_independant_2026-11-18.sql`
(+ `_INVERSE`, `_REPETITION`), opérations listées dans
`notice/AUDIT_INDEPENDANT_CLASSEUR_OPERATIONS_GEL_2026-11-18.csv`. Une garde (le gel doit
porter exactement 12 787 liens, et chaque lien à retirer exister), une sauvegarde datée
**fermée dès sa naissance**, le contrôle dans la même transaction (le compte, l'exclusivité
que la base ne garantit pas, le genre de chaque cible, et le **témoin inverse** : les liens
non visés restent identiques). ⛔ Il porte son `commit;` : il ne se joue jamais « à blanc ».
✅ **Validé en lecture seule contre la base vivante le 18/11** : 55 retraits trouvés, 109
ajouts absents, 0 cible absente, 0 cible d'un autre genre, 0 cible tenue par une ligne qui ne
la lâche pas.

**Ce qu'il pourrait casser ailleurs, mesuré** :
- le gel n'a ni déclencheur ni fonction SQL qui le lise ; deux vues seulement ;
- la sentinelle `data.classeur_ligne_sans_lien` (seuil 92) passera à 60 : **son seuil doit
  suivre la mesure** (son commentaire l'exige), sinon elle tolérerait 32 lignes de trop —
  une modification de code, avec son « vas-y » ;
- les valeurs posées par C2, C3, C4 *(pas C9 : corrigé le 19/11)* en passant par un lien qui part (**31 liens**) restent
  sur la mauvaise transaction : geste à part, après celui-ci *(une par une au § 5 ter C : 20
  transactions Hektor, et 11 créées par C5)* ;
- **le run de nuit, les workers, l'app** — mesurés le 18/11 au soir, côté CODE : aucun lecteur, hors
  la copie de la descente du matin et deux sentinelles (§ 5 ter F) ;
- la sentinelle des liens cassés est critique : **les copies de C5 ne se retirent qu'APRÈS**
  ce patch, une fois qu'aucun lien ne les vise.

---

## 5 ter. LA LISTE COMPLÈTE — ce que le patch touche, et ce qui reste ouvert (vérification des 18-19/11)

> Écrite parce que Frédéric a demandé : *« Tout est listé dans le rapport ? »* — et la réponse était **non** :
> les CSV portaient presque tout, ce document n'en donnait que les comptes et quelques exemples, et certaines
> conclusions des contre-expertises n'étaient écrites nulle part hors du dossier de travail.
> ⛔ Ce paragraphe est **généré** (`rendre_section_complete.py`) depuis les CSV, le gel et le registre lus par
> l'audit, les contre-expertises et le classement des 18 lignes à question ouverte — pas recopié à la main.
> Le classement des 18 lignes vient de **trois juges indépendants et de trois contradicteurs** (nuit du 18 au
> 19/11, en lecture seule), puis de ma relecture des deux désaccords.

```
LA LISTE ET LE PATCH   141 operations = le patch, A L'UNITE PRES : 55 liens retires,
                       109 ajoutes, 0 de plus, 0 de moins (croise par programme,
                       cle par cle, entre le CSV et le SQL)
REVALIDE CONTRE LA     19/11 a 00:20 : gel 12 787 liens (dernier lien gele le 18/11 a 11:53),
BASE VIVANTE           55 retraits presents, 109 ajouts absents, 0 cible absente,
                       0 d'un autre genre, 0 tenue par une ligne qui ne la lache pas ;
                       sauvegarde pas encore creee (patch jamais joue) ; 91 sans lien ;
                       190 transactions C5 ; 31 356 au registre
```

### A. Les 87 lignes du Sheet que le patch touche, une par une

Le **pourquoi** de chaque opération est dans `notice/AUDIT_INDEPENDANT_CLASSEUR_OPERATIONS_GEL_2026-11-18.csv`
(colonne `raison`) ; la preuve complète de la ligne, dans le CSV des verdicts. « 30776 → 30684 » = le lien
change de transaction (un déplacement).

**Les 38 lignes SANS LIEN qui reçoivent leurs transactions**

- `9Q0FHAKK` (ligne 286, sans lien) : ajoute offre 3648 · ajoute compromis 3647 · ajoute vente 3650 ❓ *l'opération tient quelle que soit la réponse (§ B1)*
- `MDOXOBIC` (ligne 301, sans lien) : ajoute offre 2164 · ajoute compromis 2163 · ajoute vente 2165
- `DHXRAK9O` (ligne 566, sans lien) : ajoute offre 9371 · ajoute compromis 9370 · ajoute vente 9372
- `72GQRHVB` (ligne 579, sans lien) : ajoute offre 6392 · ajoute compromis 6391 · ajoute vente 6393
- `6FQO29C8` (ligne 589, sans lien) : ajoute compromis 19131 · ajoute vente 19133
- `7IHI7YTJ` (ligne 692, sans lien) : ajoute offre 4235 · ajoute compromis 4234 · ajoute vente 4236
- `S8BKB6FL` (ligne 1546, sans lien) : ajoute offre 4413 · ajoute compromis 4412 · ajoute vente 4414
- `LUX9SDIL` (ligne 2298, sans lien) : ajoute offre 14120 · ajoute compromis 14119 · ajoute vente 14121
- `EJN79TJ1` (ligne 2485, sans lien) : ajoute offre 27713 · ajoute compromis 27712 · ajoute vente 27714 ❓ *question déjà tranchée (§ B1)*
- `QXDW8EQA` (ligne 2559, sans lien) : ajoute offre 1028 · ajoute compromis 1027 · ajoute vente 1029 ❓ *l'opération tient quelle que soit la réponse (§ B1)*
- `I3TFR2KG` (ligne 2665, sans lien) : ajoute offre 24619 · ajoute compromis 24618 · ajoute vente 24620 ❓ *l'opération tient quelle que soit la réponse (§ B1)*
- `J6RGX0CQ` (ligne 2774, sans lien) : ajoute offre 4929 · ajoute compromis 4928 · ajoute vente 4930
- `91IHSGNC` (ligne 2780, sans lien) : ajoute offre 4782 · ajoute compromis 4781 · ajoute vente 4783 ❓ *l'opération tient quelle que soit la réponse (§ B1)*
- `58I5AO17` (ligne 2809, sans lien) : ajoute offre 7909 · ajoute compromis 7908 · ajoute vente 7910
- `ESMCO1NC` (ligne 2914, sans lien) : ajoute offre 6589 · ajoute compromis 6588 · ajoute vente 6590
- `8ATXF2EZ` (ligne 3175, sans lien) : ajoute offre 19153 · ajoute compromis 19152 · ajoute vente 19154
- `CS38OO8R` (ligne 3263, sans lien) : ajoute offre 27986 · ajoute compromis 27984 · ajoute vente 27987
- `2U5QPKRC` (ligne 3323, sans lien) : ajoute compromis 17769 · ajoute vente 17770 ❓ *l'opération tient quelle que soit la réponse (§ B1)*
- `JL8GV7RQ` (ligne 3328, sans lien) : ajoute compromis 15169 · ajoute vente 15170
- `5H70KQZA` (ligne 3378, sans lien) : ajoute offre 14227 · ajoute compromis 14224 · ajoute vente 14228
- `MQ6H8TVQ` (ligne 3383, sans lien) : ajoute offre 26696 · ajoute compromis 26695 · ajoute vente 26698 ❓ *l'opération tient quelle que soit la réponse (§ B1)*
- `O1099YC0` (ligne 3498, sans lien) : ajoute offre 6341
- `7JXLR3JQ` (ligne 3552, sans lien) : ajoute offre 7117 · ajoute compromis 7115
- `KAYC29B7` (ligne 3635, sans lien) : ajoute offre 27170
- `D9MMB7OU` (ligne 3735, sans lien) : ajoute offre 17366 ⚠❓ *le patch applique déjà une réponse (§ B1)*
- `515RUEN3` (ligne 3810, sans lien) : ajoute offre 17430 · ajoute compromis 17428
- `O8BY6AC8` (ligne 3906, sans lien) : ajoute offre 1000105 · ajoute compromis 1000141
- `PPIM4947` (ligne 3927, sans lien) : ajoute offre 24291
- `4G2UHO35` (ligne 4117, sans lien) : ajoute offre 19819 ❓ *l'opération tient quelle que soit la réponse (§ B1)*
- `ZZ5WKMWM` (ligne 4119, sans lien) : ajoute offre 11206 ❓ *question déjà tranchée (§ B1)*
- `Z6P7KE5R` (ligne 4126, sans lien) : ajoute offre 1337 ❓ *l'opération tient quelle que soit la réponse (§ B1)*
- `9706WM9J` (ligne 4145, sans lien) : ajoute offre 23931
- `c6233284` (ligne 4789, sans lien) : ajoute offre 30801
- `b884cbd4` (ligne 4796, sans lien) : ajoute offre 30821
- `5e4c8881` (ligne 4797, sans lien) : ajoute offre 30820
- `b43e76f5` (ligne 4798, sans lien) : ajoute offre 30826
- `1eec6575` (ligne 4799, sans lien) : ajoute offre 30825
- `70740f2f` (ligne 4800, sans lien) : ajoute offre 30824

**Les 12 lignes jugées FAUSSES : leurs liens faux partent (et certaines reçoivent la bonne transaction)**

- `TR42PT5H` (ligne 173, divergence de l'audit) : ajoute compromis 27195 · retire offre 27196
- `1ESJE28Q` (ligne 3464, « à valider ») : retire compromis 12952 · retire offre 12953 — **la ligne n'a plus aucun lien**
- `Y51UMZHY` (ligne 3522, « à valider ») : retire offre 19277 — **la ligne n'a plus aucun lien**
- `8Q3LHGZ4` (ligne 3579, « à valider ») : retire compromis 8321 · retire offre 8322 — **la ligne n'a plus aucun lien**
- `8RWTD0YX` (ligne 3795, divergence de l'audit) : offre 1001477 → 4387 · retire compromis 4385
- `WJ3KA32F` (ligne 3847, « à valider ») : retire offre 10730 — **la ligne n'a plus aucun lien**
- `OXQSBZ9V` (ligne 3961, divergence de l'audit) : offre 17430 → 17431 · retire compromis 17427
- `NEFHS7JI` (ligne 3991, divergence de l'audit) : retire compromis 26395 · retire offre 26397 — **la ligne n'a plus aucun lien**
- `ea6a28a7` (ligne 4195, divergence de l'audit) : retire compromis 14033 — **la ligne n'a plus aucun lien** ❓ *question déjà tranchée (§ B1)*
- `739a0db1` (ligne 4668, divergence de l'audit) : offre 1001520 → 27196 · retire compromis 27195
- `fa06e4e5` (ligne 4674, divergence de l'audit) : offre 28930 → 28931 · retire compromis 1001553
- `a8aaeb2b` (ligne 4718, « à valider ») : retire compromis 998 · retire offre 1000 — **la ligne n'a plus aucun lien**

**Les 37 lignes PARTIELLES : une partie de leurs liens change**

- `08GV8OMZ` (ligne 380, sœur) : retire offre 6341
- `TRJ5Y59U` (ligne 457, divergence de l'audit) : offre 1001561 → 23995
- `A07EC3DH` (ligne 535, sœur) : offre 1001563 → 1876
- `QJQ9M4OF` (ligne 1089, sœur) : retire offre 17366 ⚠ *indivisible de `D9MMB7OU` (§ B1)*
- `KT0601S6` (ligne 1758, divergence de l'audit) : retire offre 24291
- `H6CTRVR6` (ligne 1841, sœur) : ajoute offre 11415
- `2SCBZXMH` (ligne 1866, divergence de l'audit) : ajoute offre 7780
- `EGR8KXOL` (ligne 1902, sœur) : compromis 6554 → 6555
- `0GV2LNV2` (ligne 1943, sœur) : ajoute offre 4747
- `3S4ZWOFK` (ligne 2388, sœur) : offre 1001580 → 11958
- `427UDDSF` (ligne 3477, divergence de l'audit) : offre 3648 → 3649 · retire vente 3650
- `DAMOO7OU` (ligne 3518, divergence de l'audit) : offre 23995 → 23996
- `FLPUUSY3` (ligne 3540, divergence de l'audit) : offre 1876 → 1877
- `V3FO5NDA` (ligne 3632, « à valider ») : retire compromis 19131 · retire vente 19133 ❓ *question déjà tranchée (§ B1)*
- `9WQ204HP` (ligne 3763, sœur) : compromis 1001532 → 4480
- `3308P0UX` (ligne 3785, sœur) : retire compromis 4480 ❓ *l'opération tient quelle que soit la réponse (§ B1)*
- `87QOXR64` (ligne 3829, sœur) : compromis 1001534 → 17427 ❓ *l'opération tient quelle que soit la réponse (§ B1)*
- `VMWFLLW4` (ligne 3910, divergence de l'audit) : compromis 1001540 → 23050
- `61OW86CS` (ligne 3938, divergence de l'audit) : retire compromis 4496
- `E9GL6MUS` (ligne 3958, divergence de l'audit) : offre 11415 → 11414 ⚠❓ *le patch applique déjà une réponse (§ B1)*
- `VEP1DVQ4` (ligne 3962, divergence de l'audit) : offre 7780 → 7781
- `RX6J289Y` (ligne 3968, divergence de l'audit) : compromis 16377 → 16378
- `Q602VZJX` (ligne 3970, divergence de l'audit) : compromis 6555 → 6554
- `3W10AEIK` (ligne 3988, divergence de l'audit) : offre 4747 → 4748
- `SBH4QWDW` (ligne 4005, sœur) : retire compromis 23050
- `R0JRVFDC` (ligne 4014, sœur) : compromis 1001542 → 16377
- `1D7EIYKW` (ligne 4031, « à valider ») : retire compromis 27512 ⚠❓ *le patch applique déjà une réponse (§ B1)*
- `CITFQGOB` (ligne 4067, divergence de l'audit) : retire compromis 16378
- `9UO5NUN6` (ligne 4113, divergence de l'audit) : offre 11958 → 11959
- `UTLG66LE` (ligne 4131, divergence de l'audit) : offre 1001482 → 5055
- `045ecde7` (ligne 4391, divergence de l'audit) : retire offre 28558
- `f90b0418` (ligne 4455, « à valider ») : ajoute offre 19050
- `774aa002` (ligne 4606, divergence de l'audit) : retire compromis 11138
- `f1aedc01` (ligne 4699, divergence de l'audit) : retire offre 28967
- `5a956cad` (ligne 4754, divergence de l'audit) : offre 30776 → 30684 ⚠❓ *le patch applique déjà une réponse (§ B1)*
- `a2abd36c` (ligne 4761, sœur) : ajoute compromis 30827
- `45225170` (ligne 4762, divergence de l'audit) : retire offre 30712 · retire offre 1001361

### B. Toutes les questions pour Frédéric (33)

Le CSV des verdicts en porte 32 (colonne `question_pour_frederic`) ; la 33e, celle de `SHN6RKDI`, n'est que
dans la correction de sa contre-expertise.

**B1. 18 questions portent sur une ligne QUE LE PATCH MODIFIE.** Question posée aux juges : si tu
répondais dans le sens que le patch n'a pas retenu, une de ses opérations deviendrait-elle fausse ?

*⚠ 4 lignes où le patch applique DÉJÀ une des réponses — ma recommandation : les sortir du patch tant que tu n'as pas répondu :*

- `D9MMB7OU` (ligne 3735) — **la question :** Hektor met ROBERT Joel sur l'offre, le compromis et la vente ; le Sheet met AFFONSO (commentaire « Guetat/Anfosso ») sur la vente : est-ce le même ménage ?  
  Le patch fait passer l'offre 17366 de QJQ9M4OF (AFFONSO) à D9MMB7OU (ROBERT). Si ROBERT et AFFONSO sont le même ménage (ligne annulée le 22/09/2022 « renégo », ressaisie le 14/10/2022 au même prix), 17366 est la seule offre que Hektor ait jamais eue pour eux, acceptée, chaînée au compromis 17365 et à la vente 17367 que QJQ9M4OF garde : c'est encore la question de principe. Les juges sont partagés (le premier : l'opération tient ; le contradicteur : elle préjuge) — je retiens la prudence. ➡ À sortir du patch AVEC le retrait de 17366 sur QJQ9M4OF : les deux opérations sont indivisibles.
- `E9GL6MUS` (ligne 3958) — **la question :** Valérie FIGARI (offre Hektor 11414 du 06/04/2021 à 295 000) est-elle la co-acquéreuse de SOUBEYRAND ?  
  Le patch déplace l'offre 11415 (MERCIER) vers 11414 (FIGARI, 06/04/2021, 0 j). Le retrait de 11415 tient dans tous les cas : elle va à H6CTRVR6, au jour près. L'ajout de 11414 ne tient que si c'est l'offre de l'affaire SOUBEYRAND : seule la date l'y relie, aucune transaction du bien ne porte le nom SOUBEYRAND, et le compromis 11412 que la ligne garde est au nom de MERCIER. Le contradicteur reformule : « l'offre 11414 du 06/04/2021 est-elle celle de l'affaire SOUBEYRAND, quel que soit le rôle de FIGARI, ou celle d'une autre acheteuse ? » ➡ À remplacer par un simple retrait de 11415.
- `1D7EIYKW` (ligne 4031) — **la question :** GANDON-BERAUD ont-ils signé un compromis le 17/02/2021 (annulé ensuite), après l'annulation du 20/11/2020 ? Si oui, c'est une seconde tentative absente du Sheet ; si c'est la même tentative, le compromis 27512 peut rester sur cette ligne.  
  Le patch retire le compromis 27512 : il applique déjà la réponse « seconde tentative ». Les faits penchent pour l'autre réponse : 27512 porte les mêmes acquéreurs (GANDON / BERAUD), le même vendeur (BARRET), le prix (51 000) et la commission (4 000) de la ligne, c'est le seul compromis du dossier Hektor D2020-0447, et aucune autre ligne ne le prend. ➡ À sortir du patch : 27512 reste, avec la note du Sheet (colonne F) que nous y avons posée.
- `5a956cad` (ligne 4754) — **la question :** Pour une offre renégociée, le rôle offre doit-il viser l'offre d'origine 30684 du 21/09/2026 (date du Sheet) ou l'offre acceptée 30776 du 27/10/2026 (prix du Sheet) ?  
  Le patch déplace l'offre 30776 (acceptée le 27/10/2026, 82 218 €, le prix du Sheet) vers 30684 (première offre, 21/09/2026, la date du Sheet) : il applique déjà « la première offre ». C'est LA QUESTION DE PRINCIPE ci-dessous, que l'audit applique dans l'autre sens pour 2dfa6ef3 et d1cb8dd7. ➡ À sortir du patch : 30776 reste.

> ⭐ **LA QUESTION DE PRINCIPE — une seule réponse pour quatre lignes.** Quand une offre est renégociée ou
> ressaisie par le même acquéreur, le rôle « offre » d'une ligne tient-il la **PREMIÈRE offre** (celle qui porte
> la date du Sheet) ou l'**offre ACCEPTÉE / refaite** (celle qui porte le prix ou le nom du Sheet) ?
> Aujourd'hui l'audit l'applique **dans les deux sens** : `5a956cad` → la première offre (le patch déplace) ;
> `2dfa6ef3` (garde 30692, l'acceptée ; la première est 30656) et `d1cb8dd7` (garde 28833, la refaite ; la
> première est 28832, au nom d'Héloïse MADERE) → l'offre acceptée (rien ne bouge). Les trois journaux Hektor
> suivent le même schéma : la première offre est refusée dans la minute où la suivante est acceptée.
> - « **l'offre acceptée** » : sortir le déplacement de `5a956cad`, et la paire `D9MMB7OU` / `QJQ9M4OF` si
>   ROBERT et AFFONSO sont le même ménage ;
> - « **la première offre** » : AJOUTER deux déplacements, 30692 → 30656 pour `2dfa6ef3` (30692 porte 11 000 €
>   d'honoraires posés par nous) et 28833 → 28832 pour `d1cb8dd7` (qui recevrait une offre au nom de MADERE).

*4 questions déjà tranchées par la contre-expertise — le patch suit sa conclusion :*

- `EJN79TJ1` (ligne 2485) — **la question :** L'acquéreur MACHADO du Sheet est-il le ménage « NERONDE Arthur » de Hektor ?  
  Réglée par les données (contre-expertise, colonne conclusion_contre_expert du CSV) : « NERONDE Arthur » est le nom de la commune (Néronde-sur-Dore) saisi à la place du nom, et la fiche porte l'adresse électronique de MACHADO. Quatre dates au jour près.
- `V3FO5NDA` (ligne 3632) — **la question :** Hektor porte pour BAUDOIN-PETIPAS / TROUILLER (Chenereilles) un compromis du 08/12/2023 et un acte du 04/06/2024 (80 000 €, honoraires 6 000), postérieurs à l'annulation du 23/06/2023 : cette vente manque-t-elle au Sheet (une nouvelle ligne prendrait 19131 et 19133) ?  
  Tranchée par la contre-expertise : le compromis 19131 et la vente 19133 sont ceux de la ligne 6FQO29C8 (POCHELON), au jour près, et le patch les lui donne. La question écrite au CSV est périmée ; celle qui la remplace ne touche pas le gel : faut-il corriger chez Hektor l'acquéreur BAUDOIN ET PETIPAS de 19131 et 19133 ?
- `ZZ5WKMWM` (ligne 4119) — **la question :** L'offre sans nom 11206 (02/12/2019, 280 000 €) est-elle bien celle de PLA BOUARD ? Le compromis sans date 11205 (280 000 €, honoraires 15 800, étiqueté KERROUM) semble aussi être le leur, mais la ligne n'affirme aucun compromis.  
  Réglée par les données pour l'offre (contre-expertise, colonne conclusion_contre_expert du CSV ; revérifiée cette nuit) : l'acquéreur de 11206 est une fiche de couple créée le 29/11/2019, jour exact de l'offre du Sheet, distincte de KERROUM. Reste ouverte, sans effet sur le patch : faut-il AUSSI rattacher le compromis 11205, étiqueté KERROUM ?
- `ea6a28a7` (ligne 4195) — **la question :** La transaction 14033 (compromis annule sans date, 140 500 EUR dont 9 500 d'honoraires, aux noms COLAS / SOLEILHAC) est-elle la trace de l'offre DONNADIEU / KOSINSKI du 04/06/2025, ou un premier compromis du dossier COLAS saisi au prix affiche puis refait a 130 000 EUR ?  
  Tranchée par la contre-expertise, et confirmée cette nuit : les deux acquéreurs de 14033 (COLAS, SOLEILHAC) sont des fiches Hektor créées les 26/07 et 12/08/2025, deux mois après la fin de l'affaire DONNADIEU (10/06/2025). 14033 appartient à l'affaire COLAS ; DONNADIEU n'a aucune transaction chez nous.

*10 lignes où l'opération tient quelle que soit ta réponse — elle ne ferait qu'ajouter un lien plus tard, ou corriger un nom chez Hektor :*

- `9Q0FHAKK` (ligne 286) — **la question :** POTTIER Dominique et SOUCHON Christine forment-ils le même ménage acquéreur ? Hektor met SOUCHON sur le compromis à 460 000 et sur la vente, le Sheet met POTTIER.  
  Trois dates au jour près (offre 23/08/2024, compromis 11/09/2024, vente 22/01/2025) : même ménage ou non, rien ne bouge. Seul le contact chez Hektor (SOUCHON sur 3647 et 3650) serait à revoir.
- `QXDW8EQA` (ligne 2559) — **la question :** TARDY (Sheet) est-il lié à la SARL VEYRARD DEVELOPPEMENT ou à STEFANELLI Léa, les acquéreurs chez Hektor ?  
  Offre, compromis et vente au jour près, au même prix non rond (1 358 840) : un « non » ne serait qu'un écart de nom.
- `I3TFR2KG` (ligne 2665) — **la question :** COTE Jean-Claude (Hektor) est-il le représentant de la SCI MADEVA (Sheet) ?  
  Quatre dates au jour près, mêmes mandants, honoraires égaux à la commission : un « non » ne serait qu'un écart de nom.
- `91IHSGNC` (ligne 2780) — **la question :** La vente 4783 nomme GRANGÉ Denis au lieu des DELAVAUD : est-ce une simple erreur de contact chez Hektor ?  
  Seule vente du bien, au jour près, au prix du mandat, mêmes mandants ; l'offre et le compromis sont au nom des DELAVAUD : même une substitution à l'acte ne détacherait pas la vente.
- `2U5QPKRC` (ligne 3323) — **la question :** MARLEE (Sheet) et OBERLIN Christian (Hektor, transactions 17769/17770) forment-ils le même ménage d'acquéreurs ?  
  Compromis et vente au jour près, honoraires égaux à la commission ; la fiche OBERLIN est créée la veille de l'offre du Sheet, avec « 6800€ » en commentaire.
- `MQ6H8TVQ` (ligne 3383) — **la question :** Le Sheet nomme MITTELETTE acquereur de la vente HDHILI du 06/07/2018 ; Hektor porte KABAB Julian (offre) et ODDOU Thibaut (compromis, vente), et MITTELETTE (SCI BEAST) a signe le meme 27/12/2017 un compromis annule sur un autre bien (26558, vendeur DUPORT) : le nom d'acquereur du Sheet est-il une erreur de saisie ?  
  La ligne est la vente HDHILI (vendeur, commission, dates au jour près). Chez Hektor, ODDOU et KABAB sont des « partenaires » et MITTELETTE l'acquéreur investisseur : aucune transaction MITTELETTE ne peut porter cette ligne.
- `3308P0UX` (ligne 3785) — **la question :** VIALLARD est saisie deux fois au Sheet avec la même offre du 02/02/2022 : 3308P0UX (annulée 22/05/2022, renonciation acq) et YRUF0S9H (annulée 22/04/2022, refus prêt). Laquelle garde l'offre 4483, l'autre restant sans lien ?  
  Le patch ne fait que retirer le compromis 4480, qui va à 9WQ204HP au jour près ; il laisse l'offre 4483 où elle est. Ta réponse dira seulement si 4483 doit passer plus tard à YRUF0S9H.
- `87QOXR64` (ligne 3829) — **la question :** Au Sheet, RIGAUD est annulée le 22/01/2022 mais a un compromis du 11/02/2022. L'annulation est-elle plutôt du 22/02/2022, juste avant le compromis LECOMPTE du 24/02/2022 ?  
  Le déplacement de la copie 1001534 vers 17427 repose sur la date de compromis de la ligne (11/02/2022, 0 j). Ta réponse ne changera que la date d'annulation à poser plus tard (la contre-expertise l'explique : LECOMPTE a fait son offre la veille).
- `4G2UHO35` (ligne 4117) — **la question :** Le compromis annule 19814 (17/02/2020, 69 000, hon 5 980 = commission de cette ligne, acte prevu 17/05/2020), range sous le contact CHEVALLET cree en mai 2020 et porte par aucune ligne, est-il le compromis de BROCHIER (affaire annulee le 20/05/2020 pour financement) ?  
  Le patch pose l'offre 19819 (0 j). Un « oui » ferait seulement AJOUTER plus tard le compromis 19814, ou son jumeau 19815, tout aussi compatible.
- `Z6P7KE5R` (ligne 4126) — **la question :** Le Sheet n'a pas de date de compromis (compromis prévu le 21/02, reporté puis annulé). Faut-il aussi rattacher 1335 (compromis THEVENON annulé, sans date, 38500 €, hon 3500) comme compromis de cette ligne ?  
  Le patch pose l'offre 1337 (0 j). Un « oui » ferait seulement AJOUTER plus tard le compromis 1335 (la contre-expertise penche pour le oui).

**B2. Les 8 lignes INCERTAINES — le patch NE LES TOUCHE PAS**, elles attendent ta réponse :

- `SHN6RKDI` (divergence de l'audit) : *(question posée par la contre-expertise)* le compromis 26613 de la maison CHANUT (annulé, jamais daté, 210 000 €, net vendeur 0) a-t-il été préparé pour les MOSNIER entre leur offre du 23/12/2024 et leur désistement du 25/01/2025, ou est-ce un brouillon de l'affaire CREPINGE/LAROUX ou LUTTENBACHER/CARRET ?
- `O6R10ZQA` (divergence de l'audit) : O6R10ZQA (annulée le 21/09/2021) et T2GZOY5O (annulée le 21/11/2021) sont la même affaire PAOLONE : laquelle garde l'offre 20075 et le compromis 20073, et quelle date d'annulation est la bonne ?
- `5QE9107L` (divergence de l'audit) : Le compromis 20088 (DEBARD, 50 000 EUR dont 5 000 d'honoraires, jamais daté) est-il celui de la 1re offre (55 000 du 20/02/2021, annulée le 21/06/2021) ou celui de la 2e (50 000 du 20/07/2021, ligne ZW7MKTWH, annulée le 21/11/2021) ?
- `YRUF0S9H` (sans lien) : YRUF0S9H (annulée le 22/04/2022, refus de prêt) et 3308P0UX (annulée le 22/05/2022, renonciation) sont-elles la même affaire VIALLARD saisie deux fois ? Si oui, laquelle garde l'offre 4483 ?
- `T2GZOY5O` (sœur) : PAOLONE est saisie deux fois au Sheet (T2GZOY5O annulée le 21/11/2021, O6R10ZQA annulée le 21/09/2021, tout le reste identique) : laquelle garde l'offre 20075 et le compromis 20073, et quelle date d'annulation est la bonne ?
- `ZW7MKTWH` (sœur) : Le compromis 20088 (DEBARD, 50 000 EUR dont 5 000 d'honoraires, jamais daté) suit-il la 2e offre (50 000 le 20/07/2021, ligne ZW7MKTWH, annulée le 21/11/2021) ou la 1re (55 000 le 20/02/2021, ligne 5QE9107L, annulée le 21/06/2021) ?
- `RGCEC677` (sœur) : Le compromis annulé et jamais daté 4542 (108 000 €, honoraires de 8 000 €) de la ferme de Cunlhat a-t-il été préparé pour les MEJEAN/MARIAGE (offre de 110 000 € du 07/03/2021, annulée le 01/08/2021 pour un problème de parcelle) ou pour FAU-PIETTE (offre de 108 000 € de septembre 2021, annulée le 21/11/2021) ?
- `XC761R8Z` (sœur) : Le compromis annulé 4496 de la maison VAN DIJK à Cunlhat (155 000 EUR dont 9 800 d'honoraires, jamais daté) a-t-il été préparé pour l'affaire BISCH (offre de 155 000 le 14/04/2021, annulée le 21/05/2021) ? Si non, il ne revient à aucune ligne.

  ⚠ Pour `O6R10ZQA` et `T2GZOY5O`, la contre-expertise dit le retrait des copies 1001480 et 1001536 « acquis quel
  que soit le choix » ; le patch ne le fait pas, parce que les deux lignes sont INCERTAINES (§ D2).

**B3. 7 questions sur des lignes que le patch LAISSE COMME ELLES SONT** (leur lien est jugé juste) :

- `TA5QUCD4` (« à valider », JUSTE) : L'offre du Sheet au 19/07/2018 est-elle une faute de saisie ? Hektor porte l'offre DUPARANT au 11/12/2018, 145 jours plus tard.
- `Y9A2L3X4` (« à valider », JUSTE) : Le compromis GERPHAGNON/JOINAUX a-t-il été signé le 20/06/2019 (Sheet) ou le 17/07/2019 (Hektor) ?
- `HUY49KEC` (divergence de l'audit, JUSTE SANS PREUVE FORTE) : Pour ce lot vendu à CANIVET, le compromis du 16/11/2018 a-t-il existé, ou est-ce une date de remplissage (toutes les dates du Sheet sont au 16/11) ? Faut-il le créer ?
- `c0a73edd` (divergence de l'audit, JUSTE) : Le dossier Hektor 28614-28616 (annonce 59136, D2025-0399, honoraires a la charge du vendeur, porte par aucune ligne) est-il un doublon de la vente 28611-28613, ou un second lot vendu par M. JUQUET a la SCI La Felolie ?
- `d1cb8dd7` (divergence de l'audit, JUSTE) : Pour le rôle offre, gardes-tu l'offre refaite au nom des MADER (28833, datée du 15/04) ou la première saisie (28832, du 09/04, au nom d'Héloïse MADERE), qui porte la date du classeur ? ➡ *c'est la question de principe du § B1*
- `2dfa6ef3` (divergence de l'audit, JUSTE) : En cas de renegociation, le role offre doit-il tenir l'offre acceptee (30692, prix du Sheet) ou la premiere offre (30656, date du Sheet) ? ➡ *c'est la question de principe du § B1*
- `JZ9693S0` (sans lien, RIEN CHEZ NOUS) : La ligne 3489 (mandat 92560, sans nom ni date, facture GGTI00002792 / avoir AVR00000465) est-elle un residu ou un avoir a laisser hors du registre ?

**B4. Une décision de fond, pas une question de ligne : les 51 lignes RIEN CHEZ NOUS.** L'affaire n'a aucune
transaction chez nous (offre jamais saisie chez Hektor, ou effacée ; ligne « Annulée » d'une affaire ressaisie).
Plusieurs verdicts disent « à recréer seulement si Frédéric le décide » ; s'y ajoutent l'affaire DONNADIEU de
`ea6a28a7` et l'offre renégociée de `QJQ9M4OF`. **Recréer ou non depuis le Sheet** est à trancher au rapatriement.

### C. Les 31 liens qui partent en laissant derrière eux quelque chose que NOUS avons posé

Sur les 55 liens retirés, 31 portaient une trace de nous. ⛔ **Le patch ne les touche pas** : c'est le geste
suivant, avec son accord. Relu dans la base vivante le 18/11 au soir : **identique à l'unité près**.

**C1. 20 transactions Hektor gardent une trace posée par nous depuis la ligne qui les lâche** — 9 dates
d'annulation (C3), 4 motifs, 19 notes du Sheet (C4) et 1 commission (C2) ; **aucune valeur de C8 ni de C9** n'est
concernée :

- compromis 27512, lâché par `1D7EIYKW` : note du Sheet (colonne F) ; la transaction ne va à aucune ligne
- compromis 12952, lâché par `1ESJE28Q` : date d'annulation 2024-09-24 · motif d'annulation Annule sans motif precise · note du Sheet (colonne G) ; la transaction ne va à aucune ligne
- compromis 4480, lâché par `3308P0UX` : motif d'annulation Retractation · note du Sheet (colonne G) ; la transaction va à `9WQ204HP`
- vente 3650, lâchée par `427UDDSF` : note du Sheet (colonne F+G) ; la transaction va à `9Q0FHAKK`
- compromis 4496, lâché par `61OW86CS` : date d'annulation 2021-06-21 · note du Sheet (colonne F) ; la transaction ne va à aucune ligne
- compromis 27195, lâché par `739a0db1` : date d'annulation 2026-07-27 · note du Sheet (colonne F+G) ; la transaction va à `TR42PT5H`
- compromis 11138, lâché par `774aa002` : date d'annulation 2026-06-02 · note du Sheet (colonne F+G) ; la transaction ne va à aucune ligne
- compromis 8321, lâché par `8Q3LHGZ4` : date d'annulation 2023-10-23 · motif d'annulation Retractation · note du Sheet (colonne G) ; la transaction ne va à aucune ligne
- compromis 4385, lâché par `8RWTD0YX` : date d'annulation 2022-04-22 · note du Sheet (colonne F) ; la transaction ne va à aucune ligne
- compromis 998, lâché par `a8aaeb2b` : honoraires d'entrée 1000 · note du Sheet (colonne G) ; la transaction ne va à aucune ligne
- compromis 16378, lâché par `CITFQGOB` : motif d'annulation Changement de situation acquereur ; la transaction va à `RX6J289Y`
- compromis 14033, lâché par `ea6a28a7` : date d'annulation 2025-06-10 · note du Sheet (colonne G) ; la transaction ne va à aucune ligne
- compromis 26395, lâché par `NEFHS7JI` : date d'annulation 2021-03-21 · note du Sheet (colonne F) ; la transaction ne va à aucune ligne
- compromis 17427, lâché par `OXQSBZ9V` : note du Sheet (colonne F) ; la transaction va à `87QOXR64`
- compromis 6555, lâché par `Q602VZJX` : note du Sheet (colonne F) ; la transaction va à `EGR8KXOL`
- compromis 16377, lâché par `RX6J289Y` : date d'annulation 2021-04-21 · note du Sheet (colonne F) ; la transaction va à `R0JRVFDC`
- compromis 23050, lâché par `SBH4QWDW` : note du Sheet (colonne F) ; la transaction va à `VMWFLLW4`
- offre 27196, lâchée par `TR42PT5H` : note du Sheet (colonne G) ; la transaction va à `739a0db1`
- vente 19133, lâchée par `V3FO5NDA` : note du Sheet (colonne F+G) ; la transaction va à `6FQO29C8`
- offre 19277, lâchée par `Y51UMZHY` : note du Sheet (colonne F+G) ; la transaction ne va à aucune ligne

⚠ **Toutes ne sont pas à jeter** : le motif « Rétractation » de 4480 reste juste pour `9WQ204HP`, qui reçoit 4480 ;
la date 2021-04-21 de 16377 est celle de 16378 (`RX6J289Y`) et se **déplace**, tandis que 16377 doit recevoir
2021-01-21 (`R0JRVFDC`, prêt refusé). Le nettoyage se fera trace par trace, pas en bloc.

**C2. 11 transactions CRÉÉES depuis le Sheet (C5) n'auront plus aucun lien** — leur seule trace est leur
création : c'est la transaction entière qui se retire (§ D1).

### D. Les transactions créées depuis le Sheet, après le patch

**D1. 11 n'auront plus aucun lien** (et pas 10 comme l'écrivait le § 5 bis) :

- 1001477 (offre, copie de 4387) — lâchée par `8RWTD0YX` ; l'originale 4387 va à `8RWTD0YX`
- 1001482 (offre, copie de 5055) — lâchée par `UTLG66LE` ; l'originale 5055 va à `UTLG66LE`
- 1001520 (offre, copie de 27196) — lâchée par `739a0db1` ; l'originale 27196 va à `739a0db1`
- 1001532 (compromis, copie de 4480) — lâchée par `9WQ204HP` ; l'originale 4480 va à `9WQ204HP`
- 1001534 (compromis, copie de 17427) — lâchée par `87QOXR64` ; l'originale 17427 va à `87QOXR64`
- 1001540 (compromis, copie de 23050) — lâchée par `VMWFLLW4` ; l'originale 23050 va à `VMWFLLW4`
- 1001542 (compromis, copie de 16377) — lâchée par `R0JRVFDC` ; l'originale 16377 va à `R0JRVFDC`
- 1001553 (compromis, **la copie d'aucune transaction Hektor** : le verdict de `fa06e4e5` dit que ce compromis « n'a jamais existé ») — lâché par `fa06e4e5`
- 1001561 (offre, copie de 23995) — lâchée par `TRJ5Y59U` ; l'originale 23995 va à `TRJ5Y59U`
- 1001563 (offre, copie de 1876) — lâchée par `A07EC3DH` ; l'originale 1876 va à `A07EC3DH`
- 1001580 (offre, copie de 11958) — lâchée par `3S4ZWOFK` ; l'originale 11958 va à `3S4ZWOFK`

⛔ **LE PIÈGE pour les retirer** : 17 transactions numérotées au-dessus de 1 001 000 sont de **vraies transactions
Hektor** (par exemple 1001361, n° Hektor 33098, que le patch détache de `45225170`). Après le patch, **12**
transactions « 1001… » n'ont plus de lien, dont 11 seulement viennent de C5. Le geste se choisit par
`transaction_origine = 'classeur'`, **jamais par la plage des numéros**, et des DEUX côtés avant 04:00.

**D2. 15 copies restent tenues après le patch** — 13 par des lignes A3 jamais jugées (le « 4e tour »), 2 par des
lignes INCERTAINES. Pour 10 d'entre elles, l'originale est tenue par une AUTRE ligne : la même affaire reste sur
deux lignes après le patch.

- 1001474 (offre, copie de 25879) — tenue par `T0WL4QE7` ; l'originale 25879 est libre
- 1001476 (offre, copie de 19458) — tenue par `I3R03A11` ; l'originale 19458 est libre
- 1001480 (offre, copie de 20075) — tenue par `O6R10ZQA` *(ligne INCERTAINE)* ; l'originale 20075 est tenue par `T2GZOY5O`
- 1001522 (compromis, copie de 20264) — tenue par `EO8MXFE9` ; l'originale 20264 est tenue par `E1WD68ZB`
- 1001529 (compromis, copie de 14813) — tenue par `SWSN80FQ` ; l'originale 14813 est tenue par `FJS4IJGZ`
- 1001530 (compromis, copie de 4370) — tenue par `FWCFAN6O` ; l'originale 4370 est libre
- 1001531 (compromis, copie de 4289) — tenue par `LKBO1TOH` ; l'originale 4289 est libre
- 1001533 (compromis, copie de 24380) — tenue par `9KHYVR1M` ; l'originale 24380 est tenue par `RF9KYWSY`
- 1001535 (compromis, copie de 11558) — tenue par `8NZ6V6XB` ; l'originale 11558 est libre
- 1001536 (compromis, copie de 20073) — tenue par `T2GZOY5O` *(ligne INCERTAINE)* ; l'originale 20073 est tenue par `O6R10ZQA`
- 1001537 (compromis, copie de 17387) — tenue par `S3HOG6UL` ; l'originale 17387 est tenue par `60CLRO51`
- 1001538 (compromis, copie de 24450) — tenue par `6U5DQQ4J` ; l'originale 24450 est tenue par `4PW2L3MG`
- 1001539 (compromis, copie de 1101) — tenue par `2FBR2M9U` ; l'originale 1101 est tenue par `E6RLLKMN`
- 1001541 (compromis, copie de 27445) — tenue par `JRN2I7TM` ; l'originale 27445 est tenue par `H78FD3YN`
- 1001593 (offre, copie de 14008) — tenue par `1cc703d9` ; l'originale 14008 est tenue par `LPBAZ1D4`

**D3. D'autres doublons de notre registre sont à neutraliser** (colonne `consequences` des verdicts) — ce ne
sont pas des créations de C5 :

- `45225170` : 30712 et 1001361 doublent l'offre 30767 (prix mal saisi a 16 000 EUR) : a neutraliser.
- `0bc98552` : 21803 et 21805 (absentes chez Hektor) doublent 21804 et 21806 : a neutraliser, aucune ligne ne doit les prendre.
- `dfb32f2b` : 19543 (compromis du 20/11/2025, ABSENT chez Hektor, D2025-0371) est un doublon de 19544, tenu par aucune ligne : ne le rattacher nulle part.
- `a8aaeb2b` : Ce compromis de l'appartement est en plus un doublon de 999, absent chez Hektor.
- `fa06e4e5` : 28930, offre anonyme refusee le 15/07, ne doit pas rester rattachee a cette ligne.
- `045ecde7` : 28558 reste dans notre registre (nous gardons les absentes), sans lien à la ligne.

### E. Lire le CSV des verdicts sans se tromper

- **Les 93 sœurs** : JUSTE 75 · PARTIEL 13 · INCERTAIN 4 · JUSTE SANS PREUVE FORTE 1.
  Leurs 4 INCERTAINES sont `T2GZOY5O`, `ZW7MKTWH`, `RGCEC677` et `XC761R8Z` (§ B2).
- **La colonne `liens` garde la décision DU JUGE** pour 4 lignes : `SHN6RKDI` (26613 « RETIRER », décision finale
  DOUTEUX), `O6R10ZQA` (1001480 « RETIRER ») et `T2GZOY5O` (1001536 « RETIRER »), toutes trois non touchées ; et
  `ea6a28a7` (14033 « DOUTEUX », pourtant retiré). La décision finale est dans `verdict` et `correction_contre_expert`,
  et **c'est elle que le patch suit**.
- **Ce que les contre-expertises concluent sans renverser n'était pas dans le CSV** (`rapport_verdicts.py` n'écrivait
  la correction que pour un verdict renversé) : `87QOXR64`, `8RWTD0YX`, `EJN79TJ1`, `O1099YC0`, `ZZ5WKMWM`. Depuis le 19/11, la colonne `conclusion_contre_expert` porte la
  conclusion des 107 contre-expertises.
- **Les questions déjà tranchées** restent écrites dans la colonne `question_pour_frederic` (`V3FO5NDA`, `ea6a28a7`,
  `EJN79TJ1`, et le premier volet de `ZZ5WKMWM`) : le § B1 dit lesquelles.

### F. Le run de nuit, les workers, l'app : ce que le patch pourrait casser ailleurs (mesuré le 18/11 au soir)

Le § 5 bis ne mesurait que la base. Frédéric a demandé si le patch « prévoit tous les risques avec le run,
les workers » : voici la mesure, côté base ET côté code.

```
CE QUE LE PATCH NE FAIT PAS   ni le RAPATRIEMENT (poser les valeurs du Sheet sur les transactions),
                              ni le nettoyage des 31 traces du § C, ni aucune ecriture sur une
                              transaction, ni aucun travail pour les workers, ni rien chez Hektor
LA BASE                       aucun declencheur, aucune fonction, aucune tache cron, pas de temps
                              reel ; deux vues seulement ; SEUL service_role a des droits : aucun
                              ecran de l'app ne peut le lire
LE CODE                       recherche de la table et de ses deux vues dans Console (les workers),
                              apps/hektor-v1 (l'app), backend, scheduled, supabase/functions,
                              phase2/sync (le run) et monitoring : AUCUN lecteur, sauf --
  la descente du matin        elle en fait une COPIE locale (table de sb_pull_state : rien ne la
                              repousse). Elle copiera aussi la sauvegarde datee (12 787 lignes,
                              sans cle primaire) : ce matin elle a copie 3 sauvegardes du gel
                              faites pareil, et sa relecture par rang les a lues EN ENTIER
                              (journal du 18/11 : 12 584/12 595 au 1er passage, puis 12 595)
  deux sentinelles            data.classeur_lien_casse (critique, 0 permis) : reste a 0, toutes les
                              cibles existent ; data.classeur_ligne_sans_lien (avertissement,
                              seuil 92) : passe a 60 et reste verte, mais tolererait 32 lignes de
                              trop -> baisser le seuil (code, avec son « vas-y » ; voir § G)
  les outils du rapatriement  36 scripts de phase2/checks lisent le gel (dont les generateurs C2,
                              C3, C4, C8, C9) : ce sont des outils LANCES A LA MAIN, aucun ne tourne
                              la nuit -- rien ne se pose tout seul sur les nouveaux liens
LA NUIT                       le push de 04:00, le chainage, le filet des workers et le controle
                              du 19/11 des 5 doublons lisent les TRANSACTIONS, que le patch ne
                              touche pas : rien ne change pour eux
```

⛔ **Le seul geste de la suite qui touche la nuit** : retirer les transactions du § D1. Elles vivent dans le
registre local (le maître) ET chez Supabase : elles se retirent **des deux côtés, dans la même fenêtre,
avant 04:00**, sinon le push les recrée (leçon du 18/11, § 4.6).

⚠ **Ce que le chaînage ne règle pas, et qui compte pour l'étape 5.2** : après le patch, des lignes d'acquéreurs
différents partagent une même étiquette de dossier (D2023-0189 : `V3FO5NDA` et `6FQO29C8` ; D2021-0091 : `OXQSBZ9V`
et `87QOXR64` ; D2024-0278 : `427UDDSF` et `9Q0FHAKK` ; D2022-0058 : `3308P0UX`, `N1CUULMN` et `9WQ204HP`). Les
comptes du § 4.5 (4 448 / 255 / 1) sont mesurés AVANT le patch, et ils ne voient pas une étiquette partagée entre
deux affaires.

### G. Ce que le patch laisse derrière lui

```
LE GEL APRES       12 841 liens : sure 12 497 . bonne 77 . a valider 267 ; 4 734 lignes liees
SANS LIEN          60 = 51 RIEN CHEZ NOUS + 7 FAUSSES + YRUF0S9H + 53ZS73KW
                   ⚠ la ligne nee 54376c72 (rang 4801) n'est pas encore dans app_classeur_ligne_id :
                   le jour ou elle y entre, elle est sans lien -> 61. A compter pour le seuil
                   de la sentinelle et pour lire la repetition (« attendu_sans_lien 60 »)
LES 267 « A VALIDER » JUGES JUSTES   restent « a valider » : le patch ne les promeut pas
                   (son temoin inverse interdit d'y toucher)
LA SAUVEGARDE      app_classeur_lien_avant_audit_independant_20261118 : ne PAS la supprimer,
                   le retour arriere la relit
LA REPETITION      n'a pas de valeur attendue pour les liens casses « DISPARUE » : il faut 0
```

⚠ **La confiance « moyenne » est écrite « bonne ».** 7 opérations sont jugées de confiance moyenne : les ajouts
MQ6H8TVQ 26696, MQ6H8TVQ 26695, MQ6H8TVQ 26698, ZZ5WKMWM 11206, 5a956cad 30684, et les retraits 1D7EIYKW 27512, ea6a28a7 14033. Le patch écrit `certaine` → « sûre » et tout le reste → « bonne » : une fois joué, le gel
ne distinguerait plus ces 5 liens des autres. ➡ Proposé : les écrire « à valider ».

**Les 55 retraits ne visent pas surtout des liens « à valider »** : sûre 43 · à valider 10 · bonne 2 ; par étage de l'apparieur : « 0 creee par C5 depuis cette ligne » 11 · « 5 mandat + vendeur » 8 · « 9 sans mandat (acquéreur + vendeur) » 7 · « 1 mandat seul » 6 · « v2 additif (13/11) : >= 3 familles » 6 · « 2 mandat + acquéreur » 4 · « 4 mandat + avancement » 4 · « 3 mandat + date » 3 · « 9 sans mandat (acquéreur + vendeur) + exclusi » 3 · « 6 mandat + prix » 2 · « 0 corrige le 17/11 : la date colle a 0 jour » 1.
Des liens « sûre » étaient donc faux aussi (dont les 11 qui visaient une copie de C5).

**Avant le patch, 4 lignes ont DEUX offres au gel** (une ligne n'en doit avoir qu'une) : `045ecde7`, `45225170`, `KT0601S6`, `f1aedc01`. Le patch les
corrige ; le « 0 ligne à deux liens pour un même rôle » du § 5 bis est l'état APRÈS.

### H. Ce que les juges ont relevé HORS du gel (colonne `consequences`, 104 verdicts sur 350)

Le patch n'y touche pas ; chaque point est un geste à part, avec son accord.

- **Des offres acceptées passées « refusées » par nos gestes du 11/11/2026** alors que le journal Hektor les dit
  acceptées : 23995 (`TRJ5Y59U / DAMOO7OU`), 7780 (`VEP1DVQ4`), 5055 (`UTLG66LE`), 6556 (`EGR8KXOL`), 20089 (`ZW7MKTWH`), 6204 (`CRWGXG9R`), 21799 (`26283bf9`), 8322 (`8Q3LHGZ4`), 3648 (`427UDDSF`). À défaire au cas par cas.
- **Des chaînes de dossier à scinder, réunir ou rechaîner** (une chaîne Hektor qui mêle deux affaires, ou une
  affaire coupée en deux) : 14 verdicts le demandent (`26283bf9`, `3W10AEIK`, `427UDDSF`, `D7CZQBZG`, `DAMOO7OU`, `E9GL6MUS`, `FBOSPXJX`, `H6CTRVR6`, `JAKQXFWK`, `O1099YC0`, `T2GZOY5O`, `VEP1DVQ4`, `XZRBWA33`, `Z6P7KE5R`).
- **Une valeur que nous avons mal posée** : la vente réglée de 27644 au format brut « 6 février20 » (`JPNCDKO1`).
- **Des commissions à NE PAS poser** : 7 000 sur 16378 (`CITFQGOB`), 5 000 sur 11138 (`774aa002`), 4 700 sur 20088
  avant ta réponse (`5QE9107L`, `ZW7MKTWH`) ; et les 1 305 € de `EAQJ9D0T` ne se comptent pas deux fois.
- **Des garde-fous pour le rapatriement** (« ne rien créer », « ne le rattacher nulle part ») : `dfb32f2b`, `YBDIPVKR`,
  `AISKUW87`, `6CFWM9TF`.
- **Ce que les rattachements appellent ensuite** (factures, règlements) : `5H70KQZA`, `72GQRHVB`, `7JXLR3JQ`, `CS38OO8R`, `J6RGX0CQ`, `MDOXOBIC`, `S8BKB6FL`.

### I. Ce que la vérification a corrigé dans ce rapport (19/11)

Les phrases fausses ou périmées sont corrigées sur place, avec la mention « corrigé le 19/11 » ; les voici :

- § 1 : « 8 entrées » — les causes nommées n'en expliquent que 7 (2 + 5), et 3 des 5 offres seulement sont nommées ;
  le croisement de `c08ff7cb` (offre 3678 tenue par `721e650c`) n'est pas réglé par le patch : aucune des deux
  lignes n'est jugée.
- § 3 : les trois comptes par lien (11 964 + 190 + 255) font 12 409 : 378 liens ne sont classés nulle part (recompte
  dans `comparaison.json` : 207 non mesurables, 67 proches de 2-3 j sur le bon dossier, 104 au jour près mais sur
  une autre chaîne). Et des « 13 liens
  FAUX », les juges en confirment 10 ; `d1cb8dd7` et `2dfa6ef3` sont jugées JUSTES (question de principe, § B1), et
  pour `45225170` la « meilleure » transaction, 30712, est elle-même un doublon.
- § 4.2 : « OXQSBZ9V -> 515RUEN3 offre 17430 et compromis 17427 » était faux : 515RUEN3 reçoit 17430 et 17428 ;
  17427 va à `87QOXR64`. Et le patch règle six croisements de plus que la liste : 08GV8OMZ → O1099YC0 (6341),
  QJQ9M4OF → D9MMB7OU (17366), KT0601S6 → PPIM4947 (24291), 3308P0UX → 9WQ204HP (4480), SBH4QWDW → VMWFLLW4
  (23050), V3FO5NDA → 6FQO29C8 (19131, 19133).
- § 4.4 : `0bc98552` est jugée JUSTE (son seul problème est le doublon 21803/21805) ; `V3FO5NDA` et `RX6J289Y`
  manquaient à la liste ; 26613 ne part pas (sa ligne `SHN6RKDI` est INCERTAINE, sa date reste pour l'instant).
- § 5 : `a8aaeb2b` est fausse par DEUX signaux faibles, pas un nom seul ; « RETIRER 10 » vaut pour les 277 liens
  « à valider », mais le patch retire 11 liens de ces 104 lignes (la colonne `liens` porte 269 GARDER et 11 RETIRER) ;
  `3308P0UX` est PARTIEL et touchée, pas INCERTAINE ; et le tour des sœurs est FAIT (§ 5 bis).
- § 5 bis : les traces des 31 liens ne viennent pas de C9 (§ C) ; il y a 11 copies de C5 à retirer, pas 10 (§ D1).
- En-tête : « le plan DÉCIDE » — le plan ne portait ni le tour des sœurs ni le patch : son entrée du 18/11 est
  complétée le 19/11.

---

## 6. CE QUI EN DÉCOULE POUR LA SUITE

**Le rapatriement** : ne rien poser sur un lien que l'audit déclare faux ; réparer d'abord le
gel (retirer, déplacer, rattacher), puis les copies de C5 (des deux côtés), puis les valeurs
posées sur une mauvaise transaction — **chaque geste avec son accord**.

**L'étape 4** : `app_modifier_affaire_optimistic` exige un utilisateur connecté (admin ou
gestionnaire, `is_app_manager_or_admin()` lit `auth.uid()`), un numéro Hektor, et une
transaction encore présente chez Hektor ; elle corrige notre registre à l'instant et pose un
travail `change_hektor_annonce_status`. ⛔ **Une « porte sans écran » appelée par un script n'a
pas d'utilisateur** : qui signe le geste est à trancher avant d'écrire 4.1. Et ce que la
reprise enverrait réellement chez Hektor reste à mesurer : commission, charge, facture,
règlement et annulation n'ont pas de case chez lui.

**L'étape 5** : 5.1 reste à Frédéric (les Apps Script) ; 5.2 bute sur les 255 lignes à
plusieurs étiquettes (§ 4.5) en plus de la réserve du 13/11 (chaînes entièrement mortes).

---

## 7. LES OUTILS — tous en lecture seule

Écrits dans le dossier de travail de la session (`scratchpad/audit/`) :

```
instantane.py        le Sheet (API), notre base (PostgREST, temoin chiffre par
                     table) et MODELO -> donnees/
apparier_audit.py    l'appariement INDEPENDANT (ne lit jamais le gel)
comparer_au_gel.py   la comparaison -- le SEUL qui lit le gel
dossiers.py          le dossier complet de chaque ligne a juger
rendre_lots.py       les fiches texte des juges
lire_verdicts.py     les verdicts des juges et des contre-experts
consolider.py        l'exclusivite apres changements, et les consequences
```
