# Étude — le statut d'une annonce : d'où il vient, qui le change, ce qu'il déclenche

**Lecture seule.** Demandée par Frédéric le 01/09/2026 : *« je veux une étude plus approfondie…
les interactions de statut manuel, suite transaction, suite mandat, pour avoir une parfaite
connaissance de mon projet avant de me proposer la solution. »*

Écrite **en lisant le code et en mesurant la base**, jamais en déduisant des notes.

---

## 1. Le fait central, et il n'était nommé nulle part

**Dans l'app, on ne crée pas une transaction : on change le statut, et Hektor crée la
transaction.** C'est la table de configuration du worker qui le dit
(`console_job_worker.js`, `HEKTOR_STATUS_CONFIG`) :

```
   active      valeur 2   diffusable = 1     aucune transaction
   offer       valeur 3   -> createOffre     CREE l'offre
   compromise  valeur 4   -> createCompromis CREE le compromis
   sold        valeur 5   -> createVente     CREE la vente
   closed      valeur 6   diffusable = 0     aucune transaction
```

D'où **l'asymétrie qui gouverne tout le reste** :

```
   CREATION     le STATUT est la cause        ->  Hektor cree la transaction
   ANNULATION   la TRANSACTION est la cause   ->  Hektor redescend le statut
```

Toute règle qui prétendrait déduire le statut des transactions ne vaudrait donc que dans **un
seul sens**. C'est l'erreur que cette étude a évitée.

---

## 2. Les trois sources de changement de statut

| source | ce qu'elle fait | mesure |
|---|---|---|
| **manuel** — modale « Faire évoluer le statut » | pose le statut **ET** crée la transaction | 42 travaux depuis le 21/05 |
| **transaction** — refuser · annuler · supprimer | ⚠ **DEMENTI LE 02/09 pour le REFUS : Hektor ne redescend PAS** *(cycle 1, bien propre)*. Annuler et supprimer : non encore mesures | 3 gestes, éprouvés 29-31/08 |
| **mandat** — statut « Clos » | pose le statut **ET coupe la diffusion** | 9 passages à `closed` |

### 2.1 La modale n'est pas un sélecteur, c'est un formulaire de transaction

Elle porte **vingt champs** : montant, prix de vente, date de transaction, date de signature,
délais de validité et de rétractation, mandat choisi, acquéreur, notaire, honoraires acquéreur
et leur taux, prix net vendeur, séquestre, motif de clôture, état et raison de clôture,
clôture du mandat à la vente, prix de clôture, et le choix « après vente ».

C'est cohérent : puisque changer le statut **crée** la transaction, il faut bien lui donner sa
matière.

### 2.2 Usage réel des cibles

```
   active       13    dont les retours en arriere
   compromise   10
   closed        9
   sold          7
   offer         2
   ------------------
                41 reussis + 1 echec
```

---

## 3. L'effet de bord que personne n'avait nommé : la diffusion

```
   passer a Actif  ->  diffusable = 1   LE BIEN REPART SUR LES PORTAILS
   passer a Clos   ->  diffusable = 0   LE BIEN EN SORT
```

**Le statut pilote la diffusion.** Une règle qui calculerait le statut automatiquement
piloterait donc aussi les portails — c'est-à-dire de la visibilité publique et de l'argent.

➡ **ARBITRAGE DE FRÉDÉRIC, 01/09** : *un bien dont le compromis vient d'échouer ne repart
**pas** en diffusion automatiquement.* La redescente de statut ne doit jamais toucher
`diffusable`.

---

## 4. La règle d'Hektor, extraite des données (pas supposée)

Sur les 720 biens du portefeuille, le croisement `statut × vente × compromis × offre` donne
une règle **parfaitement régulière** :

```
   vente vivante                          ->  Vendu
   sinon compromis actif                  ->  Sous compromis
   sinon offre acceptee                   ->  Sous offre
   sinon (tout annule/refuse, ou rien)    ->  Actif
```

Les cas qui la confirment par la bande :

```
   compromis annule, rien d'autre  ->  Actif           5 biens
   offre refusee, rien d'autre     ->  Actif           9 biens
   compromis actif + offre acceptee -> Sous compromis  90 biens
   offre acceptee seule            ->  Sous offre      40 biens
```

**Une transaction annulée ou refusée ne compte pas.** Le statut suit l'étape la plus avancée
**encore vivante** de l'affaire — et une affaire a trois étapes : **offre → compromis → vente**
*(définition de Frédéric, 01/09)*.

### 4.1 « Clos » est hors de cette règle

Aucune transaction ne produit « Clos ». Il vient de la **clôture du mandat**, geste distinct
(C.13). ➡ **ARBITRAGE DE FRÉDÉRIC, 01/09 : « Clos » reste manuel.**

### 4.2 L'archivage est hors de cette règle aussi

`archive` (dans le portefeuille / hors du portefeuille) est **indépendant** du statut. Mesure :

