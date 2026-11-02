# RAPPORT DE SITUATION — LA SYNCHRO APP ⇄ CLASSEUR

**02/11/2026.** Demandé par Frédéric : *« il faut vérifier, nous avons apporté encore
des corrections au registre mandats dans l'app, je pense que le gel a dû bouger si on le
recalcule ; et il faut reprendre les notes, nous avions fait la liste champ par champ
mais pas décidé comment faire en cas de case remplie dans l'app. Reprends en profondeur
et fais-moi un rapport de la situation. »*

**LECTURE SEULE.** Rien n'a été écrit, ni en base, ni dans le classeur, ni chez Hektor.

---

# 0. LES DEUX RÉPONSES, EN HAUT DE PAGE

```
① LE GEL N'A PAS BOUGE. Recalcul complet refait aujourd'hui, apres toutes nos
   corrections : 4 679 lignes CONCORDENT, 0 divergence, 0 perte. Il manque
   seulement 2 lignes NEUVES du classeur a y ajouter.
   -> ta crainte etait fondee en principe, mais le gel a ete concu pour ca.

② TU AS RAISON : LA REGLE DU CONFLIT N'EST PAS DECIDEE, et ce n'est pas un
   detail -- elle porte sur 8 909 cases, soit presque autant que les 10 435
   cases de remplissage qu'on a deja decide de prendre.
   -> la decision manquante est au § 3. Rien n'est code.
```

---

# 1. ① LE GEL N'A PAS BOUGÉ — *et voici la preuve, pas l'opinion*

## Ce que j'ai fait

J'ai **rejoué la cascade entière** (`apparier_classeur.py --reparer tout`, lecture
seule), sur le classeur **lu en direct** et sur notre base **à jour**, puis comparé
**ligne par ligne** au gel de `app_classeur_lien`.

⚠ **J'ai d'abord vérifié que le miroir local était à jour**, sans quoi le recalcul
aurait mesuré l'état d'avant-hier : les 68 offres y sont bien sans date, et les deux
offres de VA30102 sont bien réunies dans la chaîne 10798.

## Le résultat

```
GEL      : 4 679 lignes du classeur
RECALCUL : 4 775 lignes lues, 4 681 rattachees (98 %)

CONCORDE (meme dossier)      4 679
DIVERGE  (autre dossier)         0
PERDU    (gele, plus trouve)     0
GAGNE    (trouve, pas gele)      2
ni l'un ni l'autre              94
```

## ⭐⭐ POURQUOI IL NE POUVAIT PAS BOUGER — *c'est par construction*

`app_classeur_lien` est clé par **`app_affaire_id`**, le numéro de la **transaction**,
pas par `app_chaine_id`, le numéro du **dossier**. Un numéro de transaction ne change
jamais. **Le chaînage peut donc être refait autant de fois qu'on veut : les liens
pointent toujours la même transaction.**

⚠ **Et c'est une leçon déjà payée** : le 29/10 le gel avait d'abord été posé sur
`app_chaine_id`, et Frédéric avait fait corriger. **Sans cette correction, mon
correctif d'aujourd'hui — qui a modifié 68 dates et fusionné 53 chaînes — aurait
cassé le gel.**

## Les deux lignes à ajouter

```
1a474908  -> chaine 30784   « sure »   2 mandat + acquereur   Offre d'achat
cd29653f  -> chaine 30785   « sure »   1 mandat seul          Offre d'achat
```

Ce sont deux **lignes neuves** du classeur (il est passé de 4 773 à 4 775 lignes), pas
des correspondances retrouvées. Les deux sont « sûres ».

## ⚠ Et deux contrôles de cohérence que j'ai posés, tous les deux verts

```
TELESCOPAGE   un dossier portant DEUX lignes du classeur      0   (4 679 dossiers)
ECLATEMENT    une ligne du classeur sur DEUX dossiers         0   (4 679 lignes)
```

La correspondance est donc **bijective** : une ligne du classeur ↔ un dossier. C'est
ce que le regel du 31/10 avait rétabli, et mes changements d'aujourd'hui ne l'ont pas
abîmé.

---

# 2. ⚠ CE QUE LE RECALCUL A TROUVÉ EN PASSANT — *trois choses, aucune grave*

## a) 4 lignes du classeur portent PLUSIEURS offres

```
45225170   3 liens « offre »  -> 30712, 30767, 1001361
045ecde7   2 liens « offre »  -> 28558, 28559
KT0601S6   2 liens « offre »  -> 24290, 24291
f1aedc01   2 liens « offre »  -> 28966, 28967
```

