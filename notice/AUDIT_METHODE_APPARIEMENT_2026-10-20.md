# AUDIT DE LA MÉTHODE D'APPARIEMENT — classeur ⇄ registre

**20/10/2026, après la remise en ordre du chaînage. LECTURE SEULE.**

Demandé par Frédéric : *« refais un audit approfondi pour réfléchir à la meilleure règle
de correspondance et méthode, ensuite propose-moi. »*

> ⚠ **Cet audit ne mesure pas les écarts.** Il mesure **le pouvoir de chaque signal** :
> lequel désigne une seule affaire, lequel se trompe, lequel se tait.

---

## 0. LE VERDICT

**Ma cascade actuelle est mal construite, et la mesure le prouve :**

```
elle note le NOM 3 points (le maximum)  ->  il ne decide que  23 cas sur 782
elle note le PRIX 2 points              ->  il ne decide que   5 cas
elle ne se sert de l'ETAT qu'en dernier ->  il decide         108 cas
elle ignore les DATES comme CRITERE     ->  elles decident    640 cas
elle n'a AUCUN etage « quel BIEN ? »    ->  737 lignes (15 %) en souffrent
elle ne reserve jamais une chaine prise ->  43 lignes se telescopent
```

**Une cascade par PRÉCISION, avec exclusivité, apparie 782 des 790 lignes
ambiguës — 98 %.**

---

## 1. LE PROBLÈME A DEUX ÉTAGES, ET JE N'EN TRAITAIS QU'UN

Une ligne du classeur doit trouver **une affaire**. Mais une affaire, c'est
**un bien, puis une séquence dans ce bien**. Ma cascade mélangeait les deux.

### Étage 1 — quel BIEN ?

```
3 840 (80 %)  le mandat designe UN seul bien      OK
  644 (13 %)  il en designe DEUX                  <- le mandat est RECYCLE
   93 ( 1 %)  il en designe TROIS
  183 ( 3 %)  aucune affaire ne porte ce mandat
    6         pas de numero lisible
```

➡ **737 lignes (15 %) ne savent pas de quel bien elles parlent.** Je n'avais
jamais mesuré cet étage séparément.

### Étage 2 — quelle AFFAIRE dans ce bien ?

```
3 050 (79 %)  une seule chaine -> rien a departager
  790 (21 %)  deux chaines ou plus -> departage necessaire
```

---

## 2. ⭐⭐⭐ LE POUVOIR DE CHAQUE SIGNAL, MESURÉ UN PAR UN

Sur les **790 lignes à départager** :

| signal | désigne **1** | plusieurs | aucune | muet |
|---|---|---|---|---|
| **l'ÉTAT de l'affaire** | **563** | 224 | **3** | **0** |
| le **NOM** de l'acquéreur | 482 | 236 | 71 | 1 |
| la **DATE d'offre** | 479 | **3** | 137 | 171 |
| la **DATE de compromis** | 444 | **3** | 29 | 314 |
| la **COMMISSION** | 391 | 330 | 69 | 0 |
| le **PRIX** | 247 | **246** | **210** | 87 |

### Ce que ce tableau dit, et qui renverse ma cascade

**① Les DATES sont les signaux les plus PRÉCIS.** Quand elles parlent, elles se
trompent presque jamais : **3 ambiguïtés sur 479** et **3 sur 444**. Mais elles sont
souvent muettes *(171 et 314)*.
➡ **Un signal précis mais souvent muet doit venir EN PREMIER dans une cascade** — et
n'a rien à faire dans un score, où son silence le fait disparaître.

**② L'ÉTAT est le signal le plus DISPONIBLE** : **jamais muet** *(0)*, presque jamais
sans réponse *(3)*, et il décide **563 fois**. Or je ne m'en servais **que pour
départager des scores égaux**.

**③ Le PRIX est le pire signal** : il désigne plusieurs chaînes **246 fois** et aucune
**210 fois**. Et je lui donnais **2 points**. C'est normal : le prix bouge entre l'offre
et la vente, et deux tentatives sur un bien ont souvent le même prix.

**④ Le NOM n'est pas le roi** : 236 ambiguïtés, 71 sans réponse. Et il peut **mentir** —
nous avons mesuré **11 ventes qui portent le nom de l'acquéreur dont le compromis a été
annulé**. C'est lui qui a produit l'erreur GENILLON.

---

## 3. UN SIGNAL QU'ON N'UTILISE PAS DU TOUT : LE VENDEUR

```
4 270 (89 %)  le VENDEUR du classeur confirme le bien
  170 ( 3 %)  il ne colle pas -- a verifier
  326 ( 8 %)  l'un des deux cotes n'a pas l'information
```

⭐ **Le vendeur est le signal idéal de l'étage 1** : il est **le même pour toutes les
tentatives** d'un bien *(donc inutile à l'étage 2)*, mais **différent d'un bien à
l'autre** *(donc parfait pour choisir le bien)*.

### Et il règle les mandats recyclés

Sur les **737 lignes** dont le mandat désigne plusieurs biens :

```
251 (34 %)  le VENDEUR designe UN bien
208 (28 %)  a defaut, la VILLE
 20 ( 2 %)  a defaut, le PRIX DE L'ANNONCE
───
479 (65 %)  resolus par trois signaux que ma cascade N'UTILISE PAS

238 (32 %)  le vendeur colle a PLUSIEURS biens (le meme vendeur en possede plusieurs)
 20 ( 2 %)  indecidable
```

