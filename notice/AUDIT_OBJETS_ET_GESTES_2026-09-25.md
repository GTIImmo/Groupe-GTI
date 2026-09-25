# Audit complet — tous les objets, tous les gestes

*25/09/2026, demandé par Frédéric : « fais un audit de ce chat, de mon projet, du plan de dev
pour être sûr qu'il n'y a rien d'autre — comme les utilisateurs, agences, relations ou
transactions ». Établi **par le code et les deux bases**, pas par les notes.*

C'est le tableau que la méthode (CLAUDE.md §0) impose avant de conclure. **Une case qu'on ne
sait pas remplir est écrite « non mesuré », jamais sautée.**

## 1. Le tableau

| objet | créer | modifier | supprimer / archiver | lire |
|---|---|---|---|---|
| **annonce** | ✅ brouillon *(+ notre numéro depuis le 25/09)* | ✅ **182 champs** par groupes | ✅ supprimer · archiver · restaurer | ✅ |
| **contact** | ✅ | ✅ 24 champs | ✅ | ✅ |
| **recherche** | ✅ | ✅ | ✅ | ✅ |
| **relation (mandant)** | ✅ créer · rattacher | ✅ | ⛔ **AUCUN GESTE** | ✅ |
| **transaction** *(offre, compromis, vente)* | ✅ **par le changement de statut** de l'annonce | ✅ par reprise | ✅ annuler · supprimer | ✅ |
| **mandat** | ✅ numéro auto · document | ⚠ **prix, honoraires, surface SEULEMENT** | ⚠ clôture non mesurée | ✅ |
| **document** | ✅ envoyer | — | ✅ supprimer | ⛔ **ARRÊTÉ depuis le 23/08** |
| **photo** | ✅ ajouter | ⛔ **AUCUN** | ⛔ **AUCUN** | ⚠ partiel *(223 annonces sur 13 437)* |
| **RDV / visite** | ⛔ **AUCUN geste vers Hektor** | ⛔ | ⛔ | ⚠ 11 liens d'agenda |
| **couple** | ⚠ **c'est HEKTOR qui crée la 2ᵉ fiche** | ✅ *(via le contact)* | non mesuré | ✅ 37 404 liens traduits |
| **négociateur / agence** | ⛔ **lecture seule** | ⛔ | ⛔ | ✅ annuaire, 219 lignes |
| **utilisateur de l'app** | ⚠ 8 comptes · `F.1` **après** la coupure | ⚠ | ⚠ | ✅ |

## 2. Ce que cet audit ajoute — quatre trous jamais listés

### ⛔ ① On ne sait pas RETIRER un mandant d'un bien
Créer un mandant : oui. Le rattacher : oui. Le modifier : oui. **Le détacher : aucun geste**,
ni dans le worker, ni dans le front. Un mandant rattaché par erreur ne peut se corriger que
dans Hektor.

### ⛔ ② Les négociateurs et les agences sont en LECTURE SEULE
L'annuaire *(219 lignes)* descend de Hektor chaque nuit. L'app **ne sait ni en créer, ni en
modifier, ni en désactiver** — elle sait seulement **affecter** un négociateur à une annonce.
⚠ **À la coupure, plus personne ne pourra créer un négociateur ni changer une agence.**
C'est un manque de la même famille que `A.1` et `A.2` : il ne se voit pas aujourd'hui, et il
bloque le jour J.

### ⛔ ③ Les RDV et les visites ne partent jamais chez Hektor
**Aucun geste** : ni créer, ni modifier, ni supprimer. L'app gère un agenda de son côté
*(11 liens)*, mais **les visites saisies dans Hektor ne sont importées nulle part** — audit du
19/09, jamais traité depuis. ➡ Frédéric a déjà noté que ce sujet **attend son arbitrage**.

### ⚠ ④ Les utilisateurs, rôles et droits sont rangés « APRÈS la coupure »
`F.1`. **À vérifier** : est-ce tenable ? Pendant la période où les négociateurs travaillent
dans l'app **et** dans Hektor, qui donne les droits, et sur quoi ? **Non mesuré.**

## 3. Ce que l'audit CONFIRME — et une erreur de ma part

- **Les transactions sont complètes.** J'ai d'abord cru le contraire, parce que je cherchais
  des gestes `create_hektor_offre` qui n'existent pas. **Ce n'est pas le modèle de Hektor** :
  on crée une offre, un compromis ou une vente **en changeant le statut de l'annonce**
  *(`offer` → `createOffre`, `compromise` → `createCompromis`, `sold` → `createVente`)*.
  Les quatre gestes sont là : créer, reprendre, annuler, supprimer.
- **Les relations** sont complètes sauf le détachement *(trou ①)*.
- **Les contacts, recherches, annonces** : les quatre gestes existent.
- **36 types de travaux, 0 en erreur** sur 55 509.

## 4. Ce qui reste ouvert, dans l'ordre

| | quoi | pourquoi maintenant |
|---|---|---|
| 1 | **`D.0` documents** | **perte de données en cours**, 33 jours |
| 2 | **`C.9-couple`** · **`L9`** | ⚠ **date de péremption** : impossible après la coupure |
| 3 | **négociateurs / agences** *(trou ②)* | même famille : bloque le jour J, **à chiffrer** |
| 4 | **`A.1` portails · `A.2` signature** | à zéro, ils fixent la date |
| 5 | **photos** | 13 437 vignettes chez Hektor ; **arbitrage sur l'affichage** |
| 6 | **`L5`** | prolonger un mandat · gestes photo · fusion de doublons |
| 7 | **retirer un mandant** *(trou ①)* | petit, jamais listé |
| 8 | **RDV / visites** *(trou ③)* · **`F.1`** *(trou ④)* | **arbitrages de Frédéric** |
| 9 | rattrapages de coupure · petits défauts d'écran | la veille, ou au fil de l'eau |

## 5. Non mesuré — je le dis plutôt que de le supposer

- la **clôture d'un mandat** *(`C.13`)* : quels gestes existent vraiment ;
- la **suppression d'un couple** chez Hektor ;
- si `F.1` peut réellement attendre la coupure ;
- ce que deviennent les **droits** pendant la période mixte.
