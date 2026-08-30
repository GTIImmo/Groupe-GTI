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