```
   PORTEFEUILLE   Estimation 12 660 · Actif 582 · Sous compromis 93 · Sous offre 45
   HISTORIQUE     Vendu 8 767 · Clos 132
   ARCHIVES       Clos 33 862 · Vendu 423 · Actif 173 · Estimation 30
```

Les **173 « Actif + archivé »** prouvent qu'on archive sans vendre ; les **8 767 « Vendu non
archivé »** contre **423 archivés** montrent que **95 % des ventes ne sont pas archivées**.

➡ Conséquence pour C.19-c : le choix « laisser actif / archiver » codé le 30/08 présente à
égalité une option prise dans **5 %** des cas. Frédéric a tranché le 01/09 : **retirer le choix
pour « Vendu »**, le bien reste au portefeuille avec le statut Vendu.

---

## 5. Ce que la coupure emporte — et ce qu'elle n'emporte pas

```
   CE QUI SURVIT
      la CREATION. C'est l'utilisateur qui pose le statut dans la modale, et l'app
      le sait a l'instant du clic. Elle n'attend personne.

   CE QUI DISPARAIT
      la REDESCENTE. Apres une annulation, un refus ou une suppression, c'est
      HEKTOR qui recalcule le statut et le renvoie par la resynchronisation.
      Le jour de la coupure, le bien resterait affiche « Sous compromis » alors
      que le compromis n'existe plus.
```

**Le trou est donc plus petit qu'il n'y paraissait : il ne concerne que la redescente.**

Aujourd'hui déjà, entre le geste et la réponse d'Hektor, l'écran ment : `app_affaire_ledger`
sait que le compromis est annulé (écrit par `app_geste_affaire_optimistic` dans la même
transaction que le travail), mais `app_dossier_current.statut_annonce` affiche encore
« Sous compromis ».

---

## 6. Ce que l'app fait déjà, et ce qui manque

```
   ✅  app_geste_affaire_optimistic   controle le geste, ecrit l'etat dans le ledger,
                                      cree le travail -- tout dans la meme transaction
   ✅  les donnees                    app_dossier_current porte offre_state,
                                      compromis_state, vente_id
   ✅  un debut de calcul             mandatStatutForRegister (front) : vente_id -> Vendu,
                                      date_cloture -> Clos
   ❌  UN SEUL endroit qui calcule la redescente et l'ecrive
```

---

## 7. La solution — ✅ CODÉE le 01/09

**Une règle de REDESCENTE seulement**, appelée par les gestes d'annulation.

⚠ **CORRIGE LE 02/09 — ELLE N'EN APPELLE PLUS QUE DEUX.** Le cycle 1 a mesuré, sur un
bien vierge de toute intervention manuelle, que **Hektor ne redescend pas le statut après
un refus d'offre**. `refus` a donc été retiré : *« il faut que notre app se colle aux
mécanismes d'Hektor… le but est de RESPECTER HEKTOR »* (Frédéric, 02/09). Restent
`annuler` et `supprimer`, **non encore mesurés** — ils servent d'instrument de comparaison
jusqu'aux cycles 3 et 4.


```
   reste-t-il une vente vivante ?   -> Vendu
   sinon un compromis actif ?       -> Sous compromis
   sinon une offre acceptee ?       -> Sous offre
   sinon                            -> Actif
```

**Où elle écrit, et pourquoi aux deux endroits :**

```
   app_dossier_current.statut_annonce   pour que ce soit VISIBLE tout de suite
                                        (table refaite chaque nuit, mais c'est
                                         elle que l'ecran lit)
   app_annonce_champ_app ('statut')     pour que ca SURVIVE a la coupure
                                        (carnet jamais reconstruit ; il accepte
                                         deja statut_annonce, et reste DORMANT
                                         tant que CHAMPS_APP_ANNONCE est vide)
```

**Ce qu'elle ne touche jamais : `diffusable`.** *(arbitrage du 01/09)*

**Et pourquoi maintenant plutôt qu'à la coupure :** pendant des semaines, à chaque
resynchronisation, on peut comparer ce que la règle a calculé à ce qu'Hektor renvoie. Une
sentinelle compte les écarts. Le jour de la bascule, la règle sera déjà éprouvée — au lieu
d'être allumée à l'aveugle. C'est la méthode de la **doublure**, celle du registre des
recherches et du numéro de contact.

---

## 7bis. Ce qui a été codé le 01/09, et ce que la mesure a corrigé

```
   app_statut_redescente_calcule()   la regle seule, sans effet de bord
   app_statut_rang()                 l'echelle a quatre barreaux
   app_geste_affaire_optimistic()    la regle branchee sur le geste, avec ses bornes
   restaurerStatutRedescendu()       si Hektor refuse, le statut remonte aussi
   app_ecart_statut_regle            la doublure : la regle a vide, a cote du vrai statut
   data.ecart_statut_regle           la sentinelle, seuil 4
```

**LES TROIS BORNES, telles qu'elles sont codées :**

