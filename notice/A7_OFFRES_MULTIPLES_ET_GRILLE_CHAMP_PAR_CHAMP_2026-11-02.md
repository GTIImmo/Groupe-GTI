# A7 — LES DOSSIERS À PLUSIEURS OFFRES, ET LA GRILLE DE DÉCISION CHAMP PAR CHAMP

**02/11/2026.** Demande de Frédéric : « peux-tu avant analyser les dossiers à
plusieurs offres si cela est normal, ensuite champ par champ on va décider et
mémoriser le choix avant le rattrapage ».

**LECTURE SEULE.** Rien écrit en base, ni au classeur, ni chez Hektor. Aucun appel
à l'API Hektor, aucun login Google.

---

## § 0. LES DEUX RÉPONSES, EN HAUT DE PAGE

```
① LES DOSSIERS À PLUSIEURS OFFRES : OUI, C'EST NORMAL -- prouve par trois
  mesures independantes. 949 biens sur 10 098 (9,4 %) portent plusieurs offres,
  et 930 de ces 949 ont EXACTEMENT UNE offre acceptee contre 1 100 refusees :
  c'est la signature exacte d'offres concurrentes. Le gel ne s'est trompe
  NULLE PART de facon demontrable (0 cas sur 371 verifies).
  UN SEUL vrai defaut de donnee sur 11 206 offres : la ligne 45225170.

② LA GRILLE CHAMP PAR CHAMP EST PRÊTE, et elle change la question. Sur les
  8 910 ecarts, 2 971 (33 %) ne sont PAS des conflits : le classeur y porte un
  marqueur d'absence (« Autre », « NON TROUVE », « nan ») ou nous portons
  zero. Il reste ~5 900 vrais desaccords, et ils se concentrent sur SEPT
  champs. Les 14 autres pesent moins de 1 000 cases a eux tous.
```

---

## § 1. LES DOSSIERS À PLUSIEURS OFFRES — EST-CE NORMAL ?

### 1.1 Trois mesures, et elles disent toutes OUI

**Mesure A — la fréquence.** Les offres se comptent par BIEN (`hektor_annonce_id`),
pas par dossier :

```
 1 offre   -> 9 149 annonces
 2 offres  ->   818
 3 offres  ->   111
 4 offres  ->    16
 5 offres  ->     2
            --------
            10 098 annonces, 11 206 offres
            949 annonces (9,4 %) portent PLUSIEURS offres
```

Un bien sur onze reçoit plusieurs offres. C'est plausible pour de l'immobilier.

**Mesure B — la signature.** Si ce sont de vraies offres concurrentes, alors un
seul acheteur doit être retenu. C'est exactement ce qu'on lit :

```
nombre d'offres ACCEPTEES par bien multi-offres :
   0 acceptee  ->  15 annonces
   1 acceptee  -> 930 annonces   <-- 98 %
   2 acceptees ->   4 annonces

et les etats de ces 2 057 offres :
   refused  1 100      accepted  938      None 12      proposed 7
```

⭐ **1 100 refusées pour 938 acceptées.** On ne fabrique pas ce profil par
accident : c'est le métier qui l'écrit.

**Mesure C — l'éclatement est VOULU.** 934 des 949 biens multi-offres ont leurs
offres réparties sur **plusieurs dossiers** :

```
 1 dossier  ->  15 annonces
 2 dossiers -> 804
 3 dossiers -> 110
 4 dossiers ->  16
 5 dossiers ->   2
 7 dossiers ->   2
```

⛔ **Ce n'est pas un défaut de chaînage, c'est la bonne règle.** Un acheteur
refusé n'a pas de dossier de vente : il a son propre dossier, qui s'arrête à
son refus. Les regrouper ferait un dossier à cinq acheteurs et une seule vente.

### 1.2 L'épreuve du gel — a-t-il choisi la bonne offre ?

C'est la seule question qui compte pour le rattrapage. Sur les 4 453 offres
gelées :

