# L'assistant « enregistrer une vente » de Hektor — protocole relevé sur le réseau

*30/08/2026 · annonce 62774 · session administrateur · enregistreur posé dans la page.*

> **Pourquoi cette note existe.** Le worker envoyait à Hektor un POST plat sur
> `annonce-SuiviVente-vente-createVente`, calqué sur celui de l'offre. Deux passages réels le
> 30/08 ont montré que **Hektor accepte le changement de statut et ne crée aucune vente** —
> confirmé par les deux portes *(fiche vide, `/Api/Vente/ListVentes/` à 0)*. La cause n'était ni
> un droit, ni un champ manquant, ni un compromis absent : **la vente n'est pas un formulaire,
> c'est un assistant en quatre étapes.**
>
> Le projet croyait le contraire. `ANALYSE_TRANSACTIONS_HEKTOR_SERVEUR_APP_2026-08-28.md:93`
> affirmait *« l'app savait créer une transaction »*, et son tableau donnait « 22 champs » pour
> l'offre mais un simple « formulaire » pour le compromis et la vente. **Le compte de champs
> n'avait été mesuré que pour l'offre.** Une supposition écrite comme un fait.

---

## Ce que valent les trois popins, mesuré

| popin | taille | champs `name=` | ce que c'est |
|---|---|---|---|
| **offre** | 208 541 car | **22** | un vrai formulaire, plat — c'est pourquoi l'offre marche |
| **compromis** | 85 921 car | **0** | `compromisStepHost` · `compromisStepper` · `mustacheLoader` |
| **vente** | 85 822 car | **0** | `venteStepHost` · `venteStepper` · `mustacheLoader` |

Les champs n'existent pas dans la page reçue : ils arrivent ensuite, par gabarits Mustache
montés en JavaScript. Le worker ne voit que ce que le serveur envoie — donc rien.

---

## LA SÉQUENCE RÉELLE

**Le verbe n'est pas `createVente`.** Celui-ci ne rend que la coquille. Tout passe par
**`annonce-SuiviVente-vente-getStepVente`**.

| # | méthode | verbe | `fromStep` | `step` | `containerModule[]` | champs propres |
|---|---|---|---|---|---|---|
| 1 | GET | `…vente-createVente` | | | | la coquille (CSS + conteneurs vides) |
| 2 | GET | `moustachu` | | | | les gabarits |
| 3 | POST | `…vente-getStepVente` | | | | `initBasket=true`, `basket=` *(vide)* |
| 4 | POST | `…vente-getStepVente` | `0` | `2` | `infosFinancieresVente` + `acquereurNotaireAutresProspectsVente` + `annonceMandatVente` | `prixDeVente` `dateVente` `montantHonoraireEntree` `tauxHonoraireEntree` `montantHonoraireSortie` `tauxHonoraireSortie` `mandat` `selectedMandat` `mandantSearch` `mandants[]` `typeUser` `addAcquereurSearch` `acquereurs[]` `addAcquereurNotaireSearch` |
| 5 | POST | `…vente-getStepVente` | `2` | `3` | `commissionsVente` | `unitesEntreePercent` `unitesSortiePercent` |
| 6 | POST | `…vente-getStepVente` **+ `actionContainer[]=save` `actionContainer[]=treat` DANS L'URL** | `3` | `3` | `recapitulatifVente` | *(aucun)* |

### Les quatre points qui font la différence

**① `basket` — l'état, sérialisé PHP, transporté d'appel en appel.** 565 caractères après la
première étape. Il n'y a **rien à comprendre dedans** : on le reçoit et on le renvoie tel quel.
Sans lui, chaque appel repart de zéro et rien ne s'accumule. **C'est la pièce que le worker
n'avait pas.**

**② `actionContainer[]=save,treat` va dans l'URL**, pas dans le corps. Le worker le mettait dans
le corps — d'où une réponse qui était *le formulaire lui-même*, c'est-à-dire « je te ré-affiche
la popin ».

**③ `mandat=648-PROTEXA`** est bien au format `<id>-<FAMILLE>` que le projet redoutait de mal
former. **Il vient de la réponse d'étape, pas de la coquille** — voilà pourquoi le worker le
lisait vide *(`forme_mandat: (vide)`, mesuré)*. Le commentaire de `console_job_worker.js` avait
raison de prévenir : une valeur amputée est ignorée **sans erreur**.

**④ L'étape 2 « Rétrocession » est sautée** *(grisée à l'écran)* : on passe de `step 2` à
`step 3`. Le numéro d'étape n'est pas un compteur qu'on incrémente — il vient de l'assistant.

---

## LES DEUX BOUTONS DE L'ÉTAPE 4 — C.19-c

Le récapitulatif offre bien **« Enregistrer & laisser actif »** et **« Enregistrer & archiver »**.

- **« laisser actif »** : mesuré ci-dessus — `actionContainer[] = save, treat`.
- **« archiver »** : ⚠ **NON MESURÉ.** Ne pas le déduire.

> C'est ce qui **valide après coup** le choix de conception de C.19-c *(`6bd5b04`)* : l'app
> n'appelle pas ce bouton, elle enchaîne le geste d'archivage déjà éprouvé *(127 exécutions)*
> **après** que la vente est confirmée. On ne devine pas un paramètre sur le geste qui a
> **détruit la vente 23288** le 29/08.

