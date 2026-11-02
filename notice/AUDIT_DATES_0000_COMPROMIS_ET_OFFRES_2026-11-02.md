# AUDIT — LES DATES `0000-00-00` : RAISON, ET CE QU'ON EN A FAIT
**02/11/2026** — demandé par Frédéric : *« avant de retiré les date corrigé sur les
compromis audit pour savoir la raison et comment on a fais avec les compromis pour
les date 0000 »*.

> ⛔ **RIEN N'A ÉTÉ RETIRÉ AUX COMPROMIS.** Mon correctif du matin allait les vider
> dès la nuit suivante, par symétrie avec les offres. Je l'ai **désarmé avant** cet
> audit : `build_contacts_layer.py` ne juge plus les `0000` du compromis ni de la
> vente. Les **252** relations de compromis à `0000` sont intactes, contrôlé.

---

## 1. LA RAISON — mesurée, et elle est nette

Un compromis sans date **n'a pas été signé**. Le `date_start` de Hektor est la date
de signature : annulé avant signature, il n'y a rien à y mettre.

Le chiffre le dit sans ambiguïté :

- compromis **annulés** : **196 sans date sur 1 375** — **14,25 %**
- compromis **actifs** : **15 sans date sur 9 267** — **0,16 %**

**Un compromis annulé a près de 90 fois plus de chances d'être sans date.** Ce n'est
donc pas un défaut de lecture ni une perte : c'est une information. Hektor dit
« pas de date » parce qu'il n'y en a pas eu.

⚠ **Restent les 15 ACTIFS sans date, et ceux-là sont anormaux.** C'est la famille
que le § 2.7 avait déjà repérée le 20/10 (« 12 compromis ACTIFS sans date, tous à
`0000-00-00`, tous vus pour la première fois en 2026-07 — un lot arrivé sans sa
date »). Le § 2.7 n'est **pas allumé** : `APP_CHAINAGE_SANS_DATE` vaut 1, pas 2.

### Les chiffres exacts, et d'où ils viennent

| | |
|---|---|
| au miroir, `date_start` à `0000` | 199 |
| au miroir, `date_start` à `1990` | 7 |
| au registre, compromis à `0000` | **204** |
| au registre, compromis à `1990` | 7 |
| relations contact (compromis) à `0000` | **252** |

⭐ **Les deux écarts sont expliqués, aucun n'est un mystère :**

- **204 contre 199** : 5 de ces compromis ont été **effacés chez Hektor** et
  conservés chez nous (`present_in_hektor = false`). C'est voulu — le carnet est à
  nous, on garde la trace.
- **252 contre 204** : une relation **par acquéreur**. Un compromis à deux
  acheteurs fait deux relations.

⚠ `date_end` est à `0000` sur **10 292** compromis sur 10 631 — Hektor ne la
renseigne presque jamais. Elle n'arrive jamais au registre parce que `date_start`
passe avant elle dans la cascade. Rien à corriger, mais à savoir avant de bâtir
quoi que ce soit sur `date_end`.

---

## 2. CE QU'ON A FAIT AVEC — la réponse à la question

**Trois décisions, prises à des moments différents, et elles tiennent ensemble.**

**a) La date est GARDÉE telle quelle.** Les 204 + 7 affichent encore `0000-00-00`
ou `1990-01-01` au registre. Personne ne les a jamais vidées. C'est l'état depuis
l'origine, par absence de décision contraire.

**b) Mais elle n'a JAMAIS servi au chaînage.** `_date_utile` refuse toute année hors
`2000-2030`. Ces compromis sont donc « sans date » pour le chaînage **depuis
toujours** — c'est-à-dire : chacun seul dans sa chaîne.

**c) Et le 20/10, un repli a été posé pour les recoller par le NOM** — le § 2.6,
que Frédéric a demandé ce jour-là (« fais le repli par le nom »). Il est allumé en
production et rattache aujourd'hui **117 compromis annulés**, plus 1 abstention
pour cause de plusieurs chaînes au même nom.

### ⭐⭐ ET LA QUESTION DE LA DATE ELLE-MÊME N'A JAMAIS ÉTÉ TRANCHÉE

Elle a été **explicitement reportée**, et c'est écrit noir sur blanc dans
`notice/AUDIT_REGLE_CHAINAGE_2026-10-20.md` :

> *« toucher aux 213 sans date — c'est un autre sujet (les `0000-00-00` de Hektor),
> à traiter séparément. »*

Et dans la liste « ce qui reste à trancher par Frédéric » du même audit, la
question 3 était :

> *« Les 213 transactions sans date : autre chantier, ou tout de suite ? »*

**Elle n'a pas reçu de réponse.** C'est exactement elle qui remonte aujourd'hui, par
la porte des offres. Treize jours de réserve non traitée — la règle du projet le
dit : *une réserve d'audit non traitée devient le bug.*