Les quatre restent dans **un seul dossier** (sinon le contrôle d'éclatement l'aurait
vu). Ce n'est donc pas un télescopage, mais une **imprécision** : on ne sait pas
*laquelle* des offres la ligne désigne.

⭐ **Le cas 45225170 mérite un œil** : le lien `1001361` est un numéro **au-dessus de
1 000 000**, donc une affaire **née dans notre app**. Une même ligne du classeur est
donc liée à deux offres de Hektor **et** à une offre de chez nous — il y a sans doute
un doublon là-dessous.

## b) Les 94 lignes non rattachées ne sont PAS 94 trous béants

```
Annulee                63
Vente reglee           29
Vente fixee             1    <- VIVANTE
Compromis en attente    1    <- VIVANTE
```

⭐ **2 seulement sont vivantes.** Les 92 autres sont des affaires closes. L'enjeu est
donc très faible — mais ⚠ **il faut quand même la sentinelle** : ces lignes ne
recevront jamais rien du worker et personne ne le remarquera.

## c) Le gel est quasi complet à l'intérieur des dossiers liés

```
transactions presentes dans les dossiers deja lies   12 423
dont deja liees au classeur                          12 413
NON liees                                                10   (5 offres, 2 compromis, 3 ventes)
```

Les **78 liens manquants** repérés le 30/10 sont donc tombés à **10**. Le regel du
31/10 a fait son travail.

---

# 3. ⭐⭐⭐ ② LA QUESTION QUE TU POSES : « CASE REMPLIE DANS L'APP »

## Ce qui était décidé le 29/10, et ce qui ne l'était pas

La liste champ par champ (`A5_CHAMP_PAR_CHAMP_EST_CE_POSSIBLE_2026-10-29.md`) répond
toujours à la **même** question : *« que fait-on des cases VIDES chez nous ? »* —
« on pose les 480 vides », « les 33 vides seulement », « les 44 vides + les 13 en
cours ». **Elle ne dit nulle part ce qu'on fait quand notre case est déjà remplie et
que le classeur dit autre chose.** La seule phrase qui en approche est *« les conflits
se listent, ils ne se corrigent pas »* — ce n'est pas une règle d'écriture, c'est un
report.

## ⛔ ET LE TROU PÈSE PLUS LOURD QUE CE QUI EST DÉCIDÉ

Les 21 champs sur les 4 680 lignes rattachées font **98 280 cases**. Leur partage :

```
identiques des deux cotes          49 182   50,0 %   rien a faire
REMPLIES DES DEUX, DIFFERENTES      8 909    9,1 %   <-- NON TRANCHE
le classeur sait, nous PAS         10 435   10,6 %   deja decide : on prend
nous savons, le classeur PAS        9 077    9,2 %   phase B
vides des deux cotes               16 912   17,2 %   rien a faire
hors perimetre                      3 765    3,8 %
```

**8 909 cases contre 10 435.** La question non tranchée pèse presque autant que tout
ce qu'on a décidé de faire.

## 📋 LA DOCTRINE QUE JE PROPOSE — *quatre cas, une seule question par champ*

> **La seule question à poser, champ par champ, est : QUI FAIT FOI ?**
> Tout le reste en découle mécaniquement.

```
CAS 1  vide chez nous · rempli au classeur
       -> ON PREND.  Deja decide le 29/10. Aucun risque : on ne perd rien.

CAS 2  rempli chez nous · vide au classeur
       -> ON POUSSE, si nous faisons foi. C'est la phase B.

CAS 3  rempli des deux cotes · IDENTIQUE
       -> RIEN. Et le worker ne doit meme pas ecrire (il n'ecrit que ce qui change).

CAS 4  rempli des deux cotes · DIFFERENT        <-- LA DECISION QUI MANQUE
       -> trois reponses possibles, et c'est le PROPRIETAIRE du champ qui tranche :
          (a) NOUS faisons foi      -> on ECRASE la case du classeur
          (b) LE CLASSEUR fait foi  -> on PREND sa valeur chez nous
          (c) PERSONNE ne fait foi  -> ON NE TOUCHE A RIEN, et l'ecart s'AFFICHE
                                       pour arbitrage humain
```

