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
TRANCHEES         38 colonnes   ⭐ LA REVUE EST COMPLETE -- 09/11/2026
RESTE A VOIR       0 colonne
                 -------------
                  38 colonnes
```

⭐ **Les 38 choix vivent à DEUX endroits, et ils doivent dire la même chose :**
ce fichier *(§ 4, un par un, avec la mesure qui a justifié le choix)* et la page
de travail où **Frédéric les a notés lui-même**, colonne par colonne
*(`https://claude.ai/artifact/JFtYqskwiwgWANvgT8nk4S`, collection `choix` — elle
porte aussi ses mots et la date de chaque décision)*.

**Les quatre choix possibles, dans ses mots du 09/11** — *« on fait rien · on
récupère tout · on récupère que les vides · on compare juste »* :

```
TOUT            16 colonnes   le classeur ECRASE, ou remplit un champ NEUF
LES VIDES        7 colonnes   on ne remplit que NOS TROUS, on ne corrige rien
COMPARER JUSTE   1 colonne    on mesure et on affiche, on n'ecrit pas
RIEN            14 colonnes   on n'y touche pas
```

⚠⚠ **Ce que « les vides » ne fait pas, et il l'a dit le 09/11** : *« car
actuellement si mon apps a des erreurs on ne corrige rien »*. Sur les
7 colonnes en « les vides », **une valeur fausse chez nous reste fausse**. Le
choix a été fait colonne par colonne **après avoir mesuré que les écarts ne sont
pas des erreurs du classeur** — voir chaque ligne du § 4.

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

## § 3 octies. ⛔⛔ LA CHARGE NE SE DÉDUIT PAS DES HONORAIRES VENDEUR / ACQUÉREUR

**02/11, le soir.** Frédéric : *« le registre des transactions n'a pas la colonne
charge mais on la déduit, il y a une colonne honoraires vendeur et honoraires
acquéreur, donc pas la peine d'ajouter une colonne non ? »*

**Son vocabulaire est juste. Sa déduction, non.** Et la colonne existe déjà.

### Ce qui est exact

```
app_affaire_ledger PORTE DEJA :
   honoraires_entree / honoraires_entree_app   = « Honoraires vendeur (agence) »
   honoraires_sortie / honoraires_sortie_app   = « Honoraires acquereur »
   charge_commission_app                        <- LA COLONNE EXISTE DEJA
App.tsx:30778 « Honoraires acquereur »   <- honoraires_sortie_app / honoraires_sortie
App.tsx:30780 « Honoraires vendeur (agence) » <- honoraires_entree_app
App.tsx:19306 honoraires_sortie_app <- statusChangeBuyerFees  (buyer = acquereur)
```

`charge_commission_app` est **remplie 8 fois sur 31 124** : c'est une saisie
humaine, pas une déduction.

### ⛔ POURQUOI LA DÉDUCTION NE PEUT PAS MARCHER — DEUX MESURES

**1. Par dénombrement, et c'est imparable.**

```
app_affaire_ledger, 31 124 lignes :
   honoraires_entree  (vendeur)   renseigne 19 860
   honoraires_sortie  (acquereur) renseigne     79        <- SOIXANTE-DIX-NEUF
   les deux ensemble                              3
   aucun des deux                            11 188

   par nature :      lignes   entree   sortie
      offre          11 206        0       33
      compromis      10 642   10 605       26
      vente           9 276    9 255       20
```

Or **Hektor dit « acquéreur » pour 3 258 annonces**. Si la colonne portait
l'information, il y manquerait **plus de 3 000 valeurs**. Elle ne peut donc pas
la porter, quel que soit le raisonnement qu'on lui applique.

**2. Par croisement avec la vérité connue — et le résultat est l'inverse.**

Échantillon de 150 annonces « acquéreur » et 150 « vendeur » (dit par Hektor),
croisé avec leurs compromis et ventes :