---

## LA PREUVE

```
   vente creee                23290
   /Api/Vente/ListVentes/     du 29 au 31/08 -> count 1, id 23290, 151 000,00, 30-08-2026
```

Avant ce relevé : **0 vente** sur la même fenêtre, deux passages du worker plus tard.

---

## CE QUE ÇA CHANGE POUR LE CODE

`submitHektorTransactionStatus` a été écrit **pour l'offre**. Il convient à l'offre et **à elle
seule**. Le compromis et la vente demandent le protocole ci-dessus.

**Et on sait déjà faire.** La création d'une annonce pilote un assistant Hektor de bout en bout —
`ajoutebien_wizardBien` puis `annonce-createBien-Ajx_Bien_wizardStepNew`, étapes 2 à 7, avec
extraction des valeurs du formulaire à chaque étape et **78 travaux** à son actif. Le motif est
en interne ; ce qui manquait, c'était la séquence. Elle est là.

---

## RAPPEL DE MÉTHODE

Ce relevé confirme, une troisième fois, la leçon du 29/08 : **lire le code ne remplace pas
regarder passer l'appel.** Le verbe du compromis lu statiquement était faux ; celui de la vente
était juste ; et ici la lecture statique aurait donné `createVente` — la coquille, pas le geste.

---

# LA CONDITION DE BLOCAGE — établie le 31/08 par expérience

*Frédéric l'avait énoncée : « il peut y avoir deux compromis sur une annonce, mais il faut que
le premier soit noté refusé pour pouvoir en ajouter un autre. » **Je l'ai contredit à tort**, sur
une inférence fausse. L'expérience lui donne raison.*

## Le protocole — une seule variable à la fois

Même code, même charge, sur le bac à sable 62774 dont l'état est maîtrisé de bout en bout.
Chaque étape relève par l'**API** ce qui existait avant et ce qui a été créé.

```
   C1  aucun compromis actif au depart   ->  CREE 50053      reference
   C2  50053 ACTIF present               ->  RIEN CREE       LE TEST
       annulation de 50053                                   done
   C3  juste apres l'annulation          ->  CREE 50054      contre-epreuve
   V1  aucune vente au depart            ->  CREE 23293      reference
   V2  23293 presente                    ->  RIEN CREE       LE TEST
```

Vérifié pièce par pièce : `50053 status 2` *(annulé par le travail)*, `50054 status 1` *(créé
juste après)*, `23293` existant. **C3 ferme le raisonnement** : annuler suffit à débloquer, et
immédiatement.

## La règle, et elle diffère selon le genre

| | ce qui bloque | comment on débloque | réversible ? |
|---|---|---|---|
| **compromis** | un compromis **actif** *(status 1)* | l'**annuler** — verbe éprouvé le 29/08 | **oui** |
| **vente** | **toute** vente existante | la **supprimer** — elle n'a aucun état | **non** |

C'est la conséquence directe d'un fait déjà mesuré : `hektor_vente` **n'a pas de colonne de
statut**. Une vente ne se refuse pas, elle disparaît. Donc le geste qui débloque une vente est
**définitif**, et ne peut pas être automatisé sans décision humaine.

## Pourquoi je m'étais trompé — l'inférence, pas la mesure

J'avais objecté : *« un compromis actif ne peut pas bloquer, puisque 9 075 annonces Vendues en
portent un »*. La mesure était juste ; **le raisonnement était faux**.

Ces 9 075 dossiers sont **terminés** — personne n'y crée un nouveau compromis, donc l'actif qui
y dort ne bloque jamais rien. La règle porte sur le **geste de création**, pas sur l'état du
parc. Les deux faits sont vrais et parfaitement compatibles :

- une fois la vente enregistrée, le compromis reste actif et personne ne le clôt ;
- pour en créer un **nouveau**, il faut d'abord annuler celui qui est actif.

➡ **La leçon** : une mesure exacte ne protège pas d'une conclusion fausse. Il fallait
l'expérience, pas le raisonnement.

## Ce que `ListCompromis` est vraiment — précision de Frédéric, vérifiée

J'avais classé en « faiblesse » le fait que ce listing ne rende que **97 lignes** quand le miroir
compte 10 573 compromis, et que `50054` en ait disparu quelques minutes après sa création.

**Ce n'en est pas une.** `ListCompromis` sert l'app et le front : il rend les compromis
**EN COURS**, c'est-à-dire ceux dont l'annonce n'a pas encore de vente. Mesuré sur les 97 :

```
   dont l'annonce a DEJA une vente  :   0
   dont l'annonce n'en a AUCUNE     :  97
```

➡ Et cela **explique exactement** la disparition de `50054` : c'est la vente `23293`, créée juste
après sur la même annonce, qui l'a fait sortir de la liste. Rien n'a été perdu ni masqué.

**Un compromis peut donc être `status 1` sans être « en cours »** — 9 206 actifs au miroir, dont
seulement 1 689 sur une annonce sans vente. « Actif » et « en cours » sont deux choses
différentes, et c'est la seconde qui compte.

Pour l'arbitre, c'est même **la bonne liste** : un compromis qu'on vient de créer est forcément
en cours, donc forcément dedans. La confirmation par `CompromisById` reste utile comme second
témoin, mais elle ne rattrape pas une lacune — il n'y en a pas.
