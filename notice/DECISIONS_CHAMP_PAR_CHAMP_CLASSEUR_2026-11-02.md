# DÉCISIONS CHAMP PAR CHAMP — LES 38 COLONNES DU CLASSEUR

**02/11/2026.** Revue menée avec Frédéric, colonne par colonne, **avant le
rattrapage**. Sa consigne : « champ par champ on va décider et mémoriser le
choix avant le rattrapage ».

⛔ **CE FICHIER EST LA SOURCE DE VÉRITÉ DES DÉCISIONS.** La table
`app_champ_propriete` sera remplie à partir d'ici, pas l'inverse. Tant qu'une
colonne est marquée ⬜, **rien ne s'écrit pour elle**.

---

## § 1. L'ÉTAT DE LA REVUE

```
TRANCHEES          7 colonnes   I J K L M N  +  Q (02/11)
RESTE A VOIR      31 colonnes
                 -------------
                  38 colonnes
```

---

## § 2. ⭐ LES DÉCISIONS PRISES — LOT 1, LA RÉPARTITION ET LA PAIE

### ✅ I — Négociateur 1 · **LE CLASSEUR FAIT FOI**

```
decision        le classeur fait foi SUR LES 432 ECARTS
prise le        02/11/2026, par Frederic
sur conflit     ecraser (le classeur gagne)
```

