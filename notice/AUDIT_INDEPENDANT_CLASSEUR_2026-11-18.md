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
OXQSBZ9V  -> 515RUEN3   offre 17430 et compromis 17427
RX6J289Y <-> CITFQGOB / R0JRVFDC   compromis 16377 / 16378
Q602VZJX <-> EGR8KXOL   compromis 6554 / 6555
```

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
(257 lignes jugées : verdict, décision de chaque lien, transaction à rattacher, preuve, raison,
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
18/11 au soir (3 juges + contre-expertise), le plan de correction viendra après.

**LES QUESTIONS QUE SEUL FRÉDÉRIC PEUT TRANCHER** (lignes INCERTAIN) :
`YRUF0S9H` / `3308P0UX` (la même offre VIALLARD saisie deux fois : quelle ligne la garde ?) ·
`O6R10ZQA` / `T2GZOY5O` (même affaire PAOLONE, deux lignes) · `SHN6RKDI` (le compromis 26613
était-il préparé pour MOSNIER ?) · `5QE9107L` (le compromis 20088 suit-il la 1re ou la 2e offre
DEBARD ?) · et, dans les PARTIEL : `5a956cad` (une offre renégociée : l'offre d'origine ou
l'acceptée ?), `1D7EIYKW` (un compromis signé après l'annulation : seconde tentative ?),
`E9GL6MUS` (FIGARI est-elle la co-acquéreuse de SOUBEYRAND ?).

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