```
charge ACQUEREUR (dit par Hektor)  :  13 affaires
   « honoraires vendeur » rempli   :  12   (92 %)   <- REMPLI QUAND MEME
   « honoraires acquereur » rempli :   1   ( 8 %)

charge VENDEUR (dit par Hektor)    : 112 affaires
   « honoraires vendeur » rempli   : 112  (100 %)
   « honoraires acquereur » rempli :   0
```

⭐⭐ **`honoraires_entree` est rempli dans 92 % des cas où c'est l'ACQUÉREUR qui
paie.** La colonne ne dit pas **qui** paie : elle dit **combien** l'agence prend.
Déduire « honoraires vendeur rempli → charge vendeur » donnerait donc le
**contraire de la vérité** sur 12 cas sur 13.

⚠ **Réserve, nommée** : les 150 annonces « acquéreur » n'ont donné que **13
affaires** compromis/vente — l'échantillon du **sens** est petit. Le **dénombrement**
(mesure 1), lui, porte sur la table entière et ne dépend d'aucun échantillon.

C'est [[absence-d-un-champ-n-est-pas-un-filtre]] : un champ vide ne veut pas dire
« l'autre paie », il veut dire « on n'a pas saisi ».

### ✅ CONCLUSION, ET CE QU'IL FAUT FAIRE À LA PLACE

```
⛔ NE PAS deduire la charge des deux colonnes de montants.
✅ NE PAS ajouter de colonne au registre des TRANSACTIONS : charge_commission_app
   y est deja (et le § 3 ter l'alimente par la saisie, palier 2).
✅ AJOUTER AU REGISTRE DES MANDATS une colonne qui porte LA VALEUR DE HEKTOR,
   distincte de la saisie humaine :
     mandat_charge_honoraires_app     saisie humaine (existe, vide)   <- le carnet
     mandat_charge_honoraires_hektor  valeur lue dans honoraires_json <- la vitrine
   La precedence a l'ecran : la saisie d'abord, Hektor en repli.
⛔ ET D'ABORD trancher la reserve 2 du § 3 septies : QUELLE ANNONCE FAIT FOI pour
   un mandat. Sans ca, on ecrirait la charge d'une annonce voisine.
```

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

## § 4. ✅ LES DÉCISIONS DES LOTS 2 À 7 — *prises les 09/11, lot par lot*

> ⛔ **Le LOT 1** *(I J K L M N, et Q)* **reste aux § 2 et § 3** : il porte la paie,
> il a sa propre démonstration, et il a été tranché le 02/11. **Ne pas le recopier
> ici.**

### LOT 2 — LE FINANCIER

```
P   Commission TTC      LES VIDES   386 de nos cases sont vides
AF  Prix                COMPARER    3 688 lignes hors perimetre, 1 020 portent
                                    un DEPARTEMENT au lieu d'un prix
AA  Numero de facture    TOUT       aucun champ chez nous -> CHAMP NEUF
Q   Charge commission    TOUT       deja EXECUTE le 04/11 (voir § 3)
```

⭐ **P — la cause des 83 conflits est mesurée le 09/11, et ce ne sont pas des
erreurs** : **44 d'entre eux sont un facteur 2**, le rapport **0,500** revenant
sans cesse *(9 500 / 19 000 · 2 750 / 5 500 · 5 000 / 10 000 · 4 250 / 8 500)*.
Le classeur note **une part**, nous portons **le total**. Plus 2 cas HT contre
TTC. ⬜ **Réserve** : ce que le classeur appelle « commission » sur ces 44 lignes
n'est pas identifié *(la part d'un négociateur ? celle de GTI dans un partage ?)*
— ça ne gêne pas « les vides », qui ne touche aucun conflit.

⚠ **AF** — la question *« le classeur avant 2025, nous après ? »* reste ouverte,
mais « comparer juste » n'écrit rien, donc elle n'est pas bloquante.

### LOT 3 — LES DATES