⛔⛔ **LA RÈGLE DE SÛRETÉ, et je la propose comme non négociable : un écart ne se
résout JAMAIS tout seul.** Le cas (c) doit être le **défaut** de tout champ dont la
propriété n'a pas été déclarée explicitement. Sans ce défaut, un champ oublié se fait
écraser en silence — et c'est exactement le risque prouvé sur **Négociateur 2** (nous
en avons 209, le classeur 685 : le mettre en liste blanche l'**effacerait**).

## ⭐ CE QUE ÇA DONNE CHAMP PAR CHAMP — *ma recommandation, à valider par toi*

**(b) LE CLASSEUR FAIT FOI** — il est seule source, nous n'avons rien à opposer :

```
Negociateur 2 et 3    374 + 9 ecarts    il en sait 685, nous 209
Charge Commission       0 ecart          notre champ est VIDE partout
Vente Reglee            0 ecart          nous n'avons AUCUN champ
Numero de facture       0 ecart          nous n'avons AUCUN champ
```

**(a) NOUS FAISONS FOI** — la donnée vient de Hektor, relue chaque nuit, le classeur
est saisi à la main :

```
Ville       1 644 ecarts
Nature      1 653 ecarts
Etat Actuel   160 ecarts     ⚠ c'est un ETAT CALCULE, pas une donnee a corriger
Mandat        134 ecarts     ⛔ SAUF mandat de recherche : la 2e famille est legitime
```

**(c) PERSONNE — on liste, on n'ecrit pas** — parce que la cause de l'écart n'est pas
connue, ou parce que les deux valeurs sont également défendables :

```
Vente Prevue   1 767 ecarts   56 % des comparables : une date qui bouge par nature
Notaire        1 373 ecarts   ⛔ ce ne sont PAS des ecarts : nous portons DEUX
                              notaires (acquereur + vendeur), le classeur un seul
Agence           498 ecarts   ⚠ CAUSE NON MESUREE -- a comprendre avant de choisir
Negociateur 1    432 ecarts   demande la table d'ALIAS avant toute decision
Offre Achat      210 ecarts   la date la moins fiable des trois
Acquereur 120 · Vendeur 68 · Commission TTC 85 · Vente Fixee 61 · Compromis 44
product_ref 69
```

**LE CAS À PART : LE PRIX — propriété PARTAGÉE PAR ANNÉE**

```
208 ecarts.  NOUS a partir de 2025 · LE CLASSEUR avant.
⭐ C'est le SEUL champ dans ce cas, et il demande une regle DATEE dans le worker.
```

## 📋 CE QUE ÇA CHANGE POUR LA TABLE DE PROPRIÉTÉ

Elle a donc besoin de **quatre** colonnes, pas deux — c'est la conclusion pratique de
ce rapport :

```
champ            le nom de la case du classeur
qui_fait_foi     'nous' | 'classeur' | 'personne'      (defaut : 'personne')
depuis_quand     une date, pour le seul cas du PRIX     (NULL ailleurs)
sur_conflit      'ecraser' | 'prendre' | 'lister'       (defaut : 'lister')
```

⭐ Et elle rend la décision **réversible et sans déploiement** : changer l'avis sur un
champ = changer une ligne.

---

# 4. ⬜ CE QUI RESTE À DÉCIDER PAR FRÉDÉRIC

```
1  LA DOCTRINE DES 4 CAS du § 3 -- est-ce la bonne forme ?
   Et en particulier : le defaut 'lister' pour tout champ non declare.
2  LA REPARTITION champ par champ que je propose au § 3 -- 4 champs au
   classeur, 4 a nous, 13 en liste, 1 partage par annee (le prix).
3  LES 2 LIGNES NEUVES du classeur : on ajoute leurs liens au gel ? (sans risque)
4  LES 4 LIGNES A PLUSIEURS OFFRES, dont 45225170 avec une affaire NEE CHEZ NOUS
   -- probable doublon, a regarder.
5  LES 2 LIGNES VIVANTES non rattachees (sur 94) -- a rattacher a la main ?
6  LA SENTINELLE sur les lignes non rattachees -- a poser (elle ne depend de rien).
7  L'AGENCE : 498 ecarts dont la CAUSE N'EST PAS MESUREE. A comprendre avant
   de la classer.
```

⛔ **ET LE VERROU QUI N'A PAS BOUGÉ DEPUIS LE 22/10 : LIRE LES APPS SCRIPT DU
CLASSEUR.** Sheet1 nourrit **la paie**, et rien ne dit aujourd'hui ce qu'un script
déclenche quand une case change. **Tant que ce n'est pas lu, la phase B ne démarre
pas** — quelle que soit la qualité de la table de propriété.