```
3 652  le bien n'a QU'UNE offre  -- aucun choix a faire
  406  plusieurs offres, l'ACCEPTEE est celle qui est liee
    4  plusieurs offres, TOUTES liees (dont l'acceptee)
   13  plusieurs offres, AUCUNE acceptee
    2  plusieurs acceptees, une seule liee
  371  plusieurs offres, l'acceptee n'est PAS liee   <-- suspect
```

⚠ **Mon critère de départ était mauvais, et je le dis : les 371 ne sont pas un
défaut.** Trois mesures le démontrent :

```
. l'offre acceptee est liee a UNE AUTRE LIGNE du classeur : 363 / 371
  -> chacun est a sa place. Deux lignes du classeur, deux acheteurs, deux offres.
. le compromis ou la vente DE LA MEME LIGNE est dans le meme dossier que
  l'offre liee : 164 ; dans celui de l'acceptee : 0
  -> la cascade n'a contredit son propre compromis dans AUCUN cas.
. les deux offres portent la MEME SECONDE : 0 / 371
  -> ce n'est pas le defaut d'ordre deja connu.
  acquereurs differents : 367 / 371  ·  ecart de date > 30 j : 323 / 371
```

Les 8 restantes : l'offre acceptée du bien n'est liée à aucune ligne. Six
appartiennent à des cohôrtes anciennes (2012, 2020, 2022) que le classeur ne
couvre pas — le même profil que les 54 coquilles. ⭐ Et une se règle toute
seule : `91f7522b` désigne l'offre 30784, qui est l'un des **deux liens neufs**
à ajouter au gel (A6 § 1).

### 1.3 Les quatre lignes à plusieurs offres — une par une

Jamais deux compromis, jamais deux ventes : le multiple ne touche que l'offre.

```
045ecde7  annonce 58932, mandat 18152, compromis 69 000 au 05/12/2025
          offre 28558  accepted  montant VIDE  06/11/2025  acq 321467  DISPARUE de Hektor
          offre 28559  accepted  69 000        03/04/2026  acq 602846  vivante
          -> un VESTIGE + la vraie. Et RUSSIER Paul porte DEUX id de contact
             (321467 et 602846) : un doublon de fiche chez Hektor.

45225170  annonce 61672, mandat 18426, compromis 160 000 au 26/10/2026
          offre 30712    accepted   16 000  proposee 30/09 16:12:42, acceptee 06/10
          offre 1001361  proposed   16 000  proposee 06/10 13:51:20  (NEE CHEZ NOUS)
          offre 30767    accepted  160 000  proposee 30/09 16:14:37, acceptee 26/10
          -> ⭐ UNE FAUTE DE FRAPPE : 16 000 au lieu de 160 000, un zero oublie.
             Le compromis dit 160 000. Les trois existent chez Hektor
             (present_in_hektor = 1 pour les trois).

KT0601S6  annonce 47989, mandat 4413, compromis 78 400 au 02/08/2021
          offre 24290  accepted  78 400  24/06/2021 22:00:00  acq 397430
          offre 24291  refused   78 400  24/06/2021 22:00:00  acq 397430
          -> ⛔ MEME SECONDE, MEME MONTANT, MEME ACQUEREUR, ETATS OPPOSES.
             C'est le defaut d'ordre deja connu (A6 § 2, audit du 02/11 § 3
             quinquies) : l'etat vient du type de la DERNIERE ligne, et rien ne
             tranche a date egale. L'un des deux etats est faux.
          ⚠ Et la VENTE porte un AUTRE acheteur (FENON Clement, 398942).
             Une offre acceptee n'est pas une vente.

f1aedc01  annonce 47146, mandat 18710, compromis 76 500 au 04/09/2026
          offre 28966  accepted  78 500  19/08/2026  vivante
          offre 28967  proposed  VIDE    05/08/2026  DISPARUE de Hektor
          -> un VESTIGE + la vraie. L'ecart 78 500 -> 76 500 est une
             negociation, c'est normal.
```

### 1.4 Les cinq points réels — et ils sont tous petits