```
S   Offre Achat         LES VIDES   178 de nos cases sont vides
T   Compromis           LES VIDES   115 vides . 3 246 dates CONCORDENT
W   Vente Fixee         LES VIDES    39 vides . 2 868 dates CONCORDENT
Y   Vente Reglee         TOUT       ce n'est PAS notre date d'acte (+3 j de
                                    mediane) -> CHAMP NEUF
```

⭐⭐ **La réserve du 29/10 est FERMÉE le 09/11 : un écart de date n'est pas une
erreur.** Les écarts ont été croisés avec l'état de l'affaire, comme la réserve
le demandait. Sur l'offre d'achat, **265 des 413 écarts sont à moins de sept
jours** — signature contre réception, ou un week-end qui décale. Les vrais
écarts sont **30 cas à plus d'un mois, tous sur des affaires annulées** : la date
du classeur y est celle d'un essai abandonné que nous n'avons pas gardé. Le
compromis et la vente fixée sont encore plus propres *(86 et 80 écarts)*.

⬜ **Réserve ouverte, et elle doit tomber avant le patch** : mon décompte large
compte **413 écarts** sur l'offre d'achat là où `rapport_gel_tous_les_champs.py`
en annonce **211**. Le rapport applique donc une tolérance que je n'ai pas
retrouvée dans son code. **Les deux chiffres ne se recoupent pas ; je ne les
crois ni l'un ni l'autre tant que l'écart n'est pas expliqué.**

### LOT 4 — LES DATES ET L'ÉTAT

```
V   Vente Prevue         TOUT       le plus gros conflit des 38 (1 768), et il
                                    est NORMAL : une date previsionnelle bouge
Z   Annulee              TOUT       896 dates, 100 % lisibles -> CHAMP NEUF
R   Etat Actuel          RIEN       c'est un etat CALCULE, pas une saisie
U   Signe                RIEN       TRUE / FALSE . jamais mesuree
X   Signee               RIEN       TRUE / FALSE . jamais mesuree
```

⭐ **Z — la mesure du 09/11 a changé la décision.** Elle était notée « les
vides », et **ce choix était inexécutable** : nous n'avons **aucune** date
d'annulation, seulement un état *(`cancelled` / `refused`)* sur 2 504 affaires,
qui dit **que** l'affaire est tombée, jamais **quand**. Sa décision du 09/11 :
*« Annulée tout avec un nouveau champ »*. Les 896 dates entrent alors **sans un
seul conflit possible, par construction**.

⚠ **U et X n'ont jamais été mesurées, et c'est écrit dans la page de travail.**
Elles sont à « rien », donc l'absence de mesure ne bloque rien.

### LOT 5 — LES IDENTITÉS

```
AB  Acquereur           LES VIDES    28 vides . sauter les 462 lignes douteuses
AD  Vendeur             LES VIDES   375 vides . la MEME liste de 462
O   Notaire              RIEN       nous portons DEUX notaires, lui UN SEUL
H   Agence               RIEN       le classeur dit QUI A VENDU, nous OU LE
                                    BIEN EST PARQUE aujourd'hui
```

⭐ **AB / AD — le chiffre de 2 209 était trompeur, corrigé le 09/11 : ce sont
462 lignes à sauter, pas 2 209.** Les 2 209 sont des **transactions** au chaînage
douteux ; seules **462 lignes du classeur** les touchent *(441 ventes réglées,
20 annulées)*, contre **4 226 sur un chaînage sain**.

⭐⭐ **H — la cause des 498 conflits est établie le 09/11, en trois passes, avec
son témoin inverse.** (1) La part de conflits **tombe avec l'année** : 28 % en
2018, 15 % en 2021, 3 % en 2023, **zéro sur 455 affaires en 2026**. (2) **287 des
498** portent **Firminy** de notre côté, alors que Firminy ne pèse que 13,6 % du
registre — quatre fois trop. (3) **75,6 %** de ces lignes portent un négociateur
**ancien**, contre **30,7 %** sur les lignes qui concordent. **Le mécanisme** : le
négociateur part, le bien perd son agence, Hektor le rattache au siège. ⭐ **Son
hypothèse du 09/11 était juste**, et c'est elle qui a fermé la réserve du 29/10.