---

## 3. ⚠ CE QUE J'AI CRÉÉ CE MATIN, ET QU'IL FAUT ASSUMER OU DÉFAIRE

En corrigeant les offres, j'ai rendu les deux familles **incohérentes** :

- une **offre** sans date exploitable → la date est **vide** (68 lignes)
- un **compromis** sans date exploitable → la date affiche **`0000-00-00`** (211)

Même problème, deux affichages. Ce n'était pas une décision, c'est un effet de
bord de mon correctif.

### ⭐ MAIS LES DEUX FAMILLES NE SONT PAS DE MÊME NATURE — c'est mesuré

C'est le point qui doit guider la décision, et il vient de l'intuition de Frédéric
sur VA30156 (*« surement annulé car pas de date et annonce clos »*) :

| | les 54 offres | les 211 compromis |
|---|---|---|
| statut chez Hektor | **aucun** | 196 annulés, 15 actifs |
| montant | **aucun** *(⚠ voir le correctif ci-dessous : la colonne `raw_montant` est vide sur les 11 131 aussi — ce n'est pas un signe)* | **tous** en ont un |
| séquestre | — | **tous** en ont un |
| propositions / historique | **liste vide** | — |
| témoin de contraste | **0 des 11 131 autres offres** est dans ce cas | 14 % des annulés |

**Les offres sont des coquilles : Hektor ne porte aucune PROPOSITION, juste un lien
entre un bien et un acquéreur nommé *(⚠ « rien du tout » était faux, voir § 3 bis)*. Les compromis sont de vrais compromis complets à qui il
manque la seule date — et c'est normal, ils n'ont pas été signés.**

⚠ Et « annulée » n'est **pas** prouvé pour les offres : Hektor ne dit pas
« annulée », il ne dit **rien**. Une absence n'est pas un statut.

### ⛔ LES 68 OFFRES SANS DATE NE SONT PAS 68 COQUILLES — 54 + 14

Frédéric, 02/11 : *« les 54 coquilles sont toutes les offres sans date ? ou autres
choses ? »* — non, et la distinction commande la décision. Croisé sur les 11 199
offres du miroir, aucune case n'est ambiguë :

- **date absente, rien du tout : 54 — toutes coquilles, 0 avec un état**
- **date à `0000-00-00` : 14 — 0 coquille, toutes portent un état**
- date utilisable : 11 131 — 0 coquille

⭐ **Équivalence STRICTE dans les deux sens** : le témoin inverse (« une coquille
peut-elle avoir une date ? ») donne **0**, et le parc entier ne compte que **54**
coquilles. Il n'y en a pas une ailleurs.

**Les 14 sont de VRAIES offres**, et les masquer serait une perte :

- chacune porte **2 propositions** typées (`proposition`, `accepte`, `refus`)
- **14 sur 14 ont un montant** — de **65 000 €** à **328 000 €**
- états : **6 acceptées**, 7 proposées, 1 refusée
- seule la **date** manque, et elle vaut `0000-00-00` **jusque dans les
  propositions** — c'est pourquoi `_date_de_tri` ne peut pas la récupérer là

Exemple : l'offre 1142 (bien 53984) = proposition 97 000 € puis **accepté**
97 000 €. C'est une offre acceptée dont on ignore la date, pas une coquille.

⭐ **6 des 14 ont rejoint leur affaire** grâce au § 2.9 posé ce matin (1142, 1308,
3960, 7643, 8601, 9856). Les 8 autres restent seules, faute de cible unique.

➡ **Conséquence pour le point 3 du § 4** : la question « montrer, étiqueter ou
masquer » ne se pose que pour les **54**. Les 14 doivent rester visibles — il n'y
manque qu'une date.

### ⛔⛔ 3 bis. « LES 54, AUCUNE INFO ??? » — NON, ET J'AVAIS TORT DEUX FOIS

Frédéric, 02/11 : *« LES 54 NON AUCUNES INFO ??? »*. Il a eu raison de me reprendre.
Mesuré en ouvrant la charge **brute** de Hektor (`hektor_offre.raw_json`, colonne que
je n'avais pas regardée), sur les 54 et sur les 11 131 pour comparer.

**MES DEUX ERREURS, et elles viennent du même défaut de méthode :**

⛔ **J'ai pris pour des signes des colonnes qui sont vides PARTOUT.** `raw_status` :
vide sur les 54 **et sur les 11 131**. `raw_montant` : idem, **0 %** des deux côtés.
`nom`, `prenom`, `civ`, `id_mandat` : vides sur les 54, mais vides aussi sur 76 % à
97 % des normales. ⚠ **Un champ vide ne devient un symptôme que si on a mesuré qu'il
est rempli ailleurs.** Je ne l'avais pas fait.

⛔ **J'ai dit « Hektor ne porte rien du tout ».** C'est faux. Ce que les 54 portent :

```
numero d'offre Hektor                      54 / 54
le bien, complet (dossier VA…, prix, titre) 54 / 54
l'acquereur, identifie                      54 / 54
  dont son NOM                              52 / 54
  dont sa VILLE                             48 / 54
  dont sa date d'enregistrement             54 / 54
  dont 17 acquereurs ARCHIVES depuis
```

⭐ **IL N'Y A QU'UN SEUL CHAMP VRAIMENT ABSENT, ET C'EST LA CAUSE DE TOUT LE RESTE :**
la liste `propositions` est **vide sur les 54, pleine sur 11 131 / 11 131 (100 %)**.
C'est le seul contraste net du jeu. Et chez Hektor **le montant, le statut et la date
d'une offre vivent DANS les propositions**, jamais dans l'offre — une proposition
ressemble à ceci :

```
{"id":"31360","type":"proposition","montant":"59000","date":"2021-11-09 22:59:59", …}
{"id":"31358","type":"accepte",    "montant":"59000","date":"2021-11-09 23:00:00", …}
```

➡ **Donc « sans date », « sans montant » et « sans statut » ne sont pas trois défauts :
c'est UN SEUL FAIT dit trois fois.** La bonne définition d'une coquille est :
**une offre dont la liste des propositions est vide.**

**LA COHORTE EST FRAPPANTE** : **53 des 54** ont un acquéreur enregistré entre **2007
et 2010** (32 en 2008), une seule en 2020. Les numéros d'offre sont contigus
(6197 → 6265, plus la 3316 isolée). Ça ressemble à du vieux fonds dont les
propositions n'ont pas suivi — ⚠ mais **ce n'est pas prouvé**, je n'ai pas la trace
de l'import.

⛔ **ET UNE PISTE EST MORTE, je le dis plutôt que de la laisser croire** : j'ai testé
si le **numéro d'offre** permettait de retrouver la date par encadrement entre voisins.
**Non** : sur les 11 131 offres datées triées par numéro, **53,9 % des voisins sont en
désordre** — le numéro n'est pas chronologique. Résultat : **0 des 54** est encadrée au
même mois. **On ne peut pas deviner leur date.**

➡ **CE QUE ÇA CHANGE POUR LA DÉCISION DU § 4 POINT 3** : masquer les 54, ce n'est pas
masquer du vide — c'est retirer **52 noms d'acquéreurs rattachés à 49 biens**, avec
leur ville et leur ancienneté. ⭐ **Et ça rend l'appel à `/Api/Offre/OffreById/` plus
utile, pas moins** : s'il existe un détail, c'est là que les propositions manquantes
pourraient se trouver — c'est le seul champ qui manque.

---

## 4. CE QUI RESTE À TRANCHER PAR FRÉDÉRIC

```
1. LES COMPROMIS A 0000 : on vide la date (comme les offres), ou on la garde
   affichee telle quelle ? Garder a un sens -- « compromis non signe » est une
   information ; mais « 0000-00-00 » ne la dit pas a l'utilisateur.
   ⭐ Troisieme voie : vider la date ET ecrire « non signe » a la place.

2. LES 15 COMPROMIS ACTIFS SANS DATE : ce sont les anormaux. Le § 2.7 existe,
   il est code et mesure, il n'est PAS allume (cran 2). On l'allume ?

3. LES 54 COQUILLES D'OFFRE : les montrer, les etiqueter, ou les masquer ?
   ⭐ AVANT de choisir : interroger /Api/Offre/OffreById/ sur 2 ou 3 d'entre
   elles (6251, 6252, 6261) pour savoir si le DETAIL en dit plus que la liste.
   3 requetes, 3 secondes. Tant qu'on ne l'a pas fait, on ne sait pas si on
   masque du vide ou si on masque une donnee qu'on n'a pas su lire.
   ⚠ Accord requis : toucher l'API Hektor (blocage IP du 29/10).

4. LES 7 COMPROMIS A 1990-01-01 : jamais regardes de pres, 7 lignes.
```

---

## 5. CE QUI EST DÉJÀ FAIT, ET PROUVÉ

- registre : 68 offres sans date, **0 compromis touché** (9 contrôles verts)
- fiches contact : **66 relations d'offre nettoyées**, les 252 compromis à `0000`
  **intacts** (témoin inverse vert), 11 112 relations d'offre gardent leur date
- sauvegardes datées : `app_affaire_ledger_avant_offre_sans_date_20261102` (178
  lignes) et `app_contact_relation_avant_offre_sans_date_20261102` (66 lignes)
- retour arrière : `supabase/retour_arriere_offre_sans_date_2026-11-02.sql`