```
① UNE faute de frappe : 45225170, l'offre a 16 000 au lieu de 160 000.
   ⛔ Les trois offres sont CHEZ HEKTOR. On ne requalifie pas une fiche contre
   Hektor -- on peut la masquer a l'affichage, pas la corriger en douce.

② 17 VESTIGES dans tout le registre (present_in_hektor = 0) :
   5 offres · 11 compromis · 1 vente, sur 31 124 lignes. Deux offres sont
   liees au classeur. Marginal, mais a connaitre.

③ 5 chaines ou deux offres portent la MEME SECONDE avec des etats
   DIVERGENTS : 10920, 24289, 25378, 25435 (+1). C'est le defaut d'ordre,
   deja ouvert, qui toucherait les 11 206 offres si on y touchait.

④ 4 biens a DEUX offres acceptees : 43437, 58932, 62097, 61672. Trois sont
   expliques par un vestige, le quatrieme est la faute de frappe. Aucun cas
   de deux acheteurs reellement acceptes sur le meme bien.

⑤ 13 lignes du classeur sur des biens SANS aucune offre acceptee. Normal :
   la vente peut se faire sans que l'offre soit passee en « acceptee » chez
   Hektor. ⛔ Et cela n'a aucun effet sur le rattrapage : le gel est par
   TRANSACTION, pas par etat d'offre.
```

---

## § 2. LA GRILLE DE DÉCISION CHAMP PAR CHAMP

### 2.1 Ce que je sais maintenant et que je ne savais pas ce matin

A6 disait « 8 909 cases remplies des deux côtés et différentes ». C'est juste,
mais ⭐ **un nombre d'écarts ne dit pas s'il s'agit de fond ou de forme**, et te
faire trancher sans le savoir serait te faire décider à l'aveugle. J'ai donc
classé les 8 910 écarts par **CAUSE** :

```
2 948  33,1 %  le CLASSEUR ne sait pas (« Autre », « NON TROUVE », « nan »)
2 082  23,4 %  DEUX DATES differentes
1 838  20,6 %  ecart reel, mais notre valeur est ILLISIBLE dans le rapport
1 623  18,2 %  DEUX TEXTES differents
  368   4,1 %  DEUX NOMBRES differents
   23   0,3 %  NOUS ne savons pas (vide ou zero)
   16   0,2 %  un facteur EXACTEMENT 2 (une part contre un total)
   12   0,1 %  un facteur 1,20 (HT contre TTC)
```

⚠ **Une correction que je dois faire sur mon propre travail.** J'ai d'abord
cru que les 1 838 « illisibles » étaient un faux positif du rapport. En
relisant le code (`rapport_gel_tous_les_champs.py`, `mots_du_nom` et le
`verdict`), c'est faux : **le verdict est calculé sur l'intersection des mots et
il est juste.** Ce n'est que la colonne AFFICHÉE qui est illisible (elle imprime
toutes les combinaisons collées). Donc ces 1 838 sont de **vrais écarts** — on
ne peut simplement pas lire, dans le CSV, laquelle des deux valeurs est bonne.
⛔ Réserve d'audit à traiter : imprimer la valeur BRUTE à côté du jeu de mots.

### 2.2 Les sept champs qui portent le problème

