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
| **transaction** — refuser · annuler · supprimer | Hektor **redescend** le statut d'un cran | 3 gestes, éprouvés 29-31/08 |
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

## 7. La solution proposée

**Une règle de REDESCENTE seulement**, appelée par les trois gestes après confirmation :

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
