# AUDIT — GRAVER UN IDENTIFIANT D'AFFAIRE À LA NAISSANCE D'UNE TRANSACTION ?

**09/11/2026.** Deux questions de Frédéric :

> *« Il y a le gel pour le rattrapage : est-ce qu'on pourra en refaire un autre dans
> quelques semaines, regel etc. ? Mais pourquoi pas ajouter un id affaire dès la
> création d'une transaction dans l'app, ou récup du run de nuit de Hektor ? Refais un
> audit approfondi. »*

⛔ **Lecture seule. Rien n'est codé, rien n'est écrit en base.**

⭐ **Le contexte** : il m'avait déjà reproché, le 09/11, de ne pas avoir relu les notes du
projet sur ce sujet — *« c'était pas si simple »*. Il avait raison. Cet audit part donc des
deux notes existantes, `AUDIT_CHAINAGE_ARCHITECTURE_2026-10-28.md` et
`ANALYSE_LIEN_PAR_DOSSIER_OU_PAR_TRANSACTION_2026-10-29.md`, et les **mesure à nouveau**
plutôt que de les répéter.

---

# 1. ✅ LA PREMIÈRE QUESTION : OUI, LE GEL SE REFAIT — **et c'est déjà prouvé**

**On l'a refait aujourd'hui.** Le regel du 09/11 est l'épreuve de la question :

```
le gel du 02/11      12 413 liens . 4 679 lignes du classeur
le regel du 09/11    12 422 liens . 4 688 lignes       -> +9 liens, +9 lignes
    liens PERDUS        0
    liens DIVERGENTS    0        (une ligne deja gelee n'a pas change de cible)
    8 controles independants, tous verts
```

⭐⭐ **Pourquoi il est rejouable sans risque : le regel est un INSERT PUR.** Il n'écrase
jamais un lien existant ; il n'ajoute que les lignes du classeur qui n'en avaient pas. Un
lien gelé est donc définitif par construction, et un regel ne peut que **compléter**.

➡ **Donc oui, autant de fois qu'on veut, et dans quelques semaines aussi.** À chaque fois,
il ramassera les lignes neuves du classeur et celles dont l'appariement a enfin réussi.

## ⚠ MAIS DEUX CHOSES À SAVOIR AVANT LE PROCHAIN

```
① LE REGEL NE REPARE PAS UNE ERREUR. Un lien FAUX reste faux : l'INSERT pur ne le
   touche pas. Corriger un lien demande un geste EXPRES, nommé, ligne par ligne.
② IL FAUT RELANCER LE RAPPORT APRES. Le CSV du rapport porte 4 679 lignes, le gel en
   compte 4 688 : neuf lignes neuves ne sont dans AUCUNE liste d'ecarts. Un patch
   ecrit sur l'ancien CSV les oublierait en silence.
```

## ⭐ ET LE VRAI ENSEIGNEMENT DU REGEL, qui n'était pas la question

**Les écarts sont STABLES à onze jours.** Rien ne s'est rattrapé tout seul entre le 02 et
le 09/11, sauf la charge des honoraires posée le 04/11. ⛔ **Donc attendre ne répare rien :
ce chantier est le seul chemin.**

---

# 2. LA SECONDE QUESTION — **par où une transaction entre-t-elle vraiment ?**

Il propose deux voies : *« dès la création dans l'app »* ou *« récup du run de nuit de
Hektor »*. **Mesuré le 09/11, les deux ne pèsent pas du tout le même poids :**

```
                        offre    compromis   vente     TOTAL
LUE CHEZ HEKTOR         11 067     10 528     9 208    30 803   98,9 %
NEE DANS L APP             148        123        69       340    1,1 %
                                                      -------
                                                        31 143
```

➡ ⛔ **La voie « à la création dans l'app » ne couvre que 1,1 % des transactions.** Seule,
elle ne sert à rien : 99 cas sur 100 continueraient d'être étiquetés autrement.
➡ ⭐ **C'est donc la voie du RUN DE NUIT qui est la vraie porte.** Et comme elle existe
déjà et qu'elle lit tout, la gravure peut s'y greffer sans nouvelle plomberie.

## ⭐ ET LA MOITIÉ DU MÉCANISME EXISTE DÉJÀ — *ne pas la réécrire*

`public.app_chaine_pour(annonce, acquéreur, genre, numéro)` est **déjà appelée quand l'app
crée une transaction** *(patch `1b` du 22/10, patch chaînage offre proposée du 30/10)*. Son
en-tête le dit : *« Celle-ci sert ENTRE DEUX RUNS : quand l'app crée une transaction,
l'écran doit montrer le bon dossier tout de suite. »*