```
CHAMP              ECARTS   LA CAUSE, MESUREE                       MA RECOMMANDATION
Vente Prevue        1 767   dates ; 47 % apres / 53 % avant,        AU CARNET, le classeur
                            dispersion totale -> vrai desaccord     fait foi en attendant
Nature              1 653   1 603 fois le classeur dit « Autre »   NOUS. Ce n'est pas un
                            -> il ne porte RIEN                     conflit : c'est un vide
Ville               1 644   1 335 fois « NON TROUVE »              NOUS. Idem. Reste 309
                            -> son propre calcul a echoue           vrais ecarts a lister
Notaire             1 373   85 % de nos valeurs portent l'OFFICE    A LISTER. 67 % de
                            quand le classeur porte LA PERSONNE     desaccord = defaut
                            (« Latour » vs « OFFICE DE CRAPONNE ») systematique a creuser
Agence                498   ⭐ le mecanisme MARCHE (CRAPONNE <->    A TOI DE DIRE si
                            Groupe GTI Craponne, 383 fois juste).   « ST DIDIER » est une
                            Donc 498 VRAIS desaccords : le classeur agence reelle. Je ne
                            dit ST DIDIER (80), LE PUY (69),        tranche pas seul.
                            AMBERT (64)... nous disons Firminy
Negociateur 1         432   91 « utilisateur supprime » + 122      LE CLASSEUR sur les 213
                            « Groupe GTI » (l'agence, pas la       ou nous ne savons pas.
                            personne) = 213 ou NOUS ne savons pas ; Les 219 autres : LISTER
                            219 = deux personnes differentes        ⛔ c'est LA PAIE
Negociateur 2         374   6 supprimes + 111 « Groupe GTI »       idem, et ⛔⛔ le piege
                            = 117 ; 257 deux personnes differentes  deja paye : nous en avons
                                                                    209, le classeur 685 --
                                                                    une liste blanche
                                                                    EFFACERAIT nos 209
```

⭐ **Deux de ces sept ne sont pas des conflits du tout** : Nature et Ville, soit
**2 938 cases** où le classeur porte un marqueur d'échec. La décision y est déjà
prise (nous faisons foi, phase B les écrira vers le classeur).

### 2.3 Les quatorze autres champs — moins de 1 000 cases à eux tous

```
Offre Achat    210 ecarts  ⭐ 92 % NOUS APRES le classeur (117 a plus de 10 j).
                           Mesure sur 45225170 : la proposition est au 30/09,
                           l'acceptation au 06/10. -> CE NE SONT PAS DEUX
                           VALEURS, CE SONT DEUX EVENEMENTS. Le classeur porte
                           la date de l'offre, nous celle de l'acceptation.
                           ⛔ Ne pas « corriger » : comparer a la 1re proposition.
Prix           208 ecarts  3 688 deja « hors perimetre » (avant 2025, prix
                           d'annonce). Les 208 restants sont sur 2025-2026.
                           -> partage PAR ANNEE : nous des 2025.
Etat Actuel    161 ecarts  vocabulaire d'avancement. A LISTER.
Mandat         133 ecarts  numeros differents. ⚠ 134 lignes ont deja un numero
                           de mandat divergent (journal d'appariement).
Acquereur      120 ecarts  106 textes + 13 illisibles. A LISTER (identite).
Commission TTC  85 ecarts  ⭐⭐ 16 a un facteur EXACTEMENT 2 (2 750 / 5 500,
                           4 500 / 9 000, 4 000 / 8 000) -> le classeur porte
                           UNE PART quand nous portons LE TOTAL. C'est le sujet
                           du chantier ⑧ (repartition). 22 fois nous sommes a
                           zero -> le classeur fait foi. 12 a un facteur 1,20
                           -> HT contre TTC, deja connu.
product_ref    69 ecarts   references croisees (VM66518 contre VS046). A LISTER.
Vendeur        68 ecarts   51 textes + 17 illisibles. A LISTER (identite).
Vente Fixee    61 ecarts   79 % nous APRES. A LISTER.
Compromis      44 ecarts   52/48, disperse. A LISTER. ⚠ volume faible : 44 sur
                           4 249 compromis geles = 1,0 %. Le champ est SAIN.
Negociateur 3   9 ecarts   negligeable, mais ⛔ meme regle que Negociateur 2.
Charge Commission  0 ecart 933 « classeur seul », 3 747 vides des deux.
                           -> A NOUS (colonne CLASSE A), aucun conflit possible.
Vente Reglee       0 ecart 3 721 « classeur seul ». -> AU CLASSEUR (ou carnet).
Numero facture     0 ecart 3 694 « classeur seul ». -> AU CLASSEUR (ou carnet).
```

### 2.4 ⭐⭐ LA RÈGLE DE SÛRETÉ — je la propose comme non négociable

```
UN ECART NE SE RESOUT JAMAIS TOUT SEUL.
« lister » est le DEFAUT de tout champ dont le proprietaire n'a pas ete
declare explicitement.
```

