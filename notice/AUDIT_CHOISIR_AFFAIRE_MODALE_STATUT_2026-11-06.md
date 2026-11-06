# Audit — « Choisir » une autre affaire dans la modale « Changer le statut » ne recharge pas le formulaire

*06/11/2026. Lecture seule : rien n'a été écrit en base, chez Hektor ni dans le code. Demande de Frédéric (06/11) :
« AUDIT « Choisir » une autre affaire dans la modale ne recharge pas les champs principaux ». Suite du § 12 de
`notice/AUDIT_REFONTE_MODALE_STATUT_2026-11-05.md` (lu dans le code le 05/11, non éprouvé).*

**Audit limité à l'objet « transaction » (offre, compromis, vente), geste « modifier » depuis la modale.** Les autres
objets ne sont pas mesurés ici.

|  | créer | modifier | supprimer / archiver | lire / remonter |
|---|---|---|---|---|
| transaction — offre | non touché (pas de « Choisir » à la création) | ⚠ **le risque est ici** (§ 3) | sans risque : « Refuser » / « Accepter » ne lisent pas le formulaire | l'écran affiche des valeurs qui ne sont pas celles de l'affaire visée |
| transaction — compromis, vente | non touché | faible depuis le 03/11 : seul un champ TOUCHÉ part (§ 3) | sans risque (« Annuler », « Supprimer » ne lisent pas le formulaire) | idem |
| les autres objets | non mesuré | non mesuré | non mesuré | non mesuré |

## 1. Ce que fait « Choisir »

- Le bouton apparaît dans « Les affaires de ce bien » : onglet Offre d'un bien NON engagé (toute offre, même refusée) ;
  offre écartée d'un bien engagé ; compromis ou vente quand plusieurs sont vivants. Nouvelle modale :
  `ModaleStatutV2.tsx` ~l. 930 ; ancienne : `App.tsx` ~l. 24199. Les deux appellent
  `setStatusChangeAffaireChoisie(id)`, rien d'autre.
- `affaireCourantePourStatut()` (`App.tsx` ~l. 19058) fait passer le choix AVANT tout : les boutons du pied
  (« Refuser », « Accepter », « Mettre à jour… ») visent donc l'affaire choisie.
- Se rechargent pour elle : les conditions et la note (effets qui dépendent du choix, ~l. 18579 et 18651), la reprise
  de commission (~l. 19504), la répartition (sauf une saisie en cours — risque déjà noté le 30/10, § 3.12, non mesuré).

## 2. Le défaut, dans le code

L'effet qui PRÉREMPLIT le formulaire depuis l'affaire courante (`App.tsx` ~l. 19170 → 19350 : montant, prix, date,
date d'acte, séquestre, net vendeur, honoraires, taux, validité, rétractation, acquéreurs, notaires) appelle bien
`affaireCourantePourStatut()`, mais ses dépendances sont `[statusChangeAffaires, statusChangeStatus, carnetAffaires]`
— **pas le choix**. Cliquer « Choisir » ne le relance donc pas : le formulaire garde ce qu'il portait.

Ce qu'il porte alors, selon le bien :
- **aucune offre vivante** (toutes refusées) : pas d'affaire courante à l'ouverture → les valeurs d'ouverture, c'est-à-dire
  **le prix du bien et la date du jour** ;
- **une offre vivante et d'autres** : les valeurs de l'offre vivante — et on « Choisit » une autre offre.

⚠ **Ajouter le choix aux dépendances NE SUFFIT PAS.** L'effet n'écrit qu'une valeur PRÉSENTE et ne vide rien :
les acquéreurs ne se posent que si la liste est vide (`if (deja.length) return deja`), les notaires, le séquestre, la date
d'acte, les honoraires seulement s'ils existent sur l'affaire. Relancé seul, il laisserait sur l'affaire B les
acquéreurs, notaires, séquestre… de l'affaire A. Et la liste des champs TOUCHÉS (`statusChangeTouches`) resterait celle
d'avant le choix.

## 3. Ce qui partirait chez Hektor

« Mettre à jour l'offre / le compromis / la vente » = `handleChangeHektorAnnonceStatus(e, true)` → travail
`change_hektor_annonce_status` avec `reprendre_transaction: true`.

- **Offre** (`submitHektorTransactionStatus`, worker ~l. 15677) : le corps est construit NEUF et porte TOUJOURS
  `montantOffre`, `dateOffre`, `nbJoursValidite` depuis la charge — sans regarder les champs touchés (le commentaire
  dit pourquoi : omettre un champ serait un pari sur Hektor). → **Après « Choisir », « Mettre à jour l'offre » écrirait
  chez Hektor, sur l'offre choisie, le montant, la date et la validité qui restaient à l'écran** — le prix du bien et la
  date du jour sur une offre refusée, ou ceux d'une autre offre. Hektor accepte de reprendre une offre refusée (mesure
  du 08/09, offre 33048). Une offre ACCEPTÉE est protégée (bouton éteint, `offreAccepteeFigeeChezHektor`).