⛔ **Ce qui manque n'est donc pas le CALCUL : c'est la GRAVURE.** Aujourd'hui le résultat
est écrit dans `app_chaine_id`, que le run **recalcule entièrement chaque nuit** *(0,09 s
sur 29 321 lignes)*. Le numéro est un **résultat**, jamais une identité.

⚠ **Et les deux copies de la formule doivent rester d'accord** — c'est écrit dans le patch
du 05/09 : *« Deux copies d'une formule divergent tôt ou tard : toute correction ici doit
être reportée là-bas, et l'inverse. »* Une gravure ne supprime pas cette dette, elle la
déplace.

---

# 3. ⛔ L'OBJECTION DU PROJET, ET POURQUOI SON CHIFFRE NE S'APPLIQUE PAS

`AUDIT_CHAINAGE_ARCHITECTURE_2026-10-28.md` § 5 argumente **contre** une étiquette gravée :

```
une sequence frappee  = un ETAT a conserver
                        -> une erreur passee est GRAVEE, on ne peut plus recalculer
                        -> deux groupes qui se revelent n'en faire qu'un demandent une
                           decision, une table de fusion, un arbitrage
                        -> et la fusion devient IRREVERSIBLE
```

Et elle chiffre le dégât : *« avec une séquence frappée, on aurait eu DEUX dossiers […]
21 710 chaînes au lieu de 12 648, soit 9 000 dossiers coupés en deux. »*

## ⭐⭐⭐ CE CHIFFRE DE 9 000 EST VRAI, MAIS IL NE JUGE PAS SON IDÉE

**Les 9 000 viennent de la V1 du 03/09, qui frappait un numéro SUR LA MAUVAISE RÈGLE** —
`(annonce, acquéreur)`, celle que Frédéric a fait refondre le 04/09 parce que *« l'identité
de l'acheteur CHANGE d'une étape à l'autre »*. **Ce n'est pas la gravure qui a produit les
9 000 coupures : c'est la règle.** Confondre les deux, c'est condamner son idée pour la
faute d'une autre.

➡ **Il fallait donc refaire la mesure avec la RÈGLE ACTUELLE. C'est le cœur de cet audit.**

---

# 4. ⭐⭐⭐ LA MESURE QUI TRANCHE — *la gravure se tromperait 35 fois sur 12 138*

**Le test** : une étiquette gravée à la naissance échoue exactement quand la transaction qui
**porte** le numéro du dossier est arrivée **après** les autres. Au moment où les premières
sont nées, elle n'existait pas — rien n'aurait pu les relier à elle.

```
                                                            chaines   transactions
A. un seul membre -- rien a relier                            1 752       1 752
B. la TETE est arrivee EN PREMIER -- la gravure aurait MARCHE 10 351      29 304
C. la TETE est arrivee APRES -- la gravure aurait COUPE          35          87
                                                             ------
                                                             12 138
```

⭐⭐ **35 dossiers sur 12 138 — 0,29 %, moins de trois pour mille.** Et ce chiffre recoupe
les *« 34 dossiers dont la tête est arrivée après les autres »* mesurés le 28/10 : un de plus
en douze jours.

⭐ **Et ces 35 sont NOMMÉS** — la requête les liste. Un défaut qu'on peut énumérer se répare
une fois ; il n'a pas besoin d'un mécanisme permanent pour l'éviter.

⭐ **L'exemple du projet reste le meilleur** *(dossier 29046, annonce 46434)* : une offre et
un compromis de 2009 remontés le 27/08 avec des numéros de la plage app, puis **la vente de
2009 arrive le 15/09 avec un numéro plus petit** et prend la tête. Avec une gravure, on
aurait eu deux dossiers.

## ⭐ LE DÉBIT, qui dimensionne tout

```
semaines 39 a 45 (2026)   21 . 21 . 26 . 23 . 20 . 21 . 21  transactions nouvelles
                           -> ~21 par semaine, soit TROIS PAR JOUR
    dont nees dans l'app   0 a 6 par semaine
    dossiers touches       presque toujours 1 par transaction (21 -> 21, 20 -> 20)
⚠ la semaine 38 porte 1 632 transactions : c'est un rattrapage historique, pas un rythme.
```

➡ **Trois étiquettes par jour.** La gravure est un geste minuscule, sans enjeu de volume ni
de cadence. Rien à voir avec le mur de Hektor.

---

# 5. ⚖ MA RECOMMANDATION — **graver ET surveiller, pas graver OU déduire**

**L'opposition posée par la note du 28/10 est un faux choix.** On peut avoir les deux, et le
projet utilise déjà ce patron ailleurs.