⬜ **À part, non décidé** : créer **AUREC** *(Aurec-sur-Loire, 54 affaires
2018-2024)* et **CHATEL** *(26 affaires 2018-2021, commune inconnue)* en statut
`'fermee'` dans `app_registre_agence`. Ça ne répare **aucun** conflit : ça garde
la trace de deux agences de l'histoire du groupe. ⚠ **Le registre des agences est
le chantier de l'autre session** *(posé le 05/11)* — la prévenir avant d'y
toucher.

⭐ **O — la question « dans lequel des deux notaires ? », ouverte depuis le 29/10,
est FERMÉE le 09/11 par sa décision** : *« le notaire on ne récupère rien »*.
Remplir nos 483 vides demanderait de deviner dans lequel des deux écrire.

### LOT 6 — LE BIEN

```
C   Mandat              LES VIDES    33 vides ⛔ MAIS IL MANQUE LA COLONNE
B   product_ref          RIEN       remplie a 14 %, et la meme reference
                                    designe parfois 4 affaires (Netty)
D   Nature               RIEN       1 623 des 1 650 ecarts = le classeur dit
                                    « Autre » et nous SAVONS. Reste 27 vrais
AG  Ville                RIEN       « St Etienne 42100 21 bd. Pasteur » contre
                                    « Saint-Etienne » : pas des erreurs
AC  Adresse Acquereur    RIEN       1,3 % des lignes
AE  Adresse Vendeur      RIEN       799 cases, jamais mesurees
```

⛔⛔ **C est la seule décision des lots 2 à 7 qui soit BLOQUÉE par un préalable
technique.** `numero_mandat` est de **CLASSE C** *(à Hektor, relu chaque nuit)* :
**une écriture y est effacée au run suivant**. Il faut d'abord **une colonne « à
nous »**, sur le modèle des `_app` — c'est le préalable n° 3 du § 6 de `A5`,
écrit le 29/10 et **toujours pas fait**.

### LOT 7 — LES NOTES ET LA TECHNIQUE

```
F   En attente de        TOUT       en BLOC, sans interpreter -> CHAMP NEUF
G   COMMENTAIRES         TOUT       en BLOC, sans interpreter -> CHAMP NEUF
AH  Avis a envoyer       TOUT       120 valeurs distinctes -> CHAMP NEUF
AI  Commentaire Avis     TOUT       392 cases -> CHAMP NEUF
AJ  Avis envoye          TOUT       des PRENOMS dedans -> CHAMP NEUF
AK  Divers               RIEN       0,3 % des lignes
E   Lien CRM             RIEN       cinq logiciels successifs, quatre morts
A   affair_uuid          RIEN       vide sur TOUTES les lignes
AL  ID Unique            RIEN       ⛔ LA CLE DU PONT -- NE JAMAIS Y TOUCHER
```

⭐ **F — « V » veut dire Vendu**, et c'est mesuré : 1 537 lignes sur 1 537 sont
« Vente réglée ». Rond vert → réglée 96 %, rond rouge → annulée 99 %. Les motifs
pointent une annulation à 100 % *(rétractation 129, prêt refusé 107)*.
**G** est la seule trace du **pourquoi** : sur les dossiers en cours, **rempli à
100 %, jusqu'à 1 450 caractères**. ⛔ **Les deux se reprennent en BLOC, sans
interpréter** — c'est sa consigne, et elle évite d'inventer une sémantique.

⭐ **Les trois colonnes d'Avis, mesurées le 09/11 — aucune n'est une case à
cocher.** **AH** : 120 valeurs distinctes *(1 830 « oui », 243 « non », ~180 qui
précisent **à qui**)*. **AJ** : « ok » 1 699, « X » 218, et **des prénoms**
*(Marion 190, Nico 59, Claire 24)* plus des motifs *(« négo parti », « pas de
mail »)*. **AI** : 392 cases, « ok » 195, « 1 » 115, le reste libre.
⚠ **AH et AJ se contredisent sur 229 lignes** — à reprendre tels quels, sans
arbitrer.