**Ce qu'il savait en décidant** : 4 774 cases remplies au classeur, 99 noms
distincts, 432 écarts. Dans 213 de ces 432, **c'est nous qui ne savons pas**
(91 « cet utilisateur a été supprimé », 122 « Groupe GTI » c'est-à-dire
l'agence au lieu de la personne). Les **219 autres désignent deux personnes
différentes**, et il a choisi de les écraser aussi, au-delà de ma
recommandation qui proposait de les lister.

⛔ **PRÉALABLES OBLIGATOIRES, non optionnels** :
```
. les 14 anciens negociateurs CREES dans l'annuaire d'abord
  (sinon 213 cases pointent vers un negociateur qui n'existe pas chez nous)
. la table d'ALIAS : GIRAUD = Aline VALETTE (68) · ALVES MENDES = Lucie
  DECHANDON (178) -- sans elle on ajoute la meme personne deux fois et on
  coupe sa commission en deux, sur 282 cases
. « meilleursagents », « GTI », « DENOPCE 1/2 » EXCLUS -- ce ne sont pas des
  personnes (meilleursagents : 17 fois sur 17 en negociateur 2, c'est un
  apporteur)
. les 30 dossiers « notre nom est etranger aux deux » ECARTES
```

### ✅ K et M — Négociateurs 2 et 3 · **LE CLASSEUR FAIT FOI PARTOUT**

```
decision        le classeur fait foi PARTOUT
prise le        02/11/2026, par Frederic
sur conflit     ecraser (le classeur gagne)
```

**Ce qu'il savait en décidant** : le classeur porte **687** seconds
négociateurs et **13** troisièmes ; nous portons **209** valeurs et **15**
lignes de rang supérieur à 1. Sur les 374 écarts, 117 sont des cases où nous
ne savons pas et 257 désignent deux personnes. Le risque de la liste blanche
lui a été dit : il a tranché quand même.

⚠⚠ **UNE PRÉCISION QUE JE N'AI PAS ENCORE SA CONFIRMATION** — et elle compte :
```
« faire foi » s'applique a une VALEUR, pas a une ABSENCE. J'applique donc :
le classeur gagne PARTOUT OU IL PORTE QUELQUE CHOSE, et la ou il est VIDE
nous gardons ce que nous avons.
Sinon ses 687 valeurs effaceraient nos 209 sur les lignes ou il n'a rien
ecrit -- une destruction qu'aucune source ne demande.
⬜ A LUI CONFIRMER. S'il veut aussi vider nos cases quand le classeur est
   vide, il le dira et je corrigerai cette ligne.
```

### ✅ J, L, N — les trois Pourcentages · **LE CLASSEUR PARTOUT, SANS EXCEPTION**

```
decision        le classeur fait foi PARTOUT, SANS EXCEPTION
prise le        02/11/2026, par Frederic
sur conflit     ecraser (le classeur gagne), y compris sur nos origines
                « hektor » (501 lignes) et « saisie » (20 lignes)
```

**Ce qu'il savait en décidant** :
```
⭐⭐⭐ LA SOMME DES TROIS POURCENTAGES FAIT EXACTEMENT 100 dans 4 768 cas sur
     4 780, soit 99,75 %. C'est la colonne la MIEUX TENUE des 38.
     Les 5 anomalies : 2 lignes a 50, 2 a 200, 1 a 150. Plus 7 lignes sans
     pourcentage 1.
⭐  Les pourcentages sont LISIBLES A 100 % : 4 773 / 4 773.
⛔  En face, app_affaire_repartition porte 16 106 lignes dont 15 581
     marquees « hektor_partage_suppose » (96 %) -- un calcul par defaut, pas
     une donnee. Et 15 lignes seulement de rang > 1.
     Le classeur en porte 687 + 13.
```
Il a choisi d'écraser **aussi** nos 501 lignes d'origine « hektor » et nos 20
« saisie », au-delà de ma recommandation qui proposait de les protéger.

⚠ **PIÈGE DE FORMAT, à coder** : `Pourcentage 3` porte **« 12,5 »** avec une
**virgule**. Une conversion naïve rend 125, ou zéro. Un seul cas, mais il
suffit à fausser une paie.

---

## § 3. ✅ TRANCHÉ — Q, Charge Commission

**AUDIT FAIT le 02/11, à sa demande** (« il va falloir auditer avant car il y a
la charge de la commission ou similaire déjà dans mon projet »). Il avait
raison, et voici ce qui existe :

```
. apps/hektor-v1/src/App.tsx:5735 -- un menu « Charge des honoraires »
  (Acquereur / Mandant), champ honorairesCharge
  ⛔ MAIS c'est un champ du BROUILLON DE DOCUMENT DE MANDAT, pas une donnee
     d'affaire : il sert a cocher la case du PDF (« la totalite des honoraires
     sera a la charge du : MANDANT / ACQUEREUR », App.tsx:4803)
. ⛔ IL N'EST PAS PERSISTE : aucune colonne en base, rien dans supabase/
. ⛔ SA VALEUR EST UN DEFAUT AUTOMATIQUE :
     honorairesCharge: rawHonoraires ? 'acquereur' : ''
     -- des qu'il y a des honoraires on ecrit « acquereur », personne ne l'a dit
. ⛔ HEKTOR NE PORTE RIEN : les 1 847 payloads du registre contenant le mot
     ont ete deballes, ZERO cle de charge
. charge_commission_app : la colonne existe, VIDE A 100 % (0 / 12 413)
. le classeur : 955 lignes -- Vendeur 894, Acquereur 61
```

⚠ **DEUX PIÈGES à traiter si on remplit** :
```
① LE VOCABULAIRE : le classeur dit « Vendeur », l'app dit « mandant ».
  Meme notion, deux mots -- et notre « Mandant » est POLLUE depuis le 17/07
  (l'acheteur y est range a tort).
② DEUX OBJETS : la charge du MANDAT (signee au depart) n'est pas forcement
  celle de la VENTE (ce qui s'est passe).
```

---

### ✅ SA DÉCISION DU 02/11

```
decision      LE CLASSEUR FAIT FOI
prise le      02/11/2026, par Frederic
pour le passe « quand on va reprendre la colonne on completera les lignes
              possibles » -- donc au RATTRAPAGE, et seulement les lignes
              qu'on peut relier (955 renseignees sur 4 780)
pour l'avenir la saisie se fait dans l'app, et elle est REPAREE (voir ci-dessous)
```

⭐ **Risque nul sur l'existant** : `charge_commission_app` ne porte que **8
valeurs**, toutes des essais. Il n'y a rien à écraser.

---

## § 3 septies. ⭐ LA CHARGE N'EST PAS AU REGISTRE, ET L'API NE L'A PAS POUR 116 MANDATS

**02/11, le soir.** Deux questions de Frédéric, deux réponses mesurées.

### 1. Non, la charge n'est pas remontée au registre

```
app_mandat_register_current : 70 colonnes
  liees aux honoraires ou a la charge : AUCUNE
  (il y a mandat_montant, mais MESURE : il porte LE PRIX, pas les honoraires
   -- mandat 18569 : prix 70 000 et mandat_montant 70 000, identiques)
```

La valeur arrive chaque nuit dans `hektor_annonce_detail.honoraires_json` et
**s'arrête là**. Personne ne la remonte. La colonne
`mandat_charge_honoraires_app`, posée le 02/11 en Supabase, est **vide**, et elle
attend une saisie humaine — pas la valeur de Hektor.

### 2. Les 116 mandats de 2026 sans charge : L'API NE L'A PAS

**Mesuré en trois temps, du moins cher au plus cher.**

```
a) DANS LE MIROIR, sur les 116 :
     honoraires_json = 'null'            75
     honoraires_json RENSEIGNE           25   <- defaut de MON appariement, voir reserve
     aucune ligne de detail              16

b) DANS LA REPONSE BRUTE CONSERVEE (raw_api_response), sur les 75 :
     cle « honoraires » presente dans 100 % des 61 462 reponses
     valeur = null sur les 75, chemin /data/honoraires

c) EN DEMANDANT A HEKTOR, EN DIRECT le 02/11 au soir (12 appels, lecture seule) :
     11 mandats de 2026     -> honoraires = null
     TEMOIN POSITIF 61398   -> [{"id":"84962","taux":"12000","charge":"vendeur"}]
```

⭐ **Le témoin positif est décisif** : le même appel, la même seconde, rend la
donnée pour un bien qui l'a. Donc **ce n'est ni notre lecture, ni la fraîcheur du
miroir** (des cibles lues le 31/10 sont null, et l'appel en direct le confirme).
**Hektor n'a pas la valeur pour ces biens : elle n'y a pas été saisie.**

```
ET CE N'EST PAS QUE DES ESTIMATIONS -- les 11 cibles, par statut :
   Actif 3 (dont 18353, EXCLUSIF, 192 400 €)  ·  Sous compromis 2
   Vendu 1  ·  Clos 3  ·  Estimation 2
   91 des 116 portent un montant de mandat, donc le bien est bien commercialise.
```

⚠ **C'est donc une anomalie de SAISIE à l'agence, pas un défaut technique** — et
elle touche des biens **actifs et vendus** de 2026. Rien à corriger dans le code :
à signaler à ceux qui saisissent.

### ⛔ MES DEUX RÉSERVES, NOMMÉES

**Réserve 1 — mon « clé absente » était FAUX.** Ma première fonction de recherche
s'arrêtait à 4 niveaux de profondeur et ne lisait que les 4 premiers éléments
d'une liste : elle a rendu « clé absente » 75 fois sur 75, alors que la clé est
présente dans **100 %** des réponses. Un `LIKE` sur le texte brut l'a démenti.
C'est [[lecture-ratee-n-est-jamais-un-vert]], en faux négatif : **une mesure qui
ne trouve rien doit d'abord être soupçonnée, elle.**

**Réserve 2 — DEUX APPARIEMENTS annonce → mandat donnent deux résultats, et je ne
tranche pas.**

```
par hektor_annonce.no_mandat        10 188 mandats   8 421 vendeur  1 767 acquereur
par le lien du registre             8 571 mandats    8 467 vendeur    104 acquereur
                                                                     ^^^^^^^^^^^^^
                                                     L'ECART EST ENORME
les deux liens sont COHERENTS la ou ils coexistent : 93,4 % identiques,
6,6 % se recoupent, ZERO cas disjoint sur 18 167 mandats
```

Donc l'écart ne vient pas d'un conflit mais du **périmètre** : `no_mandat` ramasse
des annonces que le registre ne pointe pas, et ce sont elles qui portent presque
tout l'« acquéreur ». ⛔ **Avant tout rattrapage, il faut trancher quelle annonce
fait foi pour un mandat** — sinon on écrirait la charge d'une annonce voisine.
Les chiffres du § 3 sexies sont ceux de `no_mandat` : **ils sont donc à revoir à
la lumière de cette réserve.**

⛔ **Rien n'a été écrit** : miroir ouvert en `mode=ro`, et les 12 appels à Hektor
n'ont posé ni `sync_run` ni `upsert`. Arrêt prévu au premier refus, aucun refus.

---

## § 3 sexies. ⭐⭐⭐ LA CHARGE ÉTAIT DÉJÀ CHEZ NOUS — HEKTOR NOUS LA LIVRE CHAQUE NUIT

**02/11, le soir.** Frédéric : *« oublie ce classeur, cette information doit bien
être visible quelque part dans mon projet, vérifie les données récupérées par un
appel id annonce dans le détail bloc mandat »*. **Il avait raison.** Je n'ai pas eu
besoin d'ouvrir Hektor : c'est dans notre miroir.

```
data/hektor.sqlite -> table hektor_annonce_detail -> colonne honoraires_json

  [{"id": "31", "taux": "5000", "charge": "vendeur"}, ...]
                                 ^^^^^^^^^^^^^^^^^^
                      LE CHAMP EST EXPLICITE, en clair, pas un code
```

```
MESURE : 61 459 lignes de detail, 14 302 portent un bloc honoraires
  valeurs rencontrees : « vendeur » 62 571 lignes · « acheteur » 19 352
  (Hektor dit « acheteur », notre vocabulaire dit « acquereur »)
  AUCUNE valeur vide, les 3 cles sont toujours la (id, taux, charge)
  par annonce : 11 030 vendeur · 3 258 acheteur · 14 se contredisent
  -> 10 188 MANDATS avec un verdict net (8 421 vendeur, 1 767 acquereur)
```

⚠ Le code de l'app lit déjà un bloc voisin, `mandat_infofi`, avec les clés
`HONORAIRES`, `HONORAIRES_ACQUEREUR`, `PRIXNETVENDEUR` et `CHARGES`
(`App.tsx` l. 3983 et suivantes). **Mais le champ qui tranche est `charge` dans
`honoraires_json`** — celui-là n'est lu par personne aujourd'hui.

### ⭐⭐ LE TÉMOIN CROISÉ : LES DEUX SOURCES SE VALIDENT

```
8 314 mandats presents dans LES DEUX sources :
   hektor=vendeur    modelo=vendeur     6 819
   hektor=acquereur  modelo=acquereur     958
   hektor=acquereur  modelo=vendeur       414   <- desaccords
   hektor=vendeur    modelo=acquereur     123   <-
   ACCORD : 7 777 / 8 314 = 93,5 %
```

C'est une mesure dans les deux sens, pas une confirmation de confort : chacune
des deux sources a été établie sans l'autre. ⚠ Les **537 désaccords (6,5 %)**
restent à trancher ; Hektor est la source vivante, donc **Hektor gagne**, mais
cela doit être écrit, pas supposé.

### ⭐⭐⭐ ET SURTOUT : HEKTOR COUVRE LE RÉCENT, QUE LE FICHIER NE COUVRAIT PAS

```
LES DEUX SOURCES REUNIES -- Hektor d'abord, Modelo en secours
annee   registre   Hektor   Modelo   AUCUNE   couvert
2012       1 417      421       23      973    31,3 %
2013       2 158       63        9    2 086     3,3 %   <- LE TROU
2014       2 136       15       37    2 084     2,4 %   <- LE TROU
2015       1 154      424      718       12    99,0 %
2016       1 065       65      981       19    98,2 %
2017       1 018      515      488       15    98,5 %
2018         899      836       60        3    99,7 %
2019         831      818        9        4    99,5 %
2020         716      641       66        9    98,7 %
2021         888      776      104        8    99,1 %
2022       1 021      942       71        8    99,2 %
2023       1 052      990       54        8    99,2 %
2024         901      855       38        8    99,1 %
2025         789      717        0       72    90,9 %   <- Hektor SEUL
2026         682      566        0      116    83,0 %   <- Hektor SEUL
TOTAL     18 260    9 653    3 051    5 556    69,6 %
```

**Les deux sources sont complémentaires, pas concurrentes** :
Hektor tient 2018→2026 à 90-99 %, Modelo bouche 2015→2017 où Hektor est muet.
De 2015 à 2024 la couverture réunie est de **98 à 99,7 %**.

```
REPARTITION FINALE sur les 12 704 mandats couverts :
   vendeur    8 440
   acquereur  4 264
```

### Ce que cela change pour le chantier

```
✅ LE RATTRAPAGE N'A PLUS BESOIN DU CLASSEUR NI DE DEDUCTION sur 2015->2026 :
   la valeur est CONSTATEE, et pour 2018->2026 elle vient de Hektor lui-meme.
✅ LES MANDATS A VENIR SE REMPLISSENT TOUT SEULS : le bloc descend chaque nuit.
   La piece H (porte de saisie) n'est plus la seule voie -- elle devient le
   RATTRAPAGE A LA MAIN des cas que Hektor ne porte pas.
⬜ LE TROU RESTANT : 2012-2014, 5 143 mandats, ni l'un ni l'autre. Non explique.
   Piste a mesurer : leurs annonces n'ont peut-etre jamais eu de detail descendu.
⬜ 2025-2026 : 188 mandats manquants. Piste : le run ne relit le detail QUE si
   la datemaj change ([[run-de-nuit-relit-le-detail-seulement-si-datemaj-change]]).
⚠ 2 258 annonces portent un verdict mais AUCUN no_mandat -> perdues pour le
   registre en l'etat.
⬜ LES 30 MANDATS dont les annonces se contredisent, et les 537 desaccords
   Hektor/Modelo : a trancher un par un, jamais en masse.
```

⛔ **Rien n'a été écrit.** Lecture seule, sur le miroir ouvert en `mode=ro`
pour ne poser aucun verrou ([[phase2-sqlite-verrou-ecriture-long]]).

---

## § 3 quinquies. ⭐⭐⭐ LE CODE EST DÉCODÉ — ET IL NE FAUT PAS S'EN SERVIR

**02/11, le soir.** La passe propre, **un mandat par ligne**, est faite. Elle a
trouvé mieux qu'un décodage de `fees_paid_by_who` : **un témoin arithmétique**
interne à chaque ligne, qui ne dépend d'aucune interprétation.

```
LE TEMOIN, sur le mandat 16699 :
   price            134 000
   price_seller_net 124 700
   fees               9 300     et 134 000 - 124 700 = 9 300  EXACTEMENT
-> le prix AFFICHE inclut les honoraires, le vendeur touche le net
-> C'EST LE VENDEUR QUI PAIE

L'AUTRE FORME, sur le mandat 16662 :
   price             34 000
   price_seller_net  34 000     le vendeur touche TOUT
   fees                   0
   fees_paid_by_buyer 3 500     les honoraires sont LA
-> C'EST L'ACQUEREUR QUI PAIE

LA REGLE RETENUE, sans jamais lire le code :
   fees_paid_by_buyer > 0                        -> acquereur
   sinon fees > 0 et (price - price_seller_net) = fees -> vendeur
```

⛔ **Pourquoi mon croisement du 02/11 après-midi ne tranchait pas** : je le
croisais avec `legal_notice`, qui vaut `{"fr":"","en":""}` — **vide**. Je
comparais à un témoin absent. Voir [[un-zero-ne-se-croit-pas-sans-temoin-positif]].

### Ce que valent les codes, mesuré — et pourquoi on les écarte

```
code 2 -> VENDEUR     9 150 lignes sur 9 178 ou les 3 temoins disent vendeur
code 3 -> ACQUEREUR  14 947 lignes sur 16 778
   ⚠ MAIS 1 729 lignes de code 3 disent VENDEUR : 1 703 sont des LOCATIONS
     (product_offer_type = 2) et 26 sont de vraies ventes mal etiquetees.
code 1 -> PARTAGE / incoherent : 80 lignes disent « les deux », 36 acquereur,
     40 vendeur, sur 177. Aucun sens stable.
code 0 -> 76 lignes, non renseigne.
```

**Conclusion : le code n'est pas fiable, l'arithmétique l'est.** On ne se sert
que d'elle. Voir [[un-commentaire-de-code-n-est-pas-une-mesure]] : ici le code
*numérique* joue le rôle du commentaire, et le calcul joue celui de la mesure.

### ⛔⛔ LE FICHIER N'EST PAS UNE LISTE DE MANDATS

```
26 404 lignes, mais :
  product_ref       26 180 valeurs distinctes  -> c'est UN BIEN par ligne
  colonne B         18 290 distinctes seulement, une valeur vue jusqu'a 13 fois
```

**Deux systèmes de numérotation sont superposés dans le fichier** :

```
mandat « 15033 », ligne   381 : product_ref VT642    custom 15033   cree 2022-09-14 -> vendeur
mandat « 15033 », ligne 24447 : product_ref VM57314  custom M15033  cree 2011-01-24 -> acquereur
                                external_key « sphere... »
```

Les lignes dont `product_ref_custom` commence par **M** et dont l'`external_key`
commence par **sphere** viennent de **l'ancien logiciel d'avant Hektor** (9 319
lignes). Leur numéro n'est pas un numéro de mandat Hektor, et **Hektor a
réattribué ces numéros** à d'autres biens. Les croire ferait écrire la charge
d'un bien de 2011 sur un mandat de 2022.
Voir [[hektor-recycle-ses-id-mandat-corps-recopie]] et
[[ne-jamais-s-accrocher-a-une-position-toujours-a-un-identifiant]].

```
LE FILTRE QUI DEPARTAGE : la ligne doit porter « Num mandat » dans ses
observations, ET ce numero doit EGALER la colonne B.
   -> 14 364 lignes retenues, 11 676 numeros de mandat distincts
   -> 370 numeros se contredisent encore (a trancher un par un, pas en masse)
```

### ⭐⭐ LE VERDICT, ET IL CONTREDIT LE 90 %

```
11 002 mandats de VENTE mesures :
   vendeur       6 917   62,9 %
   acquereur     3 960   36,0 %
   indecidable     125    1,1 %
```

**Pourquoi l'écart avec le classeur (93,7 %) ?** Parce que la pratique a
**basculé en 2017**, et le classeur ne couvre que la période récente :

```
LA CHARGE PAR ANNEE DE CREATION -- mandats de vente
  annee   total  vendeur  acquereur   % vendeur
  2015    1 449        7      1 433      0,5 %
  2016    1 422       12      1 402      0,8 %
  2017    1 312      570        731     43,8 %   <- LA BASCULE
  2018    1 138    1 021        114     90,0 %
  2019    1 039    1 009         29     97,2 %
  2020      817      788         23     97,2 %
  2021    1 041      930        105     89,9 %
  2022    1 108    1 031         63     94,2 %
  2023      965      901         49     94,8 %
  2024      735      646         33     95,1 %
```

⛔⛔ **SA RÈGLE PAR DÉFAUT EST JUSTE — MAIS SEULEMENT À PARTIR DE 2018.**
Avant 2017, c'était **l'acquéreur** qui payait presque toujours. Appliquer
« vente → vendeur » à l'historique **inverserait la charge sur environ 3 700
mandats d'avant 2017**. La règle par défaut doit donc dépendre de l'année :

```
mandat de vente >= 2018  -> « vendeur »    par defaut
mandat de vente <= 2016  -> « acquereur »  par defaut
mandat de vente de 2017  -> ⛔ AUCUN DEFAUT : 43,8 / 56,2, on ne devine pas
mandat de recherche      -> « acquereur »  par defaut (sa regle, inchangee)
```

### Ce que le rattrapage couvrirait vraiment

```
24 568 mandats au registre
11 533 recevraient une valeur CONSTATEE par le fichier
   dont 96,8 % existent bien au registre (echantillon declare de 400 numeros,
   13 absents) -> environ 11 160 mandats, soit ~45 % du registre
⛔ 2025 : 789 mandats  et  2026 : 683 mandats  -> ZERO couverture.
   Le fichier s'arrete au numero 17439 ; nos mandats recents sont au-dela.
⚠ Le registre porte ~1,5 ligne par numero de mandat (593 appariements pour
   387 numeros) : il faudra decider QUELLE ligne recoit la charge.
```

⛔ **ET LA CONDITION DU § 3 quater TIENT TOUJOURS** : chaque ligne remplie porte
**sa source** — `fichier_modelo` (constatée), ou `deduite_par_defaut` avec
l'année qui a servi. Une valeur déduite n'est pas une valeur constatée.

✅ **Mesures reproductibles** : `decoder_charge_par_ligne.py`,
`mesurer_cle_mandat.py` et `mandats_charge_retenus.csv` (numéro ; verdict ;
type d'offre ; nombre de lignes). **Rien n'a été écrit : lecture seule.**

---

## § 3 quater. ⭐⭐ LA SOURCE DU RATTRAPAGE N'EST PAS LE CLASSEUR — 02/11, le soir

**Sa question** : *« tu as le fichier des mandats jusqu'au 27 février et même les 90
ajoutés manuellement au début du projet, sur ces tableaux la charge de la commission
doit être visible non ?»* — **il avait raison, et c'est beaucoup mieux que le
classeur.**

```
CE QUE J'AI MESURE, FICHIER PAR FICHIER :

  mandats_extraits.xlsx          export Modelo, 26 404 lignes, jusqu'au 27/02/2026
    ⭐ PORTE LA CHARGE, dans le JSON produit :
         "fees_paid_by_who": 2       le code de qui paie
         "fees": 11000               le montant des honoraires
         "fees_paid_by_buyer": 0     ⚠ un MONTANT, pas un oui/non
       et la mention legale l'ecrit EN CLAIR : « Honoraires a la charge du vendeur »
    repartition des codes : 3 -> 16 780 · 2 -> 9 153 · 1 -> 177 · 0 -> 76

  liste mandat du 02_02_2026 au 28_02_2026.xlsx   80 mandats, meme format
    fees_paid_by_who : 2 -> 68 (85 %) · 1 -> 12

  Ancien registre des mandat.csv  registre legal 2014 -> 19/12/2024, 8 441 lignes
    ⛔ SIX COLONNES SEULEMENT (n°, date, mandants, type, objet, observations)
    -> AUCUNE charge. Rien a en tirer pour ce champ.

  le classeur Sheet                933 lignes portent la charge, 871 mandats
    874 « Vendeur » (93,7 %) · 59 « Acquereur » · chez nous : ZERO
```

### ⛔ CE QUI N'EST PAS TRANCHÉ, ET QUI BLOQUE LE RATTRAPAGE

**Le sens des codes n'est pas établi.** J'ai croisé `fees_paid_by_who` avec la
mention légale : le **code 2** donne « vendeur » 752 fois (acquéreur 1 fois), mais
le **code 3** donne lui aussi « vendeur » 57 fois (acquéreur 2). Les deux codes
pointent au même endroit, donc **le croisement ne tranche pas**.

⚠ **Et ma mesure a une faiblesse que je nomme** : elle lit les chaînes du fichier
**en vrac**, pas un mandat par ligne — une cellule peut porter plusieurs produits,
donc les paires (code, mention) peuvent être mal appariées. Les **comptes de codes**
sont justes ; le **croisement** ne l'est pas.

```
⬜ A FAIRE AVANT TOUT RATTRAPAGE : une passe propre, UN MANDAT PAR LIGNE, qui
   etablit ce que valent 0, 1, 2 et 3, avec un temoin dans les DEUX sens.
   Sans ca, on remplirait 26 000 lignes avec un contresens possible.
⭐ LA PISTE LA PLUS SOLIDE : `fees_paid_by_buyer` est un MONTANT. Un montant > 0
   signifie que l'acquereur paie ; 0 signifie qu'il ne paie pas. C'est un fait
   chiffre, pas un code a interpreter -- a eprouver en priorite.
```

### ✅ SA RÈGLE PAR DÉFAUT, POSÉE LE 02/11

> *« si un doute, un mandat de vente est 90 % du temps chargé vendeur. Et
> l'inverse pour les mandats de recherche. »*

```
MANDAT DE VENTE      -> « vendeur »     par defaut
MANDAT DE RECHERCHE  -> « acquereur »   par defaut (c'est l'acquereur qui mandate)
```

⭐ **Deux mesures indépendantes confirment le 90 %** : le classeur dit **93,7 %**
vendeur (874 / 933), et l'écran de saisie ouvrait déjà sur « Vendeur » dans
**93,6 %** des cas. Trois sources, le même chiffre.

⛔⛔ **MAIS UNE VALEUR DÉDUITE N'EST PAS UNE VALEUR CONSTATÉE** — condition que je
pose, et qu'il faut tenir : **chaque ligne remplie doit porter SA SOURCE**
(`fichier_modelo` / `classeur` / `deduite_par_defaut`). Sans ça, dans six mois
personne ne saura distinguer ce qui est mesuré de ce qui est supposé, et la règle
des 90 % deviendra une vérité qu'elle n'est pas. Voir la leçon
« l'exclusion délibérée doit être déclarée » et « une déduction ne change pas ce
que l'écran affiche ».

⚠ **Reste à identifier** : *« les 90 ajoutés manuellement au début du projet »*. Les
80 mandats de février 2026 (18340 → 18419) et les 16 mandats de recherche PROTEXA
sont les candidats les plus proches, mais **je ne les ai pas formellement
identifiés comme étant ces 90-là**. À confirmer avec lui.

---

## § 3 bis. ✅ LE CORRECTIF DE LA SAISIE EST POSÉ — commit `2a82417`

Sans lui, remplir le passé n'aurait servi à rien : chaque nouvelle transaction
aurait recommencé à vide.

```
LE DEFAUT      le select ouvre sur « Vendeur » (juste dans 93,6 % des cas), et la
               RPC n'etait appelee que si on TOUCHAIT le champ. Personne n'avait
               de raison d'y toucher -> rien n'etait ecrit.
LA PREUVE      8 charges en base : 8 « acquereur », ZERO « vendeur ».
               « Acquereur » est le seul choix qui oblige a toucher le select.
LE CORRECTIF   `if (statusChangeCommissionTouchee || !reprendre)` -- la charge
               s'ecrit TOUJOURS a la creation ; les honoraires restent sous le
               drapeau (une clef vide effacerait une valeur reprise).
CE QUI NE      modification sans drapeau : rien ne part, INCHANGE. La regle de
CHANGE PAS     P5 (22/10) etait juste POUR LA MODIFICATION, elle est gardee.
ETAT           npm run build vert · ⛔ NON POUSSE, NON DEPLOYE, PAS EPROUVE EN REEL
```

---

## § 3 ter. ⬜ LES DEUX SUITES QU'IL A DEMANDÉES — possibles, et le patron existe

### ② La modale offre/compromis doit PRÉ-REMPLIR la charge depuis le registre des mandats

**OUI, c'est possible**, et sa mémoire était juste : la modale lit **déjà** le
registre des mandats (`statusChangeTarget`, un `Dossier` issu de
`app_registre_mandats_current`). Elle en affiche même déjà le numéro de mandat
(App.tsx:22152) et *« Prix du mandat »* comme repère (App.tsx:22207).

⛔ **Mais elle ne peut pas pré-remplir ce que le mandat ne porte pas.** ② attend
donc ③. Les deux ne sont pas deux chantiers : c'est **un seul**, pris par les
deux bouts.

⭐⭐ **Et le patron existe déjà, éprouvé** : `mandat_date_cloture` fait
**exactement ce chemin** depuis le 13/10, et la vue expose
`mandat_date_cloture_app`. On recopie un chemin qui marche.

### ③ Le choix fait à l'édition du mandat pour signature doit être MÉMORISÉ

**OUI, possible**, et c'est le maîllon manquant qu'il décrit. Aujourd'hui la
charge est choisie, imprimée sur le PDF (App.tsx:4803) et **jetée**.

```
LE CHEMIN COMPLET, quatre gestes dans cet ordre :
  a. a la generation du document, ecrire la charge dans app_mandat_champ_app
     (champ = 'charge_commission') -- AUCUNE migration : la table n'a pas de
     contrainte sur le nom du champ
  b. ⛔⛔ AJOUTER LE CHAMP AUX DEUX LISTES BLANCHES, sans quoi il est JETE EN
     SILENCE :  magasin_mandat_app.py:64 (CHAMPS_SUIVIS)
                contrat_autorite.py:92  (CHAMPS_APP_MANDAT)
  c. exposer la colonne dans app_registre_mandats_current, comme
     mandat_date_cloture_app
  d. le front : le type Dossier porte le champ, et la modale pre-remplit
     statusChangeChargeCommission depuis lui -- LE SELECT RESTE MODIFIABLE,
     il l'est deja, et toucher le select leve le drapeau donc la modification
     part normalement
```

⭐ **Le critère du projet justifie déjà ③** : `magasin_mandat_app.py:58` dit
qu'on ne confie à l'app que les champs *« où Hektor n'a rien à dire »*. La date
de clôture a franchi ce critère à 0,4 % ; la charge, Hektor en porte **zéro**.

⚠ **Et un piège de vocabulaire à trancher en écrivant b** : le document de mandat
dit **`mandant`**, la transaction et le classeur disent **`vendeur`**. La
contrainte de la transaction n'accepte que `vendeur` / `acquereur`. Il faut donc
traduire à l'écriture, et ⚠ notre « Mandant » est pollué depuis le 17/07.

⚠ **Et le défaut du document est à corriger au passage** : il écrit
« acquereur » dès qu'il y a des honoraires (App.tsx:4560), ce qui est **faux
9 fois sur 10**.

---

## § 4. ⬜ LES 30 COLONNES QUI RESTENT À TRANCHER

```
LOT 2  LE FINANCIER        P Commission TTC · AF Prix · AA Numero de facture
                           (+ Q, reposee)
LOT 3  LES DATES           S Offre Achat · T Compromis · W Vente Fixee
                           · Y Vente Reglee
LOT 4  DATES ET ETAT       V Vente Prevue · Z Annulee · R Etat Actuel
                           · U Signe + X Signee
LOT 5  LES IDENTITES       AB Acquereur · AD Vendeur · O Notaire · H Agence
LOT 6  LE BIEN             C Mandat · B product_ref · D Nature · AG Ville
                           · AC Adresse Acquereur · AE Adresse Vendeur
LOT 7  NOTES ET TECHNIQUE  F En attente de · G COMMENTAIRES · AH Avis a
                           envoyer · AI Commentaire Avis · AJ Avis envoye
                           · AK Divers · E Lien CRM · A affair_uuid
                           · AL ID Unique
```

---

## § 5. ⛔ DEUX RÉSERVES QUI VALENT POUR TOUTE LA REVUE

### ⛔ L'apparieur ne lit que la plage `A1:AL6000`

Les 38 colonnes vont **exactement de A à AL**. Donc **toute colonne ajoutée à
droite de AL est invisible, en silence**. Réserve écrite le 31/10, jamais
corrigée. ⬜ **Relire jusqu'à `BZ`** — deux caractères à changer, mais un appel
à l'API Google, donc son accord.

### ⚠ Les chiffres d'écart viennent du rapport du 29/10

Le classeur lui-même est mesuré sur le cache du **01/11 18:47** (4 780 lignes,
38 colonnes), sans appel réseau. Les verdicts d'écart, eux, viennent de
`notice/A4_RAPPORT_GEL_TOUS_LES_CHAMPS_2026-10-29.csv`. Le gel a gagné 2 lignes
depuis. ⛔ Le rapport n'a **pas** été relancé : son script écrit par-dessus les
fichiers du 29/10 (noms de sortie en dur) et demande un login Google.