*(⚠ Les 238 ne sont pas perdus : la mesure n'a pas essayé la ville **à l'intérieur** des
candidats du vendeur. À affiner.)*

```
mandat 16705  vendeur TOURNIER   parmi 41559 (Beaulieu) et 54929 (Courpiere)  -> 54929
mandat 14637  vendeur CHAUTARD   parmi 31023 (Lempdes) et 50027 (Saint-Just)  -> 31023
```

---

## 4. ⭐⭐⭐ CE QUE DONNE UNE CASCADE PAR PRÉCISION + EXCLUSIVITÉ

Testée sur les 790 lignes à départager :

```
782 (98 %)  APPARIEE
  4 ( 0 %)  ambigue -- ABSTENTION
  4 ( 0 %)  aucune chaine libre : le classeur est plus fin que nous
```

**Et par quel signal :**

```
443  la date de compromis
197  la date d offre
108  l etat
 23  le nom
  5  le prix
  4  la commission
  2  il ne restait qu'une chaine libre
```

⭐ **Les dates font 640 des 782 (82 %).** Le nom, que je notais au maximum, en fait 23.

### L'exclusivité, et pourquoi elle est indispensable

Sans elle, deux lignes du classeur réclament la même chaîne et une autre reste orpheline —
**43 lignes sur 21 chaînes** aujourd'hui. Le cas que Frédéric a repéré :

```
bien 15220
   L40    COUDOUR  « Vente reglee »  ->  chaine 7500   OK
   L3405  GENILLON « Annulee »       ->  chaine 7500   FAUX, c'etait 7499
   et la chaine 7499 -- le compromis annule de GENILLON -- restait SANS LIGNE
```

⚠ **Et l'ordre de traitement compte** : une ligne que la date de compromis désigne doit
**réserver** sa chaîne **avant** qu'une ligne moins sûre ne la prenne. C'est pourquoi la
cascade boucle **signal par signal**, et non ligne par ligne.

---

## 5. 📋 LA MÉTHODE PROPOSÉE

### Étage 1 — LE BIEN *(nouveau)*

```
1. le n° de mandat
2. s'il designe PLUSIEURS biens :
     a. le VENDEUR             (251)
     b. sinon la VILLE         (208)
     c. sinon le PRIX d'annonce (20)
     d. sinon -> ABSTENTION, et on le DIT
3. et quand le mandat designe UN bien, le VENDEUR le CONFIRME (89 %)
   -> s'il contredit, on le signale sans refuser : le mandat reste le maitre
```

### Étage 2 — L'AFFAIRE DANS LE BIEN, par PRÉCISION

```
pour chaque signal, du plus sur au moins sur :
     1. la date de COMPROMIS
     2. la date d'OFFRE
     3. l'ETAT
     4. le NOM
     5. la COMMISSION
     6. le PRIX
   -> toute ligne que le signal designe SEULE prend sa chaine et LA RESERVE
   -> on passe au signal suivant avec les lignes et les chaines qui restent
   -> a la fin, s'il ne reste qu'UNE chaine libre pour UNE ligne, elle la prend
   -> sinon ABSTENTION, et on le DIT
```

### Étage 3 — LE VERROU DU NOM *(conservé)*

En sortie, si le classeur donne un nom lisible et qu'il ne figure **dans aucune étape** de
la chaîne retenue, **on refuse l'appariement** *(sauf faute de frappe, seuil 0,82)*.
⛔ *Un faux lien ne se voit pas ; une case vide, si.*

---

## 6. ⚠ CE QUE JE NE PROPOSE PAS, ET POURQUOI

| | |
|---|---|
| **un score pondéré** | il noie un signal précis mais rare dans le bruit d'un signal bavard et faux. C'est exactement ce qui s'est passé : prix 2 points, nom 3 points, dates ignorées |
| **se fier au nom en priorité** | **11 ventes portent le nom du mauvais acquéreur** *(celui dont le compromis a été annulé)*. Le nom est le signal qui a produit l'erreur GENILLON |
| **deviner les 8 restants** | 4 ambiguïtés + 4 « le classeur est plus fin que nous ». Ils restent **sans lien, et dits** |
| **réécrire quoi que ce soit dans le classeur** | l'appariement se range **chez nous**, et `ID Unique` suffit comme clé *(4 766 valeurs distinctes)* |

---

## 7. CE QUE ÇA DEVRAIT DONNER, ET CE QUI RESTE À MESURER

**Attendu, à confirmer en le codant :**

```
aujourd'hui   4 403 lignes appariees et confirmees (92,4 %)
              dont 43 qui se telescopent sur 21 chaines
              + 221 sans chaine + 142 refusees par le verrou

apres         les 43 telescopages regles (8 par l'etat, le reste nomme)
              + jusqu'a 479 des 737 mandats recycles mieux ancres
              -> le taux devrait depasser 95 %, A MESURER
```

⚠ **Je n'annonce pas de chiffre final** : l'étage 1 n'a été mesuré que sur les mandats
ambigus, pas de bout en bout. **Ça se mesure en codant la cascade et en la rejouant**,
comme on l'a fait pour le chaînage.
