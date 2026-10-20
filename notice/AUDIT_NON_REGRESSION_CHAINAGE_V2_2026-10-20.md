# AUDIT DE NON-RÉGRESSION — après le chaînage V2

**20/10/2026, après la mise en production. LECTURE SEULE.**

Demandé par Frédéric : *« refais un audit pour être sûr que tes corrections n'ont rien
endommagé dans le projet, puis remesure les 37. Et pourquoi les 213 posent problème ? »*

---

## 1. RIEN N'EST ENDOMMAGÉ — onze contrôles, tous verts

### Les volumes : rien n'a bougé

| | avant | après |
|---|---|---|
| lignes du registre | 31 084 | **31 084** |
| offres | 11 187 | **11 187** |
| compromis | 10 633 | **10 633** |
| ventes | 9 264 | **9 264** |
| lignes sans chaîne | 0 | **0** |
| lignes de répartition | 16 071 | **16 071** |

➡ **Aucune ligne perdue, aucune ligne créée.** Seuls les **numéros de chaîne** ont changé
— ce qui est exactement l'objet du chantier.

### Les contrôles de cohérence

| contrôle | résultat |
|---|---|
| deux ventes dans une chaîne | **0** |
| deux compromis vivants dans une chaîne | **0** |
| un bloc daté **après** la vente qui ferme sa chaîne | **0** |
| ⭐ une chaîne qui mélange **DEUX BIENS** | **0** |
| ⭐ une chaîne dont la répartition dépasse **100 %** | **0** |
| ⭐ une personne comptée **deux fois** sur un même côté | **0** |
| répartition orpheline | **2** *(celles d'avant : l'affaire 1001347, disparue)* |
| `app_affaire_note` · `app_affaire_condition` *(portent une chaîne)* | **0 ligne** — rien à casser |

⭐ Les trois contrôles marqués sont **neufs** : je ne les avais pas posés avant. Ils
vérifient qu'une fusion n'a pas franchi une frontière qu'elle ne devait pas franchir.

### Ce qui pourrait crier demain matin : rien

| sonde | seuil | valeur |
|---|---|---|
| `app_affaires_sans_numero_hektor` | 0 | **0** |
| `app_annonces_sans_numero_hektor` | 0 | **0** |
| les 4 contrôles de `verifier_regle_chainage.py` | — | **verts, sortie 0** |
| `écarts base ↔ règle` | 0 | **0** |

⚠ **Le seul écart connu, et il est documenté** : la fonction Supabase `app_chaine_pour`
n'a pas reçu la V2. Elle ne sert qu'aux affaires **nées dans l'app** — **1 en octobre,
15 en septembre** — et la divergence dure **moins de 24 h**, le run suivant recalculant
tout. **Non bloquant, et dit.**

---

## 2. LES 37, REMESURÉES : **elles sont 4**

```
« Vente reglee » chez lui, pas de vente chez nous :   37  ->  4
```

Les quatre restantes : mandats **3816** *(BETIN LEJEUNE)*, **3201** *(CLAUDET)*,
**2959** *(DESITTER)*, **17593** *(DEBRAIZE Patrick)*.

➡ **33 des 37 n'étaient pas des trous dans nos données : c'était le chaînage.** Et
l'appariement avec le classeur passe de 4 329 à **4 385 lignes** appariées.

### Le croisement complet des états, sur la base saine

```
Vente reglee  -> abouti            3 511   OK
Annulee       -> echec               597   OK
Vente prevue  -> compromis            60   OK
Offre d'achat -> offre acceptee       24   OK
Vente fixee   -> compromis            18   OK
Compromis att.-> offre acceptee       14   OK
─────────────────────────────────────────────
Annulee       -> offre acceptee      114   <= ECART, le gros morceau
Annulee       -> abouti               24   <= ECART
Vente reglee  -> echec                 9   <= ECART
Vente reglee  -> compromis             4   <= ECART
```

⚠ **Les 114 « Annulée → offre acceptée » n'ont PAS bougé.** C'est maintenant le seul
gisement sérieux côté classeur, et **il n'a pas encore été audité comme les 37 l'ont
été** — c'est-à-dire en vérifiant d'abord que l'appariement est bon. *(Je m'étais trompé
une fois là-dessus : ne pas recommencer.)*