- **Compromis, vente** (assistant, worker ~l. 14750, « B » du 03/11) : en reprise, **seul un champ TOUCHÉ part**. Un
  champ resté à l'écran sans être touché ne part pas. Reste un écran trompeur, et la liste des champs touchés AVANT le
  choix, qui s'appliquerait à l'affaire choisie.
- **Chez nous** : le carnet et le registre n'inscrivent que ce qui a été tapé (interrupteurs `affaire_modif_champs_touches`
  et `affaire_modif_au_registre` à `on`). Mais un retour de Hektor corrompu redescend au registre la nuit.

## 4. Mesures (base, 06/11)

- **Usage de « Mettre à jour l'offre »** : 3 travaux en tout depuis mai (`reprendre_transaction = true`, cible offre) — le
  13/10 sur 61672 (corriger 16 000 → 160 000, en erreur), le 23/10 deux fois sur 24113 (essais de Frédéric). **Aucun dégât
  constaté** ; le chemin est rare, mais il est ouvert.
- **Biens exposés aujourd'hui** (vivants, au moins une offre chez Hektor, ni compromis ni vente en cours) : **14 « Actif »
  dont toutes les offres sont refusées** (le cas « prix du bien + date du jour »), et **4 « Sous offre »** avec une offre
  vivante et d'autres. Cohérent avec le § 12 du 05/11 (14 + 1, définition un peu plus stricte).
- La modale est réservée à admin et manager.
- ⚠ **Non reproduit à l'écran** : la démonstration locale ne charge pas d'affaires, et le seul bien d'essai vivant (61398)
  n'a qu'une offre (rien à « Choisir »). La preuve à l'écran se fera avec le correctif (§ 5, contrôle).

## 5. Le correctif proposé (code « derrière » → « vas-y » à part)

1. **Une remise à zéro du formulaire de transaction quand le choix change** : extraire de `openStatusChangeModal` la liste
   des remises à zéro des champs de transaction (montant et prix = prix du bien, date du jour, date d'acte, validité et
   rétractation 10, acquéreurs et notaires vides + drapeaux « affirmés » faux, honoraires, taux, net, séquestre, charge
   de la commission et ses drapeaux, **champs touchés vidés**), dans une fonction appelée par `openStatusChangeModal`
   (inchangé dans son effet) ET par un effet neuf `[statusChangeAffaireChoisie]`, placé AVANT l'effet de préremplissage.
2. **Ajouter `statusChangeAffaireChoisie` aux dépendances de l'effet de préremplissage** : il reremplit depuis l'affaire
   choisie (le carnet d'abord, le registre ensuite, comme aujourd'hui).
3. **Les deux vues ne changent pas** (elles appellent toujours `setStatusChangeAffaireChoisie`) ; l'ancien bloc non plus.

**Ce que ça pourrait casser ailleurs.**
- Une saisie tapée AVANT de cliquer « Choisir » est perdue — c'est voulu : elle visait l'autre affaire.
- Le chemin du **registre des transactions** (`ouvrirGesteDuRegistre`, ~l. 17303) pose le choix juste après l'ouverture :
  la remise à zéro est la même que celle d'ouverture, puis le préremplissage arrive avec les affaires. Pas de changement
  attendu — à contrôler.
- « Changer d'onglet » remet le choix à `null` : l'effet neuf ne doit RIEN faire sur `null` (sinon il effacerait
  l'héritage compromis → vente du 10/09). À garder tel quel.
- Les conditions, la note, la répartition ont leurs propres effets sur le choix : inchangés.
- L'outil d'empreintes signalera `openStatusChangeModal` et l'effet de préremplissage : écarts à lire, puis reposer.

**Contrôle.** Essai hors ligne de la règle (remise à zéro puis préremplissage, cas « toutes refusées » et « une vivante
et d'autres ») ; `npm run build` ; puis, à l'écran en production SANS envoyer, sur un bien exposé : « Choisir » une
offre doit afficher SES montant, date et validité. Retour arrière : retirer l'effet neuf et la dépendance.

**Non mesuré, noté :** le même « reste » existe peut-être au changement d'ONGLET (acquéreurs gardés d'un onglet à
l'autre) ; une partie est voulue (la vente hérite du compromis, règle du 10/09). Hors de cet audit.

## 6. Décision de Frédéric (06/11) : ON NE TOUCHE RIEN

« non il ne faut pas laisse comme aujourd'hui ne touche rien ». Le correctif du § 5 n'est PAS fait. ⛔ Ne pas le
reproposer de soi-même. Le défaut reste connu et écrit ici : après « Choisir », vérifier à l'œil le montant, la date et
la validité avant « Mettre à jour l'offre ».
