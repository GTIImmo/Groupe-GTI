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