Sans ce défaut, un champ oublié se fait écraser en silence. Le risque est
**déjà prouvé** sur Negociateur 2 : nous en portons 209, le classeur 685. Mettre
ce champ en liste blanche « le classeur fait foi » **effacerait nos 209**.

### 2.5 Et les quatre cas, pour chaque case

```
cas 1  le classeur sait, nous pas    10 437 cases  -> DEJA DECIDE : on prend
cas 2  nous savons, le classeur pas   9 077 cases  -> phase B : on ecrit
cas 3  les deux savent, d'accord     49 181 cases  -> rien a faire
cas 4  les deux savent, DESACCORD     8 910 cases  -> LA QUESTION OUVERTE
                                                      dont 2 971 faux conflits
                                                      et ~5 900 vrais
```

---

## § 3. COMMENT MÉMORISER LE CHOIX

⛔ **Rien n'est créé : j'attends ton go.** Ce qui est proposé :

```
TABLE  app_champ_propriete        -- une ligne par champ, lue par le worker (JS)
                                     ET par les scripts (PY)
  champ            text    'Negociateur 1', 'Prix', ...
  qui_fait_foi     text    'nous' | 'classeur' | 'lister' | 'hors_perimetre'
  depuis_quand     date    NULL sauf le Prix (2025-01-01)
  sur_conflit      text    'lister' | 'ecraser' | 'ignorer'   defaut 'lister'
  actif            bool
  decide_le        date
  decide_par       text
```

⭐ **Quatre colonnes, pas deux** — parce que le Prix se partage par ANNÉE et que
« qui fait foi » ne dit pas « que faire quand les deux savent ».

⛔⛔ **Et ne pas créer une sixième liste.** La règle « quel champ va où » existe
déjà **cinq fois** dans le code (`CHAMPS_CARNET_PAR_CHARGE`, `REGISTRE_PAR_HEKTOR`,
`CARTE_VUE`, `NOS_COLONNES`, `CHAMPS_APP_AFFAIRE`). Cette table doit les
remplacer, pas s'y ajouter.

---

## § 4. CE QU'IL RESTE À DÉCIDER — par toi

```
① LA REGLE DE SURETE du § 2.4 : « lister » par defaut. OUI / NON ?
② LES SEPT CHAMPS du § 2.2, un par un.
③ « ST DIDIER », « LE PUY », « MONTBRISON » : sont-ce de vraies agences ?
   498 cases en dependent, et je ne tranche pas seul.
④ Vente Prevue (1 767) : au carnet, et qui fait foi en attendant ?
⑤ La faute de frappe 45225170 : on masque l'offre a 16 000, ou on la laisse ?
⑥ Les 2 liens neufs a ajouter au gel (1a474908 -> 30784, cd29653f -> 30785).
⑦ La reserve d'audit du § 2.1 : imprimer la valeur BRUTE dans le rapport.
```

⛔ **LE VERROU INCHANGÉ DEPUIS LE 22/10** : lire les Apps Script du classeur
(`Sheet1` nourrit LA PAIE, ~10 min, c'est à toi). Tant que ce n'est pas lu, la
**phase B ne démarre pas** — mais tout le § 2 peut être décidé et mémorisé
sans l'attendre.

---

## § 5. PROVENANCE DES CHIFFRES

```
§ 1       mesure DU JOUR (02/11) sur phase2/phase2.sqlite, miroir verifie a jour
          (68 offres sans date, VA30102 reunie en chaine 10798)
§ 2       notice/A4_RAPPORT_GEL_TOUS_LES_CHAMPS_2026-10-29.csv, 4 680 lignes
          ⚠ DATE DU 29/10. Le gel a gagne 2 lignes depuis, les valeurs ont pu
          bouger a la marge. ⛔ Je n'ai PAS relance le rapport : son script
          ecrit par-dessus les fichiers du 29/10 (noms de sortie en dur) et
          demande un login Google. A faire sur ton accord, apres avoir date
          les noms de sortie.
```