```
L'ETIQUETTE GRAVEE   posee UNE FOIS a l'entree de la transaction (les deux portes),
                     elle ne bouge PLUS JAMAIS
                     -> on peut lui accrocher ce qu'on veut : le classeur, les
                        8 colonnes de suivi, et la PHASE B
LA DEDUCTION         continue, chaque nuit, EXACTEMENT comme aujourd'hui
                     -> mais elle ne fait plus AUTORITE : elle devient un CONTROLE
                     -> quand elle diverge de l'etiquette, elle le SIGNALE au lieu
                        de l'ecraser en silence
```

⭐⭐⭐ **Et c'est littéralement la doctrine du projet, écrite pour le carnet des affaires :**
*« On ne protège plus la DONNÉE : on protège l'ÉCRITURE, et on la rend visible. »* Le carnet
garde `valeur_hektor_au_moment` et un `etat` *(arrivée / en_attente / conflit)* pour
exactement cette raison. **Une étiquette gravée avec une sentinelle de divergence est le même
mécanisme, appliqué au dossier.**

## CE QUE ÇA RÉPARE, ET QUI EST RÉEL

```
① LES 8 COLONNES DU CLASSEUR ont enfin un point d'accrochage legitime. Aujourd'hui je
   suis oblige de les accrocher a « ID Unique », la cle du CLASSEUR -- ce qui marche
   pour la phase A mais laisse les affaires nees dans l'app sans place.
② LA PHASE B devient possible. La note du 29/10 : apres une fusion, le worker verrait
   UN dossier lie a DEUX lignes du classeur et ne saurait pas laquelle ecrire.
③ LES 595 DOSSIERS FANTOMES deviennent adressables (une offre acceptee toute seule,
   dont 545 sans mouvement depuis plus de 18 mois, la plus ancienne de 2006).
④ ET LA LACUNE DU 28/10 EST COMBLEE AU PASSAGE : « aucun journal ne dit combien de
   dossiers ont change de numero cette nuit ». La sentinelle de divergence EST ce
   journal.
```

## ⛔ CE QUE JE NE RECOMMANDE PAS

```
. NE PAS toucher a la regle de chainage. Elle a ete eprouvee (cinq pistes mesurees,
  quatre ecartees sur des chiffres) et elle n'est pas en cause ici.
. NE PAS supprimer app_chaine_id. Il reste le resultat de la deduction, donc le
  TEMOIN qui permet de juger l'etiquette. Les deux cohabitent.
. NE PAS graver seulement a la creation dans l'app (1,1 %) : ce serait un mecanisme
  a moitie pose, et le projet en a deja paye le prix ailleurs.
. NE PAS LE FAIRE MAINTENANT -- voir le rang ci-dessous.
```

## ⭐ LE RANG, et il est déjà fixé par la note du 29/10

```
1. corriger les 8 liens tres suspects
2. geler sur les TRANSACTIONS                       ✅ FAIT -- 12 422 liens
3. le rapport des ecarts + la mise en conformite     <- LA PHASE A EST FINIE
4. PUIS l'etiquette de dossier, construite A PARTIR des liens deja geles
5. la table complete, et seulement alors la PHASE B
```

⭐ La raison de cet ordre est écrite là-bas, et cet audit ne la change pas : *« les liens de
l'étape 2 DONNENT les groupes à étiqueter, déjà vérifiés par toi. »* **Étiqueter avant le
rattrapage, c'est étiqueter sans les 4 688 groupes que son classeur a déjà validés.**

➡ **Donc : son idée est bonne, elle est mesurée à 0,29 % d'erreur, et sa place est à
l'étape 4.** Rien ne se perd à attendre : la table de suivi s'accroche à « ID Unique » pour
la phase A, et l'étiquette viendra se poser à côté sans rien défaire.

---

# 6. ⚠ CE QUE JE N'AI PAS MESURÉ — *et qui manque à cet audit*

```
. LA FREQUENCE DES FUSIONS. Une seule est documentee (25/10 : 12 160 -> 12 159
  dossiers). Je n'ai pas d'historique des numeros de chaine, donc je ne peux pas
  compter les fusions passees -- c'est exactement la lacune du 28/10, § 6.
  ⛔ Et mes 35 dossiers mesurent les TETES ARRIVEES APRES, qui en sont une bonne
  approximation, PAS la meme chose. Une fusion sans changement de tete ne s'y voit pas.
. LE CHEVAUCHEMENT FUSION x CLASSEUR -- a quelle frequence une fusion toucherait DEUX
  lignes du classeur. La note du 29/10 le reclame AVANT la phase B, pas avant la A.
. SI L'INTERRUPTEUR APP_CHAINAGE_V2 EST ALLUME en production aujourd'hui. Non verifie,
  et je ne le suppose pas.
. CE QUE HEKTOR FERAIT d'une etiquette qui lui serait POUSSEE : il n'a pas le champ.
  L'etiquette resterait donc strictement a nous, comme la table de suivi.
```