---

## § 4 bis. ⛔⛔ CE QUI BLOQUE ENCORE L'EXÉCUTION — **neuf champs**

**Les 38 décisions sont prises, mais neuf d'entre elles ne sont pas exécutables
aujourd'hui, faute de case où écrire.**

```
HUIT colonnes mises a TOUT n'ont AUCUN champ en face chez nous :
    Y  Vente Reglee        AA N° de facture     F  En attente de
    G  COMMENTAIRES        AH Avis a envoyer    AI Commentaire Avis
    AJ Avis envoye         Z  Annulee
UNE colonne mise aux VIDES ecrit dans un champ de CLASSE C :
    C  Mandat  ->  il faut `numero_mandat_app`, sinon la NUIT L'EFFACE
```

⛔ **C'est une écriture en base de production ET une décision de périmètre :
neuf champs ne se créent pas sans son accord.** Tant qu'ils n'existent pas,
**P1.4 ne peut couvrir que les 7 autres colonnes** *(P S T W AB AD, et AF en
simple comparaison)*.

---

## § 5. ⛔ LES RÉSERVES QUI VALENT POUR TOUTE LA REVUE

### ⛔ L'apparieur ne lit que la plage `A1:AL6000` — **toujours vraie**

Les 38 colonnes vont **exactement de A à AL**. Donc **toute colonne ajoutée à
droite de AL est invisible, en silence**. Réserve écrite le 31/10, jamais
corrigée. ⬜ **Relire jusqu'à `BZ`** — deux caractères à changer, mais un appel
à l'API Google, donc son accord.

⚠⚠ **Et le 09/11 elle a gagné une seconde moitié : la limite de LIGNES mordra
avant celle des colonnes.** Le classeur portait **4 783 lignes le 09/11** contre
un plafond de **6 000** — il reste **~1 200 lignes de marge**. Le jour où elle
sera franchie, **les lignes du bas disparaîtront sans un mot**, exactement comme
les colonnes à droite de AL. **À corriger dans le même geste.**

### ✅ Les chiffres d'écart venaient du rapport du 29/10 — **LEVÉE le 09/11**

La réserve disait deux choses : les verdicts dataient du 29/10, et le script
écrivait par-dessus ses propres sorties *(noms en dur)*. **Les deux sont
corrigés** : `phase2/checks/rapport_gel_tous_les_champs.py` **date désormais ses
sorties du jour** *(`A4_RAPPORT_GEL_TOUS_LES_CHAMPS_<jour>.csv`)*, et **le
rapport a été relancé** sur les données du 09/11.

⭐⭐ **La relance est elle-même une mesure, et sa réponse compte : les écarts sont
STABLES à onze jours d'intervalle.** Le classeur est passé de 4 780 à **4 783
lignes**, le gel de 12 413 à **12 422 liens**, les non reliées de 94 à **104** —
mais **aucun écart n'a été rattrapé en onze jours**, sauf la charge des
honoraires posée le 04/11. ⛔ **Donc rien ne se répare tout seul : ce chantier
est le seul chemin.**

### ⭐⭐ L'AUDIT DES 21 COLONNES DU RAPPORT — *09/11, et il fallait le faire*

**Sa question du 09/11 était plus large que la charge** : *si le rapport se
trompe de case sur une colonne, il peut se tromper sur dix.* **Les 21 colonnes
ont donc été auditées une par une**, en lisant le code *(l. 519-700)* puis en
mesurant, pour chacune, **la part de nos cases vides là où le classeur est
rempli** — la signature exacte de la faute de la charge.

