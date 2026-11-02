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
| montant | **aucun** | **tous** en ont un |
| séquestre | — | **tous** en ont un |
| propositions / historique | **liste vide** | — |
| témoin de contraste | **0 des 11 131 autres offres** est dans ce cas | 14 % des annulés |

**Les offres sont des coquilles : Hektor ne porte rien du tout, juste un lien entre
un bien et un acquéreur. Les compromis sont de vrais compromis complets à qui il
manque la seule date — et c'est normal, ils n'ont pas été signés.**

⚠ Et « annulée » n'est **pas** prouvé pour les offres : Hektor ne dit pas
« annulée », il ne dit **rien**. Une absence n'est pas un statut.

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