---

## 3. POURQUOI LES 213 POSENT PROBLÈME — **et elles sont 225 aujourd'hui**

### Ce qu'elles sont

```
225 transactions sans date exploitable
   211  compromis        14  offres
   218  portent « 0000-00-00 »   (le « vide » de Hektor)
     7  portent « 1990-01-01 »
```

### Pourquoi la règle ne peut rien en faire

**La règle de chaînage travaille dans l'ORDRE DES DATES.** Elle place chaque transaction
dans une séquence, et décide d'après ce qui est *ouvert à ce moment-là*. **Une
transaction sans date n'a pas de place dans la séquence.** Le code est explicite :

```
# sans date : chacune sa chaine, elle-meme, et on n'y revient plus
```

### Le dégât, chiffré

```
194 sur 225 (86 %) sont sur un bien qui porte D AUTRES transactions
 31 sur 225 (13 %) sont seules sur leur bien -- aucun degat
```

Exemple, bien 558 :

```
compromis 205  SANS DATE  chaine 205   <- seule
compromis 204  2022-06-16 chaine 204 ─┐
offre     206  2022-03-02 chaine 206  │  l affaire complete
offre     207  2022-05-16 chaine 204  │
vente     208  2022-07-08 chaine 204 ─┘
```

➡ **L'affaire est coupée par une date manquante**, pas par un désaccord métier.

### ⛔ Et il n'existe AUCUNE date de secours

| colonne | disponible sur les 225 |
|---|---|
| `date_acte` | **0** |
| `date_fin_retractation` | **0** |
| `first_seen_at` / `last_seen_at` | 225 — **mais c'est le jour où NOUS avons lu la ligne** |

Toutes les 225 ont `first_seen_at = 2026-07-31` : la date de notre lecture, pas celle du
compromis. **Inutilisable pour ordonner une séquence de 2022.**
➡ **La vraie date n'existe que chez Hektor**, et il ne nous la donne pas. La récupérer
serait **une lecture chez Hektor**, pas une déduction : c'est un autre chantier.

### ⭐⭐ MAIS IL Y A UNE PORTE, ET C'EST LA TIENNE

Le **nom** n'a pas besoin de date. Mesuré sur les 225 :

```
132 (58 %)  UNE SEULE chaine du bien partage son nom  -> RATTACHABLE
 36 (16 %)  plusieurs chaines partagent son nom       -> ambigu, abstention
 35 (15 %)  seule sur son bien                        -> rien a faire
 16 ( 7 %)  aucune chaine ne partage son nom          -> vraiment seule
  6 ( 2 %)  elle n a pas de nom                       -> le nom ne peut pas aider
```

Et les cas rattachables sont **exactement la même famille que ton point 4** :

```
bien 408   compromis 137 ANNULE  LASSABLIERE Tiphaine  -> chaine 138
bien 558   compromis 205 ANNULE  PONS Eric             -> chaine 206
bien 822   compromis 258 ANNULE  GONTHIER Benjamin     -> chaine 262
```

➡ **Les 213 ne sont pas un mystère séparé : c'est le point 4, empêché par la date
manquante.** Le remède serait le même geste — *« à défaut de pouvoir t'ordonner, je te
rattache par le nom s'il n'y a qu'une candidate »* — et il vaudrait **132 affaires**.

⛔ **Je ne le propose pas aujourd'hui** : c'est un quatrième repli dans la règle, il
demande sa décision, et le chantier qui vient de se clore doit d'abord tenir trois nuits.

---

## 4. CE QUI RESTE, CLASSÉ PAR TAILLE

```
132  les sans-date rattachables par le nom     -> la suite naturelle du point 4
114  « Annulee » chez lui / offre acceptee chez nous  -> A AUDITER comme les 37
 93  les sans-date non rattachables (36 ambigues + 35 seules + 16 + 6)
 42  ventes seules  ·  6 ambigues  ·  4 abstentions  -> VOULU, dites au journal
  4  « Vente reglee » sans vente chez nous      -> a regarder une par une
  2  repartitions orphelines (l affaire 1001347, disparue avant la V2)
```