```
LE VERDICT : UNE SEULE FAUTE SUR 21.

Charge Commission   100,0 % de nos cases vides sur 933 comparables   ⛔ FAUTIVE
Acquereur             0,6 %       Agence         0,8 %      Nature     0,8 %
Mandat                0,7 %       product_ref    1,6 %      Ville      1,4 %
Vente Fixee           1,3 %       Vente Prevue   1,7 %      Compromis  3,3 %
Offre Achat           4,8 %       Negociateur 1  4,9 %      Vendeur    8,0 %
Commission TTC        8,1 %       Negociateur 2 13,5 %      Notaire   19,2 %
Negociateur 3        23,1 %       Prix           0,0 %      Etat       0,0 %
Vente Reglee        100,0 %  et  N° de facture  100,0 %  -> VOULU et DECLARE
```

⭐ **Et les taux de vides SONT exactement les trous à combler du § 4** : offre
d'achat 178, compromis 113, vente fixée 39, notaire 483, vendeur 375. Les deux
mesures, faites séparément, **tombent sur les mêmes nombres** — c'est le témoin
croisé de l'audit.

⛔ **MA PROPRE FAUTE, pendant cet audit, et elle vaut une leçon** : mon premier
critère comptait nos vides sur **toutes** les lignes, et déclarait
« Négociateur 2 » **suspecte à 87,5 %**. Faux : le rapport force notre case à
vide dès que la case du classeur est vide *(le `continue` de la l. 636)*, et
cette colonne n'est remplie que 675 fois. Le vrai taux est **13,5 %**.
➡ **Un dénominateur faux fabrique une alerte fausse** — et une alerte fausse
coûte autant qu'un défaut manqué.

### ⬜ LES RÉSERVES OUVERTES, au 09/11 au soir

```
1. ⛔ LE RAPPORT LIT LA MAUVAISE CASE SUR LA CHARGE -- SEULE FAUTE CONFIRMEE.
   Il annonce « 933 charges a prendre » alors que le registre des mandats en
   porte 23 474 : il mesure `charge_commission_app` du LEDGER (7 lignes) au
   lieu de `mandat_charge_honoraires_app` du REGISTRE.
   ⭐ Sans consequence sur le rattrapage : Q est TRANCHEE et DEJA EXECUTEE le
   04/11. Mais le rapport MENT a l'ecran, et on s'y fie pour les listes.
   ➡ UNE LIGNE A CHANGER : la case lue, l. 557.
2. ✅ LEVEE -- 211 CONTRE 413 ECARTS : la tolerance est DANS LE CODE, l. 578,
   `abs((dc - dn).days) <= 3`. Le rapport declare IDENTIQUE tout ecart de date
   de TROIS JOURS OU MOINS. Mon decompte large comptait tout ecart non nul :
   413 - 211 = 202 ecarts absorbes par cette tolerance, ce qui recoupe mes
   « 265 a moins de sept jours ». ⭐ LES DEUX MESURES SE RECOUPENT, et la
   tolerance de 3 jours est JUSTE au vu du LOT 3 (signature contre reception).
3. ⚠ NEUVE -- LE CSV DU RAPPORT EST D'AVANT LE REGEL. Il porte 4 679 lignes,
   le gel en compte 4 688 depuis le regel du 09/11 : NEUF LIGNES MANQUENT.
   ➡ RELANCER LE RAPPORT APRES LE REGEL, sinon le patch oubliera ces 9 lignes.
4. ⚠ LES LIGNES NON RELIEES N'ONT PAS DE SENTINELLE, et leur nombre MONTE :
   94 le 02/11, 101 le 05/11, 104 le 09/11. Personne n'est averti. Trois sont
   deja auditees (18491 = mandat de recherche, normal ; 130d81ac = mandat 18728
   et annonce 62503 existants mais AUCUNE transaction ; c6233284 = mandat 18967
   absent alors que l'offre 30801 existe, 485 000 EUR du 06/11).
```

⭐ **Un chiffre que l'audit a donné en passant, et qui sert à la PHASE B** : sur
l'offre d'achat, **926 lignes ont une date chez nous et rien au classeur**
*(compromis 777, vente fixée 763)*. C'est le **cas 2** des quatre cas — ce que
l'app aura à écrire **dans** le classeur quand elle en deviendra le rédacteur.