```
   1  la regle ne s'eveille QUE sur un geste d'ANNULATION.
      ⚠ 02/09 : `refus` RETIRE -- mesure du cycle 1, Hektor ne redescend pas.
         Restent `annuler` et `supprimer`, non mesures.
      « accepte » en est exclu : c'est une CREATION, et une creation chez Hektor
      cree une transaction. L'utilisateur pose le statut lui-meme dans la modale.

   2  elle ne fait JAMAIS remonter. Rang calcule >= rang actuel -> on ne touche rien.

   3  elle ne touche JAMAIS diffusable. Ni archive.

   (+) hors echelle -> on ne touche rien. « Estimation » et « Clos » n'ont pas de
       barreau : c'est ce qui protege les 8 fiches d'estimation qui portent encore
       une vente de 2016-2021.
```

### CE QUE LA MESURE A CORRIGÉ — la règle était fausse, sur un bien

La première écriture demandait une offre **acceptée**. Le passage à vide sur les 13 380 biens
a trouvé **un seul** contre-exemple : `VT9514` (annonce 58957), offre `proposed` et statut
« Sous offre » chez Hektor.

➡ **Hektor passe le bien « Sous offre » dès que l'offre est POSÉE.** Une offre proposée est
vivante ; seule une offre **refusée** est morte. La règle a été corrigée avant tout usage.

### L'ÉTAT DE LA DOUBLURE au 01/09

```
   716 accords parfaits sur les 720 biens de l'echelle
     4 ecarts -- et les quatre sont des REMONTEES, donc bloquees par la borne 2
```

Ces quatre écarts sont instructifs : **ce sont de vraies incohérences du côté Hektor**, pas des
erreurs de la règle.

```
   V770062061   offre acceptee, statut « Actif »
   VA32253      offre acceptee, statut « Actif »
   VM70661      compromis actif, statut « Sous offre »
   VS046        UNE VENTE, statut « Sous offre »
```

**La règle est plus juste que la donnée.** Elle ne les corrige pas — ce serait une remontée,
donc une création déguisée. Elle les *montre*, et c'est déjà beaucoup.

---

## 7ter. « Et si le registre des mandats avait ses dates de clôture ? »

*Question de Frédéric, 01/09, devant les 8 fiches d'estimation qui portent une vieille vente.*

**La mesure d'abord :**

```
   87 dates de cloture sur 23 837 mandats au registre  ->  0,4 %
   les 8 mandats en cause : AUCUN n'en a
```

Les 8 fiches sont toutes des **estimations** (`EM…`, `EA…`), avec ventes de 2016 à 2021 et
**un seul mandat** chacune. Ce sont des biens vendus il y a des années, revenus en estimation
depuis — le préfixe du dossier a même changé (`VT…` → `EM…`). Ce n'est pas une anomalie, c'est
une **réutilisation de fiche**.

**La réponse est donc en trois temps :**

```
   OUI    une date de cloture nommerait la cause : « cette vente releve d'un mandat
          clos, elle ne compte plus ». C'est la lecture juste de ces 8 cas.

   MAIS   il faudrait ECRIRE une regle de plus pour l'exploiter -- rejeter les
          affaires dont le mandat est clos. Elle n'existe pas.

   ET     surtout : LA BORNE LES PROTEGE DEJA, sans dependre de rien. Faire reposer
          la regle sur une donnee remplie a 0,4 % la rendrait fausse dans 99,6 %
          des cas -- un mandat sans date serait lu comme « jamais clos ».
```

➡ **La date de clôture serait un confort, pas une nécessité.** Elle deviendrait nécessaire le
jour où l'on voudrait *lever* la borne « Estimation hors échelle » — et on ne le veut pas.
Le rattrapage des dates de clôture reste ce qu'il était : le chantier **C.13**, à son rang.

---

## 8. Ce qui reste ouvert

- **Le geste « archiver » après une annulation** : les 736 cas « compromis annulé → Clos +
  archivé » sont le résultat de **deux** gestes successifs, pas d'un choix offert par Hektor.
  Aucun choix « actif / archiver » n'a jamais été observé à l'annulation — seulement à
  l'enregistrement d'une vente. *(relevé du 28/08)*
- **La suppression d'une vente** : son bouton est **présent en DOM mais masqué (0×0)** pour le
  compte administrateur — même phénomène que le lien mandant invisible du 31/08. Le vrai verbe
  n'a **jamais été vu passer**.
- **26bis-relations, 26bis-contacts, l'inventaire d'avant coupure** : ce statut dérivé devra
  survivre aux reconstructions nocturnes, comme le reste.

Voir `ACTIONS_TRANSACTION_HEKTOR_2026-08-28.md`, `PROTOCOLE_ASSISTANT_VENTE_HEKTOR_2026-08-30.md`,
`LISTE_TACHES_A_COCHER_2026-08-29.md` *(C.19-c)*, `PLAN_DEV_ACTUALISE_2026-08-20.md`.
